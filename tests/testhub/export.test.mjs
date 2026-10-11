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
