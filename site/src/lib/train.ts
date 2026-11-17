// Build-time data for the training pages: schools, sub-topics (in design order), question counts
// per tier, the fixed rewards and the cookie cards.
import rewards from '../data/rewards.json';
import mathSyllabus from '../data/syllabus/math.json';
import chineseSyllabus from '../data/syllabus/chinese.json';
import { cookies } from './data';
import type { School, Tier } from './store';

export const SCHOOLS: { id: School; name: string; ready: boolean }[] = [
  { id: 'math', name: 'Math', ready: true },
  { id: 'science', name: 'Science', ready: false },
  { id: 'english', name: 'English', ready: false },
  { id: 'chinese', name: 'Chinese', ready: true },
];
export const MIN_POOL = 20; // a tier is playable only with at least 20 questions

export interface BankQ {
  id: string; sub: string; level: 'basic' | 'intermediate' | 'competent';
  stem: string; options: string[]; answer: number; figure?: string;
  explain: ({ tag: string; why: string } | null)[]; solution: string[];
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
export const subSlug = (id: string) => id.replace(/^(math|sci|eng|chi)-/, '');
export const hasContent = (s: Sub) => s.playable.b || s.playable.i || s.playable.c;

export const slots = rewards.slots as Record<string, { slug: string; dup: boolean }>;
export const cookieBySlug = new Map(cookies.map((c) => [c.slug, c]));
/** Card details the client needs, keyed by slug. */
export const cardInfo = Object.fromEntries(cookies.map((c) => [c.slug, { name: c.name, image: c.image, rarity: c.rarity }]));
export const milestones = rewards.milestones as Record<string, string[]>;

const topicName = new Map([mathSyllabus, chineseSyllabus].flatMap((syl) =>
  syl.strands.flatMap((st) => st.topics.map((t) => [t.id, t.name] as [string, string]))));
/** Topics that have a question bank, for the WA/SA paper builder. */
export const paperTopics = banks
  .map((b) => ({ id: b.topic, name: topicName.get(b.topic) ?? b.topic, count: b.questions.length }))
  .sort((a, b) => a.name.localeCompare(b.name));
