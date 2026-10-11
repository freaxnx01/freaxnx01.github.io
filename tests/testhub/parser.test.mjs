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
