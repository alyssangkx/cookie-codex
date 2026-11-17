// Pure logic for the "What do you want to train today?" page: power numbers and the
// "Suggested for you" cards. No DOM, no localStorage: everything comes from the save object.
import { TIERS, TIER_NAME, triesPerDay, tierState, tierOpen, attemptsToday, capReached, isDue, type SaveV1, type Tier } from './store.ts';

export interface SubInfo {
  id: string; topic: string; topicName: string; name: string; slug: string;
  playable: Record<Tier, boolean>;
  count?: Record<Tier, number>; // questions per tier, for the "N of M mastered" wording
}
export interface Suggestion {
  kind: 'review' | 'one-more' | 'weak' | 'next' | 'done';
  title: string; reason: string; href: string; sub?: string; tier?: Tier;
}

export const TIER_WEIGHT: Record<Tier, number> = { b: 1, i: 2, c: 3 };
export const WEAK_DAYS = 14;
export const WEAK_MIN_ANSWERED = 10;
const DAY = 86_400_000;

/** 0-100: weighted share of the playable tiers in these sub-topics that are cleared. */
export function topicPower(s: SaveV1, subsInTopic: SubInfo[]): number {
  let got = 0, all = 0;
  for (const sub of subsInTopic)
    for (const t of TIERS) {
      if (!sub.playable[t]) continue;
      all += TIER_WEIGHT[t];
      if (tierState(s, sub.id, t).cleared) got += TIER_WEIGHT[t];
    }
  return all ? Math.round((100 * got) / all) : 0;
}

export const hasPlayable = (sub: SubInfo) => TIERS.some((t) => sub.playable[t]);

export function groupByTopic(subs: SubInfo[]): { topic: string; name: string; subs: SubInfo[] }[] {
  const out: { topic: string; name: string; subs: SubInfo[] }[] = [];
  for (const sub of subs) {
    const g = out.find((x) => x.topic === sub.topic) ?? out[out.push({ topic: sub.topic, name: sub.topicName, subs: [] }) - 1];
    g.subs.push(sub);
  }
  return out;
}

/** Rounded mean of topicPower over topics that have at least one playable tier. */
export function schoolPower(s: SaveV1, subs: SubInfo[]): number {
  const powers = groupByTopic(subs).filter((g) => g.subs.some(hasPlayable)).map((g) => topicPower(s, g.subs));
  return powers.length ? Math.round(powers.reduce((a, b) => a + b, 0) / powers.length) : 0;
}

/** Questions due for retest. With a question-to-sub map, only questions of known subs are counted. */
export function dueCount(s: SaveV1, now: number, questionSub?: Record<string, string>): number {
  let n = 0;
  for (const id of Object.keys(s.questions)) {
    if (questionSub && !questionSub[id]) continue;
    if (isDue(s, id, now)) n++;
  }
  return n;
}

/** Accuracy per "sub|tier" over the last 14 days from finished tier quizzes. */
export function recentAccuracy(s: SaveV1, now: number) {
  const m = new Map<string, { sub: string; tier: Tier; score: number; total: number }>();
  for (const a of s.attempts) {
    if (a.mode !== 'tier' || a.open || !a.sub || !a.tier || !a.total) continue;
    if (a.ts > now || now - a.ts > WEAK_DAYS * DAY) continue;
    const k = `${a.sub}|${a.tier}`;
    const e = m.get(k) ?? { sub: a.sub, tier: a.tier, score: 0, total: 0 };
    e.score += a.score; e.total += a.total;
    m.set(k, e);
  }
  return m;
}

const tierHref = (sub: string, tier: Tier) => `/quiz/?sub=${encodeURIComponent(sub)}&tier=${tier}`;

export function suggestions(
  s: SaveV1, subs: SubInfo[],
  ctx: { now: number; dueCount: number; questionSub?: Record<string, string> },
): Suggestion[] {
  if (capReached(s))
    return [{ kind: 'done', title: 'Done for today!', reason: "You have used today's training time. See your cards and come back tomorrow.", href: '/collection/' }];

  const canStart = (sub: SubInfo, t: Tier) =>
    sub.playable[t] && tierOpen(s, sub.id, t, sub.playable) && attemptsToday(s, sub.id, t) < triesPerDay(sub.id);
  const taken = new Set<string>();
  const out: Suggestion[] = [];
  const add = (x: Suggestion) => {
    if (x.sub && x.tier) { const k = `${x.sub}|${x.tier}`; if (taken.has(k)) return false; taken.add(k); }
    out.push(x);
    return true;
  };

  // 1. Daily Review
  if (ctx.dueCount > 0)
    add({
      kind: 'review', title: 'Daily Review',
      reason: `${ctx.dueCount} question${ctx.dueCount === 1 ? ' is' : 's are'} ready to retest`,
      href: '/quiz/?mode=review',
    });

  // 2. Keep going: a tier that is part-mastered (at least 1 question mastered, not cleared)
  for (const sub of subs) {
    const hit = TIERS.find((t) => {
      const st = tierState(s, sub.id, t);
      return canStart(sub, t) && !st.cleared && (st.mastered ?? 0) > 0;
    });
    if (hit) {
      const st = tierState(s, sub.id, hit);
      const total = st.total ?? sub.count?.[hit];
      add({
        kind: 'one-more', title: `Keep going! ${sub.name}`, sub: sub.id, tier: hit,
        reason: `${TIER_NAME[hit]}: ${total ? `${st.mastered} of ${total} questions mastered.` : `${st.mastered} questions mastered.`}`, href: tierHref(sub.id, hit),
      });
      break;
    }
  }

  // 3. Weak spot: lowest accuracy over 14 days, at least 10 answered
  const byId = new Map(subs.map((x) => [x.id, x]));
  const weak = [...recentAccuracy(s, ctx.now).values()]
    .filter((e) => e.total >= WEAK_MIN_ANSWERED && byId.has(e.sub) && canStart(byId.get(e.sub)!, e.tier) && !taken.has(`${e.sub}|${e.tier}`))
    .map((e) => ({ ...e, acc: Math.round((100 * e.score) / e.total) }))
    .sort((a, b) => a.acc - b.acc || b.total - a.total)[0];
  if (weak) {
    const sub = byId.get(weak.sub)!;
    add({
      kind: 'weak', title: `Fix a weak spot: ${sub.name}`, sub: weak.sub, tier: weak.tier,
      reason: `${TIER_NAME[weak.tier]}: ${weak.acc}% right over the last ${WEAK_DAYS} days`, href: tierHref(weak.sub, weak.tier),
    });
  }

  // 4. Next up: first open, uncleared, playable tier in syllabus order
  outer: for (const sub of subs)
    for (const t of TIERS)
      if (canStart(sub, t) && !tierState(s, sub.id, t).cleared && !taken.has(`${sub.id}|${t}`)) {
        add({
          kind: 'next', title: `Next up: ${sub.name}`, sub: sub.id, tier: t,
          reason: `${TIER_NAME[t]} is open. Try it!`, href: tierHref(sub.id, t),
        });
        break outer;
      }

  return out.slice(0, 3);
}
