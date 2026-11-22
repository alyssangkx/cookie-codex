"""Answer-free PDF packs of past-paper question sets WITH their page scans, for outside models that read PDFs (owner, 21 Nov
2026: Gemini and Perplexity agreeing were right 32/32 on keyed visual-text questions in the pilot). Private content stays
under /data/alvin/tmp; the owner uploads the PDFs himself.

  imgpack.py build --kind english-visual [--per 15] [--skip SETS.json]
      Sets: English visual-text MCQs (paper questions 21-30, tagger eng-visual-text or section "Visual Text"), 5+ keyed
      questions with pages. Each set: the two pages before its first question page through its last, then its questions
      numbered Q1.. within the PDF, each with its paper number. Writes OUT/<kind>/part<N>.pdf + part<N>.qmap.json.
  imgpack.py build --kind chinese-cloze|chinese-reading [--per 15]
      Chinese passage sections (短文填空 questions 16-20, 阅读理解一 21-25) holding a key the blind solver disputes (owner,
      21 Nov 2026: "do the outside-model packs for the disagreements"); the set's keyed questions that agree calibrate.
  imgpack.py score --kind KIND [--models gemini,perplexity] [--write]
      --write: the unanimous verdicts on disputed questions into audit/blindcheck/consensus/<subject>-<year>.jsonl
      (models = key: confirm; models = the blind solver's pick: replace; anything else is not written), merged with the
      verdicts already there, for load_pp select. Only after the owner has seen the calibration.
      Reads OUT/<kind>/part<N>_<model>.txt ("Q12: 3" lines). Calibration = questions whose key and blind solver agree;
      prints each model's score, the agreement precision, and the verdicts on the disputed questions.
  imgpack.py selftest
Prints ids and counts only."""
import argparse, collections, html, json, re, subprocess, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import load_pp as L  # noqa: E402

TMP = Path("/data/alvin/tmp/cookie-codex")
PP, BLIND, OUT = TMP / "pastpapers", TMP / "audit" / "blindcheck", TMP / "blind3" / "imgpack"
HEAD = ("You are an expert Singapore primary-school English teacher marking PSLE English Paper 2. Each SET below shows the exam "
        "page images (the poster, notice or advertisement, which may run over two pages, and the questions), followed by its "
        "numbered questions. Use the page images to answer. Each question shows its number on the exam page in brackets "
        "(paper question 21 = the page's question 21). For each question choose the single best option (1-4). Reply ONLY with "
        "one line per question: Q&lt;number&gt;: &lt;option number&gt;, for example Q1: 3. Answer every question.")
HEAD_ZH = ("你是新加坡小学华文老师，正在批改小六会考（PSLE）华文试卷。下面每一组（SET）先给出试卷的页面图片（短文和题目），"
           "然后列出这一组的题目。请根据页面图片中的短文作答。每题括号里的“paper question”是试卷上的题号。每题选出最恰当的答案（1-4）。"
           "只用一行回答一题，格式为 Q&lt;题号&gt;: &lt;选项号&gt;，例如 Q1: 3。每一题都要回答。\n"
           "You are an expert Singapore primary-school Chinese teacher marking PSLE Chinese. Each SET shows the exam page images "
           "(the passage and its questions), then its numbered questions. Use the passage in the page images. For each question "
           "choose the single best option (1-4). Reply ONLY with one line per question: Q&lt;number&gt;: &lt;option number&gt;.")
HEAD_SG = ("You are an expert Singapore primary-school {subj} teacher marking PSLE {subj} multiple-choice questions. Below are "
           "numbered questions, each with its options and, where the question refers to one, the picture printed with it. For "
           "each question choose the single best option (1-4). Reply ONLY with one line per question: Q&lt;number&gt;: &lt;option "
           "number&gt;, for example Q1: 3. Answer every question.")
HEAD_DLG = ("你是新加坡小学华文老师，正在批改小六会考（PSLE）华文试卷的“完成对话”。每一组（SET）先给出试卷的页面图片（一个有8个短语或短句的表格，"
            "和一段有空格的对话），然后列出这组对话的空格。请根据上下文，为每个空格从表中选出最恰当的短语或短句（1-8），每个短语只用一次。"
            "只用一行回答一题，格式为 Q&lt;题号&gt;: &lt;选项号&gt;，例如 Q1: 7。每一题都要回答。\n"
            "You are an expert Singapore primary-school Chinese teacher. Each SET shows the exam page images (a table of 8 phrases "
            "and a dialogue with numbered blanks), then lists the blanks. For each blank choose the phrase (1-8) that fits; each "
            "phrase is used once. Reply ONLY with one line per question: Q&lt;number&gt;: &lt;option number 1-8&gt;.")
SINGLE = {"science-single": "Science", "maths-single": "Mathematics"}  # one question per item: key disputes (owner, 21 Nov 2026)
KINDS = {  # kind: (subject, questions, tagger sub-topic, section, minimum keyed questions in a set, sets need a disputed key)
    "english-visual": ("english", (21, 30), "eng-visual-text", "Visual Text", 5, False),
    "chinese-cloze": ("chinese", (16, 20), "chi-cloze-mcq", "短文填空", 1, True),
    "chinese-reading": ("chinese", (21, 25), "chi-yuedu-mcq-text", "阅读理解一", 1, True),
    "chinese-dialogue": ("chinese", (26, 29), "chi-dialogue-mcq", "完成对话", 4, False),
    "science-single": ("science", (1, 99), None, None, 1, True),
    "maths-single": ("maths", (1, 99), None, None, 1, True),
}
CALIB = 200  # agreeing keys mixed into a single-question pack to measure the models
# the latest selection's holds: a disputed question goes in only when the dispute is all that holds it back
HOLDS = {"science": TMP / "ppimport" / "sci1826b" / "science" / "rejects.jsonl",
         "maths": TMP / "ppimport" / "math1826" / "maths" / "rejects.jsonl"}
DIALOGUE = TMP / "ppimport" / "chidialogue" / "chinese" / "candidates.jsonl"  # load_pp select --passage chinese-dialogue
ANS8 = re.compile(r"Q\s*(\d{1,3})\s*[:：.)\-]\s*\(?([1-8])\)?")  # 完成对话: 8 phrases
ANS = re.compile(r"Q\s*(\d{1,3})\s*[:：.)\-]\s*\(?([1-4])\)?")


def jl(p):
    p = Path(p)
    return [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()] if p.exists() else []


def qnum(q):
    return int(q["qno"]) if str(q.get("qno") or "").isdigit() else None  # Chinese papers store "17"


def single_sets(kind):
    """Science/Maths key disputes as one-question items: every 4-option keyed MCQ whose key the blind solver disputes, plus
    CALIB agreeing ones, shuffled. A question that refers to a picture shows its whole exam page(s) (owner, 22 Nov 2026:
    Gemini scored 77% / 66% on picture questions shown as crops, 95% / 90% on text-only ones); others are text only."""
    import random
    subject = KINDS[kind][0]
    only = {r["id"] for r in jl(HOLDS[subject]) if r.get("reason") == "blind-disagree"}
    dis, agree = [], []
    for y in range(2018, 2027):
        base = PP / subject / str(y)
        bl = {b["id"]: b for b in jl(BLIND / f"{subject}-{y}.jsonl")}
        for q in jl(base / "merged.jsonl"):
            b = bl.get(q["id"]) or {}
            if q.get("format") != "mcq" or len(q.get("options") or []) != 4 or not b.get("key") or not q.get("pages"):
                continue
            text = L.tex_to_text(q.get("text") or "")
            if L.garbled(text, L.strip_opts(q["options"])):  # statements read as options and the like: no key can make it shippable
                continue
            # as load_pp select: options like "A and C only" point at the picture too
            refers = bool(L.FIG_WORDS.search(text) or L.FIG_LETTER.search(text) or L.realfig(q)
                          or any(L.FIG_LETTER.search(L.strip_num(o)) for o in q["options"]))
            pages = sorted(q["pages"])[:2] if refers else []  # the question's own page(s), at most two
            if refers and not all((base / "pages" / f"p{p:04d}.jpg").exists() for p in pages):
                continue
            item = {"year": y, "ids": [q["id"]], "q": {q["id"]: q}, "pages": pages}
            if b.get("agree") is False and b.get("pick") and q["id"] in only:
                dis.append(item)
            elif b.get("agree") is True:
                agree.append(item)
    rng = random.Random(21)
    items = dis + rng.sample(agree, min(CALIB, len(agree)))
    rng.shuffle(items)
    return items


def dialogue_sets():
    """完成对话 candidate sets (load_pp select --passage chinese-dialogue): each blank asks which of the 8 phrases fills it."""
    sets = []
    for c in jl(DIALOGUE):
        qs = {}
        for b in c["blanks"]:
            qs[b["id"]] = {"id": b["id"], "qno": b["qno"], "pages": b["pages"], "options": c["phrases"], "key": b["key"],
                           "text": f"对话中的（{b['qno']}）应填入哪一个短语或短句？ Which phrase fills blank ({b['qno']}) of the dialogue?"}
        sets.append({"year": c["year"], "ids": [b["id"] for b in c["blanks"]], "q": qs})
    return sets


def kind_sets(kind, skip):
    if kind in SINGLE:
        return single_sets(kind)
    if kind == "chinese-dialogue":
        return dialogue_sets()
    subject, (lo, hi), st, section, least, disputed = KINDS[kind]
    sets = []
    for y in range(2018, 2027):
        base = PP / subject / str(y)
        tags = {t["id"]: t.get("st") for t in jl(base / "tags72.jsonl")}
        bl = {b["id"]: b for b in jl(BLIND / f"{subject}-{y}.jsonl")}
        by = collections.defaultdict(list)
        for q in jl(base / "merged.jsonl"):
            n = qnum(q)
            if q.get("format") != "mcq" or not n or not lo <= n <= hi:
                continue
            if len(q.get("options") or []) != 4 or not (bl.get(q["id"]) or {}).get("key") or not q.get("pages"):
                continue
            if tags.get(q["id"]) != st and q.get("section") != section:
                continue
            by[(q["paper"], q.get("part"))].append(q)
        for (paper, part), L in sorted(by.items(), key=lambda kv: str(kv[0])):
            ids = [q["id"] for q in sorted(L, key=qnum)]
            if disputed and not any(bl[i].get("agree") is False and bl[i].get("pick") for i in ids):
                continue
            span = max(p for q in L for p in q["pages"]) - min(p for q in L for p in q["pages"])
            if len(ids) >= least and not set(ids) & skip and (not disputed or span <= 4):  # a wider span is bad page data
                sets.append({"year": y, "ids": ids, "q": {q["id"]: q for q in L}})
    return sets


def english_visual_sets(skip):
    return kind_sets("english-visual", skip)


def page_range(qs):
    pages = sorted({p for q in qs for p in q["pages"]})
    return list(range(max(1, pages[0] - 2), pages[-1] + 1))


def build(a):
    from PIL import Image
    skip = set()
    if a.skip:
        for s in json.load(open(a.skip)):
            skip |= set(s[2] if isinstance(s, list) else s)
    sets = kind_sets(a.kind, skip)
    subject = KINDS[a.kind][0]
    out = OUT / a.kind
    (out / "img").mkdir(parents=True, exist_ok=True)
    for part, i in enumerate(range(0, len(sets), a.per), 1):
        chunk, qmap, n, body = sets[i:i + a.per], {}, 0, []
        for si, s in enumerate(chunk, 1):
            qs = [s["q"][x] for x in s["ids"]]
            imgs = []
            dl = a.kind == "chinese-dialogue"  # the phrase table may sit one page before the dialogue, no more
            ps = sorted({p for q in qs for p in q["pages"]})
            for p in (s.get("pages") or [] if a.kind in SINGLE else
                      list(range(max(1, ps[0] - 1), ps[-1] + 1)) if dl else page_range(qs)):
                src = PP / subject / str(s["year"]) / "pages" / f"p{p:04d}.jpg"
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
                # the printed numbers off ("1 角色"), as on the site, so the pack does not read "(1) 1 角色"
                opts = "".join(f"<div>({j}) {html.escape(L.tex_to_text(o) if a.kind in SINGLE else o)}</div>"  # TeX as plain text
                               for j, o in enumerate(L.strip_opts(q["options"]), 1))
                if a.kind in SINGLE:  # one question: its text (TeX as plain text, scanner labels off), its picture, its options
                    text = html.escape(L.scanner_marks(L.tex_to_text(q.get("text") or ""))).replace("\n", "<br>")
                    pics = "".join(f'<img class="fig" src="img/{x}">' for x in imgs)
                    items.append(f'<div class="q1"><b>Q{n}.</b> {text}{pics}{opts}</div>')
                else:
                    items.append(f'<div class="q"><b>Q{n}.</b> <i>(paper question {q["qno"]})</i> {html.escape(q["text"])}{opts}</div>')
            if a.kind in SINGLE:
                body.append("".join(items))
                continue
            body.append(f"<section><h2>SET {si} (questions Q{n - len(qs) + 1}-Q{n})</h2>"
                        + "".join(f'<img src="img/{x}">' for x in imgs) + f"<h3>Questions for SET {si}</h3>" + "".join(items) + "</section>")
        title = {"english": "Visual Text Pack", "chinese": "Chinese Passage Pack"}.get(subject, f"{subject.title()} Question Pack")
        page = (f'<!doctype html><html><head><meta charset="utf-8"><title>{title}</title><style>'
                "body{font:14px/1.4 Arial,sans-serif;margin:24px} section{page-break-before:always} h3{page-break-before:avoid}"
                "img{display:block;max-width:100%;max-height:24.5cm;margin:0 auto 4px;border:1px solid #ccc;page-break-after:always}"
                ".q{margin:10px 0;page-break-inside:avoid} h2{font-size:18px}"
                ".q1{margin:14px 0;padding-top:6px;border-top:1px solid #ddd;page-break-inside:avoid}"
                ".q1 img.fig{max-height:24cm;max-width:100%;margin:6px 0;page-break-before:auto;page-break-after:auto}</style></head><body>"
                f"<p>{HEAD if subject == 'english' else HEAD_DLG if a.kind == 'chinese-dialogue' else HEAD_ZH if subject == 'chinese' else HEAD_SG.format(subj=SINGLE[a.kind])}</p>{''.join(body)}</body></html>")
        hp = out / f"part{part}.html"
        hp.write_text(page, encoding="utf-8")
        json.dump(qmap, open(out / f"part{part}.qmap.json", "w"))
        subprocess.run(["google-chrome", "--headless", "--no-sandbox", "--disable-gpu", "--no-pdf-header-footer",
                        f"--print-to-pdf={out / f'part{part}.pdf'}", f"file://{hp}"], check=True, capture_output=True, timeout=300)
        mb = (out / f"part{part}.pdf").stat().st_size / 1e6
        bl = {}
        for y in {s["year"] for s in chunk}:
            bl.update({b["id"]: b for b in jl(BLIND / f"{subject}-{y}.jsonl")})
        nd = sum(bl.get(i, {}).get("agree") is False for i in qmap.values())
        print(f"part{part}.pdf: {len(chunk)} sets, {n} questions ({nd} disputed), {mb:.1f} MB")
    print(f"{len(sets)} sets -> {out}")


def score(a):
    out = OUT / a.kind
    subject = KINDS[a.kind][0]
    bl, year = {}, {}
    for y in range(2018, 2027):
        for r in jl(BLIND / f"{subject}-{y}.jsonl"):
            bl[r["id"]] = r
            year[r["id"]] = y
    ans_re = ANS8 if a.kind == "chinese-dialogue" else ANS
    if a.kind == "chinese-dialogue":  # no blind check exists for 8-option items: every printed key is "disputed", confirm only
        for c in jl(DIALOGUE):
            for b in c["blanks"]:
                bl[b["id"]] = {"id": b["id"], "key": b["key"], "pick": None, "agree": None}
                year[b["id"]] = c["year"]
    models = a.models.split(",")
    M = {m: {} for m in models}
    ids = []
    for qf in sorted(out.glob("part*.qmap.json")):
        part = qf.name.split(".")[0]
        qmap = {int(k): v for k, v in json.load(open(qf)).items()}
        ids += qmap.values()
        for m in models:
            # "part1_gemini.txt", any prefix ("complete_..._part1_gemini.txt"), or "part_1_2_gemini.txt"
            num = part.removeprefix("part")
            # the model's name anywhere in the name ("gemini-code-science_part1.txt" too), the part number exact
            # glob every .txt and match the name case-insensitively ("Part 3_Gemini.txt"); "part1-gemini" counts, "part1-14" not
            fs = sorted(f for f in out.glob("*.txt") if re.search(rf"(?<![a-z]){m}(?![a-z])", f.name, re.I)
                        and re.search(rf"part[ _]?{num}(?:_\d+)?(?!\d|to|-\d)", f.name, re.I))  # "Part 10_..." too, not "Part 11to24"
            if len(fs) > 1:
                print(f"warning: {len(fs)} answer files for {part} {m}; using {fs[0].name}")
            for f in fs[:1]:
                got = {}
                for mm in ans_re.finditer(f.read_text(encoding="utf-8", errors="replace")):
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
    C, verdicts = collections.Counter(), collections.defaultdict(list)
    for i in ids:
        if bl[i].get("agree") is True:
            continue
        u = vote(i)
        c = "key stands" if u == str(bl[i]["key"]) else "replace (models + local)" if u and u == str(bl[i].get("pick")) else "other" if u else "split"
        C[c] += 1
        if c == "key stands":
            verdicts[year[i]].append({"id": i, "key_old": str(bl[i]["key"]), "key_new": u, "kind": "confirm", "src": "+".join(models)})
        elif c.startswith("replace"):
            verdicts[year[i]].append({"id": i, "key_old": str(bl[i]["key"]), "key_new": u, "kind": "replace", "src": "+".join(models) + "+local"})
    print("disputed:", dict(C))
    if a.write:  # merged with the verdicts already there (a new verdict on the same id replaces the old one)
        if len(models) < (2 if a.allow_two else 3):
            sys.exit("--write needs 3 or more models (owner rule: unanimous outside models); --allow-two only where the owner chose a pair")
        # a disputed question of this pack that is no longer unanimous loses an older verdict (a re-score must not
        # leave a stale replace behind)
        stale = {i for i in ids if bl[i].get("agree") is not True} - {v["id"] for vs in verdicts.values() for v in vs}
        for y in sorted(set(verdicts) | {year[i] for i in stale}):
            vs = verdicts.get(y, [])
            f = BLIND / "consensus" / f"{subject}-{y}.jsonl"
            have = {v["id"]: v for v in jl(f) if v["id"] not in stale}
            have.update({v["id"]: v for v in vs})
            f.write_text("".join(json.dumps(v, ensure_ascii=False) + "\n" for v in have.values()), encoding="utf-8")
        print("wrote", sum(map(len, verdicts.values())), "verdicts to", BLIND / "consensus")


def selftest():
    qs = [{"pages": [12, 13]}, {"pages": [13]}]
    assert page_range(qs) == [10, 11, 12, 13] and page_range([{"pages": [1]}]) == [1]
    assert ANS.findall("Q1: 3\nQ2：4\nQ10) 2") == [("1", "3"), ("2", "4"), ("10", "2")]
    assert ANS8.findall("Q1: 7\nQ2: 8") == [("1", "7"), ("2", "8")] and ANS.findall("Q1: 7") == []
    print("imgpack selftest ok")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("cmd", choices=("build", "score", "selftest"))
    p.add_argument("--kind", default="english-visual", choices=tuple(KINDS))
    p.add_argument("--write", action="store_true", help="score: write the unanimous verdicts for load_pp select")
    p.add_argument("--allow-two", action="store_true", help="score --write with two models (owner's choice, e.g. Maths 22 Nov 2026)")
    p.add_argument("--per", type=int, default=15)
    p.add_argument("--skip", default=str(TMP / "blind3" / "english" / "vt_pilot_sets.json"))
    p.add_argument("--models", default="gemini,perplexity")
    a = p.parse_args()
    {"build": build, "score": score, "selftest": lambda _a: selftest()}[a.cmd](a)
