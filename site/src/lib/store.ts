// Client-side save (docs/game-design.md section 8). Every page reads and writes progress
// through this module, so a backend can replace localStorage later.
export type School = 'math' | 'science' | 'english' | 'chinese';
export type Tier = 'b' | 'i' | 'c';
export const TIERS: Tier[] = ['b', 'i', 'c'];
export const TIER_NAME: Record<Tier, string> = { b: 'Basic', i: 'Intermediate', c: 'Competent' };

export type TierState = { passes: string[]; scores: number[]; best: number; cleared: boolean };
// s: 0 retired, 1-3 retest step (due in 1, 3, 7 days)
export type QState = { s: 0 | 1 | 2 | 3; due: number; w: number };
export interface Attempt {
  ts: number; mode: 'tier' | 'review' | 'paper'; sub?: string; tier?: Tier; topics?: string[];
  score: number; total: number; ms: number; tags: string[];
  open?: boolean; // started but not finished: still counts as a try
}
// The interface keeps its v1 name so imports stay unchanged; schemaVersion is now 2 (see `migrations`).
export interface SaveV1 {
  schemaVersion: 2;
  createdAt: number;
  settings: {
    pinHash: string | null; dailyCapMin: number; dailyGoalQuizzes: number;
    extraTime: boolean; psleDate: string; playerName: string;
  };
  progress: Record<string, Partial<Record<Tier, TierState>>>;
  questions: Record<string, QState>;
  cards: Record<string, { stars: number; srcSub: string; srcTier: Tier; acc: number; last?: number }>;
  attempts: Attempt[];
  days: Record<string, { quizzes: number; min: number; correct: number; total: number; ms?: number; goal?: boolean }>;
  streak: { current: number; best: number; lastDay: string | null; freezeUsedWeek: string | null; studyDays: number };
  last: { sub: string; tier: Tier } | null;
}

const KEY = 'ccx:save';
const BACKUP_KEY = 'ccx:backup'; // copy of a save taken just before a migration rewrites it
export const SCHEMA = 2;
const DAY = 86_400_000;
const STEP_DAYS = [0, 1, 3, 7];
export const TIER_MIN: Record<Tier, number> = { b: 12, i: 15, c: 20 };
export const PASS = 0.8;
export const QUIZ_SIZE = 10; // a pass needs a full 10-question quiz
export const WEEK_GOAL_DAYS = 4; // a streak week needs 4 goal days; rest days never break it
export const ATTEMPTS_PER_DAY = 3;

export const fresh = (): SaveV1 => ({
  schemaVersion: 2,
  createdAt: Date.now(),
  settings: { pinHash: null, dailyCapMin: 45, dailyGoalQuizzes: 2, extraTime: false, psleDate: '2027-09-30', playerName: 'Alyssa' },
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
    // Unreadable, unknown-version, newer-version or failed-migration save: keep the raw string in the
    // first free slot of ccx:failed:1..3, only if it differs from every stored copy, so a later save()
    // cannot destroy the only copy. When all 3 are full the 3 oldest stay and nothing is overwritten.
    // ccx:save and ccx:backup are left as they were.
    if (raw) {
      try {
        const have = FAILED_KEYS.map((k) => localStorage.getItem(k));
        if (!have.includes(raw)) {
          const free = have.findIndex((v) => v === null);
          if (free >= 0) localStorage.setItem(FAILED_KEYS[free], raw);
        }
      } catch { /* full or blocked */ }
    }
  }
  return fresh();
}

export function save(s: SaveV1) {
  try { localStorage.setItem(KEY, JSON.stringify(s)); } catch { /* full or blocked */ }
}

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
export const capReached = (s: SaveV1) => today(s).min >= s.settings.dailyCapMin;
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
 *  then 3, then 7; correct at the 7-day step retires it; wrong at any step goes back to 1 day. */
export function answer(s: SaveV1, id: string, ok: boolean, now = Date.now(), retireNew = true) {
  const q = s.questions[id];
  if (ok && !q && !retireNew) return; // practice papers never drain tier pools
  if (!ok) {
    s.questions[id] = { s: 1, due: now + DAY, w: (q?.w ?? 0) + 1 };
  } else if (!q || q.s === 3) {
    s.questions[id] = { s: 0, due: 0, w: q?.w ?? 0 };
  } else if (q.s > 0) {
    const next = (q.s + 1) as 2 | 3;
    s.questions[id] = { s: next, due: now + STEP_DAYS[next] * DAY, w: q.w };
  }
}

export const isNew = (s: SaveV1, id: string) => !s.questions[id];
export const isDue = (s: SaveV1, id: string, now = Date.now()) => {
  const q = s.questions[id];
  return !!q && q.s > 0 && q.due <= now;
};
export const isRetired = (s: SaveV1, id: string) => s.questions[id]?.s === 0;

// ---------------------------------------------------------------- tiers

export const tierState = (s: SaveV1, sub: string, t: Tier): TierState =>
  s.progress[sub]?.[t] ?? { passes: [], scores: [], best: 0, cleared: false };

/** A tier opens when the tier below is cleared. Tiers with too few questions to play are skipped,
 *  so a tier is never locked behind one that cannot be cleared. Pass `playable` when known. */
export function tierOpen(s: SaveV1, sub: string, t: Tier, playable?: Record<Tier, boolean>): boolean {
  for (let i = TIERS.indexOf(t) - 1; i >= 0; i--) {
    const lower = TIERS[i];
    if (playable && !playable[lower]) continue;
    return tierState(s, sub, lower).cleared;
  }
  return true;
}

export const attemptsToday = (s: SaveV1, sub: string, t: Tier) =>
  s.attempts.filter((a) => a.mode === 'tier' && a.sub === sub && a.tier === t && dayKey(a.ts) === dayKey()).length;

/** Record a tier quiz as started, so walking away still uses one of the 3 daily tries. */
export function openAttempt(s: SaveV1, a: { sub: string; tier: Tier; total: number }, now = Date.now()) {
  s.attempts.push({ ts: now, mode: 'tier', sub: a.sub, tier: a.tier, score: 0, total: a.total, ms: 0, tags: [], open: true });
}
const dropOpen = (s: SaveV1, sub?: string, tier?: Tier) => {
  const i = s.attempts.findLastIndex((x) => x.open && x.sub === sub && x.tier === tier);
  if (i >= 0) s.attempts.splice(i, 1);
};

export const minutesFor = (s: SaveV1, t: Tier) => TIER_MIN[t] * (s.settings.extraTime ? 1.5 : 1);

export interface QuizResult {
  passed: boolean;
  cleared: boolean;
  reward: { slug: string; dup: boolean; stars: number } | null;
  goalJustMet: boolean;
}

/**
 * Record a finished quiz. Tier quizzes: >= 80% is a pass; two passes on different days clear the
 * tier and award its fixed card (a duplicate adds a star, max 5). Review quizzes count toward the
 * daily goal but never toward a pass.
 */
export function finishQuiz(
  s: SaveV1,
  a: Omit<Attempt, 'ts'>,
  rewardFor: RewardFor,
  now = Date.now(),
): QuizResult {
  const key = dayKey(now);
  const wasMet = (s.days[key]?.quizzes ?? 0) >= s.settings.dailyGoalQuizzes;
  if (a.mode === 'tier') dropOpen(s, a.sub, a.tier);
  s.attempts.push({ ...a, ts: now });
  const d = (s.days[key] ??= { quizzes: 0, min: 0, correct: 0, total: 0 });
  d.quizzes++;
  d.ms = (d.ms ?? d.min * 60000) + a.ms; // keep milliseconds so short quizzes still count toward the cap
  d.min = Math.round(d.ms / 60000);
  d.correct += a.score;
  d.total += a.total;

  let passed = false, cleared = false, reward: QuizResult['reward'] = null;
  if (a.mode === 'tier' && a.sub && a.tier) {
    const st = tierState(s, a.sub, a.tier);
    const pct = a.total ? a.score / a.total : 0;
    st.best = Math.max(st.best, Math.round(pct * 100));
    passed = a.total >= QUIZ_SIZE && pct >= PASS;
    const card = Object.values(s.cards).find((c) => c.srcSub === a.sub && c.srcTier === a.tier);
    if (card && a.total) { card.acc = Math.round(0.7 * card.acc + 0.3 * pct * 100); card.last = now; } // practice keeps cards strong
    if (passed) {
      st.scores.push(Math.round(pct * 100));
      if (!st.passes.includes(key)) st.passes.push(key);
    }
    (s.progress[a.sub] ??= {})[a.tier] = st;
    if (!st.cleared && st.passes.length >= 2) {
      cleared = true;
      reward = award(s, a.sub, a.tier, rewardFor, now);
    }
  }

  const goalJustMet = !wasMet && d.quizzes >= s.settings.dailyGoalQuizzes;
  if (d.quizzes >= s.settings.dailyGoalQuizzes) d.goal = true;
  if (goalJustMet) bumpStreak(s, now);
  return { passed, cleared, reward, goalJustMet };
}

type RewardFor = (sub: string, t: Tier) => { slug: string; dup: boolean } | undefined;

/** Mark a tier cleared and give its fixed card; a card already owned gains a star (max 5). */
function award(s: SaveV1, sub: string, t: Tier, rewardFor: RewardFor, now = Date.now()): QuizResult['reward'] {
  const st = tierState(s, sub, t);
  st.cleared = true;
  (s.progress[sub] ??= {})[t] = st;
  const r = rewardFor(sub, t);
  if (!r) return null;
  const top2 = [...st.scores].sort((x, y) => y - x).slice(0, 2);
  const acc = top2.length ? Math.round(top2.reduce((x, y) => x + y, 0) / top2.length) : 100;
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

export async function hashPin(pin: string) {
  const h = await crypto.subtle.digest('SHA-256', new TextEncoder().encode('ccx:' + pin));
  return b64url(new Uint8Array(h));
}
