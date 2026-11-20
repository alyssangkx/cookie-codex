"""Compile the reviewed English item files into site banks: site/src/data/quiz/english/<topic>.json

    python3 scripts/quiz/english/build.py

Items live in scripts/quiz/english/items/*.json (hand-written, curated), shaped
{"subtopic": ..., "items": [{key, level, outcome, syllabus, pattern, stem, options[4], answer, explain[4], solution[], gloss?, visual?}]}.
The sub-topics are the PSLE Paper 2 sections (`strands` of the syllabus JSON, owner decision 20 Nov 2026); `outcome` is the
section's outcome and `syllabus` the MOE syllabus outcome (`syllabusStrands`), kept as the bank question's second outcome.
Keys vis-NN-K, read-NN-K and ecloze-NN-K form passage sets (group/seq in the bank); a set ships whole or not at all.
An optional "visual" (poster/notice/brochure/timetable/email card) is copied into the bank question.
An item ships only if scripts/quiz/english/review.json records, under "<subtopic>|<key>", ship: true for exactly the
current content (fingerprint). Fail closed: no verdict, ship not true, or an edited item means it does not ship.
Question ids hash topic | item key, so editing an item's wording keeps its id.
"""
import hashlib
import json
import re
from collections import Counter
import random
import sys
from pathlib import Path

HERE = Path(__file__).parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE.parent))
from bankcommon import PASSAGE, fingerprint  # noqa: E402

SYL = json.loads((ROOT / "site" / "src" / "data" / "syllabus" / "english.json").read_text())
OUT = ROOT / "site" / "src" / "data" / "quiz" / "english"
REVIEW = HERE / "review.json"

TOPIC_OF = {sb["id"]: t["id"] for st in SYL["strands"] for t in st["topics"] for sb in t["subtopics"]}


def qid(topic, key):
    # no level in the id: moving an item between levels must not orphan a child's retest history
    prefix = "eng" + topic.split("-")[1][:4]  # eng-sec-grammar-mcq -> engsec
    return f"{prefix}-{hashlib.sha1(f'{topic}|{key}'.encode()).hexdigest()[:10]}"


def gloss_line(it):
    """The gloss as an extra solution line, only when it says something the solution does not."""
    g = (it.get("gloss") or "").strip()
    return [g] if g and g not in " ".join(it["solution"]) else []


def hold_sets(banks, all_keys, dropped):
    """A passage set ships only when every item of it shipped: a missing blank or question would leave the
    passage unanswerable or a blank unexplained. Held sets go to `dropped`."""
    for topic, qs in banks.items():
        total, shipped = {}, {}
        for sub, key in all_keys:
            if TOPIC_OF[sub] == topic and (m := PASSAGE.match(key)):
                total.setdefault((sub, m[1], m[2]), set()).add(key)
        for q in qs:
            if (m := PASSAGE.match(q["params"]["key"])):
                shipped.setdefault((q["params"]["subtopic"], m[1], m[2]), set()).add(q["params"]["key"])
        held = {g for g, ks in shipped.items() if ks != total.get(g)}
        keep = []
        for q in qs:
            m = PASSAGE.match(q["params"]["key"])
            if m and (q["params"]["subtopic"], m[1], m[2]) in held:
                dropped.append(f"{q['params']['subtopic']}|{q['params']['key']} (passage set held: not every item shipped)")
            else:
                keep.append(q)
        qs[:] = keep


def main():
    review = json.loads(REVIEW.read_text()) if REVIEW.exists() else {}
    banks, dropped, unreviewed, stale, all_keys = {}, [], [], [], []
    for f in sorted((HERE / "items").glob("*.json")):
        data = json.loads(f.read_text())
        sub = data["subtopic"]
        topic = TOPIC_OF[sub]
        for it in data["items"]:
            rk = f"{sub}|{it['key']}"
            all_keys.append((sub, it["key"]))
            verdict = review.get(rk)
            if verdict is None:
                unreviewed.append(rk)
                continue
            if verdict.get("ship") is not True:
                dropped.append(rk)
                continue
            if verdict.get("fingerprint") != fingerprint(it):
                stale.append(rk)
                continue
            # writers cycle the answer A-D in item order; shuffle with a seed from the key so the order is
            # random to a child but identical on every rebuild
            order = list(range(len(it["options"])))
            random.Random(f"{sub}|{it['key']}").shuffle(order)
            banks.setdefault(topic, []).append({
                "id": qid(topic, it["key"]),
                "topic": topic,
                "level": it["level"],
                "template": it["pattern"],
                "outcomes": [it["outcome"], it["syllabus"]],  # the section files it; the syllabus outcome is metadata
                "stem": re.sub(r"\s+(Which option is closest in meaning)", r"\n\1", it["stem"]),  # the question on its own line
                "options": [it["options"][i] for i in order],
                "answer": order.index(it["answer"]),
                "explain": [it["explain"][i] for i in order],
                "solution": list(it["solution"]) + gloss_line(it),
                "params": {"key": it["key"], "subtopic": sub},
                **({"visual": it["visual"]} if it.get("visual") else {}),
                **({"group": f"{sub}:{m[1]}-{m[2]}", "seq": int(m[3])} if (m := PASSAGE.match(it["key"])) else {}),
            })
    hold_sets(banks, all_keys, dropped)
    OUT.mkdir(parents=True, exist_ok=True)
    for old in OUT.glob("*.json"):  # never leave a bank behind that the current items no longer produce
        old.unlink()
    for topic, qs in banks.items():
        if not qs:
            continue  # an empty bank is not written
        (OUT / f"{topic}.json").write_text(json.dumps({"topic": topic, "questions": qs}, ensure_ascii=False, indent=1))
        print(f"{topic}: {len(qs)} questions")
    per_tier = Counter((re.sub(r"-\d+$", "", q["outcomes"][0]), q["level"]) for qs in banks.values() for q in qs)
    for (sb, lv), n in sorted(per_tier.items()):
        if n < 25:
            print(f"  warning: {sb} {lv} has {n} questions (aim for 25+; 20 is the playable minimum)")
    print(f"dropped by review: {len(dropped)}, not yet reviewed: {len(unreviewed)}, "
          f"edited since review (not shipped until re-reviewed): {len(stale)}")
    if stale:
        print("  stale:", ", ".join(stale[:10]))


if __name__ == "__main__":
    main()
