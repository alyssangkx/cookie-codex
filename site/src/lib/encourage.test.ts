import { test } from 'node:test';
import assert from 'node:assert/strict';
import { band, pickLine, lineForLast, bilingual, hash, BANDS, BILINGUAL_UNTIL, type Band } from './encourage.ts';

test('bands: perfect, 80%+, 50-79%, under 50%', () => {
  assert.equal(band(10, 10), 'perfect');
  assert.equal(band(20, 20), 'perfect');
  assert.equal(band(9, 10), 'high');
  assert.equal(band(16, 20), 'high'); // exactly 80%
  assert.equal(band(15, 20), 'mid'); // 75%
  assert.equal(band(5, 10), 'mid'); // exactly 50%
  assert.equal(band(4, 10), 'low');
  assert.equal(band(0, 10), 'low');
  assert.equal(band(0, 0), 'low'); // an empty quiz is never "perfect"
});

test('copy: 5 English and 5 Chinese lines per band, each band has lines for papers, and none breaks the rules', () => {
  for (const b of ['perfect', 'high', 'mid', 'low'] as Band[]) {
    assert.equal(BANDS[b].length, 5, b);
    assert.ok(BANDS[b].some((l) => l.use === 'all'), `${b} needs an "all" line`);
    for (const l of BANDS[b]) {
      assert.ok(l.en.trim() && l.zh.trim(), 'both languages');
      assert.ok(['all', 'tier'].includes(l.use));
      assert.doesNotMatch(l.en, /\b(smart|genius|talented|clever|fail|failed|others|everyone else|than your)\b/i);
      assert.doesNotMatch(l.zh, /聪明|天才|天赋|失败|别人|同学/);
    }
  }
  assert.match(BILINGUAL_UNTIL, /^\d{4}-\d{2}-\d{2}$/);
});

test('pickLine is deterministic per seed, skips tier lines outside tier quizzes, and avoids a given line', () => {
  const ts = 1_790_000_000_000;
  assert.deepEqual(pickLine('mid', ts, true), pickLine('mid', ts, true));
  for (let s = 0; s < 200; s++) assert.equal(pickLine('perfect', s, false).use, 'all');
  const tierLine = BANDS.perfect.find((l) => l.use === 'tier')!;
  assert.ok(Array.from({ length: 200 }, (_, s) => pickLine('perfect', s, true)).some((l) => l === tierLine), 'tier lines reachable in tier mode');
  const first = pickLine('high', ts, false);
  assert.notEqual(pickLine('high', ts, false, first.en).en, first.en);
  assert.equal(hash('abc'), hash('abc'));
  assert.notEqual(hash(1), hash(2));
});

test('lineForLast: open attempts ignored, never the same line twice in a row, stable on reload', () => {
  const base = 1_790_000_000_000;
  const attempts = Array.from({ length: 60 }, (_, k) => ({ ts: base + k * 977, mode: k % 3 ? 'tier' : 'paper', score: 7, total: 10 }));
  let prev = '';
  for (let n = 1; n <= attempts.length; n++) {
    const l = lineForLast(attempts.slice(0, n))!;
    assert.notEqual(l.en, prev, `attempt ${n} repeats the previous line`);
    prev = l.en;
  }
  const withOpen = [...attempts, { ts: base + 999_999, mode: 'tier', score: 0, total: 10, open: true }];
  assert.deepEqual(lineForLast(withOpen), lineForLast(attempts));
  assert.equal(lineForLast([]), null);
});

test('bilingual until the end of the Term 1 date (local), then Chinese only', () => {
  assert.equal(bilingual(new Date(2026, 10, 20).getTime(), '2027-03-31'), true);
  assert.equal(bilingual(new Date(2027, 2, 31, 23, 59).getTime(), '2027-03-31'), true);
  assert.equal(bilingual(new Date(2027, 3, 1, 0, 1).getTime(), '2027-03-31'), false);
});

test('pickLine never crashes on an edited copy: fitting band lines, then any non-tier line, then the band tier lines', () => {
  const only = { perfect: [{ use: 'tier' as const, en: 'T', zh: 't' }], high: [], mid: [{ use: 'all' as const, en: 'M', zh: 'm' }], low: [] };
  assert.equal(pickLine('perfect', 1, false, undefined, only)!.en, 'M'); // no fitting line in the band: any non-tier line first
  assert.equal(pickLine('high', 1, false, undefined, only)!.en, 'M'); // empty band: any non-tier line
  assert.equal(pickLine('perfect', 1, true, undefined, only)!.en, 'T'); // tier quiz: the band's tier line fits
  const tierOnly = { perfect: [{ use: 'tier' as const, en: 'T', zh: 't' }], high: [], mid: [], low: [] };
  assert.equal(pickLine('perfect', 1, false, undefined, tierOnly)!.en, 'T'); // last resort: the band's own tier lines
  assert.equal(pickLine('low', 1, false, undefined, { perfect: [], high: [], mid: [], low: [] }), null);
  assert.equal(lineForLast([{ ts: 1, mode: 'paper', score: 0, total: 10 }], { perfect: [], high: [], mid: [], low: [] }), null);
});
