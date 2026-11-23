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
SINGLE = {"science-single": "Science", "maths-single": "Mathematics",  # one question per item: key disputes (owner, 21 Nov 2026)
          "science-unsure": "Science", "maths-unsure": "Mathematics",  # printed key read unsure: outside models may only confirm it
          # no printed key at all (owner, 23 Nov 2026): the key is what all three outside models agree on
          "maths-nokey": "Mathematics", "science-nokey": "Science", "english-nokey": "English", "chinese-nokey": "Chinese",
          # live-key audit (owner, 23 Nov 2026): every live standalone MCQ, answered without its key; never writes verdicts
          "english-audit": "English"}
KINDS = {  # kind: (subject, questions, tagger sub-topic, section, minimum keyed questions in a set, sets need a disputed key)
    "english-visual": ("english", (21, 30), "eng-visual-text", "Visual Text", 5, False),
    "chinese-cloze": ("chinese", (16, 20), "chi-cloze-mcq", "短文填空", 1, True),
    "chinese-reading": ("chinese", (21, 25), "chi-yuedu-mcq-text", "阅读理解一", 1, True),
    "chinese-dialogue": ("chinese", (26, 29), "chi-dialogue-mcq", "完成对话", 4, False),
    "science-single": ("science", (1, 99), None, None, 1, True),
    "maths-single": ("maths", (1, 99), None, None, 1, True),
    "science-unsure": ("science", (1, 99), None, None, 1, True),
    "maths-unsure": ("maths", (1, 99), None, None, 1, True),
    "maths-nokey": ("maths", (1, 99), None, None, 1, True),
    "science-nokey": ("science", (1, 99), None, None, 1, True),
    "english-nokey": ("english", (1, 15), None, None, 1, True),
    "chinese-nokey": ("chinese", (1, 99), None, None, 1, True),
    "english-audit": ("english", (1, 15), None, None, 1, True),
}
# the selection whose live rows an audit pack checks, and the sub-topics it covers
AUDIT_SEL = {"english-audit": (TMP / "ppimport" / "eng1826b" / "english" / "selected.jsonl", {"eng-grammar-mcq", "eng-vocab-mcq"})}
AUDIT = "audit.json"  # {source id: [pp id, live key 1-4, year]}
# the latest selections' holds, for the no-key packs
NOKEY_HOLDS = {"maths": TMP / "ppimport" / "math1826d" / "maths" / "rejects.jsonl",
               "science": TMP / "ppimport" / "sci1826d" / "science" / "rejects.jsonl",
               "english": TMP / "ppimport" / "eng1826" / "english" / "rejects.jsonl",
               "chinese": TMP / "ppimport" / "chi1826" / "chinese" / "rejects.jsonl"}
NOKEY = "nokey.json"  # written by build for a -nokey pack: {id: year}, scored as model keys (three models, unanimous)
# owner, 23 Nov 2026 ("more past-paper questions first"): the sub-topics short of 20 past-paper questions whose held
# questions carry a printed key read as unsure (docs/audit/pp-recovery-short-subtopics.md); the latest selections' holds
UNSURE_HOLDS = {"science": TMP / "ppimport" / "sci1826c" / "science" / "rejects.jsonl",
                "maths": TMP / "ppimport" / "math1826c" / "maths" / "rejects.jsonl"}
SHORT_SUBS = {"math-geometry-2d-shapes", "math-geometry-3d-shapes-and-nets", "math-geometry-line-symmetry",
              "math-fractions-addition-and-subtraction-of-fractions", "math-fractions-mixed-numbers-and-improper-fractions",
              "math-decimals-four-operations-with-decimals", "sci-cycles-water-cycle", "sci-diversity-living-characteristics",
              "sci-energy-photo-respiration", "sci-inquiry-predict-hyp"}
CONFIRM_ONLY = "confirm-only.json"  # written by build for an -unsure pack: these ids are scored confirm-only
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


def nokey_sets(kind):
    """Standalone MCQs held only for having no printed key (English: paper questions 1-15, the single-sentence items;
    Chinese: the single-question sections), plus calibration questions whose printed key the blind solver agreed with.
    A question that refers to a picture shows its own exam page(s), as single_sets."""
    import random
    subject = KINDS[kind][0]
    holds = NOKEY_HOLDS[subject]
    if not holds.exists():
        sys.exit(f"missing holds file {holds}")
    only = {r["id"] for r in jl(holds) if r.get("reason") == "no-answer-key"}
    if not only:
        sys.exit("no no-key questions in the holds: nothing to pack")
    nokey, agree = [], []
    for y in range(2018, 2027):
        base = PP / subject / str(y)
        bl = {b["id"]: b for b in jl(BLIND / f"{subject}-{y}.jsonl")}
        st = {t["id"]: t.get("st") for t in jl(base / "tags72.jsonl")}
        for q in jl(base / "merged.jsonl"):
            if q.get("format") != "mcq" or len(q.get("options") or []) != 4 or not q.get("pages"):
                continue
            if subject == "english" and not (qnum(q) and qnum(q) <= 15 and not re.search(r"booklet\s*b", str(q.get("part") or ""), re.I)):
                continue
            if subject == "chinese" and st.get(q["id"]) not in L.CHI_SINGLE:
                continue
            text = L.tex_to_text(q.get("text") or "")
            if L.garbled(text, L.strip_opts(q["options"])):
                continue
            # the checks select applies after the key: a question it would drop anyway never goes to the models
            if subject == "english" and L.eng_incomplete(text) or subject == "chinese" and L.chi_incomplete(text, q["options"]):
                continue
            refers = bool(L.FIG_WORDS.search(text) or L.FIG_LETTER.search(text) or L.realfig(q)
                          or any(L.FIG_LETTER.search(L.strip_num(o)) for o in q["options"])) if subject in ("maths", "science") else L.realfig(q)
            pages = sorted(q["pages"])[:2] if refers else []
            if refers and not all((base / "pages" / f"p{p:04d}.jpg").exists() for p in pages):
                continue
            item = {"year": y, "ids": [q["id"]], "q": {q["id"]: q}, "pages": pages}
            if q["id"] in only:
                nokey.append(item)
            elif (bl.get(q["id"]) or {}).get("agree") is True:
                agree.append(item)
    rng = random.Random(23)
    cal = rng.sample(agree, min(max(60, len(nokey) // 10), len(agree)))  # about 1 calibration question in 11
    items = nokey + cal
    rng.shuffle(items)
    (OUT / kind).mkdir(parents=True, exist_ok=True)
    (OUT / kind / NOKEY).write_text(json.dumps({i["ids"][0]: i["year"] for i in nokey}))
    return items


def audit_sets(kind):
    """Every live row of the audited sub-topics, each shown as its exam question (single_sets layout), with no key."""
    sel, subs = AUDIT_SEL[kind]
    if not sel.exists():
        sys.exit(f"missing selection {sel}")
    # a key the three models set (model-key) needs no second audit by the same models
    live = {r["src_id"]: (r["id"], int(r["answer"]) + 1, r["year"]) for r in jl(sel)
            if r["subtopic"] in subs and "model-key" not in str(r.get("answer_src"))}
    subject = KINDS[kind][0]
    items = []
    for y in sorted({v[2] for v in live.values()}):
        for q in jl(PP / subject / str(y) / "merged.jsonl"):
            if q["id"] in live:
                items.append({"year": y, "ids": [q["id"]], "q": {q["id"]: q}, "pages": []})
    (OUT / kind).mkdir(parents=True, exist_ok=True)
    (OUT / kind / AUDIT).write_text(json.dumps(live))
    import random
    random.Random(29).shuffle(items)
    return items


def single_sets(kind):
    """Science/Maths key disputes as one-question items: every 4-option keyed MCQ whose key the blind solver disputes, plus
    CALIB agreeing ones, shuffled. A question that refers to a picture shows its whole exam page(s) (owner, 22 Nov 2026:
    Gemini scored 77% / 66% on picture questions shown as crops, 95% / 90% on text-only ones); others are text only."""
    import random
    subject = KINDS[kind][0]
    unsure = kind.endswith("-unsure")
    holds = (UNSURE_HOLDS if unsure else HOLDS)[subject]
    if not holds.exists():  # jl() reads a missing file as empty: the pack would hold calibration only and wipe confirm-only.json
        sys.exit(f"missing holds file {holds}")
    only = {r["id"] for r in jl(holds) if r.get("reason") == ("grid-uncertain" if unsure else "blind-disagree")}
    dis, agree = [], []
    for y in range(2018, 2027):
        base = PP / subject / str(y)
        bl = {b["id"]: b for b in jl(BLIND / f"{subject}-{y}.jsonl")}
        st = {t["id"]: t.get("st") for t in jl(base / "tags72.jsonl")} if unsure else {}
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
            if unsure and q["id"] in only and st.get(q["id"]) in SHORT_SUBS:
                dis.append(item)
            elif not unsure and b.get("agree") is False and b.get("pick") and q["id"] in only:
                dis.append(item)
            elif b.get("agree") is True and q["id"] not in only:
                agree.append(item)
    rng = random.Random(21)
    items = dis + rng.sample(agree, min(60 if unsure else CALIB, len(agree)))
    if unsure:
        (OUT / kind).mkdir(parents=True, exist_ok=True)
        (OUT / kind / CONFIRM_ONLY).write_text(json.dumps(sorted(i["ids"][0] for i in dis)))
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
    if kind.endswith("-audit"):
        return audit_sets(kind)
    if kind.endswith("-nokey"):
        return nokey_sets(kind)
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
                f"<p>{HEAD_SG.format(subj=SINGLE[a.kind]) if a.kind in SINGLE else HEAD if subject == 'english' else HEAD_DLG if a.kind == 'chinese-dialogue' else HEAD_ZH}</p>{''.join(body)}</body></html>")
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


# --allow-two pairs the owner approved: (subject, models). Maths: Claude + Perplexity for key disputes and unsure confirms
# (22 Nov 2026) and no-key keys (23 Nov 2026); every other subject needs all three outside models.
ALLOWED_PAIRS = [("maths", {"claude", "perplexity"})]


def model_list(s):
    """--models as distinct lower-case names: "Claude, claude" is one model (answer files match names case-insensitively)."""
    return list(dict.fromkeys(m.strip().lower() for m in s.split(",") if m.strip()))


def write_gate(subject, models, allow_two=False):
    """None when score --write may write with these models, else the reason it may not: three or more models, or a
    pair the owner approved for this subject, typed with --allow-two."""
    if len(models) >= 3:
        return None
    if len(models) == 2 and allow_two and (subject, set(models)) in ALLOWED_PAIRS:
        return None
    if len(models) == 2 and not allow_two and (subject, set(models)) in ALLOWED_PAIRS:
        return "this approved pair needs --allow-two typed (the owner's choice on record)"
    return f"--write needs three outside models; a pair only as approved: {[(s, sorted(m)) for s, m in ALLOWED_PAIRS]}"


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
    co = OUT / a.kind / CONFIRM_ONLY
    if a.kind.endswith("-unsure") and not co.exists():  # the confirm-only rule must never fall back to a dispute pack's
        sys.exit(f"missing {co}: rebuild the pack")
    unsure_ids = set(json.loads(co.read_text())) if co.exists() else set()
    if a.kind.endswith("-audit"):
        return audit_score(a)
    nk = OUT / a.kind / NOKEY
    if a.kind.endswith("-nokey") and not nk.exists():
        sys.exit(f"missing {nk}: rebuild the pack")
    nokey = json.loads(nk.read_text()) if nk.exists() else {}
    for i, y in nokey.items():  # no printed key: the models' unanimous answer becomes the key (three models, or the owner's approved pair: write_gate)
        bl[i] = {"id": i, "key": None, "pick": None, "agree": None}
        year[i] = y
    for i in unsure_ids:  # an unsure printed key: confirm only, never replace
        if i in bl:
            bl[i] = dict(bl[i], agree=None, pick=None)
    models = model_list(a.models)  # a repeated name is one model
    M = {m: {} for m in models}
    ids, missing = [], []
    for qf in sorted(out.glob("part*.qmap.json")):
        part = qf.name.split(".")[0]
        qmap = {int(k): v for k, v in json.load(open(qf)).items()}
        ids += qmap.values()
        for m in models:
            # "part1_gemini.txt", any prefix ("complete_..._part1_gemini.txt"), or "part_1_2_gemini.txt"
            num = part.removeprefix("part")
            # the model's name anywhere in the name ("gemini-code-science_part1.txt" too), the part number exact
            # glob every .txt and match the name case-insensitively ("Part 3_Gemini.txt"); "part1-gemini" counts, "part1-14" not
            fs = answer_files(out, num, m)
            if not fs:
                missing.append(f"{part} {m}")
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
        if i in nokey:
            c = "model key" if u else "split"
            C[c] += 1
            if u:
                verdicts[year[i]].append({"id": i, "key_old": None, "key_new": u, "kind": "model-key", "src": "+".join(models)})
            continue
        c = "key stands" if u == str(bl[i]["key"]) else "replace (models + local)" if u and u == str(bl[i].get("pick")) else "other" if u else "split"
        C[c] += 1
        if c == "key stands":
            verdicts[year[i]].append({"id": i, "key_old": str(bl[i]["key"]), "key_new": u, "kind": "confirm", "src": "+".join(models),
                                      **({"unsure": True} if i in unsure_ids else {})})  # only these lift load_pp's grid-uncertain hold
        elif c.startswith("replace"):
            verdicts[year[i]].append({"id": i, "key_old": str(bl[i]["key"]), "key_new": u, "kind": "replace", "src": "+".join(models) + "+local"})
    print("disputed:", dict(C))
    if missing:  # shown on every run, so a dry run's counts are read with the gap in mind
        print(f"WARNING: {len(missing)} answer file(s) missing: {', '.join(missing)} (their questions count as unanswered)")
    if a.write:  # merged with the verdicts already there (a new verdict on the same id replaces the old one)
        why = write_gate(subject, models, a.allow_two)  # first: never ask the owner to check a calibration for a refused model set
        if why:
            sys.exit(why)
        # a model key is the only key those questions get: write only after a clean calibration, unless the owner has looked
        if nokey and (len(cu) < 30 or ok / len(cu) < 0.98) and not a.accept_cal:
            sys.exit(f"calibration {ok}/{len(cu)} is under the 98% bar (or too small): check it, then --accept-cal on the owner's OK")
        # a disputed question of this pack that is no longer unanimous loses an older verdict (a re-score must not
        # leave a stale replace behind)
        # only a real split counts (every model answered, or the answers given already differ): an unanswered question (missing, misnamed, cut-off or
        # unreadable answer file) keeps its older verdict
        real_split = lambda i: all(i in M[m] for m in models) or len({M[m][i] for m in models if i in M[m]}) > 1
        stale = ({i for i in ids if bl[i].get("agree") is not True and real_split(i)}
                 - {v["id"] for vs in verdicts.values() for v in vs})
        for y in sorted(set(verdicts) | {year[i] for i in stale}):
            vs = verdicts.get(y, [])
            f = BLIND / "consensus" / f"{subject}-{y}.jsonl"
            have = {v["id"]: v for v in jl(f) if v["id"] not in stale}
            have.update({v["id"]: v for v in vs})
            f.write_text("".join(json.dumps(v, ensure_ascii=False) + "\n" for v in have.values()), encoding="utf-8")
        print("wrote", sum(map(len, verdicts.values())), "verdicts to", BLIND / "consensus")


def answer_files(out, num, m):
    """The answer files of part `num` from model `m`: the model's name anywhere in the name ("gemini-code-science_part1.txt"),
    case-insensitive, the part number exact ("Part 10_..." too, not "Part 11to24" or "part1-14")."""
    return sorted(f for f in out.glob("*.txt") if re.search(rf"(?<![a-z0-9]){re.escape(m)}(?![a-z0-9])", f.name, re.I)
                  and re.search(rf"part[ _]?{num}(?:_\d+)?(?!\d|to|-\d)", f.name, re.I))


def audit_score(a):
    """Lists the live rows where all models agree on an answer other than the live key (audit_report.json, ids and keys
    only), for the owner to decide. Writes no verdicts."""
    out = OUT / a.kind
    live = json.loads((out / AUDIT).read_text())
    models = model_list(a.models)
    if len(models) < 3:
        sys.exit("an audit needs all three outside models: 'unanimous' must mean three")
    M = {m: {} for m in models}
    for qf in sorted(out.glob("part*.qmap.json")):
        num = qf.name.split(".")[0].removeprefix("part")
        qmap = {int(k): v for k, v in json.load(open(qf)).items()}
        for m in models:
            fs = answer_files(out, num, m)
            if not fs:
                sys.exit(f"no answers from {m} for part {num}: an audit with gaps would read as clean")
            for f in fs[:1]:
                for mm in ANS.finditer(f.read_text(encoding="utf-8", errors="replace")):
                    if int(mm.group(1)) in qmap:
                        M[m][qmap[int(mm.group(1))]] = mm.group(2)
    agree, against, split = 0, [], 0
    for src, (pid, key, y) in live.items():
        v = [M[m].get(src) for m in models]
        if None in v or len(set(v)) > 1:
            split += 1
        elif v[0] == str(key):
            agree += 1
        else:
            against.append({"pp_id": pid, "src_id": src, "live_key": key, "models": int(v[0]), "year": y})
    (out / "audit_report.json").write_text(json.dumps(against, indent=1))
    print(f"{len(live)} live rows: models agree with the key {agree}, unanimous against it {len(against)}, split or missing {split}")
    print("->", out / "audit_report.json")


def selftest():
    qs = [{"pages": [12, 13]}, {"pages": [13]}]
    assert page_range(qs) == [10, 11, 12, 13] and page_range([{"pages": [1]}]) == [1]
    assert ANS.findall("Q1: 3\nQ2：4\nQ10) 2") == [("1", "3"), ("2", "4"), ("10", "2")]
    assert ANS8.findall("Q1: 7\nQ2: 8") == [("1", "7"), ("2", "8")] and ANS.findall("Q1: 7") == []
    assert model_list(" Claude,claude ,Perplexity") == ["claude", "perplexity"]
    assert {s for s, _ in ALLOWED_PAIRS} == {"maths"}, "a two-model pair is approved for Maths only (owner): other subjects need three"
    assert write_gate("maths", model_list("Claude, Perplexity"), True) is None and "--allow-two" in write_gate("maths", ["claude", "perplexity"]) and write_gate("science", ["claude", "perplexity"], True)
    assert write_gate("maths", ["claude", "grok"]) and write_gate("maths", ["claude"]) and write_gate("science", ["a", "b", "c"]) is None
    print("imgpack selftest ok")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("cmd", choices=("build", "score", "selftest"))
    p.add_argument("--kind", default="english-visual", choices=tuple(KINDS))
    p.add_argument("--write", action="store_true", help="score: write the unanimous verdicts for load_pp select")
    p.add_argument("--accept-cal", action="store_true", help="score --write on a no-key pack below the calibration bar (owner checked)")
    p.add_argument("--allow-two", action="store_true", help="score --write with two models (owner's choice, e.g. Maths 22 Nov 2026)")
    p.add_argument("--per", type=int, default=15)
    p.add_argument("--skip", default=str(TMP / "blind3" / "english" / "vt_pilot_sets.json"))
    p.add_argument("--models", default="gemini,perplexity")
    a = p.parse_args()
    {"build": build, "score": score, "selftest": lambda _a: selftest()}[a.cmd](a)
