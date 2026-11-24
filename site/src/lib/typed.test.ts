import { test } from 'node:test';
import assert from 'node:assert/strict';
import { compose, norm, typedOk, scaffoldHtml } from './typed.ts';

const esc = (s: string) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;');
const sc = 'However ____, I still did not go to the party.';
const key = ['However hard Julia tried to persuade me, I still did not go to the party.'];

test('compose fills each blank in order; no scaffold means one box', () => {
  assert.equal(compose(sc, ['hard Julia tried to persuade me']), key[0]);
  assert.equal(compose('____ unless ____.', ['We will run out of water', 'everyone saves it']), 'We will run out of water unless everyone saves it.');
  assert.equal(compose(null, ['  because  ']), 'because');
});

test('what counts: words and order; capitals, spaces, quotes, commas and full stops do not', () => {
  assert.ok(typedOk(sc, ['hard julia tried to persuade me'], key));
  assert.ok(typedOk(sc, ['  hard  Julia   tried to persuade me  '], key));
  assert.ok(typedOk('The teacher reminded the students, ____', ['"Memorise your lines."'], ['The teacher reminded the students, “Memorise your lines.”']));
  assert.ok(!typedOk(sc, ['Julia hard tried to persuade me'], key), 'word order counts');
  assert.ok(!typedOk(sc, ['hard Julia tried to persuaded me'], key), 'a wrong word form counts');
  assert.ok(!typedOk(sc, [''], key) && !typedOk('____ unless ____.', ['a', ' '], ['a unless b.']), 'an empty box is never right');
});

test('apostrophes inside words count; quote marks around words do not', () => {
  assert.equal(norm("Devi said, ‘I don’t know.’"), "devi said i don't know");
  assert.ok(norm("I don't") !== norm('I dont'));
  assert.equal(norm('a well-known writer'), 'a well-known writer');
  assert.equal(norm('a well - known writer'), 'a well known writer', 'a spaced dash is punctuation, not a hyphen');
});

test('any accepted answer is right', () => {
  const acc = ['Unless everyone drinks as little as possible, we will run out of water.', 'Unless everybody drinks as little as possible, we will run out of water.'];
  assert.ok(typedOk('Unless ____', ['everybody drinks as little as possible, we will run out of water'], acc));
});

test('scaffoldHtml puts one box in each blank and escapes the printed words', () => {
  const h = scaffoldHtml('A <b> ____ and ____.', esc);
  assert.equal((h.match(/<input /g) ?? []).length, 2);
  assert.ok(h.includes('A &lt;b> ') && h.includes('data-n="1"'));
  assert.equal((scaffoldHtml(null, esc).match(/<input /g) ?? []).length, 1);
});

test('repeated calls on different scaffolds give the same result (no regex state carried over)', () => {
  for (let i = 0; i < 3; i++) {
    assert.equal(compose('Neither ____.', ['the twins nor their brother enjoys cycling']), 'Neither the twins nor their brother enjoys cycling.');
    assert.equal((scaffoldHtml('Having ____, John left.', esc).match(/<input /g) ?? []).length, 1);
  }
});

test('review fixes: plural possessives, dashes, other scripts, symbol-only answers', () => {
  assert.ok(!typedOk(null, ['The students bags were heavy'], ["The students' bags were heavy."]), "students' keeps its apostrophe");
  assert.ok(typedOk(null, ["The students' bags were heavy"], ['The students’ bags were heavy.']));
  assert.ok(typedOk(null, ['a well-known writer'], ['a well–known writer']), 'an en dash inside a word is a hyphen');
  assert.ok(typedOk(null, ['Mr Tan, our teacher, left'], ['Mr Tan - our teacher - left']), 'a spaced dash is punctuation');
  assert.ok(typedOk(null, ['的'], ['的']) && !typedOk(null, ['我'], ['的']), 'a Chinese answer is compared, not erased');
  assert.ok(!typedOk(null, ['!!'], ['?']), 'an answer of only symbols matches nothing');
  assert.equal(norm("'Do you know?' Tessa asked."), 'do you know tessa asked');
});
