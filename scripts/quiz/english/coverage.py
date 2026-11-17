"""How the shipped English bank lines up with the PSLE syllabus and the top-school papers.

    python3 scripts/quiz/english/coverage.py   ->  docs/quiz/english-coverage.md

Two views: every outcome in site/src/data/syllabus/english.json with its shipped question count, and every
question type in patterns.json (from the OCR'd P5/P6 papers) with its paper frequency next to shipped counts.
"""
import json
from collections import Counter
from pathlib import Path

HERE = Path(__file__).parent
ROOT = HERE.parents[2]
SYL = json.loads((ROOT / "site" / "src" / "data" / "syllabus" / "english.json").read_text())
PATTERNS = json.loads((HERE / "patterns.json").read_text())

qs = [q for f in sorted((ROOT / "site" / "src" / "data" / "quiz" / "english").glob("*.json"))
      for q in json.loads(f.read_text())["questions"]]
by_outcome = Counter(o for q in qs for o in q["outcomes"])
by_pattern = Counter(q["template"] for q in qs)
by_level = Counter(q["level"] for q in qs)


def cell(text, width=None):
    t = text.replace("|", "\\|").replace("\n", " ")
    return t if width is None or len(t) <= width else t[:width - 1] + "…"


lines = ["# English bank: PSLE syllabus and top-school coverage", "",
         f"{len(qs)} shipped questions (basic {by_level['basic']}, intermediate {by_level['intermediate']}, "
         f"competent {by_level['competent']}). Regenerate with `python3 scripts/quiz/english/coverage.py`.", "",
         "## 1. PSLE syllabus (English Language Syllabus 2020)", "",
         "| Sub-topic | Outcome | MCQ-testable | Shipped |", "|---|---|---|---|"]
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
                lines.append(f"| {cell(sb['name'])} | {cell(o['text'], 70)} | {'yes' if o.get('mcqTestable') else 'no'} | {n}{flag} |")
lines += ["", f"**{mcq_done} of {mcq_total} MCQ-testable outcomes have questions.** Not yet covered: "
          + ("; ".join(missing_subs) or "none") + ".", "",
          f"## 2. Top-school question types ({PATTERNS.get('papersAnalysedCount', '?')} P5/P6 papers)", "",
          "| Type | Papers it appears in | Shipped questions |", "|---|---|---|"]
for p in sorted(PATTERNS["patterns"], key=lambda p: -p.get("frequency", 0)):
    n = by_pattern.get(p["id"], 0)
    lines.append(f"| {cell(p.get('name', p['id']))} (`{p['id']}`) | {p.get('frequency', 0)} | {n}{'' if n else ' **not yet**'} |")
(ROOT / "docs" / "quiz" / "english-coverage.md").write_text("\n".join(lines) + "\n")
print(f"{len(qs)} questions; {mcq_done}/{mcq_total} MCQ-testable outcomes; "
      f"{sum(1 for p in PATTERNS['patterns'] if by_pattern.get(p['id']))}/{len(PATTERNS['patterns'])} paper types covered")
