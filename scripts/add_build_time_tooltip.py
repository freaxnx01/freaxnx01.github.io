#!/usr/bin/env python3
"""Add the build-time tooltip to the version badge in every game-<name> repo on the hub.

For each game listed in games/index.html, injects scripts/buildtime_snippet.html
into the repo's served page (right after the fullscreen block, else before
</body>), adds a line under `## [Unreleased]` in CHANGELOG.md, commits both and
pushes. No release: version.js and tags are left alone.

The tooltip reads document.lastModified, which on GitHub Pages is the build
time of the deployment, so nothing has to be stamped into the repo.

Works on script-owned clean clones in ~/.cache/game-rollout/ — never on the
sibling working copies, which may carry in-progress branches.

Re-running is safe: a page that already carries the current snippet is skipped.

Usage:
    pip install -r scripts/requirements.txt
    python3 scripts/add_build_time_tooltip.py [--dry-run] [--only REPO[,REPO...]] [--clones-root PATH]
                                              [--trailer "Key: value" ...]
"""
import argparse
import re
import subprocess
import sys
from pathlib import Path

from add_fullscreen_toggle import (
    DEFAULT_CLONES_ROOT,
    END_MARKER as FULLSCREEN_END,
    LINKREF_RE,
    REMOTE_BASE,
    SERVED_FILE as FULLSCREEN_SERVED_FILE,
    UNRELEASED_RE,
    VERSION_HEADING_RE,
    _git,
    ensure_clean_clone,
)
from add_game_favicons import discover_games

START_MARKER = "<!-- game-nav-buildtime:start -->"
END_MARKER = "<!-- game-nav-buildtime:end -->"
SNIPPET_PATH = Path(__file__).resolve().parent / "buildtime_snippet.html"

BLOCK_RE = re.compile(re.escape(START_MARKER) + r".*?" + re.escape(END_MARKER), re.DOTALL)

# Pages served from somewhere other than the repo root's index.html.
SERVED_FILE = {**FULLSCREEN_SERVED_FILE, "game-rhyflitzer": "prototype/index.html"}

FEAT_MSG = "feat(nav): show the build time when hovering the version badge"
CHANGELOG_LINE = ("Hover over the version number to see when the game was last updated, "
                  "in your own time zone, and how long ago")


def load_snippet() -> str:
    return SNIPPET_PATH.read_text().strip()


def inject_snippet(html: str, snippet: str | None = None) -> tuple[str, bool]:
    """Put the snippet after the fullscreen block (else before the last </body>), or refresh an existing block."""
    snippet = (snippet if snippet is not None else load_snippet()).strip()
    if BLOCK_RE.search(html):
        new = BLOCK_RE.sub(lambda _m: snippet, html, count=1)
        return new, new != html
    idx = html.rfind(FULLSCREEN_END)
    if idx != -1:
        idx += len(FULLSCREEN_END)
        return html[:idx] + "\n" + snippet + html[idx:], True
    idx = html.lower().rfind("</body>")
    if idx == -1:
        raise ValueError("no </body> tag found")
    return html[:idx] + snippet + "\n" + html[idx:], True


def has_version_badge(html: str) -> bool:
    """True if the page has a #version-badge to hover.

    Our own snippet mentions "version-badge" too, so it is stripped first.
    """
    return "version-badge" in BLOCK_RE.sub("", html)


def served_file(repo: str) -> str:
    return SERVED_FILE.get(repo, "index.html")


def _with_added_line(body: str) -> str:
    """An [Unreleased] body with CHANGELOG_LINE at the end of its ### Added list (opened on top if missing)."""
    lines = body.strip("\n").split("\n") if body.strip() else []
    if "### Added" not in lines:
        return "\n".join(["### Added", f"- {CHANGELOG_LINE}"] + ([""] + lines if lines else [])) + "\n"
    head = lines.index("### Added")
    i = head + 1
    while i < len(lines) and not lines[i].strip():
        i += 1
    start = i
    while i < len(lines) and lines[i].strip() and not lines[i].startswith("### "):
        i += 1
    lines.insert(i if i > start else head + 1, f"- {CHANGELOG_LINE}")
    return "\n".join(lines) + "\n"


def add_unreleased_line(text: str) -> str:
    """CHANGELOG_LINE under `## [Unreleased]` → `### Added`, leaving every other entry as it is."""
    if CHANGELOG_LINE in text:
        return text
    m = UNRELEASED_RE.search(text)
    if m:
        nxt = VERSION_HEADING_RE.search(text, m.end()) or LINKREF_RE.search(text, m.end())
        end = nxt.start() if nxt else len(text)
        return text[:m.end()] + "\n" + _with_added_line(text[m.end():end]) + ("\n" + text[end:] if nxt else "")
    section = "## [Unreleased]\n\n" + _with_added_line("")
    nxt = VERSION_HEADING_RE.search(text)
    if nxt:
        return text[:nxt.start()] + section + "\n" + text[nxt.start():]
    return text.rstrip("\n") + "\n\n" + section


def process_repo(repo: str, clones_root: Path, remote_base: str = REMOTE_BASE, dry_run: bool = False,
                 trailers: list[str] | None = None) -> str:
    try:
        repo_path, branch = ensure_clean_clone(repo, clones_root, remote_base)
    except subprocess.CalledProcessError as e:
        return f"failed: clone/fetch error: {e.stderr.strip()[:200]}"

    page_rel = served_file(repo)
    page_path = repo_path / page_rel
    if not page_path.exists():
        return f"failed: {page_rel} not found"
    html = page_path.read_text()
    if not has_version_badge(html):
        return "skipped: no version badge"
    try:
        new_html, changed = inject_snippet(html)
    except ValueError as e:
        return f"failed: {e}"
    if not changed:
        return "skipped: up to date"

    changelog = repo_path / "CHANGELOG.md"
    has_changelog = changelog.exists()
    if dry_run:
        return "would update (dry-run)" if has_changelog else "would update, no CHANGELOG.md (dry-run)"

    try:
        page_path.write_text(new_html)
        _git(repo_path, "add", page_rel)
        if has_changelog:
            changelog.write_text(add_unreleased_line(changelog.read_text()))
            _git(repo_path, "add", "CHANGELOG.md")
        message = FEAT_MSG + ("\n\n" + "\n".join(trailers) if trailers else "")
        _git(repo_path, "commit", "-q", "-m", message)
        _git(repo_path, "push", "-q", "origin", branch)
    except subprocess.CalledProcessError as e:
        return f"failed: {' '.join(e.cmd[:3])}: {(e.stderr or '').strip()[:200]}"

    return "succeeded" if has_changelog else "succeeded (no CHANGELOG.md)"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dry-run", action="store_true",
                        help="Report what would change without writing, committing, or pushing.")
    parser.add_argument("--only", default=None,
                        help="Comma-separated list of repo names to process (default: all).")
    parser.add_argument("--clones-root", type=Path, default=DEFAULT_CLONES_ROOT,
                        help=f"Where the script keeps its own clean clones (default: {DEFAULT_CLONES_ROOT}).")
    parser.add_argument("--trailer", action="append", default=[],
                        help='A trailer line for the commit message, e.g. "Co-Authored-By: …" (repeatable).')
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
            status = process_repo(repo, args.clones_root, dry_run=args.dry_run, trailers=args.trailer)
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
