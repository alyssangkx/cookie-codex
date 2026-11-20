"""Build the math question banks: site/src/data/quiz/math/<topic_id>.json

Every topic_*.py module in this folder registers templates with @template. For each level, each
sub-topic (taken from a template's first outcome) gets quota(sub, level) unique questions, shared
among that sub-topic's templates by their weight.

Isolation: every template draws from its own random stream, seeded by (topic, level, template key, seed).
Changing a template never changes another sub-topic's questions. Inside its own sub-topic, removing a template never
changes a sibling's questions as long as the level's quota stays the same (siblings only gain questions to refill the
tier); see sub_bank, and test_isolation.py checks it. The quota can shrink when a template goes, because the variety
cap (PER_WEIGHT x total weight) binds in some sub-topics: then the merged list is cut shorter and siblings' last
questions drop. Adding a template or raising a weight can also push siblings' last questions out of the tier.
Stems are not compared across sub-topics (that would couple them): check_dupes.py fails any stem filed under two.

    python scripts/quiz/math/build.py                       # all topics
    python scripts/quiz/math/build.py --topic math-ratio --seed 2027
"""
import argparse
import hashlib
import heapq
import importlib
import json
import random
import re
import sys
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
from common import REGISTRY, finalize  # noqa: E402

for mod in sorted(HERE.glob("topic_*.py")):  # importing registers the templates
    importlib.import_module(mod.stem)

OUT = HERE.parents[2] / "site" / "src" / "data" / "quiz" / "math"
LEVELS = ["basic", "intermediate", "competent"]
QUOTA = 25  # floor per sub-topic per level; the site needs 20 to open a tier
QUOTA_MAX = 100  # ceiling per sub-topic per level (a tier clears only when all its questions are mastered)
PER_WEIGHT = 10  #at most this many questions per unit of template weight, so a tier is not one template repeated
MARKS_SCALE = 14  # questions per level for each 1% of past-paper marks

# Share of Math marks per sub-topic in the 2018-2026 top-school prelim papers (13,986 tagged items, marks-weighted;
# aggregate counts only; recomputed 20 Nov 2026 from all nine years). Sub-topics under 1.8% get the floor. Speed has no
# entry of its own: its questions are part of Rate (topic_rate.py), as school papers file them.
PAPER_MARKS_PCT = {
    "math-whole-numbers-addition-subtraction-multiplication-and-division": 17.6,
    "math-geometry-angles": 11.2,
    "math-ratio-ratio": 6.2,
    "math-fractions-fraction-of-a-whole-and-of-a-set": 5.8,
    "math-whole-numbers-numbers-up-to-100-1000-10-000-100-000-and-10-million": 5.6,
    "math-data-representation-and-interpretation-picture-graphs-bar-graphs-tables-line-graphs-and-pie-charts": 5.2,
    "math-area-and-volume-area-and-circumference-of-circle": 5.1,
    "math-area-and-volume-volume-of-cube-and-cuboid": 4.5,
    "math-percentage-percentage": 4.3,
    "math-money-money": 4.1,
    "math-area-and-volume-area-and-perimeter": 4.0,
    "math-rate-rate": 2.9,
    "math-algebra-algebra": 2.3,
    "math-area-and-volume-area-of-triangle": 2.3,
    "math-measurement-length-mass-and-volume": 2.3,
    "math-data-analysis-average-of-a-set-of-data": 2.2,
    "math-decimals-decimal-notation-and-comparison": 1.9,
}


def sub_of(t):
    return re.sub(r"-\d+$", "", t.outcomes[0])


def prefix(topic):
    return topic.replace("math-", "")[:6].rstrip("-")


def canonical(params):
    """Sorted keys, no spaces; Fractions and other odd values fall back to str()."""
    return json.dumps(params, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str)


def stable_id(topic, level, key, params):
    """Id from topic | template key | params, so rewording a stem, explanation or figure keeps it."""
    h = hashlib.sha1(f"{topic}|{key}|{canonical(params)}".encode()).hexdigest()[:10]
    return f"{prefix(topic)}-{level[0]}-{h}"


def quota(sub, group):
    """Questions for one sub-topic at one level: follows paper marks, between the floor and the ceiling, and at most
    PER_WEIGHT per unit of template weight."""
    want = round(PAPER_MARKS_PCT.get(sub, 0) * MARKS_SCALE)
    variety = PER_WEIGHT * sum(t.weight for t in group)
    return max(QUOTA, min(QUOTA_MAX, want, variety))


def sub_bank(topic, level, group, n, seed):
    """n unique questions for one sub-topic at one level.

    Each template yields its own candidates: its random stream, minus its own repeats (stem or id). The stream advances
    the same way for every candidate (one generation, then one 4-option shuffle whose state also orders that
    candidate's options), so a template's candidates never depend on its siblings.
    The candidates of all templates are merged by "virtual time" (the k-th candidate of a template with weight w comes
    at (2k + 1) / 2w; ties go to the earlier template) and the first n with a stem not already kept are taken.
    So removing a template only deletes its entries from that merged list: every question a sibling had is still
    first with its stem and still inside the first n. A template that fails 3000 draws in a row (None or its own
    repeats) has run dry; stems its siblings already hold never count against it."""
    streams = [random.Random(f"{topic}|{level}|{t.key}|{seed}") for t in group]
    seen = [(set(), set()) for _ in group]  # stems and ids this template has already yielded

    def candidate(i):
        t, rng = group[i], streams[i]
        stems, ids = seen[i]
        for _ in range(3000):
            q = t(rng)
            if not q:
                continue
            shuffler = random.Random()
            shuffler.setstate(rng.getstate())
            rng.shuffle([0, 1, 2, 3])  # the stream moves past the option shuffle, kept or not
            qid = stable_id(topic, level, t.key, q["params"])
            if q["stem"] in stems or qid in ids:
                continue
            stems.add(q["stem"])
            ids.add(qid)
            return q, qid, shuffler
        return None  # this template has run out of new questions

    heap = [(Fraction(1, 2 * t.weight), i) for i, t in enumerate(group)]
    heapq.heapify(heap)
    drawn = [0] * len(group)
    made = [[] for _ in group]
    taken = set()
    while heap and len(taken) < n:
        _, i = heapq.heappop(heap)
        c = candidate(i)
        if c is None:
            continue
        drawn[i] += 1
        heapq.heappush(heap, (Fraction(2 * drawn[i] + 1, 2 * group[i].weight), i))
        q, qid, shuffler = c
        if q["stem"] in taken:
            continue  # a sibling came first with this stem
        taken.add(q["stem"])
        made[i].append(finalize(q, group[i], shuffler, qid))
    # interleave the templates' questions (the order is cosmetic: the site shuffles new questions)
    out = []
    for r in range(max((len(m) for m in made), default=0)):
        out += [m[r] for m in made if r < len(m)]
    return out


_SUBS = {sub_of(t) for ts in REGISTRY.values() for t in ts}
_unknown = sorted(set(PAPER_MARKS_PCT) - _SUBS)
assert not _unknown, f"PAPER_MARKS_PCT names sub-topics no template files under (renamed?): {_unknown}"


def bank(topic, seed="2027"):
    out = []
    for level in LEVELS:
        by_sub = {}
        for t in REGISTRY[topic]:
            if t.level == level:
                by_sub.setdefault(sub_of(t), []).append(t)
        for sub, group in by_sub.items():
            n = quota(sub, group)
            qs = sub_bank(topic, level, group, n, seed)
            if len(qs) < n:
                print(f"  warning: {topic}/{level}/{sub}: only {len(qs)} unique questions (wanted {n})")
            out += qs
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--topic", choices=sorted(REGISTRY), action="append")
    ap.add_argument("--seed", default="2027")
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    for topic in a.topic or sorted(REGISTRY):
        qs = bank(topic, a.seed)
        (OUT / f"{topic}.json").write_text(json.dumps({"topic": topic, "seed": a.seed, "questions": qs},
                                                      ensure_ascii=False, indent=1))
        print(f"{topic}: {len(qs)} questions")


if __name__ == "__main__":
    main()
