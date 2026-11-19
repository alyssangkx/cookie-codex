"""Validate every math question bank; exits non-zero on any failure.

    python scripts/quiz/check_math.py
"""
import json
import os
import sys
from collections import Counter
from fractions import Fraction as F
from pathlib import Path

HERE = Path(__file__).parent
SHOW = int(os.environ.get("SHOW", 40))  # how many failures to print
sys.path.insert(0, str(HERE / "math"))
import importlib  # noqa: E402
import re  # noqa: E402
import xml.dom.minidom  # noqa: E402
from common import REGISTRY, a_an, hand_problems  # noqa: E402

# the "by hand" rule for Paper 1 style (calc=False) questions; its own examples first
assert hand_problems(["6000 ÷ 1200 = 5", "2 × 176.625 = 353.25", "35 ÷ 25 = 1.4", "4523 × 67 = 303041", "84 ÷ 12 = 7"]) == []
assert hand_problems(["299 ÷ 15 = 19.93", "615.44 ÷ 3.14 = 196", "12345 × 678 = 8369910"]) \
    == ["299 ÷ 15", "615.44 ÷ 3.14", "12345 × 678"]

for mod in sorted((HERE / "math").glob("topic_*.py")):
    importlib.import_module(mod.stem)

# ---- wording check: counts and articles must be right at the source (no after-the-fact rewriting) ----
# real words that end in -s / -ss and are fine after '1' or as a plural-looking token
SING_S = {"glass", "class", "bus", "address", "grass", "dress", "mass", "cross", "across", "less", "miss", "pass", "press",
          "process", "business", "unless", "guess", "boss", "plus", "minus", "thus", "this", "bonus", "status", "focus",
          "axis", "basis", "analysis", "chassis", "success", "princess", "fitness", "darkness", "kindness"}
# a 1 directly after a bigger number, a multiplier or a divisor is not a count ('11 units', '2.1 units', '3 x 1 units'... )
ONE_PLURAL = re.compile(r"(?<![\d.,])(?<![×*/] )(?<![×*/])(?<! x )\b1 ([a-z]+s)\b")
ONE_OK = {"more", "less", "times"} | SING_S
ARTICLE = re.compile(r"\b([Aa]n?) ([^\s.,;:?!)]+)")
NOT_NOUN = {"and", "or", "is", "are", "to", "was", "has", "have", "can", "then", "in", "on", "at", "of", "as", "if", "an", "a"}
# real plural slips in this bank: watchs, wishs, headphoness, classs (a singular fed to a plain +s / +es)
SLIP_ES = re.compile(r"\b[a-z]*(?:ch|sh)s\b|\b[a-z]*phoness\b|\bclasss\b")
# a singular subject with 'are' (a sentence about 'the average mass of 4 parcels is' has a singular subject, so it is skipped), or a plural count with 'is' ('1 part are shaded', '3 parts is shaded')
VERB_ONE = re.compile(r"(?<![\d.,/])\b1 [a-z]+ are\b")
VERB_MANY = re.compile(r"(?<![\d.,/])\b(?:[2-9]|\d{2,}) [a-z]+s is\b")


def wording_problems(text):
    """Bare singular-one plurals ('1 units'), wrong a/an, and plural slips ('watchs', 'headphoness')."""
    out = []
    for m in ONE_PLURAL.finditer(text):
        w = m.group(1)
        if w not in ONE_OK and not w.endswith(("ss", "us", "is")):
            out.append(f"'{m.group(0)}' should be singular")
    for m in ARTICLE.finditer(text):
        art, tok = m.group(1), m.group(2)
        bare = tok.lstrip("$£€¥(\"'")
        if not bare or len(bare) == 1 and bare.isalpha() or bare.lower() in NOT_NOUN or bare.isupper() and len(bare) < 2:
            continue
        if art[0] == "A" and (bare[0].isupper() and not bare.isupper() or not (m.start() == 0 or text[:m.start()].rstrip().endswith((".", "?", "!", ":")))):
            continue  # a capital A mid-sentence is a figure label, not an article
        want = a_an(tok)
        if want is None:
            continue  # cannot judge
        if art.lower() != want:
            out.append(f"'{m.group(0)}' should be '{want} {tok}'")
    for m in SLIP_ES.finditer(text):
        out.append(f"plural slip '{m.group(0)}'")
    for rx in (VERB_ONE, VERB_MANY):
        for m in rx.finditer(text):
            if rx is VERB_MANY and re.search(r"\b(average|mean)\b[^.?!]*$", text[:m.start()]):
                continue
            out.append(f"subject-verb disagreement '{m.group(0)}'")
    return out


# 'Multiples of N: a, b, ...' / 'Factors of N: ...' solution lines (bold ** markers allowed)
LISTING = re.compile(r"^(Multiples|Factors) of (\d+): ((?:\*\*)?\d+(?:\*\*)?(?:, (?:\*\*)?\d+(?:\*\*)?)*)$")
BANKS = HERE.parents[1] / "site" / "src" / "data" / "quiz" / "math"
tpl = {(t.topic, t.key): t for ts in REGISTRY.values() for t in ts}  # names may repeat across topics
errors, total = [], 0
seen_ids = {}  # id -> bank file, so an id is unique across all banks (saves are keyed on it)
for path in sorted(BANKS.glob("*.json")):
    qs = json.loads(path.read_text())["questions"]
    ids = Counter(q["id"] for q in qs)
    stems = Counter((q["level"], q["stem"]) for q in qs)
    for q in qs:
        total += 1
        e = lambda m: errors.append(f"{path.name} {q['id']} ({q['template']}): {m}")
        t = tpl.get((q["topic"], q["template"]))
        if t is None:
            e("unknown template"); continue
        if ids[q["id"]] > 1: e("duplicate id")
        elif seen_ids.setdefault(q["id"], path.name) != path.name: e(f"id also used in {seen_ids[q['id']]}")
        if stems[(q["level"], q["stem"])] > 1: e("duplicate stem in level")
        if len(q["options"]) != 4 or len(set(q["options"])) != 4: e(f"options not 4 distinct: {q['options']}")
        vals = [F(v) for v in q["optionValues"]]
        if not t.same_value_ok and len(set(vals)) != 4: e("two options have the same value")
        if not 0 <= q["answer"] < 4 or q["explain"][q["answer"]] is not None: e("answer index / explain mismatch")
        if sum(x is None for x in q["explain"]) != 1: e("every wrong option needs a mistake explanation")
        if any(v <= 0 for v in vals): e("non-positive option")
        texts = [("stem", q["stem"])] + [("option", o) for o in q["options"]] + [("solution", x) for x in q["solution"]] \
            + [("explanation", x["why"]) for x in q["explain"] if x]
        for where, text in texts:
            for prob in wording_problems(text):
                e(f"wording in {where}: {prob}")
        for line in q["solution"]:
            m = LISTING.match(line)
            if not m:
                continue
            kind, n = m.group(1), int(m.group(2))
            nums = [int(x) for x in re.findall(r"\d+", m.group(3).replace("**", ""))]
            ans = vals[q["answer"]]
            if ans.denominator == 1 and ans > 0:
                a = int(ans)
                if kind == "Multiples" and a % n == 0 and a not in nums:
                    e(f"listing '{line[:40]}' stops before the answer {a}")
            if kind == "Factors" and nums != [d for d in range(1, n + 1) if n % d == 0]:
                e(f"factor list of {n} is not complete: {nums}")
            if kind == "Multiples" and nums != [n * i for i in range(1, len(nums) + 1)]:
                e(f"multiples list of {n} is not consecutive from {n}: {nums}")
        if "figure" in q:
            try:
                xml.dom.minidom.parseString(q["figure"])
            except Exception as ex:
                e(f"figure is not valid SVG: {ex}")
            if len(q["figure"]) > 12000:
                e("figure larger than 12 KB")
        if q.get("calc") is not t.calc: e(f"calc is {q.get('calc')!r}, template says {t.calc}")
        if not t.calc:
            for step in hand_problems([q["stem"]] + q["solution"]):
                e(f"no-calculator question has a step that is not workable by hand: {step} (set calc=True or change the numbers)")
        if not hasattr(t, "check"):
            e("template has no independent check"); continue
        expected = t.check(q["params"])
        if expected is None or F(expected) != vals[q["answer"]]:
            e(f"independent check gives {expected}, bank says {vals[q['answer']]}")
            continue
        for i, v in enumerate(vals):
            if i != q["answer"] and v == F(expected) and not t.same_value_ok:
                e("a distractor equals the checked answer")
print(f"checked {total} questions in {len(list(BANKS.glob('*.json')))} banks")
for m in errors[:SHOW]:
    print("FAIL", m)
print(f"{len(errors)} failures")
sys.exit(1 if errors else 0)
