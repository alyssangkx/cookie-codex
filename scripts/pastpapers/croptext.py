"""Text check of past-paper figure crops (21 Nov 2026; replaces the vision-model crop check, whose gate failed: the model called
every crop complete). Each crop is located on its page scan (load_pp.locate, grown as `load_pp figures` grows it) and the
tesseract words inside it (pages/pNNNN.tsv) are checked:
  another-question    a line inside the crop starts with a question number other than the item's own (plain "12" or
                      "12.", not an option label "(1)") and carries text: the crop holds another question (tester: pp-22f8bc3801)
  two-option-sets     two or more lines start with "(1)": a second question's options are in the crop
  options-table-only  every word of 3+ letters in the crop is an option word: the crop is the options table and the
                      figure the stem refers to is missing (tester: pp-7c736161cb)
  croptext.py check [--out DIR] [--subject science] [--gate]   -> OUT/<subject>/croptext.jsonl {id, n, flags}
  croptext.py selftest
A review list, not automatic holds: every flag is looked at by eye before an item is held (a crop with its drawing AND an
options table whose labels are single letters, or a numbered table row of the item's own, can be flagged too).
A crop that cannot be placed on its page is flagged "unplaced" (unchecked, not clean).
Prints ids, counts and flag names only (no paper text)."""
import argparse, collections, json, re, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import load_pp as L  # noqa: E402

DEF_OUT = Path("/data/alvin/tmp/cookie-codex/ppimport/sci1826b")
GATE = {"pp-22f8bc3801": True, "pp-7c736161cb": True, "pp-87af45c055": False, "pp-17f298d774": False, "pp-0909f7367a": False}
QNUM = re.compile(r"^(\d{1,2})\.?$")
WORD = re.compile(r"[A-Za-z]{3,}")


def words_of(tsv):
    """Tesseract level-5 words: (left, top, right, bottom, block, par, line, text)."""
    out = []
    for ln in open(tsv, encoding="utf-8", errors="replace").read().splitlines()[1:]:
        f = ln.split("\t")
        if len(f) < 12 or f[0] != "5" or not f[11].strip():
            continue
        x, y, w, h = map(int, f[6:10])
        out.append((x, y, x + w, y + h, f[2], f[3], f[4], f[11].strip()))
    return out


def crop_box(src):
    """(page tsv, box) of the crop as uploaded (grown when its ink touched an edge), or None when it cannot be placed."""
    import numpy as np
    from PIL import Image
    m = re.search(r"-p(\d+)\.png$", str(src))
    if not m:
        return None
    base = Path(src).parent.parent / "pages"
    page_f, tsv = base / f"p{m.group(1)}.jpg", base / f"p{m.group(1)}.tsv"
    if not page_f.exists() or not tsv.exists():
        return None
    with Image.open(src) as im:
        g = np.asarray(im.convert("L"))
    with Image.open(page_f) as pi:
        page = np.asarray(pi.convert("L"))
    pos = L.locate(page, g)
    if pos is None:
        return None
    h, w = g.shape
    box = (pos[0], pos[1], pos[0] + w, pos[1] + h)
    if any(L.touches(g).values()):
        grown_box, grown = L.grow_to_whitespace(page, box)
        if grown:
            box = grown_box
    return tsv, box


POINTS = re.compile(r"\b(identif\w*|label\w*|shown|diagram|below|picture|figure)\b", re.I)


def flags_for(words, box, qno, options, stem=""):
    """words: [(l, t, r, b, block, par, line, text)] of the page; box (x0, y0, x1, y1)."""
    x0, y0, x1, y1 = box
    inside = [w for w in words if x0 <= (w[0] + w[2]) / 2 <= x1 and y0 <= (w[1] + w[3]) / 2 <= y1]
    lines = collections.defaultdict(list)
    for w in inside:
        lines[(w[4], w[5], w[6])].append(w)
    out = []
    starts = [sorted(v, key=lambda w: w[0]) for v in lines.values()]
    own = {x.lower() for t in [stem, *options] for x in WORD.findall(t)}
    # text of another question: 2+ lines of 5+ real words, mostly words the item's own stem and options never use
    # (axis numbers, row numbers and figure labels are too short to count)
    # ... and it starts with a question number other than the item's own ("15. Nicholas boiled ..."): the item's own
    # passage, tables and observation boxes are foreign-looking too, but carry no question number (sample of 6, 21 Nov)
    # rows by position, not tesseract lines: a question number is often its own block, apart from the text beside it
    for n in inside:
        m = QNUM.match(n[7])  # "12" or "12.", never an option label "1)" or "(1)"
        if not m or int(m.group(1)) == qno or n[0] - x0 > 0.15 * (x1 - x0):
            continue
        cy, hh = (n[1] + n[3]) / 2, max(8, n[3] - n[1])
        ws = [x.lower() for w in inside if w is not n and abs((w[1] + w[3]) / 2 - cy) < hh and w[0] > n[0] for x in WORD.findall(w[7])]
        if len(ws) >= 5 and sum(x in own for x in ws) < 0.3 * len(ws):
            out.append("another-question")
            break
    if sum(1 for ln in starts if ln[0][7] in ("(1)", "1)")) >= 2:
        out.append("two-option-sets")
    # the crop is the (1)-(4) options table and nothing more, while the stem points at a drawing ("identifies the plant
    # parts H, J and K", "labelled", "shown below"): the drawing was left out (a stem that defines P and Q in words is fine)
    crop_words = {x.lower() for w in inside for x in WORD.findall(w[7])}
    opt_words = {x.lower() for o in options for x in WORD.findall(o)}
    labels = sum(1 for ln in starts if ln[0][7] in ("(1)", "(2)", "(3)", "(4)"))
    if crop_words and crop_words <= opt_words and labels >= 3 and POINTS.search(stem):
        out.append("options-table-only")
    return out


def check(a):
    out = Path(a.out) / a.subject
    rows = L.jl(out / "selected.jsonl")
    res, C, unplaced = [], collections.Counter(), 0
    for r in rows:
        if a.gate and r["id"] not in GATE:
            continue
        fl = set()
        for n, c in enumerate(r.get("crops") or [], 1):
            cb = crop_box(c)
            if cb is None:
                unplaced += 1
                fl.add("unplaced")
                continue
            fl |= set(flags_for(words_of(cb[0]), cb[1], r["qno"], r["options"], r["stem"]))
        if r.get("crops"):
            res.append({"id": r["id"], "flags": sorted(fl)})
            for f in fl:
                C[f] += 1
            C["flagged"] += bool(fl)
    if a.gate:
        bad = [x["id"] for x in res if bool(x["flags"]) != GATE[x["id"]]]
        for x in res:
            print(x["id"], "expect", "flag" if GATE[x["id"]] else "pass", x["flags"])
        print("GATE", "PASSED" if not bad and len(res) == len(GATE) else f"FAILED {bad} (found {len(res)}/{len(GATE)})")
        return
    with open(out / "croptext.jsonl", "w") as f:
        for x in res:
            f.write(json.dumps(x) + "\n")
    print(f"{len(res)} items with crops, {unplaced} crops not placed on their page; flags {dict(C)} -> {out / 'croptext.jsonl'}")


def selftest():
    W = lambda x, y, t, ln: (x, y, x + 20, y + 10, "1", "1", str(ln), t)
    other = [W(10 + 30 * k, 10 + 30 * ln, t, ln) for ln, line in enumerate(["11. Which following statements about cells true",
             "Cells have nucleus that controls activities"]) for k, t in enumerate(line.split())]
    split = [(10, 10, 30, 20, "9", "1", "1", "15.")] + [(60 + 40 * k, 10, 95 + 40 * k, 20, "8", "1", "1", t)
             for k, t in enumerate("Nicholas boiled some water before removing heat".split())]
    assert flags_for(split, (0, 0, 400, 40), 14, ["a", "b", "c", "d"], "The set-up below tests light.") == ["another-question"]
    passage = [W(10 + 30 * k, 10, t, 0) for k, t in enumerate("Corals live in the sea with poisonous tentacles".split())]
    assert flags_for(passage, (0, 0, 400, 40), 5, ["a", "b", "c", "d"], "Which adaptations are correct?") == []
    stem = "Carol tied a black bag around the leaves. Why did the plant die?"
    assert flags_for(other + [W(10, 100, "(1)", 7), W(10, 130, "(1)", 8)], (0, 0, 400, 160), 12, ["The stem broke", "b", "c", "d"], stem) \
        == ["another-question", "two-option-sets"]
    table = [W(10, 10 + 30 * i, f"({i + 1})", i) for i in range(4)] + [W(60, 10, "leaf", 0), W(110, 10, "stem", 0), W(160, 10, "fruit", 0)]
    opts = ["leaf, stem, fruit", "stem, fruit, flower", "stem, leaf, fruit", "flower, stem, leaf"]
    assert flags_for(table, (0, 0, 300, 140), 8, opts, "Which row correctly identifies the plant parts, H, J and K?") == ["options-table-only"]
    assert flags_for(table, (0, 0, 300, 140), 8, opts, "P makes food and Q does not. What could P and Q be?") == []
    axis = [W(10, 10 + 30 * i, str(12 * i), i) for i in range(4)]
    assert flags_for(axis, (0, 0, 300, 140), 3, ["a", "b", "c", "d"], "The graph shows it.") == []
    print("croptext selftest ok")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("cmd", choices=("check", "selftest"))
    p.add_argument("--out", default=str(DEF_OUT))
    p.add_argument("--subject", default="science")
    p.add_argument("--gate", action="store_true")
    a = p.parse_args()
    {"check": check, "selftest": lambda _a: selftest()}[a.cmd](a)
