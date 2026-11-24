// A typed cloze passage answered whole (owner, 24 Nov 2026): every blank typed, one Submit marks them all; the Grammar
// Cloze word box is a grid whose words strike through as the child ticks them.

/** The word box line a Grammar Cloze stem starts with ("Word box: a · and · at\n\n..."): its words and the stem without it. */
export function wordBox(stem: string): { words: string[]; rest: string } {
  const m = /^Word box: (.*)\n+/.exec(stem);
  return m ? { words: m[1].split(' · ').map((w) => w.trim()).filter(Boolean), rest: stem.slice(m[0].length) } : { words: [], rest: stem };
}

const key = (w: string) => w.trim().toLowerCase().replace(/[’`]/g, "'");

/** Which box words are struck by the ticked answers (in tick order), and a note per ticked answer: 'ok' (struck a word),
 *  'not-in-box', or 'used' (its word is already struck). Notes only; nothing is refused (owner: note, but allow). */
export function strikes(words: readonly string[], ticked: readonly string[]): { struck: Set<number>; notes: ('ok' | 'not-in-box' | 'used')[] } {
  const struck = new Set<number>();
  const notes = ticked.map((t) => {
    const all = words.map((w, k) => (key(w) === key(t) ? k : -1)).filter((k) => k >= 0);
    if (!all.length) return 'not-in-box' as const;
    const free = all.find((k) => !struck.has(k));
    if (free == null) return 'used' as const;
    struck.add(free);
    return 'ok' as const;
  });
  return { struck, notes };
}

/** The end (exclusive) of the run of quiz items from i that belong to the same whole-passage group (`group` gives an
 *  item's group when it is a typed cloze blank, else null): one screen, one Submit. */
export function passageEnd(ids: readonly string[], i: number, group: (id: string) => string | null): number {
  const g = group(ids[i]);
  let j = i + 1;
  if (g != null) while (j < ids.length && group(ids[j]) === g) j++;
  return j;
}
