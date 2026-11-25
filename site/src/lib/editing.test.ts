import { test } from 'node:test';
import assert from 'node:assert/strict';
import { editingMarks, editingHtml, editAsk, editCorrections } from './editing.ts';
import { esc } from './boldans.ts';
import { typedOk } from './typed.ts';
import { readFileSync } from 'node:fs';

// a made-up passage (no past-paper text)
const stem = 'The cat {{1|sleeped}} on the mat. It was {{2|verry}} happy, and the dog {{3|run}} away from {{4|it}}.';

test('editingMarks lists each asked word by number', () => {
  assert.deepEqual([...editingMarks(stem)], [[1, 'sleeped'], [2, 'verry'], [3, 'run'], [4, 'it']]);
  assert.equal(editingMarks('no marks here').size, 0);
  assert.deepEqual([...editingMarks('a {{ 7 | wrod }} b {{7|dup}}')], [[7, 'wrod']]); // spaces allowed; first one wins
});

test('editingHtml replaces every mark, leaving the rest of the text alone', () => {
  assert.equal(editingHtml(stem, (n, w) => `[${n}:${w}]`), 'The cat [1:sleeped] on the mat. It was [2:verry] happy, and the dog [3:run] away from [4:it].');
});

test('editAsk puts the number, the printed word and the box together', () => {
  const h = editAsk(5, 'wrod', '<input class="cz">');
  assert.match(h, /<b>\(5\)<\/b> <u>wrod<\/u>/);
  assert.ok(h.indexOf('<u>wrod</u>') < h.indexOf('<input class="cz">'));
  assert.ok(h.includes('class="cz-note"')); // the page writes its "already used" notes beside the box
  // the line may break between the word and its box (the paragraph wraps like text), never inside "(5) wrod" or "→ box"
  assert.match(h, /<\/u><\/span><wbr><span class="ed-pair"><span class="ed-arrow"[^>]*>→<\/span><input[^>]*><\/span>/);
});

test('editCorrections: wrong, empty, right, given and untouched marks', () => {
  const marks = new Map<number, { kind: 'right' | 'wrong' | 'given'; typed?: string | null; answer: string }>([
    [1, { kind: 'wrong', typed: 'sleepd', answer: 'slept' }],
    [2, { kind: 'right', typed: null, answer: 'very' }],
    [3, { kind: 'wrong', typed: '', answer: 'ran' }],
    [4, { kind: 'given', answer: 'them' }],
  ]);
  const { html, placed } = editCorrections(esc(stem), marks, esc);
  assert.deepEqual([...placed], [1, 2, 3, 4]);
  assert.match(html, /<mark class="cx-fix"><b>\(1\)<\/b> <del class="ed-was">sleeped<\/del> <del class="cx-typed">sleepd<\/del> <strong>slept<\/strong><\/mark>/);
  assert.match(html, /<span class="ed-fix"><b>\(2\)<\/b> <del class="ed-was">verry<\/del> <span class="filled">very<\/span><\/span>/);
  assert.match(html, /\(3\)<\/b> <del class="ed-was">run<\/del> <span class="cx-none">\(no answer\)<\/span> <strong>ran<\/strong>/);
  assert.match(html, /<span class="filled given" title="not in this quiz">them<\/span>/);
  assert.ok(!html.includes('{{'));
  // a mark with no entry stays as the printed word, and is not "placed"
  const only = editCorrections(esc(stem), new Map([[2, { kind: 'right' as const, typed: null, answer: 'very' }]]), esc);
  assert.deepEqual([...only.placed], [2]);
  assert.match(only.html, /<u>sleeped<\/u>/);
});

test('typing the printed wrong word again is shown once and is a wrong answer', () => {
  const { html } = editCorrections(esc(stem), new Map([[1, { kind: 'wrong' as const, typed: 'Sleeped', answer: 'slept' }]]), esc);
  assert.ok(!html.includes('cx-typed'));
  assert.match(html, /<del class="ed-was">sleeped<\/del> <strong>slept<\/strong>/);
});

test('what the child typed is escaped', () => {
  const { html } = editCorrections(esc(stem), new Map([[1, { kind: 'wrong' as const, typed: '<b>x</b>', answer: 'slept' }]]), esc);
  assert.ok(!html.includes('<b>x</b>'));
  assert.match(html, /&#60;b&#62;x&#60;\/b&#62;/);
});

test('marking: the correct spelling or word is right (any case); the printed wrong word again, or an empty box, is wrong', () => {
  assert.ok(typedOk(null, ['slept'], ['slept']));
  assert.ok(typedOk(null, [' Slept '], ['slept']));
  assert.ok(!typedOk(null, ['sleeped'], ['slept']));
  assert.ok(!typedOk(null, [''], ['slept']));
});

test('the syllabus flags Editing (editing: true) and no other section', () => {
  const syl = JSON.parse(readFileSync(new URL('../data/syllabus/english.json', import.meta.url), 'utf8'));
  const flagged = syl.strands.flatMap((st: any) => st.topics.flatMap((t: any) => t.subtopics.filter((sb: any) => sb.editing).map((sb: any) => sb.id)));
  assert.deepEqual(flagged, ['eng-editing']);
});
