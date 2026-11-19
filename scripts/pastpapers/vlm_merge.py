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
- Marks: step A's value first (section rules are reliable; the VLM copies section labels and totals). With no step A
  value, other subjects use the VLM's printed marks when every part has one and the sum is 1-10; Chinese gets none."""
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
    else the longer text, with both pages. Numbers that restart in a later booklet are pages apart and stay."""
    keep = []
    for o in out:
        twin = next((k for k in reversed(keep[-12:]) if k["qno"] == o["qno"] and 1 <= min(o["pages"]) - max(k["pages"]) <= 2), None)
        if twin is None: keep.append(o); continue
        score = lambda q: (len(q["options"]), sum(len(p["text"]) for p in q["parts"]))
        best = o if score(o) > score(twin) else twin
        keep[keep.index(twin)] = {**best, "pages": sorted(set(twin["pages"]) | set(o["pages"]))}
    return keep


def _selftest():
    q = lambda n, pg, opts=0, text="x": {"qno": n, "parts": [{"text": text}], "options": ["o"] * opts, "pages": [pg]}
    got = dedupe([q(21, 92, text="instruction"), q(22, 92), q(21, 93, 4, "real"), q(22, 93, 4), q(1, 98), q(1, 99, 4)])
    assert [(g["qno"], g["pages"], len(g["options"])) for g in got] == [(21, [92, 93], 4), (22, [92, 93], 4), (1, [98, 99], 4)]
    assert len(dedupe([q(1, 3), q(1, 12)])) == 2  # booklet B restarts at 1
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
    used, out = set(), []
    for j, v in enumerate(vq):
        a = stepa[pair[j]] if j in pair else None
        if a: used.add(pair[j])
        pm = [p["marks"] for p in v["parts"]]
        printed = sum(pm) if pm and all(m is not None for m in pm) else None
        # step A first: on the 2026 maths truth papers it was right 29 times where the VLM was wrong, and wrong 5 times
        # where the VLM was right (the VLM often copies a section's "2 marks each" label onto every question)
        if a and a.get("marks") is not None:
            marks, src = a["marks"], "stepA"
        elif subject != "chinese" and printed and 1 <= printed <= 10:
            marks, src = printed, "vlm_printed"
        else:
            marks, src = None, None  # a printed sum outside 1-10, or any Chinese one, is a section total, not trusted
        text = "\n".join((f"({p['sub']}) " if p["sub"] and p["sub"] != "null" else "") + p["text"] for p in v["parts"])
        out.append({"id": a["id"] if a else f"{paper['paper_id']}-v{j:03d}", "paper": paper["paper_id"],
                    "school": paper.get("school"), "exam": paper.get("exam"), "qno": v["qno"],
                    "part": a.get("part") if a else None, "section": a.get("section") if a else None,
                    "format": (a.get("format") if a else None) or ("mcq" if len(v["options"]) >= 3 else "open"),
                    "marks": marks, "marks_from": src, "stepA_marks": a.get("marks") if a else None,
                    "text": text, "options": v["options"], "figures": v["figures"], "pages": v["pages"],
                    "parts": len(v["parts"]), "flags": [] if a else ["vlm_only"]})
    for i, a in enumerate(stepa):
        if i not in used:
            out.append({**{k: a.get(k) for k in ("id", "paper", "school", "exam", "qno", "part", "section", "format",
                                                  "marks", "text", "pages")},
                        "marks_from": "stepA", "stepA_marks": a.get("marks"), "options": [], "figures": [],
                        "parts": None, "flags": ["stepA_only"]})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--subject", required=True); ap.add_argument("--year", type=int, required=True)
    ap.add_argument("--tag", default="vlm32")
    a = ap.parse_args()
    base = OUT / a.subject / str(a.year)
    qs = [json.loads(l) for l in open(base / "questions.jsonl")]
    papers = [json.loads(l) for l in open(base / "papers.jsonl")]
    n = {"questions": 0, "vlm_only": 0, "stepA_only": 0}
    with open(base / "merged.jsonl", "w") as f:
        for p in papers:
            for r in merge_paper(a.subject, p, [q for q in qs if q["paper"] == p["paper_id"]], base / a.tag):
                n["questions"] += 1
                for fl in r["flags"]: n[fl] += 1
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(a.subject, a.year, n)


if __name__ == "__main__":
    _selftest() if sys.argv[1:2] == ["selftest"] else main()
