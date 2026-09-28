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
