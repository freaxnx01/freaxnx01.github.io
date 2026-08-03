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
