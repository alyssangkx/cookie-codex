"""Coverage of the top-school question types by our generators: docs/quiz/coverage.md

A template covers a pattern when its docstring names the pattern id (math-pat-...).
Goal: clearing every tier of a topic means the student has practised every question type
seen in the top-school papers for that topic.

    python scripts/quiz/coverage.py           # writes the report, prints a summary
    python scripts/quiz/coverage.py --strict  # also exits 1 if any pattern is uncovered
"""
import importlib
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE / "math"))
from common import REGISTRY  # noqa: E402

for mod in sorted((HERE / "math").glob("topic_*.py")):
    importlib.import_module(mod.stem)

patterns = json.loads((HERE / "math" / "patterns.json").read_text())["patterns"]
covers = defaultdict(list)  # pattern id -> template keys
for ts in REGISTRY.values():
    for t in ts:
        for pid in re.findall(r"math-pat-[a-z0-9-]+", t.__doc__ or ""):
            covers[pid].append(f"{t.key} ({t.level})")

# Speed was dropped from the 2021 primary syllabus (examined at PSLE from 2026); older papers still have it.
OUT = [p for p in patterns if "speed" in p["id"]]
patterns = [p for p in patterns if "speed" not in p["id"]]

rows = defaultdict(list)
for p in patterns:
    topic = (p.get("syllabusTopicId") or "unknown").split("-")[1] if p.get("syllabusTopicId") else "unknown"
    rows[topic].append(p)

lines = ["# Coverage of top-school question types", "",
         "Each row is a question type found in the top-school P5/P6 papers "
         "(`scripts/quiz/math/patterns.json`). A type is covered when a generator names its id.", "",
         "| Topic | Types | Covered | Missing |", "|---|---|---|---|"]
detail, total, done = [], 0, 0
for topic in sorted(rows):
    ps = sorted(rows[topic], key=lambda p: -p.get("frequency", 0))
    c = [p for p in ps if covers.get(p["id"])]
    total += len(ps)
    done += len(c)
    lines.append(f"| {topic} | {len(ps)} | {len(c)} | {', '.join(p['id'] for p in ps if not covers.get(p['id'])) or '—'} |")
    detail += [f"## {topic}", "", "| Type | Level | Papers | Diagram | Generators |", "|---|---|---|---|---|"]
    for p in ps:
        detail.append(f"| {p['id']} | {p['level']} | {p.get('frequency', 0)} | {'yes' if p.get('needsDiagram') else ''} | "
                      f"{', '.join(covers.get(p['id'], [])) or '**missing**'} |")
    detail.append("")
lines += ["", f"**{done} of {total} question types covered.**", "",
          "Not counted (outside the 2021 syllabus, which has no Speed): " + (", ".join(p["id"] for p in OUT) or "none"), ""] + detail
# ---- outcome coverage: every syllabus outcome should be practised by some template, as its first or a secondary outcome (or be in SKIP)
SKIP = {  # outcome id -> why it has no generator
    "math-area-and-volume-volume-of-cube-and-cuboid-11":
        "Placeholder: the syllabus line lost its symbols in PDF extraction (marked unverified).",
}
first, anywhere = defaultdict(list), defaultdict(list)
for ts in REGISTRY.values():
    for t in ts:
        first[t.outcomes[0]].append(f"{t.key} ({t.level})")
        for o in t.outcomes[1:]:
            anywhere[o].append(t.key)
syl = json.loads((ROOT / "site" / "src" / "data" / "syllabus" / "math.json").read_text())
orows, o_done, o_total = [], 0, 0
for st in syl["strands"]:
    for tp in st["topics"]:
        for sb in tp["subtopics"]:
            for o in sb["outcomes"]:
                o_total += 1
                g = first.get(o["id"], [])
                o_done += bool(g) or bool(anywhere.get(o["id"])) or o["id"] in SKIP
                status = (f"{len(g)} templates" if g else f"skipped: {SKIP[o['id']]}" if o["id"] in SKIP
                          else f"secondary only ({len(anywhere[o['id']])} templates)" if anywhere.get(o["id"]) else "**missing**")
                orows.append(f"| {o['id'].replace('math-', '')} | {o['level']} | {status} |")
lines += ["## Syllabus outcomes", "",
           f"**{o_done} of {o_total} outcomes** are practised by at least one generator (or documented as skipped).", "",
           "'secondary only' means the outcome is practised inside templates filed under another outcome of the same or a related sub-topic.", "",
           "| Outcome | Level | Generators |", "|---|---|---|"] + orows + [""]
(ROOT / "docs" / "quiz").mkdir(parents=True, exist_ok=True)
(ROOT / "docs" / "quiz" / "coverage.md").write_text("\n".join(lines))
print(f"coverage: {done}/{total} question types, {o_done}/{o_total} syllabus outcomes -> docs/quiz/coverage.md")
if "--strict" in sys.argv and (done < total or o_done < o_total):
    sys.exit(1)
