#!/usr/bin/env python3
"""Held "model split" past-paper MCQs: find them, pack them for a blind re-answer, score the answers.

These are past-paper single MCQs (English, Chinese) whose printed key was checked blind by two models that disagreed, so
`load_pp.py select` rejects them as `blind-disagree` (docs/todo.md, "PRIORITY: resolve every past-paper MCQ", item P3).
Nothing here selects, uploads or writes SQL; all data stays outside the repo under /data/alvin/tmp/cookie-codex/splits/.

  python3 scripts/pastpapers/splits.py find     [--subject english|chinese|all] [--run DIR]
  python3 scripts/pastpapers/splits.py pack     [--subject ...] [--size 60]
  python3 scripts/pastpapers/splits.py report   [--subject ...]
  python3 scripts/pastpapers/splits.py selftest

find   reads the newest full single-MCQ selection of the subject (the newest ppimport/*/<subject>/rejects.jsonl of 2000+
       rows: the passage runs are small), takes its `blind-disagree` rows, rebuilds each question from
       pastpapers/<subject>/<year>/merged.jsonl (+ tags72, stemfix, blind, second, consensus) and writes
       splits/<subject>/found.jsonl (id, src_id, subtopic, stem, options, key, earlier answers) and skipped.jsonl.
       A row is skipped when it needs more than the row holds: not 4 options, garbled text, an incomplete stem, an English
       passage section (Q16+ / Booklet B), a picture (figure words or a crop), a Chinese sub-topic that is a passage or
       cloze, a sub-topic not in the syllabus, no difficulty, or a copy of another row (same wording and options).
pack   writes splits/<subject>/pack_N.jsonl (about 60 questions): {"id", "stem", "options"} ONLY, no key and no earlier
       answers. The answerer is a model that has seen neither.

OUTPUT CONTRACT (one line per question, two independent answerers):
  splits/<subject>/out_N.jsonl   first answerer, for pack_N.jsonl
  splits/<subject>/out2_N.jsonl  second answerer, for pack_N.jsonl
  {"id": "<pack id>", "answer": <0-based index into that question's options>, "sure": true|false, "why": "<under 15 words>"}

report PROPOSED for release (proposed.jsonl) only when BOTH answerers are sure and both equal the printed key. When the two
agree with each other and differ from the key it is listed in differ.jsonl ("both differ from key": the owner looks).
Everything else (a disagreement, an unsure answer, a missing line) stays held. Also writes counts.json.
"""
import argparse, ast, collections, json, sys, tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import load_pp as L  # reused for the same text rules `select` applies (no select is run)

TMP = Path("/data/alvin/tmp/cookie-codex")
CFG = {"pp": L.DEF_PP, "blind": L.DEF_BLIND, "runs": L.DEF_OUT, "out": TMP / "splits"}
SUBJECTS = ("english", "chinese")
MIN_RUN_ROWS = 2000  # a full single-MCQ selection; passage runs (vocab cloze, reading, cloze) are far smaller


def newest_run(subject, runs):
    best = None
    for p in Path(runs).glob(f"*/{subject}/rejects.jsonl"):
        if sum(1 for _ in open(p)) >= MIN_RUN_ROWS and (best is None or p.stat().st_mtime > best.stat().st_mtime):
            best = p
    return best


def as_list(x):
    if isinstance(x, str):
        try:
            x = ast.literal_eval(x)
        except Exception:
            return []
    return list(x) if isinstance(x, (list, tuple)) else []


def build_rows(subject, rej_path):
    """-> (found rows, skipped rows [{id, why}], total blind-disagree)."""
    subs = L.syllabus_subs(subject)
    bd = [r["id"] for r in L.jl(rej_path) if r["reason"] == "blind-disagree"]
    by_year = collections.defaultdict(list)
    for i in bd:
        by_year[int(i.split("-")[1])].append(i)
    found, skipped, seen = [], [], set()
    for y, ids in sorted(by_year.items()):
        base = Path(CFG["pp"]) / subject / str(y)
        merged, _ = L.apply_stemfix(L.jl(base / "merged.jsonl"), L.jl(base / "stemfix.jsonl"))
        M = {q["id"]: q for q in merged}
        tags = {t["id"]: t for t in L.jl(base / "tags72.jsonl")}
        blind = {b["id"]: b for b in L.jl(Path(CFG["blind"]) / f"{subject}-{y}.jsonl")}
        second = {b["id"]: b for b in L.jl(Path(CFG["blind"]) / "second" / f"{subject}-{y}.jsonl")}
        cons = {c["id"]: c for c in L.jl(Path(CFG["blind"]) / "consensus" / f"{subject}-{y}.jsonl")}
        crops = {c.name.rsplit("-p", 1)[0] for d in ("crops", "recrop", "fixcrop") for c in (base / d).glob("*.png")}
        for i in ids:
            q = M.get(i)
            why = None
            if not q:
                skipped.append({"id": i, "why": "no-merged-row"})
                continue
            opts = as_list(q.get("options"))
            text = (q.get("text") or "").strip()
            t = tags.get(i) or {}
            st = t.get("st")
            if len(opts) != 4:
                why = "not-4-options"
            else:
                why = L.garbled(text, opts)
            if not why and subject == "english":
                why = L.eng_incomplete(text)
                try:
                    n = int(q.get("qno"))
                except (TypeError, ValueError):
                    n = None
                if not why and (n is None or n > 15 or "booklet b" in str(q.get("part") or "").lower().replace("booklet  ", "booklet ")):
                    why = "needs-passage-section"
            if not why and subject == "chinese":
                if st not in L.CHI_SINGLE:
                    why = "needs-passage-subtopic"
                else:
                    why = L.chi_incomplete(text, opts)
            if not why and (i in crops or L.FIG_WORDS_LANG.search(text)):
                why = "needs-picture"
            if not why and st not in subs:
                why = "subtopic-not-in-syllabus"
            if not why and t.get("difficulty") not in L.LEVEL:
                why = "no-difficulty"
            k = L.key(q.get("answer"), opts) if not why else None
            if not why and not k:
                why = "no-printed-key"
            if not why:
                clean = [L.tex_to_text(o) for o in L.strip_opts(opts)]
                hk = L.held_key(text, clean)
                if hk in seen:
                    why = "copy-of-another"
                seen.add(hk)
            if why:
                skipped.append({"id": i, "why": why})
                continue
            b, s, c = blind.get(i) or {}, second.get(i) or {}, cons.get(i) or {}
            found.append({
                "id": L.pp_id(i), "src_id": i, "subject": subject, "subtopic": st, "stem": text, "options": clean,
                "key": int(k) - 1,
                "earlier": {"blind_pick": b.get("pick"), "blind_src": b.get("src"), "second_pick": s.get("pick"),
                            "second_agree2": s.get("agree2"), "consensus": {x: c.get(x) for x in ("kind", "key_old", "key_new") if x in c} or None},
            })
    return found, skipped, len(bd)


def write_jl(p, rows):
    Path(p).parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def find(a):
    for subject in subjects(a):
        rp = Path(a.run) / subject / "rejects.jsonl" if a.run else newest_run(subject, CFG["runs"])
        if not rp or not Path(rp).exists():
            print(f"{subject}: no selection run found")
            continue
        found, skipped, total = build_rows(subject, rp)
        d = Path(CFG["out"]) / subject
        write_jl(d / "found.jsonl", found)
        write_jl(d / "skipped.jsonl", skipped)
        print(f"{subject}: run {rp.parent.parent.name}; blind-disagree {total}; usable {len(found)}; skipped {len(skipped)}")
        print("  skipped why:", dict(collections.Counter(s["why"] for s in skipped).most_common()))
        print("  usable by sub-topic:", dict(collections.Counter(r["subtopic"] for r in found).most_common()))


def pack(a):
    for subject in subjects(a):
        d = Path(CFG["out"]) / subject
        rows = sorted(L.jl(d / "found.jsonl"), key=lambda r: (r["subtopic"], r["id"]))
        for old in d.glob("pack_*.jsonl"):
            old.unlink()
        n = max(1, round(len(rows) / a.size)) if rows else 0
        for j in range(n):  # n near-equal packs of about `size`
            part = rows[j * len(rows) // n:(j + 1) * len(rows) // n]
            write_jl(d / f"pack_{j + 1}.jsonl", [{"id": r["id"], "stem": r["stem"], "options": r["options"]} for r in part])
        print(f"{subject}: {len(rows)} questions in {n} packs: {[len(L.jl(d / f'pack_{j + 1}.jsonl')) for j in range(n)]}")


def load_out(d, prefix):
    out = {}
    for p in sorted(Path(d).glob(f"{prefix}_*.jsonl")):
        for r in L.jl(p):
            if type(r.get("answer")) is int and "id" in r:  # not a bool (True is an int)
                out[r["id"]] = r
    return out


def report(a):
    for subject in subjects(a):
        d = Path(CFG["out"]) / subject
        found = {r["id"]: r for r in L.jl(d / "found.jsonl")}
        o1, o2 = load_out(d, "out"), load_out(d, "out2")
        proposed, differ, held, c = [], [], [], collections.Counter()
        for i, r in found.items():
            x, y = o1.get(i), o2.get(i)
            if not x or not y:
                c["missing"] += 1
                continue
            row = dict(r, a1=x["answer"], a2=y["answer"], sure1=x.get("sure") is True, sure2=y.get("sure") is True, why1=x.get("why"), why2=y.get("why"))
            if x["answer"] == y["answer"] == r["key"] and row["sure1"] and row["sure2"]:
                proposed.append(row)
                c["proposed"] += 1
            elif x["answer"] == y["answer"] != r["key"]:
                differ.append(row)
                c["both_differ_from_key"] += 1
            else:
                c["held"] += 1
                held.append({"id": i, "why": ("both answers match the key but not both are sure" if x["answer"] == y["answer"] == r["key"]
                                              else "the two answers differ from each other")})
        write_jl(d / "proposed.jsonl", proposed)
        write_jl(d / "held.jsonl", held)
        write_jl(d / "differ.jsonl", differ)
        line = {"subject": subject, "questions": len(found), **c}
        (d / "counts.json").write_text(json.dumps(line) + "\n")
        print(json.dumps(line))


def subjects(a):
    return SUBJECTS if a.subject == "all" else (a.subject,)


def selftest():
    import os
    root = Path(tempfile.mkdtemp(prefix="selftest_", dir=str(TMP / "splits") if (TMP / "splits").exists() else str(TMP)))
    pp, bl, runs, out = root / "pp", root / "blind", root / "runs", root / "out"
    saved = dict(CFG)
    CFG.update(pp=pp, blind=bl, runs=runs, out=out)
    try:
        y = pp / "english" / "2030"
        y.mkdir(parents=True)
        mk = lambda n, text, opts, ans, **kw: dict({"id": f"eng-2030-001-q{n:02d}", "paper": "eng-2030-001", "qno": str(n), "part": "Booklet A",
                                                    "format": "mcq", "text": text, "options": opts, "answer": ans}, **kw)
        qs = [mk(1, "The farmer ________ his cows every morning before breakfast.", ["feed", "feeds", "feeding", "fed up"], "2"),
              mk(2, "She was ________ tired that she fell asleep at the desk early.", ["so", "such", "very", "too"], "1"),
              mk(3, "The farmer ________ his cows every morning before breakfast.", ["feed", "feeds", "feeding", "fed up"], "2"),  # copy of 1
              mk(4, "Which one of the three words is the odd one out here today?", ["a", "b", "c"], "1"),  # 3 options
              mk(20, "The best word for the long blank here ________ is not clear today.", ["alpha", "beta", "gamma", "delta"], "1"),
              mk(5, "Look at the picture below and say what ________ the best answer is.", ["alpha", "beta", "gamma", "delta"], "1")]
        write_jl(y / "merged.jsonl", qs)
        write_jl(y / "tags72.jsonl", [{"id": q["id"], "st": "eng-grammar-mcq", "difficulty": 1} for q in qs])
        write_jl(bl / "english-2030.jsonl", [{"id": q["id"], "key": q["answer"], "pick": "3", "agree": False, "src": "text"} for q in qs])
        write_jl(runs / "r1" / "english" / "rejects.jsonl", [{"id": q["id"], "reason": "blind-disagree"} for q in qs] + [{"id": f"x{i}", "reason": "duplicate"} for i in range(MIN_RUN_ROWS)])
        ns = argparse.Namespace(subject="english", run=None, size=2)
        find(ns)
        f = L.jl(out / "english" / "found.jsonl")
        sk = {s["id"]: s["why"] for s in L.jl(out / "english" / "skipped.jsonl")}
        assert [r["src_id"] for r in f] == ["eng-2030-001-q01", "eng-2030-001-q02"], f
        assert all(r["key"] == int(q["answer"]) - 1 for r, q in zip(f, qs)), f
        assert sk == {"eng-2030-001-q03": "copy-of-another", "eng-2030-001-q04": "not-4-options", "eng-2030-001-q20": "needs-passage-section",
                      "eng-2030-001-q05": "needs-picture"}, sk
        pack(ns)
        p = L.jl(out / "english" / "pack_1.jsonl")
        assert set(p[0]) == {"id", "stem", "options"} and len(p) == 2, p
        ids = [r["id"] for r in f]  # q01 key 1 ("feeds"), q02 key 0 ("so")
        write_jl(out / "english" / "out_1.jsonl", [{"id": ids[0], "answer": 1, "sure": True, "why": "x"}, {"id": ids[1], "answer": 2, "sure": True, "why": "x"}])
        write_jl(out / "english" / "out2_1.jsonl", [{"id": ids[0], "answer": 1, "sure": True, "why": "x"}, {"id": ids[1], "answer": 2, "sure": False, "why": "x"}])
        report(ns)
        assert [r["id"] for r in L.jl(out / "english" / "proposed.jsonl")] == [ids[0]]
        assert [r["id"] for r in L.jl(out / "english" / "differ.jsonl")] == [ids[1]]
        # strict types: answer must be a real int (not true), sure the JSON boolean true (not "false" or 1); held rows are listed
        write_jl(out / "english" / "out_1.jsonl", [{"id": ids[0], "answer": True, "sure": True}, {"id": ids[1], "answer": 0, "sure": "false"}])
        write_jl(out / "english" / "out2_1.jsonl", [{"id": ids[0], "answer": 1, "sure": 1}, {"id": ids[1], "answer": 0, "sure": True}])
        report(ns)
        assert L.jl(out / "english" / "proposed.jsonl") == [] and [h["id"] for h in L.jl(out / "english" / "held.jsonl")] == [ids[1]], \
            "answer true is dropped (missing); sure 'false' is not sure"
        assert L.jl(out / "english" / "held.jsonl")[0]["why"]
        print("selftest ok")
    finally:
        CFG.update(saved)
        import shutil
        shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("cmd", choices=("find", "pack", "report", "selftest"))
    p.add_argument("--subject", default="all", choices=("all", *SUBJECTS))
    p.add_argument("--run", default="", help="find: a ppimport run directory (default: the newest full selection)")
    p.add_argument("--size", type=int, default=60)
    a = p.parse_args()
    selftest() if a.cmd == "selftest" else {"find": find, "pack": pack, "report": report}[a.cmd](a)
