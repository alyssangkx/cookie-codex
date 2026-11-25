// Pure helpers for the section page and the school list (direction A, owner 24 Nov 2026). Display only: they read the
// save and never write it, so nothing stored changes (no schema bump).
import { TIERS, MILESTONE_NAME, milestoneReached, tierOpen, tierState, isDue, type SaveV1, type Tier } from './store.ts';
import { rewardPreview, type Economy, type Preview } from './crumbs.ts';

/** "epic" -> "Epic", "super-epic" -> "Super epic": the label for a card rarity token (the token itself is the CSS name). */
export const rarityLabel = (r: string) => { const t = r.replace(/-/g, ' '); return t.charAt(0).toUpperCase() + t.slice(1); };

/** The tick used in the cleared state and the stop badges (one definition for the page's build and client code). */
export const TICK_SVG = '<svg viewBox="0 0 24 24" aria-hidden="true" width="16" height="16"><path d="M5 12.5l4.2 4.2L19 7" fill="none" stroke="currentColor" stroke-width="3.2" stroke-linecap="round" stroke-linejoin="round"/></svg>';

/** A stop (card slot) is earned when its milestone was reached on the pool, or when that slot's tier was cleared (a
 *  generated tier cleared before the section became one pool: its card was awarded then). */
export const stopEarned = (s: SaveV1, sub: string, t: Tier) => milestoneReached(s, sub, t) || tierState(s, sub, t).cleared;

/** The tier a child must clear before `t` opens: the nearest playable lower tier (tierOpen skips unplayable ones), or
 *  null when none is below. */
export function tierBelow(t: Tier, playable: Record<Tier, boolean>): Tier | null {
  for (let i = TIERS.indexOf(t) - 1; i >= 0; i--) if (playable[TIERS[i]]) return TIERS[i];
  return null;
}

/**
 * The section page's small numbers, read from the save only (store.ts poolDisplay wrote them at the last quiz end; the
 * pages never fetch a pool list). null when the section has not been played since that field was added. `due` is the
 * stored retest ids whose LIVE state is still a retest due now (so a Daily Review that cleared them shows at once); null
 * when the ids were never stored. `pd`/`pt` only for passage sections.
 */
export function sectionBoxes(s: SaveV1, sub: string, now = Date.now()): { tried: number; due: number | null; passages: { done: number; total: number } | null } | null {
  const st = tierState(s, sub, 'b');
  if (typeof st.tried !== 'number') return null;
  const due = Array.isArray(st.rq) ? st.rq.filter((id) => isDue(s, id, now, true)).length : null;
  return { tried: st.tried, due, passages: typeof st.pt === 'number' && st.pt > 0 ? { done: Math.min(st.pd ?? 0, st.pt), total: st.pt } : null };
}

/** Due retests per pool section for the school list's "N to retest" pill, from each section's stored `rq`; a section
 *  without the field is left out (no pill, never a guess). */
export function dueFromStored(s: SaveV1, subs: string[], now = Date.now()): Record<string, number> {
  const out: Record<string, number> = {};
  for (const sub of subs) { const b = sectionBoxes(s, sub, now); if (b && b.due !== null) out[sub] = b.due; }
  return out;
}

/** A pool section has been started: something counted, or a quiz tried it. One definition for both pages. */
export const sectionStarted = (s: SaveV1, sub: string, counted: number) => counted > 0 || s.attempts.some((a) => a.sub === sub);

/** Which stops count for "what is next", for a pool section: the 1st and 2nd by `stopEarned` (an old generated-tier clear
 *  paid that card), the third only when the pool's own Exam-ready milestone is reached (`ms`), so "Exam-ready" never
 *  rests on an old tier clear. */
export const goalFlags = (s: SaveV1, sub: string): [boolean, boolean, boolean] =>
  [stopEarned(s, sub, 'b'), stopEarned(s, sub, 'i'), milestoneReached(s, sub, 'c')];
/** Exam-ready: the pool's own third milestone is reached. */
export const examReady = (s: SaveV1, sub: string) => milestoneReached(s, sub, 'c');
/** The next stop not yet earned (index 0-2) and how many more counted questions it needs (0 when n already meets it and
 *  only the next finished quiz is missing), or null when all three are earned. Thresholds `at` come from the same total
 *  as `n`. */
export function nextGoal(n: number, at: readonly number[], earned: readonly boolean[]): { i: number; need: number } | null {
  const i = earned.findIndex((e) => !e);
  return i < 0 ? null : { i, need: Math.max(0, at[i] - n) };
}
/** The tier records both section pages build: cleared, and open (the tier below is cleared, or unplayable). */
export function tierFlags(s: SaveV1, sub: string, playable: Record<Tier, boolean>): { cleared: Record<Tier, boolean>; open: Record<Tier, boolean> } {
  const cleared = Object.fromEntries(TIERS.map((t) => [t, tierState(s, sub, t).cleared])) as Record<Tier, boolean>;
  const open = Object.fromEntries(TIERS.map((t) => [t, tierOpen(s, sub, t, playable)])) as Record<Tier, boolean>;
  return { cleared, open };
}

/** How full each of the three bar segments is (0-100): the bar runs 0 to the last stop, one segment per stop. */
export const trailFill = (n: number, at: readonly number[]): number[] => {
  let prev = 0;
  return at.map((a) => {
    const span = a - prev, from = prev;
    prev = a;
    return span > 0 ? Math.max(0, Math.min(100, (100 * (n - from)) / span)) : n >= a ? 100 : 0;
  });
};

/** The tier a classic section should train next: the first playable tier not cleared whose lower tier allows it
 *  (`open`), else null (every playable tier cleared, or none playable). */
export function nextTier(cleared: Record<Tier, boolean>, playable: Record<Tier, boolean>, open: Record<Tier, boolean>): Tier | null {
  return TIERS.find((t) => playable[t] && !cleared[t] && open[t]) ?? null;
}

/** "Starts with your N retests." for the note under Start: the quiz takes at most `cap` due retests first. Empty for 0. */
export const retestNote = (due: number, cap = 3) => {
  const n = Math.min(due, cap);
  return n ? `Starts with your ${n} retest${n === 1 ? '' : 's'}.` : '';
};

/** "T of U tries left today." or empty for an unlimited account (left is Infinity). */
export const triesNote = (left: number, per: number) => (Number.isFinite(left) ? `${left} of ${per} tries left today.` : '');

/** The stops a section has reached, as the section page counts them: for a pool the 1st and 2nd by `stopEarned`, the third
 *  by the pool's own milestone (`goalFlags`); for a classic section the tiers cleared. Only playable ones are counted. */
export function stopCount(s: SaveV1, sub: string, pool: boolean, playable: Record<Tier, boolean>): { reached: number; of: number } {
  const flags = pool ? goalFlags(s, sub) : TIERS.map((t) => tierState(s, sub, t).cleared);
  const open = TIERS.filter((t) => playable[t]);
  return { reached: open.filter((t) => flags[TIERS.indexOf(t)]).length, of: open.length };
}

// ---- wording (owner review, 24 Nov 2026): say what was given, not what was hoped for
/** "earned" for a new card, "reached" for a star or nothing. `reward` is the quiz result's reward (null: nothing given). */
export const stopWord = (reward: { dup: boolean } | null | undefined) => (reward && !reward.dup ? 'earned' : 'reached');
/** "1st card earned" / "1st card reached: +1 star on <card>" / "1st card reached". */
export function stopLine(t: Tier, reward: { dup: boolean } | null | undefined, cardName = ''): string {
  const name = MILESTONE_NAME[t];
  if (!reward) return `${name} reached`;
  return reward.dup ? `${name} reached: +1 star on ${cardName}` : `${name} earned`;
}
/** The note when the count already meets the next stop and only a finished quiz is missing. */
export const finishLine = (t: Tier) => `Finish a quiz to reach ${MILESTONE_NAME[t]}.`;
/** The pool verdict count, in the section page's words: "62 of 300 blanks right". */
export const poolRightText = (counted: number, total: number, cloze: boolean) => `${counted} of ${total} ${cloze ? 'blanks' : 'questions'} right`;
/** The school list's chip and topic header: "1 of 3 stops reached". */
export const stopsText = (reached: number, of: number) => `${reached} of ${of} stops reached`;

/**
 * What each UNEARNED slot would give, in slot order, treating the cards earlier slots would give as already owned (so two
 * slots of one rarity do not both preview the same replacement). `slots` are in order b, i, c; an earned slot is null.
 */
export function previewSlots(s: SaveV1, slots: { slug: string; earned: boolean }[], eco: Economy): (Preview | null)[] {
  const view = { ...s, cards: { ...s.cards } } as SaveV1;
  return slots.map((x) => {
    if (x.earned) return null;
    const p = rewardPreview(view, x.slug, eco);
    if (p.kind === 'card') view.cards[p.slug] = { stars: 1, srcSub: '', srcTier: 'b', acc: 0, last: 0 };
    return p;
  });
}
