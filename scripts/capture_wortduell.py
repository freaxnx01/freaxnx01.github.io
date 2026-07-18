#!/usr/bin/env python3
"""Capture a mid-game WORTDUELL (game-wortduell) board for the Games Hub.

The generic capture_screenshots.py can only shoot WORTDUELL's start screen: its
rack is randomised per game and it's a compiled design-tool component with no
stable selectors, so there's no simple "start gameplay" recipe. This helper
instead *plays* a real vs-CPU game — it drives the game's own "Tipp" button
(which computes and pre-places the best valid move) and "Legen" (submit) for a
few player turns, letting the CPU answer between each, then screenshots the
resulting crossword.

Outputs (same names/format as capture_screenshots.py, so it just overwrites):
  games/assets/game-wortduell.png       — full 1280x800 screenshot
  games/assets/game-wortduell-icon.png  — 256x256 center-cropped thumbnail

Usage:
    pip install -r scripts/requirements.txt   # playwright + Pillow
    playwright install chromium
    python3 scripts/capture_wortduell.py [rounds]   # rounds default 5

Requires the live site (needs the streamed dictionary), so it shoots from:
    https://github.freaxnx01.ch/game-wortduell/
"""
import sys
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

URL = "https://github.freaxnx01.ch/game-wortduell/"
VIEWPORT = {"width": 1280, "height": 800}
ICON_SIZE = 256
DEFAULT_ROUNDS = 5

ASSETS_DIR = Path(__file__).resolve().parent.parent / "games" / "assets"
FULL_PNG = ASSETS_DIR / "game-wortduell.png"
ICON_PNG = ASSETS_DIR / "game-wortduell-icon.png"


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
    rounds = int(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_ROUNDS
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport=VIEWPORT)
        print(f"→ {URL}")
        # networkidle lets the ~606k-word dictionary finish streaming/caching.
        page.goto(URL, wait_until="networkidle", timeout=45000)
        page.wait_for_timeout(2000)

        # Start a game vs the computer (the "Mittel" difficulty is preselected).
        page.get_by_text("Spiel starten", exact=False).first.click()
        page.wait_for_timeout(2500)

        for i in range(rounds):
            try:
                page.get_by_text("Tipp", exact=True).first.click()   # place best move
                page.wait_for_timeout(1200)
                page.get_by_text("Legen", exact=True).first.click()  # submit it
                page.wait_for_timeout(1000)
                page.wait_for_timeout(3200)                          # CPU's turn
                print(f"  ✓ round {i + 1}/{rounds}")
            except Exception as exc:  # noqa: BLE001 — no move available / turn stuck
                print(f"  ✗ stopped at round {i + 1} ({exc})", file=sys.stderr)
                break

        page.wait_for_timeout(800)
        page.screenshot(path=str(FULL_PNG))
        browser.close()

    make_icon(FULL_PNG, ICON_PNG)
    print(f"  ✓ saved {FULL_PNG.name} + {ICON_PNG.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
