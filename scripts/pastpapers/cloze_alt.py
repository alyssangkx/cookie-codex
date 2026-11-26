#!/usr/bin/env python3
"""Other words that fit an English Comprehension Cloze blank (owner, 26 Nov 2026: queue on the server; Claude and
Perplexity then revalidate). A child typing a fitting word that the key does not list is marked wrong (Test Player reports
27-32: raise, implement, under, take, develop, with). Two text models propose candidates; the union goes to the owner's
outside pair, and only words both accept are added.

  cloze_alt.py propose ITEMS.jsonl     server (GPU; PP_LLM model, PP_TP, PP_TAG = qwen / llama, PP_ROOT)
  cloze_alt.py selftest
ITEMS rows: {id, seq, stem (the whole passage, the asked blank as "(n) ________"), accept: [...]}.
Writes PP_ROOT/clozealt42/<PP_TAG>/<id>.json {id, raw, words: [...]}."""
import json
import os
import re
import sys
from pathlib import Path

PP = Path(os.environ.get("PP_ROOT", "/data/alvin/cookie/pastpapers_full"))
PROMPT = ("Below is an English cloze passage from a Primary 6 (Singapore PSLE) exam. Blank ({n}) is marked ________. "
          "The answer key accepts: {acc}. List OTHER single words that fit blank ({n}) just as well: grammatically correct in "
          "the sentence AND keeping the meaning of the passage, words a careful English teacher would also mark correct. "
          "Do not list words that are only possible, awkward or change the meaning. Reply with JSON only: "
          "{{\"words\": [\"...\"]}} (an empty list if none).\n\nPassage:\n{passage}")


def words_of(raw):
    m = re.search(r"\{.*\}", raw or "", re.S)
    try:
        w = json.loads(m.group(0)).get("words", []) if m else []
    except Exception:
        return []
    out = []
    for x in w if isinstance(w, list) else []:
        x = str(x).strip().strip(".,;:!?\"'").lower()
        if re.fullmatch(r"[a-z][a-z'-]{0,24}", x) and x not in out:
            out.append(x)
    return out


def main(items_file):
    rows = [json.loads(l) for l in open(items_file) if l.strip()]
    out = PP / "clozealt42" / os.environ.get("PP_TAG", "qwen")
    out.mkdir(parents=True, exist_ok=True)
    todo = [r for r in rows if not (out / f"{r['id']}.json").exists()]
    print(len(todo), "blanks to propose", flush=True)
    if not todo:
        return
    from vllm import LLM, SamplingParams
    llm = LLM(model=os.environ.get("PP_LLM", "Qwen/Qwen2.5-72B-Instruct-AWQ"), tensor_parallel_size=int(os.environ.get("PP_TP", "4")),
              gpu_memory_utilization=0.9, max_model_len=8192, enforce_eager=bool(os.environ.get("PP_EAGER")))
    sp = SamplingParams(temperature=0, max_tokens=200)
    for i in range(0, len(todo), 32):
        ch = todo[i:i + 32]
        msgs = [[{"role": "user", "content": PROMPT.format(n=r["seq"], acc=", ".join(r["accept"]), passage=r["stem"])}] for r in ch]
        for r, o in zip(ch, llm.chat(msgs, sp, use_tqdm=False)):
            acc = {a.lower() for a in r["accept"]}
            ws = [w for w in words_of(o.outputs[0].text) if w not in acc]
            (out / f"{r['id']}.json").write_text(json.dumps({"id": r["id"], "raw": o.outputs[0].text, "words": ws}, ensure_ascii=False))
        print(f"{min(i + 32, len(todo))}/{len(todo)} done", flush=True)


if __name__ == "__main__":
    if sys.argv[1:2] == ["selftest"]:
        assert words_of('```json\n{"words": ["Raise", "voice.", "two words", ""]}\n```') == ["raise", "voice"]
        assert words_of("no json") == [] and words_of('{"words": "x"}') == []
        print("cloze_alt selftest ok")
        sys.exit()
    main(sys.argv[2])
