# Individual Game Favicons Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give each of the 36 `game-<name>` repos linked from the hub its own browser-tab favicon, derived from the existing card icon already in the hub repo.

**Architecture:** One script, `scripts/add_game_favicons.py`, run from the hub repo (`freaxnx01.github.io`). It discovers the game list by parsing `games/index.html`, then for each game: syncs a local clone under the hub repo's sibling directory, derives a 32×32 `favicon.png` from the existing `games/assets/<slug>-icon.png`, inserts a `<link rel="icon">` tag into that repo's `index.html`, and commits + pushes directly to `main`. The whole run is idempotent and tolerates individual-repo failures without aborting the batch.

**Tech Stack:** Python 3, Pillow (already pinned in `scripts/requirements.txt`), `git` via `subprocess`.

## Global Constraints

- Favicon size: single 32×32 PNG, no other sizes (spec: "Format").
- Insertion point: `<link rel="icon" href="favicon.png" sizes="32x32" type="image/png">` immediately after the `<head>` opening tag, exact string (spec: "Per-repo change").
- Crop: center-crop the source icon (400×250) to a square, then resize to 32×32 (spec: "Asset generation").
- Scope: exactly the repos discoverable from `games/index.html` cards that have both a `card__thumb` icon and a `https://github.freaxnx01.ch/<repo>/` play link — this naturally excludes `dogwash` (hosted on `julia-hase.github.io`, not a `freaxnx01/game-<name>` repo) (spec: "Scope").
- No build step in game repos — `index.html` in the repo root is the deployed page (spec: "Per-repo change").
- Direct push to `main`, no PR workflow (spec: "Out of scope").
- No automated tests — this is a one-shot content-generation script; verification is manual (spec: "Testing").

---

### Task 1: Discover games from `games/index.html`

**Files:**
- Create: `scripts/add_game_favicons.py`

**Interfaces:**
- Produces: `discover_games(hub_root: Path) -> list[dict]`, each dict has keys `"repo"` (str, e.g. `"game-nibbles"`) and `"icon_path"` (`Path`, absolute path to that game's `-icon.png` under `games/assets/`).

- [ ] **Step 1: Write the module skeleton and `discover_games`**

```python
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
```

- [ ] **Step 2: Verify manually**

Run:

```bash
cd ~/repos/github/freaxnx01/public/freaxnx01.github.io
python3 -c "
from pathlib import Path
import sys
sys.path.insert(0, 'scripts')
from add_game_favicons import discover_games
games = discover_games(Path('.'))
print(len(games))
repos = {g['repo'] for g in games}
print('dogwash' in repos)
print(sorted(repos)[:5])
"
```

Expected: `36`, then `False`, then a sorted list starting with the first 5 `game-*` repo names alphabetically. If the count isn't 36 or `dogwash` is `True`, check the regexes against the actual markup in `games/index.html` before continuing.

- [ ] **Step 3: Commit**

```bash
git add scripts/add_game_favicons.py
git commit -m "feat: discover game list for favicon script"
```

---

### Task 2: Favicon image generation

**Files:**
- Modify: `scripts/add_game_favicons.py`

**Interfaces:**
- Consumes: nothing from Task 1 directly (pure function).
- Produces: `generate_favicon_bytes(icon_path: Path) -> bytes` — PNG-encoded bytes of the 32×32 favicon.

- [ ] **Step 1: Add `generate_favicon_bytes`**

```python
def generate_favicon_bytes(icon_path: Path) -> bytes:
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
```

- [ ] **Step 2: Verify manually**

Run:

```bash
cd ~/repos/github/freaxnx01/public/freaxnx01.github.io
python3 -c "
from pathlib import Path
import sys, io
sys.path.insert(0, 'scripts')
from add_game_favicons import generate_favicon_bytes
from PIL import Image
data = generate_favicon_bytes(Path('games/assets/game-nibbles-icon.png'))
img = Image.open(io.BytesIO(data))
print(img.size, img.format)
"
```

Expected: `(32, 32) PNG`.

- [ ] **Step 3: Commit**

```bash
git add scripts/add_game_favicons.py
git commit -m "feat: generate favicon PNG bytes from card icon"
```

---

### Task 3: Idempotent `<link rel="icon">` insertion

**Files:**
- Modify: `scripts/add_game_favicons.py`

**Interfaces:**
- Produces: `ensure_favicon_link(html: str) -> tuple[str, bool]` — returns `(new_html, changed)`; `changed` is `False` and `new_html == html` if a `rel="icon"` link is already present anywhere in `html`.

- [ ] **Step 1: Add `ensure_favicon_link`**

```python
def ensure_favicon_link(html: str) -> tuple[str, bool]:
    if re.search(r'rel="icon"', html, re.IGNORECASE):
        return html, False
    new_html, count = HEAD_OPEN_RE.subn(
        lambda m: f"{m.group(1)}\n{LINK_TAG}", html, count=1
    )
    if count == 0:
        raise ValueError("no <head> tag found in index.html")
    return new_html, True
```

- [ ] **Step 2: Verify manually**

Run:

```bash
cd ~/repos/github/freaxnx01/public/freaxnx01.github.io
python3 -c "
import sys
sys.path.insert(0, 'scripts')
from add_game_favicons import ensure_favicon_link

# no existing head attrs
html1 = '<!DOCTYPE html>\n<html>\n<head>\n<meta charset=\"utf-8\">\n</head>\n<body></body></html>'
new1, changed1 = ensure_favicon_link(html1)
print(changed1)
print('<link rel=\"icon\"' in new1)

# head with attrs, already has a link tag
html2 = '<html>\n<head lang=\"en\">\n<link rel=\"icon\" href=\"x.png\">\n</head>\n<body></body></html>'
new2, changed2 = ensure_favicon_link(html2)
print(changed2, new2 == html2)
"
```

Expected: `True` / `True` / `False True`.

- [ ] **Step 3: Commit**

```bash
git add scripts/add_game_favicons.py
git commit -m "feat: insert favicon link tag idempotently"
```

---

### Task 4: Repo sync and per-repo apply

**Files:**
- Modify: `scripts/add_game_favicons.py`

**Interfaces:**
- Consumes: `generate_favicon_bytes` (Task 2), `ensure_favicon_link` (Task 3).
- Produces: `ensure_local_clone(repo: str, clones_root: Path) -> Path` (returns the local repo path, cloning or pulling as needed) and `process_repo(game: dict, clones_root: Path, dry_run: bool = False) -> str` (returns one of `"succeeded"`, `"skipped (already done)"`, `"would update (dry-run)"`, or a string starting with `"failed: "`).

- [ ] **Step 1: Add `ensure_local_clone` and `process_repo`**

```python
def ensure_local_clone(repo: str, clones_root: Path) -> Path:
    repo_path = clones_root / repo
    if repo_path.exists():
        subprocess.run(
            ["git", "-C", str(repo_path), "checkout", "main"],
            check=True, capture_output=True, text=True,
        )
        subprocess.run(
            ["git", "-C", str(repo_path), "pull", "--ff-only", "origin", "main"],
            check=True, capture_output=True, text=True,
        )
    else:
        subprocess.run(
            ["git", "clone", f"https://github.com/freaxnx01/{repo}.git", str(repo_path)],
            check=True, capture_output=True, text=True,
        )
    return repo_path


def process_repo(game: dict, clones_root: Path, dry_run: bool = False) -> str:
    repo = game["repo"]
    try:
        repo_path = ensure_local_clone(repo, clones_root)
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
        return "skipped (already done)"

    if dry_run:
        return "would update (dry-run)"

    if favicon_changed:
        favicon_path.write_bytes(favicon_bytes)
    if link_changed:
        index_path.write_text(new_html)

    try:
        subprocess.run(
            ["git", "-C", str(repo_path), "add", "favicon.png", "index.html"],
            check=True, capture_output=True, text=True,
        )
        subprocess.run(
            ["git", "-C", str(repo_path), "commit", "-m", "feat: add favicon"],
            check=True, capture_output=True, text=True,
        )
        subprocess.run(
            ["git", "-C", str(repo_path), "push", "origin", "main"],
            check=True, capture_output=True, text=True,
        )
    except subprocess.CalledProcessError as e:
        return f"failed: commit/push error: {e.stderr.strip()[:200]}"

    return "succeeded"
```

- [ ] **Step 2: Verify manually on a single already-cloned repo**

Run (safe: `dry_run=True` makes no writes, no commits, no pushes):

```bash
cd ~/repos/github/freaxnx01/public/freaxnx01.github.io
python3 -c "
from pathlib import Path
import sys
sys.path.insert(0, 'scripts')
from add_game_favicons import discover_games, process_repo

hub_root = Path('.')
clones_root = hub_root.resolve().parent
games = {g['repo']: g for g in discover_games(hub_root)}
game = games['game-nibbles']
print(process_repo(game, clones_root, dry_run=True))
"
```

Expected: `would update (dry-run)` (since `game-nibbles` has no favicon yet). Re-run is safe — it does not touch the working tree.

- [ ] **Step 3: Commit**

```bash
git add scripts/add_game_favicons.py
git commit -m "feat: sync repo clone and apply favicon change per-repo"
```

---

### Task 5: CLI wiring and summary output

**Files:**
- Modify: `scripts/add_game_favicons.py`

**Interfaces:**
- Consumes: `discover_games` (Task 1), `process_repo` (Task 4).
- Produces: `main()` — the script's entry point; no return value consumed elsewhere.

- [ ] **Step 1: Add `main()` and the `if __name__` guard**

```python
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
        wanted = set(args.only.split(","))
        games = [g for g in games if g["repo"] in wanted]
        missing = wanted - {g["repo"] for g in games}
        if missing:
            print(f"warning: not found in games/index.html: {sorted(missing)}", file=sys.stderr)

    results = []
    for game in games:
        status = process_repo(game, clones_root, dry_run=args.dry_run)
        results.append((game["repo"], status))
        print(f"{game['repo']}: {status}")

    succeeded = [r for r in results if r[1] == "succeeded"]
    skipped = [r for r in results if r[1].startswith("skipped")]
    dry_run_would = [r for r in results if r[1].startswith("would update")]
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


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Verify manually — dry-run across all games**

Run:

```bash
cd ~/repos/github/freaxnx01/public/freaxnx01.github.io
python3 scripts/add_game_favicons.py --dry-run
```

Expected: 36 lines, each `<repo>: would update (dry-run)` (no favicons exist yet), then a summary with `total: 36`, `would update (dry-run): 36`, `failed: 0`. No files should be modified — confirm with `git -C ~/repos/github/freaxnx01/public/game-nibbles status` (expect clean).

- [ ] **Step 3: Verify manually — real run on 2 repos**

Run:

```bash
cd ~/repos/github/freaxnx01/public/freaxnx01.github.io
python3 scripts/add_game_favicons.py --only game-nibbles,game-zen-sudoku
```

Expected: both report `succeeded`. Then confirm:

```bash
git -C ~/repos/github/freaxnx01/public/game-nibbles log -1 --stat
git -C ~/repos/github/freaxnx01/public/game-zen-sudoku log -1 --stat
```

Expected: each shows the `feat: add favicon` commit touching `favicon.png` (new file) and `index.html`. Open `https://github.freaxnx01.ch/game-nibbles/` and `https://github.freaxnx01.ch/game-zen-sudoku/` in a browser and confirm the tab icon is the game's own crop, not the default.

- [ ] **Step 4: Verify manually — re-run is idempotent**

Run:

```bash
cd ~/repos/github/freaxnx01/public/freaxnx01.github.io
python3 scripts/add_game_favicons.py --only game-nibbles,game-zen-sudoku
```

Expected: both report `skipped (already done)`, and `git -C ~/repos/github/freaxnx01/public/game-nibbles status` is clean (no new commit).

- [ ] **Step 5: Commit**

```bash
git add scripts/add_game_favicons.py
git commit -m "feat: add CLI and summary reporting for favicon script"
```

---

### Task 6: Full rollout across all 36 games

**Files:**
- None (no code changes — this task runs the finished script).

**Interfaces:**
- Consumes: `main()` (Task 5), run as a script.

- [ ] **Step 1: Run the script for real across all games**

```bash
cd ~/repos/github/freaxnx01/public/freaxnx01.github.io
python3 scripts/add_game_favicons.py
```

- [ ] **Step 2: Confirm the summary**

Expected: `total: 36`, `failed: 0` (2 already `succeeded` from Task 5's manual verification will show as `skipped (already done)` this time, the remaining 34 as `succeeded`). If any repo fails, read the printed reason, fix the underlying issue (e.g. a repo whose `<head>` tag is malformed, or a push rejected by branch protection), and re-run the script with `--only <failed-repo>` — it's idempotent, so re-running the whole batch is also safe if needed.

- [ ] **Step 3: Spot-check a third game not touched in Task 5**

Open `https://github.freaxnx01.ch/game-space-invaders/` in a browser and confirm the tab icon is that game's own crop.

- [ ] **Step 4: Close the loop with the issue**

```bash
gh issue comment 13 --repo freaxnx01/freaxnx01.github.io --body "Rolled out via scripts/add_game_favicons.py — all 36 game-<name> repos now have their own favicon.png + <link rel=\"icon\">. Verified game-nibbles, game-zen-sudoku, and game-space-invaders in-browser."
gh issue close 13 --repo freaxnx01/freaxnx01.github.io
```
