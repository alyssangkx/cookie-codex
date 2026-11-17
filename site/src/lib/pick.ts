// Choose the questions for one quiz (docs/game-design.md section 3). Pure, so it is testable:
//   node --test site/src/lib/*.test.ts
export interface Seen {
  s: number; // 0 retired, 1-3 retest step
  due: number;
}

const shuffle = <T>(xs: T[], rand: () => number) => {
  for (let i = xs.length - 1; i > 0; i--) {
    const j = Math.floor(rand() * (i + 1));
    [xs[i], xs[j]] = [xs[j], xs[i]];
  }
  return xs;
};

/**
 * Tier quiz, always `size` questions when the tier has that many:
 * 1. up to 3 due retests (never more than 30%), from this tier or, via `sideRetests`, from other
 *    tiers of the same sub-topic, so the retest backlog drains;
 * 2. new questions from this tier;
 * 3. if new ones run short: retests from this tier that are not due yet;
 * 4. then retired questions again, so a pass is always earned on a full quiz.
 */
export function pickTier(
  ids: string[], seen: Record<string, Seen | undefined>, size = 10, now = Date.now(), rand = Math.random,
  sideRetests: string[] = [],
  passage?: (id: string) => { group: string; seq: number } | undefined,
): string[] {
  const byDue = (a: string, b: string) => seen[a]!.due - seen[b]!.due;
  const retest = ids.filter((id) => (seen[id]?.s ?? 0) > 0).sort(byDue);
  const due = [...retest, ...sideRetests.filter((id) => (seen[id]?.s ?? 0) > 0)]
    .filter((id) => seen[id]!.due <= now).sort(byDue);
  const notDue = retest.filter((id) => seen[id]!.due > now);
  const fresh = shuffle(ids.filter((id) => !seen[id]), rand);
  const retired = shuffle(ids.filter((id) => seen[id]?.s === 0), rand);
  const take = due.slice(0, Math.min(3, Math.floor(size * 0.3)));
  const out = [...take, ...fresh.slice(0, size - take.length)];
  const spare = [...due.slice(take.length).filter((id) => ids.includes(id)), ...notDue, ...retired];
  while (out.length < size && spare.length) {
    const id = spare.shift()!;
    if (!out.includes(id)) out.push(id);
  }
  return passage && out.some((id) => passage(id)) ? wholePassages(out, ids, passage, size) : shuffle(out, rand);
}

/**
 * Passage sub-topics (cloze, reading): a quiz is whole passages, read once, questions in order.
 * Passages are taken in the priority order of the picked questions (retests first, then new), whole
 * while they fit, and the last one is cut to make exactly `size`.
 */
export function wholePassages(
  picked: string[], ids: string[], passage: (id: string) => { group: string; seq: number } | undefined, size: number,
): string[] {
  const members = new Map<string, string[]>();
  for (const id of ids) {
    const g = passage(id)?.group ?? id; // an ungrouped question is a passage of one
    members.set(g, [...(members.get(g) ?? []), id]);
  }
  const out: string[] = [];
  for (const g of new Set(picked.map((id) => passage(id)?.group ?? id))) {
    if (out.length >= size) break;
    const qs = (members.get(g) ?? [g]).sort((a, b) => (passage(a)?.seq ?? 0) - (passage(b)?.seq ?? 0));
    out.push(...qs.slice(0, size - out.length));
  }
  return out;
}

/** Daily Review: due retests from anywhere, oldest first; 5 questions, growing to 15 with the backlog. */
export function pickReview(ids: string[], seen: Record<string, Seen | undefined>, size?: number, now = Date.now()) {
  const due = ids.filter((id) => (seen[id]?.s ?? 0) > 0 && seen[id]!.due <= now).sort((a, b) => seen[a]!.due - seen[b]!.due);
  return due.slice(0, size ?? Math.min(15, Math.max(5, Math.ceil(due.length / 2))));
}

export type Mix = Record<'basic' | 'intermediate' | 'competent', number>;
export const MIXES: Record<string, { label: string; mix: Mix }> = {
  wa: { label: 'Weighted Assessment (more Basic)', mix: { basic: 0.4, intermediate: 0.4, competent: 0.2 } },
  sa: { label: 'Semestral / Prelim (more Competent)', mix: { basic: 0.2, intermediate: 0.4, competent: 0.4 } },
};

/**
 * WA/SA practice paper across chosen topics: questions are spread evenly over the topics and
 * split by level per the mix. Unseen questions first, then due retests, then anything else,
 * so a paper never runs dry even after a topic is mastered.
 */
export function pickPaper(
  qs: { id: string; topic: string; level: keyof Mix }[], seen: Record<string, Seen | undefined>,
  n: number, mix: Mix, now = Date.now(), rand = Math.random,
): string[] {
  const topics = shuffle([...new Set(qs.map((q) => q.topic))], rand); // random start, so every topic gets a turn
  const rank = (id: string) => (!seen[id] ? 0 : (seen[id]!.s > 0 && seen[id]!.due <= now) ? 1 : 2);
  const levels = Object.keys(mix) as (keyof Mix)[];
  const want = levels.map((l) => Math.round(n * mix[l]));
  want[1] += n - want.reduce((a, b) => a + b, 0); // rounding goes to intermediate
  const out: string[] = [];
  levels.forEach((level, li) => {
    const pools = topics.map((t) =>
      shuffle(qs.filter((q) => q.topic === t && q.level === level).map((q) => q.id), rand).sort((a, b) => rank(a) - rank(b)));
    // round-robin over topics until this level has its share or every pool is empty
    for (let got = 0, k = 0; got < want[li] && pools.some((p) => p.length); k++) {
      const pool = pools[k % pools.length];
      if (pool.length) { out.push(pool.shift()!); got++; }
    }
  });
  // top up from any level if some level ran short
  const taken = new Set(out);
  const rest = shuffle(qs.filter((q) => !taken.has(q.id)).map((q) => q.id), rand).sort((a, b) => rank(a) - rank(b));
  while (out.length < n && rest.length) out.push(rest.shift()!);
  return out; // ordered Basic -> Intermediate -> Competent, like a real paper
}
