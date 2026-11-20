"""Code-drawn evaporation set-ups (black and white): dishes() with sun / fan / lid icons, towels()."""
from fillkit import svg, txt, AH


def _sun(cx, cy, r=9):
    b = f'<circle cx="{cx}" cy="{cy}" r="{r}"/>'
    import math
    for k in range(8):
        a = k * math.pi / 4
        b += f'<line x1="{cx + (r + 3) * math.cos(a):.1f}" y1="{cy + (r + 3) * math.sin(a):.1f}" x2="{cx + (r + 8) * math.cos(a):.1f}" y2="{cy + (r + 8) * math.sin(a):.1f}"/>'
    return b


def _fan(cx, cy, end):
    """A small fan above a dish with three air arrows blowing down toward it."""
    b = f'<circle cx="{cx}" cy="{cy}" r="13" stroke-width="1.6"/><circle cx="{cx}" cy="{cy}" r="2.5" fill="currentColor"/>'
    b += f'<ellipse cx="{cx}" cy="{cy - 7}" rx="3.5" ry="6" fill="currentColor" fill-opacity="0.25" stroke-width="1.2"/>'
    b += f'<ellipse cx="{cx - 6}" cy="{cy + 4}" rx="3.5" ry="6" transform="rotate(60 {cx - 6} {cy + 4})" fill="currentColor" fill-opacity="0.25" stroke-width="1.2"/>'
    b += f'<ellipse cx="{cx + 6}" cy="{cy + 4}" rx="3.5" ry="6" transform="rotate(-60 {cx + 6} {cy + 4})" fill="currentColor" fill-opacity="0.25" stroke-width="1.2"/>'
    for dx in (-12, 0, 12):
        b += f'<path d="M{cx + dx} {cy + 18} q4 5 0 10 t0 10" stroke-width="1.4"/>'
    return b


def dishes(items, caption=None, ch=50, minslot=96):
    """Open containers drawn to scale. Each item: dict(lab, w, h, [ch], [sun], [fan], [lid], [notes]).
    w = container width (px), h = water depth (px); equal volumes need w*h equal."""
    slots = [max(it["w"] + 36, minslot) for it in items]
    W = sum(slots) + 20
    base = 150
    maxch = max(it.get("ch", ch) for it in items)
    base = 80 + maxch
    nn = max(len(it.get("notes", [])) for it in items)
    H = base + 38 + 15 * nn
    b = AH.replace("<defs>", "<defs>", 1) if False else ""
    b += txt(W / 2, 16, caption, 13, bold=True) if caption else ""
    x = 10
    for it, sl in zip(items, slots):
        cx = x + sl / 2
        w, h = it["w"], it["h"]
        c = it.get("ch", ch)
        top = base - c
        x0, x1 = cx - w / 2, cx + w / 2
        b += f'<rect x="{x0 + 1:.1f}" y="{base - h:.1f}" width="{w - 2:.1f}" height="{h:.1f}" fill="currentColor" fill-opacity="0.3" stroke="none"/>'
        b += f'<path d="M{x0:.1f} {top} V{base} H{x1:.1f} V{top}" stroke-width="2.5"/>'
        if it.get("lid"):
            b += f'<line x1="{x0 - 5:.1f}" y1="{top - 2}" x2="{x1 + 5:.1f}" y2="{top - 2}" stroke-width="5"/>'
        if it.get("sun"):
            b += _sun(cx - w / 2 - 6 if w < 70 else cx, 42)
        if it.get("fan"):
            b += _fan(cx, 44, top)
        b += txt(cx, base + 20, it["lab"], 15, bold=True)
        for k, n in enumerate(it.get("notes", [])):
            b += txt(cx, base + 36 + 15 * k, n, 12)
        x += sl
    return svg(W, H, b)


def towels(kinds, caption=None):
    """Wet cloths hung on a line. kinds: list of (label, 'spread' | 'folded')."""
    n = len(kinds)
    W = 20 + n * 150
    b = txt(W / 2, 16, caption, 13, bold=True) if caption else ""
    b += f'<line x1="10" y1="40" x2="{W - 10}" y2="40" stroke-width="3"/>'
    for i, (lab, kind) in enumerate(kinds):
        cx = 10 + i * 150 + 75
        if kind == "spread":
            b += f'<rect x="{cx - 50}" y="42" width="100" height="74" fill="currentColor" fill-opacity="0.18"/>'
        else:
            b += f'<rect x="{cx - 25}" y="42" width="50" height="38" fill="currentColor" fill-opacity="0.3" stroke-width="3"/>'
        b += f'<line x1="{cx}" y1="34" x2="{cx}" y2="46" stroke-width="3"/>'
        b += txt(cx, 140, lab, 15, bold=True)
    return svg(W, 152, b)
