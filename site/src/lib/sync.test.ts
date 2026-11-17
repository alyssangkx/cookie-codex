import { test } from 'node:test';
import assert from 'node:assert/strict';
import { decideHydrate, decidePush, resolveConflict, isChildSession, idleExpired } from './sync.ts';
import { jumpClock, resetTier, grantCard, shiftKey } from './testtools.ts';
import { fresh, finishQuiz } from './store.ts';

const base = { serverRev: 5, lastRev: 5, owner: 'c1', childId: 'c1', dirty: false, localHasProgress: true };

test('hydrate: same rev and clean keeps local; dirty pushes', () => {
  assert.equal(decideHydrate(base), 'keep');
  assert.equal(decideHydrate({ ...base, dirty: true }), 'push-local');
});
test('hydrate: a newer server copy replaces a clean local save', () => {
  assert.equal(decideHydrate({ ...base, serverRev: 6 }), 'use-server');
});
test('hydrate: a newer server copy with unsynced local changes is a conflict, not a silent overwrite', () => {
  assert.equal(decideHydrate({ ...base, serverRev: 6, dirty: true }), 'conflict');
});
test('hydrate: never synced before for this child behaves as older than the server', () => {
  assert.equal(decideHydrate({ ...base, lastRev: null }), 'use-server');
  assert.equal(decideHydrate({ ...base, lastRev: null, dirty: true }), 'conflict');
});
test('hydrate: a server rev that went backwards is still taken (the server is the truth)', () => {
  assert.equal(decideHydrate({ ...base, serverRev: 2 }), 'use-server');
});
test('hydrate: no server row yet', () => {
  const none = { ...base, serverRev: null, lastRev: null };
  assert.equal(decideHydrate({ ...none, owner: null }), 'push-local'); // adopt the anonymous browser save
  assert.equal(decideHydrate({ ...none, owner: null, localHasProgress: false }), 'keep');
  assert.equal(decideHydrate({ ...none, owner: 'other' }), 'reset-local'); // another child's save is never pushed as this child's
});
test('hydrate: a save owned by someone else, or nobody, yields to the server copy', () => {
  assert.equal(decideHydrate({ ...base, owner: 'other' }), 'use-server');
  assert.equal(decideHydrate({ ...base, owner: null, dirty: true }), 'use-server');
});

test('push outcomes', () => {
  assert.deepEqual(decidePush([{ status: 'ok', rev: 7, data: null, schema_version: 2 }], null), { kind: 'ok', rev: 7 });
  assert.deepEqual(decidePush([{ status: 'ok', rev: '0', data: null, schema_version: 2 }], null), { kind: 'ok', rev: 0 });
  assert.deepEqual(decidePush([{ status: 'conflict', rev: 9, data: { a: 1 }, schema_version: 2 }], null), { kind: 'conflict', rev: 9, data: { a: 1 } });
  assert.deepEqual(decidePush([{ status: 'denied', rev: null, data: null, schema_version: null }], null), { kind: 'denied' });
});
test('push: errors and malformed rows are never read as success', () => {
  assert.deepEqual(decidePush(null, { message: 'x' }), { kind: 'error' });
  assert.deepEqual(decidePush([], null), { kind: 'error' });
  assert.deepEqual(decidePush(null, null), { kind: 'error' });
  assert.deepEqual(decidePush([{ status: 'ok', rev: null }], null), { kind: 'error' });
  assert.deepEqual(decidePush([{ status: 'weird', rev: 1 }], null), { kind: 'error' });
});

test('conflict choices', () => {
  assert.equal(resolveConflict('newer'), 'adopt-server');
  assert.equal(resolveConflict('mine'), 'force-push');
});

test('only a child session syncs', () => {
  assert.equal(isChildSession({ app_metadata: {} }), true);
  assert.equal(isChildSession({}), true);
  assert.equal(isChildSession({ app_metadata: { role: 'admin' } }), false);
  assert.equal(isChildSession({ app_metadata: { role: 'parent' } }), false);
  assert.equal(isChildSession(null), false);
});

test('90-day idle check', () => {
  const now = Date.UTC(2026, 10, 17), day = 86_400_000;
  assert.equal(idleExpired(now - 89 * day, now), false);
  assert.equal(idleExpired(now - 91 * day, now), true);
  assert.equal(idleExpired(0, now), false);
  assert.equal(idleExpired(NaN, now), false);
});

// ---- test tools (act on the Test Player's save only)
const played = () => {
  const s = fresh();
  const now = new Date(2026, 10, 17, 12).getTime();
  finishQuiz(s, { mode: 'tier', sub: 'sub-a', tier: 'b', score: 9, total: 10, ms: 60000, tags: [] }, () => ({ slug: 'muscle-cookie', dup: false }), now);
  s.questions.q1 = { s: 1, due: now + 86_400_000, w: 1 };
  return { s, now };
};
test('jumpClock moves day keys, passes and due dates back one day', () => {
  const { s, now } = played();
  const key = Object.keys(s.days)[0];
  const j = jumpClock(s, 1);
  assert.deepEqual(Object.keys(j.days), [shiftKey(key, -1)]);
  assert.deepEqual(j.progress['sub-a'].b!.passes, [shiftKey(key, -1)]);
  assert.equal(j.questions.q1.due, now);
  assert.equal(j.attempts[0].ts, s.attempts[0].ts - 86_400_000);
  assert.equal(Object.keys(s.days)[0], key, 'the input is not mutated');
});
test('shiftKey crosses month and year ends', () => {
  assert.equal(shiftKey('2027-01-01', -1), '2026-12-31');
  assert.equal(shiftKey('2026-03-01', -1), '2026-02-28');
});
test('resetTier clears the tier and its card', () => {
  const { s, now } = played();
  s.progress['sub-a'].b!.cleared = true;
  s.cards['muscle-cookie'] = { stars: 1, srcSub: 'sub-a', srcTier: 'b', acc: 90, last: now };
  const r = resetTier(s, 'sub-a', 'b');
  assert.equal(r.progress['sub-a'].b, undefined);
  assert.equal(r.cards['muscle-cookie'], undefined);
});
test('grantCard adds a card, then a star up to 5', () => {
  let s = fresh();
  s = grantCard(s, 'x', 'sub-a', 'b');
  assert.equal(s.cards.x.stars, 1);
  for (let i = 0; i < 6; i++) s = grantCard(s, 'x', 'sub-a', 'b');
  assert.equal(s.cards.x.stars, 5);
});
