#!/usr/bin/env python3
"""Text-only question pictures (owner, 26 Nov 2026, "text, not pictures": past-paper text is real text; only pictures,
tables and figures stay images). Queue 44: two server models look at every live Maths and Science question picture and
say PICTURE (it holds a drawing, diagram, graph, chart, table, number line, shape or photo) or give its exact text. On
dev a picture becomes text only when BOTH models say it is text and their transcripts agree (check()).

  crop_text.py read ITEMS.jsonl     server (GPU; PP_VLM model, PP_TAG required: the output folder per model, PP_TP, PP_ROOT)
  crop_text.py selftest
ITEMS rows: {id, pp_id, file (relative to PP_ROOT)}. Writes PP_ROOT/croptext44/<PP_TAG>/<id>.json {id, model, raw}."""
import json
import os
import re
import sys
from difflib import SequenceMatcher
from pathlib import Path

PP = Path(os.environ.get("PP_ROOT", "/data/alvin/cookie/pastpapers_full"))
PROMPT = ("This image is cut from a Primary school exam paper. Does it contain ANY picture, drawing, diagram, graph, chart, "
          "table, grid, number line, shape, map, photo or labelled figure (anything that is not plain printed text)? If it does, "
          "reply with the single word PICTURE and nothing else. If it is ONLY printed text (words, numbers, maths symbols, option "
          "numbers), reply with the word TEXT on the first line, then copy the text exactly, line by line, as printed.")


def parse(raw):
    """('picture', None), ('text', the transcript) or ('unclear', None)."""
    s = re.sub(r"^[*_`#\s]+", "", (raw or "").strip())  # a reply may open with markdown
    if s.upper().startswith("PICTURE"):
        return "picture", None
    m = re.match(r"TEXT[*_`]*\s*[:：]?\s*(.+)", s, re.S | re.I)
    return ("text", m.group(1).strip()) if m and m.group(1).strip() else ("unclear", None)


def norm(s):
    return re.sub(r"\s+", "", s or "").lower()


def check(a, b):
    """(ok, text, why) for the two models' replies on one picture: text only when both say TEXT and agree."""
    (ka, ta), (kb, tb) = parse(a), parse(b)
    if "picture" in (ka, kb):
        return False, None, "a model sees a picture"
    if ka != "text" or kb != "text":
        return False, None, "unclear reply"
    # every number, operator and option label must be read the same by both (a one-digit slip in a long question still
    # scores above 0.95), and the words nearly the same
    sym = lambda x: re.findall(r"[0-9０-９+\-−×x÷=/.%()（）<>≤≥:]", norm(x))
    if sym(ta) != sym(tb):
        return False, None, "numbers or symbols differ"
    s = SequenceMatcher(None, norm(ta), norm(tb), autojunk=False).ratio()
    if s < 0.97:
        return False, None, f"transcripts disagree ({s:.2f})"
    return True, ta, None


def main(items_file):
    rows = [json.loads(l) for l in open(items_file) if l.strip()]
    tag = os.environ.get("PP_TAG")
    if not tag:  # a run without a tag would find the other model's files and read nothing
        sys.exit("PP_TAG is required (one output folder per model, e.g. 72b, 32b)")
    out = PP / "croptext44" / tag
    model = os.environ.get("PP_VLM", "Qwen/Qwen2.5-VL-72B-Instruct-AWQ")
    out.mkdir(parents=True, exist_ok=True)
    todo = [r for r in rows if (PP / r["file"]).exists() and not (out / f"{r['id']}.json").exists()]
    print(len(todo), "pictures to read", flush=True)
    if not todo:
        return
    from vllm import LLM, SamplingParams
    llm = LLM(model=model, tensor_parallel_size=int(os.environ.get("PP_TP", "4")),
              gpu_memory_utilization=0.9, max_model_len=8192, max_num_seqs=16, limit_mm_per_prompt={"image": 1},
              mm_processor_kwargs={"max_pixels": 1_500_000}, allowed_local_media_path=str(PP), enforce_eager=bool(os.environ.get("PP_EAGER")))
    sp = SamplingParams(temperature=0, max_tokens=1200)
    for i in range(0, len(todo), 32):
        ch = todo[i:i + 32]
        msgs = [[{"role": "user", "content": [{"type": "image_url", "image_url": {"url": f"file://{PP / r['file']}"}},
                                              {"type": "text", "text": PROMPT}]}] for r in ch]
        for r, o in zip(ch, llm.chat(msgs, sp, use_tqdm=False)):
            (out / f"{r['id']}.json").write_text(json.dumps({"id": r["id"], "model": model, "raw": o.outputs[0].text}, ensure_ascii=False))
        print(f"{min(i + 32, len(todo))}/{len(todo)} read", flush=True)


def selftest():
    assert parse("PICTURE") == ("picture", None) and parse("picture.") == ("picture", None)
    assert parse("TEXT\nWhich of the following is a mixture?") == ("text", "Which of the following is a mixture?")
    assert parse("TEXT\n") == ("unclear", None) and parse("I think") == ("unclear", None)
    t = "TEXT\nFind the value of 3 x 4.\n(1) 7 (2) 12"
    assert check(t, t)[:2] == (True, "Find the value of 3 x 4.\n(1) 7 (2) 12")
    assert check(t, "PICTURE")[2] == "a model sees a picture"
    assert check(t, "TEXT\nSomething else entirely here")[2] == "numbers or symbols differ"
    assert check(t, t.replace("3 x 4", "3 x 5"))[2] == "numbers or symbols differ"
    assert parse("**TEXT**: Which is a mixture?") == ("text", "Which is a mixture?") and parse("Text:\nAbc") == ("text", "Abc")
    print("crop_text selftest ok")


if __name__ == "__main__":
    if sys.argv[1:2] == ["selftest"]:
        selftest()
        sys.exit()
    if sys.argv[1:2] != ["read"] or len(sys.argv) != 3:
        sys.exit(__doc__)
    main(sys.argv[2])
