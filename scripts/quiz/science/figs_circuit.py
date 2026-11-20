"""Code-drawn circuit diagrams (black and white, standard symbols): circuit(rows, left, right).
Items: ("B", n[, label]) battery of n cells | ("L", label[, lit]) bulb | ("S", label, closed) switch | ("O", label) object under test.
rows = horizontal wires (first at the top, last at the bottom, others between are parallel branches joined to the side wires; put the battery on the bottom row or on `left`); left/right = items on the side wires."""
from fillkit import svg, txt


def _bulb(x, y, label, lit):
    b = f'<circle cx="{x}" cy="{y}" r="14" fill="#fff" stroke-width="2"/><line x1="{x - 10}" y1="{y - 10}" x2="{x + 10}" y2="{y + 10}" stroke-width="1.6"/><line x1="{x + 10}" y1="{y - 10}" x2="{x - 10}" y2="{y + 10}" stroke-width="1.6"/>'
    if lit:
        for dx, dy in ((0, -22), (-17, -17), (17, -17)):
            b += f'<line x1="{x + dx * 0.8:.1f}" y1="{y + dy * 0.8:.1f}" x2="{x + dx * 1.15:.1f}" y2="{y + dy * 1.15:.1f}" stroke-width="1.6"/>'
    return b, 16


def _cells(x, y, n):
    w = n * 10 + 6
    b = f'<rect x="{x - w / 2}" y="{y - 14}" width="{w}" height="28" fill="#fff" stroke="none"/>'
    for i in range(n):
        cx = x - w / 2 + 5 + i * 10
        b += f'<line x1="{cx}" y1="{y - 13}" x2="{cx}" y2="{y + 13}" stroke-width="2.4"/><line x1="{cx + 6}" y1="{y - 7}" x2="{cx + 6}" y2="{y + 7}" stroke-width="4"/>'
    return b, w / 2 + 2


def _switch(x, y, closed):
    b = f'<rect x="{x - 15}" y="{y - 6}" width="30" height="12" fill="#fff" stroke="none"/><circle cx="{x - 14}" cy="{y}" r="2.5" fill="currentColor"/><circle cx="{x + 14}" cy="{y}" r="2.5" fill="currentColor"/>'
    b += f'<line x1="{x - 14}" y1="{y}" x2="{x + 14}" y2="{y}" stroke-width="2"/>' if closed else f'<line x1="{x - 14}" y1="{y}" x2="{x + 10}" y2="{y - 13}" stroke-width="2"/>'
    return b, 16


def _object(x, y, label):
    return f'<rect x="{x - 16}" y="{y - 10}" width="32" height="20" fill="#fff" stroke-width="2"/>' + txt(x, y + 5, label, 12), 18


def _item(it, x, y, rot):
    k = it[0]
    if k == "B":
        s, hw = _cells(0, 0, it[1]); lab = it[2] if len(it) > 2 else None
    elif k == "L":
        s, hw = _bulb(0, 0, it[1], it[2] if len(it) > 2 else None); lab = it[1]
    elif k == "S":
        s, hw = _switch(0, 0, it[2]); lab = it[1]
    else:
        s, hw = _object(0, 0, it[1]); lab = None
    g = f'<g transform="translate({x} {y}) rotate({90 if rot else 0})">{s}</g>'
    if lab:
        g += txt(x + (24 if rot else 0), y + (4 if rot else -22), lab, 13, bold=True) if k != "L" else txt(x + (26 if rot else 0), y + (5 if rot else (-36 if len(it) > 2 and it[2] else -22)), lab, 13, bold=True)
    return g


def circuit(rows, left=(), right=(), W=300, H=None, caption=None, main=None):
    # main = a switch item drawn in series on the left side wire, between the last branch and the battery row
    # (put it in a top row instead and it would be a parallel branch across the battery). Pass it explicitly; rows then holds the branches and the battery row (at least 2).
    n = len(rows)
    x0, x1 = 44, W - 44
    top = 58 if caption else 36
    H = H or (top + (n - 1) * 56 + 40 if n > 2 else top + 100 + 36)
    y1 = H - 36
    ys = [top + (y1 - top) * i / (n - 1) for i in range(n)]
    b = txt(W / 2, 16, caption, 13, bold=True) if caption else ""
    b += f'<line x1="{x0}" y1="{ys[0]}" x2="{x0}" y2="{y1}"/><line x1="{x1}" y1="{ys[0]}" x2="{x1}" y2="{y1}"/>'
    for y in ys:
        b += f'<line x1="{x0}" y1="{y}" x2="{x1}" y2="{y}"/>'
    if n > 2:
        for y in ys[1:-1]:
            b += f'<circle cx="{x0}" cy="{y}" r="2.5" fill="currentColor"/><circle cx="{x1}" cy="{y}" r="2.5" fill="currentColor"/>'
    for y, items in zip(ys, rows):
        m = len(items)
        for i, it in enumerate(items):
            b += _item(it, x0 + (x1 - x0) * (i + 1) / (m + 1), y, False)
    if main:
        b += _item(main, x0, (ys[-2] + ys[-1]) / 2, True)
    for xs, items in ((x0, left), (x1, right)):
        m = len(items)
        for i, it in enumerate(items):
            b += _item(it, xs, ys[0] + (y1 - ys[0]) * (i + 1) / (m + 1), True)
    return svg(W, H, b)


def pair(figs, gap=14):
    """Place several circuit() figures side by side in one figure."""
    import re
    parts = []
    x = 0
    H = 0
    for f in figs:
        m = re.match(r'<svg viewBox="0 0 ([\d.]+) ([\d.]+)"', f)
        w, h = float(m.group(1)), float(m.group(2))
        parts.append((x, w, h, f))
        x += w + gap
        H = max(H, h)
    body = ""
    for x0, w, h, f in parts:
        body += f.replace("<svg viewBox", f'<svg x="{x0}" y="{(H - h) / 2:.1f}" width="{w}" height="{h}" viewBox', 1)
    return svg(x - gap, H, body)
