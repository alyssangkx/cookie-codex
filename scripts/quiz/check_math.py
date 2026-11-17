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
import xml.dom.minidom  # noqa: E402
from common import REGISTRY  # noqa: E402

for mod in sorted((HERE / "math").glob("topic_*.py")):
    importlib.import_module(mod.stem)

BANKS = HERE.parents[1] / "site" / "src" / "data" / "quiz" / "math"
tpl = {(t.topic, t.key): t for ts in REGISTRY.values() for t in ts}  # names may repeat across topics
errors, total = [], 0
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
        if stems[(q["level"], q["stem"])] > 1: e("duplicate stem in level")
        if len(q["options"]) != 4 or len(set(q["options"])) != 4: e(f"options not 4 distinct: {q['options']}")
        vals = [F(v) for v in q["optionValues"]]
        if not t.same_value_ok and len(set(vals)) != 4: e("two options have the same value")
        if not 0 <= q["answer"] < 4 or q["explain"][q["answer"]] is not None: e("answer index / explain mismatch")
        if sum(x is None for x in q["explain"]) != 1: e("every wrong option needs a mistake explanation")
        if any(v <= 0 for v in vals): e("non-positive option")
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
for m in errors[:40]:
    print("FAIL", m)
print(f"{len(errors)} failures")
sys.exit(1 if errors else 0)
