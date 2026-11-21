import { test } from 'node:test';
import assert from 'node:assert/strict';
import { cleanSave } from './cleansave.ts';
import { fresh, SCHEMA } from './store.ts';

test('a well-formed save comes through unchanged', () => {
  const s = fresh();
  s.progress['math-x'] = { b: { passes: ['d1'], scores: [80], best: 80, cleared: false, mastered: 5, total: 20, hash: 'k3x9a' } };
  s.questions['q1'] = { s: 2, due: 1000, w: 1, a: 'cat' };
  s.questions['q2'] = { s: 1, due: 1000, w: 1, parked: true };
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

test('a __proto__ key in a save cannot reach the prototype', () => {
  const c = cleanSave(JSON.parse('{"questions": {"__proto__": {"s": 1, "due": 0, "w": 3}, "q1": {"s": 1, "due": 5, "w": 1}}}'));
  assert.deepEqual(Object.keys(c.questions), ['q1']);
  assert.equal(Object.getPrototypeOf(c.questions), Object.prototype);
  assert.equal((c.questions as Record<string, unknown>).w, undefined);
});

test('garbage in gives a fresh save, never a throw', () => {
  for (const g of [null, undefined, 5, 'x', [], { questions: [] }]) assert.equal(cleanSave(g).schemaVersion, SCHEMA);
});

test('a tampered tier hash or parked flag is dropped', () => {
  const c = cleanSave({ progress: { 'math-x': { b: { best: 1, hash: '<b>x</b>' } } }, questions: { q1: { s: 1, due: 1, w: 0, parked: 'Yes!' } } }); // a bank-set marker is [a-z0-9]{1,16}
  assert.equal(c.progress['math-x'].b!.hash, undefined);
  assert.equal(c.questions.q1.parked, undefined);
});

test('the Crumbs ledger comes through a server round trip unchanged; a save without one stays without one', () => {
  const s = fresh();
  s.crumbs = {
    bal: 41, earned: 101, spent: 60, test: 0, goalDay: '2026-11-20', week: '2026-11-16', topics: ['math-fractions'], legWeek: '2026-11-16', subjects: ['math'],
    log: [{ ts: 1, n: 12, bal: 101, why: 'quiz', note: 'math-x|b' }, { ts: 2, n: -60, bal: 41, why: 'buy', slug: 'r1', test: true }],
    buys: [{ ts: 2, slug: 'r1', kind: 'card', price: 60, stars: 1, test: true }],
  };
  assert.deepEqual(cleanSave(JSON.parse(JSON.stringify(s))), s);
  assert.equal('crumbs' in cleanSave(JSON.parse(JSON.stringify(fresh()))), false);
});

test('a tampered ledger is made well-formed: no negative balance, unknown reasons dropped, at most 50 entries', () => {
  const log = Array.from({ length: 70 }, (_, k) => ({ ts: k, n: 1, bal: k, why: k === 69 ? '<b>hack</b>' : 'quiz' }));
  const c = cleanSave({ ...fresh(), crumbs: { bal: -5, earned: 'x', log, buys: [{ slug: 3 }], topics: 'no' } }).crumbs!;
  assert.equal(c.bal, 0);
  assert.equal(c.earned, 0);
  assert.equal(c.log.length, 49); // the last 50, minus the one with an unknown reason
  assert.ok(c.log.every((e) => e.why === 'quiz'));
  assert.deepEqual(c.buys, []);
  assert.equal(c.topics, undefined);
});

test('a parked marker naming the bank set survives a round trip', () => {
  const s = fresh();
  s.questions.q1 = { s: 1, due: 5, w: 1, parked: 'k3x9a' };
  assert.deepEqual(cleanSave(JSON.parse(JSON.stringify(s))).questions.q1, { s: 1, due: 5, w: 1, parked: 'k3x9a' });
});

test('one-pool markers (pool, ms) survive the server round trip; anything but true is dropped', () => {
  const s = fresh();
  s.progress.sci = { b: { passes: [], scores: [], best: 0, cleared: true, mastered: 5, total: 24, pool: true, ms: true },
    i: { passes: [], scores: [], best: 0, cleared: false, pool: 'yes', ms: 1 } as any };
  const c = cleanSave(JSON.parse(JSON.stringify(s)));
  assert.equal(c.progress.sci.b?.pool, true);
  assert.equal(c.progress.sci.b?.ms, true);
  assert.equal(c.progress.sci.i?.pool, undefined);
  assert.equal(c.progress.sci.i?.ms, undefined);
});
