import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  PP_ENABLED, PP_SWITCH, ppMode, ppSubjectOf, countingPool, POOL_CAP, pageStep, ppSubsFor, poolModeFor, isPpId, ppBadge, validRow, safeSignedUrl, toQ, mergePool, ppFigureHtml, optionLabel, ppTierCount, tierPoolIds, PP_MIN_TIER, type PpRow, stubOf, isStub, easierFirst, isPoolSub } from './pastpaper.ts';
import { syncTiers, tierHash, liveMastered, fresh, answer } from './store.ts';

const SB = 'https://abcdefgh.supabase.co';
const row = (over: Partial<PpRow> = {}): PpRow => ({
  id: 'pp-0123456789', subtopic: 'sci-systems-plant-transport-parts', level: 'basic', pattern: null,
  stem: 'placeholder stem', options: ['a', 'b', 'c', 'd'], answer: 2,
  figures: [{ path: 'science/pp-0123456789-1.webp', w: 900, h: 400 }], year: 2025, ...over,
});
const signedFor = (p: string) => `${SB}/storage/v1/object/sign/pp-figures/${p}?token=abc.def`;

test('the master switch is ON; the Science upload (21 Nov 2026) puts 20+ sub-topics in one pool, smaller ones merge', () => {
  assert.equal(PP_ENABLED, true);
  assert.ok(Object.values(PP_SWITCH).every((m) => m === 'pool' || m === 'merge'));
  assert.equal(ppMode('sci-systems-plant-transport-parts', false), null); // nothing while the flag is off
  assert.equal(ppMode('sci-systems-plant-transport-parts'), 'pool');
  assert.equal(ppMode('sci-cycles-water-cycle'), 'pool'); // 21 since 23 Nov 2026 (unsure-key confirms): one pool
  assert.equal(ppMode('sci-energy-photo-respiration'), 'merge'); // 13 past-paper questions: merged into its tiers
  assert.equal(ppMode('math-rate-rate'), 'merge'); // 38 past-paper questions, merged so the generated speed questions stay (owner)
  assert.equal(ppMode('math-geometry-line-symmetry'), 'merge'); // 12: merged into its tiers
});

test('which sub-topics a quiz fetches', () => {
  const sw = { a: 'replace', b: 'merge' } as const;
  assert.deepEqual(ppSubsFor('tier', 'a', [], true, sw), ['a']);
  assert.deepEqual(ppSubsFor('tier', 'c', [], true, sw), []);
  assert.deepEqual(ppSubsFor('review', '', [], true, sw), ['a', 'b']);
  assert.deepEqual(ppSubsFor('paper', '', ['b', 'c', 'b'], true, sw), ['b']);
  assert.deepEqual(ppSubsFor('review', '', [], false, sw), []);
  assert.deepEqual(ppSubsFor('tier', 'a', [], false, sw), []);
});

test('validRow accepts the RPC shape and rejects anything odd', () => {
  assert.ok(validRow(row()));
  assert.ok(validRow(row({ figures: [] })));
  for (const bad of [
    null, 'x', row({ id: 'eng-123' }), row({ level: 'hard' as PpRow['level'] }), row({ stem: '  ' }),
    row({ options: ['a', 'b', 'c'] }), row({ answer: 4 }), row({ answer: 1.5 }),
    row({ figures: [{ path: '../secret.png', w: 1, h: 1 }] }),
    row({ figures: [{ path: 'https://evil.example/x.webp', w: 1, h: 1 }] }),
    row({ subtopic: 'Bad Sub' }),
  ]) assert.equal(validRow(bad), false, JSON.stringify(bad));
});

test('only signed URLs from our own private bucket are used', () => {
  assert.ok(safeSignedUrl(signedFor('science/pp-0123456789-1.webp'), SB));
  assert.ok(safeSignedUrl(signedFor('science/pp-0123456789-1.webp'), `${SB}/`));
  assert.equal(safeSignedUrl(`${SB}/storage/v1/object/public/pp-figures/science/x.webp`, SB), false); // public path
  assert.equal(safeSignedUrl(`${SB}/storage/v1/object/sign/other/science/x.webp?token=a`, SB), false); // other bucket
  assert.equal(safeSignedUrl(`${SB}/storage/v1/object/sign/pp-figures/science/x.webp`, SB), false); // no token
  assert.equal(safeSignedUrl(`https://evil.example/storage/v1/object/sign/pp-figures/x.webp?token=a`, SB), false);
  assert.equal(safeSignedUrl(signedFor('x.webp'), 'javascript:alert(1)'), false);
});

test('toQ keeps the paper order, labels (1)-(4), and drops a row whose picture was not signed', () => {
  const r = row();
  const q = toQ(r, new Map([[r.figures[0].path, signedFor(r.figures[0].path)]]), 'plant-transport')!;
  assert.deepEqual(q.options, ['a', 'b', 'c', 'd']);
  assert.equal(q.answer, 2);
  assert.equal(q.numbered, true);
  assert.equal(q.topic, 'plant-transport');
  assert.equal(q.explain[2], null);
  assert.equal(q.explain.filter((e) => e && e.tag === 'past-paper').length, 3);
  assert.deepEqual(q.ppFigs, [{ src: signedFor(r.figures[0].path), w: 900, h: 400 }]);
  assert.equal(toQ(r, new Map()), null);
  assert.ok(toQ(row({ figures: [] }), new Map()));
});

test('mergePool: off, merge, and replace only when the past-paper tier is full', () => {
  const mk = (pre: string, sub: string, level: string, n: number) =>
    Array.from({ length: n }, (_, i) => ({ id: `${pre}${sub}${level}${i}`, sub, level }));
  const gen = [...mk('g', 'a', 'basic', 25), ...mk('g', 'a', 'intermediate', 25), ...mk('g', 'b', 'basic', 25)];
  const pp = [...mk('pp-', 'a', 'basic', 20), ...mk('pp-', 'a', 'intermediate', 5), ...mk('pp-', 'b', 'basic', 30)];
  const modes: Record<string, 'replace' | 'merge'> = { a: 'replace' };
  const out = mergePool(gen, pp, (s) => modes[s] ?? null, 20);
  const count = (pre: string, sub: string, level: string) =>
    out.filter((q) => q.id.startsWith(pre) && q.sub === sub && q.level === level).length;
  assert.equal(count('g', 'a', 'basic'), 0); // replaced: 20 past-paper items fill the tier
  assert.equal(count('pp-', 'a', 'basic'), 20);
  assert.equal(count('g', 'a', 'intermediate'), 25); // too few to replace: merged
  assert.equal(count('pp-', 'a', 'intermediate'), 5);
  assert.equal(count('g', 'b', 'basic'), 25); // b is off: its past-paper items are dropped
  assert.equal(count('pp-', 'b', 'basic'), 0);
  const merged = mergePool(gen, pp, (s) => (s === 'b' ? 'merge' : null), 20);
  assert.equal(merged.filter((q) => q.sub === 'b').length, 55);
  assert.deepEqual(mergePool(gen, pp, () => null), gen);
});

test('figure HTML escapes the source and labels follow the item kind', () => {
  const h = ppFigureHtml([{ src: `${SB}/x?token=a"b&c`, w: 10, h: 20 }]);
  assert.ok(h.includes('token=a&#34;b&#38;c') && !h.includes('a"b'));
  assert.ok(h.includes('width="10" height="20"') && h.includes('referrerpolicy="no-referrer"'));
  assert.equal(optionLabel({ numbered: true }, 0), '(1)');
  assert.equal(optionLabel({}, 3), 'D');
});

test('Daily Review merges instead of replacing, so old retests stay reachable', () => {
  const sw = { a: 'replace' } as const;
  assert.equal(poolModeFor('tier', true, sw)('a'), 'replace');
  assert.equal(poolModeFor('paper', true, sw)('a'), 'replace');
  assert.equal(poolModeFor('review', true, sw)('a'), 'merge');
  assert.equal(poolModeFor('review', true, sw)('b'), null);
  assert.equal(poolModeFor('tier', false, sw)('a'), null);
});

test('"Past paper <year>" only on past-paper items, never a school; pp ids are recognised', () => {
  const q = toQ(row({ figures: [] }), new Map())!;
  assert.equal(q.ppYear, 2025);
  assert.equal(ppBadge(q), '<span class="pp-badge">Past paper 2025</span>');
  assert.equal(ppBadge({ ...q, ppYear: null }), '<span class="pp-badge">Past paper</span>');
  assert.equal(ppBadge({}), '');
  assert.equal(validRow({ ...row(), year: '2025' }), false);
  assert.ok(isPpId('pp-0123456789') && !isPpId('sci-abc') && !isPpId('pp-xyz'));
});

test('ppTierCount mirrors mergePool: merge = gen + pp, replace = pp once it fills a tier, else gen + pp', () => {
  assert.deepEqual(ppTierCount(40, 12, 'merge'), { count: 52, usesPp: true });
  assert.deepEqual(ppTierCount(40, PP_MIN_TIER, 'replace'), { count: PP_MIN_TIER, usesPp: true });
  assert.deepEqual(ppTierCount(40, PP_MIN_TIER - 1, 'replace'), { count: 40 + PP_MIN_TIER - 1, usesPp: true });
  // same answer as the real merge
  const gen = Array.from({ length: 30 }, (_, i) => ({ id: `g${i}`, sub: 's', level: 'basic' }));
  for (const n of [5, 20, 33]) for (const mode of ['merge', 'replace'] as const) {
    const pp = Array.from({ length: n }, (_, i) => ({ id: `pp-${i}`, sub: 's', level: 'basic' }));
    assert.equal(mergePool(gen, pp, () => mode).length, ppTierCount(30, n, mode).count, `${mode} ${n}`);
  }
});

test('ppTierCount changes nothing for a non-pp tier (switch off, or no pp rows)', () => {
  assert.deepEqual(ppTierCount(40, 12, null), { count: 40, usesPp: false });
  assert.deepEqual(ppTierCount(40, 0, 'replace'), { count: 40, usesPp: false });
  assert.deepEqual(ppTierCount(0, 0, 'merge'), { count: 0, usesPp: false });
  assert.equal(ppMode('sci-systems-plant-transport-parts', false), null); // flag off: nothing is counted
});

test('liveMastered matches the total a merged quiz stored, with no hash on pp tiers', () => {
  const genIds = Array.from({ length: 30 }, (_, i) => `g${i}`);
  const ppIds = Array.from({ length: 12 }, (_, i) => `pp-${String(i).padStart(10, '0')}`);
  const s = fresh();
  // the quiz page's pool for a merged tier: generated + pp, every one retired
  const all = [...genIds, ...ppIds];
  for (const id of all) answer(s, id, true, 1);
  syncTiers(s, { 'x|b': all }, () => undefined, 1);
  const st = s.progress.x!.b!;
  const view = ppTierCount(genIds.length, ppIds.length, 'merge');
  assert.equal(st.total, view.count);
  assert.equal(liveMastered(st, view.count, view.usesPp ? undefined : tierHash(genIds)), all.length); // size check only
  assert.equal(liveMastered(st, view.count, tierHash(genIds)), 0); // the old build-time hash would have read 0
  assert.equal(liveMastered(st, genIds.length, undefined), 0); // the old build-time count too
});

test('tierPoolIds: every quiz mode reports the tier quiz pool (replace tier = pp only), matching ppTierCount and liveMastered', () => {
  const mk = (pre: string, n: number, sub = 's', level = 'basic') => Array.from({ length: n }, (_, i) => ({ id: `${pre}${String(i).padStart(10, '0')}`, sub, level }));
  const gen = [...mk('g', 30), ...mk('h', 30, 'plain'), ...mk('m', 30, 'mrg')];
  const pp = [...mk('pp-', 25), ...mk('pq-', 5, 'mrg')];
  const modeOf = (s: string) => (s === 's' ? 'replace' : s === 'mrg' ? 'merge' : null) as 'replace' | 'merge' | null;
  const tierQuiz = tierPoolIds(gen, pp, modeOf);
  // Daily Review asks from the merged pool but reports the same ids
  assert.deepEqual(tierPoolIds(gen, pp, modeOf), tierQuiz);
  assert.deepEqual(tierQuiz['s|basic'].sort(), pp.slice(0, 25).map((q) => q.id).sort());
  assert.equal(tierQuiz['s|basic'].length, ppTierCount(30, 25, 'replace').count);
  assert.equal(tierQuiz['mrg|basic'].length, ppTierCount(30, 5, 'merge').count); // merge unchanged: gen + pp
  assert.equal(tierQuiz['plain|basic'].length, 30); // non-pp tier unchanged
  const st = fresh();
  syncTiers(st, { 's|b': tierQuiz['s|basic'] }, () => undefined);
  assert.equal(st.progress.s.b.total, 25);
  assert.equal(liveMastered(st.progress.s.b, ppTierCount(30, 25, 'replace').count, undefined), 0);
  st.progress.s.b.mastered = 3; // as if 3 were retired
  assert.equal(liveMastered(st.progress.s.b, 25, undefined), 3); // not read as 0
});

test('tierPoolIds: a failed pp fetch reports nothing for a switched sub-topic, so syncTiers leaves it alone', () => {
  const mk = (pre: string, n: number, sub: string) => Array.from({ length: n }, (_, i) => ({ id: `${pre}${i}`, sub, level: 'basic' }));
  const gen = [...mk('g', 30, 's'), ...mk('h', 30, 'plain')];
  const out = tierPoolIds(gen, [], (s) => (s === 's' ? 'replace' : null), true);
  assert.deepEqual(Object.keys(out), ['plain|basic']);
});

test('stubs (ADR 0012): ids, sub-topic, level and rank only; anything malformed is refused', () => {
  const st = stubOf({ id: 'pp-0123456789', subtopic: 'sci-x', level: 'basic', ord: 3 }, 'sci-file');
  assert.ok(st && isStub(st) && st.ord === 3 && st.topic === 'sci-file' && st.options.length === 4 && st.stem === '');
  assert.equal(stubOf({ id: 'pp-xyz', subtopic: 'sci-x', level: 'basic' }), null);
  assert.equal(stubOf({ id: 'pp-0123456789', subtopic: 'sci-x', level: 'hard' }), null);
  assert.equal(stubOf({ id: 'pp-0123456789', subtopic: 'sci-x', level: 'basic', ord: 'x' })?.ord, null);
});

test('easierFirst: rank, then id; unranked last', () => {
  assert.deepEqual(easierFirst([{ id: 'pp-c', ord: 2 }, { id: 'pp-a', ord: null }, { id: 'pp-b', ord: 1 }, { id: 'pp-0', ord: 2 }]), ['pp-b', 'pp-0', 'pp-c', 'pp-a']);
});

test('pool mode: a pool sub-topic is its past-paper questions only, and reports no tier ids', () => {
  const sw = { 'sci-pool': 'pool' as const, 'sci-merge': 'merge' as const };
  const gen = [{ id: 'g1', sub: 'sci-pool', level: 'basic' }, { id: 'g2', sub: 'sci-merge', level: 'basic' }];
  const pp = [{ id: 'pp-0000000001', sub: 'sci-pool', level: 'competent' }, { id: 'pp-0000000002', sub: 'sci-merge', level: 'basic' }];
  const modeOf = (x: string) => (sw as Record<string, 'pool' | 'merge'>)[x] ?? null;
  assert.deepEqual(mergePool(gen, pp, modeOf).map((q) => q.id).sort(), ['g2', 'pp-0000000001', 'pp-0000000002']);
  assert.deepEqual(Object.keys(tierPoolIds(gen, pp, modeOf)), ['sci-merge|basic']);
  assert.equal(isPoolSub('sci-pool', true, sw), true);
  assert.equal(isPoolSub('sci-pool', false, sw), false);
  assert.deepEqual(ppTierCount(25, 30, 'pool'), { count: 0, usesPp: true });
});

test('ppSubjectOf maps a sub-topic id to its pp_items subject (pp_pool lists one subject per call)', () => {
  assert.equal(ppSubjectOf('sci-cycles-water-states'), 'science');
  assert.equal(ppSubjectOf('eng-grammar-mcq'), 'english');
  assert.equal(ppSubjectOf('chi-ciyu-choose'), 'chinese');
  assert.equal(ppSubjectOf('math-ratio-basic'), 'maths');
  assert.equal(ppSubjectOf('xyz-thing'), null);
});

test('the counting pool is a pool\'s first POOL_CAP questions easier-first; a small pool is all of it', () => {
  const big = Array.from({ length: 450 }, (_, i) => ({ id: `pp-${String(i).padStart(10, '0')}`, ord: 450 - i }));
  const c = countingPool(big);
  assert.equal(c.length, POOL_CAP);
  assert.equal(c[0], 'pp-0000000449'); // ord 1, served first
  assert.deepEqual(countingPool(big.slice(0, 30)).length, 30);
});

test('pageStep: pp_pool paging against the exact total fails closed on a cut or moved list', () => {
  assert.equal(pageStep(1919, 1919, 1000, 1000, 1000), 'more');
  assert.equal(pageStep(1919, 1919, 1919, 919, 1000), 'done');
  assert.equal(pageStep(1919, 1919, 500, 500, 1000), 'more');   // a lower server cap: more pages, not the end
  assert.equal(pageStep(1919, 1918, 1500, 500, 1000), 'fail');  // the total moved between pages
  assert.equal(pageStep(1919, 1919, 1500, 0, 1000), 'fail');    // the server stopped short
  assert.equal(pageStep(1000, 1000, 1000, 1000, 1000), 'done'); // an exact multiple: no extra empty call
  assert.equal(pageStep(0, 0, 0, 0, 1000), 'done');
  assert.equal(pageStep(null, null, 400, 400, 1000), 'done');   // no total: a short page ends it (pre-paging rule)
  assert.equal(pageStep(null, null, 1000, 1000, 1000), 'more');
});

test('a past-paper Maths question is marked no-calculator (Paper 1); other subjects are not', () => {
  const row = { id: 'pp-0123456789', subtopic: 'math-ratio-ratio', level: 'basic', stem: 'x', options: ['a', 'b', 'c', 'd'], answer: 0, figures: [], year: 2024 } as unknown as PpRow;
  assert.equal(toQ(row, new Map())?.calc, false);
  assert.equal(toQ({ ...row, subtopic: 'sci-cycles-water-states' } as PpRow, new Map())?.calc, undefined);
});

test('a long Maths sub-topic id (103 characters, migration 009) passes the stub and row checks', () => {
  const sub = 'math-data-representation-and-interpretation-picture-graphs-bar-graphs-tables-line-graphs-and-pie-charts';
  assert.ok(stubOf({ id: 'pp-0123456789', subtopic: sub, level: 'basic', ord: 1 }));
  assert.ok(validRow({ id: 'pp-0123456789', subtopic: sub, level: 'basic', stem: 'x', options: ['a', 'b', 'c', 'd'], answer: 0, figures: [], year: 2024 }));
});

test('a pool row carries its passage set (migration 010); odd set values are ignored', () => {
  const st = stubOf({ id: 'pp-0123456789', subtopic: 'eng-visual-text', level: 'basic', ord: 3, grp: 'eng-2023-001-paper-2-vt', seq: 23 });
  assert.equal(st?.group, 'eng-2023-001-paper-2-vt');
  assert.equal(st?.seq, 23);
  const odd = stubOf({ id: 'pp-0123456789', subtopic: 'eng-visual-text', level: 'basic', grp: 'Bad Set!', seq: 0 });
  assert.equal(odd?.group, undefined);
  assert.equal(stubOf({ id: 'pp-0123456789', subtopic: 'eng-grammar-mcq', level: 'basic', grp: null, seq: null })?.group, undefined);
});

test('a counting pool with passage sets takes whole sets, easiest first, until the cap', () => {
  const qs: { id: string; ord: number; group?: string }[] = [];
  let o = 0;
  for (let g = 0; g < 80; g++) for (let k = 0; k < 6; k++) qs.push({ id: `pp-${String(g * 10 + k).padStart(10, '0')}`, ord: ++o, group: `set-${g}` });
  const c = countingPool(qs);
  const sets = new Set(c.map((id) => qs.find((q) => q.id === id)!.group));
  assert.equal(c.length, POOL_CAP); // the size train.ts and the milestone preview use
  const part = [...sets].filter((g) => c.filter((id) => qs.find((q) => q.id === id)!.group === g).length !== 6);
  assert.ok(part.length <= 1); // whole sets, only the one at the cap in part
});

test('validRow: 8 phrases only for the 完成对话 dialogue sets (migration 011), the answer inside them', () => {
  const eight = ['一', '二', '三', '四', '五', '六', '七', '八'];
  assert.ok(validRow(row({ subtopic: 'chi-dialogue-mcq', options: eight, answer: 7 })));
  assert.ok(!validRow(row({ subtopic: 'chi-cloze-mcq', options: eight, answer: 0 })));
  assert.ok(!validRow(row({ subtopic: 'chi-dialogue-mcq', options: eight, answer: 8 })));
  assert.ok(!validRow(row({ answer: 4 })));
});
