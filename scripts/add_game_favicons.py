#!/usr/bin/env python3
"""Add a per-game favicon to every game-<name> repo linked from the hub.

For each game listed in games/index.html, derives a 32x32 favicon.png from
the game's existing card icon (games/assets/<slug>-icon.png), adds a
<link rel="icon"> tag to that repo's index.html, and commits + pushes the
change directly to the repo's main branch.

Re-running is safe: a repo whose favicon.png and <link rel="icon"> tag
already match what this script would produce is skipped with no commit.

Usage:
    pip install -r scripts/requirements.txt
    python3 scripts/add_game_favicons.py [--dry-run] [--only REPO[,REPO...]]
"""
import argparse
import io
import os
import re
import subprocess
import sys
from pathlib import Path

from PIL import Image

ARTICLE_RE = re.compile(r'<article class="card"[^>]*>(.*?)</article>', re.DOTALL)
ICON_RE = re.compile(r'<img class="card__thumb" src="assets/([^"]+)"')
PLAY_RE = re.compile(r'href="https://github\.freaxnx01\.ch/([^/]+)/"')

FAVICON_SIZE = (32, 32)
LINK_TAG = '<link rel="icon" href="favicon.png" sizes="32x32" type="image/png">'
HEAD_OPEN_RE = re.compile(r'(<head(?:\s[^>]*)?>)')

# Fail fast instead of hanging if git tries to prompt for HTTPS credentials.
GIT_ENV = {**os.environ, "GIT_TERMINAL_PROMPT": "0"}


def discover_games(hub_root: Path) -> list[dict]:
    html = (hub_root / "games" / "index.html").read_text()
    games = []
    for block in ARTICLE_RE.findall(html):
        icon_m = ICON_RE.search(block)
        play_m = PLAY_RE.search(block)
        if not icon_m or not play_m:
            continue
        games.append({
            "repo": play_m.group(1),
            "icon_path": hub_root / "games" / "assets" / icon_m.group(1),
        })
    return games


def generate_favicon_bytes(icon_path: Path) -> bytes:
    """Generate a 32x32 PNG favicon from a game's card icon.

    Takes a card icon (typically 400x250), center-crops to a square,
    resizes to 32x32, and returns PNG-encoded bytes.

    Args:
        icon_path: Path to the card icon image (e.g. games/assets/game-nibbles-icon.png)

    Returns:
        PNG-encoded bytes of the 32x32 favicon.
    """
    with Image.open(icon_path) as img:
        img = img.convert("RGB")
        width, height = img.size
        side = min(width, height)
        left = (width - side) // 2
        top = (height - side) // 2
        cropped = img.crop((left, top, left + side, top + side))
        resized = cropped.resize(FAVICON_SIZE, Image.LANCZOS)
        buf = io.BytesIO()
        resized.save(buf, format="PNG")
        return buf.getvalue()


def ensure_favicon_link(html: str) -> tuple[str, bool]:
    """Idempotently insert a favicon link tag into HTML.

    Checks if a rel="icon" link already exists in the HTML (case-insensitive).
    If it does, returns the HTML unchanged with changed=False.
    If not, inserts a link tag right after the opening <head> tag.

    Args:
        html: HTML content as a string

    Returns:
        A tuple of (new_html, changed) where:
        - new_html: The HTML with favicon link inserted (or unchanged if already present)
        - changed: False if a rel="icon" link already existed, True if it was inserted

    Raises:
        ValueError: If no <head> tag is found in the HTML
    """
    if re.search(r'rel="icon"', html, re.IGNORECASE):
        return html, False
    new_html, count = HEAD_OPEN_RE.subn(
        lambda m: f"{m.group(1)}\n{LINK_TAG}", html, count=1
    )
    if count == 0:
        raise ValueError("no <head> tag found in index.html")
    return new_html, True


def default_branch(repo_path: Path) -> str:
    """Resolve the repo's default branch (e.g. "main" or "master").

    Reads refs/remotes/origin/HEAD, which `git clone` sets automatically to
    point at the remote's default branch. Falls back to "main" if the ref
    can't be resolved (e.g. detached HEAD, missing ref) — callers already
    handle a failed checkout/pull/push on a wrong branch name gracefully.
    """
    try:
        result = subprocess.run(
            ["git", "-C", str(repo_path), "symbolic-ref", "refs/remotes/origin/HEAD"],
            check=True, capture_output=True, text=True, env=GIT_ENV,
        )
        ref = result.stdout.strip()  # e.g. "refs/remotes/origin/main"
        branch = ref.rsplit("/", 1)[-1]
        return branch or "main"
    except subprocess.CalledProcessError:
        return "main"


def ensure_local_clone(repo: str, clones_root: Path) -> tuple[Path, str]:
    repo_path = clones_root / repo
    if repo_path.exists():
        branch = default_branch(repo_path)
        subprocess.run(
            ["git", "-C", str(repo_path), "checkout", branch],
            check=True, capture_output=True, text=True, env=GIT_ENV,
        )
        subprocess.run(
            ["git", "-C", str(repo_path), "pull", "--ff-only", "origin", branch],
            check=True, capture_output=True, text=True, env=GIT_ENV,
        )
    else:
        subprocess.run(
            ["git", "clone", f"https://github.com/freaxnx01/{repo}.git", str(repo_path)],
            check=True, capture_output=True, text=True, env=GIT_ENV,
        )
        branch = default_branch(repo_path)
    return repo_path, branch


def process_repo(game: dict, clones_root: Path, dry_run: bool = False) -> str:
    repo = game["repo"]
    try:
        repo_path, branch = ensure_local_clone(repo, clones_root)
    except subprocess.CalledProcessError as e:
        return f"failed: clone/pull error: {e.stderr.strip()[:200]}"

    favicon_bytes = generate_favicon_bytes(game["icon_path"])
    favicon_path = repo_path / "favicon.png"
    favicon_changed = (
        not favicon_path.exists() or favicon_path.read_bytes() != favicon_bytes
    )

    index_path = repo_path / "index.html"
    html = index_path.read_text()
    try:
        new_html, link_changed = ensure_favicon_link(html)
    except ValueError as e:
        return f"failed: {e}"

    if not favicon_changed and not link_changed:
        # Local working tree already matches what we'd produce, but a prior
        # run may have committed locally and then failed to push (auth,
        # branch protection, network). Check whether the local branch is
        # still ahead of origin before declaring victory.
        try:
            result = subprocess.run(
                ["git", "-C", str(repo_path), "rev-list", "--count", f"origin/{branch}..{branch}"],
                check=True, capture_output=True, text=True, env=GIT_ENV,
            )
            ahead = int(result.stdout.strip() or "0")
        except subprocess.CalledProcessError as e:
            return f"failed: commit/push error: {e.stderr.strip()[:200]}"

        if ahead == 0:
            return "skipped (already done)"

        if dry_run:
            return "would push (dry-run)"

        try:
            subprocess.run(
                ["git", "-C", str(repo_path), "push", "origin", branch],
                check=True, capture_output=True, text=True, env=GIT_ENV,
            )
        except subprocess.CalledProcessError as e:
            return f"failed: commit/push error: {e.stderr.strip()[:200]}"

        return "succeeded"

    if dry_run:
        return "would update (dry-run)"

    if favicon_changed:
        favicon_path.write_bytes(favicon_bytes)
    if link_changed:
        index_path.write_text(new_html)

    try:
        subprocess.run(
            ["git", "-C", str(repo_path), "add", "favicon.png", "index.html"],
            check=True, capture_output=True, text=True, env=GIT_ENV,
        )
        subprocess.run(
            ["git", "-C", str(repo_path), "commit", "-m", "feat: add favicon"],
            check=True, capture_output=True, text=True, env=GIT_ENV,
        )
        subprocess.run(
            ["git", "-C", str(repo_path), "push", "origin", branch],
            check=True, capture_output=True, text=True, env=GIT_ENV,
        )
    except subprocess.CalledProcessError as e:
        return f"failed: commit/push error: {e.stderr.strip()[:200]}"

    return "succeeded"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Report what would change without writing, committing, or pushing.",
    )
    parser.add_argument(
        "--only", default=None,
        help="Comma-separated list of repo names to process (default: all).",
    )
    args = parser.parse_args()

    hub_root = Path(__file__).resolve().parent.parent
    clones_root = hub_root.parent

    games = discover_games(hub_root)
    if args.only:
        wanted = {r.strip() for r in args.only.split(",")}
        games = [g for g in games if g["repo"] in wanted]
        missing = wanted - {g["repo"] for g in games}
        if missing:
            print(f"warning: not found in games/index.html: {sorted(missing)}", file=sys.stderr)

    results = []
    for game in games:
        try:
            status = process_repo(game, clones_root, dry_run=args.dry_run)
        except Exception as e:
            status = f"failed: {type(e).__name__}: {e}"
        results.append((game["repo"], status))
        print(f"{game['repo']}: {status}")

    succeeded = [r for r in results if r[1] == "succeeded"]
    skipped = [r for r in results if r[1].startswith("skipped")]
    dry_run_would = [r for r in results if r[1].startswith("would")]
    failed = [r for r in results if r[1].startswith("failed")]

    print("\nSummary:")
    print(f"  total:     {len(results)}")
    print(f"  succeeded: {len(succeeded)}")
    print(f"  skipped:   {len(skipped)}")
    if dry_run_would:
        print(f"  would update (dry-run): {len(dry_run_would)}")
    print(f"  failed:    {len(failed)}")
    if failed:
        print("\nFailures:")
        for repo, status in failed:
            print(f"  {repo}: {status}")

    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
