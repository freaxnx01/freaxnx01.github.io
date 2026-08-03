# Per-Game i18n (EN/DE) — Convention + Pilot Design

**Issue:** #14 — "Add DE/EN support to every game (default EN)"

## Problem

Games in the Browser Games Hub live in ~37 independent `game-<name>` repos with no
shared framework or build step. Some already have a bilingual UI (built
organically, not by convention); most have none. There's no established pattern
for adding a language toggle, and "every game" is too large a scope for one
implementation pass — this design covers the reusable convention plus applying it
to three representative pilot games. Rolling it out to the remaining games is
separate, tracked backlog work.

## Findings from the existing codebase

- **`game-wortduell`** already has full i18n: a `T = { de: {...}, en: {...} }`
  string dictionary, a `t() { return this.T[this.state.lang]; }` accessor,
  `state.lang` (currently defaulting to `'de'`), and a toggle button. It's a
  German-vocabulary word game (the dictionary of playable words is German) —
  i18n here means the UI chrome, not the gameplay content.
- **`game-geography-quiz`** shows the same `{{ t.xxx }}` / EN-DE-toggle shape in
  its markup — also already has i18n.
- **`game-nibbles`** and **`game-millionenfrage`** have zero i18n scaffolding —
  every UI string is a hardcoded literal. `game-nibbles` draws all its UI via
  canvas `fillText` (no DOM text at all for gameplay); `game-millionenfrage`'s
  actual *content* (trivia questions) is German-language content, not just UI
  chrome — translating that is a content-authoring effort out of scope here.
- Every game repo is a single committed `index.html` at its root, no build step,
  direct push to `main` (confirmed during the favicon rollout, issue #13).

## Scope

**In scope:** the reusable i18n convention, applied to three pilot games:
`game-nibbles` (canvas-only, no existing i18n), `game-geography-quiz` (DOM-heavy,
already has the shape), `game-wortduell` (German-native, already has the shape,
UI-chrome-only translation).

**Out of scope:** the other ~34 games (tracked separately), translating
`game-millionenfrage`'s trivia question content, any shared/site-wide language
preference (each game keeps its own independent choice), browser-locale
auto-detection.

## Convention

Every game that adopts this pattern gets:

- **`T` dictionary** — `T = { en: { key: 'string', ... }, de: { key: 'string', ... } }`,
  a plain object literal near the top of the component. One flat key per UI
  string, no nesting.
- **`state.lang`** — part of component state, defaulting to `'en'` on first load
  (no saved preference, no browser-locale detection — matches the issue's literal
  "default EN").
- **`t()` accessor** — `t() { return this.T[this.state.lang]; }`.
- **Toggle control** — an EN/DE toggle that calls `this.setState({ lang })` and
  persists the choice into that game's existing localStorage prefs blob (each
  pilot game already has one, e.g. `wortduell-prefs`). The language preference is
  per-game, not shared across the hub.
- **Interpolation** — `{n}` / `{name}`-style placeholders resolved with
  `.replace()`, matching `wortduell`'s existing convention. No new templating
  engine.

## Per-pilot-game application

- **`game-wortduell`**: flip the default from `lang: 'de'` to `'en'`. Audit the
  file for any UI string not already routed through `t()` and route it. The
  German word dictionary (the actual gameplay content) is untouched — only the
  UI chrome changes language.
- **`game-geography-quiz`**: confirm/flip its default to `'en'`; audit for any
  string not already using the `t.` pattern.
- **`game-nibbles`**: full retrofit.
  - Add `T`, `state.lang` (via its existing `settings` load/save pattern), and
    `t()`.
  - Replace every literal string passed to `this.txt(...)` with a
    `this.t().key` lookup (title screen, setup screen, in-game HUD, dialogs).
  - Add a small DOM button overlaid near the canvas for the toggle — the canvas
    itself can't host a clickable element. Also add a keyboard shortcut
    consistent with the game's existing single-letter shortcuts (`M` toggles
    sound; `L` toggles language).

## Error handling

A missing key in one language's `T` object is a coding mistake to catch at
review time, not a runtime condition to guard against — no fallback/default-key
logic. (A cheap same-keys sanity check is fine as a comment or manual check, not
runtime code.)

## Testing

These are static single-file games with no test infrastructure (same precedent
as the favicon rollout, issue #13) — verification is manual: toggle the
language, confirm every visible string switches, confirm the choice persists
across a reload.

## Rollout

This design produces the convention plus three worked examples. Applying it to
the remaining ~34 games is tracked separately, game by game, as capacity allows.
