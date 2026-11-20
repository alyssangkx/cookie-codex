"""Automatic crop review for private past-paper Science pictures (ADR 0004; to-do "Automatic crop review").

The server's vision model (Qwen2.5-VL-32B-AWQ under vLLM) looks at every figure crop of every selected item,
next to the full page scan, and says: is the figure complete, does it belong to this question, does it carry
part of another question. A failing item goes to OUT/<subject>/hold-auto.txt (`load_pp.py cropcheck-apply`).
Private content: this script prints and logs ids, counts and the model's one-line reasons only; never the paper text.

Dev side (needs PIL; writes only under /data/alvin/tmp/cookie-codex/cropcheck/):
  cropcheck.py pack [--out DIR] [--subject science] [--push]
      Builds PACK/ (items.jsonl, gate.jsonl, figs/, pages/ downscaled, gate/) from OUT/<subject>/selected.jsonl and
      figures.jsonl. --push copies it to the server (/data/alvin/cookie/cropcheck/pack). REFRESH after the selection
      changes (queue 9 recovered more items): re-run `load_pp.py select` and `figures`, then
          python3 scripts/pastpapers/cropcheck.py pack --push
      run_tag11.sh reads pack/items.jsonl when its full run starts, so a refresh before that is enough.
  cropcheck.py pickup
      When the server's vlm/tag11-done.txt ends with QUEUE EMPTY, copies the results to PACK/results.jsonl.
      Then: python3 scripts/pastpapers/load_pp.py cropcheck-apply PACK/results.jsonl --out <OUT dir> --subject science

Server side (CUDA, vLLM; env /data/alvin/envs/ppvlm; started by vlm/run_tag11.sh):
  cropcheck.py gate               the gate cases must come out as expected; tries the prompt variants in order
  cropcheck.py run K N [--prompt i]   shard K of N over pack/items.jsonl (TP2 on CUDA_VISIBLE_DEVICES), resumes
"""
import argparse, hashlib, json, os, re, subprocess, sys
from pathlib import Path

TMP = Path("/data/alvin/tmp/cookie-codex")
WORK = TMP / "cropcheck"
PACK = WORK / "pack"
DEF_OUT = TMP / "ppimport" / "final2526"
SERVER = "alvin@192.168.1.170"
SERVER_BASE = "/data/alvin/cookie/cropcheck"
SERVER_PACK = SERVER_BASE + "/pack"
PAGE_MAX = 1800  # longest side of the page image sent to the model

# Gate: (pp id, source selection dirs to find its row, figure source, expectation). "orig" = the raw cut-off PNG crop.
GATE = [
    ("pp-1ffa814c59", ["prov2526", "preblind"], "webp", "fail"),
    ("pp-394ecb0bd1", ["prov2526", "preblind"], "webp", "fail"),
    ("pp-59bab0deb1", ["final2526"], "orig", "fail"),
    ("pp-17f298d774", ["final2526"], "webp", "pass"),
    ("pp-59bab0deb1", ["final2526"], "webp", "pass"),
]

BASE = ("You are checking a crop taken from a Singapore PSLE Science exam page. Image 1 is the crop. Image 2 is the full "
        "page it was cut from. The crop is meant for question number {qno}. It should show the WHOLE figure, table or "
        "graph that question {qno} uses, and nothing from any other question. The wording and the answer options of "
        "question {qno} itself may appear in the crop; that is fine.\n")
ASK = ('Answer ONLY with one JSON object, no other text: {{"complete": true/false, "belongs_to_question": true/false, '
       '"contains_other_question": true/false, "reason": "one short sentence"}}.\n')
VARIANTS = [
    BASE + ("complete = nothing of the figure is cut off at any edge of the crop (no box, label, axis, table row or "
            "column is cut). belongs_to_question = the picture is the one drawn for question {qno}, not for another "
            "question. contains_other_question = the crop shows any question number, question text or options that "
            "belong to a different question.\n") + ASK,
    BASE + ("Compare the crop with the page. Find question {qno} on the page and see which picture sits with it. "
            "Be strict. complete=false if any border line, box, label or table edge is cut off at the edge of the crop, "
            "or the picture is only part of what the page shows for this question. belongs_to_question=false if the "
            "picture sits under another question number on the page. contains_other_question=true if even a fragment "
            "of another question (a number, a line of its text, an option, a picture) is visible in the crop.\n") + ASK,
    BASE + ("Work in three steps inside the JSON reason field. (1) On the page, locate question {qno} and the figure that "
            "belongs to it. (2) Check that the crop matches that figure and that its outer border is fully inside the "
            "crop. (3) Look at the top and bottom strips of the crop for leftover pieces of the previous or the next "
            "question. When in doubt, answer the strict way: complete=false, belongs_to_question=false or "
            "contains_other_question=true.\n") + ASK,
    BASE + ("Be a harsh examiner. Fail the crop (complete=false, belongs_to_question=false or contains_other_question="
            "true) whenever: a part of the picture is missing or touches the crop edge; the picture is not the one "
            "printed for question {qno}; or any text or drawing from a neighbouring question is visible. Pass it only "
            "when the crop is a clean, whole picture of question {qno}.\n") + ASK,
]


def jl(p):
    p = Path(p)
    return [json.loads(l) for l in open(p) if l.strip()] if p.exists() else []


# ------------------------------------------------------------------ pure helpers (selftest)

def parse_answer(raw: str):
    """JSON object from the model's text -> normalised dict, or None when unreadable."""
    for m in re.finditer(r"\{[^{}]*\}", raw or "", re.S):
        try:
            d = json.loads(m.group(0))
        except Exception:
            continue
        if all(isinstance(d.get(k), bool) for k in ("complete", "belongs_to_question", "contains_other_question")):
            return {"complete": d["complete"], "belongs_to_question": d["belongs_to_question"],
                    "contains_other_question": d["contains_other_question"], "reason": str(d.get("reason", ""))[:160]}
    return None


def fig_ok(f: dict) -> bool:
    return bool(f and f.get("complete") is True and f.get("belongs_to_question") is True
                and f.get("contains_other_question") is False)


def item_ok(figs: list) -> bool:
    return bool(figs) and all(fig_ok(f) for f in figs)


def pack_stamp(pack: Path) -> str:
    """Identity of a pack: sha1 over items.jsonl and every figure file (name, size, content). Results carry it, so a
    result made from another pack (older run, different selection) is never resumed or merged."""
    h = hashlib.sha1()
    ip = Path(pack) / "items.jsonl"
    h.update(ip.read_bytes() if ip.exists() else b"")
    for f in sorted((Path(pack) / "figs").glob("*")) if (Path(pack) / "figs").is_dir() else []:
        h.update(f"{f.name}:{f.stat().st_size}:".encode())
        h.update(hashlib.sha1(f.read_bytes()).digest())
    return h.hexdigest()[:16]


def stamped(rows, stamp: str):
    """Only the result rows made from the pack with this stamp."""
    return [r for r in rows if r.get("stamp") == stamp]


def page_of_crop(crop: str):
    """('2026', 'p0519') from .../science/2026/crops/sci-...-p0519.png, else None."""
    p = Path(crop)
    m = re.search(r"-(p\d+)\.png$", p.name)
    return (p.parent.parent.name, m.group(1)) if m else None


# ------------------------------------------------------------------ dev side

def downscale_page(src: Path, dst: Path):
    from PIL import Image
    if dst.exists():
        return
    with Image.open(src) as im:
        im = im.convert("RGB")
        s = PAGE_MAX / max(im.size)
        if s < 1:
            im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
        im.save(dst, quality=85)


def pack(a):
    out = Path(a.out) / a.subject
    pp = TMP / "pastpapers" / a.subject
    for d in ("figs", "pages", "gate"):
        (PACK / d).mkdir(parents=True, exist_ok=True)
    items, nfig = [], 0
    figs = {}
    for m in jl(out / "figures.jsonl"):
        figs.setdefault(m["pp_id"], []).append(m["path"])
    for r in jl(out / "selected.jsonl"):
        fl = []
        for n, c in enumerate(r["crops"], 1):
            pg = page_of_crop(c)
            webp = out / "figures" / f"{r['id']}-{n}.webp"
            if not pg or not webp.exists():
                sys.exit(f"missing page or figure for {r['id']} crop {n}")
            link = PACK / "figs" / webp.name
            link.write_bytes(webp.read_bytes())
            pn = f"{pg[0]}-{pg[1]}.jpg"
            downscale_page(pp / pg[0] / "pages" / f"{pg[1]}.jpg", PACK / "pages" / pn)
            fl.append({"n": n, "img": f"figs/{webp.name}", "page": f"pages/{pn}"})
            nfig += 1
        if fl:  # an item without a picture has nothing to check
            items.append({"id": r["id"], "qno": r["qno"], "figs": fl})
    with open(PACK / "items.jsonl", "w") as f:
        for it in items:
            f.write(json.dumps(it) + "\n")
    gate = []
    for gid, dirs, kind, expect in GATE:
        row = None
        for d in dirs:
            row = next((r for r in jl(Path(a.out).parent / d / a.subject / "selected.jsonl") if r["id"] == gid), None)
            if row:
                src_dir = Path(a.out).parent / d / a.subject
                break
        if not row:
            sys.exit(f"gate item {gid} not found in {dirs}")
        for n, c in enumerate(row["crops"], 1):
            pg = page_of_crop(c)
            if kind == "orig":
                img = f"gate/{gid}-{n}-orig.png"
                (PACK / img).write_bytes(Path(c).read_bytes())
            else:
                img = f"gate/{gid}-{n}-fixed.webp"
                (PACK / img).write_bytes((src_dir / "figures" / f"{gid}-{n}.webp").read_bytes())
            pn = f"{pg[0]}-{pg[1]}.jpg"
            downscale_page(pp / pg[0] / "pages" / f"{pg[1]}.jpg", PACK / "pages" / pn)
            gate.append({"name": f"{gid}/{kind}", "id": gid, "qno": row["qno"], "expect": expect, "img": img, "page": f"pages/{pn}"})
    with open(PACK / "gate.jsonl", "w") as f:
        for g in gate:
            f.write(json.dumps(g) + "\n")
    (PACK / "stamp.txt").write_text(pack_stamp(PACK) + "\n")
    print(f"packed {len(items)} items, {nfig} figures, {len(gate)} gate figures -> {PACK}")
    if a.push:
        subprocess.run(["ssh", SERVER, f"mkdir -p {SERVER_PACK} {SERVER_BASE}/out"], check=True)
        subprocess.run(["rsync", "-a", "--delete", f"{PACK}/", f"{SERVER}:{SERVER_PACK}/"], check=True)
        subprocess.run(["scp", "-q", str(Path(__file__).resolve()), f"{SERVER}:/data/alvin/cookie/code/scripts/pastpapers/cropcheck.py"], check=True)
        print("pushed to", SERVER_PACK)


def pickup(a):
    r = subprocess.run(["ssh", SERVER, "tail -1 /data/alvin/cookie/vlm/tag11-done.txt"], capture_output=True, text=True)
    if "QUEUE EMPTY" not in r.stdout:
        sys.exit("queue 11 not finished: " + r.stdout.strip()[-120:])
    WORK.mkdir(parents=True, exist_ok=True)
    subprocess.run(["scp", "-q", f"{SERVER}:{SERVER_BASE}/out/results.jsonl", str(PACK / "results.jsonl")], check=True)
    subprocess.run(["scp", "-q", f"{SERVER}:/data/alvin/cookie/vlm/tag11-done.txt", str(WORK / "tag11-done.txt")], check=True)
    rows = stamped(jl(PACK / "results.jsonl"), pack_stamp(PACK))
    print(f"{len(rows)} items (current pack stamp), {sum(not r['ok'] for r in rows)} failed -> {PACK / 'results.jsonl'}")


# ------------------------------------------------------------------ server side

def run_model():
    """Starts the vLLM engine. Returns (llm, sampling params)."""
    from vllm import LLM, SamplingParams
    llm = LLM(model="Qwen/Qwen2.5-VL-32B-Instruct-AWQ", tensor_parallel_size=int(os.environ.get("PP_TP", "2")),
              gpu_memory_utilization=0.92, max_model_len=16384, max_num_seqs=6, limit_mm_per_prompt={"image": 2},
              mm_processor_kwargs={"max_pixels": 3500000}, allowed_local_media_path=SERVER_PACK,
              enforce_eager=bool(os.environ.get("PP_EAGER")))
    return llm, SamplingParams(temperature=0, max_tokens=300)


def ask(llm, sp, cases, prompt_idx):
    msgs = []
    for c in cases:
        txt = VARIANTS[prompt_idx].format(qno=c["qno"])
        msgs.append([{"role": "user", "content": [
            {"type": "image_url", "image_url": {"url": "file://" + c["img"]}},
            {"type": "image_url", "image_url": {"url": "file://" + c["page"]}},
            {"type": "text", "text": txt}]}])
    outs = llm.chat(msgs, sp, use_tqdm=False)
    return [parse_answer(o.outputs[0].text) for o in outs]


def gate_cases():
    P = Path(SERVER_PACK)
    return [{**g, "key": f"{g['name']}#{i}", "img": str(P / g["img"]), "page": str(P / g["page"])}
            for i, g in enumerate(jl(P / "gate.jsonl"))]


def gate_verdict(cases, answers):
    """Per gate item id/kind: expectation met when every figure of a 'fail' fails at least... one fails; 'pass' all pass."""
    by = {}
    for c, a in zip(cases, answers):
        by.setdefault(c["name"], []).append((c["expect"], a))
    res = {}
    for name, lst in by.items():
        expect = lst[0][0]
        oks = [fig_ok(a) if a else False for _, a in lst]
        res[name] = (not all(oks)) if expect == "fail" else all(oks)
    return res


def gate(a):
    cases = gate_cases()
    llm, sp = run_model()
    tried = []
    for i in range(len(VARIANTS)) if a.prompt is None else [a.prompt]:
        ans = ask(llm, sp, cases, i)
        res = gate_verdict(cases, ans)
        tried.append((i, res))
        print(f"gate prompt {i}: " + ", ".join(f"{k}={'ok' if v else 'WRONG'}" for k, v in res.items()), flush=True)
        for c, x in zip(cases, ans):
            print("  ", c["key"], "expect", c["expect"], json.dumps(x), flush=True)
        if all(res.values()):
            Path(SERVER_BASE).mkdir(parents=True, exist_ok=True)
            (Path(SERVER_BASE) / "prompt.txt").write_text(str(i))
            print(f"GATE PASSED prompt {i}")
            return 0
    print("GATE FAILED all prompts")
    return 1


def run(a):
    P = Path(SERVER_PACK)
    pf = Path(SERVER_BASE) / "prompt.txt"
    idx = a.prompt if a.prompt is not None else int(pf.read_text()) if pf.exists() else 0
    out = Path(SERVER_BASE) / "out" / f"results-{a.k}.jsonl"
    out.parent.mkdir(parents=True, exist_ok=True)
    stamp = pack_stamp(P)
    done = {r["id"] for r in stamped(jl(out), stamp)}
    items = [it for it in jl(P / "items.jsonl")[a.k::a.n] if it["id"] not in done]
    print(f"shard {a.k}/{a.n}: {len(items)} items to do, prompt {idx}", flush=True)
    if not items:
        return 0
    llm, sp = run_model()
    for i in range(0, len(items), 16):
        ch = items[i:i + 16]
        cases = [{"qno": it["qno"], "img": str(P / f["img"]), "page": str(P / f["page"]), "id": it["id"], "n": f["n"]}
                 for it in ch for f in it["figs"]]
        ans = ask(llm, sp, cases, idx)
        retry = [k for k, x in enumerate(ans) if x is None]
        if retry:  # unreadable answer: one more try, then it counts as a fail
            for k, x in zip(retry, ask(llm, sp, [cases[k] for k in retry], idx)):
                ans[k] = x
        with open(out, "a") as f:
            for it in ch:
                figs = []
                for c, x in zip(cases, ans):
                    if c["id"] == it["id"]:
                        figs.append({"n": c["n"], **(x or {"complete": False, "belongs_to_question": False,
                                                            "contains_other_question": True, "reason": "unparsed answer"})})
                f.write(json.dumps({"id": it["id"], "ok": item_ok(figs), "figs": figs, "prompt": idx, "stamp": stamp}) + "\n")
        print("done", i + len(ch), "/", len(items), flush=True)
    return 0


def merge(a):
    rows = {}
    stamp = pack_stamp(Path(SERVER_PACK))
    for f in sorted((Path(SERVER_BASE) / "out").glob("results-*.jsonl")):
        for r in stamped(jl(f), stamp):
            rows[r["id"]] = r
    order = [it["id"] for it in jl(Path(SERVER_PACK) / "items.jsonl")]
    with open(Path(SERVER_BASE) / "out" / "results.jsonl", "w") as f:
        for i in order:
            if i in rows:
                f.write(json.dumps(rows[i]) + "\n")
    bad = sum(not rows[i]["ok"] for i in order if i in rows)
    print(f"merged {len([i for i in order if i in rows])} of {len(order)} items, {bad} failed")
    return 0


def selftest():
    assert parse_answer('x {"complete": true, "belongs_to_question": true, "contains_other_question": false, "reason": "ok"} y')["complete"]
    assert parse_answer("```json\n{\"complete\": false, \"belongs_to_question\": true, \"contains_other_question\": false}\n```")["reason"] == ""
    assert parse_answer("no json") is None and parse_answer('{"complete": "yes"}') is None
    good = {"complete": True, "belongs_to_question": True, "contains_other_question": False}
    assert item_ok([good]) and not item_ok([]) and not item_ok([good, {**good, "complete": False}])
    assert not item_ok([{**good, "contains_other_question": True}])
    assert page_of_crop("/x/science/2026/crops/sci-2026-013-BookletA-q04-p0519.png") == ("2026", "p0519")
    assert page_of_crop("/x/y.png") is None
    cs = [{"name": "a/webp", "expect": "fail"}, {"name": "b/webp", "expect": "pass"}, {"name": "b/webp", "expect": "pass"}]
    assert gate_verdict(cs, [{**good, "complete": False}, good, good]) == {"a/webp": True, "b/webp": True}
    assert gate_verdict(cs, [good, good, None]) == {"a/webp": False, "b/webp": False}
    assert all("{qno}" in v and v.count("{{") == v.count("}}") for v in VARIANTS) and VARIANTS[0].format(qno=3)
    import tempfile
    tmpd = TMP / "reviewfix"; tmpd.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=tmpd) as td:
        pk = Path(td); (pk / "figs").mkdir()
        (pk / "items.jsonl").write_text('{"id":"a"}\n'); (pk / "figs" / "a-1.webp").write_bytes(b"xx")
        s1 = pack_stamp(pk)
        assert s1 == pack_stamp(pk)
        (pk / "figs" / "a-1.webp").write_bytes(b"xy")  # same size, other content
        s2 = pack_stamp(pk); assert s2 != s1
        (pk / "items.jsonl").write_text('{"id":"b"}\n'); assert pack_stamp(pk) != s2
        assert stamped([{"id": "a", "stamp": s1}, {"id": "b", "stamp": s2}, {"id": "c"}], s2) == [{"id": "b", "stamp": s2}]
    print("cropcheck selftest ok")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("cmd", choices=("pack", "pickup", "gate", "run", "merge", "selftest"))
    p.add_argument("k", nargs="?", type=int, default=0)
    p.add_argument("n", nargs="?", type=int, default=1)
    p.add_argument("--out", default=str(DEF_OUT))
    p.add_argument("--subject", default="science")
    p.add_argument("--push", action="store_true")
    p.add_argument("--prompt", type=int, default=None)
    a = p.parse_args()
    if a.cmd == "selftest":
        return selftest()
    r = {"pack": pack, "pickup": pickup, "gate": gate, "run": run, "merge": merge}[a.cmd](a)
    sys.exit(r or 0)


if __name__ == "__main__":
    main()
