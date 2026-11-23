#!/usr/bin/env python3
"""Explanations for past-paper MCQs (owner, 23 Nov 2026: "why is the answer correct ... for all applicable English
questions"; Maths and Science next): why the key is right, and why each other option does not fit, for a 12-year-old.

  explain.py pack [SEL ...]        dev: items.jsonl from the selections (default: English grammar and vocabulary)
  explain.py write ITEMS           server: Qwen2.5-72B writes one per item (PP_LLM, PP_TP) -> written.jsonl (resumable)
  explain.py judge ITEMS           server: a second model of another family (Llama-3.1-70B, PP_JUDGE) checks each one
                                   against the question and its key -> judged.jsonl (resumable)
  explain.py apply [--sample N]    dev: the passed ones -> <selection>/<subject>/explain.jsonl (read by load_pp upload);
                                   prints N random passed ones for the owner's spot check
  explain.py selftest
A key is never questioned here (the keys are settled); an explanation that argues for another option, or that the judge
calls wrong, is dropped, and that question simply shows no explanation. Past-paper text stays off the repo and the site."""
import json
import os
import random
import re
import sys
from pathlib import Path

TMP = Path("/data/alvin/tmp/cookie-codex")
WORK = TMP / "explain"
SELS = [TMP / "ppimport/eng1826d/english"]
SUBS = {"english": {"eng-grammar-mcq", "eng-vocab-mcq"}}
LLM = os.environ.get("PP_LLM", "Qwen/Qwen2.5-72B-Instruct-AWQ")
JUDGE = os.environ.get("PP_JUDGE", "hugging-quants/Meta-Llama-3.1-70B-Instruct-AWQ-INT4")
SYS = ("You are a kind, precise Singapore primary school English teacher. You explain PSLE English MCQ answers to a "
       "12-year-old in simple words.")
WRITE = ("Question: {stem}\nOptions:\n{opts}\nThe correct answer is ({k}) {ans}.\n\n"
         "Explain in one or two short sentences why ({k}) is correct: name the grammar rule, or say what the word means "
         "and why it fits this sentence. Then, for each other option, write one short sentence saying why it does not fit. "
         "Quote the words themselves, use simple language, and never say another option could also be right.\n"
         "Reply with JSON only: {{\"right\": \"...\", \"wrong\": {{\"<option number>\": \"...\"}}}}")
CHECK = ("Question: {stem}\nOptions:\n{opts}\nThe correct answer (already confirmed) is ({k}) {ans}.\n"
         "A teacher wrote this explanation for a 12-year-old:\nWhy ({k}) is right: {right}\n{wrongs}\n\n"
         "Is every statement in the explanation true English grammar or meaning, and does it support ({k}) without "
         "suggesting any other option is correct? Reply with JSON only: {{\"ok\": true or false, \"problem\": \"...\"}}")


def jl(p):
    p = Path(p)
    return [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()] if p.exists() else []


def parse(text):
    m = re.search(r"\{.*\}", text or "", re.S)
    try:
        return json.loads(m.group(0)) if m else None
    except Exception:
        return None


def fp(r):
    """The question as the explanation was written for it: an explanation is used only while stem, options and key match."""
    import hashlib
    return hashlib.sha1(json.dumps([r["stem"], r["options"], r["answer"]], ensure_ascii=False).encode()).hexdigest()[:12]


def opts_text(opts):
    return "\n".join(f"({i}) {o}" for i, o in enumerate(opts, 1))


def shape(read, opts, k):
    """The written explanation as {right, wrong[]} (null at the key), or None when it is incomplete."""
    if not isinstance(read, dict) or not isinstance(read.get("right"), str) or not read["right"].strip():
        return None
    w = read.get("wrong") if isinstance(read.get("wrong"), dict) else {}
    wrong = []
    for i in range(len(opts)):
        if i == k:
            wrong.append(None)
            continue
        s = w.get(str(i + 1))
        if not isinstance(s, str) or not s.strip():
            return None  # every other option needs its reason
        wrong.append(s.strip()[:400])
    right = read["right"].strip()
    return {"right": right[:600], "wrong": wrong} if len(right) >= 15 else None


def pack(sels):
    WORK.mkdir(parents=True, exist_ok=True)
    out = []
    for sel in sels:
        subject = sel.name
        for r in jl(sel / "selected.jsonl"):
            # a question with a picture is left out: the model reads text only and would explain what it cannot see
            if r["subtopic"] in SUBS.get(subject, set()) and not r.get("grp") and not r.get("crops") and not r.get("set_pages"):
                x = {"id": r["id"], "sel": str(sel), "subject": subject, "stem": r["stem"], "options": r["options"], "answer": r["answer"]}
                out.append(dict(x, fp=fp(x)))
    (WORK / "items.jsonl").write_text("".join(json.dumps(x, ensure_ascii=False) + "\n" for x in out))
    print(f"{len(out)} questions -> {WORK / 'items.jsonl'}")


def llm(model):
    from vllm import LLM, SamplingParams
    return LLM(model=model, tensor_parallel_size=int(os.environ.get("PP_TP", "4")), gpu_memory_utilization=0.9,
               max_model_len=4096, enforce_eager=bool(os.environ.get("PP_EAGER"))), SamplingParams(temperature=0, max_tokens=500)


def run(items_file, phase):
    items = jl(items_file)
    out = Path(items_file).with_name("written.jsonl" if phase == "write" else "judged.jsonl")
    done = {(r["id"], r.get("fp")) for r in jl(out)}  # a changed question (new fp) is written and judged again
    written = {(r["id"], r.get("fp")): r for r in jl(Path(items_file).with_name("written.jsonl"))} if phase == "judge" else {}
    key = lambda r: (r["id"], r.get("fp"))
    todo = [r for r in items if key(r) not in done and (phase == "write" or (written.get(key(r)) or {}).get("explain"))]
    print(len(todo), "to", phase, flush=True)
    if not todo:
        return
    model, sp = llm(LLM if phase == "write" else JUDGE)
    with open(out, "a", encoding="utf-8") as f:
        for i in range(0, len(todo), 64):
            ch, msgs = todo[i:i + 64], []
            for r in ch:
                k, o = r["answer"], r["options"]
                if phase == "write":
                    p = WRITE.format(stem=r["stem"], opts=opts_text(o), k=k + 1, ans=o[k])
                else:
                    e = written[key(r)]["explain"]
                    wr = "\n".join(f"Why ({j + 1}) does not fit: {w}" for j, w in enumerate(e["wrong"]) if w)
                    p = CHECK.format(stem=r["stem"], opts=opts_text(o), k=k + 1, ans=o[k], right=e["right"], wrongs=wr)
                msgs.append([{"role": "system", "content": SYS}, {"role": "user", "content": p}])
            for r, res in zip(ch, model.chat(msgs, sp, use_tqdm=False)):
                raw = res.outputs[0].text
                if phase == "write":
                    rec = {"id": r["id"], "fp": r.get("fp"), "explain": shape(parse(raw), r["options"], r["answer"]), "raw": raw}
                else:
                    v = parse(raw) or {}
                    rec = {"id": r["id"], "fp": r.get("fp"), "ok": v.get("ok") is True, "problem": str(v.get("problem") or "")[:300], "raw": raw}
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            f.flush()
            print(f"{min(i + 64, len(todo))}/{len(todo)}", flush=True)


def apply(sample=0):
    """Only rows of the current items.jsonl count, matched by id and fingerprint (rows from before fingerprints, fp None,
    are taken as written for the current version); every selection in the items gets a fresh explain.jsonl, empty when
    none passed, so a file from an earlier run never outlives it."""
    items = {r["id"]: r for r in jl(WORK / "items.jsonl")}
    cur = lambda r: r["id"] in items and r.get("fp") in (None, items[r["id"]]["fp"])
    written = {r["id"]: r.get("explain") for r in jl(WORK / "written.jsonl") if cur(r)}
    judged = {r["id"]: r for r in jl(WORK / "judged.jsonl") if cur(r)}
    passed = {i: e for i, e in written.items() if e and judged.get(i, {}).get("ok")}
    by = {r["sel"]: [] for r in items.values()}
    for i, e in passed.items():
        by[items[i]["sel"]].append({"id": i, "fp": items[i]["fp"], "explain": e})
    for sel, rows in by.items():
        (Path(sel) / "explain.jsonl").write_text("".join(json.dumps(x, ensure_ascii=False) + "\n" for x in rows))
    n, w, j = len(items), sum(bool(e) for e in written.values()), len(judged)
    print(f"{n} questions: {w} written, {j} judged, {len(passed)} passed ({len(passed) / max(1, n):.0%}); "
          f"incomplete {len(written) - w}, judged wrong {sum(1 for x in judged.values() if not x['ok'])}")
    for i in random.Random(7).sample(sorted(passed), min(sample, len(passed))):
        r, e = items[i], passed[i]
        print(f"\n{r['stem']}\n  " + "  ".join(f"({k + 1}) {o}" for k, o in enumerate(r["options"])) + f"\n  answer ({r['answer'] + 1})")
        print(f"  why right: {e['right']}")
        for k, w in enumerate(e["wrong"]):
            if w:
                print(f"  ({k + 1}) does not fit: {w}")


def selftest():
    opts = ["doesn't", "hasn't", "isn't", "didn't"]
    good = {"right": "Prefers is present simple, so the tag uses does: doesn't he?", "wrong": {"2": "Hasn't needs has as a helper.", "3": "Isn't needs is.", "4": "Didn't is past tense."}}
    assert shape(good, opts, 0) == {"right": good["right"], "wrong": [None, "Hasn't needs has as a helper.", "Isn't needs is.", "Didn't is past tense."]}
    assert shape(dict(good, wrong={"2": "x", "3": "y"}), opts, 0) is None, "every wrong option needs a reason"
    assert shape({"right": "ok", "wrong": good["wrong"]}, opts, 0) is None, "too short to explain anything"
    assert shape(parse("```json\n" + json.dumps(good) + "\n```"), opts, 0)["right"].startswith("Prefers")
    q = {"stem": "s", "options": opts, "answer": 0}
    assert fp(q) == fp(dict(q)) and fp(q) != fp(dict(q, answer=1)) and fp(q) != fp(dict(q, options=opts[::-1])), "a changed key or options is another version"
    print("explain selftest ok")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "pack":
        pack([Path(s) for s in sys.argv[2:]] or SELS)
    elif cmd in ("write", "judge"):
        run(sys.argv[2], cmd)
    elif cmd == "apply":
        apply(int(sys.argv[sys.argv.index("--sample") + 1]) if "--sample" in sys.argv else 0)
    elif cmd == "selftest":
        selftest()
    else:
        sys.exit(__doc__)
