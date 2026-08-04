# DE/EN i18n Pattern + Iron Valhalla Pilot Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the loose i18n guidance already in `ai-instructions/.ai/stacks/browser-game.md` into a concrete, copy-pasteable pattern, and prove it works end-to-end on one pilot game, `game-iron-valhalla`.

**Architecture:** A self-contained `i18n.js` (documented in `browser-game.md`, copied file-for-file into the pilot repo) exposes `window.GG_LANG`, `window.ggSetLang(lang)`, and a `gg-langchange` event, and injects an EN/DE toggle into the game's existing `#game-nav` footer. Each game keeps its own `STRINGS`/`t()` and calls `t()` wherever it currently has literal English UI text.

**Tech Stack:** Vanilla JS, no build tooling, no test runner in either repo (docs repo + buildless static-site game repo). Verification is manual: read-through for the docs change, browser playtest for the pilot.

## Global Constraints

- Two separate repos, two separate branches/PRs — do not mix commits between them:
  - `ai-instructions` — local checkout: `/home/freax/repos/github/freaxnx01/public/ai-instructions`, default branch `main`.
  - `game-iron-valhalla` — not checked out locally yet; clone fresh (see Task 2, Step 1).
- `game-iron-valhalla` is dc-bundled: `source/Iron Valhalla Battlechess v2.dc.html` is the file to edit; `index.html` / `support.js` are generated and must never be hand-edited for *logic* changes — except the two additions already established as manual, direct edits to the generated `index.html` in this repo: the `<script src="./version.js">` tag and the `#game-nav` footer block (neither appears in `source/`, confirming this repo's convention is to hand-add nav/head chrome to the generated file). The new `<script src="./i18n.js">` tag and the language-toggle button follow that same established exception — Task 2 edits `index.html` directly for those two pieces. Everything that touches actual game rendering (`STRINGS`, `t()`, the `gg-langchange` listener, replacing literal English strings) is genuine component logic and MUST go in `source/Iron Valhalla Battlechess v2.dc.html`, then be re-bundled (Task 3).
- The re-bundle command/tool for `game-iron-valhalla` is not known yet — Task 3, Step 1 has the implementer find it (check `AGENT-NOTES.md` at the repo root, or ask the user) before touching the source file.
- Rollout to the other 37 `game-*` repos is explicitly out of scope for this plan.

---

### Task 1: Document the concrete i18n pattern in `ai-instructions`

**Files:**
- Repo: `/home/freax/repos/github/freaxnx01/public/ai-instructions`
- Modify: `.ai/stacks/browser-game.md` (replace the existing `## Localization (i18n)` section)

**Interfaces:**
- Produces: the canonical `i18n.js` source (below) that Task 2 copies verbatim into `game-iron-valhalla`, and the `window.GG_LANG` / `window.ggSetLang(lang)` / `gg-langchange` / `STRINGS` / `t(key)` API names that Tasks 2–3 implement against.

- [ ] **Step 1: Create a fresh branch**

```bash
cd /home/freax/repos/github/freaxnx01/public/ai-instructions
git fetch origin
git checkout -b docs/browser-game-i18n-pattern origin/main
```

- [ ] **Step 2: Replace the Localization section**

Find this exact block in `.ai/stacks/browser-game.md`:

```markdown
## Localization (i18n)

Base's `de`/`en` rule applies to games with meaningful UI text (menus, HUD
copy, quiz questions). Lightweight vanilla pattern:

- A `strings` object keyed by locale (`{ en: {...}, de: {...} }`)
- Detect the initial language from `navigator.language`
- Provide a switcher; persist the choice in `localStorage`

**Carve-out:** pure-arcade games with negligible on-screen text (a score and a
"GAME OVER") may defer i18n. Text-heavy games (quizzes, dialog-driven games)
must comply.
```

Replace it with:

```markdown
## Localization (i18n)

Base's `de`/`en` rule applies to games with meaningful UI text (menus, HUD
copy, quiz questions).

**Carve-out:** pure-arcade games with negligible on-screen text (a score and a
"GAME OVER") may defer i18n. Text-heavy games (quizzes, dialog-driven games)
must comply.

### `i18n.js` (copy verbatim into the game repo)

Every `game-*` repo is served under the same `github.freaxnx01.ch` origin
(different path per repo), so `localStorage` is shared across all of them —
one `gg-lang` key means picking a language once carries into every other
game. `i18n.js` loads like `version.js` (classic script, before the game's
own script) and owns detection, persistence, and the toggle button; it knows
nothing about any individual game's strings.

```javascript
(function () {
  "use strict";

  var SUPPORTED = ["en", "de"];
  var STORAGE_KEY = "gg-lang";

  function detect() {
    var stored = null;
    try { stored = localStorage.getItem(STORAGE_KEY); } catch (e) {}
    if (stored && SUPPORTED.indexOf(stored) !== -1) return stored;
    var nav = (navigator.language || "en").toLowerCase();
    return nav.indexOf("de") === 0 ? "de" : "en";
  }

  window.GG_LANG = detect();

  window.ggSetLang = function (lang) {
    if (SUPPORTED.indexOf(lang) === -1) return;
    window.GG_LANG = lang;
    try { localStorage.setItem(STORAGE_KEY, lang); } catch (e) {}
    window.dispatchEvent(new CustomEvent("gg-langchange", { detail: { lang: lang } }));
  };

  function injectToggle() {
    var nav = document.getElementById("game-nav");
    if (!nav || document.getElementById("gg-lang-toggle")) return;

    var sep = document.createElement("span");
    sep.setAttribute("aria-hidden", "true");
    sep.style.color = "#5a6072";
    sep.textContent = "·";

    var btn = document.createElement("button");
    btn.id = "gg-lang-toggle";
    btn.type = "button";
    btn.title = "Switch language";
    btn.style.cssText =
      "background:none;border:none;padding:0;margin:0;font:inherit;color:#8fd8e8;cursor:pointer";
    btn.textContent = window.GG_LANG.toUpperCase();

    btn.addEventListener("click", function () {
      window.ggSetLang(window.GG_LANG === "en" ? "de" : "en");
    });

    window.addEventListener("gg-langchange", function (e) {
      btn.textContent = e.detail.lang.toUpperCase();
    });

    nav.appendChild(sep);
    nav.appendChild(btn);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", injectToggle);
  } else {
    injectToggle();
  }
})();
```

Load it in `index.html`, right where `version.js` loads:

```html
<script src="./version.js"></script>
<script src="./i18n.js"></script>
```

The toggle button is appended into the existing `#game-nav` footer — no new
UI surface to design per game.

### Per-game strings

Each game owns its own strings — `i18n.js` never sees them:

```javascript
const STRINGS = {
  en: { newGame: "NEW GAME" /* ... */ },
  de: { newGame: "NEUES SPIEL" /* ... */ },
};

function t(key) {
  return (STRINGS[window.GG_LANG] && STRINGS[window.GG_LANG][key])
    || STRINGS.en[key]
    || key;
}
```

Replace every literal English UI string in a render path with `t("key")`.
Whatever a game's normal re-render mechanism is, trigger it from a
`gg-langchange` listener so switching languages updates on-screen text
immediately, without a reload:

```javascript
window.addEventListener("gg-langchange", () => /* re-render */);
```
```

(Keep everything else in the file — the `## Games Hub Integration` heading
and content that follows stays exactly as-is.)

- [ ] **Step 3: Read the result back and confirm it renders as valid markdown**

```bash
sed -n '/## Localization/,/## Games Hub Integration/p' .ai/stacks/browser-game.md
```

Expected: the new section prints cleanly, ending right before (not
including) the `## Games Hub Integration` heading.

- [ ] **Step 4: Commit, push, open a PR**

```bash
git add .ai/stacks/browser-game.md
git commit -m "docs(browser-game): document concrete DE/EN i18n pattern"
git push -u origin docs/browser-game-i18n-pattern
gh pr create --title "docs(browser-game): document concrete DE/EN i18n pattern" --body "Fills in the loose Localization section with a copy-pasteable i18n.js + STRINGS/t() pattern, piloted in game-iron-valhalla. Ref freaxnx01/freaxnx01.github.io#14."
```

---

### Task 2: Wire the shared runtime into game-iron-valhalla

**Files:**
- Repo: `game-iron-valhalla` (clone fresh — see Step 1)
- Create: `i18n.js`
- Modify: `index.html` (generated file — see Global Constraints for why this one is a direct edit)

**Interfaces:**
- Consumes: the `i18n.js` source from Task 1, Step 2, copied verbatim.
- Produces: `window.GG_LANG`, `window.ggSetLang(lang)`, and the `gg-langchange` window event, which Task 3's `STRINGS`/`t()`/listener consume.

- [ ] **Step 1: Clone the repo and branch**

```bash
cd /home/freax/repos/github/freaxnx01/public
git clone https://github.com/freaxnx01/game-iron-valhalla.git
cd game-iron-valhalla
git checkout -b feat/de-en-i18n-pilot
cat AGENT-NOTES.md 2>/dev/null || echo "no AGENT-NOTES.md — ask the user for the dc-tool re-bundle command before Task 3"
```

- [ ] **Step 2: Create `i18n.js`**

Create `i18n.js` at the repo root with exactly the source from Task 1, Step
2's code block above (the `(function () { "use strict"; ... })();` IIFE).

- [ ] **Step 3: Load it in `index.html`**

In `index.html`, find:

```html
<script src="./version.js"></script>
```

Replace with:

```html
<script src="./version.js"></script>
<script src="./i18n.js"></script>
```

- [ ] **Step 4: Verify the toggle appears and flips `GG_LANG`**

```bash
python3 -m http.server 8123 &
```

Open `http://localhost:8123/index.html`. In the `#game-nav` footer
(bottom-right), confirm a new `EN` (or `DE`, depending on your browser's
language) button appears after the version badge, separated by a `·`.
Click it and confirm it toggles between `EN`/`DE`. In the browser console,
confirm:

```javascript
window.GG_LANG // reflects the toggle's current state
```

(Text elsewhere in the game won't change yet — `STRINGS`/`t()` don't exist
until Task 3. That's expected at this step.)

```bash
kill %1
```

- [ ] **Step 5: Commit**

```bash
git add i18n.js index.html
git commit -m "feat(i18n): wire shared DE/EN toggle into game-nav"
```

---

### Task 3: Translate Iron Valhalla's UI text

**Files:**
- Repo: `game-iron-valhalla` (same clone as Task 2)
- Modify: `source/Iron Valhalla Battlechess v2.dc.html`

**Interfaces:**
- Consumes: `window.GG_LANG` / `gg-langchange` from Task 2's `i18n.js`.
- Produces: none consumed by a later task in this plan — this is the last code task.

- [ ] **Step 1: Find the re-bundle command**

Check `AGENT-NOTES.md` at the repo root (read in Task 2, Step 1). If it
doesn't document the dc-tool re-bundle command, stop and ask the user for it
before continuing — do not guess.

- [ ] **Step 2: Add `STRINGS` and `t()` as class fields**

In `source/Iron Valhalla Battlechess v2.dc.html`, find:

```javascript
  BCOL = { mech:{l:'#a9b5c3',d:'#57616f'}, viking:{l:'#a6ab99',d:'#585e4f'}, wood:{l:'#dcc093',d:'#8a6642'} };
```

Replace with (adds two new fields right after it):

```javascript
  BCOL = { mech:{l:'#a9b5c3',d:'#57616f'}, viking:{l:'#a6ab99',d:'#585e4f'}, wood:{l:'#dcc093',d:'#8a6642'} };
  STRINGS = {
    en: {
      battleStatus:'BATTLE STATUS', hint:'HINT', undoMove:'UNDO MOVE', newGame:'NEW GAME',
      searchMonitor:'SEARCH MONITOR', salvageYard:'SALVAGE YARD', enemyLosses:'ENEMY LOSSES',
      yourLosses:'YOUR LOSSES', warLog:'WAR LOG', vizLegend:'TEAL = EVALUATING · GOLD = BEST LINE',
      themeMech:'THEME: MECH', themeViking:'THEME: VIKING', themeWood:'THEME: CLASSIC WOOD',
      battlesInstant:'BATTLES: INSTANT', battlesCinema:'BATTLES: CINEMA',
      soundOn:'SOUND: ON', soundOff:'SOUND: OFF', aiViewOn:'AI VIEW: ON', aiViewOff:'AI VIEW: OFF',
      yourMove:'YOUR MOVE', combatEngaged:'COMBAT ENGAGED', computing:'COMPUTING',
      fieldPromotion:'FIELD PROMOTION', campaignComplete:'CAMPAIGN COMPLETE',
      clickToSkip:'CLICK ANYWHERE TO SKIP', calculatingVector:'CALCULATING ASSAULT VECTOR…',
      selectUpgrade:'SELECT AN UPGRADE', kingUnderThreat:'WARNING — KING UNDER THREAT',
      selectUnit:'SELECT A UNIT', awaitingTurn:'AWAITING ENEMY TURN…',
      promoSub:'Your {piece} reached enemy lines. Choose its promotion.',
      stalemate:'STALEMATE', victory:'VICTORY', defeat:'DEFEAT',
      drawSub:'Both armies stand exhausted among the wreckage. The field is drawn.',
      winSub:'The enemy warlord lies in ruin. The skalds will sing of this day.',
      loseSub:'Your king has fallen. The enemy claims the field.',
      newBattle:'NEW BATTLE', you:'YOU', cpu:'CPU', vs:'VS', clickToSkipShort:'CLICK TO SKIP',
    },
    de: {
      battleStatus:'KAMPFSTATUS', hint:'TIPP', undoMove:'ZUG RÜCKGÄNGIG', newGame:'NEUES SPIEL',
      searchMonitor:'SUCHMONITOR', salvageYard:'SCHROTTPLATZ', enemyLosses:'FEINDVERLUSTE',
      yourLosses:'EIGENE VERLUSTE', warLog:'KRIEGSPROTOKOLL', vizLegend:'TÜRKIS = BEWERTUNG · GOLD = BESTE LINIE',
      themeMech:'THEMA: MECH', themeViking:'THEMA: WIKINGER', themeWood:'THEMA: KLASSISCH HOLZ',
      battlesInstant:'KÄMPFE: SOFORT', battlesCinema:'KÄMPFE: KINO',
      soundOn:'TON: AN', soundOff:'TON: AUS', aiViewOn:'KI-ANSICHT: AN', aiViewOff:'KI-ANSICHT: AUS',
      yourMove:'DEIN ZUG', combatEngaged:'KAMPF BEGONNEN', computing:'BERECHNET',
      fieldPromotion:'BEFÖRDERUNG', campaignComplete:'FELDZUG BEENDET',
      clickToSkip:'ÜBERALL KLICKEN ZUM ÜBERSPRINGEN', calculatingVector:'BERECHNE ANGRIFFSVEKTOR…',
      selectUpgrade:'UPGRADE WÄHLEN', kingUnderThreat:'WARNUNG — KÖNIG BEDROHT',
      selectUnit:'EINHEIT WÄHLEN', awaitingTurn:'WARTE AUF GEGNERZUG…',
      promoSub:'Dein {piece} hat die feindlichen Linien erreicht. Wähle seine Beförderung.',
      stalemate:'PATT', victory:'SIEG', defeat:'NIEDERLAGE',
      drawSub:'Beide Armeen stehen erschöpft inmitten der Trümmer. Das Feld ist unentschieden.',
      winSub:'Der feindliche Kriegsherr liegt in Trümmern. Die Skalden werden von diesem Tag singen.',
      loseSub:'Dein König ist gefallen. Der Feind beansprucht das Feld.',
      newBattle:'NEUE SCHLACHT', you:'DU', cpu:'KI', vs:'GEGEN', clickToSkipShort:'KLICKEN ZUM ÜBERSPRINGEN',
    },
  };
  t(key, vars) {
    var s = (this.STRINGS[window.GG_LANG] && this.STRINGS[window.GG_LANG][key]) || this.STRINGS.en[key] || key;
    if (vars) for (var k in vars) s = s.replace('{' + k + '}', vars[k]);
    return s;
  }
```

- [ ] **Step 3: Force a re-render on language change**

Find:

```javascript
  componentDidMount(){ this.measure(); window.addEventListener('resize',this.measure); this.to(this.measure,50); }
```

Replace with:

```javascript
  componentDidMount(){ this.measure(); window.addEventListener('resize',this.measure); this.to(this.measure,50); window.addEventListener('gg-langchange', () => this.setState({})); }
```

- [ ] **Step 4: Replace the turn-status literals**

Find:

```javascript
    let turnText,turnColor,turnSub;
    if(s.over){ turnText=s.over.title; turnColor=s.over.color; turnSub='CAMPAIGN COMPLETE'; }
    else if(s.battle){ turnText='COMBAT ENGAGED'; turnColor='#e8b34b'; turnSub='CLICK ANYWHERE TO SKIP'; }
    else if(s.thinking){ turnText=CL.b.nm+' COMPUTING'; turnColor=CL.b.col; turnSub='CALCULATING ASSAULT VECTOR…'; }
    else if(s.promo){ turnText='FIELD PROMOTION'; turnColor='#e8b34b'; turnSub='SELECT AN UPGRADE'; }
    else { turnText='YOUR MOVE'; turnColor='#35e0cf'; turnSub=s.checkSq>=0?'WARNING — KING UNDER THREAT':CL.w.nm+' — SELECT A UNIT'; }
```

Replace with:

```javascript
    let turnText,turnColor,turnSub;
    if(s.over){ turnText=s.over.title; turnColor=s.over.color; turnSub=this.t('campaignComplete'); }
    else if(s.battle){ turnText=this.t('combatEngaged'); turnColor='#e8b34b'; turnSub=this.t('clickToSkip'); }
    else if(s.thinking){ turnText=CL.b.nm+' '+this.t('computing'); turnColor=CL.b.col; turnSub=this.t('calculatingVector'); }
    else if(s.promo){ turnText=this.t('fieldPromotion'); turnColor='#e8b34b'; turnSub=this.t('selectUpgrade'); }
    else { turnText=this.t('yourMove'); turnColor='#35e0cf'; turnSub=s.checkSq>=0?this.t('kingUnderThreat'):CL.w.nm+' — '+this.t('selectUnit'); }
```

- [ ] **Step 5: Replace the game-over message construction**

Find:

```javascript
      this.to(()=>{ this.setState({over:{ title:stale?'STALEMATE':win?'VICTORY':'DEFEAT', color:stale?'#e8b34b':win?'#35e0cf':'#ff6a4d', sub:stale?'Both armies stand exhausted among the wreckage. The field is drawn.':win?'The enemy warlord lies in ruin. The skalds will sing of this day.':'Your king has fallen. The enemy claims the field.' }}); this.play(win?'win':stale?'horn':'lose'); },900);
```

Replace with:

```javascript
      this.to(()=>{ this.setState({over:{ title:stale?this.t('stalemate'):win?this.t('victory'):this.t('defeat'), color:stale?'#e8b34b':win?'#35e0cf':'#ff6a4d', sub:stale?this.t('drawSub'):win?this.t('winSub'):this.t('loseSub') }}); this.play(win?'win':stale?'horn':'lose'); },900);
```

- [ ] **Step 6: Replace the render()-return literals**

Find:

```javascript
      toggleViz:()=>this.setState(x=>({aiView:!x.aiView})),
      vizBtnLabel:'AI VIEW: '+(s.aiView?'ON':'OFF'),
      aiViewOn:!!s.aiView,
      vizStats:vizSrc?vizSrc.stats:'AWAITING ENEMY TURN…',
```

Replace with:

```javascript
      toggleViz:()=>this.setState(x=>({aiView:!x.aiView})),
      vizBtnLabel:s.aiView?this.t('aiViewOn'):this.t('aiViewOff'),
      aiViewOn:!!s.aiView,
      vizStats:vizSrc?vizSrc.stats:this.t('awaitingTurn'),
```

Find:

```javascript
      turnText, turnColor, turnSub,
      youClan:CL.w.nm+' — YOU', cpuClan:CL.b.nm+' — CPU', youDot:CL.w.col, cpuDot:CL.b.col,
```

Replace with:

```javascript
      turnText, turnColor, turnSub,
      youClan:CL.w.nm+' — '+this.t('you'), cpuClan:CL.b.nm+' — '+this.t('cpu'), youDot:CL.w.col, cpuDot:CL.b.col,
```

Find:

```javascript
      toggleInstant:()=>this.setState(x=>({instant:!x.instant})), instantLabel:s.instant?'BATTLES: INSTANT':'BATTLES: CINEMA',
      toggleSound:()=>this.setState(x=>({sound:!x.sound})), soundLabel:s.sound?'SOUND: ON':'SOUND: OFF',
      cycleTheme:()=>{ const order=['mech','viking','wood']; const nx=order[(order.indexOf(th)+1)%3]; this.setState({theme:nx}); this.play('select'); },
      themeLabel:'THEME: '+(th==='mech'?'MECH':th==='viking'?'VIKING':'CLASSIC WOOD'),
      battleOn:!!b, skipBattle:()=>this.endBattle(),
      battleLabel:b?(CL[b.atk.c].nm+' '+NM[b.atk.t]+'  VS  '+CL[b.def.c].nm+' '+NM[b.def.t]):'',
      battleBoardEl:b?this.battleBoard(b):null,
      promoOn:!!s.promo, promoSub:'Your '+NM.p+' reached enemy lines. Choose its promotion.',
```

Replace with:

```javascript
      toggleInstant:()=>this.setState(x=>({instant:!x.instant})), instantLabel:s.instant?this.t('battlesInstant'):this.t('battlesCinema'),
      toggleSound:()=>this.setState(x=>({sound:!x.sound})), soundLabel:s.sound?this.t('soundOn'):this.t('soundOff'),
      cycleTheme:()=>{ const order=['mech','viking','wood']; const nx=order[(order.indexOf(th)+1)%3]; this.setState({theme:nx}); this.play('select'); },
      themeLabel:th==='mech'?this.t('themeMech'):th==='viking'?this.t('themeViking'):this.t('themeWood'),
      battleOn:!!b, skipBattle:()=>this.endBattle(),
      battleLabel:b?(CL[b.atk.c].nm+' '+NM[b.atk.t]+'  '+this.t('vs')+'  '+CL[b.def.c].nm+' '+NM[b.def.t]):'',
      battleBoardEl:b?this.battleBoard(b):null,
      promoOn:!!s.promo, promoSub:this.t('promoSub',{piece:NM.p}),
```

- [ ] **Step 7: Replace the static template labels**

In the same file, find each of these template lines and swap the literal
text for a `{{ }}`-bound field (add the matching key to the `render()`
return object from Step 6, next to `themeLabel`):

Find:
```html
        <div style="font-family:'Russo One',sans-serif;font-size:9px;letter-spacing:2.5px;color:#e8b34b">BATTLE STATUS</div>
```
Replace with:
```html
        <div style="font-family:'Russo One',sans-serif;font-size:9px;letter-spacing:2.5px;color:#e8b34b">{{ battleStatusLabel }}</div>
```

Find:
```html
        <div onClick="{{ hint }}" style="background:#14323a;border:1px solid #2a6b66;border-radius:8px;padding:9px 6px;font-size:10px;font-weight:700;letter-spacing:1.5px;color:#6fe6d8;cursor:pointer;text-align:center" style-hover="background: #1a4650; color: #a5f4ea">HINT</div>
        <div onClick="{{ undo }}" style="background:#1b2431;border:1px solid #2e3a4c;border-radius:8px;padding:9px 6px;font-size:10px;font-weight:700;letter-spacing:1.5px;color:#aebccb;cursor:pointer;text-align:center" style-hover="background: #232f40; color: #e6eef7">UNDO MOVE</div>
```
Replace with:
```html
        <div onClick="{{ hint }}" style="background:#14323a;border:1px solid #2a6b66;border-radius:8px;padding:9px 6px;font-size:10px;font-weight:700;letter-spacing:1.5px;color:#6fe6d8;cursor:pointer;text-align:center" style-hover="background: #1a4650; color: #a5f4ea">{{ hintLabel }}</div>
        <div onClick="{{ undo }}" style="background:#1b2431;border:1px solid #2e3a4c;border-radius:8px;padding:9px 6px;font-size:10px;font-weight:700;letter-spacing:1.5px;color:#aebccb;cursor:pointer;text-align:center" style-hover="background: #232f40; color: #e6eef7">{{ undoLabel }}</div>
```

Find:
```html
        <div onClick="{{ newGame }}" style="background:#1b2431;border:1px solid #2e3a4c;border-radius:8px;padding:9px 6px;font-size:10px;font-weight:700;letter-spacing:1.5px;color:#aebccb;cursor:pointer;text-align:center" style-hover="background: #232f40; color: #e6eef7">NEW GAME</div>
```
Replace with:
```html
        <div onClick="{{ newGame }}" style="background:#1b2431;border:1px solid #2e3a4c;border-radius:8px;padding:9px 6px;font-size:10px;font-weight:700;letter-spacing:1.5px;color:#aebccb;cursor:pointer;text-align:center" style-hover="background: #232f40; color: #e6eef7">{{ newGameLabel }}</div>
```

Find:
```html
            <div style="font-family:'Russo One',sans-serif;font-size:9px;letter-spacing:2.5px;color:#b9a8e8">SEARCH MONITOR</div>
```
Replace with:
```html
            <div style="font-family:'Russo One',sans-serif;font-size:9px;letter-spacing:2.5px;color:#b9a8e8">{{ searchMonitorLabel }}</div>
```

Find:
```html
          <div style="font-size:8px;color:#55657a;margin-top:5px;letter-spacing:1.2px">TEAL = EVALUATING · GOLD = BEST LINE</div>
```
Replace with:
```html
          <div style="font-size:8px;color:#55657a;margin-top:5px;letter-spacing:1.2px">{{ vizLegendLabel }}</div>
```

Find:
```html
        <div style="font-family:'Russo One',sans-serif;font-size:9px;letter-spacing:2.5px;color:#e8b34b">SALVAGE YARD</div>
        <div style="font-size:9px;letter-spacing:1.5px;color:#ff8a72;margin-top:6px;font-weight:700">ENEMY LOSSES</div>
```
Replace with:
```html
        <div style="font-family:'Russo One',sans-serif;font-size:9px;letter-spacing:2.5px;color:#e8b34b">{{ salvageYardLabel }}</div>
        <div style="font-size:9px;letter-spacing:1.5px;color:#ff8a72;margin-top:6px;font-weight:700">{{ enemyLossesLabel }}</div>
```

Find:
```html
        <div style="font-size:9px;letter-spacing:1.5px;color:#6fd3c8;margin-top:5px;font-weight:700">YOUR LOSSES</div>
```
Replace with:
```html
        <div style="font-size:9px;letter-spacing:1.5px;color:#6fd3c8;margin-top:5px;font-weight:700">{{ yourLossesLabel }}</div>
```

Find:
```html
        <div style="font-family:'Russo One',sans-serif;font-size:9px;letter-spacing:2.5px;color:#e8b34b;flex:none">WAR LOG</div>
```
Replace with:
```html
        <div style="font-family:'Russo One',sans-serif;font-size:9px;letter-spacing:2.5px;color:#e8b34b;flex:none">{{ warLogLabel }}</div>
```

Find:
```html
        <div style="font-family:'Russo One',sans-serif;font-size:16px;letter-spacing:2px;color:#e8b34b">FIELD PROMOTION</div>
```
Replace with:
```html
        <div style="font-family:'Russo One',sans-serif;font-size:16px;letter-spacing:2px;color:#e8b34b">{{ fieldPromotionLabel }}</div>
```

Find (both occurrences of `NEW BATTLE`):
```html
        <div onClick="{{ newGame }}" style="margin-top:26px;display:inline-block;background:#35e0cf;color:#08191c;font-family:'Russo One',sans-serif;font-size:13px;letter-spacing:2px;padding:12px 30px;border-radius:8px;cursor:pointer" style-hover="background: #5ff0e0">NEW BATTLE</div>
```
Replace with:
```html
        <div onClick="{{ newGame }}" style="margin-top:26px;display:inline-block;background:#35e0cf;color:#08191c;font-family:'Russo One',sans-serif;font-size:13px;letter-spacing:2px;padding:12px 30px;border-radius:8px;cursor:pointer" style-hover="background: #5ff0e0">{{ newBattleLabel }}</div>
```

Find:
```html
        <div style="position:absolute;left:50%;top:4px;transform:translateX(-50%);z-index:5;background:rgba(13,18,26,.85);border:1px solid #2c3850;border-radius:20px;padding:7px 18px;font-size:11px;letter-spacing:2px;color:#e8b34b;font-weight:700;white-space:nowrap;animation:kfFadeIn .3s">{{ battleLabel }} — CLICK TO SKIP</div>
```
Replace with:
```html
        <div style="position:absolute;left:50%;top:4px;transform:translateX(-50%);z-index:5;background:rgba(13,18,26,.85);border:1px solid #2c3850;border-radius:20px;padding:7px 18px;font-size:11px;letter-spacing:2px;color:#e8b34b;font-weight:700;white-space:nowrap;animation:kfFadeIn .3s">{{ battleLabel }} — {{ clickToSkipShortLabel }}</div>
```

Now add the corresponding `*Label` fields to the `render()` return object
from Step 6 — find:

```javascript
      themeLabel:th==='mech'?this.t('themeMech'):th==='viking'?this.t('themeViking'):this.t('themeWood'),
```

Replace with:

```javascript
      themeLabel:th==='mech'?this.t('themeMech'):th==='viking'?this.t('themeViking'):this.t('themeWood'),
      battleStatusLabel:this.t('battleStatus'), hintLabel:this.t('hint'), undoLabel:this.t('undoMove'),
      newGameLabel:this.t('newGame'), searchMonitorLabel:this.t('searchMonitor'), vizLegendLabel:this.t('vizLegend'),
      salvageYardLabel:this.t('salvageYard'), enemyLossesLabel:this.t('enemyLosses'), yourLossesLabel:this.t('yourLosses'),
      warLogLabel:this.t('warLog'), fieldPromotionLabel:this.t('fieldPromotion'), newBattleLabel:this.t('newBattle'),
      clickToSkipShortLabel:this.t('clickToSkipShort'),
```

- [ ] **Step 8: Re-bundle**

Run the re-bundle command found in Step 1. Confirm it regenerated
`index.html` / `support.js` (check their mtimes or diff them) — but do NOT
let it overwrite the `<script src="./i18n.js">` tag or the `#game-nav`
block from Task 2; if it does, reapply those two edits to `index.html`
afterward (per Global Constraints, they're a manual, non-source-tracked
addition in this repo).

```bash
git diff --stat index.html support.js
```

- [ ] **Step 9: Verify end-to-end in a browser**

```bash
python3 -m http.server 8123 &
```

Open `http://localhost:8123/index.html`. Confirm:

- The game loads with an empty console (no errors).
- Clicking the `EN`/`DE` toggle in `#game-nav` immediately switches the
  sidebar labels (BATTLE STATUS/KAMPFSTATUS, HINT/TIPP, etc.), the
  "YOUR MOVE"/"DEIN ZUG" status text, and — after triggering a promotion or
  finishing a game — the promotion dialog and game-over screen text.
- Reloading the page after switching to DE keeps DE (persisted via
  `localStorage["gg-lang"]`).
- Switching back to EN restores the original English text exactly as it was
  before any changes.

```bash
kill %1
```

- [ ] **Step 10: Commit**

```bash
git add "source/Iron Valhalla Battlechess v2.dc.html" index.html support.js
git commit -m "feat(i18n): translate Iron Valhalla UI text to DE/EN"
```

---

### Task 4: Push and open the pilot PR

**Files:** none (git operations only)

**Interfaces:**
- Consumes: the combined output of Tasks 2–3 (game-iron-valhalla branch
  `feat/de-en-i18n-pilot`).

- [ ] **Step 1: Push and open the PR**

```bash
cd /home/freax/repos/github/freaxnx01/public/game-iron-valhalla
git push -u origin feat/de-en-i18n-pilot
gh pr create --title "feat(i18n): DE/EN support (pilot)" --body "Pilots the DE/EN i18n pattern documented in freaxnx01/ai-instructions (see that repo's PR). Ref freaxnx01/freaxnx01.github.io#14."
```

- [ ] **Step 2: Cross-link the two PRs**

Add a comment on the `ai-instructions` PR (from Task 1) linking the
`game-iron-valhalla` PR, and vice versa, so a reviewer can see both halves
of the pilot together:

```bash
cd /home/freax/repos/github/freaxnx01/public/ai-instructions
ai_pr=$(gh pr view --json url -q .url)
cd /home/freax/repos/github/freaxnx01/public/game-iron-valhalla
game_pr=$(gh pr view --json url -q .url)
gh pr comment --body "Pilot implementation: $game_pr"
cd /home/freax/repos/github/freaxnx01/public/ai-instructions
gh pr comment "$ai_pr" --body "Pilot implementation: $game_pr" 2>/dev/null || gh pr comment --body "Pilot implementation: $game_pr"
```

No commit needed for this task — it's PR bookkeeping.
