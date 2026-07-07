# Publish 5 new browser games + wire up nav — design

**Date:** 2026-07-07

## Goal

Publish the 5 game zips created today into their own public GitHub repos with
GitHub Pages, add them to the Browser Games Hub (alphabetically), and give every
hub game an in-page footer with "More Games…" and "Source" links.

## Games → repos

| Zip (today) | Title | Repo | Hub badge |
|---|---|---|---|
| California Games BMX clone | BMX Beach Jam | `game-bmx-beach-jam` | Solo |
| Racer Beach Buggy Game | Beach Buggy Racer | `game-beach-buggy-racer` | Solo |
| Space invaders clone | Space Invaders | `game-space-invaders` | Solo |
| Tux Racer with Squirrel and Axolotl | Splashdown | `game-splashdown` | Solo |
| Two-player Tetris game | Stack Duel | `game-stack-duel` | Multiplayer · Local |

`game-tschau-sepp` (also in today's zips) already exists and is in the hub — skip
creation; it still gets the footer as one of the existing repos.

## Per new repo

- Push runtime files: `index.html` (footer injected) + any `src/`/`source/` +
  `README.md` (Tux: `REPO_README.md` → `README.md`) + `LICENSE` if present.
- Skip internal docs: `HANDOFF.md`, `PUBLISH_INSTRUCTIONS.md`, `CLAUDE.md`,
  `CLAUDE_INSTRUCTIONS.md`.
- Public repo, default branch `main`. Enable Pages (branch `main`, path `/`).
- Play URL = `https://github.freaxnx01.ch/<repo>/` (project pages resolve under the
  user custom domain, same as the existing 6). Replace README placeholder Play URL
  with this real one.

## Footer nav (all 11 hub repos: 5 new + 6 existing)

Inject a fixed, low-opacity bottom-right overlay before `</body>` of each game's
`index.html`:

```html
<!-- game-nav -->
<nav id="game-nav" aria-label="Game navigation" style="position:fixed;right:10px;bottom:8px;z-index:2147483647;display:flex;gap:12px;align-items:center;font:600 13px/1.4 system-ui,-apple-system,sans-serif;padding:6px 11px;border-radius:8px;background:rgba(15,17,26,.55);backdrop-filter:blur(4px);-webkit-backdrop-filter:blur(4px);opacity:.55;transition:opacity .2s" onmouseover="this.style.opacity=1" onmouseout="this.style.opacity=.55">
  <a href="https://github.freaxnx01.ch/games/" style="color:#8fd8e8;text-decoration:none">More Games…</a>
  <span style="color:#5a6072" aria-hidden="true">·</span>
  <a href="https://github.com/freaxnx01/REPO" target="_blank" rel="noopener" style="color:#8fd8e8;text-decoration:none">Source</a>
</nav>
```

Replace `REPO` with the repo name. Existing 6 repos: clone → inject → commit →
push. Excludes `game-moki-racer` (not in the hub).

## Hub (`games/index.html`)

Add 5 cards, re-sort all 11 alphabetically by title:

Barrel Blast · Beach Buggy Racer · BMX Beach Jam · Esel vs. Karotte · Gorillazz ·
North & South Clone · Space Invaders · Splashdown · Stack Duel · Tank Toys ·
Tschau Sepp

New card descriptions:
- Beach Buggy Racer — "Isometric arcade beach racer."
- BMX Beach Jam — "Retro 8-bit BMX trick game."
- Space Invaders — "Retro arcade shooter clone."
- Splashdown — "Endless waterslide racer."
- Stack Duel — "Two-player Tetris battle."

## Thumbnails

Add the 5 new repos to `scripts/capture_screenshots.py` `REPOS`, run after the
games are live, commit the generated `assets/<repo>.png` + `-icon.png`.

## Order of operations

1. Create + deploy 5 new repos (independent → parallel).
2. Inject footer into the 6 existing repos (independent → parallel).
3. Run screenshot capture for the 5 new games.
4. Update + commit the hub (`freaxnx01.github.io`).
