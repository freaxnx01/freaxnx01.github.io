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
    "game-bmx-beach-jam",
    "game-beach-buggy-racer",
    "game-space-invaders",
    "game-splashdown",
    "game-stack-duel",
    "game-fruit-frenzy",
    "game-kick-fury",
    "game-dustline",
    "game-moon-lander",
    "game-plod",
]
BASE_URL = "https://github.freaxnx01.ch/{repo}/"
VIEWPORT = {"width": 1280, "height": 800}
RENDER_DELAY_MS = 2000  # let canvas games paint a real frame
ICON_SIZE = 256

ASSETS_DIR = Path(__file__).resolve().parent.parent / "games" / "assets"

# Per-game "action recipes": drive the game out of its title/menu into live
# gameplay before the shot. Each step is a (verb, arg) tuple:
#   ("click",   fraction (x, y))   -- mouse click at viewport fraction (focus / start)
#   ("select",  css selector)      -- click a specific DOM element (menu buttons)
#   ("press",   key)               -- tap a key
#   ("down",    key)               -- hold a key (auto-released at the end)
#   ("up",      key)               -- release a held key
#   ("wait",    milliseconds)      -- let the frame evolve
# Keys use Playwright names ("Space", "Enter", "ArrowRight", "KeyA", ...).
# Games without a recipe are shot as-is (their title screen is fine).
CENTER = (0.5, 0.6)
ACTIONS = {
    "game-space-invaders": [
        ("click", CENTER), ("press", "Space"), ("wait", 500),
        ("down", "ArrowRight"),
        ("press", "Space"), ("wait", 220), ("press", "Space"), ("wait", 220),
        ("press", "Space"), ("wait", 220), ("up", "ArrowRight"),
        ("press", "Space"), ("wait", 200),
    ],
    "game-bmx-beach-jam": [
        ("click", CENTER), ("press", "Space"), ("wait", 300),
        ("down", "ArrowRight"), ("wait", 1600),
        ("press", "Space"), ("wait", 360),          # bunny hop -> airborne trick
        ("down", "ArrowLeft"), ("wait", 240),       # flip in the air
        ("up", "ArrowLeft"),
    ],
    "game-beach-buggy-racer": [
        ("click", CENTER), ("press", "Space"), ("wait", 300),
        ("down", "ArrowUp"), ("wait", 1050),        # accelerate straight; stay on track
    ],
    "game-splashdown": [
        ("select", "#pickPenguin"), ("wait", 900),  # pick a character -> start
        ("down", "ArrowUp"), ("wait", 2600),        # paddle down the river
        ("down", "ArrowRight"), ("wait", 650),
    ],
    "game-stack-duel": [
        ("click", CENTER), ("press", "Enter"), ("wait", 3500),  # start + let 3-2-1 finish
        # build up both stacks: P1 hard-drop = Space, P2 hard-drop = Enter
        ("press", "KeyA"), ("press", "Space"), ("press", "ArrowRight"), ("press", "Enter"), ("wait", 260),
        ("press", "KeyD"), ("press", "Space"), ("press", "ArrowLeft"), ("press", "Enter"), ("wait", 260),
        ("press", "Space"), ("press", "Enter"), ("wait", 260),
        ("press", "KeyD"), ("press", "Space"), ("press", "ArrowRight"), ("press", "Enter"), ("wait", 260),
        ("press", "KeyA"), ("press", "Space"), ("press", "ArrowLeft"), ("press", "Enter"), ("wait", 300),
    ],
    "game-fruit-frenzy": [
        # Drop a run of fruit near the top-centre so the board shows a real,
        # partly-merged pile (with a live score) instead of an empty box.
        # Drop cooldown is 480ms, so keep waits above that.
        ("click", (0.50, 0.30)), ("wait", 560),
        ("click", (0.50, 0.30)), ("wait", 640),   # same spot -> a merge
        ("click", (0.42, 0.30)), ("wait", 560),
        ("click", (0.58, 0.30)), ("wait", 560),
        ("click", (0.46, 0.30)), ("wait", 560),
        ("click", (0.54, 0.30)), ("wait", 560),
        ("click", (0.50, 0.30)), ("wait", 560),
        ("click", (0.45, 0.30)), ("wait", 900),    # let everything settle
    ],
    "game-kick-fury": [
        # Title screen -> [1] starts a 1P vs CPU fight; close in and strike so
        # the shot catches a live exchange (leg mid-kick) rather than the menu.
        ("click", CENTER), ("press", "Digit1"), ("wait", 1800),  # start + round intro
        ("down", "KeyD"), ("wait", 500), ("up", "KeyD"),          # close the distance
        ("press", "KeyF"), ("wait", 220),                        # punch
        ("press", "KeyG"), ("wait", 220),                        # kick
        ("down", "KeyD"), ("wait", 180), ("up", "KeyD"),
        ("press", "KeyG"), ("wait", 160),                        # kick — leg extended
    ],
    "game-dustline": [
        # Enter launches; guns auto-fire. Advance up the desert and fire a
        # rocket so the shot catches tracers/explosions, not the title card.
        ("click", CENTER), ("press", "Enter"), ("wait", 2600),   # launch + first wave
        ("down", "ArrowUp"), ("wait", 900),                      # push up the battlefield
        ("press", "Space"), ("wait", 250),                       # homing rocket
        ("down", "ArrowRight"), ("wait", 380), ("up", "ArrowRight"),
        ("press", "Space"), ("wait", 320), ("up", "ArrowUp"),
    ],
    "game-moon-lander": [
        # Any key starts; catch the lander mid-descent over the pads with the
        # engine burning and the live telemetry HUD, not the pre-start screen.
        ("click", CENTER), ("press", "Space"), ("wait", 800),    # focus + start
        ("down", "ArrowUp"), ("wait", 450), ("up", "ArrowUp"),   # main-engine burn
        ("press", "ArrowLeft"), ("wait", 350),                   # RCS rotate
        ("down", "ArrowUp"), ("wait", 450), ("up", "ArrowUp"),   # burn again, mid-fall
        ("wait", 250),
    ],
    "game-plod": [
        # Lemmings-style: dismiss the start modal via its PLAY button, then let
        # the plodders spawn from the hatch and march the destructible terrain.
        ("click", (0.50, 0.665)), ("wait", 4200),  # PLAY -> plodders march out
    ],
}


def run_actions(page, steps) -> None:
    """Execute an action recipe, tracking held keys so they're always released."""
    held = []
    try:
        for verb, arg in steps:
            if verb == "wait":
                page.wait_for_timeout(arg)
            elif verb == "click":
                page.mouse.click(int(VIEWPORT["width"] * arg[0]),
                                 int(VIEWPORT["height"] * arg[1]))
            elif verb == "select":
                page.click(arg, timeout=5000)
            elif verb == "press":
                page.keyboard.press(arg)
            elif verb == "down":
                page.keyboard.down(arg)
                held.append(arg)
            elif verb == "up":
                page.keyboard.up(arg)
                if arg in held:
                    held.remove(arg)
    finally:
        for key in held:
            page.keyboard.up(key)


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
    # Optional CLI args capture only the named repos (default: all in REPOS).
    repos = sys.argv[1:] or REPOS

    with sync_playwright() as p:
        browser = p.chromium.launch()
        for repo in repos:
            url = BASE_URL.format(repo=repo)
            full_png = ASSETS_DIR / f"{repo}.png"
            icon_png = ASSETS_DIR / f"{repo}-icon.png"
            print(f"→ {repo}: {url}")
            try:
                page = browser.new_page(viewport=VIEWPORT)
                page.goto(url, wait_until="networkidle", timeout=30000)
                page.wait_for_timeout(RENDER_DELAY_MS)
                if repo in ACTIONS:
                    run_actions(page, ACTIONS[repo])
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
