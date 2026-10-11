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
  assert.throws(() => api.register('Bad Id', () => {}), { name: 'TypeError' });
});
