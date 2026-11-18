"""Step A for the English papers: its own page, section, question, passage and marks rules.

catalogue.py does the OCR and calls catalogue_pdf() here for subject "english". Shared pieces (TSV reading, cover
fields, figure crops) come from catalogue.py; everything that is about how a P6 English paper is laid out lives here.

How a P6 English paper is laid out (surveyed on the 2026 compilation; RGPS, Nanyang, CHIJ St Nicholas):
  Paper 1   writing (Part 1 situational writing, Part 2 continuous writing): "writing" pages, no questions
  Paper 3 / 4  listening / oral: "listening" / "oral" pages, no questions (none seen in 2026)
  Paper 2   Booklet A (MCQ, shade the OAS) then Booklet B (written), question numbers run 1..75 across both:
              A Grammar MCQ 1-10, B Vocabulary MCQ 11-15, C Vocabulary Cloze 16-20 (passage, blanks (16).., MCQ),
              D Visual Text 21-25 (Text 1 + Text 2, then 5 MCQ)                                  [Booklet A, 1 mark each]
              E Grammar Cloze 26-35 (word list, blanks), F Editing 36-45, G Comprehension Cloze 46-60,
              H Synthesis 61-65 (2 marks each), I Comprehension OE 66-75 (20 marks, "[2m]" printed)   [Booklet B]
            the OE passage is printed at the END of Booklet A ("Refer to the passage below ... questions 66 to 75 in
            Booklet B"); Booklet B says "Read the passage on page N of Booklet A and answer questions 66 to 75".
  headings  "Section E: Grammar Cloze (10 x 1 mark)" (some schools print no heading, only the instruction line)
  numbering "1." / "21 " at the left; cloze and editing have no numbered stems: the blanks "(26)".."(35)" sit in the passage
  keys      "YEAR : 2026 / LEVEL / SCHOOL" pages, "ANSWER KEY" pages, or "Q71 | ..." lines
Output: papers.jsonl (with "sections"), questions.jsonl (each has "passage"), passages.jsonl (each lists its "questions").
A cloze/editing blank is a question: qno = the blank number, text = the line(s) around the blank, format "open".
"""
import difflib, json, os, re

from catalogue import (OUT, OPTION, P6, EXAMWORD, INDEX_PAGE, WATERMARK, exam_of, figure_box, npages, page_range,
                       read_tsv, school_key, school_of)

ANSWER_TITLE = re.compile(r"answer\s*key|^\s*answers?\s*$|marking\s*scheme|suggested\s*answers?|答案", re.I)
QSTART = re.compile(r"^\s*Q?\s*(\d{1,2})(?:\s*[.．、,)|]|\s+|$)")  # "12 ...", "12. ...", "Q12"; never "(12)"
QCONF = re.compile(r"^\s*([0-9A-Za-z|&]{1,2})(?:\s*[.．、)]|\s+|$)")  # a number token the OCR may have garbled
CONF = {"1": "1il|47", "2": "2zZ", "3": "38", "4": "4", "5": "5Ss", "6": "6bG&", "7": "7", "8": "8B3&", "9": "9g", "0": "0Oo"}
BLANK = re.compile(r"\(\s*(\d{1,2})\s*\)")
STEM = re.compile(r"\s*(The|Which|What|Why|How|Study|Look|Refer|In|An?|Some|Two|Three|Four|Each|When|[A-Z][a-z]+ (?:placed|put|carried|wanted|set|used|had|has|made|went|took|gave))\b")
FOOTER = re.compile(r"examination|\bexam\b|prelim|page\s*\d|go on|continue|turn over|booklet|school|\b20\d\d\b", re.I)
TRAILER = re.compile(r"you may now go on|end of (paper|booklet)|please note that the passage|go on to booklet", re.I)

MARK_RX = re.compile(r"[\[{(]\s*([0-9iIl|SsOo]{1,2})\s*(?:m|rn|ry|mk|mks|marks?)\s*[\]})]")  # "[2m]", "[im]", "{2m]", "[Sry]"
OCR_DIGIT = {"i": 1, "l": 1, "I": 1, "|": 1, "S": 3, "s": 3}  # S is a garbled 3 on the one image checked (RGPS Q73 "[3m]"): flagged as a guess

HEAD = re.compile(r"^\s*(?:section|part)\s*[A-Z0-9]{1,2}\b\s*[:;.\-]?", re.I)
INSTR = re.compile(r"^\s*(?:for\s+each\s+(?:of\s+the\s+)?questions?|for\s+questions?|there\s+are\s+\d+\s+blanks|fill\s+in\s+each\s+blank"
                   r"|each\s+of\s+the\s+underlined|study\s+the\s+(?:poster|text|notice|advert|brochure|leaflet|flyer|email|extract|table|timetable|map|information|infographic|schedule|programme)"
                   r"|refer\s+to\s+the\s+(?:passage|text)|read\s+the\s+(?:passage|text|extract)|for\s+each\s+of\s+the\s+questions)", re.I)

MCQ_SECS = {"Grammar MCQ", "Vocabulary MCQ", "Vocabulary Cloze", "Visual Text", "Comprehension MCQ"}
BLANK_SECS = {"Grammar Cloze", "Editing", "Comprehension Cloze"}  # no numbered stems: the question is the blank
PASSAGE_SECS = {"Vocabulary Cloze", "Visual Text", "Grammar Cloze", "Editing", "Comprehension Cloze", "Comprehension OE", "Comprehension MCQ"}
DEFAULT_PER = {"Grammar MCQ": 1, "Vocabulary MCQ": 1, "Vocabulary Cloze": 1, "Visual Text": 1, "Grammar Cloze": 1,
               "Editing": 1, "Comprehension Cloze": 1, "Synthesis": 2}  # PSLE format: used only when the paper's own numbers are unreadable
TOTAL_ONLY = {"Comprehension OE"}  # marks differ per question: never total / count


def classify(text):
    """Section name from a heading or instruction text, or None."""
    t = re.sub(r"\s+", " ", text)
    for pat, name in [
            (r"grammar\s*cloze|list of words|numbered \d+ to \d+", "Grammar Cloze"),
            (r"editing|spelling or grammatical|underlined words? contains?", "Editing"),
            (r"comprehension\s*cloze|fill in each blank with a suitable", "Comprehension Cloze"),
            (r"vocabulary\s*cloze|closest in meaning", "Vocabulary Cloze"),
            (r"synthesis|transformation|rewrite the given", "Synthesis"),
            (r"visual\s*text|study the (?:poster|notice|advert\w*|brochure|leaflet|flyer|email|extract|text|information|infographic|schedule|programme)", "Visual Text"),
            (r"open[- ]?ended|read the passage on page|passage below when you answer|answer questions \d+ to \d+ in booklet b", "Comprehension OE"),
            (r"comprehension.{0,40}(?:mcq|multiple)|read the passage.{0,200}(?:choose|best answer)", "Comprehension MCQ"),
            (r"vocabulary", "Vocabulary MCQ"),
            (r"grammar", "Grammar MCQ"),
            (r"comprehension", "Comprehension OE")]:
        if re.search(pat, t, re.I): return name
    return None


def eng_part_of(text):
    """Paper 1-4 and Booklet A/B from a cover; English also has Paper 3 (listening) and 4 (oral)."""
    m = re.search(r"booklet\s*([AB])\b", text, re.I)
    p = re.search(r"paper\s*([1-4])\b", text, re.I)
    if not p:
        for pat, n in ((r"\bwriting\b", "1"), (r"listening", "3"), (r"oral\b", "4")):
            if re.search(pat, text, re.I): p = re.search(r"(.)", n); break
    part = "/".join(x for x in (p and f"Paper {p.group(1)}", m and f"Booklet {m.group(1).upper()}") if x)
    return part or None


def conf_match(tok, expected):
    s = str(expected)
    if len(tok) != len(s) or tok == "I": return False
    return all(t == e or t in CONF.get(e, e) for t, e in zip(tok, s))


def content(lines, H):
    """Like catalogue.content but the top band starts at 3%: some papers print an instruction line at the very top."""
    return [l for l in lines if 0.03 * H < l["top"] < 0.955 * H and not WATERMARK.search(l["text"])
            and len(re.findall(r"[\w一-鿿]", l["text"])) >= 2]


def mark_value(tok):
    """A printed mark like "[2m]" -> 2, "[im]" -> 1, "[Sm]" -> 3 (a guess, see OCR_DIGIT), else None."""
    m = MARK_RX.fullmatch(tok.strip())
    if not m: return None
    v = m.group(1)
    if v.isdigit(): return int(v) if 0 < int(v) <= 20 else None
    return OCR_DIGIT.get(v)


def page_kind(lines, H, pageno):
    text = " ".join(l["text"] for l in lines)
    if pageno <= 2 and INDEX_PAGE.search(text): return "index"
    c = content(lines, H)
    if len(c) <= 1: return "blank"
    top = " ".join(l["text"] for l in c if l["top"] < 0.5 * H)
    nopts = len({m for l in c for m in re.findall(r"^\s*\(\s*([1-4])\s*\)", l["text"])})
    ctext = " ".join(l["text"] for l in c)
    if P6.search(ctext) and EXAMWORD.search(ctext) and nopts < 3 and (
            re.search(r"instructions?\s*to\s*candidates|duration|total\s*time|this\s*booklet|do not (?:open|turn)|name\s*[:;(]", ctext, re.I)):
        return "cover"
    for l in c[:3]:  # "Nanyang Primary School P6 ENGLISH Prelim 2024 Suggested Answers"
        if re.search(r"suggested\s*answers?|answer\s*key|marking\s*scheme", l["text"], re.I): return "answers"
    for l in c[:6]:
        title = len(l["text"].split()) <= 5 and len(re.sub(r"\s", "", l["text"])) <= 30  # a heading, not an instruction
        if title and ANSWER_TITLE.search(l["text"]) and not re.search(r"optical|sheet|写|填|涂", l["text"], re.I):
            return "answers"
    # a key table packs several "Q1 Q2 Q3" on a line; question pages have one number per line
    qtok = [len(re.findall(r"(?<![\w])Q\s?\d{1,2}(?![\w])", re.sub(r"Q\s?\d{1,2}\s*[-—–~至]+\s*Q?\s?\d{1,2}", "", l["text"])))
            for l in lines]
    if sum(n >= 2 for n in qtok) >= 2 or sum(qtok) >= 15: return "answers"
    head = " ".join(l["text"] for l in c[:5])
    if re.search(r"situational\s*writing|continuous\s*writing|^\s*your\s*task\b|part\s*[12]\s*[:;]\s*(?:situational|continuous)", head, re.I | re.M): return "writing"
    if re.search(r"listening\s*comprehension|stimulus.based|reading\s*aloud", head, re.I) and nopts < 3: return "listening"
    return "content"


def catalogue_pdf(job):
    import numpy as np
    from PIL import Image
    subject, year, pdf, pages_spec = job
    base = OUT / subject / str(year); pdir = base / "pages"; cdir = base / "crops"; cdir.mkdir(exist_ok=True)
    pages = [p for p in page_range(pages_spec, npages(pdf)) if (pdir / f"p{p:04d}.tsv").exists()]
    papers, questions, passages, kinds = [], [], [], {}
    st = {"paper": None, "sec": None, "passage": None, "q": None, "opt4": None, "qcol": 0}

    def new_paper(school, guessed, exam, part, page, no_cover=False):
        n = len(papers) + 1
        p = {"n": n, "paper_id": f"{subject[:3]}-{year}-{n:03d}", "subject": subject, "year": year, "school": school,
             "school_guessed": guessed, "exam": exam, "part": part, "parts": [part], "first_page": page, "last_page": page,
             "answer_pages": [], "last_q": 0, "sections": [], "cover_marks": [], "file": pdf.name, "in_answers": False,
             "mcq_blocks": 0}
        if no_cover: p["no_cover"] = True
        papers.append(p); return p

    def reset():
        st.update(sec=None, passage=None, q=None, opt4=None)

    def start_section(name, lines_text, page, ref_only):
        paper = st["paper"]
        nxm = re.search(r"(\d{1,2})\s*[x×*]\s*\W{0,2}\s*(\d{1,2})\s*marks?", lines_text, re.I)
        total = None if nxm else re.search(r"\(?\s*(\d{1,3})\s*marks\b\s*\)?", lines_text, re.I)
        rg = re.search(r"questions?\s*(?:from\s*)?(\d{1,2})\s*(?:to|tc|-|–|and)\s*(\d{1,2})|numbered\s*(\d{1,2})\s*(?:to|tc|-)\s*(\d{1,2})|from\s*(\d{1,2})\s*to\s*(\d{1,2})",
                       lines_text, re.I)
        a = b = None
        if rg:
            g = [x for x in rg.groups() if x]
            a, b = int(g[0]), int(g[1])
            if b < a or b - a > 40: a = b = None
        nexp = (b - a + 1) if a else (int(nxm.group(1)) if nxm else (int(total.group(1)) if total and int(total.group(1)) <= 30 else None))
        if a and 0 < abs(a - (paper["last_q"] + 1)) <= 9 and name in MCQ_SECS | {"Synthesis"} and b and b >= paper["last_q"] + 1 and not ref_only:
            a = paper["last_q"] + 1  # "from 7 to 10" read for "from 1 to 10": questions follow on from the last one
        sec = {"name": name, "a": a, "b": b, "first": a or paper["last_q"] + 1, "nexp": nexp, "total": int(total.group(1)) if total else None,
               "nxm": (int(nxm.group(1)), int(nxm.group(2))) if nxm else None, "qs": [], "page": page, "passage": None}
        paper["sections"].append(sec); st["sec"] = sec; st["opt4"] = None
        if name in PASSAGE_SECS and not ref_only:
            ps = {"id": f"{paper['paper_id']}-P{len(passages) + 1:02d}", "paper": paper["paper_id"], "section": name,
                  "qrange": [a, b] if a else None, "pages": [page], "text": "", "figures": [], "questions": []}
            passages.append(ps); sec["passage"] = ps; st["passage"] = ps
        else:
            st["passage"] = None
        return sec

    def new_question(qno, page, flags, text=""):
        paper, sec = st["paper"], st["sec"]
        last = paper["last_q"]
        flags = list(flags)
        if last and qno != last + 1: flags.append(f"qno_gap_after_{last}")
        paper["last_q"] = qno
        name = sec["name"] if sec else None
        pid = sec["passage"]["id"] if sec and sec["passage"] else None
        q = {"id": f"{subject[:3]}-{year}-{paper['n']:03d}-{(paper['part'] or 'x').replace(' ', '').replace('/', '')}-q{qno:02d}",
             "subject": subject, "year": year, "paper": paper["paper_id"], "school": paper["school"],
             "exam": paper["exam"], "part": paper["part"], "section": name, "passage": pid, "qno": qno, "format": None,
             "marks": None, "marks_source": None, "pages": [page], "text": text, "figures": [], "flags": flags,
             "syllabus": None, "_marks": [], "_sec": sec}
        questions.append(q)
        if sec: sec["qs"].append(q)
        if pid and name not in ("Comprehension OE",): sec["passage"]["questions"].append(q["id"])
        return q

    for page in pages:
        W, H, words, lines = read_tsv(pdir / f"p{page:04d}.tsv")
        kind = page_kind(lines, H, page)
        paper = st["paper"]
        if kind == "content" and paper is not None:  # Paper 1 / 3 / 4 pages carry no questions
            pp = paper["part"] or ""
            if re.search(r"Paper 1", pp) and not re.search(r"Paper 2", pp): kind = "writing"
            elif re.search(r"Paper 3", pp): kind = "listening"
            elif re.search(r"Paper 4", pp): kind = "oral"
        kinds[kind] = kinds.get(kind, 0) + 1
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
            exam = exam_of(text)
            part = eng_part_of(" ".join(l["text"] for l in c if len(l["text"].split()) <= 8 and not re.search(r"booklet\s*b\b.*(?:go|continue)|do not", l["text"], re.I))) or eng_part_of(text)
            sim = difflib.SequenceMatcher(None, school_key(school), school_key(paper["school"])).ratio() if paper else 0
            # a later Paper / Booklet B cover right after this paper's is the same paper even when OCR garbles the
            # school name ("Auglo-Chinese Srhoal"); only a clearly different name starts a new one
            follows = bool(paper and part and re.search(r"Booklet B|Paper [234]", part) and (exam == paper["exam"] or not exam))
            same = paper and (sim >= 0.75 or (follows and (sim >= 0.4 or guessed)))  # no school name read on a B cover: still the same paper
            if same:
                paper["parts"].append(part); paper["part"] = part
            else:
                paper = st["paper"] = new_paper(school, guessed, exam, part, page)
            paper["cover_marks"] += [int(x) for x in re.findall(r"(\d{1,3})\s*marks?\b", text, re.I)]
            paper["last_page"] = page; paper["in_answers"] = False; reset()
            continue  # a cover never holds questions (its numbered lines are the candidate instructions)
        if paper is None or kind in ("index", "blank"): continue
        paper["last_page"] = page
        opt_page = len({m for l in c for m in re.findall(r"^\s*\(\s*([1-4])\s*\)", l["text"])}) >= 3
        if paper["in_answers"] and kind == "content" and opt_page:  # a school's paper starts without a cover
            paper = st["paper"] = new_paper(None, True, None, None, page, no_cover=True); reset()
        if kind == "answers" or paper["in_answers"]:
            paper["answer_pages"].append(page); paper["in_answers"] = True; st["q"] = None
            continue
        if kind in ("writing", "listening", "oral"):
            paper["non_question_pages"] = paper.get("non_question_pages", []) + [page]; reset()
            continue

        # a question number printed alone in the margin, a few pixels off its text line: put it in front of the text
        for l in c:
            if re.fullmatch(r"\s*\d{1,2}\s*[.．)]?\s*", l["text"]):
                part_ = [o for o in c if o is not l and abs(o["top"] - l["top"]) < 60 and o["left"] > l["right"]]
                if part_:
                    o = min(part_, key=lambda o: abs(o["top"] - l["top"]))
                    if re.match(rf"\s*{int(l['text'].strip(' .．)'))}\b", o["text"]): l["drop"] = True
                    else: l["top"] = min(l["top"], o["top"]) - 1
        c = sorted((l for l in c if not l.get("drop")), key=lambda l: (l["top"], l["left"]))
        img = None
        min_left = min((l["left"] for l in c if QSTART.match(l["text"]) and l["left"] < 0.35 * W
                        and not BLANK.match(l["text"])), default=0) or paper.get("qcol_", 0)
        if min_left: paper["qcol_"] = min_left
        segs = []; owner = st["passage"] if st["q"] is None else st["q"]; seg_top = c[0]["top"] if c else 0

        def switch(new_owner, top):
            nonlocal owner, seg_top
            if owner is not None: segs.append((owner, seg_top, top))
            owner, seg_top = new_owner, top

        nxt = []
        if pages.index(page) + 1 < len(pages):  # the first lines of the next page: an instruction may run over the page break
            try:
                nW, nH, _, nl = read_tsv(pdir / f"p{pages[pages.index(page) + 1]:04d}.tsv")
                nxt = [x["text"] for x in content(nl, nH)[:3]]
            except OSError: pass

        def dtext(i, n=4):
            t = [x["text"] for x in c[i:i + n]]
            return " ".join(t + (nxt[:i + n - len(c)] if i + n > len(c) else []))
        score_table = bool(re.search(r"section\s+marks|total\s+marks|marks\s+obtained|score\s+table", " ".join(x["text"] for x in c), re.I)) \
            and sum(bool(re.search(r"\s\d{1,2}\s*$", x["text"])) for x in c) >= 4
        i = 0
        while i < len(c):
            l = c[i]; text = l["text"]; sec = st["sec"]
            i += 1
            if score_table: continue  # a "Section / Marks" table: its row names are not headings
            if TRAILER.search(text):
                switch(None, l["top"]); st["q"] = None; continue
            mc = re.match(r"\s*continued?\s*(?:from|of)\s*question\s*(\d{1,2})", text, re.I)
            if mc:
                q0 = next((q for q in reversed(questions) if q["paper"] == paper["paper_id"] and q["qno"] == int(mc.group(1))), None)
                switch(q0 if q0 else owner, l["top"]); st["q"] = q0 or st["q"]; continue
            m = QSTART.match(text)
            isq = bool(m) and not BLANK.match(text)
            # ---- a section heading or an instruction line starts (or continues) a section
            heading = bool(HEAD.match(text)) and not (isq and not re.match(r"\s*(section|part)\b", text, re.I))
            instr = bool(INSTR.match(text)) and not (sec and sec["name"] in BLANK_SECS and BLANK.search(text))
            kw = (not heading and not instr and not isq and len(text.split()) <= 9 and not text.lstrip().startswith("(")
                  and not FOOTER.search(text)
                  and bool(re.search(r"cloze|synthesis|transformation|visual text|open.ended|^\W*(?:grammar|vocabulary|editing)\b", text, re.I)))
            name = None
            if heading or instr or kw:
                dt = dtext(i - 1, 4)
                name = (classify(text) if not instr else None) or classify(dt if instr else dtext(i, 3))
                if name is None and instr and re.match(r"\s*for\s+each\s+(of\s+the\s+)?questions?", text, re.I):
                    name = sec["name"] if sec and not sec["qs"] and (sec["name"] in ("Grammar MCQ", "Vocabulary MCQ") or (
                        sec["name"] in MCQ_SECS and sec["passage"] is not None)) \
                        else ("Grammar MCQ" if paper["mcq_blocks"] == 0 else "Vocabulary MCQ" if paper["mcq_blocks"] == 1 else "MCQ")
                    if name == "MCQ": MCQ_SECS.add("MCQ")
            if name:
                ref_only = name == "Comprehension OE" and bool(re.search(r"page \d+ of booklet a", dt, re.I)) \
                    and not re.search(r"passage below when", dt, re.I)
                a_new = re.search(r"questions?\s*(?:from\s*)?(\d{1,2})\s*(?:to|tc|-|–)\s*(\d{1,2})", dt, re.I)
                a_new = int(a_new.group(1)) if a_new else None
                same = sec and sec["name"] == name and (not sec["qs"] or a_new is None or a_new == sec["a"]) and sec["page"] >= page - 3
                if same:  # the heading and its instruction line, or a header repeated on the next page
                    rg2 = re.search(r"questions?\s*(?:from\s*)?(\d{1,2})\s*(?:to|tc|-|–|and)\s*(\d{1,2})|numbered\s*(\d{1,2})\s*(?:to|tc|-)\s*(\d{1,2})", dt, re.I)
                    if rg2 and not sec["a"]:
                        g = [x for x in rg2.groups() if x]; a, b = int(g[0]), int(g[1])
                        if a <= b <= a + 40: sec["a"], sec["b"] = a, b; sec["nexp"] = sec["nexp"] or b - a + 1
                    if sec["total"] is None and sec["nxm"] is None:
                        nx = re.search(r"(\d{1,2})\s*[x×*]\s*\W{0,2}\s*(\d{1,2})\s*marks?", dt, re.I)
                        tt = re.search(r"\(\s*(\d{1,3})\s*marks\s*\)", dt, re.I)
                        if nx: sec["nxm"] = (int(nx.group(1)), int(nx.group(2)))
                        elif tt: sec["total"] = int(tt.group(1))
                    ps = sec["passage"]
                    if re.match(r"\s*for\s+each\s+questions?", text, re.I) and ps is not None and not sec["qs"] \
                            and (len(ps["text"].split("\n")) >= 6 or any(o is ps for o, _, _ in segs)):
                        switch(None, l["top"]); st["passage"] = None; st["q"] = None  # the passage is over: questions follow
                else:
                    switch(None, l["top"])
                    if name in ("Grammar MCQ", "Vocabulary MCQ", "MCQ"): paper["mcq_blocks"] += 1
                    start_section(name, dt, page, ref_only)
                    st["q"] = None
                    switch(st["passage"], l["top"])
                continue
            # ---- blanks of a cloze or editing passage are questions
            if sec and sec["name"] in BLANK_SECS and st["passage"] is not None:
                for bm in BLANK.finditer(text):
                    n = int(bm.group(1))
                    lo = sec["first"]; hi = lo + sec["nexp"] - 1 if sec["nexp"] else None
                    last_b = sec["qs"][-1]["qno"] if sec["qs"] else lo - 1
                    if n > last_b and n >= lo and (n <= hi if hi else n <= last_b + 3):
                        snip = text
                        if sec["name"] == "Editing" and re.fullmatch(r"[\s()\d|]*", text) and i >= 2: snip = c[i - 2]["text"] + " " + text
                        new_question(n, page, [], snip)
                continue
            last = paper["last_q"]
            exp = sec["a"] if sec and not sec["qs"] and sec["a"] and last < sec["a"] else last + 1
            reading = st["passage"] is not None and owner is st["passage"] and not (sec and sec["qs"])
            at_col = l["left"] <= min_left + 0.04 * W
            qno = None; flag = []
            if isq and at_col:
                n = int(m.group(1))
                ok = n == exp if reading else (last < n <= last + 3 or n == exp or (n == 1 and not last))
                if ok: qno = n
            if qno is None and at_col and not reading and sec and sec["name"] not in BLANK_SECS:
                mt = QCONF.match(text)
                if mt and len(text.split()) >= 3 and mt.group(1) != str(exp) and conf_match(mt.group(1), exp):
                    qno = exp; flag = ["qno_ocr"]
            if qno is None and st["opt4"] is not None and not isq and sec and sec["name"] in MCQ_SECS and not reading \
                    and not text.lstrip().startswith("(") and len(l["words"]) >= 4 and l["left"] < st["opt4"] + 40 \
                    and (STEM.match(text) or re.match(r"\s*[\"“'‘|A-Z]", text)) and not FOOTER.search(text) and not INSTR.match(text):
                qno = exp; flag = ["qno_inferred"]
            if qno is not None:
                if sec is None:  # no heading or instruction read: start a section from the question
                    switch(None, l["top"])
                    name = "Grammar MCQ" if paper["mcq_blocks"] == 0 else "Vocabulary MCQ"
                    paper["mcq_blocks"] += 1
                    sec = start_section(name, "", page, False)
                switch(None, l["top"])
                st["q"] = new_question(qno, page, flag)
                owner = st["q"]; seg_top = l["top"]; st["opt4"] = None
            if re.match(r"\s*\(\s*4\s*\)", text): st["opt4"] = l["left"]
        switch(None, 0.955 * H)
        # the page's lines go to their owners
        for o, y0, y1 in segs:
            if o is None: continue
            seg_lines = [l for l in c if y0 <= l["top"] < y1 and not TRAILER.search(l["text"])]
            if not seg_lines: continue
            if page not in o["pages"]: o["pages"].append(page)
            o["text"] += ("\n" if o["text"] else "") + "\n".join(l["text"] for l in seg_lines)
            if "_marks" in o:
                for mm in MARK_RX.finditer("\n".join(l["text"] for l in seg_lines)):
                    o["_marks"].append(mark_value(mm.group(0)))
                    if mm.group(1) in "Ss": o["_guess"] = True
            if img is None: img = np.asarray(Image.open(pdir / f"p{page:04d}.jpg").convert("L"))
            box = None if os.environ.get("PP_NOFIG") else figure_box(img, words, lines, y0 - 5, y1 - 5, W)
            if box:
                crop = cdir / f"{o['id']}-p{page:04d}.png"
                Image.fromarray(img[box[1]:box[3], box[0]:box[2]]).save(crop, optimize=True)
                o["figures"].append({"page": page, "bbox": box, "crop": str(crop)})
        # the open question/passage at the end of the page carries over to the next
        st["q"] = owner if owner in questions else None

    # ---- link answers-section questions to passages that sit elsewhere (the OE passage is in Booklet A)
    for q in questions:
        if q["passage"] is None:
            ps = next((p for p in passages if p["paper"] == q["paper"] and p["qrange"] and p["qrange"][0] <= q["qno"] <= p["qrange"][1]), None)
            if ps and ps["section"] == q["section"]: q["passage"] = ps["id"]; ps["questions"].append(q["id"])
    # ---- blanks the OCR did not read ("(48)" printed in a box): the passage says how many there are
    for p in papers:
        for sec in p["sections"]:
            if sec["name"] in BLANK_SECS and sec["nexp"]:
                have = {q["qno"] for q in sec["qs"]}
                for n in range(sec["first"], sec["first"] + sec["nexp"]):
                    if n not in have:
                        q = {"id": f"{subject[:3]}-{year}-{p['n']:03d}-{(p['part'] or 'x').replace(' ', '').replace('/', '')}-q{n:02d}",
                             "subject": subject, "year": year, "paper": p["paper_id"], "school": p["school"], "exam": p["exam"],
                             "part": p["part"], "section": sec["name"], "passage": sec["passage"]["id"], "qno": n, "format": None,
                             "marks": None, "marks_source": None, "pages": [], "text": "", "figures": [],
                             "flags": ["blank_not_read"], "syllabus": None, "_marks": [], "_sec": sec}
                        questions.append(q); sec["qs"].append(q); sec["passage"]["questions"].append(q["id"])
                sec["qs"].sort(key=lambda q: q["qno"])
    qby = {q["id"]: q["qno"] for q in questions}
    for ps in passages:
        if ps["qrange"] is None and ps["questions"]: ps["qrange"] = [min(qby[i] for i in ps["questions"]), max(qby[i] for i in ps["questions"])]
    order = {(p["paper_id"], id(sec)): (i, j) for i, p in enumerate(papers) for j, sec in enumerate(p["sections"])}
    questions.sort(key=lambda q: (order.get((q["paper"], id(q["_sec"])), (999, 999)), q["qno"]))
    # ---- format and marks
    for p in papers:
        for sec in p["sections"]:
            sq = sec["qs"]
            if sec["name"] in TOTAL_ONLY or not sq: sec["per"] = None; sec["per_source"] = None; continue
            n, per, src = len(sq), None, None
            nx, tot = sec["nxm"], sec["total"]
            d = DEFAULT_PER.get(sec["name"])
            if nx and (d is None or nx[1] == d) and nx[0] == n: per, src = nx[1], "section instruction"
            elif tot and tot % n == 0 and tot // n <= 5 and (d is None or tot // n == d): per, src = tot // n, "section instruction"
            elif d: per, src = d, "PSLE format (section marks unreadable or not matching)"
            sec["per"], sec["per_source"] = per, src
    for q in questions:
        sec = q.pop("_sec")
        opts = set(OPTION.findall(q["text"])) | {"1" for _ in re.findall(r"\(\s*[lI|]\s*\)", q["text"])}
        sname = q["section"]
        q["format"] = "mcq" if (sname in MCQ_SECS and len(opts) >= 2) or (len(opts) >= 3 and sname not in BLANK_SECS) \
            else "structured" if re.search(r"\(a\).*\(b\)", q["text"], re.S) and sname == "Comprehension OE" else "open"
        raw = q.pop("_marks")
        if sname in BLANK_SECS or q["format"] == "mcq": raw = []
        known = [v for v in raw if isinstance(v, int)]
        if raw and known: q["marks"], q["marks_source"] = sum(known), "printed"
        elif sec and sec.get("per"): q["marks"], q["marks_source"] = sec["per"], sec["per_source"]
        elif raw: q["flags"].append("marks_ocr_unreadable")
        if q.pop("_guess", None) and q["marks_source"] == "printed": q["flags"].append("marks_guessed")
        if q["marks"] is None: q["flags"].append("marks_unknown")
        q["_s"] = sec
        if not q["text"].strip(): q["flags"].append("no_text")
        if sname in BLANK_SECS: q["flags"] = [f for f in q["flags"] if not f.startswith("qno_gap")]  # missing blanks are placeholders
    for p in papers:  # OE: one question without readable marks takes what is left of the section total
        for sec in p["sections"]:
            sq = sec["qs"]; tot = sec["total"]
            if sec["name"] in TOTAL_ONLY and tot and sq:
                missing = [q for q in sq if q["marks"] is None]
                got = sum(q["marks"] or 0 for q in sq)
                if len(missing) == 1 and 0 < tot - got <= 6:
                    missing[0]["marks"], missing[0]["marks_source"] = tot - got, "section total minus printed marks"
                    missing[0]["flags"] = [f for f in missing[0]["flags"] if f not in ("marks_unknown", "marks_ocr_unreadable")]
    for q in questions: q.pop("_s", None)
    for p in papers:
        p["questions"] = sum(q["paper"] == p["paper_id"] for q in questions)
        p["sections"] = [{"name": s["name"], "page": s["page"], "qrange": [s["qs"][0]["qno"], s["qs"][-1]["qno"]] if s["qs"] else None,
                          "instruction_range": [s["a"], s["b"]] if s["a"] else None, "total_marks": s["total"] or (s["nxm"][0] * s["nxm"][1] if s["nxm"] else None),
                          "found": len(s["qs"]), "marks_found": sum(q["marks"] or 0 for q in s["qs"]),
                          "passage": s["passage"]["id"] if s["passage"] else None} for s in p["sections"]]
        p["cover_marks"] = sorted(set(p["cover_marks"]))
        for k in ("n", "last_q", "part", "in_answers", "mcq_blocks", "qcol_"): p.pop(k, None)
    for name, rows in (("papers", papers), ("questions", questions), ("passages", passages)):
        with open(base / f"{name}.jsonl", "w") as f:
            for r in rows: f.write(json.dumps(r, ensure_ascii=False) + "\n")
    s = {"subject": subject, "year": year, "pages": len(pages), "page_kinds": kinds, "papers": len(papers),
         "papers_school_guessed": sum(p["school_guessed"] for p in papers),
         "questions": len(questions), "passages": len(passages), "mcq": sum(q["format"] == "mcq" for q in questions),
         "with_marks": sum(q["marks"] is not None for q in questions),
         "with_figure": sum(bool(q["figures"]) for q in questions),
         "qno_gaps": sum(any(f.startswith("qno_gap") for f in q["flags"]) for q in questions)}
    json.dump(s, open(base / "summary.json", "w"), indent=1)
    return s


def selftest():
    assert classify("Section E: Grammar Cloze (10 x 1 mark)") == "Grammar Cloze"
    assert classify("There are 10 blanks, numbered 26 to 35, in the passage below") == "Grammar Cloze"
    assert classify("Section F: Editing for Spelling and Grammar") == "Editing"
    assert classify("Fill in each blank with a suitable word. (15 marks)") == "Comprehension Cloze"
    assert classify("Section C: Vocabulary Cloze (5 x 1 mark)") == "Vocabulary Cloze"
    assert classify("choose the word closest in meaning to the underlined word") == "Vocabulary Cloze"
    assert classify("Section B: Vocabulary (5 x 1 mark)") == "Vocabulary MCQ"
    assert classify("Study the poster (Text 1) and the extract from an article (Text 2) and answer questions 21 to 25.") == "Visual Text"
    assert classify("Section I: Comprehension (Open-ended) 20 marks") == "Comprehension OE"
    assert classify("Refer to the passage below when you answer questions 66 to 75 in Booklet B.") == "Comprehension OE"
    assert classify("Section H: Transformation / Synthesis (5 x 2 marks)") == "Synthesis"
    assert eng_part_of("PAPER 1 (WRITING) (QUESTION BOOKLET)") == "Paper 1"
    assert eng_part_of("ENGLISH LANGUAGE PAPER 2 (BOOKLET A)") == "Paper 2/Booklet A"
    assert eng_part_of("ENGLISH LANGUAGE Booklet B") == "Booklet B"
    assert conf_match("41", 11) and conf_match("i", 1) and not conf_match("I", 1) and not conf_match("21", 11)
    assert mark_value("[2m]") == 2 and mark_value("[im]") == 1 and mark_value("[Sm]") == 3 and mark_value("{2m]") == 2
    assert mark_value("[Sry]") == 3 and mark_value("(4)") is None and mark_value("[7]") is None and mark_value("[ ]") is None
    assert [int(mark_value(x.group(0))) for x in MARK_RX.finditer("tick [| the answer. [1m] and [2m]")] == [1, 2]
    assert QSTART.match("21 Which of the following").group(1) == "21" and not QSTART.match("(26) the diaphragm")
    assert QSTART.match("66 From paragraph 1").group(1) == "66" and QSTART.match("1. Sam and").group(1) == "1"
    assert BLANK.findall("(39) (40)") == ["39", "40"]
    assert TRAILER.search("You may now go on to Booklet B.")
    print("english selftest ok")
