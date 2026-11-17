"""Build the math question banks: site/src/data/quiz/math/<topic_id>.json

Every topic_*.py module in this folder registers templates with @template. For each level, each
sub-topic (taken from a template's first outcome) gets at least QUOTA unique questions, spread
round-robin over that sub-topic's templates, and each level has at least --n questions in total.

    python scripts/quiz/math/build.py                       # all topics
    python scripts/quiz/math/build.py --topic math-ratio --seed 2027
"""
import argparse
import hashlib
import importlib
import json
import math
import random
import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
from common import REGISTRY, finalize  # noqa: E402

for mod in sorted(HERE.glob("topic_*.py")):  # importing registers the templates
    importlib.import_module(mod.stem)

OUT = HERE.parents[2] / "site" / "src" / "data" / "quiz" / "math"
LEVELS = ["basic", "intermediate", "competent"]
QUOTA = 25  # per sub-topic per level; the site needs 20 to open a tier


def sub_of(t):
    return re.sub(r"-\d+$", "", t.outcomes[0])


def prefix(topic):
    return topic.replace("math-", "")[:6].rstrip("-")


def bank(topic, n, seed):
    out = []
    for level in LEVELS:
        tpls = [t for t in REGISTRY[topic] if t.level == level]
        if not tpls:
            continue
        by_sub = {}
        for t in tpls:
            by_sub.setdefault(sub_of(t), []).append(t)
        quota = max(QUOTA, math.ceil(n / len(by_sub)))
        rng = random.Random(f"{topic}|{level}|{seed}")
        stems, made = set(), []
        for sub, group in by_sub.items():
            got, tries = 0, 0
            while got < quota and tries < quota * 3000:
                tries += 1
                t = group[got % len(group)] if tries < quota * 1500 else rng.choice(group)
                q = t(rng)
                if not q or q["stem"] in stems:
                    continue
                stems.add(q["stem"])
                got += 1
                # id from the stem, so adding templates later never re-points saved progress
                qid = f"{prefix(topic)}-{level[0]}-{hashlib.sha1(q['stem'].encode()).hexdigest()[:10]}"
                made.append(finalize(q, t, rng, qid))
            if got < quota:
                print(f"  warning: {topic}/{level}/{sub}: only {got} unique questions (wanted {quota})")
        out += made
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--topic", choices=sorted(REGISTRY), action="append")
    ap.add_argument("--n", type=int, default=100, help="minimum questions per level")
    ap.add_argument("--seed", default="2027")
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    for topic in a.topic or sorted(REGISTRY):
        qs = bank(topic, a.n, a.seed)
        (OUT / f"{topic}.json").write_text(json.dumps({"topic": topic, "seed": a.seed, "questions": qs},
                                                      ensure_ascii=False, indent=1))
        print(f"{topic}: {len(qs)} questions")


if __name__ == "__main__":
    main()
