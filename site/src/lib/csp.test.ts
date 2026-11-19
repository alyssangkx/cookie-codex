import { test } from 'node:test';
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { addPolicy, policy } from '../../scripts/csp.mjs';

test('inline scripts are hashed, external and JSON ones are not', () => {
  const html = '<head><script>a()</script><script type="module">b()</script><script src="/x.js"></script>'
    + '<script type="application/ld+json">{}</script></head>';
  const h = (s: string) => `'sha256-${createHash('sha256').update(s).digest('base64')}'`;
  const p = policy(html);
  assert.ok(p.startsWith("script-src 'self' ") && p.includes(h('a()')) && p.includes(h('b()')));
  assert.ok(!p.includes(h('{}')) && p.endsWith("object-src 'none'; base-uri 'self'"));
  assert.match(addPolicy(html)!, /^<head><meta http-equiv="Content-Security-Policy" content="script-src/);
  assert.equal(addPolicy('<html><script>x()</script></html>'), null);
  assert.equal(addPolicy('<html>verify</html>'), '<html>verify</html>');
});
