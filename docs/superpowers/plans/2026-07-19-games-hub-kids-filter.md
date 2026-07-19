# Games Hub Kids Games Filter Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a "Kids only" toggle to the Games Hub (`games/index.html`) that narrows the grid to 27 kid-appropriate games, composing (AND) with the existing mode/category/search filters.

**Architecture:** A `data-kids="true"` attribute is added to the 27 qualifying `<article class="card">` elements (data model). A toggle `<button>` is added to the existing search row. `games/filter.js` gains a `kidsOnly` state variable, a `matchesKids()` check ANDed into the existing `matches()` pipeline, and a click handler that flips `kidsOnly` and re-runs the existing `apply()`.

**Tech Stack:** Static HTML/CSS/vanilla JS (no build step, no framework, no test runner — this repo's Games Hub page has no automated test suite; verification is manual/live-browser, matching every prior hub-feature spec in `docs/superpowers/specs/`).

## Global Constraints

- Exactly these 27 cards get `data-kids="true"` (verbatim titles as they appear in `games/index.html`'s `<h2 class="card__title">`): Photo Puzzler, Criss Cross, Die Millionenfrage, Neon Pong, Zen Sudoku, WORTDUELL, Gem Cascade, Maze Muncher, Nibbles, The Marquee, Acronym Quiz, Battleship Toys, Beach Buggy Racer, BMX Beach Jam, Esel vs. Karotte, Fruit Frenzy, Geography Quiz, Moon Lander, PLOD, Splashdown, Stack Duel, Tank Toys, Tschau Sepp, Voxel Sandbox, Gorillazz, Space Invaders, Cluck &amp; Load (note: `&amp;` is the literal HTML entity as it appears in the source — match it exactly, not a literal `&`).
- These 5 cards must NOT get the attribute (already correct if untouched — do not add it): Barrel Blast, Dustline, North &amp; South Clone, Sky Fury, Kick Fury.
- No `data-kids="false"` on non-qualifying cards — attribute is present-or-absent, not a boolean string on every card (matches the codebase's existing sparse-attribute style, e.g. `data-added`).
- Kids filter ANDs with existing mode/category/search filters — never resets them.
- Reuse the existing `.filter-btn` / `.filter-btn.is-active` CSS classes for the toggle — no new color hues, no new pill styling.
- Toggle lives in the existing `.filter-row--search` row, after the search input.

---

### Task 1: Tag kid-appropriate cards with `data-kids="true"`

**Files:**
- Modify: `games/index.html` (27 `<article class="card" ...>` opening tags, one per qualifying game)

**Interfaces:**
- Produces: `data-kids="true"` attribute, present only on the 27 qualifying `<article class="card">` elements. Task 3 reads this via `card.hasAttribute("data-kids")`.

This is a mechanical, precise transformation across 27 non-contiguous locations in a 490-line file. A script is more reliable than 27 manual find/replace edits (titles are unique per card, but several cards share identical `data-modes`/`data-category`/`data-added` combinations, so the `<article>` line alone isn't a safe match target — the script below matches each `<article>` tag together with the `<h2 class="card__title">` that follows it later in the same block, using the title text as the unique anchor).

- [ ] **Step 1: Run the tagging script**

From the repo root, run:

```bash
python3 - <<'PYEOF'
import re
from pathlib import Path

path = Path("games/index.html")
html = path.read_text()

KIDS_TITLES = [
    "Photo Puzzler", "Criss Cross", "Die Millionenfrage", "Neon Pong",
    "Zen Sudoku", "WORTDUELL", "Gem Cascade", "Maze Muncher", "Nibbles",
    "The Marquee", "Acronym Quiz", "Battleship Toys", "Beach Buggy Racer",
    "BMX Beach Jam", "Esel vs. Karotte", "Fruit Frenzy", "Geography Quiz",
    "Moon Lander", "PLOD", "Splashdown", "Stack Duel", "Tank Toys",
    "Tschau Sepp", "Voxel Sandbox", "Gorillazz", "Space Invaders",
    "Cluck &amp; Load",
]

pattern = re.compile(
    r'(<article class="card"(?:(?!>).)*)(>(?:(?!</article>).)*?<h2 class="card__title">('
    + "|".join(re.escape(t) for t in KIDS_TITLES)
    + r')</h2>)',
    re.DOTALL,
)

seen = set()

def add_attr(m):
    attrs, rest, title = m.group(1), m.group(2), m.group(3)
    seen.add(title)
    return attrs + ' data-kids="true"' + rest

new_html, count = pattern.subn(add_attr, html)
assert count == 27, f"expected 27 replacements, got {count}"
missing = set(KIDS_TITLES) - seen
assert not missing, f"titles never matched: {missing}"
path.write_text(new_html)
print("OK — tagged", count, "cards")
PYEOF
```

Expected output: `OK — tagged 27 cards`. If the script's `assert` fails, it means either a title in `KIDS_TITLES` doesn't exist verbatim in `games/index.html` (check for typos, e.g. curly vs. straight apostrophes, `&amp;` vs `&`) or a card already had `data-kids` from a prior run — investigate before re-running, do not loosen the assertion.

- [ ] **Step 2: Verify the count and spot-check exclusions**

```bash
grep -c 'data-kids="true"' games/index.html
```

Expected: `27`

```bash
grep -B1 -A6 '<h2 class="card__title">Barrel Blast</h2>\|<h2 class="card__title">Dustline</h2>\|<h2 class="card__title">Sky Fury</h2>\|<h2 class="card__title">Kick Fury</h2>\|North &amp; South Clone' games/index.html | grep 'data-kids'
```

Expected: no output (none of the 5 excluded cards should match) — the grep prints nothing, which is correct.

- [ ] **Step 3: Commit**

```bash
git add games/index.html
git commit -m "$(cat <<'EOF'
Tag kid-appropriate games with data-kids

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_012aMPnjtnPEx8ebyPK6tALY
EOF
)"
```

---

### Task 2: Kids-only toggle markup + styling

**Files:**
- Modify: `games/index.html:22-24` (the `.filter-row--search` block, add a toggle button after the search input)
- Modify: `games/style.css:104-106` (the `.filter-row--search` rule, add flex layout so the input and toggle sit side by side)

**Interfaces:**
- Produces: `<button id="kids-toggle" class="filter-btn" aria-pressed="false">` — Task 3 queries this by ID and listens for its `click` event, and toggles its `is-active` class / `aria-pressed` attribute (reusing the existing `.filter-btn.is-active` styling already defined in `games/style.css`, no new CSS needed for the button's states).

- [ ] **Step 1: Add the toggle button to the search row**

In `games/index.html`, find:

```html
      <div class="filter-row filter-row--search">
        <input type="search" id="game-search" class="search-input" placeholder="Search games…" aria-label="Search games by name">
      </div>
```

Replace with:

```html
      <div class="filter-row filter-row--search">
        <input type="search" id="game-search" class="search-input" placeholder="Search games…" aria-label="Search games by name">
        <button type="button" class="filter-btn" id="kids-toggle" aria-pressed="false">🧒 Kids only</button>
      </div>
```

- [ ] **Step 2: Make the search row a flex row so the toggle sits beside the input**

In `games/style.css`, find:

```css
.filter-row--search {
  width: 100%;
}
```

Replace with:

```css
.filter-row--search {
  width: 100%;
  display: flex;
  gap: 0.5rem;
  align-items: center;
}
```

- [ ] **Step 3: Verify markup and styling render correctly**

Serve the site locally and open it in a browser (or use a browser-automation tool):

```bash
cd games && python3 -m http.server 8123
```

Open `http://localhost:8123/` and confirm:
- The "🧒 Kids only" pill button appears immediately to the right of the search input, same row, vertically centered with it.
- It uses the same pill/border styling as the mode/category filter buttons (unstyled/default state — not yet clickable-functional, that's Task 3).
- No layout overflow/wrapping issues at a typical desktop width.

Stop the server (`Ctrl-C`) when done.

- [ ] **Step 4: Commit**

```bash
git add games/index.html games/style.css
git commit -m "$(cat <<'EOF'
Add Kids-only toggle to Games Hub filter panel

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_012aMPnjtnPEx8ebyPK6tALY
EOF
)"
```

---

### Task 3: Wire the Kids-only filter logic

**Files:**
- Modify: `games/filter.js:4-20` (add `kidsToggle` selector and `kidsOnly` state)
- Modify: `games/filter.js:33-45` (add `matchesKids`, extend `matches`)
- Modify: `games/filter.js:47-54` (`apply()` — read `data-kids` and pass it into `matches`)
- Modify: `games/filter.js:131-136` (add the `kidsToggle` click listener, right after the existing search-input listener block)

**Interfaces:**
- Consumes: `#kids-toggle` button and `data-kids` attribute from Task 1/2's changes.
- Consumes/extends: existing `matches(modes, cardCategory, title)` (from the prior search feature) and `apply()`.
- Produces: `kidsOnly` state variable and `matchesKids(cardKids)` function — no other task depends on these beyond this file.

Note: the exact line numbers above match the current state of `games/filter.js` as of this plan (after the prior search-feature tasks landed). If the file has drifted since, use the find/replace blocks below — they match on unique surrounding code, not line numbers.

- [ ] **Step 1: Add the toggle selector and `kidsOnly` state**

Find:

```js
  var count = panel.querySelector(".hub__count");
  var searchInput = document.getElementById("game-search");

  // Current selection. primary: all | solo | mp. sub applies only when primary === "mp".
  var primary = "all";
  var sub = "all";
  var category = "all";
  var search = "";
```

Replace with:

```js
  var count = panel.querySelector(".hub__count");
  var searchInput = document.getElementById("game-search");
  var kidsToggle = document.getElementById("kids-toggle");

  // Current selection. primary: all | solo | mp. sub applies only when primary === "mp".
  var primary = "all";
  var sub = "all";
  var category = "all";
  var search = "";
  var kidsOnly = false;
```

- [ ] **Step 2: Add `matchesKids` and extend `matches`**

Find:

```js
  // Does a card's title satisfy the active search text (case-insensitive substring)?
  function matchesSearch(title) {
    return search === "" || title.toLowerCase().indexOf(search) !== -1;
  }

  function matches(modes, cardCategory, title) {
    return matchesMode(modes) && matchesCategory(cardCategory) && matchesSearch(title);
  }
```

Replace with:

```js
  // Does a card's title satisfy the active search text (case-insensitive substring)?
  function matchesSearch(title) {
    return search === "" || title.toLowerCase().indexOf(search) !== -1;
  }

  // Does a card satisfy the active Kids-only filter?
  function matchesKids(cardKids) {
    return !kidsOnly || cardKids === true;
  }

  function matches(modes, cardCategory, title, cardKids) {
    return matchesMode(modes) && matchesCategory(cardCategory) && matchesSearch(title) && matchesKids(cardKids);
  }
```

- [ ] **Step 3: Pass each card's kids-tag into `matches` from `apply()`**

Find:

```js
      var titleEl = card.querySelector(".card__title");
      var title = titleEl ? titleEl.textContent : "";
      var show = matches(modes, cardCategory, title);
```

Replace with:

```js
      var titleEl = card.querySelector(".card__title");
      var title = titleEl ? titleEl.textContent : "";
      var cardKids = card.hasAttribute("data-kids");
      var show = matches(modes, cardCategory, title, cardKids);
```

- [ ] **Step 4: Wire the toggle's `click` event**

Find the end of the search-input wiring block:

```js
  if (searchInput) {
    searchInput.addEventListener("input", function () {
      search = searchInput.value.trim().toLowerCase();
      apply();
    });
  }
```

Immediately after it, add:

```js

  if (kidsToggle) {
    kidsToggle.addEventListener("click", function () {
      kidsOnly = !kidsOnly;
      kidsToggle.classList.toggle("is-active", kidsOnly);
      kidsToggle.setAttribute("aria-pressed", kidsOnly ? "true" : "false");
      apply();
    });
  }
```

- [ ] **Step 5: Verify the filter live in a browser**

Serve the site locally:

```bash
cd games && python3 -m http.server 8123
```

Using a browser-automation tool, open `http://localhost:8123/` and:
1. Click "🧒 Kids only". Confirm the button visually activates (same look as an active mode/category filter button) and `.hub__count` reads "Showing 27 of 32 games".
2. Click it again to deactivate. Confirm the full grid returns ("Showing all 32 games").
3. Re-activate "Kids only", then type "fury" into the search box. Confirm zero cards show (both "Sky Fury" and "Kick Fury" are untagged, so the AND of kids-only + that search term yields nothing) and the count reads "Showing 0 of 32 games".
4. With "Kids only" still active, click the "Arcade" category filter. Confirm only tagged Arcade games show (e.g. Neon Pong, Maze Muncher, Moon Lander) and untagged Arcade games (e.g. Barrel Blast is Shooter not Arcade — pick whatever untagged card shares the active category at test time and confirm it's excluded).
5. Check the browser console for JS errors throughout — expect none.

Stop the server when done.

- [ ] **Step 6: Commit**

```bash
git add games/filter.js
git commit -m "$(cat <<'EOF'
Wire Kids-only filtering into Games Hub

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_012aMPnjtnPEx8ebyPK6tALY
EOF
)"
```
