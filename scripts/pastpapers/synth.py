#!/usr/bin/env python3
"""Synthesis & Transformation (English Paper 2 Booklet B; owner, 24 Nov 2026: typed answers checked against an answer set).
Step 1: the server reads each question again from its exam page, because the first read lost the lead-in line the child
completes ("However ________, I still did not go to the party."). A question is kept only when the printed answer fits
that line (check), which also drops answers that were attached to the wrong question.

  synth.py pack                 dev: items.jsonl (questions tagged S&T whose key is a sentence) -> /data/alvin/tmp/cookie-codex/synth
  synth.py run ITEMS            server (GPU; PP_ROOT, PP_VLM, PP_TP): read.jsonl, resumable
  synth.py check [--sample N]   dev: checked.jsonl {id, sentences, scaffold, answer, ok, why}; prints counts (and N kept ones)
  synth.py selftest
A scaffold writes each blank as "____" and keeps the given words exactly: "However ____, I still did not go to the party.",
"____ unless ____." Past-paper text stays off the repo and the site until the owner's review."""
import json
import os
import random
import re
import sys
from pathlib import Path

TMP = Path("/data/alvin/tmp/cookie-codex")
DEV_PP = TMP / "pastpapers"
WORK = Path(os.environ.get("PP_WORK", str(TMP / "synth")))
PROMPT = ("This is a page from a Singapore Primary 6 English exam paper (Synthesis and Transformation). Find question {qno}. "
          "Its given sentence(s) begin: \"{start}\". Below the given sentence(s) there is a line for the answer that already "
          "prints some word(s) (for example \"However\" at the start, or \"unless\" in the middle) with blank lines to fill. "
          "Copy exactly. Reply with JSON only: {{\"sentences\": \"<the given sentence(s), as printed>\", "
          "\"scaffold\": \"<the answer line, every blank written as ____, the printed words kept exactly>\"}}. "
          "If question {qno} is not on this page, reply {{\"none\": true}}.")


def jl(p):
    p = Path(p)
    return [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()] if p.exists() else []


def parse(text):
    m = re.search(r"\{.*\}", text or "", re.S)
    try:
        return json.loads(m.group(0)) if m else None
    except Exception:
        return None


def norm(s):
    """For matching an answer to a scaffold: lower case, straight quotes, single spaces."""
    s = (s or "").replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"').lower()
    return re.sub(r"\s+", " ", s).strip()


def fits(answer, scaffold):
    """The printed answer fills the scaffold: its given words appear in order with something in every blank."""
    parts = [p for p in re.split(r"_{2,}", norm(scaffold))]
    if len(parts) < 2:
        return False
    pat = "".join((re.escape(p.strip()) if p.strip() else "") + (r"\s*(.+?)\s*" if i < len(parts) - 1 else "")
                  for i, p in enumerate(parts))
    a = norm(answer).rstrip(".!? ")
    pat = pat.rstrip(r"\.\!\? ").rstrip("\\")
    return bool(re.fullmatch(r"\s*" + pat + r"[.!?]?\s*", a + ".") or re.fullmatch(r"\s*" + pat + r"\s*", a))


def pack():
    WORK.mkdir(parents=True, exist_ok=True)
    out = []
    for y in range(2018, 2027):
        base = DEV_PP / "english" / str(y)
        tags = {t["id"]: t for t in jl(base / "tags72.jsonl")}
        for q in jl(base / "merged.jsonl"):
            st = (tags.get(q["id"]) or {}).get("st")
            if not (st == "eng-synthesis" or re.search(r"synthesis|transformation", str(q.get("section") or ""), re.I)):
                continue
            a, t = str(q.get("answer") or ""), str(q.get("text") or "")
            if len(a.split()) >= 5 and len(t.split()) >= 4 and q.get("pages"):
                start = re.sub(r"^.*?(?:given sentence\(s\)\.|provided\.)\s*", "", t, flags=re.S)[:110]
                out.append({"id": q["id"], "year": y, "qno": q.get("qno"), "pages": sorted(q["pages"])[:2], "start": start,
                            "answer": a, "text": t})
    (WORK / "items.jsonl").write_text("".join(json.dumps(x, ensure_ascii=False) + "\n" for x in out))
    print(f"{len(out)} questions -> {WORK / 'items.jsonl'}")


def run(items_file):
    from PIL import Image
    items_file = Path(items_file).resolve()
    pp = Path(os.environ.get("PP_ROOT", "/data/alvin/cookie/pastpapers_full"))
    out = items_file.with_name("read.jsonl")
    done = {(r["id"], r["page"]) for r in jl(out)}
    tmp = items_file.with_name("img")
    tmp.mkdir(exist_ok=True)
    todo = []
    for r in jl(items_file):
        for p in r["pages"]:
            src = pp / "english" / str(r["year"]) / "pages" / f"p{p:04d}.jpg"
            if (r["id"], p) in done or not src.exists():
                continue
            dst = tmp / f"{r['year']}-p{p:04d}.jpg"
            if not dst.exists():
                im = Image.open(src).convert("L")
                im.thumbnail((1400, 1960))
                im.save(dst, quality=85)
            todo.append((r, p, dst))
    print(len(todo), "page reads to do", flush=True)
    if not todo:
        return
    from vllm import LLM, SamplingParams
    llm = LLM(model=os.environ.get("PP_VLM", "Qwen/Qwen2.5-VL-72B-Instruct-AWQ"), tensor_parallel_size=int(os.environ.get("PP_TP", "4")),
              gpu_memory_utilization=0.9, max_model_len=8192, max_num_seqs=16, limit_mm_per_prompt={"image": 1},
              mm_processor_kwargs={"max_pixels": 2_000_000}, allowed_local_media_path=str(tmp.parent), enforce_eager=bool(os.environ.get("PP_EAGER")))
    sp = SamplingParams(temperature=0, max_tokens=500)
    with open(out, "a", encoding="utf-8") as f:
        for i in range(0, len(todo), 32):
            ch = todo[i:i + 32]
            msgs = [[{"role": "user", "content": [{"type": "image_url", "image_url": {"url": f"file://{dst}"}},
                     {"type": "text", "text": PROMPT.format(qno=r["qno"], start=r["start"].replace('"', "'"))}]}] for r, _, dst in ch]
            for (r, p, _), o in zip(ch, llm.chat(msgs, sp, use_tqdm=False)):
                f.write(json.dumps({"id": r["id"], "page": p, "raw": o.outputs[0].text}, ensure_ascii=False) + "\n")
            f.flush()
            print(f"{min(i + 32, len(todo))}/{len(todo)}", flush=True)


def check(sample=0):
    items = {r["id"]: r for r in jl(WORK / "items.jsonl")}
    best = {}
    for r in jl(WORK / "read.jsonl"):
        v = parse(r["raw"]) or {}
        if v.get("none") or not v.get("scaffold"):
            continue
        it = items.get(r["id"])
        if it and (r["id"] not in best or fits(it["answer"], v["scaffold"])):
            best[r["id"]] = v
    rows, why = [], {}
    for i, it in items.items():
        v = best.get(i)
        if not v:
            w = "not found on its pages"
        elif not re.search(r"_{2,}", v["scaffold"]):  # the same blank test as fits()
            w = "no blank in the answer line"
        elif not fits(it["answer"], v["scaffold"]):
            w = "the printed answer does not fit the answer line"
        else:
            w = None
        why[w or "kept"] = why.get(w or "kept", 0) + 1
        rows.append({"id": i, "year": it["year"], "sentences": (v or {}).get("sentences"), "scaffold": (v or {}).get("scaffold"),
                     "answer": it["answer"], "ok": w is None, "why": w})
    (WORK / "checked.jsonl").write_text("".join(json.dumps(x, ensure_ascii=False) + "\n" for x in rows))
    print(f"{len(items)} questions: " + ", ".join(f"{k} {v}" for k, v in sorted(why.items(), key=lambda kv: -kv[1])))
    for x in random.Random(5).sample([r for r in rows if r["ok"]], min(sample, sum(r["ok"] for r in rows))):
        print(f"\n  {x['sentences']}\n  {x['scaffold']}\n  -> {x['answer']}")


def selftest():
    assert fits("However hard Julia tried to persuade me, I still did not go to the party.", "However ____, I still did not go to the party.")
    assert fits("Unless everyone drinks as little as possible, we will run out of water.", "Unless ____.")
    assert fits("The librarian asked me if I had placed the book back on that shelf.", "The librarian asked me ____.")
    assert fits("We will run out of water unless everyone drinks as little as possible.", "____ unless ____.")
    assert not fits("The bird pecked at it suddenly and had it.", "However ____, I still did not go to the party.")
    assert not fits("Anything at all.", "No blank here.")
    print("synth selftest ok")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "pack":
        pack()
    elif cmd == "run":
        run(sys.argv[2])
    elif cmd == "check":
        check(int(sys.argv[sys.argv.index("--sample") + 1]) if "--sample" in sys.argv else 0)
    elif cmd == "selftest":
        selftest()
    else:
        sys.exit(__doc__)
