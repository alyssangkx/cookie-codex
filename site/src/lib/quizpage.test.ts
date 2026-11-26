import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync, readdirSync, statSync } from 'node:fs';
import { fileURLToPath } from 'node:url';

function* walk(dir: URL | string): Generator<string> {
  const d = typeof dir === 'string' ? dir : fileURLToPath(dir);
  for (const n of readdirSync(d)) { const p = `${d.replace(/\/$/, '')}/${n}`; if (statSync(p).isDirectory()) yield* walk(p); else yield p; }
}

// The build does not type-check, so an imported name that the page also declares as its own function is shadowed without
// any error (26 Nov 2026: `choose` from lib/passageset was hidden by the page's `function choose(k)`, and a set's options
// could not be picked). Each scope of a page (the frontmatter, each <script> block) is checked on its own.
const PAGES = ['../pages/quiz/index.astro', '../pages/train/[school]/[sub].astro', '../pages/parent/index.astro'];

function clashes(src: string): string[] {
  const imported = new Set<string>();
  for (const m of src.matchAll(/import\s*\{([^}]*)\}\s*from/g))
    for (const part of m[1].split(',')) {
      const name = part.replace(/^\s*type\s+/, '').split(/\s+as\s+/).pop()!.trim();
      if (name) imported.add(name);
    }
  const declared = [...src.matchAll(/^\s*(?:async\s+)?(?:function\s+([A-Za-z_$][\w$]*)|const\s+([A-Za-z_$][\w$]*)\s*=)/gm)].map((m) => m[1] || m[2]);
  return declared.filter((n) => imported.has(n));
}

test('no imported name is redeclared in a page script', () => {
  for (const rel of PAGES) {
    let file: string;
    try { file = readFileSync(new URL(rel, import.meta.url), 'utf8'); } catch { continue; }
    const scopes = [file.split(/^---\s*$/m)[1] ?? '', ...[...file.matchAll(/<script\b[^>]*>([\s\S]*?)<\/script>/g)].map((m) => m[1])];
    for (const src of scopes) assert.deepEqual(clashes(src), [], `${rel}: imported and redeclared`);
  }
});

test('the check catches a shadowed import', () => {
  assert.deepEqual(clashes("import { choose, place } from '../lib/x';\nfunction choose(k) {}\n"), ['choose']);
  assert.deepEqual(clashes("import { choose as pick } from '../lib/x';\nfunction choose(k) {}\n"), []);
});

// 26 Nov 2026 review: a text figure {text} has no path, so every place that signs picture paths must skip it.
test('every page or module that signs figure paths skips text figures', () => {
  const files = [...walk(new URL('../', import.meta.url))].filter((f) => /\.(ts|astro)$/.test(f) && !f.endsWith('.test.ts'));
  const bad: string[] = [];
  for (const f of files) {
    const s = readFileSync(f, 'utf8');
    // every signing call (createSignedUrl or createSignedUrls): the line declaring the variable it signs must skip text
    // figures with isTextFig
    for (const m of s.matchAll(/createSignedUrls?\(\s*([\w.]+)/g)) {
      const v = m[1].split('.')[0];
      const decl = s.match(new RegExp(`(?:const|let|var)\\s+${v}\\s*=[^\\n]*`))?.[0] ?? '';
      if (!decl.includes('isTextFig')) bad.push(`${f.split('/src/')[1]}: ${m[0]}`);
    }
  }
  assert.deepEqual(bad, []);
});

// 26 Nov 2026 review: a letter key answered one question of a passage set on its own; the shortcut must stand down for a set.
test('the quiz keyboard shortcut ignores passage sets', () => {
  const src = readFileSync(new URL('../pages/quiz/index.astro', import.meta.url), 'utf8');
  const h = src.slice(src.indexOf("document.addEventListener('keydown'"));
  assert.match(h.slice(0, h.indexOf('\n  });')), /setUi/);
});
