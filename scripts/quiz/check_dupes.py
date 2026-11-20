"""Every question belongs to exactly one sub-topic (owner, 20 Nov 2026: perfect classification is not required, but no
question may appear in two). Fails if, within one subject, the same stem appears under two sub-topics.
The sub-topic is the question's first outcome id without its trailing -NN (the rule the banks are built on).

    python3 scripts/quiz/check_dupes.py      # prints "0 failures" or the clashes, exit 1 on any
"""
import json, re, sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "site/src/data/quiz"


def sub_of(q):
    o = (q.get("outcomes") or [q.get("outcome", "")])[0]
    return re.sub(r"-\d+$", "", o)


def clashes(questions):
    """-> [(stem, sorted sub-topics)] for stems filed under more than one sub-topic."""
    seen = defaultdict(set)
    for q in questions:
        seen[q["stem"].strip()].add(sub_of(q))
    return [(s, sorted(v)) for s, v in seen.items() if len(v) > 1]


def main():
    bad = 0
    for subject in sorted(p for p in ROOT.iterdir() if p.is_dir()):
        qs = [q for f in sorted(subject.glob("*.json")) for q in json.loads(f.read_text())["questions"]]
        for stem, subs in clashes(qs):
            bad += 1
            if bad <= 20: print(f"{subject.name}: {stem[:80]!r} in {', '.join(subs)}")
    print(f"{bad} failures")
    return 1 if bad else 0


if __name__ == "__main__":
    assert clashes([{"stem": "a", "outcomes": ["x-1"]}, {"stem": "a", "outcomes": ["y-2"]}]) == [("a", ["x", "y"])]
    assert clashes([{"stem": "a", "outcomes": ["x-1"]}, {"stem": "a", "outcomes": ["x-2"]}]) == []
    sys.exit(main())
