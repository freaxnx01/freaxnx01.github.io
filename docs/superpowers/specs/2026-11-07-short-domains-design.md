# Short domains: freax.games and rhyflitzer.ch — design

**Status:** approved in chat 2026-11-07 (scheme and approach), spec awaiting review
**Blocked on:** the maintainer registering `freax.games` and `rhyflitzer.ch`

## Goal

`github.freaxnx01.ch/games/` and `rhyflitzer.freaxnx01.ch` are too long to copy from a
note or a newspaper, and "freaxnx01" confuses people. Every game gets an address that
can be read out loud and typed without mistakes.

Decisions from the session:

- New domains: **`freax.games`** for the hub and all games, **`rhyflitzer.ch`** for
  Rhyflitzer. Both looked unregistered in RDAP on 2026-11-07.
- **Mixed scheme:** every game is reachable at a short path `freax.games/<name>`,
  where `<name>` is the repo name without `game-`. A subdomain is only given to a
  game that is promoted on its own, currently Rhyflitzer.
- No public URL shortener.

## Target addresses

| What | Today | After |
|------|-------|-------|
| Hub landing | `github.freaxnx01.ch/` | `freax.games/` |
| Games hub | `github.freaxnx01.ch/games/` | `freax.games/games/` (and `freax.games/` links there prominently) |
| A game | `github.freaxnx01.ch/game-wipfelkratzer/` | `freax.games/game-wipfelkratzer/`, short: `freax.games/wipfelkratzer` |
| Rhyflitzer | `rhyflitzer.freaxnx01.ch/` | `rhyflitzer.ch/`, plus `rhyflitzer.freax.games` and `freax.games/rhyflitzer` forwarding there |
| NFZ link | `rhyflitzer.freaxnx01.ch/nfz` | `rhyflitzer.ch/nfz` (the stub is relative, no change) |

## How it works

**GitHub Pages.** A user site's custom domain also serves all project sites of that
account. Setting the `CNAME` of `freaxnx01.github.io` to `freax.games` therefore moves
every `game-*` repo to `freax.games/game-<name>/` with no change in the game repos.
A repo with its own `CNAME` (Rhyflitzer) keeps its own domain. GitHub Pages allows
exactly one custom domain per repo; every extra name is a redirect at Cloudflare.

**Short paths.** The hub repo gets one stub `<name>/index.html` per game that forwards
to `/game-<name>/` and keeps query and hash. The pattern is
`game-rhyflitzer/prototype/index.html`. A script generates the stubs from the
cards in `games/index.html`, so a new game gets its short path when the script runs.
The script refuses a name that clashes with a top-level directory (`games`, `docs`,
`scripts`, `testhub`, `tests`, `assets`). The script skips cards whose play link is
not a `game-*` repo on this site (e.g. `julia-hase.github.io/dogwash/`). A card with
its own domain (Rhyflitzer) gets a stub that forwards to that domain.

**DNS (Cloudflare, zone per domain).**

- `freax.games` apex: the four GitHub Pages A records (185.199.108–111.153) and AAAA
  records; `www` CNAME to `freaxnx01.github.io`.
- `rhyflitzer.ch` apex: the same; `www` CNAME to `freaxnx01.github.io`.
- `rhyflitzer.freax.games`: proxied, Redirect Rule 301 to `https://rhyflitzer.ch`
  with path and query kept.
- `github.freaxnx01.ch`: proxied (orange cloud), Redirect Rule 301
  `https://github.freaxnx01.ch/*` → `https://freax.games/${1}` with the query kept.
- `rhyflitzer.freaxnx01.ch`: proxied, Redirect Rule 301 to `https://rhyflitzer.ch/${1}`.
- No wildcard records (`*.freax.games`): GitHub warns that they allow subdomain takeover.

**Umami.** `data-domains` filters on the hostname. Before the switch, each tag gets the
new hostnames **added** (old and new side by side), so counting never stops:
`game-tschau-sepp`, `game-toepferscheibe`, `game-rhyflitzer` (`index.html`,
`editor/index.html`). After the switch, the old hostnames can stay; they are harmless.

**Links.** `games/index.html` holds 44 absolute `https://github.freaxnx01.ch/game-<name>/`
play links. They stay absolute (shared links and the scripts read them) and switch to
`https://freax.games/game-<name>/` at the switch; Rhyflitzer's card links to
`https://rhyflitzer.ch/`. The scripts that know the domain get one shared constant,
`SITE = "https://freax.games"`, and accept both domains while reading:
`add_game_favicons.py` (`PLAY_RE`, parses the play links), `capture_screenshots.py`
(`BASE_URL`), `capture_wortduell.py` (`URL`). About 40 game repos link back to the hub
with the old domain. The 301 keeps those working; updating them is optional follow-up
work and out of scope here.

## Accepted cost

- **Saved data stays behind.** `localStorage` belongs to the origin. High scores,
  settings, the shared `gg-dev` flag and Rhyflitzer's album stay on the old domains.
  The redirect sends players to an empty store. This is accepted for a hobby hub. A
  hub note ("new address, high scores restart") is optional.
- **Short-lived certificate gap.** GitHub issues the HTTPS certificate after the
  `CNAME` change; until then the site may show a certificate warning for a few minutes.
  Switch outside the NFZ publication window.

## Order of the switch

1. The maintainer registers the domains and adds both zones to Cloudflare.
2. Add the new hostnames to Umami `data-domains`, generate the short-path stubs, and
   make the scripts accept both domains. All of this works on the old domain too.
3. Set the DNS records for `freax.games` and `rhyflitzer.ch` (DNS only, grey cloud).
4. Change `CNAME` in `freaxnx01.github.io` → `freax.games`, and in `game-rhyflitzer` →
   `rhyflitzer.ch`; in the same hub commit, point the 44 play links and `SITE` to the new
   domain. Wait for "HTTPS certificate issued", then turn on Enforce HTTPS.
5. Turn on the Cloudflare redirect rules for the old hostnames and `rhyflitzer.freax.games`.
6. Verify (below), then update `CLAUDE.md` (domain, `data-domains` rule).

## Verification

A script (`scripts/check_domains.py`, curl-level, no browser) asserts:

- `https://freax.games/games/` → 200; `https://freax.games/wipfelkratzer` ends at
  `/game-wipfelkratzer/` with query and hash kept
- `https://github.freaxnx01.ch/game-wipfelkratzer/?x=1` → 301 to
  `https://freax.games/game-wipfelkratzer/?x=1`
- `https://rhyflitzer.ch/` → 200; `https://rhyflitzer.ch/nfz` ends at
  `/?utm_source=nfz&utm_medium=artikel`
- `https://rhyflitzer.freaxnx01.ch/nfz` and `https://rhyflitzer.freax.games/` → 301 to `rhyflitzer.ch`
- Umami receives a pageview with hostname `freax.games` and one with `rhyflitzer.ch`
  (realistic user agent, campaign `claude-test`)

## Out of scope

- Subdomains for other games (added one at a time later, like Rhyflitzer).
- Rewriting old-domain links inside the ~40 game repos.
- Migrating `localStorage` between origins.
- `mapmadness.freax.games` (the game is called Rhyflitzer now; can be one more redirect rule later).
