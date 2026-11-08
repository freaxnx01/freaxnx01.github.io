# Game Subdomains Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Serve every hub game from `<name>.freax.games` with the address visible in the browser.

**Architecture:** Each game repo gets its own GitHub Pages custom domain; a script creates the Cloudflare DNS record first and then sets the Pages domain through the GitHub API. The hub reads play links of both the old path form and the new subdomain form, links to subdomains, and its short-path stubs forward there.

**Tech Stack:** Python 3 (stdlib only: `urllib`, `json`, `subprocess`), pytest, GitHub REST API via `gh api`, Cloudflare API v4, Passbolt CLI.

**Spec:** `docs/superpowers/specs/2026-11-08-game-subdomains-design.md`

## Global Constraints

- Subdomain name = repo name without `game-`: `game-wipfelkratzer` → `wipfelkratzer.freax.games`.
- Order per game: Cloudflare record **before** the Pages domain (the reverse loops through the interim wildcard).
- DNS record: `<name>.freax.games` CNAME `freaxnx01.github.io`, `proxied: false`.
- 43 hub games; Rhyflitzer (`https://rhyflitzer.ch/`) and Dogwash (external) are not moved.
- GitHub only via `direnv exec /home/freax/repos/github/freaxnx01/public gh …`; on HTTP 401 stop. Never another auth.
- Cloudflare token: Passbolt resource `9cffcece-887d-4b30-a11f-2fc92586079b`, the `Password:` line of `passbolt get resource --id … --timeout 10s`. Never print it or write it to disk.
- `game-n-s-clone` uses branch `master`; no code may assume `main`.
- Stubs keep query and hash, like today.

## Review Focus

1. A play link that is already `https://<name>.freax.games/` must still name the repo `game-<name>` (favicons, short links) — tested in Task 1.
2. Re-running the move for a game that has already moved must change nothing and report OK (idempotent) — tested in Task 2.
3. An existing DNS record with another target or proxied on must stop the move for that game instead of being overwritten — tested in Task 2.
4. `rhyflitzer.freax.games` / `www.freax.games` are never play links of a hub game — tested in Task 1.
5. A game whose certificate is not approved within the wait limit must be reported, not enforced and not counted as done — tested in Task 2.

## Maintainer steps (not for agents)

The pipeline does Tasks 1–3 (code in this repo, one PR). Tasks 4–6 need the Cloudflare token and the GitHub Pages API, so they run in a maintainer session.

---

### Task 1: The hub reads subdomain play links

**Files:**
- Modify: `scripts/hubsite.py`
- Modify: `scripts/add_game_favicons.py:44-50`
- Modify: `scripts/make_short_links.py:31-34`
- Test: `tests/test_hubsite.py`, `tests/test_make_short_links.py`

**Interfaces:**
- Produces: `hubsite.play_repo(block: str) -> str | None` (repo name `game-<name>` of the first play link in `block`, any of the three forms); `hubsite.game_url(repo: str) -> str` returns `https://<name>.freax.games/`; `hubsite.subdomain(repo: str) -> str` returns `<name>.freax.games`. `PLAY_RE` is removed.

- [ ] **Step 1: Write the failing tests** — replace `tests/test_hubsite.py` with:

```python
"""Tests for scripts/hubsite.py"""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from hubsite import game_url, play_repo, subdomain  # noqa: E402


def link(href):
    return f'<a class="card__play" href="{href}" target="_blank">▶ Play</a>'


def test_all_three_play_link_forms_name_the_repo():
    for href in ("https://github.freaxnx01.ch/game-nibbles/",
                 "https://freax.games/game-nibbles/",
                 "https://nibbles.freax.games/"):
        assert play_repo(link(href)) == "game-nibbles"


def test_foreign_and_special_links_are_not_games():
    for href in ("https://julia-hase.github.io/dogwash/", "https://rhyflitzer.ch/",
                 "https://rhyflitzer.freax.games/", "https://www.freax.games/",
                 "https://freax.games/games/"):
        assert play_repo(link(href)) is None


def test_game_url_and_subdomain():
    assert subdomain("game-zen-sudoku") == "zen-sudoku.freax.games"
    assert game_url("game-zen-sudoku") == "https://zen-sudoku.freax.games/"
```

Append to `tests/test_make_short_links.py`:

```python
def test_subdomain_play_links_forward_to_the_subdomain():
    html = card("game-wipfelkratzer-icon.png", "https://wipfelkratzer.freax.games/")
    assert short_links(html) == {"wipfelkratzer": "https://wipfelkratzer.freax.games/"}
```

and change the existing `test_site_games_get_a_root_relative_target` to:

```python
def test_path_play_links_also_forward_to_the_subdomain():
    html = card("game-wipfelkratzer-icon.png", "https://github.freaxnx01.ch/game-wipfelkratzer/")
    assert short_links(html) == {"wipfelkratzer": "https://wipfelkratzer.freax.games/"}
```

If any other test in `tests/test_make_short_links.py` expects a `/game-…/` target, change its expectation to the `https://<name>.freax.games/` form the same way.

- [ ] **Step 2: Run, expect FAIL**

Run: `python3 -m pytest -q tests/test_hubsite.py tests/test_make_short_links.py`
Expected: FAIL (`ImportError: cannot import name 'play_repo'`).

- [ ] **Step 3: Implement** — replace `scripts/hubsite.py` with:

```python
"""Where the hub and its games live (game-subdomains spec, 2026-11-08)."""
import re

SITE = "https://freax.games"
GAME_DOMAIN = "freax.games"
# Subdomains of freax.games that are not hub games.
NOT_GAMES = {"www", "rhyflitzer"}
# Play links in three forms: old host path, freax.games path, own subdomain.
_PATH_RE = re.compile(r'href="https://(?:github\.freaxnx01\.ch|freax\.games)/(game-[a-z0-9-]+)/"')
_SUB_RE = re.compile(r'href="https://([a-z0-9-]+)\.freax\.games/"')


def play_repo(block: str) -> str | None:
    """Repo name (game-<name>) of the play link in a card, or None for other links."""
    m = _PATH_RE.search(block)
    if m:
        return m.group(1)
    m = _SUB_RE.search(block)
    if m and m.group(1) not in NOT_GAMES:
        return f"game-{m.group(1)}"
    return None


def subdomain(repo: str) -> str:
    return f"{repo.removeprefix('game-')}.{GAME_DOMAIN}"


def game_url(repo: str) -> str:
    return f"https://{subdomain(repo)}/"
```

In `scripts/add_game_favicons.py` change the import to `from hubsite import play_repo` and the loop body to:

```python
        icon_m = ICON_RE.search(block)
        repo = play_repo(block)
        if not icon_m or not repo:
            continue
        games.append({
            "repo": repo,
            "icon_path": hub_root / "games" / "assets" / icon_m.group(1),
        })
```

In `scripts/make_short_links.py` change the import to `from hubsite import game_url, play_repo` and the match to:

```python
        repo = play_repo(block)
        if repo:
            links[name] = game_url(repo)
            continue
```

Update its module docstring line 1 to `Short paths for the games hub: freax.games/<name> forwards to the game's subdomain.`

- [ ] **Step 4: Run all tests, expect PASS**

Run: `python3 -m pytest -q tests`
Expected: all pass. `grep -rn PLAY_RE scripts tests` → no hits.

- [ ] **Step 5: Commit**

```bash
git add scripts/hubsite.py scripts/add_game_favicons.py scripts/make_short_links.py tests/test_hubsite.py tests/test_make_short_links.py
git commit -m "refactor(scripts): read subdomain play links, game_url points to <name>.freax.games"
```

---

### Task 2: `move_to_subdomain.py`

**Files:**
- Create: `scripts/move_to_subdomain.py`
- Test: `tests/test_move_to_subdomain.py`

**Interfaces:**
- Consumes: `hubsite.subdomain(repo)`, `hubsite.play_repo(block)`.
- Produces: CLI `python3 scripts/move_to_subdomain.py [--all | <name> …] [--wait-minutes N]`; functions `ensure_dns(cf, host) -> str` (`"created"`/`"ok"`), `move(repo, cf, gh) -> str`, `finish(repo, gh, deadline) -> str`, `hub_repos(page) -> list[str]`. Clients: `Cloudflare` with `find(host) -> dict | None`, `create_cname(host, target) -> None`; `GitHub` with `pages(repo) -> dict`, `set_cname(repo, cname) -> None`, `enforce_https(repo, cname) -> None`.

- [ ] **Step 1: Write the failing tests** — `tests/test_move_to_subdomain.py`:

```python
"""Tests for scripts/move_to_subdomain.py (no network: fake clients)."""
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import move_to_subdomain as m  # noqa: E402


class FakeCF:
    def __init__(self, records=None):
        self.records = dict(records or {})
        self.created = []

    def find(self, host):
        return self.records.get(host)

    def create_cname(self, host, target):
        self.created.append(host)
        self.records[host] = {"type": "CNAME", "content": target, "proxied": False}


class FakeGH:
    def __init__(self, cname=None, cert="approved"):
        self.cname, self.cert, self.enforced, self.calls = cname, cert, False, []

    def pages(self, repo):
        return {"cname": self.cname, "https_enforced": self.enforced,
                "https_certificate": {"state": self.cert}}

    def set_cname(self, repo, cname):
        self.calls.append(("cname", cname))
        self.cname = cname

    def enforce_https(self, repo, cname):
        self.calls.append(("https", cname))
        self.enforced = True


def test_dns_is_created_before_the_pages_domain():
    cf, gh = FakeCF(), FakeGH()
    assert m.move("game-wipfelkratzer", cf, gh) == "moved"
    assert cf.created == ["wipfelkratzer.freax.games"]
    assert gh.calls == [("cname", "wipfelkratzer.freax.games")]


def test_second_run_changes_nothing():
    cf = FakeCF({"nibbles.freax.games": {"type": "CNAME", "content": "freaxnx01.github.io", "proxied": False}})
    gh = FakeGH(cname="nibbles.freax.games")
    assert m.move("game-nibbles", cf, gh) == "already moved"
    assert cf.created == [] and gh.calls == []


@pytest.mark.parametrize("rec", [
    {"type": "CNAME", "content": "elsewhere.example", "proxied": False},
    {"type": "CNAME", "content": "freaxnx01.github.io", "proxied": True},
    {"type": "A", "content": "1.2.3.4", "proxied": False},
])
def test_foreign_dns_record_stops_the_move(rec):
    cf, gh = FakeCF({"nibbles.freax.games": rec}), FakeGH()
    with pytest.raises(m.MoveError, match="nibbles.freax.games"):
        m.move("game-nibbles", cf, gh)
    assert gh.calls == []


def test_https_is_enforced_only_with_an_approved_certificate():
    gh = FakeGH(cname="nibbles.freax.games", cert="approved")
    assert m.finish("game-nibbles", gh, deadline=0) == "https on"
    gh2 = FakeGH(cname="nibbles.freax.games", cert="authorization_pending")
    assert m.finish("game-nibbles", gh2, deadline=0) == "certificate not ready"
    assert gh2.calls == []


def test_hub_repos_lists_movable_games_only():
    page = "".join(f'<article class="card"><a class="card__play" href="{h}">Play</a></article>'
                   for h in ("https://freax.games/game-nibbles/", "https://zen-sudoku.freax.games/",
                             "https://rhyflitzer.ch/", "https://julia-hase.github.io/dogwash/"))
    assert m.hub_repos(page) == ["game-nibbles", "game-zen-sudoku"]
```

- [ ] **Step 2: Run, expect FAIL**

Run: `python3 -m pytest -q tests/test_move_to_subdomain.py`
Expected: FAIL (`ModuleNotFoundError: move_to_subdomain`).

- [ ] **Step 3: Implement** — `scripts/move_to_subdomain.py`:

```python
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
        page = (Path(__file__).resolve().parent.parent / "games" / "index.html").read_text()
        repos = hub_repos(page)
    else:
        repos = [f"game-{n.removeprefix('game-')}" for n in a.names]
    if not repos:
        ap.error("name at least one game or use --all")
    cf, gh = Cloudflare(), GitHub()
    failed = 0
    for repo in repos:
        try:
            print(f"{repo}: {move(repo, cf, gh)}")
        except MoveError as e:
            failed += 1
            print(f"{repo}: FAILED {e}")
            repos = [r for r in repos if r != repo]
    deadline = time.time() + 60 * a.wait_minutes
    for repo in repos:
        state = finish(repo, gh, deadline)
        failed += state != "https on"
        print(f"{repo}: {state}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run, expect PASS**

Run: `python3 -m pytest -q tests/test_move_to_subdomain.py && python3 -m pytest -q tests`
Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add scripts/move_to_subdomain.py tests/test_move_to_subdomain.py
git commit -m "feat(scripts): move_to_subdomain.py moves games to <name>.freax.games"
```

---

### Task 3: Hub links, stubs, live check, docs

**Files:**
- Modify: `games/index.html` (43 play links), the 43 stub dirs `<name>/index.html` (regenerated)
- Modify: `scripts/check_domains.py:7-21`
- Modify: `CLAUDE.md:11-17`

**Interfaces:**
- Consumes: `hubsite.game_url`, `make_short_links.write_stubs`.

- [ ] **Step 1: Rewrite play links**

```bash
sed -i -E 's#href="https://(github\.freaxnx01\.ch|freax\.games)/game-([a-z0-9-]+)/"#href="https://\2.freax.games/"#g' games/index.html
grep -c 'href="https://[a-z0-9-]*\.freax\.games/"' games/index.html
grep -cE 'href="https://(github\.freaxnx01\.ch|freax\.games)/game-' games/index.html
```

Expected: `43`, then `0`. `rhyflitzer.ch` and the Dogwash link are unchanged (`git diff games/index.html | grep -c '^-.*card__play'` → `43`).

- [ ] **Step 2: Regenerate stubs**

Run: `python3 scripts/make_short_links.py`
Expected: `44 short links: …`; `grep -l 'location.replace("https://wipfelkratzer.freax.games/"' wipfelkratzer/index.html` → hit; `git status --short | grep -v '/index.html$' | grep -v games/index.html` → nothing new except script/doc files.

- [ ] **Step 3: Update `scripts/check_domains.py`** — replace `CHECKS` and `STUB_TARGETS`:

```python
CHECKS = [
    # (start URL, expected final URL after redirects, or None = just expect HTTP 200)
    ("https://freax.games/games/", None),
    ("https://rhyflitzer.ch/", None),
    ("https://wipfelkratzer.freax.games/", None),
    ("https://freax.games/game-wipfelkratzer/?x=1", "https://wipfelkratzer.freax.games/?x=1"),
    ("https://github.freaxnx01.ch/game-wipfelkratzer/?x=1", "https://wipfelkratzer.freax.games/?x=1"),
    ("https://github.freaxnx01.ch/games/", "https://freax.games/games/"),
    ("https://rhyflitzer.freaxnx01.ch/nfz/", "https://rhyflitzer.ch/nfz/"),
    ("https://rhyflitzer.freax.games/", "https://rhyflitzer.ch/"),
    ("https://freax.games/wipfelkratzer", "https://freax.games/wipfelkratzer/"),
]
STUB_TARGETS = [
    # stub URL, string its JS forward must contain
    ("https://freax.games/wipfelkratzer/", 'location.replace("https://wipfelkratzer.freax.games/"'),
    ("https://freax.games/rhyflitzer/", 'location.replace("https://rhyflitzer.ch/"'),
    ("https://rhyflitzer.ch/nfz/", 'location.replace("../?utm_source=nfz&utm_medium=artikel"'),
]
```

and its docstring to `"""Live check of the hub domains and game subdomains. Exit 1 on any failure."""`.

- [ ] **Step 4: Update `CLAUDE.md`** — replace the paragraph starting "Each game lives in its own `game-<name>` repo" and the following short-path paragraph with:

```markdown
Each game lives in its own `game-<name>` repo (GitHub Pages, root `index.html`),
is served at its own subdomain `https://<name>.freax.games/` (`<name>` = repo name
without `game-`), and gets a card in `games/index.html` whose play link is that
subdomain. A new game gets its subdomain with
`python3 scripts/move_to_subdomain.py <name>` (maintainer session: needs the
Cloudflare token from Passbolt). Until then `<name>.freax.games` forwards to
`freax.games/<name>/` through a Cloudflare wildcard. Rhyflitzer has its own domain,
`rhyflitzer.ch`.

Every card also gets a short path `freax.games/<name>/`, a redirect stub generated by
`python3 scripts/make_short_links.py`. Rerun it after adding or removing a card and
commit the stubs with the card.
```

In the Umami paragraph replace `data-domains="github.freaxnx01.ch,freax.games"` (keep both: …) with `data-domains="github.freaxnx01.ch,freax.games,<name>.freax.games"` (keep all three: old hostnames still arrive via redirects).

- [ ] **Step 5: Run tests and commit**

Run: `python3 -m pytest -q tests` → all pass.

```bash
git add games/index.html */index.html scripts/check_domains.py CLAUDE.md
git commit -m "feat(hub): play links and short paths point to <name>.freax.games"
```

Open the PR; **do not merge** — it goes live after Task 5.

---

### Task 4 (maintainer): Game repo fixes

One PR per repo, each with a CHANGELOG entry where the repo has one. Merge before the repo's move.

| Repo | Change |
|------|--------|
| `game-tschau-sepp` | `index.html` and `source/Tschau Sepp Online.dc.html`: `data-domains="github.freaxnx01.ch,freax.games"` → `data-domains="github.freaxnx01.ch,freax.games,tschau-sepp.freax.games"`; `scripts/sim/test-invite-link.mjs`: origin `https://github.freaxnx01.ch` → `https://tschau-sepp.freax.games`, pathname `/game-tschau-sepp/` → `/` |
| `game-toepferscheibe` | `index.html`: `data-domains` add `toepferscheibe.freax.games` |
| `game-wipfelkratzer` | `js/game.js`: `SPLASHDOWN_URL = 'https://splashdown.freax.games/'` |
| `game-kit-racer` | `test/signal.test.mjs`: `https://github.freaxnx01.ch/game-kit-racer/index.html` → `https://kit-racer.freax.games/index.html` (2 asserts); `tools/aerodrome-tracks.mjs` default source → `https://aerodrome-apex.freax.games/` |
| `game-gorillazz` | delete `.github/workflows/deploy.yml` (Pages stays legacy `main:/docs`) |

Verify per repo: its own test command from its `CLAUDE.md`/`package.json`, and `grep -rn 'github.freaxnx01.ch/game-' --include=*.js --include=*.mjs --include=*.html . | grep -v docs/` shows no code hits other than the footer link.

### Task 5 (maintainer): Pilot, then the wave

- [ ] **Pilot:** `python3 scripts/move_to_subdomain.py wipfelkratzer splashdown` → both `moved`, then `https on`. Check in a browser: both games play at their subdomain; Wipfelkratzer → Splashdown link and its `zurueck` back-link work; `https://freax.games/game-wipfelkratzer/?x=1` ends at `https://wipfelkratzer.freax.games/?x=1`. If GitHub drops the query on that redirect, note it in the issue and drop `?x=1` from the two `check_domains.py` expectations.
- [ ] **Wave:** `python3 scripts/move_to_subdomain.py --all` (already moved games report `already moved`). Every line must end in `https on`; rerun for the rest.

### Task 6 (maintainer): Ship the hub PR and check

- [ ] Merge the PR from Task 3.
- [ ] `python3 scripts/check_domains.py` → all `OK`.
- [ ] Homepage (mydocker-compose `services/homepage`) already links `<name>.freax.games`; no change.
- [ ] Comment the results on the issue.
