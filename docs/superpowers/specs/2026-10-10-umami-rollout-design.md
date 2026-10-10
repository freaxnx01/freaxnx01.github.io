# Umami analytics with a `game_start` event for all games — design

**Date:** 2026-10-10
**Reference implementation:** game-tschau-sepp PR #44 (`analytics.js` + events)

## Goal

Every `freaxnx01/game-*` game on the hub gets Umami analytics like Tschau Sepp:
page views plus a `game_start` event each time a game is actually started, and a
privacy notice that names Umami and the server location (Germany).

## Scope

- **In:** the 42 `freaxnx01/game-*` repos linked from `games/index.html` other
  than game-tschau-sepp (already done); a rollout script, its templates and
  tests in this hub repo; one implementation issue per game for the
  game-specific part.
- **Out:** further events (round start/end, score, online), a shared hub-level
  Umami website, external games (`julia-hase/*`), changes to Tschau Sepp,
  re-bundling dc games (Claude Design's own step).

## Decisions

| Question | Decision |
|---|---|
| Umami websites | One website per game, named `game-<name>`, created through the Umami API |
| When `game_start` fires | On every real game start, restarts included (`track`, not `trackOnce`) |
| Event properties | `game` (repo name without `game-`) always; `mode` only if the game has modes |
| Execution | Two stages: deterministic script, then a pipeline issue per game |
| Rollout | Pilot with game-nibbles, game-brickfall, game-acronym-quiz, then the rest |

## Stage 1 — rollout script `scripts/add_umami.py`

It follows `scripts/add_fullscreen_toggle.py`. It works on script-owned clean
clones in `~/.cache/game-rollout/` and never on the sibling working copies. It
reuses `discover_games` and `default_branch` from `add_game_favicons.py`.
Flags: `--dry-run`, `--only REPO[,REPO...]`, `--clones-root PATH`.

For each game:

1. **Website.** Log in to `https://stats.freaxnx01.ch` with the Passbolt entry
   „Umami admin stats.freaxnx01.ch“, the same lookup `umami_rounds.py` uses. Find
   the website by name `game-<name>` in `GET /api/websites`. If there is none,
   create it with `POST /api/websites` (`name`, `domain: github.freaxnx01.ch`).
   The website id is never hard-coded, so re-runs reuse it.
2. **Snippet.** A marker-delimited block goes before `</head>` of the served
   page (`index.html`; game-gorillazz uses `docs/index.html`, the same
   `SERVED_FILE` map as the fullscreen script):

   ```html
   <!-- umami:start -->
   <!-- Umami analytics (self-hosted, server in Germany). data-domains keeps dev/local runs out of the stats. -->
   <script defer src="https://stats.freaxnx01.ch/g.js" data-website-id="<id>" data-domains="github.freaxnx01.ch"></script>
   <script src="./analytics.js"></script>
   <!-- umami:end -->
   ```

   If the block already exists, it is replaced, not duplicated.
   **dc games** (dustline, fruit-frenzy, gem-cascade, iron-valhalla,
   moon-lander, stack-duel, tank-toys) get the same block in their `.dc.html`
   source **and** in the bundled served page, as Tschau Sepp does. Only the
   game's real source file counts as the dc source: design mockups (e.g.
   `game-rhyflitzer/design/mockups/`) and spec files are excluded. The script
   holds an explicit `DC_SOURCE` map per repo rather than guessing.
3. **`analytics.js`.** A copy of `scripts/umami_analytics.js`, a template that
   matches game-tschau-sepp's `analytics.js` byte for byte, written next to the
   served page.
4. **README privacy section.** `## Datenschutz / Privacy` in German and English,
   from the template `scripts/umami_privacy.md`. It says that visits and game
   starts (game, mode) are counted with Umami, self-hosted on a server in Germany
   (`stats.freaxnx01.ch`). It says that no cookies are set and no personal data
   is stored, that the IP address is used only transiently for country and
   region, and that the game runs unchanged if the script is blocked. If the
   section exists, it is replaced. The anchor stays `#datenschutz--privacy`.
5. **Commit and release.** `feat(analytics): add Umami page views`. Games with
   `version.js` get a minor release (version bump, CHANGELOG section, tag), using
   the same release helpers as the fullscreen rollout. Games without
   `version.js` (gorillazz, maze-muncher, neon-pong, rhyflitzer, zen-sudoku) get
   the commit only. Then push to the default branch.

A page that already carries the current block, file and section is skipped,
so re-running is safe.

## Stage 2 — one issue per game (game-specific part)

The script `scripts/create_umami_issues.py` creates the issue in each repo from
the template `scripts/umami_issue.md`, and labels it `ai-implement` so the
agent-workflow pipeline implements it. Titles follow the conventional-commit
convention:

**`feat: track game_start and link the privacy notice from the game menu`**

The body states the following.

- `analytics.js` is already loaded (stage 1). Call
  `window.gameAnalytics.track('game_start', {game: '<name>', mode: '<mode>'})`
  at the point where a game actually begins: start button, new game, restart or
  "play again". It must not fire on page load, on menu navigation or on
  pause/resume.
- `mode` names the selected variant (e.g. `1p`/`2p`, difficulty, level set,
  `online`). Leave the property out if the game has no modes. Use short
  lowercase values, never player names or typed-in text.
- Guard the call (`try` / existence check) so the game runs unchanged when
  `g.js` is blocked or offline.
- Add a „Datenschutz“ link in the game's own menu, start screen or settings,
  pointing to `https://github.com/freaxnx01/<repo>#datenschutz--privacy`
  (`target="_blank" rel="noopener"`). **Not** in `#game-nav`, because a wider nav
  covers game buttons at 1280×720.
- dc games: make the change in the `.dc.html` source and in the bundled
  `index.html`. Do not re-bundle.
- Acceptance criteria: a headless test with a stubbed `window.umami.track`
  records exactly one `game_start` per start, with the expected properties.
  The game works with `g.js` blocked. The privacy link is visible and opens the
  README section.

game-trip-muncher has no pipeline, so it is implemented locally from the same
issue text instead of being labeled `ai-implement`.

## Rollout order

1. Run the script for the pilot (`--only game-nibbles,game-brickfall,game-acronym-quiz`).
   Check the live pages: g.js loads, a page view shows up in Umami.
2. Create the 3 pilot issues and let the pipeline implement them. Review the PRs
   and a `game_start` in the Umami dashboard. Then tighten the issue template
   where the agents went wrong.
3. Run the script for all remaining games, then create the remaining issues in
   batches. The agent-run wall-clock cap and parallel-dispatch limits apply,
   so don't flood the pipeline.
4. Add a pointer to both scripts to the Analytics section of `CLAUDE.md`.

## Testing

- pytest for the pure helpers, in the style of `tests/test_add_fullscreen_toggle.py`:
  snippet injection before `</head>`, block replacement (idempotence), README
  section insert and replace, dc dual-file handling, and the website lookup that
  creates only when missing (with the API mocked).
- `--dry-run` over all games before any real run, listing the actions per repo.
- Stage 2 correctness is checked in each PR by its acceptance criteria.

## Risks

- **Umami API shape**: the `POST /api/websites` fields depend on the Umami
  version. Verify them against the server once before the pilot.
- **dc source drift**: if a later Claude Design re-bundle doesn't carry the
  source block, the served page loses the snippet. That's why the block goes
  into the source as well.
- **Pipeline load**: 41 pipeline runs. Dispatch in batches and watch for green-but-empty
  runs (see the pipeline background-delegation note).
