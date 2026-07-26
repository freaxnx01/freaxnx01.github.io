# Random Game Button Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a "🎲 Random" button to the games hub (`games/index.html`) that opens a randomly chosen game from the currently visible (filtered/searched) set in a new tab, disabling itself when zero cards match.

**Architecture:** Extend the existing `games/filter.js` IIFE — it already computes visibility via `apply()` and toggles `card--hidden` on every `.card`. No new script file, no changes to filtering/search/sort logic itself. One new button in `games/index.html`, one new `.filter-btn:disabled` CSS rule in `games/style.css`, three additions to `games/filter.js` (element lookup, disabled-state toggle inside `apply()`, click listener).

**Tech Stack:** Vanilla JS (ES5-style, matches existing `filter.js`), plain CSS, static HTML. No build step, no test runner — this repo's convention for `games/` is manual browser verification.

## Global Constraints

- Additive only — no changes to existing filtering, search, sorting, or card markup beyond the new button and its disabled-state CSS.
- Random must pick only among cards currently visible under active filters/search/toggles (not the full catalog).
- Picking a game opens it in a new tab via the same `href`/`target="_blank"` pattern as the card's own `.card__play` link, with `rel="noopener"` parity (use `window.open(href, "_blank", "noopener")`).
- Zero visible matches → button is `disabled` (greyed out, non-clickable), not an error state.
- Button lives in `.filter-row--search`, alongside the search input and Kids/Retro toggles.
- No new script file — extend `games/filter.js` in place.

---

### Task 1: Add the Random button markup and disabled-state CSS

**Files:**
- Modify: `games/index.html:24-25` (filter-row--search block)
- Modify: `games/style.css:80-102` (`.filter-btn` rules)

**Interfaces:**
- Produces: a `<button id="random-game-btn" class="filter-btn">` element that Task 2's `filter.js` changes look up by that exact id.

- [ ] **Step 1: Add the button markup**

In `games/index.html`, the `filter-row--search` block currently reads:

```html
      <div class="filter-row filter-row--search">
        <input type="search" id="game-search" placeholder="Search games…" aria-label="Search games" />
        <button type="button" class="filter-btn" id="kids-toggle" aria-pressed="false">🧒 Kids only</button>
        <button type="button" class="filter-btn" id="retro-toggle" aria-pressed="false">🕹️ Retro/Clones only</button>
      </div>
```

(Confirm the exact current content of lines 22-26 before editing — the search input line above is illustrative of the surrounding structure, not necessarily verbatim.)

Add the Random button after the Retro toggle, inside the same `<div>`:

```html
        <button type="button" class="filter-btn" id="random-game-btn">🎲 Random</button>
```

So the block becomes:

```html
      <div class="filter-row filter-row--search">
        <input type="search" id="game-search" placeholder="Search games…" aria-label="Search games" />
        <button type="button" class="filter-btn" id="kids-toggle" aria-pressed="false">🧒 Kids only</button>
        <button type="button" class="filter-btn" id="retro-toggle" aria-pressed="false">🕹️ Retro/Clones only</button>
        <button type="button" class="filter-btn" id="random-game-btn">🎲 Random</button>
      </div>
```

- [ ] **Step 2: Add the disabled-state CSS rule**

In `games/style.css`, immediately after the existing `.filter-btn.is-active` rule (around line 97-102):

```css
.filter-btn.is-active {
  color: var(--bg);
  background: var(--accent);
  border-color: var(--accent);
  font-weight: 600;
}
.filter-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}
```

- [ ] **Step 3: Manually verify in browser**

Open `games/index.html` directly in a browser (e.g. `open games/index.html` on macOS, or serve the repo root with any static file server and navigate to `/games/`). Confirm:
- The "🎲 Random" button renders after "🕹️ Retro/Clones only" in the search row, styled identically to the other filter buttons (pill shape, same font).
- It does nothing yet when clicked (no listener wired up — expected at this point).

- [ ] **Step 4: Commit**

```bash
git add games/index.html games/style.css
git commit -m "feat(hub): add random game button markup and disabled styling"
```

---

### Task 2: Wire up random-pick and disabled-state logic in filter.js

**Files:**
- Modify: `games/filter.js:14-16` (element lookups)
- Modify: `games/filter.js:88-93` (end of `apply()`)
- Modify: `games/filter.js` (new click listener, alongside the `kidsToggle`/`retroToggle` listeners at lines 159-175)

**Interfaces:**
- Consumes: `#random-game-btn` from Task 1 (`games/index.html`); `cards` array (`games/filter.js:8`, each a `.card` element with `card--hidden` toggled by `apply()`); `.card__play` anchor with an `href` attribute (existing card markup, e.g. `games/index.html:74`).
- Produces: none consumed by later tasks — this is the final task.

- [ ] **Step 1: Add the element lookup**

In `games/filter.js`, the existing lookups read:

```javascript
  var searchInput = document.getElementById("game-search");
  var kidsToggle = document.getElementById("kids-toggle");
  var retroToggle = document.getElementById("retro-toggle");
```

Add a fourth lookup immediately after:

```javascript
  var searchInput = document.getElementById("game-search");
  var kidsToggle = document.getElementById("kids-toggle");
  var retroToggle = document.getElementById("retro-toggle");
  var randomBtn = document.getElementById("random-game-btn");
```

- [ ] **Step 2: Disable the button when zero cards are visible**

In `games/filter.js`, `apply()` currently ends with:

```javascript
    if (count) {
      count.textContent =
        visible === cards.length
          ? "Showing all " + cards.length + " games"
          : "Showing " + visible + " of " + cards.length + " games";
    }
  }
```

Add the `randomBtn` guard right after the `count` block, still inside `apply()`:

```javascript
    if (count) {
      count.textContent =
        visible === cards.length
          ? "Showing all " + cards.length + " games"
          : "Showing " + visible + " of " + cards.length + " games";
    }
    if (randomBtn) {
      randomBtn.disabled = visible === 0;
    }
  }
```

- [ ] **Step 3: Add the click listener**

In `games/filter.js`, immediately after the `retroToggle` listener block (lines 168-175):

```javascript
  if (retroToggle) {
    retroToggle.addEventListener("click", function () {
      retroOnly = !retroOnly;
      retroToggle.classList.toggle("is-active", retroOnly);
      retroToggle.setAttribute("aria-pressed", retroOnly ? "true" : "false");
      apply();
    });
  }
```

add:

```javascript
  if (randomBtn) {
    randomBtn.addEventListener("click", function () {
      var visibleCards = cards.filter(function (c) {
        return !c.classList.contains("card--hidden");
      });
      if (visibleCards.length === 0) return;
      var pick = visibleCards[Math.floor(Math.random() * visibleCards.length)];
      var playLink = pick.querySelector(".card__play");
      if (!playLink) return;
      window.open(playLink.getAttribute("href"), "_blank", "noopener");
    });
  }
```

(The `visibleCards.length === 0` and `!playLink` guards are defensive no-ops given `apply()` already disables the button in the zero-match case and every card ships a `.card__play` anchor — they exist so a stray click event fired before `apply()` has run, or a future card missing `.card__play`, fails silently instead of throwing.)

- [ ] **Step 4: Manually verify in browser**

Reload `games/index.html` (or the served `/games/` page) and confirm, in order:

1. **No filters active:** click "🎲 Random" repeatedly — a new tab opens each time to one of the games, and at least two different games are reached across ~5 clicks.
2. **Narrow filter:** click "🧒 Kids only", then click "🎲 Random" several times — every opened tab is one of the kids-flagged games (cross-check against which cards remain visible, i.e. lack `card--hidden`).
3. **Zero matches:** type a search string matching no game title (e.g. `zzzzz`) — confirm "🎲 Random" visually greys out and clicking it does nothing (no new tab, no console error).
4. **Recovery:** clear the search box — confirm "🎲 Random" re-enables and works again.
5. **Keyboard:** Tab to the "🎲 Random" button and press Enter — confirm it activates like a click (native `<button>` behavior; no custom key handling was added, so this should just work).
6. Open the browser devtools console during all of the above — confirm no errors are logged.

- [ ] **Step 5: Commit**

```bash
git add games/filter.js
git commit -m "feat(hub): pick and open a random visible game"
```

---

## Self-Review Notes

- **Spec coverage:** filter-scope restriction (visible cards only) → Task 2 Step 3; new-tab open via `card__play` href → Task 2 Step 3; empty-match disables button → Task 2 Step 2; placement in `filter-row--search` → Task 1 Step 1; architecture (extend `filter.js`, no new file) → Task 2; CSS disabled-state minimal rule → Task 1 Step 2; manual testing checklist → Task 2 Step 4 (mirrors spec's Testing section line for line).
- **Placeholders:** none — every step ships literal, complete code.
- **Type/name consistency:** `randomBtn` used consistently across Task 2 Steps 1-3; `#random-game-btn` id matches Task 1's markup; `.card__play` selector matches existing card markup (verified against `games/index.html:74` et al.).
