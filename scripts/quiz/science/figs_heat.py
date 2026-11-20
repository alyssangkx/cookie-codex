"""Code-drawn heat set-ups (black and white): blocks(), thermometer(), rods(), ball_ring(), flask_tube(), balloon(), touching(), bath()."""
from fillkit import svg, txt, AH, arrow


def thermometer(value, lo=0, hi=50, major=10, minor=2, caption=None, W=150, H=270, unit="°C"):
    """Vertical liquid-in-glass thermometer. The liquid reaches `value` on the scale (ticks every `minor`, numbers every `major`)."""
    top, bot = (54 if caption else 38), H - 54
    tx = 78
    b = (txt(W / 2, 16, caption, 13, bold=True) if caption else "") + txt(tx - 36, top - 12, unit, 12)
    b += f'<rect x="{tx - 7}" y="{top - 6}" width="14" height="{bot - top + 12}" rx="7" stroke-width="2"/>'
    b += f'<circle cx="{tx}" cy="{bot + 20}" r="14" fill="currentColor"/>'
    b += f'<rect x="{tx - 7}" y="{bot}" width="14" height="22" fill="#fff" stroke="none"/><rect x="{tx - 3}" y="{bot}" width="6" height="22" fill="currentColor" stroke="none"/>'
    def y(v):
        return bot - (v - lo) / (hi - lo) * (bot - top)
    v = lo
    while v <= hi + 1e-9:
        mj = abs(v / major - round(v / major)) < 1e-9
        b += f'<line x1="{tx - 7 - (12 if mj else 6)}" y1="{y(v):.1f}" x2="{tx - 7}" y2="{y(v):.1f}" stroke-width="{1.6 if mj else 1}"/>'
        if mj:
            b += txt(tx - 28, y(v) + 4, f"{v:g}", 11, anchor="end")
        v += minor
    b += f'<rect x="{tx - 3}" y="{y(value):.1f}" width="6" height="{bot - y(value):.1f}" fill="currentColor" stroke="none"/>'
    return svg(W, H, b)


def rods(names, fallen, caption=None, W=380):
    """Rods of different materials, one end in hot water; 3 wax-and-pin marks on each; fallen[i] pins have dropped (nearest the hot end first)."""
    n = len(names)
    top = 46 if caption else 20
    gap = 38
    H = top + n * gap + 40
    b = AH + (txt(W / 2, 16, caption, 13, bold=True) if caption else "")
    b += f'<rect x="10" y="{top - 10}" width="70" height="{n * gap + 6}" rx="4"/>' + txt(45, top + n * gap / 2 - 4, "hot", 12) + txt(45, top + n * gap / 2 + 10, "water", 12)
    ground = top + n * gap + 8
    b += f'<line x1="80" y1="{ground}" x2="{W - 10}" y2="{ground}" stroke-width="1" stroke-dasharray="3 4"/>'
    for i, nm in enumerate(names):
        y = top + i * gap + 8
        b += f'<rect x="80" y="{y - 4}" width="{W - 120}" height="8" fill="none"/>' + txt(W - 18, y + 5, nm, 14, bold=True)
        for k in range(3):
            x = 130 + k * 70
            if k < fallen[i]:
                b += f'<line x1="{x - 8}" y1="{ground - 3}" x2="{x + 8}" y2="{ground - 3}" stroke-width="2"/>'
            else:
                b += f'<line x1="{x}" y1="{y + 4}" x2="{x}" y2="{y + 17}" stroke-width="2"/><circle cx="{x}" cy="{y + 4}" r="2.5" fill="currentColor"/>'
    return svg(W, H, b)


def ball_ring(through, caption=None, W=300, H=200):
    """A metal ball on a chain and a ring on a stand. through=True: the ball hangs through the ring; False: it rests on top of the ring."""
    b = (txt(W / 2, 16, caption, 13, bold=True) if caption else "")
    cx, ry = 150, 108
    b += f'<ellipse cx="{cx}" cy="{ry}" rx="34" ry="8" stroke-width="3"/><line x1="{cx + 34}" y1="{ry}" x2="{cx + 90}" y2="{ry}" stroke-width="3"/><line x1="{cx + 90}" y1="{ry}" x2="{cx + 90}" y2="{H - 14}" stroke-width="3"/><line x1="{cx + 60}" y1="{H - 14}" x2="{cx + 120}" y2="{H - 14}" stroke-width="3"/>'
    by = ry + 36 if through else ry - 24
    b += f'<line x1="{cx}" y1="30" x2="{cx}" y2="{by - 20}" stroke-width="1.5"/><circle cx="{cx}" cy="{by}" r="22" fill="currentColor" fill-opacity="0.2"/>'
    return svg(W, H, b)


def _flask(cx, cy, r, tube_h, tube_w=10):
    return (f'<path d="M{cx - tube_w / 2} {cy - tube_h - r + 6} V{cy - r * 0.92} A{r} {r} 0 1 0 {cx + tube_w / 2} {cy - r * 0.92} V{cy - tube_h - r + 6}" stroke-width="2.5"/>')


def flask_tube(level, start=None, bath="water bath", caption=None, W=260, H=274):
    """A flask full of coloured water with a thin tube; the liquid is at height `level` (0..1) in the tube; a dashed mark shows `start`."""
    b = (txt(W / 2, 16, caption, 13, bold=True) if caption else "")
    cx, cy, r, th = 130, 178, 40, 110
    b += _flask(cx, cy, r, th)
    top = cy - r - th + 6
    ytube0 = cy - r + 4
    def ly(l):
        return ytube0 - l * (ytube0 - top - 6)
    b += f'<circle cx="{cx}" cy="{cy}" r="{r - 4}" fill="currentColor" fill-opacity="0.4" stroke="none"/><rect x="{cx - 3.5}" y="{ly(level):.1f}" width="7" height="{ytube0 - ly(level) + 6:.1f}" fill="currentColor" fill-opacity="0.4" stroke="none"/>'
    for i in range(1, 6):
        b += f'<line x1="{cx + 5}" y1="{ly(i / 6):.1f}" x2="{cx + 12}" y2="{ly(i / 6):.1f}" stroke-width="1"/>'
    if start is not None:
        b += f'<line x1="{cx - 22}" y1="{ly(start):.1f}" x2="{cx + 22}" y2="{ly(start):.1f}" stroke-width="1.2" stroke-dasharray="3 3"/>' + txt(cx - 26, ly(start) + 4, "start", 11, anchor="end")
    b += f'<path d="M{cx - 66} {cy - 10} V{cy + 62} H{cx + 66} V{cy - 10}" stroke-width="2"/>' + txt(cx, cy + 82, bath, 12)
    return svg(W, H, b)


def balloon(radius, bath="", caption=None, W=240, H=262):
    """A flask with a balloon stretched over its neck. `radius` is the balloon's radius (small = limp, large = puffed up)."""
    b = (txt(W / 2, 16, caption, 13, bold=True) if caption else "")
    cx, cy, r = 120, 178, 40
    b += f'<path d="M{cx - 8} {cy - r - 28} V{cy - r * 0.9} A{r} {r} 0 1 0 {cx + 8} {cy - r * 0.9} V{cy - r - 28}" stroke-width="2.5"/>'
    by = cy - r - 28
    b += f'<rect x="{cx - 11}" y="{by - 2}" width="22" height="9" fill="currentColor" fill-opacity="0.2"/>'
    b += f'<ellipse cx="{cx}" cy="{by - radius}" rx="{radius}" ry="{radius * 1.1:.1f}" fill="currentColor" fill-opacity="0.2" stroke-width="2"/>'
    if bath:
        b += f'<path d="M{cx - 66} {cy - 14} V{cy + 58} H{cx + 66} V{cy - 14}" stroke-width="2"/>' + txt(cx, cy + 78, bath, 12)
    return svg(W, H, b)


def touching(a, ta, b_, tb, caption=None, W=330, H=130):
    """Two blocks side by side in contact, each labelled with a letter and a temperature."""
    b = (txt(W / 2, 16, caption, 13, bold=True) if caption else "")
    y = 44 if caption else 20
    b += f'<rect x="40" y="{y}" width="120" height="64"/><rect x="160" y="{y}" width="120" height="64"/>'
    b += txt(100, y + 28, a, 16, bold=True) + txt(100, y + 50, ta, 13) + txt(220, y + 28, b_, 16, bold=True) + txt(220, y + 50, tb, 13)
    return svg(W, H, b)


def bath(items, caption=None, W=360, H=190):
    """Beakers in a row, each (label, text lines); used for 'a thermometer in each' set-ups."""
    n = len(items)
    b = (txt(W / 2, 16, caption, 13, bold=True) if caption else "")
    w = (W - 20) / n
    for i, (lab, lines) in enumerate(items):
        x = 10 + i * w + w / 2
        b += f'<path d="M{x - 38} 56 V138 H{x + 38} V56" stroke-width="2.5"/><path d="M{x - 36} 76 H{x + 36}" stroke-width="1" stroke-dasharray="3 3"/>'
        b += txt(x, 160, lab, 16, bold=True)
        for k, l in enumerate(lines):
            b += txt(x, 104 + k * 15, l, 12)
    return svg(W, H, b)


def blocks(items, caption=None, W=None):
    """A row of blocks in contact, each (letter, temperature text)."""
    n = len(items)
    bw = 96
    W = W or n * bw + 60
    b = (txt(W / 2, 16, caption, 13, bold=True) if caption else "")
    y = 44 if caption else 20
    for i, (lab, t) in enumerate(items):
        x = 30 + i * bw
        b += f'<rect x="{x}" y="{y}" width="{bw}" height="64"/>' + txt(x + bw / 2, y + 28, lab, 16, bold=True) + txt(x + bw / 2, y + 50, t, 13)
    return svg(W, y + 84, b)
