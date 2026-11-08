#!/usr/bin/env python3
"""Move hub games to <name>.freax.games (game-subdomains spec, 2026-11-08).

Per game: Cloudflare CNAME <name>.freax.games -> freaxnx01.github.io (DNS only) FIRST,
then the repo's Pages custom domain, then Enforce HTTPS once the certificate is approved.
Usage: move_to_subdomain.py wipfelkratzer splashdown | --all  [--wait-minutes 30]
Needs: Passbolt CLI (Cloudflare token) and direnv-gh (GitHub). Safe to rerun.
"""
import argparse
import json
import re
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

from hubsite import play_repo, subdomain

TARGET = "freaxnx01.github.io"
ZONE = "freax.games"
CF_PASSBOLT_RESOURCE = "9cffcece-887d-4b30-a11f-2fc92586079b"
GH = ["direnv", "exec", "/home/freax/repos/github/freaxnx01/public", "gh"]
ARTICLE_RE = re.compile(r'<article class="card"[^>]*>(.*?)</article>', re.DOTALL)


class MoveError(Exception):
    pass


class Cloudflare:
    API = "https://api.cloudflare.com/client/v4"

    def __init__(self):
        out = subprocess.run(["passbolt", "get", "resource", "--id", CF_PASSBOLT_RESOURCE, "--timeout", "10s"],
                             capture_output=True, text=True, check=True).stdout
        self.token = next(l.split(": ", 1)[1] for l in out.splitlines() if l.startswith("Password"))
        self.zone = self._call("GET", f"/zones?name={ZONE}")[0]["id"]

    def _call(self, method, path, body=None):
        req = urllib.request.Request(self.API + path, method=method,
                                     data=json.dumps(body).encode() if body else None,
                                     headers={"Authorization": f"Bearer {self.token}",
                                              "Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=30) as r:
            d = json.load(r)
        if not d.get("success"):
            raise MoveError(f"Cloudflare {method} {path}: {d.get('errors')}")
        return d["result"]

    def find(self, host):
        res = self._call("GET", f"/zones/{self.zone}/dns_records?name={host}")
        return res[0] if res else None

    def create_cname(self, host, target):
        self._call("POST", f"/zones/{self.zone}/dns_records",
                   {"type": "CNAME", "name": host, "content": target, "proxied": False, "ttl": 1})


class GitHub:
    def _api(self, *args):
        p = subprocess.run(GH + ["api", *args], capture_output=True, text=True)
        if "401" in p.stderr or "Bad credentials" in p.stderr:
            raise SystemExit("GitHub 401: the PAT is invalid or expired - stop.")
        if p.returncode:
            raise MoveError(f"gh api {' '.join(args)}: {p.stderr.strip()}")
        return json.loads(p.stdout) if p.stdout.strip() else {}

    def pages(self, repo):
        return self._api(f"repos/freaxnx01/{repo}/pages")

    def set_cname(self, repo, cname):
        self._api("-X", "PUT", f"repos/freaxnx01/{repo}/pages", "-f", f"cname={cname}")

    def enforce_https(self, repo, cname):
        self._api("-X", "PUT", f"repos/freaxnx01/{repo}/pages", "-f", f"cname={cname}",
                  "-F", "https_enforced=true")


def ensure_dns(cf, host):
    rec = cf.find(host)
    if rec is None:
        cf.create_cname(host, TARGET)
        return "created"
    if rec.get("type") == "CNAME" and rec.get("content") == TARGET and not rec.get("proxied"):
        return "ok"
    raise MoveError(f"{host}: existing DNS record {rec.get('type')} {rec.get('content')} "
                    f"proxied={rec.get('proxied')} - fix by hand")


def move(repo, cf, gh):
    host = subdomain(repo)
    dns = ensure_dns(cf, host)
    if gh.pages(repo).get("cname") == host:
        return "already moved" if dns == "ok" else "moved"
    gh.set_cname(repo, host)
    return "moved"


def finish(repo, gh, deadline):
    host = subdomain(repo)
    while True:
        p = gh.pages(repo)
        if p.get("https_enforced"):
            return "https on"
        if (p.get("https_certificate") or {}).get("state") == "approved":
            gh.enforce_https(repo, host)
            return "https on"
        if time.time() >= deadline:
            return "certificate not ready"
        time.sleep(30)


def hub_repos(page):
    repos = (play_repo(b) for b in ARTICLE_RE.findall(page))
    return [r for r in repos if r]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("names", nargs="*", help="short names, e.g. wipfelkratzer")
    ap.add_argument("--all", action="store_true", help="every hub game")
    ap.add_argument("--wait-minutes", type=int, default=30)
    a = ap.parse_args(argv)
    if a.all:
        page = (Path(__file__).resolve().parent.parent / "index.html").read_text()
        repos = hub_repos(page)
    else:
        repos = [f"game-{n.removeprefix('game-')}" for n in a.names]
    if not repos:
        ap.error("name at least one game or use --all")
    cf, gh = Cloudflare(), GitHub()
    moved, failed = [], 0
    for repo in repos:
        try:
            print(f"{repo}: {move(repo, cf, gh)}")
            moved.append(repo)
        except MoveError as e:
            failed += 1
            print(f"{repo}: FAILED {e}")
    deadline = time.time() + 60 * a.wait_minutes
    for repo in moved:
        state = finish(repo, gh, deadline)
        failed += state != "https on"
        print(f"{repo}: {state}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
