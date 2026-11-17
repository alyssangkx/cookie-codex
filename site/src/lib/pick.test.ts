import { test } from 'node:test';
import assert from 'node:assert/strict';
import { pickTier, pickReview, wholePassages, type Seen } from './pick.ts';

const ids = Array.from({ length: 30 }, (_, i) => `q${i}`);
const NOW = 1_000_000;

test('tier quiz: no retired questions, at most 3 due retests, rest new', () => {
  const seen: Record<string, Seen> = {};
  for (let i = 0; i < 10; i++) seen[`q${i}`] = { s: 0, due: 0 }; // retired
  for (let i = 10; i < 18; i++) seen[`q${i}`] = { s: 1, due: NOW - i }; // 8 due
  const quiz = pickTier(ids, seen, 10, NOW);
  assert.equal(quiz.length, 10);
  assert.equal(new Set(quiz).size, 10);
  assert.ok(quiz.every((id) => seen[id]?.s !== 0));
  assert.equal(quiz.filter((id) => seen[id]).length, 3);
});

test('tier quiz: always full; not-due retests, then retired questions, fill a shortage', () => {
  const seen: Record<string, Seen> = {};
  ids.forEach((id, i) => (seen[id] = i < 26 ? { s: 0, due: 0 } : { s: 2, due: NOW + 1000 })); // 4 not due
  delete seen.q0; // 1 new
  const quiz = pickTier(ids, seen, 10, NOW);
  assert.equal(quiz.length, 10);
  assert.equal(new Set(quiz).size, 10);
  assert.ok(quiz.includes('q0') && ['q26', 'q27', 'q28', 'q29'].every((id) => quiz.includes(id)));
});

test('tier quiz: due retests from other tiers of the sub-topic count toward the 3', () => {
  const seen: Record<string, Seen> = { x1: { s: 1, due: NOW - 5 }, x2: { s: 1, due: NOW - 4 } };
  const quiz = pickTier(ids, seen, 10, NOW, Math.random, ['x1', 'x2']);
  assert.equal(quiz.length, 10);
  assert.ok(quiz.includes('x1') && quiz.includes('x2'));
});

test('review: only due retests, oldest first; grows with the backlog', () => {
  const seen: Record<string, Seen> = {};
  for (let i = 0; i < 8; i++) seen[`q${i}`] = { s: 1, due: NOW - 100 + i };
  seen.q9 = { s: 1, due: NOW + 5 }; // not due
  assert.deepEqual(pickReview(ids, seen, undefined, NOW), ['q0', 'q1', 'q2', 'q3', 'q4']);
  for (let i = 10; i < 30; i++) seen[`q${i}`] = { s: 1, due: NOW - 1 };
  assert.equal(pickReview(ids, seen, undefined, NOW).length, 14); // 28 due -> 14
});

test('paper: spreads topics, follows the mix, prefers unseen questions', async () => {
  const { pickPaper, MIXES } = await import('./pick.ts');
  const qs = ['a', 'b'].flatMap((t) => (['basic', 'intermediate', 'competent'] as const).flatMap((l) =>
    Array.from({ length: 10 }, (_, k) => ({ id: `${t}-${l}-${k}`, topic: t, level: l }))));
  const seen: Record<string, Seen> = { 'a-basic-0': { s: 0, due: 0 } };
  const p = pickPaper(qs, seen, 20, MIXES.wa.mix, NOW);
  assert.equal(p.length, 20);
  assert.equal(new Set(p).size, 20);
  const lv = (l: string) => p.filter((id) => id.includes(`-${l}-`)).length;
  assert.deepEqual([lv('basic'), lv('intermediate'), lv('competent')], [8, 8, 4]);
  assert.equal(p.filter((id) => id.startsWith('a-')).length, 10);
  assert.ok(!p.includes('a-basic-0')); // retired question only used when nothing else is left
});

test('paper: every topic gets a turn when many topics are chosen', async () => {
  const { pickPaper, MIXES } = await import('./pick.ts');
  const topics = Array.from({ length: 12 }, (_, i) => `t${i}`);
  const qs = topics.flatMap((t) => (['basic', 'intermediate', 'competent'] as const).flatMap((l) =>
    Array.from({ length: 5 }, (_, k) => ({ id: `${t}-${l}-${k}`, topic: t, level: l }))));
  const used = new Set<string>();
  for (let r = 0; r < 20; r++) pickPaper(qs, {}, 10, MIXES.wa.mix, NOW).forEach((id) => used.add(id.split('-')[0]));
  assert.equal(used.size, 12);
});

test('passage tiers: whole passages, questions in order, exactly size', () => {
  // 4 passages x 5 questions; p2 has only 3 shipped questions
  const ids: string[] = []; const meta: Record<string, { group: string; seq: number }> = {};
  for (const p of [1, 2, 3, 4]) for (let n = 1; n <= (p === 2 ? 3 : 5); n++) { const id = `p${p}q${n}`; ids.push(id); meta[id] = { group: `p${p}`, seq: n }; }
  const picked = ['p3q4', 'p1q2', 'p3q1', 'p2q3', 'p4q1']; // priority order from pickTier
  const out = wholePassages(picked, ids, (id) => meta[id], 10);
  assert.deepEqual(out, ['p3q1', 'p3q2', 'p3q3', 'p3q4', 'p3q5', 'p1q1', 'p1q2', 'p1q3', 'p1q4', 'p1q5']);
  const out2 = wholePassages(['p2q1', 'p4q2', 'p1q1'], ids, (id) => meta[id], 10);
  assert.deepEqual(out2, ['p2q1', 'p2q2', 'p2q3', 'p4q1', 'p4q2', 'p4q3', 'p4q4', 'p4q5', 'p1q1', 'p1q2']);
});
