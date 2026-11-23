#!/usr/bin/env python3
"""Repair pass (owner, 23 Nov 2026): the server re-reads held MCQs from their exam pages.

  (a) crops: questions held as needs-figure-no-crop / crop-other-page get a new picture box, found by the vision model on
      the question's own page(s). Gated first: the model must find the known box of 80 questions whose crop is already right.
  (b) Chinese stems held as chi-no-blank-underline-lost: the model copies the question sentence and marks the underlined
      word as 「word」 (the way the generated Chinese questions mark the asked word). A read is used only when the sentence
      matches the first read and the marked word is in it (check_stem).

  repair.py pack [SEL ...]      dev: items.jsonl from the selections' rejects (default: the latest ones) + the gate set
  repair.py run ITEMS.jsonl     server (GPU; PP_ROOT = pastpapers folder, PP_VLM / PP_TP pick the model; PP_JOBS=stem
                                reads only the stems, PP_OUT names the results file): results.jsonl. The stems' second
                                read must use another model: PP_VLM=Qwen/Qwen2.5-VL-32B-Instruct-AWQ PP_JOBS=stem
                                PP_OUT=results2.jsonl (apply refuses a second read from the first read's model)
  repair.py gate RESULTS        dev: how well the boxes match the gate set (the bar: GATE_BAR of them, IoU and cover)
  repair.py apply RESULTS [--second RESULTS2] [--stems-only]
                                dev: cut the new crops into <year>/recrop/ (only after the gate; only on the question's
                                first page), write <year>/stemfix.jsonl (only stems two independent reads mark alike)
  repair.py audit-pack [SEL ...] dev: every selected question with a picture (its crop box from questions.jsonl) ->
                                repair/audit/items.jsonl; run it like the repair items (results in repair/audit/)
  repair.py audit-report RESULTS dev: model box against each crop: crops that miss part of the model's picture, crops much
                                bigger than it (extra text, another question), pages where the model sees no picture;
                                draws a sample of each on its page (repair/audit/look/) for a person to judge
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
SELS = [TMP / "ppimport" / s for s in ("math1826g/maths", "sci1826f/science", "eng1826c/english", "chi1826d/chinese")]
AUDIT = WORK / "audit"
MISS, EXTRA = 0.15, 0.5  # flag a crop leaving out 15% of the model's box, or one whose area is half outside it
CROP_REASONS = ("needs-figure-no-crop", "crop-other-page")
STEM_REASON = "chi-no-blank-underline-lost"
GATE_N, GATE_BAR, IOU_MIN, COVER_MIN = 80, 0.90, 0.5, 0.9  # a gate box counts when IoU >= 0.5 and it covers 90% of the known box
GATE_NEG = 40  # text-only questions: the model must say "none" (a box there is a picture that does not exist)
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
DEFAULT_VLM = "Qwen/Qwen2.5-VL-72B-Instruct-AWQ"


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
    """The first read's question sentence: the text before option 1, printed (1), （1） or "1." on a new line."""
    return re.split(r"(?:(?<=[\s。？！.?!:：])|^)[（(]\s*1\s*[)）]|\n\s*1\s*[.、]", text or "", maxsplit=1)[0].strip()


def text_hash(text):
    import hashlib
    return hashlib.sha1((text or "").encode()).hexdigest()[:12]


UNDERLINE_WORDS = re.compile(r"[画划](?:了)?(?:横)?线(?:的)?(?=词语|字词|词|字|部分|句子)")  # the instruction only, not 规划线路


def unline(stem):
    """The site shows the asked word in 「」, not underlined: '画线的词语' becomes '「」里的词语'."""
    return UNDERLINE_WORDS.sub("「」里的", stem)


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
    if list(WORK.glob("results*.jsonl")):  # gate and apply read every row: old reads must not mix with a new pack
        sys.exit(f"{WORK} holds results of an earlier pack: move them aside first")
    items, gate, neg = [], [], []
    for sel in sels:
        subject = sel.name
        want = {r["id"]: r["reason"] for r in jl(sel / "rejects.jsonl") if r.get("reason") in CROP_REASONS + (STEM_REASON,)}
        sel_rows = jl(sel / "selected.jsonl")
        live = {r["src_id"] for r in sel_rows if r.get("crops")}
        plain = {r["src_id"] for r in sel_rows if not r.get("crops")} if subject in ("maths", "science") else set()
        for y in range(2018, 2027):
            base = DEV_PP / subject / str(y)
            qs = {q["id"]: q for q in jl(base / "questions.jsonl")}
            for q in jl(base / "merged.jsonl"):
                if not q.get("pages"):
                    continue
                row = {"id": q["id"], "subject": subject, "year": y, "qno": q.get("qno"), "pages": sorted(q["pages"])[:1 if q["id"] in want and want[q["id"]] != STEM_REASON else 2],
                       "start": (q.get("text") or "")[:120]}
                if q["id"] in want:
                    items.append(dict(row, job="stem" if want[q["id"]] == STEM_REASON else "crop",
                                      **({"text": q.get("text") or "", "first": text_hash(q.get("text"))} if want[q["id"]] == STEM_REASON else {})))
                elif q["id"] in live:  # a question whose crop is right: its known box is the gate's answer
                    figs = [f for f in (qs.get(q["id"]) or {}).get("figures", []) if isinstance(f, dict) and f.get("bbox")
                            and f.get("page") in q["pages"]]
                    if len(figs) == 1:
                        gate.append(dict(row, job="crop", pages=[figs[0]["page"]], gate={"page": figs[0]["page"], "bbox": figs[0]["bbox"]}))
                elif q["id"] in plain:  # a selected text-only question: the right answer is "none"
                    neg.append(dict(row, job="crop", pages=row["pages"][:1], gate={"none": True}))
    random.Random(23).shuffle(gate)
    random.Random(29).shuffle(neg)
    gate = gate[:GATE_N] + neg[:GATE_NEG]
    out = WORK / "items.jsonl"
    out.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in items + gate))
    c = {}
    for r in items:
        c[(r["subject"], r["job"])] = c.get((r["subject"], r["job"]), 0) + 1
    print(f"{len(items)} to repair {dict(sorted(c.items()))}, {len(gate)} gate questions -> {out}")


def run(items_file):
    from PIL import Image
    items_file = Path(items_file).resolve()  # vLLM takes only absolute file:// paths under allowed_local_media_path
    pp = Path(os.environ.get("PP_ROOT", "/data/alvin/cookie/pastpapers_full"))
    out = Path(items_file).with_name(os.environ.get("PP_OUT", "results.jsonl"))
    jobs = set(os.environ.get("PP_JOBS", "crop,stem").split(","))
    done = {(r["id"], r.get("page")) for r in jl(out)}
    tmp = Path(items_file).with_name("img")
    tmp.mkdir(exist_ok=True)
    todo = []
    for r in jl(items_file):
        if r["job"] not in jobs:
            continue
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
    model = os.environ.get("PP_VLM", DEFAULT_VLM)
    llm = LLM(model=model, tensor_parallel_size=int(os.environ.get("PP_TP", "4")),
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
                f.write(json.dumps({"id": r["id"], "subject": r["subject"], "year": r["year"], "job": r["job"], "page": p, "model": model,
                                    "w": W, "h": H, "raw": o.outputs[0].text, **({"gate": r["gate"]} if "gate" in r else {}),
                                    **({"text": r["text"], "first": r.get("first")} if "text" in r else {})}, ensure_ascii=False) + "\n")
            f.flush()
            print(f"{min(i + 32, len(todo))}/{len(todo)}", flush=True)


def audit_pack(sels):
    AUDIT.mkdir(parents=True, exist_ok=True)
    if list(AUDIT.glob("results*.jsonl")):
        sys.exit(f"{AUDIT} holds results of an earlier audit: move them aside first")
    items = []
    for sel in sels:
        subject = sel.name
        for r in jl(sel / "selected.jsonl"):
            if not r.get("crops"):
                continue
            items.append({"id": r["src_id"], "pp_id": r["id"], "subject": subject, "year": r["year"], "crops": r["crops"]})
    boxes, merged = {}, {}
    for s, y in {(i["subject"], i["year"]) for i in items}:  # each year's files read once
        for q in jl(DEV_PP / s / str(y) / "questions.jsonl"):
            for f in q.get("figures") or []:
                if isinstance(f, dict) and f.get("bbox"):
                    boxes.setdefault((q["id"], f.get("page")), []).append(f["bbox"])
        merged.update({q["id"]: q for q in jl(DEV_PP / s / str(y) / "merged.jsonl")})
    out, two = [], 0
    for i in items:
        q = merged.get(i["id"]) or {}
        for c in i["crops"]:
            m = re.search(r"-p(\d+)\.png$", c)
            page = int(m.group(1)) if m else None
            bs = boxes.get((i["id"], page)) or []
            if len(bs) != 1:
                two += len(bs) > 1  # two pictures of one question on one page: one model read cannot judge both
                continue  # (none: a recrop or a crop with no recorded box)
            out.append({"id": i["id"], "pp_id": i["pp_id"], "subject": i["subject"], "year": i["year"], "qno": q.get("qno"),
                        "pages": [page], "start": (q.get("text") or "")[:120], "job": "crop",
                        "audit": {"page": page, "bbox": bs[0]}})
    (AUDIT / "items.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in out))
    c = {}
    for r in out:
        c[r["subject"]] = c.get(r["subject"], 0) + 1
    print(f"{len(out)} crops to audit {c} -> {AUDIT / 'items.jsonl'}; {two} pages with two crops of one question left out")


def audit_box_ok(b, w, h):
    """For the audit any real box counts, a full-page diagram too (box_ok's 80% cap is for cutting new crops)."""
    if not (isinstance(b, list) and len(b) == 4 and all(isinstance(x, (int, float)) for x in b)):
        return False
    x1, y1, x2, y2 = b
    return 0 <= x1 < x2 <= w * 1.02 and 0 <= y1 < y2 <= h * 1.02 and x2 - x1 >= 0.02 * w and y2 - y1 >= 0.01 * h


def audit_flags(model_box, live_box):
    """Flags for one crop against the model's box (both in page pixels; model_box None = the model saw no picture)."""
    if not model_box:
        return ["model-sees-no-picture"]
    flags = []
    if 1 - iou_cover(live_box, model_box)[1] > MISS:
        flags.append("crop-misses-part")  # part of the model's picture lies outside the crop
    if 1 - iou_cover(model_box, live_box)[1] > EXTRA:
        flags.append("crop-much-bigger")  # most of the crop lies outside the model's picture: text, options, another question
    return flags or ["agree"]


def audit_report(results, per=6):
    from PIL import Image, ImageDraw
    rows, by = jl(results), {}
    items = {(i["id"], i["pages"][0]): i for i in jl(Path(results).with_name("items.jsonl"))}  # run() does not copy audit/pp_id
    look = Path(results).with_name("look")
    look.mkdir(exist_ok=True)
    report = []
    for r in rows:
        if not page_path(r["subject"], r["year"], r["page"]).exists():
            continue
        it = items.get((r["id"], r["page"]))
        if not it:
            continue
        b = (parse(r["raw"]) or {}).get("bbox_2d")
        mb = to_page(b, r) if audit_box_ok(b, r["w"], r["h"]) else None
        k = it["audit"]["bbox"]
        if (k[2] - k[0]) * (k[3] - k[1]) <= 0:
            continue
        fl = audit_flags(mb, k)
        report.append({"id": r["id"], "pp_id": it["pp_id"], "subject": r["subject"], "year": r["year"], "page": r["page"],
                       "flags": fl, "model": mb, "crop": k})
        for f in fl:
            by.setdefault((r["subject"], f), []).append(report[-1])
    (Path(results).with_name("report.jsonl")).write_text("".join(json.dumps(x) + "\n" for x in report))
    rng = random.Random(31)
    for (s, f), xs in sorted(by.items()):
        print(f"{s:8} {f:22} {len(xs):5}")
        for x in rng.sample(xs, min(per, len(xs))):
            im = Image.open(page_path(x["subject"], x["year"], x["page"])).convert("RGB")
            d = ImageDraw.Draw(im)
            d.rectangle(x["crop"], outline=(0, 160, 0), width=10)  # green: the crop
            if x["model"]:
                d.rectangle(x["model"], outline=(220, 0, 0), width=10)  # red: the model's box
            im.thumbnail((900, 1300))
            im.save(look / f"{s}-{f}-{x['pp_id']}.jpg", quality=70)
    print(f"{len(report)} crops compared; samples in {look} (green = crop, red = model)")


def page_path(subject, year, page):
    return DEV_PP / subject / str(year) / "pages" / f"p{page:04d}.jpg"


def to_page(b, r):
    """The model's box (in the w x h frame it saw) in the dev page's pixels, or None when dev lacks the page."""
    from PIL import Image
    f = page_path(r["subject"], r["year"], r["page"])
    if not f.exists():
        return None
    with Image.open(f) as im:
        W, H = im.size
    return [round(b[0] * W / r["w"]), round(b[1] * H / r["h"]), round(b[2] * W / r["w"]), round(b[3] * H / r["h"])]


def gate_score(rows):
    """(found, positives, quiet, negatives): known boxes found (IoU and cover), and text-only pages left without a box."""
    found = pos = quiet = negs = 0
    for r in rows:
        b = (parse(r["raw"]) or {}).get("bbox_2d")
        good = box_ok(b, r["w"], r["h"])
        if r["gate"].get("none"):
            negs += 1
            quiet += not good
            continue
        k = r["gate"]["bbox"]
        if (k[2] - k[0]) * (k[3] - k[1]) <= 0 or not page_path(r["subject"], r["year"], r["page"]).exists():
            continue  # a degenerate known box, or a page dev lacks, measures nothing
        pos += 1
        pb = to_page(b, r) if good else None
        if pb:
            iou, cov = iou_cover(pb, k)
            found += iou >= IOU_MIN and cov >= COVER_MIN
    return found, pos, quiet, negs


def gate(results):
    found, pos, quiet, negs = gate_score([r for r in jl(results) if "gate" in r])
    ok = pos >= 50 and negs >= 20 and found / pos >= GATE_BAR and quiet / negs >= GATE_BAR
    print(f"gate: known boxes found {found}/{pos} ({found / max(1, pos):.1%}); text-only pages left without a box "
          f"{quiet}/{negs} ({quiet / max(1, negs):.1%}); bar {GATE_BAR:.0%} each -> {'PASSED' if ok else 'FAILED'}")
    print("note: the gate questions are ones the first cropper got right; spot-check a sample of the repaired crops before upload")
    return ok


def marks(read):
    return MARK.findall(str((read or {}).get("stem") or ""))


def apply(results, second=None, stems_only=False):
    from PIL import Image
    rows = jl(results)
    items = {r["id"]: r for r in jl(Path(results).with_name("items.jsonl"))}
    c = {"crops": 0, "no-box": 0, "not-first-page": 0, "no-dev-page": 0, "stems": 0}
    years = {(r["subject"], r["year"]) for r in items.values()}
    if not stems_only:
        for s, y in years:  # this run's crops replace every earlier run's, also where none is written now or the gate fails
            for old in (DEV_PP / s / str(y) / "recrop").glob("*.png"):
                old.unlink()
        if not gate(results):
            sys.exit("the crop gate failed: no crops written, earlier repaired crops removed (stems alone: --stems-only)")
        for r in rows:
            if "gate" in r or r["job"] != "crop":
                continue
            b = (parse(r["raw"]) or {}).get("bbox_2d")
            if not box_ok(b, r["w"], r["h"]):
                c["no-box"] += 1
                continue
            # only the question's first page: on a later page the box may be the next question's picture
            if r["page"] != min((items.get(r["id"]) or {}).get("pages") or [r["page"]]):
                c["not-first-page"] += 1
                continue
            pb = to_page(b, r)
            if not pb:
                c["no-dev-page"] += 1
                continue
            d = DEV_PP / r["subject"] / str(r["year"]) / "recrop"
            d.mkdir(exist_ok=True)
            x1, y1, x2, y2 = pb
            pad = 12  # the model's box sits tight on the lines; `figures` grows a crop still touching an edge
            with Image.open(page_path(r["subject"], r["year"], r["page"])) as im:
                im.convert("L").crop((max(0, x1 - pad), max(0, y1 - pad), min(im.width, x2 + pad), min(im.height, y2 + pad))).save(
                    d / f"{r['id']}-p{r['page']:04d}.png", optimize=True)
            c["crops"] += 1
    # stems: one model's choice of word is not enough (the underline is what the first read lost): two independent reads
    # must mark the same word(s), and the read must match the first read's sentence
    why, fixes = {}, {}
    two_rows = [r for r in jl(second) if r["job"] == "stem"] if second else []
    two = {(r["id"], r["page"]): parse(r["raw"]) for r in two_rows}
    model_of = lambda r: r.get("model") or DEFAULT_VLM  # rows from before the field was written came from the default
    if two_rows and {model_of(r) for r in two_rows} & {model_of(r) for r in rows if r["job"] == "stem"}:
        sys.exit("the second read must come from another model (PP_VLM): the same greedy model repeats its own answer")
    for r in rows:
        if r["job"] != "stem":
            continue
        st, w = check_stem(parse(r["raw"]), r["text"])
        if st and not second:
            w, st = "needs-a-second-read", None
        elif st and marks(two.get((r["id"], r["page"]))) != MARK.findall(st):
            w, st = "second-read-marks-differ", None
        if st:
            fixes.setdefault((r["subject"], r["year"]), {})[r["id"]] = (unline(st), r.get("first"))
        else:
            why[w] = why.get(w, 0) + 1
    for s, y in {k for k in years if k[0] == "chinese"}:  # this run's stems replace every earlier run's
        fx = fixes.get((s, y), {})
        f = DEV_PP / s / str(y) / "stemfix.jsonl"
        if fx or f.exists():
            f.write_text("".join(json.dumps({"id": i, "stem": st, "first": h, "src": "repair.py"}, ensure_ascii=False) + "\n"
                                 for i, (st, h) in fx.items()), encoding="utf-8")
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
    assert first_stem("他做事很认真。（1）仔细（2）马虎") == "他做事很认真。" and first_stem("他很认真。\n1. 仔细\n2. 马虎") == "他很认真。"
    assert unline("下面句子中画线的词语是什么意思？他很「认真」。") == "下面句子中「」里的词语是什么意思？他很「认真」。"
    assert unline("句中划线部分") == "句中「」里的部分"
    assert unline("下面句子中画线的词语是什么意思？工人在「规划」线路。") == "下面句子中「」里的词语是什么意思？工人在「规划」线路。"
    assert first_stem("阅读短文(1)，回答问题。他很认真。\n(1) 仔细") == "阅读短文(1)，回答问题。他很认真。"
    assert audit_flags(None, [0, 0, 10, 10]) == ["model-sees-no-picture"]
    assert audit_flags([0, 0, 10, 10], [0, 0, 10, 10]) == ["agree"]
    assert audit_flags([0, 0, 10, 20], [0, 0, 10, 10]) == ["crop-misses-part"]  # the crop has only half the picture
    assert audit_flags([0, 0, 10, 10], [0, 0, 10, 40]) == ["crop-much-bigger"]
    assert audit_box_ok([10, 10, 990, 1450], 1000, 1500) and not box_ok([10, 10, 990, 1450], 1000, 1500)
    g = lambda raw, gt, w=1000, h=1000: {"raw": raw, "gate": gt, "w": w, "h": h, "subject": "x", "year": 0, "page": 1}
    assert gate_score([g('{"none": true}', {"none": True}), g('{"bbox_2d": [10, 10, 400, 300]}', {"none": True}),
                       g('{"none": true}', {"bbox": [0, 0, 0, 5]})]) == (0, 0, 1, 2), "a degenerate known box is skipped, a box on a text-only page counts against"
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
        sec = sys.argv[sys.argv.index("--second") + 1] if "--second" in sys.argv else None
        apply(sys.argv[2], sec, "--stems-only" in sys.argv)
    elif cmd == "audit-pack":
        audit_pack([Path(s) for s in sys.argv[2:]] or SELS)
    elif cmd == "audit-report":
        audit_report(sys.argv[2])
    elif cmd == "selftest":
        selftest()
    else:
        sys.exit(__doc__)
