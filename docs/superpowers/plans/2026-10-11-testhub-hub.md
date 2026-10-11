# Testhub Hub Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A playtest hub page at `/testhub/` plus one shared `client.js`, so the maintainer sees only untested `test-todo.md` items per game, jumps to each with one click, adds notes and screenshots, and exports it all with **Copy all**.

**Architecture:** Pure ES modules tested with `node --test`; a plain-DOM hub UI talking to game windows over `BroadcastChannel('gg-testhub')`; `client.js` as a classic script any game loads with `<script src>`. One Python Playwright file opens the hub and a fake game in two pages of one context, served by `context.route`.

**Tech Stack:** Vanilla JS (ES modules, no framework/build/`package.json`), `node --test`, pytest + Playwright.

**Spec:** `docs/superpowers/specs/2026-10-11-testhub-design.md` in `freaxnx01/game-rhyflitzer` (sections 1, 2, 4, error handling, hub tests); parent issue `freaxnx01/game-rhyflitzer#251`. The Rhyflitzer integration is a separate plan.

## Global Constraints

- Static only (Pages, branch `master`): no server, token, build step, framework or `eval`. Hub in `testhub/`.
- BroadcastChannel and localStorage key are both `gg-testhub`; language key `gg-lang` (`en`/`de`). All storage access in try/catch.
- Item key `<game>|<block heading>|<item text without tag>`; tag `{go: <id>}`, id `[a-z0-9._-]+`; status `open|noted|done`; screenshots `fb-<game>-<MMDD>-<n>.png`; go/screenshot timeout 10 s; games start `rhyflitzer`, `wipfelkratzer`.
- Copy-all export format exactly as the spec's section 4 (header `Testhub feedback — <game> v<version> — <YYYY-MM-DD>`, note lines, `✓ tested` lines); Task 3's test pins it.
- `client.js` contract (agreed with the Rhyflitzer plan): defines `window.ggTesthub`, then fires `gg-testhub-ready` on `window` and sends a first `hello`; every `register`/`setInfo`/`onScreenshot` call triggers a fresh debounced `hello`; the game registers after that. `register(id, fn, label)`: a repeated id replaces the earlier one, `fn()` is synchronous, its return value ignored. `onScreenshot(fn)`: `fn()` returns `Promise<'data:image/png;base64,…'>`, may reject or hang; the hub's 10 s timeout covers it. `setInfo({game, version})` once, `version` without leading `v` (the hub shows `v` + version). Loader URL exactly `/testhub/client.js`, async, dev mode only.
- UI strings de/en via `gg-lang` (real umlauts); item text stays as in `test-todo.md`.

## Review Focus

1. Foreign/malformed channel messages (`targets: "nope"`, non-PNG data URL, hub-style `hello` at a game, another game's `hello`) are ignored without error: Tasks 4, 6, 10.
2. A second game window must not change the hub status: Task 10.
3. CRLF, `###` sub-headings, malformed tags in `test-todo.md`: Task 1.
4. Corrupt JSON or a throwing `localStorage` accessor must not stop the hub: Tasks 2, 7.
5. Multi-line or quoted notes export as one line: Task 3.

## Test setup (decision)

The repo has pytest + Playwright in `tests/` (`.venv/` gitignored) and no JS tooling. So: `node --test tests/testhub/*.test.mjs` for modules and `client.js` (if Node reports a module-type error, add `testhub/package.json` = `{"type":"module"}`), Python Playwright for e2e (`python3 -m venv .venv && .venv/bin/pip install pytest playwright && .venv/bin/playwright install chromium`). No CI runs tests here (out of scope).

---

### Task 1: Pure parser for `test-todo.md`

**Files:** Create `testhub/parser.js`; Test `tests/testhub/parser.test.mjs`

**Interfaces:** Produces `splitTag(text) -> {text, tag|null}`, `itemKey(game, heading, text)`, `parseTodo(markdown, game) -> [{heading, tag, items:[{key, text, tag}]}]` (blocks without open items dropped; item tag falls back to block tag).

- [ ] **Step 1: Write the failing test**

```js
import test from 'node:test';
import assert from 'node:assert/strict';
import { parseTodo, splitTag } from '../../testhub/parser.js';

test('splitTag_tagInText_isStrippedAndReturned', () => {
  assert.deepEqual(splitTag('Inside: tower {go: hideout.tower} reads dark'), { text: 'Inside: tower reads dark', tag: 'hideout.tower' });
});

test('splitTag_malformedTags_stayAsText', () => {
  assert.deepEqual(splitTag('a {go: BAD ID} b'), { text: 'a {go: BAD ID} b', tag: null });
  assert.deepEqual(splitTag('a {go:} b'), { text: 'a {go:} b', tag: null });
});

test('parseTodo_openItemsOnly_withKeys_crlfAndSubheadingsOk', () => {
  const md = '# Title\r\n- [ ] no block yet\r\n## Alpha\r\n- [ ] one\r\n- [x] done\r\n### Sub\r\n- [X] done too\r\n  - [ ] two\r\n## Empty\r\n- [x] all ticked\r\n';
  const blocks = parseTodo(md, 'g');
  assert.equal(blocks.length, 1);
  assert.deepEqual(blocks[0].items.map((i) => i.text), ['one', 'two']);
  assert.equal(blocks[0].items[0].key, 'g|Alpha|one');
});

test('parseTodo_blockTag_isInheritedUnlessItemHasOwn', () => {
  const [block] = parseTodo('## Hideout {go: hideout.gate}\n- [ ] inherits\n- [ ] own {go: hideout.tower}\n', 'g');
  assert.equal(block.heading, 'Hideout');
  assert.deepEqual(block.items.map((i) => i.tag), ['hideout.gate', 'hideout.tower']);
  assert.equal(block.items[1].text, 'own');
});
```

- [ ] **Step 2: Run to verify it fails**

Run: `node --test tests/testhub/parser.test.mjs` — Expected: FAIL, missing `testhub/parser.js`.

- [ ] **Step 3: Implement**

```js
const TAG_RE = /\{go:\s*([a-z0-9._-]+)\s*\}/;
const TAG_STRIP_RE = /\s*\{go:\s*[a-z0-9._-]+\s*\}/g;
const H1_RE = /^#\s/;
const H2_RE = /^##\s+(.*\S)\s*$/;
const ITEM_RE = /^\s*- \[ \]\s+(.*\S)\s*$/;

export function splitTag(text) {
  const match = TAG_RE.exec(text);
  return { text: text.replace(TAG_STRIP_RE, '').replace(/\s+/g, ' ').trim(), tag: match ? match[1] : null };
}

export const itemKey = (game, heading, text) => `${game}|${heading}|${text}`;

export function parseTodo(markdown, game) {
  const blocks = [];
  let block = null;
  for (const line of markdown.split(/\r?\n/)) {
    if (H1_RE.test(line)) { block = null; continue; }
    const heading = H2_RE.exec(line);
    if (heading) {
      const { text, tag } = splitTag(heading[1]);
      block = { heading: text, tag, items: [] };
      blocks.push(block);
      continue;
    }
    const item = ITEM_RE.exec(line);
    if (!item || !block) continue;
    const { text, tag } = splitTag(item[1]);
    if (text) block.items.push({ key: itemKey(game, block.heading, text), text, tag: tag || block.tag });
  }
  return blocks.filter((b) => b.items.length > 0);
}
```

- [ ] **Step 4: Run to verify it passes** — `node --test tests/testhub/parser.test.mjs` — Expected: PASS (4).

- [ ] **Step 5: Commit** — `git add testhub tests && git commit -m "feat(testhub): parse test-todo.md into blocks and tagged items"`

---

### Task 2: State store with localStorage fallback

**Files:** Create `testhub/store.js`; Test `tests/testhub/store.test.mjs`

**Interfaces:** Produces `getStorage() -> Storage|null` (never throws); `createStore(storage) -> { get(key), update(key, patch), setVersion(game, v), version(game), nextShotName(game, date), isPersistent() }`. `get` merges stored data over `{status:'open', note:'', screenshots:[], sent:false}`; `update` merges the patch and resets `sent` unless the patch sets it; `nextShotName(game, Date)` = `fb-<game>-<MMDD>-<1 + highest stored n that day>.png`.

- [ ] **Step 1: Write the failing test**

```js
import test from 'node:test';
import assert from 'node:assert/strict';
import { createStore } from '../../testhub/store.js';

const fakeStorage = (initial) => {
  const data = new Map(initial ? [['gg-testhub', initial]] : []);
  return { getItem: (k) => (data.has(k) ? data.get(k) : null), setItem: (k, v) => data.set(k, v) };
};

test('get_unknownKey_returnsOpenDefaults', () => {
  assert.deepEqual(createStore(fakeStorage()).get('k'), { status: 'open', note: '', screenshots: [], sent: false });
});

test('update_persistsAndResetsSent', () => {
  const storage = fakeStorage();
  const store = createStore(storage);
  store.update('k', { status: 'noted', note: 'x', sent: true });
  assert.equal(store.get('k').sent, true);
  store.update('k', { note: 'y' });
  assert.equal(store.get('k').sent, false);
  assert.equal(createStore(storage).get('k').note, 'y');
});

test('createStore_corruptJson_startsEmpty', () => {
  assert.equal(createStore(fakeStorage('{not json')).get('k').status, 'open');
});

test('nextShotName_countsUpPerGameAndDay', () => {
  const store = createStore(fakeStorage());
  const day = new Date(2026, 9, 11);
  assert.equal(store.nextShotName('rhyflitzer', day), 'fb-rhyflitzer-1011-1.png');
  store.update('b', { screenshots: ['fb-rhyflitzer-1011-3.png', 'fb-other-1011-9.png'] });
  assert.equal(store.nextShotName('rhyflitzer', day), 'fb-rhyflitzer-1011-4.png');
  assert.equal(store.nextShotName('rhyflitzer', new Date(2026, 9, 12)), 'fb-rhyflitzer-1012-1.png');
});
```

- [ ] **Step 2: Run to verify it fails** — `node --test tests/testhub/store.test.mjs` — Expected: FAIL, missing `testhub/store.js`.

- [ ] **Step 3: Implement**

```js
const KEY = 'gg-testhub';
const DEFAULT_ENTRY = { status: 'open', note: '', screenshots: [], sent: false };
const pad = (n) => String(n).padStart(2, '0');
const emptyState = () => ({ v: 1, items: {}, versions: {} });

export function getStorage() {
  try { return globalThis.localStorage || null; } catch (e) { return null; }
}

function readState(storage) {
  if (!storage) return emptyState();
  try {
    const parsed = JSON.parse(storage.getItem(KEY));
    const valid = parsed && typeof parsed === 'object' && !Array.isArray(parsed) && parsed.items && typeof parsed.items === 'object';
    if (!valid) return emptyState();
    return { v: 1, items: parsed.items, versions: parsed.versions && typeof parsed.versions === 'object' ? parsed.versions : {} };
  } catch (e) {
    return emptyState();
  }
}

export function createStore(storage) {
  const state = readState(storage);
  let persistent = Boolean(storage);

  function save() {
    if (!storage) { persistent = false; return; }
    try { storage.setItem(KEY, JSON.stringify(state)); } catch (e) { persistent = false; }
  }

  function get(key) {
    const stored = state.items[key] || {};
    return { ...DEFAULT_ENTRY, ...stored, screenshots: [...(stored.screenshots || [])] };
  }

  function update(key, patch) {
    const next = { ...get(key), ...patch };
    if (!('sent' in patch)) next.sent = false;
    state.items[key] = next;
    save();
  }

  function nextShotName(game, date) {
    const prefix = `fb-${game}-${pad(date.getMonth() + 1)}${pad(date.getDate())}-`;
    let highest = 0;
    for (const entry of Object.values(state.items)) {
      for (const name of entry.screenshots || []) {
        if (name.startsWith(prefix)) highest = Math.max(highest, parseInt(name.slice(prefix.length), 10) || 0);
      }
    }
    return `${prefix}${highest + 1}.png`;
  }

  return {
    get, update, nextShotName,
    setVersion(game, version) { state.versions[game] = version; save(); },
    version: (game) => state.versions[game] || '',
    isPersistent: () => persistent,
  };
}
```

- [ ] **Step 4: Run to verify it passes** — `node --test tests/testhub/store.test.mjs` — Expected: PASS (4).

- [ ] **Step 5: Commit** — `git add testhub tests && git commit -m "feat(testhub): persist item state in gg-testhub with in-memory fallback"`

---

### Task 3: Copy-all export format

**Files:** Create `testhub/export.js`; Test `tests/testhub/export.test.mjs`

**Interfaces:** Produces `isoDate(Date) -> 'YYYY-MM-DD'` (local) and `buildExport({game, version, date, entries}) -> string` with `entries = [{block, text, tag, status, note, screenshots}]`: a note line if `note`/`screenshots` is non-empty, then a `✓ tested` line if `status === 'done'`; whitespace in notes collapses; empty `version` gives `version unknown`.

- [ ] **Step 1: Write the failing test**

```js
import test from 'node:test';
import assert from 'node:assert/strict';
import { buildExport } from '../../testhub/export.js';

test('buildExport_matchesSpecFormat', () => {
  const text = buildExport({ game: 'rhyflitzer', version: '0.9.0', date: '2026-10-11', entries: [
    { block: 'Hideout in the Hübel', text: 'Inside: the tower reads as…', tag: 'hideout.tower', status: 'noted',
      note: 'Turm wirkt von unten zu dunkel', screenshots: ['fb-rhyflitzer-1011-3.png'] },
    { block: 'Pontoon bridge', text: 'U again: the bridge disappears…', tag: null, status: 'done', note: '', screenshots: [] },
  ] });
  assert.equal(text, [
    'Testhub feedback — rhyflitzer v0.9.0 — 2026-10-11',
    '- [Hideout in the Hübel · "Inside: the tower reads as…" · go:hideout.tower] Turm wirkt von unten zu dunkel (📷 fb-rhyflitzer-1011-3.png)',
    '- ✓ tested: [Pontoon bridge · "U again: the bridge disappears…"]',
  ].join('\n'));
});

test('buildExport_multilineNoteWithQuotes_staysOneLine', () => {
  const text = buildExport({ game: 'g', version: '', date: 'D', entries: [
    { block: 'B', text: 'T', tag: null, status: 'noted', note: 'one\n  line "two"', screenshots: ['a.png', 'b.png'] },
  ] });
  assert.deepEqual(text.split('\n'), ['Testhub feedback — g version unknown — D', '- [B · "T"] one line "two" (📷 a.png, b.png)']);
});
```

- [ ] **Step 2: Run to verify it fails** — `node --test tests/testhub/export.test.mjs` — Expected: FAIL, missing `testhub/export.js`.

- [ ] **Step 3: Implement**

```js
const pad = (n) => String(n).padStart(2, '0');

export const isoDate = (d) => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;

function noteLine(entry) {
  const tag = entry.tag ? ` · go:${entry.tag}` : '';
  const note = entry.note.replace(/\s+/g, ' ').trim();
  const shots = entry.screenshots.length ? `(📷 ${entry.screenshots.join(', ')})` : '';
  return `- [${entry.block} · "${entry.text}"${tag}] ${[note, shots].filter(Boolean).join(' ')}`;
}

export function buildExport({ game, version, date, entries }) {
  const lines = [`Testhub feedback — ${game} ${version ? `v${version}` : 'version unknown'} — ${date}`];
  for (const entry of entries) {
    if (entry.note.trim() || entry.screenshots.length) lines.push(noteLine(entry));
    if (entry.status === 'done') lines.push(`- ✓ tested: [${entry.block} · "${entry.text}"]`);
  }
  return lines.join('\n');
}
```

- [ ] **Step 4: Run to verify it passes** — `node --test tests/testhub/export.test.mjs` — Expected: PASS (2).

- [ ] **Step 5: Commit** — `git add testhub tests && git commit -m "feat(testhub): build the Copy-all feedback block"`

---

### Task 4: Protocol validation and message builders

**Files:** Create `testhub/protocol.js`; Test `tests/testhub/protocol.test.mjs`

**Interfaces:** Produces `CHANNEL = 'gg-testhub'`; `validateGameMessage(raw) -> normalized msg|null` for `hello {game, version, targets:[{id,label}]}`, `png {req, dataUrl}`, `done {req}`, `error {req, message}`; `helloMsg()`, `goMsg(game, id, req)`, `screenshotMsg(game, req)`, `newReq()`. Compatible extensions of the spec wire format: `go`/`screenshot` carry `game`; `go` carries `req` and is answered by `done {req}`.

- [ ] **Step 1: Write the failing test**

```js
import test from 'node:test';
import assert from 'node:assert/strict';
import { validateGameMessage as v } from '../../testhub/protocol.js';

const PNG = 'data:image/png;base64,iVBORw0KGgo=';

test('validateGameMessage_validHello_isNormalized', () => {
  assert.deepEqual(v({ type: 'hello', game: 'g', version: '1.0', targets: [{ id: 'j.a', label: 'A', x: 1 }], junk: 1 }),
    { type: 'hello', game: 'g', version: '1.0', targets: [{ id: 'j.a', label: 'A' }] });
});

test('validateGameMessage_badTargets_areRejected', () => {
  assert.equal(v({ type: 'hello' }), null);
  assert.equal(v({ type: 'hello', game: 'g', version: '1', targets: 'nope' }), null);
  assert.equal(v({ type: 'hello', game: 'g', version: '1', targets: [{ id: '<script>', label: 'x' }] }), null);
  assert.equal(v({ type: 'hello', game: 'g', version: 1, targets: [] }), null);
});

test('validateGameMessage_png_requiresPngDataUrl', () => {
  assert.deepEqual(v({ type: 'png', req: 'r', dataUrl: PNG }), { type: 'png', req: 'r', dataUrl: PNG });
  assert.equal(v({ type: 'png', req: 'r', dataUrl: 'data:text/html;base64,AAAA' }), null);
  assert.equal(v({ type: 'png', req: 'r', dataUrl: PNG + 'A'.repeat(16 * 1024 * 1024) }), null);
});

test('validateGameMessage_doneErrorAndGarbage', () => {
  assert.deepEqual(v({ type: 'done', req: 'r' }), { type: 'done', req: 'r' });
  assert.deepEqual(v({ type: 'error', req: 'r', message: 'm' }), { type: 'error', req: 'r', message: 'm' });
  for (const raw of [null, undefined, 'x', 5, [], {}, { type: 5 }, { type: 'error', req: 'r' }, { type: 'go', id: 'a' }]) {
    assert.equal(v(raw), null);
  }
});
```

- [ ] **Step 2: Run to verify it fails** — `node --test tests/testhub/protocol.test.mjs` — Expected: FAIL, missing `testhub/protocol.js`.

- [ ] **Step 3: Implement**

```js
export const CHANNEL = 'gg-testhub';

const ID_RE = /^[a-z0-9._-]+$/;
const MAX_TARGETS = 500;
const MAX_DATA_URL = 15 * 1024 * 1024;
const PNG_PREFIX = 'data:image/png;base64,';

const isString = (v, max = 300) => typeof v === 'string' && v.length <= max;
const isObject = (v) => v !== null && typeof v === 'object' && !Array.isArray(v);

function validateTargets(list) {
  if (!Array.isArray(list) || list.length > MAX_TARGETS) return null;
  const out = [];
  for (const target of list) {
    const valid = isObject(target) && isString(target.id, 100) && ID_RE.test(target.id) && isString(target.label, 200);
    if (!valid) return null;
    out.push({ id: target.id, label: target.label });
  }
  return out;
}

function validateHello(msg) {
  const targets = validateTargets(msg.targets);
  if (!targets || !isString(msg.game, 100) || !isString(msg.version, 50)) return null;
  return { type: 'hello', game: msg.game, version: msg.version, targets };
}

export function validateGameMessage(msg) {
  if (!isObject(msg) || !isString(msg.type, 20)) return null;
  if (msg.type === 'hello') return validateHello(msg);
  if (!isString(msg.req, 100)) return null;
  if (msg.type === 'done') return { type: 'done', req: msg.req };
  if (msg.type === 'error') return isString(msg.message, 500) ? { type: 'error', req: msg.req, message: msg.message } : null;
  if (msg.type === 'png') {
    return isString(msg.dataUrl, MAX_DATA_URL) && msg.dataUrl.startsWith(PNG_PREFIX) ? { type: 'png', req: msg.req, dataUrl: msg.dataUrl } : null;
  }
  return null;
}

export const helloMsg = () => ({ type: 'hello' });
export const goMsg = (game, id, req) => ({ type: 'go', game, id, req });
export const screenshotMsg = (game, req) => ({ type: 'screenshot', game, req });
export const newReq = () => Math.random().toString(36).slice(2) + Date.now().toString(36);
```

- [ ] **Step 4: Run to verify it passes** — `node --test tests/testhub/protocol.test.mjs` — Expected: PASS (5).

- [ ] **Step 5: Commit** — `git add testhub tests && git commit -m "feat(testhub): validate channel messages from game windows"`

---

### Task 5: de/en strings and language detection

**Files:** Create `testhub/strings.js`; Test `tests/testhub/strings.test.mjs`

**Interfaces:** Produces `STRINGS = {en, de}`; `detectLang(storage|null, navigatorLanguage) -> 'en'|'de'` (`gg-lang` first, else `de*` navigator, else `en`); `createT(lang) -> (key, params?) -> string` (`{name}` placeholders; unknown key returns the key).

- [ ] **Step 1: Write the failing test**

```js
import test from 'node:test';
import assert from 'node:assert/strict';
import { STRINGS, detectLang, createT } from '../../testhub/strings.js';

test('STRINGS_bothLanguages_haveTheSameKeys', () => {
  assert.deepEqual(Object.keys(STRINGS.de).sort(), Object.keys(STRINGS.en).sort());
});

test('detectLang_storedWins_elseNavigator', () => {
  assert.equal(detectLang({ getItem: () => 'de' }, 'en-GB'), 'de');
  assert.equal(detectLang({ getItem: () => 'fr' }, 'de-CH'), 'de');
  assert.equal(detectLang(null, 'en-US'), 'en');
});

test('createT_replacesPlaceholdersAndFallsBackToKey', () => {
  assert.equal(createT('en')('copyAll', { n: 3 }), 'Copy all 3');
  assert.equal(createT('de')('copyAll', { n: 3 }), 'Alle kopieren 3');
  assert.equal(createT('en')('missing.key'), 'missing.key');
});
```

- [ ] **Step 2: Run to verify it fails** — `node --test tests/testhub/strings.test.mjs` — Expected: FAIL, missing `testhub/strings.js`.

- [ ] **Step 3: Implement**

```js
export const STRINGS = {
  en: {
    title: 'Testhub',
    connected: 'Game connected (v{version} · {n} targets)',
    disconnected: 'No game window',
    openGame: 'Open the game with ?dev=1',
    filter_open: 'Open', filter_noted: 'Noted', filter_done: 'Done',
    search: 'Search…',
    copyAll: 'Copy all {n}',
    go: 'Go ▸',
    goUnknown: 'Unknown target',
    notePlaceholder: 'Note…',
    save: 'Save',
    done: '✓ Done',
    shot: '📷 Screenshot',
    loadError: 'Could not load test-todo.md for {game}: {reason}',
    noItems: 'Nothing to show.',
    noStorage: 'Storage is unavailable: notes are kept for this session only.',
    err_timeout: 'No answer from the game within 10 s.',
    err_noGame: 'No game window connected.',
    copied: 'Copied {n} entries.',
    copyManual: 'Copy was refused. Copy the text below by hand:',
    langToggle: 'DE',
  },
  de: {
    title: 'Testhub',
    connected: 'Spiel verbunden (v{version} · {n} Ziele)',
    disconnected: 'Kein Spielfenster',
    openGame: 'Spiel mit ?dev=1 öffnen',
    filter_open: 'Offen', filter_noted: 'Notiert', filter_done: 'Erledigt',
    search: 'Suchen…',
    copyAll: 'Alle kopieren {n}',
    go: 'Los ▸',
    goUnknown: 'Unbekanntes Ziel',
    notePlaceholder: 'Notiz…',
    save: 'Speichern',
    done: '✓ Erledigt',
    shot: '📷 Screenshot',
    loadError: 'test-todo.md für {game} konnte nicht geladen werden: {reason}',
    noItems: 'Nichts anzuzeigen.',
    noStorage: 'Speicher nicht verfügbar: Notizen gelten nur für diese Sitzung.',
    err_timeout: 'Keine Antwort vom Spiel innerhalb von 10 s.',
    err_noGame: 'Kein Spielfenster verbunden.',
    copied: '{n} Einträge kopiert.',
    copyManual: 'Kopieren wurde abgelehnt. Text unten von Hand kopieren:',
    langToggle: 'EN',
  },
};

export function detectLang(storage, navigatorLanguage) {
  let stored = null;
  try { stored = storage ? storage.getItem('gg-lang') : null; } catch (e) { stored = null; }
  if (stored === 'en' || stored === 'de') return stored;
  return String(navigatorLanguage || 'en').toLowerCase().startsWith('de') ? 'de' : 'en';
}

export function createT(lang) {
  const table = STRINGS[lang] || STRINGS.en;
  return (key, params = {}) => {
    const template = table[key] ?? STRINGS.en[key] ?? key;
    return template.replace(/\{(\w+)\}/g, (match, name) => (name in params ? String(params[name]) : match));
  };
}
```

- [ ] **Step 4: Run to verify it passes** — `node --test tests/testhub/strings.test.mjs` — Expected: PASS (3).

- [ ] **Step 5: Commit** — `git add testhub tests && git commit -m "feat(testhub): de/en UI strings driven by gg-lang"`

---

### Task 6: `client.js` for game windows

**Files:** Create `testhub/client.js`; Test `tests/testhub/client.test.mjs`

**Interfaces:** Consumes Task 4's wire format. Produces a classic script defining `window.ggTesthub = { register(id, fn, label?), onScreenshot(fn), setInfo({game, version}) }`, then firing `gg-testhub-ready` on `window` and queueing a first `hello`. Ignores malformed messages, other games' `go`/`screenshot` and any `hello` carrying `targets`.

- [ ] **Step 1: Write the failing test**

```js
import test from 'node:test';
import assert from 'node:assert/strict';
import vm from 'node:vm';
import { readFileSync } from 'node:fs';

const SOURCE = readFileSync(new URL('../../testhub/client.js', import.meta.url), 'utf8');
const PNG = 'data:image/png;base64,iVBORw0KGgo=';
const tick = () => new Promise((resolve) => setTimeout(resolve, 15));

function boot() {
  const posted = [];
  const channels = [];
  const events = [];
  class FakeChannel {
    constructor(name) { this.name = name; channels.push(this); }
    postMessage(m) { posted.push(JSON.parse(JSON.stringify(m))); }
  }
  const win = { BroadcastChannel: FakeChannel, setTimeout, Event: class { constructor(type) { this.type = type; } }, dispatchEvent: (e) => events.push(e.type) };
  win.window = win;
  vm.runInNewContext(SOURCE, win);
  return { api: win.ggTesthub, posted, events, deliver: (m) => channels[0].onmessage({ data: m }) };
}

async function ready(game = 'g') {
  const env = boot();
  env.api.setInfo({ game, version: '1' });
  await tick();
  env.posted.length = 0;
  return env;
}

test('load_firesReadyEventAndSendsFirstHello', async () => {
  const { events, posted } = boot();
  assert.deepEqual(events, ['gg-testhub-ready']);
  await tick();
  assert.deepEqual(posted, [{ type: 'hello', game: '', version: '', targets: [] }]);
});

test('lateRegistration_sendsOneFreshHello_repeatedIdReplaces', async () => {
  const { api, posted, deliver } = await ready();
  const calls = [];
  api.register('j.a', () => calls.push('old'), 'Old');
  api.register('j.a', () => calls.push('new'), 'New');
  api.register('j.b', () => {});
  await tick();
  assert.equal(posted.length, 1);
  assert.deepEqual(posted[0].targets, [{ id: 'j.a', label: 'New' }, { id: 'j.b', label: 'j.b' }]);
  deliver({ type: 'go', game: 'g', id: 'j.a', req: 'r' });
  assert.deepEqual(calls, ['new']);
});

test('go_answersDone_ignoresReturnValue_errorsOnThrowOrUnknownId', async () => {
  const { api, posted, deliver } = await ready();
  api.register('j.hang', () => new Promise(() => {}));
  api.register('j.boom', () => { throw new Error('boom'); });
  await tick();
  posted.length = 0;
  deliver({ type: 'go', game: 'g', id: 'j.hang', req: 'r1' });
  deliver({ type: 'go', game: 'g', id: 'j.boom', req: 'r2' });
  deliver({ type: 'go', game: 'g', id: 'nope', req: 'r3' });
  deliver({ type: 'go', game: 'other', id: 'j.hang', req: 'r4' });
  assert.deepEqual(posted.map((m) => [m.type, m.req]), [['done', 'r1'], ['error', 'r2'], ['error', 'r3']]);
  assert.equal(posted[1].message, 'boom');
});

test('screenshot_returnsPng_orErrors', async () => {
  const { api, posted, deliver } = await ready();
  deliver({ type: 'screenshot', game: 'g', req: 'r0' });
  api.onScreenshot(() => Promise.resolve(PNG));
  deliver({ type: 'screenshot', game: 'g', req: 'r1' });
  await tick();
  api.onScreenshot(() => 'data:text/html;base64,AAAA');
  deliver({ type: 'screenshot', game: 'g', req: 'r2' });
  api.onScreenshot(() => Promise.reject('photo failed'));
  deliver({ type: 'screenshot', game: 'g', req: 'r3' });
  await tick();
  const byReq = Object.fromEntries(posted.map((m) => [m.req, m]));
  assert.equal(byReq.r0.type, 'error');
  assert.deepEqual(byReq.r1, { type: 'png', req: 'r1', dataUrl: PNG });
  assert.equal(byReq.r2.type, 'error');
  assert.deepEqual(byReq.r3, { type: 'error', req: 'r3', message: 'photo failed' });
});

test('malformedMessages_areIgnoredWithoutThrowing', async () => {
  const { api, posted, deliver } = await ready();
  api.register('j.a', () => {});
  await tick();
  posted.length = 0;
  for (const m of [{ type: 'hello', game: 'other', version: '1', targets: [] }, null, 'x', 5, [], {}, { type: 'go' }, { type: 'go', id: '<script>', req: 'r' }, { type: 'go', id: 'j.a', req: 7 }, { type: 'screenshot' }, { type: 'unknown' }]) {
    deliver(m);
  }
  await tick();
  assert.equal(posted.length, 0);
  assert.throws(() => api.register('Bad Id', () => {}), TypeError);
});
```

- [ ] **Step 2: Run to verify it fails** — `node --test tests/testhub/client.test.mjs` — Expected: FAIL, ENOENT reading `testhub/client.js`.

- [ ] **Step 3: Implement**

```js
// Classic script, loaded async by a game in dev mode only. Contract: window.ggTesthub = { setInfo({game, version}) once,
// register(id, fn, label) (sync fn, repeated id replaces), onScreenshot(fn) }; register after 'gg-testhub-ready' fires on window.
(function () {
  'use strict';
  if (window.ggTesthub) return;

  var ID_RE = /^[a-z0-9._-]+$/;
  var PNG_PREFIX = 'data:image/png;base64,';
  var targets = new Map();
  var info = { game: '', version: '' };
  var screenshotFn = null;
  var helloQueued = false;
  var channel = null;
  try { channel = new BroadcastChannel('gg-testhub'); } catch (e) { channel = null; }

  function send(message) { if (channel) channel.postMessage(message); }
  function isText(v, max) { return typeof v === 'string' && v.length <= max; }
  function isOptionalText(v) { return v === undefined || isText(v, 100); }

  function sendHello() {
    helloQueued = false;
    var list = [];
    targets.forEach(function (target, id) { list.push({ id: id, label: target.label }); });
    send({ type: 'hello', game: info.game, version: info.version, targets: list });
  }

  function queueHello() {
    if (helloQueued) return;
    helloQueued = true;
    setTimeout(sendHello, 0);
  }

  function fail(req, err) {
    send({ type: 'error', req: req || '', message: String(err && err.message ? err.message : err).slice(0, 500) });
  }

  function parse(m) {
    if (!m || typeof m !== 'object' || Array.isArray(m) || typeof m.type !== 'string') return null;
    if (m.type === 'hello') return m.targets === undefined ? { type: 'hello' } : null;
    if (!isOptionalText(m.game) || !isOptionalText(m.req)) return null;
    if (m.type === 'go') return isText(m.id, 100) && ID_RE.test(m.id) ? { type: 'go', game: m.game, id: m.id, req: m.req } : null;
    if (m.type === 'screenshot') return isText(m.req, 100) ? { type: 'screenshot', game: m.game, req: m.req } : null;
    return null;
  }

  function onGo(m) {
    var target = targets.get(m.id);
    if (!target) { fail(m.req, 'unknown target ' + m.id); return; }
    try { target.fn(); } catch (err) { fail(m.req, err); return; }
    send({ type: 'done', req: m.req || '' });
  }

  function onScreenshotRequest(m) {
    if (!screenshotFn) { fail(m.req, 'no screenshot handler'); return; }
    Promise.resolve().then(screenshotFn).then(function (url) {
      if (typeof url !== 'string' || url.indexOf(PNG_PREFIX) !== 0) throw new Error('screenshot is not a PNG data URL');
      send({ type: 'png', req: m.req, dataUrl: url });
    }).catch(function (err) { fail(m.req, err); });
  }

  if (channel) {
    channel.onmessage = function (event) {
      var m = parse(event.data);
      if (!m) return;
      if (m.type === 'hello') { sendHello(); return; }
      if (m.game && info.game && m.game !== info.game) return;
      if (m.type === 'go') onGo(m); else onScreenshotRequest(m);
    };
  }

  window.ggTesthub = {
    register: function (id, fn, label) {
      if (typeof id !== 'string' || !ID_RE.test(id)) throw new TypeError('ggTesthub.register: id must match [a-z0-9._-]+');
      if (typeof fn !== 'function') throw new TypeError('ggTesthub.register: fn must be a function');
      targets.set(id, { fn: fn, label: label ? String(label) : id });
      queueHello();
    },
    onScreenshot: function (fn) {
      if (typeof fn !== 'function') throw new TypeError('ggTesthub.onScreenshot: fn must be a function');
      screenshotFn = fn;
    },
    setInfo: function (next) {
      info = { game: String((next && next.game) || ''), version: String((next && next.version) || '') };
      queueHello();
    },
  };

  window.dispatchEvent(new Event('gg-testhub-ready'));
  queueHello();
})();
```

- [ ] **Step 4: Run to verify it passes** — `node --test tests/testhub/*.test.mjs` — Expected: PASS (all).

- [ ] **Step 5: Commit** — `git add testhub tests && git commit -m "feat(testhub): client.js registers jump targets and answers the hub"`

---

### Task 7: Hub page shell, list rendering, e2e harness

**Files:** Create `testhub/{index.html,style.css,dom.js,list.js,app.js}`, `tests/testhub/fixtures/{test-todo.md,fake-game.html}`, `tests/test_testhub_e2e.py`

**Interfaces:** Consumes Tasks 1, 2, 5. Produces `h(tag, props, ...children)` (`on*` props are listeners, `class` sets className, `true`/`false`/`null` as attribute values set or skip, never `innerHTML`); `renderList(view)` with `view = { t, blocks, store, filter, query, expanded:Set, collapsed:Map, drafts:Map, errors:Map, conn:{version,targets}|null, actions:{toggleItem, toggleBlock, go, shot, save, done} }`, rendering `li.item` with `button.text` and a Go control (`button.go`, disabled without `conn`; grey `span.go-unknown` for a tag not in `conn.targets`); `app.js` with `GAMES` and `?game=<slug>` (`[a-z0-9-]+`, appended to the picker if unknown). E2E helpers `new_context`, `open_game`, `open_hub`, `item` on `ORIGIN = http://localhost:4173` (a secure context, so the Clipboard API works).

- [ ] **Step 1: Write fixtures and the failing e2e tests**

`tests/testhub/fixtures/test-todo.md`:

```markdown
# Playtest list

## Alpha block {go: fake.alpha}
- [ ] First item inherits the block tag
- [ ] Second item has its own tag {go: fake.beta}
- [x] Already tested item

## Beta block
- [ ] Typo tag item {go: fake.typo}
- [ ] Plain item without tag
```

`tests/testhub/fixtures/fake-game.html` (loads the client async like a real game, registers on `gg-testhub-ready`, registers one target late, screenshot behaviour switched via `window.__shot`):

```html
<!doctype html>
<meta charset="utf-8">
<title>Fake game</title>
<script>
  window.__at = null;
  window.__shot = 'ok'; // 'ok' | 'reject' | 'hang'
  var PNG = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==';
  function boot() {
    ggTesthub.setInfo({ game: 'fake', version: '1.2.3' });
    ggTesthub.register('fake.alpha', function () { window.__at = 'alpha'; }, 'Alpha spot');
    ggTesthub.onScreenshot(function () {
      if (window.__shot === 'hang') return new Promise(function () {});
      if (window.__shot === 'reject') return Promise.reject('photo failed');
      return Promise.resolve(PNG);
    });
    setTimeout(function () { ggTesthub.register('fake.beta', function () { window.__at = 'beta'; }, 'Late spot'); }, 200);
  }
  if (window.ggTesthub) boot(); else window.addEventListener('gg-testhub-ready', boot);
  var s = document.createElement('script');
  s.src = '/testhub/client.js';
  s.async = true;
  document.head.appendChild(s);
</script>
```

`tests/test_testhub_e2e.py`:

```python
"""Headless end-to-end tests for testhub/: the hub and a fake game in two pages of one browser context."""
import re
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest
from playwright.sync_api import expect, sync_playwright

ROOT = Path(__file__).parent.parent
FIXTURES = Path(__file__).parent / "testhub" / "fixtures"
ORIGIN = "http://localhost:4173"
TZ = "Europe/Zurich"
TYPES = {".html": "text/html; charset=utf-8", ".js": "text/javascript; charset=utf-8",
         ".css": "text/css; charset=utf-8", ".md": "text/markdown; charset=utf-8"}


def serve(route, request, todo):
    path = request.url.removeprefix(ORIGIN).split("?")[0]
    source = None
    if path == "/game-fake/test-todo.md":
        source = FIXTURES / "test-todo.md" if todo else None
    elif path == "/game-fake/":
        source = FIXTURES / "fake-game.html"
    elif path == "/testhub/":
        source = ROOT / "testhub" / "index.html"
    elif path.startswith("/testhub/") and ".." not in path:
        source = ROOT / path.lstrip("/")
    if source is None or not source.is_file():
        return route.fulfill(status=404, body="not found")
    route.fulfill(status=200, body=source.read_bytes(), content_type=TYPES.get(source.suffix, "application/octet-stream"))


def new_context(browser, todo=True, **kwargs):
    ctx = browser.new_context(locale="en-GB", timezone_id=TZ, accept_downloads=True,
                              permissions=["clipboard-read", "clipboard-write"], **kwargs)
    ctx.route(f"{ORIGIN}/**", lambda route, request: serve(route, request, todo))
    return ctx


def open_game(ctx):
    game = ctx.new_page()
    game.goto(f"{ORIGIN}/game-fake/")
    return game


def open_hub(ctx, errors=None, init_script=None):
    hub = ctx.new_page()
    if errors is not None:
        hub.on("pageerror", lambda e: errors.append(str(e)))
    if init_script:
        hub.add_init_script(init_script)
    hub.goto(f"{ORIGIN}/testhub/?game=fake")
    expect(hub.locator(".status")).to_be_visible()
    return hub


def item(hub, text):
    return hub.locator(".item", has_text=text)


@pytest.fixture(scope="module")
def browser():
    with sync_playwright() as p:
        b = p.chromium.launch()
        yield b
        b.close()


@pytest.fixture
def ctx(browser):
    c = new_context(browser)
    yield c
    c.close()


def test_list_showsOpenItemsOnly_tagsStripped_noGameIsRed(ctx):
    errors = []
    hub = open_hub(ctx, errors)
    expect(hub.locator(".item")).to_have_count(4)
    expect(item(hub, "Second item has its own tag")).to_have_text(re.compile(r"^\s*☐ Second item has its own tag\s*Go"))
    expect(hub.locator(".block", has_text="Alpha block").locator(".progress")).to_have_text("0 / 2 ✓")
    expect(hub.locator(".status.off")).to_contain_text("No game window")
    expect(hub.locator(".status a")).to_have_attribute("href", "/game-fake/?dev=1")
    expect(item(hub, "First item").locator("button.go")).to_be_disabled()
    assert errors == []


def test_missingTodo_showsMessage_hubStillOpens(browser):
    ctx = new_context(browser, todo=False)
    try:
        hub = open_hub(ctx)
        expect(hub.locator(".load-error")).to_contain_text("Could not load test-todo.md for fake")
        expect(hub.locator(".toolbar")).to_be_visible()
    finally:
        ctx.close()


def test_storageUnavailable_warnsAndStillRenders(ctx):
    hub = open_hub(ctx, init_script="Object.defineProperty(window,'localStorage',{get(){throw new Error('denied')}})")
    expect(hub.locator(".notice.warn")).to_contain_text("notes are kept for this session only")
    expect(hub.locator(".item")).to_have_count(4)
```

- [ ] **Step 2: Run to verify it fails** — `.venv/bin/pytest tests/test_testhub_e2e.py -v` — Expected: FAIL (`testhub/index.html` 404, `.status` never appears).

- [ ] **Step 3: Implement**

`testhub/dom.js`:

```js
export function h(tag, props = {}, ...children) {
  const el = document.createElement(tag);
  for (const [name, value] of Object.entries(props)) {
    if (name.startsWith('on')) el.addEventListener(name.slice(2), value);
    else if (name === 'class') el.className = value;
    else if (value === true) el.setAttribute(name, '');
    else if (value !== false && value !== null && value !== undefined) el.setAttribute(name, value);
  }
  for (const child of children.flat()) {
    if (child !== null && child !== undefined && child !== false) el.append(child);
  }
  return el;
}
```

`testhub/list.js`:

```js
import { h } from './dom.js';

function matchesFilter(view, block, item) {
  const entry = view.store.get(item.key);
  if (view.filter === 'open' && entry.status === 'done') return false;
  if (view.filter === 'noted' && entry.status !== 'noted') return false;
  if (view.filter === 'done' && entry.status !== 'done') return false;
  const query = view.query.trim().toLowerCase();
  return !query || `${block.heading} ${item.text} ${entry.note}`.toLowerCase().includes(query);
}

function goControl(view, item) {
  if (!item.tag) return null;
  const { t, conn } = view;
  if (!conn) return h('button', { class: 'go', disabled: true, title: item.tag }, t('go'));
  if (!conn.targets.some((target) => target.id === item.tag)) {
    return h('span', { class: 'go-unknown', title: t('goUnknown') }, item.tag);
  }
  return h('button', { class: 'go', onclick: () => view.actions.go(item) }, t('go'));
}

function renderItem(view, item) {
  const entry = view.store.get(item.key);
  const open = view.expanded.has(item.key);
  const error = view.errors.get(item.key);
  return h('li', { class: `item ${entry.status}${open ? ' expanded' : ''}`, 'data-key': item.key },
    h('div', { class: 'row' },
      h('button', { class: 'text', 'aria-expanded': String(open), onclick: () => view.actions.toggleItem(item.key) },
        h('span', { class: 'box' }, entry.status === 'done' ? '☑' : '☐'), ' ', item.text),
      goControl(view, item)),
    error ? h('p', { class: 'error', role: 'alert' }, error) : null);
}

function renderBlock(view, block) {
  const visible = block.items.filter((item) => matchesFilter(view, block, item));
  if (visible.length === 0) return null;
  const done = block.items.filter((item) => view.store.get(item.key).status === 'done').length;
  const total = block.items.length;
  const collapsed = view.collapsed.has(block.heading) ? view.collapsed.get(block.heading) : done === total;
  return h('section', { class: 'block', 'data-block': block.heading },
    h('button', { class: 'block-head', 'aria-expanded': String(!collapsed), onclick: () => view.actions.toggleBlock(block.heading, collapsed) },
      h('span', { class: 'block-title' }, `${collapsed ? '▸' : '▾'} ${block.heading}`),
      h('span', { class: 'progress' }, `${done} / ${total} ✓`)),
    collapsed ? null : h('ul', {}, visible.map((item) => renderItem(view, item))));
}

export function renderList(view) {
  const blocks = view.blocks.map((block) => renderBlock(view, block)).filter(Boolean);
  return blocks.length === 0 ? h('p', { class: 'empty' }, view.t('noItems')) : h('div', { class: 'list' }, blocks);
}
```

`testhub/app.js`:

```js
import { h } from './dom.js';
import { parseTodo } from './parser.js';
import { getStorage, createStore } from './store.js';
import { createT, detectLang } from './strings.js';
import { renderList } from './list.js';

export const GAMES = ['rhyflitzer', 'wipfelkratzer'];
const SLUG_RE = /^[a-z0-9-]+$/;

const requested = new URLSearchParams(location.search).get('game');
const game = requested && SLUG_RE.test(requested) ? requested : GAMES[0];
const games = GAMES.includes(game) ? GAMES : [...GAMES, game];
const storage = getStorage();
const store = createStore(storage);
let lang = detectLang(storage, navigator.language);
let t = createT(lang);
let link = null; // created in Task 8

const ui = {
  blocks: [], loadError: null, filter: 'open', query: '',
  expanded: new Set(), collapsed: new Map(), drafts: new Map(), errors: new Map(),
};
const conn = () => (link ? link.conn : null);

function captureFocus() {
  const el = document.activeElement;
  if (!el || !el.dataset || !el.dataset.focus) return null;
  return { id: el.dataset.focus, start: el.selectionStart };
}

function restoreFocus(saved) {
  const el = saved && document.querySelector(`[data-focus="${CSS.escape(saved.id)}"]`);
  if (!el) return;
  el.focus();
  if (typeof saved.start === 'number') el.setSelectionRange(saved.start, saved.start);
}

const actions = {
  toggleItem(key) {
    if (ui.expanded.has(key)) ui.expanded.delete(key); else ui.expanded.add(key);
    render();
  },
  toggleBlock(heading, wasCollapsed) {
    ui.collapsed.set(heading, !wasCollapsed);
    render();
  },
};

const view = () => ({ ...ui, t, store, conn: conn(), actions });

function switchLang() {
  lang = lang === 'en' ? 'de' : 'en';
  t = createT(lang);
  try { if (storage) storage.setItem('gg-lang', lang); } catch (e) { /* stays for this session */ }
  render();
}

function header() {
  const picker = h('select', { class: 'picker', 'aria-label': 'Game', onchange: (e) => { location.search = `?game=${e.target.value}`; } },
    games.map((g) => h('option', { value: g, selected: g === game }, g)));
  return h('header', { class: 'head' }, h('h1', {}, t('title')), picker,
    h('button', { class: 'lang', type: 'button', onclick: switchLang }, t('langToggle')));
}

const copyButton = () => null; // replaced in Task 9

function statusBar() {
  const c = conn();
  const line = c
    ? h('span', {}, '● ', t('connected', { version: c.version, n: c.targets.length }))
    : h('span', {}, '● ', t('disconnected'), ' ',
      h('a', { href: `/game-${game}/?dev=1`, target: '_blank', rel: 'noopener' }, t('openGame')));
  return h('div', { class: `status ${c ? 'on' : 'off'}` }, line, copyButton());
}

function toolbar() {
  const radios = ['open', 'noted', 'done'].map((f) => h('label', {},
    h('input', { type: 'radio', name: 'filter', value: f, checked: ui.filter === f, onchange: () => { ui.filter = f; render(); } }),
    ' ', t(`filter_${f}`)));
  const search = h('input', {
    type: 'search', class: 'search', placeholder: t('search'), value: ui.query, 'data-focus': 'search',
    oninput: (e) => { ui.query = e.target.value; render(); },
  });
  return h('div', { class: 'toolbar' }, radios, search);
}

function notices() {
  return [store.isPersistent() ? null : h('p', { class: 'notice warn' }, t('noStorage'))];
}

function body() {
  if (ui.loadError) return h('p', { class: 'load-error' }, t('loadError', { game, reason: ui.loadError }));
  return renderList(view());
}

function render() {
  const focus = captureFocus();
  document.getElementById('app').replaceChildren(header(), statusBar(), toolbar(), ...notices(), body());
  restoreFocus(focus);
}

async function loadTodo() {
  try {
    const response = await fetch(`/game-${game}/test-todo.md`, { cache: 'no-store' });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    ui.blocks = parseTodo(await response.text(), game);
    ui.loadError = null;
  } catch (e) {
    ui.blocks = [];
    ui.loadError = e.message;
  }
  render();
}

render();
loadTodo();
```

`testhub/index.html`:

```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Testhub</title>
  <link rel="stylesheet" href="./style.css">
</head>
<body>
  <div id="app"></div>
  <script type="module" src="./app.js"></script>
</body>
</html>
```

`testhub/style.css` (fluid, narrow-strip friendly):

```css
* { box-sizing: border-box; }
body { margin: 0; font: 15px/1.4 system-ui, sans-serif; color-scheme: dark light; }
#app { padding: 8px 12px; }
button, input, select, textarea { font: inherit; }
.head, .status, .toolbar, .buttons, .chips, .item .row { display: flex; flex-wrap: wrap; gap: 6px 10px; align-items: center; }
.head h1 { font-size: 1.1rem; margin: 0 auto 0 0; }
.status { justify-content: space-between; overflow-wrap: anywhere; }
.status.on, .notice.ok { color: #2e9e5b; }
.status.off, .notice.warn, .error, .load-error { color: #d64545; }
.search { flex: 1 1 8rem; min-width: 0; }
.block-head { display: flex; justify-content: space-between; gap: 8px; width: 100%; }
.block-title, .item .text { overflow-wrap: anywhere; min-width: 0; text-align: left; }
.item .text { flex: 1; border: 0; background: none; }
.item.done .text, .progress, .chip, .go-unknown { opacity: .6; }
ul { list-style: none; margin: 0; padding-left: 12px; }
.note, .export-box { width: 100%; }
```

- [ ] **Step 4: Run to verify it passes** — `.venv/bin/pytest tests/test_testhub_e2e.py -v` — Expected: PASS (3).

- [ ] **Step 5: Commit** — `git add testhub tests && git commit -m "feat(testhub): hub page lists open test-todo items per game"`

---

### Task 8: Game connection, Go, screenshot download

**Files:** Create `testhub/link.js`; Modify `testhub/app.js`, `testhub/list.js`; Test `tests/test_testhub_e2e.py` (append)

**Interfaces:** Produces `createLink({game, onChange, timeoutMs?}) -> { get conn(): {version, targets, seen}|null, go(id), screenshot() }`; requests resolve with the answering message or reject with an `Error` whose `code` is `timeout` (10 s), `noGame`, or `remote` (the game's message). `onChange` fires when connection or target list changes; the hub sends `hello` on creation and every 10 s and drops a connection silent for 25 s. `app.js` gains actions `go(item)`, `shot(item)`; `list.js` gains `editor(view, item, entry)` (extended in Task 9).

- [ ] **Step 1: Append the failing e2e tests**

```python
def mmdd():
    return datetime.now(ZoneInfo(TZ)).strftime("%m%d")


def test_connected_greyTag_lateTarget_goRunsInGame(ctx):
    game = open_game(ctx)
    hub = open_hub(ctx)
    expect(hub.locator(".status.on")).to_contain_text("v1.2.3 · 2 targets")  # fake.beta registers 200 ms late
    expect(item(hub, "Typo tag item").locator(".go-unknown")).to_have_text("fake.typo")
    item(hub, "First item inherits").locator("button.go").click()
    game.wait_for_function("window.__at === 'alpha'")
    item(hub, "Second item").locator("button.go").click()
    game.wait_for_function("window.__at === 'beta'")


def test_screenshot_downloadsNumberedFiles(ctx):
    open_game(ctx)
    hub = open_hub(ctx)
    expect(hub.locator(".status.on")).to_be_visible()
    row = item(hub, "First item inherits")
    row.locator("button.text").click()
    with hub.expect_download() as first:
        row.locator("button.shot").click()
    assert first.value.suggested_filename == f"fb-fake-{mmdd()}-1.png"
    expect(row.locator(".chip")).to_have_text(f"📷 fb-fake-{mmdd()}-1.png ✓")
    with hub.expect_download() as second:
        row.locator("button.shot").click()
    assert second.value.suggested_filename == f"fb-fake-{mmdd()}-2.png"


def test_screenshot_withoutAnswer_showsTimeoutError(ctx):
    game = open_game(ctx)
    game.evaluate("window.__shot = 'hang'")
    hub = ctx.new_page()
    hub.clock.install()
    hub.goto(f"{ORIGIN}/testhub/?game=fake")
    expect(hub.locator(".status.on")).to_be_visible()
    row = item(hub, "First item inherits")
    row.locator("button.text").click()
    row.locator("button.shot").click()
    hub.clock.run_for(11000)
    expect(row.locator(".error")).to_contain_text("No answer from the game within 10 s")


def test_screenshot_rejected_showsGameMessage_andStoresNothing(ctx):
    game = open_game(ctx)
    game.evaluate("window.__shot = 'reject'")
    hub = open_hub(ctx)
    expect(hub.locator(".status.on")).to_be_visible()
    row = item(hub, "First item inherits")
    row.locator("button.text").click()
    row.locator("button.shot").click()
    expect(row.locator(".error")).to_have_text("photo failed")
```

- [ ] **Step 2: Run to verify it fails** — `.venv/bin/pytest tests/test_testhub_e2e.py -v -k "connected or screenshot"` — Expected: FAIL (status never green; no `button.shot`).

- [ ] **Step 3: Implement**

`testhub/link.js`:

```js
import { CHANNEL, validateGameMessage, helloMsg, goMsg, screenshotMsg, newReq } from './protocol.js';

export const REQUEST_TIMEOUT_MS = 10000;
const POLL_MS = 10000;
const STALE_MS = 25000;

function linkError(code, message) {
  const error = new Error(message || code);
  error.code = code;
  return error;
}

const signature = (c) => (c ? `${c.version}|${c.targets.map((x) => x.id).join(',')}` : '');

export function createLink({ game, onChange, timeoutMs = REQUEST_TIMEOUT_MS }) {
  const channel = typeof BroadcastChannel === 'function' ? new BroadcastChannel(CHANNEL) : null;
  const pending = new Map();
  let conn = null;

  function setConn(next) {
    const changed = signature(next) !== signature(conn);
    conn = next;
    if (changed) onChange();
  }

  function settle(msg) {
    const entry = pending.get(msg.req);
    if (!entry) return;
    pending.delete(msg.req);
    clearTimeout(entry.timer);
    if (msg.type === 'error') entry.reject(linkError('remote', msg.message)); else entry.resolve(msg);
  }

  function onMessage(raw) {
    const msg = validateGameMessage(raw);
    if (!msg) return;
    if (msg.type !== 'hello') { settle(msg); return; }
    if (msg.game === game) setConn({ version: msg.version, targets: msg.targets, seen: Date.now() });
  }

  function request(build) {
    if (!channel || !conn) return Promise.reject(linkError('noGame'));
    const req = newReq();
    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => { pending.delete(req); reject(linkError('timeout')); }, timeoutMs);
      pending.set(req, { resolve, reject, timer });
      channel.postMessage(build(req));
    });
  }

  const hello = () => { if (channel) channel.postMessage(helloMsg()); };

  if (channel) channel.onmessage = (event) => onMessage(event.data);
  setInterval(() => {
    hello();
    if (conn && Date.now() - conn.seen > STALE_MS) setConn(null);
  }, POLL_MS);
  hello();

  return {
    get conn() { return conn; },
    go: (id) => request((req) => goMsg(game, id, req)),
    screenshot: () => request((req) => screenshotMsg(game, req)),
  };
}
```

`testhub/app.js` edits:

1. Add `import { createLink } from './link.js';` with the other imports.
2. Replace `let link = null; // created in Task 8` with:

```js
const link = createLink({
  game,
  onChange: () => { if (link.conn) store.setVersion(game, link.conn.version); render(); },
});
```

3. Replace `const conn = () => (link ? link.conn : null);` with `const conn = () => link.conn;`
4. Add before `const actions`:

```js
const errorText = (error) => (error.code && error.code !== 'remote' ? t(`err_${error.code}`) : error.message);

function download(dataUrl, name) {
  const anchor = h('a', { href: dataUrl, download: name });
  document.body.append(anchor);
  anchor.click();
  anchor.remove();
}
```

5. Add inside `actions`:

```js
  async go(item) {
    ui.errors.delete(item.key);
    try { await link.go(item.tag); } catch (error) { ui.errors.set(item.key, errorText(error)); }
    render();
  },
  async shot(item) {
    ui.errors.delete(item.key);
    try {
      const png = await link.screenshot();
      const name = store.nextShotName(game, new Date());
      download(png.dataUrl, name);
      store.update(item.key, { screenshots: [...store.get(item.key).screenshots, name] });
    } catch (error) {
      ui.errors.set(item.key, errorText(error));
    }
    render();
  },
```

`testhub/list.js`: add the editor and render it in `renderItem` (after the `error ? ... : null` argument add `, open ? editor(view, item, entry) : null`):

```js
function editor(view, item, entry) {
  const { t, conn, actions } = view;
  return h('div', { class: 'editor' },
    h('div', { class: 'chips' }, entry.screenshots.map((name) => h('span', { class: 'chip' }, `📷 ${name} ✓`))),
    h('div', { class: 'buttons' },
      h('button', { class: 'shot', type: 'button', disabled: !conn, onclick: () => actions.shot(item) }, t('shot'))));
}
```

- [ ] **Step 4: Run to verify it passes** — `.venv/bin/pytest tests/test_testhub_e2e.py -v` — Expected: PASS.

- [ ] **Step 5: Commit** — `git add testhub tests && git commit -m "feat(testhub): connect to the game window, Go jumps, screenshot download"`

---

### Task 9: Notes, Done, filter/search, Copy all with clipboard fallback

**Files:** Modify `testhub/list.js`, `testhub/app.js`; Test `tests/test_testhub_e2e.py` (append)

**Interfaces:** Consumes `buildExport`, `isoDate` (Task 3). Produces actions `save(item)` (status `noted`; ignored when note and screenshots are empty), `done(item)` (status `done`), `copyAll()`; `button.copy-all` ("Copy all N", disabled at 0; N = items `noted`/`done` and not `sent`). If the clipboard is refused, the block shows in a pre-selected `textarea.export-box` and the entries are marked sent.

- [ ] **Step 1: Append the failing e2e tests**

```python
def add_note(hub, text, note):
    row = item(hub, text)
    row.locator("button.text").click()
    row.locator("textarea.note").fill(note)
    row.locator("button.save").click()


def test_noteAndDone_copyAllExportsExactBlock_andMarksSent(ctx):
    open_game(ctx)
    hub = open_hub(ctx)
    expect(hub.locator(".status.on")).to_be_visible()
    add_note(hub, "First item inherits", "Turm zu dunkel")
    typo = item(hub, "Typo tag item")
    typo.locator("button.text").click()
    typo.locator("button.done").click()
    expect(hub.locator("button.copy-all")).to_have_text("Copy all 2")
    hub.bring_to_front()
    hub.locator("button.copy-all").click()
    expect(hub.locator(".notice.ok")).to_contain_text("Copied 2 entries")
    date = datetime.now(ZoneInfo(TZ)).strftime("%Y-%m-%d")
    assert hub.evaluate("navigator.clipboard.readText()") == "\n".join([
        f"Testhub feedback — fake v1.2.3 — {date}",
        '- [Alpha block · "First item inherits the block tag" · go:fake.alpha] Turm zu dunkel',
        '- ✓ tested: [Beta block · "Typo tag item"]',
    ])
    expect(hub.locator("button.copy-all")).to_have_text("Copy all 0")
    expect(hub.locator("button.copy-all")).to_be_disabled()


def test_stateSurvivesReload_doneHiddenUnderOpen_search(ctx):
    hub = open_hub(ctx)
    add_note(hub, "Plain item", "findme")
    typo = item(hub, "Typo tag item")
    typo.locator("button.text").click()
    typo.locator("button.done").click()
    expect(item(hub, "Typo tag item")).to_have_count(0)
    hub.reload()
    expect(hub.locator(".item")).to_have_count(3)
    hub.locator("input.search").fill("findme")
    expect(hub.locator(".item")).to_have_count(1)
    hub.locator("input.search").fill("")
    hub.locator("input[value=done]").check()
    expect(hub.locator(".block", has_text="Beta block").locator(".progress")).to_have_text("1 / 2 ✓")


def test_clipboardRefused_showsTextareaWithBlock(ctx):
    hub = open_hub(ctx, init_script="Object.defineProperty(navigator,'clipboard',{value:{writeText:()=>Promise.reject(new Error('no'))}})")
    add_note(hub, "Plain item", "x")
    hub.locator("button.copy-all").click()
    expect(hub.locator("textarea.export-box")).to_have_value(
        re.compile(r"^Testhub feedback — fake .* — \d{4}-\d\d-\d\d\n- \[Beta block · \"Plain item\"\] x$"))
    expect(hub.locator("button.copy-all")).to_have_text("Copy all 0")
```

- [ ] **Step 2: Run to verify it fails** — `.venv/bin/pytest tests/test_testhub_e2e.py -v -k "note or Reload or clipboard"` — Expected: FAIL (`textarea.note`, `button.copy-all` missing).

- [ ] **Step 3: Implement**

`testhub/list.js`: replace `editor` with the full version:

```js
function editor(view, item, entry) {
  const { t, conn, actions, drafts } = view;
  const draft = drafts.has(item.key) ? drafts.get(item.key) : entry.note;
  const area = h('textarea', {
    class: 'note', rows: 3, placeholder: t('notePlaceholder'), 'data-focus': `note:${item.key}`,
    oninput: (e) => drafts.set(item.key, e.target.value),
  }, draft);
  return h('div', { class: 'editor' }, area,
    h('div', { class: 'chips' }, entry.screenshots.map((name) => h('span', { class: 'chip' }, `📷 ${name} ✓`))),
    h('div', { class: 'buttons' },
      h('button', { class: 'shot', type: 'button', disabled: !conn, onclick: () => actions.shot(item) }, t('shot')),
      h('button', { class: 'save', type: 'button', onclick: () => actions.save(item) }, t('save')),
      h('button', { class: 'done', type: 'button', onclick: () => actions.done(item) }, t('done'))));
}
```

`testhub/app.js` edits:

1. Import: `import { buildExport, isoDate } from './export.js';`
2. Extend `ui` with `notice: null, manual: null` (`manual` = export text while the fallback panel shows).
3. Add before `const actions`:

```js
const draftFor = (item) => (ui.drafts.has(item.key) ? ui.drafts.get(item.key) : store.get(item.key).note);

function collectUnsent() {
  const entries = [];
  for (const block of ui.blocks) {
    for (const item of block.items) {
      const entry = store.get(item.key);
      if (entry.sent || (entry.status !== 'noted' && entry.status !== 'done')) continue;
      entries.push({ key: item.key, block: block.heading, text: item.text, tag: item.tag, status: entry.status, note: entry.note, screenshots: entry.screenshots });
    }
  }
  return entries;
}

const markSent = (entries) => entries.forEach((entry) => store.update(entry.key, { sent: true }));

async function copyAll() {
  const entries = collectUnsent();
  if (entries.length === 0) return;
  const version = (conn() && conn().version) || store.version(game);
  const text = buildExport({ game, version, date: isoDate(new Date()), entries });
  ui.notice = ui.manual = null;
  try {
    await navigator.clipboard.writeText(text);
    ui.notice = t('copied', { n: entries.length });
  } catch (error) {
    ui.manual = text;
  }
  markSent(entries);
  render();
}
```

4. Add inside `actions`:

```js
  save(item) {
    const note = draftFor(item);
    if (!note.trim() && store.get(item.key).screenshots.length === 0) return;
    store.update(item.key, { status: 'noted', note });
    render();
  },
  done(item) {
    store.update(item.key, { status: 'done', note: draftFor(item) });
    render();
  },
  copyAll,
```

5. Replace the `copyButton` stub and `notices`:

```js
function copyButton() {
  const n = collectUnsent().length;
  return h('button', { class: 'copy-all', type: 'button', disabled: n === 0, onclick: actions.copyAll }, t('copyAll', { n }));
}

function notices() {
  return [
    store.isPersistent() ? null : h('p', { class: 'notice warn' }, t('noStorage')),
    ui.notice ? h('p', { class: 'notice ok' }, ui.notice) : null,
    ui.manual ? h('div', { class: 'notice' }, h('p', {}, t('copyManual')),
      h('textarea', { class: 'export-box', readonly: true, 'data-focus': 'export' }, ui.manual)) : null,
  ];
}
```

6. At the end of `render()` add: `const box = document.querySelector('.export-box'); if (box) box.select();`

- [ ] **Step 4: Run to verify it passes** — `.venv/bin/pytest tests/test_testhub_e2e.py -v && node --test tests/testhub/*.test.mjs` — Expected: PASS.

- [ ] **Step 5: Commit** — `git add testhub tests && git commit -m "feat(testhub): notes, done marks, filters and Copy all with clipboard fallback"`

---

### Task 10: Hardening tests (foreign messages, second game, narrow window, German)

**Files:** Test `tests/test_testhub_e2e.py` (append). Production code changes only if a test fails: fix the owning module, not the test.

**Interfaces:** Pins Review Focus 1-2, the narrow layout and `gg-lang`.

- [ ] **Step 1: Append the tests**

```python
def test_foreignMessagesAndOtherGame_areIgnored(ctx):
    errors = []
    game = open_game(ctx)
    game.on("pageerror", lambda e: errors.append(str(e)))
    hub = open_hub(ctx, errors)
    expect(hub.locator(".status.on")).to_contain_text("v1.2.3 · 2 targets")
    game.evaluate("""() => {
      const c = new BroadcastChannel('gg-testhub');
      c.postMessage({ type: 'hello', game: 'fake', version: '9', targets: 'nope' });
      c.postMessage({ type: 'hello', game: 'other', version: '7.7.7', targets: [] });
      c.postMessage('garbage');
    }""")
    hub.wait_for_timeout(300)
    expect(hub.locator(".status.on")).to_contain_text("v1.2.3 · 2 targets")
    assert game.evaluate("window.__at") is None
    assert errors == []


def test_narrowWindow_hasNoHorizontalScroll(browser):
    ctx = new_context(browser, viewport={"width": 360, "height": 700})
    try:
        open_game(ctx)
        hub = open_hub(ctx)
        expect(hub.locator(".status.on")).to_be_visible()
        item(hub, "Second item has its own tag").locator("button.text").click()
        assert hub.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
    finally:
        ctx.close()


def test_ggLang_de_switchesUiStrings(ctx):
    hub = open_hub(ctx, init_script="localStorage.setItem('gg-lang','de')")
    expect(hub.locator("button.copy-all")).to_have_text("Alle kopieren 0")
    hub.locator("button.lang").click()
    expect(hub.locator("button.copy-all")).to_have_text("Copy all 0")
```

- [ ] **Step 2: Run** — `.venv/bin/pytest tests/test_testhub_e2e.py -v` — Expected: PASS. A failure is a real defect: fix the owning module and re-run the suite.

- [ ] **Step 3: Commit** — `git add tests && git commit -m "test(testhub): pin foreign messages, second game, narrow layout and German UI"`

---

### Task 11: Documentation

**Files:** Modify `CLAUDE.md`, `CONTRIBUTING.md`

- [ ] **Step 1:** Add to `CLAUDE.md` (after the Umami section) a "Testhub" section: `/testhub/` lists each game's open `test-todo.md` items, jumps the game to the place an item is about and exports notes with Copy all; spec in `freaxnx01/game-rhyflitzer` `docs/superpowers/specs/2026-10-11-testhub-design.md`; add a game by appending its slug to `GAMES` in `testhub/app.js`; a game loads `/testhub/client.js` async in dev mode only (`?dev=1`) and registers after the `gg-testhub-ready` event (contract in the header comment of `testhub/client.js`); items are tagged `{go: <id>}`; tests: `node --test tests/testhub/*.test.mjs` and `.venv/bin/pytest tests/test_testhub_e2e.py`.

- [ ] **Step 2:** In `CONTRIBUTING.md` replace `There is no test suite.` with `Tests live in tests/ (pytest + Playwright in .venv; node --test for testhub/).` and add the Layout line `- testhub/ — the playtest hub and client.js, the one script games load in dev mode.`

- [ ] **Step 3: Run the whole suite** — `node --test tests/testhub/*.test.mjs && .venv/bin/pytest tests -v` — Expected: PASS. Then `git add CLAUDE.md CONTRIBUTING.md && git commit -m "docs(testhub): document the hub, client contract and test commands"`.
