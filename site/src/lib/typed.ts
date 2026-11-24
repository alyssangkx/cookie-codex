/**
 * Typed answers (owner, 24 Nov 2026: Synthesis & Transformation first, then Grammar Cloze, Editing, Comprehension Cloze).
 * A typed past-paper question (migration 015) has no options: a scaffold, the answer line with its printed words and
 * blanks ("However ____, I still did not go to the party."), and the accepted answers as whole sentences. The child types
 * into each blank; the sentence they made is compared with every accepted one.
 *
 * What counts: the words and their order, and apostrophes inside words (don't / dont differ). What does not: capitals,
 * spacing, curly or straight quotes, and punctuation between words (commas, full stops, quotation marks).
 * ponytail: lenient on punctuation on purpose (a P6 child loses no mark for a comma here); tighten norm() if the owner
 * wants commas or quotation marks marked.
 */

export const BLANK = /_{2,}/g; // for replace/split/match only: .test() on a /g regex keeps lastIndex between calls
const HAS_BLANK = /_{2,}/;

/** The sentence the child made: each blank filled with its box, in order; with no scaffold, the one box alone. */
export function compose(scaffold: string | null | undefined, parts: string[]): string {
  if (!scaffold || !HAS_BLANK.test(scaffold)) return (parts[0] ?? '').trim();
  let i = 0;
  return scaffold.replace(BLANK, () => (parts[i++] ?? '').trim());
}

/** The comparable form of an answer: letters and digits of any script, apostrophes inside a word or after a plural's s
 * (students' bags), and hyphens inside a word (en and em dashes too: well–known). */
export function norm(s: string): string {
  return s.normalize('NFKC').toLowerCase()
    .replace(/[\u2018\u2019\u02bc`]/g, "'").replace(/[\u201c\u201d]/g, '"')
    .replace(/(?<=[\p{L}\p{N}])[\u2010-\u2015](?=[\p{L}\p{N}])/gu, '-') // a dash inside a word is a hyphen
    .replace(/(?<![\p{L}\p{N}])-|-(?![\p{L}\p{N}])/gu, ' ') // a spaced dash is punctuation
    // a quote mark: not inside a word, and not a plural possessive (an apostrophe right after a word's final s)
    .replace(/(?<![\p{L}\p{N}])'|(?<=[\p{L}\p{N}])(?<!s)'(?![\p{L}\p{N}])/gu, ' ')
    .replace(/[^\p{L}\p{N}'\s-]/gu, ' ')
    .replace(/\s+/g, ' ').trim();
}

/** Right when the sentence matches one accepted answer; an empty box is never right. */
export function typedOk(scaffold: string | null | undefined, parts: string[], accept: readonly string[]): boolean {
  if (!parts.length || parts.some((p) => !p.trim())) return false;
  const mine = norm(compose(scaffold, parts));
  return mine !== '' && accept.some((a) => norm(a) === mine); // an answer of only symbols matches nothing
}

/** The scaffold as HTML with a text box in each blank (escaped by the caller's esc). */
export function scaffoldHtml(scaffold: string | null | undefined, esc: (s: string) => string): string {
  const box = (n: number) => `<input type="text" class="typed-box" data-n="${n}" autocomplete="off" autocapitalize="off" spellcheck="false" aria-label="Answer box ${n + 1}">`;
  if (!scaffold || !HAS_BLANK.test(scaffold)) return box(0);
  let n = 0;
  return scaffold.split(BLANK).map((t, i, all) => esc(t) + (i < all.length - 1 ? box(n++) : '')).join('');
}
