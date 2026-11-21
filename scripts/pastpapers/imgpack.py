"""Answer-free PDF packs of past-paper question sets WITH their page scans, for outside models that read PDFs (owner, 21 Nov
2026: Gemini and Perplexity agreeing were right 32/32 on keyed visual-text questions in the pilot). Private content stays
under /data/alvin/tmp; the owner uploads the PDFs himself.

  imgpack.py build --kind english-visual [--per 15] [--skip SETS.json]
      Sets: English visual-text MCQs (paper questions 21-30, tagger eng-visual-text or section "Visual Text"), 5+ keyed
      questions with pages. Each set: the two pages before its first question page through its last, then its questions
      numbered Q1.. within the PDF, each with its paper number. Writes OUT/<kind>/part<N>.pdf + part<N>.qmap.json.
  imgpack.py score --kind english-visual [--models gemini,perplexity]
      Reads OUT/<kind>/part<N>_<model>.txt ("Q12: 3" lines). Calibration = questions whose key and blind solver agree;
      prints each model's score, the agreement precision, and the verdicts on the disputed questions.
  imgpack.py selftest
Prints ids and counts only."""
import argparse, collections, html, json, re, subprocess, sys
from pathlib import Path

TMP = Path("/data/alvin/tmp/cookie-codex")
PP, BLIND, OUT = TMP / "pastpapers", TMP / "audit" / "blindcheck", TMP / "blind3" / "imgpack"
HEAD = ("You are an expert Singapore primary-school English teacher marking PSLE English Paper 2. Each SET below shows the exam "
        "page images (the poster, notice or advertisement, which may run over two pages, and the questions), followed by its "
        "numbered questions. Use the page images to answer. Each question shows its number on the exam page in brackets "
        "(paper question 21 = the page's question 21). For each question choose the single best option (1-4). Reply ONLY with "
        "one line per question: Q&lt;number&gt;: &lt;option number&gt;, for example Q1: 3. Answer every question.")
ANS = re.compile(r"Q\s*(\d{1,3})\s*[:：.)\-]\s*\(?([1-4])\)?")


def jl(p):
    p = Path(p)
    return [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()] if p.exists() else []


def english_visual_sets(skip):
    sets = []
    for y in range(2018, 2027):
        base = PP / "english" / str(y)
        tags = {t["id"]: t.get("st") for t in jl(base / "tags72.jsonl")}
        bl = {b["id"]: b for b in jl(BLIND / f"english-{y}.jsonl")}
        by = collections.defaultdict(list)
        for q in jl(base / "merged.jsonl"):
            if q.get("format") != "mcq" or not isinstance(q.get("qno"), int) or not 21 <= q["qno"] <= 30:
                continue
            if len(q.get("options") or []) != 4 or not (bl.get(q["id"]) or {}).get("key") or not q.get("pages"):
                continue
            if tags.get(q["id"]) != "eng-visual-text" and q.get("section") != "Visual Text":
                continue
            by[(q["paper"], q.get("part"))].append(q)
        for (paper, part), L in sorted(by.items(), key=lambda kv: str(kv[0])):
            ids = [q["id"] for q in sorted(L, key=lambda q: q["qno"])]
            if len(ids) >= 5 and not set(ids) & skip:
                sets.append({"year": y, "ids": ids, "q": {q["id"]: q for q in L}})
    return sets


def page_range(qs):
    pages = sorted({p for q in qs for p in q["pages"]})
    return list(range(max(1, pages[0] - 2), pages[-1] + 1))


def build(a):
    from PIL import Image
    skip = set()
    if a.skip:
        for s in json.load(open(a.skip)):
            skip |= set(s[2] if isinstance(s, list) else s)
    sets = english_visual_sets(skip)
    out = OUT / a.kind
    (out / "img").mkdir(parents=True, exist_ok=True)
    for part, i in enumerate(range(0, len(sets), a.per), 1):
        chunk, qmap, n, body = sets[i:i + a.per], {}, 0, []
        for si, s in enumerate(chunk, 1):
            qs = [s["q"][x] for x in s["ids"]]
            imgs = []
            for p in page_range(qs):
                src = PP / "english" / str(s["year"]) / "pages" / f"p{p:04d}.jpg"
                if not src.exists():
                    continue
                dst = out / "img" / f"{s['year']}-p{p:04d}.jpg"
                if not dst.exists():
                    im = Image.open(src).convert("L")
                    im.thumbnail((1300, 1840))
                    im.save(dst, quality=70)
                imgs.append(dst.name)
            items = []
            for q in qs:
                n += 1
                qmap[n] = q["id"]
                opts = "".join(f"<div>({j}) {html.escape(o)}</div>" for j, o in enumerate(q["options"], 1))
                items.append(f'<div class="q"><b>Q{n}.</b> <i>(paper question {q["qno"]})</i> {html.escape(q["text"])}{opts}</div>')
            body.append(f"<section><h2>SET {si} (questions Q{n - len(qs) + 1}-Q{n})</h2>"
                        + "".join(f'<img src="img/{x}">' for x in imgs) + f"<h3>Questions for SET {si}</h3>" + "".join(items) + "</section>")
        page = ('<!doctype html><html><head><meta charset="utf-8"><title>Visual Text Pack</title><style>'
                "body{font:14px/1.4 Arial,sans-serif;margin:24px} section{page-break-before:always} h3{page-break-before:avoid}"
                "img{display:block;max-width:100%;max-height:24.5cm;margin:0 auto 4px;border:1px solid #ccc;page-break-after:always}"
                ".q{margin:10px 0;page-break-inside:avoid} h2{font-size:18px}</style></head><body>"
                f"<p>{HEAD}</p>{''.join(body)}</body></html>")
        hp = out / f"part{part}.html"
        hp.write_text(page, encoding="utf-8")
        json.dump(qmap, open(out / f"part{part}.qmap.json", "w"))
        subprocess.run(["google-chrome", "--headless", "--no-sandbox", "--disable-gpu", "--no-pdf-header-footer",
                        f"--print-to-pdf={out / f'part{part}.pdf'}", f"file://{hp}"], check=True, capture_output=True, timeout=300)
        mb = (out / f"part{part}.pdf").stat().st_size / 1e6
        print(f"part{part}.pdf: {len(chunk)} sets, {n} questions, {mb:.1f} MB")
    print(f"{len(sets)} sets -> {out}")


def score(a):
    out = OUT / a.kind
    bl = {}
    for y in range(2018, 2027):
        for r in jl(BLIND / f"english-{y}.jsonl"):
            bl[r["id"]] = r
    models = a.models.split(",")
    M = {m: {} for m in models}
    ids = []
    for qf in sorted(out.glob("part*.qmap.json")):
        part = qf.name.split(".")[0]
        qmap = {int(k): v for k, v in json.load(open(qf)).items()}
        ids += qmap.values()
        for m in models:
            f = out / f"{part}_{m}.txt"
            if f.exists():
                got = {}
                for mm in ANS.finditer(f.read_text(encoding="utf-8", errors="replace")):
                    got.setdefault(int(mm.group(1)), mm.group(2))
                M[m].update({qmap[k]: v for k, v in got.items() if k in qmap})
    cal = [i for i in ids if bl[i].get("agree") is True]
    for m in models:
        c = [i for i in cal if i in M[m]]
        print(f"{m}: {len(M[m])} answers; calibration {sum(M[m][i] == str(bl[i]['key']) for i in c)}/{len(c)}")
    def vote(i):
        v = [M[m].get(i) for m in models]
        return v[0] if None not in v and len(set(v)) == 1 else None
    cu = [i for i in cal if vote(i)]
    ok = sum(vote(i) == str(bl[i]["key"]) for i in cu)
    print(f"agreement on calibration: {len(cu)}/{len(cal)}, precision {ok}/{len(cu)} = {100 * ok / max(1, len(cu)):.1f}%")
    C = collections.Counter()
    for i in ids:
        if bl[i].get("agree") is True:
            continue
        u = vote(i)
        C["key stands" if u == str(bl[i]["key"]) else "replace (models + local)" if u and u == str(bl[i].get("pick")) else "other" if u else "split"] += 1
    print("disputed:", dict(C))


def selftest():
    qs = [{"pages": [12, 13]}, {"pages": [13]}]
    assert page_range(qs) == [10, 11, 12, 13] and page_range([{"pages": [1]}]) == [1]
    assert ANS.findall("Q1: 3\nQ2：4\nQ10) 2") == [("1", "3"), ("2", "4"), ("10", "2")]
    print("imgpack selftest ok")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("cmd", choices=("build", "score", "selftest"))
    p.add_argument("--kind", default="english-visual")
    p.add_argument("--per", type=int, default=15)
    p.add_argument("--skip", default=str(TMP / "blind3" / "english" / "vt_pilot_sets.json"))
    p.add_argument("--models", default="gemini,perplexity")
    a = p.parse_args()
    {"build": build, "score": score, "selftest": lambda _a: selftest()}[a.cmd](a)
