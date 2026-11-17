"""Figure helpers for measurement, area and volume questions (group C).

Everything draws through figures.Fig, so it uses currentColor only.
UF maps unit coordinates (y down) onto the canvas at one uniform scale, so figures are to scale.
"""
import math
from fractions import Fraction as F

from figures import Fig


def num(x):
    x = F(x)
    if x.denominator == 1:
        return str(x.numerator)
    return f"{float(x):.4f}".rstrip("0").rstrip(".")


def inside_poly(p, verts):
    x, y = p
    c = False
    n = len(verts)
    for i in range(n):
        x1, y1 = verts[i]
        x2, y2 = verts[(i + 1) % n]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            c = not c
    return c


class PB:
    """Path builder in unit coordinates."""

    def __init__(self, uf):
        self.u, self.d = uf, []

    def m(self, x, y):
        p = self.u.P(x, y)
        self.d.append(f"M {p[0]:.1f} {p[1]:.1f}")
        return self

    def l(self, x, y):
        p = self.u.P(x, y)
        self.d.append(f"L {p[0]:.1f} {p[1]:.1f}")
        return self

    def a(self, r, x, y, sweep=1, large=0):
        p = self.u.P(x, y)
        rp = r * self.u.sc
        self.d.append(f"A {rp:.1f} {rp:.1f} 0 {large} {sweep} {p[0]:.1f} {p[1]:.1f}")
        return self

    def z(self):
        self.d.append("Z")
        return self

    def get(self):
        return " ".join(self.d)


class UF:
    def __init__(self, x0, y0, x1, y1, w=340, h=230, mx=46, my=32, maxscale=None):
        sc = min((w - 2 * mx) / (x1 - x0), (h - 2 * my) / (y1 - y0))
        if maxscale:
            sc = min(sc, maxscale)
        self.sc = sc
        self.ox = (w - (x1 - x0) * sc) / 2 - x0 * sc
        self.oy = (h - (y1 - y0) * sc) / 2 - y0 * sc
        self.f = Fig(w, h)

    def P(self, x, y):
        return self.ox + x * self.sc, self.oy + y * self.sc

    def poly(self, verts, shade=0.0, dash=False, width=1.6):
        self.f.poly([self.P(*v) for v in verts], shade=shade, dash=dash, width=width)

    def seg(self, a, b, dash=False, width=1.6):
        self.f.line(*self.P(*a), *self.P(*b), dash=dash, width=width)

    def circle(self, c, r, shade=0.0, dash=False):
        p = self.P(*c)
        self.f.circle(p[0], p[1], r * self.sc, shade=shade, dash=dash)

    def dot(self, p):
        self.f.dot(*self.P(*p))

    def path(self, pb, shade=0.0, dash=False, width=1.6):
        self.f.path(pb.get(), shade=shade, dash=dash, width=width)

    def text(self, p, s, dx=0, dy=0, size=13, bold=False, anchor="middle"):
        q = self.P(*p)
        self.f.text(q[0] + dx, q[1] + dy, s, size=size, bold=bold, anchor=anchor)

    def _normal(self, verts, a, b):
        dx, dy = b[0] - a[0], b[1] - a[1]
        n = math.hypot(dx, dy) or 1
        nx, ny = -dy / n, dx / n
        mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
        eps = 3 / self.sc
        if inside_poly((mx + nx * eps, my + ny * eps), verts):
            nx, ny = -nx, -ny
        return nx, ny

    def edge_label(self, verts, i, s, size=13, extra=0):
        a, b = verts[i], verts[(i + 1) % len(verts)]
        nx, ny = self._normal(verts, a, b)
        tw = 0.55 * size * len(s)
        off = 7 + abs(nx) * tw / 2 + abs(ny) * size * 0.5 + extra
        mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
        p = self.P(mx, my)
        self.f.text(p[0] + nx * off, p[1] + ny * off, s, size=size)

    def seg_label(self, a, b, s, away, size=13, extra=0):
        """Label segment a-b, pushed to the side opposite the point `away`."""
        dx, dy = b[0] - a[0], b[1] - a[1]
        n = math.hypot(dx, dy) or 1
        nx, ny = -dy / n, dx / n
        mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
        if (away[0] - mx) * nx + (away[1] - my) * ny > 0:
            nx, ny = -nx, -ny
        tw = 0.55 * size * len(s)
        off = 7 + abs(nx) * tw / 2 + abs(ny) * size * 0.5 + extra
        p = self.P(mx, my)
        self.f.text(p[0] + nx * off, p[1] + ny * off, s, size=size)

    def letter(self, verts, i, s, off=11):
        n = len(verts)
        a, b, c = verts[i - 1], verts[i], verts[(i + 1) % n]
        n1 = self._normal(verts, a, b)
        n2 = self._normal(verts, b, c)
        nx, ny = n1[0] + n2[0], n1[1] + n2[1]
        m = math.hypot(nx, ny) or 1
        p = self.P(*b)
        self.f.text(p[0] + nx / m * off, p[1] + ny / m * off, s, size=13, bold=True)

    def right_mark(self, v, d1, d2, s=9):
        """Right-angle mark at unit point v, with direction vectors d1 and d2 (unit coords)."""
        def u(d):
            n = math.hypot(*d) or 1
            return d[0] / n, d[1] / n
        a, b = u(d1), u(d2)
        p = self.P(*v)
        pts = [(p[0] + a[0] * s, p[1] + a[1] * s),
               (p[0] + (a[0] + b[0]) * s, p[1] + (a[1] + b[1]) * s),
               (p[0] + b[0] * s, p[1] + b[1] * s)]
        self.f.poly(pts, closed=False, width=1.2)

    def svg(self, title="Diagram"):
        return self.f.svg(title)


# ------------------------------------------------------------------ plane figures

def rectilinear(verts, labels, shade=0.0, names=None, dashes=(), w=340, h=230, title="Composite figure"):
    """Polygon with side labels. labels: {side index: text}; side i runs verts[i] -> verts[i+1]."""
    xs, ys = [v[0] for v in verts], [v[1] for v in verts]
    u = UF(min(xs), min(ys), max(xs), max(ys), w, h)
    u.poly(verts, shade=shade)
    for a, b in dashes:
        u.seg(a, b, dash=True, width=1.2)
    for i, s in labels.items():
        u.edge_label(verts, i, s)
    for i, s in (names or {}).items():
        u.letter(verts, i, s)
    return u.svg(title)


def cells_fig(cells, c=30, shade=0.14, title="Figure made of squares"):
    """Grid of unit squares; cells is a set of (col, row)."""
    cols = max(x for x, _ in cells) + 1
    rows = max(y for _, y in cells) + 1
    c = min(c, 290 / cols, 190 / rows)
    w, h = cols * c + 30, rows * c + 30
    f = Fig(w, h)
    for x, y in cells:
        f.rect(15 + x * c, 15 + y * c, c, c, shade=shade, width=1.3)
    return f.svg(title)


def tri_fig(base, height, off, base_lab=None, h_lab=None, names=("A", "B", "C"), side_labs=None,
            shade=0.0, title="Triangle", foot=None):
    """Triangle with base on the bottom, apex above x=off (may be outside the base).
    A=(0,height), B=(base,height), C=(off,0). The height is dashed (or a solid side for a right triangle)."""
    A, B, C = (0, height), (base, height), (off, 0)
    D = (off, height)
    u = UF(min(0, off), 0, max(base, off), height, mx=50, my=34)
    verts = [A, B, C]
    u.poly(verts, shade=shade)
    if off < 0:
        u.seg(A, D, dash=True, width=1.2)
    elif off > base:
        u.seg(B, D, dash=True, width=1.2)
    right = off in (0, base)
    if not right:
        u.seg(C, D, dash=True, width=1.2)
        u.right_mark(D, (1, 0) if off < base / 2 or off > base else (-1, 0), (0, -1))
    else:
        u.right_mark(A if off == 0 else B, (1 if off == 0 else -1, 0), (0, -1))
    if names:
        for i, s in enumerate(names):
            u.letter(verts, i, s)
    if base_lab:
        u.edge_label(verts, 0, base_lab) if False else u.seg_label(A if off >= 0 else A, B, base_lab,
                                                                   (base / 2, 0), extra=0)
    if h_lab:
        mid = (off, height / 2)
        if right:
            u.seg_label(C, D, h_lab, (base / 2, height / 2))
        else:
            sgn = -1 if (off < base / 2) is False and off <= base else 1
            sgn = 1 if (off < base / 2) else -1
            if off < 0:
                sgn = -1
            if off > base:
                sgn = 1
            tw = 0.55 * 13 * len(h_lab)
            if side_labs:
                mid = (off, height * 0.82)
            u.text(mid, h_lab, dx=sgn * (9 + tw / 2))
    if foot:
        u.text(D, foot, dy=14, bold=True)
    for k, s in (side_labs or {}).items():
        i = {"AB": 0, "BC": 1, "CA": 2}[k]
        u.edge_label(verts, i, s)
    return u.svg(title)


# ------------------------------------------------------------------ instruments

def _clock_into(f, cx, cy, r, h, m):
    f.circle(cx, cy, r, width=2)
    minor, major = [], []
    for i in range(60):
        a = math.radians(i * 6)
        L = 9 if i % 5 == 0 else 4
        seg = (f"M{cx + (r - L) * math.sin(a):.0f} {cy - (r - L) * math.cos(a):.0f}"
               f"L{cx + r * math.sin(a):.0f} {cy - r * math.cos(a):.0f}")
        (major if i % 5 == 0 else minor).append(seg)
    f.path("".join(minor), width=0.8)
    f.path("".join(major), width=1.8)
    for i in range(1, 13):
        a = math.radians(i * 30)
        f.text(cx + (r - 21) * math.sin(a), cy - (r - 21) * math.cos(a), i, size=max(10, int(r / 5.5)))
    ha = math.radians((h % 12 + m / 60) * 30)
    ma = math.radians(m * 6)
    f.line(cx, cy, cx + r * 0.5 * math.sin(ha), cy - r * 0.5 * math.cos(ha), width=4.2)
    f.line(cx, cy, cx + r * 0.76 * math.sin(ma), cy - r * 0.76 * math.cos(ma), width=2.2)
    f.dot(cx, cy, 3.5)


def clock_svg(h, m):
    f = Fig(190, 190)
    _clock_into(f, 95, 95, 84, h, m)
    return f.svg(f"Clock face")


def two_clocks_svg(t1, t2, c1="Start", c2="End"):
    f = Fig(380, 215)
    _clock_into(f, 100, 98, 78, *t1)
    _clock_into(f, 280, 98, 78, *t2)
    f.text(100, 202, c1, size=13, bold=True)
    f.text(280, 202, c2, size=13, bold=True)
    return f.svg("Two clock faces")


def ruler_svg(start, end, n=15):
    w = 340
    f = Fig(w, 112)
    left, u = 20, (w - 40) / n
    xa, xb = left + start * u, left + end * u
    f.rect(xa, 12, xb - xa, 26, shade=0.2)
    f.rect(left - 6, 40, n * u + 12, 54, width=1.4)
    for i in range(n * 2 + 1):
        x = left + i * u / 2
        if i % 2 == 0:
            f.line(x, 40, x, 58, width=1.4)
            f.text(x, 76, i // 2, size=12)
        else:
            f.line(x, 40, x, 49, width=1.0)
    f.text(w - 24, 100, "cm", size=11, italic=True)
    return f.svg("Ruler")


def beaker_svg(level, vmax, minor, major, unit="ml"):
    f = Fig(200, 240)
    top, bot, x0, x1 = 28, 214, 70, 140

    def yv(v):
        return bot - (bot - top) * v / vmax
    yl = yv(level)
    f.rect(x0, yl, x1 - x0, bot - yl, shade=0.22, width=1.0)
    f.poly([(x0, top - 8), (x0, bot), (x1, bot), (x1, top - 8)], closed=False, width=2)
    f.line(x0, yl, x1, yl, width=2.2)
    v = 0
    while v <= vmax:
        L = 16 if v % major == 0 else 8
        f.line(x0, yv(v), x0 + L, yv(v), width=1.3 if v % major == 0 else 0.9)
        if v % major == 0:
            f.text(x0 - 7, yv(v), v, anchor="end", size=12)
        v += minor
    f.text(40, 12, f"({unit})", size=11, italic=True)
    return f.svg("Measuring beaker")


def _obl(l, w, h, W=340, H=240, extra_top=0):
    k = min(190 / l, 120 / h)
    fw, fh = l * k, h * k
    d = min(max(w * k * 0.5, 30), 66)
    dx, dy = d * 0.8, d * 0.55
    x0 = (W - (fw + dx)) / 2 + 12
    yb = (H - (fh + dy)) / 2 + dy + fh - 2
    return fw, fh, dx, dy, x0, yb


def tank_svg(L, Wd, H, water=None, labs=("", "", ""), depth_lab=None, title="Rectangular tank"):
    """Cuboid tank in oblique projection. water = depth in the same units as H (or None)."""
    fw, fh, dx, dy, x0, yb = _obl(L, Wd, H)
    f = Fig(340, 240)
    FBL, FBR, FTL, FTR = (x0, yb), (x0 + fw, yb), (x0, yb - fh), (x0 + fw, yb - fh)
    BBL, BBR = (x0 + dx, yb - dy), (x0 + fw + dx, yb - dy)
    BTL, BTR = (x0 + dx, yb - fh - dy), (x0 + fw + dx, yb - fh - dy)
    if water is not None:
        fr = water / H
        ly = yb - fr * fh
        f.poly([(x0, ly), (x0 + fw, ly), FBR, FBL], shade=0.25, width=0.5)
        f.poly([(x0 + fw, ly), (x0 + fw + dx, ly - dy), BBR, FBR], shade=0.25, width=0.5)
        f.poly([(x0, ly), (x0 + fw, ly), (x0 + fw + dx, ly - dy), (x0 + dx, ly - dy)], shade=0.1, width=1.0)
    f.line(*BBL, *BBR, dash=True, width=1.0)
    f.line(*BBL, *BTL, dash=True, width=1.0)
    f.line(*BBL, *FBL, dash=True, width=1.0)
    f.poly([FTL, FTR, FBR, FBL], width=1.8)
    f.poly([FTL, FTR, BTR, BTL], width=1.8)
    f.poly([FTR, FBR, BBR, BTR], width=1.8)
    if labs[0]:
        f.text(x0 + fw / 2, yb + 15, labs[0], size=13)
    if labs[1]:
        f.text(x0 + fw + dx / 2 + 8, yb - dy / 2 + 17, labs[1], size=13, anchor="start")
    if labs[2]:
        f.text(x0 - 7, yb - fh / 2, labs[2], size=13, anchor="end")
    if depth_lab and water is not None:
        ly = yb - water / H * fh
        xx = x0 + 0.3 * fw
        f.line(xx, ly + 1, xx, yb - 1, width=1.2)
        f.line(xx - 4, ly + 1, xx + 4, ly + 1, width=1.2)
        f.line(xx - 4, yb - 1, xx + 4, yb - 1, width=1.2)
        f.text(xx + 7, (ly + yb) / 2, depth_lab, size=13, anchor="start", bold=True)
    return f.svg(title)


def cubes_svg(l, w, h, labs=False):
    c = min(26, 190 / l, 110 / h)
    ddx, ddy = c * 0.5, c * 0.36
    tw, th = l * c + w * ddx, h * c + w * ddy
    x0 = (340 - tw) / 2
    ytop = (230 - th) / 2 + w * ddy
    f = Fig(340, 230)
    # faces
    f.poly([(x0, ytop), (x0 + l * c, ytop), (x0 + l * c + w * ddx, ytop - w * ddy), (x0 + w * ddx, ytop - w * ddy)],
           shade=0.07, width=1.6)
    f.poly([(x0 + l * c, ytop), (x0 + l * c + w * ddx, ytop - w * ddy),
            (x0 + l * c + w * ddx, ytop - w * ddy + h * c), (x0 + l * c, ytop + h * c)], shade=0.17, width=1.6)
    f.rect(x0, ytop, l * c, h * c, width=1.6)
    for i in range(1, l):
        f.line(x0 + i * c, ytop, x0 + i * c, ytop + h * c, width=0.8)
        f.line(x0 + i * c, ytop, x0 + i * c + w * ddx, ytop - w * ddy, width=0.8)
    for j in range(1, h):
        f.line(x0, ytop + j * c, x0 + l * c, ytop + j * c, width=0.8)
        f.line(x0 + l * c, ytop + j * c, x0 + l * c + w * ddx, ytop + j * c - w * ddy, width=0.8)
    for k in range(1, w):
        f.line(x0 + k * ddx, ytop - k * ddy, x0 + l * c + k * ddx, ytop - k * ddy, width=0.8)
        f.line(x0 + l * c + k * ddx, ytop - k * ddy, x0 + l * c + k * ddx, ytop - k * ddy + h * c, width=0.8)
    return f.svg("Cuboid made of unit cubes")


# ------------------------------------------------------------------ self-check
if __name__ == "__main__":
    import xml.dom.minidom as md
    for s in (rectilinear([(0, 0), (6, 0), (6, 3), (3, 3), (3, 6), (0, 6)], {0: "6 cm", 5: "6 cm"}),
              cells_fig({(0, 0), (1, 0), (1, 1)}), tri_fig(8, 5, 11, "8 cm", "5 cm"), tri_fig(8, 5, 3, "8", "5"),
              clock_svg(3, 20), two_clocks_svg((3, 20), (5, 5)), ruler_svg(2, 9), beaker_svg(350, 500, 50, 100),
              tank_svg(40, 25, 30, 18, ("40 cm", "25 cm", "30 cm"), "18 cm"), cubes_svg(4, 3, 2)):
        md.parseString(s)
    print("figures_C OK")
