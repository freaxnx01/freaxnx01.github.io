# Fullscreen toggle in `#game-nav` for all games — design

**Issue:** #25 — "Alle Browser-Games: Vollbild-Button"
**Date:** 2026-09-28

## Goal

Every `freaxnx01/game-*` game on the hub gets a fullscreen toggle (⛶) in its
standard bottom-right `#game-nav` overlay, and every new game ships with it.

## Scope

- **In:** the 41 `freaxnx01/game-*` repos linked from `games/index.html`; the
  canonical nav snippet template; a rollout script + tests in this hub repo.
- **Out:** external games (e.g. `julia-hase/*` — left as their author made them),
  a keyboard shortcut (collides with game keys), a shared hub-hosted
  `game-nav.js` (separate idea — would change the nav mechanism for every game),
  per-game in-canvas fullscreen buttons.

## Approach

One **self-contained snippet**, appended before `</body>` of each game's served
page. It does not edit the existing nav markup; it inserts a button into
whatever `#game-nav` exists at runtime. That makes it identical for both nav
variants (static A, self-healing B) and for the hand-patched self-healing navs
(e.g. `game-n-s-clone`), without parsing them.

A rollout script `scripts/add_fullscreen_toggle.py` (modelled on
`scripts/add_game_favicons.py`) injects the snippet into every game repo,
releases each game as a minor version, and pushes.

## The snippet

Delimited by marker comments so the script can detect and replace it:

```html
<!-- game-nav-fullscreen:start -->
<script>/* IIFE */</script>
<!-- game-nav-fullscreen:end -->
```

Behaviour of the IIFE:

1. **Feature check** — if neither `document.fullscreenEnabled` nor
   `document.webkitFullscreenEnabled` is true (e.g. iPhone Safari), do nothing:
   no button, no separator.
2. **`ensure()`** — if `#game-nav` exists and `#fs-toggle` does not, create
   `<button id="fs-toggle" type="button">` plus a `·` separator
   (`<span aria-hidden="true" style="color:#5a6072">·</span>`, same as the nav's).
   - If `#version-badge` is a child of the nav: insert **separator + button
     directly after the badge** → `v0.3.1 · ⛶ · More Games… · …`.
   - Otherwise: insert **button + separator as the nav's first children**.
3. **Styling** — button reset to look like the nav links:
   `background:none;border:0;padding:0;margin:0;cursor:pointer;color:#8fd8e8;font:inherit;line-height:1`.
4. **Click** — if `document.fullscreenElement || document.webkitFullscreenElement`
   → `exitFullscreen()` (webkit fallback); else
   `document.documentElement.requestFullscreen()` (webkit fallback). Promise
   rejections are caught and ignored. Then `btn.blur()` — keyboard games
   otherwise re-trigger the focused button with Enter/Space (lesson from
   `game-nibbles`' i18n toggle).
5. **State** — on `fullscreenchange` / `webkitfullscreenchange` and at creation,
   update: text `⛶` (enter) / `✕` (exit); `title` + `aria-label`
   `Fullscreen` / `Exit fullscreen`; `aria-pressed` `false` / `true`.
6. **Re-assertion** — `ensure()` runs immediately, on `DOMContentLoaded`, on
   `load`, and on a `setInterval` of 250 ms for 40 ticks (10 s) — the same
   schedule as nav Variant B, so a dc bundle's `documentElement.replaceWith()`
   that recreates the nav is followed by the button being re-added. The state
   listeners are registered once on `document` (survives `replaceWith`).

Fullscreen targets `document.documentElement`, so the nav remains visible and
clickable in fullscreen; Esc still exits natively (the change event updates the
icon).

Labels are English, like the rest of the nav (`More Games…`, `Source`, …).

## Rollout script — `scripts/add_fullscreen_toggle.py`

- **Game discovery:** reuse `discover_games()` from `add_game_favicons.py`
  (import, don't copy); only the `repo` field is needed.
- **Clones:** its own clean clones under `~/.cache/game-rollout/<repo>`
  (`--clones-root` to override) — **not** the sibling working copies in
  `~/repos/github/freaxnx01/public/`, some of which carry in-progress local
  branches (e.g. `game-wipfelkratzer` on `rb121b`). Clone if missing, else
  `fetch` + `checkout <default>` + `reset --hard origin/<default>` (the cache is
  script-owned, never hand-edited). Default branch from `refs/remotes/origin/HEAD`.
- **Served file:** `docs/index.html` for `game-gorillazz` (Pages serves
  `main:/docs`); `index.html` otherwise. Table-driven (`SERVED_FILE`).
- **Pure functions (unit-tested):**
  - `inject_snippet(html) -> (html, changed)` — insert the snippet before the
    last `</body>`; if markers exist, replace the block between them (so a
    changed snippet can be re-rolled); unchanged if identical. Raises if there is
    no `</body>`.
  - `has_game_nav(html) -> bool` — `"game-nav"` occurs anywhere in the page
    (static markup or a self-healing IIFE's `"game-nav"` id string).
  - `bump_minor(version) -> str` — `"0.11.1"` → `"0.12.0"`.
  - `read_version(version_js) -> str | None` / `write_version(version_js, v) -> str`
    — for the `window.GAME_VERSION = "X.Y.Z";` line.
- **Per-repo flow:**
  1. Page has no `game-nav` → `skipped: no game-nav`.
  2. `inject_snippet` unchanged → `skipped: up to date`.
  3. Write, commit `feat(nav): add fullscreen toggle` (served file only).
  4. If `version.js` has `GAME_VERSION`: bump minor, write it,
     `git cliff --tag vX.Y.0 -o CHANGELOG.md`, commit `version.js` +
     `CHANGELOG.md` as `chore(release): vX.Y.0`, `git tag vX.Y.0`.
     If not: report `released: no (no version.js)`.
  5. `git push --follow-tags origin <default>`.
  6. Status line per repo; summary counts at the end; exit non-zero if any
     repo failed.
- **Flags:** `--dry-run` (report only: no write, commit, tag, or push),
  `--only REPO[,REPO…]`, `--clones-root PATH`.
- **Git env:** `GIT_TERMINAL_PROMPT=0` (fail fast, as in the favicon script).

The script is **built and tested by the pipeline; it is run by a human**
locally — the `ai-implement` pipeline cannot push to other repos, and pushing
tags to 41 public repos should be a watched run (`--dry-run` first, then a
one-game pilot with `--only`, then the rest).

## Canonical template

`docs/superpowers/specs/2026-07-13-game-card-feedback-star-snippet.html` gets
the snippet block appended after both variants' nav code, with a header note
that it applies to either variant. New games thus ship with the toggle. The
snippet's single source is a file `scripts/fullscreen_snippet.html` read by the
script; a test asserts the template contains it verbatim.

## Testing

- **pytest unit tests** (`tests/test_add_fullscreen_toggle.py`) for every pure
  function above, including: injection before `</body>`, idempotency,
  marker-block replacement, missing `</body>`, `bump_minor` edge cases,
  served-file resolution for `game-gorillazz`, template ↔ snippet equality.
- **Headless Playwright test** (`tests/test_fullscreen_snippet_browser.py`) on
  local fixture pages:
  - static nav with `#version-badge` → button is the element right after the
    badge's separator; `aria-label` = `Fullscreen`;
  - nav without badge → button is the nav's first child;
  - fullscreen unsupported (stub `fullscreenEnabled = false` via init script)
    → no `#fs-toggle`;
  - self-healing: remove `#game-nav` and re-create it without the button →
    button re-appears within 1 s;
  - no `#game-nav` at all → no error on the console, no button.
  (Real fullscreen entry is not asserted — headless Chromium's fullscreen is
  not a reliable signal; the click handler is covered by a stubbed
  `requestFullscreen` being called once.)

## Acceptance criteria

- `scripts/add_fullscreen_toggle.py --dry-run` lists all 41 hub games with a
  status, touching nothing.
- After a real run, every game whose page has a `game-nav` shows ⛶ right after
  the version badge (or first in the nav when there is no badge), toggles
  fullscreen, flips to ✕ in fullscreen, and is hidden where the Fullscreen API
  is unavailable.
- Re-running the script produces no commits.
- Each changed game with a `version.js` has a new minor tag, matching
  `version.js`, and a `CHANGELOG.md` entry.
- dc-bundled self-healing games keep the button after their unpack.
- The canonical nav template contains the snippet.
