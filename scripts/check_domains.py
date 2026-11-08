#!/usr/bin/env python3
"""Live check of the hub domains and game subdomains. Exit 1 on any failure."""
import sys
import urllib.error
import urllib.request

CHECKS = [
    # (start URL, expected final URL after redirects, or None = just expect HTTP 200)
    ("https://freax.games/", None),
    ("https://rhyflitzer.ch/", None),
    ("https://wipfelkratzer.freax.games/", None),
    ("https://freax.games/game-wipfelkratzer/?x=1", "https://wipfelkratzer.freax.games/?x=1"),
    ("https://github.freaxnx01.ch/game-wipfelkratzer/?x=1", "https://wipfelkratzer.freax.games/?x=1"),
    # 301 to freax.games/games/, whose JS stub (STUB_TARGETS) then forwards to the root
    ("https://github.freaxnx01.ch/games/", "https://freax.games/games/"),
    ("https://rhyflitzer.freaxnx01.ch/nfz/", "https://rhyflitzer.ch/nfz/"),
    ("https://rhyflitzer.freax.games/", "https://rhyflitzer.ch/"),
    ("https://freax.games/wipfelkratzer", "https://freax.games/wipfelkratzer/"),
]
STUB_TARGETS = [
    # stub URL, string its JS forward must contain (urllib does not run JS)
    ("https://freax.games/games/", 'location.replace("/" + location.search + location.hash)'),
    ("https://freax.games/wipfelkratzer/", 'location.replace("https://wipfelkratzer.freax.games/"'),
    ("https://freax.games/rhyflitzer/", 'location.replace("https://rhyflitzer.ch/"'),
    ("https://rhyflitzer.ch/nfz/", 'location.replace("../?utm_source=nfz&utm_medium=artikel"'),
]


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "check_domains"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.status, r.geturl(), r.read().decode("utf-8", "replace")


def main() -> int:
    failed = 0
    for url, want in CHECKS:
        try:
            status, final, _ = fetch(url)
            ok = status == 200 and (want is None or final == want)
            print(f"{'OK ' if ok else 'BAD'} {url} -> {final} ({status})")
        except urllib.error.URLError as e:
            ok = False
            print(f"BAD {url}: {e}")
        failed += not ok
    for url, needle in STUB_TARGETS:
        try:
            _, _, body = fetch(url)
            ok = needle in body
        except urllib.error.URLError as e:
            ok, body = False, str(e)
        print(f"{'OK ' if ok else 'BAD'} {url} forwards with {needle}")
        failed += not ok
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
