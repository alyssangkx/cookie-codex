import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  PAUSE_MAX, newClock, pauseLeft, canPause, startPause, endPause, tickPaper, timeUsed, blanks, paperScore, reviewList,
  paperOk, draftOk, loadDraft, saveDraft, draftCurrent, clearDraft, type PaperDraft,
} from './paper.ts';

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
  assert.deepEqual(c, { deadline: T + 34 * MIN, pauseUsed: 4 * MIN, pausedAt: 0 });
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
