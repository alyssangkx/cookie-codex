// Web Interface Guidelines faults found by the 27 Nov 2026 audit (docs/audit/web-guidelines-2026-11-27.md), kept as checks
// so they cannot come back: no control inside <summary>, fast tap on every control, one <h1> per page, no faded text for
// "coming soon", and no keyboard-opening focus on a phone when a quiz screen is drawn.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync, readdirSync, statSync } from 'node:fs';
import { fileURLToPath } from 'node:url';

const SRC = fileURLToPath(new URL('../', import.meta.url));
const files = (d: string): string[] => readdirSync(d).flatMap((n) => {
  const p = `${d.replace(/\/$/, '')}/${n}`;
  return statSync(p).isDirectory() ? files(p) : [p];
});
const astro = files(SRC).filter((f) => f.endsWith('.astro'));
const rel = (f: string) => f.slice(SRC.length);
// comments mention tags in prose ("a <summary> would…"): leave them out of every scan
const code = (f: string) => readFileSync(f, 'utf8').replace(/<!--[\s\S]*?-->/g, '').replace(/\/\*[\s\S]*?\*\//g, '').replace(/(^|[^:'"`])\/\/.*$/gm, '$1');

test('no button, link or input inside a <summary> (M7: invalid, read as part of the fold name)', () => {
  const bad: string[] = [];
  for (const f of astro) {
    for (const m of code(f).matchAll(/<summary\b[^>]*>([\s\S]*?)<\/summary>/g))
      if (/<(button|a|input|select|textarea)\b/.test(m[1])) bad.push(`${rel(f)}: ${m[0].slice(0, 80)}`);
  }
  assert.deepEqual(bad, []);
});

test('controls get touch-action: manipulation site-wide (M5)', () => {
  const css = readFileSync(`${SRC}styles/global.css`, 'utf8');
  assert.match(css, /:where\([^)]*\bbutton\b[^)]*\)\s*\{[^}]*touch-action:\s*manipulation/);
});

test('every page has an <h1> (M17)', () => {
  const pages = astro.filter((f) => f.includes('/pages/'));
  assert.deepEqual(pages.filter((f) => !/<h1\b/.test(readFileSync(f, 'utf8'))).map(rel), []);
});

test('"coming soon" text is not faded with opacity (M16: contrast)', () => {
  // below .85 drops ordinary text under 4.5:1 here; a slight dim (.92) keeps it readable
  const faded = (s: string) => [...s.matchAll(/\.soon[^{]*\{[^}]*opacity:\s*(0?\.\d+)/g)].some((m) => Number(m[1]) < 0.85);
  const bad = astro.filter((f) => faded(code(f))).map(rel);
  assert.deepEqual(bad, []);
});

test('a quiz screen does not focus a text box on a phone when drawn (M2: it opens the keyboard)', () => {
  const src = readFileSync(`${SRC}pages/quiz/index.astro`, 'utf8').split('\n');
  // a line that focuses a text box (a typed box, or `first` taken from input.cz just above) must sit under a mouseUser()
  // check; focus after the child acts (Enter to the next blank, an empty one after Submit) is fine
  const textBox = (i: number) => /typed-box|input\.cz/.test(src.slice(Math.max(0, i - 3), i + 1).join('\n'));
  const bad = src.map((l, i) => [l, i] as const).filter(([l, i]) =>
    /\.focus\(/.test(l) && textBox(i) && !/mouseUser\(\)/.test(src.slice(Math.max(0, i - 2), i + 1).join(' ')) && !/empty|nx|next|boxes|submit|\.find\(/.test(l));
  assert.deepEqual(bad.map(([l, i]) => `${i + 1}: ${l.trim()}`), []);
});
