# Retro Clone Original-Title + Wikipedia Link Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Show each retro-clone card's original inspiration (title + Wikipedia link, where one exists) on the Games Hub.

**Architecture:** Add `data-original-title` / `data-original-url` attributes to each `data-retro="true"` card in `games/index.html`. A small script in `games/lightbox.js` reads those attributes on page load and injects an "Inspired by …" line into `.card__body`. A new `.card__inspired` rule in `games/style.css` styles that line.

**Tech Stack:** Static HTML/CSS/vanilla JS (no build step, no test runner — this repo has none). Verification is done by grepping the rendered output and by loading the page in a browser.

## Global Constraints

- No build tooling exists in this repo (`games/` is plain HTML/CSS/JS served as static files) — do not introduce one.
- Every one of the 14 cards below gets **both** `data-original-title` and `data-original-url` — the exact values are locked in the spec (`docs/superpowers/specs/2026-08-03-retro-original-title-design.md`); do not substitute different titles or URLs.
- The plain-text-only rendering path (no link, when `data-original-url` is absent) must exist in the code even though no current card exercises it — future retro cards may not have a Wikipedia article.
- Non-retro cards (no `data-original-title` attribute) must render with zero DOM/visual change.

---

### Task 1: Add `data-original-title` / `data-original-url` attributes to all 14 retro cards

**Files:**
- Modify: `games/index.html` (14 separate `<article>` opening tags)

**Interfaces:**
- Produces: every `<article class="card" ... data-retro="true">` element also carries `data-original-title="..."` and `data-original-url="..."`, which Task 2's script reads via `el.getAttribute(...)`.

This is a single mechanical data-entry task — apply all 14 edits, then verify all 14 at once.

- [ ] **Step 1: Edit each of the 14 retro-card opening tags**

For each pair below, find the `old` line in `games/index.html` and replace it with `new` (only the attribute list changes — nothing else on the line moves).

1. Iron Valhalla — Battlechess (line 66)

old:
```html
      <article class="card" data-modes="solo" data-category="strategy" data-added="2026-08-01" data-retro="true">
```
new:
```html
      <article class="card" data-modes="solo" data-category="strategy" data-added="2026-08-01" data-retro="true" data-original-title="Battle Chess" data-original-url="https://en.wikipedia.org/wiki/Battle_Chess">
```

2. Brickfall (line 92)

old:
```html
      <article class="card" data-modes="solo" data-category="arcade" data-added="2026-07-27" data-kids="true" data-retro="true">
```
This exact line also matches Rockfall and Maze Muncher — use surrounding context (the `card__title` a few lines below, or line number) to pick the right one. For Brickfall (the occurrence immediately before `<h2 class="card__title">Brickfall</h2>` at line 96):
new:
```html
      <article class="card" data-modes="solo" data-category="arcade" data-added="2026-07-27" data-kids="true" data-retro="true" data-original-title="Arkanoid" data-original-url="https://en.wikipedia.org/wiki/Arkanoid">
```

3. Rockfall (line 105, immediately before `<h2 class="card__title">Rockfall</h2>` at line 109)

old:
```html
      <article class="card" data-modes="solo" data-category="arcade" data-added="2026-07-27" data-kids="true" data-retro="true">
```
new:
```html
      <article class="card" data-modes="solo" data-category="arcade" data-added="2026-07-27" data-kids="true" data-retro="true" data-original-title="Boulder Dash" data-original-url="https://en.wikipedia.org/wiki/Boulder_Dash">
```

4. Oil Fever '89 (line 118, immediately before `<h2 class="card__title">Oil Fever '89</h2>` at line 122)

old:
```html
      <article class="card" data-modes="solo" data-category="arcade" data-added="2026-07-27" data-kids="true" data-retro="true">
```
new:
```html
      <article class="card" data-modes="solo" data-category="arcade" data-added="2026-07-27" data-kids="true" data-retro="true" data-original-title="Oil Imperium" data-original-url="https://en.wikipedia.org/wiki/Oil_Imperium">
```

5. Neon Pong (line 183)

old:
```html
      <article class="card" data-modes="solo local p2p" data-category="arcade" data-added="2026-07-18" data-kids="true" data-retro="true">
```
new:
```html
      <article class="card" data-modes="solo local p2p" data-category="arcade" data-added="2026-07-18" data-kids="true" data-retro="true" data-original-title="Pong" data-original-url="https://en.wikipedia.org/wiki/Pong">
```

6. Gem Cascade (line 226)

old:
```html
      <article class="card" data-modes="solo" data-category="puzzle" data-added="2026-07-18" data-kids="true" data-retro="true">
```
new:
```html
      <article class="card" data-modes="solo" data-category="puzzle" data-added="2026-07-18" data-kids="true" data-retro="true" data-original-title="Bejeweled" data-original-url="https://en.wikipedia.org/wiki/Bejeweled">
```

7. Maze Muncher (line 239, immediately before `<h2 class="card__title">Maze Muncher</h2>` at line 243)

old:
```html
      <article class="card" data-modes="solo" data-category="arcade" data-added="2026-07-18" data-kids="true" data-retro="true">
```
new:
```html
      <article class="card" data-modes="solo" data-category="arcade" data-added="2026-07-18" data-kids="true" data-retro="true" data-original-title="Pac-Man" data-original-url="https://en.wikipedia.org/wiki/Pac-Man">
```

8. Nibbles (line 252, immediately before `<h2 class="card__title">Nibbles</h2>` at line 256)

old:
```html
      <article class="card" data-modes="solo local" data-category="arcade" data-added="2026-07-18" data-kids="true" data-retro="true">
```
new:
```html
      <article class="card" data-modes="solo local" data-category="arcade" data-added="2026-07-18" data-kids="true" data-retro="true" data-original-title="Nibbles (QBasic)" data-original-url="https://en.wikipedia.org/wiki/Nibbles_(video_game)">
```

9. BMX Beach Jam (line 333)

old:
```html
      <article class="card" data-modes="solo" data-category="sports" data-added="2026-07-07" data-kids="true" data-retro="true">
```
new:
```html
      <article class="card" data-modes="solo" data-category="sports" data-added="2026-07-07" data-kids="true" data-retro="true" data-original-title="California Games" data-original-url="https://en.wikipedia.org/wiki/California_Games">
```

10. Cluck & Load (line 401)

old:
```html
      <article class="card" data-modes="solo" data-category="shooter" data-added="2026-07-13" data-kids="true" data-retro="true">
```
new:
```html
      <article class="card" data-modes="solo" data-category="shooter" data-added="2026-07-13" data-kids="true" data-retro="true" data-original-title="Moorhuhn" data-original-url="https://en.wikipedia.org/wiki/Moorhuhn">
```

11. Gorillazz (line 414)

old:
```html
      <article class="card" data-modes="local p2p" data-category="action" data-added="2026-07-07" data-kids="true" data-retro="true">
```
new:
```html
      <article class="card" data-modes="local p2p" data-category="action" data-added="2026-07-07" data-kids="true" data-retro="true" data-original-title="Gorillas (QBasic)" data-original-url="https://en.wikipedia.org/wiki/Gorillas_(video_game)">
```

12. Moon Lander (line 443)

old:
```html
      <article class="card" data-modes="solo" data-category="arcade" data-added="2026-07-12" data-kids="true" data-retro="true">
```
new:
```html
      <article class="card" data-modes="solo" data-category="arcade" data-added="2026-07-12" data-kids="true" data-retro="true" data-original-title="Lunar Lander (1979)" data-original-url="https://en.wikipedia.org/wiki/Lunar_Lander_(1979_video_game)">
```

13. North & South Clone (line 456)

old:
```html
      <article class="card" data-modes="solo local p2p" data-category="strategy" data-added="2026-07-07" data-retro="true">
```
new:
```html
      <article class="card" data-modes="solo local p2p" data-category="strategy" data-added="2026-07-07" data-retro="true" data-original-title="The North &amp; South" data-original-url="https://en.wikipedia.org/wiki/The_North_%26_South_(video_game)">
```

14. Space Invaders (line 497)

old:
```html
      <article class="card" data-modes="solo" data-category="shooter" data-added="2026-07-07" data-kids="true" data-retro="true">
```
new:
```html
      <article class="card" data-modes="solo" data-category="shooter" data-added="2026-07-07" data-kids="true" data-retro="true" data-original-title="Space Invaders" data-original-url="https://en.wikipedia.org/wiki/Space_Invaders">
```

- [ ] **Step 2: Verify all 14 edits landed**

Run:
```bash
grep -c 'data-original-title=' games/index.html
```
Expected: `14`

Run:
```bash
grep -c 'data-retro="true"' games/index.html
```
Expected: `14` (unchanged count — confirms no card was duplicated or missed)

- [ ] **Step 3: Commit**

```bash
git add games/index.html
git commit -m "feat(hub): add original-title/Wikipedia data to retro cards"
```

---

### Task 2: Render the "Inspired by …" line from the data attributes

**Files:**
- Modify: `games/lightbox.js`

**Interfaces:**
- Consumes: `data-original-title` / `data-original-url` attributes on `.card` elements, produced by Task 1.
- Produces: a `<p class="card__inspired">` element appended as the last child of each card's `.card__body`, for Task 3's CSS to target.

- [ ] **Step 1: Add the rendering pass to `lightbox.js`**

Insert this block right after the closing `}` of the IIFE's opening `var closeBtn = ...` line (i.e. as a new top-level statement inside the IIFE, before the `// Any element carrying data-full opens the lightbox.` comment at line 23):

```javascript
  // Retro-clone cards: show what the game is inspired by, if known.
  document.querySelectorAll(".card[data-original-title]").forEach(function (card) {
    var title = card.getAttribute("data-original-title");
    var url = card.getAttribute("data-original-url");
    var body = card.querySelector(".card__body");
    if (!title || !body) return;

    var p = document.createElement("p");
    p.className = "card__inspired";

    if (url) {
      p.appendChild(document.createTextNode("Inspired by "));
      var a = document.createElement("a");
      a.href = url;
      a.target = "_blank";
      a.rel = "noopener";
      a.textContent = title;
      p.appendChild(a);
    } else {
      p.textContent = "Inspired by " + title;
    }

    var badges = body.querySelector(".card__badges");
    if (badges) {
      body.insertBefore(p, badges);
    } else {
      body.appendChild(p);
    }
  });

```

- [ ] **Step 2: Verify the script is syntactically valid**

Run:
```bash
node --check games/lightbox.js
```
Expected: no output, exit code 0.

- [ ] **Step 3: Verify rendering manually in a browser**

```bash
cd games && python3 -m http.server 8123 &
```
Open `http://localhost:8123/index.html`, and confirm:
- Retro cards (e.g. "Brickfall") show a line reading "Inspired by Arkanoid" between the description and the mode badges, with "Arkanoid" as a clickable link to Wikipedia.
- Non-retro cards (e.g. "Aerodrome Apex") show no such line.

Stop the server:
```bash
kill %1
```

- [ ] **Step 4: Commit**

```bash
git add games/lightbox.js
git commit -m "feat(hub): render original-title/Wikipedia line on retro cards"
```

---

### Task 3: Style the `.card__inspired` line

**Files:**
- Modify: `games/style.css`

**Interfaces:**
- Consumes: the `.card__inspired` element produced by Task 2, living inside `.card__body` between `.card__desc` (`games/style.css:226`) and `.card__badges` (`games/style.css:233`).

- [ ] **Step 1: Add the CSS rule**

Insert this rule in `games/style.css` immediately after the existing `.card__desc` rule (after the closing `}` at line 231, before `.card__badges` at line 233):

```css
.card__inspired {
  color: var(--text-dim);
  font-size: 0.78rem;
  font-style: italic;
  margin: 0;
}

.card__inspired a {
  color: var(--accent);
  text-decoration: none;
}

.card__inspired a:hover {
  text-decoration: underline;
}
```

- [ ] **Step 2: Verify visually**

```bash
cd games && python3 -m http.server 8123 &
```
Open `http://localhost:8123/index.html` and confirm the "Inspired by …" line reads as small, muted, italic text with the linked title in the accent color, sitting cleanly between the description and badges with no layout overlap or clipping. Check both a short-description card (e.g. Space Invaders) and a long-description card (e.g. Iron Valhalla — Battlechess).

Stop the server:
```bash
kill %1
```

- [ ] **Step 3: Commit**

```bash
git add games/style.css
git commit -m "feat(hub): style the retro-card inspired-by line"
```

---

### Task 4: Full smoke check

**Files:** none (verification only)

**Interfaces:**
- Consumes: the combined output of Tasks 1-3.

- [ ] **Step 1: Confirm the retro filter still works alongside the new line**

```bash
cd games && python3 -m http.server 8123 &
```
Open `http://localhost:8123/index.html`, click "🕹️ Retro/Clones only", and confirm:
- Only the 14 retro cards remain visible, each still showing its "Inspired by …" line.
- Toggling the filter off restores all cards, non-retro cards still showing no "Inspired by …" line.

Stop the server:
```bash
kill %1
```

- [ ] **Step 2: Confirm all 14 mappings render the expected title**

```bash
grep -A1 'data-original-title="Battle Chess"' games/index.html
grep -c 'data-original-title=' games/index.html
```
Expected: the first command shows the Iron Valhalla card's opening tag; the second prints `14`.

No commit needed for this task — it's verification of work already committed in Tasks 1-3.
