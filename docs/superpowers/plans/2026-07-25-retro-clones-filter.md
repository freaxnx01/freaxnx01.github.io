# Games Hub Retro/Clones Filter Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a `🕹️ Retro/Clones only` toggle filter to the Games Hub so the user
can distinguish their own original game ideas from recreations of existing
video games.

**Architecture:** Follow the existing `🧒 Kids only` toggle pattern exactly —
a `data-retro` HTML attribute on the relevant cards, a matching toggle button,
and a `matchesRetro()` predicate wired into the same `matches()` filter chain
already used by mode/category/search/kids/WIP.

**Tech Stack:** Static HTML + vanilla JS (`games/filter.js`), no build step.

## Global Constraints

- Exactly these 10 games get `data-retro="true"`: Neon Pong, Maze Muncher,
  Nibbles, Gorillazz, Moon Lander, North & South Clone, Space Invaders,
  Cluck & Load, Gem Cascade, BMX Beach Jam. No other card gets the attribute.
- The new filter must compose with every existing filter (AND, not OR) — it
  plugs into the same `matches()` function the existing filters use, exactly
  like `matchesKids` does.
- Button label: `🕹️ Retro/Clones only`, id `retro-toggle`, placed next to the
  existing `🧒 Kids only` button (id `kids-toggle`) in `games/index.html`.
- No test runner in this repo — this is a static site, manual browser
  verification is the test gate for every task.

---

### Task 1: Add `data-retro` attribute to the 10 cards + the toggle button

**Files:**
- Modify: `games/index.html`

**Interfaces:**
- Produces: 10 `<article class="card">` elements gain a `data-retro="true"`
  attribute. A new `<button id="retro-toggle">` exists in the DOM. Task 2
  reads both by these exact names.

This task only touches markup — the button won't do anything yet (that's
Task 2). Verification is a DOM/attribute check, not a behavioral one.

- [ ] **Step 1: Add `data-retro="true"` to the 10 target cards**

Each of the 10 lines below is a `<article class="card" ...>` opening tag,
identified by exact line number (some of these lines are byte-identical to
other unrelated cards elsewhere in the file, so edit by line number with
`sed -i`, not by matching the string — matching the string could hit the
wrong card). Run each command from the repo root:

```bash
sed -n '116p' games/index.html
```
Expected: `      <article class="card" data-modes="solo local p2p" data-category="arcade" data-added="2026-07-18" data-kids="true">` (Neon Pong — confirm by checking `sed -n '120p' games/index.html` shows `<h2 class="card__title">Neon Pong</h2>`)

Then for each of the 10 (line, title) pairs below: confirm the title on the
given title-line, then append ` data-retro="true"` immediately before the
closing `>` of the article line using `sed -i '<N>s/>$/ data-retro="true">/'`.

| Article line | Title line | Title (confirm before editing) |
|---|---|---|
| 116 | 120 | Neon Pong |
| 159 | 163 | Gem Cascade |
| 172 | 176 | Maze Muncher |
| 185 | 189 | Nibbles |
| 266 | 270 | BMX Beach Jam |
| 334 | 338 | Cluck & Load |
| 347 | 351 | Gorillazz |
| 376 | 380 | Moon Lander |
| 389 | 393 | North &amp; South Clone |
| 430 | 434 | Space Invaders |

For each row, run:
```bash
sed -n '<title line>p' games/index.html   # confirm it shows the expected title
sed -i '<article line>s/>$/ data-retro="true">/' games/index.html
```

Apply this to all 10 rows in the table (20 commands total: one confirm, one
edit, per row). Work from the **highest line number to the lowest** if you
end up making any other edits to the file in between (you won't in this
task, since `sed -i` on a single line never changes the file's line count,
but confirm line numbers are still correct after each edit by re-running
`grep -n '<article class="card"' games/index.html | grep data-retro` and
checking you have exactly 10 matches after all 10 edits).

- [ ] **Step 2: Verify all 10 and only 10 cards have `data-retro`**

```bash
grep -c 'data-retro="true"' games/index.html
```
Expected: `10`

```bash
grep -B4 'data-retro="true"' games/index.html | grep 'card__title'
```
Expected: exactly these 10 titles, in some order — Neon Pong, Gem Cascade,
Maze Muncher, Nibbles, BMX Beach Jam, Cluck &amp; Load, Gorillazz, Moon
Lander, North &amp; South Clone, Space Invaders.

If the count or the title list doesn't match exactly, you edited the wrong
line(s) — revert with `git checkout games/index.html` and redo Step 1
carefully, re-confirming each title line before each edit.

- [ ] **Step 3: Add the toggle button**

Find the existing Kids-only button:

```bash
grep -n 'id="kids-toggle"' games/index.html
```

It looks like this (single line):

```html
        <button type="button" class="filter-btn" id="kids-toggle" aria-pressed="false">🧒 Kids only</button>
```

Using the Edit tool, replace that exact line with:

```html
        <button type="button" class="filter-btn" id="kids-toggle" aria-pressed="false">🧒 Kids only</button>
        <button type="button" class="filter-btn" id="retro-toggle" aria-pressed="false">🕹️ Retro/Clones only</button>
```

- [ ] **Step 4: Manual verification**

```bash
python3 -m http.server 8000
```
Open `http://localhost:8000/games/` in a browser. Confirm:
- The `🕹️ Retro/Clones only` button appears next to `🧒 Kids only`, styled
  the same way (it's inert — clicking it does nothing yet, that's expected
  until Task 2).
- No console errors.
- All games still display normally (the new attribute doesn't affect
  anything without Task 2's JS).

- [ ] **Step 5: Commit**

```bash
git add games/index.html
git commit -m "feat(hub): mark 10 games as Retro/Clones, add toggle button markup"
```

---

### Task 2: Wire the Retro/Clones filter logic

**Files:**
- Modify: `games/filter.js:15` (element lookups), `:22` (state), after `:48`
  (new predicate function), `:52-56` (`matches()`), `:58-79` (`apply()`),
  after `:158` (new click handler) — exact line numbers below, re-verify
  with `grep -n` before editing since Task 1 didn't touch this file so these
  should be unchanged.

**Interfaces:**
- Consumes: `data-retro="true"` attribute from Task 1 (via
  `card.hasAttribute("data-retro")`), `retro-toggle` button id from Task 1.
- Produces: nothing consumed by a later task — this is the last task.

Current code (for reference — re-run `grep -n` to confirm line numbers
haven't drifted before editing):

```javascript
  var kidsToggle = document.getElementById("kids-toggle");

  // Current selection. primary: all | solo | mp. sub applies only when primary === "mp".
  var primary = "all";
  var sub = "all";
  var category = "all";
  var search = "";
  var kidsOnly = false;
```

```javascript
  // Does a card satisfy the active Kids-only filter?
  function matchesKids(cardKids) {
    return !kidsOnly || cardKids === true;
  }

  // WIP games are hidden under every other primary mode and shown only
  // when "Under construction" itself is the active filter.
  function matches(modes, cardCategory, title, cardKids, cardWip) {
    if (primary === "wip") return cardWip && matchesCategory(cardCategory) && matchesSearch(title) && matchesKids(cardKids);
    if (cardWip) return false;
    return matchesMode(modes) && matchesCategory(cardCategory) && matchesSearch(title) && matchesKids(cardKids);
  }

  function apply() {
    var visible = 0;
    cards.forEach(function (card) {
      var modes = (card.getAttribute("data-modes") || "").split(/\s+/);
      var cardCategory = card.getAttribute("data-category") || "";
      var titleEl = card.querySelector(".card__title");
      var title = titleEl ? titleEl.textContent : "";
      var cardKids = card.hasAttribute("data-kids");
      var cardWip = card.hasAttribute("data-wip");
      var show = matches(modes, cardCategory, title, cardKids, cardWip);
```

```javascript
  if (kidsToggle) {
    kidsToggle.addEventListener("click", function () {
      kidsOnly = !kidsOnly;
      kidsToggle.classList.toggle("is-active", kidsOnly);
      kidsToggle.setAttribute("aria-pressed", kidsOnly ? "true" : "false");
      apply();
    });
  }
```

- [ ] **Step 1: Add the `retroToggle` lookup and `retroOnly` state**

Replace:

```javascript
  var kidsToggle = document.getElementById("kids-toggle");

  // Current selection. primary: all | solo | mp. sub applies only when primary === "mp".
  var primary = "all";
  var sub = "all";
  var category = "all";
  var search = "";
  var kidsOnly = false;
```

with:

```javascript
  var kidsToggle = document.getElementById("kids-toggle");
  var retroToggle = document.getElementById("retro-toggle");

  // Current selection. primary: all | solo | mp. sub applies only when primary === "mp".
  var primary = "all";
  var sub = "all";
  var category = "all";
  var search = "";
  var kidsOnly = false;
  var retroOnly = false;
```

- [ ] **Step 2: Add `matchesRetro()` and wire it into `matches()`/`apply()`**

Replace:

```javascript
  // Does a card satisfy the active Kids-only filter?
  function matchesKids(cardKids) {
    return !kidsOnly || cardKids === true;
  }

  // WIP games are hidden under every other primary mode and shown only
  // when "Under construction" itself is the active filter.
  function matches(modes, cardCategory, title, cardKids, cardWip) {
    if (primary === "wip") return cardWip && matchesCategory(cardCategory) && matchesSearch(title) && matchesKids(cardKids);
    if (cardWip) return false;
    return matchesMode(modes) && matchesCategory(cardCategory) && matchesSearch(title) && matchesKids(cardKids);
  }

  function apply() {
    var visible = 0;
    cards.forEach(function (card) {
      var modes = (card.getAttribute("data-modes") || "").split(/\s+/);
      var cardCategory = card.getAttribute("data-category") || "";
      var titleEl = card.querySelector(".card__title");
      var title = titleEl ? titleEl.textContent : "";
      var cardKids = card.hasAttribute("data-kids");
      var cardWip = card.hasAttribute("data-wip");
      var show = matches(modes, cardCategory, title, cardKids, cardWip);
```

with:

```javascript
  // Does a card satisfy the active Kids-only filter?
  function matchesKids(cardKids) {
    return !kidsOnly || cardKids === true;
  }

  // Does a card satisfy the active Retro/Clones-only filter?
  function matchesRetro(cardRetro) {
    return !retroOnly || cardRetro === true;
  }

  // WIP games are hidden under every other primary mode and shown only
  // when "Under construction" itself is the active filter.
  function matches(modes, cardCategory, title, cardKids, cardWip, cardRetro) {
    if (primary === "wip") return cardWip && matchesCategory(cardCategory) && matchesSearch(title) && matchesKids(cardKids) && matchesRetro(cardRetro);
    if (cardWip) return false;
    return matchesMode(modes) && matchesCategory(cardCategory) && matchesSearch(title) && matchesKids(cardKids) && matchesRetro(cardRetro);
  }

  function apply() {
    var visible = 0;
    cards.forEach(function (card) {
      var modes = (card.getAttribute("data-modes") || "").split(/\s+/);
      var cardCategory = card.getAttribute("data-category") || "";
      var titleEl = card.querySelector(".card__title");
      var title = titleEl ? titleEl.textContent : "";
      var cardKids = card.hasAttribute("data-kids");
      var cardWip = card.hasAttribute("data-wip");
      var cardRetro = card.hasAttribute("data-retro");
      var show = matches(modes, cardCategory, title, cardKids, cardWip, cardRetro);
```

- [ ] **Step 3: Add the click handler**

Replace:

```javascript
  if (kidsToggle) {
    kidsToggle.addEventListener("click", function () {
      kidsOnly = !kidsOnly;
      kidsToggle.classList.toggle("is-active", kidsOnly);
      kidsToggle.setAttribute("aria-pressed", kidsOnly ? "true" : "false");
      apply();
    });
  }
```

with:

```javascript
  if (kidsToggle) {
    kidsToggle.addEventListener("click", function () {
      kidsOnly = !kidsOnly;
      kidsToggle.classList.toggle("is-active", kidsOnly);
      kidsToggle.setAttribute("aria-pressed", kidsOnly ? "true" : "false");
      apply();
    });
  }

  if (retroToggle) {
    retroToggle.addEventListener("click", function () {
      retroOnly = !retroOnly;
      retroToggle.classList.toggle("is-active", retroOnly);
      retroToggle.setAttribute("aria-pressed", retroOnly ? "true" : "false");
      apply();
    });
  }
```

- [ ] **Step 4: Manual verification**

```bash
python3 -m http.server 8000
```
Open `http://localhost:8000/games/` in a browser, open the console. Confirm:
- No console errors on load.
- Click `🕹️ Retro/Clones only` → exactly these 10 cards remain visible: Neon
  Pong, Gem Cascade, Maze Muncher, Nibbles, BMX Beach Jam, Cluck & Load,
  Gorillazz, Moon Lander, North & South Clone, Space Invaders. The count
  text reads "Showing 10 of 32 games" (or the current total card count).
- The button gets the active/pressed visual style and `aria-pressed="true"`.
- With Retro/Clones active, also click a genre filter (e.g. "Arcade") →
  only retro games in that genre remain (both filters apply together, AND
  not OR).
- With Retro/Clones active, also click `🧒 Kids only` → both filters apply
  together correctly.
- Click `🕹️ Retro/Clones only` again to toggle it off → all games return
  (subject to whatever other filters are still active).
- Type into the search box while Retro/Clones is active → search narrows
  within the retro-only set.

- [ ] **Step 5: Commit**

```bash
git add games/filter.js
git commit -m "feat(hub): wire up Retro/Clones only filter logic"
```
