// Passage sets answered whole (owner, 26 Nov 2026, docs/passage-sets-ui.md): one screen per set, every question answered,
// one Submit. Pure helpers for the MCQ cloze chips, the dialogue phrase bank and the text passage; the quiz page draws them.

/** A blank in a passage: Chinese "（3）＿＿＿＿" or English "(3) ____" ("(3) ________" when asked). */
const BLANK_SRC = '（(\\d{1,3})）＿{2,}|\\((\\d{1,3})\\) ?_{4,}';

/** Replace every blank in already-escaped HTML. `fn` gets the blank's number and whether it is the Chinese form; the
 *  blanks found come back so the caller can list a question the passage does not show. */
export function replaceBlanks(html: string, fn: (n: number, zh: boolean) => string): { html: string; found: Set<number> } {
  const found = new Set<number>();
  const out = html.replace(new RegExp(BLANK_SRC, 'g'), (_all, zh: string | undefined, en: string | undefined) => {
    const n = Number(zh ?? en);
    found.add(n);
    return fn(n, zh != null);
  });
  return { html: out, found };
}

/** Does the stem hold this question's own blank? Then the passage is text and the options go inline; else the stem is one
 *  sentence under a page image and the question keeps its option list. */
export function hasOwnBlank(stem: string, seq: number | null | undefined): boolean {
  if (seq == null) return false;
  return new RegExp(`（${seq}）＿|\\(${seq}\\) ?_{2}`).test(stem);
}

/** An old dialogue stem ends with a line "第（K）空…" naming the asked blank: the phrase bank makes it redundant. */
export const dropAskedLine = (stem: string): string => stem.replace(/\n*第（\d+）空[^\n]*$/, '');

/** A text figure: paragraphs separated by blank lines, every line escaped. */
export function textFigureHtml(text: string, esc: (s: string) => string): string {
  const paras = text.replace(/\r\n?/g, '\n').split(/\n\s*\n/).map((p) => p.trim()).filter(Boolean);
  return `<div class="qfig-text">${paras.map((p) => `<p>${esc(p).replace(/\n/g, '<br>')}</p>`).join('')}</div>`;
}

// ---- state: blank number -> a choice (cloze chips: the row's option index; dialogue: the phrase index in the bank)
export type Picks = ReadonlyMap<number, number>;

/** Tap a chip (or another chip of the same blank): that blank now holds this option. */
export const choose = (picks: Picks, seq: number, k: number): Map<number, number> => new Map(picks).set(seq, k);

/** Put a phrase on a blank. A phrase placed elsewhere leaves that blank; whatever the blank held returns to the bank. */
export function place(picks: Picks, phrase: number, seq: number): Map<number, number> {
  const next = new Map(picks);
  for (const [s, p] of next) if (p === phrase) next.delete(s);
  next.set(seq, phrase);
  return next;
}
/** Tap a filled blank: its phrase goes back to the bank. */
export function unplace(picks: Picks, seq: number): Map<number, number> {
  const next = new Map(picks);
  next.delete(seq);
  return next;
}
/** Phrases on a blank now (greyed in the bank). */
export const usedPhrases = (picks: Picks): Set<number> => new Set(picks.values());
/** Blanks (in passage order) with nothing on them. */
export const emptyBlanks = (seqs: readonly number[], picks: Picks): number[] => seqs.filter((s) => !picks.has(s));
/** The first empty blank after `from` (wrapping round), or null when all are filled. */
export function nextEmpty(seqs: readonly number[], picks: Picks, from: number): number | null {
  const at = seqs.indexOf(from);
  const order = [...seqs.slice(at + 1), ...seqs.slice(0, at + 1)];
  return order.find((s) => !picks.has(s)) ?? null;
}
/** The option index of a phrase in a row's options (rows share the 8 phrases but need not share their order); -1 when absent. */
export const optionIndex = (options: readonly string[], phrase: string): number => options.indexOf(phrase);

/** A blank's result for the in-place passage. */
export type SetMark = { kind: 'right' | 'wrong' | 'given'; picked?: string | null; answer: string };

/** The passage after Submit: right = the child's word in green, wrong = the pick struck out and the answer in bold (a blank
 *  left empty says so), given = a blank not in this quiz, grey. Runs on escaped HTML; a blank with no mark stays a blank. */
export function setCorrections(html: string, marks: ReadonlyMap<number, SetMark>, esc: (s: string) => string): { html: string; placed: Set<number> } {
  const placed = new Set<number>();
  const r = replaceBlanks(html, (n, zh) => {
    const m = marks.get(n);
    const lead = zh ? `（${n}）` : `(${n}) `;
    if (!m) return zh ? `（${n}）＿＿＿＿` : `(${n}) ____`;
    placed.add(n);
    if (m.kind === 'right') return `${lead}<span class="filled">${esc(m.answer)}</span>`;
    if (m.kind === 'given') return `${lead}<span class="filled given" title="not in this quiz">${esc(m.answer)}</span>`;
    const yours = m.picked ? `<del>${esc(m.picked)}</del> ` : '<span class="cx-none">(no answer)</span> ';
    return `<mark class="cx-fix">${lead}${yours}<strong>${esc(m.answer)}</strong></mark>`;
  });
  return { html: r.html, placed };
}
