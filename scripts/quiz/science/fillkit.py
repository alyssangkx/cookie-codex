"""Shared helpers for the 2026-11-20 Science fill rounds (PSLE-style items written as code).

    add(subtopic, file, rows)   append rows (new keys only) to items/<file>
    ship(subtopic, file, round_name, note)   mark every item of the file that has no verdict yet as shipped (current fingerprint)
    lint(subtopic, file)        prints give-away heuristics for the review pass
Rows are (key, level, outcome no., pattern, stem, correct, [(wrong, tag, why) x3], [solution lines], figure maker or None).
Figures: code-drawn SVG, black and white (currentColor), viewBox, no scripts or external references.
"""
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
import figs_basic as F  # noqa: E402
from bankcommon import fingerprint  # noqa: E402

ITEMS = HERE / "items"
REVIEW = HERE / "review.json"
svg, txt, box = F.svg, F.txt, F.box
AH = '<defs><marker id="ah" markerUnits="userSpaceOnUse" markerWidth="10" markerHeight="10" refX="9" refY="5" orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="currentColor"/></marker></defs>'


def arrow(x1, y1, x2, y2, w=2):
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke-width="{w}" marker-end="url(#ah)"/>'


def _tw(s, fs, bold=False):
    """Estimated text width in px (same estimate as bankcommon.svg_text_overflows)."""
    return len(s) * fs * (0.6 if bold else 0.55)


def _best_split(s, fs, bold):
    """Two-line split at a space that makes the wider line narrowest; None if there is no space."""
    ws = s.split(" ")
    if len(ws) < 2:
        return None
    return min(((" ".join(ws[:i]), " ".join(ws[i:])) for i in range(1, len(ws))),
               key=lambda p: max(_tw(p[0], fs, bold), _tw(p[1], fs, bold)))


def table(headers, rows, widths=None, caption=None, rowh=30, fs=14, first_left=False):
    """A ruled table. Cells may contain '|' for two lines. A cell that does not fit its column wraps at a space into two
    lines; a line that still does not fit widens the column (the given width is a minimum). The font is never shrunk."""
    n = len(headers)
    widths = list(widths or [90] * n)
    PAD = 12
    grid = [[str(c) for c in row] for row in [headers] + rows]
    cells = []  # per row: per column: list of lines
    for r, row in enumerate(grid):
        bold = r == 0
        cells.append([c.split("|") for c in row])
    for c in range(n):
        for r, row in enumerate(cells):
            lines = row[c]
            bold = r == 0
            if max(_tw(l, fs, bold) for l in lines) + PAD <= widths[c]:
                continue
            if len(lines) == 1 and (sp := _best_split(lines[0], fs, bold)):
                lines = list(sp)
            widths[c] = max(widths[c], int(max(_tw(l, fs, bold) for l in lines) + PAD + 0.999))
    for row_i, row in enumerate(cells):  # wrap what no longer fits at the final widths
        for c in range(n):
            lines = row[c]
            if len(lines) == 1 and _tw(lines[0], fs, row_i == 0) + PAD > widths[c] and (sp := _best_split(lines[0], fs, row_i == 0)):
                row[c] = list(sp)
    W = sum(widths) + 20
    if caption:
        W = max(W, int(_tw(caption, 13, True)) + 20)
    y0 = 36 if caption else 10
    off = (W - sum(widths) - 20) / 2
    b = txt(W / 2, 22, caption, 13, bold=True) if caption else ""
    y = y0
    for r, row in enumerate(cells):
        h = (rowh + 4 if r == 0 else rowh) + 14 * (max(len(l) for l in row) - 1)
        x = 10 + off
        for c, parts in enumerate(row):
            b += f'<rect x="{x:g}" y="{y}" width="{widths[c]}" height="{h}"/>'
            for k, p in enumerate(parts):
                yy = y + h / 2 + 5 - (len(parts) - 1) * 8 + k * 16
                b += txt(x + widths[c] / 2, yy, p, fs, bold=(r == 0))
            x += widths[c]
        y += h
    H = y + 10
    return svg(W, H, b)


def graph(xs, series, ymax, xlabel, ylabel, caption=None, ystep=None, W=340, H=240, labels=True, bars=False, ymin=0, legend="tl"):
    """Line (or bar) graph. series = [(name, [y...])]; xs are x tick labels (evenly spaced)."""
    L, R, T, B = 52, 18, 38 if caption else 20, 52
    pw, ph = W - L - R, H - T - B
    ystep = ystep or ymax / 5
    b = txt(W / 2, 18, caption, 13, bold=True) if caption else ""
    b += f'<path d="M{L} {T} V{T + ph} H{L + pw}"/>'
    k = 0
    v = ymin
    while v <= ymax + 1e-9:
        y = T + ph - (v - ymin) / (ymax - ymin) * ph
        b += f'<line x1="{L - 4}" y1="{y:.1f}" x2="{L}" y2="{y:.1f}"/>' + txt(L - 8, y + 4, f"{v:g}", 11, anchor="end")
        v += ystep
    n = len(xs)
    def xp(i):
        return L + (i + 0.5) * pw / n if bars else L + (i * pw / (n - 1) if n > 1 else pw / 2)
    for i, xl in enumerate(xs):
        b += txt(xp(i), T + ph + 16, xl, 11)
        if not bars:
            b += f'<line x1="{xp(i):.1f}" y1="{T + ph}" x2="{xp(i):.1f}" y2="{T + ph + 4}"/>'
    b += txt(L + pw / 2, H - 8, xlabel, 12)
    b += f'<text transform="translate(14 {T + ph / 2}) rotate(-90)" text-anchor="middle" font-size="12" fill="currentColor" stroke="none">{ylabel}</text>'
    dash = ["", "6 4", "2 4"]
    for s, (name, ys) in enumerate(series):
        if bars:
            bw = pw / n * 0.5
            for i, y in enumerate(ys):
                yy = T + ph - (y - ymin) / (ymax - ymin) * ph
                b += f'<rect x="{xp(i) - bw / 2:.1f}" y="{yy:.1f}" width="{bw:.1f}" height="{T + ph - yy:.1f}"/>'
        else:
            pts = " ".join(f"{xp(i):.1f},{T + ph - (y - ymin) / (ymax - ymin) * ph:.1f}" for i, y in enumerate(ys))
            d = f' stroke-dasharray="{dash[s]}"' if dash[s] else ""
            b += f'<polyline points="{pts}"{d}/>'
            for i, y in enumerate(ys):
                b += f'<circle cx="{xp(i):.1f}" cy="{T + ph - (y - ymin) / (ymax - ymin) * ph:.1f}" r="2.5" fill="currentColor"/>'
    if len(series) > 1 and labels:
        lx = L + 8 if legend[1] == "l" else L + pw - 62
        ly = T + 8 if legend[0] == "t" else T + ph - 12 - 16 * (len(series) - 1)
        for s, (name, ys) in enumerate(series):
            b += f'<line x1="{lx}" y1="{ly + s * 16}" x2="{lx + 26}" y2="{ly + s * 16}"' + (f' stroke-dasharray="{dash[s]}"' if dash[s] else "") + "/>"
            b += txt(lx + 32, ly + 4 + s * 16, name, 11, anchor="start")
    return svg(W, H, b)


# Keys that were retired (content changed, a new key took their place). add() never re-adds them.
RETIRED = set("""
ag-018 ag-101 ag-102 ag-103 ag-114 ag-201 rc-201 rc-212 wc-223 ev-116 cv-013
ws-111 ws-112 ws-113 ws-114 ws-115 ws-201 ws-202 ws-203
ci-110 ci-113 ci-202 ci-203 ci-204 ci-205 ci-220 cv-102 cv-119 cv-202 cv-203 cv-204 cv-205 cv-215 cv-503
""".split())


def build_items(subtopic, rows):
    """Rows -> item dicts (no file access). Rows with a retired key are refused."""
    out = []
    for key, lvl, on, pat, stem, ok, wrongs, sol, fm in rows:
        assert len(wrongs) == 3, key
        if key in RETIRED:  # never re-added; said out loud so a copy-paste under an old key is noticed
            print(f"fillkit: skipped retired key {key} ({subtopic})", file=sys.stderr)
            continue
        pos = (int(key.split("-")[1]) * 3 + 1) % 4
        opts = [w[0] for w in wrongs]
        expl = [{"tag": w[1], "why": w[2]} for w in wrongs]
        opts.insert(pos, ok)
        expl.insert(pos, None)
        it = {"key": key, "level": lvl, "outcome": f"{subtopic}-{on}", "pattern": pat, "stem": stem, "options": opts, "answer": pos,
              "explain": expl, "solution": sol}
        if fm:
            it["figure"] = fm() if callable(fm) else fm
        out.append(it)
    return out


def add(subtopic, fname, rows):
    f = ITEMS / fname
    d = json.loads(f.read_text()) if f.exists() else {"subtopic": subtopic, "items": []}
    have = {it["key"] for it in d["items"]}
    new = [it for it in build_items(subtopic, rows) if it["key"] not in have]
    d["items"].extend(new)
    f.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n")
    return len(new)


def remove(subtopic, fname, keys):
    """Delete items (and their review verdicts) so they can be re-added under a new key."""
    f = ITEMS / fname
    d = json.loads(f.read_text())
    d["items"] = [it for it in d["items"] if it["key"] not in keys]
    f.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n")
    rv = json.loads(REVIEW.read_text())
    for k in keys:
        rv.pop(f"{subtopic}|{k}", None)
    REVIEW.write_text(json.dumps(rv, ensure_ascii=False, indent=1) + "\n")


def ship(subtopic, fname, round_name, note, only=None):
    """Mark items of this file without a verdict yet as shipped for exactly their current content."""
    rv = json.loads(REVIEW.read_text())
    d = json.loads((ITEMS / fname).read_text())
    n = 0
    for it in d["items"]:
        rk = f"{subtopic}|{it['key']}"
        if rk in rv or (only and not only(it)):
            continue
        rv[rk] = {"ship": True, "reasons": [], "notes": [note], "fingerprint": fingerprint(it), "round": round_name}
        n += 1
    REVIEW.write_text(json.dumps(rv, ensure_ascii=False, indent=1) + "\n")
    return n


def lint(subtopic, fname, prefix=None):
    """Heuristics for the item-by-item pass: longest-correct, stem echo, near-duplicate options."""
    d = json.loads((ITEMS / fname).read_text())
    words = lambda s: set(re.findall(r"[a-z]{4,}", s.lower()))
    longest = tot = 0
    for it in d["items"]:
        if prefix and not it["key"].startswith(prefix):
            continue
        o = it["options"]; a = it["answer"]
        tot += 1
        ln = [len(x) for x in o]
        flag = []
        if ln[a] == max(ln) and ln[a] > 1.3 * sorted(ln)[-2]:
            flag.append("answer much longer")
        if ln[a] == max(ln):
            longest += 1
        ov = [len(words(x) & words(it["stem"])) for x in o]
        if ov[a] >= 2 and ov[a] > max(ov[i] for i in range(4) if i != a):
            flag.append("answer echoes stem")
        if flag:
            print(it["key"], flag, "|", o[a][:70])
    print(f"{tot} items, answer is longest in {longest}")
