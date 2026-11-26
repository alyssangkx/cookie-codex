import test from 'node:test';
import assert from 'node:assert/strict';
import { blanksIn, replaceBlanks, hasOwnBlank, dropAskedLine, textFigureHtml, choose, place, unplace, usedPhrases, emptyBlanks, nextEmpty, optionIndex, setCorrections } from './passageset.ts';

const esc = (x: string) => x.replace(/[&<>"]/g, (c) => `&#${c.charCodeAt(0)};`);

test('replaceBlanks finds Chinese and English blanks, asked or not', () => {
  const r = replaceBlanks('甲：（1）＿＿＿＿ 乙：（2）＿＿＿＿ and (3) ____ then (4) ________.', (n) => `[${n}]`);
  assert.equal(r.html, '甲：[1] 乙：[2] and [3] then [4].');
  assert.deepEqual([...r.found], [1, 2, 3, 4]);
  assert.equal(replaceBlanks('no blanks', () => 'x').found.size, 0);
});

test('hasOwnBlank: a whole-passage stem has it, a one-sentence stem does not', () => {
  assert.ok(hasOwnBlank('甲：（2）＿＿＿＿', 2));
  assert.ok(hasOwnBlank('Tom went (3) ________ home', 3));
  assert.ok(!hasOwnBlank('第（2）空应填什么？', 2));
  assert.ok(!hasOwnBlank('甲：（1）＿＿＿＿', 2));
  assert.ok(!hasOwnBlank('甲：（1）＿＿＿＿', undefined));
});

test('dropAskedLine removes only the trailing asked-blank line', () => {
  assert.equal(dropAskedLine('甲：（1）＿＿＿＿\n\n第（1）空应填什么？'), '甲：（1）＿＿＿＿');
  assert.equal(dropAskedLine('甲：（1）＿＿＿＿'), '甲：（1）＿＿＿＿');
});

test('textFigureHtml escapes and splits paragraphs on blank lines', () => {
  const h = textFigureHtml('One <b>two</b>\nstill one\n\n\nThree & "four"', esc);
  assert.equal((h.match(/<p>/g) ?? []).length, 2);
  assert.ok(!h.includes('<b>'));
  assert.ok(h.includes('&#60;b&#62;') && h.includes('&#38;') && h.includes('<br>'));
  assert.equal(textFigureHtml('   ', esc), '<div class="qfig-text"></div>');
});

test('chips: choosing again changes the pick, nothing else moves', () => {
  let p = choose(new Map(), 1, 2);
  p = choose(p, 3, 0);
  p = choose(p, 1, 3);
  assert.deepEqual([...p], [[1, 3], [3, 0]]);
});

test('dialogue: place, move, replace and return', () => {
  let p = place(new Map(), 5, 1);
  assert.deepEqual([...usedPhrases(p)], [5]);
  p = place(p, 5, 2); // the same phrase on another blank leaves the first
  assert.deepEqual([...p], [[2, 5]]);
  p = place(p, 6, 2); // a new phrase on a filled blank: the old one is back in the bank
  assert.deepEqual([...p], [[2, 6]]);
  assert.ok(!usedPhrases(p).has(5));
  p = unplace(p, 2);
  assert.equal(p.size, 0);
  assert.equal(unplace(p, 9).size, 0);
});

test('place and unplace never change the map they are given', () => {
  const p = new Map([[1, 0]]);
  place(p, 1, 2); unplace(p, 1); choose(p, 1, 3);
  assert.deepEqual([...p], [[1, 0]]);
});

test('emptyBlanks and nextEmpty walk the blanks in order and wrap', () => {
  const seqs = [1, 2, 3, 4];
  const p = new Map([[1, 0], [3, 1]]);
  assert.deepEqual(emptyBlanks(seqs, p), [2, 4]);
  assert.equal(nextEmpty(seqs, p, 1), 2);
  assert.equal(nextEmpty(seqs, p, 2), 4);
  assert.equal(nextEmpty(seqs, p, 4), 2);
  assert.equal(nextEmpty(seqs, new Map([[1, 0], [2, 1], [3, 2], [4, 3]]), 4), null);
});

test('optionIndex matches a phrase by text, whatever the option order', () => {
  assert.equal(optionIndex(['b', 'a', 'c'], 'a'), 1);
  assert.equal(optionIndex(['b'], 'z'), -1);
});

test('setCorrections: right green, wrong struck with the answer, given grey, unmarked stays a blank; text is escaped', () => {
  const html = '（1）＿＿＿＿ （2）＿＿＿＿ (3) ____ (4) ____ （5）＿＿＿＿';
  const r = setCorrections(html, new Map([
    [1, { kind: 'right' as const, answer: '好<' }],
    [2, { kind: 'wrong' as const, picked: '坏', answer: '对' }],
    [3, { kind: 'wrong' as const, picked: null, answer: 'went' }],
    [4, { kind: 'given' as const, answer: 'to' }],
  ]), esc);
  assert.ok(r.html.includes('（1）<span class="filled">好&#60;</span>'));
  assert.ok(r.html.includes('<del>坏</del> <strong>对</strong>'));
  assert.ok(r.html.includes('(3) <span class="cx-none">(no answer)</span> <strong>went</strong>'));
  assert.ok(r.html.includes('(4) <span class="filled given"'));
  assert.ok(r.html.endsWith('（5）＿＿＿＿'));
  assert.deepEqual([...r.placed].sort(), [1, 2, 3, 4]);
});

// 26 Nov 2026 review: hasOwnBlank accepted a blank the passage drawing does not (one ＿, or "(3) ___"), so a set went
// inline with a question that had no chip. Both now use the same pattern.
test('hasOwnBlank and blanksIn agree with the blanks replaceBlanks draws', () => {
  for (const s of ['他（3）＿听到', '(3) ___ here', '(3)__']) { assert.equal(hasOwnBlank(s, 3), false, s); assert.equal(blanksIn(s).size, 0, s); }
  for (const s of ['他（3）＿＿＿＿听到', '(3) ____ here', '(3) ________']) { assert.equal(hasOwnBlank(s, 3), true, s); assert.deepEqual([...blanksIn(s)], [3], s); }
});
