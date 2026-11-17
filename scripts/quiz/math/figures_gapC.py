"""Figure helpers for the Group C outcome-gap templates (drawing outcomes turned into A-D / reading MCQs).

Rulers with lines, grids with shapes and line segments, an oblique-projection engine for 2D drawings of solids
(hidden edges dashed), isometric cube stacks as panels, and a small protractor for panels.
All figures use currentColor via figures.Fig.
"""
import math
from xml.sax.saxutils import escape

from figures import Fig, FONT
from figures_D import panels  # noqa: F401  (re-exported for the topic modules)


# ------------------------------------------------------------------ rulers


def ruler_line_svg(start, end10, n=15, name=None):
    """A line segment above a cm ruler. start: whole cm mark; end10: right end in tenths of a cm."""
    w = 340
    f = Fig(w, 118)
    left, u = 20, (w - 40) / n
    xa, xb = left + start * u, left + end10 / 10 * u
    f.line(xa, 22, xb, 22, width=3.2)
    f.line(xa, 15, xa, 29, width=1.6)
    f.line(xb, 15, xb, 29, width=1.6)
    f.line(xa, 30, xa, 44, dash=True, width=0.9)
    f.line(xb, 30, xb, 44, dash=True, width=0.9)
    if name:
        f.text((xa + xb) / 2, 8, name, size=12, bold=True)
    f.rect(left - 6, 46, n * u + 12, 54, width=1.4)
    for i in range(n * 2 + 1):
        x = left + i * u / 2
        if i % 2 == 0:
            f.line(x, 46, x, 64, width=1.4)
            f.text(x, 82, i // 2, size=12)
        else:
            f.line(x, 46, x, 55, width=1.0)
    f.text(w - 24, 108, "cm", size=11, italic=True)
    return f.svg("Line above a ruler")


def ruler_lines_svg(lines, n=15):
    """Several labelled lines (letter, start, end in whole cm) above a cm ruler; faint cm guides."""
    w = 340
    k = len(lines)
    top = 12 + 22 * k
    f = Fig(w, top + 76)
    left, u = 20, (w - 40) / n
    for i in range(n + 1):
        f.parts.append(f'<line x1="{left + i * u:.1f}" y1="6" x2="{left + i * u:.1f}" y2="{top}" stroke="currentColor" '
                       f'stroke-opacity="0.18" stroke-width="0.8"/>')
    for j, (lab, a, b) in enumerate(lines):
        y = 16 + 22 * j
        f.line(left + a * u, y, left + b * u, y, width=3.2)
        f.line(left + a * u, y - 6, left + a * u, y + 6, width=1.6)
        f.line(left + b * u, y - 6, left + b * u, y + 6, width=1.6)
        f.text(left + a * u - 12, y, lab, size=13, bold=True) if a >= 1 else f.text(left + b * u + 12, y, lab, size=13, bold=True)
    f.rect(left - 6, top + 2, n * u + 12, 54, width=1.4)
    for i in range(n * 2 + 1):
        x = left + i * u / 2
        if i % 2 == 0:
            f.line(x, top + 2, x, top + 20, width=1.4)
            f.text(x, top + 38, i // 2, size=12)
        else:
            f.line(x, top + 2, x, top + 11, width=1.0)
    f.text(w - 24, top + 66, "cm", size=11, italic=True)
    return f.svg("Lines above a ruler")


# ------------------------------------------------------------------ grids with shapes


def shape_grid(cols, rows, polys=(), cell=15, dots=False, pad_tl=22, pad_br=8, shade=0.14, segs=(), title="Grid"):
    """Fig with a square grid (or dot grid) and polygons (vertex lists in grid units, y down).
    segs: [(label, (x1,y1), (x2,y2), thick)] line segments with a letter near the far end."""
    w, h = pad_tl + cols * cell + pad_br, pad_tl + rows * cell + pad_br
    f = Fig(w, h)
    ox = oy = pad_tl
    if dots:
        d = "".join(f"M{ox + c * cell:.0f},{oy + r * cell:.0f}h0.1" for c in range(cols + 1) for r in range(rows + 1))
        f.parts.append(f'<path d="{d}" stroke="currentColor" stroke-width="3.4" stroke-linecap="round" fill="none"/>')
    else:
        d = "".join(f"M{ox + c * cell:.0f},{oy}v{rows * cell}" for c in range(cols + 1))
        d += "".join(f"M{ox},{oy + r * cell:.0f}h{cols * cell}" for r in range(rows + 1))
        f.parts.append(f'<path d="{d}" stroke="currentColor" stroke-width="0.6" fill="none"/>')
        f.rect(ox, oy, cols * cell, rows * cell, width=1.2)
    for poly in polys:
        f.poly([(ox + x * cell, oy + y * cell) for x, y in poly], shade=shade, width=2.2)
    for lab, p, q, thick in segs:
        f.line(ox + p[0] * cell, oy + p[1] * cell, ox + q[0] * cell, oy + q[1] * cell, width=2.6 if thick else 1.8)
        dx, dy = q[0] - p[0], q[1] - p[1]
        d = math.hypot(dx, dy)
        f.text(ox + q[0] * cell + dx / d * 10, oy + q[1] * cell + dy / d * 10, lab, size=13, bold=True)
        if thick:
            f.text(ox + p[0] * cell - dx / d * 10, oy + p[1] * cell - dy / d * 10, "P", size=13, bold=True)
    return f


def source_and_panels(src, figs, title="Figure and four copies", gap=10, label="Figure"):
    """Source Fig at the left with a caption, and the A-D option Figs as a 2 x 2 block to its right."""
    pw, ph = figs[0].w, figs[0].h
    W = src.w + 22 + 2 * pw + gap
    H = max(2 * ph + gap, src.h + 24)
    sy = (H - src.h) / 2 + 8
    out = [f'<g transform="translate(0,{sy:.1f})">{"".join(src.parts)}</g>',
           f'<text x="{src.w / 2:.1f}" y="{sy - 8:.1f}" text-anchor="middle" font-size="13" {FONT} fill="currentColor" '
           f'font-weight="700">{escape(label)}</text>']
    for i, g in enumerate(figs):
        x, y = src.w + 22 + (i % 2) * (pw + gap), (i // 2) * (ph + gap)
        out.append(f'<g transform="translate({x},{y})">{"".join(g.parts)}'
                   f'<text x="12" y="14" font-size="15" {FONT} fill="currentColor" font-weight="700">{"ABCD"[i]}</text>'
                   f'<rect x="0.5" y="0.5" width="{pw - 1}" height="{ph - 1}" fill="none" stroke="currentColor" '
                   f'stroke-opacity="0.25" stroke-width="1" rx="6"/></g>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W:.0f} {H:.0f}" role="img" '
            f'aria-label="{escape(title)}" class="qfig">{"".join(out)}</svg>')


# ------------------------------------------------------------------ isometric stacks as panels


def iso_fig(heights, W=170, H=150, s=None):
    """Isometric drawing of a stack (heights[i][j], non-increasing in i and j) fitted into a W x H Fig."""
    ni, nj = len(heights), len(heights[0])
    top = max(max(r) for r in heights)
    c30 = math.cos(math.radians(30))
    if s is None:
        s = min((W - 24) / ((ni + nj) * c30), (H - 36) / ((ni + nj) * 0.5 + top))
    tw = (ni + nj) * c30 * s
    th = (ni + nj) * s * 0.5 + top * s
    ox = (W - tw) / 2 + nj * c30 * s
    oy = (H - th) / 2 + 8 + top * s
    f = Fig(W, H)

    def P(i, j, k):
        return (ox + (i - j) * c30 * s, oy + (i + j) * s * 0.5 - k * s)
    cubes = sorted(((i, j, k) for i in range(ni) for j in range(nj) for k in range(heights[i][j])),
                   key=lambda c: (sum(c), c))
    have = set(cubes)
    top_d, right_d, left_d = [], [], []

    def sub(pts):
        return "M" + "L".join(f"{x:.0f},{y:.0f}" for x, y in pts) + "Z"
    for i, j, k in cubes:
        if (i, j, k + 1) not in have:
            top_d.append(sub([P(i, j, k + 1), P(i + 1, j, k + 1), P(i + 1, j + 1, k + 1), P(i, j + 1, k + 1)]))
        if (i + 1, j, k) not in have:
            right_d.append(sub([P(i + 1, j, k), P(i + 1, j + 1, k), P(i + 1, j + 1, k + 1), P(i + 1, j, k + 1)]))
        if (i, j + 1, k) not in have:
            left_d.append(sub([P(i, j + 1, k), P(i + 1, j + 1, k), P(i + 1, j + 1, k + 1), P(i, j + 1, k + 1)]))
    for d, shade in ((top_d, 0.0), (right_d, 0.3), (left_d, 0.15)):
        if d:
            f.path("".join(d), shade=shade, width=1.1)
    return f


# ------------------------------------------------------------------ 2D drawings of solids (oblique projection)

_A, _B = 0.55, 0.38  # depth goes up and to the right


def _regular(n, r, cx, cy):
    return [(cx + r * math.cos(2 * math.pi * k / n + math.pi / 2 + math.pi / n * (n % 2 == 0)),
             cy - r * math.sin(2 * math.pi * k / n + math.pi / 2 + math.pi / n * (n % 2 == 0))) for k in range(n)]


def solid_model(kind, a=1.0, b=1.0, c=1.0):
    """(vertices, faces) in 3D (x right, y up, z away from the viewer). a, b, c: length, height, depth."""
    if kind in ("cube", "cuboid"):
        l, h, d = a, b, c
        v = [(0, 0, 0), (l, 0, 0), (l, h, 0), (0, h, 0), (0, 0, d), (l, 0, d), (l, h, d), (0, h, d)]
        faces = [[0, 1, 2, 3], [4, 5, 6, 7], [0, 3, 7, 4], [1, 2, 6, 5], [0, 1, 5, 4], [3, 2, 6, 7]]
    elif kind == "tri_prism":
        w, h, d = a, b, c
        t = [(0, 0), (w, 0), (w / 2, h)]
        v = [(x, y, 0) for x, y in t] + [(x, y, d) for x, y in t]
        faces = [[0, 1, 2], [3, 4, 5], [0, 1, 4, 3], [1, 2, 5, 4], [0, 2, 5, 3]]
    elif kind in ("pent_prism", "hex_prism"):
        n = 5 if kind == "pent_prism" else 6
        poly = _regular(n, a / 2, a / 2, b / 2)
        v = [(x, y, 0) for x, y in poly] + [(x, y, c) for x, y in poly]
        faces = [list(range(n)), list(range(n, 2 * n))] + [[k, (k + 1) % n, n + (k + 1) % n, n + k] for k in range(n)]
    elif kind == "sq_pyr":
        l, h, d = a, b, c
        v = [(0, 0, 0), (l, 0, 0), (l, 0, d), (0, 0, d), (l / 2, h, d / 2)]
        faces = [[0, 1, 2, 3], [0, 1, 4], [1, 2, 4], [2, 3, 4], [3, 0, 4]]
    elif kind == "tri_pyr":
        l, h, d = a, b, c
        v = [(0, 0, 0), (l, 0, 0), (l / 2, 0, d), (l / 2, h, d / 3)]
        faces = [[0, 1, 2], [0, 1, 3], [1, 2, 3], [2, 0, 3]]
    else:
        raise ValueError(kind)
    return v, faces


def _normal(v, face, centre):
    p0, p1, p2 = (v[i] for i in face[:3])
    u = [p1[k] - p0[k] for k in range(3)]
    w = [p2[k] - p0[k] for k in range(3)]
    n = [u[1] * w[2] - u[2] * w[1], u[2] * w[0] - u[0] * w[2], u[0] * w[1] - u[1] * w[0]]
    if sum(n[k] * (p0[k] - centre[k]) for k in range(3)) < 0:
        n = [-x for x in n]
    return n


def solid_edges(kind, a=1.0, b=1.0, c=1.0):
    """[(i, j, visible)] for every edge, from the model (visible if it borders a face turned towards the viewer)."""
    v, faces = solid_model(kind, a, b, c)
    centre = [sum(p[k] for p in v) / len(v) for k in range(3)]
    view = (_A, _B, -1.0)
    vis_face = [sum(n * u for n, u in zip(_normal(v, fc, centre), view)) > 1e-9 for fc in faces]
    edges = {}
    for fc, vis in zip(faces, vis_face):
        for k in range(len(fc)):
            e = tuple(sorted((fc[k], fc[(k + 1) % len(fc)])))
            edges[e] = edges.get(e, False) or vis
    return v, [(i, j, vis) for (i, j), vis in sorted(edges.items())]


def solid_fig(kind, a=1.0, b=1.0, c=1.0, W=150, H=135, labels=(), title="Drawing of a solid"):
    """Fig with a 2D drawing of a solid: visible edges solid, hidden edges dashed.
    labels: [(vertex i, vertex j, text)] placed beside that edge."""
    v, edges = solid_edges(kind, a, b, c)
    pr = [(x + _A * z, y + _B * z) for x, y, z in v]
    xs, ys = [p[0] for p in pr], [p[1] for p in pr]
    padx, pady_t, pady_b = (34 if labels else 16), (30 if not labels else 24), 14
    sc = min((W - 2 * padx) / (max(xs) - min(xs)), (H - pady_t - pady_b) / (max(ys) - min(ys)))
    X0 = (W - (max(xs) - min(xs)) * sc) / 2 - min(xs) * sc
    Y0 = pady_t + (H - pady_t - pady_b - (max(ys) - min(ys)) * sc) / 2 + max(ys) * sc
    S = [(X0 + x * sc, Y0 - y * sc) for x, y in pr]
    f = Fig(W, H)
    for i, j, vis in edges:
        f.line(*S[i], *S[j], dash=not vis, width=1.7 if vis else 1.1)
    cx, cy = sum(p[0] for p in S) / len(S), sum(p[1] for p in S) / len(S)
    for i, j, t in labels:
        mx, my = (S[i][0] + S[j][0]) / 2, (S[i][1] + S[j][1]) / 2
        dx, dy = mx - cx, my - cy
        d = math.hypot(dx, dy) or 1
        f.text(mx + dx / d * 15, my + dy / d * 11, t, size=12)
    return f


# ------------------------------------------------------------------ protractor panels


def mini_protractor(alpha, base_right, W=200, H=116, R=84):
    """Small protractor, centre Q. Baseline QP along the 0 mark on one side; arm QR at alpha degrees from QP."""
    cx, cy = W / 2, H - 12
    f = Fig(W, H)
    f.path(f"M {cx - R} {cy} A {R} {R} 0 0 1 {cx + R} {cy} Z", shade=0.05, width=1.1)
    d = ""
    for a in range(0, 181, 5):
        L = 11 if a % 10 == 0 else 6
        c_, s_ = math.cos(math.radians(a)), math.sin(math.radians(a))
        d += f"M{cx + R * c_:.0f},{cy - R * s_:.0f}L{cx + (R - L) * c_:.0f},{cy - (R - L) * s_:.0f}"
    f.parts.append(f'<path d="{d}" stroke="currentColor" stroke-width="0.8" fill="none"/>')
    f.parts.append(f'<g font-size="7.5" text-anchor="middle" dominant-baseline="middle" fill="currentColor" {FONT}>')
    for a in range(0, 181, 10):
        for off, val in ((R + 8, a), (R - 20, 180 - a)):
            x, y = cx + off * math.cos(math.radians(a)), cy - off * math.sin(math.radians(a))
            f.parts.append(f'<text x="{x:.0f}" y="{y:.0f}">{val}</text>')
    f.parts.append('</g>')
    arm = alpha if base_right else 180 - alpha
    bx = cx + (R + 12 if base_right else -(R + 12))
    f.line(cx, cy, bx, cy, width=2)
    ex, ey = cx + (R + 12) * math.cos(math.radians(arm)), cy - (R + 12) * math.sin(math.radians(arm))
    f.line(cx, cy, ex, ey, width=2)
    f.dot(cx, cy, 2.6)
    f.text(cx, cy + 8, "Q", size=11, bold=True)
    return f
