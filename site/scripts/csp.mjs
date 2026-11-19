// Post-build: give every page a script-src CSP (site review F3). Each page's inline scripts (the Base.astro pre-paint
// gate, Astro's small inlined modules) are allowed by their sha256; everything else must come from this origin or the
// Turnstile host. Styles are left alone: the pages use many style="" attributes. frame-ancestors stays in vercel.json
// (a <meta> CSP cannot set it). Runs after `astro build`; exits 1 if a page with scripts has no <head>.
import { createHash } from 'node:crypto';
import { readdirSync, readFileSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';

const EXEC = /^(|module|(text|application)\/(java|ecma)script)$/i; // types the browser runs; JSON data blocks need no hash
export function policy(html) {
  const hashes = new Set();
  for (const [, attrs, body] of html.matchAll(/<script\b([^>]*)>([\s\S]*?)<\/script>/g)) {
    if (/\ssrc=/.test(attrs) || !EXEC.test(attrs.match(/\stype="([^"]*)"/)?.[1] ?? '')) continue;
    hashes.add(`'sha256-${createHash('sha256').update(body).digest('base64')}'`);
  }
  return ["script-src 'self'", ...hashes, 'https://challenges.cloudflare.com;', "object-src 'none'; base-uri 'self'"].join(' ');
}

export function addPolicy(html) {
  if (html.includes('http-equiv="Content-Security-Policy"')) return html; // already done (a second run adds nothing)
  const at = html.match(/<meta charset="[^"]*">/) ?? html.match(/<head\b[^>]*>/); // after charset: keep it in the first 1 KB
  if (!at) return /<script\b/.test(html) ? null : html; // e.g. the Google verification file: no scripts
  const i = at.index + at[0].length;
  return `${html.slice(0, i)}<meta http-equiv="Content-Security-Policy" content="${policy(html)}">${html.slice(i)}`;
}

const walk = (d) => readdirSync(d, { withFileTypes: true }).flatMap((e) => (e.isDirectory() ? walk(join(d, e.name)) : [join(d, e.name)]));
if (process.argv[1]?.endsWith('csp.mjs')) {
  let n = 0; // pages written, including script-free ones left as they were
  for (const f of walk(process.argv[2] ?? 'dist').filter((f) => f.endsWith('.html'))) {
    const out = addPolicy(readFileSync(f, 'utf8'));
    if (out === null) { console.error(`csp: no <head> in ${f}`); process.exit(1); }
    writeFileSync(f, out); n++;
  }
  console.log(`csp: script-src policy added to ${n} pages`);
}
