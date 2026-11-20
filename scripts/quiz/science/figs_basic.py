"""Add figures to the shipped basic Science items that had none, and re-file mis-filed plant-parts items.

    python3 scripts/quiz/science/figs_basic.py           # set "figure" on the listed items (idempotent)

(The one-off re-filing of adaptation / reproduction items out of plant-parts is done and its code removed.)

Figures are inline SVG made here (black and white, currentColor, viewBox, no scripts or external refs) or an existing
line-art image under site/public/science/ with no labels. A figure shows the scene of the stem; it never shows the
answer (no label that names the answer, no ordered sequence for an ordering question). Original drawings only.
"""
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
ITEMS = HERE / "items"
H = 'font-family="Arial, Helvetica, sans-serif" font-size="14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"'


def svg(w, h, body):
    return f'<svg viewBox="0 0 {w} {h}" {H}>{body}</svg>'


def txt(x, y, s, size=12, anchor="middle", bold=False):
    b = ' font-weight="bold"' if bold else ""
    return f'<text x="{x}" y="{y}" text-anchor="{anchor}" font-size="{size}"{b} fill="currentColor" stroke="none">{s}</text>'


def leaf(cx, cy, rot, rx=34, ry=13):
    return f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" transform="rotate({rot} {cx} {cy})"/>'


def plant(ground=True):
    """A plain plant above and below the soil; no letters or names."""
    b = '<line x1="20" y1="200" x2="280" y2="200"/>' + txt(272, 218, "soil", anchor="end") + txt(272, 40, "air", anchor="end")
    b += '<line x1="150" y1="200" x2="150" y2="62" stroke-width="4"/>'
    for q in ("120 227 90 255", "135 235 120 270", "150 237 150 275", "165 235 180 270", "180 227 210 255"):
        b += f'<path d="M150 200 Q {q}"/>'
    b += leaf(205, 95, -25, 38, 14) + '<line x1="170" y1="108" x2="238" y2="82"/>'
    b += leaf(95, 120, 25, 38, 14) + '<line x1="130" y1="132" x2="62" y2="108"/>'
    for cx, cy, r in ((166, 48, 0), (154.9, 63.2, 72), (137.1, 57.4, 144), (137.1, 38.6, 216), (154.9, 32.8, 288)):
        b += f'<ellipse cx="{cx}" cy="{cy}" rx="9" ry="6" transform="rotate({r} {cx} {cy})"/>'
    b += '<circle cx="150" cy="48" r="6"/>'
    return svg(300, 290, b)


def tree(fruit=False):
    b = '<line x1="10" y1="250" x2="290" y2="250"/>'
    b += '<path d="M138 250 L142 150 M162 250 L158 150"/><path d="M138 250 Q120 262 100 266 M162 250 Q180 262 200 266"/>'
    b += '<path d="M142 150 Q70 150 70 100 Q60 50 110 45 Q150 15 190 45 Q240 50 230 100 Q230 150 158 150 Z"/>'
    if fruit:
        for cx, cy in ((105, 90), (150, 70), (195, 100), (125, 125), (180, 135)):
            b += f'<circle cx="{cx}" cy="{cy}" r="9"/>'
    return svg(300, 280, b)


def tree_ringed():
    """A stem with a ring of bark removed; shows the cut only."""
    b = '<line x1="20" y1="220" x2="280" y2="220"/>' + txt(272, 238, "soil", anchor="end")
    b += '<path d="M136 220 L136 150 M164 220 L164 150"/>'                    # lower stem
    b += '<path d="M136 150 L142 150 M164 150 L158 150"/>'
    b += '<path d="M142 150 L142 118 M158 150 L158 118" stroke-dasharray="3 3"/>'  # bared band, thin stem
    b += '<path d="M136 118 L142 118 M164 118 L158 118"/><path d="M136 118 L136 70 M164 118 L164 70"/>'
    b += '<line x1="136" y1="70" x2="164" y2="70"/>'
    b += leaf(100, 78, 20, 36, 14) + leaf(200, 78, -20, 36, 14) + leaf(150, 48, 0, 14, 28)
    for q in ("120 245 95 268", "150 250 150 275", "180 245 205 268"):
        b += f'<path d="M150 220 Q {q}"/>'
    b += txt(95, 138, "bark removed", anchor="end") + txt(95, 154, "in a ring", anchor="end")
    b += '<line x1="102" y1="134" x2="134" y2="134"/>'
    return svg(300, 285, b)


def drooping():
    b = '<path d="M95 175 L105 245 L195 245 L205 175 Z"/><line x1="90" y1="175" x2="210" y2="175"/>'
    b += '<path d="M100 185 Q150 195 200 185" stroke-dasharray="2 4"/>'
    b += '<path d="M150 175 Q150 120 150 85"/>'
    b += '<path d="M150 100 Q105 80 80 125"/><path d="M80 125 Q108 112 150 112" />'
    b += '<path d="M150 90 Q195 70 222 118"/><path d="M222 118 Q192 106 150 100"/>'
    b += '<path d="M150 85 Q140 60 118 62 Q122 80 150 85"/>'
    b += txt(150, 268, "a potted plant")
    return svg(300, 285, b)


def flower_beaker():
    b = '<path d="M95 130 L95 235 Q95 245 105 245 L195 245 Q205 245 205 235 L205 130"/><line x1="90" y1="130" x2="210" y2="130"/>'
    b += '<path d="M97 160 L203 160" />' + txt(122, 200, "coloured") + txt(122, 216, "water") + '<path d="M150 235 L150 85"/>'
    b += '<ellipse cx="150" cy="58" rx="9" ry="22"/><ellipse cx="150" cy="58" rx="9" ry="22" transform="rotate(72 150 80)"/>'
    b += '<ellipse cx="150" cy="58" rx="9" ry="22" transform="rotate(-72 150 80)"/>'
    b += '<ellipse cx="150" cy="58" rx="9" ry="22" transform="rotate(144 150 80)"/><ellipse cx="150" cy="58" rx="9" ry="22" transform="rotate(-144 150 80)"/>'
    b += '<circle cx="150" cy="80" r="6" fill="white"/>'
    b += txt(150, 268, "white flower, stem cut")
    return svg(300, 285, b)


def tadpole():
    b = '<path d="M20 120 Q55 108 90 120 T160 120 T230 120 T280 120"/>'
    b += '<ellipse cx="110" cy="170" rx="30" ry="20"/><path d="M140 170 Q175 150 215 175 Q175 195 140 175"/>'
    b += '<circle cx="96" cy="164" r="3" fill="currentColor"/>'
    b += txt(150, 230, "a young frog in a pond")
    return svg(300, 250, b)


def cutting():
    b = '<path d="M105 120 L105 235 Q105 245 115 245 L185 245 Q195 245 195 235 L195 120"/><line x1="100" y1="120" x2="200" y2="120"/>'
    b += '<path d="M107 160 L193 160"/><path d="M150 235 L150 60"/>'
    b += leaf(120, 82, 25, 28, 12) + leaf(180, 70, -25, 28, 12)
    b += txt(150, 268, "a cutting at the start")
    return svg(300, 285, b)


def carrot():
    b = '<line x1="20" y1="120" x2="280" y2="120"/>' + txt(272, 138, "soil", anchor="end")
    b += '<path d="M130 120 Q150 125 170 120 L152 232 Q150 238 148 232 Z"/>'
    for q in ("118 90 100 50", "150 85 150 40", "182 90 200 50"):
        b += f'<path d="M150 120 Q {q}"/>'
    for cx, cy in ((100, 46), (150, 36), (200, 46)):
        b += f'<ellipse cx="{cx}" cy="{cy}" rx="10" ry="16"/>'
    b += txt(150, 262, "a carrot plant, pulled up")  # kept neutral: no part named
    return svg(300, 280, b)


def box(x, y, w, h, s, bold=False):
    b = f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6"/>'
    if "|" in s:
        a, c = s.split("|")
        return b + txt(x + w / 2, y + h / 2 - 3, a, 14, bold=bold) + txt(x + w / 2, y + h / 2 + 15, c, 14, bold=bold)
    return b + txt(x + w / 2, y + h / 2 + 5, s, 14, bold=bold)


def stages(names, caption):
    """Boxes in the given (scrambled) order with no arrows: shows the stages, not their order."""
    n = len(names)
    w = 84
    gap = 12
    total = n * w + (n - 1) * gap
    W = max(total + 20, 300)
    x0 = (W - total) / 2
    b = "".join(box(x0 + i * (w + gap), 40, w, 54, s) for i, s in enumerate(names))
    b += txt(W / 2, 22, caption, 13) + txt(W / 2, 122, "(not in order)", 12)
    return svg(W, 136, b)


def chain(names, caption):
    """Boxes joined by arrows; '?' marks the stage asked about, an ellipsis marks stages not shown."""
    n = len(names)
    w, gap = 76, 22
    total = n * w + (n - 1) * gap
    W = total + 20
    defs = '<defs><marker id="ah" markerUnits="userSpaceOnUse" markerWidth="10" markerHeight="10" refX="9" refY="5" orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="currentColor"/></marker></defs>'
    b = defs
    for i, s in enumerate(names):
        x = 10 + i * (w + gap)
        b += box(x, 40, w, 54, s, bold=(s == "?"))
        if i < n - 1:
            b += f'<line x1="{x + w + 2}" y1="67" x2="{x + w + gap - 2}" y2="67" marker-end="url(#ah)"/>'
    b += txt(W / 2, 22, caption, 13)
    return svg(W, 112, b)


def rows(lines, caption):
    defs = '<defs><marker id="ah" markerUnits="userSpaceOnUse" markerWidth="10" markerHeight="10" refX="9" refY="5" orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="currentColor"/></marker></defs>'
    b = defs + txt(180, 22, caption, 13)
    for i, (name, cells) in enumerate(lines):
        y = 40 + i * 50
        b += txt(10, y + 24, name, 14, anchor="start", bold=True)
        x = 92
        for j, c in enumerate(cells):
            wd = 62 if c in ("?", "...") else 78
            b += box(x, y, wd, 34, c, bold=(c == "?"))
            if j < len(cells) - 1:
                b += f'<line x1="{x + wd + 1}" y1="{y + 17}" x2="{x + wd + 11}" y2="{y + 17}" marker-end="url(#ah)"/>'
            x += wd + 13
    return svg(480, 40 + len(lines) * 50, b)


def img(name, alt):
    return {"img": f"/science/{name}.webp", "alt": alt, "labels": []}


RING = "Life cycle of a {} drawn as a ring of pictures of its stages joined by arrows."

SPECS = {
    "sci-life-cycles": {
        "lc-001": lambda: chain(["Egg", "?", "Pupa", "Adult"], "Life cycle of a butterfly"),
        "lc-002": lambda: chain(["Egg", "...", "Adult frog"], "Life cycle of a frog (stages in between not shown)"),
        "lc-003": lambda: img("butterfly-ring", RING.format("butterfly")),
        "lc-005": lambda: chain(["Egg", "?", "Young frog", "Adult frog"], "Life cycle of a frog"),
        "lc-006": lambda: stages(["Adult hen", "Egg", "Chick"], "Stages of a chicken"),
        "lc-007": lambda: stages(["Young plant", "Seed", "Adult plant", "Seedling"], "Stages of a bean plant"),
        "lc-008": lambda: stages(["Adult plant", "Seed", "Seedling", "Young plant"], "Stages of a flowering plant"),
        "lc-012": lambda: stages(["Pupa", "Adult", "Egg", "Larva"], "Stages of a butterfly"),
        "lc-013": lambda: stages(["Pupa", "Adult", "Egg", "Larva"], "Stages of a butterfly"),
        "lc-014": lambda: stages(["Pupa", "Adult", "Egg", "Larva"], "Stages of a mosquito"),
        "lc-015": lambda: stages(["Adult frog", "Egg", "Young frog", "Tadpole"], "Stages of a frog"),
        "lc-016": lambda: img("grasshopper-ring", RING.format("grasshopper")),
        "lc-017": lambda: chain(["Egg", "Larva", "?", "Adult"], "Life cycle of a butterfly"),
        "lc-019": lambda: img("pp-bean-seed", "A bean seed cut open, showing its outer covering and the parts inside."),
        "lc-020": lambda: img("grasshopper-ring", RING.format("grasshopper")),
        "lc-023": lambda: stages(["Pupa", "Adult", "Egg", "Larva"], "Stages of a mosquito"),
        "lc-024": lambda: rows([("Cockroach", ["?", "Nymph", "Adult"]), ("Chicken", ["?", "Chick", "Adult hen"]),
                                ("Frog", ["?", "Tadpole", "Young frog", "Adult frog"])], "The first stage is left blank"),
        "lc-025": lambda: stages(["Pupa", "Adult", "Egg", "Larva"], "Stages of a beetle"),
    },
    "sci-plant-parts": {
        "pp-001": lambda: img("pp-whole-plant", "A potted plant in line art."),
        "pp-002": lambda: img("pp-whole-plant", "A potted plant in line art."),
        "pp-003": lambda: img("pp-whole-plant", "A potted plant in line art."),
        "pp-009": lambda: cutting(),
        "pp-010": lambda: img("pp-kangkong", "A kangkong plant floating in water."),
        "pp-011": None,
        "pp-012": lambda: img("pp-whole-plant", "A potted plant in line art."),
        "pp-013": lambda: tree(),
        "pp-016": lambda: img("pp-whole-plant", "A potted plant in line art."),
        "pp-018": lambda: img("pp-whole-plant", "A potted plant in line art."),
        "pp-019": lambda: plant(),
        "pp-020": lambda: plant(),
        "pp-022": lambda: img("pp-whole-plant", "A potted plant in line art."),
        # re-filed under Plant reproduction
        "pp-005": lambda: img("pp-whole-plant", "A potted plant in line art."),
        "pp-006": lambda: img("pp-mango-cut", "A fruit cut open, showing its skin, the soft part and a large seed inside."),
        "pp-021": lambda: img("pp-flower-cut", "A flower cut in half, showing its petals and the parts inside."),
        "pp-024": lambda: img("pp-bean-seed", "A bean seed cut open, showing its outer covering and the parts inside."),
        "pp-025": lambda: tree(),
    },
    "sci-plant-transport": {
        "pt-001": lambda: plant(), "pt-002": lambda: img("pt-root-hairs", "A young root with many tiny thread-like growths along it."),
        "pt-003": lambda: img("pt-root-hairs", "A young root with many tiny thread-like growths along it."),
        "pt-004": lambda: plant(), "pt-005": lambda: plant(), "pt-006": lambda: plant(), "pt-008": lambda: plant(),
        "pt-009": lambda: plant(), "pt-010": lambda: plant(), "pt-011": lambda: plant(), "pt-012": lambda: plant(),
        "pt-013": lambda: plant(), "pt-016": lambda: plant(), "pt-017": lambda: tree_ringed(), "pt-018": lambda: tree_ringed(),
        "pt-020": lambda: plant(), "pt-021": lambda: drooping(), "pt-022": lambda: plant(), "pt-023": lambda: flower_beaker(),
        "pt-024": lambda: tree(), "pt-025": lambda: plant(), "pt-026": lambda: plant(),
        "pt-028": lambda: img("pt-root-hairs", "A young root with many tiny thread-like growths along it."),
    },
}


def figures():
    """Set (or, where the spec is None, remove) the figure of every listed item, whichever file it is in."""
    specs = {k: v for group in SPECS.values() for k, v in group.items()}
    n = 0
    for f in sorted(ITEMS.glob("*.json")):
        d = json.loads(f.read_text())
        for it in d["items"]:
            if it["key"] in specs:
                fn = specs[it["key"]]
                if fn is None:
                    it.pop("figure", None)
                else:
                    it["figure"] = fn()
                n += 1
        f.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n")
    print("figures set:", n)


if __name__ == "__main__":
    figures()
