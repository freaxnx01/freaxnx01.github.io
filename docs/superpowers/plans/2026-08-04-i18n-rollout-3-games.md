# DE/EN i18n Rollout — wortduell, geography-quiz, nibbles Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Bring `game-wortduell`, `game-geography-quiz`, and `game-nibbles` onto the canonical `i18n.js`/`window.GG_LANG`/`gg-lang` pattern documented in `ai-instructions/.ai/stacks/browser-game.md`.

**Architecture:** wortduell and geography-quiz already have full DE/EN string dictionaries and their own `t()`/`T()` accessors — only the language *state* is rewired from a per-game `state.lang` + per-game localStorage key onto `window.GG_LANG` + the shared `gg-lang` key, mirrored back into `state.lang` on every `gg-langchange` so all their existing string-lookup call sites keep working unchanged. nibbles gets `i18n.js` fresh, plus a new `STRINGS`/`t()` pair and DE translations for its canvas text. All three get `#game-nav`; wortduell and nibbles don't have one yet.

**Tech Stack:** Vanilla JS / DCLogic (React-like runtime via `support.js`), no build tooling in any of the three repos, no test runner — manual browser verification, same as the Iron Valhalla pilot.

## Global Constraints

- Three separate repos, three separate branches/PRs — do not mix commits between them. Clone fresh under `/home/freax/repos/github/freaxnx01/public/`, default branch `main` for all three.
- **wortduell and geography-quiz have no committed `source/*.dc.html`** — only the generated `index.html` exists in git (unlike `game-iron-valhalla`, which has a separate source file). Per user decision, edit `index.html` directly for these two, and say so explicitly in each PR description: *"No source/*.dc.html exists in this repo (unlike the usual dc-tool convention) — this PR edits the generated index.html directly. Reconcile with the real Claude Design source if one exists outside this git checkout."*
- **nibbles' entire document is generated content packed as a JSON-escaped string** inside `<script type="__bundler/template">` — there is no readable source file at all, and this is a different bundler than dc-tool. Never attempt to reverse-engineer or replicate that bundler's own build step. Task 3 below decodes the string to a normal HTML file, edits that, then re-encodes it back into place — the decode/encode round-trip is mechanical (Python's `json` module) and is fully specified in that task, so this isn't guesswork.
- None of the three repos has a test runner. Verification throughout is manual browser playtesting (`python3 -m http.server`), same as Iron Valhalla.
- Every reference to `i18n.js`'s source is the exact version already shipped in `ai-instructions/.ai/stacks/browser-game.md` (Iron Valhalla's version, including the framework-managed-`#game-nav` delegated-click-listener fix) — copy it verbatim, don't re-derive it.

---

### Task 1: Rewire game-wortduell

**Files:**
- Repo: clone fresh — `git clone https://github.com/freaxnx01/game-wortduell.git /home/freax/repos/github/freaxnx01/public/game-wortduell`
- Create: `i18n.js`
- Modify: `index.html`

**Interfaces:**
- Consumes: the canonical `i18n.js` source from `ai-instructions/.ai/stacks/browser-game.md`.
- Produces: none consumed by a later task in this plan.

- [ ] **Step 1: Clone and branch**

```bash
cd /home/freax/repos/github/freaxnx01/public
git clone https://github.com/freaxnx01/game-wortduell.git
cd game-wortduell
git checkout -b feat/de-en-i18n-canonical
```

- [ ] **Step 2: Create `i18n.js`**

Create `i18n.js` at the repo root with the exact source from
`ai-instructions/.ai/stacks/browser-game.md`'s `## Localization (i18n)`
section (the `(function () { "use strict"; ... })();` IIFE — includes the
`document`-level delegated click listener and the framework-managed-nav
comment; copy the whole thing verbatim, it applies here too since this game
is dc-bundled).

- [ ] **Step 3: Load `i18n.js`**

Find:
```html
<script src="./support.js"></script>
</head>
<body>
<script src="./version.js"></script>
```
Replace with:
```html
<script src="./support.js"></script>
</head>
<body>
<script src="./version.js"></script>
<script src="./i18n.js"></script>
```

- [ ] **Step 4: Add `#game-nav`**

Find the closing `</x-dc>` tag (around line 296, right before the
`<script type="text/x-dc" data-dc-script ...>` component script). Insert
this block immediately before it:

```html
<!-- game-nav: copy-paste template. Replace the repo placeholder with the target
     repo name (e.g. game-stack-duel) before pasting into a game's index.html,
     just before </body>. See docs/superpowers/specs/2026-07-13-game-card-feedback-star-design.md
     for design rationale. -->
<nav id="game-nav" aria-label="Game navigation" style="position:fixed;right:10px;bottom:8px;z-index:2147483647;display:flex;gap:12px;align-items:center;font:600 13px/1.4 system-ui,-apple-system,sans-serif;padding:6px 11px;border-radius:8px;background:rgba(15,17,26,.55);backdrop-filter:blur(4px);-webkit-backdrop-filter:blur(4px);opacity:.55;transition:opacity .2s" onmouseover="this.style.opacity=1" onmouseout="this.style.opacity=.55">
  <span id="version-badge" title="Version" style="color:#5a6072"></span>
  <span style="color:#5a6072" aria-hidden="true">·</span>
  <a href="https://github.freaxnx01.ch/games/" style="color:#8fd8e8;text-decoration:none">More Games…</a>
  <span style="color:#5a6072" aria-hidden="true">·</span>
  <a href="https://github.com/freaxnx01/game-wortduell" target="_blank" rel="noopener" style="color:#8fd8e8;text-decoration:none">Source</a>
  <span style="color:#5a6072" aria-hidden="true">·</span>
  <a href="https://github.com/freaxnx01/game-wortduell/issues/new?title=%5BFeedback%5D%20game-wortduell&labels=feedback" target="_blank" rel="noopener" style="color:#8fd8e8;text-decoration:none">Feedback</a>
  <span style="color:#5a6072" aria-hidden="true">·</span>
  <a class="github-button" href="https://github.com/freaxnx01/game-wortduell" data-icon="octicon-star" data-size="small" data-show-count="true" aria-label="Star freaxnx01/game-wortduell on GitHub">Star</a>
</nav>
<script>
  (function () {
    var el = document.getElementById('version-badge');
    if (!el) return;
    var a = document.createElement('a');
    a.href = 'https://github.com/freaxnx01/game-wortduell/blob/main/CHANGELOG.md';
    a.target = '_blank'; a.rel = 'noopener'; a.title = 'Changelog';
    a.textContent = 'v' + (window.GAME_VERSION || '0.0.0');
    a.style.color = 'inherit'; a.style.textDecoration = 'none';
    el.appendChild(a);
  })();
</script>
<script async defer crossorigin="anonymous" src="https://buttons.github.io/buttons.js"></script>
```

- [ ] **Step 5: Rewire `componentDidMount`'s prefs load**

Find:
```javascript
    try {
      const p = JSON.parse(localStorage.getItem('wortduell-prefs') || '{}');
      this.setState({ lang: p.lang || 'de', sound: p.sound !== false, nameP1: p.n1 || '', nameP2: p.n2 || '', diff: p.diff || 'mittel', hasSave: !!localStorage.getItem('wortduell-save') });
    } catch (e) {}
```
Replace with:
```javascript
    try {
      const p = JSON.parse(localStorage.getItem('wortduell-prefs') || '{}');
      this.setState({ lang: window.GG_LANG, sound: p.sound !== false, nameP1: p.n1 || '', nameP2: p.n2 || '', diff: p.diff || 'mittel', hasSave: !!localStorage.getItem('wortduell-save') });
    } catch (e) {}
    window.addEventListener('gg-langchange', () => this.setState({ lang: window.GG_LANG }));
```

- [ ] **Step 6: Rewire `savePrefs`**

Find:
```javascript
  savePrefs(patch) {
    const s = { ...this.state, ...patch };
    try { localStorage.setItem('wortduell-prefs', JSON.stringify({ lang: s.lang, sound: s.sound, n1: s.nameP1, n2: s.nameP2, diff: s.diff })); } catch (e) {}
  }
```
Replace with:
```javascript
  savePrefs(patch) {
    const s = { ...this.state, ...patch };
    try { localStorage.setItem('wortduell-prefs', JSON.stringify({ sound: s.sound, n1: s.nameP1, n2: s.nameP2, diff: s.diff })); } catch (e) {}
  }
```

- [ ] **Step 7: Rewire the in-game language toggle**

Find:
```javascript
      langLabel: s.lang === 'de' ? 'DE → EN' : 'EN → DE',
      onToggleLang: () => { const lang = s.lang === 'de' ? 'en' : 'de'; this.setState({ lang }); this.savePrefs({ lang }); },
```
Replace with:
```javascript
      langLabel: s.lang === 'de' ? 'DE → EN' : 'EN → DE',
      onToggleLang: () => window.ggSetLang(s.lang === 'de' ? 'en' : 'de'),
```

- [ ] **Step 8: Verify in a browser**

```bash
python3 -m http.server 8123 &
```
Open `http://localhost:8123/index.html`. Confirm:
- The `#game-nav` footer appears bottom-right with a version badge, More
  Games/Source/Feedback/Star links, and (from `i18n.js`) an EN/DE toggle.
- The game's own in-game language button (top of the home screen, and the
  smaller one in-game — `{{ langLabel }}` at both call sites) still works,
  and stays in sync with the `#game-nav` toggle: click either one, confirm
  both update and every DE/EN string in the UI switches together.
- Reloading the page after switching to DE keeps DE (persisted via
  `localStorage["gg-lang"]`).
- Start a game, change sound/name/difficulty prefs, reload, confirm those
  still persist correctly (that `wortduell-prefs` no longer carries `lang`
  doesn't break anything else in that blob).

```bash
kill %1
```

- [ ] **Step 9: Commit, push, open a PR**

```bash
git add i18n.js index.html
git commit -m "feat(i18n): rewire onto canonical i18n.js/gg-lang"
git push -u origin feat/de-en-i18n-canonical
gh pr create --title "feat(i18n): rewire onto canonical i18n.js/gg-lang" --body "Rewires this game's existing DE/EN i18n (T/t()/state.lang, wortduell-prefs) onto the canonical i18n.js/window.GG_LANG/gg-lang pattern documented in ai-instructions' browser-game.md (piloted in game-iron-valhalla). Adds the missing #game-nav footer as a prerequisite.

No source/*.dc.html exists in this repo (unlike the usual dc-tool convention) — this PR edits the generated index.html directly. Reconcile with the real Claude Design source if one exists outside this git checkout.

Ref freaxnx01/freaxnx01.github.io#23."
```

---

### Task 2: Rewire game-geography-quiz

**Files:**
- Repo: clone fresh — `git clone https://github.com/freaxnx01/game-geography-quiz.git /home/freax/repos/github/freaxnx01/public/game-geography-quiz`
- Create: `i18n.js`
- Modify: `index.html`

**Interfaces:**
- Consumes: the canonical `i18n.js` source (same as Task 1, Step 2).
- Produces: none consumed by a later task in this plan.

- [ ] **Step 1: Clone and branch**

```bash
cd /home/freax/repos/github/freaxnx01/public
git clone https://github.com/freaxnx01/game-geography-quiz.git
cd game-geography-quiz
git checkout -b feat/de-en-i18n-canonical
```

- [ ] **Step 2: Create `i18n.js`**

Same as Task 1, Step 2 — copy the canonical source verbatim from
`ai-instructions/.ai/stacks/browser-game.md`.

- [ ] **Step 3: Load `i18n.js`**

Find:
```html
<script src="./version.js"></script>
```
(the one near the top of the file, right after `<script src="./support.js"></script>` / `</head><body>` — there is only one `version.js` load in this file). Replace with:
```html
<script src="./version.js"></script>
<script src="./i18n.js"></script>
```

`#game-nav` already exists in this repo — no nav template needed.

- [ ] **Step 4: Rewire the initial state**

Find:
```javascript
  state = {
    lang: localStorage.getItem('terra.lang') || 'en',
```
Replace with:
```javascript
  state = {
    lang: window.GG_LANG,
```

- [ ] **Step 5: Add a `gg-langchange` listener to `componentDidMount`**

Find:
```javascript
  componentDidMount() {
    this._shapeCache = {};
    this._trimCache = {};
    this._cmpCache = { key: '', shapes: [] };
    import(new URL('geo-data.js', document.baseURI).href)
      .then(m => { this.DATA = m; this.setState({ ready: true }); })
      .catch(e => console.error('data load failed', e));
    this._injectLib('https://cdn.jsdelivr.net/npm/d3@7/dist/d3.min.js');
    this._injectLib('https://cdn.jsdelivr.net/npm/topojson-client@3/dist/topojson-client.min.js');
    this.topoPromise = this._loadTopo();
  }
```
Replace with:
```javascript
  componentDidMount() {
    this._shapeCache = {};
    this._trimCache = {};
    this._cmpCache = { key: '', shapes: [] };
    import(new URL('geo-data.js', document.baseURI).href)
      .then(m => { this.DATA = m; this.setState({ ready: true }); })
      .catch(e => console.error('data load failed', e));
    this._injectLib('https://cdn.jsdelivr.net/npm/d3@7/dist/d3.min.js');
    this._injectLib('https://cdn.jsdelivr.net/npm/topojson-client@3/dist/topojson-client.min.js');
    this.topoPromise = this._loadTopo();
    window.addEventListener('gg-langchange', () => { this._cmpCache = { key: '', shapes: [] }; this.setState({ lang: window.GG_LANG }); });
  }
```

- [ ] **Step 6: Rewire `setLang`**

Find:
```javascript
  setLang(l) { localStorage.setItem('terra.lang', l); this.setState({ lang: l }); this._cmpCache = { key: '', shapes: [] }; }
```
Replace with:
```javascript
  setLang(l) { window.ggSetLang(l); }
```

(The cache-clear moved into the `gg-langchange` listener in Step 5, so it
still fires no matter which toggle — the game's own EN/DE buttons or the new
`#game-nav` one — triggered the change.)

- [ ] **Step 7: Verify in a browser**

```bash
python3 -m http.server 8123 &
```
Open `http://localhost:8123/index.html`. Confirm:
- `#game-nav` now shows an EN/DE toggle alongside its existing links.
- The game's own in-game EN/DE buttons (`setEn`/`setDe`) still work and stay
  in sync with the `#game-nav` toggle.
- Quiz content (country/capital names) switches language together with the
  UI chrome — pick a quiz, confirm names shown match the selected language.
- The toggle survives the framework's periodic `#game-nav` re-render — this
  is the exact gotcha `i18n.js`'s delegated click listener exists for
  (confirmed on Iron Valhalla); verify it holds here too rather than
  assuming.
- Reload after switching to DE — confirms `gg-lang` persistence, and that
  `terra.best` (unrelated high-score data, still keyed separately) is
  unaffected.

```bash
kill %1
```

- [ ] **Step 8: Commit, push, open a PR**

```bash
git add i18n.js index.html
git commit -m "feat(i18n): rewire onto canonical i18n.js/gg-lang"
git push -u origin feat/de-en-i18n-canonical
gh pr create --title "feat(i18n): rewire onto canonical i18n.js/gg-lang" --body "Rewires this game's existing DE/EN i18n (I18N/T()/state.lang, terra.lang) onto the canonical i18n.js/window.GG_LANG/gg-lang pattern documented in ai-instructions' browser-game.md (piloted in game-iron-valhalla). Quiz content (country/capital names) moves with the same language setting as the UI chrome.

No source/*.dc.html exists in this repo (unlike the usual dc-tool convention) — this PR edits the generated index.html directly. Reconcile with the real Claude Design source if one exists outside this git checkout.

Ref freaxnx01/freaxnx01.github.io#23."
```

---

### Task 3: Add i18n.js + German translations to game-nibbles

**Files:**
- Repo: clone fresh — `git clone https://github.com/freaxnx01/game-nibbles.git /home/freax/repos/github/freaxnx01/public/game-nibbles`
- Create: `i18n.js`, `version.js`, a scratch decode/encode helper (not committed — see Step 2)
- Modify: `index.html`

**Interfaces:**
- Consumes: the canonical `i18n.js` source (same as Task 1, Step 2).
- Produces: none consumed by a later task in this plan.

nibbles' entire document (including the `class Component extends DCLogic`
game logic) is packed as a JSON-escaped string inside a
`<script type="__bundler/template">` tag — there is no readable source file.
This task decodes that string to a normal HTML file, edits the normal file,
then re-encodes it back into place. The decode/encode step is mechanical
(Python's `json` module handles the escaping correctly) — this is not
guesswork.

- [ ] **Step 1: Clone and branch**

```bash
cd /home/freax/repos/github/freaxnx01/public
git clone https://github.com/freaxnx01/game-nibbles.git
cd game-nibbles
git checkout -b feat/de-en-i18n-canonical
```

- [ ] **Step 2: Decode the bundler template to a readable scratch file**

Run this from the repo root — it extracts the JSON string literal inside
`<script type="__bundler/template">...</script>` and writes the decoded HTML
to `/tmp/nibbles-template.html`:

```bash
python3 - <<'PYEOF'
import re, json

src = open('index.html').read()
m = re.search(r'<script type="__bundler/template">\n(.*)\n  </script>', src, re.S)
if not m:
    raise SystemExit("template script tag not found — check the marker text in index.html")
decoded = json.loads(m.group(1))
open('/tmp/nibbles-template.html', 'w').write(decoded)
print(f"decoded {len(decoded)} chars to /tmp/nibbles-template.html")
PYEOF
```

Verify it worked:
```bash
grep -c "class Component extends DCLogic" /tmp/nibbles-template.html
```
Expected: `1`.

- [ ] **Step 3: Add `#game-nav` and load `i18n.js`/`version.js` in the decoded file**

Edit `/tmp/nibbles-template.html` (a normal, readable HTML file now). Find:
```html
<html><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<script src="bef7c4c8-7a30-4c7a-9e19-358933c5f329"></script>
</head>
<body>
```
Replace with:
```html
<html><head>
<link rel="icon" href="favicon.png" sizes="32x32" type="image/png">
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<script src="bef7c4c8-7a30-4c7a-9e19-358933c5f329"></script>
</head>
<body>
<script src="./version.js"></script>
<script src="./i18n.js"></script>
```

(Leave the `bef7c4c8-...` placeholder script src untouched — it's the
bundler's own internal reference to `support.js`, resolved at whatever step
produced this file; do not try to "fix" it to `./support.js`.)

Find the closing `</x-dc>` tag (search for `<\/x-dc>` in the raw JSON-escaped
file if editing before decoding — but you're editing the decoded file now,
so it's a plain `</x-dc>`) and insert immediately before it:

```html
<nav id="game-nav" aria-label="Game navigation" style="position:fixed;right:10px;bottom:8px;z-index:2147483647;display:flex;gap:12px;align-items:center;font:600 13px/1.4 system-ui,-apple-system,sans-serif;padding:6px 11px;border-radius:8px;background:rgba(15,17,26,.55);backdrop-filter:blur(4px);-webkit-backdrop-filter:blur(4px);opacity:.55;transition:opacity .2s" onmouseover="this.style.opacity=1" onmouseout="this.style.opacity=.55">
  <span id="version-badge" title="Version" style="color:#5a6072"></span>
  <span style="color:#5a6072" aria-hidden="true">·</span>
  <a href="https://github.freaxnx01.ch/games/" style="color:#8fd8e8;text-decoration:none">More Games…</a>
  <span style="color:#5a6072" aria-hidden="true">·</span>
  <a href="https://github.com/freaxnx01/game-nibbles" target="_blank" rel="noopener" style="color:#8fd8e8;text-decoration:none">Source</a>
  <span style="color:#5a6072" aria-hidden="true">·</span>
  <a href="https://github.com/freaxnx01/game-nibbles/issues/new?title=%5BFeedback%5D%20game-nibbles&labels=feedback" target="_blank" rel="noopener" style="color:#8fd8e8;text-decoration:none">Feedback</a>
  <span style="color:#5a6072" aria-hidden="true">·</span>
  <a class="github-button" href="https://github.com/freaxnx01/game-nibbles" data-icon="octicon-star" data-size="small" data-show-count="true" aria-label="Star freaxnx01/game-nibbles on GitHub">Star</a>
</nav>
<script>
  (function () {
    var el = document.getElementById('version-badge');
    if (!el) return;
    var a = document.createElement('a');
    a.href = 'https://github.com/freaxnx01/game-nibbles/blob/main/CHANGELOG.md';
    a.target = '_blank'; a.rel = 'noopener'; a.title = 'Changelog';
    a.textContent = 'v' + (window.GAME_VERSION || '0.0.0');
    a.style.color = 'inherit'; a.style.textDecoration = 'none';
    el.appendChild(a);
  })();
</script>
<script async defer crossorigin="anonymous" src="https://buttons.github.io/buttons.js"></script>
```

- [ ] **Step 4: Add `STRINGS`/`t()` and translate the canvas text**

In `/tmp/nibbles-template.html`, find the `class Component extends DCLogic {`
line and, immediately after the `PALETTES = { ... };` field (right before
`componentDidMount() {`), insert:

```javascript
  STRINGS = {
    en: {
      subtitle1:'STEER YOUR SNAKE TO EACH NUMBER AS IT APPEARS.', subtitle2:'EVERY BITE MAKES YOU LONGER - AVOID WALLS AND TAILS.', subtitle3:'EAT 1 THROUGH 9 TO CLEAR THE FIELD.',
      highScore:'HIGH SCORE  ', pushStart:'PUSH SPACE TO START', modeLine:'1-2 PLAYERS  ·  10 FIELDS  ·  {n} LIVES',
      gameSetup:'GAME SETUP', players:'PLAYERS', onePlayer:'ONE - SAMMY', twoPlayers:'TWO - SAMMY VS JAKE',
      skillLevel:'SKILL LEVEL', speedIncrease:'SPEED INCREASE', on:'ON', off:'OFF', sound:'SOUND',
      setupHelp1:'UP/DOWN SELECT · LEFT/RIGHT CHANGE', setupHelp2:'ENTER START · ESC BACK',
      controls2p:'SAMMY: ARROWS · JAKE: W A S D', controls1p:'STEER WITH THE ARROW KEYS',
      sammy:'SAMMY', jake:'JAKE', level:'LEVEL ', high:'HIGH',
      crashed:' CRASHED!  -1000 PTS', pushSpace:'PUSH SPACE', paused:'PAUSED', pauseHelp:'SPACE RESUME · ESC QUIT',
      gameOver:'GAME OVER', score:'SCORE  ', deadHeat:'DEAD HEAT!', sammyWins:'SAMMY TAKES IT!', jakeWins:'JAKE TAKES IT!',
      newHigh:'NEW HIGH SCORE!', playAgain:'SPACE PLAY AGAIN · ESC MENU',
    },
    de: {
      subtitle1:'STEUERE DEINE SCHLANGE ZU JEDER ERSCHEINENDEN ZAHL.', subtitle2:'JEDER BISSEN MACHT DICH LÄNGER - MEIDE WÄNDE UND SCHWÄNZE.', subtitle3:'ISS 1 BIS 9, UM DAS FELD ZU RÄUMEN.',
      highScore:'HÖCHSTPUNKTZAHL  ', pushStart:'LEERTASTE ZUM START', modeLine:'1-2 SPIELER  ·  10 FELDER  ·  {n} LEBEN',
      gameSetup:'SPIELEINSTELLUNGEN', players:'SPIELER', onePlayer:'EINS - SAMMY', twoPlayers:'ZWEI - SAMMY GEGEN JAKE',
      skillLevel:'SCHWIERIGKEIT', speedIncrease:'TEMPOSTEIGERUNG', on:'AN', off:'AUS', sound:'TON',
      setupHelp1:'HOCH/RUNTER WÄHLEN · LINKS/RECHTS ÄNDERN', setupHelp2:'ENTER START · ESC ZURÜCK',
      controls2p:'SAMMY: PFEILTASTEN · JAKE: W A S D', controls1p:'STEUERE MIT DEN PFEILTASTEN',
      sammy:'SAMMY', jake:'JAKE', level:'LEVEL ', high:'HOCH',
      crashed:' ABGESTÜRZT!  -1000 PKT', pushSpace:'LEERTASTE', paused:'PAUSE', pauseHelp:'LEERTASTE WEITER · ESC BEENDEN',
      gameOver:'SPIEL VORBEI', score:'PUNKTE  ', deadHeat:'UNENTSCHIEDEN!', sammyWins:'SAMMY GEWINNT!', jakeWins:'JAKE GEWINNT!',
      newHigh:'NEUE HÖCHSTPUNKTZAHL!', playAgain:'LEERTASTE NOCHMAL · ESC MENÜ',
    },
  };
  t(key, vars) {
    var s = (this.STRINGS[window.GG_LANG] && this.STRINGS[window.GG_LANG][key]) || this.STRINGS.en[key] || key;
    if (vars) for (var k in vars) s = s.replace('{' + k + '}', vars[k]);
    return s;
  }
```

Find:
```javascript
  componentDidMount() {
    this.settings = this.load('nibbles.settings', { players: 1, skill: 50, speedUp: true, sound: true });
    this.high = this.load('nibbles.high', 0);
    this.buildTitlePath();
    this.onKey = this.onKey.bind(this);
```
Replace with:
```javascript
  componentDidMount() {
    this.settings = this.load('nibbles.settings', { players: 1, skill: 50, speedUp: true, sound: true });
    this.high = this.load('nibbles.high', 0);
    this.buildTitlePath();
    window.addEventListener('gg-langchange', () => {});
    this.onKey = this.onKey.bind(this);
```

(An empty listener is enough here — nibbles redraws every animation frame
via `requestAnimationFrame` regardless of state changes, so `draw()` already
picks up the new `t()` output on the very next frame with no explicit
re-render trigger needed. The listener still needs to exist so
`window.addEventListener` registration doesn't silently rely on undefined
behavior — but it does nothing beyond that.)

Find:
```javascript
    this.txt(x, 'N I B B L E S', 320, 64, C.fg, 64, true);
    x.fillStyle = C.accent; x.fillRect(112, 138, 416, 6);
    this.txt(x, 'STEER YOUR SNAKE TO EACH NUMBER AS IT APPEARS.', 320, 172, C.dim, 16, true);
    this.txt(x, 'EVERY BITE MAKES YOU LONGER - AVOID WALLS AND TAILS.', 320, 192, C.dim, 16, true);
    this.txt(x, 'EAT 1 THROUGH 9 TO CLEAR THE FIELD.', 320, 212, C.dim, 16, true);
    this.txt(x, 'HIGH SCORE  ' + this.pad(this.high), 320, 248, C.accent, 16, true);
    if (((ts / 530) | 0) % 2) this.txt(x, 'PUSH SPACE TO START', 320, 292, C.fg, 24, true);
    const lives = this.props.startingLives ?? 5;
    this.txt(x, '1-2 PLAYERS  ·  10 FIELDS  ·  ' + lives + ' LIVES', 320, 356, C.dim, 16, true);
```
Replace with:
```javascript
    this.txt(x, 'N I B B L E S', 320, 64, C.fg, 64, true);
    x.fillStyle = C.accent; x.fillRect(112, 138, 416, 6);
    this.txt(x, this.t('subtitle1'), 320, 172, C.dim, 16, true);
    this.txt(x, this.t('subtitle2'), 320, 192, C.dim, 16, true);
    this.txt(x, this.t('subtitle3'), 320, 212, C.dim, 16, true);
    this.txt(x, this.t('highScore') + this.pad(this.high), 320, 248, C.accent, 16, true);
    if (((ts / 530) | 0) % 2) this.txt(x, this.t('pushStart'), 320, 292, C.fg, 24, true);
    const lives = this.props.startingLives ?? 5;
    this.txt(x, this.t('modeLine', { n: lives }), 320, 356, C.dim, 16, true);
```

Find:
```javascript
  drawSetup(x, C, ts) {
    const s = this.settings;
    this.txt(x, 'GAME SETUP', 320, 48, C.fg, 32, true);
    const rows = [
      ['PLAYERS', s.players === 1 ? 'ONE - SAMMY' : 'TWO - SAMMY VS JAKE'],
      ['SKILL LEVEL', String(s.skill)],
      ['SPEED INCREASE', s.speedUp ? 'ON' : 'OFF'],
      ['SOUND', s.sound ? 'ON' : 'OFF']
    ];
    rows.forEach((r, i) => {
      const y = 140 + i * 36, sel = i === this.setupSel;
      if (sel) this.txt(x, '»', 132, y, C.accent);
      this.txt(x, r[0], 152, y, sel ? C.fg : C.dim);
      if (sel) this.txt(x, '« ' + r[1] + ' »', 400, y, C.accent);
      else this.txt(x, r[1], 416, y, C.fg);
    });
    this.txt(x, 'UP/DOWN SELECT · LEFT/RIGHT CHANGE', 320, 300, C.dim, 16, true);
    this.txt(x, 'ENTER START · ESC BACK', 320, 322, C.dim, 16, true);
    this.txt(x, s.players === 2 ? 'SAMMY: ARROWS · JAKE: W A S D' : 'STEER WITH THE ARROW KEYS', 320, 356, C.accent, 16, true);
  }
```
Replace with:
```javascript
  drawSetup(x, C, ts) {
    const s = this.settings;
    this.txt(x, this.t('gameSetup'), 320, 48, C.fg, 32, true);
    const rows = [
      [this.t('players'), s.players === 1 ? this.t('onePlayer') : this.t('twoPlayers')],
      [this.t('skillLevel'), String(s.skill)],
      [this.t('speedIncrease'), s.speedUp ? this.t('on') : this.t('off')],
      [this.t('sound'), s.sound ? this.t('on') : this.t('off')]
    ];
    rows.forEach((r, i) => {
      const y = 140 + i * 36, sel = i === this.setupSel;
      if (sel) this.txt(x, '»', 132, y, C.accent);
      this.txt(x, r[0], 152, y, sel ? C.fg : C.dim);
      if (sel) this.txt(x, '« ' + r[1] + ' »', 400, y, C.accent);
      else this.txt(x, r[1], 416, y, C.fg);
    });
    this.txt(x, this.t('setupHelp1'), 320, 300, C.dim, 16, true);
    this.txt(x, this.t('setupHelp2'), 320, 322, C.dim, 16, true);
    this.txt(x, s.players === 2 ? this.t('controls2p') : this.t('controls1p'), 320, 356, C.accent, 16, true);
  }
```

Find:
```javascript
    this.txt(x, 'SAMMY', 8, 0, C.s1);
    this.txt(x, this.pad(p1.score), 56, 0, C.fg);
    x.fillStyle = C.s1;
    for (let i = 0; i < p1.lives; i++) x.fillRect(112 + i * 8, 5, 5, 5);
    this.txt(x, 'LEVEL ' + String(Math.min(99, g.level + 1)).padStart(2, '0'), 320, 0, C.fg, 16, true);
    if (p2) {
      this.txt(x, 'JAKE', 544, 0, C.s2);
      this.txt(x, this.pad(p2.score), 584, 0, C.fg);
      x.fillStyle = C.s2;
      for (let i = 0; i < p2.lives; i++) x.fillRect(528 - i * 8, 5, 5, 5);
    } else {
      this.txt(x, 'HIGH', 544, 0, C.dim);
      this.txt(x, this.pad(Math.max(this.high, p1.score)), 584, 0, C.fg);
    }
```
Replace with:
```javascript
    this.txt(x, this.t('sammy'), 8, 0, C.s1);
    this.txt(x, this.pad(p1.score), 56, 0, C.fg);
    x.fillStyle = C.s1;
    for (let i = 0; i < p1.lives; i++) x.fillRect(112 + i * 8, 5, 5, 5);
    this.txt(x, this.t('level') + String(Math.min(99, g.level + 1)).padStart(2, '0'), 320, 0, C.fg, 16, true);
    if (p2) {
      this.txt(x, this.t('jake'), 544, 0, C.s2);
      this.txt(x, this.pad(p2.score), 584, 0, C.fg);
      x.fillStyle = C.s2;
      for (let i = 0; i < p2.lives; i++) x.fillRect(528 - i * 8, 5, 5, 5);
    } else {
      this.txt(x, this.t('high'), 544, 0, C.dim);
      this.txt(x, this.pad(Math.max(this.high, p1.score)), 584, 0, C.fg);
    }
```

Find:
```javascript
    if (this.mode === 'ready') {
      const L = [];
      if (g.readyMsg) L.push({ t: g.readyMsg, c: C.dlgAccent });
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
      else L.push({ t: 'HIGH SCORE  ' + this.pad(this.high) });
      L.push({ t: 'SPACE PLAY AGAIN · ESC MENU' });
      this.dlg(x, C, L);
    }
```
Replace with:
```javascript
    if (this.mode === 'ready') {
      const L = [];
      if (g.readyMsg) L.push({ t: g.readyMsg, c: C.dlgAccent });
      L.push({ t: this.t('level') + (g.level + 1), size: 32 });
      L.push({ t: this.t('pushSpace'), c: blink ? C.dlgAccent : C.dlgBg });
      this.dlg(x, C, L);
    } else if (this.mode === 'paused') {
      this.dlg(x, C, [{ t: this.t('paused'), size: 32 }, { t: this.t('pauseHelp'), c: C.dlgAccent }]);
    } else if (this.mode === 'gameover') {
      const L = [{ t: this.t('gameOver'), size: 32 }];
      if (p2) {
        L.push({ t: this.t('sammy') + '  ' + this.pad(p1.score) });
        L.push({ t: this.t('jake') + '   ' + this.pad(p2.score) });
        L.push({ t: p1.score === p2.score ? this.t('deadHeat') : (p1.score > p2.score ? this.t('sammyWins') : this.t('jakeWins')), c: C.dlgAccent });
      } else {
        L.push({ t: this.t('score') + this.pad(p1.score) });
      }
      if (g.newHigh) L.push({ t: this.t('newHigh'), c: C.dlgAccent });
      else L.push({ t: this.t('highScore') + this.pad(this.high) });
      L.push({ t: this.t('playAgain') });
      this.dlg(x, C, L);
    }
```

Find:
```javascript
      g.readyMsg = (g.deadNames || []).join(' & ') + ' CRASHED!  -1000 PTS';
```
Replace with:
```javascript
      g.readyMsg = (g.deadNames || []).join(' & ') + this.t('crashed');
```

- [ ] **Step 5: Add `favicon.png`**

Copy the existing `favicon.png` (already at the repo root, per the earlier
`ls` — confirm with `ls favicon.png`) — no action needed, Step 3 already
references `favicon.png` in `<head>` and the file already exists.

- [ ] **Step 6: Add `version.js`**

Create `version.js` at the repo root:

```javascript
window.GAME_VERSION = "0.1.0";
```

(This repo predates the versioning rollout — `0.1.0` matches the baseline
every other game was tagged at. Tag the repo `v0.1.0` in Step 8 to match.)

- [ ] **Step 7: Re-encode the decoded file back into `index.html`**

```bash
python3 - <<'PYEOF'
import re, json

repo_html = open('index.html').read()
new_content = open('/tmp/nibbles-template.html').read()

encoded = json.dumps(new_content).replace('</', '<\\u002F')

new_repo_html = re.sub(
    r'(<script type="__bundler/template">\n).*(\n  </script>)',
    lambda m: m.group(1) + encoded + m.group(2),
    repo_html,
    flags=re.S,
)
open('index.html', 'w').write(new_repo_html)
print("re-encoded", len(encoded), "chars back into index.html")
PYEOF
```

Verify it round-tripped correctly:
```bash
python3 - <<'PYEOF'
import re, json
src = open('index.html').read()
m = re.search(r'<script type="__bundler/template">\n(.*)\n  </script>', src, re.S)
decoded = json.loads(m.group(1))
assert 'STRINGS' in decoded, "STRINGS not found after round-trip"
assert 'game-nav' in decoded, "game-nav not found after round-trip"
print("round-trip OK,", len(decoded), "chars")
PYEOF
```

- [ ] **Step 8: Verify in a browser**

```bash
python3 -m http.server 8123 &
```
Open `http://localhost:8123/index.html`. Confirm:
- The game loads with an empty console (no errors — a JSON round-trip
  mistake would most likely show up as a template-parsing error here).
- `#game-nav` appears bottom-right with a version badge (`v0.1.0`) and an
  EN/DE toggle.
- Click through the title screen, setup screen, and start a game — confirm
  every text element listed in Step 4 appears in English by default.
- Click the toggle: title screen subtitles, setup screen labels and values,
  in-game HUD (SAMMY/JAKE/LEVEL/HIGH), and — trigger a crash and a game
  over — the crash message and game-over dialog all switch to German
  immediately (next animation frame, no reload needed).
- Reload after switching to DE — confirms `gg-lang` persistence.

```bash
kill %1
```

- [ ] **Step 9: Commit, push, open a PR**

```bash
git add i18n.js version.js index.html
git commit -m "feat(i18n): add canonical i18n.js/gg-lang DE/EN support"
git push -u origin feat/de-en-i18n-canonical
gh pr create --title "feat(i18n): add DE/EN support (canonical pattern)" --body "Adds the canonical i18n.js/window.GG_LANG/gg-lang pattern (documented in ai-instructions' browser-game.md, piloted in game-iron-valhalla) to this game, which had zero i18n. Also adds the missing #game-nav footer and version.js (this repo predated both rollouts).

This repo's document is packed as a JSON-escaped string inside a <script type=\"__bundler/template\"> tag — a different bundler than dc-tool, with no readable source file in git at all. This PR was produced by decoding that string, editing the decoded HTML, and re-encoding it back into place (see the implementation plan for the exact script). Reconcile with the real Claude Design source if one exists outside this git checkout.

Ref freaxnx01/freaxnx01.github.io#23."
```

- [ ] **Step 10: Tag the release**

```bash
git tag v0.1.0
git push origin v0.1.0
```

---

### Task 4: Cross-game smoke check

**Files:** none (verification only)

**Interfaces:**
- Consumes: the combined output of Tasks 1–3 (three open PRs).

- [ ] **Step 1: Confirm all three PRs are open and reference issue #23**

```bash
gh pr list --repo freaxnx01/game-wortduell --head feat/de-en-i18n-canonical --json url,title
gh pr list --repo freaxnx01/game-geography-quiz --head feat/de-en-i18n-canonical --json url,title
gh pr list --repo freaxnx01/game-nibbles --head feat/de-en-i18n-canonical --json url,title
```

- [ ] **Step 2: Confirm `gg-lang` is genuinely shared across all three**

With all three games' dev servers stopped (per each task's Step 8/9), start
just `game-iron-valhalla`'s server (already merged, live pattern) on
`localhost:8123`, open it, switch to DE, then — **without clearing browser
storage** — open each of the three new games' `python3 -m http.server`
instances in the same browser. Confirm all four open in DE by default
(same-origin `localhost:8123` in a real browser session shares
`localStorage` across paths only if served from literally the same origin +
port; for a true cross-repo check, this must happen on the actual
`github.freaxnx01.ch/<repo>/` deployment after merge, not on four separate
local `http.server` ports, which do NOT share an origin with each other even
on `localhost` if ports differ — note this caveat in the check itself rather
than reporting a false pass/fail from local-only testing).

No commit needed for this task — it's cross-repo verification.
