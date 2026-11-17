import { test } from 'node:test';
import assert from 'node:assert/strict';
import { fresh, answer, finishQuiz, dayKey, liveStreak, power, openAttempt, attemptsToday, load, importCode, exportCode, migrate } from './store.ts';
import ALIASES from '../data/quiz/id-aliases.json' with { type: 'json' };

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
const small = { 'old-a': 'new-a', 'old-b': 'new-b', 'old-c': 'new-c' };
const v1Save = () => {
  const s: any = fresh();
  s.schemaVersion = 1;
  s.questions = {
    'old-a': { s: 2, due: t0 + 3 * DAY, w: 2 },
    'old-b': { s: 0, due: 0, w: 1 },
    'old-gone': { s: 1, due: t0, w: 1 },
  };
  s.settings.playerName = 'Kept';
  return s;
};

test('a v1 save loads as v2: same retest states under the new ids, unknown ids dropped, backup written', () => {
  const v1 = v1Save();
  const data = mockStorage({ 'ccx:save': JSON.stringify(v1) });
  const s = load(small);
  assert.equal(s.schemaVersion, 2);
  assert.deepEqual(s.questions, {
    'new-a': { s: 2, due: t0 + 3 * DAY, w: 2 },
    'new-b': { s: 0, due: 0, w: 1 },
  });
  assert.equal(s.settings.playerName, 'Kept');
  assert.deepEqual(JSON.parse(data['ccx:backup']), v1); // pre-migration copy, old ids intact
  assert.equal(JSON.parse(data['ccx:save']).schemaVersion, 2); // migrated save is stored
  assert.deepEqual(load(small).questions, s.questions); // a second load is a plain v2 load
});

test('a v2 save loads untouched and writes no backup', () => {
  const v2: any = fresh();
  v2.questions = { 'new-a': { s: 1, due: t0, w: 1 } };
  const data = mockStorage({ 'ccx:save': JSON.stringify(v2) });
  assert.deepEqual(load(small).questions, v2.questions);
  assert.equal(data['ccx:backup'], undefined);
});

test('importCode accepts a v1 code and migrates it; a newer code is still refused', async () => {
  const data = mockStorage();
  const code = await exportCode(v1Save() as any);
  const s = await importCode(code, small);
  assert.equal(s.schemaVersion, 2);
  assert.deepEqual(Object.keys(s.questions).sort(), ['new-a', 'new-b']);
  assert.ok(data['ccx:backup']);
  const newer: any = { ...fresh(), schemaVersion: 3 };
  await assert.rejects(importCode(await exportCode(newer), small), /newer version/);
});

test('the real alias map renames ids and maps to unique new ids', () => {
  const entries = Object.entries(ALIASES as Record<string, string>);
  assert.ok(entries.length > 1000);
  const [oldId, newId] = entries[0];
  const s: any = { ...fresh(), schemaVersion: 1, questions: { [oldId]: { s: 1, due: 5, w: 1 } } };
  assert.deepEqual(migrate(s).questions, { [newId]: { s: 1, due: 5, w: 1 } });
});
