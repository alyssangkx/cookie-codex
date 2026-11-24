import { test } from 'node:test';
import assert from 'node:assert/strict';
import { wordBox, strikes, passageEnd } from './cloze.ts';

test('wordBox reads the box line and leaves the passage', () => {
  assert.deepEqual(wordBox('Word box: a · and · it’s\n\nAndy (29) ________ ran.'), { words: ['a', 'and', 'it’s'], rest: 'Andy (29) ________ ran.' });
  assert.deepEqual(wordBox('No box (1) ____.'), { words: [], rest: 'No box (1) ____.' });
});

test('strikes: one word per tick, notes for a word not in the box or already used; case and curly apostrophes ignored', () => {
  const r = strikes(['a', 'the', "it's", 'the'], ['The', 'the', 'THE', 'of', 'it’s']);
  assert.deepEqual([...r.struck].sort(), [1, 2, 3]);
  assert.deepEqual(r.notes, ['ok', 'ok', 'used', 'not-in-box', 'ok']);
});

test('passageEnd: the run of one passage group from i, nothing else', () => {
  const g: Record<string, string | null> = { a1: 'A', a2: 'A', b1: 'B', m: null, a3: 'A' };
  const ids = ['a1', 'a2', 'b1', 'm', 'a3'];
  assert.equal(passageEnd(ids, 0, (id) => g[id]), 2);
  assert.equal(passageEnd(ids, 2, (id) => g[id]), 3);
  assert.equal(passageEnd(ids, 3, (id) => g[id]), 4, 'an item outside any passage is a run of one');
  assert.equal(passageEnd(ids, 4, (id) => g[id]), 5);
});
