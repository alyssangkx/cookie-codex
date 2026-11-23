#!/usr/bin/env python3
"""Explanations for past-paper MCQs (owner, 23 Nov 2026: "why is the answer correct ... for all applicable English
questions"; Maths and Science next): why the key is right, and why each other option does not fit, for a 12-year-old.

  explain.py pack [SEL ...]        dev: items.jsonl from the selections (default: English grammar and vocabulary)
  explain.py write ITEMS           server: Qwen2.5-72B writes one per item (PP_LLM, PP_TP) -> written.jsonl (resumable)
  explain.py judge ITEMS           server: a second model of another family (Llama-3.1-70B, PP_JUDGE) checks each one
                                   against the question and its key -> judged.jsonl (resumable)
  explain.py calib                 dev: calib.jsonl = 60 passed explanations + 60 planted wrong ones (another question's
                                   reason, or the reason argued for a wrong option): the judge must reject >= 90% of the
                                   planted ones before its verdicts count (`judge` on calib.jsonl, then `calib-score`)
  explain.py revise ITEMS          server: the writer rewrites every rejected one, given the judge's objection ->
                                   revised.jsonl; `judge2` checks those -> judged2.jsonl (a second rejection drops it)
  explain.py apply [--sample N]    dev: the passed ones -> <selection>/<subject>/explain.jsonl (read by load_pp upload);
                                   prints N random passed ones for the owner's spot check
  explain.py apply-opus [--sample N]  dev: the Claude Opus agents' files (opus/out_NN_partN.jsonl, owner's choice A,
                                   23 Nov 2026) -> each selection's explain.jsonl; lines that doubt the key go to
                                   opus/doubts.jsonl for the owner, never to the site
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
WORK = Path(os.environ.get("PP_WORK", str(TMP / "explain")))  # the server sets its own folder
SELS = [TMP / "ppimport/eng1826d/english"]
# Chinese (owner, 24 Nov 2026: option B, Qwen writes and InternLM checks): the single-question sections
SELS_ZH = [TMP / "ppimport/chi1826e/chinese"]
SUBS = {"english": {"eng-grammar-mcq", "eng-vocab-mcq"},
        "chinese": {"chi-pinyin-sound", "chi-zixing-form", "chi-ciyu-choose", "chi-ciyu-idiom", "chi-juzi-choose", "chi-juzi-guanlian"}}
LLM = os.environ.get("PP_LLM", "Qwen/Qwen2.5-72B-Instruct-AWQ")
JUDGE = os.environ.get("PP_JUDGE", "hugging-quants/Meta-Llama-3.1-70B-Instruct-AWQ-INT4")
SYS = ("You are a kind, precise Singapore primary school English teacher. You explain PSLE English MCQ answers to a "
       "12-year-old in simple words.")
WRITE = ("Question: {stem}\nOptions:\n{opts}\nThe correct answer is ({k}) {ans}.\n\n"
         "Explain in one or two short sentences why ({k}) is correct: name the grammar rule, or say what the word means "
         "and why it fits this sentence. Then, for each other option, write one short sentence saying why it does not fit. "
         "Quote the words themselves, use simple language, and never say another option could also be right.\n"
         "Reply with JSON only: {{\"right\": \"...\", \"wrong\": {{\"<option number>\": \"...\"}}}}")
REVISE = ("Question: {stem}\nOptions:\n{opts}\nThe correct answer (already confirmed) is ({k}) {ans}.\n"
          "Your earlier explanation:\n{old}\nA reviewer objected: {problem}\n\n"
          "If the objection is right, fix the explanation; if it is wrong, keep what was right but make the wording "
          "clearer. Keep it short and simple for a 12-year-old, quote the words, never say another option could also be "
          "right. Reply with JSON only: {{\"right\": \"...\", \"wrong\": {{\"<option number>\": \"...\"}}}}")
SYS_ZH = "你是一位亲切、严谨的新加坡小学华文老师，为12岁的学生解释小六华文选择题的答案。"
WRITE_ZH = ("题目：{stem}\n选项：\n{opts}\n正确答案是（{k}）{ans}。\n\n"
            "先用一两句简单的中文说明为什么（{k}）是对的：说明词语的意思、用法或搭配，或者字音、字形的分别；后面用括号加一句英文翻译。"
            "然后为每个其他选项写一句话，说明它为什么不对（中文，后面用括号加简短英文）。不要说别的选项也可以。\n"
            "只回复JSON：{{\"right\": \"中文说明（English: ...）\", \"wrong\": {{\"<选项号>\": \"...\"}}}}")
CHECK_ZH = ("题目：{stem}\n选项：\n{opts}\n正确答案（已确认）是（{k}）{ans}。\n老师为12岁学生写的解释：\n为什么（{k}）对：{right}\n{wrongs}\n\n"
            "这个解释里的每一句都正确吗？它是否支持（{k}），而没有暗示别的选项也对？"
            "只回复JSON：{{\"ok\": true 或 false, \"problem\": \"...\"}}")
JUDGE_ZH = os.environ.get("PP_JUDGE_ZH", "internlm/internlm2_5-20b-chat")
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
               max_model_len=4096, enforce_eager=bool(os.environ.get("PP_EAGER")), trust_remote_code=True), SamplingParams(temperature=0, max_tokens=500)


def run(items_file, phase):
    """write: items -> written.jsonl; judge: written -> judged.jsonl (for calib.jsonl: the explanations inside it ->
    calib_judged.jsonl); revise: rejected -> revised.jsonl; judge2: revised -> judged2.jsonl. All resumable."""
    items_file = Path(items_file)
    items = jl(items_file)
    d = items_file.parent
    calib = items_file.name == "calib.jsonl"
    names = {"write": "written", "judge": "calib_judged" if calib else "judged", "revise": "revised", "judge2": "judged2"}
    out = d / f"{names[phase]}.jsonl"
    key = lambda r: (r["id"], r.get("fp"))
    done = {key(r) for r in jl(out)}
    if phase == "write":
        src = {}
    elif phase == "judge":
        src = {key(r): r for r in items} if calib else {key(r): r for r in jl(d / "written.jsonl")}
    elif phase == "revise":
        bad = {key(r): r for r in jl(d / "judged.jsonl") if not r["ok"]}
        wr = {key(r): r for r in jl(d / "written.jsonl")}
        src = {k: dict(wr[k], problem=bad[k]["problem"]) for k in bad if (wr.get(k) or {}).get("explain")}
    else:
        src = {key(r): r for r in jl(d / "revised.jsonl")}
    todo = [r for r in items if key(r) not in done and (phase == "write" or (src.get(key(r)) or {}).get("explain"))]
    print(len(todo), "to", phase, flush=True)
    if not todo:
        return
    zh = bool(items) and items[0].get("subject") == "chinese"
    model, sp = llm((JUDGE_ZH if zh else JUDGE) if phase in ("judge", "judge2") else LLM)
    sys_p, write_p, check_p = (SYS_ZH, WRITE_ZH, CHECK_ZH) if zh else (SYS, WRITE, CHECK)
    with open(out, "a", encoding="utf-8") as f:
        for i in range(0, len(todo), 64):
            ch, msgs = todo[i:i + 64], []
            for r in ch:
                k, o = r["answer"], r["options"]
                if phase == "write":
                    p = write_p.format(stem=r["stem"], opts=opts_text(o), k=k + 1, ans=o[k])
                elif phase == "revise":
                    s = src[key(r)]
                    p = REVISE.format(stem=r["stem"], opts=opts_text(o), k=k + 1, ans=o[k], old=say(s["explain"]), problem=s["problem"])
                else:
                    e = src[key(r)]["explain"]
                    wr = "\n".join(f"{'为什么（' + str(j + 1) + '）不对' if zh else 'Why (' + str(j + 1) + ') does not fit'}: {w}" for j, w in enumerate(e["wrong"]) if w)
                    p = check_p.format(stem=r["stem"], opts=opts_text(o), k=k + 1, ans=o[k], right=e["right"], wrongs=wr)
                msgs.append([{"role": "system", "content": sys_p}, {"role": "user", "content": p}])
            for r, res in zip(ch, model.chat(msgs, sp, use_tqdm=False)):
                raw = res.outputs[0].text
                if phase in ("write", "revise"):
                    rec = {"id": r["id"], "fp": r.get("fp"), "explain": shape(parse(raw), r["options"], r["answer"]), "raw": raw}
                else:
                    v = parse(raw) or {}
                    rec = {"id": r["id"], "fp": r.get("fp"), "ok": v.get("ok") is True, "problem": str(v.get("problem") or "")[:300], "raw": raw}
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            f.flush()
            print(f"{min(i + 64, len(todo))}/{len(todo)}", flush=True)


def say(e):
    return f"Why it is right: {e['right']}\n" + "\n".join(f"Why ({j + 1}) does not fit: {w}" for j, w in enumerate(e["wrong"]) if w)


def calib():
    """60 passed explanations kept as they are, and 60 planted wrong ones: half take another question's reason, half say
    the reason for a wrong option (its words put where the answer's were)."""
    items = {r["id"]: r for r in jl(WORK / "items.jsonl")}
    wr = {r["id"]: r["explain"] for r in jl(WORK / "written.jsonl") if r.get("explain")}
    judged = jl(WORK / "judged.jsonl")
    pool = [r["id"] for r in judged if r["ok"]] if judged else list(wr)  # no judge yet: the written ones (only the planted catch rate counts)
    ok = [i for i in pool if i in wr and i in items]
    rng = random.Random(11)
    pick = rng.sample(ok, min(120, len(ok)))
    good, plant = pick[:60], pick[60:]
    out = [dict(items[i], id=f"good-{i}", explain=wr[i], planted=False) for i in good]
    for n, i in enumerate(plant):
        it, e = items[i], dict(wr[i])
        if n % 2:  # another question's reason
            other = wr[plant[(n + 1) % len(plant)]]
            e = dict(e, right=other["right"])
        else:  # argue for a wrong option: its words where the answer's were
            wrong = next(j for j in range(len(it["options"])) if j != it["answer"])
            tail = f"所以答案是（{wrong + 1}）。" if it.get("subject") == "chinese" else f" So the answer is ({wrong + 1})."
            e = dict(e, right=e["right"].replace(it["options"][it["answer"]], it["options"][wrong]) + tail)
        out.append(dict(it, id=f"plant-{i}", explain=e, planted=True))
    (WORK / "calib.jsonl").write_text("".join(json.dumps(x, ensure_ascii=False) + "\n" for x in out))
    print(f"{len(out)} calibration rows -> {WORK / 'calib.jsonl'}")


def calib_score(path=WORK / "calib_judged.jsonl", bar=0.9):
    rows = {r["id"]: r for r in jl(WORK / "calib.jsonl")}
    j = jl(path)
    caught = sum(1 for x in j if rows[x["id"]]["planted"] and not x["ok"])
    planted = sum(1 for x in j if rows[x["id"]]["planted"])
    kept = sum(1 for x in j if not rows[x["id"]]["planted"] and x["ok"])
    good = len(j) - planted
    rate = caught / max(1, planted)
    print(f"judge caught {caught}/{planted} planted wrong explanations ({rate:.0%}); passed {kept}/{good} good ones "
          f"-> {'PASSED' if rate >= bar else 'FAILED'} (bar {bar:.0%})")
    return rate >= bar


def apply(sample=0):
    """Only rows of the current items.jsonl count, matched by id and fingerprint (rows from before fingerprints, fp None,
    are taken as written for the current version); every selection in the items gets a fresh explain.jsonl, empty when
    none passed, so a file from an earlier run never outlives it."""
    items = {r["id"]: r for r in jl(WORK / "items.jsonl")}
    cur = lambda r: r["id"] in items and r.get("fp") in (None, items[r["id"]]["fp"])
    written = {r["id"]: r.get("explain") for r in jl(WORK / "written.jsonl") if cur(r)}
    judged = {r["id"]: r for r in jl(WORK / "judged.jsonl") if cur(r)}
    revised = {r["id"]: r.get("explain") for r in jl(WORK / "revised.jsonl") if cur(r)}
    judged2 = {r["id"]: r for r in jl(WORK / "judged2.jsonl") if cur(r)}
    passed = {i: e for i, e in written.items() if e and judged.get(i, {}).get("ok")}
    passed.update({i: e for i, e in revised.items() if e and judged2.get(i, {}).get("ok") and i not in passed})
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


def mentions(text, opt):
    """The explanation talks about the option: for each part ("had...rushed" -> had, rushed) most of its words appear in
    the text in some form ("incurred" ~ "incur", "backed off" ~ "back off", "blow over" ~ "blows over")."""
    words = lambda s: re.findall(r"[a-z']+", (s or "").lower().replace("’", "'"))
    tw = words(text)

    def near(w):
        if len(w) <= 3:
            return w in tw
        return any(len(x) >= 3 and (x == w or (x[:3] == w[:3] and len(os.path.commonprefix([x, w])) >= max(3, min(len(x), len(w)) - 3))) for x in tw)
    parts = [p for p in re.split(r"\.{2,}|…|/", opt or "") if p.strip()]
    if not parts:
        return False
    for part in parts:
        ws = words(part)
        if not ws or sum(near(w) for w in ws) * 2 < len(ws):
            return False
    return True


def aligned(e, item):
    """The explanation is about this question (an agent once re-took ids by position): its reason quotes the answer,
    and at least two of the wrong-option lines quote their own option."""
    o, k = item["options"], item["answer"]
    hits = sum(mentions(w, o[j]) for j, w in enumerate(e["wrong"]) if j != k and w)
    return mentions(e["right"], o[k]) and hits >= len(o) - 2


def opus_row(x, item):
    """An Opus agent's line as {right, wrong[]}, or None when its shape does not fit the question it names."""
    if not item or x.get("fp") != item["fp"] or "doubt" in x:
        return None
    w, k = x.get("wrong"), item["answer"]
    if not isinstance(x.get("right"), str) or len(x["right"].strip()) < 15 or not isinstance(w, list) or len(w) != len(item["options"]):
        return None
    if w[k] is not None or not all(isinstance(s, str) and s.strip() for j, s in enumerate(w) if j != k):
        return None
    e = {"right": x["right"].strip()[:600], "wrong": [None if j == k else s.strip()[:400] for j, s in enumerate(w)]}
    return e if aligned(e, item) else None


def apply_opus(sample=0):
    import glob
    items = {r["id"]: r for r in jl(WORK / "items.jsonl")}
    got, doubts, bad = {}, [], 0
    for f in sorted(glob.glob(str(WORK / "opus/out_*_part*.jsonl"))):
        for l in open(f, encoding="utf-8"):
            if not l.strip():
                continue
            try:
                x = json.loads(l)
            except Exception:
                bad += 1
                continue
            if "doubt" in x and x.get("id") in items:
                doubts.append({"id": x["id"], "doubt": x["doubt"], "stem": items[x["id"]]["stem"], "options": items[x["id"]]["options"],
                               "answer": items[x["id"]]["answer"]})
                continue
            e = opus_row(x, items.get(x.get("id")))
            if e:
                got[x["id"]] = e
            else:
                bad += 1
    by = {r["sel"]: [] for r in items.values()}
    for i, e in got.items():
        by[items[i]["sel"]].append({"id": i, "fp": items[i]["fp"], "explain": e, "src": "claude-opus"})
    for sel, rows in by.items():
        (Path(sel) / "explain.jsonl").write_text("".join(json.dumps(x, ensure_ascii=False) + "\n" for x in rows))
    (WORK / "opus/doubts.jsonl").write_text("".join(json.dumps(x, ensure_ascii=False) + "\n" for x in doubts))
    print(f"{len(items)} questions: {len(got)} explained, {len(doubts)} key doubts (opus/doubts.jsonl), {bad} lines unusable, "
          f"{len(items) - len(got) - len(doubts)} not covered")
    for i in random.Random(7).sample(sorted(got), min(sample, len(got))):
        r, e = items[i], got[i]
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
    it = {"fp": "f", "answer": 0, "options": opts}
    wl = [None, "\"Hasn't\" needs has.", "\"Isn't\" needs is.", "\"Didn't\" is past."]
    ok = {"id": "x", "fp": "f", "right": "A question tag repeats the helper, so \"doesn't he?\"", "wrong": wl}
    assert opus_row(ok, it)["wrong"] == wl
    assert opus_row(dict(ok, fp="g"), it) is None, "another question version"
    assert opus_row(dict(ok, wrong=["x"] + wl[1:]), it) is None, "the key's slot must be null"
    assert opus_row(dict(ok, wrong=wl[:3]), it) is None and opus_row(dict(ok, doubt="key?"), it) is None
    it2 = {"fp": "f", "answer": 2, "options": ["had...rush", "have...rush", "had...rushed", "have...rushed"]}
    e2 = {"id": "y", "fp": "f", "right": "\"Had I not rushed\" means if I had not rushed.", "wrong": ["\"Rush\" after had is wrong.", "\"Have\" cannot mean if; \"rush\" too.", None, "\"Have\" with \"rushed\" is wrong."]}
    assert opus_row(e2, it2), "multi-part options are matched part by part"
    assert opus_row(dict(e2, right="Fatigue means extreme tiredness."), it2) is None, "a reason about another question is dropped"
    assert mentions('To "incur" a fine means', "incurred") and mentions('When a storm "blows over"', "blow over")
    assert mentions('"Come across as" means', "came across") and not mentions("Fatigue means tiredness.", "incurred")
    print("explain selftest ok")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "pack":
        pack([Path(s) for s in sys.argv[2:] if s != "--zh"] or (SELS_ZH if "--zh" in sys.argv else SELS))
    elif cmd in ("write", "judge", "revise", "judge2"):
        run(sys.argv[2], cmd)
    elif cmd == "apply-opus":
        apply_opus(int(sys.argv[sys.argv.index("--sample") + 1]) if "--sample" in sys.argv else 0)
    elif cmd == "calib":
        calib()
    elif cmd == "calib-score":
        sys.exit(0 if calib_score() else 1)
    elif cmd == "apply":
        apply(int(sys.argv[sys.argv.index("--sample") + 1]) if "--sample" in sys.argv else 0)
    elif cmd == "selftest":
        selftest()
    else:
        sys.exit(__doc__)
