# Browser Games Hub Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a single static overview page at `https://github.freaxnx01.ch/games/` listing freaxnx01's 6 live browser games as cards, each with a screenshot thumbnail, name, one-liner, mode badge(s), a Play link, and a click-to-enlarge lightbox.

**Architecture:** Hand-authored static files under `games/` (no Jekyll front matter, so Jekyll copies them through verbatim). A one-time Python + Playwright script captures a full screenshot and a 256×256 cropped icon per game into `games/assets/`. The page is dependency-free: `index.html` + `style.css` + `lightbox.js`, dark arcade-hub aesthetic, responsive CSS Grid. The root `index.md` gains one link to `/games/`.

**Tech Stack:** Static HTML/CSS/vanilla JS (no framework, no build). Python 3 + Playwright (Chromium) + Pillow for the one-time screenshot capture. Jekyll (`jekyll-theme-hacker`) already builds the repo for GitHub Pages.

## Global Constraints

- Games included (exactly these 6, in this order): `game-tschau-sepp`, `game-tank-toys`, `game-barrel-shooter`, `game-gorillazz`, `game-esel-running`, `game-n-s-clone`. Excluded: `game-moki-racer`, `civil-war-battlefield`.
- Live game URL pattern: `https://github.freaxnx01.ch/<repo>/` (trailing slash).
- The `games/` page is plain static HTML/CSS/JS — **no Jekyll front matter** in any file under `games/` (front matter would make Jekyll re-template it).
- **No external runtime dependencies** — no CDN scripts, fonts, or CSS. Everything self-contained in the repo. System/web-safe monospace font stack only.
- Mode badge values are exactly: `Solo`, `Multiplayer · Peer2Peer`, `Multiplayer · Local` (middot `·` = U+00B7). `Server` is reserved but unused today.
- Screenshot assets: `games/assets/<repo>.png` (full) and `games/assets/<repo>-icon.png` (256×256 cropped), committed as binary.
- Root `index.md` changes are limited to adding one `/games/` link — nothing else on that page changes.

---

## Per-game data (single source of truth for Task 3)

| Repo | Name | One-liner | Badges |
|---|---|---|---|
| game-tschau-sepp | Tschau Sepp | Swiss Jass card game | Solo · Multiplayer · Peer2Peer |
| game-tank-toys | Tank Toys | Isometric toy-tank battle | Multiplayer · Peer2Peer · Multiplayer · Local |
| game-barrel-shooter | Barrel Blast | 3D physics shooter | Solo |
| game-gorillazz | Gorillazz | QBasic Gorillas clone | Multiplayer · Local |
| game-esel-running | Esel vs. Karotte | 2-player donkey race (German) | Multiplayer · Local |
| game-n-s-clone | North & South Clone | Civil War strategy/action clone | Solo |

---

## Task 1: Screenshot capture script + generated assets

**Files:**
- Create: `scripts/capture_screenshots.py`
- Create (generated, binary): `games/assets/<repo>.png` and `games/assets/<repo>-icon.png` for all 6 repos
- Create: `scripts/requirements.txt`

**Interfaces:**
- Produces: 12 PNG files under `games/assets/` with the exact names referenced by Task 3's `<img>` tags: `game-tschau-sepp-icon.png`, `game-tschau-sepp.png`, … one full + one icon per repo.

- [ ] **Step 1: Create the requirements file**

Create `scripts/requirements.txt`:

```
playwright==1.48.0
Pillow==10.4.0
```

- [ ] **Step 2: Write the capture script**

Create `scripts/capture_screenshots.py`:

```python
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
```

- [ ] **Step 3: Install dependencies**

Run:
```bash
pip install -r scripts/requirements.txt && playwright install chromium
```
Expected: Playwright + Pillow install; Chromium downloads (~150MB).

- [ ] **Step 4: Run the capture script**

Run:
```bash
python3 scripts/capture_screenshots.py
```
Expected: six `→ <repo>` lines each followed by `✓ saved …`. If any game prints `✗ FAILED`, note it — a placeholder must be swapped in for that repo before Task 3's verification.

- [ ] **Step 5: Verify the assets exist and are non-empty**

Run:
```bash
ls -la games/assets/ && python3 -c "from PIL import Image; import glob; [print(f, Image.open(f).size) for f in sorted(glob.glob('games/assets/*-icon.png'))]"
```
Expected: 12 PNGs; every `*-icon.png` reports `(256, 256)`.

- [ ] **Step 6: Commit**

```bash
git add scripts/requirements.txt scripts/capture_screenshots.py games/assets/
git commit -m "feat(games): add screenshot capture script and generated assets"
```

---

## Task 2: Page scaffold, CSS, and lightbox behaviour

**Files:**
- Create: `games/style.css`
- Create: `games/lightbox.js`

**Interfaces:**
- Produces (CSS classes consumed by Task 3's HTML): `.hub`, `.hub__header`, `.hub__grid`, `.card`, `.card__thumb`, `.card__body`, `.card__title`, `.card__desc`, `.card__badges`, `.badge`, `.badge--solo`, `.badge--p2p`, `.badge--local`, `.card__play`.
- Produces (lightbox contract): `lightbox.js` opens an overlay when any element with `data-full="<url>"` and `data-title="<name>"` is clicked; closes on overlay click, close-button click, or `Escape`. Requires an element `#lightbox` present in the DOM (added in Task 3).

- [ ] **Step 1: Write the stylesheet**

Create `games/style.css` (no front matter, plain CSS):

```css
:root {
  --bg: #0e1016;
  --bg-card: #171a24;
  --bg-card-hover: #1d2130;
  --border: #262b3a;
  --text: #e6e8ef;
  --text-dim: #9aa0b4;
  --accent: #5cf2c4;
  --accent-2: #ff7b6b;
  --mono: ui-monospace, "SFMono-Regular", "Cascadia Code", "Menlo", "Consolas", monospace;
}

* { box-sizing: border-box; }

body {
  margin: 0;
  background:
    radial-gradient(1200px 600px at 50% -10%, #1a1f30 0%, transparent 60%),
    var(--bg);
  color: var(--text);
  font-family: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
  line-height: 1.5;
  min-height: 100vh;
}

.hub {
  max-width: 1120px;
  margin: 0 auto;
  padding: clamp(2rem, 5vw, 4rem) 1.25rem 4rem;
}

.hub__header { margin-bottom: 2.5rem; }

.hub__header h1 {
  font-family: var(--mono);
  font-size: clamp(1.8rem, 5vw, 2.8rem);
  letter-spacing: 0.02em;
  margin: 0 0 0.5rem;
}

.hub__header h1 .accent { color: var(--accent); }

.hub__header p {
  color: var(--text-dim);
  margin: 0;
  max-width: 60ch;
}

.hub__back {
  display: inline-block;
  margin-bottom: 1.5rem;
  color: var(--text-dim);
  text-decoration: none;
  font-family: var(--mono);
  font-size: 0.85rem;
}
.hub__back:hover { color: var(--accent); }

.hub__grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 1.25rem;
}

.card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 14px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  transition: transform 0.15s ease, background 0.15s ease, border-color 0.15s ease;
}
.card:hover {
  transform: translateY(-4px);
  background: var(--bg-card-hover);
  border-color: var(--accent);
}

.card__thumb {
  display: block;
  width: 100%;
  aspect-ratio: 16 / 10;
  object-fit: cover;
  background: #0a0c12;
  cursor: zoom-in;
  border: none;
  padding: 0;
}

.card__body {
  padding: 1rem 1.1rem 1.2rem;
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
  flex: 1;
}

.card__title {
  font-family: var(--mono);
  font-size: 1.15rem;
  margin: 0;
}

.card__desc {
  color: var(--text-dim);
  font-size: 0.9rem;
  margin: 0;
  flex: 1;
}

.card__badges {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
}

.badge {
  font-family: var(--mono);
  font-size: 0.68rem;
  letter-spacing: 0.03em;
  padding: 0.2rem 0.5rem;
  border-radius: 999px;
  border: 1px solid var(--border);
  color: var(--text-dim);
  white-space: nowrap;
}
.badge--solo  { color: var(--accent);   border-color: color-mix(in srgb, var(--accent) 45%, transparent); }
.badge--p2p   { color: #8fb4ff;         border-color: color-mix(in srgb, #8fb4ff 45%, transparent); }
.badge--local { color: var(--accent-2); border-color: color-mix(in srgb, var(--accent-2) 45%, transparent); }

.card__play {
  margin-top: 0.4rem;
  align-self: flex-start;
  font-family: var(--mono);
  font-size: 0.9rem;
  text-decoration: none;
  color: var(--bg);
  background: var(--accent);
  padding: 0.5rem 0.9rem;
  border-radius: 8px;
  font-weight: 600;
  transition: filter 0.15s ease;
}
.card__play:hover { filter: brightness(1.1); }

/* Lightbox */
.lightbox {
  position: fixed;
  inset: 0;
  background: rgba(6, 8, 12, 0.88);
  display: none;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  z-index: 50;
}
.lightbox.is-open { display: flex; }
.lightbox__img {
  max-width: 92vw;
  max-height: 82vh;
  border-radius: 10px;
  border: 1px solid var(--border);
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.6);
}
.lightbox__caption {
  position: absolute;
  bottom: 1.25rem;
  left: 0;
  right: 0;
  text-align: center;
  font-family: var(--mono);
  color: var(--text);
}
.lightbox__close {
  position: absolute;
  top: 1rem;
  right: 1.25rem;
  background: none;
  border: none;
  color: var(--text);
  font-size: 2rem;
  line-height: 1;
  cursor: pointer;
}
.lightbox__close:hover { color: var(--accent); }

@media (prefers-reduced-motion: reduce) {
  .card { transition: none; }
  .card:hover { transform: none; }
}
```

- [ ] **Step 2: Write the lightbox script**

Create `games/lightbox.js` (plain JS, no front matter):

```javascript
(function () {
  "use strict";

  var overlay = document.getElementById("lightbox");
  if (!overlay) return;

  var img = overlay.querySelector(".lightbox__img");
  var caption = overlay.querySelector(".lightbox__caption");
  var closeBtn = overlay.querySelector(".lightbox__close");

  function open(full, title) {
    img.src = full;
    img.alt = title;
    caption.textContent = title;
    overlay.classList.add("is-open");
  }

  function close() {
    overlay.classList.remove("is-open");
    img.src = "";
  }

  // Any element carrying data-full opens the lightbox.
  document.querySelectorAll("[data-full]").forEach(function (el) {
    el.addEventListener("click", function () {
      open(el.getAttribute("data-full"), el.getAttribute("data-title") || "");
    });
  });

  overlay.addEventListener("click", function (e) {
    if (e.target === overlay) close();
  });
  closeBtn.addEventListener("click", close);
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape" && overlay.classList.contains("is-open")) close();
  });
})();
```

- [ ] **Step 3: Commit**

```bash
git add games/style.css games/lightbox.js
git commit -m "feat(games): add hub stylesheet and dependency-free lightbox"
```

---

## Task 3: The games hub page (all 6 cards)

**Files:**
- Create: `games/index.html`

**Interfaces:**
- Consumes: CSS classes and the `#lightbox` / `data-full` contract from Task 2; thumbnail assets `games/assets/<repo>-icon.png` and full assets `games/assets/<repo>.png` from Task 1.

- [ ] **Step 1: Write the page**

Create `games/index.html` (no Jekyll front matter — relative asset paths, so it works both locally and at `/games/`):

```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Browser Games Hub · freaxnx01</title>
  <link rel="stylesheet" href="style.css">
</head>
<body>
  <main class="hub">
    <a class="hub__back" href="/">&larr; back to github.freaxnx01.ch</a>
    <header class="hub__header">
      <h1><span class="accent">▶</span> Browser Games Hub</h1>
      <p>A handful of finished browser games — card games, tank battles, physics shooters and retro clones. Click a screenshot to enlarge, or hit Play to jump straight in.</p>
    </header>

    <section class="hub__grid">

      <article class="card">
        <img class="card__thumb" src="assets/game-tschau-sepp-icon.png" alt="Tschau Sepp screenshot"
             data-full="assets/game-tschau-sepp.png" data-title="Tschau Sepp">
        <div class="card__body">
          <h2 class="card__title">Tschau Sepp</h2>
          <p class="card__desc">Swiss Jass card game.</p>
          <div class="card__badges">
            <span class="badge badge--solo">Solo</span>
            <span class="badge badge--p2p">Multiplayer · Peer2Peer</span>
          </div>
          <a class="card__play" href="https://github.freaxnx01.ch/game-tschau-sepp/">▶ Play</a>
        </div>
      </article>

      <article class="card">
        <img class="card__thumb" src="assets/game-tank-toys-icon.png" alt="Tank Toys screenshot"
             data-full="assets/game-tank-toys.png" data-title="Tank Toys">
        <div class="card__body">
          <h2 class="card__title">Tank Toys</h2>
          <p class="card__desc">Isometric toy-tank battle.</p>
          <div class="card__badges">
            <span class="badge badge--p2p">Multiplayer · Peer2Peer</span>
            <span class="badge badge--local">Multiplayer · Local</span>
          </div>
          <a class="card__play" href="https://github.freaxnx01.ch/game-tank-toys/">▶ Play</a>
        </div>
      </article>

      <article class="card">
        <img class="card__thumb" src="assets/game-barrel-shooter-icon.png" alt="Barrel Blast screenshot"
             data-full="assets/game-barrel-shooter.png" data-title="Barrel Blast">
        <div class="card__body">
          <h2 class="card__title">Barrel Blast</h2>
          <p class="card__desc">3D physics shooter.</p>
          <div class="card__badges">
            <span class="badge badge--solo">Solo</span>
          </div>
          <a class="card__play" href="https://github.freaxnx01.ch/game-barrel-shooter/">▶ Play</a>
        </div>
      </article>

      <article class="card">
        <img class="card__thumb" src="assets/game-gorillazz-icon.png" alt="Gorillazz screenshot"
             data-full="assets/game-gorillazz.png" data-title="Gorillazz">
        <div class="card__body">
          <h2 class="card__title">Gorillazz</h2>
          <p class="card__desc">QBasic Gorillas clone.</p>
          <div class="card__badges">
            <span class="badge badge--local">Multiplayer · Local</span>
          </div>
          <a class="card__play" href="https://github.freaxnx01.ch/game-gorillazz/">▶ Play</a>
        </div>
      </article>

      <article class="card">
        <img class="card__thumb" src="assets/game-esel-running-icon.png" alt="Esel vs. Karotte screenshot"
             data-full="assets/game-esel-running.png" data-title="Esel vs. Karotte">
        <div class="card__body">
          <h2 class="card__title">Esel vs. Karotte</h2>
          <p class="card__desc">2-player donkey race (German).</p>
          <div class="card__badges">
            <span class="badge badge--local">Multiplayer · Local</span>
          </div>
          <a class="card__play" href="https://github.freaxnx01.ch/game-esel-running/">▶ Play</a>
        </div>
      </article>

      <article class="card">
        <img class="card__thumb" src="assets/game-n-s-clone-icon.png" alt="North &amp; South Clone screenshot"
             data-full="assets/game-n-s-clone.png" data-title="North &amp; South Clone">
        <div class="card__body">
          <h2 class="card__title">North &amp; South Clone</h2>
          <p class="card__desc">Civil War strategy/action clone.</p>
          <div class="card__badges">
            <span class="badge badge--solo">Solo</span>
          </div>
          <a class="card__play" href="https://github.freaxnx01.ch/game-n-s-clone/">▶ Play</a>
        </div>
      </article>

    </section>
  </main>

  <div class="lightbox" id="lightbox" role="dialog" aria-modal="true" aria-label="Screenshot">
    <button class="lightbox__close" type="button" aria-label="Close">&times;</button>
    <img class="lightbox__img" src="" alt="">
    <div class="lightbox__caption"></div>
  </div>

  <script src="lightbox.js"></script>
</body>
</html>
```

- [ ] **Step 2: Serve locally and verify visually**

Run:
```bash
python3 -m http.server 8099 --directory games &
sleep 1 && curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8099/index.html
```
Expected: `200`. Then open `http://localhost:8099/` in a browser and confirm:
- All 6 cards render with a thumbnail (no broken-image icons).
- Clicking a thumbnail opens the lightbox with the full screenshot + caption; clicking the backdrop, the `×`, or pressing `Escape` closes it.
- Badges show the right colors; each `▶ Play` points at the correct `https://github.freaxnx01.ch/<repo>/` URL (hover to check).
- Layout reflows to a single column at a narrow (~375px) width.

Stop the server:
```bash
kill %1
```

- [ ] **Step 3: Commit**

```bash
git add games/index.html
git commit -m "feat(games): add browser games hub page with 6 game cards"
```

---

## Task 4: Link the hub from the root page

**Files:**
- Modify: `index.md`

**Interfaces:**
- Consumes: the deployed `/games/` route from Task 3.

- [ ] **Step 1: Add the link**

Append one line to `index.md` (leave the existing content untouched):

```markdown
[🎮 Browser Games Hub](/games/)
```

The file should now end with that line as its own paragraph, e.g.:

```markdown
--=={ Hello World!?! }==--

[Sample](http://octocat.github.io/)

[github-pages-example](https://freaxnx01.github.io/github-pages-example)

[Jekyll Doc](https://jekyllrb.com/docs/)

[md](https://github.com/adam-p/markdown-here/wiki/Markdown-Cheatsheet)

[🎮 Browser Games Hub](/games/)
```

- [ ] **Step 2: Verify the link markup**

Run:
```bash
grep -F "[🎮 Browser Games Hub](/games/)" index.md
```
Expected: the line prints (exit 0).

- [ ] **Step 3: Commit**

```bash
git add index.md
git commit -m "feat: link Browser Games Hub from root page"
```

---

## Task 5: Push and verify the live deploy

**Files:** none (deploy + smoke test only)

- [ ] **Step 1: Push all commits**

Run:
```bash
git push
```
Expected: push succeeds to `origin/master`.

- [ ] **Step 2: Wait for Pages, then smoke-test the live URLs**

GitHub Pages redeploys on push (usually < 2 min). Then run:
```bash
for u in / /games/ /games/style.css /games/lightbox.js /games/assets/game-tschau-sepp-icon.png; do
  code=$(curl -s -o /dev/null -w "%{http_code}" -L "https://github.freaxnx01.ch$u")
  echo "$code  $u"
done
```
Expected: `200` for every line. (If `/games/` 404s, wait another minute for the Pages build and retry.)

- [ ] **Step 3: Confirm the root link resolves**

Load `https://github.freaxnx01.ch/` in a browser, click **🎮 Browser Games Hub**, and confirm it lands on the hub with all 6 cards. Done.

---

## Notes for the implementer

- **Front matter kills these files.** Do not add `---` YAML blocks to anything under `games/`. Jekyll only copies files through verbatim when they have no front matter; a stray front-matter block would make it re-template the HTML.
- **If a screenshot failed to capture** (Task 1 flagged a repo as skipped), drop a hand-made placeholder PNG at both `games/assets/<repo>.png` and `games/assets/<repo>-icon.png` (256×256) before Task 3's visual check, so no card shows a broken image.
- **Asset paths are relative** (`assets/…`, `style.css`) so the page works both under `python3 -m http.server --directory games` locally and at `/games/` in production. The only absolute paths are the `▶ Play` links (full live URLs) and the root back-link (`/`).
