// Editing answered whole (owner, 25 Nov 2026): the passage as the paper prints it, every asked word underlined with its
// number and a box beside it for the correction; one Submit marks them all, like the typed cloze passages. A row's stem
// carries each asked word as `{{39|manufakchered}}` (number | the printed, wrong word); the quiz page escapes the stem
// first, then these helpers place the boxes, or the corrections after marking. Pure, so they are tested.
import type { CxMark } from './pastpaper.ts';

const MARK = /\{\{\s*(\d{1,3})\s*\|\s*([^{}|]*?)\s*\}\}/g;

/** Every asked word of a passage, number -> the printed word (works on raw or escaped text). */
export function editingMarks(text: string): Map<number, string> {
  const out = new Map<number, string>();
  for (const m of text.matchAll(MARK)) if (!out.has(Number(m[1]))) out.set(Number(m[1]), m[2]);
  return out;
}

/** The passage with each `{{n|word}}` replaced by what `render(n, word)` returns (word as it stands in the text). */
export const editingHtml = (html: string, render: (n: number, word: string) => string): string =>
  html.replace(MARK, (_all, n: string, w: string) => render(Number(n), w));

/** The printed word, underlined, with its number: also how an item outside this quiz reads before marking. */
export const editWord = (n: number, word: string) => `<span class="vc-u"><b>(${n})</b> <u>${word}</u></span>`;

/** One asked word with its correction box beside it. The number stays with its word and the arrow with its box, but the
 *  line may break between the word and the box (<wbr>), so the paragraph wraps like text instead of jumping a whole
 *  word-and-box group to the next line (owner, 25 Nov 2026). */
export const editAsk = (n: number, word: string, boxHtml: string) =>
  `<span class="ask-inline ed-ask">${editWord(n, word)}<wbr><span class="ed-pair"><span class="ed-arrow" aria-hidden="true">→</span>${boxHtml}</span><span class="cz-note" aria-live="polite"></span></span>`;

/**
 * The passage after marking, every mistake in place: the printed word struck, then what the child typed (struck, only when it
 * is wrong and not the same word again), then the correct word in bold; a right answer shows the printed word struck and
 * the right word plainly; a word not in this quiz shows its correction in grey; any other stays as printed.
 * `placed` lists the numbers found in the passage, so a mistake the passage cannot show is listed by the caller.
 */
export function editCorrections(html: string, marks: ReadonlyMap<number, CxMark>, esc: (s: string) => string): { html: string; placed: Set<number> } {
  const placed = new Set<number>();
  const out = editingHtml(html, (n, word) => {
    const m = marks.get(n);
    if (!m) return editWord(n, word);
    placed.add(n);
    const was = `<del class="ed-was">${word}</del>`;
    if (m.kind === 'right') return `<span class="ed-fix"><b>(${n})</b> ${was} <span class="filled">${esc(m.answer)}</span></span>`;
    if (m.kind === 'given') return `<span class="ed-fix"><b>(${n})</b> ${was} <span class="filled given" title="not in this quiz">${esc(m.answer)}</span></span>`;
    const typed = m.typed == null ? '' : m.typed.trim();
    const same = esc(typed).toLowerCase() === word.trim().toLowerCase(); // the printed word typed again: shown once
    const yours = m.typed == null || same ? '' : typed ? `<del class="cx-typed">${esc(typed)}</del> ` : '<span class="cx-none">(no answer)</span> ';
    return `<mark class="cx-fix"><b>(${n})</b> ${was} ${yours}<strong>${esc(m.answer)}</strong></mark>`;
  });
  return { html: out, placed };
}
