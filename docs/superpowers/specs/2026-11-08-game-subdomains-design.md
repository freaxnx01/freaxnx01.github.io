# Game subdomains: `<name>.freax.games` — design

**Status:** approved in chat 2026-11-08, spec awaiting review
**Follows:** `2026-11-07-short-domains-design.md` (issue #40, live since 2026-11-08)

## Goal

Every hub game is served from its own subdomain, `<name>.freax.games`, and that address
stays visible in the browser. `<name>` is the repo name without `game-`
(`game-wipfelkratzer` → `wipfelkratzer.freax.games`). This replaces the "subdomain only
for promoted games" part of the short-domains design.

Decisions from the session:

- Real hosting per subdomain, not a redirect: each game repo gets its own GitHub Pages
  custom domain.
- Saved progress in the browser (localStorage) is **not** carried over. Most of it was
  already left behind on `github.freaxnx01.ch` by the move to `freax.games` on
  2026-11-08; a second move only loses what was played since. Move soon.
- Pilot with Wipfelkratzer and Splashdown (they link to each other), then all other
  games in one wave.
- Out of scope: the "More Games" footer links (`github.freaxnx01.ch/games/`) in the
  games — they keep working through the redirect; and any storage bridge.

## Scope

43 hub games: every card in `games/index.html` whose play link is
`https://freax.games/game-<name>/` or `https://github.freaxnx01.ch/game-<name>/`.
Not affected: Rhyflitzer (own domain `rhyflitzer.ch`), Dogwash (external).

Survey of the 43 repos (2026-11-08): no root-relative paths, no `/game-<name>/`
self-references, no service worker, no web manifest, no existing `CNAME`. All Pages
sites are legacy branch builds. So every game runs unchanged from `/`.

## How a game moves

Per game, in this order (the order matters):

1. **Cloudflare:** DNS record `<name>.freax.games` CNAME `freaxnx01.github.io`, DNS only.
   It overrides the interim wildcard `*.freax.games` (proxied, 302 to
   `freax.games/<name>/`). Between step 1 and 2 the subdomain shows GitHub's 404 for
   a few seconds.
2. **GitHub:** `PUT /repos/freaxnx01/game-<name>/pages` with `cname=<name>.freax.games`.
   GitHub commits a `CNAME` file to the Pages branch and from then on redirects
   `freax.games/game-<name>/` (and through Cloudflare `github.freaxnx01.ch/game-<name>/`)
   to the subdomain.
3. **HTTPS:** once the certificate state is `approved`, `https_enforced=true`.

The reverse order (GitHub first) loops: `freax.games/game-x/` → `x.freax.games` →
wildcard → `freax.games/x/` → stub → `/game-x/`.

`freax.games` is a verified domain of the freaxnx01 account, which covers its
subdomains, so no one else can claim `<name>.freax.games`.

A script, `scripts/move_to_subdomain.py <name>…`, does steps 1–3 and checks the result
(subdomain serves 200, old path redirects there). It needs the Cloudflare token from
Passbolt, so it runs in a maintainer session, not in the pipeline.

## Hub changes (this repo)

- Play links in `games/index.html` become `https://<name>.freax.games/`.
- `scripts/hubsite.py`: `PLAY_RE` also accepts `https://<name>.freax.games/` and still
  yields the repo name `game-<name>`; `game_url(repo)` returns the subdomain URL.
- `scripts/make_short_links.py`: stubs `freax.games/<name>/` forward to
  `https://<name>.freax.games/` (query and hash kept).
- `scripts/add_game_favicons.py`, `capture_screenshots.py`, `capture_wortduell.py`
  follow through `hubsite`.
- `scripts/check_domains.py`: expectations for the subdomain scheme.
- Hub `CLAUDE.md`: how a new game gets its subdomain.

The hub change ships after the games have moved (until then the old links still work
and would only redirect).

## Changes in game repos

| Repo | Change |
|------|--------|
| `game-tschau-sepp` | Umami `data-domains` add `tschau-sepp.freax.games` (`index.html` and `source/Tschau Sepp Online.dc.html`); `scripts/sim/test-invite-link.mjs` fixture to the new origin |
| `game-toepferscheibe` | Umami `data-domains` add `toepferscheibe.freax.games` |
| `game-wipfelkratzer` | `js/game.js` `SPLASHDOWN_URL` → `https://splashdown.freax.games/` |
| `game-kit-racer` | `test/signal.test.mjs` fixture URLs; `tools/aerodrome-tracks.mjs` default source → `https://aerodrome-apex.freax.games/` |
| `game-gorillazz` | remove the redundant `.github/workflows/deploy.yml` (Pages stays legacy from `main:/docs`) before the move |
| `game-n-s-clone` | nothing to change; its branch is `master` — the script must not assume `main` |

Umami changes merge before the move, so no visit is lost. The Umami website IDs stay.

## Effects to accept

- Saved progress and settings start fresh per game (see Goal).
- Settings that were shared across games through the common origin (e.g. a language
  choice) become per game.

## Testing

- Unit tests for `hubsite`, `make_short_links`, `move_to_subdomain` (planning only, with
  the Cloudflare and GitHub calls behind a small client that the tests replace).
- Live check after each step: `check_domains.py` and the script's own check.
- Pilot first: Wipfelkratzer and Splashdown, play both in a browser, follow the
  Wipfelkratzer → Splashdown link and its `zurueck` back-link.
