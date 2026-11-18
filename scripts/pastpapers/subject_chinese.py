"""Step A for the Chinese papers: its own page, section, question and marks rules.

catalogue.py does the OCR and calls catalogue_pdf() here for subject "chinese". Shared pieces (TSV reading, cover
fields, figure crops) come from catalogue.py; everything that is about how a Chinese paper is laid out lives here.

How a P6 Chinese paper is laid out (surveyed on the 2026 compilation):
  Paper 1   composition only (第一题 / 第二题 看图作文): no questions to catalogue -> "composition" pages
  Paper 2   sections with Chinese-numeral headings and section marks: "一、语文应用 (15题30分)",
            "三、阅读理解一 (5题10分)"; sub-groups "A组 (Q30-Q33，4题10分)"
            questions numbered "Q1".."Q45" at the left (OCR reads Q1 as Qi/Ql); options (1)-(4)
            instructions quote ranges "[Q1-Q2 请选出…]" (not answer keys); open questions end "(3分)"
            passage sections (短文填空, 阅读理解, 完成对话): the passage sits between the heading and its first question
  keys      "答案" pages or "Q1 Q2 Q3" tables
"""
import difflib, json, re
from pathlib import Path

from catalogue import (OUT, OPTION, P6, EXAMWORD, COVERWORD, INDEX_PAGE, WATERMARK, content, exam_of, figure_box,
                       npages, page_range, part_of, read_tsv, school_key, school_of)

ZQ = re.compile(r"^\s*Q\s?(\d{1,2})(?!\d)")
NUMERAL = "一二三四五六七八九十"
SECTION_NAMES = [("语文应用", "语文应用"), ("短文填空", "短文填空"), ("完成对话", "完成对话"), ("阅读理解", "阅读理解"),
                 ("词语", "语文应用"), ("句子", "语文应用"), ("口试", "口试"), ("听力", "听力理解")]
PASSAGE_SECTIONS = {"短文填空", "阅读理解", "完成对话"}
SEC_MARKS = re.compile(r"(\d{1,2})题(\d{1,3})分")
Q_RANGE = re.compile(r"Q\s?(\d{1,2})\s*[-—–~至]+\s*Q?\s?(\d{1,2})")


def flat(t):
    return re.sub(r"\s+", "", t)


def heading(t):
    """'三、阅读理解一(5题10分)' -> ('阅读理解', '三'); a sub-group 'A组(Q30-Q33,4题10分)' -> ('group', 'A')."""
    f = flat(t)
    if len(f) > 40: return None
    m = re.match(rf"^([{NUMERAL}]+)[、.．:：]?(.*)", f)
    if m:
        for key, name in SECTION_NAMES:
            if key in m.group(2): return name, m.group(1)
        if SEC_MARKS.search(m.group(2)): return "section", m.group(1)
    m = re.match(r"^([A-F])组", f)
    if m: return "group", m.group(1)
    return None


def page_kind(lines, H, pageno):
    text = " ".join(l["text"] for l in lines)
    if pageno <= 2 and INDEX_PAGE.search(text): return "index"
    c = content(lines, H)
    if len(c) <= 1 or "BLANKPAGE" in flat(text).upper(): return "blank"
    top = " ".join(l["text"] for l in c if l["top"] < 0.5 * H)
    if (P6.search(top) or "六年级" in flat(top)) and (EXAMWORD.search(top) or re.search("考试|测验|评估", flat(top))) \
            and (COVERWORD.search(text) or re.search("姓名|班级|说明", flat(text))):
        return "cover"
    f = flat(text)
    if re.search(r"作文|看图|第[一二]题[:：]?.{0,6}(仔细|根据|以)", f) and not ZQ.search(text): return "composition"
    for l in c[:4]:
        if re.search(r"答案|ANSWERKEY|MARKINGSCHEME", flat(l["text"]).upper()) and len(flat(l["text"])) <= 30 \
                and not re.search("写|填|涂|选出", l["text"]):
            return "answers"
    qtok = [len(re.findall(r"(?<![\w])Q\s?\d{1,2}(?![\w])", Q_RANGE.sub("", l["text"]))) for l in lines]
    if sum(n >= 2 for n in qtok) >= 2: return "answers"
    if re.search("OPTICALANSWERSHEET|电脑作答卷", f.upper()) and len(c) < 8: return "oas"
    return "content"


def catalogue_pdf(job):
    import numpy as np
    from PIL import Image
    subject, year, pdf, pages_spec = job
    base = OUT / subject / str(year); pdir = base / "pages"; cdir = base / "crops"; cdir.mkdir(exist_ok=True)
    pages = [p for p in page_range(pages_spec, npages(pdf)) if (pdir / f"p{p:04d}.tsv").exists()]
    papers, questions, passages, kinds = [], [], [], {}
    paper = section = group = None; open_q = None; passage = None

    def new_paper(school, guessed, exam, part, page, **extra):
        p = {"n": len(papers) + 1, "paper_id": f"chi-{year}-{len(papers) + 1:03d}", "subject": subject, "year": year,
             "school": school, "school_guessed": guessed, "exam": exam, "part": part, "parts": [part],
             "first_page": page, "last_page": page, "answer_pages": [], "composition_pages": [], "last_q": 0,
             "sec_marks": [], "in_answers": False, "file": pdf.name, **extra}
        papers.append(p); return p

    for page in pages:
        W, H, words, lines = read_tsv(pdir / f"p{page:04d}.tsv")
        kind = page_kind(lines, H, page); kinds[kind] = kinds.get(kind, 0) + 1
        c = content(lines, H)
        if kind == "cover":
            text = " ".join(l["text"] for l in c)
            school, guessed = school_of(c, H)
            exam, part = exam_of(text), part_of(text)
            sim = difflib.SequenceMatcher(None, school_key(school), school_key(paper["school"])).ratio() if paper else 0
            follows = bool(paper and part and re.search(r"Booklet B|Paper 2", part) and (exam == paper["exam"] or not exam))
            if paper and (sim >= 0.75 or (follows and sim >= 0.4)):
                paper["parts"].append(part); paper["part"] = part; paper["in_answers"] = False
            else:
                paper = new_paper(school, guessed, exam, part, page)
            section = group = None; open_q = passage = None
            continue
        if paper is None or kind in ("index", "blank", "oas"): continue
        paper["last_page"] = page
        if kind == "composition":
            paper["composition_pages"].append(page); continue
        options_page = len({m for l in c for m in re.findall(r"^\s*\(\s*([1-4])\s*\)", l["text"])}) >= 3
        if paper["in_answers"] and kind == "content" and (options_page or any(heading(l["text"]) for l in c[:3])):
            paper = new_paper(None, True, None, None, page, no_cover=True); section = group = None; open_q = passage = None
        if kind == "answers" or paper["in_answers"]:
            paper["answer_pages"].append(page); paper["in_answers"] = True; open_q = None
            continue

        img = None
        qcol = min((l["left"] for l in c if ZQ.match(l["text"])), default=0)
        owner = open_q if open_q is not None else passage  # what the top of the page continues
        seg_top = c[0]["top"] if c else 0; segments = []
        for l in c:
            h = heading(l["text"])
            m = ZQ.match(l["text"])
            start = None
            if h:
                start = ("head", h)
            elif m and l["left"] <= qcol + 0.05 * W:
                qno = int(m.group(1)); last = paper["last_q"]
                if last < qno <= last + 4 or (qno == 1 and last > 8):
                    start = ("q", qno)
            if not start: continue
            if owner is not None: segments.append((owner, seg_top, l["top"]))
            seg_top = l["top"]
            if start[0] == "head":
                kind_h, num = start[1]
                f = flat(l["text"]); sm = SEC_MARKS.search(f); rg = Q_RANGE.search(l["text"])
                if kind_h == "group": group = num
                else: section, group = (kind_h if kind_h != "section" else section), None
                if sm and int(sm.group(1)) and int(sm.group(2)) % int(sm.group(1)) == 0:
                    n, per = int(sm.group(1)), int(sm.group(2)) // int(sm.group(1))
                    a, b = (int(rg.group(1)), int(rg.group(2))) if rg else (paper["last_q"] + 1, paper["last_q"] + n)
                    paper["sec_marks"].append((a, b, per))
                open_q = None
                passage = None
                if section in PASSAGE_SECTIONS:
                    passage = {"id": f"{paper['paper_id']}-{section}-{num}", "paper": paper["paper_id"], "section": section,
                               "group": group, "pages": [page], "text": "", "figures": []}
                    passages.append(passage)
                owner = passage
            else:
                qno = start[1]; flags = [] if not paper["last_q"] or qno == paper["last_q"] + 1 else [f"qno_gap_after_{paper['last_q']}"]
                paper["last_q"] = qno
                open_q = {"id": f"chi-{year}-{paper['n']:03d}-q{qno:02d}", "subject": subject, "year": year,
                          "paper": paper["paper_id"], "school": paper["school"], "exam": paper["exam"], "part": paper["part"],
                          "section": section, "group": group, "passage": passage["id"] if passage else None, "qno": qno,
                          "format": None, "marks": None, "marks_source": None, "pages": [page], "text": "", "figures": [],
                          "flags": flags, "syllabus": None, "_marks": []}
                questions.append(open_q); owner = open_q
        if owner is not None: segments.append((owner, seg_top, 0.955 * H))
        for o, y0, y1 in segments:
            seg = [l for l in c if y0 <= l["top"] < y1 and not heading(l["text"])]
            if page not in o["pages"]: o["pages"].append(page)
            o["text"] += ("\n" if o["text"] else "") + "\n".join(l["text"] for l in seg)
            if "_marks" in o:
                o["_marks"] += [int(x) for l in seg if "题" not in l["text"]
                                for x in re.findall(r"[（(](\d{1,2})分[)）]", flat(l["text"]))]
            if img is None: img = np.asarray(Image.open(pdir / f"p{page:04d}.jpg").convert("L"))
            box = figure_box(img, words, lines, y0 - 5, y1 - 5, W)
            if box:
                crop = cdir / f"{o['id']}-p{page:04d}.png"
                Image.fromarray(img[box[1]:box[3], box[0]:box[2]]).save(crop, optimize=True)
                o["figures"].append({"page": page, "bbox": box, "crop": str(crop)})

    for q in questions:
        opts = set(OPTION.findall(q["text"]))
        q["format"] = "mcq" if len(opts) >= 3 else "open"
        marks = q.pop("_marks")
        pap = next(p for p in papers if p["paper_id"] == q["paper"])
        hit = [per for a, b, per in pap["sec_marks"] if a <= q["qno"] <= b]
        if marks and q["format"] == "open": q["marks"], q["marks_source"] = sum(marks), "printed (N分)"
        elif hit: q["marks"], q["marks_source"] = hit[-1], "section (N题M分)"
        else: q["flags"].append("marks_unknown")
        if not q["text"].strip(): q["flags"].append("no_text")
    for p in papers:
        p["questions"] = sum(q["paper"] == p["paper_id"] for q in questions)
        for k in ("n", "last_q", "part", "in_answers"): p.pop(k, None)
        p["sec_marks"] = sorted(set(map(tuple, p["sec_marks"])))
    for name, rows in (("papers", papers), ("questions", questions), ("passages", passages)):
        with open(base / f"{name}.jsonl", "w") as f:
            for r in rows: f.write(json.dumps(r, ensure_ascii=False) + "\n")
    s = {"subject": subject, "year": year, "pages": len(pages), "page_kinds": kinds, "papers": len(papers),
         "papers_school_guessed": sum(p["school_guessed"] for p in papers), "questions": len(questions),
         "passages": len(passages), "mcq": sum(q["format"] == "mcq" for q in questions),
         "with_marks": sum(q["marks"] is not None for q in questions),
         "with_figure": sum(bool(q["figures"]) for q in questions),
         "qno_gaps": sum(any(f.startswith("qno_gap") for f in q["flags"]) for q in questions)}
    json.dump(s, open(base / "summary.json", "w"), indent=1)
    return s


def selftest():
    assert heading("三 “阅读 理解 一 (5 题 10 分 )") == ("阅读理解", "三")
    assert heading("A 组 (Q30-Q33，4 题 10 分 )") == ("group", "A")
    assert heading("一 语文 应用 (15 题 30 分 )") == ("语文应用", "一")
    assert not heading("Q12 ， 需 要 有 人 翻译 。")
    assert ZQ.match("Q12 ， 需 要").group(1) == "12" and not ZQ.match("(Q21—Q25)")
    assert Q_RANGE.search("[Q1-Q2 请 选 出]").groups() == ("1", "2")
    print("chinese selftest ok")
