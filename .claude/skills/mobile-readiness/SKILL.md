---
name: mobile-readiness
description: Maintain docs/mobile-readiness.md — re-audit every hub game for phone readiness (touch, manifest, reload in fullscreen, iPhone home-screen hint) and update the table and checklists, or file the open checklist items of one game as issues in its game repo. Use when the user asks to refresh/update the mobile list, check which games are mobile-ready, or "make <game> mobile-ready" / "create the mobile issues for <game>".
---

# Mobile readiness

`docs/mobile-readiness.md` tracks which Games Hub games work on a phone and what each
still needs to become an installable app. This skill has two jobs:

- **refresh** — re-audit the games and bring the document up to date.
- **issues `<game>`** — file the open checklist items of one game as issues in its repo
  and link them in the document.

If the user doesn't say which, ask (interview tool, one question).

## The four checklist items (fixed wording, same order in every game section)

1. Make steering/UI mobile-ready
2. Add what's needed for "App installieren" (manifest, 192/512 + maskable icons, apple-touch-icon, theme-color)
3. iPhone hint for adding to the home screen ("Teilen → Zum Home-Bildschirm")
4. Ability to reload when in fullscreen / installed app

`[x]` only when the code proves it. A linked issue goes after the item as
` — game-<name>#<N>`.

## Where things are

- Game list (source of truth): the hub cards in the root `index.html`. Repo = `game-<name>`
  where the play link is `https://<name>.freax.games/` (Rhyflitzer: `rhyflitzer.ch`,
  repo `game-rhyflitzer`). Local clones: `~/repos/github/freaxnx01/public/game-*`.
- Reference implementations and platform notes: the document's own **How to** section.
  Keep it current when a game becomes a better reference.

## refresh

Read-only on the game repos: `git -C <repo> fetch -q origin`, then `git grep` /
`git show origin/<default>:<file>` on the default branch. Never check out, edit or push
a game repo here. No builds, no browsers — `git grep` is enough and keeps memory low.

Per game, look for:

- **touch**: `touchstart`/`pointerdown` handlers, on-screen buttons/stick/pad, a `touch*.js`
  → `yes`; click-only UI that works by tapping → `tap`; keyboard/mouse only → `no`.
- **manifest**: `<link rel="manifest">` (and whether a maskable icon and an
  `apple-touch-icon` exist — note what is missing).
- **reload**: a reload control usable without the browser bar (e.g. `location.reload()`
  behind a button such as `#reload-btn`, `#reloadbtn`).
- **iOS hint**: a "Zum Home-Bildschirm" / "Add to Home Screen" hint, `navigator.standalone`
  checks.

Bundled dc-tool games keep their template JSON-escaped inside `index.html`; grep for the
escaped forms too (`<`, `\"`), or say "unclear" rather than guess.

Classify: **mobile-ready** (touch controls, UI fits a phone), **mobile candidate**
(playable on a phone with reasonable effort), **not a candidate** (needs keyboard/mouse
precision). One-line reason each; "unclear – needs a phone test" is a valid answer.

Then update the document in place, keeping its structure (Summary table, Todo per game,
Not a candidate, Games not on the hub, How to):

- Update the date line, the counts, the table rows and the checkbox states.
- **Never uncheck an item or drop an issue link a human added** unless the code clearly
  regressed — then say so in the report.
- New hub games get a row and (if ready/candidate) a section; removed ones move out.

Show the user a short diff summary (what changed status, which boxes flipped) before
committing.

## issues `<game>`

1. Find the game's section; take its open (`[ ]`) items that have no linked issue yet.
   Check the repo's open issues first (`gh issue list -R freaxnx01/game-<name> --search`)
   so you don't file a duplicate — link an existing one instead.
2. One issue per item, title in Conventional Commits form, e.g.
   `feat(pwa): make <Game> installable as an app (manifest, icons)`,
   `feat(pwa): reload button for the fullscreen app`,
   `feat(pwa): show iPhone players how to add <Game> to the home screen`,
   `feat(touch): touch controls for phones`.
   Body: what's missing (from the audit), the goal, and the reference implementation
   from **How to** (link the reference issue, e.g. game-rhyflitzer#1076 / #1080,
   game-barrel-shooter#50). Label `needs-enrichment` only (create it if missing; apply
   labels in separate calls). Write issues in English.
3. Read each issue back (`gh issue view`) and add ` — game-<name>#<N>` to the item in the
   document.

Don't dispatch or enrich here — that happens in the game repo's own session.

## Committing

- Docs-only change: commit with `docs(mobile): …` and push straight to `master`
  (unprotected; the repo's convention for docs).
- The main clone may hold unrelated uncommitted changes — never commit, stash or reset
  them. Work in a temporary worktree:
  `git worktree add <mktemp dir>/hub origin/master -b wt/<name>`, commit, rebase on
  `origin/master`, `git push origin HEAD:master`, then remove that worktree and branch.
- GitHub auth: only the direnv `GH_TOKEN`. On 401 / "Bad credentials", stop and tell the
  user; never fall back to another login.

If you run into blockers, find a solution and update this skill for the future.
