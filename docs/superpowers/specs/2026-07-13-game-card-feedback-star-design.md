# Game card feedback & star — design

**Status:** Approved by user (2026-07-13). Ready for implementation planning.

**Source idea:** `2026-07-13-game-card-feedback-star` (originally captured in this
repo's `docs/ideas.md`).

## Problem

Players who finish a game have no easy way to (a) leave feedback / report a bug,
or (b) show appreciation by starring the game's GitHub repo, without leaving the
game and hunting down the repo themselves.

## Scope

This feature lives entirely in each `game-<name>` repo (not in this hub repo,
`freaxnx01.github.io`). This session produces the design + a copy-paste-ready
snippet; applying it to the existing game repos is separate follow-up work
(not done in this session).

Out of scope: GitHub Discussions as a feedback channel (would require enabling
Discussions per repo — deferred in favor of the simpler Issues-only path).

## Design

Every game repo already ships a small floating nav bar, `#game-nav`
(bottom-right, translucent dark pill, low-opacity until hovered), containing:

```
More Games… · Source
```

Example (from `game-stack-duel/index.html`):

```html
<!-- game-nav -->
<nav id="game-nav" aria-label="Game navigation" style="position:fixed;right:10px;bottom:8px;z-index:2147483647;display:flex;gap:12px;align-items:center;font:600 13px/1.4 system-ui,-apple-system,sans-serif;padding:6px 11px;border-radius:8px;background:rgba(15,17,26,.55);backdrop-filter:blur(4px);-webkit-backdrop-filter:blur(4px);opacity:.55;transition:opacity .2s" onmouseover="this.style.opacity=1" onmouseout="this.style.opacity=.55">
  <a href="https://github.freaxnx01.ch/games/" style="color:#8fd8e8;text-decoration:none">More Games…</a>
  <span style="color:#5a6072" aria-hidden="true">·</span>
  <a href="https://github.com/freaxnx01/game-stack-duel" target="_blank" rel="noopener" style="color:#8fd8e8;text-decoration:none">Source</a>
</nav>
```

This design extends that bar to:

```
More Games… · Source · Feedback · [★ Star widget]
```

### Feedback link

A plain text link, styled identically to the existing `More Games…` / `Source`
links (`color:#8fd8e8; text-decoration:none`), opening in a new tab
(`target="_blank" rel="noopener"`), deep-linking to a pre-filled new-issue form:

```
https://github.com/freaxnx01/game-<name>/issues/new?title=%5BFeedback%5D%20game-<name>&labels=feedback
```

- Title is pre-filled as `[Feedback] game-<name>` so incoming issues are
  identifiable and consistent across all game repos.
- `labels=feedback` pre-applies a `feedback` label. GitHub silently ignores the
  `labels` param if that label doesn't yet exist in the target repo (no error,
  just no label applied) — so repos without a `feedback` label pre-created still
  work, just without the label. Creating the label per repo is a nice-to-have,
  not a hard requirement.

### Star widget

GitHub's official iframe star button (the `ghbtns.com`/`buttons.github.io`
embed), small size, **with live star count shown**, pointed at
`freaxnx01/game-<name>`. Clicking it stars the repo via the user's own GitHub
session (prompts login if not authenticated) — no API keys, no backend.

```html
<a class="github-button" href="https://github.com/freaxnx01/game-<name>" data-icon="octicon-star" data-size="small" data-show-count="true" aria-label="Star freaxnx01/game-<name> on GitHub">Star</a>
<script async defer crossorigin="anonymous" src="https://buttons.github.io/buttons.js"></script>
```

No Subresource Integrity (`integrity="sha384-..."`) hash is pinned on this
script: GitHub updates `buttons.js` periodically, and a pinned hash would go
stale and silently break the button until manually re-pinned. `crossorigin="anonymous"`
is kept (harmless, enables cleaner error reporting); the residual supply-chain
risk of GitHub's own CDN is accepted as out of scope for a game-page nav
widget.

Known visual seam: the iframe renders in GitHub's own light/white chrome and
won't perfectly match the dark translucent pill background. This is accepted —
a cross-origin iframe can't be restyled to match, and re-implementing a custom
star-count-and-click widget was considered and rejected as unnecessary
complexity for a small cosmetic mismatch.

### Final nav bar order

`More Games…` · `Source` · `Feedback` · `[★ Star N]`

Separators (`·`) match the existing style. The star widget goes last since it's
visually distinct (its own island) regardless of position.

## Rollout

Not part of this design/implementation cycle. Once the snippet is finalized,
propagating it to each existing `game-<name>` repo (currently: game-barrel-shooter,
game-battleship-toys, game-stack-duel, game-tank-toys, game-plod,
game-moon-lander, game-dustline, game-bmx-beach-jam, game-beach-buggy-racer,
game-space-invaders, and any others not yet enumerated here) is separate
follow-up work, likely scripted/batched given the repeated nature of the edit.
New games going forward should include the full 4-item nav bar from the start.

## Testing

No automated tests — this is a static HTML/CSS snippet with no app logic.
Verification is manual: load a game page, confirm the nav bar renders all four
items, confirm Feedback opens a pre-filled GitHub issue form in a new tab, and
confirm the star button shows a live count and stars the repo on click (when
logged into GitHub).
