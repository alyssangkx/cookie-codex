"""Tag merged past-paper questions with a local text LLM (vLLM, Qwen2.5-72B-Instruct-AWQ), no Claude tokens.

  tag_llm.py --sets science:2024,chinese:2026        -> PP_ROOT/<subject>/<year>/tags72.jsonl (resumes by id)
  tag_llm.py compare <tags72.jsonl> <stepB.jsonl>     -> sub-topic and pattern agreement on shared ids
  tag_llm.py selftest

Record: {id, st, pat, method, difficulty 1-3, ans_check, conf, flags}. st/pat must be ids from the subject's taxonomy
(packet.taxonomy); an invalid answer is asked again once, then kept with st null and flag "invalid".
Few-shot examples come from the Science 2024 Haiku step B file at run time (outside the repo), for Science only."""
import argparse, json, os, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from vlm_read import parse  # noqa: E402  (JSON with LaTeX repair)
from packet import taxonomy  # noqa: E402

PP = Path(os.environ.get("PP_ROOT", "/data/alvin/tmp/cookie-codex/pastpapers"))
MODEL = os.environ.get("PP_MODEL", "Qwen/Qwen2.5-72B-Instruct-AWQ")
GATE = 0.8  # owner's gate: the full run starts only if sub-topic agreement with Haiku step B is at least 80%
HAIKU = PP / "stepB-2024" / "science-2024-stepB.jsonl"
SYSTEM = ("You are an experienced Singapore primary school {subject} teacher who classifies PSLE prelim exam questions "
          "against the P6 syllabus. Reply with one JSON object only, no code fences.")
TASK = """{tax}
Classify the question below.
- st: exactly one sub-topic id from the list above: the main thing the question tests.
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
    """-> (prompt text, ids used). 3 Haiku-tagged Science 2024 questions with different sub-topics."""
    merged = PP / "science" / "2024" / "merged.jsonl"
    if subject != "science" or not HAIKU.exists() or not merged.exists(): return "", set()
    text = {r["id"]: r for r in map(json.loads, open(merged)) if r.get("text")}
    out, ids, seen = [], set(), set()
    for h in map(json.loads, open(HAIKU)):
        q = text.get(h.get("id"))
        if not q or h.get("subtopic") in seen or len(out) == 3: continue
        seen.add(h["subtopic"]); ids.add(h["id"])
        out.append(f"Example\n{show(q)}\nJSON: " + json.dumps({"st": h["subtopic"], "pat": h.get("pattern"), "method": "...",
                                                             "difficulty": 2, "ans_check": None, "conf": 0.9}))
    return "\n\n".join(out) + "\n\nNow the real question.\n", ids


def check(rec, subs, pats):
    """-> problem text, or None if the record is valid."""
    if not isinstance(rec, dict): return "not a JSON object"
    if rec.get("st") not in subs: return f"st {rec.get('st')!r} is not a sub-topic id from the list"
    if rec.get("pat") not in pats and rec.get("pat") is not None: return f"pat {rec.get('pat')!r} is not a pattern id from the list (use null)"
    if rec.get("difficulty") not in (1, 2, 3): return "difficulty must be 1, 2 or 3"
    if not isinstance(rec.get("conf"), (int, float)): return "conf must be a number"
    return None


def run(sets, batch, tp):
    from vllm import LLM, SamplingParams
    llm = LLM(model=MODEL, tensor_parallel_size=tp, gpu_memory_utilization=0.9, max_model_len=12288,
              enable_prefix_caching=True, max_num_seqs=64)
    sp = SamplingParams(temperature=0, max_tokens=200)
    for subject, year in sets:
        base = PP / subject / str(year)
        tax, subs, pats = taxonomy(subject)
        ex, _ = examples(subject)
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
                    if bad: rec["st"] = rec["st"] if rec["st"] in subs else None
                    f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            print(f"done {i + len(chunk)}/{len(todo)}", flush=True)


def compare(tags, haiku):
    _, used = examples("science")
    t = {r["id"]: r for r in map(json.loads, open(tags))}
    h = {r["id"]: r for r in map(json.loads, open(haiku)) if r.get("id") in t and r["id"] not in used}
    st = sum(t[i]["st"] == r.get("subtopic") for i, r in h.items())
    pat = [(t[i]["pat"], r.get("pattern")) for i, r in h.items() if r.get("pattern")]
    print(f"shared ids {len(h)} (3 example ids left out) | sub-topic agree {st}/{len(h)} = {100 * st / max(len(h), 1):.0f}% | "
          f"pattern agree {sum(a == b for a, b in pat)}/{len(pat)}")
    for i, r in [(i, r) for i, r in h.items() if t[i]["st"] != r.get("subtopic")][:30]:
        print(f"{i} | haiku {r.get('subtopic')} | 72b {t[i]['st']} (conf {t[i].get('conf')})")
    return st >= GATE * len(h) and len(h) >= 100


def selftest():
    subs, pats = {"s1"}, {"p1"}
    assert check({"st": "s1", "pat": None, "difficulty": 2, "conf": 0.8}, subs, pats) is None
    assert "sub-topic" in check({"st": "x", "pat": None, "difficulty": 2, "conf": 1}, subs, pats)
    assert "pattern" in check({"st": "s1", "pat": "x", "difficulty": 2, "conf": 1}, subs, pats)
    assert check("text", subs, pats) == "not a JSON object"
    q = {"format": "mcq", "marks": 2, "section": "Booklet A", "text": "Which is a mammal?", "options": ["(1) a", "(2) b"], "answer": "2"}
    p = TASK.format(tax=taxonomy("science")[0], examples="", question=show(q))
    assert "Options: (1) a | (2) b" in p and "Given answer: 2" in p and "sci-pat-" in p
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
