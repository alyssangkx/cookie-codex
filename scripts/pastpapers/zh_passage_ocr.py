#!/usr/bin/env python3
"""Chinese passage sections as text (owner, 26 Nov 2026): the site shows the 完型填空, 完成对话 and 阅读理解 passages as scanned
pages; the owner wants real text (cloze options inside the passage, dialogue phrases dragged into the blanks). Two vision
models read each set's pages on the server (queue 41); on dev a passage is used only when both reads agree and, for cloze
and dialogue, every stored blank sentence is found around its blank.

  zh_passage_ocr.py read ITEMS.jsonl   server (GPU; PP_ROOT, PP_VLM, PP_TP; PP_TAG names the read, e.g. 72b / 32b)
  zh_passage_ocr.py selftest
ITEMS rows: {grp, kind: cloze|dialogue|reading, pages: [paths under PP_ROOT], blanks: {n: stem}}. Writes
PP_ROOT/zhcloze41/<PP_TAG>/<grp>.json {grp, raw}. The dev side is `check()` / `blank_ok()` here."""
import json
import os
import re
import sys
from difflib import SequenceMatcher
from pathlib import Path

PP = Path(os.environ.get("PP_ROOT", "/data/alvin/cookie/pastpapers_full"))
PROMPTS = {
    "cloze": ("If the page also has a picture, photo, chart, map or table that the passage or its questions need (not just a small decoration), reply with the single word PICTURE and nothing else. Otherwise: This page is a Chinese cloze passage (完型填空) from a Primary 6 exam. Copy the passage text exactly, character for "
              "character, keeping its paragraph breaks as blank lines. Each numbered blank must be written as （n） with the blank's "
              "number, e.g. （16）, and nothing else in its place. Do not copy the instructions, the title line with the marks, or the "
              "table of answer options. Reply with the passage text only."),
    "dialogue": ("If the page also has a picture, photo, chart, map or table that the passage or its questions need (not just a small decoration), reply with the single word PICTURE and nothing else. Otherwise: This page is a Chinese dialogue-completion exercise (完成对话) from a Primary 6 exam. Copy the dialogue exactly, "
                 "character for character, one speaker turn per line, in the form 名字：话. Each numbered blank must be written as （n） "
                 "with its number, e.g. （26）, and nothing else in its place. Do not copy the instructions or the table of numbered "
                 "phrases to choose from. Reply with the dialogue only."),
    "reading": ("If the page also has a picture, photo, chart, map or table that the passage or its questions need (not just a small decoration), reply with the single word PICTURE and nothing else. Otherwise: This page is a Chinese reading-comprehension passage (阅读理解) from a Primary 6 exam. Copy the passage text exactly, "
                "character for character, keeping its paragraph breaks as blank lines (and its title, if it has one, on the first "
                "line). Do not copy the instructions or the questions and answer options. Reply with the passage text only."),
}
BLANK = re.compile(r"[（(]\s*(\d{1,2})\s*[）)]")


def norm(s):
    return re.sub(r"[\s，。！？、；：,.!?;:“”‘’'\"「」『』（）()＿_—\-…]", "", s or "")


def sim(a, b):
    a, b = norm(a), norm(b)
    return SequenceMatcher(None, a, b, autojunk=False).ratio() if a and b else 0.0


def blank_ok(text, n, stem):
    """The stored sentence for blank n (its stem, with the blank) is found in the passage around （n）."""
    m = re.search(rf"[（(]\s*{n}\s*[）)]", text)
    if not m:
        return False
    parts = re.split(r"[（(]\s*\d{1,2}\s*[）)]\s*[＿_]*", stem, maxsplit=1)
    left, right = (parts + [""])[:2]
    left, right = norm(left)[-12:], norm(right)[:12]
    ctx_l, ctx_r = norm(text[max(0, m.start() - 60):m.start()]), norm(text[m.end():m.end() + 60])
    ok_l = not left or SequenceMatcher(None, left, ctx_l, autojunk=False).find_longest_match(0, len(left), 0, len(ctx_l)).size >= 0.7 * len(left)
    ok_r = not right or SequenceMatcher(None, right, ctx_r, autojunk=False).find_longest_match(0, len(right), 0, len(ctx_r)).size >= 0.7 * len(right)
    return ok_l and ok_r


def check(a, b, blanks, kind="cloze"):
    """(ok, why) for two independent reads a, b of one passage and its stored blanks {n: stem} (none for reading).
    Owner (26 Nov 2026): only text-only passages become text; a page with a picture, chart or table keeps its scan."""
    blanks = {int(k): v for k, v in (blanks or {}).items()}  # JSON object keys arrive as strings
    if any(str(x or "").strip().upper().startswith("PICTURE") for x in (a, b)):
        return False, "page has a picture: keep the scan"
    if kind == "reading":
        if min(len(norm(a)), len(norm(b))) < 80:
            return False, "read too short"
        s = sim(a, b)
        return (True, None) if s >= 0.95 else (False, f"the two reads disagree ({s:.2f})")
    for t in (a, b):
        found = [int(x) for x in BLANK.findall(t or "")]
        if sorted(set(found) & set(blanks)) != sorted(blanks):
            return False, f"blank numbers missing ({sorted(set(blanks) - set(found))})"
    s = sim(a, b)
    if s < 0.95:
        return False, f"the two reads disagree ({s:.2f})"
    bad = [n for n, st in blanks.items() if not blank_ok(a, n, st)]
    if bad:
        return False, f"stored blank sentences not found in the read ({bad})"
    return True, None


def main(items_file):
    rows = [json.loads(l) for l in open(items_file) if l.strip()]
    out = PP / "zhcloze41" / os.environ.get("PP_TAG", "72b")
    out.mkdir(parents=True, exist_ok=True)
    todo = [r for r in rows if all((PP / p).exists() for p in r["pages"]) and not (out / f"{r['grp']}.json").exists()]
    print(len(todo), "passages to read", flush=True)
    if not todo:
        return
    from vllm import LLM, SamplingParams
    llm = LLM(model=os.environ.get("PP_VLM", "Qwen/Qwen2.5-VL-72B-Instruct-AWQ"), tensor_parallel_size=int(os.environ.get("PP_TP", "4")),
              gpu_memory_utilization=0.9, max_model_len=12288, max_num_seqs=8, limit_mm_per_prompt={"image": 2},
              mm_processor_kwargs={"max_pixels": 3_000_000}, allowed_local_media_path=str(PP), enforce_eager=bool(os.environ.get("PP_EAGER")))
    sp = SamplingParams(temperature=0, max_tokens=2500)
    for i in range(0, len(todo), 8):
        ch = todo[i:i + 8]
        msgs = [[{"role": "user", "content": [{"type": "image_url", "image_url": {"url": f"file://{PP / p}"}} for p in r["pages"][:2]]
                  + [{"type": "text", "text": PROMPTS[r["kind"]]}]}] for r in ch]
        for r, o in zip(ch, llm.chat(msgs, sp, use_tqdm=False)):
            (out / f"{r['grp']}.json").write_text(json.dumps({"grp": r["grp"], "raw": o.outputs[0].text}, ensure_ascii=False))
        print(f"{min(i + 8, len(todo))}/{len(todo)} read", flush=True)


def to_stem(text, blanks):
    """An agreed read as a site stem: each of the passage's own blanks (the numbers in `blanks`), however the read wrote
    it (（17） or (17), spaces, any ＿ after it), becomes （17）＿＿＿＿, the form the quiz page draws (lib/passageset.ts
    BLANK_SRC). Only the first copy of each number is a blank (a list's （1） elsewhere, or a repeat, is left alone), and
    line breaks after a blank stay (paragraphs are split on blank lines)."""
    want, done = {int(k) for k in blanks}, set()

    def sub(m):
        n = int(m.group(1))
        if n not in want or n in done:
            return m.group(0)
        done.add(n)
        return f"（{n}）＿＿＿＿"
    return re.sub(r"[（(][ \t\u3000]*(\d{1,2})[ \t\u3000]*[）)][ \t\u3000]*[＿_]*", sub, text)


def selftest():
    a = "小男孩大声喊道。可是，他（17）听到对方说一样的话。\n\n一回到家里，小男孩马上（18）妈妈的怀里，告诉妈妈山上有鬼。"
    blanks = {17: "可是，他（17）＿＿＿＿听到对方说一样的话", 18: "一回到家里，小男孩马上（18）＿＿＿＿妈妈的怀里，告诉妈妈"}
    assert check(a, a, blanks) == (True, None), check(a, a, blanks)
    assert check(a, a.replace("（18）", ""), blanks)[1].startswith("blank numbers missing")
    assert check(a, "完全不同的一段文字（17）（18）", blanks)[1].startswith("the two reads disagree")
    assert check(a.replace("一样的话", "别的事情"), a.replace("一样的话", "别的事情"), blanks)[1].startswith("stored blank sentences")
    r = "第一段文字，讲了一个故事。" * 10
    assert check(r, r, {}, "reading") == (True, None) and check(r, "完全不同" * 40, {}, "reading")[1].startswith("the two reads")
    assert check("短", "短", {}, "reading")[1] == "read too short"
    assert check("PICTURE", a, blanks)[1].startswith("page has a picture") and check(r, "PICTURE", {}, "reading")[1].startswith("page has")
    assert check(a, a, {str(k): v for k, v in blanks.items()}) == (True, None), "string keys from JSON"
    assert to_stem("他（17）听到，（18）＿妈妈，(19)看，（ 20 ）___走（1）首先", {"17": 0, "18": 0, 19: 0, 20: 0}) \
        == "他（17）＿＿＿＿听到，（18）＿＿＿＿妈妈，（19）＿＿＿＿看，（20）＿＿＿＿走（1）首先"
    assert to_stem("他（17）\n\n一回到家里（1）首先（1）", {1: 0, 17: 0}) == "他（17）＿＿＿＿\n\n一回到家里（1）＿＿＿＿首先（1）"
    print("zh_passage_ocr selftest ok")


if __name__ == "__main__":
    if sys.argv[1:2] == ["selftest"]:
        selftest()
        sys.exit()
    main(sys.argv[2])
