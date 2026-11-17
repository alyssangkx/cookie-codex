"""How the shipped Chinese bank lines up with the PSLE syllabus and the top-school papers.

    python3 scripts/quiz/chinese/coverage.py   ->  docs/quiz/chinese-coverage.md

Three views:
  1. syllabus: every outcome in site/src/data/syllabus/chinese.json, with its shipped question count
  2. top-school question types: every pattern in patterns.json (from 171 OCR'd P5/P6 papers), with
     its paper frequency next to the number of shipped questions built on it
  3. tested vocabulary (optional): of the words seen in the papers' MCQ slots (a noisy OCR list kept
     outside the repo), how many appear anywhere in the shipped questions
"""
import json
from collections import Counter
from pathlib import Path

HERE = Path(__file__).parent
ROOT = HERE.parents[2]
SYL = json.loads((ROOT / "site" / "src" / "data" / "syllabus" / "chinese.json").read_text())
PATTERNS = json.loads((HERE / "patterns.json").read_text())
WORDS = Path("/data/alvin/tmp/cookie-codex/chinese/tested_words.json")  # temp: derived from copyrighted papers

qs = [q for f in sorted((ROOT / "site" / "src" / "data" / "quiz" / "chinese").glob("*.json"))
      for q in json.loads(f.read_text())["questions"]]
by_outcome = Counter(o for q in qs for o in q["outcomes"])
by_pattern = Counter(q["template"] for q in qs)
by_level = Counter(q["level"] for q in qs)

lines = ["# Chinese bank: PSLE syllabus and top-school coverage", "",
         f"{len(qs)} shipped questions (basic {by_level['basic']}, intermediate {by_level['intermediate']}, "
         f"competent {by_level['competent']}). Regenerate with `python3 scripts/quiz/chinese/coverage.py`.", "",
         "## 1. PSLE syllabus (SEAB 0005 / 小学华文课程标准)", "",
         "| Sub-topic | Outcome | MCQ-testable | Shipped |", "|---|---|---|---|"]
mcq_total = mcq_done = 0
missing_subs = []


def cell(text, width=None):
    """Markdown-table-safe text, cut with an ellipsis rather than mid-word."""
    t = text.replace("|", "\\|").replace("\n", " ")
    return t if width is None or len(t) <= width else t[:width - 1] + "…"

for st in SYL["strands"]:
    for t in st["topics"]:
        for sb in t["subtopics"]:
            for o in sb["outcomes"]:
                n = by_outcome.get(o["id"], 0)
                if o.get("mcqTestable"):
                    mcq_total += 1
                    mcq_done += n > 0
                flag = "" if n or not o.get("mcqTestable") else " **not yet**"
                if not n and o.get("mcqTestable") and sb["name"] not in missing_subs:
                    missing_subs.append(sb["name"])
                lines.append(f"| {cell(sb['name'])} | {cell(o['text'], 70)} | {'yes' if o.get('mcqTestable') else 'no'} | {n}{flag} |")
lines += ["", f"**{mcq_done} of {mcq_total} MCQ-testable outcomes have questions.** Not yet covered: "
          + ("; ".join(missing_subs) or "none") + ". See `docs/content-schedule.md` for when they are planned.", "",
          "## 2. Top-school question types (171 P5/P6 papers, 21 schools, 2022–2025)", "",
          "| Type | Papers it appears in | Shipped questions |", "|---|---|---|"]
for p in sorted(PATTERNS["patterns"], key=lambda p: -p.get("frequency", 0)):
    n = by_pattern.get(p["id"], 0)
    lines.append(f"| {p.get('name', p['id'])} (`{p['id']}`) | {p.get('frequency', 0)} | {n}{'' if n else ' **not yet**'} |")

if WORDS.exists():
    entries = json.loads(WORDS.read_text())["words"]
    common = [e for e in entries if e.get("count", 0) >= 2 and 2 <= len(e["word"]) <= 4]
    texts = [q["stem"] + " " + " ".join(q["options"]) for q in qs]

    def found(e):
        w = e["word"]
        if "conjunction" in e.get("slots", {}):
            # pairs are stored joined (虽然但是, 只要就, 既又): both halves must occur in the SAME question
            return any(w[:i] in t and w[i:] in t for t in texts for i in range(1, len(w)))
        return any(w in t for t in texts)  # substring match: approximate (can hit inside a longer word)
    hit = [e for e in common if found(e)]
    lines += ["", "## 3. Words tested in the papers", "",
              f"Of {len(common)} two-to-four-character words seen at least twice in the papers' MCQ slots (OCR, noisy), "
              f"**{len(hit)} ({100 * len(hit) // max(1, len(common))}%)** appear somewhere in the shipped questions. "
              "Approximate: a plain substring match can also hit a word inside a longer word. "
              "No paper sentences are copied; only which words get tested."]
else:
    # keep the previous section 3 rather than silently dropping it
    old = (ROOT / "docs" / "quiz" / "chinese-coverage.md")
    prev = old.read_text().split("## 3.", 1) if old.exists() else []
    print("warning: tested-word list not found; keeping the previous section 3 unchanged")
    if len(prev) == 2:
        lines += ["", "## 3." + prev[1].rstrip("\n")]
(ROOT / "docs" / "quiz" / "chinese-coverage.md").write_text("\n".join(lines) + "\n")
print(f"{len(qs)} questions; {mcq_done}/{mcq_total} MCQ-testable outcomes; "
      f"{sum(1 for p in PATTERNS['patterns'] if by_pattern.get(p['id']))}/{len(PATTERNS['patterns'])} paper types covered")
