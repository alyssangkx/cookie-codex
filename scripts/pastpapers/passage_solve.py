"""Independent check of past-paper passage keys with the server's vision model (owner, 22 Nov 2026: "go with option 1").
The 274 Chinese cloze / reading questions whose key came from the answer-page re-read (queue 24) have no blind check: the
text solver ran before their keys existed. Qwen2.5-VL-32B answers each from its passage pages and the question (it never
sees the key); calibration on already-confirmed passage questions measures how far to trust its agreement.

  dev:    passage_solve.py pack [--calib 300] [--push]   -> WORK/items.jsonl (targets + calibration, shuffled)
  server: passage_solve.py run SHARD NSHARDS               (PP_ROOT = pastpapers_full; resumable) -> WORK/picks-<k>.jsonl
  dev:    passage_solve.py report [--pull] [--write]       calibration accuracy, then agreement on the targets; --write adds
          the targets to audit/blindcheck/chinese-<year>.jsonl as blind records {id, key, pick, agree, src} (only ids with
          no record yet), which load_pp select already treats as the blind check. Only after the owner has seen the report.
  selftest
Prints ids and counts only."""
import argparse, collections, json, os, random, re, subprocess, sys
from pathlib import Path

TMP = Path("/data/alvin/tmp/cookie-codex")
PP_DEV, BLIND = TMP / "pastpapers", TMP / "audit" / "blindcheck"
WORK = TMP / "passage_solve"
SERVER, SERVER_BASE = "alvin@192.168.1.170", "/data/alvin/cookie/passage_solve"
KINDS = {"chinese-cloze": ("chicloze", (16, 20)), "chinese-reading": ("chireading", (21, 25))}
SYS = "你是新加坡小学华文老师，正在做小六会考（PSLE）华文选择题。You are an expert Singapore primary-school Chinese teacher."
ASK = ("页面图片中有一篇短文和它的题目。请在图片中找到下面这道题（试卷上的第{n}题），根据短文的内容和上下文作答。先简短思考，"
       "最后一行只写：ANSWER: <选项号 1-4>\nThe page images show a passage and its questions. Find paper question {n} below on "
       "them and answer it from the passage. Think briefly, then end with a final line exactly: ANSWER: <option number 1-4>.")


def jl(p):
    p = Path(p)
    return [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()] if p.exists() else []


ASK_DLG = ("页面图片中有一个8个短语或短句的表格和一段有空格的对话。请根据上下文，为对话中的第{n}个空格从表中选出最恰当的一项。先简短思考，"
           "最后一行只写：ANSWER: <选项号 1-8>\nThe pages show a table of 8 phrases and a dialogue with numbered blanks. Choose the "
           "phrase that fits blank ({n}). Think briefly, then end with a final line exactly: ANSWER: <option number 1-8>.")


def pick(raw):
    m = re.findall(r"ANSWER[:：]\s*\(?([1-8])\)?", raw or "")
    return m[-1] if m else None


def reread_keys():
    """{(paper, qno): key} exactly as load_pp select reads them (final cells, gate applied) - one rule, not a copy."""
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import load_pp as L
    out = {}
    for y in range(2018, 2027):
        out.update({(p, int(n)): k for (p, n), k in L.reread_keys(PP_DEV / "chinese" / str(y)).items()})
    return out


def pages_for(q, kind):
    """The passage and question pages: reading also the page before the first question page (where the passage starts)."""
    ps = sorted(q["pages"])
    lo = ps[0] - (1 if kind == "chinese-reading" else 0)
    return [p for p in range(max(1, lo), ps[-1] + 1)][-3:]  # 3 images at most: never drop the page the question is on


def pack_dialogue(a):
    """完成对话 (22 Nov 2026): every blank of the candidate sets (load_pp select --passage chinese-dialogue), the printed key
    kept on dev; no calibration set exists for 8-option items, so the report gives the agreement rate only."""
    items = []
    for c in jl(TMP / "ppimport" / "chidialogue" / "chinese" / "candidates.jsonl"):
        ps = sorted({p for b in c["blanks"] for p in b["pages"]})
        pages = [f"chinese/{c['year']}/pages/p{p:04d}.jpg" for p in range(max(1, ps[0] - 1), ps[-1] + 1)][:3]
        for b in c["blanks"]:
            items.append({"id": b["id"], "y": c["year"], "kind": "chinese-dialogue", "role": "target", "key": b["key"], "qno": b["qno"],
                          "pages": pages, "text": f"对话中的（{b['qno']}）应填入哪一个短语或短句？", "options": c["phrases"]})
    return items


def pack(a):
    if a.dialogue:
        items = pack_dialogue(a)
        WORK.mkdir(parents=True, exist_ok=True)
        with open(WORK / "items-dialogue.jsonl", "w", encoding="utf-8") as f:
            for it in items:
                f.write(json.dumps(it, ensure_ascii=False) + "\n")
        with open(WORK / "items-dialogue-server.jsonl", "w", encoding="utf-8") as f:
            for it in items:
                f.write(json.dumps({k: v for k, v in it.items() if k not in ("key", "role")}, ensure_ascii=False) + "\n")
        print(f"{len(items)} dialogue blanks -> {WORK}")
        if a.push:
            subprocess.run(["ssh", SERVER, f"mkdir -p {SERVER_BASE}/dialogue"], check=True)
            subprocess.run(["scp", "-q", str(WORK / "items-dialogue-server.jsonl"), f"{SERVER}:{SERVER_BASE}/dialogue/items.jsonl"], check=True)
            subprocess.run(["scp", "-q", str(Path(__file__).resolve()), f"{SERVER}:{SERVER_BASE}/passage_solve.py"], check=True)
            print("pushed to", SERVER_BASE + "/dialogue")
        return
    rr = reread_keys()
    items, rng = [], random.Random(22)
    for kind, (d, (lo, hi)) in KINDS.items():
        held = {r["id"] for r in jl(TMP / "ppimport" / f"{d}3" / "chinese" / "rejects.jsonl") if r["reason"] == "needs-blind-check-ocr"}
        live = {r["src_id"]: r for r in jl(TMP / "ppimport" / f"{d}2" / "chinese" / "selected.jsonl")}
        calib = set(rng.sample(sorted(live), min(a.calib // 2, len(live))))
        for y in range(2018, 2027):
            for q in jl(PP_DEV / "chinese" / str(y) / "merged.jsonl"):
                n = int(q["qno"]) if str(q.get("qno") or "").isdigit() else None
                if q["id"] in held and (q["paper"], n) in rr:
                    key, role = rr[(q["paper"], n)], "target"
                elif q["id"] in calib:
                    key, role = str(live[q["id"]]["answer"] + 1), "calib"
                else:
                    continue
                sys.path.insert(0, str(Path(__file__).resolve().parent))
                import load_pp as L
                items.append({"id": q["id"], "y": y, "kind": kind, "role": role, "key": key, "qno": n,
                              "pages": [f"chinese/{y}/pages/p{p:04d}.jpg" for p in pages_for(q, kind)],
                              "text": q["text"], "options": L.strip_opts(q["options"])})  # no "(1) (1) 焦急"
    rng.shuffle(items)
    WORK.mkdir(parents=True, exist_ok=True)
    with open(WORK / "items.jsonl", "w", encoding="utf-8") as f:  # the key stays on dev: the server copy drops it
        for it in items:
            f.write(json.dumps(it, ensure_ascii=False) + "\n")
    with open(WORK / "items-server.jsonl", "w", encoding="utf-8") as f:
        for it in items:
            f.write(json.dumps({k: v for k, v in it.items() if k not in ("key", "role")}, ensure_ascii=False) + "\n")
    c = collections.Counter((it["kind"], it["role"]) for it in items)
    print(f"{len(items)} items: {dict(c)} -> {WORK}")
    if a.push:
        subprocess.run(["ssh", SERVER, f"mkdir -p {SERVER_BASE}"], check=True)
        subprocess.run(["scp", "-q", str(WORK / "items-server.jsonl"), f"{SERVER}:{SERVER_BASE}/items.jsonl"], check=True)
        subprocess.run(["scp", "-q", str(Path(__file__).resolve()), f"{SERVER}:{SERVER_BASE}/passage_solve.py"], check=True)
        print("pushed to", SERVER_BASE)


def run(a):
    root = Path(os.environ.get("PP_ROOT", "/data/alvin/cookie/pastpapers_full"))
    w = Path(SERVER_BASE) / ("dialogue" if a.dialogue else "")
    items = jl(w / "items.jsonl")[a.shard::a.nshards]
    out = w / f"picks-{a.shard}.jsonl"
    want = {q["id"]: q["pages"] for q in items}
    done = {r["id"] for r in jl(out) if r.get("pages", want.get(r["id"])) == want.get(r["id"])}  # a pick from other pages is redone
    todo = [q for q in items if q["id"] not in done]
    print(len(todo), "to solve", flush=True)
    if not todo:
        return
    from vllm import LLM, SamplingParams
    llm = LLM(model="Qwen/Qwen2.5-VL-32B-Instruct-AWQ", tensor_parallel_size=2, gpu_memory_utilization=0.92, max_model_len=16384,
              max_num_seqs=6, limit_mm_per_prompt={"image": 3}, mm_processor_kwargs={"max_pixels": 2500000},
              allowed_local_media_path=str(root), enforce_eager=bool(os.environ.get("PP_EAGER")))
    sp = SamplingParams(temperature=0, max_tokens=1500)
    for i in range(0, len(todo), 16):
        ch = todo[i:i + 16]
        msgs = [[{"role": "system", "content": SYS}, {"role": "user", "content":
                 [{"type": "image_url", "image_url": {"url": "file://" + str(root / p)}} for p in q["pages"]]
                 + [{"type": "text", "text": (ASK_DLG if q.get("kind") == "chinese-dialogue" else ASK).format(n=q["qno"]) + "\n\n" + q["text"] + "\n"
                     + "\n".join(f"({j}) {o}" for j, o in enumerate(q["options"], 1))}]}] for q in ch]
        res = llm.chat(msgs, sp, use_tqdm=False)
        with open(out, "a", encoding="utf-8") as f:
            for q, r in zip(ch, res):
                f.write(json.dumps({"id": q["id"], "pick": pick(r.outputs[0].text), "pages": q["pages"],
                                    "raw": r.outputs[0].text[-300:]}, ensure_ascii=False) + "\n")
        print("done", i + len(ch), "/", len(todo), flush=True)


def report_dialogue(a):
    if a.pull:
        subprocess.run(["scp", "-q", f"{SERVER}:{SERVER_BASE}/dialogue/picks-*.jsonl", str(WORK) + "/"], check=False)
    picks = {r["id"]: r["pick"] for f in WORK.glob("picks-*.jsonl") for r in jl(f)}
    items = [it for it in jl(WORK / "items-dialogue.jsonl") if it["id"] in picks]
    agree = sum(picks[it["id"]] == it["key"] for it in items)
    print(f"chinese-dialogue: VL-32B agrees with the printed key on {agree}/{len(items)} = {100 * agree / max(1, len(items)):.1f}% "
          f"(no calibration set: a further check beside the three outside models), unparsed {sum(picks[it['id']] is None for it in items)}")


def report(a):
    if a.dialogue:
        return report_dialogue(a)
    if a.pull:
        subprocess.run(["scp", "-q", f"{SERVER}:{SERVER_BASE}/picks-*.jsonl", str(WORK) + "/"], check=False)  # every shard
    items = jl(WORK / "items.jsonl")
    # only picks made from this pack's pages (a leftover picks file from an earlier pack is ignored); older picks carry no pages
    want = {it["id"]: it.get("pages") for it in items}
    picks = {r["id"]: r["pick"] for f in sorted(WORK.glob("picks-*.jsonl")) for r in jl(f)
             if "pages" not in r or want.get(r["id"]) is None or r["pages"] == want[r["id"]]}
    for kind in KINDS:
        cal = [it for it in items if it["kind"] == kind and it["role"] == "calib" and it["id"] in picks]
        tgt = [it for it in items if it["kind"] == kind and it["role"] == "target" and it["id"] in picks]
        ok = sum(picks[it["id"]] == it["key"] for it in cal)
        agree = sum(picks[it["id"]] == it["key"] for it in tgt)
        print(f"{kind}: calibration {ok}/{len(cal)} = {100 * ok / max(1, len(cal)):.1f}%; re-read keys confirmed {agree}/{len(tgt)}, "
              f"unparsed {sum(picks[it['id']] is None for it in tgt)}")
    if a.write:
        by = collections.defaultdict(list)
        for it in items:
            if it["role"] == "target" and picks.get(it["id"]):  # an unparsed answer is not written: a re-run can still answer it
                by[it["y"]].append({"id": it["id"], "key": it["key"], "pick": picks[it["id"]],
                                    "agree": picks[it["id"]] == it["key"], "src": "vl32-passage"})
        n = 0
        for y, rs in sorted(by.items()):
            f = BLIND / f"chinese-{y}.jsonl"
            have = {r["id"] for r in jl(f)}
            new = [r for r in rs if r["id"] not in have]  # never overwrite an existing blind record
            with open(f, "a", encoding="utf-8") as fh:
                for r in new:
                    fh.write(json.dumps(r) + "\n")
            n += len(new)
        print("wrote", n, "blind records to", BLIND)


def selftest():
    assert pick("思考……\nANSWER: 3") == "3" and pick("ANSWER：(2)") == "2" and pick("no") is None and pick("ANSWER: 7") == "7"
    assert pages_for({"pages": [10, 11]}, "chinese-reading") == [9, 10, 11] and pages_for({"pages": [8]}, "chinese-cloze") == [8]
    assert pages_for({"pages": [10, 11, 12]}, "chinese-reading") == [10, 11, 12]  # the question's own last page is kept
    print("passage_solve selftest ok")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("cmd", choices=("pack", "run", "report", "selftest"))
    p.add_argument("shard", nargs="?", type=int, default=0)
    p.add_argument("nshards", nargs="?", type=int, default=1)
    p.add_argument("--calib", type=int, default=300)
    p.add_argument("--push", action="store_true")
    p.add_argument("--pull", action="store_true")
    p.add_argument("--write", action="store_true")
    p.add_argument("--dialogue", action="store_true", help="完成对话: pack/run/report the dialogue blanks (8 phrases)")
    a = p.parse_args()
    {"pack": pack, "run": run, "report": report, "selftest": lambda _a: selftest()}[a.cmd](a)
