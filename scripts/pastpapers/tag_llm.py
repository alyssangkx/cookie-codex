"""Tag merged past-paper questions with a local text LLM (vLLM, Qwen2.5-72B-Instruct-AWQ), no Claude tokens.

  tag_llm.py --sets science:2024,chinese:2026        -> PP_ROOT/<subject>/<year>/tags72.jsonl (resumes by id)
  tag_llm.py compare <tags72.jsonl> [<gold.jsonl>]    -> sub-topic agreement with the checked key (exit 3 below the gate)
  tag_llm.py selftest

Record: {id, st, pat, method, difficulty 1-3, ans_check, conf, flags}. st/pat must be ids from the subject's taxonomy
(packet.taxonomy); an invalid answer is asked again once, then kept with st null and flag "invalid".
Gold key (outside the repo): PP_ROOT/gold/science-2024-gold.jsonl, {id, st, ok: [acceptable ids], use: example|eval, pat?},
from a blind Sonnet tagging of 110 Science 2024 questions, adjudicated against the Haiku step B and first 72B tags.
"example" rows are the few-shot examples (Science only); "eval" rows are the gate."""
import argparse, json, os, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from vlm_read import parse  # noqa: E402  (JSON with LaTeX repair)
from packet import taxonomy  # noqa: E402

PP = Path(os.environ.get("PP_ROOT", "/data/alvin/tmp/cookie-codex/pastpapers"))
MODEL = os.environ.get("PP_MODEL", "Qwen/Qwen2.5-72B-Instruct-AWQ")
GATE = 0.8  # owner's gate: the full run starts only if at least 80% of the gold eval rows get an acceptable sub-topic
GOLD = PP / "gold" / "science-2024-gold.jsonl"
SYSTEM = ("You are an experienced Singapore primary school {subject} teacher who classifies PSLE prelim exam questions "
          "against the P6 syllabus. Reply with one JSON object only, no code fences.")
TASK = """{tax}
Classify the question below.
- st: exactly one sub-topic id from the list above: the idea the marks reward, i.e. what the correct answer has to know
  or explain. The setting is not the topic: a garden question whose answer is about evaporation is a water question,
  not a plants question. An experiment question (fair test, variable, aim, conclusion) gets the concept it investigates.
- pat: one question-type pattern id from the list, or null if none fits.
- method: the method or skill a strong pupil uses, at most 8 words (e.g. "model drawing, before-after", "claim-evidence-reasoning", "subject-verb agreement", "inference from context").
- difficulty: 1 easy, 2 medium, 3 hard, for a P6 pupil.
- ans_check: true if the given answer fits the question, false if it does not, null if no answer is given.
- conf: 0 to 1, your confidence in st.
{examples}{question}
JSON: {{"st": "<id>", "pat": "<id or null>", "method": "...", "difficulty": 1, "ans_check": null, "conf": 0.0}}"""


def show(q):
    head = f"Question ({q.get('format') or '?'}, {q.get('marks') if q.get('marks') is not None else '?'} marks"
    head += f", section: {q['section']}" if q.get("section") else ""
    opts = "\nOptions: " + " | ".join(q["options"]) if q.get("options") else ""
    ans = f"\nGiven answer: {q['answer'][:400]}" if q.get("answer") else "\nGiven answer: none"
    return f"{head}):\n{(q.get('text') or '')[:1500]}{opts}{ans}"


def examples(subject):
    """-> prompt text: the gold "example" rows (Science only), each with its question."""
    merged = PP / "science" / "2024" / "merged.jsonl"
    if subject != "science" or not GOLD.exists() or not merged.exists(): return ""
    rows = [g for g in map(json.loads, open(GOLD)) if g.get("use") == "example"][:15]  # ponytail: 15 keeps prompts < 16k
    want = {g["id"] for g in rows}
    text = {r["id"]: r for r in map(json.loads, open(merged)) if r.get("id") in want and r.get("text")}
    # each example carries a real pattern: examples all showing null made the 72B leave pat null on 85% of Science
    out = [f"Example\n{show(text[g['id']])}\nJSON: " + json.dumps({"st": g["st"], "pat": g.get("pat"), "method": "...", "difficulty": 2,
                                                                  "ans_check": None, "conf": 0.9})
           for g in rows if g["id"] in text]
    return "\n\n".join(out) + "\n\nNow the real question.\n" if out else ""


def check(rec, subs, pats):
    """-> problem text, or None if the record is valid."""
    if not isinstance(rec, dict): return "not a JSON object"
    if not isinstance(rec.get("st"), str): return "st must be one id string"
    if rec.get("pat") is not None and not isinstance(rec.get("pat"), str): return "pat must be one id string or null"
    if rec.get("st") not in subs: return f"st {rec.get('st')!r} is not a sub-topic id from the list"
    if rec.get("pat") not in pats and rec.get("pat") is not None: return f"pat {rec.get('pat')!r} is not a pattern id from the list (use null)"
    if rec.get("difficulty") not in (1, 2, 3): return "difficulty must be 1, 2 or 3"
    if not isinstance(rec.get("conf"), (int, float)): return "conf must be a number"
    return None


def run(sets, batch, tp):
    from vllm import LLM, SamplingParams
    llm = LLM(model=MODEL, tensor_parallel_size=tp, gpu_memory_utilization=0.9, max_model_len=16384,
              enable_prefix_caching=True, max_num_seqs=64)
    sp = SamplingParams(temperature=0, max_tokens=200)
    for subject, year in sets:
        base = PP / subject / str(year)
        tax, subs, pats = taxonomy(subject, outcomes=True)
        ex = examples(subject)
        out = base / "tags72.jsonl"
        done = {json.loads(l)["id"] for l in open(out)} if out.exists() else set()
        todo = [q for q in map(json.loads, open(base / "merged.jsonl")) if q["id"] not in done]
        print(f"{subject} {year}: {len(todo)} to tag", flush=True)
        sysmsg = {"role": "system", "content": SYSTEM.format(subject=subject)}
        for i in range(0, len(todo), batch):
            chunk = todo[i:i + batch]
            msgs = [[sysmsg, {"role": "user", "content": TASK.format(tax=tax, examples=ex, question=show(q))}] for q in chunk]
            first = [parse(o.outputs[0].text) for o in llm.chat(msgs, sp, use_tqdm=False)]
            again = [k for k, r in enumerate(first) if check(r, subs, pats)]
            if again:  # ask once more, saying what was wrong
                retry = [msgs[k] + [{"role": "assistant", "content": json.dumps(first[k]) if isinstance(first[k], dict) else "?"},
                                    {"role": "user", "content": f"Invalid: {check(first[k], subs, pats)}. Reply with corrected JSON only."}]
                         for k in again]
                for k, o in zip(again, llm.chat(retry, sp, use_tqdm=False)): first[k] = parse(o.outputs[0].text)
            with open(out, "a") as f:
                for q, r in zip(chunk, first):
                    bad = check(r, subs, pats)
                    r = r if isinstance(r, dict) else {}
                    rec = {"id": q["id"], **{k: r.get(k) for k in ("st", "pat", "method", "difficulty", "ans_check", "conf")},
                           "flags": ["invalid"] if bad else []}
                    if bad:
                        rec["st"] = rec["st"] if isinstance(rec["st"], str) and rec["st"] in subs else None
                        rec["pat"] = rec["pat"] if isinstance(rec["pat"], str) and rec["pat"] in pats else None
                    f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            print(f"done {i + len(chunk)}/{len(todo)}", flush=True)


def score(tags, gold):
    """-> (eval rows scored, acceptable, exact, misses [(id, gold st, tag st)])."""
    g = [r for r in gold if r["use"] == "eval" and r["id"] in tags]
    miss = [(r["id"], r["st"], tags[r["id"]]) for r in g if tags[r["id"]] not in r["ok"] + [r["st"]]]
    return len(g), len(g) - len(miss), sum(tags[r["id"]] == r["st"] for r in g), miss


def compare(tags, gold=GOLD):
    rows = [json.loads(l) for l in open(tags)]
    t = {r["id"]: r["st"] for r in rows}
    n, ok, exact, miss = score(t, [json.loads(l) for l in open(gold)])
    nullpat = sum(r.get("pat") is None for r in rows)  # no gold patterns: a null-rate check stands in (first run: 5 of 1229)
    print(f"gold eval rows {n} | acceptable sub-topic {ok}/{n} = {100 * ok / max(n, 1):.0f}% | exact {exact}/{n} | gate {GATE:.0%}"
          f" | pat null {nullpat}/{len(rows)}")
    for i, want, got in miss: print(f"{i} | gold {want} | 72b {got}")
    return n >= 80 and ok >= GATE * n and nullpat <= 0.1 * len(rows)


def selftest():
    subs, pats = {"s1"}, {"p1"}
    assert check({"st": "s1", "pat": None, "difficulty": 2, "conf": 0.8}, subs, pats) is None
    assert "sub-topic" in check({"st": "x", "pat": None, "difficulty": 2, "conf": 1}, subs, pats)
    assert "pattern" in check({"st": "s1", "pat": "x", "difficulty": 2, "conf": 1}, subs, pats)
    assert check("text", subs, pats) == "not a JSON object"
    assert check({"st": ["s1", "s2"], "pat": None, "difficulty": 2, "conf": 1}, subs, pats) == "st must be one id string"
    q = {"format": "mcq", "marks": 2, "section": "Booklet A", "text": "Which is a mammal?", "options": ["(1) a", "(2) b"], "answer": "2"}
    p = TASK.format(tax=taxonomy("science", outcomes=True)[0], examples="", question=show(q))
    assert "Options: (1) a | (2) b" in p and "Given answer: 2" in p and "sci-pat-" in p and "    - " in p
    gold = [{"id": "a", "st": "s1", "ok": ["s1", "s2"], "use": "eval"}, {"id": "b", "st": "s1", "ok": ["s1"], "use": "eval"},
            {"id": "c", "st": "s3", "ok": ["s3"], "use": "example"}]
    assert score({"a": "s2", "b": "s2", "c": "x"}, gold) == (2, 1, 0, [("b", "s1", "s2")])
    assert score({"a": "s1", "b": "s1"}, [{"id": "a", "st": "s1", "ok": ["s2"], "use": "eval"}, gold[1]])[1] == 2
    print("tag_llm selftest ok")


if __name__ == "__main__":
    if sys.argv[1:2] == ["selftest"]: selftest(); sys.exit()
    if sys.argv[1:2] == ["compare"]: sys.exit(0 if compare(*sys.argv[2:4]) else 3)
    ap = argparse.ArgumentParser()
    ap.add_argument("--sets", required=True, help="subject:year pairs in order, e.g. science:2024,chinese:2026")
    ap.add_argument("--batch", type=int, default=256)
    ap.add_argument("--tp", type=int, default=int(os.environ.get("PP_TP", "4")))
    a = ap.parse_args()
    run([(x.split(":")[0], int(x.split(":")[1])) for x in a.sets.split(",")], a.batch, a.tp)
