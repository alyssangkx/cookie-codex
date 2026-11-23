// A save is written by the child's own browser and synced, so pages that SHOW a save (another child's, or whatever is on
// this device) must not trust its shape. cleanSave() returns a well-formed SaveV1 for display: every number is a finite
// number in range, every string a string, malformed entries dropped. It never writes storage and changes no save rules;
// store.ts load()/migrations stay as they are. Use it before rendering a save into HTML.
import { fresh, TIERS, PICK_MAX, ASSIGN_HREF, ASSIGN_MAX, type SaveV1, type Tier, type TierState, type Attempt } from './store.ts';
import { CRUMB_WHYS, LEDGER_MAX, type Crumbs, type CrumbWhy, type LedgerEntry, type Purchase } from './crumbs.ts';

type Obj = Record<string, unknown>;
const obj = (v: unknown): Obj => (v && typeof v === 'object' && !Array.isArray(v) ? (v as Obj) : {});
const num = (v: unknown, lo = 0, hi = Number.MAX_SAFE_INTEGER) =>
  typeof v === 'number' && Number.isFinite(v) ? Math.min(hi, Math.max(lo, v)) : lo;
const str = (v: unknown, max = 200) => (typeof v === 'string' ? v.slice(0, max) : '');
const strOrNull = (v: unknown) => (typeof v === 'string' ? v.slice(0, 40) : null);
const strs = (v: unknown, max = 50) => (Array.isArray(v) ? v.filter((x): x is string => typeof x === 'string').slice(0, max).map((x) => x.slice(0, 120)) : []);
const tier = (v: unknown): Tier | undefined => (TIERS.includes(v as Tier) ? (v as Tier) : undefined);
// keys come from the save: obj['__proto__'] = x would set the prototype, every other key is a plain own property
const entries = (v: unknown, max = 200000) => Object.entries(obj(v)).filter(([k]) => k !== '__proto__').slice(0, max);

function cleanTier(v: unknown): TierState | null {
  const t = obj(v);
  if (!Object.keys(t).length) return null;
  const out: TierState = {
    passes: strs(t.passes, 500).filter((x) => /^[\w:.-]{1,40}$/.test(x)), scores: Array.isArray(t.scores) ? t.scores.slice(0, 500).map((x) => num(x, 0, 100)) : [],
    best: num(t.best, 0, 100), cleared: t.cleared === true,
  };
  if (t.total !== undefined) out.total = num(t.total);
  if (t.mastered !== undefined) out.mastered = Math.min(num(t.mastered), out.total ?? Number.MAX_SAFE_INTEGER);
  if (typeof t.hash === 'string' && /^[a-z0-9]{1,16}$/.test(t.hash)) out.hash = t.hash;
  if (t.pool === true) out.pool = true;
  if (t.ms === true) out.ms = true;
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

const day = (v: unknown) => (typeof v === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(v) ? v : undefined);
const COIN = 10_000_000; // no real balance gets near this

/** The optional Crumbs ledger (crumbs.ts). Kept field for field, so a save synced through the server keeps its coins. */
function cleanCrumbs(v: unknown): Crumbs {
  const c = obj(v);
  const log: LedgerEntry[] = (Array.isArray(c.log) ? c.log.slice(-LEDGER_MAX) : []).flatMap((x) => {
    const e = obj(x);
    if (!CRUMB_WHYS.includes(e.why as CrumbWhy)) return [];
    const out: LedgerEntry = { ts: num(e.ts), n: num(e.n, -COIN, COIN), bal: num(e.bal, 0, COIN), why: e.why as CrumbWhy };
    if (typeof e.slug === 'string') out.slug = str(e.slug, 120);
    if (typeof e.note === 'string') out.note = str(e.note, 120);
    if (e.test === true) out.test = true;
    return [out];
  });
  const buys: Purchase[] = (Array.isArray(c.buys) ? c.buys.slice(-5000) : []).flatMap((x) => {
    const b = obj(x);
    if (typeof b.slug !== 'string' || (b.kind !== 'card' && b.kind !== 'star')) return [];
    const out: Purchase = { ts: num(b.ts), slug: str(b.slug, 120), kind: b.kind, price: num(b.price, 0, COIN), stars: num(b.stars, 1, 99) };
    if (b.test === true) out.test = true;
    return [out];
  });
  const out: Crumbs = { bal: num(c.bal, 0, COIN), earned: num(c.earned, 0, COIN), spent: num(c.spent, 0, COIN), test: num(c.test, 0, COIN), log, buys };
  const g = day(c.goalDay), w = day(c.week);
  const lw = day(c.legWeek);
  if (g) out.goalDay = g;
  if (w) out.week = w;
  if (Array.isArray(c.topics)) out.topics = strs(c.topics, 1000);
  if (lw) out.legWeek = lw;
  if (Array.isArray(c.subjects)) out.subjects = strs(c.subjects, 20);
  return out;
}

export function cleanSave(raw: unknown): SaveV1 {
  const r = obj(raw), f = fresh();
  const s: SaveV1 = { ...f, createdAt: num(r.createdAt) || f.createdAt };

  const st = obj(r.settings);
  s.settings = {
    // settings stay as the game sees them (only made finite), so the parent page never shows or writes back a value the
    // game does not use; the parent controls apply their own ranges on change
    dailyCapMin: typeof st.dailyCapMin === 'number' ? num(st.dailyCapMin, 0, 1440) : f.settings.dailyCapMin,
    dailyGoalQuizzes: typeof st.dailyGoalQuizzes === 'number' ? num(st.dailyGoalQuizzes, 0, 1000) : f.settings.dailyGoalQuizzes,
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
    s.questions[id.slice(0, 120)] = { s: step, due: num(q.due), w: num(q.w, 0, 100000), ...(typeof q.a === 'string' ? { a: q.a.slice(0, PICK_MAX) } : {}), ...(q.parked === true ? { parked: true as const } : typeof q.parked === 'string' && /^[a-z0-9]{1,16}$/.test(q.parked) ? { parked: q.parked } : {}) };
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
  if (r.crumbs !== undefined) s.crumbs = cleanCrumbs(r.crumbs);
  const rv = obj(r.revision);
  // assignments: the link is only ever a sub-topic page (it is rendered as an href)
  if (Array.isArray(r.assigned)) s.assigned = r.assigned.map(obj)
    .filter((a: Obj) => typeof a.sub === 'string' && typeof a.href === 'string' && ASSIGN_HREF.test(a.href as string))
    .slice(0, ASSIGN_MAX).map((a: Obj) => ({ sub: str(a.sub, 120), name: str(a.name, 120), href: str(a.href, 160), ts: num(a.ts, 0, 1e15), base: num(a.base, 0, 1e9) }));
  if (Array.isArray(rv.ids)) s.revision = { ids: rv.ids.filter((x: unknown) => typeof x === 'string').slice(0, 10).map((x: string) => str(x, 40)), ts: num(rv.ts, 0, 1e15) };
  return s;
}
