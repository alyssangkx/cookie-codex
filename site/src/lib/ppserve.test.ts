// pp-serve's figure mapping and filter (supabase/functions/pp-serve/index.ts runs on Deno, so it is not importable here:
// the block is read from the file, its types stripped, and run). 26 Nov 2026 review: a text figure {text} passes with no
// URL; a picture that could not be signed, a figure with both path and text, or a malformed text drops its question.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { stripTypeScriptTypes } from 'node:module';

const src = readFileSync(new URL('../../../supabase/functions/pp-serve/index.ts', import.meta.url), 'utf8');
const block = src.slice(src.indexOf('    const isText'), src.indexOf('    return json({ items: out });'));
const run = new Function('items', 'signed', stripTypeScriptTypes(block) + '\nreturn out;') as
  (items: unknown[], signed: Map<string, string>) => { id: number; figures: unknown[] }[];

test('pp-serve keeps text figures and signed pictures, drops unsigned or malformed figures', () => {
  assert.ok(block.length > 50, 'found the block in pp-serve');
  const signed = new Map([['a.webp', 'https://x/sign/a']]);
  const keep = run([{ id: 1, figures: [{ text: 'passage' }] }, { id: 2, figures: [{ path: 'a.webp', w: 1, h: 1 }] }, { id: 3, figures: [] }], signed);
  assert.deepEqual(keep.map((i) => i.id), [1, 2, 3]);
  assert.deepEqual(keep[0].figures, [{ text: 'passage' }]);
  assert.equal('figures_raw' in keep[0], false);
  const drop = run([{ id: 4, figures: [{ path: 'b.webp', w: 1, h: 1, text: 'x' }] }, { id: 5, figures: [{ text: null }] },
    { id: 6, figures: [{ path: 'missing.webp' }] }, { id: 7, figures: [{ text: '  ' }] }, { id: 8, figures: [{ path: 'a.webp', w: 1, h: 1, text: 'x' }] }], signed);
  assert.deepEqual(drop.map((i) => i.id), []);
});
