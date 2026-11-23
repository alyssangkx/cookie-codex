import { test } from 'node:test';
import assert from 'node:assert/strict';
import { windows, optionWords, glossOption, type Gloss } from './zhgloss.ts';

const g: Gloss = {
  c: { 项: [['xiàng', 'back of neck; item']], 像: [['xiàng', 'to resemble']], 长: [['cháng', 'long'], ['zhǎng', 'to grow']], 扰: [['rǎo', 'to disturb']] },
  w: { 项链: ['xiàng liàn', 'necklace'], 长大: ['zhǎng dà', 'to grow up'], 打扰: ['dǎ rǎo', 'to disturb'], 因为: ['yīn wèi', 'because'], 所以: ['suǒ yǐ', 'therefore'], 一丝不苟: ['yī sī bù gǒu', 'meticulous'] },
};

test('windows: words around the blank that hold the option, longest first (same as build_gloss.py)', () => {
  assert.ok(windows('奶奶戴了一条非常漂亮的', '项', '链。').includes('项链'));
  assert.ok(windows('一条', '项', '链').every((w) => w.includes('项')));
  assert.equal(windows('他说，', '扰', '。').length, 0, 'punctuation ends the context');
});

test('字形: the character and the word it forms; a character takes the reading its word uses', () => {
  assert.deepEqual(glossOption(g, 'chi-zixing-form', '奶奶戴了一条非常漂亮的____链。', '项').map((l) => l.text), ['项', '项链']);
  assert.equal(glossOption(g, 'chi-zixing-form', '小树慢慢____大了。', '长')[0].py, 'zhǎng', 'the word 长大 picks zhǎng, not the first reading');
  assert.deepEqual(glossOption(g, 'chi-zixing-form', '奶奶戴了一条非常漂亮的____链。', '像').map((l) => l.text), ['像'], 'a wrong pick has no word: its meaning only');
  assert.deepEqual(glossOption(g, 'chi-zixing-form', '奶奶戴了一条非常漂亮的____链。', '项', true).map((l) => l.text), ['项'],
    'a picked option never shows a word it forms around the blank (it would look right)');
});

test('other categories: a word, an idiom, a connective pair; sentences and skipped sections give nothing', () => {
  assert.deepEqual(glossOption(g, 'chi-ciyu-choose', 'x', '（2）打扰').map((l) => l.py), ['dǎ rǎo']);
  assert.deepEqual(glossOption(g, 'chi-juzi-guanlian', 'x', '因为……所以……').map((l) => l.text), ['因为', '所以']);
  assert.equal(glossOption(g, 'chi-ciyu-idiom', 'x', '一丝不苟')[0].mean, 'meticulous');
  assert.deepEqual(glossOption(g, 'chi-ciyu-choose', 'x', '他每天都很早起床。'), []);
  assert.deepEqual(glossOption(g, 'chi-pinyin-sound', 'x', '打扰'), [], 'pinyin questions are skipped');
  assert.deepEqual(optionWords('（1）因为……所以……'), ['因为', '所以']);
});
