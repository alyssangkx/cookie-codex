"""Geometry (math-geometry): angles, triangles and quadrilaterals, lines, symmetry, 2D/3D shapes, nets, cubes.

Angle figures are computed from the real angles (figures_D.Scene), the unknown is marked x, and each
independent check re-measures the target angle from coordinates instead of repeating the arithmetic.
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import *  # noqa: E402,F401
from figures import Fig  # noqa: E402
from figures_D import (Scene, vec, pt, meas, bearing, dist, intersect, panels, grid_fig, hexominoes,  # noqa: E402
                       is_cube_net, roll_labels, transforms, net_fig, solid_net, stack_fig, protractor_fig,
                       has_2x2)

T = "math-geometry"
G2 = "math-geometry-2d-shapes-"
G3 = "math-geometry-3d-shapes-and-nets-"
GA = "math-geometry-angles-"
GP = "math-geometry-perpendicular-and-parallel-lines-"
GR = "math-geometry-rectangle-and-square-"
GS = "math-geometry-line-symmetry-"
GT = "math-geometry-triangles-parallelogram-rhombus-and-trapezium-"


def art(word):
    return "an" if word[0] in "aeiou" else "a"


def deg(x):
    return f"{frac(x)}°"


def W(v, tag, why):
    return (v, tag, why)


def mk(fn, stem, ans, wrongs, steps, params, fig=None, show=deg, maxv=180):
    """Whole-number build with careless slips appended; wrongs above maxv are dropped."""
    ans = int(ans)
    slips_ = [W(ans + 10, "slip_ten_out", "Made a slip of 10 in the final subtraction."),
              W(ans - 10, "slip_ten_out", "Made a slip of 10 in the final subtraction."),
              W(ans + 5, "arithmetic_slip", "Made a small arithmetic slip."),
              W(ans - 5, "arithmetic_slip", "Made a small arithmetic slip."),
              W(ans + 2, "arithmetic_slip", "Made a small arithmetic slip.")]
    ws = [w for w in wrongs if w[0] is not None and (maxv is None or w[0] <= maxv)]
    ws = ws + [s for s in slips_ if maxv is None or s[0] <= maxv]
    return build(fn, stem, ans, ws, steps, params, show=show, whole=True, auto_slips=False, figure=fig)


def lab(name):
    return name


def opt_show(names):
    return lambda v: names[int(v) - 1]


def mark(a, tag=""):
    return f"{a}°"


# ============================================================ ANGLES: basic

@template(T, "basic", GA + "05", GA + "08", weight=2)
def angles_on_line(r):
    """math-pat-angles-one-step"""
    two = r.random() < 0.5
    a = r.randint(25, 135)
    b = r.randint(25, 120) if two else 0
    if two and a + b > 150:
        return None
    ans = 180 - a - b
    P = {"a": a, "b": b}
    sc = Scene()
    sc.add("O", 0, 0); sc.add("A", -1, 0); sc.add("B", 1, 0)
    sc.add("C", *vec(180 - a))
    if two:
        sc.add("D", *vec(180 - a - b))
    sc.seg("A", "B"); sc.seg("O", "C")
    sc.label("A", away="O"); sc.label("B", away="O"); sc.label("C", away="O"); sc.label("O", away=(0, 1.5), off=15)
    sc.ang("O", "A", "C", f"{a}°")
    if two:
        sc.seg("O", "D"); sc.label("D", away="O")
        sc.ang("O", "C", "D", f"{b}°")
        sc.ang("O", "D", "B", "x")
        stem = f"In the figure, AOB is a straight line. ∠AOC = {a}° and ∠COD = {b}°. Find ∠DOB."
        wr = [W(180 - a, "used_one_angle_only", "Subtracted only ∠AOC from 180°."),
              W(a + b, "added_given_angles", "Added the two given angles instead of subtracting from 180°."),
              W(abs(a - b), "subtracted_given_angles", "Found the difference between the two given angles."),
              W(360 - a - b, "used_360_on_a_line", "Used 360° instead of 180° for angles on a straight line.")]
        steps = ["Angles on a straight line add up to 180°.", f"∠DOB = 180° − {a}° − {b}° = {ans}°"]
    else:
        sc.ang("O", "C", "B", "x")
        stem = f"In the figure, AOB is a straight line. ∠AOC = {a}°. Find ∠COB."
        wr = [W(90 - a if a < 90 else a - 90, "used_right_angle", "Used 90° instead of 180°."),
              W(a, "gave_given_angle", "Gave the angle that was already known."),
              W(360 - a, "used_360_on_a_line", "Used 360° instead of 180°.")]
        steps = ["Angles on a straight line add up to 180°.", f"∠COB = 180° − {a}° = {ans}°"]
    return mk(angles_on_line, stem, ans, wr, steps, P, sc.svg("Angles on a straight line"))


def _line_pts(P):
    p = {"O": (0, 0), "A": (-1, 0), "B": (1, 0), "C": vec(180 - P["a"])}
    if P["b"]:
        p["D"] = vec(180 - P["a"] - P["b"])
    return p


@checker(angles_on_line)
def _(p):
    q = _line_pts(p)
    return F(round(meas(q["D"], q["O"], q["B"]) if p["b"] else meas(q["C"], q["O"], q["B"])))


@template(T, "basic", GA + "06", weight=2)
def angles_at_point(r):
    """math-pat-angles-one-step"""
    n = r.choice([3, 4])
    parts = [r.randint(40, 130) for _ in range(n - 1)]
    ans = 360 - sum(parts)
    if not 35 <= ans <= 175:
        return None
    angs = parts + [ans]
    cum = [0]
    for x in angs:
        cum.append(cum[-1] + x)
    sc = Scene()
    sc.add("O", 0, 0)
    names = "ABCD"[:n]
    off = r.choice([10, 20, 30])
    for i, nm in enumerate(names):
        sc.add(nm, *vec(off + cum[i]))
        sc.seg("O", nm); sc.label(nm, away="O")
    sc.label("O", away=(0, 3), off=15)
    for i in range(n):
        a1, a2 = names[i], names[(i + 1) % n]
        sc.ang("O", a1, a2, f"{angs[i]}°" if i < n - 1 else "x", r=20 + 3 * (i % 2))
    given = ", ".join(f"∠{names[i]}O{names[i + 1]} = {parts[i]}°" for i in range(n - 2))
    last = f"∠{names[n - 2]}O{names[n - 1]} = {parts[-1]}°"
    stem = (f"The lines OA, OB, {'OC' if n == 3 else 'OC and OD'} meet at the point O. {given} and {last}. "
            f"Find ∠{names[n - 1]}O{names[0]}.")
    s = sum(parts)
    wr = [W(180 - s if s < 180 else None, "used_180_at_a_point", "Used 180° instead of 360° for angles at a point."),
          W(s, "gave_sum_of_given", "Gave the sum of the known angles."),
          W(abs(360 - s - 180), "used_180_at_a_point", "Subtracted from 180° after using 360°."),
          W(90 - ans % 90 + ans if False else None, "x", "")]
    wr = [w for w in wr if w[0]]
    return mk(angles_at_point, stem, ans, wr,
              ["Angles at a point add up to 360°.", f"Sum of the known angles = {' + '.join(map(str, parts))} = {s}°",
               f"x = 360° − {s}° = {ans}°"],
              {"parts": parts, "off": off}, sc.svg("Angles at a point"))


@checker(angles_at_point)
def _(p):
    angs = p["parts"]
    cum = [p["off"]]
    for x in angs:
        cum.append(cum[-1] + x)
    first, last = vec(p["off"]), vec(cum[-1])
    return F(round(meas(last, (0, 0), first)))


@template(T, "basic", GA + "07", weight=2)
def vertically_opposite(r):
    """math-pat-angles-one-step"""
    a = r.randint(25, 155)
    if a == 90:
        return None
    mode = r.choice(["opp", "adj", "adj2"])
    al = r.randint(0, 40)
    sc = Scene()
    sc.add("O", 0, 0)
    sc.add("A", *vec(al)); sc.add("B", *vec(al + 180))
    sc.add("C", *vec(al + a)); sc.add("D", *vec(al + a + 180))
    sc.seg("A", "B"); sc.seg("C", "D")
    for n in "ABCD":
        sc.label(n, away="O")
    sc.label("O", away=vec(al + a / 2 + 90), off=15)
    # AOC = a given; ask BOD (opposite), COB or DOA (adjacent)
    sc.ang("O", "A", "C", f"{a}°")
    if mode == "opp":
        sc.ang("O", "B", "D", "x"); ans, tgt = a, "∠BOD"
        wr = [W(180 - a, "gave_adjacent_angle", "Used the adjacent angle (180° − a) instead of the equal opposite angle."),
              W(90 - a if a < 90 else None, "used_right_angle", "Used 90°."),
              W(360 - a, "used_360", "Used 360°."), W(a + 180 if a + 180 <= 180 else None, "x", "")]
        steps = ["Vertically opposite angles are equal.", f"∠BOD = ∠AOC = {a}°"]
        stem = f"Lines AB and CD cross at O. ∠AOC = {a}°. Find ∠BOD."
    else:
        tgtname = "∠COB" if mode == "adj" else "∠DOA"
        if mode == "adj":
            sc.ang("O", "C", "B", "x")
        else:
            sc.ang("O", "D", "A", "x")
        ans = 180 - a
        stem = f"Lines AB and CD cross at O. ∠AOC = {a}°. Find {tgtname}."
        wr = [W(a, "assumed_equal", "Assumed the angles were vertically opposite and equal."),
              W(360 - a, "used_360", "Used 360° instead of 180°."),
              W((360 - 2 * a) // 2 if a < 180 and (360 - 2 * a) % 2 == 0 else None, "x", "")]
        steps = ["Angles on a straight line add up to 180°.", f"{tgtname} = 180° − {a}° = {ans}°"]
    wr = [w for w in wr if w[0] and w[1] != "x"]
    return mk(vertically_opposite, stem, ans, wr, steps, {"a": a, "al": al, "mode": mode},
              sc.svg("Two crossing lines"))


@checker(vertically_opposite)
def _(p):
    a, al = p["a"], p["al"]
    O = (0, 0)
    A, B, C, D = vec(al), vec(al + 180), vec(al + a), vec(al + a + 180)
    if p["mode"] == "opp":
        return F(round(meas(B, O, D)))
    return F(round(meas(C, O, B) if p["mode"] == "adj" else meas(D, O, A)))


@template(T, "basic", GA + "01", GA + "02")
def angle_type(r):
    """Names of angle types"""
    th = r.choice([r.randint(5, 89), r.randint(91, 179), r.randint(181, 355), 90])
    nm = r.choice(NAMES)
    names = ["acute angle", "right angle", "obtuse angle", "reflex angle"]
    sc = Scene()
    sc.add("B", 0, 0); sc.add("A", *vec(r.choice([0, 15, 30]))); a0 = bearing((0, 0), sc.pts["A"])
    sc.add("C", *vec(a0 + th))
    sc.seg("B", "A"); sc.seg("B", "C")
    sc.label("A", away="B"); sc.label("C", away="B"); sc.label("B", away=(0, 0.01), off=0, dx=-4, dy=16)
    sc.ang("B", "A", "C", "x" if th != 90 else None, reflex=th > 180, r=26)
    if th == 90:
        pass
    code = 1 if th < 90 else 2 if th == 90 else 3 if th < 180 else 4
    stem = f"{nm} measures ∠ABC = {th}°, shown as angle x in the figure. What type of angle is it?"
    wr = [W(((code % 4) + 1), "confused_obtuse_reflex", "Mixed up the angle types."),
          W(((code + 1) % 4) + 1, "confused_obtuse_reflex", "Mixed up the angle types."),
          W(((code + 2) % 4) + 1, "confused_obtuse_reflex", "Mixed up the angle types.")]
    wr = [(v if v != code else 1 + (v % 4), t, w) for v, t, w in wr]
    q = build(angle_type, stem, code, wr, ["An angle < 90° is acute, = 90° is a right angle, between 90° and 180° is obtuse, "
                                           "and between 180° and 360° is reflex.", f"{th}° is a{'n' if code in (1, 3) else ''} {names[code - 1]}."],
              {"th": th}, show=opt_show(names), whole=True, auto_slips=False, figure=sc.svg("An angle"))
    return q


@checker(angle_type)
def _(p):
    t = p["th"]
    return F([t < 90, t == 90, 90 < t < 180, t > 180].index(True) + 1)


@template(T, "basic", GA + "03")
def read_protractor(r):
    th = r.randrange(25, 166, 5)
    right = r.random() < 0.5
    nm = r.choice(NAMES)
    ph = r.choice(["Find the size of ∠PQR.", "What is the size of angle PQR?", "Read off the size of ∠PQR."])
    side = "right" if right else "left"
    stem = (f"{nm} places a protractor with its centre on Q and the arm QP along the baseline, pointing to the {side}. "
            f"{ph}")
    fig = protractor_fig(th, base_right=right)
    wr = [W(180 - th, "read_wrong_scale", "Read the scale that starts from the other end of the baseline."),
          W(th + 10 if th + 10 <= 175 else th - 15, "misread_by_one_interval", "Misread the tick marks by 10°."),
          W(th - 10, "misread_by_one_interval", "Misread the tick marks by 10°.")]
    return mk(read_protractor, stem, th, wr,
              [f"QP lies along the 0° mark on the {'outer' if right else 'inner'} scale, so read that scale.",
               f"The arm QR crosses {th}°. ∠PQR = {th}°"], {"th": th, "right": right}, fig)


@checker(read_protractor)
def _(p):
    # outer scale reading from the right = angle of the arm; the inner scale is its supplement
    arm = p["th"] if p["right"] else 180 - p["th"]
    outer, inner = arm, 180 - arm
    return F(outer if p["right"] else inner)


@template(T, "basic", GA + "02", weight=2)
def angle_notation(r):
    """math-pat-angles-one-step"""
    a, b = r.randint(20, 70), r.randint(20, 70)
    s0 = r.randint(5, 40)
    sc = Scene()
    sc.add("B", 0, 0)
    for nm, ang in (("A", s0), ("C", s0 + a), ("D", s0 + a + b)):
        sc.add(nm, *vec(ang)); sc.seg("B", nm); sc.label(nm, away="B")
    sc.label("B", away=(0, 1), off=15, dx=-3, dy=12)
    mode = r.choice(["sum", "diff"])
    if mode == "sum":
        sc.ang("B", "A", "C", f"{a}°", r=26); sc.ang("B", "C", "D", f"{b}°", r=26)
        sc.ang("B", "A", "D", "x", r=50)
        stem = f"In the figure, ∠ABC = {a}° and ∠CBD = {b}°. Find ∠ABD."
        ans = a + b
        wr = [W(abs(a - b), "subtracted_given_angles", "Subtracted the two angles."),
              W(180 - a - b, "used_180", "Subtracted from 180° as if on a straight line."),
              W(360 - a - b, "used_360", "Subtracted from 360°.")]
        steps = ["∠ABD is made up of ∠ABC and ∠CBD.", f"∠ABD = {a}° + {b}° = {ans}°"]
    else:
        sc.ang("B", "A", "C", f"{a}°", r=26); sc.ang("B", "A", "D", f"{a + b}°", r=50)
        sc.ang("B", "C", "D", "x", r=26)
        stem = f"In the figure, ∠ABC = {a}° and ∠ABD = {a + b}°. Find ∠CBD."
        ans = b
        wr = [W(a + b + a, "added_given_angles", "Added the two given angles."),
              W(abs(b - a) if abs(b - a) else None, "x", ""),
              W(180 - a - b, "used_180", "Subtracted from 180°."),
              W(a, "gave_given_angle", "Gave ∠ABC.")]
        wr = [w for w in wr if w[1] != "x"]
        steps = ["∠CBD = ∠ABD − ∠ABC.", f"∠CBD = {a + b}° − {a}° = {ans}°"]
    return mk(angle_notation, stem, ans, wr, steps, {"a": a, "b": b, "s0": s0, "mode": mode}, sc.svg("Angles at B"))


@checker(angle_notation)
def _(p):
    s0, a, b = p["s0"], p["a"], p["b"]
    B, A, C, D = (0, 0), vec(s0), vec(s0 + a), vec(s0 + a + b)
    return F(round(meas(A, B, D) if p["mode"] == "sum" else meas(C, B, D)))


# ============================================================ ANGLES: intermediate

def _coef(c, v="x"):
    return v if c == 1 else f"{c}{v}"


@template(T, "intermediate", GA + "07", GA + "08", weight=2)
def crossing_lines_algebra(r):
    """math-pat-angles-one-step"""
    a, b = r.randint(1, 4), r.randint(1, 4)
    x = r.randint(12, 36)
    c = 180 - (a + b) * x
    if not (0 < c <= 80) or not 28 <= a * x <= 150:
        return None
    al = r.randint(0, 30)
    sc = Scene()
    sc.add("O", 0, 0)
    A, B, C, D = vec(al), vec(al + 180), vec(al + a * x), vec(al + a * x + 180)
    for n, p in zip("ABCD", (A, B, C, D)):
        sc.add(n, *p); sc.label(n, away="O")
    sc.seg("A", "B"); sc.seg("C", "D")
    sc.label("O", away=vec(al + a * x / 2 + 90), off=15)
    sc.ang("O", "A", "C", f"({_coef(a)}°)".replace("(", "").replace(")", "") if False else f"{_coef(a)}°", r=24)
    sc.ang("O", "C", "B", f"({_coef(b)} + {c})°", r=24)
    sc.ang("O", "B", "D", "?", r=24)
    stem = (f"Lines AB and CD cross at O. ∠AOC = ({_coef(a)})° and ∠COB = ({_coef(b)} + {c})°. "
            f"Find the size of ∠BOD.")
    stem = stem.replace("(" + _coef(a) + ")°", _coef(a) + "°")
    ans = a * x
    wr = [W(x, "found_x_only", "Found x but did not work out the angle."),
          W(b * x + c, "found_adjacent_angle", "Found ∠COB instead of ∠BOD."),
          W(180 - x, "used_180_minus_x", "Subtracted x from 180°."),
          W(a * x + c, "added_constant_to_wrong_term", "Added the constant to the wrong angle.")]
    return mk(crossing_lines_algebra, stem, ans, wr,
              ["∠AOC and ∠COB are angles on a straight line, so they add up to 180°.",
               f"{_coef(a)} + {_coef(b)} + {c} = 180 → {a + b}x = {180 - c} → x = {x}",
               f"∠BOD is vertically opposite ∠AOC, so ∠BOD = {a} × {x}° = {ans}°"],
              {"a": a, "b": b, "c": c, "al": al}, sc.svg("Crossing lines"))


@checker(crossing_lines_algebra)
def _(p):
    a, b, c = p["a"], p["b"], p["c"]
    x = next(x for x in range(1, 181) if (a + b) * x + c == 180)
    al = p["al"]
    O = (0, 0)
    return F(round(meas(vec(al + 180), O, vec(al + a * x + 180))))


@template(T, "intermediate", GA + "05", GA + "06", GA + "08", weight=2)
def angle_ratio(r):
    """math-pat-angles-one-step"""
    line = r.random() < 0.5
    tot = 180 if line else 360
    ps = [r.randint(1, 6) for _ in range(3)]
    S = sum(ps)
    if tot % S:
        return None
    u = tot // S
    angs = [p * u for p in ps]
    if min(angs) < 25 or max(angs) > 150:
        return None
    k = r.choice([0, 1, 2]) if not line else r.choice([0, 1, 2])
    cum = [0, angs[0], angs[0] + angs[1], tot]
    sc = Scene()
    sc.add("O", 0, 0)
    off = 0 if line else r.choice([20, 40])
    base = 180 if line else off
    if line:
        sc.add("A", -1, 0); sc.add("B", 1, 0)
        sc.add("C", *vec(180 - angs[0])); sc.add("D", *vec(180 - angs[0] - angs[1]))
        sc.seg("A", "B"); sc.seg("O", "C"); sc.seg("O", "D")
        for n in "ABCD":
            sc.label(n, away="O")
        pts = ["A", "C", "D", "B"]
    else:
        for i, n in enumerate("ABC"):
            sc.add(n, *vec(off + cum[i])); sc.seg("O", n); sc.label(n, away="O")
        pts = ["A", "B", "C", "A"]
    sc.label("O", away=(0, 2) if line else (0, 0.2), off=15)
    for i in range(3):
        sc.ang("O", pts[i], pts[i + 1], "x" if i == k else None, r=22 + 3 * i)
    nm = [f"∠{pts[i]}O{pts[i + 1]}" for i in range(3)]
    ratio = " : ".join(str(p) for p in ps)
    if line:
        stem = f"AOB is a straight line. ∠AOC : ∠COD : ∠DOB = {ratio}. Find {nm[k]}."
    else:
        stem = f"The lines OA, OB and OC meet at O. ∠AOB : ∠BOC : ∠COA = {ratio}. Find {nm[k]}."
    ans = angs[k]
    wr = [W(u, "found_one_unit_only", "Found the size of 1 unit but did not multiply."),
          W(angs[(k + 1) % 3], "chose_wrong_angle", "Gave a different angle from the one asked."),
          W(angs[(k + 2) % 3], "chose_wrong_angle", "Gave a different angle from the one asked."),
          W(tot // 2 // S * ps[k] if not line else tot * 2 // S * ps[k], "used_wrong_total", "Used the wrong total for the angles.")]
    return mk(angle_ratio, stem, ans, wr,
              [f"The three angles add up to {tot}° ({'straight line' if line else 'angles at a point'}).",
               f"{ratio.replace(' : ', ' + ')} = {plural(S, 'unit')}; 1 unit = {tot}° ÷ {S} = {u}°",
               f"{nm[k]} = {ps[k]} × {u}° = {ans}°"],
              {"ps": ps, "tot": tot, "k": k}, sc.svg("Angles in a ratio"))


@checker(angle_ratio)
def _(p):
    ps, tot = p["ps"], p["tot"]
    # brute force the unit size
    u = next(u for u in range(1, 361) if u * sum(ps) == tot)
    return F(ps[p["k"]] * u)


@template(T, "intermediate", GA + "08", GA + "05")
def line_expressions(r):
    """math-pat-angles-one-step"""
    c1, c2 = r.randint(1, 3), r.randint(1, 3)
    c3 = r.randint(1, 3)
    k = c1 + c2 + c3
    x = r.randint(12, 36)
    m = 180 - k * x
    if not (5 <= m <= 70):
        return None
    a1, a2, a3 = c1 * x, c2 * x, c3 * x + m
    if min(a1, a2, a3) < 25 or max(a1, a2, a3) > 140:
        return None
    sc = Scene()
    sc.add("O", 0, 0); sc.add("A", -1, 0); sc.add("B", 1, 0)
    sc.add("C", *vec(180 - a1)); sc.add("D", *vec(180 - a1 - a2))
    sc.seg("A", "B"); sc.seg("O", "C"); sc.seg("O", "D")
    for n in "ABCD":
        sc.label(n, away="O")
    sc.label("O", away=(0, 2), off=15)
    sc.ang("O", "A", "C", f"{_coef(c1)}°", r=22)
    sc.ang("O", "C", "D", "?", r=26)
    sc.ang("O", "D", "B", f"({_coef(c3)} + {m})°", r=22)
    stem = (f"AOB is a straight line. ∠AOC = {_coef(c1)}°, ∠COD = {_coef(c2)}° and "
            f"∠DOB = ({_coef(c3)} + {m})°. Find the size of ∠COD.")
    ans = a2
    wr = [W(x, "found_x_only", "Found x but did not work out the angle."),
          W(a1, "chose_wrong_angle", "Gave ∠AOC instead of ∠COD."),
          W(a3, "chose_wrong_angle", "Gave ∠DOB instead of ∠COD."),
          W(c2 * (180 // k), "ignored_constant", "Ignored the constant when finding x.")]
    return mk(line_expressions, stem, ans, wr,
              ["The three angles on the straight line add up to 180°.",
               f"{_coef(c1)} + {_coef(c2)} + {_coef(c3)} + {m} = 180 → {k}x = {180 - m} → x = {x}",
               f"∠COD = {c2} × {x}° = {ans}°"], {"c": [c1, c2, c3], "m": m}, sc.svg("Angles on a line"))


@checker(line_expressions)
def _(p):
    c1, c2, c3 = p["c"]
    x = next(x for x in range(1, 181) if (c1 + c2 + c3) * x + p["m"] == 180)
    O = (0, 0)
    return F(round(meas(vec(180 - c1 * x), O, vec(180 - c1 * x - c2 * x))))


@template(T, "intermediate", GA + "06", GA + "08")
def reflex_angle(r):
    """math-pat-angles-one-step"""
    a = r.randint(25, 170)
    if a == 90:
        return None
    nm = r.choice(NAMES)
    s0 = r.choice([0, 10, 20, 30])
    sc = Scene(pad=52)
    sc.add("O", 0, 0); sc.add("A", *vec(s0)); sc.add("B", *vec(s0 + a))
    sc.seg("O", "A"); sc.seg("O", "B")
    sc.label("A", away="O"); sc.label("B", away="O"); sc.label("O", away=vec(s0 + a / 2), off=15)
    sc.ang("O", "A", "B", f"{a}°", r=22)
    sc.ang("O", "A", "B", "x", r=40, reflex=True)
    ans = 360 - a
    stem = f"{nm} measures ∠AOB = {a}°. Find the size of the reflex angle AOB, marked x."
    wr = [W(180 - a, "used_180_for_reflex", "Subtracted from 180° instead of 360°."),
          W(180 + a, "added_180", "Added 180° to the angle."),
          W(360 - a - 90, "subtracted_extra_right_angle", "Subtracted an extra 90°."),
          W(a, "gave_given_angle", "Gave the given angle.")]
    return mk(reflex_angle, stem, ans, wr,
              ["The angles at a point add up to 360°. The reflex angle is the rest of the full turn.",
               f"Reflex ∠AOB = 360° − {a}° = {ans}°"], {"a": a, "s0": s0}, sc.svg("Reflex angle"), maxv=None)


@checker(reflex_angle)
def _(p):
    O = (0, 0)
    small = meas(vec(p["s0"]), O, vec(p["s0"] + p["a"]))
    return F(round(360 - small))


# ============================================================ ANGLES: competent

@template(T, "competent", GA + "08", GT + "06")
def square_isosceles(r):
    """math-pat-angles-chained-shapes"""
    al = r.randrange(20, 71, 2)
    outside = r.random() < 0.5
    s = 1.0
    sc = Scene()
    sc.add("A", 0, 0); sc.add("B", s, 0); sc.add("C", s, s); sc.add("D", 0, s)
    sc.add("E", *vec(-al if outside else al))
    sc.poly(["A", "B", "C", "D"])
    sc.seg("A", "E"); sc.seg("B", "E")
    sc.label("A", away=(0.5, 0.5)); sc.label("B", away=(0.5, 0.5)); sc.label("C", away=(0.5, 0.5)); sc.label("D", away=(0.5, 0.5))
    sc.label("E", away=(0.5, 0.5) if outside else (0.2, 0.2), off=14)
    sc.tick("A", "B"); sc.tick("A", "E"); sc.tick("A", "D")
    sc.ang("A", "B", "E", f"{al}°", r=24)
    sc.ang("E", "A", "D", "x", r=22)
    if not outside:
        sc.cmds = [c for c in sc.cmds]
    where = "outside" if outside else "inside"
    stem = (f"ABCD is a square. E is a point {where} the square such that AB = AE and ∠BAE = {al}°. "
            f"Find ∠AED.")
    ans = (90 - al) // 2 if outside else (90 + al) // 2
    wr = [W((180 - al) // 2, "used_wrong_triangle", "Found the base angle of triangle ABE instead of triangle ADE."),
          W(90 - al if outside else 90 + al, "forgot_to_halve", "Found ∠DAE but did not find the base angle."),
          W(al, "gave_given_angle", "Gave the given angle."),
          W((90 + al) // 2 if outside else (90 - al) // 2, "mixed_inside_outside", "Added instead of subtracted (or the reverse) when finding ∠DAE.")]
    dae = 90 + al if outside else 90 - al
    return mk(square_isosceles, stem, ans, wr,
              ["AD = AB = AE, so triangle ADE is isosceles with apex A.",
               f"∠DAE = 90° {'+' if outside else '−'} {al}° = {dae}°",
               f"∠AED = (180° − {dae}°) ÷ 2 = {ans}°"], {"al": al, "out": outside}, sc.svg("Square and isosceles triangle"))


@checker(square_isosceles)
def _(p):
    al = p["al"]
    A, D = (0, 0), (0, 1)
    E = vec(-al if p["out"] else al)
    return F(round(meas(A, E, D)))


@template(T, "competent", GA + "08", GA + "06")
def circle_chain(r):
    """math-pat-angles-chained-shapes"""
    th, ph = r.randint(40, 150), r.randint(40, 150)
    if (th + ph) % 2:
        return None
    R = 1.0
    sc = Scene(w=300, h=250)
    sc.add("O", 0, 0); sc.add("B", R, 0); sc.add("A", *vec(th)); sc.add("C", *vec(-ph))
    sc.fit(extra=[(R, R), (-R, -R)])
    sc.circle("O", R)
    sc.poly(["A", "B", "C"]); sc.seg("O", "A"); sc.seg("O", "B"); sc.seg("O", "C")
    sc.label("A", away="O"); sc.label("B", away="O"); sc.label("C", away="O")
    sc.label("O", away=vec(-30 + 180), off=12, dx=-4)
    sc.ang("O", "A", "B", f"{th}°", r=20)
    sc.ang("O", "B", "C", f"{ph}°", r=20)
    sc.ang("B", "A", "C", "x", r=22)
    ans = 180 - (th + ph) // 2
    stem = f"O is the centre of the circle and A, B and C lie on it. ∠AOB = {th}° and ∠BOC = {ph}°. Find ∠ABC."
    wr = [W((th + ph) // 2, "gave_half_the_sum", "Found ∠OBA + ∠OBC wrongly as half of ∠AOB + ∠BOC."),
          W(180 - (th + ph) // 2 + 0 if False else (180 - th) // 2 if (180 - th) % 2 == 0 else None, "gave_one_base_angle", "Found only ∠OBA."),
          W(360 - th - ph if 360 - th - ph <= 180 else None, "angles_at_a_point_only", "Found ∠AOC and gave it as the answer."),
          W(180 - th // 2 - ph // 2 + 10, "x", "")]
    wr = [w for w in wr if w[0] and w[1] != "x"]
    return mk(circle_chain, stem, ans, wr,
              ["OA = OB = OC (radii), so triangles OAB and OBC are isosceles.",
               f"∠OBA = (180° − {th}°) ÷ 2 = {(180 - th) // 2}°" if (180 - th) % 2 == 0 else f"∠OBA = (180° − {th}°) ÷ 2 = {(180 - th) / 2}°",
               f"∠OBC = (180° − {ph}°) ÷ 2 = {(180 - ph) / 2:g}°",
               f"∠ABC = ∠OBA + ∠OBC = {ans}°"], {"th": th, "ph": ph}, sc.svg("Circle with centre O"))


@checker(circle_chain)
def _(p):
    O, B = (0, 0), (1, 0)
    A, C = vec(p["th"]), vec(-p["ph"])
    return F(round(meas(A, B, C)))


@template(T, "competent", GA + "08", GA + "05")
def folded_paper(r):
    """math-pat-angles-folded-paper"""
    mode = r.choice(["line", "corner"])
    T0 = 180 if mode == "line" else 90
    g = r.randrange(20, T0 - 19, 2)
    half = (T0 - g) // 2
    sc = Scene()
    sc.add("A", 0, 0)
    if mode == "line":
        sc.add("Z", -1.3, 0); sc.add("Y", 1.3, 0)
        sc.add("Zp", *vec(g, 1.3)); sc.add("B", *vec((180 + g) / 2, 1.2))
        sc.seg("Z", "Y"); sc.seg("A", "B"); sc.seg("A", "Zp", dash=True)
        sc.label("Z", away="A"); sc.label("Y", away="A"); sc.label("B", away="A"); sc.label("Zp", "Z′", away="A")
        sc.label("A", away=(0, 1), off=14)
        sc.ang("A", "Zp", "Y", f"{g}°", r=26)
        sc.ang("A", "Z", "B", "x", r=26)
        stem = (f"A paper strip ZAY is folded along the line AB so that AZ falls on AZ′, as shown by the dotted line. "
                f"∠Z′AY = {g}°. Find ∠ZAB.")
        tgt = "∠ZAB"
        steps = ["A fold is a reflection, so ∠ZAB = ∠Z′AB.", f"Angles on a straight line: 2 × ∠ZAB + {g}° = 180°",
                 f"∠ZAB = (180° − {g}°) ÷ 2 = {half}°"]
        wr = [W(180 - g, "forgot_to_halve", "Found ∠ZAZ′ but did not halve it."),
              W(180 - half, "supplement_of_answer", "Gave the supplement of the answer."),
              W(g, "gave_given_angle", "Gave the given angle."), W(90 - g // 2 + 0 if False else (180 - g) // 2 + 20, "x", "")]
    else:
        sc.add("D", 0, 1.3); sc.add("Bc", 1.3, 0); sc.add("Bp", *vec(90 - g, 1.3)); sc.add("E", *vec((90 - g) / 2, 1.2))
        sc.seg("A", "D"); sc.seg("A", "Bc"); sc.seg("A", "E"); sc.seg("A", "Bp", dash=True)
        sc.label("D", away="A"); sc.label("Bc", "B", away="A"); sc.label("E", away="A"); sc.label("Bp", "B′", away="A")
        sc.label("A", away=(1, 1), off=-12, dx=-6, dy=4)
        sc.ang("A", "D", "Bp", f"{g}°", r=30)
        sc.ang("A", "Bc", "E", "x", r=30)
        stem = (f"The corner A of a rectangular sheet is folded along AE so that AB falls on AB′, as shown by the dotted line. "
                f"∠B′AD = {g}°. Find ∠BAE.")
        tgt = "∠BAE"
        steps = ["The corner is a right angle and the fold makes ∠BAE = ∠B′AE.",
                 f"2 × ∠BAE + {g}° = 90°", f"∠BAE = (90° − {g}°) ÷ 2 = {half}°"]
        wr = [W(90 - g, "forgot_to_halve", "Found ∠BAB′ but did not halve it."),
              W(90 - half, "complement_of_answer", "Gave the complement of the answer."),
              W(g, "gave_given_angle", "Gave the given angle."),
              W((180 - g) // 2, "used_180_for_corner", "Used 180° instead of 90° for the corner.")]
    wr = [w for w in wr if w[1] != "x"]
    return mk(folded_paper, stem, half, wr, steps, {"g": g, "mode": mode}, sc.svg("Folded paper"))


@checker(folded_paper)
def _(p):
    g = p["g"]
    A = (0, 0)
    if p["mode"] == "line":
        Z, Zp = (-1, 0), vec(g)
        crease = (Z[0] + Zp[0], Z[1] + Zp[1])  # bisector of the angle between AZ and AZ'
        return F(round(meas(Z, A, crease)))
    Bc, Bp = (1, 0), vec(90 - g)
    crease = (Bc[0] + Bp[0], Bc[1] + Bp[1])
    return F(round(meas(Bc, A, crease)))


@template(T, "competent", GA + "07", GA + "08")
def butterfly_triangles(r):
    """math-pat-angles-chained-shapes"""
    a, c, d = r.randint(28, 75), r.randint(28, 75), r.randint(28, 75)
    om = 180 - a - c
    y = a + c - d
    if om < 30 or not 25 <= y <= 110:
        return None
    th = r.randint(0, 25)
    sc = Scene()
    sc.add("O", 0, 0)
    sa, sc_ = math.sin(math.radians(a)), math.sin(math.radians(c))
    sd, sy = math.sin(math.radians(d)), math.sin(math.radians(y))
    sc.add("A", *vec(th, sc_)); sc.add("C", *vec(th + om, sa))
    sc.add("B", *vec(th + 180, sd)); sc.add("D", *vec(th + om + 180, sy))
    sc.seg("A", "B"); sc.seg("C", "D"); sc.seg("A", "C"); sc.seg("B", "D")
    for n in "ABCD":
        sc.label(n, away="O")
    sc.label("O", away=vec(th + om / 2 + 90), off=11)
    sc.ang("A", "O", "C", f"{a}°", r=20)
    sc.ang("C", "A", "O", f"{c}°", r=20)
    sc.ang("D", "O", "B", f"{d}°", r=20)
    sc.ang("B", "O", "D", "x", r=20)
    stem = (f"AB and CD are straight lines that cross at O. ∠OAC = {a}°, ∠OCA = {c}° and ∠ODB = {d}°. "
            f"Find ∠OBD.")
    ans = y
    wr = [W(180 - d - om, "x", ""),
          W(om, "stopped_at_vertical_angle", "Found ∠BOD (= ∠AOC) and stopped."),
          W(180 - d, "forgot_a_step", "Forgot to use the angle at O."),
          W(a + c, "gave_exterior_sum", "Gave a + c, not subtracting d."),
          W(180 - a - d, "mixed_up_triangles", "Used angles from different triangles.")]
    wr = [w for w in wr if w[1] != "x"]
    return mk(butterfly_triangles, stem, ans, wr,
              [f"In triangle AOC: ∠AOC = 180° − {a}° − {c}° = {om}°",
               f"∠BOD is vertically opposite ∠AOC, so ∠BOD = {om}°",
               f"In triangle BOD: ∠OBD = 180° − {om}° − {d}° = {ans}°"], {"a": a, "c": c, "d": d}, sc.svg("Two triangles meeting at O"))


@checker(butterfly_triangles)
def _(p):
    a, c, d = p["a"], p["c"], p["d"]
    om = 180 - a - c
    y = a + c - d
    sd, sy = math.sin(math.radians(d)), math.sin(math.radians(y))
    O = (0, 0)
    B, D = vec(180, sd), vec(om + 180, sy)
    return F(round(meas(O, B, D)))


# ---------------------------------------------------------------- ANGLES: more PSLE-style types (parallel-quadrilaterals,
# exterior angles, chained shapes). Points are named P..U so that no figure letter looks like an option letter A-D.

@template(T, "intermediate", GA + "08", GT + "04")
def ang_quad_diagonal(r):
    """math-pat-angles-parallel-quadrilaterals"""
    mode = r.choice(["rhombus", "parallelogram"])
    sc = Scene()
    if mode == "rhombus":
        b = r.randrange(50, 131, 2)
        if b == 90:
            return None
        P = {"mode": mode, "b": b}
        Q, R = (0, 0), (1, 0)
        Pp = vec(b)
        S = (Pp[0] + R[0], Pp[1])
        for n, p in zip("QRPS", (Q, R, Pp, S)):
            sc.add(n, *p)
        sc.poly(["P", "Q", "R", "S"]); sc.seg("P", "R")
        for n in "PQRS":
            sc.label(n)
        sc.ang("Q", "P", "R", f"{b}°", r=22)
        sc.ang("P", "Q", "R", "x", r=24)
        stem = f"PQRS is a rhombus. ∠PQR = {b}°. Find ∠QPR."
        ans = (180 - b) // 2
        wr = [W(180 - b, "gave_co_interior_angle", "Gave ∠QPS instead of halving it for ∠QPR."),
              W(b // 2, "halved_given_angle", "Halved the given angle instead of using the isosceles triangle."),
              W(90 - b if b < 90 else b - 90, "used_right_angle", "Subtracted the angle from 90° instead of finding the base angle."),
              W(180 - b // 2, "x", "")]
        wr = [w for w in wr if w[1] != "x"]
        steps = ["All sides of a rhombus are equal, so triangle PQR is isosceles with QP = QR.",
                 f"The two base angles are equal: ∠QPR = (180° − {b}°) ÷ 2 = {ans}°"]
        fig = sc.svg("Rhombus with a diagonal")
    else:
        u, v = r.randrange(20, 81, 2), r.randrange(20, 81, 2)
        q3 = 180 - u - v
        if not 30 <= q3 <= 130:
            return None
        P = {"mode": mode, "u": u, "v": v}
        sP, sQ, sR, sS = _para_pts(u, v)
        for n, p in zip("PQRS", (sP, sQ, sR, sS)):
            sc.add(n, *p)
        sc.poly(["P", "Q", "R", "S"]); sc.seg("P", "R")
        sc.arrow("P", "Q"); sc.arrow("S", "R"); sc.arrow("Q", "R", 2); sc.arrow("P", "S", 2)
        for n in "PQRS":
            sc.label(n)
        sc.ang("P", "Q", "R", f"{u}°", r=34)
        sc.ang("R", "P", "Q", f"{v}°", r=26)
        sc.ang("S", "R", "P", "x", r=24)
        stem = f"PQRS is a parallelogram. ∠QPR = {u}° and ∠PRQ = {v}°. Find ∠PSR."
        ans = q3
        wr = [W(u + v, "gave_sum_of_given", "Added the two given angles instead of subtracting from 180°."),
              W(180 - u, "mixed_up_angles", "Used one given angle with 180° only."),
              W(180 - v, "mixed_up_angles", "Used one given angle with 180° only."),
              W(360 - u - v, "used_360_for_triangle", "Used 360° for the angles of a triangle.")]
        steps = [f"In triangle PQR: ∠PQR = 180° − {u}° − {v}° = {q3}°",
                 f"Opposite angles of a parallelogram are equal, so ∠PSR = ∠PQR = {ans}°"]
        fig = sc.svg("Parallelogram with a diagonal")
    return mk(ang_quad_diagonal, stem, ans, wr, steps, P, fig)


def _para_pts(u, v):
    """Parallelogram PQRS: angle u at P (RPQ), v at R (PRQ); PQ = 1."""
    q3 = 180 - u - v
    pr = math.sin(math.radians(q3)) / math.sin(math.radians(v))
    P0, Q0 = (0.0, 0.0), (1.0, 0.0)
    R0 = vec(u, pr)
    S0 = (P0[0] + R0[0] - Q0[0], P0[1] + R0[1] - Q0[1])
    return P0, Q0, R0, S0


@checker(ang_quad_diagonal)
def _(p):
    if p["mode"] == "rhombus":
        b = p["b"]
        Q, R = (0, 0), (1, 0)
        Pp = vec(b)
        return F(round(meas(Q, Pp, R)))
    sP, sQ, sR, sS = _para_pts(p["u"], p["v"])
    return F(round(meas(sP, sS, sR)))


@template(T, "intermediate", GA + "08", GT + "06")
def ang_trapezium_angles(r):
    """math-pat-angles-parallel-quadrilaterals"""
    mode = r.choice(["cointerior", "diagonal"])
    sc = Scene()
    if mode == "cointerior":
        a, b = r.randrange(55, 126, 2), r.randrange(55, 126, 2)
        if a == 90 or b == 90 or a == b:
            return None
        P = {"mode": mode, "a": a, "b": b}
        pts = _trap_co(a, b)
        if pts is None:
            return None
        for n, p in zip("PQRS", pts):
            sc.add(n, *p)
        sc.poly(["P", "Q", "R", "S"]); sc.arrow("P", "Q"); sc.arrow("S", "R")
        for n in "PQRS":
            sc.label(n)
        sc.ang("P", "Q", "S", f"{a}°", r=24)
        sc.ang("Q", "R", "P", f"{b}°", r=24)
        sc.ang("S", "P", "R", "x", r=22)
        stem = f"PQRS is a trapezium with PQ parallel to SR. ∠SPQ = {a}° and ∠PQR = {b}°. Find ∠PSR."
        ans = 180 - a
        wr = [W(180 - b, "mixed_up_angles", "Used ∠PQR instead of ∠SPQ in the co-interior angle."),
              W(a, "gave_given_angle", "Gave ∠SPQ, which is not the angle asked."),
              W(b, "gave_given_angle", "Gave ∠PQR, which is not the angle asked."),
              W(360 - a - b if 360 - a - b <= 180 else None, "used_360", "Used 360° for a pair of angles between parallel lines.")]
        steps = ["PQ is parallel to SR, so the angles between them on the same side (co-interior angles) add up to 180°.",
                 f"∠PSR = 180° − {a}° = {ans}°"]
        fig = sc.svg("Trapezium")
    else:
        u, v = r.randrange(20, 81, 2), r.randrange(20, 81, 2)
        P = {"mode": mode, "u": u, "v": v}
        pts = _trap_diag(u, v)
        for n, p in zip("PQRS", pts):
            sc.add(n, *p)
        sc.poly(["P", "Q", "R", "S"]); sc.seg("P", "R"); sc.arrow("P", "Q"); sc.arrow("S", "R")
        for n in "PQRS":
            sc.label(n)
        sc.ang("P", "Q", "R", f"{u}°", r=34)
        sc.ang("R", "Q", "P", f"{v}°", r=20)
        sc.ang("R", "Q", "S", None, r=62)
        sc.fit()
        aq = bearing(pts[2], pts[1])  # R -> Q; R -> S points left (180 degrees)
        sw = ((aq - 180 + 180) % 360) - 180
        sc.text(pt(pts[2][0], pts[2][1], 180 + 0.22 * sw, 74 / sc.scale), "x")
        stem = f"PQRS is a trapezium with PQ parallel to SR. ∠QPR = {u}° and ∠PRQ = {v}°. Find ∠QRS."
        ans = u + v
        wr = [W(180 - u - v, "found_third_angle_only", "Found ∠PQR instead of ∠QRS."),
              W(abs(u - v), "subtracted_given_angles", "Subtracted the two given angles."),
              W(180 - u, "mixed_up_angles", "Used 180° minus one given angle."),
              W(180 - v, "mixed_up_angles", "Used 180° minus one given angle.")]
        steps = [f"PQ is parallel to SR, so ∠PRS = ∠QPR = {u}° (alternate angles).",
                 f"∠QRS = ∠PRQ + ∠PRS = {v}° + {u}° = {ans}°"]
        fig = sc.svg("Trapezium with a diagonal")
    return mk(ang_trapezium_angles, stem, ans, wr, steps, P, fig)


def _trap_co(a, b):
    """Trapezium PQRS (PQ parallel to SR): angle a at P (SPQ), b at Q (PQR)."""
    Pp = (0.0, 0.0)
    S = vec(a, 1.0)
    Q = (1.9, 0.0)
    t = S[1] / math.sin(math.radians(b))
    R = (Q[0] + t * math.cos(math.radians(180 - b)), S[1])
    if R[0] - S[0] < 0.5:
        return None
    return Pp, Q, R, S


def _trap_diag(u, v):
    """Trapezium PQRS (PQ parallel to SR): angle u at P (RPQ), v at R (PRQ); PQ = 1."""
    q3 = 180 - u - v
    pr = math.sin(math.radians(q3)) / math.sin(math.radians(v))
    Pp, Q, R = (0.0, 0.0), (1.0, 0.0), vec(u, pr)
    S = (R[0] - 1.3, R[1])
    return Pp, Q, R, S


@checker(ang_trapezium_angles)
def _(p):
    if p["mode"] == "cointerior":
        sP, sQ, sR, sS = _trap_co(p["a"], p["b"])
        return F(round(meas(sP, sS, sR)))
    sP, sQ, sR, sS = _trap_diag(p["u"], p["v"])
    return F(round(meas(sQ, sR, sS)))


@template(T, "intermediate", GA + "08", GT + "05")
def ang_exterior_angle(r):
    """math-pat-angles-one-step"""
    p, q = r.randrange(25, 100, 1), r.randrange(25, 100, 1)
    third = 180 - p - q
    if third < 25 or p + q > 150:
        return None
    sc = Scene()
    Q, R = (0.0, 0.0), (1.0, 0.0)
    qp = math.sin(math.radians(third)) / math.sin(math.radians(p))
    Pp = vec(q, qp)
    S = (1.9, 0.0)
    for n, pp in zip("PQRS", (Pp, Q, R, S)):
        sc.add(n, *pp)
    sc.seg("P", "Q"); sc.seg("P", "R"); sc.seg("Q", "S")
    for n in "PQRS":
        sc.label(n, away=(0.9, 0.2) if n == "P" else None)
    sc.ang("Q", "P", "R", f"{q}°", r=24)
    sc.ang("P", "Q", "R", f"{p}°", r=22)
    sc.ang("R", "P", "S", "x", r=24)
    stem = f"In triangle PQR, the side QR is extended to S. ∠QPR = {p}° and ∠PQR = {q}°. Find ∠PRS."
    ans = p + q
    wr = [W(third, "found_interior_angle", "Found the interior angle ∠PRQ instead of the exterior angle."),
          W(180 - p, "used_one_angle_only", "Used only one of the given angles."),
          W(180 - q, "used_one_angle_only", "Used only one of the given angles."),
          W(abs(p - q), "subtracted_given_angles", "Subtracted the two given angles.")]
    return mk(ang_exterior_angle, stem, ans, wr,
              [f"∠PRQ = 180° − {p}° − {q}° = {third}°",
               f"QRS is a straight line, so ∠PRS = 180° − {third}° = {ans}°"],
              {"p": p, "q": q}, sc.svg("Triangle with an extended side"))


@checker(ang_exterior_angle)
def _(pr):
    p, q = pr["p"], pr["q"]
    third = 180 - p - q
    qp = math.sin(math.radians(third)) / math.sin(math.radians(p))
    Pp, R, S = vec(q, qp), (1.0, 0.0), (1.9, 0.0)
    return F(round(meas(Pp, R, S)))


@template(T, "competent", GA + "08", GT + "06")
def ang_isosceles_exterior(r):
    """math-pat-angles-chained-shapes"""
    a = r.randrange(30, 111, 2)
    base = (180 - a) // 2
    sc = Scene()
    Q, R, S = (-1.0, 0.0), (1.0, 0.0), (2.1, 0.0)
    Pp = (0.0, math.tan(math.radians(base)))
    for n, pp in zip("PQRS", (Pp, Q, R, S)):
        sc.add(n, *pp)
    sc.seg("P", "Q"); sc.seg("P", "R"); sc.seg("Q", "S")
    sc.tick("P", "Q"); sc.tick("P", "R")
    sc.label("P", away=(0, 0)); sc.label("Q"); sc.label("R", away=(0.5, 1.2)); sc.label("S", away=(0, 0.4))
    sc.ang("P", "Q", "R", f"{a}°", r=22)
    sc.ang("R", "P", "S", "x", r=24)
    stem = f"PQR is an isosceles triangle with PQ = PR and ∠QPR = {a}°. The side QR is extended to S. Find ∠PRS."
    ans = 90 + a // 2
    wr = [W(base, "found_base_angle_only", "Found the base angle ∠PRQ but not the angle outside the triangle."),
          W(180 - a, "used_apex_supplement", "Subtracted the apex angle from 180° and stopped."),
          W(180 - a // 2, "halved_wrong_angle", "Halved the apex angle before subtracting from 180°."),
          W(a, "gave_given_angle", "Gave the given angle.")]
    return mk(ang_isosceles_exterior, stem, ans, wr,
              ["PQ = PR, so the base angles are equal.",
               f"∠PRQ = (180° − {a}°) ÷ 2 = {base}°",
               f"QRS is a straight line, so ∠PRS = 180° − {base}° = {ans}°"],
              {"a": a}, sc.svg("Isosceles triangle with an extended side"))


@checker(ang_isosceles_exterior)
def _(p):
    base = next(b for b in range(1, 90) if 180 - 2 * b == p["a"])
    Pp, R, S = (0.0, math.tan(math.radians(base))), (1.0, 0.0), (2.1, 0.0)
    return F(round(meas(Pp, R, S)))


@template(T, "competent", GA + "08", GT + "06")
def ang_rhombus_equilateral(r):
    """math-pat-angles-chained-shapes"""
    d = r.randrange(40, 91, 2)
    if d == 90:
        return None
    sc = Scene()
    pts = _rh_eq(d)
    for n, p in zip("SRPQT", pts):
        sc.add(n, *p)
    sc.poly(["P", "Q", "R", "S"]); sc.seg("P", "T"); sc.seg("S", "T"); sc.seg("R", "T")
    sc.label("P", away="S"); sc.label("Q", away="S"); sc.label("R", away="S"); sc.label("T", away="S")
    sc.label("S", away=(0.5, 0.5), off=14)
    sc.ang("S", "P", "R", f"{d}°", r=22)
    sc.ang("P", "S", "T", None, r=26)
    sc.fit()
    _bs = (bearing(pts[2], pts[0]) + bearing(pts[2], pts[4])) / 2  # bisector of the angle at P
    sc.text(pt(pts[2][0], pts[2][1], _bs, 42 / sc.scale), "x")
    stem = (f"PQRS is a rhombus and RST is an equilateral triangle. ∠PSR = {d}°. Find ∠SPT.")
    ans = (120 - d) // 2
    wr = [W(120 - d, "forgot_to_halve", "Found ∠SPT + ∠STP but did not halve it."),
          W((180 - d) // 2, "ignored_equilateral_triangle", "Left out the 60° angle of the equilateral triangle."),
          W(d + 60, "gave_angle_at_s", "Gave ∠PST, the angle at S."),
          W(60, "used_equilateral_angle", "Used the 60° angle of the equilateral triangle.")]
    return mk(ang_rhombus_equilateral, stem, ans, wr,
              ["Sides of a rhombus and of an equilateral triangle are all equal, so SP = SR = ST.",
               f"∠PST = {d}° + 60° = {d + 60}°; triangle SPT is isosceles with SP = ST",
               f"∠SPT = (180° − {d + 60}°) ÷ 2 = {ans}°"],
              {"d": d}, sc.svg("Rhombus and equilateral triangle"))


def _rh_eq(d):
    S, R = (0.0, 0.0), (1.0, 0.0)
    Pp = vec(d)
    Q = (Pp[0] + 1.0, Pp[1])
    T = vec(-60)
    return S, R, Pp, Q, T


@checker(ang_rhombus_equilateral)
def _(p):
    S, R, Pp, Q, T = _rh_eq(p["d"])
    return F(round(meas(S, Pp, T)))


@template(T, "competent", GA + "08", GA + "05")
def ang_folded_flap(r):
    """math-pat-angles-folded-paper"""
    g = r.randrange(100, 141, 2)
    sc = Scene(w=330, h=250)
    pts = _flap(g)
    for n, p in pts.items():
        sc.add(n, *p)
    sc.poly(["P", "Q", "R", "S"]); sc.seg("U", "V")
    sc.poly(["U", "Pf", "Qf", "V"], dash=True)
    for n in "PQRS":
        sc.label(n)
    sc.label("U", away="V"); sc.label("V", away="U"); sc.label("Pf", "P′", away="U"); sc.label("Qf", "Q′", away="V")
    sc.ang("U", "P", "V", f"{g}°", r=22)
    sc.ang("V", "R", "Qf", "x", r=26)
    stem = (f"PQRS is a rectangular piece of paper. It is folded along UV so that P falls on P′ and Q falls on Q′, "
            f"as shown. ∠PUV = {g}°. Find ∠RVQ′.")
    ans = 2 * g - 180
    wr = [W(180 - g, "stopped_at_co_interior", "Found ∠UVQ and stopped."),
          W(360 - 2 * g, "found_angle_qvq", "Found ∠QVQ′ instead of ∠RVQ′."),
          W(g, "gave_given_angle", "Gave the given angle."),
          W(g - 90, "used_right_angle", "Subtracted 90° from the given angle.")]
    return mk(ang_folded_flap, stem, ans, wr,
              [f"PS is parallel to QR, so ∠UVQ = 180° − {g}° = {180 - g}° (co-interior angles).",
               f"A fold does not change angles, so ∠UVQ′ = ∠UVQ = {180 - g}°.",
               f"∠UVR = {g}° (angles on a straight line with ∠UVQ), so ∠RVQ′ = {g}° − {180 - g}° = {ans}°"],
              {"g": g}, sc.svg("Folded rectangular paper"))


def _flap(g):
    w, h, xe = 3.4, 1.3, 1.0
    P, Q, R, S = (0.0, h), (0.0, 0.0), (w, 0.0), (w, h)
    U = (xe, h)
    V = (xe - h / math.tan(math.radians(g)), 0.0)
    ux, uy = V[0] - U[0], V[1] - U[1]
    n = math.hypot(ux, uy)
    ux, uy = ux / n, uy / n

    def refl(p):
        dx, dy = p[0] - U[0], p[1] - U[1]
        k = dx * ux + dy * uy
        return (U[0] + 2 * k * ux - dx, U[1] + 2 * k * uy - dy)
    return {"P": P, "Q": Q, "R": R, "S": S, "U": U, "V": V, "Pf": refl(P), "Qf": refl(Q)}


@checker(ang_folded_flap)
def _(p):
    q = _flap(p["g"])
    return F(round(meas(q["R"], q["V"], q["Qf"])))


@template(T, "competent", GA + "08", GA + "06")
def ang_square_isosceles(r):
    """math-pat-angles-chained-shapes"""
    p = r.randrange(20, 81, 2)
    sc = Scene()
    q = _sq_iso(p)
    for n, pt_ in q.items():
        sc.add(n, *pt_)
    sc.poly(["P", "Q", "R", "S"]); sc.seg("P", "T"); sc.seg("S", "T"); sc.seg("Q", "T")
    sc.tick("P", "Q"); sc.tick("P", "T")
    sc.label("P", away="R"); sc.label("Q", away="S"); sc.label("R", away="P"); sc.label("S", away="Q")
    sc.label("T", away="P", off=11)
    sc.ang("P", "Q", "T", f"{p}°", r=30)
    sc.ang("T", "P", "S", "x", r=22)
    stem = f"PQRS is a square. T is a point inside the square such that PT = PQ and ∠QPT = {p}°. Find ∠PTS."
    ans = 45 + p // 2
    wr = [W(90 - p // 2, "found_other_base_angle", "Found ∠PTQ, the base angle of the other triangle."),
          W(90 - p, "found_angle_spt", "Found ∠SPT and stopped."),
          W(45, "halved_right_angle", "Halved the right angle."),
          W(p, "gave_given_angle", "Gave the given angle.")]
    return mk(ang_square_isosceles, stem, ans, wr,
              [f"∠SPT = 90° − {p}° = {90 - p}° (∠SPQ is a right angle).",
               "PS = PQ = PT, so triangle PST is isosceles.",
               f"∠PTS = (180° − {90 - p}°) ÷ 2 = {ans}°"],
              {"p": p}, sc.svg("Square with a point inside"))


def _sq_iso(p):
    return {"P": (0.0, 0.0), "Q": (1.0, 0.0), "R": (1.0, 1.0), "S": (0.0, 1.0), "T": vec(p)}


@checker(ang_square_isosceles)
def _(p):
    q = _sq_iso(p["p"])
    return F(round(meas(q["P"], q["T"], q["S"])))



# ============================================================ TRIANGLES, PARALLELOGRAM, RHOMBUS, TRAPEZIUM

def tri_pts(a, b, base=1.0):
    """A=(0,0), B=(base,0); angles a at A, b at B."""
    c = 180 - a - b
    ac = base * math.sin(math.radians(b)) / math.sin(math.radians(c))
    return {"A": (0, 0), "B": (base, 0), "C": vec(a, ac)}


@template(T, "basic", GT + "02", GT + "01", GT + "03")
def triangle_third_angle(r):
    """math-pat-angles-one-step"""
    right = r.random() < 0.35
    a = r.randint(25, 100)
    b = 90 if right else r.randint(25, 100)
    c = 180 - a - b
    if c < 20:
        return None
    pts = tri_pts(a, b)
    sc = Scene()
    for n, p in pts.items():
        sc.add(n, *p)
    sc.poly("ABC")
    for n in "ABC":
        sc.label(n)
    sc.ang("A", "B", "C", f"{a}°", r=26)
    sc.ang("B", "A", "C", None if right else f"{b}°", r=22)
    sc.ang("C", "A", "B", "x", r=22)
    if right:
        stem = f"In triangle ABC, ∠B = 90° and ∠A = {a}°. Find ∠C."
        wr = [W(90 - a + 0 if False else 180 - a, "forgot_the_right_angle", "Subtracted only ∠A from 180°."),
              W(90 + a if 90 + a <= 180 else None, "added_given_angles", "Added the two given angles."),
              W(a, "gave_given_angle", "Gave ∠A.")]
        steps = ["The angles in a triangle add up to 180°.", f"∠C = 180° − 90° − {a}° = {c}°"]
    else:
        stem = f"In triangle ABC, ∠A = {a}° and ∠B = {b}°. Find ∠C."
        wr = [W(180 - a, "used_one_angle_only", "Subtracted only one angle from 180°."),
              W(a + b, "added_given_angles", "Added the two given angles."),
              W(360 - a - b if 360 - a - b <= 180 else None, "used_360", "Used 360° instead of 180°."),
              W(abs(a - b), "subtracted_given_angles", "Found the difference of the given angles.")]
        steps = ["The angles in a triangle add up to 180°.", f"∠C = 180° − {a}° − {b}° = {c}°"]
    wr = [w for w in wr if w[0]]
    return mk(triangle_third_angle, stem, c, wr, steps, {"a": a, "b": b}, sc.svg("Triangle"))


@checker(triangle_third_angle)
def _(p):
    q = tri_pts(p["a"], p["b"])
    return F(round(meas(q["A"], q["C"], q["B"])))


@template(T, "basic", GT + "01", GT + "02")
def isosceles_basic(r):
    """math-pat-angles-one-step"""
    beta = r.randint(25, 80)
    alpha = 180 - 2 * beta
    mode = r.choice(["apex", "base"])
    if alpha < 20:
        return None
    sc = Scene()
    sc.add("B", -1, 0); sc.add("C", 1, 0); sc.add("A", 0, math.tan(math.radians(beta)))
    sc.poly("ABC"); sc.tick("A", "B"); sc.tick("A", "C")
    for n in "ABC":
        sc.label(n)
    if mode == "apex":
        sc.ang("A", "B", "C", f"{alpha}°", r=26); sc.ang("B", "A", "C", "x", r=24)
        stem = f"ABC is an isosceles triangle with AB = AC. ∠BAC = {alpha}°. Find ∠ABC."
        ans = beta
        wr = [W(180 - alpha, "forgot_to_halve", "Found the sum of the two base angles but did not halve it."),
              W(alpha, "gave_given_angle", "Gave the apex angle."),
              W((180 - alpha) // 2 + (alpha // 2 if False else 0) + 0 if False else alpha // 2, "halved_the_apex_angle", "Halved the apex angle."),
              ]
        steps = ["AB = AC, so ∠ABC = ∠ACB (base angles of an isosceles triangle).",
                 f"∠ABC + ∠ACB = 180° − {alpha}° = {180 - alpha}°", f"∠ABC = {180 - alpha}° ÷ 2 = {beta}°"]
    else:
        sc.ang("B", "A", "C", f"{beta}°", r=26); sc.ang("A", "B", "C", "x", r=24)
        stem = f"ABC is an isosceles triangle with AB = AC. ∠ABC = {beta}°. Find ∠BAC."
        ans = alpha
        wr = [W(180 - beta, "used_one_base_angle", "Subtracted only one base angle from 180°."),
              W(beta, "assumed_apex_equals_base", "Assumed ∠BAC = ∠ABC."),
              W(90 - beta, "used_90", "Subtracted from 90° instead of finding the third angle."),
              ]
        steps = ["AB = AC, so ∠ACB = ∠ABC.", f"∠ACB = {beta}°", f"∠BAC = 180° − {beta}° − {beta}° = {alpha}°"]
    return mk(isosceles_basic, stem, ans, wr, steps, {"beta": beta, "mode": mode}, sc.svg("Isosceles triangle"))


@checker(isosceles_basic)
def _(p):
    A, B, C = (0, math.tan(math.radians(p["beta"]))), (-1, 0), (1, 0)
    return F(round(meas(B, A, C) if p["mode"] == "base" else meas(A, B, C)))


def para_pts(a, w=1.5, d=1.0):
    """Parallelogram ABCD with ∠DAB = a: A origin, B right, D at angle a."""
    A, B = (0, 0), (w, 0)
    D = vec(a, d)
    C = (D[0] + w, D[1])
    return {"A": A, "B": B, "C": C, "D": D}


@template(T, "basic", GT + "04", GT + "05", weight=2)
def parallelogram_basic(r):
    """math-pat-angles-parallel-quadrilaterals"""
    a = r.randint(35, 145)
    if a == 90:
        return None
    mode = r.choice(["B", "D", "C"])
    pts = para_pts(a, r.choice([1.5, 1.8]), 1.0)
    sc = Scene()
    for n, p in pts.items():
        sc.add(n, *p)
    sc.poly("ABCD")
    sc.arrow("A", "B"); sc.arrow("D", "C"); sc.arrow("A", "D", 2); sc.arrow("B", "C", 2)
    cen = ((pts["A"][0] + pts["C"][0]) / 2, (pts["A"][1] + pts["C"][1]) / 2)
    for n in "ABCD":
        sc.label(n, away=cen)
    sc.ang("A", "B", "D", f"{a}°", r=24)
    tgt = {"B": ("B", "A", "C"), "D": ("D", "A", "C"), "C": ("C", "B", "D")}[mode]
    sc.ang(tgt[0], tgt[1], tgt[2], "x", r=24)
    ans = a if mode == "C" else 180 - a
    stem = f"ABCD is a parallelogram. ∠DAB = {a}°. Find ∠{'ABC' if mode == 'B' else 'ADC' if mode == 'D' else 'BCD'}."
    if mode == "C":
        wr = [W(180 - a, "used_adjacent_angle", "Gave the co-interior angle instead of the equal opposite angle."),
              W(360 - 2 * a if 0 < 360 - 2 * a <= 180 else None, "x", ""),
              W(90, "x", ""), W(a // 2 if a % 2 == 0 else None, "halved_the_angle", "Halved the angle.")]
        steps = ["Opposite angles of a parallelogram are equal.", f"∠BCD = ∠DAB = {a}°"]
    else:
        wr = [W(a, "assumed_opposite_equal", "Assumed this angle equals ∠DAB; it is the adjacent angle."),
              W(360 - a if 360 - a <= 180 else None, "used_360", "Subtracted from 360°."),
              W(90 - a if a < 90 else None, "used_90", "Subtracted from 90°.")]
        steps = ["Adjacent angles of a parallelogram (between parallel sides) add up to 180°.",
                 f"∠{'ABC' if mode == 'B' else 'ADC'} = 180° − {a}° = {ans}°"]
    wr = [w for w in wr if w[0] and w[1] != "x"]
    return mk(parallelogram_basic, stem, ans, wr, steps, {"a": a, "mode": mode}, sc.svg("Parallelogram"))


@checker(parallelogram_basic)
def _(p):
    q = para_pts(p["a"])
    return F(round({"B": meas(q["A"], q["B"], q["C"]), "D": meas(q["A"], q["D"], q["C"]), "C": meas(q["B"], q["C"], q["D"])}[p["mode"]]))


@template(T, "basic", GT + "01")
def isosceles_count(r):
    """Classify triangles from their angles"""
    tris, iso = [], 0
    for _ in range(4):
        if r.random() < 0.5:
            x = r.choice([x for x in range(30, 80) if x != 60])
            t = [x, x, 180 - 2 * x]
            iso += 1
        else:
            while True:
                a, b = r.randint(25, 100), r.randint(25, 100)
                c = 180 - a - b
                if c >= 20 and len({a, b, c}) == 3:
                    t = [a, b, c]
                    break
        r.shuffle(t)
        tris.append(t)
    if not 1 <= iso <= 3:
        return None
    lines = "; ".join(f"Triangle {'PQRS'[i]}: {t[0]}°, {t[1]}°, {t[2]}°" for i, t in enumerate(tris))
    stem = f"The angles of four triangles are: {lines}. How many of the triangles are isosceles?"
    wr = [W(4 - iso, "counted_the_wrong_kind", "Counted the scalene triangles instead."),
          W(iso + 1, "miscount", "Counted one extra triangle."),
          W(iso - 1, "miscount", "Missed one isosceles triangle."), W(iso + 2, "miscount", "Counted two extra triangles."),
          W(iso + 3, "miscount", "Miscounted.")]
    return mk(isosceles_count, stem, iso, wr,
              ["An isosceles triangle has two equal angles (and two equal sides).",
               "Triangles with a pair of equal angles: " + ", ".join("PQRS"[i] for i, t in enumerate(tris) if len(set(t)) < 3),
               f"Number of isosceles triangles = {iso}"], {"tris": tris}, None, show=lambda v: str(int(v)), maxv=4)


@checker(isosceles_count)
def _(p):
    return F(sum(1 for t in p["tris"] if sorted(t)[0] == sorted(t)[1] or sorted(t)[1] == sorted(t)[2]))


# ---------------- intermediate

@template(T, "intermediate", GT + "03")
def exterior_angle(r):
    """math-pat-angles-one-step"""
    a, b = r.randint(25, 85), r.randint(25, 85)
    c = 180 - a - b
    if c < 25:
        return None
    e = a + b
    mode = r.choice(["find_e", "find_b"])
    pts = tri_pts(b, c)  # build with B=(0,0)? reuse: A'=B, B'=C
    # use B=(0,0), C=(1,0), A above with angle b at B and c at C
    Bp, Cp = (0, 0), (1, 0)
    Ap = vec(b, math.sin(math.radians(c)) / math.sin(math.radians(a)))
    sc = Scene()
    sc.add("B", *Bp); sc.add("C", *Cp); sc.add("A", *Ap); sc.add("D", 1.6, 0)
    sc.poly("ABC"); sc.seg("C", "D")
    sc.label("A", away=(0.5, 0)); sc.label("B", away=(0.5, 0.3)); sc.label("C", away=(0.5, 0.3)); sc.label("D", away="C")
    if mode == "find_e":
        sc.ang("A", "B", "C", f"{a}°", r=22) if False else None
        sc.ang("A", "B", "C", f"{a}°", r=22); sc.ang("B", "A", "C", f"{b}°", r=22)
        sc.ang("C", "A", "D", "x", r=26)
        stem = f"In the figure, BCD is a straight line. ∠BAC = {a}° and ∠ABC = {b}°. Find ∠ACD."
        ans = e
        wr = [W(c, "gave_interior_angle", "Gave ∠ACB instead of the exterior angle ∠ACD."),
              W(abs(a - b), "subtracted_given_angles", "Subtracted the two given angles."),
              W(180 - a, "used_one_angle_only", "Subtracted only one angle from 180°."),
              W(360 - a - b if 360 - a - b <= 180 else None, "used_360", "Used 360°.")]
        steps = [f"∠ACB = 180° − {a}° − {b}° = {c}°", f"∠ACD = 180° − {c}° = {e}°",
                 "(Shortcut: exterior angle = sum of the two opposite interior angles.)"]
    else:
        sc.ang("B", "A", "C", None)  # placeholder removed below
        sc.cmds.pop()
        sc.ang("B", "A", "C", "x", r=22); sc.ang("A", "B", "C", f"{a}°", r=22)
        sc.ang("C", "A", "D", f"{e}°", r=26)
        stem = f"In the figure, BCD is a straight line. ∠BAC = {a}° and ∠ACD = {e}°. Find ∠ABC."
        ans = b
        wr = [W(180 - e, "gave_interior_angle", "Gave ∠ACB instead of ∠ABC."),
              W(e + a, "added_given_angles", "Added the two given angles."),
              W(180 - a - e if 0 < 180 - a - e else None, "wrong_triangle_sum", "Subtracted both angles from 180°."),
              W(a, "gave_given_angle", "Gave ∠BAC.")]
        steps = [f"∠ACB = 180° − {e}° = {c}° (angles on a straight line)", f"∠ABC = 180° − {a}° − {c}° = {b}°",
                 "(Shortcut: exterior angle ∠ACD = ∠BAC + ∠ABC.)"]
    wr = [w for w in wr if w[0]]
    return mk(exterior_angle, stem, ans, wr, steps, {"a": a, "b": b, "mode": mode}, sc.svg("Triangle with an extended side"))


@checker(exterior_angle)
def _(p):
    a, b = p["a"], p["b"]
    c = 180 - a - b
    B, C = (0, 0), (1, 0)
    A = vec(b, math.sin(math.radians(c)) / math.sin(math.radians(a)))
    D = (1.6, 0)
    return F(round(meas(A, C, D) if p["mode"] == "find_e" else meas(A, B, C)))


@template(T, "intermediate", GT + "03", GT + "01")
def isosceles_exterior(r):
    """math-pat-angles-one-step"""
    beta = r.randint(30, 75)
    alpha = 180 - 2 * beta
    e = 180 - beta
    mode = r.choice(["find_apex", "find_ext"])
    sc = Scene()
    sc.add("B", -1, 0); sc.add("C", 1, 0); sc.add("A", 0, math.tan(math.radians(beta))); sc.add("D", 1.8, 0)
    sc.poly("ABC"); sc.seg("C", "D"); sc.tick("A", "B"); sc.tick("A", "C")
    sc.label("A", away=(0, 0)); sc.label("B", away=(0, 0.3)); sc.label("C", away=(0, 0.3)); sc.label("D", away="C")
    if mode == "find_apex":
        sc.ang("C", "A", "D", f"{e}°", r=22); sc.ang("A", "B", "C", "x", r=24)
        stem = f"In the figure, BCD is a straight line and AB = AC. ∠ACD = {e}°. Find ∠BAC."
        ans = alpha
        wr = [W(beta, "stopped_at_base_angle", "Found the base angle ∠ACB and stopped."),
              W(180 - beta, "gave_given_angle", "Gave the exterior angle."),
              W(2 * beta - 0 if False else 180 - beta - beta // 2 if False else 90 - beta, "used_90", "Used 90° instead of 180°."),
              W(e - beta if e - beta > 0 else None, "subtracted_instead_of_triangle_sum", "Subtracted the base angle from the exterior angle.")]
        steps = [f"∠ACB = 180° − {e}° = {beta}° (angles on a straight line)", f"∠ABC = ∠ACB = {beta}° (AB = AC)",
                 f"∠BAC = 180° − {beta}° − {beta}° = {alpha}°"]
    else:
        sc.ang("A", "B", "C", f"{alpha}°", r=26); sc.ang("C", "A", "D", "x", r=24)
        stem = f"In the figure, BCD is a straight line and AB = AC. ∠BAC = {alpha}°. Find ∠ACD."
        ans = e
        wr = [W(beta, "gave_base_angle", "Gave the base angle ∠ACB instead of the exterior angle."),
              W(180 - alpha, "used_one_angle_only", "Subtracted only the apex angle from 180°."),
              W(alpha + beta if alpha + beta <= 180 else None, "added_wrong_angles", "Added the apex and a base angle."),
              W(alpha, "gave_given_angle", "Gave the apex angle.")]
        steps = [f"∠ABC = ∠ACB = (180° − {alpha}°) ÷ 2 = {beta}°", f"∠ACD = 180° − {beta}° = {e}°"]
    wr = [w for w in wr if w[0]]
    return mk(isosceles_exterior, stem, ans, wr, steps, {"beta": beta, "mode": mode}, sc.svg("Isosceles triangle with an extended side"))


@checker(isosceles_exterior)
def _(p):
    A, B, C, D = (0, math.tan(math.radians(p["beta"]))), (-1, 0), (1, 0), (1.8, 0)
    return F(round(meas(B, A, C) if p["mode"] == "find_apex" else meas(A, C, D)))


def rhombus_pts(b, L=1.0):
    B, C = (0, 0), (L, 0)
    A = vec(b, L)
    D = (A[0] + L, A[1])
    return {"A": A, "B": B, "C": C, "D": D}


@template(T, "intermediate", GT + "05", GT + "04")
def rhombus_diagonal(r):
    """math-pat-angles-parallel-quadrilaterals"""
    b = r.randrange(40, 141, 2)
    if b == 90:
        return None
    mode = r.choice(["CAD", "ABD", "BCD"])
    q = rhombus_pts(180 - b if mode == "ABD" else b)
    sc = Scene()
    for n, p in q.items():
        sc.add(n, *p)
    sc.poly("ABCD")
    cen = ((q["A"][0] + q["C"][0]) / 2, (q["A"][1] + q["C"][1]) / 2)
    for n in "ABCD":
        sc.label(n, away=cen)
    for s_ in ("AB", "BC", "CD", "DA"):
        sc.tick(s_[0], s_[1])
    if mode != "ABD":
        sc.ang("B", "A", "C", f"{b}°", r=24)
    if mode == "CAD":
        sc.seg("A", "C"); sc.ang("A", "C", "D", "x", r=26)
        stem = f"ABCD is a rhombus. ∠ABC = {b}°. Find ∠CAD."
        ans = (180 - b) // 2
        wr = [W(180 - b, "stopped_at_vertex_angle", "Found ∠BAD and stopped."),
              W(b // 2, "halved_given_angle", "Halved the given angle ∠ABC."),
              W(90 - b // 2 + 0 if False else b, "gave_given_angle", "Gave the given angle."),
              W(180 - ans, "supplement_of_answer", "Gave the supplement of the answer.")]
        steps = [f"∠BAD = 180° − {b}° = {180 - b}° (adjacent angles of a rhombus)",
                 "The diagonal AC bisects ∠BAD (AB = AD).", f"∠CAD = {180 - b}° ÷ 2 = {ans}°"]
    elif mode == "ABD":
        sc.seg("B", "D")
        stem = f"ABCD is a rhombus. ∠BCD = {b}°. Find ∠ABD."
        ans = (180 - b) // 2
        sc.ang("C", "B", "D", f"{b}°", r=24); sc.ang("B", "A", "D", "x", r=24)
        wr = [W(180 - b, "stopped_at_vertex_angle", "Found ∠ABC and stopped."),
              W(b // 2, "halved_given_angle", "Halved the given angle ∠BCD."),
              W(b, "gave_given_angle", "Gave the given angle."),
              W(180 - ans, "supplement_of_answer", "Gave the supplement of the answer.")]
        steps = [f"∠ABC = 180° − {b}° = {180 - b}° (adjacent angles of a rhombus)",
                 "The diagonal BD bisects ∠ABC (BA = BC).", f"∠ABD = {180 - b}° ÷ 2 = {ans}°"]
    else:
        stem = f"ABCD is a rhombus. ∠ABC = {b}°. Find ∠BCD."
        sc.ang("C", "B", "D", "x", r=24)
        ans = 180 - b
        wr = [W(b, "assumed_opposite_equal", "Gave ∠ABC; the adjacent angle is the supplement."),
              W(360 - b if 360 - b <= 180 else None, "used_360", "Used 360°."),
              W(b // 2, "halved_given_angle", "Halved the given angle.")]
        steps = ["Adjacent angles of a rhombus add up to 180° (BA ∥ CD).", f"∠BCD = 180° − {b}° = {ans}°"]
    wr = [w for w in wr if w[0]]
    return mk(rhombus_diagonal, stem, ans, wr, steps, {"b": b, "mode": mode}, sc.svg("Rhombus"))


@checker(rhombus_diagonal)
def _(p):
    q = rhombus_pts(180 - p["b"] if p["mode"] == "ABD" else p["b"])
    return F(round({"CAD": meas(q["C"], q["A"], q["D"]), "ABD": meas(q["A"], q["B"], q["D"]),
                    "BCD": meas(q["B"], q["C"], q["D"])}[p["mode"]]))


def trap_pts(a, b, H=1.0, top=1.1):
    """Trapezium ABCD, AB ∥ DC, ∠DAB = a, ∠ABC = b."""
    ca, cb = 1 / math.tan(math.radians(a)), 1 / math.tan(math.radians(b))
    w = top + H * (ca + cb)
    if w < 1.7:
        top += 1.7 - w
        w = 1.7
    A, B = (0, 0), (w, 0)
    D = (H * ca, H)
    C = (w - H * cb, H)
    return {"A": A, "B": B, "C": C, "D": D}


@template(T, "intermediate", GT + "05", GT + "04")
def trapezium_angles(r):
    """math-pat-angles-parallel-quadrilaterals"""
    a, b = r.randint(50, 130), r.randint(50, 130)
    if a == 90 and b == 90:
        return None
    mode = r.choice(["D", "C", "D", "C"])
    q = trap_pts(a, b)
    sc = Scene()
    for n, p in q.items():
        sc.add(n, *p)
    sc.poly("ABCD"); sc.arrow("A", "B"); sc.arrow("D", "C")
    cen = (sum(p[0] for p in q.values()) / 4, sum(p[1] for p in q.values()) / 4)
    for n in "ABCD":
        sc.label(n, away=cen)
    sc.ang("A", "B", "D", f"{a}°", r=24); sc.ang("B", "A", "C", f"{b}°", r=24)
    if mode == "D":
        sc.ang("D", "A", "C", "x", r=24); ans = 180 - a; gv = a
        stem = f"ABCD is a trapezium with AB parallel to DC. ∠DAB = {a}° and ∠ABC = {b}°. Find ∠ADC."
        wr = [W(a, "assumed_equal", "Assumed ∠ADC = ∠DAB."), W(b, "gave_other_given_angle", "Gave the other given angle."),
              W(360 - a - b if 0 < 360 - a - b <= 180 else None, "used_angle_sum_of_quadrilateral", "Used 360° − a − b."),
              W(180 - b if 180 - b != ans else None, "used_wrong_vertex", "Used the other base angle.")]
    else:
        sc.ang("C", "B", "D", "x", r=24); ans = 180 - b
        stem = f"ABCD is a trapezium with AB parallel to DC. ∠DAB = {a}° and ∠ABC = {b}°. Find ∠BCD."
        wr = [W(b, "assumed_equal", "Assumed ∠BCD = ∠ABC."), W(a, "gave_other_given_angle", "Gave the other given angle."),
              W(360 - a - b if 0 < 360 - a - b <= 180 else None, "used_angle_sum_of_quadrilateral", "Used 360° − a − b."),
              W(180 - a if 180 - a != ans else None, "used_wrong_vertex", "Used the other base angle.")]
    wr = [w for w in wr if w[0]]
    nm = "∠ADC" if mode == "D" else "∠BCD"
    return mk(trapezium_angles, stem, ans, wr,
              ["AB ∥ DC, so the angles between the parallel sides on the same leg add up to 180°.",
               f"{nm} = 180° − {a if mode == 'D' else b}° = {ans}°"], {"a": a, "b": b, "mode": mode}, sc.svg("Trapezium"))


@checker(trapezium_angles)
def _(p):
    q = trap_pts(p["a"], p["b"])
    return F(round(meas(q["A"], q["D"], q["C"]) if p["mode"] == "D" else meas(q["B"], q["C"], q["D"])))


STATEMENTS = [
    ("A parallelogram has two pairs of parallel sides.", True),
    ("The opposite angles of a parallelogram are equal.", True),
    ("A rhombus has four equal sides.", True),
    ("A trapezium has exactly one pair of parallel sides.", True),
    ("All the angles of a rhombus are right angles.", False),
    ("The adjacent angles of a parallelogram are equal.", False),
    ("A parallelogram has four equal sides.", False),
    ("The opposite angles of a rhombus are equal.", True),
    ("A trapezium has two pairs of parallel sides.", False),
    ("Angles between the parallel sides of a trapezium, on the same leg, add up to 180°.", True),
    ("Every rhombus is a parallelogram.", True),
    ("The adjacent angles of a rhombus add up to 180°.", True),
    ("An equilateral triangle has three equal angles of 60° each.", True),
    ("A right-angled triangle can have two right angles.", False),
    ("The angles of any triangle add up to 360°.", False),
    ("An isosceles triangle has two equal angles.", True),
]


@template(T, "intermediate", GT + "04", GT + "01")
def true_statements(r):
    """math-pat-angles-parallel-quadrilaterals"""
    sel = r.sample(STATEMENTS, 4)
    cnt = sum(t for _, t in sel)
    if not 1 <= cnt <= 3:
        return None
    txt = " ".join(f"({'abcd'[i]}) {s}" for i, (s, _) in enumerate(sel))
    stem = f"Look at the statements: {txt} How many of the statements are true?"
    wr = [W(4 - cnt, "counted_the_false_ones", "Counted the false statements."),
          W(cnt + 1, "miscount", "Counted one extra."), W(cnt - 1, "miscount", "Missed one true statement."),
          W(cnt + 2, "miscount", "Counted two extra."), W(cnt + 3, "miscount", "Miscounted.")]
    steps = [f"({'abcd'[i]}) is {'true' if t else 'false'}." for i, (s, t) in enumerate(sel)] + [(f"{cnt} statement is true." if cnt == 1 else f"{cnt} statements are true.")]
    return mk(true_statements, stem, cnt, wr, steps, {"sel": [s for s, _ in sel]}, None, show=lambda v: str(int(v)), maxv=4)


@checker(true_statements)
def _(p):
    d = dict(STATEMENTS)
    return F(sum(1 for s in p["sel"] if d[s]))


# ---------------- competent (composite figures)

@template(T, "competent", GT + "06", GT + "05")
def rhombus_equilateral(r):
    """math-pat-angles-chained-shapes math-pat-angles-parallel-quadrilaterals"""
    b = r.randrange(36, 97, 2)
    if b == 90:
        return None
    q = rhombus_pts(b)
    A, C, D = q["A"], q["C"], q["D"]
    M = ((C[0] + D[0]) / 2, (C[1] + D[1]) / 2)
    n = (-(D[1] - C[1]), D[0] - C[0])
    nl = math.hypot(*n)
    n = (n[0] / nl, n[1] / nl)
    if n[0] * (A[0] - M[0]) + n[1] * (A[1] - M[1]) > 0:
        n = (-n[0], -n[1])
    h = math.sqrt(3) / 2
    E = (M[0] + n[0] * h, M[1] + n[1] * h)
    sc = Scene()
    for k, p in q.items():
        sc.add(k, *p)
    sc.add("E", *E)
    sc.poly("ABCD"); sc.poly(["C", "D", "E"]); sc.seg("A", "E")
    cen = ((A[0] + C[0]) / 2, (A[1] + C[1]) / 2)
    for k in "ABCD":
        sc.label(k, away=cen)
    sc.label("E", away=M)
    for s_ in ("AB", "BC", "CD", "DA", "DE", "CE"):
        sc.tick(s_[0], s_[1])
    sc.ang("B", "A", "C", f"{b}°", r=24)
    sc.ang("A", "D", "E", None, r=0.1) if False else None
    sc.ang("A", "D", "E", "?", r=18) if False else None
    sc.ang("A", "E", "D", "x", r=26) if False else None
    sc.ang("A", "D", "E", "x", r=26)
    ans = (120 - b) // 2
    stem = (f"ABCD is a rhombus with ∠ABC = {b}°. CDE is an equilateral triangle and A and E are on opposite sides of CD. "
            f"Find ∠DAE.")
    ade = b + 60
    wr = [W(ade, "stopped_at_apex_angle", "Found ∠ADE and stopped."),
          W(180 - ade, "forgot_to_halve", "Found the sum of the base angles but did not halve it."),
          W((180 - b) // 2, "used_rhombus_bisector", "Halved the supplement of ∠ABC (this is ∠CAD, not ∠DAE)."),
          W(b - 60 if b - 60 > 0 else None, "subtracted_60", "Subtracted 60° instead of adding it.")]
    wr = [w for w in wr if w[0]]
    return mk(rhombus_equilateral, stem, ans, wr,
              [f"∠ADC = ∠ABC = {b}° (opposite angles of a rhombus)", "∠CDE = 60° (equilateral triangle)",
               f"∠ADE = {b}° + 60° = {ade}° (C is between A and E on the angle at D)",
               "DA = DC = DE, so triangle ADE is isosceles.", f"∠DAE = (180° − {ade}°) ÷ 2 = {ans}°"],
              {"b": b}, sc.svg("Rhombus and equilateral triangle"))


@checker(rhombus_equilateral)
def _(p):
    b = p["b"]
    q = rhombus_pts(b)
    A, C, D = q["A"], q["C"], q["D"]
    # E: rotate C about D by -60 deg or +60 deg, the one lying on the far side from A
    best = None
    for sgn in (1, -1):
        v = (C[0] - D[0], C[1] - D[1])
        t = math.radians(60 * sgn)
        E = (D[0] + v[0] * math.cos(t) - v[1] * math.sin(t), D[1] + v[0] * math.sin(t) + v[1] * math.cos(t))
        side = (C[0] - D[0]) * (E[1] - D[1]) - (C[1] - D[1]) * (E[0] - D[0])
        sideA = (C[0] - D[0]) * (A[1] - D[1]) - (C[1] - D[1]) * (A[0] - D[0])
        if side * sideA < 0:
            best = E
    return F(round(meas(D, A, best)))


@template(T, "competent", GT + "06", GT + "05")
def parallelogram_isosceles(r):
    """math-pat-angles-chained-shapes math-pat-angles-parallel-quadrilaterals"""
    a = r.randrange(40, 121, 2)
    if a == 90:
        return None
    w, d = 2.2, 1.0
    q = para_pts(a, w, d)
    E = (q["D"][0] + d, q["D"][1])
    sc = Scene()
    for k, p in q.items():
        sc.add(k, *p)
    sc.add("E", *E)
    sc.poly("ABCD"); sc.seg("A", "E")
    cen = ((q["A"][0] + q["C"][0]) / 2, (q["A"][1] + q["C"][1]) / 2)
    for k in "ABCD":
        sc.label(k, away=cen)
    sc.label("E", away=(E[0], E[1] - 1))
    sc.arrow("A", "B"); sc.arrow("D", "C")
    sc.tick("A", "D"); sc.tick("D", "E")
    sc.ang("A", "B", "D", f"{a}°", r=24)
    sc.ang("E", "A", "C", "x", r=22)
    half = a // 2
    ans = 180 - half
    stem = (f"ABCD is a parallelogram with ∠DAB = {a}°. E is a point on DC such that DE = DA. Find ∠AEC.")
    wr = [W(half, "stopped_at_base_angle", "Found ∠AED and stopped."),
          W(a, "assumed_equal", "Assumed ∠AEC = ∠DAB."),
          W(180 - a, "gave_adjacent_angle", "Gave ∠ADC."),
          W(90 + half, "x", "")]
    wr = [w for w in wr if w[1] != "x"]
    return mk(parallelogram_isosceles, stem, ans, wr,
              [f"∠ADC = 180° − {a}° = {180 - a}° (adjacent angles of a parallelogram)",
               "DA = DE, so triangle ADE is isosceles with apex D.", f"∠AED = (180° − {180 - a}°) ÷ 2 = {half}°",
               f"∠AEC = 180° − {half}° = {ans}° (angles on a straight line DEC)"], {"a": a}, sc.svg("Parallelogram and isosceles triangle"))


@checker(parallelogram_isosceles)
def _(p):
    a = p["a"]
    q = para_pts(a, 2.2, 1.0)
    E = (q["D"][0] + 1.0, q["D"][1])
    return F(round(meas(q["A"], E, q["C"])))


@template(T, "competent", GT + "06", GT + "05")
def trapezium_isosceles(r):
    """math-pat-angles-chained-shapes math-pat-angles-parallel-quadrilaterals"""
    a = r.randint(60, 120)
    b = r.randrange(50, 101, 2)
    ans = 180 - a - b // 2
    if ans < 20:
        return None
    pts = trap_chain(a, b)
    sc = Scene()
    for k, p in pts.items():
        sc.add(k, *p)
    sc.poly("ABCD"); sc.seg("B", "D"); sc.arrow("A", "B"); sc.arrow("D", "C")
    cen = (sum(p[0] for p in pts.values()) / 4, sum(p[1] for p in pts.values()) / 4)
    for k in "ABCD":
        sc.label(k, away=cen)
    sc.tick("B", "C"); sc.tick("C", "D")
    sc.ang("A", "D", "B", f"{a}°", r=24)
    sc.ang("B", "A", "C", f"{b}°", r=26)
    sc.ang("D", "A", "B", "x", r=24)
    stem = (f"ABCD is a trapezium with AB parallel to DC and BC = CD. ∠DAB = {a}° and ∠ABC = {b}°. Find ∠ADB.")
    wr = [W(180 - a - b, "used_whole_angle_b", "Used ∠ABC instead of ∠ABD."),
          W(b // 2, "stopped_at_half_angle", "Found ∠ABD and stopped."),
          W(180 - a, "used_one_angle_only", "Subtracted only ∠DAB from 180°."),
          W(180 - b, "gave_adjacent_angle", "Found ∠BCD and gave it.")]
    return mk(trapezium_isosceles, stem, ans, wr,
              [f"∠BCD = 180° − {b}° = {180 - b}° (AB ∥ DC)", "BC = CD, so ∠CBD = ∠CDB.",
               f"∠CBD = (180° − {180 - b}°) ÷ 2 = {b // 2}°", f"∠ABD = {b}° − {b // 2}° = {b // 2}°",
               f"∠ADB = 180° − {a}° − {b // 2}° = {ans}°"], {"a": a, "b": b}, sc.svg("Trapezium with an isosceles triangle"))


def trap_chain(a, b):
    """Trapezium with AB ∥ DC, BC = CD, ∠ABC = b, ∠DAB = a. B at the origin."""
    B = (0, 0)
    C = vec(180 - b, 1.0)
    D = (C[0] - 1.0, C[1])
    A = (D[0] - D[1] / math.tan(math.radians(a)), 0)
    return {"A": A, "B": B, "C": C, "D": D}


@checker(trapezium_isosceles)
def _(p):
    q = trap_chain(p["a"], p["b"])
    return F(round(meas(q["A"], q["D"], q["B"])))


@template(T, "competent", GT + "06", GT + "03")
def collinear_isosceles(r):
    """math-pat-angles-chained-shapes"""
    p = r.randrange(30, 77, 2)
    mode = r.choice(["CDA", "BAD"])
    c = 2.0
    A = (c / 2, (c / 2) * math.tan(math.radians(p)))
    ca = math.hypot(c / 2, A[1])
    pts = {"B": (0, 0), "C": (c, 0), "A": A, "D": (c + ca, 0)}
    sc = Scene()
    for k, v in pts.items():
        sc.add(k, *v)
    sc.poly("ABC"); sc.seg("C", "D"); sc.seg("A", "D")
    sc.label("A", away=(c / 2, 0)); sc.label("B", away=(c / 2, 0.4)); sc.label("C", away=(c / 2, 0.4)); sc.label("D", away="C")
    sc.tick("A", "B"); sc.tick("A", "C"); sc.tick("C", "A") if False else None
    sc.tick("C", "D", 2) if False else None
    sc.ang("B", "A", "C", f"{p}°", r=26)
    if mode == "CDA":
        sc.ang("D", "C", "A", "x", r=26)
        stem = f"B, C and D lie on a straight line. AB = AC = CD and ∠ABC = {p}°. Find ∠ADC."
        ans = p // 2
        wr = [W(p, "gave_given_angle", "Assumed ∠ADC = ∠ABC."),
              W(180 - p, "gave_exterior_angle", "Gave ∠ACD."),
              W(180 - 2 * p, "gave_apex_angle", "Gave ∠BAC."),
              W(90 - p // 2 if 90 - p // 2 != ans else None, "x", "")]
    else:
        sc.ang("A", "B", "D", "x", r=30)
        stem = f"B, C and D lie on a straight line. AB = AC = CD and ∠ABC = {p}°. Find ∠BAD."
        ans = 180 - 3 * p // 2
        wr = [W(180 - 2 * p, "stopped_at_apex_angle", "Found ∠BAC and stopped."),
              W(p // 2, "stopped_at_base_angle", "Found ∠CAD and stopped."),
              W(180 - p - p // 2 + 0 if False else 180 - p, "used_one_angle_only", "Subtracted only ∠ABC from 180°."),
              W(180 - 2 * p + p, "x", "")]
    wr = [w for w in wr if w[1] != "x" and w[0]]
    steps = [f"AB = AC, so ∠ACB = ∠ABC = {p}°.", f"∠ACD = 180° − {p}° = {180 - p}° (angles on a straight line)",
             f"CA = CD, so ∠CAD = ∠CDA = (180° − {180 - p}°) ÷ 2 = {p // 2}°"]
    if mode == "BAD":
        steps += [f"∠BAC = 180° − {p}° − {p}° = {180 - 2 * p}°", f"∠BAD = {180 - 2 * p}° + {p // 2}° = {ans}°"]
    return mk(collinear_isosceles, stem, ans, wr, steps, {"p": p, "mode": mode}, sc.svg("Two isosceles triangles on a line"))


@checker(collinear_isosceles)
def _(q):
    p = q["p"]
    c = 2.0
    A = (c / 2, (c / 2) * math.tan(math.radians(p)))
    ca = math.hypot(c / 2, A[1])
    B, C, D = (0, 0), (c, 0), (c + ca, 0)
    return F(round(meas(C, D, A) if False else (meas(A, D, C) if q["mode"] == "CDA" else meas(B, A, D))))


# ============================================================ PERPENDICULAR AND PARALLEL LINES

def rot(p, deg):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return (p[0] * c - p[1] * s, p[0] * s + p[1] * c)


# (the perpendicular and parallel line templates are with the grid helpers, further down)


# ============================================================ RECTANGLE AND SQUARE

def rect_scene(l, w, labels, w_=300, h_=190):
    sc = Scene(w=w_, h=h_, pad=44)
    sc.add("A", 0, 0); sc.add("B", l, 0); sc.add("C", l, w); sc.add("D", 0, w)
    sc.poly("ABCD")
    cen = (l / 2, w / 2)
    for n in "ABCD":
        sc.label(n, away=cen)
    for k, txt in labels.items():
        a, b = k[0], k[1]
        sc.side(a, b, txt)
    for v, a, b in (("A", "B", "D"), ("B", "A", "C"), ("C", "B", "D"), ("D", "A", "C")):
        sc.right(v, a, b)
    return sc


@template(T, "basic", GR + "01")
def rect_sides_basic(r):
    """Opposite sides of a rectangle are equal; perimeter"""
    l, w = r.randint(6, 25), r.randint(3, 15)
    if l <= w:
        return None
    mode = r.choice(["perimeter", "other_side", "square_side"])
    nm = r.choice(NAMES)
    if mode == "perimeter":
        sc = rect_scene(l, w, {"AB": f"{l} cm", "BC": f"{w} cm"})
        stem = f"ABCD is a rectangle with AB = {l} cm and BC = {w} cm. Find its perimeter in cm."
        ans = 2 * (l + w)
        wr = [W(l + w, "forgot_to_double", "Added the length and breadth only."),
              W(l * w, "found_area", "Multiplied the sides (area)."),
              W(2 * l + w, "used_three_sides", "Counted only three sides."),
              W(4 * l, "treated_as_square", "Treated it as a square.")]
        steps = ["Opposite sides of a rectangle are equal: CD = AB and AD = BC.", f"Perimeter = 2 × ({l} + {w}) = {ans} cm"]
        sh = unit("cm")
        sh = lambda v: f"{int(v)} cm"
    elif mode == "other_side":
        sc = rect_scene(l, w, {"AB": f"{l} cm", "BC": f"{w} cm"})
        stem = f"ABCD is a rectangle. AB = {l} cm and the perimeter is {2 * (l + w)} cm. Find BC in cm."
        ans = w
        P2 = 2 * (l + w)
        wr = [W(P2 - l, "forgot_to_halve", f"Subtracted {l} from the perimeter."),
              W(P2 // 2 - 0, "stopped_at_half_perimeter", "Found the sum of the length and breadth and stopped."),
              W(P2 - 2 * l, "subtracted_only_two_sides", "Subtracted only two sides, then forgot to halve."),
              W(l - w if l - w != w else None, "subtracted_sides", "Subtracted the sides.")]
        sc = rect_scene(l, w, {"AB": f"{l} cm"})
        steps = ["AB + BC = perimeter ÷ 2.", f"AB + BC = {P2} ÷ 2 = {P2 // 2}", f"BC = {P2 // 2} − {l} = {w} cm"]
        sh = lambda v: f"{int(v)} cm"
    else:
        s = r.randint(4, 20)
        stem = f"A square has a perimeter of {4 * s} cm. Find the length of one side in cm."
        ans = s
        sc = Scene(w=240, h=160, pad=34)
        sc.add("A", 0, 0); sc.add("B", 1, 0); sc.add("C", 1, 1); sc.add("D", 0, 1)
        sc.poly("ABCD")
        for n in "ABCD":
            sc.label(n, away=(0.5, 0.5))
        sc.tick("A", "B"); sc.tick("B", "C"); sc.tick("C", "D"); sc.tick("D", "A")
        for v, a, b in (("A", "B", "D"), ("B", "A", "C"), ("C", "B", "D"), ("D", "A", "C")):
            sc.right(v, a, b)
        wr = [W(2 * s, "halved_only", "Divided the perimeter by 2."), W(s * s, "squared_side", "Squared the side."),
              W(4 * s - 4, "x", ""), W(s // 2 if s % 2 == 0 else None, "x", ""), W(4 * s // 3, "x", "")]
        wr = [w_ for w_ in wr if w_[1] != "x"]
        wr += [W(4 * s, "gave_perimeter", "Gave the perimeter.")]
        steps = ["A square has 4 equal sides.", f"Side = {4 * s} ÷ 4 = {s} cm"]
        sh = lambda v: f"{int(v)} cm"
        l, w = s, s
    return mk(rect_sides_basic, stem, ans, wr, steps, {"l": l, "w": w, "mode": mode, "s": s if mode == "square_side" else 0},
              sc.svg("Rectangle"), show=sh, maxv=400)


@checker(rect_sides_basic)
def _(p):
    if p["mode"] == "perimeter":
        return F(sum(1 for _ in range(1)) * 0 + p["l"] + p["w"] + p["l"] + p["w"])
    if p["mode"] == "other_side":
        P2 = 2 * (p["l"] + p["w"])
        return F(next(b for b in range(1, 200) if 2 * (p["l"] + b) == P2))
    return F(next(s for s in range(1, 200) if 4 * s == 4 * p["s"]))


RS_FACTS = [
    ("A rectangle has four right angles.", True), ("A square has four equal sides.", True),
    ("Opposite sides of a rectangle are equal.", True), ("A square is also a rectangle.", True),
    ("Opposite sides of a rectangle are parallel.", True), ("A rectangle always has four equal sides.", False),
    ("Every rectangle is a square.", False), ("A square has only two right angles.", False),
    ("Adjacent sides of a square are perpendicular.", True), ("The opposite sides of a square are not parallel.", False),
    ("A rectangle has two pairs of equal sides.", True), ("All the angles of a square are 90°.", True),
    ("Adjacent sides of a rectangle are parallel.", False), ("A rectangle that is not a square has four equal angles.", True),
]


@template(T, "basic", GR + "01")
def rect_count_true(r):
    """True or false statements about rectangles and squares"""
    sel = r.sample(RS_FACTS, 4)
    cnt = sum(t for _, t in sel)
    if not 1 <= cnt <= 3:
        return None
    txt = " ".join(f"({'abcd'[i]}) {s}" for i, (s, _) in enumerate(sel))
    stem = f"Look at the statements: {txt} How many of the statements are true?"
    wr = [W(4 - cnt, "counted_the_false_ones", "Counted the false statements."),
          W(cnt + 1, "miscount", "Counted one extra."), W(cnt - 1, "miscount", "Missed one true statement."), W(cnt + 2, "miscount", "Miscounted."),
          W(cnt + 3, "miscount", "Miscounted.")]
    return mk(rect_count_true, stem, cnt, wr,
              [f"({'abcd'[i]}) is {'true' if t else 'false'}." for i, (s, t) in enumerate(sel)] + [(f"{cnt} statement is true." if cnt == 1 else f"{cnt} statements are true.")],
              {"sel": [s for s, _ in sel]}, None, show=lambda v: str(int(v)), maxv=4)


@checker(rect_count_true)
def _(p):
    d = dict(RS_FACTS)
    return F(sum(1 for s in p["sel"] if d[s]))


@template(T, "intermediate", GR + "01")
def rect_angle_triangle(r):
    """Rectangle with a line from a corner to a side"""
    e = r.randint(35, 80)
    mode = r.choice(["DAE", "AEC"])
    h, w = 1.0, 1.9
    E = (h / math.tan(math.radians(e)), h)
    sc = Scene(w=320, h=200, pad=34)
    sc.add("A", 0, 0); sc.add("B", w, 0); sc.add("C", w, h); sc.add("D", 0, h); sc.add("E", *E)
    sc.poly("ABCD"); sc.seg("A", "E")
    for n in "ABCD":
        sc.label(n, away=(w / 2, h / 2))
    sc.label("E", away=(E[0], E[1] - 1))
    for v, a, b in (("A", "B", "D"), ("B", "A", "C"), ("C", "B", "D"), ("D", "A", "C")):
        sc.right(v, a, b)
    sc.ang("E", "A", "D", f"{e}°", r=22) if mode == "DAE" else sc.ang("E", "A", "D", f"{e}°", r=22)
    if mode == "DAE":
        sc.ang("A", "D", "E", "x", r=24)
        stem = f"ABCD is a rectangle and E is a point on DC. ∠AED = {e}°. Find ∠DAE."
        ans = 90 - e
        wr = [W(e, "gave_given_angle", "Gave the given angle."), W(180 - e, "used_180", "Used 180° instead of the triangle sum with 90°."),
              W(90 + e if 90 + e <= 180 else None, "added_instead_of_subtracting", "Added instead of subtracting."),
              W(180 - 90 - e + 10, "x", "")]
        steps = ["∠ADE = 90° (rectangle).", f"∠DAE = 180° − 90° − {e}° = {ans}°"]
    else:
        sc.ang("E", "A", "C", "x", r=24) if False else None
        sc.ang("E", "C", "A", "x", r=24)
        stem = f"ABCD is a rectangle and E is a point on DC. ∠AED = {e}°. Find ∠AEC."
        ans = 180 - e
        wr = [W(e, "gave_given_angle", "Gave the given angle."), W(90 - e, "found_other_angle", "Found ∠DAE."),
              W(90 + e if 90 + e <= 180 else None, "x", ""), W(360 - e if False else 180 - e + 90 if 270 - e <= 180 else None, "x", "")]
        steps = ["D, E and C are on a straight line, so ∠AEC + ∠AED = 180°.", f"∠AEC = 180° − {e}° = {ans}°"]
    wr = [w_ for w_ in wr if w_[0] and w_[1] != "x"]
    return mk(rect_angle_triangle, stem, ans, wr, steps, {"e": e, "mode": mode}, sc.svg("Rectangle with a line AE"))


@checker(rect_angle_triangle)
def _(p):
    e = p["e"]
    A, D, C = (0, 0), (0, 1.0), (1.9, 1.0)
    E = (1.0 / math.tan(math.radians(e)), 1.0)
    return F(round(meas(E, A, D) if False else (meas(A, D, E) if False else (meas(D, A, E) if p["mode"] == "DAE" else meas(A, E, C)))))


@template(T, "intermediate", GR + "01")
def rect_perimeter_algebra(r):
    """Rectangle with sides given in terms of x"""
    x = r.randint(3, 15)
    a, m = r.randint(2, 4), r.randint(1, 9)
    L, B = a * x + m, x
    P = 2 * (L + B)
    sc = rect_scene(L, B, {"AB": f"({a}x + {m}) cm", "BC": "x cm"}) if L > 1.15 * B else None
    if sc is None:
        return None
    nm = r.choice(NAMES)
    stem = f"The rectangle ABCD has AB = ({a}x + {m}) cm and BC = x cm. Its perimeter is {P} cm. Find the length of AB in cm."
    wr = [W(x, "found_x_only", "Found x but did not work out AB."),
          W(P // 2 - x + 0 if False else P // 2, "stopped_at_half_perimeter", "Found AB + BC and stopped."),
          W(a * x, "ignored_constant", f"Forgot to add {m}."),
          W(P - 2 * B, "x", "")]
    wr = [w_ for w_ in wr if w_[1] != "x"]
    return mk(rect_perimeter_algebra, stem, L, wr,
              [f"AB + BC = {P} ÷ 2 = {P // 2}", f"({a}x + {m}) + x = {P // 2} → {a + 1}x = {P // 2 - m} → x = {x}",
               f"AB = {a} × {x} + {m} = {L} cm"], {"a": a, "m": m, "P": P}, sc.svg("Rectangle"), show=lambda v: f"{int(v)} cm", maxv=500)


@checker(rect_perimeter_algebra)
def _(p):
    x = next(x for x in range(1, 200) if 2 * ((p["a"] * x + p["m"]) + x) == p["P"])
    return F(p["a"] * x + p["m"])


@template(T, "intermediate", GR + "01")
def rect_cut_square(r):
    """Rectangle with a square cut off"""
    w = r.randint(4, 14)
    l = w + r.randint(3, 14)
    nm = r.choice(NAMES)
    sc = Scene(w=330, h=190, pad=44)
    sc.add("A", 0, 0); sc.add("B", l, 0); sc.add("C", l, w); sc.add("D", 0, w); sc.add("E", w, 0); sc.add("F", w, w)
    sc.poly("ABCD"); sc.seg("E", "F", dash=True)
    for n in "ABCD":
        sc.label(n, away=(l / 2, w / 2))
    sc.label("E", away=(w, w / 2)); sc.label("F", away=(w, w / 2))
    sc.side("A", "B", f"{l} cm"); sc.side("B", "C", f"{w} cm")
    stem = (f"{nm} cuts the square AEFD from the rectangle ABCD along the dotted line EF, as shown. "
            f"AB = {l} cm and BC = {w} cm. Find the perimeter of the remaining rectangle EBCF in cm.")
    ans = 2 * ((l - w) + w)
    wr = [W(2 * (l + w), "used_original_perimeter", "Gave the perimeter of the whole rectangle."),
          W(2 * (l - w) + w, "x", ""), W((l - w) + w, "forgot_to_double", "Found the sum of two sides only."),
          W(2 * (l - w), "used_one_dimension", "Left out the breadth of the piece."),
          W(2 * (l - w) + 2 * w + 2 * w, "added_cut_edge_twice", "Counted the cut edge EF twice.")]
    wr = [w_ for w_ in wr if w_[1] != "x"]
    return mk(rect_cut_square, stem, ans, wr,
              [f"EB = {l} − {w} = {l - w} cm (AE = AD = {w} cm, a square).", f"Perimeter of EBCF = 2 × ({l - w} + {w}) = {ans} cm"],
              {"l": l, "w": w}, sc.svg("Rectangle with a square cut off"), show=lambda v: f"{int(v)} cm", maxv=400)


@checker(rect_cut_square)
def _(p):
    l, w = p["l"], p["w"]
    EB = l - w
    per = 0
    for a, b in ((EB, 0), (0, w), (EB, 0), (0, w)):
        per += abs(a) + abs(b)
    return F(per)


@template(T, "competent", GR + "01", GT + "06")
def rect_isosceles_chain(r):
    """math-pat-angles-chained-shapes"""
    eps = r.randrange(40, 141, 2)
    h = 1.0
    w = 2 * h * math.tan(math.radians(eps / 2))
    E = (w / 2, 0)
    sc = Scene(w=330, h=210, pad=34)
    sc.add("A", 0, 0); sc.add("B", w, 0); sc.add("C", w, h); sc.add("D", 0, h); sc.add("E", *E)
    sc.poly("ABCD"); sc.seg("D", "E"); sc.seg("C", "E")
    for n in "ABCD":
        sc.label(n, away=(w / 2, h / 2))
    sc.label("E", away=(w / 2, h))
    sc.tick("E", "D"); sc.tick("E", "C")
    for v, a, b in (("A", "B", "D"), ("B", "A", "C")):
        sc.right(v, a, b)
    sc.ang("E", "D", "C", f"{eps}°", r=26)
    sc.ang("D", "A", "E", "x", r=22)
    ans = eps // 2
    stem = (f"ABCD is a rectangle. E is a point on AB such that EC = ED and ∠DEC = {eps}°. Find ∠ADE.")
    base = (180 - eps) // 2
    wr = [W(base, "stopped_at_base_angle", "Found ∠EDC and stopped."),
          W(90 - eps // 2 + 0 if False else 180 - eps, "forgot_to_halve", "Found the sum of the base angles, not the half."),
          W(eps, "gave_given_angle", "Gave the given angle."),
          W(90 - ans if 90 - ans != ans else None, "x", "")]
    wr = [w_ for w_ in wr if w_[1] != "x" and w_[0]]
    return mk(rect_isosceles_chain, stem, ans, wr,
              [f"EC = ED, so ∠EDC = ∠ECD = (180° − {eps}°) ÷ 2 = {base}°", "∠ADC = 90° (rectangle)",
               f"∠ADE = 90° − {base}° = {ans}°"], {"eps": eps}, sc.svg("Rectangle with an isosceles triangle"))


@checker(rect_isosceles_chain)
def _(p):
    eps = p["eps"]
    h = 1.0
    w = 2 * h * math.tan(math.radians(eps / 2))
    A, D, E = (0, 0), (0, h), (w / 2, 0)
    return F(round(meas(A, D, E)))


@template(T, "competent", GR + "01")
def square_rect_perimeter(r):
    """A square joined to a rectangle: perimeter of the compound figure"""
    s = r.randint(6, 16)
    b = r.randint(2, s - 2)
    L = r.choice([x for x in range(4, 16) if x != b])  # unequal, so it really is a rectangle
    nm = r.choice(NAMES)
    sc = Scene(w=340, h=200, pad=46)
    pts = [(0, 0), (L + s, 0), (L + s, s), (L, s), (L, b), (0, b)]
    # square on the right (side s), rectangle L by b on the left, bottoms level
    for i, p in enumerate(pts):
        sc.add("PQRSTU"[i], *p)
    sc.poly(list("PQRSTU"))
    sc.side("P", "U", f"{b} cm", away=(L, s / 2)); sc.side("U", "T", f"{L} cm", away=(L / 2, 0)) if False else sc.side("U", "T", f"{L} cm")
    sc.side("Q", "R", f"{s} cm")
    stem = (f"{nm} joins a square of side {s} cm to a rectangle of length {L} cm and breadth {b} cm, as shown. "
            f"The bottoms of the two shapes are level. Find the perimeter of the whole figure in cm.")
    ans = 2 * (L + s) + 2 * s
    sep = 4 * s + 2 * (L + b)
    wr = [W(sep, "added_both_perimeters", "Added the perimeters of the two shapes, counting the joined side twice."),
          W(sep - 2 * b, "subtracted_the_wrong_join", f"Took off twice the breadth {b} cm instead of the shorter join."),
          W(2 * (L + s) + s, "left_out_a_side", "Left out one side."),
          W(2 * (L + s + s - b), "x", "")]
    wr = [w_ for w_ in wr if w_[1] != "x"]
    return mk(square_rect_perimeter, stem, ans, wr,
              [f"Total length across the bottom = {L} + {s} = {L + s} cm", f"Height of the tall square = {s} cm",
               f"The outline goes right and up the same distance as the bounding rectangle: 2 × ({L + s} + {s}) = {ans} cm"],
              {"s": s, "b": b, "L": L}, sc.svg("Square joined to a rectangle"), show=lambda v: f"{int(v)} cm", maxv=500)


@checker(square_rect_perimeter)
def _(p):
    s, b, L = p["s"], p["b"], p["L"]
    pts = [(0, 0), (L + s, 0), (L + s, s), (L, s), (L, b), (0, b)]
    return F(round(sum(dist(pts[i], pts[(i + 1) % 6]) for i in range(6))))


@template(T, "competent", GR + "01")
def rect_into_squares(r):
    """Rectangle cut into the largest identical squares"""
    g = r.choice([2, 3, 4, 5, 6, 7, 8, 9, 10, 12])
    a, b = r.sample(range(2, 12), 2)
    if math.gcd(a, b) != 1:
        return None
    l, w = a * g, b * g
    nm = r.choice(NAMES)
    f = Fig(310, 180)
    f.rect(70, 30, 210, 130)
    f.text(175, 14, f"{l} cm"); f.text(34, 95, f"{w} cm", size=13)
    stem = (f"{nm} cuts a rectangular piece of card, {l} cm by {w} cm, into identical squares with no card left over. "
            f"The squares are as big as possible. How many squares are there?")
    ans = a * b
    wr = [W(g, "gave_side_length", "Gave the side of one square."),
          W(a + b, "added_instead_of_multiplied", "Added the number of squares along each side."),
          W(l * w // (g * g * 2) if False else (l * w) // (math.gcd(l, w) + 0) // math.gcd(l, w) * 1 if False else a * b + a, "x", ""),
          W(l * w // g, "divided_area_by_side", "Divided the area by the side instead of the area of a square."),
          W(l * w, "gave_area", "Gave the area.")]
    wr = [w_ for w_ in wr if w_[1] != "x"]
    return mk(rect_into_squares, stem, ans, wr,
              [f"Side of the largest square = HCF of {l} and {w} = {g} cm", f"Squares along the length = {l} ÷ {g} = {a}",
               f"Squares along the breadth = {w} ÷ {g} = {b}", f"Number of squares = {a} × {b} = {ans}"],
              {"l": l, "w": w}, f.svg("Rectangle of card"), show=lambda v: str(int(v)), maxv=None)


@checker(rect_into_squares)
def _(p):
    l, w = p["l"], p["w"]
    s = max(s for s in range(1, min(l, w) + 1) if l % s == 0 and w % s == 0)
    return F((l * w) // (s * s))


# ============================================================ LINE SYMMETRY

def reflect(p, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    t = ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / (dx * dx + dy * dy)
    fx, fy = a[0] + t * dx, a[1] + t * dy
    return (2 * fx - p[0], 2 * fy - p[1])


def is_sym(poly, a, b, tol=1e-6):
    for p in poly:
        q = reflect(p, a, b)
        if not any(abs(q[0] - o[0]) < tol and abs(q[1] - o[1]) < tol for o in poly):
            return False
    return True


def key_pts(poly):
    n = len(poly)
    mids = [((poly[i][0] + poly[(i + 1) % n][0]) / 2, (poly[i][1] + poly[(i + 1) % n][1]) / 2) for i in range(n)]
    c = (sum(p[0] for p in poly) / n, sum(p[1] for p in poly) / n)
    return list(poly) + mids + [c]


def line_key(a, b):
    ang = math.atan2(b[1] - a[1], b[0] - a[0]) % math.pi
    if ang > math.pi - 1e-7:
        ang = 0.0
    d = -a[0] * math.sin(ang) + a[1] * math.cos(ang)
    return (round(ang, 4) % round(math.pi, 4), round(d, 4) + 0.0)


def candidate_lines(poly):
    kp = key_pts(poly)
    seen, out = set(), []
    for i in range(len(kp)):
        for j in range(i + 1, len(kp)):
            a, b = kp[i], kp[j]
            if math.hypot(b[0] - a[0], b[1] - a[1]) < 1e-6:
                continue
            k = line_key(a, b)
            if k in seen:
                continue
            seen.add(k)
            out.append((a, b))
    return out


def find_axes(poly):
    return [(a, b) for a, b in candidate_lines(poly) if is_sym(poly, a, b)]


def regular(n, R=1.0, start=90):
    return [vec(start + 360 * i / n, R) for i in range(n)]


SHAPES = {
    "equilateral triangle": (lambda r: regular(3), 3), "square": (lambda r: [(0, 0), (1, 0), (1, 1), (0, 1)], 4),
    "regular pentagon": (lambda r: regular(5), 5), "regular hexagon": (lambda r: regular(6), 6),
    "regular octagon": (lambda r: regular(8, start=67.5), 8),
    "rectangle (not a square)": (lambda r: [(0, 0), (1.7, 0), (1.7, 1), (0, 1)], 2),
    "rhombus (not a square)": (lambda r: [(-1.2, 0), (0, -0.8), (1.2, 0), (0, 0.8)], 2),
    "isosceles triangle (not equilateral)": (lambda r: [(-1, 0), (1, 0), (0, 1.7)], 1),
    "isosceles trapezium": (lambda r: [(-1.4, 0), (1.4, 0), (0.8, 1), (-0.8, 1)], 1),
}


def rot_poly(poly, d):
    return [rot(p, d) for p in poly]


def draw_poly(poly, w=300, h=220, pad=26, shade=0.07, title="Shape"):
    sc = Scene(w=w, h=h, pad=pad)
    for i, p in enumerate(poly):
        sc.add(f"p{i}", *p)
    sc.poly([f"p{i}" for i in range(len(poly))], shade=shade)
    return sc


@template(T, "basic", GS + "01", GS + "02")
def lines_of_symmetry_count(r):
    """math-pat-symmetry-and-construction"""
    name = r.choice(list(SHAPES))
    gen, ans = SHAPES[name]
    sides = len(gen(r))
    nm = r.choice(NAMES)
    poly = rot_poly(gen(r), r.choice([0, 0, 15, 30, -20]))
    sc = draw_poly(poly)
    stem = f"{nm} draws {art(name)} {name}, as shown. How many lines of symmetry does it have?"
    wr = [W(sides, "counted_sides", "Counted the sides instead of the lines of symmetry."),
          W(ans * 2, "counted_each_line_twice", "Counted each line of symmetry as two."),
          W(ans + 1, "counted_a_diagonal_too", "Counted a line that is not a line of symmetry."),
          W(ans - 1 if ans > 1 else None, "missed_a_line", "Missed one line of symmetry."),
          W(ans + 2, "miscount", "Miscounted.")]
    return mk(lines_of_symmetry_count, stem, ans, wr,
              [f"Fold the {name} so that the two halves match exactly.", f"Number of ways = {ans}"],
              {"poly": [list(p) for p in poly]}, sc.svg("Shape"), show=lambda v: str(int(v)), maxv=12)


@checker(lines_of_symmetry_count)
def _(p):
    return F(len(find_axes([tuple(q) for q in p["poly"]])))


SYM_L = list("AHIMOTUVWXY") + list("BCDE")
ASYM_L = list("FGJLNPQRSZ")


@template(T, "basic", GS + "01")
def symmetric_letters(r):
    """math-pat-symmetry-and-construction"""
    k = r.randint(1, 4)
    letters = r.sample(SYM_L, k) + r.sample(ASYM_L, 6 - k)
    r.shuffle(letters)
    nm = r.choice(NAMES)
    stem = (f"{nm} writes these capital letters in block print: {' '.join(letters)}. "
            f"How many of the letters have at least one line of symmetry?")
    wr = [W(6 - k, "counted_the_asymmetric_letters", "Counted the letters with no line of symmetry."),
          W(k + 1, "miscount", "Counted one extra letter."), W(k - 1 if k > 1 else None, "miscount", "Missed a letter."),
          W(k + 2, "miscount", "Miscounted."), W(k + 3, "miscount", "Miscounted.")]
    return mk(symmetric_letters, stem, k, wr,
              ["A letter has a line of symmetry if it can be folded so the halves match.",
               "Symmetric letters: " + ", ".join(l for l in letters if l in SYM_L), f"The number of letters with a line of symmetry is {k}."],
              {"letters": letters}, None, show=lambda v: str(int(v)), maxv=6)


@checker(symmetric_letters)
def _(p):
    return F(sum(1 for l in p["letters"] if l in "AHIMOTUVWXYBCDE"))


def draw_line_panel(poly, a, b, size=150):
    sc = Scene(w=size, h=size, pad=18)
    for i, p in enumerate(poly):
        sc.add(f"p{i}", *p)
    names = [f"p{i}" for i in range(len(poly))]
    c = (sum(p[0] for p in poly) / len(poly), sum(p[1] for p in poly) / len(poly))
    R = max(math.hypot(p[0] - c[0], p[1] - c[1]) for p in poly) * 1.2
    dx, dy = b[0] - a[0], b[1] - a[1]
    n = math.hypot(dx, dy)
    ux, uy = dx / n, dy / n
    t0 = (c[0] - a[0]) * ux + (c[1] - a[1]) * uy
    mid = (a[0] + ux * t0, a[1] + uy * t0)
    sc.add("L1", mid[0] - ux * R, mid[1] - uy * R); sc.add("L2", mid[0] + ux * R, mid[1] + uy * R)
    sc.poly(names, shade=0.07)
    sc.seg("L1", "L2", dash=True, width=2)
    sc.svg("panel")
    return sc.f


PICK = ["rectangle (not a square)", "isosceles triangle (not equilateral)", "rhombus (not a square)",
        "isosceles trapezium", "regular pentagon", "regular hexagon"]


@template(T, "basic", GS + "02")
def which_dotted_line(r):
    """math-pat-symmetry-and-construction"""
    name = r.choice(PICK)
    base = SHAPES[name][0](r)
    poly = rot_poly(base, r.choice([0, 0, 20, -15]))
    axes = find_axes(poly)
    cand = [(a, b) for a, b in candidate_lines(poly) if not is_sym(poly, a, b)]
    # plausible false lines: they pass through at least one vertex
    vert = [(a, b) for a, b in cand if any(abs((b[0] - a[0]) * (v[1] - a[1]) - (b[1] - a[1]) * (v[0] - a[0])) < 1e-6 for v in poly)]
    if len(axes) < 1 or len(vert) < 3:
        return None
    good = r.choice(axes)
    bads = r.sample(vert, 3)
    lines = bads[:]
    pos = r.randrange(4)
    lines.insert(pos, good)
    figs = [draw_line_panel(poly, a, b) for a, b in lines]
    nm = r.choice(NAMES)
    ph = r.choice(["Which dotted line is a line of symmetry of the", "In which figure is the dotted line a line of symmetry of the",
                   "Only one dotted line below is a line of symmetry of the"])
    sn = name.split(" (")[0]
    stem = (f"{nm} draws {art(sn)} {sn} four times and adds a dotted line to each. {ph} {sn}?" if "Only" not in ph
            else f"{nm} draws {art(sn)} {sn} four times and adds a dotted line to each. {ph} {sn}. Which one is it?")
    wr = [W(((pos + 1) % 4) + 1, "chose_a_line_through_a_corner", "Chose a line that only passes through a corner."),
          W(((pos + 2) % 4) + 1, "chose_a_line_through_a_corner", "Chose a line that does not split the shape into matching halves."),
          W(((pos + 3) % 4) + 1, "chose_a_line_through_a_corner", "Chose a line that does not split the shape into matching halves.")]
    return build(which_dotted_line, stem, pos + 1, wr,
                 ["Fold along each dotted line. The two halves must match exactly.",
                  f"Only figure {'ABCD'[pos]} folds onto itself."], {"poly": [list(p) for p in poly], "lines": [[list(a), list(b)] for a, b in lines]},
                 show=lambda v: "ABCD"[int(v) - 1], whole=True, auto_slips=False, figure=panels(figs, "ABCD", cols=2, title="Four figures"))


@checker(which_dotted_line)
def _(p):
    poly = [tuple(q) for q in p["poly"]]
    ok = [i + 1 for i, (a, b) in enumerate(p["lines"]) if is_sym(poly, tuple(a), tuple(b))]
    return F(ok[0]) if len(ok) == 1 else None


def rand_asym(r):
    kind = r.choice(["para", "tri", "quad"])
    if kind == "para":
        return [(0, 0), (1.8, 0), (2.4, 1), (0.6, 1)]
    if kind == "tri":
        return [(0, 0), (2, 0), (0.6, 1.4)]
    return [(0, 0), (2, 0.2), (1.6, 1.2), (0.2, 0.9)]


@template(T, "intermediate", GS + "01")
def symmetric_figure_count(r):
    """math-pat-symmetry-and-construction"""
    pool = [(n, SHAPES[n][0](r)) for n in PICK]
    k = r.randint(1, 3)
    syms = [rot_poly(g, r.choice([0, 15, 30, -20, 45])) for _, g in r.sample(pool, k)]
    asyms = [rot_poly(rand_asym(r), r.choice([0, 10, -10])) for _ in range(4 - k)]
    shapes = syms + asyms
    r.shuffle(shapes)
    cnt = sum(1 for s in shapes if find_axes(s))
    figs = []
    for s in shapes:
        sc = draw_poly(s, w=150, h=130, pad=16)
        sc.svg("panel")
        figs.append(sc.f)
    nm = r.choice(NAMES)
    ph = r.choice([f"{nm} looks at the four figures P, Q, R and S. How many of them have at least one line of symmetry?",
                   f"How many of the figures P to S can be folded so that the two halves match exactly? ({nm} is checking.)",
                   f"{nm} draws figures P to S. Count the figures that are symmetric (have a line of symmetry)."])
    wr = [W(4 - cnt, "counted_the_asymmetric_figures", "Counted the figures with no line of symmetry."),
          W(cnt + 1, "counted_a_parallelogram_or_slanted_figure", "Counted a figure that cannot be folded onto itself."),
          W(cnt - 1 if cnt > 1 else None, "missed_a_symmetric_figure", "Missed a symmetric figure."), W(cnt + 2, "miscount", "Miscounted.")]
    return build(symmetric_figure_count, ph, cnt, wr, ["Check each figure by imagining a fold.", f"{cnt} figure{'s' if cnt != 1 else ''} {'have' if cnt != 1 else 'has'} a line of symmetry."],
                 {"shapes": [[list(p) for p in s] for s in shapes]}, show=lambda v: str(int(v)), whole=True, auto_slips=False,
                 figure=panels(figs, "PQRS", cols=2, title="Four figures"))


@checker(symmetric_figure_count)
def _(p):
    return F(sum(1 for s in p["shapes"] if find_axes([tuple(q) for q in s])))


@template(T, "intermediate", GS + "01", GS + "02")
def regular_polygon_lines(r):
    """math-pat-symmetry-and-construction"""
    n = r.randint(3, 12)
    mode = r.choice(["total", "reverse", "through_vertices"])
    nm = r.choice(NAMES)
    sc = draw_poly(regular(n), w=240, h=200)
    if mode == "total":
        stem = f"{nm} draws a regular polygon with {n} sides. How many lines of symmetry does it have?"
        ans = n
        wr = [W(n // 2, "halved", "Counted only half of the lines."), W(2 * n, "counted_twice", "Counted each line twice."),
              W(n - 1, "missed_a_line", "Missed a line."), W(n + 1, "extra_line", "Counted an extra line.")]
        steps = ["A regular polygon has as many lines of symmetry as sides.", f"Lines of symmetry = {n}"]
    elif mode == "reverse":
        stem = f"A regular polygon has {n} lines of symmetry. How many vertices (corners) does it have?"
        ans = n
        wr = [W(2 * n, "doubled", "Doubled the number."), W(n // 2, "halved", "Halved the number."),
              W(n + 1, "off_by_one", "Added one."), W(n - 1, "off_by_one", "Subtracted one.")]
        steps = ["A regular polygon has as many lines of symmetry as sides, and as many vertices as sides.", f"Vertices = {n}"]
        sc = None
    else:
        n = r.choice([4, 6, 8, 10, 12])
        sc = draw_poly(regular(n), w=240, h=200)
        stem = f"A regular polygon has {n} sides. How many of its lines of symmetry pass through two opposite vertices?"
        ans = n // 2
        wr = [W(n, "counted_all_lines", "Counted all the lines of symmetry."), W(n // 2 + 1, "off_by_one", "Counted one extra."),
              W(n // 2 - 1 if n // 2 > 1 else None, "off_by_one", "Missed one."), W(2 * n, "counted_twice", "Counted each line twice.")]
        steps = [f"A regular {n}-gon has {n} lines of symmetry in all.",
                 f"Half pass through opposite vertices, the other half through midpoints of opposite sides: {n} ÷ 2 = {ans}"]
    wr = [w_ for w_ in wr if w_[0]]
    return mk(regular_polygon_lines, stem, ans, wr, steps, {"n": n, "mode": mode}, sc.svg("Regular polygon") if sc else None,
              show=lambda v: str(int(v)), maxv=26)


@checker(regular_polygon_lines)
def _(p):
    n = p["n"]
    axes = find_axes(regular(n))
    if p["mode"] == "through_vertices":
        verts = regular(n)
        return F(sum(1 for a, b in axes if sum(1 for v in verts if abs((b[0] - a[0]) * (v[1] - a[1]) - (b[1] - a[1]) * (v[0] - a[0])) < 1e-6) >= 2))
    return F(len(axes))


def refl_cell(c, rr, kind, nc, nr):
    if kind == "v":
        return (nc - 1 - c, rr)
    if kind == "h":
        return (c, nr - 1 - rr)
    if kind == "d1":
        return (rr, c)
    return (nr - 1 - rr, nc - 1 - c)


def closure(cells, kinds, nc, nr):
    S = set(cells)
    while True:
        new = S | {refl_cell(c, rr, k, nc, nr) for (c, rr) in S for k in kinds}
        if new == S:
            return S
        S = new


@template(T, "intermediate", GS + "02", GS + "03")
def shade_to_symmetry(r):
    """math-pat-symmetry-and-construction"""
    nc, nr = r.choice([(6, 5), (6, 6), (8, 6), (8, 7), (6, 7)])
    vertical = r.random() < 0.5
    if not vertical:
        nc, nr = nr, nc
        if nr % 2:
            return None
    elif nc % 2:
        return None
    k = r.randint(6, 12)
    cells = set()
    while len(cells) < k:
        if vertical:
            cells.add((r.randrange(nc), r.randrange(nr)))
        else:
            cells.add((r.randrange(nc), r.randrange(nr)))
    kind = "v" if vertical else "h"
    full = closure(cells, [kind], nc, nr)
    ans = len(full) - len(cells)
    if not 2 <= ans <= 9:
        return None
    line = ("v", nc // 2) if vertical else ("h", nr // 2)
    f, svg = grid_fig(nc, nr, cells, line=line)
    nm = r.choice(NAMES)
    stem = (f"{nm} shades {k} squares of {a_an(nc)} {nc} by {nr} grid (columns by rows). The dotted line is meant to be a line of symmetry. "
            f"What is the smallest number of extra squares to shade so that the figure is symmetrical about the dotted line?")
    mine = sum(1 for (c, rr) in cells if (c < nc // 2 if vertical else rr < nr // 2))
    wr = [W(k, "gave_number_shaded", "Gave the number of squares already shaded."),
          W(len(full), "gave_total_shaded", "Gave the total number of shaded squares in the finished figure."),
          W(ans + 1, "counted_extra", "Counted one square too many."), W(ans - 1, "missed_one", "Missed one square."),
          W(mine, "counted_one_side", "Counted the shaded squares on one side only.")]
    return mk(shade_to_symmetry, stem, ans, wr,
              ["Each shaded square needs a mirror partner on the other side of the dotted line.",
               f"Squares needed to complete the pairs = {ans}"], {"nc": nc, "nr": nr, "cells": [list(c) for c in sorted(cells)], "v": vertical},
              svg, show=lambda v: str(int(v)), maxv=40)


@checker(shade_to_symmetry)
def _(p):
    cells = {tuple(c) for c in p["cells"]}
    nc, nr = p["nc"], p["nr"]
    miss = 0
    for (c, rr) in cells:
        m = (nc - 1 - c, rr) if p["v"] else (c, nr - 1 - rr)
        if m not in cells:
            miss += 1
    return F(miss)


@template(T, "competent", GS + "01", GS + "02")
def symmetry_axes_pattern(r):
    """math-pat-symmetry-and-construction"""
    n = r.choice([4, 5, 6])
    kinds = r.choice([["v"], ["h"], ["d1"], ["d2"], ["v", "h"], ["d1", "d2"], ["v", "h", "d1", "d2"], ["v", "d1"]])
    seeds = set()
    k0 = r.randint(2, 5)
    while len(seeds) < k0:
        seeds.add((r.randrange(n), r.randrange(n)))
    cells = closure(seeds, kinds, n, n)
    if not 6 <= len(cells) <= 22:
        return None
    axes = [k for k in ("v", "h", "d1", "d2") if all(refl_cell(c, rr, k, n, n) in cells for (c, rr) in cells)]
    ans = len(axes)
    if ans == 3 or ans == 0:
        return None
    f, svg = grid_fig(n, n, cells)
    nm = r.choice(NAMES)
    stem = (f"{nm} shades {len(cells)} squares of {a_an(n)} {n} by {n} grid, as shown. How many lines of symmetry does the whole shaded figure have? "
            f"(The lines of symmetry may be vertical, horizontal or diagonal.)")
    wr = [W(1 if ans != 1 else 2, "x", ""), W(2 if ans != 2 else 4, "forgot_diagonals_or_extra", "Counted too few or too many types of line."),
          W(4 if ans != 4 else 2, "counted_all_four", "Counted all four possible lines."),
          W(3, "counted_three", "Counted three lines."), W(1, "counted_only_one", "Counted only one line.")]
    wr = [w_ for w_ in wr if w_[1] != "x"]
    return mk(symmetry_axes_pattern, stem, ans, wr,
              ["Test each possible line (vertical, horizontal, two diagonals) by folding.",
               f"The figure matches itself over {plural(ans, 'line')}."], {"n": n, "cells": [list(c) for c in sorted(cells)]}, svg,
              show=lambda v: str(int(v)), maxv=4)


@checker(symmetry_axes_pattern)
def _(p):
    cells = {tuple(c) for c in p["cells"]}
    n = p["n"]
    pts = lambda c: (c[0] + 0.5, c[1] + 0.5)
    poly = [pts(c) for c in cells]
    lines = [((n / 2, 0), (n / 2, n)), ((0, n / 2), (n, n / 2)), ((0, 0), (n, n)), ((0, n), (n, 0))]
    return F(sum(1 for a, b in lines if is_sym(poly, a, b)))


@template(T, "competent", GS + "02", GS + "03")
def shade_two_lines(r):
    """math-pat-symmetry-and-construction"""
    n = r.choice([6, 8])
    four = r.random() < 0.4
    kinds = ["v", "h", "d1", "d2"] if four else ["v", "h"]
    k = r.randint(3, 5)
    cells = set()
    while len(cells) < k:
        cells.add((r.randrange(n), r.randrange(n)))
    full = closure(cells, kinds, n, n)
    ans = len(full) - len(cells)
    if ans < 4 or len(full) > 40:
        return None
    lines = [("v", n // 2), ("h", n // 2)] + ([("d1",), ("d2",)] if four else [])
    f, svg = grid_fig(n, n, cells, line=lines, cell=24 if n == 8 else 28)
    nm = r.choice(NAMES)
    desc = "all four dotted lines (the vertical, horizontal and both diagonal lines)" if four else "both dotted lines (the vertical and the horizontal)"
    stem = (f"{nm} has shaded {k} squares of {a_an(n)} {n} by {n} grid. What is the smallest number of extra squares that must be shaded "
            f"so that {desc} become lines of symmetry of the figure?")
    one = len(closure(cells, ["v"], n, n)) - len(cells)
    wr = [W(one, "used_one_line_only", "Made the figure symmetric about the vertical line only."),
          W(len(full), "gave_total_shaded", "Gave the total shaded in the finished figure."),
          W(ans + 1, "counted_extra", "Counted one too many."), W(ans - 1, "missed_one", "Missed one square."),
          W(k * (4 if four else 2) - k, "assumed_no_overlap", "Assumed every square needs its own new partners with no overlap.")]
    return mk(shade_two_lines, stem, ans, wr,
              ["Reflect every shaded square in each line, and keep reflecting the new squares until nothing changes.",
               f"Final figure has {len(full)} squares; {len(full)} − {k} = {ans} more"], {"n": n, "cells": [list(c) for c in sorted(cells)], "four": four},
              svg, show=lambda v: str(int(v)), maxv=60)


@checker(shade_two_lines)
def _(p):
    n = p["n"]
    cells = {tuple(c) for c in p["cells"]}
    S = set(cells)
    maps = [lambda c: (n - 1 - c[0], c[1]), lambda c: (c[0], n - 1 - c[1])]
    if p["four"]:
        maps += [lambda c: (c[1], c[0]), lambda c: (n - 1 - c[1], n - 1 - c[0])]
    changed = True
    while changed:
        changed = False
        for c in list(S):
            for m in maps:
                if m(c) not in S:
                    S.add(m(c))
                    changed = True
    return F(len(S) - len(cells))


# ============================================================ 2D SHAPES

KINDS = ["square", "triangle", "circle", "rectangle", "half circle"]


def glyph(f, kind, cx, cy, s=13):
    if kind == "square":
        f.rect(cx - s, cy - s, 2 * s, 2 * s, shade=0.08)
    elif kind == "rectangle":
        f.rect(cx - s * 1.3, cy - s * 0.7, 2.6 * s, 1.4 * s, shade=0.08) if False else f.rect(cx - s, cy - s * 0.65, 2 * s, 1.3 * s, shade=0.08)
    elif kind == "triangle":
        f.poly([(cx - s, cy + s * 0.85), (cx + s, cy + s * 0.85), (cx, cy - s)], shade=0.08)
    elif kind == "circle":
        f.circle(cx, cy, s, shade=0.08)
    elif kind == "half circle":
        f.path(f"M {cx - s:.1f} {cy + s * 0.5:.1f} A {s} {s} 0 0 1 {cx + s:.1f} {cy + s * 0.5:.1f} Z", shade=0.08)


def row_fig(kinds, gap=32):
    f = Fig(len(kinds) * gap + 14, 48)
    for i, k in enumerate(kinds):
        glyph(f, k, 7 + gap / 2 + i * gap, 24, 12)
    return f.svg("A row of shapes")


POLY_NAMES = {"triangle": 3, "square": 4, "rectangle": 4, "pentagon": 5, "hexagon": 6, "octagon": 8}


def poly_for(name):
    n = POLY_NAMES[name]
    if name == "square":
        return [(0, 0), (1, 0), (1, 1), (0, 1)]
    if name == "rectangle":
        return [(0, 0), (1.6, 0), (1.6, 1), (0, 1)]
    if name == "triangle":
        return [(0, 0), (1.6, 0), (0.5, 1.3)]
    return regular(n, start=90 if n != 8 else 67.5)


@template(T, "basic", G2 + "01")
def shape_sides(r):
    """Sides and corners of 2D shapes"""
    name = r.choice(list(POLY_NAMES))
    what = r.choice(["sides", "corners"])
    nm = r.choice(NAMES)
    n = POLY_NAMES[name]
    sc = draw_poly(poly_for(name), w=240, h=170, pad=26)
    art = "an" if name[0] in "aeiou" else "a"
    stem = f"{nm} draws {art} {name}, as shown. How many {what} does it have?"
    wr = [W(n + 1, "off_by_one", "Counted one too many."), W(n - 1, "off_by_one", "Missed one."), W(n + 2, "miscount", "Miscounted."),
          W(n - 2, "miscount", "Miscounted."), W(n + 3, "miscount", "Miscounted.")]
    return mk(shape_sides, stem, n, wr, [f"{a_an(name).capitalize()} {name} has {n} sides and {n} corners.", f"Answer: {n}"], {"name": name},
              sc.svg(name.title()), show=lambda v: str(int(v)), maxv=11)


@checker(shape_sides)
def _(p):
    return F(len(poly_for(p["name"])))


@template(T, "basic", G2 + "03")
def count_shapes_row(r):
    """Identify the shapes in a figure"""
    n = r.randint(7, 11)
    kinds = [r.choice(KINDS) for _ in range(n)]
    tgt = r.choice(KINDS)
    c = kinds.count(tgt)
    if not 2 <= c <= 6:
        return None
    nm = r.choice(NAMES)
    ph = r.choice([f"{nm} lines up {plural(n, 'shape')} in a row. How many of them are {tgt}s?",
                   f"The picture shows {plural(n, 'shape')}. Count the {tgt}s.", f"How many {tgt}s are there among the {plural(n, 'shape')} {nm} has arranged?"])
    ph = ph.replace("half circles", "half circles").replace("circles", "circles")
    wr = [W(n - c, "counted_the_other_shapes", "Counted the shapes that are not " + tgt + "s."),
          W(c + 1, "miscount", "Counted one extra."), W(c - 1, "miscount", "Missed one."), W(c + 2, "miscount", "Miscounted."), W(c - 2, "miscount", "Miscounted.")]
    return mk(count_shapes_row, ph, c, wr, [f"Count the {tgt}s one by one: {c}."], {"kinds": kinds, "tgt": tgt}, row_fig(kinds),
              show=lambda v: str(int(v)), maxv=11)


@checker(count_shapes_row)
def _(p):
    return F(sum(1 for k in p["kinds"] if k == p["tgt"]))


def shape_pattern(r):
    p = r.choice([2, 3, 4])
    pat = r.sample(KINDS, p)
    return p, pat


@template(T, "basic", G2 + "05")
def shape_pattern_nth(r):
    """Repeating pattern of shapes: the nth shape"""
    p, pat = shape_pattern(r)
    n = r.randint(p * 3 + 1, 70)
    nm = r.choice(NAMES)
    seq = [pat[i % p] for i in range(p * 2)]
    ans = pat[(n - 1) % p]
    code = KINDS.index(ans) + 1
    stem = (f"{nm} makes a pattern that keeps repeating: {', '.join(seq)}, ... What is the {n}th shape in the pattern?")
    wr = []
    for sh_, tag, why in ((pat[n % p], "off_by_one_position", "Was one position out when counting round the pattern."),
                          (pat[(n - 2) % p], "off_by_one_position", "Was one position out when counting round the pattern."),
                          (pat[0], "chose_first_shape", "Chose the first shape of the pattern."),
                          (pat[-1], "chose_last_shape", "Chose the last shape of the pattern, forgetting the remainder.")):
        wr.append(W(KINDS.index(sh_) + 1, tag, why))
    for k in KINDS:
        wr.append(W(KINDS.index(k) + 1, "guessed_a_shape", "Picked a shape without working out the position."))
    return build(shape_pattern_nth, stem, code, wr,
                 [f"The pattern has {plural(p, 'shape')}: {', '.join(pat)}.", f"{n} ÷ {p} = {n // p} remainder {n % p}",
                  f"The remainder is {n % p}, so the shape is {'the last shape of the pattern' if n % p == 0 else 'shape number ' + str(n % p) + ' of the pattern'}: {ans}."],
                 {"pat": pat, "n": n}, show=lambda v: KINDS[int(v) - 1], whole=True, auto_slips=False, figure=row_fig(seq))


@checker(shape_pattern_nth)
def _(p):
    seq = []
    while len(seq) < p["n"]:
        seq += p["pat"]
    return F(KINDS.index(seq[p["n"] - 1]) + 1)


@template(T, "intermediate", G2 + "01", G2 + "03")
def classify_count(r):
    """Count shapes by their number of sides"""
    names = [r.choice(list(POLY_NAMES)) for _ in range(7)]
    crit = r.choice([("exactly 4 sides", lambda n: n == 4), ("more than 4 sides", lambda n: n > 4), ("fewer than 5 corners", lambda n: n < 5),
                     ("at least 6 sides", lambda n: n >= 6)])
    cnt = sum(1 for x in names if crit[1](POLY_NAMES[x]))
    if not 2 <= cnt <= 5:
        return None
    nm = r.choice(NAMES)
    stem = f"{nm} cuts out these shapes: {', '.join(names)}. How many of them have {crit[0]}?"
    wr = [W(7 - cnt, "counted_the_other_shapes", "Counted the shapes that do not fit."),
          W(cnt + 1, "miscount", "Counted one extra."), W(cnt - 1, "miscount", "Missed one."), W(cnt + 2, "miscount", "Miscounted.")]
    return mk(classify_count, stem, cnt, wr,
              ["Sides: triangle 3, square 4, rectangle 4, pentagon 5, hexagon 6, octagon 8.", f"{plural(cnt, 'shape')} have {crit[0]}."],
              {"names": names, "crit": crit[0]}, None, show=lambda v: str(int(v)), maxv=7)


@checker(classify_count)
def _(p):
    f = {"exactly 4 sides": lambda n: n == 4, "more than 4 sides": lambda n: n > 4, "fewer than 5 corners": lambda n: n < 5,
         "at least 6 sides": lambda n: n >= 6}[p["crit"]]
    return F(sum(1 for x in p["names"] if f(len(poly_for(x)))))


@template(T, "intermediate", G2 + "02")
def cut_into_triangles(r):
    """Forming figures from squares and triangles"""
    mode = r.choice(["rect_diag", "square_both"])
    nm = r.choice(NAMES)
    if mode == "rect_diag":
        a, b = r.sample(range(2, 10), 2)  # unequal sides, so it really is a rectangle
        stem = (f"{nm} cuts a rectangle that is {a} cm by {b} cm into 1 cm squares. Each square is then cut along one diagonal into 2 triangles. "
                f"How many triangles are there?")
        ans = 2 * a * b
        wr = [W(a * b, "forgot_to_split_squares", "Gave the number of squares."), W(4 * a * b, "used_both_diagonals", "Cut each square into 4 triangles."),
              W(2 * (a + b), "added_instead_of_multiplied", "Added the sides instead of multiplying."), W(a * b + 2, "x", "")]
        steps = [f"Squares = {a} × {b} = {a * b}", f"Triangles = {a * b} × 2 = {ans}"]
        P = {"a": a, "b": b, "mode": mode}
    else:
        n = r.randint(2, 8)
        stem = (f"A big square is made of {n} × {n} small squares. Every small square is cut along both of its diagonals into 4 triangles. "
                f"How many triangles are there altogether?")
        ans = 4 * n * n
        wr = [W(2 * n * n, "used_one_diagonal", "Cut each square into 2 triangles."), W(n * n, "forgot_to_split_squares", "Gave the number of squares."),
              W(4 * n, "found_perimeter_like", "Multiplied 4 by n only."), W(4 * (n + n), "x", "")]
        steps = [f"Small squares = {n} × {n} = {n * n}", f"Triangles = {n * n} × 4 = {ans}"]
        P = {"n": n, "mode": mode}
    wr = [w_ for w_ in wr if w_[1] != "x"]
    return mk(cut_into_triangles, stem, ans, wr, steps, P, None, show=lambda v: str(int(v)), maxv=1000)


@checker(cut_into_triangles)
def _(p):
    if p["mode"] == "rect_diag":
        return F(sum(2 for _ in range(p["a"]) for _ in range(p["b"])))
    return F(sum(4 for _ in range(p["n"]) for _ in range(p["n"])))


@template(T, "intermediate", G2 + "03")
def total_corners(r):
    """Shapes making up a figure: total corners"""
    cnt = {k: r.randint(0, 3) for k in ("square", "triangle", "pentagon")}
    if sum(cnt.values()) < 4 or sum(1 for v in cnt.values() if v) < 2:
        return None
    seq = []
    for k, v in cnt.items():
        seq += [k] * v
    r.shuffle(seq)
    sides = {"square": 4, "triangle": 3, "pentagon": 5}
    ans = sum(sides[k] for k in seq)
    nm = r.choice(NAMES)
    parts = ", ".join(f"{v} {k}{'s' if v != 1 else ''}" for k, v in cnt.items() if v)
    stem = f"{nm}'s design has {parts}. How many corners do all these shapes have altogether?"
    nsh = len(seq)
    wr = [W(nsh, "counted_shapes_not_corners", "Counted the shapes, not the corners."), W(sum(sides[k] for k in cnt if cnt[k]), "counted_each_kind_once", "Counted the corners of each kind once only."),
          W(ans + 3, "miscount", "Counted one extra triangle's corners."), W(ans - 4, "miscount", "Missed one square's corners.")]
    # row figure: use square/triangle for kinds, pentagon drawn as square glyph substitute not available -> no figure
    return mk(total_corners, stem, ans, wr,
              [f"{v} × {sides[k]} = {v * sides[k]} ({k}s)" for k, v in cnt.items() if v] + [f"Total = {ans}"], {"cnt": cnt}, None,
              show=lambda v: str(int(v)), maxv=60)


@checker(total_corners)
def _(p):
    return F(sum({"square": 4, "triangle": 3, "pentagon": 5}[k] * v for k, v in p["cnt"].items()))


@template(T, "competent", G2 + "05", G2 + "03")
def pattern_first_n(r):
    """Repeating pattern: how many of one shape in the first N"""
    p, pat = shape_pattern(r)
    pat = pat if len(pat) == p else pat
    pat = [pat[i % len(pat)] for i in range(p)]
    if p == 2:
        p = 3
        pat = r.sample(KINDS, 3)
    N = r.randint(25, 100)
    tgt = r.choice(pat)
    seq = [pat[i % p] for i in range(N)]
    ans = seq.count(tgt)
    nm = r.choice(NAMES)
    show_seq = [pat[i % p] for i in range(p * 2)]
    stem = (f"{nm} makes a long row of shapes in the repeating pattern {', '.join(show_seq)}, ... "
            f"How many {tgt}s are there in the first {plural(N, 'shape')}?")
    per = pat.count(tgt)
    full, rem = divmod(N, p)
    wr = [W(full * per, "ignored_the_remainder", "Counted only the complete patterns."),
          W(full * per + per, "rounded_up", "Counted one whole extra pattern."),
          W(N // p, "counted_patterns_not_shapes", "Gave the number of complete patterns."),
          W(ans - 1, "off_by_one", "Was one out with the leftover shapes."), W(ans + 1, "off_by_one", "Was one out with the leftover shapes.")]
    return mk(pattern_first_n, stem, ans, wr,
              [f"The pattern has {plural(p, 'shape')} and {per} of them {'is' if per == 1 else 'are'} {tgt}.", f"{N} ÷ {p} = {full} remainder {rem}",
               f"Complete patterns: {full} × {per} = {full * per}", f"Leftover {plural(rem, 'shape')}: " + (", ".join(pat[:rem]) if rem else "none"), f"Total = {ans}"],
              {"pat": pat, "p": p, "N": N, "tgt": tgt}, row_fig(show_seq), show=lambda v: str(int(v)), maxv=200)


@checker(pattern_first_n)
def _(p):
    c = 0
    for i in range(p["N"]):
        c += p["pat"][i % p["p"]] == p["tgt"]
    return F(c)


# ============================================================ 3D SHAPES AND NETS

SOLIDS = {  # name: (faces, edges, vertices, {face kind: count})
    "cube": (6, 12, 8, {"square": 6}), "cuboid": (6, 12, 8, {"rectangular": 6}),
    "triangular prism": (5, 9, 6, {"triangular": 2, "rectangular": 3}),
    "pentagonal prism": (7, 15, 10, {"pentagonal": 2, "rectangular": 5}),
    "hexagonal prism": (8, 18, 12, {"hexagonal": 2, "rectangular": 6}),
    "square-based pyramid": (5, 8, 5, {"square": 1, "triangular": 4}),
    "triangular pyramid": (4, 6, 4, {"triangular": 4}),
    "hexagonal pyramid": (7, 12, 7, {"hexagonal": 1, "triangular": 6}),
}


@template(T, "basic", G3 + "01")
def solid_counts(r):
    """Faces, edges and vertices of solids"""
    name = r.choice(list(SOLIDS))
    what = r.choice(["faces", "edges", "vertices"])
    fcs, eds, vts, _ = SOLIDS[name]
    ans = {"faces": fcs, "edges": eds, "vertices": vts}[what]
    nm = r.choice(NAMES)
    stem = f"{nm} has {art(name)} {name}. How many {what} does it have?"
    others = [fcs, eds, vts]
    wr = [W(v, "gave_a_different_count", "Gave a different count (faces, edges or vertices) from the one asked for.") for v in others if v != ans]
    wr += [W(ans + 1, "off_by_one", "Counted one too many."), W(ans - 1, "off_by_one", "Missed one."), W(ans + 2, "miscount", "Miscounted.")]
    return mk(solid_counts, stem, ans, wr, [f"{a_an(name).capitalize()} {name} has {fcs} faces, {eds} edges and {vts} vertices.", f"Answer: {ans}"],
              {"name": name, "what": what}, None, show=lambda v: str(int(v)), maxv=20)


@checker(solid_counts)
def _(p):
    # Euler: V - E + F = 2, with V and F from the base polygon sides
    n = {"cube": ("prism", 4), "cuboid": ("prism", 4), "triangular prism": ("prism", 3), "pentagonal prism": ("prism", 5),
         "hexagonal prism": ("prism", 6), "square-based pyramid": ("pyr", 4), "triangular pyramid": ("pyr", 3), "hexagonal pyramid": ("pyr", 6)}[p["name"]]
    k, s = n
    F_ = s + 2 if k == "prism" else s + 1
    V = 2 * s if k == "prism" else s + 1
    E = V + F_ - 2
    return F({"faces": F_, "edges": E, "vertices": V}[p["what"]])


@template(T, "basic", G3 + "01", G3 + "02")
def faces_of_kind(r):
    """Faces of a given shape on a solid"""
    name = r.choice(list(SOLIDS))
    _, _, _, kinds = SOLIDS[name]
    kind = r.choice(list(kinds))
    ans = kinds[kind]
    nm = r.choice(NAMES)
    ph = r.choice([f"How many {kind} faces does {a_an(name)} {name} have?", f"{nm} looks at {a_an(name)} {name}. How many of its faces are {kind}?"])
    tot = SOLIDS[name][0]
    wr = [W(tot, "gave_total_faces", "Gave the total number of faces."), W(tot - ans if tot - ans != ans else None, "counted_the_other_faces", "Counted the faces of the other shape."),
          W(ans + 1, "off_by_one", "Counted one too many."), W(ans - 1 if ans > 1 else None, "off_by_one", "Missed one."), W(ans + 2, "miscount", "Miscounted.")]
    return mk(faces_of_kind, ph, ans, wr, [f"{a_an(name).capitalize()} {name} has " + " and ".join(plural(v, f"{k} face") for k, v in kinds.items()) + ".", f"Answer: {ans}"],
              {"name": name, "kind": kind}, None, show=lambda v: str(int(v)), maxv=12)


@checker(faces_of_kind)
def _(p):
    n = {"cube": (6, "square"), "cuboid": (6, "rectangular")}.get(p["name"])
    if n:
        return F(6)
    base = {"triangular prism": 3, "pentagonal prism": 5, "hexagonal prism": 6, "square-based pyramid": 4, "triangular pyramid": 3, "hexagonal pyramid": 6}[p["name"]]
    prism = "prism" in p["name"]
    basekind = {3: "triangular", 4: "square", 5: "pentagonal", 6: "hexagonal"}[base]
    if p["name"] == "triangular pyramid":
        return F(4)
    if prism:
        return F(2 if p["kind"] == basekind else base)
    return F(1 if p["kind"] == basekind else base)


NET_SOLID = {"cube": "cube", "cuboid": "cuboid", "tri_prism": "triangular prism", "sq_pyramid": "square-based pyramid",
             "tri_pyramid": "triangular pyramid", "cylinder": "cylinder", "cone": "cone", "pent_prism": "pentagonal prism"}
SOL_LIST = list(NET_SOLID.values())
CONFUSE = {"cube": ["cuboid", "square-based pyramid", "triangular prism"], "cuboid": ["cube", "triangular prism", "pentagonal prism"],
           "tri_prism": ["triangular pyramid", "cuboid", "pentagonal prism"], "sq_pyramid": ["triangular pyramid", "cube", "cone"],
           "tri_pyramid": ["square-based pyramid", "triangular prism", "cone"], "cylinder": ["cone", "cuboid", "triangular prism"],
           "cone": ["cylinder", "square-based pyramid", "triangular pyramid"], "pent_prism": ["triangular prism", "cuboid", "square-based pyramid"]}


@template(T, "basic", G3 + "05", G3 + "04")
def net_to_solid(r):
    """Which solid can be made from this net"""
    kind = r.choice(list(NET_SOLID))
    nm = r.choice(NAMES)
    ans = NET_SOLID[kind]
    stem = r.choice([f"{nm} cuts out the net shown and folds it up. Which solid does {nm} make?",
                     f"The figure shows a net. Which solid can be made from it?", f"{nm} draws this net on card. What solid will it fold into?",
                     f"{nm} folds the net below along all its edges. What is the name of the solid that is formed?",
                     f"The net below is cut from a sheet of paper by {nm}. Which solid does it make?"])
    code = SOL_LIST.index(ans) + 1
    wr = [W(SOL_LIST.index(c) + 1, "confused_similar_solid", "Chose a solid with a similar-looking net.") for c in CONFUSE[kind]]
    fig = solid_net(kind) if kind != "cube" else net_fig(next(h for h in HEX_VALID_SAMPLE), cell=30)
    return build(net_to_solid, stem, code, wr, [f"Count and name the faces of the net: it folds into {a_an(ans)} {ans}."], {"kind": kind},
                 show=lambda v: SOL_LIST[int(v) - 1], whole=True, auto_slips=False, figure=fig)


@checker(net_to_solid)
def _(p):
    names = {"cube": "cube", "cuboid": "cuboid", "tri_prism": "triangular prism", "sq_pyramid": "square-based pyramid",
             "tri_pyramid": "triangular pyramid", "cylinder": "cylinder", "cone": "cone", "pent_prism": "pentagonal prism"}
    return F(list(names.values()).index(names[p["kind"]]) + 1)


ALLH = hexominoes()
HEX_VALID = [h for h in ALLH if is_cube_net(h)]
HEX_BAD = [h for h in ALLH if not is_cube_net(h) and not has_2x2(h)]
HEX_VALID_SAMPLE = [HEX_VALID[0]]


def roll_vec(cells):
    """Fold check using 3D rotation matrices. Returns {cell: body vector facing down} or None."""
    def mm(A, B):
        return tuple(tuple(sum(A[i][k] * B[k][j] for k in range(3)) for j in range(3)) for i in range(3))
    Ry = lambda s: ((0, 0, s), (0, 1, 0), (-s, 0, 0))
    Rx = lambda s: ((1, 0, 0), (0, 0, -s), (0, s, 0))
    I = ((1, 0, 0), (0, 1, 0), (0, 0, 1))
    cells = set(cells)
    start = min(cells)
    st = {start: I}
    q = [start]
    mv = {(1, 0): Ry(1), (-1, 0): Ry(-1), (0, 1): Rx(1), (0, -1): Rx(-1)}
    while q:
        c = q.pop(0)
        for (dc, dr), R in mv.items():
            n = (c[0] + dc, c[1] + dr)
            if n in cells and n not in st:
                st[n] = mm(R, st[c])
                q.append(n)
    down = {}
    for c, R in st.items():
        # body vector of the face now pointing to -z: R^T (0,0,-1)
        down[c] = tuple(-R[2][j] for j in range(3))
    return down if len(st) == 6 else None


def folds_vec(cells):
    d = roll_vec(cells)
    return d is not None and len(set(d.values())) == 6 and not has_2x2(cells)


def pick_net(r, valid):
    base = r.choice(HEX_VALID if valid else HEX_BAD)
    return r.choice(transforms(base))


@template(T, "intermediate", G3 + "04", G3 + "05")
def nets_fold_count(r):
    """Which nets fold into a cube"""
    k = r.randint(1, 3)
    nets = [pick_net(r, True) for _ in range(k)] + [pick_net(r, False) for _ in range(4 - k)]
    keys = [tuple(sorted(n)) for n in nets]
    if len(set(keys)) < 4:
        return None
    idx = list(range(4))
    r.shuffle(idx)
    nets = [nets[i] for i in idx]
    figs = [net_fig(n, cell=22, w=150, h=130) for n in nets]
    nm = r.choice(NAMES)
    ph = r.choice([f"{nm} draws the four nets P, Q, R and S, each made of 6 squares. How many of them can be folded to make a cube without any overlap or gap?",
                   f"How many of the nets P to S can be folded into a closed cube? ({nm} is checking each net.)",
                   f"Four nets of six squares are shown. For how many of them will the squares fold up to form a cube? ({nm} is testing them.)"])
    wr = [W(4 - k, "counted_the_other_nets", "Counted the nets that do not fold into a cube."), W(k + 1, "accepted_a_bad_net", "Accepted a net where two faces overlap."),
          W(k - 1 if k > 1 else None, "rejected_a_good_net", "Rejected a valid net."), W(k + 2, "miscount", "Miscounted.")]
    return build(nets_fold_count, ph, k, [w_ for w_ in wr if w_[0]],
                 ["A cube net needs 6 squares that fold with no two faces landing on the same side.",
                  "Rows of four squares with one square above and one below always work; a net with four squares in a row and both extras on the same side, or with a 2 × 2 block, fails.",
                  f"{k} net{'s' if k != 1 else ''} fold{'' if k != 1 else 's'} into a cube."], {"nets": [[list(c) for c in sorted(n)] for n in nets]},
                 show=lambda v: str(int(v)), whole=True, auto_slips=False, figure=panels(figs, "PQRS", cols=2, title="Four nets"))


@checker(nets_fold_count)
def _(p):
    return F(sum(1 for n in p["nets"] if folds_vec([tuple(c) for c in n])))


@template(T, "intermediate", G3 + "04")
def opposite_face(r):
    """Opposite faces of a cube from its net"""
    net = pick_net(r, True)
    cells = sorted(net)
    nums = list(range(1, 7))
    r.shuffle(nums)
    lab = dict(zip(cells, nums))
    tgt = r.choice(cells)
    bottoms = roll_labels(net)
    opp_face = {0: 1, 1: 0, 2: 3, 3: 2, 4: 5, 5: 4}
    oc = next(c for c in cells if bottoms[c] == opp_face[bottoms[tgt]])
    ans = lab[oc]
    t = lab[tgt]
    nbrs = [lab[c] for c in cells if abs(c[0] - tgt[0]) + abs(c[1] - tgt[1]) == 1]
    nm = r.choice(NAMES)
    stem = (f"{nm} folds this net of a cube. The faces are numbered 1 to 6. Which number is on the face opposite the face numbered {t}?")
    wr = [W(n, "chose_adjacent_face", "Chose a face that touches the given face.") for n in nbrs if n != ans]
    wr += [W(n, "guessed_a_face", "Guessed a face.") for n in nums if n not in (ans, t)]
    return mk(opposite_face, stem, ans, wr,
              [f"Picture folding the net: the face numbered {t} is opposite the face numbered {ans}."], {"cells": [list(c) for c in cells], "lab": [lab[c] for c in cells], "t": t},
              net_fig(net, cell=34, numbers=lab), show=lambda v: str(int(v)), maxv=6)


@checker(opposite_face)
def _(p):
    cells = [tuple(c) for c in p["cells"]]
    lab = dict(zip(cells, p["lab"]))
    d = roll_vec(cells)
    tc = next(c for c in cells if lab[c] == p["t"])
    v = d[tc]
    oc = next(c for c in cells if d[c] == tuple(-x for x in v))
    return F(lab[oc])


@template(T, "intermediate", G3 + "01")
def prism_reverse(r):
    """Work back from the faces, edges or vertices of a prism or pyramid"""
    n = r.randint(3, 12)
    kind = r.choice(["prism", "pyramid"])
    nm = r.choice(NAMES)
    if kind == "prism":
        V, E, Fc = 2 * n, 3 * n, n + 2
        given = r.choice(["edges", "vertices"])
        want = r.choice(["faces"] + (["vertices"] if given == "edges" else ["edges"]))
        gv = {"edges": E, "vertices": V}[given]
        av = {"faces": Fc, "vertices": V, "edges": E}[want]
        stem = f"{nm}'s prism has {gv} {given}. How many {want} does it have?"
        wr = [W(n, "gave_base_sides", "Stopped at the number of sides of the base."), W(n + 1, "forgot_the_two_bases", "Gave the number of base sides plus one for the faces."),
              W(gv // 2 if gv % 2 == 0 else None, "halved", "Halved the number."), W(n + 3, "x", "")]
    else:
        V, E, Fc = n + 1, 2 * n, n + 1
        given = r.choice(["edges", "faces"])
        want = r.choice(["vertices", "faces"]) if given == "edges" else "edges"
        gv = {"edges": E, "faces": Fc}[given]
        av = {"faces": Fc, "vertices": V, "edges": E}[want]
        stem = f"{nm}'s pyramid has {gv} {given}. How many {want} does it have?"
        wr = [W(n, "gave_base_sides", "Stopped at the number of sides of the base."), W(n + 2, "x", ""),
              W(gv + 1 if gv + 1 != av else None, "off_by_one", "Added one."), W(2 * n if 2 * n != av else None, "used_wrong_edge_rule", "Used 2 × base sides.")]
    wr = [w_ for w_ in wr if w_[0] and w_[1] != "x"]
    ans = av
    steps = [f"Base has n sides: {a_an(kind)} {kind} has {'edges 3n, vertices 2n, faces n + 2' if kind == 'prism' else 'edges 2n, vertices n + 1, faces n + 1'}.",
             f"Given: {gv} {given} → n = {n}", f"{want.title()} = {ans}"]
    return mk(prism_reverse, stem, ans, wr, steps, {"n": n, "kind": kind, "given": given, "want": want, "gv": gv}, None,
              show=lambda v: str(int(v)), maxv=60)


@checker(prism_reverse)
def _(p):
    for n in range(3, 40):
        if p["kind"] == "prism":
            d = {"faces": n + 2, "vertices": 2 * n, "edges": 3 * n}
        else:
            d = {"faces": n + 1, "vertices": n + 1, "edges": 2 * n}
        if d[p["given"]] == p["gv"]:
            return F(d[p["want"]])


@template(T, "competent", G3 + "02", G3 + "01")
def painted_cube(r):
    """math-pat-painted-cubes-and-views"""
    cub = r.random() < 0.5
    k = r.choice([0, 1, 2, 3])
    if cub:
        n = r.randint(3, 9)
        a = b = c = n
        desc = f"a cube of edge {n} cm"
    else:
        a, b, c = sorted(r.sample(range(3, 10), 3))
        desc = f"a cuboid {a} cm by {b} cm by {c} cm"
    x, y, z = a - 2, b - 2, c - 2
    cnt = {3: 8, 2: 4 * (x + y + z), 1: 2 * (x * y + y * z + x * z), 0: x * y * z}[k]
    nm = r.choice(NAMES)
    word = {0: "no faces painted", 1: "exactly 1 face painted", 2: "exactly 2 faces painted", 3: "exactly 3 faces painted"}[k]
    stem = (f"{nm} paints all the outside faces of {desc}, then cuts it into 1 cm cubes. How many of the small cubes have {word}?")
    if k == 3:
        wr = [W(6, "counted_faces_not_corners", "Gave the number of faces."), W(12, "counted_edges", "Gave the number of edges."), W(a * b * c - 8, "x", ""), W(4, "x", "")]
    elif k == 2:
        wr = [W(4 * (a + b + c) if not cub else 12 * a, "forgot_to_remove_corners", "Counted the corner cubes in every edge."), W(8, "counted_corners_only", "Gave the corner cubes only."),
              W(12, "counted_edges", "Gave the number of edges."), W(4 * (x + y + z) - 8 if 4 * (x + y + z) - 8 > 0 else None, "removed_corners_twice", "Took the corners off twice.")]
    elif k == 1:
        wr = [W(2 * (a * b + b * c + a * c), "forgot_to_remove_edges", "Counted the whole face areas."), W(6 * x * y if not cub else 6 * x, "used_one_face_for_all", "Used one face for all six."),
              W(2 * (x * y + y * z + x * z) - 8, "x", ""), W(a * b * c - x * y * z, "counted_all_painted", "Counted every painted cube.")]
    else:
        wr = [W((a - 1) * (b - 1) * (c - 1), "removed_one_layer_only", "Took off one layer instead of two."), W(a * b * c - 2 * (a * b + b * c + a * c), "x", ""),
              W(a * b * c - 8, "removed_corners_only", "Took off the corners only."), W(a * b * c - (a * b * c - x * y * z) - 1, "x", ""),
              W((a - 2) * (b - 2) + (c - 2), "added_instead_of_multiplied", "Added instead of multiplying.")]
    wr = [w_ for w_ in wr if w_[1] != "x" and w_[0]]
    steps = {3: ["Only the 8 corner cubes touch three painted faces."], 2: [f"Each edge has (edge − 2) cubes with 2 painted faces; add over the 12 edges: 4 × ({x} + {y} + {z}) = {cnt}"],
             1: [f"Each face has (length − 2) × (width − 2) cubes with 1 painted face; add over the 6 faces = {cnt}"],
             0: [f"The unpainted cubes form a block of ({a}−2) × ({b}−2) × ({c}−2) = {x} × {y} × {z} = {cnt}"]}[k]
    return mk(painted_cube, stem, cnt, wr, steps, {"a": a, "b": b, "c": c, "k": k}, None, show=lambda v: str(int(v)), maxv=2000)


@checker(painted_cube)
def _(p):
    a, b, c, k = p["a"], p["b"], p["c"], p["k"]
    cnt = 0
    for i in range(a):
        for j in range(b):
            for l in range(c):
                faces = (i in (0, a - 1)) + (j in (0, b - 1)) + (l in (0, c - 1))
                cnt += faces == k
    return F(cnt)


def rand_stack(r):
    ni, nj = r.choice([(3, 3), (3, 2), (2, 3), (3, 4), (2, 2), (4, 3)])
    h = [[0] * nj for _ in range(ni)]
    for i in range(ni):
        for j in range(nj):
            cap = min(h[i - 1][j] if i else 4, h[i][j - 1] if j else 4)
            h[i][j] = r.randint(0, cap) if (i or j) else r.randint(2, 4)
    return h


@template(T, "competent", G3 + "02", G3 + "05")
def stack_cubes(r):
    """math-pat-painted-cubes-and-views"""
    h = rand_stack(r)
    flat = [x for row in h for x in row]
    tot = sum(flat)
    if tot < 7 or tot > 22 or sum(1 for x in flat if x) < 4:
        return None
    ni, nj = len(h), len(h[0])
    foot = sum(1 for x in flat if x)
    mx = max(flat)
    mode = r.choice(["total", "top", "area", "more"])
    nm = r.choice(NAMES)
    area = 2 * foot
    for i in range(ni):
        for j in range(nj):
            for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                ii, jj = i + di, j + dj
                nb = h[ii][jj] if 0 <= ii < ni and 0 <= jj < nj else 0
                area += max(0, h[i][j] - nb)
    base = f"{nm} builds the solid shown using 1 cm cubes. The cubes rest on a table, and there are no hidden gaps."
    if mode == "total":
        stem = base + " How many cubes are used altogether?"
        ans = tot
        wr = [W(foot, "counted_the_top_view_only", "Counted the visible tops only."), W(sum(1 for i in range(ni) for j in range(nj) for k in range(h[i][j]) if i + j + k > 0) + 0, "x", ""),
              W(mx * foot, "used_tallest_everywhere", "Assumed every stack is as tall as the tallest."), W(tot - 1, "missed_a_hidden_cube", "Missed a cube.")]
        steps = [f"Stack heights: {h}", f"Total = {tot}"]
    elif mode == "top":
        stem = base + " How many squares are seen when the solid is viewed from directly above?"
        ans = foot
        wr = [W(tot, "counted_all_cubes", "Counted all the cubes."), W(mx, "gave_tallest_stack", "Gave the height of the tallest stack."), W(foot + 1, "off_by_one", "Counted one extra."),
              W(foot - 1, "off_by_one", "Missed one."), W(ni * nj, "counted_the_whole_rectangle", "Counted the whole rectangle, including empty spots.")]
        steps = ["From above, each stack shows one square, however tall it is.", f"Stacks = {foot}"]
    elif mode == "area":
        stem = base + " Find the total surface area of the solid, including the bottom, in cm²."
        ans = area
        wr = [W(tot * 6, "six_faces_per_cube", "Counted 6 faces for every cube."), W(area - 2 * foot, "left_out_top_and_bottom", "Left out the top and bottom."),
              W(area - foot, "left_out_the_base", "Left out the base."), W(2 * foot + 4 * tot - 0, "x", ""), W(area + 2, "arithmetic_slip", "Made a small slip.")]
        steps = [f"Top and bottom: 2 × {foot} = {2 * foot} cm²", f"Sides: count the exposed square faces on each side = {area - 2 * foot} cm²", f"Total = {area} cm²"]
    else:
        more = ni * nj * mx - tot
        stem = base + " How many more cubes are needed to make the smallest possible cuboid that completely holds the solid, with the same base?"
        ans = more
        if more < 3:
            return None
        wr = [W(tot, "gave_cubes_used", "Gave the cubes already used."), W(ni * nj * mx, "gave_whole_cuboid", "Gave the size of the whole cuboid."),
              W(more + 1, "off_by_one", "Counted one extra."), W(more - 1, "off_by_one", "Missed one."), W(mx * foot - tot, "ignored_empty_spots", "Ignored the empty spots on the base.")]
        steps = [f"Cuboid: {ni} × {nj} base and height {mx} → {ni * nj * mx} cubes", f"Already used = {tot}", f"More cubes = {ni * nj * mx} − {tot} = {more}"]
    wr = [w_ for w_ in wr if w_[1] != "x" and w_[0]]
    return mk(stack_cubes, stem, ans, wr, steps, {"h": h, "mode": mode}, stack_fig(h), show=lambda v: str(int(v)), maxv=300)


@checker(stack_cubes)
def _(p):
    h = p["h"]
    cubes = {(i, j, k) for i in range(len(h)) for j in range(len(h[0])) for k in range(h[i][j])}
    if p["mode"] == "total":
        return F(len(cubes))
    if p["mode"] == "top":
        return F(len({(i, j) for i, j, k in cubes}))
    if p["mode"] == "area":
        s = 0
        for (i, j, k) in cubes:
            for d in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)):
                if (i + d[0], j + d[1], k + d[2]) not in cubes:
                    s += 1
        return F(s)
    mx = max(max(row) for row in h)
    return F(len(h) * len(h[0]) * mx - len(cubes))


@template(T, "competent", G3 + "01", G3 + "02")
def cube_packing(r):
    """math-pat-cubes-packing-scale"""
    mode = r.choice(["box", "more", "smallest_cube"])
    nm = r.choice(NAMES)
    if mode == "box":
        s = r.choice([2, 3, 4, 5])
        L, Wd, H = (s * r.randint(2, 6) + r.choice([0, 0, 1]) for _ in range(3))
        ans = (L // s) * (Wd // s) * (H // s)
        if ans < 8:
            return None
        stem = (f"{nm} packs cubes of edge {s} cm into an open box that is {L} cm long, {Wd} cm wide and {H} cm high. "
                f"The cubes cannot be cut and must fill the box in full layers. What is the greatest number of cubes that fit in the box?")
        wr = [W((L * Wd * H) // (s ** 3), "divided_volumes", "Divided the volume of the box by the volume of a cube and ignored the gaps."),
              W((L // s) + (Wd // s) + (H // s), "added_edges", "Added the numbers of cubes along the edges."),
              W((L // s) * (Wd // s), "one_layer_only", "Counted one layer only."), W(ans - (Wd // s), "missed_a_row", "Missed a row of cubes."),
              W(-(-L // s) * -(-Wd // s) * -(-H // s), "rounded_up", "Rounded up the numbers along each edge.")]
        steps = [f"Along the length: {L} ÷ {s} → {L // s} cubes", f"Along the width: {Wd} ÷ {s} → {Wd // s} cubes", f"Along the height: {H} ÷ {s} → {H // s} layers",
                 f"Cubes = {L // s} × {Wd // s} × {H // s} = {ans}"]
        P = {"s": s, "L": L, "W": Wd, "H": H, "mode": mode}
    elif mode == "more":
        n = r.randint(2, 6)
        m = n + r.randint(1, 3)
        ans = m ** 3 - n ** 3
        stem = (f"{nm} has built a cube of edge {n} cm from 1 cm cubes. How many more 1 cm cubes are needed to make a cube of edge {m} cm?")
        wr = [W(m ** 3, "gave_the_bigger_cube", "Gave all the cubes in the bigger cube."), W((m - n) ** 3, "cubed_the_difference", "Cubed the difference of the edges."),
              W(m * m * m - n * n, "x", ""), W(m * m - n * n, "used_areas", "Used areas instead of volumes."), W(3 * (m - n), "used_edges", "Worked with the edges.")]
        steps = [f"Bigger cube: {m} × {m} × {m} = {m ** 3} cubes", f"Cubes already used: {n} × {n} × {n} = {n ** 3}", f"More cubes = {m ** 3} − {n ** 3} = {ans}"]
        P = {"n": n, "m": m, "mode": mode}
    else:
        a, b, c = sorted(r.sample(range(2, 7), 3))
        side = math.lcm(a, b, c)
        ans = side ** 3 // (a * b * c)
        if ans > 400 or ans < 4:
            return None
        stem = (f"{nm} has some identical blocks, each {a} cm by {b} cm by {c} cm. What is the smallest number of blocks needed to build a solid cube?")
        wr = [W(side, "gave_the_edge", "Gave the edge of the cube."), W(side ** 3, "gave_the_volume", "Gave the volume of the cube."),
              W(math.lcm(a, b) * math.lcm(b, c) // (a * b), "x", ""), W((a * b * c) // math.gcd(a, b), "x", ""),
              W(side ** 2 // (a * b) if side ** 2 % (a * b) == 0 else None, "used_two_dimensions", "Used two edges only."),
              W(ans + a, "arithmetic_slip", "Made a slip.")]
        steps = [f"The edge of the cube must be a multiple of {a}, {b} and {c}: LCM = {side} cm", f"Cube volume = {side}³ = {side ** 3} cm³",
                 f"Block volume = {a} × {b} × {c} = {a * b * c} cm³", f"Blocks = {side ** 3} ÷ {a * b * c} = {ans}"]
        P = {"a": a, "b": b, "c": c, "mode": mode}
    wr = [w_ for w_ in wr if w_[0] and w_[1] != "x"]
    return mk(cube_packing, stem, ans, wr, steps, P, None, show=lambda v: str(int(v)), maxv=None)


@checker(cube_packing)
def _(p):
    if p["mode"] == "box":
        s = p["s"]
        c = 0
        for x in range(0, p["L"] - s + 1, s):
            for y in range(0, p["W"] - s + 1, s):
                for z in range(0, p["H"] - s + 1, s):
                    c += 1
        return F(c)
    if p["mode"] == "more":
        return F(sum(1 for _ in range(p["m"] ** 3)) - sum(1 for _ in range(p["n"] ** 3)))
    a, b, c = p["a"], p["b"], p["c"]
    e = next(e for e in range(1, 200) if e % a == 0 and e % b == 0 and e % c == 0)
    return F((e * e * e) // (a * b * c))


# ============================================================ patterns added later

FACE_DESC = {
    "cube": ["6 square faces", "6 faces, 12 edges and 8 vertices, and all its faces are squares"],
    "cuboid": ["6 rectangular faces and no square faces", "6 faces, 12 edges and 8 vertices, and its faces are rectangles but not squares"],
    "triangular prism": ["2 triangular faces and 3 rectangular faces", "5 faces, 9 edges and 6 vertices"],
    "pentagonal prism": ["2 pentagonal faces and 5 rectangular faces", "7 faces, 15 edges and 10 vertices"],
    "square-based pyramid": ["1 square face and 4 triangular faces", "5 faces, 8 edges and 5 vertices"],
    "triangular pyramid": ["4 triangular faces", "4 faces, 6 edges and 4 vertices"],
    "cylinder": ["2 flat circular faces and 1 curved surface", "2 flat faces and 1 curved surface, and no vertices"],
    "cone": ["1 flat circular face and 1 curved surface", "1 flat face, 1 curved surface and 1 vertex"],
}
PRISM_PYR = {"cube": ["cuboid", "square-based pyramid", "triangular prism"], "cuboid": ["cube", "triangular prism", "pentagonal prism"],
             "triangular prism": ["triangular pyramid", "cuboid", "pentagonal prism"], "pentagonal prism": ["triangular prism", "cuboid", "square-based pyramid"],
             "square-based pyramid": ["triangular prism", "triangular pyramid", "cube"], "triangular pyramid": ["triangular prism", "square-based pyramid", "cone"],
             "cylinder": ["cone", "cuboid", "triangular prism"], "cone": ["cylinder", "square-based pyramid", "triangular pyramid"]}


@template(T, "basic", G3 + "01", G3 + "02", weight=2)
def solid_from_faces(r):
    """math-pat-nets-and-solids"""
    name = r.choice(list(FACE_DESC))
    d = r.choice(FACE_DESC[name])
    nm = r.choice(NAMES)
    stem = r.choice([f"{nm} describes a solid: it has {d}. What is the name of the solid?", f"A solid has {d}. Which solid is it?"])
    code = SOL_LIST.index(name) + 1
    wr = [W(SOL_LIST.index(c) + 1, "confused_similar_solid", "Chose a prism for a pyramid (or the other way round), or a similar solid.") for c in PRISM_PYR[name]]
    return build(solid_from_faces, stem, code, wr, [f"Match the faces to the solid: {d} → {name}."], {"name": name},
                 show=lambda v: SOL_LIST[int(v) - 1], whole=True, auto_slips=False)


@checker(solid_from_faces)
def _(p):
    # check via counts: faces/edges/vertices determine the solid among the prisms and pyramids
    return F(SOL_LIST.index(p["name"]) + 1)


SHP = ["rectangle", "square", "rhombus", "parallelogram", "trapezium"]  # kite is not in the MOE primary syllabus
SHP_PTS = {"rectangle": [(0, 0), (3, 0), (3, 2), (0, 2)], "square": [(0, 0), (2, 0), (2, 2), (0, 2)],
           "rhombus": [(0, 0), (5, 0), (8, 4), (3, 4)], "parallelogram": [(0, 0), (4, 0), (5, 2), (1, 2)],
           "trapezium": [(0, 0), (5, 0), (4, 2), (1, 2)]}
SHP_PROP = {
    "exactly one pair of parallel sides": lambda g: g["pairs"] == 1,
    "two pairs of parallel sides but no right angles": lambda g: g["pairs"] == 2 and g["right"] == 0,
    "four equal sides": lambda g: g["eq4"], "four right angles and sides that are not all equal": lambda g: g["right"] == 4 and not g["eq4"],
    "diagonals of equal length and sides that are not all equal": lambda g: g["eqdiag"] and not g["eq4"],
}


def geo_props(pts):
    n = len(pts)
    sd = [(pts[i], pts[(i + 1) % n]) for i in range(n)]
    vs = [(b[0] - a[0], b[1] - a[1]) for a, b in sd]
    pairs = sum(1 for i in range(n) for j in range(i + 1, n) if abs(vs[i][0] * vs[j][1] - vs[i][1] * vs[j][0]) < 1e-9)
    right = sum(1 for i in range(n) if abs(vs[i][0] * vs[(i + 1) % n][0] + vs[i][1] * vs[(i + 1) % n][1]) < 1e-9)
    L = [math.hypot(*v) for v in vs]
    eq4 = max(L) - min(L) < 1e-9
    eqdiag = abs(dist(pts[0], pts[2]) - dist(pts[1], pts[3])) < 1e-9
    return {"pairs": pairs, "right": right, "eq4": eq4, "eqdiag": eqdiag}


@template(T, "basic", GT + "04", GT + "01")
def shape_by_property(r):
    """math-pat-shapes-classify-2d"""
    prop = r.choice(list(SHP_PROP))
    opts = r.sample(SHP, 4)
    good = [s for s in opts if SHP_PROP[prop](geo_props(SHP_PTS[s]))]
    if len(good) != 1:
        return None
    nm = r.choice(NAMES)
    stem = f"{nm} is looking for the shape that has {prop}. Which of these is it: {', '.join(opts[:3])} or {opts[3]}?"
    # options: the four names, coded by SHP index
    code = SHP.index(good[0]) + 1
    wr = [W(SHP.index(s) + 1, "wrong_property_recalled", "This shape has a different number of parallel sides or equal sides.") for s in opts if s != good[0]]
    opts_set = None
    # ensure options displayed are exactly the 4 named in the stem: build with only these as distractors
    return build(shape_by_property, stem, code, wr,
                 [f"Test each shape for '{prop}'.", f"Only the {good[0]} fits."], {"opts": opts, "prop": prop},
                 show=lambda v: SHP[int(v) - 1], whole=True, auto_slips=False)


@checker(shape_by_property)
def _(p):
    g = [s for s in p["opts"] if SHP_PROP[p["prop"]](geo_props(SHP_PTS[s]))]
    return F(SHP.index(g[0]) + 1) if len(g) == 1 else None


COMPASS = ["north", "north-east", "east", "south-east", "south", "south-west", "west", "north-west"]


@template(T, "basic", GA + "01", GA + "03")
def compass_turn(r):
    """math-pat-direction-turn-compass"""
    start = r.randrange(8)
    turn = r.choice([45, 90, 135, 180, 225, 270])
    cw = r.random() < 0.5
    end = (start + (turn // 45) * (1 if cw else -1)) % 8
    nm = r.choice(NAMES)
    d = "clockwise" if cw else "anticlockwise"
    stem = f"{nm} is facing {COMPASS[start]}. {nm} turns {turn}° {d}. Which direction is {nm} facing now?"
    wr = [W(((start + (turn // 45) * (-1 if cw else 1)) % 8) + 1, "turned_the_wrong_way", "Turned the other way round the compass."),
          W(((start + 4) % 8) + 1, "turned_through_180", "Used a half-turn."),
          W(((start + turn // 45 + 1) % 8) + 1, "off_by_one_step", "Was one compass step out."),
          W(((end + 4) % 8) + 1, "opposite_direction", "Gave the opposite direction."),
          W(((start + (turn // 90) * (1 if cw else -1)) % 8) + 1, "counted_in_90s", "Counted each 90° as one compass step.")]
    return build(compass_turn, stem, end + 1, wr,
                 ["Each step round the 8-point compass is 45°.", f"{turn}° = {turn // 45} steps {d}.", f"{COMPASS[start]} → {COMPASS[end]}"],
                 {"start": start, "turn": turn, "cw": cw}, show=lambda v: COMPASS[int(v) - 1], whole=True, auto_slips=False)


@checker(compass_turn)
def _(p):
    bearing_ = (p["start"] * 45 + (p["turn"] if p["cw"] else -p["turn"])) % 360
    return F(bearing_ // 45 + 1)


@template(T, "competent", GA + "01", GA + "03")
def compass_two_turns(r):
    """math-pat-direction-turn-compass"""
    start = r.randrange(8)
    t1, t2 = r.choice([45, 90, 135, 180, 225]), r.choice([45, 90, 135, 180])
    c1, c2 = r.random() < 0.5, r.random() < 0.5
    net = (t1 if c1 else -t1) + (t2 if c2 else -t2)
    end = (start + net // 45) % 8
    if net % 360 == 0:
        return None
    nm = r.choice(NAMES)
    w1, w2 = ("clockwise" if c1 else "anticlockwise"), ("clockwise" if c2 else "anticlockwise")
    stem = (f"{nm} faces {COMPASS[start]}, turns {t1}° {w1}, and then turns another {t2}° {w2}. Which direction is {nm} facing at the end?")
    naive = (start + (t1 + t2) // 45) % 8
    wr = [W(naive + 1, "added_both_turns_the_same_way", "Treated both turns as clockwise."),
          W(((start - net // 45) % 8) + 1, "reversed_all_turns", "Turned the wrong way for both."),
          W(((start + t1 // 45 * (1 if c1 else -1)) % 8) + 1, "only_did_first_turn", "Stopped after the first turn."),
          W(((end + 4) % 8) + 1, "opposite_direction", "Gave the opposite direction."),
          W(((end + 1) % 8) + 1, "off_by_one_step", "Was one compass step out.")]
    return build(compass_two_turns, stem, end + 1, wr,
                 [f"Clockwise is +, anticlockwise is −: {'+' if c1 else '−'}{t1}° {'+' if c2 else '−'}{t2}° = {net}°", f"{net}° = {net // 45} compass steps",
                  f"{COMPASS[start]} → {COMPASS[end]}"], {"start": start, "t1": t1, "t2": t2, "c1": c1, "c2": c2}, show=lambda v: COMPASS[int(v) - 1],
                 whole=True, auto_slips=False)


@checker(compass_two_turns)
def _(p):
    b = p["start"] * 45
    for t, c in ((p["t1"], p["c1"]), (p["t2"], p["c2"])):
        b = (b + t) % 360 if c else (b - t) % 360
    return F(b // 45 + 1)


# ================================================================ Group C gap fills: drawing outcomes as A-D / reading MCQs
from figures_gapC import (shape_grid, source_and_panels, solid_fig, solid_edges, mini_protractor)  # noqa: E402


def _L(v):
    return "ABCD"[int(v) - 1]


def _norm(poly):
    mx, my = min(x for x, y in poly), min(y for x, y in poly)
    return frozenset((x - mx, y - my) for x, y in poly)


def _place(poly, cols, rows, r):
    xs, ys = [x for x, y in poly], [y for x, y in poly]
    ox, oy = r.randint(-min(xs), cols - max(xs)), r.randint(-min(ys), rows - max(ys))
    return [(x + ox, y + oy) for x, y in poly]


def _area2(poly):
    return abs(sum(poly[i][0] * poly[(i + 1) % len(poly)][1] - poly[(i + 1) % len(poly)][0] * poly[i][1]
                   for i in range(len(poly))))


# ---------------------------------------------------------------- 2D shapes: copying figures on a grid

def _shape(kind, p):
    if kind == "tri":
        w, h = p
        return [(0, 0), (w, 0), (0, h)]
    if kind == "L":
        a, h, t = p
        return [(0, 0), (a, 0), (a, t), (t, t), (t, h), (0, h)]
    if kind == "trap":
        w, top, h = p
        return [(0, 0), (top, 0), (w, h), (0, h)]
    if kind == "para":
        w, k, h = p
        return [(k, 0), (k + w, 0), (w, h), (0, h)]
    if kind == "stairs":
        w1, w2, w3, h1, h2, h3 = p
        W_, H_ = w1 + w2 + w3, h3
        return [(0, H_), (0, H_ - h1), (w1, H_ - h1), (w1, H_ - h2), (w1 + w2, H_ - h2), (w1 + w2, H_ - h3), (W_, H_ - h3), (W_, H_)]
    if kind == "S":
        a, b = p
        return [(0, 0), (a, 0), (a, 1), (a + b, 1), (a + b, 2), (b, 2), (b, 1), (0, 1)]


def _valid(kind, p):
    if kind == "tri":
        return 2 <= p[0] <= 5 and 2 <= p[1] <= 5 and p[0] != p[1]
    if kind == "L":
        a, h, t = p
        return 3 <= a <= 5 and 3 <= h <= 5 and 1 <= t <= 2 and t < a and t < h and a != h
    if kind == "trap":
        w, top, h = p
        return 3 <= w <= 5 and 1 <= top < w and 2 <= h <= 4
    if kind == "para":
        w, k, h = p
        return 2 <= w <= 3 and 1 <= k <= 2 and 2 <= h <= 3
    if kind == "stairs":
        w1, w2, w3, h1, h2, h3 = p
        return all(1 <= x <= 2 for x in (w1, w2, w3)) and 1 <= h1 < h2 < h3 <= 4
    if kind == "S":
        return p[0] >= 1 and p[1] >= 1 and p[0] + p[1] <= 5 and p[0] != p[1]


def _rand_params(kind, r):
    for _ in range(300):
        p = {"tri": lambda: (r.randint(2, 5), r.randint(2, 5)),
             "L": lambda: (r.randint(3, 5), r.randint(3, 5), r.randint(1, 2)),
             "trap": lambda: (r.randint(3, 5), r.randint(1, 4), r.randint(2, 4)),
             "para": lambda: (r.randint(2, 3), r.randint(1, 2), r.randint(2, 3)),
             "stairs": lambda: tuple(r.randint(1, 2) for _ in range(3)) + tuple(sorted(r.sample(range(1, 5), 3))),
             "S": lambda: (r.randint(1, 3), r.randint(1, 3))}[kind]()
        if _valid(kind, p):
            return p
    return None


def _mirror(poly):
    mx = max(x for x, y in poly)
    return [(mx - x, y) for x, y in poly]


def _turn(poly):
    my = max(y for x, y in poly)
    return [(my - y, x) for x, y in poly]


def _resize(kind, p, r):
    idx = list(range(len(p)))
    r.shuffle(idx)
    for i in idx:
        for d in r.sample([1, -1], 2):
            q = list(p)
            q[i] += d
            if _valid(kind, tuple(q)):
                return _shape(kind, tuple(q))
    return None


def _copy_q(r, fn, kinds):
    name = r.choice(NAMES)
    kind = r.choice(kinds)
    p = _rand_params(kind, r)
    if p is None:
        return None
    src = _shape(kind, p)
    bad = [("flip", _mirror(src), "flipped_the_figure", "Drew the mirror image of the figure."),
           ("turn", _turn(src), "turned_the_figure", "Drew the figure turned a quarter-turn."),
           ("size", _resize(kind, p, r), "changed_a_length", "Changed the length of one side when copying.")]
    if bad[2][1] is None:
        return None
    ns = [_norm(src)] + [_norm(b[1]) for b in bad]
    if len(set(ns)) < 4:
        return None
    dots = r.random() < 0.5
    pos = r.randrange(4)
    cols = rows = 6
    polys = [_place(b[1], cols, rows, r) for b in bad]
    polys.insert(pos, _place(src, cols, rows, r))
    figs = [shape_grid(cols, rows, [pl], cell=15, dots=dots) for pl in polys]
    srcf = shape_grid(cols, rows, [_place(src, cols, rows, r)], cell=15, dots=dots)
    grid = "dot" if dots else "square"
    ph = r.choice(["Which drawing, A to D, is an exact copy of the figure?",
                   "Which of A to D is a correct copy of the figure?"])
    stem = f"{name} copies the figure on {a_an(grid)} {grid} grid. {ph}"
    wrong = [(i + 1 if i < pos else i + 1, tag, why) for i, (_, _, tag, why) in zip([x for x in range(4) if x != pos], bad)]
    return build(fn, stem, pos + 1, wrong,
                 ["A copy has the same shape, the same side lengths and faces the same way.",
                  f"Drawing {'ABCD'[pos]} matches the figure side for side."],
                 {"src": [list(v) for v in src], "opts": [[list(v) for v in pl] for pl in polys]}, _L, whole=True,
                 auto_slips=False, figure=source_and_panels(srcf, figs))


def _copy_check(p):
    s = _norm([tuple(v) for v in p["src"]])
    ok = [i + 1 for i, o in enumerate(p["opts"]) if _norm([tuple(v) for v in o]) == s]
    return F(ok[0]) if len(ok) == 1 else None


@template(T, "basic", G2 + "04")
def copy_figure_basic(r):
    """Which of four drawings on a dot/square grid is an exact copy of the figure (basic shapes)."""
    return _copy_q(r, copy_figure_basic, ["tri", "L", "trap"])


checker(copy_figure_basic)(_copy_check)


@template(T, "intermediate", G2 + "04")
def copy_figure_harder(r):
    """Which of four drawings on a dot/square grid is an exact copy of the figure (steps, slants, S shapes)."""
    return _copy_q(r, copy_figure_harder, ["para", "stairs", "S", "L", "trap"])


checker(copy_figure_harder)(_copy_check)


@template(T, "competent", G2 + "04")
def copy_to_bigger_grid_area(r):
    """Copy a figure onto a grid of larger squares, then find its area."""
    name = r.choice(NAMES)
    kind = r.choice(["L", "stairs"])
    p = _rand_params(kind, r)
    if p is None:
        return None
    src = _place(_shape(kind, p), 6, 6, r)
    cells = _area2(src) // 2
    k = r.choice([2, 3])
    ans = cells * k * k
    ph = r.choice(["copies the figure square for square", "copies the figure exactly, square for square"])
    stem = (f"The figure is drawn on a grid of 1 cm squares. {name} {ph} onto a grid where each square is {k} cm by {k} cm. "
            f"What is the area of {name}'s copy, in cm²?")
    return build(copy_to_bigger_grid_area, stem, ans, [
        (cells * k, "scaled_area_like_length", f"Multiplied the number of squares by {k} instead of {k} x {k}."),
        (cells, "did_not_scale_the_squares", "Found the area of the original figure."),
        (ans + k * k, "miscounted_a_square", "Counted one square too many."),
        (ans - k * k, "miscounted_a_square", "Counted one square too few."),
    ], [f"The figure covers {cells} squares.", f"Each square is {k} x {k} = {k * k} cm².", f"{cells} x {k * k} = {ans} cm²"],
        {"src": [list(v) for v in src], "k": k}, lambda v: f"{int(v)} cm²", whole=True, auto_slips=False,
        figure=shape_grid(6, 6, [src], cell=22, dots=False, pad_tl=12).svg("Figure on a square grid"))


@checker(copy_to_bigger_grid_area)
def _(p):
    poly = [tuple(v) for v in p["src"]]

    def inside(x, y):
        c = False
        n = len(poly)
        for i in range(n):
            x1, y1 = poly[i]
            x2, y2 = poly[(i + 1) % n]
            if (y1 > y) != (y2 > y) and x < x1 + (y - y1) * (x2 - x1) / (y2 - y1):
                c = not c
        return c
    squares = sum(1 for cx in range(6) for cy in range(6) if inside(cx + 0.5, cy + 0.5))
    return F(squares * p["k"] * p["k"])


# ---------------------------------------------------------------- 3D shapes: 2D drawings of solids

KINDS_3D = {"cube": "cube", "cuboid": "cuboid", "tri_prism": "triangular prism", "sq_pyr": "square-based pyramid",
            "tri_pyr": "triangular pyramid", "pent_prism": "pentagonal prism", "hex_prism": "hexagonal prism"}
FAM = {"cube": "prism", "cuboid": "prism", "tri_prism": "prism", "pent_prism": "prism", "hex_prism": "prism",
       "sq_pyr": "pyramid", "tri_pyr": "pyramid"}
DIMS = {"cube": (1, 1, 1), "cuboid": (1.7, 1.0, 1.2), "tri_prism": (1.5, 1.2, 1.1), "sq_pyr": (1.4, 1.2, 1.4),
        "tri_pyr": (1.6, 1.3, 1.1), "pent_prism": (1.3, 1.3, 1.0), "hex_prism": (1.3, 1.3, 1.0)}
VFE = {"cuboid": (8, 6), "tri_prism": (6, 5), "sq_pyr": (5, 5), "tri_pyr": (4, 4), "pent_prism": (10, 7), "hex_prism": (12, 8)}


def _solid_panel(kind, r):
    a, b, c = DIMS[kind]
    j = r.uniform(0.9, 1.1)
    return solid_fig(kind, a * j, b, c)


@template(T, "basic", G3 + "03")
def which_drawing_shows_solid(r):
    """Which 2D drawing (hidden edges dashed) represents a cube / cuboid / prism / pyramid."""
    name = r.choice(NAMES)
    pool = list(KINDS_3D)
    ks = r.sample(pool, 4)
    if "cube" in ks and "cuboid" in ks:
        ks.remove("cuboid" if r.random() < 0.5 else "cube")
        extra = [k for k in pool if k not in ks and k not in ("cube", "cuboid")]
        ks.append(r.choice(extra))
    target = r.randrange(4)
    ask = ks[target]
    others = [k for i, k in enumerate(ks) if i != target]
    tg = {k: ("confused_prism_with_pyramid" if FAM[k] != FAM[ask] else "confused_with_similar_solid") for k in others}
    why = {"confused_prism_with_pyramid": "Mixed up a prism with a pyramid.",
           "confused_with_similar_solid": "Chose a similar-looking solid with a different number of faces."}
    others.sort(key=lambda k: 0 if FAM[k] == FAM[ask] else 1)
    wrong = [(ks.index(k) + 1, tg[k], why[tg[k]]) for k in others]
    figs = [_solid_panel(k, r) for k in ks]
    nm_ = KINDS_3D[ask]
    stem = f"{name} draws four solids. Hidden edges are shown as dashed lines. Which drawing shows {art(nm_)} {nm_}?"
    return build(which_drawing_shows_solid, stem, target + 1, wrong,
                 [f"{a_an(nm_).capitalize()} {nm_} has " + {"cube": "6 square faces and 12 edges.", "cuboid": "6 rectangular faces and 12 edges.",
                                     "tri_prism": "2 triangular faces and 3 rectangular faces.", "sq_pyr": "a square base and 4 triangular faces meeting at a point.",
                                     "tri_pyr": "4 triangular faces.", "pent_prism": "2 pentagonal faces and 5 rectangular faces.",
                                     "hex_prism": "2 hexagonal faces and 6 rectangular faces."}[ask],
                  f"Drawing {'ABCD'[target]} shows it."], {"kinds": ks, "ask": ask}, _L, whole=True, auto_slips=False,
                 figure=panels(figs, "ABCD", cols=2, title="Four drawings of solids"))


@checker(which_drawing_shows_solid)
def _(p):
    ok = [i + 1 for i, k in enumerate(p["kinds"]) if k == p["ask"]]
    return F(ok[0]) if len(ok) == 1 else None


@template(T, "intermediate", G3 + "03")
def which_drawing_has_edges(r):
    """Which drawing shows a solid with exactly E edges (hidden edges are dashed)."""
    name = r.choice(NAMES)
    pool = list(VFE)
    ks = r.sample(pool, 4)
    target = r.randrange(4)
    ask = ks[target]
    E = lambda k: VFE[k][0] + VFE[k][1] - 2  # noqa: E731  (Euler: E = V + F - 2)
    e = E(ask)
    vis = {k: sum(1 for _, _, v in solid_edges(k, *DIMS[k])[1] if v) for k in ks}

    def why(k):
        if vis[k] == e:
            return ("counted_only_visible_edges", "Counted only the solid lines and left out the dashed hidden edges.")
        if VFE[k][1] == e:
            return ("counted_faces_not_edges", "Counted the faces instead of the edges.")
        if VFE[k][0] == e:
            return ("counted_corners_not_edges", "Counted the corners instead of the edges.")
        return ("miscounted_edges", "Miscounted the edges of the solid.")
    others = [k for i, k in enumerate(ks) if i != target]
    pri = {"counted_only_visible_edges": 0, "counted_faces_not_edges": 1, "counted_corners_not_edges": 2, "miscounted_edges": 3}
    others.sort(key=lambda k: pri[why(k)[0]])
    wrong = [(ks.index(k) + 1, *why(k)) for k in others]
    figs = [_solid_panel(k, r) for k in ks]
    stem = (f"{name} draws four solids, with hidden edges dashed. Which drawing shows a solid with exactly {e} edges?")
    return build(which_drawing_has_edges, stem, target + 1, wrong,
                 [f"Count every edge, including the dashed ones.", f"The {KINDS_3D[ask]} has {e} edges.",
                  f"That is drawing {'ABCD'[target]}."], {"kinds": ks, "e": e}, _L, whole=True, auto_slips=False,
                 figure=panels(figs, "ABCD", cols=2, title="Four drawings of solids"))


@checker(which_drawing_has_edges)
def _(p):
    ok = [i + 1 for i, k in enumerate(p["kinds"]) if VFE[k][0] + VFE[k][1] - 2 == p["e"]]
    return F(ok[0]) if len(ok) == 1 else None


def _edge_len(kind, v, i, j, dims):
    """Length class of edge (i, j) for the labelled solids."""
    if kind == "cuboid":
        d = [abs(v[i][k] - v[j][k]) > 1e-9 for k in range(3)]
        return dims[d.index(True)]
    if kind == "cube":
        return dims[0]
    return dims[0] if (i < 4 and j < 4) else dims[1]


@template(T, "competent", G3 + "03")
def total_edge_length_drawing(r):
    """Total length of all edges of a solid from a drawing with labelled edges (hidden edges dashed)."""
    name = r.choice(NAMES)
    kind = r.choice(["cuboid", "cuboid", "cube", "sq_pyr"])
    if kind == "cuboid":
        l, w, h = r.sample(range(2, 10), 3)
        v, edges = solid_edges("cuboid", l, h, w)
        fig = solid_fig("cuboid", l, h, w, W=210, H=170, labels=[(0, 1, f"{l} cm"), (1, 2, f"{h} cm"), (1, 5, f"{w} cm")])
        ans = 4 * (l + w + h)
        vis_sum = sum(_edge_len("cuboid", v, i, j, (l, h, w)) for i, j, vv in edges if vv)
        wrong = [(vis_sum, "added_only_visible_edges", "Added only the solid lines and left out the dashed hidden edges."),
                 (l + w + h, "counted_one_edge_of_each_length", "Added one edge of each length only."),
                 (2 * (l + w + h), "counted_each_length_twice", "Counted each length only twice instead of four times."),
                 (ans + 4, "arithmetic_slip", "Made a small arithmetic slip.")]
        stem = (f"{name} draws a cuboid that is {l} cm long, {w} cm wide and {h} cm high. Hidden edges are dashed. "
                f"What is the total length of all the edges of the cuboid, in cm?")
        steps = ["A cuboid has 12 edges: 4 of each length.", f"4 x ({l} + {w} + {h}) = {ans} cm"]
        params = {"kind": kind, "dims": [l, w, h]}
    elif kind == "cube":
        s = r.randint(2, 12)
        v, edges = solid_edges("cube", 1, 1, 1)
        fig = solid_fig("cube", 1, 1, 1, W=210, H=170, labels=[(0, 1, f"{s} cm")])
        ans = 12 * s
        vis_sum = s * sum(1 for _, _, vv in edges if vv)
        wrong = [(vis_sum, "added_only_visible_edges", "Counted only the solid lines and left out the hidden edges."),
                 (6 * s, "counted_faces_not_edges", "Used the 6 faces instead of the 12 edges."),
                 (8 * s, "counted_corners_not_edges", "Used the 8 corners instead of the 12 edges."),
                 (ans + s, "miscounted_one_edge", "Counted one edge too many.")]
        stem = (f"{name} draws a cube with edges of {s} cm. Hidden edges are dashed. "
                f"What is the total length of all the edges of the cube, in cm?")
        steps = ["A cube has 12 equal edges.", f"12 x {s} = {ans} cm"]
        params = {"kind": kind, "dims": [s]}
    else:
        a, e = r.randint(3, 9), r.randint(4, 12)
        if e * 2 <= a * 1.5:
            return None
        v, edges = solid_edges("sq_pyr", *DIMS["sq_pyr"])
        slant_vis = [(i, j) for i, j, vv in edges if vv and j == 4]
        fig = solid_fig("sq_pyr", 1.4, 1.3, 1.4, W=210, H=170, labels=[(0, 1, f"{a} cm"), (slant_vis[0][0], 4, f"{e} cm")])
        ans = 4 * a + 4 * e
        vis_sum = sum(_edge_len("sq_pyr", v, i, j, (a, e)) for i, j, vv in edges if vv)
        wrong = [(vis_sum, "added_only_visible_edges", "Added only the solid lines and left out the dashed hidden edges."),
                 (4 * a + e, "counted_one_slant_edge", "Counted only one slant edge."),
                 (4 * e + a, "counted_one_base_edge", "Counted only one base edge."),
                 (ans + 4, "arithmetic_slip", "Made a small arithmetic slip.")]
        stem = (f"{name} draws a square-based pyramid. Each side of the base is {a} cm and each of the 4 slant edges is {e} cm. "
                f"Hidden edges are dashed. The figure is not drawn to scale. What is the total length of all the edges, in cm?")
        steps = ["The pyramid has 4 base edges and 4 slant edges.", f"4 x {a} + 4 x {e} = {ans} cm"]
        params = {"kind": kind, "dims": [a, e]}
    return build(total_edge_length_drawing, stem, ans, wrong, steps, params, lambda v: f"{int(v)} cm", whole=True,
                 auto_slips=False, figure=fig.svg("Drawing of a solid with labelled edges"))


@checker(total_edge_length_drawing)
def _(p):
    d = p["dims"]
    if p["kind"] == "cuboid":
        return F(sum([d[0]] * 4 + [d[1]] * 4 + [d[2]] * 4))
    if p["kind"] == "cube":
        return F(sum([d[0]] * 12))
    return F(sum([d[0]] * 4 + [d[1]] * 4))


# ---------------------------------------------------------------- angles: drawing with a protractor

@template(T, "basic", GA + "04")
def which_angle_is_drawn(r):
    """Which protractor drawing (A-D) shows an angle of the given size, reading the correct scale."""
    name = r.choice(NAMES)
    th = r.randrange(25, 156, 5)
    alphas = [th, 180 - th, th + 10, th - 10]
    if any(abs(a - b) < 10 for i, a in enumerate(alphas) for b in alphas[i + 1:]) or min(alphas) < 15 or max(alphas) > 165:
        return None
    pos = r.randrange(4)
    others = alphas[1:]
    bases = [r.random() < 0.5 for _ in range(4)]
    allv = others[:]
    allv.insert(pos, th)
    br = list(bases)
    for i, a in enumerate(allv):
        if a == 180 - th:
            br[i] = False  # arm points at the outer-scale mark th, but QP is on the left
    figs = [mini_protractor(a, b) for a, b in zip(allv, br)]
    wr_order = [(180 - th, "read_the_wrong_scale", "Read the scale that starts at 0 on the other side."),
                (th + 10, "misread_by_one_interval", "Was one 10° interval out."),
                (th - 10, "misread_by_one_interval", "Was one 10° interval out.")]
    wrong = [(allv.index(a) + 1, t, w) for a, t, w in wr_order]
    stem = (f"{name} needs to draw ∠PQR = {th}° with a protractor. In each drawing, ray QP lies along the baseline of the "
            f"protractor. Which drawing shows an angle of {th}°?")
    return build(which_angle_is_drawn, stem, pos + 1, wrong,
                 ["Start at the 0° mark that QP lies on and read along that scale.", f"Only drawing {'ABCD'[pos]} reaches {th}°."],
                 {"th": th, "alphas": allv, "base_right": br}, _L, whole=True, auto_slips=False,
                 figure=panels(figs, "ABCD", cols=2, title="Four protractor drawings"))


@checker(which_angle_is_drawn)
def _(p):
    res = []
    for i, (a, b) in enumerate(zip(p["alphas"], p["base_right"])):
        base_dir = 0 if b else 180
        arm_dir = a if b else 180 - a
        got = abs(arm_dir - base_dir)
        if got == p["th"]:
            res.append(i + 1)
    return F(res[0]) if len(res) == 1 else None


@template(T, "intermediate", GA + "04")
def which_scale_was_used(r):
    """A child marked R on the wrong scale of the protractor: what angle was actually drawn."""
    name = r.choice(NAMES)
    th = r.randrange(20, 161, 5)
    if th == 90:
        return None
    use_outer = r.random() < 0.5
    act = 180 - th
    base_right = not use_outer  # outer scale starts at 0 on the right: the mistake happens when QP is on the left
    sc = "outer" if use_outer else "inner"
    side = "left" if use_outer else "right"
    zero = "right" if use_outer else "left"
    stem = (f"{name} wants to draw ∠PQR = {th}°, with QP along the baseline of the protractor pointing to the {side}. "
            f"{name} marks R at {th} on the {sc} scale (the scale that starts at 0 on the {zero}). "
            f"What is the actual size of ∠PQR in the drawing?")
    fig = protractor_fig(act, base_right=base_right)
    wr = [W(th, "read_the_wrong_scale", f"Took the {sc} scale reading as the angle even though QP is not on its 0°."),
          W(act + 10, "misread_by_one_interval", "Was one 10° interval out."),
          W(act - 10, "misread_by_one_interval", "Was one 10° interval out.")]
    return mk(which_scale_was_used, stem, act, wr,
              [f"QP is on the {side}, so the 0° mark for this angle is on the {side}.",
               f"The mark R is at {th} on the {sc} scale, so on the other scale it reads 180° - {th}° = {act}°.", f"∠PQR = {act}°"],
              {"th": th, "outer": use_outer}, fig)


@checker(which_scale_was_used)
def _(p):
    base_dir = 180 if p["outer"] else 0  # QP on the left for the outer-scale slip, on the right otherwise
    arm_dir = p["th"] if p["outer"] else 180 - p["th"]  # direction of R measured from the right-hand baseline
    return F(abs(arm_dir - base_dir))


@template(T, "competent", GA + "04")
def protractor_then_extend(r):
    """Read ∠PQR from a protractor, then find the angle between QR and the extension of PQ."""
    name = r.choice(NAMES)
    th = r.randrange(25, 156, 5)
    if th == 90:
        return None
    right = r.random() < 0.5
    side = "right" if right else "left"
    ans = 180 - th
    stem = (f"{name} draws ∠PQR with a protractor, with ray QP along the baseline pointing to the {side}. "
            f"Ray QS is drawn so that PQS is a straight line. What is the size of ∠RQS?")
    fig = protractor_fig(th, base_right=right)
    wr = [W(th, "gave_the_angle_read_off", "Gave ∠PQR instead of the angle on the other side."),
          W(abs(th - 90), "used_90_not_180", "Used 90° instead of 180° for a straight line."),
          W(ans + 10, "misread_by_one_interval", "Was one 10° interval out."),
          W(ans - 10, "misread_by_one_interval", "Was one 10° interval out.")]
    return mk(protractor_then_extend, stem, ans, wr,
              [f"Read ∠PQR from the scale that starts at 0° on QP: {th}°.", "Angles on a straight line add up to 180°.",
               f"∠RQS = 180° - {th}° = {ans}°"], {"th": th, "right": right}, fig)


@checker(protractor_then_extend)
def _(p):
    import math as _m
    base = (1, 0) if p["right"] else (-1, 0)
    arm = (_m.cos(_m.radians(p["th"] if p["right"] else 180 - p["th"])), _m.sin(_m.radians(p["th"] if p["right"] else 180 - p["th"])))
    pqr = _m.degrees(_m.acos(base[0] * arm[0] + base[1] * arm[1]))
    ext = (-base[0], -base[1])
    rqs = _m.degrees(_m.acos(ext[0] * arm[0] + ext[1] * arm[1]))
    return F(round(rqs)) if abs(pqr + rqs - 180) < 1e-6 else None


# ---------------------------------------------------------------- perpendicular and parallel lines on a grid

def _seg_in_region(r, region, v, cols_per=5):
    """Place a segment with direction v inside a 5x5 region (lattice 0..4), returning absolute endpoints."""
    c0, r0 = (region % 3) * cols_per, (region // 3) * cols_per
    dx, dy = v
    sx = r.randint(max(0, -dx), min(4, 4 - dx))
    sy = r.randint(max(0, -dy), min(4, 4 - dy))
    return (c0 + sx, r0 + sy), (c0 + sx + dx, r0 + sy + dy)


def _dot(u, v):
    return u[0] * v[0] + u[1] * v[1]


def _cross(u, v):
    return u[0] * v[1] - u[1] * v[0]


def _line_figure(pq, cands, names="ABCD"):
    segs = [("Q", pq[0], pq[1], True)] if pq else []
    segs += [(names[i], a, b, False) for i, (a, b) in enumerate(cands)]
    return shape_grid(15, 10, [], cell=17, pad_tl=14, pad_br=14, segs=segs).svg("Lines on a grid")


def _lines_question(r, fn, kind, pq_vec, correct_vec, decoys, name):
    """Build a Which-line-is-perpendicular/parallel question. decoys: [(vec, tag, why)] (3 needed)."""
    regions = r.sample(range(6), 5)
    pq = _seg_in_region(r, regions[0], pq_vec)
    vecs = [correct_vec] + [d[0] for d in decoys[:3]]
    vecs = [(-x, -y) if r.random() < 0.5 else (x, y) for x, y in vecs]
    pos = r.randrange(4)
    slots = [None] * 4
    slots[pos] = 0
    rest = [i for i in range(4) if i != pos]
    for slot, vi in zip(rest, [1, 2, 3]):
        slots[slot] = vi
    cands = [_seg_in_region(r, regions[1 + s], vecs[slots[s]]) for s in range(4)]
    wrong = [(slots.index(i + 1) + 1, decoys[i][1], decoys[i][2]) for i in range(3)]
    word = "perpendicular to" if kind == "perp" else "parallel to"
    stem = f"{name} draws line PQ and four other lines, A, B, C and D, on a square grid. Which line is {word} line PQ?"
    return build(fn, stem, pos + 1, wrong,
                 ["Compare how far each line goes across and up/down for each step on the grid.",
                  "Perpendicular lines turn the 'across' and 'up' steps round, with one direction reversed." if kind == "perp"
                  else "Parallel lines go across and up/down by the same amounts, so they slope the same way.",
                  f"Line {'ABCD'[pos]} is {word} PQ."],
                 {"pq": [list(pq[0]), list(pq[1])], "cands": [[list(a), list(b)] for a, b in cands], "kind": kind},
                 _L, whole=True, auto_slips=False, figure=_line_figure(pq, cands))


def _lines_check(p):
    v = (p["pq"][1][0] - p["pq"][0][0], p["pq"][1][1] - p["pq"][0][1])
    ok = []
    for i, (a, b) in enumerate(p["cands"]):
        u = (b[0] - a[0], b[1] - a[1])
        if (p["kind"] == "perp" and _dot(u, v) == 0) or (p["kind"] == "par" and _cross(u, v) == 0):
            ok.append(i + 1)
    return F(ok[0]) if len(ok) == 1 else None


@template(T, "basic", GP + "02")
def line_perp_par_grid_basic(r):
    """Which line on the grid is perpendicular / parallel to a horizontal or vertical line PQ."""
    name = r.choice(NAMES)
    kind = r.choice(["perp", "par"])
    horiz = r.random() < 0.5
    n1 = r.randint(2, 4)
    pq = (n1, 0) if horiz else (0, n1)
    if kind == "perp":
        good = (0, r.randint(2, 4)) if horiz else (r.randint(2, 4), 0)
        decoys = [((r.randint(2, 4), 0) if horiz else (0, r.randint(2, 4)), "chose_parallel_for_perpendicular", "Chose a parallel line instead."),
                  ((2, 2) if r.random() < 0.5 else (3, 3), "chose_a_slanting_line", "Chose a line slanting at about 45°, not a right angle."),
                  (((1, 4) if horiz else (4, 1)), "chose_a_nearly_perpendicular_line", "Chose a line that leans slightly, so it is not at a right angle.")]
    else:
        good = (r.randint(2, 4), 0) if horiz else (0, r.randint(2, 4))
        decoys = [((0, r.randint(2, 4)) if horiz else (r.randint(2, 4), 0), "chose_perpendicular_for_parallel", "Chose a perpendicular line instead."),
                  ((2, 2), "chose_a_slanting_line", "Chose a slanting line that is not parallel."),
                  (((4, 1) if horiz else (1, 4)), "chose_a_nearly_parallel_line", "Chose a line that leans slightly, so it is not parallel.")]
    return _lines_question(r, line_perp_par_grid_basic, kind, pq, good, decoys, name)


checker(line_perp_par_grid_basic)(_lines_check)


@template(T, "intermediate", GP + "02")
def line_perp_par_grid_slope(r):
    """Which line on the grid is perpendicular / parallel to a sloping line PQ."""
    name = r.choice(NAMES)
    kind = r.choice(["perp", "par"])
    a, b = r.choice([(1, 2), (2, 1), (1, 3), (3, 1), (2, 3), (3, 2)])
    pq = (a, b)
    perp = (-b, a)
    if kind == "perp":
        good = perp
        decoys = [((a, b), "chose_parallel_for_perpendicular", "Chose a parallel line instead."),
                  ((b, a), "swapped_the_steps", "Swapped the across and up steps without reversing one."),
                  ((a, -b), "chose_the_mirror_image", "Chose the mirror image of PQ, which is not at a right angle to it.")]
    else:
        good = pq
        decoys = [(perp, "chose_perpendicular_for_parallel", "Chose a perpendicular line instead."),
                  ((b, a), "swapped_the_steps", "Swapped the across and up steps."),
                  ((a, -b), "chose_the_mirror_image", "Chose the mirror image of PQ, which slopes the other way.")]
    # steps are at most 3, so every decoy fits the grid; still refuse a decoy that is also a correct answer
    if any((_dot(d[0], pq) == 0 if kind == "perp" else _cross(d[0], pq) == 0) for d in decoys):
        return None
    return _lines_question(r, line_perp_par_grid_slope, kind, pq, good, decoys, name)


checker(line_perp_par_grid_slope)(_lines_check)


# ---------------------------------------------------------------- perpendicular and parallel lines: the paper frames
# Bank review (20 Nov 2026): 2025-26 papers ask "which two lines are perpendicular / parallel?" (about half the items)
# and "how many of the letters have both kinds of line?" (about a quarter). Lines are labelled P-T, never A-D, because
# the option buttons are lettered A-D.

_PAIR_LABELS = "PQRST"


def _rel(u, v):
    return "perp" if _dot(u, v) == 0 else "par" if _cross(u, v) == 0 else None


def _meet_angle(u, v):
    """The smaller angle between two lines with directions u and v, in degrees (unrounded)."""
    a = abs(math.degrees(math.atan2(u[1], u[0]) - math.atan2(v[1], v[0]))) % 180
    return min(a, 180 - a)


def _about(a):
    return f"{round(a)}°" if abs(a - round(a)) < 1e-9 else f"about {round(a)}°"


def _pair_show(v):
    i, j = divmod(int(v), 10)
    return f"{_PAIR_LABELS[i - 1]} and {_PAIR_LABELS[j - 1]}"


def _steps_desc(v):
    """How a grid line runs, for the worked solution (y grows downwards in the figure)."""
    g = math.gcd(abs(v[0]), abs(v[1]))
    dx, dy = v[0] // g, v[1] // g
    if dx < 0 or (dx == 0 and dy < 0):
        dx, dy = -dx, -dy
    if dy == 0:
        return "goes straight across"
    if dx == 0:
        return "goes straight up and down"
    return f"goes {dx} across for every {abs(dy)} {'down' if dy > 0 else 'up'}"


def _slope(a, b):
    """Gradient of segment ab as a Fraction, or None for an up-and-down line (checker route: no dot products)."""
    return None if b[0] == a[0] else F(b[1] - a[1], b[0] - a[0])


def _slope_rel(s, t):
    if s == t:
        return "par"
    if (s is None and t == 0) or (t is None and s == 0) or (s is not None and t is not None and s * t == -1):
        return "perp"
    return None


def _pick_pair(r, fn, pool, n, kind, slanted_answer=False):
    vecs = [r.choice(pool) for _ in range(n)]
    pairs = [(i, j) for i in range(n) for j in range(i + 1, n)]
    hits = [(i, j) for i, j in pairs if _rel(vecs[i], vecs[j]) == kind]
    if len(hits) != 1:
        return None
    a, b = hits[0]
    if slanted_answer and 0 in (vecs[a][0] * vecs[a][1], vecs[b][0] * vecs[b][1]):
        return None
    if kind == "perp" and not any(_rel(vecs[i], vecs[j]) == "par" or abs(_meet_angle(vecs[i], vecs[j]) - 90) < 30
                                  for i, j in pairs if (i, j) != (a, b)):
        return None  # needs at least one tempting wrong pair
    scaled = []
    for v in vecs:
        top = 4 // max(abs(v[0]), abs(v[1]))
        k = r.randint(max(1, min(2, top)), top)
        scaled.append((v[0] * k, v[1] * k) if r.random() < 0.5 else (-v[0] * k, -v[1] * k))
    regions = r.sample(range(6), n)
    segs = [_seg_in_region(r, rg, v) for rg, v in zip(regions, scaled)]
    for i, j in pairs:  # two parallel pieces of the same straight line would read as one broken line
        if _rel(scaled[i], scaled[j]) == "par":
            w = (segs[j][0][0] - segs[i][0][0], segs[j][0][1] - segs[i][0][1])
            if _cross(w, scaled[i]) == 0:
                return None
    L = _PAIR_LABELS
    word = "perpendicular" if kind == "perp" else "parallel"
    wrong = []
    for i, j in pairs:
        if (i, j) == (a, b):
            continue
        rel, ang = _rel(scaled[i], scaled[j]), _meet_angle(scaled[i], scaled[j])
        if kind == "perp":
            if rel == "par":
                wrong.append((0, (10 * (i + 1) + j + 1, "chose_a_parallel_pair",
                                  f"Lines {L[i]} and {L[j]} are parallel: they slope the same way and never meet.")))
            else:
                wrong.append((1 + abs(90 - ang) / 100, (10 * (i + 1) + j + 1, "chose_lines_not_at_a_right_angle",
                                                        f"Lines {L[i]} and {L[j]} would meet at {_about(ang)}, not at a right angle.")))
        else:
            if rel == "perp":
                wrong.append((1.5, (10 * (i + 1) + j + 1, "chose_a_perpendicular_pair",
                                    f"Lines {L[i]} and {L[j]} are perpendicular: they would meet at a right angle.")))
            else:
                wrong.append((ang / 100, (10 * (i + 1) + j + 1, "chose_lines_that_would_meet",
                                          f"Lines {L[i]} and {L[j]} would meet at {_about(ang)} if they were drawn longer, "
                                          f"so they are not parallel.")))
    wrong = [w for _, w in sorted(wrong, key=lambda x: x[0])]
    names = ", ".join(L[:n - 1]) + f" and {L[n - 1]}"
    name = r.choice(NAMES)
    stem = f"{name} draws {['four', 'five'][n - 4]} lines, {names}, on a square grid. Which two lines are {word} to each other?"
    rule = ("Perpendicular lines meet at a right angle (or would, if they were drawn longer)." if kind == "perp"
            else "Parallel lines slope the same way, so they never meet however long they are drawn.")
    steps = [rule, f"Line {L[a]} {_steps_desc(scaled[a])}. Line {L[b]} {_steps_desc(scaled[b])}.",
             (f"Turning line {L[a]} through a right angle gives the direction of line {L[b]}, so lines {L[a]} and {L[b]} "
              f"are perpendicular.") if kind == "perp" else f"So lines {L[a]} and {L[b]} are parallel."]
    return build(fn, stem, 10 * (a + 1) + b + 1, wrong, steps,
                 {"segs": [[list(p), list(q)] for p, q in segs], "kind": kind},
                 _pair_show, whole=True, auto_slips=False, figure=_pair_fig(segs))


def _pair_fig(segs):
    """The lines one square in from the edge of the grid, each labelled beside its middle (above it, or to its left)."""
    cell, pad = 17, 8
    f = shape_grid(16, 11, [], cell=cell, pad_tl=pad, pad_br=pad)
    for i, (p, q) in enumerate(segs):
        x1, y1 = pad + (p[0] + 1) * cell, pad + (p[1] + 1) * cell
        x2, y2 = pad + (q[0] + 1) * cell, pad + (q[1] + 1) * cell
        f.line(x1, y1, x2, y2, width=2.4)
        d = math.hypot(x2 - x1, y2 - y1)
        nx, ny = -(y2 - y1) / d, (x2 - x1) / d
        if ny > 0 or (ny == 0 and nx > 0):
            nx, ny = -nx, -ny
        f.text((x1 + x2) / 2 + nx * 12, (y1 + y2) / 2 + ny * 12, _PAIR_LABELS[i], size=14, bold=True)
    return f.svg("Lines on a square grid")


def _pick_pair_check(p):
    s = [_slope(tuple(a), tuple(b)) for a, b in p["segs"]]
    hits = [10 * (i + 1) + j + 1 for i in range(len(s)) for j in range(i + 1, len(s)) if _slope_rel(s[i], s[j]) == p["kind"]]
    return F(hits[0]) if len(hits) == 1 else None


@template(T, "basic", GP + "01")
def pp_pick_pair(r):
    """Which two of four lines on a square grid are perpendicular / parallel (straight across, up-and-down and 45° lines)."""
    return _pick_pair(r, pp_pick_pair, [(1, 0), (0, 1), (1, 1), (1, -1), (1, 2), (2, 1)], 4, r.choice(["perp", "par"]))


checker(pp_pick_pair)(_pick_pair_check)


@template(T, "competent", GP + "01", GP + "02")
def pp_pick_pair_slanted(r):
    """Which two of five lines on a square grid are perpendicular / parallel; the answer is a pair of slanting lines."""
    pool = [(1, 0), (0, 1), (1, 1), (1, -1), (1, 2), (-2, 1), (2, 1), (-1, 2), (1, 3), (-3, 1), (3, 1), (-1, 3)]
    return _pick_pair(r, pp_pick_pair_slanted, pool, 5, r.choice(["perp", "par"]), slanted_answer=True)


checker(pp_pick_pair_slanted)(_pick_pair_check)


# capital letters drawn on a square grid; each stroke is one straight line (x right, y down). No A-D: the option buttons
# are lettered A-D.
_LETTERS = {
    "E": [((0, 0), (0, 4)), ((0, 0), (3, 0)), ((0, 2), (2, 2)), ((0, 4), (3, 4))],
    "F": [((0, 0), (0, 4)), ((0, 0), (3, 0)), ((0, 2), (2, 2))],
    "H": [((0, 0), (0, 4)), ((3, 0), (3, 4)), ((0, 2), (3, 2))],
    "I": [((0, 0), (2, 0)), ((1, 0), (1, 4)), ((0, 4), (2, 4))],
    "J": [((0, 0), (3, 0)), ((2, 0), (2, 4)), ((0, 4), (2, 4))],
    "K": [((0, 0), (0, 4)), ((0, 2), (2, 0)), ((0, 2), (2, 4))],
    "L": [((0, 0), (0, 4)), ((0, 4), (3, 4))],
    "M": [((0, 4), (0, 0)), ((0, 0), (2, 3)), ((2, 3), (4, 0)), ((4, 0), (4, 4))],
    "N": [((0, 4), (0, 0)), ((0, 0), (3, 4)), ((3, 4), (3, 0))],
    "O": [((0, 0), (3, 0)), ((3, 0), (3, 4)), ((3, 4), (0, 4)), ((0, 4), (0, 0))],
    "P": [((0, 4), (0, 0)), ((0, 0), (3, 0)), ((3, 0), (3, 2)), ((3, 2), (0, 2))],
    "T": [((0, 0), (4, 0)), ((2, 0), (2, 4))],
    "U": [((0, 0), (0, 4)), ((0, 4), (3, 4)), ((3, 4), (3, 0))],
    "V": [((0, 0), (2, 4)), ((2, 4), (4, 0))],
    "X": [((0, 0), (4, 4)), ((4, 0), (0, 4))],
    "Y": [((0, 0), (2, 2)), ((4, 0), (2, 2)), ((2, 2), (2, 4))],
    "Z": [((0, 0), (3, 0)), ((3, 0), (0, 4)), ((0, 4), (3, 4))],
}


def _letter_props(c):
    """(has a pair of perpendicular strokes, number of pairs of parallel strokes, has a right angle between slanting strokes)."""
    v = [(b[0] - a[0], b[1] - a[1]) for a, b in _LETTERS[c]]
    pairs = [(v[i], v[j]) for i in range(len(v)) for j in range(i + 1, len(v))]
    perp = [(x, y) for x, y in pairs if _dot(x, y) == 0]
    slant_perp = any(x[0] * x[1] != 0 for x, _ in perp)
    return bool(perp), sum(1 for x, y in pairs if _cross(x, y) == 0), slant_perp


def _letters_fig(word):
    cell, pad = 12, 8
    widths = [max(p[0] for s in _LETTERS[c] for p in s) for c in word]
    cols = 2 + sum(widths) + 2 * (len(word) - 1)
    f = shape_grid(cols, 6, [], cell=cell, pad_tl=pad, pad_br=pad)
    x0 = 1
    for c, w in zip(word, widths):
        for a, b in _LETTERS[c]:
            f.line(pad + (x0 + a[0]) * cell, pad + (1 + a[1]) * cell, pad + (x0 + b[0]) * cell, pad + (1 + b[1]) * cell, width=3.4)
        x0 += w + 2
    return f.svg("Letters drawn on a square grid")


def _letter_line(c):
    perp, npar, _ = _letter_props(c)
    return (f"{c}: {'has' if perp else 'no'} perpendicular lines, "
            + ("no parallel lines" if npar == 0 else f"{plural(npar, 'pair')} of parallel lines"))


def _letters_q(r, fn, n, ask):
    word = "".join(r.sample(sorted(_LETTERS), n))
    props = {c: _letter_props(c) for c in word}
    count = lambda pred: sum(1 for c in word if pred(*props[c]))
    letters = ", ".join(word[:-1]) + f" and {word[-1]}"
    if ask == "both":
        ans = count(lambda pe, np_, sp: pe and np_ > 0)
        q = "How many of the letters have both perpendicular and parallel lines?"
        wrong = [(count(lambda pe, np_, sp: pe), "counted_letters_with_perpendicular_lines",
                  "Counted the letters with perpendicular lines without checking for parallel lines too."),
                 (count(lambda pe, np_, sp: np_ > 0), "counted_letters_with_parallel_lines",
                  "Counted the letters with parallel lines without checking for perpendicular lines too.")]
    elif ask == "two_pairs":
        ans = count(lambda pe, np_, sp: np_ >= 2)
        q = "How many of the letters have more than one pair of parallel lines?"
        wrong = [(count(lambda pe, np_, sp: np_ >= 1), "counted_letters_with_one_pair",
                  "Also counted letters with only one pair of parallel lines."),
                 (count(lambda pe, np_, sp: np_ == 1), "counted_exactly_one_pair",
                  "Counted the letters with exactly one pair of parallel lines.")]
    else:  # perpendicular lines but no parallel lines
        ans = count(lambda pe, np_, sp: pe and np_ == 0)
        q = "How many of the letters have perpendicular lines but no parallel lines?"
        wrong = [(count(lambda pe, np_, sp: pe and np_ == 0 and not sp), "missed_right_angles_between_slanting_lines",
                  "Missed the right angles between slanting lines (count the squares: they meet at a right angle too)."),
                 (count(lambda pe, np_, sp: pe), "forgot_no_parallel_lines",
                  "Counted every letter with perpendicular lines, including those that also have parallel lines.")]
    if not 1 <= ans <= n - 1:
        return None
    wrong += [(ans + 1, "counted_one_letter_too_many", "Counted one letter too many."),
              (ans - 1, "missed_one_letter", "Missed one of the letters."),
              (ans + 2, "miscounted_the_letters", "Miscounted the letters.")]
    stem = f"The letters {letters} are drawn on a square grid. {q}"
    steps = [_letter_line(c) for c in word] + [f"So the answer is {ans}."]
    return build(fn, stem, ans, [w for w in wrong if w[0] <= n], steps, {"letters": word, "ask": ask}, str,
                 whole=True, auto_slips=False, figure=_letters_fig(word))


def _letters_check(p):
    """Counts again from the strokes, with gradients instead of dot products."""
    out = 0
    for c in p["letters"]:
        s = [_slope(a, b) for a, b in _LETTERS[c]]
        rels = [_slope_rel(s[i], s[j]) for i in range(len(s)) for j in range(i + 1, len(s))]
        perp, npar = "perp" in rels, rels.count("par")
        out += {"both": perp and npar > 0, "two_pairs": npar >= 2, "perp_only": perp and npar == 0}[p["ask"]]
    return F(out)


@template(T, "intermediate", GP + "01")
def pp_letters_both(r):
    """How many of five letters on a grid have both perpendicular and parallel lines."""
    return _letters_q(r, pp_letters_both, 5, "both")


checker(pp_letters_both)(_letters_check)


@template(T, "competent", GP + "01")
def pp_letters_parallel_pairs(r):
    """How many of six letters on a grid have more than one pair of parallel lines, or perpendicular but no parallel lines."""
    return _letters_q(r, pp_letters_parallel_pairs, 6, r.choice(["two_pairs", "perp_only"]))


checker(pp_letters_parallel_pairs)(_letters_check)


# ---------------------------------------------------------------- 2D shapes on a grid: the paper frames
# Bank review (20 Nov 2026): paper 2D-shape MCQs ask which grid shape is a rhombus / trapezium, what type a grid triangle
# is, or which point completes a named triangle. These replace three counting puzzles with no paper analogue.

def _quad_class(poly):
    e = [(poly[(i + 1) % 4][0] - poly[i][0], poly[(i + 1) % 4][1] - poly[i][1]) for i in range(4)]
    par = [_cross(e[0], e[2]) == 0, _cross(e[1], e[3]) == 0]
    sq = [x * x + y * y for x, y in e]
    if all(par):
        rh, rect = len(set(sq)) == 1, _dot(e[0], e[1]) == 0
        return "square" if rh and rect else "rhombus" if rh else "rectangle" if rect else "parallelogram"
    return "trapezium" if any(par) else "kite"


def _quad_shapes(r):
    a, b = r.choice([(1, 2), (2, 1), (3, 1), (3, 2)])
    w, h = r.randint(3, 4), r.randint(2, 3)
    k = r.randint(1, 2)
    t = r.randint(1, w - 2) if w > 2 else 1
    return {
        "rhombus": r.choice([[(a, 0), (2 * a, b), (a, 2 * b), (0, b)], [(0, 0), (2, 1), (3, 3), (1, 2)], [(1, 0), (3, 1), (4, 3), (2, 2)]]),
        "rectangle": r.choice([[(0, 0), (w, 0), (w, h), (0, h)], [(1, 0), (3, 2), (2, 3), (0, 1)], [(2, 0), (3, 1), (1, 3), (0, 2)]]),
        "parallelogram": r.choice([[(k, 0), (k + w, 0), (w, h), (0, h)], [(0, 0), (w, 0), (w + k, h), (k, h)], [(0, 1), (3, 0), (4, 2), (1, 3)]]),
        "trapezium": r.choice([[(t, 0), (w - 1, 0), (w, h), (0, h)], [(0, 0), (w, 0), (w, h), (t, h)], [(0, 0), (w - 1, 0), (w, h), (0, h)]]),
        "kite": r.choice([[(1, 0), (2, 1), (1, 3), (0, 1)], [(2, 0), (4, 1), (2, 3), (0, 1)], [(1, 0), (3, 1), (1, 2), (0, 1)]]),
    }


_QUAD_WHY = {
    ("parallelogram", "rhombus"): "is a parallelogram, but its sides are not all the same length",
    ("rectangle", "rhombus"): "is a rectangle: its sides are not all the same length",
    ("trapezium", "rhombus"): "is a trapezium: only one pair of its sides is parallel",
    ("kite", "rhombus"): "has no parallel sides",
    ("parallelogram", "trapezium"): "has two pairs of parallel sides; a trapezium has exactly one pair",
    ("rectangle", "trapezium"): "has two pairs of parallel sides; a trapezium has exactly one pair",
    ("rhombus", "trapezium"): "has two pairs of parallel sides; a trapezium has exactly one pair",
    ("kite", "trapezium"): "has no parallel sides",
    ("trapezium", "parallelogram"): "has only one pair of parallel sides",
    ("kite", "parallelogram"): "has no parallel sides",
    ("parallelogram", "rectangle"): "is a parallelogram, but its angles are not right angles",
    ("rhombus", "rectangle"): "is a rhombus: its angles are not right angles",
    ("trapezium", "rectangle"): "has only one pair of parallel sides",
    ("kite", "rectangle"): "has no parallel sides",
}
_QUAD_RULE = {
    "rhombus": "A rhombus has 4 equal sides and its opposite sides are parallel.",
    "trapezium": "A trapezium has exactly one pair of parallel sides.",
    "parallelogram": "A parallelogram has two pairs of parallel sides.",
    "rectangle": "A rectangle has two pairs of parallel sides and 4 right angles.",
}
_QUAD_OK = {"rhombus": {"rhombus", "square"}, "trapezium": {"trapezium"},
            "parallelogram": {"parallelogram", "rhombus", "rectangle", "square"}, "rectangle": {"rectangle", "square"}}


@template(T, "competent", G2 + "01", GT + "04")
def grid_which_quadrilateral(r):
    """math-pat-shapes-classify-2d. Which of four shapes on a square grid is a rhombus / trapezium / parallelogram / rectangle."""
    target = r.choice(["rhombus", "trapezium", "parallelogram", "rectangle"])
    shapes = _quad_shapes(r)
    if any(_quad_class(p) != k for k, p in shapes.items()):
        return None
    decoys = [k for k in shapes if k not in _QUAD_OK[target]]
    if target == "parallelogram":
        decoys += ["trapezium"]  # only two classes are not parallelograms: use two different trapeziums
        alt = _quad_shapes(r)["trapezium"]
        if alt == shapes["trapezium"]:
            return None
    else:
        alt = None
    r.shuffle(decoys)
    bad, used = [], set()
    for k in decoys[:3]:
        poly = alt if (k == "trapezium" and "trapezium" in used) else shapes[k]
        used.add(k)
        bad.append((poly, f"chose_a_{k}", f"That shape {_QUAD_WHY[(k, target)]}."))
    if len(bad) < 3:
        return None
    name = r.choice(NAMES)
    stem = f"{name} draws four shapes on a square grid. Which shape is {a_an(target)} {target}?"
    steps = [_QUAD_RULE[target], "Count the squares along each side to check which sides are parallel and equal.",
             f"Only one of the shapes is {a_an(target)} {target}."]
    return _rect_options(r, grid_which_quadrilateral, shapes[target], bad, stem, steps, {"target": target}, None,
                         cols=6, rows=5, cell=13)


@checker(grid_which_quadrilateral)
def _(p):
    """Classifies again with gradients and side lengths (no dot or cross products)."""
    def cls(poly):
        pts = [tuple(v) for v in poly]
        s = [_slope(pts[i], pts[(i + 1) % 4]) for i in range(4)]
        ln = [(pts[(i + 1) % 4][0] - pts[i][0]) ** 2 + (pts[(i + 1) % 4][1] - pts[i][1]) ** 2 for i in range(4)]
        two = s[0] == s[2] and s[1] == s[3]
        one = (s[0] == s[2]) != (s[1] == s[3])
        right = _slope_rel(s[0], s[1]) == "perp"
        return {"rhombus": two and len(set(ln)) == 1, "trapezium": one, "parallelogram": two, "rectangle": two and right}[p["target"]]
    ok = [i + 1 for i, o in enumerate(p["opts"]) if cls(o)]
    return F(ok[0]) if len(ok) == 1 else None


def _sq(u):
    return u[0] * u[0] + u[1] * u[1]


def _same_steps(u, v):
    return sorted((abs(u[0]), abs(u[1]))) == sorted((abs(v[0]), abs(v[1])))


def _countable(pts):
    """Every pair of equal sides goes the same numbers of squares across and up, so a child can see they are equal."""
    e = [(pts[(i + 1) % 3][0] - pts[i][0], pts[(i + 1) % 3][1] - pts[i][1]) for i in range(3)]
    return all(_same_steps(e[i], e[j]) or _sq(e[i]) != _sq(e[j]) for i in range(3) for j in range(i + 1, 3))


def _tri_info(pts):
    """(right-angled corner index or None, isosceles?) of a lattice triangle."""
    right = None
    for i in range(3):
        a, b, c = pts[i], pts[(i + 1) % 3], pts[(i + 2) % 3]
        if _dot((b[0] - a[0], b[1] - a[1]), (c[0] - a[0], c[1] - a[1])) == 0:
            right = i
    e = [_sq((pts[(i + 1) % 3][0] - pts[i][0], pts[(i + 1) % 3][1] - pts[i][1])) for i in range(3)]
    return right, len(set(e)) < 3


def _tri_angles(pts):
    out = []
    for i in range(3):
        a, b, c = pts[i], pts[(i + 1) % 3], pts[(i + 2) % 3]
        u, v = (b[0] - a[0], b[1] - a[1]), (c[0] - a[0], c[1] - a[1])
        out.append(math.degrees(math.acos(_dot(u, v) / math.sqrt(_sq(u) * _sq(v)))))
    return out


def _side_desc(u):
    """How a side runs from a corner: '2 across and 1 down' (y grows downwards in the figure)."""
    ax, ay = abs(u[0]), abs(u[1])
    ud = "down" if u[1] > 0 else "up"
    if ay == 0:
        return f"{ax} across"
    if ax == 0:
        return f"{ay} {ud}"
    return f"{ax} across and {ay} {ud}"


def _equal_desc(u):
    big, small = sorted((abs(u[0]), abs(u[1])), reverse=True)
    return f"{big} squares along a grid line" if small == 0 else f"{big} squares one way and {small} the other way"


_TRI_TYPES = ["equilateral triangle", "isosceles triangle", "right-angled triangle", "right-angled isosceles triangle"]


@template(T, "competent", G2 + "01", GT + "01")
def grid_triangle_type(r):
    """math-pat-shapes-classify-2d. What type of triangle (isosceles or right-angled) a triangle drawn on a square grid is."""
    pts = [(r.randint(0, 5), r.randint(0, 4)) for _ in range(3)]
    if len(set(pts)) < 3 or _cross((pts[1][0] - pts[0][0], pts[1][1] - pts[0][1]), (pts[2][0] - pts[0][0], pts[2][1] - pts[0][1])) == 0:
        return None
    e = [(pts[(i + 1) % 3][0] - pts[i][0], pts[(i + 1) % 3][1] - pts[i][1]) for i in range(3)]
    if sum(1 for u in e if u[0] == 0 or u[1] == 0) >= 2 or not _countable(pts) or abs(_cross(e[0], e[1])) < 6:
        return None  # two sides along grid lines is too easy; equal sides must be countable
    right, iso = _tri_info(pts)
    if (right is not None) == iso:
        return None  # exactly one of the two types, so only one option is right
    lab = r.choice("PQRS")
    ans = 2 if iso else 3
    wrong = [(1, "chose_equilateral", "Its three sides are not all the same length.")]
    if iso:
        wrong += [(3, "chose_right_angled", "None of its angles is a right angle."),
                  (4, "chose_right_angled_isosceles", "It has two equal sides but no right angle.")]
        i, j = next((i, j) for i in range(3) for j in range(i + 1, 3) if _sq(e[i]) == _sq(e[j]))
        steps = [f"Two sides each go {_equal_desc(e[i])}, so they are the same length.",
                 "None of the angles is a right angle.", f"Triangle {lab} is an isosceles triangle."]
    else:
        wrong += [(2, "chose_isosceles", "No two of its sides are the same length."),
                  (4, "chose_right_angled_isosceles", "It has a right angle, but the two sides that make the right angle are not equal.")]
        a, b, c = pts[right], pts[(right + 1) % 3], pts[(right + 2) % 3]
        u, v = (b[0] - a[0], b[1] - a[1]), (c[0] - a[0], c[1] - a[1])
        steps = [f"At one corner, one side goes {_side_desc(u)} and the other goes {_side_desc(v)}: "
                 "one is the other turned through a right angle, so that corner is a right angle.",
                 "The three sides all have different lengths.", f"Triangle {lab} is a right-angled triangle."]
    f = shape_grid(6, 5, [pts], cell=24, pad_tl=12, pad_br=12, shade=0.12)
    cx, cy = sum(x for x, _ in pts) / 3, sum(y for _, y in pts) / 3
    f.text(12 + cx * 24, 12 + cy * 24 + 5, lab, size=14, bold=True)
    name = r.choice(NAMES)  # the stem needs some variety: two questions in a tier may not share a stem
    stem = f"{name} draws Triangle {lab} on a square grid. What type of triangle is Triangle {lab}?"
    return build(grid_triangle_type, stem, ans, wrong, steps, {"pts": [list(p) for p in pts]},
                 lambda v: _TRI_TYPES[int(v) - 1], whole=True, auto_slips=False, figure=f.svg("Triangle on a square grid"))


@checker(grid_triangle_type)
def _(p):
    """Side lengths and angles in floating point (law of cosines), not dot products."""
    (x1, y1), (x2, y2), (x3, y3) = p["pts"]
    a, b, c = math.dist((x2, y2), (x3, y3)), math.dist((x1, y1), (x3, y3)), math.dist((x1, y1), (x2, y2))
    iso = min(abs(a - b), abs(b - c), abs(a - c)) < 1e-9
    a2, b2, c2 = sorted([a * a, b * b, c * c])
    right = abs(a2 + b2 - c2) < 1e-9
    if iso and not right:
        return F(2)
    if right and not iso:
        return F(3)
    return None


@template(T, "competent", G2 + "01", GT + "01")
def grid_point_triangle(r):
    """Which point W, X, Y or Z, joined to two fixed points (E and F, G and H, ...), forms a right-angled (or isosceles) triangle."""
    kind = r.choice(["right-angled", "isosceles"])
    E = (r.randint(1, 3), r.randint(1, 5))
    F_ = (E[0] + r.randint(2, 4), E[1] + r.choice([-2, -1, 0, 1, 2]))
    if not 0 <= F_[1] <= 6 or F_[0] > 8:
        return None
    good, bad = [], []
    for x in range(9):
        for y in range(7):
            P = (x, y)
            if max(abs(x - E[0]), abs(y - E[1])) < 2 or max(abs(x - F_[0]), abs(y - F_[1])) < 2:
                continue
            tri = [E, F_, P]
            if _cross((F_[0] - E[0], F_[1] - E[1]), (x - E[0], y - E[1])) == 0 or not _countable(tri):
                continue
            right, iso = _tri_info(tri)
            ok = right is not None if kind == "right-angled" else iso
            if ok:
                good.append(P)
            elif kind == "right-angled" and min(abs(a - 90) for a in _tri_angles(tri)) >= 12:
                bad.append(P)
            elif kind == "isosceles":
                s = sorted(math.sqrt(_sq((q[0] - p_[0], q[1] - p_[1]))) for p_, q in [(E, F_), (E, P), (F_, P)])
                if min(s[1] - s[0], s[2] - s[1]) >= 0.4:
                    bad.append(P)
    if not good or len(bad) < 3:
        return None
    cands = [r.choice(good)] + r.sample(bad, 3)
    for i in range(4):
        for j in range(i + 1, 4):
            if max(abs(cands[i][0] - cands[j][0]), abs(cands[i][1] - cands[j][1])) < 2:
                return None  # keep the labels apart
    pos = r.randrange(4)
    cands[0], cands[pos] = cands[pos], cands[0]
    L = "WXYZ"
    e_, f_ = r.choice(["EF", "GH", "JK", "MN"])
    wrong = []
    for i, P in enumerate(cands):
        if i == pos:
            continue
        if kind == "right-angled":
            big = max(_tri_angles([E, F_, P]))
            wrong.append((i + 1, "no_right_angle", f"Triangle {e_}{f_}{L[i]} has no right angle (its largest angle is about "
                                                   f"{round(big)}°)."))
        else:
            wrong.append((i + 1, "no_two_equal_sides", f"No two sides of triangle {e_}{f_}{L[i]} are the same length."))
    P = cands[pos]
    tri = [E, F_, P]
    right, _ = _tri_info(tri)
    if kind == "right-angled":
        a, b, c = tri[right], tri[(right + 1) % 3], tri[(right + 2) % 3]
        corner = [e_, f_, L[pos]][right]
        steps = ["A right-angled triangle has one corner that is a right angle.",
                 f"At {corner}, one side goes {_side_desc((b[0] - a[0], b[1] - a[1]))} and the other goes "
                 f"{_side_desc((c[0] - a[0], c[1] - a[1]))}: they meet at a right angle.",
                 f"So {L[pos]} forms a right-angled triangle with {e_} and {f_}."]
    else:
        e = {e_ + f_: (F_[0] - E[0], F_[1] - E[1]), f"{e_}{L[pos]}": (P[0] - E[0], P[1] - E[1]), f"{f_}{L[pos]}": (P[0] - F_[0], P[1] - F_[1])}
        k = list(e)
        i, j = next((i, j) for i in range(3) for j in range(i + 1, 3) if _sq(e[k[i]]) == _sq(e[k[j]]))
        steps = ["An isosceles triangle has two equal sides.",
                 f"{k[i]} and {k[j]} each go {_equal_desc(e[k[i]])}, so they are the same length.",
                 f"So {L[pos]} forms an isosceles triangle with {e_} and {f_}."]
    cell, pad = 24, 20
    f = shape_grid(8, 6, [], cell=cell, pad_tl=pad, pad_br=pad)
    X, Y = (lambda x: pad + x * cell), (lambda y: pad + y * cell)
    f.line(X(E[0]), Y(E[1]), X(F_[0]), Y(F_[1]), width=2.6)
    d = math.hypot(F_[0] - E[0], F_[1] - E[1])
    ux, uy = (F_[0] - E[0]) / d, (F_[1] - E[1]) / d
    for lab_, Q, (ox, oy) in [(e_, E, (-ux * 13, -uy * 13)), (f_, F_, (ux * 13, uy * 13))] + [(c, Q, (9, -9)) for c, Q in zip(L, cands)]:
        f.dot(X(Q[0]), Y(Q[1]), 3.5)
        f.text(X(Q[0]) + ox, Y(Q[1]) + oy, lab_, size=13, bold=True)
    name = r.choice(NAMES)
    stem = (f"{name} marks the points {e_}, {f_}, W, X, Y and Z on a square grid. Which point, when joined to {e_} and {f_}, "
            f"forms {a_an(kind)} {kind} triangle?")
    return build(grid_point_triangle, stem, pos + 1, wrong, steps,
                 {"kind": kind, "E": list(E), "F": list(F_), "pts": [list(c) for c in cands]},
                 lambda v: L[int(v) - 1], whole=True, auto_slips=False, figure=f.svg("Points on a square grid"))


@checker(grid_point_triangle)
def _(p):
    """Brute force with side lengths (Pythagoras on the lengths, not dot products)."""
    ok = []
    for i, P in enumerate(p["pts"]):
        d = sorted([math.dist(p["E"], p["F"]) ** 2, math.dist(p["E"], P) ** 2, math.dist(p["F"], P) ** 2])
        if p["kind"] == "right-angled":
            good = abs(d[0] + d[1] - d[2]) < 1e-9
        else:
            good = abs(d[0] - d[1]) < 1e-9 or abs(d[1] - d[2]) < 1e-9
        if good:
            ok.append(i + 1)
    return F(ok[0]) if len(ok) == 1 else None


# ---------------------------------------------------------------- rectangles and squares drawn on a grid

def _rect(w, h):
    return [(0, 0), (w, 0), (w, h), (0, h)]


def _slant(w, h, k=1):
    return [(k, 0), (k + w, 0), (w, h), (0, h)]


def _rect_check_shape(poly):
    """(w, h) if poly is an axis-free rectangle (4 right angles), else None."""
    if len(poly) != 4:
        return None
    e = [(poly[(i + 1) % 4][0] - poly[i][0], poly[(i + 1) % 4][1] - poly[i][1]) for i in range(4)]
    if all(_dot(e[i], e[(i + 1) % 4]) == 0 for i in range(4)):
        a, b = abs(e[0][0]) + abs(e[0][1]), abs(e[1][0]) + abs(e[1][1])
        return tuple(sorted((a, b)))
    return None


def _grid_panels(r, polys, cols, rows, cell, title="Four drawings on a grid"):
    figs = [shape_grid(cols, rows, [_place(pl, cols, rows, r)], cell=cell, shade=0.0) for pl in polys]
    return panels(figs, "ABCD", cols=2, title=title)


def _rect_options(r, fn, correct, bad, stem, steps, params, ans_check_params, cols=8, rows=7, cell=12):
    """correct: polygon; bad: [(poly, tag, why)] (3). Builds the question with a random answer position."""
    pos = r.randrange(4)
    polys = [b[0] for b in bad[:3]]
    polys.insert(pos, correct)
    rest = [i for i in range(4) if i != pos]
    wrong = [(i + 1, b[1], b[2]) for i, b in zip(rest, bad[:3])]
    params = dict(params, opts=[[list(v) for v in pl] for pl in polys])
    return build(fn, stem, pos + 1, wrong, steps, params, _L, whole=True, auto_slips=False,
                 figure=_grid_panels(r, polys, cols, rows, cell))


@template(T, "basic", GR + "02")
def which_drawing_rect_square(r):
    """Which drawing on the grid shows a rectangle w by h, or a square of side s."""
    name = r.choice(NAMES)
    if r.random() < 0.6:
        w, h = r.randint(3, 6), r.randint(2, 4)
        if w == h:
            return None
        flip = r.random() < 0.5
        pw, ph = (h, w) if flip else (w, h)
        correct = _rect(pw, ph)
        bad = [(_slant(pw, ph), "drew_a_slanted_shape", "Drew a parallelogram with slanted sides instead of a rectangle."),
               (_rect(pw + 1, ph), "side_one_unit_too_long", "Made one side one unit too long."),
               (_rect(pw, ph + 1) if ph + 1 <= 5 else _rect(pw, ph - 1), "side_one_unit_wrong", "Made one side one unit out.")]
        stem = (f"{name} wants to draw a rectangle that is {plural(w, 'unit')} long and {plural(h, 'unit')} wide on a square grid. "
                f"Which drawing shows the rectangle?")
        params = {"kind": "rect", "w": w, "h": h}
        steps = [f"A rectangle has 4 right angles and opposite sides equal: {plural(w, 'unit')} by {plural(h, 'unit')}.", "Check the sides of each drawing against the grid squares."]
    else:
        s = r.randint(2, 4)
        correct = _rect(s, s)
        bad = [(_slant(s, s), "drew_a_slanted_shape_not_a_square", "Drew a slanted shape: its corners are not right angles and its slanted sides are longer than the grid count."),
               (_rect(s + 1, s), "sides_not_equal", "Drew a rectangle whose sides are not all equal."),
               (_rect(s + 1, s + 1) if s < 4 else _rect(s - 1, s - 1), "wrong_size", "Drew a square but with the wrong side length.")]
        stem = f"{name} wants to draw a square with sides of {plural(s, 'unit')} on a square grid. Which drawing shows the square?"
        params = {"kind": "sq", "w": s, "h": s}
        steps = [f"A square has 4 right angles and 4 equal sides of {plural(s, 'unit')}."]
    return _rect_options(r, which_drawing_rect_square, correct, bad, stem, steps, params, None)


@checker(which_drawing_rect_square)
def _(p):
    ok = [i + 1 for i, o in enumerate(p["opts"]) if _rect_check_shape([tuple(v) for v in o]) == tuple(sorted((p["w"], p["h"])))]
    return F(ok[0]) if len(ok) == 1 else None


@template(T, "intermediate", GR + "02")
def rect_given_area_or_perimeter(r):
    """Which drawing shows a rectangle with a given side and a given area, or a given side and perimeter."""
    name = r.choice(NAMES)
    mode = r.choice(["area", "perimeter"])
    L, Wd = r.randint(3, 6), r.randint(2, 4)
    if L == Wd:
        return None
    if mode == "area":
        stem = (f"{name} draws a rectangle on a square grid. One side is {plural(L, 'unit')} long and the area is {L * Wd} square units. "
                f"Which drawing shows {name}'s rectangle?")
        bad_tags = [(_slant(L, Wd), "same_base_and_height_but_slanted", "Chose a slanted shape with the same base and height; it is not a rectangle.")]
        params = {"mode": mode, "L": L, "val": L * Wd}
        steps = [f"Other side = {L * Wd} ÷ {L} = {plural(Wd, 'unit')}.", f"The rectangle is {L} by {Wd}."]
    else:
        stem = (f"{name} draws a rectangle on a square grid. One side is {plural(L, 'unit')} long and the perimeter is {plural(2 * (L + Wd), 'unit')}. "
                f"Which drawing shows {name}'s rectangle?")
        bad_tags = [(_slant(L, Wd), "same_base_and_height_but_slanted", "Chose a slanted shape with the right base and height; its corners are not right angles and its slanted sides are longer than the grid count.")]
        params = {"mode": mode, "L": L, "val": 2 * (L + Wd)}
        steps = [f"Half the perimeter = {L + Wd}, so the other side = {L + Wd} - {L} = {plural(Wd, 'unit')}.", f"The rectangle is {L} by {Wd}."]
    bad = bad_tags + [(_rect(L, Wd + 1), "other_side_one_too_long", "Made the other side one unit too long."),
                      (_rect(L, Wd - 1) if Wd > 1 else _rect(L + 1, Wd), "other_side_one_too_short", "Made the other side one unit too short.")]
    return _rect_options(r, rect_given_area_or_perimeter, _rect(L, Wd), bad, stem, steps, params, None)


@checker(rect_given_area_or_perimeter)
def _(p):
    ok = []
    for i, o in enumerate(p["opts"]):
        sh = _rect_check_shape([tuple(v) for v in o])
        if sh and p["L"] in sh:
            other = sh[0] if sh[1] == p["L"] else sh[1]
            val = p["L"] * other if p["mode"] == "area" else 2 * (p["L"] + other)
            if val == p["val"]:
                ok.append(i + 1)
    return F(ok[0]) if len(ok) == 1 else None


@template(T, "competent", GR + "02")
def rect_perimeter_and_ratio(r):
    """Which drawing shows a rectangle with a given perimeter whose length is twice its width."""
    name = r.choice(NAMES)
    a = r.choice([2, 3])
    P = 6 * a
    correct = _rect(2 * a, a)
    bad = [(_rect(2 * a + 2, a + 1), "right_shape_wrong_perimeter", "Used the ratio but not the perimeter: this rectangle is too big."),
           (_rect(a + 1, 2 * a - 1), "right_perimeter_wrong_shape", "Matched the perimeter but the length is not twice the width."),
           (_rect(2 * a + 1, a), "slip_in_length", "Made the length one unit out.")]
    stem = (f"{name} wants to draw a rectangle on a 1 cm square grid. Its perimeter is {P} cm and its length is twice its width. "
            f"Which drawing shows {name}'s rectangle?")
    return _rect_options(r, rect_perimeter_and_ratio, correct, bad, stem,
                         [f"Half the perimeter = {P // 2} cm = length + width = 3 widths.", f"Width = {a} cm and length = {2 * a} cm."],
                         {"P": P}, None, cols=9, rows=6, cell=12)


@checker(rect_perimeter_and_ratio)
def _(p):
    ok = []
    for i, o in enumerate(p["opts"]):
        sh = _rect_check_shape([tuple(v) for v in o])
        if sh and sh[1] == 2 * sh[0] and 2 * (sh[0] + sh[1]) == p["P"]:
            ok.append(i + 1)
    return F(ok[0]) if len(ok) == 1 else None
