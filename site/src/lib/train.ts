// Build-time data for the training pages: schools, sub-topics (in design order), question counts
// per tier, the fixed rewards and the cookie cards.
import rewards from '../data/rewards.json';
import mathSyllabus from '../data/syllabus/math.json';
import chineseSyllabus from '../data/syllabus/chinese.json';
import englishSyllabus from '../data/syllabus/english.json';
import scienceSyllabus from '../data/syllabus/science.json';
import { cookies } from './data';
import { MIN_POOL, type School, type Tier } from './store';
import { paperOk } from './paper';

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

const LEVEL_TIER = { basic: 'b', intermediate: 'i', competent: 'c' } as const;
const counts = new Map<string, number>(); // "sub|tier" -> questions
const subFile = new Map<string, string>(); // sub -> topic file
for (const b of banks)
  for (const q of b.questions) {
    const k = `${q.sub}|${LEVEL_TIER[q.level]}`;
    counts.set(k, (counts.get(k) ?? 0) + 1);
    subFile.set(q.sub, b.topic);
  }

export interface Sub {
  id: string; name: string; topic: string; topicName: string; home: number; capstone: boolean;
  school: School; file: string | null; count: Record<Tier, number>; playable: Record<Tier, boolean>;
}

export const subs: Sub[] = (Object.entries(rewards.order) as [School, any[]][]).flatMap(([school, list]) =>
  list.map((s) => {
    const count = { b: counts.get(`${s.id}|b`) ?? 0, i: counts.get(`${s.id}|i`) ?? 0, c: counts.get(`${s.id}|c`) ?? 0 };
    return {
      ...s, school, file: subFile.get(s.id) ?? null, count,
      playable: { b: count.b >= MIN_POOL, i: count.i >= MIN_POOL, c: count.c >= MIN_POOL },
    };
  }),
);
export const subsOf = (school: School) => subs.filter((s) => s.school === school);

// English sub-topics are the PSLE Paper 2 sections (one topic each, in paper order); its school page groups them by
// booklet (the syllabus strand) and calls them sections.
const booklet = new Map(englishSyllabus.strands.flatMap((st) =>
  st.topics.flatMap((t) => t.subtopics.map((sb) => [sb.id, { topic: st.id, topicName: st.name }] as const))));
/** The group a sub-topic is listed under on its school page: the English booklet, else its own topic. */
export const listGroup = (s: Sub) => booklet.get(s.id) ?? { topic: s.topic, topicName: s.topicName };
/** What a school calls its sub-topics on the training pages. */
export const unitName = (school: School, n = 2) => (school === 'english' ? 'section' : 'sub-topic') + (n === 1 ? '' : 's');
export const subSlug = (id: string) => id.replace(/^(math|sci|eng|chi)-/, '');
export const hasContent = (s: Sub) => s.playable.b || s.playable.i || s.playable.c;

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

const topicName = new Map([mathSyllabus, chineseSyllabus, englishSyllabus, scienceSyllabus].flatMap((syl) =>
  syl.strands.flatMap((st) => st.topics.map((t) => [t.id, t.name] as [string, string]))));
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
