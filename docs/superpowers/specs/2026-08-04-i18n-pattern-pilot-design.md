# DE/EN i18n pattern + Iron Valhalla pilot — design

## Problem

Issue #14 asks for DE/EN support "on every game" — but each game lives in its
own `game-<name>` repo (38 of them today), so that's not a single spec/plan's
worth of work. `ai-instructions/.ai/stacks/browser-game.md` already has a loose
`## Localization (i18n)` section (a `strings` object per locale, detect from
`navigator.language`, persist the choice in `localStorage`) but it has never
been implemented in any actual game, and it's missing the specifics an
implementer needs: the exact runtime file, the toggle's placement, the
localStorage key.

**This spec covers two things only:**

1. Fill in the missing specifics in `ai-instructions/.ai/stacks/browser-game.md`
   so the pattern is concrete and ready for any game to adopt.
2. Implement that pattern end-to-end on **one pilot game, `game-iron-valhalla`**,
   to prove it out.

Rolling the pattern out to the other 37 `game-*` repos is explicitly **out of
scope** — each becomes its own future issue once the pilot is validated, the
same way the versioning/changelog stack was piloted then rolled out repo by
repo (see `project-browser-game-stack` memory).

## Design

### Shared runtime: `i18n.js`

Each adopting game gets an `i18n.js` file at repo root, loaded via
`<script src="./i18n.js">` before the game's own script — same loading
convention as `version.js`.

On load, `i18n.js`:

1. Reads `localStorage.getItem("gg-lang")`.
2. If unset, detects from `navigator.language`: starts with `"de"` → `"de"`,
   anything else → `"en"`.
3. Clamps the result to the game's supported languages (currently always
   `["en", "de"]`); anything unsupported falls back to `"en"`.
4. Exposes the result as `window.GG_LANG`.

It also exposes:

- `window.ggSetLang(lang)` — writes `lang` to `localStorage["gg-lang"]`, sets
  `window.GG_LANG = lang`, and dispatches
  `window.dispatchEvent(new CustomEvent("gg-langchange", { detail: { lang } }))`.
- On `DOMContentLoaded`, injects a toggle pill into `#game-nav` (styled like
  the existing version badge — small, muted, matching font/spacing) showing
  the current language (`EN` or `DE`). Clicking it calls
  `ggSetLang(window.GG_LANG === "en" ? "de" : "en")`.

**Why a shared localStorage key, not per-game:** every `game-<name>` repo is
served under the same `github.freaxnx01.ch` origin (different paths only), so
`localStorage` is already shared across all of them. Using one key
(`gg-lang`) means picking a language once carries across every game (and the
hub, if it adopts this later) instead of surprising users with a per-game
reset.

### Per-game strings

Each game defines its own `STRINGS` object in its own script (not in
`i18n.js`, which stays game-agnostic):

```javascript
const STRINGS = {
  en: { newGame: "NEW GAME", /* ... */ },
  de: { newGame: "NEUES SPIEL", /* ... */ },
};

function t(key) {
  return (STRINGS[window.GG_LANG] && STRINGS[window.GG_LANG][key])
    || STRINGS.en[key]
    || key;
}
```

Game code calls `t("newGame")` wherever it currently has a literal English
string in a render path.

### Re-rendering on language change

`i18n.js` only flips `window.GG_LANG` and fires `gg-langchange` — it has no
knowledge of how a given game renders. Each game's own code listens for that
event and triggers whatever its normal re-render mechanism is (e.g. a
state-touching update). For Iron Valhalla specifically, see the pilot section
below — its render path already re-evaluates `t()` calls on every state-driven
render, so the listener only needs to force one re-render pass.

### `ai-instructions/.ai/stacks/browser-game.md` changes

Replace the current `## Localization (i18n)` section with the concrete
version above: `i18n.js` file, `window.GG_LANG` / `ggSetLang` /
`gg-langchange` API, `gg-lang` localStorage key, `#game-nav` toggle placement,
and the `STRINGS` + `t()` per-game convention. Keep the existing carve-out
("pure-arcade games with negligible on-screen text ... may defer i18n").

## Pilot: game-iron-valhalla

Iron Valhalla is dc-bundled (`source/Iron Valhalla Battlechess v2.dc.html` →
generated `index.html`/`support.js`, never hand-edited — the source is edited
and re-bundled). **The implementer must locate the repo's re-bundle
command/tool before starting** (check `AGENT-NOTES.md` at the repo root, or
ask the user) — it is not yet known at spec-writing time.

### Strings to translate

All literal UI-chrome text in the template and in `render()`'s computed label
logic (`source/Iron Valhalla Battlechess v2.dc.html`, class `Component`,
around the `render()` method building `turnText`/`turnSub`/`themeLabel`/
`instantLabel`/`soundLabel`/`vizBtnLabel`/`promoSub`/`resultTitle`/
`resultSub`, plus the static template labels in the `Sidebar`, `Promotion`,
and `Game Over` sections):

- Sidebar: `BATTLE STATUS`, `HINT`, `UNDO MOVE`, `NEW GAME`, `SEARCH MONITOR`,
  `SALVAGE YARD`, `ENEMY LOSSES`, `YOUR LOSSES`, `WAR LOG`,
  `TEAL = EVALUATING · GOLD = BEST LINE`
- Toggle labels: `THEME: MECH` / `THEME: VIKING` / `THEME: CLASSIC WOOD`,
  `BATTLES: INSTANT` / `BATTLES: CINEMA`, `SOUND: ON` / `SOUND: OFF`,
  `AI VIEW: ON` / `AI VIEW: OFF`
- Turn status: `YOUR MOVE`, `COMBAT ENGAGED`, `<faction> COMPUTING`,
  `FIELD PROMOTION`, `CAMPAIGN COMPLETE`, `CLICK ANYWHERE TO SKIP`,
  `CALCULATING ASSAULT VECTOR…`, `SELECT AN UPGRADE`,
  `WARNING — KING UNDER THREAT`, `<faction> — SELECT A UNIT`,
  `AWAITING ENEMY TURN…`
- Promotion dialog: `FIELD PROMOTION` (title), `Your <piece> reached enemy
  lines. Choose its promotion.`
- Game over: `STALEMATE` / `VICTORY` / `DEFEAT`, their three flavor-text subs
  (drawn/victory/defeat descriptions), `NEW BATTLE`

**Carve-out (this pilot only):** themed piece/faction flavor names (the
`NAMES/CLANS` per-theme nicknames shown as a secondary hover label) stay
untranslated — they read as proper nouns, and translating them would roughly
double the string count for cosmetic flavor text rather than functional UI.
`NEGAMAX α·β` (the search-monitor sub-label) also stays as-is — it's a
technical/algorithm label, not UI copy.

### Re-render trigger

Iron Valhalla's `render()` (DCLogic component) recomputes `turnText`, labels,
etc. from `t()` on every render pass driven by `setState`. The pilot adds a
listener:

```javascript
window.addEventListener("gg-langchange", () => this.setState({}));
```

in the component's mount/init path, which is enough to force one re-render
without touching game state.

## Testing

No test runner in either repo (buildless static sites). Manual verification:

- `ai-instructions`: confirm the rewritten `## Localization (i18n)` section
  reads clearly and matches this spec (no automated check — docs only).
- `game-iron-valhalla`: after re-bundling, open the pilot locally and confirm:
  - The `#game-nav` toggle shows `EN` by default (assuming an English browser
    locale) and switches all listed strings to German on click, without a
    page reload.
  - Reloading the page after switching to DE keeps DE (persisted via
    `localStorage["gg-lang"]`).
  - Setting `localStorage["gg-lang"] = "de"` from the console before load and
    refreshing starts the game in German.
  - The existing game-nav links (More Games / Source / Feedback / Star) and
    version badge are unaffected by the new toggle.
