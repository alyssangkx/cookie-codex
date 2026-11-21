// Build-time data for the training pages: schools, sub-topics (in design order), question counts
// per tier, the fixed rewards and the cookie cards.
import rewards from '../data/rewards.json';
import mathSyllabus from '../data/syllabus/math.json';
import chineseSyllabus from '../data/syllabus/chinese.json';
import englishSyllabus from '../data/syllabus/english.json';
import scienceSyllabus from '../data/syllabus/science.json';
import { cookies } from './data';
import { MIN_POOL, tierHash, type School, type Tier } from './store';
import { paperOk } from './paper';
import { unitName } from './suggest';
import { competencyGroups } from './crumbs';
import { ppMode, ppTierCount, POOL_CAP, PP_SWITCH } from './pastpaper';
import ppCounts from '../data/pp_counts.json'; // numbers only: {"<sub>|<b|i|c>": n}; no past-paper ids or content

export { MIN_POOL };

export interface BankQ {
  id: string; sub: string; level: 'basic' | 'intermediate' | 'competent';
  stem: string; options: string[]; answer: number; figure?: Figure;
  explain: ({ tag: string; why: string } | null)[]; solution: string[];
  group?: string; seq?: number; // passage sets: questions sharing one passage
  visual?: Visual; // English visual text (poster, notice...) drawn as a card above the stem
  calc?: false; // Math only: false = no calculator (PSLE Paper 1 style); absent = a calculator is allowed or n/a
}
/** Inline SVG (code-made, currentColor) or Science line art with HTML labels placed at x/y percent of the image. */
export type Figure = string | { img: string; alt: string; labels?: { x: number; y: number; text: string }[] };
export interface Visual {
  kind: 'poster' | 'notice' | 'brochure' | 'timetable' | 'email'; title: string; subtitle?: string;
  blocks: { heading?: string; lines: string[] }[]; footer?: string;
}

const files = import.meta.glob<{ topic: string; questions: any[] }>('../data/quiz/*/*.json', {
  eager: true, import: 'default',
});

/** One slim bank per topic file; each question is filed under the sub-topic of its first outcome. */
export const banks = Object.values(files).map((f) => ({
  topic: f.topic as string,
  questions: f.questions.map((q) => ({
    id: q.id, sub: (q.outcomes[0] as string).replace(/-\d+$/, ''), level: q.level,
    stem: q.stem, options: q.options, answer: q.answer, explain: q.explain, solution: q.solution,
    ...(q.figure ? { figure: q.figure } : {}),
    ...(q.visual ? { visual: q.visual } : {}),
    ...(q.group ? { group: q.group, seq: q.seq } : {}), // passage sets (cloze, reading)
    ...(q.calc === false ? { calc: false } : {}), // Math Paper 1 style: no calculator (shown as a badge)
  })) as BankQ[],
}));

/** tierHash of every question id in every bank: names the bank set a Daily Review parked against (store.ts syncParked,
 * reviewDueCount), so a state parked by an older tab or build is re-checked instead of hidden. */
export const banksHash = tierHash(banks.flatMap((b) => b.questions.map((q) => q.id)));

const LEVEL_TIER = { basic: 'b', intermediate: 'i', competent: 'c' } as const;
const tierQs = new Map<string, string[]>(); // "sub|tier" -> question ids
const subFile = new Map<string, string>(); // sub -> topic file
for (const b of banks)
  for (const q of b.questions) {
    const k = `${q.sub}|${LEVEL_TIER[q.level]}`;
    if (!tierQs.has(k)) tierQs.set(k, []);
    tierQs.get(k)!.push(q.id);
    subFile.set(q.sub, b.topic);
  }
const countOf = (k: string) => tierQs.get(k)?.length ?? 0;
// the same tierHash() syncTiers stores, so liveMastered can tell a redesigned tier of the same size
const hashOf = (k: string) => tierHash(tierQs.get(k) ?? []);

export interface Sub {
  id: string; name: string; topic: string; topicName: string; home: number; capstone: boolean;
  school: School; file: string | null; count: Record<Tier, number>; playable: Record<Tier, boolean>;
  hash: Record<Tier, string | undefined>; // tierHash of each tier's question ids, for liveMastered; undefined on a tier that uses past-paper items (size check only)
  /** A one-pool sub-topic (ADR 0011): its past-paper question count (20+); its tiers' card slots are milestones 1-3. */
  pool?: number;
  poolAll?: number; // the whole past-paper pool when it is larger than the counting pool (POOL_CAP)
}
const ppTotal = (sub: string) => (['b', 'i', 'c'] as const).reduce((n, t) => n + ((ppCounts as Record<string, number>)[`${sub}|${t}`] ?? 0), 0);

/** Sub-topics the owner keeps on 'merge' at 20+ past-paper questions (21 Nov 2026: Rate keeps the generated speed questions). */
const OWNER_MERGE = new Set(['math-rate-rate']);
export const subs: Sub[] = (Object.entries(rewards.order) as [School, any[]][]).flatMap(([school, list]) =>
  list.map((s) => {
    // a switched-on past-paper sub-topic: the quiz merges or swaps in pp items, so count what it will use and drop the hash
    const view = (t: Tier) => ppTierCount(countOf(`${s.id}|${t}`), (ppCounts as Record<string, number>)[`${s.id}|${t}`] ?? 0, ppMode(s.id));
    const v = { b: view('b'), i: view('i'), c: view('c') };
    const count = { b: v.b.count, i: v.i.count, c: v.c.count };
    const hash = { b: v.b.usesPp ? undefined : hashOf(`${s.id}|b`), i: v.i.usesPp ? undefined : hashOf(`${s.id}|i`),
      c: v.c.usesPp ? undefined : hashOf(`${s.id}|c`) };
    if (ppMode(s.id) === 'pool' && ppTotal(s.id) < MIN_POOL) // mergePool drops a pool sub-topic's generated questions
      throw new Error(`train.ts: ${s.id} is 'pool' in PP_SWITCH with ${ppTotal(s.id)} past-paper questions (needs ${MIN_POOL}); use 'merge'`);
    if (ppMode(s.id) === 'merge' && ppTotal(s.id) >= MIN_POOL && !OWNER_MERGE.has(s.id)) // ADR 0011: one pool at 20
      console.warn(`train.ts: ${s.id} has ${ppTotal(s.id)} past-paper questions: switch it to 'pool' in PP_SWITCH`);
    const pool = ppMode(s.id) === 'pool' ? Math.min(ppTotal(s.id), POOL_CAP) : undefined; // the counting pool (POOL_CAP)
    return {
      ...s, school, file: subFile.get(s.id) ?? null, count, hash, ...(pool ? { pool, ...(ppTotal(s.id) > pool ? { poolAll: ppTotal(s.id) } : {}) } : {}),
      // playable from the generated bank only, as build_rewards.py decides slots and capstones (pp items never make a tier
      // playable); a one-pool sub-topic's three slots are milestones, all reachable, so they count as playable (power, pages)
      playable: pool ? { b: true, i: true, c: true }
        : { b: countOf(`${s.id}|b`) >= MIN_POOL, i: countOf(`${s.id}|i`) >= MIN_POOL, c: countOf(`${s.id}|c`) >= MIN_POOL },
    };
  }),
);
// every past-paper switch names a real sub-topic: a mistyped (long) id would otherwise stay off without a word (review)
{ const known = new Set(subs.map((s) => s.id)); const stray = Object.keys(PP_SWITCH).filter((k) => !known.has(k));
  if (stray.length) throw new Error(`train.ts: PP_SWITCH names sub-topics that do not exist: ${stray.join(', ')}`); }
export const subsOf = (school: School) => subs.filter((s) => s.school === school);

// The PSLE paper booklet of each English and Chinese sub-topic (their syllabus topics are single paper sections).
// English: the syllabus strands are the Paper 2 booklets. Chinese: the strands are skill strands, so the booklet comes from
// this table of syllabus topics (Paper 2 Booklet A: 语文应用, 短文填空, 阅读理解一; Booklet B: 完成对话, 阅读理解二;
// Paper 3: 听力). A Chinese topic missing here fails the build. Used by listGroup (English school page) and the
// competency groups (crumbs.ts competencyGroups).
const CHI_BOOKLET: Record<string, { topic: string; topicName: string }> = (() => {
  const a = { topic: 'chi-p2a', topicName: 'Paper 2 Booklet A (语文应用, 短文填空, 阅读理解一)' };
  const b = { topic: 'chi-p2b', topicName: 'Paper 2 Booklet B (完成对话, 阅读理解二)' };
  const l = { topic: 'chi-p3', topicName: 'Paper 3 (听力 listening)' };
  return { 'chi-pinyin': a, 'chi-zixing': a, 'chi-ciyu': a, 'chi-juzi-yunyong': a, 'chi-cloze': a, 'chi-yuedu-mcq': a,
    'chi-dialogue': b, 'chi-yuedu-open': b, 'chi-tingli-types': l };
})();
const booklet = new Map([
  ...englishSyllabus.strands.flatMap((st) =>
    st.topics.flatMap((t) => t.subtopics.map((sb) => [sb.id, { topic: st.id, topicName: st.name }] as const))),
  ...chineseSyllabus.strands.flatMap((st) => st.topics.flatMap((t) => {
    if (!CHI_BOOKLET[t.id]) throw new Error(`train.ts: Chinese topic ${t.id} has no paper booklet in CHI_BOOKLET`);
    return t.subtopics.map((sb) => [sb.id, CHI_BOOKLET[t.id]] as const);
  })),
]);
/** The group a sub-topic is listed under on its school page: the English booklet, else its own topic. */
export const listGroup = (s: Sub) => (s.school === 'english' ? booklet.get(s.id) : undefined) ?? { topic: s.topic, topicName: s.topicName };
export { unitName }; // lives in suggest.ts so client scripts can use it without the banks
/** Sub-topics whose questions are blanks in one passage (`cloze: true` in the syllabus JSON): the quiz page fills
 *  the blanks in as they are answered. */
export const clozeSubs = [mathSyllabus, chineseSyllabus, englishSyllabus, scienceSyllabus].flatMap((syl) =>
  syl.strands.flatMap((st) => st.topics.flatMap((t) =>
    (t.subtopics as { id: string; cloze?: boolean }[]).filter((sb) => sb.cloze).map((sb) => sb.id))));
export const subSlug = (id: string) => id.replace(/^(math|sci|eng|chi)-/, '');
export const hasContent = (s: Sub) => !!s.pool || s.playable.b || s.playable.i || s.playable.c;

// English and Science go live as soon as their banks have a playable tier; Math and Chinese are always on.
export const SCHOOLS: { id: School; name: string; ready: boolean }[] = [
  { id: 'math', name: 'Math', ready: true },
  { id: 'science', name: 'Science', ready: subs.some((s) => s.school === 'science' && hasContent(s)) },
  { id: 'english', name: 'English', ready: subs.some((s) => s.school === 'english' && hasContent(s)) },
  { id: 'chinese', name: 'Chinese', ready: true },
];

export const slots = rewards.slots as Record<string, { slug: string; dup: boolean }>;
export const cookieBySlug = new Map(cookies.map((c) => [c.slug, c]));
/** Card details the client needs, keyed by slug. */
export const cardInfo = Object.fromEntries(cookies.map((c) => [c.slug, { name: c.name, image: c.image, rarity: c.rarity }]));
export const milestones = rewards.milestones as Record<string, string[]>;
/** Replacement and shop order per rarity (build_rewards.py `rarityOrder`): every non-milestone card once. */
export const rarityOrder = rewards.rarityOrder as Record<string, string[]>;
const topicName = new Map([mathSyllabus, chineseSyllabus, englishSyllabus, scienceSyllabus].flatMap((syl) =>
  syl.strands.flatMap((st) => st.topics.map((t) => [t.id, t.name] as [string, string]))));
for (const b of booklet.values()) topicName.set(b.topic, b.topicName); // booklet groups are named as the child sees them
/** Competency groups (crumbs.ts competencyGroups): groups a Super Epic can be earned for (Math, Science topics; English,
 * Chinese paper booklets; only sub-topics with a playable Competent tier, 2 or more per group), and subjects for the
 * subject Legendary (every sub-topic of the subject playable at Competent, 2 or more groups). */
export const { topics: competencyTopics, subjects: competencySubjects } = competencyGroups(
  subs.map((s) => ({ id: s.id, school: s.school, group: booklet.get(s.id)?.topic ?? s.topic, playableC: s.playable.c })));
/** Everything the client economy needs (crumbs.ts Economy plus card names), served at /data/economy.json. */
export const economyData = () => ({
  order: rarityOrder,
  topics: competencyTopics,
  subjects: competencySubjects,
  topicNames: Object.fromEntries(Object.keys(competencyTopics).map((t) => [t, topicName.get(t) ?? t])),
  cards: Object.fromEntries(cookies.map((c) => [c.slug, { name: c.name, image: c.image, rarity: c.rarity }])),
  milestones,
});

const PREFIX_SCHOOL: Record<string, School> = { math: 'math', sci: 'science', eng: 'english', chi: 'chinese' };
/** Subjects the WA/SA builder offers. Chinese stays out for now (its banks are mostly passage and 8-option sets). */
export const PAPER_SCHOOLS: School[] = ['math', 'english', 'science'];
/** Topics with paper-ready questions (4 options, not in a passage set: paperOk), for the WA/SA paper builder. */
export const paperTopics = banks
  .map((b) => ({
    id: b.topic, name: topicName.get(b.topic) ?? b.topic, school: PREFIX_SCHOOL[b.topic.split('-')[0]],
    count: b.questions.filter(paperOk).length,
  }))
  .filter((t) => PAPER_SCHOOLS.includes(t.school) && t.count > 0)
  .sort((a, b) => a.name.localeCompare(b.name));
