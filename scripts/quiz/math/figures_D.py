"""Geometry figures for topic_geometry.py: angle scenes computed from real coordinates, nets,
isometric cube stacks, symmetry grids, a protractor and multi-panel (A-D) figures.

Everything is drawn with currentColor through figures.Fig. Scenes work in maths coordinates
(y up) and are scaled uniformly, so a 40 degree angle is drawn as 40 degrees.

    python scripts/quiz/math/figures_D.py     # self-check
"""
import math
from xml.sax.saxutils import escape

from figures import Fig, FONT

# ------------------------------------------------------------------ helpers


def pt(x, y, ang, r):
    """Point at distance r, angle ang (degrees, maths convention) from (x, y)."""
    a = math.radians(ang)
    return (x + r * math.cos(a), y + r * math.sin(a))


def meas(p, q, r):
    """Angle PQR in degrees (at q), from coordinates."""
    a = (p[0] - q[0], p[1] - q[1])
    b = (r[0] - q[0], r[1] - q[1])
    c = (a[0] * b[0] + a[1] * b[1]) / (math.hypot(*a) * math.hypot(*b))
    return math.degrees(math.acos(max(-1, min(1, c))))


def bearing(p, q):
    """Direction of the vector p->q in degrees (maths convention)."""
    return math.degrees(math.atan2(q[1] - p[1], q[0] - p[0]))


def dist(p, q):
    return math.hypot(q[0] - p[0], q[1] - p[1])


def intersect(p1, d1, p2, d2):
    """Intersection of the lines p1 + t*d1 and p2 + u*d2 (directions as vectors)."""
    det = d1[0] * (-d2[1]) - d1[1] * (-d2[0])
    t = ((p2[0] - p1[0]) * (-d2[1]) - (p2[1] - p1[1]) * (-d2[0])) / det
    return (p1[0] + t * d1[0], p1[1] + t * d1[1])


def vec(ang, r=1.0):
    return (r * math.cos(math.radians(ang)), r * math.sin(math.radians(ang)))


# ------------------------------------------------------------------ scene


class Scene:
    """Named points in maths coordinates, fitted uniformly into a w x h picture."""

    def __init__(self, w=320, h=230, pad=30):
        self.w, self.h, self.pad = w, h, pad
        self.pts = {}
        self.f = Fig(w, h)
        self.ready = False
        self.cmds = []  # drawing commands, run after fit()

    def add(self, name, x, y=None):
        if y is None:
            x, y = x
        self.pts[name] = (x, y)
        return (x, y)

    def fit(self, extra=()):
        xs = [p[0] for p in self.pts.values()] + [p[0] for p in extra]
        ys = [p[1] for p in self.pts.values()] + [p[1] for p in extra]
        bw, bh = (max(xs) - min(xs)) or 1, (max(ys) - min(ys)) or 1
        s = min((self.w - 2 * self.pad) / bw, (self.h - 2 * self.pad) / bh)
        cx, cy = (max(xs) + min(xs)) / 2, (max(ys) + min(ys)) / 2
        self.tf = lambda p: (self.w / 2 + (p[0] - cx) * s, self.h / 2 - (p[1] - cy) * s)
        self.scale = s
        self.centroid = (sum(xs) / len(xs), sum(ys) / len(ys))
        self.ready = True

    def P(self, n):
        return self.tf(self.pts[n] if isinstance(n, str) else n)

    # drawing: queued, so that points can be added after the first call
    def _q(self, fn, *a, **k):
        self.cmds.append((fn, a, k))

    def poly(self, names, shade=0.0, dash=False):
        self._q(lambda names, shade, dash: self.f.poly([self.P(n) for n in names], shade=shade, dash=dash), names, shade, dash)

    def seg(self, a, b, dash=False, width=1.6):
        self._q(lambda a, b, dash, width: self.f.line(*self.P(a), *self.P(b), dash=dash, width=width), a, b, dash, width)

    def circle(self, center, r_units, shade=0.0):
        self._q(lambda c, r, shade: self.f.circle(*self.P(c), r * self.scale, shade=shade), center, r_units, shade)

    def label(self, n, text=None, away=None, off=13, dx=0, dy=0, size=13):
        self._q(self._label, n, text, away, off, dx, dy, size)

    def _label(self, n, text, away, off, dx, dy, size):
        x, y = self.P(n)
        ax, ay = self.P(away) if away is not None else self.P(self.centroid)
        vx, vy = x - ax, y - ay
        m = math.hypot(vx, vy) or 1
        self.f.text(x + vx / m * off + dx, y + vy / m * off + dy, text or n, size=size, bold=True)

    def ang(self, v, a, b, text=None, r=24, reflex=False, size=13):
        self._q(self._ang, v, a, b, text, r, reflex, size)

    def _ang(self, v, a, b, text, r, reflex, size):
        vx, vy = self.P(v)
        pa, pb = self.P(a), self.P(b)
        a1 = math.degrees(math.atan2(vy - pa[1], pa[0] - vx))
        a2 = math.degrees(math.atan2(vy - pb[1], pb[0] - vx))
        start, sweep = a1, (a2 - a1) % 360
        if sweep > 180:
            start, sweep = a2, 360 - sweep
        if reflex:
            start, sweep = start + sweep, 360 - sweep
        la, lb = math.hypot(pa[0] - vx, pa[1] - vy), math.hypot(pb[0] - vx, pb[1] - vy)
        rr = min(r, 0.42 * min(la, lb))
        if abs(sweep - 90) < 0.6 and not reflex and text in (None, "", "90°"):
            self.f.right_angle(vx, vy, pa, pb)
            mid = start + sweep / 2
            rr = 14
        else:
            self.f.arc(vx, vy, rr, start, start + sweep, width=1.2)
            mid = start + sweep / 2
        if text:
            tw = 7.4 * len(text) + 2
            d = rr + 6 + 0.42 * tw
            if sweep < 75:
                d = max(d, (tw + 4) / (2 * math.sin(math.radians(sweep / 2))))
            d = min(d, 0.92 * min(la, lb) + (0 if sweep < 75 else 20))
            tx, ty = self.f.polar(vx, vy, d, mid)
            self.f.text(tx, ty, text, size=size)

    def right(self, v, a, b):
        self._q(lambda v, a, b: self.f.right_angle(*self.P(v), self.P(a), self.P(b)), v, a, b)

    def tick(self, a, b, n=1):
        self._q(self._tick, a, b, n)

    def _tick(self, a, b, n):
        (x1, y1), (x2, y2) = self.P(a), self.P(b)
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        m = math.hypot(x2 - x1, y2 - y1) or 1
        ux, uy = (x2 - x1) / m, (y2 - y1) / m
        nx, ny = -uy, ux
        for i in range(n):
            o = (i - (n - 1) / 2) * 5
            cx, cy = mx + ux * o, my + uy * o
            self.f.line(cx - nx * 5, cy - ny * 5, cx + nx * 5, cy + ny * 5, width=1.3)

    def arrow(self, a, b, n=1):
        """Parallel-side arrowheads on segment a-b."""
        self._q(self._arrow, a, b, n)

    def _arrow(self, a, b, n):
        (x1, y1), (x2, y2) = self.P(a), self.P(b)
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        m = math.hypot(x2 - x1, y2 - y1) or 1
        ux, uy = (x2 - x1) / m, (y2 - y1) / m
        nx, ny = -uy, ux
        for i in range(n):
            o = (i - (n - 1) / 2) * 7
            cx, cy = mx + ux * o, my + uy * o
            self.f.poly([(cx - ux * 5 + nx * 4, cy - uy * 5 + ny * 4), (cx + ux * 2, cy + uy * 2),
                         (cx - ux * 5 - nx * 4, cy - uy * 5 - ny * 4)], closed=False, width=1.3)

    def side(self, a, b, text, away=None, off=13):
        self._q(self._side, a, b, text, away, off)

    def _side(self, a, b, text, away, off):
        self.f.side_label(self.P(a), self.P(b), text, offset=off, inside=self.P(away if away is not None else self.centroid))

    def text(self, p, s, size=13, bold=False):
        self._q(lambda p, s, size, bold: self.f.text(*self.P(p), s, size=size, bold=bold), p, s, size, bold)

    def svg(self, title="Diagram", extra=()):
        if not self.ready:
            self.fit(extra)
        for fn, a, k in self.cmds:
            fn(*a, **k)
        return self.f.svg(title)


# ------------------------------------------------------------------ panels (A-D)


def panels(figs, letters="ABCD", cols=2, gap=10, title="Options"):
    """Combine several Fig objects (already drawn) into one svg with a bold letter on each."""
    pw, ph = figs[0].w, figs[0].h
    rows = math.ceil(len(figs) / cols)
    W, H = cols * pw + (cols - 1) * gap, rows * ph + (rows - 1) * gap
    out = []
    for i, f in enumerate(figs):
        x, y = (i % cols) * (pw + gap), (i // cols) * (ph + gap)
        body = "".join(f.parts)
        out.append(f'<g transform="translate({x},{y})">{body}'
                   f'<text x="12" y="14" font-size="15" {FONT} fill="currentColor" font-weight="700">{letters[i]}</text>'
                   f'<rect x="0.5" y="0.5" width="{pw - 1}" height="{ph - 1}" fill="none" stroke="currentColor" '
                   f'stroke-opacity="0.25" stroke-width="1" rx="6"/></g>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" role="img" '
            f'aria-label="{escape(title)}" class="qfig">{"".join(out)}</svg>')


# ------------------------------------------------------------------ grids (symmetry)


def grid_fig(n_cols, n_rows, shaded, line=None, cell=26, title="Grid", ghost=()):
    """Square grid with shaded cells {(col,row)} (row 0 at the top). line: ('v', x) vertical at column
    boundary x, ('h', y) horizontal at row boundary y, ('d1',) / ('d2',) diagonals of a square grid."""
    pad = 10
    w, h = n_cols * cell + 2 * pad, n_rows * cell + 2 * pad
    f = Fig(w, h)
    for (c, r) in shaded:
        f.rect(pad + c * cell, pad + r * cell, cell, cell, shade=0.45, width=0.8)
    for c in range(n_cols + 1):
        f.line(pad + c * cell, pad, pad + c * cell, pad + n_rows * cell, width=0.7)
    for r in range(n_rows + 1):
        f.line(pad, pad + r * cell, pad + n_cols * cell, pad + r * cell, width=0.7)
    f.rect(pad, pad, n_cols * cell, n_rows * cell, width=1.6)
    for line in ([] if not line else [line] if isinstance(line[0], str) else line):
        k = line[0]
        if k == "v":
            f.line(pad + line[1] * cell, pad - 6, pad + line[1] * cell, pad + n_rows * cell + 6, dash=True, width=2)
        elif k == "h":
            f.line(pad - 6, pad + line[1] * cell, pad + n_cols * cell + 6, pad + line[1] * cell, dash=True, width=2)
        elif k == "d1":
            f.line(pad - 4, pad - 4, pad + n_cols * cell + 4, pad + n_rows * cell + 4, dash=True, width=2)
        elif k == "d2":
            f.line(pad - 4, pad + n_rows * cell + 4, pad + n_cols * cell + 4, pad - 4, dash=True, width=2)
    return f, f.svg(title)


# ------------------------------------------------------------------ nets


def hexominoes():
    """All fixed hexominoes as frozensets of (c, r), by growing cells."""
    def norm(s):
        mc, mr = min(c for c, r in s), min(r for c, r in s)
        return frozenset((c - mc, r - mr) for c, r in s)
    cur = {frozenset([(0, 0)])}
    for _ in range(5):
        nxt = set()
        for s in cur:
            for c, r in s:
                for dc, dr in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    q = (c + dc, r + dr)
                    if q not in s:
                        nxt.add(norm(s | {q}))
        cur = nxt
    return sorted(cur, key=lambda s: sorted(s))


def has_2x2(cells):
    return any({(c, r), (c + 1, r), (c, r + 1), (c + 1, r + 1)} <= set(cells) for c, r in cells)


def roll_labels(cells):
    """Roll a labelled cube over the net. Returns {cell: face id on the bottom} or None if some face repeats.
    Faces: 0 top,1 bottom,2 north,3 south,4 east,5 west."""
    cells = set(cells)
    start = min(cells)
    state = {start: (0, 1, 2, 3, 4, 5)}
    queue = [start]
    while queue:
        c = queue.pop(0)
        t, b, n, s, e, w = state[c]
        for dc, dr, nxt in ((1, 0, (w, e, n, s, t, b)), (-1, 0, (e, w, n, s, b, t)),
                            (0, -1, (s, n, t, b, e, w)), (0, 1, (n, s, b, t, e, w))):
            q = (c[0] + dc, c[1] + dr)
            if q in cells and q not in state:
                state[q] = nxt
                queue.append(q)
    bottoms = {c: st[1] for c, st in state.items()}
    if len(state) != 6 or len(set(bottoms.values())) != 6:
        return None
    return bottoms


def is_cube_net(cells):
    return (not has_2x2(cells)) and roll_labels(cells) is not None


def transforms(cells):
    """The 8 rotations/reflections of a cell set, each normalised."""
    out = []
    s = list(cells)
    for refl in (False, True):
        cur = [(-c, r) if refl else (c, r) for c, r in s]
        for _ in range(4):
            cur = [(-r, c) for c, r in cur]
            mc, mr = min(c for c, r in cur), min(r for c, r in cur)
            out.append(frozenset((c - mc, r - mr) for c, r in cur))
    return out


def net_fig(cells, cell=24, numbers=None, w=None, h=None, title="Net", ox=None, oy=None, fig=None):
    """Draw a polyomino net. numbers: {cell: label}. Returns a Fig (not yet svg) when fig is None -> svg string."""
    cs = list(cells)
    mc, Mc = min(c for c, r in cs), max(c for c, r in cs)
    mr, Mr = min(r for c, r in cs), max(r for c, r in cs)
    nw, nh = (Mc - mc + 1) * cell, (Mr - mr + 1) * cell
    W = w or nw + 20
    H = h or nh + 20
    f = Fig(W, H)
    x0 = (W - nw) / 2 if ox is None else ox
    y0 = (H - nh) / 2 if oy is None else oy
    for c, r in cs:
        f.rect(x0 + (c - mc) * cell, y0 + (r - mr) * cell, cell, cell, shade=0.07, width=1.5)
        if numbers and (c, r) in numbers:
            f.text(x0 + (c - mc + 0.5) * cell, y0 + (r - mr + 0.5) * cell, numbers[(c, r)], size=13, bold=True)
    return f if w or h else f.svg(title)


def solid_net(kind, title="Net"):
    """Nets of other solids, drawn with true proportions. kind: cuboid, tri_prism, sq_pyramid,
    tri_pyramid, cylinder, cone, pent_prism, cube."""
    u = 26
    f = Fig(330, 210)
    ox, oy = 20, 30
    if kind == "cube":
        for c, r in ((0, 1), (1, 1), (2, 1), (3, 1), (1, 0), (1, 2)):
            f.rect(ox + 40 + c * u * 1.5, oy + r * u * 1.5, u * 1.5, u * 1.5, shade=0.07)
        w = 330
    elif kind == "cuboid":
        l, wd, h = 70, 46, 40
        x = 30
        for i, ww in enumerate((l, wd, l, wd)):
            f.rect(x, 80, ww, h, shade=0.07)
            x += ww
        f.rect(30, 80 - wd, l, wd, shade=0.07)
        f.rect(30, 80 + h, l, wd, shade=0.07)
    elif kind == "tri_prism":
        a, h = 64, 52
        for i in range(3):
            f.rect(30 + i * a, 80, a, h, shade=0.07)
        tx = 30 + a
        f.poly([(tx, 80), (tx + a, 80), (tx + a / 2, 80 - a * 0.866)], shade=0.07)
        f.poly([(tx, 80 + h), (tx + a, 80 + h), (tx + a / 2, 80 + h + a * 0.866)], shade=0.07)
    elif kind == "sq_pyramid":
        s = 58
        x0, y0 = 120, 70
        f.rect(x0, y0, s, s, shade=0.07)
        f.poly([(x0, y0), (x0 + s, y0), (x0 + s / 2, y0 - 52)], shade=0.07)
        f.poly([(x0, y0 + s), (x0 + s, y0 + s), (x0 + s / 2, y0 + s + 52)], shade=0.07)
        f.poly([(x0, y0), (x0, y0 + s), (x0 - 52, y0 + s / 2)], shade=0.07)
        f.poly([(x0 + s, y0), (x0 + s, y0 + s), (x0 + s + 52, y0 + s / 2)], shade=0.07)
    elif kind == "tri_pyramid":
        a = 130
        A, B, C = (100, 160), (100 + a, 160), (100 + a / 2, 160 - a * 0.866)
        mAB, mBC, mCA = ((A[0] + B[0]) / 2, A[1]), ((B[0] + C[0]) / 2, (B[1] + C[1]) / 2), ((A[0] + C[0]) / 2, (A[1] + C[1]) / 2)
        f.poly([A, mAB, mCA], shade=0.07)
        f.poly([mAB, B, mBC], shade=0.07)
        f.poly([mCA, mBC, C], shade=0.07)
        f.poly([mAB, mBC, mCA], shade=0.07)
    elif kind == "cylinder":
        f.rect(70, 70, 150, 70, shade=0.07)
        f.circle(145 - 40, 40, 30)
        f.circle(145 + 40, 170, 30)
        f.circle(145 + 40 - 120, 170, 0.1)
    elif kind == "cone":
        f.circle(100, 150, 32)
        cx, cy, R = 170, 60, 100
        f.path(f"M {cx} {cy} L {cx + R * math.cos(math.radians(-10)):.1f} {cy - R * math.sin(math.radians(-10)):.1f} "
               f"A {R} {R} 0 0 1 {cx + R * math.cos(math.radians(-100)):.1f} {cy - R * math.sin(math.radians(-100)):.1f} Z", shade=0.07)
    elif kind == "pent_prism":
        a, h = 40, 44
        for i in range(5):
            f.rect(50 + i * a, 90, a, h, shade=0.07)
        for sgn in (-1, 1):
            y = 90 if sgn < 0 else 90 + h
            x1, x2 = 50 + 2 * a, 50 + 3 * a
            f.poly([(x1, y), (x2, y), (x2 + 0.309 * a, y + sgn * 0.951 * a), (x1 + a / 2, y + sgn * 1.539 * a), (x1 - 0.309 * a, y + sgn * 0.951 * a)], shade=0.07)
    return f.svg(title)


# ------------------------------------------------------------------ isometric cube stacks


def stack_fig(heights, s=26, title="Solid made of cubes"):
    """heights[i][j]: stack height at (i, j). The viewer looks from the +i +j side, so stacks must not
    get taller towards the viewer (heights non-increasing in i and j) for every cube to be determined."""
    ni, nj = len(heights), len(heights[0])
    c30 = math.cos(math.radians(30)) * s
    top = max(max(r) for r in heights)
    W = (ni + nj) * c30 + 24
    H = (ni + nj) * s * 0.5 + top * s + 24
    ox = nj * c30 + 12
    oy = top * s + 12
    f = Fig(W, H)

    def P(i, j, k):
        return (ox + (i - j) * c30, oy + (i + j) * s * 0.5 - k * s)
    cubes = sorted(((i, j, k) for i in range(ni) for j in range(nj) for k in range(heights[i][j])),
                   key=lambda c: (sum(c), c))
    have = set(cubes)
    for i, j, k in cubes:
        if (i, j, k + 1) not in have:
            f.poly([P(i, j, k + 1), P(i + 1, j, k + 1), P(i + 1, j + 1, k + 1), P(i, j + 1, k + 1)], shade=0.0, width=1.2)
        if (i + 1, j, k) not in have:
            f.poly([P(i + 1, j, k), P(i + 1, j + 1, k), P(i + 1, j + 1, k + 1), P(i + 1, j, k + 1)], shade=0.3, width=1.2)
        if (i, j + 1, k) not in have:
            f.poly([P(i, j + 1, k), P(i + 1, j + 1, k), P(i + 1, j + 1, k + 1), P(i, j + 1, k + 1)], shade=0.15, width=1.2)
    return f.svg(title)


# ------------------------------------------------------------------ protractor


def protractor_fig(theta, base_right=True, labels=("P", "Q", "R")):
    """Protractor, centre Q. One arm QP along the baseline (to the right when base_right, else left),
    the other arm QR at theta degrees from it, on the upper side. Reading: the scale that starts at 0 on QP."""
    w, h, R = 330, 178, 120
    cx, cy = 165, 150
    parts = [f'<g font-family="Literata, Georgia, serif" fill="currentColor" font-size="9" text-anchor="middle" '
             f'dominant-baseline="middle">']
    parts.append(f'<path d="M {cx - R} {cy} A {R} {R} 0 0 1 {cx + R} {cy} Z" fill="currentColor" fill-opacity="0.06" '
                 f'stroke="currentColor" stroke-width="1.2"/>')
    for a in range(0, 181, 5):
        L = 12 if a % 10 == 0 else 6
        x1, y1 = pt(cx, cy, a, R)
        x2, y2 = pt(cx, cy, a, R - L)
        parts.append(f'<line x1="{x1:.1f}" y1="{cy * 2 - y1 - (cy * 2 - cy) * 0:.1f}" x2="{x2:.1f}" y2="{2 * cy - y2:.1f}" '
                     f'stroke="currentColor" stroke-width="0.9"/>')
    # fix y: pt uses y-up, convert to svg
    parts = parts[:2]
    for a in range(0, 181, 5):
        L = 12 if a % 10 == 0 else 6
        x1, y1 = pt(cx, cy, a, R)
        x2, y2 = pt(cx, cy, a, R - L)
        y1, y2 = 2 * cy - y1, 2 * cy - y2
        parts.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="currentColor" stroke-width="0.9"/>')
    for a in range(0, 181, 10):
        xo, yo = pt(cx, cy, a, R + 9)
        xi, yi = pt(cx, cy, a, R - 22)
        parts.append(f'<text x="{xo:.1f}" y="{2 * cy - yo:.1f}" font-size="8.5">{a}</text>')
        parts.append(f'<text x="{xi:.1f}" y="{2 * cy - yi:.1f}" font-size="8.5" fill-opacity="0.75">{180 - a}</text>')
    # arms
    ang2 = theta if base_right else 180 - theta
    bx = cx + (R + 20 if base_right else -(R + 20))
    ex, ey = pt(cx, cy, ang2, R + 20)
    parts.append(f'<line x1="{cx}" y1="{cy}" x2="{bx}" y2="{cy}" stroke="currentColor" stroke-width="1.8"/>')
    parts.append(f'<line x1="{cx}" y1="{cy}" x2="{ex:.1f}" y2="{2 * cy - ey:.1f}" stroke="currentColor" stroke-width="1.8"/>')
    parts.append(f'<circle cx="{cx}" cy="{cy}" r="2.5"/>')
    parts.append('</g>')
    parts.append(f'<g font-family="Literata, Georgia, serif" fill="currentColor" font-size="13" font-weight="600" '
                 f'text-anchor="middle" dominant-baseline="middle">'
                 f'<text x="{cx}" y="{cy + 14}">{labels[1]}</text>'
                 f'<text x="{bx + (8 if base_right else -8)}" y="{cy + 2}">{labels[0]}</text>'
                 f'<text x="{ex + (6 if ex > cx else -6):.1f}" y="{2 * cy - ey - 8:.1f}">{labels[2]}</text></g>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 -12 {w} {h + 18}" role="img" '
            f'aria-label="Protractor" class="qfig">{"".join(parts)}</svg>')


if __name__ == "__main__":
    import xml.dom.minidom as md
    hs = hexominoes()
    good = {h for h in hs if is_cube_net(h)}
    assert len(hs) == 35 * 1 or len(hs) == 216, len(hs)
    free = {min(map(lambda t: tuple(sorted(t)), transforms(h))) for h in good}
    assert len(free) == 11, len(free)
    for k in ("cube", "cuboid", "tri_prism", "sq_pyramid", "tri_pyramid", "cylinder", "cone", "pent_prism"):
        md.parseString(solid_net(k))
    md.parseString(stack_fig([[3, 2, 1], [2, 1, 1], [1, 1, 0]]))
    md.parseString(protractor_fig(65))
    print("figures_D OK", len(hs), len(good), len(free), len(protractor_fig(65)))
