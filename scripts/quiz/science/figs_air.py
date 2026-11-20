"""Code-drawn figures for the gases-in-air items (fill_air.py): pie chart, jar over a burning candle, bell jars, limewater tubes.
Black and white (currentColor / #fff), viewBox, no scripts or external references."""
import math
from fillkit import svg, txt


def pie(parts, caption, r=72):
    """parts = [(fraction of 100, 'P 78%'), ...] drawn clockwise from the top."""
    cx, cy = 150, 138
    b = txt(150, 20, caption, 13, bold=True)
    ops = [0.12, 0.42, 0.7, 0.92]
    a0 = 0.0
    for i, (v, lab) in enumerate(parts):
        a1 = a0 + v / 100 * 2 * math.pi
        x0, y0 = cx + r * math.sin(a0), cy - r * math.cos(a0)
        x1, y1 = cx + r * math.sin(a1), cy - r * math.cos(a1)
        big = 1 if a1 - a0 > math.pi else 0
        b += f'<path d="M{cx} {cy} L{x0:.1f} {y0:.1f} A{r} {r} 0 {big} 1 {x1:.1f} {y1:.1f} Z" fill="currentColor" fill-opacity="{ops[i % 4]}"/>'
        am = (a0 + a1) / 2
        lx, ly = cx + (r + 18) * math.sin(am), cy - (r + 18) * math.cos(am)
        anchor = "start" if math.sin(am) > 0.25 else ("end" if math.sin(am) < -0.25 else "middle")
        b += txt(f"{lx:.1f}", f"{ly + 4:.1f}", lab, 13, anchor=anchor, bold=True)
        a0 = a1
    return svg(300, 240, b)


def _candle(x, ytop, ybase, flame):
    b = f'<rect x="{x - 7}" y="{ytop}" width="14" height="{ybase - ytop}" fill="#fff"/>'
    if flame:
        b += f'<path d="M{x} {ytop - 16} Q{x + 6} {ytop - 6} {x} {ytop - 2} Q{x - 6} {ytop - 6} {x} {ytop - 16} Z" fill="currentColor"/>'
    return b


def trough(rise=0.0, flame=True, marks=False, caption="Jar over a burning candle", liquid="water"):
    """Inverted jar standing in a trough of water over a burning candle. rise = fraction of the jar's air space the water has climbed."""
    b = txt(150, 20, caption, 13, bold=True)
    b += '<rect x="31" y="170" width="238" height="60" fill="currentColor" fill-opacity="0.15" stroke="none"/>'
    b += '<path d="M30 150 V230 H270 V150"/>'
    if rise:
        h = 120 * rise
        b += f'<rect x="101" y="{170 - h:.1f}" width="98" height="{h:.1f}" fill="currentColor" fill-opacity="0.15" stroke="none"/>'
        b += f'<line x1="101" y1="{170 - h:.1f}" x2="199" y2="{170 - h:.1f}" stroke-width="1.5"/>'
    b += '<path d="M100 200 V50 H200 V200"/>'
    if marks:
        for k in range(1, 5):
            b += f'<line x1="100" y1="{170 - 24 * k}" x2="118" y2="{170 - 24 * k}" stroke-width="1.5"/>'
    b += '<line x1="150" y1="176" x2="150" y2="228"/><line x1="128" y1="176" x2="172" y2="176"/>'
    b += _candle(150, 142, 176, flame)
    b += txt(62, 94, "jar", 13) + '<line x1="78" y1="90" x2="98" y2="90" stroke-width="1.5"/>'
    b += txt(240, 120, "candle", 13) + '<line x1="214" y1="116" x2="160" y2="150" stroke-width="1.5"/>'
    b += txt(238, 208, liquid, 13)
    return svg(300, 245, b)


def bells(specs, caption):
    """Bell jars standing over burning candles. specs = [(cx, width, height, label)]."""
    b = txt(150, 20, caption, 13, bold=True) + '<line x1="10" y1="200" x2="290" y2="200" stroke-width="3"/>'
    for cx, w, h, lab in specs:
        b += f'<path d="M{cx - w / 2} 200 V{200 - h} H{cx + w / 2} V200"/>'
        b += _candle(cx, 164, 200, True)
        b += txt(cx, 224, lab, 14, bold=True)
    return svg(300, 235, b)


def tubes(specs, caption, note=None):
    """Test tubes of limewater with a delivery tube. specs = [(x, label, spacing or None, under-text)]; spacing = hatch gap of the milky look."""
    b = txt(150 if len(specs) > 1 else 110, 20, caption, 13, bold=True)
    for x, lab, sp, under in specs:
        b += '<path d="M%d 60 V150 a20 20 0 0 0 40 0 V60"/>' % (x - 20)
        b += f'<rect x="{x - 19}" y="108" width="38" height="42" fill="currentColor" fill-opacity="0.12" stroke="none"/>'
        b += f'<path d="M{x - 19} 150 a19 19 0 0 0 38 0 Z" fill="currentColor" fill-opacity="0.12" stroke="none"/>'
        if sp:
            y = 114
            while y <= 150:
                b += f'<line x1="{x - 15}" y1="{y}" x2="{x + 15}" y2="{y}" stroke-width="1.5" stroke-dasharray="5 3"/>'
                y += sp
        b += f'<line x1="{x + 8}" y1="28" x2="{x + 8}" y2="140" stroke-width="3"/>'
        b += f'<circle cx="{x + 3}" cy="128" r="2.5"/><circle cx="{x + 12}" cy="119" r="2.5"/>'
        b += txt(x, 196, lab, 14, bold=True)
        if under:
            b += txt(x, 214, under, 12)
    if note:
        b += txt(215, 150, note, 12, anchor="start")
    return svg(300 if len(specs) > 1 else 240, 225, b)
