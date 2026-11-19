// Pure helpers of the parent sign-up functions (supabase/functions/_shared), run under Node.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { weakPin } from '../../../supabase/functions/_shared/weakpin.ts';
import { CODE_RE, lockKey, newCode, normaliseCode } from '../../../supabase/functions/_shared/family.ts';

test('weak PINs are refused, ordinary ones pass', () => {
  for (const p of ['1111', '1234', '9876', '1212', '6969', '2580', '1999', '2026']) assert.ok(weakPin(p), p);
  for (const p of ['3817', '5049', '7302', '0461']) assert.equal(weakPin(p), null, p);
  assert.equal(weakPin('12a4'), 'format');
  let n = 0;
  for (let i = 0; i < 10000; i++) if (weakPin(String(i).padStart(4, '0'))) n++;
  assert.ok(n > 150 && n < 200, `about 171 weak PINs, got ${n}`); // removes first guesses, does not change the bound
});

test('family codes: typed forms normalise, generated codes are valid and varied', () => {
  assert.equal(normaliseCode(' k7m4-qx2p '), 'K7M4QX2P');
  assert.ok(CODE_RE.test(normaliseCode('k7m4 qx2p')));
  for (const bad of ['K7M4QX2', 'K7M4QX2PP', 'K7M4QX2O', 'I7M4QX2P', '17M4QX2P']) assert.ok(!CODE_RE.test(bad), bad);
  const codes = new Set(Array.from({ length: 500 }, newCode));
  assert.ok([...codes].every((c) => CODE_RE.test(c)));
  assert.ok(codes.size > 495);
});

test('lock keys carry the family, so the same name in two families never shares a lock', () => {
  assert.notEqual(lockKey('p1', 'emma'), lockKey('p2', 'emma'));
  assert.equal(lockKey('p1', 'emma'), 'p1:emma'); // the format 002's pin_clear_name_lock builds
});
