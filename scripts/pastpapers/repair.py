#!/usr/bin/env python3
"""Repair pass (owner, 23 Nov 2026): the server re-reads held MCQs from their exam pages.

  (a) crops: questions held as needs-figure-no-crop / crop-other-page get a new picture box, found by the vision model on
      the question's own page(s). Gated first: the model must find the known box of 80 questions whose crop is already right.
  (b) Chinese stems held as chi-no-blank-underline-lost: the model copies the question sentence and marks the underlined
      word as 「word」 (the way the generated Chinese questions mark the asked word). A read is used only when the sentence
      matches the first read and the marked word is in it (check_stem).

  repair.py pack [SEL ...]      dev: items.jsonl from the selections' rejects (default: the latest ones) + the gate set
  repair.py run ITEMS.jsonl     server (GPU; PP_ROOT = pastpapers folder, PP_VLM / PP_TP pick the model): results.jsonl
  repair.py gate RESULTS        dev: how well the boxes match the gate set (the bar: GATE_BAR of them, IoU and cover)
  repair.py apply RESULTS       dev: cut the new crops into <year>/recrop/, write <year>/stemfix.jsonl (only after the gate)
  repair.py selftest
load_pp select reads recrop/*.png like crops/*.png and stemfix.jsonl as the stem. Prints counts only."""
import json
import os
import random
import re
import sys
from difflib import SequenceMatcher
from pathlib import Path

TMP = Path("/data/alvin/tmp/cookie-codex")
DEV_PP = TMP / "pastpapers"
WORK = TMP / "repair"
SELS = [TMP / "ppimport" / s for s in ("math1826g/maths", "sci1826e/science", "eng1826c/english", "chi1826d/chinese")]
CROP_REASONS = ("needs-figure-no-crop", "crop-other-page")
STEM_REASON = "chi-no-blank-underline-lost"
GATE_N, GATE_BAR, IOU_MIN, COVER_MIN = 80, 0.90, 0.5, 0.9  # a gate box counts when IoU >= 0.5 and it covers 90% of the known box
SUBJ = {"maths": "Mathematics", "science": "Science", "english": "English", "chinese": "Chinese"}
PROMPT_CROP = ("This is a page from a Primary 6 {subj} exam paper. Find question {qno}; its text begins: \"{start}\". "
               "Give the bounding box of the diagram, picture, graph or table that belongs to question {qno}: not its text "
               "lines, not its answer options unless they are drawn inside the picture, and nothing of any other question. "
               "Reply with JSON only: {{\"bbox_2d\": [x1, y1, x2, y2]}} in this image's pixel coordinates, or {{\"none\": true}} "
               "if question {qno} has no picture on this page.")
PROMPT_STEM = ("这是新加坡小六华文试卷的一页。找到第{qno}题，题目开头是：“{start}”。题目里有字词下面画了线。请把第{qno}题的题目句子"
               "（不要选项）照原文抄出来，并用「」把画线的字词括起来。只回复JSON：{{\"stem\": \"...\"}}；如果第{qno}题没有画线的字词，"
               "回复{{\"none\": true}}。")
MARK = re.compile(r"「([^「」]{1,12})」")


def jl(p):
    p = Path(p)
    return [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()] if p.exists() else []


def parse(text):
    m = re.search(r"\{.*\}", text or "", re.S)
    try:
        return json.loads(m.group(0)) if m else None
    except Exception:
        return None


def fit28(w, h, max_pixels=1_600_000):
    """The size the image is sent at: a multiple of 28 each way within max_pixels, so the model's pixel coordinates are in
    exactly this frame (Qwen2.5-VL does not resize it again) and scale back to the page by plain ratios."""
    s = min(1.0, (max_pixels / (w * h)) ** 0.5)
    return max(28, int(w * s) // 28 * 28), max(28, int(h * s) // 28 * 28)


def box_ok(b, w, h):
    """A usable picture box in a w x h frame: inside it, at least 4% of the width and 2% of the height, not the whole page."""
    if not (isinstance(b, list) and len(b) == 4 and all(isinstance(x, (int, float)) for x in b)):
        return False
    x1, y1, x2, y2 = b
    return (0 <= x1 < x2 <= w * 1.01 and 0 <= y1 < y2 <= h * 1.01 and x2 - x1 >= 0.04 * w and y2 - y1 >= 0.02 * h
            and (y2 - y1) <= 0.8 * h)


def iou_cover(p, k):
    ix = max(0, min(p[2], k[2]) - max(p[0], k[0])) * max(0, min(p[3], k[3]) - max(p[1], k[1]))
    area = lambda b: (b[2] - b[0]) * (b[3] - b[1])
    return ix / (area(p) + area(k) - ix), ix / area(k)


def first_stem(text):
    """The first read's question sentence: the text before option (1)."""
    return re.split(r"\n\s*\(?1\)|\s\(1\)\s", text or "", maxsplit=1)[0].strip()


def check_stem(read, first_text):
    """(stem, why): the marked stem is used only when there is one or two 「」 marks, each word is in the first read, and
    the sentence without the marks matches the first read's sentence (an independent read of the same text)."""
    if not isinstance(read, dict) or read.get("none"):
        return None, "no-underline"
    st = str(read.get("stem") or "").strip()
    marks = MARK.findall(st)
    if not 1 <= len(marks) <= 2:
        return None, f"marks-{len(marks)}"
    fs = re.sub(r"\s+", "", first_stem(first_text))
    plain = re.sub(r"\s+", "", st.replace("「", "").replace("」", ""))
    if not all(m in fs for m in marks):
        return None, "marked-word-not-in-first-read"
    if SequenceMatcher(None, plain, fs).ratio() < 0.85:
        return None, "sentence-differs-from-first-read"
    return st, None


def pack(sels):
    WORK.mkdir(parents=True, exist_ok=True)
    items, gate = [], []
    for sel in sels:
        subject = sel.name
        want = {r["id"]: r["reason"] for r in jl(sel / "rejects.jsonl") if r.get("reason") in CROP_REASONS + (STEM_REASON,)}
        live = {r["src_id"] for r in jl(sel / "selected.jsonl") if r.get("crops")}
        for y in range(2018, 2027):
            base = DEV_PP / subject / str(y)
            qs = {q["id"]: q for q in jl(base / "questions.jsonl")}
            for q in jl(base / "merged.jsonl"):
                if not q.get("pages"):
                    continue
                row = {"id": q["id"], "subject": subject, "year": y, "qno": q.get("qno"), "pages": sorted(q["pages"])[:2],
                       "start": (q.get("text") or "")[:120]}
                if q["id"] in want:
                    items.append(dict(row, job="stem" if want[q["id"]] == STEM_REASON else "crop",
                                      **({"text": q.get("text") or ""} if want[q["id"]] == STEM_REASON else {})))
                elif q["id"] in live:  # a question whose crop is right: its known box is the gate's answer
                    figs = [f for f in (qs.get(q["id"]) or {}).get("figures", []) if isinstance(f, dict) and f.get("bbox")
                            and f.get("page") in q["pages"]]
                    if len(figs) == 1:
                        gate.append(dict(row, job="crop", pages=[figs[0]["page"]], gate={"page": figs[0]["page"], "bbox": figs[0]["bbox"]}))
    random.Random(23).shuffle(gate)
    gate = gate[:GATE_N]
    out = WORK / "items.jsonl"
    out.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in items + gate))
    c = {}
    for r in items:
        c[(r["subject"], r["job"])] = c.get((r["subject"], r["job"]), 0) + 1
    print(f"{len(items)} to repair {dict(sorted(c.items()))}, {len(gate)} gate questions -> {out}")


def run(items_file):
    from PIL import Image
    pp = Path(os.environ.get("PP_ROOT", "/data/alvin/cookie/pastpapers_full"))
    out = Path(items_file).with_name("results.jsonl")
    done = {(r["id"], r.get("page")) for r in jl(out)}
    tmp = Path(items_file).with_name("img")
    tmp.mkdir(exist_ok=True)
    todo = []
    for r in jl(items_file):
        for p in r["pages"]:
            src = pp / r["subject"] / str(r["year"]) / "pages" / f"p{p:04d}.jpg"
            if (r["id"], p) in done or not src.exists():
                continue
            im = Image.open(src)
            W, H = fit28(*im.size)
            dst = tmp / f"{r['subject']}-{r['year']}-p{p:04d}.jpg"
            if not dst.exists():
                im.convert("L").resize((W, H)).save(dst, quality=85)
            todo.append((r, p, dst, W, H))
    print(len(todo), "page reads to do", flush=True)
    if not todo:
        return
    from vllm import LLM, SamplingParams
    llm = LLM(model=os.environ.get("PP_VLM", "Qwen/Qwen2.5-VL-72B-Instruct-AWQ"), tensor_parallel_size=int(os.environ.get("PP_TP", "4")),
              gpu_memory_utilization=0.9, max_model_len=8192, max_num_seqs=16, limit_mm_per_prompt={"image": 1},
              mm_processor_kwargs={"max_pixels": 1_700_000}, allowed_local_media_path=str(tmp.parent), enforce_eager=bool(os.environ.get("PP_EAGER")))
    sp = SamplingParams(temperature=0, max_tokens=400)
    with open(out, "a", encoding="utf-8") as f:
        for i in range(0, len(todo), 32):
            ch = todo[i:i + 32]
            msgs = [[{"role": "user", "content": [{"type": "image_url", "image_url": {"url": f"file://{dst}"}},
                     {"type": "text", "text": (PROMPT_STEM if r["job"] == "stem" else PROMPT_CROP).format(
                         subj=SUBJ[r["subject"]], qno=r["qno"], start=r["start"].replace('"', "'"))}]}] for r, _, dst, _, _ in ch]
            for (r, p, _, W, H), o in zip(ch, llm.chat(msgs, sp, use_tqdm=False)):
                f.write(json.dumps({"id": r["id"], "subject": r["subject"], "year": r["year"], "job": r["job"], "page": p,
                                    "w": W, "h": H, "raw": o.outputs[0].text, **({"gate": r["gate"]} if "gate" in r else {}),
                                    **({"text": r["text"]} if "text" in r else {})}, ensure_ascii=False) + "\n")
            f.flush()
            print(f"{min(i + 32, len(todo))}/{len(todo)}", flush=True)


def page_size(subject, year, page):
    from PIL import Image
    with Image.open(DEV_PP / subject / str(year) / "pages" / f"p{page:04d}.jpg") as im:
        return im.size


def to_page(b, r):
    """The model's box (in the w x h frame it saw) in the dev page's pixels."""
    W, H = page_size(r["subject"], r["year"], r["page"])
    return [round(b[0] * W / r["w"]), round(b[1] * H / r["h"]), round(b[2] * W / r["w"]), round(b[3] * H / r["h"])]


def gate(results):
    rows = [r for r in jl(results) if "gate" in r]
    hit = 0
    for r in rows:
        b = (parse(r["raw"]) or {}).get("bbox_2d")
        if box_ok(b, r["w"], r["h"]):
            iou, cov = iou_cover(to_page(b, r), r["gate"]["bbox"])
            hit += iou >= IOU_MIN and cov >= COVER_MIN
    rate = hit / max(1, len(rows))
    print(f"gate: {hit}/{len(rows)} known boxes found (IoU >= {IOU_MIN}, covering >= {COVER_MIN:.0%}): {rate:.1%}, bar {GATE_BAR:.0%}"
          f" -> {'PASSED' if rate >= GATE_BAR and len(rows) >= 50 else 'FAILED'}")
    return rate >= GATE_BAR and len(rows) >= 50


def apply(results, force=False):
    from PIL import Image
    if not gate(results) and not force:
        sys.exit("the crop gate failed: no crops written (stems are written separately with --stems-only)")
    stems_only = force == "stems"
    c = {"crops": 0, "no-box": 0, "stems": 0}
    why = {}
    fixes = {}
    for r in jl(results):
        if "gate" in r:
            continue
        if r["job"] == "crop" and not stems_only:
            b = (parse(r["raw"]) or {}).get("bbox_2d")
            if not box_ok(b, r["w"], r["h"]):
                c["no-box"] += 1
                continue
            x1, y1, x2, y2 = to_page(b, r)
            pad = 12  # the model's box sits tight on the lines; `figures` grows a crop still touching an edge
            src = DEV_PP / r["subject"] / str(r["year"]) / "pages" / f"p{r['page']:04d}.jpg"
            d = DEV_PP / r["subject"] / str(r["year"]) / "recrop"
            d.mkdir(exist_ok=True)
            with Image.open(src) as im:
                im.convert("L").crop((max(0, x1 - pad), max(0, y1 - pad), min(im.width, x2 + pad), min(im.height, y2 + pad))).save(
                    d / f"{r['id']}-p{r['page']:04d}.png", optimize=True)
            c["crops"] += 1
        elif r["job"] == "stem":
            st, w = check_stem(parse(r["raw"]), r["text"])
            if st:
                fixes.setdefault((r["subject"], r["year"]), {})[r["id"]] = st
            else:
                why[w] = why.get(w, 0) + 1
    for (subject, y), fx in fixes.items():
        f = DEV_PP / subject / str(y) / "stemfix.jsonl"
        have = {x["id"]: x for x in jl(f)}
        have.update({i: {"id": i, "stem": s, "src": "repair.py"} for i, s in fx.items()})
        f.write_text("".join(json.dumps(x, ensure_ascii=False) + "\n" for x in have.values()), encoding="utf-8")
        c["stems"] += len(fx)
    print(c, "stems not used:", why)


def selftest():
    w, h = fit28(1241, 1755); assert w % 28 == 0 and h % 28 == 0 and w * h <= 1_600_000 and abs(w / h - 1241 / 1755) < 0.02
    assert box_ok([10, 10, 300, 200], 1036, 1540) and not box_ok([10, 10, 20, 200], 1036, 1540) and not box_ok([0, 0, 1000, 1500], 1036, 1540)
    assert not box_ok(None, 100, 100) and not box_ok([1, 2, 3], 100, 100)
    iou, cov = iou_cover([0, 0, 10, 10], [0, 0, 10, 10]); assert iou == 1 and cov == 1
    iou, cov = iou_cover([0, 0, 10, 10], [5, 0, 15, 10]); assert abs(iou - 1 / 3) < 1e-9 and cov == 0.5
    first = "下面句子中画线的词语是什么意思？\n他做事一向很认真。\n(1) 仔细 (2) 马虎 (3) 快速 (4) 随便"
    good = {"stem": "下面句子中画线的词语是什么意思？他做事一向很「认真」。"}
    assert check_stem(good, first) == (good["stem"], None)
    assert check_stem({"stem": "他做事一向很认真。"}, first)[1] == "marks-0"
    assert check_stem({"stem": "下面句子中画线的词语是什么意思？他做事一向很「仔细」。"}, first)[1] == "marked-word-not-in-first-read"
    assert check_stem({"stem": "「他」今天去了动物园看大象和长颈鹿。"}, first)[1] in ("marked-word-not-in-first-read", "sentence-differs-from-first-read")
    assert check_stem({"none": True}, first)[1] == "no-underline"
    assert first_stem("Which is right?\n(1) a\n(2) b") == "Which is right?"
    print("repair selftest ok")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "pack":
        pack([Path(s) for s in sys.argv[2:]] or SELS)
    elif cmd == "run":
        run(sys.argv[2])
    elif cmd == "gate":
        gate(sys.argv[2])
    elif cmd == "apply":
        apply(sys.argv[2], "stems" if "--stems-only" in sys.argv else False)
    elif cmd == "selftest":
        selftest()
    else:
        sys.exit(__doc__)
