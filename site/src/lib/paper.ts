// WA/SA practice papers, submit-then-review (docs/learning-loop-design.md item 2): pure clock, scoring and
// draft rules, so the quiz page stays thin and the rules are tested. The draft lives in store.ts's kv (never in
// the save), so there is no schema change and an old tab never meets a field it cannot read.
import { kv } from './store.ts';

/** One pause per paper, up to 10 minutes. */
export const PAUSE_MAX = 10 * 60_000;

/** deadline: wall-clock end (moves later by the pause used); pausedAt: 0 while running. */
export interface PaperClock { deadline: number; pauseUsed: number; pausedAt: number }

export const newClock = (start: number, ms: number): PaperClock => ({ deadline: start + ms, pauseUsed: 0, pausedAt: 0 });

/** Pause time still available (counts down while paused). */
export const pauseLeft = (c: PaperClock, now: number) =>
  Math.max(0, PAUSE_MAX - c.pauseUsed - (c.pausedAt ? Math.max(0, now - c.pausedAt) : 0));

/** Only one pause per paper, and never after the time is up. */
export const canPause = (c: PaperClock, now: number) => !c.pausedAt && c.pauseUsed === 0 && c.deadline > now;

export const startPause = (c: PaperClock, now: number): PaperClock => (canPause(c, now) ? { ...c, pausedAt: now } : c);

/** End the pause: the deadline moves later by the time paused, capped at what was left of the 10 minutes. */
export function endPause(c: PaperClock, now: number): PaperClock {
  if (!c.pausedAt) return c;
  const used = Math.min(Math.max(0, now - c.pausedAt), PAUSE_MAX - c.pauseUsed);
  return { deadline: c.deadline + used, pauseUsed: c.pauseUsed + used, pausedAt: 0 };
}

/**
 * One clock step: a pause that has run out ends by itself (at the moment it ran out, even if the page was closed
 * then); `submit` is true once the time is up and the paper is not paused. `left` is the paper time remaining.
 */
export function tickPaper(c: PaperClock, now: number): { clock: PaperClock; left: number; submit: boolean; resumed: boolean } {
  let resumed = false;
  if (c.pausedAt && pauseLeft(c, now) === 0) {
    c = endPause(c, c.pausedAt + (PAUSE_MAX - c.pauseUsed));
    resumed = true;
  }
  const left = Math.max(0, c.deadline - (c.pausedAt || now));
  return { clock: c, left, submit: !c.pausedAt && left === 0, resumed };
}

/** Time spent working: start to submit (or the deadline, if later), minus the pause. */
export function timeUsed(c: PaperClock, start: number, end: number): number {
  const done = endPause(c, end);
  return Math.max(0, Math.min(end, done.deadline) - start - done.pauseUsed);
}

/** A pick is an option index, or null for a blank. */
export type Pick = number | null;
export const blanks = (picks: Pick[]) => picks.filter((p) => p == null).length;
export const paperScore = (answers: number[], picks: Pick[]) => answers.filter((a, i) => picks[i] === a).length;
/** Indices to review after submitting: wrong and blank answers only, in paper order. */
export const reviewList = (answers: number[], picks: Pick[]) => answers.flatMap((a, i) => (picks[i] === a ? [] : [i]));

/** Items a paper can use: 4 options and not part of a passage set (sets are never split, so they stay out). */
export const paperOk = (q: { options: unknown[]; group?: string }) => q.options.length === 4 && !q.group;

// ------------------------------------------------------------------ draft (resume after a reload or a locked phone)

export interface PaperDraft {
  v: 1;
  owner: string; // who started it: sync owner + save createdAt, so another child on this device never sees it
  ts: number; // the open attempt's start: the paper's id
  rev: number; // bumped on every write; a tab whose rev is stale refuses to write or submit (two tabs)
  topics: string[]; mix: string; ids: string[]; picks: Pick[]; at: number; clock: PaperClock; mins: number;
}
const DRAFT_KEY = 'paper-draft';

/** A stored draft is usable when it has the right shape and belongs to this player. */
export function draftOk(d: unknown, owner: string): d is PaperDraft {
  const x = d as PaperDraft;
  return !!x && x.v === 1 && x.owner === owner && typeof x.ts === 'number' && typeof x.rev === 'number'
    && Array.isArray(x.ids) && x.ids.length > 0 && Array.isArray(x.picks) && x.picks.length === x.ids.length
    && Array.isArray(x.topics) && !!x.clock && typeof x.clock.deadline === 'number';
}

export const draftOwner = (createdAt: number) => `${kv.get('sync:owner') ?? ''}|${createdAt}`;

export function loadDraft(owner: string): PaperDraft | null {
  try {
    const d = JSON.parse(kv.get(DRAFT_KEY) ?? 'null');
    return draftOk(d, owner) ? d : null;
  } catch { return null; }
}

/**
 * Write the draft unless this tab's copy is stale; returns the stored draft (rev + 1) or null. rev 0 = a new paper
 * (always written). Otherwise the stored draft must be this paper at this rev: if another tab wrote since, or
 * submitted it (the draft is gone), this tab must not bring it back.
 */
export function saveDraft(d: PaperDraft): PaperDraft | null {
  if (d.rev !== 0 && !draftCurrent(d)) return null;
  const next = { ...d, rev: d.rev + 1 };
  kv.set(DRAFT_KEY, JSON.stringify(next));
  return next;
}

/** True when this tab holds the latest stored copy of the draft. False once another tab wrote or submitted it. */
export function draftCurrent(d: PaperDraft): boolean {
  const cur = loadDraft(d.owner);
  return !!cur && cur.ts === d.ts && cur.rev === d.rev;
}

export const clearDraft = () => kv.del(DRAFT_KEY);
