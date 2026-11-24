#!/usr/bin/env python3
"""Passages as text (owner, 24 Nov 2026: "all subjects OCR any text; pictures, tables and figures stay images"). The English
passage sections are read from their exam pages by the vision model, with what the question needs kept as markup:
  {{16|entrusted}}   an underlined word or phrase with its question number (Vocabulary Cloze, Editing)
  [[31]]             a numbered blank (Grammar Cloze, Comprehension Cloze); printed letters next to it stay: b[[41]]
A second, different model reads every passage too; a passage is used only when both reads carry the same markers, the same
underlined words, and nearly the same text (check).

  passage.py pack                 dev: sections.jsonl (one per passage section of a paper) -> /data/alvin/tmp/cookie-codex/passage
  passage.py run ITEMS            server (GPU; PP_ROOT, PP_VLM, PP_TP, PP_OUT): read.jsonl or PP_OUT, resumable
  passage.py check [--sample N]   dev: passages.jsonl {sec, st, passage, markers}; prints counts
  passage.py selftest"""
import collections
import difflib
import json
import os
import random
import re
import sys
from pathlib import Path

TMP = Path("/data/alvin/tmp/cookie-codex")
WORK = Path(os.environ.get("PP_WORK", str(TMP / "passage")))
SECTIONS = {  # sub-topic: (name on the paper, what to mark)
    "eng-vocab-cloze": ("Vocabulary Cloze", "under"),
    "eng-editing": ("Editing for Spelling and Grammar", "under"),
    "eng-grammar-cloze": ("Grammar Cloze", "blank"),
    "eng-comp-cloze": ("Comprehension Cloze", "blank"),
}
MARK = {
    "under": "Each underlined word or phrase has a question number printed next to or under it. Write it as {{N|word}} with "
             "the number and the underlined words exactly, e.g. {{16|entrusted}} or {{18|detailed plan for their trip}}.",
    "blank": "Each numbered blank is a gap the student fills. Write it as [[N]] with its number, e.g. [[31]]. If letters are "
             "printed in or next to the blank (a hint), keep them next to it, e.g. b[[41]].",
}
PROMPT = ("These are pages from a Singapore Primary 6 English exam paper. Transcribe the {name} passage (questions {a} to {b}) "
          "exactly as printed, word for word, with its punctuation. {mark} Leave out the instructions, any word box or list of "
          "options, the question numbers in the margin, page headers and footers. Separate paragraphs with a blank line. If the "
          "passage has a title, put it on the first line. Reply with JSON only: {{\"passage\": \"...\"}}. If the passage is not "
          "on these pages, reply {{\"none\": true}}.")
UNDER = re.compile(r"\{\{\s*(\d{1,3})\s*\|\s*([^{}|]+?)\s*\}\}")
BLANK = re.compile(r"\[\[\s*(\d{1,3})\s*\]\]")


def jl(p):
    p = Path(p)
    return [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()] if p.exists() else []


def parse(text):
    m = re.search(r"\{.*\}", text or "", re.S)
    try:
        return json.loads(m.group(0)) if m else None
    except Exception:
        return None


def markers(passage, kind):
    """{question number: underlined words (lower case) or ""} in the order they appear; None when a number repeats."""
    found = [(int(n), " ".join(w.lower().split())) for n, w in UNDER.findall(passage)] if kind == "under" \
        else [(int(n), "") for n in BLANK.findall(passage)]
    d = dict(found)
    return d if len(d) == len(found) else None


def plain(passage):
    """The words alone, for comparing two reads."""
    t = BLANK.sub(" ", UNDER.sub(lambda m: m.group(2), passage or ""))
    return " ".join(re.sub(r"[^\w']+", " ", t.lower().replace("’", "'")).split())


def clusters(qs):
    """A paper's questions of one section, split where their pages jump (a file holding two papers), as runs of pages."""
    qs = sorted((q for q in qs if q.get("pages")), key=lambda q: min(q["pages"]))
    out, cur = [], []
    for q in qs:
        if cur and min(q["pages"]) - max(p for c in cur for p in c["pages"]) > 1:
            out.append(cur)
            cur = []
        cur.append(q)
    return out + ([cur] if cur else [])


def pack():
    WORK.mkdir(parents=True, exist_ok=True)
    base = TMP / "pastpapers" / "english"
    rows = []
    for y in range(2018, 2027):
        tags = {t["id"]: t for t in jl(base / str(y) / "tags72.jsonl")}
        by = collections.defaultdict(list)
        for q in jl(base / str(y) / "merged.jsonl"):
            st = (tags.get(q["id"]) or {}).get("st")
            if st in SECTIONS and isinstance(q.get("qno"), int):
                by[(q.get("paper"), st)].append(q)
        for (paper, st), qs in by.items():
            for n, c in enumerate(clusters(qs)):
                pages = sorted({p for q in c for p in q["pages"]})
                if len(c) < 3 or pages[-1] - pages[0] > 2:
                    continue  # one or two stray questions, or bad page data
                qn = sorted({q["qno"] for q in c})
                # and the page before: a passage often starts on the page before its first question (vocabulary cloze options,
                # a cloze's instruction at the foot of a page)
                rows.append({"sec": f"{paper}-{st}-{n}", "year": y, "paper": paper, "st": st, "kind": SECTIONS[st][1],
                             "pages": list(range(max(1, pages[0] - 1), pages[-1] + 1)), "a": qn[0], "b": qn[-1], "qnos": qn,
                             "ids": [q["id"] for q in sorted(c, key=lambda q: q["qno"])]})
    (WORK / "sections.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
    print(f"{len(rows)} passage sections ({dict(collections.Counter(r['st'] for r in rows))}) -> {WORK / 'sections.jsonl'}")


def run(items_file):
    from PIL import Image
    items_file = Path(items_file).resolve()
    pp = Path(os.environ.get("PP_ROOT", "/data/alvin/cookie/pastpapers_full"))
    out = items_file.with_name(os.environ.get("PP_OUT", "read.jsonl"))
    done = {r["sec"] for r in jl(out)}
    img = items_file.with_name("img")
    img.mkdir(exist_ok=True)
    todo = []
    for r in jl(items_file):
        if r["sec"] in done:
            continue
        files = []
        for p in r["pages"]:
            src, dst = pp / "english" / str(r["year"]) / "pages" / f"p{p:04d}.jpg", img / f"{r['year']}-p{p:04d}.jpg"
            if not src.exists():
                break
            if not dst.exists():
                im = Image.open(src).convert("L")
                im.thumbnail((1400, 1960))
                im.save(dst, quality=88)
            files.append(dst)
        if len(files) == len(r["pages"]):
            todo.append((r, files))
    print(len(todo), "passages to read", flush=True)
    if not todo:
        return
    from vllm import LLM, SamplingParams
    model = os.environ.get("PP_VLM", "Qwen/Qwen2.5-VL-72B-Instruct-AWQ")
    llm = LLM(model=model, tensor_parallel_size=int(os.environ.get("PP_TP", "4")), gpu_memory_utilization=0.9,
              max_model_len=16384, max_num_seqs=8, limit_mm_per_prompt={"image": 4}, mm_processor_kwargs={"max_pixels": 1_600_000},
              allowed_local_media_path=str(img.parent), enforce_eager=bool(os.environ.get("PP_EAGER")))
    sp = SamplingParams(temperature=0, max_tokens=2500)
    with open(out, "a", encoding="utf-8") as f:
        for i in range(0, len(todo), 16):
            ch = todo[i:i + 16]
            msgs = [[{"role": "user", "content": [*({"type": "image_url", "image_url": {"url": f"file://{x}"}} for x in files),
                     {"type": "text", "text": PROMPT.format(name=SECTIONS[r["st"]][0], a=r["a"], b=r["b"], mark=MARK[r["kind"]])}]}]
                    for r, files in ch]
            for (r, _), o in zip(ch, llm.chat(msgs, sp, use_tqdm=False)):
                f.write(json.dumps({"sec": r["sec"], "model": model, "raw": o.outputs[0].text}, ensure_ascii=False) + "\n")
            f.flush()
            print(f"{min(i + 16, len(todo))}/{len(todo)}", flush=True)


def judge(r, raw1, raw2):
    """(passage, None) when both reads agree, else (None, why)."""
    v1, v2 = parse(raw1) or {}, parse(raw2) or {}
    p1, p2 = v1.get("passage"), v2.get("passage")
    if not p1 or not p2:
        return None, "not read" if not (p1 or p2) else "one read missing"
    m1, m2 = markers(p1, r["kind"]), markers(p2, r["kind"])
    if m1 is None or m2 is None:
        return None, "a question number repeats"
    want = set(r["qnos"])
    if set(m1) != want:
        return None, "markers differ from the questions"
    if m1 != m2:
        return None, "the two reads mark different words" if set(m2) == want else "the second read's markers differ"
    if difflib.SequenceMatcher(None, plain(p1), plain(p2), autojunk=False).ratio() < 0.95:
        return None, "the two reads' text differs"
    return p1.strip(), None


def check(sample=0):
    secs = {r["sec"]: r for r in jl(WORK / "sections.jsonl")}
    a = {r["sec"]: r["raw"] for r in jl(WORK / "read.jsonl")}
    b = {r["sec"]: r["raw"] for r in jl(WORK / "read2.jsonl")}
    ok, why = [], collections.Counter()
    for s, r in secs.items():
        p, w = judge(r, a.get(s), b.get(s))
        why[(r["st"], w or "kept")] += 1
        if p:
            ok.append({"sec": s, "st": r["st"], "year": r["year"], "paper": r["paper"], "ids": r["ids"], "passage": p,
                       "markers": markers(p, r["kind"])})
    (WORK / "passages.jsonl").write_text("".join(json.dumps(x, ensure_ascii=False) + "\n" for x in ok))
    for st in SECTIONS:
        print(st + ": " + ", ".join(f"{w} {n}" for (s, w), n in sorted(why.items(), key=lambda kv: -kv[1]) if s == st))
    for x in random.Random(3).sample(ok, min(sample, len(ok))):
        print(f"\n[{x['st']}] {x['sec']}\n{x['passage'][:700]}")


def selftest():
    p = "Benedict read {{17|widely}} to find out more. They made a {{18| detailed plan  for their trip }}."
    assert markers(p, "under") == {17: "widely", 18: "detailed plan for their trip"}
    assert markers("A [[31]] and b[[32]].", "blank") == {31: "", 32: ""}
    assert markers("A [[31]] and [[31]].", "blank") is None, "a repeated number is a misread"
    assert plain("He read {{17|widely}} [[3]] more.") == "he read widely more"
    r = {"kind": "under", "qnos": [17, 18]}
    raw = lambda t: json.dumps({"passage": t})
    assert judge(r, raw(p), raw(p.replace("Benedict", "Benedict "))) == (p, None)
    assert judge(r, raw(p), raw(p.replace("|widely", "|wisely")))[1] == "the two reads mark different words"
    assert judge(r, raw(p), raw(p.replace("{{18| detailed plan  for their trip }}", "detailed plan")))[1] == "the second read's markers differ"
    assert judge({"kind": "under", "qnos": [16, 17, 18]}, raw(p), raw(p))[1] == "markers differ from the questions"
    qs = [{"pages": [4]}, {"pages": [4]}, {"pages": [5]}, {"pages": [30]}, {"pages": [30]}]
    assert [len(c) for c in clusters(qs)] == [3, 2], "a jump in pages starts another paper's section"
    print("passage selftest ok")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "pack":
        pack()
    elif cmd == "run":
        run(sys.argv[2])
    elif cmd == "check":
        check(int(sys.argv[sys.argv.index("--sample") + 1]) if "--sample" in sys.argv else 0)
    elif cmd == "selftest":
        selftest()
    else:
        sys.exit(__doc__)
