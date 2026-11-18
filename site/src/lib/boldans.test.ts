import { test } from 'node:test';
import assert from 'node:assert/strict';
import { boldAns, esc } from './boldans.ts';

test('a fraction inside a mixed number is not bolded', () => {
  assert.equal(boldAns('So the total is 1 3/4 litres.', '3/4'), 'So the total is 1 3/4 litres.');
  assert.equal(boldAns('So 3/4 of it is left.', '3/4'), 'So <strong>3/4</strong> of it is left.');
});
test('a number is bolded alone, not inside a longer number', () => {
  assert.equal(boldAns('30, 32, 36', '36'), '30, 32, <strong>36</strong>');
  assert.equal(boldAns('it is 136', '36'), 'it is 136');
});
test('an answer with & < > " matches its escaped form', () => {
  assert.equal(boldAns(esc('Mix salt & water now'), 'salt & water'), 'Mix <strong>salt &#38; water</strong> now');
  assert.equal(boldAns(esc('use a < b here'), 'a < b'), 'use <strong>a &#60; b</strong> here');
});
test('an entity is never matched from inside', () => {
  assert.equal(boldAns(esc('a & b'), '38'), 'a &#38; b');
});
