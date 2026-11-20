import { test } from 'node:test';
import assert from 'node:assert/strict';
import { topicPower, schoolPower, suggestions, dueCount, type SubInfo } from './suggest.ts';
import { fresh, dayKey, type SaveV1, type Tier } from './store.ts';

const ALL = { b: true, i: true, c: true };
const mk = (id: string, topic: string, playable: Record<Tier, boolean> = ALL): SubInfo =>
  ({ id, topic, topicName: topic.toUpperCase(), name: id, slug: id.replace('math-', ''), playable, count: { b: 20, i: 20, c: 20 } });
const NOW = new Date(2026, 5, 15, 12).getTime();
const DAY = 86_400_000;
const TODAY = dayKey(NOW), PAST = dayKey(NOW - 3 * DAY);

const clear = (s: SaveV1, sub: string, t: Tier) => {
  (s.progress[sub] ??= {})[t] = { passes: [PAST, PAST + 'x'], scores: [90, 90], best: 90, cleared: true };
};
const onePass = (s: SaveV1, sub: string, t: Tier, day = PAST) => {
  (s.progress[sub] ??= {})[t] = { passes: [day], scores: [80], best: 80, cleared: false, mastered: 5, total: 20 };
};
const tierAttempt = (s: SaveV1, sub: string, tier: Tier, score: number, ageDays = 1, total = 10) =>
  s.attempts.push({ ts: NOW - ageDays * DAY, mode: 'tier', sub, tier, score, total, ms: 1000, tags: [] });
const run = (s: SaveV1, subs: SubInfo[], due = 0) => suggestions(s, subs, { now: NOW, dueCount: due });
const real = () => { const s = fresh(); s.createdAt = NOW; return s; };

test('topicPower weights tiers 1/2/3', () => {
  const s = real(); const subs = [mk('math-a', 't'), mk('math-b', 't')];
  assert.equal(topicPower(s, subs), 0);
  clear(s, 'math-a', 'b');
  assert.equal(topicPower(s, subs), Math.round(100 / 12));
  clear(s, 'math-a', 'i'); clear(s, 'math-a', 'c');
  assert.equal(topicPower(s, subs), 50);
});

test('topicPower ignores unplayable tiers on both sides', () => {
  const s = real(); const subs = [mk('math-a', 't', { b: true, i: true, c: false })];
  clear(s, 'math-a', 'b');
  assert.equal(topicPower(s, subs), 33); // 1 of 3
  clear(s, 'math-a', 'c'); // cleared but unplayable: not counted
  assert.equal(topicPower(s, subs), 33);
  assert.equal(topicPower(s, [mk('math-x', 't', { b: false, i: false, c: false })]), 0);
});

test('schoolPower is the rounded mean over topics with playable tiers', () => {
  const s = real();
  const subs = [mk('math-a', 't1'), mk('math-b', 't2'), mk('math-c', 't3', { b: false, i: false, c: false })];
  clear(s, 'math-a', 'b'); clear(s, 'math-a', 'i'); clear(s, 'math-a', 'c');
  assert.equal(schoolPower(s, subs), 50); // (100 + 0) / 2; t3 excluded
  assert.equal(schoolPower(s, [subs[2]]), 0);
});

test('next up: first open uncleared playable tier in syllabus order', () => {
  const s = real(); const subs = [mk('math-a', 't'), mk('math-b', 't')];
  assert.deepEqual(run(s, subs).map((x) => [x.kind, x.sub, x.tier]), [['next', 'math-a', 'b']]);
  clear(s, 'math-a', 'b');
  assert.equal(run(s, subs)[0].tier, 'i');
  const skip = [mk('math-a', 't', { b: false, i: false, c: false }), mk('math-b', 't')];
  assert.equal(run(real(), skip)[0].sub, 'math-b');
  assert.match(run(s, subs)[0].href, /^\/quiz\/\?sub=math-a&tier=i$/);
});

test('review first when something is due, with count', () => {
  const s = real(); const subs = [mk('math-a', 't')];
  const r = run(s, subs, 6);
  assert.equal(r[0].kind, 'review');
  assert.equal(r[0].href, '/quiz/?mode=review');
  assert.match(r[0].reason, /6 questions are ready to retest/);
  assert.equal(r[1].kind, 'next');
  assert.match(run(s, subs, 1)[0].reason, /1 question is ready/);
});

test('dueCount uses isDue and the optional question map', () => {
  const s = real();
  s.questions.q1 = { s: 1, due: NOW - 1, w: 1 };
  s.questions.q2 = { s: 2, due: NOW + DAY, w: 1 };
  s.questions.q3 = { s: 0, due: 0, w: 1 };
  s.questions.q4 = { s: 3, due: NOW - 5, w: 1 };
  assert.equal(dueCount(s, NOW), 2);
  assert.equal(dueCount(s, NOW, { q1: 'math-a' }), 1);
});

test('keep going: a part-mastered tier is suggested with N of M mastered', () => {
  const subs = [mk('math-a', 't'), mk('math-b', 't')];
  const s = real(); clear(s, 'math-a', 'b'); onePass(s, 'math-b', 'b');
  const r = run(s, subs);
  assert.equal(r[0].kind, 'one-more');
  assert.equal(r[0].sub, 'math-b');
  assert.match(r[0].reason, /5 of 20 questions mastered/);
  // a count stored against a bank of another size is stale and is not suggested
  const t = run(s, [mk('math-a', 't'), { ...mk('math-b', 't'), count: { b: 25, i: 20, c: 20 } }]);
  assert.notEqual(t[0]?.kind, 'one-more');
  const u = real(); u.progress['math-a'] = { b: { passes: [], scores: [], best: 0, cleared: false } };
  assert.ok(!run(u, subs).some((x) => x.kind === 'one-more')); // nothing mastered yet
});

test('weak spot: lowest accuracy in 14 days, at least 10 answered, states accuracy', () => {
  const subs = [mk('math-a', 't'), mk('math-b', 't'), mk('math-c', 't')];
  const s = real();
  clear(s, 'math-a', 'b'); clear(s, 'math-b', 'b'); clear(s, 'math-c', 'b');
  tierAttempt(s, 'math-a', 'i', 6); tierAttempt(s, 'math-a', 'i', 5); // 55%
  tierAttempt(s, 'math-b', 'i', 3, 1, 5); // 60% but 5 answered: ignored
  tierAttempt(s, 'math-c', 'i', 2, 20); // too old
  tierAttempt(s, 'math-c', 'i', 9); // 90%
  const w = run(s, subs).find((x) => x.kind === 'weak')!;
  assert.equal(w.sub, 'math-a'); assert.equal(w.tier, 'i');
  assert.match(w.reason, /55%/);
  s.attempts.push({ ts: NOW - DAY, mode: 'tier', sub: 'math-b', tier: 'i', score: 0, total: 10, ms: 0, tags: [], open: true });
  assert.equal(run(s, subs).find((x) => x.kind === 'weak')!.sub, 'math-a'); // open tries are not answers
});

test('priority order review > one-more > weak > next, max 3, no duplicates', () => {
  const subs = [mk('math-a', 't'), mk('math-b', 't'), mk('math-c', 't')];
  const s = real();
  clear(s, 'math-a', 'b'); onePass(s, 'math-a', 'i');
  tierAttempt(s, 'math-b', 'b', 5); tierAttempt(s, 'math-b', 'b', 5);
  const r = run(s, subs, 2);
  assert.deepEqual(r.map((x) => x.kind), ['review', 'one-more', 'weak']);
  const keys = r.filter((x) => x.sub).map((x) => `${x.sub}|${x.tier}`);
  assert.equal(new Set(keys).size, keys.length);
});

test('same tier is never suggested twice', () => {
  const subs = [mk('math-a', 't'), mk('math-b', 't')];
  const s = real(); clear(s, 'math-a', 'b'); onePass(s, 'math-a', 'i');
  tierAttempt(s, 'math-a', 'i', 5); tierAttempt(s, 'math-a', 'i', 5); // would be weak too
  const r = run(s, subs);
  const keys = r.map((x) => `${x.sub}|${x.tier}`);
  assert.equal(new Set(keys).size, keys.length);
  assert.deepEqual(r.map((x) => x.kind), ['one-more', 'next']);
  assert.deepEqual([r[1].sub, r[1].tier], ['math-b', 'b']); // a-i is taken, a-c is locked
});

test('blocked: locked tiers and unplayable tiers are never suggested', () => {
  const s = real();
  onePass(s, 'math-a', 'c'); // a pass on a tier whose predecessor is not cleared: locked
  tierAttempt(s, 'math-a', 'c', 1); tierAttempt(s, 'math-a', 'c', 1);
  // Basic playable but not cleared: Intermediate and Competent are locked, so only Basic is suggested
  assert.deepEqual(run(s, [mk('math-a', 't', { b: true, i: true, c: true })]).map((x) => x.tier), ['b']);
  // Basic unplayable: Intermediate opens instead of being locked forever; Competent stays locked
  assert.deepEqual(run(s, [mk('math-a', 't', { b: false, i: true, c: true })]).map((x) => x.tier), ['i']);
  const open = [mk('math-b', 't', { b: false, i: false, c: false })];
  assert.deepEqual(run(real(), open), []);
});

test('blocked: 3 tries used today drops that tier', () => {
  const subs = [mk('math-a', 't'), mk('math-b', 't')];
  const s = real();
  for (let i = 0; i < 3; i++) s.attempts.push({ ts: Date.now(), mode: 'tier', sub: 'math-a', tier: 'b', score: 4, total: 10, ms: 1, tags: [] });
  const r = suggestions(s, subs, { now: Date.now(), dueCount: 0 });
  assert.deepEqual(r.map((x) => [x.sub, x.tier]), [['math-b', 'b']]);
});

test('cap reached: only a done card linking to the collection', () => {
  const s = fresh();
  s.days[dayKey()] = { quizzes: 3, min: s.settings.dailyCapMin, correct: 0, total: 0 };
  const r = suggestions(s, [mk('math-a', 't')], { now: Date.now(), dueCount: 5 });
  assert.equal(r.length, 1);
  assert.equal(r[0].kind, 'done');
  assert.equal(r[0].href, '/collection/');
});
