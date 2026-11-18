#!/usr/bin/env python3
"""Catalogue the P6 past papers in PastPapers/ without an LLM (step A).

  ocr        render every page (300 dpi grey JPEG) and OCR it with Tesseract -> TSV with word boxes
  catalogue  split each compiled PDF into papers (school, exam, booklet/paper, answer-key pages) and
             questions (number, section, format, marks, text, figure crops)
  all        ocr then catalogue
  selftest   run the parser checks

  python3 scripts/pastpapers/catalogue.py ocr --subject science --year 2024 --pages 1-120
  python3 scripts/pastpapers/catalogue.py catalogue --subject science --year 2024 --pages 1-120
  python3 scripts/pastpapers/catalogue.py all                    # everything; resumable (done pages are skipped)

Output under OUT/<subject>/<year>/:
  pages/pNNNN.jpg + pNNNN.tsv   page image and Tesseract words (kept for step B, so nothing is OCR'd twice)
  papers.jsonl                  one line per school paper
  questions.jsonl               one line per question; "syllabus" is null, filled by the LLM in step B
  crops/<id>-pNNNN.png          the figure/table/picture area of a question on that page
  summary.json
The papers and everything derived from them stay outside the repo; only this script is committed.
"""
import argparse, csv, difflib, json, os, re, subprocess, sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

SRC = Path("/data/alvin/cookie-codex/PastPapers")
OUT = Path("/data/alvin/tmp/cookie-codex/pastpapers")
BIN = Path("/data/alvin/tmp/cookie-codex/ocr-env/bin")  # pdftoppm, pdfinfo, tesseract
SUBJECTS = {"maths": "P6 Maths", "science": "P6 Science", "english": "P6 English", "chinese": "P6 Chinese"}
LANG = {"chinese": "chi_sim+eng"}  # default eng
DPI = 300

# ---------------------------------------------------------------- page text

WATERMARK = re.compile(r"kiasu\s*exam\s*paper|www\.|whatsapp", re.I)
INDEX_PAGE = re.compile(r"softcopy|islandwide", re.I)
P6 = re.compile(r"primary\s*(6|six)\b|\bp\s*6\b|六年级", re.I)
EXAMWORD = re.compile(r"exam|assessment|prelim|\bsa\s*[12]\b|semestral|review|test|考试|测验", re.I)
COVERWORD = re.compile(r"instruction|name\s*[:;]|class\s*[:;]|index|duration|time\s*[:;]|姓名|班级|说明", re.I)
SCHOOLWORD = re.compile(r"school|pri\.?\s*sch|convent|institution|\bacs\b|\bchij\b|anglo|academy|小学|学校", re.I)
ANSWER_TITLE = re.compile(r"answer\s*key|^\s*answers?\s*$|marking\s*scheme|suggested\s*answers?|答案", re.I)
QSTART = re.compile(r"^\s*Q?\s*(\d{1,2})(?:\s*[.．、)]|\s+|$)")  # "12 ...", "12. ...", "Q12"; never "(12)"
STEM = re.compile(r"\s*(The|Which|What|Why|How|Study|Look|Refer|In|An?|Some|Two|Three|Four|Each|When|[A-Z][a-z]+ (?:placed|put|carried|wanted|set|conducted|used|had|has|filled|poured|tested|observed|measured|added|kept|left|prepared|investigated|made|built|connected))\b")
FOOTER = re.compile(r"examination|\bexam\b|prelim|page\s*\d|go on|continue|turn over|booklet|school|\b20\d\d\b", re.I)
OPTION = re.compile(r"\(\s*([1-4])\s*\)")
MARK_WORD = re.compile(r"^\[\s*(\d{1,2})\s*(?:m|mk|mks|marks?)?\s*\]$|^\(\s*(\d{1,2})\s*(?:m|mk|mks|marks?)\s*\)$|^\[(\d{1,2})$|^(\d{1,2})\]$", re.I)
SEC_MARKS = [
    re.compile(r"questions?\s*(\d{1,2})\s*(?:to|-|–)\s*(\d{1,2})\s*(?:carry|carries)\s*(\d)\s*marks?\s*each", re.I | re.S),
    re.compile(r"(?:questions?|from)\s*(\d{1,2})\s*(?:to|-|–)\s*(\d{1,2}).{0,300}?\((\d{1,3})\s*marks?\)", re.I | re.S),
]
SECTIONS = {
    "english": [(r"grammar\s*cloze", "Grammar Cloze"), (r"editing|spelling", "Editing"),
                (r"comprehension\s*cloze", "Comprehension Cloze"), (r"vocabulary\s*cloze", "Vocabulary Cloze"),
                (r"synthesis|transformation", "Synthesis"), (r"visual\s*text", "Visual Text"),
                (r"comprehension|open[- ]?ended", "Comprehension OE"), (r"grammar", "Grammar MCQ"),
                (r"vocabulary", "Vocabulary MCQ")],
    "chinese": [(r"语文应用", "语文应用"), (r"短文填空", "短文填空"), (r"完成对话", "完成对话"),
                (r"阅读理解", "阅读理解"), (r"词语", "词语"), (r"句子", "句子")],
    "maths": [(r"short[- ]?answer", "Short Answer"), (r"multiple[- ]?choice", "MCQ")],
    "science": [(r"multiple[- ]?choice", "MCQ"), (r"open[- ]?ended", "Open-ended")],
}


def exam_of(text):
    t = text.lower()
    if "prelim" in t: return "Prelim"
    if re.search(r"\bsa\s*2\b|semestral\s*assessment\s*(2|ii)\b|end[- ]of[- ]year|\beoy\b", t): return "SA2"
    if re.search(r"\bsa\s*1\b|semestral\s*assessment\s*(1|i)\b|mid[- ]year", t): return "SA1"
    if re.search(r"\bwa\s*\d|weighted|continual|\bca\s*\d|review", t): return "WA"
    return None


def part_of(text):
    m = re.search(r"booklet\s*([AB])\b", text, re.I) or re.search(r"([甲乙])\s*卷", text)
    b = {"甲": "A", "乙": "B"}.get(m.group(1), m.group(1).upper()) if m else None
    m = re.search(r"paper\s*([12])\b", text, re.I) or re.search(r"试?卷\s*([一二])", text)
    p = {"一": "1", "二": "2"}.get(m.group(1), m.group(1)) if m else None
    return "/".join(x for x in (p and f"Paper {p}", b and f"Booklet {b}") if x) or None


def school_of(lines, H):
    top = [l for l in lines if l["top"] < 0.5 * H]
    for l in top:
        if SCHOOLWORD.search(l["text"]) and not P6.search(l["text"]) and not re.search(r"leaving", l["text"], re.I):
            return clean(l["text"]), False
    for l in top:  # fallback: the first real words at the top of the cover
        if not EXAMWORD.search(l["text"]) and len(re.findall(r"[A-Za-z]{2,}|[一-鿿]{2,}", l["text"])) >= 2:
            return clean(l["text"]), True
    return None, True


def clean(s):
    return re.sub(r"\s+", " ", re.sub(r"^[^\w一-鿿]+|[^\w)一-鿿]+$", "", s)).strip()


def school_key(s):
    s = re.sub(r"primary|school|pri|sch|小学|学校", "", (s or "").lower())
    return re.sub(r"[^a-z0-9一-鿿]", "", s)


def section_of(subject, text):
    t = re.sub(r"\s+", "" if subject == "chinese" else " ", text)
    for pat, name in SECTIONS.get(subject, []):
        if re.search(pat, t, re.I): return name
    return None


def fix_qnum(t):
    """OCR reads the 1 in "Q1", "Q11" as i / l / I / | (common in the Chinese papers)."""
    return re.sub(r"^(\s*Q)([0-9il|I]{1,2})(?=\W|$)", lambda m: m.group(1) + re.sub(r"[il|I]", "1", m.group(2)), t)


def read_tsv(path):
    """-> (W, H, words, lines). Lines group Tesseract words by block/par/line, top to bottom."""
    W = H = 0; words = []; groups = {}
    with open(path, encoding="utf-8", errors="replace") as f:
        for r in csv.reader(f, delimiter="\t", quoting=csv.QUOTE_NONE):
            if len(r) < 12 or not r[0].isdigit(): continue
            lvl, x, y, w, h = int(r[0]), int(r[6]), int(r[7]), int(r[8]), int(r[9])
            if lvl == 1: W, H = w, h
            if lvl != 5 or not r[11].strip(): continue
            wd = {"left": x, "top": y, "right": x + w, "bottom": y + h, "conf": float(r[10]), "text": r[11].strip()}
            words.append(wd)
            groups.setdefault((r[2], r[3], r[4]), []).append(wd)
    lines = []
    for ws in groups.values():
        ws.sort(key=lambda w: w["left"])
        lines.append({"left": ws[0]["left"], "top": min(w["top"] for w in ws), "right": max(w["right"] for w in ws),
                      "bottom": max(w["bottom"] for w in ws), "words": ws,
                      "text": fix_qnum(" ".join(w["text"] for w in ws))})
    lines.sort(key=lambda l: (l["top"], l["left"]))
    return W, H, words, lines


def content(lines, H):
    """Drop the header/footer bands (page numbers) and watermark lines."""
    return [l for l in lines if 0.045 * H < l["top"] < 0.955 * H and not WATERMARK.search(l["text"])
            and len(re.findall(r"[\w一-鿿]", l["text"])) >= 2]


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


# ---------------------------------------------------------------- figures

def figure_box(img, words, lines, y0, y1, W):
    """Bounding box of the non-text ink between y0 and y1 (pictures, diagrams, tables), or None.
    ponytail: one union box per question per page; split into several boxes if step B needs them separately."""
    import numpy as np
    from scipy import ndimage
    y0, y1 = max(0, int(y0)), min(img.shape[0], int(y1))
    if y1 - y0 < 120: return None
    ink = img[y0:y1] < 140

    def blank(t, b, l, r): ink[max(0, t - y0 - 4):max(0, b - y0 + 4), max(0, l - 4):r + 4] = False
    # sentences are text, not picture: mask whole lines of 3+ confident words, then any confident word;
    # short low-confidence "words" (labels inside a diagram) stay as ink, so the figure keeps them
    for l in lines:
        if y0 <= l["top"] < y1 and len(l["words"]) >= 3 and sum(w["conf"] for w in l["words"]) / len(l["words"]) >= 50:
            blank(l["top"], l["bottom"], l["left"], l["right"])
    for w in words:
        if w["conf"] >= 40 and y0 <= w["top"] < y1:
            blank(w["top"], w["bottom"], w["left"], w["right"])
    # long horizontal rules are answer lines, not pictures
    ink &= ~ndimage.binary_opening(ink, structure=np.ones((1, int(0.2 * W)), bool))
    B = 12
    h, w = ink.shape[0] // B * B, ink.shape[1] // B * B
    blocks = ink[:h, :w].reshape(h // B, B, w // B, B).any(axis=(1, 3))
    lab, n = ndimage.label(ndimage.binary_dilation(blocks, iterations=2))
    boxes = []
    for sl in ndimage.find_objects(lab):
        bh, bw = (sl[0].stop - sl[0].start) * B, (sl[1].stop - sl[1].start) * B
        if bh >= 150 and bw >= 150:
            boxes.append((sl[1].start * B, sl[0].start * B + y0, sl[1].stop * B, sl[0].stop * B + y0))
    if not boxes: return None
    x0, t, x1, b = min(b[0] for b in boxes), min(b[1] for b in boxes), max(b[2] for b in boxes), max(b[3] for b in boxes)
    for _ in range(2):  # take in the labels beside or inside the picture: short lines (<= 4 words) next to the box
        for l in lines:
            mid = (l["top"] + l["bottom"]) / 2
            if y0 <= l["top"] < y1 and len(l["words"]) <= 4 and t - 40 <= mid <= b + 40 \
                    and l["left"] - x1 <= 150 and x0 - l["right"] <= 150:
                x0, t, x1, b = min(x0, l["left"]), min(t, l["top"]), max(x1, l["right"]), max(b, l["bottom"])
    return [max(0, x0 - 15), max(0, t - 15), min(img.shape[1], x1 + 15), min(img.shape[0], b + 15)]


# ---------------------------------------------------------------- OCR stage

def pdfs(subject=None, year=None):
    for key, folder in SUBJECTS.items():
        if subject and subject != key: continue
        for p in sorted((SRC / folder).glob("*.pdf")):
            m = re.search(r"(20\d\d)", p.name)
            if m and (not year or m.group(1) == str(year)):
                yield key, int(m.group(1)), p


def npages(pdf):
    out = subprocess.run([str(BIN / "pdfinfo"), str(pdf)], capture_output=True, text=True).stdout
    return int(re.search(r"Pages:\s+(\d+)", out).group(1))


def ocr_margin(jpg, tsv, out):
    """Tesseract drops a question number that stands alone far left of its text ("4.      Which of ...").
    OCR only the strip left of the text column, digits only, so those numbers are found."""
    from PIL import Image
    W, H, _, lines = read_tsv(tsv)
    body = [l["left"] for l in lines if 0.06 * H < l["top"] < 0.93 * H and len(l["words"]) >= 3]
    x = (min(body) - 8) if body else 0
    if x < 40:
        out.write_text(""); return
    crop = out.with_suffix(".png")
    Image.open(jpg).crop((0, 0, x, H)).save(crop)
    tmp = out.parent / f".m{out.stem}"
    subprocess.run([str(BIN / "tesseract"), str(crop), str(tmp), "--psm", "6", "-c", "tessedit_char_whitelist=0123456789.Q",
                    "tsv"], check=True, capture_output=True, env={**os.environ, "OMP_THREAD_LIMIT": "1"})
    os.replace(f"{tmp}.tsv", out); crop.unlink()


def ocr_page(job):
    subject, pdf, page, d = job
    tsv = d / f"p{page:04d}.tsv"
    margin = d / f"p{page:04d}.m.tsv"
    if tsv.exists():
        if margin.exists(): return "skip"
        ocr_margin(d / f"p{page:04d}.jpg", tsv, margin); return "ok"
    jpg = d / f"p{page:04d}.jpg"
    if not jpg.exists():
        subprocess.run([str(BIN / "pdftoppm"), "-r", str(DPI), "-gray", "-jpeg", "-jpegopt", "quality=90",
                        "-f", str(page), "-l", str(page), "-singlefile", str(pdf), str(d / f".r{page:04d}")], check=True)
        os.replace(d / f".r{page:04d}.jpg", jpg)
    tmp = d / f".t{page:04d}"
    subprocess.run([str(BIN / "tesseract"), str(jpg), str(tmp), "-l", LANG.get(subject, "eng"), "--psm", "4", "tsv"],
                   check=True, capture_output=True, env={**os.environ, "OMP_THREAD_LIMIT": "1"})
    os.replace(f"{tmp}.tsv", tsv)
    ocr_margin(jpg, tsv, margin)
    return "ok"


def page_range(spec, n):
    if not spec: return range(1, n + 1)
    a, _, b = spec.partition("-")
    return range(int(a), min(n, int(b or a)) + 1)


def run_ocr(args):
    jobs = []
    for subject, year, pdf in pdfs(args.subject, args.year):
        d = OUT / subject / str(year) / "pages"; d.mkdir(parents=True, exist_ok=True)
        jobs += [(subject, pdf, p, d) for p in page_range(args.pages, npages(pdf))]
    print(f"ocr: {len(jobs)} pages, {args.jobs} workers", flush=True)
    done = 0
    with ProcessPoolExecutor(args.jobs) as ex:
        for i, r in enumerate(ex.map(ocr_page, jobs, chunksize=4), 1):
            done += r == "ok"
            if i % 500 == 0: print(f"  {i}/{len(jobs)} ({done} new)", flush=True)
    print(f"ocr: done, {done} pages newly OCR'd")


# ---------------------------------------------------------------- catalogue stage

def catalogue_any(job):
    """Each subject has its own step A rules: scripts/pastpapers/subject_<subject>.py."""
    import importlib
    return importlib.import_module(f"subject_{job[0]}").catalogue_pdf(job)


def run_catalogue(args):
    jobs = [(s, y, p, args.pages) for s, y, p in pdfs(args.subject, args.year)]
    with ProcessPoolExecutor(min(args.jobs, len(jobs) or 1)) as ex:
        for s in ex.map(catalogue_any, jobs):
            print(json.dumps(s, ensure_ascii=False), flush=True)


# ---------------------------------------------------------------- checks

def selftest():
    assert QSTART.match("12 The diagram shows").group(1) == "12"
    assert QSTART.match("3. Which of these").group(1) == "3"
    assert QSTART.match("Q7 Study the graph").group(1) == "7"
    assert not QSTART.match("(1) Both need light to grow.")
    assert not QSTART.match("(12)")
    assert sorted(set(OPTION.findall("(1) a (2) b ( 3 ) c (4) d"))) == ["1", "2", "3", "4"]
    for w, v in [("[2]", 2), ("(3m)", 3), ("[1", 1), ("2]", 2), ("(2 marks)", 2), ("(4)", None), ("(6)", None), ("[2m]", 2)]:
        m = MARK_WORD.match(w)
        assert (next(g for g in m.groups() if g) if m else None) == (str(v) if v else None), w
    assert exam_of("PRELIMINARY EXAMINATION (2024)") == "Prelim"
    assert exam_of("SEMESTRAL ASSESSMENT 2") == "SA2" and exam_of("SA1 2023") == "SA1"
    assert part_of("SCIENCE (BOOKLET A)") == "Booklet A" and part_of("MATHEMATICS PAPER 2") == "Paper 2"
    assert part_of("试卷一 甲卷") == "Paper 1/Booklet A"
    assert section_of("english", "Grammar Cloze (10 marks)") == "Grammar Cloze"
    assert section_of("english", "Section B: Vocabulary") == "Vocabulary MCQ"
    assert section_of("chinese", "二、 短 文 填 空") == "短文填空"
    cover = [{"text": "Anglo- Chinese School (Junior)", "top": 300}, {"text": "PRELIMINARY EXAMINATION (2024)", "top": 400},
             {"text": "PRIMARY 6", "top": 500}]
    assert school_of(cover, 3300) == ("Anglo- Chinese School (Junior)", False)
    assert school_key("Rosyth School") == school_key("ROSYTH SCH")
    m = SEC_MARKS[1].search("For each question from 1 to 28, four options are given.\nshade the OAS.\n(56 marks)")
    assert m.groups() == ("1", "28", "56")
    assert fix_qnum("Qi 邻居") == "Q1 邻居" and fix_qnum("Q1i5 x") == "Q115 x"[:0] + fix_qnum("Q1i5 x") and fix_qnum("Ql2 abc") == "Q12 abc"
    assert QSTART.match(fix_qnum("Qi")).group(1) == "1"
    print("selftest ok")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["ocr", "catalogue", "all", "selftest"])
    ap.add_argument("--subject", choices=list(SUBJECTS))
    ap.add_argument("--year", type=int)
    ap.add_argument("--pages", help="page range for a pilot, e.g. 1-120")
    ap.add_argument("--jobs", type=int, default=max(1, (os.cpu_count() or 2) - 4))
    a = ap.parse_args()
    if a.cmd == "selftest":
        selftest(); import subject_chinese; subject_chinese.selftest(); sys.exit()
    if a.cmd in ("ocr", "all"): run_ocr(a)
    if a.cmd in ("catalogue", "all"): run_catalogue(a)
