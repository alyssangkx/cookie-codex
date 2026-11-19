// Pure helpers of the parent sign-up functions (supabase/functions/_shared), run under Node.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { weakPin } from '../../../supabase/functions/_shared/weakpin.ts';

test('weak PINs are refused, ordinary ones pass', () => {
  for (const p of ['1111', '1234', '9876', '1212', '6969', '2580', '1999', '2026']) assert.ok(weakPin(p), p);
  for (const p of ['3817', '5049', '7302', '0461']) assert.equal(weakPin(p), null, p);
  assert.equal(weakPin('12a4'), 'format');
  let n = 0;
  for (let i = 0; i < 10000; i++) if (weakPin(String(i).padStart(4, '0'))) n++;
  assert.ok(n > 150 && n < 200, `about 171 weak PINs, got ${n}`); // removes first guesses, does not change the bound
});
