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
import difflib, json, os, re, sys
from pathlib import Path

from catalogue import (OUT, OPTION, P6, SCHOOLWORD, INDEX_PAGE, content, clean, exam_of, figure_box,
                       npages, page_range, part_of, read_tsv, school_key)

ZQ = re.compile(r"^\s*Q\s?(\d{1,2})(?!\d)")
NUMERAL = "一二三四五六七八九十"
SEC_MARKS = re.compile(r"(\d{1,2})题(\d{1,3})分")
Q_RANGE = re.compile(r"Q\s?(\d{1,2})\s*[-—–~至一]+\s*[Q@]?\s?(\d{1,2})")
SECTION_KEYS = [(r"语文应|文应用", "语文应用"), (r"短文.?[填空室撤盾真]|文填|短文(?=.{0,3}\d?题)", "短文填空"), (r"完成对|成对话", "完成对话"),
                (r"阅读理|读理解", "阅读理解")]
PASSAGE_SECTIONS = {"短文填空", "阅读理解一", "阅读理解二", "完成对话"}
INLINE = {"短文填空": (5, "mcq", 16), "完成对话": (4, "match", 26)}  # questions sit inside the passage: "Q16 (1.. 2.. 3.. 4..)", "Q26。"
# the fixed P6 Paper 2 layout, used only when a heading's own "(N题M分)" is unreadable
GROUP_TOTALS = [(30, 33, 10), (34, 40, 22)]
DEFAULT_MARKS = [(1, 15, 2), (16, 20, 2), (21, 25, 2), (26, 29, 2), (30, 32, 2)]  # Q30-32: the A组 MCQs
LABEL_ANSWER = re.compile(r"ANSWER.{0,25}BOOKLET|^作答[簿薄筹筑]|作答[簿薄筹筑]$")
LABEL_QUESTION = re.compile(r"QUESTION.{0,25}BOOKLET|^问题[簿卷]")
CN_SCHOOL = re.compile(r"[一-鿿]{2,}?(?:小学|学校|女校|附小|中学|华小)(?:[(（][一-鿿]{1,4}[)）])?")
EXAM_CN = re.compile(r"考试|预考|预试|测验|评估|考查|练习|复习|学段|PRELIM|EXAM|ASSESS|EXERCISE|PRACTICE|REVIEW|QUIZ|TEST", re.I)
OPT_BARE = re.compile(r"^\s*([1-4])\s+[一-鿿]")  # "1 举办了四个活动": an option without brackets
DIGIT_ROW = re.compile(r"^[\d\s|,.:;()\[\]-]{6,}$")  # the answers row under a "Q1 Q2 Q3 ..." key table
OCR_DIGIT = {"S": "5", "s": "5", "O": "0", "o": "0", "l": "1", "I": "1", "i": "1", "t": "1", "T": "1", "|": "1",
             "B": "8", "G": "6", "Z": "2", "z": "2", "g": "9"}
# printed marks "(2分)"; OCR often turns 分 into a digit or letter: "(24)" "(27)" "(34)" "(19>)"; a plain option "(2)" never matches
MARK = re.compile(r"[（(《〈<]\s*([1-5])\s*(?:分|[0-9>A-Za-z])\s*[)）】\]〉》]?")
MARK_BARE = re.compile(r"[（(《〈<]([1-5])[)）】\]〉》]$")  # "(3)" at the end of a line of an open question (分 lost)
MARK_NOOPEN = re.compile(r"(?<=[?？。.，,])([1-5])分[)）]")  # "?2分)": the opening bracket lost
PART1 = ("语文应用", "短文填空", "完成对话", "阅读理解一")  # Prelim Part 1: MCQ / match sections, marks only in the heading


def marks_in(f, open_sec):
    """Printed marks on one (space-free) line: "(2分)", OCR "(24)" "(19>)", "?2分)", and in an open-question section a
    bare "(3)" ending the line."""
    out = [int(x) for x in MARK.findall(f)] + [int(x) for x in MARK_NOOPEN.findall(f)]
    if open_sec and not f.endswith(("分)", "分）")):
        out += [int(x) for x in MARK_BARE.findall(f)]
    return out
INSTR = re.compile(r"从第.{0,4}题到第|^第\d{1,2}题到第|请[把将].{0,10}答案写在")  # "从第26题到第40题，请把答案写在作答簿上": ends a part
NOISE = re.compile(r"^\s*(\d{1,2}|[(（〈《]?接下页[)）〉》]?|从第.{0,3}题到第.{0,3}题.*)\s*$")


def flat(t):
    return re.sub(r"\s+", "", t)


def numeral_of(f):
    m = re.match(rf"^[^一-鿿A-Za-z0-9]{{0,2}}([{NUMERAL}=三二])", f)
    return m.group(1) if m else None


def heading(t):
    """'三、阅读理解一(5题10分)' -> ('阅读理解', f); 'A组(Q30-Q33,4题10分)' -> ('group', 'A'|'B'); else None.
    Numerals and brackets are often OCR-garbled, so a heading is a short line with a section name and either a numeral
    in front or a (N题M分); a group is a short line 'X组(Q30-...' with 1-4 characters before the bracket."""
    f = flat(t)
    if len(f) > 34 or ZQ.match(t) or f.startswith("["): return None
    m = re.match(r"^([^(（《〈\[]{1,4})[(（《〈]Q\s?(\d{1,2})", f)
    if m and Q_RANGE.search(f):
        return "group", "A" if int(m.group(2)) < 34 else "B"
    if re.match(r"^[^一-鿿]{0,2}四", f) and re.search(r"4题8分|\(4题", f): return "完成对话", f  # garbled name
    for key, name in SECTION_KEYS:
        m = re.search(key, f)
        if not m or re.match("[根报很]据|从", f): continue
        if m.start() <= 4 or SEC_MARKS.search(f) or "题" in f:
            return name, f
    if len(f) <= 20 and re.match(r"^[^一-鿿]{0,3}[一-鿿A-Za-z,=、.]{0,6}[(（《〈]\d{1,2}题\d{1,3}分", f):
        return "其他", f  # a section heading whose name OCR lost: "=,FES(5题10分)"
    return None


def sec_name(name, f, paper_secs):
    """阅读理解 -> 阅读理解一 / 阅读理解二 from the text after the name, the numeral before it, or the order."""
    if name != "阅读理解": return name
    m = re.search(r"阅读理|读理解", f); tail = f[m.end() + 1:][:4] if m else ""
    if re.match(r"^[(（]?二|^[(（]?[=_]", tail) or re.search(r"11题|32分", f) or numeral_of(f) == "五": return "阅读理解二"
    if re.match(r"^[(（]?一", tail) or re.search(r"5题|10分", f) or numeral_of(f) == "三": return "阅读理解一"
    return "阅读理解二" if "阅读理解一" in paper_secs else "阅读理解一"


def sec_count(f, mcq):
    """(N, M) of a heading's "(N题M分)", repaired for OCR: "S题" = 5题; a "1" read as "4" ("45题10分", "S题40分") is
    undone when the section is all MCQ (1 or 2 marks each) and only the repaired reading gives that. None if unreadable."""
    m = re.search(r"([0-9SsOlIi]{1,2})题(\d{1,3})分", f)
    if not m: return None
    n = "".join(OCR_DIGIT.get(ch, ch) for ch in m.group(1)); tot = m.group(2)
    cands = [(int(n), int(tot))]
    if len(n) == 2 and n[0] == "4": cands.append((int(n[1]), int(tot)))
    if tot[0] == "4" and len(tot) == 2: cands += [(a, int("1" + tot[1])) for a, _ in list(cands)]
    for a, b in cands:
        if 1 <= a <= 15 and b % a == 0 and (b // a in (1, 2) or not mcq): return a, b
    a, b = cands[0]
    return (a, b) if 1 <= a <= 15 and b >= a else None


def school_cn(c, H):
    """(school, guessed): a Chinese or English school name from the top of a cover/composition page."""
    top = [l for l in c if l["top"] < 0.5 * H]
    for l in top:
        t = l["text"]
        if len(flat(t)) > 30: continue
        if re.search("老师|姓名|班级|leaving|institution|founded|estd", t, re.I): continue
        f = re.split(r"20\d\d|六年级", flat(t))[0]
        m = CN_SCHOOL.search(f)
        if m: return m.group(0), False
        if SCHOOLWORD.search(t) and not P6.search(t) and len(re.findall(r"[A-Za-z]{3,}", t)) >= 1:
            return clean(t), False
    return None, True


def school_good(s):
    return bool(s and re.search(r"school|primary|pri\b|小学|学校|女校|附小|中学", s, re.I))


def script(s):
    return "zh" if s and re.search("[一-鿿]", s) else "en"


def school_sim(a, b):
    if not a or not b: return 0.5
    if script(a) != script(b): return 0.5
    return difflib.SequenceMatcher(None, school_key(a), school_key(b)).ratio()


def exam_cn(text):
    """Prelim / SA2 (年终) / SA1 (年中) / WA (测验, 考查, 练习, 复习, 学段, weighted, review) from cover or title text."""
    f = flat(text)
    if re.search(r"预考|预试|prelim", f, re.I): return "Prelim"
    if re.search(r"年终|年底", f): return "SA2"
    if re.search(r"年中", f): return "SA1"
    e = exam_of(text)
    if e: return e
    if re.search(r"测验|考查|练习|复习|学段|小测|weighted|review|quiz|exercise|practice", f, re.I): return "WA"
    return None


def q_tokens(lines):
    """'Q<n>' tokens of a key table row; the row is often OCR'd without spaces ('Q1Q2Q3'), so a token ends at a non-digit."""
    return sum(len(re.findall(r"Q[0-9ilIoO|]{1,2}(?![0-9])(?=Q|[^A-Za-z]|$)", Q_RANGE.sub("", flat(l["text"])))) for l in lines)


def booklet_label(c):
    """'answer' / 'question' for the label line of a booklet cover ('作答簿', 'ANSWER BOOKLET', ...), else None."""
    head = c[:8]
    shorts = [flat(l["text"]).upper() for l in head if len(flat(l["text"])) <= 20]
    joined = "".join(shorts)
    if LABEL_ANSWER.search(joined) or any(re.fullmatch("作答[簿薄筹筑]", s) for s in shorts): return "answer"
    if LABEL_QUESTION.search(joined) or any(re.fullmatch("问题[簿卷]", s) for s in shorts): return "question"
    return None


def option_lines(c):
    return {m for l in c for m in re.findall(r"^\s*[(（C]\s*([1-4])\s*[)）]", l["text"])}


def page_kind(lines, H, pageno):
    text = " ".join(l["text"] for l in lines)
    if pageno <= 2 and INDEX_PAGE.search(text): return "index"
    c = content(lines, H)
    f = flat(text)
    # "BLANK PAGE" alone; a cover saying "This booklet consists of 16 printed pages and 2 blank pages" is not blank
    if (len(c) <= 1 and not any(ZQ.match(l["text"]) for l in c)) or ("BLANKPAGE" in f.upper() or "空页" in f) and len(c) <= 3:
        return "blank"
    has_q = any(ZQ.match(l["text"]) for l in c)
    has_opts = len(option_lines(c)) >= 3
    for l in c[:6]:  # the key's title: "答案", "参考答案", "选择题答案", "ANSWER KEY"
        fl = flat(l["text"])
        if re.search(r"答案|ANSWERKEY|MARKINGSCHEME", fl.upper()) and len(fl) <= 30 \
                and not re.search("写|填|涂|选出|作答|请|[，。,.]", fl) and not has_opts:
            return "answers"
    # key table rows "Q1 Q2 Q3 ...": a row with a digit row under it, or on a page with no section heading (a question
    # page can carry an empty answer grid "Q13 Q14 Q15 Q16 Q17" under its passage)
    if sum(bool(re.match(r"(SCHOOL|LEVEL|SUBJECT|TERM|YEAR)[:：]", flat(l["text"]).upper())) for l in c[:6]) >= 2 and not has_opts:
        return "answers"  # the answer sheet header "SCHOOL: ... LEVEL: PRIMARY 6 SUBJECT: CHINESE TERM: 2024 WA1"
    rows = [i for i, l in enumerate(c) if q_tokens([l]) >= 4]
    headed = any(heading(l["text"]) for l in c)
    if any(i + 1 < len(c) and DIGIT_ROW.match(flat(c[i + 1]["text"])) for i in rows) or len(rows) >= 2 and not headed \
            or sum(q_tokens([l]) >= 2 for l in c) >= 3 and not headed:
        return "answers"
    if has_q or has_opts: return "content"
    if booklet_label(c) and len(c) <= 30: return "cover"
    top = " ".join(l["text"] for l in c if l["top"] < 0.5 * H)
    if (P6.search(top) or "六年级" in flat(top)) and EXAM_CN.search(flat(top)): return "cover"
    if any(heading(l["text"]) for l in c[:6]): return "content"
    if re.search("OPTICALANSWERSHEET|电脑作答卷", f.upper()) and len(c) < 12: return "oas"
    if re.search(r"作文|看图作文|第[一二]题|参考词语|试卷一|PAPER1|写作", f.upper()): return "composition"
    return "content"


def qlabel(text, exp, last):
    """The question number a line starts with, tolerating OCR junk ('QS' = Q5, 'Qt' = Q1, 'O37', 'Q1S'), or None."""
    if re.match(r"^[\s(（\[【|]*Q\s?\d{1,2}\s*[-—–~至一]", text): return None  # "(Q21—Q25)": a range, never a label
    text = re.sub(r"^[\s，,.。C(（|‘'\"“”\-—_~]+(?=Q)", "", text)
    m = ZQ.match(text)
    if m:
        n = int(m.group(1))
        if last < n <= last + 6 or (n == 1 and last >= 25): return n
    m = re.match(r"^\s*[GgO0C]\s?(\d{1,2})(?!\d)", text)  # "G25" / "C10" for Q25 / Q10: only the expected number
    if m and int(m.group(1)) == exp: return exp
    if exp >= 26 and re.match(rf"^\s*{exp}\s?[一-鿿]", text): return exp  # "33假如你是" lost its Q
    # OCR splits a garbled label with spaces ("Q1 AAIRA" for Q7, "Q85 LER" for Q35): read the label on the space-free text
    text = flat(text)
    if q_tokens([{"text": text}]) >= 3: return None  # "Q13 Q14 Q15 Q16 Q17": an answer grid, not a label
    m = re.match(r"^[O0C]([0-9lIiSsOo|]{1,2})(?=[一-鿿“”\"'，,])", text)  # "Ol妹妹" for Q1 (the Q read as O)
    if m and "".join(OCR_DIGIT.get(ch, ch) for ch in m.group(1)) == str(exp): return exp
    m = re.match(r"^\s*Q(\d{3,4})(?!\d)", text)  # "Q1410" for Q10 (also when Q9 before it was lost)
    if m:
        for n in range(exp, exp + 3):
            if m.group(1).endswith(str(n)): return n
    m = re.match(r"^\s*(?:Q\s?([0-9A-Za-z€|,]{1,3})|[O0](\d{2})(?!\d))", text)
    if m and m.group(1) and re.match(r"^[A-Za-z]{3,}", m.group(1)): return None  # a word, not a label
    if not m: return None
    if m.group(2): n = int(m.group(2)); return n if last < n <= last + 6 else None
    raw = m.group(1)
    digits = ""; garbled = False
    for ch in raw:
        d = ch if ch.isdigit() else OCR_DIGIT.get(ch)
        if d is None: garbled = True; break
        garbled |= not ch.isdigit()
        digits += d
    if not digits: return exp
    n = int(digits)
    if n == exp or garbled and str(exp) == digits[-len(str(exp)):] and len(digits) <= 3: return exp
    if last < n <= last + 6 and not garbled: return n  # a garbled letter ("QB") is no evidence of a jump
    return exp if garbled else None


def junk_label(text, exp):
    """exp when a line at the question column starts with 1-4 junk characters whose last digit matches the expected
    number and a Chinese character follows ('85”知道' for Q5, '943以下' for Q13), else None."""
    m = re.match(r"^\s*([0-9A-Za-z|€]{1,4})\s*[”“\"']?\s*[一-鿿]", text)
    m2 = re.match(r"^\s*(\d{1,2})(?=[A-Z]{2})", text)  # "36HAAA..." / "2RIENG...": the digits, then Latin OCR junk
    if m2: return exp if m2.group(1) == str(exp) else None
    if not m: return None
    d = ""
    for ch in m.group(1):  # the leading run of digits / digit-like letters
        x = ch if ch.isdigit() else OCR_DIGIT.get(ch)
        if x is None: break
        d += x
    e = str(exp)
    if d.endswith(e) or (d and d[-1] == e[-1] and (exp < 10 or len(d) >= 2) and not d.startswith("0" * 3)): return exp
    return None


def prefix_label(text, exp, last):
    """n for a label whose Q was read as another glyph ("61" = Q1, "84" = Q4, "621" = Q21, "G2" = Q2): one of 6/8/9/0/G/O
    then the number; only the expected number or one just after it (a lost label before). The caller checks the context."""
    m = re.match(r"^[689G0OQ]([0-9]{1,2})(?![0-9])", flat(text))
    if not m: return None
    n = int(m.group(1))
    return n if n == exp or last < n <= last + 6 else None


def catalogue_pdf(job):
    import numpy as np
    from PIL import Image
    subject, year, pdf, pages_spec = job
    base = OUT / subject / str(year); pdir = base / "pages"; cdir = base / "crops"; cdir.mkdir(exist_ok=True)
    pages = [p for p in page_range(pages_spec, npages(pdf)) if (pdir / f"p{p:04d}.tsv").exists()]
    papers, questions, passages, kinds = [], [], [], {}
    paper = section = group = None; open_q = None; passage = None; mode = None  # mode: q | abook | key

    def new_paper(school, guessed, exam, part, page, **extra):
        if papers: papers[-1]["last_page"] = max(papers[-1]["first_page"], min(papers[-1]["last_page"], page - 1))
        p = {"n": len(papers) + 1, "paper_id": f"chi-{year}-{len(papers) + 1:03d}", "subject": subject, "year": year,
             "school": school, "school_guessed": guessed, "exam": exam, "part": part, "parts": [part] if part else [],
             "first_page": page, "last_page": page, "answer_pages": [], "answer_booklet_pages": [],
             "composition_pages": [], "last_q": 0, "sec_marks": [], "sec_totals": [], "secs": [], "file": pdf.name, **extra}
        papers.append(p); return p

    def start_paper(*a, **k):
        nonlocal paper, section, group, open_q, passage, mode
        paper = new_paper(*a, **k); section = group = None; open_q = passage = None; mode = "q"
        return paper

    def make_q(qno, page, flags=None, **extra):
        q = {"id": f"chi-{year}-{paper['n']:03d}-q{qno:02d}", "subject": subject, "year": year,
             "paper": paper["paper_id"], "school": paper["school"], "exam": paper["exam"], "part": "Paper 2",
             "section": section, "group": group, "passage": passage["id"] if passage else None, "qno": qno,
             "format": None, "marks": None, "marks_source": None, "pages": [page], "text": "", "figures": [],
             "flags": flags or [], "syllabus": None, "_marks": [], **extra}
        questions.append(q); return q

    for page in pages:
        W, H, words, lines = read_tsv(pdir / f"p{page:04d}.tsv")
        kind = page_kind(lines, H, page); kinds[kind] = kinds.get(kind, 0) + 1
        if os.environ.get("PP_DEBUG"): print(page, kind, mode, paper and paper["last_q"], file=sys.stderr)
        c = content(lines, H)
        if kind in ("index", "blank"): continue
        if kind == "oas":  # the instruction page that opens Booklet A: a new paper when the last one is finished
            if paper is not None and (mode == "key" or paper["last_q"] >= 25):
                start_paper(None, True, None, "Paper 2", page, no_cover=True)
            continue
        text = " ".join(l["text"] for l in c)
        school, guessed = school_cn(c, H)
        if kind == "cover":
            label = booklet_label(c)
            exam = exam_cn(text); part = part_of(text) or ("Paper 1" if "作文" in flat(text) else None)
            if label == "question" and not part: part = "Paper 2"
            if paper is None or mode == "key":
                start_paper(school, guessed, exam, part, page)
            else:
                sim = school_sim(school, paper["school"])
                if paper["last_q"] >= 5 and label != "answer" and not guessed and sim < 0.4 and school:
                    start_paper(school, guessed, exam, part, page)  # another school's cover after questions (a WA has 9-26)
                else:
                    if part and part not in paper["parts"]: paper["parts"].append(part)
                    if school and not guessed and (paper["school_guessed"] or not paper["school"]
                                                   or (school_good(school) and not school_good(paper["school"]))):
                        paper["school"], paper["school_guessed"] = school, False
                    if exam and not paper["exam"]: paper["exam"] = exam
            paper["last_page"] = page
            if label == "answer" or (label is None and paper["last_q"] >= 25): mode = "abook"
            else: mode = "q"
            if mode == "abook": paper["answer_booklet_pages"].append(page)
            section = group = None; open_q = passage = None
            continue
        if kind == "composition":
            if paper is None or mode == "key":
                start_paper(school, guessed, exam_cn(text), "Paper 1", page); mode = "composition"
            elif school and paper["school_guessed"] and not paper["school"]:
                paper["school"], paper["school_guessed"] = school, False
            if "Paper 1" not in paper["parts"]: paper["parts"].append("Paper 1")
            paper["composition_pages"].append(page); paper["last_page"] = page
            continue
        if paper is None:
            start_paper(school, guessed, exam_cn(text), None, page, no_cover=True)
        title = " ".join(l["text"] for l in c[:4])  # a WA / quiz without a cover: school + exam title on its first page
        titled = bool(school and not guessed and re.search(r"六年级|PRIMARY\s*6|P6", flat(title), re.I) and exam_cn(title))
        if mode == "key" and kind != "answers" and titled and (any(qlabel(l["text"], 1, 0) for l in c) or any(heading(l["text"]) for l in c)
                                                               or any(re.search(r"\d题\d+分", flat(l["text"])) for l in c)):
            start_paper(school, guessed, exam_cn(title), None, page, no_cover=True)
        paper["last_page"] = page
        if not paper["exam"]:  # the running footer often names the exam: "CHSP2026P6CLPRELIMP2QB", "ACS(J) P6 CL Prelim 2026"
            paper["exam"] = exam_cn(" ".join(l["text"] for l in lines if l["top"] > 0.9 * H)) if kind != "answers" else None
        if kind == "answers" and (not paper["school"] or paper["school_guessed"]):
            sk, gk = school_cn(c[:3], H)  # the key page names the school in its first lines
            if sk and not gk: paper["school"], paper["school_guessed"] = sk, False
        if kind == "answers":
            mode = "key"; paper["answer_pages"].append(page); open_q = None; continue
        qcol = min((l["left"] for l in c if ZQ.match(l["text"])), default=0)
        opts = option_lines(c)
        if mode == "key":
            q1 = any((m := ZQ.match(l["text"])) and int(m.group(1)) <= 2 for l in c)
            if any(h and h[0] == "语文应用" for h in (heading(l["text"]) for l in c[:6])) or (q1 and len(opts) >= 3):
                start_paper(school, guessed, exam_cn(title), None, page, no_cover=True)
            else:
                paper["answer_pages"].append(page); continue
        seen_heads = [heading(l["text"]) for l in c]
        repeat = any(h and h[0] in ("语文应用", "短文填空", "完成对话") and h[0] in paper["secs"] for h in seen_heads)
        bare = sum(1 for l in c if re.fullmatch(r".{0,2}Q[0-9ilIoO|]{1,2}[。.]?", flat(l["text"])))
        wordy = sum(len(flat(l["text"])) > 10 and not heading(l["text"]) for l in c)  # an answer-booklet page is mostly bare labels
        low = sum(1 for l in c if (m := ZQ.match(l["text"])) and int(m.group(1)) <= 15)
        if mode == "abook" and low >= 3 and not any(heading(l["text"]) and heading(l["text"])[0] != "语文应用" for l in c[:2]):
            mode = "key"; paper["answer_pages"].append(page); open_q = None; continue  # Q1-Q15 after the answer booklet: the key
        if mode == "abook" or (bare >= 3 and len(opts) < 3 and wordy <= 4) or (repeat and bare >= 1):
            mode = "abook"; paper["answer_booklet_pages"].append(page); open_q = None; passage = None; continue
        labelled = [l for l in c if ZQ.match(l["text"]) and not Q_RANGE.match(flat(l["text"]))]
        if paper["last_q"] >= 5 and labelled and re.match(r"^\s*Q\s?1(?=[\s.。,，:：]*[一-鿿])", labelled[0]["text"]) \
                and (titled or any(h and h[0] == "语文应用" for h in seen_heads) or re.search(r"\[Q1|【Q1", flat(text))):
            start_paper(school, guessed, exam_cn(title) if titled else None, None, page, no_cover=True)  # a new paper's Q1

        img = None
        owner = open_q if open_q is not None else passage  # what the top of the page continues
        seg_top = c[0]["top"] if c else 0; segments = []
        body = [l for l in c if not NOISE.match(flat(l["text"])) or heading(l["text"]) or INSTR.search(flat(l["text"]))]
        is_opt = [bool(re.match(r"^\s*[(（C《]\s*[1-4]\s*[)）》]", l["text"]) or OPT_BARE.match(l["text"])) for l in body]
        is_opt1 = [o and bool(re.match(r"^\s*[(（C《]?\s*1\s*[)）》]?", l["text"])) for o, l in zip(is_opt, body)]
        opt_left = min((l["left"] for l, o in zip(body, is_opt) if o), default=None)
        # an option block (1) seen since the open question started: a second (1) block means a question whose label was lost
        seen1 = open_q is not None and bool(re.search(r"(?m)^\s*[(（C]\s*1\s*[)）]", open_q["text"]))
        last_opt = -1
        for idx, l in enumerate(body):
            if INSTR.search(flat(l["text"])) and not heading(l["text"]):  # the part instruction box belongs to no question
                if owner is not None: segments.append((owner, seg_top, l["top"]))
                seg_top = l["top"]; owner = open_q = None
                continue
            h = heading(l["text"])
            start = None; inferred = False
            if h:
                start = ("head", h)
            elif l["left"] <= qcol + 0.05 * W or not qcol:
                qno = qlabel(l["text"], paper["last_q"] + 1, paper["last_q"])
                if qno is None and paper.get("qleft") is not None and abs(l["left"] - paper["qleft"]) < 0.05 * W:
                    qno = junk_label(l["text"], paper["last_q"] + 1)  # "85" / "943" for a Q whose letter was lost
                if qno is None and section not in INLINE and (any(is_opt1[j] for j in range(idx + 1, min(idx + 3, len(body))))
                                                              or re.search(r"[?？]|\d分", flat(l["text"]))):
                    qno = prefix_label(l["text"], paper["last_q"] + 1, paper["last_q"])  # "61" = Q1 before its options
                if qno is not None and qno > 0:
                    paper["qleft"] = l["left"]
                if qno is not None and not (qno == 1 and paper["last_q"] > 8): start = ("q", qno)
            mcq_zone = section not in INLINE and paper["last_q"] >= 1 and open_q is not None and seen1
            if not start and mcq_zone and not is_opt[idx] and opt_left is not None and l["left"] < opt_left - 0.02 * W \
                    and (idx == 0 or is_opt[idx - 1]) and any(is_opt1[j] for j in range(idx + 1, min(idx + 3, len(body)))) \
                    and not re.match(r"^\s*[\[【]", l["text"]) and not re.search(r"根据|从第|选出|请把", flat(l["text"])):
                start = ("q", paper["last_q"] + 1); inferred = True  # a stem at the question column right before its options
            if not start and mcq_zone and is_opt1[idx] and idx > 0 and is_opt[idx - 1]:
                start = ("q", paper["last_q"] + 1); inferred = True  # a (1)-(4) block straight after another: its stem was lost
            if is_opt[idx]: last_opt = idx
            if is_opt1[idx] and not inferred: seen1 = True
            if not start: continue
            seen1 = bool(inferred and is_opt1[idx])
            y_start = l["top"]
            if start[0] == "q" and len(flat(l["text"])) <= 5:  # a bare "Q5" under its stem: the stem is above the label
                j = idx
                while j > 0 and idx - j < 3 and body[j - 1]["top"] > seg_top and \
                        not re.match(r"^\s*[(（C]\s*[1-4]", body[j - 1]["text"]) and not heading(body[j - 1]["text"]) \
                        and not qlabel(body[j - 1]["text"], 0, 99):
                    j -= 1
                y_start = body[j]["top"]
            if owner is not None: segments.append((owner, seg_top, y_start))
            seg_top = y_start
            if start[0] == "head":
                kind_h, num = start[1]
                f = flat(l["text"]); rg = Q_RANGE.search(l["text"])
                if kind_h == "group": group = num
                else:
                    section, group = sec_name(kind_h, num, paper["secs"]), None
                    if section == "其他" and sum(bool(re.search(r"(?:Q|[O0](?=\d\d))\s?\d{1,2}[(（]\s*1", flat(b["text"])))
                                                for b in body[idx + 1:]) >= 2:
                        section = "短文填空"  # blanks "Q2(1.. 2.. 3.. 4..)" inside the passage: a cloze
                    paper["secs"].append(section)
                sm = sec_count(f, kind_h != "group" and section in ("语文应用", "短文填空", "完成对话", "阅读理解一"))
                if sm:
                    n, tot = sm
                    a, b = (int(rg.group(1)), int(rg.group(2))) if rg else (paper["last_q"] + 1, paper["last_q"] + n)
                    if b - a + 1 == n: paper["sec_totals"].append((a, b, tot))
                    if tot % n == 0: paper["sec_marks"].append((a, b, tot // n))
                open_q = None
                if kind_h != "group" or section in PASSAGE_SECTIONS:
                    passage = None
                    if section in PASSAGE_SECTIONS:
                        passage = {"id": f"{paper['paper_id']}-{section}-{group or len(paper['secs'])}",
                                   "paper": paper["paper_id"], "section": section, "group": group, "pages": [page],
                                   "text": "", "figures": []}
                        passages.append(passage)
                    if section in INLINE and kind_h != "group":  # questions live inside the passage text
                        n = INLINE[section][0]  # 5 / 4 by the Prelim layout; "(5题10分)" is often misread ("45题")
                        if sm and 3 <= sm[0] <= 8: n = sm[0]
                        last = paper["last_q"]
                        # the passage names its blanks: "Q13(1..2..)", "Q26。", OCR "016(1"; the first one is the start
                        toks = sorted({int(t) for b in body[idx:] for t in re.findall(
                            r"(?<![0-9A-Za-z])(?:Q\s?|[O0](?=\d\d))(\d{1,2})(?=[(（。.,，?？_\s]|[一-鿿]|$)", flat(b["text"]))
                            if last - 3 <= int(t) <= last + 6})
                        toks = [t for t in toks if t > last]
                        if toks:  # the last blank found fixes the start (the first blank's label is often lost)
                            st = max(last + 1, toks[-1] - n + 1)
                            if toks[0] == INLINE[section][2] and toks[0] > st: st = toks[0]  # the Prelim anchors Q16 / Q26
                            paper["last_q"] = st - 1
                        elif 0 <= INLINE[section][2] - (last + 1) <= 3:  # Prelim layout: a missed label before must not shift these
                            paper["last_q"] = INLINE[section][2] - 1
                        prev = next((q for q in reversed(questions) if q["paper"] == paper["paper_id"]), None)
                        first = not any(q["paper"] == paper["paper_id"] and page in q["pages"] for q in questions)
                        for miss in range(last + 1, paper["last_q"] + 1):  # a lost label just before the passage
                            q = make_q(miss, prev["pages"][-1] if prev and first else page, ["label_not_found"])
                            q["section"] = paper["secs"][-2] if len(paper["secs"]) > 1 else None; q["passage"] = None
                        for k in range(n):
                            q = make_q(paper["last_q"] + 1, page, inline=True); paper["last_q"] += 1
                            q["format"] = INLINE[section][1]
                owner = passage
            else:
                qno = start[1]
                for miss in range(paper["last_q"] + 1, qno):  # a section heading that OCR lost: its inline questions
                    sec_i = "短文填空" if 16 <= miss <= 20 else "完成对话" if 26 <= miss <= 29 else None
                    if sec_i:
                        keep, section = section, sec_i
                        q = make_q(miss, page, ["section_heading_missing"], inline=True)
                        q["format"] = INLINE[sec_i][1]; section = keep
                    elif qno - paper["last_q"] <= 4 and (paper["last_q"] or qno <= 3):
                        # numbering is sequential, so a question between two found labels exists: its label was lost
                        # (garbled beyond reading, or no OCR line at all). Its text stays with the question before it.
                        near_top = open_q is not None and l["top"] - c[0]["top"] < 0.12 * H and page not in open_q["pages"]
                        make_q(miss, open_q["pages"][-1] if near_top else page, ["label_not_found"])
                gap = paper["last_q"] and qno - paper["last_q"] > 4
                flags = [f"qno_gap_after_{paper['last_q']}"] if gap else []
                if inferred: flags.append("label_inferred")
                paper["last_q"] = qno
                open_q = make_q(qno, page, flags); owner = open_q
        if owner is not None: segments.append((owner, seg_top, 0.955 * H))
        for o, y0, y1 in segments:
            seg = [l for l in body if y0 <= l["top"] < y1 and not heading(l["text"])]
            if page not in o["pages"]: o["pages"].append(page)
            o["text"] += ("\n" if o["text"] else "") + "\n".join(l["text"] for l in seg)
            if "_marks" in o:
                o["_marks"] += [x for l in seg if "题" not in l["text"]
                                for x in marks_in(flat(l["text"]), o["section"] not in ("语文应用", "短文填空", "完成对话"))]
            if os.environ.get("PP_NOCROP"): continue  # development runs: skip the slow figure crops
            if img is None: img = np.asarray(Image.open(pdir / f"p{page:04d}.jpg").convert("L"))
            box = figure_box(img, words, lines, y0 - 5, y1 - 5, W)
            if box:
                crop = cdir / f"{o['id']}-p{page:04d}.png"
                Image.fromarray(img[box[1]:box[3], box[0]:box[2]]).save(crop, optimize=True)
                o["figures"].append({"page": page, "bbox": box, "crop": str(crop)})

    for p in papers:  # the heading "B组 (Q34-Q40, 7题22分)" promises questions after the last label found: a lost last label
        mine = [q for q in questions if q["paper"] == p["paper_id"]]
        if not mine: continue
        top = max(mine, key=lambda q: q["qno"])
        for a, b, tot in p["sec_totals"]:
            if a <= top["qno"] < b <= top["qno"] + 2:
                for n in range(top["qno"] + 1, b + 1):
                    questions.append({**top, "id": top["id"][:-2] + f"{n:02d}", "qno": n, "pages": top["pages"][-1:], "text": "",
                                      "figures": [], "flags": ["label_not_found"], "format": None, "_marks": []})
                break
    by_id = {p["paper_id"]: p for p in papers}; pass_by_id = {p["id"]: p for p in passages}
    for p in papers: p["qno_max"] = max((q["qno"] for q in questions if q["paper"] == p["paper_id"]), default=0)
    for q in questions:
        pap = by_id[q["paper"]]; sec = q["section"]
        if q.pop("inline", False):
            ps = pass_by_id.get(q["passage"]); lines_ = (ps["text"] if ps else "").split("\n")
            for ln in lines_:
                m = re.search(rf"Q\s?{q['qno']}(?![0-9])", ln)
                if m:
                    q["text"] = ln[m.start():] if sec == "短文填空" else ln
                    if sec == "短文填空": q["text"] = q["text"][:60]
                    break
            else: q["flags"].append("inline_label_not_found")
            if ps and ps["pages"]: q["pages"] = list(ps["pages"])
        opts = set(OPTION.findall(q["text"])) | {m.group(1) for ln in q["text"].split("\n")[1:] if (m := OPT_BARE.match(ln))}
        marks = q.pop("_marks")
        # the narrowest heading range holding the question ("A组 Q30-Q33 4题10分" inside "11题32分"); its per-question
        # marks only when the total divides evenly, and for an MCQ only 1 or 2 (a mixed group "2题6分" is MCQ 2 + open 4)
        rng = sorted((b - a, a, b, tot) for a, b, tot in pap["sec_totals"] if a <= q["qno"] <= b)
        per = rng[0][3] // (rng[0][0] + 1) if rng and rng[0][3] % (rng[0][0] + 1) == 0 else None
        part1 = sec in PART1 and per is not None and per <= 2
        if q["format"] is None:  # an open question prints its own "(N分)"; an MCQ in Part 1 does not
            q["format"] = "mcq" if len(opts) >= 3 or part1 or (sec in ("语文应用", "阅读理解一") and not marks) else "open"
        if q["format"] == "mcq" and per is not None and per > 2: per = None
        if q["format"] == "mcq" and marks and sum(marks) > 2: marks = []  # OCR noise in the options, not a printed mark
        if marks and sum(marks) > 5: marks = []; q["flags"].append("marks_misread")  # no Paper 2 question is worth more than 4-5
        prelim = pap["qno_max"] >= 36  # the fixed Prelim Paper 2 layout (Q1-40) is the only one the defaults describe
        hit = [per] if per is not None else []
        dflt = [per for a, b, per in DEFAULT_MARKS if a <= q["qno"] <= b and (b < 30 or q["format"] == "mcq")] if prelim else []
        if hit and (part1 or not marks): q["marks"], q["marks_source"] = hit[0], "section (N题M分)"
        elif marks: q["marks"], q["marks_source"] = sum(marks), "printed (N分)"
        elif dflt: q["marks"], q["marks_source"] = dflt[0], "default layout"
        else: q["flags"].append("marks_unknown")
        if not q["text"].strip(): q["flags"].append("no_text")
    for pap in papers:  # a heading's total "(A组 Q30-Q33, 4题10分)" fills lost "(N分)": one question, or several MCQs evenly
        qs = [q for q in questions if q["paper"] == pap["paper_id"]]
        totals = list(pap["sec_totals"]) + (GROUP_TOTALS if pap["qno_max"] >= 36 else [])
        for a, b, tot in totals:
            g = {q["qno"]: q for q in qs if a <= q["qno"] <= b}
            gone = [q for q in g.values() if q["marks"] is None]
            if len(g) != b - a + 1 or not gone: continue
            rest = tot - sum(q["marks"] or 0 for q in g.values())
            if len(gone) == 1 and 1 <= rest <= 6: each = rest
            elif len(gone) > 1 and rest > 0 and rest % len(gone) == 0 and len({q["format"] for q in gone}) == 1 \
                    and 1 <= rest // len(gone) <= (2 if gone[0]["format"] == "mcq" else 4): each = rest // len(gone)
            else: continue
            for q in gone:
                q["marks"], q["marks_source"] = each, "group total" if len(gone) == 1 else "group total (split evenly)"
                q["flags"] = [f for f in q["flags"] if f != "marks_unknown"]
    for p in papers:
        qs = [q for q in questions if q["paper"] == p["paper_id"]]
        p["questions"] = len(qs); p["marks_found"] = sum(q["marks"] or 0 for q in qs)
        p["qno_range"] = [min((q["qno"] for q in qs), default=0), max((q["qno"] for q in qs), default=0)]
        for k in ("n", "last_q", "secs", "qno_max", "qleft"): p.pop(k, None)
        p["sec_marks"] = sorted(set(map(tuple, p["sec_marks"])))
    for name, rows in (("papers", papers), ("questions", questions), ("passages", passages)):
        with open(base / f"{name}.jsonl", "w") as f:
            for r in rows: f.write(json.dumps(r, ensure_ascii=False) + "\n")
    s = {"subject": subject, "year": year, "pages": len(pages), "page_kinds": kinds, "papers": len(papers),
         "papers_school_guessed": sum(p["school_guessed"] for p in papers),
         "papers_without_school": sum(not p["school"] for p in papers), "questions": len(questions),
         "papers_with_40q": sum(p["qno_range"] == [1, 40] and p["questions"] == 40 for p in papers),
         "passages": len(passages), "mcq": sum(q["format"] == "mcq" for q in questions),
         "with_marks": sum(q["marks"] is not None for q in questions),
         "with_figure": sum(bool(q["figures"]) for q in questions),
         "qno_gaps": sum(any(f.startswith("qno_gap") for f in q["flags"]) for q in questions),
         "label_not_found": sum("label_not_found" in q["flags"] for q in questions),
         "label_inferred": sum("label_inferred" in q["flags"] for q in questions)}
    json.dump(s, open(base / "summary.json", "w"), indent=1)
    return s


def selftest():
    assert heading("三 “阅读 理解 一 (5 题 10 分 )")[0] == "阅读理解"
    assert heading("A 组 (Q30-Q33，4 题 10 分 )") == ("group", "A")
    assert heading("B 组 (Q34—Q40, 7 题 22 分 )") == ("group", "B")
    assert heading("B#8(Q34-Q40,7题22分)") == ("group", "B")
    assert heading("一 语文 应用 (15 题 30 分 )")[0] == "语文应用"
    assert heading("语文应用(15题30分)")[0] == "语文应用"
    assert heading("二 ” 和 短文 填空 (5 题 10 分 )")[0] == "短文填空"
    assert not heading("根据 短文 的 内 容 和 上 下 文 的 意思 ， 从 括号 中 选出 适当 的 词语 。")
    assert not heading("(Q21—Q25)") and not heading("[Q1-Q2 请 选 出 画线 词语 的 汉语 拼音 。]")
    assert not heading("Q12 ， 需 要 有 人 翻译 。")
    assert sec_name("阅读理解", "三阅读理解一(5题10分)", []) == "阅读理解一"
    assert sec_name("阅读理解", "五阅读理解(二)(32分)", ["阅读理解一"]) == "阅读理解二"
    assert ZQ.match("Q12 ， 需 要").group(1) == "12" and not ZQ.match("(Q21—Q25)")
    assert Q_RANGE.search("[Q1-Q2 请 选 出]").groups() == ("1", "2")
    assert qlabel("QS ” 外公 每天", 5, 4) == 5 and qlabel("Qt 这本 新书", 1, 0) == 1 and qlabel("O37 小光", 37, 36) == 37
    assert qlabel("Q1S 以下 哪 一 个", 15, 14) == 15 and qlabel("QIl5 以下", 15, 14) == 15 and qlabel("Q 他 的", 3, 2) is None
    assert MARK.findall("(24)") == ["2"] and MARK.findall("(23)") == ["2"] and MARK_BARE.findall("批评y(3)") == ["3"] and MARK.findall("(2 分 )") == ["2"] and not MARK.findall("(1) zanshi")
    assert junk_label("85 ” 知道 自己", 5) == 5 and junk_label("943 ” 以下", 13) == 13 and junk_label("1 难道", 26) is None
    assert school_cn([{"top": 1, "text": "公教 中 学 ( 附小 )"}], 100) == ("公教中学(附小)", False)
    assert school_cn([{"top": 1, "text": "南华 小学 2026 年"}], 100)[0] == "南华小学"
    assert school_sim("南华小学", "RAFFLES GIRLS PRIMARY SCHOOL") == 0.5
    L = lambda t, top=100: {"text": t, "top": top, "left": 300, "right": 900, "bottom": top + 40, "words": []}
    H = 3510
    assert page_kind([L("参考 答案", 400), L("Q1 Q2 Q3 Q4 Q5 Q6", 600)], H, 50) == "answers"
    assert page_kind([L("从 第 1 题 到 第 25 题 ， 请 选出 答案 ， 把 电脑", 400), L("一 语文 应用 (15 题 30 分 )", 600),
                      L("Q1 我 的 手机 没电 了", 800)], H, 50) == "content"
    assert page_kind([L("公教 中 学 (附小 )", 400), L("2026 年 六 年 级 华文 预 考", 500), L("试卷 二", 600)], H, 50) == "cover"
    assert page_kind([L("作答 簿", 400), L("ANSWER BOOKLET", 500), L("姓名 :", 800)], H, 50) == "cover"
    assert booklet_label([L("QUESTION", 400), L("BOOKLET", 500)]) == "question"
    assert booklet_label([L("从 第 26 题 到 第 40 题 ， 请 把 答案 写 在 作答 簿 上 。")]) is None
    assert sec_name(*heading("五 阅读 理解 二 (11 题 32 分 )"), []) == "阅读理解二"
    assert heading("=.上短文填空45题10分)")[0] == "短文填空" and heading("四SMT(4题8分)")[0] == "完成对话"
    assert not heading("报据短文的内容和上下文的意思，选出适当的答案。")
    # round 2 rules
    assert qlabel("(Q21—Q25)", 21, 20) is None  # a range is never a label
    assert qlabel("Q1 AAIRA, BHW", 7, 6) == 7 and qlabel("Q85 LER BERRA", 35, 34) == 35 and qlabel("Q1410_要参加", 10, 9) == 10
    assert qlabel("Q1, BERS TRE", 11, 10) == 11 and qlabel("|Q32 想 了解", 32, 31) == 32 and qlabel("Ol 妹妹 一 走进", 1, 0) == 1
    assert qlabel("QB ”哥哥 只 顾", 3, 2) == 3  # a garbled letter is no jump to Q8
    assert qlabel("Q13Q14Q15Q16G17", 18, 17) is None  # an empty answer grid on a question page
    assert junk_label("36HAAAARRE", 36) == 36 and junk_label("2RIENGERETO18", 2) == 2 and junk_label("36HAAA", 35) is None
    assert prefix_label("61 ”我 头 有 点 痛", 1, 0) == 1 and prefix_label("621 bAUS", 21, 20) == 21 and prefix_label("2026 年", 1, 0) is None
    assert exam_cn("2026 年 六 年 级 华文 预 考") == "Prelim" and exam_cn("六 年 级 华文 年终 考试") == "SA2"
    assert exam_cn("2026年六年级年中练习") == "SA1" and exam_cn("华文 小 测验 (一)") == "WA" and exam_cn("TIMED PRACTICE PAPER") == "WA"
    assert sec_count("二短文填空45题10分)", True) == (5, 10) and sec_count("二短文填空(S题40分)", True) == (5, 10)
    assert sec_count("三、阅读理解(5题16分)", False) == (5, 16) and sec_count("一语文应用(15题30分)", True) == (15, 30)
    assert marks_in("Q37家庭日当天,作者有什么感受?(1分)AHA?(2)", True) == [1, 2] and marks_in("Q24伟文?2分)老师", True) == [2]
    assert heading("=,FES(5题10分)") == ("其他", "=,FES(5题10分)")
    assert page_kind([L("This booklet consists of 16 printed pages and 2 blank pages", 2900), L("Anglo-Chinese School (Junior)", 400),
                      L("PRELIMINARY EXAMINATION (2026)", 600), L("PRIMARY 6", 700), L("QUESTION BOOKLET", 800)], H, 31) == "cover"
    assert page_kind([L("菜佛士 女子 小学 测验 (一)", 300), L("Q1 Q2 Q3 Q4 Q5 Q6 Q7 Q8 Q9", 500), L("2 3 1 4 2 3 4 2 3", 600)], H, 525) == "answers"
    assert page_kind([L("二 短文 填空 (5 题 10 分 )", 300), L("Q13 Q14 Q15 Q16 G17", 2300)], H, 539) == "content"
    assert page_kind([L("SCHOOL: RAFFLES GIRLS' PRIMARY", 300), L("LEVEL: PRIMARY 6", 400), L("TERM: 2024 WA1", 500)], H, 421) == "answers"
    assert INSTR.search(flat("从 第 26 题 到 第 40 题 ， 请 把 答案 写 在 作答 簿 上 。")) and not INSTR.search("Q26 小华 写 在")
    print("chinese selftest ok")
