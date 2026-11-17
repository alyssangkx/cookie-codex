// Pure edits the admin page applies to the TEST PLAYER's save (never a real child's: the server refuses an
// admin write to anyone else, see push_save). Each returns a new object; none touches storage.
import type { SaveV1, Tier } from './store';

const DAY = 86_400_000;
const pad = (n: number) => String(n).padStart(2, '0');
/** 'YYYY-MM-DD' moved by n days (local calendar, like store.ts dayKey). */
export function shiftKey(key: string, n: number): string {
  const [y, m, d] = key.split('-').map(Number);
  const t = new Date(y, m - 1, d + n);
  return `${t.getFullYear()}-${pad(t.getMonth() + 1)}-${pad(t.getDate())}`;
}

/** Make everything in the save happen `days` days earlier, as if the clock jumped forward: day keys, pass days, due dates, timestamps. */
export function jumpClock(s: SaveV1, days = 1): SaveV1 {
  const out: SaveV1 = JSON.parse(JSON.stringify(s));
  out.createdAt = s.createdAt - days * DAY;
  out.days = Object.fromEntries(Object.entries(s.days).map(([k, v]) => [shiftKey(k, -days), v]));
  for (const subs of Object.values(out.progress))
    for (const t of Object.values(subs)) if (t) t.passes = t.passes.map((k) => shiftKey(k, -days));
  for (const q of Object.values(out.questions)) if (q.due > 0) q.due -= days * DAY;
  for (const a of out.attempts) a.ts -= days * DAY;
  for (const c of Object.values(out.cards)) if (c.last) c.last -= days * DAY;
  if (out.streak.lastDay) out.streak.lastDay = shiftKey(out.streak.lastDay, -days);
  if (out.streak.freezeUsedWeek) out.streak.freezeUsedWeek = shiftKey(out.streak.freezeUsedWeek, -days);
  return out;
}

/** Forget a tier's passes and clear flag, and drop the card that tier awarded. */
export function resetTier(s: SaveV1, sub: string, tier: Tier): SaveV1 {
  const out: SaveV1 = JSON.parse(JSON.stringify(s));
  if (out.progress[sub]) delete out.progress[sub][tier];
  for (const [slug, c] of Object.entries(out.cards)) if (c.srcSub === sub && c.srcTier === tier) delete out.cards[slug];
  return out;
}

/** Give a card (a duplicate adds a star, max 5). */
export function grantCard(s: SaveV1, slug: string, sub: string, tier: Tier, now = Date.now()): SaveV1 {
  const out: SaveV1 = JSON.parse(JSON.stringify(s));
  const have = out.cards[slug];
  if (have) have.stars = Math.min(5, have.stars + 1);
  else out.cards[slug] = { stars: 1, srcSub: sub, srcTier: tier, acc: 100, last: now };
  return out;
}
