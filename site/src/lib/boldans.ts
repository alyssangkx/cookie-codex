// Escape text for innerHTML as numeric entities, so a later pass can tell an entity from text.
export const esc = (x: string) => x.replace(/[&<>"]/g, (c) => `&#${c.charCodeAt(0)};`);

// Bold the correct option's text inside an explanation (already escaped, ** already turned into <strong>).
// Text outside tags only, never inside an existing <strong> or an &#NN; entity. Skips 1-char options and 2-char non-CJK ones (except 2-digit numbers).
// The option is compared in its escaped form, so "salt & water" matches "salt &#38; water". An answer that is part of a
// larger number or expression ("3/4" in "1 3/4", "36" in "136") is never bolded.
export const boldAns = (h: string, opt: string) => {
  const raw = opt.trim();
  // a letter answer (figure labels A-D): bold the standalone capital; "A" only in letter contexts, since it is also an article
  if (/^[A-D]$/.test(raw)) {
    const re = raw === 'A'
      ? /(?<=\()A(?=\))|(?<=\b(?:[Ss]tage|[Pp]art|[Ll]etter|[Ll]abel|[Ll]abelled|[Mm]arked|[Ss]et-up) )A(?![A-Za-z0-9_])/g
      : new RegExp(`(?<![A-Za-z0-9_#°])${raw}(?![A-Za-z0-9_])`, 'g');
    return h.split(/(<strong>[\s\S]*?<\/strong>|<[^>]+>)/).map((p, n) => (n % 2 ? p : p.replace(re, (m) => `<strong>${m}</strong>`))).join('');
  }
  const cjk = /[㐀-鿿]/.test(raw);
  if (raw.length < 2 || (raw.length === 2 && !cjk && !/^\d+$/.test(raw))) return h;
  const body = esc(raw).replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const notInEntity = '(?<!&#\\d*)';
  const notMixed = /^\d/.test(raw) ? '(?<!\\d\\s)' : ''; // a number after "digit + space" is the tail of a mixed number
  const make = (flags: string) => new RegExp(cjk ? `${notInEntity}${body}` : `(?<![A-Za-z0-9_])(?<!\\d[.,/])${notMixed}${notInEntity}${body}(?![A-Za-z0-9_])(?![.,/]\\d)`, flags);
  const parts = h.split(/(<strong>[\s\S]*?<\/strong>|<[^>]+>)/);
  const hit = (re: RegExp) => parts.some((p, n) => n % 2 === 0 && re.test(p));
  let re = make('g');
  if (!cjk && !hit(make(''))) re = make('gi');
  return parts.map((p, n) => (n % 2 ? p : p.replace(re, (m) => `<strong>${m}</strong>`))).join('');
};
