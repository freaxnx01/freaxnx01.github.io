# Games Hub: Retro/Clones filter — design

## Problem

The hub mixes the user's own original game ideas with browser recreations of
existing/classic games (Space Invaders, Pac-Man, Pong, etc.). There's no way to
filter by that distinction, only by mode (solo/multiplayer) and genre.

## Design

Add a boolean toggle filter, following the exact pattern already established by
`🧒 Kids only` (`data-kids` / `kidsOnly` / `matchesKids`).

### Data: `data-retro` attribute

Add `data-retro="true"` to the `<article class="card">` element for each of the
following 10 games in `games/index.html` (leave all other cards unchanged — the
attribute's absence means "original", same as `data-kids`' absence means
"not for kids"):

- Neon Pong (Pong clone)
- Maze Muncher (Pac-Man clone)
- Nibbles (classic Nibbles/Snake clone)
- Gorillazz ("clone of the classic QBasic Gorillas game" — per its README)
- Moon Lander (Lunar Lander clone)
- North & South Clone (explicit in name/README)
- Space Invaders (explicit clone)
- Cluck & Load ("Moorhuhn-style shooting gallery" — per its README)
- Gem Cascade ("match-3 tile-swapper (Bejeweled-style)" — per its README)
- BMX Beach Jam ("inspired by the classic California Games BMX event" — per its README)

**Scope note:** "clone" means recreating an existing *video game*. Digitizing a
real-world board/card game the user built themselves (Battleship Toys, Zen
Sudoku, Criss Cross, WORTDUELL/Scrabble-style, Tschau Sepp, Die Millionenfrage)
is an original digital adaptation, not a clone — excluded from this list.
Splashdown and Fruit Frenzy were considered (both README's describe them as
"inspired by" a specific classic game) but are explicitly excluded per user
confirmation — the inspiration is loose enough (structure/style, not a direct
recreation) that they read as original games.

### UI: new toggle button

In the `filter-row--search` row of `games/index.html`, next to the existing
`🧒 Kids only` button, add:

```html
<button type="button" class="filter-btn" id="retro-toggle" aria-pressed="false">🕹️ Retro/Clones only</button>
```

### Logic: `games/filter.js`

Mirror the existing kids-filter wiring exactly:

- A new `retroToggle` element lookup (`document.getElementById("retro-toggle")`),
  alongside the existing `kidsToggle` lookup.
- A new `retroOnly` state boolean (default `false`), alongside `kidsOnly`.
- A new `matchesRetro(cardRetro)` function:
  ```js
  function matchesRetro(cardRetro) {
    return !retroOnly || cardRetro === true;
  }
  ```
- In `apply()`, read `var cardRetro = card.hasAttribute("data-retro");` alongside
  the existing `cardKids` read, and thread it through `matches()`.
- `matches()` gains a `cardRetro` parameter and calls `matchesRetro(cardRetro)`
  in both its branches (WIP and normal), exactly where `matchesKids(cardKids)`
  already appears.
- A click handler on `retroToggle` that flips `retroOnly`, updates
  `aria-pressed`, and calls `apply()` — mirroring the existing `kidsToggle`
  click handler exactly.

This filter composes for free with every other filter (mode, category, search,
kids, WIP) since it plugs into the same `matches()` predicate chain.

## Testing

Manual (buildless static site, no test runner):
- Toggle `🕹️ Retro/Clones only` → confirm exactly the 10 listed games remain
  visible (and their count matches `.hub__count`).
- Combine with an existing filter (e.g. genre = Arcade, or Kids only) → confirm
  both filters apply together (AND, not OR).
- Toggle off → all games return.
- Confirm the button's `aria-pressed` state updates and keyboard/screen-reader
  behavior matches the existing `Kids only` button (same markup pattern).
