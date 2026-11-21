"""Third-model adjudication of blind-check disagreements (owner, 21 Nov 2026: "when the blind check and the key disagree, a
third model decides, 2 of 3"). Private content stays out of the repo: the pack and results live under /data/alvin/tmp.

  dev:    blind3.py pack [--subject english] [--calib 300] [--push]
             items.jsonl = every single-sentence MCQ whose key and first blind answer disagree, plus a calibration sample
             of items where they agree (the third model's agreement there measures how far to trust it).
  server: blind3.py run            Qwen2.5-72B-Instruct-AWQ (text only, TP4), resumable -> results.jsonl
  dev:    blind3.py report [--pull]  calibration agreement, then per disagreement: third = key (key stands, 2 of 3),
             third = blind (key suspect: hold), neither/unparsed (hold). Writes BLIND/third/<subject>-<year>.jsonl
             {id, key, pick1, pick3, agree3} for load_pp select to use once the owner has seen the calibration.
  selftest
Logs and prints ids and counts only, never question text.
"""
import argparse, collections, json, os, random, re, subprocess, sys
from pathlib import Path

TMP = Path("/data/alvin/tmp/cookie-codex")
PP, BLIND = TMP / "pastpapers", TMP / "audit" / "blindcheck"
SERVER, SERVER_BASE = "alvin@192.168.1.170", "/data/alvin/cookie/blind3"
# single-sentence sections only (passage sets are phase 2, owner 21 Nov 2026)
SINGLE = {"english": {"eng-grammar-mcq", "eng-vocab-mcq"}}
SYS = {"english": "You are an expert Singapore primary school English teacher solving PSLE English Paper 2 multiple-choice questions."}
ASK = "Think step by step, briefly, then end with a final line exactly: ANSWER: <option number 1-4>."


def jl(p):
    p = Path(p)
    return [json.loads(l) for l in open(p) if l.strip()] if p.exists() else []


def pick(raw):
    m = re.findall(r"ANSWER:\s*\(?([1-4A-Da-d])\)?", raw or "")
    if not m:
        return None
    x = m[-1].upper()
    return str("ABCD".index(x) + 1) if x in "ABCD" else x


def strip_num(o):
    return re.sub(r"^\s*\(?[1-4A-Da-d][).]\s*", "", o or "").strip()


def qtext(q):
    opts = "\n".join(f"({i}) {o}" for i, o in enumerate(q["options"], 1))
    return "Question:\n" + q["text"] + "\n\nOptions:\n" + opts


def work(subject):
    return TMP / "blind3" / subject


def pack(a):
    rng = random.Random(21)
    dis, agree = [], []
    for y in range(2018, 2027):
        base = PP / a.subject / str(y)
        st = {t["id"]: t.get("st") for t in jl(base / "tags72.jsonl")}
        bl = {b["id"]: b for b in jl(BLIND / f"{a.subject}-{y}.jsonl")}
        for q in jl(base / "merged.jsonl"):
            b = bl.get(q["id"])
            opts = [strip_num(o) for o in q.get("options") or []]
            if q.get("format") != "mcq" or len(opts) != 4 or not all(opts) or not b or not b.get("key"):
                continue
            if st.get(q["id"]) not in SINGLE[a.subject] or q.get("figures"):
                continue
            it = {"id": q["id"], "y": y, "text": q["text"], "options": opts, "key": str(b["key"]), "pick1": b.get("pick")}
            if b.get("agree") is True:
                agree.append({**it, "calib": True})
            elif b.get("pick"):
                dis.append({**it, "calib": False})
    calib = rng.sample(agree, min(a.calib, len(agree)))
    w = work(a.subject)
    w.mkdir(parents=True, exist_ok=True)
    with open(w / "items.jsonl", "w") as f:
        for it in dis + calib:
            f.write(json.dumps(it, ensure_ascii=False) + "\n")
    print(f"{len(dis)} disagreements + {len(calib)} calibration items -> {w / 'items.jsonl'}")
    if a.push:
        dst = f"{SERVER_BASE}/{a.subject}"
        subprocess.run(["ssh", SERVER, f"mkdir -p {dst}"], check=True)
        subprocess.run(["scp", "-q", str(w / "items.jsonl"), f"{SERVER}:{dst}/items.jsonl"], check=True)
        subprocess.run(["scp", "-q", str(Path(__file__).resolve()), f"{SERVER}:{SERVER_BASE}/blind3.py"], check=True)
        print("pushed to", dst)


def run(a):
    w = Path(SERVER_BASE) / a.subject
    out = w / "results.jsonl"
    done = {r["id"] for r in jl(out) if r.get("pick") is not None}
    todo = [q for q in jl(w / "items.jsonl") if q["id"] not in done]
    print(len(todo), "to solve", flush=True)
    if not todo:
        return
    from vllm import LLM, SamplingParams
    llm = LLM(model=os.environ.get("PP_LLM", "Qwen/Qwen2.5-72B-Instruct-AWQ"), tensor_parallel_size=int(os.environ.get("PP_TP", "4")),
              gpu_memory_utilization=0.9, max_model_len=8192, enable_prefix_caching=True, max_num_seqs=48,
              enforce_eager=bool(os.environ.get("PP_EAGER")))
    sp = SamplingParams(temperature=0, max_tokens=1000)
    sysmsg = SYS[a.subject] + " " + ASK
    for i in range(0, len(todo), 128):
        ch = todo[i:i + 128]
        res = llm.chat([[{"role": "system", "content": sysmsg}, {"role": "user", "content": qtext(q)}] for q in ch], sp, use_tqdm=False)
        with open(out, "a") as f:
            for q, o in zip(ch, res):
                f.write(json.dumps({"id": q["id"], "pick": pick(o.outputs[0].text)}) + "\n")
        print("done", i + len(ch), "/", len(todo), flush=True)


def report(a):
    w = work(a.subject)
    if a.pull:
        subprocess.run(["scp", "-q", f"{SERVER}:{SERVER_BASE}/{a.subject}/results.jsonl", str(w / "results.jsonl")], check=True)
    p3 = {r["id"]: r.get("pick") for r in jl(w / "results.jsonl")}
    items = jl(w / "items.jsonl")
    cal = [q for q in items if q["calib"] and q["id"] in p3]
    ok = sum(p3[q["id"]] == q["key"] for q in cal)
    print(f"calibration: third model agrees with key+blind on {ok}/{len(cal)} ({100 * ok / max(1, len(cal)):.1f}%)")
    C = collections.Counter()
    by = collections.defaultdict(list)
    for q in items:
        if q["calib"] or q["id"] not in p3:
            continue
        t = p3[q["id"]]
        k = "key stands (2 of 3)" if t == q["key"] else "blind wins: key suspect" if t == q["pick1"] else "no majority" if t else "unparsed"
        C[k] += 1
        by[q["y"]].append({"id": q["id"], "key": q["key"], "pick1": q["pick1"], "pick3": t, "agree3": t == q["key"]})
    for k, n in C.most_common():
        print(f"  {k}: {n}")
    if a.write:
        (BLIND / "third").mkdir(exist_ok=True)
        for y, L in by.items():
            with open(BLIND / "third" / f"{a.subject}-{y}.jsonl", "w") as f:
                for r in L:
                    f.write(json.dumps(r) + "\n")
        print("wrote", BLIND / "third")


def selftest():
    assert pick("so ANSWER: 3") == "3" and pick("ANSWER: (B)") == "2" and pick("no answer") is None
    assert strip_num("(2) went") == "went" and strip_num("B. gone") == "gone"
    assert qtext({"text": "He ___ home.", "options": ["go", "goes", "going", "gone"]}).endswith("(4) gone")
    print("blind3 selftest ok")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("cmd", choices=("pack", "run", "report", "selftest"))
    p.add_argument("--subject", default="english")
    p.add_argument("--calib", type=int, default=300)
    p.add_argument("--push", action="store_true")
    p.add_argument("--pull", action="store_true")
    p.add_argument("--write", action="store_true", help="report: write BLIND/third/ for load_pp (after the owner has seen it)")
    a = p.parse_args()
    {"pack": pack, "run": run, "report": report, "selftest": lambda _a: selftest()}[a.cmd](a)
