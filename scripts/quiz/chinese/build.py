"""Compile the reviewed Chinese item files into site banks: site/src/data/quiz/chinese/<topic>.json

    python3 scripts/quiz/chinese/build.py

Items live in scripts/quiz/chinese/items/<subtopic>.json (hand-written, curated). An item ships only if
scripts/quiz/chinese/review.json records that the blind reviewer chose the same answer, found no second
defensible option, found the item sound, and found every explanation true. Question ids hash topic | item key, so editing an item's wording keeps its id.
"""
import hashlib
import json
import random
import re
from pathlib import Path

HERE = Path(__file__).parent
ROOT = HERE.parents[2]
SYL = json.loads((ROOT / "site" / "src" / "data" / "syllabus" / "chinese.json").read_text())
OUT = ROOT / "site" / "src" / "data" / "quiz" / "chinese"
REVIEW = HERE / "review.json"

TOPIC_OF = {sb["id"]: t["id"] for st in SYL["strands"] for t in st["topics"] for sb in t["subtopics"]}


def qid(topic, level, key):
    prefix = topic.replace("chi-", "chi")[:8]
    return f"{prefix}-{level[0]}-{hashlib.sha1(f'{topic}|{key}'.encode()).hexdigest()[:10]}"


def main():
    review = json.loads(REVIEW.read_text()) if REVIEW.exists() else {}
    banks, dropped, unreviewed = {}, [], []
    for f in sorted((HERE / "items").glob("*.json")):
        data = json.loads(f.read_text())
        sub = data["subtopic"]
        topic = TOPIC_OF[sub]
        for it in data["items"]:
            rk = f"{sub}|{it['key']}"
            verdict = review.get(rk)
            if verdict is None:
                unreviewed.append(rk)
                continue
            if not verdict.get("agree") or verdict.get("ambiguous") or verdict.get("bad") or verdict.get("explain_ok") is False:
                dropped.append(rk)
                continue
            # writers cycle the answer A-D in item order; shuffle each item's options with a seed from its key,
            # so the order is random to a child but identical on every rebuild
            order = list(range(4))
            random.Random(f"{sub}|{it['key']}").shuffle(order)
            options = [it["options"][i] for i in order]
            explain = [it["explain"][i] for i in order]
            answer = order.index(it["answer"])
            banks.setdefault(topic, []).append({
                "id": qid(topic, it["level"], it["key"]),
                "topic": topic,
                "level": it["level"],
                "template": it["pattern"],
                "outcomes": [it["outcome"]],
                "stem": it["stem"],
                "options": options,
                "answer": answer,
                "explain": explain,
                "solution": it["solution"] + ([it["gloss"]] if it.get("gloss") else []),
                "params": {"key": it["key"], "subtopic": sub},
            })
    OUT.mkdir(parents=True, exist_ok=True)
    for topic, qs in banks.items():
        (OUT / f"{topic}.json").write_text(json.dumps({"topic": topic, "questions": qs}, ensure_ascii=False, indent=1))
        print(f"{topic}: {len(qs)} questions")
    print(f"dropped by review: {len(dropped)}, not yet reviewed (not shipped): {len(unreviewed)}")


if __name__ == "__main__":
    main()
