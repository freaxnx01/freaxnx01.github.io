# Games Hub: original title + Wikipedia link for retro clones — design

## Problem

Retro-clone cards on the hub (`data-retro="true"`) mention their inspiration
only loosely, buried in `card__desc` prose (e.g. Brickfall: "8-level
Arkanoid-style brick-breaker..."). There's no consistent, scannable way to see
which classic game a card is a clone of, or to look it up.

## Design

### Data: `data-original-title` / `data-original-url` attributes

Add these two attributes to each `data-retro="true"` `<article class="card">`
in `games/index.html`:

| Card | `data-original-title` | `data-original-url` |
|---|---|---|
| Iron Valhalla — Battlechess | Battle Chess | `https://en.wikipedia.org/wiki/Battle_Chess` |
| Brickfall | Arkanoid | `https://en.wikipedia.org/wiki/Arkanoid` |
| Rockfall | Boulder Dash | `https://en.wikipedia.org/wiki/Boulder_Dash` |
| Oil Fever '89 | Oil Imperium | `https://en.wikipedia.org/wiki/Oil_Imperium` |
| Neon Pong | Pong | `https://en.wikipedia.org/wiki/Pong` |
| Gem Cascade | Bejeweled | `https://en.wikipedia.org/wiki/Bejeweled` |
| Maze Muncher | Pac-Man | `https://en.wikipedia.org/wiki/Pac-Man` |
| Nibbles | Nibbles (QBasic) | `https://en.wikipedia.org/wiki/Nibbles_(video_game)` |
| BMX Beach Jam | California Games | `https://en.wikipedia.org/wiki/California_Games` |
| Cluck & Load | Moorhuhn | `https://en.wikipedia.org/wiki/Moorhuhn` |
| Gorillazz | Gorillas (QBasic) | `https://en.wikipedia.org/wiki/Gorillas_(video_game)` |
| Moon Lander | Lunar Lander (1979) | `https://en.wikipedia.org/wiki/Lunar_Lander_(1979_video_game)` |
| North & South Clone | The North & South | `https://en.wikipedia.org/wiki/The_North_%26_South_(video_game)` |
| Space Invaders | Space Invaders | `https://en.wikipedia.org/wiki/Space_Invaders` |

All 14 currently-tagged `data-retro="true"` cards get both attributes — every
one has a clear single original. No card gets `data-original-title` without
also getting `data-original-url` today, but the rendering must support the
title-only case (see below) since future retro cards may not have a Wikipedia
article.

### Extension: non-retro cards + `data-original-screenshot`

The rendering script keys off `data-original-title` alone (see below), not off
`data-retro="true"` — so cards that aren't tagged retro can carry the same
attributes and still show an "Inspired by …" line. Five such cards were added:

| Card | `data-original-title` | `data-original-url` | `data-original-screenshot` |
|---|---|---|---|
| Dustline | AirStrike 3D: Operation W.A.T. | `https://www.myabandonware.com/game/airstrike-3d-operation-w-a-t-duf` | same (page shows screenshots inline) |
| Kick Fury | Panza Kick Boxing | `https://en.wikipedia.org/wiki/Panza_Kick_Boxing` | `https://en.wikipedia.org/wiki/File:PanzaKickBoxing_cover.png` |
| PLOD | Lemmings | `https://en.wikipedia.org/wiki/Lemmings_(video_game)` | `https://en.wikipedia.org/wiki/File:Amiga_Lemmings.png` |
| Sky Fury | Wings of Fury | `https://en.wikipedia.org/wiki/Wings_of_Fury` | `https://en.wikipedia.org/wiki/File:Wings_of_Fury_Coverart.png` |
| Stack Duel | Tetris for Windows | `https://www.apfeltalk.de/magazin/news/microsoft-tetris-fuer-windows-3-11-direkt-im-browser-spielen/` | `https://classicreload.com/win3x-tetris-for-windows.html` |

A new optional `data-original-screenshot` attribute was also backfilled onto
all 14 original retro cards (see the implementation plan for the per-card
mapping). When present, it renders as a second, separate link — `(screenshot)`
— appended after the title link inside the same `card__inspired` line. Most
Wikipedia images used are cover art / arcade flyers rather than true gameplay
captures (Wikipedia rarely hosts the latter); this is a known limitation, not
a bug.

### Rendering: JS-injected `card__inspired` line

A small script (added to `lightbox.js`, since it already runs a
`DOMContentLoaded`-style pass over `.card` elements) reads
`data-original-title` / `data-original-url` off each card on page load and, if
`data-original-title` is present, injects:

```html
<p class="card__inspired">Inspired by <a href="[data-original-url]" target="_blank" rel="noopener">[data-original-title]</a></p>
```

as the last child of `.card__body`, right after `.card__desc` and before
`.card__badges`.

If `data-original-title` is present but `data-original-url` is absent, render
the same line with plain text instead of a link:

```html
<p class="card__inspired">Inspired by [data-original-title]</p>
```

If neither attribute is present (all non-retro cards, and any future retro
card with no identifiable original), no line is injected — `card__body`
renders unchanged.

### Styling

Add a `.card__inspired` rule to `style.css`: small, muted text (matching the
existing badge/desc secondary-text treatment), sitting between the description
and the badges with the same vertical rhythm as other `card__body` children.

## Testing

Manual verification only (static site, no test suite):

- Open `games/index.html` locally and confirm all 14 retro cards show an
  "Inspired by …" line with a working Wikipedia link.
- Confirm non-retro cards are unaffected (no `card__inspired` line, no layout
  shift).
- Confirm the retro-only filter toggle (`#retro-toggle`) still works alongside
  the new line.
