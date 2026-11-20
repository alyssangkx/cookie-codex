"""Code-drawn figures for the water-cycle items: cycle(), bowl(), pair(), can(). Black and white (currentColor / #fff)."""
from fillkit import svg, txt, AH


def _tag(x, y, s):
    return f'<circle cx="{x}" cy="{y}" r="11" fill="#fff"/>' + txt(x, y + 5, s, 14, bold=True)


def _cloud(cx, cy, k=1.0):
    return (f'<path d="M{cx - 50 * k} {cy + 18 * k} Q{cx - 66 * k} {cy + 18 * k} {cx - 62 * k} {cy + 2 * k} Q{cx - 58 * k} {cy - 12 * k} {cx - 40 * k} {cy - 8 * k} '
            f'Q{cx - 36 * k} {cy - 34 * k} {cx - 8 * k} {cy - 28 * k} Q{cx + 12 * k} {cy - 42 * k} {cx + 30 * k} {cy - 20 * k} Q{cx + 60 * k} {cy - 22 * k} {cx + 58 * k} {cy + 2 * k} '
            f'Q{cx + 68 * k} {cy + 18 * k} {cx + 48 * k} {cy + 18 * k} Z" fill="#fff"/>')


def cycle(L=None, caption="The water cycle"):
    """Sea, Sun, cloud, mountain and river. L maps a stage to its letter: ev (sea to air), co (in the cloud),
    pr (cloud to mountain), ru (river back to sea). A stage not in L has an arrow but no letter."""
    L = L or {"ev": "P", "co": "Q", "pr": "R", "ru": "S"}
    W, H = 420, 270
    b = AH + txt(W / 2, 16, caption, 13, bold=True)
    # Sun
    b += '<circle cx="48" cy="58" r="14"/>' + "".join(
        f'<line x1="{48 + 20 * c:.1f}" y1="{58 + 20 * s:.1f}" x2="{48 + 28 * c:.1f}" y2="{58 + 28 * s:.1f}"/>'
        for c, s in ((1, 0), (.707, .707), (0, 1), (-.707, .707), (-1, 0), (-.707, -.707), (0, -1), (.707, -.707))) + txt(48, 100, "Sun", 12)
    # sea and mountain
    b += '<path d="M10 205 H222 V252 H10 Z" fill-opacity="0"/>'
    for y in (220, 236):
        b += f'<path d="M16 {y} q10 -8 20 0 t20 0 t20 0 t20 0 t20 0 t20 0 t20 0 t20 0 t20 0"/>'
    b += txt(70, 200, "sea", 12)
    b += '<path d="M222 252 L330 112 L410 252 Z"/><path d="M308 140 l12 8 l10 -10 l12 10"/>'
    b += txt(330, 100, "mountain", 12)
    # cloud
    b += _cloud(190, 62)
    # arrows
    b += f'<line x1="112" y1="190" x2="130" y2="108" stroke-width="2" marker-end="url(#ah)"/>'
    b += '<line x1="238" y1="96" x2="272" y2="158" stroke-width="2" stroke-dasharray="6 4" marker-end="url(#ah)"/>'
    b += '<path d="M300 172 Q290 200 262 214 Q240 226 226 232" stroke-width="2" marker-end="url(#ah)"/>'
    pos = {"ev": (96, 150), "co": (190, 66), "pr": (232, 130), "ru": (292, 212)}
    for k, (x, y) in pos.items():
        if k in L:
            b += _tag(x, y, L[k])
    return svg(W, H, b)


def _bowl_body(ox, ice=True, drops=True, label=True, tag=None):
    b = f'<g transform="translate({ox} 0)">'
    b += '<path d="M30 80 V110 Q30 170 100 170 Q170 170 170 110 V80"/>'                      # bowl
    b += '<path d="M40 128 Q100 138 160 128" stroke-dasharray="3 3"/>'                # water level
    for x in (70, 100, 130):                                                          # vapour
        b += f'<path d="M{x} 126 q-6 -6 0 -12 t0 -12" stroke-dasharray="2 4"/>'
    b += '<path d="M24 78 Q100 98 176 78" stroke-width="3"/>'                         # sheet
    if ice:
        for x in (68, 91, 114):
            b += f'<rect x="{x}" y="68" width="18" height="16" rx="2" fill="#fff"/>'
    if drops:
        for x, y in ((62, 94), (88, 100), (112, 100), (138, 94)):
            b += f'<path d="M{x} {y} q-3 5 0 7 q3 -2 0 -7 z"/>'
    if label:
        b += txt(100, 190, "hot water", 12)
    if tag:
        b += txt(100, 210, tag, 14, bold=True)
    return b + "</g>"


def bowl(caption="A model of the water cycle", ice=True, drops=True):
    """A bowl of hot water covered with a plastic sheet; ice cubes on the sheet; drops under the sheet."""
    b = txt(100, 16, caption, 13, bold=True) + _bowl_body(0, ice, drops)
    b += txt(100, 52, "plastic sheet" if not ice else "ice cubes on plastic sheet", 12)
    return svg(200, 200, b)


def pair(caption="Two set-ups with hot water"):
    """Set-ups A and B: the same bowl of hot water and plastic sheet; ice on the sheet of A only."""
    b = txt(210, 16, caption, 13, bold=True)
    b += _bowl_body(0, True, False, True, "Set-up A") + _bowl_body(220, False, False, True, "Set-up B")
    b += txt(100, 52, "ice on sheet", 12) + txt(320, 52, "no ice on sheet", 12)
    return svg(430, 224, b)


def can(caption="A cold can in a warm room"):
    """A can with droplets on its outside surface."""
    b = txt(110, 16, caption, 13, bold=True)
    b += '<path d="M70 50 V170 Q110 182 150 170 V50"/><ellipse cx="110" cy="50" rx="40" ry="8"/>'
    b += txt(110, 120, "ice-cold", 12) + txt(110, 136, "drink", 12)
    for x, y in ((62, 80), (60, 120), (64, 156), (158, 90), (160, 130), (156, 160), (176, 105)):
        b += f'<path d="M{x} {y} q-4 7 0 9 q4 -2 0 -9 z"/>'
    b += txt(110, 204, "air in the room is warm", 12)
    return svg(220, 216, b)
