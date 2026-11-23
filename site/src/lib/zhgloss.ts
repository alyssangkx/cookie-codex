// Pinyin and English meanings for Chinese MCQ options (owner, 23 Nov 2026), from /zh-gloss.json
// (scripts/quiz/chinese/build_gloss.py, CC-CEDICT, CC BY-SA 4.0). Pure: the quiz page fetches the file and renders.
// 字形 (chi-zixing-form): the option character's reading and the word it forms with the characters around the blank
// (`windows` mirrors build_gloss.py); every other option that is a word, an idiom or a connective pair is looked up whole.

export type Gloss = { c: Record<string, [string, string][]>; w: Record<string, [string, string]> };
export type GlossLine = { text: string; py: string; mean: string };

const BLANK = /[_＿]{2,}|（\s*）|\(\s*\)/;
const STOP = /[，。！？、；：“”‘’（）()《》\s,.!?;:]/;
const CJK = /^[㐀-鿿]+$/;
const PARTS = /[….]{2,}|……|…|、|\//;
const SKIP = new Set(['chi-pinyin-sound', 'chi-juzi-choose', 'chi-dialogue-mcq', 'chi-yuedu-open-text']);

/** Every word of 2-4 characters around the blank that holds the whole option, longest first (as build_gloss.py). */
export function windows(left: string, opt: string, right: string, longest = 4): string[] {
  const l = left.split(STOP).pop()!.slice(-3), r = right.split(STOP)[0].slice(0, 3);
  const ctx = l + opt + r, a = l.length, b = a + opt.length, out: string[] = [];
  for (let n = longest; n > 1; n--)
    for (let i = Math.max(0, b - n); i <= Math.min(a, ctx.length - n); i++) if (i <= a && i + n >= b) out.push(ctx.slice(i, i + n));
  return out;
}

const strip = (o: string) => o.replace(/^\s*[(（]?[1-4][)）.．、]?\s*/, '').trim();

/** The option's words: itself, or the parts of a connective pair ("因为……所以……"). */
export function optionWords(o: string): string[] {
  const s = strip(o);
  if (CJK.test(s) && s.length <= 8) return [s];
  const parts = s.split(PARTS).map((x) => x.trim()).filter(Boolean);
  return parts.length > 1 ? parts.filter((x) => CJK.test(x) && x.length <= 8) : [];
}

/** A character's reading: the one whose syllable the word uses, else its first. */
function charLine(g: Gloss, ch: string, wordPy?: string, at = 0): GlossLine | null {
  const rs = g.c[ch];
  if (!rs?.length) return null;
  const syl = wordPy?.split(' ')[at];
  const r = (syl && rs.find(([py]) => py === syl)) || rs[0];
  return { text: ch, py: r[0], mean: r[1] };
}

/** The lines to show for one option of a question (empty when nothing applies). */
export function glossOption(g: Gloss, sub: string, stem: string, option: string): GlossLine[] {
  if (SKIP.has(sub)) return [];
  const o = strip(option);
  if (sub === 'chi-zixing-form') {
    const m = BLANK.exec(stem);
    const w = m ? windows(stem.slice(0, m.index), o, stem.slice(m.index + m[0].length)).find((x) => x.length > o.length && g.w[x]) : undefined;
    const lines: GlossLine[] = [];
    if (o.length === 1) {
      const c = charLine(g, o, w ? g.w[w][0] : undefined, w ? w.indexOf(o) : 0);
      if (c) lines.push(c);
    }
    if (w) lines.push({ text: w, py: g.w[w][0], mean: g.w[w][1] });
    return lines;
  }
  return optionWords(o).flatMap((x) => (x.length === 1 ? [charLine(g, x)].filter((l): l is GlossLine => !!l)
    : g.w[x] ? [{ text: x, py: g.w[x][0], mean: g.w[x][1] }] : []));
}
