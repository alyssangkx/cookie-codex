import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  PAUSE_MAX, newClock, pauseLeft, canPause, startPause, endPause, tickPaper, timeUsed, blanks, paperScore, reviewList,
  paperOk, draftOk, loadDraft, saveDraft, draftCurrent, clearDraft, draftState, discardDraft, GRACE, paperSubject, staleText, type PaperDraft,
} from './paper.ts';
import { fresh, openAttempt, closeStalePapers, answer, finishQuiz, LEFT_BLANK, STALE_PAPER_MS } from './store.ts';

const DAY = 86_400_000;

const MIN = 60_000;
const T = 1_790_000_000_000;

function memStore() {
  const data: Record<string, string> = {};
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

test('wall clock: leaving the page does not stop it, and the paper submits itself at zero', () => {
  const c = newClock(T, 30 * MIN);
  assert.deepEqual(tickPaper(c, T + 10 * MIN), { clock: c, left: 20 * MIN, submit: false, resumed: false });
  const late = tickPaper(c, T + 45 * MIN); // e.g. the phone was locked past the end
  assert.equal(late.left, 0);
  assert.equal(late.submit, true);
});

test('one pause of up to 10 minutes: the clock stops, the deadline moves, and a second pause is refused', () => {
  let c = newClock(T, 30 * MIN);
  assert.equal(canPause(c, T), true);
  c = startPause(c, T + 5 * MIN);
  const during = tickPaper(c, T + 9 * MIN);
  assert.equal(during.left, 25 * MIN); // frozen at the pause moment
  assert.equal(during.submit, false);
  assert.equal(pauseLeft(c, T + 9 * MIN), 6 * MIN);
  c = endPause(c, T + 9 * MIN); // paused 4 minutes
  assert.deepEqual(c, { deadline: T + 34 * MIN, pauseUsed: 4 * MIN, pausedAt: 0, pauseTaken: true });
  assert.equal(canPause(c, T + 10 * MIN), false); // one pause per paper, even with 6 minutes unused
  assert.deepEqual(startPause(c, T + 10 * MIN), c);
});

test('a pause that runs out ends by itself at 10 minutes, even if the page was closed', () => {
  let c = startPause(newClock(T, 30 * MIN), T + 5 * MIN);
  const r = tickPaper(c, T + 60 * MIN); // came back long after: the pause ended at 15 min, the clock ran on
  assert.equal(r.resumed, true);
  assert.equal(r.clock.pauseUsed, PAUSE_MAX);
  assert.equal(r.clock.deadline, T + 40 * MIN);
  assert.equal(r.submit, true);
  c = startPause(newClock(T, 30 * MIN), T + 5 * MIN);
  const r2 = tickPaper(c, T + 16 * MIN); // 1 minute after the pause ran out: 24 minutes left
  assert.equal(r2.left, 24 * MIN);
  assert.equal(r2.submit, false);
});

test('no pause once the time is up', () => {
  assert.equal(canPause(newClock(T, MIN), T + MIN), false);
});

test('time used: start to submit, capped at the deadline, minus the pause', () => {
  let c = newClock(T, 30 * MIN);
  assert.equal(timeUsed(c, T, T + 12 * MIN), 12 * MIN);
  assert.equal(timeUsed(c, T, T + 90 * MIN), 30 * MIN); // submitted late (offline): never more than the paper's time
  c = endPause(startPause(c, T + 2 * MIN), T + 5 * MIN);
  assert.equal(timeUsed(c, T, T + 20 * MIN), 17 * MIN);
  assert.equal(timeUsed(startPause(newClock(T, 30 * MIN), T + 2 * MIN), T, T + 5 * MIN), 2 * MIN); // still paused
});

test('score, blanks and the review list (wrong and blank only, in paper order)', () => {
  const answers = [0, 1, 2, 3, 0];
  const picks = [0, 2, null, 3, 1];
  assert.equal(paperScore(answers, picks), 2);
  assert.equal(blanks(picks), 1);
  assert.deepEqual(reviewList(answers, picks), [1, 2, 4]);
  assert.deepEqual(reviewList([1, 1], [1, 1]), []);
  assert.deepEqual(reviewList([1, 1], [null, null]), [0, 1]);
});

test('papers use 4-option items that are not in a passage set', () => {
  assert.equal(paperOk({ options: [1, 2, 3, 4] }), true);
  assert.equal(paperOk({ options: [1, 2, 3, 4], group: 'read-01' }), false);
  assert.equal(paperOk({ options: [1, 2, 3, 4, 5, 6, 7, 8] }), false);
});

const draft = (o: Partial<PaperDraft> = {}): PaperDraft => ({
  v: 1, owner: 'u1|5', ts: T, rev: 0, topics: ['math-ratio'], mix: 'wa', ids: ['a', 'b'], picks: [null, null], at: 0,
  clock: newClock(T, 10 * MIN), mins: 10, ...o,
});

test('draft: belongs to one player; shape is checked', () => {
  assert.equal(draftOk(draft(), 'u1|5'), true);
  assert.equal(draftOk(draft(), 'u2|5'), false); // another child on this device
  assert.equal(draftOk(draft({ picks: [null] }), 'u1|5'), false);
  assert.equal(draftOk(null, 'u1|5'), false);
  assert.equal(draftOk({ v: 2 }, 'u1|5'), false);
});

test('draft: resume after reload; a stale tab cannot write or bring back a submitted paper', () => {
  memStore();
  const a = saveDraft(draft())!;
  assert.equal(a.rev, 1);
  assert.deepEqual(loadDraft('u1|5'), a);
  const tab2 = loadDraft('u1|5')!; // a second tab resumes the same paper
  const a2 = saveDraft({ ...a, picks: [1, null] })!; // tab 1 answers
  assert.equal(a2.rev, 2);
  assert.equal(draftCurrent(tab2), false);
  assert.equal(saveDraft({ ...tab2, picks: [3, 3] }), null); // tab 2 is stale: refused
  assert.deepEqual(loadDraft('u1|5')!.picks, [1, null]);
  assert.equal(draftCurrent(a2), true);
  clearDraft(); // tab 1 submits
  assert.equal(draftCurrent(a2), false); // a second submit from any tab is refused
  assert.equal(saveDraft(a2), null); // and nothing recreates the draft
  assert.equal(loadDraft('u1|5'), null);
});

test('one pause is a flag: a pause of 0 ms still uses it', () => {
  const c = endPause(startPause(newClock(T, 30 * MIN), T + MIN), T + MIN);
  assert.equal(c.pauseUsed, 0);
  assert.equal(c.pauseTaken, true);
  assert.equal(canPause(c, T + 2 * MIN), false);
});

test('draft state: live, due within the grace (handed in), stale after it (put away unscored)', () => {
  const c = newClock(T, 30 * MIN);
  assert.equal(draftState(c, T + 29 * MIN), 'live');
  assert.equal(draftState(c, T + 30 * MIN), 'due');
  assert.equal(draftState(c, T + 30 * MIN + GRACE), 'due');
  assert.equal(draftState(c, T + 30 * MIN + GRACE + 1), 'stale');
  assert.equal(draftState(c, T + 3 * 86_400_000), 'stale'); // opened days later: never a fresh result
  const paused = startPause(c, T + 10 * MIN); // closed while paused: the pause ends at 10 min, then the clock runs
  assert.equal(draftState(paused, T + 39 * MIN), 'live');
  assert.equal(draftState(paused, T + 40 * MIN + GRACE + 1), 'stale');
});

test('a new paper never replaces a live or due one (another tab); a stale one may be replaced', () => {
  memStore();
  const a = saveDraft(draft(), T + MIN)!;
  assert.equal(saveDraft(draft({ ts: T + 5 * MIN }), T + 5 * MIN), null); // live: refused
  assert.equal(loadDraft('u1|5')!.ts, a.ts);
  assert.equal(saveDraft(draft({ ts: T + 11 * MIN }), T + 11 * MIN), null); // due (10 min paper ended at T+10): refused
  const b = saveDraft(draft({ ts: T + 25 * MIN }), T + 25 * MIN); // stale: replaced
  assert.equal(b!.ts, T + 25 * MIN);
});

test('a paper open record is matched by its own ts: finishing or discarding one never touches another', () => {
  const now = new Date(2026, 10, 20, 12).getTime();
  const s = fresh();
  openAttempt(s, { mode: 'paper', total: 10 }, now - 5 * 60_000); // running on another device
  openAttempt(s, { mode: 'paper', total: 10 }, now - 60_000); // this paper (started later)
  finishQuiz(s, { mode: 'paper', score: 5, total: 10, ms: 1, tags: [] }, () => undefined, now, {}, now - 60_000);
  assert.deepEqual(s.attempts.filter((a) => a.open).map((a) => a.ts), [now - 5 * 60_000]); // the other device's stays
  openAttempt(s, { mode: 'paper', total: 10 }, now - 30_000);
  memStore();
  const d = saveDraft(draft({ ts: now - 30_000 }), now - 30_000)!;
  discardDraft(s, d);
  assert.equal(loadDraft('u1|5'), null);
  assert.deepEqual(s.attempts.filter((a) => a.open).map((a) => a.ts), [now - 5 * 60_000]); // only its own record closed
});

test('open paper records over 2 days old are closed (no paper runs that long); newer ones and tier records stay', () => {
  const now = new Date(2026, 10, 20, 12).getTime();
  const s = fresh();
  openAttempt(s, { mode: 'paper', total: 10 }, now - 3 * DAY);
  openAttempt(s, { mode: 'paper', total: 10 }, now - DAY); // e.g. still on another device's draft: kept
  openAttempt(s, { mode: 'tier', sub: 'x', tier: 'b', total: 10 }, now - 3 * DAY);
  closeStalePapers(s, now);
  assert.deepEqual(s.attempts.map((a) => [a.mode, a.ts]), [['paper', now - DAY], ['tier', now - 3 * DAY]]);
  assert.equal(STALE_PAPER_MS, 2 * DAY);
});

test('wording shared by /quiz/ and /paper/', () => {
  assert.equal(paperSubject({ topics: ['sci-cycles-reproduction'] }), 'Science');
  assert.equal(paperSubject({ topics: ['chi-ciyu'] }), 'Chinese');
  assert.equal(paperSubject({ topics: [] }), 'practice');
  assert.match(staleText({ topics: ['math-ratio'], ts: T }), /^Your Math paper from .+ put away without a score\. Nothing from it was counted\.$/);
});

test('a blank on purpose is stored apart from a time-out blank', () => {
  const s = fresh();
  answer(s, 'p', false, T, false, LEFT_BLANK);
  answer(s, 't', false, T, false);
  assert.equal(s.questions.p.a, LEFT_BLANK);
  assert.equal(s.questions.t.a, '');
  answer(s, 'n', true, T, false); // a right answer to a new question on a paper stores nothing
  assert.equal(s.questions.n, undefined);
});
