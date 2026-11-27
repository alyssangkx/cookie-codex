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
import collections
import json
import os
import random
import re
import sys
from pathlib import Path

TMP = Path("/data/alvin/tmp/cookie-codex")
DEV_PP = TMP / "pastpapers"
WORK = Path(os.environ.get("PP_WORK", str(TMP / "synth")))
# queue 47 (27 Nov 2026): the question numbers of the first read are sometimes wrong, so a re-read finds the question by its
# given sentence(s) alone (PP_BYSENT=1: the prompt does not name a number)
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
    """The model's JSON; when it ran out of tokens writing a dotted line as "____ ____ ____ ..." the reply is cut off, so
    the sentences and the scaffold's start are taken from the partial text. Runs of blanks become one ____."""
    m = re.search(r"\{.*\}", text or "", re.S)
    v = None
    try:
        v = json.loads(m.group(0)) if m else None
    except Exception:
        pass
    if v is None and text and '"none"' not in text:
        un = lambda x: json.loads(f'"{x}"') if x is not None else None
        se = re.search(r'"sentences"\s*:\s*"((?:[^"\\]|\\.)*)"', text)
        whole = re.search(r'"scaffold"\s*:\s*"((?:[^"\\]|\\.)*)"', text)
        part = re.search(r'"scaffold"\s*:\s*"((?:[^"\\]|\\.)*)$', text.strip())
        try:
            if se and whole:  # complete strings in a reply that failed for another reason: taken as they are
                v = {"sentences": un(se.group(1)), "scaffold": un(whole.group(1))}
            elif se and part:  # cut off inside the dotted line: only the words before the first blank are known
                lead = re.split(r"_{2,}", un(part.group(1).rstrip("\\")))[0].strip()
                v = {"sentences": un(se.group(1)), "scaffold": f"{lead} ____", "cut": True} if lead else None
        except Exception:
            v = None
    if v and isinstance(v.get("scaffold"), str):
        v["scaffold"] = re.sub(r"_{2,}(?:[\s.]*_{2,})*", "____", v["scaffold"]).strip()
    return v


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


def fits_key(answer, scaffold):
    """fits(), allowing what keys and reads do: a key that prints only the completion ("Ben commented ____" keyed "that he
    had been ..."), and a read that dropped the line's last blank ("____ whom" for "____ whom ____")."""
    # a dropped last blank ("____ whom"): only when the line does not end its sentence ("..., I still did not go." is whole)
    sc = [scaffold] + ([scaffold.rstrip() + " ____"] if not re.search(r"(_{2,}|[.!?])\s*$", scaffold) else [])
    lead = re.split(r"_{2,}", scaffold)[0].strip()
    join = lead and answer[:1].islower()  # only a true completion ("that he had ..."), never a whole other sentence
    return any(fits(answer, x) or (join and fits(f"{lead} {answer}", x)) for x in sc)


STOP = set("a an the and but or so of to in on at by for with from as is was were be been are am it he she they we i you his her "
           "their our my your him them us me that this these those not did does do had has have will would could should can".split())


def same_topic(answer, sentences):
    """The key reuses at least two content words of the given sentences (an answer from another question does not)."""
    w = lambda t: {x for x in re.findall(r"[a-z']+", norm(t)) if x not in STOP and len(x) > 2}
    return len(w(answer) & w(sentences)) >= 2


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


def prompt_for(r, bysent=False):
    """The read prompt; by sentence: "Find the question whose given sentence(s) begin ..." with no question number."""
    p = PROMPT.format(qno=r["qno"], start=r["start"].replace('"', "'"))
    if bysent:
        p = p.replace(f"Find question {r['qno']}. Its given sentence(s) begin:", "Find the question whose given sentence(s) begin:")
        p = p.replace(f"If question {r['qno']} is not on this page", "If that question is not on this page")
    return p


def run(items_file):
    from PIL import Image
    items_file = Path(items_file).resolve()
    pp = Path(os.environ.get("PP_ROOT", "/data/alvin/cookie/pastpapers_full"))
    out = items_file.with_name(os.environ.get("PP_OUT", "read.jsonl"))
    bysent = bool(os.environ.get("PP_BYSENT"))
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
    sp = SamplingParams(temperature=0, max_tokens=int(os.environ.get("PP_MAXTOK", "500")))
    with open(out, "a", encoding="utf-8") as f:
        for i in range(0, len(todo), 32):
            ch = todo[i:i + 32]
            msgs = [[{"role": "user", "content": [{"type": "image_url", "image_url": {"url": f"file://{dst}"}},
                     {"type": "text", "text": prompt_for(r, bysent)}]}] for r, _, dst in ch]
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
        if it and (r["id"] not in best or fits_key(it["answer"], v["scaffold"])):
            best[r["id"]] = v
    rows, why = [], {}
    for i, it in items.items():
        v = best.get(i)
        if not v:
            w = "not found on its pages"
        elif not re.search(r"_{2,}", v["scaffold"]):  # the same blank test as fits()
            w = "no blank in the answer line"
        elif not fits_key(it["answer"], v["scaffold"]):
            w = "the printed answer does not fit the answer line"
        elif not same_topic(it["answer"], v.get("sentences") or ""):
            w = "the printed answer is about other sentences"
        else:
            w = None
        why[w or "kept"] = why.get(w or "kept", 0) + 1
        rows.append({"id": i, "year": it["year"], "sentences": (v or {}).get("sentences"), "scaffold": (v or {}).get("scaffold"),
                     "answer": it["answer"], "ok": w is None, "why": w})
    (WORK / "checked.jsonl").write_text("".join(json.dumps(x, ensure_ascii=False) + "\n" for x in rows))
    print(f"{len(items)} questions: " + ", ".join(f"{k} {v}" for k, v in sorted(why.items(), key=lambda kv: -kv[1])))
    for x in random.Random(5).sample([r for r in rows if r["ok"]], min(sample, sum(r["ok"] for r in rows))):
        print(f"\n  {x['sentences']}\n  {x['scaffold']}\n  -> {x['answer']}")


# a comprehension question filed under S&T (the Opus check found 5): it asks about a passage, not to rewrite sentences
NOT_ST = re.compile(r"\bparagraph|\bpassage\b|according to|\bgive (?:two|one|three)\b|true or false|\bwhich (?:word|phrase|line)s?\b"
                    r"|\bin (?:the )?lines? \d|\bfrom the text\b|\bwhy did\b|\bhow did\b|\bwhat did\b", re.I)


def words(t):
    """For comparing answers: lower case, apostrophes kept, all other punctuation gone (as typed.ts norm, roughly)."""
    t = (t or "").replace("’", "'").replace("‘", "'").lower()
    t = re.sub(r"(?<![a-z0-9])'|(?<=[a-z0-9])(?<!s)'(?![a-z0-9])", " ", t)  # students' keeps its apostrophe, as on the site
    return " ".join(re.sub(r"[^a-z0-9'\s-]", " ", t).split())


def full_key(key, scaffold):
    """The school's key as a whole sentence (a completion-only key gets the lead-in in front)."""
    lead = re.split(r"_{2,}", scaffold or "")[0].strip()
    return f"{lead} {key}" if lead and key[:1].islower() and fits(f"{lead} {key}", scaffold) else key


def clean_sentences(sent, scaffold):
    """The given sentence(s) as the child sees them: no question number in front ("67 Janet was ill."), and not ending in
    the answer line's printed words, which the page reader sometimes copied in ("... my purse. My purse")."""
    t = re.sub(r"^\s*(?:Q\s*)?\d{1,3}\s*[.)]?\s+(?=[A-Za-z'\"‘“])", "", (sent or "").strip())
    t = t[:1].upper() + t[1:]  # "69 it was not easy ..." -> "It was not easy ..."
    lead = re.split(r"_{2,}", scaffold or "")[0].strip()
    if len(lead) >= 3 and t.lower().endswith(lead.lower()) and len(t) > len(lead) + 10:
        t = t[:-len(lead)].rstrip()
    return t


def school_alternatives(key, scaffold):
    """The whole sentences a school key offers: split at " / " or " OR ", each kept only when it fits the answer line."""
    parts = [p.strip() for p in re.split(r"\s+(?:/|OR)\s+(?=[A-Z\"'‘“])", key or "") if p.strip()]  # never a lowercase "or"
    return [f for f in (full_key(p, scaffold) for p in parts) if fits_key(f, scaffold) and re.search(r"[.!?][\"'’”]?$", f)] if len(parts) > 1 else []


def accept_merge():
    """The Opus agents' accepted answers (accept/out_N_partM.jsonl) joined to the questions: accept/merged.jsonl.
    Dropped: a doubt, a comprehension question, an answer list that breaks its scaffold. Marked key_changed: the first
    accepted answer differs from the school's key in more than punctuation and capitals (the agent corrected it: it ships
    only if the blind Perplexity answer agrees)."""
    import glob
    qs = {r["id"]: r for b in sorted(glob.glob(str(WORK / "accept/batch_*.jsonl"))) for r in jl(b)}
    out, why = [], collections.Counter()
    for f in sorted(glob.glob(str(WORK / "accept/out_*_part*.jsonl"))):
        for x in jl(f):
            q = qs.get(x.get("id"))
            if not q:
                why["unknown id"] += 1
                continue
            row = dict(q, sentences=clean_sentences(q["sentences"], q["scaffold"]), accept=x.get("accept"), why=x.get("why"),
                       doubt=x.get("doubt"))
            if x.get("doubt"):
                w = "doubt"
            elif NOT_ST.search(q["sentences"] or ""):
                w = "comprehension question"
            elif not (isinstance(x.get("accept"), list) and 1 <= len(x["accept"]) <= 8
                      and all(isinstance(a, str) and fits_key(a, q["scaffold"]) for a in x["accept"])):
                w = "an answer breaks the scaffold"
            else:
                w = None
                alts = school_alternatives(q["key"], q["scaffold"]) or [full_key(q["key"], q["scaffold"])]
                row["key_changed"] = words(x["accept"][0]) not in {words(a) for a in alts}
                # the school key's own alternatives ("... by the chef. / Every evening, ..." or "... OR ...") are always
                # accepted: the agents sometimes kept only the first
                have = {words(a) for a in row["accept"]}
                for alt in school_alternatives(q["key"], q["scaffold"]):
                    if words(alt) not in have and len(row["accept"]) < 8:
                        row["accept"] = row["accept"] + [alt]
                        have.add(words(alt))
            why[w or ("kept, key corrected" if row.get("key_changed") else "kept")] += 1
            row["ok"] = w is None
            row["drop"] = w
            out.append(row)
    (WORK / "accept/merged.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in out))
    print(f"{len(qs)} questions: " + ", ".join(f"{k} {v}" for k, v in why.most_common()))


PPLX_HEAD = ("Singapore PSLE English, Synthesis & Transformation. For each numbered item, combine or rewrite the given "
             "sentence(s) into ONE sentence with the same meaning. Your sentence must use the answer line exactly as printed: keep "
             "its printed words in the same order and fill each ____ with your words. Reply with one line per item and nothing else, "
             "in the form  N. <your full sentence>")


def pplx_pack(per=100):
    """Blind PDFs for Perplexity (the owner runs them): accept/perplexity/st_part_NN.pdf, with st_part_NN.ids naming each
    item's question. The answers go back as accept/perplexity/st_part_NN.txt (one "N. sentence" line per item)."""
    import html
    import subprocess
    rows = [r for r in jl(WORK / "accept/merged.jsonl") if r["ok"]]
    d = WORK / "accept/perplexity"
    d.mkdir(parents=True, exist_ok=True)
    for p in range(0, len(rows), per):
        part = rows[p:p + per]
        n = p // per + 1
        items = "".join(f"<li><p>{html.escape(r['sentences'])}</p><p class=a>Answer line: {html.escape(r['scaffold'])}</p></li>"
                        for r in part)
        page = (f"<!doctype html><meta charset=utf-8><style>body{{font:12pt/1.45 Arial,sans-serif;margin:18mm}}li{{margin:0 0 9pt}}"
                f"p{{margin:0}}.a{{font-weight:bold}}</style><p><b>Part {n}.</b> {html.escape(PPLX_HEAD)}</p><ol>{items}</ol>")
        (d / f"st_part_{n:02d}.html").write_text(page)
        (d / f"st_part_{n:02d}.ids").write_text("".join(r["id"] + "\n" for r in part))
        subprocess.run(["google-chrome", "--headless", "--no-sandbox", "--disable-gpu", "--no-pdf-header-footer",
                        f"--print-to-pdf={d / f'st_part_{n:02d}.pdf'}", (d / f"st_part_{n:02d}.html").as_uri()],
                       check=True, capture_output=True, timeout=120)
    print(f"{len(rows)} questions in {-(-len(rows) // per)} PDFs -> {d}")


def pplx_check():
    """Perplexity's blind answers against the accepted lists: confirmed when its sentence is one of them (as the site marks).
    A corrected key (key_changed) ships only when confirmed; a school key ships unless Perplexity disagrees AND writes a
    sentence that fits the scaffold (then both go to the owner). Writes accept/final.jsonl (what ships) and
    accept/review.jsonl (for the owner)."""
    import glob
    rows = {r["id"]: r for r in jl(WORK / "accept/merged.jsonl") if r["ok"]}
    got = {}
    for f in sorted(glob.glob(str(WORK / "accept/perplexity/st_part_*.ids"))):
        ids = Path(f).read_text().split()
        ans = Path(f[:-4] + ".txt")
        if not ans.exists():
            continue
        for m in re.finditer(r"^\s*(\d{1,3})[.)]\s*(.+?)\s*$", ans.read_text(encoding="utf-8"), re.M):
            k = int(m.group(1)) - 1
            if 0 <= k < len(ids):
                got[ids[k]] = m.group(2)
    final, review, why = [], [], collections.Counter()
    for i, r in rows.items():
        a = got.get(i)
        # Perplexity validates the key: any trivial variant of it confirms (that / no that ...). A corrected key is never
        # confirmed by Perplexity writing the school's original key (the review's point): those sentences do not count
        orig = {words(x) for x in [full_key(r["key"], r["scaffold"]), *school_alternatives(r["key"], r["scaffold"])]}
        confirm = {words(x) for x in r["accept"]} - (orig if r.get("key_changed") else set())
        same = a is not None and words(a) in confirm
        if a is None:
            w = "no Perplexity answer yet"
        elif same:
            w = "confirmed"
        elif r.get("key_changed"):
            w = "corrected key not confirmed"
        elif fits_key(a, r["scaffold"]):
            w = "Perplexity wrote another sentence"
        else:
            w = "Perplexity broke the answer line"  # its slip: the school key stands
        why[w] += 1
        if w in ("confirmed", "Perplexity broke the answer line"):  # an unanswered one waits (review), never ships unchecked
            final.append(r)
        else:
            review.append(dict(r, perplexity=a, why_review=w))
    (WORK / "accept/final.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in final))
    (WORK / "accept/review.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in review))
    print(f"{len(rows)} questions: " + ", ".join(f"{k} {v}" for k, v in why.most_common()) + f" -> ship {len(final)}, review {len(review)}")


ST_OUT = TMP / "ppimport" / "engst"


def fills(answer, scaffold):
    """Strict, as the site's boxes are: the answer is the printed words in order with at least one word typed in every
    blank (fits() is looser: it tolerates the reads' slips)."""
    parts = re.split(r"_{2,}", scaffold or "")
    if len(parts) < 2:
        return False
    sep = lambda p: r"\s+".join(map(re.escape, p.split()))
    pat = "".join(sep(p) + (r"\s*(\S.*?)\s*" if i < len(parts) - 1 else "") for i, p in enumerate(parts))
    a = re.sub(r"[.!?][\"'’”]?\s*$", "", (answer or "").strip())
    pat = re.sub(r"(\\[.!?])+$", "", pat)
    m = re.fullmatch(r"\s*" + pat + r"[.!?]?\s*", a, re.I)
    return bool(m) and all(re.search(r"\w", g) for g in m.groups())


TIME_WORDS = [(r"\b([Tt])he next (day|morning|afternoon|evening|night|week|month|year)\b", r"\1he following \2"),
              (r"\b([Tt])he day after(?! tomorrow)\b", r"\1he following day"),
              (r"\b([Tt])he (day|night|morning|afternoon|evening|week|month|year) before(?! yesterday| last)\b", r"\1he previous \2")]


def time_words(t, scaffold=""):
    """Owner, 24 Nov 2026: in reported speech "the previous day" and "the following day" are always used. Kept as is when
    the answer line itself prints the other phrase (the child must keep printed words)."""
    for a, b in TIME_WORDS:
        if not re.search(a, scaffold or ""):
            t = re.sub(a, b, t)
    return t


def site_scaffold(sc, final=True):
    """The answer line as the site shows it: spaces around each blank, and a final blank when the read dropped it ("____ whom"
    is "____ whom ____": the child must be able to type the rest of the sentence)."""
    t = re.sub(r"(?<!_)_{2,}(?!_)", "\x00", sc or "")  # each whole run of underscores is one blank
    t = re.sub(r"\s*\x00(?!['’]s\b)\s*", " ____ ", t)
    t = re.sub(r"\s*\x00", " ____", t).strip()  # "____'s" keeps the possessive attached
    t = re.sub(r" ____ ([,.;:!?])", r" ____\1", t)
    return t if not final or re.search(r"(_{2,}|[.!?][\"'’”]?)$", t) else t + " ____"


def export():
    """The shipping S&T questions as a load_pp selection (ST_OUT/english/selected.jsonl, explain.jsonl): typed rows
    (migration 015), strictly the school key (or its confirmed correction), the key's own alternatives and the owner's
    answers (accept/owner.jsonl); a disagreement ships only when the judge passed it (accept/judge.jsonl).
    One copy of each question (same given sentences and answer line), the earliest by year then id, counted as `repeat`.
    Then:  load_pp.py upload --subject english --out ST_OUT --subtopics eng-synthesis [--apply]"""
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from load_pp import pp_id, LEVEL
    from explain import fp as explain_fp
    judge = {j["id"]: j for j in jl(WORK / "accept/judge.jsonl")}
    owner = collections.defaultdict(list)
    for o in jl(WORK / "accept/owner.jsonl"):
        owner[o["src_id"]].append(o["answer"])
    review = {r["id"] for r in jl(WORK / "accept/review.jsonl")}
    final = {r["id"] for r in jl(WORK / "accept/final.jsonl")}
    meta = {}
    for y in range(2018, 2027):
        base = TMP / "pastpapers" / "english" / str(y)
        tags = {t["id"]: t for t in jl(base / "tags72.jsonl")}
        for q in jl(base / "merged.jsonl"):
            meta[q["id"]] = dict(q, difficulty=(tags.get(q["id"]) or {}).get("difficulty"))
    rows = []
    for r in jl(WORK / "accept/merged.jsonl"):
        if not r["ok"] or (r["id"] not in final and r["id"] not in review):
            continue
        j = judge.get(r["id"])
        if r["id"] in review and not (j and j.get("accept_ok") is True):
            continue  # disagreed and not judged yet, or the judge refused the accepted answers: waits
        # owner, 24 Nov 2026: "in most cases it is strictly one answer": the school's key (accept[0]: the key, or its
        # correction confirmed by Perplexity or the judge) and only the alternatives the key itself prints; the variants the
        # agents and Perplexity offered are not accepted. Time words follow the owner's rule (the previous / following ...)
        acc = []
        # the owner's own answer (accept/owner.jsonl, from the spot checks) comes first; the school's key stays accepted
        for a in [*owner.get(r["id"], []), r["accept"][0], *school_alternatives(r["key"], r["scaffold"])]:
            a = time_words(a, r["scaffold"])
            if words(a) not in {words(x) for x in acc}:
                acc.append(a)
        # the answer line as shown; a final blank is added back only when the answers need one ("____ whom" lost its last
        # blank; "My purse ____ by one of the cleaners" only lost its full stop)
        sc = site_scaffold(r["scaffold"], final=False)
        if not any(fills(a, sc) for a in acc):
            sc = site_scaffold(r["scaffold"])
        acc = [a for a in acc if fills(a, sc)]  # every box gets words (a misread line with an extra blank fits none)
        if not acc:
            print(f"  dropped {r['id']}: no accepted answer fills the answer line {r['scaffold']!r}")
        if not acc:
            continue
        m = meta.get(r["id"], {})
        d = m.get("difficulty") if isinstance(m.get("difficulty"), int) else 2
        rows.append({"id": pp_id(r["id"]), "src_id": r["id"],
                     **{"scaffold_raw": r["scaffold"]}, "subject": "english", "subtopic": "eng-synthesis",
                     "level": LEVEL.get(d, "intermediate"), "difficulty": d, "pattern": None, "stem": r["sentences"],
                     "options": [], "answer": 0, "crops": [], "year": m.get("year") or int(r["id"].split("-")[1]),
                     "school": m.get("school"), "paper": m.get("paper"), "qno": m.get("qno"), "marks": m.get("marks"),
                     "blind_src": "opus+perplexity", "kind": "typed", "accept": acc, "scaffold": sc, "why": r.get("why")})
    groups = collections.defaultdict(list)
    for x in rows:
        groups[(words(x["stem"]), words(x["scaffold"]))].append(x)
    keep = []
    for g in groups.values():
        g.sort(key=lambda x: (x["year"] or 9999, x["src_id"]))
        g[0]["repeat"] = len(g)
        merged = []  # the copies' accepted answers together (an owner answer may sit on a later copy), owner's first
        for x in sorted(g, key=lambda x: not any(x["src_id"] == o for o in owner)):
            for a in x["accept"]:
                if words(a) not in {words(m) for m in merged} and fills(a, g[0]["scaffold"]):
                    merged.append(a)
        g[0]["accept"] = merged[:8]
        keep.append(g[0])
    out = ST_OUT / "english"
    out.mkdir(parents=True, exist_ok=True)
    (out / "selected.jsonl").write_text("".join(json.dumps({k: v for k, v in x.items() if k not in ("why", "scaffold_raw")}, ensure_ascii=False) + "\n" for x in keep))
    (out / "explain.jsonl").write_text("".join(json.dumps({"id": x["id"], "fp": explain_fp(x), "explain": {"right": x["why"], "wrong": []}},
                                                          ensure_ascii=False) + "\n" for x in keep if x.get("why")))
    lv = collections.Counter(x["level"] for x in keep)
    print(f"{len(rows)} shipping, {len(keep)} after duplicates ({sum(x['repeat'] > 1 for x in keep)} in 2+ papers); levels {dict(lv)} -> {out}")


def selftest_prompt():
    r = {"qno": 41, "start": 'Tom ran "fast".'}
    assert "question 41" in prompt_for(r) and "41" not in prompt_for(r, True) and "Find the question whose" in prompt_for(r, True)


def selftest():
    assert fits("However hard Julia tried to persuade me, I still did not go to the party.", "However ____, I still did not go to the party.")
    assert fits("Unless everyone drinks as little as possible, we will run out of water.", "Unless ____.")
    assert fits("The librarian asked me if I had placed the book back on that shelf.", "The librarian asked me ____.")
    assert fits("We will run out of water unless everyone drinks as little as possible.", "____ unless ____.")
    assert not fits("The bird pecked at it suddenly and had it.", "However ____, I still did not go to the party.")
    assert not fits("Anything at all.", "No blank here.")
    assert fits_key("that he had been preparing all evening.", "Ben commented ____")
    assert fits_key("The zookeeper, whom the elephant attacked, was very experienced.", "____ whom")
    assert not fits_key("I ate fried rice for dinner last night.", "____ prefers ____"), "an answer from another question"
    assert not fits_key("Sally said that she had run to school.", "Her ____"), "a whole sentence is never joined to the lead-in"
    assert same_topic("Owing to her illness, Janet could not sing.", "Janet was ill. She was unable to sing at the concert.")
    assert not same_topic("Mrs Lee prefers walking to driving.", "Aziz was committed to studying hard.")
    assert NOT_ST.search("Give two reasons from paragraph 2 why Ken was sad.") and not NOT_ST.search("Ken was sad. He cried.")
    assert clean_sentences("66 One of the cleaners found my purse. My purse", "My purse ____") == "One of the cleaners found my purse."
    assert clean_sentences("67 Janet was ill. She was unable to sing.", "Owing to ____") == "Janet was ill. She was unable to sing."
    assert clean_sentences("He has 3 cats. He likes them.", "Having ____") == "He has 3 cats. He likes them.", "a number inside stays"
    assert clean_sentences("69 it was not easy to stay awake.", "Staying ____") == "It was not easy to stay awake."
    assert full_key("that he had been preparing all evening.", "Ben commented ____") == "Ben commented that he had been preparing all evening."
    assert words("The students’ bags, he said.") == "the students' bags he said"
    assert site_scaffold("____ whom") == "____ whom ____" and site_scaffold("Much to____") == "Much to ____"
    assert fills("However hard Julia tried, I still did not go.", "However ____, I still did not go.")
    assert time_words("He said he would come the next day and had left the day before.") == "He said he would come the following day and had left the previous day."
    assert time_words("The next day, she left.") == "The following day, she left."
    assert time_words("He came the day before yesterday.") == "He came the day before yesterday."
    assert time_words("We left the next day.", "We left the next day ____") == "We left the next day.", "a printed phrase stays"
    assert school_alternatives("You must hurry or I will leave without you.", "____.") == [], "a lowercase or is not a separator"
    assert site_scaffold("The ____'s bag was lost.") == "The ____'s bag was lost."
    assert site_scaffold("My purse ____ by one of the cleaners", final=False) == "My purse ____ by one of the cleaners"
    assert not fills("David would rather read than play computer games.", "David ____ would rather ____."), "a box left empty"
    assert not fills("Your phone will run out unless you charge it fully.", "____ unless you charge it fully ____."), "a trailing box left empty"
    assert site_scaffold("However ____, I still did not go.") == "However ____, I still did not go."
    assert school_alternatives("Meals are made by the chef every evening. / Every evening, meals are made by the chef.", "Every evening ____") == ["Every evening, meals are made by the chef."], "only the alternative that fits the answer line"
    assert len(school_alternatives("Delicious meals are prepared by the chef. / Delicious meals were prepared by the chef.", "Delicious meals ____")) == 2
    cut = '```json { "sentences": "Janet was ill. She was unable to sing at the concert.", "scaffold": "Owing to ____ ____ ____ ____ __'
    assert parse(cut)["scaffold"] == "Owing to ____" and fits("Owing to her illness, Janet was unable to sing at the concert.", parse(cut)["scaffold"])
    assert parse('{"sentences": "x", "scaffold": "However _____ _____ _____, I still went."}')["scaffold"] == "However ____, I still went."
    junk = parse('{"sentences":"Tom ran.","scaffold":"However ____, I still went."} and then {x}')
    assert junk["scaffold"] == "However ____, I still went." and not junk.get("cut"), "a whole reply is never treated as cut"
    assert parse('{"sentences": "x", "scaffold": "____ ____ ____') is None, "cut before any printed word: unusable"
    assert not fits_key("However hard I tried, I still did not go to the party because I was sick.", "However ____, I still did not go to the party.")
    selftest_prompt()
    print("synth selftest ok")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "pack":
        pack()
    elif cmd == "run":
        run(sys.argv[2])
    elif cmd == "check":
        check(int(sys.argv[sys.argv.index("--sample") + 1]) if "--sample" in sys.argv else 0)
    elif cmd == "pplx-pack":
        pplx_pack()
    elif cmd == "pplx-check":
        pplx_check()
    elif cmd == "export":
        export()
    elif cmd == "accept-merge":
        accept_merge()
    elif cmd == "selftest":
        selftest()
    else:
        sys.exit(__doc__)
