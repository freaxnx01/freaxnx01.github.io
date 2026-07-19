# Games hub: Kids Games filter — design

**Date:** 2026-07-19

## Goal

Add a "Kids only" toggle to the Browser Games Hub (`games/index.html`) that
narrows the grid to kid-appropriate games, composing with the existing
mode/category/search filters (all ANDed together).

## Data model addition (per `.card`)

A new boolean attribute, `data-kids="true"`, added only to cards that qualify
as kid-appropriate (absent/omitted on cards that don't — no `data-kids="false"`
needed, matching the existing sparse-attribute style of the codebase).

Kid-appropriate is judged on theme (no war/combat realism, no gore, no explicit
weapons-as-the-point) and complexity, not mechanics alone — a classic
arcade shooter (Space Invaders) or cartoonish target-shooting game
(Cluck & Load, Gorillazz's banana-throwing) can still qualify if the tone is
light. Reviewed and confirmed with the user game-by-game.

### `data-kids="true"` (27 games)

Photo Puzzler, Criss Cross, Die Millionenfrage, Neon Pong, Zen Sudoku,
WORTDUELL, Gem Cascade, Maze Muncher, Nibbles, The Marquee, Acronym Quiz,
Battleship Toys, Beach Buggy Racer, BMX Beach Jam, Esel vs. Karotte,
Fruit Frenzy, Geography Quiz, Moon Lander, PLOD, Splashdown, Stack Duel,
Tank Toys, Tschau Sepp, Voxel Sandbox, Gorillazz, Space Invaders, Cluck & Load

### Not tagged (5 games — war/combat themes)

Barrel Blast, Dustline, North & South Clone (Civil War battle), Sky Fury
(WWII combat), Kick Fury (fighting)

## UI changes (`games/index.html` + `games/style.css`)

- Extend the existing search row (`.filter-row--search`, added by the prior
  search-box feature) to also hold a toggle pill button, placed after the
  search input in the same row:
  `<button type="button" class="filter-btn" id="kids-toggle" aria-pressed="false">🧒 Kids only</button>`
- Reuses the existing `.filter-btn` / `.filter-btn.is-active` styling
  (pill, `--bg-card` default, `--accent` background when active) — no new
  CSS rules needed for the button itself, only a flex/gap tweak on
  `.filter-row--search` to hold two children side by side instead of one
  full-width input.
- `.search-input`'s `max-width: 22rem` stays; the row becomes
  `display: flex; gap: 0.5rem; align-items: center;` so the toggle sits
  beside it rather than below.

## Filter logic (`games/filter.js`)

- Add `kidsOnly` state (default `false`), alongside `search`.
- Add `matchesKids(cardKids)`: `!kidsOnly || cardKids === true`.
- Extend `matches(modes, cardCategory, title, cardKids)` to AND in
  `matchesKids(cardKids)` alongside the existing three checks.
- `apply()` reads `card.hasAttribute("data-kids")` per card and passes that
  boolean through to `matches()`.
- Click handler on `#kids-toggle` toggles `kidsOnly`, updates
  `aria-pressed`/`is-active` (reusing the existing `setPressed`-style
  pattern already used for mode/category buttons), and calls `apply()`.
- `.hub__count` text unchanged in shape — kids-filtering further narrows
  `visible`, same counter logic as every other filter dimension.

## Testing

- Manual/live-browser: toggle "Kids only" alone, confirm the grid narrows to
  exactly the 27 tagged cards and the count reads "Showing 27 of N games";
  toggle off, confirm full grid returns. Combine with search (e.g. "fury" —
  matches only Sky Fury/Kick Fury, both un-tagged) to confirm AND logic
  yields zero results. Combine with a category filter that includes both
  tagged and untagged games (e.g. Arcade: Neon Pong tagged, Barrel Blast/
  Dustline untagged) and confirm only the tagged subset shows. No automated
  test suite exists for this page, consistent with prior hub-feature specs.
