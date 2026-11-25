import { test } from 'node:test';
import assert from 'node:assert/strict';
import { fresh, answer, milestoneAt, MILESTONE_NAME, finishQuiz, poolDisplay, syncMilestones, RQ_MAX, tierState, mergeRetests } from './store.ts';
import { cleanSave } from './cleansave.ts';
import { toEconomy } from './crumbs.ts';
import { sectionBoxes, dueFromStored, sectionStarted, nextGoal, goalFlags, examReady, tierFlags, trailFill, nextTier, retestNote, triesNote, stopEarned, tierBelow, rarityLabel, stopCount, stopWord, stopLine, finishLine, poolRightText, stopsText, previewSlots } from './section.ts';

const DAY = 86_400_000;
const t0 = new Date(2026, 10, 16, 10).getTime();

test('trailFill follows the milestones; the bar runs 0 to the Exam-ready stop', () => {
  const at = milestoneAt(300); // 50, 100, 151
  assert.deepEqual(trailFill(0, at), [0, 0, 0]);
  assert.deepEqual(trailFill(62, at).map(Math.round), [100, 24, 0]);
  assert.deepEqual(trailFill(500, at), [100, 100, 100]);
  assert.deepEqual(trailFill(1, [1, 1, 2]), [100, 100, 0]); // a zero-width segment is full once reached
  assert.deepEqual(MILESTONE_NAME, { b: '1st card', i: '2nd card', c: 'Exam-ready' });
});

test('nextGoal names the next UNEARNED stop, not the next one by count (finding 1)', () => {
  const at = milestoneAt(300);
  assert.deepEqual(nextGoal(0, at, [false, false, false]), { i: 0, need: 50 });
  assert.deepEqual(nextGoal(3, at, [true, false, false]), { i: 1, need: 97 }); // 1st card paid by an old tier clear, n small
  assert.deepEqual(nextGoal(62, at, [false, false, false]), { i: 0, need: 0 }); // met, the quiz-end sync is what is missing
  assert.deepEqual(nextGoal(62, at, [true, false, false]), { i: 1, need: 38 });
  assert.equal(nextGoal(200, at, [true, true, true]), null);
});

test('thresholds come from the live total, not the build pool (finding 2)', () => {
  assert.deepEqual(milestoneAt(300), [50, 100, 151]);
  assert.deepEqual(milestoneAt(120), [20, 40, 61]);
  assert.deepEqual(nextGoal(45, milestoneAt(120), [true, true, false]), { i: 2, need: 16 });
});

test('goalFlags and examReady: Exam-ready rests on the pool milestone, never on an old tier clear (finding 3)', () => {
  const s = fresh();
  const old = { passes: [], scores: [], best: 0, cleared: true, mastered: 25, total: 25 };
  s.progress.x = { b: old, i: { ...old }, c: { ...old } } as never; // all three generated tiers cleared before the switch
  assert.deepEqual(goalFlags(s, 'x'), [true, true, false]);
  assert.equal(examReady(s, 'x'), false);
  assert.deepEqual(nextGoal(3, milestoneAt(300), goalFlags(s, 'x')), { i: 2, need: 148 }); // "N more right to reach Exam-ready"
  (s.progress.x.c as { ms?: boolean }).ms = true;
  assert.equal(examReady(s, 'x'), true);
  assert.equal(nextGoal(151, milestoneAt(300), goalFlags(s, 'x')), null);
});

test('tierFlags: cleared and open per tier, the tier below gating the next', () => {
  const s = fresh();
  const all = { b: true, i: true, c: true };
  assert.deepEqual(tierFlags(s, 'x', all), { cleared: { b: false, i: false, c: false }, open: { b: true, i: false, c: false } });
  s.progress.x = { b: { passes: [], scores: [], best: 0, cleared: true } } as never;
  assert.deepEqual(tierFlags(s, 'x', all).open, { b: true, i: true, c: false });
  assert.deepEqual(tierFlags(s, 'x', { b: true, i: false, c: true }).open, { b: true, i: true, c: true }); // Intermediate unplayable: skipped
});

test('nextTier: the first playable, open tier not cleared', () => {
  const all = { b: true, i: true, c: true }, none = { b: false, i: false, c: false };
  assert.equal(nextTier(none, all, { b: true, i: false, c: false }), 'b');
  assert.equal(nextTier({ b: true, i: false, c: false }, all, { b: true, i: true, c: false }), 'i');
  assert.equal(nextTier(none, { b: false, i: true, c: true }, { b: true, i: true, c: false }), 'i'); // Basic unplayable
  assert.equal(nextTier(all, all, all), null);
  assert.equal(nextTier(none, none, all), null);
});

test('notes under Start: retests capped at what the quiz takes; no tries text for an unlimited account', () => {
  assert.equal(retestNote(0), '');
  assert.equal(retestNote(1), 'Starts with your 1 retest.');
  assert.equal(retestNote(7), 'Starts with your 3 retests.');
  assert.equal(triesNote(2, 3), '2 of 3 tries left today.');
  assert.equal(triesNote(Infinity, 3), '');
});

test('stopEarned: milestone reached, or the slot tier cleared before the section became one pool; not otherwise', () => {
  const s = fresh();
  assert.equal(stopEarned(s, 'x', 'b'), false);
  s.progress.x = { b: { passes: [], scores: [], best: 0, cleared: true, mastered: 25, total: 25 } } as never; // generated tier cleared, card awarded
  assert.equal(stopEarned(s, 'x', 'b'), true);
  assert.equal(stopEarned(s, 'x', 'i'), false);
  s.progress.y = { i: { passes: [], scores: [], best: 0, cleared: false, pool: true, ms: true } } as never; // milestone only
  assert.equal(stopEarned(s, 'y', 'i'), true);
  assert.equal(stopEarned(s, 'y', 'b'), false);
});

test('tierBelow names the nearest playable lower tier, as tierOpen skips unplayable ones', () => {
  assert.equal(tierBelow('c', { b: true, i: true, c: true }), 'i');
  assert.equal(tierBelow('c', { b: true, i: false, c: true }), 'b');
  assert.equal(tierBelow('i', { b: false, i: true, c: true }), null);
  assert.equal(tierBelow('b', { b: true, i: true, c: true }), null);
});

test('rarityLabel turns the CSS token into the label', () => {
  assert.equal(rarityLabel('epic'), 'Epic');
  assert.equal(rarityLabel('super-epic'), 'Super epic');
});


const pool = ['a', 'b', 'c', 'd', 'e'];
const groups = { a: 'p1', b: 'p1', c: 'p2', d: 'p2', e: 'p3' };
const setDisplay = (s: ReturnType<typeof fresh>, sub: string, ids: string[], g?: Record<string, string>) => {
  const row = (s.progress[sub] ??= {});
  row.b = Object.assign(tierState(s, sub, 'b'), poolDisplay(s, ids, g));
};

test('poolDisplay: tried, rq (retest ids), passages done of total; no passage fields without groups', () => {
  const s = fresh();
  answer(s, 'a', true, t0); answer(s, 'b', true, t0); // p1 done
  answer(s, 'c', false, t0); answer(s, 'd', true, t0); // p2 has a retest
  assert.deepEqual(poolDisplay(s, pool, groups), { tried: 4, rq: ['c'], pt: 3, pd: 1 });
  assert.deepEqual(poolDisplay(s, pool), { tried: 4, rq: ['c'] });
  assert.deepEqual(poolDisplay(fresh(), pool, groups), { tried: 0, rq: [], pt: 3, pd: 0 });
  const many = Array.from({ length: RQ_MAX + 10 }, (_, i) => 'q' + i);
  const s2 = fresh(); for (const id of many) answer(s2, id, false, t0);
  assert.equal(poolDisplay(s2, many).rq!.length, RQ_MAX);
  assert.equal(poolDisplay(s2, many).tried, many.length);
});

test('the display fields are set at quiz end on the Basic slot, not on the other slots; an older save lacks them', () => {
  const s = fresh();
  const ids = Array.from({ length: 24 }, (_, i) => 'pp-' + String(i).padStart(10, '0'));
  const gr = Object.fromEntries(ids.map((id, i) => [id, 'g' + Math.floor(i / 4)]));
  answer(s, ids[0], true, t0); answer(s, ids[1], false, t0);
  assert.equal(tierState(s, 'x', 'b').tried, undefined); // never played since the change: no fields
  syncMilestones(s, { x: ids }, () => undefined, t0, undefined, false, { x: gr });
  const b = tierState(s, 'x', 'b');
  assert.deepEqual([b.tried, b.rq, b.pt, b.pd], [2, [ids[1]], 6, 0]);
  assert.equal(tierState(s, 'x', 'i').rq, undefined);
  // finishQuiz passes poolGroups through
  const s2 = fresh(); answer(s2, ids[0], true, t0);
  finishQuiz(s2, { mode: 'tier', sub: 'x', score: 5, total: 10, ms: 1000, tags: [] } as never, () => undefined, t0, {}, undefined, { pools: { x: ids }, poolGroups: { x: gr } });
  assert.equal(tierState(s2, 'x', 'b').pt, 6);
});

test('cleanSave keeps the display fields and drops junk', () => {
  const s = fresh();
  s.progress.x = { b: { passes: [], scores: [], best: 0, cleared: false, pool: true, total: 30, mastered: 3, tried: 7, rq: ['pp-0123456789', 5, 'bad id'], pt: 4, pd: 9 } } as never;
  const b = cleanSave(JSON.parse(JSON.stringify(s))).progress.x.b;
  assert.deepEqual([b.tried, b.rq, b.pt, b.pd], [7, ['pp-0123456789'], 4, 4]);
  const old = cleanSave({ ...fresh(), progress: { y: { b: { passes: [], scores: [], best: 0, cleared: false } } } }).progress.y.b;
  assert.deepEqual([old.tried, old.rq, old.pt], [undefined, undefined, undefined]);
});

test('sectionBoxes: live due count from rq; a Daily Review that clears a retest shows at once; missing fields hide', () => {
  const s = fresh();
  assert.equal(sectionBoxes(s, 'x', t0), null); // never played since the change: boxes hidden
  answer(s, 'a', false, t0 - 2 * DAY); answer(s, 'b', false, t0 - 2 * DAY); answer(s, 'c', false, t0); // c due tomorrow
  setDisplay(s, 'x', ['a', 'b', 'c', 'd'], { a: 'g', b: 'g', c: 'h', d: 'h' });
  assert.deepEqual(sectionBoxes(s, 'x', t0), { tried: 3, due: 2, passages: { done: 0, total: 2 } });
  answer(s, 'a', true, t0); // cleared by a Daily Review (no quiz end yet)
  assert.equal(sectionBoxes(s, 'x', t0)!.due, 1);
  s.questions.b.parked = 'z'; // in the pool: parked flag ignored
  assert.equal(sectionBoxes(s, 'x', t0)!.due, 1);
  assert.equal(sectionBoxes(s, 'x', t0 + 2 * DAY)!.due, 2);
  const st = tierState(s, 'x', 'b'); delete st.rq; delete st.pt;
  assert.deepEqual(sectionBoxes(s, 'x', t0), { tried: 3, due: null, passages: null });
  assert.deepEqual(dueFromStored(s, ['x', 'nope'], t0), {}); // no rq: no pill
});

test('dueFromStored: one number per pool section from its rq', () => {
  const s = fresh();
  answer(s, 'a', false, t0 - 2 * DAY); answer(s, 'b', false, t0);
  setDisplay(s, 'x', ['a', 'b']);
  setDisplay(s, 'y', ['q']);
  assert.deepEqual(dueFromStored(s, ['x', 'y', 'z'], t0), { x: 1, y: 0 });
});

test('sectionStarted: counted, or any quiz on it', () => {
  const s = fresh();
  assert.equal(sectionStarted(s, 'x', 0), false);
  assert.equal(sectionStarted(s, 'x', 2), true);
  s.attempts.push({ ts: t0, mode: 'tier', sub: 'x', score: 1, total: 10, ms: 1, tags: [] } as never);
  assert.equal(sectionStarted(s, 'x', 0), true);
});

test('stop wording follows what was given (finding 5), the finish line names the stop (6), the verdict uses the pages words (8)', () => {
  assert.equal(stopLine('b', { dup: false }), '1st card earned');
  assert.equal(stopLine('i', { dup: true }, 'Hero Cookie'), '2nd card reached: +1 star on Hero Cookie');
  assert.equal(stopLine('c', null), 'Exam-ready reached');
  assert.equal(stopLine('c', { dup: false }), 'Exam-ready earned');
  assert.deepEqual([stopWord({ dup: false }), stopWord({ dup: true }), stopWord(null), stopWord(undefined)], ['earned', 'reached', 'reached', 'reached']);
  assert.equal(finishLine('c'), 'Finish a quiz to reach Exam-ready.');
  assert.equal(finishLine('b'), 'Finish a quiz to reach 1st card.');
  assert.equal(poolRightText(62, 300, false), '62 of 300 questions right');
  assert.equal(poolRightText(5, 40, true), '5 of 40 blanks right');
});

test('stops are counted the way the section page counts them (finding 7): Exam-ready only by the pool milestone', () => {
  const s = fresh();
  const old = { passes: [], scores: [], best: 0, cleared: true, mastered: 25, total: 25 };
  s.progress.x = { b: old, i: { ...old }, c: { ...old } } as never; // all three old tiers cleared; the pool's own c milestone not reached
  const all = { b: true, i: true, c: true };
  assert.deepEqual(stopCount(s, 'x', true, all), { reached: 2, of: 3 });
  assert.deepEqual(stopCount(s, 'x', false, all), { reached: 3, of: 3 }); // classic: tiers cleared
  assert.deepEqual(stopCount(s, 'x', false, { b: true, i: false, c: true }), { reached: 2, of: 2 });
  assert.equal(stopsText(1, 3), '1 of 3 stops reached');
  (s.progress.x.c as { ms?: boolean }).ms = true;
  assert.deepEqual(stopCount(s, 'x', true, all), { reached: 3, of: 3 });
});

test('previewSlots: earlier slots previews count as owned for the later ones (finding 9)', () => {
  const eco = toEconomy({
    cards: { s1: { name: 'S1', image: '', rarity: 'epic' }, s2: { name: 'S2', image: '', rarity: 'epic' }, r1: { name: 'R1', image: '', rarity: 'epic' }, r2: { name: 'R2', image: '', rarity: 'epic' } },
    order: { epic: ['r1', 'r2', 's1', 's2'] },
  } as never);
  const s = fresh();
  for (const slug of ['s1', 's2']) s.cards[slug] = { stars: 1, srcSub: 'z', srcTier: 'b', acc: 90, last: t0 };
  const out = previewSlots(s, [{ slug: 's1', earned: false }, { slug: 's2', earned: false }, { slug: 's1', earned: true }], eco);
  assert.deepEqual(out.map((p) => p && p.slug), ['r1', 'r2', null]); // not r1 twice
  assert.equal(s.cards.r1, undefined); // the save is untouched
});

test('poolDisplay: rq keeps the earliest-due ids, not the first in pool order', () => {
  const many = Array.from({ length: RQ_MAX + 5 }, (_, i) => 'q' + i);
  const s = fresh();
  many.forEach((id, i) => { answer(s, id, false, t0); s.questions[id].due = 1000 - i; }); // later ids are due first
  const rq = poolDisplay(s, many).rq!;
  assert.equal(rq.length, RQ_MAX);
  assert.equal(rq[0], 'q' + (RQ_MAX + 4));
  assert.ok(!rq.includes('q0'));
});

test('mergeRetests: a paper adds its retests to the stored rq, in due order, leaving tried/pd/pt alone', () => {
  const s = fresh();
  s.progress['p-sec'] = { b: { passes: [], scores: [], best: 0, cleared: false, pool: true, tried: 7, pd: 2, pt: 5, rq: ['x', 'gone'] } };
  answer(s, 'x', false, t0); s.questions.x.due = 500;
  answer(s, 'pp-y', false, t0); s.questions['pp-y'].due = 100;
  answer(s, 'pp-z', true, t0);
  answer(s, 'gen1', false, t0); // a generated question of the same sub-topic (a paper's fallback): the pool never asks it
  mergeRetests(s, { 'pp-y': 'p-sec', 'pp-z': 'p-sec', gen1: 'p-sec', w: 'other' }, ['pp-y', 'pp-z', 'gen1', 'w']);
  const b = s.progress['p-sec'].b!;
  assert.deepEqual(b.rq, ['pp-y', 'x']); // gone dropped, pp-z is retired, gen1 is not a past-paper id, pp-y is due first
  assert.deepEqual([b.tried, b.pd, b.pt], [7, 2, 5]);
  assert.equal(s.progress.other, undefined); // no slot, nothing created
});

test('syncMilestones: pd/pt are removed when a later quiz has no groups for the section', () => {
  const s = fresh();
  s.progress['p-sec'] = { b: { passes: [], scores: [], best: 0, cleared: false, pool: true, pd: 1, pt: 3 } };
  syncMilestones(s, { 'p-sec': Array.from({ length: 30 }, (_, i) => 'k' + i) }, () => undefined, t0, undefined, false, {});
  assert.equal(s.progress['p-sec'].b!.pd, undefined);
  assert.equal(s.progress['p-sec'].b!.pt, undefined);
});
