"""Small SVG toolkit for question diagrams (angles, composite figures, circles, graphs, pie charts).

Figures use currentColor, so they follow the page's text colour in light and dark themes.
Shading uses fill-opacity, never a fixed colour. Every figure is a self-contained <svg> string
that check_math.py parses as XML.

Diagrams are "not drawn to scale" in PSLE style when the numbers would look odd, but we draw
them roughly to scale so a child is never misled by a wildly wrong picture.

    python scripts/quiz/math/figures.py      # self-check
"""
import math
from xml.sax.saxutils import escape

FONT = "font-family=\"Literata, Georgia, serif\""


class Fig:
    def __init__(self, w=320, h=220, pad=8):
        self.w, self.h, self.pad = w, h, pad
        self.parts = []

    # ---- primitives
    def line(self, x1, y1, x2, y2, dash=False, width=1.6):
        d = ' stroke-dasharray="5 4"' if dash else ""
        self.parts.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
                          f'stroke="currentColor" stroke-width="{width}"{d}/>')

    def poly(self, pts, shade=0.0, closed=True, dash=False, width=1.6):
        tag = "polygon" if closed else "polyline"
        p = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
        fill = f'fill="currentColor" fill-opacity="{shade}"' if shade else 'fill="none"'
        d = ' stroke-dasharray="5 4"' if dash else ""
        self.parts.append(f'<{tag} points="{p}" {fill} stroke="currentColor" stroke-width="{width}"{d}/>')

    def rect(self, x, y, w, h, shade=0.0, width=1.6):
        self.poly([(x, y), (x + w, y), (x + w, y + h), (x, y + h)], shade=shade, width=width)

    def circle(self, cx, cy, r, shade=0.0, dash=False, width=1.6):
        fill = f'fill="currentColor" fill-opacity="{shade}"' if shade else 'fill="none"'
        d = ' stroke-dasharray="5 4"' if dash else ""
        self.parts.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" {fill} stroke="currentColor" '
                          f'stroke-width="{width}"{d}/>')

    def dot(self, x, y, r=2.5):
        self.parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="currentColor"/>')

    def path(self, d, shade=0.0, width=1.6, dash=False):
        fill = f'fill="currentColor" fill-opacity="{shade}"' if shade else 'fill="none"'
        ds = ' stroke-dasharray="5 4"' if dash else ""
        self.parts.append(f'<path d="{d}" {fill} stroke="currentColor" stroke-width="{width}"{ds}/>')

    def text(self, x, y, s, anchor="middle", size=14, bold=False, italic=False):
        w = ' font-weight="600"' if bold else ""
        it = ' font-style="italic"' if italic else ""
        self.parts.append(f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="{anchor}" dominant-baseline="middle" '
                          f'font-size="{size}" {FONT} fill="currentColor"{w}{it}>{escape(str(s))}</text>')

    # ---- geometry helpers (angles in degrees, y axis points down as in SVG)
    @staticmethod
    def polar(cx, cy, r, deg):
        a = math.radians(deg)
        return cx + r * math.cos(a), cy - r * math.sin(a)

    def arc(self, cx, cy, r, a0, a1, shade=0.0, sector=False, width=1.6):
        """Arc (or pie sector) from a0 to a1 degrees, counter-clockwise, maths convention."""
        x0, y0 = self.polar(cx, cy, r, a0)
        x1, y1 = self.polar(cx, cy, r, a1)
        large = 1 if (a1 - a0) % 360 > 180 else 0
        d = f"M {x0:.1f} {y0:.1f} A {r:.1f} {r:.1f} 0 {large} 0 {x1:.1f} {y1:.1f}"
        if sector:
            d = f"M {cx:.1f} {cy:.1f} L {x0:.1f} {y0:.1f} A {r:.1f} {r:.1f} 0 {large} 0 {x1:.1f} {y1:.1f} Z"
        self.path(d, shade=shade, width=width)

    def angle_mark(self, vx, vy, p1, p2, label=None, r=22, size=13):
        """Mark the angle at vertex V between rays V->p1 and V->p2 (the smaller one), with a label."""
        a1 = math.degrees(math.atan2(vy - p1[1], p1[0] - vx))
        a2 = math.degrees(math.atan2(vy - p2[1], p2[0] - vx))
        start, sweep = a1, (a2 - a1) % 360
        if sweep > 180:
            start, sweep = a2, 360 - sweep
        if abs(sweep - 90) < 0.5:
            self.right_angle(vx, vy, p1, p2)
        else:
            self.arc(vx, vy, r, start, start + sweep, width=1.2)
        if label is not None:
            mx, my = self.polar(vx, vy, r + 14, start + sweep / 2)
            self.text(mx, my, label, size=size)

    def right_angle(self, vx, vy, p1, p2, s=10):
        def unit(p):
            dx, dy = p[0] - vx, p[1] - vy
            n = math.hypot(dx, dy) or 1
            return dx / n, dy / n
        u, v = unit(p1), unit(p2)
        a = (vx + u[0] * s, vy + u[1] * s)
        b = (vx + u[0] * s + v[0] * s, vy + u[1] * s + v[1] * s)
        c = (vx + v[0] * s, vy + v[1] * s)
        self.poly([a, b, c], closed=False, width=1.2)

    def side_label(self, p1, p2, s, offset=12, size=13, inside=None):
        """Label the middle of segment p1-p2, pushed sideways. inside=(x, y) pushes away from that point."""
        mx, my = (p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2
        dx, dy = p2[0] - p1[0], p2[1] - p1[1]
        n = math.hypot(dx, dy) or 1
        nx, ny = -dy / n, dx / n
        if inside is not None and (inside[0] - mx) * nx + (inside[1] - my) * ny > 0:
            nx, ny = -nx, -ny
        self.text(mx + nx * offset, my + ny * offset, s, size=size)

    def point_label(self, x, y, s, dx=0, dy=-12, size=13):
        self.text(x + dx, y + dy, s, size=size, bold=True)

    def svg(self, title="Diagram"):
        body = "".join(self.parts)
        return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.w} {self.h}" '
                f'role="img" aria-label="{escape(title)}" class="qfig">{body}</svg>')


# ---------------------------------------------------------------- charts

def bar_chart(labels, values, title="", ylabel="", step=None, w=340, h=230, horizontal=False):
    """Vertical bar chart with gridlines. values are numbers; step is the gridline interval."""
    f = Fig(w, h)
    top = max(values)
    step = step or nice_step(top)
    ymax = step * math.ceil(top / step)
    left, right, tp, bot = 48, w - 12, 26 if title else 12, h - 34
    if title:
        f.text(w / 2, 12, title, size=13, bold=True)
    k = 0
    while k * step <= ymax:
        y = bot - (bot - tp) * k * step / ymax
        f.line(left, y, right, y, dash=k > 0, width=0.8)
        f.text(left - 6, y, fmt_num(k * step), anchor="end", size=11)
        k += 1
    f.line(left, tp, left, bot)
    n = len(values)
    slot = (right - left) / n
    for i, (lab, v) in enumerate(zip(labels, values)):
        bh = (bot - tp) * v / ymax
        x = left + i * slot + slot * 0.2
        f.rect(x, bot - bh, slot * 0.6, bh, shade=0.25)
        f.text(left + i * slot + slot / 2, bot + 14, lab, size=11)
    if ylabel:
        f.parts.append(f'<text x="12" y="{(tp + bot) / 2:.1f}" transform="rotate(-90 12 {(tp + bot) / 2:.1f})" '
                       f'text-anchor="middle" font-size="11" {FONT} fill="currentColor">{escape(ylabel)}</text>')
    return f.svg(title or "Bar graph")


def line_graph(labels, values, title="", step=None, w=340, h=230):
    f = Fig(w, h)
    top = max(values)
    step = step or nice_step(top)
    ymax = step * math.ceil(top / step)
    left, right, tp, bot = 48, w - 16, 26 if title else 12, h - 34
    if title:
        f.text(w / 2, 12, title, size=13, bold=True)
    k = 0
    while k * step <= ymax:
        y = bot - (bot - tp) * k * step / ymax
        f.line(left, y, right, y, dash=k > 0, width=0.8)
        f.text(left - 6, y, fmt_num(k * step), anchor="end", size=11)
        k += 1
    f.line(left, tp, left, bot)
    n = len(values)
    xs = [left + (right - left) * (i + 0.5) / n for i in range(n)]
    ys = [bot - (bot - tp) * v / ymax for v in values]
    f.poly(list(zip(xs, ys)), closed=False, width=2)
    for x, y, lab in zip(xs, ys, labels):
        f.dot(x, y)
        f.text(x, bot + 14, lab, size=11)
    return f.svg(title or "Line graph")


def pie_chart(labels, parts, title="", show=None, w=320, h=220):
    """Pie chart; parts are fractions or degrees (any positive numbers, scaled to 360).
    show: list of label strings drawn in each sector (default: the labels)."""
    f = Fig(w, h)
    cx, cy, r = w / 2, h / 2 + (8 if title else 0), min(w, h) / 2 - 24
    if title:
        f.text(w / 2, 12, title, size=13, bold=True)
    total = sum(parts)
    a = 90.0
    for i, (lab, p) in enumerate(zip(labels, parts)):
        sweep = 360 * p / total
        f.arc(cx, cy, r, a, a + sweep, sector=True, shade=0.08 + 0.12 * (i % 3))
        mx, my = f.polar(cx, cy, r * 0.62, a + sweep / 2)
        f.text(mx, my, (show or labels)[i], size=11)
        a += sweep
    return f.svg(title or "Pie chart")


def nice_step(top):
    for s in (1, 2, 5, 10, 20, 25, 50, 100, 200, 250, 500, 1000, 2000, 5000):
        if top / s <= 8:
            return s
    return 10 ** int(math.log10(top))


def fmt_num(x):
    return str(int(x)) if float(x).is_integer() else f"{x:g}"


if __name__ == "__main__":
    import xml.dom.minidom as md
    f = Fig()
    A, B, C = (30, 190), (290, 190), (120, 40)
    f.poly([A, B, C], shade=0.1)
    f.angle_mark(*A, B, C, "40°")
    f.angle_mark(*C, A, B, "x")
    f.side_label(A, B, "12 cm", inside=C)
    for s in (f.svg("Triangle"), bar_chart(list("ABCD"), [12, 30, 18, 25], "Books read"),
              line_graph(["Mon", "Tue", "Wed"], [3, 7, 5]), pie_chart(["Red", "Blue", "Green"], [1, 2, 1])):
        md.parseString(s)
    print("figures OK")
