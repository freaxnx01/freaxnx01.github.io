import test from 'node:test';
import assert from 'node:assert/strict';
import { createStore } from '../../testhub/store.js';

const fakeStorage = (initial) => {
  const data = new Map(initial ? [['gg-testhub', initial]] : []);
  return { getItem: (k) => (data.has(k) ? data.get(k) : null), setItem: (k, v) => data.set(k, v) };
};

test('get_unknownKey_returnsOpenDefaults', () => {
  assert.deepEqual(createStore(fakeStorage()).get('k'), { status: 'open', notes: [], draftShots: [], sent: false });
});

test('update_persistsAndResetsSent', () => {
  const storage = fakeStorage();
  const store = createStore(storage);
  store.update('k', { status: 'done', sent: true });
  assert.equal(store.get('k').sent, true);
  store.update('k', { status: 'done' });
  assert.equal(store.get('k').sent, false);
  assert.equal(createStore(storage).get('k').status, 'done');
});

test('createStore_corruptJson_startsEmpty', () => {
  assert.equal(createStore(fakeStorage('{not json')).get('k').status, 'open');
});

test('nextShotName_countsUpPerGameAndDay', () => {
  const store = createStore(fakeStorage());
  const day = new Date(2026, 9, 11);
  assert.equal(store.nextShotName('rhyflitzer', day), 'fb-rhyflitzer-1011-1.png');
  store.addDraftShot('b', 'fb-rhyflitzer-1011-3.png');
  store.addDraftShot('b', 'fb-other-1011-9.png');
  assert.equal(store.nextShotName('rhyflitzer', day), 'fb-rhyflitzer-1011-4.png');
  store.addNote('b', 'x', 1);
  assert.equal(store.nextShotName('rhyflitzer', day), 'fb-rhyflitzer-1011-4.png');
  assert.equal(store.nextShotName('rhyflitzer', new Date(2026, 9, 12)), 'fb-rhyflitzer-1012-1.png');
});

test('toggleDone_openEntry_marksDone', () => {
  const store = createStore(fakeStorage());
  assert.equal(store.toggleDone('k'), 'done');
  assert.equal(store.get('k').status, 'done');
});

test('toggleDone_unsentDone_goesBackToOpen', () => {
  const store = createStore(fakeStorage());
  store.toggleDone('k');
  assert.equal(store.toggleDone('k'), 'open');
});

test('toggleDone_unsentDoneWithNote_goesBackToNoted', () => {
  const store = createStore(fakeStorage());
  store.addNote('k', 'a note', 1);
  store.toggleDone('k');
  assert.equal(store.toggleDone('k'), 'noted');
});

test('toggleDone_sentDone_staysDoneAndSent', () => {
  const store = createStore(fakeStorage());
  store.toggleDone('k');
  store.markSent('k', [], true);
  assert.equal(store.toggleDone('k'), null);
  assert.deepEqual([store.get('k').status, store.get('k').sent], ['done', true]);
});

test('addNote_twice_appendsTwoNotesAndStatusIsNoted', () => {
  const store = createStore(fakeStorage());
  assert.equal(store.addNote('k', ' first ', 10), true);
  store.addNote('k', 'second', 20);
  const entry = store.get('k');
  assert.deepEqual(entry.notes, [
    { text: 'first', ts: 10, screenshots: [], sent: false },
    { text: 'second', ts: 20, screenshots: [], sent: false },
  ]);
  assert.equal(entry.status, 'noted');
});

test('addNote_emptyTextAndNoDraftShot_isRefused', () => {
  const store = createStore(fakeStorage());
  assert.equal(store.addNote('k', '   ', 1), false);
  assert.equal(store.get('k').notes.length, 0);
});

test('addNote_withDraftShots_attachesThemToThatNoteOnly', () => {
  const store = createStore(fakeStorage());
  store.addDraftShot('k', 'a.png');
  store.addNote('k', 'one', 1);
  store.addNote('k', 'two', 2);
  const entry = store.get('k');
  assert.deepEqual(entry.notes.map((n) => n.screenshots), [['a.png'], []]);
  assert.deepEqual(entry.draftShots, []);
});

test('addNote_onDoneItem_keepsDoneAndSentLock', () => {
  const store = createStore(fakeStorage());
  store.toggleDone('k');
  store.markSent('k', [], true);
  store.addNote('k', 'late', 1);
  assert.deepEqual([store.get('k').status, store.get('k').sent], ['done', true]);
});

test('deleteNote_unsent_removesIt', () => {
  const store = createStore(fakeStorage());
  store.addNote('k', 'a', 1);
  store.addNote('k', 'b', 2);
  assert.equal(store.deleteNote('k', 0), true);
  assert.deepEqual(store.get('k').notes.map((n) => n.text), ['b']);
  store.deleteNote('k', 0);
  assert.equal(store.get('k').status, 'open');
});

test('deleteNote_sent_isRefused', () => {
  const store = createStore(fakeStorage());
  store.addNote('k', 'a', 1);
  store.markSent('k', [0], false);
  assert.equal(store.deleteNote('k', 0), false);
  assert.equal(store.get('k').notes.length, 1);
});

test('markSent_onlyGivenNotes_leavesOthersUnsent', () => {
  const store = createStore(fakeStorage());
  store.addNote('k', 'a', 1);
  store.addNote('k', 'b', 2);
  store.markSent('k', [0], false);
  assert.deepEqual(store.get('k').notes.map((n) => n.sent), [true, false]);
});

test('createStore_legacySingleNote_migratesToOneElementList', () => {
  const legacy = JSON.stringify({ v: 1, versions: { g: '1' }, items: {
    a: { status: 'noted', note: 'alt', screenshots: ['s.png'], sent: false },
    b: { status: 'noted', note: 'gesendet', screenshots: [], sent: true },
    c: { status: 'done', note: '', screenshots: [], sent: false },
    d: { status: 'open', note: '', screenshots: [], sent: false },
  } });
  const store = createStore(fakeStorage(legacy));
  assert.deepEqual(store.get('a').notes, [{ text: 'alt', ts: null, screenshots: ['s.png'], sent: false }]);
  assert.equal(store.get('a').status, 'noted');
  assert.deepEqual(store.get('b').notes, [{ text: 'gesendet', ts: null, screenshots: [], sent: true }]);
  assert.equal(store.get('c').status, 'done');
  assert.deepEqual(store.get('c').notes, []);
  assert.equal(store.get('d').status, 'open');
  assert.equal(store.version('g'), '1');
});

test('createStore_migratedData_isPersistedInNewShapeOnNextSave', () => {
  const storage = fakeStorage(JSON.stringify({ v: 1, items: { a: { status: 'noted', note: 'alt', screenshots: [], sent: false } } }));
  const store = createStore(storage);
  store.addNote('a', 'neu', 5);
  const again = createStore(storage).get('a');
  assert.deepEqual(again.notes.map((n) => n.text), ['alt', 'neu']);
});
