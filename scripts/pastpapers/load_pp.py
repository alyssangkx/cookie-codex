"""Private import of verbatim past-paper MCQs (ADR 0004). Reads and writes ONLY outside the repo.

  load_pp.py select  [--subject science] [--years 2018-2026] [--pp DIR] [--blind DIR] [--out DIR]
      Picks the importable MCQs and writes OUT/<subject>/selected.jsonl (private rows), rejects.jsonl (id + reason)
      and report.json (counts only). Rules: exactly 4 options; an answer key; not in the quarantine; not
      answer_flag grid-uncertain (with --ocr-keys: unless a full anskey_ocr.jsonl row reads the same key, and a missing
      key is taken from a full row; only rows read from the paper's own answer pages count, a partial row can only
      contradict a key; the row's answer_src says which). Order for OCR-only keys: anskey_ocr.py run -> blind check with
      OCR keys (run_blind_ocr.sh under /data/alvin/tmp/cookie-codex/anskey/) -> select --ocr-keys; an OCR-only item
      absent from that blind file is rejected as needs-blind-check-ocr; --reread-keys does the same with the cells on which
      two independent VL-32B reads of the key page agree (ans_reread.py; answer_src 'vision-reread', same blind check); the blind-answer check agrees with the key, or the second solver (--blind2: VL-32B at
      full resolution AND the 72B on the transcribed figure text) both reach it; text and options not garbled; options
      not only in the picture; a sub-topic that exists in the site's syllabus; and a usable crop whenever the stem
      points at a figure, table or graph (or labels such as A/B/P/Q) or the reader saw a figure.
  load_pp.py where <question id> [--out DIR]
      Where a reported question (question_reports, migration 005) comes from: paper, PDF file and page, crops, text, key,
      and any hold file naming it. A generated id prints its bank and stem.
  load_pp.py figures [--subject science] [--out DIR] [--max-width 900] [--target-kb 60]
      Compresses each selected item's crops to WebP (grayscale when the crop has no colour) into
      OUT/<subject>/figures/ and writes figures.jsonl {pp_id, path, w, h, bytes}.
      Before compressing, a crop whose ink touches an edge is grown to the surrounding whitespace (located in its page scan;
      grow_to_whitespace) and a page rotated 0.3-3 degrees is straightened (deskew). `load_pp.py selftest` checks both.
  load_pp.py review  [--subject science] [--out DIR] --subtopics a,b
      Writes OUT/<subject>/review-<first sub-topic>.html (private, local only): every selected item of those
      sub-topics with its pictures, options and key, for the visual review before a switch. Put the pp id of any item
      that fails on its own line in OUT/<subject>/hold.txt (or let the server crop review write hold-auto.txt); `select` and
      `upload` then leave it out.
  load_pp.py cropcheck-apply RESULTS [--subject science] [--out DIR]
      Writes OUT/<subject>/hold-auto.txt (id + short reason as a comment) from the server crop review's results.jsonl
      (scripts/pastpapers/cropcheck.py). `select` and `upload` read it like hold.txt.
  load_pp.py upload  [--subject science] [--out DIR] [--subtopics a,b] [--apply]
      Upserts rows into public.pp_items and uploads the WebP files to the private bucket pp-figures. Without
      --apply it only prints what it would do. Needs SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY in the environment;
      the key is never printed. Run only after the owner says "apply" (migration 004 must be applied first).

  load_pp.py counts  [--subject science] [--out DIR] [--subtopics a,b]
      Writes site/src/data/pp_counts.json ({"<sub>|<tier letter>": n}, numbers only, no ids or content) from the rows
      `upload` would send, without uploading. `upload --apply` writes it too. train.ts uses it for the tier counts.
  upload also sets active=false on existing pp_items rows of each uploaded sub-topic that are not in this upload
  (held, dropped by select, or re-tagged away). A held row is never re-activated. Dry run reports how many (needs the
  Supabase env to look; else says it cannot count).

Ids: pp-<sha1(source question id)[:10]>. The sub-topic is NOT part of the id, so a re-tag keeps saves and retests.
Nothing here prints question text, options or answers: counts and ids only.
"""
import argparse, collections, hashlib, json, os, re, sys
from pathlib import Path

import cropcheck  # fig_ok, pack_stamp: the per-figure pass rule and pack identity are shared

REPO = Path(__file__).resolve().parents[2]
TMP = Path("/data/alvin/tmp/cookie-codex")
DEF_PP, DEF_BLIND, DEF_OUT = TMP / "pastpapers", TMP / "audit" / "blindcheck", TMP / "ppimport"
DEF_BLIND2 = DEF_BLIND / "second"  # queue 9: second local solver; recovers a failure only when both its routes reach the key
LEVEL = {1: "basic", 2: "intermediate", 3: "competent"}
LATE = 0.6  # tier rule "position": a difficulty-2 item in the last 40% of its booklet's MCQs counts as Competent


def tier(difficulty: int, qno, booklet_mcqs: int, rule: str) -> str:
    """Tags rate almost no Science MCQ as difficulty 3, so rule 'tags' leaves Competent empty; 'position' (default)
    keeps difficulty 1 = Basic and splits difficulty 2 by where the item sits in its booklet (papers run easy to hard)."""
    if rule == "tags" or difficulty != 2:
        return LEVEL[difficulty]
    return "competent" if (qno or 0) / max(booklet_mcqs, 1) >= LATE else "intermediate"
BUCKET = "pp-figures"

# a stem that points at something drawn: words, or a label letter (B-Z except I; "A" only beside and/or/commas)
FIG_WORDS = re.compile(r"\b(shown|show(s)? (below|above)|below|above|diagram|figure|table|graph|chart|picture|"
                       r"set-?up|illustrat\w*|drawing|labelled|marked)\b", re.I)
FIG_LETTER = re.compile(r"(?<![A-Za-z'])[B-HJ-Z](?![A-Za-z'])|\bA(?=\s*,|\s+(and|or)\b)|\b(?:and|or)\s+A\b|\bA\b(?=\s*(only|and))")


HEADER = re.compile(r"([A-Za-z][a-z]{2,}(?: [a-z]{2,})?) ([A-Z])")


def outside_repo(p: Path) -> Path:
    p = p.resolve()
    if p == REPO or REPO in p.parents:
        sys.exit(f"refusing to write inside the repo: {p}")
    return p


def jl(p):
    p = Path(p)
    return [json.loads(l) for l in open(p)] if p.exists() else []


def years(spec: str):
    a, _, b = spec.partition("-")
    return list(range(int(a), int(b or a) + 1))


def pp_id(src_id: str) -> str:
    return "pp-" + hashlib.sha1(src_id.encode()).hexdigest()[:10]


def key(a, opts):
    """The answer as '1'..'4' (same rule as the blind check's key())."""
    a = str(a or "").strip()
    if not a:
        return None  # no key (an empty answer must not match an option that is empty after its "(n)")
    m = re.fullmatch(r"\(?([1-4])\)?", a)
    if m:
        return m.group(1)
    m = re.fullmatch(r"\(?([A-Da-d])\)?", a)
    if m:
        return str("ABCD".index(m.group(1).upper()) + 1)
    for i, o in enumerate(opts, 1):
        if re.sub(r"^\s*\(\d\)\s*", "", o).strip() == a:
            return str(i)
    return None


def strip_num(o: str) -> str:
    return re.sub(r"^\s*\(\d\)\s*", "", o).strip()


def realfig(q):
    return any(isinstance(f, str) and f and f.lower() not in ("none", "null") for f in (q.get("figures") or []))


FIG_WORDS_LANG = re.compile(r"\b(picture|diagram|chart|graph|poster|map|timetable|table (below|above)|the table)\b|图|表格", re.I)
BLANK_PUNCT = set("_.,;:?!'\"()[]-…—–·。，、；：？！“”‘’（）《》〈〉【】「」")
LETTERED = re.compile(r"\(?([A-D])(?:[.)]\s*|\s+(?![\s&+,]|and\b|or\b|only\b))")  # "A. Air" / "A Air", not "A and X only"


def garbled(text: str, opts) -> str | None:
    t = text or ""
    # a CJK character carries about a word: 8 of them make a full Chinese stem (黑衣人是一个怎么样的人？), 20 letters an English one
    cjk = sum("\u3400" <= c <= "\u9fff" for c in t)
    if len(t.strip()) + 2 * cjk < 20:
        return "text-short"
    if "�" in t or any("�" in o for o in opts):
        return "text-replacement-char"
    # answer blanks (____) and punctuation are not noise: judge only the other characters
    body = [c for c in t if not c.isspace() and c not in BLANK_PUNCT]
    if sum(c.isalpha() for c in body) < 8:
        return "text-short"  # mostly blanks or dots: no real stem left
    if sum(c.isalpha() for c in body) / (len(body) or 1) < 0.6:
        return "text-low-alpha"
    if re.search(r"([A-Za-z])\1{4,}", t):
        return "text-letter-run"
    s = [strip_num(o) for o in opts]
    if all(x == "" for x in s):
        return "options-in-picture"
    if any(x == "" for x in s) or len(set(s)) < 4:
        return "options-duplicate-or-empty"
    if any(len(x) > 300 for x in s):
        return "option-too-long"
    # a table read as options: its column headers ("Substance R", "Tube W") instead of the rows (review, 20 Nov)
    m = [HEADER.fullmatch(x) for x in s]
    if all(m) and len({x.group(1).lower() for x in m}) > 1:
        return "options-are-table-headers"
    # statements A-D read as the options: the paper's real options are combinations ("(1) B and D only") printed after
    # them, so the stored options and key are wrong (owner spot-check, 21 Nov: pp-3f46ebd0cf). PSLE options are (1)-(4).
    if all((m := LETTERED.match(o or "")) and m.group(1) == "ABCD"[i] for i, o in enumerate(opts)):
        return "options-are-statements"
    return None


def syllabus_subs(subject: str) -> set:
    out = set()

    def walk(n):
        if isinstance(n, dict):
            if isinstance(n.get("outcomes"), list) and "id" in n:
                out.add(n["id"])
            for v in n.values():
                if isinstance(v, (list, dict)):
                    walk(v)
        elif isinstance(n, list):
            for x in n:
                walk(x)
    walk(json.load(open(REPO / "site" / "src" / "data" / "syllabus" / f"{ {'maths': 'math'}.get(subject, subject)}.json")))
    return out


def crop_ok(path: Path) -> bool:
    from PIL import Image, ImageStat
    try:
        with Image.open(path) as im:
            w, h = im.size
            if w < 120 or h < 60:
                return False
            g = im.convert("L")
            g.thumbnail((300, 300))
            return ImageStat.Stat(g).stddev[0] > 8  # not a blank strip
    except Exception:
        return False


def parse_hold(text: str) -> set:
    return {l.split("#")[0].strip() for l in text.splitlines() if l.split("#")[0].strip()}


def read_hold(out: Path) -> set:
    """hold.txt (visual review), hold-auto.txt (cropcheck-apply, the server model's crop review) and hold-crop.txt
    (`figures`: a crop still cut off at an edge after the automatic fixes)."""
    return set().union(*(parse_hold(open(out / n).read()) for n in HOLD_FILES if (out / n).exists()))


HOLD_FILES = ("hold.txt", "hold-auto.txt", "hold-crop.txt")
BLIND_RERUN = ("needs-blind-check-ocr", "no-blind-check-yet", "not-in-blind-check", "blind-key-mismatch")  # fixed by a blind run with the current key
UNRESOLVED = ("not_located", "touch_unresolved", "no_page")  # fix_crop outcomes that leave a crop possibly cut off


def hold_auto_text(rows, expected_ids=None) -> str:
    """hold-auto.txt from cropcheck results rows {id, ok, figs:[{n, complete, ..., reason}]}: one line per failed item."""
    lines = ["# written by `load_pp.py cropcheck-apply` from the server crop review; read like hold.txt. Do not edit: re-apply overwrites."]
    for i in sorted(set(expected_ids or ()) - {r["id"] for r in rows}):  # no result (crashed shard, partial merge): held
        lines.append(f"{i}  # not checked")
    for r in rows:
        if r.get("ok"):
            continue
        why = next((f.get("reason", "") for f in r.get("figs", []) if not cropcheck.fig_ok(f)), "")
        flags = [k for k in ("complete", "belongs_to_question") if any(f.get(k) is False for f in r.get("figs", []))]
        flags += ["contains_other_question"] if any(f.get("contains_other_question") is True for f in r.get("figs", [])) else []
        lines.append(f"{r['id']}  # {','.join(flags) or 'failed'}: {' '.join(why.split())[:100]}")
    return "\n".join(lines) + "\n"


def cropcheck_apply(a):
    out = outside_repo(Path(a.out)) / a.subject
    allrows = jl(a.arg)
    expected = [it["id"] for it in jl(cropcheck.PACK / "items.jsonl")]
    # an item selected after the pack was built has no result either: hold it too (only science packs exist today)
    expected += [r["id"] for r in jl(out / "selected.jsonl") if r.get("crops") and r["id"] not in set(expected)]
    if not allrows or not expected:
        sys.exit("no results rows in " + str(a.arg) + " or no pack at " + str(cropcheck.PACK))
    rows = cropcheck.stamped(allrows, cropcheck.pack_stamp(cropcheck.PACK))  # results of another pack count as missing
    (out / "hold-auto.txt").write_text(hold_auto_text(rows, expected))
    bad = sum(not r.get("ok") for r in rows)
    missing = len(set(expected) - {r["id"] for r in rows})
    print(f"{len(expected)} in pack: {len(rows)} checked, {bad} failed, {missing} missing (held as 'not checked') -> {out / 'hold-auto.txt'}")


# ------------------------------------------------------------------ select

OCR_COVER = 0.6  # anskey_ocr.py alone supplies a key only for a paper whose grid read covers this share of its MCQs


def ocr_keys(base: Path) -> dict:
    """{(paper, qno): (digit '1'-'4', full)} from <year>/anskey_ocr.jsonl (scripts/pastpapers/anskey_ocr.py). Only rows
    read from the paper's own answer pages (from_answer_pages) with coverage >= OCR_COVER are used; a row read from
    question pages never fills or contradicts a key. full = the row is ok (no conflict, every MCQ read): only a full
    row may fill a missing key or clear grid-uncertain; a partial one may only contradict a key. Empty when the file
    does not exist."""
    out = {}
    for r in jl(base / "anskey_ocr.jsonl"):
        if r.get("from_answer_pages") is True and r.get("n_mcq") and len(r.get("answers") or {}) >= OCR_COVER * r["n_mcq"]:
            for qn, d in r["answers"].items():
                if d in ("1", "2", "3", "4"):
                    out[(r["paper"], int(qn))] = (d, r.get("ok") is True)
    return out


def reread_keys(base: Path) -> dict:
    """{(paper, qno): digit '1'-'4'} from <year>/ansreread/pNNNN.json (ans_reread.py, two independent VL-32B reads): only
    cells whose two reads agree (final), on a page the run gate (ans_reread.gate, recomputed here so a file written by an
    older gate is judged by the current one) does not flag. Empty when the folder does not exist."""
    from ans_reread import gate
    out = {}
    for f in sorted((base / "ansreread").glob("p*.json")):
        try:
            j = json.loads(f.read_text())
        except Exception:
            continue
        if gate({int(n): c["final"] for n, c in (j.get("cells") or {}).items() if c.get("final") in ("1", "2", "3", "4")}):
            continue
        for qn, c in (j.get("cells") or {}).items():
            if c.get("final") in ("1", "2", "3", "4") and c.get("a") == c.get("b") == c["final"]:
                if out.get((j["paper"], int(qn)), c["final"]) != c["final"]:
                    out[(j["paper"], int(qn))] = None  # two pages disagree: no key
                else:
                    out[(j["paper"], int(qn))] = c["final"]
    return {k: v for k, v in out.items() if v}


def on_answer_pages(base: Path) -> set:
    """Question ids whose pages all lie on the paper's answer pages (anskey_ocr.py find-answer-pages writes
    <year>/questions_on_answer_pages.json): rows of the key, not questions. Empty when the file does not exist."""
    f = base / "questions_on_answer_pages.json"
    return {i for ids in json.loads(f.read_text()).values() for i in ids} if f.exists() else set()


def select(a):
    out = outside_repo(Path(a.out)) / a.subject
    out.mkdir(parents=True, exist_ok=True)
    subs = syllabus_subs(a.subject)
    quar = {r["id"] for r in jl(Path(a.pp) / "quarantine.jsonl")}
    hold = read_hold(out)
    rows, rejects = [], []
    R = collections.Counter()
    per_year = collections.defaultdict(collections.Counter)
    for y in years(a.years):
        base = Path(a.pp) / a.subject / str(y)
        tags = {t["id"]: t for t in jl(base / "tags72.jsonl")}
        bfile = Path(a.blind) / f"{a.subject}-{y}.jsonl"
        blind = {b["id"]: b for b in jl(bfile)} if bfile.exists() else None
        second = {b["id"]: b for b in jl(Path(a.blind2) / f"{a.subject}-{y}.jsonl")}
        merged = jl(base / "merged.jsonl")
        ocrk = ocr_keys(base) if a.ocr_keys else {}
        rrk = reread_keys(base) if a.reread_keys else {}
        onans = on_answer_pages(base)
        last = collections.Counter()  # (paper, part) -> highest MCQ number
        for q in merged:
            if q.get("format") == "mcq" and isinstance(q.get("qno"), int):
                last[(q.get("paper"), q.get("part"))] = max(last[(q.get("paper"), q.get("part"))], q["qno"])
        crops = collections.defaultdict(list)
        for c in sorted((base / "crops").glob("*.png")):
            crops[re.sub(r"-p\d+\.png$", "", c.name)].append(c)
        for q in merged:
            if q.get("format") != "mcq":
                continue
            opts = q.get("options") or []
            k = key(q.get("answer"), opts) if len(opts) == 4 else None
            t = tags.get(q["id"]) or {}
            reason = None
            ok, full = ocrk.get((q.get("paper"), q.get("qno")), (None, False))
            src = "vision"
            conflict = False
            if len(opts) == 4 and ok:
                if not k and full:
                    k, src = ok, "ocr"
                elif k and k != ok:
                    conflict = True  # judged below, after the quarantine and hold checks
                elif k and full and q.get("answer_flag") == "grid-uncertain":
                    q = dict(q, answer_flag=None)  # two independent strong reads agree
                    src = "vision+ocr"
            rr = rrk.get((q.get("paper"), q.get("qno")))
            if len(opts) == 4 and rr:
                if not k:
                    k, src = rr, "vision-reread"
                elif k != rr:
                    conflict = True
                elif q.get("answer_flag") == "grid-uncertain" and src == "vision":
                    q = dict(q, answer_flag=None)  # a second, independent two-read agreement
                    src = "vision+reread"
            if len(opts) == 4 and ok and k and k != ok:
                conflict = True  # also catches a partial OCR read against a key the reread supplied
            if len(opts) != 4:
                reason = "not-4-options"
            elif q["id"] in onans:
                reason = "on-answer-page"  # every page it sits on is the paper's answer key
            elif not k:
                reason = "no-answer-key"
            elif q["id"] in quar:
                reason = "quarantined"
            elif pp_id(q["id"]) in hold:
                reason = "held-by-review"
            elif q.get("answer_flag") == "grid-uncertain":
                reason = "grid-uncertain"
            elif conflict:
                reason = "ocr-key-conflict"
            elif src in ("ocr", "vision-reread") and (blind is None or q["id"] not in blind or blind[q["id"]].get("key") != k):
                reason = "needs-blind-check-ocr"  # a blind file made with OCR keys must contain it
            elif blind is None:
                reason = "no-blind-check-yet"
            elif q["id"] not in blind:
                reason = "not-in-blind-check"
            elif blind[q["id"]].get("key") != k:
                reason = "blind-key-mismatch"  # the key changed after the blind run: re-run it
            elif blind[q["id"]].get("agree") is not True and not (
                    second.get(q["id"], {}).get("agree2") is True and second[q["id"]].get("key") == k):
                reason = "blind-unparsed" if blind[q["id"]].get("pick") is None else "blind-disagree"
            else:
                reason = garbled(q.get("text") or "", opts)
                if not reason and t.get("st") not in subs:
                    reason = "subtopic-not-in-syllabus"
                if not reason and t.get("difficulty") not in LEVEL:
                    reason = "no-difficulty"
                if not reason:
                    # letter labels (A, P, X) and "below" point at a figure only in Science and Maths; in English and Chinese a
                    # capital is just a word ("The") and "below" a sentence, so there only an explicit picture word or a figure the
                    # reader saw counts (21 Nov 2026)
                    refers = (bool(FIG_WORDS.search(q["text"]) or FIG_LETTER.search(q["text"]) or any(FIG_LETTER.search(strip_num(o)) for o in opts))
                              if a.subject in ("science", "maths") else bool(FIG_WORDS_LANG.search(q["text"])))
                    if refers or realfig(q):
                        usable = [c for c in crops.get(q["id"], []) if crop_ok(c)]
                        good = own_page_crops(usable, q.get("pages"))
                        if not crops.get(q["id"]):
                            reason = "needs-figure-no-crop"
                        elif not usable:
                            reason = "crop-unusable"
                        elif not good:
                            reason = "crop-other-page"
                        else:
                            q["_crops"] = [str(c) for c in good]
                    else:
                        q["_crops"] = []
            per_year[y]["mcq"] += 1
            if reason:
                R[reason] += 1
                per_year[y][reason] += 1
                rejects.append({"id": q["id"], "reason": reason, **({"answer_src": src} if src != "vision" else {}),
                                **({"key": k} if reason in BLIND_RERUN else {})})  # input for a blind run
                continue
            per_year[y]["selected"] += 1
            rows.append({
                "id": pp_id(q["id"]), "src_id": q["id"], "subject": a.subject, "subtopic": t["st"],
                "level": tier(t["difficulty"], q.get("qno"), last[(q.get("paper"), q.get("part"))], a.tier_rule),
                "difficulty": t["difficulty"], "pattern": t.get("pat"),
                "stem": q["text"].strip(), "options": [strip_num(o) for o in opts], "answer": int(k) - 1,
                "answer_src": src, "crops": q["_crops"], "year": y, "school": q.get("school"), "paper": q.get("paper"),
                "part": q.get("part"), "qno": q.get("qno"), "marks": q.get("marks"),
                "blind_src": (blind[q["id"]].get("src") or "blind") if blind[q["id"]].get("agree") is True
                else "second:vl2-fullres+text72-ocr",
            })
    ids = [r["id"] for r in rows]
    assert len(ids) == len(set(ids)), "pp id collision"
    with open(out / "selected.jsonl", "w") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    with open(out / "rejects.jsonl", "w") as f:
        for r in rejects:
            f.write(json.dumps(r) + "\n")
    by = collections.defaultdict(collections.Counter)
    for r in rows:
        by[r["subtopic"]][r["level"]] += 1
    report = {"subject": a.subject, "years": a.years, "selected": len(rows), "rejected": dict(R.most_common()),
              "per_year": {str(y): dict(c) for y, c in sorted(per_year.items())},
              "by_subtopic": {s: dict(c) for s, c in sorted(by.items())},
              "with_figure": sum(bool(r["crops"]) for r in rows), "crops": sum(len(r["crops"]) for r in rows)}
    (out / "report.json").write_text(json.dumps(report, indent=1))
    print(f"selected {len(rows)}; with figure {report['with_figure']} ({report['crops']} crops); rejected", dict(R.most_common()))


# ------------------------------------------------------------------ figures

def is_gray(im) -> bool:
    from PIL import ImageChops
    if im.mode in ("L", "LA", "1"):
        return True
    rgb = im.convert("RGB")
    rgb.thumbnail((400, 400))
    r, g, b = rgb.split()
    spread = max(ImageChops.difference(r, g).getextrema()[1], ImageChops.difference(g, b).getextrema()[1])
    if spread <= 24:
        return True
    # scanner fringes: colour only in a handful of pixels
    d = ImageChops.difference(r, g).point(lambda v: 255 if v > 40 else 0)
    return sum(d.histogram()[255:]) / (rgb.width * rgb.height) < 0.002


def compress(src: Path, dst: Path, max_w: int, target: int):
    from PIL import Image
    import io
    with Image.open(src) as im:
        im.load()
        im = im.convert("L") if is_gray(im) else im.convert("RGB")
        if im.width > max_w:
            im = im.resize((max_w, round(im.height * max_w / im.width)), Image.LANCZOS)
        while True:
            for q in (80, 70, 60, 50, 42):
                buf = io.BytesIO()
                im.save(buf, "WEBP", quality=q, method=6)
                if buf.tell() <= target:
                    break
            if buf.tell() <= target or im.width <= 520:
                break
            im = im.resize((int(im.width * 0.85), int(im.height * 0.85)), Image.LANCZOS)
        dst.write_bytes(buf.getvalue())
        return im.width, im.height, buf.tell(), im.mode


DARK = 140        # grey level below which a pixel is ink
BLANK_BAND = 25   # blank rows/columns that end a figure (the gap between a stem line and its figure is wider)
GROW_PAD = 10     # blank pixels kept beyond the last ink when an edge is pushed out
GROW_CAP = 0.40   # a top/bottom edge never moves more than this share of the page's height
GROW_CAP_X = 0.12  # left/right: share of the page width (a crop wider than its figure only touches text lines)
SKEW_MAX, SKEW_STEP, SKEW_MIN = 3.0, 0.1, 0.3
SKEW_GAIN = 1.15  # variance of the projection must rise 15% (a noisy peak on a figure without straight lines is not skew)


def touches(g):
    """Edges of the grey array g where ink touches the border (a speck of noise, < 2 dark pixels, does not count)."""
    d = g < DARK
    return {"top": d[:2].sum() >= 2, "bottom": d[-2:].sum() >= 2, "left": d[:, :2].sum() >= 2, "right": d[:, -2:].sum() >= 2}


def locate(page, crop):
    """(x, y) of the crop inside the page (both grey uint8 arrays, same pixel scale), or None. Coarse FFT match on a
    4x downsample, then an exact search of +-6 px at full size; accepted only when the mean absolute difference < 12."""
    import numpy as np
    H, W = page.shape
    h, w = crop.shape
    if h >= H or w >= W:
        return None

    def down(a, f=4):
        hh, ww = a.shape[0] // f * f, a.shape[1] // f * f
        return a[:hh, :ww].reshape(hh // f, f, ww // f, f).mean(axis=(1, 3)).astype(np.float32)
    P, T = down(page), down(crop)
    ph, pw = P.shape
    th, tw = T.shape
    if th < 8 or tw < 8:
        return None
    fh, fw = ph + th, pw + tw
    corr = np.fft.irfft2(np.fft.rfft2(P, (fh, fw)) * np.conj(np.fft.rfft2(T, (fh, fw))), (fh, fw))[:ph - th + 1, :pw - tw + 1]
    ii = np.pad((P.astype(np.float64) ** 2).cumsum(0).cumsum(1), ((1, 0), (1, 0)))
    win = ii[th:, tw:][:ph - th + 1, :pw - tw + 1] - ii[:ph - th + 1, tw:][:, :pw - tw + 1] \
        - ii[th:, :pw - tw + 1][:ph - th + 1] + ii[:ph - th + 1, :pw - tw + 1]
    ssd = win - 2 * corr
    cy, cx = np.unravel_index(int(np.argmin(ssd)), ssd.shape)
    best = (1e9, None)
    cf = crop.astype(np.int16)
    for y in range(max(cy * 4 - 6, 0), min(cy * 4 + 7, H - h + 1)):
        for x in range(max(cx * 4 - 6, 0), min(cx * 4 + 7, W - w + 1)):
            m = float(np.abs(page[y:y + h, x:x + w].astype(np.int16) - cf).mean())
            if m < best[0]:
                best = (m, (x, y))
    return best[1] if best[0] < 12 else None


def grow_to_whitespace(page, box, cap=GROW_CAP, cap_x=GROW_CAP_X):
    """page: grey uint8 array. box: (x0, y0, x1, y1) of the crop in the page. For each edge where ink touches the border,
    push it outward until BLANK_BAND blank rows (columns, within the box's span) or the page margin, at most cap of
    the page's height (width); GROW_PAD blank pixels are kept past the last ink. An edge with no such band inside the
    cap stays. Returns (new_box, {edge: px}). The band stops it at the gap between a stem line and its figure."""
    import numpy as np
    H, W = page.shape
    x0, y0, x1, y1 = box
    grown = {}
    d = page < DARK
    t = touches(page[y0:y1, x0:x1])

    def run(counts, start, step, limit):
        """counts[i] = ink pixels of line i; walk from start in direction step; return how many lines the edge must move
        to cover the ink before the blank band that ends the figure (0 = no ink beyond the edge), or None."""
        blank, last_ink, i = 0, -1, start
        while 0 <= i < len(counts) and abs(i - start) <= limit:
            if counts[i] >= 2:
                blank, last_ink = 0, i
            else:
                blank += 1
                if blank >= BLANK_BAND:
                    return last_ink + 1
            i += step
        if not (0 <= i < len(counts)):  # reached the page margin through blank lines
            return last_ink + 1
        return None
    rows = lambda a, b, c, e: d[a:b, c:e].sum(axis=1)
    cols = lambda a, b, c, e: d[a:b, c:e].sum(axis=0)
    if t["top"]:
        r = run(rows(0, y0, x0, x1)[::-1], 0, 1, int(cap * H))
        if r is not None:
            ny = max(y0 - r - GROW_PAD, 0) if r else y0
            if ny < y0:
                grown["top"] = y0 - ny
                y0 = ny
    if t["bottom"]:
        r = run(rows(y1, H, x0, x1), 0, 1, int(cap * H))
        if r is not None:
            ny = min(y1 + r + GROW_PAD, H) if r else y1
            if ny > y1:
                grown["bottom"] = ny - y1
                y1 = ny
    if t["left"]:
        r = run(cols(y0, y1, 0, x0)[::-1], 0, 1, int(cap_x * W))
        if r is not None:
            nx = max(x0 - r - GROW_PAD, 0) if r else x0
            if nx < x0:
                grown["left"] = x0 - nx
                x0 = nx
    if t["right"]:
        r = run(cols(y0, y1, x1, W), 0, 1, int(cap_x * W))
        if r is not None:
            nx = min(x1 + r + GROW_PAD, W) if r else x1
            if nx > x1:
                grown["right"] = nx - x1
                x1 = nx
    return (x0, y0, x1, y1), grown


def estimate_skew(g):
    """Angle (degrees, counter-clockwise as PIL rotate() takes it) in [-SKEW_MAX, SKEW_MAX] that maximises the variance of
    the horizontal ink projection on a downsampled copy; 0.0 when the variance gain over no rotation is under 15%."""
    import numpy as np
    from PIL import Image
    im = Image.fromarray(g)
    s = 700 / max(im.size)
    if s < 1:
        im = im.resize((max(int(im.width * s), 1), max(int(im.height * s), 1)), Image.BILINEAR)
    ink = Image.fromarray(255 - np.asarray(im))
    base = None
    best = (-1.0, 0.0)
    for k in range(-int(round(SKEW_MAX / SKEW_STEP)), int(round(SKEW_MAX / SKEW_STEP)) + 1):
        ang = k * SKEW_STEP
        r = np.asarray(ink.rotate(ang, resample=Image.BILINEAR, fillcolor=0), dtype=np.float32)
        v = float(r.sum(axis=1).var())
        if k == 0:
            base = v
        if v > best[0]:
            best = (v, ang)
    if not base or best[0] < base * SKEW_GAIN:
        return 0.0
    return round(best[1], 1)


def deskew(g):
    """g: grey uint8 array. Returns (array, angle): rotated with white fill only when |angle| >= SKEW_MIN."""
    import numpy as np
    from PIL import Image
    ang = estimate_skew(g)
    if abs(ang) < SKEW_MIN:
        return g, 0.0
    im = Image.fromarray(g).rotate(ang, resample=Image.BICUBIC, expand=True, fillcolor=255)  # expand: keep the corners
    return np.asarray(im), ang


def fix_crop(src: Path, stats):
    """Returns a PIL grey image for the crop: grown to whitespace if ink touches an edge, then deskewed."""
    import numpy as np
    from PIL import Image
    with Image.open(src) as im:
        im.load()
        g = np.asarray(im.convert("L"))
    m = re.search(r"-p(\d+)\.png$", src.name)
    page_f = src.parent.parent / "pages" / f"p{m.group(1)}.jpg" if m else None
    if any(touches(g).values()):
        stats["touching"] += 1
        if page_f and page_f.exists():
            with Image.open(page_f) as pi:
                page = np.asarray(pi.convert("L"))
            pos = locate(page, g)
            if pos is None:
                stats["not_located"] += 1
            else:
                h, w = g.shape
                box, grown = grow_to_whitespace(page, (pos[0], pos[1], pos[0] + w, pos[1] + h))
                if grown:
                    stats["grown"] += 1
                    g = page[box[1]:box[3], box[0]:box[2]]
                    stats["log"].append((src.name, grown))
                else:
                    stats["touch_unresolved"] += 1
        else:
            stats["no_page"] += 1
    g, ang = deskew(g)
    if ang:
        stats["deskewed"] += 1
        stats["angles"].append((src.name, ang))
    return Image.fromarray(g)


def figures(a):
    out = outside_repo(Path(a.out)) / a.subject
    fdir = out / "figures"
    fdir.mkdir(parents=True, exist_ok=True)
    man, tot, modes = [], 0, collections.Counter()
    stats = {"touching": 0, "grown": 0, "not_located": 0, "touch_unresolved": 0, "no_page": 0, "deskewed": 0, "log": [], "angles": []}
    tmpd = outside_repo(Path(a.out)) / a.subject / "_fixed"
    tmpd.mkdir(exist_ok=True)
    unresolved = {}  # pp id -> figure numbers still touching an edge
    seen = set()  # ids re-checked by this run
    for r in jl(out / "selected.jsonl"):
        seen.add(r["id"])
        for n, c in enumerate(r["crops"], 1):
            name = f"{r['id']}-{n}.webp"
            fixed = tmpd / f"{r['id']}-{n}.png"
            before = [stats[k] for k in UNRESOLVED]
            fix_crop(Path(c), stats).save(fixed)
            if before != [stats[k] for k in UNRESOLVED]:
                unresolved.setdefault(r["id"], []).append(n)
            w, h, b, mode = compress(fixed, fdir / name, a.max_width, a.target_kb * 1024)
            man.append({"pp_id": r["id"], "path": f"{a.subject}/{name}", "w": w, "h": h, "bytes": b})
            tot += b
            modes[mode] += 1
            if stats["log"] and stats["log"][-1][0] == Path(c).name:
                stats["log"][-1] = (r["id"], n) + tuple(stats["log"][-1][1:])
    for f in tmpd.glob("*.png"):
        f.unlink()
    tmpd.rmdir()
    with open(out / "figures.jsonl", "w") as f:
        for m in man:
            f.write(json.dumps(m) + "\n")
    # Keep earlier holds for items this run did not re-check: `select` leaves held items out of selected.jsonl, so
    # rewriting from this run alone would release them on the next run.
    hc = out / "hold-crop.txt"
    keep = [ln for ln in (hc.read_text().splitlines() if hc.exists() else [])
            if ln.split("#")[0].strip() and ln.split("#")[0].strip() not in seen]  # same id rule as parse_hold
    hc.write_text("# written by `load_pp.py figures`: a crop still cut off at an edge after the automatic fixes. "
                  "Only edit to release an item (delete its line, re-run select + figures, which re-checks it); "
                  "a held item is not re-checked otherwise.\n"
                  + "".join(ln + "\n" for ln in keep)
                  + "".join(f"{i}  # figure {', '.join(map(str, ns))}\n" for i, ns in sorted(unresolved.items())))
    print(f"held (crop still cut off): {len(unresolved)} new, {len(keep)} kept -> {hc}")
    for it in stats["log"]:
        print("grown", it[0], f"crop{it[1]}", it[2])
    over = sum(m["bytes"] > a.target_kb * 1024 for m in man)
    print(f"{len(man)} figures, {tot / 1e6:.1f} MB, mean {tot / max(len(man), 1) / 1024:.1f} KB, over target {over}, modes {dict(modes)}")
    hist = collections.Counter(a for _, a in stats["angles"])
    print("skew angles:", dict(sorted(hist.items())))
    print("crop fixes:", {k: v for k, v in stats.items() if k not in ("log", "angles")})


def own_page_crops(crops, pages):
    """Crops on the question's own page(s). The cropper also files crops from other parts of the paper under the same
    question number (Booklet B q5 under Booklet A q5, 40-50 pages away; 372 of 1,250 Science items, 21 Nov 2026 tester
    reports), so a crop counts only on a page of the question, or, without page data, on the first crop's page (MCQs are in
    Booklet A, before Booklet B, so the first crop is the question's). Not the page after: a sample of 6 such crops were all
    another question's picture (21 Nov 2026)."""
    def pg(c):
        m = re.search(r"-p(\d+)\.png$", str(c))
        return int(m.group(1)) if m else -1
    if not crops:
        return []
    own = set(pages or []) or {pg(crops[0])}
    return [c for c in crops if pg(c) in own]


def selftest():
    """Synthetic checks of grow_to_whitespace and deskew (python3 load_pp.py selftest)."""
    c3 = ["x/sci-2022-015-BookletA-q05-p0501.png", "x/sci-2022-015-BookletA-q05-p0544.png", "x/q05-p0502.png"]
    assert own_page_crops(c3, [501, 502]) == [c3[0], c3[2]], own_page_crops(c3, [501, 502])
    assert own_page_crops(c3, None) == [c3[0]] and own_page_crops(c3, [544]) == [c3[1]] and own_page_crops([], [1]) == []
    assert own_page_crops(c3, [501]) == [c3[0]] and own_page_crops(["x/q.png"], [1]) == []  # never the page after; odd name
    import base64
    jwt = "eyJhbGciOiJIUzI1NiJ9." + base64.urlsafe_b64encode(b'{"role":"anon"}').decode().rstrip("=") + ".sig"
    assert key_kind(jwt).startswith("legacy JWT key, role anon"), key_kind(jwt)
    assert key_kind("sb_publishable_abc").startswith("publishable key") and "abc" not in key_kind("sb_secret_abc")
    assert garbled("黑衣人是一个怎么样的人？", ["(1) 贪心", "(2) 自私", "(3) 糊涂", "(4) 骄傲"]) is None  # a short Chinese stem is complete
    assert garbled("你____多生气，____不应该对长辈无礼。", ["(1) 不管……也", "(2) 由于……才", "(3) 只要……都", "(4) 如果……就"]) is None
    assert garbled("I'm not good _________ dancing.", ["in", "at", "for", "with"]) is None  # blanks are not noise
    assert garbled("intimidated", ["worried", "terrified", "helpless", "ashamed"]) == "text-short"  # the sentence was lost
    assert garbled("好", ["a", "b", "c", "d"]) == "text-short"
    assert garbled("ab 12 cd 34 ef 56 gh 78 ij 90 11 22 33 44 55", ["a", "b", "c", "d"]) == "text-low-alpha"
    rk = easier_first([{"id": "pp-c", "subtopic": "s", "difficulty": 2, "level": "basic", "qno": 1},
                       {"id": "pp-a", "subtopic": "s", "difficulty": 1, "level": "competent", "qno": 28},
                       {"id": "pp-b", "subtopic": "s", "difficulty": 2, "level": "basic", "qno": 3},
                       {"id": "pp-z", "subtopic": "t", "difficulty": 3, "level": "basic", "qno": 1}])
    assert rk == {"pp-a": 1, "pp-c": 2, "pp-b": 3, "pp-z": 1}, rk  # difficulty first, then position; ranked per sub-topic
    stem = "Which of the following statements can be concluded from the experiment?"
    assert garbled(stem, ["A. Object 1 is a magnet.", "B. Object 2 is a magnet.", "C. Both are iron.", "D. Neither."]) == "options-are-statements"
    assert garbled(stem, ["A Object 1 is a magnet.", "B Object 2 is a magnet.", "C Both are iron.", "D Neither."]) == "options-are-statements"
    assert garbled(stem, ["A and B only", "B and C only", "A and D only", "B and D only"]) is None  # combinations are real options
    assert garbled(stem, ["(1) Air", "(2) Bark", "(3) Clay", "(4) Dust"]) is None
    assert garbled(stem, ["A and X only", "B and Y only", "C and Z only", "D and W only"]) is None
    assert garbled(stem, ["A  and B only", "B  and C only", "C  and D only", "D  and A only"]) is None  # double spaces
    assert garbled(stem, ["A & B", "B & C", "C & D", "D & A"]) is None and garbled(stem, ["A + B", "B + C", "C + D", "D + A"]) is None
    assert garbled("a ____________ ..... ---- b ____", ["w", "x", "y", "z"]) == "text-short"
    import numpy as np
    from PIL import Image, ImageDraw
    # page 600x800 white: stem text line at y 100-115, gap, box (figure) at y 200-300, x 150-450
    pg = Image.new("L", (600, 800), 255)
    d = ImageDraw.Draw(pg)
    d.rectangle([60, 100, 500, 115], fill=0)
    d.rectangle([150, 200, 450, 300], outline=0, width=3)
    d.rectangle([180, 330, 420, 400], outline=0, width=3)
    page = np.asarray(pg)
    # crop starts at y=230, cutting the box
    box, grown = grow_to_whitespace(page, (140, 230, 460, 420))
    assert "top" in grown and 200 - GROW_PAD - 1 <= box[1] <= 200, (box, grown)
    assert box[1] > 115, "must not swallow the stem line"
    assert "bottom" not in grown and "left" not in grown and "right" not in grown, grown
    # a figure that continues only 1 px past the edge is still grown
    p1 = np.full((200, 200), 255, np.uint8)
    p1[100, 50:150] = 0
    p1[99, 50:150] = 0
    p1[98, 50:150] = 0
    b1, g1 = grow_to_whitespace(p1, (40, 99, 160, 140))
    assert g1.get("top", 0) >= 1 and b1[1] < 99, (b1, g1)
    # a crop that touches nothing is left alone
    box2, g2 = grow_to_whitespace(page, (100, 150, 500, 450))
    assert g2 == {} and box2 == (100, 150, 500, 450)
    # locate finds the crop (page with texture)
    rng = np.random.default_rng(1)
    tex = np.asarray(pg).copy()
    tex[::7, ::5] = 90
    tex[rng.random(tex.shape) < 0.01] = 0
    assert locate(tex, tex[230:420, 140:460].copy()) == (140, 230)
    # deskew: a table drawn then rotated by 1.2 degrees must come back level
    t = Image.new("L", (500, 300), 255)
    dt = ImageDraw.Draw(t)
    for y in range(20, 290, 40):
        dt.line([(20, y), (480, y)], fill=0, width=2)
    for x in range(20, 490, 115):
        dt.line([(x, 20), (x, 280)], fill=0, width=2)
    skewed = np.asarray(t.rotate(1.2, resample=Image.BICUBIC, fillcolor=255))
    ang = estimate_skew(skewed)
    assert abs(ang + 1.2) <= 0.2, ang
    fixed, a2 = deskew(skewed)
    assert abs(estimate_skew(fixed)) < SKEW_MIN
    lvl, l2 = deskew(np.asarray(t))
    assert l2 == 0.0 and (lvl == np.asarray(t)).all()
    tiny = np.asarray(t.rotate(0.2, resample=Image.BICUBIC, fillcolor=255))
    assert deskew(tiny)[1] == 0.0
    # deactivate set and tier counts
    assert deactivate_set({"a", "b", "c"}, {"b", "x"}) == {"a", "c"}  # held/dropped/re-tagged rows go; new row x is not "existing"
    assert deactivate_set(set(), {"a"}) == set() and deactivate_set({"a"}, {"a"}) == set()
    held = {"b"}
    upl = {"a", "c"} - held  # a held id is never in the upload set, so it is only ever deactivated, never revived
    assert "b" in deactivate_set({"a", "b", "c"}, upl) and "b" not in upl
    trs = [{"subtopic": "s1", "level": "basic"}, {"subtopic": "s1", "level": "basic"}, {"subtopic": "s1", "level": "competent"},
           {"subtopic": "s2", "level": "intermediate"}]
    assert tier_counts(trs, {"s1"}) == {"s1|b": 2, "s1|c": 1}
    import tempfile
    tmpd = Path(os.environ.get("PP_TMP", "/data/alvin/tmp/cookie-codex/ppfix")); tmpd.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=tmpd) as td:
        cp = Path(td) / "c.json"
        cp.write_text('{"s1|b": 9, "s3|b": 4}')
        got = write_counts(trs, {"s1", "s2"}, cp)
        assert got == {"s1|b": 2, "s1|c": 1, "s2|i": 1, "s3|b": 4} and json.load(open(cp)) == got
    assert parse_hold("pp-a  # note\n# c\n\npp-b\n") == {"pp-a", "pp-b"}
    ht = hold_auto_text([{"id": "pp-x", "ok": False, "figs": [{"n": 1, "complete": False, "belongs_to_question": True,
                          "contains_other_question": True, "reason": "cut\noff"}]},
                         {"id": "pp-y", "ok": True, "figs": []}])
    assert "pp-x  # complete,contains_other_question: cut off" in ht and "pp-y" not in ht and parse_hold(ht) == {"pp-x"}
    hm = hold_auto_text([{"id": "pp-y", "ok": True, "figs": []}], ["pp-y", "pp-z"])
    assert parse_hold(hm) == {"pp-z"} and "pp-z  # not checked" in hm
    with tempfile.TemporaryDirectory(dir=tmpd) as td:
        (Path(td) / "hold.txt").write_text("pp-h # a\n")
        (Path(td) / "hold-auto.txt").write_text(ht)
        assert read_hold(Path(td)) == {"pp-h", "pp-x"}
    # ocr_keys: only answer-page rows count; full needs ok
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        rows = [{"paper": "A", "ok": True, "from_answer_pages": True, "n_mcq": 2, "answers": {"1": "3", "2": "4"}},
                {"paper": "B", "ok": False, "from_answer_pages": True, "n_mcq": 3, "answers": {"1": "2", "2": "1"}},
                {"paper": "C", "ok": True, "from_answer_pages": False, "n_mcq": 1, "answers": {"1": "1"}}]
        (Path(td) / "anskey_ocr.jsonl").write_text("\n".join(json.dumps(r) for r in rows))
        k = ocr_keys(Path(td))
        assert k == {("A", 1): ("3", True), ("A", 2): ("4", True), ("B", 1): ("2", False), ("B", 2): ("1", False)}, k
    with tempfile.TemporaryDirectory() as td:  # reread_keys: both reads agree, gate clear, two pages must not disagree
        d = Path(td) / "ansreread"
        d.mkdir()
        (d / "p0001.json").write_text(json.dumps({"paper": "A", "page": 1, "gate": None, "cells": {
            "1": {"a": "3", "b": "3", "final": "3"}, "2": {"a": "1", "b": "2", "final": None}, "3": {"a": "4", "b": "4", "final": "4"}}}))
        (d / "p0002.json").write_text(json.dumps({"paper": "A", "page": 2, "gate": None, "cells": {"3": {"a": "2", "b": "2", "final": "2"}}}))
        (d / "p0003.json").write_text(json.dumps({"paper": "B", "page": 3, "gate": None, "cells": {
            str(n): {"a": "1", "b": "1", "final": "1"} for n in range(1, 8)}}))  # 7 identical in a row: gated
        (d / "p0004-x.json").write_text(json.dumps({"paper": "C", "page": 4, "gate": "identical run", "cells": {
            str(n): {"a": "2", "b": "2", "final": "2"} for n in range(1, 5)}}))  # an old gate's flag is ignored
        assert reread_keys(Path(td)) == {("A", 1): "3", **{("C", n): "2" for n in range(1, 5)}}, reread_keys(Path(td))
        assert on_answer_pages(Path(td)) == set()
        (Path(td) / "questions_on_answer_pages.json").write_text(json.dumps({"A": ["q1", "q2"], "B": ["q3"]}))
        assert on_answer_pages(Path(td)) == {"q1", "q2", "q3"}
    print("selftest ok")


# ------------------------------------------------------------------ review page (private, local)

def review(a):
    import base64, html
    out = outside_repo(Path(a.out)) / a.subject
    keep = set(a.subtopics.split(",")) if a.subtopics else None
    if not keep:
        sys.exit("--subtopics is required (or 'all' with --sample)")
    figs = collections.defaultdict(list)
    for m in jl(out / "figures.jsonl"):
        figs[m["pp_id"]].append(m["path"])
    held = read_hold(out)
    rows = [r for r in jl(out / "selected.jsonl") if (keep == {"all"} or r["subtopic"] in keep) and r["id"] not in held]
    if a.sample:  # owner's spot-check: a seeded random few per sub-topic (same draw every run)
        import random
        by = collections.defaultdict(list)
        for r in rows:
            by[r["subtopic"]].append(r)
        rows = [r for sub in sorted(by) for r in random.Random(sub).sample(by[sub], min(a.sample, len(by[sub])))]
        keep = {"spotcheck"}
    parts = ["<!doctype html><meta charset=utf-8><title>pp review</title><style>body{font:16px Arial;max-width:960px;margin:auto;padding:16px}"
             "section{border-top:2px solid #444;padding:12px 0}img{max-width:100%;border:1px solid #999;margin:6px 0}"
             ".k{background:#d6f5d6;font-weight:bold}.m{color:#555;font-size:13px}</style>",
             f"<h1>{html.escape(', '.join(sorted(keep)))}: {len(rows)} items</h1><p>Check each: picture readable and complete "
             "(all (1)-(4) labels visible), picture matches the stem, nothing gives the answer away, key is right. "
             "Put the pp id of a failing item in hold.txt.</p>"]
    for n, r in enumerate(sorted(rows, key=lambda r: (r["subtopic"], r["level"], r["id"])), 1):
        imgs = "".join(f'<img src="data:image/webp;base64,{base64.b64encode((out / "figures" / Path(p).name).read_bytes()).decode()}">'
                       for p in figs[r["id"]])
        opts = "".join(f'<li class="{"k" if i == r["answer"] else ""}">({i + 1}) {html.escape(o)}</li>' for i, o in enumerate(r["options"]))
        parts.append(f'<section><div class=m>#{n} {r["id"]} · {html.escape(r["subtopic"])} · {r["level"]} · Past paper {r["year"]} · blind: {html.escape(r["blind_src"])}</div>'
                     f'<p>{html.escape(r["stem"])}</p>{imgs}<ol style="list-style:none;padding:0">{opts}</ol></section>')
    dst = out / f"review-{sorted(keep)[0]}.html"
    dst.write_text("\n".join(parts))
    print(f"{len(rows)} items -> {dst}")


# ------------------------------------------------------------------ upload (owner's "apply" only)

COUNTS = REPO / "site" / "src" / "data" / "pp_counts.json"
TIER = {"basic": "b", "intermediate": "i", "competent": "c"}


def deactivate_set(existing_active: set, upload_ids: set) -> set:
    """Rows live in the table for an uploaded sub-topic that this upload no longer carries: held, dropped by select,
    or re-tagged away. Pure (selftest)."""
    return set(existing_active) - set(upload_ids)


def tier_counts(rows, subs: set) -> dict:
    """{"<sub>|<tier letter>": n} for the given sub-topics; numbers only. Pure (selftest)."""
    c = collections.Counter(f"{r['subtopic']}|{TIER[r['level']]}" for r in rows if r["subtopic"] in subs)
    return dict(sorted(c.items()))


def write_counts(rows, subs: set, path: Path = COUNTS) -> dict:
    """Replace the entries of `subs` in the counts file, keep every other sub-topic's."""
    old = json.load(open(path)) if path.exists() else {}
    new = {k: v for k, v in old.items() if k.split("|")[0] not in subs}
    new.update(tier_counts(rows, subs))
    path.write_text(json.dumps(dict(sorted(new.items())), indent=1) + "\n")
    return new


def selection(a):
    """(upload rows after hold, sub-topics in the selection, db figures map, out dir)."""
    out = Path(a.out) / a.subject
    rows = jl(out / "selected.jsonl")
    if a.subtopics:
        keep = set(a.subtopics.split(","))
        rows = [r for r in rows if r["subtopic"] in keep]
    subs = {r["subtopic"] for r in rows} | (set(a.subtopics.split(",")) if a.subtopics else set())
    hold = read_hold(out)
    return [r for r in rows if r["id"] not in hold], subs, out


def counts(a):
    rows, subs, _ = selection(a)
    new = write_counts(rows, subs)
    print(f"{COUNTS.name}: {len(new)} tier counts ({len(subs)} sub-topics updated)")


def easier_first(rows):
    """{pp id: rank} inside each sub-topic for pp_items.ord (migration 006, ADR 0011): the tagger's difficulty, then the
    paper position (the level the position rule gave, then the question number), then the id. 1 = served first."""
    lv = {"basic": 0, "intermediate": 1, "competent": 2}
    out, by = {}, collections.defaultdict(list)
    for r in rows:
        by[r["subtopic"]].append(r)
    for rs in by.values():
        rs.sort(key=lambda r: (r.get("difficulty") if isinstance(r.get("difficulty"), int) else 2, lv.get(r.get("level"), 1),
                               r.get("qno") if isinstance(r.get("qno"), int) else 99, r["id"]))
        out.update({r["id"]: i for i, r in enumerate(rs, 1)})
    return out


def key_kind(k):
    """What kind of Supabase key this is, never the key itself: prefix, the JWT role claim, length."""
    import base64
    if k.startswith(("sb_secret_", "sb_publishable_")):
        return f"{k.split('_')[1]} key, {len(k)} chars"
    if k.startswith("eyJ") and k.count(".") == 2:
        try:
            part = k.split(".")[1]
            claims = json.loads(base64.urlsafe_b64decode(part + "=" * (-len(part) % 4)))
            role = claims.get("role", "?") if isinstance(claims, dict) else "unreadable"
        except ValueError:
            role = "unreadable"
        return f"legacy JWT key, role {role}, {len(k)} chars"
    return f"unrecognised key, {len(k)} chars"


def upload(a):
    rows, usubs, out = selection(a)
    ord_ = easier_first(rows)  # needs migration 006 (pp_items.ord) on the live project
    figs = collections.defaultdict(list)
    for m in jl(out / "figures.jsonl"):
        figs[m["pp_id"]].append({"path": m["path"], "w": m["w"], "h": m["h"]})
    missing = [r["id"] for r in rows if r["crops"] and len(figs[r["id"]]) != len(r["crops"])]
    if missing:
        sys.exit(f"{len(missing)} rows lack their WebP figures: run `figures` first")
    db = [{"id": r["id"], "src_id": r["src_id"], "subject": r["subject"], "subtopic": r["subtopic"], "level": r["level"],
           "pattern": r["pattern"], "stem": r["stem"], "options": r["options"], "answer": r["answer"],
           "figures": figs[r["id"]], "year": r["year"], "school": r["school"], "paper": r["paper"],
           "qno": r["qno"], "marks": r["marks"], "blind_src": r["blind_src"], "ord": ord_[r["id"]], "active": True} for r in rows]
    nfig = sum(len(d["figures"]) for d in db)
    print(f"{len(db)} rows, {nfig} figures, sub-topics {len({d['subtopic'] for d in db})}")
    if not db:  # ponytail: an empty selection is almost always a wrong --out; stop before touching the table or pp_counts
        sys.exit(f"nothing selected under {a.out}/{a.subject} for those sub-topics: wrong --out? "
                 "(the 2025-26 import lives in /data/alvin/tmp/cookie-codex/ppimport/final2526)")
    url, k = os.environ.get("SUPABASE_URL", "").rstrip("/"), os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "").strip()
    if not a.apply and not (url and k):
        print("dry run: nothing sent; deactivations not counted (no Supabase env); "
              "add --apply after the owner's go-ahead")
        return
    if not url or not k:
        sys.exit("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set")
    import requests
    h = {"apikey": k}
    if k.startswith("eyJ"):  # legacy JWT service key; new sb_secret_ keys go in apikey only
        h["authorization"] = f"Bearer {k}"
    s = requests.Session()
    s.headers.update(h)
    keepids = {d["id"] for d in db}
    stale = set()
    for sub in sorted(usubs):  # active rows of an uploaded sub-topic that this upload no longer carries
        r = s.get(f"{url}/rest/v1/pp_items", params={"select": "id", "subject": f"eq.{a.subject}",
                  "subtopic": f"eq.{sub}", "active": "eq.true", "limit": "10000"}, timeout=60)
        if r.status_code >= 300:  # 401: the key is not a service-role key (or was pasted cut short)
            sys.exit(f"could not list existing rows of {sub}: HTTP {r.status_code} {r.text[:200]}\n"
                     f"key given: {key_kind(k)} (needs the service-role / secret key)")
        stale |= deactivate_set({x["id"] for x in r.json()}, keepids)
    print(f"would deactivate {len(stale)} existing rows no longer selected" if not a.apply
          else f"deactivating {len(stale)} existing rows no longer selected")
    if not a.apply:
        print("dry run: nothing sent (add --apply after the owner's go-ahead)")
        return
    fdir = out / "figures"
    for d in db:
        for f in d["figures"]:
            body = (fdir / Path(f["path"]).name).read_bytes()
            r = s.post(f"{url}/storage/v1/object/{BUCKET}/{f['path']}", data=body,
                       headers={"content-type": "image/webp", "x-upsert": "true", "cache-control": "3600"}, timeout=60)
            if r.status_code >= 300:
                sys.exit(f"figure upload failed for {d['id']}: HTTP {r.status_code}")
    for i in range(0, len(db), 200):
        r = s.post(f"{url}/rest/v1/pp_items?on_conflict=id", json=db[i:i + 200], timeout=60,
                   headers={"prefer": "resolution=merge-duplicates,return=minimal", "content-type": "application/json"})
        if r.status_code >= 300:
            sys.exit(f"row upsert failed at batch {i // 200}: HTTP {r.status_code}")
    ids = sorted(stale)
    for i in range(0, len(ids), 100):  # after the upsert: a failed upsert leaves the old rows live (stale never holds an uploaded id)
        r = s.patch(f"{url}/rest/v1/pp_items", params={"id": f"in.({','.join(ids[i:i + 100])})"}, json={"active": False},
                    headers={"prefer": "return=minimal", "content-type": "application/json"}, timeout=60)
        if r.status_code >= 300:
            sys.exit(f"deactivate failed at batch {i // 100}: HTTP {r.status_code}")
    print(f"loaded {len(db)} rows and {nfig} figures")
    write_counts(rows, usubs)
    print(f"wrote {COUNTS.name}")


def where(a):
    """Where a reported question comes from (question_reports, migration 005): a pp id -> its paper (school, exam, PDF
    file and page), crops, text, options and key, and the hold files that name it; a generated id -> its bank and stem.
    Prints private past-paper text: terminal only."""
    qid = a.arg or ""
    if not qid.startswith("pp-"):
        root = Path(__file__).resolve().parents[2] / "site" / "src" / "data" / "quiz"
        for f in sorted(root.glob("*/*.json")):
            d = json.loads(f.read_text())
            for q in d["questions"] if isinstance(d, dict) else d:
                if q.get("id") == qid:
                    print(f"{qid}: generated, {f.relative_to(root.parents[3])}, sub-topic {(q.get('outcomes') or [f.stem + '-0'])[0].rsplit('-', 1)[0]}, level {q.get('level')}\n  {q.get('stem')}")
                    return
        sys.exit(f"{qid}: not in any bank under {root}")
    for subj_dir in sorted(p for p in Path(a.pp).iterdir() if p.is_dir()):
        for ydir in sorted(subj_dir.glob("20[0-9][0-9]")):
            for q in jl(ydir / "merged.jsonl"):
                if pp_id(q["id"]) != qid:
                    continue
                paper = next((x for x in jl(ydir / "papers.jsonl") if x["paper_id"] == q.get("paper")), {})
                print(f"{qid} = {q['id']}  ({paper.get('school')}, {paper.get('exam')}, question {q.get('qno')})")
                print(f"  PDF: {paper.get('file')}  page(s) {q.get('pages')} (paper runs {paper.get('first_page')}-{paper.get('last_page')})")
                print(f"  page scans: {', '.join(str(ydir / 'pages' / f'p{n:04d}.jpg') for n in q.get('pages') or [])}")
                print(f"  crops: {', '.join(str(c) for c in sorted((ydir / 'crops').glob(q['id'] + '-p*.png'))) or 'none'}")
                print(f"  text: {q.get('text')}\n  options: {q.get('options')}\n  key: {q.get('answer')} (flag {q.get('answer_flag')})")
                for hf in sorted(Path(a.out).glob(f"*/{subj_dir.name}/hold*.txt")) + sorted(Path(a.out).glob(f"{subj_dir.name}/hold*.txt")):
                    for line in hf.read_text().splitlines():
                        if line.split("#")[0].strip() == qid:
                            print(f"  held: {hf}: {line}")
                return
    sys.exit(f"{qid}: no past-paper question under {a.pp} has this id")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("cmd", choices=("select", "figures", "review", "upload", "counts", "cropcheck-apply", "where", "selftest"))
    p.add_argument("arg", nargs="?", help="cropcheck-apply: the results.jsonl; where: a question id (pp-... or generated)")
    p.add_argument("--subject", default="science")
    p.add_argument("--years", default="2018-2026")
    p.add_argument("--pp", default=str(DEF_PP))
    p.add_argument("--blind", default=str(DEF_BLIND))
    p.add_argument("--blind2", default=str(DEF_BLIND2))
    p.add_argument("--out", default=str(DEF_OUT))
    p.add_argument("--max-width", type=int, default=900)
    p.add_argument("--target-kb", type=int, default=60)
    p.add_argument("--subtopics", default="")
    p.add_argument("--sample", type=int, default=0, help="review: this many random items per sub-topic (spot-check)")
    p.add_argument("--apply", action="store_true")
    p.add_argument("--ocr-keys", action="store_true", help="select: use <year>/anskey_ocr.jsonl as a fallback key source")
    p.add_argument("--reread-keys", action="store_true", help="select: use agreed <year>/ansreread/ cells (ans_reread.py) as a fallback key source, answer_src 'vision-reread'")
    p.add_argument("--tier-rule", choices=("position", "tags"), default="position")
    a = p.parse_args()
    {"select": select, "figures": figures, "review": review, "upload": upload, "counts": counts, "cropcheck-apply": cropcheck_apply, "where": where, "selftest": lambda _a: selftest()}[a.cmd](a)


if __name__ == "__main__":
    main()
