#!/usr/bin/env python3
"""Merge step A (paper boundaries, sections, marks rules) with the VLM page reads (text, question numbers, options,
printed per-part marks) into one question list per subject and year.

  python3 scripts/pastpapers/vlm_merge.py --subject maths --year 2026 [--tag vlm32]
  -> <OUT>/<subject>/<year>/merged.jsonl, one record per question; flags say where each value came from.

Rules (ponytail: plain rules from the 2026 pilot; revisit when the truth scores say so):
- Pages: a paper's first..last pages minus step A's answer, answer-booklet, composition and non-question pages. VLM
  questions on a page where step A found none and the VLM calls it a cover are cover instructions: dropped.
- One question per printed number: consecutive entries with the same number are its parts; "cont" joins the previous.
- The VLM and step A number sequences are aligned (longest common subsequence). Matched questions keep step A's id,
  section and format.
- Marks: step A's value first (section rules are reliable; the VLM copies section labels and totals), except Science
  open questions, where the VLM's printed per-part sum (every part has one, sum 1-10) comes first. With no step A value:
  an MCQ takes the paper's usual MCQ mark; other questions (not Chinese) the VLM's printed sum, else none."""
import argparse, json, re, sys
from difflib import SequenceMatcher
from pathlib import Path

OUT = Path("/data/alvin/tmp/cookie-codex/pastpapers")


def qnum(q):
    m = re.match(r"\D*(\d+)", str(q.get("qno") or ""))
    return int(m.group(1)) if m else None


def num(v):
    m = re.search(r"\d+(\.\d+)?", str(v if v is not None else ""))
    return float(m.group(0)) if m else None


def vlm_questions(vdir, pages, stepa_pages):
    """-> [{qno, parts: [{sub, text, marks}], options, figures, pages}] in page order."""
    out = []
    for pg in pages:
        f = vdir / f"p{pg:04d}.json"
        if not f.exists(): continue
        d = json.loads(f.read_text())
        if "error" in d or d.get("kind") == "answers": continue
        if d.get("kind") == "cover" and pg not in stepa_pages: continue
        for q in d.get("questions") or []:
            n = qnum(q)
            part = {"sub": q.get("sub"), "text": (q.get("text") or "").strip(), "marks": num(q.get("marks"))}
            if n is None or (out and out[-1]["qno"] == n):
                if not out: continue
                o = out[-1]
            else:
                o = {"qno": n, "parts": [], "options": [], "figures": [], "pages": []}
                out.append(o)
            o["parts"].append(part)
            o["options"] += [x for x in (q.get("options") or []) if isinstance(x, str)]
            if q.get("figure"): o["figures"].append(q["figure"])
            if pg not in o["pages"]: o["pages"].append(pg)
    return dedupe(out)


def dedupe(out):
    """A passage page often lists the question numbers it serves (the section instruction read once per number), and
    the questions follow on the next page or the one after: one qno within 2 pages is one question. Keep the copy with options,
    else the longer text, with both pages. Only a weak copy is folded in: no options, and its text is under 15
    characters or repeated by another entry on the same page (the instruction line). A section that restarts at 1 on
    the next page has real, different questions, so both stay."""
    seen = {}
    for o in out:
        t = "".join(p["text"] for p in o["parts"]).strip()
        seen[(o["pages"][0], t)] = seen.get((o["pages"][0], t), 0) + 1
    def weak(q):
        t = "".join(p["text"] for p in q["parts"]).strip()
        return not q["options"] and (len(t) < 15 or seen.get((q["pages"][0], t), 0) > 1)
    keep = []
    for o in out:
        lo = max(0, len(keep) - 12)
        ti = next((i for i in range(len(keep) - 1, lo - 1, -1) if keep[i]["qno"] == o["qno"]
                   and 1 <= min(o["pages"]) - max(keep[i]["pages"]) <= 2 and (weak(keep[i]) or weak(o))), None)
        if ti is None: keep.append(o); continue
        twin = keep[ti]
        score = lambda q: (not weak(q), len(q["options"]), sum(len(p["text"]) for p in q["parts"]))
        best = o if score(o) > score(twin) else twin
        keep[ti] = {**best, "pages": sorted(set(twin["pages"]) | set(o["pages"]))}
    return keep


def _selftest():
    q = lambda n, pg, opts=0, text="x": {"qno": n, "parts": [{"text": text}], "options": ["o"] * opts, "pages": [pg]}
    got = dedupe([q(21, 92, text="instruction"), q(22, 92), q(21, 93, 4, "real"), q(22, 93, 4), q(1, 98), q(1, 99, 4)])
    assert [(g["qno"], g["pages"], len(g["options"])) for g in got] == [(21, [92, 93], 4), (22, [92, 93], 4), (1, [98, 99], 4)]
    assert len(dedupe([q(1, 3), q(1, 12)])) == 2  # booklet B restarts at 1
    assert len(dedupe([q(1, 3, 4, "Real question one"), q(1, 4, 4, "Another real question")])) == 2  # section restarts next page
    qs = [{"qno": n, "pages": [pg], "format": f} for n, pg, f in [(1, 3, "mcq"), (2, 3, "mcq"), (3, 4, "open"), (1, 9, "open"), (2, 9, "open")]]
    attach_answers(qs, [(1, "A"), (2, "B"), (3, "x = 7"), (1, "(a) 5; (b) 6"), (2, "7 cm")])  # booklet B restarts at 1
    assert [q["answer"] for q in qs] == ["A", "B", "x = 7", "(a) 5; (b) 6", "7 cm"]
    mc = [{"qno": 1, "pages": [3], "format": "mcq"}, {"qno": 2, "pages": [3], "format": "mcq"}]
    attach_answers(mc, [(1, "Let n be the boxes. 8n < 50"), (2, "y = 7")])  # another paper's working: no option, no answer
    assert [q["answer"] for q in mc] == [None, None]
    sa = [{"qno": 1, "pages": [3], "format": "mcq"}, {"qno": 16, "pages": [5], "format": "open"}, {"qno": 7, "pages": [6], "format": "match"}]
    attach_answers(sa, [(1, "3"), (16, "4"), (7, "B")])  # a short answer "4" and a match letter reach the open pass
    assert [q["answer"] for q in sa] == ["3", "4", "B"]
    print("vlm_merge selftest ok")


def merge_paper(subject, paper, stepa, vdir):
    skip = set(paper.get("answer_pages") or []) | set(paper.get("answer_booklet_pages") or []) \
        | set(paper.get("composition_pages") or []) | set(paper.get("non_question_pages") or [])
    pages = [p for p in range(paper["first_page"], paper["last_page"] + 1) if p not in skip]
    stepa_pages = {p for q in stepa for p in q["pages"]}
    vq = vlm_questions(vdir, pages, stepa_pages)
    sm = SequenceMatcher(None, [q["qno"] for q in stepa], [q["qno"] for q in vq], autojunk=False)
    pair = {}
    for blk in sm.get_matching_blocks():
        for k in range(blk.size): pair[blk.b + k] = blk.a + k
    mm = [q["marks"] for q in stepa if q.get("format") == "mcq" and q.get("marks") is not None]
    mcq_mark = max(set(mm), key=mm.count) if mm else None
    used, out, key = set(), [], []
    for j, v in enumerate(vq):
        a = stepa[pair[j]] if j in pair else None
        if a: used.add(pair[j])
        pm = [p["marks"] for p in v["parts"]]
        printed = sum(pm) if pm and all(m is not None for m in pm) else None
        # Step A first, except Science open questions. Where the two disagree on the 2026 truth papers: maths step A
        # right 29 vs VLM 5 (the VLM copies "2 marks each" labels); science open VLM right 8 vs step A 1 (step A moves
        # a part's [n] to the next question). An MCQ with no step A mark takes the paper's usual MCQ mark.
        fmt = (a.get("format") if a else None) or ("mcq" if len(v["options"]) >= 3 else "open")
        if subject == "science" and fmt != "mcq" and printed and 1 <= printed <= 10:
            marks, src = printed, "vlm_printed"
        elif a and a.get("marks") is not None:
            marks, src = a["marks"], "stepA"
        elif fmt == "mcq" and mcq_mark:
            marks, src = mcq_mark, "paper_mcq_mode"
        elif subject != "chinese" and printed and 1 <= printed <= 10:
            marks, src = printed, "vlm_printed"
        else:
            marks, src = None, None  # a printed sum outside 1-10, or any Chinese one, is a section total, not trusted
        text = "\n".join((f"({p['sub']}) " if p["sub"] and p["sub"] != "null" else "") + p["text"] for p in v["parts"])
        vid = f"{paper['paper_id']}-p{v['pages'][0]:04d}-q{v['qno']}"  # stable across re-merges (not a list position)
        n = sum(1 for r in out if r["id"] == vid or r["id"].startswith(vid + "-"))
        vid += f"-{n}" if n else ""
        out.append({"id": a["id"] if a else vid, "paper": paper["paper_id"],
                    "school": paper.get("school"), "exam": paper.get("exam"), "qno": v["qno"],
                    "part": a.get("part") if a else None, "section": a.get("section") if a else None,
                    "format": fmt,
                    "marks": marks, "marks_from": src, "stepA_marks": a.get("marks") if a else None, "vlm_marks": printed,
                    "text": text, "options": v["options"], "figures": v["figures"], "pages": v["pages"],
                    "parts": len(v["parts"]), "flags": [] if a else ["vlm_only"]})
        key.append(j)
    a2v = {i: j for j, i in pair.items()}
    for i, a in enumerate(stepa):
        if i not in used:  # reading order: right after the nearest earlier step A question that was matched
            prev = max((k for k in a2v if k < i), default=None)
            key.append((a2v[prev] if prev is not None else -1) + (i - (prev if prev is not None else -1)) / 1000)
            out.append({**{k: a.get(k) for k in ("id", "paper", "school", "exam", "qno", "part", "section", "format",
                                                  "marks", "text", "pages")},
                        "marks_from": "stepA", "stepA_marks": a.get("marks"), "vlm_marks": None, "options": [], "figures": [],
                        "parts": None, "flags": ["stepA_only"]})
    out = [r for _, r in sorted(zip(key, out), key=lambda x: x[0])]
    attach_answers(out, key_answers(vdir, paper))
    return out


ANS_TAG = "ans32"


def key_answers(vdir, paper):
    """The VLM's answer-key pages (and step A's answer pages) for this paper, in page order -> [(qno, "answer")], parts joined:
    26a "18" + 26b "$60" -> (26, "(a) 18; (b) $60")."""
    rows, worked, keypages = [], [], set(paper.get("answer_pages") or [])
    for pg in sorted(set(range(paper["first_page"], paper["last_page"] + 1)) | keypages):
        f = vdir / f"p{pg:04d}.json"
        if not f.exists(): continue
        d = json.loads(f.read_text())
        af = vdir.parent / ANS_TAG / f.name  # the answer-only re-read (vlm_read --page-list) wins where it exists
        if af.exists() and "error" not in (ad := json.loads(af.read_text())):
            d, keypages = ad, keypages - {pg}
        # worked-solution pages (step A's answer_pages) come back as kind "questions" with the solution as the text
        entries = [(a, rows) for a in (d.get("answers") or [] if d.get("kind") == "answers" else [])]
        if pg in keypages and d.get("kind") in ("answers", "questions"):
            entries += [({"qno": q.get("qno"), "sub": q.get("sub"), "answer": q.get("text")}, worked) for q in d.get("questions") or []]
        for a, into in entries:
            m = re.match(r"\D*(\d+)\s*\(?([a-z]{1,4})?", str(a.get("qno") or ""))
            if not m or not str(a.get("answer") or "").strip(): continue
            sub = (m.group(2) or str(a.get("sub") or "").strip("() ") or "").lower()
            into.append((pg, len(rows) + len(worked), int(m.group(1)), sub, str(a["answer"]).strip()))  # page, reading order
    # ponytail: a worked solution only fills a number the short key lacks; a second booklet's restarted numbers that
    # the key already has (1, 2 ...) lose their worked solution. The answer-page re-read (ANS_TAG) makes this rare.
    have = {r[2] for r in rows}
    rows = [r[2:] for r in sorted(rows + [w for w in worked if w[2] not in have])]
    out = []
    for n, sub, ans in rows:
        text = f"({sub}) {ans}" if sub else ans
        if out and out[-1][0] == n: out[-1] = (n, out[-1][1] + "; " + text)
        else: out.append((n, text))
    return out


OPTION = re.compile(r"\(?[1-4A-Da-d]\)?\.?")


def attach_answers(qs, keys):
    """Align key answers to questions by question number in order (handles a second booklet restarting at 1). MCQs
    first, and only with option-like answers ("3", "(B)", or one of that paper's option texts): a run of 1, 2, 3 ...
    matches any other run, and on 2026 maths a paper's MCQs had picked up another paper's worked solutions. Every key
    the MCQ pass did not use (including a short answer like "4") is then aligned to the other questions."""
    for q in qs: q["answer"] = None
    order = range(len(qs))  # merge_paper returns questions in reading order
    mi = [i for i in order if qs[i].get("format") == "mcq"]
    opts = {o.strip() for i in mi for o in qs[i].get("options") or []}
    used = set()
    for qi, ok in ((mi, lambda a: bool(OPTION.fullmatch(a.strip())) or a.strip() in opts),
                   ([i for i in order if qs[i].get("format") != "mcq"], lambda a: True)):
        ks = [k for k, (_, a) in enumerate(keys) if k not in used and ok(a)]
        sm = SequenceMatcher(None, [qs[i]["qno"] for i in qi], [keys[k][0] for k in ks], autojunk=False)
        for b in sm.get_matching_blocks():
            for j in range(b.size):
                qs[qi[b.a + j]]["answer"] = keys[ks[b.b + j]][1]; used.add(ks[b.b + j])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--subject", required=True); ap.add_argument("--year", type=int, required=True)
    ap.add_argument("--tag", default="vlm32")
    ap.add_argument("--ans-tag", default="ans32", help="folder of the answer-page re-read, used where present")
    a = ap.parse_args()
    global ANS_TAG
    ANS_TAG = a.ans_tag
    base = OUT / a.subject / str(a.year)
    qs = [json.loads(l) for l in open(base / "questions.jsonl")]
    papers = [json.loads(l) for l in open(base / "papers.jsonl")]
    n = {"questions": 0, "vlm_only": 0, "stepA_only": 0}
    ids = {}  # step A can repeat an id (two booklets with one label): suffix repeats in reading order so ids stay unique
    with open(base / "merged.jsonl", "w") as f:
        for p in papers:
            for r in merge_paper(a.subject, p, [q for q in qs if q["paper"] == p["paper_id"]], base / a.tag):
                k = ids[r["id"]] = ids.get(r["id"], 0) + 1
                if k > 1: r["id"] += f"-dup{k}"
                n["questions"] += 1
                for fl in r["flags"]: n[fl] += 1
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(a.subject, a.year, n)


if __name__ == "__main__":
    _selftest() if sys.argv[1:2] == ["selftest"] else main()
