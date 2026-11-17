"""Build site/src/data/progression.json: the P1-P5 sub-topics, for store.ts (tries per day: 5 vs 3).

A sub-topic's P-level is the highest `level` among its outcomes in the syllabus JSON. Only P1-P5
sub-topics are listed; any sub-topic not listed (every P6 and Chinese one) counts as P6.
Run after build_rewards.py:

    python3 scripts/quiz/build_progression.py
"""
import json
from pathlib import Path

DATA = Path(__file__).resolve().parents[2] / "site" / "src" / "data"


def main():
    levels = {}
    for f in ("math", "chinese"):
        for strand in json.loads((DATA / "syllabus" / f"{f}.json").read_text())["strands"]:
            for topic in strand["topics"]:
                for sub in topic["subtopics"]:
                    levels[sub["id"]] = max(int(o["level"].lstrip("P")) for o in sub["outcomes"])
    rewards = json.loads((DATA / "rewards.json").read_text())
    ids = {s["id"] for lst in rewards["order"].values() for s in lst}
    low = {k: v for k, v in sorted(levels.items()) if v <= 5 and k in ids}
    (DATA / "progression.json").write_text(json.dumps({"levels": low}, indent=1) + "\n")
    p6 = sum(1 for k in ids if k in levels and levels[k] >= 6)
    print(f"P1-P5 sub-topics: {len(low)}; P6 sub-topics: {p6}; other (no syllabus entry): {len(ids) - len(low) - p6}")


main()
