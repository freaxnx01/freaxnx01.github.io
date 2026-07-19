# Games Hub Search/Filter Textbox Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a live search textbox to the Games Hub (`games/index.html`) that narrows the visible cards by name, ANDed with the existing mode/category filters.

**Architecture:** A new `.filter-row--search` row (native `<input type="search">`) is added at the top of `.hub__filters`. `games/filter.js` gains a `search` state variable, a `matchesSearch(title)` substring check, and an `input`-event listener that updates `search` and re-runs the existing `apply()` pipeline — no new rendering path, reuses the current hide/show + count logic.

**Tech Stack:** Static HTML/CSS/vanilla JS (no build step, no framework, no test runner — this repo's Games Hub page has no automated test suite; verification is manual/live-browser, matching every prior hub-feature spec in `docs/superpowers/specs/`).

## Global Constraints

- Case-insensitive plain substring match against each card's `.card__title` text — no fuzzy matching, no per-word splitting.
- Search ANDs with existing mode/category filters (narrows current selection, doesn't reset it).
- Live filtering on every keystroke (`input` event), no debounce, no submit step.
- No new empty-state UI — the existing `.hub__count` "Showing N of M games" text is sufficient for zero-result feedback.
- No new color hues — reuse existing CSS custom properties (`--bg-card`, `--border`, `--text`, `--text-dim`, `--accent`, `--mono`).
- Native `type="search"` clear-× only — no custom clear button.

---

### Task 1: Search input markup + styling

**Files:**
- Modify: `games/index.html:21-24` (insert new row as the first child of `.hub__filters`, immediately after the `<div class="hub__filters" data-filters>` opening tag, before the existing `.filter-row` mode-filter block)
- Modify: `games/style.css` (append new rule block near the existing `.filter-row`/`.filter-btn` rules, i.e. after the `.filter-btn.is-active` rule block currently ending around line 100)

**Interfaces:**
- Produces: `<input type="search" id="game-search">` — Task 2 queries this by ID and listens for its `input` event.
- Produces: CSS class `.filter-row--search` applied to the wrapping `<div>`, and a `.search-input` class on the `<input>` itself for styling.

- [ ] **Step 1: Insert the search row markup**

In `games/index.html`, the filters panel currently opens like this:

```html
    <div class="hub__filters" data-filters>
      <div class="filter-row" role="group" aria-label="Filter games by mode">
```

Change it to insert a new row immediately after the opening `<div class="hub__filters" data-filters>` tag, before the mode-filter row:

```html
    <div class="hub__filters" data-filters>
      <div class="filter-row filter-row--search">
        <input type="search" id="game-search" class="search-input" placeholder="Search games…" aria-label="Search games by name">
      </div>
      <div class="filter-row" role="group" aria-label="Filter games by mode">
```

- [ ] **Step 2: Add CSS for the search row and input**

In `games/style.css`, find the existing rule block:

```css
.filter-btn.is-active {
  color: var(--bg);
  background: var(--accent);
  border-color: var(--accent);
  font-weight: 600;
}
```

Immediately after it (still before the `.hub__toolbar` rule), add:

```css
.filter-row--search {
  width: 100%;
}

.search-input {
  width: 100%;
  max-width: 22rem;
  font-family: var(--mono);
  font-size: 0.82rem;
  color: var(--text);
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 999px;
  padding: 0.45rem 0.9rem;
}
.search-input::placeholder { color: var(--text-dim); }
.search-input:hover { border-color: var(--accent); }
.search-input:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}
```

- [ ] **Step 3: Verify markup and styling render correctly**

Serve the site locally and open it in a browser:

```bash
cd games && python3 -m http.server 8123
```

Open `http://localhost:8123/` in a browser (or take a screenshot via any available browser-automation tool). Confirm:
- A pill-shaped search input appears at the top of the filter panel, above "All / Single player / Multiplayer".
- It has placeholder text "Search games…".
- Typing into it does nothing yet (expected — Task 2 wires the behavior).
- Tabbing from the page load reaches the search input before the "All" mode button (natural DOM order).

Stop the server (`Ctrl-C`) when done.

- [ ] **Step 4: Commit**

```bash
git add games/index.html games/style.css
git commit -m "$(cat <<'EOF'
Add search input markup to Games Hub filter panel

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_012aMPnjtnPEx8ebyPK6tALY
EOF
)"
```

---

### Task 2: Wire search filtering logic

**Files:**
- Modify: `games/filter.js:4-38` (add selector, state var, `matchesSearch`, extend `matches`)
- Modify: `games/filter.js:40-64` (`apply()` — pass card title into `matches`)
- Modify: `games/filter.js` (near the end of the primary/sub/category button wiring — add the new `input` listener; exact insertion point given in Step 3 below)

**Interfaces:**
- Consumes: `#game-search` input element and `.card__title` text from Task 1's markup (and the existing per-card `<h2 class="card__title">` already present in every card in `games/index.html`).
- Consumes/extends: existing `matches(modes, cardCategory)` function and `apply()` from `games/filter.js:36-64`.
- Produces: `search` module-level state variable and `matchesSearch(title)` function — no other task depends on these beyond this file.

- [ ] **Step 1: Add the search input selector and state variable**

In `games/filter.js`, find:

```js
  var categoryBtns = Array.prototype.slice.call(panel.querySelectorAll("[data-category]"));
  var count = panel.querySelector(".hub__count");

  // Current selection. primary: all | solo | mp. sub applies only when primary === "mp".
  var primary = "all";
  var sub = "all";
  var category = "all";
```

Replace with:

```js
  var categoryBtns = Array.prototype.slice.call(panel.querySelectorAll("[data-category]"));
  var count = panel.querySelector(".hub__count");
  var searchInput = document.getElementById("game-search");

  // Current selection. primary: all | solo | mp. sub applies only when primary === "mp".
  var primary = "all";
  var sub = "all";
  var category = "all";
  var search = "";
```

- [ ] **Step 2: Add `matchesSearch` and extend `matches`**

Find:

```js
  // Does a card's category satisfy the active category filter?
  function matchesCategory(cardCategory) {
    return category === "all" || cardCategory === category;
  }

  function matches(modes, cardCategory) {
    return matchesMode(modes) && matchesCategory(cardCategory);
  }
```

Replace with:

```js
  // Does a card's category satisfy the active category filter?
  function matchesCategory(cardCategory) {
    return category === "all" || cardCategory === category;
  }

  // Does a card's title satisfy the active search text (case-insensitive substring)?
  function matchesSearch(title) {
    return search === "" || title.toLowerCase().indexOf(search) !== -1;
  }

  function matches(modes, cardCategory, title) {
    return matchesMode(modes) && matchesCategory(cardCategory) && matchesSearch(title);
  }
```

- [ ] **Step 3: Pass the card title into `matches` from `apply()`**

Find:

```js
  function apply() {
    var visible = 0;
    cards.forEach(function (card) {
      var modes = (card.getAttribute("data-modes") || "").split(/\s+/);
      var cardCategory = card.getAttribute("data-category") || "";
      var show = matches(modes, cardCategory);
```

Replace with:

```js
  function apply() {
    var visible = 0;
    cards.forEach(function (card) {
      var modes = (card.getAttribute("data-modes") || "").split(/\s+/);
      var cardCategory = card.getAttribute("data-category") || "";
      var titleEl = card.querySelector(".card__title");
      var title = titleEl ? titleEl.textContent : "";
      var show = matches(modes, cardCategory, title);
```

- [ ] **Step 4: Wire the search input's `input` event**

Find the end of the `categoryBtns.forEach(...)` block:

```js
  categoryBtns.forEach(function (btn) {
    btn.addEventListener("click", function () {
      category = btn.getAttribute("data-category");
      setPressed(categoryBtns, btn);
      apply();
    });
  });
```

Immediately after it, add:

```js

  if (searchInput) {
    searchInput.addEventListener("input", function () {
      search = searchInput.value.trim().toLowerCase();
      apply();
    });
  }
```

- [ ] **Step 5: Verify search filtering live in a browser**

Serve the site locally:

```bash
cd games && python3 -m http.server 8123
```

Using any available browser-automation tool (e.g. Playwright), open `http://localhost:8123/` and:
1. Type `cross` into the search box. Confirm only "Criss Cross" (once Task 3 below adds it — if run before that task, confirm the count/grid still narrows correctly to zero matches with no JS errors) or any currently-matching card(s) remain visible, and `.hub__count` reads "Showing N of M games" with N matching the visible count.
2. Clear the box (click the native ×, or select-all + Delete). Confirm all cards reappear and the count returns to "Showing all M games".
3. Click "Single player" mode filter, then type a search term that only matches a multiplayer game's title. Confirm zero cards show (AND logic working) and the count reads "Showing 0 of M games".
4. Check the browser console for JS errors during all of the above — expect none.

Stop the server when done.

- [ ] **Step 6: Commit**

```bash
git add games/filter.js
git commit -m "$(cat <<'EOF'
Wire live search filtering into Games Hub

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_012aMPnjtnPEx8ebyPK6tALY
EOF
)"
```
