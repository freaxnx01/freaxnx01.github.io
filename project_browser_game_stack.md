---
name: project-browser-game-stack
description: "The browser-game AI-instructions stack for game-* repos — versioning (git tag + version.js), changelog, and rollout status"
metadata: 
  node_type: memory
  type: project
  originSessionId: b215d5a2-06b3-4359-9b82-4f6a9c8de736
---

`freaxnx01/ai-instructions` has a **`browser-game` stack overlay**
(`.ai/stacks/browser-game.md`, merged 2026-07-18 in PR #17) for the buildless
vanilla HTML/CSS/JS `game-*` repos. A game adopts it by running
`/sync-ai-instructions browser-game` from the game repo, which assembles
`CLAUDE.md`/`SKILL.md`/`.github/copilot-instructions.md` from base + the overlay.

**Versioning convention (the key thing):**
- The **git tag `vX.Y.Z` is the authoritative source of truth** (on `main`, or
  `master` for `game-n-s-clone`).
- `version.js` is a **display mirror** of the tag, NOT a second source. Standard
  form used across all games: classic `window.GAME_VERSION = "X.Y.Z";` loaded via
  `<script src="./version.js">` before the game script.
- A small `vX.Y.Z` badge is populated FROM `version.js` (never hardcode the
  literal in markup, or it becomes a competing source) and is a **clickable link**
  to the repo's changelog: `<a href="https://github.com/freaxnx01/<repo>/blob/<branch>/CHANGELOG.md" target="_blank">vX.Y.Z</a>`.
  Where a repo has the standard `#game-nav` footer the badge sits inside it; where
  it doesn't, a standalone fixed bottom-right badge is used.
- Changelog: `CHANGELOG.md` (Keep a Changelog) + `cliff.toml` (Conventional
  Commits → git-cliff). Release flow: bump `version.js` → `chore(release): vX.Y.Z`
  → `git tag vX.Y.Z` → `git cliff --tag vX.Y.Z -o CHANGELOG.md`.

**Rollout status: COMPLETE (2026-07-19).** All **25 `game-*` repos** are adopted
and tagged **`v0.1.0`** (baseline; kick-fury was realigned down from its pilot
`v1.0.0`). Landed via **direct commit to the default branch + tag** (no PRs),
each gated by a headless Playwright check (badge renders `vX.Y.Z` + is a working
changelog link). **`game-gorillazz` special case:** it is NOT bundled and is
served via GitHub Pages from **`main` branch `/docs`** (legacy branch source, not
root and not its `deploy.yml` Actions workflow). So its `version.js` + badge live
in **`docs/index.html`** / `docs/version.js` (the served page); `src/` is the
working source and has diverged (older, no game-nav) — the served `docs/` copy is
the maintained one. It is fully adopted (v0.1.0, badge, changelog).

**dc-bundled games caveat:** several games are **dc-bundled** (`source/`/`*.dc.html`
→ generated `index.html`+`support.js`, marker `type="text/x-dc"`). The rollout
edited only the SERVED `index.html`; on the next re-bundle the version.js load +
badge must be carried into the source or they're lost. Some bundlers
(e.g. `game-dustline`, `-plod`, `-fruit-frenzy`, `-stack-duel`, `-gem-cascade`,
`-marquee-quiz`, `-n-s-clone`) do a destructive `document.documentElement.replaceWith()`
on unpack, so their badge lives inside a **self-healing IIFE** (setInterval +
DOMContentLoaded/load) that re-asserts it after each unpack.

**Known pre-existing bugs (NOT caused by the rollout):**
- `game-geography-quiz` — **FIXED (2026-07-19).** Its ~39 SVG "Expected number"
  errors + 8 image 404s came from the dc template living in a live `<x-dc>`
  element, so the browser parsed its `{{ }}` placeholders in SVG attrs
  (`d`/`cx`/`cy`) and `<img src>` before `support.js` hydrated. Fix: moved the
  template into an inert `<template data-dc-tpl>` and taught `support.js`'s two
  runtime template reads (`parseDcDocument` + `boot`) to fall back to it. This is
  the general fix for any dc game that puts dynamic SVG/img in its template.
- `game-moon-lander` — **FIXED (2026-07-19).** `groundY` threw
  `Cannot read '.length' of undefined` on first paint: `renderVals()` runs during
  React's initial `render()` (before `componentDidMount()` builds `this.terrain`)
  and its altitude guard checked `this.groundY` (a method, always truthy) instead
  of `this.terrain`. Now guards `this.terrain`. Fixed in `index.html` + the
  `.dc.html` source.
- `game-n-s-clone` — **FIXED (2026-07-19).** Its bundler `replaceWith`s the DOM
  on unpack, wiping the static `#game-nav`, so the nav links never rendered
  (`#game-nav` count was 0 live). The self-healing overlay only recreated the
  badge; it now rebuilds the whole nav (links + badge, re-injecting buttons.js
  for the star) after each unpack — the general fix for any self-healing dc game
  whose nav is wiped. All three earlier-flagged bugs are now resolved.

**Why:** The user explicitly wanted SemVer + changelog to apply to game projects
like they do to the .NET/Go/Flutter stacks. Design spec + plan live in
`ai-instructions/docs/superpowers/{specs,plans}/2026-07-18-browser-game-stack-overlay*`.

**How to apply:** To version/roll out another game, run
`/sync-ai-instructions browser-game` in it, add `version.js` + a badge +
`CHANGELOG.md` + `cliff.toml`, verify the badge renders headless, then PR + tag.
See also [[project-game-hub-conventions]].
