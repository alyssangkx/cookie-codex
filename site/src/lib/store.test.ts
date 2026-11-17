import { test } from 'node:test';
import assert from 'node:assert/strict';
import { fresh, answer, finishQuiz, dayKey, liveStreak, power, openAttempt, attemptsToday, load, importCode, exportCode } from './store.ts';

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
  answer(s, 'b', true); answer(s, 'b', true); answer(s, 'b', true);
  assert.equal(s.questions.b.s, 0);
});

test('two passes on different days clear the tier and award the card; a duplicate adds a star', () => {
  const s = fresh();
  const reward = () => ({ slug: 'muscle-cookie', dup: false });
  const q = { mode: 'tier' as const, sub: 'x', tier: 'b' as const, total: 10, ms: 600_000, tags: [] };
  assert.equal(finishQuiz(s, { ...q, score: 9 }, reward, t0).cleared, false);
  assert.equal(finishQuiz(s, { ...q, score: 10 }, reward, t0 + 3600_000).cleared, false); // same day
  assert.equal(finishQuiz(s, { ...q, score: 7 }, reward, t0 + DAY).passed, false); // 70% fails
  const r = finishQuiz(s, { ...q, score: 8 }, reward, t0 + DAY);
  assert.ok(r.cleared);
  assert.deepEqual(r.reward, { slug: 'muscle-cookie', dup: false, stars: 1 });
  assert.equal(s.cards['muscle-cookie'].acc, 95); // best two passes: 100, 90
  assert.equal(power({ acc: 95, stars: 2, last: t0 }, t0), 100);
  assert.equal(power({ acc: 80, stars: 1, last: t0 }, t0 + 5 * 7 * DAY), 70); // 2 idle weeks past 3: -10
  // a short quiz never passes, even at 100%
  assert.equal(finishQuiz(s, { ...q, sub: 'z', score: 5, total: 5 }, reward, t0).passed, false);
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
  assert.equal(s.schemaVersion, 2);
  assert.deepEqual(s.questions, {});
  assert.deepEqual(s.cards, v1.cards);
  assert.deepEqual(s.progress, v1.progress);
  assert.deepEqual(s.streak, v1.streak);
  assert.equal(s.settings.playerName, 'Kept');
  assert.deepEqual(JSON.parse(data['ccx:backup']), v1);
  assert.equal(JSON.parse(data['ccx:save']).schemaVersion, 2);
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
  assert.equal(s.schemaVersion, 2);
  assert.deepEqual(s.cards, {});
  assert.equal(data['ccx:failed:1'], raw);
  assert.equal(data['ccx:failed:2'], undefined);
  assert.equal(data['ccx:save'], raw);
  assert.equal(data['ccx:backup'], undefined);
});

test('two loads of the same broken save write ccx:failed:1 once and create no extra keys', () => {
  for (const raw of ['{not json', JSON.stringify({ ...fresh(), schemaVersion: 3 })]) {
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
  assert.equal(s.schemaVersion, 2);
  assert.deepEqual(s.questions, {});
  assert.equal(data['ccx:backup'], undefined);
  assert.equal(data['ccx:save'], 'current-save');
  const newer: any = { ...fresh(), schemaVersion: 3 };
  await assert.rejects(importCode(await exportCode(newer)), /newer version/);
  assert.equal(data['ccx:backup'], undefined);
});
