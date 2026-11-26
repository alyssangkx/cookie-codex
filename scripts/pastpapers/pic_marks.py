#!/usr/bin/env python3
"""Scan every live picture for answer marks and foreign text on the server (GPU), queue 39 (owner, 26 Nov 2026: queue
the next server items). The owner's rule (25 Nov 2026): a standalone question whose picture shows its answer is held;
a passage question goes to review. The picture run found such marks only in the questions it explained; this looks at
all of them, plus pictures that carry text from another question.

  pic_marks.py ITEMS.jsonl    (PP_ROOT = folder holding the copied pictures; PP_VLM / PP_TP pick the model)
  pic_marks.py selftest
ITEMS rows: {id (pp id), subject, file (path under PP_ROOT), gate: true for a known answer-marked picture}.
Writes PP_ROOT/marks39/<id>.json {id, raw, read}; read = {marks, marks_what, foreign_text, foreign_what}. Prints counts.
On dev, `flags(read)` decides; the gate (the 22 pictures held on 25 Nov) must be found before any hold is applied."""
import json
import os
import re
import sys
from pathlib import Path

PP = Path(os.environ.get("PP_ROOT", "/data/alvin/cookie/pastpapers_full"))
OUT = PP / "marks39"
PROMPT = ("This picture comes from a printed Primary 6 {subject} exam question. Look only for things a student or "
          "teacher ADDED by hand, not printed parts of the question (printed ticks, crosses or circles in a table, "
          "printed arrows and labels are part of the question). Reply with JSON only: "
          "{{\"marks\": <true if there is handwriting, a hand-drawn tick, cross, circle, underline or arrow, a crossed-out "
          "option, or a written answer or working on the picture>, \"marks_what\": \"<what and where, short; empty if "
          "none>\", \"foreign_text\": <true if the picture also holds printed text from a DIFFERENT numbered question, "
          "e.g. another question's number, its sentence or its answer options>, \"foreign_what\": \"<short; empty if "
          "none>\"}}")


def parse(text):
    m = re.search(r"\{.*\}", text or "", re.S)
    try:
        return json.loads(m.group(0)) if m else None
    except Exception:
        return None


def flags(read):
    """(marks, foreign) from a parsed read; an unreadable reply flags nothing (it is reported as unread)."""
    if not isinstance(read, dict):
        return False, False
    return read.get("marks") is True, read.get("foreign_text") is True


def main(items_file):
    rows = [json.loads(l) for l in open(items_file) if l.strip()]
    OUT.mkdir(parents=True, exist_ok=True)
    todo = [r for r in rows if (PP / r["file"]).exists() and not (OUT / f"{r['id']}.json").exists()]
    print(len(todo), "pictures to read", flush=True)
    if not todo:
        return
    from vllm import LLM, SamplingParams
    llm = LLM(model=os.environ.get("PP_VLM", "Qwen/Qwen2.5-VL-72B-Instruct-AWQ"), tensor_parallel_size=int(os.environ.get("PP_TP", "4")),
              gpu_memory_utilization=0.9, max_model_len=8192, max_num_seqs=16, limit_mm_per_prompt={"image": 1},
              mm_processor_kwargs={"max_pixels": 1_600_000}, allowed_local_media_path=str(PP), enforce_eager=bool(os.environ.get("PP_EAGER")))
    sp = SamplingParams(temperature=0, max_tokens=300)
    nm = nf = 0
    subj = {"science": "Science", "maths": "Mathematics", "chinese": "Chinese"}
    for i in range(0, len(todo), 32):
        ch = todo[i:i + 32]
        msgs = [[{"role": "user", "content": [{"type": "image_url", "image_url": {"url": f"file://{PP / r['file']}"}},
                                              {"type": "text", "text": PROMPT.format(subject=subj.get(r["subject"], r["subject"]))}]}] for r in ch]
        for r, out in zip(ch, llm.chat(msgs, sp, use_tqdm=False)):
            raw = out.outputs[0].text
            read = parse(raw)
            m, f = flags(read)
            nm += m; nf += f
            (OUT / f"{r['id']}.json").write_text(json.dumps({"id": r["id"], "raw": raw, "read": read}))
        print(f"{min(i + 32, len(todo))}/{len(todo)} read, {nm} with marks, {nf} with foreign text", flush=True)


if __name__ == "__main__":
    if sys.argv[1:2] == ["selftest"]:
        assert flags(parse('```json\n{"marks": true, "marks_what": "tick on (2)", "foreign_text": false}\n```')) == (True, False)
        assert flags(parse('{"marks": false, "foreign_text": true, "foreign_what": "Q13 options"}')) == (False, True)
        assert flags(parse("no json here")) == (False, False) and flags(parse('{"marks": "yes"}')) == (False, False)
        print("pic_marks selftest ok")
        sys.exit()
    main(sys.argv[1])
