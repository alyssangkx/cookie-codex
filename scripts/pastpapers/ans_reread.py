#!/usr/bin/env python3
"""Two independent VL-32B reads of MCQ answer-key pages found by anskey_ocr.py find-answer-pages (server job, GPU).

  ans_reread.py --pages reread/pages-science.jsonl [--pages ...]     (PP_ROOT = the pastpapers folder on the server)
Each input row {subject, year, paper, page, n_mcq, mcq: [...]}. Read A: the original page image (vLLM caps both reads at
3 MP), row-wise prompt. Read B: the page converted to grey, contrast-stretched and sharpened (damps a coloured watermark stamp), 3 MP,
cell-pair prompt. A cell is final only when A and B give the same option and the question number is one of the paper's
MCQ numbers. Writes PP_ROOT/<subject>/<year>/ansreread/pNNNN-<sha1(paper)[:8]>.json (one file per paper and page):
  {paper, page, expected: [...], cells: {"7": {"a": "3", "b": "3", "final": "3"}}, dropped: [numbers read that are not
  MCQs of the paper], gate: <flag or null>}
(a page the paper owns twice, or a page that is not a key, simply yields no final cells). load_pp.py select
--reread-keys uses the final cells (answer_src 'vision-reread'). Prints counts only."""
import argparse, hashlib, json, os, re, sys
from pathlib import Path

PP = Path(os.environ.get("PP_ROOT", "/data/alvin/cookie/pastpapers_full"))
CELL = re.compile(r"\bQ?\s*(\d{1,2})\s*[=:\-]\s*\(?([1-4])\)?(?![\w.])")
PA = ("This page is a marking scheme. Find the table of multiple-choice answers (each cell pair is a question number such as Q7 and a single digit 1-4 printed with it). "
      "Ignore every other answer and any watermark. Read the table row by row, left to right, exactly as printed, one table row per line, in the form: Q1=3 Q2=1 Q3=2 ... "
      "Do not guess or continue a pattern; write only what is printed. Reply with the lines only.")
PB = ("This page is a marking scheme with a table of multiple-choice answers. For every cell pair of that table, in reading order, write one line 'Qn=a' where n is the question "
      "number printed and a is the single digit 1-4 printed with it. Copy each cell carefully; do not infer values; ignore long answers and watermarks. Reply with the lines only.")


def parse(t):
    d = {}
    for n, a in CELL.findall(t):
        d.setdefault(int(n), a)
    return d


def boost(src, dst, max_pixels=3_000_000):
    """Grey, autocontrast (1% clipped), unsharp, scaled to about max_pixels."""
    from PIL import Image, ImageFilter, ImageOps
    im = ImageOps.autocontrast(Image.open(src).convert("L"), cutoff=1).filter(ImageFilter.UnsharpMask(radius=2, percent=150))
    k = (max_pixels / (im.width * im.height)) ** 0.5
    if k != 1:
        im = im.resize((int(im.width * k), int(im.height * k)), Image.LANCZOS)
    im.save(dst)


def gate(vals, same=7, cyc=8):
    """Flags a page whose agreed cells look like a continued pattern, not a printed key: `same` identical answers on
    consecutive question numbers, or a 1234 / 4321 cycle `cyc` long. A random 40-question key has a 7-run about 0.6% of
    the time (a 4-run about half the time, so short runs are normal). Run lengths count question numbers spanned; a run
    may span ONE missing number (a cell the reads disagreed on, or that neither returned), so one disputed cell cannot
    hide a made-up pattern; a second gap or a gap of two numbers ends it."""
    run_s = run_c = 0
    gap_s = gap_c = False
    prev_n = prev_v = last_d = None
    for n, v in sorted(vals.items()):
        step = n - prev_n if prev_n is not None else 0
        d = (int(v) - int(prev_v)) % 4 if prev_n is not None else None  # 1 = up one (4 -> 1 wraps), 3 = down one
        if v == prev_v and (step == 1 or (step == 2 and not gap_s)):
            run_s, gap_s = run_s + step, gap_s or step == 2
        else:
            run_s, gap_s = 1, False
        if step == 1 and d in (1, 3):
            run_c, gap_c = (run_c + 1, gap_c) if d == last_d else (2, False)
            last_d = d
        elif step == 2 and d == 2 and last_d in (1, 3) and not gap_c:
            run_c, gap_c = run_c + 2, True  # up two or down two across the gap continues the direction already seen
        else:
            run_c, gap_c, last_d = 1, False, None
        if run_s >= same:
            return "identical run"
        if run_c >= cyc:
            return "ascending/descending cycle"
        prev_n, prev_v = n, v
    return None


def out_name(r):
    return f"p{r['page']:04d}-{hashlib.sha1(str(r['paper']).encode()).hexdigest()[:8]}.json"


def merge(pa, pb, expected):
    """(cells for the paper's MCQ numbers, sorted numbers read that are not among them)."""
    cells, dropped = {}, []
    for n in sorted(set(pa) | set(pb)):
        if n in expected:
            cells[str(n)] = {"a": pa.get(n), "b": pb.get(n), "final": pa.get(n) if pa.get(n) == pb.get(n) else None}
        else:
            dropped.append(n)
    return cells, dropped


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pages", action="append", required=True)
    ap.add_argument("--tmp", default=os.environ.get("PP_TMP", "/data/alvin/cookie/tmp/ansreread"))
    ap.add_argument("--batch", type=int, default=16)
    a = ap.parse_args()
    rows = [json.loads(l) for f in a.pages for l in open(f) if l.strip()]
    todo, seen = [], set()
    for r in rows:
        od = PP / r["subject"] / str(r["year"]) / "ansreread"
        jpg = PP / r["subject"] / str(r["year"]) / "pages" / f"p{r['page']:04d}.jpg"
        if not jpg.exists():
            continue
        od.mkdir(parents=True, exist_ok=True)
        if not (od / out_name(r)).exists() and (od / out_name(r)) not in seen:
            seen.add(od / out_name(r))
            todo.append((r, jpg, od))
    print(len(todo), "pages to read", flush=True)
    if not todo:
        return
    tmp = Path(a.tmp)
    tmp.mkdir(parents=True, exist_ok=True)
    from vllm import LLM, SamplingParams
    llm = LLM(model="Qwen/Qwen2.5-VL-32B-Instruct-AWQ", tensor_parallel_size=int(os.environ.get("PP_TP", "2")), gpu_memory_utilization=0.9,
              max_model_len=12288, max_num_seqs=8, limit_mm_per_prompt={"image": 1}, mm_processor_kwargs={"max_pixels": 3_000_000},
              allowed_local_media_path="/", enforce_eager=bool(os.environ.get("PP_EAGER")))
    sp = SamplingParams(temperature=0, max_tokens=600)
    for i in range(0, len(todo), a.batch):
        ch = todo[i:i + a.batch]
        boosted = []
        for r, jpg, _ in ch:
            b = tmp / f"{r['subject']}-{r['year']}-p{r['page']:04d}.png"
            boost(jpg, b)
            boosted.append(b)

        def msgs(paths, prompt):
            return [[{"role": "user", "content": [{"type": "image_url", "image_url": {"url": f"file://{p}"}}, {"type": "text", "text": prompt}]}] for p in paths]
        ra = llm.chat(msgs([j for _, j, _ in ch], PA), sp, use_tqdm=False)
        rb = llm.chat(msgs(boosted, PB), sp, use_tqdm=False)
        for (r, _, od), x, y in zip(ch, ra, rb):
            cells, dropped = merge(parse(x.outputs[0].text), parse(y.outputs[0].text), set(r["mcq"]))
            fin = {int(n): c["final"] for n, c in cells.items() if c["final"]}
            (od / out_name(r)).write_text(json.dumps({"paper": r["paper"], "page": r["page"], "expected": r["mcq"], "cells": cells,
                                                      "dropped": dropped, "gate": gate(fin)}))
        print("done", i + len(ch), "/", len(todo), flush=True)
    print("finished; final cells:", sum(1 for f in PP.glob("*/*/ansreread/p*.json") for c in json.load(open(f))["cells"].values() if c["final"]))


if __name__ == "__main__":
    if sys.argv[1:2] == ["selftest"]:
        assert parse("Q1=3 Q2 = 1\nQ10:4 Q11=5") == {1: "3", 2: "1", 10: "4"}
        assert merge({1: "3", 2: "1", 99: "2"}, {1: "3", 2: "2"}, {1, 2}) == ({"1": {"a": "3", "b": "3", "final": "3"}, "2": {"a": "1", "b": "2", "final": None}}, [99])
        assert gate({n: "2" for n in range(1, 8)}) == "identical run" and not gate({n: "2" for n in range(1, 7)})
        assert gate({1: "2", 2: "2", 3: "2", 5: "2", 6: "2", 7: "2", 8: "2"})  # one disputed cell does not hide the run
        assert not gate({1: "2", 2: "2", 3: "2", 6: "2", 7: "2", 8: "2", 9: "2"})  # a longer gap breaks it
        assert not gate({n: "2" for n in range(1, 14, 2)})  # alternate cells disputed: a second gap ends the run
        assert gate({1: "1", 2: "2", 3: "3", 4: "4", 6: "2", 7: "3", 8: "4", 9: "1", 10: "2"})  # cycle across one gap
        assert gate({1: "4", 2: "3", 3: "2", 5: "4", 6: "3", 7: "2", 8: "1"})  # descending cycle across one gap
        assert not gate({1: "1", 2: "2", 3: "3", 5: "1", 6: "2", 7: "3", 9: "1", 10: "2"})  # two gaps: no cycle
        assert gate({n: "1234"[(n - 1) % 4] for n in range(1, 9)}) and gate({n: "4321"[(n - 1) % 4] for n in range(1, 9)})
        assert not gate({n: "1234"[(n - 1) % 4] for n in range(1, 8)}) and not gate({1: "1", 2: "2", 3: "3", 4: "4", 5: "3", 6: "2", 7: "1", 8: "4"})
        assert not gate({1: "1", 2: "2", 3: "3", 4: "4", 11: "2", 12: "2", 13: "2", 14: "2"})  # short runs are normal
        assert out_name({"page": 7, "paper": "X"}) != out_name({"page": 7, "paper": "Y"})
        print("ans_reread selftest ok"); sys.exit()
    main()
