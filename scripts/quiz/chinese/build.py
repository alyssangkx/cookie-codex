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
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from bankcommon import fingerprint  # noqa: E402  (shared with the English build)

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


PASSAGE = re.compile(r"^(cloze|yuedu|duihua)-(\d+)-(\d+)$")  # passage sets: 5 questions on one passage (4 for a dialogue)
DIALOGUE = "chi-dialogue-mcq"  # 8 shared phrases (A-H) for 4 blanks; every other sub-topic has 4 options


PINYIN_SUB = "chi-ciyu-choose"
PINYIN = json.loads((HERE / "pinyin.json").read_text())  # {"word": "pīn yīn", "word|key": override for one item}
ZH_RUN = re.compile(r"[\u4e00-\u9fff]+(?:……[\u4e00-\u9fff]+)*")
EN = re.compile(r"[A-Za-z]")


def _py(word, key):
    py = PINYIN.get(f"{word}|{key}") or PINYIN.get(word)
    if not py:
        raise SystemExit(f"pinyin.json has no reading for {word!r} (item {key}); add it")
    return py


def add_pinyin(text, key):
    """Pinyin for the Chinese words in the ENGLISH parts of a line only: "词 = meaning" becomes "词 (pīn yīn) = meaning",
    and a Chinese run inside an English parenthetical gets " pīn yīn" after it (after the closing 」 when quoted).
    Chinese-only text is never touched. Applied to the built bank, so item files, review.json and fingerprints stay as they are."""
    out, i = [], 0
    if " = " in text:  # gloss line: segments joined by "；"
        segs = []
        for seg in text.split("；"):
            if " = " in seg:
                w, m = seg.split(" = ", 1)
                seg = f"{w.strip()} ({_py(w.strip(), key)}) = {m}"
            segs.append(seg)
        text = "；".join(segs)
    depth, start, spans = 0, 0, []
    for j, c in enumerate(text):
        if c == "(":
            if depth == 0:
                start = j
            depth += 1
        elif c == ")" and depth:
            depth -= 1
            if depth == 0:
                spans.append((start, j + 1))
    for a, b in spans:
        out.append(text[i:a])
        sp = text[a:b]
        if EN.search(sp):
            sp = re.sub(ZH_RUN.pattern + "」?", lambda m: _pyrun(m, key), sp)  # "「词」" keeps its quote; the pinyin follows it
        out.append(sp)
        i = b
    out.append(text[i:])
    return "".join(out)


def _pyrun(m, key):
    g = m.group()
    quoted = g.endswith("」")
    w = g[:-1] if quoted else g
    nxt = m.string[m.end():m.end() + 1]
    return f"{w}{'」' if quoted else ''} {_py(w, key)}{' ' if nxt.isascii() and nxt.isalnum() else ''}"


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
                q["stem"] = q["stem"].replace(f"（{n}）＿＿", it["options"][it["answer"]])  # a filled blank reads as plain text (a numbered gap with the answer in it looked unfinished)
        keep.append(q)
    bank[:] = keep


def hold_dialogues(bank, items, dropped):
    """A dialogue set ships whole or not at all: its 4 blanks share one stem and one list of 8 phrases, and a
    blank that is never asked would sit in the dialogue unanswerable. Any blank held, stale or unreviewed
    holds its set."""
    want = {1, 2, 3, 4}
    total, shipped = {}, {}
    for it in items:
        if (m := PASSAGE.match(it["key"])):
            total.setdefault(m[2], []).append(int(m[3]))
    for q in bank:
        if q["params"]["subtopic"] == DIALOGUE and (m := PASSAGE.match(q["params"]["key"])):
            shipped.setdefault(m[2], []).append(int(m[3]))
    # exactly blanks 1-4, each once, in the items and in what ships
    whole = {k for k, s in shipped.items() if sorted(s) == sorted(want) and sorted(total.get(k, [])) == sorted(want)}
    keep = []
    for q in bank:
        m = PASSAGE.match(q["params"]["key"]) if q["params"]["subtopic"] == DIALOGUE else None
        if m and m[2] not in whole:
            dropped.append(f"{DIALOGUE}|{q['params']['key']} (dialogue set held: not all 4 blanks shipped)")
        else:
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
            if sub == PINYIN_SUB:
                it = {**it, "explain": [x and {**x, "why": add_pinyin(x["why"], it["key"])} for x in it["explain"]],
                      "solution": [add_pinyin(l, it["key"]) for l in it["solution"]],
                      "gloss": add_pinyin(it["gloss"], it["key"]) if it.get("gloss") else it.get("gloss")}
            # writers cycle the answer A-D in item order; shuffle each item's options with a seed from its key,
            # so the order is random to a child but identical on every rebuild
            # a dialogue set shares one list of 8 phrases across its 4 blanks: ONE seed per set, so the
            # shuffled list stays identical on all four items (the seed is the set key, not the item key)
            m = PASSAGE.match(it["key"])
            n_opt = len(it["options"])  # 4, or 8 for dialogue sets (check_chinese.py enforces which)
            order = list(range(n_opt))
            random.Random(f"{sub}|{m[1]}-{m[2]}" if sub == DIALOGUE and m else f"{sub}|{it['key']}").shuffle(order)
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
                "solution": [re.sub(r"[。，]([；;])", r"\1", line) for line in it["solution"]] + gloss_line(it),  # tidy "。；" joins
                "params": {"key": it["key"], "subtopic": sub},
                **({"group": f"{sub}:{m[2]}", "seq": int(m[3])} if (m := PASSAGE.match(it["key"])) else {}),
            })
        if sub == "chi-cloze-mcq":
            fill_cloze(banks.get(topic, []), data["items"], review, dropped)
        if sub == DIALOGUE:
            hold_dialogues(banks.get(topic, []), data["items"], dropped)
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
        if not qs:
            continue  # an empty bank (e.g. every dialogue set held) is not written
        (OUT / f"{topic}.json").write_text(json.dumps({"topic": topic, "questions": qs}, ensure_ascii=False, indent=1))
        print(f"{topic}: {len(qs)} questions")
    print(f"dropped by review: {len(dropped)}, not yet reviewed: {len(unreviewed)}, "
          f"edited since review (not shipped until re-reviewed): {len(stale)}")
    if stale:
        print("  stale:", ", ".join(stale[:10]))


if __name__ == "__main__":
    main()
