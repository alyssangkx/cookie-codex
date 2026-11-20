"""Code-drawn photosynthesis set-ups (black and white): leaf(), jar(), pondweed(), tubes()."""
from fillkit import svg, txt


def _hatch(x, y, w, h, gap=9):
    b = f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="none" stroke-width="1.5"/>'
    k = -h
    while k < w:
        x1, y1, x2, y2 = x + max(k, 0), y + (h if k < 0 else 0) - (0 if k < 0 else 0), x + min(k + h, w), y
        # diagonal from bottom-left to top-right inside the rectangle
        xa, ya = x + k, y + h
        xb, yb = x + k + h, y
        if xa < x:
            ya -= (x - xa); xa = x
        if xb > x + w:
            yb += (xb - x - w); xb = x + w
        if xb > xa:
            b += f'<line x1="{xa}" y1="{ya}" x2="{xb}" y2="{yb}" stroke-width="1"/>'
        k += gap
    return b


def leaf(zones, caption=None, W=360, H=170):
    """A leaf drawn as a rounded shape split into vertical zones. zones = [(letter, colour_word, covered_by_foil)]
    colour_word is printed under the zone ('green' or 'white'); a covered zone is hatched."""
    n = len(zones)
    x0, y0, lw, lh = 40, 44, 280, 84
    b = (txt(W / 2, 16, caption, 13, bold=True) if caption else "")
    b += f'<rect x="{x0}" y="{y0}" width="{lw}" height="{lh}" rx="38" fill="none" stroke-width="2.5"/>'
    b += f'<line x1="14" y1="{y0 + lh / 2}" x2="{x0}" y2="{y0 + lh / 2}" stroke-width="3"/>'
    zw = (lw - 76) / n
    for i, (L, word, covered) in enumerate(zones):
        zx = x0 + 38 + i * zw
        if i > 0:
            b += f'<line x1="{zx}" y1="{y0 + 4}" x2="{zx}" y2="{y0 + lh - 4}" stroke-width="1" stroke-dasharray="3 3"/>'
        if covered:
            b += _hatch(zx + 3, y0 + 4, zw - 6, lh - 8)
        b += f'<circle cx="{zx + zw / 2}" cy="{y0 + lh / 2}" r="12" fill="#fff"/>' + txt(zx + zw / 2, y0 + lh / 2 + 5, L, 15, bold=True)
        b += txt(zx + zw / 2, y0 + lh + 20, word, 12)
    return svg(W, H, b)


def jar(dish=None, light=True, W=250, H=230, caption=None):
    """A potted plant under a glass jar. dish = text shown on a dish inside (or None); light=False draws a dark cover."""
    b = (txt(W / 2, 16, caption, 13, bold=True) if caption else "")
    jx, jy, jw, jh = 60, 40, 140, 150
    b += f'<path d="M{jx} {jy + jh} V{jy + 30} Q{jx} {jy} {jx + 40} {jy} H{jx + jw - 40} Q{jx + jw} {jy} {jx + jw} {jy + 30} V{jy + jh}" fill="none" stroke-width="2.5"/>'
    b += f'<line x1="{jx - 12}" y1="{jy + jh}" x2="{jx + jw + 12}" y2="{jy + jh}" stroke-width="3"/>'
    px = jx + 90
    b += f'<path d="M{px - 24} {jy + jh - 34} H{px + 24} L{px + 18} {jy + jh} H{px - 18} Z" fill="none"/>'
    b += f'<line x1="{px}" y1="{jy + jh - 34}" x2="{px}" y2="{jy + 70}" stroke-width="3"/>'
    b += f'<ellipse cx="{px - 22}" cy="{jy + 92}" rx="22" ry="8" transform="rotate(-25 {px - 22} {jy + 92})" fill="none"/><ellipse cx="{px + 22}" cy="{jy + 80}" rx="22" ry="8" transform="rotate(25 {px + 22} {jy + 80})" fill="none"/>'
    if dish:
        b += f'<rect x="{jx + 8}" y="{jy + jh - 20}" width="34" height="14" rx="3" fill="none"/>' + txt(jx + 25, jy + jh + 18, dish, 11)
    if not light:
        b += f'<rect x="{jx - 6}" y="{jy - 8}" width="{jw + 12}" height="{jh + 8}" fill="none" stroke-width="2" stroke-dasharray="6 4"/>'
    else:
        for k, dy in enumerate((0, 22, 44)):
            b += f'<line x1="6" y1="{jy + 20 + dy}" x2="40" y2="{jy + 20 + dy}" stroke-width="2"/>'
        b += txt(24, jy + 100, "light", 12)
    return svg(W, H, b)


def pondweed(dist, W=340, H=220, caption=None):
    """A beaker with pondweed under an upturned funnel and test tube, with a lamp dist cm away."""
    b = (txt(W / 2, 16, caption, 13, bold=True) if caption else "")
    bx, by, bw, bh = 150, 60, 150, 130
    b += f'<path d="M{bx} {by} V{by + bh} H{bx + bw} V{by}" fill="none" stroke-width="2.5"/>'
    b += f'<line x1="{bx + 4}" y1="{by + 22}" x2="{bx + bw - 4}" y2="{by + 22}" stroke-dasharray="4 3"/>'
    cx = bx + bw / 2
    b += f'<path d="M{cx - 40} {by + bh - 40} L{cx - 8} {by + 40} H{cx + 8} L{cx + 40} {by + bh - 40} Z" fill="none"/>'
    b += f'<rect x="{cx - 9}" y="{by + 4}" width="18" height="38" fill="#fff" stroke-width="1.8"/>'
    for sx in (-14, 0, 14):
        b += f'<path d="M{cx + sx} {by + bh} Q{cx + sx + 6} {by + bh - 30} {cx + sx} {by + bh - 56}" fill="none" stroke-width="2"/>'
    for i, (dx, dy) in enumerate(((-6, 62), (5, 78), (-3, 94))):
        b += f'<circle cx="{cx + dx}" cy="{by + dy}" r="2.5" fill="none"/>'
    b += f'<circle cx="40" cy="{by + 84}" r="18" fill="none" stroke-width="2.5"/>' + txt(40, by + 124, "lamp", 12)
    b += f'<line x1="58" y1="{by + 130}" x2="{bx}" y2="{by + 130}" stroke-width="1.5"/><line x1="58" y1="{by + 124}" x2="58" y2="{by + 136}"/><line x1="{bx}" y1="{by + 124}" x2="{bx}" y2="{by + 136}"/>'
    b += txt((58 + bx) / 2, by + 150, f"{dist} cm", 13)
    return svg(W, H, b)


def tubes(specs, W=None, H=190, caption=None):
    """Test tubes in a row. specs = [(letter, line1, line2, in_dark)]; a tube kept in the dark is hatched with foil."""
    n = len(specs)
    gap = 84
    W = W or n * gap + 24
    b = (txt(W / 2, 16, caption, 13, bold=True) if caption else "")
    for i, (L, l1, l2, dark) in enumerate(specs):
        x = 14 + i * gap + 10
        w, y, h = 46, 34, 104
        b += f'<path d="M{x} {y} V{y + h - 22} Q{x} {y + h} {x + w / 2} {y + h} Q{x + w} {y + h} {x + w} {y + h - 22} V{y}" fill="none" stroke-width="2"/>'
        if dark:
            b += _hatch(x - 3, y + 30, w + 6, h - 36, 8)
        b += f'<line x1="{x + 2}" y1="{y + 24}" x2="{x + w - 2}" y2="{y + 24}" stroke-dasharray="3 3"/>'
        for yy, t in ((y + 62, l1), (y + 78, l2)):
            if t:
                b += f'<rect x="{x + w / 2 - len(t) * 3.4 - 2}" y="{yy - 11}" width="{len(t) * 6.8 + 4}" height="15" fill="#fff"/>' + txt(x + w / 2, yy, t, 11)
        b += txt(x + w / 2, y + h + 22, L, 15, bold=True)
    return svg(W, H, b)
