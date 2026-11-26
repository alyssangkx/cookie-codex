#!/usr/bin/env python3
"""Re-read whole picture MCQs on the server (GPU) from their pages (queue 38, owner OK 26 Nov 2026): the questions removed
after the picture-explanation run because the first read lost text (the question sentence, statements A-D, labels or
the options drawn in the picture). Same pattern as stmt_reread.py.

  q_reread.py ITEMS.jsonl     (PP_ROOT = the pastpapers folder on the server; PP_VLM / PP_TP pick the model)
  q_reread.py selftest
ITEMS rows: {id, subject, year, qno, pages: [...], text, options: [the 4 options as first read]} (no key: the model never
sees it). The model sees the question's pages plus the next page and returns the whole question text, the 4 options, its
own answer, and whether the page carries a handwritten answer mark. A read is usable only when check() passes: a stem that
asks something, 4 distinct options, and agreement with the first read where they overlap (an independent read of the
same text). Writes PP_ROOT/qread38/<id>.json {id, raw, read, ok, why}. Prints counts only."""
import json
import os
import re
import sys
from difflib import SequenceMatcher
from pathlib import Path

PP = Path(os.environ.get("PP_ROOT", "/data/alvin/cookie/pastpapers_full"))
OUT = PP / os.environ.get("PP_QOUT", "qread38")  # queue 40 (held key problems) writes to its own folder
SUBJ = {"science": "Science", "maths": "Mathematics"}
PROMPT = ("These are pages from a Primary 6 {subject} exam paper. Find question {qno}; its text begins: \"{start}\". "
          "Copy the question exactly and reply with JSON only: "
          "{{\"stem\": \"<all the text of question {qno} before its answer options: the introduction, any statements or "
          "parts labelled A, B, C, D, any table text, and the question sentence; copy words, do not describe pictures>\", "
          "\"options\": [\"<option (1) without its number>\", \"<(2)>\", \"<(3)>\", \"<(4)>\"], "
          "\"answer\": <your own answer, 1-4, worked out from the page; null if the page does not let you decide>, "
          "\"marked\": <true if this question on the page carries a handwritten tick, circle, cross, crossing-out or "
          "written answer, else false>}}. If the four options are drawn inside a picture or table, copy what each option "
          "says. If question {qno} is not on these pages, reply {{\"form\": \"missing\"}}.")
COMBO = re.compile(r"^(?:[A-D]|and|or|only|,|\s)+$", re.I)
ASKS = re.compile(r"\?|\b(which|what|how|why|find|state|name|identify|select|choose|calculate|estimate|work out)\b", re.I)


def norm(s, letters=False):
    """Lower case, one space, no leading option number "(1)"/"1."; letters=True also drops a leading statement letter
    ("A:", "A ") - only for the FIRST read's options, never for combinations like "A and C only"."""
    lab = r"^\s*(?:\(?[1-4]\)|[1-4][.)]|\(?[A-D][.):]|[A-D](?=\s))\s*" if letters else r"^\s*(?:\(?[1-4]\)|[1-4][.)])\s*"
    return re.sub(r"\s+", " ", re.sub(lab, "", str(s or ""))).strip().lower()


def parse(text):
    m = re.search(r"\{.*\}", text or "", re.S)
    try:
        return json.loads(m.group(0)) if m else None
    except Exception:
        return None


def check(read, first_text, first_opts):
    """(ok, why). first_text / first_opts = the first read (an independent read of the same page)."""
    if not isinstance(read, dict) or read.get("form") == "missing":
        return False, "not-found"
    stem, op = str(read.get("stem") or "").strip(), read.get("options") or []
    if len(stem) < 15 or not ASKS.search(stem):
        return False, "stem-asks-nothing"
    if len(op) != 4 or not all(isinstance(o, str) and o.strip() for o in op) or len({norm(o) for o in op}) != 4:
        return False, "options-not-4"
    if read.get("marked") is True:
        return False, "answer-marked-on-page"
    if all(COMBO.fullmatch(o.strip()) for o in op):  # "A and C only" options need the statements A-D in the stem
        letters = set(re.findall(r"[A-D]", " ".join(op)))
        if any(not re.search(rf"(?:^|[\s(]){l}[\s.:)]", stem) for l in letters):
            return False, "statements-missing-for-combination-options"
    # agreement with the first read: its options, or (statement questions: the first read took statements A-D as the
    # options) its option texts inside the new stem; and the opening of the first read's text inside the new stem
    fo = [norm(o, letters=True) for o in first_opts or []]
    same_opts = sum(any(SequenceMatcher(None, f, norm(o)).ratio() >= 0.8 for o in op) for f in fo if f)
    in_stem = sum(SequenceMatcher(None, f, norm(stem), autojunk=False).find_longest_match(0, len(f), 0, len(norm(stem))).size >= 0.8 * len(f) for f in fo if f)
    head = norm(first_text)[:40]  # the opening words: the first read may lack what follows (statements, the question)
    start_ok = not head or SequenceMatcher(None, head, norm(stem), autojunk=False).find_longest_match(0, len(head), 0, len(norm(stem))).size >= 0.6 * len(head)
    if not start_ok:
        return False, "stem-differs-from-first-read"
    if fo and max(same_opts, in_stem) < 3:
        return False, f"options-differ-from-first-read ({same_opts}/4 options, {in_stem}/4 in stem)"
    return True, None


def main(items_file):
    rows = [json.loads(l) for l in open(items_file) if l.strip()]
    OUT.mkdir(parents=True, exist_ok=True)
    todo = []
    for r in rows:
        pdir = PP / r["subject"] / str(r["year"]) / "pages"
        pages = sorted(set(r["pages"]) | {max(r["pages"]) + 1})
        imgs = [pdir / f"p{p:04d}.jpg" for p in pages if (pdir / f"p{p:04d}.jpg").exists()][:3]
        if imgs and not (OUT / f"{r['id']}.json").exists():
            todo.append((r, imgs))
    print(len(todo), "questions to read", flush=True)
    if not todo:
        return
    from vllm import LLM, SamplingParams
    llm = LLM(model=os.environ.get("PP_VLM", "Qwen/Qwen2.5-VL-72B-Instruct-AWQ"), tensor_parallel_size=int(os.environ.get("PP_TP", "4")),
              gpu_memory_utilization=0.9, max_model_len=16384, max_num_seqs=8, limit_mm_per_prompt={"image": 3},
              mm_processor_kwargs={"max_pixels": 2_000_000}, allowed_local_media_path=str(PP), enforce_eager=bool(os.environ.get("PP_EAGER")))
    sp = SamplingParams(temperature=0, max_tokens=1500)
    ok = 0
    for i in range(0, len(todo), 16):
        ch = todo[i:i + 16]
        msgs = [[{"role": "user", "content": [{"type": "image_url", "image_url": {"url": f"file://{p}"}} for p in imgs]
                  + [{"type": "text", "text": PROMPT.format(subject=SUBJ.get(r["subject"], r["subject"]), qno=r["qno"],
                                                           start=r["text"][:120].replace('"', "'"))}]}] for r, imgs in ch]
        for (r, _), out in zip(ch, llm.chat(msgs, sp, use_tqdm=False)):
            raw = out.outputs[0].text
            read = parse(raw)
            good, why = check(read, r["text"], r["options"])
            ok += good
            (OUT / f"{r['id']}.json").write_text(json.dumps({"id": r["id"], "raw": raw, "read": read, "ok": good, "why": why}))
        print(f"{min(i + 16, len(todo))}/{len(todo)} read, {ok} usable", flush=True)


def selftest():
    first_text = "The diagram shows the water cycle. Which of the following statements are correct?"
    stmts = ["A: At S, the water gains heat.", "B: At S, the water loses heat.", "C: At Y, the vapour gains heat.", "D: At Y, the vapour loses heat."]
    good = {"stem": "The diagram shows the water cycle. A At S, the water gains heat. B At S, the water loses heat. C At Y, the "
                    "vapour gains heat. D At Y, the vapour loses heat. Which of the following statements are correct?",
            "options": ["A and C only", "A and D only", "B and C only", "B and D only"], "answer": 2, "marked": False}
    assert check(good, first_text, stmts) == (True, None), check(good, first_text, stmts)  # statements now in the stem
    assert check(parse("```json\n" + json.dumps(good) + "\n```"), first_text, stmts) == (True, None)
    plain = dict(good, stem="The diagram shows the water cycle. Which process is shown at S?", options=["melting", "freezing", "evaporation", "condensation"])
    assert check(plain, first_text, ["(1) melting", "(2) freezing", "(3) evaporation", "(4) condensation"]) == (True, None)
    assert check(plain, first_text, ["(1) iron", "(2) wood", "(3) glass", "(4) rubber"])[1].startswith("options-differ")
    assert check(dict(good, stem="The diagram shows the water cycle."), first_text, stmts)[1] == "stem-asks-nothing"
    assert check(dict(good, marked=True), first_text, stmts)[1] == "answer-marked-on-page"
    assert check(dict(good, options=good["options"][:3]), first_text, stmts)[1] == "options-not-4"
    assert check(dict(good, options=["A only"] * 4), first_text, stmts)[1] == "options-not-4"
    assert check({"form": "missing"}, first_text, stmts)[1] == "not-found"
    assert check(dict(plain, stem="A magnet attracts iron nails. Which process is shown at S?"), first_text,
                 ["(1) melting", "(2) freezing", "(3) evaporation", "(4) condensation"])[1] == "stem-differs-from-first-read"
    nostat = dict(good, stem="The diagram shows the water cycle. Which of the following statements are correct?")
    assert check(nostat, first_text, stmts)[1] == "statements-missing-for-combination-options"
    print("q_reread selftest ok")


if __name__ == "__main__":
    if sys.argv[1:2] == ["selftest"]:
        selftest()
        sys.exit()
    main(sys.argv[1])
