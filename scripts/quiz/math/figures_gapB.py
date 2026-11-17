"""Figures for the group-B gap templates: fraction bars and counter / unit models."""
from figures import Fig


def fraction_bars(specs, bar_w=300, title="Fraction bars of equal length"):
    """specs: list of (label, parts, shaded). shaded=None draws an unshaded bar. Bars are the same total length."""
    h = 28
    f = Fig(bar_w + 70, 20 + len(specs) * (h + 22))
    for i, (label, parts, shaded) in enumerate(specs):
        y = 12 + i * (h + 22)
        f.text(8, y + h / 2, label, anchor="start", size=13, bold=True)
        cw = bar_w / parts
        for j in range(parts):
            f.rect(60 + j * cw, y, cw, h, shade=0.45 if shaded is not None and j < shaded else 0, width=1.2)
    return f.svg(title)


def counters(rows, title="Counters in rows"):
    """rows: list of (label, count). Each row has its own fill so colours are distinguishable without colour words."""
    gap, r = 24, 9
    n = max(c for _, c in rows)
    x0 = max(80, 16 + 8 * max(len(label) for label, _ in rows))
    f = Fig(max(300, x0 + n * gap), 14 + len(rows) * 34)
    fills = [0.85, 0.0, 0.35, 0.6]
    for i, (label, c) in enumerate(rows):
        y = 22 + i * 34
        f.text(6, y, label, anchor="start", size=13, bold=True)
        for j in range(c):
            f.circle(x0 + j * gap + r, y, r, shade=fills[i % 4], width=1.4)
    return f.svg(title)


def unit_rows(rows, unit_w=30, title="Bar model with equal units"):
    """rows: list of (label, units): one row of equal boxes per person."""
    n = max(c for _, c in rows)
    x0 = 16 + 8 * max(len(label) for label, _ in rows)  # label column fits the longest name, e.g. "Shu Fen"
    f = Fig(max(300, x0 + 10 + n * unit_w), 12 + len(rows) * 40)
    for i, (label, c) in enumerate(rows):
        y = 8 + i * 40
        f.text(6, y + 15, label, anchor="start", size=13, bold=True)
        for j in range(c):
            f.rect(x0 + j * unit_w, y, unit_w, 30, shade=0.2, width=1.4)
    return f.svg(title)
