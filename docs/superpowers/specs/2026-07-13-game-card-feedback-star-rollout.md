# Game-nav feedback + star — rollout checklist

**Source design:** `docs/superpowers/specs/2026-07-13-game-card-feedback-star-design.md`
**Source snippet:** `docs/superpowers/specs/2026-07-13-game-card-feedback-star-snippet.html`

This session (2026-07-13) produced the design + snippet only. Applying the
snippet to each existing `game-<name>` repo is separate follow-up work, not
yet done. Use this checklist when that follow-up happens.

## Per-repo steps

For each repo `game-<name>` below:

1. Clone the repo locally (or open it in an existing worktree).
2. Open `index.html` and find the existing `<!-- game-nav -->` block (a
   `<nav id="game-nav">` with 2 links: "More Games…" and "Source").
3. Replace that whole block (through its closing `</nav>`, and any trailing
   `<script>` tag for `buttons.js` if one already exists from a prior partial
   rollout) with the contents of
   `docs/superpowers/specs/2026-07-13-game-card-feedback-star-snippet.html`,
   substituting every `{{REPO}}` with this repo's exact name (e.g. `game-stack-duel`).
4. Save, then open `index.html` locally in a browser (or via a local static
   server) and confirm:
   - All four items render: `More Games…` · `Source` · `Feedback` · `★ Star N`.
   - `Feedback` opens `https://github.com/freaxnx01/<repo>/issues/new?title=%5BFeedback%5D%20<repo>&labels=feedback`
     in a new tab, with that title pre-filled in GitHub's new-issue form.
   - The star button shows a live star count and, when logged into GitHub,
     starring the repo on click.
5. Commit with message `Add Feedback link and star widget to game-nav` and push.
6. (Optional, nice-to-have per design) Create a `feedback` label in the repo
   via GitHub's Labels UI, so the pre-applied `labels=feedback` query param
   actually attaches a label instead of being silently ignored.
7. Check this repo off below.

## Repos

- [x] game-barrel-shooter
- [x] game-battleship-toys
- [x] game-stack-duel
- [x] game-tank-toys
- [x] game-plod
- [x] game-moon-lander
- [x] game-dustline
- [x] game-bmx-beach-jam
- [x] game-beach-buggy-racer
- [x] game-space-invaders
- [x] game-splashdown
- [x] game-tschau-sepp
- [x] game-esel-running
- [x] game-fruit-frenzy
- [x] game-geography-quiz
- [x] game-gorillazz
- [x] game-kick-fury
- [x] game-n-s-clone
- [x] game-sky-fury
- [x] game-voxel-sandbox

Before starting, cross-check this list against the current `games/index.html`
in this hub repo — new games may have been added to the hub since this
checklist was written, and those repos need the same rollout.

`game-cluck-and-load` shipped after this checklist was written and already has
the full 4-item nav from the start (per "New games going forward" below) — no
rollout needed for it.

## New games going forward

Any new `game-<name>` repo created after this rollout should ship the full
4-item nav bar from the start (paste the Task 1 snippet directly, substituting
`{{REPO}}`), not the old 2-item version.
