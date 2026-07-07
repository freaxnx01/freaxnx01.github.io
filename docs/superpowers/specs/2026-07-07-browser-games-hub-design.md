# Browser Games Hub — Design Spec

Date: 2026-07-07

Source: GitHub issue #1 (freaxnx01/freaxnx01.github.io).

## Goal

A single overview page listing all of freaxnx01's finished browser games, each with
name, icon, short description, multiplayer mode, and a screenshot — so a visitor to
`github.freaxnx01.ch` can discover and jump into any game.

## Location

- New folder `games/` inside the existing `freaxnx01.github.io` repo (cloned locally
  at `~/repos/github/freaxnx01/public/freaxnx01.github.io`).
- Served at `https://github.freaxnx01.ch/games/` via the repo's existing GitHub Pages
  + custom domain (CNAME `github.freaxnx01.ch`) setup — no new Pages site needed.
- Root `index.md` (currently a placeholder Jekyll page using `jekyll-theme-hacker`)
  gets one added link to `/games/`. Nothing else on the root page changes.
- The `games/` page itself is plain static HTML/CSS (not Jekyll-templated) — it is
  copied through unmodified by Jekyll's build since it has no front matter.

## Scope: games included

Only games that are already live on GitHub Pages today. Excluded: `game-moki-racer`
and `civil-war-battlefield` (no Pages site yet — revisit once they're deployed).

| Repo | Name | One-liner | Mode |
|---|---|---|---|
| game-tschau-sepp | Tschau Sepp | Swiss Jass card game | Solo (vs AI) + Multiplayer · Peer2Peer (2–4p, WebRTC) |
| game-tank-toys | Tank Toys | Isometric toy-tank battle | Multiplayer · Peer2Peer (WebRTC) + Multiplayer · Local (hot-seat) |
| game-barrel-shooter | Barrel Blast | 3D physics shooter (three.js + cannon-es) | Solo |
| game-gorillazz | Gorillazz | QBasic Gorillas clone | Multiplayer · Local (hot-seat) |
| game-esel-running | Esel vs. Karotte | 2-player donkey race (German) | Multiplayer · Local (hot-seat) |
| game-n-s-clone | North & South Clone | Civil War strategy/action clone | Solo |

All live URLs follow the pattern `https://github.freaxnx01.ch/<repo>/`.

## Content & data model

Hand-authored static HTML — one card per game, no JSON/fetch/build layer (6 items is
too small to justify a data-driven pipeline). Each card shows:

- Cropped screenshot icon (thumbnail)
- Game name
- One-liner description
- Mode badge(s): `Solo`, `Multiplayer · Peer2Peer`, `Multiplayer · Local` — a game can
  show more than one badge (e.g. Tschau Sepp shows both Solo and Peer2Peer; Tank Toys
  shows both Peer2Peer and Local). `Server` is a reserved-but-unused badge value for
  future games that use a real backend — none do today.
- `▶ Play` link to the live game URL
- Click/hover on the thumbnail enlarges the full screenshot in a lightweight CSS+JS
  lightbox (no dependencies)

## Screenshot capture pipeline

One-time script, run locally this session:

1. `pip install playwright && playwright install chromium` (~300MB download).
2. Python script (`scripts/capture_screenshots.py` in the repo, kept after the run so
   it can be re-run manually later) that, for each of the 6 live URLs:
   - Launches headless Chromium, navigates to the URL.
   - Waits for network-idle plus a fixed extra delay (~2s) so canvas-based games
     render at least one real frame instead of a blank/loading state.
   - Saves a full-viewport screenshot to `games/assets/<repo>.png`.
   - Saves a center-cropped, resized (256×256) version to
     `games/assets/<repo>-icon.png` for the card thumbnail.
   - On load failure/timeout: logs and skips that game rather than aborting the run;
     any skipped game is flagged so a placeholder can be swapped in by hand.
3. Both PNGs per game are committed as regular binary assets under `games/assets/`.
4. No ongoing automation (no GitHub Action) — re-running the script is a manual,
   on-demand step if a game's visuals change later.

## Visual design

Standalone dark, arcade-hub aesthetic — independent of the root page's
`jekyll-theme-hacker` look, since these are indie/retro-style games:

- Responsive CSS Grid card layout (`auto-fill`/`minmax`), readable down to mobile
  widths.
- Subtle hover lift on cards; monospace/pixel-ish accent font for headings.
- Apply `frontend-design` skill guidance during implementation so it doesn't read as
  generic templated Bootstrap cards.

## Testing / verification

After implementation:

- Open `games/index.html` locally in a browser (or via `python3 -m http.server`).
- Confirm all 6 thumbnails render and the lightbox opens/closes correctly.
- Confirm all `▶ Play` links resolve to the correct live game URLs.
- Check layout at a couple of viewport widths (mobile + desktop).
- Confirm the root page's new `/games/` link works once deployed.

## Out of scope

- `game-moki-racer` and `civil-war-battlefield` (not yet deployed to Pages).
- Any backend/server-hosted multiplayer game (none exist today; `Server` badge is
  reserved for the future).
- Automated/scheduled screenshot refresh (CI-based capture) — explicitly deferred.
