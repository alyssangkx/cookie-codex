import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

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
