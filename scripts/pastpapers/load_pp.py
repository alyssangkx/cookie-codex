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
FIG_MAX = 200 * 1024  # the bucket's file_size_limit (storage refuses a bigger file with HTTP 400)

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
    for i, o in enumerate(strip_opts(opts), 1):
        if o == a:
            return str(i)
    return None


def strip_num(o: str) -> str:
    """The option's printed numbering off: "(2)", "（2）", "2." / "2)" / "2、" before a non-digit (a decimal like "2.5" stays)."""
    return re.sub(r"^\s*(?:[(（]\s*\d\s*[)）]|[1-4][.)．、](?=\s*\D))\s*", "", o or "").strip()


def scanner_marks(t: str) -> str:
    """The scanner's part labels a child should not see (owner's report, 21 Nov 2026: pp-699ed1d689 "(cont)",
    pp-29e22e295c "(sub)"): "(cont)"/"(cont'd)"/"(continued)", "(sub)" anywhere, and an "(a)"-"(d)" label at the start of a
    line (the part of a structured question this MCQ was). Science and Maths stems."""
    t = re.sub(r"(?m)^[ \t]*\((?:cont(?:'d|inued)?|sub)\.?\)[ \t]*", "", t, flags=re.I)  # a label opening a line
    t = re.sub(r"[ \t]*\((?:cont(?:'d|inued)?|sub)\.?\)", "", t, flags=re.I)  # one inside a line
    return re.sub(r"(?m)^[ \t]*\([a-d]\)[ \t]+", "", t)  # nothing else is touched


def strip_opts(opts):
    """strip_num on each option, and "1 获得" (a number and a space) only when the four options are numbered 1-4 in order
    (owner sample, 21 Nov 2026: "(1) 1 焦急"); an unlabelled "3 天" keeps its number."""
    opts = [strip_num(o) for o in opts]
    # "1 获得" or "1反问": a number before a Chinese word (or after a space), all four in order 1-4; never when that would
    # leave four equal options (a real "1 年 / 2 年 / 3 年 / 4 年")
    if len(opts) == 4 and all(re.match(rf"^{i}(?:\s+\S|\s*[\u3400-\u9fff])", o) for i, o in enumerate(opts, 1)):
        bare = [re.sub(r"^[1-4]\s*", "", o) for o in opts]
        if len(set(bare)) == 4:
            opts = bare
    return opts


def realfig(q):
    return any(isinstance(f, str) and f and f.lower() not in ("none", "null") for f in (q.get("figures") or []))


FIG_WORDS_LANG = re.compile(r"\b(picture|diagram|chart|graph|poster|map|timetable|table (below|above)|the table)\b|图|表格", re.I)
BLANK_PUNCT = set("_.,;:?!'\"()[]-…—–·。，、；：？！“”‘’（）《》〈〉【】「」")
LETTERED = re.compile(r"\(?([A-D])(?:[.)]\s*|\s+(?![\s&+,]|and\b|or\b|only\b))")  # "A. Air" / "A Air", not "A and X only"


CHI_SINGLE = {"chi-pinyin-sound", "chi-zixing-form", "chi-ciyu-choose", "chi-ciyu-idiom", "chi-juzi-choose", "chi-juzi-guanlian"}
ENG_INSTR = re.compile(r"(?:^|(?<=[.?!]))\s*(?:select|choose|circle|fill in|pick)\b[^.?!]*[.?!]?", re.I)
ENG_BLANK = re.compile(r"_{2,}|\(\s*\)|\.{4,}")
ENG_PASSAGE = re.compile(r"\b(passage|paragraph|line \d+|lines \d+|the (?:poster|advertisement|notice|brochure|flyer|leaflet|"
                         r"article|email|letter|text above|text below|story)|according to the|in the (?:text|story|article))\b", re.I)


def eng_incomplete(text: str) -> str | None:
    """A single-sentence English MCQ (grammar, vocabulary) must carry its own sentence with a blank or a question
    (owner's sample, 21 Nov 2026: 13 of 30 had none). Rejects: a stem that is only an instruction ("Select the most
    appropriate word to fill in the blank."), a lone word whose sentence was lost ("portrayed"), a sentence with no blank
    or question (the underlined word is lost in OCR), and a stem that needs a passage or visual text."""
    t = (text or "").strip()
    rest = ENG_INSTR.sub(" ", t)
    if sum(c.isalpha() for c in rest) < 15:
        return "stem-instruction-only"
    if not ENG_BLANK.search(t) and "?" not in t:
        return "stem-no-blank-or-question"
    if ENG_PASSAGE.search(t):
        return "stem-needs-passage"
    return None


CHI_BLANK = re.compile(r"_{2,}|（\s*）|\(\s*\)")
PINYIN = re.compile(r"[a-zāáǎàēéěèīíǐìōóǒòūúǔùǖǘǚǜü' ]+")


def chi_incomplete(text: str, opts) -> str | None:
    """A single Chinese MCQ must carry a blank, or pinyin options (字音: the pinyin shows which word is asked). A meaning or
    usage question names its word by an underline, which the scan loses, and a sentence fragment has no blank: neither can be
    answered (owner's spot check, 21 Nov 2026)."""
    if CHI_BLANK.search(text or ""):
        return None
    if opts and all(len(strip_num(o)) >= 2 and PINYIN.fullmatch(strip_num(o)) for o in opts):
        return None
    return "chi-no-blank-underline-lost"


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
    s = strip_opts(opts)
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
    if a.passage and PASSAGE[a.passage]["subject"] != a.subject:
        sys.exit(f"--passage {a.passage} is a {PASSAGE[a.passage]['subject']} section")
    for y in years(a.years):
        base = Path(a.pp) / a.subject / str(y)
        tags = {t["id"]: t for t in jl(base / "tags72.jsonl")}
        bfile = Path(a.blind) / f"{a.subject}-{y}.jsonl"
        blind = {b["id"]: b for b in jl(bfile)} if bfile.exists() else None
        second = {b["id"]: b for b in jl(Path(a.blind2) / f"{a.subject}-{y}.jsonl")}
        # owner-approved model consensus (21 Nov 2026, English): three outside models agree with the key ("confirm"), or
        # with the local blind solver against it ("replace"; spot check 20/20 for the models). Used only while the key is
        # still the one the verdict was made on (key_old).
        consensus = {c["id"]: c for c in jl(Path(a.blind) / "consensus" / f"{a.subject}-{y}.jsonl")}
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
            pk = PASSAGE.get(a.passage)
            vt = bool(pk)
            qn = int(q["qno"]) if str(q.get("qno") or "").isdigit() else None  # Chinese papers store "17"
            if vt and not (qn and pk["q"][0] <= qn <= pk["q"][1] and not re.search(r"booklet\s*b", str(q.get("part") or ""), re.I)
                           and ((tags.get(q["id"]) or {}).get("st") == pk["st"] or q.get("section") == pk["section"])):
                continue  # passage mode takes only its section
            opts = q.get("options") or []
            k = key(q.get("answer"), opts) if len(opts) == 4 else None
            t = tags.get(q["id"]) or {}
            if vt:
                t = dict(t, st=pk["st"])  # the section, whatever the tagger filed it under
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
            cv = consensus.get(q["id"])
            cv_ok = bool(cv and len(opts) == 4 and k and cv["key_old"] == k)
            if cv_ok and cv["kind"] == "replace":  # an OCR or reread key that disagrees with the new key still holds it
                k, src = cv["key_new"], "consensus"
                conflict = bool((ok and ok != k) or (rr and rr != k))
            elif cv_ok:
                src = f"{src}+consensus"
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
            elif not cv_ok and src in ("ocr", "vision-reread") and (blind is None or q["id"] not in blind or blind[q["id"]].get("key") != k):
                reason = "needs-blind-check-ocr"  # a blind file made with OCR keys must contain it
            elif not cv_ok and blind is None:
                reason = "no-blind-check-yet"
            elif not cv_ok and q["id"] not in blind:
                reason = "not-in-blind-check"
            elif not cv_ok and blind[q["id"]].get("key") != k:
                reason = "blind-key-mismatch"  # the key changed after the blind run: re-run it
            elif not cv_ok and blind[q["id"]].get("agree") is not True and not (
                    second.get(q["id"], {}).get("agree2") is True and second[q["id"]].get("key") == k):
                reason = "blind-unparsed" if blind[q["id"]].get("pick") is None else "blind-disagree"
            else:
                reason = garbled(q.get("text") or "", opts) or (eng_incomplete(q.get("text") or "") if a.subject == "english" and not vt else None) \
                    or ("tex-left" if any(re.search(r"\\|\^|[\x00-\x08\x0b\x0c\x0e-\x1f]", tex_to_text(x)) for x in [q.get("text") or "", *opts]) else None) \
                    or (chi_incomplete(q.get("text") or "", opts) if a.subject == "chinese" and t.get("st") in CHI_SINGLE else None)
                # PSLE English Paper 2 Booklet A: Q1-15 are the single-sentence grammar and vocabulary items; 16-20 vocabulary
                # cloze and 21+ visual text need their passage (owner, 21 Nov 2026: the split questions were visual text)
                if not reason and a.subject == "english" and not vt and (not isinstance(q.get("qno"), int) or q["qno"] > 15
                                                              or re.search(r"booklet\s*b", str(q.get("part") or ""), re.I)):
                    reason = "eng-passage-section"
                if not reason and a.passage == "chinese-cloze" and not cloze_stem(q.get("text"), qn, opts):
                    reason = "cloze-no-blank"
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
                    # bare two-cell table rows ("Sound, None") mean the column headings are in the picture: the table is
                    # needed (tester report 21 Nov: pp-87af45c055 "Useful energy | Wasted energy" shipped without it)
                    refers = refers or (a.subject == "science" and table_rows(opts))
                    if vt:  # the set's pages are its picture (set_pages below); no crop of its own
                        q["_crops"] = []
                        if not q.get("pages"):
                            reason = "no-page-data"
                    elif refers or realfig(q):
                        usable = [c for c in crops.get(q["id"], []) if crop_ok(c)]
                        good = own_page_crops(usable, q.get("pages"))
                        if not crops.get(q["id"]):
                            reason = "needs-figure-no-crop"
                        elif not usable:
                            reason = "crop-unusable"
                        elif not q.get("pages"):
                            reason = "no-page-data"  # own_page_crops cannot tell the question's crops from misfiled ones
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
                "stem": cloze_stem(q["text"], qn, opts) if a.passage == "chinese-cloze" else
                        tex_to_text(scanner_marks(speaker_lines(q["text"].strip()) if a.subject == "science" else q["text"].strip())
                                    if a.subject in ("science", "maths") else q["text"].strip()),
                "options": [tex_to_text(o) for o in strip_opts(opts)], "answer": int(k) - 1,
                **({"grp": set_id(q, pk["suffix"]), "seq": qn, "pages": q["pages"], "pages_dir": str(base / "pages")} if vt else {}),
                "answer_src": src, "crops": q["_crops"], "year": y, "school": q.get("school"), "paper": q.get("paper"),
                "part": q.get("part"), "qno": q.get("qno"), "marks": q.get("marks"),
                "blind_src": (cv.get("src", "consensus") if cv_ok else (blind[q["id"]].get("src") or "blind") if blind[q["id"]].get("agree") is True
                              else "second:vl2-fullres+text72-ocr"),
            })
    if a.passage:
        for r, why in set_pages(rows, out, a.passage):  # a dropped set is held with its reason, like any other question
            rejects.append({"id": r["src_id"], "reason": why})
            R[why] += 1
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
    done_sets = {}
    for r in jl(out / "selected.jsonl"):
        seen.add(r["id"])
        if r.get("set_pages"):  # a passage set: its pages, stored once under the set's first question
            if r["set_owner"] not in done_sets:
                done_sets[r["set_owner"]] = []
                for n, pg in enumerate(r["set_pages"], 1):
                    name = f"{r['set_owner']}-{n}.webp"
                    w, h, b, mode = compress(Path(pg), fdir / name, 1400, 190 * 1024)
                    done_sets[r["set_owner"]].append({"path": f"{a.subject}/{name}", "w": w, "h": h, "bytes": b})
                    tot += b
                    modes[mode] += 1
            man += [{"pp_id": r["id"], **m} for m in done_sets[r["set_owner"]]]
            continue
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
    toobig = sorted({m["path"] for m in man if m["bytes"] > FIG_MAX})
    if toobig:  # compress() stops shrinking at 520 px wide; such a picture cannot be uploaded: hold its item by hand
        sys.exit(f"{len(toobig)} pictures still over the bucket's {FIG_MAX // 1024} KB limit: {', '.join(toobig[:5])}")
    over = sum(m["bytes"] > a.target_kb * 1024 for m in man)
    print(f"{len(man)} figures, {tot / 1e6:.1f} MB, mean {tot / max(len(man), 1) / 1024:.1f} KB, over target {over}, modes {dict(modes)}")
    hist = collections.Counter(a for _, a in stats["angles"])
    print("skew angles:", dict(sorted(hist.items())))
    print("crop fixes:", {k: v for k, v in stats.items() if k not in ("log", "angles")})


TITLE = r"(?:Mr|Mrs|Ms|Mdm|Dr)"
SPEAKER = re.compile(r'(?<=[.?!:"\u201d\u2019\')])(?<!\bMr\.)(?<!\bMrs\.)(?<!\bMs\.)(?<!\bMdm\.)(?<!\bDr\.)\s+'
                     r'(?=(?:' + TITLE + r'\.? )?[A-Z][a-z]+:\s)')
# the stem's own question after the last comment: a sentence starting with a question word and ending in "?" (decimals
# allowed); a comment's own "Do you agree?" is left with its speaker
ASK = re.compile(r'(?<=[.!?"\u201d\u2019])\s+(?=(?:\S+\s+){2}\S)(?=(?:Which|What|Who|Whose|Whom|How|When|Where|Why|Based|In|From|According)\b'
                 r'(?:[^.!?]|\.\d)*\?\s*$)')  # 3+ words: a bare "Why?" stays with its speaker


def speaker_lines(t):
    """Comments by named people ("Aminah: ... Bala: ...") each on their own line, as printed, and the question after them
    on its own line (tester report 21 Nov: pp-aaaeb1ffd1 read as one block). Only with 2+ speakers; other line breaks are
    kept; the quiz shows the stem with white-space: pre-line. Science only (Maths "Ans:" and English "To:" are labels).
    ponytail: one-word names (and Mr/Mrs/Ms/Mdm/Dr + name) only; "Jun Wei:" stays on the line before; a speaker's own 3+ word
    closing question starting with a question word would move to its own line. Fine on the 7 Science stems it touches."""
    parts = SPEAKER.split(t)
    if len(parts) < 3:
        return t
    parts[-1] = ASK.sub("\n", parts[-1])
    return "\n".join(parts)


def table_rows(opts):
    """Every option is one flattened table row of exactly two short unlabelled cells ("Light + sound, Heat"): the column
    headings exist only in the picture. Lists ("water, oil and flour") and labelled cells ("Mass: increase") read fine.
    Science only (the caller): Maths "2, 4" answers and Chinese sentences with an OCR'd comma are not tables. A list's
    last cell joins its final item with "and" ("oil and flour"); a row may have it in the first ("Light and sound, Heat").
    ponytail: two cells only; a 3-column row ("Increases, Decreases, Increases") looks like a 3-item list, so it is not caught."""
    s = [strip_num(o or "") for o in opts]
    cells = [x.split(", ") for x in s]
    return len(s) == 4 and all(
        len(c) == 2 and all(re.fullmatch(r"[A-Za-z][A-Za-z +'-]{0,24}", y) for y in c) and " and " not in c[1] for c in cells)


def own_page_crops(crops, pages):
    """Crops on the question's own page(s). The cropper also files crops from other parts of the paper under the same
    question number (Booklet B q5 under Booklet A q5, 40-50 pages away; 372 of 1,250 Science items, 21 Nov 2026 tester
    reports), so a crop counts only on a page of the question; without page data none counts (the item is held; every
    Science item had page data on 21 Nov 2026). Not the page after: a sample of 6 such crops were all another question's
    picture."""
    def pg(c):
        m = re.search(r"-p(\d+)\.png$", str(c))
        return int(m.group(1)) if m else -1
    if not crops:
        return []
    own = set(pages or [])
    return [c for c in crops if pg(c) in own]


def selftest():
    """Synthetic checks of grow_to_whitespace and deskew (python3 load_pp.py selftest)."""
    sp = speaker_lines("Four comments. Aminah: Roots hold it. Bala: It is uprooted. Caden: It makes food. Which are correct?")
    assert sp == "Four comments.\nAminah: Roots hold it.\nBala: It is uprooted.\nCaden: It makes food.\nWhich are correct?", sp
    assert speaker_lines("Note: one label only. Which is it?") == "Note: one label only. Which is it?"
    assert speaker_lines("Said: Aminah: Roots. Bala: Stem. Mr Tan: Leaf. In which part is food made?") == \
        "Said:\nAminah: Roots.\nBala: Stem.\nMr Tan: Leaf.\nIn which part is food made?"
    assert speaker_lines("Said: Aminah: Roots. Bala: It wilts. What a pity.") == "Said:\nAminah: Roots.\nBala: It wilts. What a pity."
    assert speaker_lines("Said: Mr. Tan: Leaf. Aminah: Roots. Which is correct?") == "Said:\nMr. Tan: Leaf.\nAminah: Roots.\nWhich is correct?"
    assert speaker_lines("Comments. Aminah: Roots. Bala: Is it dry? Which is correct?") == "Comments.\nAminah: Roots.\nBala: Is it dry?\nWhich is correct?"
    assert speaker_lines("Said: Aminah: Roots. Bala: It is dry. Do you agree?") == "Said:\nAminah: Roots.\nBala: It is dry. Do you agree?"
    assert speaker_lines("Said: Aminah: Roots. Bala: Stem is 2.5 cm. Which is 3.5 cm?") == "Said:\nAminah: Roots.\nBala: Stem is 2.5 cm.\nWhich is 3.5 cm?"
    assert speaker_lines("Said: Aminah: It needs water. Bala: It wilts. How?").endswith("Bala: It wilts. How?")
    assert speaker_lines("Four. Aminah: Roots. Bala: Stem.\n\nA | B\nWhich?") == "Four.\nAminah: Roots.\nBala: Stem.\n\nA | B\nWhich?"
    assert table_rows(["(1) Light, Heat", "(2) Sound, None", "(3) Light + sound, Heat", "(4) Light + sound, None"])
    assert not table_rows(["water, oil and flour", "ice, sugar and flour", "a, b and c", "d, e and f"])
    assert not table_rows(["Mass: increase, Volume: increase"] * 4) and not table_rows(["K", "L", "M", "N"])
    assert table_rows(["Light and sound, Heat", "Sound, None", "Light, Heat", "Heat, None"])
    assert not table_rows(["2, 4", "8, 18", "32, 40", "16, 36"]) and not table_rows([r"\( 12 \, \text{cm}^3 \)"] * 4)
    assert not table_rows(["哥哥的钱包很贫穷, 里面只剩下一块钱。"] * 4)
    c3 = ["x/sci-2022-015-BookletA-q05-p0501.png", "x/sci-2022-015-BookletA-q05-p0544.png", "x/q05-p0502.png"]
    assert own_page_crops(c3, [501, 502]) == [c3[0], c3[2]], own_page_crops(c3, [501, 502])
    assert own_page_crops(c3, None) == [] and own_page_crops(c3, [544]) == [c3[1]] and own_page_crops([], [1]) == []
    assert own_page_crops(c3, [501]) == [c3[0]] and own_page_crops(["x/q.png"], [1]) == []  # never the page after; odd name
    import base64
    jwt = "eyJhbGciOiJIUzI1NiJ9." + base64.urlsafe_b64encode(b'{"role":"anon"}').decode().rstrip("=") + ".sig"
    assert key_kind(jwt).startswith("legacy JWT key, role anon"), key_kind(jwt)
    assert key_kind("sb_publishable_abc").startswith("publishable key") and "abc" not in key_kind("sb_secret_abc")
    assert garbled("黑衣人是一个怎么样的人？", ["(1) 贪心", "(2) 自私", "(3) 糊涂", "(4) 骄傲"]) is None  # a short Chinese stem is complete
    assert garbled("你____多生气，____不应该对长辈无礼。", ["(1) 不管……也", "(2) 由于……才", "(3) 只要……都", "(4) 如果……就"]) is None
    assert garbled("I'm not good _________ dancing.", ["in", "at", "for", "with"]) is None  # blanks are not noise
    assert garbled("intimidated", ["worried", "terrified", "helpless", "ashamed"]) == "text-short"  # the sentence was lost
    assert tex_to_text(r"Each had \(\frac{3}{5}\) kg") == "Each had 3/5 kg"
    assert tex_to_text(r"\(2\frac{1}{3}\) m") == "2 1/3 m" and tex_to_text(r"\(\frac{12}{5}\)") == "12/5"
    assert tex_to_text(r"\(\frac{3b - 7 + 4b}{3} + 6\)") == "(3b - 7 + 4b)/3 + 6"
    assert tex_to_text(r"\(12 \times 5 \div 3\) and \(45^\circ\) and 8 cm\(^2\)") == "12 × 5 ÷ 3 and 45° and 8 cm²"
    assert tex_to_text(r"\(120 \, \text{cm}^3\)") == "120 cm³" and tex_to_text("Cost $5.20") == "Cost $5.20"
    assert tex_to_text("90.9\\nFind it") == "90.9\nFind it" and tex_to_text(r"\(x \neq 3\)") == "x ≠ 3"
    assert tex_to_text(r"\(1, 2, 3, \cdots\)") == "1, 2, 3, …" and tex_to_text(r"\(10^{23}\)") == "10²³"
    assert tex_to_text("5 × \\\x0crac{1}{3}") == "5 × 1/3" and tex_to_text("120 \x09ext{cm}") == "120 cm"
    assert tex_to_text("On 21/11/2026 \\(\\times\\) 2") == "On 21/11/2026 × 2" and tex_to_text(r"$\frac{1}{2}$ of it") == "1/2 of it"
    assert tex_to_text(r"8\(\frac{1}{2}\)") == "8 1/2" and tex_to_text(r"\(\frac{3}{4}\) of 2\(\frac{1}{2}\)") == "3/4 of 2 1/2"
    assert tex_to_text(r"Ali paid $5 more than \(\frac{1}{2}\) of what Ben paid, $12.") == "Ali paid $5 more than 1/2 of what Ben paid, $12."
    assert tex_to_text(r"Ali paid \$5 and \(\frac{1}{2}\) of \$12") == "Ali paid $5 and 1/2 of $12"
    assert tex_to_text(r"\(\frac{1}{2}\)\(\frac{1}{3}\)") == "1/2 1/3" and tex_to_text(r"\(10^23\)") == "10²3"
    assert tex_to_text(r"\(\frac{1}{\sqrt{2}}\)") == "1/√2" and tex_to_text(r"\(\frac12\)") == "1/2"
    assert "^" in tex_to_text(r"\(x^{-1}\)")  # held by tex-left
    assert tex_to_text(r"$(2\pi + 16)$ cm") == "(2π + 16) cm" and tex_to_text(r"How many in \(\frac{1}{2}\)?") == "How many in 1/2?"
    assert tex_to_text(r"Express \(4\frac{4}{5}\) as a decimal.") == "Express 4 4/5 as a decimal."
    assert tex_to_text("$(50-23z)$") == "(50-23z)" and tex_to_text("$(2x - 14)") == "$(2x - 14)" and tex_to_text("$12$") == "$12$"
    assert "\\" in tex_to_text(r"\(\overline{AB}\)")  # an unknown command keeps its backslash: select holds it (tex-left)
    assert chi_incomplete("班长是我们学习的好____样。", ["旁", "傍", "膀", "榜"]) is None
    assert chi_incomplete("他们在行业里很有名。", ["（1）xíng yè", "（2）xíng yà", "（3）háng yè", "（4）háng yà"]) is None
    assert chi_incomplete("老师说的话。", ["a", "b", "c", "d"]) == "chi-no-blank-underline-lost"
    assert strip_num("（3）跌") == "跌" and strip_num("1. went") == "went" and strip_num("2.5 kg") == "2.5 kg" and strip_num("(4) 12") == "12"
    assert chi_incomplete("哥哥吃了一碗炒饭，但仍然觉得饿。", ["rēng rán", "réng rán", "lēng rán", "léng rán"]) is None
    assert chi_incomplete("老师让班长统计一下参加的人数。", ["记录重要的数字", "算出总体的数字", "a", "b"]) == "chi-no-blank-underline-lost"
    assert eng_incomplete("Select the most appropriate word to fill in the blank.") == "stem-instruction-only"
    assert eng_incomplete("portrayed") == "stem-instruction-only"
    assert eng_incomplete("He tried to remain poised as he realised he was trapped in the car.") == "stem-no-blank-or-question"
    assert eng_incomplete("According to the poster, when should Mr Tan ____ the book?") == "stem-needs-passage"
    assert eng_incomplete("The number of community cases _______ increased since January.") is None
    assert eng_incomplete("Choose the correct word. She _____ to school every day.") is None
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
    # poster_pieces: from the instruction (OCR "Siudy") to the questions' heading; the previous section's question 20 and
    # a poster line "21 October!" are not cut points; the scanned questions are never in a piece
    def pg(lines):  # [(y, words)] -> page_lines shape, page 1000 x 3000
        return rows_of([(100 + 60 * k, y, 150 + 60 * k, y + 30, w) for y, ws in lines for k, w in enumerate(ws.split())]), 1000, 3000
    P = {5: pg([(100, "20, (1) favourite"), (150, "(4) significant"), (300, "Siudy this poster carefully and answer questions 21 to 28."),
                (900, "Fun Festival 2018 is here"), (1500, "21 October! We are sure everyone will enjoy it"), (2400, "Come and join us all")]),
         6: pg([(200, "For each question from 21 to 28, four options are given."), (400, "21. The festival is organised by"),
                (500, "(1) Funfest.com")])}
    pieces, why = poster_pieces(P, 21)
    assert why is None and pieces == [(5, 292, 3000)], (pieces, why)
    assert poster_pieces({6: P[6]}, 21) == (None, "set-no-cut")  # no poster before the questions: held
    assert cloze_stem("这些礼物 Q16（1 表达 2 保存 3 集合 4 见证）了她对我的关爱。", 16) == "这些礼物（16）＿＿＿＿了她对我的关爱。"
    assert cloze_stem("根据短文的内容和上下文的意思，从括号中选出适当的词语。她总是（1. 保持 2. 保证 3. 保留 4. 保守）身体健康。", 17,
                      ["1. 保持", "2. 保证", "3. 保留", "4. 保守"]) \
        == "她总是（17）＿＿＿＿身体健康。"
    assert cloze_stem("但还是答应了他的________。", 18) == "但还是答应了他的（18）＿＿＿＿。"
    assert cloze_stem("根据短文的内容和上下文的意思，从括号中选出适当的词语。", 16) is None
    # the asked blank is picked by its number, not by being first; the neighbour stays a fillable blank
    assert cloze_stem("员工Q18（1设法 2提早 3创作 4分享）让它多吃。猴子Q19（1竟然 2果然 3仍然 4猛然）长不大。", 19) \
        == "员工（18）＿＿让它多吃。猴子（19）＿＿＿＿长不大。"
    assert cloze_stem("Q20.（1 无论 2 只要 3 不但 4 虽然）是日常生活，我们都应该。(（一）)根据短文的内容和上下文的意思，选出适当的答案。", 20,
                      ["1 无论", "2 只要", "3 不但", "4 虽然"]) == "（20）＿＿＿＿是日常生活，我们都应该。"
    assert strip_opts(["1 焦急", "2 紧张", "3 悲伤", "4 麻烦"]) == ["焦急", "紧张", "悲伤", "麻烦"]
    assert strip_opts(["2 年", "3 年", "4 年", "5 年"]) == ["2 年", "3 年", "4 年", "5 年"] and strip_num("3 天") == "3 天"
    # review cases (21 Nov 2026): a mislabelled bracket is not asked; an unlabelled neighbour holds the item; an instruction
    # ending in ：is stripped, not the whole stem
    assert cloze_stem("员工Q17（1设法 2提早 3创作 4分享）让它。她Q17（1 保持 2 保证 3 保留 4 保守）身体", 17,
                      ["1 保持", "2 保证", "3 保留", "4 保守"]) == "员工（17）＿＿让它。她（17）＿＿＿＿身体"
    assert cloze_stem("Q17（1 a 2 b 3 c 4 d）他（1 设法 2 提早 3 创作 4 分享）了", 17) is None
    assert cloze_stem("根据短文的内容，选出适当的词语：她总是Q17（1 保持 2 保证 3 保留 4 保守）身体健康。", 17,
                      ["1 保持", "2 保证", "3 保留", "4 保守"]) == "她总是（17）＿＿＿＿身体健康。"
    # a reading cut never starts at a question line holding 根据短文, and a paragraph numbered （1） is not an option block
    pgr = lambda lines: (rows_of([(100 + 60 * k, y, 150 + 60 * k, y + 30, w) for y, ws in lines for k, w in enumerate(ws.split())]), 1000, 3000)
    R = {9: pgr([(100, "三 阅读理解一"), (160, "根据短文的内容和上下文的意思，选出适当的答案。"), (240, "小明的故事"),
                 (300, "（1） 第一段 小明 很 早 就 起床 了"), (360, "第二段 他 去 上学"), (420, "第三段 他 很 开心"),
                 *[(480 + 60 * i, "他 和 同学们 一起 在 操场 上 跑步 ， 大家 都 跑 得 满头大汗 ， 可是 谁 也 不 愿意 停下来 休息") for i in range(4)],
                 (900, "Q21 小明 为什么 开心"), (960, "(1) 甲"), (1010, "(2) 乙"), (1060, "(3) 丙"), (1110, "(4) 丁"),
                 (1300, "Q22根据短文，下面 哪一项 是 正确的？"), (1360, "(1) 甲"), (1410, "(2) 乙"), (1460, "(3) 丙"), (1510, "(4) 丁")])}
    pc, why = chi_pieces(R, "chinese-reading", 21, 25)
    assert why is None and pc == [(9, 92, 892)], (pc, why)
    O17 = ["1 保持", "2 保证", "3 保留", "4 保守"]
    assert cloze_stem("根据短文的内容，选出适当的词语，把它的号码填写在括号内。她总是Q17（1 保持 2 保证 3 保留 4 保守）身体健康。", 17, O17) \
        == "她总是（17）＿＿＿＿身体健康。"
    assert cloze_stem("他走Q16（1 的 2 地 3 得 4 了）很快，Q17（1 的 2 地 3 得 4 了）开心", 17, ["1 的", "2 地", "3 得", "4 了"]) \
        == "他走（16）＿＿很快，（17）＿＿＿＿开心"
    assert cloze_stem("那天（1月4日）她总是Q17（1 保持 2 保证 3 保留 4 保守）身体健康。", 17, O17) == "那天（1月4日）她总是（17）＿＿＿＿身体健康。"
    assert strip_opts(["(1) 1 焦急", "(2) 2 紧张", "(3) 3 悲伤", "(4) 4 麻烦"]) == ["焦急", "紧张", "悲伤", "麻烦"]
    assert key("焦急", ["1 焦急", "2 紧张", "3 悲伤", "4 麻烦"]) == "1"
    assert strip_opts(["1反问", "2责问", "3访问", "4发问"]) == ["反问", "责问", "访问", "发问"]
    # third review: a printed blank line next to the bracket goes; an OCR'd "1）" option list left in the stem holds it
    assert cloze_stem("让我这个________（1 勤劳 2 慈祥 3 慷慨 4 勇敢）的好心人来帮助你！", 17, ["1 勤劳", "2 慈祥", "3 慷慨", "4 勇敢"]) \
        == "让我这个（17）＿＿＿＿的好心人来帮助你！"
    assert cloze_stem("便________（1）准备 2 选择 3 参加 4 走向）了很多食物", 16, ["1 准备", "2 选择", "3 参加", "4 走向"]) is None
    assert cloze_stem("她Q17（1 保持 2 保证 3 保留 4 保守）身体，（1 保持 Z保证 3 保留 4 保守）好。", 17, O17) is None
    for bad in ["她Q17（1 保持 2 保证 3 保留 4 保守）身体，（１保持 ２保证 ３保留 ４保守）好。", "他Q17（1 保持 2 保证 3 保留 4 保守）________（18）很好",
                "他Ql7（1 保持 2 保证 3 保留 4 保守）身体", "他Q17（1 保持 2 保证 3 保留 4 保守）身体。（1)高兴 (2)难过 (3)生气",
                "他Q17（1 保持 2 保证 3 保留 4 保守）。① 高兴 ② 难过", "他很________Q17（1 保持 2 保证 3 保留 4 保守）________的人"]:
        assert cloze_stem(bad, 17, O17) is None, bad
    assert cloze_stem("让我这个————Q17（1 保持 2 保证 3 保留 4 保守）的人", 17, O17) == "让我这个（17）＿＿＿＿的人"
    assert cloze_stem("我明白——如果……那只是Q17（1 保持 2 保证 3 保留 4 保守）的。", 17, O17) == "我明白——如果……那只是（17）＿＿＿＿的。"
    assert strip_opts(["1 年", "2 年", "3 年", "4 年"]) == ["1 年", "2 年", "3 年", "4 年"]
    assert cloze_stem("负责人在接受Q17（1反问 2责问 3访问 4发问）时表示。", 17, ["1反问", "2责问", "3访问", "4发问"]) == "负责人在接受（17）＿＿＿＿时表示。"
    assert scanner_marks("Study the chart below.\n(sub) Which letters represent X?") == "Study the chart below.\nWhich letters represent X?"
    assert scanner_marks("with object Y.\n(cont) The results are shown.") == "with object Y.\nThe results are shown."
    assert scanner_marks("The table shows it.\n(a) Which cell makes food?") == "The table shows it.\nWhich cell makes food?"
    assert scanner_marks("Mix (a) and (b) in the beaker.") == "Mix (a) and (b) in the beaker."  # labels inside a sentence stay
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
    rows = [r for r in rows if r["id"] not in hold]
    left = collections.Counter(r["grp"] for r in rows if r.get("grp"))
    lone = [r["id"] for r in rows if r.get("grp") and left[r["grp"]] < 2]
    if lone:  # a hold may leave a set of one: dropped, and said so
        print(f"{len(lone)} questions left alone in their set by a hold are not uploaded: {', '.join(lone[:5])}")
    return [r for r in rows if r["id"] not in lone], subs, out


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


TEX_SYM = {"times": "×", "div": "÷", "pi": "π", "angle": "∠", "ell": "ℓ", "square": "□", "cdot": "·", "cdots": "…",
           "ldots": "…", "dots": "…", "geq": "≥", "leq": "≤", "ge": "≥", "le": "≤", "neq": "≠", "ne": "≠", "triangle": "△",
           "circ": "°", "degree": "°", "left": "", "right": "", "quad": " ", "qquad": " "}
SUPER = str.maketrans("0123456789", "⁰¹²³⁴⁵⁶⁷⁸⁹")
# a JSON escape upstream ate the backslash of these commands ("\frac" stored as a form feed + "rac", "\text" as a tab + "ext")
EATEN = re.compile("\x0c(rac)|\x09(ext|frac|imes|heta|riangle|extrm)|\x0d(ight)|\x08(egin|ar)|\x0b(ec)")
EATEN_CH = {"\x0c": "f", "\x09": "t", "\x0d": "r", "\x08": "b", "\x0b": "v"}


PASSAGE = {  # passage mode: the section's questions, its sub-topic, and the set id's suffix
    "english-visual": {"subject": "english", "q": (21, 30), "st": "eng-visual-text", "section": "Visual Text", "suffix": "vt"},
    "chinese-cloze": {"subject": "chinese", "q": (16, 20), "st": "chi-cloze-mcq", "section": "短文填空", "suffix": "cz"},
    "chinese-reading": {"subject": "chinese", "q": (21, 25), "st": "chi-yuedu-mcq-text", "section": "阅读理解一", "suffix": "rd"},
}


def set_id(q, suffix="vt") -> str:
    """A passage set's id (pp_items.grp): the paper and part, plus the section."""
    return re.sub(r"[^a-z0-9]+", "-", f"{q.get('paper') or q['id']}-{q.get('part') or ''}-{suffix}".lower()).strip("-")[:80]  # no paper: a set of its own


QROW = re.compile(r"^(\d{1,2})[.,]?$")  # OCR reads "20." as "20," too
QRANGE = re.compile(r"questions?\s+(?:from\s+)?(\d{1,2})\s*(?:to|-|–|and)\s*(\d{1,2})", re.I)
STUDY = re.compile(r"^\W*(s[tli1]u?dy|read|look)\b", re.I)  # OCR: "Siudy", "Sludy"
STUDY_REST = re.compile(r"carefully|answer|question|following|below", re.I)
FOOT = re.compile(r"kiasu|exampaper|go on to|blank page|接下页|空白页|翻页|^\W*\d{1,3}\W*$|^\W*[A-Z]?\s*-\s*\d{1,2}\W*$", re.I)
QHEAD = re.compile(r"for each question|shade|optical answer", re.I)


def page_lines(jpg):
    """OCR rows of a page scan from its tesseract .tsv: ([(top, bottom, [(l, t, r, b, word)])], width, height), or None."""
    from PIL import Image
    tsv = Path(jpg).with_suffix(".tsv")
    if not Path(jpg).exists() or not tsv.exists():
        return None
    with Image.open(jpg) as im:
        W, H = im.size
    words = []
    for ln in tsv.read_text(encoding="utf-8", errors="replace").splitlines()[1:]:
        f = ln.split("\t")
        if len(f) >= 12 and f[0] == "5" and f[11].strip():
            x, y, w, h = map(int, f[6:10])
            words.append((x, y, x + w, y + h, f[11].strip()))
    return rows_of(words), W, H


def rows_of(words):
    """Words grouped into rows by position (a question number is often its own tesseract block)."""
    rows = []
    for w in sorted(words, key=lambda w: (w[1] + w[3]) / 2):
        cy = (w[1] + w[3]) / 2
        if rows and abs(cy - rows[-1][3]) < 0.6 * max(8, w[3] - w[1]):
            rows[-1][2].append(w)
            rows[-1][0], rows[-1][1] = min(rows[-1][0], w[1]), max(rows[-1][1], w[3])
        else:
            rows.append([w[1], w[3], [w], cy])
    return [(t, b, sorted(ws)) for t, b, ws, _ in rows]


def poster_pieces(pages, own_min):
    """A visual text without its questions (owner, 21 Nov 2026: the scanned questions showed next to the quiz's own text).
    pages: {page number: page_lines(...)} up to the set's first question page. A piece runs from the "Study this poster
    ... answer questions 21 to 28" line (else just below the previous section's last option) down to the section's
    "For each question from 21 to 28 ... shade" heading (else its first question's line). Returns ([(page, top, bottom)],
    None), or (None, "set-no-cut") when either end is not found: the set is held rather than shown with questions on it."""
    flat = [(p, r, pages[p][1], pages[p][2]) for p in sorted(pages) for r in pages[p][0]]
    text = lambda r: " ".join(w[4] for w in r[2])
    num = lambda r, W: int(m.group(1)) if (m := QROW.match(r[2][0][4])) and r[2][0][0] < 0.25 * W else None
    rng = lambda r: int(m.group(1)) if (m := QRANGE.search(text(r))) else None
    # a range below 21 is the previous section's ("questions 16 to 20"): never this one's
    S = max((n for _, r, _, _ in flat if (n := rng(r)) and 21 <= n <= own_min), default=None) \
        or min((n for _, r, W, _ in flat if (n := num(r, W)) and 21 <= n <= own_min and len(r[2]) >= 3), default=None)
    if not S:
        return None, "set-no-cut"
    # start: the section's instruction (a range in it must be this section's), else after the previous section's options
    # an instruction's range may wrap onto its next line ("... and answer / questions 21 to 25.")
    rng_at = lambda k: rng(flat[k][1]) or (rng(flat[k + 1][1]) if k + 1 < len(flat) and flat[k + 1][0] == flat[k][0] else None)
    study = [k for k, (_, r, _, _) in enumerate(flat) if STUDY.match(text(r)) and STUDY_REST.search(text(r))
             and rng_at(k) in (None, S) and not QHEAD.search(text(r))]
    # the end: the questions' heading ("For each question from 21 to 28 ... shade"); a line starting with the number only
    # when no heading follows ("21 October!" in a poster is not question 21)
    is_head = lambda k: bool(QHEAD.search(text(flat[k][1])))
    is_q = lambda k: num(flat[k][1], flat[k][2]) == S and len(flat[k][1][2]) >= 3
    is_end = lambda k: is_head(k) or (is_q(k) and not any(is_head(j) for j in range(k, len(flat))))
    if study:  # the last instruction before the questions (an earlier match is the previous section's)
        e0 = next((k for k in range(study[0] + 1, len(flat)) if is_end(k)), len(flat))
        # the first instruction naming this section's questions (a paper may repeat it on each page: Text 1, Text 2),
        # else the last one before the questions (an earlier one belongs to the previous section)
        k0 = next((k for k in study if k < e0 and rng_at(k) == S), max(k for k in study if k < e0))
        top0 = flat[k0][1][0] - 8
    else:
        prev = [k for k, (_, r, W, _) in enumerate(flat) if (n := num(r, W)) is not None and n < S and len(r[2]) >= 3]
        opt4 = [k for k, (_, r, _, _) in enumerate(flat) if prev and k > prev[-1] and re.match(r"^\(?4\)", r[2][0][4])]
        if not opt4:
            return None, "set-no-cut"
        k0, top0 = opt4[0], flat[opt4[0]][1][1] + 8
    end = next((k for k in range(k0 + 1, len(flat)) if is_end(k)), None)
    if end is None:
        return None, "set-no-cut"
    return cut_pieces(pages, flat[k0][0], top0, flat[end][0], flat[end][1][0] - 8)


def cut_pieces(pages, p0, top0, pe, bot_e, cjk=False):
    """The pieces of pages p0 (from top0) to pe (down to bot_e): page footers and school header lines trimmed, empty strips
    and blank pages dropped (an English poster keeps 6+ words, a Chinese passage 15+ characters)."""
    text = lambda r: " ".join(w[4] for w in r[2])
    pieces = []
    for p in sorted(pages):
        if p0 <= p <= pe:
            rows, _, H = pages[p]
            top, bot = (top0 if p == p0 else 0), (bot_e if p == pe else H)
            # the page footer (scan site, page number, "Go on to the next page", 接下页) is not part of the passage
            foot = [r[0] for r in rows if r[0] > 0.8 * H and FOOT.search(text(r))]
            bot = min([bot] + [f - 8 for f in foot])
            # the school's header line at the top of a page is no content either
            inside = [r for r in rows if top <= r[0] and r[1] <= bot and not FOOT.search(text(r)) and r[0] > 0.08 * H]
            # an empty strip, or a "BLANK PAGE" / 空白页, is no piece; a picture-only poster still has a few words
            enough = (sum(len(text(r).replace(" ", "")) for r in inside) >= 15) if cjk else (sum(len(r[2]) for r in inside) >= 6)
            if bot - top > 0.06 * H and enough:
                pieces.append((p, max(0, top), min(H, bot)))
    return (pieces, None) if pieces else (None, "set-no-cut")


CHI_HEAD = {"chinese-cloze": re.compile(r"短文填空"), "chinese-reading": re.compile(r"阅读理解")}
CHI_INSTR = re.compile(r"根据短文")
CHI_NEXT = re.compile(r"阅读理解|完成对话|短文填空|根据短文|^\W*[一二三四五六七八九十]\s*[、.．]?\s*\S{2,6}[（(]\s*\d+\s*题")


def chi_qnum(t):
    """A Chinese question row's number ("Q21当我把…", "21."), not a range ("(Q21-Q25)")."""
    m = re.match(r"^\W{0,2}[QO0]?\s?(\d{1,2})(?![\d\-–－—~])", t)  # OCR reads "Q21" as "021" too
    return int(m.group(1)) if m else None


def chi_pieces(pages, kind, first, last):
    """A Chinese passage without its questions (owner, 21 Nov 2026: no question shown twice). Reading (阅读理解一): from
    the section heading (else the 根据短文 instruction) down to the line above the first question. Cloze (短文填空): the
    passage holds its blanks, so it runs from the heading to the end of the page holding the last blank, or to the next
    section's heading on that page. (None, "set-no-cut") when an end is not found."""
    flat = [(p, r) for p in sorted(pages) for r in pages[p][0]]
    text = lambda r: "".join(w[4] for w in r[2])
    blank = lambda n: re.compile(rf"Q\s?{n}\s?[（(]")
    # the first question (or blank) the OCR read: an OCR slip on one number ("QIO(" for Q19) falls back to the next
    if kind == "chinese-reading":
        hit = lambda k, n: chi_qnum(text(flat[k][1])) == n and not CHI_INSTR.search(text(flat[k][1]))
    else:
        hit = lambda k, n: bool(blank(n).search(text(flat[k][1])))
    qk = next((k for n in range(first, last + 1) for k in range(len(flat)) if hit(k, n)), None)
    if qk is None:
        return None, "set-no-cut"
    # the start: the later of the section's heading and its 根据短文 instruction before the questions (a heading the OCR
    # missed must not let an earlier mention, or the previous section, in)
    heads = [k for k in range(qk) if CHI_HEAD[kind].search(text(flat[k][1])) or CHI_INSTR.search(text(flat[k][1]))]
    if not heads:
        return None, "set-no-cut"
    k0 = heads[-1]
    if k0 > 0 and CHI_HEAD[kind].search(text(flat[k0 - 1][1])) and flat[k0 - 1][0] == flat[k0][0]:
        k0 -= 1  # keep the heading line just above the instruction
    if kind == "chinese-reading":
        return chi_reading_pieces(pages, flat, first, last)
    lk = next((k for n in range(last, first - 1, -1) for k in range(len(flat) - 1, qk - 1, -1) if hit(k, n)), None)
    if lk is None:
        return None, "set-no-cut"
    pe = flat[lk][0]
    nxt = next((k for k in range(lk + 1, len(flat)) if flat[k][0] == pe and CHI_NEXT.search(text(flat[k][1]))), None)
    return cut_pieces(pages, flat[k0][0], flat[k0][1][0] - 8, pe, flat[nxt][1][0] - 8 if nxt is not None else pages[pe][2], cjk=True)


CHI_RANGE = re.compile(r"[(（]\s*Q?\s?2[01]\s*[-—–－~至到]")  # "(Q21—Q25)" under the reading instruction
CHI_MIN_PASSAGE = 150  # characters the OCR read inside a reading passage
CHI_OPT1 = re.compile(r"^\W{0,2}[(（《]\s*[1iIl]\s*[)）]")  # OCR: "(i)"
CHI_BLANKROW = re.compile(r"Q\s?\d{1,2}\s?[（(]\s*1|[（(]\s*1\s*[.．、]?\s*[\u3400-\u9fff][^（）()]*(?<!\d)4\s*[.．、]?")


def chi_reading_pieces(pages, flat, first, last):
    """Reading (阅读理解一): the passage from the section's heading, instruction or "(Q21—Q25)" line down to the first
    question: a question line, or the first "(1)" option row (cut above the question line over it, which the OCR may not
    have read as "Q21"). A cloze blank inside is the previous section: held."""
    text = lambda r: "".join(w[4] for w in r[2])
    # a question line: "Q21…"/"021…" (any OCR'd number, "Q2l" too) or "21." — never a bare "22岁那年…" passage line
    isq = lambda k: not CHI_RANGE.search(text(flat[k][1])) and bool(
        re.match(rf"^\W{{0,2}}[QO0]\s?(?:{'|'.join(map(str, range(first, last + 1)))}|{str(first)[0]}[lI])(?!\d)", text(flat[k][1]))  # "Q21", "Q2l", "021"
        or ((n := chi_qnum(text(flat[k][1]))) and first <= n <= last and re.match(r"^\W{0,2}\d{1,2}\s*[.．、]", text(flat[k][1]))))
    # an option block: a "(1)" row with a "(2)" row within the next 4 (a passage paragraph numbered （1） is not one)
    opt_block = lambda k: bool(CHI_OPT1.match(text(flat[k][1]))) and any(
        re.match(r"^\W{0,2}[(（《]?\s*[2②]\s*[)）]", text(flat[j][1])) for j in range(k + 1, min(k + 5, len(flat))))
    # a start: the heading, the instruction or the "(Q21—Q25)" line, never a question line ("Q22根据短文，…")
    starts = [k for k, (_, r) in enumerate(flat) if (CHI_HEAD["chinese-reading"].search(text(r)) or CHI_INSTR.search(text(r))
              or CHI_RANGE.search(text(r))) and not isq(k) and not re.search(r"词语", text(r))]  # not the cloze's instruction (选出适当的词语)
    for k0 in reversed(starts):
        end = next((k for k in range(k0 + 1, len(flat)) if isq(k) or opt_block(k)), None)
        if end is None:
            continue
        if not isq(end):  # an option block whose question line the OCR did not read: where it starts is a guess, so held
            return None, "set-no-cut"
        if end - k0 < 3:  # nothing between: an instruction right above the questions, try an earlier start
            continue
        if any(CHI_BLANKROW.search(text(flat[k][1])) for k in range(k0, end)):
            return None, "set-no-cut"
        while k0 > 0 and flat[k0 - 1][0] == flat[k0][0] and (CHI_HEAD["chinese-reading"].search(text(flat[k0 - 1][1]))
                                                            or CHI_INSTR.search(text(flat[k0 - 1][1]))):
            k0 -= 1  # keep the heading and instruction lines with the range line
        top0 = flat[k0][1][0] - (int(0.06 * pages[flat[k0][0]][2]) if CHI_RANGE.search(text(flat[k0][1])) else 8)
        got = cut_pieces(pages, flat[k0][0], top0, flat[end][0], flat[end][1][0] - 8, cjk=True)
        # the automatic check: option rows inside mean a question the OCR could not read got in (owner: no question twice)
        inside = [text(r) for p, t, b in (got[0] or []) for r in pages[p][0] if t <= r[0] and r[1] <= b]
        if sum(bool(re.match(r"^\W{0,2}(?:[(（《]?\s*[1-4iIl]\s*[)）]|[①②③④])", x)) for x in inside) >= 2:
            return None, "set-no-cut"
        if sum(len(x) for x in inside) < CHI_MIN_PASSAGE:  # a reading passage is long: a strip is a wrong cut
            return None, "set-no-cut"
        return got
    return None, "set-no-cut"


def cloze_stem(t, n, opts=()):
    """A Chinese cloze blank's sentence with the asked blank as the site writes it, （16）＿＿＿＿: the paper's inline options
    ("Q16（1 表达 2 保存 …）", or the bracket alone, picked by its own number or by holding the item's options) or a bare
    line become the blank; a neighbouring blank becomes （19）＿＿, which the quiz fills once it is answered. None when the
    asked blank is not found."""
    # the section's instruction, read into the first blank's text (OCR may end it with ：or ，)
    t, k = re.subn(r"^\s*根据短文[^。（(Q]*[。：:]\s*", "", t or "")
    if not k:
        t = re.sub(r"^\s*根据短文[^。：:]*(?:词语|答案)[^。：:，,]*[。：:，,]?\s*", "", t)
    t = re.sub(r"(?<=\S)\s*[(（]*\s*[（(][一二三]\s*[）)]\s*[)）]*\s*根据短文.*$|(?<=\S)\s*根据短文.*$", "", t, flags=re.S)  # the next section's
    t = re.sub(r"(?<![\u3400-\u9fff])Q\s?\d{1,2}\s*[.．](?!\d)", "", t)  # a stray question label ("Q20.")
    ask = f"（{n}）＿＿＿＿"
    words = {o.replace(" ", "") for o in strip_opts(list(opts)) if o}
    # the bracket's own options, split at their numbers: whole options compared, not substrings (的 inside 目的)
    own = lambda g: {x.replace(" ", "") for x in re.split(r"[1-4]\s*[.．、]?", re.sub(r"^(?:Q\s?\d{1,2}\s?)?[（(]|[）)]$", "", g)) if x.strip()}
    holds = lambda g: len(words & own(g)) >= 3
    labelled = lambda g: bool(re.match(rf"Q\s?{n}\s?[（(]", g))
    t2, k = t, 0
    brackets = list(re.finditer(r"(?:Q\s?\d{1,2}\s?)?[（(][^（）()]*[）)]", t))
    # the bracket labelled Q{n} that holds this item's options; else an unlabelled one holding them (two blanks may
    # share an option set: 的/地/得); by label alone only when the options are unknown
    pick = next((m for m in brackets if labelled(m.group(0)) and (holds(m.group(0)) if words else True)), None) \
        or next((m for m in brackets if words and not re.match(r"Q\s?\d", m.group(0)) and holds(m.group(0))), None)
    if pick:  # a printed blank line next to the bracket ("这个________（1 …）") goes with it; one on each side is ambiguous
        line = r"(?:[_＿]{2,}|[—－-]{4,}|﹍{2,}|…{3,}|\.{4,})"  # 破折号 —— and 省略号 …… are punctuation, not blanks
        pre, post = t[:pick.start()], t[pick.end():]
        lp, rp = re.search(line + r"\s*$", pre), re.match(r"\s*" + line, post)
        if lp and rp:
            return None
        t2, k = (pre[:lp.start()] if lp else pre) + ask + (post[rp.end():] if rp else post), 1
    if not k and len(re.findall(r"_{2,}|＿{2,}|[（(]\s*[)）]", t)) == 1:
        t2, k = re.subn(r"_{2,}|＿{2,}|[（(]\s*[)）]", ask, t)
    if not k:
        return None
    t2 = re.sub(r"Q\s?(\d{1,2})\s?[（(][^（）()]*[）)]", r"（\1）＿＿", t2)  # neighbouring blanks
    if re.search(r"[（(]\s*1\s*[.．、]?\s*[\u3400-\u9fff][^（）()]*?(?<!\d)2\s*[.．、]?\s*[\u3400-\u9fff][^（）()]*?(?<!\d)3\s*[.．、]?\s*[\u3400-\u9fff][^（）()]*?(?<!\d)4\s*[.．、]?\s*[\u3400-\u9fff][^（）()]*[）)]", t2):
        return None  # an unlabelled neighbouring blank: the quiz cannot number or fill it
    t2 = re.sub(r"\s+(?=[\u3400-\u9fff（，。！？＿])|(?<=[\u3400-\u9fff）＿])\s+", "", t2).strip()
    # the automatic check: exactly the asked blank; once the quiz's own blanks are taken out, no blank line, no option list
    # (1 … 2 … 3 … 4, inside a bracket or not, however OCR'd) and no question label or instruction left
    rest = re.sub(r"（\d{1,2}）＿＿＿＿|（\d{1,2}）＿＿", "", t2)
    if t2.count("＿＿＿＿") != 1 or re.search(r"[_＿]", rest) or re.search(r"Q\s?[\dlI]|根据短文|号码|填写在", rest) \
            or re.search(r"[０-９①②③④]|[—－]{4,}|﹍{2,}|…{3,}|\.{4,}|（\d{1,2}）|[(（]\s*[1-4lI]\s*[)）.．、]", rest) \
            or re.search(r"(?<!\d)1\D{1,10}?(?<!\d)2\D{1,10}?(?<!\d)3\D{1,10}?(?<!\d)4(?!\d)", rest) \
            or any(len(re.findall(r"(?<!\d)[1-4]\s*[.．、]?\s*[\u3400-\u9fff“《]", g)) >= 3 for g in re.findall(r"[（(][^（）()]*[）)]?", rest)):
        return None  # a bracket with 3+ numbered words is an option list even with one number misread (a date has 2)
    return t2


def set_pages(rows, out, kind="english-visual"):
    """Every question of a set shows the same pages: from up to three pages before the set's first question page (the poster or
    passage, which may run over two pages) to its first question page. Sets of one question, and sets whose questions spread
    over more than 5 pages (bad page data), are dropped. The pictures are the poster pieces only (poster_pieces), cut
    from the page scans into OUT/setpages."""
    by, dropped, seen_sets = collections.defaultdict(list), [], set()
    for r in rows:
        if r.get("grp"):
            by[r["grp"]].append(r)
    for g, rs in by.items():
        if len(rs) < 2:
            for r in rs:
                rows.remove(r)
                dropped.append((r, "set-one-question"))
            continue
        # the same paper filed under two schools: a set whose questions and options all match an earlier set is a copy
        sig = tuple(sorted((re.sub(r"\W+", " ", r["stem"]).strip().lower(), tuple(r["options"])) for r in rs))
        if sig in seen_sets:
            for r in rs:
                rows.remove(r)
                dropped.append((r, "set-duplicate"))
            continue
        seen_sets.add(sig)
        pages = sorted({p for r in rs for p in r["pages"]})
        pdir = Path(rs[0]["pages_dir"])
        if pages[-1] - pages[0] > 4:  # a visual text and its questions fit in a few pages: a longer span is bad page data
            for r in rs:
                rows.remove(r)
                dropped.append((r, "set-bad-pages"))
            continue
        # a second text inside the set's questions ("answer questions 27 to 28" on a later page): its questions would show
        # the first text's poster, so the set is held
        seqs = [r["seq"] for r in rs]
        later = []
        for p in (range(max(1, pages[0] - 3), pages[-1] + 1) if kind == "english-visual" else ()):  # a Chinese section: one passage
            v = page_lines(pdir / f"p{p:04d}.jpg")
            lines = [" ".join(w[4] for w in row[2]) for row in v[0]] if v else []
            for i in range(len(lines)):  # each row with the next: a range may wrap ("questions" / "26 to 28")
                m = QRANGE.search(" ".join(lines[i:i + 2]))
                if m and min(seqs) < int(m.group(1)) <= max(seqs):
                    later.append(int(m.group(1)))
        if later:
            for r in rs:
                rows.remove(r)
                dropped.append((r, "set-two-texts"))
            continue
        # the poster: up to three pages before the first question page, and that page down to the questions
        if kind == "english-visual":
            win = {p: page_lines(pdir / f"p{p:04d}.jpg") for p in range(max(1, pages[0] - 3), pages[0] + 1)}
            pieces, why = poster_pieces({p: v for p, v in win.items() if v}, min(r["seq"] for r in rs))
        else:  # a Chinese passage: from two pages before its questions to the last question page
            win = {p: page_lines(pdir / f"p{p:04d}.jpg") for p in range(max(1, pages[0] - 2), pages[-1] + 1)}
            pieces, why = chi_pieces({p: v for p, v in win.items() if v}, kind, PASSAGE[kind]["q"][0], PASSAGE[kind]["q"][1])
        if not pieces:
            for r in rs:
                rows.remove(r)
                dropped.append((r, why))
            continue
        from PIL import Image
        (out / "setpages").mkdir(parents=True, exist_ok=True)
        files = []
        for n, (p, top, bot) in enumerate(pieces, 1):
            f = out / "setpages" / f"{g}-{n}.png"
            with Image.open(pdir / f"p{p:04d}.jpg") as im:
                im.crop((0, top, im.size[0], bot)).save(f)
            files.append(str(f))
        first = min(rs, key=lambda r: (r["seq"], r["id"]))["id"]
        for r in rs:
            r["set_pages"] = files
            r["set_owner"] = first  # the pages are stored once, under the set's first question
            r.pop("pages_dir", None)
    return dropped


def tex_to_text(t: str) -> str:
    """LaTeX in an OCR'd stem or option as plain text, the way the site writes Maths ("3/5", "2 1/3", "×", "°"): the owner's
    report of 21 Nov 2026 ("\\frac{3}{4}" shown raw; 359 Maths items). Money "$" is left alone. Anything it cannot turn into
    text keeps its backslash, and select holds that item (tex-left)."""
    t = EATEN.sub(lambda m: "\\" + EATEN_CH[m.group(0)[0]] + m.group(0)[1:], t)
    t = re.sub(r"^\s*\$(?!\s*\d)([^$]+)\$\s*$", r"\1", t)  # a whole option in TeX dollars "$(50-23z)$" (money "$(2x - 14)" has one $)
    if "\\" not in t and "^" not in t:
        return t
    t = re.sub(r"\\{2,}(?=[A-Za-z()\[\]])", r"\\", t)  # "\\\\times" -> "\\times"
    t = re.sub(r"\\n(?=[A-Z0-9\s(]|$)", "\n", t)  # a literal backslash-n from the OCR ("90.9\nFind"), not \neq
    t = t.replace("\\$", "\x00")  # an escaped dollar is money: keep it out of the $...$ math rule
    t = re.sub(r"\$(?!\s*\d)([^$]*\\[^$]*)\$", r"\1", t)  # $...$ math holding a command; money ("$5 ...") starts with a digit
    t = re.sub(r"\\[()\[\]]", " ", t)  # \( \) \[ \] wrappers out first, so "8\(\frac{1}{2}\)" is seen as a mixed number
    t = re.sub(r"\\(?:text|mathrm|textrm|mbox)\s*\{([^{}]*)\}", r"\1", t)
    t = re.sub(r"\\sqrt\s*\{([^{}]*)\}", lambda m: "√" + (m.group(1) if re.fullmatch(r"\w+", m.group(1)) else f"({m.group(1)})"), t)
    t = re.sub(r"\\[dt]?frac\s*(\d)(\d)(?!\d)", r"\\frac{\1}{\2}", t)  # "\frac12" -> "\frac{1}{2}"
    t = re.sub(r"(\d)\s*(?=\\[dt]?frac)", r"\1 ", t)  # a mixed number "2\frac{1}{3}" keeps its space: "2 1/3"
    t = re.sub(r"\}\s*(?=\\[dt]?frac)", "} ", t)  # two fractions side by side stay apart: "1/2 1/3"
    def frac(m):
        a, b = m.group(1).strip(), m.group(2).strip()
        wrap = lambda x: f"({x})" if re.search(r"[\s+\-−×÷]", x) else x
        return f"{wrap(a)}/{wrap(b)}"
    for _ in range(3):  # nested fractions, innermost first
        t = re.sub(r"\\[dt]?frac\s*\{([^{}]*)\}\s*\{([^{}]*)\}", frac, t)
    t = re.sub(r"\^\s*(?:\{\s*\\circ\s*\}|\\circ)", "°", t)  # ^\circ or ^{\circ}; the space after stays
    t = re.sub(r"\^\s*\{(\d+)\}|\^(\d)", lambda m: (m.group(1) or m.group(2)).translate(SUPER), t)  # bare ^23 raises the 2 only (TeX)
    t = re.sub(r"\\([A-Za-z]+)(?![A-Za-z])", lambda m: TEX_SYM.get(m.group(1), m.group(0)), t)  # whole command names only
    t = re.sub(r"\\[,;!:]", " ", t).replace("\\%", "%").replace("\x00", "$")
    t = re.sub(r"[ \t]+(?=[⁰¹²³⁴⁵⁶⁷⁸⁹°])", "", t)  # "8 cm \(^2\)" -> "8 cm²"
    t = re.sub(r"[ \t]+(?=[?!,;:]|\.(?!\d))", "", t)  # "in 1/2 ?" -> "in 1/2?" (a wrapper's space; ".5" stays)
    t = re.sub(r"[ \t]{2,}", " ", t)
    return re.sub(r"\( (?=\S)|(?<=\S) \)", lambda m: m.group(0).strip(), t).strip()


SUBTOPIC_DB = re.compile(r"^[a-z0-9-]{3,120}$")  # pp_items_subtopic_check (migration 009; 004 allowed 80)


def upload(a):
    rows, usubs, out = selection(a)
    bad = sorted({r["subtopic"] for r in rows if not SUBTOPIC_DB.fullmatch(r["subtopic"])})
    if bad:  # the database refuses the whole batch: say so before sending anything
        sys.exit(f"sub-topic ids the database would refuse (pp_items_subtopic_check): {bad}")
    ord_ = easier_first(rows)  # needs migration 006 (pp_items.ord) on the live project
    figs = collections.defaultdict(list)
    for m in jl(out / "figures.jsonl"):
        figs[m["pp_id"]].append({"path": m["path"], "w": m["w"], "h": m["h"]})
    missing = [r["id"] for r in rows if (r["crops"] and len(figs[r["id"]]) != len(r["crops"]))
               or (r.get("set_pages") and len(figs[r["id"]]) != len(r["set_pages"]))]  # a set row without its pages too
    if missing:
        sys.exit(f"{len(missing)} rows lack their WebP figures: run `figures` first")
    db = [{"id": r["id"], "src_id": r["src_id"], "subject": r["subject"], "subtopic": r["subtopic"], "level": r["level"],
           "pattern": r["pattern"], "stem": r["stem"], "options": r["options"], "answer": r["answer"],
           "figures": figs[r["id"]], "year": r["year"], "school": r["school"], "paper": r["paper"],
           "qno": r["qno"], "marks": r["marks"], "blind_src": r["blind_src"], "ord": ord_[r["id"]], "active": True,
           "grp": r.get("grp"), "seq": r.get("seq")} for r in rows]
    nfig = sum(len(d["figures"]) for d in db)
    print(f"{len(db)} rows, {nfig} figures, sub-topics {len({d['subtopic'] for d in db})}")
    if not db:  # ponytail: an empty selection is almost always a wrong --out; stop before touching the table or pp_counts
        sys.exit(f"nothing selected under {a.out}/{a.subject} for those sub-topics: wrong --out? "
                 "(the 2025-26 import lives in /data/alvin/tmp/cookie-codex/ppimport/final2526)")
    big = sorted({f["path"] for d in db for f in d["figures"] if (out / "figures" / Path(f["path"]).name).stat().st_size > FIG_MAX})
    if big:  # checked before anything is sent, dry run included: a half-sent upload leaves pictures without rows
        sys.exit(f"{len(big)} pictures exceed the bucket's {FIG_MAX // 1024} KB limit (e.g. {big[0]}): re-run `figures`")
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
    sent = set()  # a passage set's pages are shared by its questions: send each file once
    for d in db:
        for f in d["figures"]:
            if f["path"] in sent:
                continue
            sent.add(f["path"])
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
    p.add_argument("--passage", choices=("", *PASSAGE), default="", help="select: passage sets instead of single questions")
    a = p.parse_args()
    {"select": select, "figures": figures, "review": review, "upload": upload, "counts": counts, "cropcheck-apply": cropcheck_apply, "where": where, "selftest": lambda _a: selftest()}[a.cmd](a)


if __name__ == "__main__":
    main()
