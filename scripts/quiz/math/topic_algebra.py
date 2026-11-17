"""Algebra (math-algebra): generators for basic, intermediate and competent levels.

Answers that are expressions (3n + 5) are encoded as a stable integer code per text so that the
distinctness checks in build() and check_math.py work; show() turns the code back into text.
"""
import hashlib

from common import *
from figures_b import rectangle_labels, triangle_labels

T = "math-algebra"
O = "math-algebra-algebra-"
LETTER, NOTATION, SIMPLIFY, SUBST, EQUATION = (O + f"0{i}" for i in range(1, 6))

DISP = {}


def code(text):
    c = int(hashlib.sha1(text.encode()).hexdigest()[:8], 16) % 900000 + 1
    assert DISP.get(c, text) == text, "code collision"
    DISP[c] = text
    return c


def show(v):
    return DISP[int(v)]


def E(text):
    return (text, code(text))


def lin(a, b, v="n"):
    """a*v + b as text: 3n + 5, n - 2, 5 - 2n, 7."""
    a, b = F(a), F(b)
    if a.denominator != 1:
        assert b == 0
        return f"{v} ÷ {a.denominator}" if a.numerator == 1 else f"{a.numerator}{v} ÷ {a.denominator}"
    a, b = int(a), int(b)
    if a == 0:
        return str(b)
    t = lambda k: v if k == 1 else f"{k}{v}"
    if a > 0:
        return t(a) + ("" if b == 0 else f" + {b}" if b > 0 else f" - {-b}")
    return f"-{t(-a)}" if b == 0 else f"{b} - {t(-a)}" if b > 0 else f"-{t(-a)} - {-b}"


def terms_text(terms):
    """terms: list of (coef, var-or-None) with signed coefficients."""
    out = ""
    for i, (c, v) in enumerate(terms):
        body = (str(abs(c)) if v is None else (v if abs(c) == 1 else f"{abs(c)}{v}"))
        if i == 0:
            out += ("-" if c < 0 else "") + body
        else:
            out += (" - " if c < 0 else " + ") + body
    return out


def brute(pred, hi=20000):
    return next((F(n) for n in range(1, hi + 1) if pred(n)), None)


def slipn(v, d=1):
    return [(v + d, "careless_slip", "Made a slip in the calculation."),
            (v - d, "careless_slip", "Made a slip in the calculation.")]


def ex(a, b, v="n"):
    return E(lin(a, b, v))


LETTERS = ["n", "a", "k", "p", "x", "m"]
THINGS = ["stickers", "marbles", "sweets", "stamps", "cards", "beads", "pencils"]


# ---------------------------------------------------------------- basic

def _ctx_sim(kind, k):
    return {"more": lambda n: n + k, "fewer": lambda n: n - k, "times": lambda n: k * n,
            "share": lambda n: F(n, k)}[kind]


@template(T, "basic", LETTER, NOTATION)
def letter_context(r):
    kind = r.choice(["more", "fewer", "times", "share"])
    k = r.randint(2, 9)
    v = r.choice(LETTERS)
    th = r.choice(THINGS)
    x, y = two_names(r)
    if kind == "more":
        stem = f"{x} has {v} {th}. {y} has {k} more {th} than {x}. How many {th} does {y} have?"
        wr = [E(f"{v} - {k}"), E(f"{k}{v}"), E(f"{k} - {v}"), E(f"{v}{k}")]
        tags = ["subtracted_instead_of_added", "multiplied_instead_of_added", "reversed_the_subtraction", "wrote_digits_together"]
    elif kind == "fewer":
        stem = f"{x} has {v} {th}. {y} has {k} fewer {th} than {x}. How many {th} does {y} have?"
        wr = [E(f"{v} + {k}"), E(f"{k}{v}"), E(f"{k} - {v}"), E(f"{v}{k}")]
        tags = ["added_instead_of_subtracted", "multiplied_instead_of_subtracted", "reversed_the_subtraction", "wrote_digits_together"]
    elif kind == "times":
        stem = f"{x} has {v} {th}. {y} has {k} times as many {th} as {x}. How many {th} does {y} have?"
        wr = [E(f"{v} + {k}"), E(f"{v} ÷ {k}"), E(f"{v} - {k}"), E(f"{v}{k}")]
        tags = ["added_instead_of_multiplied", "divided_instead_of_multiplied", "subtracted_instead_of_multiplied", "wrote_digits_together"]
    else:
        stem = f"{x} shares {v} {th} equally among {k} children. How many {th} does each child get?"
        wr = [E(f"{k}{v}"), E(f"{v} - {k}"), E(f"{k} ÷ {v}"), E(f"{v} + {k}")]
        tags = ["multiplied_instead_of_divided", "subtracted_instead_of_divided", "reversed_the_division", "added_instead_of_divided"]
    ans = {"more": ex(1, k, v), "fewer": ex(1, -k, v), "times": ex(k, 0, v), "share": (f"{v} ÷ {k}", code(f"{v} ÷ {k}"))}[kind]
    wrong = [(w, t, f"Wrote {w[0]}: {t.replace('_', ' ')}.") for w, t in zip(wr, tags)]
    return build(letter_context, stem, ans[1], wrong,
                 [f"Let the number of {th} be {v}.", f"The answer is {ans[0]}."],
                 {"kind": kind, "k": k, "v": v}, show, auto_slips=False)


@checker(letter_context)
def _(q):
    f = _ctx_sim(q["kind"], q["k"])
    b = f(0)
    a = f(1) - f(0)
    return F(code(lin(a, b, q["v"])))


@template(T, "basic", SIMPLIFY)
def simplify_basic(r):
    """math-pat-algebra-simplify-substitute"""
    a1, a2 = r.randint(2, 9), r.randint(1, 8)
    s = r.choice([1, -1])
    if s == -1 and a2 >= a1:
        return None
    c = r.choice([x for x in range(-9, 10) if x])
    v = r.choice(LETTERS)
    order = r.choice([0, 1])
    ts = [(a1, v), (c, None), (s * a2, v)] if order == 0 else [(c, None), (a1, v), (s * a2, v)]
    if order == 1 and c < 0:
        ts = [(a1, v), (s * a2, v), (c, None)]
    stem = f"Simplify {terms_text(ts)}."
    a = a1 + s * a2
    ans = ex(a, c, v)
    wrong = [
        (E(f"{a + c}{v}") if a + c > 0 else None, "combined_unlike_terms", "Added the number to the letter terms."),
        (ex(a, -c, v), "sign_error_on_constant", "Changed the sign of the number."),
        (ex(a1 + a2 if s == -1 else abs(a1 - a2) or 1, c, v), "wrong_operation_on_letter_terms",
         "Added the letter terms when they should be subtracted." if s == -1 else "Subtracted the letter terms."),
        *[((lin(a, c + d, v), code(lin(a, c + d, v))), t, w) for (_, t, w), d in zip(slipn(0), (1, -1))],
    ]
    return build(simplify_basic, stem, ans[1], [(w, t, wh) for w, t, wh in wrong if w is not None],
                 [f"Add or subtract the {v} terms: {a1}{v} {'+' if s == 1 else '-'} {a2}{v} = {lin(a, 0, v)}", f"Keep the number: {lin(a, c, v)}"],
                 {"a1": a1, "a2": a2, "s": s, "c": c, "v": v}, show, auto_slips=False)


@checker(simplify_basic)
def _(q):
    e = lambda x: q["a1"] * x + q["c"] + q["s"] * q["a2"] * x
    return F(code(lin(e(1) - e(0), e(0), q["v"])))


@template(T, "basic", SUBST)
def substitute_basic(r):
    """math-pat-algebra-simplify-substitute"""
    a, xv = r.randint(2, 9), r.randint(2, 9)
    b = r.choice([x for x in range(-9, 10) if x])
    v = r.choice(LETTERS)
    if a * xv + b <= 0:
        return None
    stem = f"Find the value of {lin(a, b, v)} when {v} = {xv}."
    ans = a * xv + b
    return build(substitute_basic, stem, ans, [
        (int(f"{a}{xv}") + b, "wrote_digits_together", f"Read {a}{v} as {a}{xv}."),
        (a + xv + b, "added_instead_of_multiplied", f"Added {a} and {xv} instead of multiplying."),
        (a * xv - b, "sign_error_on_constant", "Changed the sign of the number."),
        (a * (xv + b) if a * (xv + b) > 0 else None, "multiplied_the_constant", f"Multiplied {a} by ({xv} {'+' if b > 0 else '−'} {abs(b)})."),
        *slipn(ans, 1), *slipn(ans, a),
    ], [f"{lin(a, b, v)} = {a} × {xv} {'+' if b > 0 else '−'} {abs(b)}", f"= {a * xv} {'+' if b > 0 else '−'} {abs(b)} = {ans}"],
        {"a": a, "b": b, "x": xv}, auto_slips=False, whole=True)


@checker(substitute_basic)
def _(q):
    return F(sum(q["a"] for _ in range(q["x"])) + q["b"])


@template(T, "basic", EQUATION)
def solve_basic(r):
    kind = r.choice(["add", "sub", "mul", "div"])
    x = r.randint(2, 30)
    k = r.randint(2, 12)
    v = r.choice(LETTERS)
    nm = r.choice(NAMES)
    if kind == "add":
        m = x + k
        stem = r.choice([f"Solve {v} + {k} = {m}.", f"{nm} thinks of a number, {v}. When {k} is added to it, the result is {m}. Find {v}."])
        wrong = [(m + k, "added_instead_of_subtracted", f"Added {k} to {m}."), (k * m, "multiplied", f"Multiplied {k} by {m}."),
                 (m - k + 1 if False else k, "gave_the_constant", f"Gave {k}.")]
    elif kind == "sub":
        m = x - k
        if m <= 0:
            return None
        stem = r.choice([f"Solve {v} - {k} = {m}.", f"{nm} thinks of a number, {v}. When {k} is taken away from it, the result is {m}. Find {v}."])
        wrong = [(m - k if m > k else None, "subtracted_instead_of_added", f"Subtracted {k} from {m}."), (k * m, "multiplied", f"Multiplied {k} by {m}."),
                 (k, "gave_the_constant", f"Gave {k}.")]
    elif kind == "mul":
        m = k * x
        stem = r.choice([f"Solve {k}{v} = {m}.", f"{nm} buys {k} identical pens for ${m}. The price of one pen is ${v}. Find {v}."])
        wrong = [(m - k, "subtracted_instead_of_divided", f"Subtracted {k} from {m}."), (m * k, "multiplied_instead_of_divided", f"Multiplied {m} by {k}."),
                 (m + k, "added_instead_of_divided", f"Added {m} and {k}.")]
    else:
        m = x
        n0 = k * m
        stem = r.choice([f"Solve {v} ÷ {k} = {m}.", f"{nm} shares some sweets equally among {k} friends and each friend gets {m} sweets. How many sweets, {v}, did {nm} have?"])
        wrong = [(F(n0, k * k) if n0 % (k * k) == 0 else m // k if m % k == 0 and m // k else None, "divided_again", f"Divided {m} by {k}."),
                 (m + k, "added", f"Added {m} and {k}."), (m - k if m > k else None, "subtracted", f"Subtracted {k} from {m}.")]
        x = n0
    return build(solve_basic, stem, x, wrong + slipn(x, 1) + slipn(x, 2),
                 [f"Do the opposite operation to both sides, giving {v} = {x}."], {"kind": kind, "k": k, "m": m},
                 auto_slips=False, whole=True)


@checker(solve_basic)
def _(q):
    k, m = q["k"], q["m"]
    f = {"add": lambda x: x + k == m, "sub": lambda x: x - k == m, "mul": lambda x: k * x == m, "div": lambda x: F(x, k) == m}[q["kind"]]
    return brute(f, 5000)


# ---------------------------------------------------------------- intermediate

@template(T, "intermediate", LETTER, NOTATION)
def expression_two_events(r):
    """math-pat-algebra-expression-from-context"""
    a, c = r.randint(2, 8), r.randint(1, 6)
    if a <= c:
        return None
    b, d = r.randint(1, 9), r.randint(2, 9)
    buy = r.random() < 0.6
    x, y = two_names(r)
    th = r.choice(THINGS)
    v = r.choice(["n", "k", "p"])
    ev = f"then {'bought' if buy else 'lost'} {d} {'more ' if buy else ''}{th}"
    stem = (f"{x} had ({lin(a, b, v)}) {th}. {x} gave {lin(c, 0, v)} {th} to {y} and {ev}. "
            f"Express the number of {th} {x} has now in terms of {v}.")
    ans = ex(a - c, b + d if buy else b - d, v)
    wrong = [
        (ex(a + c, b + d if buy else b - d, v), "added_the_given_away_amount", f"Added {lin(c, 0, v)} instead of subtracting it."),
        (ex(a - c, b - d if buy else b + d, v), "sign_error_on_constant", f"{'Subtracted' if buy else 'Added'} the {d}."),
        (E(f"{a - c + b + (d if buy else -d)}{v}") if a - c + b + (d if buy else -d) > 0 else None, "combined_unlike_terms", "Added the number to the letter terms."),
        (ex(a - c, (b + d if buy else b - d) + 1, v), "careless_slip", "Made a slip in the calculation."),
        (ex(a - c, (b + d if buy else b - d) - 1, v), "careless_slip", "Made a slip in the calculation."),
    ]
    return build(expression_two_events, stem, ans[1], [w for w in wrong if w[0] is not None],
                 [f"{lin(a, b, v)} − {lin(c, 0, v)} {'+' if buy else '−'} {d}", f"Group like terms: ({a} − {c}){v} + ({b} {'+' if buy else '−'} {d})", f"= {ans[0]}"],
                 {"a": a, "b": b, "c": c, "d": d, "buy": buy, "v": v}, show, auto_slips=False)


@checker(expression_two_events)
def _(q):
    f = lambda n: q["a"] * n + q["b"] - q["c"] * n + (q["d"] if q["buy"] else -q["d"])
    return F(code(lin(f(1) - f(0), f(0), q["v"])))


@template(T, "intermediate", SIMPLIFY)
def simplify_intermediate(r):
    a1, a2 = r.randint(3, 12), r.randint(1, 9)
    if a1 <= a2:
        return None
    b, d = r.randint(1, 9), r.randint(1, 12)
    sb, sd = r.choice([1, -1]), r.choice([1, -1])
    v = r.choice(LETTERS)
    ts = [(a1, v), (sb * b, None), (-a2, v), (sd * d, None)]
    stem = f"Simplify {terms_text(ts)}."
    const = sb * b + sd * d
    if const == 0:
        return None
    ans = ex(a1 - a2, const, v)
    wrong = [
        (ex(a1 + a2, const, v), "added_instead_of_subtracted", f"Added the {v} terms instead of subtracting."),
        (ex(a1 - a2, sb * b - sd * d, v) if sb * b - sd * d != const else ex(a1 - a2, -const, v), "sign_error_on_constant", "Made a sign error with the numbers."),
        (E(f"{a1 - a2 + const}{v}") if a1 - a2 + const > 0 else None, "combined_unlike_terms", "Added the number to the letter terms."),
        (ex(a1 - a2, const + 1, v), "careless_slip", "Made a slip in the calculation."),
        (ex(a1 - a2, const - 1, v), "careless_slip", "Made a slip in the calculation."),
    ]
    return build(simplify_intermediate, stem, ans[1], [w for w in wrong if w[0] is not None],
                 [f"{v} terms: {a1}{v} − {a2}{v} = {a1 - a2}{v}", f"Numbers: {sb * b} {'+' if sd * d > 0 else '−'} {abs(d)} = {const}", f"= {ans[0]}"],
                 {"a1": a1, "a2": a2, "b": sb * b, "d": sd * d, "v": v}, show, auto_slips=False)


@checker(simplify_intermediate)
def _(q):
    e = lambda x: q["a1"] * x + q["b"] - q["a2"] * x + q["d"]
    return F(code(lin(e(1) - e(0), e(0), q["v"])))


def two_text(ca, cb):
    return terms_text([(ca, "a"), (cb, "b")]) if ca else terms_text([(cb, "b")])


@template(T, "intermediate", SIMPLIFY)
def simplify_two_letters(r):
    a1, a2 = r.randint(2, 9), r.randint(1, 9)
    b1, b2 = r.randint(1, 9), r.randint(1, 8)
    s1, s2 = r.choice([1, -1]), r.choice([1, -1])
    ca, cb = a1 + s1 * a2, b1 + s2 * b2
    if ca <= 0 or cb <= 0:
        return None
    terms = [(a1, "a"), (b1, "b"), (s1 * a2, "a"), (s2 * b2, "b")]
    if r.random() < 0.5:
        terms = [terms[1], terms[0], terms[2], terms[3]]
    if terms[0][0] < 0:
        return None
    stem = f"Simplify {terms_text(terms)}."
    ans = E(two_text(ca, cb))
    wrong = [
        (E(f"{ca + cb}ab"), "multiplied_unlike_terms", "Joined a and b into one term."),
        (E(f"{ca + cb}a"), "combined_unlike_terms", "Added all the coefficients as if a and b were the same."),
        (E(two_text(a1 + a2, b1 + b2)), "ignored_the_signs", "Added every coefficient and ignored the minus signs."),
        (E(two_text(ca, cb + 1)), "careless_slip", "Made a slip in the calculation."),
        (E(two_text(ca + 1, cb)), "careless_slip", "Made a slip in the calculation."),
    ]
    return build(simplify_two_letters, stem, ans[1], [w for w in wrong if w[0] != ans],
                 [f"a terms: {a1}a {'+' if s1 > 0 else '−'} {a2}a = {ca}a", f"b terms: {b1}b {'+' if s2 > 0 else '−'} {b2}b = {cb}b", f"= {ans[0]}"],
                 {"terms": [list(t) for t in terms]}, show, auto_slips=False)


@checker(simplify_two_letters)
def _(q):
    def ev(av, bv):
        return sum(c * (av if v == "a" else bv) for c, v in q["terms"])
    return F(code(two_text(ev(1, 0), ev(0, 1))))


@template(T, "intermediate", SUBST)
def substitute_two_letters(r):
    p, qn = r.randint(2, 9), r.randint(2, 9)
    av, bv = r.randint(2, 9), r.randint(2, 9)
    sgn = r.choice([1, -1])
    c = r.randint(1, 12) * r.choice([1, -1])
    val = p * av + sgn * qn * bv + c
    if val <= 0 or av == bv:
        return None
    expr = terms_text([(p, "a"), (sgn * qn, "b"), (c, None)])
    stem = f"Find the value of {expr} when a = {av} and b = {bv}."
    return build(substitute_two_letters, stem, val, [
        (p * bv + sgn * qn * av + c if p * bv + sgn * qn * av + c > 0 else None, "swapped_the_values", f"Used a = {bv} and b = {av}."),
        (p * av + (-sgn) * qn * bv + c if p * av - sgn * qn * bv + c > 0 else None, "sign_error_on_second_term", "Changed the sign of the b term."),
        (p * av + sgn * qn * bv - c if p * av + sgn * qn * bv - c > 0 else None, "sign_error_on_constant", "Changed the sign of the number."),
        (int(f"{p}{av}") + sgn * int(f"{qn}{bv}") + c if int(f"{p}{av}") + sgn * int(f"{qn}{bv}") + c > 0 else None, "wrote_digits_together", "Wrote the digits side by side instead of multiplying."),
        *slipn(val, 1), *slipn(val, 2),
    ], [f"{p} × {av} {'+' if sgn > 0 else '−'} {qn} × {bv} {'+' if c > 0 else '−'} {abs(c)}",
        f"= {p * av} {'+' if sgn > 0 else '−'} {qn * bv} {'+' if c > 0 else '−'} {abs(c)} = {val}"],
        {"p": p, "q": qn, "a": av, "b": bv, "sgn": sgn, "c": c}, whole=True, auto_slips=False)


@checker(substitute_two_letters)
def _(q):
    t = 0
    for _ in range(q["a"]):
        t += q["p"]
    for _ in range(q["b"]):
        t += q["sgn"] * q["q"]
    return F(t + q["c"])


@template(T, "intermediate", EQUATION)
def equation_from_context(r):
    a = r.randint(2, 8)
    x = r.randint(2, 15)
    b = r.randint(2, 20)
    sgn = r.choice([1, -1])
    c = a * x + sgn * b
    if c <= 0:
        return None
    nm = r.choice(NAMES)
    it = r.choice([("notebooks", "notebook", "pen"), ("packets of sweets", "packet", "ruler"), ("bottles of juice", "bottle", "pen")])
    if sgn == 1:
        stem = (f"{nm} bought {a} {it[0]} that cost $m each and a {it[2]} for ${b}. The total cost was ${c}. "
                f"Find the cost of one {it[1]}, $m.")
    else:
        stem = (f"{nm} bought {a} {it[0]} that cost $m each and received ${b} change after paying with a ${c + b + 0} note. "
                f"Find the cost of one {it[1]}, $m.") if False else (
            f"{nm} bought {a} {it[0]} at $m each. After a ${b} discount, {nm} paid ${c} altogether. Find the cost of one {it[1]}, $m.")
    return build(equation_from_context, stem, x, [
        (F(c, a), "forgot_the_other_amount", f"Divided ${c} by {a} and ignored the ${b}."),
        (c - sgn * b, "forgot_to_divide", f"Found ${c} {'−' if sgn == 1 else '+'} ${b} but did not divide by {a}."),
        (F(c + sgn * b, a), "wrong_operation", f"{'Added' if sgn == 1 else 'Subtracted'} ${b} instead of {'subtracting' if sgn == 1 else 'adding'}."),
        *slipn(x, 1), *slipn(x, 2),
    ], [f"{a}m {'+' if sgn == 1 else '−'} {b} = {c}", f"{a}m = {c - sgn * b}", f"m = {x}"], {"a": a, "b": b, "sgn": sgn, "c": c},
        money, auto_slips=False, whole=True)


@checker(equation_from_context)
def _(q):
    return brute(lambda m: q["a"] * m + q["sgn"] * q["b"] == q["c"], 2000)


@template(T, "intermediate", EQUATION, SIMPLIFY)
def equation_from_figure_triangle(r):
    """math-pat-algebra-equation-from-figure"""
    x = r.randint(3, 14)
    a = [r.randint(1, 4) for _ in range(3)]
    b = [r.randint(0, 9), r.randint(0, 9), 0 if r.random() < 0.5 else r.randint(1, 5)]
    sides = [a[i] * x + b[i] for i in range(3)]
    s = sorted(sides)
    if len(set(sides)) < 3 or s[2] >= s[0] + s[1]:
        return None
    P = sum(sides)
    labels = [f"({lin(a[i], b[i], 'x')}) cm" if b[i] else f"{lin(a[i], 0, 'x')} cm" for i in range(3)]
    fig = triangle_labels(*labels)
    A, B = sum(a), sum(b)
    stem = (f"The figure shows a triangle with sides {labels[0]}, {labels[1]} and {labels[2]}. The figure is not drawn to scale. "
            f"The perimeter of the triangle is {P} cm. What is the length of the longest side?")
    return build(equation_from_figure_triangle, stem, s[2], [
        (x, "gave_x", "Gave the value of x, not a side."),
        (s[1], "gave_the_wrong_side", "Gave the second longest side."),
        (P, "gave_the_perimeter", "Gave the perimeter."),
        (s[0], "gave_the_shortest_side", "Gave the shortest side."),
        *slipn(s[2], 1), *slipn(s[2], 2),
    ], [f"Perimeter: {lin(A, B, 'x')} = {P}", f"{A}x = {P - B}", f"x = {x}", f"The sides are {sides[0]} cm, {sides[1]} cm and {sides[2]} cm.",
        f"The longest side is {s[2]} cm."], {"a": a, "b": b, "P": P}, unit("cm"), auto_slips=False, whole=True, figure=fig)


@checker(equation_from_figure_triangle)
def _(q):
    for x in range(1, 500):
        sides = [q["a"][i] * x + q["b"][i] for i in range(3)]
        if sum(sides) == q["P"]:
            return F(max(sides))


@template(T, "intermediate", EQUATION)
def equation_both_sides(r):
    c = r.randint(1, 4)
    a = c + r.randint(1, 4)
    x = r.randint(2, 15)
    b = r.randint(1, 15)
    d = b + (a - c) * x
    x1, y = two_names(r)
    th = r.choice(THINGS)
    if d > 60:
        return None
    stem = (f"{x1} has ({lin(a, b, 'x')}) {th} and {y} has ({lin(c, d, 'x')}) {th}?" if False else
            f"{x1} has ({lin(a, b, 'x')}) {th}. {y} has ({lin(c, d, 'x')}) {th}. They have the same number of {th}. "
            f"How many {th} does each of them have?")
    ans = a * x + b
    return build(equation_both_sides, stem, ans, [
        (x, "gave_x", "Gave the value of x, not the number of items."),
        (c * x + b, "mixed_up_the_constants", f"Used {lin(c, b, 'x')}."),
        (a * x + d, "mixed_up_the_constants", f"Used {lin(a, d, 'x')}."),
        *slipn(ans, 1), *slipn(ans, 2),
    ], [f"{lin(a, b, 'x')} = {lin(c, d, 'x')}", f"{a - c}x = {d - b}", f"x = {x}", f"Each has {a} × {x} + {b} = {ans}"],
        {"a": a, "b": b, "c": c, "d": d}, unit(th), auto_slips=False, whole=True)


@checker(equation_both_sides)
def _(q):
    x = brute(lambda x: q["a"] * x + q["b"] == q["c"] * x + q["d"], 2000)
    return q["c"] * x + q["d"]


# --- true / false / not possible to tell, as a multiple-choice question

def _statements(kind, p):
    if kind == "tank":
        a, c = p["a"], p["c"]
        return [
            (f"Together, the two tanks hold ({lin(a + 1, c, 'x')}) litres.", lambda x: a * x + (x + c) == (a + 1) * x + c),
            ("Tank A holds more water than Tank B.", lambda x: a * x > x + c),
            ("Tank B holds more water than Tank A.", lambda x: x + c > a * x),
            (f"Together, the two tanks hold {a + 1}(x + {c}) litres.", lambda x: a * x + (x + c) == (a + 1) * (x + c)),
        ]
    b, k = p["b"], p["k"]
    return [
        ("Ben has more sweets than Ali.", lambda x: x + k > x),
        ("Cat has more sweets than Ben.", lambda x: b * x > x + k),
        ("Ali has more sweets than Cat.", lambda x: x > b * x),
        (f"Ben and Cat have {lin(b + k, 0, 'p')} sweets altogether.", lambda x: b * x + x + k == (b + k) * x),
    ]


@template(T, "intermediate", NOTATION, LETTER)
def always_true_statement(r):
    """math-pat-true-false-not-possible-to-tell"""
    if r.random() < 0.5:
        a, c = r.randint(2, 5), r.randint(3, 30)
        kind, p = "tank", {"a": a, "c": c}
        stem = (f"Tank A holds {plural(lin(a, 0, 'x'), 'litre')} of water and Tank B holds ({lin(1, c, 'x')}) litres, where x is a whole number "
                f"greater than 0. Which one of the following statements must be true?")
    else:
        b = r.randint(2, 5)
        k = r.randint(max(3, b), 15)
        kind, p = "sweets", {"b": b, "k": k}
        stem = (f"Ali has p sweets, where p is a whole number greater than 0. Ben has {k} more sweets than Ali. "
                f"Cat has {b} times as many sweets as Ali. Which one of the following statements must be true?")
        stem = stem.replace("p sweets", "p sweets").replace(lin(b + k, 0, "p"), lin(b + k, 0, "p"))
    sts = _statements(kind, p)
    # the unknown is written x in the tank question and p in the sweets question
    texts = [s[0] for s in sts]
    if kind == "sweets":
        texts = [t for t in texts]
    why = [None, ("assumed_a_value_for_the_letter", "Assumed a value of the letter: it may be true for some values but not for others."),
           ("assumed_a_value_for_the_letter", "Assumed a value of the letter: it may be true for some values but not for others."),
           ("combined_unlike_terms", "Simplified wrongly by treating the number and the letter terms as like terms.")]
    if kind == "sweets":
        why[2] = ("misread_the_comparison", "Compared the wrong way round: Cat has more sweets than Ali.")
    wrong = [((texts[i], i + 1), why[i][0], why[i][1]) for i in (1, 2, 3)]
    # the correct statement is item 0; the check recomputes truth over x = 1..100
    shows = lambda v: texts[int(v) - 1]
    return build(always_true_statement, stem, 1, wrong,
                 ["Test each statement with different values of the letter.", f"Only “{texts[0]}” is true for every value.",
                  "A statement that is true for some values and false for others cannot be said to be true: it is not possible to tell."],
                 {"kind": kind, **p}, shows, auto_slips=False)


@checker(always_true_statement)
def _(q):
    sts = _statements(q["kind"], q)
    always = [i + 1 for i, (_, pred) in enumerate(sts) if all(pred(x) for x in range(1, 101))]
    return F(always[0]) if len(always) == 1 else None


# ---------------------------------------------------------------- competent

@template(T, "competent", EQUATION, NOTATION)
def workers_total(r):
    """math-pat-algebra-workers-total"""
    a = r.randint(2, 6)
    m = r.randint(3, 10)
    W = a * m
    coef = W * (m - 1)
    job = r.choice([("packed", "cartons", "workers"), ("planted", "trees", "volunteers"), ("folded", "paper cranes", "pupils"),
                    ("painted", "posters", "students")])
    stem = (f"{W} {job[2]} were to share a job equally, and each was to have {job[0]} the same number of {job[1]}. "
            f"{a} of them were absent, so each of the others {job[0]} n more {job[1]}. "
            f"Find the total number of {job[1]} {job[0]}, in terms of n.")
    ans = E(f"{coef}n")
    wrong = [
        (E(f"{W - a}n"), "used_remaining_workers_times_n", f"Gave {W - a}n, the extra {job[1]} for the {W - a} who were present only."),
        (E(f"{W}n"), "used_original_workers_times_n", f"Gave {W}n."),
        (E(f"{(W - a) * (m - 1)}n"), "multiplied_wrong_share", f"Used {W - a} workers instead of {W}."),
        (E(f"{coef + W}n"), "careless_slip", "Made a slip in the calculation."),
        (E(f"{coef - W}n"), "careless_slip", "Made a slip in the calculation."),
    ]
    return build(workers_total, stem, ans[1], wrong,
                 [f"Let each person's share have been c.", f"{W}c = {W - a}(c + n)", f"{a}c = {W - a}n, so c = {m - 1}n",
                  f"Total = {W} × {m - 1}n = {coef}n"], {"W": W, "a": a}, show, auto_slips=False)


@checker(workers_total)
def _(q):
    W, a = q["W"], q["a"]
    n = a  # take n = a, then c is a whole number
    c = brute(lambda c: W * c == (W - a) * (c + n), 5000)
    return F(code(f"{int(W * c / n)}n"))


@template(T, "competent", EQUATION, SIMPLIFY)
def rectangle_perimeter_area(r):
    """math-pat-algebra-equation-from-figure"""
    x = r.randint(2, 12)
    a, c = r.randint(1, 4), r.randint(1, 3)
    b, d = r.randint(0, 8), r.randint(0, 6)
    L, W = a * x + b, c * x + d
    if L <= W + 1 or W < 2:
        return None
    P = 2 * (L + W)
    lab_l, lab_w = f"({lin(a, b, 'x')}) cm" if b else f"{lin(a, 0, 'x')} cm", f"({lin(c, d, 'x')}) cm" if d else f"{lin(c, 0, 'x')} cm"
    fig = rectangle_labels(lab_l, lab_w)
    stem = (f"The figure shows a rectangle with length {lab_l} and width {lab_w}. The figure is not drawn to scale. "
            f"The perimeter of the rectangle is {P} cm. What is the area of the rectangle in cm²?")
    area = L * W
    half = F(P, 2)
    return build(rectangle_perimeter_area, stem, area, [
        (x, "gave_x", "Gave the value of x."),
        (P, "gave_the_perimeter", "Gave the perimeter."),
        (L + W, "gave_the_half_perimeter", "Gave the sum of the length and width."),
        (L * W + L, "careless_slip", "Made a slip in the multiplication."),
        (L * W - W, "careless_slip", "Made a slip in the multiplication."),
        (L * c * x if False else (L + 1) * W, "careless_slip", "Made a slip in the multiplication."),
        (half * W if half * W != area else None, "mixed_up_the_sides", "Multiplied the wrong numbers."),
    ], [f"Perimeter = 2 × ({lin(a, b, 'x')} + {lin(c, d, 'x')}) = 2 × ({lin(a + c, b + d, 'x')}) = {P}",
        f"{lin(a + c, b + d, 'x')} = {P // 2}, so {a + c}x = {P // 2 - b - d}, x = {x}", f"Length = {L} cm, width = {W} cm",
        f"Area = {L} × {W} = {area} cm²"], {"a": a, "b": b, "c": c, "d": d, "P": P}, unit("cm²"), whole=True,
        auto_slips=False, figure=fig)


@checker(rectangle_perimeter_area)
def _(q):
    for x in range(1, 500):
        L, W = q["a"] * x + q["b"], q["c"] * x + q["d"]
        if 2 * L + 2 * W == q["P"]:
            return F(sum(W for _ in range(L)))


@template(T, "competent", EQUATION)
def equation_three_people(r):
    j = r.randint(2, 4)
    k = r.randint(2, 12)
    m = r.randint(3, 15)
    x = r.randint(4, 20)
    ben = j * x + k
    cat = ben - m
    if cat <= 0:
        return None
    tot = x + ben + cat
    n1, n2, n3 = r.sample(NAMES, 3)
    th = r.choice(THINGS)
    word = {2: "twice", 3: "3 times", 4: "4 times"}[j]
    stem = (f"{n1} has x {th}. {n2} has {k} more than {word} as many {th} as {n1}. {n3} has {m} fewer {th} than {n2}. "
            f"The three of them have {tot} {th} altogether. How many {th} does {n3} have?")
    return build(equation_three_people, stem, cat, [
        (x, "gave_x", f"Gave the number of {th} {n1} has."),
        (ben, "gave_the_wrong_person", f"Gave the number of {th} {n2} has."),
        (cat + 2 * m if cat + 2 * m != ben else None, "sign_error_on_constant", f"Added {m} instead of subtracting it."),
        (x + m, "careless_slip", "Made a slip in the calculation."),
        *slipn(cat, 1), *slipn(cat, 2),
    ], [f"{n2}: {lin(j, k, 'x')}; {n3}: {lin(j, k - m, 'x')}", f"Total: x + ({lin(j, k, 'x')}) + ({lin(j, k - m, 'x')}) = {lin(2 * j + 1, 2 * k - m, 'x')} = {tot}",
        f"{2 * j + 1}x = {tot - 2 * k + m}, x = {x}", f"{n3} has {j} × {x} + {k} − {m} = {cat}"],
        {"j": j, "k": k, "m": m, "tot": tot}, unit(th), whole=True, auto_slips=False)


@checker(equation_three_people)
def _(q):
    for x in range(1, 1000):
        ben = q["j"] * x + q["k"]
        if x + ben + ben - q["m"] == q["tot"]:
            return F(ben - q["m"])


@template(T, "competent", EQUATION)
def hire_hours(r):
    fee = r.randint(10, 60)
    rate = r.randint(3, 15)
    h = r.randint(3, 14)
    tot = fee + rate * h
    thing = r.choice([("A hall", "hire"), ("A bouncy castle", "rental"), ("A coach", "hire")])
    stem = (f"The {thing[1]} charge for {thing[0].lower()} is (${fee} + ${rate}h), where h is the number of hours. "
            f"{r.choice(NAMES)} paid ${tot} for the {thing[1]}. For how many hours was it hired?")
    return build(hire_hours, stem, h, [
        (F(tot, rate), "forgot_the_fixed_charge", f"Divided ${tot} by {rate} and forgot the ${fee}."),
        (tot - fee, "forgot_to_divide", "Stopped after taking away the fixed charge."),
        (F(tot + fee, rate), "added_the_fixed_charge", f"Added ${fee} instead of subtracting it."),
        *slipn(h, 1), *slipn(h, 2),
    ], [f"{fee} + {rate}h = {tot}", f"{rate}h = {tot - fee}", f"h = {h}"], {"fee": fee, "rate": rate, "tot": tot}, unit("hours"),
        whole=True, auto_slips=False)


@checker(hire_hours)
def _(q):
    return brute(lambda h: q["fee"] + q["rate"] * h == q["tot"], 1000)


@template(T, "competent", EQUATION)
def consecutive_numbers(r):
    m = r.choice([3, 4, 5])
    s = r.choice([1, 2])
    n = r.randint(5, 40)
    if s == 2 and n % 2 == 0:
        n += 1
    odd_even = ""
    if s == 2:
        odd_even = "odd " if n % 2 else "even "
    S = sum(n + i * s for i in range(m))
    big = n + (m - 1) * s
    word = {3: "three", 4: "four", 5: "five"}[m]
    stem = (f"The sum of {word} consecutive {odd_even}whole numbers is {S}. What is the largest of the {word} numbers?"
            if s == 2 else f"The sum of {word} consecutive whole numbers is {S}. What is the largest of the {word} numbers?")
    # wrong if taking step 1 for odd/even: n' with sum m n' + m(m-1)/2
    n1 = F(S - m * (m - 1) // 2, m)
    return build(consecutive_numbers, stem, big, [
        (n, "gave_the_smallest", "Gave the smallest number."),
        (F(S, m), "gave_the_average", "Gave the average of the numbers."),
        (n1 + m - 1 if s == 2 else big - 1, "used_step_of_one" if s == 2 else "careless_slip",
         "Treated the numbers as consecutive whole numbers instead of odd or even ones." if s == 2 else "Made a slip in the calculation."),
        (big + s, "gave_the_next_number", "Gave the number after the largest."),
        (big - s, "gave_the_second_largest", "Gave the second largest number."),
    ], [f"Let the smallest number be n. The numbers are n, n + {s}, ... , n + {(m - 1) * s}.",
        f"{m}n + {s * m * (m - 1) // 2} = {S}", f"n = {n}", f"Largest = {n} + {(m - 1) * s} = {big}"],
        {"m": m, "s": s, "S": S}, whole=True, auto_slips=False)


@checker(consecutive_numbers)
def _(q):
    for n in range(1, 5000):
        if sum(n + i * q["s"] for i in range(q["m"])) == q["S"]:
            return F(n + (q["m"] - 1) * q["s"])


@template(T, "competent", SUBST, NOTATION)
def fraction_then_substitute(r):
    q_ = r.choice([2, 3, 4, 5])
    a = q_ * r.randint(1, 3)
    N = r.randint(4, 15)
    b = r.randint(2, 12)
    val = F(a * N * (q_ - 1), q_) - b
    if val <= 0 or F(a * N, q_).denominator != 1:
        return None
    nm = r.choice(NAMES)
    th = r.choice(THINGS)
    frac_w = {2: "half", 3: "one-third", 4: "one-quarter", 5: "one-fifth"}[q_]
    stem = (f"{nm} had {a}n {th}. {nm} gave away {frac_w} of them and then used {b} more. "
            f"How many {th} did {nm} have left when n = {N}?")
    tot = a * N
    return build(fraction_then_substitute, stem, val, [
        (F(tot, q_), "gave_the_fraction_given_away", f"Gave the number of {th} given away."),
        (tot - b, "forgot_to_give_away_the_fraction", f"Forgot the {frac_w} that was given away."),
        (F(tot * (q_ - 1), q_) + b, "sign_error_on_constant", f"Added {b} instead of subtracting it."),
        (F(tot, q_) - b if F(tot, q_) - b > 0 else None, "took_the_fraction_not_the_remainder", f"Subtracted from the {frac_w} instead of from what was left."),
        *slipn(val, 1), *slipn(val, 2),
    ], [f"At first: {a} × {N} = {tot}", f"Gave away {frac_w}: {tot} ÷ {q_} = {tot // q_}", f"Left: {tot} − {tot // q_} − {b} = {int(val)}"],
        {"q": q_, "a": a, "N": N, "b": b}, whole=True, auto_slips=False)


@checker(fraction_then_substitute)
def _(q):
    start = q["a"] * q["N"]
    left = start - start * F(1, q["q"])
    return left - q["b"]


@template(T, "competent", EQUATION)
def ages_equation(r):
    j = r.randint(3, 4)
    x = r.randint(6, 14)
    yrs = r.randint(3, 8)
    S = x + j * x + 2 * yrs
    c1, c2 = two_names(r)
    stem = (f"{c1}'s mother is {j} times as old as {c1}. In {yrs} years' time, the sum of their ages will be {S} years. "
            f"How old is {c1}'s mother now?")
    ans = j * x
    return build(ages_equation, stem, ans, [
        (x, "gave_the_childs_age", f"Gave {c1}'s age."),
        (ans + yrs, "gave_the_age_in_the_future", f"Gave the mother's age in {yrs} years."),
        (F(S, 1 + j) * j if S % (1 + j) == 0 else None, "forgot_the_years_passing", "Ignored that both of them get older."),
        (F(S - yrs, 1 + j) * j if (S - yrs) % (1 + j) == 0 else None, "added_the_years_once", f"Took away {yrs} years only once."),
        *slipn(ans, 1), *slipn(ans, j),
    ], [f"Now: {c1} is x, mother is {j}x", f"In {yrs} years: x + {yrs} and {j}x + {yrs}", f"{j + 1}x + {2 * yrs} = {S}", f"x = {x}", f"Mother = {j} × {x} = {ans}"],
        {"j": j, "yrs": yrs, "S": S}, unit("years"), whole=True, auto_slips=False)


@checker(ages_equation)
def _(q):
    for x in range(1, 100):
        if (x + q["yrs"]) + (q["j"] * x + q["yrs"]) == q["S"]:
            return F(q["j"] * x)


@template(T, "competent", EQUATION)
def plans_same_cost(r):
    ra = r.randint(5, 15)
    rb = r.randint(2, ra - 2)
    h = r.randint(3, 12)
    fa = r.randint(5, 30)
    fb = fa + (ra - rb) * h
    if fb > 120:
        return None
    nm = r.choice(NAMES)
    kind = r.choice([("gym", "per visit", "visits"), ("swimming club", "per lesson", "lessons"), ("karaoke room", "per hour", "hours")])
    stem = (f"Plan A for a {kind[0]} charges ${fa} to join and ${ra} {kind[1]}. Plan B charges ${fb} to join and ${rb} {kind[1]}. "
            f"After how many {kind[2]} will the two plans cost the same?")
    return build(plans_same_cost, stem, h, [
        (F(fb + fa, ra - rb) if (fb + fa) % (ra - rb) == 0 else None, "added_the_joining_fees", "Added the joining fees instead of subtracting."),
        (F(fb - fa, ra + rb) if (fb - fa) % (ra + rb) == 0 else None, "added_the_rates", f"Added the two rates instead of subtracting."),
        (F(fa, ra - rb) if fa % (ra - rb) == 0 else None, "used_one_fee_only", "Used only Plan A's joining fee."),
        *slipn(h, 1), *slipn(h, 2),
    ], [f"Plan A: {fa} + {ra}h; Plan B: {fb} + {rb}h", f"{fa} + {ra}h = {fb} + {rb}h", f"{ra - rb}h = {fb - fa}", f"h = {h}"],
        {"fa": fa, "ra": ra, "fb": fb, "rb": rb}, whole=True, auto_slips=False)


@checker(plans_same_cost)
def _(q):
    return brute(lambda h: q["fa"] + q["ra"] * h == q["fb"] + q["rb"] * h, 1000)
