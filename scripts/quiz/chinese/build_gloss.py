#!/usr/bin/env python3
"""Pinyin and English meanings for Chinese MCQ options (owner, 23 Nov 2026: a wrong answer shows the hanyu pinyin and the
meaning of the word being tested, and of the one picked; first for 字形, then every applicable Chinese category).

  build_gloss.py [CEDICT_U8]  -> site/public/zh-gloss.json (fetched by the quiz only when a Chinese answer is wrong)

Covered: 字形 (each option character's readings and the word it forms with the characters next to the blank, found again
at run time by zhgloss.ts), and every other option that is a word or idiom (词语, 成语, 关联词 by its parts, cloze and
reading options) in the past-paper selections and the generated banks. Not covered: 字音 (the options are pinyin and the
tested word's underline was lost), sentence options (句子, 完成对话). Only dictionary entries are written, never a question.
CC-CEDICT is CC BY-SA 4.0 (https://cc-cedict.org): the quiz shows the credit with the note. Past-paper stems are read
here on the dev machine only; they never reach the repo or the site."""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PPI = Path("/data/alvin/tmp/cookie-codex/ppimport")
SELS = sorted(PPI.glob("*/chinese/selected.jsonl"))  # every Chinese selection (older ones only add words)
BANKS = ROOT / "site/dist/data/quiz"  # the built banks (each question carries its sub-topic): run `npm run build` first
CEDICT = Path("/data/alvin/tmp/cookie-codex/cedict/cedict_ts.u8")
OUT = ROOT / "site/public/zh-gloss.json"
SKIP_SUBS = {"chi-pinyin-sound", "chi-juzi-choose", "chi-dialogue-mcq", "chi-yuedu-open-text"}
PARTS = re.compile(r"[…\.]{2,}|……|…|、|/")
CJK = re.compile(r"^[\u3400-\u9fff]+$")
SUB = "chi-zixing-form"
BLANK = re.compile(r"[_＿]{2,}|（\s*）|\(\s*\)")
STOP = re.compile(r"[，。！？、；：“”‘’（）()《》\s,.!?;:]")
SKIP = re.compile(r"^(CL:|variant of|old variant|surname |see |also written|abbr\. for|used in |\(old\)|Japanese variant)")
TONE = {"a": "āáǎà", "e": "ēéěè", "i": "īíǐì", "o": "ōóǒò", "u": "ūúǔù", "ü": "ǖǘǚǜ"}


def mark(syl):
    """CC-CEDICT numbered pinyin ('xiang4', 'lu:4', 'ma5') as tone marks ('xiàng', 'lǜ', 'ma')."""
    m = re.fullmatch(r"([a-zA-Z:]+)([1-5])", syl)
    if not m:
        return syl.replace("u:", "ü")
    s, t = m.group(1).replace("u:", "ü").replace("v", "ü"), int(m.group(2))
    if t == 5:
        return s
    low = s.lower()
    i = low.find("a") if "a" in low else low.find("e") if "e" in low else low.find("o") if "ou" in low else \
        max(low.rfind(v) for v in "aeiouü")
    if i < 0:
        return s
    return s[:i] + TONE[low[i]][t - 1] + s[i + 1:]


def pinyin(p):
    return " ".join(mark(x) for x in p.split())


def sense(defs):
    keep = [d for d in defs if d and not SKIP.match(d)]
    out = "; ".join(keep[:3])
    return out if len(out) <= 80 else out[:77].rsplit(";", 1)[0] + "…"


def load_cedict(path):
    d = {}
    for line in open(path, encoding="utf-8"):
        if line.startswith("#"):
            continue
        m = re.match(r"\S+ (\S+) \[([^\]]+)\] /(.*)/\s*$", line)
        if not m:
            continue
        simp, py, defs = m.group(1), m.group(2), m.group(3).split("/")
        if py[:1].isupper():  # proper nouns and surnames
            continue
        s = sense(defs)
        if s:
            d.setdefault(simp, []).append([pinyin(py), s])
    return d


def windows(left, opt, right, longest=4):
    """Every word of 2-4 characters around the blank that contains the whole option: the same list zhgloss.ts tries."""
    left, right = STOP.split(left)[-1][-3:], STOP.split(right)[0][:3]
    ctx, a = left + opt, len(left)
    ctx += right
    b = a + len(opt)
    out = []
    for n in range(longest, 1, -1):
        for i in range(max(0, b - n), min(a, len(ctx) - n) + 1):
            if i <= a and i + n >= b:
                out.append(ctx[i:i + n])
    return out


def option_words(o):
    """The dictionary words an option is: itself, or the parts of a connective pair ("因为……所以……")."""
    o = re.sub(r"^\s*[(（]?[1-4][)）.．、]?\s*", "", o or "").strip()
    if CJK.match(o) and len(o) <= 8:
        return [o]
    parts = [x.strip() for x in PARTS.split(o) if x.strip()]
    return [x for x in parts if CJK.match(x) and len(x) <= 8] if len(parts) > 1 else []


def items():
    """(sub-topic, stem, options, answer) of every Chinese MCQ: the past-paper selections and the generated banks."""
    for f in SELS:
        for l in open(f, encoding="utf-8") if f.exists() else []:
            r = json.loads(l)
            yield r["subtopic"], r["stem"], r["options"], r["answer"]
    for f in sorted(BANKS.glob("chi*.json")):
        b = json.loads(f.read_text(encoding="utf-8"))
        for q in (b["questions"] if isinstance(b, dict) else b):
            yield q.get("sub"), q.get("stem") or "", q.get("options") or [], q.get("answer", 0)


def main(cedict=CEDICT):
    d = load_cedict(cedict)
    chars, words = {}, {}
    zx = zx_found = other = other_found = 0
    for sub, stem, opts, ans in items():
        if sub in SKIP_SUBS:
            continue
        if sub == SUB:
            zx += 1
            m = BLANK.search(stem)
            hit = False
            for k, o in enumerate(opts):
                o = o.strip()
                for c in o:
                    if c in d:
                        chars[c] = d[c]
                if m:
                    for w in windows(stem[:m.start()], o, stem[m.end():]):
                        if w in d and len(w) > len(o):
                            words[w] = d[w][0]
                            hit = hit or k == ans
            zx_found += hit
            continue
        other += 1
        hit = False
        for k, o in enumerate(opts):
            for w in option_words(o):
                if w in d:
                    if len(w) == 1:
                        chars[w] = d[w]
                    else:
                        words[w] = d[w][0]
                    hit = hit or k == ans
        other_found += hit
    # a missing input must not publish a near-empty dictionary over the good one
    if not SELS or zx < 100 or other < 1000 or len(words) < 1000:
        sys.exit(f"inputs look incomplete ({len(SELS)} selections, {zx} 字形 and {other} other questions, {len(words)} words): "
                 "run `npm run build` in site/ and check the selections; nothing written")
    OUT.write_text(json.dumps({"licence": "CC-CEDICT (https://cc-cedict.org), CC BY-SA 4.0 (https://creativecommons.org/licenses/by-sa/4.0/)",
                               "c": dict(sorted(chars.items())), "w": dict(sorted(words.items()))}, ensure_ascii=False,
                              separators=(",", ":")) + "\n", encoding="utf-8")
    print(f"字形 {zx} questions, the answer's word found in {zx_found} ({zx_found / max(1, zx):.0%}); other categories {other}"
          f" questions, the answer glossed in {other_found} ({other_found / max(1, other):.0%}); {len(chars)} characters, "
          f"{len(words)} words -> {OUT.relative_to(ROOT)} ({OUT.stat().st_size // 1024} KB)")


def selftest():
    assert mark("xiang4") == "xiàng" and mark("lu:4") == "lǜ" and mark("ma5") == "ma" and mark("gou3") == "gǒu" and mark("hui4") == "huì"
    assert pinyin("xiang4 lian4") == "xiàng liàn"
    assert "项链" in windows("奶奶戴了一条非常漂亮的", "项", "链。") and "慈祥" in windows("母亲慈", "祥", "地望着熟睡")
    assert all("项" in w for w in windows("一条", "项", "链"))
    assert windows("，", "贴", "心。")[-1] in ("贴心",) and "贴心" in windows("非常", "贴", "心。")
    assert sense(["CL:個|个", "necklace"]) == "necklace"
    assert option_words("（2）因为……所以……") == ["因为", "所以"] and option_words("一丝不苟") == ["一丝不苟"]
    assert option_words("他每天都很早起床。") == []
    print("build_gloss selftest ok")


if __name__ == "__main__":
    if sys.argv[1:2] == ["selftest"]:
        selftest()
    else:
        main(*(Path(x) for x in sys.argv[1:2]))
