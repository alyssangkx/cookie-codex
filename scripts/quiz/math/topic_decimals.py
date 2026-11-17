"""Decimals (math-decimals): basic, intermediate and competent generators."""
from itertools import permutations
from decimal import Decimal, ROUND_HALF_UP, ROUND_FLOOR
from common import *

T = "math-decimals"
DN = "math-decimals-decimal-notation-and-comparison-"
DO = "math-decimals-four-operations-with-decimals-"


def dec(x):
    """Decimal text with as few places as needed (0.5, 0.45, 12)."""
    x = F(x)
    for p in range(0, 8):
        if (x * 10 ** p).denominator == 1:
            return f"{float(x):.{p}f}"
    return f"{float(x):.4f}"


def fx(dp):
    return lambda x: f"{float(x):.{dp}f}"


def H(n, dp=2):
    """Integer n in units of 10^-dp as an exact value."""
    return F(n, 10 ** dp)


def digitwise(a, b, op):
    """The 'column by column, no carrying or borrowing' wrong answer, on integers."""
    L = max(len(str(a)), len(str(b)))
    sa, sb = str(a).zfill(L), str(b).zfill(L)
    if op == "+":
        return int("".join(str((int(x) + int(y)) % 10) for x, y in zip(sa, sb)))
    return int("".join(str(abs(int(x) - int(y))) for x, y in zip(sa, sb)))


def rnd(x, dp):
    return F(str((Decimal(x.numerator) / Decimal(x.denominator)).quantize(Decimal(1).scaleb(-dp), rounding=ROUND_HALF_UP)))


def trunc(x, dp):
    return F(str((Decimal(x.numerator) / Decimal(x.denominator)).quantize(Decimal(1).scaleb(-dp), rounding=ROUND_FLOOR)))


def dtxt(n, dp):
    return f"{n / 10 ** dp:.{dp}f}"


# ================================================================ NOTATION: basic

PLACE_DP = {1: "tenths", 2: "hundredths", 3: "thousandths"}


@template(T, "basic", DN + "01")
def dec_place_value(r):
    """math-pat-place-value-decimals"""
    digits = r.sample(range(1, 10), 4)
    w = r.randint(1, 99)
    k = r.randint(1, 3)
    n = w * 1000 + digits[0] * 100 + digits[1] * 10 + digits[2]
    d = [digits[0], digits[1], digits[2]][k - 1]
    ans = F(d, 10 ** k)
    stem = f"What is the value of the digit {d} in {n / 1000:.3f}?"
    return build(dec_place_value, stem, ans, [
        (F(d, 10 ** (k - 1)) if k > 1 else d, "read_one_place_too_high", "Read the digit as being one place to the left."),
        (F(d, 10 ** (k + 1)), "read_one_place_too_low", "Read the digit as being one place to the right."),
        (d, "gave_the_digit", "Gave the digit and not its value."),
        (d * 10 ** k, "mixed_up_decimal_and_whole_places", "Mixed up thousandths with thousands."),
    ], [f"The {d} is in the {PLACE_DP[k]} place.", f"Value = {d}/{10 ** k} = {dec(ans)}"],
        {"n": n, "d": d}, dec, auto_slips=False)


@checker(dec_place_value)
def _(p):
    s = f"{p['n'] / 1000:.3f}".split(".")[1]
    return F(p["d"], 10 ** (s.index(str(p["d"])) + 1))


@template(T, "basic", DN + "02")
def dec_compare(r):
    """math-pat-decimal-compare-order"""
    vals = set()
    t = r.randint(2, 7)
    while len(vals) < 4:
        dp = r.choice([1, 2, 3])
        m = r.randint(t * 100, t * 100 + 99)
        vals.add(F(m // 10 ** (3 - dp), 10 ** dp))
    vals = sorted(vals)
    big = r.random() < 0.5
    ans = vals[-1] if big else vals[0]
    scale = lambda v: v < 10
    others = [v for v in vals if v != ans]
    longest = max(others, key=lambda v: len(dec(v)))
    others.sort(key=lambda v: (v != longest))
    listing = ", ".join(dec(v) for v in r.sample(vals, 4))
    stem = f"Which is the {'greatest' if big else 'smallest'} of these numbers: {listing}?"
    return build(dec_compare, stem, ans, [
        (v, "longer_decimal_thought_larger" if v == longest else "compared_digits_not_place_values",
         "Thought the decimal with more digits is larger." if v == longest else "Did not compare the numbers place by place.")
        for v in others], [f"Write each number to {max(len(dec(v).split('.')[1]) if '.' in dec(v) else 0 for v in vals)} decimal places and compare.",
                           f"Answer: {dec(ans)}"], {"vals": [[v.numerator, v.denominator] for v in vals], "big": big}, dec, auto_slips=False)


@checker(dec_compare)
def _(p):
    xs = [F(a, b) for a, b in p["vals"]]
    return max(xs) if p["big"] else min(xs)


@template(T, "basic", DN + "03", same_value_ok=True)
def dec_to_fraction(r):
    dp = r.choice([1, 2, 3])
    n = r.randint(1, 10 ** dp - 1)
    if n % 10 == 0 and dp > 1:
        return None
    ans = F(n, 10 ** dp)
    if ans.denominator == 10 ** dp:
        return None  # already simplest, no simplification skill used
    stem = f"Express {dtxt(n, dp)} as a fraction in its simplest form."
    return build(dec_to_fraction, stem, ans, [
        ((f"{n}/{10 ** dp}", ans), "stopped_before_simplest", "Wrote the fraction but did not simplify it."),
        (F(n, 10 ** (dp - 1)) if dp > 1 else F(n, 100), "wrong_denominator", "Used the wrong power of 10 as the denominator."),
        (F(n, 10 ** (dp + 1)), "wrong_denominator", "Used one place too many in the denominator."),
        (F(n, 10 ** dp * 10 // 10) + F(1, 10 ** dp), "slip_in_numerator", "Slip in the numerator."),
    ], [f"{dtxt(n, dp)} = {n}/{10 ** dp}", f"Divide the top and bottom by {gcd(n, 10 ** dp)}: {frac(ans, mixed=False)}"],
        {"n": n, "dp": dp}, lambda x: frac(x, mixed=False), auto_slips=False)


@checker(dec_to_fraction)
def _(p):
    return F(dtxt(p["n"], p["dp"]))


@template(T, "basic", DN + "04")
def frac_to_dec_exact(r):
    b = r.choice([2, 4, 5, 10, 20, 25, 50, 100])
    a = r.randint(1, b - 1) if b > 2 else 1
    if b in (10, 100) and a % 10 == 0:
        return None
    ans = F(a, b)
    cat = F(int(f"{a}{b}"), 10 ** len(f"{a}{b}"))
    stem = f"Express {a}/{b} as a decimal."
    return build(frac_to_dec_exact, stem, ans, [
        (cat, "wrote_numerator_and_denominator_after_point", "Wrote the numerator and denominator after the decimal point."),
        (ans * 10, "wrong_decimal_place", "Put the decimal point one place too far right."),
        (ans / 10, "wrong_decimal_place", "Put the decimal point one place too far left."),
        (F(b, a) if F(b, a).denominator in (1, 2, 4, 5, 10, 20, 25) else None, "divided_the_wrong_way", "Divided the denominator by the numerator."),
        (ans + F(1, 100), "slip", "Slip in the last digit."),
    ], [f"Make the denominator 100: {a}/{b} = {a * (100 // b)}/100", f"= {dec(ans)}"], {"a": a, "b": b}, dec, auto_slips=False)


@checker(frac_to_dec_exact)
def _(p):
    return F(str(Decimal(p["a"]) / Decimal(p["b"])))


@template(T, "basic", DN + "05")
def round_decimal(r):
    dp = r.choice([0, 1, 2])
    n = r.randint(1000, 98999)
    x = F(n, 1000)
    if n % 10 == 0:
        return None
    ans = rnd(x, dp)
    stem = f"Round {n / 1000:.3f} to {'the nearest whole number' if dp == 0 else str(dp) + ' decimal place' + ('s' if dp > 1 else '')}."
    show = fx(dp)
    wrong = []
    tr = trunc(x, dp)
    if tr != ans:
        wrong.append((tr, "cut_off_instead_of_rounding", "Cut the number off without rounding."))
    for odp in [d for d in (0, 1, 2, 3) if d != dp]:
        v = rnd(x, odp)
        if v != ans:
            wrong.append(((fx(odp)(v), v), "rounded_to_wrong_number_of_places", f"Rounded to {plural(odp, 'decimal place')}."))
    wrong += [(ans + F(1, 10 ** dp), "rounding_slip", "Made a slip with the last digit."),
              (ans - F(1, 10 ** dp), "rounding_slip", "Made a slip with the last digit.")]
    return build(round_decimal, stem, ans, wrong, [f"Look at the next digit after the {'ones place' if dp == 0 else ordinal(dp) + ' decimal place'}.", f"Answer: {show(ans)}"],
                 {"n": n, "dp": dp}, show, auto_slips=False)


@checker(round_decimal)
def _(p):
    return F(str((Decimal(p["n"]) / 1000).quantize(Decimal(1).scaleb(-p["dp"]), rounding=ROUND_HALF_UP)))


# ================================================================ NOTATION: intermediate

@template(T, "intermediate", DN + "02")
def between_decimals(r):
    """math-pat-decimal-compare-order"""
    a = r.randint(120, 880)
    A, B = F(a, 100), F(a + 1, 100)
    x = r.randint(1, 9)
    ans = A + F(x, 1000)
    d1, d2, d3 = r.sample(range(1, 10), 3)
    stem = f"Which number lies between {dec(A)} and {dec(B)}?"
    return build(between_decimals, stem, ans, [
        (A - F(d1, 1000), "chose_a_number_below", f"Chose a number just below {dec(A)}."),
        (B + F(d2, 1000), "chose_a_number_above", f"Chose a number just above {dec(B)}."),
        (B + F(d3 + 10, 1000), "compared_digits_as_whole_numbers", "Compared the digits after the point as whole numbers."),
        (A - F(d3 + 10, 1000), "compared_digits_as_whole_numbers", "Compared the digits after the point as whole numbers."),
    ], [f"{dec(A)} = {dec(A)}0 and {dec(B)} = {dec(B)}0 in thousandths: {int(A * 1000)} and {int(B * 1000)}", f"{int(ans * 1000)} is between them."],
        {"a": a, "ans": int(ans * 1000)}, fx(3), auto_slips=False)


@checker(between_decimals)
def _(p):
    lo, hi = p["a"] * 10, (p["a"] + 1) * 10
    return F(p["ans"], 1000) if lo < p["ans"] < hi else None


@template(T, "intermediate", DN + "03", same_value_ok=True)
def dec_to_mixed(r):
    w = r.randint(1, 9)
    dp = r.choice([2, 3])
    n = r.randint(1, 10 ** dp - 1)
    if n % 10 == 0 or F(n, 10 ** dp).denominator == 10 ** dp:
        return None
    f_ = F(n, 10 ** dp)
    ans = w + f_
    stem = f"Express {w}.{n:0{dp}d} as a mixed number in its simplest form."
    return build(dec_to_mixed, stem, ans, [
        ((f"{w} {n}/{10 ** dp}", ans), "stopped_before_simplest", "Did not simplify the fraction part."),
        (w + F(n, 10 ** (dp - 1)), "wrong_denominator", "Used one place too few in the denominator."),
        (w + F(n, 10 ** (dp + 1)), "wrong_denominator", "Used one place too many in the denominator."),
        (w + F(n, 10 ** dp) * 10 % 1 if False else (w + 1) + f_, "slip_in_whole_part", "Slip in the whole number part."),
    ], [f"0.{n:0{dp}d} = {n}/{10 ** dp} = {frac(f_)}", f"Answer: {frac(ans)}"], {"w": w, "n": n, "dp": dp}, frac, auto_slips=False)


@checker(dec_to_mixed)
def _(p):
    return F(f"{p['w']}.{p['n']:0{p['dp']}d}")


@template(T, "intermediate", DN + "04", DN + "02")
def compare_mixed_forms(r):
    pool = [F(a, b) for b in (2, 4, 5, 8, 20, 25) for a in range(1, b)]
    dpool = [F(x, 100) for x in range(20, 90)]
    for _ in range(50):
        fr = r.sample(pool, 2)
        dc = r.sample(dpool, 2)
        vs = fr + dc
        if len(set(vs)) == 4 and all(0.2 < v < 0.9 for v in vs) and not any(d.denominator in (1,) for d in vs):
            break
    else:
        return None
    disp = {}
    for v in fr:
        disp[v] = frac(v, mixed=False)
    for v in dc:
        disp[v] = dec(v)
    if len(set(disp.values())) != 4:
        return None
    if len({F(x) for x in vs}) != 4:
        return None
    big = r.random() < 0.5
    ans = max(vs) if big else min(vs)
    others = [v for v in vs if v != ans]
    order = r.sample(vs, 4)
    stem = f"Which is the {'greatest' if big else 'smallest'} number: {', '.join(disp[v] for v in order)}?"
    return build(compare_mixed_forms, stem, ans, [
        (v, "compared_without_converting", "Compared a fraction and a decimal without writing them in the same form.") for v in
        sorted(others, key=lambda v: -abs(v - ans))[::-1]],
        ["Write every number as a decimal.", ", ".join(f"{disp[v]} = {dec(v)}" for v in order)],
        {"vs": [[v.numerator, v.denominator] for v in vs], "big": big}, lambda x: disp[F(x)], auto_slips=False)


@checker(compare_mixed_forms)
def _(p):
    xs = [F(a, b) for a, b in p["vs"]]
    return max(xs) if p["big"] else min(xs)


@template(T, "intermediate", DN + "05", DN + "02")
def rounding_range_decimal(r):
    t = r.choice([0, 1])
    u = F(1, 10 ** (t + 1))
    X = F(r.randint(11 if t else 3, 98 if t else 40), 10 ** t)
    big = r.random() < 0.5
    ans = X + 4 * u if big else X - 5 * u
    dp = t + 1
    wrong = ([(X + 5 * u, "boundary_rounds_up", "Used a number that rounds up to the next value."), (X + 9 * u, "used_next_digit_nine", "Used the largest digit."),
              (X + 3 * u, "slip", "Slip."), (X, "gave_the_rounded_number", "Gave the rounded number itself.")] if big else
             [(X - 6 * u, "rounds_down_to_the_lower_value", "Used a number that rounds to the lower value."), (X - 4 * u, "slip", "Used a number just above the boundary."),
              (X - 9 * u, "used_next_digit_nine", "Used the wrong boundary."), (X, "gave_the_rounded_number", "Gave the rounded number itself.")])
    stem = (f"A number is {dec(X) if t else int(X)} when rounded to {'1 decimal place' if t else 'the nearest whole number'}. "
            f"What is the {'greatest' if big else 'smallest'} {'2-decimal-place' if t else '1-decimal-place'} number it could be?")
    return build(rounding_range_decimal, stem, ans, wrong, [f"Numbers from {fx(dp)(X - 5 * u)} to {fx(dp)(X + 4 * u)} round to {dec(X)}.", f"Answer: {fx(dp)(ans)}"],
                 {"X": [X.numerator, X.denominator], "t": t, "big": big}, fx(dp), auto_slips=False)


@checker(rounding_range_decimal)
def _(p):
    X, t = F(*p["X"]), p["t"]
    step = F(1, 10 ** (t + 1))
    cand = [X + i * step for i in range(-10, 11)]
    ok = [c for c in cand if rnd(c, t) == X]
    return max(ok) if p["big"] else min(ok)


# ================================================================ NOTATION: competent

@template(T, "competent", DN + "02", DN + "05")
def digit_cards_decimal(r):
    ds = r.sample(range(10), 4)
    if 0 not in ds and r.random() < .5:
        return None
    g = F(int("".join(map(str, sorted(ds, reverse=True)))), 100)
    asc = sorted(ds)
    if asc[0] == 0:
        asc[0], asc[1] = asc[1], asc[0]
    s = F(int("".join(map(str, asc))), 100)
    ans = g - s
    lead0 = F(int("".join(map(str, sorted(ds)))), 100)
    stem = (f"Using each of the digits {', '.join(map(str, sorted(ds)))} once and a decimal point, Priya forms the greatest and the smallest "
            f"numbers with 2 digits before the decimal point and 2 decimal places. A number cannot start with 0. What is the difference between them?")
    return build(digit_cards_decimal, stem, ans, [
        (g - lead0, "allowed_a_leading_zero", "Used a smallest number that starts with 0."),
        (g + s, "added_instead_of_subtracted", "Added the two numbers."),
        (g - s + F(9, 100), "slip", "Swapped the last two digits of one number."),
        (g - s - F(9, 100), "slip", "Swapped the last two digits of one number.")],
        [f"Greatest: {fx(2)(g)}", f"Smallest: {fx(2)(s)}", f"{fx(2)(g)} − {fx(2)(s)} = {fx(2)(ans)}"], {"ds": ds}, fx(2), auto_slips=False)


@checker(digit_cards_decimal)
def _(p):
    xs = [F(int("".join(map(str, q))), 100) for q in permutations(p["ds"]) if q[0] != 0]
    return max(xs) - min(xs)


@template(T, "competent", DN + "02", DN + "01")
def count_decimals_between(r):
    dp = r.choice([1, 2])
    lo = r.randint(15, 90) * (1 if dp == 1 else 1)
    A = lo
    B = lo + r.randint(8, 60)
    incl = r.random() < 0.5
    ans = B - A + 1 if incl else B - A - 1
    a, b = dtxt(A, dp), dtxt(B, dp)
    stem = (f"How many numbers with exactly {dp} decimal place{'s' if dp > 1 else ''} are there from {a} to {b}, "
            f"{'including both' if incl else 'not including'} {a} and {b}?" if True else "")
    return build(count_decimals_between, stem, ans, [
        (B - A if incl else B - A + 1, "forgot_the_ends_rule", "Used the difference without handling the ends correctly."),
        (B - A - 1 if incl else B - A, "forgot_the_ends_rule", "Used the difference without handling the ends correctly."),
        (F(B - A, 10) if (B - A) % 10 == 0 else None, "divided_by_ten", "Thought there are only tenths."),
        (ans + 2, "slip", "Counted the ends twice."), (ans * 10, "slip", "Counted tenths of tenths.")],
        [f"{a} = {A} units and {b} = {B} units of 0.{'1' if dp == 1 else '01'}.", f"Count = {ans}"],
        {"A": A, "B": B, "incl": incl}, str, whole=True, auto_slips=False)


@checker(count_decimals_between)
def _(p):
    xs = range(p["A"], p["B"] + 1) if p["incl"] else range(p["A"] + 1, p["B"])
    return F(len(list(xs)))


@template(T, "competent", DN + "02", DN + "01")
def mixed_unit_lengths(r):
    x, y, z = r.sample(NAMES, 3)
    cms = r.sample(range(105, 175), 3)
    a, b, c = cms
    ans = max(cms) - min(cms)
    mid = sorted(cms)[1]
    stem = (f"{x} jumped {a / 100:.2f} m, {y} jumped {b} cm and {z} jumped {c / 100:.2f} m in the long jump. "
            f"What is the difference, in cm, between the longest and the shortest jump?")
    cm = lambda v: int(v)
    wrong = [(max(a, c * 10, b) - min(a, b, c) if False else abs(max([a * 10, b, c * 10]) - min([a * 10, b, c * 10])), "converted_metres_to_cm_wrongly", "Multiplied the metres by 1 000 instead of 100."),
             (max(cms) - mid, "used_wrong_pair", "Compared the longest with the middle jump."),
             (mid - min(cms), "used_wrong_pair", "Compared the middle with the shortest jump."),
             (ans + 10, "slip", "Slip in the subtraction."), (ans - 5, "slip", "Slip in the subtraction.")]
    return build(mixed_unit_lengths, stem, ans, wrong, [f"{a / 100:.2f} m = {a} cm, {c / 100:.2f} m = {c} cm", f"Longest − shortest = {max(cms)} − {min(cms)} = {ans} cm"],
                 {"a": a, "b": b, "c": c}, lambda v: f"{int(v)} cm", whole=True, auto_slips=False)


@checker(mixed_unit_lengths)
def _(p):
    v = [F(p["a"] / 1) , F(p["b"]), F(p["c"])]
    return max(v) - min(v)


# ================================================================ OPERATIONS: basic

def _dec_operand(r, dp):
    return r.randint(1, 99) if dp == 0 else None


@template(T, "basic", DO + "01")
def decimal_add_subtract(r):
    """math-pat-decimal-add-subtract"""
    dpa, dpb = r.choice([(2, 1), (1, 2), (0, 2), (2, 0), (1, 0), (2, 1), (1, 2)])
    A = r.randint(300, 2999) if dpa == 2 else r.randint(30, 299) * 10 if dpa == 1 else r.randint(5, 40) * 100
    B = r.randint(100, 999) if dpb == 2 else r.randint(10, 99) * 10 if dpb == 1 else r.randint(2, 9) * 100
    add = r.random() < 0.5
    if not add and A <= B + 100:
        return None
    ans = H(A + B) if add else H(A - B)
    fmt = lambda n, dp: dtxt(n, 2) if dp == 2 else (f"{n / 100:.1f}" if dp == 1 else f"{n // 100}")
    stem = f"Find {fmt(A, dpa)} {'+' if add else '−'} {fmt(B, dpb)}."
    # misaligned: the shorter number is lined up to the right as if it had the same number of places
    sh = lambda n, dp: n // 100 * 100 + (n % 100) // 10 if False else (n // 100) * 100 + (n // 10 % 10 if dp == 1 else 0) if dp < 2 else n
    mis_b = (B // 100) * 100 + ((B // 10) % 10) if dpb == 1 else B
    mis_a = (A // 100) * 100 + ((A // 10) % 10) if dpa == 1 else A
    mis = (mis_a + mis_b if add else mis_a - mis_b) if (dpa != 2 or dpb != 2) else None
    wrong = [(H(digitwise(A, B, "+" if add else "−")), "forgot_to_carry" if add else "subtracted_smaller_digit_from_larger",
              "Added the columns without carrying." if add else "Took the smaller digit from the larger in each column."),
             (H(mis) if mis and mis > 0 else None, "misaligned_decimal_point", "Did not line up the decimal points."),
             (ans + F(1, 10), "slip", "Slip in the tenths."), (ans - 1 if ans > 1 else ans + 1, "slip", "Slip with borrowing or carrying."),
             (ans + F(1, 100), "slip", "Slip in the hundredths.")]
    return build(decimal_add_subtract, stem, ans, wrong,
                 ["Line up the decimal points and write in zeros where needed.", f"Answer: {dec(ans)}"], {"A": A, "B": B, "add": add},
                 dec, auto_slips=False)


@checker(decimal_add_subtract)
def _(p):
    return F(str(Decimal(p["A"]) / 100 + Decimal(p["B"]) / 100)) if p["add"] else F(str(Decimal(p["A"]) / 100 - Decimal(p["B"]) / 100))


@template(T, "basic", DO + "02")
def mult_by_digit(r):
    """math-pat-decimal-operations-direct"""
    dp = r.choice([1, 2])
    a = r.randint(11, 99) * 10 if dp == 1 and False else r.randint(105, 899) if dp == 2 else r.randint(11, 99)
    d = r.randint(3, 9)
    if a % 10 == 0:
        return None
    A = F(a, 10 ** dp)
    ans = A * d
    stem = f"Find {dtxt(a, dp)} × {d}."
    return build(mult_by_digit, stem, ans, [
        (ans * 10, "misplaced_decimal_point", "Put the decimal point one place too far right."),
        (ans / 10, "misplaced_decimal_point", "Put the decimal point one place too far left."),
        (ans - A, "missed_one_group", "Missed one copy of the number."),
        (ans + F(1, 10 ** dp) * 10, "carry_slip", "Slip with a carry."), (ans - F(1, 10 ** dp) * 10, "carry_slip", "Slip with a carry.")],
        [f"{a} × {d} = {a * d}", f"Put back {plural(dp, 'decimal place')}: {dec(ans)}"], {"a": a, "dp": dp, "d": d}, dec, auto_slips=False)


@checker(mult_by_digit)
def _(p):
    return F(str(Decimal(p["a"]) / 10 ** p["dp"] * p["d"]))


@template(T, "basic", DO + "02")
def div_by_digit(r):
    """math-pat-decimal-operations-direct"""
    dp = r.choice([1, 2])
    d = r.randint(3, 9)
    q = r.randint(11, 199) if dp == 1 else r.randint(105, 899)
    if q % 10 == 0:
        return None
    n = q * d
    ans = F(q, 10 ** dp)
    stem = f"Find {dtxt(n, dp)} ÷ {d}."
    return build(div_by_digit, stem, ans, [
        (ans * 10, "misplaced_decimal_point", "Put the decimal point one place too far right."),
        (ans / 10, "misplaced_decimal_point", "Put the decimal point one place too far left."),
        (ans + F(1, 10), "slip", "Slip in the tenths."), (ans - F(1, 10), "slip", "Slip in the tenths."),
        (ans + F(1, 100), "slip", "Slip in the hundredths.")],
        [f"{n} ÷ {d} = {q}", f"Put back {plural(dp, 'decimal place')}: {dec(ans)}"], {"n": n, "dp": dp, "d": d}, dec, auto_slips=False)


@checker(div_by_digit)
def _(p):
    return F(str(Decimal(p["n"]) / 10 ** p["dp"] / p["d"]))


@template(T, "basic", DO + "05")
def mul_div_ten_powers(r):
    """math-pat-decimal-operations-direct"""
    k = r.randint(1, 3)
    mult = r.random() < 0.5
    mm = r.choice([1, 1, 2, 3, 4, 5])
    f_ = mm * 10 ** k
    x = F(r.randint(11, 9999), 10 ** r.randint(1, 3))
    if x.denominator == 1 or (x * 1000).denominator != 1:
        return None
    ans = x * f_ if mult else x / f_
    if (ans * 10 ** 4).denominator != 1 or (base_ := (x * mm if mult else x / mm)).denominator not in (1, 2, 4, 5, 10, 20, 25, 50, 100, 1000, 8, 40, 125, 200, 250, 500):
        return None
    stem = f"Find {dec(x)} {'×' if mult else '÷'} {f_:,}".replace(",", " ") + "."
    base = x * mm if mult else x / mm
    return build(mul_div_ten_powers, stem, ans, [
        (ans / 10 if mult else ans * 10, "moved_point_wrong_way" if False else "moved_point_one_place_too_few", "Moved the decimal point one place the wrong amount."),
        (ans * 10 if mult else ans / 10, "moved_point_one_place_too_many", "Moved the decimal point one place too many."),
        (x / f_ if mult else x * f_, "moved_point_the_wrong_way", "Moved the decimal point in the wrong direction."),
        (base, "forgot_the_powers_of_ten", "Forgot to move the decimal point."),
        (ans + F(1, 10), "slip", "Slip.")],
        [f"{'×' if mult else '÷'} {10 ** k:,}: move the decimal point {k} place{'s' if k > 1 else ''} {'right' if mult else 'left'}.".replace(",", " ")
         + (f" Then {'×' if mult else '÷'} {mm}." if mm > 1 else ""), f"Answer: {dec(ans)}"],
        {"x": [x.numerator, x.denominator], "f": f_, "mult": mult}, dec, auto_slips=False)


@checker(mul_div_ten_powers)
def _(p):
    x = Decimal(p["x"][0]) / Decimal(p["x"][1])
    return F(str(x * p["f"] if p["mult"] else x / p["f"]))


UNITS = [("km", "m", 1000), ("m", "cm", 100), ("kg", "g", 1000), ("l", "ml", 1000)]


@template(T, "basic", DO + "06")
def unit_convert(r):
    big, small, f_ = r.choice(UNITS)
    to_small = r.random() < 0.5
    if to_small:
        x = F(r.randint(11, 999), 100 if f_ == 100 or r.random() < .5 else 1000) if True else None
        if (x * f_).denominator != 1:
            return None
        ans = x * f_
        stem = f"Express {dec(x)} {big} in {small}."
        wrong_ = [(ans * 10, "used_wrong_factor", f"Multiplied by {f_ * 10}."), (ans / 10, "used_wrong_factor", f"Multiplied by {f_ // 10}."),
                  (x / f_, "converted_the_wrong_way", "Divided instead of multiplying."), (ans + 10, "slip", "Slip.")]
        sh = lambda v: f"{dec(v)} {small}".replace(".", ".") if v != int(v) else f"{int(v):,} {small}".replace(",", " ")
        steps = [f"1 {big} = {f_} {small}", f"{dec(x)} × {f_} = {dec(ans)} {small}"]
        prm = {"x": [x.numerator, x.denominator], "f": f_, "to_small": True}
    else:
        n = r.randint(110, 9999)
        x = F(n, f_)
        ans = x
        stem = f"Express {n:,} {small} in {big}.".replace(",", " ")
        wrong_ = [(x * 10, "used_wrong_factor", "Divided by the wrong power of 10."), (x / 10, "used_wrong_factor", "Divided by the wrong power of 10."),
                  (F(n * f_), "converted_the_wrong_way", "Multiplied instead of dividing."), (x + F(1, 10), "slip", "Slip.")]
        sh = lambda v: f"{dec(v)} {big}"
        steps = [f"1 {big} = {f_} {small}", f"{n} ÷ {f_} = {dec(ans)} {big}"]
        prm = {"x": [n, 1], "f": f_, "to_small": False}
    return build(unit_convert, stem, ans, wrong_, steps, prm, sh, auto_slips=False)


@checker(unit_convert)
def _(p):
    x = Decimal(p["x"][0]) / Decimal(p["x"][1])
    return F(str(x * p["f"] if p["to_small"] else x / p["f"]))


@template(T, "basic", DO + "03")
def whole_div_decimal(r):
    b = r.choice([2, 4, 5, 8, 20, 25])
    a = r.randint(5, 99)
    if a % b == 0 or a < b:
        return None
    ans = F(a, b)
    q, rem = divmod(a, b)
    stem = f"Express {a} ÷ {b} as a decimal."
    return build(whole_div_decimal, stem, ans, [
        (q + F(rem, 10), "wrote_remainder_as_tenths", f"Wrote the remainder {rem} after the decimal point."),
        (ans * 10, "misplaced_decimal_point", "Put the decimal point one place too far right."),
        (ans / 10, "misplaced_decimal_point", "Put the decimal point one place too far left."),
        (q + F(rem, b * 10) if False else F(q), "ignored_remainder", "Gave the quotient only."),
        (ans + F(1, 10), "slip", "Slip.")],
        [f"{a} ÷ {b} = {q} remainder {rem}", f"Keep dividing with zeros after the decimal point: {dec(ans)}"], {"a": a, "b": b}, dec, auto_slips=False)


@checker(whole_div_decimal)
def _(p):
    return F(str(Decimal(p["a"]) / Decimal(p["b"])))


# ================================================================ OPERATIONS: intermediate

@template(T, "intermediate", DO + "01", DO + "02")
def pieces_left(r):
    x = r.choice(NAMES)
    n = r.randint(3, 9)
    p_ = r.randint(105, 399)
    left = r.randint(35, 280)
    Tt = n * p_ + left
    ans = H(left)
    thing = r.choice(["ribbon", "rope", "wire"])
    stem = (f"{x} had a roll of {thing} {Tt / 100:.2f} m long. {x} cut {n} pieces, each {p_ / 100:.2f} m long. "
            f"How much {thing} is left, in metres?")
    return build(pieces_left, stem, ans, [
        (H(Tt - p_), "cut_only_one_piece", "Subtracted the length of only one piece."),
        (H(Tt + n * p_), "added_instead_of_subtracted", "Added instead of subtracting."),
        (H(Tt - p_ * n + 10) if False else ans + F(1, 10), "slip", "Slip in the tenths."),
        (ans - F(1, 10), "slip", "Slip in the tenths."), (H(abs(digitwise(Tt, n * p_, "−"))), "subtracted_smaller_digit_from_larger", "Took the smaller digit from the larger.")],
        [f"Cut: {n} × {p_ / 100:.2f} = {n * p_ / 100:.2f} m", f"Left: {Tt / 100:.2f} − {n * p_ / 100:.2f} = {dec(ans)} m"], {"T": Tt, "n": n, "p": p_}, fx(2), auto_slips=False)


@checker(pieces_left)
def _(p):
    rest = F(p["T"], 100)
    for _ in range(p["n"]):
        rest -= F(p["p"], 100)
    return rest


@template(T, "intermediate", DO + "04", DO + "03")
def rounded_share(r):
    d = r.choice([3, 6, 7, 9, 11])
    t = r.randint(25, 99)
    if (t * 10) % d == 0:
        return None
    Tm = F(t, 10)
    x = F(Tm, d)
    ans = rnd(x, 2)
    thing = r.choice(["rope", "ribbon", "pipe"])
    stem = f"A {thing} {t / 10:.1f} m long is cut into {d} equal pieces. What is the length of each piece, correct to 2 decimal places?"
    tr = trunc(x, 2)
    return build(rounded_share, stem, ans, [
        (tr if tr != ans else None, "cut_off_instead_of_rounding", "Cut the decimal off instead of rounding."),
        ((fx(1)(rnd(x, 1)), rnd(x, 1)), "rounded_to_1_decimal_place", "Rounded to 1 decimal place."),
        (F(d, 1) / Tm if False else rnd(F(d) / Tm, 2), "divided_the_wrong_way", "Divided the number of pieces by the length."),
        (ans + F(1, 100), "rounding_slip", "Rounded up when it should round down."), (ans - F(1, 100), "rounding_slip", "Slip in the last digit.")],
        [f"{t / 10:.1f} ÷ {d} = {float(x):.4f}…", f"Round to 2 decimal places: {fx(2)(ans)}"], {"t": t, "d": d}, fx(2), auto_slips=False)


@checker(rounded_share)
def _(p):
    q = (Decimal(p["t"]) / 10 / p["d"]).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return F(str(q))


@template(T, "intermediate", DO + "06", DO + "01")
def mixed_units_total(r):
    x = r.choice(NAMES)
    kind = r.choice([("kg", "g", "bag of rice", "mass", 1000), ("l", "ml", "jug of water", "volume", 1000), ("m", "cm", "piece of string", "length", 100)])
    big, small, thing, noun, f_ = kind
    a = F(r.randint(11, 99), 10)
    g = r.randint(11, 99) * 5 if f_ == 1000 else r.randint(11, 99)
    in_small = r.random() < 0.5
    total_small = a * f_ + g
    ans = total_small if in_small else total_small / f_
    stem = (f"A {thing} has a {noun} of {dec(a)} {big}. {x} adds {g} {small} more. What is the total {noun}, in {small if in_small else big}?")
    sh = (lambda v: f"{dec(v)} {small}") if in_small else (lambda v: f"{dec(v)} {big}")
    if in_small:
        wrong = [(a + g, "added_without_converting", f"Added {dec(a)} and {g} without changing units."),
                 (a * f_ // 10 + g if False else a * (f_ // 10) + g, "used_wrong_conversion", f"Used 1 {big} = {f_ // 10} {small}."),
                 (a * f_ * 10 + g, "used_wrong_conversion", f"Used 1 {big} = {f_ * 10} {small}."), (ans + 10, "slip", "Slip.")]
    else:
        wrong = [(a + g, "added_without_converting", f"Added {dec(a)} and {g} without changing units."),
                 (a + F(g, f_ // 10), "used_wrong_conversion", f"Used 1 {big} = {f_ // 10} {small}."),
                 (a + F(g, f_ * 10), "used_wrong_conversion", f"Used 1 {big} = {f_ * 10} {small}."), (ans + F(1, 10), "slip", "Slip.")]
    return build(mixed_units_total, stem, ans, wrong, [f"{g} {small} = {dec(F(g, f_))} {big}", f"Total = {dec(total_small if in_small else total_small / f_)} {small if in_small else big}"],
                 {"a": [a.numerator, a.denominator], "g": g, "f": f_, "in_small": in_small}, sh, auto_slips=False)


@checker(mixed_units_total)
def _(p):
    a = Decimal(p["a"][0]) / Decimal(p["a"][1])
    g = Decimal(p["g"])
    tot = (a * p["f"] + g) if p["in_small"] else (a + g / p["f"])
    return F(str(tot))


@template(T, "intermediate", DO + "01")
def brackets_decimals(r):
    a = r.randint(1500, 3999)
    b = r.randint(305, 799)
    c = r.randint(105, 299)
    plus = r.random() < 0.5
    s = f"{a / 100:.2f} − ({b / 100:.2f} {'+' if plus else '−'} {c / 100:.2f})"
    ans = H(a - (b + c if plus else b - c))
    w1 = H(a - b + c) if plus else H(a - b - c)
    return build(brackets_decimals, f"Find the value of {s}.", ans, [
        (w1, "ignored_the_brackets", "Ignored the brackets."),
        (H(a - b - c) if not plus and False else H(a + b + c if plus else a + b - c), "wrong_operation_with_brackets", "Added the bracket instead of subtracting it."),
        (ans + F(1, 10), "slip", "Slip in the tenths."), (ans - F(1, 10), "slip", "Slip in the tenths."), (ans + 1, "slip", "Slip with borrowing.")],
        ["Work out the brackets first.", f"Answer: {fx(2)(ans)}"], {"a": a, "b": b, "c": c, "plus": plus}, fx(2), auto_slips=False)


@checker(brackets_decimals)
def _(p):
    a, b, c = (Decimal(p[k]) / 100 for k in "abc")
    return F(str(a - (b + c if p["plus"] else b - c)))


@template(T, "intermediate", DO + "02", DO + "06")
def share_convert(r):
    n = r.choice([4, 5, 8, 20, 25])
    kind = r.choice([("kg", "g", "bag of flour"), ("l", "ml", "bottle of juice")])
    big, small, thing = kind
    each = r.randint(15, 240) * (5 if n in (8, 25) else 1)
    Tt = F(each * n, 1000)
    if Tt.denominator > 100:
        return None
    ans = each
    stem = f"A {thing} of {dec(Tt)} {big} is shared equally among {n} people. How many {small} does each person get?"
    return build(share_convert, stem, ans, [
        (F(each, 1000), "forgot_to_convert", f"Gave the answer in {big}."),
        (each * 10, "used_wrong_conversion", f"Used 1 {big} = {10000} {small}."), (F(each, 10), "used_wrong_conversion", f"Used 1 {big} = 100 {small}."),
        (each + 10, "slip", "Slip.")],
        [f"{dec(Tt)} {big} ÷ {n} = {dec(Tt / n)} {big}", f"{dec(Tt / n)} {big} = {each} {small}"], {"T": [Tt.numerator, Tt.denominator], "n": n},
        lambda v: f"{dec(v)} {small}" , auto_slips=False)


@checker(share_convert)
def _(p):
    return F(str(Decimal(p["T"][0]) / Decimal(p["T"][1]) * 1000 / p["n"]))


@template(T, "intermediate", DO + "02", DO + "01")
def unit_scaling(r):
    k, m = r.sample(range(3, 13), 2)
    if k == m:
        return None
    u = r.randint(5, 99)
    Tot = F(u * k, 10)
    what = r.choice(["bags of sand", "boxes of books", "cartons of milk"])
    ans = F(u * m, 10)
    stem = f"{k} identical {what} have a mass of {dec(Tot)} kg altogether. What is the mass of {m} such {what}, in kg?"
    return build(unit_scaling, stem, ans, [
        (F(u, 10), "found_one_unit_only", "Found the mass of one and stopped."),
        (Tot * m, "multiplied_total_by_m", "Multiplied the total by the new number."),
        (Tot + (m - k), "added_the_difference", f"Added {m - k} to the total."),
        (ans + F(1, 10), "slip", "Slip."), (ans - F(1, 10), "slip", "Slip.")],
        [f"1 = {dec(Tot)} ÷ {k} = {dec(F(u, 10))} kg", f"{m} × {dec(F(u, 10))} = {dec(ans)} kg"], {"u": u, "k": k, "m": m}, dec, auto_slips=False)


@checker(unit_scaling)
def _(p):
    return F(str(Decimal(p["u"]) / 10 * p["m"]))


# ================================================================ OPERATIONS: competent

@template(T, "competent", DO + "02", DO + "06")
def bottles_filled(r):
    L = F(r.randint(60, 250), 10)
    ml = r.choice([250, 350, 150, 450, 120, 180])
    full = int(L * 1000) // ml
    if (L * 1000) % ml == 0:
        return None
    stem = f"A tank has {dec(L)} litres of water. The water is poured into bottles that each hold {ml} ml. How many bottles can be completely filled?"
    return build(bottles_filled, stem, full, [
        (full + 1, "rounded_up", "Counted the bottle that is not full."),
        (int(L * 100) // ml if int(L * 100) // ml else None, "used_wrong_conversion", "Used 1 litre = 100 ml."),
        (int(L * 10000) // ml, "used_wrong_conversion", "Used 1 litre = 10 000 ml."),
        (full - 1, "slip", "Off by 1.")],
        [f"{dec(L)} l = {int(L * 1000)} ml", f"{int(L * 1000)} ÷ {ml} = {full} remainder {int(L * 1000) % ml}", f"Full bottles = {full}"],
        {"L": [L.numerator, L.denominator], "ml": ml}, str, whole=True, auto_slips=False)


@checker(bottles_filled)
def _(p):
    total = int(F(*p["L"]) * 1000)
    n, used = 0, 0
    while used + p["ml"] <= total:
        used += p["ml"]
        n += 1
    return F(n)


@template(T, "competent", DO + "01", DO + "02")
def jug_backwards(r):
    x = r.choice(NAMES)
    n = r.randint(3, 6)
    c = r.randint(20, 60) * 5
    spill = r.randint(20, 90)
    rem = r.randint(60, 250)
    start = rem + n * c + spill
    ans = H(start)
    stem = (f"A container had some water. {x} used {n} pails of {c / 100:.2f} litres each to water the plants, and then {spill / 100:.2f} litres were spilled. "
            f"{rem / 100:.2f} litres were left in the container. How many litres of water were in the container at first?")
    return build(jug_backwards, stem, ans, [
        (H(rem + c + spill), "forgot_to_multiply_cups", "Added the amount of only one pail."),
        (H(rem + n * c), "forgot_the_spill", "Forgot the water that was spilled."),
        (H(abs(rem - n * c - spill)) if abs(rem - n * c - spill) > 0 else None, "subtracted_instead_of_added", "Subtracted when working backwards."),
        (ans + F(1, 10), "slip", "Slip."), (ans - F(1, 10), "slip", "Slip.")],
        [f"Poured: {n} × {c / 100:.2f} = {n * c / 100:.2f} l", f"At first: {rem / 100:.2f} + {spill / 100:.2f} + {n * c / 100:.2f} = {fx(2)(ans)} l"],
        {"n": n, "c": c, "spill": spill, "rem": rem}, fx(2), auto_slips=False)


@checker(jug_backwards)
def _(p):
    v = F(p["rem"], 100)
    v += F(p["spill"], 100)
    for _ in range(p["n"]):
        v += F(p["c"], 100)
    return v


@template(T, "competent", DO + "02", DO + "01")
def ribbon_remaining_pieces(r):
    x = r.choice(NAMES)
    n, pa, pb, k = r.randint(2, 5), r.randint(105, 250), r.choice([15, 20, 25, 35, 45]), r.randint(5, 18)
    Tt = n * pa + k * pb
    stem = (f"{x} had a ribbon {Tt / 100:.2f} m long. {x} cut {n} pieces of {pa / 100:.2f} m each. "
            f"The rest was cut into pieces of {pb / 100:.2f} m each. How many of these shorter pieces were there?")
    return build(ribbon_remaining_pieces, stem, k, [
        (Tt // pb, "forgot_the_first_cuts", "Divided the whole length by the short piece."),
        ((Tt - pa) // pb, "subtracted_one_long_piece_only", "Subtracted only one long piece."),
        (k + n, "added_the_pieces", "Added the numbers of pieces."),
        (k + 1, "slip", "Off by 1."), (k - 1, "slip", "Off by 1.")],
        [f"Long pieces: {n} × {pa / 100:.2f} = {n * pa / 100:.2f} m", f"Rest: {Tt / 100:.2f} − {n * pa / 100:.2f} = {k * pb / 100:.2f} m", f"{k * pb / 100:.2f} ÷ {pb / 100:.2f} = {k}"],
        {"T": Tt, "n": n, "pa": pa, "pb": pb}, str, whole=True, auto_slips=False)


@checker(ribbon_remaining_pieces)
def _(p):
    rest = p["T"] - p["n"] * p["pa"]
    c = 0
    while rest >= p["pb"]:
        rest -= p["pb"]
        c += 1
    return F(c)


@template(T, "competent", DO + "01", DO + "02")
def sum_and_difference_decimals(r):
    y = r.randint(250, 1800)
    d = r.randint(105, 900)
    Sx = 2 * y + d
    x, z = two_names(r)
    big = r.random() < 0.5
    ans = H(y + d) if big else H(y)
    item = r.choice([("mass", "kg", "bag"), ("length", "m", "rope")])
    stem = (f"{x}'s {item[2]} and {z}'s {item[2]} have a total {item[0]} of {Sx / 100:.2f} {item[1]}. {x}'s is {d / 100:.2f} {item[1]} more than {z}'s. "
            f"What is the {item[0]} of {x if big else z}'s {item[2]}, in {item[1]}?")
    return build(sum_and_difference_decimals, stem, ans, [
        (H(Sx) / 2, "halved_the_total", "Divided the total by 2 only."),
        (H(Sx - d) if big else H(Sx + d) / 2, "subtracted_without_halving", "Subtracted the difference without halving."),
        (H(y) if big else H(y + d), "gave_the_other_person", "Gave the other person's amount."),
        (ans + F(1, 10), "slip", "Slip."), (ans - F(1, 10), "slip", "Slip.")],
        [f"Two equal parts: {Sx / 100:.2f} − {d / 100:.2f} = {(Sx - d) / 100:.2f}", f"{z}'s = {(Sx - d) / 200:.2f}", f"{x}'s = {(Sx + d) / 200:.2f}"],
        {"S": Sx, "d": d, "big": big}, fx(2), auto_slips=False)


@checker(sum_and_difference_decimals)
def _(p):
    for y in range(1, p["S"]):
        if y + (y + p["d"]) == p["S"]:
            return F(y + p["d"] if p["big"] else y, 100)


@template(T, "basic", DN + "01", DN + "03")
def decimal_as_units(r):
    """math-pat-place-value-decimals"""
    dp_ = r.choice([1, 2, 3])
    n = r.randint(105, 9999)
    if n % 10 == 0:
        return None
    x = F(n, 10 ** dp_)
    unit = {1: "tenths", 2: "hundredths", 3: "thousandths"}[dp_]
    stem = f"How many {unit} are there in {dec(x)}?"
    return build(decimal_as_units, stem, n, [
        (n * 10, "used_one_place_too_many", f"Counted in the next smaller place value."),
        (F(n, 10), "used_one_place_too_few", "Counted in the next larger place value."),
        (n % 10 ** dp_ if n % 10 ** dp_ else None, "counted_decimal_digits_only", "Counted only the digits after the decimal point."),
        (n + 10, "slip", "Slip."), (n + 1, "slip", "Slip.")],
        [f"{dec(x)} = {n}/{10 ** dp_}", f"So there are {n} {unit}."], {"n": n, "dp": dp_}, whole=True, show=lambda v: f"{int(v)}", auto_slips=False)


@checker(decimal_as_units)
def _(p):
    return F(str(Decimal(p["n"]) / 10 ** p["dp"] * 10 ** p["dp"]))
