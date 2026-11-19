#!/usr/bin/env python3
"""Step B packets: one small folder per paper so a cheap agent reads ~3 images and one text file, not 30 crops,
full pages and the 600 KB pattern files.

  python3 scripts/pastpapers/packet.py build --subject science --year 2026      # -> STEPB/science-2026/<paper>/
  python3 scripts/pastpapers/packet.py merge --subject science --year 2026      # validate out/*.json -> stepB.jsonl
  python3 scripts/pastpapers/packet.py selftest

A packet holds q.txt (questions, compact), fig*.jpg (crops tiled with F-labels), key*.jpg (answer pages, small),
pg-NNNN.jpg (pages around question-number gaps or unreadable questions, small). Shared per subject: tax-<subject>.txt
(sub-topic ids and pattern ids, one line each). Everything is written outside the repo (past-paper content)."""
import argparse, json, re, sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
PP = Path("/data/alvin/tmp/cookie-codex/pastpapers")
STEPB = PP / "stepB"
SYL = {"maths": "math", "science": "science", "english": "english", "chinese": "chinese"}
TILE, COLS, PER_SHEET = (420, 300), 3, 12
MAX_KEY, MAX_PG, TEXT_CAP = 4, 6, 420


def taxonomy(subject):
    """-> (text, subtopic ids, pattern ids)."""
    s = SYL[subject]
    syl = json.loads((ROOT / f"site/src/data/syllabus/{s}.json").read_text())
    pat = json.loads((ROOT / f"scripts/quiz/{s}/patterns.json").read_text())["patterns"]
    out, subs, pats = [f"# {subject}: sub-topic ids (pick one per question)"], set(), set()
    for st in syl["strands"]:
        for t in st["topics"]:
            for sb in t.get("subtopics", []):
                subs.add(sb["id"]); out.append(f"{sb['id']}  {sb['name']}  [{t['name']}]")
    out.append(f"\n# {subject}: question-type pattern ids (pick one or null)")
    for p in pat:
        pats.add(p["id"])
        label = p.get("name") or f"{p.get('topic', '')}: {p.get('structure', '')}"
        out.append(f"{p['id']}  {label[:110]}")
    return "\n".join(out) + "\n", subs, pats


def small(src, dst, width):
    im = Image.open(src).convert("L")
    if im.width > width: im = im.resize((width, round(im.height * width / im.width)))
    im.save(dst, quality=70)


def sheets(crops, folder):
    """Tile crops 3 across, 12 per sheet, each labelled F1, F2... -> [(label, crop path)]."""
    font = ImageFont.load_default(size=28)
    labels = []
    for start in range(0, len(crops), PER_SHEET):
        chunk = crops[start:start + PER_SHEET]
        rows = (len(chunk) + COLS - 1) // COLS
        sheet = Image.new("L", (COLS * TILE[0], rows * TILE[1]), 255)
        d = ImageDraw.Draw(sheet)
        for i, c in enumerate(chunk):
            im = Image.open(c).convert("L")
            im.thumbnail((TILE[0] - 10, TILE[1] - 40))
            x, y = (i % COLS) * TILE[0], (i // COLS) * TILE[1]
            sheet.paste(im, (x + 5, y + 36))
            lab = f"F{start + i + 1}"
            d.rectangle([x, y, x + TILE[0] - 1, y + TILE[1] - 1], outline=0)
            d.text((x + 6, y + 2), lab, fill=0, font=font)
            labels.append((lab, c))
        sheet.save(folder / f"fig{start // PER_SHEET + 1}.jpg", quality=70)
    return labels


def build(subject, year):
    base = PP / subject / str(year)
    tax, _, _ = taxonomy(subject)
    STEPB.mkdir(parents=True, exist_ok=True)
    (STEPB / f"tax-{subject}.txt").write_text(tax)
    papers = [json.loads(l) for l in open(base / "papers.jsonl")]
    qs = [json.loads(l) for l in open(base / "questions.jsonl")]
    made = []
    for p in papers:
        pid = p.get("paper_id") or p.get("id")
        pq = [q for q in qs if q["paper"] == pid]
        folder = STEPB / f"{subject}-{year}" / pid
        folder.mkdir(parents=True, exist_ok=True)
        for old in folder.glob("*.jpg"): old.unlink()
        crops = [f["crop"] for q in pq for f in (q.get("figures") or [])]
        lab = dict((c, l) for l, c in sheets([c for c in crops if Path(c).exists()], folder))
        keys = (p.get("answer_pages") or [])[:MAX_KEY]
        for n in [n for n in keys if (base / "pages" / f"p{n:04d}.jpg").exists()]: small(base / "pages" / f"p{n:04d}.jpg", folder / f"key-{n:04d}.jpg", 1000)
        need = sorted({pg for q in pq if any(f.startswith(("qno_gap", "no_text")) for f in q.get("flags", []))
                       for pg in q["pages"][-1:]})[:MAX_PG]
        for n in [n for n in need if (base / "pages" / f"p{n:04d}.jpg").exists()]: small(base / "pages" / f"p{n:04d}.jpg", folder / f"pg-{n:04d}.jpg", 1100)
        head = {k: p.get(k) for k in ("school", "exam", "part", "first_page", "last_page", "printed_total", "marks_sum")
                if p.get(k) is not None}
        lines = [f"PAPER {pid} {json.dumps(head, ensure_ascii=False)}",
                 f"answer-key pages: {p.get('answer_pages') or []} (small copies: key-*.jpg)", ""]
        for q in pq:
            figs = [lab[f["crop"]] for f in (q.get("figures") or []) if f["crop"] in lab]
            text = re.sub(r"\s+", " ", q.get("text") or "").strip()
            text = text[:TEXT_CAP] + (" ..." if len(text) > TEXT_CAP else "")
            meta = [f"q{q['qno']}", q.get("section") or "", q.get("format") or "",
                    f"marks={q.get('marks')}({(q.get('marks_source') or '?')[:24]})", f"p{','.join(map(str, q['pages']))}"]
            if q.get("passage"): meta.append(f"passage={q['passage']}")
            if q.get("flags"): meta.append("flags=" + ",".join(q["flags"]))
            if figs: meta.append("figs=" + ",".join(figs))
            lines += [f"## {q['id']} | " + " | ".join(m for m in meta if m), text, ""]
        (folder / "q.txt").write_text("\n".join(lines))
        made.append((pid, len(pq), len(lab), len(keys), len(need)))
    (STEPB / f"{subject}-{year}" / "out").mkdir(exist_ok=True)
    for m in made: print(*m)
    print(f"{subject} {year}: {len(made)} packets")


def check_out(out, qids, subs, pats):
    """-> list of problems in one agent output."""
    bad = []
    q = out.get("questions")
    if not isinstance(q, dict): return ["no questions object"]
    miss = [i for i in qids if i not in q]
    if miss: bad.append(f"{len(miss)} questions missing, e.g. {miss[:3]}")
    for i, r in q.items():
        if i not in qids: bad.append(f"unknown id {i}"); continue
        if not isinstance(r, dict): bad.append(f"{i}: not an object"); continue
        if r.get("st") not in subs: bad.append(f"{i}: bad sub-topic {r.get('st')!r}")
        if r.get("pat") is not None and r.get("pat") not in pats: bad.append(f"{i}: bad pattern {r.get('pat')!r}")
        if not isinstance(r.get("marks"), (int, float)) or r["marks"] <= 0: bad.append(f"{i}: marks {r.get('marks')!r}")
    added = out.get("added") or []
    if not isinstance(added, list) or not all(isinstance(a, dict) for a in added): return bad + ["added is not a list of objects"]
    for a in added:
        if a.get("st") not in subs: bad.append(f"added q{a.get('qno')}: bad sub-topic {a.get('st')!r}")
    return bad


def merge(subject, year):
    base, d = PP / subject / str(year), STEPB / f"{subject}-{year}"
    _, subs, pats = taxonomy(subject)
    qs = [json.loads(l) for l in open(base / "questions.jsonl")]
    by = {}
    for q in qs: by.setdefault(q["paper"], []).append(q)
    done = bad_papers = 0
    with open(d / f"{subject}-{year}-stepB.jsonl", "w") as f:
        for pid, pq in by.items():
            # every question is written; a paper whose output is missing, unreadable or invalid gets stepB=null and a
            # stepB_problems list, so nothing vanishes and nothing bad passes as a tag
            o = d / "out" / f"{pid}.json"
            try: out = json.loads(o.read_text()) if o.exists() else None
            except json.JSONDecodeError: out = {}
            probs = ["no output"] if out is None else check_out(out, {q["id"] for q in pq}, subs, pats) if isinstance(out, dict) else ["not an object"]
            if probs: bad_papers += 1; print(f"{pid}: " + "; ".join(probs[:5]))
            for q in pq:
                r = None if probs else out["questions"][q["id"]]
                f.write(json.dumps({**q, "stepB": r, **({"stepB_problems": probs} if probs else {})}, ensure_ascii=False) + "\n")
            for a in ([] if probs else out.get("added") or []):
                f.write(json.dumps({"paper": pid, "added": True, **a}, ensure_ascii=False) + "\n")
            done += not probs
    print(f"{subject} {year}: {done}/{len(by)} papers merged cleanly, {bad_papers} written with stepB=null")


def selftest():
    subs, pats = {"s1"}, {"p1"}
    good = {"questions": {"a": {"st": "s1", "pat": None, "marks": 2}}, "added": []}
    assert check_out(good, {"a"}, subs, pats) == []
    assert check_out({"questions": {}}, {"a"}, subs, pats)[0].startswith("1 questions missing")
    assert any("bad pattern" in b for b in check_out({"questions": {"a": {"st": "s1", "pat": "x", "marks": 1}}}, {"a"}, subs, pats))
    assert any("marks" in b for b in check_out({"questions": {"a": {"st": "s1", "pat": None, "marks": 0}}}, {"a"}, subs, pats))
    assert check_out({"questions": {"a": None}, "added": None}, {"a"}, subs, pats) == ["a: not an object"]
    assert check_out({"questions": {"a": {"st": "s1", "marks": 1}}, "added": [None]}, {"a"}, subs, pats) == ["added is not a list of objects"]
    t, s, p = taxonomy("science")
    assert len(s) > 20 and len(p) > 20 and "sci-pat-" in t
    print("packet selftest ok")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["build", "merge", "selftest"])
    ap.add_argument("--subject", choices=list(SYL))
    ap.add_argument("--year", type=int)
    a = ap.parse_args()
    if a.cmd == "selftest": selftest(); sys.exit()
    (build if a.cmd == "build" else merge)(a.subject, a.year)
