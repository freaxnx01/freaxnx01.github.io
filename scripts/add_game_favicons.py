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
