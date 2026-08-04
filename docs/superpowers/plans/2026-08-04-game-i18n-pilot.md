# Per-Game i18n Pilot (EN/DE) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Formalize the i18n convention already used by two games and apply/retrofit it across three pilot `game-<name>` repos (`game-wortduell`, `game-geography-quiz`, `game-nibbles`), all defaulting to English.

**Architecture:** Each game repo is a single committed `index.html`, no build step, direct push to its default branch (same convention validated by the favicon rollout, issue #13). `game-wortduell` and `game-geography-quiz` already implement a `T`/`I18N` dictionary + accessor + toggle pattern — those tasks flip the default and audit for stragglers. `game-nibbles` has zero i18n and additionally stores its entire component source as a JSON-escaped string inside a `<script type="__bundler/template">` tag (a no-code-tool bundler artifact) — that task adds a small extract/reembed script so the retrofit happens on readable text, not a 24,000-character single line.

**Tech Stack:** Plain JS (no framework, no build step) in each game repo; Python 3 (stdlib only, no dependencies) for the nibbles template extract/reembed script, run from this hub repo (`freaxnx01.github.io`).

## Global Constraints

- Default language on first visit (no saved preference): always `'en'`, never browser-locale-detected (per issue #14: "default EN").
- Language preference is per-game (each game's own localStorage key), never a shared/site-wide preference.
- `game-wortduell`'s actual gameplay content (the German word dictionary, the words being played) is untouched — only UI chrome (menus, buttons, labels) is translated.
- No new templating engine, no external translation files, no build step — strings live inline in each game's `index.html`, matching the existing `T`/`I18N` object + accessor pattern.
- Interpolation uses `{placeholder}` + `.replace()`, matching `wortduell`'s existing convention — no new templating syntax.
- A missing key in one language's dictionary is a coding mistake to catch by inspection, not a runtime fallback case — no fallback/default-key logic.
- No automated tests — these are static single-file games with no test infrastructure (same precedent as the favicon rollout, issue #13); verification is manual (toggle language, confirm every visible string switches, confirm the choice persists across reload).
- Proper nouns (player character names `SAMMY`/`JAKE` in `game-nibbles`, the `TERRA` brand name in `game-geography-quiz`) are not translated.
- Each game repo's clone lives as a sibling directory of this hub repo, at `/home/freax/repos/github/freaxnx01/public/game-<name>/` (matches the favicon rollout's `clones_root` convention) — this plan assumes those clones already exist and are up to date; if a repo isn't cloned yet, `git clone https://github.com/freaxnx01/game-<name>.git` into that sibling directory first.

---

### Task 1: `game-wortduell` — default to English

**Files:**
- Modify: `/home/freax/repos/github/freaxnx01/public/game-wortduell/index.html:300` (initial state default)
- Modify: `/home/freax/repos/github/freaxnx01/public/game-wortduell/index.html:382` (localStorage-pref fallback default — this is the one that actually takes effect for a fresh visitor, since it runs in `componentDidMount` and overrides the initial state)

**Interfaces:**
- Consumes: nothing from other tasks.
- Produces: nothing other tasks depend on (this is a self-contained, independently verifiable change).

- [ ] **Step 1: Flip the initial state default**

In `game-wortduell/index.html`, find this line (around line 300):

```js
    screen: 'menu', lang: 'de', sound: true, nameP1: '', nameP2: '', diff: 'mittel',
```

Change `lang: 'de'` to `lang: 'en'`:

```js
    screen: 'menu', lang: 'en', sound: true, nameP1: '', nameP2: '', diff: 'mittel',
```

- [ ] **Step 2: Flip the localStorage-fallback default**

Find this line (around line 382):

```js
      this.setState({ lang: p.lang || 'de', sound: p.sound !== false, nameP1: p.n1 || '', nameP2: p.n2 || '', diff: p.diff || 'mittel', hasSave: !!localStorage.getItem('wortduell-save') });
```

Change `p.lang || 'de'` to `p.lang || 'en'`:

```js
      this.setState({ lang: p.lang || 'en', sound: p.sound !== false, nameP1: p.n1 || '', nameP2: p.n2 || '', diff: p.diff || 'mittel', hasSave: !!localStorage.getItem('wortduell-save') });
```

- [ ] **Step 3: Audit for stray hardcoded strings**

```bash
cd /home/freax/repos/github/freaxnx01/public/game-wortduell
awk 'NR<300 || NR>375' index.html | grep -nE '>[A-Za-zÄÖÜäöüß ]{3,50}<' | grep -v 't\.' | grep -v 'langLabel' | grep -v '{{'
```

Expected: no output (every visible DOM string in this file is already routed through `t.` or `langLabel`, confirmed during planning). If this produces any output, it's a real hardcoded string outside the `T` dictionary — add matching `en`/`de` keys to the `T` object (lines ~312-374) and route the markup through `t.yourKey`, matching the existing style. Note in your report exactly what you found and fixed.

- [ ] **Step 4: Verify manually**

```bash
cd /home/freax/repos/github/freaxnx01/public/game-wortduell
python3 -m http.server 8811 &
```

Open `http://localhost:8811/` in a browser (or use a headless fetch/screenshot tool if available). With no `wortduell-prefs` key in localStorage (fresh incognito window, or run `localStorage.clear()` in devtools console first), confirm:
- The subtitle reads "The German crossword duel" (not "Das deutsche Kreuzwort-Duell").
- The language toggle button reads "EN → DE" (not "DE → EN").
- Clicking the toggle switches every visible string to German, and clicking again switches back.
- Reload the page — the last-chosen language persists (this was already working; confirm it still does).

Stop the server:

```bash
kill %1
```

- [ ] **Step 5: Commit**

```bash
cd /home/freax/repos/github/freaxnx01/public/game-wortduell
git add index.html
git commit -m "feat(i18n): default to English (#14)"
git push origin main
```

---

### Task 2: `game-geography-quiz` — confirm already-correct default, audit for stragglers

**Files:**
- Read-only audit: `/home/freax/repos/github/freaxnx01/public/game-geography-quiz/index.html`

**Interfaces:**
- Consumes: nothing from other tasks.
- Produces: nothing other tasks depend on.

This game's default is already `lang: localStorage.getItem('terra.lang') || 'en'` (line 437) — no code change needed for the default itself. This task is a verification-only pass: confirm that's still true and that no UI string bypasses the existing `I18N`/`T()` pattern.

- [ ] **Step 1: Confirm the default in code**

```bash
grep -n "lang: localStorage.getItem" /home/freax/repos/github/freaxnx01/public/game-geography-quiz/index.html
```

Expected output contains: `lang: localStorage.getItem('terra.lang') || 'en',`

If it does NOT say `|| 'en'` (e.g. it says `|| 'de'`), change it to `|| 'en'` and note that as a deviation from this task's expectation in your report — do not silently "fix" an assumption that turned out wrong without flagging it.

- [ ] **Step 2: Audit for stray hardcoded strings**

```bash
cd /home/freax/repos/github/freaxnx01/public/game-geography-quiz
awk 'NR<460 || NR>700' index.html | grep -nE '>[A-Za-z ]{4,50}<' | grep -v 't\.' | grep -v '{{'
```

Expected: only three kinds of matches, all out of scope for this task (do not change them):
- `TERRA` (line ~46) — the brand/logo name, a proper noun.
- `Source` / `Feedback` / `Star` (lines ~1720-1724) — a shared repo-footer credit bar present the same way across other game repos; a cross-cutting concern, not part of this game's i18n.

If the audit turns up any OTHER hardcoded string (a real UI label that isn't already routed through `t.` and isn't one of the three items above), route it through the existing `I18N`/`T()` pattern: add an `en`/`de` entry with the same key name in both `I18N.en` and `I18N.de` (see the object starting at line 460 for the existing style), then replace the hardcoded string with `{{ t.yourKey }}` in the markup. Note in your report exactly what you found and fixed.

- [ ] **Step 3: Verify manually**

```bash
cd /home/freax/repos/github/freaxnx01/public/game-geography-quiz
python3 -m http.server 8812 &
```

Open `http://localhost:8812/`. With `localStorage.clear()` run first (or a fresh incognito window), confirm:
- The page loads in English by default ("How well do you know the world?").
- The EN/DE toggle buttons switch every visible string.
- Reload — the choice persists.

```bash
kill %1
```

- [ ] **Step 4: Commit (only if Step 2 found and fixed something)**

If Step 2 required no code changes, skip this step — there is nothing to commit for this task.

```bash
cd /home/freax/repos/github/freaxnx01/public/game-geography-quiz
git add index.html
git commit -m "feat(i18n): route stray string through existing I18N pattern (#14)"
git push origin main
```

---

### Task 3: `game-nibbles` — template extract/reembed script

**Files:**
- Create: `scripts/nibbles_template_sync.py` (in this hub repo, `freaxnx01.github.io`)

**Interfaces:**
- Produces: a CLI with two subcommands, run from this hub repo's root:
  - `python3 scripts/nibbles_template_sync.py extract <html_path> <out_path>` — writes the unescaped template content to `<out_path>` as plain, readable text.
  - `python3 scripts/nibbles_template_sync.py reembed <html_path> <in_path>` — reads `<in_path>`, re-escapes it, and writes it back into `<html_path>`'s `<script type="__bundler/template">` block.
- Consumed by: Task 4 (the actual i18n retrofit happens on the extracted text file).

`game-nibbles/index.html` stores its entire game as a JSON-encoded string inside `<script type="__bundler/template">...</script>` — a bundler-tool artifact, not something authored by hand. Every `</` sequence inside that string is escaped as `</` (to avoid the browser's HTML parser treating a literal `</script>`, `</div>`, etc. as closing the wrapping `<script>` tag), and non-ASCII characters are kept as literal UTF-8, not `\uXXXX`-escaped. This task writes a small script that extracts that content to a normal, readable file and can write it back byte-identically.

- [ ] **Step 1: Write the script**

```python
#!/usr/bin/env python3
"""Extract/reembed the __bundler/template JSON string in game-nibbles/index.html
so it can be edited as normal, readable text instead of one 24,000-character line.

Usage:
    python3 scripts/nibbles_template_sync.py extract <html_path> <out_path>
    python3 scripts/nibbles_template_sync.py reembed <html_path> <in_path>
"""
import json
import sys
from pathlib import Path

TEMPLATE_OPEN = '<script type="__bundler/template">'
TEMPLATE_CLOSE = '</script>'


def extract(html_path: Path, out_path: Path) -> None:
    html = html_path.read_text()
    start = html.index(TEMPLATE_OPEN) + len(TEMPLATE_OPEN)
    end = html.index(TEMPLATE_CLOSE, start)
    text = json.loads(html[start:end].strip())
    out_path.write_text(text)


def reembed(html_path: Path, in_path: Path) -> None:
    html = html_path.read_text()
    start = html.index(TEMPLATE_OPEN) + len(TEMPLATE_OPEN)
    end = html.index(TEMPLATE_CLOSE, start)
    text = in_path.read_text()
    encoded = json.dumps(text, ensure_ascii=False).replace('</', '<\\u002F')
    html_path.write_text(html[:start] + '\n' + encoded + '\n  ' + html[end:])


def main() -> None:
    if len(sys.argv) != 4 or sys.argv[1] not in ('extract', 'reembed'):
        print(__doc__)
        sys.exit(1)
    mode, html_path, other_path = sys.argv[1], Path(sys.argv[2]), Path(sys.argv[3])
    if mode == 'extract':
        extract(html_path, other_path)
    else:
        reembed(html_path, other_path)


if __name__ == '__main__':
    main()
```

- [ ] **Step 2: Verify the round trip is byte-identical**

Run from this hub repo's root:

```bash
cd /home/freax/repos/github/freaxnx01/public/freaxnx01.github.io
python3 scripts/nibbles_template_sync.py extract \
  /home/freax/repos/github/freaxnx01/public/game-nibbles/index.html \
  /tmp/nibbles_extracted.js
python3 scripts/nibbles_template_sync.py reembed \
  /tmp/nibbles_roundtrip.html \
  /tmp/nibbles_extracted.js
```

Wait — `reembed`'s first argument must be an existing file containing the `<script type="__bundler/template">...</script>` wrapper to fill in, not an output path to create from scratch. Copy the original first, then reembed into the copy, then diff against the original:

```bash
cp /home/freax/repos/github/freaxnx01/public/game-nibbles/index.html /tmp/nibbles_roundtrip.html
python3 scripts/nibbles_template_sync.py reembed /tmp/nibbles_roundtrip.html /tmp/nibbles_extracted.js
diff /home/freax/repos/github/freaxnx01/public/game-nibbles/index.html /tmp/nibbles_roundtrip.html
```

Expected: `diff` produces no output (files are byte-identical). If it produces any output, the script has a bug — do not proceed to Task 4 until this is byte-identical. (This exact approach was verified working during planning: `ensure_ascii=False` is required to keep literal UTF-8 characters like `·` instead of escaping them to `·`, and `</` — not just `</script>` — must be replaced with `</` everywhere, since the original escapes every closing HTML tag inside the string, not just the outer `</script>`.)

Also confirm the extracted file is genuinely readable multi-line JS/HTML, not one long line:

```bash
wc -l /tmp/nibbles_extracted.js
```

Expected: several hundred lines (not 1).

- [ ] **Step 3: Commit**

```bash
cd /home/freax/repos/github/freaxnx01/public/freaxnx01.github.io
git add scripts/nibbles_template_sync.py
git commit -m "feat(i18n): add extract/reembed script for nibbles' bundled template (#14)"
```

---

### Task 4: `game-nibbles` — i18n retrofit

**Files:**
- Modify (via extract → edit → reembed, using Task 3's script): `/home/freax/repos/github/freaxnx01/public/game-nibbles/index.html`

**Interfaces:**
- Consumes: `scripts/nibbles_template_sync.py extract`/`reembed` from Task 3.
- Produces: nothing other tasks depend on.

**The exact English → German string table for this task** (use these exact translations — do not invent your own; "GAME SETUP" e.g. means `setupTitle`, not something else):

| Key | English | German |
|---|---|---|
| `title` | `N I B B L E S` | `N I B B L E S` |
| `instr1` | `STEER YOUR SNAKE TO EACH NUMBER AS IT APPEARS.` | `STEUERE DEINE SCHLANGE ZU JEDER ERSCHEINENDEN ZAHL.` |
| `instr2` | `EVERY BITE MAKES YOU LONGER - AVOID WALLS AND TAILS.` | `JEDER BISSEN MACHT DICH LÄNGER - MEIDE WÄNDE UND SCHWÄNZE.` |
| `instr3` | `EAT 1 THROUGH 9 TO CLEAR THE FIELD.` | `ISS 1 BIS 9, UM DAS FELD ZU RÄUMEN.` |
| `highScore` | `HIGH SCORE` | `REKORD` |
| `pushStart` | `PUSH SPACE TO START` | `LEERTASTE ZUM START DRÜCKEN` |
| `playersFieldsLives` | `1-2 PLAYERS  ·  10 FIELDS  ·  {lives} LIVES` | `1-2 SPIELER · 10 FELDER · {lives} LEBEN` |
| `setupTitle` | `GAME SETUP` | `SPIELEINSTELLUNGEN` |
| `playersLabel` | `PLAYERS` | `SPIELER` |
| `skillLevel` | `SKILL LEVEL` | `SCHWIERIGKEIT` |
| `speedIncrease` | `SPEED INCREASE` | `TEMPOSTEIGERUNG` |
| `soundLabel` | `SOUND` | `TON` |
| `onePlayer` | `ONE - SAMMY` | `EINER - SAMMY` |
| `twoPlayers` | `TWO - SAMMY VS JAKE` | `ZWEI - SAMMY GEGEN JAKE` |
| `on` | `ON` | `AN` |
| `off` | `OFF` | `AUS` |
| `setupHelp1` | `UP/DOWN SELECT · LEFT/RIGHT CHANGE` | `HOCH/RUNTER WÄHLEN · LINKS/RECHTS ÄNDERN` |
| `setupHelp2` | `ENTER START · ESC BACK` | `ENTER START · ESC ZURÜCK` |
| `controlsTwo` | `SAMMY: ARROWS · JAKE: W A S D` | `SAMMY: PFEILTASTEN · JAKE: W A S D` |
| `controlsOne` | `STEER WITH THE ARROW KEYS` | `STEUERE MIT DEN PFEILTASTEN` |
| `level` | `LEVEL {n}` | `LEVEL {n}` |
| `highLabel` | `HIGH` | `BEST` |
| `crashed` | `{names} CRASHED!  -1000 PTS` | `{names} GECRASHT!  -1000 PKT` |
| `pausedLabel` | `PAUSED` | `PAUSE` |
| `pausedHelp` | `SPACE RESUME · ESC QUIT` | `LEERTASTE WEITER · ESC BEENDEN` |
| `gameOver` | `GAME OVER` | `SPIEL VORBEI` |
| `deadHeat` | `DEAD HEAT!` | `UNENTSCHIEDEN!` |
| `sammyWins` | `SAMMY TAKES IT!` | `SAMMY GEWINNT!` |
| `jakeWins` | `JAKE TAKES IT!` | `JAKE GEWINNT!` |
| `scoreLabel` | `SCORE  {score}` | `PUNKTE  {score}` |
| `newHighScore` | `NEW HIGH SCORE!` | `NEUER REKORD!` |
| `gameOverHelp` | `SPACE PLAY AGAIN · ESC MENU` | `LEERTASTE NOCHMAL · ESC MENÜ` |
| `controlsHint1` (static DOM text below canvas) | `ARROWS - SAMMY  ·  W A S D - JAKE  ·  SPACE - CONFIRM` | `PFEILE - SAMMY · W A S D - JAKE · LEERTASTE - BESTÄTIGEN` |
| `controlsHint2` (static DOM text below canvas) | `P - PAUSE  ·  M - SOUND  ·  ESC - MENU  ·  TOUCH: SWIPE + TAP` | `P - PAUSE · M - TON · ESC - MENÜ · TOUCH: WISCHEN + TIPPEN` |
| `langToggle` (new toggle button label) | `DE` (button shows the language you'd switch TO) | `EN` |

Player names `SAMMY`/`JAKE` are proper nouns (per Global Constraints) and are NOT in this table — every literal `'SAMMY'`/`'JAKE'` string in the code that identifies a player (not display copy) stays exactly as-is.

- [ ] **Step 1: Extract the template to a readable file**

```bash
cd /home/freax/repos/github/freaxnx01/public/freaxnx01.github.io
python3 scripts/nibbles_template_sync.py extract \
  /home/freax/repos/github/freaxnx01/public/game-nibbles/index.html \
  /tmp/nibbles_work.js
```

All remaining steps in this task edit `/tmp/nibbles_work.js` as normal, readable JS/HTML.

- [ ] **Step 2: Add the `T` dictionary, `state.lang`, and `t()` accessor**

In `/tmp/nibbles_work.js`, find the `PALETTES` object (it ends with `};` right before `componentDidMount()`). Add the following immediately after that `};`, before `componentDidMount()`:

```js
  T = {
    en: {
      title: 'N I B B L E S',
      instr1: 'STEER YOUR SNAKE TO EACH NUMBER AS IT APPEARS.',
      instr2: 'EVERY BITE MAKES YOU LONGER - AVOID WALLS AND TAILS.',
      instr3: 'EAT 1 THROUGH 9 TO CLEAR THE FIELD.',
      highScore: 'HIGH SCORE', pushStart: 'PUSH SPACE TO START',
      playersFieldsLives: '1-2 PLAYERS  ·  10 FIELDS  ·  {lives} LIVES',
      setupTitle: 'GAME SETUP', playersLabel: 'PLAYERS', skillLevel: 'SKILL LEVEL',
      speedIncrease: 'SPEED INCREASE', soundLabel: 'SOUND',
      onePlayer: 'ONE - SAMMY', twoPlayers: 'TWO - SAMMY VS JAKE', on: 'ON', off: 'OFF',
      setupHelp1: 'UP/DOWN SELECT · LEFT/RIGHT CHANGE', setupHelp2: 'ENTER START · ESC BACK',
      controlsTwo: 'SAMMY: ARROWS · JAKE: W A S D', controlsOne: 'STEER WITH THE ARROW KEYS',
      level: 'LEVEL {n}', highLabel: 'HIGH', crashed: '{names} CRASHED!  -1000 PTS',
      pausedLabel: 'PAUSED', pausedHelp: 'SPACE RESUME · ESC QUIT', gameOver: 'GAME OVER',
      deadHeat: 'DEAD HEAT!', sammyWins: 'SAMMY TAKES IT!', jakeWins: 'JAKE TAKES IT!',
      scoreLabel: 'SCORE  {score}', newHighScore: 'NEW HIGH SCORE!',
      gameOverHelp: 'SPACE PLAY AGAIN · ESC MENU',
      controlsHint1: 'ARROWS - SAMMY  ·  W A S D - JAKE  ·  SPACE - CONFIRM',
      controlsHint2: 'P - PAUSE  ·  M - SOUND  ·  ESC - MENU  ·  TOUCH: SWIPE + TAP',
      langToggle: 'DE'
    },
    de: {
      title: 'N I B B L E S',
      instr1: 'STEUERE DEINE SCHLANGE ZU JEDER ERSCHEINENDEN ZAHL.',
      instr2: 'JEDER BISSEN MACHT DICH LÄNGER - MEIDE WÄNDE UND SCHWÄNZE.',
      instr3: 'ISS 1 BIS 9, UM DAS FELD ZU RÄUMEN.',
      highScore: 'REKORD', pushStart: 'LEERTASTE ZUM START DRÜCKEN',
      playersFieldsLives: '1-2 SPIELER · 10 FELDER · {lives} LEBEN',
      setupTitle: 'SPIELEINSTELLUNGEN', playersLabel: 'SPIELER', skillLevel: 'SCHWIERIGKEIT',
      speedIncrease: 'TEMPOSTEIGERUNG', soundLabel: 'TON',
      onePlayer: 'EINER - SAMMY', twoPlayers: 'ZWEI - SAMMY GEGEN JAKE', on: 'AN', off: 'AUS',
      setupHelp1: 'HOCH/RUNTER WÄHLEN · LINKS/RECHTS ÄNDERN', setupHelp2: 'ENTER START · ESC ZURÜCK',
      controlsTwo: 'SAMMY: PFEILTASTEN · JAKE: W A S D', controlsOne: 'STEUERE MIT DEN PFEILTASTEN',
      level: 'LEVEL {n}', highLabel: 'BEST', crashed: '{names} GECRASHT!  -1000 PKT',
      pausedLabel: 'PAUSE', pausedHelp: 'LEERTASTE WEITER · ESC BEENDEN', gameOver: 'SPIEL VORBEI',
      deadHeat: 'UNENTSCHIEDEN!', sammyWins: 'SAMMY GEWINNT!', jakeWins: 'JAKE GEWINNT!',
      scoreLabel: 'PUNKTE  {score}', newHighScore: 'NEUER REKORD!',
      gameOverHelp: 'LEERTASTE NOCHMAL · ESC MENÜ',
      controlsHint1: 'PFEILE - SAMMY · W A S D - JAKE · LEERTASTE - BESTÄTIGEN',
      controlsHint2: 'P - PAUSE · M - TON · ESC - MENÜ · TOUCH: WISCHEN + TIPPEN',
      langToggle: 'EN'
    }
  };
  fmt(s, map) { let o = s; for (const k in map) o = o.split('{' + k + '}').join(map[k]); return o; }
  t() { return this.T[this.lang]; }
```

Note: `this.lang` (not `this.state.lang`) — this component's existing `mode`/`setupSel`/`fontReady` fields are plain instance properties, not React-style `state`, so `lang` follows the same convention for consistency with the rest of this file.

- [ ] **Step 3: Initialize and persist `lang` alongside the existing settings**

Find `componentDidMount()`'s first line:

```js
    this.settings = this.load('nibbles.settings', { players: 1, skill: 50, speedUp: true, sound: true });
```

Change it to also load `lang`, defaulting to `'en'`:

```js
    this.settings = this.load('nibbles.settings', { players: 1, skill: 50, speedUp: true, sound: true, lang: 'en' });
    this.lang = this.settings.lang || 'en';
```

Find `toggleSound()`:

```js
  toggleSound() {
    this.settings.sound = !this.settings.sound;
    this.save('nibbles.settings', this.settings);
    this.ensureAC(); this.sBlip();
  }
```

Add a matching `toggleLang()` right after it:

```js
  toggleLang() {
    this.lang = this.lang === 'en' ? 'de' : 'en';
    this.settings.lang = this.lang;
    this.save('nibbles.settings', this.settings);
    this.ensureAC(); this.sBlip();
  }
```

- [ ] **Step 4: Add the DOM toggle button and keyboard shortcut**

Find the static instruction markup (the two `<div>` lines below the canvas, inside the outer wrapper `<div style="text-align:center;...">`):

```html
  <div style="text-align:center;color:#585866;font-size:clamp(14px, 1.5vw, 19px);letter-spacing:0.14em;line-height:1.6;">
    <div>ARROWS - SAMMY &nbsp;·&nbsp; W A S D - JAKE &nbsp;·&nbsp; SPACE - CONFIRM</div>
    <div>P - PAUSE &nbsp;·&nbsp; M - SOUND &nbsp;·&nbsp; ESC - MENU &nbsp;·&nbsp; TOUCH: SWIPE + TAP</div>
  </div>
```

Replace it with a version that uses `{{ }}` interpolation for the two lines (routed through `t()` via `renderVals()` — see next step) and adds a toggle button:

```html
  <div style="text-align:center;color:#585866;font-size:clamp(14px, 1.5vw, 19px);letter-spacing:0.14em;line-height:1.6;">
    <div>{{ controlsHint1 }}</div>
    <div>{{ controlsHint2 }}</div>
  </div>
  <button onClick="{{ onToggleLang }}" style="background:#1c1c24;border:1px solid #33333d;border-radius:8px;color:#9f9fe8;padding:8px 16px;font:inherit;font-size:14px;letter-spacing:0.1em;cursor:pointer;">{{ langToggleLabel }}</button>
```

Find `renderVals()`:

```js
  renderVals() {
    return { canvasRef: this.canvasRef, crtOn: this.props.crt ?? true };
  }
```

Change it to also expose the two hint strings and the toggle button's label/handler:

```js
  renderVals() {
    return {
      canvasRef: this.canvasRef, crtOn: this.props.crt ?? true,
      controlsHint1: this.t().controlsHint1, controlsHint2: this.t().controlsHint2,
      langToggleLabel: this.t().langToggle, onToggleLang: () => this.toggleLang()
    };
  }
```

Find `onKey(e)`'s early lines:

```js
  onKey(e) {
    const k = e.key;
    if (k.startsWith('Arrow') || k === ' ') e.preventDefault();
    if ((k === 'm' || k === 'M') && !e.repeat && this.mode !== 'play') { this.toggleSound(); return; }
```

Add an `L`/`l` shortcut right after the sound-toggle line, with the same "not while playing" guard:

```js
  onKey(e) {
    const k = e.key;
    if (k.startsWith('Arrow') || k === ' ') e.preventDefault();
    if ((k === 'm' || k === 'M') && !e.repeat && this.mode !== 'play') { this.toggleSound(); return; }
    if ((k === 'l' || k === 'L') && !e.repeat && this.mode !== 'play') { this.toggleLang(); return; }
```

- [ ] **Step 5: Route every canvas-drawn string through `t()`**

Replace each of these exact lines in `drawTitle`, `drawSetup`, and `drawGame` (find-and-replace, one at a time, matching the existing surrounding code exactly):

```js
    this.txt(x, 'N I B B L E S', 320, 64, C.fg, 64, true);
```
→
```js
    this.txt(x, this.t().title, 320, 64, C.fg, 64, true);
```

```js
    this.txt(x, 'STEER YOUR SNAKE TO EACH NUMBER AS IT APPEARS.', 320, 172, C.dim, 16, true);
    this.txt(x, 'EVERY BITE MAKES YOU LONGER - AVOID WALLS AND TAILS.', 320, 192, C.dim, 16, true);
    this.txt(x, 'EAT 1 THROUGH 9 TO CLEAR THE FIELD.', 320, 212, C.dim, 16, true);
    this.txt(x, 'HIGH SCORE  ' + this.pad(this.high), 320, 248, C.accent, 16, true);
    if (((ts / 530) | 0) % 2) this.txt(x, 'PUSH SPACE TO START', 320, 292, C.fg, 24, true);
```
→
```js
    this.txt(x, this.t().instr1, 320, 172, C.dim, 16, true);
    this.txt(x, this.t().instr2, 320, 192, C.dim, 16, true);
    this.txt(x, this.t().instr3, 320, 212, C.dim, 16, true);
    this.txt(x, this.t().highScore + '  ' + this.pad(this.high), 320, 248, C.accent, 16, true);
    if (((ts / 530) | 0) % 2) this.txt(x, this.t().pushStart, 320, 292, C.fg, 24, true);
```

```js
    this.txt(x, '1-2 PLAYERS  ·  10 FIELDS  ·  ' + lives + ' LIVES', 320, 356, C.dim, 16, true);
```
→
```js
    this.txt(x, this.fmt(this.t().playersFieldsLives, { lives }), 320, 356, C.dim, 16, true);
```

```js
    this.txt(x, 'GAME SETUP', 320, 48, C.fg, 32, true);
    const rows = [
      ['PLAYERS', s.players === 1 ? 'ONE - SAMMY' : 'TWO - SAMMY VS JAKE'],
      ['SKILL LEVEL', String(s.skill)],
      ['SPEED INCREASE', s.speedUp ? 'ON' : 'OFF'],
      ['SOUND', s.sound ? 'ON' : 'OFF']
    ];
```
→
```js
    this.txt(x, this.t().setupTitle, 320, 48, C.fg, 32, true);
    const rows = [
      [this.t().playersLabel, s.players === 1 ? this.t().onePlayer : this.t().twoPlayers],
      [this.t().skillLevel, String(s.skill)],
      [this.t().speedIncrease, s.speedUp ? this.t().on : this.t().off],
      [this.t().soundLabel, s.sound ? this.t().on : this.t().off]
    ];
```

```js
    this.txt(x, 'UP/DOWN SELECT · LEFT/RIGHT CHANGE', 320, 300, C.dim, 16, true);
    this.txt(x, 'ENTER START · ESC BACK', 320, 322, C.dim, 16, true);
    this.txt(x, s.players === 2 ? 'SAMMY: ARROWS · JAKE: W A S D' : 'STEER WITH THE ARROW KEYS', 320, 356, C.accent, 16, true);
```
→
```js
    this.txt(x, this.t().setupHelp1, 320, 300, C.dim, 16, true);
    this.txt(x, this.t().setupHelp2, 320, 322, C.dim, 16, true);
    this.txt(x, s.players === 2 ? this.t().controlsTwo : this.t().controlsOne, 320, 356, C.accent, 16, true);
```

```js
    this.txt(x, 'LEVEL ' + String(Math.min(99, g.level + 1)).padStart(2, '0'), 320, 0, C.fg, 16, true);
```
→
```js
    this.txt(x, this.fmt(this.t().level, { n: String(Math.min(99, g.level + 1)).padStart(2, '0') }), 320, 0, C.fg, 16, true);
```

```js
      this.txt(x, 'HIGH', 544, 0, C.dim);
```
→
```js
      this.txt(x, this.t().highLabel, 544, 0, C.dim);
```

```js
      g.readyMsg = (g.deadNames || []).join(' & ') + ' CRASHED!  -1000 PTS';
```
→
```js
      g.readyMsg = this.fmt(this.t().crashed, { names: (g.deadNames || []).join(' & ') });
```

```js
      L.push({ t: 'LEVEL ' + (g.level + 1), size: 32 });
      L.push({ t: 'PUSH SPACE', c: blink ? C.dlgAccent : C.dlgBg });
      this.dlg(x, C, L);
    } else if (this.mode === 'paused') {
      this.dlg(x, C, [{ t: 'PAUSED', size: 32 }, { t: 'SPACE RESUME · ESC QUIT', c: C.dlgAccent }]);
    } else if (this.mode === 'gameover') {
      const L = [{ t: 'GAME OVER', size: 32 }];
      if (p2) {
        L.push({ t: 'SAMMY  ' + this.pad(p1.score) });
        L.push({ t: 'JAKE   ' + this.pad(p2.score) });
        L.push({ t: p1.score === p2.score ? 'DEAD HEAT!' : (p1.score > p2.score ? 'SAMMY TAKES IT!' : 'JAKE TAKES IT!'), c: C.dlgAccent });
      } else {
        L.push({ t: 'SCORE  ' + this.pad(p1.score) });
      }
      if (g.newHigh) L.push({ t: 'NEW HIGH SCORE!', c: C.dlgAccent });
      else L.push({ t: 'HIGH SCORE  ' + this.pad(this.high), c: C.dlgAccent });
      L.push({ t: 'SPACE PLAY AGAIN · ESC MENU' });
      this.dlg(x, C, L);
```
→
```js
      L.push({ t: this.fmt(this.t().level, { n: g.level + 1 }), size: 32 });
      L.push({ t: this.t().pushStart.replace(' TO START', ''), c: blink ? C.dlgAccent : C.dlgBg });
      this.dlg(x, C, L);
    } else if (this.mode === 'paused') {
      this.dlg(x, C, [{ t: this.t().pausedLabel, size: 32 }, { t: this.t().pausedHelp, c: C.dlgAccent }]);
    } else if (this.mode === 'gameover') {
      const L = [{ t: this.t().gameOver, size: 32 }];
      if (p2) {
        L.push({ t: 'SAMMY  ' + this.pad(p1.score) });
        L.push({ t: 'JAKE   ' + this.pad(p2.score) });
        L.push({ t: p1.score === p2.score ? this.t().deadHeat : (p1.score > p2.score ? this.t().sammyWins : this.t().jakeWins), c: C.dlgAccent });
      } else {
        L.push({ t: this.fmt(this.t().scoreLabel, { score: this.pad(p1.score) }) });
      }
      if (g.newHigh) L.push({ t: this.t().newHighScore, c: C.dlgAccent });
      else L.push({ t: this.t().highScore + '  ' + this.pad(this.high), c: C.dlgAccent });
      L.push({ t: this.t().gameOverHelp });
      this.dlg(x, C, L);
```

Note: the `'PUSH SPACE'` short dialog prompt reuses `pushStart` with `' TO START'` stripped off rather than adding a fourth near-duplicate key — this keeps the string table from Task 4's header in sync with what's actually used. `'SAMMY  ' + this.pad(...)` / `'JAKE   ' + this.pad(...)` keep the literal player names (proper nouns, per Global Constraints) with their original score-line spacing unchanged.

- [ ] **Step 6: Write the extracted file back and validate**

```bash
cd /home/freax/repos/github/freaxnx01/public/freaxnx01.github.io
python3 scripts/nibbles_template_sync.py reembed \
  /home/freax/repos/github/freaxnx01/public/game-nibbles/index.html \
  /tmp/nibbles_work.js
```

Validate the file is still well-formed (the reembed script would already have thrown a `ValueError` from `json.dumps` on truly broken input, but confirm the whole file still parses as valid HTML-ish structure and the JSON round-trips):

```bash
python3 -c "
import json
html = open('/home/freax/repos/github/freaxnx01/public/game-nibbles/index.html').read()
start = html.index('<script type=\"__bundler/template\">') + len('<script type=\"__bundler/template\">')
end = html.index('</script>', start)
text = json.loads(html[start:end].strip())
assert 'class Component extends DCLogic' in text
assert \"this.t().title\" in text
print('OK, template still valid JSON,', len(text), 'chars')
"
```

Expected: `OK, template still valid JSON, <some number> chars` with no error.

- [ ] **Step 7: Verify manually in a browser**

```bash
cd /home/freax/repos/github/freaxnx01/public/game-nibbles
python3 -m http.server 8813 &
```

Open `http://localhost:8813/`. With `localStorage.clear()` run first (fresh state):
- Confirm the title screen shows the English instructions ("STEER YOUR SNAKE...", "PUSH SPACE TO START", etc.).
- Click the new toggle button — confirm every visible string (title screen, setup screen, in-game HUD, pause dialog, game-over dialog) switches to German. Play a short game (at least reach the setup screen and start a game) to see the in-game HUD and confirm `SAMMY`/`JAKE` names are unchanged in both languages.
- Press `L` on the title or setup screen — confirm it also toggles language (and does nothing while `mode === 'play'`, matching the `M` sound-toggle's existing behavior).
- Reload the page — confirm the last-chosen language persists (it's saved into `nibbles.settings` alongside the other settings).

```bash
kill %1
```

- [ ] **Step 8: Commit**

```bash
cd /home/freax/repos/github/freaxnx01/public/game-nibbles
git add index.html
git commit -m "feat(i18n): add EN/DE support, default English (#14)"
git push origin main
```

---

### Task 5: Wrap-up verification across all three pilot games

**Files:**
- None (no code changes — this task is a final cross-game sanity pass).

**Interfaces:**
- Consumes: the completed state of Tasks 1, 2, and 4.

- [ ] **Step 1: Re-verify each pilot game live (post-push)**

```bash
curl -s https://raw.githubusercontent.com/freaxnx01/game-wortduell/main/index.html | grep -c "lang: 'en'"
curl -s https://raw.githubusercontent.com/freaxnx01/game-nibbles/main/index.html | grep -o "this.t().title" | head -1
```

Expected: the first command reports at least `1`; the second prints `this.t().title` (confirms the pushed `index.html` contains the retrofit, not a stale cached copy).

- [ ] **Step 2: Open each live game in a browser**

Visit `https://github.freaxnx01.ch/game-wortduell/`, `https://github.freaxnx01.ch/game-geography-quiz/`, and `https://github.freaxnx01.ch/game-nibbles/`. For each, confirm the page loads in English by default and the language toggle works, exactly as verified locally in each task.

- [ ] **Step 3: Report**

No further action needed if all three pilots verify cleanly. This plan's scope ends here — rolling the same convention out to the remaining ~34 games is separate, tracked backlog work (per the design spec's Rollout section).
