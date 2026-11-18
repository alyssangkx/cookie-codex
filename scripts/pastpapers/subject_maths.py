"""Step A for the Maths papers: page, section, question and marks rules.

catalogue.py does the OCR and calls catalogue_pdf() here for subject "maths". The shared pieces (TSV reading, cover
fields, figure crops) are imported from catalogue.py; every rule about how a maths paper is laid out lives here, so
this subject can be refined without touching the others.
ponytail: started as a copy of the shared rules (Science-tuned); the copies diverge as each subject is piloted.
"""
import difflib, json, re

from catalogue import (OUT, OPTION, P6, EXAMWORD, COVERWORD, INDEX_PAGE, WATERMARK, content, exam_of, figure_box, npages, page_range, part_of, read_tsv, school_key, school_of)

ANSWER_TITLE = re.compile(r"answer\s*key|^\s*answers?\s*$|marking\s*scheme|suggested\s*answers?|答案", re.I)

QSTART = re.compile(r"^\s*Q?\s*(\d{1,2})(?:\s*[.．、)]|\s+|$)")  # "12 ...", "12. ...", "Q12"; never "(12)"

STEM = re.compile(r"\s*(The|Which|What|Why|How|Study|Look|Refer|In|An?|Some|Two|Three|Four|Each|When|[A-Z][a-z]+ (?:placed|put|carried|wanted|set|conducted|used|had|has|filled|poured|tested|observed|measured|added|kept|left|prepared|investigated|made|built|connected))\b")

FOOTER = re.compile(r"examination|\bexam\b|prelim|page\s*\d|go on|continue|turn over|booklet|school|\b20\d\d\b", re.I)

MARK_WORD = re.compile(r"^\[\s*(\d{1,2})\s*(?:m|mk|mks|marks?)?\s*\]$|^\(\s*(\d{1,2})\s*(?:m|mk|mks|marks?)\s*\)$|^\[(\d{1,2})$|^(\d{1,2})\]$", re.I)

SEC_MARKS = [
    re.compile(r"questions?\s*(\d{1,2})\s*(?:to|-|–)\s*(\d{1,2})\s*(?:carry|carries)\s*(\d)\s*marks?\s*each", re.I | re.S),
    re.compile(r"(?:questions?|from)\s*(\d{1,2})\s*(?:to|-|–)\s*(\d{1,2}).{0,300}?\((\d{1,3})\s*marks?\)", re.I | re.S),
]

SECTIONS = {'maths': [('short[- ]?answer', 'Short Answer'), ('multiple[- ]?choice', 'MCQ')]}


def section_of(subject, text):
    t = re.sub(r"\s+", "" if subject == "chinese" else " ", text)
    for pat, name in SECTIONS.get(subject, []):
        if re.search(pat, t, re.I): return name
    return None


def page_kind(lines, H, pageno):
    text = " ".join(l["text"] for l in lines)
    if pageno <= 2 and INDEX_PAGE.search(text): return "index"
    c = content(lines, H)
    if len(c) <= 1: return "blank"
    top = " ".join(l["text"] for l in c if l["top"] < 0.5 * H)
    if P6.search(top) and EXAMWORD.search(top) and COVERWORD.search(text): return "cover"
    nopts = len({m for l in c for m in re.findall(r"^\s*\(\s*([1-4])\s*\)", l["text"])})
    if re.search(r"\bname\b", top, re.I) and re.search(r"\bclass\b", top, re.I) \
            and re.search(r"date|time|duration|marks|instruction|booklet", top, re.I) and nopts < 3:
        return "cover"
    for l in c[:3]:  # "Nanyang Primary School P6 SCIENCE Prelim 2024 Suggested Answers"
        if re.search(r"suggested\s*answers?|answer\s*key|marking\s*scheme", l["text"], re.I): return "answers"
    for l in c[:6]:
        title = len(l["text"].split()) <= 5 and len(re.sub(r"\s", "", l["text"])) <= 30  # a heading, not an instruction
        if title and ANSWER_TITLE.search(l["text"]) and not re.search(r"optical|sheet|写|填|涂", l["text"], re.I):
            return "answers"
    # a key table packs several "Q1 Q2 Q3" on a line; question pages (Chinese papers number stems "Q12") have one per line
    qtok = [len(re.findall(r"(?<![\w])Q\s?\d{1,2}(?![\w])", re.sub(r"Q\s?\d{1,2}\s*[-—–~至]+\s*Q?\s?\d{1,2}", "", l["text"])))
            for l in lines]
    if sum(n >= 2 for n in qtok) >= 2 or sum(qtok) >= 15: return "answers"
    if re.search(r"optical\s*answer\s*sheet", top, re.I) and len(c) < 15: return "oas"
    return "content"


def catalogue_pdf(job):
    import numpy as np
    from PIL import Image
    subject, year, pdf, pages_spec = job
    base = OUT / subject / str(year); pdir = base / "pages"; cdir = base / "crops"; cdir.mkdir(exist_ok=True)
    pages = [p for p in page_range(pages_spec, npages(pdf)) if (pdir / f"p{p:04d}.tsv").exists()]
    papers, questions, kinds = [], [], {}
    paper = None; section = None; open_q = None; opt4 = None

    def new_question(qno, page, line):
        nonlocal open_q
        flags = []
        last = paper["last_q"]
        if last and qno != last + 1: flags.append(f"qno_gap_after_{last}")
        paper["last_q"] = qno
        q = {"id": f"{subject[:3]}-{year}-{paper['n']:03d}-{(paper['part'] or 'x').replace(' ', '').replace('/', '')}-q{qno:02d}",
             "subject": subject, "year": year, "paper": paper["paper_id"], "school": paper["school"],
             "exam": paper["exam"], "part": paper["part"], "section": section, "qno": qno, "format": None,
             "marks": None, "marks_source": None, "pages": [page], "text": "", "figures": [], "flags": flags,
             "syllabus": None, "_marks": []}
        questions.append(q); open_q = q
        return q

    for page in pages:
        W, H, words, lines = read_tsv(pdir / f"p{page:04d}.tsv")
        kind = page_kind(lines, H, page); kinds[kind] = kinds.get(kind, 0) + 1
        c = content(lines, H)
        mpath = pdir / f"p{page:04d}.m.tsv"  # margin numbers the main pass dropped: put each in front of its line
        if mpath.exists() and mpath.stat().st_size:
            for w in read_tsv(mpath)[2]:
                m = re.fullmatch(r"Q?(\d{1,2})\.?", w["text"])
                near = [l for l in c if abs(l["top"] - w["top"]) < 45 and l["left"] > w["right"]] if m and w["conf"] >= 30 else []
                if near:
                    l = min(near, key=lambda l: abs(l["top"] - w["top"]))
                    if not QSTART.match(l["text"]):
                        l["text"] = f"{m.group(1)} {l['text']}"; l["left"] = w["left"]
        if kind == "cover":
            text = " ".join(l["text"] for l in c)
            school, guessed = school_of(c, H)
            exam, part = exam_of(text), part_of(text)
            sim = difflib.SequenceMatcher(None, school_key(school), school_key(paper["school"])).ratio() if paper else 0
            # a Booklet B / Paper 2 cover right after this paper's A / 1 is the same paper even when OCR garbles the
            # school name ("Auglo-Chinese Srhoal"); only a clearly different name starts a new one
            follows = bool(paper and part and re.search(r"Booklet B|Paper 2", part) and (exam == paper["exam"] or not exam))
            same = paper and (sim >= 0.75 or (follows and sim >= 0.4))
            if same:
                paper["parts"].append(part); paper["part"] = part
            else:
                paper = {"n": len(papers) + 1, "paper_id": f"{subject[:3]}-{year}-{len(papers) + 1:03d}", "subject": subject,
                         "year": year, "school": school, "school_guessed": guessed, "exam": exam, "part": part,
                         "parts": [part], "first_page": page, "last_page": page, "answer_pages": [], "last_q": 0,
                         "sec_marks": [], "file": pdf.name}
                papers.append(paper)
            section = None; open_q = None; paper["in_answers"] = False; opt4 = None
            if part and paper["last_q"] and re.search(r"paper", part, re.I): paper["last_q"] = 0  # Paper 2 restarts at 1
            if not any((m := QSTART.match(l["text"])) and int(m.group(1)) == 1 and l["top"] > 0.35 * H for l in c):
                continue  # else Q1 is printed on the cover (short tests): read the page as content too
        if paper is None or kind in ("index", "blank", "oas"): continue
        paper["last_page"] = page
        # a key runs until the next cover ("Q33 | a) ..." lines look like questions but are answers)
        opt_page = len({m for l in c for m in re.findall(r"^\s*\(\s*([1-4])\s*\)", l["text"])}) >= 3
        if paper.get("in_answers") and kind == "content" and opt_page:
            paper = {"n": len(papers) + 1, "paper_id": f"{subject[:3]}-{year}-{len(papers) + 1:03d}", "subject": subject,
                     "year": year, "school": None, "school_guessed": True, "exam": None, "part": None, "parts": [None],
                     "first_page": page, "last_page": page, "answer_pages": [], "last_q": 0, "sec_marks": [],
                     "file": pdf.name, "no_cover": True}
            papers.append(paper); section = None; open_q = None; opt4 = None
        if kind == "answers" or paper.get("in_answers"):
            paper["answer_pages"].append(page); paper["in_answers"] = True; open_q = None
            continue
        page_text = "\n".join(l["text"] for l in c)
        for rx in SEC_MARKS:
            for m in rx.finditer(page_text):
                a, b, v = map(int, m.groups())
                per = v if rx is SEC_MARKS[0] else (v / (b - a + 1) if b >= a else 0)
                if per and per == int(per) and per <= 5: paper["sec_marks"].append((a, b, int(per)))
        img = None
        # the question-number column: the leftmost line that starts with a number (scans shift left/right,
        # and footers sit further left than the numbers, so the page's leftmost line is no guide)
        min_left = min((l["left"] for l in c if QSTART.match(l["text"]) and l["left"] < 0.35 * W), default=0)
        starts = []  # (line index, kind, value): kind q | qi (inferred number) | cont | section | part
        for i, l in enumerate(c):
            mc = re.match(r"\s*continued?\s*(?:from|of)\s*question\s*(\d{1,2})", l["text"], re.I)
            if mc:
                starts.append((i, "cont", int(mc.group(1)))); continue
            m = QSTART.match(l["text"])
            if re.match(r"\s*\(\s*4\s*\)", l["text"]):
                opt4 = l["left"]
            elif opt4 is not None and not m and subject != "chinese" and not l["text"].lstrip().startswith("(") \
                    and len(l["words"]) >= 4 and l["left"] < opt4 + 40 and STEM.match(l["text"]) \
                    and not FOOTER.search(l["text"]):
                # an MCQ ended at option (4) and a stem starts at the stem column with no number read:
                # the next question (ponytail: inferred, flagged; step B confirms the number)
                last = paper["last_q"] if not any(s[1] in ("q", "qi") for s in starts) else [s for s in starts if s[1] in ("q", "qi")][-1][2]
                starts.append((i, "qi", last + 1)); opt4 = None; continue
            short = len(l["text"].split()) <= 8 or (subject == "chinese" and len(l["text"]) <= 20)
            if not m and short:
                s = section_of(subject, l["text"])
                if s: starts.append((i, "section", s)); continue
                p = part_of(l["text"]) if len(l["text"]) < 40 else None
                if p: starts.append((i, "part", p)); continue
            if not m or l["left"] > min_left + 0.04 * W: continue
            qs_ = [s for s in starts if s[1] in ("q", "qi")]
            qno = int(m.group(1)); last = qs_[-1][2] if qs_ else paper["last_q"]
            fresh = not last or any(s[1] in ("section", "part") for s in starts[-1:])
            if qs_ and qs_[-1][1] == "qi" and qno == qs_[-1][2]:  # the number turned up after all: drop the guess
                starts.remove(qs_[-1]); last = qno - 1
            if last < qno <= last + 3 or (qno == 1 and fresh) or (qno == last + 1):
                starts.append((i, "q", qno)); opt4 = None
        # walk the page: lines before the first start continue the open question
        cur = open_q; seg_top = c[0]["top"] if c else 0; segments = []
        for idx, (i, kind_, val) in enumerate(starts + [(len(c), "end", None)]):
            top = c[i]["top"] if i < len(c) else 0.955 * H
            if cur is not None:
                segments.append((cur, seg_top, top))
            if kind_ == "section": section = val; cur = None
            elif kind_ == "part": paper["part"] = val
            elif kind_ == "cont":
                cur = next((q for q in reversed(questions) if q["paper"] == paper["paper_id"] and q["qno"] == val), cur)
            elif kind_ in ("q", "qi"):
                cur = new_question(val, page, c[i])
                if kind_ == "qi": cur["flags"].append("qno_inferred")
            seg_top = top
        open_q = cur
        for q, y0, y1 in segments:
            seg_lines = [l for l in c if y0 <= l["top"] < y1]
            if page not in q["pages"]: q["pages"].append(page)
            q["text"] += ("\n" if q["text"] else "") + "\n".join(l["text"] for l in seg_lines)
            for l in seg_lines:
                for w in l["words"]:
                    if w["left"] <= 0.55 * W: continue
                    m = MARK_WORD.match(w["text"])
                    if m: q["_marks"].append(int(next(g for g in m.groups() if g)))
                    else: q["_marks"] += [int(x) for x in re.findall(r"\[\s*(\d{1,2})\s*\]$", w["text"])]
            if img is None: img = np.asarray(Image.open(pdir / f"p{page:04d}.jpg").convert("L"))
            box = figure_box(img, words, lines, y0 - 5, y1 - 5, W)
            if box:
                crop = cdir / f"{q['id']}-p{page:04d}.png"
                Image.fromarray(img[box[1]:box[3], box[0]:box[2]]).save(crop, optimize=True)
                q["figures"].append({"page": page, "bbox": box, "crop": str(crop)})

    for q in questions:
        opts = set(OPTION.findall(q["text"]))
        opts |= {"1" for _ in re.findall(r"\(\s*[lI|]\s*\)", q["text"])}
        if subject == "science" and (q["part"] or "").endswith("Booklet A") and q["qno"] <= 28: opts = {"1", "2", "3", "4"}
        q["format"] = "mcq" if len(opts) >= 3 else "structured" if re.search(r"\(a\).*\(b\)", q["text"], re.S) else "open"
        if q["_marks"] and q["format"] != "mcq":  # in an MCQ, "(4)" at the right edge is an option, not marks
            q["marks"], q["marks_source"] = sum(q.pop("_marks")), "printed"
        else:
            q.pop("_marks")
            pap = next(p for p in papers if p["paper_id"] == q["paper"])
            hit = [per for a, b, per in pap["sec_marks"] if a <= q["qno"] <= b]
            if hit: q["marks"], q["marks_source"] = hit[-1], "section instruction"
            elif subject == "science" and q["format"] == "mcq" and q["qno"] <= 28:
                q["marks"], q["marks_source"] = 2, "PSLE format (Booklet A MCQ = 2)"
            else: q["flags"].append("marks_unknown")
        if not q["text"].strip(): q["flags"].append("no_text")
    for p in papers:
        p["questions"] = sum(q["paper"] == p["paper_id"] for q in questions)
        for k in ("n", "last_q", "part", "in_answers"): p.pop(k, None)
        p["sec_marks"] = sorted(set(map(tuple, p["sec_marks"])))
    with open(base / "papers.jsonl", "w") as f:
        for p in papers: f.write(json.dumps(p, ensure_ascii=False) + "\n")
    with open(base / "questions.jsonl", "w") as f:
        for q in questions: f.write(json.dumps(q, ensure_ascii=False) + "\n")
    s = {"subject": subject, "year": year, "pages": len(pages), "page_kinds": kinds, "papers": len(papers),
         "papers_school_guessed": sum(p["school_guessed"] for p in papers),
         "questions": len(questions), "mcq": sum(q["format"] == "mcq" for q in questions),
         "with_marks": sum(q["marks"] is not None for q in questions),
         "with_figure": sum(bool(q["figures"]) for q in questions),
         "qno_gaps": sum(any(f.startswith("qno_gap") for f in q["flags"]) for q in questions)}
    json.dump(s, open(base / "summary.json", "w"), indent=1)
    return s
