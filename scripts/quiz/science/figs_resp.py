"""Code-drawn figures for the respiratory / circulatory sub-topic (black and white, currentColor, viewBox).

resp_system(nose, windpipe, lung, heart)   front view of head and chest with four letters
fish(gill, fin, tail, eye)                 a fish with four lettered regions
circ_block(letters, legend)                heart, lungs and body with four arrows (solid = oxygen-rich, dashed = oxygen-poor when legend)
integ_block()                              small intestine, blood and lungs with three lettered arrows
"""
from fillkit import svg, txt, AH


def _tag(x, y, s):
    return f'<circle cx="{x}" cy="{y}" r="12" fill="#fff"/>' + txt(x, y + 6, s, 17, bold=True)


def resp_system(nose="P", windpipe="Q", lung="R", heart="S", caption="Parts of the human body"):
    b = txt(150, 16, caption, 13, bold=True)
    b += '<circle cx="150" cy="62" r="30"/><path d="M150 54 L140 78 Q150 83 160 78 Z" stroke-width="1.6"/>'
    b += '<path d="M92 112 Q58 128 54 175 L54 300 H246 V175 Q242 128 208 112" stroke-width="1.4"/>'
    b += '<path d="M143 92 V150 M157 92 V150"/><path d="M143 150 Q135 160 120 170 M157 150 Q165 160 180 170"/>'
    b += '<path d="M120 160 Q70 160 66 215 Q64 262 104 262 Q132 258 134 220 Q136 180 120 160 Z"/>'
    b += '<path d="M180 160 Q230 160 234 215 Q236 262 196 262 Q168 258 166 220 Q164 180 180 160 Z"/>'
    b += '<path d="M150 272 C128 255 134 232 150 240 C166 232 172 255 150 272 Z"/>'
    b += '<line x1="162" y1="70" x2="212" y2="46"/>' + _tag(224, 42, nose)
    b += '<line x1="143" y1="120" x2="96" y2="120"/>' + _tag(84, 120, windpipe)
    b += '<line x1="226" y1="215" x2="266" y2="215"/>' + _tag(274, 215, lung)
    b += '<line x1="140" y1="256" x2="96" y2="284"/>' + _tag(84, 288, heart)
    return svg(300, 310, b)


def fish(gill="Q", fin="P", tail="R", eye="S", caption="A fish in water"):
    b = txt(150, 16, caption, 13, bold=True)
    b += '<path d="M60 110 Q100 60 170 62 Q225 66 245 110 Q225 154 170 156 Q100 158 60 110 Z"/>'
    b += '<path d="M245 110 L292 76 L292 144 Z"/>'
    b += '<circle cx="84" cy="104" r="5" fill="currentColor"/>'
    b += '<path d="M62 112 L76 114" stroke-width="1.6"/>'
    b += '<path d="M118 76 Q132 110 118 142"/><path d="M126 82 Q138 110 126 138" stroke-width="1.2"/><path d="M134 88 Q144 110 134 134" stroke-width="1.2"/>'
    b += '<path d="M165 62 Q185 30 215 70"/>'
    b += '<line x1="124" y1="110" x2="124" y2="110"/>'
    b += '<line x1="126" y1="108" x2="82" y2="176"/>' + _tag(76, 188, gill)
    b += '<line x1="196" y1="52" x2="216" y2="38"/>' + _tag(226, 34, fin)
    b += '<line x1="285" y1="110" x2="270" y2="168"/>' + _tag(268, 182, tail)
    b += '<line x1="84" y1="99" x2="64" y2="60"/>' + _tag(58, 48, eye)
    return svg(300, 210, b)


def _arrow(x1, y1, x2, y2, dashed):
    d = ' stroke-dasharray="7 5"' if dashed else ""
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke-width="2.4"{d} marker-end="url(#ah)"/>'


def circ_block(letters=("A", "B", "C", "D"), legend=False, caption="How blood moves round the body"):
    """letters = (heart->lungs, lungs->heart, heart->body, body->heart). With legend: solid = oxygen-rich, dashed = oxygen-poor."""
    hl, lh, hb, bh = letters
    H = 330 if legend else 280
    b = AH + txt(150, 16, caption, 13, bold=True)
    for (x, y, w, h, t) in ((105, 30, 100, 40, "Lungs"), (105, 120, 100, 44, "Heart"), (105, 220, 100, 40, "Body")):
        b += f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8"/>' + txt(x + w / 2, y + h / 2 + 5, t, 15, bold=True)
    b += _arrow(135, 118, 135, 72, legend) + txt(120, 98, hl, 17, anchor="end", bold=True)
    b += _arrow(175, 72, 175, 118, False) + txt(190, 98, lh, 17, anchor="start", bold=True)
    b += _arrow(175, 166, 175, 218, False) + txt(190, 198, hb, 17, anchor="start", bold=True)
    b += _arrow(135, 218, 135, 166, legend) + txt(120, 198, bh, 17, anchor="end", bold=True)
    if legend:
        b += '<line x1="40" y1="290" x2="84" y2="290" stroke-width="2.4"/>' + txt(92, 295, "oxygen-rich blood", 13, anchor="start")
        b += '<line x1="40" y1="314" x2="84" y2="314" stroke-width="2.4" stroke-dasharray="7 5"/>' + txt(92, 319, "oxygen-poor blood", 13, anchor="start")
    return svg(300, H, b)


def integ_block(letters=("P", "Q", "R"), caption="Moving substances in the body"):
    """letters = (small intestine->blood, lungs->blood, blood->lungs)."""
    p, q, r = letters
    b = AH + txt(150, 16, caption, 13, bold=True)
    for (x, y, w, h, t) in ((90, 30, 120, 40, "Small intestine"), (90, 120, 120, 44, "Blood"), (90, 220, 120, 40, "Lungs")):
        b += f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8"/>' + txt(x + w / 2, y + h / 2 + 5, t, 15, bold=True)
    b += _arrow(150, 72, 150, 118, False) + txt(165, 100, p, 17, anchor="start", bold=True)
    b += _arrow(130, 218, 130, 166, False) + txt(116, 198, q, 17, anchor="end", bold=True)
    b += _arrow(170, 166, 170, 218, False) + txt(185, 198, r, 17, anchor="start", bold=True)
    return svg(300, 275, b)
