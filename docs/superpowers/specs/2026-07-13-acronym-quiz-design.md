# Acronym Quiz — design (IN PROGRESS — brainstorming phase, not yet fully approved)

**Status:** Section 1 (Modes & navigation) was presented to the user and we were
interrupted before they approved it. Resume by re-confirming Section 1, then
continue presenting Sections 2–5 below, one at a time, per the
`superpowers:brainstorming` skill flow (ask "does this look right?" after each).

## Source material

- Original design proposal (visual mockup, terminal/CLI direction): `/home/freax/LocalSend/Acronym Quiz Proposal.html`
  — this is a Claude "design canvas" bundle (self-unpacking JS). The actual template/markup was extracted and decoded to:
  `docs/superpowers/specs/2026-07-13-acronym-quiz-proposal-decoded.html` (plain HTML, readable directly).
  - It shows 3 screens: **Start** (topic checkboxes + difficulty radio + RUN QUIZ), **Quiz** (question header w/ streak+score, timer bar, acronym, 4 lettered options A–D), **Results** (score/rank, run.log of each question ✔/✘, RUN AGAIN / share result buttons).
  - Palette: near-black bg `#08090b`, panel `#0c0f0d`, border `#1f2a22`, green accent `#4ade80`, amber `#facc15`, red `#f87171`, text `#e8f5e8`/`#c9d1c9`/`#7d8a7d`/`#5c675c`, font `JetBrains Mono`. Scanline overlay + blinking cursor block on the title.

- User's raw notes (captured verbatim, also duplicated below): expand scope well beyond the single mockup into a bilingual acronym platform with a searchable DB and 3 game modes + a browse mode.

## Codebase conventions (researched)

- Each game lives in its own `game-<name>` GitHub repo (GitHub Pages, root `index.html`), gets a card in this repo's `games/index.html`.
- Reference sibling repo: `game-geography-quiz` (bilingual EN/DE, multiple quiz modes, localStorage best-scores) — same shape as what we're building.
- **Tech stack convention discovered:** these repos are NOT hand-written vanilla JS from scratch — they run on a small generated component runtime called **dc-runtime** (`support.js`, header comment: "GENERATED from dc-runtime/src/*.ts — do not edit. Rebuild with `cd dc-runtime && bun run build`"). It's a thin React-based template engine:
  - `index.html` contains `<script src="./support.js"></script>` then an `<x-dc>...</x-dc>` block with Handlebars-style `{{ expr }}` bindings, `<sc-if>` / `<sc-for>` control-flow custom elements, `onClick="{{ handlerName }}"`, `style-hover="..."` for hover styles.
  - A `<script type="text/x-dc" data-dc-script data-props="...">` block defines `class Component extends DCLogic { renderVals() { ... } ... }` — this is where state/handlers/computed view-model values live.
  - `support.js` is copy-paste reusable across repos (near-identical between `game-stack-duel` and `game-geography-quiz`, only a small tail diff). **Plan:** copy it verbatim from `game-geography-quiz` into the new repo.
  - Data is split into a separate file (e.g. `geo-data.js`) and dynamically `import()`ed — **must be served over HTTP**, not opened as `file://`, because of the dynamic import.
- README convention: title, short pitch, Features bullets, Tech notes, Run locally (`python3 -m http.server`), Deploy note, Files list.

## User's raw notes (verbatim, from notes.md)

```
I want to develop an Acronym Quiz in nerdy IT design. design proposal: Acronym Quiz Proposal.html.

Languages UI DE|EN

Grouped by categories

Category: e.g. IT
Sub category: e.g. AI

LSTM stands for Long Short-Term Memory
xLSTM
recurrent neural network (RNN)
GPT

take lot more other from IT like:
ISDN
...

or software development/sw architecture
SDLC

like Glücksrad:
- Choose single letter (Button click or keyboard)
- Solve: type complete rest

separate section: Recursive Acronyms like GNU
- Explain Recursive Acronyms
- show a list with all recursive acronyms (facts)
- Quiz like Glücksrad

Make "DB" with all acronyms:
Acronym|Full|Cat|SubCat|Source|Flag Recursive|Wikipedia link or link to explanation site

Let the user/player search the "DB"
```

## Decisions locked in via clarifying questions (all confirmed by user)

1. **DB scope:** IT + adjacent nerd topics. Broad IT coverage (networking, dev/SW architecture, AI/ML, hardware, security, cloud, protocols/standards) **plus** a nerd-culture category (sci-fi/gaming, e.g. RPG, NPC, FTL) for variety. Target ~150–250+ acronyms total.
2. **Difficulty (junior/senior/greybeard):** changes the **question pool** — each acronym tagged easy/medium/hard; difficulty selects which pool + how plausible the wrong-answer distractors are (greybeard = obscure acronyms + tricky distractors).
3. **Classic Quiz timer/scoring:** timer bar is visual pacing only, **no score effect**. Correct answer = flat points, streak adds a multiplier/bonus. (Matches mockup's streak ×N display; the mockup's varying +100/+120/+140 per question should be reinterpreted as flat base value scaled by streak, not by speed.)
4. **Share result:** copy a text summary (score, rank, streak) to clipboard via the Clipboard API. No external service, no Web Share API needed.
5. **Glücksrad mechanic:** hangman-style. Acronym shown as blank letters (of the *expansion*, not the acronym itself — needs confirming in next session, see Open Questions). Player picks letters one at a time (button grid + keyboard support); correct picks reveal all matching occurrences; limited wrong guesses before a loss; player can attempt to type the full expansion at any time to solve early for a bonus.
6. **Navigation:** hub/menu screen (terminal-style, mode picker) with 4 entries: Classic Quiz, Glücksrad, Recursive Acronyms, Browse DB. Each mode returns to the hub when done.
7. **Localization depth:** UI chrome only (buttons, labels, instructions, results text) gets DE/EN. Acronym expansions and fact/description text stay English (matches user's own notes being written in English already, and most expansions are English terms).
8. **Repo name:** `game-acronym-quiz`.
9. **Content authoring:** Claude authors the full acronym DB (expansions, categories, subcategories, recursive flags, Wikipedia links) from training knowledge; user will spot-check a sample before it ships (not a full manual review of every entry).

## Section 1 — Modes & navigation (drafted, presented to user, NOT YET explicitly approved — re-confirm on resume)

A terminal-styled hub screen (same green-on-black CLI aesthetic as the mockup's start screen) becomes the entry point, listing 4 menu entries:

1. **Classic Quiz** — the mockup's flow: pick topics + difficulty → 10 multiple-choice questions → results/run-log screen. Difficulty selects acronym pool + distractor plausibility. Timer bar is pacing-only. Flat points + streak multiplier.
2. **Glücksrad** — hangman-style letter-reveal + type-the-rest-to-solve. Same topic/difficulty pickers as Classic.
3. **Recursive Acronyms** — explainer of what a recursive acronym is + browsable fact list (GNU, PHP, WINE, etc.) + a Glücksrad-style quiz scoped only to recursive acronyms.
4. **Browse DB** — searchable/filterable table of the full acronym DB (search box + category/subcategory filters), read-only, not scored.

Each mode returns to the hub via a terminal-flavored exit control (e.g. `$ exit`).

## Sections still to present (do these next, one at a time, get approval after each)

### Section 2 — Data model
Draft schema per user's notes: `{ acronym, full, category, subCategory, source, recursive: bool, link, difficulty: 'junior'|'senior'|'greybeard', topicTags: [...] }`. Need to decide: how `topics` (networking/dev/hardware/security/cloud from mockup) map to `category`/`subCategory` — likely category IS the mockup's "topic" concept, subCategory is the finer grouping (e.g. category: IT, subCategory: AI). Also decide storage format (JS module exporting an array, like `geo-data.js`) and whether distractors (wrong MC answers) are hand-authored per acronym or generated at runtime from other same-category entries.

### Section 3 — Screens & visual design per mode
Extend the mockup's terminal aesthetic to: hub/menu screen, Glücksrad play screen, Recursive Acronyms list + quiz screens, Browse DB screen (search input + filterable table, still terminal-styled e.g. `grep`-style search bar). Keep existing mockup screens (start/quiz/results) mostly as-is for Classic Quiz, adapted to also work for Glücksrad's start screen.

### Section 4 — Mechanics recap & edge cases
Nail down: Glücksrad reveal target (letters of the acronym itself, since typing "the complete rest" implies revealing acronym letters then typing the expansion — OR revealing expansion letters directly; **ambiguous in user's notes, must ask**), lives count, scoring formula for both modes, high-score persistence keys (per mode × difficulty?, localStorage), recursive-acronyms quiz question format (probably same Glücksrad mechanic but pool = recursive-flagged entries only).

### Section 5 — Tech, localization, persistence
`index.html` (x-dc/DCLogic component, mirroring `game-geography-quiz` structure) + `support.js` (copied verbatim) + `acronym-data.js` (the DB) + `i18n` dict for DE/EN UI strings (likely inline object, matching geography-quiz's `t.xxx` pattern) + `localStorage` for high scores/best streak per mode and last-used language. README following the established convention.

## Open questions to resolve before finalizing spec

- Glücksrad: reveal letters of the **acronym** or of the **expansion**? User's notes are ambiguous ("choose single letter... solve: type complete rest" — likely: acronym itself is already fully visible as the prompt like Classic Quiz, and Glücksrad reveals letters of the **expansion** as a hangman board, since "type complete rest" implies completing an expansion typed progressively). Confirm with user.
- Exact list of categories/subcategories beyond the IT + nerd-culture split (need a concrete taxonomy before authoring ~150–250 entries).
- Number of lives / wrong-guess tolerance in Glücksrad.

## Next step after design is approved

Write the finalized spec to this same file (replace the "IN PROGRESS" sections with
final content), do the spec self-review pass (placeholder/consistency/ambiguity/scope
check), get user to review the written spec, then invoke `superpowers:writing-plans`
to produce the implementation plan. Implementation itself should use
`superpowers:subagent-driven-development` per user's global instructions.
