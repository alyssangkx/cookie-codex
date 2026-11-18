"""Step A for the Science papers: page, section, question and marks rules.

catalogue.py does the OCR and calls catalogue_pdf() here for subject "science". The shared pieces (TSV reading, cover
fields, figure crops) are imported from catalogue.py; every rule about how a science paper is laid out lives here, so
this subject can be refined without touching the others.
ponytail: started as a copy of the shared rules (Science-tuned); the copies diverge as each subject is piloted.
"""
import difflib, json, os, re

from catalogue import (OUT, OPTION, P6, EXAMWORD, COVERWORD, INDEX_PAGE, WATERMARK, content, exam_of, figure_box, npages, page_range, part_of, read_tsv, school_key, school_of)

ANSWER_TITLE = re.compile(r"answer\s*key|^\s*answers?\s*$|marking\s*scheme|suggested\s*answers?|答案", re.I)

SCORE_BOX = re.compile(r"(?:^|\s)score\W{0,3}(?:[^\w\s]\s*)?([1-9])\s*$", re.I)  # "Score 3" (the box's out-of mark)
PART_LABEL = re.compile(r"^\s*(?:[^\s(){}\[\]]{1,2}\s+)?[\(\{\[]\s*([a-h])\s*[\)\}\]]\s+\S")  # a margin glyph may precede: "¢ (a) Identify"
QSTART = re.compile(r"^\s*Q?\s*(\d{1,2})(?:\s*[.．、),]|\s+|$)")  # "12 ...", "12. ...", "Q12"; never "(12)"

STEM = re.compile(r"\s*(The|Which|What|Why|How|Study|Look|Refer|In|An?|Some|Two|Three|Four|Each|When|[A-Z][a-z]+ (?:placed|put|carried|wanted|set|conducted|used|had|has|filled|poured|tested|observed|measured|added|kept|left|prepared|investigated|made|built|connected))\b")

END_PAPER = re.compile(r"^\W*end\s+of\s+(?:the\s+)?(?:paper|test|examination|booklet\s*b)\W*$", re.I)
KEY_HEAD = re.compile(r"correction\s*template|suggested\s*answers?|\bQn\s+Ans\b|answer\s*key|marking\s*scheme", re.I)
KEY_LINE = re.compile(r"^\W*\d{1,2}\s?[a-h]\W*$")
def exam_sig(text):
    """"Term 1 Weighted Assessment", "WA2", "SA1": what tells two tests of one school apart."""
    m = re.findall(r"(?:term\s*\d|\bwa\s*\d|\bsa\s*\d|\bca\s*\d|weighted\s*assessment\s*\d|bite-?sized\s*\d)", text, re.I)
    return tuple(sorted({re.sub(r"\s+", "", x).lower() for x in m}))


FOOTER = re.compile(r"examination|\bexam\b|prelim|page\s*\d|go on|continue|turn over|booklet|school|\b20\d\d\b", re.I)

MARK_WORD = re.compile(r"^\[\s*(\d{1,2})\s*(?:m|mk|mks|marks?)?\s*\]$|^\(\s*(\d{1,2})\s*(?:m|mk|mks|marks?)\s*\)$|^\[(\d{1,2})$|^(\d{1,2})\]$", re.I)

SEC_MARKS = [
    re.compile(r"questions?\s*(\d{1,2})\s*(?:to|-|–)\s*(\d{1,2})\s*(?:carry|carries)\s*(\d)\s*marks?\s*each", re.I | re.S),
    re.compile(r"(?:questions?|from)\s*(\d{1,2})\s*(?:to|-|–)\s*(\d{1,2}).{0,300}?\((\d{1,3})\s*marks?\)", re.I | re.S),
]

SECTIONS = {'science': [('multiple[- ]?choice', 'MCQ'), ('open[- ]?ended', 'Open-ended')]}


def section_of(subject, text):
    t = re.sub(r"\s+", "" if subject == "chinese" else " ", text)
    for pat, name in SECTIONS.get(subject, []):
        if re.search(pat, t, re.I): return name
    return None


EXAMWORD = re.compile(EXAMWORD.pattern + r"|practice|mid-?year|term\s*\d|bite-?sized|class\s*test|topical", re.I)  # local widening


def page_kind(lines, H, pageno):
    text = " ".join(l["text"] for l in lines)
    if pageno <= 2 and INDEX_PAGE.search(text): return "index"
    c = content(lines, H)
    if len(c) <= 1: return "blank"
    top = " ".join(l["text"] for l in c if l["top"] < 0.5 * H)
    nopts = len({m for l in c for m in re.findall(r"^\s*\(\s*([1-4])\s*\)", l["text"])})
    if any(re.search(r"answers?\s*(for|to)\s*(booklet|paper|section)", l["text"], re.I) for l in c[:8]) and nopts < 3:
        return "answers"  # a handwritten key page: "Answers for Booklet B"
    head = " ".join(l["text"] for l in c[:5])
    if KEY_HEAD.search(head) and nopts < 3: return "answers"  # a "Correction Template", "Suggested answer" or "Qn Ans" key sheet
    if sum(bool(KEY_LINE.match(l["text"])) for l in c) >= 4 and nopts < 3: return "answers"  # handwritten key: "32c", "33a" ... one per line
    if P6.search(top) and EXAMWORD.search(top) and COVERWORD.search(text): return "cover"
    if re.search(r"\bname\b", top, re.I) and re.search(r"\bclass\b", top, re.I) \
            and re.search(r"date|time|duration|marks|instruction|booklet", top, re.I) and nopts < 3:
        return "cover"
    if nopts < 3 and any(len(l["text"].split()) <= 4 and re.search(r"^\W*booklet\s*[AB]\W*$", l["text"], re.I) and l["top"] < 0.6 * H
                         for l in c) and re.search(r"\bname\b|instruction|index number", text, re.I) and len(c) < 40:
        return "cover"  # "(BOOKLET A)" title block with Name / instructions, when "Primary 6" is printed lower down
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


INSTR = re.compile(r"write your name|do not turn|do not open|follow all|answer all|use (a )?2b|optical answer|number of marks|"
                   r"index number|spaces? provided|in the bracket|shade (your|its)|instructions? to|this booklet|"
                   r"booklet [ab]\b|marks? (is|are) shown|read (the )?instructions|invigilator", re.I)


CONFUSED = {frozenset(x) for x in ("17", "38", "56", "69", "35", "28", "08", "49")}


def num_near(qno, exp):
    """OCR damaged the number: "3." for 31, "1." for 31, "4" for 1 (a one-digit slip)."""
    a, b = str(qno), str(exp)
    if a == b: return True
    if len(b) == 2 and len(a) == 1: return b.startswith(a) or b.endswith(a)
    if len(a) == len(b) == 1: return frozenset((a, b)) in CONFUSED
    if len(a) == len(b): return sum(x != y for x, y in zip(a, b)) == 1 and frozenset((a[0], b[0])) in CONFUSED | {frozenset((a[0],))} or a[0] == b[0] and frozenset((a[1], b[1])) in CONFUSED
    return False


BR_OPEN, BR_CLOSE = r"[\[\(\{\|!lI:;]", r"[\]\)\}\|!lI]"
MARK_END = re.compile(r"(?:^|\s)(" + BR_OPEN + r"?)\s*(\d{1,2})\s*(" + BR_CLOSE + r"?)\s*[.:]?$")


ONE_LIKE = "1iIl|!tfj"  # glyphs OCR gives for a printed 1 inside a bracket: "[i}", "{ft}", "(im)", "i]"
TAIL_JUNK = r"[\s|=_~.,;:'\"`\u2018\u2019\u201c\u201d-]*"


def _digit(g):
    if g.isdigit(): return int(g) if g != "0" else None
    return 1 if g and all(ch in ONE_LIKE for ch in g) and len(g) <= 2 else None


def mark_value(text):
    """The [n] printed at the end of a line: OCR reads [1] as [71], 11], {1}, [i}, {ft}, (im), (2] ...; -> n or None.
    Trailing junk after the bracket ("[1] |", "[1] =") is ignored."""
    t = re.sub(TAIL_JUNK + r"$", "", text.strip()) if re.search(r"[\]\)\}\|]\W*$", text.strip()) else text.strip().rstrip(".").strip()
    w = re.search(r"[\[\(\{]\s*([1-9" + ONE_LIKE + r"]{1,2})\s*(?:m|mk|mks|marks?)\s*[\]\)\}]$", t, re.I)  # "(1m)" "[2 marks]" "(im)"
    if w and _digit(w.group(1)): return _digit(w.group(1))
    m = re.search(r"(?:^|\s)([\[\(\{\|!lI:;]?)\s*([0-9" + ONE_LIKE + r"]{1,2})\s*([\]\)\}\|!lI]?)\s*[.:]?$", t)
    if not m or not (m.group(1) or m.group(3)): return None
    if not m.group(3) and not re.match(r"[\[\(\{]", m.group(1)): return None
    if not m.group(1) and m.group(3) not in "])}": return None
    d = m.group(2)
    if len(d) == 2:  # "[71]" "11]" "[11" : the bracket was read as a digit
        if d[0] in "17" + ONE_LIKE and d[1] in "123456" + ONE_LIKE: d = d[1]
        elif d[0] in ONE_LIKE and d[1] in ONE_LIKE: d = "1"
        else: return None
    v = _digit(d)
    return v if v and 1 <= v <= 9 else None


def line_marks(l, W):
    """A line's printed marks: only a mark token at the right end of the line counts (never an option '(4)')."""
    t = l["text"].strip()
    if re.match(r"\s*\(\s*[1-4]\s*\)", t) and l["right"] < 0.7 * W: return None
    return mark_value(t)


def digit_is_one(img, w):
    """OCR often reads a printed "[1]" (a 1 with a foot serif) as "[4]" or "[14]". The ink of a printed 1 is a third
    as wide as it is tall (0.29-0.35) and a 2, 3, 4 is about half (0.47-0.54): measure the first ink blob after the
    opening bracket. True when the glyph is as thin as a 1."""
    import numpy as np
    c = np.asarray(img.crop((max(0, w["left"] - 4), max(0, w["top"] - 4), w["right"] + 4, w["bottom"] + 4)))
    if c.size == 0 or w["bottom"] - w["top"] < 20: return True  # cannot measure: a part is almost never 4 or 7 marks
    ink = c < min(150, c.mean() - 30)
    cols = np.flatnonzero(np.diff(np.concatenate(([0], (ink.sum(0) > 0).astype(int), [0]))))
    runs = list(zip(cols[0::2], cols[1::2]))
    return len(runs) < 3 or (runs[1][1] - runs[1][0]) / (w["bottom"] - w["top"]) < 0.43


FUZZY_NO = re.compile(r"^\W{0,2}([A-Za-z0-9|]{1,3})[.,]\s+(?=[A-Z(])")


def fuzzy_tok(tok, exp):
    """OCR read the number token "o3." for 33 ("|0" for 10, "l2" for 12): same length, no digit that disagrees."""
    e = str(exp)
    if tok.isdigit() or len(tok) != len(e) or len(tok) > 2: return False
    ok = [t == d for t, d in zip(tok, e)]
    bad = [t for t, d in zip(tok, e) if t != d]
    return any(ok) and all(not b.isdigit() for b in bad)


def cover_has_q1(c, H, n=1):
    """Q1 is printed on a short test's cover. The numbered instructions ("1. Write your name ...") are not Q1: a real
    Q1 line is not an instruction and has a (1)-(4) option line or an (a) part below it."""
    for i, l in enumerate(c):
        m = QSTART.match(l["text"])
        if not (m and int(m.group(1)) == n and l["top"] > 0.2 * H) or INSTR.search(l["text"]): continue
        if n > 1 and len(l["words"]) >= 5: return True  # a booklet starting at Q14: its number was announced on the cover
        below = c[i + 1:]
        if sum(bool(re.match(r"\s*\(\s*[1-4l]\s*\)", b["text"])) for b in below) >= 2 \
                or any(re.match(r"\s*\(\s*a\s*\)", b["text"], re.I) for b in below): return True
    return False


def catalogue_pdf(job):
    import numpy as np
    from PIL import Image
    subject, year, pdf, pages_spec = job
    base = OUT / subject / str(year); pdir = base / "pages"; cdir = base / "crops"; cdir.mkdir(exist_ok=True)
    pages = [p for p in page_range(pages_spec, npages(pdf)) if (pdir / f"p{p:04d}.tsv").exists()]
    papers, questions, kinds = [], [], {}
    paper = None; section = None; open_q = None; opt4 = None; open_parts = set()

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
        end_top = None  # "End of paper": whatever follows (printed answers, a corrections sheet) is not a question
        if kind == "content" and paper is not None:
            for l in c:
                if END_PAPER.match(l["text"]): end_top = l["top"]; break
            if end_top is not None: c = [l for l in c if l["top"] <= end_top]
        # catalogue.content() drops lines with fewer than 2 letters/digits, which loses every lone "[1]" mark token
        # that OCR set on a line of its own at the right margin: keep those for the marks only
        cid = {id(l) for l in c}
        lone = [l for l in lines if id(l) not in cid and (end_top is None or l["top"] < end_top) and 0.045 * H < l["top"] < 0.955 * H and len(l["text"]) <= 8
                and l["left"] > 0.5 * W and mark_value(l["text"])]
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
            for l in c:  # the title line decides: "BOOKLET 8" (a B) over a score-table row "Booklet A 60" further down
                tm = re.match(r"^\W*booklet\s*([AB8])\W*$", l["text"], re.I)
                if tm and l["top"] < 0.6 * H: part = "Booklet A" if tm.group(1).upper() == "A" else "Booklet B"; break
            sim = difflib.SequenceMatcher(None, school_key(school), school_key(paper["school"])).ratio() if paper else 0
            # a Booklet B / Paper 2 cover right after this paper's A / 1 is the same paper even when OCR garbles the
            # school name ("Auglo-Chinese Srhoal"); only a clearly different name starts a new one
            follows = bool(paper and part and re.search(r"Booklet B|Paper 2", part) and (exam == paper["exam"] or not exam)
                           and not any(re.search(r"Booklet B|Paper 2", x or "") for x in paper["parts"]))  # a 2nd B cover is another paper
            same = paper and (sim >= 0.75 or (follows and sim >= 0.4))
            if paper and not same and guessed and not exam and not part and not paper.get("in_answers"):
                same = True; part = "Booklet B" if re.search(r"Booklet A", paper["part"] or "") else paper["part"]  # a bare "Name: / Class:" page with no school, exam or booklet: a booklet's first page, not a new paper
            # the same school's next paper (Term 1 then Term 2, WA1 then WA2, a second practice paper) restarts at a
            # Booklet A / Paper 1 / single-booklet cover once this one has questions or an answer key
            continues = bool(same and not follows and not paper.get("in_answers") and paper.get("sig") and exam_sig(text) == paper["sig"]
                             and not re.search(r"Booklet A|Paper 1", part or ""))  # the same WA's second booklet (Section A, then Section B)
            if same and not follows and not continues and (paper.get("in_answers") or paper["last_q"]) \
                    and (re.search(r"Booklet A|Paper 1", part or "") or (part is None and not guessed)):
                same = False
            if same:
                paper["parts"].append(part); paper["part"] = part
                if not paper.get("sig"): paper["sig"] = exam_sig(text)
            else:
                paper = {"n": len(papers) + 1, "paper_id": f"{subject[:3]}-{year}-{len(papers) + 1:03d}", "subject": subject,
                         "year": year, "school": school, "school_guessed": guessed, "exam": exam, "part": part,
                         "parts": [part], "first_page": page, "last_page": page, "answer_pages": [], "last_q": 0,
                         "sec_marks": [], "file": pdf.name, "sig": exam_sig(text)}
                papers.append(paper)
            section = None; open_q = None; paper["in_answers"] = False; opt4 = None
            if part and paper["last_q"] and re.search(r"paper", part, re.I): paper["last_q"] = 0  # Paper 2 restarts at 1
            qr = re.search(r"questions?\s*(\d{1,2})\s*(?:to|-|–)\s*(\d{1,2}),?\s*(?:write|answer|you)", text, re.I)
            if qr and not paper["last_q"] and 1 < int(qr.group(1)) <= 40 and int(qr.group(2)) > int(qr.group(1)):
                paper["last_q"] = int(qr.group(1)) - 1  # the cover itself says "Section B ... For Questions 14 to 17"
            if not cover_has_q1(c, H, paper["last_q"] + 1 if qr and paper["last_q"] else 1):
                continue  # else Q1 is printed on the cover (short tests): read the page as content too
        if paper is None or kind in ("index", "blank", "oas"): continue
        # a key runs until the next cover ("Q33 | a) ..." lines look like questions but are answers)
        opt_page = len({m for l in c for m in re.findall(r"^\s*\(\s*([1-4])\s*\)", l["text"])}) >= 3
        has_q1 = any((m := QSTART.match(l["text"])) and int(m.group(1)) == 1 and l["left"] < 0.35 * W for l in c)
        if paper.get("in_answers") and kind == "content" and opt_page and has_q1:
            paper = {"n": len(papers) + 1, "paper_id": f"{subject[:3]}-{year}-{len(papers) + 1:03d}", "subject": subject,
                     "year": year, "school": None, "school_guessed": True, "exam": None, "part": None, "parts": [None],
                     "first_page": page, "last_page": page, "answer_pages": [], "last_q": 0, "sec_marks": [],
                     "file": pdf.name, "no_cover": True}
            papers.append(paper); section = None; open_q = None; opt4 = None
        paper["last_page"] = page  # after the cover-less split above, so the old paper keeps its own last page
        if kind == "answers" or paper.get("in_answers"):
            paper["answer_pages"].append(page); paper["in_answers"] = True; open_q = None
            continue
        page_text = "\n".join(l["text"] for l in c)
        for tm in re.finditer(r"\(\s*(\d{2,3})\s*marks?\s*\)", page_text, re.I):  # "(44 marks)" under a booklet title
            if 20 <= int(tm.group(1)) <= 100: paper.setdefault("printed_totals", []).append(int(tm.group(1)))
        qr = re.search(r"questions?\s*(\d{1,2})\s*(?:to|-|–)\s*(\d{1,2}),?\s*(?:write|answer|you)", page_text, re.I)
        if qr and not paper["last_q"] and 1 < int(qr.group(1)) <= 40 and int(qr.group(2)) > int(qr.group(1)):
            paper["last_q"] = int(qr.group(1)) - 1  # a booklet that starts at Q14 ("Section B ... For Questions 14 to 17")
        for rx in SEC_MARKS:
            for m in rx.finditer(page_text):
                a, b, v = map(int, m.groups())
                per = v if rx is SEC_MARKS[0] else (v / (b - a + 1) if b >= a else 0)
                if per and per == int(per) and per <= 5: paper["sec_marks"].append((a, b, int(per)))
        img = None
        # the question-number column: the leftmost line that starts with a number (scans shift left/right,
        # and footers sit further left than the numbers, so the page's leftmost line is no guide)
        def _qleft(l):
            m_ = QSTART.match(l["text"])
            return bool(m_) and l["left"] < 0.35 * W and paper["last_q"] < int(m_.group(1)) <= paper["last_q"] + 4
        min_left = min((l["left"] for l in c if _qleft(l)), default=None)
        if min_left is None:  # no expected number on this page: fall back to any numbered line
            min_left = min((l["left"] for l in c if QSTART.match(l["text"]) and l["left"] < 0.35 * W), default=0)
        starts_misread = set()
        for l in c:  # "BPRS: 30 Asher conducted ..." : watermark noise glued in front of the number we expect next
            m = re.match(r"^\W*[A-Za-z]{2,5}\W{0,2}\s+(\d{1,2})[.,]?\s+([A-Z][a-z])", l["text"])
            if m and paper["last_q"] and int(m.group(1)) == paper["last_q"] + 1 and not QSTART.match(l["text"]):
                l["text"] = l["text"][m.start(1):]
        starts = []  # (line index, kind, value): kind q | qi (inferred number) | cont | section | part
        pp = set(open_parts)  # part labels (a) (b) ... seen in the open question
        for i, l in enumerate(c):
            pl = PART_LABEL.match(l["text"])
            if pl and pl.group(1) == "a" and "a" in pp and "b" in pp and (paper["last_q"] >= 28 or "B" in (paper["part"] or "")):
                # "(a)" again after (a) and (b): a new question whose number OCR lost. Its stem starts after the last
                # marked line (the end of the previous question's last part), or at the top of the page.
                last_i = max((x[0] for x in starts if x[1] in ("q", "qi")), default=-1)
                j = i - 1
                while j > last_i and mark_value(c[j]["text"]) is None: j -= 1
                b = j + 1 if j > last_i else (0 if last_i < 0 else None)
                while b is not None and b < i and re.match(r"\W*(score|go on|continued?)\b|^\W*\d{0,2}\W*$", c[b]["text"], re.I): b += 1
                if b is not None and b < i:
                    qs0 = [x for x in starts if x[1] in ("q", "qi")]
                    starts.append((b, "qi", (qs0[-1][2] if qs0 else paper["last_q"]) + 1)); starts_misread.add(-b - 1)
                    pp = set()
            if pl: pp.add(pl.group(1))
            mc = re.match(r"\s*continued?\s*(?:from|of)\s*question\s*(\d{1,2})", l["text"], re.I)
            if mc:
                starts.append((i, "cont", int(mc.group(1)))); continue
            if not QSTART.match(l["text"]) and l["left"] < 0.3 * W and (fm := FUZZY_NO.match(l["text"])):
                qs0 = [x for x in starts if x[1] in ("q", "qi")]
                exp0 = (qs0[-1][2] if qs0 else paper["last_q"]) + 1
                if fuzzy_tok(fm.group(1), exp0):
                    l["text"] = f"{exp0}. " + l["text"][fm.end():]
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
            if not m or l["left"] > (min_left or 0.25 * W) + 0.04 * W: continue
            qs_ = [s for s in starts if s[1] in ("q", "qi")]
            qno = int(m.group(1)); last = qs_[-1][2] if qs_ else paper["last_q"]
            fresh = not last or any(s[1] in ("section", "part") for s in starts[-1:])
            if qs_ and qs_[-1][1] == "qi" and qno == qs_[-1][2]:  # the number turned up after all: drop the guess
                starts.remove(qs_[-1]); last = qno - 1
            if last < qno <= last + 3 or (qno == 1 and fresh) or (qno == last + 1):
                starts.append((i, "q", qno)); opt4 = None; pp = set()
            elif (opt4 is not None or fresh or num_near(qno, last + 1)) and STEM.match(QSTART.sub("", l["text"], 1)) and not FOOTER.search(l["text"]):
                # a stem right after the previous MCQ's option (4) (or at the paper start) whose number OCR misread
                # ("4 The table ..." for Q1): it is the next question; step B confirms the number
                starts.append((i, "qi", last + 1)); opt4 = None; pp = set()
                starts_misread.add(i)
            elif not last and not qs_ and 1 < qno <= 45 and len(l["words"]) >= 5 and not FOOTER.search(l["text"]) \
                    and not INSTR.search(l["text"]):
                # a booklet whose first question is not 1 (a Booklet B on its own, or a cover-less excerpt); the first
                # question of a Booklet A is 1 whatever OCR printed ("4 Jia Hao wanted ..." is Q1)
                first_a = bool(re.search(r"Booklet A|Paper 1", paper["part"] or ""))
                starts.append((i, "qi", 1 if first_a else qno)); opt4 = None; starts_misread.add(i); pp = set()
        open_parts = pp
        starts.sort(key=lambda x: x[0])
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
                if i in starts_misread: cur["flags"].append("qno_misread")
                if -i - 1 in starts_misread: cur["flags"].append("qno_split_at_part_a")
            seg_top = top
        open_q = cur
        ptoks = []  # (question, index in its _marks) of every mark token read on this page
        for q, y0, y1 in segments:
            seg_lines = [l for l in c if y0 <= l["top"] < y1]
            if page not in q["pages"]: q["pages"].append(page)
            q["text"] += ("\n" if q["text"] else "") + "\n".join(l["text"] for l in seg_lines)
            if img is None: img = np.asarray(Image.open(pdir / f"p{page:04d}.jpg").convert("L"))
            for l in seg_lines + [x for x in lone if y0 <= x["top"] < y1]:
                v = line_marks(l, W)
                if v in (4, 7) and digit_is_one(Image.fromarray(img), l["words"][-1]):
                    v = 1; q["flags"].append("mark_4_read_as_1")
                if v: q["_marks"].append(v); ptoks.append((q, len(q["_marks"]) - 1))
            box = None if os.environ.get("SCI_NOCROP") or os.environ.get("PP_NOCROP") else figure_box(img, words, lines, y0 - 5, y1 - 5, W)
            if box:
                crop = cdir / f"{q['id']}-p{page:04d}.png"
                Image.fromarray(img[box[1]:box[3], box[0]:box[2]]).save(crop, optimize=True)
                q["figures"].append({"page": page, "bbox": box, "crop": str(crop)})

        if end_top is not None: paper["in_answers"] = True; open_q = None  # the pages after "End of paper" are a key or a stray sheet
        # The printed "Score N" box at the foot of a Booklet B page is the page's total marks: use it to repair the page's tokens
        sc = next((int(m_.group(1)) for l in c[-6:] if (m_ := SCORE_BOX.match(l["text"]))), None)
        in_b = bool(segments) and not re.search(r"Booklet A|Paper 1", paper["part"] or "")
        if sc and in_b and segments:
            owners = {id(q): q for q, _, _ in segments}
            tot = sum(q["_marks"][k] for q, k in ptoks)
            if not ptoks and len(owners) == 1:  # no bracket read at all on a page of one question
                q = next(iter(owners.values())); q["_marks"].append(sc); q["flags"].append("marks_from_score_box")
            elif ptoks and tot != sc:
                fixes = [(j, nv) for j, (q, k) in enumerate(ptoks) for nv in range(1, 7)
                         if nv != q["_marks"][k] and tot - q["_marks"][k] + nv == sc]
                one = {j for j, _ in fixes}
                if len(one) == 1 and len(fixes) == 1:
                    q, k = ptoks[fixes[0][0]]; q["_marks"][k] = fixes[0][1]; q["flags"].append("marks_fixed_by_score_box")
                else:
                    for q in owners.values(): q["flags"].append("marks_page_mismatch")

    amax = {}  # last Booklet A question per paper: its instruction "Questions 1 to 28 ... (56 marks)", else the printed A total
    for p in papers:
        lim = [b for a, b, per in p["sec_marks"] if a == 1 and per == 2]
        tots = p.get("printed_totals") or []
        amax[p["paper_id"]] = max(lim) if lim else 28 if 56 in tots else 30 if 60 in tots else 30
    for q in questions:
        if (q["part"] or "").endswith("Booklet A") and q["qno"] > amax[q["paper"]]:
            q["part"] = "Booklet B"; q["flags"].append("part_b_by_number")  # Booklet A ends at amax; its B cover was not found yet
        opts = set(OPTION.findall(q["text"]))
        opts |= {"1" for _ in re.findall(r"\(\s*[lI|]\s*\)", q["text"])}
        in_a = (q["part"] or "").endswith("Booklet A")  # Booklet A is all MCQ: 1-28 in 2024, 1-30 in 2026
        if subject == "science" and in_a and (q["qno"] <= amax[q["paper"]] and not re.search(r"\(\s*a\s*\)", q["text"][:400])): opts = {"1", "2", "3", "4"}
        q["format"] = "mcq" if len(opts) >= 3 else "structured" if re.search(r"\(a\).*\(b\)", q["text"], re.S) else "open"
        if q["_marks"] and q["format"] != "mcq":  # in an MCQ, "(4)" at the right edge is an option, not marks
            q["marks"], q["marks_source"] = sum(q.pop("_marks")), "printed"
            if q["marks"] > 12: q["flags"].append("marks_suspect")  # a merged question or a misread bracket
        else:
            q.pop("_marks")
            pap = next(p for p in papers if p["paper_id"] == q["paper"])
            hit = [per for a, b, per in pap["sec_marks"] if a <= q["qno"] <= b]
            if hit: q["marks"], q["marks_source"] = hit[-1], "section instruction"
            elif subject == "science" and q["format"] == "mcq" and q["qno"] <= amax[q["paper"]]:
                q["marks"], q["marks_source"] = 2, "PSLE format (Booklet A MCQ = 2)"
            else: q["flags"].append("marks_unknown")
        if not q["text"].strip(): q["flags"].append("no_text")
    for p in papers:
        p["questions"] = sum(q["paper"] == p["paper_id"] for q in questions)
        for k in ("n", "last_q", "part", "in_answers", "sig"): p.pop(k, None)
        p["sec_marks"] = sorted(set(map(tuple, p["sec_marks"])))
        p["marks_sum"] = sum(q["marks"] or 0 for q in questions if q["paper"] == p["paper_id"])
        # step B's cheap check: Booklet B's marks add up to the printed total (44 in 2024, 40 in 2026; the cover or a
        # "(44 marks)" under the booklet title, else the year's convention for a Prelim with a Booklet B)
        bq = [q for q in questions if q["paper"] == p["paper_id"] and (q["part"] or "").endswith(("Booklet B", "Paper 2"))]
        p["marks_sum_b"] = sum(q["marks"] or 0 for q in bq)
        tots = [t for t in p.get("printed_totals", []) if t <= 50]
        if tots and bq:
            p["printed_total"], p["printed_total_source"] = max(set(tots), key=tots.count), "printed"
        elif bq and p.get("exam") == "Prelim" and year in (2024, 2026):
            p["printed_total"], p["printed_total_source"] = {2024: 44, 2026: 40}[year], "convention"
        else:
            p["printed_total"], p["printed_total_source"] = None, None
        p["marks_b_ok"] = (p["marks_sum_b"] == p["printed_total"]) if p["printed_total"] else None
        p["no_questions"] = p["questions"] == 0  # e.g. a corrections template or a stray answer sheet
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
    """Rules added by the Science lead; run: python3 -c "import subject_science; subject_science.selftest()"."""
    mv = mark_value
    assert mv("Give a reason. [71]") == 1 and mv("properly. 11]") == 1 and mv("to reduce D. {1}") == 1
    assert mv("Why? :2}") == 2 and mv("Name Y. (2]") == 2 and mv("(b) Explain [2") == 2 and mv("rate (1m)") == 1
    assert mv("In 2019 the value was 12") is None and mv("x 12 [") is None and mv("a heading") is None
    assert num_near(3, 31) and num_near(1, 31) and not num_near(5, 31) and num_near(7, 1) and not num_near(2, 1)
    assert fuzzy_tok("o3", 33) and fuzzy_tok("l2", 12) and not fuzzy_tok("33", 33) and not fuzzy_tok("x4", 33)
    assert QSTART.match("38, Zemin conducted") and QSTART.match("12. The") and not QSTART.match("(12) The")
    assert PART_LABEL.match("{c} Explain why") and PART_LABEL.match("(a) State two") and not PART_LABEL.match("(1) mass")
    assert SCORE_BOX.search("Continued on page 32 Score 3") and not SCORE_BOX.search("Your score out of 100")
    mk = lambda t, top=900: {"text": t, "top": top, "left": 300, "right": 900, "bottom": top + 40, "words": []}
    instr = [mk("1. Write your name, class and index number in the spaces provided", 1800), mk("above.", 1880),
             mk("2. Do not turn over this page until you are told to do so.", 1950)]
    assert not cover_has_q1(instr, 3510)  # numbered instructions are not Q1
    q1 = [mk("Section A"), mk("1. The diagram below shows how living things are grouped.", 1100), mk("(1) K is a reptile.", 1900),
          mk("(2) L is a fish.", 1950), mk("(3) M is a bird.", 2000)]
    assert cover_has_q1(q1, 3510)  # Q1 printed on a short test's cover
    assert INSTR.search("Write your name and index number")
    # round 2
    assert mv("x [i}") == 1 and mv("x {ft}") == 1 and mv("a (im)") == 1 and mv("b i]") == 1 and mv("c [1] |") == 1 and mv("d [1] =") == 1
    assert mv("Q: 2 cm = 5") is None and mv("In 2019 the value was 12") is None
    assert END_PAPER.match("End of Paper") and END_PAPER.match("*** END OF PAPER ***") and not END_PAPER.match("End of Booklet A")
    assert KEY_HEAD.search("P6 Preliminary Science 2026 Correction Template") and KEY_HEAD.search("Qn Ans Qn Ans") and KEY_LINE.match("32c")
    assert PART_LABEL.match("¢ (a) Identify the following") and PART_LABEL.match("3 {b) Bird G also") and not PART_LABEL.match("(1) mass")
    assert exam_sig("2026 Term 1 Weighted Assessment") == ("term1",) and exam_sig("Term 2 WA") != exam_sig("Term 1 WA")
    from PIL import Image, ImageDraw
    def tok(digit_w):  # "[d]" 30 px high: bracket stems 6 px wide, digit blob digit_w wide
        im = Image.new("L", (90, 50), 255); d = ImageDraw.Draw(im)
        d.rectangle([10, 8, 16, 38], fill=0); d.rectangle([66, 8, 72, 38], fill=0); d.rectangle([30, 10, 30 + digit_w, 36], fill=0)
        return im, {"left": 6, "top": 4, "right": 76, "bottom": 42}
    assert digit_is_one(*tok(9)) and not digit_is_one(*tok(22))
    import reocr_pages
    ws = [{"text": "HPPS", "left": 45, "right": 117, "top": 10 * i, "bottom": 10 * i + 8, "conf": 90} for i in range(30)] + \
         [{"text": "HPPS", "left": 2247, "right": 2313, "top": 10 * i, "bottom": 10 * i + 8, "conf": 90} for i in range(30)]
    assert reocr_pages.stamp_columns(ws, 2483) == [117, 2247] and reocr_pages.stamp_columns(ws[:5], 2483) == [None, None]
    print("subject_science selftest ok")
