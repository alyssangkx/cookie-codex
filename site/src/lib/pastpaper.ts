// Verbatim past-paper MCQs (ADR 0004). They reach the browser ONLY from Supabase, per quiz (ADR 0012): ids, sub-topic,
// level and rank through the pp_pool RPC (migration 006), then the text of the picked questions (at most 15 a call) and
// 10-minute signed picture URLs through the pp-serve function, under daily limits. Signed-in child or admin only. Never through the public /data/quiz endpoint, site/public or the static build. This module is pure (no
// I/O, no imports) so it can be tested; ppfetch.ts does the network calls. Everything is OFF until PP_ENABLED is true.
// Owner, 20 Nov 2026 (ADR 0004 amendment): checked past-paper items count like generated ones (mastery, tiers, cards,
// Crumbs); readable by children and the admin only; shown as "Past paper <year>" (never the school); left out of the
// parent page's wrong-answer list.
import { esc } from './boldans.ts';

/** Master switch. On since 20 Nov 2026 (004 applied, Plant transport uploaded and reviewed by the owner). */
export const PP_ENABLED = true;

/** merge: past-paper items join the generated ones; replace: they take over a tier once it has a full pool; pool (ADR
 * 0011): the sub-topic is one pool of its past-paper questions (20+), no tiers, milestones; generated questions leave it. */
export type PpMode = 'merge' | 'replace' | 'pool';

/** Per-sub-topic switch, added in the order the imports land (Plant transport first). Ignored while PP_ENABLED is false. */
export const PP_SWITCH: Readonly<Record<string, PpMode>> = {
  // Science upload, 21 Nov 2026 (owner OK): 1,250 questions 2018-2026; 'pool' at 20+ past-paper questions (ADR 0011),
  // 'merge' below that (they join the sub-topic's generated tiers)
  'sci-cycles-life-cycles-compare': 'pool',
  'sci-cycles-matter-states': 'pool',
  'sci-cycles-repro-cell': 'pool',
  'sci-cycles-repro-plants': 'pool',
  'sci-cycles-water-evaporation': 'pool',
  'sci-cycles-water-states': 'pool',
  'sci-diversity-living-classification': 'pool',
  'sci-diversity-materials-properties': 'pool',
  'sci-energy-conv-forms': 'pool',
  'sci-energy-heat-effects': 'pool',
  'sci-energy-light-seeing': 'pool',
  'sci-energy-photo-requirements': 'pool',
  'sci-interactions-env-adapt': 'pool',
  'sci-interactions-env-community': 'pool',
  'sci-interactions-env-survival': 'pool',
  'sci-interactions-forces-effects': 'pool',
  'sci-interactions-forces-investigate': 'pool',
  'sci-interactions-magnet-props': 'pool',
  'sci-systems-circuit': 'pool',
  'sci-systems-circuit-vars': 'pool',
  'sci-systems-digestive-parts': 'pool',
  'sci-systems-plant-parts-fn': 'pool', // 24 with the three-model / Claude+Perplexity verdicts (22 Nov 2026)
  'sci-systems-plant-transport-parts': 'pool',
  'sci-systems-resp-circ-parts': 'pool',
  'sci-cycles-repro-humans': 'pool', // 21 with the three-model / Claude+Perplexity verdicts (22 Nov 2026)
  'sci-cycles-water-cycle': 'merge',
  'sci-diversity-living-characteristics': 'pool', // 21 after the unsure-key confirms (23 Nov 2026)
  'sci-energy-heat-temp': 'pool', // 20 with the three-model / Claude+Perplexity verdicts (22 Nov 2026)
  'sci-energy-photo-respiration': 'merge',
  'sci-inquiry-predict-hyp': 'merge',
  'sci-systems-air-gases': 'merge',
  'sci-systems-human-overview': 'merge',
  // English upload (owner OK, 21 Nov 2026): single-sentence MCQs, paper questions 1-15 (grammar 1,926, vocabulary 969);
  // keys confirmed by the blind check or by owner-approved outside-model consensus
  'eng-grammar-mcq': 'pool',
  'eng-vocab-mcq': 'pool',
  // English visual text (passage phase, 21 Nov 2026): 396 questions in 97 sets, each set shown with its exam pages
  'eng-visual-text': 'pool',
  // Chinese upload (owner OK, 21 Nov 2026): single-item MCQs (a blank or pinyin options); keys confirmed by the blind check
  // or owner-approved outside-model consensus. Cloze, reading and dialogue wait for the passage phase.
  'chi-ciyu-choose': 'pool',
  'chi-pinyin-sound': 'pool',
  'chi-juzi-guanlian': 'pool',
  'chi-zixing-form': 'pool',
  'chi-juzi-choose': 'pool',
  'chi-ciyu-idiom': 'merge',
  // Chinese passage phase (21 Nov 2026): cloze (短文填空, 446 in 102 sets; each blank's sentence with （16）＿＿＿＿, the
  // passage page shown once) and reading (阅读理解一, 614 in 144 sets; the passage without its questions)
  'chi-cloze-mcq': 'pool',
  'chi-yuedu-mcq-text': 'pool',
  // Chinese 完成对话 (22 Nov 2026, migration 011): 8 phrases per blank; keys confirmed by Claude and Perplexity (owner's pair)
  'chi-dialogue-mcq': 'pool',
  // Maths upload (owner OK after the 40-question sample, 21 Nov 2026): MCQs 2018-2026, keys confirmed by the blind check;
  // 'pool' at 20+ past-paper questions, 'merge' below (they join the sub-topic's generated tiers)
  'math-algebra-algebra': 'pool', // 59
  'math-area-and-volume-area-and-circumference-of-circle': 'pool', // 45
  'math-area-and-volume-volume-of-cube-and-cuboid': 'pool', // 21
  'math-data-analysis-average-of-a-set-of-data': 'pool', // 25
  'math-data-representation-and-interpretation-picture-graphs-bar-graphs-tables-line-graphs-and-pie-charts': 'pool', // 27
  'math-decimals-decimal-notation-and-comparison': 'pool', // 104
  'math-fractions-equivalent-fractions-and-simplest-form': 'pool', // 50
  'math-fractions-fraction-of-a-whole-and-of-a-set': 'pool', // 54
  'math-fractions-multiplication-and-division-of-fractions': 'pool', // 41
  'math-geometry-angles': 'pool', // 49
  'math-measurement-length-mass-and-volume': 'pool', // 99
  'math-measurement-time': 'pool', // 35
  'math-money-money': 'pool', // 40
  'math-percentage-percentage': 'pool', // 116
  'math-rate-rate': 'merge', // 38: owner, 21 Nov 2026: keep the generated speed questions next to the past papers
  'math-ratio-ratio': 'pool', // 95
  'math-whole-numbers-addition-subtraction-multiplication-and-division': 'pool', // 126
  'math-whole-numbers-factors-and-multiples': 'pool', // 30
  'math-whole-numbers-numbers-up-to-100-1000-10-000-100-000-and-10-million': 'pool', // 107
  'math-area-and-volume-area-and-perimeter': 'pool', // 26 with the three-model / Claude+Perplexity verdicts (22 Nov 2026)
  'math-area-and-volume-area-of-triangle': 'pool', // 26 with the three-model / Claude+Perplexity verdicts (22 Nov 2026)
  'math-decimals-four-operations-with-decimals': 'merge', // 13
  'math-fractions-addition-and-subtraction-of-fractions': 'merge', // 13
  'math-fractions-fraction-and-division': 'merge', // 1
  'math-fractions-mixed-numbers-and-improper-fractions': 'merge', // 11
  'math-geometry-2d-shapes': 'pool', // 20 after the unsure-key confirms (23 Nov 2026)
  'math-geometry-3d-shapes-and-nets': 'merge', // 7
  'math-geometry-line-symmetry': 'merge', // 8
  'math-geometry-perpendicular-and-parallel-lines': 'pool', // 25 with the three-model / Claude+Perplexity verdicts (22 Nov 2026)
  'math-geometry-rectangle-and-square': 'merge', // 2
  'math-geometry-triangles-parallelogram-rhombus-and-trapezium': 'pool', // 31 with the three-model / Claude+Perplexity verdicts (22 Nov 2026)
};

/** pp_items.subject of a sub-topic, from its id prefix (pp_pool lists one subject per call). */
const SUBJECT_OF: Readonly<Record<string, string>> = { sci: 'science', eng: 'english', chi: 'chinese', math: 'maths' };
export const ppSubjectOf = (sub: string): string | null => SUBJECT_OF[sub.split('-')[0]] ?? null;
export const PP_BUCKET = 'pp-figures';
/** A sub-topic id as pp_items stores it (pp_items_subtopic_check, migration 009: up to 120; one Maths id has 103). */
const SUBTOPIC_ID = /^[a-z0-9-]{3,120}$/;
export const PP_MIN_TIER = 20; // same as MIN_POOL: a smaller past-paper pool never replaces a tier, it is merged in
const LEVELS = ['basic', 'intermediate', 'competent'] as const;

export interface PpFigure { path: string; w: number; h: number }
/** A row as pp_items_for returns it. */
export interface PpRow {
  id: string; subtopic: string; level: (typeof LEVELS)[number]; pattern: string | null; stem: string;
  options: string[]; answer: number; figures: PpFigure[]; year: number | null;
  grp?: string | null; seq?: number | null; // a passage set (migration 010): its id and the question's place in it
}
/** A signed, checked picture ready for an <img>. */
export interface PpFig { src: string; w: number; h: number }
/** The quiz page's question shape, as far as past-paper items fill it. */
export interface PpQ {
  id: string; sub: string; level: string; topic?: string; stem: string; options: string[]; answer: number;
  explain: ({ tag: string; why: string } | null)[]; solution: string[];
  numbered: true; // label options (1)-(4) as the paper and its pictures do, not A-D
  ppFigs: PpFig[];
  ppYear: number | null;
  calc?: false; // Maths: PSLE-style MCQs sit in Paper 1 (no calculator), so the quiz shows its "No calculator" badge
  group?: string; seq?: number; // a passage set: asked whole and in order, its pages shown once (migration 010)
}
const SET_ID = /^[a-z0-9-]{3,80}$/;
/** A passage set's id and position from a pool or content row; nothing for a single question or anything odd. */
const setOf = (r: { grp?: unknown; seq?: unknown }) => typeof r.grp === 'string' && SET_ID.test(r.grp) && Number.isInteger(r.seq)
  && (r.seq as number) >= 1 && (r.seq as number) <= 99 ? { group: r.grp, seq: r.seq as number } : {};

/** A past-paper question known only by id until the quiz has picked it (ADR 0012): sub-topic, level and easier-first
 * rank from pp_pool. Shaped like a PpQ (4 placeholder options so paper filters keep it) and replaced by the real
 * question (hydrate) before it is shown. */
export type PpStub = PpQ & { stub: true; ord: number | null };
export function stubOf(r: { id: unknown; subtopic: unknown; level: unknown; ord?: unknown; grp?: unknown; seq?: unknown }, topic?: string): PpStub | null {
  if (typeof r.id !== 'string' || !isPpId(r.id) || typeof r.subtopic !== 'string' || !SUBTOPIC_ID.test(r.subtopic)
    || !LEVELS.includes(r.level as PpRow['level'])) return null;
  return { id: r.id, sub: r.subtopic, level: r.level as string, topic, stem: '', options: ['', '', '', ''], answer: 0,
    explain: [null, null, null, null], solution: [], numbered: true, ppFigs: [], ppYear: null, stub: true,
    ord: Number.isInteger(r.ord) ? (r.ord as number) : null, ...setOf(r) };
}
export const isStub = (q: unknown): q is PpStub => !!q && (q as PpStub).stub === true;
/** A one-pool sub-topic (ADR 0011). */
export const isPoolSub = (sub: string, enabled = PP_ENABLED, sw: Readonly<Record<string, PpMode>> = PP_SWITCH) => ppMode(sub, enabled, sw) === 'pool';
/** A pool's ids easier-first (rank, then id), as pickPool wants them. */
export const easierFirst = (qs: { id: string; ord?: number | null }[]) =>
  [...qs].sort((a, b) => (a.ord ?? 1e9) - (b.ord ?? 1e9) || (a.id < b.id ? -1 : 1)).map((q) => q.id);

/** Milestones count at most a pool's first POOL_CAP questions in easier-first order (owner, 21 Nov 2026: Exam-ready on
 * 1,926 English grammar questions would need 964 counted). The rest of the pool is still served for practice. */
export const POOL_CAP = 300;
export function countingPool(qs: { id: string; ord?: number | null; group?: string }[]): string[] {
  const order = easierFirst(qs);
  const groupOf = new Map(qs.map((q) => [q.id, q.group]));
  if (!qs.some((q) => q.group)) return order.slice(0, POOL_CAP);
  // passage sets count whole (they are asked whole): take sets in the order their easiest question comes, until the cap;
  // ponytail: the set at the cap is counted only in part, so the counting pool is exactly POOL_CAP, the size train.ts
  // and the milestone preview use
  const out: string[] = [], taken = new Set<string>();
  for (const id of order) {
    if (out.length >= POOL_CAP) break;
    const g = groupOf.get(id);
    if (!g) { out.push(id); continue; }
    if (taken.has(g)) continue;
    taken.add(g);
    out.push(...order.filter((x) => groupOf.get(x) === g));
  }
  return out.slice(0, POOL_CAP);
}

/** One pp_pool page (fetchPool): 'more' to ask for the next page, 'done', or 'fail' (the list would be partial).
 * total: the server's exact count from the first page (null when it sent none: then a short page ends the list, the
 * pre-paging rule; a count is always asked for); count: this page's count; got: rows received so far, this page included.
 * ponytail: a row removed before the offset and another added after it while an upload runs keeps the total and is
 * not seen; key-based paging (pass the last row into pp_pool) if uploads ever overlap play. */
export function pageStep(total: number | null, count: number | null, got: number, pageLen: number, pageSize: number): 'more' | 'done' | 'fail' {
  if (total === null) return pageLen < pageSize ? 'done' : 'more';
  if (count !== total || got > total) return 'fail'; // the pool changed between pages
  if (got === total) return 'done';
  return pageLen ? 'more' : 'fail'; // the server stopped short of its own total
}

/** A past-paper question id (pp-<10 hex>), as opposed to a generated one. */
export const isPpId = (id: string) => /^pp-[0-9a-f]{10}$/.test(id);

/** The switch for one sub-topic, or null when past-paper items are off for it. */
export function ppMode(sub: string, enabled = PP_ENABLED, sw: Readonly<Record<string, PpMode>> = PP_SWITCH): PpMode | null {
  return enabled && Object.hasOwn(sw, sub) ? sw[sub] : null;
}

/** Which sub-topics to fetch: a tier quiz needs its own; Daily Review every switched one (so their retests are not
 * parked as missing); a paper the switched ones among its topics' sub-topics. */
export function ppSubsFor(mode: 'tier' | 'review' | 'paper', subId: string, paperSubs: string[],
  enabled = PP_ENABLED, sw: Readonly<Record<string, PpMode>> = PP_SWITCH): string[] {
  const on = (s: string) => ppMode(s, enabled, sw) !== null;
  if (mode === 'tier') return on(subId) ? [subId] : [];
  if (mode === 'review') return enabled ? Object.keys(sw).filter(on) : [];
  return [...new Set(paperSubs)].filter(on);
}

/** The mode mergePool applies in a quiz. Daily Review always merges, so a due retest of a generated question in a
 * replaced tier is still found (and not parked as missing) after its sub-topic switches. */
export function poolModeFor(quizMode: 'tier' | 'review' | 'paper', enabled = PP_ENABLED,
  sw: Readonly<Record<string, PpMode>> = PP_SWITCH): (sub: string) => PpMode | null {
  return (sub) => {
    const m = ppMode(sub, enabled, sw);
    return m && quizMode === 'review' ? 'merge' : m;
  };
}

const FIG_PATH = /^[a-z]+\/pp-[0-9a-f]{10}-\d{1,2}\.webp$/;

/** Shape check of an RPC row; anything else is dropped (never rendered). */
export function validRow(r: unknown): r is PpRow {
  if (!r || typeof r !== 'object') return false;
  const x = r as Record<string, unknown>;
  return typeof x.id === 'string' && /^pp-[0-9a-f]{10}$/.test(x.id)
    && typeof x.subtopic === 'string' && SUBTOPIC_ID.test(x.subtopic)
    && LEVELS.includes(x.level as PpRow['level'])
    && typeof x.stem === 'string' && x.stem.trim().length > 0
    // 4 options; 8 only for the 完成对话 dialogue sets (migration 011), the answer always one of them
    && Array.isArray(x.options) && (x.options.length === 4 || (x.subtopic === 'chi-dialogue-mcq' && x.options.length === 8))
    && x.options.every((o) => typeof o === 'string')
    && Number.isInteger(x.answer) && (x.answer as number) >= 0 && (x.answer as number) < x.options.length
    && Array.isArray(x.figures) && x.figures.every((f) => f && typeof f.path === 'string' && FIG_PATH.test(f.path)
      && Number.isFinite(f.w) && Number.isFinite(f.h))
    && (x.year === null || x.year === undefined || Number.isInteger(x.year));
}

/** A signed URL from our own project's private bucket, and nothing else (no other host, no public object path). */
export function safeSignedUrl(u: string, supabaseUrl: string): boolean {
  const base = supabaseUrl.replace(/\/+$/, '');
  if (!/^https:\/\/[a-z0-9.-]+$/i.test(base) && !/^http:\/\/(localhost|127\.0\.0\.1)(:\d+)?$/.test(base)) return false;
  if (!u.startsWith(`${base}/storage/v1/object/sign/${PP_BUCKET}/`)) return false;
  try {
    const p = new URL(u);
    return !!p.searchParams.get('token') && !p.pathname.includes('..');
  } catch { return false; }
}

/** A row plus its signed URLs as a quiz question. A row whose picture could not be signed is dropped (the stem
 * may depend on it). Wrong options carry an empty note so the quiz can log a tag; the page shows no "tempting" line. */
export function toQ(r: PpRow, signed: ReadonlyMap<string, string>, topic?: string): PpQ | null {
  const figs: PpFig[] = [];
  for (const f of r.figures) {
    const src = signed.get(f.path);
    if (!src) return null;
    figs.push({ src, w: Math.round(f.w), h: Math.round(f.h) });
  }
  return {
    id: r.id, sub: r.subtopic, level: r.level, topic, stem: r.stem, options: [...r.options], answer: r.answer,
    explain: r.options.map((_, k) => (k === r.answer ? null : { tag: 'past-paper', why: '' })),
    solution: [], numbered: true, ppFigs: figs,
    ppYear: Number.isInteger(r.year) && (r.year as number) >= 2000 && (r.year as number) <= 2100 ? r.year : null,
    ...(r.subtopic.startsWith('math-') ? { calc: false as const } : {}), // every past-paper Maths MCQ is Paper 1 (owner, 21 Nov 2026)
    ...setOf(r),
  };
}

/**
 * The quiz pool after the switch. Per (sub-topic, tier): off -> generated only (any past-paper item dropped);
 * merge -> both; replace -> the past-paper items alone when they fill a tier (PP_MIN_TIER), else both, so a tier
 * never becomes unplayable. Ids never clash (pp- prefix).
 */
export function mergePool<T extends { id: string; sub: string; level: string }>(generated: T[], pp: T[],
  modeOf: (sub: string) => PpMode | null = (s) => ppMode(s), minTier = PP_MIN_TIER): T[] {
  const key = (q: T) => `${q.sub}|${q.level}`;
  const ppBy = new Map<string, T[]>();
  for (const q of pp) if (modeOf(q.sub)) ppBy.set(key(q), [...(ppBy.get(key(q)) ?? []), q]);
  const replaced = new Set([...ppBy].filter(([k, v]) => modeOf(k.split('|')[0]) === 'replace' && v.length >= minTier).map(([k]) => k));
  // a one-pool sub-topic is its past-paper questions only (generated ones leave it, ADR 0011)
  return [...generated.filter((q) => !replaced.has(key(q)) && modeOf(q.sub) !== 'pool'), ...[...ppBy.values()].flat()];
}

/**
 * The ids a quiz reports to syncTiers, per "sub|level": exactly the TIER quiz's pool for that tier, whatever pool this
 * quiz asked from (Daily Review asks from the merged pool but must still report a replaced tier as pp-only, or the
 * stored total would not match the page's count and the tier could only clear once generated items are retired too).
 * `ppFailed` (the past-paper fetch failed): a switched sub-topic's tiers are left out, so syncTiers leaves them alone
 * instead of storing a generated-only total.
 */
export function tierPoolIds<T extends { id: string; sub: string; level: string }>(generated: T[], pp: T[],
  modeOf: (sub: string) => PpMode | null = (s) => ppMode(s), ppFailed = false, minTier = PP_MIN_TIER): Record<string, string[]> {
  const out: Record<string, string[]> = {};
  for (const q of mergePool(generated, ppFailed ? [] : pp, modeOf, minTier)) {
    if (modeOf(q.sub) !== 'pool') (out[`${q.sub}|${q.level}`] ??= []).push(q.id); // a pool sub-topic has milestones, no tiers
  }
  if (ppFailed) for (const k of Object.keys(out)) if (modeOf(k.split('|')[0])) delete out[k];
  return out;
}

/** Tier question count as the quiz will use it (mirrors mergePool for one tier): `gen` generated questions, `pp` active
 * past-paper rows (public counts only, data/pp_counts.json). `usesPp` tells the caller the tier's id set is not the
 * generated bank, so its tierHash cannot be known at build time (pp ids are private) and liveMastered must use the size. */
export function ppTierCount(gen: number, pp: number, mode: PpMode | null, minTier = PP_MIN_TIER): { count: number; usesPp: boolean } {
  if (!mode || pp <= 0) return { count: gen, usesPp: false };
  if (mode === 'pool') return { count: 0, usesPp: true }; // no tiers: train.ts counts the whole pool (Sub.pool)
  return { count: mode === 'replace' && pp >= minTier ? pp : gen + pp, usesPp: true };
}

/** The source line above a past-paper stem: "Past paper 2025" (year only, never the school). */
export function ppBadge(q: { ppYear?: number | null; numbered?: boolean }): string {
  if (!q.numbered) return '';
  return `<span class="pp-badge">Past paper${q.ppYear ? ` ${q.ppYear}` : ''}</span>`;
}

/** The pictures under the stem. Sources must already have passed safeSignedUrl. */
export function ppFigureHtml(figs: PpFig[], again = false): string {
  // a tap opens the page full size, where a phone can zoom it (passage pages are dense)
  const imgs = figs.map((f) => `<a class="qfig-art qfig-pp" href="${esc(f.src)}" target="_blank" rel="noopener noreferrer" `
    + `aria-label="Open this picture full size"><img src="${esc(f.src)}" width="${f.w}" height="${f.h}" `
    + `alt="Picture for this question" loading="eager" decoding="async" referrerpolicy="no-referrer"></a>`).join('');
  // a later question of a passage set: the pages were shown with its first question, so they wait behind a tap
  return again ? `<details class="qfig-again"><summary>Show the pages again</summary>${imgs}</details>` : imgs;
}

/** Option label: (1)-(4) for past-paper items, whose pictures and options say (1)-(4); else the page's letters. */
export const optionLabel = (q: { numbered?: boolean }, k: number, letters = 'ABCDEFGH') =>
  q.numbered ? `(${k + 1})` : letters[k];

