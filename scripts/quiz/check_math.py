"""Validate every math question bank; exits non-zero on any failure.

    python scripts/quiz/check_math.py
"""
import json
import sys
from collections import Counter
from fractions import Fraction as F
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE / "math"))
import importlib  # noqa: E402
import re  # noqa: E402
import xml.dom.minidom  # noqa: E402
from common import REGISTRY, a_an  # noqa: E402

for mod in sorted((HERE / "math").glob("topic_*.py")):
    importlib.import_module(mod.stem)

# ---- wording check: counts and articles must be right at the source (no after-the-fact rewriting) ----
SING_S = {"glass", "class", "bus", "address", "grass", "dress", "mass", "cross", "across", "less", "miss", "pass", "press",
          "process", "business", "unless", "guess", "boss", "plus", "minus", "thus", "this", "bonus", "status", "focus",
          "axis", "basis", "analysis", "chassis", "pairs of", "success", "princess", "fitness", "darkness", "kindness"}
ONE_PLURAL = re.compile(r"(?<![\d.,/×x*+−-])(?<![\d.,/×x*+−-] )\b1 ([a-z]+s)\b")
ONE_OK = {"more", "less", "times"} | SING_S
ARTICLE = re.compile(r"\b([Aa]n?) ([^\s.,;:?!)]+)")
NOT_NOUN = {"and", "or", "is", "are", "to", "was", "has", "have", "can", "then", "in", "on", "at", "of", "as", "if", "an", "a"}
SLIP_ES = re.compile(r"\b[a-z]*(?:ch|sh|x|z|ss)s\b")
SLIP_SS = re.compile(r"\b[a-z]+ss\b")
SS_OK = {"class", "glass", "mass", "grass", "dress", "cross", "across", "less", "miss", "pass", "press", "process", "business",
         "unless", "guess", "boss", "success", "princess", "fitness", "address", "possess", "assess", "express", "progress",
         "dessert", "kindness", "darkness", "unbiased", "compass", "bypass", "stress", "witness", "illness", "loss", "gross",
         "brass", "bass", "mess", "toss", "moss", "floss", "chess", "stiffness"}


def wording_problems(text):
    """Bare singular-one plurals ('1 units'), wrong a/an, and plural slips ('watchs', 'headphoness')."""
    out = []
    for m in ONE_PLURAL.finditer(text):
        w = m.group(1)
        if w not in ONE_OK and not w.endswith(("ss", "us", "is")):
            out.append(f"'{m.group(0)}' should be singular")
    for m in ARTICLE.finditer(text):
        art, tok = m.group(1), m.group(2).lstrip("$(\"'").rstrip("%")
        if not tok or len(tok) == 1 and tok.isalpha() or tok.lower() in NOT_NOUN or tok.isupper():
            continue
        if art[0] == "A" and (tok[0].isupper() or not (m.start() == 0 or text[:m.start()].rstrip().endswith((".", "?", "!", ":")))):
            continue  # a capital A mid-sentence is a figure label, not an article
        if not (tok[0].isalnum()):
            continue
        want = a_an(tok)
        if art.lower() != want:
            out.append(f"'{m.group(0)}' should be '{want} {tok}'")
    for m in SLIP_ES.finditer(text):
        if m.group(0) not in SS_OK and not m.group(0).endswith(("ss", "ess")):
            out.append(f"plural slip '{m.group(0)}'")
    for m in SLIP_SS.finditer(text):
        if m.group(0) not in SS_OK and not m.group(0).endswith("less"):
            out.append(f"plural slip '{m.group(0)}'")
    return out


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
        if "figure" in q:
            try:
                xml.dom.minidom.parseString(q["figure"])
            except Exception as ex:
                e(f"figure is not valid SVG: {ex}")
            if len(q["figure"]) > 12000:
                e("figure larger than 12 KB")
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
for m in errors[:int(__import__('os').environ.get('SHOW', 40))]:
    print("FAIL", m)
print(f"{len(errors)} failures")
sys.exit(1 if errors else 0)
