"""Code-drawn figures for sci-cycles-water-states: states(), curve(), glass(), kettle(), pot_lid(). Black and white (currentColor)."""
from fillkit import svg, txt, box, AH, arrow

MAPS = {
    "A": dict(melt="P", freeze="Q", boil="R", cond="S"),
    "B": dict(melt="R", freeze="S", boil="P", cond="Q"),
    "C": dict(melt="S", freeze="R", boil="Q", cond="P"),
}


def states(m="A", caption="Three states of water", W=440, H=210):
    """Ice, water and water vapour in a row; four lettered arrows (melting, freezing, boiling or evaporation, condensation)."""
    L = MAPS[m]
    b = AH + txt(W / 2, 18, caption, 13, bold=True)
    y = 78
    b += box(10, y, 90, 56, "Ice", bold=True) + box(175, y, 90, 56, "Water", bold=True) + box(340, y, 90, 56, "Water|vapour", bold=True)
    for x0 in (100, 265):
        b += arrow(x0 + 4, y + 16, x0 + 71, y + 16) + arrow(x0 + 71, y + 40, x0 + 4, y + 40)
    mid = {0: 137, 1: 302}
    b += txt(mid[0], y + 6, L["melt"], 16, bold=True) + txt(mid[0], y + 62, L["freeze"], 16, bold=True)
    b += txt(mid[1], y + 6, L["boil"], 16, bold=True) + txt(mid[1], y + 62, L["cond"], 16, bold=True)
    return svg(W, H, b)


def curve(pts, labels, caption="Temperature of a substance", ymin=-20, ymax=120, ystep=20, xmax=24, xstep=4, W=400, H=270):
    """Temperature-time line graph from (t, T) points, with letters placed at (letter, t, T, dx, dy)."""
    L, R, T, B = 56, 16, 34, 48
    pw, ph = W - L - R, H - T - B
    X = lambda t: L + t / xmax * pw
    Y = lambda v: T + ph - (v - ymin) / (ymax - ymin) * ph
    b = txt(W / 2, 18, caption, 13, bold=True) + f'<path d="M{L} {T} V{T + ph} H{L + pw}"/>'
    v = ymin
    while v <= ymax + 1e-9:
        b += f'<line x1="{L - 4}" y1="{Y(v):.1f}" x2="{L}" y2="{Y(v):.1f}"/>' + txt(L - 8, Y(v) + 4, f"{v:g}", 11, anchor="end")
        v += ystep
    if ymin < 0:
        b += f'<line x1="{L}" y1="{Y(0):.1f}" x2="{L + pw}" y2="{Y(0):.1f}" stroke-width="0.8" stroke-dasharray="3 4" stroke-opacity="0.5"/>'
    t = 0
    while t <= xmax:
        b += f'<line x1="{X(t):.1f}" y1="{T + ph}" x2="{X(t):.1f}" y2="{T + ph + 4}"/>' + txt(X(t), T + ph + 17, f"{t:g}", 11)
        t += xstep
    b += txt(L + pw / 2, H - 8, "Time (min)", 12)
    b += f'<text transform="translate(14 {T + ph / 2}) rotate(-90)" text-anchor="middle" font-size="12" fill="currentColor" stroke="none">Temperature (°C)</text>'
    b += '<polyline points="' + " ".join(f"{X(a):.1f},{Y(c):.1f}" for a, c in pts) + '"/>'
    for lab, a, c, dx, dy in labels:
        b += txt(X(a) + dx, Y(c) + dy, lab, 15, bold=True)
    return svg(W, H, b)


def glass(caption="A glass of iced water", W=260, H=240, ice=True, drops=True):
    """A glass of water with ice cubes; small droplets on the outside wall."""
    b = txt(W / 2, 18, caption, 13, bold=True)
    x1, x2, top, bot = 80, 180, 48, 200
    b += f'<path d="M{x1} {top} L{x1 + 8} {bot} H{x2 - 8} L{x2} {top}" stroke-width="2.5"/>'
    b += f'<path d="M{x1 + 2} {top + 30} H{x2 - 2}" stroke-width="1.2" stroke-dasharray="3 3"/>'
    if ice:
        for cx, cy in ((106, top + 40), (140, top + 48), (122, top + 72)):
            b += f'<rect x="{cx - 12}" y="{cy - 12}" width="24" height="24" rx="3" fill="#fff" stroke-width="1.8"/>'
    if drops:
        for cx, cy in ((x1 - 7, 86), (x1 - 4, 124), (x1 + 0, 160), (x2 + 8, 80), (x2 + 5, 118), (x2 + 2, 156), (x2 - 6, 186)):
            b += f'<path d="M{cx} {cy - 7} Q{cx + 5} {cy + 1} {cx} {cy + 5} Q{cx - 5} {cy + 1} {cx} {cy - 7} Z" fill="currentColor" fill-opacity="0.35" stroke-width="1.2"/>'
    return svg(W, H, b)


def kettle(caption="A kettle of boiling water", W=380, H=250):
    """A kettle on a heater; a clear gap X just above the spout and white mist (dots) further up at Y."""
    b = txt(W / 2, 18, caption, 13, bold=True)
    b += '<path d="M70 190 L82 120 H190 L202 190 Z" stroke-width="2.5"/><path d="M82 120 L96 104 H176 L190 120" stroke-width="2"/>'
    b += '<path d="M202 150 L262 112 L270 122 L206 170" stroke-width="2.5"/>'
    b += '<path d="M82 128 Q40 130 50 170 Q56 188 74 182" stroke-width="3"/>'
    b += '<line x1="56" y1="208" x2="224" y2="208" stroke-width="3"/>'
    b += txt(280, 100, "X", 16, bold=True)
    import random
    rnd = random.Random(5)
    for _ in range(26):
        x, y = rnd.uniform(268, 345), rnd.uniform(32, 76)
        b += f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{rnd.uniform(3, 5):.1f}" fill="currentColor" fill-opacity="0.25" stroke-width="1"/>'
    b += txt(360, 58, "Y", 16, bold=True)
    return svg(W, H, b)


def pot_lid(caption="A pot of boiling water", W=300, H=250):
    """A pot of bubbling water with a lid held above it; droplets hang under the lid."""
    b = txt(W / 2, 18, caption, 13, bold=True)
    b += '<path d="M60 130 V210 H240 V130" stroke-width="2.5"/><path d="M62 150 H238" stroke-width="1.2" stroke-dasharray="3 3"/>'
    for cx, cy in ((100, 170), (130, 184), (160, 166), (190, 180), (215, 168), (145, 196)):
        b += f'<circle cx="{cx}" cy="{cy}" r="5"/>'
    b += '<path d="M48 70 Q150 38 252 70 Z" fill="#fff" stroke-width="2.5"/><line x1="150" y1="44" x2="150" y2="34" stroke-width="3"/>'
    for cx in (96, 126, 160, 194, 222):
        b += f'<path d="M{cx} 74 Q{cx + 4} 82 {cx} 86 Q{cx - 4} 82 {cx} 74 Z" fill="currentColor" fill-opacity="0.35" stroke-width="1.2"/>'
    b += txt(150, 236, "Lid", 13) if False else ""
    return svg(W, H, b)
