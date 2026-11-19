// A save is written by the child's own browser and synced, so pages that SHOW a save (another child's, or whatever is on
// this device) must not trust its shape. cleanSave() returns a well-formed SaveV1 for display: every number is a finite
// number in range, every string a string, malformed entries dropped. It never writes storage and changes no save rules;
// store.ts load()/migrations stay as they are. Use it before rendering a save into HTML.
import { fresh, TIERS, PICK_MAX, type SaveV1, type Tier, type TierState, type Attempt } from './store.ts';

type Obj = Record<string, unknown>;
const obj = (v: unknown): Obj => (v && typeof v === 'object' && !Array.isArray(v) ? (v as Obj) : {});
const num = (v: unknown, lo = 0, hi = Number.MAX_SAFE_INTEGER) =>
  typeof v === 'number' && Number.isFinite(v) ? Math.min(hi, Math.max(lo, v)) : lo;
const str = (v: unknown, max = 200) => (typeof v === 'string' ? v.slice(0, max) : '');
const strOrNull = (v: unknown) => (typeof v === 'string' ? v.slice(0, 40) : null);
const strs = (v: unknown, max = 50) => (Array.isArray(v) ? v.filter((x): x is string => typeof x === 'string').slice(0, max).map((x) => x.slice(0, 120)) : []);
const tier = (v: unknown): Tier | undefined => (TIERS.includes(v as Tier) ? (v as Tier) : undefined);
const entries = (v: unknown, max = 200000) => Object.entries(obj(v)).slice(0, max);

function cleanTier(v: unknown): TierState | null {
  const t = obj(v);
  if (!Object.keys(t).length) return null;
  const out: TierState = {
    passes: strs(t.passes, 500).filter((x) => /^[\w:.-]{1,40}$/.test(x)), scores: Array.isArray(t.scores) ? t.scores.slice(0, 500).map((x) => num(x, 0, 100)) : [],
    best: num(t.best, 0, 100), cleared: t.cleared === true,
  };
  if (t.total !== undefined) out.total = num(t.total);
  if (t.mastered !== undefined) out.mastered = Math.min(num(t.mastered), out.total ?? Number.MAX_SAFE_INTEGER);
  return out;
}

function cleanAttempt(v: unknown): Attempt | null {
  const a = obj(v);
  if (!Object.keys(a).length) return null;
  const total = num(a.total, 0, 1000);
  const out: Attempt = {
    ts: num(a.ts), mode: a.mode === 'review' || a.mode === 'paper' ? a.mode : 'tier',
    score: Math.min(num(a.score, 0, 1000), total), total, ms: num(a.ms), tags: strs(a.tags, 100),
  };
  if (typeof a.sub === 'string') out.sub = str(a.sub, 120);
  const t = tier(a.tier); if (t) out.tier = t;
  if (Array.isArray(a.topics)) out.topics = strs(a.topics, 100);
  if (a.open === true) out.open = true;
  return out;
}

export function cleanSave(raw: unknown): SaveV1 {
  const r = obj(raw), f = fresh();
  const s: SaveV1 = { ...f, createdAt: num(r.createdAt) || f.createdAt };

  const st = obj(r.settings);
  s.settings = {
    dailyCapMin: typeof st.dailyCapMin === 'number' ? num(st.dailyCapMin, 15, 600) : f.settings.dailyCapMin,
    dailyGoalQuizzes: typeof st.dailyGoalQuizzes === 'number' ? num(st.dailyGoalQuizzes, 0, 100) : f.settings.dailyGoalQuizzes,
    extraTime: st.extraTime === true, psleDate: str(st.psleDate, 20) || f.settings.psleDate, playerName: str(st.playerName, 40),
  };

  for (const [sub, tiers] of entries(r.progress)) {
    const row: Partial<Record<Tier, TierState>> = {};
    for (const [t, v] of entries(tiers, 10)) { const k = tier(t), c = cleanTier(v); if (k && c) row[k] = c; }
    if (Object.keys(row).length) s.progress[sub.slice(0, 120)] = row;
  }

  for (const [id, v] of entries(r.questions)) {
    const q = obj(v);
    if (!Object.keys(q).length) continue;
    const step = [0, 1, 2, 3].includes(q.s as number) ? (q.s as 0 | 1 | 2 | 3) : 0;
    s.questions[id.slice(0, 120)] = { s: step, due: num(q.due), w: num(q.w, 0, 100000), ...(typeof q.a === 'string' ? { a: q.a.slice(0, PICK_MAX) } : {}) };
  }

  for (const [slug, v] of entries(r.cards)) {
    const c = obj(v);
    if (!Object.keys(c).length) continue;
    s.cards[slug.slice(0, 120)] = {
      stars: num(c.stars, 1, 99), srcSub: str(c.srcSub, 120), srcTier: tier(c.srcTier) ?? 'b', acc: num(c.acc, 0, 100),
      ...(c.last !== undefined ? { last: num(c.last) } : {}),
    };
  }

  s.attempts = (Array.isArray(r.attempts) ? r.attempts.slice(-200000) : []).map(cleanAttempt).filter((a): a is Attempt => a !== null);

  for (const [key, v] of entries(r.days, 4000)) {
    const d = obj(v);
    if (!Object.keys(d).length) continue;
    const total = num(d.total);
    s.days[key.slice(0, 20)] = {
      quizzes: num(d.quizzes, 0, 1000), min: num(d.min, 0, 1440), correct: Math.min(num(d.correct), total), total,
      ...(d.ms !== undefined ? { ms: num(d.ms) } : {}), ...(d.goal === true ? { goal: true } : {}),
    };
  }

  const k = obj(r.streak);
  s.streak = { current: num(k.current, 0, 10000), best: num(k.best, 0, 10000), lastDay: strOrNull(k.lastDay), freezeUsedWeek: strOrNull(k.freezeUsedWeek), studyDays: num(k.studyDays, 0, 100000) };

  const last = obj(r.last), lt = tier(last.tier);
  s.last = typeof last.sub === 'string' && lt ? { sub: str(last.sub, 120), tier: lt } : null;
  return s;
}
