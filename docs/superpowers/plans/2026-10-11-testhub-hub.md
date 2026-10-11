# Testhub Hub Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A playtest hub page at `/testhub/` plus a one-copy-for-all-games `client.js`, so the maintainer sees only untested `test-todo.md` items per game, jumps to each with one click, attaches notes and screenshots, and exports everything with **Copy all**.

**Architecture:** Pure ES modules (`parser`, `store`, `export`, `protocol`, `strings`) are unit-tested with `node --test`. The hub UI (`app.js`, `list.js`, `link.js`) renders with plain DOM calls and talks to game windows over `BroadcastChannel('gg-testhub')`. `client.js` is a classic (non-module) script so any game can load it with a plain `<script src>`. One Python Playwright test opens the hub and a fake game in two pages of one browser context, both served by `context.route` on a fixed origin, so no server is needed.

**Tech Stack:** Vanilla JS (ES modules, no framework, no build step, no `package.json` unless Task 1's fallback applies), `node --test` (Node 22+, repo has v24), pytest + Playwright (Python) as already used in `tests/`.

**Spec:** `docs/superpowers/specs/2026-10-11-testhub-design.md` in `freaxnx01/game-rhyflitzer` (origin/main). Sections 1, 2, 4, "Error handling" and the hub half of "Testing". The Rhyflitzer integration (spec section 3) and the ai-instructions section are separate plans. Parent issue: `freaxnx01/game-rhyflitzer#251`.

## Global Constraints

- Static only (GitHub Pages, served from `master`). No server, no token, no build step, no framework, no `eval`.
- Hub path `testhub/` in this repo; client at `/testhub/client.js` (one copy for all games).
- BroadcastChannel name and localStorage key are both `gg-testhub`. Language key is `gg-lang` (`en`/`de`).
- Item key is `<game>|<block heading>|<item text without tag>`. Tag syntax `{go: <id>}`, id `[a-z0-9._-]+`.
- Item status values: `open`, `noted`, `done`. Per-item state: `{ status, note, screenshots: [filename], sent: bool }`.
- Screenshot file name: `fb-<game>-<MMDD>-<n>.png`.
- Copy-all export, exactly:

```
Testhub feedback — rhyflitzer v0.9.0 — 2026-10-11
- [Hideout in the Hübel · "Inside: the tower reads as…" · go:hideout.tower] Turm wirkt von unten zu dunkel (📷 fb-rhyflitzer-1011-3.png)
- ✓ tested: [Pontoon bridge · "U again: the bridge disappears…"]
```

- `client.js` contract (agreed with the Rhyflitzer plan, `game-rhyflitzer#251`): it defines `window.ggTesthub`, then fires `window.dispatchEvent(new Event('gg-testhub-ready'))` and sends a first `hello`; any `register`/`setInfo`/`onScreenshot` call triggers a fresh debounced `hello`; the game registers after that first hello. `register(id, fn, label)`: id `[a-z0-9._-]+`, a repeated id replaces the earlier one, `fn()` is synchronous and its return value is ignored. `onScreenshot(fn)`: `fn()` returns `Promise<'data:image/png;base64,…'>` and may reject (e.g. `'screenshot already pending'`, `'photo failed'`) or hang; the hub's 10 s timeout covers it. `setInfo({game, version})` is called once, `version` has no leading `v`. Loader URL exactly `/testhub/client.js`, loaded async in dev mode only. Ids look like `j.<slug>`, `uw.boat`, `uw.car`, `hideout.gate`, `hideout.tower`.
- Request timeout for go/screenshot: 10 s. All `localStorage` access in try/catch.
- UI strings de/en via `gg-lang`; item text stays as in `test-todo.md`. German text: real umlauts, capitalized address pronouns.
- Game list starts with `rhyflitzer`, `wipfelkratzer`.
- Base branch is `master`. Conventional Commits. Do not add a `package.json`, bundler or dependencies (Task 1 documents the single permitted fallback).

## Review Focus

Failure modes the spec implies; each has a pinning test in the named task.

1. Foreign or malformed `BroadcastChannel` messages (wrong types, `targets: "nope"`, non-PNG `dataUrl`, a hub-style `{type:'hello'}` arriving at a game, a game-style hello arriving at a game) must be ignored without a thrown error: Tasks 4, 6, 10.
2. A second game window of a different game must not change the hub's status or receive Go: Task 10.
3. `test-todo.md` with CRLF line endings, a `###` sub-heading, malformed tags (`{go: BAD ID}`, `{go:}`) must not break parsing or leak into item text wrongly: Task 1.
4. Corrupt JSON in `gg-testhub` (or a throwing `localStorage` accessor) must not stop the hub: Tasks 2 and 7.
5. A multi-line note or a note containing quotes must still export as one line per entry: Task 3.

## File Structure

| File | Responsibility |
|---|---|
| `testhub/parser.js` | Pure: `test-todo.md` text to blocks/items with tags and keys |
| `testhub/store.js` | `gg-testhub` state in localStorage with in-memory fallback; screenshot file names |
| `testhub/export.js` | Pure: Copy-all Markdown; `isoDate` |
| `testhub/protocol.js` | Pure: channel name, message validation (game to hub), message builders |
| `testhub/strings.js` | de/en strings, language detection, `createT` |
| `testhub/dom.js` | Tiny `h()` element builder (no `innerHTML`) |
| `testhub/list.js` | Renders blocks and items (progress, filter, Go control, editor) |
| `testhub/link.js` | Channel to the game window: hello polling, `go`, `screenshot`, timeouts |
| `testhub/app.js` | Wiring: state, load `test-todo.md`, header/status/toolbar, actions |
| `testhub/index.html`, `testhub/style.css` | Page shell and narrow-strip layout |
| `testhub/client.js` | Classic script loaded by games in dev mode; `window.ggTesthub` |
| `tests/testhub/*.test.mjs` | `node --test` unit tests |
| `tests/test_testhub_e2e.py` | Playwright e2e (hub + fake game) |
| `tests/testhub/fixtures/` | `test-todo.md`, `fake-game.html` |

## Test setup (decision)

The repo already has pytest + Playwright under `tests/` (venv `.venv/` is gitignored) and no JS tooling. So:

- **Pure modules and `client.js`**: `node --test tests/testhub/*.test.mjs`. Node built-in, no `package.json`, no dependency. Source files are `.js` ES modules; Node 22.12+/24 detects module syntax in a typeless context. If a Node run prints `ERR_REQUIRE_ESM` or a module-type error, the one permitted fallback is a file `testhub/package.json` containing `{"type":"module"}` (served harmlessly by Pages).
- **E2E**: Python Playwright in `tests/test_testhub_e2e.py`, same style as `tests/test_buildtime_snippet_browser.py`. Setup once: `python3 -m venv .venv && .venv/bin/pip install pytest playwright && .venv/bin/playwright install chromium`.
- No CI workflow runs tests in this repo today; adding one is out of scope. Tests run locally.

---

### Task 1: Pure parser for `test-todo.md`

**Files:**
- Create: `testhub/parser.js`
- Test: `tests/testhub/parser.test.mjs`

**Interfaces:**
- Produces: `splitTag(text) -> { text: string, tag: string|null }`; `itemKey(game, heading, text) -> string`; `parseTodo(markdown, game) -> Block[]` where `Block = { heading: string, tag: string|null, items: Item[] }`, `Item = { key: string, text: string, tag: string|null }`. Blocks without open items are dropped.

- [ ] **Step 1: Write the failing test**

```js
// tests/testhub/parser.test.mjs
import test from 'node:test';
import assert from 'node:assert/strict';
import { parseTodo, splitTag, itemKey } from '../../testhub/parser.js';

test('splitTag_tagInText_isStrippedAndReturned', () => {
  assert.deepEqual(splitTag('Inside: tower {go: hideout.tower} reads dark'), { text: 'Inside: tower reads dark', tag: 'hideout.tower' });
});

test('splitTag_malformedTags_stayAsText', () => {
  assert.deepEqual(splitTag('a {go: BAD ID} b'), { text: 'a {go: BAD ID} b', tag: null });
  assert.deepEqual(splitTag('a {go:} b'), { text: 'a {go:} b', tag: null });
});

test('itemKey_joinsGameHeadingText', () => {
  assert.equal(itemKey('rhyflitzer', 'Pontoon bridge', 'U again'), 'rhyflitzer|Pontoon bridge|U again');
});

test('parseTodo_blocksAndOpenItems_ticked_skipped', () => {
  const md = '# Title\n- [ ] ignored, no block yet\n## Alpha\n- [ ] one\n- [x] done already\n- [X] done too\n- [ ] two\n## Empty\n- [x] all ticked\n';
  const blocks = parseTodo(md, 'g');
  assert.equal(blocks.length, 1);
  assert.equal(blocks[0].heading, 'Alpha');
  assert.deepEqual(blocks[0].items.map((i) => i.text), ['one', 'two']);
  assert.equal(blocks[0].items[0].key, 'g|Alpha|one');
});

test('parseTodo_blockTag_isInheritedUnlessItemHasOwn', () => {
  const md = '## Hideout {go: hideout.gate}\n- [ ] inherits\n- [ ] own {go: hideout.tower}\n';
  const [block] = parseTodo(md, 'g');
  assert.equal(block.heading, 'Hideout');
  assert.equal(block.tag, 'hideout.gate');
  assert.deepEqual(block.items.map((i) => i.tag), ['hideout.gate', 'hideout.tower']);
  assert.equal(block.items[1].text, 'own');
});

test('parseTodo_crlfAndSubheadings_areHandled', () => {
  const md = '## Alpha\r\n### Sub\r\n- [ ] one\r\n  - [ ] nested\r\n';
  const [block] = parseTodo(md, 'g');
  assert.equal(block.heading, 'Alpha');
  assert.deepEqual(block.items.map((i) => i.text), ['one', 'nested']);
});

test('parseTodo_itemWithOnlyTag_isSkipped', () => {
  assert.equal(parseTodo('## A\n- [ ] {go: x}\n', 'g').length, 0);
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `node --test tests/testhub/parser.test.mjs`
Expected: FAIL, cannot find module `testhub/parser.js`.

- [ ] **Step 3: Write minimal implementation**

```js
// testhub/parser.js
const TAG_RE = /\{go:\s*([a-z0-9._-]+)\s*\}/;
const TAG_STRIP_RE = /\s*\{go:\s*[a-z0-9._-]+\s*\}/g;
const H1_RE = /^#\s/;
const H2_RE = /^##\s+(.*\S)\s*$/;
const ITEM_RE = /^\s*- \[ \]\s+(.*\S)\s*$/;

export function splitTag(text) {
  const match = TAG_RE.exec(text);
  const clean = text.replace(TAG_STRIP_RE, '').replace(/\s+/g, ' ').trim();
  return { text: clean, tag: match ? match[1] : null };
}

export function itemKey(game, heading, text) {
  return `${game}|${heading}|${text}`;
}

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
    if (!text) continue;
    block.items.push({ key: itemKey(game, block.heading, text), text, tag: tag || block.tag });
  }
  return blocks.filter((b) => b.items.length > 0);
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `node --test tests/testhub/parser.test.mjs`
Expected: PASS (7 tests). If Node reports a module-type error, apply the `testhub/package.json` fallback from "Test setup" and re-run.

- [ ] **Step 5: Commit**

```bash
git add testhub/parser.js tests/testhub/parser.test.mjs
git commit -m "feat(testhub): parse test-todo.md into blocks and tagged items"
```

---

### Task 2: State store with localStorage fallback

**Files:**
- Create: `testhub/store.js`
- Test: `tests/testhub/store.test.mjs`

**Interfaces:**
- Produces: `getStorage() -> Storage|null` (never throws); `createStore(storage) -> { get(key), update(key, patch), setVersion(game, version), version(game), nextShotName(game, date), isPersistent() }`. `get` returns `{ status:'open', note:'', screenshots:[], sent:false }` merged with stored data. `update` merges `patch` and resets `sent` to `false` unless `patch` contains `sent`. `nextShotName(game, date: Date) -> 'fb-<game>-<MMDD>-<n>.png'`, `n` = 1 + highest `n` already stored for that game and day (local date).

- [ ] **Step 1: Write the failing test**

```js
// tests/testhub/store.test.mjs
import test from 'node:test';
import assert from 'node:assert/strict';
import { createStore, getStorage } from '../../testhub/store.js';

function fakeStorage(initial) {
  const data = new Map(initial ? [['gg-testhub', initial]] : []);
  return { getItem: (k) => (data.has(k) ? data.get(k) : null), setItem: (k, v) => data.set(k, v), data };
}

test('get_unknownKey_returnsOpenDefaults', () => {
  const store = createStore(fakeStorage());
  assert.deepEqual(store.get('a|b|c'), { status: 'open', note: '', screenshots: [], sent: false });
});

test('update_persistsAndResetsSent', () => {
  const storage = fakeStorage();
  const store = createStore(storage);
  store.update('k', { status: 'noted', note: 'x', sent: true });
  assert.equal(store.get('k').sent, true);
  store.update('k', { note: 'y' });
  assert.equal(store.get('k').sent, false);
  const again = createStore(storage);
  assert.equal(again.get('k').note, 'y');
  assert.equal(store.isPersistent(), true);
});

test('createStore_corruptJson_startsEmpty', () => {
  const store = createStore(fakeStorage('{not json'));
  assert.equal(store.get('k').status, 'open');
});

test('createStore_wrongShape_startsEmpty', () => {
  const store = createStore(fakeStorage('[1,2]'));
  assert.equal(store.get('k').status, 'open');
});

test('createStore_nullStorage_worksInMemoryButNotPersistent', () => {
  const store = createStore(null);
  store.update('k', { status: 'done' });
  assert.equal(store.get('k').status, 'done');
  assert.equal(store.isPersistent(), false);
});

test('update_throwingSetItem_keepsStateAndFlagsNotPersistent', () => {
  const storage = { getItem: () => null, setItem: () => { throw new Error('quota'); } };
  const store = createStore(storage);
  store.update('k', { status: 'done' });
  assert.equal(store.get('k').status, 'done');
  assert.equal(store.isPersistent(), false);
});

test('getStorage_throwingAccessor_returnsNull', () => {
  const original = Object.getOwnPropertyDescriptor(globalThis, 'localStorage');
  Object.defineProperty(globalThis, 'localStorage', { configurable: true, get() { throw new Error('denied'); } });
  try { assert.equal(getStorage(), null); } finally {
    if (original) Object.defineProperty(globalThis, 'localStorage', original); else delete globalThis.localStorage;
  }
});

test('version_roundTrips', () => {
  const store = createStore(fakeStorage());
  store.setVersion('rhyflitzer', '0.9.0');
  assert.equal(store.version('rhyflitzer'), '0.9.0');
  assert.equal(store.version('other'), '');
});

test('nextShotName_countsUpPerGameAndDay', () => {
  const store = createStore(fakeStorage());
  const day = new Date(2026, 9, 11);
  assert.equal(store.nextShotName('rhyflitzer', day), 'fb-rhyflitzer-1011-1.png');
  store.update('a', { screenshots: ['fb-rhyflitzer-1011-1.png'] });
  store.update('b', { screenshots: ['fb-rhyflitzer-1011-3.png', 'fb-other-1011-9.png'] });
  assert.equal(store.nextShotName('rhyflitzer', day), 'fb-rhyflitzer-1011-4.png');
  assert.equal(store.nextShotName('rhyflitzer', new Date(2026, 9, 12)), 'fb-rhyflitzer-1012-1.png');
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `node --test tests/testhub/store.test.mjs`
Expected: FAIL, cannot find module `testhub/store.js`.

- [ ] **Step 3: Write minimal implementation**

```js
// testhub/store.js
const KEY = 'gg-testhub';
const DEFAULT_ENTRY = { status: 'open', note: '', screenshots: [], sent: false };

export function getStorage() {
  try { return globalThis.localStorage || null; } catch (e) { return null; }
}

function emptyState() { return { v: 1, items: {}, versions: {} }; }

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

const pad = (n) => String(n).padStart(2, '0');

export function createStore(storage) {
  const state = readState(storage);
  let persistent = storage !== null && storage !== undefined;

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

  function setVersion(game, version) { state.versions[game] = version; save(); }
  function version(game) { return state.versions[game] || ''; }

  function nextShotName(game, date) {
    const prefix = `fb-${game}-${pad(date.getMonth() + 1)}${pad(date.getDate())}-`;
    let highest = 0;
    for (const entry of Object.values(state.items)) {
      for (const name of entry.screenshots || []) {
        if (!name.startsWith(prefix)) continue;
        const n = parseInt(name.slice(prefix.length), 10);
        if (n > highest) highest = n;
      }
    }
    return `${prefix}${highest + 1}.png`;
  }

  return { get, update, setVersion, version, nextShotName, isPersistent: () => persistent };
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `node --test tests/testhub/store.test.mjs`
Expected: PASS (9 tests).

- [ ] **Step 5: Commit**

```bash
git add testhub/store.js tests/testhub/store.test.mjs
git commit -m "feat(testhub): persist item state in gg-testhub with in-memory fallback"
```

---

### Task 3: Copy-all export format

**Files:**
- Create: `testhub/export.js`
- Test: `tests/testhub/export.test.mjs`

**Interfaces:**
- Produces: `isoDate(date: Date) -> 'YYYY-MM-DD'` (local date); `buildExport({ game, version, date, entries }) -> string` with `entries = [{ block, text, tag, status, note, screenshots }]` in list order. A note line is emitted when `note` or `screenshots` is non-empty; a `✓ tested` line when `status === 'done'`. Whitespace runs in notes (including newlines) collapse to one space. `version` empty gives `version unknown` in the header.

- [ ] **Step 1: Write the failing test**

```js
// tests/testhub/export.test.mjs
import test from 'node:test';
import assert from 'node:assert/strict';
import { buildExport, isoDate } from '../../testhub/export.js';

test('isoDate_usesLocalDate', () => {
  assert.equal(isoDate(new Date(2026, 9, 1)), '2026-10-01');
});

test('buildExport_matchesSpecFormat', () => {
  const text = buildExport({
    game: 'rhyflitzer', version: '0.9.0', date: '2026-10-11',
    entries: [
      { block: 'Hideout in the Hübel', text: 'Inside: the tower reads as…', tag: 'hideout.tower', status: 'noted',
        note: 'Turm wirkt von unten zu dunkel', screenshots: ['fb-rhyflitzer-1011-3.png'] },
      { block: 'Pontoon bridge', text: 'U again: the bridge disappears…', tag: null, status: 'done', note: '', screenshots: [] },
    ],
  });
  assert.equal(text, [
    'Testhub feedback — rhyflitzer v0.9.0 — 2026-10-11',
    '- [Hideout in the Hübel · "Inside: the tower reads as…" · go:hideout.tower] Turm wirkt von unten zu dunkel (📷 fb-rhyflitzer-1011-3.png)',
    '- ✓ tested: [Pontoon bridge · "U again: the bridge disappears…"]',
  ].join('\n'));
});

test('buildExport_doneWithNote_emitsNoteLineThenTestedLine', () => {
  const text = buildExport({ game: 'g', version: '1', date: 'D', entries: [
    { block: 'B', text: 'T', tag: null, status: 'done', note: 'fine but slow', screenshots: [] },
  ] });
  assert.deepEqual(text.split('\n').slice(1), ['- [B · "T"] fine but slow', '- ✓ tested: [B · "T"]']);
});

test('buildExport_multilineNoteWithQuotes_staysOneLine', () => {
  const text = buildExport({ game: 'g', version: '1', date: 'D', entries: [
    { block: 'B', text: 'T', tag: null, status: 'noted', note: 'line one\n  line "two"', screenshots: ['a.png', 'b.png'] },
  ] });
  assert.equal(text.split('\n')[1], '- [B · "T"] line one line "two" (📷 a.png, b.png)');
});

test('buildExport_screenshotOnly_hasNoteLineWithoutText', () => {
  const text = buildExport({ game: 'g', version: '1', date: 'D', entries: [
    { block: 'B', text: 'T', tag: null, status: 'noted', note: '', screenshots: ['a.png'] },
  ] });
  assert.equal(text.split('\n')[1], '- [B · "T"] (📷 a.png)');
});

test('buildExport_unknownVersion_saysSo', () => {
  assert.equal(buildExport({ game: 'g', version: '', date: 'D', entries: [] }), 'Testhub feedback — g version unknown — D');
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `node --test tests/testhub/export.test.mjs`
Expected: FAIL, cannot find module `testhub/export.js`.

- [ ] **Step 3: Write minimal implementation**

```js
// testhub/export.js
const pad = (n) => String(n).padStart(2, '0');

export function isoDate(date) {
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`;
}

function label(entry) {
  const tag = entry.tag ? ` · go:${entry.tag}` : '';
  return `[${entry.block} · "${entry.text}"${tag}]`;
}

function noteLine(entry) {
  const note = entry.note.replace(/\s+/g, ' ').trim();
  const shots = entry.screenshots.length ? `(📷 ${entry.screenshots.join(', ')})` : '';
  const body = [note, shots].filter(Boolean).join(' ');
  return `- ${label(entry)} ${body}`;
}

function testedLine(entry) {
  return `- ✓ tested: [${entry.block} · "${entry.text}"]`;
}

export function buildExport({ game, version, date, entries }) {
  const versionText = version ? `v${version}` : 'version unknown';
  const lines = [`Testhub feedback — ${game} ${versionText} — ${date}`];
  for (const entry of entries) {
    if (entry.note.trim() || entry.screenshots.length) lines.push(noteLine(entry));
    if (entry.status === 'done') lines.push(testedLine(entry));
  }
  return lines.join('\n');
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `node --test tests/testhub/export.test.mjs`
Expected: PASS (6 tests).

- [ ] **Step 5: Commit**

```bash
git add testhub/export.js tests/testhub/export.test.mjs
git commit -m "feat(testhub): build the Copy-all feedback block"
```

---

### Task 4: Protocol validation and message builders

**Files:**
- Create: `testhub/protocol.js`
- Test: `tests/testhub/protocol.test.mjs`

**Interfaces:**
- Produces: `CHANNEL = 'gg-testhub'`; `validateGameMessage(raw) -> msg|null` accepting `hello {game, version, targets:[{id,label}]}`, `png {req, dataUrl}`, `done {req}`, `error {req, message}` and returning a normalized copy; `helloMsg() -> {type:'hello'}`; `goMsg(game, id, req) -> {type:'go', game, id, req}`; `screenshotMsg(game, req) -> {type:'screenshot', game, req}`; `newReq() -> string`.
- Note (documented extension of the spec's wire format, kept compatible): `go` and `screenshot` carry `game` so only the matching game window answers; `go` carries `req` and the game answers `done {req}` so the hub can tell success from silence.

- [ ] **Step 1: Write the failing test**

```js
// tests/testhub/protocol.test.mjs
import test from 'node:test';
import assert from 'node:assert/strict';
import { CHANNEL, validateGameMessage, helloMsg, goMsg, screenshotMsg, newReq } from '../../testhub/protocol.js';

const PNG = 'data:image/png;base64,iVBORw0KGgo=';

test('channel_name', () => assert.equal(CHANNEL, 'gg-testhub'));

test('validateGameMessage_validHello_isNormalized', () => {
  const msg = validateGameMessage({ type: 'hello', game: 'g', version: '1.0', targets: [{ id: 'j.a', label: 'A', extra: 1 }], junk: true });
  assert.deepEqual(msg, { type: 'hello', game: 'g', version: '1.0', targets: [{ id: 'j.a', label: 'A' }] });
});

test('validateGameMessage_hubStyleHelloWithoutTargets_isRejected', () => {
  assert.equal(validateGameMessage({ type: 'hello' }), null);
});

test('validateGameMessage_badTargets_areRejected', () => {
  assert.equal(validateGameMessage({ type: 'hello', game: 'g', version: '1', targets: 'nope' }), null);
  assert.equal(validateGameMessage({ type: 'hello', game: 'g', version: '1', targets: [{ id: 'Bad Id', label: 'x' }] }), null);
  assert.equal(validateGameMessage({ type: 'hello', game: 'g', version: '1', targets: [{ id: '<script>', label: 'x' }] }), null);
  assert.equal(validateGameMessage({ type: 'hello', game: 'g', version: 1, targets: [] }), null);
});

test('validateGameMessage_png_requiresPngDataUrl', () => {
  assert.deepEqual(validateGameMessage({ type: 'png', req: 'r', dataUrl: PNG }), { type: 'png', req: 'r', dataUrl: PNG });
  assert.equal(validateGameMessage({ type: 'png', req: 'r', dataUrl: 'data:text/html;base64,AAAA' }), null);
  assert.equal(validateGameMessage({ type: 'png', req: 5, dataUrl: PNG }), null);
  assert.equal(validateGameMessage({ type: 'png', req: 'r', dataUrl: PNG + 'A'.repeat(16 * 1024 * 1024) }), null);
});

test('validateGameMessage_doneAndError', () => {
  assert.deepEqual(validateGameMessage({ type: 'done', req: 'r' }), { type: 'done', req: 'r' });
  assert.deepEqual(validateGameMessage({ type: 'error', req: 'r', message: 'm' }), { type: 'error', req: 'r', message: 'm' });
  assert.equal(validateGameMessage({ type: 'error', req: 'r' }), null);
});

test('validateGameMessage_garbage_isRejected', () => {
  for (const raw of [null, undefined, 'x', 5, [], {}, { type: 5 }, { type: 'go', id: 'a' }, { type: 'unknown' }]) {
    assert.equal(validateGameMessage(raw), null);
  }
});

test('builders_shape', () => {
  assert.deepEqual(helloMsg(), { type: 'hello' });
  assert.deepEqual(goMsg('g', 'j.a', 'r1'), { type: 'go', game: 'g', id: 'j.a', req: 'r1' });
  assert.deepEqual(screenshotMsg('g', 'r2'), { type: 'screenshot', game: 'g', req: 'r2' });
});

test('newReq_isUnique', () => assert.notEqual(newReq(), newReq()));
```

- [ ] **Step 2: Run test to verify it fails**

Run: `node --test tests/testhub/protocol.test.mjs`
Expected: FAIL, cannot find module `testhub/protocol.js`.

- [ ] **Step 3: Write minimal implementation**

```js
// testhub/protocol.js
export const CHANNEL = 'gg-testhub';

const ID_RE = /^[a-z0-9._-]+$/;
const MAX_TARGETS = 500;
const MAX_DATA_URL = 15 * 1024 * 1024;
const PNG_PREFIX = 'data:image/png;base64,';

const isString = (v, max = 300) => typeof v === 'string' && v.length <= max;
const isPlainObject = (v) => v !== null && typeof v === 'object' && !Array.isArray(v);

function validateTargets(list) {
  if (!Array.isArray(list) || list.length > MAX_TARGETS) return null;
  const out = [];
  for (const target of list) {
    const valid = isPlainObject(target) && isString(target.id, 100) && ID_RE.test(target.id) && isString(target.label, 200);
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

function validatePng(msg) {
  const valid = isString(msg.req, 100) && isString(msg.dataUrl, MAX_DATA_URL) && msg.dataUrl.startsWith(PNG_PREFIX);
  return valid ? { type: 'png', req: msg.req, dataUrl: msg.dataUrl } : null;
}

export function validateGameMessage(msg) {
  if (!isPlainObject(msg) || !isString(msg.type, 20)) return null;
  if (msg.type === 'hello') return validateHello(msg);
  if (msg.type === 'png') return validatePng(msg);
  if (msg.type === 'done') return isString(msg.req, 100) ? { type: 'done', req: msg.req } : null;
  if (msg.type === 'error') {
    return isString(msg.req, 100) && isString(msg.message, 500) ? { type: 'error', req: msg.req, message: msg.message } : null;
  }
  return null;
}

export const helloMsg = () => ({ type: 'hello' });
export const goMsg = (game, id, req) => ({ type: 'go', game, id, req });
export const screenshotMsg = (game, req) => ({ type: 'screenshot', game, req });
export const newReq = () => Math.random().toString(36).slice(2) + Date.now().toString(36);
```

- [ ] **Step 4: Run test to verify it passes**

Run: `node --test tests/testhub/protocol.test.mjs`
Expected: PASS (8 tests).

- [ ] **Step 5: Commit**

```bash
git add testhub/protocol.js tests/testhub/protocol.test.mjs
git commit -m "feat(testhub): validate channel messages from game windows"
```

---

### Task 5: de/en strings and language detection

**Files:**
- Create: `testhub/strings.js`
- Test: `tests/testhub/strings.test.mjs`

**Interfaces:**
- Produces: `STRINGS = { en: {...}, de: {...} }`; `detectLang(storage|null, navigatorLanguage) -> 'en'|'de'` (reads `gg-lang`, else `de*` navigator language, else `en`); `createT(lang) -> (key, params?) -> string` replacing `{name}` placeholders; unknown key returns the key.
- Keys used by later tasks: `title`, `connected` (`{version}`, `{n}`), `disconnected`, `openGame`, `filter_open`, `filter_noted`, `filter_done`, `search`, `copyAll` (`{n}`), `go`, `goUnknown`, `notePlaceholder`, `save`, `done`, `reopen`, `shot`, `loadError` (`{game}`, `{reason}`), `noItems`, `noStorage`, `err_timeout`, `err_noGame`, `copied` (`{n}`), `copyManual`, `markSent`, `langToggle`.

- [ ] **Step 1: Write the failing test**

```js
// tests/testhub/strings.test.mjs
import test from 'node:test';
import assert from 'node:assert/strict';
import { STRINGS, detectLang, createT } from '../../testhub/strings.js';

test('STRINGS_bothLanguages_haveTheSameKeys', () => {
  assert.deepEqual(Object.keys(STRINGS.de).sort(), Object.keys(STRINGS.en).sort());
});

test('STRINGS_german_usesRealUmlauts', () => {
  const all = Object.values(STRINGS.de).join(' ');
  assert.doesNotMatch(all, /\b\w*(ae|oe|ue)\w*\b.*(ä|ö|ü)?/i.source === '' ? /$^/ : /Spiel verbunden/ ? /\bwaehl|\bkoenn|\bfuer\b|\bueber\b/ : /$^/);
  assert.match(STRINGS.de.openGame, /öffnen/);
});

test('detectLang_storedValueWins', () => {
  const storage = { getItem: (k) => (k === 'gg-lang' ? 'de' : null) };
  assert.equal(detectLang(storage, 'en-GB'), 'de');
});

test('detectLang_invalidStored_fallsBackToNavigator', () => {
  const storage = { getItem: () => 'fr' };
  assert.equal(detectLang(storage, 'de-CH'), 'de');
  assert.equal(detectLang(storage, 'en-US'), 'en');
});

test('detectLang_noStorage_usesNavigator', () => {
  assert.equal(detectLang(null, 'de'), 'de');
  assert.equal(detectLang(null, undefined), 'en');
});

test('detectLang_throwingStorage_fallsBack', () => {
  assert.equal(detectLang({ getItem() { throw new Error('x'); } }, 'de-AT'), 'de');
});

test('createT_replacesPlaceholdersAndFallsBackToKey', () => {
  const t = createT('en');
  assert.equal(t('copyAll', { n: 3 }), 'Copy all 3');
  assert.equal(t('missing.key'), 'missing.key');
  assert.equal(createT('de')('copyAll', { n: 3 }), 'Alle kopieren 3');
});
```

Note for the implementer: the second test above is deliberately simple in intent (real umlauts, no `ae/oe/ue` transliteration); replace its body with this clearer version before running:

```js
test('STRINGS_german_usesRealUmlauts', () => {
  const all = Object.values(STRINGS.de).join(' ');
  assert.doesNotMatch(all, /\b(fuer|ueber|koennen|oeffnen|Eintraege)\b/);
  assert.match(STRINGS.de.openGame, /öffnen/);
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `node --test tests/testhub/strings.test.mjs`
Expected: FAIL, cannot find module `testhub/strings.js`.

- [ ] **Step 3: Write minimal implementation**

```js
// testhub/strings.js
export const STRINGS = {
  en: {
    title: 'Testhub',
    connected: 'Game connected (v{version} · {n} targets)',
    disconnected: 'No game window',
    openGame: 'Open the game with ?dev=1',
    filter_open: 'Open',
    filter_noted: 'Noted',
    filter_done: 'Done',
    search: 'Search…',
    copyAll: 'Copy all {n}',
    go: 'Go ▸',
    goUnknown: 'Unknown target',
    notePlaceholder: 'Note…',
    save: 'Save',
    done: '✓ Done',
    reopen: 'Reopen',
    shot: '📷 Screenshot',
    loadError: 'Could not load test-todo.md for {game}: {reason}',
    noItems: 'Nothing to show.',
    noStorage: 'Storage is unavailable: notes are kept for this session only.',
    err_timeout: 'No answer from the game within 10 s.',
    err_noGame: 'No game window connected.',
    copied: 'Copied {n} entries.',
    copyManual: 'Copy was refused. Copy the text below by hand:',
    markSent: 'Mark as sent',
    langToggle: 'DE',
  },
  de: {
    title: 'Testhub',
    connected: 'Spiel verbunden (v{version} · {n} Ziele)',
    disconnected: 'Kein Spielfenster',
    openGame: 'Spiel mit ?dev=1 öffnen',
    filter_open: 'Offen',
    filter_noted: 'Notiert',
    filter_done: 'Erledigt',
    search: 'Suchen…',
    copyAll: 'Alle kopieren {n}',
    go: 'Los ▸',
    goUnknown: 'Unbekanntes Ziel',
    notePlaceholder: 'Notiz…',
    save: 'Speichern',
    done: '✓ Erledigt',
    reopen: 'Wieder öffnen',
    shot: '📷 Screenshot',
    loadError: 'test-todo.md für {game} konnte nicht geladen werden: {reason}',
    noItems: 'Nichts anzuzeigen.',
    noStorage: 'Speicher nicht verfügbar: Notizen gelten nur für diese Sitzung.',
    err_timeout: 'Keine Antwort vom Spiel innerhalb von 10 s.',
    err_noGame: 'Kein Spielfenster verbunden.',
    copied: '{n} Einträge kopiert.',
    copyManual: 'Kopieren wurde abgelehnt. Text unten von Hand kopieren:',
    markSent: 'Als gesendet markieren',
    langToggle: 'EN',
  },
};

const SUPPORTED = ['en', 'de'];

export function detectLang(storage, navigatorLanguage) {
  let stored = null;
  try { stored = storage ? storage.getItem('gg-lang') : null; } catch (e) { stored = null; }
  if (SUPPORTED.includes(stored)) return stored;
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

- [ ] **Step 4: Run test to verify it passes**

Run: `node --test tests/testhub/strings.test.mjs`
Expected: PASS (7 tests).

- [ ] **Step 5: Commit**

```bash
git add testhub/strings.js tests/testhub/strings.test.mjs
git commit -m "feat(testhub): de/en UI strings driven by gg-lang"
```

---

### Task 6: `client.js` for game windows

**Files:**
- Create: `testhub/client.js`
- Test: `tests/testhub/client.test.mjs`

**Interfaces:**
- Consumes: wire format from Task 4 (`go {game,id,req}`, `screenshot {game,req}`, hub `hello` without `targets`).
- Produces: classic script defining `window.ggTesthub = { register(id, fn, label?), onScreenshot(fn), setInfo({game, version}) }`, then firing `window.dispatchEvent(new Event('gg-testhub-ready'))` and queueing a first `hello` (the script is loaded async, so games register on that event or immediately if `window.ggTesthub` already exists). `register` with a repeated id replaces the target; `fn()` is called synchronously and its return value ignored. Game to hub: `hello {game, version, targets}` (debounced after `register`/`setInfo`, and in reply to a hub hello), `done {req}`, `png {req, dataUrl}`, `error {req, message}`. Ignores everything malformed, messages with a different `game`, and any `hello` that carries `targets` (another game's hello).

- [ ] **Step 1: Write the failing test**

```js
// tests/testhub/client.test.mjs
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
  class FakeChannel {
    constructor(name) { this.name = name; channels.push(this); }
    postMessage(m) { posted.push(JSON.parse(JSON.stringify(m))); }
  }
  const events = [];
  const win = { BroadcastChannel: FakeChannel, setTimeout, Event: class { constructor(type) { this.type = type; } }, dispatchEvent: (e) => events.push(e.type) };
  win.window = win;
  vm.runInNewContext(SOURCE, win);
  return { api: win.ggTesthub, posted, events, channel: channels[0], deliver: (m) => channels[0].onmessage({ data: m }) };
}

test('register_thenHello_listsTargetsOnce', async () => {
  const { api, posted } = boot();
  api.setInfo({ game: 'g', version: '1.2.3' });
  api.register('j.a', () => {}, 'Alpha');
  api.register('j.b', () => {});
  await tick();
  assert.equal(posted.length, 1);
  assert.deepEqual(posted[0], { type: 'hello', game: 'g', version: '1.2.3', targets: [{ id: 'j.a', label: 'Alpha' }, { id: 'j.b', label: 'j.b' }] });
});

test('load_firesReadyEventAndSendsFirstHello', async () => {
  const { api, events, posted } = boot();
  assert.deepEqual(events, ['gg-testhub-ready']);
  assert.ok(api);
  await tick();
  assert.equal(posted.length, 1);
  assert.deepEqual(posted[0], { type: 'hello', game: '', version: '', targets: [] });
});

test('lateRegistration_sendsFreshHelloWithAllTargets', async () => {
  const { api, posted } = boot();
  await tick();
  posted.length = 0;
  api.register('j.a', () => {});
  api.register('j.b', () => {});
  await tick();
  assert.equal(posted.length, 1);
  assert.deepEqual(posted[0].targets.map((t) => t.id), ['j.a', 'j.b']);
});

test('register_repeatedId_replacesEarlierTarget', async () => {
  const { api, posted, deliver } = boot();
  api.setInfo({ game: 'g', version: '1' });
  const calls = [];
  api.register('j.a', () => calls.push('old'), 'Old');
  api.register('j.a', () => calls.push('new'), 'New');
  await tick();
  assert.deepEqual(posted[0].targets, [{ id: 'j.a', label: 'New' }]);
  deliver({ type: 'go', game: 'g', id: 'j.a', req: 'r' });
  assert.deepEqual(calls, ['new']);
});

test('channel_usesGgTesthubName', () => assert.equal(boot().channel.name, 'gg-testhub'));

test('hubHello_isAnswered', async () => {
  const { api, posted, deliver } = boot();
  api.setInfo({ game: 'g', version: '1' });
  await tick();
  posted.length = 0;
  deliver({ type: 'hello' });
  assert.equal(posted.length, 1);
  assert.equal(posted[0].type, 'hello');
});

test('helloWithTargets_fromAnotherGame_isIgnored', () => {
  const { posted, deliver } = boot();
  deliver({ type: 'hello', game: 'other', version: '1', targets: [] });
  assert.equal(posted.length, 0);
});

test('go_knownId_runsFnAndAnswersDone', async () => {
  const { api, posted, deliver } = boot();
  api.setInfo({ game: 'g', version: '1' });
  let ran = 0;
  api.register('j.a', () => { ran += 1; });
  await tick();
  posted.length = 0;
  deliver({ type: 'go', game: 'g', id: 'j.a', req: 'r1' });
  await tick();
  assert.equal(ran, 1);
  assert.deepEqual(posted, [{ type: 'done', req: 'r1' }]);
});

test('go_returnedPromise_isIgnoredAndStillAnswersDone', async () => {
  const { api, posted, deliver } = boot();
  api.setInfo({ game: 'g', version: '1' });
  api.register('j.a', () => new Promise(() => {}));
  await tick();
  posted.length = 0;
  deliver({ type: 'go', game: 'g', id: 'j.a', req: 'r1' });
  await tick();
  assert.deepEqual(posted, [{ type: 'done', req: 'r1' }]);
});

test('go_unknownId_answersError', async () => {
  const { api, posted, deliver } = boot();
  api.setInfo({ game: 'g', version: '1' });
  await tick();
  posted.length = 0;
  deliver({ type: 'go', game: 'g', id: 'nope', req: 'r1' });
  await tick();
  assert.equal(posted[0].type, 'error');
  assert.equal(posted[0].req, 'r1');
});

test('go_throwingFn_answersError', async () => {
  const { api, posted, deliver } = boot();
  api.setInfo({ game: 'g', version: '1' });
  api.register('j.a', () => { throw new Error('boom'); });
  await tick();
  posted.length = 0;
  deliver({ type: 'go', game: 'g', id: 'j.a', req: 'r1' });
  await tick();
  assert.deepEqual(posted, [{ type: 'error', req: 'r1', message: 'boom' }]);
});

test('go_forAnotherGame_isIgnored', async () => {
  const { api, posted, deliver } = boot();
  api.setInfo({ game: 'g', version: '1' });
  let ran = 0;
  api.register('j.a', () => { ran += 1; });
  await tick();
  posted.length = 0;
  deliver({ type: 'go', game: 'other', id: 'j.a', req: 'r1' });
  await tick();
  assert.equal(ran, 0);
  assert.equal(posted.length, 0);
});

test('screenshot_returnsPng_orErrors', async () => {
  const { api, posted, deliver } = boot();
  api.setInfo({ game: 'g', version: '1' });
  await tick();
  posted.length = 0;
  deliver({ type: 'screenshot', game: 'g', req: 'r0' });
  await tick();
  assert.equal(posted[0].type, 'error');

  api.onScreenshot(() => Promise.resolve(PNG));
  posted.length = 0;
  deliver({ type: 'screenshot', game: 'g', req: 'r1' });
  await tick();
  assert.deepEqual(posted, [{ type: 'png', req: 'r1', dataUrl: PNG }]);

  api.onScreenshot(() => 'data:text/html;base64,AAAA');
  posted.length = 0;
  deliver({ type: 'screenshot', game: 'g', req: 'r2' });
  await tick();
  assert.equal(posted[0].type, 'error');
});

test('screenshot_rejectionWithString_becomesErrorMessage', async () => {
  const { api, posted, deliver } = boot();
  api.setInfo({ game: 'g', version: '1' });
  api.onScreenshot(() => Promise.reject('photo failed'));
  await tick();
  posted.length = 0;
  deliver({ type: 'screenshot', game: 'g', req: 'r1' });
  await tick();
  assert.deepEqual(posted, [{ type: 'error', req: 'r1', message: 'photo failed' }]);
});

test('malformedMessages_areIgnoredWithoutThrowing', async () => {
  const { api, posted, deliver } = boot();
  api.setInfo({ game: 'g', version: '1' });
  api.register('j.a', () => {});
  await tick();
  posted.length = 0;
  for (const m of [null, 'x', 5, [], {}, { type: 'go' }, { type: 'go', id: '<script>', req: 'r' }, { type: 'go', id: 'j.a', req: 7 },
    { type: 'screenshot' }, { type: 'unknown' }]) {
    deliver(m);
  }
  await tick();
  assert.equal(posted.length, 0);
});

test('register_invalidInput_throws', () => {
  const { api } = boot();
  assert.throws(() => api.register('Bad Id', () => {}), TypeError);
  assert.throws(() => api.register('ok.id', 'notAFunction'), TypeError);
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `node --test tests/testhub/client.test.mjs`
Expected: FAIL, ENOENT reading `testhub/client.js`.

- [ ] **Step 3: Write minimal implementation**

```js
// testhub/client.js
// Classic script (no modules): a game loads it async, only in dev mode, and registers on 'gg-testhub-ready'. See CLAUDE.md "Testhub".
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
    var message = String(err && err.message ? err.message : err).slice(0, 500);
    send({ type: 'error', req: req || '', message: message });
  }

  function parse(m) {
    if (!m || typeof m !== 'object' || Array.isArray(m) || typeof m.type !== 'string') return null;
    if (m.type === 'hello') return m.targets === undefined ? { type: 'hello' } : null;
    if (!isOptionalText(m.game) || !isOptionalText(m.req)) return null;
    if (m.type === 'go') {
      return isText(m.id, 100) && ID_RE.test(m.id) ? { type: 'go', game: m.game, id: m.id, req: m.req } : null;
    }
    if (m.type === 'screenshot') return isText(m.req, 100) ? { type: 'screenshot', game: m.game, req: m.req } : null;
    return null;
  }

  function isForMe(m) { return !m.game || !info.game || m.game === info.game; }

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
      if (!isForMe(m)) return;
      if (m.type === 'go') onGo(m);
      else onScreenshotRequest(m);
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

- [ ] **Step 4: Run test to verify it passes**

Run: `node --test tests/testhub/client.test.mjs`
Expected: PASS (11 tests).

- [ ] **Step 5: Commit**

```bash
git add testhub/client.js tests/testhub/client.test.mjs
git commit -m "feat(testhub): client.js registers jump targets and answers the hub"
```

---

### Task 7: Hub page shell, list rendering, e2e harness

**Files:**
- Create: `testhub/index.html`, `testhub/style.css`, `testhub/dom.js`, `testhub/list.js`, `testhub/app.js`
- Create: `tests/testhub/fixtures/test-todo.md`, `tests/testhub/fixtures/fake-game.html`
- Create: `tests/test_testhub_e2e.py`

**Interfaces:**
- Consumes: `parseTodo` (Task 1), `getStorage`/`createStore` (Task 2), `detectLang`/`createT` (Task 5).
- Produces:
  - `h(tag, props, ...children) -> HTMLElement` (`dom.js`): `on*` props add listeners, `class` sets className, `true` sets an empty attribute, `false`/`null` skip, children arrays are flattened, strings become text nodes.
  - `renderList(view) -> HTMLElement` (`list.js`), `view = { t, blocks, store, filter, query, expanded: Set<key>, collapsed: Map<heading, bool>, drafts: Map<key,string>, errors: Map<key,string>, conn: {version, targets}|null, actions: { toggleItem(key), toggleBlock(heading, wasCollapsed), go(item), shot(item), save(item), done(item), reopen(item) } }`. Each item renders as `li.item[data-key]` with a `button.text` and a Go control (`button.go`, or `span.go-unknown` for an unknown tag; disabled button when `conn` is null).
  - `app.js` sets up `#app` with `.status` (red/green line), `.toolbar`, notices and the list; `?game=<slug>` selects the game (slug `[a-z0-9-]+`, appended to the picker if not in `GAMES`); `GAMES = ['rhyflitzer', 'wipfelkratzer']`.
  - E2E helpers in `tests/test_testhub_e2e.py`: `ORIGIN = "http://localhost:4173"` (served by `context.route`, secure context so the Clipboard API works), `new_context(browser, todo=True)`, `open_game(ctx)`, `open_hub(ctx, errors=None)`, `item(hub, text)`.

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

`tests/testhub/fixtures/fake-game.html` (a tiny game: loads the client async like a real game, registers on `gg-testhub-ready`, registers one target late, and a screenshot hook whose behaviour the test switches via `window.__shot`):

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
<p>fake game</p>
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
TYPES = {
    ".html": "text/html; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".md": "text/markdown; charset=utf-8",
}


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
    ctx = browser.new_context(
        locale="en-GB", timezone_id=TZ, accept_downloads=True,
        permissions=["clipboard-read", "clipboard-write"], **kwargs,
    )
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


def test_list_showsOpenItemsOnly_withTagsStripped(ctx):
    errors = []
    hub = open_hub(ctx, errors)
    expect(hub.locator(".item")).to_have_count(4)
    expect(item(hub, "Second item has its own tag")).to_have_text(re.compile(r"^\s*☐ Second item has its own tag\s*Go"))
    expect(hub.locator(".block", has_text="Alpha block").locator(".progress")).to_have_text("0 / 2 ✓")
    assert hub.locator("text=Already tested").count() == 0
    assert hub.locator("text={go:").count() == 0
    assert errors == []


def test_noGameWindow_statusRed_goDisabled_linkToGame(ctx):
    hub = open_hub(ctx)
    expect(hub.locator(".status.off")).to_contain_text("No game window")
    expect(hub.locator(".status a")).to_have_attribute("href", "/game-fake/?dev=1")
    expect(item(hub, "First item").locator("button.go")).to_be_disabled()


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

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/pytest tests/test_testhub_e2e.py -v`
Expected: FAIL, the hub page 404s (`testhub/index.html` does not exist), so `.status` never appears.

- [ ] **Step 3: Write the implementation**

`testhub/dom.js`:

```js
// testhub/dom.js
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
// testhub/list.js
import { h } from './dom.js';

function matchesFilter(view, block, item) {
  const entry = view.store.get(item.key);
  if (view.filter === 'open' && entry.status === 'done') return false;
  if (view.filter === 'noted' && entry.status !== 'noted') return false;
  if (view.filter === 'done' && entry.status !== 'done') return false;
  const query = view.query.trim().toLowerCase();
  if (!query) return true;
  return `${block.heading} ${item.text} ${entry.note}`.toLowerCase().includes(query);
}

function goControl(view, item) {
  if (!item.tag) return null;
  const { t, conn } = view;
  if (!conn) return h('button', { class: 'go', disabled: true, title: item.tag }, t('go'));
  const known = conn.targets.some((target) => target.id === item.tag);
  if (!known) return h('span', { class: 'go-unknown', title: t('goUnknown') }, item.tag);
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
  if (blocks.length === 0) return h('p', { class: 'empty' }, view.t('noItems'));
  return h('div', { class: 'list' }, blocks);
}
```

`testhub/app.js`:

```js
// testhub/app.js
import { h } from './dom.js';
import { parseTodo } from './parser.js';
import { getStorage, createStore } from './store.js';
import { createT, detectLang } from './strings.js';
import { renderList } from './list.js';

export const GAMES = ['rhyflitzer', 'wipfelkratzer'];
const SLUG_RE = /^[a-z0-9-]+$/;

function pickGame() {
  const requested = new URLSearchParams(location.search).get('game');
  return requested && SLUG_RE.test(requested) ? requested : GAMES[0];
}

const game = pickGame();
const games = GAMES.includes(game) ? GAMES : [...GAMES, game];
const storage = getStorage();
const store = createStore(storage);
let lang = detectLang(storage, navigator.language);
let t = createT(lang);
let link = null; // set in Task 8

const ui = {
  blocks: [], loadError: null, filter: 'open', query: '',
  expanded: new Set(), collapsed: new Map(), drafts: new Map(), errors: new Map(),
};

const conn = () => (link ? link.conn : null);

function captureFocus() {
  const el = document.activeElement;
  if (!el || !el.dataset || !el.dataset.focus) return null;
  return { id: el.dataset.focus, start: el.selectionStart, end: el.selectionEnd };
}

function restoreFocus(saved) {
  if (!saved) return;
  const el = document.querySelector(`[data-focus="${CSS.escape(saved.id)}"]`);
  if (!el) return;
  el.focus();
  if (saved.start !== null && saved.start !== undefined && el.setSelectionRange) el.setSelectionRange(saved.start, saved.end);
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

function view() {
  return { t, blocks: ui.blocks, store, filter: ui.filter, query: ui.query, conn: conn(), actions, ...ui };
}

function header() {
  const picker = h('select', { class: 'picker', 'aria-label': 'Game', onchange: (e) => { location.search = `?game=${e.target.value}`; } },
    games.map((g) => h('option', { value: g, selected: g === game }, g)));
  const toggle = h('button', { class: 'lang', type: 'button', onclick: switchLang }, t('langToggle'));
  return h('header', { class: 'head' }, h('h1', {}, t('title')), picker, toggle);
}

function switchLang() {
  lang = lang === 'en' ? 'de' : 'en';
  t = createT(lang);
  try { if (storage) storage.setItem('gg-lang', lang); } catch (e) { /* language stays for this session */ }
  render();
}

function statusBar() {
  const c = conn();
  if (c) {
    return h('div', { class: 'status on' }, '● ', t('connected', { version: c.version, n: c.targets.length }));
  }
  return h('div', { class: 'status off' }, '● ', t('disconnected'), ' ',
    h('a', { href: `/game-${game}/?dev=1`, target: '_blank', rel: 'noopener' }, t('openGame')));
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

Note on `view()`: the spread of `ui` supplies `expanded`, `collapsed`, `drafts`, `errors` to `renderList`.

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

`testhub/style.css` (fluid, works as a strip beside the game, no fixed widths):

```css
:root { color-scheme: dark light; --bg: #12151c; --fg: #e6e9f0; --muted: #8a93a6; --line: #2a3040; --ok: #3ecf6e; --bad: #ef5b5b; --accent: #8fd8e8; }
@media (prefers-color-scheme: light) { :root { --bg: #f6f7fa; --fg: #1b1f2a; --muted: #5a6072; --line: #d5d9e3; --accent: #0b6e86; } }
* { box-sizing: border-box; }
body { margin: 0; background: var(--bg); color: var(--fg); font: 15px/1.4 system-ui, sans-serif; }
#app { padding: 8px 12px; max-width: 100%; }
button, input, select, textarea { font: inherit; color: inherit; }
button { background: none; border: 1px solid var(--line); border-radius: 6px; padding: 4px 8px; cursor: pointer; }
button:disabled { opacity: .45; cursor: not-allowed; }
.head { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.head h1 { font-size: 1.1rem; margin: 0; flex: 1; }
.status { padding: 6px 0; overflow-wrap: anywhere; }
.status.on { color: var(--ok); }
.status.off { color: var(--bad); }
.status a { color: var(--accent); }
.toolbar { display: flex; flex-wrap: wrap; gap: 8px 14px; align-items: center; padding: 4px 0 8px; }
.search { flex: 1 1 8rem; min-width: 0; background: transparent; border: 1px solid var(--line); border-radius: 6px; padding: 4px 8px; }
.notice.warn, .error, .load-error { color: var(--bad); margin: 4px 0; overflow-wrap: anywhere; }
.block { border-top: 1px solid var(--line); }
.block-head { display: flex; justify-content: space-between; gap: 8px; width: 100%; border: 0; text-align: left; padding: 8px 0; }
.block-title { overflow-wrap: anywhere; min-width: 0; }
.progress { color: var(--muted); white-space: nowrap; }
ul { list-style: none; margin: 0; padding: 0 0 8px 12px; }
.item .row { display: flex; gap: 8px; align-items: flex-start; }
.item .text { flex: 1; min-width: 0; text-align: left; border: 0; padding: 2px 0; overflow-wrap: anywhere; }
.item.done .text { color: var(--muted); }
.go-unknown { color: var(--muted); font-size: .85em; border: 1px dashed var(--line); border-radius: 6px; padding: 2px 6px; overflow-wrap: anywhere; }
.editor { padding: 4px 0 8px 18px; }
.note { width: 100%; background: transparent; border: 1px solid var(--line); border-radius: 6px; padding: 6px; resize: vertical; }
.chips { display: flex; flex-wrap: wrap; gap: 6px; padding: 4px 0; }
.chip { color: var(--muted); font-size: .85em; overflow-wrap: anywhere; }
.buttons { display: flex; flex-wrap: wrap; gap: 6px; }
.export-box { width: 100%; min-height: 8rem; background: transparent; border: 1px solid var(--line); border-radius: 6px; padding: 6px; }
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/pytest tests/test_testhub_e2e.py -v`
Expected: PASS (4 tests). First-time setup if `.venv` is missing: `python3 -m venv .venv && .venv/bin/pip install pytest playwright && .venv/bin/playwright install chromium`.

- [ ] **Step 5: Commit**

```bash
git add testhub tests/test_testhub_e2e.py tests/testhub/fixtures
git commit -m "feat(testhub): hub page lists open test-todo items per game"
```

---

### Task 8: Game connection, Go, screenshot download

**Files:**
- Create: `testhub/link.js`
- Modify: `testhub/app.js` (import, create `link`, `go`/`shot` actions), `testhub/list.js` (editor with the screenshot button; see below)
- Test: `tests/test_testhub_e2e.py` (append)

**Interfaces:**
- Consumes: `CHANNEL`, `validateGameMessage`, `helloMsg`, `goMsg`, `screenshotMsg`, `newReq` (Task 4); `store.nextShotName`, `store.update`, `store.setVersion` (Task 2); `h` (Task 7).
- Produces: `createLink({ game, onChange, timeoutMs? }) -> { get conn(): {version, targets:[{id,label}], seen:number}|null, hello(), go(id): Promise<msg>, screenshot(): Promise<{type:'png', dataUrl}>, close() }`. Requests reject with an `Error` whose `code` is `'timeout'` (after 10 s) or `'noGame'` (no connection), or with the game's error message (no `code`). `onChange()` fires when connection state or the target list changes. The hub sends `hello` on creation and every 10 s; a connection with no hello for 25 s is dropped.
- `app.js` actions added: `go(item)`, `shot(item)`. The list gets an `editor(view, item, entry)` (screenshot chips and button); Task 9 extends it with the textarea and buttons.

- [ ] **Step 1: Write the failing e2e tests (append to `tests/test_testhub_e2e.py`)**

```python
def mmdd():
    return datetime.now(ZoneInfo(TZ)).strftime("%m%d")


def test_connectedStatus_showsVersionAndTargets_unknownTagIsGrey(ctx):
    open_game(ctx)
    hub = open_hub(ctx)
    expect(hub.locator(".status.on")).to_contain_text("v1.2.3 · 2 targets")
    expect(item(hub, "Typo tag item").locator("button.go")).to_have_count(0)
    expect(item(hub, "Typo tag item").locator(".go-unknown")).to_have_text("fake.typo")
    expect(item(hub, "Plain item").locator("button.go")).to_have_count(0)


def test_gameOpenedAfterHub_turnsStatusGreen(ctx):
    hub = open_hub(ctx)
    expect(hub.locator(".status.off")).to_be_visible()
    open_game(ctx)
    expect(hub.locator(".status.on")).to_contain_text("2 targets")


def test_go_runsTargetInGameWindow(ctx):
    game = open_game(ctx)
    hub = open_hub(ctx)
    expect(hub.locator(".status.on")).to_be_visible()
    item(hub, "First item inherits").locator("button.go").click()
    game.wait_for_function("window.__at === 'alpha'")


def test_lateRegisteredTarget_turnsGreyTagIntoGoButton(ctx):
    game = open_game(ctx)
    hub = open_hub(ctx)
    row = item(hub, "Second item has its own tag")
    expect(row.locator("button.go")).to_be_visible()
    expect(hub.locator(".status.on")).to_contain_text("2 targets")
    row.locator("button.go").click()
    game.wait_for_function("window.__at === 'beta'")


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
    expect(row.locator(".chip")).to_have_count(0)


def test_screenshot_downloadsNumberedFile(ctx):
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


def test_screenshot_withoutGame_isDisabled(ctx):
    hub = open_hub(ctx)
    item(hub, "First item inherits").locator("button.text").click()
    expect(item(hub, "First item inherits").locator("button.shot")).to_be_disabled()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/pytest tests/test_testhub_e2e.py -v -k "connected or opened_after or go_ or screenshot"`
Expected: FAIL (status never turns green; no `button.shot`).

- [ ] **Step 3: Write the implementation**

`testhub/link.js`:

```js
// testhub/link.js
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
    if (msg.type === 'error') entry.reject(linkError('remote', msg.message));
    else entry.resolve(msg);
  }

  function onMessage(raw) {
    const msg = validateGameMessage(raw);
    if (!msg) return;
    if (msg.type !== 'hello') { settle(msg); return; }
    if (msg.game !== game) return;
    setConn({ version: msg.version, targets: msg.targets, seen: Date.now() });
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

  function hello() {
    if (channel) channel.postMessage(helloMsg());
  }

  function poll() {
    hello();
    if (conn && Date.now() - conn.seen > STALE_MS) setConn(null);
  }

  if (channel) channel.onmessage = (event) => onMessage(event.data);
  const timer = setInterval(poll, POLL_MS);
  hello();

  return {
    get conn() { return conn; },
    hello,
    go: (id) => request((req) => goMsg(game, id, req)),
    screenshot: () => request((req) => screenshotMsg(game, req)),
    close() { clearInterval(timer); if (channel) channel.close(); },
  };
}
```

`testhub/app.js` edits:

1. Add imports after the existing ones:

```js
import { createLink } from './link.js';
```

2. Replace `let link = null; // set in Task 8` with:

```js
const link = createLink({
  game,
  onChange: () => { const c = link && link.conn; if (c) store.setVersion(game, c.version); render(); },
});
```

(`link` is referenced inside `onChange` only after construction; `onChange` can fire only from a later message, so there is no temporal-dead-zone problem. Keep `const conn = () => link.conn;` in place of the old `conn` helper.)

3. Add helpers before `const actions`:

```js
function errorText(error) {
  return error.code && error.code !== 'remote' ? t(`err_${error.code}`) : error.message;
}

function download(dataUrl, name) {
  const anchor = h('a', { href: dataUrl, download: name });
  document.body.append(anchor);
  anchor.click();
  anchor.remove();
}
```

4. Add to the `actions` object:

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

5. In `view()` nothing changes (`conn: conn()` now reads `link.conn`).

`testhub/list.js` edits: add the editor and show it when expanded.

```js
function editor(view, item, entry) {
  const { t, conn, actions } = view;
  return h('div', { class: 'editor' },
    h('div', { class: 'chips' }, entry.screenshots.map((name) => h('span', { class: 'chip' }, `📷 ${name} ✓`))),
    h('div', { class: 'buttons' },
      h('button', { class: 'shot', type: 'button', disabled: !conn, onclick: () => actions.shot(item) }, t('shot'))));
}
```

and in `renderItem`, after the `error ? … : null` line add `open ? editor(view, item, entry) : null`.

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/pytest tests/test_testhub_e2e.py -v`
Expected: PASS (all tests so far). If `test_screenshot_withoutAnswer_showsTimeoutError` is flaky because of the fake clock, replace `hub.clock.install()` / `run_for` with a short-timeout hook: export `REQUEST_TIMEOUT_MS` and read an optional `?timeout=` query value in `app.js` only when the slug page is served on `localhost`; document the choice in the commit message.

- [ ] **Step 5: Commit**

```bash
git add testhub tests/test_testhub_e2e.py
git commit -m "feat(testhub): connect to the game window, Go jumps, screenshot download"
```

---

### Task 9: Notes, Done, filter/search, Copy all with clipboard fallback

**Files:**
- Modify: `testhub/list.js` (full editor), `testhub/app.js` (actions `save`, `done`, `reopen`, copy-all button and fallback panel)
- Test: `tests/test_testhub_e2e.py` (append)

**Interfaces:**
- Consumes: `buildExport`, `isoDate` (Task 3); `store.get/update` (Task 2); `ui.drafts` (Task 7).
- Produces: actions `save(item)` (status `noted`; ignored when note and screenshots are both empty), `done(item)` (status `done`, note kept), `reopen(item)` (status `open`); `collectUnsent() -> entries[]`; `copyAll()`; **Copy all N** button `button.copy-all` (disabled at N = 0); fallback panel `textarea.export-box` plus `button.mark-sent` when the clipboard is refused. N counts items with status `noted` or `done` and `sent === false`.

- [ ] **Step 1: Write the failing e2e tests (append)**

```python
def expected_header():
    return f"Testhub feedback — fake v1.2.3 — {datetime.now(ZoneInfo(TZ)).strftime('%Y-%m-%d')}"


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
    clipboard = hub.evaluate("navigator.clipboard.readText()")
    assert clipboard == "\n".join([
        expected_header(),
        '- [Alpha block · "First item inherits the block tag" · go:fake.alpha] Turm zu dunkel',
        '- ✓ tested: [Beta block · "Typo tag item"]',
    ])
    expect(hub.locator("button.copy-all")).to_have_text("Copy all 0")
    expect(hub.locator("button.copy-all")).to_be_disabled()


def test_stateSurvivesReload_doneItemsDisappearFromOpenFilter(ctx):
    hub = open_hub(ctx)
    typo = item(hub, "Typo tag item")
    typo.locator("button.text").click()
    typo.locator("button.done").click()
    expect(item(hub, "Typo tag item")).to_have_count(0)
    hub.reload()
    expect(hub.locator(".item")).to_have_count(3)
    hub.locator("input[value=done]").check()
    expect(hub.locator(".item")).to_have_count(1)
    expect(hub.locator(".block", has_text="Beta block").locator(".progress")).to_have_text("1 / 2 ✓")


def test_noteWithScreenshot_exportsScreenshotName(ctx):
    open_game(ctx)
    hub = open_hub(ctx)
    expect(hub.locator(".status.on")).to_be_visible()
    row = item(hub, "First item inherits")
    row.locator("button.text").click()
    with hub.expect_download():
        row.locator("button.shot").click()
    row.locator("textarea.note").fill("sieht schief aus")
    row.locator("button.save").click()
    hub.bring_to_front()
    hub.locator("button.copy-all").click()
    clipboard = hub.evaluate("navigator.clipboard.readText()")
    assert clipboard.endswith(f"] sieht schief aus (📷 fb-fake-{mmdd()}-1.png)")


def test_search_filtersByTextAndNote(ctx):
    hub = open_hub(ctx)
    add_note(hub, "Plain item", "findme")
    hub.locator("input.search").fill("findme")
    expect(hub.locator(".item")).to_have_count(1)
    hub.locator("input.search").fill("")
    hub.locator("input[value=noted]").check()
    expect(hub.locator(".item")).to_have_count(1)


def test_typingInNote_survivesStatusRerender(ctx):
    hub = open_hub(ctx)
    row = item(hub, "Plain item")
    row.locator("button.text").click()
    row.locator("textarea.note").fill("half typed")
    open_game(ctx)
    expect(hub.locator(".status.on")).to_be_visible()
    expect(item(hub, "Plain item").locator("textarea.note")).to_have_value("half typed")


def test_reopen_bringsDoneItemBack(ctx):
    hub = open_hub(ctx)
    row = item(hub, "Plain item")
    row.locator("button.text").click()
    row.locator("button.done").click()
    hub.locator("input[value=done]").check()
    row = item(hub, "Plain item")
    row.locator("button.text").click()
    row.locator("button.reopen").click()
    hub.locator("input[value=open]").check()
    expect(item(hub, "Plain item")).to_have_count(1)


def test_clipboardRefused_showsTextareaWithBlock_andMarkSent(ctx):
    hub = open_hub(ctx, init_script="Object.defineProperty(navigator,'clipboard',{value:{writeText:()=>Promise.reject(new Error('no'))}})")
    add_note(hub, "Plain item", "x")
    hub.locator("button.copy-all").click()
    box = hub.locator("textarea.export-box")
    expect(box).to_be_visible()
    expect(box).to_have_value(re.compile(r"^Testhub feedback — fake .* — \d{4}-\d\d-\d\d\n- \[Beta block · \"Plain item\"\] x$"))
    expect(hub.locator("button.copy-all")).to_have_text("Copy all 1")
    hub.locator("button.mark-sent").click()
    expect(box).to_have_count(0)
    expect(hub.locator("button.copy-all")).to_have_text("Copy all 0")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/pytest tests/test_testhub_e2e.py -v -k "note or Done or reload or search or typing or reopen or clipboard"`
Expected: FAIL (`textarea.note` and `button.copy-all` do not exist).

- [ ] **Step 3: Write the implementation**

`testhub/list.js`: replace the `editor` function from Task 8 with the full version:

```js
function editor(view, item, entry) {
  const { t, conn, actions, drafts } = view;
  const draft = drafts.has(item.key) ? drafts.get(item.key) : entry.note;
  const area = h('textarea', {
    class: 'note', rows: 3, placeholder: t('notePlaceholder'), 'data-focus': `note:${item.key}`,
    oninput: (e) => drafts.set(item.key, e.target.value),
  }, draft);
  const finish = entry.status === 'done'
    ? h('button', { class: 'reopen', type: 'button', onclick: () => actions.reopen(item) }, t('reopen'))
    : h('button', { class: 'done', type: 'button', onclick: () => actions.done(item) }, t('done'));
  return h('div', { class: 'editor' }, area,
    h('div', { class: 'chips' }, entry.screenshots.map((name) => h('span', { class: 'chip' }, `📷 ${name} ✓`))),
    h('div', { class: 'buttons' },
      h('button', { class: 'shot', type: 'button', disabled: !conn, onclick: () => actions.shot(item) }, t('shot')),
      h('button', { class: 'save', type: 'button', onclick: () => actions.save(item) }, t('save')),
      finish));
}
```

`testhub/app.js` edits:

1. Imports: `import { buildExport, isoDate } from './export.js';`
2. Extend `ui` with `notice: null, manual: null` (manual = `{ text, keys }` while the clipboard fallback panel is shown).
3. Add helpers and actions (before `const actions`, and inside it):

```js
function draftFor(item) {
  return ui.drafts.has(item.key) ? ui.drafts.get(item.key) : store.get(item.key).note;
}

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

function markSent(entries) {
  for (const entry of entries) store.update(entry.key, { sent: true });
}

async function copyAll() {
  const entries = collectUnsent();
  if (entries.length === 0) return;
  const version = (conn() && conn().version) || store.version(game);
  const text = buildExport({ game, version, date: isoDate(new Date()), entries });
  ui.notice = null;
  try {
    await navigator.clipboard.writeText(text);
    markSent(entries);
    ui.manual = null;
    ui.notice = t('copied', { n: entries.length });
  } catch (error) {
    ui.manual = { text, entries };
  }
  render();
}
```

Actions to add inside `actions`:

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
  reopen(item) {
    store.update(item.key, { status: 'open' });
    render();
  },
  copyAll,
  markSent() {
    markSent(ui.manual.entries);
    ui.manual = null;
    render();
  },
```

4. In `statusBar()` append the copy button to both returned elements. Replace the function with:

```js
function copyButton() {
  const n = collectUnsent().length;
  return h('button', { class: 'copy-all', type: 'button', disabled: n === 0, onclick: actions.copyAll }, t('copyAll', { n }));
}

function statusBar() {
  const c = conn();
  const line = c
    ? [h('span', {}, '● ', t('connected', { version: c.version, n: c.targets.length }))]
    : [h('span', {}, '● ', t('disconnected'), ' ',
      h('a', { href: `/game-${game}/?dev=1`, target: '_blank', rel: 'noopener' }, t('openGame')))];
  return h('div', { class: `status ${c ? 'on' : 'off'}` }, line, copyButton());
}
```

5. In `notices()` return the fallback panel and the success notice too:

```js
function notices() {
  const manual = ui.manual && h('div', { class: 'notice' },
    h('p', {}, t('copyManual')),
    h('textarea', { class: 'export-box', readonly: true, 'data-focus': 'export' }, ui.manual.text),
    h('button', { class: 'mark-sent', type: 'button', onclick: actions.markSent }, t('markSent')));
  return [
    store.isPersistent() ? null : h('p', { class: 'notice warn' }, t('noStorage')),
    ui.notice ? h('p', { class: 'notice ok' }, ui.notice) : null,
    manual,
  ];
}
```

6. After the fallback `textarea` is rendered, select its text: at the end of `render()`, add

```js
  const box = document.querySelector('.export-box');
  if (box) box.select();
```

Add to `style.css`: `.status { display: flex; justify-content: space-between; gap: 8px; flex-wrap: wrap; align-items: center; }` and `.notice.ok { color: var(--ok); }`.

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/pytest tests/test_testhub_e2e.py -v` and `node --test tests/testhub/*.test.mjs`
Expected: PASS for both.

- [ ] **Step 5: Commit**

```bash
git add testhub tests/test_testhub_e2e.py
git commit -m "feat(testhub): notes, done marks, filters and Copy all with clipboard fallback"
```

---

### Task 10: Hardening tests (foreign messages, second game, narrow window, German)

**Files:**
- Test: `tests/test_testhub_e2e.py` (append). Production files only change if a test fails; fix the owning module (`protocol.js`, `link.js`, `client.js`, `style.css`, `strings.js`).

**Interfaces:**
- Consumes: everything from Tasks 4-9. These tests pin Review Focus items 1 and 2 plus the narrow-layout and `gg-lang` requirements at e2e level. They are expected to pass on first run; a failure is a real defect to fix.

- [ ] **Step 1: Write the tests (append)**

```python
def test_foreignAndMalformedMessages_areIgnored(ctx):
    errors = []
    game = open_game(ctx)
    game.on("pageerror", lambda e: errors.append(str(e)))
    hub = open_hub(ctx, errors)
    expect(hub.locator(".status.on")).to_contain_text("v1.2.3")
    game.evaluate("""() => {
      const c = new BroadcastChannel('gg-testhub');
      c.postMessage({ type: 'hello', game: 'fake', version: '9', targets: 'nope' });
      c.postMessage({ type: 'hello', game: 'fake', version: '9', targets: [{ id: '<script>', label: 'x' }] });
      c.postMessage({ type: 'png', req: 5, dataUrl: 'data:text/html;base64,AAAA' });
      c.postMessage({ type: 'error', req: 'unknown-req', message: 'x' });
      c.postMessage({ type: 'go', id: '<script>', req: 'r' });
      c.postMessage('garbage');
      c.postMessage(null);
      c.close();
    }""")
    hub.wait_for_timeout(300)
    expect(hub.locator(".status.on")).to_contain_text("v1.2.3 · 2 targets")
    assert game.evaluate("window.__at") is None
    assert errors == []


def test_otherGameWindow_doesNotChangeStatus(ctx):
    open_game(ctx)
    hub = open_hub(ctx)
    expect(hub.locator(".status.on")).to_contain_text("v1.2.3")
    other = ctx.new_page()
    other.goto(f"{ORIGIN}/game-fake/")
    other.evaluate("""() => {
      const c = new BroadcastChannel('gg-testhub');
      c.postMessage({ type: 'hello', game: 'other', version: '7.7.7', targets: [] });
    }""")
    hub.wait_for_timeout(300)
    expect(hub.locator(".status.on")).to_contain_text("v1.2.3 · 2 targets")


def test_narrowWindow_hasNoHorizontalScroll(browser):
    ctx = new_context(browser, viewport={"width": 360, "height": 700})
    try:
        open_game(ctx)
        hub = open_hub(ctx)
        expect(hub.locator(".status.on")).to_be_visible()
        row = item(hub, "Second item has its own tag")
        row.locator("button.text").click()
        assert hub.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
    finally:
        ctx.close()


def test_ggLang_de_switchesUiStringsNotItemText(ctx):
    open_game(ctx)
    hub = open_hub(ctx, init_script="localStorage.setItem('gg-lang','de')")
    expect(hub.locator(".status.on")).to_contain_text("Spiel verbunden (v1.2.3 · 2 Ziele)")
    expect(hub.locator("button.copy-all")).to_have_text("Alle kopieren 0")
    expect(item(hub, "First item inherits the block tag")).to_be_visible()
    hub.locator("button.lang").click()
    expect(hub.locator("button.copy-all")).to_have_text("Copy all 0")
```

- [ ] **Step 2: Run tests**

Run: `.venv/bin/pytest tests/test_testhub_e2e.py -v`
Expected: PASS. If one fails, fix the owning module (not the test), rerun the full suite and `node --test tests/testhub/*.test.mjs`.

- [ ] **Step 3: Commit**

```bash
git add tests/test_testhub_e2e.py testhub
git commit -m "test(testhub): pin foreign messages, second game, narrow layout and German UI"
```

---

### Task 11: Documentation for game repos and contributors

**Files:**
- Modify: `CLAUDE.md` (new "Testhub" section), `CONTRIBUTING.md` (the "There is no test suite" sentence and layout list)
- Test: none (docs); verify with the full test run.

**Interfaces:**
- Produces: the loader snippet and API reference that the Rhyflitzer plan and the ai-instructions stack overlay copy from.

- [ ] **Step 1: Add the Testhub section to `CLAUDE.md`** (after the Umami section)

````markdown
## Testhub (playtest hub)

`/testhub/` lists each game's open `test-todo.md` items (`- [ ]` under `## ` blocks), jumps the
game to the place an item is about, and exports notes with **Copy all**. Spec:
`freaxnx01/game-rhyflitzer` `docs/superpowers/specs/2026-10-11-testhub-design.md`. State is in
`localStorage['gg-testhub']`, messages travel on `BroadcastChannel('gg-testhub')`.

- Add a game: append its slug to `GAMES` in `testhub/app.js`; `?game=<slug>` also works ad hoc.
- A game loads `client.js` async and only in dev mode. Put this loader in its `index.html`:

```html
<script>
try {
  var dev = /[?&]dev=([01])/.exec(location.search);
  if (dev && dev[1] === '1') localStorage.setItem('gg-dev', '1');
  if (dev && dev[1] === '0') localStorage.removeItem('gg-dev');
  if (localStorage.getItem('gg-dev') === '1') {
    var s = document.createElement('script');
    s.src = '/testhub/client.js';
    s.async = true;
    document.head.appendChild(s);
  }
} catch (e) { /* no dev mode without storage */ }
</script>
```

- The client fires `gg-testhub-ready` on `window` once `window.ggTesthub` exists, so register like
  `if (window.ggTesthub) boot(); else window.addEventListener('gg-testhub-ready', boot);`
  (it never fires outside dev mode, so players load nothing).
- API: `ggTesthub.setInfo({ game, version })` once (`game` = repo slug without `game-`,
  `version` without a leading `v`), `ggTesthub.register(id, fn, label)` (`id` `[a-z0-9._-]+`,
  a repeated id replaces the earlier one, `fn()` is synchronous and its return value is ignored),
  `ggTesthub.onScreenshot(fn)` (`fn()` returns a promise of a PNG data URL; it may reject with a
  message, which the hub shows, or hang, which the hub's 10 s timeout covers).
  Each call makes the client send a fresh `hello` with all targets.
- Tag items in `test-todo.md` with `{go: <id>}`; a tag on the `## ` heading is inherited.
- Tests: `node --test tests/testhub/*.test.mjs` and `.venv/bin/pytest tests/test_testhub_e2e.py`.
````

- [ ] **Step 2: Update `CONTRIBUTING.md`**

Replace the sentence `There is no test suite.` with `Tests live in tests/: pytest + Playwright for the scripts and the Testhub e2e (.venv, see CLAUDE.md), node --test for the Testhub modules (node --test tests/testhub/*.test.mjs).` and add to the Layout list: `- testhub/ — the playtest hub (index.html, ES modules) and client.js, the one script games load in dev mode.`

- [ ] **Step 3: Run the whole suite**

Run: `node --test tests/testhub/*.test.mjs && .venv/bin/pytest tests -v`
Expected: PASS (the pre-existing `tests/test_*.py` still pass).

- [ ] **Step 4: Commit**

```bash
git add CLAUDE.md CONTRIBUTING.md
git commit -m "docs(testhub): document loader, client API and test commands"
```

---

## Self-Review

- **Spec coverage:** hub page and picker (Task 7), parser rules (1), state key and try/catch (2), UI list/status/Go/greyed tag/note/Save/Done/progress/collapse/filter (7-9), narrow layout and `gg-lang` (5, 7, 10), client API and validated messages and unknown-id error (6), several game windows (4, 8, 10), screenshot file name and download (2, 8), Copy all format, sent marks, clipboard fallback (3, 9), all five error-handling cases (7 load/storage, 8 timeout/no game, 9 clipboard, 7 missing todo), tests (1-6 node, 7-10 Playwright). Not in this plan by design: Rhyflitzer integration, ai-instructions overlay, `/processing-test-feedback` format note.
- **Spec extensions (small, compatible):** `go`/`screenshot` carry `game`; `go` carries `req` and is answered by `done {req}`; the client fires `gg-testhub-ready` and sends a first `hello` on load (loader is async, per the Rhyflitzer contract); the hub polls `hello` every 10 s and drops a connection silent for 25 s; a `Reopen` button undoes Done.
- **Type consistency:** `createLink` returns `conn`/`go`/`screenshot` used by `app.js`; `store.update/get/nextShotName/setVersion/version/isPersistent` match Task 2; `view` fields used by `list.js` (`t, blocks, store, filter, query, expanded, collapsed, drafts, errors, conn, actions`) are all supplied by `view()` in `app.js`; message builders and validators match `client.js`.
