#!/usr/bin/env python3
"""Re-crop past-paper pictures that hold part of another question (queue 48, owner 27 Nov 2026). The Sonnet picture scan
(marks47/recrop_foreign.txt) found 41 live pictures that carry printed text of a DIFFERENT question. The vision model is
given the whole page and the question number and asked for the box of that question's own picture (Qwen2.5-VL answers
in the pixel coordinates of the image it is given, so each page is resized to a size it takes as it is). The new crop is
cut from the full page scan, padded, and saved like load_pp's figures. Nothing replaces a live figure: `apply` writes the
new crops and a before/after sheet to WORK for an eye check; `install` (after that check) backs up and replaces the
figure files of the listed ids in the selection folder, for the owner's upload. Private content: prints ids and counts.

  recrop.py pack LIST [--out SEL_DIR]      dev: LIST lines "<pp id>  <subject>" -> WORK/pack (pages + items.jsonl)
  recrop.py run                            server (GPU; PP_VLM, PP_TP): WORK/pack/items.jsonl -> WORK/pack/boxes.jsonl
  recrop.py apply [--out SEL_DIR]          dev: boxes -> WORK/new/<id>-1.webp + WORK/sheets/*.png (old | new)
  recrop.py install IDS [--out SEL_DIR]    dev: replace SEL_DIR/<subject>/figures/<id>-1.webp for IDS (backup kept)
  recrop.py selftest"""
import json
import os
import re
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

TMP = Path("/data/alvin/tmp/cookie-codex")
WORK = Path(os.environ.get("PP_RECROP", str(TMP / "recrop48")))
SERVER_WORK = "/data/alvin/cookie/" + WORK.name  # the work folder of the same name on the server
PAGE_MAX = 1568  # long side sent to the model; 56 * 28, so the model sees the page at exactly this size
PAD = 14         # pixels of the full page added around the box
SEL = {"science": TMP / "ppimport" / "sci1826g", "maths": TMP / "ppimport" / "math1826h"}  # the live selections


def sel_dir(a, subject):
    return Path(a.out) if a.out else SEL[subject]

PROMPT = ("This is a page from a Singapore PSLE {subject} exam paper. Find question {qno}. Give the bounding box of the "
          "picture, diagram, graph or table that belongs to question {qno} only: include its labels, axes and caption, and "
          "leave out the question text, the answer options and anything that belongs to another question. Reply with JSON "
          "only: {{\"bbox_2d\": [x1, y1, x2, y2]}} in pixel coordinates of this image.")
# PP_RECROP_KEEP=1 (27 Nov 2026): the box also takes in what the question needs beside its picture: a results table, lettered
# statements, or the options set out as a table (8 re-crops had lost one of these)
PROMPT_KEEP = ("This is a page from a Singapore PSLE {subject} exam paper. Find question {qno}. Give one bounding box that covers "
               "everything printed for question {qno} that a pupil needs besides its question sentence: its picture, diagram, graph "
               "or table, any results table, any lettered statements (A, B, C, D) and, if the answer options are set out as a "
               "table, that whole options table with its headings. Leave out anything that belongs to another question. Reply "
               "with JSON only: {{\"bbox_2d\": [x1, y1, x2, y2]}} in pixel coordinates of this image.")


def jl(p):
    p = Path(p)
    return [json.loads(l) for l in p.read_text().splitlines() if l.strip()] if p.exists() else []


def fit28(w, h):
    """A size Qwen2.5-VL takes as it is (multiples of 28, long side <= PAGE_MAX): then its coordinates are this image's."""
    s = min(1.0, PAGE_MAX / max(w, h))
    return max(28, round(w * s / 28) * 28), max(28, round(h * s / 28) * 28)


def parse_box(raw):
    """[x1, y1, x2, y2] from the model's text, or None."""
    m = re.search(r"\[\s*(\d+(?:\.\d+)?)\s*,\s*(\d+(?:\.\d+)?)\s*,\s*(\d+(?:\.\d+)?)\s*,\s*(\d+(?:\.\d+)?)\s*\]", raw or "")
    if not m:
        return None
    x1, y1, x2, y2 = (float(v) for v in m.groups())
    return [x1, y1, x2, y2] if x2 > x1 and y2 > y1 else None


def to_full(box, small, full, pad=PAD):
    """A box on the resized page -> the full page, padded and kept inside it."""
    sx, sy = full[0] / small[0], full[1] / small[1]
    x1, y1, x2, y2 = box
    fb = [min(full[0], max(0, int(x1 * sx) - pad)), min(full[1], max(0, int(y1 * sy) - pad)),
          min(full[0], max(0, int(x2 * sx) + pad)), min(full[1], max(0, int(y2 * sy) + pad))]
    return fb if fb[2] > fb[0] and fb[3] > fb[1] else None  # a box off the page


def needs_old_parts(row) -> str:
    """Why a re-crop may cut away something the question needs ('' when nothing): the stem refers to a table or statements
    printed beside the picture, or an option reads like a table row (its headings were only in the old picture).
    27 Nov 2026: 8 of 41 installed re-crops lost a results table, statements A-D, a picture or option-table headings."""
    stem = " ".join(row.get("stem", "").split()).lower()
    if re.search(r"\btable\b|statements?\b", stem):
        return "the question refers to a table or statements"
    for o in row.get("options", []):
        if ":" in o:  # a labelled row ("Gravitational potential energy: decreases") carries its own heading
            continue
        ws = o.split()
        if o.count("?") >= 2 or re.search(r"[A-Za-z],\s*[A-Za-z]", o) or len(ws) >= 5 and all(len(w) <= 6 for w in ws) and not o.rstrip().endswith("."):
            return "an option reads like a table row without its headings"
    return ""


def page_path(subject, crop):
    from cropcheck import page_of_crop
    pg = page_of_crop(crop)
    return (TMP / "pastpapers" / subject / pg[0] / "pages" / f"{pg[1]}.jpg") if pg else None


def pack(a):
    from PIL import Image
    (WORK / "pack" / "pages").mkdir(parents=True, exist_ok=True)
    items = []
    for line in Path(a.list).read_text().splitlines():
        if not line.strip():
            continue
        pid, subject = line.split()[:2]
        row = next((r for r in jl(sel_dir(a, subject) / subject / "selected.jsonl") if r["id"] == pid), None)
        if not row or len(row["crops"]) != 1:
            print(f"skip {pid}: not in the selection or not one picture")
            continue
        src = page_path(subject, row["crops"][0])
        if not src or not src.exists():
            print(f"skip {pid}: page not found")
            continue
        with Image.open(src) as im:
            full = im.size
            small = fit28(*full)
            im.convert("RGB").resize(small, Image.LANCZOS).save(WORK / "pack" / "pages" / f"{pid}.jpg", quality=90)
        items.append({"id": pid, "subject": subject, "qno": row["qno"], "page": f"pages/{pid}.jpg", "small": small,
                      "full": full, "src": str(src)})
    (WORK / "pack" / "items.jsonl").write_text("".join(json.dumps(x) + "\n" for x in items))
    print(f"packed {len(items)} -> {WORK / 'pack'}")


def run(a):
    from vllm import LLM, SamplingParams
    model = os.environ.get("PP_VLM", "Qwen/Qwen2.5-VL-72B-Instruct-AWQ")
    if "Qwen2.5-VL" not in model:  # its boxes are pixels of the image given; other models use other scales
        sys.exit(f"recrop needs a Qwen2.5-VL model, not {model}")
    P = Path(SERVER_WORK) / "pack"
    items = jl(P / "items.jsonl")
    llm = LLM(model=model, tensor_parallel_size=int(os.environ.get("PP_TP", "4")),
              gpu_memory_utilization=0.92, max_model_len=8192, max_num_seqs=8, limit_mm_per_prompt={"image": 1},
              mm_processor_kwargs={"max_pixels": PAGE_MAX * PAGE_MAX}, allowed_local_media_path=str(P),
              enforce_eager=bool(os.environ.get("PP_EAGER")))
    sp = SamplingParams(temperature=0, max_tokens=120)
    msgs = [[{"role": "user", "content": [{"type": "image_url", "image_url": {"url": f"file://{P / it['page']}"}},
                                          {"type": "text", "text": (PROMPT_KEEP if os.environ.get("PP_RECROP_KEEP") else PROMPT).format(subject=it["subject"].capitalize(), qno=it["qno"])}]}]
            for it in items]
    outs = llm.chat(msgs, sp, use_tqdm=False)
    with open(P / "boxes.jsonl", "w") as f:
        for it, o in zip(items, outs):
            f.write(json.dumps({"id": it["id"], "raw": o.outputs[0].text}) + "\n")
    print(f"{len(items)} boxes -> {P / 'boxes.jsonl'}")


def apply(a):
    from PIL import Image
    from load_pp import compress
    items = {x["id"]: x for x in jl(WORK / "pack" / "items.jsonl")}
    (WORK / "new").mkdir(parents=True, exist_ok=True)
    (WORK / "sheets").mkdir(parents=True, exist_ok=True)
    ok, bad = 0, []
    for b in jl(WORK / "pack" / "boxes.jsonl"):
        it = items[b["id"]]
        box = parse_box(b["raw"])
        if not box:
            bad.append(b["id"])
            continue
        fb = to_full(box, it["small"], it["full"])
        if not fb:
            bad.append(b["id"])
            continue
        tmp = WORK / "new" / f"{b['id']}-1.png"
        with Image.open(it["src"]) as im:
            im.crop(fb).save(tmp)
        compress(tmp, WORK / "new" / f"{b['id']}-1.webp", 900, 60 * 1024)
        tmp.unlink()
        old = WORK / "backup" / f"{b['id']}-1.webp"  # install keeps the original here; else the live file is the original
        old = old if old.exists() else sel_dir(a, it["subject"]) / it["subject"] / "figures" / f"{b['id']}-1.webp"
        with Image.open(old) as o, Image.open(WORK / "new" / f"{b['id']}-1.webp") as n:
            h = max(o.height, n.height)
            sheet = Image.new("RGB", (o.width + n.width + 30, h + 30), "white")
            sheet.paste(o.convert("RGB"), (0, 30))
            sheet.paste(n.convert("RGB"), (o.width + 30, 30))
            sheet.save(WORK / "sheets" / f"{b['id']}.png")
        ok += 1
    print(f"{ok} new crops -> {WORK / 'new'}; before/after sheets -> {WORK / 'sheets'}; no box: {bad}")


def install(a):
    ids = [l.split()[0] for l in Path(a.ids).read_text().splitlines() if l.strip()]
    items = {x["id"]: x for x in jl(WORK / "pack" / "items.jsonl")}
    # a question that may need what the old picture held is refused unless a person has looked (--checked FILE of ids)
    checked = {l.split()[0] for l in Path(a.checked).read_text().splitlines() if l.strip()} if a.checked else set()
    rows = {r["id"]: r for s in {items[p]["subject"] for p in ids} for r in jl(sel_dir(a, s) / s / "selected.jsonl")}
    risky = {p: needs_old_parts(rows[p]) for p in ids if needs_old_parts(rows[p]) and p not in checked}
    if risky:
        sys.exit("refused (look at each, then list the good ones in --checked): "
                 + "; ".join(f"{p}: {w}" for p, w in sorted(risky.items())))
    missing = [p for p in ids if p not in items or not (WORK / "new" / f"{p}-1.webp").exists()]
    if missing:  # checked before any file is touched, so a stop never leaves files and figures.jsonl out of step
        sys.exit(f"no new crop for {missing}: nothing installed")
    bak = WORK / "backup"
    bak.mkdir(parents=True, exist_ok=True)
    from PIL import Image
    meta = {}  # figures.jsonl carries each picture's w, h and bytes (the site sizes the picture from them): update them too
    for pid in ids:
        subj = items[pid]["subject"]
        dst = sel_dir(a, subj) / subj / "figures" / f"{pid}-1.webp"
        if not (bak / dst.name).exists():
            shutil.copy2(dst, bak / dst.name)
        shutil.copy2(WORK / "new" / f"{pid}-1.webp", dst)
        with Image.open(dst) as im:
            meta[f"{subj}/{pid}-1.webp"] = (subj, im.width, im.height, dst.stat().st_size)
    for subj in {m[0] for m in meta.values()}:
        fj = sel_dir(a, subj) / subj / "figures.jsonl"
        if not (bak / f"figures.{subj}.jsonl").exists():
            shutil.copy2(fj, bak / f"figures.{subj}.jsonl")
        rows = jl(fj)
        for r in rows:
            if r["path"] in meta:
                _, r["w"], r["h"], r["bytes"] = meta[r["path"]]
        fj.write_text("".join(json.dumps(r) + "\n" for r in rows))
    hit = sum(1 for subj in {m[0] for m in meta.values()} for r in jl(sel_dir(a, subj) / subj / "figures.jsonl") if r["path"] in meta)
    print(f"installed {len(ids)} crops, {hit} figures.jsonl entries updated (old files in {bak})")


def selftest():
    assert fit28(2480, 3508) == (1120, 1568) and fit28(500, 400) == (504, 392)
    assert parse_box('```json\n{"bbox_2d": [10, 20, 300, 400]}\n```') == [10.0, 20.0, 300.0, 400.0]
    assert parse_box('{"bbox_2d": [300, 20, 10, 400]}') is None and parse_box("no box") is None
    assert to_full([100, 100, 200, 200], (1000, 1000), (2000, 2000), pad=10) == [190, 190, 410, 410]
    assert to_full([0, 0, 1000, 1000], (1000, 1000), (2000, 2000), pad=10) == [0, 0, 2000, 2000]
    assert to_full([1200, 100, 1300, 300], (1120, 1568), (2480, 3508)) is None  # off the page
    assert not needs_old_parts({"stem": "Which is true?", "options": ["It has no leaves.", "1,200 g", "It has roots", "x"]})
    assert needs_old_parts({"stem": "He recorded the results in the table below. Which surface?", "options": ["A", "B"]})
    assert needs_old_parts({"stem": "Which is correct?", "options": ["closed closed yes no yes yes", "x", "y", "z"]})
    assert needs_old_parts({"stem": "What colour?", "options": ["remained green, turned blue", "a", "b", "c"]})
    assert not needs_old_parts({"stem": "Which energy?", "options": ["Gravitational potential energy: decreases; Kinetic: increases", "240°", "Point P", "Shark"]})
    print("recrop selftest ok")


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("cmd", choices=["pack", "run", "apply", "install", "selftest"])
    p.add_argument("list", nargs="?")
    p.add_argument("--checked", default=None)  # install: ids a person has looked at (allowed though needs_old_parts flags them)
    p.add_argument("--out", default=None)  # else the live selection of each subject (SEL)
    a = p.parse_args()
    a.ids = a.list
    {"pack": pack, "run": run, "apply": apply, "install": install, "selftest": lambda a: selftest()}[a.cmd](a)
