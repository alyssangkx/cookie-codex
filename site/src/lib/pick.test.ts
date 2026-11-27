import { test } from 'node:test';
import assert from 'node:assert/strict';
import { pickTier, pickReview, wholePassages, reviewPassages, type Seen, pickPool, pickPassage } from './pick.ts';

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

test('tier quiz: not-due retests fill a shortage; questions answered right never do (owner, 27 Nov 2026)', () => {
  const seen: Record<string, Seen> = {};
  ids.forEach((id, i) => (seen[id] = i < 26 ? { s: 0, due: 0 } : { s: 2, due: NOW + 1000 })); // 4 not due
  delete seen.q0; // 1 new
  const quiz = pickTier(ids, seen, 10, NOW);
  assert.deepEqual([...quiz].sort(), ['q0', 'q26', 'q27', 'q28', 'q29'], 'the new one and the 4 not-due retests, nothing retired');
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

test('passage tiers: a side retest from another level is a question, never a group name', () => {
  const ids: string[] = []; const meta: Record<string, { group: string; seq: number }> = {};
  for (const p of [1, 2, 3]) for (let n = 1; n <= 5; n++) { const id = `i${p}q${n}`; ids.push(id); meta[id] = { group: `i${p}`, seq: n }; }
  meta['b9q2'] = { group: 'b9', seq: 2 }; // a Basic-level question, due for retest
  const now = 1e12;
  const seen = { b9q2: { s: 1, due: now - 1 } };
  const out = pickTier(ids, seen, 10, now, () => 0.5, ['b9q2'], (id) => meta[id]);
  assert.equal(out.length, 10);
  assert.ok(out.includes('b9q2'));
  assert.ok(out.every((id) => id === 'b9q2' || ids.includes(id)));
});

test('passage tiers: a passage too big for the space left gives way to one that fits', () => {
  const meta: Record<string, { group: string; seq: number }> = {}; const ids: string[] = [];
  const add = (g: string, n: number) => { for (let k = 1; k <= n; k++) { ids.push(`${g}${k}`); meta[`${g}${k}`] = { group: g, seq: k }; } };
  add('a', 4); add('b', 5); add('c', 3); add('d', 2);
  const out = wholePassages(['a1', 'b1', 'c1', 'd1'], ids, (id) => meta[id], 10);
  assert.deepEqual(out, ['a1', 'a2', 'a3', 'a4', 'b1', 'b2', 'b3', 'b4', 'b5', 'c1']); // 4+5 then c cut (no exact fit left)
  const out2 = wholePassages(['a1', 'b1', 'd1', 'c1'], ids, (id) => meta[id], 11);
  assert.deepEqual(out2, ['a1', 'a2', 'a3', 'a4', 'b1', 'b2', 'b3', 'b4', 'b5', 'd1', 'd2']); // c (3) skipped, d (2) fits
});

test('passage tiers: a due retest is never skipped for a passage that fits better', () => {
  const meta: Record<string, { group: string; seq: number }> = {}; const ids: string[] = [];
  const add = (g: string, n: number) => { for (let k = 1; k <= n; k++) { ids.push(`${g}${k}`); meta[`${g}${k}`] = { group: g, seq: k }; } };
  add('a', 5); add('b', 6); add('c', 5);
  const out = wholePassages(['b5', 'a1', 'c1'], ids, (id) => meta[id], 10, new Set(['b5']));
  assert.ok(out.includes('b5'));
  assert.equal(out.length, 10);
  // two due retests from the same other-level passage both stay
  meta['x2'] = { group: 'x', seq: 2 }; meta['x4'] = { group: 'x', seq: 4 };
  const out2 = wholePassages(['x2', 'x4', 'a1', 'c1'], ids, (id) => meta[id], 10, new Set(['x2', 'x4']));
  assert.ok(out2.includes('x2') && out2.includes('x4'));
});

test('passage tiers: three due retests in three passages all fit; a cut keeps new over retired', () => {
  const meta: Record<string, { group: string; seq: number }> = {}; const ids: string[] = [];
  const add = (g: string, n: number) => { for (let k = 1; k <= n; k++) { ids.push(`${g}${k}`); meta[`${g}${k}`] = { group: g, seq: k }; } };
  add('a', 5); add('b', 5); add('c', 5);
  const out = wholePassages(['a3', 'b2', 'c4'], ids, (id) => meta[id], 10, new Set(['a3', 'b2', 'c4']));
  assert.equal(out.length, 10);
  for (const id of ['a3', 'b2', 'c4']) assert.ok(out.includes(id));
  add('d', 6);
  const cutOut = wholePassages(['d5', 'd6'], ids, (id) => meta[id], 4, new Set(['d5'])); // d6 picked as new
  assert.deepEqual(cutOut, ['d3', 'd4', 'd5', 'd6']); // a consecutive run holding the due d5 and the new d6
});

test('Daily Review groups a passage\'s due blanks in passage order and adds nothing', () => {
  const P: Record<string, { group: string; seq: number }> = {
    c1: { group: 'cz', seq: 1 }, c2: { group: 'cz', seq: 2 }, c4: { group: 'cz', seq: 4 },
  };
  const passage = (id: string) => P[id];
  // due in this order (oldest first): c4, m1, c1, c2; c3 retired and c5 not due are NOT added
  assert.deepEqual(reviewPassages(['c4', 'm1', 'c1', 'c2'], passage), ['c1', 'c2', 'c4', 'm1']);
  assert.deepEqual(reviewPassages(['m1', 'm2'], passage), ['m1', 'm2']);
});

test('pickPool: due retests first, then new questions easier-first (no shuffle), then the rest', () => {
  const ids = Array.from({ length: 30 }, (_, i) => `pp-${String(i).padStart(10, '0')}`); // already easier-first
  const now = 1_000_000_000_000;
  const seen = { [ids[0]]: { s: 0, due: 0 }, [ids[1]]: { s: 0, due: 0 }, [ids[25]]: { s: 1, due: now - 1 }, [ids[26]]: { s: 1, due: now + 1e9 } };
  const q = pickPool(ids, seen, 10, now);
  assert.equal(q.length, 10);
  assert.equal(q[0], ids[25]);                       // the due retest leads
  assert.deepEqual(q.slice(1), ids.slice(2, 11));    // then the easiest unseen ones, in order
  assert.ok(!q.includes(ids[0]) && !q.includes(ids[26]));
});

test('pickPool with passage sets: whole sets, each in paper order (migration 010)', () => {
  // three visual-text sets of 4, easier-first order interleaves them
  const sets: Record<string, { group: string; seq: number }> = {};
  const ids: string[] = [];
  for (const g of ['a', 'b', 'c']) for (let k = 1; k <= 4; k++) { const id = `${g}${k}`; sets[id] = { group: g, seq: 20 + k }; }
  for (let k = 1; k <= 4; k++) for (const g of ['c', 'a', 'b']) ids.push(`${g}${k}`);
  const q = pickPool(ids, {}, 8, Date.now(), (id) => sets[id]);
  assert.equal(q.length, 8);
  const groups = [...new Set(q.map((id) => sets[id].group))];
  assert.equal(groups.length, 2); // two whole sets of 4, not pieces of three
  for (const g of groups) {
    const mine = q.filter((id) => sets[id].group === g);
    assert.equal(mine.length, 4);
    assert.deepEqual(mine.map((id) => sets[id].seq), [21, 22, 23, 24]);
  }
});

test('a merged tier asks every new past-paper question before any generated one (owner, 24 Nov 2026)', () => {
  const pp = Array.from({ length: 6 }, (_, i) => `pp-00000000${i}a`), gen = Array.from({ length: 20 }, (_, i) => `g${i}`);
  for (let r = 0; r < 20; r++) {
    const out = pickTier([...gen, ...pp], {}, 10, NOW, Math.random);
    assert.equal(out.length, 10);
    assert.deepEqual(new Set(out.filter((id) => id.startsWith('pp-'))), new Set(pp), 'all 6 past-paper questions are in');
  }
  const seen: Record<string, Seen> = Object.fromEntries(pp.slice(0, 4).map((id) => [id, { s: 0, due: 0 } as Seen]));
  const out = pickTier([...gen, ...pp], seen, 10, NOW, Math.random);
  assert.ok(pp.slice(4).every((id) => out.includes(id)), 'the two unasked past-paper questions come before generated ones');
});

test('a passage longer than the quiz starts at its first blank not answered yet (owner, 24 Nov 2026)', () => {
  const set = Array.from({ length: 15 }, (_, i) => `pp-c${String(i).padStart(9, '0')}`); // blanks 51-65
  const passage = (id: string) => { const k = set.indexOf(id); return k < 0 ? undefined : { group: 'g', seq: 51 + k }; };
  const easierFirst = [...set.slice(5), ...set.slice(0, 5)]; // the ranking puts blanks 56-65 first
  const out = pickPool(easierFirst, {}, 10, NOW, passage);
  assert.deepEqual(out.map((id) => passage(id)!.seq), [51, 52, 53, 54, 55, 56, 57, 58, 59, 60], 'a new child starts at blank 51');
  const seen: Record<string, Seen> = Object.fromEntries(set.slice(0, 10).map((id) => [id, { s: 0, due: 0 } as Seen]));
  const next = pickPool(easierFirst, seen, 10, NOW, passage);
  assert.deepEqual(next.map((id) => passage(id)!.seq), [61, 62, 63, 64, 65], 'the next quiz reads on: only the blanks not done yet');
});

test('pickPassage: a cloze quiz is one whole passage, every blank in order (owner: 15 blanks, 15 questions)', () => {
  const A = Array.from({ length: 15 }, (_, i) => `a${i}`), B = Array.from({ length: 5 }, (_, i) => `b${i}`);
  const passage = (id: string) => ({ group: id[0], seq: Number(id.slice(1)) + (id[0] === 'a' ? 51 : 16) });
  const ids = [...B.slice(2), ...A.slice(7), ...A.slice(0, 7), ...B.slice(0, 2)]; // an easier-first order mixing both
  assert.deepEqual(pickPassage(ids, {}, NOW, passage), B, 'the passage of the first new question, whole and in order');
  const doneB: Record<string, Seen> = Object.fromEntries(B.map((id) => [id, { s: 0, due: 0 } as Seen]));
  assert.deepEqual(pickPassage(ids, doneB, NOW, passage), A, 'then the next passage with blanks never answered: all 15');
  const dueA = { ...doneB, a3: { s: 1, due: NOW - 1 } as Seen };
  assert.deepEqual(pickPassage(ids, dueA, NOW, passage), [], 'a passage with an answered blank is not asked again (27 Nov 2026)');
  assert.deepEqual(pickPassage([], {}, NOW, passage), []);
  assert.deepEqual(pickPassage(['lone', ...B], {}, NOW, (id) => (id === 'lone' ? undefined : passage(id))), B, 'an ungrouped question is skipped');
});

// owner, 27 Nov 2026: a question answered right is never asked again; only wrong answers come back. A wrong answer in a
// passage set is held (stored done with h: 1), so its passage is never asked again either.
test('pickTier never refills with questions answered right: the quiz gets shorter', () => {
  const ids = Array.from({ length: 12 }, (_, i) => `q${i}`);
  const seen: Record<string, Seen> = {};
  for (let i = 0; i < 9; i++) seen[`q${i}`] = { s: 0, due: 0 };
  const q = pickTier(ids, seen, 10, Date.now(), () => 0.5);
  assert.deepEqual([...q].sort(), ['q10', 'q11', 'q9']);
  assert.deepEqual(pickTier(ids, Object.fromEntries(ids.map((id) => [id, { s: 0, due: 0 }])), 10), []);
});

test('pickTier with passages: answered blanks are not asked again; the passage carries on from its first new blank', () => {
  const ids = ['a1', 'a2', 'a3', 'a4', 'b1', 'b2'];
  const passage = (id: string) => ({ group: id[0], seq: Number(id[1]) });
  const seen: Record<string, Seen> = { a1: { s: 0, due: 0 }, a2: { s: 0, due: 0 } };
  const q = pickTier(ids, seen, 10, Date.now(), () => 0.5, [], passage);
  assert.ok(!q.includes('a1') && !q.includes('a2'), String(q));
  assert.deepEqual([...q].sort(), ['a3', 'a4', 'b1', 'b2']);
});

test('pickPassage: never a passage with a blank already answered; [] when all are done', () => {
  const ids = ['a1', 'a2', 'b1', 'b2'];
  const passage = (id: string) => ({ group: id[0], seq: Number(id[1]) });
  assert.deepEqual(pickPassage(ids, { a2: { s: 0, due: 0 } }, Date.now(), passage), ['b1', 'b2']);
  assert.deepEqual(pickPassage(ids, { a2: { s: 1, due: 0 }, b1: { s: 0, due: 0 } }, Date.now(), passage), []);
});
