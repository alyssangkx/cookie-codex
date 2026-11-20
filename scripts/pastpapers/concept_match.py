#!/usr/bin/env python3
"""Past-paper precedent for generated questions (owner rule, 21 Nov 2026): a generated question stays only if some past
paper has a question testing the same concept (any format). Private data stays outside the repo.

  concept_match.py pack   [--out DIR]     dev: probes.jsonl from the site banks (Maths: 2 questions per template) plus
                                          calibration probes (real past-paper MCQs that must find a twin; owner-ruled-out
                                          and off-syllabus questions that must not)
  concept_match.py run    PROBES OUT      server (GPU): for each probe, 8 candidates from ALL scanned questions of the
                                          subject (word overlap, same sub-topic first), then Qwen2.5-72B judges whether
                                          one tests the same concept -> OUT/results.jsonl {pid, cands, match, reason}
  concept_match.py report PROBES RESULTS  dev: calibration, counts per subject and sub-topic, no-match list -> report.md
  concept_match.py selftest
"""
import argparse
import collections
import json
import math
import os
import random
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
TMP = Path("/data/alvin/tmp/cookie-codex")
SUBJECTS = {"math": "maths", "science": "science", "english": "english", "chinese": "chinese"}  # bank folder -> past-paper subject
STOP = set("""a an the of to in on at for and or is are was were be been it its this that these those which what who whom
whose how why when where with as by from into than then there their they them he she his her you your we our i my me do does
did not no can could would should will shall may might has have had more most less least following shown below above""".split())
PROMPT = ("Generated question:\n<<<{gen}>>>\n\nPast-paper questions:\n{cands}\n\n"
          "Does any past-paper question test the same concept as the generated question: the same fact, rule or skill a pupil "
          "must know to answer it, even if the numbers, context, wording or question format differ? A question on the same "
          "broad topic that needs different knowledge does NOT count. Reply with JSON only: "
          "{{\"match\": <the number 1-{n} of the best match, or null>, \"reason\": \"<one short sentence: the shared concept, or what none of them tests>\"}}")
# off-syllabus probes: concepts P6 does not teach (CLAUDE.md: no mass and acceleration, no action-reaction; Speed is not in
# the 2021 Maths syllabus; owner: no reproduction from plant parts). They must find no match.
NEGATIVE = [
    ("science", "A force of 10 N acts on a 2 kg trolley. What is the acceleration of the trolley?", ["2 m/s²", "5 m/s²", "8 m/s²", "20 m/s²"]),
    ("science", "A boy pushes against a wall. Which statement describes the reaction force?", ["The wall pushes the boy with an equal force in the opposite direction", "The wall does not push back", "The wall pushes the boy with a bigger force", "The wall pulls the boy towards it"]),
    ("science", "During which stage of cell division do the chromosomes line up in the middle of the cell?", ["Prophase", "Metaphase", "Anaphase", "Telophase"]),
    ("science", "Which gas is produced when an acid reacts with a metal carbonate?", ["Hydrogen", "Oxygen", "Carbon dioxide", "Nitrogen"]),
    ("science", "What is the chemical formula of glucose produced in photosynthesis?", ["C6H12O6", "CO2", "H2O", "O2"]),
    ("science", "Which particle in an atom has a negative charge?", ["Proton", "Neutron", "Electron", "Nucleus"]),
    ("science", "A wire has a voltage of 6 V across it and a current of 2 A. What is its resistance?", ["3 ohms", "4 ohms", "8 ohms", "12 ohms"]),
    ("science", "Which of these is an example of a plant reproducing from its leaves?", ["Bryophyllum", "Rose", "Hibiscus", "Balsam"]),
    ("maths", "A car travels 180 km in 3 hours. What is its average speed?", ["50 km/h", "60 km/h", "90 km/h", "540 km/h"]),
    ("maths", "Solve the quadratic equation x² - 5x + 6 = 0.", ["x = 1 or 6", "x = 2 or 3", "x = -2 or -3", "x = 5 or 6"]),
    ("maths", "What is the value of sin 30°?", ["0.5", "0.707", "0.866", "1"]),
    ("maths", "What is the gradient of the straight line y = 3x + 2?", ["2", "3", "5", "6"]),
    ("maths", "Find the derivative of 3x².", ["3x", "6x", "6", "x³"]),
    ("english", "What is the rhyme scheme of a Shakespearean sonnet?", ["ABAB CDCD EFEF GG", "ABBA ABBA CDE CDE", "AABB CCDD EEFF GG", "ABCABC DEFDEF"]),
    ("chinese", "下列哪一项是文言文中“之”作代词的用法？", ["（1）学而时习之", "（2）大道之行也", "（3）何陋之有", "（4）予独爱莲之出淤泥而不染"]),
]
RULED_OUT = [("science", "sci-cycles-repro-plants", k) for k in ("rq-221", "rq-818", "rq-119", "rq-211", "rp-013")]  # owner, 21 Nov 2026


def words(t):
    """Tokens for overlap: lower-case words (stopwords and pure numbers dropped) and CJK character bigrams."""
    t = str(t or "")
    out = [w for w in re.findall(r"[a-z][a-z'-]+", t.lower()) if w not in STOP and len(w) > 2]
    cjk = re.sub(r"[^㐀-鿿]", " ", t).split()
    for run in cjk:
        out += [run[i:i + 2] for i in range(len(run) - 1)] or [run]
    return out


def qtext(stem, options):
    return (str(stem).strip() + "\n" + "\n".join(f"({i + 1}) {re.sub(r'^\s*\(?\d\)?\s*', '', str(o))}" for i, o in enumerate(options or []))).strip()


def jl(p):
    return [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()] if Path(p).exists() else []


def pack(a):
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    probes = []
    for bank, subj in SUBJECTS.items():
        per_tpl = collections.defaultdict(list)
        for f in sorted((REPO / "site/src/data/quiz" / bank).glob("*.json")):
            for q in json.loads(f.read_text())["questions"]:
                sub = (q.get("outcomes") or [f.stem + "-0"])[0].rsplit("-", 1)[0]
                unit = q.get("template") if bank == "math" else q["id"]  # Maths: every question of a template tests one thing
                per_tpl[unit].append({"pid": q["id"], "kind": "gen", "subject": subj, "sub": sub, "unit": unit,
                                      "text": qtext(q["stem"], q["options"])})
        for unit, qs in per_tpl.items():
            probes += qs[:2] if bank == "math" else qs
    rnd = random.Random(21)
    for subj in SUBJECTS.values():
        pool = []
        for y in range(2018, 2027):
            tags = {t["id"]: t for t in jl(TMP / "pastpapers" / subj / str(y) / "tags72.jsonl")}
            for q in jl(TMP / "pastpapers" / subj / str(y) / "merged.jsonl"):
                if q.get("format") == "mcq" and len(q.get("options") or []) == 4 and len(str(q.get("text") or "")) >= 30:
                    pool.append({"pid": "cal-pos-" + q["id"], "kind": "cal-pos", "subject": subj, "sub": (tags.get(q["id"]) or {}).get("st"),
                                 "unit": q["id"], "exclude": q["id"], "text": qtext(q["text"], q["options"])})
        probes += rnd.sample(pool, min(40, len(pool)))
    items = {}
    for f in (REPO / "scripts/quiz/science/items").glob("*.json"):
        d = json.loads(f.read_text())
        for it in d["items"]:
            items[(d["subtopic"], it["key"])] = it
    for subj, sub, key in RULED_OUT:
        it = items[(sub, key)]
        probes.append({"pid": f"cal-neg-{key}", "kind": "cal-neg", "subject": subj, "sub": sub, "unit": key, "text": qtext(it["stem"], it["options"])})
    for i, (subj, stem, opts) in enumerate(NEGATIVE):
        probes.append({"pid": f"cal-neg-off{i:02d}", "kind": "cal-neg", "subject": subj, "sub": None, "unit": f"off{i:02d}", "text": qtext(stem, opts)})
    with open(out / "probes.jsonl", "w", encoding="utf-8") as f:
        for p in probes:
            f.write(json.dumps(p, ensure_ascii=False) + "\n")
    print(len(probes), "probes", dict(collections.Counter((p["kind"], p["subject"]) for p in probes)), "->", out / "probes.jsonl")


class Index:
    """TF-IDF over one subject's scanned questions (all formats), searched through an inverted index."""

    def __init__(self, docs):
        self.docs = docs
        df = collections.Counter()
        self.tf = []
        for d in docs:
            c = collections.Counter(words(d["text"]))
            self.tf.append(c)
            df.update(c.keys())
        n = len(docs)
        self.idf = {w: math.log((n + 1) / (k + 1)) + 1 for w, k in df.items()}
        self.post = collections.defaultdict(list)
        self.norm = []
        for i, c in enumerate(self.tf):
            vec = {w: (1 + math.log(k)) * self.idf[w] for w, k in c.items()}
            self.norm.append(math.sqrt(sum(v * v for v in vec.values())) or 1)
            for w, v in vec.items():
                self.post[w].append((i, v))

    def top(self, text, sub=None, k=8, exclude=None):
        c = collections.Counter(words(text))
        q = {w: (1 + math.log(n)) * self.idf[w] for w, n in c.items() if w in self.idf}
        qn = math.sqrt(sum(v * v for v in q.values())) or 1
        score = collections.defaultdict(float)
        for w, qv in q.items():
            for i, v in self.post[w]:
                score[i] += qv * v
        ranked = []
        for i, s in score.items():
            d = self.docs[i]
            if d["id"] == exclude:
                continue
            ranked.append((s / (qn * self.norm[i]) + (0.15 if sub and d.get("st") == sub else 0.0), i))
        ranked.sort(reverse=True)
        return [self.docs[i] for _, i in ranked[:k]]


def corpus(root, subj):
    docs = []
    for ydir in sorted((root / subj).glob("20[0-9][0-9]")):
        tags = {t["id"]: t for t in jl(ydir / "tags72.jsonl")}
        for q in jl(ydir / "merged.jsonl"):
            t = qtext(q.get("text") or "", q.get("options") or [])
            if len(t) >= 15:
                docs.append({"id": q["id"], "st": (tags.get(q["id"]) or {}).get("st"), "text": t[:600]})
    return docs


def parse(raw, n):
    m = re.search(r"\{.*\}", raw or "", re.S)
    try:
        j = json.loads(m.group(0)) if m else {}
    except Exception:
        j = {}
    k = j.get("match")
    k = int(k) if isinstance(k, (int, float)) or (isinstance(k, str) and k.strip().isdigit()) else None
    return (k if k and 1 <= k <= n else None), str(j.get("reason") or "")[:300], bool(m)


def run(a):
    root = Path(os.environ.get("PP_ROOT", "/data/alvin/cookie/pastpapers_full"))
    probes = jl(a.probes)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    done = {r["pid"] for r in jl(out / "results.jsonl")}
    todo = [p for p in probes if p["pid"] not in done]
    print(len(todo), "probes to judge", flush=True)
    if not todo:
        return
    idx = {s: Index(corpus(root, s)) for s in sorted({p["subject"] for p in todo})}
    print({s: len(i.docs) for s, i in idx.items()}, "scanned questions indexed", flush=True)
    from vllm import LLM, SamplingParams
    llm = LLM(model=os.environ.get("PP_LLM", "Qwen/Qwen2.5-72B-Instruct-AWQ"), tensor_parallel_size=int(os.environ.get("PP_TP", "4")),
              gpu_memory_utilization=0.9, max_model_len=8192, max_num_seqs=32, enforce_eager=bool(os.environ.get("PP_EAGER")))
    sp = SamplingParams(temperature=0, max_tokens=160)
    sysmsg = "You compare Singapore Primary 6 (PSLE) exam questions. You answer with JSON only."
    with open(out / "results.jsonl", "a", encoding="utf-8") as f:
        for i in range(0, len(todo), 64):
            ch = todo[i:i + 64]
            cands = [idx[p["subject"]].top(p["text"], p.get("sub"), 8, p.get("exclude")) for p in ch]
            msgs = [[{"role": "system", "content": sysmsg},
                     {"role": "user", "content": PROMPT.format(gen=p["text"][:1500], n=len(c),
                                                               cands="\n\n".join(f"[{j + 1}] {d['text']}" for j, d in enumerate(c)))}]
                    for p, c in zip(ch, cands)]
            for p, c, o in zip(ch, cands, llm.chat(msgs, sp, use_tqdm=False)):
                raw = o.outputs[0].text
                k, reason, ok = parse(raw, len(c))
                f.write(json.dumps({"pid": p["pid"], "cands": [d["id"] for d in c], "match": c[k - 1]["id"] if k else None,
                                    "reason": reason, "parsed": ok}, ensure_ascii=False) + "\n")
            f.flush()
            print(f"{min(i + 64, len(todo))}/{len(todo)}", flush=True)


def report(a):
    probes = {p["pid"]: p for p in jl(a.probes)}
    res = {r["pid"]: r for r in jl(a.results)}
    L = ["# Past-paper precedent: judge report", ""]
    cal = collections.defaultdict(collections.Counter)
    for pid, r in res.items():
        p = probes.get(pid)
        if p and p["kind"] != "gen":
            cal[p["kind"]][("match" if r["match"] else "none")] += 1
    pos, neg = cal["cal-pos"], cal["cal-neg"]
    L += [f"Calibration: real past-paper MCQs that found a twin {pos['match']}/{sum(pos.values())}; "
          f"ruled-out or off-syllabus questions wrongly matched {neg['match']}/{sum(neg.values())}.", ""]
    L += [f"- wrongly matched: {pid}: {probes[pid]['text'][:90]!r} -> {r['match']} ({r['reason']})"
          for pid, r in res.items() if probes.get(pid, {}).get("kind") == "cal-neg" and r["match"]]
    units = collections.defaultdict(list)
    for pid, r in res.items():
        p = probes.get(pid)
        if p and p["kind"] == "gen":
            units[(p["subject"], p["sub"], p["unit"])].append((p, r))
    keep = {u: any(r["match"] for _, r in v) for u, v in units.items()}
    per = collections.defaultdict(collections.Counter)
    for (s, sub, _), k in keep.items():
        per[s]["kept" if k else "no-match"] += 1
    L += ["", "| subject | judged (Maths: templates) | match | no match |", "|---|---|---|---|"]
    L += [f"| {s} | {sum(c.values())} | {c['kept']} | {c['no-match']} |" for s, c in sorted(per.items())]
    subs = collections.Counter((s, sub) for (s, sub, _), k in keep.items() if not k)
    L += ["", "No-match by sub-topic (top 25):"] + [f"- {s} {sub}: {n}" for (s, sub), n in subs.most_common(25)]
    nomatch = [(u, v) for u, v in units.items() if not keep[u]]
    random.Random(7).shuffle(nomatch)
    L += ["", "Sample of no-match decisions (30):"]
    for (s, sub, unit), v in nomatch[:30]:
        p, r = v[0]
        L += [f"- **{s} {sub}** `{unit}`: {p['text'][:220]!r}  \n  judge: {r['reason']}"]
    Path(a.out).write_text("\n".join(L) + "\n", encoding="utf-8")
    with open(Path(a.out).with_suffix(".nomatch.jsonl"), "w", encoding="utf-8") as f:
        for (s, sub, unit), v in sorted(nomatch):
            f.write(json.dumps({"subject": s, "sub": sub, "unit": unit, "pids": [p["pid"] for p, _ in v], "reason": v[0][1]["reason"]}, ensure_ascii=False) + "\n")
    print("\n".join(L[:12]))
    print("->", a.out)


def selftest():
    assert words("The plant's leaves make 12 food.") == ["plant's", "leaves", "make", "food"]
    assert "种子" in words("种子发芽需要水") and "the" not in words("the seed")
    docs = [{"id": "a", "st": "s1", "text": "seeds need water air and warmth to germinate"},
            {"id": "b", "st": "s2", "text": "the heart pumps blood around the body"},
            {"id": "c", "st": "s1", "text": "magnets attract iron and steel"}]
    ix = Index(docs)
    assert ix.top("Do seeds need light to germinate?", "s1", 2)[0]["id"] == "a"
    assert all(d["id"] != "a" for d in ix.top("seeds germinate water", None, 3, exclude="a"))
    assert parse('{"match": 2, "reason": "same"}', 8) == (2, "same", True)
    assert parse('```json\n{"match": null, "reason": "no"}\n```', 8) == (None, "no", True)
    assert parse('{"match": 9, "reason": "x"}', 8)[0] is None and parse("garbage", 8) == (None, "", False)
    assert qtext("Q?", ["(1) a", "b"]) == "Q?\n(1) a\n(2) b"
    print("concept_match selftest ok")


if __name__ == "__main__":
    if sys.argv[1:2] == ["selftest"]:
        selftest()
        sys.exit()
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers(dest="cmd", required=True)
    p = sp.add_parser("pack"); p.add_argument("--out", default=str(TMP / "concept"))
    p = sp.add_parser("run"); p.add_argument("probes"); p.add_argument("out")
    p = sp.add_parser("report"); p.add_argument("probes"); p.add_argument("results"); p.add_argument("--out", default=str(TMP / "concept" / "report.md"))
    a = ap.parse_args()
    {"pack": pack, "run": run, "report": report}[a.cmd](a)
