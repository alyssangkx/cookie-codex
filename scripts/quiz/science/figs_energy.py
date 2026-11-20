"""Code-drawn energy diagrams (black and white): echain(), track(), pendulum(), springboard()."""
import math
from fillkit import svg, txt, AH, arrow


def echain(labels, caption=None, W=None):
    """Boxes joined by arrows. A label may hold two lines separated by '|'. Use '?' or a letter for an unknown box."""
    n = len(labels)
    bw, gap = 92, 34
    W = W or n * bw + (n - 1) * gap + 20
    bh, y = 46, 38 if caption else 14
    b = AH + (txt(W / 2, 18, caption, 13, bold=True) if caption else "")
    x = 10
    for i, lab in enumerate(labels):
        b += f'<rect x="{x}" y="{y}" width="{bw}" height="{bh}" rx="5"/>'
        parts = lab.split("|")
        for k, p in enumerate(parts):
            b += txt(x + bw / 2, y + bh / 2 + 5 - (len(parts) - 1) * 8 + k * 16, p, 13)
        if i < n - 1:
            b += arrow(x + bw + 3, y + bh / 2, x + bw + gap - 4, y + bh / 2, 2)
        x += bw + gap
    return svg(W, y + bh + 14, b)


def _profile(shape, t):
    """Height 0..1 of the track at t in 0..1."""
    if shape == "slope":      # down a ramp then flat
        return max(0.0, 1 - t / 0.45)
    if shape == "valley":     # down one side and up the other
        return (1 - t / 0.5) if t < 0.5 else (t - 0.5) / 0.5 * 0.8
    if shape == "hills":      # roller coaster: high start, dip, lower hill, dip
        k = [(0, 1.0), (0.3, 0.05), (0.55, 0.6), (0.8, 0.0), (1, 0.15)]
        for (a, ha), (b_, hb) in zip(k, k[1:]):
            if a <= t <= b_:
                u = (t - a) / (b_ - a)
                return ha + (hb - ha) * (1 - math.cos(math.pi * u)) / 2
    return 0.0


def track(shape, points, W=340, H=170, ball=None, caption=None):
    """A track drawn as a line. points = {letter: t (0..1)} get a dot and a letter; ball = letter whose dot is drawn as a ball."""
    x0, x1, ybase, ytop = 20, W - 20, H - 26, 40 if caption else 26
    b = (txt(W / 2, 16, caption, 13, bold=True) if caption else "")
    pts = []
    for i in range(61):
        t = i / 60
        pts.append(f"{x0 + t * (x1 - x0):.1f},{ybase - _profile(shape, t) * (ybase - ytop - 20):.1f}")
    b += f'<polyline points="{" ".join(pts)}" stroke-width="3"/>'
    b += f'<line x1="{x0}" y1="{ybase + 6}" x2="{x1}" y2="{ybase + 6}" stroke-width="1" stroke-dasharray="3 4"/>'
    for L, t in points.items():
        x = x0 + t * (x1 - x0)
        y = ybase - _profile(shape, t) * (ybase - ytop - 20)
        if ball == L:
            b += f'<circle cx="{x:.1f}" cy="{y - 9:.1f}" r="8" fill="none" stroke-width="2"/>'
        else:
            b += f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3" fill="currentColor"/>'
        b += txt(x, y - 22 if ball == L else y - 10, L, 15, bold=True) if ball != L else txt(x, y - 22, L, 15, bold=True)
    return svg(W, H, b)


def pendulum(W=300, H=190, caption=None):
    """A bob on a string at three positions: A (left, high), B (lowest, middle), C (right, high)."""
    px, py, L = W / 2, 22, 120
    a = math.radians(40)
    b = (txt(W / 2, 14, caption, 13, bold=True) if caption else "")
    b += f'<line x1="{px - 40}" y1="{py - 4}" x2="{px + 40}" y2="{py - 4}" stroke-width="4"/>'
    for lab, ang, solid in (("A", -a, False), ("B", 0, True), ("C", a, False)):
        x, y = px + L * math.sin(ang), py + L * math.cos(ang)
        b += f'<line x1="{px}" y1="{py}" x2="{x:.1f}" y2="{y:.1f}" stroke-width="{2 if solid else 1}"' + ('' if solid else ' stroke-dasharray="4 3"') + '/>'
        b += f'<circle cx="{x:.1f}" cy="{y:.1f}" r="11" fill="{"currentColor" if solid else "none"}"/>'
        b += txt(x + (-22 if ang < 0 else 22 if ang > 0 else 0), y + (4 if ang else 30), lab, 15, bold=True)
    return svg(W, H, b)


def springboard(W=300, H=170):
    """A diver standing on the end of a bent springboard (no labels)."""
    b = '<rect x="20" y="110" width="50" height="40"/><path d="M70 112 Q150 134 236 128" stroke-width="5"/>'
    b += '<circle cx="232" cy="82" r="8"/><line x1="232" y1="90" x2="232" y2="118"/><line x1="232" y1="98" x2="218" y2="110"/><line x1="232" y1="98" x2="246" y2="110"/><line x1="232" y1="118" x2="224" y2="128"/><line x1="232" y1="118" x2="240" y2="128"/>'
    b += '<line x1="20" y1="158" x2="280" y2="158" stroke-dasharray="4 4"/>'
    return svg(W, H, b)
