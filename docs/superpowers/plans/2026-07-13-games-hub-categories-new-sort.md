# Games hub: category filter, NEW badge, sort + Geography Quiz Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a category filter, a 14-day "NEW" badge, and a date-added sort control to the Browser Games Hub, and publish the new Geography Quiz game so the Quiz category has a real member.

**Architecture:** Static site, no build step. Two new per-card data attributes (`data-category`, `data-added`) drive three independent, composable client-side behaviors in `games/filter.js`: category filtering (AND'd with the existing mode filter), a NEW badge computed at load time from `data-added`, and a DOM-reordering sort control. Geography Quiz ships as its own `game-geography-quiz` GitHub Pages repo, following the existing per-game repo pattern, then gets a card in the hub grid.

**Tech Stack:** Plain HTML/CSS/vanilla JS (no framework, no bundler), GitHub Pages, GitHub CLI (`gh`), Python + Playwright for screenshot capture (`scripts/capture_screenshots.py`).

## Global Constraints

- No build step, bundler, or framework may be introduced anywhere (hub or new game repo) — matches every existing file in this project.
- `data-added` dates are historical facts sourced from `git log --format=%ad -- games/index.html`, not invented — see exact per-game table in Task 1.
- Category is single-select per card (one `data-category` value), unlike `data-modes` which is space-separated multi-value.
- New game repo naming follows the established `game-<name>` convention; hub title is "Geography Quiz" (not "Terra").
- This project has no automated test runner for the static hub pages — verification steps use `grep`/`node -c`-style sanity checks plus explicit manual browser checks, matching the pattern in the existing spec docs under `docs/superpowers/specs/`.

---

### Task 1: Add `data-category` and `data-added` attributes to the 19 existing cards

**Files:**
- Modify: `games/index.html` (all 19 `<article class="card" data-modes="...">` opening tags)

**Interfaces:**
- Produces: every `.card` element now carries `data-category="<slug>"` and `data-added="YYYY-MM-DD"`, which Task 3 (`matches()`) and Task 4 (NEW badge) read.

Exact per-card values (slug and date), derived from `git log --format=%ad -- games/index.html` per the design spec (`docs/superpowers/specs/2026-07-13-games-hub-categories-new-sort-design.md`):

| Card title (in current file order) | `data-category` | `data-added` |
|---|---|---|
| Barrel Blast | `shooter` | `2026-07-07` |
| Battleship Toys | `strategy` | `2026-07-12` |
| Beach Buggy Racer | `racing` | `2026-07-07` |
| BMX Beach Jam | `sports` | `2026-07-07` |
| Dustline | `shooter` | `2026-07-11` |
| Esel vs. Karotte | `racing` | `2026-07-07` |
| Fruit Frenzy | `puzzle` | `2026-07-08` |
| Gorillazz | `action` | `2026-07-07` |
| Kick Fury | `sports` | `2026-07-11` |
| Moon Lander | `arcade` | `2026-07-12` |
| North & South Clone | `strategy` | `2026-07-07` |
| PLOD | `puzzle` | `2026-07-12` |
| Sky Fury | `action` | `2026-07-12` |
| Space Invaders | `shooter` | `2026-07-07` |
| Splashdown | `racing` | `2026-07-07` |
| Stack Duel | `puzzle` | `2026-07-07` |
| Tank Toys | `action` | `2026-07-07` |
| Tschau Sepp | `card` | `2026-07-07` |
| Voxel Sandbox | `sandbox` | `2026-07-07` |

- [ ] **Step 1: Edit each card's opening tag**

For every card, change:
```html
<article class="card" data-modes="solo">
```
to (example for Barrel Blast):
```html
<article class="card" data-modes="solo" data-category="shooter" data-added="2026-07-07">
```
Apply the same pattern to all 19 cards using the table above — keep each card's existing `data-modes` value untouched, only append the two new attributes.

- [ ] **Step 2: Verify every card got both new attributes**

Run:
```bash
grep -c 'data-category=' games/index.html
grep -c 'data-added=' games/index.html
```
Expected: both print `19`.

- [ ] **Step 3: Verify no card was missed or double-edited**

Run:
```bash
grep -oP 'data-modes="[^"]*"' games/index.html | wc -l
```
Expected: `19` (unchanged from before this task — confirms no card markup was duplicated).

- [ ] **Step 4: Commit**

```bash
git add games/index.html
git commit -m "feat(games): tag hub cards with category and added-date"
```

---

### Task 2: Category filter row markup + styling

**Files:**
- Modify: `games/index.html:20-30` (the `.hub__filters` block)
- Modify: `games/style.css:59-109` (mode/filter styles)

**Interfaces:**
- Consumes: nothing new.
- Produces: a `.filter-row--category` DOM row with `[data-category]` buttons that Task 3's JS attaches click handlers to. Category slugs must exactly match Task 1's `data-category` values: `all, shooter, action, strategy, racing, sports, puzzle, card, sandbox, arcade, quiz`.

- [ ] **Step 1: Add the category filter row to `games/index.html`**

Locate the existing filters block:
```html
    <div class="hub__filters" data-filters>
      <div class="filter-row" role="group" aria-label="Filter games by mode">
        <button type="button" class="filter-btn is-active" data-filter="all" aria-pressed="true">All</button>
        <button type="button" class="filter-btn" data-filter="solo" aria-pressed="false">Single player</button>
        <button type="button" class="filter-btn" data-filter="mp" aria-pressed="false" aria-expanded="false" aria-controls="filter-sub">Multiplayer</button>
      </div>
      <div class="filter-row filter-row--sub" id="filter-sub" role="group" aria-label="Filter multiplayer by connection" hidden>
        <button type="button" class="filter-btn is-active" data-sub="all" aria-pressed="true">Local &amp; Peer2Peer</button>
        <button type="button" class="filter-btn" data-sub="local" aria-pressed="false">Local</button>
        <button type="button" class="filter-btn" data-sub="p2p" aria-pressed="false">Peer2Peer</button>
      </div>
      <p class="hub__count" role="status" aria-live="polite"></p>
    </div>
```

Replace it with (adds a category row before `.hub__count`, and a sort control after it):
```html
    <div class="hub__filters" data-filters>
      <div class="filter-row" role="group" aria-label="Filter games by mode">
        <button type="button" class="filter-btn is-active" data-filter="all" aria-pressed="true">All</button>
        <button type="button" class="filter-btn" data-filter="solo" aria-pressed="false">Single player</button>
        <button type="button" class="filter-btn" data-filter="mp" aria-pressed="false" aria-expanded="false" aria-controls="filter-sub">Multiplayer</button>
      </div>
      <div class="filter-row filter-row--sub" id="filter-sub" role="group" aria-label="Filter multiplayer by connection" hidden>
        <button type="button" class="filter-btn is-active" data-sub="all" aria-pressed="true">Local &amp; Peer2Peer</button>
        <button type="button" class="filter-btn" data-sub="local" aria-pressed="false">Local</button>
        <button type="button" class="filter-btn" data-sub="p2p" aria-pressed="false">Peer2Peer</button>
      </div>
      <div class="filter-row filter-row--category" role="group" aria-label="Filter games by category">
        <button type="button" class="filter-btn is-active" data-category="all" aria-pressed="true">All genres</button>
        <button type="button" class="filter-btn" data-category="shooter" aria-pressed="false">Shooter</button>
        <button type="button" class="filter-btn" data-category="action" aria-pressed="false">Action</button>
        <button type="button" class="filter-btn" data-category="strategy" aria-pressed="false">Strategy</button>
        <button type="button" class="filter-btn" data-category="racing" aria-pressed="false">Racing</button>
        <button type="button" class="filter-btn" data-category="sports" aria-pressed="false">Sports</button>
        <button type="button" class="filter-btn" data-category="puzzle" aria-pressed="false">Puzzle</button>
        <button type="button" class="filter-btn" data-category="card" aria-pressed="false">Card</button>
        <button type="button" class="filter-btn" data-category="sandbox" aria-pressed="false">Sandbox</button>
        <button type="button" class="filter-btn" data-category="arcade" aria-pressed="false">Arcade</button>
        <button type="button" class="filter-btn" data-category="quiz" aria-pressed="false">Quiz</button>
      </div>
      <div class="hub__toolbar">
        <p class="hub__count" role="status" aria-live="polite"></p>
        <label class="hub__sort">
          Sort:
          <select id="sort-select">
            <option value="az" selected>A&ndash;Z</option>
            <option value="newest">Newest first</option>
          </select>
        </label>
      </div>
    </div>
```

- [ ] **Step 2: Add `.hub__toolbar` / `.hub__sort` styles to `games/style.css`**

Find:
```css
.hub__count {
  margin: 0;
  color: var(--text-dim);
  font-family: var(--mono);
  font-size: 0.78rem;
}
```

Replace with:
```css
.hub__toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.hub__count {
  margin: 0;
  color: var(--text-dim);
  font-family: var(--mono);
  font-size: 0.78rem;
}

.hub__sort {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  color: var(--text-dim);
  font-family: var(--mono);
  font-size: 0.78rem;
}

.hub__sort select {
  font-family: var(--mono);
  font-size: 0.78rem;
  color: var(--text);
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 0.25rem 0.5rem;
  cursor: pointer;
}
.hub__sort select:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}
```

- [ ] **Step 3: Verify markup is well-formed**

Run:
```bash
grep -c 'data-category="' games/index.html
```
Expected: `30` (11 filter buttons with `data-category` + 19 card attributes from Task 1).

- [ ] **Step 4: Open the page and confirm layout**

```bash
python3 -m http.server 8000 --directory games
```
Open `http://localhost:8000/` in a browser. Confirm: a new row of genre buttons renders below the existing mode filters, and a "Sort: A–Z / Newest first" dropdown appears to the right of the "Showing N of 19 games" count. Clicking genre buttons doesn't yet filter anything (JS wiring is Task 3) — that's expected at this point. Stop the server with Ctrl-C.

- [ ] **Step 5: Commit**

```bash
git add games/index.html games/style.css
git commit -m "feat(games): add category filter row and sort control markup"
```

---

### Task 3: Category filtering logic in `games/filter.js`

**Files:**
- Modify: `games/filter.js` (entire file — extends existing `matches()`/state/wiring)

**Interfaces:**
- Consumes: `[data-category]` buttons and `.card[data-category]` from Task 1 & 2.
- Produces: `category` state variable and re-run `apply()` on category button clicks, composable with existing `primary`/`sub` mode state (AND logic).

- [ ] **Step 1: Add `category` state and extend `matches()`**

Find:
```javascript
  // Current selection. primary: all | solo | mp. sub applies only when primary === "mp".
  var primary = "all";
  var sub = "all";

  // Does a card's mode list satisfy the active filter?
  function matches(modes) {
    if (primary === "all") return true;
    if (primary === "solo") return modes.indexOf("solo") !== -1;
    // primary === "mp"
    if (sub === "local") return modes.indexOf("local") !== -1;
    if (sub === "p2p") return modes.indexOf("p2p") !== -1;
    // sub === "all": any multiplayer mode
    return modes.indexOf("local") !== -1 || modes.indexOf("p2p") !== -1;
  }
```

Replace with:
```javascript
  // Current selection. primary: all | solo | mp. sub applies only when primary === "mp".
  var primary = "all";
  var sub = "all";
  var category = "all";

  // Does a card's mode list satisfy the active mode filter?
  function matchesMode(modes) {
    if (primary === "all") return true;
    if (primary === "solo") return modes.indexOf("solo") !== -1;
    // primary === "mp"
    if (sub === "local") return modes.indexOf("local") !== -1;
    if (sub === "p2p") return modes.indexOf("p2p") !== -1;
    // sub === "all": any multiplayer mode
    return modes.indexOf("local") !== -1 || modes.indexOf("p2p") !== -1;
  }

  // Does a card's category satisfy the active category filter?
  function matchesCategory(cardCategory) {
    return category === "all" || cardCategory === category;
  }

  function matches(modes, cardCategory) {
    return matchesMode(modes) && matchesCategory(cardCategory);
  }
```

- [ ] **Step 2: Pass category into `matches()` inside `apply()`**

Find:
```javascript
  function apply() {
    var visible = 0;
    cards.forEach(function (card) {
      var modes = (card.getAttribute("data-modes") || "").split(/\s+/);
      var show = matches(modes);
```

Replace with:
```javascript
  function apply() {
    var visible = 0;
    cards.forEach(function (card) {
      var modes = (card.getAttribute("data-modes") || "").split(/\s+/);
      var cardCategory = card.getAttribute("data-category") || "";
      var show = matches(modes, cardCategory);
```

- [ ] **Step 3: Wire up category buttons**

Find:
```javascript
  var subRow = panel.querySelector(".filter-row--sub");
  var subBtns = Array.prototype.slice.call(panel.querySelectorAll("[data-sub]"));
  var count = panel.querySelector(".hub__count");
```

Replace with:
```javascript
  var subRow = panel.querySelector(".filter-row--sub");
  var subBtns = Array.prototype.slice.call(panel.querySelectorAll("[data-sub]"));
  var categoryBtns = Array.prototype.slice.call(panel.querySelectorAll("[data-category]"));
  var count = panel.querySelector(".hub__count");
```

Then find the closing `apply();` call at the end of the file:
```javascript
  apply();
})();
```

Replace with:
```javascript
  categoryBtns.forEach(function (btn) {
    btn.addEventListener("click", function () {
      category = btn.getAttribute("data-category");
      setPressed(categoryBtns, btn);
      apply();
    });
  });

  apply();
})();
```

- [ ] **Step 4: Verify the file still parses**

Run:
```bash
node -c games/filter.js
```
Expected: no output (exit code 0).

- [ ] **Step 5: Manual browser check**

```bash
python3 -m http.server 8000 --directory games
```
Open `http://localhost:8000/`. Click "Shooter" — confirm only Barrel Blast, Dustline, Space Invaders remain visible and the count reads "Showing 3 of 19 games". Click "Single player" (mode row) while "Shooter" is still active — confirm the set narrows further using AND logic (all three shooters are solo, so it should still show 3; then click "Multiplayer" instead — confirm it drops to 0 with "Showing 0 of 19 games", since none of the three shooters are multiplayer). Click "All genres" and "All" (mode) to reset. Stop the server.

- [ ] **Step 6: Commit**

```bash
git add games/filter.js
git commit -m "feat(games): filter hub cards by category, AND'd with mode filter"
```

---

### Task 4: "NEW" badge (14-day window, computed from `data-added`)

**Files:**
- Modify: `games/style.css` (add `.badge--new`)
- Modify: `games/filter.js` (add badge-injection logic)

**Interfaces:**
- Consumes: `card.getAttribute("data-added")` (Task 1), `.card__badges` container (existing markup in every card).
- Produces: a `.badge.badge--new` element prepended into `.card__badges` for qualifying cards, run once at load (not re-run by `apply()` — it's static per page load, unlike filtering).

- [ ] **Step 1: Add `.badge--new` style to `games/style.css`**

Find:
```css
.badge--solo  { color: var(--accent);   border-color: color-mix(in srgb, var(--accent) 45%, transparent); }
.badge--p2p   { color: #8fb4ff;         border-color: color-mix(in srgb, #8fb4ff 45%, transparent); }
.badge--local { color: var(--accent-2); border-color: color-mix(in srgb, var(--accent-2) 45%, transparent); }
```

Replace with:
```css
.badge--solo  { color: var(--accent);   border-color: color-mix(in srgb, var(--accent) 45%, transparent); }
.badge--p2p   { color: #8fb4ff;         border-color: color-mix(in srgb, #8fb4ff 45%, transparent); }
.badge--local { color: var(--accent-2); border-color: color-mix(in srgb, var(--accent-2) 45%, transparent); }
.badge--new   { color: var(--bg); background: var(--accent); border-color: var(--accent); font-weight: 700; }
```

- [ ] **Step 2: Add badge-injection logic to `games/filter.js`**

Find the end of the file:
```javascript
  categoryBtns.forEach(function (btn) {
    btn.addEventListener("click", function () {
      category = btn.getAttribute("data-category");
      setPressed(categoryBtns, btn);
      apply();
    });
  });

  apply();
})();
```

Replace with:
```javascript
  categoryBtns.forEach(function (btn) {
    btn.addEventListener("click", function () {
      category = btn.getAttribute("data-category");
      setPressed(categoryBtns, btn);
      apply();
    });
  });

  // Mark cards added within the last 14 days as NEW. Computed once at load;
  // does not change as filters/sort are toggled.
  var NEW_WINDOW_DAYS = 14;
  function markNewBadges() {
    var now = Date.now();
    cards.forEach(function (card) {
      var added = card.getAttribute("data-added");
      if (!added) return;
      var addedTime = new Date(added + "T00:00:00Z").getTime();
      var ageDays = (now - addedTime) / (1000 * 60 * 60 * 24);
      if (ageDays > NEW_WINDOW_DAYS) return;
      var badges = card.querySelector(".card__badges");
      if (!badges || badges.querySelector(".badge--new")) return;
      var badge = document.createElement("span");
      badge.className = "badge badge--new";
      badge.textContent = "NEW";
      badges.insertBefore(badge, badges.firstChild);
    });
  }
  markNewBadges();

  apply();
})();
```

- [ ] **Step 3: Verify the file still parses**

Run:
```bash
node -c games/filter.js
```
Expected: no output (exit code 0).

- [ ] **Step 4: Manual browser check**

```bash
python3 -m http.server 8000 --directory games
```
Open `http://localhost:8000/`. Confirm every card shows a solid "NEW" pill as the first badge (expected today, 2026-07-13 — see spec's dated table; all 19 games were added within the last 14 days). Stop the server.

- [ ] **Step 5: Commit**

```bash
git add games/style.css games/filter.js
git commit -m "feat(games): show a NEW badge on games added within 14 days"
```

---

### Task 5: Sort-by-date-added control

**Files:**
- Modify: `games/filter.js` (add sort logic)

**Interfaces:**
- Consumes: `#sort-select` (Task 2 markup), `.hub__grid` and `cards` array (existing).
- Produces: reorders `.card` DOM children on `change`; re-runs `apply()` afterward so visibility/animation state stays correct. Sort state persists independently of filter state (already true since they touch different variables).

- [ ] **Step 1: Add sort logic to `games/filter.js`**

Find:
```javascript
  // Mark cards added within the last 14 days as NEW. Computed once at load;
  // does not change as filters/sort are toggled.
  var NEW_WINDOW_DAYS = 14;
```

Replace with:
```javascript
  // Sort control: A-Z (document order, cached once) vs newest-added-first.
  var sortSelect = document.getElementById("sort-select");
  var originalOrder = cards.slice();

  function sortCards(mode) {
    var ordered;
    if (mode === "newest") {
      ordered = cards.slice().sort(function (a, b) {
        var da = a.getAttribute("data-added") || "";
        var db = b.getAttribute("data-added") || "";
        if (da === db) return 0;
        return da < db ? 1 : -1; // descending: newest first
      });
    } else {
      ordered = originalOrder;
    }
    ordered.forEach(function (card) {
      grid.appendChild(card);
    });
  }

  if (sortSelect) {
    sortSelect.addEventListener("change", function () {
      sortCards(sortSelect.value);
      apply(); // reapply hidden state + re-trigger enter animation in new order
    });
  }

  // Mark cards added within the last 14 days as NEW. Computed once at load;
  // does not change as filters/sort are toggled.
  var NEW_WINDOW_DAYS = 14;
```

Note: `Array.prototype.sort` is stable in all browsers this project targets (evergreen), so cards sharing the same `data-added` date keep their original relative order — satisfying the spec's tie-breaking requirement without extra code.

- [ ] **Step 2: Verify the file still parses**

Run:
```bash
node -c games/filter.js
```
Expected: no output (exit code 0).

- [ ] **Step 3: Manual browser check**

```bash
python3 -m http.server 8000 --directory games
```
Open `http://localhost:8000/`. Confirm the grid starts in A-Z order (Barrel Blast first). Switch the dropdown to "Newest first" — confirm the 5 games added `2026-07-12` (Battleship Toys, Moon Lander, PLOD, Sky Fury, Voxel Sandbox) appear first, followed by the `2026-07-11` pair (Kick Fury, Dustline), then Fruit Frenzy (`2026-07-08`), then the `2026-07-07` batch. Apply a category filter (e.g. "Racing") while sorted "Newest first" — confirm only matching cards show, still in newest-first order. Switch back to "A–Z" — confirm original order returns. Stop the server.

- [ ] **Step 4: Commit**

```bash
git add games/filter.js
git commit -m "feat(games): sort hub cards by date added"
```

---

### Task 6: Publish the Geography Quiz game repo

**Files:**
- Create (new repo, not in this working tree): `game-geography-quiz/index.html`, `game-geography-quiz/support.js`, `game-geography-quiz/geo-data.js`, `game-geography-quiz/README.md`, `game-geography-quiz/LICENSE`
- Source: `/home/freax/LocalSend/Geography Quiz Browser Game.zip`

**Interfaces:**
- Produces: a live site at `https://github.freaxnx01.ch/game-geography-quiz/`, consumed by Task 8's card `href` and Task 7's screenshot script.

- [ ] **Step 1: Unzip the game into a scratch directory**

```bash
mkdir -p /tmp/geo-quiz-publish
cd /tmp/geo-quiz-publish
unzip -q "/home/freax/LocalSend/Geography Quiz Browser Game.zip"
ls publish_geo_quiz
```
Expected: `.gitignore  CLAUDE.md  LICENSE  README.md  geo-data.js  index.html  support.js`

- [ ] **Step 2: Inject the shared hub footer nav before `</body>` in `index.html`**

```bash
cd /tmp/geo-quiz-publish/publish_geo_quiz
python3 - <<'EOF'
from pathlib import Path

nav = '''<!-- game-nav -->
<nav id="game-nav" aria-label="Game navigation" style="position:fixed;right:10px;bottom:8px;z-index:2147483647;display:flex;gap:12px;align-items:center;font:600 13px/1.4 system-ui,-apple-system,sans-serif;padding:6px 11px;border-radius:8px;background:rgba(15,17,26,.55);backdrop-filter:blur(4px);-webkit-backdrop-filter:blur(4px);opacity:.55;transition:opacity .2s" onmouseover="this.style.opacity=1" onmouseout="this.style.opacity=.55">
  <a href="https://github.freaxnx01.ch/games/" style="color:#8fd8e8;text-decoration:none">More Games&hellip;</a>
  <span style="color:#5a6072" aria-hidden="true">&middot;</span>
  <a href="https://github.com/freaxnx01/game-geography-quiz" target="_blank" rel="noopener" style="color:#8fd8e8;text-decoration:none">Source</a>
</nav>
</body>'''

p = Path("index.html")
text = p.read_text()
assert text.count("</body>") == 1, "expected exactly one </body>"
p.write_text(text.replace("</body>", nav))
EOF
tail -8 index.html
```
Expected: the last lines now show the injected `<nav id="game-nav">...` block immediately before `</html>`.

- [ ] **Step 3: Remove publish-only files, keep runtime + docs**

```bash
rm CLAUDE.md
```
Keep `.gitignore` (harmless — only ignores OS/editor/node_modules cruft), `README.md`, `LICENSE`.

- [ ] **Step 4: Init git, create the GitHub repo, and push**

```bash
git init -q
git add .
git commit -q -m "Terra geography quiz — initial commit"
gh repo create game-geography-quiz --public --source=. --remote=origin --push
```
Expected: `gh` prints the new repo URL, e.g. `https://github.com/freaxnx01/game-geography-quiz`.

- [ ] **Step 5: Enable GitHub Pages**

```bash
gh api -X POST repos/freaxnx01/game-geography-quiz/pages -f "source[branch]=main" -f "source[path]=/"
```
Expected: JSON response describing the new Pages site (or a 409 if Pages auto-enabled already — either is fine).

- [ ] **Step 6: Verify the live site**

Wait about 60 seconds for the first Pages build, then:
```bash
curl -s -o /dev/null -w "%{http_code}\n" https://github.freaxnx01.ch/game-geography-quiz/
```
Expected: `200`. If it 404s immediately, wait another 60s and retry (first-deploy propagation delay) — do not treat one 404 as failure.

No commit step here — this task's output lives in the new `game-geography-quiz` repo, not this working tree.

---

### Task 7: Generate screenshot + icon assets for Geography Quiz

**Files:**
- Modify: `scripts/capture_screenshots.py:22-40` (the `REPOS` list)
- Create: `games/assets/game-geography-quiz.png`, `games/assets/game-geography-quiz-icon.png` (generated, not hand-written)

**Interfaces:**
- Consumes: the live site from Task 6 (`https://github.freaxnx01.ch/game-geography-quiz/`).
- Produces: the two asset files Task 8's card `<img>` tags reference.

- [ ] **Step 1: Add the new repo to the capture list**

Find:
```python
    "game-battleship-toys",
    "game-sky-fury",
]
```

Replace with:
```python
    "game-battleship-toys",
    "game-sky-fury",
    "game-geography-quiz",
]
```

- [ ] **Step 2: Install deps if not already present and run the capture script**

```bash
pip install -r scripts/requirements.txt
playwright install chromium
python3 scripts/capture_screenshots.py
```
This re-captures all 20 games (idempotent — matches the script's documented behavior), including the new one. Expected: no entries for `game-geography-quiz` in the "skipped" summary printed at the end.

- [ ] **Step 3: Verify the new asset files exist**

```bash
ls -la games/assets/game-geography-quiz.png games/assets/game-geography-quiz-icon.png
```
Expected: both files exist and are non-zero size.

- [ ] **Step 4: Commit**

```bash
git add scripts/capture_screenshots.py games/assets/game-geography-quiz.png games/assets/game-geography-quiz-icon.png
git commit -m "feat(games): capture screenshots for Geography Quiz"
```

(If the capture run also regenerated screenshots for pre-existing games with visible diffs, that's expected re-run behavior — include those changed files in this commit too, since the script is documented as re-runnable for the whole set.)

---

### Task 8: Add the Geography Quiz card to the hub grid

**Files:**
- Modify: `games/index.html` (insert new `<article class="card">` between Fruit Frenzy and Gorillazz)

**Interfaces:**
- Consumes: `data-category="quiz"` (must match Task 2's filter button value exactly), assets from Task 7, live URL from Task 6.
- Produces: final visible card; this is the last task, so also does full end-to-end manual QA across every feature added by Tasks 1-8.

- [ ] **Step 1: Insert the new card**

Find (the existing Fruit Frenzy → Gorillazz boundary):
```html
      <article class="card" data-modes="solo local p2p" data-category="puzzle" data-added="2026-07-08">
        <img class="card__thumb" src="assets/game-fruit-frenzy-icon.png" alt="Fruit Frenzy screenshot"
             data-full="assets/game-fruit-frenzy.png" data-title="Fruit Frenzy" tabindex="0" role="button" aria-label="Enlarge Fruit Frenzy screenshot">
        <div class="card__body">
          <h2 class="card__title">Fruit Frenzy</h2>
          <p class="card__desc">Suika-style fruit-merge — solo, 2P local or P2P.</p>
          <div class="card__badges">
            <span class="badge badge--p2p">Multiplayer · Peer2Peer</span>
            <span class="badge badge--local">Multiplayer · Local</span>
            <span class="badge badge--solo">Solo</span>
          </div>
          <a class="card__play" href="https://github.freaxnx01.ch/game-fruit-frenzy/">▶ Play</a>
        </div>
      </article>

      <article class="card" data-modes="local p2p" data-category="action" data-added="2026-07-07">
        <img class="card__thumb" src="assets/game-gorillazz-icon.png" alt="Gorillazz screenshot"
```

Insert a new card between them:
```html
      <article class="card" data-modes="solo local p2p" data-category="puzzle" data-added="2026-07-08">
        <img class="card__thumb" src="assets/game-fruit-frenzy-icon.png" alt="Fruit Frenzy screenshot"
             data-full="assets/game-fruit-frenzy.png" data-title="Fruit Frenzy" tabindex="0" role="button" aria-label="Enlarge Fruit Frenzy screenshot">
        <div class="card__body">
          <h2 class="card__title">Fruit Frenzy</h2>
          <p class="card__desc">Suika-style fruit-merge — solo, 2P local or P2P.</p>
          <div class="card__badges">
            <span class="badge badge--p2p">Multiplayer · Peer2Peer</span>
            <span class="badge badge--local">Multiplayer · Local</span>
            <span class="badge badge--solo">Solo</span>
          </div>
          <a class="card__play" href="https://github.freaxnx01.ch/game-fruit-frenzy/">▶ Play</a>
        </div>
      </article>

      <article class="card" data-modes="solo" data-category="quiz" data-added="2026-07-13">
        <img class="card__thumb" src="assets/game-geography-quiz-icon.png" alt="Geography Quiz screenshot"
             data-full="assets/game-geography-quiz.png" data-title="Geography Quiz" tabindex="0" role="button" aria-label="Enlarge Geography Quiz screenshot">
        <div class="card__body">
          <h2 class="card__title">Geography Quiz</h2>
          <p class="card__desc">Flags, capitals, shapes &amp; more — bilingual EN/DE geography quiz.</p>
          <div class="card__badges">
            <span class="badge badge--solo">Solo</span>
          </div>
          <a class="card__play" href="https://github.freaxnx01.ch/game-geography-quiz/">▶ Play</a>
        </div>
      </article>

      <article class="card" data-modes="local p2p" data-category="action" data-added="2026-07-07">
        <img class="card__thumb" src="assets/game-gorillazz-icon.png" alt="Gorillazz screenshot"
```

- [ ] **Step 2: Update the page's card count references**

Find:
```html
      <p class="hub__desc">A handful of finished browser games — card games, tank battles, physics shooters and retro clones. Click a screenshot to enlarge, or hit Play to jump straight in.</p>
```
(this is `<header class="hub__header"><h1>...<p>` earlier in the file — the intro paragraph doesn't hardcode a count, so no edit needed here.) Confirm no other file hardcodes "19 games" anywhere:
```bash
grep -rn "19 games\|19 finished" games/ README.md 2>/dev/null
```
Expected: no matches (the "Showing N of 19 games" text in `filter.js` is computed from `cards.length`, not hardcoded — verify):
```bash
grep -n "cards.length" games/filter.js
```
Expected: one match, inside the `count.textContent` block — this auto-updates to 20 once the new card exists, no code change needed.

- [ ] **Step 3: Verify markup**

```bash
grep -c '<article class="card"' games/index.html
```
Expected: `20`.

```bash
grep -c 'data-category="' games/index.html
```
Expected: `31` (11 filter buttons from Task 2 + 20 cards, up from Task 2's count of 30 now that this task added one more card).

- [ ] **Step 4: Full manual QA pass**

```bash
python3 -m http.server 8000 --directory games
```
Open `http://localhost:8000/`. Walk through every feature added in this plan:
1. Count reads "Showing all 20 games" on load.
2. Click "Quiz" category filter — only Geography Quiz shows, count reads "Showing 1 of 20 games".
3. Click the Geography Quiz thumbnail — lightbox opens with the captured screenshot.
4. Click "▶ Play" on the Geography Quiz card — new tab opens `https://github.freaxnx01.ch/game-geography-quiz/` and the quiz loads and is playable (not a blank page — confirms it wasn't opened via `file://` and Pages serves the ES module import correctly).
5. Switch sort to "Newest first" — Geography Quiz (2026-07-13) appears first, ahead of the 2026-07-12 batch.
6. Confirm Geography Quiz shows a "NEW" badge (added today).
7. Reset all filters to "All"/"All genres"/"A–Z" — grid returns to the original 20-card alphabetical layout.

Stop the server with Ctrl-C.

- [ ] **Step 5: Commit**

```bash
git add games/index.html
git commit -m "feat(games): add Geography Quiz to the hub"
```
