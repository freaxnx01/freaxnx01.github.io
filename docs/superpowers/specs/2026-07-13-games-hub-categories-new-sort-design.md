# Games hub: category filter, NEW badge, sort-by-date + publish Geography Quiz — design

**Date:** 2026-07-13

## Goal

Extend the Browser Games Hub (`games/index.html`) with:
1. A genre/category filter, independent of the existing mode filter (Solo / Multiplayer).
2. A "NEW" badge on games added within the last 14 days.
3. A sort control to reorder the grid by date added (newest first) vs. the current A–Z order.

Alongside this, publish the new **Geography Quiz** game (from
`Geography Quiz Browser Game.zip`, internally branded "Terra — Geography Quiz") as
`game-geography-quiz`, giving the new Quiz category a real member instead of shipping
empty.

## Data model additions (per `.card` in `games/index.html`)

Two new attributes on every existing `<article class="card">`, alongside the current
`data-modes`:

- `data-category="<slug>"` — one category per card (single-select taxonomy, not
  multi like modes). Slugs: `shooter`, `action`, `strategy`, `racing`, `sports`,
  `puzzle`, `card`, `sandbox`, `arcade`, `quiz`.
- `data-added="YYYY-MM-DD"` — sourced from git history (each game's own
  `feat(games): add X to the hub` commit date, see table below). Not editable at
  runtime; static per card.

### Category assignments (existing 19 games + new Geography Quiz)

| Category | Games |
|---|---|
| Shooter | Barrel Blast, Dustline, Space Invaders |
| Action | Sky Fury, Tank Toys, Gorillazz |
| Strategy | Battleship Toys, North & South Clone |
| Racing | Beach Buggy Racer, Esel vs. Karotte, Splashdown |
| Sports | BMX Beach Jam, Kick Fury |
| Puzzle | Fruit Frenzy, PLOD, Stack Duel |
| Card | Tschau Sepp |
| Sandbox | Voxel Sandbox |
| Arcade | Moon Lander |
| Quiz | Geography Quiz (new) |

### `data-added` per game (from `git log --format=%ad -- games/index.html`)

| Date | Games |
|---|---|
| 2026-07-07 | Tschau Sepp, Tank Toys, Barrel Blast, Gorillazz, Esel vs. Karotte, North & South Clone, Beach Buggy Racer, BMX Beach Jam, Space Invaders, Splashdown, Stack Duel |
| 2026-07-08 | Fruit Frenzy |
| 2026-07-11 | Kick Fury, Dustline |
| 2026-07-12 | Moon Lander, PLOD, Voxel Sandbox, Battleship Toys, Sky Fury |
| 2026-07-13 | Geography Quiz (today) |

Known consequence: today is 2026-07-13, so with a 14-day window **every game
currently shows NEW**. Expected/correct given the hub's age — badges will taper off
starting with the 2026-07-07 batch after 2026-07-21. Not something to "fix".

## UI changes (`games/index.html` + `games/style.css`)

- New filter row under the existing sub-row, inside `.hub__filters`:
  `<div class="filter-row filter-row--category" role="group" aria-label="Filter games by category">`
  containing one `.filter-btn[data-category]` per slug above, plus a leading `All`
  button (`data-category="all"`, `is-active` by default). Same `.filter-btn` styling
  as the existing rows — no new CSS needed for the buttons themselves, just layout.
- New sort control next to `.hub__count`: a `<select id="sort-select">` with two
  `<option>`s, `az` (default, selected) and `newest`. Small `.hub__sort` wrapper,
  styled to match the `--mono` / `--text-dim` look of `.hub__count`.
- New `.badge--new` pill on cards where `data-added` is within 14 days of "today"
  (computed client-side via `Date.now()`), placed in `.card__badges` before the mode
  badges. Style: reuse the `.badge` base class, distinct accent color (e.g.
  `var(--accent)` background, `var(--bg)` text — matches the `.filter-btn.is-active`
  treatment) so it pops without introducing a new hue.

## Filter logic (`games/filter.js`)

- Add `category` state (default `"all"`), alongside existing `primary`/`sub`.
- `matches(modes, category)` extends the current mode check with:
  `category === "all" || cardCategory === category`.
- Category buttons behave like the existing primary buttons: click sets `category`
  and re-runs `apply()`. No sub-row nesting needed (flat list, unlike mode's
  local/p2p sub-filter).
- `.hub__count` text unchanged in shape ("Showing N of 19 games") — filtering by
  category further narrows `visible`, same counter.

## Sort logic (new, in `filter.js` or a small addition)

- On `change` of `#sort-select`:
  - `"az"`: re-append cards to `.hub__grid` in original document order (cache the
    original NodeList order once on load).
  - `"newest"`: re-append cards sorted by `data-added` descending; ties (same day)
    keep relative original order (stable sort).
- Sorting reorders the actual DOM children (not just a visual transform) so tab
  order / accessibility stays correct. Re-run `apply()` after reordering so
  hidden/filtered state and the enter animation stay consistent.
- Sort state persists across filter changes (independent concerns); filter state
  persists across sort changes.

## Geography Quiz publish (follows the established pattern from
`docs/superpowers/specs/2026-07-07-publish-game-batch-design.md`)

- Repo: `game-geography-quiz`, public, root `index.html`, GitHub Pages from `main`.
- Push `index.html`, `support.js`, `geo-data.js`, `README.md`, `LICENSE`. Skip the
  zip's own `CLAUDE.md` (internal publish instructions, not needed once published)
  and `.gitignore` if it only covers local/dev cruft — keep it if it's harmless.
- Inject the same fixed bottom-right `#game-nav` footer (More Games… / Source) used
  on every other hub game, pointing `Source` at `game-geography-quiz`.
- Do not add a build step / bundler / package.json — the zip's own CLAUDE.md is
  explicit that this is intentional (dynamic `import()` of `geo-data.js`, must be
  served over HTTP not `file://`).
- New hub card: title "Geography Quiz", `data-modes="solo"` (no multiplayer in the
  README), `data-category="quiz"`, `data-added="2026-07-13"`, description mentions
  flags/capitals/geography (e.g. "Flags, capitals, shapes & more — bilingual EN/DE
  geography quiz."). Badge: Solo only.
- Screenshot/icon assets generated via `scripts/capture_screenshots.py` like every
  other card (`assets/game-geography-quiz-icon.png`,
  `assets/game-geography-quiz.png`), inserted alphabetically among the existing 19
  cards (a card **before** Gorillazz, after Fruit Frenzy — "Geography Quiz" sorts
  G-e before G-o).

## Testing

- Manual: open `games/index.html` locally, exercise mode filter × category filter
  combinations, confirm AND logic; toggle sort, confirm order changes and persists
  through filtering; confirm NEW badges appear on all current cards (documented
  above) and the Geography Quiz card renders with a working Play link once the repo
  is live.
- No automated test suite exists for this static page; this matches the existing
  testing approach for prior hub changes (spec docs above are also manual-test-only).
