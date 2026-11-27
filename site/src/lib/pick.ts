import { isPpId } from './pastpaper.ts';
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
 * 3. if new ones run short: retests from this tier that are not due yet.
 * A question answered right is never asked again (owner, 27 Nov 2026: only wrong answers come back), so a quiz near the
 * end of a tier is shorter than `size`; nor is an answered question of a passage set (its wrong ones are held, QState.h).
 */
export function pickTier(
  ids: string[], seen: Record<string, Seen | undefined>, size = 10, now = Date.now(), rand = Math.random,
  sideRetests: string[] = [],
  passage?: (id: string) => { group: string; seq: number } | undefined,
  ordered = false, // ids are easier-first (a one-pool sub-topic, ADR 0011): new questions keep that order, no shuffle
): string[] {
  const byDue = (a: string, b: string) => seen[a]!.due - seen[b]!.due;
  const retest = ids.filter((id) => (seen[id]?.s ?? 0) > 0).sort(byDue);
  const due = [...retest, ...sideRetests.filter((id) => (seen[id]?.s ?? 0) > 0)]
    .filter((id) => seen[id]!.due <= now).sort(byDue);
  const notDue = retest.filter((id) => seen[id]!.due > now);
  // owner, 24 Nov 2026: a generated question only when no past-paper one is left. In a merged tier the new past-paper
  // questions come first (each kind shuffled on its own); generated ones only fill the quiz
  const unseen = ids.filter((id) => !seen[id]);
  const fresh = ordered ? unseen : [...shuffle(unseen.filter(isPpId), rand), ...shuffle(unseen.filter((id) => !isPpId(id)), rand)];
  const take = due.slice(0, Math.min(3, Math.floor(size * 0.3)));
  const out = [...take, ...fresh.slice(0, size - take.length)];
  const spare = [...due.slice(take.length).filter((id) => ids.includes(id)), ...notDue];
  while (out.length < size && spare.length) {
    const id = spare.shift()!;
    if (!out.includes(id)) out.push(id);
  }
  if (passage && out.some((id) => passage(id)))
    return wholePassages(out, ids.filter((id) => !(seen[id] && passage(id))), passage, size, new Set(take), (id) => !!seen[id]);
  return ordered ? out : shuffle(out, rand);
}

/** A cloze section's quiz (owner, 24 Nov 2026: "if there are 15 blanks, then the quiz needs 15 questions"): ONE passage,
 *  whole, every blank in passage order: the first passage (in `ids` order, easier-first) with no blank answered yet.
 *  An answered passage is never asked again (owner, 27 Nov 2026: right answers retire, wrong ones in a passage are held);
 *  [] when every passage has been done. */
export function pickPassage(all: string[], seen: Record<string, Seen | undefined>, _now = Date.now(),
  passage: (id: string) => { group: string; seq: number } | undefined = () => undefined): string[] {
  const ids = all.filter((id) => passage(id)); // a question outside any passage is never a "passage of one"
  const group = (id: string) => passage(id)!.group;
  const done = new Set(ids.filter((id) => seen[id]).map(group));
  const pickId = ids.find((id) => !done.has(group(id)));
  if (pickId == null) return [];
  const g = group(pickId);
  return ids.filter((id) => group(id) === g).sort((a, b) => (passage(a)?.seq ?? 0) - (passage(b)?.seq ?? 0));
}

/** A one-pool sub-topic's quiz (ADR 0011): `ids` are its past-paper questions easier-first (pp_pool order). Due retests
 *  first (at most 3), then new questions in that order, then not-due retests, then counted ones again. */
export const pickPool = (ids: string[], seen: Record<string, Seen | undefined>, size = 10, now = Date.now(),
  passage?: (id: string) => { group: string; seq: number } | undefined) =>
  pickTier(ids, seen, size, now, Math.random, [], passage, true); // a passage set is asked whole and in order

/**
 * Passage sub-topics (cloze, reading): a quiz is whole passages, read once, questions in order.
 * Every due retest (`must`, at most 3) is always included: passages holding one go first and are cut
 * if needed so that the due questions of later passages still fit. Then other passages in picked
 * order, whole while they fit; one too big gives way to a later, smaller one; only if nothing fits
 * exactly is one cut. A cut keeps due questions, then picked ones, then passage order.
 * A picked question outside this tier's passages (a retest from another level) is a unit of its own.
 */
export function wholePassages(
  picked: string[], ids: string[], passage: (id: string) => { group: string; seq: number } | undefined, size: number,
  must: Set<string> = new Set(),
  done?: (id: string) => boolean, // answered before: a cut with no due retest starts at the passage's first blank not done
): string[] {
  const tier = new Set(ids);
  const members = new Map<string, string[]>();
  for (const id of ids) {
    const g = passage(id)?.group ?? id; // an ungrouped question is a passage of one
    if (!members.has(g)) members.set(g, []);
    members.get(g)!.push(id);
  }
  const seq = (id: string) => passage(id)?.seq ?? 0;
  const unitKey = (id: string) => (tier.has(id) ? passage(id)?.group ?? id : id);
  const units = new Map<string, string[]>();
  for (const id of picked) {
    const k = unitKey(id);
    if (!units.has(k)) units.set(k, k === id ? [id] : [...members.get(k)!].sort((a, b) => seq(a) - seq(b)));
  }
  const want = new Set(picked);
  const rank = (id: string) => (must.has(id) ? 0 : want.has(id) ? 1 : 2);
  // A cut passage keeps a CONSECUTIVE run of its questions (blanks 1-2, never 1 and 3, which reads as a
  // skipped question). The run is chosen to hold the due retests first, then picked (new) ones, as early
  // in the passage as possible.
  const cut = (u: string[], n: number) => {
    if (n <= 0) return [];
    if (n >= u.length) return u;
    // no due retest in it: read on from the first blank not answered yet (owner, 24 Nov 2026: a passage started at its
    // 4th blank), never from the middle because the easier-first order picked later blanks
    if (done && !u.some((id) => must.has(id))) {
      const first = Math.max(0, u.findIndex((id) => !done(id)));
      const s = Math.min(first, u.length - n);
      return u.slice(s, s + n);
    }
    let best = 0, bestScore = -Infinity;
    for (let s = 0; s + n <= u.length; s++) {
      const w = u.slice(s, s + n);
      const score = w.filter((id) => rank(id) === 0).length * 100 + w.filter((id) => rank(id) === 1).length - s * 0.5;
      if (score > bestScore) { bestScore = score; best = s; }
    }
    return u.slice(best, best + n);
  };
  const all = [...units.values()];
  const mustUnits = all.filter((u) => u.some((id) => must.has(id)));
  const out: string[] = [];
  mustUnits.forEach((u, i) => {
    const later = mustUnits.slice(i + 1).reduce((n, v) => n + v.filter((id) => must.has(id)).length, 0);
    const room = size - out.length - later; // keep space for the due questions still to come
    out.push(...(u.length <= room ? u : cut(u, room)));
  });
  const skipped: string[][] = [];
  for (const u of all.filter((u) => !mustUnits.includes(u))) {
    const room = size - out.length;
    if (room <= 0) break;
    if (u.length <= room) out.push(...u);
    else skipped.push(u);
  }
  for (const u of skipped) if (out.length < size) out.push(...cut(u, size - out.length));
  return out;
}

/** Daily Review: due retests from anywhere, oldest first; 5 questions, growing to 15 with the backlog. */
/** How many questions one Daily Review asks when `due` are waiting: half of them, between 5 and 15, never more than are due. */
export const reviewSize = (due: number) => Math.min(due, 15, Math.max(5, Math.ceil(due / 2)));

export function pickReview(ids: string[], seen: Record<string, Seen | undefined>, size?: number, now = Date.now()) {
  const due = ids.filter((id) => (seen[id]?.s ?? 0) > 0 && seen[id]!.due <= now).sort((a, b) => seen[a]!.due - seen[b]!.due);
  return due.slice(0, size ?? reviewSize(due.length));
}

/**
 * Daily Review keeps passage sets readable: due questions that share a passage are asked together, in passage order,
 * where the passage first comes up (due order c4, m1, c1, c2 -> c1, c2, c4, m1). Only due questions are asked; a
 * passage blank that is not due is shown with its answer by the quiz page, so nothing reads as skipped.
 */
export function reviewPassages(picked: string[], passage: (id: string) => { group: string; seq: number } | undefined): string[] {
  const byGroup = new Map<string, string[]>();
  for (const id of picked) { const g = passage(id)?.group; if (g) byGroup.set(g, [...(byGroup.get(g) ?? []), id]); }
  const out: string[] = [], done = new Set<string>();
  for (const id of picked) {
    const g = passage(id)?.group;
    if (!g) out.push(id);
    else if (!done.has(g)) { done.add(g); out.push(...byGroup.get(g)!.sort((a, b) => passage(a)!.seq - passage(b)!.seq)); }
  }
  return out;
}

export type Mix = Record<'basic' | 'intermediate' | 'competent', number>;
export const MIXES: Record<string, { label: string; mix: Mix }> = {
  wa: { label: 'Quick test (more Basic questions)', mix: { basic: 0.4, intermediate: 0.4, competent: 0.2 } },
  sa: { label: 'Exam paper (more Competent questions)', mix: { basic: 0.2, intermediate: 0.4, competent: 0.4 } },
};

/**
 * WA/SA practice paper across chosen topics: questions are spread evenly over the topics and
 * split by level per the mix. Unseen questions first, then due retests, then retests not due yet; never a question
 * answered right (owner, 27 Nov 2026), so a paper can come out shorter once the topics are nearly done.
 */
export function pickPaper(
  qs: { id: string; topic: string; level: keyof Mix }[], seen: Record<string, Seen | undefined>,
  n: number, mix: Mix, now = Date.now(), rand = Math.random,
): string[] {
  qs = qs.filter((q) => seen[q.id]?.s !== 0); // answered right (or a held passage question): never asked again (27 Nov 2026)
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
