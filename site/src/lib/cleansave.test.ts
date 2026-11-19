import { test } from 'node:test';
import assert from 'node:assert/strict';
import { cleanSave } from './cleansave.ts';
import { fresh } from './store.ts';

test('a well-formed save comes through unchanged', () => {
  const s = fresh();
  s.progress['math-x'] = { b: { passes: ['d1'], scores: [80], best: 80, cleared: false, mastered: 5, total: 20 } };
  s.questions['q1'] = { s: 2, due: 1000, w: 1, a: 'cat' };
  s.cards['chip'] = { stars: 2, srcSub: 'math-x', srcTier: 'b', acc: 90, last: 5 };
  s.days['2026-11-19'] = { quizzes: 3, min: 40, correct: 25, total: 30 };
  s.attempts.push({ ts: 1, mode: 'tier', sub: 'math-x', tier: 'b', score: 8, total: 10, ms: 9, tags: ['slip'] });
  assert.deepEqual(cleanSave(JSON.parse(JSON.stringify(s))), s);
});

test('a tampered save cannot carry markup or crash the page', () => {
  const evil = '<img src=x onerror=alert(1)>';
  const c = cleanSave({
    progress: { 'math-x': { b: { best: evil, mastered: evil, cleared: 'yes', passes: [evil, 3] }, z: { best: 1 } } },
    questions: { q1: { s: '2', due: 'x', w: evil, a: 5 }, q2: null, q3: 7 },
    cards: { chip: { stars: evil, acc: 1e9, srcTier: 'q' }, bad: null },
    days: { d: { quizzes: evil, min: -5, correct: 1e9, total: 1 } },
    attempts: [null, 5, { tags: 5, score: evil, total: 10, mode: evil }],
    streak: { best: evil, studyDays: '<b>' },
    settings: { dailyCapMin: evil },
    last: { sub: 'x', tier: evil },
  });
  const tierState = c.progress['math-x'].b!;
  assert.equal(tierState.best, 0); assert.equal(tierState.mastered, 0); assert.equal(tierState.cleared, false);
  assert.equal(c.progress['math-x'].z, undefined);
  assert.deepEqual(c.questions, { q1: { s: 0, due: 0, w: 0 } });
  assert.deepEqual(c.cards.chip, { stars: 1, srcSub: '', srcTier: 'b', acc: 100 });
  assert.equal(c.cards.bad, undefined);
  assert.deepEqual(c.days.d, { quizzes: 0, min: 0, correct: 1, total: 1 }); // accuracy can never pass 100%
  assert.equal(c.attempts.length, 1); assert.deepEqual(c.attempts[0].tags, []); assert.equal(c.attempts[0].mode, 'tier');
  assert.equal(c.streak.best, 0); assert.equal(c.streak.studyDays, 0);
  assert.equal(c.settings.dailyCapMin, fresh().settings.dailyCapMin);
  assert.equal(c.last, null);
  assert.ok(!JSON.stringify(c).includes('<img'), 'no markup survives in any number field');
});

test('garbage in gives a fresh save, never a throw', () => {
  for (const g of [null, undefined, 5, 'x', [], { questions: [] }]) assert.equal(cleanSave(g).schemaVersion, 4);
});
