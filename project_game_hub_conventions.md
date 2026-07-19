---
name: project-game-hub-conventions
description: How new games get published and added to the Games Hub at github.freaxnx01.ch/games
metadata: 
  node_type: memory
  type: project
  originSessionId: 30ca226d-80cd-4490-98f6-7db7d0df9d2e
---

Each game is its own public repo named `game-<name>` (GitHub Pages, root `index.html`,
served at `https://github.freaxnx01.ch/game-<name>/`). Publishing a new game end-to-end:

1. Create the repo: `gh repo create game-<name> --public --source=. --remote=origin --push`
   from a local dir containing the built `index.html`.
2. Enable Pages: `gh api -X POST repos/freaxnx01/game-<name>/pages -f 'source[branch]=main' -f 'source[path]=/'`.
3. Inject the **standard hub-nav overlay** before `</body>`: a fixed-position `<nav id="game-nav">`
   with a **version badge** (first item, `v0.1.0` → links to the repo's `CHANGELOG.md`),
   "More Games…" (→ `https://github.freaxnx01.ch/games/`), "Source" (→ repo URL),
   "Feedback" (→ `<repo>/issues/new?title=%5BFeedback%5D%20<repo>&labels=feedback`), and a
   GitHub star button (`buttons.github.io/buttons.js`). The **canonical template** (with
   `{{REPO}}`/`{{BRANCH}}` placeholders) is
   `freaxnx01.github.io/docs/superpowers/specs/2026-07-13-game-card-feedback-star-snippet.html`
   — copy from there, not from a game repo. It has **two variants**: **A) static** for normal
   games; **B) self-healing IIFE** for dc-bundled games whose bootstrapper does
   `document.documentElement.replaceWith()` on unpack (it wipes the static nav, so the IIFE
   re-asserts it — grep the served `index.html` for `documentElement.replaceWith` to tell them
   apart). **Prerequisite:** the repo carries the browser-game stack files (`version.js` with
   `window.GAME_VERSION`, `CHANGELOG.md`, `cliff.toml`) — see [[project-browser-game-stack]].
   The version badge is thus part of THIS post-export overlay, not the dc `.dc.html` source; a
   re-export just re-injects this overlay (which now includes the badge).
4. In the hub repo (`freaxnx01.github.io`), add a `<article class="card">` to `games/index.html`
   with `data-modes`, `data-category` (one of: action/all/arcade/card/puzzle/quiz/racing/
   sandbox/shooter/sports/strategy), and `data-added="YYYY-MM-DD"` — the NEW badge is
   auto-computed client-side from `data-added` by `filter.js` (14-day window), no manual tag needed.
5. Add the repo name to `REPOS` in `scripts/capture_screenshots.py` and run
   `python3 scripts/capture_screenshots.py game-<name>` to generate the hub thumbnail +
   full screenshot. Only add an `ACTIONS` recipe if the title screen isn't a good shot —
   many games (e.g. a menu-driven quiz) look fine captured as-is.

**Why:** Followed exactly when publishing `game-marquee-quiz` from a design-handoff zip —
matching this pattern made the new game indistinguishable from the other 20 in nav,
feedback flow, and hub presentation.

**How to apply:** Any "publish a new game" or "add X to the hub" request should follow
these 5 steps in order; steps 3-5 are easy to skip and leave the game feeling
inconsistent with the rest of the hub.

See also [[feedback-screenshot-capture-recipes]] (if it exists) and [[feedback-worktree-tool-scope]].
