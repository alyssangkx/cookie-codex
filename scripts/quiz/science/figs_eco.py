"""Code-drawn food webs (black and white): web(). Arrows point from the food to the organism that eats it."""
from fillkit import svg, txt, AH


def _clip(c, d, hw, hh, pad=0):
    dx, dy = d[0] - c[0], d[1] - c[1]
    t = min((hw + pad) / abs(dx) if dx else 1e9, (hh + pad) / abs(dy) if dy else 1e9)
    return c[0] + dx * t, c[1] + dy * t


def web(nodes, edges, W=380, H=230, caption=None, fs=12):
    """nodes = {label: (x, y)}; edges = [(food, eater)]; boxes sized from the label."""
    half = {k: (len(k) * fs * 0.3 + 9, 12) for k in nodes}
    b = AH + (txt(W / 2, 14, caption, 13, bold=True) if caption else "")
    for a, e in edges:
        ca, ce = nodes[a], nodes[e]
        x1, y1 = _clip(ca, ce, *half[a], pad=2)
        x2, y2 = _clip(ce, ca, *half[e], pad=4)
        b += f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke-width="1.8" marker-end="url(#ah)"/>'
    for k, (x, y) in nodes.items():
        hw, hh = half[k]
        b += f'<rect x="{x - hw:.1f}" y="{y - hh}" width="{2 * hw:.1f}" height="{2 * hh}" rx="4" fill="#fff"/>' + txt(x, y + 4, k, fs)
    return svg(W, H, b)


MEADOW = ({"grass": (190, 204), "grasshopper": (85, 152), "rabbit": (295, 152), "frog": (85, 98), "snake": (190, 98), "hawk": (250, 42)},
          [("grass", "grasshopper"), ("grass", "rabbit"), ("grasshopper", "frog"), ("frog", "snake"), ("rabbit", "snake"), ("snake", "hawk"), ("rabbit", "hawk")])
POND = ({"P": (190, 200), "Q": (100, 140), "R": (280, 140), "S": (190, 90), "T": (190, 44)},
        [("P", "Q"), ("P", "R"), ("Q", "S"), ("R", "S"), ("S", "T")])
FOREST = ({"grass": (120, 206), "shrub": (285, 206), "grasshopper": (55, 148), "mouse": (190, 148), "rabbit": (335, 148),
           "frog": (55, 92), "snake": (150, 92), "fox": (345, 92), "owl": (250, 34)},
          [("grass", "grasshopper"), ("grass", "mouse"), ("shrub", "mouse"), ("shrub", "rabbit"), ("grass", "rabbit"), ("grasshopper", "frog"),
           ("frog", "snake"), ("mouse", "snake"), ("mouse", "owl"), ("snake", "owl"), ("rabbit", "fox")])


def meadow(caption="A food web in a meadow"):
    return web(*MEADOW, W=380, H=230, caption=caption)


def pond(caption="A food web in a pond"):
    return web(*POND, W=380, H=224, caption=caption)


def forest(caption="A food web in a forest"):
    return web(*FOREST, W=400, H=232, caption=caption)
