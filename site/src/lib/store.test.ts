import { test } from 'node:test';
import assert from 'node:assert/strict';
import { DAILY_QUIZ_CAP, QUIZ_CAP_ON, DEFAULT_CAP_MIN, quizzesToday, quizCapReached, capReached, dayBlock, triesUsedUp, isUnlimited, resetUnlimitedCache, beginQuiz, tierOpen, setProgression, fresh, answer, finishQuiz, dayKey, liveStreak, power, openAttempt, attemptsToday, attemptsLeft, triesPerDay, migrate, syncTiers, load, importCode, exportCode } from './store.ts';

const DAY = 86_400_000;
const t0 = new Date(2026, 10, 16, 10).getTime(); // Mon 16 Nov 2026, 10:00 local

test('spaced retest: wrong -> 1, 3, 7 days -> retired; wrong at any step resets', () => {
  const s = fresh();
  answer(s, 'a', true, t0);
  assert.deepEqual(s.questions.a, { s: 0, due: 0, w: 0 }); // new + correct = retired at once
  answer(s, 'b', false, t0);
  assert.equal(s.questions.b.s, 1);
  assert.equal(s.questions.b.due, t0 + DAY);
  answer(s, 'b', true, t0 + DAY);
  assert.equal(s.questions.b.due, t0 + 4 * DAY);
  answer(s, 'b', true, t0 + 4 * DAY);
  assert.equal(s.questions.b.s, 3);
  answer(s, 'b', false, t0 + 11 * DAY);
  assert.deepEqual([s.questions.b.s, s.questions.b.w], [1, 2]);
  answer(s, 'b', true, t0 + 12 * DAY); answer(s, 'b', true, t0 + 15 * DAY); answer(s, 'b', true, t0 + 22 * DAY);
  assert.equal(s.questions.b.s, 0);
});

test('a tier clears only when all its ids are retired; a wrong answer delays it; a duplicate card adds a star', () => {
  const s = fresh();
  const reward = () => ({ slug: 'muscle-cookie', dup: false });
  const ids = ['q1', 'q2', 'q3'];
  const tierIds = { 'x|b': ids };
  const q = { mode: 'tier' as const, sub: 'x', tier: 'b' as const, total: 10, ms: 600_000, tags: [], score: 9 };
  answer(s, 'q1', true, t0); answer(s, 'q2', false, t0); answer(s, 'q3', true, t0);
  let r = finishQuiz(s, q, reward, t0, tierIds);
  assert.equal(r.cleared, false); // q2 is wrong: not retired yet
  assert.deepEqual([s.progress.x.b.mastered, s.progress.x.b.total], [2, 3]);
  answer(s, 'q2', true, t0 + DAY); // step 2 (due in 3 days): still not retired
  assert.equal(finishQuiz(s, q, reward, t0 + DAY, tierIds).cleared, false);
  answer(s, 'q2', true, t0 + 4 * DAY);
  assert.equal(finishQuiz(s, q, reward, t0 + 4 * DAY, tierIds).cleared, false); // step 3
  answer(s, 'q2', true, t0 + 11 * DAY);
  r = finishQuiz(s, { ...q, score: 3 }, reward, t0 + 11 * DAY, tierIds); // a low score does not matter
  assert.ok(r.cleared);
  assert.deepEqual(r.reward, { slug: 'muscle-cookie', dup: false, stars: 1 });
  assert.equal(r.newlyCleared.length, 1);
  assert.equal(finishQuiz(s, q, reward, t0 + 12 * DAY, tierIds).cleared, false); // already cleared: no second award
  assert.equal(s.cards['muscle-cookie'].stars, 1);
  // a cleared tier is never un-cleared by a later wrong answer
  answer(s, 'q1', false, t0 + 13 * DAY);
  finishQuiz(s, q, reward, t0 + 13 * DAY, tierIds);
  assert.equal(s.progress.x.b.cleared, true);
  assert.equal(power({ acc: 95, stars: 2, last: t0 }, t0), 100);
  assert.equal(power({ acc: 80, stars: 1, last: t0 }, t0 + 5 * 7 * DAY), 70); // 2 idle weeks past 3: -10
  // a duplicate card adds a star
  const s2 = fresh();
  answer(s2, 'r1', true, t0);
  finishQuiz(s2, { ...q, sub: 'y' }, reward, t0, { 'y|b': ['r1'] });
  answer(s2, 'r2', true, t0);
  const d = finishQuiz(s2, { ...q, sub: 'z' }, () => ({ slug: 'muscle-cookie', dup: true }), t0, { 'z|b': ['r2'] });
  assert.equal(d.reward?.stars, 2);
  // papers do not retire new questions
  answer(s, 'p', true, t0, false);
  assert.equal(s.questions.p, undefined);
  // an abandoned quiz still counts as a try
  openAttempt(s, { sub: 'w', tier: 'b', total: 10 });
  assert.equal(attemptsToday(s, 'w', 'b'), 1);
});

test('streak: weeks with 4+ goal days; weekends never break it; a thin week does', () => {
  const s = fresh();
  const quiz = { mode: 'review' as const, score: 5, total: 5, ms: 300_000, tags: [] };
  const day = (n: number) => t0 + n * DAY; // day 0 = Monday
  const play = (n: number) => { finishQuiz(s, quiz, () => undefined, day(n)); return finishQuiz(s, quiz, () => undefined, day(n)); };
  assert.ok(play(0).goalJustMet);
  [1, 2, 3].forEach(play); // Mon-Thu: 4 goal days in week 1
  assert.equal(liveStreak(s, day(4)), 1);
  assert.equal(liveStreak(s, day(9)), 1); // week 2 in progress with 0 days: still 1
  [7, 8, 9, 10].forEach(play); // week 2: 4 days, weekend skipped
  assert.equal(liveStreak(s, day(11)), 2);
  [14, 15].forEach(play); // week 3: only 2 days
  assert.equal(liveStreak(s, day(21)), 0); // week 4 starts: week 3 was thin, streak resets
  assert.deepEqual([s.streak.best, s.streak.studyDays], [2, 10]);
  assert.equal(s.days[dayKey(day(15))].quizzes, 2);
});

test('review fixes: tiers skip unplayable lower tiers; goal days keep their status; short quizzes count', async () => {
  const { tierOpen, fresh: f, finishQuiz: fq, liveStreak: ls, today } = await import('./store.ts');
  const s = f();
  assert.equal(tierOpen(s, 'x', 'i'), false);
  assert.equal(tierOpen(s, 'x', 'i', { b: false, i: true, c: true }), true); // Basic unplayable: Intermediate opens
  assert.equal(tierOpen(s, 'x', 'c', { b: false, i: true, c: true }), false); // still needs Intermediate
  const quiz = { mode: 'review' as const, score: 5, total: 5, ms: 25_000, tags: [] };
  for (let d = 0; d < 4; d++) { fq(s, quiz, () => undefined, t0 + d * DAY); fq(s, quiz, () => undefined, t0 + d * DAY); }
  assert.equal(ls(s, t0 + 4 * DAY), 1);
  s.settings.dailyGoalQuizzes = 3; // a parent raises the goal: past goal days still count
  assert.equal(ls(s, t0 + 4 * DAY), 1);
  const s2 = f();
  for (let k = 0; k < 10; k++) fq(s2, quiz, () => undefined); // ten 25-second quizzes today
  assert.equal(today(s2).min, 4); // 250 s, not 10 x round(0.4 min) = 0
});

// ---------------------------------------------------------------- schema v1 -> v2 (stable question ids)

function mockStorage(initial: Record<string, string> = {}) {
  const data = { ...initial };
  resetUnlimitedCache(); // isUnlimited() caches the player name per page load
  Object.defineProperty(globalThis, 'localStorage', {
    configurable: true,
    value: {
      getItem: (k: string) => (k in data ? data[k] : null),
      setItem: (k: string, v: string) => { data[k] = String(v); },
      removeItem: (k: string) => { delete data[k]; },
    },
  });
  return data;
}
const v1Save = () => {
  const s: any = fresh();
  s.schemaVersion = 1;
  s.questions = { 'old-a': { s: 2, due: t0 + 3 * DAY, w: 2 }, 'old-b': { s: 0, due: 0, w: 1 } };
  s.progress = { x: { b: { passes: ['2026-11-15'], scores: [90], best: 90, cleared: false } } };
  s.cards = { 'muscle-cookie': { stars: 2, srcSub: 'x', srcTier: 'b', acc: 90 } };
  s.streak = { current: 3, best: 5, lastDay: '2026-11-15', freezeUsedWeek: null, studyDays: 12 };
  s.settings.playerName = 'Kept';
  return s;
};

test('v1 -> v2 keeps cards, progress and streak, clears questions, backs up the old save', () => {
  const v1 = v1Save();
  const data = mockStorage({ 'ccx:save': JSON.stringify(v1) });
  const s = load();
  assert.equal(s.schemaVersion, 4);
  assert.deepEqual(s.questions, {});
  assert.deepEqual(s.cards, v1.cards);
  assert.deepEqual(s.progress, v1.progress);
  assert.deepEqual(s.streak, v1.streak);
  assert.equal(s.settings.playerName, 'Kept');
  assert.deepEqual(JSON.parse(data['ccx:backup']), v1);
  assert.equal(JSON.parse(data['ccx:save']).schemaVersion, 4);
});

test('a v2 save loads untouched and writes no backup', () => {
  const v2: any = fresh();
  v2.questions = { 'new-a': { s: 1, due: t0, w: 1 } };
  const data = mockStorage({ 'ccx:save': JSON.stringify(v2) });
  assert.deepEqual(load().questions, v2.questions);
  assert.equal(data['ccx:backup'], undefined);
});

test('a failed migration preserves the raw save in ccx:failed:1 and leaves ccx:save and ccx:backup alone', () => {
  const raw = JSON.stringify({ ...fresh(), schemaVersion: 0 }); // no migration from 0
  const data = mockStorage({ 'ccx:save': raw });
  const s = load();
  assert.equal(s.schemaVersion, 4);
  assert.deepEqual(s.cards, {});
  assert.equal(data['ccx:failed:1'], raw);
  assert.equal(data['ccx:failed:2'], undefined);
  assert.equal(data['ccx:save'], raw);
  assert.equal(data['ccx:backup'], undefined);
});

test('two loads of the same broken save write ccx:failed:1 once and create no extra keys', () => {
  for (const raw of ['{not json', JSON.stringify({ ...fresh(), schemaVersion: 5 })]) {
    const data = mockStorage({ 'ccx:save': raw, 'ccx:backup': 'old-backup' });
    let writes = 0;
    const set = (localStorage as any).setItem;
    (localStorage as any).setItem = (k: string, v: string) => { writes++; set(k, v); };
    load(); load();
    assert.equal(writes, 1);
    assert.deepEqual(Object.keys(data).sort(), ['ccx:backup', 'ccx:failed:1', 'ccx:save']);
    assert.equal(data['ccx:failed:1'], raw);
    assert.equal(data['ccx:backup'], 'old-backup');
  }
});

test('with all 3 slots full a new broken save rotates in: 2->1, 3->2, new->3', () => {
  const data = mockStorage({});
  for (const raw of ['{bad1', '{bad2', '{bad3', '{bad4']) { data['ccx:save'] = raw; load(); }
  assert.equal(data['ccx:failed:1'], '{bad2');
  assert.equal(data['ccx:failed:2'], '{bad3');
  assert.equal(data['ccx:failed:3'], '{bad4');
  data['ccx:save'] = '{bad3'; load(); // duplicate of a stored copy: no change
  assert.equal(data['ccx:failed:1'], '{bad2');
  assert.equal(data['ccx:failed:3'], '{bad4');
  assert.equal(Object.keys(data).filter((k) => k.startsWith('ccx:failed')).length, 3);
});

test('a legacy ccx:failed key is deduped against, folded into the slots once, then removed', () => {
  const data = mockStorage({ 'ccx:failed': '{old', 'ccx:save': '{old' });
  load(); // same as the legacy copy: folds it, adds nothing else
  assert.equal(data['ccx:failed:1'], '{old');
  assert.equal(data['ccx:failed:2'], undefined);
  assert.equal('ccx:failed' in data, false);
  data['ccx:save'] = '{new'; load();
  assert.equal(data['ccx:failed:1'], '{old');
  assert.equal(data['ccx:failed:2'], '{new');
  // legacy value folded even when the current save is different, and rotation keeps the newest
  const d2 = mockStorage({ 'ccx:failed': '{L', 'ccx:failed:1': '{a', 'ccx:failed:2': '{b', 'ccx:save': '{c' });
  load();
  assert.deepEqual([d2['ccx:failed:1'], d2['ccx:failed:2'], d2['ccx:failed:3']], ['{b', '{L', '{c']);
  assert.equal('ccx:failed' in d2, false);
});

test('importCode migrates a v1 code, refuses a newer one, and writes no backup', async () => {
  const data = mockStorage({ 'ccx:save': 'current-save' });
  const s = await importCode(await exportCode(v1Save() as any));
  assert.equal(s.schemaVersion, 4);
  assert.deepEqual(s.questions, {});
  assert.equal(data['ccx:backup'], undefined);
  assert.equal(data['ccx:save'], 'current-save');
  const newer: any = { ...fresh(), schemaVersion: 5 };
  await assert.rejects(importCode(await exportCode(newer)), /newer version/);
  assert.equal(data['ccx:backup'], undefined);
});

// ---- P-level tries: P1-P5 get 5 tries a day per tier, P6 keeps 3
setProgression({ 'p5-sub': 5, 'p4-sub': 4 });

test('a P5 tier allows 5 tries a day; a P6 (or unlisted) tier allows 3', () => {
  const s = fresh();
  for (let i = 0; i < 3; i++) { openAttempt(s, { sub: 'p5-sub', tier: 'b', total: 10 }); openAttempt(s, { sub: 'p6-sub', tier: 'b', total: 10 }); }
  assert.equal(triesPerDay('p5-sub'), 5);
  assert.equal(triesPerDay('p6-sub'), 3);
  assert.equal(attemptsLeft(s, 'p5-sub', 'b'), 2);
  assert.equal(attemptsLeft(s, 'p6-sub', 'b'), 0);
  openAttempt(s, { sub: 'p5-sub', tier: 'b', total: 10 }); openAttempt(s, { sub: 'p5-sub', tier: 'b', total: 10 });
  assert.equal(attemptsLeft(s, 'p5-sub', 'b'), 0);
});

test('migration 2 -> 3 keeps cleared tiers, cards and everything else', () => {
  const v2: any = fresh();
  v2.schemaVersion = 2;
  v2.questions = { q1: { s: 1, due: t0, w: 1 } };
  v2.settings.playerName = 'Kept';
  v2.progress = {
    'p4-sub': { b: { passes: ['2026-11-14', '2026-11-15'], scores: [90, 90], best: 90, cleared: true } },
    'p6-sub': { b: { passes: ['2026-11-15'], scores: [90], best: 90, cleared: false } },
  };
  v2.cards = { 'muscle-cookie': { stars: 1, srcSub: 'p4-sub', srcTier: 'b', acc: 90 } };
  const before = JSON.stringify(v2);
  const s = migrate(v2);
  assert.equal(JSON.stringify(v2), before);
  assert.equal(s.schemaVersion, 4);
  assert.equal(s.progress['p4-sub'].b.cleared, true);
  assert.equal(s.progress['p6-sub'].b.cleared, false); // lazily judged from its questions at the next quiz
  assert.deepEqual(s.cards, v2.cards);
  assert.deepEqual(s.questions, v2.questions);
  assert.equal(s.settings.playerName, 'Kept');
});

test('a correct answer to a retest that is not due leaves it unchanged; a due one advances; a wrong one resets', () => {
  const s = fresh();
  answer(s, 'a', false, t0);
  const before = { ...s.questions.a };
  answer(s, 'a', true, t0 + 1000); // not due yet
  assert.deepEqual(s.questions.a, before);
  answer(s, 'a', true, t0 + DAY); // due
  assert.deepEqual([s.questions.a.s, s.questions.a.due], [2, t0 + 4 * DAY]);
  answer(s, 'a', true, t0 + DAY + 1000); // not due again
  assert.equal(s.questions.a.s, 2);
  answer(s, 'a', false, t0 + DAY + 2000); // wrong still resets
  assert.equal(s.questions.a.s, 1);
});

test('a tier cannot clear on the day a wrong answer happened', () => {
  const s = fresh();
  const reward = () => ({ slug: 'muscle-cookie', dup: false });
  const q = { mode: 'tier' as const, sub: 'x', tier: 'b' as const, total: 10, ms: 1, tags: [], score: 9 };
  answer(s, 'q1', false, t0);
  for (let i = 0; i < 5; i++) answer(s, 'q1', true, t0 + i * 1000);
  assert.equal(finishQuiz(s, q, reward, t0 + 5000, { 'x|b': ['q1'] }).cleared, false);
  assert.equal(s.questions.q1.s, 1);
});

test('syncTiers clears only open tiers, in b-i-c order within one pass', () => {
  const s = fresh();
  const reward = (sub: string, t: string) => ({ slug: `${sub}-${t}`, dup: false });
  answer(s, 'b1', true, t0); answer(s, 'i1', true, t0);
  // Intermediate is fully retired but Basic is not: Intermediate must stay uncleared
  answer(s, 'b2', false, t0);
  let out = syncTiers(s, { 'x|i': ['i1'], 'x|b': ['b1', 'b2'] }, reward, t0);
  assert.deepEqual(out, []);
  assert.equal(s.progress.x.i?.cleared, false);
  // Basic completes; listed after Intermediate, both clear in the same pass
  answer(s, 'b2', true, t0 + DAY); answer(s, 'b2', true, t0 + 4 * DAY); answer(s, 'b2', true, t0 + 11 * DAY);
  out = syncTiers(s, { 'x|i': ['i1'], 'x|b': ['b1', 'b2'] }, reward, t0 + 11 * DAY);
  assert.deepEqual(out.map((o) => o.tier), ['b', 'i']);
});

test('perfect first-ever Basic quiz clears Basic and awards the card; only that case', () => {
  const reward = (sub: string, t: string) => ({ slug: `${sub}-${t}`, dup: false });
  const q = (tier: 'b' | 'i' | 'c', score: number) => ({ mode: 'tier' as const, sub: 'x', tier, total: 10, ms: 1, tags: [], score });
  const ids = { 'x|b': ['b1', 'b2'], 'x|i': ['i1', 'i2'] };

  // 10/10 on the first Basic attempt: cleared at once, card awarded, Intermediate open
  let s = fresh();
  answer(s, 'b1', true, t0); answer(s, 'b2', false, t0); // not all retired: only the rule can clear it
  let r = finishQuiz(s, q('b', 10), reward, t0, ids);
  assert.equal(r.autoPromoted, true);
  assert.equal(r.cleared, true);
  assert.equal(r.reward?.slug, 'x-b');
  assert.equal(s.cards['x-b'].stars, 1);
  assert.equal(s.progress.x.b.cleared, true);
  assert.equal(tierOpen(s, 'x', 'i'), true);

  // a second attempt at 10/10 does not auto-clear
  s = fresh();
  finishQuiz(s, q('b', 8), reward, t0, ids);
  r = finishQuiz(s, q('b', 10), reward, t0 + 1000, ids);
  assert.equal(r.autoPromoted, false);
  assert.equal(s.progress.x.b.cleared, false);

  // 9/10 on the first try does not
  s = fresh();
  assert.equal(finishQuiz(s, q('b', 9), reward, t0, ids).autoPromoted, false);
  assert.equal(s.progress.x.b.cleared, false);

  // Competent first try at 10/10 does not
  s = fresh();
  assert.equal(finishQuiz(s, q('c', 10), reward, t0, { ...ids, 'x|c': ['c1', 'c2'] }).autoPromoted, false);
  assert.equal(s.progress.x.c.cleared, false);

  // a first-ever Intermediate 10/10 clears it, awards the card, and opens Competent
  const ids3 = { ...ids, 'x|c': ['c1', 'c2'] };
  s = fresh();
  answer(s, 'b1', true, t0); answer(s, 'b2', true, t0); // Basic cleared so Intermediate is a real play
  finishQuiz(s, q('b', 10), reward, t0 - 1000, ids3); // perfect first Basic clears it
  answer(s, 'i1', true, t0); answer(s, 'i2', false, t0);
  r = finishQuiz(s, q('i', 10), reward, t0, ids3);
  assert.equal(r.autoPromoted, true);
  assert.equal(r.reward?.slug, 'x-i');
  assert.equal(s.progress.x.i.cleared, true);
  assert.equal(tierOpen(s, 'x', 'c'), true);
  // a second Intermediate try does not, 9/10 does not
  s = fresh();
  finishQuiz(s, q('i', 8), reward, t0, ids3);
  assert.equal(finishQuiz(s, q('i', 10), reward, t0 + 1000, ids3).autoPromoted, false);
  s = fresh();
  assert.equal(finishQuiz(s, q('i', 9), reward, t0, ids3).autoPromoted, false);
  // an abandoned earlier Intermediate try blocks it
  s = fresh();
  openAttempt(s, { sub: 'x', tier: 'i', total: 10 }, t0 - 9000);
  openAttempt(s, { sub: 'x', tier: 'i', total: 10 }, t0 - 5000);
  assert.equal(finishQuiz(s, q('i', 10), reward, t0, ids3).autoPromoted, false);

  // this quiz's own open record is not an earlier try
  s = fresh();
  openAttempt(s, { sub: 'x', tier: 'b', total: 10 }, t0 - 5000);
  assert.equal(finishQuiz(s, q('b', 10), reward, t0, ids).autoPromoted, true);
  // but an earlier ABANDONED try does count: quitting after a mistake and retrying until perfect gets no promote
  s = fresh();
  openAttempt(s, { sub: 'x', tier: 'b', total: 10 }, t0 - 9000); // abandoned
  openAttempt(s, { sub: 'x', tier: 'b', total: 10 }, t0 - 5000); // this quiz
  assert.equal(finishQuiz(s, q('b', 10), reward, t0, ids).autoPromoted, false);
  // ...and neither does an open attempt for this very quiz
  s = fresh();
  openAttempt(s, { sub: 'x', tier: 'b', total: 10 }, t0);
  assert.equal(finishQuiz(s, q('b', 10), reward, t0 + 1, ids).cleared, true);
});

// ---- daily limits: 120 minutes or 10 quizzes; Admin has none
const rw = () => null;
const finish = (s: any, mode: 'tier' | 'paper' | 'review', n = 1, ms = 1000) => {
  for (let i = 0; i < n; i++) {
    const a: any = { mode, score: 5, total: 10, ms, tags: [] };
    if (mode === 'tier') { a.sub = 'x'; a.tier = 'b'; }
    finishQuiz(s, a, rw as any);
  }
};

test('quiz cap (when switched on): the 11th tier quiz is blocked; Daily Review after 10 is allowed and does not count', () => {
  mockStorage({});
  const s = fresh();
  finish(s, 'tier', 9);
  assert.equal(dayBlock(s, 'tier', true), null);
  finish(s, 'paper', 1); // papers count too: 10 now
  assert.equal(quizzesToday(s), DAILY_QUIZ_CAP);
  assert.equal(quizCapReached(s, true), true);
  assert.equal(dayBlock(s, 'tier', true), 'quizzes');
  assert.equal(dayBlock(s, 'paper', true), 'quizzes');
  assert.equal(dayBlock(s, 'review', true), null);
  finish(s, 'review', 3);
  assert.equal(quizzesToday(s), DAILY_QUIZ_CAP); // reviews never count
  assert.equal(dayBlock(s, 'review', true), null);
});

test('quiz cap is off for now (owner, 19 Nov 2026): 10+ quizzes do not block; the time cap still does', () => {
  mockStorage({});
  const s = fresh();
  assert.equal(QUIZ_CAP_ON, false);
  finish(s, 'tier', 12, 60_000);
  assert.equal(quizCapReached(s), false);
  assert.equal(dayBlock(s, 'tier'), null);
  assert.equal(beginQuiz(s, 'paper', { total: 10 }), null);
  finish(s, 'tier', 1, 120 * 60_000);
  assert.equal(dayBlock(s, 'tier'), 'time');
});

test('an open (started, unfinished) tier quiz counts toward the quiz cap once, not twice', () => {
  mockStorage({});
  const s = fresh();
  finish(s, 'tier', 9);
  openAttempt(s, { sub: 'x', tier: 'b', total: 10 });
  assert.equal(quizzesToday(s), 10);
  finish(s, 'tier', 1); // finishing replaces the open record
  assert.equal(quizzesToday(s), 10);
});

test('time cap still works at the 120-minute default; review is blocked too', () => {
  mockStorage({});
  const s = fresh();
  assert.equal(s.settings.dailyCapMin, DEFAULT_CAP_MIN);
  assert.equal(DEFAULT_CAP_MIN, 120);
  finish(s, 'tier', 1, 119 * 60_000);
  assert.equal(capReached(s), false);
  finish(s, 'tier', 1, 60_000);
  assert.equal(capReached(s), true);
  assert.equal(dayBlock(s, 'tier'), 'time');
  assert.equal(dayBlock(s, 'review'), 'time');
});

test('Admin: no time cap, no quiz cap, unlimited tries per day', () => {
  try {
    mockStorage({ 'ccx:player-name': 'Admin' });
    assert.equal(isUnlimited(), true);
    const s = fresh();
    finish(s, 'tier', 12, 20 * 60_000); // 240 minutes, 12 quizzes
    for (let i = 0; i < 9; i++) openAttempt(s, { sub: 'x', tier: 'b', total: 10 });
    assert.equal(capReached(s), false);
    assert.equal(quizCapReached(s), false);
    assert.equal(dayBlock(s, 'tier'), null);
    assert.equal(triesUsedUp(s, 'x', 'b'), false);
    assert.equal(attemptsLeft(s, 'x', 'b'), Infinity);
    mockStorage({ 'ccx:player-name': 'Alyssa' });
    assert.equal(isUnlimited(), false);
    assert.equal(triesUsedUp(s, 'x', 'b'), true);
    assert.equal(isUnlimited('Admin'), true);
  } finally {
    mockStorage({});
  }
});

test('beginQuiz is blocked at the time cap and records nothing', () => {
  mockStorage({});
  const s = fresh();
  finish(s, 'tier', 10, 12 * 60_000); // 120 minutes
  const n = s.attempts.length;
  assert.equal(beginQuiz(s, 'tier', { sub: 'x', tier: 'b', total: 10 }), 'time');
  assert.equal(beginQuiz(s, 'paper', { total: 10 }), 'time');
  assert.equal(beginQuiz(s, 'review', { total: 5 }), 'time');
  assert.equal(s.attempts.length, n);
});

test('a started paper counts toward the 10; an abandoned one still counts; finishing does not double-count', () => {
  mockStorage({});
  const s = fresh();
  finish(s, 'tier', 8);
  assert.equal(beginQuiz(s, 'paper', { total: 10 }), null);
  assert.equal(quizzesToday(s), 9); // abandoned paper counts
  assert.equal(beginQuiz(s, 'paper', { total: 10 }), null);
  assert.equal(quizzesToday(s), 10);
  finish(s, 'paper', 1); // finishing replaces one open record
  assert.equal(quizzesToday(s), 10);
  assert.equal(dayBlock(s, 'paper', true), 'quizzes');
});

test('migration 3 -> 4: a cap of exactly 45 becomes 120; other values stay', () => {
  const v3 = (cap: number): any => { const x: any = fresh(); x.schemaVersion = 3; x.settings.dailyCapMin = cap; return x; };
  assert.equal(migrate(v3(45)).settings.dailyCapMin, 120);
  assert.equal(migrate(v3(60)).settings.dailyCapMin, 60);
  assert.equal(migrate(v3(90)).schemaVersion, 4);
});

test('Admin: every tier is open with nothing cleared; a normal player is locked', () => {
  const s = fresh();
  try {
    mockStorage({ 'ccx:player-name': 'Admin' });
    assert.equal(tierOpen(s, 'x', 'c'), true);
    assert.equal(tierOpen(s, 'x', 'i'), true);
    mockStorage({ 'ccx:player-name': 'Alyssa' });
    assert.equal(tierOpen(s, 'x', 'c'), false);
  } finally {
    mockStorage({});
  }
});

test('a wrong answer keeps the picked option text (capped), through retests and retirement; old saves still load', () => {
  const s = fresh();
  const t0 = Date.UTC(2026, 10, 19);
  answer(s, 'q', false, t0, true, 'x'.repeat(200));
  assert.equal(s.questions.q.a, 'x'.repeat(120));
  answer(s, 'q', false, t0, true, 'wrong again');
  assert.equal(s.questions.q.a, 'wrong again');
  assert.equal(s.questions.q.w, 2);
  answer(s, 'q', true, t0 + DAY); answer(s, 'q', true, t0 + 4 * DAY); answer(s, 'q', true, t0 + 11 * DAY);
  assert.deepEqual(s.questions.q, { s: 0, due: 0, w: 2, a: 'wrong again' }); // retired, still shows the last pick
  answer(s, 't', false, t0); // ran out of time: a blank answer
  assert.equal(s.questions.t.a, '');
  answer(s, 'q', false, t0 + 12 * DAY); // a later blank answer replaces the old pick
  assert.equal(s.questions.q.a, '');
  answer(s, 'n', true, t0);
  assert.deepEqual(s.questions.n, { s: 0, due: 0, w: 0 });
  const old = fresh(); old.questions.z = { s: 1, due: t0, w: 1 }; // a save from before the field existed
  assert.deepEqual(migrate(JSON.parse(JSON.stringify(old))).questions.z, { s: 1, due: t0, w: 1 });
});
