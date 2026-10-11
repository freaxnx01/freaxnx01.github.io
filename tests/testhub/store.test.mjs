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

test('toggleDone_openEntry_marksDoneKeepingNote', () => {
  const store = createStore(fakeStorage());
  assert.equal(store.toggleDone('k', 'hello'), 'done');
  assert.deepEqual([store.get('k').status, store.get('k').note], ['done', 'hello']);
});

test('toggleDone_unsentDone_goesBackToOpen', () => {
  const store = createStore(fakeStorage());
  store.toggleDone('k', '');
  assert.equal(store.toggleDone('k', ''), 'open');
  assert.equal(store.get('k').status, 'open');
});

test('toggleDone_unsentDoneWithNote_goesBackToNoted', () => {
  const store = createStore(fakeStorage());
  store.toggleDone('k', 'a note');
  assert.equal(store.toggleDone('k', 'a note'), 'noted');
});

test('toggleDone_sentDone_staysDoneAndSent', () => {
  const store = createStore(fakeStorage());
  store.toggleDone('k', '');
  store.update('k', { sent: true });
  assert.equal(store.toggleDone('k', ''), null);
  assert.deepEqual([store.get('k').status, store.get('k').sent], ['done', true]);
});
