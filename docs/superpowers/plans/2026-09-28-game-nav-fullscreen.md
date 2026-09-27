# Fullscreen Toggle in `#game-nav` Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship a self-contained fullscreen-toggle snippet for the standard `#game-nav` overlay, a rollout script that injects it into every `freaxnx01/game-*` repo and releases each as a minor version, and the updated canonical nav template.

**Architecture:** One HTML snippet (`scripts/fullscreen_snippet.html`) holds a marker-delimited IIFE that inserts a `<button id="fs-toggle">` into whatever `#game-nav` exists and re-asserts it for 10 s (survives dc bundles' `documentElement.replaceWith()`). `scripts/add_fullscreen_toggle.py` has pure, unit-tested text functions plus a git flow over script-owned clean clones in `~/.cache/game-rollout/`. The canonical template embeds the snippet verbatim (test-enforced).

**Tech Stack:** Vanilla JS (ES5, no build), Python 3 stdlib + existing `scripts/add_game_favicons.py`, pytest 9, Playwright (Python, sync API) 1.48, git, git-cliff.

**Spec:** `docs/superpowers/specs/2026-09-28-game-nav-fullscreen-design.md`

## Global Constraints

- Snippet markers, exact: `<!-- game-nav-fullscreen:start -->` … `<!-- game-nav-fullscreen:end -->`.
- Button: `id="fs-toggle"`, `type="button"`; text `⛶` (U+26F6) / `✕` (U+2715); `title` + `aria-label` `Fullscreen` / `Exit fullscreen`; `aria-pressed` `false` / `true`.
- Button style: `background:none;border:0;padding:0;margin:0;cursor:pointer;color:#8fd8e8;font:inherit;line-height:1`. Separator: `<span aria-hidden="true" style="color:#5a6072">·</span>`.
- Placement: separator + button directly after `#version-badge` when it is a child of `#game-nav`; else button + separator as the nav's first children.
- Hidden entirely (no button, no separator) when neither `document.fullscreenEnabled` nor `document.webkitFullscreenEnabled` is true.
- Fullscreen target `document.documentElement`; `btn.blur()` after every click.
- Re-assertion: immediately, `DOMContentLoaded`, `load`, and `setInterval` 250 ms × 40 ticks.
- Feature commit message: `feat(nav): add fullscreen toggle`. Release commit: `chore(release): vX.Y.0`; minor bump; tag `vX.Y.0`.
- Served file: `docs/index.html` for `game-gorillazz`, `index.html` otherwise.
- Clones: `~/.cache/game-rollout/<repo>` by default (never the sibling working copies).
- `GIT_TERMINAL_PROMPT=0` for every git call.
- The implementing agent does **not** run the real rollout (no pushes to `game-*` repos). That is the manual section at the end.

## Review Focus

- A page with a `</body>` inside a string/template before the real one → snippet goes before the **last** `</body>` (case-insensitive). Pinned in Task 2.
- A page whose only `game-nav` mention is our own already-injected snippet → treated as having **no** nav. Pinned in Task 2.
- Re-run after a run that committed/tagged in the cache but failed to push → stale local tag must not block the re-run. Pinned in Task 3.
- Remote already has the computed tag `vX.Y.0` → repo fails with a clear status and nothing is pushed. Pinned in Task 3.
- Keyboard game after clicking ⛶ → button is not left focused (Space/Enter must not re-toggle). Pinned in Task 1.

---

## File structure

- Create `scripts/fullscreen_snippet.html` — the snippet; single source of truth.
- Create `scripts/add_fullscreen_toggle.py` — pure functions + git flow + CLI.
- Create `tests/test_fullscreen_snippet_browser.py` — Playwright tests of the snippet.
- Create `tests/test_add_fullscreen_toggle.py` — unit + git-integration tests.
- Modify `docs/superpowers/specs/2026-07-13-game-card-feedback-star-snippet.html` — append the snippet.

Setup (once, before Task 1):

```bash
pip install -r scripts/requirements.txt
python -m playwright install chromium
```

Git commits inside tests need an identity; tests set `GIT_AUTHOR_*`/`GIT_COMMITTER_*` themselves (CI runners may have no git identity).

---

### Task 1: Fullscreen snippet + browser tests

**Files:**
- Create: `scripts/fullscreen_snippet.html`
- Test: `tests/test_fullscreen_snippet_browser.py`

**Interfaces:**
- Produces: `scripts/fullscreen_snippet.html` — starts with `<!-- game-nav-fullscreen:start -->`, ends with `<!-- game-nav-fullscreen:end -->`. Tasks 2 and 4 read it as text.

- [ ] **Step 1: Write the failing test**

`tests/test_fullscreen_snippet_browser.py`:

```python
"""Headless tests for scripts/fullscreen_snippet.html (issue #25)."""
from pathlib import Path

import pytest
from playwright.sync_api import sync_playwright

SNIPPET = (Path(__file__).parent.parent / "scripts" / "fullscreen_snippet.html").read_text()

NAV_WITH_BADGE = """
<nav id="game-nav">
  <span id="version-badge"><a>v0.3.1</a></span>
  <span aria-hidden="true">·</span>
  <a id="more" href="#">More Games…</a>
</nav>"""

NAV_NO_BADGE = """
<nav id="game-nav">
  <a id="more" href="#">More Games…</a>
</nav>"""

FS_SUPPORTED = """
Object.defineProperty(Document.prototype, 'fullscreenEnabled', {get: () => true, configurable: true});
window.__fsCalls = 0;
Element.prototype.requestFullscreen = function () { window.__fsCalls++; return Promise.resolve(); };
"""

FS_UNSUPPORTED = """
Object.defineProperty(Document.prototype, 'fullscreenEnabled', {get: () => false, configurable: true});
Object.defineProperty(Document.prototype, 'webkitFullscreenEnabled', {get: () => false, configurable: true});
"""


def page_html(body: str) -> str:
    return f"<!doctype html><html><head><meta charset='utf-8'></head><body>{body}{SNIPPET}</body></html>"


@pytest.fixture(scope="module")
def browser():
    with sync_playwright() as p:
        b = p.chromium.launch()
        yield b
        b.close()


def open_page(browser, body, init_script):
    page = browser.new_page()
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.add_init_script(init_script)
    page.set_content(page_html(body))
    return page, errors


def test_button_sits_right_after_badge_separator(browser):
    page, errors = open_page(browser, NAV_WITH_BADGE, FS_SUPPORTED)
    order = page.evaluate(
        "Array.from(document.getElementById('game-nav').children).map(e => e.id || e.textContent.trim())"
    )
    assert order[:4] == ["version-badge", "·", "fs-toggle", "·"]
    btn = page.locator("#fs-toggle")
    assert btn.text_content() == "⛶"
    assert btn.get_attribute("aria-label") == "Fullscreen"
    assert btn.get_attribute("title") == "Fullscreen"
    assert btn.get_attribute("aria-pressed") == "false"
    assert btn.get_attribute("type") == "button"
    assert errors == []


def test_button_is_first_when_no_badge(browser):
    page, errors = open_page(browser, NAV_NO_BADGE, FS_SUPPORTED)
    order = page.evaluate(
        "Array.from(document.getElementById('game-nav').children).map(e => e.id || e.textContent.trim())"
    )
    assert order[:3] == ["fs-toggle", "·", "more"]
    assert errors == []


def test_hidden_when_fullscreen_unsupported(browser):
    page, errors = open_page(browser, NAV_WITH_BADGE, FS_UNSUPPORTED)
    page.wait_for_timeout(600)
    assert page.locator("#fs-toggle").count() == 0
    assert page.evaluate("document.getElementById('game-nav').children.length") == 3
    assert errors == []


def test_click_requests_fullscreen_once_and_blurs(browser):
    page, errors = open_page(browser, NAV_WITH_BADGE, FS_SUPPORTED)
    page.locator("#fs-toggle").click()
    assert page.evaluate("window.__fsCalls") == 1
    assert page.evaluate("document.activeElement && document.activeElement.id") != "fs-toggle"
    assert errors == []


def test_state_flips_on_fullscreenchange(browser):
    page, errors = open_page(browser, NAV_WITH_BADGE, FS_SUPPORTED)
    page.evaluate("""
        Object.defineProperty(Document.prototype, 'fullscreenElement',
            {get: () => document.documentElement, configurable: true});
        document.dispatchEvent(new Event('fullscreenchange'));
    """)
    btn = page.locator("#fs-toggle")
    assert btn.text_content() == "✕"
    assert btn.get_attribute("aria-label") == "Exit fullscreen"
    assert btn.get_attribute("aria-pressed") == "true"
    assert errors == []


def test_readded_after_nav_is_recreated(browser):
    page, errors = open_page(browser, NAV_WITH_BADGE, FS_SUPPORTED)
    page.evaluate("""
        document.getElementById('game-nav').remove();
        const nav = document.createElement('nav');
        nav.id = 'game-nav';
        nav.innerHTML = '<span id="version-badge">v1</span><span aria-hidden="true">·</span><a>More</a>';
        document.body.appendChild(nav);
    """)
    page.wait_for_selector("#game-nav #fs-toggle", timeout=1000)
    assert page.locator("#fs-toggle").count() == 1
    assert errors == []


def test_no_nav_no_button_no_error(browser):
    page, errors = open_page(browser, "<main>game</main>", FS_SUPPORTED)
    page.wait_for_timeout(600)
    assert page.locator("#fs-toggle").count() == 0
    assert errors == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_fullscreen_snippet_browser.py -v`
Expected: collection ERROR — `FileNotFoundError: ... scripts/fullscreen_snippet.html`

- [ ] **Step 3: Write the snippet**

`scripts/fullscreen_snippet.html`:

```html
<!-- game-nav-fullscreen:start -->
<script>
// Fullscreen toggle for #game-nav (freaxnx01.github.io issue #25).
// Self-contained: inserts a button into whatever #game-nav exists and
// re-asserts it for 10 s, so dc bundles that replaceWith() the DOM keep it.
(function () {
  var d = document;
  if (!(d.fullscreenEnabled || d.webkitFullscreenEnabled)) return;
  function fsEl() { return d.fullscreenElement || d.webkitFullscreenElement || null; }
  function sync() {
    var b = d.getElementById("fs-toggle");
    if (!b) return;
    var on = !!fsEl();
    b.textContent = on ? "✕" : "⛶";
    b.title = on ? "Exit fullscreen" : "Fullscreen";
    b.setAttribute("aria-label", b.title);
    b.setAttribute("aria-pressed", on ? "true" : "false");
  }
  function toggle() {
    var p;
    try {
      if (fsEl()) {
        p = (d.exitFullscreen || d.webkitExitFullscreen).call(d);
      } else {
        var r = d.documentElement;
        p = (r.requestFullscreen || r.webkitRequestFullscreen).call(r);
      }
    } catch (e) {}
    if (p && p.catch) p.catch(function () {});
  }
  function sep() {
    var s = d.createElement("span");
    s.setAttribute("aria-hidden", "true");
    s.style.cssText = "color:#5a6072";
    s.textContent = "·";
    return s;
  }
  function ensure() {
    var nav = d.getElementById("game-nav");
    if (!nav || d.getElementById("fs-toggle")) return;
    var b = d.createElement("button");
    b.id = "fs-toggle";
    b.type = "button";
    b.style.cssText = "background:none;border:0;padding:0;margin:0;cursor:pointer;color:#8fd8e8;font:inherit;line-height:1";
    // blur(): keyboard games would otherwise re-trigger the focused button
    // with Enter/Space and silently toggle fullscreen back.
    b.addEventListener("click", function () { toggle(); b.blur(); });
    var badge = d.getElementById("version-badge");
    if (badge && badge.parentNode === nav) {
      nav.insertBefore(b, badge.nextSibling);
      nav.insertBefore(sep(), b);
    } else {
      nav.insertBefore(sep(), nav.firstChild);
      nav.insertBefore(b, nav.firstChild);
    }
    sync();
  }
  d.addEventListener("fullscreenchange", sync);
  d.addEventListener("webkitfullscreenchange", sync);
  d.addEventListener("DOMContentLoaded", ensure);
  window.addEventListener("load", ensure);
  ensure();
  var n = 0, iv = setInterval(function () { ensure(); if (++n >= 40) clearInterval(iv); }, 250);
})();
</script>
<!-- game-nav-fullscreen:end -->
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_fullscreen_snippet_browser.py -v`
Expected: 7 passed

- [ ] **Step 5: Commit**

```bash
git add scripts/fullscreen_snippet.html tests/test_fullscreen_snippet_browser.py
git commit -m "feat(games): fullscreen toggle snippet for game-nav (#25)"
```

---

### Task 2: Pure text functions

**Files:**
- Create: `scripts/add_fullscreen_toggle.py`
- Test: `tests/test_add_fullscreen_toggle.py`

**Interfaces:**
- Consumes: `scripts/fullscreen_snippet.html` (Task 1).
- Produces (module `add_fullscreen_toggle`):
  - `START_MARKER: str`, `END_MARKER: str`, `SNIPPET_PATH: Path`
  - `load_snippet() -> str` — file content, `.strip()`ped
  - `inject_snippet(html: str, snippet: str | None = None) -> tuple[str, bool]`
  - `has_game_nav(html: str) -> bool`
  - `read_version(version_js: str) -> str | None`
  - `write_version(version_js: str, version: str) -> str`
  - `bump_minor(version: str) -> str`
  - `served_file(repo: str) -> str`

- [ ] **Step 1: Write the failing test**

`tests/test_add_fullscreen_toggle.py`:

```python
"""Tests for scripts/add_fullscreen_toggle.py (issue #25)."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from add_fullscreen_toggle import (  # noqa: E402
    END_MARKER,
    START_MARKER,
    bump_minor,
    has_game_nav,
    inject_snippet,
    load_snippet,
    read_version,
    served_file,
    write_version,
)

SNIP = f"{START_MARKER}\n<script>x()</script>\n{END_MARKER}"


def test_load_snippet_is_marker_delimited():
    s = load_snippet()
    assert s.startswith(START_MARKER)
    assert s.endswith(END_MARKER)


def test_inject_before_body_close():
    html = "<html><body><nav id='game-nav'></nav></body></html>"
    new, changed = inject_snippet(html, SNIP)
    assert changed
    assert new == f"<html><body><nav id='game-nav'></nav>{SNIP}\n</body></html>"


def test_inject_uses_last_body_close_case_insensitive():
    html = "<body><script>var t='</body>';</script></BODY></html>"
    new, changed = inject_snippet(html, SNIP)
    assert changed
    assert new == f"<body><script>var t='</body>';</script>{SNIP}\n</BODY></html>"


def test_inject_is_idempotent():
    html = "<body></body>"
    once, _ = inject_snippet(html, SNIP)
    twice, changed = inject_snippet(once, SNIP)
    assert not changed
    assert twice == once


def test_inject_replaces_outdated_block():
    old = f"<body>{START_MARKER}\n<script>old()</script>\n{END_MARKER}\n</body>"
    new, changed = inject_snippet(old, SNIP)
    assert changed
    assert new == f"<body>{SNIP}\n</body>"
    assert new.count(START_MARKER) == 1


def test_inject_without_body_raises():
    with pytest.raises(ValueError, match="</body>"):
        inject_snippet("<div>no body close</div>", SNIP)


def test_inject_defaults_to_real_snippet():
    new, changed = inject_snippet("<body></body>")
    assert changed
    assert load_snippet() in new


def test_has_game_nav_static_and_selfhealing():
    assert has_game_nav('<nav id="game-nav">')
    assert has_game_nav('nav.id = "game-nav";')
    assert not has_game_nav("<body>plain</body>")


def test_has_game_nav_ignores_own_snippet():
    html = f"<body>{load_snippet()}\n</body>"
    assert not has_game_nav(html)


def test_read_and_write_version():
    js = '// mirror\nwindow.GAME_VERSION = "0.11.1";\n'
    assert read_version(js) == "0.11.1"
    assert write_version(js, "0.12.0") == '// mirror\nwindow.GAME_VERSION = "0.12.0";\n'
    assert read_version("// nothing here\n") is None


@pytest.mark.parametrize("old,new", [
    ("0.1.0", "0.2.0"),
    ("0.11.1", "0.12.0"),
    ("1.9.9", "1.10.0"),
])
def test_bump_minor(old, new):
    assert bump_minor(old) == new


def test_bump_minor_rejects_garbage():
    with pytest.raises(ValueError):
        bump_minor("v1.2")


def test_served_file():
    assert served_file("game-gorillazz") == "docs/index.html"
    assert served_file("game-nibbles") == "index.html"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_add_fullscreen_toggle.py -v`
Expected: collection ERROR — `ModuleNotFoundError: No module named 'add_fullscreen_toggle'`

- [ ] **Step 3: Write minimal implementation**

`scripts/add_fullscreen_toggle.py`:

```python
#!/usr/bin/env python3
"""Add the fullscreen toggle to #game-nav in every game-<name> repo on the hub.

For each game listed in games/index.html, injects scripts/fullscreen_snippet.html
before </body> of the repo's served page, commits it, releases the game as a
minor version (version.js + git-cliff CHANGELOG + tag), and pushes.

Works on script-owned clean clones in ~/.cache/game-rollout/ — never on the
sibling working copies, which may carry in-progress branches.

Re-running is safe: a page that already carries the current snippet is skipped.

Usage:
    pip install -r scripts/requirements.txt
    python3 scripts/add_fullscreen_toggle.py [--dry-run] [--only REPO[,REPO...]] [--clones-root PATH]

Design: docs/superpowers/specs/2026-09-28-game-nav-fullscreen-design.md (#25)
"""
import re
from pathlib import Path

START_MARKER = "<!-- game-nav-fullscreen:start -->"
END_MARKER = "<!-- game-nav-fullscreen:end -->"
SNIPPET_PATH = Path(__file__).resolve().parent / "fullscreen_snippet.html"

BLOCK_RE = re.compile(re.escape(START_MARKER) + r".*?" + re.escape(END_MARKER), re.DOTALL)
VERSION_RE = re.compile(r'(window\.GAME_VERSION\s*=\s*")(\d+\.\d+\.\d+)(")')
SEMVER_RE = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")

# Pages served from somewhere other than the repo root's index.html.
SERVED_FILE = {"game-gorillazz": "docs/index.html"}


def load_snippet() -> str:
    return SNIPPET_PATH.read_text().strip()


def inject_snippet(html: str, snippet: str | None = None) -> tuple[str, bool]:
    """Put the snippet before the last </body>, or refresh an existing block."""
    snippet = (snippet if snippet is not None else load_snippet()).strip()
    if BLOCK_RE.search(html):
        new = BLOCK_RE.sub(lambda _m: snippet, html, count=1)
        return new, new != html
    idx = html.lower().rfind("</body>")
    if idx == -1:
        raise ValueError("no </body> tag found")
    return html[:idx] + snippet + "\n" + html[idx:], True


def has_game_nav(html: str) -> bool:
    """True if the page has a game-nav (static markup or self-healing IIFE).

    Our own snippet mentions "game-nav" too, so it is stripped first.
    """
    return "game-nav" in BLOCK_RE.sub("", html)


def read_version(version_js: str) -> str | None:
    m = VERSION_RE.search(version_js)
    return m.group(2) if m else None


def write_version(version_js: str, version: str) -> str:
    return VERSION_RE.sub(lambda m: m.group(1) + version + m.group(3), version_js, count=1)


def bump_minor(version: str) -> str:
    m = SEMVER_RE.match(version)
    if not m:
        raise ValueError(f"not a X.Y.Z version: {version!r}")
    major, minor, _patch = (int(x) for x in m.groups())
    return f"{major}.{minor + 1}.0"


def served_file(repo: str) -> str:
    return SERVED_FILE.get(repo, "index.html")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_add_fullscreen_toggle.py -v`
Expected: all passed (15)

- [ ] **Step 5: Commit**

```bash
git add scripts/add_fullscreen_toggle.py tests/test_add_fullscreen_toggle.py
git commit -m "feat(scripts): pure helpers for the fullscreen rollout (#25)"
```

---

### Task 3: Git flow, release, and CLI

**Files:**
- Modify: `scripts/add_fullscreen_toggle.py` (append below the pure functions)
- Test: `tests/test_add_fullscreen_toggle.py` (append)

**Interfaces:**
- Consumes: everything from Task 2; `discover_games(hub_root: Path) -> list[dict]` and `default_branch(repo_path: Path) -> str` from `scripts/add_game_favicons.py`.
- Produces:
  - `REMOTE_BASE = "https://github.com/freaxnx01"`, `DEFAULT_CLONES_ROOT = Path.home() / ".cache" / "game-rollout"`
  - `ensure_clean_clone(repo: str, clones_root: Path, remote_base: str = REMOTE_BASE) -> tuple[Path, str]`
  - `process_repo(repo: str, clones_root: Path, remote_base: str = REMOTE_BASE, dry_run: bool = False) -> str` — returns a status beginning with `succeeded`, `skipped`, `would`, or `failed`.
  - `main(argv: list[str] | None = None) -> int`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_add_fullscreen_toggle.py`:

```python
import shutil
import subprocess

from add_fullscreen_toggle import process_repo  # noqa: E402

needs_cliff = pytest.mark.skipif(shutil.which("git-cliff") is None, reason="git-cliff not installed")

CLIFF_TOML = '''[changelog]
header = "# Changelog\\n"
body = """
{% if version %}## [{{ version | trim_start_matches(pat="v") }}]{% else %}## [Unreleased]{% endif %}
{% for commit in commits %}- {{ commit.message | split(pat="\\n") | first }}
{% endfor %}"""
trim = true

[git]
conventional_commits = true
filter_unconventional = false
tag_pattern = "v[0-9].*"
'''

GAME_HTML = """<!doctype html><html><body>
<nav id="game-nav"><span id="version-badge"></span></nav>
</body></html>
"""


@pytest.fixture
def git_identity(monkeypatch):
    for k, v in {
        "GIT_AUTHOR_NAME": "Test", "GIT_AUTHOR_EMAIL": "test@example.com",
        "GIT_COMMITTER_NAME": "Test", "GIT_COMMITTER_EMAIL": "test@example.com",
    }.items():
        monkeypatch.setenv(k, v)


def git(cwd, *args):
    return subprocess.run(["git", "-C", str(cwd), *args], check=True, capture_output=True, text=True).stdout


@pytest.fixture
def remote(tmp_path, git_identity):
    """A bare remote game-demo.git seeded with a game at v0.3.1."""
    base = tmp_path / "remotes"
    bare = base / "game-demo.git"
    git(tmp_path, "init", "-q", "--bare", "-b", "main", str(bare))
    seed = tmp_path / "seed"
    git(tmp_path, "clone", "-q", str(bare), str(seed))
    (seed / "index.html").write_text(GAME_HTML)
    (seed / "version.js").write_text('window.GAME_VERSION = "0.3.1";\n')
    (seed / "cliff.toml").write_text(CLIFF_TOML)
    (seed / "CHANGELOG.md").write_text("# Changelog\n")
    git(seed, "add", ".")
    git(seed, "commit", "-q", "-m", "chore(release): v0.3.1")
    git(seed, "tag", "v0.3.1")
    git(seed, "push", "-q", "--follow-tags", "origin", "main")
    return {"base": f"file://{base}", "bare": bare, "clones": tmp_path / "clones", "tmp": tmp_path}


def remote_file(remote, path, ref="main"):
    return git(remote["bare"], "show", f"{ref}:{path}")


@needs_cliff
def test_process_repo_injects_releases_and_pushes(remote):
    status = process_repo("game-demo", remote["clones"], remote_base=remote["base"])
    assert status.startswith("succeeded"), status
    assert "v0.4.0" in status
    assert "game-nav-fullscreen:start" in remote_file(remote, "index.html")
    assert '"0.4.0"' in remote_file(remote, "version.js")
    assert "0.4.0" in remote_file(remote, "CHANGELOG.md")
    assert "v0.4.0" in git(remote["bare"], "tag", "--list")
    log = git(remote["bare"], "log", "--format=%s", "-2", "main").splitlines()
    assert log == ["chore(release): v0.4.0", "feat(nav): add fullscreen toggle"]


@needs_cliff
def test_process_repo_rerun_is_noop(remote):
    process_repo("game-demo", remote["clones"], remote_base=remote["base"])
    head = git(remote["bare"], "rev-parse", "main")
    status = process_repo("game-demo", remote["clones"], remote_base=remote["base"])
    assert status == "skipped: up to date"
    assert git(remote["bare"], "rev-parse", "main") == head


@needs_cliff
def test_stale_local_tag_from_failed_push_does_not_block(remote):
    # A previous run tagged locally, then the push failed.
    clone = remote["clones"] / "game-demo"
    git(remote["tmp"], "clone", "-q", f"{remote['base']}/game-demo.git", str(clone))
    git(clone, "tag", "v0.4.0")
    status = process_repo("game-demo", remote["clones"], remote_base=remote["base"])
    assert status.startswith("succeeded"), status
    assert "v0.4.0" in git(remote["bare"], "tag", "--list")


def test_existing_remote_tag_fails_without_pushing(remote):
    seed = remote["tmp"] / "seed"
    git(seed, "tag", "v0.4.0")
    git(seed, "push", "-q", "origin", "v0.4.0")
    head = git(remote["bare"], "rev-parse", "main")
    status = process_repo("game-demo", remote["clones"], remote_base=remote["base"])
    assert status.startswith("failed"), status
    assert "v0.4.0" in status and "exists" in status
    assert git(remote["bare"], "rev-parse", "main") == head


def test_dry_run_touches_nothing(remote):
    head = git(remote["bare"], "rev-parse", "main")
    status = process_repo("game-demo", remote["clones"], remote_base=remote["base"], dry_run=True)
    assert status == "would update → v0.4.0 (dry-run)"
    assert git(remote["bare"], "rev-parse", "main") == head
    assert "game-nav-fullscreen" not in (remote["clones"] / "game-demo" / "index.html").read_text()


def test_page_without_nav_is_skipped(remote):
    seed = remote["tmp"] / "seed"
    (seed / "index.html").write_text("<html><body>no nav</body></html>")
    git(seed, "commit", "-q", "-am", "chore: drop nav")
    git(seed, "push", "-q", "origin", "main")
    status = process_repo("game-demo", remote["clones"], remote_base=remote["base"])
    assert status == "skipped: no game-nav"


def test_no_version_js_commits_without_release(remote):
    seed = remote["tmp"] / "seed"
    git(seed, "rm", "-q", "version.js")
    git(seed, "commit", "-q", "-m", "chore: drop version")
    git(seed, "push", "-q", "origin", "main")
    status = process_repo("game-demo", remote["clones"], remote_base=remote["base"])
    assert status == "succeeded (no release: no version.js)"
    assert git(remote["bare"], "log", "--format=%s", "-1", "main").strip() == "feat(nav): add fullscreen toggle"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_add_fullscreen_toggle.py -v`
Expected: collection ERROR — `ImportError: cannot import name 'process_repo'`

- [ ] **Step 3: Write the implementation**

Append to `scripts/add_fullscreen_toggle.py` (move the new imports to the top of the file, next to `import re`):

```python
import argparse
import os
import subprocess
import sys

from add_game_favicons import default_branch, discover_games

REMOTE_BASE = "https://github.com/freaxnx01"
DEFAULT_CLONES_ROOT = Path.home() / ".cache" / "game-rollout"
FEAT_MSG = "feat(nav): add fullscreen toggle"


def _git(repo_path: Path, *args: str) -> str:
    # Env built per call so a caller's GIT_* identity/overrides are honoured.
    env = {**os.environ, "GIT_TERMINAL_PROMPT": "0"}
    return subprocess.run(
        ["git", "-C", str(repo_path), *args],
        check=True, capture_output=True, text=True, env=env,
    ).stdout


def ensure_clean_clone(repo: str, clones_root: Path, remote_base: str = REMOTE_BASE) -> tuple[Path, str]:
    """Clone, or hard-reset the script-owned clone to origin's default branch.

    --prune-tags drops local tags that the remote lacks, so a run that tagged
    locally and then failed to push does not block the next run.
    """
    repo_path = clones_root / repo
    if not repo_path.exists():
        clones_root.mkdir(parents=True, exist_ok=True)
        _git(clones_root, "clone", "-q", f"{remote_base}/{repo}.git", str(repo_path))
    else:
        _git(repo_path, "fetch", "-q", "--prune", "--prune-tags", "--tags", "origin")
    branch = default_branch(repo_path)
    _git(repo_path, "checkout", "-q", "-B", branch, f"origin/{branch}")
    _git(repo_path, "reset", "-q", "--hard", f"origin/{branch}")
    _git(repo_path, "clean", "-q", "-fdx")
    return repo_path, branch


def process_repo(repo: str, clones_root: Path, remote_base: str = REMOTE_BASE, dry_run: bool = False) -> str:
    try:
        repo_path, branch = ensure_clean_clone(repo, clones_root, remote_base)
    except subprocess.CalledProcessError as e:
        return f"failed: clone/fetch error: {e.stderr.strip()[:200]}"

    page_rel = served_file(repo)
    page_path = repo_path / page_rel
    if not page_path.exists():
        return f"failed: {page_rel} not found"
    html = page_path.read_text()
    if not has_game_nav(html):
        return "skipped: no game-nav"
    try:
        new_html, changed = inject_snippet(html)
    except ValueError as e:
        return f"failed: {e}"
    if not changed:
        return "skipped: up to date"

    version_path = repo_path / "version.js"
    version_js = version_path.read_text() if version_path.exists() else ""
    current = read_version(version_js)
    new_version = bump_minor(current) if current else None
    tag = f"v{new_version}" if new_version else None

    if tag:
        try:
            if _git(repo_path, "ls-remote", "--tags", "origin", f"refs/tags/{tag}").strip():
                return f"failed: tag {tag} already exists on origin"
        except subprocess.CalledProcessError as e:
            return f"failed: ls-remote error: {e.stderr.strip()[:200]}"

    if dry_run:
        return f"would update → {tag} (dry-run)" if tag else "would update, no release: no version.js (dry-run)"

    try:
        page_path.write_text(new_html)
        _git(repo_path, "add", page_rel)
        _git(repo_path, "commit", "-q", "-m", FEAT_MSG)
        if tag:
            version_path.write_text(write_version(version_js, new_version))
            subprocess.run(
                ["git-cliff", "--tag", tag, "-o", "CHANGELOG.md"],
                cwd=repo_path, check=True, capture_output=True, text=True,
            )
            _git(repo_path, "add", "version.js", "CHANGELOG.md")
            _git(repo_path, "commit", "-q", "-m", f"chore(release): {tag}")
            _git(repo_path, "tag", tag)
        _git(repo_path, "push", "-q", "--follow-tags", "origin", branch)
    except subprocess.CalledProcessError as e:
        return f"failed: {' '.join(e.cmd[:3])}: {(e.stderr or '').strip()[:200]}"

    return f"succeeded → {tag}" if tag else "succeeded (no release: no version.js)"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dry-run", action="store_true",
                        help="Report what would change without writing, committing, tagging, or pushing.")
    parser.add_argument("--only", default=None,
                        help="Comma-separated list of repo names to process (default: all).")
    parser.add_argument("--clones-root", type=Path, default=DEFAULT_CLONES_ROOT,
                        help=f"Where the script keeps its own clean clones (default: {DEFAULT_CLONES_ROOT}).")
    args = parser.parse_args(argv)

    hub_root = Path(__file__).resolve().parent.parent
    repos = [g["repo"] for g in discover_games(hub_root)]
    if args.only:
        wanted = {r.strip() for r in args.only.split(",")}
        missing = wanted - set(repos)
        if missing:
            print(f"warning: not found in games/index.html: {sorted(missing)}", file=sys.stderr)
        repos = [r for r in repos if r in wanted]

    results = []
    for repo in repos:
        try:
            status = process_repo(repo, args.clones_root, dry_run=args.dry_run)
        except Exception as e:  # keep going; one bad repo must not stop the batch
            status = f"failed: {type(e).__name__}: {e}"
        results.append((repo, status))
        print(f"{repo}: {status}", flush=True)

    def count(prefix):
        return sum(1 for _, s in results if s.startswith(prefix))

    print(f"\n{len(results)} repos — succeeded {count('succeeded')}, would {count('would')}, "
          f"skipped {count('skipped')}, failed {count('failed')}")
    return 1 if count("failed") else 0


if __name__ == "__main__":
    sys.exit(main())
```

Note: the test for `test_existing_remote_tag_fails_without_pushing`, `test_dry_run_touches_nothing`, `test_page_without_nav_is_skipped`, `test_no_version_js_commits_without_release` do not need git-cliff; the others are skipped when it is absent. If `git-cliff` rejects the test's `CLIFF_TOML`, fix the fixture's TOML (not the script) until `git cliff --tag v0.4.0 -o CHANGELOG.md` works in the seed repo.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_add_fullscreen_toggle.py -v`
Expected: all passed (git-cliff tests skipped only if git-cliff is not installed — install it with `pip install git-cliff` to run them)

Also smoke-test the CLI against the real hub card list without touching any repo:

Run: `python3 scripts/add_fullscreen_toggle.py --help`
Expected: usage text listing `--dry-run`, `--only`, `--clones-root`.

- [ ] **Step 5: Commit**

```bash
git add scripts/add_fullscreen_toggle.py tests/test_add_fullscreen_toggle.py
git commit -m "feat(scripts): fullscreen rollout git flow and release (#25)"
```

---

### Task 4: Canonical nav template carries the snippet

**Files:**
- Modify: `docs/superpowers/specs/2026-07-13-game-card-feedback-star-snippet.html` (header comment + append at end)
- Test: `tests/test_add_fullscreen_toggle.py` (append)

**Interfaces:**
- Consumes: `load_snippet()` (Task 2).

- [ ] **Step 1: Write the failing test**

Append to `tests/test_add_fullscreen_toggle.py`:

```python
TEMPLATE = Path(__file__).parent.parent / "docs" / "superpowers" / "specs" / "2026-07-13-game-card-feedback-star-snippet.html"


def test_canonical_template_contains_snippet_verbatim():
    assert load_snippet() in TEMPLATE.read_text()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_add_fullscreen_toggle.py::test_canonical_template_contains_snippet_verbatim -v`
Expected: FAIL (`assert ... in ...`)

- [ ] **Step 3: Update the template**

In the template's top comment block, after the `TWO VARIANTS below — pick ONE:` list (before the closing `===… -->` line), add:

```
     THEN, for either variant, also paste the FULLSCREEN TOGGLE block at the
     very end of this file (right after the variant, still before </body>).
     It adds a ⛶ button to #game-nav at runtime and is identical for A and B.
     Source of truth: scripts/fullscreen_snippet.html (issue #25) — keep this
     copy in sync (tests/test_add_fullscreen_toggle.py enforces it).
```

At the end of the file append a heading comment and then the **exact** contents of `scripts/fullscreen_snippet.html`:

```html


<!-- ===== FULLSCREEN TOGGLE — paste after EITHER variant ===== -->
```

followed by the snippet (copy it with `cat scripts/fullscreen_snippet.html >> docs/superpowers/specs/2026-07-13-game-card-feedback-star-snippet.html` after adding the heading line, so it is byte-identical).

- [ ] **Step 4: Run all tests**

Run: `python -m pytest tests/ -v`
Expected: all passed (git-cliff tests may be skipped if git-cliff is absent)

- [ ] **Step 5: Commit**

```bash
git add docs/superpowers/specs/2026-07-13-game-card-feedback-star-snippet.html tests/test_add_fullscreen_toggle.py
git commit -m "docs(games): canonical game-nav template carries the fullscreen toggle (#25)"
```

---

## Post-merge rollout (manual — NOT for the implementing agent)

The `ai-implement` pipeline cannot push to other repos, and pushing tags to 41
public repos must be a watched run. After this plan's PR is merged, a human runs
locally from the hub repo:

1. `python3 scripts/add_fullscreen_toggle.py --dry-run` — expect one status line
   per hub game (41), each `would update → vX.Y.0`, `skipped: …`, or a `failed`
   to investigate.
2. Pilot one static and one self-healing game:
   `python3 scripts/add_fullscreen_toggle.py --only game-brickfall,game-nibbles`
   — then open both live pages (after Pages rebuilds) and check ⛶ sits right
   after the version badge, toggles fullscreen, shows ✕ in fullscreen, and
   survives the nibbles dc unpack.
3. Full run: `python3 scripts/add_fullscreen_toggle.py`. Re-run once more —
   every line must be `skipped: up to date` or `skipped: no game-nav`.
4. Refresh hub screenshots if desired:
   `python3 scripts/capture_screenshots.py` (the nav is in the capture).
