"""Validate the English item files and the compiled banks; exits non-zero on any failure.

    python3 scripts/quiz/check_english.py
"""
import json
import re
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).parent
ROOT = HERE.parents[1]
SYL = json.loads((ROOT / "site" / "src" / "data" / "syllabus" / "english.json").read_text())
OUTCOMES = {o["id"] for st in SYL["strands"] for t in st["topics"] for sb in t["subtopics"] for o in sb["outcomes"]}
SUBS = {sb["id"] for st in SYL["strands"] for t in st["topics"] for sb in t["subtopics"]}
PATTERNS = {p["id"] for p in json.loads((HERE / "english" / "patterns.json").read_text())["patterns"]}
LEVELS = {"basic", "intermediate", "competent"}
BLANK = "____"
errors = []


def end_punct(s):
    return s.rstrip()[-1] if s.rstrip()[-1:] in ".?!," else ""


for f in sorted((HERE / "english" / "items").glob("*.json")):
    data = json.loads(f.read_text())
    sub = data.get("subtopic")
    if sub not in SUBS:
        errors.append(f"{f.name}: unknown subtopic {sub}")
    keys = Counter(it.get("key") for it in data["items"])
    stems = Counter(it.get("stem") for it in data["items"])
    for it in data["items"]:
        e = lambda m: errors.append(f"{f.name} {it.get('key')}: {m}")
        if keys[it.get("key")] > 1: e("duplicate key")
        if stems[it.get("stem")] > 1: e("duplicate stem")
        if it.get("level") not in LEVELS: e(f"bad level {it.get('level')}")
        if it.get("outcome") not in OUTCOMES or not str(it.get("outcome", "")).startswith(str(sub)): e(f"bad outcome {it.get('outcome')}")
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

# compiled banks: unique ids, 4-option shape
ids = Counter()
for f in sorted((ROOT / "site" / "src" / "data" / "quiz" / "english").glob("*.json")):
    for q in json.loads(f.read_text())["questions"]:
        ids[q["id"]] += 1
        if len(q["options"]) != 4 or not 0 <= q["answer"] < 4 or q["explain"][q["answer"]] is not None:
            errors.append(f"{f.name} {q['id']}: bad compiled shape")
errors += [f"duplicate question id {i}" for i, n in ids.items() if n > 1]

print(f"checked {sum(1 for _ in (HERE / 'english' / 'items').glob('*.json'))} item files, {sum(ids.values())} shipped questions")
for m in errors[:40]:
    print("FAIL", m)
print(f"{len(errors)} failures")
sys.exit(1 if errors else 0)
