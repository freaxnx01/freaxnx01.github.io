#!/usr/bin/env python3
"""One-time (re-runnable) screenshot capture for the Browser Games Hub.

For each live game it saves:
  games/assets/<repo>.png       — full viewport screenshot
  games/assets/<repo>-icon.png  — 256x256 center-cropped thumbnail

Load failures are logged and skipped (the run continues); skipped games are
listed at the end so a placeholder can be dropped in by hand.

Usage:
    pip install -r scripts/requirements.txt
    playwright install chromium
    python3 scripts/capture_screenshots.py
"""
import sys
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

REPOS = [
    "game-tschau-sepp",
    "game-tank-toys",
    "game-barrel-shooter",
    "game-gorillazz",
    "game-esel-running",
    "game-n-s-clone",
]
BASE_URL = "https://github.freaxnx01.ch/{repo}/"
VIEWPORT = {"width": 1280, "height": 800}
RENDER_DELAY_MS = 2000  # let canvas games paint a real frame
ICON_SIZE = 256

ASSETS_DIR = Path(__file__).resolve().parent.parent / "games" / "assets"


def make_icon(full_png: Path, icon_png: Path) -> None:
    """Center-crop the full screenshot to a square, then resize to 256x256."""
    with Image.open(full_png) as img:
        img = img.convert("RGB")
        w, h = img.size
        side = min(w, h)
        left = (w - side) // 2
        top = (h - side) // 2
        square = img.crop((left, top, left + side, top + side))
        square = square.resize((ICON_SIZE, ICON_SIZE), Image.LANCZOS)
        square.save(icon_png, "PNG")


def main() -> int:
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    skipped = []

    with sync_playwright() as p:
        browser = p.chromium.launch()
        for repo in REPOS:
            url = BASE_URL.format(repo=repo)
            full_png = ASSETS_DIR / f"{repo}.png"
            icon_png = ASSETS_DIR / f"{repo}-icon.png"
            print(f"→ {repo}: {url}")
            try:
                page = browser.new_page(viewport=VIEWPORT)
                page.goto(url, wait_until="networkidle", timeout=30000)
                page.wait_for_timeout(RENDER_DELAY_MS)
                page.screenshot(path=str(full_png))
                page.close()
                make_icon(full_png, icon_png)
                print(f"  ✓ saved {full_png.name} + {icon_png.name}")
            except Exception as exc:  # noqa: BLE001 — log and continue
                print(f"  ✗ FAILED ({exc}); skipping", file=sys.stderr)
                skipped.append(repo)
        browser.close()

    if skipped:
        print("\nSKIPPED (drop in a placeholder by hand):")
        for repo in skipped:
            print(f"  - {repo}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
