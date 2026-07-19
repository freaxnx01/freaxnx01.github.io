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
    "game-wortduell",
    "game-gem-cascade",
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
    "game-voxel-sandbox",
    "game-battleship-toys",
    "game-sky-fury",
    "game-geography-quiz",
    "game-cluck-and-load",
    "game-marquee-quiz",
    "game-nibbles",
    "game-maze-muncher",
    "game-zen-sudoku",
    "game-neon-pong",
    "game-photo-puzzler",
    "game-criss-cross",
    "game-millionenfrage",
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
        # Enter launches; guns auto-fire. The chopper is screen-locked near
        # its spawn point and ArrowUp drives it toward the top HUD, so don't
        # hold it — stay put (or nudge sideways only) to keep WOLF-1 centered
        # and clear of the wave banner. Wait out enough scroll for a jeep/tank
        # to scroll into frame, then fire a rocket for tracers + a live shot.
        ("click", CENTER), ("press", "Enter"), ("wait", 5500),   # launch + let a target scroll in
        ("down", "ArrowLeft"), ("wait", 150), ("up", "ArrowLeft"),  # slight bank, stays centered
        ("press", "Space"), ("wait", 300),                       # homing rocket
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
    "game-battleship-toys": [
        # Menu -> "Play the computer" (#b-ai) starts a match immediately. Sail the
        # Red ship (WASD) toward the action and fire so the shot catches the
        # isometric sea, both fleets and a cannon splash, not the title card.
        ("select", "#b-ai"), ("wait", 1600),        # start vs computer
        ("down", "KeyD"), ("wait", 650), ("up", "KeyD"),   # sail east
        ("press", "Space"), ("wait", 220),          # cannon
        ("down", "KeyS"), ("wait", 380), ("up", "KeyS"),
        ("press", "KeyE"), ("wait", 220),           # torpedo
        ("press", "Space"), ("wait", 320),          # another salvo
    ],
    "game-voxel-sandbox": [
        # "CLICK TO PLAY" drops into a first-person pointer-lock world. It starts
        # facing the sky, so pitch the camera down (~35 deg) with a slight yaw to
        # frame the terrain/trees, then step forward for depth.
        ("click", (0.50, 0.69)), ("wait", 1200),   # enter the world
        ("look", (16, 44)), ("wait", 45), ("look", (16, 44)), ("wait", 45),
        ("look", (16, 44)), ("wait", 45), ("look", (16, 44)), ("wait", 45),
        ("look", (16, 44)), ("wait", 45), ("look", (16, 44)), ("wait", 45),
        ("look", (16, 44)), ("wait", 60),
        ("down", "KeyW"), ("wait", 500), ("up", "KeyW"),
        ("wait", 500),
    ],
    "game-sky-fury": [
        # First Enter: menu -> playing (parked on deck, "rearming"). It needs
        # ~2.6s on deck before a second Enter is accepted to start the
        # takeoff roll; that finishes airborne in well under a second.
        ("click", CENTER), ("press", "Enter"), ("wait", 2900),
        ("press", "Enter"), ("wait", 900),
        ("down", "ArrowUp"), ("wait", 260), ("up", "ArrowUp"),  # nose up off the deck
        ("down", "ArrowRight"), ("wait", 400), ("up", "ArrowRight"),
        ("press", "Space"), ("wait", 200), ("press", "Space"), ("wait", 200),
    ],
    "game-cluck-and-load": [
        # Click on the menu starts a round; fire a few shots at birds crossing
        # mid-screen so the shot catches live gameplay (feathers/HUD), not the
        # title card.
        ("click", CENTER), ("wait", 900),
        ("click", (0.35, 0.45)), ("wait", 250),
        ("click", (0.60, 0.55)), ("wait", 250),
        ("click", (0.50, 0.35)), ("wait", 400),
    ],
    "game-nibbles": [
        # Title -> Space enters setup, Space starts (ready dialog), Space
        # confirms into live play.
        #
        # A fixed-timing key sequence here (as before: hold right, hold
        # down, hold right some more) almost never actually reaches the
        # single food pellet: the pellet's position is randomized fresh
        # on every page load, the snake only crawls ~80-90px/s, and this
        # game -- like classic Nibbles -- ignores a keypress that would
        # reverse it straight into its own body, so a blind guess is as
        # likely to be silently dropped as it is to connect. The result
        # was a screenshot of a tiny, un-grown 2-cell stub with score
        # 000000 that read as an empty menu rather than gameplay.
        # Verified live against https://github.freaxnx.ch/game-nibbles/
        # with a scratch Playwright probe before landing this: blind
        # holds of up to 6s in one direction never once grew the snake,
        # confirming the fixed-recipe approach was fundamentally the
        # wrong tool here (see _nibbles_chase for the closed-loop fix).
        ("click", CENTER), ("press", "Space"), ("wait", 500),   # title -> setup
        ("press", "Space"), ("wait", 500),                      # setup -> ready
        ("press", "Space"), ("wait", 800),                      # ready -> play
        ("chase", 22),
        ("wait", 300),
    ],
    "game-maze-muncher": [
        # Attract screen -> Space starts, ~1.8s ready countdown, then play.
        # Steer the muncher through the maze so pellets, a ghost and the
        # HUD are all visible in frame.
        ("click", CENTER), ("press", "Space"), ("wait", 2200),  # start + ready
        ("down", "ArrowRight"), ("wait", 900), ("up", "ArrowRight"),
        ("down", "ArrowDown"), ("wait", 500), ("up", "ArrowDown"),
        ("wait", 300),
    ],
    "game-zen-sudoku": [
        # No title screen — it opens straight into a live puzzle, so just
        # select a couple of cells and place digits for a shot that shows
        # off the peer/selection highlighting, not just a static grid.
        ("click", (0.30, 0.40)), ("wait", 150),
        ("press", "7"), ("wait", 150),
        ("click", (0.36, 0.52)), ("wait", 150),
        ("press", "3"), ("wait", 150),
        ("click", (0.42, 0.46)), ("wait", 300),
    ],
    "game-neon-pong": [
        # Menu -> LOCAL 2P starts an immediate match. Nudge both paddles so
        # the shot catches a live rally (ball + both paddles in frame) and
        # not the serve-start moment.
        ("click", (0.50, 0.33)), ("wait", 1300),
        ("down", "KeyW"), ("wait", 350), ("up", "KeyW"),
        ("down", "ArrowUp"), ("wait", 350), ("up", "ArrowUp"),
        ("wait", 300),
    ],
}


# game-nibbles: canvas-pixel probe used by _nibbles_chase (see below) to
# locate the snake's head (bright yellow) and the current food digit
# (near-white text), scanning only below the HUD band. Once the snake has
# grown past a couple of segments, the naive centroid of *all* yellow
# pixels drifts toward the body and stops tracking the head -- so once we
# know the last horizontal direction driven, we instead take the leading
# edge (max-x if last move was right, min-x if left) as the head.
_NIBBLES_FIND_JS = """
(lastHDir) => {
  const canvas = document.querySelector('canvas');
  const ctx = canvas.getContext('2d');
  const rect = canvas.getBoundingClientRect();
  const w = canvas.width, h = canvas.height;
  const data = ctx.getImageData(0, 0, w, h).data;
  const scaleX = rect.width / w, scaleY = rect.height / h;
  const hudCutoff = Math.round(90 / scaleY);
  let yellow = [], white = [];
  for (let y = hudCutoff; y < h; y++) {
    for (let x = 0; x < w; x++) {
      const i = (y * w + x) * 4;
      const r = data[i], g = data[i + 1], b = data[i + 2], a = data[i + 3];
      if (a < 200) continue;
      if (r > 170 && g > 170 && b < 130) yellow.push([x, y]);
      else if (r > 150 && g > 150 && b > 150) white.push([x, y]);
    }
  }
  function centroid(pts) {
    if (!pts.length) return null;
    let sx = 0, sy = 0;
    for (const [x, y] of pts) { sx += x; sy += y; }
    return [sx / pts.length, sy / pts.length];
  }
  let head = centroid(yellow);
  if (yellow.length && lastHDir) {
    let ext = lastHDir === "right" ? -Infinity : Infinity;
    let pts = [];
    for (const [x, y] of yellow) {
      if (lastHDir === "right" ? x > ext : x < ext) { ext = x; pts = [[x, y]]; }
      else if (x === ext) pts.push([x, y]);
    }
    head = centroid(pts);
  }
  // The "SAMMY CRASHED!" dialog is a large light-gray filled rectangle,
  // which also matches the near-white food-digit test above but with a
  // pixel count orders of magnitude bigger than a single digit's ~15-20
  // -- use that to tell "crashed" apart from "food is on screen".
  const crashed = white.length > 300;
  const food = crashed ? null : centroid(white);
  const margin = 8; // keep clear of the wall -- crashing resets score/length
  return {
    head: head ? [rect.left + head[0] * scaleX, rect.top + head[1] * scaleY] : null,
    food: food ? [rect.left + food[0] * scaleX, rect.top + food[1] * scaleY] : null,
    bounds: [rect.left + margin, rect.top + hudCutoff * scaleY + margin,
              rect.left + rect.width - margin, rect.top + rect.height - margin],
    yellowCount: yellow.length,
    crashed: crashed,
  };
}
"""


def _nibbles_chase(page, rounds: int, target_eaten: int = 2) -> None:
    """game-nibbles: steer the snake onto its (randomly-placed) food by
    closed-loop pixel sampling instead of guessing a fixed key sequence.

    Each round re-reads the live head/food positions off the canvas
    (_NIBBLES_FIND_JS) and moves vertically first, then horizontally.
    Vertical-first matters: this game ignores a keypress that would
    reverse the snake 180 degrees into itself, the default spawn heading
    is rightward, and vertical is always perpendicular to whatever the
    current heading is -- so leading with the vertical leg guarantees the
    very first correction is never a blocked reversal, and every
    following horizontal leg is likewise perpendicular to the vertical
    leg that just preceded it. Grid-snapped movement means a single
    round often overshoots slightly, so it typically takes 2-3 rounds to
    actually connect with one pellet.

    Safety nets, added after earlier versions crashed the snake ("SAMMY
    CRASHED! -1000 PTS") on longer runs -- a much worse shot than the
    original bug, since a crash resets score AND snake length back to
    the tiny spawn stub: every leg's duration is clamped so the head
    can't be driven within `margin`px of a wall; the loop stops as soon
    as `target_eaten` pellets have been eaten (detected via jumps in the
    live yellow-pixel count) rather than always spending the full
    `rounds` budget and racking up unnecessary self-collision risk from
    a growing body crossing its own earlier path; and a crash is itself
    detected (the "CRASHED" dialog's gray fill trips the food-color
    scan) and recovered from with a Space press + a fresh, lowered
    growth target, so a mid-run self-collision doesn't waste the whole
    capture -- the loop still lands a decently-grown live shot instead
    of a frozen game-over dialog.
    """
    speed_x, speed_y = 89.0, 72.0  # px/s, calibrated against the live game
    buffer_ms = 80
    last_hdir = None
    baseline_count = None
    eaten = 0
    for _ in range(rounds):
        info = page.evaluate(_NIBBLES_FIND_JS, last_hdir)
        if info.get("crashed"):
            # Respawn and keep going with a lower bar -- better a
            # smaller-but-live snake than the game-over dialog.
            page.keyboard.press("Space")
            page.wait_for_timeout(600)
            last_hdir = None
            baseline_count = None
            eaten = 0
            target_eaten = 1
            continue
        head, food, bounds = info.get("head"), info.get("food"), info.get("bounds")
        count = info.get("yellowCount") or 0
        if baseline_count is None:
            baseline_count = count
        elif count > baseline_count + 60:  # ~one segment's worth of pixels
            eaten += 1
            baseline_count = count
            if eaten >= target_eaten:
                break
        if not head or not food or not bounds:
            continue
        left, top, right, bottom = bounds
        dx, dy = food[0] - head[0], food[1] - head[1]

        vkey = "ArrowDown" if dy > 0 else "ArrowUp"
        vroom = (bottom - head[1]) if vkey == "ArrowDown" else (head[1] - top)
        vms = max(0, min(int(abs(dy) / speed_y * 1000) + buffer_ms,
                          int(max(vroom, 0) / speed_y * 1000)))
        page.keyboard.down(vkey)
        page.wait_for_timeout(vms)
        page.keyboard.up(vkey)

        hkey = "ArrowRight" if dx > 0 else "ArrowLeft"
        hroom = (right - head[0]) if hkey == "ArrowRight" else (head[0] - left)
        hms = max(0, min(int(abs(dx) / speed_x * 1000) + buffer_ms,
                          int(max(hroom, 0) / speed_x * 1000)))
        page.keyboard.down(hkey)
        page.wait_for_timeout(hms)
        page.keyboard.up(hkey)
        last_hdir = "right" if hkey == "ArrowRight" else "left"


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
            elif verb == "chase":
                _nibbles_chase(page, arg)
            elif verb == "look":
                # Pointer-lock mouse-look: dispatch a synthetic mousemove so
                # first-person games (which read movementX/Y) pan/pitch the camera.
                page.evaluate(
                    "([dx, dy]) => document.dispatchEvent("
                    "new MouseEvent('mousemove', {movementX: dx, movementY: dy, bubbles: true}))",
                    [arg[0], arg[1]],
                )
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
