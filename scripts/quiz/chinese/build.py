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


def qid(topic, key):
    # no level in the id: moving an item between levels must not orphan a child's retest history
    prefix = topic.replace("chi-", "chi")[:8]
    return f"{prefix}-{hashlib.sha1(f'{topic}|{key}'.encode()).hexdigest()[:10]}"


def fingerprint(it):
    """Hash of everything a reviewer judged; an item edited after review no longer matches its verdict."""
    body = json.dumps([it["stem"], it["options"], it["answer"], it["explain"], it["solution"]], ensure_ascii=False)
    return hashlib.sha1(body.encode()).hexdigest()[:16]


PASSAGE = re.compile(r"^(cloze|yuedu)-(\d+)-(\d+)$")  # passage sets: 5 questions on one passage


def gloss_line(it):
    """The gloss as an extra solution line, only when it carries a meaning ("词 = meaning") not already said."""
    g = it.get("gloss") or ""
    if "=" not in g:
        return []  # e.g. a bare list of the options: says nothing
    meaning = g.split("=", 1)[1].strip()
    if not meaning:
        print(f"  warning: empty gloss meaning in {it['key']}")
        return []
    return [] if meaning in " ".join(it["solution"]) else [g]


def fill_cloze(bank, items, review, dropped):
    """A cloze passage shows every blank. A sibling blank that is not asked is shown filled with its answer,
    but only when review.json records "fill_ok": true for it (an explicit decision that its answer is sound;
    it was held for its explanation only). Any other unasked sibling (doubted answer,
    unreviewed, or edited since review) holds the whole passage set, so a child never sees a blank that is
    never asked, or a doubted word written into the passage."""
    by_key = {it["key"]: it for it in items}

    def state(it):
        v = review.get(f"chi-cloze-mcq|{it['key']}")
        if v is None or v.get("fingerprint") != fingerprint(it):
            return "unknown"
        if v.get("ship") is True:
            return "asked"
        # filled only on an explicit, recorded decision that the answer itself is sound (review.json
        # "fill_ok": true, set by hand after reading the notes); anything else holds the passage set
        return "fill" if v.get("fill_ok") is True else "unknown"

    sets = {}
    for k, it in by_key.items():
        if (m := PASSAGE.match(k)):
            sets.setdefault(m[2], {})[int(m[3])] = it
    states = {k: state(it) for k, it in by_key.items()}
    keep = []
    for q in bank:
        m = PASSAGE.match(q["params"]["key"]) if q["params"]["subtopic"] == "chi-cloze-mcq" else None
        if not m:
            keep.append(q)
            continue
        sibs = {n: (it, states[it["key"]]) for n, it in sets[m[2]].items() if n != int(m[3])}
        if any(st == "unknown" for _, st in sibs.values()):
            dropped.append(f"chi-cloze-mcq|{q['params']['key']} (passage set held: a sibling blank cannot be shown)")
            continue
        for n, (it, st) in sibs.items():
            if st == "fill":
                q["stem"] = q["stem"].replace(f"（{n}）＿＿", f"（{n}）{it['options'][it['answer']]}")
        keep.append(q)
    bank[:] = keep


def main():
    review = json.loads(REVIEW.read_text()) if REVIEW.exists() else {}
    banks, dropped, unreviewed, stale = {}, [], [], []
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
            # fail closed: ship only an explicit yes for exactly the content that was reviewed
            if verdict.get("ship") is not True:
                dropped.append(rk)
                continue
            if verdict.get("fingerprint") != fingerprint(it):
                stale.append(rk)
                continue
            # writers cycle the answer A-D in item order; shuffle each item's options with a seed from its key,
            # so the order is random to a child but identical on every rebuild
            order = list(range(4))
            random.Random(f"{sub}|{it['key']}").shuffle(order)
            options = [it["options"][i] for i in order]
            explain = [it["explain"][i] for i in order]
            answer = order.index(it["answer"])
            banks.setdefault(topic, []).append({
                "id": qid(topic, it["key"]),
                "topic": topic,
                "level": it["level"],
                "template": it["pattern"],
                "outcomes": [it["outcome"]],
                "stem": it["stem"],
                "options": options,
                "answer": answer,
                "explain": explain,
                # add the gloss line only when the solution does not already say the same thing
                "solution": it["solution"] + gloss_line(it),
                "params": {"key": it["key"], "subtopic": sub},
                **({"group": f"{sub}:{m[2]}", "seq": int(m[3])} if (m := PASSAGE.match(it["key"])) else {}),
            })
        if sub == "chi-cloze-mcq":
            fill_cloze(banks.get(topic, []), data["items"], review, dropped)
    levels = {}
    for qs in banks.values():
        for q in qs:
            if "group" in q:
                levels.setdefault(q["group"], set()).add(q["level"])
    mixed = [g for g, ls in levels.items() if len(ls) > 1]
    assert not mixed, f"passage sets must sit at one level: {mixed}"
    OUT.mkdir(parents=True, exist_ok=True)
    for old in OUT.glob("*.json"):  # never leave a bank behind that the current items no longer produce
        old.unlink()
    for topic, qs in banks.items():
        (OUT / f"{topic}.json").write_text(json.dumps({"topic": topic, "questions": qs}, ensure_ascii=False, indent=1))
        print(f"{topic}: {len(qs)} questions")
    print(f"dropped by review: {len(dropped)}, not yet reviewed: {len(unreviewed)}, "
          f"edited since review (not shipped until re-reviewed): {len(stale)}")
    if stale:
        print("  stale:", ", ".join(stale[:10]))


if __name__ == "__main__":
    main()
