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
