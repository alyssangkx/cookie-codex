#!/usr/bin/env python3
"""Read past-paper pages with a local vision-language model (vLLM, Qwen2.5-VL), one pass per page, no Claude tokens.

  /data/alvin/envs/ppvlm/bin/python scripts/pastpapers/vlm_read.py --subject maths --year 2026 --pages 41-78
  ... --gpu-mem 0.55     # fraction of the card vLLM may take (the 4090 is shared with CycloneMaster: at most 0.6)
  Both GPUs (3060 = device 0, 4090 = device 1), 4090 takes 2 of 3 pages:
    CUDA_DEVICE_ORDER=PCI_BUS_ID CUDA_VISIBLE_DEVICES=0 ... --parts 3 --mine 0 --gpu-mem 0.8 &  CUDA_DEVICE_ORDER=PCI_BUS_ID CUDA_VISIBLE_DEVICES=1 ... --parts 3 --mine 1,2

Writes OUT/<subject>/<year>/vlm/pNNNN.json: {"page", "kind", "school", "exam", "part", "section", "questions": [...],
"answers": [...]} or {"page", "error", "raw"} when the model's JSON does not parse. Pages already done are skipped.
ponytail: one prompt for all subjects; split per subject if the pilot shows it needs to."""
import argparse, json, os, re, sys
from pathlib import Path

OUT = Path(os.environ.get("PP_ROOT", "/data/alvin/tmp/cookie-codex/pastpapers"))
MODEL = os.environ.get("PP_MODEL", "Qwen/Qwen2.5-VL-7B-Instruct-AWQ")

PROMPT = """This is one scanned page of a Singapore Primary 6 {subject} exam paper. Transcribe it as JSON only, no prose:
{{"kind": "cover|questions|answers|blank|other",
 "school": "<school name if printed on this page, else null>", "exam": "<e.g. Prelim, SA2, WA2, else null>",
 "part": "<e.g. Booklet A, Booklet B, Paper 1, Paper 2, else null>", "section": "<section heading on this page, else null>",
 "questions": [{{"qno": "<printed question number, e.g. 12>", "sub": "<part label like a, b, i, else null>",
   "text": "<the question text exactly as printed, without the options>", "options": ["<option 1>", "..."],
   "marks": <a mark printed right beside THIS question or part, as a number (from [2], (2 marks), (2分)); never a section or page total; else null>,
   "figure": "<what the diagram, table or picture shows in at most 10 words, else null>"}}],
 "answers": [{{"qno": "<number>", "answer": "<the answer as printed in an answer key, short>"}}]}}
Rules: kind "answers" for an answer key or marking scheme page (then fill "answers", not "questions"); kind "cover"
for a cover or instructions page (no questions). List every question that starts on this page, in order, with its
printed number; one entry per printed part (a), (b) with its own marks. A question continued from the
previous page with no number: qno "cont". Keep Chinese text in Chinese characters. "answers" only on answer-key pages.
Do not solve the questions. Output the JSON compact on one line: no code fences, no indentation."""


def page_list(spec, n):
    out = []
    for part in spec.split(","):
        a, _, b = part.partition("-")
        out += list(range(int(a), int(b or a) + 1))
    return [p for p in out if 1 <= p <= n]


def parse(raw):
    m = re.search(r"\{.*\}", raw, re.S)
    if not m: return None
    # LaTeX (\\( \\frac \\times) is not JSON: escape a backslash unless it starts a real one-letter escape
    loose = re.sub(r'\\(?!["\\/]|u[0-9a-fA-F]{4}|[bfnrt](?![A-Za-z]))', r"\\\\", m.group(0))
    for text in (m.group(0), loose):
        try: return json.loads(text)
        except json.JSONDecodeError: pass
    return None


def repair(folder):
    """Re-parse saved pages that failed (after a parser fix). -> number fixed."""
    n = 0
    for f in Path(folder).glob("p*.json"):
        d = json.loads(f.read_text())
        if "error" in d and isinstance(parse(d.get("raw", "")), dict):
            f.write_text(json.dumps({"page": d["page"], **parse(d["raw"])}, ensure_ascii=False)); n += 1
    return n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--subject"); ap.add_argument("--year", type=int)
    ap.add_argument("--sets", help="several subject:year pairs in order, e.g. chinese:2026,maths:2026 (one model load)")
    ap.add_argument("--pages", default=None, help="page range (only with a single --subject/--year)")
    ap.add_argument("--gpu-mem", type=float, default=0.55)
    ap.add_argument("--max-pixels", type=int, default=1600 * 28 * 28)
    ap.add_argument("--batch", type=int, default=32)
    ap.add_argument("--parts", type=int, default=1, help="split pages into N interleaved parts...")
    ap.add_argument("--mine", default="0", help="...and read these parts, e.g. 1,2 (run one process per GPU)")
    ap.add_argument("--tag", default="vlm", help="output folder name, e.g. vlm32 for a second model")
    ap.add_argument("--max-seqs", type=int, default=16)
    a = ap.parse_args()
    sets = [(x.split(":")[0], int(x.split(":")[1])) for x in a.sets.split(",")] if a.sets else [(a.subject, a.year)]
    mine = {int(x) for x in a.mine.split(",")}
    todo = []
    for subject, year in sets:
        pdir, vdir = OUT / subject / str(year) / "pages", OUT / subject / str(year) / a.tag
        vdir.mkdir(exist_ok=True)
        n = max((int(f.stem[1:]) for f in pdir.glob("p[0-9][0-9][0-9][0-9].jpg")), default=0)  # highest page, not a count
        pages = [p for p in page_list(a.pages or f"1-{n}", n) if not (vdir / f"p{p:04d}.json").exists()]
        todo += [(subject, pdir, vdir, p) for k, p in enumerate(pages) if k % a.parts in mine]
    print(f"{len(todo)} pages to read", flush=True)
    if not todo: return

    from vllm import LLM, SamplingParams
    llm = LLM(model=MODEL, tensor_parallel_size=int(os.environ.get("PP_TP", "1")), gpu_memory_utilization=a.gpu_mem, max_model_len=8192, max_num_seqs=a.max_seqs,
              limit_mm_per_prompt={"image": 1}, mm_processor_kwargs={"max_pixels": a.max_pixels},
              allowed_local_media_path=str(OUT), enforce_eager=bool(os.environ.get("PP_EAGER")))
    sp = SamplingParams(temperature=0, max_tokens=3000)
    for i in range(0, len(todo), a.batch):
        chunk = todo[i:i + a.batch]
        msgs = [[{"role": "user", "content": [
            {"type": "image_url", "image_url": {"url": f"file://{pdir}/p{p:04d}.jpg"}},
            {"type": "text", "text": PROMPT.format(subject=subject)}]}] for subject, pdir, _, p in chunk]
        outs = llm.chat(msgs, sp, use_tqdm=False)
        for (_, _, vdir, p), o in zip(chunk, outs):
            raw = o.outputs[0].text
            d = parse(raw)
            rec = {"page": p, **d} if isinstance(d, dict) else {"page": p, "error": "unparsed", "raw": raw[:4000]}
            (vdir / f"p{p:04d}.json").write_text(json.dumps(rec, ensure_ascii=False))
        print(f"done {i + len(chunk)}/{len(todo)}", flush=True)


if __name__ == "__main__":
    if sys.argv[1:2] == ["repair"]:
        print(sum(repair(d) for d in sys.argv[2:]), "pages repaired"); sys.exit()
    main()
