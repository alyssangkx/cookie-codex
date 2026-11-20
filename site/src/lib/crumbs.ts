// Crumbs: the coin of the game economy (docs/game-economy.md; owner's answers 20 Nov 2026, all as recommended).
// Pure rules only: no storage. store.ts calls these from finishQuiz and the purchase wrappers.
import type { SaveV1 } from './store.ts';

/** PSLE AL cut-offs, in percent: band 1 needs 90, band 2 needs 85, ... band 7 needs 20, below that band 8. */
const AL_CUT = [90, 85, 80, 75, 65, 45, 20];
/** Crumbs per band (index 0 = AL1). */
const AL_CRUMBS = [8, 7, 6, 5, 4, 3, 2, 1];
export const PERFECT_BONUS = 4;
export const PAPER_MULT = 3; // the most a paper multiplies by (30+ questions)

/** AL band 1-8 of a score (integer arithmetic, so 17/20 is exactly 85%). */
export function alBand(score: number, total: number): number {
  if (!(total > 0)) return 8;
  const i = AL_CUT.findIndex((cut) => 100 * score >= cut * total);
  return i < 0 ? 8 : i + 1;
}

/** Crumbs for one finished quiz: by AL band, +4 for a perfect score, at least 1. A WA/SA paper scales with its length:
 * x(questions / 10), at most x3 (10 questions x1, 20 x2, 30+ x3), so a paper never pays more per question than a quiz. */
export function quizCrumbs(score: number, total: number, mode: 'tier' | 'review' | 'paper'): number {
  const base = AL_CRUMBS[alBand(score, total) - 1] + (total > 0 && score === total ? PERFECT_BONUS : 0);
  return mode === 'paper' ? Math.max(1, Math.round(base * Math.min(PAPER_MULT, total / 10))) : base;
}

// ---------------------------------------------------------------- ledger

export const LEDGER_MAX = 50; // ledger entries kept (the parent page shows them); the balance is a running total
/** Why Crumbs moved: a finished tier quiz, Daily Review or WA/SA paper; a retest step passed; the daily goal; a streak
 * week; a bonus when a card's rarity has nothing left to give; a card or a star bought in the shop. */
export type CrumbWhy = 'quiz' | 'review' | 'paper' | 'retest' | 'goal' | 'week' | 'bonus' | 'buy' | 'star';
export const CRUMB_WHYS: readonly CrumbWhy[] = ['quiz', 'review', 'paper', 'retest', 'goal', 'week', 'bonus', 'buy', 'star'];
/** n: Crumbs added (negative for a purchase); bal: the balance after it; slug: the card bought or starred; note: the
 * sub-topic|tier or paper topics; test: earned or spent on the unlimited test account (kept out of parent totals). */
export interface LedgerEntry { ts: number; n: number; bal: number; why: CrumbWhy; slug?: string; note?: string; test?: true }
export interface Purchase { ts: number; slug: string; kind: 'card' | 'star'; price: number; stars: number; test?: true }
/**
 * The optional `crumbs` field of a save (added 20 Nov 2026 with no schema bump, ADR 0002: an older tab keeps it as an
 * unknown field). bal: spendable balance; earned/spent: lifetime totals; test: lifetime Crumbs earned on the unlimited
 * test account; log: the last LEDGER_MAX entries; buys: every purchase. goalDay/week: the last day and week a goal or
 * streak bonus was paid (each pays once); topics: competency topics whose Super Epic has been awarded; legWeek: the week
 * (Monday) a paper last gave a Legendary (one a week); subjects: subjects whose Legendary has been awarded.
 */
export interface Crumbs {
  bal: number; earned: number; spent: number; test: number;
  log: LedgerEntry[]; buys: Purchase[];
  goalDay?: string; week?: string; topics?: string[]; legWeek?: string; subjects?: string[];
}
type WithCrumbs = { crumbs?: Crumbs };

/** The save's Crumbs, created empty the first time they are needed. */
export function crumbsOf(s: WithCrumbs): Crumbs {
  return (s.crumbs ??= { bal: 0, earned: 0, spent: 0, test: 0, log: [], buys: [] });
}
export const balanceOf = (s: WithCrumbs) => s.crumbs?.bal ?? 0;

function addEntry(c: Crumbs, e: Omit<LedgerEntry, 'bal'>) {
  c.bal += e.n;
  const entry: LedgerEntry = { ts: e.ts, n: e.n, bal: c.bal, why: e.why };
  if (e.slug) entry.slug = e.slug;
  if (e.note) entry.note = e.note;
  if (e.test) entry.test = true;
  c.log.push(entry);
  if (c.log.length > LEDGER_MAX) c.log.splice(0, c.log.length - LEDGER_MAX);
}

/** Add `n` (> 0) Crumbs. Coins never expire or drop; only a purchase spends them. */
export function earn(s: WithCrumbs, n: number, why: CrumbWhy, now: number, o: { test?: boolean; slug?: string; note?: string } = {}) {
  if (!(n > 0)) return 0;
  const c = crumbsOf(s);
  c.earned += n;
  if (o.test) c.test += n;
  addEntry(c, { ts: now, n, why, slug: o.slug, note: o.note, test: o.test ? true : undefined });
  return n;
}

// ---------------------------------------------------------------- cards and the shop

/** Build-time card data a page passes in: the per-rarity order from rewards.json (`rarityOrder`), each card's rarity,
 * and the competency groups (competencyGroups): topics for Super Epics, subjects for the subject Legendary. */
export interface Economy {
  order: Record<string, string[]>;
  rarityOf: (slug: string) => string | undefined;
  topics?: Record<string, string[]>;
  subjects?: Record<string, string[]>;
}
type Card = SaveV1['cards'][string];
type Save = WithCrumbs & { cards: Record<string, Card> };

/** Shop prices; a rarity not listed here is not for sale. */
export const PRICE: Record<string, number> = { common: 30, rare: 60, special: 120, epic: 120 };
export const MAX_STARS = 5;
export const SHOP_ACC = 50; // card power starts here for a bought card (power reflects retention; nothing was learnt to earn it)
export const priceOf = (eco: Economy, slug: string): number | undefined => PRICE[eco.rarityOf(slug) ?? ''];

export type BuyResult = { ok: true; price: number } | { ok: false; reason: 'owned' | 'poor' | 'not-for-sale' | 'cards-left' | 'stale' | 'max' | 'not-owned' };

/** The first card of `rarity` in the fixed order that the save does not own yet. */
export const nextUnowned = (s: Save, rarity: string, eco: Economy) => (eco.order[rarity] ?? []).find((x) => !s.cards[x]);

function charge(s: Save, price: number, why: 'buy' | 'star', slug: string, stars: number, now: number, test?: boolean) {
  const c = crumbsOf(s);
  c.spent += price;
  addEntry(c, { ts: now, n: -price, why, slug, test: test ? true : undefined });
  const p: Purchase = { ts: now, slug, kind: why === 'buy' ? 'card' : 'star', price, stars };
  if (test) p.test = true;
  c.buys.push(p);
}

/** Buy the exact card the child picked. Refused (nothing changes) when it is owned, not for sale, or too dear. */
export function buyCard(s: Save, slug: string, eco: Economy, now: number, test?: boolean): BuyResult {
  const price = priceOf(eco, slug);
  if (price === undefined) return { ok: false, reason: 'not-for-sale' };
  if (s.cards[slug]) return { ok: false, reason: 'owned' };
  if (balanceOf(s) < price) return { ok: false, reason: 'poor' };
  s.cards[slug] = { stars: 1, srcSub: 'shop', srcTier: 'b', acc: SHOP_ACC, last: now };
  charge(s, price, 'buy', slug, 1, now, test);
  return { ok: true, price };
}

/**
 * Buy one star for an owned card, at its rarity's price, once every card of that rarity is owned (owner's answer 6a).
 * `from` is the star count the page showed: if the card already has more (the same click landed twice, or another tab
 * bought it), the purchase is refused as stale instead of charging again.
 */
export function buyStar(s: Save, slug: string, from: number, eco: Economy, now: number, test?: boolean): BuyResult {
  const price = priceOf(eco, slug);
  if (price === undefined) return { ok: false, reason: 'not-for-sale' };
  const card = s.cards[slug];
  if (!card) return { ok: false, reason: 'not-owned' };
  if (nextUnowned(s, eco.rarityOf(slug)!, eco)) return { ok: false, reason: 'cards-left' };
  if (card.stars >= MAX_STARS) return { ok: false, reason: 'max' };
  if (card.stars !== from) return { ok: false, reason: 'stale' };
  if (balanceOf(s) < price) return { ok: false, reason: 'poor' };
  card.stars++;
  charge(s, price, 'star', slug, card.stars, now, test);
  return { ok: true, price };
}

/** Crumbs given with a star when a rarity has no card left to give: half the shop price, or 60 for the rarities that
 * are not for sale (Super Epic, Legendary). */
export const NOTHING_LEFT_BONUS = 60;
export const bonusFor = (rarity: string | undefined) => (PRICE[rarity ?? ''] ? PRICE[rarity!] / 2 : NOTHING_LEFT_BONUS);

export type Preview = { kind: 'card'; slug: string; replaces?: string } | { kind: 'star'; slug: string; crumbs: number };
/**
 * What clearing a slot gives right now (docs/game-economy.md section 1): its card if not owned; else the next unowned
 * card of the same rarity in the fixed order (a replacement); else a star on the slot card plus a Crumbs bonus. The tier
 * page shows exactly this, and store.ts award() gives exactly this.
 */
export function rewardPreview(s: Save, slot: string, eco: Economy): Preview {
  if (!s.cards[slot]) return { kind: 'card', slug: slot };
  const rarity = eco.rarityOf(slot);
  const next = rarity ? nextUnowned(s, rarity, eco) : undefined;
  return next ? { kind: 'card', slug: next, replaces: slot } : { kind: 'star', slug: slot, crumbs: bonusFor(rarity) };
}

// ---------------------------------------------------------------- achievement-only cards

/** Legendary: a WA/SA paper at AL1-AL2 (owner's answer 5a). A paper needs this many questions to count as a WA/SA
 * paper (the builder allows 5 to 40; 20 is its default). */
export const LEGENDARY_MIN_QUESTIONS = 20;
export const LEGENDARY_MIN_TOPICS = 3; // a paper must mix at least this many topics
export const LEGENDARY_MAX_BAND = 2;
export const MIN_GROUP_SUBS = 2; // a competency topic needs this many sub-topics with a playable Competent tier

/**
 * Competency groups for the achievement cards. `group` is worked out by the caller (train.ts): the topic for Math and
 * Science, the PSLE paper booklet for English and Chinese (their syllabus topics are single paper sections). A group's
 * members are its sub-topics with a playable Competent tier, and a group counts only with MIN_GROUP_SUBS or more (one
 * clear must never earn a Super Epic). A subject counts for the subject Legendary only when EVERY one of its sub-topics
 * has a playable Competent tier (a partly built subject cannot earn it) and it has 2 or more groups; its members are
 * all its sub-topics.
 */
export function competencyGroups(subs: { id: string; school: string; group: string; playableC: boolean }[]) {
  const by = new Map<string, { school: string; ids: string[] }>();
  for (const s of subs) {
    if (!s.playableC) continue;
    if (!by.has(s.group)) by.set(s.group, { school: s.school, ids: [] });
    by.get(s.group)!.ids.push(s.id);
  }
  const topics: Record<string, string[]> = {};
  const groupsPer = new Map<string, number>();
  for (const [key, g] of by) {
    if (g.ids.length < MIN_GROUP_SUBS) continue;
    topics[key] = g.ids;
    groupsPer.set(g.school, (groupsPer.get(g.school) ?? 0) + 1);
  }
  const subjects: Record<string, string[]> = {};
  for (const school of new Set(subs.map((s) => s.school))) {
    const all = subs.filter((s) => s.school === school);
    if (all.every((s) => s.playableC) && (groupsPer.get(school) ?? 0) >= 2) subjects[school] = all.map((s) => s.id);
  }
  return { topics, subjects };
}
/** How the cards that cannot be bought are earned (shown in the shop and My House). */
export const EARN_RULE: Record<string, string> = {
  'super-epic': `Clear the Competent tier of every sub-topic in a topic that has Competent questions ready, one card per topic. A topic counts once at least ${MIN_GROUP_SUBS} of its sub-topics have Competent questions ready; for English and Chinese a topic is a paper booklet`,
  legendary: `Score 85% or more (AL1 or AL2) on a WA/SA paper of ${LEGENDARY_MIN_QUESTIONS}+ questions drawn from ${LEGENDARY_MIN_TOPICS}+ topics (one a week), or clear the Competent tier of every sub-topic in a subject (only once every sub-topic of that subject has Competent questions ready)`,
  ancient: 'Get your legendary cards to 2 stars or more, then pass the Ancient Trial (coming later)',
  dragon: 'Reach 30 / 100 study days',
  beast: 'Beat a school monster (coming later)',
  witch: 'Fix 150 old mistakes',
};

/**
 * What an achievement of `rarity` gives right now: the next unowned card of that rarity in the fixed order, else a star
 * on the owned card of that rarity with the fewest stars (the first in the order on a tie) plus NOTHING_LEFT_BONUS.
 * Deterministic, so the shop can preview it. Null only when the rarity has no cards.
 */
export function achievementPreview(s: Save, rarity: string, eco: Economy): Preview | null {
  const next = nextUnowned(s, rarity, eco);
  if (next) return { kind: 'card', slug: next };
  const list = eco.order[rarity] ?? [];
  if (!list.length) return null;
  const slug = list.reduce((best, x) => (s.cards[x].stars < s.cards[best].stars ? x : best), list[0]);
  return { kind: 'star', slug, crumbs: bonusFor(rarity) };
}

/** The client side of /data/economy.json (train.ts economyData). */
export interface EconomyData {
  order: Record<string, string[]>; topics: Record<string, string[]>; topicNames: Record<string, string>; subjects: Record<string, string[]>;
  cards: Record<string, { name: string; image: string; rarity: string }>; milestones: Record<string, string[]>;
}
export const toEconomy = (d: Pick<EconomyData, 'order' | 'topics' | 'subjects' | 'cards'>): Economy =>
  ({ order: d.order, topics: d.topics, subjects: d.subjects, rarityOf: (slug) => d.cards[slug]?.rarity });
