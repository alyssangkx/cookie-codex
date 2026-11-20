// Growth-mindset lines on result screens (docs/learning-loop-design.md item 4). The copy lives in
// data/encouragement.json so the owner can edit it; this module only picks a line. No save change.
import copy from '../data/encouragement.json' with { type: 'json' };

export type Band = 'perfect' | 'high' | 'mid' | 'low';
export type Line = { use: 'all' | 'tier'; en: string; zh: string };
export const BANDS = copy.bands as unknown as Record<Band, Line[]>;
/** Chinese-subject results show the English line under the Chinese one up to and including this local date. */
export const BILINGUAL_UNTIL: string = copy.bilingualUntil;

/** perfect = every answer right; high = 80% and over; mid = 50-79%; low = under 50% (and an empty quiz). */
export function band(score: number, total: number): Band {
  if (total > 0 && score >= total) return 'perfect';
  const p = total > 0 ? score / total : 0;
  return p >= 0.8 ? 'high' : p >= 0.5 ? 'mid' : 'low';
}

/** FNV-1a (32 bit): a stable small hash, so the same attempt always gets the same line. */
export function hash(x: string | number): number {
  let h = 0x811c9dc5;
  for (const ch of String(x)) { h ^= ch.charCodeAt(0); h = Math.imul(h, 0x01000193) >>> 0; }
  return h >>> 0;
}

/** The band's line for `seed` (null only if the copy is empty). 'tier' lines only after tier quizzes. A line equal to `avoid` moves to the next one. */
export function pickLine(b: Band, seed: string | number, tier: boolean, avoid?: string, bands = BANDS): Line | null {
  // an edit can leave a band with only 'tier' lines (or none): then any fitting line of another band, then the
  // band's own tier lines
  const fits = (l: Line) => tier || l.use !== 'tier';
  const own = bands[b] ?? [];
  const fit = own.filter(fits);
  const any = fit.length ? fit : Object.values(bands).flat().filter(fits);
  const pool = any.length ? any : own;
  if (!pool.length) return null;
  let k = hash(seed) % pool.length;
  if (avoid !== undefined && pool.length > 1 && pool[k].en === avoid) k = (k + 1) % pool.length;
  return pool[k];
}

type Done = { ts: number; mode: string; score: number; total: number; open?: boolean };
/**
 * The line for the latest finished attempt, never the same as the one the attempt before it showed. Walks the
 * whole finished history (append-only), so every attempt's line is fixed: a reload shows the same line.
 */
export function lineForLast(attempts: Done[], bands = BANDS): Line | null {
  let prev: string | undefined, line: Line | null = null;
  for (const a of attempts) {
    if (a.open) continue;
    line = pickLine(band(a.score, a.total), a.ts, a.mode === 'tier', prev, bands);
    prev = line?.en;
  }
  return line;
}

const localDay = (t: number) => {
  const d = new Date(t);
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
};
/** True while Chinese results should still show the English line underneath (Term 1 2027). */
export const bilingual = (now = Date.now(), until = BILINGUAL_UNTIL) => localDay(now) <= until;
