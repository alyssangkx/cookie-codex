"""Figure helpers for data representation: picture graph with key, table, two-line-label pie chart."""
import math
from figures import Fig


def picture_graph(labels, counts, key, noun, title="", w=300):
    """counts are multiples of key/2; half symbols are drawn as half discs when counts are odd half-keys."""
    n = len(labels)
    f = Fig(w, 34 + 26 * n + 28)
    if title:
        f.text(w / 2, 12, title, size=13, bold=True)
    r = 6.5
    for i, (lab, c) in enumerate(zip(labels, counts)):
        y = 36 + 26 * i
        f.text(74, y, lab, anchor="end", size=12)
        half = c / key * 2
        full = int(half // 2)
        for j in range(full):
            f.circle(88 + 18 * j, y, r, shade=0.3)
        if half % 2 >= 1:
            cx = 88 + 18 * full
            f.path(f"M {cx:.1f} {y - r:.1f} A {r} {r} 0 0 0 {cx:.1f} {y + r:.1f} Z", shade=0.3)
    ky = 36 + 26 * n + 4
    f.text(10, ky, "Key:", anchor="start", size=12, bold=True)
    f.circle(58, ky, r, shade=0.3)
    f.text(70, ky, f"= {key} {noun}", anchor="start", size=12)
    return f.svg(title or "Picture graph")


def table_fig(header, rows, title="", blanks=(), size=12):
    """header: list of str; rows: list of list of str. blanks: set of (row, col) shown shaded as '?'."""
    cols = len(header)
    cw = []
    for c in range(cols):
        m = max(len(str(x)) for x in [header[c]] + [r[c] for r in rows])
        cw.append(max(46, m * 7.4 + 16))
    rh = 26
    top = 28 if title else 6
    w = sum(cw) + 16
    h = top + rh * (len(rows) + 1) + 8
    f = Fig(w, h)
    if title:
        f.text(w / 2, 13, title, size=13, bold=True)
    x0 = 8
    f.rect(x0, top, sum(cw), rh, shade=0.12)
    f.rect(x0, top, sum(cw), rh * (len(rows) + 1))
    for i in range(1, len(rows) + 1):
        f.line(x0, top + rh * i, x0 + sum(cw), top + rh * i, width=0.9)
    x = x0
    for c in range(cols - 1):
        x += cw[c]
        f.line(x, top, x, top + rh * (len(rows) + 1), width=0.9)
    x = x0
    for c in range(cols):
        f.text(x + cw[c] / 2, top + rh / 2, header[c], size=size, bold=True)
        for i, row in enumerate(rows):
            cy = top + rh * (i + 1)
            if (i, c) in blanks:
                f.rect(x + 1, cy + 1, cw[c] - 2, rh - 2, shade=0.18, width=0.1)
                f.text(x + cw[c] / 2, cy + rh / 2, "?", size=size, bold=True)
            else:
                f.text(x + cw[c] / 2, cy + rh / 2, row[c], size=size)
        x += cw[c]
    return f.svg(title or "Table")


def pie_fig(labels, parts, shows, title="", w=320, h=232):
    """Pie with two-line sector labels: category, then shows[i] (None leaves the value off)."""
    f = Fig(w, h)
    cx, cy, r = w / 2, h / 2 + 10, 94
    if title:
        f.text(w / 2, 12, title, size=13, bold=True)
    total = sum(parts)
    a = 90.0
    for i, (lab, p) in enumerate(zip(labels, parts)):
        sw = 360 * p / total
        f.arc(cx, cy, r, a, a + sw, sector=True, shade=0.06 + 0.12 * (i % 3))
        mx, my = f.polar(cx, cy, r * 0.64, a + sw / 2)
        if shows[i]:
            f.text(mx, my - 7, lab, size=11)
            f.text(mx, my + 7, shows[i], size=11)
        else:
            f.text(mx, my, lab, size=11)
        a += sw
    return f.svg(title or "Pie chart")
