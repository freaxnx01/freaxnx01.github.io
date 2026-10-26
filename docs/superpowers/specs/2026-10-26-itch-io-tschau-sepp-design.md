# Tschau Sepp on itch.io — design (DRAFT)

> **Status:** brainstorming. Section 1 (pipeline) **approved**. Section 2 (page)
> **presented, awaiting approval**. Once approved: finish this spec, self-review it,
> have the user review it, then run `superpowers:writing-plans`.
> Implementation happens in `freaxnx01/game-tschau-sepp`; this spec lives in the hub repo
> next to the other cross-game specs.

## Goal

Publish `game-tschau-sepp` as the first game on itch.io at
**`freaxnx01.itch.io/tschau-sepp`**, for two reasons:

- **Visibility:** reach players who will never find `github.freaxnx01.ch`.
- **A repeatable channel:** later releases, and later games, ship to itch.io without manual work.

## Decisions made (with the user)

- **Account:** itch.io account `freaxnx01` exists. Profile is set up and links to the hub. No payment or tax setup.
- **Upload trigger:** a `v*` tag push runs a GitHub Action in the game repo, which runs `butler push`. A manual local script was rejected.
- **Build contents:** the same files GitHub Pages serves, unchanged. Hub, star, feedback and changelog links stay in. Runtime or build-time stripping was rejected for now; revisit only if the nav bar looks wrong in the itch.io embed.
- **Page language:** English, with the Swiss German interface presented as a feature.
- **Pricing:** free. No "pay what you want", no donation prompt.

## Facts found

- The game is about 1.9 MB: `index.html` (dc-bundled), `support.js`, `version.js`, `favicon.png`, `vendor/` (React).
- External requests: Google Fonts, `buttons.github.io`, and links to GitHub and the hub.
- P2P play is WebRTC with Google STUN and manual code exchange, with no signaling server. It is expected to work in itch.io's iframe; check this on the first upload.
- Releases are git tags `vX.Y.Z`. `version.js` (`window.GAME_VERSION`) mirrors the tag.
- `butler` isn't installed on agent-dev, and it isn't needed there because CI runs it.
- itch.io has **no API for creating a project or editing its page**. The page is made once by hand; `butler` only uploads builds.

## Section 1 — pipeline (APPROVED)

In `game-tschau-sepp`:

- **`.github/workflows/itch.yml`** runs on `push: tags: ['v*']` and on `workflow_dispatch`, for the first upload and re-pushes.

- **Two variables at the top** hold everything game-specific:
  - `ITCH_TARGET: freaxnx01/tschau-sepp:html5`
  - the file allowlist: `index.html support.js version.js favicon.png vendor/`

- **Build:** copy the allowlist into `dist/`, so `docs/`, `source/`, `scripts/` and the `.md` files never ship. A comment in the workflow says that a new runtime file must be added to the list.

- **Version guard:** fail if `GAME_VERSION` in `version.js` doesn't equal the tag minus the `v`. On `workflow_dispatch`, use `version.js` as the version.

- **Upload:** install `butler` from the official channel (`https://broth.itch.zone/butler/linux-amd64/LATEST/archive/default`), then run `butler push dist "$ITCH_TARGET" --userversion <X.Y.Z>`.

- **API key:** repo secret `BUTLER_API_KEY`, with a copy in Passbolt (suggested name: `itch.io butler API key freaxnx01`). It's a personal account, so there are no org secrets and each game gets `gh secret set` once. **A missing secret is a hard failure with a clear message**, never a silent skip.

- **Reuse:** the canonical copy of the workflow is documented in this hub repo next to the game-nav template. **Rolling it out to other games is out of scope.** Park it as a follow-up.

## Section 2 — itch.io page (PRESENTED, NOT YET APPROVED)

Prepared files in `game-tschau-sepp/docs/itch/`, for the user to paste into the itch.io form:

- **`page.md`**
  - **Title:** Tschau Sepp
  - **Tagline:** "The Swiss card game — solo vs AI or online with friends."
  - **English description:** pitch; the interface is Swiss German (a feature); the rules table (7 / 8 / Under / Ass / Tschau–Sepp, from the README); online play (paste a code, no server, 2–4 players); the two AI levels (Gmüetlich / Gwieft); a closing link to the hub and the repo.

- **`cover.png`** (630×500): rendered from the game, with the title over a played hand.

- **Screenshots** (3–4 at 1280×720): start screen, a game in progress, a "Sepp!" win, the online lobby. Use the hub's `scripts/capture_screenshots.py` and the screenshot recipes in memory.

- **Settings checklist:**
  - **Kind:** HTML, played in browser.
  - **Pricing:** No payments.
  - **Genre:** Card Game.
  - **Tags (10):** `card-game`, `swiss`, `multiplayer`, `singleplayer`, `online`, `ai`, `casual`, `family-friendly`, `browser`, `peer-to-peer`.
  - **Embed size:** measure the size at which the game actually fits; don't guess.
  - **Fullscreen button:** yes.
  - **Mobile friendly:** only if the layout holds up at phone width.
  - **Visibility:** Draft first; check the embed, including P2P between two browsers; then Public.

**Out of scope:** devlogs, itch.io community/forum, game jams, an itch.io link on the hub card, and rollout to other games.

## User's manual steps (after implementation)

1. Create the project on itch.io as a Draft: kind HTML, URL slug `tschau-sepp`.
2. Paste in `docs/itch/page.md`, upload the cover and screenshots, apply the settings checklist.
3. Create an API key (Settings → API keys) and store it in Passbolt.
4. `gh secret set BUTLER_API_KEY -R freaxnx01/game-tschau-sepp`.
5. Start the first upload: `workflow_dispatch`, or the next `vX.Y.Z` tag.
6. Check the embed size and P2P, then set the page to Public.

## Testing

- Lint the workflow with `actionlint`, if available.
- Dry-run the build step locally to confirm `dist/` holds exactly the allowlist.
- Test the version guard against a mismatched tag.
- The first real `workflow_dispatch` run is the integration test. Confirm the build appears on itch.io and plays.
