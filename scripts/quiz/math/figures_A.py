"""Figures for group A (whole numbers): growing square patterns and overlapping cards."""
from figures import Fig


def growing_rows_fig(c, nfigs=3, u=9):
    """Figure k has k rows; row i has c*i squares (a staircase), drawn for Figure 1..nfigs."""
    gap = 26
    widths = [max(c * k * u, 60) for k in range(1, nfigs + 1)]
    w = sum(widths) + gap * (nfigs - 1) + 24
    h = nfigs * u + 52
    f = Fig(w, h)
    x = 12
    for k in range(1, nfigs + 1):
        for i in range(1, k + 1):
            for j in range(c * i):
                f.rect(x + (widths[k - 1] - c * k * u) / 2 + j * u, 14 + (i - 1) * u, u, u, shade=0.18, width=1.0)
        f.text(x + widths[k - 1] / 2, 14 + nfigs * u + 16, f"Figure {k}", size=12)
        x += widths[k - 1] + gap
    return f.svg("First three figures of a pattern of squares")


def overlap_cards_fig(L, ov, total):
    """Identical cards, each L cm long, overlapping by ov cm; the whole row is `total` cm long.
    Two cards are drawn at each end with dots between. Not drawn to scale."""
    Lp = 64
    ovp = max(10, min(30, round(Lp * ov / L)))
    step = Lp - ovp
    ch = 26
    off = 14
    x0 = 14
    f = Fig(300, 150)
    y0 = 34

    def chain(xs):
        for i in range(2):
            y = y0 + (off if i % 2 else 0)
            f.rect(xs + i * step, y, Lp, ch, width=1.4)
        # shade the overlap
        f.rect(xs + step, y0 + off, ovp, ch - off, shade=0.25, width=0.6)
        return xs + step + Lp

    end1 = chain(x0)
    xr = end1 + 40
    end2 = chain(xr)
    f.text((end1 + xr) / 2, y0 + 20, ". . .", size=16)
    # card length marker
    yd = y0 - 10
    f.line(x0, yd, x0 + Lp, yd, width=1.0)
    f.line(x0, yd - 4, x0, yd + 4, width=1.0)
    f.line(x0 + Lp, yd - 4, x0 + Lp, yd + 4, width=1.0)
    f.text(x0 + Lp / 2, yd - 10, f"{L} cm", size=12)
    # overlap label
    f.text(x0 + step + ovp / 2, y0 + off + ch + 12, f"{ov} cm", size=12)
    # total bracket
    yb = y0 + off + ch + 40
    f.line(x0, yb, end2, yb, width=1.0)
    f.line(x0, yb - 5, x0, yb + 5, width=1.0)
    f.line(end2, yb - 5, end2, yb + 5, width=1.0)
    f.text((x0 + end2) / 2, yb + 14, f"{total} cm", size=12)
    f.w = int(end2 + 16)
    return f.svg("Identical cards overlapping in a row")


def number_grid_fig(c, rows=3):
    """Numbers 1, 2, 3, ... in c columns A.. with alternate rows running in opposite directions (first `rows` rows)."""
    cw, ch = 34, 26
    w, h = c * cw + 56, (rows + 1) * ch + 22
    f = Fig(w, h)
    x0, y0 = 44, 10
    for j in range(c):
        f.text(x0 + j * cw + cw / 2, y0 + ch / 2, "ABCDEFGH"[j], size=14, bold=True)
    for i in range(rows):
        f.text(24, y0 + (i + 1) * ch + ch / 2, f"Row {i + 1}", size=11, anchor="middle")
        for j in range(c):
            n = i * c + (j + 1 if i % 2 == 0 else c - j)
            f.rect(x0 + j * cw, y0 + (i + 1) * ch, cw, ch, width=1.0)
            f.text(x0 + j * cw + cw / 2, y0 + (i + 1) * ch + ch / 2, n, size=13)
    f.w = w + 10
    return f.svg("Numbers written in a table with columns A onwards")


if __name__ == "__main__":
    print(len(growing_rows_fig(2)), len(overlap_cards_fig(10, 3, 100)))
