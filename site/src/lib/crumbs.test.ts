import { test } from 'node:test';
import assert from 'node:assert/strict';
import { alBand, quizCrumbs, earn, LEDGER_MAX, priceOf, buyCard, buyStar, rewardPreview, achievementPreview, competencyGroups, LEGENDARY_MIN_QUESTIONS, type Economy } from './crumbs.ts';
import { fresh, answer, finishQuiz, beginQuiz, purchase, load, save, resetUnlimitedCache, syncParkedStored, inReview, type SaveV1 } from './store.ts';

const t0 = new Date(2026, 10, 16, 10).getTime(); // Mon 16 Nov 2026, 10:00 local

test('AL bands follow the PSLE cut-offs (90, 85, 80, 75, 65, 45, 20)', () => {
  const band = (pct: number) => alBand(pct, 100);
  assert.deepEqual([100, 90, 89, 85, 84, 80, 79, 75, 74, 65, 64, 45, 44, 20, 19, 0].map(band),
    [1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 6, 7, 7, 8, 8]);
  assert.equal(alBand(17, 20), 2); // 85% exactly
  assert.equal(alBand(0, 0), 8); // an empty quiz is the lowest band, never a crash
});

test('a finished quiz earns Crumbs by band, +4 for perfect, never less than 1; papers by length (x1 per 10 questions, at most x3)', () => {
  const ten = [10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0].map((n) => quizCrumbs(n, 10, 'tier'));
  assert.deepEqual(ten, [12, 8, 6, 4, 3, 3, 2, 2, 2, 1, 1]);
  assert.equal(quizCrumbs(17, 20, 'tier'), 7); // 85% = AL2
  assert.equal(quizCrumbs(5, 5, 'review'), 12); // Daily Review earns like a tier quiz
  assert.equal(quizCrumbs(9, 10, 'paper'), 8); // a 10-question paper pays like a 10-question quiz
  assert.equal(quizCrumbs(18, 20, 'paper'), 16); // 90%: 8 x 2
  assert.equal(quizCrumbs(20, 20, 'paper'), 24); // perfect: (8 + 4) x 2
  assert.equal(quizCrumbs(0, 20, 'paper'), 2);
  assert.equal(quizCrumbs(27, 30, 'paper'), 24); // 8 x 3
  assert.equal(quizCrumbs(36, 40, 'paper'), 24); // never more than x3
  assert.equal(quizCrumbs(5, 5, 'paper'), 6); // (8 + 4) x 0.5
  assert.equal(quizCrumbs(0, 5, 'paper'), 1); // still at least 1
});

test('the ledger keeps a running balance and only the last 50 entries; coins never drop when entries are trimmed', () => {
  const s = fresh();
  assert.equal(s.crumbs, undefined); // optional field: an old save simply has none
  for (let k = 1; k <= 60; k++) earn(s, 2, 'quiz', t0 + k);
  assert.equal(LEDGER_MAX, 50);
  assert.equal(s.crumbs!.log.length, 50);
  assert.equal(s.crumbs!.bal, 120);
  assert.equal(s.crumbs!.earned, 120);
  assert.deepEqual(s.crumbs!.log.at(-1), { ts: t0 + 60, n: 2, bal: 120, why: 'quiz' });
  assert.equal(s.crumbs!.log[0].ts, t0 + 11); // the oldest 10 were dropped
});

test('coins earned on the unlimited test account are flagged and counted apart', () => {
  const s = fresh();
  earn(s, 5, 'quiz', t0);
  earn(s, 8, 'quiz', t0 + 1, { test: true });
  assert.equal(s.crumbs!.bal, 13);
  assert.equal(s.crumbs!.test, 8);
  assert.equal(s.crumbs!.log[1].test, true);
  assert.equal(s.crumbs!.log[0].test, undefined);
});

// a tiny fixed card set: order lists are the replacement/shop order per rarity
const RARITY: Record<string, string> = { c1: 'common', c2: 'common', r1: 'rare', e1: 'epic', sp1: 'special', se1: 'super-epic', se2: 'super-epic', l1: 'legendary', l2: 'legendary', a1: 'ancient' };
const eco: Economy = {
  order: { common: ['c1', 'c2'], rare: ['r1'], epic: ['e1'], special: ['sp1'], 'super-epic': ['se1', 'se2'], legendary: ['l1', 'l2'] },
  rarityOf: (slug) => RARITY[slug],
};
const rich = (n = 1000) => { const s = fresh(); earn(s, n, 'quiz', t0); return s; };

test('fixed prices: Common 30, Rare 60, Epic and Special 120; the rarest classes are not for sale', () => {
  assert.deepEqual(['c1', 'r1', 'e1', 'sp1'].map((x) => priceOf(eco, x)), [30, 60, 120, 120]);
  for (const x of ['se1', 'l1', 'a1', 'nope']) assert.equal(priceOf(eco, x), undefined);
});

test('buying a chosen card spends its price once; a second buy of the same card is refused (idempotent)', () => {
  const s = rich(100);
  assert.deepEqual(buyCard(s, 'r1', eco, t0 + 1), { ok: true, price: 60 });
  assert.equal(s.crumbs!.bal, 40);
  assert.equal(s.cards.r1.stars, 1);
  assert.equal(s.cards.r1.srcSub, 'shop');
  assert.deepEqual(s.crumbs!.buys, [{ ts: t0 + 1, slug: 'r1', kind: 'card', price: 60, stars: 1 }]);
  assert.deepEqual(s.crumbs!.log.at(-1), { ts: t0 + 1, n: -60, bal: 40, why: 'buy', slug: 'r1' });
  assert.deepEqual(buyCard(s, 'r1', eco, t0 + 2), { ok: false, reason: 'owned' });
  assert.equal(s.crumbs!.bal, 40);
  assert.equal(s.crumbs!.spent, 60);
});

test('a card is refused when the balance is short or the card is not for sale', () => {
  const s = rich(100);
  assert.deepEqual(buyCard(s, 'e1', eco, t0), { ok: false, reason: 'poor' });
  assert.deepEqual(buyCard(s, 'se1', eco, t0), { ok: false, reason: 'not-for-sale' });
  assert.deepEqual(buyCard(fresh(), 'c1', eco, t0), { ok: false, reason: 'poor' }); // no ledger yet = 0 Crumbs
  assert.equal(s.crumbs!.bal, 100);
  assert.equal(s.cards.e1, undefined);
});

test('stars are for sale only once every card of that rarity is owned, at the rarity price, up to 5 stars', () => {
  const s = rich(1000);
  buyCard(s, 'c1', eco, t0);
  assert.deepEqual(buyStar(s, 'c1', 1, eco, t0), { ok: false, reason: 'cards-left' }); // c2 can still be bought
  buyCard(s, 'c2', eco, t0);
  assert.deepEqual(buyStar(s, 'c1', 1, eco, t0 + 5), { ok: true, price: 30 });
  assert.equal(s.cards.c1.stars, 2);
  assert.deepEqual(s.crumbs!.buys.at(-1), { ts: t0 + 5, slug: 'c1', kind: 'star', price: 30, stars: 2 });
  // the same click again (the page still thinks the card has 1 star) is refused, not charged twice
  assert.deepEqual(buyStar(s, 'c1', 1, eco, t0 + 6), { ok: false, reason: 'stale' });
  for (const n of [2, 3, 4]) assert.equal(buyStar(s, 'c1', n, eco, t0).ok, true);
  assert.deepEqual(buyStar(s, 'c1', 5, eco, t0), { ok: false, reason: 'max' });
  assert.deepEqual(buyStar(s, 'r1', 1, eco, t0), { ok: false, reason: 'not-owned' });
  assert.equal(s.crumbs!.bal, 1000 - 30 - 30 - 4 * 30);
});

// clear tier x|b (3 questions, all answered right) with the slot card `slot`
const clearTier = (s: SaveV1, slot: string, sub = 'x', score = 7, now = t0) => {
  const ids = [`${sub}1`, `${sub}2`, `${sub}3`];
  for (const id of ids) answer(s, id, true, now);
  return finishQuiz(s, { mode: 'tier', sub, tier: 'b', score, total: 10, ms: 60_000, tags: [] },
    () => ({ slug: slot, dup: false }), now, { [`${sub}|b`]: ids }, undefined, { eco });
};

test('a cleared tier whose card is owned gives the next unowned card of the same rarity, as previewed', () => {
  const s = fresh();
  s.cards.c1 = { stars: 1, srcSub: 'old', srcTier: 'b', acc: 90 };
  assert.deepEqual(rewardPreview(s, 'c1', eco), { kind: 'card', slug: 'c2', replaces: 'c1' });
  const res = clearTier(s, 'c1');
  assert.deepEqual(res.reward, { slug: 'c2', dup: false, stars: 1, replaces: 'c1' });
  assert.equal(s.cards.c2.srcSub, 'x');
  assert.equal(s.cards.c1.stars, 1); // the owned card is untouched
  assert.deepEqual(rewardPreview(fresh(), 'c1', eco), { kind: 'card', slug: 'c1' }); // not owned: the slot card itself
});

test('when every card of the rarity is owned, a clear gives a star on the slot card plus half its price in Crumbs', () => {
  const s = fresh();
  for (const x of ['c1', 'c2']) s.cards[x] = { stars: 1, srcSub: 'old', srcTier: 'b', acc: 90 };
  assert.deepEqual(rewardPreview(s, 'c1', eco), { kind: 'star', slug: 'c1', crumbs: 15 });
  const res = clearTier(s, 'c1', 'x', 7);
  assert.deepEqual(res.reward, { slug: 'c1', dup: true, stars: 2, crumbs: 15 });
  assert.equal(s.crumbs!.log.find((e) => e.why === 'bonus')!.n, 15);
  assert.equal(res.crumbs, 4 + 15); // 7/10 = AL5 (4) + the bonus
  // a not-for-sale rarity with nothing left: the bonus is 60
  for (const x of ['se1', 'se2']) s.cards[x] = { stars: 1, srcSub: 'old', srcTier: 'c', acc: 90 };
  assert.deepEqual(rewardPreview(s, 'se1', eco), { kind: 'star', slug: 'se1', crumbs: 60 });
});

const quiz = (score = 10) => ({ mode: 'tier' as const, sub: 'y', tier: 'b' as const, score, total: 10, ms: 60_000, tags: [] });
const DAY = 86_400_000;

test('answer() reports a retest step passed, and each one earns 1 Crumb at the finish', () => {
  const s = fresh();
  answer(s, 'q', false, t0);
  assert.equal(answer(s, 'q', true, t0 + DAY), true); // due retest passed
  assert.equal(answer(s, 'q', true, t0 + DAY + 1), false); // not due again yet: no progress, no Crumb
  assert.equal(answer(s, 'n', true, t0), false); // a new question is not a retest
  const res = finishQuiz(s, quiz(9), () => undefined, t0 + DAY, {}, undefined, { eco, retests: 1, test: false });
  assert.equal(res.crumbs, 8 + 1);
  assert.deepEqual(s.crumbs!.log.map((e) => [e.why, e.n]), [['quiz', 8], ['retest', 1]]);
});

test('the daily goal pays 3 once a day; the 4th goal day of a week pays a 10 Crumb streak week once', () => {
  const s = fresh(); // daily goal: 2 quizzes
  const fin = (now: number) => finishQuiz(s, quiz(0), () => undefined, now, {}, undefined, { eco, test: false });
  const goalPaid = () => s.crumbs!.log.filter((e) => e.why === 'goal').length;
  fin(t0); assert.equal(goalPaid(), 0);
  assert.equal(fin(t0 + 1).crumbs, 1 + 3); // 2nd quiz: the goal is met
  fin(t0 + 2); assert.equal(goalPaid(), 1); // a 3rd quiz the same day pays no second goal bonus
  for (const d of [1, 2]) { fin(t0 + d * DAY); fin(t0 + d * DAY + 1); }
  assert.equal(s.crumbs!.log.filter((e) => e.why === 'week').length, 0); // 3 goal days so far
  fin(t0 + 3 * DAY);
  const r = fin(t0 + 3 * DAY + 1); // Thursday: the 4th goal day this week
  assert.equal(r.crumbs, 1 + 3 + 10);
  for (const d of [4, 5]) { fin(t0 + d * DAY); fin(t0 + d * DAY + 1); }
  assert.equal(s.crumbs!.log.filter((e) => e.why === 'week').length, 1); // once per week
});

test('the unlimited test account earns, but every entry is flagged', () => {
  const s = fresh();
  finishQuiz(s, quiz(10), () => undefined, t0, {}, undefined, { eco, test: true });
  assert.equal(s.crumbs!.bal, 12);
  assert.equal(s.crumbs!.test, 12);
  assert.ok(s.crumbs!.log.every((e) => e.test));
});

test('a quiz that is started but never finished (abandoned, put away) earns nothing', () => {
  const s = fresh();
  assert.equal(beginQuiz(s, 'paper', { total: 20 }, t0), null);
  assert.equal(s.crumbs, undefined);
});

test('Super Epic: once per topic, when every sub-topic in it has its Competent tier cleared', () => {
  const s = fresh();
  const topicEco: Economy = { ...eco, topics: { t1: ['a', 'b'], t2: ['c'] } };
  const done = (sub: string) => { (s.progress[sub] ??= {}).c = { passes: [], scores: [], best: 90, cleared: true }; };
  const fin = () => finishQuiz(s, quiz(5), () => undefined, t0, {}, undefined, { eco: topicEco, test: false });
  done('a');
  assert.deepEqual(fin().achieved, []); // b is not cleared yet
  assert.deepEqual(achievementPreview(s, 'super-epic', topicEco), { kind: 'card', slug: 'se1' });
  done('b');
  const r = fin();
  assert.deepEqual(r.achieved, [{ kind: 'super-epic', topic: 't1', reward: { slug: 'se1', dup: false, stars: 1 } }]);
  assert.equal(s.cards.se1.srcSub, 'topic:t1');
  assert.deepEqual(fin().achieved, []); // never twice for one topic
  done('c');
  assert.equal(fin().achieved[0].reward.slug, 'se2'); // the next one in the fixed order
});

test('Legendary from a paper: 20+ questions, 3+ topics, AL1-AL2, at most one per calendar week', () => {
  const s = fresh();
  const paper = (score: number, now: number, topics = ['m1', 'm2', 'm3'], total = 20) => finishQuiz(s, { mode: 'paper', topics, score, total, ms: 60_000, tags: [] },
    () => undefined, now, {}, undefined, { eco, test: false });
  assert.equal(LEGENDARY_MIN_QUESTIONS, 20);
  assert.deepEqual(paper(16, t0).achieved, []); // 80%: AL3
  assert.deepEqual(paper(10, t0, ['m1', 'm2', 'm3'], 10).achieved, []); // perfect, but a short paper
  assert.deepEqual(paper(20, t0, ['m1', 'm2']).achieved, []); // only 2 topics
  assert.deepEqual(paper(20, t0, ['m1', 'm1', 'm2']).achieved, []); // topics are counted once each
  assert.deepEqual(paper(17, t0).achieved, [{ kind: 'legendary', reward: { slug: 'l1', dup: false, stars: 1 } }]); // Monday
  assert.equal(s.cards.l1.srcSub, 'paper');
  const again = paper(20, t0 + 3 * DAY); // Thursday, same week: the paper's Crumbs only
  assert.deepEqual(again.achieved, []);
  assert.equal(again.crumbs, 24);
  assert.equal(paper(20, t0 + 7 * DAY).achieved![0].reward.slug, 'l2'); // next Monday
  assert.deepEqual(achievementPreview(s, 'legendary', eco), { kind: 'star', slug: 'l1', crumbs: 60 });
  const r = paper(18, t0 + 14 * DAY);
  assert.deepEqual(r.achieved, [{ kind: 'legendary', reward: { slug: 'l1', dup: true, stars: 2, crumbs: 60 } }]);
  assert.equal(r.crumbs, 16 + 60);
});

test('Legendary from a subject: once, when every competency topic of the subject has its Competent tiers cleared', () => {
  const s = fresh();
  const subjEco: Economy = { ...eco, subjects: { math: ['a', 'b', 'c'] } };
  const done = (sub: string) => { (s.progress[sub] ??= {}).c = { passes: [], scores: [], best: 90, cleared: true }; };
  const fin = (now = t0) => finishQuiz(s, quiz(5), () => undefined, now, {}, undefined, { eco: subjEco, test: false });
  done('a'); done('b');
  assert.deepEqual(fin().achieved, []);
  done('c');
  assert.deepEqual(fin().achieved, [{ kind: 'legendary', subject: 'math', reward: { slug: 'l1', dup: false, stars: 1 } }]);
  assert.equal(s.cards.l1.srcSub, 'subject:math');
  assert.deepEqual(fin(t0 + 1).achieved, []); // once per subject
  // the subject route does not use up the week's paper Legendary
  const p = finishQuiz(s, { mode: 'paper', topics: ['x', 'y', 'z'], score: 20, total: 20, ms: 1, tags: [] }, () => undefined, t0 + 2, {}, undefined, { eco: subjEco, test: false });
  assert.equal(p.achieved![0].reward.slug, 'l2');
});

test('competency groups: topics (Math, Science) or booklets (English, Chinese) with 2+ playable Competent tiers', () => {
  const sub = (id: string, school: string, topic: string, strand: string, c = true) => ({ id, school, topic, strand, playableC: c });
  const g = competencyGroups([
    sub('m1', 'math', 'fr', 'num'), sub('m2', 'math', 'fr', 'num'), sub('m3', 'math', 'fr', 'num', false),
    sub('m4', 'math', 'ratio', 'num'), // one playable sub-topic: not a group
    sub('e1', 'english', 'e-sec1', 'p2a'), sub('e2', 'english', 'e-sec2', 'p2a'), sub('e3', 'english', 'e-sec3', 'p2b'),
    sub('c1', 'chinese', 'c-t1', 'zi'), sub('c2', 'chinese', 'c-t2', 'zi', false),
  ]);
  assert.deepEqual(g.topics, { fr: ['m1', 'm2'], p2a: ['e1', 'e2'] });
  assert.deepEqual(g.subjects, {}); // a subject needs 2+ groups (Math and English have one each here)
  const two = competencyGroups([sub('m1', 'math', 'a', 's'), sub('m2', 'math', 'a', 's'), sub('m3', 'math', 'b', 's'), sub('m4', 'math', 'b', 's')]);
  assert.deepEqual(two.subjects, { math: ['m1', 'm2', 'm3', 'm4'] });
});

test('parking re-reads the stored save after the banks load, so a purchase in another tab is not overwritten', () => {
  mockStorage();
  const s = fresh();
  earn(s, 100, 'quiz', t0);
  answer(s, 'gone', false, t0);
  save(s);
  const page = load(); // the quiz page loaded this, then awaited the bank files
  assert.equal(purchase('card', 'r1', 0, eco, t0 + 1).ok, true); // meanwhile, another tab buys a card
  const after = syncParkedStored(['other'], true, 'banksV1'); // what the page now does instead of save(page)
  assert.equal(after.questions.gone.parked, 'banksV1');
  assert.equal(load().cards.r1.stars, 1);
  assert.equal(load().crumbs!.bal, 40);
  assert.equal(page.cards.r1, undefined); // the stale copy was never saved
});

test('the parent retest queue and the child gate share one parked rule', () => {
  const q = (parked?: true | string) => ({ s: 1 as const, due: 0, w: 1, ...(parked ? { parked } : {}) });
  assert.equal(inReview(q(), 'b1'), true);
  assert.equal(inReview(q(true), 'b1'), true); // parked by an older tab: may be live
  assert.equal(inReview(q('b0'), 'b1'), true); // parked by another bank set
  assert.equal(inReview(q('b1'), 'b1'), false); // confirmed gone by these banks
  assert.equal(inReview({ s: 0, due: 0, w: 0 }, 'b1'), false); // retired
});

function mockStorage() {
  const data: Record<string, string> = {};
  resetUnlimitedCache();
  Object.defineProperty(globalThis, 'localStorage', {
    configurable: true,
    value: { getItem: (k: string) => (k in data ? data[k] : null), setItem: (k: string, v: string) => { data[k] = String(v); }, removeItem: (k: string) => { delete data[k]; } },
  });
  return data;
}

test('two tabs cannot double-spend: each purchase re-reads the stored save before it charges', () => {
  mockStorage();
  const s = fresh();
  earn(s, 70, 'quiz', t0);
  save(s);
  // both tabs rendered the shop showing 70 Crumbs; purchase() never trusts a page's copy
  assert.deepEqual(purchase('card', 'r1', 0, eco, t0 + 1), { ok: true, price: 60 }); // tab A
  assert.deepEqual(purchase('card', 'r1', 0, eco, t0 + 2), { ok: false, reason: 'owned' }); // tab B, same card: not charged
  assert.deepEqual(purchase('card', 'c1', 0, eco, t0 + 3), { ok: false, reason: 'poor' }); // tab B, another card: 10 left
  const after = load();
  assert.equal(after.crumbs!.bal, 10);
  assert.equal(after.crumbs!.buys.length, 1);
  assert.equal(after.cards.r1.stars, 1);
});

test('a star bought twice from the same stale page is charged once', () => {
  mockStorage();
  const s = fresh();
  earn(s, 200, 'quiz', t0);
  for (const x of ['c1', 'c2']) s.cards[x] = { stars: 1, srcSub: 'x', srcTier: 'b', acc: 90 };
  save(s);
  assert.equal(purchase('star', 'c2', 1, eco, t0).ok, true);
  assert.deepEqual(purchase('star', 'c2', 1, eco, t0), { ok: false, reason: 'stale' });
  assert.equal(load().crumbs!.bal, 170);
  assert.equal(load().cards.c2.stars, 2);
});
