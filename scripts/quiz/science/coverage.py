"""How the shipped Science bank lines up with the PSLE syllabus (and the top-school papers, once patterns.json exists).

    python3 scripts/quiz/science/coverage.py   ->  docs/quiz/science-coverage.md

Two views: every outcome in site/src/data/syllabus/science.json with its shipped question count, and every
question type in patterns.json (when present) with its paper frequency next to shipped counts.
"""
import json
from collections import Counter
from pathlib import Path

HERE = Path(__file__).parent
ROOT = HERE.parents[2]
SYL = json.loads((ROOT / "site" / "src" / "data" / "syllabus" / "science.json").read_text())
PAT_FILE = HERE / "patterns.json"
PATTERNS = json.loads(PAT_FILE.read_text()) if PAT_FILE.exists() else None

qs = [q for f in sorted((ROOT / "site" / "src" / "data" / "quiz" / "science").glob("*.json"))
      for q in json.loads(f.read_text())["questions"]]
by_outcome = Counter(o for q in qs for o in q["outcomes"])
by_pattern = Counter(q["template"] for q in qs)
by_level = Counter(q["level"] for q in qs)
n_fig = sum(1 for q in qs if q.get("figure"))


def cell(text, width=None):
    t = text.replace("|", "\\|").replace("\n", " ")
    return t if width is None or len(t) <= width else t[:width - 1] + "…"


lines = ["# Science bank: PSLE syllabus and top-school coverage", "",
         f"{len(qs)} shipped questions (basic {by_level['basic']}, intermediate {by_level['intermediate']}, "
         f"competent {by_level['competent']}), {n_fig} with a figure. Regenerate with `python3 scripts/quiz/science/coverage.py`.", "",
         "## 1. PSLE syllabus (Science Syllabus 2023)", "",
         "| Sub-topic | Outcome | MCQ-testable | Needs diagram | Shipped |", "|---|---|---|---|---|"]
mcq_total = mcq_done = 0
missing_subs = []
for st in SYL["strands"]:
    for t in st["topics"]:
        for sb in t["subtopics"]:
            for o in sb["outcomes"]:
                n = by_outcome.get(o["id"], 0)
                if o.get("mcqTestable"):
                    mcq_total += 1
                    mcq_done += n > 0
                    if not n and sb["name"] not in missing_subs:
                        missing_subs.append(sb["name"])
                flag = "" if n or not o.get("mcqTestable") else " **not yet**"
                lines.append(f"| {cell(sb['name'])} | {cell(o['text'], 70)} | {'yes' if o.get('mcqTestable') else 'no'} | "
                             f"{'yes' if o.get('needsDiagram') else 'no'} | {n}{flag} |")
lines += ["", f"**{mcq_done} of {mcq_total} MCQ-testable outcomes have questions.** Not yet covered: "
          + ("; ".join(missing_subs) or "none")]
n_types = n_done = 0
if PATTERNS:
    pats = PATTERNS["patterns"]
    n_types, n_done = len(pats), sum(1 for p in pats if by_pattern.get(p["id"]))
    lines += ["", f"## 2. Top-school question types ({PATTERNS.get('papersAnalysedCount', '?')} P5/P6 papers)", "",
              "| Type | Papers it appears in | Shipped questions |", "|---|---|---|"]
    for p in sorted(pats, key=lambda p: -p.get("frequency", 0)):
        n = by_pattern.get(p["id"], 0)
        lines.append(f"| {cell(p.get('name', p['id']))} (`{p['id']}`) | {p.get('frequency', 0)} | {n}{'' if n else ' **not yet**'} |")
else:
    lines += ["", "## 2. Top-school question types", "", "`scripts/quiz/science/patterns.json` does not exist yet."]
(ROOT / "docs" / "quiz" / "science-coverage.md").write_text("\n".join(lines) + "\n")
print(f"{len(qs)} questions; {mcq_done}/{mcq_total} MCQ-testable outcomes; {n_done}/{n_types} paper types covered")
