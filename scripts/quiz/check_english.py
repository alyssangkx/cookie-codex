"""Validate the English item files and the compiled banks; exits non-zero on any failure.

    python3 scripts/quiz/check_english.py
"""
import json
import re
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
from bankcommon import PASSAGE  # noqa: E402
ROOT = HERE.parents[1]
SYL = json.loads((ROOT / "site" / "src" / "data" / "syllabus" / "english.json").read_text())
OUTCOMES = {o["id"] for st in SYL["strands"] for t in st["topics"] for sb in t["subtopics"] for o in sb["outcomes"]}
SUBS = {sb["id"] for st in SYL["strands"] for t in st["topics"] for sb in t["subtopics"]}
# sub-topics are the PSLE Paper 2 sections; each item also names its MOE syllabus outcome (metadata)
SYLLABUS = {o["id"] for st in SYL["syllabusStrands"] for t in st["topics"] for sb in t["subtopics"] for o in sb["outcomes"]}
SUB_OF = {sb["id"]: sb for st in SYL["strands"] for t in st["topics"] for sb in t["subtopics"]}
OPEN_SECTIONS = {k for k, sb in SUB_OF.items() if not any(o.get("mcqTestable") for o in sb["outcomes"])}  # "Coming soon"
# the section's format, flagged on the sub-topic: "passage" sections take only passage-set items (vis-, read-, ecloze-),
# "cloze" ones only blank-filling ecloze- sets (the quiz page fills their blanks from the same flag); other sections
# take only single items. So a one-sentence item cannot pass for a Vocabulary Cloze passage.
PATTERNS = {p["id"] for p in json.loads((HERE / "english" / "patterns.json").read_text())["patterns"]}
LEVELS = {"basic", "intermediate", "competent"}
BLANK = "____"
errors = []
VISUAL_KINDS = {"poster", "notice", "brochure", "timetable", "email"}


def visual_errors(v):
    """Schema of an item's "visual": plain strings only (the page escapes them, but HTML has no place in them)."""
    if not isinstance(v, dict): return ["visual is not an object"]
    out = []
    extra = set(v) - {"kind", "title", "subtitle", "blocks", "footer"}
    if extra: out.append(f"visual has unknown fields {sorted(extra)}")
    if v.get("kind") == "email":
        lines = [l for blk in v.get("blocks") or [] if isinstance(blk, dict) for l in blk.get("lines") or [] if isinstance(l, str)]
        if not (str(v.get("subtitle", "")).startswith("From:") or any(l.startswith("From:") for l in lines)):
            out.append("email visual must show its sender (subtitle or a From: line)")
    if v.get("kind") == "timetable":
        if not any(isinstance(blk, dict) and any(isinstance(l, str) and " | " in l for l in blk.get("lines") or []) for blk in v.get("blocks") or []):
            out.append("timetable visual needs at least one block with ' | ' rows")
    if v.get("kind") not in VISUAL_KINDS: out.append(f"visual kind {v.get('kind')!r} not in {sorted(VISUAL_KINDS)}")
    texts = []
    for f in ("title", "subtitle", "footer"):
        if f in v:
            if not isinstance(v[f], str) or not v[f].strip(): out.append(f"visual {f} must be a non-empty string")
            else: texts.append(v[f])
    if not isinstance(v.get("title"), str): out.append("visual needs a title")
    b = v.get("blocks")
    if not isinstance(b, list) or not b: out.append("visual blocks must be a non-empty list")
    else:
        for blk in b:
            if not isinstance(blk, dict) or set(blk) - {"heading", "lines"}: out.append("visual block must be {heading?, lines}"); continue
            if "heading" in blk:
                if not isinstance(blk["heading"], str) or not blk["heading"].strip(): out.append("visual block heading must be a non-empty string")
                else: texts.append(blk["heading"])
            ln = blk.get("lines")
            if not isinstance(ln, list) or not ln or any(not isinstance(x, str) or not x.strip() for x in ln):
                out.append("visual block lines must be a non-empty list of non-empty strings")
            else: texts += ln
    if any(re.search(r"<[A-Za-z/!]|&[#A-Za-z0-9]+;", t) for t in texts): out.append("visual text must be plain (no HTML or entities)")
    return out


def end_punct(s):
    return s.rstrip()[-1] if s.rstrip()[-1:] in ".?!," else ""


# keys and stems must be unique per SUB-TOPIC across files (several files can share one sub-topic, and the
# review verdict, shuffle seed and question id are all keyed by sub-topic|key)
_all = [(f, json.loads(f.read_text())) for f in sorted((HERE / "english" / "items").glob("*.json"))]
sub_keys = Counter((d.get("subtopic"), it.get("key")) for _, d in _all for it in d["items"])
sub_stems = Counter((d.get("subtopic"), it.get("stem")) for _, d in _all for it in d["items"])

sets = {}
for f in sorted((HERE / "english" / "items").glob("*.json")):
    data = json.loads(f.read_text())
    sub = data.get("subtopic")
    if sub not in SUBS:
        errors.append(f"{f.name}: unknown subtopic {sub}")
    elif sub in OPEN_SECTIONS and data["items"]:
        errors.append(f"{f.name}: {sub} is an open-answer section; the site has no MCQ items for it yet")
    for it in data["items"]:
        e = lambda m: errors.append(f"{f.name} {it.get('key')}: {m}")
        if sub_keys[(sub, it.get("key"))] > 1: e("duplicate key in this sub-topic")
        if sub_stems[(sub, it.get("stem"))] > 1: e("duplicate stem in this sub-topic")
        if it.get("level") not in LEVELS: e(f"bad level {it.get('level')}")
        if it.get("outcome") not in OUTCOMES or not str(it.get("outcome", "")).startswith(str(sub)): e(f"bad outcome {it.get('outcome')}")
        if it.get("syllabus") not in SYLLABUS: e(f"bad syllabus outcome {it.get('syllabus')}")
        if it.get("pattern") not in PATTERNS: e(f"unknown pattern {it.get('pattern')}")
        stem = str(it.get("stem", ""))
        opts = it.get("options", [])
        if not stem.strip(): e("empty stem")
        elif not re.search(r"_{3,}", stem) and "?" not in stem: e(f"stem has no blank ({BLANK}) and asks no question")
        if len(opts) != 4 or len(set(opts)) != 4 or any(not isinstance(o, str) or not o.strip() for o in opts):
            e(f"options not 4 distinct non-empty strings: {opts}")
        else:
            if len({o.strip().lower() for o in opts}) != 4: e(f"options differ only by case: {opts}")
            # "I" (and words after it, e.g. "I'm") is always capitalised, so it never counts as mixed case
            cased = {o.lstrip()[0].isupper() for o in opts if not (o.split() or [""])[0].split("'")[0] == "I"}
            if len(cased) > 1: e(f"options start with mixed case: {opts}")
            if len({end_punct(o) for o in opts}) > 1: e(f"options end with inconsistent punctuation: {opts}")
        a = it.get("answer")
        ex = it.get("explain", [])
        if not isinstance(a, int) or not 0 <= a < 4: e("answer out of range")
        elif len(ex) != 4 or ex[a] is not None or any(not (x and x.get("tag") and x.get("why")) for i, x in enumerate(ex) if i != a):
            e("explain must be null for the answer and {tag, why} for each wrong option")
        if not it.get("solution"): e("missing solution")
        m = PASSAGE.match(str(it.get("key", "")))
        sec = SUB_OF.get(sub, {})
        if bool(m) != bool(sec.get("passage")):
            e("passage sections take only passage-set items, other sections only single items")
        elif bool(m and m[1] == "ecloze") != bool(sec.get("cloze")):
            e("ecloze- sets go in a cloze section, and a cloze section takes only ecloze- sets")
        if m:
            sets.setdefault((sub, m[1], m[2]), []).append(it)
        if "visual" in it:
            if not (m and m[1] == "vis"): e("visual is only for vis-NN-K set items")
            for msg in visual_errors(it["visual"]): e(msg)
        elif m and m[1] == "vis": e("vis- item has no visual")
        if m and m[1] == "ecloze":
            asked = re.findall(r"\((\d+)\) _{8}(?!_)", stem)
            if len(asked) != 1 or int(asked[0]) != int(m[3]): e(f"ecloze stem needs exactly one asked blank (N) ________ with N = {m[3]}, found {asked}")
            if any(len(u) != 4 for n, u in re.findall(r"\((\d+)\) (_+)", stem) if int(n) != int(m[3])):
                e("ecloze: every blank other than the asked one must be written (k) ____ (4 underscores)")

for (sub, kind, nn), its in sets.items():
    nums = sorted(int(PASSAGE.match(i["key"])[3]) for i in its)
    if nums != list(range(1, len(nums) + 1)): errors.append(f"{sub} {kind}-{nn}: set numbers {nums} are not 1..N")
    if len({i.get("level") for i in its}) > 1: errors.append(f"{sub} {kind}-{nn}: a set must sit at one level")
    if kind == "vis" and len({json.dumps(i.get("visual"), sort_keys=True) for i in its}) > 1:
        errors.append(f"{sub} vis-{nn}: items of a set must share an identical visual")

# compiled banks: unique ids, 4-option shape
ids = Counter()
for f in sorted((ROOT / "site" / "src" / "data" / "quiz" / "english").glob("*.json")):
    for q in json.loads(f.read_text())["questions"]:
        ids[q["id"]] += 1
        if len(q["options"]) != 4 or not 0 <= q["answer"] < 4 or q["explain"][q["answer"]] is not None:
            errors.append(f"{f.name} {q['id']}: bad compiled shape")
        if "visual" in q:
            errors += [f"{f.name} {q['id']}: {m}" for m in visual_errors(q["visual"])]
        if ("group" in q) != ("seq" in q): errors.append(f"{f.name} {q['id']}: group and seq go together")
        if len(q["outcomes"]) != 2 or q["outcomes"][1] not in SYLLABUS:
            errors.append(f"{f.name} {q['id']}: outcomes must be [section outcome, syllabus outcome]")
errors += [f"duplicate question id {i}" for i, n in ids.items() if n > 1]

print(f"checked {sum(1 for _ in (HERE / 'english' / 'items').glob('*.json'))} item files, {sum(ids.values())} shipped questions")
for m in errors[:40]:
    print("FAIL", m)
print(f"{len(errors)} failures")
sys.exit(1 if errors else 0)
