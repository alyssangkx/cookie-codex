// Client-side save (docs/game-design.md section 8). Every page reads and writes progress
// through this module, so a backend can replace localStorage later.
import progression from '../data/progression.json' with { type: 'json' };
import {
  crumbsOf, earn, quizCrumbs, rewardPreview, buyCard, buyStar, achievementPreview, alBand,
  LEGENDARY_MIN_QUESTIONS, LEGENDARY_MIN_TOPICS, LEGENDARY_MAX_BAND,
  type BuyResult, type Crumbs, type Economy, type Preview,
} from './crumbs.ts';

export type School = 'math' | 'science' | 'english' | 'chinese';
export type Tier = 'b' | 'i' | 'c';
export const TIERS: Tier[] = ['b', 'i', 'c'];
export const TIER_NAME: Record<Tier, string> = { b: 'Basic', i: 'Intermediate', c: 'Competent' };

// passes/scores/best are history for display only; `cleared` is set by syncTiers (all questions retired).
// mastered/total are the last count seen when a quiz ended; hash is tierHash() of the ids they were counted against
// (optional, added 20 Nov 2026 with no schema bump; older states lack it and fall back to the size check).
export type TierState = { passes: string[]; scores: number[]; best: number; cleared: boolean; mastered?: number; total?: number; hash?: string;
  pool?: true; ms?: true }; // one-pool slots (ADR 0011): pool = counts are past-paper counts; ms = milestone reached on the pool
// s: 0 retired, 1-3 retest step (due in 1, 3, 7 days); w: times answered wrong
// a: the option text picked on the latest wrong answer, '' when it was not answered because time ran out, LEFT_BLANK
// when it was left blank on purpose (a paper submitted with blanks, 20 Nov 2026); optional,
// added 19 Nov 2026 for the parent page; older saves simply lack it, so no schema bump. Kept after the question
// retires, so the parent still sees it.
// parked: a retest whose id was in no bank when Daily Review last loaded every bank (syncParked). It is not counted as
// due, and is never deleted (ADR 0002): an older tab missing newer bank files may park live states, so the next Daily
// Review unparks any parked id it finds, and answering a question always unparks it. Optional, no schema bump.
// Since 20 Nov 2026 a newer build stores the bank-set hash it parked against (`banksHash` in train.ts) instead of true;
// a state parked by any other bank set (an older tab writes true) still counts toward reviewDueCount, so it cannot hide
// Daily Review until this build has re-checked it. Older code treats any truthy value as parked.
export type QState = { s: 0 | 1 | 2 | 3; due: number; w: number; a?: string; parked?: true | string };
export const PICK_MAX = 120; // characters of a picked option kept in the save
export const LEFT_BLANK = '\u2205'; // "∅": a paper question left blank on purpose (never an option's text)
export interface Attempt {
  ts: number; mode: 'tier' | 'review' | 'paper'; sub?: string; tier?: Tier; topics?: string[];
  score: number; total: number; ms: number; tags: string[];
  open?: boolean; // started but not finished: still counts as a try
}
// The interface keeps its v1 name so imports stay unchanged; schemaVersion is now 4 (see `migrations`).
export interface SaveV1 {
  schemaVersion: 4;
  createdAt: number;
  settings: {
    dailyCapMin: number; dailyGoalQuizzes: number;
    extraTime: boolean; psleDate: string; playerName: string;
  };
  progress: Record<string, Partial<Record<Tier, TierState>>>;
  questions: Record<string, QState>;
  cards: Record<string, { stars: number; srcSub: string; srcTier: Tier; acc: number; last?: number }>;
  attempts: Attempt[];
  days: Record<string, { quizzes: number; min: number; correct: number; total: number; ms?: number; goal?: boolean }>;
  streak: { current: number; best: number; lastDay: string | null; freezeUsedWeek: string | null; studyDays: number };
  last: { sub: string; tier: Tier } | null;
  /** Crumbs ledger (crumbs.ts). Optional, added 20 Nov 2026 with no schema bump (ADR 0002); absent until first earned. */
  crumbs?: Crumbs;
  /** A revision test a parent sent from the parent page (owner, 23 Nov 2026): up to 10 of the child's mistakes, made due
   *  at once. Optional, no schema bump. Daily Review asks the ones still due first; answered, they leave it by themselves. */
  revision?: { ids: string[]; ts: number };
}

export const REVISION_MAX = 10;
const KEY = 'ccx:save';
const BACKUP_KEY = 'ccx:backup'; // copy of a save taken just before a migration rewrites it
export const SCHEMA = 4;
const DAY = 86_400_000;
const STEP_DAYS = [0, 1, 3, 7];
export const TIER_MIN: Record<Tier, number> = { b: 12, i: 15, c: 20 };
export const MIN_POOL = 20; // a tier is playable (and can clear) only with at least this many questions
export const PASS = 0.8;
export const QUIZ_SIZE = 10; // a pass needs a full 10-question quiz
export const WEEK_GOAL_DAYS = 4; // a streak week needs 4 goal days; rest days never break it
export const DEFAULT_CAP_MIN = 120; // default daily training time, in minutes (parent range 45-180)
export const DAILY_QUIZ_CAP = 10; // tier quizzes + WA/SA papers per day; Daily Review does not count
// Owner, 19 Nov 2026: the quiz-count limit is off for now; set this to true to bring it back (time cap unaffected).
export const QUIZ_CAP_ON = false;
export const ATTEMPTS_PER_DAY = 3; // tries per tier per day for P6 sub-topics (and any sub-topic with no listed P-level)
export const ATTEMPTS_PER_DAY_LOW = 5; // P1-P5 sub-topics

// P-level rule: tries per tier per day depend on the sub-topic's P-level (highest outcome level in the
// syllabus JSON). The generated progression.json (scripts/quiz/build_progression.py) lists only the P1-P5
// sub-topics, so store.ts never imports the big syllabus; an unlisted sub-topic (all P6, all Chinese)
// counts as P6. Clearing does not depend on the level: every tier clears when all its questions are mastered.
let levels: Record<string, number> = progression.levels;
/** Tests replace the map; pages never need to. */
export function setProgression(l: Record<string, number>) { levels = l; }
export const subLevel = (sub: string) => levels[sub] ?? 6;
export const isLow = (sub: string) => subLevel(sub) <= 5;
export const triesPerDay = (sub: string) => (isLow(sub) ? ATTEMPTS_PER_DAY_LOW : ATTEMPTS_PER_DAY);

export const fresh = (): SaveV1 => ({
  schemaVersion: 4,
  createdAt: Date.now(),
  settings: { dailyCapMin: DEFAULT_CAP_MIN, dailyGoalQuizzes: 2, extraTime: false, psleDate: '2027-09-30', playerName: '' },
  progress: {}, questions: {}, cards: {}, attempts: [], days: {},
  streak: { current: 0, best: 0, lastDay: null, freezeUsedWeek: null, studyDays: 0 },
  last: null,
});

/** Fill fields missing from older or imported saves; unknown fields are kept. */
function normalise(s: any): SaveV1 {
  const base = fresh();
  return { ...base, ...s, settings: { ...base.settings, ...s.settings }, streak: { ...base.streak, ...s.streak } };
}

/** One step per schema version: migrations[n] turns a version-n save into version n+1. */
export const migrations: Record<number, (s: any) => any> = {
  // 1 -> 2: question ids were stem hashes, now they hash topic | template | params. No alias map
  // (the site was never deployed with v1 saves), so retest states are cleared; everything else stays.
  1: (s) => ({ ...s, questions: {} }),
  // 2 -> 3: tiers clear by mastery (every question retired) instead of two passes. A cleared tier stays
  // cleared and keeps its card (nothing is ever taken away). A tier whose questions are all retired but
  // not yet marked is cleared lazily: store.ts has no question ids, so syncTiers() runs at the end of the
  // next quiz that touches the tier (the quiz page passes the ids). Saves need no field changes.
  // Consequence: an already fully-retired tier clears only after its next quiz, not at load time
  // (deliberately no load-time sync).
  2: (s) => s,
  // 3 -> 4: the default daily cap rose from 45 to 120 minutes (deliberate: the owner asked for a 2-hour cap
  // for the existing child). Only the old default (exactly 45) moves;
  // any other value was chosen by a parent and stays.
  3: (s) => (s.settings?.dailyCapMin === 45 ? { ...s, settings: { ...s.settings, dailyCapMin: DEFAULT_CAP_MIN } } : s),
};

/** Short, order-independent hash of a tier's question ids (cyrb53 over the sorted ids, base 36). syncTiers stores it
 * on the tier state; train.ts computes the same value per tier at build time. */
export function tierHash(ids: readonly string[]): string {
  const str = [...ids].sort().join('\n');
  let h1 = 0xdeadbeef, h2 = 0x41c6ce57;
  for (let i = 0; i < str.length; i++) {
    const c = str.charCodeAt(i);
    h1 = Math.imul(h1 ^ c, 2654435761);
    h2 = Math.imul(h2 ^ c, 1597334677);
  }
  h1 = Math.imul(h1 ^ (h1 >>> 16), 2246822507) ^ Math.imul(h2 ^ (h2 >>> 13), 3266489909);
  h2 = Math.imul(h2 ^ (h2 >>> 16), 2246822507) ^ Math.imul(h1 ^ (h1 >>> 13), 3266489909);
  return (4294967296 * (2097151 & h2) + (h1 >>> 0)).toString(36);
}

/** "N mastered" for display: only when the stored count was made against the tier's current questions. After a
 * bank redesign (20 Nov 2026: the first banks were a pilot) the stored count points at questions that are gone,
 * so it reads as 0 until the next quiz on the tier recounts it (syncTiers). No schema bump: an old tab must never
 * meet a save version it cannot read. A state with a stored id hash must match `hash` (and the size), which also
 * catches a redesign of the same size; an older state without one, or a caller without the hash, falls back to the
 * size check. */
export const liveMastered = (st: { mastered?: number; total?: number; hash?: string }, count: number | undefined, hash?: string) => {
  if (!st.mastered || count === undefined || st.total !== count) return 0; // unknown bank size: treat as stale
  if (st.hash && hash && st.hash !== hash) return 0; // same size, different questions
  return st.mastered;
};

/** Run every migration from the save's version up to SCHEMA. Does not touch storage. */
export function migrate(s: any): any {
  let v = s.schemaVersion;
  while (v < SCHEMA) {
    const step = migrations[v];
    if (!step) throw new Error(`No migration from save version ${v}.`);
    s = { ...step(s), schemaVersion: ++v };
  }
  return s;
}

/** Copy the current save string to `ccx:backup`. The parent page calls this just before an import replaces it. */
export function backupLocal() {
  try {
    const raw = localStorage.getItem(KEY);
    if (raw !== null) localStorage.setItem(BACKUP_KEY, raw);
  } catch { /* full or blocked */ }
}

const FAILED_KEYS = ['ccx:failed:1', 'ccx:failed:2', 'ccx:failed:3']; // up to 3 distinct preserved copies of saves this site cannot read
const LEGACY_FAILED_KEY = 'ccx:failed'; // an older single-slot key: folded into the slots once, then removed
const SPARE_FAILED_KEY = 'ccx:failed:spare'; // staging slot while rotating

/**
 * Keep `raw` in ccx:failed:1..3 unless a stored copy already equals it. First free slot; when all 3 are
 * full, rotate (2 -> 1, 3 -> 2, new -> 3) so the newest broken save is always kept. A legacy
 * ccx:failed value goes through the same steps first, then its key is removed.
 */
function preserveBroken(raw: string) {
  const slots = FAILED_KEYS.map((k) => localStorage.getItem(k));
  const legacy = localStorage.getItem(LEGACY_FAILED_KEY);
  for (const v of [legacy, raw]) {
    if (v === null || slots.includes(v)) continue;
    const free = slots.findIndex((x) => x === null);
    if (free >= 0) {
      localStorage.setItem(FAILED_KEYS[free], v);
      slots[free] = v;
    } else {
      // write the new copy to a spare key first; only once it is stored, drop the oldest and shift
      localStorage.setItem(SPARE_FAILED_KEY, v); // throws on quota: nothing has been lost yet
      localStorage.setItem(FAILED_KEYS[0], slots[1]!);
      localStorage.setItem(FAILED_KEYS[1], slots[2]!);
      localStorage.setItem(FAILED_KEYS[2], v);
      localStorage.removeItem(SPARE_FAILED_KEY);
      slots.splice(0, 3, slots[1], slots[2], v);
    }
  }
  if (legacy !== null && slots.includes(legacy)) localStorage.removeItem(LEGACY_FAILED_KEY);
}

export function load(): SaveV1 {
  let raw: string | null = null;
  try {
    raw = localStorage.getItem(KEY);
    if (raw) {
      let s = JSON.parse(raw);
      if (typeof s?.schemaVersion === 'number' && s.schemaVersion < SCHEMA) {
        s = migrate(s); // may throw: then nothing below runs and ccx:backup is untouched
        backupLocal();
        save(normalise(s)); // a failed write must not lose the migrated save in memory
      }
      if (s?.schemaVersion === SCHEMA) return normalise(s);
      throw new Error('Unreadable save version.'); // e.g. a newer site's save: preserve it below
    }
  } catch {
    // Unreadable, unknown-version, newer-version or failed-migration save: keep the raw string in
    // ccx:failed:1..3 (see preserveBroken) so a later save() cannot destroy the only copy.
    // ccx:save and ccx:backup are left as they were.
    if (raw) {
      try { preserveBroken(raw); } catch { /* full or blocked */ }
    }
  }
  return fresh();
}

const DIRTY_KEY = 'ccx:sync:dirty'; // set by every save(); sync.ts clears it once the server has the copy
let saveHook: (() => void) | null = null;
/** sync.ts registers a callback that runs after every save(). */
export function setSaveHook(fn: (() => void) | null) { saveHook = fn; }

export function save(s: SaveV1) {
  try { localStorage.setItem(KEY, JSON.stringify(s)); localStorage.setItem(DIRTY_KEY, '1'); } catch { /* full or blocked */ }
  try { saveHook?.(); } catch { /* sync must never break a save */ }
}

/** The raw save string, for sync. */
export function readLocalRaw(): string | null {
  try { return localStorage.getItem(KEY); } catch { return null; }
}
/** Replace the local save with a copy from the server. Does not mark it unsynced and does not fire the hook. */
export function replaceLocal(data: unknown) {
  try { localStorage.setItem(KEY, JSON.stringify(data)); localStorage.removeItem(DIRTY_KEY); } catch { /* full or blocked */ }
}
/** Put a raw save back as the local save and mark it unsynced (a child's stashed save, on their next sign-in). */
export function restoreDirty(raw: string) {
  try { localStorage.setItem(KEY, raw); localStorage.setItem(DIRTY_KEY, '1'); } catch { /* full or blocked */ }
}
/** Remove the local save (it was another child's). The caller backs it up first. */
export function clearLocal() { try { localStorage.removeItem(KEY); localStorage.removeItem(DIRTY_KEY); } catch { /* ignore */ } }
export const isDirty = () => { try { return localStorage.getItem(DIRTY_KEY) === '1'; } catch { return false; } };
export function clearDirty() { try { localStorage.removeItem(DIRTY_KEY); } catch { /* ignore */ } }
/** True when a save holds any real progress (used to decide whether replacing it needs a backup). */
export const hasProgress = (s: Partial<SaveV1> | null | undefined) =>
  !!s && (Object.keys(s.progress ?? {}).length > 0 || Object.keys(s.cards ?? {}).length > 0 ||
    (s.attempts?.length ?? 0) > 0 || Object.keys(s.days ?? {}).length > 0);

/** The stored Crumbs balance, for the header (no migration, no writes; 0 when unreadable). */
export function crumbBalance(): number {
  try { const b = JSON.parse(readLocalRaw() ?? '{}')?.crumbs?.bal; return typeof b === 'number' && b > 0 ? Math.floor(b) : 0; } catch { return 0; }
}

/** Small string store for sync and login metadata (device id, tokens, revs). This module stays the only code that touches localStorage. */
export const kv = {
  get(k: string): string | null { try { return localStorage.getItem('ccx:' + k); } catch { return null; } },
  set(k: string, v: string) { try { localStorage.setItem('ccx:' + k, v); } catch { /* full or blocked */ } },
  del(k: string) { try { localStorage.removeItem('ccx:' + k); } catch { /* ignore */ } },
};

// ---------------------------------------------------------------- dates

export const dayKey = (t = Date.now()) => {
  const d = new Date(t);
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
};
const shiftDay = (key: string, n: number) => {
  const [y, m, d] = key.split('-').map(Number);
  return dayKey(new Date(y, m - 1, d + n).getTime());
};
/** ISO-ish week id (Monday start), used for the weekly streak freeze. */
export const weekId = (key: string) => {
  const [y, m, d] = key.split('-').map(Number);
  const dt = new Date(y, m - 1, d);
  const monday = new Date(y, m - 1, d - ((dt.getDay() + 6) % 7));
  return dayKey(monday.getTime());
};

export const today = (s: SaveV1) => s.days[dayKey()] ?? { quizzes: 0, min: 0, correct: 0, total: 0 };

/**
 * A profile the server marks `unlimited` (the owner's "Admin" player; migration 002, profiles.unlimited) has no
 * limits: no time cap, no quiz cap, no tries per day, every tier open. pin-login returns the flag and the login page
 * stores it in kv `profile-unlimited`; no name check, so a family cannot get it by naming a child "Admin".
 * `flag` is injectable for tests.
 */
let adminCache: boolean | undefined;
export const isUnlimited = (flag?: boolean) => {
  if (flag !== undefined) return flag;
  // Read once per page load. Login and logout both navigate, so the page reloads and the cache is fresh.
  return (adminCache ??= kv.get('profile-unlimited') === '1');
};
/** Tests only: forget the cached flag. */
export const resetUnlimitedCache = () => { adminCache = undefined; };

/** Time cap: today's minutes have reached the parent's daily limit. Daily Review is blocked too. */
export const capReached = (s: SaveV1) => !isUnlimited() && today(s).min >= s.settings.dailyCapMin;

/** Quizzes started today that count toward the quiz cap: tier quizzes (started or finished) and WA/SA papers.
 *  Daily Review never counts, and retests inside a tier quiz do not change the count. */
export const quizzesToday = (s: SaveV1) =>
  s.attempts.filter((a) => (a.mode === 'tier' || a.mode === 'paper') && dayKey(a.ts) === dayKey()).length;
export const quizCapReached = (s: SaveV1, on = QUIZ_CAP_ON) => on && !isUnlimited() && quizzesToday(s) >= DAILY_QUIZ_CAP;

/** Why a quiz of this mode cannot start now, or null. Review is exempt from the quiz cap only. */
export function dayBlock(s: SaveV1, mode: Attempt['mode'], quizCap = QUIZ_CAP_ON): 'time' | 'quizzes' | null {
  if (capReached(s)) return 'time';
  if (mode !== 'review' && quizCapReached(s, quizCap)) return 'quizzes';
  return null;
}
export const blockMessage = (r: 'time' | 'quizzes') =>
  r === 'time' ? "Done for today! You have reached today's training time. Come back tomorrow."
    : `${DAILY_QUIZ_CAP} quizzes done today. Daily Review is still open.`;
export const goalMet = (s: SaveV1) => today(s).quizzes >= s.settings.dailyGoalQuizzes;

/** Goal-met days (YYYY-MM-DD), judged against the current daily goal. */
// a day keeps the goal it met at the time; days saved before `goal` existed are judged by quiz count
const goalDays = (s: SaveV1) =>
  Object.entries(s.days).filter(([, d]) => d.goal ?? d.quizzes >= s.settings.dailyGoalQuizzes).map(([k]) => k);

/**
 * Weekly streak: consecutive weeks (Monday start) with at least 4 goal days. The week in progress
 * adds one once it reaches 4, and never breaks the streak while it is still going, so weekends
 * and rest days are safe.
 */
export function liveStreak(s: SaveV1, now = Date.now()) {
  const perWeek = new Map<string, number>();
  for (const d of goalDays(s)) perWeek.set(weekId(d), (perWeek.get(weekId(d)) ?? 0) + 1);
  const thisWeek = weekId(dayKey(now));
  let n = (perWeek.get(thisWeek) ?? 0) >= WEEK_GOAL_DAYS ? 1 : 0;
  for (let w = shiftDay(thisWeek, -7); (perWeek.get(w) ?? 0) >= WEEK_GOAL_DAYS; w = shiftDay(w, -7)) n++;
  return n;
}

// ---------------------------------------------------------------- questions

/** Spaced retest: a new question answered correctly retires at once; a wrong one is due in 1 day,
 *  then 3, then 7; correct at the 7-day step retires it; wrong at any step goes back to 1 day.
 *  A correct answer to a retest that is not yet due changes nothing (no progress, no penalty), so
 *  the spacing cannot be skipped by repeating questions on the same day. */
/** Record one answer. `picked` is the option text chosen on a wrong answer; omitted = not answered because time ran
 *  out (stored as ''); LEFT_BLANK = a paper question left blank on purpose. Returns true when a due retest step was
 *  passed (1 Crumb each at the finish). */
/** `short` (ADR 0011, a past-paper question of a one-pool sub-topic): a wrong answer comes back after 1 day, and a correct
 *  answer at that due retest retires it (counts toward the milestones); no 3- and 7-day steps. */
export function answer(s: SaveV1, id: string, ok: boolean, now = Date.now(), retireNew = true, picked?: string, short = false): boolean {
  const q = s.questions[id];
  if (ok && !q && !retireNew) return false; // practice papers never drain tier pools
  if (q?.parked) delete q.parked; // the question exists after all: answering always unparks
  const a = ok ? q?.a : (picked ?? '').slice(0, PICK_MAX);
  const keep = a != null ? { a } : {};
  if (!ok) {
    s.questions[id] = { s: 1, due: now + DAY, w: (q?.w ?? 0) + 1, ...keep };
  } else if (!q) {
    s.questions[id] = { s: 0, due: 0, w: 0 };
  } else if (q.s > 0 && q.due <= now) {
    if (q.s === 3 || short) s.questions[id] = { s: 0, due: 0, w: q.w, ...keep };
    else {
      const next = (q.s + 1) as 2 | 3;
      s.questions[id] = { s: next, due: now + STEP_DAYS[next] * DAY, w: q.w, ...keep };
    }
    return true; // a due retest step passed (the caller counts these for Crumbs)
  }
  return false;
}

export const isNew = (s: SaveV1, id: string) => !s.questions[id];
/** A retest that is due now. Parked states (id in no bank at the last Daily Review) are skipped unless the caller
 *  already knows the id is in a bank (`ignoreParked`). */
export const isDue = (s: SaveV1, id: string, now = Date.now(), ignoreParked = false) => {
  const q = s.questions[id];
  return !!q && (ignoreParked || !q.parked) && q.s > 0 && q.due <= now;
};
/** The questions of the parent's revision test not yet answered since it was sent: sending sets due to the send time and
 *  any answer moves due later, so an answered question leaves the test for good (its later retests are ordinary ones). */
export const revisionDue = (s: SaveV1, now = Date.now()) =>
  // a parked one (its question is in no bank: Daily Review set it aside) is left out, so the button never promises it
  (s.revision?.ids ?? []).filter((id) => isDue(s, id, now) && s.questions[id].due <= s.revision!.ts);

/**
 * Keep the `parked` flags in step with the banks a page has loaded. Every parked state whose id is in `ids` is
 * unparked. Only when `complete` (the ids of every bank: Daily Review) is a retest state whose id is missing parked;
 * nothing is ever deleted (ADR 0002). Retired states are never parked (they are never counted as due). Reversible:
 * an older build missing newer bank files may park live states, and the next complete call in a newer build unparks
 * them. Returns true when anything changed (the caller saves).
 */
export function syncParked(s: SaveV1, ids: Iterable<string>, complete: boolean, banks?: string): boolean {
  const present = new Set(ids);
  const mark = banks || true; // the bank set that confirmed the id is missing
  let changed = false;
  for (const [id, q] of Object.entries(s.questions)) {
    if (present.has(id)) {
      if (q.parked) { delete q.parked; changed = true; }
    } else if (complete && q.s > 0 && q.parked !== mark) {
      q.parked = mark; // parked, or re-marked as checked by this bank set
      changed = true;
    }
  }
  return changed;
}

/**
 * Retests due now for the Daily Review gates (the /train/ button, the school page): every due retest state except those
 * parked by this very bank set (`banks`, train.ts banksHash). A state parked by an older tab or build may be live, so it
 * counts until a Daily Review here re-checks it (syncParked with `banks`), which unparks it or re-marks it. Without this
 * an old tab could park live retests and hide the only page that unparks them.
 */
export const reviewDueCount = (s: SaveV1, now = Date.now(), banks?: string) =>
  Object.values(s.questions).filter((q) => inReview(q, banks) && q.due <= now).length;
/** A retest state that belongs in review lists (the child's gates, the parent's retest queue): not retired, and not
 * parked by this very bank set. */
export const inReview = (q: QState, banks?: string) => q.s > 0 && (!q.parked || q.parked !== banks);

/**
 * syncParked against the save as stored NOW, then save. Pages call this after awaiting bank files instead of saving the
 * copy they loaded before the await, which would overwrite a purchase or award made in another tab meanwhile.
 * Returns the stored save.
 */
export function syncParkedStored(ids: Iterable<string>, complete: boolean, banks?: string): SaveV1 {
  const s = load();
  if (syncParked(s, ids, complete, banks)) save(s);
  return s;
}
export const isRetired = (s: SaveV1, id: string) => s.questions[id]?.s === 0;

// ---------------------------------------------------------------- tiers

export const tierState = (s: SaveV1, sub: string, t: Tier): TierState =>
  s.progress[sub]?.[t] ?? { passes: [], scores: [], best: 0, cleared: false };

/** A tier opens when the tier below is cleared. Tiers with too few questions to play are skipped,
 *  so a tier is never locked behind one that cannot be cleared. Pass `playable` when known. */
export function tierOpen(s: SaveV1, sub: string, t: Tier, playable?: Record<Tier, boolean>): boolean {
  if (isUnlimited()) return true; // Admin test account: every tier is open (playability is checked by the callers)
  for (let i = TIERS.indexOf(t) - 1; i >= 0; i--) {
    const lower = TIERS[i];
    if (playable && !playable[lower]) continue;
    return tierState(s, sub, lower).cleared;
  }
  return true;
}

export const attemptsLeft = (s: SaveV1, sub: string, t?: Tier) =>
  isUnlimited() ? Infinity : Math.max(0, triesPerDay(sub) - attemptsToday(s, sub, t));
/** True when no more tries are allowed at this tier today (never for Admin). */
export const triesUsedUp = (s: SaveV1, sub: string, t?: Tier) => !isUnlimited() && attemptsToday(s, sub, t) >= triesPerDay(sub);
/** Tries today at this tier; with no tier (a one-pool sub-topic, ADR 0011) every try at the sub-topic today. */
export const attemptsToday = (s: SaveV1, sub: string, t?: Tier) =>
  s.attempts.filter((a) => a.mode === 'tier' && a.sub === sub && (t === undefined || a.tier === t) && dayKey(a.ts) === dayKey()).length;

/** Record a tier quiz or practice paper as started, so walking away still uses one of the daily tries
 *  (tier) and counts toward the daily quiz cap (tier and paper). */
export function openAttempt(
  s: SaveV1, a: { mode?: 'tier' | 'paper'; sub?: string; tier?: Tier; total: number }, now = Date.now(),
) {
  s.attempts.push({ ts: now, mode: a.mode ?? 'tier', sub: a.sub, tier: a.tier, score: 0, total: a.total, ms: 0, tags: [], open: true });
}
/**
 * Start a quiz: re-checks the daily block (the page may have sat open past the cap) and, for tier quizzes and
 * papers, records the open attempt. Returns the block reason and records nothing when blocked.
 */
export function beginQuiz(
  s: SaveV1, mode: Attempt['mode'], a: { sub?: string; tier?: Tier; total: number }, now = Date.now(),
): 'time' | 'quizzes' | null {
  const b = dayBlock(s, mode);
  if (b) return b;
  if (mode === 'tier' || mode === 'paper') openAttempt(s, { mode, ...a }, now);
  return null;
}
/** A paper's open record is matched by its own start time (the paper draft's ts), never by mode alone. */
export function closeOpenPaper(s: SaveV1, ts: number) {
  const i = s.attempts.findIndex((x) => x.open && x.mode === 'paper' && x.ts === ts);
  if (i >= 0) s.attempts.splice(i, 1);
}
/** No paper runs longer than about 2 hours, so an open paper record over 2 days old is one abandoned without its draft
 *  being discarded (e.g. on another device whose draft was lost). Removing it cannot touch a paper still running. */
export const STALE_PAPER_MS = 2 * DAY;
export function closeStalePapers(s: SaveV1, now = Date.now()) {
  s.attempts = s.attempts.filter((a) => !(a.open && a.mode === 'paper' && now - a.ts > STALE_PAPER_MS));
}
const dropOpen = (s: SaveV1, mode: Attempt['mode'], sub?: string, tier?: Tier, openTs?: number) => {
  if (mode === 'paper' && openTs !== undefined) return closeOpenPaper(s, openTs);
  const i = s.attempts.findLastIndex((x) => x.open && x.mode === mode && x.sub === sub && x.tier === tier);
  if (i >= 0) s.attempts.splice(i, 1);
};

export const minutesFor = (s: SaveV1, t: Tier) => TIER_MIN[t] * (s.settings.extraTime ? 1.5 : 1);

/** A card given for a cleared tier. dup: a star on an owned card instead (then `crumbs` is the bonus that came with it);
 * replaces: the slot's own card, already owned, when a replacement card was given. */
export type Reward = { slug: string; dup: boolean; stars: number; replaces?: string; crumbs?: number };
export interface QuizResult {
  passed: boolean;
  cleared: boolean;
  reward: Reward | null;
  /** Crumbs earned by this call (quiz band, retests, goal, streak week, bonuses). */
  crumbs: number;
  goalJustMet: boolean;
  /** Basic cleared at once by a perfect first-ever Basic quiz on this sub-topic. */
  autoPromoted?: boolean;
  newlyCleared: { sub: string; tier: Tier; reward: QuizResult['reward']; again?: true }[]; // again: a pool milestone on a slot already cleared (paid before)
  /** Achievement-only cards this call gave (needs opts.eco): Super Epic per completed topic, Legendary per paper. */
  achieved?: { kind: 'super-epic' | 'legendary'; topic?: string; subject?: string; reward: Reward }[];
}

/**
 * Record a finished quiz (answer() has already been called for each question). A tier quiz scoring >= 80%
 * on a full 10 is still logged as a pass, but only for display. A tier is cleared when every one of its
 * questions is retired (mastered): `tierIds` maps "sub|tier" to that tier's question ids, which the quiz
 * page knows and store.ts does not. syncTiers() then marks tiers cleared and awards the fixed card (a
 * duplicate adds a star, max 5). `cleared`/`reward` describe the quiz's own tier; `newlyCleared` lists
 * every tier this call cleared (a Daily Review can retire the last question of another tier).
 */
export function finishQuiz(
  s: SaveV1,
  a: Omit<Attempt, 'ts'>,
  rewardFor: RewardFor,
  now = Date.now(),
  tierIds: Record<string, string[]> = {},
  openTs?: number, // a paper: the start time of its open record (removed exactly; other papers' records stay)
  opts: FinishOpts = {},
): QuizResult {
  const key = dayKey(now);
  const test = opts.test ?? isUnlimited();
  const earned0 = s.crumbs?.earned ?? 0;
  const wasMet = (s.days[key]?.quizzes ?? 0) >= s.settings.dailyGoalQuizzes;
  if (a.mode === 'tier' || a.mode === 'paper') dropOpen(s, a.mode, a.sub, a.tier, openTs);
  // "First" = no other attempt for this sub|tier at all (Basic and Intermediate only), finished OR abandoned (this quiz's own open record
  // was dropped above). Counting abandoned tries closes the "quit after a mistake, retry until perfect" loophole.
  const firstEver = a.mode === 'tier' && (a.tier === 'b' || a.tier === 'i') && !!a.sub && !s.attempts.some((x) => x.mode === 'tier' && x.sub === a.sub && x.tier === a.tier);
  s.attempts.push({ ...a, ts: now });
  const d = (s.days[key] ??= { quizzes: 0, min: 0, correct: 0, total: 0 });
  d.quizzes++;
  d.ms = (d.ms ?? d.min * 60000) + a.ms; // keep milliseconds so short quizzes still count toward the cap
  d.min = Math.round(d.ms / 60000);
  d.correct += a.score;
  d.total += a.total;

  let passed = false, cleared = false, reward: QuizResult['reward'] = null;
  if (a.mode === 'tier' && a.sub && !a.tier && a.total) { // a one-pool quiz: practice keeps the sub-topic's cards strong
    const pct = a.score / a.total;
    for (const card of Object.values(s.cards)) if (card.srcSub === a.sub) { card.acc = Math.round(0.7 * card.acc + 0.3 * pct * 100); card.last = now; }
  }
  if (a.mode === 'tier' && a.sub && a.tier) {
    const st = tierState(s, a.sub, a.tier);
    const pct = a.total ? a.score / a.total : 0;
    st.best = Math.max(st.best, Math.round(pct * 100));
    passed = a.total >= QUIZ_SIZE && pct >= PASS;
    const slug = slotCard(s, a.sub, a.tier), card = slug ? s.cards[slug] : undefined;
    if (card && a.total) { card.acc = Math.round(0.7 * card.acc + 0.3 * pct * 100); card.last = now; } // practice keeps cards strong
    if (passed) {
      st.scores.push(Math.round(pct * 100));
      if (!st.passes.includes(key)) st.passes.push(key);
    }
    (s.progress[a.sub] ??= {})[a.tier] = st;
  }
  const early: QuizResult['newlyCleared'] = [];
  let autoPromoted = false;
  if (firstEver && a.tier && a.sub && a.total >= QUIZ_SIZE && a.score === a.total && !tierState(s, a.sub, a.tier).cleared) {
    // owner's rule: a perfect first Basic or Intermediate quiz clears that tier now (before syncTiers, so the next tier opens)
    early.push({ sub: a.sub, tier: a.tier, reward: award(s, a.sub, a.tier, rewardFor, now, opts.eco, test) });
    autoPromoted = true;
  }
  // Crumbs for finishing (never for an abandoned quiz: that never reaches finishQuiz); bonuses come with the clears below
  earn(s, quizCrumbs(a.score, a.total, a.mode), a.mode === 'tier' ? 'quiz' : a.mode, now,
    { test, note: a.mode === 'tier' ? `${a.sub}|${a.tier ?? 'pool'}` : a.mode === 'paper' ? (a.topics ?? []).join(',').slice(0, 120) : undefined });
  earn(s, (opts.retests ?? 0) * RETEST_CRUMBS, 'retest', now, { test });
  const newlyCleared = [...early, ...syncTiers(s, tierIds, rewardFor, now, opts.eco, test),
    ...syncMilestones(s, opts.pools ?? {}, rewardFor, now, opts.eco, test)];
  const mine = newlyCleared.filter((x) => x.sub === a.sub && (a.tier ? x.tier === a.tier : !!opts.pools?.[x.sub])).reverse();
  const own = mine.find((x) => !x.again); // a pool milestone on a slot paid before is announced, but is not this quiz's clear
  if (own) { cleared = true; reward = own.reward; }

  const goalJustMet = !wasMet && d.quizzes >= s.settings.dailyGoalQuizzes;
  if (d.quizzes >= s.settings.dailyGoalQuizzes) d.goal = true;
  if (goalJustMet) {
    bumpStreak(s, now);
    const c = crumbsOf(s);
    if (c.goalDay !== key) { c.goalDay = key; earn(s, GOAL_CRUMBS, 'goal', now, { test }); }
    const wk = weekId(key);
    if (c.week !== wk && goalDays(s).filter((d) => weekId(d) === wk).length >= WEEK_GOAL_DAYS) {
      c.week = wk;
      earn(s, WEEK_CRUMBS, 'week', now, { test });
    }
  }
  const achieved = opts.eco ? achievements(s, a, opts.eco, now, test, opts.paperTopics) : [];
  return { passed, cleared, reward, crumbs: (s.crumbs?.earned ?? 0) - earned0, goalJustMet, autoPromoted, newlyCleared, achieved };
}

/**
 * Achievement-only cards (owner's answer 5a), checked at the end of every finished quiz, so a topic completed earlier is
 * picked up by the next quiz. Super Epic: once per competency topic in eco.topics, when all its sub-topics have the
 * Competent tier cleared. Legendary: once per subject in eco.subjects the same way, or a WA/SA paper of
 * LEGENDARY_MIN_QUESTIONS+ questions whose questions come from LEGENDARY_MIN_TOPICS+ topics (opts.paperTopics) at
 * AL1-AL2, at most one paper Legendary per
 * calendar week (later papers that week earn their Crumbs only). Each gives crumbs.ts achievementPreview(): the next
 * unowned card of the rarity, else a star and a Crumbs bonus.
 */
function achievements(s: SaveV1, a: Omit<Attempt, 'ts'>, eco: Economy, now: number, test: boolean, paperTopics: string[] = []): NonNullable<QuizResult['achieved']> {
  const out: NonNullable<QuizResult['achieved']> = [];
  for (const [topic, list] of Object.entries(eco.topics ?? {})) {
    if (!list.length || s.crumbs?.topics?.includes(topic) || !list.every((sub) => tierState(s, sub, 'c').cleared)) continue;
    const reward = giveAchievement(s, achievementPreview(s, 'super-epic', eco), `topic:${topic}`, 100, now, test);
    if (!reward) continue;
    (crumbsOf(s).topics ??= []).push(topic);
    out.push({ kind: 'super-epic', topic, reward });
  }
  for (const [subject, list] of Object.entries(eco.subjects ?? {})) {
    if (!list.length || s.crumbs?.subjects?.includes(subject) || !list.every((sub) => tierState(s, sub, 'c').cleared)) continue;
    const reward = giveAchievement(s, achievementPreview(s, 'legendary', eco), `subject:${subject}`, 100, now, test);
    if (!reward) continue;
    (crumbsOf(s).subjects ??= []).push(subject);
    out.push({ kind: 'legendary', subject, reward });
  }
  const week = weekId(dayKey(now));
  if (a.mode === 'paper' && a.total >= LEGENDARY_MIN_QUESTIONS && new Set(paperTopics).size >= LEGENDARY_MIN_TOPICS
    && alBand(a.score, a.total) <= LEGENDARY_MAX_BAND && s.crumbs?.legWeek !== week) {
    const reward = giveAchievement(s, achievementPreview(s, 'legendary', eco), 'paper', Math.round((100 * a.score) / a.total), now, test);
    if (reward) { crumbsOf(s).legWeek = week; out.push({ kind: 'legendary', reward }); }
  }
  return out;
}

function giveAchievement(s: SaveV1, p: Preview | null, src: string, acc: number, now: number, test: boolean): Reward | null {
  if (!p) return null;
  if (p.kind === 'card') {
    s.cards[p.slug] = { stars: 1, srcSub: src, srcTier: 'c', acc, last: now };
    return { slug: p.slug, dup: false, stars: 1 };
  }
  const card = s.cards[p.slug];
  card.stars = Math.min(5, card.stars + 1);
  earn(s, p.crumbs, 'bonus', now, { test, slug: p.slug, note: src });
  return { slug: p.slug, dup: true, stars: card.stars, crumbs: p.crumbs };
}

/**
 * Count mastered (retired) questions for each tier in `tierIds` ("sub|tier" -> ids), store the count, and
 * clear a tier whose questions are all retired, awarding its card. A cleared tier is never un-cleared, even
 * if a question later slips back to retest. Returns the tiers cleared by this call.
 */
export function syncTiers(
  s: SaveV1, tierIds: Record<string, string[]>, rewardFor: RewardFor, now = Date.now(), eco?: Economy, test = false,
): QuizResult['newlyCleared'] {
  const out: QuizResult['newlyCleared'] = [];
  const entries = Object.entries(tierIds)
    .map(([key, ids]) => { const [sub, tier] = key.split('|') as [string, Tier]; return { sub, tier, ids }; })
    .filter((e) => e.ids.length && TIERS.includes(e.tier))
    .sort((a, b) => TIERS.indexOf(a.tier) - TIERS.indexOf(b.tier)); // b, i, c: clearing Basic can open Intermediate in the same pass
  const playable = (sub: string): Record<Tier, boolean> => ({
    b: !!tierIds[`${sub}|b`]?.length, i: !!tierIds[`${sub}|i`]?.length, c: !!tierIds[`${sub}|c`]?.length,
  });
  for (const { sub, tier, ids } of entries) {
    const st = tierState(s, sub, tier);
    st.total = ids.length;
    st.mastered = ids.filter((id) => isRetired(s, id)).length;
    st.hash = tierHash(ids);
    delete st.pool; // these are tier counts now (a sub-topic back in tiers): never read them as past-paper counts
    (s.progress[sub] ??= {})[tier] = st;
    if (!st.cleared && st.mastered === st.total && tierOpen(s, sub, tier, playable(sub)))
      out.push({ sub, tier, reward: award(s, sub, tier, rewardFor, now, eco, test) });
  }
  return out;
}

/** Milestones of a one-pool sub-topic with n past-paper questions (ADR 0011, owner 21 Nov 2026): a sixth, a third, and a
 *  majority (over half) = competency, the "Exam-ready" badge. Milestone k uses the sub-topic's k-th card slot (b, i, c). */
export const milestoneAt = (n: number): [number, number, number] => [Math.ceil(n / 6), Math.ceil(n / 3), Math.floor(n / 2) + 1];
export const MILESTONE_NAME: Record<Tier, string> = { b: 'Milestone 1', i: 'Milestone 2', c: 'Exam-ready' };

/**
 * One-pool sub-topics ("sub" -> its past-paper question ids, never generated ones): count the retired (counted) ones,
 * store the count on each milestone slot, and reach every milestone whose threshold the count meets, awarding its card.
 * A milestone once reached is never taken away (the pool can grow later). Returns the milestones reached by this call.
 */
export function syncMilestones(
  s: SaveV1, pools: Record<string, string[]>, rewardFor: RewardFor, now = Date.now(), eco?: Economy, test = false,
): QuizResult['newlyCleared'] {
  const out: QuizResult['newlyCleared'] = [];
  for (const [sub, ids] of Object.entries(pools)) {
    if (ids.length < MIN_POOL) continue; // a sub-topic switches to one pool only at 20 past-paper questions
    const at = milestoneAt(ids.length);
    const mastered = ids.filter((id) => isRetired(s, id)).length;
    const hash = tierHash(ids);
    TIERS.forEach((t, k) => {
      const st = tierState(s, sub, t);
      st.total = ids.length; st.mastered = mastered; st.hash = hash; st.pool = true;
      (s.progress[sub] ??= {})[t] = st;
      // a generated tier cleared before the switch keeps its clear and card, but the milestone is earned on the pool; a slot
      // already cleared (that old tier, or a milestone the first one-pool build awarded without the marker) is announced with
      // no second reward (the pool page previews it as already earned). A sub-topic back in tiers keeps its clears (a clear
      // is never taken away) and ms (reached stays reached); syncTiers drops `pool`, so tier counts never read as pool counts
      if (!st.ms && mastered >= at[k]) {
        st.ms = true;
        out.push(st.cleared ? { sub, tier: t, reward: null, again: true } : { sub, tier: t, reward: award(s, sub, t, rewardFor, now, eco, test) });
      }
    });
  }
  return out;
}

/** One-pool progress: only what syncMilestones stored; a count left by the replaced generated tiers reads as 0. */
export function poolProgress(s: SaveV1, sub: string): { counted: number; total?: number } {
  const st = tierState(s, sub, 'b');
  return st.pool ? { counted: st.mastered ?? 0, total: st.total } : { counted: 0 };
}
/** The card a (sub-topic, slot) clear gave: its slot card or a replacement; undefined when it paid a star or nothing. */
export const slotCard = (s: SaveV1, sub: string, t: Tier) =>
  Object.entries(s.cards).find(([, c]) => c.srcSub === sub && c.srcTier === t)?.[0];
/** A milestone reached on the pool, not a generated tier cleared before the switch. */
export const milestoneReached = (s: SaveV1, sub: string, t: Tier) => !!tierState(s, sub, t).ms;

type RewardFor = (sub: string, t: Tier) => { slug: string; dup: boolean } | undefined;
/** eco: build-time card data (crumbs.ts Economy); without it a tier clear gives only its slot card or a star, as before
 * the economy. retests: retest steps passed in this quiz (answer() returned true). test: the unlimited test account
 * (defaults to isUnlimited()); its Crumbs are flagged. paperTopics: a paper's question topics, one per question asked
 * (the Legendary counts distinct ones; the topics the child picked may not all have been drawn). */
export type FinishOpts = { eco?: Economy; retests?: number; test?: boolean; paperTopics?: string[]; pools?: Record<string, string[]> };
export const RETEST_CRUMBS = 1, GOAL_CRUMBS = 3, WEEK_CRUMBS = 10;

/**
 * Mark a tier cleared and give its card. With `eco` (the economy): the slot card if not owned, else the next unowned card
 * of its rarity (a replacement), else a star on the slot card (max 5) plus a Crumbs bonus: crumbs.ts rewardPreview(),
 * which the tier page shows. Without `eco`, an owned card gains a star.
 */
function award(s: SaveV1, sub: string, t: Tier, rewardFor: RewardFor, now = Date.now(), eco?: Economy, test = false): QuizResult['reward'] {
  const st = tierState(s, sub, t);
  st.cleared = true;
  (s.progress[sub] ??= {})[t] = st;
  const r = rewardFor(sub, t);
  if (!r) return null;
  const top2 = [...st.scores].sort((x, y) => y - x).slice(0, 2);
  const acc = top2.length ? Math.round(top2.reduce((x, y) => x + y, 0) / top2.length) : st.best || 100;
  if (eco) {
    const p = rewardPreview(s, r.slug, eco);
    if (p.kind === 'card') {
      s.cards[p.slug] = { stars: 1, srcSub: sub, srcTier: t, acc, last: now };
      return { slug: p.slug, dup: false, stars: 1, ...(p.replaces ? { replaces: p.replaces } : {}) };
    }
    const owned = s.cards[p.slug];
    owned.stars = Math.min(5, owned.stars + 1);
    earn(s, p.crumbs, 'bonus', now, { test, slug: p.slug, note: `${sub}|${t}` });
    return { slug: p.slug, dup: true, stars: owned.stars, crumbs: p.crumbs };
  }
  const card = s.cards[r.slug];
  if (card) card.stars = Math.min(5, card.stars + 1);
  else s.cards[r.slug] = { stars: 1, srcSub: sub, srcTier: t, acc, last: now };
  return { slug: r.slug, dup: !!card, stars: s.cards[r.slug].stars };
}

function bumpStreak(s: SaveV1, now: number) {
  const st = s.streak;
  st.studyDays++;
  st.lastDay = dayKey(now);
  st.current = liveStreak(s, now);
  st.best = Math.max(st.best, st.current);
}

/**
 * Card power = retention x star bonus, capped at 100. acc follows later quiz scores on the tier that
 * earned the card; a card not practised for 3 weeks loses 5 power a week (never below 40), so power
 * says how well the topic is remembered now, not how it went once.
 */
export function power(c: { acc: number; stars: number; last?: number }, now = Date.now()) {
  const idleWeeks = c.last ? Math.max(0, Math.floor((now - c.last) / (7 * DAY)) - 3) : 0;
  const base = Math.max(40, c.acc - 5 * idleWeeks);
  return Math.min(100, Math.round(base * (1 + 0.05 * (c.stars - 1))));
}

/**
 * Buy a card or a star in the shop (crumbs.ts buyCard/buyStar). It reads the stored save itself, checks, charges and
 * saves in one synchronous step, never a page's in-memory copy: a second tab, or a double click, sees the first
 * purchase and is refused ('owned', 'stale' or 'poor') instead of spending twice. `from` is the star count the page
 * showed (stars only).
 */
export function purchase(kind: 'card' | 'star', slug: string, from: number, eco: Economy, now = Date.now()): BuyResult {
  const s = load();
  const r = kind === 'card' ? buyCard(s, slug, eco, now, isUnlimited()) : buyStar(s, slug, from, eco, now, isUnlimited());
  if (r.ok) save(s);
  return r;
}

/** The reward a tier gives right now: a star if the card is already owned, else the new card. */
export const actualReward = (s: SaveV1, slug: string) => (s.cards[slug] ? 'star' : 'card');

// ---------------------------------------------------------------- save code

const b64url = (u: Uint8Array) => {
  let bin = '';
  for (let i = 0; i < u.length; i += 0x8000) bin += String.fromCharCode(...u.subarray(i, i + 0x8000)); // chunked: no stack overflow
  return btoa(bin).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
};
const unb64url = (t: string) => Uint8Array.from(atob(t.replace(/-/g, '+').replace(/_/g, '/')), (c) => c.charCodeAt(0));

async function pipe(data: Uint8Array, stream: CompressionStream | DecompressionStream) {
  const out = new Response(new Blob([data]).stream().pipeThrough(stream));
  return new Uint8Array(await out.arrayBuffer());
}

export async function exportCode(s: SaveV1) {
  const packed = await pipe(new TextEncoder().encode(JSON.stringify(s)), new CompressionStream('deflate'));
  return 'CCX1:' + b64url(packed);
}

export async function importCode(code: string): Promise<SaveV1> {
  const t = code.trim();
  if (!t.startsWith('CCX1:')) throw new Error('This is not a Cookie Codex save code.');
  const json = new TextDecoder().decode(await pipe(unb64url(t.slice(5)), new DecompressionStream('deflate')));
  let s = JSON.parse(json);
  if (typeof s?.schemaVersion !== 'number') throw new Error('The save code is damaged.');
  if (s.schemaVersion > SCHEMA) throw new Error('This save code comes from a newer version of the site.');
  if (s.schemaVersion < SCHEMA) s = migrate(s); // writes nothing; the caller backs up before replacing
  return normalise(s);
}
