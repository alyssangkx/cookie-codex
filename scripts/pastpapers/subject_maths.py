"""Step A for the Maths papers: page, section, question and marks rules.

catalogue.py does the OCR and calls catalogue_pdf() here for subject "maths". The shared pieces (TSV reading, cover
fields, figure crops) are imported from catalogue.py; every rule about how a maths paper is laid out lives here, so
this subject can be refined without touching the others.
ponytail: started as a copy of the shared rules (Science-tuned); the copies diverge as each subject is piloted.
"""
import difflib, json, os, re

from catalogue import (OUT, OPTION, P6, EXAMWORD, COVERWORD, SCHOOLWORD, INDEX_PAGE, WATERMARK, content, exam_of, figure_box, npages, page_range, part_of, read_tsv, school_key, school_of)

OCRDIGIT = str.maketrans({"G": "6", "S": "5", "O": "0", "o": "0", "l": "1", "I": "1", "|": "1", "B": "8", "Z": "2"})
NUMTOK = re.compile(r"[\s“”\"'‘’]*(?:[a-z]{1,3}[\s.]+)?Q?\s*([0-9A-Za-z|]{1,3})\s*[.．、)]?\s+(?=\S)")


def fuzzy_qno(text, expected):
    """True if the leading token of `text` is a misread of the number `expected`. Tesseract reads "1" as "4" or "7"
    ("44." for 11, "4G" for 16, "42" for 12) but numbering is strictly sequential, so the expected number decides."""
    m = NUMTOK.match(text)
    if not m: return False
    tok, exp = m.group(1).translate(OCRDIGIT), str(expected)
    ok = lambda t: len(t) == len(exp) and t.isdigit() and all(a == b or (b == "1" and a in "47") for a, b in zip(t, exp))
    return ok(tok) or (len(tok) == len(exp) + 1 and (ok(tok[1:]) or ok(tok[:-1])))  # "222" for 22: a stray mark next to the number


ANSWER_TITLE = re.compile(r"answer\s*key|^\s*answers?\s*$|marking\s*scheme|suggested\s*answers?|答案", re.I)

QSTART = re.compile(r"^\s*Q?\s*(\d{1,2})(?:\s*[.．、),]|\s+|$)")  # "12 ...", "12. ...", "Q12"; never "(12)"

STEM = re.compile(r"\s*(?:[^\w\s(]{1,2}\s*)*[A-Z][a-z]+\b")  # maths stems start with any capitalised word ("Arrange", "Express", a name)

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


EXAM2 = re.compile(r"exam|assessment|prelim|review|revision|practice|\btest\b|\bterm\b|\bsa\s*[12]\b|semestral", re.I)
PAPERLINE = re.compile(r"\bpaper\s*[1lI2t]\b|\bbooklet\s*[ABab]\b", re.I)
MATHWORD = re.compile(r"mathematics|\bmaths?\b", re.I)
ANS_HDR = re.compile(r"simplified\s*ans|answer\s*key|marking\s*scheme|suggested\s*(?:answers?|solutions?)|worked\s*solutions?|level\s*:?\s*primary", re.I)
FORM_LINE = re.compile(r"^\W*(?:\w{1,3}\s+)?(name|class)\b", re.I)
SCHOOL_NAMES = [  # canonical names of the schools that recur in the compilations; an OCR'd cover name is snapped to the closest
    "Tao Nan School", "Anglo-Chinese School (Junior)", "Anglo-Chinese School (Primary)", "Anglo-Chinese School (Barker Road)",
    "Catholic High School (Primary)", "CHIJ St Nicholas Girls' School (Primary)", "CHIJ Primary (Toa Payoh)", "CHIJ Katong Primary",
    "Nan Hua Primary School", "Ai Tong School", "Methodist Girls' School (Primary)", "Raffles Girls' Primary School",
    "Red Swastika School", "Nanyang Primary School", "Henry Park Primary School", "St Hilda's Primary School",
    "Rulang Primary School", "Singapore Chinese Girls' School (Primary)", "Nan Chiau Primary School", "Rosyth School",
    "Paya Lebar Methodist Girls' School (Primary)", "Pei Hwa Presbyterian Primary School", "Pei Chun Public School",
    "Maha Bodhi School", "Mee Toh School", "Kong Hwa School", "Poi Ching School", "Chongfu School", "Gongshang Primary School",
    "Fairfield Methodist School (Primary)", "Temasek Primary School", "Holy Innocents' Primary School", "Admiralty Primary School",
    "Rivervale Primary School", "Qifa Primary School", "Tampines Primary School", "St Joseph's Institution Junior",
    "Opera Estate Primary School", "Anderson Primary School", "Anglo-Chinese School (Independent)", "Princess Elizabeth Primary School",
    "Zhonghua Primary School", "Hong Wen School", "Jiemin Primary School", "Greendale Primary School", "Canberra Primary School",
]


def canon_school(name, strict=False):
    """Snap an OCR'd school name ("Anglo-Ghinese Srhoul (Junior)") to the closest known school; keep it as read if none is close."""
    if not name: return name
    def key(x):  # the name words only: drop "(Junior)", "Primary", and any word that is a misread "School" ("Srhoul")
        x = re.sub(r"\([^)]*\)?", " ", x.lower())
        ws = [w for w in re.findall(r"[a-z0-9]+", x) if w not in ("primary", "pri", "sch") and difflib.SequenceMatcher(None, w, "school").ratio() < 0.6]
        return "".join(ws)
    k = key(name)
    paren = re.search(r"\(([^)]*)\)", name)
    best, score = None, 0
    for cand in SCHOOL_NAMES:
        ck = key(cand)
        r = difflib.SequenceMatcher(None, k, ck).ratio()
        pc = re.search(r"\(([^)]*)\)", cand)
        if pc and paren and difflib.SequenceMatcher(None, pc.group(1).lower(), paren.group(1).lower()).ratio() < 0.4: r -= 0.15  # (Junior) is not (Primary)
        if r > score: best, score = cand, r
    return best if score >= 0.78 else (None if strict else name)


def cover_part(blk):
    """Part from the cover's own title lines. "Paper 1 comprises 2 booklets, A and B" and "PRACTICE PAPER 2" are not part titles."""
    paper = booklet = None
    for l in blk[:16]:
        t = l["text"]
        m = re.match(r"^\W*(?:\w{1,3}\s+)?(?:mathematics\s+)?paper\s*([12lIt])\b(.*)$", t, re.I)
        if m and not re.match(r"\s*comprises", m.group(2), re.I):
            paper = paper or ("2" if m.group(1) == "2" else "1")
        if paper != "2" and not re.search(r"comprises|booklets\b|and\s*B\b|A\s*&\s*B", t, re.I):
            mb = re.search(r"booklet\s*([AB])\b", t, re.I)
            if mb: booklet = booklet or mb.group(1).upper()
    if paper == "2": return "Paper 2"
    if booklet: return f"Paper 1/Booklet {booklet}"
    return "Paper 1" if paper else None


def cover_cut(c, H):
    """Is this page a cover? Returns None if not, else the index of the first content line after the cover block
    (len(c) for a pure cover; smaller where the first questions share the page, as in the Nan Hua papers)."""
    nopts = len({m for l in c for m in re.findall(r"^\s*\(\s*([1-4])\s*\)", l["text"])})
    hdr = " ".join(l["text"] for l in c[:10])
    t14 = " ".join(l["text"] for l in c[:14])
    form = len({m.lower() for m in re.findall(r"\bname\b|\bclass\b|\bdate\b|duration|total\s*marks|parent", t14, re.I)}) >= 2  # two of the form labels
    title = bool(P6.search(hdr) or MATHWORD.search(hdr)) and bool(EXAM2.search(hdr) or PAPERLINE.search(hdr))
    ctext = " ".join(l["text"] for l in c)
    evidence = form or any(SCHOOLWORD.search(l["text"]) for l in c[:3]) or bool(re.search(r"instructions|do not (?:turn|open)|total\s*(?:time|marks)|duration|parent", ctext, re.I))
    if not title and re.search(r"\bname\b", t14, re.I) and nopts == 0 and sum(len(re.findall(r"\w", re.split(r"\s+(?:Name|Class|Date)\b", l["text"])[0])) <= 4 for l in c[:14]) >= 8:
        return len(c)  # a logo-only cover (RPS): the repeated logo is OCR'd as "RPS RPS RPS", only "Name : ( )" is readable
    if not title or not (form or (PAPERLINE.search(hdr) and evidence)): return None
    for i, l in enumerate(c):  # a cover that also holds the first questions: "Questions 19 to 30 carry 2 marks each" then "19", "20" in the number column
        m = re.match(r"\s*\w{0,2}\s*questions?\s*(\d{1,2})\s*\w{1,3}\s*(\d{1,2})", l["text"], re.I)
        if i >= 3 and m:
            for j in range(i + 1, len(c)):
                if fuzzy_qno(c[j]["text"], int(m.group(1))) or re.match(rf"\W*{m.group(1)}(?:\W|$)", c[j]["text"]): return j
    if nopts < 3: return len(c) if len(c) < 90 else None  # the back of a cover is often OCR noise: many short lines
    for i, l in enumerate(c):  # questions share the page: the cover block ends where the instructions or the first stem start
        if i >= 3 and (re.match(r"\s*questions?\s*\d", l["text"], re.I) or (QSTART.match(l["text"]) and len(l["words"]) >= 4)): return i
    return None


def page_kind(lines, H, pageno):
    text = " ".join(l["text"] for l in lines)
    if pageno <= 2 and INDEX_PAGE.search(text): return "index"
    c = content(lines, H)
    if len(c) <= 1: return "blank"
    for l in c[:6]:  # "P6 STANDARD PRELIM 2026 - SIMPLIFIED ANS", "YEAR : 2026 / LEVEL : PRIMARY 6", "Mass Review - Answer Key"
        if ANS_HDR.search(l["text"]) and not re.search(r"optical|sheet|write|shade", l["text"], re.I): return "answers"
    if cover_cut(c, H) is not None: return "cover"
    for l in c[:3]:  # "Nanyang Primary School P6 SCIENCE Prelim 2024 Suggested Answers"
        if re.search(r"suggested\s*answers?|answer\s*key|marking\s*scheme", l["text"], re.I): return "answers"
    for l in c[:6]:
        title = len(l["text"].split()) <= 5 and len(re.sub(r"\s", "", l["text"])) <= 30  # a heading, not an instruction
        if title and ANSWER_TITLE.search(l["text"]) and not re.search(r"optical|sheet", l["text"], re.I):
            return "answers"
    # a key table packs several "Q1 Q2 Q3" on a line; question pages number stems "12." not "Q12"
    qtok = [len(re.findall(r"(?<![\w])Q\s?\d{1,2}(?![\w])", re.sub(r"Q\s?\d{1,2}\s*[-—–~]+\s*Q?\s?\d{1,2}", "", l["text"])))
            for l in lines]
    if sum(n >= 2 for n in qtok) >= 2 or sum(qtok) >= 15: return "answers"
    if any(re.match(r"\s*Question\s+\d{1,2}\b", l["text"]) for l in c[:3]) and any(re.match(r"\s*(?:Method|Step\s*1)\b", l["text"]) for l in c): return "answers"  # "Question 7 Time taken to print... Method: ..."
    if sum(bool(re.match(r"\s*Q\d{1,2}\s*[|:]\s*\S", l["text"])) for l in c) >= 2: return "answers"  # worked-solution pages: "Q24 | From F, move ..."
    if re.search(r"optical\s*answer\s*sheet", " ".join(l["text"] for l in c if l["top"] < 0.5 * H), re.I) and len(c) < 15: return "oas"
    return "content"


def catalogue_pdf(job):
    import numpy as np
    from PIL import Image
    subject, year, pdf, pages_spec = job
    base = OUT / subject / str(year); pdir = base / "pages"; cdir = base / "crops"; cdir.mkdir(exist_ok=True)
    pages = [p for p in page_range(pages_spec, npages(pdf)) if (pdir / f"p{p:04d}.tsv").exists()]
    papers, questions, kinds = [], [], {}
    paper = None; section = None; open_q = None; opt4 = None; ans_seen = False; ref_left = 0

    def new_question(qno, page, line):
        nonlocal open_q
        flags = []
        last = paper["last_q"]
        if last and qno != last + 1: flags.append(f"qno_gap_after_{last}")
        paper["last_q"] = qno
        paper["questions_seen"] += 1
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
            for w in read_tsv(mpath)[2]:  # a margin token only counts when it equals the expected next number (checked where the lines are walked)
                if re.fullmatch(r"Q?[0-9A-Za-z|]{1,3}\.?", w["text"]):
                    near = [l for l in c if abs(l["top"] - w["top"]) < 60 and l["left"] > w["right"]]
                    if near: min(near, key=lambda l: abs(l["top"] - w["top"])).setdefault("mtoks", []).append(w["text"].rstrip(".").lstrip("Q"))
        if kind == "cover":
            cut = cover_cut(c, H)
            blk = c[:cut]
            text = " ".join(l["text"] for l in blk)
            school, guessed = school_of(blk, H)
            for i in range(min(5, len(blk))):  # "Augls-Chinese Srhoul | (Primary) | A Methodist Institution": the known school wins over the first "School"-like line
                hit = canon_school(blk[i]["text"] + (" " + blk[i + 1]["text"] if i + 1 < len(blk) and blk[i + 1]["text"].lstrip().startswith(("(", "{")) else ""), strict=True)
                if hit: school, guessed = hit, False; break
            if school and (mm := re.search(r"^(.*?\bschool\b(?:\s*\([^)]*\))?)", school, re.I)): school = mm.group(1)  # drop OCR junk after the name
            school = canon_school(school) if school else school
            if guessed and school and (P6.search(school) or EXAM2.search(school)): school = None  # the "school" line was the exam title
            exam, part = exam_of(text), cover_part(blk)
            if not exam and re.search(r"practice|revision|test", text, re.I): exam = "Practice"
            title = " ".join(l["text"] for l in blk[:10] if EXAM2.search(l["text"]) and not FORM_LINE.match(l["text"]))
            tkey = (re.sub(r"[^a-z0-9 ]", "", re.sub(r"paper\s*\w|booklets?\s*\w|primary\s*\w|mathematics|school|\(.*?\)", "", title.lower())).strip(),
                    "".join(re.findall(r"\d", re.sub(r"paper\s*\w|booklets?\s*\w|primary\s*\w|20\d\d", "", title.lower()))))
            # Maths papers run Paper 1 Booklet A -> Booklet B -> Paper 2, one school after another. A cover whose part ranks
            # above the current paper's latest part is the next part of the same paper; a cover that does not starts a new
            # paper (single-booklet weighted assessments have no part, so every cover is a paper).
            rank = lambda p: 0 if not p else 3 if "Paper 2" in p else 2 if "Booklet B" in p else 1
            compat = bool(paper) and (not school or not paper["school"] or guessed or paper["school_guessed"]
                                      or difflib.SequenceMatcher(None, school_key(school), school_key(paper["school"])).ratio() >= 0.6)
            r_new, inferred = rank(part), False
            if part is None or part == "Paper 1":  # part not readable: it is the next one after the current paper's latest
                pr = paper["rank"] if paper else 0
                if paper and compat and (1 <= pr <= 2 or (pr == 0 and paper["tkey"] == tkey and paper["questions_seen"])):
                    r_new, inferred = (2 if pr == 0 else pr + 1), True
                    if pr == 0:  # the first cover's part was unreadable (logo): it was Booklet A
                        paper["part"] = "Paper 1/Booklet A"; paper["parts"][0] = "Paper 1/Booklet A"; paper["rank"] = 1
                        for q in questions:
                            if q["paper"] == paper["paper_id"] and q["part"] is None:
                                q["part"] = "Paper 1/Booklet A"; q["id"] = q["id"].replace("-x-", "-Paper1BookletA-")
                        paper["flags"].append("part_inferred_Paper 1/Booklet A"); r_new = 2
                    part = {1: "Paper 1/Booklet A", 2: "Paper 1/Booklet B", 3: "Paper 2"}[r_new]
                elif part == "Paper 1": r_new = 1
            same = bool(paper and compat and r_new and r_new > paper["rank"] and (paper["rank"] >= 1 or (paper["tkey"] == tkey and paper["questions_seen"])))
            if same:
                paper["parts"].append(part); paper["part"] = part; paper["rank"] = r_new
                if inferred: paper["flags"].append(f"part_inferred_{part}")
                if guessed is False and (paper["school_guessed"] or "school" in (school or "").lower() and "school" not in (paper["school"] or "").lower()):
                    paper["school"], paper["school_guessed"] = school, False
            else:
                paper = {"n": len(papers) + 1, "paper_id": f"{subject[:3]}-{year}-{len(papers) + 1:03d}", "subject": subject,
                         "year": year, "school": school, "school_guessed": guessed, "exam": exam, "part": part, "rank": r_new,
                         "title": re.sub(r"\s+", " ", title).strip()[:80], "tkey": tkey, "questions_seen": 0, "flags": [],
                         "parts": [part], "first_page": page, "last_page": page, "answer_pages": [], "last_q": 0,
                         "sec_marks": [], "file": pdf.name}
                papers.append(paper)
            section = None; open_q = None; paper["in_answers"] = False; opt4 = None; ans_seen = False
            if part and paper["last_q"] and "Paper 2" in part: paper["last_q"] = 0  # Paper 2 restarts at 1
            if cut == len(c): continue  # a pure cover carries only instructions ("1. Do not turn over...", never Q1)
            c = c[cut:]; kind = "content"  # the first questions share the page with the cover
        if kind == "oas" and any(re.match(r"\s*\(\s*[1-4]\s*\)", l["text"]) or QSTART.match(l["text"]) for l in c[1:]): kind = "content"  # instructions + first questions on one page
        if paper is None or kind in ("index", "blank", "oas"): continue
        paper["last_page"] = page
        # a key runs until the next cover ("Q33 | a) ..." lines look like questions but are answers)
        opt_page = len({m for l in c for m in re.findall(r"^\s*\(\s*([1-4])\s*\)", l["text"])}) >= 3
        if paper.get("in_answers") and kind == "content" and opt_page:
            paper = {"n": len(papers) + 1, "paper_id": f"{subject[:3]}-{year}-{len(papers) + 1:03d}", "subject": subject,
                     "year": year, "school": None, "school_guessed": True, "exam": None, "part": "Paper 1/Booklet A", "rank": 1,
                     "title": "", "tkey": ("", ""), "questions_seen": 0, "flags": ["no_cover_part_assumed_booklet_A"], "parts": ["Paper 1/Booklet A"],
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
                # "(60 marks)" over Paper 2 Q6-15 is a total, not a per-question mark: those carry printed [n]
                if per and per == int(per) and per <= 5 and (rx is SEC_MARKS[0] or "Paper" not in (paper["part"] or "")):
                    paper["sec_marks"].append((a, b, int(per), paper["part"]))
        if paper["part"] and not paper["part"].endswith(("Booklet A", "Paper 2")) and not any(q["paper"] == paper["paper_id"] and q["part"] == paper["part"] for q in questions[-60:]):  # Booklet A and Paper 2 start at 1
            mi = re.search(r"questions?\s*(\d{1,2})\s*(?:to|-|\w{1,2})\s*(\d{1,2})\s*car", page_text, re.I)  # the part's first page says where its numbering starts: "Questions 19 to 30"
            if mi and 1 <= int(mi.group(1)) <= 40 and int(mi.group(2)) > int(mi.group(1)): paper["last_q"] = int(mi.group(1)) - 1
        img = None
        # the question-number column: the leftmost line that starts with a number (scans shift left/right,
        # and footers sit further left than the numbers, so the page's leftmost line is no guide)
        def plausible(l):  # a line that can be a question start here: its number is in the next few of the sequence
            mm = QSTART.match(l["text"]); lq = paper["last_q"]
            return bool(mm) and (lq < int(mm.group(1)) <= lq + 10 or (lq == 0 and int(mm.group(1)) == 1) or fuzzy_qno(l["text"], lq + 1))
        min_left = min((l["left"] for l in c if plausible(l) and l["left"] < 0.35 * W and l["top"] > 0.06 * H), default=0)  # not the page-number sticker at the very top, not a stray "6 (2) 60" option
        if not min_left: min_left = min((l["left"] for l in c if QSTART.match(l["text"]) and l["left"] < 0.35 * W and l["top"] > 0.06 * H), default=0)
        starts = []  # (line index, kind, value): kind q | qi (inferred number) | cont | section | part
        nstarts = 0
        for i, l in enumerate(c):
            if len(starts) != nstarts:  # a question just started: remember its stem column, and that no Ans line is seen yet
                nstarts = len(starts)
                if starts[-1][1] in ("q", "qi"):
                    j = starts[-1][0]; ans_seen = False
                    ws = [w for k in (j, j + 1) if k < len(c) for w in c[k]["words"] if not re.fullmatch(r"\D{0,2}\d{1,2}\.?", w["text"])]
                    ref_left = ws[0]["left"] if ws else c[j]["left"]  # the stem text column, not the number box
            if re.match(r"\W*(?:\w{1,2}\s+)?Ans\b", l["text"]) or re.search(r"\[\s*\d\s*\]\s*$", l["text"]): ans_seen = True
            mc = re.match(r"\s*continued?\s*(?:from|of)\s*question\s*(\d{1,2})", l["text"], re.I)
            if mc:
                starts.append((i, "cont", int(mc.group(1)))); continue
            m = QSTART.match(l["text"])
            if re.match(r"\s*\(\s*4\s*\)", l["text"]) or (opt4 is None and re.match(r"\s*[\(\{]\s*3\s*[\)\}]", l["text"])):  # (3) is enough: (4) is often lost in a figure or by OCR
                opt4 = l["left"]
            elif opt4 is not None and not m and subject != "chinese" and not l["text"].lstrip().startswith("(") \
                    and len(l["words"]) >= 4 and l["left"] < opt4 + 40 and STEM.match(l["text"]) \
                    and not FOOTER.search(l["text"]):
                # an MCQ ended at option (4) and a stem starts at the stem column with no number read:
                # the next question (ponytail: inferred, flagged; step B confirms the number)
                last = paper["last_q"] if not any(s[1] in ("q", "qi") for s in starts) else [s for s in starts if s[1] in ("q", "qi")][-1][2]
                starts.append((i, "qi", last + 1)); opt4 = None; continue
            if ans_seen and not m and not (paper["part"] or "").endswith("Booklet A") and not l["text"].lstrip().startswith("(") \
                    and len(l["words"]) >= 4 and abs(l["left"] - ref_left) < 70 and STEM.match(l["text"]) and not FOOTER.search(l["text"]) \
                    and not re.match(r"\W*(?:\w{1,2}\s+)?Ans\b", l["text"]):
                # a stem right after the previous question's Ans line, in the same column, with its number unreadable
                last = ([s for s in starts if s[1] in ("q", "qi")] or [(0, 0, paper["last_q"])])[-1][2]
                starts.append((i, "qi", last + 1)); opt4 = None; continue
            if not m and l["left"] <= min_left + 0.04 * W and re.match(r"[^\w\s(]\s*[.,]\s+[A-Z][a-z]+", l["text"]) and not any(s_[1] in ("section", "part") for s_ in starts[-1:]):
                # "@. The figure ..." : the number was read as a symbol; numbering is sequential, so it is the next one
                last = ([s_ for s_ in starts if s_[1] in ("q", "qi")] or [(0, 0, paper["last_q"])])[-1][2]
                starts.append((i, "qi", last + 1)); opt4 = None; continue
            short = len(l["text"].split()) <= 8 or (subject == "chinese" and len(l["text"]) <= 20)
            if not m and short:
                s = section_of(subject, l["text"])
                if s: starts.append((i, "section", s)); continue
                p = part_of(l["text"]) if len(l["text"]) < 40 else None
                if p: starts.append((i, "part", p)); continue
            if not m and not l["text"].lstrip().startswith("(") and not any(s[1] in ("section", "part") for s in starts[-1:]) \
                    and ((l["left"] <= min_left + 0.04 * W and fuzzy_qno(l["text"], ([s for s in starts if s[1] in ("q", "qi")] or [(0, 0, paper["last_q"])])[-1][2] + 1))
                         or any(fuzzy_qno(t + " x", ([s for s in starts if s[1] in ("q", "qi")] or [(0, 0, paper["last_q"])])[-1][2] + 1) for t in l.get("mtoks", []))):
                starts.append((i, "q", ([s for s in starts if s[1] in ("q", "qi")] or [(0, 0, paper["last_q"])])[-1][2] + 1)); opt4 = None; continue
            if not m or l["left"] > min_left + 0.04 * W: continue
            qs_ = [s for s in starts if s[1] in ("q", "qi")]
            qno = int(m.group(1)); last = qs_[-1][2] if qs_ else paper["last_q"]
            if qno != last + 1 and fuzzy_qno(l["text"], last + 1): qno = last + 1
            fresh = not last or any(s[1] in ("section", "part") for s in starts[-1:])
            if qs_ and qs_[-1][1] == "qi" and qno == qs_[-1][2]:  # the number turned up after all: drop the guess
                starts.remove(qs_[-1]); last = qno - 1
            if (last < qno <= last + 3 and (qno == last + 1 or len(l["words"]) >= 4)) or (qno == 1 and fresh) or (qno == last + 1):  # a skipped number needs a real stem line, not an axis label "10"
                starts.append((i, "q", qno)); opt4 = None
            elif (fresh or opt4 is not None) and re.match(r"\s*\d{1,2}\s+[A-Za-z]{3,}", l["text"]) and qno != last:
                # OCR misreads the number ("1" as "4", "14" as "44") but the numbering is strictly sequential, and
                # the previous question is closed (options (1)-(4) seen) or this follows a heading: take last+1
                starts.append((i, "qi", last + 1)); opt4 = None
        # walk the page: lines before the first start continue the open question
        cur = open_q; seg_top = c[0]["top"] if c else 0; segments = []
        for idx, (i, kind_, val) in enumerate(starts + [(len(c), "end", None)]):
            top = c[i]["top"] if i < len(c) else 0.955 * H
            if i < len(c) and kind_ in ("q", "qi") and re.fullmatch(r"\W*[0-9A-Za-z|]{1,3}\W?", c[i]["text"]):  # a number in its own box: the stem's first line can sit a hair above it
                above = [l["top"] for l in c if l is not c[i] and top - 0.014 * H < l["top"] < top and l["left"] > c[i]["right"]]
                if above: top = min(above)
            if cur is not None:
                segments.append((cur, seg_top, top))
            if kind_ == "section": section = val; cur = None
            elif kind_ == "part": paper["part"] = paper["part"] or val  # the cover decides the part, not a stray heading
            elif kind_ == "cont":
                cur = next((q for q in reversed(questions) if q["paper"] == paper["paper_id"] and q["qno"] == val), cur)
            elif kind_ in ("q", "qi") and paper["part"] == "Paper 2" and val > 15:
                pass  # a PSLE Paper 2 has 15 questions: what follows Q15 (an advert page, a stray number) continues Q15
            elif kind_ in ("q", "qi"):
                cur = new_question(val, page, c[i])
                if kind_ == "qi": cur["flags"].append("qno_inferred")
            seg_top = top
        open_q = cur
        for q, y0, y1 in segments:
            seg_lines = [l for l in c if y0 <= l["top"] < y1]
            if page not in q["pages"]: q["pages"].append(page)
            q["text"] += ("\n" if q["text"] else "") + "\n".join(l["text"] for l in seg_lines)
            for w in words:  # all words, not the content() lines: a mark alone on its line ("[1]") has one letter and content() drops it
                if not (y0 <= w["top"] < y1 and 0.045 * H < w["top"] < 0.955 * H) or w["left"] <= 0.55 * W: continue
                m = MARK_WORD.match(w["text"])
                if not m and re.fullmatch(r"\[\s*[tlI|!]\s*\]", w["text"]): q["_marks"].append(1); continue  # "[1]" read as "[t]"
                if m: q["_marks"].append(int(next(g for g in m.groups() if g)))
                else: q["_marks"] += [int(x) for x in re.findall(r"\[\s*(\d{1,2})\s*\]$", w["text"])]
            if os.environ.get("PP_NOCROP"): continue
            if img is None: img = np.asarray(Image.open(pdir / f"p{page:04d}.jpg").convert("L"))
            box = figure_box(img, words, lines, y0 - 5, y1 - 5, W)
            if box:
                crop = cdir / f"{q['id']}-p{page:04d}.png"
                Image.fromarray(img[box[1]:box[3], box[0]:box[2]]).save(crop, optimize=True)
                q["figures"].append({"page": page, "bbox": box, "crop": str(crop)})

    A15 = year == 2025 or year <= 2020  # the 2025 file (and, untested, 2018-2020) prints Booklet A Q1-15 and B Q16-30; the 2026 file A Q1-18, B Q19-30
    def psle_marks(part, qno):
        """The standard PSLE split when nothing printed says otherwise: A = Q1-18 (10x1 + 8x2), B = Q19-30 (2 each) in the 2026 file;
        A = Q1-15 (10x1 + 5x2), B = Q16-30 (5x1 + 10x2) in the 2025 file."""
        a_n = 15 if A15 else 18
        bare = part == "Paper 1"
        if (part.endswith("Booklet A") or bare) and qno <= a_n: return (1 if qno <= 10 else 2), f"PSLE format (Booklet A: Q1-10 = 1, Q11-{a_n} = 2)"
        if part.endswith("Booklet B") or bare:
            if A15 and 16 <= qno <= 30: return (1 if qno <= 20 else 2), "PSLE format (2025 Booklet B: Q16-20 = 1, Q21-30 = 2)"
            if not A15 and 19 <= qno <= 30: return 2, "PSLE format (Booklet B Q19-30 = 2)"
        return None, None

    for q in questions:
        opts = set(OPTION.findall(q["text"]))
        opts |= {"1" for _ in re.findall(r"\(\s*[lI|]\s*\)", q["text"])}
        part = q["part"] or ""
        a_n = 15 if A15 else 18
        if (part.endswith("Booklet A") or part == "Paper 1") and q["qno"] <= a_n: opts = {"1", "2", "3", "4"}  # Booklet A is all MCQ (options may sit in a figure)
        q["format"] = "mcq" if len(opts) >= 3 else "structured" if re.search(r"\(a\).*\(b\)", q["text"], re.S) else "open"
        booklet = part.endswith(("Booklet A", "Booklet B")) or part == "Paper 1"  # booklets print no per-question marks: use the section instruction
        if q["_marks"] and q["format"] != "mcq" and not booklet:  # in an MCQ, "(4)" at the right edge is an option, not marks
            q["marks"], q["marks_source"] = sum(q["_marks"]), "printed"
            parts = len(re.findall(r"^\W*(?:\w{1,2}\s+)?Ans\W{0,3}\(\w\)", q["text"], re.M))
            if parts > len(q["_marks"]): q["flags"].append("marks_partial")  # more (a)(b)(c) answer lines than printed marks read
            q.pop("_marks")
        else:
            q.pop("_marks")
            pap = next(p for p in papers if p["paper_id"] == q["paper"])
            hit = [per for a, b, per, pt in pap["sec_marks"] if a <= q["qno"] <= b and pt == q["part"]]
            if hit: q["marks"], q["marks_source"] = hit[-1], "section instruction"
            else:
                q["marks"], q["marks_source"] = psle_marks(part, q["qno"])
                if q["marks"] is None: q["flags"].append("marks_unknown")
        if not q["text"].strip(): q["flags"].append("no_text")
    for q in questions:  # the school printed on the first cover may be garbled; the paper's (best) name applies to all its questions
        q["school"] = next(p["school"] for p in papers if p["paper_id"] == q["paper"])
    for p in papers:
        p["questions"] = sum(q["paper"] == p["paper_id"] for q in questions)
        byp = {}
        for q in questions:
            if q["paper"] == p["paper_id"]: byp.setdefault(q["part"] or "-", []).append(q)
        p["marks_by_part"] = {k: {"questions": len(v), "marks": sum(q["marks"] or 0 for q in v), "unmarked": sum(q["marks"] is None for q in v)} for k, v in byp.items()}  # step B: a part whose marks fall short of its printed total lost a [n]
        for k in ("n", "last_q", "part", "in_answers", "rank", "tkey", "questions_seen"): p.pop(k, None)
        p["sec_marks"] = sorted(set(map(tuple, p["sec_marks"])), key=str)
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


def selftest():
    """Rules added for Maths (run: python3 -c 'import sys; sys.path.insert(0, "scripts/pastpapers"); import subject_maths as s; s.selftest()')."""
    assert QSTART.match("4 Thirty-five thousand") and not QSTART.match("(4) 350 107")
    assert MARK_WORD.match("[3]") and MARK_WORD.match("(2 marks)")
    assert SEC_MARKS[0].search("Questions 1 to 10 carry 1 mark each.")
    assert fuzzy_qno("44. In the number line", 11) and fuzzy_qno("4G 300 students", 16) and fuzzy_qno("42 Mdm Asmah", 12)
    assert fuzzy_qno("ao 27 The average", 27) and fuzzy_qno("\u201c2 Hariz has", 2) and not fuzzy_qno("3 kg 70g", 5)
    assert section_of("maths", "Short Answer Questions") == "Short Answer"
    assert canon_school("Anglo-Ghinese Srhoul (Junior)") == "Anglo-Chinese School (Junior)" and canon_school("TAONAN SCHOOL") == "Tao Nan School"
    assert canon_school("Anglo-Chinese Srhuul (Primary)") == "Anglo-Chinese School (Primary)"  # (Junior) and (Primary) are different schools
    assert cover_part([{"text": "2026 PRIMARY 6 PRACTICE PAPER 2"}, {"text": "Paper 1 comprises 2 booklets, A and B."}, {"text": "PAPER 1"}, {"text": "(BOOKLET A)"}]) == "Paper 1/Booklet A"
    assert cover_part([{"text": "MATHEMATICS PAPER 2"}]) == "Paper 2" and cover_part([{"text": "2026 WEIGHTED ASSESSMENT 1"}]) is None
    assert MARK_WORD.match("[1]") and re.fullmatch(r"\[\s*[tlI|!]\s*\]", "[t]")  # "[1]" read as "[t]" counts as 1
    assert QSTART.match("22, Rachel had") and not QSTART.match("(22) Rachel")
    assert ANS_HDR.search("YEAR : 2026 | LEVEL PRIMARY 6") and ANS_HDR.search("P6 STANDARD PRELIM 2026 - SIMPLIFIED ANS")
    assert STEM.match(": & Tie pie chart below") and STEM.match("Roy has 7 as much money")
    lines = lambda *t: [{"text": x, "words": x.split(), "left": 0, "top": i * 50, "right": 100, "bottom": i * 50 + 20} for i, x in enumerate(t)]
    cover = lines("Nan Hua Primary School", "Primary 6 Mathematics", "Timed Practice 1", "Name: ( ) Date:", "Class: Primary 6M Parent's Signature:", "Paper 1 Booklet A", "Questions 1 to 10 carry 1 mark each.", "1 Which of the following is seven hundred", "(1) 730012", "(2) 703012", "(3) 73012", "(4) 70312")
    assert cover_cut(cover, 3000) == 7  # the first question shares the cover page
    assert cover_cut(lines("2026 P6 Math Prelim Paper 2", "Page 3", "15 The figure is made up of", "Ans: cm"), 3000) is None  # a running header is not a cover
    print("subject_maths selftest ok")
