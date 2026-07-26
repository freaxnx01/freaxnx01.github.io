# Random game button — design

Issue: [#4](https://github.com/freaxnx01/freaxnx01.github.io/issues/4) — "Button
for picking a random game".

## Problem

The games hub (`games/index.html`) lists 33+ games behind a search box, a
mode filter, a category filter, and Kids/Retro toggles. There's no quick way
to say "surprise me" — a visitor has to either scroll the whole grid or
already know what they want.

## Scope

Additive only. No changes to existing filtering, search, sorting, or card
markup beyond adding one button and a few lines of `disabled`-state logic.

## Behavior

- **Filter scope:** clicking Random picks among only the cards currently
  visible under the active filters/search/toggles — not the full catalog.
  This makes it "surprise me from what I'm looking at" rather than ignoring
  the user's own narrowing.
- **Action on pick:** opens the chosen game in a new tab, via the same
  `href`/`target="_blank"` navigation its card's own "▶ Play" link already
  uses. No in-page scroll/highlight behavior.
- **Empty match:** if the current filter/search state matches zero cards,
  the button is disabled (greyed out, non-clickable) rather than showing an
  error state.
- **Placement:** in the `filter-row--search` row of `games/index.html`,
  alongside the search input and the 🧒 Kids only / 🕹️ Retro only toggles.

## Architecture

**Extend `games/filter.js` in place — no new script file.** `filter.js`
already owns the single source of truth for which cards are visible: its
`apply()` function (`games/filter.js:65`) toggles a `card--hidden` class on
every `.card` element and re-runs on every filter/search/toggle change. A
separate `random.js` would have to duplicate that visibility computation (or
re-derive it via a `MutationObserver` on the `card--hidden` class), which is
unnecessary complexity for what `apply()` already computes for free.

Changes to `games/filter.js`:

1. Look up the new `#random-game-btn` element alongside the other button
   references at the top of the IIFE (same pattern as `searchInput`,
   `kidsToggle`, `retroToggle`).
2. In `apply()`, immediately after the `visible` count is finalized, set
   `randomBtn.disabled = visible === 0` (guarded by `if (randomBtn)`,
   matching the existing `if (count)` guard style).
3. Add one `click` listener on `randomBtn` (guarded the same way the
   `kidsToggle`/`retroToggle` listeners are): collect
   `cards.filter(function (c) { return !c.classList.contains("card--hidden"); })`,
   pick one at `Math.floor(Math.random() * visibleCards.length)`, read its
   `.card__play` anchor's `href`, and call
   `window.open(href, "_blank", "noopener")`.

Changes to `games/index.html`:

- Add `<button type="button" class="filter-btn" id="random-game-btn">🎲 Random</button>`
  inside the existing `<div class="filter-row filter-row--search">`, after
  the Kids/Retro toggle buttons.

No changes to `games/style.css` are anticipated — `filter-btn` and its
`:disabled` state should be styled via the existing `.filter-btn` class and a
plain `:disabled` selector if one doesn't already exist; add a minimal
`.filter-btn:disabled` rule (opacity + `cursor: not-allowed`) only if the
button doesn't already look visibly disabled with the browser default.

## Testing

Manual, static site, no build step (matches this repo's existing test
convention):

- Click Random with no filters active — confirm a new tab opens to one of
  the 33+ games, and repeated clicks can land on different games.
- Apply a narrow filter (e.g. 🧒 Kids only, or a category with very few
  entries) — confirm Random only ever opens a game matching that filter.
- Filter/search down to zero matching cards — confirm the Random button
  becomes disabled and is not clickable.
- Clear the filter again — confirm the Random button re-enables.
- Keyboard: confirm the button is reachable via Tab and activates via
  Enter/Space (native `<button>` behavior, no custom handling needed).
