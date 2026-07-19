# Games hub: search/filter textbox — design

**Date:** 2026-07-19

## Goal

Add a text search box to the Browser Games Hub (`games/index.html`) so a user can
narrow the grid by typing a game's name (or part of it), on top of the existing
mode/category filters and sort control.

## UI changes (`games/index.html` + `games/style.css`)

- New row at the **top of `.hub__filters`**, before the existing mode filter row:
  `<div class="filter-row filter-row--search"><input type="search" id="game-search" placeholder="Search games…" aria-label="Search games by name"></div>`
- Styled to match the panel's existing look: same border/spacing rhythm as the other
  `.filter-row`s, full-width input, `--mono`/`--text-dim` placeholder color. No new
  color hues — reuse existing panel tokens.
- No custom clear button — `type="search"` gives the native browser clear-× for free.
- No new empty-state UI — the existing `.hub__count` "Showing N of M games" text
  already communicates zero results ("Showing 0 of M games"); confirmed sufficient,
  no extra message/illustration needed.

## Filter logic (`games/filter.js`)

- Add `search` state (default `""`), alongside existing `primary`/`sub`/`category`.
- Add `matchesSearch(title)`: case-insensitive substring match — `title.toLowerCase().indexOf(search) !== -1`
  when `search` is non-empty, else always `true`. Plain substring only; no
  fuzzy/word-split matching (~30 titles, predictability over cleverness).
- `title` is read per-card from the existing `.card__title` element's `textContent`.
- Extend `matches(modes, cardCategory, title)` to AND in `matchesSearch(title)`
  alongside the current mode/category checks — search narrows whatever mode/category
  is currently selected, consistent with how mode and category already compose.
- Wire the input's `input` event (fires on every keystroke, including native-clear-×
  clicks) to: lowercase-trim the value into `search`, then call `apply()`. No
  debounce — substring check over ~30 DOM nodes is instant, and debouncing would only
  add a perceptible lag for no benefit at this scale.
- `.hub__count` text unchanged in shape; search-narrowed results just further reduce
  `visible`, same counter logic as category filtering today.

## Interaction with sort

No changes needed — sort reorders `.hub__grid` children independently of
visibility; `apply()` (which search also triggers) only toggles `card--hidden` /
re-triggers the enter animation, same as it does today after a sort change.

## Testing

- Manual: open `games/index.html` locally, type partial/full/mixed-case game names,
  confirm live narrowing with no submit step; combine search with each mode and
  category filter to confirm AND logic; clear via the native ×, confirm the full
  grid returns; confirm the count text updates correctly including a 0-result case;
  tab-order/focus check on the new input.
- No automated test suite exists for this static page, consistent with prior hub
  changes (see `2026-07-13-games-hub-categories-new-sort-design.md`).
