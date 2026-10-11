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
