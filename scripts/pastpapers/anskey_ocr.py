"""Deterministic answer-key reader for private past papers (ADR 0004). Reads and writes ONLY outside the repo.

  anskey_ocr.py run [--subject science] [--years 2018-2024] [--pp DIR] [--jobs N]
      For each paper, scans its answer pages (papers.jsonl answer_pages; when none, every page from the paper's first
      page up to the next paper) in the tesseract word boxes (pages/pNNNN.tsv) and reads the MCQ answer grid into
      {qno: option 1-4}. Writes PP/<subject>/<year>/anskey_ocr.jsonl, one row per paper:
        {paper, ok, answers: {"1": "3", ...}, pages: [...], layout, n_mcq, coverage, from_answer_pages, why}
      from_answer_pages is true when the paper has its own answer pages (otherwise question pages were scanned and
      load_pp.py select --ocr-keys ignores the row).
      ok is true only when every MCQ number 1..N of the paper (N = the paper's MCQ numbers in merged.jsonl) is read
      from one or more pages with one digit 1-4, and any repeat read agrees.
  anskey_ocr.py compare [--subject science] [--years 2018-2024]
      Reports per year how the OCR read agrees with the existing merged.jsonl answers (vision model reads); counts only.
  anskey_ocr.py find-answer-pages [--subject science] [--years 2018-2026] [--pp DIR] [--reread-dir DIR] [--measure]
      Papers recorded with empty answer_pages often carry their key inside their own page range (the last pages: the
      repeated paper header, a "Q1 Q2 ..." grid with the answers under it, Booklet B lines "Q29 a)"). Scores every page
      of such a paper from its TSV words (page_signals / is_answer_page) and keeps a page only on strong evidence:
      a grid (structure() finds >= 4 cells, or a line of >= 3 strict Q labels, or >= 2 "Qn a)" lines), or >= 6 labels
      under the repeated header, or (last 8 pages only) the paper header on a page after the paper's first two. Pages in the paper's last 8 pages use that rule; an earlier page needs a stronger one
      (>= 8 cells, or the header with 3+ labels in a line). Writes PP/<subject>/<year>/answer_pages_found.json
      {paper_id: [pages]} and questions_on_answer_pages.json {paper_id: [question ids]} (a question whose every page is a
      found or listed answer page was catalogued from an answer page: exclude it). papers.jsonl is not touched. With
      --reread-dir, also writes DIR/pages.jsonl {subject, year, paper, page, n_mcq, mcq: [...]} (one row per found page;
      the input of run_ans_reread.sh). --measure prints the detector's page precision and recall on the papers that DO
      have answer_pages (truth: listed answer pages; grid truth: listed pages whose ans32 read has >= 8 MCQ cells).
  anskey_ocr.py selftest

Layouts read (rows, pairs, slots, numslots; all from word-box geometry; label text is only a hint because tesseract garbles "Q1" into "Qi", "a10~"):
  rows    a line of >=4 labels (Q1 Q2 ...) with a line of single digits 1-4 directly below, one digit per label x-position
  pairs   lines of alternating label, digit (Q1 3 Q6 1 ...; or plain "1 4  11 2  21 2"): column-major numbering
  slots   table lines of (label, digit) cells read by x-position; row-major numbering
  numslots  tables of (number, answer) column pairs without Q prefixes, e.g. "Qn | Answer" lists; column-major numbering
Not read: pages rotated 90 degrees, anything that fails the checks above.
Nothing here prints question text or answers: counts and ids only.
"""
import argparse, collections, csv, io, json, multiprocessing, re, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from load_pp import jl, years  # load_pp does not import this module: no cycle

TMP = Path("/data/alvin/tmp/cookie-codex")
DEF_PP = TMP / "pastpapers"
LABEL = re.compile(r"^[QqGg9aAoO0@(\[]?[.\-]?\s?[\w.\-~]{0,3}$")
DIG = re.compile(r"^[1-4]$")
TESS = TMP / "ocr-env" / "bin" / "tesseract"  # the binary catalogue.py uses


PAGE = {}


def read_words(path):
    """[(cx, cy, h, text)] of level-5 words, with a lone 'Q' glued to the number to its right."""
    out = []
    if not Path(path).exists():
        return out
    with open(path, newline="") as f:
        for r in csv.DictReader(f, delimiter="\t", quoting=csv.QUOTE_NONE):
            if r["level"] != "5" or not r["text"].strip():
                continue
            t = r["text"].strip()
            if set(t) <= set("|_-—.,:;'`~‘’"):
                continue
            L, T, W, H = int(r["left"]), int(r["top"]), int(r["width"]), int(r["height"])
            t = t.strip("|[]{}()_.,:;'`")
            if t:
                out.append([L + W / 2, T + H / 2, H, t])
    return out


def lines_of(words):
    """Group words into text lines by y (tolerance 0.6 of the median height); each line sorted by x."""
    if not words:
        return []
    hs = sorted(w[2] for w in words)
    tol = max(12, 0.6 * hs[len(hs) // 2])
    ws = sorted(words, key=lambda w: w[1])
    lines, cur = [], [ws[0]]
    for w in ws[1:]:
        if abs(w[1] - sum(x[1] for x in cur) / len(cur)) <= tol:
            cur.append(w)
        else:
            lines.append(cur)
            cur = [w]
    lines.append(cur)
    out = []
    for ln in lines:
        ln = sorted(ln, key=lambda w: w[0])
        merged = []
        for w in ln:  # glue a lone Q/G to the number on its right
            if merged and re.fullmatch(r"[QqGg]", merged[-1][3]) and re.fullmatch(r"\d{1,2}", w[3]):
                merged[-1] = [w[0], w[1], w[2], "Q" + w[3]]
            else:
                merged.append(list(w))
        out.append(merged)
    return out


def num_of(t):
    """Question number in a (garbled) label: 'Qi2' -> 12 (tesseract reads the 1 as i), 'Qio' -> 10, 'O19' -> 19."""
    t = re.sub(r"[iIl|]", "1", t[1:] if t[:1].isalpha() else t)
    t = re.sub(r"[zZ]", "2", t)
    t = re.sub(r"(?<=\d)[oO]", "0", t)
    m = re.match(r"\W*(\d{1,2})\W*$", t)
    return int(m.group(1)) if m else None


def labelish(t, bare=False):
    """A label token: Q-ish text that is not a bare answer digit 1-4. A bare 1-2 digit number counts only when
    bare=True (the pairs layout, whose labels may be plain numbers), so a line of answers is not read as labels."""
    return (bool(LABEL.match(t)) and t not in ("", "|") and not DIG.match(t)) or \
        (bare and bool(re.fullmatch(r"\d{1,2}", t)))


def vote_start(readable, prev_end):
    """Row start number from the readable labels (n - index); falls back to prev_end + 1 when unsupported."""
    votes = collections.Counter(n - i for i, n in readable if n is not None and 1 <= n <= 60)
    if votes:
        s, c = votes.most_common(1)[0]
        if c >= 2:
            return s, c
    return (prev_end + 1 if prev_end is not None else None), 0


USE_CROP = True  # a TSV digit needs the crop vote to agree (the TSV alone misreads 2-3% of digits)
ANYDIG = re.compile(r"^\D{0,1}(\d)\D{0,1}$")


def tsv_digit(t):
    """The single digit 1-4 a noisy answer token stands for ('4°' -> '4'), else None ('1.4', '5' -> None)."""
    m = ANYDIG.match(t)
    return m.group(1) if m and m.group(1) in "1234" and len(t) <= 2 else None


def read_rows(lines):
    """Layout 'rows': a label line (>=4 labels) and the answer line below it (>= half as many digit-like tokens).
    Returns cells [(qno, x, y, tsv digit or None, pitch)] with the x of each label and the y of the answer line."""
    cells, rows, prev_end, prev_y = [], 0, None, None
    for i in range(len(lines) - 1):
        lab, ans = lines[i], lines[i + 1]
        lt = [t for t in lab if labelish(t[3]) or re.fullmatch(r"\W*\w{1,5}\W*", t[3])]
        if len(lt) < 4 or len(lt) != len(lab):
            continue
        dg = [t for t in ans if re.fullmatch(r"\D{0,1}\d\D{0,1}|\d\.\d", t[3])]
        if len(dg) < 0.5 * len(lt) or len(dg) != len(ans):
            continue
        if not any(re.match(r"[QqGg9aAoO0@]", t[3]) for t in lt) or sum(bool(re.search(r"\d|[iIlzsS]", t[3])) for t in lt) < 0.6 * len(lt):
            continue
        xs = [t[0] for t in lt]
        pitch = (xs[-1] - xs[0]) / (len(lt) - 1)
        if pitch < 60 or any(b - a_ < 0.6 * pitch or b - a_ > 1.4 * pitch for a_, b in zip(xs, xs[1:])):
            continue
        ay = sum(t[1] for t in ans) / len(ans)
        if ay - lab[0][1] > 4 * max(t[2] for t in lab) + 40:
            continue
        readable = [(j, num_of(t[3])) for j, t in enumerate(lt) if len(t[3]) <= 5]
        if prev_y is not None and lab[0][1] - prev_y > 250:
            prev_end = None  # a different table
        s, _ = vote_start(readable, prev_end)
        if s is None:
            continue
        for j, x in enumerate(xs):
            near = [t for t in ans if abs(t[0] - x) <= 0.4 * pitch]
            cells.append((s + j, x, ay, tsv_digit(near[0][3]) if len(near) == 1 else None, pitch))
        prev_end, prev_y, rows = s + len(lt) - 1, ay, rows + 1
    return cells


def read_pairs(lines):
    """Layout 'pairs': consecutive lines of alternating (label, digit). Numbering is row-major (Q1 Q2 Q3 .. along a
    line, the next line continues) or column-major (Q1 Q2 .. down a column); whichever agrees with >= 70% of the
    readable labels (and >= 4 of them) is used."""
    blocks, cur = [], []
    for ln in lines:
        ok = len(ln) >= 4 and len(ln) % 2 == 0 and all(re.fullmatch(r"\D{0,1}\d\D{0,1}", ln[j][3]) for j in range(1, len(ln), 2)) \
            and all(labelish(ln[j][3], True) for j in range(0, len(ln), 2))
        if ok:
            cur.append(ln)
        else:
            if cur:
                blocks.append(cur)
            cur = []
    if cur:
        blocks.append(cur)
    cells = []
    for blk in blocks:
        R, C = len(blk), max(len(r) for r in blk) // 2
        if R < 2 and C < 5:
            continue
        pos = [(r, c, num_of(ln[2 * c][3])) for r, ln in enumerate(blk) for c in range(len(ln) // 2)]
        score = {}
        for name, f in (("row", lambda r, c: r * C + c + 1), ("col", lambda r, c: r + 1 + c * R)):
            tot = sum(n is not None for _, _, n in pos)
            score[name] = (sum(n == f(r, c) for r, c, n in pos), tot)
        best = max(score, key=lambda k: score[k][0])
        ag, tot = score[best]
        if tot < 4 or ag < 0.7 * tot:
            continue
        for r, ln in enumerate(blk):
            for c in range(len(ln) // 2):
                t = ln[2 * c + 1]
                q = r * C + c + 1 if best == "row" else r + 1 + c * R
                cells.append((q, t[0], t[1], tsv_digit(t[3]), 0))
    return cells


QLAB = re.compile(r"^(?:[QqGg@9]\w{0,4}|[Oa0][\dilIszZ]\w{0,2})\W{0,2}$")


def read_slots(lines):
    """Layout 'slots': table lines whose cells are (label, digit) pairs, read by x-position so a garbled or missing
    token costs one cell, not the line. Columns come from the x-clusters of the Q-labels; the digit of column c is the
    token between label c and label c+1. Row r comes from y; numbering is row-major (r*C + c + 1), accepted only
    when >= 70% (and >= 4) of the readable labels agree with it."""
    cells = []
    i = 0
    while i < len(lines):
        j = i
        while j < len(lines) and sum(bool(QLAB.match(t[3])) for t in lines[j]) >= 3 and len(lines[j]) <= 14:
            j += 1
        blk = lines[i:j]
        i = max(j, i + 1)
        if len(blk) < 2:
            continue
        lx = sorted(t[0] for ln in blk for t in ln if QLAB.match(t[3]))
        cl = [[lx[0]]]
        for x in lx[1:]:
            (cl[-1].append(x) if x - cl[-1][-1] < 70 else cl.append([x]))
        cl = [c for c in cl if len(c) >= max(2, 0.4 * len(blk))]
        C = len(cl)
        if C < 3:
            continue
        cx = [sum(c) / len(c) for c in cl]
        pitch = (cx[-1] - cx[0]) / (C - 1)
        ys = [sum(t[1] for t in ln) / len(ln) for ln in blk]
        gaps = sorted(b - a for a, b in zip(ys, ys[1:]))
        rp = gaps[len(gaps) // 2] if gaps else 0
        if rp < 20 or pitch < 100:
            continue
        pos, agree, tot = [], 0, 0
        for ln, y in zip(blk, ys):
            r = round((y - ys[0]) / rp)
            for c in range(C):
                lo, hi = cx[c] - 0.15 * pitch, (cx[c + 1] - 0.15 * pitch) if c + 1 < C else cx[c] + pitch
                lab = [t for t in ln if abs(t[0] - cx[c]) < 0.3 * pitch and QLAB.match(t[3])]
                dg = [t for t in ln if cx[c] + 0.1 * pitch < t[0] < hi - 0.0 * pitch and not QLAB.match(t[3])]
                n = num_of(lab[0][3]) if lab else None
                if n is not None and 1 <= n <= 60:
                    tot += 1
                    agree += n == r * C + c + 1
                pos.append((r * C + c + 1, dg[0] if len(dg) == 1 else None))
        if tot < 4 or agree < 0.7 * tot:
            continue
        for q, t in pos:
            if t is not None:
                cells.append((q, t[0], t[1], tsv_digit(t[3]), 0))
    return cells


NUMTOK = re.compile(r"^\W?[\dOoiIlzZ]{1,3}\W{0,2}$")


def read_numslots(lines):
    """Layout 'numslots': a table of (number, answer) column pairs without Q prefixes ('Qns Ans' tables, '01. 2' lists),
    numbered column-major (the first column holds 1..R). Slots come from the x-clusters of all tokens in the block;
    even slots are numbers, odd slots answers; accepted only when >= 70% (and >= 4) of the readable numbers agree."""
    cells = []
    i = 0
    while i < len(lines):
        j = i
        while j < len(lines) and sum(bool(NUMTOK.match(t[3])) for t in lines[j]) >= 3 and len(lines[j]) <= 14:
            j += 1
        blk = lines[i:j]
        i = max(j, i + 1)
        if len(blk) < 4:
            continue
        xs = sorted(t[0] for ln in blk for t in ln)
        cl = [[xs[0]]]
        for x in xs[1:]:
            (cl[-1].append(x) if x - cl[-1][-1] < 60 else cl.append([x]))
        cl = [c for c in cl if len(c) >= max(3, 0.4 * len(blk))]
        if len(cl) < 4 or len(cl) % 2:
            continue
        cx = [sum(c) / len(c) for c in cl]
        C = len(cx) // 2
        ys = [sum(t[1] for t in ln) / len(ln) for ln in blk]
        gaps = sorted(b - a_ for a_, b in zip(ys, ys[1:]))
        rp = gaps[len(gaps) // 2]
        if rp < 20:
            continue
        rows = [round((y - ys[0]) / rp) for y in ys]
        R = max(rows) + 1
        pos, agree, tot = [], 0, 0
        for ln, r in zip(blk, rows):
            for c in range(C):
                lab = [t for t in ln if abs(t[0] - cx[2 * c]) < 40]
                dg = [t for t in ln if abs(t[0] - cx[2 * c + 1]) < 40]
                n = num_of(lab[0][3]) if len(lab) == 1 else None
                if n is not None:
                    tot += 1
                    agree += n == r + 1 + c * R
                if len(dg) == 1:
                    pos.append((r + 1 + c * R, dg[0]))
        if tot < 4 or agree < 0.7 * tot:
            continue
        cells += [(q, t[0], t[1], tsv_digit(t[3]), 0) for q, t in pos]
    return cells


VARIANTS = ((0.18, 1, "10", 0), (0.30, 2, "10", 0), (0.25, 3, "7", 160))  # crop reads: (half width / pitch, scale, psm, threshold)


def page_words(jpg, scale, y0=0, y1=None):
    """Words of a fresh tesseract run (psm 6) on the page (or a band of it) at the given scale, in page pixels."""
    from PIL import Image
    import subprocess, tempfile
    im = Image.open(jpg).convert("L")
    y1 = y1 or im.height
    band = im.crop((0, max(0, y0), im.width, min(im.height, y1)))
    if scale != 1:
        band = band.resize((int(band.width * scale), int(band.height * scale)), Image.LANCZOS)
    (TMP / "anskey").mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=str(TMP / "anskey")) as td:
        band.save(f"{td}/b.png")
        r = subprocess.run([str(TESS), f"{td}/b.png", "stdout", "--psm", "6", "tsv"], capture_output=True, text=True)
    out = []
    for l in csv.DictReader(io.StringIO(r.stdout), delimiter="\t", quoting=csv.QUOTE_NONE):
        if l["level"] == "5" and l["text"].strip():
            t = l["text"].strip().strip("|[]{}()_.,:;'`")
            if t:
                out.append([(int(l["left"]) + int(l["width"]) / 2) / scale,
                            (int(l["top"]) + int(l["height"]) / 2) / scale + max(0, y0), int(l["height"]) / scale, t])
    return out


def structure(words):
    """(cells, layout): the best of the three layouts on one word list."""
    ls = lines_of(words)
    best, lay = [], None
    for name, fn in (("rows", read_rows), ("pairs", read_pairs), ("slots", read_slots), ("numslots", read_numslots)):
        c = fn(ls)
        if len(c) > len(best):
            best, lay = c, name
    return (best, lay) if len(best) >= 4 else ([], None)


def tok_near(words, x, y):
    near = [t for t in words if abs(t[0] - x) < 45 and abs(t[1] - y) < 35]
    return tsv_digit(near[0][3]) if len(near) == 1 else None


def crop_vote(im, x, y, pitch):
    """Digit that >= 2 of three whitelist-1-4 crop reads agree on, or None."""
    from PIL import Image
    import subprocess, tempfile
    votes = collections.Counter()
    for hwf, sc, psm, thr in VARIANTS:
        hw = int(hwf * pitch) if pitch else 40 + 20 * (sc - 1)
        t = im.crop((int(x - hw), int(y - 45), int(x + hw), int(y + 45)))
        if sc != 1:
            t = t.resize((t.width * sc, t.height * sc), Image.LANCZOS)
        if thr:
            t = t.point(lambda v: 255 if v > thr else 0)
        (TMP / "anskey").mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=str(TMP / "anskey")) as td:
            b = Image.new("L", (t.width + 120, t.height + 120), 255)
            b.paste(t, (60, 60))
            b.save(f"{td}/c.png")
            r = subprocess.run([str(TESS), f"{td}/c.png", "stdout", "--psm", psm, "-c", "tessedit_char_whitelist=1234"],
                               capture_output=True, text=True)
        v = (re.findall(r"[1-4]", r.stdout) or [None])[0]
        if v:
            votes[v] += 1
    top = votes.most_common(1)
    return top[0][0] if top and top[0][1] >= 2 else None


def table_like(words):
    """Cheap prefilter: enough label-ish tokens or short digit tokens to be worth a re-OCR."""
    return sum(bool(QLAB.match(t[3])) for t in words) >= 6


def read_page(tsv_path, jpg_path=None):
    """({qno: digit or '?'}, layout) for one page. The structure comes from the best of the page TSV and two fresh
    OCR runs (psm 6, 1x and 1.5x; only run when the TSV is table-like or empty of a grid). A cell's digit needs >= 2
    agreeing sources among: the three word lists and a three-variant crop vote, and no source may disagree.
    {} when no table-like structure is found."""
    w0 = read_words(tsv_path)
    cells, lay = structure(w0)
    lists = [w0]
    if jpg_path and USE_CROP:
        if len(cells) < 12 and table_like(w0):
            lists += [page_words(jpg_path, 1), page_words(jpg_path, 1.5)]
            for w in lists[1:]:
                c, l = structure(w)
                if len(c) > len(cells):
                    cells, lay = c, l
        elif cells:
            ys = [c[2] for c in cells]
            y0, y1 = int(min(ys) - 200), int(max(ys) + 100)
            lists += [page_words(jpg_path, 1, y0, y1), page_words(jpg_path, 1.5, y0, y1)]
    if not cells:
        return {}, None
    if not (jpg_path and USE_CROP):
        return {q: (d or "?") for q, x, y, d, p in cells}, lay
    from PIL import Image
    im = Image.open(jpg_path).convert("L")
    got = {}
    for q, x, y, d, pitch in cells:
        srcs = [tok_near(w, x, y) for w in lists] + [crop_vote(im, x, y, pitch)]
        seen = [v for v in srcs if v]
        top = collections.Counter(seen).most_common(1)
        v = top[0][0] if top and top[0][1] >= 2 and len(set(seen)) == 1 else "?"
        if v == "?":
            got.setdefault(q, "?")  # unreadable here; a clear read elsewhere may still fill it
        elif got.get(q, "?") in ("?", v):
            got[q] = v
        else:
            got[q] = "!"  # two different clear digits: a real conflict
    return got, lay


def tsv_only(cells):
    return {q: (d or "?") for q, x, y, d, p in cells}


def judge(pages, need):
    """Combine page reads of one paper: ok only when every MCQ number of the paper is read as one digit, repeats agree."""
    ans, layouts = {}, []
    for pn, (g, lay) in pages.items():
        if not g:
            continue
        layouts.append(lay)
        if not all(1 <= q <= 80 for q in g):
            continue
        for q, v in g.items():
            if v == "!":
                ans[q] = "!"
            elif q not in ans or ans[q] == "?":
                ans[q] = v
            elif v != "?" and ans[q] != v:
                ans[q] = "!"  # two different clear digits
    missing = [q for q in need if q not in ans]
    bad = [q for q in need if ans.get(q) in ("?", "!")]
    if not layouts:
        return {"ok": False, "why": "no-grid", "answers": {}}
    if missing or bad:
        return {"ok": False, "why": f"incomplete:missing{len(missing)}/conflict{len(bad)}",
                "answers": {str(q): ans[q] for q in need if q in ans and ans[q] not in ("?", "!")}, "layout": layouts[0]}
    return {"ok": True, "why": None, "answers": {str(q): ans[q] for q in need}, "layout": layouts[0]}


def run(a):
    tot = collections.Counter()
    for y in years(a.years):
        base = Path(a.pp) / a.subject / str(y)
        papers = jl(base / "papers.jsonl")
        mcq = collections.defaultdict(list)
        for q in jl(base / "merged.jsonl"):
            if q.get("format") == "mcq" and isinstance(q.get("qno"), int) and len(q.get("options") or []) == 4:
                mcq[q["paper"]].append(q["qno"])
        order = sorted(papers, key=lambda p: p["first_page"])
        nxt = {p["paper_id"]: (order[i + 1]["first_page"] if i + 1 < len(order) else p["last_page"] + 6)
               for i, p in enumerate(order)}
        out = []
        todo = sorted({pn for p in papers if p["paper_id"] in mcq
                       for pn in (p["answer_pages"] or range(p["first_page"], min(nxt[p["paper_id"]], p["last_page"] + 6)))})
        with multiprocessing.Pool(a.jobs) as pool:
            res = pool.starmap(read_page, [(base / "pages" / f"p{pn:04d}.tsv", base / "pages" / f"p{pn:04d}.jpg") for pn in todo])
        PAGE.update({(y, pn): r for pn, r in zip(todo, res)})
        for p in papers:
            pid = p["paper_id"]
            if pid not in mcq:
                continue
            need = sorted(set(mcq[pid]))
            n = len(need)
            cand = p["answer_pages"] or list(range(p["first_page"], min(nxt[pid], p["last_page"] + 6)))
            pages = {pn: PAGE[y, pn] for pn in cand}
            r = judge(pages, need)
            # a page far from the key (no answer_pages) is only trusted when the paper has no answer page of its own
            r.update(paper=pid, n_mcq=n, coverage=round(len(r["answers"]) / n, 3), pages=[pn for pn, (g, _) in pages.items() if g],
                     from_answer_pages=bool(p["answer_pages"]))
            out.append(r)
            tot[y, "ok" if r["ok"] else r["why"].split(":")[0]] += 1
        with open(base / "anskey_ocr.jsonl", "w") as f:
            for r in out:
                f.write(json.dumps(r) + "\n")
        print(y, {k[1]: v for k, v in tot.items() if k[0] == y})


def compare(a):
    for y in years(a.years):
        base = Path(a.pp) / a.subject / str(y)
        ocr = {r["paper"]: r for r in jl(base / "anskey_ocr.jsonl")}
        c = collections.Counter()
        for q in jl(base / "merged.jsonl"):
            if q.get("format") != "mcq" or not isinstance(q.get("qno"), int):
                continue
            r = ocr.get(q["paper"])
            if not r:
                continue
            o = r["answers"].get(str(q["qno"]))
            e = re.sub(r"[^1-4]", "", str(q.get("answer") or ""))[:1] or None
            if o is None:
                c["not_read"] += 1
                continue
            flag = ("full:" if r["ok"] else "partial:") + (q.get("answer_flag") or "plain")
            if e in (None, ""):
                c["ocr_only"] += 1
            elif e == o:
                c["agree_" + flag] += 1
            else:
                c["differ_" + flag] += 1
        print(y, dict(c))


# ---------------------------------------------------------------- answer pages hidden in the paper's own range

QSTRICT = re.compile(r"^[QqGg9OoCc0@]\s?[0-9iIlLzZoOsS|]{1,2}[.:]?$")
NEAR_END = 8  # pages from the end of the paper where a key usually sits


def page_signals(tsv_path):
    """Cheap evidence of an answer-key page from the TSV words only: {cells (structure() grid cells), qrow (most strict
    Q labels in one line), qdist (distinct label numbers 1-60), qa (lines 'Qn a)'), hdr (header keywords in the first
    14 lines: LEVEL SCHOOL SUBJECT TERM EXAM PAPER YEAR), nw}."""
    w = read_words(tsv_path)
    ls = lines_of(w)
    try:
        cells, _ = structure(w)
    except Exception:
        cells = []
    nums = [num_of(x[3]) for ln in ls for x in ln if QSTRICT.match(x[3])]
    nums = [n for n in nums if n and 1 <= n <= 60]
    head = " ".join(" ".join(x[3] for x in ln) for ln in ls[:14]).upper()
    return {"cells": len(cells), "nw": len(w), "qdist": len(set(nums)),
            "qrow": max([sum(1 for x in ln if QSTRICT.match(x[3])) for ln in ls] or [0]),
            "qa": sum(1 for ln in ls if len(ln) >= 2 and QSTRICT.match(ln[0][3]) and re.fullmatch(r"\(?[a-dA-D][).]?", ln[1][3])),
            "hdr": sum(k in head for k in ("LEVEL", "SCHOOL", "SUBJECT", "TERM", "EXAM PAPER", "YEAR "))}


def is_answer_page(f, near, repeat=False):
    """Strong evidence only. near = the page is among the paper's last NEAR_END pages; repeat = it is not the paper's
    first or second page, so the paper header on it is the key's repeated header, not the cover."""
    if near:
        return (f["cells"] >= 4 or f["qrow"] >= 3 or f["qa"] >= 2 or (f["qdist"] >= 6 and f["hdr"] >= 3)
                or (repeat and f["hdr"] >= 3))
    return f["cells"] >= 8 or (f["hdr"] >= 3 and f["qrow"] >= 3)


def _sig(args):
    return page_signals(args)


def mcq_numbers(base):
    out = collections.defaultdict(set)
    for q in jl(base / "merged.jsonl"):
        if q.get("format") == "mcq" and isinstance(q.get("qno"), int) and len(q.get("options") or []) == 4:
            out[q["paper"]].add(q["qno"])
    return out


def grid_truth(base, pg):
    """True when the listed answer page's ans32 read has >= 8 MCQ cells (qno + one option 1-4/A-D); None without a read."""
    f = base / "ans32" / f"p{pg:04d}.json"
    if not f.exists():
        return None
    try:
        j = json.loads(f.read_text())
    except Exception:
        return None
    n = sum(1 for a in j.get("answers") or []
            if re.fullmatch(r"\(?[1-4A-Da-d]\)?", str(a.get("answer") or "").strip()) and not a.get("sub")
            and re.match(r"\D*\d+\s*$", str(a.get("qno") or "")))
    return n >= 8


def find_answer_pages(a):
    meas = collections.Counter()
    rr = []
    for y in years(a.years):
        base = Path(a.pp) / a.subject / str(y)
        papers = jl(base / "papers.jsonl")
        if not papers:
            continue
        jobs = [(p, pg) for p in papers for pg in range(p["first_page"], p["last_page"] + 1)]
        with multiprocessing.Pool(a.jobs) as pool:
            sig = pool.map(_sig, [base / "pages" / f"p{pg:04d}.tsv" for _, pg in jobs], chunksize=20)
        det = collections.defaultdict(list)
        listed = {p["paper_id"]: set(p["answer_pages"] or []) for p in papers}
        for (p, pg), f in zip(jobs, sig):
            near = pg > p["last_page"] - NEAR_END
            hit = is_answer_page(f, near, pg > p["first_page"] + 1)
            if p["answer_pages"]:  # measurement only: papers that have their own listed pages
                truth, gt = pg in listed[p["paper_id"]], grid_truth(base, pg) if pg in listed[p["paper_id"]] else None
                meas["tp" if hit and truth else "fp" if hit else "fn" if truth else "tn"] += 1
                if gt:
                    meas["grid"] += 1
                    meas["grid_hit"] += hit
            elif hit:
                det[p["paper_id"]].append(pg)
        for p in papers:  # paper-level recall on papers with listed pages and MCQs
            if p["answer_pages"] and p["paper_id"] in mcq_numbers(base) and any(grid_truth(base, g) for g in p["answer_pages"]):
                meas["papers"] += 1
                meas["papers_hit"] += any(is_answer_page(f, pg > q["last_page"] - NEAR_END, pg > q["first_page"] + 1)
                                          for (q, pg), f in zip(jobs, sig) if q is p and pg in listed[p["paper_id"]]
                                          and grid_truth(base, pg))
        found = {pid: sorted(pgs) for pid, pgs in det.items()}
        allp = {p["paper_id"]: listed[p["paper_id"]] | set(found.get(p["paper_id"], [])) for p in papers}
        flag = collections.defaultdict(list)
        for q in jl(base / "merged.jsonl"):
            pgs = q.get("pages") or []
            if pgs and set(pgs) <= allp.get(q.get("paper"), set()):
                flag[q["paper"]].append(q["id"])
        need = mcq_numbers(base)
        if not a.measure:
            (base / "answer_pages_found.json").write_text(json.dumps(found, indent=0))
            (base / "questions_on_answer_pages.json").write_text(json.dumps(flag, indent=0))
        for pid, pgs in found.items():
            for pg in pgs:
                if need.get(pid):
                    rr.append({"subject": a.subject, "year": y, "paper": pid, "page": pg, "n_mcq": len(need[pid]), "mcq": sorted(need[pid])})
        print(y, f"papers_without_pages={sum(1 for p in papers if not p['answer_pages'])} found_for={len(found)} "
              f"pages={sum(len(v) for v in found.values())} questions_on_answer_pages={sum(len(v) for v in flag.values())}")
    if a.measure:
        tp, fp, fn = meas["tp"], meas["fp"], meas["fn"]
        print(f"page precision vs listed answer pages {tp / max(1, tp + fp):.3f}, recall {tp / max(1, tp + fn):.3f} (listed pages include worked solutions);"
              f" grid-page recall {meas['grid_hit']}/{meas['grid']}; paper-level recall {meas['papers_hit']}/{meas['papers']}")
    if a.reread_dir and not a.measure:
        d = Path(a.reread_dir)
        d.mkdir(parents=True, exist_ok=True)
        with open(d / f"pages-{a.subject}.jsonl", "w") as f:
            for r in rr:
                f.write(json.dumps(r) + "\n")
        print(f"reread input: {len(rr)} pages, {sum(r['n_mcq'] for r in rr)} MCQs (counted once per page) -> {d}/pages-{a.subject}.jsonl")


def selftest():
    def tsv(rows):  # rows: [(y, [(x, text)])]
        return [[x, y, 30, t] for y, ws in rows for x, t in ws]
    lab1 = [(200 + 200 * i, t) for i, t in enumerate(["Qi", "Q2", "G3", "a4", "Q5"])]
    ans1 = [(200 + 200 * i, d) for i, d in enumerate("42134")]
    lab2 = [(200 + 200 * i, t) for i, t in enumerate(["Q6", "Q7", "Q8", "ais", "Q10"])]
    ans2 = [(200 + 200 * i, d) for i, d in enumerate(["3", "1", "2", "4°", "5"])]
    ls = lines_of(tsv([(100, lab1), (160, ans1), (300, lab2), (360, ans2)]))
    c = read_rows(ls)
    g = tsv_only(c)
    assert [g[i] for i in range(1, 6)] == list("42134"), g
    assert [g[i] for i in range(6, 9)] == list("312") and g[9] == "4" and g[10] == "?", g  # '4°' -> 4, '5' unreadable
    # a missing answer token leaves its cell for the crop reader (None), the page still has all 5 cells
    c = read_rows(lines_of(tsv([(100, lab1), (160, ans1[:4])])))
    assert len(c) == 5 and c[4][3] is None
    # a text line above a digit line is not a grid
    txt = [(100, [(100, "The"), (300, "bulb"), (500, "is"), (700, "lit")]), (160, [(100, "1"), (300, "2")])]
    assert read_rows(lines_of(tsv(txt))) == []
    # pairs layout, 3 rows, 2 columns, plain numbers
    pr = [(100, [(100, "1"), (200, "4"), (400, "4"), (500, "1")]),
          (160, [(100, "2"), (200, "3"), (400, "5"), (500, "2")]),
          (220, [(100, "3"), (200, "2"), (400, "6"), (500, "3")])]
    g = tsv_only(read_pairs(lines_of(tsv(pr))))
    assert [g[i] for i in range(1, 7)] == list("432123"), g
    # judge: complete, then one missing, then a conflict across pages
    pg = {1: ({i: "1" for i in range(1, 7)}, "rows")}
    assert judge(pg, range(1, 7))["ok"] and not judge(pg, range(1, 9))["ok"]
    pg[2] = ({3: "2"}, "rows")
    assert not judge(pg, range(1, 7))["ok"]
    # '?' never blocks a later clear read; two different clear digits do
    pg = {1: ({1: "?", 2: "1"}, "rows"), 2: ({1: "3", 2: "?"}, "rows")}
    r = judge(pg, [1, 2])
    assert r["ok"] and r["answers"] == {"1": "3", "2": "1"}, r
    pg = {1: ({1: "3"}, "rows"), 2: ({1: "?"}, "rows")}
    assert judge(pg, [1])["ok"]
    pg = {1: ({1: "3"}, "rows"), 2: ({1: "2"}, "rows"), 3: ({1: "3"}, "rows")}
    assert not judge(pg, [1])["ok"]
    # a line of bare answer digits is not label/digit pairs
    assert not any(labelish(t) for t in "1 3 2 4 1 2".split())  # bare answer digits are never labels by default
    assert read_pairs(lines_of(tsv([(100, [(100 + 100 * i, d) for i, d in enumerate("132412")])]))) == []
    assert labelish("Q3") and not labelish("3") and labelish("3", True)
    # answer-page evidence: a Q grid with its header counts, a prose page does not; far pages need a stronger sign
    assert is_answer_page({"cells": 5, "qrow": 0, "qa": 0, "qdist": 0, "hdr": 0}, True)
    assert not is_answer_page({"cells": 5, "qrow": 4, "qa": 0, "qdist": 5, "hdr": 0}, False)
    assert is_answer_page({"cells": 0, "qrow": 3, "qa": 0, "qdist": 3, "hdr": 3}, False)
    assert not is_answer_page({"cells": 0, "qrow": 1, "qa": 1, "qdist": 2, "hdr": 3}, True)
    assert is_answer_page({"cells": 0, "qrow": 0, "qa": 0, "qdist": 0, "hdr": 3}, True, True)
    assert not is_answer_page({"cells": 0, "qrow": 0, "qa": 0, "qdist": 0, "hdr": 3}, False, True)
    print("selftest ok")


def main():
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers(dest="cmd", required=True)
    for n in ("run", "compare"):
        s = sp.add_parser(n)
        s.add_argument("--subject", default="science")
        s.add_argument("--years", default="2018-2024")
        s.add_argument("--pp", default=str(DEF_PP))
        s.add_argument("--jobs", type=int, default=24)
    s = sp.add_parser("find-answer-pages")
    s.add_argument("--subject", default="science")
    s.add_argument("--years", default="2018-2026")
    s.add_argument("--pp", default=str(DEF_PP))
    s.add_argument("--jobs", type=int, default=24)
    s.add_argument("--reread-dir", default=None)
    s.add_argument("--measure", action="store_true")
    sp.add_parser("selftest")
    a = ap.parse_args()
    {"run": run, "compare": compare, "find-answer-pages": find_answer_pages, "selftest": lambda a: selftest()}[a.cmd](a)


if __name__ == "__main__":
    main()
