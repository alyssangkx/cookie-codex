#!/usr/bin/env python3
"""Passages as text (owner, 24 Nov 2026: "all subjects OCR any text; pictures, tables and figures stay images"). The English
passage sections are read from their exam pages by the vision model, with what the question needs kept as markup:
  {{16|entrusted}}   an underlined word or phrase with its question number (Vocabulary Cloze, Editing)
  [[31]]             a numbered blank (Grammar Cloze, Comprehension Cloze); printed letters next to it stay: b[[41]]
A second, different model reads every passage too; a passage is used only when both reads carry the same markers, the same
underlined words, and nearly the same text (check).

  passage.py pack                 dev: sections.jsonl (one per passage section of a paper) -> /data/alvin/tmp/cookie-codex/passage
  passage.py run ITEMS            server (GPU; PP_ROOT, PP_VLM, PP_TP, PP_OUT): read.jsonl or PP_OUT, resumable
  passage.py check [--sample N]   dev: passages.jsonl {sec, st, passage, markers}; prints counts
  passage.py selftest"""
import collections
import difflib
import json
import os
import random
import re
import sys
from pathlib import Path

TMP = Path("/data/alvin/tmp/cookie-codex")
WORK = Path(os.environ.get("PP_WORK", str(TMP / "passage")))
SECTIONS = {  # sub-topic: (name on the paper, what to mark)
    "eng-vocab-cloze": ("Vocabulary Cloze", "under"),
    "eng-editing": ("Editing for Spelling and Grammar", "under"),
    "eng-grammar-cloze": ("Grammar Cloze", "blank"),
    "eng-comp-cloze": ("Comprehension Cloze", "blank"),
}
MARK = {
    "under": "Each underlined word or phrase has a question number printed next to or under it. Write it as {{N|word}} with "
             "the number and the underlined words exactly, e.g. {{16|entrusted}} or {{18|detailed plan for their trip}}.",
    "blank": "Each numbered blank is a gap the student fills. Write it as [[N]] with its number, e.g. [[31]]. If letters are "
             "printed in or next to the blank (a hint), keep them next to it, e.g. b[[41]].",
}
PROMPT = ("These are pages from a Singapore Primary 6 English exam paper. Transcribe the {name} passage (questions {a} to {b}) "
          "exactly as printed, word for word, with its punctuation. {mark} Leave out the instructions, any word box or list of "
          "options, the question numbers in the margin, page headers and footers. Separate paragraphs with a blank line. If the "
          "passage has a title, put it on the first line. Reply with JSON only: {{\"passage\": \"...\"}}. If the passage is not "
          "on these pages, reply {{\"none\": true}}.")
UNDER = re.compile(r"\{\{\s*(\d{1,3})\s*\|\s*([^{}|]*?)\s*\}\}")  # empty: Editing's missing-word box
BLANK = re.compile(r"\[\[\s*(\d{1,3})\s*\]\]")


def jl(p):
    p = Path(p)
    return [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()] if p.exists() else []


def parse(text):
    m = re.search(r"\{.*\}", text or "", re.S)
    try:
        return json.loads(m.group(0)) if m else None
    except Exception:
        return None


def markers(passage, kind):
    """{question number: underlined words (lower case) or ""} in the order they appear; None when a number repeats."""
    found = [(int(n), " ".join(w.lower().split())) for n, w in UNDER.findall(passage)] if kind == "under" \
        else [(int(n), "") for n in BLANK.findall(passage)]
    d = dict(found)
    return d if len(d) == len(found) else None


def plain(passage):
    """The words alone, for comparing two reads."""
    t = BLANK.sub(" ", UNDER.sub(lambda m: m.group(2), passage or ""))
    return " ".join(re.sub(r"[^\w']+", " ", t.lower().replace("’", "'")).split())


def clusters(qs):
    """A paper's questions of one section, split where their pages jump (a file holding two papers), as runs of pages."""
    qs = sorted((q for q in qs if q.get("pages")), key=lambda q: min(q["pages"]))
    out, cur = [], []
    for q in qs:
        if cur and min(q["pages"]) - max(p for c in cur for p in c["pages"]) > 1:
            out.append(cur)
            cur = []
        cur.append(q)
    return out + ([cur] if cur else [])


def pack():
    WORK.mkdir(parents=True, exist_ok=True)
    base = TMP / "pastpapers" / "english"
    rows = []
    for y in range(2018, 2027):
        tags = {t["id"]: t for t in jl(base / str(y) / "tags72.jsonl")}
        by = collections.defaultdict(list)
        for q in jl(base / str(y) / "merged.jsonl"):
            st = (tags.get(q["id"]) or {}).get("st")
            if st in SECTIONS and isinstance(q.get("qno"), int):
                by[(q.get("paper"), st)].append(q)
        for (paper, st), qs in by.items():
            for n, c in enumerate(clusters(qs)):
                pages = sorted({p for q in c for p in q["pages"]})
                if len(c) < 3 or pages[-1] - pages[0] > 2:
                    continue  # one or two stray questions, or bad page data
                qn = sorted({q["qno"] for q in c})
                # and the page before: a passage often starts on the page before its first question (vocabulary cloze options,
                # a cloze's instruction at the foot of a page)
                rows.append({"sec": f"{paper}-{st}-{n}", "year": y, "paper": paper, "st": st, "kind": SECTIONS[st][1],
                             "pages": list(range(max(1, pages[0] - 1), pages[-1] + 1)), "a": qn[0], "b": qn[-1], "qnos": qn,
                             "ids": [q["id"] for q in sorted(c, key=lambda q: q["qno"])]})
    (WORK / "sections.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
    print(f"{len(rows)} passage sections ({dict(collections.Counter(r['st'] for r in rows))}) -> {WORK / 'sections.jsonl'}")


def run(items_file):
    from PIL import Image
    items_file = Path(items_file).resolve()
    pp = Path(os.environ.get("PP_ROOT", "/data/alvin/cookie/pastpapers_full"))
    out = items_file.with_name(os.environ.get("PP_OUT", "read.jsonl"))
    done = {r["sec"] for r in jl(out)}
    img = items_file.with_name("img")
    img.mkdir(exist_ok=True)
    todo = []
    for r in jl(items_file):
        if r["sec"] in done:
            continue
        files = []
        for p in r["pages"]:
            src, dst = pp / "english" / str(r["year"]) / "pages" / f"p{p:04d}.jpg", img / f"{r['year']}-p{p:04d}.jpg"
            if not src.exists():
                break
            if not dst.exists():
                im = Image.open(src).convert("L")
                im.thumbnail((1400, 1960))
                im.save(dst, quality=88)
            files.append(dst)
        if len(files) == len(r["pages"]):
            todo.append((r, files))
    print(len(todo), "passages to read", flush=True)
    if not todo:
        return
    from vllm import LLM, SamplingParams
    model = os.environ.get("PP_VLM", "Qwen/Qwen2.5-VL-72B-Instruct-AWQ")
    llm = LLM(model=model, tensor_parallel_size=int(os.environ.get("PP_TP", "4")), gpu_memory_utilization=0.9,
              max_model_len=16384, max_num_seqs=8, limit_mm_per_prompt={"image": 4}, mm_processor_kwargs={"max_pixels": 1_600_000},
              allowed_local_media_path=str(img.parent), enforce_eager=bool(os.environ.get("PP_EAGER")))
    sp = SamplingParams(temperature=0, max_tokens=2500)
    with open(out, "a", encoding="utf-8") as f:
        for i in range(0, len(todo), 16):
            ch = todo[i:i + 16]
            msgs = [[{"role": "user", "content": [*({"type": "image_url", "image_url": {"url": f"file://{x}"}} for x in files),
                     {"type": "text", "text": PROMPT.format(name=SECTIONS[r["st"]][0], a=r["a"], b=r["b"], mark=MARK[r["kind"]])}]}]
                    for r, files in ch]
            for (r, _), o in zip(ch, llm.chat(msgs, sp, use_tqdm=False)):
                f.write(json.dumps({"sec": r["sec"], "model": model, "raw": o.outputs[0].text}, ensure_ascii=False) + "\n")
            f.flush()
            print(f"{min(i + 16, len(todo))}/{len(todo)}", flush=True)


def judge(r, raw1, raw2):
    """(passage, None) when both reads agree, else (None, why)."""
    v1, v2 = parse(raw1) or {}, parse(raw2) or {}
    p1, p2 = v1.get("passage"), v2.get("passage")
    if not p1 or not p2:
        return None, "not read" if not (p1 or p2) else "one read missing"
    m1, m2 = markers(p1, r["kind"]), markers(p2, r["kind"])
    if m1 is None or m2 is None:
        return None, "a question number repeats"
    # the passage holds every blank, and the first read of the paper missed some questions: the markers must be one unbroken
    # run of numbers covering most of the known questions (a stray known number far off is the first read's slip)
    nums, want = sorted(m1), set(r["qnos"])
    if nums != list(range(nums[0], nums[0] + len(nums))) if nums else True:
        return None, "markers are not one run of numbers"
    # every known question has its blank (one first-read slip allowed), and at most 3 blanks beyond the known ones (the first
    # read missed a few questions; more is the next section run in)
    if len(want - set(nums)) > 1 or len(set(nums) - set(range(min(want), max(want) + 1))) > 3:
        return None, "markers differ from the questions"
    if r.get("st") != "eng-editing" and any(not w for w in m1.values()) and r["kind"] == "under":
        return None, "an underline lost its words"  # only Editing has a box with no word (a missing word)
    if m1 != m2:
        return None, "the two reads mark different words" if set(m2) == set(m1) else "the second read's markers differ"
    if difflib.SequenceMatcher(None, plain(p1), plain(p2), autojunk=False).ratio() < 0.95:
        return None, "the two reads' text differs"
    return p1.strip(), None


def check(sample=0):
    secs = {r["sec"]: r for r in jl(WORK / "sections.jsonl")}
    a = {r["sec"]: r["raw"] for r in jl(WORK / "read.jsonl")}
    b = {r["sec"]: r["raw"] for r in jl(WORK / "read2.jsonl")}
    ok, why = [], collections.Counter()
    for s, r in secs.items():
        p, w = judge(r, a.get(s), b.get(s))
        why[(r["st"], w or "kept")] += 1
        if p:
            ok.append({"sec": s, "st": r["st"], "year": r["year"], "paper": r["paper"], "ids": r["ids"], "passage": p,
                       "markers": markers(p, r["kind"])})
    (WORK / "passages.jsonl").write_text("".join(json.dumps(x, ensure_ascii=False) + "\n" for x in ok))
    for st in SECTIONS:
        print(st + ": " + ", ".join(f"{w} {n}" for (s, w), n in sorted(why.items(), key=lambda kv: -kv[1]) if s == st))
    for x in random.Random(3).sample(ok, min(sample, len(ok))):
        print(f"\n[{x['st']}] {x['sec']}\n{x['passage'][:700]}")


GC_LETTERS = "ABCDEFGHJKLMNPQRSTUVWXYZ"  # a grammar-cloze word box skips I and O ("omitted to avoid confusion")
CLOZE_OUT = TMP / "ppimport" / "engcloze"


def box_ok(box):
    """A Grammar Cloze word box the letters can be trusted against: 10+ entries, each a word (or two), none repeated."""
    return bool(box) and len(box) >= 10 and len({b.lower() for b in box}) == len(box) \
        and all(re.fullmatch(r"[A-Za-z'’-]+(?: [A-Za-z'’-]+)?", b) for b in box)


def read_answers(path):
    """{(P label, blank number): word} from a blind reply ("P12" then "29. word" lines; "P12 (Grammar Cloze)" accepted)."""
    out, cur = {}, None
    for line in Path(path).read_text(encoding="utf-8").splitlines() if Path(path).exists() else ():
        m = re.match(r"^\s*\**\s*(P\d+)\b", line)
        if m:
            cur = m.group(1)
            continue
        m = re.match(r"^\s*(\d{1,3})[.)]\s*(.+?)\s*$", line)
        if m and cur:
            out[(cur, int(m.group(1)))] = m.group(2).strip(" *.")
    return out


def cloze_check():
    """Each typed cloze blank against the blind answers: ships when its key matches Claude and Perplexity (any of the key's
    own alternatives counts). CLOZE_OUT/english/checked.jsonl {id, key, claude, perplexity, verdict}; prints counts. A
    Perplexity reply may be split per part (cloze_part_NN.perplexity.txt) or one file with "Part N" headings."""
    import glob
    rows = jl(CLOZE_OUT / "english" / "selected.jsonl")
    d = CLOZE_OUT / "blind"
    label = {}
    for f in sorted(glob.glob(str(d / "cloze_part_*.json"))):
        for k, g in json.loads(Path(f).read_text()).items():
            label[g] = k
    claude, pplx = {}, {}
    for f in sorted(glob.glob(str(d / "cloze_part_*.claude.txt"))):
        claude.update(read_answers(f))
    for f in sorted(glob.glob(str(d / "cloze_part_*.perplexity.txt"))) + sorted(glob.glob(str(d / "*perplexity*all*.txt"))):
        pplx.update(read_answers(f))
    n = lambda w: (w or "").strip().lower().strip(" .,'\"")
    out, why = [], collections.Counter()
    for r in rows:
        k = (label.get(r["grp"]), r["seq"])
        keys = {n(a) for a in r["accept"]}
        c, pp = claude.get(k), pplx.get(k)
        if c is None:
            v = "no Claude answer"
        elif n(c) not in keys:
            v = "Claude disagrees"
        elif pp is None:
            v = "Claude agrees, Perplexity not in yet"
        elif n(pp) not in keys:
            v = "Perplexity disagrees"
        else:
            v = "confirmed"
        why[(r["subtopic"], v)] += 1
        out.append({"id": r["id"], "grp": r["grp"], "seq": r["seq"], "sub": r["subtopic"], "key": r["accept"], "claude": c,
                    "perplexity": pp, "verdict": v})
    # a passage whose keys are out of step (a lost word-box entry, a blank number off by one) agrees by chance on a few
    # blanks: when over 40% of its blanks disagree with Claude, none of them ships
    tot, bad = collections.Counter(x["grp"] for x in out), collections.Counter(x["grp"] for x in out if x["verdict"] == "Claude disagrees")
    for x in out:
        if bad[x["grp"]] > 0.4 * tot[x["grp"]] and x["verdict"] != "Claude disagrees":
            why[(x["sub"], x["verdict"])] -= 1
            x["verdict"] = "passage keys out of step"
            why[(x["sub"], x["verdict"])] += 1
    (CLOZE_OUT / "english" / "checked.jsonl").write_text("".join(json.dumps(x, ensure_ascii=False) + "\n" for x in out))
    for st in ("eng-grammar-cloze", "eng-comp-cloze"):
        print(st + ": " + ", ".join(f"{v} {c}" for (s2, v), c in sorted(why.items(), key=lambda kv: -kv[1]) if s2 == st))


CLOZE_SHIP = TMP / "ppimport" / "engcloze-ship"


def cloze_final():
    """The blanks that ship: the key agrees with Claude's blind answer (and with Perplexity's when it is in; owner, 24 Nov
    2026: a third check rarely changes an agreed key). Sets keep 2+ shipping blanks; the others stay "(n) ____" in the
    passage. CLOZE_SHIP/english/selected.jsonl -> load_pp.py upload --out CLOZE_SHIP"""
    ok = {x["id"] for x in jl(CLOZE_OUT / "english" / "checked.jsonl")
          if x["verdict"] in ("confirmed", "Claude agrees, Perplexity not in yet")}
    rows = [r for r in jl(CLOZE_OUT / "english" / "selected.jsonl") if r["id"] in ok]
    n = collections.Counter(r["grp"] for r in rows)
    rows = [r for r in rows if n[r["grp"]] >= 2]
    out = CLOZE_SHIP / "english"
    out.mkdir(parents=True, exist_ok=True)
    (out / "selected.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows))
    print(f"{len(rows)} blanks in {len(set(r['grp'] for r in rows))} sets ({dict(collections.Counter(r['subtopic'] for r in rows))}) -> {out}")


def cloze_keys(st, key, box, letters=None):
    """The accepted words for one blank, strictly from the key: a word-box letter ("K", "D (during)") is its word, the
    school's own alternatives ("make/produce") all count. [] when the key cannot be read."""
    key = (key or "").strip()
    if re.fullmatch(r"\(?[A-Z]{2,}\)?", key):
        return []  # "(AVOID)": a word in capitals is another section's key read onto this blank
    if st == "eng-grammar-cloze":
        m2 = re.fullmatch(r"\(([A-Z])\)\s+([A-Za-z'’-]+)", key)  # "(D) for"
        if m2:
            key = f"{m2.group(1)} ({m2.group(2)})"
        m = re.fullmatch(r"\(?([A-Z])\)?(?:\s*\(([^()]+)\))?", key)
        if m:
            word = (m.group(2) or "").strip()
            # the letters the box itself prints (a school may letter it A-P with I, or skip I and O: GC_LETTERS)
            k = letters.index(m.group(1)) if letters and m.group(1) in letters else (-1 if letters else GC_LETTERS.find(m.group(1)))
            if box and 0 <= k < len(box):
                return [box[k]] if not word or word.lower() == box[k].lower() else []  # letter and word disagree: unsure
            return [word] if word and (not box or word.lower() in {b.lower() for b in box}) else []
        if box and key.lower() not in {b.lower() for b in box}:
            return []  # a Grammar Cloze answer is a word from its box; anything else is a misread or another section's key
    key = re.sub(r"^\((.+)\)$", r"\1", key)  # "(on)"
    alts = [a.strip(" .") for a in re.split(r"\s*/\s*", key) if a.strip(" .")]
    return alts if alts and all(len(a.split()) <= 3 for a in alts) else []


def cloze_stem(passage, asked, box=None):
    """The passage as the quiz shows one blank's question: every blank "(n) ____", the asked one "(n) ________" (the quiz
    highlights it), the word box first for Grammar Cloze."""
    t = BLANK.sub(lambda m: f"({m.group(1)}) ________" if int(m.group(1)) == asked else f"({m.group(1)}) ____", passage)
    t = re.sub(r"(\w)\((\d+)\)", r"\1 (\2)", t)  # "b(41)": a printed hint letter stays, spaced from the number
    return (f"Word box: {' · '.join(box)}\n\n" if box else "") + t


def export_cloze():
    """Agreed Grammar and Comprehension Cloze passages as typed question sets (migration 015): one question per keyed blank,
    grouped by passage (grp/seq). CLOZE_OUT/english/selected.jsonl, then
    load_pp.py upload --subject english --out CLOZE_OUT --subtopics eng-grammar-cloze,eng-comp-cloze [--apply]"""
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from load_pp import pp_id, LEVEL, set_id
    base = TMP / "pastpapers" / "english"
    qs, tags = {}, {}
    for y in range(2018, 2027):
        for q in jl(base / str(y) / "merged.jsonl"):
            qs[q["id"]] = q
        for t in jl(base / str(y) / "tags72.jsonl"):
            tags[t["id"]] = t
    rows, why, seen_text = [], collections.Counter(), set()
    for p in jl(WORK / "passages.jsonl"):
        if p["st"] not in ("eng-grammar-cloze", "eng-comp-cloze"):
            continue
        cands = [qs[i] for i in p["ids"] if i in qs]
        box = next((q["options"] for q in cands if len(q.get("options") or []) >= 8), None) if p["st"] == "eng-grammar-cloze" else None
        letters = [m.group(1) for m in (re.match(r"^\(?([A-Z])\)?\s+", o) for o in box or []) if m] if box else []
        letters = letters if box and len(letters) == len(box) else None  # printed letters for every entry, or none used
        box = [re.sub(r"^\(?[A-Z]\)?\s+", "", o).strip() for o in box] if box else None
        if p["st"] == "eng-grammar-cloze" and not box_ok(box):
            why["word box missing or garbled"] += len(p["markers"])  # a lost or repeated word shifts every letter key after it
            continue
        sig = " ".join(plain(p["passage"]).split())
        if sig in seen_text:
            why["same passage in another paper"] += len(p["markers"])
            continue
        seen_text.add(sig)
        by = collections.defaultdict(list)
        for q in cands:
            by[q.get("qno")].append(q)
        grp = None
        for n in sorted(int(k) for k in p["markers"]):
            keys = [cloze_keys(p["st"], q.get("answer"), box, letters) for q in by.get(n, [])]
            keys = [k for k in keys if k]
            if not keys or any([w.lower() for w in k] != [w.lower() for w in keys[0]] for k in keys):
                why["no key" if not keys else "copies disagree"] += 1
                continue
            q = sorted(by[n], key=lambda q: q["id"])[0]
            grp = grp or set_id(q, "gc" if p["st"] == "eng-grammar-cloze" else "cc")
            d = (tags.get(q["id"]) or {}).get("difficulty")
            rows.append({"id": pp_id(q["id"]), "src_id": q["id"], "subject": "english", "subtopic": p["st"],
                         "level": LEVEL.get(d if isinstance(d, int) else 2, "intermediate"), "difficulty": d, "pattern": None,
                         "stem": cloze_stem(p["passage"], n, box), "options": [], "answer": 0, "crops": [], "year": p["year"],
                         "school": q.get("school"), "paper": q.get("paper"), "qno": n, "marks": q.get("marks"),
                         "blind_src": "two-readers", "kind": "typed", "accept": keys[0], "scaffold": None, "grp": grp, "seq": n})
            why["kept"] += 1
    counts = collections.Counter(r["grp"] for r in rows)
    rows = [r for r in rows if counts[r["grp"]] >= 2]  # a set of one is not a set
    out = CLOZE_OUT / "english"
    out.mkdir(parents=True, exist_ok=True)
    (out / "selected.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows))
    print(", ".join(f"{k} {v}" for k, v in why.most_common()) + f" -> {len(rows)} questions in {len(set(r['grp'] for r in rows))} sets "
          f"({dict(collections.Counter(r['subtopic'] for r in rows))}) -> {out}")


CLOZE_HEAD = ("Singapore PSLE English cloze passages. For each passage, fill every numbered blank with ONE word (Grammar Cloze: "
              "a word from its word box) so the passage is correct English. Reply with one line per blank and nothing else, "
              "grouped under the passage heading:  P<passage>  then  <blank number>. <word>")


def pack_cloze(per=20):
    """Blind packs: the cloze sets' passages with every blank open (the keys never shown), for Perplexity (PDF) and the
    Claude agents (the same text). CLOZE_OUT/blind/cloze_part_NN.{pdf,txt,json}; the json maps P<k> to the set id."""
    import html
    import subprocess
    rows = jl(CLOZE_OUT / "english" / "selected.jsonl")
    sets = collections.OrderedDict()
    for r in rows:
        sets.setdefault(r["grp"], r)
    d = CLOZE_OUT / "blind"
    d.mkdir(parents=True, exist_ok=True)
    keys = list(sets)
    for p in range(0, len(keys), per):
        n = p // per + 1
        part, txt, items = keys[p:p + per], [CLOZE_HEAD, ""], []
        for k, g in enumerate(part, p + 1):
            r = sets[g]
            open_text = re.sub(r"\((\d+)\) _{8}", r"(\1) ____", r["stem"])  # the asked blank like the rest: nothing marked
            name = "Grammar Cloze" if r["subtopic"] == "eng-grammar-cloze" else "Comprehension Cloze"
            txt += [f"P{k} ({name})", open_text, ""]
            items.append(f"<h3>P{k} ({name})</h3><p>{html.escape(open_text).replace(chr(10), '<br>')}</p>")
        (d / f"cloze_part_{n:02d}.txt").write_text("\n".join(txt))
        (d / f"cloze_part_{n:02d}.json").write_text(json.dumps({f"P{k}": g for k, g in enumerate(part, p + 1)}))
        page = (f"<!doctype html><meta charset=utf-8><style>body{{font:12pt/1.5 Arial,sans-serif;margin:16mm}}h3{{margin:14pt 0 4pt}}"
                f"p{{margin:0}}</style><p><b>Part {n}.</b> {html.escape(CLOZE_HEAD)}</p>{''.join(items)}")
        (d / f"cloze_part_{n:02d}.html").write_text(page)
        subprocess.run(["google-chrome", "--headless", "--no-sandbox", "--disable-gpu", "--no-pdf-header-footer",
                        f"--print-to-pdf={d / f'cloze_part_{n:02d}.pdf'}", (d / f"cloze_part_{n:02d}.html").as_uri()],
                       check=True, capture_output=True, timeout=120)
    print(f"{len(keys)} passages in {-(-len(keys) // per)} parts -> {d}")


def selftest():
    p = "Benedict read {{17|widely}} to find out more. They made a {{18| detailed plan  for their trip }}."
    assert markers(p, "under") == {17: "widely", 18: "detailed plan for their trip"}
    assert markers("A [[31]] and b[[32]].", "blank") == {31: "", 32: ""}
    assert markers("A [[31]] and [[31]].", "blank") is None, "a repeated number is a misread"
    assert plain("He read {{17|widely}} [[3]] more.") == "he read widely more"
    r = {"kind": "under", "qnos": [17, 18]}
    raw = lambda t: json.dumps({"passage": t})
    assert judge(r, raw(p), raw(p.replace("Benedict", "Benedict "))) == (p, None)
    assert judge(r, raw(p), raw(p.replace("|widely", "|wisely")))[1] == "the two reads mark different words"
    assert judge(r, raw(p), raw(p.replace("{{18| detailed plan  for their trip }}", "detailed plan")))[1] == "the second read's markers differ"
    assert judge({"kind": "under", "qnos": [16, 17, 18, 19, 20]}, raw(p), raw(p))[1] == "markers differ from the questions"
    assert judge({"kind": "under", "qnos": [17]}, raw(p), raw(p)) == (p, None), "more blanks than the first read found is fine"
    run = " ".join(f"{{{{{n}|w{n}}}}}" for n in range(16, 36))
    assert judge({"kind": "under", "qnos": list(range(16, 26))}, raw(run), raw(run))[1] == "markers differ from the questions", "the next section ran in"
    e = "A {{17|}} b {{18|x}}."
    assert judge({"kind": "under", "st": "eng-vocab-cloze", "qnos": [17, 18]}, raw(e), raw(e))[1] == "an underline lost its words"
    assert judge({"kind": "under", "st": "eng-editing", "qnos": [17, 18]}, raw(e), raw(e)) == (e, None)
    assert judge(r, raw("A {{17|x}} b {{19|y}}."), raw("A {{17|x}} b {{19|y}}."))[1] == "markers are not one run of numbers"
    assert markers("useful {{29|}} reminders", "under") == {29: ""}, "Editing: a missing word is an empty box"
    qs = [{"pages": [4]}, {"pages": [4]}, {"pages": [5]}, {"pages": [30]}, {"pages": [30]}]
    assert [len(c) for c in clusters(qs)] == [3, 2], "a jump in pages starts another paper's section"
    box = ["about", "and", "as", "been", "being", "from", "have", "however", "instead", "other"]
    assert cloze_keys("eng-grammar-cloze", "K", box) == ["other"] and cloze_keys("eng-grammar-cloze", "D (been)", box) == ["been"]
    assert cloze_keys("eng-grammar-cloze", "D (during)", box) == [], "letter and word disagree: unsure"
    assert cloze_keys("eng-comp-cloze", "make/produce", None) == ["make", "produce"]
    assert cloze_keys("eng-grammar-cloze", "(D) been", box) == ["been"] and cloze_keys("eng-comp-cloze", "(on)", None) == ["on"]
    assert cloze_keys("eng-comp-cloze", "(AVOID)", None) == [], "a capitalised word is another section's key"
    assert cloze_keys("eng-grammar-cloze", "beer", box) == [] and cloze_keys("eng-grammar-cloze", "been", box) == ["been"], "a word key must be in the box"
    lettered = list("ABCDEFGHIJ")  # a box lettered with I
    assert cloze_keys("eng-grammar-cloze", "J", box, lettered) == ["other"] and cloze_keys("eng-grammar-cloze", "I", box, lettered) == ["instead"]
    assert cloze_stem("Unlike [[29]] insects, they [[30]] die.", 30) == "Unlike (29) ____ insects, they (30) ________ die."
    assert box_ok(box) and not box_ok(box[:9]) and not box_ok(box + ["about"]) and not box_ok(box[:-1] + ["8"]), "a short, repeated or garbled box"
    assert cloze_stem("a b[[41]] c", 41).endswith("b (41) ________ c")
    print("passage selftest ok")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "pack":
        pack()
    elif cmd == "run":
        run(sys.argv[2])
    elif cmd == "check":
        check(int(sys.argv[sys.argv.index("--sample") + 1]) if "--sample" in sys.argv else 0)
    elif cmd == "cloze-final":
        cloze_final()
    elif cmd == "cloze-check":
        cloze_check()
    elif cmd == "pack-cloze":
        pack_cloze()
    elif cmd == "export-cloze":
        export_cloze()
    elif cmd == "selftest":
        selftest()
    else:
        sys.exit(__doc__)
