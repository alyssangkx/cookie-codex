"""Area and Volume (math-area-and-volume): area/perimeter, triangles, cuboids and circles, three levels each."""
import math

from common import *
from figures import Fig
from figures_C import (PB, UF, beaker_svg, cells_fig, cubes_svg, num, rectilinear, tank_svg, tri_fig)

T = "math-area-and-volume"
AP_ = "math-area-and-volume-area-and-perimeter-"
AT_ = "math-area-and-volume-area-of-triangle-"
VC_ = "math-area-and-volume-volume-of-cube-and-cuboid-"
CI_ = "math-area-and-volume-area-and-circumference-of-circle-"
AP1, AP2, AP3, AP4, AP5, AP6, AP7 = (AP_ + f"0{i}" for i in range(1, 8))
AT1, AT2, AT3 = (AT_ + f"0{i}" for i in range(1, 4))
VC1, VC2, VC4, VC5, VC6, VC7, VC8, VC9, VC10 = (VC_ + n for n in ("01", "02", "04", "05", "06", "07", "08", "09", "10"))
CI1, CI2, CI3 = (CI_ + f"0{i}" for i in range(1, 4))


def U(u):
    return lambda v: f"{num(v)} {u}"


def nm(r):
    return r.choice(NAMES)


def L(x, u="cm"):
    return f"{num(x)} {u}"


# ================================================================ area and perimeter: basic

def rand_cells(r, n, maxw=5, maxh=4):
    while True:
        cells = {(r.randrange(maxw), r.randrange(maxh))}
        while len(cells) < n:
            x, y = r.choice(sorted(cells))
            dx, dy = r.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
            if 0 <= x + dx < maxw and 0 <= y + dy < maxh:
                cells.add((x + dx, y + dy))
        mx, my = min(x for x, _ in cells), min(y for _, y in cells)
        cells = {(x - mx, y - my) for x, y in cells}
        if max(x for x, _ in cells) >= 1 and max(y for _, y in cells) >= 1:
            return cells


def edges_gen(cells):
    adj = sum(1 for (x, y) in cells if (x + 1, y) in cells) + sum(1 for (x, y) in cells if (x, y + 1) in cells)
    return 4 * len(cells) - 2 * adj


def edges_check(cells):
    return sum(1 for (x, y) in cells for d in ((1, 0), (-1, 0), (0, 1), (0, -1)) if (x + d[0], y + d[1]) not in cells)


@template(T, "basic", AP2, AP1, AP3)
def unit_squares(r):
    n = r.randint(6, 12)
    cells = rand_cells(r, n)
    ask = r.choice(["area", "perimeter"])
    name = nm(r)
    thing = r.choice(["square tiles", "square stickers", "square cards", "square paper pieces"])
    w = max(x for x, _ in cells) + 1
    h = max(y for _, y in cells) + 1
    per, ar = edges_gen(cells), len(cells)
    stem = (f"{name} joins {thing}, each 1 cm by 1 cm, to make the figure shown. "
            f"What is the {ask} of the figure, in {'cm²' if ask == 'area' else 'cm'}?")
    fig = cells_fig(cells)
    if ask == "area":
        return build(unit_squares, stem, ar, [
            (per, "found_perimeter_instead", "Counted the outside edges instead of the squares."),
            (w * h, "used_bounding_rectangle", "Used the rectangle that covers the whole figure."),
            (ar + 1, "miscounted_squares", "Counted one square too many."),
            (ar - 1, "miscounted_squares", "Missed one square."),
        ], [f"Count the squares: {ar}.", f"Each square is 1 cm², so the area is {ar} cm²."],
            {"cells": sorted(cells), "ask": ask}, U("cm²"), whole=True, auto_slips=False, figure=fig)
    return build(unit_squares, stem, per, [
        (ar, "found_area_instead", "Counted the squares instead of the edges."),
        (2 * (w + h), "used_bounding_rectangle", "Used the perimeter of the rectangle that covers the figure."),
        (per + 2, "miscounted_edges", "Counted two edges too many."),
        (per - 2, "miscounted_edges", "Missed two edges."),
    ], [f"Count the edges on the outside: {per}.", f"Each edge is 1 cm, so the perimeter is {per} cm."],
        {"cells": sorted(cells), "ask": ask}, U("cm"), whole=True, auto_slips=False, figure=fig)


@checker(unit_squares)
def _(p):
    cells = {tuple(c) for c in p["cells"]}
    return F(len(cells)) if p["ask"] == "area" else F(edges_check(cells))


RECT_OBJ = ["card", "poster", "garden bed", "tabletop", "notice board", "picture frame", "football pitch model", "rug"]


@template(T, "basic", AP3)
def rect_perimeter(r):
    a, b = r.sample(range(3, 21), 2)
    name, obj = nm(r), r.choice(RECT_OBJ)
    stem = f"The figure shows {name}'s rectangular {obj}. What is its perimeter?"
    fig = rectilinear([(0, 0), (a, 0), (a, b), (0, b)], {0: L(a), 1: L(b)})
    return build(rect_perimeter, stem, 2 * (a + b), [
        (a * b, "found_area_instead", "Multiplied the length by the width."),
        (a + b, "forgot_to_double", "Added only two sides."),
        (2 * a + b, "added_only_three_sides", "Added only three sides."),
        (2 * (a + b) + 2, "slip_in_addition", "Made a slip in the addition."),
        (2 * (a + b) - 2, "slip_in_addition", "Made a slip in the addition."),
    ], [f"Perimeter = 2 × ({a} + {b})", f"= {2 * (a + b)} cm"], {"a": a, "b": b}, U("cm"), whole=True,
        auto_slips=False, figure=fig)


@checker(rect_perimeter)
def _(p):
    return F(p["a"] + p["b"] + p["a"] + p["b"])


@template(T, "basic", AP4)
def rect_area(r):
    a, b = r.sample(range(3, 16), 2)
    name, obj = nm(r), r.choice(RECT_OBJ)
    stem = f"The figure shows {name}'s rectangular {obj}. What is its area?"
    fig = rectilinear([(0, 0), (a, 0), (a, b), (0, b)], {0: L(a), 1: L(b)})
    return build(rect_area, stem, a * b, [
        (2 * (a + b), "found_perimeter_instead", "Added all the sides."),
        (a + b, "added_instead_of_multiplied", "Added the length and width."),
        (a * b + a, "slip_in_multiplication", "Made a slip in the multiplication."),
        (a * b - b, "slip_in_multiplication", "Made a slip in the multiplication."),
    ], [f"Area = {a} × {b}", f"= {a * b} cm²"], {"a": a, "b": b}, U("cm²"), whole=True, auto_slips=False, figure=fig)


@checker(rect_area)
def _(p):
    return F(sum(p["a"] for _ in range(p["b"])))


@template(T, "basic", AP3, AP4)
def square_perim_area(r):
    s = r.randint(3, 15)
    ask = r.choice(["perimeter", "area"])
    name = nm(r)
    stem = f"The figure shows {name}'s square tile. What is its {ask}?"
    fig = rectilinear([(0, 0), (s, 0), (s, s), (0, s)], {0: L(s)})
    if ask == "perimeter":
        return build(square_perim_area, stem, 4 * s, [
            (s * s, "found_area_instead", "Multiplied the side by itself."),
            (2 * s, "added_only_two_sides", "Added only two sides."),
            (3 * s, "added_only_three_sides", "Added only three sides."),
            (4 * s + 4, "slip_in_addition", "Made a slip in the addition."),
        ], [f"Perimeter = 4 × {s} = {4 * s} cm"], {"s": s, "ask": ask}, U("cm"), whole=True, auto_slips=False, figure=fig)
    return build(square_perim_area, stem, s * s, [
        (4 * s, "found_perimeter_instead", "Added all four sides."),
        (2 * s, "doubled_instead_of_squared", "Multiplied the side by 2."),
        (s * s + s, "slip_in_multiplication", "Made a slip in the multiplication."),
        (s * s - s, "slip_in_multiplication", "Made a slip in the multiplication."),
    ], [f"Area = {s} × {s} = {s * s} cm²"], {"s": s, "ask": ask}, U("cm²"), whole=True, auto_slips=False, figure=fig)


@checker(square_perim_area)
def _(p):
    return F(sum(p["s"] for _ in range(4))) if p["ask"] == "perimeter" else F(p["s"] * p["s"])


@template(T, "basic", AP5)
def missing_side(r):
    a, b = r.sample(range(4, 25), 2)
    name = nm(r)
    if r.random() < 0.5:
        A = a * b
        stem = f"A rectangle has an area of {A} cm² and a length of {a} cm. What is its width?"
        return build(missing_side, stem, b, [
            (A - a, "subtracted_instead_of_divided", "Subtracted the length from the area."),
            (A // 2 // a if (A // 2) % a == 0 else None, "halved_the_area", "Halved the area before dividing."),
            (b + 1, "slip_in_division", "Made a slip in the division."),
            (b - 1, "slip_in_division", "Made a slip in the division."),
            (A * a, "multiplied_instead_of_divided", "Multiplied the area by the length."),
        ], [f"Width = {A} ÷ {a} = {b} cm"], {"mode": "area", "A": A, "a": a}, U("cm"), whole=True, auto_slips=False)
    P = 2 * (a + b)
    stem = f"A rectangle has a perimeter of {P} cm and a length of {a} cm. What is its width?"
    return build(missing_side, stem, b, [
        (P - a, "forgot_to_halve_perimeter", "Subtracted the length from the perimeter only."),
        (P // 2, "gave_length_plus_width", "Gave the sum of the length and width."),
        (P - 2 * a, "forgot_to_halve_remainder", "Did not halve after taking away two lengths."),
        (b + 1, "slip_in_working", "Made a slip in the working."),
    ], [f"Length + width = {P} ÷ 2 = {P // 2} cm", f"Width = {P // 2} - {a} = {b} cm"],
        {"mode": "perim", "P": P, "a": a}, U("cm"), whole=True, auto_slips=False)


@checker(missing_side)
def _(p):
    if p["mode"] == "area":
        return F(next(w for w in range(1, 1000) if w * p["a"] == p["A"]))
    return F(next(w for w in range(1, 1000) if 2 * (w + p["a"]) == p["P"]))


@template(T, "basic", AP6)
def square_side(r):
    s = r.randint(3, 20)
    if r.random() < 0.5:
        A = s * s
        stem = f"A square has an area of {A} cm². What is the length of one side?"
        return build(square_side, stem, s, [
            (A // 2 if A % 2 == 0 else None, "halved_the_area", "Divided the area by 2."),
            (A // 4 if A % 4 == 0 else None, "divided_area_by_4", "Divided the area by 4."),
            (s * 2, "doubled_the_side", "Gave twice the side."),
            (s + 1, "slip_in_working", "Made a slip in the working."),
            (s - 1, "slip_in_working", "Made a slip in the working."),
            (A - s, "slip_in_working", "Made a slip in the working."),
        ], [f"{s} × {s} = {A}, so each side is {s} cm."], {"mode": "area", "v": A}, U("cm"), whole=True, auto_slips=False)
    P = 4 * s
    stem = f"A square has a perimeter of {P} cm. What is its area?"
    return build(square_side, stem, s * s, [
        (P * P, "squared_the_perimeter", "Squared the perimeter."),
        (P // 2 * 2, "found_perimeter_again", "Gave the perimeter."),
        (s * 4, "gave_perimeter", "Multiplied the side by 4."),
        (s * s + s, "slip_in_working", "Made a slip in the working."),
        (P // 2, "halved_the_perimeter", "Halved the perimeter."),
    ], [f"Side = {P} ÷ 4 = {s} cm", f"Area = {s} × {s} = {s * s} cm²"], {"mode": "perim", "v": P}, U("cm²"), whole=True, auto_slips=False)


@checker(square_side)
def _(p):
    if p["mode"] == "area":
        return F(next(s for s in range(1, 200) if s * s == p["v"]))
    s = next(s for s in range(1, 200) if 4 * s == p["v"])
    return F(s * s)


# ================================================================ area and perimeter: intermediate

def shape_L(a, b, c, d):
    return [(0, 0), (a, 0), (a, b), (c, b), (c, d), (0, d)], {0: a, 1: b, 4: c, 5: d}


def shape_T(a, b, c, d, p):
    return [(0, 0), (a, 0), (a, b), (p + c, b), (p + c, b + d), (p, b + d), (p, b), (0, b)], {0: a, 1: b, 4: c, 5: d}


def shoelace(v):
    return F(abs(sum(v[i][0] * v[(i + 1) % len(v)][1] - v[(i + 1) % len(v)][0] * v[i][1] for i in range(len(v)))), 2)


def perim_of(v):
    return sum(abs(v[i][0] - v[(i + 1) % len(v)][0]) + abs(v[i][1] - v[(i + 1) % len(v)][1]) for i in range(len(v)))


@template(T, "intermediate", AP7)
def composite_rectilinear(r):
    u = r.choice(["cm", "m"])
    kind = r.choice(["L", "T"])
    ask = r.choice(["area", "perimeter"])
    name = nm(r)
    if kind == "L":
        a = r.randint(8, 16)
        c = r.randint(3, a - 3)
        d = r.randint(8, 15)
        b = r.randint(3, d - 3)
        verts, labs = shape_L(a, b, c, d)
        area = a * b + c * (d - b)
        per = 2 * (a + d)
        w_area = [(a * d, "used_the_whole_rectangle", "Treated the figure as the big rectangle."),
                  (a * b + c * d, "counted_a_part_twice", f"Counted the {c} by {b} part twice."),
                  (a * b + (a - c) * (d - b), "used_the_missing_piece", "Used the missing corner instead of the lower part.")]
        w_per = [(a + b + c + d, "added_only_the_labelled_sides", "Added only the four labelled sides."),
                 (a * d, "found_area_instead", "Found the area of the big rectangle."),
                 (2 * (a + d) - 2 * (a - c), "left_out_the_steps", "Left out the sides of the step."),
                 (2 * (a + d) + 2 * (a - c), "counted_the_step_twice", "Counted the step twice.")]
    else:
        a = r.randint(10, 18)
        b = r.randint(3, 6)
        c = r.randint(3, a - 6)
        d = r.randint(4, 10)
        p_ = r.randint(2, a - c - 2)
        verts, labs = shape_T(a, b, c, d, p_)
        area = a * b + c * d
        per = 2 * (a + b + d)
        w_area = [(a * (b + d), "used_the_whole_rectangle", "Treated the figure as the big rectangle."),
                  (a * b + a * d, "used_wrong_width_for_the_stem", "Used the width of the bar for the stem."),
                  (a * b + c * d + c, "slip_in_addition", "Made a slip in the addition.")]
        w_per = [(a + b + c + d, "added_only_the_labelled_sides", "Added only the four labelled sides."),
                 (a * b + c * d, "found_area_instead", "Found the area."),
                 (2 * (a + b + d) - 2 * d, "left_out_the_stem", "Left out the sides of the stem."),
                 (2 * (a + b + c + d), "doubled_the_labelled_sides", "Doubled the four labelled sides.")]
    fig = rectilinear(verts, {i: L(v, u) for i, v in labs.items()})
    sq = "²"
    stem = (f"The figure shows the plan of {name}'s garden. All the angles are right angles. "
            f"Find the {ask} of the garden, in {u}{sq if ask == 'area' else ''}.")
    if ask == "area":
        return build(composite_rectilinear, stem, area, w_area + [(area + 2, "slip_in_addition", "Made a slip in the addition.")],
                     ["Split the figure into two rectangles and add their areas.", f"Area = {area} {u}²"],
                     {"kind": kind, "dims": [a, b, c, d] + ([p_] if kind == "T" else []), "ask": ask},
                     U(u + sq), whole=True, auto_slips=False, figure=fig)
    return build(composite_rectilinear, stem, per, w_per + [(per + 2, "slip_in_addition", "Made a slip in the addition.")],
                 ["The missing sides can be found from the labelled sides.", f"Perimeter = {per} {u}"],
                 {"kind": kind, "dims": [a, b, c, d] + ([p_] if kind == "T" else []), "ask": ask},
                 U(u), whole=True, auto_slips=False, figure=fig)


@checker(composite_rectilinear)
def _(p):
    d = p["dims"]
    v = shape_L(*d)[0] if p["kind"] == "L" else shape_T(*d)[0]
    return shoelace(v) if p["ask"] == "area" else F(perim_of(v))


@template(T, "intermediate", AP7, AP3)
def identical_squares(r):
    """math-pat-perimeter-composite-identical-pieces"""
    n = r.randint(5, 8)
    cells = rand_cells(r, n, 5, 3)
    s = r.randint(2, 6)
    A = n * s * s
    name = nm(r)
    per = edges_gen(cells) * s
    w = max(x for x, _ in cells) + 1
    h = max(y for _, y in cells) + 1
    stem = (f"The figure is made up of {n} identical squares. Its total area is {A} cm². "
            f"What is the perimeter of the figure? The figure is not drawn to scale.")
    return build(identical_squares, stem, per, [
        (4 * n * s, "added_all_square_perimeters", "Added the perimeters of all the separate squares."),
        (2 * (w + h) * s, "used_the_bounding_rectangle", "Used the perimeter of the rectangle around the figure."),
        (per + 2 * s, "counted_extra_edges", "Counted one square edge too many on each side."),
        (per - 2 * s, "missed_edges", "Missed some square edges."),
        (A // n, "gave_area_of_one_square", "Gave the area of one square."),
    ], [f"Area of one square = {A} ÷ {n} = {s * s} cm²", f"Side of a square = {s} cm", f"Count the sides on the outside: {edges_gen(cells)}",
        f"Perimeter = {edges_gen(cells)} × {s} = {per} cm"], {"cells": sorted(cells), "n": n, "A": A},
        U("cm"), whole=True, auto_slips=False, figure=cells_fig(cells))


@checker(identical_squares)
def _(p):
    cells = {tuple(c) for c in p["cells"]}
    s = next(s for s in range(1, 100) if s * s * p["n"] == p["A"])
    return F(edges_check(cells) * s)


def ring_rect(u, outer, inner, shade=0.18):
    """Shade the frame between two rectangles ((x0,y0,x1,y1) each)."""
    ox0, oy0, ox1, oy1 = outer
    ix0, iy0, ix1, iy1 = inner
    pb = PB(u).m(ox0, oy0).l(ox1, oy0).l(ox1, oy1).l(ox0, oy1).z().m(ix0, iy0).l(ix0, iy1).l(ix1, iy1).l(ix1, iy0).z()
    u.path(pb, shade=shade)


@template(T, "intermediate", AP7)
def path_around(r):
    a, b = r.sample(range(6, 19), 2)
    w = r.randint(1, 3)
    inside = r.random() < 0.5
    name = nm(r)
    if inside:
        Lo, Wo = a + 2 * w, b + 2 * w
        area = Lo * Wo - a * b
        u = UF(0, 0, Lo, Wo)
        ring_rect(u, (0, 0, Lo, Wo), (w, w, Lo - w, Wo - w))
        v = [(0, 0), (Lo, 0), (Lo, Wo), (0, Wo)]
        u.edge_label(v, 0, f"{Lo} m")
        u.edge_label(v, 1, f"{Wo} m")
        stem = (f"A rectangular lawn measures {Lo} m by {Wo} m. {name} lays a path {w} m wide along the inside edge of the lawn, "
                f"as shown by the shaded part. What is the area of the path?")
        wrongs = [(2 * w * (Lo + Wo), "forgot_the_overlap_at_corners", "Used 2 × width × (length + width) and counted the corners twice."),
                  (Lo * Wo - (Lo - w) * (Wo - w), "took_the_width_off_once", "Took the path width off only once from each side."),
                  (a * b, "gave_inner_area", "Gave the area of the grass that is left."),
                  (area + w * w, "slip_in_working", "Made a slip in the working.")]
        steps = [f"Inner rectangle: {Lo} - 2 × {w} = {a} m by {Wo} - 2 × {w} = {b} m", f"Area of path = {Lo} × {Wo} - {a} × {b} = {area} m²"]
        params = {"outer": [Lo, Wo], "inner": [a, b]}
    else:
        Lo, Wo = a + 2 * w, b + 2 * w
        area = Lo * Wo - a * b
        u = UF(0, 0, Lo, Wo)
        ring_rect(u, (0, 0, Lo, Wo), (w, w, Lo - w, Wo - w))
        vi = [(w, w), (Lo - w, w), (Lo - w, Wo - w), (w, Wo - w)]
        u.text(((Lo) / 2, Wo / 2), f"{a} m by {b} m", size=13)
        stem = (f"{name}'s rectangular garden is {a} m long and {b} m wide. A path {w} m wide is built all around the garden, "
                f"as shown by the shaded part. What is the area of the path?")
        wrongs = [(2 * w * (a + b), "forgot_the_corner_squares", "Left out the four corner squares of the path."),
                  (Lo * Wo, "gave_outer_area", "Gave the area of the garden and the path together."),
                  ((a + w) * (b + w) - a * b, "added_the_width_once", "Added the path width once to each side."),
                  (area + 4, "slip_in_working", "Made a slip in the working.")]
        steps = [f"Whole figure: {a} + 2 × {w} = {Lo} m by {b} + 2 × {w} = {Wo} m", f"Area of path = {Lo} × {Wo} - {a} × {b} = {area} m²"]
        params = {"outer": [Lo, Wo], "inner": [a, b]}
    params["inside"] = inside
    return build(path_around, stem, area, wrongs, steps, params, U("m²"), whole=True, auto_slips=False, figure=u.svg("Path"))


@checker(path_around)
def _(p):
    (Lo, Wo), (a, b) = p["outer"], p["inner"]
    return F(sum(1 for x in range(Lo) for y in range(Wo) if not (
        (Lo - a) // 2 <= x < (Lo - a) // 2 + a and (Wo - b) // 2 <= y < (Wo - b) // 2 + b)))


@template(T, "intermediate", AP5, AP3)
def rect_from_clues(r):
    w = r.randint(3, 12)
    if r.random() < 0.5:
        k = r.randint(2, 4)
        Lg = k * w
        P = 2 * (Lg + w)
        stem = f"The length of a rectangle is {k} times its width. Its perimeter is {P} cm. What is its area?"
        return build(rect_from_clues, stem, Lg * w, [
            ((P // 4) ** 2 if P % 4 == 0 else None, "treated_as_a_square", "Treated the rectangle as a square."),
            (Lg + w, "gave_half_the_perimeter", "Gave the sum of the length and width."),
            ((P // (k + 1)) * w if P % (k + 1) == 0 else None, "forgot_to_halve", f"Divided the perimeter by {k + 1} without halving."),
            (Lg * w + w, "slip_in_working", "Made a slip in the working."),
            (Lg * Lg, "used_length_twice", "Used the length twice."),
        ], [f"Half the perimeter = {P // 2} cm = {k + 1} units", f"Width = {w} cm, length = {Lg} cm", f"Area = {Lg} × {w} = {Lg * w} cm²"],
            {"k": k, "P": P, "mode": "k"}, U("cm²"), whole=True, auto_slips=False)
    d = r.randint(2, 9)
    Lg = w + d
    P = 2 * (Lg + w)
    stem = f"The length of a rectangle is {d} cm more than its width. Its perimeter is {P} cm. What is its area?"
    return build(rect_from_clues, stem, Lg * w, [
        ((P // 4) ** 2 if P % 4 == 0 else None, "treated_as_a_square", "Treated the rectangle as a square."),
        ((P // 2 - d) * d, "used_wrong_dimensions", "Multiplied the wrong pair of numbers."),
        (Lg * Lg, "used_length_twice", "Used the length twice."),
        (Lg * w + w, "slip_in_working", "Made a slip in the working."),
        (((P - d) // 2) * ((P + d) // 2) if (P - d) % 2 == 0 else None, "forgot_to_halve", "Did not halve correctly."),
    ], [f"Length + width = {P // 2} cm", f"Width = ({P // 2} - {d}) ÷ 2 = {w} cm", f"Area = {Lg} × {w} = {Lg * w} cm²"],
        {"d": d, "P": P, "mode": "d"}, U("cm²"), whole=True, auto_slips=False)


@checker(rect_from_clues)
def _(p):
    for w in range(1, 400):
        Lg = p["k"] * w if p["mode"] == "k" else w + p["d"]
        if 2 * (Lg + w) == p["P"]:
            return F(Lg * w)


@template(T, "intermediate", AP3, AP7)
def fence_cost(r):
    a, b = r.sample(range(8, 31), 2)
    c = r.choice([4, 5, 6, 8, 9, 12])
    name = nm(r)
    if r.random() < 0.5:
        stem = f"{name} fences a rectangular plot {a} m long and {b} m wide on all four sides. The fence costs ${c} per metre. What is the total cost of the fence?"
        cost = 2 * (a + b) * c
        return build(fence_cost, stem, cost, [
            (a * b * c, "used_area_instead", "Used the area instead of the perimeter."),
            ((a + b) * c, "forgot_to_double", "Used only half the perimeter."),
            ((2 * a + b) * c, "used_three_sides", "Used only three sides."),
            (cost + c, "slip_in_working", "Made a slip in the working."),
            (cost - c, "slip_in_working", "Made a slip in the working."),
        ], [f"Perimeter = 2 × ({a} + {b}) = {2 * (a + b)} m", f"Cost = {2 * (a + b)} × {c} = ${cost}"],
            {"a": a, "b": b, "c": c, "sides": 4}, money, whole=True, auto_slips=False)
    stem = (f"{name} fences a rectangular plot {a} m long and {b} m wide. One of the {a} m sides is a wall and needs no fence. "
            f"The fence costs ${c} per metre. What is the total cost of the fence?")
    cost = (a + 2 * b) * c
    return build(fence_cost, stem, cost, [
        (2 * (a + b) * c, "fenced_all_four_sides", "Fenced all four sides."),
        ((2 * a + b) * c, "left_out_a_wrong_side", "Left out a width instead of a length."),
        (a * b * c, "used_area_instead", "Used the area instead of the length of the fence."),
        (cost + c, "slip_in_working", "Made a slip in the working."),
        (cost - c, "slip_in_working", "Made a slip in the working."),
    ], [f"Length of fence = {a} + {b} + {b} = {a + 2 * b} m", f"Cost = {a + 2 * b} × {c} = ${cost}"],
        {"a": a, "b": b, "c": c, "sides": 3}, money, whole=True, auto_slips=False)


@checker(fence_cost)
def _(p):
    sides = [p["a"], p["b"], p["b"]] + ([p["a"]] if p["sides"] == 4 else [])
    return F(sum(sides) * p["c"])


@template(T, "intermediate", AP4, AP5)
def tiles_count(r):
    t = r.choice([20, 25, 50])
    a, b = r.randint(2, 9), r.randint(2, 7)
    Wm, Hm = a, b
    if (a * 100) % t or (b * 100) % t:
        return None
    n = (a * 100 // t) * (b * 100 // t)
    name = nm(r)
    stem = f"{name} covers a rectangular floor {a} m by {b} m with square tiles of side {t} cm. How many tiles are needed?"
    return build(tiles_count, stem, n, [
        (a * b * 100 * 100 // t, "divided_area_by_the_side", "Divided the area in cm² by the side length."),
        (2 * (a + b) * 100 // t, "used_perimeter", "Divided the perimeter by the side of a tile."),
        (a * b * 100 // t if (a * b * 100) % t == 0 else None, "wrong_unit_conversion", "Used 1 m² = 100 cm²."),
        (n + 10, "slip_in_working", "Made a slip in the working."),
        (n - 8, "slip_in_working", "Made a slip in the working."),
    ], [f"{a} m = {a * 100} cm, {b} m = {b * 100} cm", f"{a * 100} ÷ {t} = {a * 100 // t} tiles along, {b * 100} ÷ {t} = {b * 100 // t} tiles across",
        f"{a * 100 // t} × {b * 100 // t} = {n}"], {"a": a, "b": b, "t": t}, lambda v: f"{num(v)} tiles", whole=True, auto_slips=False)


@checker(tiles_count)
def _(p):
    W, H, t = p["a"] * 100, p["b"] * 100, p["t"]
    return F(sum(1 for x in range(0, W, t) for y in range(0, H, t)))


# ================================================================ area and perimeter: competent

def draw_rects(rects, w=340, h=230, shade=0.0):
    xs = [x for x0, y0, x1, y1 in rects for x in (x0, x1)]
    ys = [y for x0, y0, x1, y1 in rects for y in (y0, y1)]
    u = UF(min(xs), min(ys), max(xs), max(ys), w, h, mx=30, my=22)
    for x0, y0, x1, y1 in rects:
        u.poly([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], shade=shade)
    return u


@template(T, "competent", AP7, AP4)
def identical_rects(r):
    """math-pat-perimeter-area-identical-rectangles"""
    mode = r.choice(["D", "A"])
    name = nm(r)
    if mode == "D":
        n = r.randint(2, 4)
        v = r.randint(1, 4)
        w, l = 2 * v if n == 3 else v, 0
        w = v + 1
        l = n * w
        rects = [(0, 0, w, l)] + [(w, i * w, w + l, (i + 1) * w) for i in range(n)]
        pieces = n + 1
        Wt, Ht = w + l, l
    else:
        p_, q = r.choice([(3, 2), (4, 3), (5, 3), (5, 2)])
        v = r.randint(1, 3)
        w, l = q * v, p_ * v
        rects = [(i * w, 0, (i + 1) * w, l) for i in range(p_)] + [(i * l, l, (i + 1) * l, l + w) for i in range(q)]
        pieces = p_ + q
        Wt, Ht = p_ * w, l + w
    P = 2 * (Wt + Ht)
    ask = r.choice(["one", "whole"])
    fig = draw_rects(rects, shade=0.08).svg("Identical rectangles")
    small, whole_a = w * l, Wt * Ht
    if ask == "one":
        stem = (f"The figure is made up of {pieces} identical rectangles and is not drawn to scale. Its perimeter is {P} cm. "
                f"What is the area of one rectangle? ({name}'s puzzle)")
        ans = small
        wrong = [(whole_a, "found_whole_area", "Found the area of the whole figure."),
                 (w * w, "treated_as_a_square", "Treated the rectangle as a square."),
                 ((P // 4) ** 2 // pieces if ((P // 4) ** 2) % pieces == 0 else None, "treated_whole_as_square", "Treated the whole figure as a square."),
                 (small + w, "slip_in_working", "Made a slip in the working."),
                 (l * l, "used_length_twice", "Used the long side twice.")]
    else:
        stem = (f"The figure is made up of {pieces} identical rectangles and is not drawn to scale. Its perimeter is {P} cm. "
                f"What is the area of the whole figure? ({name}'s puzzle)")
        ans = whole_a
        wrong = [(small, "found_area_of_one", "Found the area of one rectangle only."),
                 (small * pieces + w, "slip_in_working", "Made a slip in the working."),
                 ((P // 4) ** 2, "treated_as_a_square", "Treated the figure as a square."),
                 (P * P // 16 + w, "slip_in_working", "Made a slip in the working."),
                 (whole_a + 2 * w, "slip_in_working", "Made a slip in the working.")]
    steps = [f"Compare the sides to find that the long side is {l} cm when the short side is {w} cm.",
             f"Whole figure: {Wt} cm by {Ht} cm, perimeter = {P} cm.", f"One rectangle = {w} × {l} = {small} cm²; whole = {whole_a} cm²"]
    return build(identical_rects, stem, ans, wrong, steps,
                 {"mode": mode, "P": P, "ask": ask, "pieces": pieces, "n": n if mode == "D" else None,
                  "pq": None if mode == "D" else [p_, q]}, U("cm²"), whole=True, auto_slips=False, figure=fig)


@checker(identical_rects)
def _(p):
    for v in range(1, 200):
        if p["mode"] == "D":
            n = p["n"]
            w = v
            l = n * w
            Wt, Ht = w + l, l
        else:
            pp, q = p["pq"]
            w, l = q * (v), pp * (v)
            Wt, Ht = pp * w, l + w
        if 2 * (Wt + Ht) == p["P"]:
            return F(w * l if p["ask"] == "one" else Wt * Ht)


@template(T, "competent", AP4, AP3)
def cut_squares(r):
    s = r.randint(4, 9)
    a, b = r.randint(5, 9) * s + r.randint(1, s - 1), r.randint(3, 6) * s + r.randint(1, s - 1)
    n = (a // s) * (b // s)
    by_area = (a * b) // (s * s)
    if by_area == n:
        return None
    name = nm(r)
    stem = (f"{name} has a rectangular sheet of card {a} cm long and {b} cm wide. {name} cuts out as many squares of side {s} cm "
            f"as possible, with no overlap. How many squares can be cut out?")
    return build(cut_squares, stem, n, [
        (by_area, "divided_areas", "Divided the area of the card by the area of one square."),
        (-(-a // s) * -(-b // s), "rounded_up_each_side", "Rounded up the squares along each side."),
        (n - (a // s), "slip_in_counting", "Counted one row too few."),
        (n + (b // s), "slip_in_counting", "Counted one row too many."),
        (a // s + b // s, "added_the_counts", "Added the numbers along each side."),
    ], [f"Along the length: {a} ÷ {s} = {a // s} squares (remainder {a % s})", f"Along the width: {b} ÷ {s} = {b // s} squares (remainder {b % s})",
        f"{a // s} × {b // s} = {n} squares"], {"a": a, "b": b, "s": s}, lambda v: f"{num(v)} squares", whole=True, auto_slips=False)


@checker(cut_squares)
def _(p):
    a, b, s = p["a"], p["b"], p["s"]
    return F(sum(1 for x in range(0, a - s + 1, s) for y in range(0, b - s + 1, s)))


@template(T, "competent", AP7, AP5)
def square_vs_rectangle(r):
    s = r.randint(8, 20)
    Lg = r.randint(s + 1, 2 * s - 2)
    w = 2 * s - Lg
    P = 4 * s
    diff = s * s - Lg * w
    name = nm(r)
    stem = (f"{name} bends a wire into a square of side {s} cm. {name} then bends the same wire into a rectangle with a length of "
            f"{Lg} cm. How much bigger is the area of the square than the area of the rectangle?")
    return build(square_vs_rectangle, stem, diff, [
        (abs(s * s - Lg * (P - Lg)), "used_perimeter_minus_length", "Took the width as the wire length minus the length."),
        (s * s - Lg * s, "used_side_as_width", "Used the side of the square as the width of the rectangle."),
        (Lg * w, "gave_rectangle_area", "Gave the area of the rectangle."),
        (diff + 2, "slip_in_working", "Made a slip in the working."),
        (diff - 1, "slip_in_working", "Made a slip in the working."),
    ], [f"Length of wire = 4 × {s} = {P} cm", f"Width of rectangle = {P // 2} - {Lg} = {w} cm", f"Areas: {s * s} cm² and {Lg * w} cm²", f"Difference = {diff} cm²"],
        {"s": s, "L": Lg}, U("cm²"), whole=True, auto_slips=False)


@checker(square_vs_rectangle)
def _(p):
    s, Lg = p["s"], p["L"]
    w = next(w for w in range(1, 200) if 2 * (Lg + w) == 4 * s)
    return F(s * s - Lg * w)


@template(T, "competent", AP5, AP4)
def length_increased(r):
    Lg = r.randint(12, 30)
    w = r.randint(8, 25)
    inc = r.choice([3, 4, 5, 6])
    d_area = inc * w
    name = nm(r)
    stem = (f"A rectangle is {Lg} cm long. When its width is increased by {inc} cm... ") if False else \
        (f"A rectangle is {Lg} cm long. When its length is increased by {inc} cm, its area increases by {d_area} cm². "
         f"What is the perimeter of the original rectangle?")
    P = 2 * (Lg + w)
    return build(length_increased, stem, P, [
        (Lg + w, "forgot_to_double", "Gave the sum of the length and width."),
        (2 * (Lg + inc + w), "used_the_new_length", "Used the new length."),
        (2 * (Lg + d_area // Lg) if d_area % Lg == 0 else None, "divided_by_the_wrong_side", "Divided the extra area by the length."),
        (P + 2, "slip_in_working", "Made a slip in the working."),
        (2 * (Lg + d_area), "used_extra_area_as_width", "Used the extra area as the width."),
    ], [f"Extra strip is {inc} cm by (width) = {d_area} cm²", f"Width = {d_area} ÷ {inc} = {w} cm", f"Perimeter = 2 × ({Lg} + {w}) = {P} cm"],
        {"L": Lg, "inc": inc, "d": d_area}, U("cm"), whole=True, auto_slips=False)


@checker(length_increased)
def _(p):
    w = next(w for w in range(1, 500) if w * p["inc"] == p["d"])
    return F(2 * (p["L"] + w))


@template(T, "competent", AP7)
def two_squares_step(r):
    k = r.choice([2, 3])
    a = r.randint(2, 6)
    P = 2 * a * (1 + 2 * k)
    ask = r.choice(["whole", "small"])
    name = nm(r)
    verts = [(0, k * a - a), (a, k * a - a), (a, 0), (a + k * a, 0), (a + k * a, k * a), (0, k * a)]
    u = UF(0, 0, a + k * a, k * a, mx=40, my=30)
    u.poly([(0, 0), (a, 0), (a, a), (0, a)] if False else [(0, k * a - a), (a, k * a - a), (a, k * a), (0, k * a)])
    u.poly([(a, 0), (a + k * a, 0), (a + k * a, k * a), (a, k * a)])
    area_whole = a * a * (1 + k * k)
    if ask == "whole":
        stem = (f"The figure is made up of a small square and a large square whose side is {k} times the side of the small square. "
                f"The perimeter of the figure is {P} cm. What is the area of the figure?")
        ans = area_whole
        wrong = [(a * a, "found_small_square_only", "Found the area of the small square only."),
                 (k * a * k * a, "found_large_square_only", "Found the area of the large square only."),
                 (((P // 4) ** 2), "treated_as_a_square", "Treated the figure as one square."),
                 ((P // (4 * (1 + k))) ** 2 * (1 + k * k), "added_all_the_perimeters", "Treated the perimeter as the sum of the perimeters of both squares."),
                 (area_whole + a, "slip_in_working", "Made a slip in the working.")]
    else:
        stem = (f"The figure is made up of a small square and a large square whose side is {k} times the side of the small square. "
                f"The perimeter of the figure is {P} cm. What is the area of the large square?")
        ans = (k * a) ** 2
        wrong = [(a * a, "found_small_square_only", "Found the area of the small square only."),
                 (area_whole, "found_whole_area", "Found the area of the whole figure."),
                 ((P // (4 * (1 + k)) * k) ** 2, "added_all_the_perimeters", "Treated the perimeter as the sum of the perimeters of both squares."),
                 ((k * a) ** 2 + a, "slip_in_working", "Made a slip in the working."),
                 ((P // 4) ** 2, "treated_as_a_square", "Treated the figure as one square.")]
    return build(two_squares_step, stem, ans, wrong,
                 [f"The perimeter is the same as that of a rectangle {1 + k} units by {k} units: 2 × ({1 + k} + {k}) = {2 * (1 + 2 * k)} units", f"1 unit = {P} ÷ {2 * (1 + 2 * k)} = {a} cm",
                  f"Small square side {a} cm, large square side {k * a} cm"], {"k": k, "P": P, "ask": ask}, U("cm²"), whole=True,
                 auto_slips=False, figure=u.svg("Two squares"))


@checker(two_squares_step)
def _(p):
    k = p["k"]
    a = next(a for a in range(1, 200) if 2 * (a + k * a + k * a) == p["P"])
    return F((a * a + (k * a) ** 2) if p["ask"] == "whole" else (k * a) ** 2)


# ================================================================ triangles

TRIP = [(3, 4, 5), (5, 12, 13), (8, 15, 17), (7, 24, 25), (6, 8, 10)]
LEGS = {12: [(5, 13), (9, 15), (16, 20), (35, 37)], 8: [(6, 10), (15, 17)], 15: [(8, 17), (20, 25), (36, 39)], 24: [(7, 25), (10, 26)]}
TOBJ = ["triangular flag", "triangular sail", "triangular garden bed", "triangular signboard", "triangular tile", "triangular scarf"]


def acute_params(r):
    h = r.choice(list(LEGS))
    (l1, s1), (l2, s2) = r.sample(LEGS[h], 2)
    return l1 + l2, h, l1, s1, s2


def obtuse_params(r):
    h = r.choice(list(LEGS))
    (e, s1), (f, s2) = sorted(r.sample(LEGS[h], 2))
    return f - e, h, f, s1, s2  # base, height, apex offset, BC, AC


@template(T, "basic", AT1)
def base_height_identify(r):
    """math-pat-area-triangle-height-base"""
    letters = r.choice([("A", "B", "C", "D"), ("P", "Q", "R", "S"), ("X", "Y", "Z", "W"), ("K", "L", "M", "N"), ("E", "F", "G", "H")])
    X, Y, Z, D = letters
    obtuse = r.random() < 0.4
    b, h = r.randint(5, 9), r.randint(4, 7)
    off = r.choice([b + 2, b + 3, -2, -3]) if obtuse else r.randint(2, b - 2)
    name = nm(r)
    mode = r.choice(["height", "base"])
    codes = {f"{Z}{D}": 1, f"{Z}{X}": 2, f"{Z}{Y}": 3, f"{X}{Y}": 4, f"{Y}{D}": 5, f"{X}{D}": 6}
    inv = {v: k for k, v in codes.items()}
    ext = f"{Y}{D}" if off > b else f"{X}{D}"
    if mode == "height":
        stem = (f"{name} draws triangle {X}{Y}{Z} as shown and takes {X}{Y} as the base. "
                f"Which line segment is the height of the triangle?")
        correct = codes[f"{Z}{D}"]
        wrong = [(codes[f"{Z}{X}"], "slanted_side_as_height", f"Chose the slanted side {Z}{X}."),
                 (codes[f"{Z}{Y}"], "slanted_side_as_height", f"Chose the slanted side {Z}{Y}."),
                 (codes[ext] if obtuse else codes[f"{X}{Y}"], "base_or_extension_as_height",
                  "Chose a line along the base." if not obtuse else "Chose the extension of the base."),
                 (codes[f"{X}{Y}"], "base_as_height", "Chose the base itself.")]
        steps = [f"The height is the line from {Z} perpendicular to the base {X}{Y} (extended if needed).", f"It is {Z}{D}."]
    else:
        stem = (f"{name} draws triangle {X}{Y}{Z}. The dashed line {Z}{D} is the height. Which side is the base that goes with this height?")
        correct = codes[f"{X}{Y}"]
        wrong = [(codes[f"{Z}{X}"], "slanted_side_as_base", f"Chose the slanted side {Z}{X}."),
                 (codes[f"{Z}{Y}"], "slanted_side_as_base", f"Chose the slanted side {Z}{Y}."),
                 (codes[ext] if obtuse else codes[f"{Y}{D}"], "part_of_base_as_base", "Chose only part of the line along the base."),
                 (codes[f"{Z}{D}"], "height_as_base", "Chose the height itself.")]
        steps = [f"The base is the side that the height {Z}{D} is perpendicular to.", f"It is {X}{Y}."]
    fig = tri_fig(b, h, off, names=(X, Y, Z), foot=D)
    return build(base_height_identify, stem, correct, wrong, steps,
                 {"b": b, "h": h, "off": off, "letters": list(letters), "mode": mode}, lambda v: inv[int(v)], whole=True,
                 auto_slips=False, figure=fig)


@checker(base_height_identify)
def _(p):
    X, Y, Z, D = p["letters"]
    A, B, C = (0, p["h"]), (p["b"], p["h"]), (p["off"], 0)
    pts = {X: A, Y: B, Z: C, D: (p["off"], p["h"])}
    codes = {f"{Z}{D}": 1, f"{Z}{X}": 2, f"{Z}{Y}": 3, f"{X}{Y}": 4, f"{Y}{D}": 5, f"{X}{D}": 6}

    def vec(s):
        return pts[s[1]][0] - pts[s[0]][0], pts[s[1]][1] - pts[s[0]][1]
    base = vec(f"{X}{Y}")
    if p["mode"] == "height":
        hit = [k for k in codes if k[0] == Z and vec(k)[0] * base[0] + vec(k)[1] * base[1] == 0 and vec(k) != (0, 0)]
        return F(codes[hit[0]])
    h = vec(f"{Z}{D}")
    hit = [k for k in codes if vec(k) != (0, 0) and vec(k)[0] * h[0] + vec(k)[1] * h[1] == 0 and k in (f"{X}{Y}",)]
    return F(codes[hit[0]])


@template(T, "basic", AT2)
def triangle_area_labelled(r):
    name, obj = nm(r), r.choice(TOBJ)
    if r.random() < 0.6:
        b, h, off, s1, s2 = acute_params(r)
        sides = {"BC": f"{s2} cm", "CA": f"{s1} cm"}
        slant = s1
    else:
        b, h = r.randint(4, 16), r.randint(3, 14)
        off = r.randint(1, b - 1)
        sides, slant = {}, None
    if (b * h) % 2:
        b += 1
    area = F(b * h, 2)
    stem = f"The figure shows {name}'s {obj}. What is its area?"
    fig = tri_fig(b, h, off, base_lab=f"{b} cm", h_lab=f"{h} cm", names=None, side_labs=sides)
    return build(triangle_area_labelled, stem, area, [
        (b * h, "forgot_the_half", "Multiplied the base by the height and did not halve."),
        (F(b * slant, 2) if slant else None, "used_slanted_side_as_height", "Used the slanted side as the height."),
        (F(b + h, 2), "added_instead_of_multiplied", "Added the base and height before halving."),
        (area + 2, "slip_in_working", "Made a slip in the working."),
        (area - 1, "slip_in_working", "Made a slip in the working."),
    ], [f"Area = 1/2 × base × height", f"= 1/2 × {b} × {h} = {num(area)} cm²"], {"b": b, "h": h}, U("cm²"), whole=True,
        auto_slips=False, figure=fig)


@checker(triangle_area_labelled)
def _(p):
    return shoelace([(0, p["h"]), (p["b"], p["h"]), (0, 0)])


@template(T, "basic", AT2)
def right_triangle_legs(r):
    k = r.randint(1, 3)
    a, b, c = r.choice(TRIP[:4])
    if r.random() < 0.5:
        a, b, c = a * k, b * k, c * k
    else:
        a, b = r.randint(3, 14), r.randint(3, 14)
        c = None
    if (a * b) % 2:
        a += 1
    area = F(a * b, 2)
    name, obj = nm(r), r.choice(TOBJ)
    sides = {"BC": f"{c} cm"} if c else {}
    stem = f"The figure shows {name}'s {obj}, which has a right angle. Find its area."
    fig = tri_fig(a, b, 0, base_lab=f"{a} cm", h_lab=f"{b} cm", names=None, side_labs=sides)
    return build(right_triangle_legs, stem, area, [
        (a * b, "forgot_the_half", "Multiplied the two shorter sides and did not halve."),
        (F(a * c, 2) if c else None, "used_the_longest_side", "Used the longest side as the height."),
        (F(a * c) if c else a + b, "used_the_longest_side", "Used the longest side and forgot to halve."),
        (area + 3, "slip_in_working", "Made a slip in the working."),
        (area - 2, "slip_in_working", "Made a slip in the working."),
    ], [f"The two sides at the right angle are the base and height.", f"Area = 1/2 × {a} × {b} = {num(area)} cm²"],
        {"b": a, "h": b}, U("cm²"), whole=True, auto_slips=False, figure=fig)


@checker(right_triangle_legs)
def _(p):
    return F(p["b"] * p["h"], 2)


@template(T, "basic", AT2)
def base_from_area(r):
    h = r.randint(4, 14)
    b = r.randint(4, 18)
    if (b * h) % 2:
        b += 1
    A = b * h // 2
    name, obj = nm(r), r.choice(TOBJ)
    stem = f"The area of {name}'s {obj} is {A} cm² and its height is {h} cm. What is the length of its base?"
    off = r.randint(1, b - 1)
    fig = tri_fig(b, h, off, base_lab="? cm", h_lab=f"{h} cm", names=None)
    return build(base_from_area, stem, b, [
        (F(A, h) if A % h == 0 else None, "forgot_to_double", "Divided the area by the height without doubling."),
        (A * h // 2 if (A * h) % 2 == 0 else None, "multiplied_instead_of_divided", "Multiplied the area by the height and halved."),
        (A - h, "subtracted_instead_of_divided", "Subtracted the height from the area."),
        (b + 2, "slip_in_working", "Made a slip in the working."),
        (b - 1, "slip_in_working", "Made a slip in the working."),
    ], [f"{A} = 1/2 × base × {h}", f"base = {A} × 2 ÷ {h} = {b} cm"], {"A": A, "h": h}, U("cm"), whole=True, auto_slips=False, figure=fig)


@checker(base_from_area)
def _(p):
    return F(next(b for b in range(1, 500) if F(b * p["h"], 2) == p["A"]))


# ---------------------------------------------------------------- triangles: intermediate

@template(T, "intermediate", AT2, AT1)
def obtuse_area(r):
    name, obj = nm(r), r.choice(TOBJ)
    if r.random() < 0.7:
        b, h, f, bc, ac = obtuse_params(r)
        e = f - b
        sides = {"BC": f"{bc} cm", "CA": f"{ac} cm"}
    else:
        b, h, e = r.randint(4, 12), r.randint(4, 12), r.randint(2, 6)
        f, bc, ac, sides = b + e, None, None, {}
    if (b * h) % 2:
        b += 1
        f += 1
    area = F(b * h, 2)
    off = b + e
    stem = f"The figure shows {name}'s {obj}. The height drawn is perpendicular to the extended base. Find the area of the triangle."
    fig = tri_fig(b, h, off, base_lab=f"{b} cm", h_lab=f"{h} cm", names=None, side_labs=sides)
    return build(obtuse_area, stem, area, [
        (F(b * ac, 2) if ac else b * h, "used_slanted_side_as_height", "Used a slanted side as the height."),
        (F((b + e) * h, 2), "used_the_extended_base", "Used the whole extended base instead of the base of the triangle."),
        (b * h, "forgot_the_half", "Did not halve."),
        (F(e * h, 2), "used_the_extension_as_base", "Used the dotted extension as the base."),
        (area + 2, "slip_in_working", "Made a slip in the working."),
    ], [f"The base is {b} cm and the height is {h} cm (the dotted part is not part of the triangle).", f"Area = 1/2 × {b} × {h} = {num(area)} cm²"],
        {"b": b, "h": h, "e": e}, U("cm²"), whole=True, auto_slips=False, figure=fig)


@checker(obtuse_area)
def _(p):
    return shoelace([(0, p["h"]), (p["b"], p["h"]), (p["b"] + p["e"], 0)])


@template(T, "intermediate", AT2)
def triangle_rect_same_area(r):
    b, h = r.choice([4, 6, 8, 10, 12, 14, 16]), r.choice([4, 6, 9, 10, 12, 15])
    A = b * h // 2
    wd = r.choice([x for x in range(2, 13) if A % x == 0 and x != h and x != b])
    Lg = A // wd
    name, obj = nm(r), r.choice(["flag", "sail", "cloth"])
    stem = (f"{name} cuts a triangular {obj} with a base of {b} cm and a height of {h} cm. {name} then cuts a rectangular piece with the same area "
            f"and a width of {wd} cm. What is the length of the rectangle?")
    return build(triangle_rect_same_area, stem, Lg, [
        (b * h // wd if (b * h) % wd == 0 else None, "forgot_the_half", "Forgot to halve when finding the triangle's area."),
        (b * h // 2 - wd, "subtracted_instead_of_divided", "Subtracted the width from the area."),
        (A * wd, "multiplied_instead_of_divided", "Multiplied the area by the width."),
        (Lg + 2, "slip_in_working", "Made a slip in the working."),
        (Lg - 1, "slip_in_working", "Made a slip in the working."),
    ], [f"Triangle area = 1/2 × {b} × {h} = {A} cm²", f"Length = {A} ÷ {wd} = {Lg} cm"], {"b": b, "h": h, "w": wd}, U("cm"),
        whole=True, auto_slips=False)


@checker(triangle_rect_same_area)
def _(p):
    A = shoelace([(0, 0), (p["b"], 0), (0, p["h"])])
    return F(next(x for x in range(1, 800) if x * p["w"] == A))


@template(T, "intermediate", AT3)
def composite_house(r):
    """math-pat-area-triangle-rectangle-composite"""
    w = r.choice([8, 10, 12, 14, 16, 18])
    hh = r.randint(5, 12)
    t = r.randint(3, 9)
    p_ = r.randint(2, w - 2)
    u = UF(0, 0, w, t + hh, mx=48, my=26)
    verts = [(0, t), (p_, 0), (w, t), (w, t + hh), (0, t + hh)]
    u.poly(verts)
    u.seg((0, t), (w, t), dash=True, width=1.2)
    u.seg((p_, 0), (p_, t), dash=True, width=1.2)
    u.right_mark((p_, t), (1 if p_ < w / 2 else -1, 0), (0, -1))
    u.edge_label(verts, 3, f"{w} cm")
    u.edge_label(verts, 4, f"{hh} cm")
    u.text((p_, t * 0.7), f"{t} cm", dx=(8 + 20) * (1 if p_ < w / 2 else -1))
    area = w * hh + F(w * t, 2)
    name = nm(r)
    stem = f"The figure shows the side of {name}'s tent. Find its area."
    if (w * t) % 2:
        return None
    return build(composite_house, stem, area, [
        (w * (hh + t), "treated_as_a_rectangle", "Treated the whole figure as one rectangle."),
        (w * hh + w * t, "forgot_the_half", "Did not halve the triangle."),
        (F(w * t, 2), "found_triangle_only", "Found the area of the triangle only."),
        (w * hh, "found_rectangle_only", "Found the area of the rectangle only."),
        (area + 4, "slip_in_working", "Made a slip in the working."),
    ], [f"Rectangle = {w} × {hh} = {w * hh} cm²", f"Triangle = 1/2 × {w} × {t} = {num(F(w * t, 2))} cm²", f"Total = {num(area)} cm²"],
        {"w": w, "h": hh, "t": t, "p": p_}, U("cm²"), whole=True, auto_slips=False, figure=u.svg("Tent"))


@checker(composite_house)
def _(p):
    return shoelace([(0, p["t"]), (p["p"], 0), (p["w"], p["t"]), (p["w"], p["t"] + p["h"]), (0, p["t"] + p["h"])])


@template(T, "intermediate", AT3)
def rect_minus_triangle(r):
    """math-pat-area-triangle-rectangle-composite"""
    Wd = r.choice([10, 12, 14, 16, 18, 20])
    H = r.choice([6, 8, 10, 12])
    full = r.random() < 0.3
    b = Wd if full else r.choice([x for x in range(4, Wd - 1, 2)])
    x0 = 0 if full else r.randint(0, Wd - b)
    ap = r.randint(0, Wd)
    u = UF(0, 0, Wd, H, mx=48, my=34)
    v = [(0, 0), (Wd, 0), (Wd, H), (0, H)]
    u.poly(v)
    u.poly([(x0, H), (x0 + b, H), (ap, 0)], shade=0.25)
    u.edge_label(v, 2, f"{Wd} cm")
    u.edge_label(v, 1, f"{H} cm")
    if not full:
        u.text((x0 + b / 2, H), f"{b} cm", dy=-9, size=12)
    shaded = F(b * H, 2)
    ans = Wd * H - shaded
    name = nm(r)
    stem = f"The figure shows a rectangle with a shaded triangle inside it. Find the area of the unshaded part. ({name} drew it.)"
    return build(rect_minus_triangle, stem, ans, [
        (shaded, "gave_shaded_area", "Gave the area of the shaded triangle."),
        (Wd * H - b * H if Wd * H > b * H else None, "forgot_the_half", "Forgot to halve the triangle."),
        (F(Wd * H, 2), "used_half_of_the_rectangle", "Took half of the rectangle as the unshaded part."),
        (ans + 4, "slip_in_working", "Made a slip in the working."),
        (Wd * H, "gave_rectangle_area", "Gave the area of the whole rectangle."),
    ], [f"Rectangle = {Wd} × {H} = {Wd * H} cm²", f"Shaded triangle = 1/2 × {b} × {H} = {num(shaded)} cm²", f"Unshaded = {Wd * H} - {num(shaded)} = {num(ans)} cm²"],
        {"W": Wd, "H": H, "b": b, "x0": x0, "ap": ap}, U("cm²"), whole=True, auto_slips=False, figure=u.svg("Rectangle with triangle"))


@checker(rect_minus_triangle)
def _(p):
    return F(p["W"] * p["H"]) - shoelace([(p["x0"], p["H"]), (p["x0"] + p["b"], p["H"]), (p["ap"], 0)])


# ---------------------------------------------------------------- triangles: competent

@template(T, "competent", AT3)
def corner_two_points(r):
    """math-pat-area-triangle-rectangle-composite"""
    Wd, H = r.choice([12, 16, 20, 24]), r.choice([10, 12, 16, 18])
    p_ = r.choice([x for x in range(2, Wd - 1, 2)])
    q = r.choice([x for x in range(2, H - 1, 2)])
    u = UF(0, 0, Wd, H, mx=48, my=34)
    v = [(0, 0), (Wd, 0), (Wd, H), (0, H)]
    u.poly(v)
    A, P, Q = (0, H), (p_, 0), (Wd, q)
    u.poly([A, P, Q], shade=0.25)
    u.edge_label(v, 2, f"{Wd} cm")
    u.edge_label(v, 3, f"{H} cm")
    u.seg_label((0, 0), (p_, 0), f"{p_} cm", (Wd / 2, H / 2), size=12)
    u.seg_label((Wd, 0), (Wd, q), f"{q} cm", (0, H / 2), size=12)
    u.letter(v, 0, "D")
    u.letter(v, 1, "C")
    u.letter(v, 2, "B")
    u.letter(v, 3, "A")
    u.text(P, "P", dy=-11, bold=True)
    u.text(Q, "Q", dx=11, bold=True)
    t1, t2, t3 = F(H * p_, 2), F((Wd - p_) * q, 2), F(Wd * (H - q), 2)
    ans = Wd * H - t1 - t2 - t3
    name = nm(r)
    stem = (f"ABCD is a rectangle. P is on DC and Q is on BC. Find the area of the shaded triangle APQ. ({name} marks the lengths shown.)")
    return build(corner_two_points, stem, ans, [
        (t1 + t2 + t3, "gave_unshaded_area", "Gave the total area of the three unshaded triangles."),
        (Wd * H - t1 - t2, "left_out_a_triangle", "Took away only two of the unshaded triangles."),
        (F(Wd * H, 2), "assumed_half_of_the_rectangle", "Assumed the shaded triangle is half the rectangle."),
        (Wd * H - 2 * (t1 + t2 + t3) if Wd * H > 2 * (t1 + t2 + t3) else None, "doubled_the_unshaded", "Took away the unshaded triangles twice."),
        (ans + 4, "slip_in_working", "Made a slip in the working."),
    ], [f"Triangle ADP = 1/2 × {H} × {p_} = {num(t1)} cm²", f"Triangle PCQ = 1/2 × {Wd - p_} × {q} = {num(t2)} cm²", f"Triangle ABQ = 1/2 × {Wd} × {H - q} = {num(t3)} cm²",
        f"Shaded = {Wd * H} - {num(t1)} - {num(t2)} - {num(t3)} = {num(ans)} cm²"], {"W": Wd, "H": H, "p": p_, "q": q}, U("cm²"),
        whole=True, auto_slips=False, figure=u.svg("Rectangle ABCD"))


@checker(corner_two_points)
def _(p):
    return shoelace([(0, p["H"]), (p["p"], 0), (p["W"], p["q"])])


@template(T, "competent", AT3)
def three_sides_points(r):
    """math-pat-area-triangle-rectangle-composite"""
    Wd, H = r.choice([12, 16, 20, 24]), r.choice([12, 16, 20])
    p_ = r.choice(range(2, Wd - 1, 2))
    q = r.choice(range(2, H - 3, 2))
    l = r.choice(range(2, H - 3, 2))
    u = UF(0, 0, Wd, H, mx=48, my=34)
    v = [(0, 0), (Wd, 0), (Wd, H), (0, H)]
    u.poly(v)
    P, Q, R = (p_, 0), (Wd, q), (0, l)
    u.poly([P, Q, R], shade=0.25)
    u.edge_label(v, 2, f"{Wd} cm")
    u.seg_label((0, 0), (p_, 0), f"{p_} cm", (Wd / 2, H / 2), size=12)
    u.seg_label((Wd, 0), (Wd, q), f"{q} cm", (0, H / 2), size=12)
    u.seg_label((0, 0), (0, l), f"{l} cm", (Wd / 2, H / 2), size=12)
    u.seg_label((0, l), (0, H), f"{H - l} cm", (Wd / 2, H / 2), size=12)
    u.text(P, "P", dy=-11, bold=True)
    u.text(Q, "Q", dx=13, dy=10, bold=True)
    u.text(R, "R", dx=-11, bold=True)
    t1, t2 = F(p_ * l, 2), F((Wd - p_) * q, 2)
    t3 = F(((H - l) + (H - q)) * Wd, 2)
    ans = Wd * H - t1 - t2 - t3
    stem = "The figure shows a rectangle with three points P, Q and R on its sides. Find the area of the shaded triangle PQR."
    if ans.denominator != 1:
        return None
    return build(three_sides_points, stem, ans, [
        (t1 + t2 + t3, "gave_unshaded_area", "Gave the area of the unshaded parts."),
        (Wd * H - t1 - t2, "left_out_the_bottom_part", "Forgot to take away the bottom trapezium."),
        (F(Wd * H, 2), "assumed_half_of_the_rectangle", "Assumed the shaded triangle is half the rectangle."),
        (ans + 6, "slip_in_working", "Made a slip in the working."),
        (ans - 4, "slip_in_working", "Made a slip in the working."),
    ], [f"Top-left triangle = 1/2 × {p_} × {l} = {num(t1)} cm²", f"Top-right triangle = 1/2 × {Wd - p_} × {q} = {num(t2)} cm²",
        f"Bottom part = 1/2 × ({H - l} + {H - q}) × {Wd} = {num(t3)} cm²", f"Shaded = {Wd * H} - {num(t1 + t2 + t3)} = {num(ans)} cm²"],
        {"W": Wd, "H": H, "p": p_, "q": q, "l": l}, U("cm²"), whole=True, auto_slips=False, figure=u.svg("Rectangle with points"))


@checker(three_sides_points)
def _(p):
    return shoelace([(p["p"], 0), (p["W"], p["q"]), (0, p["l"])])


@template(T, "competent", AT3, AT2)
def point_inside(r):
    """math-pat-area-triangle-rectangle-composite"""
    Wd, H = r.choice([12, 14, 16, 18, 20]), r.choice([8, 10, 12, 14])
    hb = r.randint(2, H - 2)
    px = r.randint(2, Wd - 2)
    if (Wd * hb) % 2:
        return None
    pab = F(Wd * hb, 2)
    pcd = F(Wd * (H - hb), 2)
    u = UF(0, 0, Wd, H, mx=48, my=34)
    v = [(0, 0), (Wd, 0), (Wd, H), (0, H)]
    P = (px, H - hb)
    u.poly(v)
    u.poly([P, (Wd, 0), (0, 0)], shade=0.25)
    for c in v:
        u.seg(P, c, width=1.2)
    u.edge_label(v, 2, f"{Wd} cm")
    u.edge_label(v, 1, f"{H} cm")
    u.letter(v, 0, "D")
    u.letter(v, 1, "C")
    u.letter(v, 2, "B")
    u.letter(v, 3, "A")
    u.text(P, "P", dy=-11, bold=True)
    cx, cy = (0 + Wd + px) / 3, (H + H + H - hb) / 3
    u.text((cx, cy), f"{num(pab)} cm²", size=12)
    ans = F(Wd * H, 2) - pab
    stem = (f"ABCD is a rectangle and P is a point inside it. The area of triangle PAB is {num(pab)} cm². "
            f"What is the area of the shaded triangle PCD?")
    return build(point_inside, stem, ans, [
        (pab, "assumed_equal_areas", "Assumed the two triangles have the same area."),
        (Wd * H - pab, "took_pab_from_the_rectangle", "Took the area of PAB from the whole rectangle."),
        (F(Wd * H, 2) + pab, "added_instead_of_subtracted", "Added the area of PAB to half the rectangle."),
        (F(Wd * H, 4), "used_a_quarter", "Used a quarter of the rectangle."),
        (ans + 3, "slip_in_working", "Made a slip in the working."),
    ], [f"Triangles PAB and PCD together make half of the rectangle: 1/2 × {Wd} × {H} = {Wd * H // 2} cm²", f"PCD = {Wd * H // 2} - {num(pab)} = {num(ans)} cm²"],
        {"W": Wd, "H": H, "hb": hb, "px": px}, U("cm²"), whole=True, auto_slips=False, figure=u.svg("Rectangle ABCD with point P"))


@checker(point_inside)
def _(p):
    return shoelace([(p["px"], p["H"] - p["hb"]), (p["W"], 0), (0, 0)])


@template(T, "competent", AT2, AT3)
def altitude_hypotenuse(r):
    k = r.randint(1, 3)
    a, b, c = r.choice([(3, 4, 5), (3, 4, 5), (7, 24, 25)])
    k = r.randint(1, 4) if c == 5 else r.randint(1, 2)
    a, b, c = a * k, b * k, c * k
    if r.random() < 0.5:
        a, b = b, a
    # right angle at Q (bottom-left), P top-left, R bottom-right: PQ = b, QR = a, PR = c
    P, Q, R = (0, 0), (0, b), (a, b)
    d = F(a * b, c)
    t = ((Q[0] - P[0]) * (R[0] - P[0]) + (Q[1] - P[1]) * (R[1] - P[1])) / (c * c)
    D = (P[0] + t * (R[0] - P[0]), P[1] + t * (R[1] - P[1]))
    u = UF(0, 0, a, b, mx=52, my=36)
    v = [P, R, Q]
    u.poly(v)
    u.seg(Q, D, dash=True, width=1.3)
    u.right_mark(Q, (1, 0), (0, -1))
    ux, uy = (R[0] - P[0]) / c, (R[1] - P[1]) / c
    u.right_mark(D, (ux, uy), (Q[0] - D[0], Q[1] - D[1]))
    u.edge_label([P, Q, R], 1, f"{a} cm")
    u.edge_label([P, Q, R], 2, f"{c} cm", extra=0)
    u.edge_label([P, Q, R], 0, f"{b} cm")
    u.letter([P, Q, R], 0, "P")
    u.letter([P, Q, R], 1, "Q")
    u.letter([P, Q, R], 2, "R")
    u.text(D, "D", dx=10, dy=-4, bold=True)
    name = nm(r)
    stem = (f"In triangle PQR, angle PQR is a right angle, PQ = {b} cm, QR = {a} cm and PR = {c} cm. QD is perpendicular to PR. "
            f"Find the length of QD. ({name} may give the answer as a decimal.)")
    fmt = lambda v: f"{num(v)} cm"
    return build(altitude_hypotenuse, stem, d, [
        (F(a * b, 2), "gave_the_area", "Gave the area of the triangle."),
        (F(a * b, 2 * c), "forgot_to_double", "Divided the area by PR without doubling."),
        (F(a + b - c), "added_sides_wrongly", "Used the sum of the shorter sides minus the longest."),
        (F(2 * a * b, c) + 1 if False else F(a * c, b), "used_the_wrong_ratio", "Divided the wrong pair of sides."),
        (d + 1, "slip_in_working", "Made a slip in the working."),
        (d - F(1, 2), "slip_in_working", "Made a slip in the working."),
    ], [f"Area of triangle PQR = 1/2 × {a} × {b} = {a * b // 2} cm²", f"Area = 1/2 × PR × QD, so {a * b // 2} = 1/2 × {c} × QD", f"QD = {a * b} ÷ {c} = {num(d)} cm"],
        {"a": a, "b": b, "c": c}, fmt, auto_slips=False, figure=u.svg("Right triangle PQR"))


@checker(altitude_hypotenuse)
def _(p):
    a, b = p["a"], p["b"]
    c = next(x for x in range(1, 200) if x * x == a * a + b * b)
    # distance from Q to line PR by the point-line formula
    return F(abs(a * b), c)


@template(T, "competent", AT2)
def triangle_base_reduced(r):
    b = r.choice([10, 12, 15, 16, 18, 20, 24])
    h = r.randint(4, 12)
    cut = r.choice([x for x in range(2, b - 3) if x % 2 == 0])
    A = F(b * h, 2)
    new = F((b - cut) * h, 2)
    name, obj = nm(r), r.choice(["flag", "sail", "signboard"])
    stem = (f"The area of a triangular {obj} is {num(A)} cm² and its base is {b} cm. {name} cuts the {obj} so that its base is {cut} cm shorter "
            f"but its height stays the same. What is the area of the new {obj}?")
    return build(triangle_base_reduced, stem, new, [
        (A - cut, "subtracted_from_the_area", "Subtracted the base reduction from the area."),
        (A - cut * h, "forgot_the_half", "Took away the reduction times the height without halving."),
        (F(new * 2), "forgot_the_half", "Forgot to halve the new area."),
        (new + h, "slip_in_working", "Made a slip in the working."),
        (new - 2, "slip_in_working", "Made a slip in the working."),
    ], [f"Height = {num(A)} × 2 ÷ {b} = {h} cm", f"New base = {b} - {cut} = {b - cut} cm", f"New area = 1/2 × {b - cut} × {h} = {num(new)} cm²"],
        {"A2": b * h, "b": b, "cut": cut}, U("cm²"), whole=True, auto_slips=False)


@checker(triangle_base_reduced)
def _(p):
    h = next(h for h in range(1, 500) if p["b"] * h == p["A2"])
    return F((p["b"] - p["cut"]) * h, 2)


# ================================================================ volume of cube and cuboid

def box(L_, W_, H_, water=None, dl=None, hl="", lw=True):
    return tank_svg(L_, W_, H_, water=water, labs=(f"{L_} cm" if lw else "", f"{W_} cm" if lw else "", hl or f"{H_} cm"),
                    depth_lab=dl)


@template(T, "basic", VC1, VC2)
def count_cubes(r):
    """math-pat-volume-count-unit-cubes"""
    l, w, h = r.randint(2, 5), r.randint(2, 4), r.randint(2, 4)
    name = nm(r)
    thing = r.choice(["building blocks", "sugar cubes", "wooden cubes", "toy bricks"])
    n = l * w * h
    stem = f"{name} stacks identical {thing}, each 1 cm by 1 cm by 1 cm, to make the solid shown. How many {thing.split()[-1]} are used?"
    return build(count_cubes, stem, n, [
        (l * h + l * w + w * h, "counted_visible_faces", "Counted the squares on the three faces you can see."),
        (l + w + h, "added_the_dimensions", "Added the numbers of cubes along the three edges."),
        (n + l, "miscounted_cubes", "Counted one layer row too many."),
        (n - w, "miscounted_cubes", "Missed a row of cubes."),
        (l * w * (h - 1), "missed_a_layer", "Missed a layer."),
    ], [f"One layer has {l} × {w} = {l * w} cubes.", f"There are {h} layers: {l * w} × {h} = {n}"], {"l": l, "w": w, "h": h},
        lambda v: f"{num(v)}", whole=True, auto_slips=False, figure=cubes_svg(l, w, h))


@checker(count_cubes)
def _(p):
    return F(sum(1 for _x in range(p["l"]) for _y in range(p["w"]) for _z in range(p["h"])))


@template(T, "basic", VC1, VC4)
def cubes_to_fill(r):
    """math-pat-volume-count-unit-cubes"""
    l, w, h = r.randint(3, 6), r.randint(2, 5), r.randint(2, 4)
    tot = l * w * h
    have = r.randint(l * w // 2 + 1, tot - 3)
    name = nm(r)
    stem = (f"{name} has a box that is {l} cm long, {w} cm wide and {h} cm high. {name} has already put {have} cubes, each 1 cm by 1 cm by 1 cm, into it. "
            f"How many more of these cubes are needed to fill the box completely?")
    ans = tot - have
    return build(cubes_to_fill, stem, ans, [
        (tot, "gave_the_volume_of_the_box", "Gave the number of cubes that fill the whole box."),
        (tot + have, "added_instead_of_subtracted", "Added the cubes already in the box."),
        (have, "gave_the_cubes_already_in", "Gave the cubes already in the box."),
        (ans + 2, "slip_in_subtraction", "Made a slip in the subtraction."),
        (ans - 3, "slip_in_subtraction", "Made a slip in the subtraction.")],
        [f"Cubes to fill the box = {l} × {w} × {h} = {tot}", f"More cubes = {tot} - {have} = {ans}"], {"l": l, "w": w, "h": h, "have": have},
        lambda v: f"{num(v)}", whole=True, auto_slips=False, figure=box(l, w, h))


@checker(cubes_to_fill)
def _(p):
    return F(sum(1 for _x in range(p["l"]) for _y in range(p["w"]) for _z in range(p["h"])) - p["have"])


@template(T, "basic", VC4, VC2)
def cuboid_volume(r):
    """math-pat-volume-cube-cuboid-direct"""
    big = r.random() < 0.3
    l, w, h = r.randint(3, 12), r.randint(2, 9), r.randint(2, 9)
    if big:
        l, w, h = r.randint(2, 6), r.randint(2, 5), r.randint(2, 5)
    u = "m" if big else "cm"
    name = nm(r)
    obj = r.choice(["storage box", "fish tank", "wooden block", "water tank", "crate"]) if not big else r.choice(["storeroom", "container", "water tank"])
    stem = f"The figure shows {name}'s {obj}, a cuboid. What is its volume?"
    fig = tank_svg(l, w, h, labs=(f"{l} {u}", f"{w} {u}", f"{h} {u}"))
    v = l * w * h
    return build(cuboid_volume, stem, v, [
        (l * w, "found_base_area_only", "Found the area of the base only."),
        (l + w + h, "added_the_dimensions", "Added the three measurements."),
        (2 * (l * w + l * h + w * h), "found_surface_area", "Found the total area of all the faces."),
        (v + l, "slip_in_multiplication", "Made a slip in the multiplication."),
        (v - w, "slip_in_multiplication", "Made a slip in the multiplication."),
    ], [f"Volume = {l} × {w} × {h} = {v} {u}³"], {"l": l, "w": w, "h": h}, U(u + "³"), whole=True, auto_slips=False, figure=fig)


@checker(cuboid_volume)
def _(p):
    return F(sum(p["l"] * p["w"] for _ in range(p["h"])))


@template(T, "basic", VC4)
def cube_volume(r):
    """math-pat-volume-cube-cuboid-direct"""
    a = r.randint(2, 12)
    name = nm(r)
    stem = f"The figure shows {name}'s cube-shaped box. What is its volume?"
    fig = tank_svg(a, a, a, labs=(f"{a} cm", "", ""))
    return build(cube_volume, stem, a ** 3, [
        (3 * a, "added_instead_of_multiplied", "Added the edge three times."),
        (a * a, "found_face_area", "Found the area of one face."),
        (6 * a * a, "found_surface_area", "Found the total area of the faces."),
        (a ** 3 + a, "slip_in_multiplication", "Made a slip in the multiplication."),
        (a ** 3 - a, "slip_in_multiplication", "Made a slip in the multiplication."),
    ], [f"Volume = {a} × {a} × {a} = {a ** 3} cm³"], {"a": a}, U("cm³"), whole=True, auto_slips=False, figure=fig)


@checker(cube_volume)
def _(p):
    return F(p["a"] ** 3)


@template(T, "basic", VC6)
def litre_cm3(r):
    name = nm(r)
    mode = r.choice(["l_to_cm3", "cm3_to_l", "ml_to_cm3", "cm3_to_ml"])
    if mode == "l_to_cm3":
        x = r.choice([2, 3, 4, 5, 6, 8, 9, 12, 15, 20])
        stem = f"{name}'s fish tank holds {x} l of water. What is its capacity in cm³?"
        return build(litre_cm3, stem, x * 1000, [
            (x * 100, "used_100_not_1000", "Used 1 l = 100 cm³."),
            (x * 10000, "used_10000", "Used 1 l = 10 000 cm³."),
            (x, "did_not_convert", "Did not convert."),
            (x * 1000 + 100, "slip_in_working", "Made a slip in the working.")], [f"1 l = 1000 cm³", f"{x} l = {x * 1000} cm³"],
            {"mode": mode, "x": x}, U("cm³"), whole=True, auto_slips=False)
    if mode == "cm3_to_l":
        x = r.choice([2500, 3500, 4500, 6000, 7500, 12000, 18000, 2000, 9000, 3200])
        stem = f"A container has a volume of {x} cm³. What is its capacity in litres?"
        a = F(x, 1000)
        return build(litre_cm3, stem, a, [
            (F(x, 100), "used_100_not_1000", "Divided by 100."),
            (F(x, 10000), "used_10000", "Divided by 10 000."),
            (F(x), "did_not_convert", "Did not convert."),
            (a * 10, "decimal_place_error", "Put the decimal point in the wrong place.")], [f"{x} ÷ 1000 = {num(a)} l"],
            {"mode": mode, "x": x}, U("l"), auto_slips=False)
    if mode == "ml_to_cm3":
        x = r.choice([150, 250, 350, 450, 600, 750, 1200, 2400, 3600])
        stem = f"A bottle holds {x} ml of juice. What is the volume of the juice in cm³?"
        return build(litre_cm3, stem, x, [
            (x * 1000, "used_1000", "Multiplied by 1000."),
            (F(x, 1000), "used_1000", "Divided by 1000."),
            (x * 10, "used_10", "Multiplied by 10."),
            (x + 100, "slip_in_working", "Made a slip in the working."),
            (x - 50, "slip_in_working", "Made a slip in the working.")], ["1 ml = 1 cm³"],
            {"mode": mode, "x": x}, U("cm³"), auto_slips=False)
    x = r.choice([4, 6, 8, 12, 15, 20, 24, 30])
    stem = f"The volume of a cuboid is {x} cm³. How many millilitres of water can it hold when it is full?"
    return build(litre_cm3, stem, x, [
        (x * 1000, "used_1000", "Multiplied by 1000."),
        (F(x, 1000), "used_1000", "Divided by 1000."),
        (x * 10, "used_10", "Multiplied by 10."),
        (x + 2, "slip_in_working", "Made a slip in the working."),
        (x - 1, "slip_in_working", "Made a slip in the working.")], ["1 cm³ = 1 ml"],
        {"mode": mode, "x": x}, U("ml"), auto_slips=False)


@checker(litre_cm3)
def _(p):
    x, m = F(p["x"]), p["mode"]
    return {"l_to_cm3": x * 1000, "cm3_to_l": x / 1000, "ml_to_cm3": x, "cm3_to_ml": x}[m]


def dims_1000(r):
    for _ in range(200):
        l, w, h = r.choice([10, 20, 25, 40, 50, 5, 8, 15, 30]), r.choice([10, 20, 25, 40, 50, 5, 8, 12, 30]), r.choice([10, 20, 25, 5, 8, 12, 15, 30, 40])
        if (l * w * h) % 1000 == 0 and l * w * h <= 60000 and l != w:
            return l, w, h
    return 20, 25, 10


@template(T, "basic", VC6, VC4)
def cuboid_capacity_litres(r):
    l, w, h = dims_1000(r)
    name = nm(r)
    v = l * w * h
    stem = f"{name}'s rectangular container is {l} cm long, {w} cm wide and {h} cm high. What is its capacity in litres?"
    return build(cuboid_capacity_litres, stem, v // 1000, [
        (v, "did_not_change_to_litres", "Gave the volume in cm³."),
        (F(v, 100), "used_100_not_1000", "Divided by 100."),
        (v // 10000 if v % 10000 == 0 else None, "used_10000", "Divided by 10 000."),
        (l + w + h, "added_the_dimensions", "Added the three measurements."),
        (v // 1000 + 2, "slip_in_working", "Made a slip in the working.")], [f"Volume = {l} × {w} × {h} = {v} cm³", f"{v} ÷ 1000 = {v // 1000} l"],
        {"l": l, "w": w, "h": h}, U("l"), whole=True, auto_slips=False, figure=box(l, w, h))


@checker(cuboid_capacity_litres)
def _(p):
    return F(p["l"] * p["w"] * p["h"], 1000)


def water_dims(r):
    for _ in range(500):
        l, w = r.choice([20, 25, 30, 40, 50, 60]), r.choice([20, 25, 30, 40, 50])
        d = r.choice([8, 10, 12, 15, 16, 18, 20, 24, 25, 30])
        h = d + r.choice([6, 8, 10, 12, 15, 20])
        if l != w and (l * w * d) % 1000 == 0 and 0.35 < d / h < 0.85:
            return l, w, h, d
    return 40, 25, 30, 20


@template(T, "intermediate", VC5, VC6)
def tank_water_volume(r):
    """math-pat-volume-cuboid-water-level"""
    l, w, h, d = water_dims(r)
    name = nm(r)
    stem = (f"The figure shows {name}'s rectangular tank, {l} cm long, {w} cm wide and {h} cm high. "
            f"The water in the tank is {d} cm deep. How much water is in the tank, in litres?")
    v = l * w * d // 1000
    return build(tank_water_volume, stem, v, [
        (l * w * h // 1000 if (l * w * h) % 1000 == 0 else F(l * w * h, 1000), "used_the_full_height", "Used the height of the tank instead of the depth of the water."),
        (l * w * d, "did_not_change_to_litres", "Gave the volume in cm³."),
        (F(l * w * d, 100), "used_100_not_1000", "Divided by 100."),
        (v + 2, "slip_in_working", "Made a slip in the working."),
        (v - 1, "slip_in_working", "Made a slip in the working."),
    ], [f"Volume of water = {l} × {w} × {d} = {l * w * d} cm³", f"{l * w * d} ÷ 1000 = {v} l"], {"l": l, "w": w, "h": h, "d": d},
        U("l"), auto_slips=False, figure=box(l, w, h, water=d, dl=f"{d} cm"))


@checker(tank_water_volume)
def _(p):
    return F(p["l"] * p["w"] * p["d"], 1000)


@template(T, "intermediate", VC7, VC9)
def find_dimension(r):
    """math-pat-volume-cube-cuboid-direct"""
    l, w, h = r.randint(4, 15), r.randint(3, 12), r.randint(3, 12)
    V = l * w * h
    name = nm(r)
    stem = f"{name}'s cuboid has a volume of {V} cm³. Its length is {l} cm and its width is {w} cm. What is its height?"
    return build(find_dimension, stem, h, [
        (V // l, "forgot_to_divide_by_width", "Divided the volume by the length only."),
        (V // (l + w) if V % (l + w) == 0 else V // (l + w) + 1, "divided_by_the_sum", "Divided the volume by the sum of the length and width."),
        (V - l * w, "subtracted_instead_of_divided", "Subtracted the base area from the volume."),
        (h + 1, "slip_in_division", "Made a slip in the division."),
        (h - 1, "slip_in_division", "Made a slip in the division.")], [f"Base area = {l} × {w} = {l * w} cm²", f"Height = {V} ÷ {l * w} = {h} cm"],
        {"V": V, "l": l, "w": w}, U("cm"), whole=True, auto_slips=False, figure=tank_svg(l, w, h, labs=(f"{l} cm", f"{w} cm", "? cm")))


@checker(find_dimension)
def _(p):
    return F(next(h for h in range(1, 2000) if p["l"] * p["w"] * h == p["V"]))


CUBES = [27, 64, 125, 216, 343, 512, 729, 1000, 1331, 1728]


@template(T, "intermediate", VC8)
def cube_edge(r):
    a = r.choice([3, 4, 5, 6, 7, 8, 9, 10, 11, 12])
    V = a ** 3
    name = nm(r)
    stem = f"{name}'s cube-shaped box has a volume of {V} cm³. What is the length of one edge of the box?"
    return build(cube_edge, stem, a, [
        (3 * a, "found_three_times_the_edge", "Gave the sum of three edges."),
        (a * a, "found_face_area", "Gave the area of one face."),
        (V // 6 if V % 6 == 0 else V // 6 + 1, "divided_by_six", "Divided the volume by 6."),
        (V // 3 if V % 3 == 0 else V // 3 + 1, "divided_by_three", "Divided the volume by 3."),
        (a + 1, "slip_in_working", "Made a slip in the working.")],
        [f"{a} × {a} × {a} = {V}", f"The edge is {a} cm."], {"V": V}, U("cm"), whole=True, auto_slips=False)


@checker(cube_edge)
def _(p):
    return F(next(a for a in range(1, 100) if a * a * a == p["V"]))


@template(T, "intermediate", VC9, VC5)
def depth_from_base_area(r):
    ba = r.choice([200, 250, 300, 400, 500, 600, 800, 1000, 1200])
    d = r.choice([4, 5, 6, 8, 10, 12, 15, 20])
    V = ba * d
    name = nm(r)
    if V % 1000:
        return None
    lit = V // 1000
    stem = f"The base of {name}'s rectangular tank has an area of {ba} cm². The tank contains {lit} l of water. How deep is the water, in cm?"
    return build(depth_from_base_area, stem, d, [
        (F(lit, ba), "did_not_change_litres_to_cm3", "Divided litres by the base area without changing units."),
        (V // ba * 10, "decimal_place_error", "Made an error with the zeros."),
        (lit * 100 // ba if (lit * 100) % ba == 0 else None, "used_100_not_1000", "Used 1 l = 100 cm³."),
        (d + 2, "slip_in_division", "Made a slip in the division."),
        (d - 1, "slip_in_division", "Made a slip in the division.")],
        [f"{lit} l = {V} cm³", f"Depth = {V} ÷ {ba} = {d} cm"], {"ba": ba, "lit": lit}, U("cm"), auto_slips=False,
        figure=tank_svg(40, 25, 30, water=r.choice([12, 15, 18, 20]), labs=("", "", ""), depth_lab="? cm"))


@checker(depth_from_base_area)
def _(p):
    return F(next(d for d in range(1, 5000) if p["ba"] * d == p["lit"] * 1000))


@template(T, "intermediate", VC10)
def face_area_from_volume(r):
    base = r.choice([20, 24, 30, 36, 40, 48, 54, 60])
    h = r.randint(3, 12)
    V = base * h
    name = nm(r)
    stem = f"{name}'s cuboid has a volume of {V} cm³ and a height of {h} cm. What is the area of its base?"
    return build(face_area_from_volume, stem, base, [
        (V * h, "multiplied_instead_of_divided", "Multiplied the volume by the height."),
        (V - h, "subtracted_instead_of_divided", "Subtracted the height from the volume."),
        (V // (2 * h) if V % (2 * h) == 0 else None, "divided_by_twice_the_height", "Divided by twice the height."),
        (base + h, "slip_in_division", "Made a slip in the division."),
        (base - 2, "slip_in_division", "Made a slip in the division.")],
        [f"Volume = base area × height", f"Base area = {V} ÷ {h} = {base} cm²"], {"V": V, "h": h}, U("cm²"), whole=True, auto_slips=False,
        figure=tank_svg(30, 20, 22 if h > 6 else 15, labs=("", "", f"{h} cm")))


@checker(face_area_from_volume)
def _(p):
    return F(next(b for b in range(1, 3000) if b * p["h"] == p["V"]))


@template(T, "intermediate", VC5, VC6)
def depth_after_pour(r):
    """math-pat-volume-cuboid-water-level"""
    for _ in range(200):
        l, w = r.choice([20, 25, 30, 40, 50]), r.choice([20, 25, 30, 40])
        X = r.choice([2, 3, 4, 5, 6, 8, 10, 12])
        if l != w and (X * 1000) % (l * w) == 0:
            d = X * 1000 // (l * w)
            h = d + r.choice([6, 10, 14])
            if 3 <= d <= 40:
                break
    else:
        return None
    name = nm(r)
    stem = (f"{name}'s empty rectangular tank has a base {l} cm by {w} cm and is {h} cm high. {name} pours {X} l of water into it. "
            f"How deep is the water, in cm?")
    return build(depth_after_pour, stem, d, [
        (d * 10, "decimal_place_error", "Made an error with the zeros."),
        (X * 1000 // l if (X * 1000) % l == 0 else None, "forgot_the_width", "Divided by the length only."),
        (X * 1000 // (l + w) if (X * 1000) % (l + w) == 0 else None, "divided_by_the_sum", "Divided by the sum of the length and width."),
        (d + 2, "slip_in_division", "Made a slip in the division."),
        (d - 1 if d > 1 else d + 3, "slip_in_division", "Made a slip in the division.")],
        [f"{X} l = {X * 1000} cm³", f"Base area = {l} × {w} = {l * w} cm²", f"Depth = {X * 1000} ÷ {l * w} = {d} cm"],
        {"l": l, "w": w, "X": X}, U("cm"), whole=True, auto_slips=False, figure=box(l, w, h))


@checker(depth_after_pour)
def _(p):
    return F(next(d for d in range(1, 500) if p["l"] * p["w"] * d == p["X"] * 1000))


@template(T, "competent", VC5, VC9)
def pour_into_tank(r):
    """math-pat-volume-cuboid-water-level"""
    for _ in range(300):
        l, w = r.choice([20, 25, 30, 40, 50]), r.choice([20, 25, 30, 40])
        d1 = r.choice([6, 8, 10, 12, 15])
        X = r.choice([2, 3, 4, 5, 6, 8])
        h = r.choice([20, 24, 25, 30, 36, 40])
        if l != w and (X * 1000) % (l * w) == 0 and d1 + X * 1000 // (l * w) < h - 2 and (l * w * (h - d1)) % 1000 == 0:
            break
    else:
        return None
    name = nm(r)
    add = X * 1000 // (l * w)
    mode = r.choice(["depth", "more"])
    fig = box(l, w, h, water=d1, dl=f"{d1} cm")
    if mode == "depth":
        stem = (f"The tank in the figure is {l} cm long, {w} cm wide and {h} cm high. It has water {d1} cm deep. {name} pours in another {X} l of water. "
                f"What is the depth of the water now, in cm?")
        ans = d1 + add
        return build(pour_into_tank, stem, ans, [
            (add, "gave_the_rise_only", "Gave the increase in depth only."),
            (d1 + X, "added_litres_to_cm", "Added the litres to the depth."),
            (d1 + add * 10, "decimal_place_error", "Made an error with the zeros."),
            (ans + 2, "slip_in_working", "Made a slip in the working."),
            (ans - 1, "slip_in_working", "Made a slip in the working.")],
            [f"{X} l = {X * 1000} cm³", f"Rise in depth = {X * 1000} ÷ ({l} × {w}) = {add} cm", f"New depth = {d1} + {add} = {ans} cm"],
            {"l": l, "w": w, "h": h, "d1": d1, "X": X, "mode": mode}, U("cm"), whole=True, auto_slips=False, figure=fig)
    more = l * w * (h - d1) // 1000
    stem = (f"The tank in the figure is {l} cm long, {w} cm wide and {h} cm high. It has water {d1} cm deep. "
            f"How many more litres of water are needed to fill the tank completely?")
    return build(pour_into_tank, stem, more, [
        (l * w * h // 1000 if (l * w * h) % 1000 == 0 else None, "gave_the_capacity", "Gave the capacity of the tank."),
        (l * w * d1 // 1000 if (l * w * d1) % 1000 == 0 else None, "gave_the_water_already_in", "Gave the water already in the tank."),
        (h - d1, "gave_the_height_difference", "Gave the difference in heights."),
        (l * w * (h - d1), "did_not_change_to_litres", "Gave the answer in cm³."),
        (more + 2, "slip_in_working", "Made a slip in the working.")],
        [f"Empty space: {l} × {w} × ({h} - {d1}) = {l * w * (h - d1)} cm³", f"{l * w * (h - d1)} ÷ 1000 = {more} l"],
        {"l": l, "w": w, "h": h, "d1": d1, "X": X, "mode": mode}, U("l"), whole=True, auto_slips=False, figure=fig)


@checker(pour_into_tank)
def _(p):
    l, w, h, d1 = p["l"], p["w"], p["h"], p["d1"]
    if p["mode"] == "depth":
        return F(l * w * d1 + p["X"] * 1000, l * w)
    return F(sum(l * w for _ in range(h - d1)), 1000)


@template(T, "competent", VC5, VC2)
def solid_in_water(r):
    """math-pat-volume-cuboid-water-level"""
    for _ in range(400):
        l, w = r.choice([20, 25, 30, 40, 50]), r.choice([20, 25, 30, 40])
        e = r.choice([10, 15, 20])
        d = r.choice([6, 8, 10, 12, 15])
        h = r.choice([25, 30, 36, 40])
        if l != w and (e ** 3) % (l * w) == 0 and e <= 20 and d + e ** 3 // (l * w) < h - 1:
            break
    else:
        return None
    rise = e ** 3 // (l * w)
    name = nm(r)
    mode = r.choice(["rise", "new"])
    fig = box(l, w, h, water=d, dl=f"{d} cm")
    if mode == "rise":
        stem = (f"The rectangular tank in the figure has a base {l} cm by {w} cm. It holds water {d} cm deep. {name} puts in a metal cube of edge {e} cm, "
                f"which sinks to the bottom and is completely under water. By how many cm does the water level rise?")
        return build(solid_in_water, stem, rise, [
            (e, "used_the_edge_as_the_rise", "Used the edge of the cube as the rise."),
            (e ** 3 // (l + w) if (e ** 3) % (l + w) == 0 else None, "divided_by_the_sum", "Divided by the sum of the sides of the base."),
            (e * e * 1 // 1 // (l * w // 100) if (e * e) % (l * w // 100) == 0 else None, "used_the_face_area", "Used the area of one face of the cube."),
            (rise + 2, "slip_in_division", "Made a slip in the division."),
            (rise * 2 + 1, "slip_in_division", "Made a slip in the division.")],
            [f"Volume of cube = {e} × {e} × {e} = {e ** 3} cm³", f"Rise = {e ** 3} ÷ ({l} × {w}) = {rise} cm"],
            {"l": l, "w": w, "e": e, "d": d, "h": h, "mode": mode}, U("cm"), whole=True, auto_slips=False, figure=fig)
    stem = (f"The rectangular tank in the figure has a base {l} cm by {w} cm. It holds water {d} cm deep. {name} puts in a metal cube of edge {e} cm, "
            f"which sinks to the bottom and is completely under water. What is the depth of the water now, in cm?")
    return build(solid_in_water, stem, d + rise, [
        (rise, "gave_the_rise_only", "Gave the rise only."),
        (d + e, "added_the_edge", "Added the edge of the cube to the depth."),
        (d + e ** 3 // (l + w) if (e ** 3) % (l + w) == 0 else None, "divided_by_the_sum", "Divided by the sum of the sides of the base."),
        (d + rise + 2, "slip_in_division", "Made a slip in the working."),
        (d + rise * 2, "slip_in_division", "Made a slip in the working.")],
        [f"Volume of cube = {e ** 3} cm³", f"Rise = {e ** 3} ÷ ({l} × {w}) = {rise} cm", f"New depth = {d} + {rise} = {d + rise} cm"],
        {"l": l, "w": w, "e": e, "d": d, "h": h, "mode": mode}, U("cm"), whole=True, auto_slips=False, figure=fig)


@checker(solid_in_water)
def _(p):
    vol = p["e"] * p["e"] * p["e"]
    base = p["l"] * p["w"]
    level, v = p["d"], 0
    while v < vol:
        v += base
        level += 1
    rise = level - p["d"]
    return F(rise if p["mode"] == "rise" else level)


@template(T, "competent", VC4, VC2)
def cubes_in_box(r):
    e = r.choice([2, 3, 4, 5])
    l, w, h = r.randint(4, 7) * e + r.randint(0, e - 1), r.randint(3, 5) * e + r.randint(0, e - 1), r.randint(2, 4) * e + r.randint(0, e - 1)
    n = (l // e) * (w // e) * (h // e)
    by_vol = (l * w * h) // (e ** 3)
    if by_vol == n:
        return None
    name = nm(r)
    stem = (f"{name} packs {e}-cm cubes into the open box shown, which is {l} cm long, {w} cm wide and {h} cm high, so that the cubes fit neatly in rows and layers. "
            f"What is the greatest number of cubes that can be packed in the box?")
    return build(cubes_in_box, stem, n, [
        (by_vol, "divided_volumes", "Divided the volume of the box by the volume of one cube."),
        (-(-l // e) * -(-w // e) * -(-h // e), "rounded_up_each_edge", "Rounded up the number of cubes along each edge."),
        (n + (l // e) * (w // e), "counted_an_extra_layer", "Counted one layer too many."),
        (n - (l // e) * (w // e) if n > (l // e) * (w // e) else None, "missed_a_layer", "Missed a layer."),
        (n + 2, "slip_in_working", "Made a slip in the working.")],
        [f"Along the length: {l} ÷ {e} = {l // e} cubes", f"Along the width: {w} ÷ {e} = {w // e} cubes", f"Layers: {h} ÷ {e} = {h // e}", f"{l // e} × {w // e} × {h // e} = {n}"],
        {"l": l, "w": w, "h": h, "e": e}, lambda v: f"{num(v)} cubes", whole=True, auto_slips=False, figure=box(l, w, h))


@checker(cubes_in_box)
def _(p):
    e = p["e"]
    return F(sum(1 for x in range(0, p["l"] - e + 1, e) for y in range(0, p["w"] - e + 1, e) for z in range(0, p["h"] - e + 1, e)))


@template(T, "competent", VC5, VC6)
def tap_fill_time(r):
    for _ in range(300):
        l, w, h = r.choice([40, 50, 60, 80]), r.choice([30, 40, 50]), r.choice([30, 40, 50, 60])
        d = r.choice([0, 0, 10, 15, 20])
        rate = r.choice([4, 5, 6, 8, 10, 12, 15, 20])
        vol = l * w * (h - d)
        if vol % 1000 == 0 and (vol // 1000) % rate == 0 and l != w and (vol // 1000) // rate >= 3 and d < h:
            break
    else:
        return None
    lit = vol // 1000
    t = lit // rate
    name = nm(r)
    start = "empty" if d == 0 else f"already holds water to a depth of {d} cm"
    stem = (f"{name}'s rectangular tank is {l} cm long, {w} cm wide and {h} cm high and {start}. A tap fills the tank at {rate} l per minute. "
            f"How many minutes does it take to fill the tank completely?")
    return build(tap_fill_time, stem, t, [
        (lit, "gave_the_litres_needed", "Gave the number of litres needed."),
        (vol // rate if vol % rate == 0 else None, "did_not_change_units", "Divided cm³ by litres per minute."),
        (l * w * h // 1000 // rate if d and (l * w * h) % (1000 * rate) == 0 else None, "ignored_the_water_already_there", "Filled the whole tank, ignoring the water already in it."),
        (lit * rate, "multiplied_instead_of_divided", "Multiplied by the rate."),
        (t + 2, "slip_in_division", "Made a slip in the division.")],
        [f"Space to fill = {l} × {w} × {h - d} = {vol} cm³ = {lit} l", f"Time = {lit} ÷ {rate} = {t} minutes"],
        {"l": l, "w": w, "h": h, "d": d, "rate": rate}, lambda v: f"{num(v)} minutes", whole=True, auto_slips=False,
        figure=box(l, w, h, water=d if d else None, dl=f"{d} cm" if d else None))


@checker(tap_fill_time)
def _(p):
    litres = F(p["l"] * p["w"] * (p["h"] - p["d"]), 1000)
    t = 0
    while litres > 0:
        litres -= p["rate"]
        t += 1
    return F(t)


@template(T, "competent", VC5, VC9)
def pour_between_tanks(r):
    """math-pat-volume-cuboid-water-level"""
    for _ in range(500):
        l1, w1 = r.choice([30, 40, 50, 60]), r.choice([20, 25, 30, 40])
        d1 = r.choice([10, 12, 15, 18, 20, 24])
        l2, w2 = r.choice([20, 25, 30, 40]), r.choice([20, 25, 30, 40])
        if l1 != w1 and (l1 * w1 * d1) % (l2 * w2) == 0:
            d2 = l1 * w1 * d1 // (l2 * w2)
            if 4 <= d2 <= 45 and d2 != d1:
                break
    else:
        return None
    h2 = d2 + r.choice([6, 10, 15])
    name = nm(r)
    stem = (f"Tank A has a base {l1} cm by {w1} cm and contains water {d1} cm deep. {name} pours all the water from Tank A into the empty Tank B shown, "
            f"which has a base {l2} cm by {w2} cm. How deep is the water in Tank B, in cm?")
    return build(pour_between_tanks, stem, d2, [
        (d1, "assumed_the_same_depth", "Assumed the depth stays the same."),
        ((l2 * w2 * d1) // (l1 * w1) if (l2 * w2 * d1) % (l1 * w1) == 0 else None, "inverted_the_ratio", "Divided the base areas the wrong way round."),
        (l1 * w1 * d1 // (l2 + w2) if (l1 * w1 * d1) % (l2 + w2) == 0 else None, "divided_by_the_sum", "Divided by the sum of the sides of the base."),
        (d2 + 2, "slip_in_division", "Made a slip in the division."),
        (d2 - 1, "slip_in_division", "Made a slip in the division.")],
        [f"Volume of water = {l1} × {w1} × {d1} = {l1 * w1 * d1} cm³", f"Depth in B = {l1 * w1 * d1} ÷ ({l2} × {w2}) = {d2} cm"],
        {"l1": l1, "w1": w1, "d1": d1, "l2": l2, "w2": w2}, U("cm"), whole=True, auto_slips=False,
        figure=tank_svg(l2, w2, h2, labs=(f"{l2} cm", f"{w2} cm", f"{h2} cm")))


@checker(pour_between_tanks)
def _(p):
    vol = p["l1"] * p["w1"] * p["d1"]
    return F(next(d for d in range(1, 500) if p["l2"] * p["w2"] * d == vol))


@template(T, "competent", VC4, VC5)
def block_with_hole(r):
    l, w, h = r.randint(15, 30), r.randint(10, 20), r.randint(6, 14)
    a, b = r.randint(2, 5), r.randint(2, 5)
    if a >= w or b >= l:
        return None
    left = l * w * h - a * b * h
    name = nm(r)
    stem = (f"{name} has a solid wooden cuboid {l} cm long, {w} cm wide and {h} cm high. {name} cuts a square-ended hole, {a} cm by {b} cm, "
            f"straight through the block from the top to the bottom. What is the volume of wood left, in cm³?")
    return build(block_with_hole, stem, left, [
        (a * b * h, "gave_the_volume_removed", "Gave the volume of the hole."),
        (l * w * h, "ignored_the_hole", "Ignored the hole."),
        (l * w * h - a * b, "took_away_the_area_of_the_hole", "Took away the area of the end of the hole."),
        (left + h, "slip_in_working", "Made a slip in the working."),
        (left - 10, "slip_in_working", "Made a slip in the working.")],
        [f"Volume of block = {l} × {w} × {h} = {l * w * h} cm³", f"Volume of hole = {a} × {b} × {h} = {a * b * h} cm³", f"Left = {left} cm³"],
        {"l": l, "w": w, "h": h, "a": a, "b": b}, U("cm³"), whole=True, auto_slips=False, figure=box(l, w, h))


@checker(block_with_hole)
def _(p):
    wood = sum(1 for x in range(p["l"]) for y in range(p["w"]) if not (x < p["b"] and y < p["a"]))
    return F(wood * p["h"])


@template(T, "competent", VC5, VC7)
def fraction_capacity(r):
    for _ in range(500):
        l, w, h = r.choice([40, 50, 60, 25, 30]), r.choice([20, 25, 30, 40]), r.choice([24, 30, 36, 40, 50])
        f1, f2 = r.choice([(F(1, 4), F(2, 3)), (F(2, 5), F(7, 10)), (F(1, 3), F(3, 4)), (F(1, 5), F(3, 5)), (F(3, 8), F(7, 8))])
        cap = l * w * h
        add = (f2 - f1) * cap
        if l != w and add.denominator == 1 and add % 1000 == 0 and cap % 1000 == 0:
            break
    else:
        return None
    X = int(add) // 1000
    name = nm(r)
    stem = (f"{name}'s rectangular tank has a base {l} cm by {w} cm. It is {f1.numerator}/{f1.denominator} full of water. After {X} l more water is poured in, "
            f"it is {f2.numerator}/{f2.denominator} full. What is the height of the tank, in cm?")
    fr = f2 - f1
    return build(fraction_capacity, stem, h, [
        (X * 1000 // (l * w) if (X * 1000) % (l * w) == 0 else None, "gave_the_rise_in_depth", "Gave the rise in water level, not the height of the tank."),
        (cap // (l * w) // 2 if cap % (2 * l * w) == 0 else None, "halved_the_height", "Halved the height."),
        (int(X * 1000 // fr) // (l * w) + 5 if (X * 1000 / fr) % 1 == 0 else None, "slip_in_working", "Made a slip in the working."),
        (int(X * 1000 / f2) // (l * w) if (X * 1000 / f2) % (l * w) == 0 else None, "used_the_final_fraction_only", "Used the final fraction only."),
        (h + 6, "slip_in_working", "Made a slip in the working."),
        (h - 4, "slip_in_working", "Made a slip in the working.")],
        [f"Fraction added = {f2.numerator}/{f2.denominator} - {f1.numerator}/{f1.denominator} = {fr.numerator}/{fr.denominator}", f"Capacity = {X} l ÷ {fr.numerator}/{fr.denominator} = {X * 1000 / fr:.0f} cm³",
         f"Height = {cap} ÷ ({l} × {w}) = {h} cm"], {"l": l, "w": w, "X": X, "f1": [f1.numerator, f1.denominator], "f2": [f2.numerator, f2.denominator]},
        U("cm"), whole=True, auto_slips=False, figure=tank_svg(l, w, h, water=F(f1) * h, labs=(f"{l} cm", f"{w} cm", "? cm")))


@checker(fraction_capacity)
def _(p):
    f1, f2 = F(*p["f1"]), F(*p["f2"])
    cap = F(p["X"] * 1000) / (f2 - f1)
    return cap / (p["l"] * p["w"])


# ================================================================ circles

PIS = [(F(314, 100), "3.14"), (F(22, 7), "22/7")]
PI_REAL = math.pi


def pick_pi(r):
    return r.choice(PIS)


def lens_for(pi_s, full=True, half=False):
    """Lengths that keep the arithmetic clean for the chosen value of pi."""
    if pi_s == "22/7":
        return [14, 28, 42] if half else [7, 14, 21, 28, 35]
    return [4, 6, 8, 10, 12, 14, 16, 20] if half else [3, 4, 5, 6, 8, 10, 12, 14, 15, 20]


def circ_fig(rad, mode):
    u = UF(-rad, -rad, rad, rad, mx=56, my=30, maxscale=14)
    u.circle((0, 0), rad, shade=0.08)
    u.dot((0, 0))
    if mode == "radius":
        u.seg((0, 0), (rad, 0), width=1.8)
        u.seg_label((0, 0), (rad, 0), f"{num(rad)} cm", (0, rad), size=13)
    else:
        u.seg((-rad, 0), (rad, 0), width=1.8)
        u.seg_label((-rad, 0), (rad, 0), f"{num(2 * rad)} cm", (0, rad), size=13)
    return u.svg("Circle")


@template(T, "basic", CI1)
def circle_circumference(r):
    pi, ps = pick_pi(r)
    d = r.choice(lens_for(ps, half=True)) if r.random() < 0.5 else r.choice(lens_for(ps)) * 2
    mode = r.choice(["radius", "diameter"])
    rad = F(d, 2)
    C = pi * d
    given = rad if mode == "radius" else d
    name = nm(r)
    stem = f"The figure shows {name}'s circular plate with a {mode} of {num(given)} cm. Find its circumference. Take π = {ps}."
    return build(circle_circumference, stem, C, [
        (pi * rad * rad, "found_area_instead", "Used the area formula."),
        (pi * d * 2 if mode == "diameter" else pi * rad, "used_wrong_length_in_formula",
         "Put the diameter into 2 × π × r." if mode == "diameter" else "Used π × r and forgot the 2."),
        (pi * rad, "forgot_the_2", "Used π × radius."),
        (pi * d * d, "squared_the_diameter", "Squared the diameter."),
        (C + 2, "slip_in_working", "Made a slip in the working."),
        (C - 1, "slip_in_working", "Made a slip in the working.")],
        [f"Diameter = {num(d)} cm", f"Circumference = π × d = {ps} × {num(d)} = {num(C)} cm"], {"d": d, "pi": ps, "mode": mode},
        U("cm"), auto_slips=False, figure=circ_fig(rad, mode))


@checker(circle_circumference)
def _(p):
    pi = dict((s, v) for v, s in PIS)[p["pi"]]
    return 2 * pi * F(p["d"], 2)


@template(T, "basic", CI1)
def circle_area(r):
    pi, ps = pick_pi(r)
    rad = r.choice(lens_for(ps))
    mode = r.choice(["radius", "diameter"])
    given = rad if mode == "radius" else 2 * rad
    A = pi * rad * rad
    name = nm(r)
    stem = f"The figure shows {name}'s circular rug with a {mode} of {num(given)} cm. Find its area. Take π = {ps}."
    return build(circle_area, stem, A, [
        (2 * pi * rad, "found_circumference_instead", "Used the circumference formula."),
        (pi * 2 * rad * 2 * rad if mode == "diameter" else pi * rad, "used_diameter_as_radius" if mode == "diameter" else "forgot_to_square",
         "Used the diameter as the radius." if mode == "diameter" else "Forgot to square the radius."),
        (pi * rad, "forgot_to_square", "Forgot to square the radius."),
        (pi * rad * 2, "doubled_instead_of_squared", "Multiplied the radius by 2 instead of by itself."),
        (A + 3, "slip_in_working", "Made a slip in the working.")],
        [f"Radius = {num(rad)} cm", f"Area = π × r × r = {ps} × {num(rad)} × {num(rad)} = {num(A)} cm²"], {"r": rad, "pi": ps, "mode": mode},
        U("cm²"), auto_slips=False, figure=circ_fig(rad, mode))


@checker(circle_area)
def _(p):
    pi = dict((s, v) for v, s in PIS)[p["pi"]]
    return pi * F(2 * p["r"]) ** 2 / 4


@template(T, "basic", CI1)
def radius_from_circumference(r):
    pi, ps = pick_pi(r)
    d = r.choice(lens_for(ps, half=True))
    C = pi * d
    ask = r.choice(["radius", "diameter"])
    name = nm(r)
    stem = f"The circumference of {name}'s circular pond is {num(C)} m. Find the {ask} of the pond. Take π = {ps}."
    ans = F(d, 2) if ask == "radius" else F(d)
    return build(radius_from_circumference, stem, ans, [
        (F(d) if ask == "radius" else F(d, 2), "mixed_up_radius_and_diameter", "Gave the diameter instead of the radius." if ask == "radius" else "Gave the radius instead of the diameter."),
        (F(d, 4) if ask == "radius" else F(d) * 2, "halved_twice" if ask == "radius" else "doubled_twice", "Halved twice." if ask == "radius" else "Doubled twice."),
        (C / 2, "halved_the_circumference", "Halved the circumference and did not divide by π."),
        (ans + 1, "slip_in_working", "Made a slip in the working."),
        (ans + 3, "slip_in_working", "Made a slip in the working.")],
        [f"Diameter = {num(C)} ÷ {ps} = {num(d)} m", f"Radius = {num(F(d, 2))} m"], {"C": str(C), "pi": ps, "ask": ask}, U("m"), auto_slips=False)


@checker(radius_from_circumference)
def _(p):
    pi = dict((s, v) for v, s in PIS)[p["pi"]]
    d = next(F(x, 2) for x in range(1, 4000) if pi * F(x, 2) == F(p["C"]))
    return d / 2 if p["ask"] == "radius" else d


@template(T, "basic", CI1)
def radius_from_area(r):
    pi, ps = pick_pi(r)
    rad = r.choice(lens_for(ps))
    A = pi * rad * rad
    name = nm(r)
    stem = f"The area of {name}'s circular mat is {num(A)} cm². What is its radius? Take π = {ps}."
    return build(radius_from_area, stem, rad, [
        (rad * rad, "stopped_at_r_squared", "Found the radius squared and did not take the square root."),
        (A / pi / 2, "divided_by_two_instead_of_root", "Divided by 2 instead of finding the square root."),
        (2 * rad, "gave_the_diameter", "Gave the diameter."),
        (F(rad, 2) if rad % 2 == 0 else rad + 2, "halved_the_radius", "Halved the radius."),
        (rad + 1, "slip_in_working", "Made a slip in the working.")],
        [f"π × r × r = {num(A)}, so r × r = {num(A)} ÷ {ps} = {rad * rad}", f"r = {rad} cm"], {"A": str(A), "pi": ps}, U("cm"), auto_slips=False)


@checker(radius_from_area)
def _(p):
    pi = dict((s, v) for v, s in PIS)[p["pi"]]
    sq = F(p["A"]) / pi
    return F(next(x for x in range(1, 500) if x * x == sq))


# ---------------------------------------------------------------- plane shapes with arcs

def fig_semicircle(d):
    R = F(d, 2)
    u = UF(-R, -R, R, 0, mx=50, my=40, maxscale=14)
    pb = PB(u).m(-R, 0).a(R, R, 0, 1).z()
    u.path(pb, shade=0.12)
    u.seg_label((-R, 0), (R, 0), f"{num(d)} cm", (0, -R))
    return u.svg("Semicircle")


def fig_quarter(rad):
    u = UF(0, -rad, rad, 0, mx=50, my=36, maxscale=14)
    pb = PB(u).m(0, 0).l(0, -rad).a(rad, rad, 0, 1).z()
    u.path(pb, shade=0.12)
    u.right_mark((0, 0), (1, 0), (0, -1))
    u.seg_label((0, 0), (rad, 0), f"{num(rad)} cm", (0, -rad))
    u.seg_label((0, 0), (0, -rad), f"{num(rad)} cm", (rad, 0))
    return u.svg("Quarter circle")


@template(T, "intermediate", CI2)
def semicircle_pa(r):
    pi, ps = pick_pi(r)
    d = r.choice(lens_for(ps, half=True))
    ask = r.choice(["perimeter", "area"])
    name = nm(r)
    arc = pi * d / 2
    stem = f"The figure shows a semicircle with a diameter of {num(d)} cm, cut by {name}. Find its {ask}. Take π = {ps}."
    fig = fig_semicircle(d)
    if ask == "perimeter":
        ans = arc + d
        return build(semicircle_pa, stem, ans, [
            (arc, "left_out_the_diameter", "Found only the curved part."),
            (pi * d + d, "used_the_full_circle", "Used the whole circumference and added the diameter."),
            (arc + F(d, 2), "added_the_radius", "Added the radius instead of the diameter."),
            (pi * d, "used_the_full_circle", "Gave the circumference of the whole circle."),
            (ans + 2, "slip_in_working", "Made a slip in the working.")],
            [f"Curved part = 1/2 × π × {num(d)} = {num(arc)} cm", f"Perimeter = {num(arc)} + {num(d)} = {num(ans)} cm"],
            {"d": d, "pi": ps, "ask": ask}, U("cm"), auto_slips=False, figure=fig)
    A = pi * F(d, 2) ** 2 / 2
    return build(semicircle_pa, stem, A, [
        (pi * F(d, 2) ** 2, "used_the_full_circle", "Found the area of the whole circle."),
        (pi * d * d / 2, "used_diameter_as_radius", "Used the diameter as the radius."),
        (pi * F(d, 2) / 2, "forgot_to_square", "Forgot to square the radius."),
        (pi * F(d, 2) ** 2 / 4, "halved_twice", "Halved the area twice."),
        (A + 3, "slip_in_working", "Made a slip in the working.")],
        [f"Radius = {num(F(d, 2))} cm", f"Area = 1/2 × π × {num(F(d, 2))} × {num(F(d, 2))} = {num(A)} cm²"], {"d": d, "pi": ps, "ask": ask},
        U("cm²"), auto_slips=False, figure=fig)


@checker(semicircle_pa)
def _(p):
    pi = dict((s, v) for v, s in PIS)[p["pi"]]
    d = F(p["d"])
    if p["ask"] == "perimeter":
        return (2 * pi * (d / 2)) / 2 + 2 * (d / 2)
    return (pi * d * d / 4) / 2


@template(T, "intermediate", CI2)
def quarter_pa(r):
    pi, ps = pick_pi(r)
    rad = r.choice(lens_for(ps))
    ask = r.choice(["perimeter", "area"])
    name = nm(r)
    stem = f"The figure shows {name}'s quarter circle with a radius of {num(rad)} cm. Find its {ask}. Take π = {ps}."
    fig = fig_quarter(rad)
    arc = pi * rad / 2
    if ask == "perimeter":
        ans = arc + 2 * rad
        return build(quarter_pa, stem, ans, [
            (arc, "left_out_the_straight_sides", "Found only the curved part."),
            (arc + rad, "added_only_one_radius", "Added only one radius."),
            (pi * rad + 2 * rad, "used_a_semicircle", "Used half the circumference instead of a quarter."),
            (2 * pi * rad / 4 * 4 if False else pi * rad * 2, "used_the_full_circle", "Gave the circumference of the whole circle."),
            (ans + 2, "slip_in_working", "Made a slip in the working.")],
            [f"Curved part = 1/4 × 2 × π × {num(rad)} = {num(arc)} cm", f"Perimeter = {num(arc)} + {rad} + {rad} = {num(ans)} cm"],
            {"r": rad, "pi": ps, "ask": ask}, U("cm"), auto_slips=False, figure=fig)
    A = pi * rad * rad / 4
    return build(quarter_pa, stem, A, [
        (pi * rad * rad, "used_the_full_circle", "Found the area of the whole circle."),
        (pi * rad * rad / 2, "used_a_semicircle", "Found the area of a semicircle."),
        (pi * rad / 4, "forgot_to_square", "Forgot to square the radius."),
        (pi * rad * rad / 8, "halved_twice", "Divided by 8."),
        (A + 3, "slip_in_working", "Made a slip in the working.")],
        [f"Area = 1/4 × π × {rad} × {rad} = {num(A)} cm²"], {"r": rad, "pi": ps, "ask": ask}, U("cm²"), auto_slips=False, figure=fig)


@checker(quarter_pa)
def _(p):
    pi = dict((s, v) for v, s in PIS)[p["pi"]]
    rad = F(p["r"])
    if p["ask"] == "perimeter":
        return pi * 2 * rad / 4 + rad + rad
    return pi * rad * rad * F(90, 360)


def fig_track(L_, d):
    u = UF(-F(d, 2), 0, L_ + F(d, 2), d, mx=34, my=40, maxscale=12)
    R = F(d, 2)
    pb = PB(u).m(0, 0).l(L_, 0).a(R, L_, d, 1).l(0, d).a(R, 0, 0, 1).z()
    u.path(pb, shade=0.1)
    u.seg((0, 0), (0, d), dash=True, width=1.2)
    u.seg((L_, 0), (L_, d), dash=True, width=1.2)
    u.seg_label((0, 0), (L_, 0), f"{num(L_)} m", (L_ / 2, d))
    u.text((0, d / 2), f"{num(d)} m", dx=5, anchor="start", size=12)
    return u.svg("Running track")


@template(T, "intermediate", CI3, CI2)
def track_pa(r):
    """math-pat-circle-perimeter-composite"""
    pi, ps = pick_pi(r)
    d = r.choice(lens_for(ps, half=True)) if ps == "3.14" else r.choice([14, 28])
    Lg = r.choice([30, 40, 50, 60, 70])
    ask = r.choice(["perimeter", "area"])
    name = nm(r)
    fig = fig_track(Lg, d)
    stem = (f"The figure shows a running track made of a rectangle and two semicircles. The rectangle is {Lg} m by {d} m. "
            f"{name} wants the {'distance around the track' if ask == 'perimeter' else 'area enclosed by the track'}. Take π = {ps}.")
    if ask == "perimeter":
        ans = 2 * Lg + pi * d
        return build(track_pa, stem, ans, [
            (2 * Lg + pi * d / 2, "used_one_semicircle", "Added the curved part of one semicircle only."),
            (2 * Lg + 2 * d + pi * d, "added_the_diameters", "Added the diameters that are not on the outside."),
            (Lg + pi * d, "used_one_straight_side", "Added only one straight side."),
            (2 * (Lg + d) , "left_out_the_curves", "Left out the curved parts."),
            (ans + 2, "slip_in_working", "Made a slip in the working.")],
            [f"The two semicircles make a circle of diameter {d} m: π × {d} = {num(pi * d)} m", f"Perimeter = 2 × {Lg} + {num(pi * d)} = {num(ans)} m"],
            {"L": Lg, "d": d, "pi": ps, "ask": ask}, U("m"), auto_slips=False, figure=fig)
    ans = Lg * d + pi * F(d, 2) ** 2
    return build(track_pa, stem, ans, [
        (Lg * d + pi * F(d, 2) ** 2 / 2, "used_one_semicircle", "Added the area of one semicircle only."),
        (Lg * d, "left_out_the_semicircles", "Found the rectangle only."),
        (Lg * d + pi * d * d, "used_diameter_as_radius", "Used the diameter as the radius."),
        (pi * F(d, 2) ** 2, "left_out_the_rectangle", "Found the circle only."),
        (ans + 4, "slip_in_working", "Made a slip in the working.")],
        [f"Rectangle = {Lg} × {d} = {Lg * d} m²", f"Two semicircles = π × {num(F(d, 2))} × {num(F(d, 2))} = {num(pi * F(d, 2) ** 2)} m²", f"Total = {num(ans)} m²"],
        {"L": Lg, "d": d, "pi": ps, "ask": ask}, U("m²"), auto_slips=False, figure=fig)


@checker(track_pa)
def _(p):
    pi = dict((s, v) for v, s in PIS)[p["pi"]]
    L_, d = F(p["L"]), F(p["d"])
    if p["ask"] == "perimeter":
        return L_ + L_ + 2 * (pi * (d / 2))
    return L_ * d + 2 * (pi * (d / 2) ** 2 / 2)


def fig_semis(a, b, shade=0.2):
    D = a + b
    u = UF(-F(D, 2), -F(D, 2), F(D, 2), 0, mx=46, my=44, maxscale=12)
    x0 = -F(D, 2)
    pb = PB(u).m(x0, 0).a(F(D, 2), F(D, 2), 0, 1).a(F(b, 2), x0 + a, 0, 0).a(F(a, 2), x0, 0, 0).z()
    u.path(pb, shade=shade)
    u.seg_label((x0, 0), (x0 + a, 0), f"{num(a)} cm", (0, -D))
    u.seg_label((x0 + a, 0), (F(D, 2), 0), f"{num(b)} cm", (0, -D))
    p0, p1 = u.P(x0, 0), u.P(F(D, 2), 0)
    y = p0[1] + 30
    u.f.line(p0[0], y, p1[0], y, width=1.1)
    u.f.line(p0[0], y - 4, p0[0], y + 4, width=1.1)
    u.f.line(p1[0], y - 4, p1[0], y + 4, width=1.1)
    u.f.text((p0[0] + p1[0]) / 2, y + 12, f"{num(D)} cm", size=13)
    return u.svg("Semicircles")


def semi_ab(r, ps):
    a, b = r.sample(lens_for(ps, half=True) if ps == "3.14" else [7, 14, 21], 2)
    return a, b


@template(T, "intermediate", CI3, CI2)
def semis_perimeter(r):
    """math-pat-circle-perimeter-composite"""
    pi, ps = pick_pi(r)
    a, b = semi_ab(r, ps)
    D = a + b
    ans = pi * D
    name = nm(r)
    stem = (f"The figure shows a large semicircle of diameter {num(D)} cm with two smaller semicircles of diameters {num(a)} cm and {num(b)} cm inside it. "
            f"{name} finds the perimeter of the shaded part. Take π = {ps}.")
    return build(semis_perimeter, stem, ans, [
        (pi * D / 2, "used_the_big_arc_only", "Found the curved part of the big semicircle only."),
        (pi * D / 2 + D, "used_the_diameter", "Used the big semicircle's perimeter."),
        (pi * (a + b) / 2, "used_the_small_arcs_only", "Added the small curved parts only."),
        (pi * D + D, "added_the_diameter", "Added the straight line that is not on the boundary."),
        (ans + 2, "slip_in_working", "Made a slip in the working.")],
        [f"Big arc = 1/2 × π × {num(D)} = {num(pi * D / 2)} cm", f"Small arcs = 1/2 × π × {num(a)} + 1/2 × π × {num(b)} = {num(pi * D / 2)} cm", f"Perimeter = {num(ans)} cm"],
        {"a": a, "b": b, "pi": ps}, U("cm"), auto_slips=False, figure=fig_semis(a, b))


@checker(semis_perimeter)
def _(p):
    pi = dict((s, v) for v, s in PIS)[p["pi"]]
    a, b = F(p["a"]), F(p["b"])
    return pi * (a + b) / 2 + pi * a / 2 + pi * b / 2


def fig_rect_semi(w, h):
    R = F(w, 2)
    u = UF(0, -R, w, h, mx=48, my=34, maxscale=12)
    pb = PB(u).m(0, h).l(0, 0).a(R, w, 0, 1).l(w, h).z()
    u.path(pb, shade=0.1)
    u.seg((0, 0), (w, 0), dash=True, width=1.2)
    u.seg_label((0, h), (w, h), f"{num(w)} cm", (w / 2, 0))
    u.seg_label((0, 0), (0, h), f"{num(h)} cm", (w, h / 2))
    return u.svg("Rectangle with semicircle")


@template(T, "intermediate", CI3)
def rect_semi_pa(r):
    """math-pat-circle-perimeter-composite"""
    pi, ps = pick_pi(r)
    w = r.choice([14, 28]) if ps == "22/7" else r.choice([4, 6, 8, 10, 12, 16, 20])
    h = r.randint(5, 20)
    ask = r.choice(["perimeter", "area"])
    name = nm(r)
    stem = (f"The figure shows {name}'s window, made of a rectangle {num(w)} cm wide and {h} cm high with a semicircle on top. "
            f"Find the {ask} of the window. Take π = {ps}.")
    fig = fig_rect_semi(w, h)
    arc = pi * w / 2
    if ask == "perimeter":
        ans = w + 2 * h + arc
        return build(rect_semi_pa, stem, ans, [
            (2 * w + 2 * h + arc, "counted_the_dashed_line", "Counted the top of the rectangle as part of the perimeter."),
            (w + 2 * h + pi * w, "used_the_full_circle", "Used the whole circumference."),
            (w + 2 * h, "left_out_the_arc", "Left out the curved part."),
            (arc + 2 * h, "left_out_the_bottom", "Left out the bottom side."),
            (ans + 2, "slip_in_working", "Made a slip in the working.")],
            [f"Curved part = 1/2 × π × {num(w)} = {num(arc)} cm", f"Perimeter = {num(w)} + {h} + {h} + {num(arc)} = {num(ans)} cm"],
            {"w": w, "h": h, "pi": ps, "ask": ask}, U("cm"), auto_slips=False, figure=fig)
    ans = w * h + pi * F(w, 2) ** 2 / 2
    return build(rect_semi_pa, stem, ans, [
        (w * h + pi * F(w, 2) ** 2, "used_the_full_circle", "Added the area of a whole circle."),
        (w * h + pi * w * w / 2, "used_diameter_as_radius", "Used the diameter as the radius."),
        (w * h, "left_out_the_semicircle", "Found the rectangle only."),
        (pi * F(w, 2) ** 2 / 2, "left_out_the_rectangle", "Found the semicircle only."),
        (ans + 3, "slip_in_working", "Made a slip in the working.")],
        [f"Rectangle = {num(w)} × {h} = {w * h} cm²", f"Semicircle = 1/2 × π × {num(F(w, 2))} × {num(F(w, 2))} = {num(pi * F(w, 2) ** 2 / 2)} cm²", f"Total = {num(ans)} cm²"],
        {"w": w, "h": h, "pi": ps, "ask": ask}, U("cm²"), auto_slips=False, figure=fig)


@checker(rect_semi_pa)
def _(p):
    pi = dict((s, v) for v, s in PIS)[p["pi"]]
    w, h = F(p["w"]), F(p["h"])
    if p["ask"] == "perimeter":
        return h + h + w + (pi * w) / 2
    return h * w + (pi * (w / 2) * (w / 2)) / 2


def square_figs(kind, s, shade=0.25, mark=True):
    """Shaded part of a square (or rectangle/square of circles). s is the main length."""
    if kind == "two_circles":
        r_ = s
        u = UF(0, 0, 4 * r_, 2 * r_, mx=30, my=40, maxscale=16)
        pb = PB(u).m(0, 0).l(4 * r_, 0).l(4 * r_, 2 * r_).l(0, 2 * r_).z()
        for cx in (r_, 3 * r_):
            pb.m(cx - r_, r_).a(r_, cx + r_, r_, 0).a(r_, cx - r_, r_, 0).z()
        u.path(pb, shade=shade)
        u.seg((r_, r_), (2 * r_, r_), width=1.6)
        u.seg_label((r_, r_), (2 * r_, r_), f"{num(r_)} cm", (r_, 2 * r_), size=12)
        return u.svg("Rectangle with two circles")
    if kind == "four_circles":
        r_ = s
        u = UF(0, 0, 4 * r_, 4 * r_, mx=70, my=24, maxscale=16)
        pb = PB(u).m(0, 0).l(4 * r_, 0).l(4 * r_, 4 * r_).l(0, 4 * r_).z()
        for cx in (r_, 3 * r_):
            for cy in (r_, 3 * r_):
                pb.m(cx - r_, cy).a(r_, cx + r_, cy, 0).a(r_, cx - r_, cy, 0).z()
        u.path(pb, shade=shade)
        u.seg((r_, r_), (2 * r_, r_), width=1.6)
        u.seg_label((r_, r_), (2 * r_, r_), f"{num(r_)} cm", (r_, 2 * r_), size=12)
        return u.svg("Square with four circles")
    u = UF(0, 0, s, s, mx=70, my=30, maxscale=16)
    sq = [(0, 0), (s, 0), (s, s), (0, s)]
    h2 = F(s, 2)
    if kind == "quarter_sq":
        u.path(PB(u).m(0, 0).l(s, 0).l(s, s).a(s, 0, 0, 0).z(), shade=shade)
    elif kind == "inscribed":
        pb = PB(u).m(0, 0).l(s, 0).l(s, s).l(0, s).z().m(0, h2).a(h2, s, h2, 0).a(h2, 0, h2, 0).z()
        u.path(pb, shade=shade)
    elif kind == "four_quarters":
        u.path(PB(u).m(h2, 0).a(h2, 0, h2, 1).a(h2, h2, s, 1).a(h2, s, h2, 1).a(h2, h2, 0, 1).z(), shade=shade)
    elif kind == "semi_sq":
        u.path(PB(u).m(0, 0).l(s, 0).l(s, s).a(h2, 0, s, 0).z(), shade=shade)
    elif kind == "lens":
        u.path(PB(u).m(s, 0).a(s, 0, s, 1).a(s, s, 0, 1).z(), shade=shade)
    u.poly(sq, width=1.4)
    u.edge_label(sq, 0, f"{num(s)} cm")
    return u.svg("Shaded part of a square")


KIND_TEXT = {
    "quarter_sq": "The figure shows a square of side {s} cm. A quarter circle with its centre at one corner and a radius of {s} cm is drawn inside the square.",
    "inscribed": "The figure shows a circle of diameter {s} cm drawn inside a square of side {s} cm.",
    "four_quarters": "The figure shows a square of side {s} cm. Four identical quarter circles, each with its centre at a corner of the square, are drawn inside it. Each quarter circle has a radius of half the side of the square.",
    "semi_sq": "The figure shows a square of side {s} cm. A semicircle, whose diameter is one side of the square, is drawn inside the square.",
}
SQ_COEF = {  # area of the shaded part = a * pi + b
    "quarter_sq": lambda s: (F(-s * s, 4), F(s * s)), "inscribed": lambda s: (F(-s * s, 4), F(s * s)),
    "four_quarters": lambda s: (F(-s * s, 4), F(s * s)), "semi_sq": lambda s: (F(-s * s, 8), F(s * s)),
    "two_circles": lambda s: (F(-2 * s * s), F(8 * s * s)), "four_circles": lambda s: (F(-4 * s * s), F(16 * s * s)),
    "lens": lambda s: (F(s * s, 2), F(-s * s)),
}


def _outside(cx, cy, rr):
    return lambda x, y: (x - cx) ** 2 + (y - cy) ** 2 > rr * rr


SQ_PRED = {
    "quarter_sq": (lambda s: (s, s), lambda s: (lambda x, y: x * x + (y - s) ** 2 > s * s)),
    "inscribed": (lambda s: (s, s), lambda s: _outside(s / 2, s / 2, s / 2)),
    "four_quarters": (lambda s: (s, s), lambda s: (lambda x, y: all((x - cx) ** 2 + (y - cy) ** 2 > (s / 2) ** 2
                                                                 for cx in (0, s) for cy in (0, s)))),
    "semi_sq": (lambda s: (s, s), lambda s: _outside(s / 2, s, s / 2)),
    "two_circles": (lambda s: (4 * s, 2 * s), lambda s: (lambda x, y: all((x - cx) ** 2 + (y - s) ** 2 > s * s for cx in (s, 3 * s)))),
    "four_circles": (lambda s: (4 * s, 4 * s), lambda s: (lambda x, y: all((x - cx) ** 2 + (y - cy) ** 2 > s * s
                                                                        for cx in (s, 3 * s) for cy in (s, 3 * s)))),
    "lens": (lambda s: (s, s), lambda s: (lambda x, y: x * x + y * y <= s * s and (x - s) ** 2 + (y - s) ** 2 <= s * s)),
}


def area_by_coef(kind, s, pi):
    a, b = SQ_COEF[kind](s)
    est = None
    (bw, bh), pred = SQ_PRED[kind][0](s), SQ_PRED[kind][1](s)
    n = 110
    cnt = sum(1 for i in range(n) for j in range(n) if pred((i + .5) * bw / n, (j + .5) * bh / n))
    est = cnt / (n * n) * bw * bh
    exact = a * pi + b
    if abs(est - (float(a) * PI_REAL + float(b))) > 0.03 * abs(float(a) * PI_REAL + float(b)):
        return None
    return exact


@template(T, "competent", CI3)
def shaded_square_family(r):
    """math-pat-circle-area-composite-shaded"""
    kind = r.choice(["quarter_sq", "inscribed", "four_quarters", "semi_sq", "two_circles", "four_circles"])
    pi, ps = pick_pi(r)
    half = kind in ("inscribed", "four_quarters", "semi_sq")
    s = r.choice(lens_for(ps, half=half))
    if kind in ("two_circles", "four_circles"):
        s = r.choice([7, 14] if ps == "22/7" else [2, 3, 4, 5, 6, 8, 10])
    name = nm(r)
    if kind == "two_circles":
        text = f"The figure shows a rectangle with two identical circles, each of radius {s} cm, drawn inside it. The circles touch each other and the sides of the rectangle."
    elif kind == "four_circles":
        text = f"The figure shows a square with four identical circles, each of radius {s} cm, drawn inside it. The circles touch each other and the sides of the square."
    else:
        text = KIND_TEXT[kind].format(s=num(s))
    stem = f"{text} Find the area of the shaded part. Take π = {ps}. ({name}'s design)"
    a, b = SQ_COEF[kind](s)
    ans = a * pi + b
    full = b
    circ = -a * pi
    steps = [f"Area of the whole shape = {num(full)} cm²", f"Area removed = {num(circ)} cm²", f"Shaded area = {num(full)} - {num(circ)} = {num(ans)} cm²"]
    return build(shaded_square_family, stem, ans, [
        (circ, "gave_area_of_circles_only", "Found the area of the circle parts instead of the shaded part."),
        (full, "gave_area_of_square_only", "Found the area of the square or rectangle only."),
        (full + circ, "added_instead_of_subtracted", "Added the circle part instead of taking it away."),
        (full - circ / 2 if kind != "semi_sq" else full - circ * 2, "used_wrong_fraction_of_circle", "Took away the wrong fraction of the circle."),
        (ans + 5, "slip_in_working", "Made a slip in the working.")],
        steps, {"kind": kind, "s": s, "pi": ps}, U("cm²"), auto_slips=False, figure=square_figs(kind, s))


@checker(shaded_square_family)
def _(p):
    pi = dict((s, v) for v, s in PIS)[p["pi"]]
    return area_by_coef(p["kind"], p["s"], pi)


@template(T, "competent", CI3, CI2)
def shaded_lens(r):
    """math-pat-circle-area-composite-shaded"""
    pi, ps = pick_pi(r)
    s = r.choice(lens_for(ps))
    ask = r.choice(["area", "perimeter"])
    name = nm(r)
    stem = (f"The figure shows a square of side {num(s)} cm. {name} draws two quarter circles, each of radius {num(s)} cm, with centres at two opposite corners. "
            f"Find the {ask} of the shaded part. Take π = {ps}.")
    fig = square_figs("lens", s)
    if ask == "area":
        q = pi * s * s / 4
        ans = 2 * q - s * s
        return build(shaded_lens, stem, ans, [
            (q, "gave_one_quarter_circle", "Gave the area of one quarter circle."),
            (2 * q, "did_not_take_away_the_square", "Added the two quarter circles and did not take away the square."),
            (s * s - q, "square_minus_one_quarter", "Took one quarter circle from the square."),
            (q - s * s / 2 if q > s * s / 2 else None, "wrong_overlap", "Took away half the square."),
            (ans + 4, "slip_in_working", "Made a slip in the working.")],
            [f"Two quarter circles = 2 × {num(q)} = {num(2 * q)} cm²", "They cover the square once and the shaded part twice.", f"Shaded = {num(2 * q)} - {s * s} = {num(ans)} cm²"],
            {"kind": "lens", "s": s, "pi": ps, "ask": ask}, U("cm²"), auto_slips=False, figure=fig)
    arc = pi * s / 2
    ans = 2 * arc
    return build(shaded_lens, stem, ans, [
        (arc, "gave_one_arc", "Gave one curved line only."),
        (ans + 2 * s, "added_the_sides", "Added the sides of the square."),
        (arc + 2 * s, "added_two_sides", "Added one arc and two sides."),
        (pi * s * s / 4 * 2, "used_area", "Used the area formula."),
        (ans + 3, "slip_in_working", "Made a slip in the working.")],
        [f"Each arc is a quarter of a circle of radius {num(s)} cm: {num(arc)} cm", f"Perimeter = 2 × {num(arc)} = {num(ans)} cm"],
        {"kind": "lens", "s": s, "pi": ps, "ask": ask}, U("cm"), auto_slips=False, figure=fig)


@checker(shaded_lens)
def _(p):
    pi = dict((s, v) for v, s in PIS)[p["pi"]]
    if p["ask"] == "area":
        return area_by_coef("lens", p["s"], pi)
    return (pi * 2 * p["s"] / 4) * 2


@template(T, "competent", CI3)
def semis_area(r):
    """math-pat-circle-area-composite-shaded"""
    pi, ps = pick_pi(r)
    a, b = semi_ab(r, ps)
    D = a + b
    name = nm(r)
    ans = pi * (D * D - a * a - b * b) / 8
    stem = (f"The figure shows a large semicircle of diameter {num(D)} cm with two smaller semicircles of diameters {num(a)} cm and {num(b)} cm cut out of it. "
            f"{name} finds the area of the shaded part. Take π = {ps}.")
    big = pi * D * D / 8
    return build(semis_area, stem, ans, [
        (big, "gave_the_big_semicircle", "Gave the area of the big semicircle."),
        (pi * (a * a + b * b) / 8, "gave_the_small_ones", "Gave the area of the two small semicircles."),
        (big - pi * (a + b) ** 2 / 16 if False else big - pi * D * D / 16, "took_away_wrong_amount", "Took away half of the big semicircle."),
        (pi * (D - a - b) ** 2 / 8 + big - big if False else pi * (D * D - a * a) / 8, "left_out_one_small_semicircle", "Took away only one small semicircle."),
        (ans + 3, "slip_in_working", "Made a slip in the working.")],
        [f"Big semicircle = 1/2 × π × {num(F(D, 2))} × {num(F(D, 2))} = {num(big)} cm²", f"Small ones = {num(pi * (a * a + b * b) / 8)} cm²", f"Shaded = {num(ans)} cm²"],
        {"a": a, "b": b, "pi": ps}, U("cm²"), auto_slips=False, figure=fig_semis(a, b))


@checker(semis_area)
def _(p):
    pi = dict((s, v) for v, s in PIS)[p["pi"]]
    a, b = F(p["a"]), F(p["b"])
    est = 0
    D = a + b
    n = 90
    pred = lambda x, y: y >= 0 and (x - D / 2) ** 2 + y * y <= (D / 2) ** 2 and (x - a / 2) ** 2 + y * y > (a / 2) ** 2 and (x - a - b / 2) ** 2 + y * y > (b / 2) ** 2
    cnt = sum(1 for i in range(n) for j in range(n) if pred(float((i + .5) * D / n), float((j + .5) * (D / 2) / n)))
    est = cnt / (n * n) * float(D) * float(D) / 2
    exact_real = float(D * D - a * a - b * b) * PI_REAL / 8
    if abs(est - exact_real) > 0.03 * exact_real:
        return None
    return pi * (a * b) / 4


@template(T, "competent", CI1, CI3)
def wheel_revolutions(r):
    """math-pat-circumference-in-context"""
    ps = "22/7"
    pi = F(22, 7)
    d = r.choice([14, 21, 28, 35, 42, 56, 70, 84])
    circ = pi * d
    name = nm(r)
    obj = r.choice(["bicycle wheel", "trolley wheel", "scooter wheel", "wheelchair wheel"])
    if r.random() < 0.5:
        n = r.choice([20, 25, 40, 50, 60, 80, 100, 120])
        dist = n * circ / 100
        stem = (f"The diameter of {name}'s {obj} is {d} cm. How far, in metres, does the wheel travel when it makes {n} complete turns? Take π = 22/7.")
        return build(wheel_revolutions, stem, dist, [
            (n * pi * F(d, 2) / 100, "used_the_radius", "Used the radius instead of the diameter."),
            (n * circ, "did_not_change_to_metres", "Gave the distance in cm."),
            (n * circ / 1000, "wrong_conversion_factor", "Divided by 1000 instead of 100."),
            (n * d / 100, "forgot_pi", "Forgot to multiply by π."),
            (dist + 2, "slip_in_working", "Made a slip in the working.")],
            [f"One turn = π × {d} = {num(circ)} cm", f"{n} turns = {n} × {num(circ)} = {num(n * circ)} cm", f"= {num(dist)} m"],
            {"mode": "dist", "d": d, "n": n}, U("m"), auto_slips=False)
    n = r.choice([50, 100, 200, 250, 400, 500, 800, 1000])
    dist = n * circ / 100
    if dist.denominator != 1:
        return None
    stem = (f"The diameter of {name}'s {obj} is {d} cm. How many complete turns does the wheel make when it travels {num(dist)} m? Take π = 22/7.")
    return build(wheel_revolutions, stem, n, [
        (2 * n, "used_the_radius", "Used the radius instead of the diameter."),
        (n * 100, "did_not_change_to_cm", "Did not change metres to centimetres."),
        (int(dist * 100 / d), "forgot_pi", "Divided by the diameter and forgot π."),
        (n // 10 if n % 10 == 0 else n + 10, "wrong_conversion_factor", "Used 1 m = 1000 cm."),
        (n + 10, "slip_in_working", "Made a slip in the working.")],
        [f"One turn = {num(circ)} cm", f"{num(dist)} m = {num(dist * 100)} cm", f"Number of turns = {num(dist * 100)} ÷ {num(circ)} = {n}"],
        {"mode": "turns", "d": d, "dist": str(dist)}, lambda v: f"{num(v)} turns", whole=True, auto_slips=False)


@checker(wheel_revolutions)
def _(p):
    pi = F(22, 7)
    circ = 2 * pi * F(p["d"], 2)
    if p["mode"] == "dist":
        return F(sum(circ for _ in range(p["n"])), 100)
    D, n = F(p["dist"]) * 100, 0
    while D > 0:
        D -= circ
        n += 1
    return F(n)


@template(T, "competent", CI1, CI3)
def loops_around(r):
    """math-pat-circumference-in-context"""
    name = nm(r)
    if r.random() < 0.5:
        pi = F(22, 7)
        rad = r.choice([7, 14, 21, 28, 35, 42])
        k = r.choice([3, 4, 5, 6, 8, 10])
        C = 2 * pi * rad
        dist = k * C
        stem = (f"{name} runs {k} complete laps around a circular field of radius {rad} m. How far does {name} run, in metres? Take π = 22/7.")
        return build(loops_around, stem, dist, [
            (k * pi * rad, "forgot_the_2", "Used π × r instead of 2 × π × r."),
            (k * pi * rad * rad, "used_the_area", "Used the area formula."),
            (C, "gave_one_lap", "Gave the distance for one lap only."),
            (k * pi * 2 * rad * 2, "used_the_diameter_wrongly", "Doubled the diameter."),
            (dist + 10, "slip_in_working", "Made a slip in the working.")],
            [f"One lap = 2 × π × {rad} = {num(C)} m", f"{k} laps = {k} × {num(C)} = {num(dist)} m"],
            {"mode": "laps", "r": rad, "k": k, "pi": "22/7"}, U("m"), auto_slips=False)
    pi = F(314, 100)
    d = r.choice([4, 5, 6, 8, 10, 12])
    k = r.randint(3, 9)
    C = pi * d
    ln = k * C
    obj = r.choice(["tin", "pipe", "drum", "round cake tin"])
    stem = (f"{name} winds a string {k} times exactly around a {obj} of diameter {d} cm, with no overlap and no spare string. "
            f"How long is the string, in cm? Take π = 3.14.")
    return build(loops_around, stem, ln, [
        (k * pi * F(d, 2), "used_the_radius", "Used the radius instead of the diameter."),
        (C, "gave_one_turn", "Gave the length for one turn only."),
        (k * pi * d * d / 4, "used_the_area", "Used the area formula."),
        (k * d, "forgot_pi", "Forgot to multiply by π."),
        (ln + 2, "slip_in_working", "Made a slip in the working.")],
        [f"One turn = π × {d} = {num(C)} cm", f"{k} turns = {num(ln)} cm"], {"mode": "string", "d": d, "k": k, "pi": "3.14"}, U("cm"), auto_slips=False)


@checker(loops_around)
def _(p):
    pi = dict((s, v) for v, s in PIS)[p["pi"]]
    if p["mode"] == "laps":
        return sum(2 * pi * p["r"] for _ in range(p["k"]))
    return sum(pi * p["d"] for _ in range(p["k"]))


def fig_pond(rad, w):
    R = rad + w
    u = UF(-R, -R, R, R, mx=56, my=26, maxscale=10)
    pb = PB(u).m(-R, 0).a(R, R, 0, 1).a(R, -R, 0, 1).z().m(-rad, 0).a(rad, rad, 0, 0).a(rad, -rad, 0, 0).z()
    u.path(pb, shade=0.2)
    u.dot((0, 0))
    u.seg((0, 0), (rad, 0), width=1.8)
    u.seg_label((0, 0), (rad, 0), f"{num(rad)} m", (0, R), size=12)
    u.seg((-R, 0), (-rad, 0), width=2.4)
    u.text((-R, 0), f"{num(w)} m", dx=-6, anchor="end", size=12)
    return u.svg("Pond with path")


@template(T, "competent", CI3, CI1)
def pond_path(r):
    """math-pat-circle-area-composite-shaded"""
    pi, ps = pick_pi(r)
    if ps == "22/7":
        rad, w = r.choice([7, 14]), r.choice([F(7, 2), 7])
    else:
        rad, w = r.choice([4, 5, 6, 8]), r.choice([2, 3, 4])
    R = rad + w
    ans = pi * (R * R - rad * rad)
    name = nm(r)
    stem = (f"The figure shows a circular pond of radius {num(rad)} m with a path {num(w)} m wide all the way round it. "
            f"{name} wants to know the area of the path (the shaded part). Take π = {ps}.")
    return build(pond_path, stem, ans, [
        (pi * R * R, "gave_the_outer_circle", "Gave the area of the pond and path together."),
        (pi * w * w, "squared_the_width", "Used the width of the path as a radius."),
        (pi * (R - rad) * (R - rad) + 0 if False else 2 * pi * rad * w, "used_the_circumference", "Found the circumference times the width."),
        (pi * rad * rad, "gave_the_pond", "Gave the area of the pond."),
        (ans + 5, "slip_in_working", "Made a slip in the working.")],
        [f"Radius of pond and path = {num(rad)} + {num(w)} = {num(R)} m", f"Area of path = π × {num(R)} × {num(R)} - π × {num(rad)} × {num(rad)}", f"= {num(ans)} m²"],
        {"r": str(rad), "w": str(w), "pi": ps}, U("m²"), auto_slips=False, figure=fig_pond(rad, w))


@checker(pond_path)
def _(p):
    pi = dict((s, v) for v, s in PIS)[p["pi"]]
    rad, w = F(p["r"]), F(p["w"])
    return pi * w * (2 * rad + w)


# ---------------------------------------------------------------- intermediate: arcs on squares

@template(T, "intermediate", CI3, CI2)
def square_arc_perimeter(r):
    """math-pat-circle-perimeter-composite"""
    kind = r.choice(["quarter_sq", "semi_sq", "four_quarters"])
    pi, ps = pick_pi(r)
    s = r.choice(lens_for(ps, half=(kind != "quarter_sq")))
    name = nm(r)
    text = KIND_TEXT[kind].format(s=num(s))
    stem = f"{text} Find the perimeter of the shaded part. Take π = {ps}. ({name}'s design)"
    if kind == "quarter_sq":
        ans = 2 * s + pi * s / 2
        wrong = [(4 * s + pi * s / 2, "counted_all_four_sides", "Counted all four sides."), (2 * s + pi * s, "used_a_semicircle_arc", "Used half the circumference."),
                 (pi * s / 2, "left_out_the_straight_sides", "Found the curved part only."), (4 * s, "left_out_the_arc", "Gave the perimeter of the square."),
                 (ans + 2, "slip_in_working", "Made a slip in the working.")]
        steps = [f"Curved part = 1/4 × 2 × π × {num(s)} = {num(pi * s / 2)} cm", f"Two straight sides = {2 * s} cm", f"Perimeter = {num(ans)} cm"]
    elif kind == "semi_sq":
        ans = 3 * s + pi * s / 2
        wrong = [(4 * s + pi * s / 2, "counted_all_four_sides", "Counted the side that the semicircle replaces."), (3 * s + pi * s, "used_the_full_circle", "Used the whole circumference."),
                 (pi * s / 2, "left_out_the_straight_sides", "Found the curved part only."), (3 * s, "left_out_the_arc", "Left out the curved part."),
                 (ans + 2, "slip_in_working", "Made a slip in the working.")]
        steps = [f"Curved part = 1/2 × π × {num(s)} = {num(pi * s / 2)} cm", f"Three straight sides = {3 * s} cm", f"Perimeter = {num(ans)} cm"]
    else:
        ans = pi * s
        wrong = [(4 * s, "gave_the_perimeter_of_the_square", "Gave the perimeter of the square."), (4 * s + pi * s, "added_the_sides", "Added the sides of the square."),
                 (pi * s / 2, "used_half_the_arcs", "Counted two of the four arcs."), (pi * s * 2, "doubled", "Doubled the answer."),
                 (ans + 2, "slip_in_working", "Made a slip in the working.")]
        steps = [f"The four quarter circles make one circle of radius {num(F(s, 2))} cm", f"Perimeter = π × {num(s)} = {num(ans)} cm"]
    return build(square_arc_perimeter, stem, ans, wrong, steps, {"kind": kind, "s": s, "pi": ps}, U("cm"), auto_slips=False, figure=square_figs(kind, s))


@checker(square_arc_perimeter)
def _(p):
    pi = dict((s, v) for v, s in PIS)[p["pi"]]
    s = F(p["s"])
    return {"quarter_sq": s + s + (2 * pi * s) / 4, "semi_sq": s + s + s + (2 * pi * (s / 2)) / 2,
            "four_quarters": 4 * ((2 * pi * (s / 2)) / 4)}[p["kind"]]


# ================================================================ Group C gap fills: isometric drawings of cubes and cuboids
from figures_D import stack_fig, panels  # noqa: E402
from figures_gapC import iso_fig  # noqa: E402

VC3 = VC_ + "03"


def _heights(r, ni, nj, top):
    """Random stack heights, non-increasing in i and j (so the isometric picture is valid), tallest = top."""
    h = [[0] * nj for _ in range(ni)]
    for i in range(ni):
        for j in range(nj):
            cap = min(top, h[i - 1][j] if i else top, h[i][j - 1] if j else top)
            h[i][j] = r.randint(1, cap)
    h[0][0] = top
    return h


def _visible(h):
    ni, nj = len(h), len(h[0])
    have = {(i, j, k) for i in range(ni) for j in range(nj) for k in range(h[i][j])}
    return sum(1 for (i, j, k) in have if (i, j, k + 1) not in have or (i + 1, j, k) not in have or (i, j + 1, k) not in have)


def _total(h):
    return sum(sum(row) for row in h)


@template(T, "basic", VC3)
def iso_count_cubes(r):
    """Count the unit cubes in an isometric drawing (hidden ones included)."""
    name = nm(r)
    ni, nj, top = r.choice([2, 3]), r.choice([2, 3]), r.choice([2, 3])
    h = _heights(r, ni, nj, top)
    tot, vis = _total(h), _visible(h)
    if vis >= tot or tot < 5:
        return None
    ctx = r.choice(["builds this solid from 1-cm cubes", "stacks 1-cm cubes to make this solid",
                    "glues 1-cm cubes together to make this solid"])
    stem = (f"{name} {ctx}. The base is {ni} cubes by {nj} cubes. There are no gaps inside, "
            f"and some cubes cannot be seen. How many cubes did {name} use?")
    return build(iso_count_cubes, stem, tot, [
        (vis, "counted_only_visible_cubes", "Counted only the cubes that can be seen and left out the hidden ones."),
        (ni * nj * top, "assumed_a_full_cuboid", "Assumed every stack is as tall as the tallest one."),
        (tot + 1, "miscounted_one_cube", "Counted one cube too many."),
        (tot - 1, "miscounted_one_cube", "Counted one cube too few."),
    ], ["Count the cubes stack by stack, including the ones hidden behind.", " + ".join(str(x) for row in h for x in row) + f" = {tot}"],
        {"h": h}, str, whole=True, auto_slips=False, figure=stack_fig(h))


@checker(iso_count_cubes)
def _(p):
    n = 0
    for i, row in enumerate(p["h"]):
        for j, hh in enumerate(row):
            for _k in range(hh):
                n += 1
    return F(n)


@template(T, "intermediate", VC3)
def iso_which_cuboid(r):
    """Which isometric drawing (A-D) shows a cuboid with the given base and number of layers."""
    name = nm(r)
    a, b, h = r.randint(2, 4), r.randint(2, 4), r.randint(2, 4)
    if a == b == h:
        return None
    vol = a * b * h
    decoys = [((a, b, h + 1) if h < 4 else (a, b, h - 1), "miscounted_layers", "Counted one layer too many or too few."),
              ((a + 1, b, h) if a < 4 else (a - 1, b, h), "miscounted_base_length", "Miscounted the length of the base by one cube."),
              ((a, b + 1, h) if b < 4 else (a, b - 1, h), "miscounted_base_width", "Miscounted the width of the base by one cube."),
              ((a, b, h + 2) if h < 3 else (a, b, h - 2), "miscounted_layers", "Counted two layers too many or too few.")]
    seen, outs = {(tuple(sorted((a, b))), h)}, []
    for dims, tag, why in decoys:
        key = (tuple(sorted(dims[:2])), dims[2])
        if key in seen or min(dims) < 1 or max(dims) > 5:
            continue
        seen.add(key)
        outs.append((dims, tag, why))
    if len(outs) < 3:
        return None
    outs = outs[:3]
    pos = r.randrange(4)
    allv = [o[0] for o in outs]
    ca, cb = (a, b) if r.random() < 0.5 else (b, a)
    allv.insert(pos, (ca, cb, h))
    figs = [iso_fig([[d[2]] * d[1] for _ in range(d[0])], W=150, H=140) for d in allv]
    wrong = [(i + 1, tag, why) for i, (_, tag, why) in zip([x for x in range(4) if x != pos], outs)]
    stem = (f"{name} stacks unit cubes to make a cuboid. Its base is {a} cubes by {b} cubes and it is {h} layers high. "
            f"Which drawing shows {name}'s cuboid?")
    return build(iso_which_cuboid, stem, pos + 1, wrong,
                 [f"The cuboid has {a} x {b} cubes in each layer and {h} layers.", f"Its volume is {vol} cubes.",
                  f"Only drawing {'ABCD'[pos]} has a {a} by {b} base and {h} layers."],
                 {"a": a, "b": b, "h": h, "opts": [list(d) for d in allv]}, lambda v: "ABCD"[int(v) - 1], whole=True,
                 auto_slips=False, figure=panels(figs, "ABCD", cols=2, title="Four isometric drawings"))


@checker(iso_which_cuboid)
def _(p):
    ok = [i + 1 for i, (x, y, z) in enumerate(p["opts"]) if z == p["h"] and sorted((x, y)) == sorted((p["a"], p["b"]))]
    return F(ok[0]) if len(ok) == 1 else None


@template(T, "competent", VC3)
def iso_cubes_to_complete(r):
    """How many more cubes are needed to complete the box around an isometric stack."""
    name = nm(r)
    ni, nj, top = r.choice([2, 3]), r.choice([2, 3]), r.choice([2, 3])
    h = _heights(r, ni, nj, top)
    tot, vis = _total(h), _visible(h)
    box = ni * nj * top
    ans = box - tot
    if ans < 1 or vis >= tot or box - vis == ans:
        return None
    ctx = r.choice(["has built the solid shown", "made the solid shown", "stuck cubes together to make the solid shown"])
    stem = (f"{name} {ctx} using 1-cm cubes (there are no gaps inside). {name} wants to add cubes to make a complete "
            f"cuboid with the same {ni} by {nj} base and the same height as the tallest part. How many more cubes does {name} need?")
    return build(iso_cubes_to_complete, stem, ans, [
        (box - vis, "forgot_the_hidden_cubes", "Counted only the cubes you can see in the solid."),
        (tot, "gave_the_cubes_already_used", "Gave the number of cubes already in the solid."),
        (box, "gave_the_cuboid_volume", "Gave the number of cubes in the complete cuboid."),
        (ans + 1, "miscounted_one_cube", "Was one cube out."),
        (ans - 1, "miscounted_one_cube", "Was one cube out."),
    ], [f"Complete cuboid: {ni} x {nj} x {top} = {box} cubes.", f"Cubes in the solid: {tot}.", f"{box} - {tot} = {ans}"],
        {"h": h, "ni": ni, "nj": nj, "top": top}, str, whole=True, auto_slips=False, figure=stack_fig(h))


@checker(iso_cubes_to_complete)
def _(p):
    missing = 0
    for i in range(p["ni"]):
        for j in range(p["nj"]):
            for k in range(p["top"]):
                if k >= p["h"][i][j]:
                    missing += 1
    return F(missing)


@template(T, "competent", VC3)
def iso_cuboid_volume_edge(r):
    """Volume (cm3) of a cuboid shown in an isometric drawing, each cube having an edge of s cm."""
    name = nm(r)
    a, b, hh = r.randint(2, 4), r.randint(2, 4), r.randint(2, 3)
    s = r.choice([2, 3, 4])
    n = a * b * hh
    ans = n * s ** 3
    ctx = r.choice(["made this cuboid", "built this cuboid", "stacked these cubes into this cuboid"])
    stem = (f"{name} {ctx} using identical cubes. Each cube has an edge of {s} cm. "
            f"What is the volume of the cuboid, in cm³?")
    return build(iso_cuboid_volume_edge, stem, ans, [
        (n, "gave_the_number_of_cubes", "Counted the cubes but did not find the volume of each cube."),
        (n * s, "used_edge_instead_of_cube_volume", f"Multiplied the number of cubes by {s} instead of {s} x {s} x {s}."),
        (n * s * s, "used_face_area_of_a_cube", "Used the area of a face instead of the volume of a cube."),
        (ans + s ** 3, "miscounted_one_cube", "Counted one cube too many."),
        (ans - s ** 3, "miscounted_one_cube", "Counted one cube too few."),
    ], [f"Number of cubes = {a} x {b} x {hh} = {n}.", f"Volume of one cube = {s} x {s} x {s} = {s ** 3} cm³.", f"{n} x {s ** 3} = {ans} cm³"],
        {"a": a, "b": b, "h": hh, "s": s}, lambda v: f"{int(v)} cm³", whole=True, auto_slips=False,
        figure=stack_fig([[hh] * b for _ in range(a)]))


@checker(iso_cuboid_volume_edge)
def _(p):
    total = 0
    for _i in range(p["a"]):
        for _j in range(p["b"]):
            for _k in range(p["h"]):
                total += p["s"] ** 3
    return F(total)
