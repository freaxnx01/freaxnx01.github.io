# Short Domains Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move the hub and all games to `freax.games` (with short paths `freax.games/<name>`) and Rhyflitzer to `rhyflitzer.ch`, without losing Umami counts or old links.

**Architecture:** GitHub Pages serves every project site under the user site's custom domain, so one `CNAME` change moves all games. Short paths are static redirect stubs generated into the hub repo from the cards in `games/index.html`. Old hostnames are 301-redirected by Cloudflare (manual steps for the maintainer).

**Tech Stack:** static HTML on GitHub Pages, Python 3 scripts + pytest, Playwright (Python) for the browser check, Cloudflare DNS / Redirect Rules (manual).

**Spec:** `docs/superpowers/specs/2026-11-07-short-domains-design.md`

## Global Constraints

- New hub domain: `freax.games`. Rhyflitzer: `rhyflitzer.ch`, plus `rhyflitzer.freax.games` as a Cloudflare redirect only.
- Short path name = repo name without `game-` (`game-wipfelkratzer` → `/wipfelkratzer/`).
- Stubs keep query and hash, like `game-rhyflitzer/prototype/index.html`.
- Reserved top-level names a stub may never take: `games`, `docs`, `scripts`, `testhub`, `tests`, `assets`.
- Umami: new hostnames are **added** to `data-domains` before the switch; old ones stay.
- No wildcard DNS records. No public URL shortener.
- `localStorage` is not migrated (accepted cost).
- Tasks 1–3 must work on the **old** domain; only Task 4 flips the domain, and only after the maintainer's steps M1–M2.
- Conventional Commits; commit trailers as in the repo's history.

## Review Focus

1. A card whose play link is not a `game-*` repo on this site (dogwash on `julia-hase.github.io`) → no stub, no crash. Test in Task 3.
2. A future game named like a reserved directory (`game-games`, `game-docs`) → the generator refuses with a clear error instead of overwriting the hub. Test in Task 3.
3. A short link with query or hash (`/wipfelkratzer?lang=de#x`) → arrives at `/game-wipfelkratzer/?lang=de#x`. Browser test in Task 3.
4. A short path typed without trailing slash (`freax.games/wipfelkratzer`) → GitHub Pages 301s to `/wipfelkratzer/`, then the stub. Checked live in Task 5.
5. Running a script before and after the switch (play links on either domain) → `discover_games` still finds every game. Test in Task 2.

## Maintainer steps (not for agents)

- **M1** (before Task 4): register `freax.games` and `rhyflitzer.ch`; add both zones to Cloudflare.
- **M2** (before Task 4): DNS only (grey cloud) for `freax.games` and `rhyflitzer.ch` apex: A `185.199.108.153`, `185.199.109.153`, `185.199.110.153`, `185.199.111.153`; AAAA `2606:50c0:8000::153`, `2606:50c0:8001::153`, `2606:50c0:8002::153`, `2606:50c0:8003::153`; `www` CNAME `freaxnx01.github.io`.
- **M3** (right after Task 4, once both sites show "HTTPS certificate issued"): in GitHub Pages settings of `freaxnx01.github.io` and `game-rhyflitzer` turn on **Enforce HTTPS**.
- **M4** (after M3): Cloudflare, records proxied (orange cloud), Redirect Rules (301, preserve query string):
  - `github.freaxnx01.ch/*` → `https://freax.games/${1}`
  - `rhyflitzer.freaxnx01.ch/*` → `https://rhyflitzer.ch/${1}`
  - `rhyflitzer.freax.games/*` → `https://rhyflitzer.ch/${1}` (needs a proxied placeholder record, e.g. AAAA `100::`)

---

### Task 1: Umami counts the new hostnames

**Files (other repos, one PR each):**
- Modify: `freaxnx01/game-tschau-sepp` `index.html:14`
- Modify: `freaxnx01/game-toepferscheibe` `index.html:12`
- Modify: `freaxnx01/game-rhyflitzer` `index.html` (Umami tag near the end, `data-domains="rhyflitzer.freaxnx01.ch,github.freaxnx01.ch"`) and `editor/index.html:58`

Line numbers are from 2026-11-07; find the tags with `grep -n 'data-domains=' index.html editor/index.html` on a fresh `git fetch` of each repo's default branch. Check for a `.dc.html` source first (hub `CLAUDE.md`: in dc games the snippet lives in the `.dc.html`).

**Interfaces:** none.

- [ ] **Step 1: Change the attributes**

| File | New value |
|------|-----------|
| game-tschau-sepp `index.html` | `data-domains="github.freaxnx01.ch,freax.games"` |
| game-toepferscheibe `index.html` | `data-domains="github.freaxnx01.ch,freax.games"` |
| game-rhyflitzer `index.html` | `data-domains="rhyflitzer.freaxnx01.ch,github.freaxnx01.ch,rhyflitzer.ch,freax.games"` |
| game-rhyflitzer `editor/index.html` | `data-domains="github.freaxnx01.ch,rhyflitzer.freaxnx01.ch,rhyflitzer.ch,freax.games"` |

- [ ] **Step 2: Verify**

Run in each repo: `grep -o 'data-domains="[^"]*"' index.html editor/index.html 2>/dev/null`
Expected: the values from the table, nothing else changed (`git diff --stat` shows one line per file). In game-rhyflitzer also run its analytics tests: `node --test tests/analytics.test.mjs`. Expected: pass.

- [ ] **Step 3: Commit and open a PR per repo**

```bash
git commit -am "chore(analytics): count visits on the new short domains"
```

---

### Task 2: Scripts know both domains

**Files:**
- Create: `scripts/hubsite.py` (not `site.py`: that name shadows Python's stdlib `site` module)
- Modify: `scripts/add_game_favicons.py:28` (`PLAY_RE`)
- Modify: `scripts/capture_screenshots.py:67` (`BASE_URL`)
- Modify: `scripts/capture_wortduell.py:22,30` (`URL`, docstring)
- Test: `tests/test_hubsite.py`

**Interfaces:**
- Produces: `scripts/hubsite.py` with `SITE: str` (no trailing slash), `SITE_HOSTS: tuple[str, ...]`, `PLAY_RE: re.Pattern` whose group 1 is the repo name, `game_url(repo: str) -> str`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_hubsite.py
"""Tests for scripts/hubsite.py"""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from hubsite import PLAY_RE, SITE, SITE_HOSTS, game_url  # noqa: E402


def test_play_links_on_either_domain_name_the_repo():
    for host in ("github.freaxnx01.ch", "freax.games"):
        m = PLAY_RE.search(f'<a class="card__play" href="https://{host}/game-nibbles/" target="_blank">')
        assert m and m.group(1) == "game-nibbles"


def test_foreign_play_links_do_not_match():
    assert not PLAY_RE.search('href="https://julia-hase.github.io/dogwash/"')
    assert not PLAY_RE.search('href="https://rhyflitzer.ch/"')


def test_game_url_uses_the_current_site():
    assert game_url("game-nibbles") == f"{SITE}/game-nibbles/"
    assert SITE.split("//")[1] in SITE_HOSTS
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest -q tests/test_hubsite.py`
Expected: FAIL with `ModuleNotFoundError: No module named 'hubsite'`

- [ ] **Step 3: Write the module**

```python
# scripts/hubsite.py
"""Where the hub lives. Flip SITE at the domain switch (short-domains plan, Task 4)."""
import re

SITE = "https://github.freaxnx01.ch"
# Both hostnames are accepted when reading play links, so scripts work before and after the switch.
SITE_HOSTS = ("github.freaxnx01.ch", "freax.games")
PLAY_RE = re.compile(
    r'href="https://(?:' + "|".join(re.escape(h) for h in SITE_HOSTS) + r')/(game-[^/"]+)/"'
)


def game_url(repo: str) -> str:
    return f"{SITE}/{repo}/"
```

- [ ] **Step 4: Use it in the three scripts**

`scripts/add_game_favicons.py`: delete line 28 (`PLAY_RE = re.compile(...)`) and add after the other imports:

```python
from hubsite import PLAY_RE
```

`scripts/capture_screenshots.py`: replace `BASE_URL = "https://github.freaxnx01.ch/{repo}/"` with

```python
from hubsite import game_url
```

and in `main()` replace `URL_OVERRIDES.get(repo, BASE_URL.format(repo=repo))` with `URL_OVERRIDES.get(repo, game_url(repo))`.

`scripts/capture_wortduell.py`: replace `URL = "https://github.freaxnx01.ch/game-wortduell/"` with

```python
from hubsite import game_url

URL = game_url("game-wortduell")
```

and change the docstring line `https://github.freaxnx01.ch/game-wortduell/` to `game_url("game-wortduell") (scripts/hubsite.py)`.

All three scripts are run as `python3 scripts/<name>.py`, so `scripts/` is on `sys.path` and the import works.

- [ ] **Step 5: Run the tests**

Run: `python3 -m pytest -q tests/test_hubsite.py tests/test_add_game_favicons.py tests/test_capture_screenshots.py`
Expected: all pass (`test_discover_games_sanity_floor` still finds ≥ 30 games).

- [ ] **Step 6: Commit**

```bash
git add scripts/hubsite.py scripts/add_game_favicons.py scripts/capture_screenshots.py scripts/capture_wortduell.py tests/test_hubsite.py
git commit -m "refactor(scripts): one place for the hub domain, accept freax.games links"
```

---

### Task 3: Short-path stubs

**Files:**
- Create: `scripts/make_short_links.py`
- Create (generated): `<name>/index.html` for every game card
- Test: `tests/test_make_short_links.py`, `tests/test_short_links_browser.py`
- Modify: `CLAUDE.md` (one paragraph under the Games Hub section)

**Interfaces:**
- Consumes: `hubsite.PLAY_RE` (Task 2).
- Produces: `short_links(html: str) -> dict[str, str]` (short name → target URL or root-relative path), `stub_html(target: str) -> str`, `write_stubs(hub_root: Path) -> list[str]`; constant `RESERVED = {"games", "docs", "scripts", "testhub", "tests", "assets"}`. Task 4 reruns `python3 scripts/make_short_links.py`.

Rules:
- Name: from the card's thumbnail `src="assets/game-<name>-icon.png"`; only `game-*` cards get a stub.
- Target: if the play link matches `PLAY_RE` → root-relative `/game-<name>/` (stays on whatever domain serves the hub). Otherwise, if the card is a `game-*` card with an absolute play link elsewhere (Rhyflitzer after Task 4: `https://rhyflitzer.ch/`) → that absolute URL. Cards without a `game-*` thumbnail (dogwash) → no stub.
- Reserved name → `SystemExit` naming the card.
- The script only writes stubs it generated; it marks them with `<meta name="generator" content="make_short_links">` and deletes stale stubs carrying that marker whose card is gone. It never touches a directory without the marker.

- [ ] **Step 1: Write the failing unit tests**

```python
# tests/test_make_short_links.py
"""Tests for scripts/make_short_links.py"""
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from make_short_links import RESERVED, short_links, stub_html, write_stubs  # noqa: E402


def card(icon, href):
    return (f'<article class="card"><img class="card__thumb" src="assets/{icon}">'
            f'<a class="card__play" href="{href}" target="_blank">▶ Play</a></article>')


def test_site_games_get_a_root_relative_target():
    html = card("game-wipfelkratzer-icon.png", "https://github.freaxnx01.ch/game-wipfelkratzer/")
    assert short_links(html) == {"wipfelkratzer": "/game-wipfelkratzer/"}


def test_a_game_on_its_own_domain_gets_that_domain():
    html = card("game-rhyflitzer-icon.png", "https://rhyflitzer.ch/")
    assert short_links(html) == {"rhyflitzer": "https://rhyflitzer.ch/"}


def test_cards_that_are_not_game_repos_are_skipped():
    html = card("dogwash-icon.png", "https://julia-hase.github.io/dogwash/")
    assert short_links(html) == {}


@pytest.mark.parametrize("name", sorted(RESERVED))
def test_reserved_names_are_refused(name):
    html = card(f"game-{name}-icon.png", f"https://freax.games/game-{name}/")
    with pytest.raises(SystemExit, match=name):
        short_links(html)


def test_stub_keeps_query_and_hash():
    html = stub_html("/game-nibbles/")
    assert 'location.replace("/game-nibbles/" + location.search + location.hash)' in html
    assert '<meta name="generator" content="make_short_links">' in html


def test_write_stubs_removes_only_its_own_stale_stubs(tmp_path):
    (tmp_path / "games").mkdir()
    (tmp_path / "games" / "index.html").write_text(
        card("game-nibbles-icon.png", "https://github.freaxnx01.ch/game-nibbles/"))
    (tmp_path / "gone").mkdir()
    (tmp_path / "gone" / "index.html").write_text(stub_html("/game-gone/"))
    (tmp_path / "keep").mkdir()
    (tmp_path / "keep" / "index.html").write_text("<p>hand-made</p>")
    assert write_stubs(tmp_path) == ["nibbles"]
    assert (tmp_path / "nibbles" / "index.html").exists()
    assert not (tmp_path / "gone").exists()
    assert (tmp_path / "keep" / "index.html").exists()


def test_the_real_hub_gets_a_stub_per_game():
    hub = Path(__file__).parent.parent
    links = short_links((hub / "games" / "index.html").read_text())
    assert len(links) >= 40
    assert links["wipfelkratzer"] == "/game-wipfelkratzer/"
    assert "dogwash" not in links
```

- [ ] **Step 2: Run to verify it fails**

Run: `python3 -m pytest -q tests/test_make_short_links.py`
Expected: FAIL with `ModuleNotFoundError: No module named 'make_short_links'`

- [ ] **Step 3: Write the script**

```python
# scripts/make_short_links.py
"""Short paths for the games hub: freax.games/<name> forwards to the game.

One stub <name>/index.html per game card, generated from games/index.html. Run after
adding a card:  python3 scripts/make_short_links.py
Spec: docs/superpowers/specs/2026-11-07-short-domains-design.md
"""
import html as htmllib
import re
import shutil
import sys
from pathlib import Path

from hubsite import PLAY_RE

ARTICLE_RE = re.compile(r'<article class="card"[^>]*>(.*?)</article>', re.DOTALL)
ICON_RE = re.compile(r'<img class="card__thumb" src="assets/game-([a-z0-9-]+)-icon\.png"')
ANY_PLAY_RE = re.compile(r'class="card__play" href="(https://[^"]+)"')
RESERVED = {"games", "docs", "scripts", "testhub", "tests", "assets"}
MARKER = '<meta name="generator" content="make_short_links">'


def short_links(page: str) -> dict[str, str]:
    links = {}
    for block in ARTICLE_RE.findall(page):
        icon = ICON_RE.search(block)
        if not icon:
            continue
        name = icon.group(1)
        if name in RESERVED:
            raise SystemExit(f"game-{name}: short name '{name}' clashes with a hub directory")
        site = PLAY_RE.search(block)
        if site:
            links[name] = f"/{site.group(1)}/"
            continue
        other = ANY_PLAY_RE.search(block)
        if other:
            links[name] = other.group(1)
    return links


def stub_html(target: str) -> str:
    t = htmllib.escape(target)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
{MARKER}
<title>Redirecting…</title>
<meta http-equiv="refresh" content="0; url={t}">
<script>location.replace("{target}" + location.search + location.hash);</script>
</head>
<body>
<p><a href="{t}">Play</a></p>
</body>
</html>
"""


def write_stubs(hub_root: Path) -> list[str]:
    links = short_links((hub_root / "games" / "index.html").read_text())
    for d in hub_root.iterdir():
        stub = d / "index.html"
        if d.is_dir() and d.name not in links and stub.exists() and MARKER in stub.read_text():
            shutil.rmtree(d)
    for name, target in links.items():
        (hub_root / name).mkdir(exist_ok=True)
        (hub_root / name / "index.html").write_text(stub_html(target))
    return sorted(links)


if __name__ == "__main__":
    names = write_stubs(Path(__file__).resolve().parent.parent)
    print(f"{len(names)} short links: " + ", ".join(names))
```

Targets come from the hub's own `games/index.html`, so embedding them in the inline script is safe; `ICON_RE` restricts names to `[a-z0-9-]`.

- [ ] **Step 4: Run the unit tests**

Run: `python3 -m pytest -q tests/test_make_short_links.py`
Expected: all pass.

- [ ] **Step 5: Write the browser test**

```python
# tests/test_short_links_browser.py
"""A generated stub forwards to the game and keeps query and hash. Serves the repo locally."""
import functools
import http.server
import threading
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).parent.parent
STUB = "<!doctype html><title>landed</title>"


def test_short_link_keeps_query_and_hash():
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(ROOT))
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{httpd.server_port}"
    try:
        with sync_playwright() as p:
            b = p.chromium.launch()
            page = b.new_page()
            page.route(f"{base}/game-wipfelkratzer/**",
                       lambda r: r.fulfill(status=200, content_type="text/html", body=STUB))
            page.goto(f"{base}/wipfelkratzer/?lang=de#x")
            page.wait_for_function("() => document.title === 'landed'", timeout=15000)
            assert page.url == f"{base}/game-wipfelkratzer/?lang=de#x"
            b.close()
    finally:
        httpd.shutdown()
```

- [ ] **Step 6: Generate the stubs and run all tests**

Run: `python3 scripts/make_short_links.py`
Expected: `44 short links: …` listing every game, `wipfelkratzer` among them, no `dogwash`.
Run: `python3 -m pytest -q tests/test_make_short_links.py tests/test_short_links_browser.py`
Expected: all pass.

- [ ] **Step 7: Document**

Add to `CLAUDE.md` after the paragraph "Each game lives in its own `game-<name>` repo …":

```markdown
Every card also gets a short path `/<name>/` (repo name without `game-`), a redirect
stub generated by `python3 scripts/make_short_links.py`. Rerun it after adding or
removing a card and commit the stubs with the card.
```

- [ ] **Step 8: Commit**

```bash
git add scripts/make_short_links.py tests/test_make_short_links.py tests/test_short_links_browser.py CLAUDE.md
git add $(python3 -c "import sys;sys.path.insert(0,'scripts');from make_short_links import short_links;print(' '.join(n+'/index.html' for n in short_links(open('games/index.html').read())))")
git commit -m "feat(hub): short paths /<name>/ for every game"
```

---

### Task 4: The switch (only after maintainer steps M1–M2)

**Files:**
- Modify: `CNAME` (hub)
- Modify: `scripts/hubsite.py` (`SITE`)
- Modify: `games/index.html` (44 play links, Rhyflitzer's play link)
- Regenerate: `rhyflitzer/index.html` (via `make_short_links.py`)
- Modify: `CLAUDE.md` (domain mentions)
- Modify (other repo): `freaxnx01/game-rhyflitzer` `CNAME`

**Interfaces:**
- Consumes: `make_short_links.py` (Task 3), `hubsite.SITE` (Task 2).

- [ ] **Step 1: Check the preconditions**

Run: `dig +short A freax.games; dig +short A rhyflitzer.ch`
Expected: the four `185.199.10x.153` addresses for each. If not, stop: M2 is not done.

- [ ] **Step 2: Flip the hub**

```bash
printf 'freax.games\n' > CNAME
sed -i 's|^SITE = "https://github.freaxnx01.ch"|SITE = "https://freax.games"|' scripts/hubsite.py
sed -i 's|href="https://github.freaxnx01.ch/game-rhyflitzer/"|href="https://rhyflitzer.ch/"|' games/index.html
sed -i 's|href="https://github.freaxnx01.ch/game-|href="https://freax.games/game-|g' games/index.html
python3 scripts/make_short_links.py
```

In `CLAUDE.md` replace `github.freaxnx01.ch` with `freax.games` in the first paragraph and the "served at" line, and change the Umami sentence to `data-domains="github.freaxnx01.ch,freax.games"` (keep both).

- [ ] **Step 3: Verify locally**

Run: `grep -c 'https://github.freaxnx01.ch/game-' games/index.html` → Expected: `0`
Run: `grep -c 'href="https://freax.games/game-' games/index.html` → Expected: `43`
Run: `cat rhyflitzer/index.html | grep -o 'location.replace("[^"]*"'` → Expected: `location.replace("https://rhyflitzer.ch/"`
Run: `python3 -m pytest -q tests/test_hubsite.py tests/test_add_game_favicons.py tests/test_capture_screenshots.py tests/test_make_short_links.py tests/test_short_links_browser.py` → Expected: all pass. `discover_games` loses Rhyflitzer (its play link is no longer on the site); `test_discover_games_sanity_floor` still passes (≥ 30). Rhyflitzer already has its own favicon.

- [ ] **Step 4: Commit and merge (hub)**

```bash
git add CNAME scripts/hubsite.py games/index.html rhyflitzer/index.html CLAUDE.md
git commit -m "feat(hub): move to freax.games"
```

Open the PR; merge only with the maintainer's go.

- [ ] **Step 5: Flip Rhyflitzer**

In `freaxnx01/game-rhyflitzer`: `printf 'rhyflitzer.ch\n' > CNAME`, commit `feat(site): move to rhyflitzer.ch`, PR, merge with the maintainer's go. Rhyflitzer's own pages use relative links (`/nfz` stub: `../?utm_source=…`), so nothing else changes there; confirm with `grep -rn 'rhyflitzer.freaxnx01.ch' --include=*.html --include=*.js . | grep -v 'data-domains' | grep -v '^./docs/'` → Expected: no hits that build URLs.

- [ ] **Step 6: Hand over to the maintainer**

Ask the maintainer to do M3 and M4, then run Task 5.

---

### Task 5: Live verification

**Files:**
- Create: `scripts/check_domains.py`

**Interfaces:** none (standalone, stdlib only).

- [ ] **Step 1: Write the check**

```python
# scripts/check_domains.py
"""Live check of the short domains (short-domains plan, Task 5). Exit 1 on any failure."""
import sys
import urllib.error
import urllib.request

CHECKS = [
    # (start URL, expected final URL after redirects, or None = just expect HTTP 200)
    ("https://freax.games/games/", None),
    ("https://rhyflitzer.ch/", None),
    ("https://github.freaxnx01.ch/game-wipfelkratzer/?x=1", "https://freax.games/game-wipfelkratzer/?x=1"),
    ("https://github.freaxnx01.ch/games/", "https://freax.games/games/"),
    ("https://rhyflitzer.freaxnx01.ch/nfz/", "https://rhyflitzer.ch/nfz/"),
    ("https://rhyflitzer.freax.games/", "https://rhyflitzer.ch/"),
    ("https://freax.games/wipfelkratzer", "https://freax.games/wipfelkratzer/"),
]
STUB_TARGETS = [
    # stub URL, string its JS forward must contain
    ("https://freax.games/wipfelkratzer/", 'location.replace("/game-wipfelkratzer/"'),
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
```

- [ ] **Step 2: Run it**

Run: `python3 scripts/check_domains.py`
Expected: every line `OK`, exit 0. A `BAD` on a `github.freaxnx01.ch` or `rhyflitzer.freax*` line means M4 is missing; a certificate error means M3 is not done yet.

- [ ] **Step 3: Umami**

With a realistic user agent (headless Chromium's default UA is filtered as a bot), open `https://freax.games/game-tschau-sepp/?utm_campaign=claude-test` and `https://rhyflitzer.ch/?utm_campaign=claude-test` once each (Playwright, `user_agent=` a desktop Chrome UA). Then query the Umami API (Passbolt „Umami admin stats.freaxnx01.ch", `POST /api/auth/login`, `GET /api/websites/<id>/metrics?type=hostname&startAt=…&endAt=…`) for website `35f395c0-a1ba-4706-ad56-7c95fcc0169f`.
Expected: hostnames `freax.games` and `rhyflitzer.ch` each with ≥ 1. Report that two `claude-test` visits are now in the stats.

- [ ] **Step 4: Commit**

```bash
git add scripts/check_domains.py
git commit -m "test(hub): live check for the short domains"
```
