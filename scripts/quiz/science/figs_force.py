"""Code-drawn force diagrams (black and white): arrows(), ramp(), spring()."""
from fillkit import svg, txt, AH, arrow


def arrows(obj, specs, ground=True, W=300, H=190, caption=None, on_ramp=False):
    """An object (rounded box with a label) with force arrows. specs = [(dir 'L'|'R'|'U'|'D', letter-or-label, length)]."""
    cx, cy, bw, bh = W / 2, 92, 104, 44
    b = AH
    if caption:
        b += txt(W / 2, 16, caption, 13, bold=True)
    if ground:
        b += f'<line x1="14" y1="{cy + bh / 2}" x2="{W - 14}" y2="{cy + bh / 2}" stroke-width="2"/>'
    b += f'<rect x="{cx - bw / 2}" y="{cy - bh / 2}" width="{bw}" height="{bh}" rx="5"/>' + txt(cx, cy + 5, obj, 13)
    for d, lab, ln in specs:
        if d == "R":
            x1, y1, x2, y2, tx, ty = cx + bw / 2, cy, cx + bw / 2 + ln, cy, cx + bw / 2 + ln + 14, cy + 5
        elif d == "L":
            x1, y1, x2, y2, tx, ty = cx - bw / 2, cy, cx - bw / 2 - ln, cy, cx - bw / 2 - ln - 14, cy + 5
        elif d == "U":
            x1, y1, x2, y2, tx, ty = cx, cy - bh / 2, cx, cy - bh / 2 - ln, cx + 14, cy - bh / 2 - ln + 4
        else:
            x1, y1, x2, y2, tx, ty = cx, cy + bh / 2, cx, cy + bh / 2 + ln, cx + 14, cy + bh / 2 + ln
        b += arrow(x1, y1, x2, y2, 3) + txt(tx, ty, lab, 15, bold=True)
    return svg(W, H, b)


def ramp(h, surface, W=380, H=150, stop=None):
    """Ramp h cm high with a toy car at the top, a floor patch of the named surface and a ruler on the floor.
    stop = distance in cm travelled (drawn as a car and a dashed mark) or None."""
    top = 112 - h * 1.1
    b = f'<path d="M20 120 L20 {top:.0f} L150 120 Z"/><line x1="14" y1="120" x2="{W - 10}" y2="120"/>'
    b += f'<rect x="150" y="120" width="{W - 160}" height="9" fill="none"/>' + txt((150 + W - 10) / 2, 144, surface, 12)
    ang = 3.14159 / 180 * 0
    import math
    a = math.degrees(math.atan2(120 - top, 130))
    b += f'<rect x="36" y="{top + 5:.0f}" width="28" height="14" rx="3" transform="rotate({a:.0f} 50 {top + 12:.0f})"/>'
    b += f'<circle cx="42" cy="{top + 22:.0f}" r="3"/><circle cx="60" cy="{top + 28:.0f}" r="3"/>'
    b += txt(10, top - 6, f"{h} cm", 12, anchor="start")
    if stop:
        x = 150 + stop * 1.6
        b += f'<rect x="{x - 14:.0f}" y="104" width="28" height="14" rx="3"/><line x1="150" y1="98" x2="{x:.0f}" y2="98" stroke-dasharray="4 3"/>' + txt((150 + x) / 2, 92, f"{stop} cm", 12)
    return svg(W, H, b)


def spring(load, ext=None, W=190, H=210, scale=True):
    """A spring hanging from a stand, mass box labelled load, with a ruler (cm) beside it. ext = extension in cm drawn
    as spring length 5 + ext (cm) with 8 px per cm; the ruler shows 0-14 cm from the top of the spring."""
    n = 8
    L = 5 + (ext or 0)
    px = 8
    ytop = 24
    ybot = ytop + L * px
    b = '<line x1="20" y1="14" x2="110" y2="14" stroke-width="4"/>'
    pts = f"M65 14 V{ytop} "
    for i in range(n):
        y = ytop + (i + 0.5) * (ybot - ytop) / n
        pts += f"L{50 if i % 2 == 0 else 80} {y:.1f} "
    pts += f"L65 {ybot} V{ybot + 8}"
    b += f'<path d="{pts}"/><rect x="45" y="{ybot + 8}" width="40" height="30" rx="4"/>' + txt(65, ybot + 28, load, 13)
    if scale:
        for c in range(0, 15):
            y = ytop + c * px
            ln = 12 if c % 5 == 0 else 7
            b += f'<line x1="130" y1="{y}" x2="{130 + ln}" y2="{y}" stroke-width="1.2"/>'
            if c % 5 == 0:
                b += txt(160, y + 4, str(c), 10, anchor="start")
        b += f'<line x1="130" y1="{ytop}" x2="130" y2="{ytop + 14 * px}" stroke-width="1.2"/>'
        b += f'<line x1="90" y1="{ybot}" x2="128" y2="{ybot}" stroke-dasharray="3 3" stroke-width="1.2"/>'
    return svg(W, H, b)


def _zig(x1, x2, y, n=7, amp=7):
    d = f"M{x1} {y} "
    step = (x2 - x1) / (n * 2)
    for i in range(n * 2):
        d += f"L{x1 + (i + 0.5) * step:.1f} {y + (amp if i % 2 == 0 else -amp)} "
    return d + f"L{x2} {y}"


def _spec_arrows(cx, cy, bw, bh, specs, yoff=0):
    """Force arrows drawn from the edges of a box centred at (cx, cy). Horizontal arrows sit yoff px above the middle."""
    b = ""
    for d, lab, ln in specs:
        if d == "R":
            b += arrow(cx + bw / 2, cy + yoff, cx + bw / 2 + ln, cy + yoff, 3) + txt(cx + bw / 2 + ln + 12, cy + yoff + 5, lab, 15, bold=True)
        elif d == "L":
            b += arrow(cx - bw / 2, cy + yoff, cx - bw / 2 - ln, cy + yoff, 3) + txt(cx - bw / 2 - ln - 12, cy + yoff + 5, lab, 15, bold=True)
        elif d == "U":
            b += arrow(cx, cy - bh / 2, cx, cy - bh / 2 - ln, 3) + txt(cx + 14, cy - bh / 2 - ln + 4, lab, 15, bold=True)
        else:
            b += arrow(cx, cy + bh / 2, cx, cy + bh / 2 + ln, 3) + txt(cx + 14, cy + bh / 2 + ln, lab, 15, bold=True)
    return b


def pulled_block(obj, specs, caption=None, W=330, H=190):
    """A block on a table with a stretched spring joined to its right side and a hand holding the far end."""
    cx, cy, bw, bh = 130, 92, 96, 44
    b = AH + (txt(W / 2, 16, caption, 13, bold=True) if caption else "")
    b += f'<line x1="10" y1="{cy + bh / 2}" x2="{W - 10}" y2="{cy + bh / 2}" stroke-width="2"/>'
    b += f'<rect x="{cx - bw / 2}" y="{cy - bh / 2}" width="{bw}" height="{bh}" rx="5"/>' + txt(cx, cy + 5, obj, 12)
    b += f'<path d="{_zig(cx + bw / 2, 286, cy + 12)}"/><circle cx="296" cy="{cy + 12}" r="10"/>' + txt(296, cy + 41, "hand", 11)
    b += _spec_arrows(cx, cy, bw, bh, specs, yoff=-12)
    return svg(W, H, b)


def wall_spring(specs, caption=None, W=330, H=190):
    """A spring fixed to a wall at the left, its free end held by a hand (a box) at the right."""
    cx, cy, bw, bh = 220, 92, 74, 44
    b = AH + (txt(W / 2, 16, caption, 13, bold=True) if caption else "")
    b += f'<line x1="26" y1="40" x2="26" y2="150" stroke-width="5"/>' + "".join(f'<line x1="26" y1="{y}" x2="14" y2="{y + 10}" stroke-width="1.5"/>' for y in range(44, 146, 14))
    b += f'<path d="{_zig(26, cx - bw / 2, cy + 12, 9)}"/>'
    b += f'<rect x="{cx - bw / 2}" y="{cy - bh / 2}" width="{bw}" height="{bh}" rx="5"/>' + txt(cx, cy + 5, "hand", 13)
    b += _spec_arrows(cx, cy, bw, bh, specs, yoff=-12)
    return svg(W, H, b)


def magnet_ball(specs, caption=None, W=300, H=200):
    """A magnet fixed above an iron ball with a gap between them (nothing touches)."""
    cx, cy = W / 2, 112
    b = AH + (txt(W / 2, 16, caption, 13, bold=True) if caption else "")
    b += f'<rect x="{cx - 40}" y="26" width="80" height="26" rx="3"/>' + txt(cx, 44, "magnet", 13)
    b += f'<circle cx="{cx}" cy="{cy}" r="18"/>' + txt(cx, cy + 5, "iron", 11)
    for d, lab, ln in specs:
        if d == "U":
            b += arrow(cx - 8, cy - 18, cx - 8, cy - 18 - ln, 3) + txt(cx - 22, cy - 18 - ln / 2 + 5, lab, 15, bold=True)
        else:
            b += arrow(cx - 8, cy + 18, cx - 8, cy + 18 + ln, 3) + txt(cx - 22, cy + 18 + ln / 2 + 5, lab, 15, bold=True)
    return svg(W, H, b)


def pusher(specs, caption=None, W=360, H=190):
    """A boy (stick figure) on the left with his hands on a box, pushing it along the floor to the right."""
    cx, cy, bw, bh = 215, 92, 90, 44
    b = AH + (txt(W / 2, 16, caption, 13, bold=True) if caption else "")
    b += f'<line x1="10" y1="{cy + bh / 2}" x2="{W - 10}" y2="{cy + bh / 2}" stroke-width="2"/>'
    b += f'<rect x="{cx - bw / 2}" y="{cy - bh / 2}" width="{bw}" height="{bh}" rx="5"/>' + txt(cx, cy + 5, "box", 13)
    hx = cx - bw / 2
    fx = hx - 90
    b += f'<circle cx="{fx - 6}" cy="{cy - 30}" r="9"/><line x1="{fx - 4}" y1="{cy - 21}" x2="{fx + 10}" y2="{cy + 6}"/>'
    b += f'<line x1="{fx}" y1="{cy - 14}" x2="{hx}" y2="{cy - 6}"/><line x1="{fx + 10}" y1="{cy + 6}" x2="{fx - 6}" y2="{cy + 22}"/><line x1="{fx + 10}" y1="{cy + 6}" x2="{fx + 22}" y2="{cy + 22}"/>'
    b += _spec_arrows(cx, cy, bw, bh, specs, yoff=14)
    return svg(W, H, b)
