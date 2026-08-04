# DE/EN i18n rollout: wortduell, geography-quiz, nibbles — design

## Problem

Issue #23 continues #14: roll the canonical i18n pattern (`i18n.js` /
`window.GG_LANG` / `STRINGS` / `t()` / shared `gg-lang` localStorage key,
documented in `ai-instructions/.ai/stacks/browser-game.md`, piloted on
`game-iron-valhalla`) out to three more games. Each is in a different
starting state:

- **`game-wortduell`** — plain classic-script game (not dc-bundled). Already
  has its own working i18n: a `T = { de: {...}, en: {...} }` dictionary,
  `t() { return this.T[this.state.lang]; }`, `state.lang` defaulting to
  `'de'`, persisted inside its own `wortduell-prefs` localStorage JSON blob
  (alongside sound/player-name/difficulty settings). Has `version.js` but
  **no `#game-nav` footer at all** — no More Games/Source/Feedback/Star
  links, no version badge.
- **`game-geography-quiz`** — dc-bundled (DCLogic/React runtime, same shape
  as Iron Valhalla). Already has `I18N` / `T() { return this.I18N[this.state.lang]
  || this.I18N.en; }` / `state.lang` sourced from its own `terra.lang`
  localStorage key (default `'en'`). **Has `#game-nav`.** Its i18n is deeper
  than UI chrome — quiz content itself (country/capital names, via
  `cname()`/`ccap()`/etc.) is bilingual data keyed off the same
  `state.lang`.
- **`game-nibbles`** — canvas-only rendering, zero existing i18n. **No
  `#game-nav`, no `version.js`** — predates both rollouts. Its entire
  component source lives inside a `<script type="__bundler/template">` tag
  as a JSON-escaped string (a different, non-dc-tool bundler); the tool that
  regenerates `index.html` from that template is unknown at spec-writing
  time.

## Design

### 1. Rewire wortduell and geography-quiz onto `i18n.js`/`gg-lang`

Both games keep their existing `T`/`I18N` dictionaries and their own
`t()`/`T()` accessor methods — only the *language state* moves:

- Add `i18n.js` (copied verbatim from `browser-game.md`) and load it before
  the game's own script, same as Iron Valhalla.
- Change `t() { return this.T[this.state.lang]; }` to
  `t() { return this.T[window.GG_LANG] || this.T.en; }` (wortduell) and the
  equivalent for geography-quiz's `T()`/`cname()`/`ccap()`/etc. — every place
  that currently reads `this.state.lang` reads `window.GG_LANG` instead,
  including geography-quiz's content lookups (country/capital names move
  with the same setting, matching the game's current behavior where
  everything already follows one language flag).
- Remove `lang` from each game's own localStorage prefs blob
  (`wortduell-prefs`, and geography-quiz's dedicated `terra.lang` key) —
  `gg-lang` now owns persistence for both.
- Add a `gg-langchange` listener that forces a re-render (`this.setState({})`
  or equivalent), same pattern as the Iron Valhalla pilot.
- Toggle appears via `i18n.js`'s existing `#game-nav` injection — for
  geography-quiz this works immediately (nav already exists); for wortduell
  it requires part 2 below first.

**Why rewire instead of leaving them alone:** the whole point of documenting
one canonical pattern in `browser-game.md` is that every game ends up on it.
Leaving these two on their own bespoke mechanism means three different i18n
systems permanently coexist across the hub.

### 2. Add `#game-nav` to wortduell and nibbles

Both are missing the standard footer entirely — not part of any i18n work,
just a gap from before the nav/version-badge convention existed. Add the
same `#game-nav` block (More Games / Source / Feedback / Star / version
badge) used by every other game, copied from an existing repo (e.g.
`game-iron-valhalla`) with the repo name swapped. Once it exists,
`i18n.js`'s current `injectToggle()` logic works unmodified — **no changes
to `i18n.js` or `browser-game.md` are needed for this rollout.**

### 3. Add `i18n.js` fresh to nibbles

- `i18n.js` + `#game-nav` (part 2) loaded the same way as any other game.
- A `STRINGS`/`t()` pair added to nibbles' own script, and every literal
  string passed to its canvas text-draw calls (title screen, setup screen,
  in-game HUD, dialogs) routed through `t()`.
- A `gg-langchange` listener triggers a canvas redraw (nibbles' existing
  render loop, forced once on language change).
- Nibbles' packaging tool is unknown. Treat it like the dc-tool games: edit
  only inside the `<script type="__bundler/template">` content, never
  hand-edit anything else in the generated `index.html`, and — per house
  convention for dc-bundled games — the actual repackage/publish step is not
  something to run or guess a CLI for; note in the PR that the change needs
  the real publish step run afterward, the same way dc-tool games are
  handled.

## Testing

No test runner in any of the three repos (buildless static sites, same as
Iron Valhalla) — manual verification per game:

- Toggle EN↔DE via `#game-nav`, confirm every visible string (and, for
  geography-quiz, quiz content) switches immediately, no reload needed.
- Reload after switching to DE — confirms `gg-lang` persistence.
- wortduell: confirm sound/player-name/difficulty prefs still persist
  correctly in `wortduell-prefs` now that `lang` is removed from that blob.
- geography-quiz: confirm the toggle survives the framework's periodic
  `#game-nav` re-render (the exact gotcha `i18n.js` already handles via its
  document-level delegated click listener — verify it actually works here
  too, don't assume the fix generalizes untested).
- nibbles: confirm the toggle button appears despite canvas rendering, and
  triggers a text redraw without disrupting an in-progress game.
