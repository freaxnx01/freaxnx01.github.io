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
import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

from add_game_favicons import default_branch, discover_games

START_MARKER = "<!-- game-nav-fullscreen:start -->"
END_MARKER = "<!-- game-nav-fullscreen:end -->"
SNIPPET_PATH = Path(__file__).resolve().parent / "fullscreen_snippet.html"

BLOCK_RE = re.compile(re.escape(START_MARKER) + r".*?" + re.escape(END_MARKER), re.DOTALL)
VERSION_RE = re.compile(r'(window\.GAME_VERSION\s*=\s*")(\d+\.\d+\.\d+)(")')
SEMVER_RE = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")

# Pages served from somewhere other than the repo root's index.html.
SERVED_FILE = {"game-gorillazz": "docs/index.html"}

REMOTE_BASE = "https://github.com/freaxnx01"
DEFAULT_CLONES_ROOT = Path.home() / ".cache" / "game-rollout"
FEAT_MSG = "feat(nav): add fullscreen toggle"


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
            # Annotated: `push --follow-tags` below pushes annotated tags only,
            # so a lightweight tag would stay local and never reach origin.
            _git(repo_path, "tag", "-a", tag, "-m", tag)
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
