#!/usr/bin/env python3
"""Re-read statement questions on the server (GPU): MCQs that list statements A-D and give combinations as the options
("(1) B and D only"), which the first read took as four lettered options (load_pp.py reject options-are-statements).

  stmt_reread.py ITEMS.jsonl        (PP_ROOT = the pastpapers folder on the server; PP_VLM / PP_TP pick the model)
  stmt_reread.py selftest
ITEMS rows: {id, subject, year, qno, pages: [...], text, options: [the 4 lettered statements as first read]}.
The model sees the question's pages plus the next page (the options often run over) and returns the intro, statements
A-D and the 4 options. A read is usable only when it passes check(): 4 statements, 4 options that name only the letters
A-D, and at least 3 of the statements matching the first read (an independent read of the same text). Writes
PP_ROOT/<subject>/<year>/stmtreread/<id>.json {id, raw, read, ok, why}. Prints counts only."""
import json
import os
import re
import sys
from difflib import SequenceMatcher
from pathlib import Path

PP = Path(os.environ.get("PP_ROOT", "/data/alvin/cookie/pastpapers_full"))
PROMPT = ("These are pages from a Primary 6 Science exam paper. Find question {qno}; its text begins: \"{start}\". "
          "It lists statements labelled A, B, C and D, then four answer options (1) to (4), each a combination of those "
          "letters. Copy the text exactly and reply with JSON only: "
          "{{\"intro\": \"<the question text before statement A, including the question sentence>\", "
          "\"statements\": {{\"A\": \"...\", \"B\": \"...\", \"C\": \"...\", \"D\": \"...\"}}, "
          "\"options\": [\"<option (1) without the number>\", \"<(2)>\", \"<(3)>\", \"<(4)>\"]}}. "
          "If question {qno} is not of this form, reply {{\"form\": \"other\"}}.")
LABEL = re.compile(r"^\s*\(?[A-D][.)]?\s+")
COMBO = re.compile(r"^(?:[A-D]|and|or|only|,|\s)+$")


def parse(text):
    m = re.search(r"\{.*\}", text or "", re.S)
    try:
        return json.loads(m.group(0)) if m else None
    except Exception:
        return None


def check(read, first):
    """(ok, why). first = the 4 lettered statements of the first read."""
    if not isinstance(read, dict) or read.get("form") == "other":
        return False, "not-statement-form"
    st, op = read.get("statements") or {}, read.get("options") or []
    if sorted(st) != ["A", "B", "C", "D"] or not all(isinstance(v, str) and v.strip() for v in st.values()):
        return False, "statements-not-A-D"
    if len(op) != 4 or len({o.strip() for o in op}) != 4:
        return False, "options-not-4"
    if not all(isinstance(o, str) and COMBO.fullmatch(re.sub(r"^\(?\d\)?\s*", "", o.strip())) for o in op):
        return False, "options-not-combinations"
    if not str(read.get("intro") or "").strip():
        return False, "no-intro"
    same = sum(SequenceMatcher(None, LABEL.sub("", f).lower(), st[k].lower()).ratio() >= 0.8 for k, f in zip("ABCD", first))
    if same < 3:
        return False, f"statements-differ-from-first-read ({same}/4)"
    return True, None


def main(items_file):
    rows = [json.loads(l) for l in open(items_file) if l.strip()]
    todo = []
    for r in rows:
        od = PP / r["subject"] / str(r["year"]) / "stmtreread"
        pdir = PP / r["subject"] / str(r["year"]) / "pages"
        pages = sorted(set(r["pages"]) | {max(r["pages"]) + 1})
        imgs = [pdir / f"p{p:04d}.jpg" for p in pages if (pdir / f"p{p:04d}.jpg").exists()][:3]
        if imgs and not (od / f"{r['id']}.json").exists():
            od.mkdir(parents=True, exist_ok=True)
            todo.append((r, imgs, od))
    print(len(todo), "questions to read", flush=True)
    if not todo:
        return
    from vllm import LLM, SamplingParams
    llm = LLM(model=os.environ.get("PP_VLM", "Qwen/Qwen2.5-VL-72B-Instruct-AWQ"), tensor_parallel_size=int(os.environ.get("PP_TP", "4")),
              gpu_memory_utilization=0.9, max_model_len=16384, max_num_seqs=8, limit_mm_per_prompt={"image": 3},
              mm_processor_kwargs={"max_pixels": 2_000_000}, allowed_local_media_path=str(PP), enforce_eager=bool(os.environ.get("PP_EAGER")))
    sp = SamplingParams(temperature=0, max_tokens=1200)
    ok = 0
    for i in range(0, len(todo), 16):
        ch = todo[i:i + 16]
        msgs = [[{"role": "user", "content": [{"type": "image_url", "image_url": {"url": f"file://{p}"}} for p in imgs]
                  + [{"type": "text", "text": PROMPT.format(qno=r["qno"], start=r["text"][:120].replace('"', "'"))}]}] for r, imgs, _ in ch]
        for (r, _, od), out in zip(ch, llm.chat(msgs, sp, use_tqdm=False)):
            raw = out.outputs[0].text
            read = parse(raw)
            good, why = check(read, r["options"])
            ok += good
            (od / f"{r['id']}.json").write_text(json.dumps({"id": r["id"], "raw": raw, "read": read, "ok": good, "why": why}))
        print(f"{min(i + 16, len(todo))}/{len(todo)} read, {ok} usable", flush=True)


if __name__ == "__main__":
    if sys.argv[1:2] == ["selftest"]:
        first = ["A. Object 1 is a magnet.", "B. Object 2 is a magnet.", "C. Objects 1 and 2 can be made of iron.", "D. Neither is a magnet."]
        good = {"intro": "Which can be concluded?", "statements": {"A": "Object 1 is a magnet.", "B": "Object 2 is a magnet.",
                "C": "Objects 1 and 2 can be made of iron.", "D": "Neither is a magnet."}, "options": ["B and D only", "B and C only", "A and D only", "A, B and C only"]}
        assert check(good, first) == (True, None)
        assert check(parse("```json\n" + json.dumps(good) + "\n```"), first) == (True, None)
        assert check({"form": "other"}, first)[1] == "not-statement-form"
        assert check(dict(good, options=["B and D only", "B and C only", "A and D only", "Object 1"]), first)[1] == "options-not-combinations"
        assert check(dict(good, options=["(1) B and D only", "(2) B and C only", "(3) A and D only", "(4) A only"]), first) == (True, None)
        assert check(dict(good, statements={"A": "x", "B": "y", "C": "z", "D": "Neither is a magnet."}), first)[1].startswith("statements-differ")
        assert check(dict(good, options=good["options"][:3]), first)[1] == "options-not-4"
        print("stmt_reread selftest ok")
        sys.exit()
    main(sys.argv[1])
