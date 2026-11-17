"""Validate the Chinese item files and the compiled banks; exits non-zero on any failure.

    python3 scripts/quiz/check_chinese.py
"""
import json
import re
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).parent
ROOT = HERE.parents[1]
SYL = json.loads((ROOT / "site" / "src" / "data" / "syllabus" / "chinese.json").read_text())
OUTCOMES = {o["id"] for st in SYL["strands"] for t in st["topics"] for sb in t["subtopics"] for o in sb["outcomes"]}
SUBS = {sb["id"] for st in SYL["strands"] for t in st["topics"] for sb in t["subtopics"]}
PATTERNS = {p["id"] for p in json.loads((HERE / "chinese" / "patterns.json").read_text())["patterns"]}
DIALOGUE = "chi-dialogue-mcq"
LEVELS = {"basic", "intermediate", "competent"}
errors = []

for f in sorted((HERE / "chinese" / "items").glob("*.json")):
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
        opts = it.get("options", [])
        n = 8 if sub == DIALOGUE else 4  # dialogue items pick from 8 shared phrases
        if len(opts) != n or len(set(opts)) != n: e(f"options not {n} distinct: {opts}")
        a = it.get("answer")
        ex = it.get("explain", [])
        if not isinstance(a, int) or not 0 <= a < n: e("answer out of range")
        elif len(ex) != n or ex[a] is not None or any(not (x and x.get("tag") and x.get("why")) for i, x in enumerate(ex) if i != a):
            e("explain must be null for the answer and {tag, why} for each wrong option")
        if not it.get("solution"): e("missing solution")

    if sub == DIALOGUE:  # sets: key duihua-NN-K, K=1..4; one stem and one option list per set; each answer used once
        sets = {}
        for it in data["items"]:
            m = re.match(r"^duihua-(\d+)-([1-4])$", str(it.get("key")))
            if not m:
                errors.append(f"{f.name} {it.get('key')}: dialogue key must be duihua-NN-K, K=1..4")
                continue
            sets.setdefault(m[1], {})[int(m[2])] = it
        for nn, blanks in sorted(sets.items()):
            e = lambda m: errors.append(f"{f.name} duihua-{nn}: {m}")
            if sorted(blanks) != [1, 2, 3, 4]: e(f"needs blanks 1-4, has {sorted(blanks)}"); continue
            b = list(blanks.values())
            if len({x.get("stem", "").rsplit("\n", 1)[0] for x in b}) != 1: e("dialogue text differs across the set")
            if len({tuple(x.get("options", [])) for x in b}) != 1: e("options differ across the set")
            if len({x.get("level") for x in b}) != 1: e("level differs across the set")
            if len({x.get("answer") for x in b}) != 4: e("each answer must be used once per set (4 different answers)")
            for k, x in blanks.items():
                if not str(x.get("stem", "")).rstrip().endswith(f"第（{k}）空应该填哪一句？"): e(f"blank {k}: stem must end with 第（{k}）空应该填哪一句？")
                for j in range(1, 5):
                    if f"（{j}）＿＿" not in x.get("stem", ""): e(f"blank {k}: stem lacks （{j}）＿＿")

# pinyin.json: every reading is syllables with a tone mark, or neutral tone (no mark)
INIT = "b p m f d t n l g k h j q x zh ch sh r z c s y w".split()
FIN = ("a o e ai ei ao ou an en ang eng ong er i ia ie iao iu ian in iang ing iong u ua uo uai ui uan un uang ueng ue "
       "ü üe üan ün").split()
TONED = {"a": "āáǎà", "e": "ēéěè", "i": "īíǐì", "o": "ōóǒò", "u": "ūúǔù", "ü": "ǖǘǚǜ"}
MARKED = "".join("".join(v) for v in TONED.values())
SYL = re.compile(r"^(?:%s)?(?:%s)$" % ("|".join(sorted(INIT, key=len, reverse=True)), "|".join(sorted(FIN, key=len, reverse=True))))
PLAIN = str.maketrans({c: k for k, v in TONED.items() for c in v})
pyfile = HERE / "chinese" / "pinyin.json"
for word, py in json.loads(pyfile.read_text()).items():
    sy = py.split(" ")
    zh = re.findall(r"[\u4e00-\u9fff]", word.split("|")[0])
    for s in sy:
        if s == "…":
            continue
        base = s.translate(PLAIN)
        ok = bool(SYL.match(base))
        if not ok or sum(c in MARKED for c in s) > 1 or s != s.lower():
            errors.append(f"pinyin.json {word}: bad syllable {s!r} in {py!r}")
    if len(sy) - sy.count("…") != len(zh):
        errors.append(f"pinyin.json {word}: {len(sy)} syllables for {len(zh)} characters")

# compiled banks: unique ids across all Chinese banks
ids = Counter()
for f in sorted((ROOT / "site" / "src" / "data" / "quiz" / "chinese").glob("*.json")):
    for q in json.loads(f.read_text())["questions"]:
        ids[q["id"]] += 1
errors += [f"duplicate question id {i}" for i, n in ids.items() if n > 1]

print(f"checked {sum(1 for _ in (HERE / 'chinese' / 'items').glob('*.json'))} item files, {sum(ids.values())} shipped questions")
for m in errors[:40]:
    print("FAIL", m)
print(f"{len(errors)} failures")
sys.exit(1 if errors else 0)
