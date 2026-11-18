# Mobile readiness of the games

Overview of which Games Hub games work on a phone and what each one still needs for an installed, fullscreen-capable app. Date: 2026-11-18.

Source of truth is the hub list (`index.html`, 45 games: 43 on freax.games, rhyflitzer.ch and the external Dogwash). Status is derived from the code on each game repo's default branch (viewport meta, touch/pointer handlers, manifest, reload control, iOS hint). **Nothing here was tested on a real phone**; "unclear" means a phone test is needed.

## Summary

Legend: touch `yes` = dedicated touch controls, `tap` = click-only UI that works by tapping, `no` = keyboard/mouse only. Manifest/reload/iOS hint are `yes` only when found in the code.

| Game | Status | Touch | Manifest | Reload | iOS hint |
|---|---|---|---|---|---|
| [Barrel Shooter](https://barrel-shooter.freax.games/) | mobile-ready | yes | yes | yes | no |
| [Brickfall](https://brickfall.freax.games/) | mobile-ready | yes | no | no | no |
| [Cluck And Load](https://cluck-and-load.freax.games/) | mobile-ready | yes | no | no | no |
| [Fruit Frenzy](https://fruit-frenzy.freax.games/) | mobile-ready | yes | no | no | no |
| [Gem Cascade](https://gem-cascade.freax.games/) | mobile-ready | yes | no | no | no |
| [Kit Racer](https://kit-racer.freax.games/) | mobile-ready | yes | no | no | no |
| [Maze Muncher](https://maze-muncher.freax.games/) | mobile-ready | yes | no | no | no |
| [Nibbles](https://nibbles.freax.games/) | mobile-ready | yes | no | no | no |
| [Rhyflitzer](https://rhyflitzer.ch/) | mobile-ready | yes | yes | yes | no |
| [Toepferscheibe](https://toepferscheibe.freax.games/) | mobile-ready | yes | no | no | yes |
| [Acronym Quiz](https://acronym-quiz.freax.games/) | mobile candidate | tap | no | no | no |
| [Beach Buggy Racer](https://beach-buggy-racer.freax.games/) | mobile candidate | no | no | no | no |
| [Bmx Beach Jam](https://bmx-beach-jam.freax.games/) | mobile candidate | no | no | no | no |
| [Criss Cross](https://criss-cross.freax.games/) | mobile candidate | tap | no | no | no |
| [Dustline](https://dustline.freax.games/) | mobile candidate | no | no | no | no |
| [Geography Quiz](https://geography-quiz.freax.games/) | mobile candidate | tap | no | no | no |
| [Gorillazz](https://gorillazz.freax.games/) | mobile candidate | no | no | no | no |
| [Huusli Jagd](https://huusli-jagd.freax.games/) | mobile candidate | tap | no | no | no |
| [Iron Valhalla](https://iron-valhalla.freax.games/) | mobile candidate | tap | no | no | no |
| [Marquee Quiz](https://marquee-quiz.freax.games/) | mobile candidate | tap | no | no | no |
| [Millionenfrage](https://millionenfrage.freax.games/) | mobile candidate | tap | no | no | no |
| [Moon Lander](https://moon-lander.freax.games/) | mobile candidate | no | no | no | no |
| [Neon Pong](https://neon-pong.freax.games/) | mobile candidate | no | no | no | no |
| [Oil Fever 89](https://oil-fever-89.freax.games/) | mobile candidate | tap | no | no | no |
| [Photo Puzzler](https://photo-puzzler.freax.games/) | mobile candidate | tap | no | no | no |
| [Rockfall](https://rockfall.freax.games/) | mobile candidate | no | no | no | no |
| [Space Invaders](https://space-invaders.freax.games/) | mobile candidate | no | no | no | no |
| [Splashdown](https://splashdown.freax.games/) | mobile candidate | no | no | no | no |
| [Stylestar](https://stylestar.freax.games/) | mobile candidate | tap | no | no | no |
| [Trip Muncher](https://trip-muncher.freax.games/) | mobile candidate | no | no | no | no |
| [Tschau Sepp](https://tschau-sepp.freax.games/) | mobile candidate | tap | no | no | no |
| [Wipfelkratzer](https://wipfelkratzer.freax.games/) | mobile candidate | tap | no | no | no |
| [Wortduell](https://wortduell.freax.games/) | mobile candidate | tap | no | no | no |
| [Zen Sudoku](https://zen-sudoku.freax.games/) | mobile candidate | no | no | no | no |
| [Aerodrome Apex](https://aerodrome-apex.freax.games/) | not a candidate | no | no | no | no |
| [Battleship Toys](https://battleship-toys.freax.games/) | not a candidate | no | no | no | no |
| [Esel Running](https://esel-running.freax.games/) | not a candidate | no | no | no | no |
| [Kick Fury](https://kick-fury.freax.games/) | not a candidate | no | no | no | no |
| [N S Clone](https://n-s-clone.freax.games/) | not a candidate | no | no | no | no |
| [Plod](https://plod.freax.games/) | not a candidate | no | no | no | no |
| [Sky Fury](https://sky-fury.freax.games/) | not a candidate | no | no | no | no |
| [Stack Duel](https://stack-duel.freax.games/) | not a candidate | no | no | no | no |
| [Tank Toys](https://tank-toys.freax.games/) | not a candidate | no | no | no | no |
| [Voxel Sandbox](https://voxel-sandbox.freax.games/) | not a candidate | no | no | no | no |
| Dogwash (external, julia-hase) | unclear | ? | ? | ? | ? |

Counts: 10 mobile-ready, 24 mobile candidate, 10 not a candidate, plus Dogwash (external repo, not inspected).

## Todo per game

Only mobile-ready and candidate games. Item 1 is checked once steering/UI works on touch (code level, not phone-tested); the other three are checked only when found in the code.

### Barrel Shooter

_mobile-ready._ Reference: touch pad, mobile bar, reload button. No iOS hint, no maskable icon.

- [x] Make steering/UI mobile-ready
- [ ] Add what's needed for "App installieren" (manifest, 192/512 + maskable icons, apple-touch-icon, theme-color)
- [ ] iPhone hint for adding to the home screen ("Teilen → Zum Home-Bildschirm") — game-barrel-shooter#50
- [x] Ability to reload when in fullscreen / installed app

### Brickfall

_mobile-ready._ Paddle follows touchmove; text hints still say mouse/keys.

- [x] Make steering/UI mobile-ready
- [ ] Add what's needed for "App installieren" (manifest, 192/512 + maskable icons, apple-touch-icon, theme-color)
- [ ] iPhone hint for adding to the home screen ("Teilen → Zum Home-Bildschirm")
- [ ] Ability to reload when in fullscreen / installed app

### Cluck And Load

_mobile-ready._ Moorhuhn-style tap to shoot (touchstart/touchmove on the canvas); machine-gun hold fire and weapon switching may be awkward. Phone test needed.

- [x] Make steering/UI mobile-ready
- [ ] Add what's needed for "App installieren" (manifest, 192/512 + maskable icons, apple-touch-icon, theme-color)
- [ ] iPhone hint for adding to the home screen ("Teilen → Zum Home-Bildschirm")
- [ ] Ability to reload when in fullscreen / installed app

### Fruit Frenzy

_mobile-ready._ Pointer-drag to aim, tap to drop; canvas scales to viewport.

- [x] Make steering/UI mobile-ready
- [ ] Add what's needed for "App installieren" (manifest, 192/512 + maskable icons, apple-touch-icon, theme-color)
- [ ] iPhone hint for adding to the home screen ("Teilen → Zum Home-Bildschirm")
- [ ] Ability to reload when in fullscreen / installed app

### Gem Cascade

_mobile-ready._ Match-3 with pointer down/move/up swipes on the canvas.

- [x] Make steering/UI mobile-ready
- [ ] Add what's needed for "App installieren" (manifest, 192/512 + maskable icons, apple-touch-icon, theme-color)
- [ ] iPhone hint for adding to the home screen ("Teilen → Zum Home-Bildschirm")
- [ ] Ability to reload when in fullscreen / installed app

### Kit Racer

_mobile-ready._ Controls.js adds on-screen touch controls when `ontouchstart` exists. Phone test needed.

- [x] Make steering/UI mobile-ready
- [ ] Add what's needed for "App installieren" (manifest, 192/512 + maskable icons, apple-touch-icon, theme-color)
- [ ] iPhone hint for adding to the home screen ("Teilen → Zum Home-Bildschirm")
- [ ] Ability to reload when in fullscreen / installed app

### Maze Muncher

_mobile-ready._ Shows an on-screen touch control when `(pointer: coarse)`. No viewport meta in the template.

- [x] Make steering/UI mobile-ready
- [ ] Add what's needed for "App installieren" (manifest, 192/512 + maskable icons, apple-touch-icon, theme-color)
- [ ] iPhone hint for adding to the home screen ("Teilen → Zum Home-Bildschirm")
- [ ] Ability to reload when in fullscreen / installed app

### Nibbles

_mobile-ready._ Swipe steering via touchstart/touchmove on the canvas.

- [x] Make steering/UI mobile-ready
- [ ] Add what's needed for "App installieren" (manifest, 192/512 + maskable icons, apple-touch-icon, theme-color)
- [ ] iPhone hint for adding to the home screen ("Teilen → Zum Home-Bildschirm")
- [ ] Ability to reload when in fullscreen / installed app

### Rhyflitzer

_mobile-ready._ Touch controls (#535). Manifest, icons and reload button landed 2026-11-18 (game-rhyflitzer#1076, PR#1079); iPhone hint in progress (game-rhyflitzer#1080).

- [x] Make steering/UI mobile-ready
- [x] Add what's needed for "App installieren" (manifest, 192/512 + maskable icons, apple-touch-icon, theme-color)
- [ ] iPhone hint for adding to the home screen ("Teilen → Zum Home-Bildschirm") — game-rhyflitzer#1080
- [x] Ability to reload when in fullscreen / installed app

### Toepferscheibe

_mobile-ready._ Built for an iPad (finger shaping); has an iOS home-screen hint text. No manifest or reload button.

- [x] Make steering/UI mobile-ready
- [ ] Add what's needed for "App installieren" (manifest, 192/512 + maskable icons, apple-touch-icon, theme-color)
- [x] iPhone hint for adding to the home screen ("Teilen → Zum Home-Bildschirm")
- [ ] Ability to reload when in fullscreen / installed app

### Acronym Quiz

_mobile candidate._ Click-only multiple choice; works by tapping. Check layout on narrow screens.

- [ ] Make steering/UI mobile-ready
- [ ] Add what's needed for "App installieren" (manifest, 192/512 + maskable icons, apple-touch-icon, theme-color)
- [ ] iPhone hint for adding to the home screen ("Teilen → Zum Home-Bildschirm")
- [ ] Ability to reload when in fullscreen / installed app

### Beach Buggy Racer

_mobile candidate._ Accelerate + steer + handbrake: needs on-screen pedals/steering.

- [ ] Make steering/UI mobile-ready
- [ ] Add what's needed for "App installieren" (manifest, 192/512 + maskable icons, apple-touch-icon, theme-color)
- [ ] iPhone hint for adding to the home screen ("Teilen → Zum Home-Bildschirm")
- [ ] Ability to reload when in fullscreen / installed app

### Bmx Beach Jam

_mobile candidate._ Pedal, lean and trick keys: needs a touch button scheme.

- [ ] Make steering/UI mobile-ready
- [ ] Add what's needed for "App installieren" (manifest, 192/512 + maskable icons, apple-touch-icon, theme-color)
- [ ] iPhone hint for adding to the home screen ("Teilen → Zum Home-Bildschirm")
- [ ] Ability to reload when in fullscreen / installed app

### Criss Cross

_mobile candidate._ Unclear: no viewport meta, no touch code found. Needs a phone test.

- [ ] Make steering/UI mobile-ready
- [ ] Add what's needed for "App installieren" (manifest, 192/512 + maskable icons, apple-touch-icon, theme-color)
- [ ] iPhone hint for adding to the home screen ("Teilen → Zum Home-Bildschirm")
- [ ] Ability to reload when in fullscreen / installed app

### Dustline

_mobile candidate._ WASD/arrows helicopter shooter: needs a virtual stick and fire button.

- [ ] Make steering/UI mobile-ready
- [ ] Add what's needed for "App installieren" (manifest, 192/512 + maskable icons, apple-touch-icon, theme-color)
- [ ] iPhone hint for adding to the home screen ("Teilen → Zum Home-Bildschirm")
- [ ] Ability to reload when in fullscreen / installed app

### Geography Quiz

_mobile candidate._ Map pin placing uses mouse events and wheel zoom; needs touch/pinch support.

- [ ] Make steering/UI mobile-ready
- [ ] Add what's needed for "App installieren" (manifest, 192/512 + maskable icons, apple-touch-icon, theme-color)
- [ ] iPhone hint for adding to the home screen ("Teilen → Zum Home-Bildschirm")
- [ ] Ability to reload when in fullscreen / installed app

### Gorillazz

_mobile candidate._ Angle/velocity input via keyboard; needs on-screen number input.

- [ ] Make steering/UI mobile-ready
- [ ] Add what's needed for "App installieren" (manifest, 192/512 + maskable icons, apple-touch-icon, theme-color)
- [ ] iPhone hint for adding to the home screen ("Teilen → Zum Home-Bildschirm")
- [ ] Ability to reload when in fullscreen / installed app

### Huusli Jagd

_mobile candidate._ Click-based board game; dense board UI, check layout.

- [ ] Make steering/UI mobile-ready
- [ ] Add what's needed for "App installieren" (manifest, 192/512 + maskable icons, apple-touch-icon, theme-color)
- [ ] iPhone hint for adding to the home screen ("Teilen → Zum Home-Bildschirm")
- [ ] Ability to reload when in fullscreen / installed app

### Iron Valhalla

_mobile candidate._ Chess; clicking pieces works with taps, the pseudo-3D board needs a size check.

- [ ] Make steering/UI mobile-ready
- [ ] Add what's needed for "App installieren" (manifest, 192/512 + maskable icons, apple-touch-icon, theme-color)
- [ ] iPhone hint for adding to the home screen ("Teilen → Zum Home-Bildschirm")
- [ ] Ability to reload when in fullscreen / installed app

### Marquee Quiz

_mobile candidate._ Click-only quiz; no viewport meta in the outer file. Check layout.

- [ ] Make steering/UI mobile-ready
- [ ] Add what's needed for "App installieren" (manifest, 192/512 + maskable icons, apple-touch-icon, theme-color)
- [ ] iPhone hint for adding to the home screen ("Teilen → Zum Home-Bildschirm")
- [ ] Ability to reload when in fullscreen / installed app

### Millionenfrage

_mobile candidate._ Quiz with answer buttons; steering is clicks only. Check layout.

- [ ] Make steering/UI mobile-ready
- [ ] Add what's needed for "App installieren" (manifest, 192/512 + maskable icons, apple-touch-icon, theme-color)
- [ ] iPhone hint for adding to the home screen ("Teilen → Zum Home-Bildschirm")
- [ ] Ability to reload when in fullscreen / installed app

### Moon Lander

_mobile candidate._ Rotate + thrust only: needs 3 touch buttons.

- [ ] Make steering/UI mobile-ready
- [ ] Add what's needed for "App installieren" (manifest, 192/512 + maskable icons, apple-touch-icon, theme-color)
- [ ] iPhone hint for adding to the home screen ("Teilen → Zum Home-Bildschirm")
- [ ] Ability to reload when in fullscreen / installed app

### Neon Pong

_mobile candidate._ Paddle game; no viewport meta, touch drag to move would be simple.

- [ ] Make steering/UI mobile-ready
- [ ] Add what's needed for "App installieren" (manifest, 192/512 + maskable icons, apple-touch-icon, theme-color)
- [ ] iPhone hint for adding to the home screen ("Teilen → Zum Home-Bildschirm")
- [ ] Ability to reload when in fullscreen / installed app

### Oil Fever 89

_mobile candidate._ Mini-games with arrows or hold-mouse steering; hold-to-steer already maps to touch.

- [ ] Make steering/UI mobile-ready
- [ ] Add what's needed for "App installieren" (manifest, 192/512 + maskable icons, apple-touch-icon, theme-color)
- [ ] iPhone hint for adding to the home screen ("Teilen → Zum Home-Bildschirm")
- [ ] Ability to reload when in fullscreen / installed app

### Photo Puzzler

_mobile candidate._ Click/drag puzzle; no viewport meta in the outer file. Unclear, needs a phone test.

- [ ] Make steering/UI mobile-ready
- [ ] Add what's needed for "App installieren" (manifest, 192/512 + maskable icons, apple-touch-icon, theme-color)
- [ ] iPhone hint for adding to the home screen ("Teilen → Zum Home-Bildschirm")
- [ ] Ability to reload when in fullscreen / installed app

### Rockfall

_mobile candidate._ Grid movement with arrows: needs a d-pad or swipe.

- [ ] Make steering/UI mobile-ready
- [ ] Add what's needed for "App installieren" (manifest, 192/512 + maskable icons, apple-touch-icon, theme-color)
- [ ] iPhone hint for adding to the home screen ("Teilen → Zum Home-Bildschirm")
- [ ] Ability to reload when in fullscreen / installed app

### Space Invaders

_mobile candidate._ Left/right/fire only: needs 3 touch buttons.

- [ ] Make steering/UI mobile-ready
- [ ] Add what's needed for "App installieren" (manifest, 192/512 + maskable icons, apple-touch-icon, theme-color)
- [ ] iPhone hint for adding to the home screen ("Teilen → Zum Home-Bildschirm")
- [ ] Ability to reload when in fullscreen / installed app

### Splashdown

_mobile candidate._ Mouse steering; maps to touch-drag, needs a handler and fullscreen layout.

- [ ] Make steering/UI mobile-ready
- [ ] Add what's needed for "App installieren" (manifest, 192/512 + maskable icons, apple-touch-icon, theme-color)
- [ ] iPhone hint for adding to the home screen ("Teilen → Zum Home-Bildschirm")
- [ ] Ability to reload when in fullscreen / installed app

### Stylestar

_mobile candidate._ Dress-up with clicks/drags; unclear if the wardrobe fits phones, needs a phone test.

- [ ] Make steering/UI mobile-ready
- [ ] Add what's needed for "App installieren" (manifest, 192/512 + maskable icons, apple-touch-icon, theme-color)
- [ ] iPhone hint for adding to the home screen ("Teilen → Zum Home-Bildschirm")
- [ ] Ability to reload when in fullscreen / installed app

### Trip Muncher

_mobile candidate._ 8-way steering: needs a d-pad or swipe.

- [ ] Make steering/UI mobile-ready
- [ ] Add what's needed for "App installieren" (manifest, 192/512 + maskable icons, apple-touch-icon, theme-color)
- [ ] iPhone hint for adding to the home screen ("Teilen → Zum Home-Bildschirm")
- [ ] Ability to reload when in fullscreen / installed app

### Tschau Sepp

_mobile candidate._ Card game with clicks; only audio unlock uses pointer events. Check hand layout.

- [ ] Make steering/UI mobile-ready
- [ ] Add what's needed for "App installieren" (manifest, 192/512 + maskable icons, apple-touch-icon, theme-color)
- [ ] iPhone hint for adding to the home screen ("Teilen → Zum Home-Bildschirm")
- [ ] Ability to reload when in fullscreen / installed app

### Wipfelkratzer

_mobile candidate._ Three.js, `touch-action: none` and pointer events present, but UI built for mouse/keys. Kids game, phone test needed.

- [ ] Make steering/UI mobile-ready
- [ ] Add what's needed for "App installieren" (manifest, 192/512 + maskable icons, apple-touch-icon, theme-color)
- [ ] iPhone hint for adding to the home screen ("Teilen → Zum Home-Bildschirm")
- [ ] Ability to reload when in fullscreen / installed app

### Wortduell

_mobile candidate._ Word board with clicks; letter tray and board need a phone layout check.

- [ ] Make steering/UI mobile-ready
- [ ] Add what's needed for "App installieren" (manifest, 192/512 + maskable icons, apple-touch-icon, theme-color)
- [ ] iPhone hint for adding to the home screen ("Teilen → Zum Home-Bildschirm")
- [ ] Ability to reload when in fullscreen / installed app

### Zen Sudoku

_mobile candidate._ Keyboard entry (1-9, arrows); needs an on-screen number pad.

- [ ] Make steering/UI mobile-ready
- [ ] Add what's needed for "App installieren" (manifest, 192/512 + maskable icons, apple-touch-icon, theme-color)
- [ ] iPhone hint for adding to the home screen ("Teilen → Zum Home-Bildschirm")
- [ ] Ability to reload when in fullscreen / installed app

## Not a candidate

Revisit if a touch scheme is designed.

- Aerodrome Apex: Splash screen says "Keyboard required"; racing with many keys.
- Battleship Toys: Local 2-player on one keyboard (or P2P), many keys.
- Esel Running: Local 2-player on one keyboard.
- Kick Fury: Fighting game with several keys, local 2-player.
- N S Clone: Large strategy/action map UI; unclear, would need a phone test and a redesign.
- Plod: Lemmings-style pixel precision and hotkeys 1-8; unclear, needs a phone test.
- Sky Fury: Many simultaneous keys (pitch, thrust, brake, flip, fire).
- Stack Duel: Two-player Tetris on one keyboard; keyboard-only.
- Tank Toys: Two players on one keyboard, twin-stick style.
- Voxel Sandbox: WASD plus mouse look and block building needs keyboard and mouse.

## Games not on the hub

Local `game-*` repos without a hub card: `game-kontrollgruppe` (no playable code yet, docs only), `game-moki-racer` (viewport meta, keyboard only, no hub card), `game-rechenfuchs` (buildless maths game for tablets, described as PWA; no hub card, not inspected further). `Dogwash` is on the hub but lives in `julia-hase/dogwash`, so it was not inspected.

## How to

Reference implementations:

- **game-barrel-shooter**: mobile bar and orbit pad (`#mob-bar`, `#cam-pad`), reload button `#reload-btn` (⟳) plus `.hint-reload`, `manifest.webmanifest`, `icons/icon-192.png` and `icon-512.png`, `theme-color`.
- **game-rhyflitzer**: touch controls (#535); manifest, icons and reload button (game-rhyflitzer#1076, PR#1079); iPhone home-screen hint game-rhyflitzer#1080.

Platform notes:

- iOS Safari never shows "App installieren". The only route is Share → "Zum Home-Bildschirm" (Add to Home Screen), so the hint has to be in the game itself.
- iOS has no `display: fullscreen`; the installed app falls back to `standalone`. In both modes there is no browser reload button, so the game needs its own (⟳).
- Minimum for installability elsewhere: `manifest.webmanifest` with 192 and 512 icons, one maskable icon, `apple-touch-icon`, `theme-color`, `<meta name="viewport">`.

