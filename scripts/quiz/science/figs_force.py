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


def ramp(h, surface, label="ramp", W=360, H=170, block=True):
    """A ramp with a toy car at the top and a floor covered with a surface name; h is the ramp height in cm label."""
    top = 140 - h * 1.1
    b = f'<path d="M20 140 L20 {top} L170 140 Z"/><line x1="20" y1="140" x2="{W - 14}" y2="140"/>'
    b += f'<rect x="{W - 120}" y="{143}" width="104" height="10"/>' + txt(W - 68, 166, surface, 12)
    b += f'<rect x="38" y="{top + 8}" width="30" height="16" rx="3" transform="rotate(26 53 {top + 16})"/>'
    b += txt(20 - 0, top - 6, f"{h} cm", 12, anchor="start")
    return svg(W, H, b)


def spring(load_g, length_label="", W=150, H=230, ruler=True):
    """A spring hanging from a stand with a mass hanging at the bottom; load_g is the mass label."""
    b = '<line x1="30" y1="14" x2="110" y2="14" stroke-width="4"/>'
    n, y = 9, 14
    pts = "M70 14 V24 "
    for i in range(n):
        pts += f"L{58 if i % 2 == 0 else 82} {24 + i * 9 + 4} "
    pts += "L70 112 V120"
    b += f'<path d="{pts}"/><rect x="50" y="120" width="40" height="34" rx="4"/>' + txt(70, 142, load_g, 13)
    return svg(W, H - 40, b)
