"""Code-drawn flower cut in half (black and white). flower({"A": "petal", ...}, ovules=1) -> svg string.
Part names: petal, anther, filament, stigma, style, ovary, ovule, sepal. The letters are placed on leader lines."""
from fillkit import svg, txt

# part -> (point on the part, label position, anchor)
ANCH = {
    "petal": ((66, 118), (24, 126), "middle"),
    "anther": ((86, 88), (50, 60), "middle"),
    "filament": ((98, 130), (66, 168), "middle"),
    "stigma": ((138, 62), (176, 44), "middle"),
    "style": ((130, 96), (176, 86), "middle"),
    "ovary": ((148, 152), (222, 150), "middle"),
    "ovule": ((130, 156), (222, 190), "middle"),
    "sepal": ((84, 190), (40, 206), "middle"),
    "anther2": ((174, 88), (206, 60), "middle"),
}


def flower(labels, ovules=1, extra=""):
    b = '<path d="M122 232 V190 Q130 184 138 190 V232"/>'
    b += '<path d="M112 176 Q42 154 44 78 Q96 98 112 176 Z"/><path d="M148 176 Q218 154 216 78 Q164 98 148 176 Z"/>'
    b += '<path d="M112 184 Q86 200 70 190 Q90 178 112 176"/><path d="M148 184 Q174 200 190 190 Q170 178 148 176"/>'
    b += '<path d="M112 168 Q84 140 88 98"/><path d="M148 168 Q176 140 172 98"/>'
    b += '<ellipse cx="88" cy="90" rx="6" ry="9"/><ellipse cx="172" cy="90" rx="6" ry="9"/>'
    b += '<ellipse cx="130" cy="152" rx="20" ry="26"/><path d="M130 126 V72"/><ellipse cx="130" cy="64" rx="10" ry="6"/>'
    pos = {1: [(130, 156)], 2: [(123, 146), (137, 160)], 3: [(130, 140), (121, 160), (139, 160)], 4: [(122, 142), (138, 142), (122, 162), (138, 162)]}[ovules]
    for (x, y) in pos:
        b += f'<ellipse cx="{x}" cy="{y}" rx="5" ry="6"/>'
    for letter, part in labels.items():
        (px, py), (tx, ty), an = ANCH[part]
        lx = tx + (10 if tx < px else -10)
        b += f'<line x1="{px}" y1="{py}" x2="{lx}" y2="{ty - 4}" stroke-width="1.5"/>' + txt(tx, ty + 2, letter, 16, bold=True)
    return svg(250, 240, b + extra)
