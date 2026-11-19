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
- Marks: Chinese uses step A (section headings are reliable, the VLM copies section totals). Other subjects use the
  VLM's printed marks when every part has one and the sum is 1-10, else step A's value."""
import argparse, json, re
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
    return out


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
        if subject != "chinese" and printed and 1 <= printed <= 10:
            marks, src = printed, "vlm_printed"
        elif a and a.get("marks") is not None:
            marks, src = a["marks"], "stepA"
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
    main()
