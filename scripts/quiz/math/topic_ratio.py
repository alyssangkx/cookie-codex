"""Ratio (math-ratio): generators for basic, intermediate and competent levels."""
from common import *

T = "math-ratio"
O = "math-ratio-ratio-"
NOTATION, EQUIV, DIVIDE, SIMPLEST, FIND, MISSING, FRAC_REL = (O + f"0{i}" for i in range(1, 8))


def ratio_text(*xs):
    return " : ".join(str(x) for x in xs)


def simplify(*xs):
    g = 0
    for x in xs:
        g = gcd(g, x)
    return tuple(x // g for x in xs)


def brute(pred, hi=5000):
    return next((n for n in range(1, hi + 1) if pred(n)), None)


# Ratio options are not single numbers, so each ratio option is (display, code) where
# code = a*10^6 + b*10^3 + c encodes the ratio for the distinctness check.
def rcode(*xs):
    v = 0
    for x in xs:
        v = v * 1000 + x
    return v


def ropt(*xs):
    return (ratio_text(*xs), rcode(*xs))


# ---------------------------------------------------------------- basic

@template(T, "basic", SIMPLEST)
def simplest_ratio(r):
    """math-pat-ratio-express-and-equivalent"""
    n = r.choice([2, 3])
    base = simplify(*[r.randint(1, 9) for _ in range(n)])
    if len(set(base)) < n:
        return None
    k = r.choice([4, 6, 8, 9, 10, 12])
    big = tuple(x * k for x in base)
    f = next(f for f in range(2, k) if k % f == 0)
    part = tuple(x // f for x in big)
    stem = f"Express {ratio_text(*big)} in its simplest form."
    swapped = tuple(reversed(base))
    return build(simplest_ratio, stem, rcode(*base), [
        (ropt(*part), "stopped_before_simplest", f"Divided by {f} but not by the HCF {k}."),
        (ropt(*swapped), "reversed_order", "Wrote the terms in the wrong order."),
        (ropt(*[x // k if i < len(big) - 1 else x // f for i, x in enumerate(big)]),
         "divided_terms_by_different_numbers", f"Divided the last term by {f} instead of {k}."),
        (ropt(*(base[:-1] + (base[-1] + 1,))), "slip_in_last_term", "Made a slip dividing the last term."),
    ], [f"HCF of {', '.join(map(str, big))} is {k}.", f"Divide each term by {k}: {ratio_text(*base)}"],
        {"terms": list(big)}, lambda c: ratio_text(*base) if c == rcode(*base) else "?")


@checker(simplest_ratio)
def _(p):
    return F(rcode(*simplify(*p["terms"])))


@template(T, "basic", DIVIDE)
def divide_in_ratio(r):
    a, b = simplify(r.randint(1, 9), r.randint(1, 9))
    if a == b:
        return None
    m = r.randint(3, 20)
    Q = (a + b) * m
    big = max(a, b)
    x, y = two_names(r)
    stem = f"{x} and {y} share ${Q} in the ratio {a} : {b}. How much does the person with the larger share get?"
    return build(divide_in_ratio, stem, big * m, [
        (m, "found_one_unit_only", f"Found 1 unit (${Q} ÷ {a + b}) but did not multiply."),
        (min(a, b) * m, "gave_smaller_share", "Gave the smaller share."),
        (F(Q, big) if Q % big == 0 else None, "divided_by_ratio_term", f"Divided ${Q} by {big}."),
    ], [f"Total units = {a} + {b} = {a + b}", f"1 unit = ${Q} ÷ {a + b} = ${m}",
        f"Larger share = {big} × ${m} = ${big * m}"], {"a": a, "b": b, "Q": Q}, money, unit_size=m, whole=True)


@checker(divide_in_ratio)
def _(p):
    # brute force: find the larger share s with s : (Q - s) = max : min
    hi, lo = max(p["a"], p["b"]), min(p["a"], p["b"])
    return F(brute(lambda s: s * lo == (p["Q"] - s) * hi))


@template(T, "basic", MISSING)
def missing_term(r):
    """math-pat-ratio-express-and-equivalent"""
    a, b = simplify(r.randint(2, 9), r.randint(2, 9))
    if a == b:
        return None
    k = r.randint(2, 9)
    c, ans = a * k, b * k
    stem = f"Find the missing number: {a} : {b} = {c} : ?"
    return build(missing_term, stem, ans, [
        (b + (c - a), "added_the_difference", f"Added {c - a} to {b} instead of multiplying by {k}."),
        (F(a * c, b) if (a * c) % b == 0 else None, "multiplied_wrong_terms", f"Worked out {c} × {a} ÷ {b}."),
        (c - (a - b) if c - (a - b) > 0 else None, "kept_same_difference", "Kept the difference between the terms the same."),
    ], [f"{c} = {a} × {k}", f"Missing number = {b} × {k} = {ans}"], {"a": a, "b": b, "c": c}, unit_size=b, whole=True)


@checker(missing_term)
def _(p):
    return F(brute(lambda x: p["a"] * x == p["b"] * p["c"]))


@template(T, "basic", FIND)
def ratio_with_units(r):
    """math-pat-ratio-express-and-equivalent"""
    mins = r.choice([15, 20, 25, 30, 35, 40, 45, 50])
    hrs = r.randint(1, 4)
    a, b = simplify(mins, hrs * 60)
    stem = f"Find the ratio of {plural(mins, 'minute')} to {plural(hrs, 'hour')}. Give your answer in its simplest form."
    return build(ratio_with_units, stem, rcode(a, b), [
        (ropt(*simplify(mins, hrs)), "forgot_to_convert_units", f"Compared {mins} with {hrs} without changing hours to minutes."),
        (ropt(b, a), "reversed_order", "Wrote the terms in the wrong order."),
        (ropt(*simplify(mins, hrs * 100)), "used_100_minutes_in_an_hour", "Used 100 minutes in an hour."),
        (ropt(mins, hrs * 60) if (mins, hrs * 60) != (a, b) else None, "did_not_simplify", "Did not simplify."),
    ], [f"{hrs} h = {hrs * 60} min", f"{mins} : {hrs * 60} = {a} : {b}"], {"mins": mins, "hrs": hrs},
        lambda c: ratio_text(a, b))


@checker(ratio_with_units)
def _(p):
    return F(rcode(*simplify(p["mins"], p["hrs"] * 60)))


@template(T, "basic", FRAC_REL)
def ratio_to_fraction(r):
    """math-pat-ratio-fraction-conversion"""
    a, b = simplify(r.randint(1, 9), r.randint(1, 9))
    if a == b:
        return None
    x, y = r.sample(["red beads", "blue beads", "green beads", "yellow beads"], 2)
    stem = f"The ratio of {x} to {y} in a box is {a} : {b}. What fraction of the beads are {x}?"
    show = lambda v: frac(v, mixed=False)
    return build(ratio_to_fraction, stem, F(a, a + b), [
        (F(a, b), "used_other_part_as_whole", f"Wrote {a}/{b}, comparing with {y} instead of all the beads."),
        (F(b, a + b), "found_fraction_of_other_colour", f"Found the fraction of {y}."),
        (F(b, a), "inverted_ratio", f"Wrote {b}/{a}."),
    ], [f"Total units = {a} + {b} = {a + b}", f"Fraction of {x} = {a}/{a + b}"], {"a": a, "b": b}, show)


@checker(ratio_to_fraction)
def _(p):
    return F(p["a"]) / (p["a"] + p["b"])


# ---------------------------------------------------------------- intermediate

@template(T, "intermediate", DIVIDE, FIND)
def ratio_difference_to_total(r):
    """math-pat-ratio-difference-find-total"""
    a, b = simplify(r.randint(2, 9), r.randint(1, 8))
    if a <= b or a - b == 1 and r.random() < 0.5:
        return None
    m = r.randint(3, 15)
    D, total = (a - b) * m, (a + b) * m
    x, y = two_names(r)
    stem = (f"The ratio of {x}'s marbles to {y}'s marbles is {a} : {b}. {x} has {D} more marbles than {y}. "
            f"How many marbles do they have altogether?")
    return build(ratio_difference_to_total, stem, total, [
        (D * (a + b), "treated_difference_as_one_unit", f"Took {D} as 1 unit."),
        (a * m, "gave_first_person_only", f"Gave {x}'s marbles only."),
        (D + b * m, "added_difference_to_smaller", "Added the difference to the smaller amount only."),
        (b * m, "gave_second_person_only", f"Gave {y}'s marbles only."),
    ], [f"Difference = {a} − {b} = {plural(a - b, 'unit')} → {D}", f"1 unit = {D} ÷ {a - b} = {m}",
        f"Altogether = {a + b} × {m} = {total}"], {"a": a, "b": b, "D": D}, unit("marbles"), unit_size=m, whole=True)


@checker(ratio_difference_to_total)
def _(p):
    A = brute(lambda A: A > p["D"] and (A - p["D"]) * p["a"] == A * p["b"])
    return F(2 * A - p["D"])


@template(T, "intermediate", EQUIV)
def combine_ratios(r):
    a, b = simplify(r.randint(1, 7), r.randint(1, 7))
    c, d = simplify(r.randint(1, 7), r.randint(1, 7))
    if b == c or a == b or c == d:
        return None
    L = lcm(b, c)
    A, B, C = simplify(a * L // b, L, d * L // c)
    if max(A, B, C) > 60:
        return None
    stem = f"The ratio of A to B is {a} : {b}. The ratio of B to C is {c} : {d}. Find the ratio of A to B to C."
    return build(combine_ratios, stem, rcode(A, B, C), [
        (ropt(a, b, d), "joined_without_matching_B", f"Joined the ratios as {a} : {b} : {d} without making B the same."),
        (ropt(*simplify(a * c, b * c, d * b)) if (a * c, b * c, d * b) != (A, B, C) else None,
         "scaled_with_wrong_factors", "Multiplied the ratios by the wrong numbers."),
        (ropt(a * c, L, d), "scaled_only_first_ratio", "Changed the first ratio but not the second."),
        (ropt(C, B, A), "reversed_order", "Wrote the ratio backwards."),
    ], [f"Make B the same: LCM of {b} and {c} is {L}",
        f"A : B = {a * L // b} : {L}, B : C = {L} : {d * L // c}", f"A : B : C = {ratio_text(A, B, C)}"],
        {"a": a, "b": b, "c": c, "d": d}, lambda v: ratio_text(A, B, C))


@checker(combine_ratios)
def _(p):
    # B = b*c units: A = a*c, C = d*b, then simplify (a different route from using the LCM)
    return F(rcode(*simplify(p["a"] * p["c"], p["b"] * p["c"], p["d"] * p["b"])))


@template(T, "intermediate", DIVIDE, FRAC_REL)
def part_to_total(r):
    a, b = simplify(r.randint(2, 9), r.randint(2, 9))
    if a == b:
        return None
    m = r.randint(3, 12)
    girls, total = b * m, (a + b) * m
    stem = f"The ratio of boys to girls in a choir is {a} : {b}. There are {girls} girls. How many children are in the choir?"
    return build(part_to_total, stem, total, [
        (girls * (a + b), "did_not_find_one_unit", f"Multiplied {girls} by {a + b} without finding 1 unit."),
        (a * m, "gave_number_of_boys", "Gave the number of boys."),
        (F(girls * (a + b), a), "used_wrong_part", f"Took {girls} as {plural(a, 'unit')}."),
        (girls + a, "added_ratio_term", f"Added {a} to {girls}."),
    ], [f"{plural(b, 'unit')} → {girls}", f"1 unit = {girls} ÷ {b} = {m}", f"Total = {a + b} × {m} = {total}"],
        {"a": a, "b": b, "girls": girls}, unit("children"), unit_size=m, whole=True)


@checker(part_to_total)
def _(p):
    boys = brute(lambda x: x * p["b"] == p["girls"] * p["a"])
    return F(boys + p["girls"])


@template(T, "intermediate", DIVIDE, weight=2)
def three_way_share(r):
    """math-pat-ratio-total-find-part"""
    a, b, c = simplify(*sorted(r.sample(range(1, 10), 3)))
    m = r.randint(2, 12)
    Q = (a + b + c) * m
    stem = (f"${Q} is shared among three friends in the ratio {a} : {b} : {c}. "
            f"How much more does the person with the largest share get than the person with the smallest share?")
    return build(three_way_share, stem, (c - a) * m, [
        (c * m, "gave_largest_share", "Gave the largest share instead of the difference."),
        (m, "found_one_unit_only", "Found 1 unit only."),
        ((c - b) * m, "compared_wrong_shares", "Compared the largest with the middle share."),
        (c - a, "used_ratio_terms_as_amounts", "Subtracted the ratio terms without finding 1 unit."),
    ], [f"Total units = {a + b + c}", f"1 unit = ${Q} ÷ {a + b + c} = ${m}",
        f"Difference = ({c} − {a}) × ${m} = ${(c - a) * m}"], {"a": a, "b": b, "c": c, "Q": Q}, money, unit_size=m, whole=True)


@checker(three_way_share)
def _(p):
    u = F(p["Q"], p["a"] + p["b"] + p["c"])
    return u * p["c"] - u * p["a"]


# ---------------------------------------------------------------- competent

@template(T, "competent", EQUIV, DIVIDE)
def transfer_total_unchanged(r):
    """math-pat-ratio-transfer-constant-total"""
    a, b = simplify(r.randint(2, 9), r.randint(1, 9))
    c, d = simplify(r.randint(1, 9), r.randint(1, 9))
    if F(c, d) >= F(a, b):
        return None
    L = lcm(a + b, c + d)
    k1, k2 = L // (a + b), L // (c + d)
    dx = a * k1 - c * k2  # units moved
    if dx <= 0 or L > 60:
        return None
    u = r.randint(2, 10)
    A0, B0, x = a * k1 * u, b * k1 * u, dx * u
    p_, q_ = two_names(r)
    stem = (f"The ratio of {p_}'s cards to {q_}'s cards was {a} : {b}. After {p_} gave {x} cards to {q_}, "
            f"the ratio became {c} : {d}. How many cards did {p_} have at first?")
    return build(transfer_total_unchanged, stem, A0, [
        (A0 - x, "gave_amount_after_transfer", f"Gave {p_}'s cards after giving some away."),
        (B0, "gave_other_person", f"Gave {q_}'s cards at first."),
        (A0 + B0, "gave_total", "Gave the total number of cards."),
        (F(x * a, a - c) if a > c else None, "compared_terms_without_matching_totals",
         "Compared the ratios without making the totals the same."),
    ], [f"The total does not change. Make the totals equal: {a + b} and {c + d} → {plural(L, 'unit')}",
        f"Before {a * k1} : {b * k1}, after {c * k2} : {d * k2}",
        f"{p_} lost {plural(dx, 'unit')} → {x} cards, so 1 unit = {u}", f"{p_} at first = {a * k1} × {u} = {A0}"],
        {"a": a, "b": b, "c": c, "d": d, "x": x}, unit("cards"), unit_size=u, whole=True)


@checker(transfer_total_unchanged)
def _(p):
    def ok(A0):
        if (A0 * p["b"]) % p["a"]:
            return False
        B0 = A0 * p["b"] // p["a"]
        return A0 > p["x"] and (A0 - p["x"]) * p["d"] == (B0 + p["x"]) * p["c"]
    return F(brute(ok))


@template(T, "competent", EQUIV)
def one_quantity_unchanged(r):
    """math-pat-ratio-one-quantity-constant math-pat-ratio-one-changes-other-constant"""
    a, b = simplify(r.randint(1, 8), r.randint(2, 9))
    c, d = simplify(r.randint(2, 9), r.randint(1, 9))
    if F(c, d) <= F(a, b):
        return None
    L = lcm(b, d)
    A_units, A2_units = a * L // b, c * L // d
    if L > 40:
        return None
    u = r.randint(2, 8)
    x = (A2_units - A_units) * u
    total0 = (A_units + L) * u
    stem = (f"The ratio of red balloons to blue balloons at a party was {a} : {b}. After {x} more red balloons "
            f"were added, the ratio became {c} : {d}. How many balloons were there at first?")
    return build(one_quantity_unchanged, stem, total0, [
        (total0 + x, "gave_total_after", "Gave the total after the red balloons were added."),
        (A_units * u, "gave_red_only", "Gave the red balloons at first only."),
        (L * u, "gave_blue_only", "Gave the blue balloons only."),
        (F(x * (a + b), c - a) if c > a else None, "compared_terms_without_matching_blue",
         "Compared the ratios without keeping the blue balloons the same."),
    ], [f"Blue does not change. Make blue the same: {b} and {d} → {plural(L, 'unit')}",
        f"Before {A_units} : {L}, after {A2_units} : {L}",
        f"Red increased by {plural(A2_units - A_units, 'unit')} → {x}, so 1 unit = {u}",
        f"At first = ({A_units} + {L}) × {u} = {total0}"],
        {"a": a, "b": b, "c": c, "d": d, "x": x}, unit("balloons"), unit_size=u, whole=True)


@checker(one_quantity_unchanged)
def _(p):
    def ok(R):
        if (R * p["b"]) % p["a"]:
            return False
        B = R * p["b"] // p["a"]
        return (R + p["x"]) * p["d"] == B * p["c"]
    R = brute(ok)
    return F(R + R * p["b"] // p["a"])


@template(T, "competent", EQUIV)
def ages_constant_difference(r):
    """math-pat-ratio-same-amount-both-change"""
    a, b = simplify(r.randint(3, 9), r.randint(1, 4))
    c, d = simplify(r.randint(2, 9), r.randint(1, 6))
    if not (a > b and c > d and F(c, d) < F(a, b)):
        return None
    L = lcm(a - b, c - d)
    now_units, later_units = a * L // (a - b), c * L // (c - d)
    if later_units <= now_units:
        return None
    u = r.randint(1, 4)
    A, B, n = now_units * u, b * L // (a - b) * u, (later_units - now_units) * u
    if A > 70 or A < 8 or n > 30 or n < 2:  # n = 1 would read "in 1 years' time"
        return None
    x, y = two_names(r)
    stem = (f"The ratio of {x}'s age to {y}'s age is {a} : {b}. In {n} years' time, the ratio will be "
            f"{c} : {d}. How old is {x} now?")
    return build(ages_constant_difference, stem, A, [
        (A + n, "gave_age_in_future", f"Gave {x}'s age in {n} years' time."),
        (B, "gave_other_person", f"Gave {y}'s age."),
        (F(n * a, c - a) if c > a else (F(n * a, a - c) if a != c else None), "compared_terms_without_matching_difference",
         "Compared the ratios without keeping the age difference the same."),
        (A + B, "gave_total", "Gave the sum of their ages."),
    ], [f"The age difference does not change. Make it the same: {a - b} and {c - d} → {plural(L, 'unit')}",
        f"Now {now_units} : {b * L // (a - b)}, later {later_units} : {d * L // (c - d)}",
        f"{plural(later_units - now_units, 'unit')} → {n} years, so 1 unit = {u}", f"{x} now = {now_units} × {u} = {A}"],
        {"a": a, "b": b, "c": c, "d": d, "n": n}, unit("years old"), unit_size=u, whole=True)


@checker(ages_constant_difference)
def _(p):
    def ok(A):
        if (A * p["b"]) % p["a"]:
            return False
        B = A * p["b"] // p["a"]
        return (A + p["n"]) * p["d"] == (B + p["n"]) * p["c"]
    return F(brute(ok, 200))


# ---------------------------------------------------------------- from the top-school paper survey

@template(T, "basic", FRAC_REL)
def fraction_to_ratio(r):
    """math-pat-ratio-fraction-conversion"""
    a, b = simplify(r.randint(1, 9), r.randint(2, 9))
    if a == b:
        return None
    stem = (f"The number of boys in a club is {a}/{b} of the number of girls. "
            f"What is the ratio of the number of boys to the total number of children?")
    return build(fraction_to_ratio, stem, rcode(a, a + b), [
        (ropt(a, b), "gave_boys_to_girls", "Gave boys : girls, not boys : total."),
        (ropt(b, a + b), "gave_girls_to_total", "Gave girls : total."),
        (ropt(*simplify(a, abs(b - a))) if b != a else None, "subtracted_instead_of_added",
         f"Used {b} − {a} for the total."),
        (ropt(a + b, a), "reversed_order", "Wrote the ratio backwards."),
    ], [f"Boys : girls = {a} : {b}", f"Total = {a} + {b} = {plural(a + b, 'unit')}", f"Boys : total = {a} : {a + b}"],
        {"a": a, "b": b}, lambda c: ratio_text(a, a + b))


@checker(fraction_to_ratio)
def _(p):
    return F(rcode(*simplify(p["a"], p["a"] + p["b"])))


@template(T, "intermediate", DIVIDE, EQUIV)
def multiple_and_ratio(r):
    """math-pat-ratio-total-find-part"""
    k = r.randint(2, 4)
    p_, q_ = simplify(r.randint(1, 6), r.randint(1, 6))
    if p_ == q_:
        return None
    A, B, C = simplify(k * p_, p_, q_)
    u = r.randint(2, 15)
    total = (A + B + C) * u
    x, y, z = r.sample(NAMES, 3)
    stem = (f"{x}, {y} and {z} share ${total}. {x} gets {k} times as much as {y}. "
            f"The ratio of {y}'s share to {z}'s share is {p_} : {q_}. How much does {z} get?")
    wrongC = F(total * q_, k + p_ + q_) if (total * q_) % (k + p_ + q_) == 0 else None
    return build(multiple_and_ratio, stem, C * u, [
        (wrongC, "used_multiple_as_ratio_term", f"Took {x} : {y} : {z} as {k} : {p_} : {q_} without matching {y}."),
        (A * u, "gave_first_person", f"Gave {x}'s share."),
        (B * u, "gave_second_person", f"Gave {y}'s share."),
        (F(total, A + B + C), "found_one_unit_only", "Found 1 unit only."),
    ], [f"{y} : {z} = {p_} : {q_}, so {x} = {k} × {p_} = {plural(k * p_, 'unit')}",
        f"{x} : {y} : {z} = {ratio_text(A, B, C)}", f"1 unit = ${total} ÷ {A + B + C} = ${u}",
        f"{z} = {C} × ${u} = ${C * u}"], {"k": k, "p": p_, "q": q_, "total": total}, money,
        unit_size=u, whole=True)


@checker(multiple_and_ratio)
def _(p):
    # brute force on y's share
    for yv in range(1, p["total"]):
        if (yv * p["q"]) % p["p"]:
            continue
        if p["k"] * yv + yv + yv * p["q"] // p["p"] == p["total"]:
            return F(yv * p["q"] // p["p"])


@template(T, "competent", EQUIV, FRAC_REL)
def give_fraction_new_ratio(r):
    """math-pat-ratio-transfer-constant-total (fraction of one person's share is given away)"""
    a, b = simplify(r.randint(2, 9), r.randint(1, 9))
    p_, q_ = coprime_pair(r, 2, 6)
    A1, B1 = simplify(a * (q_ - p_), b * q_ + a * p_)
    x, y = two_names(r)
    stem = (f"The ratio of {x}'s stickers to {y}'s stickers is {a} : {b}. {x} gives {p_}/{q_} of {x}'s stickers "
            f"to {y}. What is the new ratio of {x}'s stickers to {y}'s stickers?")
    naive = (a * q_ - (a + b) * p_, b * q_ + (a + b) * p_)
    return build(give_fraction_new_ratio, stem, rcode(A1, B1), [
        (ropt(*simplify(a * (q_ - p_), b * q_)), "forgot_to_add_to_other_person", f"Took the stickers from {x} but did not add them to {y}."),
        (ropt(*simplify(*naive)) if naive[0] > 0 else None, "took_fraction_of_total", f"Took {p_}/{q_} of all the stickers."),
        (ropt(*simplify(a - p_, b + p_)) if a > p_ and (a - p_, b + p_) != (A1, B1) else None,
         "moved_numerator_as_units", f"Moved {plural(p_, 'unit')} instead of {p_}/{q_} of {x}'s share."),
        (ropt(B1, A1), "reversed_order", "Wrote the ratio backwards."),
    ], [f"Let {x} = {plural(a * q_, 'unit')} and {y} = {plural(b * q_, 'unit')} (multiply by {q_})",
        f"{x} gives {p_}/{q_} × {a * q_} = {plural(a * p_, 'unit')}", f"New: {a * q_ - a * p_} : {b * q_ + a * p_} = {ratio_text(A1, B1)}"],
        {"a": a, "b": b, "p": p_, "q": q_}, lambda c: ratio_text(A1, B1))


@checker(give_fraction_new_ratio)
def _(p):
    A0, B0 = p["a"] * p["q"] * 7, p["b"] * p["q"] * 7  # any common multiple works
    moved = A0 * p["p"] // p["q"]
    return F(rcode(*simplify(A0 - moved, B0 + moved)))


@template(T, "competent", EQUIV)
def square_sides_area(r):
    """math-pat-square-sides-ratio-area-units"""
    a, b = simplify(r.randint(1, 5), r.randint(2, 6))
    if a >= b:
        return None
    u = r.randint(1, 6) ** 2  # area of 1 unit square, so sides stay whole numbers
    small, big = a * a * u, b * b * u
    D = big - small
    stem = (f"The lengths of the sides of two squares are in the ratio {a} : {b}. The difference between their "
            f"areas is {D} cm². What is the area of the bigger square?")
    return build(square_sides_area, stem, big, [
        (F(D * b, b - a), "used_side_ratio_for_areas", f"Used {a} : {b} for the areas instead of {a * a} : {b * b}."),
        (small, "gave_smaller_square", "Gave the area of the smaller square."),
        (big + small, "gave_total_area", "Gave the total area."),
        (F(D, b * b - a * a) * b, "forgot_to_square_units", "Found 1 unit but multiplied by the side ratio term."),
    ], [f"Areas are in the ratio {a}² : {b}² = {a * a} : {b * b}", f"Difference = {plural(b * b - a * a, 'unit')} → {D} cm²",
        f"1 unit = {u} cm²", f"Bigger square = {b * b} × {u} = {big} cm²"], {"a": a, "b": b, "D": D},
        unit("cm²"), unit_size=u, whole=True)


@checker(square_sides_area)
def _(p):
    # brute force over the smaller square's side length
    for s in range(1, 200):
        if (s * p["b"]) % p["a"]:
            continue
        big = (s * p["b"] // p["a"]) ** 2
        if big - s * s == p["D"]:
            return F(big)


# ---------------------------------------------------------------- catalogue v2 (OCR of 209 papers)

from figures import Fig  # noqa: E402


@template(T, "intermediate", FIND, EQUIV)
def triangle_area_shared_height(r):
    """math-pat-ratio-triangle-area-shared-height"""
    m, n = simplify(r.randint(1, 5), r.randint(1, 5))
    if m == n:
        return None
    X = m * r.randint(3, 15)
    ans = X * n // m
    f = Fig(320, 190)
    Bx, Dx, y = 20, 300, 160
    Cx = Bx + (Dx - Bx) * m / (m + n)
    A = (Bx + (Dx - Bx) * 0.35, 30)
    f.poly([(Bx, y), (Dx, y), A])
    f.line(*A, Cx, y)
    for lab, x in (("B", Bx), ("C", Cx), ("D", Dx)):
        f.point_label(x, y, lab, dy=16)
    f.point_label(*A, "A")
    stem = (f"In the figure, B, C and D lie on a straight line and BC : CD = {m} : {n}. The area of triangle ABC is "
            f"{X} cm². What is the area of triangle ACD?")
    return build(triangle_area_shared_height, stem, ans, [
        (F(X * m, n) if (X * m) % n == 0 else None, "inverted_ratio", f"Used CD : BC = {m} : {n} the wrong way round."),
        (X * (m + n) // m, "gave_whole_triangle", "Gave the area of the whole triangle ABD."),
        (X + (n - m) if n > m else None, "added_ratio_difference", "Added the difference in ratio terms to the area."),
        (X // m, "found_one_unit_only", "Found 1 unit of area only."),
    ], ["The triangles share the same height from A, so their areas are in the ratio of their bases.",
        f"{plural(m, 'unit')} → {X} cm², so 1 unit = {X // m} cm²", f"Area ACD = {n} × {X // m} = {ans} cm²"],
        {"m": m, "n": n, "X": X}, unit("cm²"), unit_size=X // m, whole=True, figure=f.svg("Triangle ABD with C on BD"))


@checker(triangle_area_shared_height)
def _(p):
    # area = 1/2 x base x height with a common height h = 2: base BC = m*k, CD = n*k
    for k in range(1, 10000):
        if p["m"] * k == p["X"]:
            return F(p["n"] * k)


@template(T, "competent", DIVIDE, FRAC_REL)
def three_way_share_remainder(r):
    """math-pat-ratio-three-way-share-remainder"""
    f_n, f_d = coprime_pair(r, 3, 6)
    a, b, c = simplify(*sorted(r.sample(range(1, 8), 3)))
    u = r.randint(2, 12) * 5
    rest = (a + b + c) * u
    if (rest * f_d) % (f_d - f_n):
        return None
    total = rest * f_d // (f_d - f_n)
    x, y, z = r.sample(NAMES, 3)
    stem = (f"Mr Lim spent {f_n}/{f_d} of a sum of money. He shared the rest among {x}, {y} and {z} in the ratio "
            f"{a} : {b} : {c}. {z} received ${c * u}. How much money did Mr Lim have at first?")
    return build(three_way_share_remainder, stem, total, [
        (rest, "forgot_the_fraction_spent_first", f"Found the money shared but did not undo the {f_n}/{f_d} spent."),
        (F(rest * (f_d + f_n), f_d), "added_fraction_of_the_rest", f"Added {f_n}/{f_d} of the shared money instead of working back."),
        (F(c * u * (a + b + c), a) * F(f_d, f_d - f_n), "used_wrong_share", f"Took ${c * u} as {x}'s share."),
        (total + u, "miscounted_units", "Counted one unit too many."),
    ], [f"{plural(c, 'unit')} → ${c * u}, so 1 unit = ${u}", f"Money shared = {a + b + c} × ${u} = ${rest}",
        f"Money shared = {f_d - f_n}/{f_d} of the money", f"At first = ${rest} ÷ {f_d - f_n} × {f_d} = ${total}"],
        {"fn": f_n, "fd": f_d, "a": a, "b": b, "c": c, "C": c * u}, money, whole=True)


@checker(three_way_share_remainder)
def _(p):
    def ok(n):
        rest = n - n * F(p["fn"], p["fd"])
        return rest * p["c"] == p["C"] * (p["a"] + p["b"] + p["c"])
    return F(brute(ok, 50000))


# ---------------------------------------------------------------- gap group B: notation and representation of a:b and a:b:c

from figures_gapB import counters, unit_rows  # noqa: E402

COLOURS = ["red", "blue", "green", "yellow", "white", "black"]


def _distinct_terms(r, parts, lo=1, hi=6):
    """parts distinct-ish whole numbers with at least two different values and no ratio that is all equal."""
    while True:
        xs = [r.randint(lo, hi) for _ in range(parts)]
        if len(set(xs)) >= 2:
            return xs


@template(T, "basic", NOTATION)
def counters_two_colours(r):
    """Read a:b from two rows of counters (a model of coloured units), simplest form."""
    a, b = simplify(r.randint(1, 7), r.randint(1, 7))
    if a == b:
        return None
    k = r.choice([1, 1, 2, 3])
    if k * max(a, b) > 14:
        k = 1
    c1, c2 = r.sample(COLOURS, 2)
    name = r.choice(NAMES)
    ra, rb = k * a, k * b
    stem = (f"{name} put {ra + rb} counters in two rows, as shown. "
            f"What is the ratio of the number of {c1} counters to the number of {c2} counters? "
            f"Give your answer in its simplest form.")
    fig = counters([(c1.capitalize(), ra), (c2.capitalize(), rb)], title=f"{ra} {c1} counters and {rb} {c2} counters")
    return build(counters_two_colours, stem, rcode(a, b), [
        (ropt(ra, rb) if k > 1 else None, "stopped_before_simplest", f"Wrote {ra} : {rb} and did not simplify."),
        (ropt(b, a), "reversed_order", "Wrote the ratio the wrong way round."),
        (ropt(a, a + b), "gave_part_to_total", f"Compared {c1} counters with all the counters."),
        (ropt(a + 1, b), "careless_slip", "Miscounted one counter."),
        (ropt(a, b + 1), "careless_slip", "Miscounted one counter."),
    ], [f"{c1.capitalize()}: {ra}, {c2}: {rb}", f"{ra} : {rb} = {a} : {b}"],
        {"ra": ra, "rb": rb}, lambda c: ratio_text(a, b), auto_slips=False, figure=fig)


@checker(counters_two_colours)
def _(p):
    g = next(g for g in range(min(p["ra"], p["rb"]), 0, -1) if p["ra"] % g == 0 and p["rb"] % g == 0)
    return F(rcode(p["ra"] // g, p["rb"] // g))


@template(T, "intermediate", NOTATION)
def counters_three_colours(r):
    """Read a:b:c from three rows of counters, in the order asked."""
    xs = _distinct_terms(r, 3, 1, 6)
    k = r.choice([1, 1, 2])
    cols = r.sample(COLOURS, 3)
    counts = [x * k for x in xs]
    order = r.sample([0, 1, 2], 3)
    if order == [0, 1, 2] and r.random() < 0.7:
        return None
    asked = [counts[i] for i in order]
    ans = simplify(*asked)
    name = r.choice(NAMES)
    stem = (f"{name} arranged {sum(counts)} counters in three rows, as shown. What is the ratio of the number of "
            f"{cols[order[0]]} counters to the number of {cols[order[1]]} counters to the number of "
            f"{cols[order[2]]} counters? Give your answer in its simplest form.")
    fig = counters([(c.capitalize(), n) for c, n in zip(cols, counts)], title="Three rows of counters")
    shown = simplify(*counts)
    return build(counters_three_colours, stem, rcode(*ans), [
        (ropt(*asked) if asked != list(ans) else None, "stopped_before_simplest", "Wrote the counts without simplifying."),
        (ropt(*simplify(*counts)) if list(shown) != list(ans) else None, "used_the_order_of_the_rows", "Wrote the ratio in the order of the rows, not the order asked."),
        (ropt(*ans[::-1]) if ans[::-1] != ans else None, "reversed_order", "Wrote the ratio backwards."),
        (ropt(ans[0], ans[1]), "left_out_a_term", "Wrote only the first two terms."),
        (ropt(ans[0] + 1, ans[1], ans[2]), "careless_slip", "Miscounted one counter."),
    ], [", ".join(f"{cols[i]}: {counts[i]}" for i in order), f"{ratio_text(*asked)} = {ratio_text(*ans)}"],
        {"counts": counts, "order": order}, lambda c: ratio_text(*ans), auto_slips=False, figure=fig)


@checker(counters_three_colours)
def _(p):
    asked = [p["counts"][i] for i in p["order"]]
    g = next(g for g in range(min(asked), 0, -1) if all(x % g == 0 for x in asked))
    return F(rcode(*[x // g for x in asked]))


@template(T, "intermediate", NOTATION)
def counters_part_to_total(r):
    """Read one colour to the total from rows of counters (part : whole as a ratio)."""
    xs = _distinct_terms(r, 3, 1, 6)
    k = r.choice([1, 1, 2])
    cols = r.sample(COLOURS, 3)
    counts = [x * k for x in xs]
    i = r.randrange(3)
    tot = sum(counts)
    a, t = simplify(counts[i], tot)
    name = r.choice(NAMES)
    stem = (f"{name} used {tot} counters to make the three rows shown. What is the ratio of the number of "
            f"{cols[i]} counters to the total number of counters? Give your answer in its simplest form.")
    fig = counters([(c.capitalize(), n) for c, n in zip(cols, counts)], title="Three rows of counters")
    others = tot - counts[i]
    return build(counters_part_to_total, stem, rcode(a, t), [
        (ropt(*simplify(counts[i], others)), "compared_with_the_others_only", f"Compared the {cols[i]} counters with the other counters, not the total."),
        (ropt(t, a), "reversed_order", "Wrote the ratio backwards."),
        (ropt(counts[i], tot) if counts[i] != a else None, "stopped_before_simplest", "Did not simplify."),
        (ropt(*simplify(counts[i], counts[(i + 1) % 3])), "compared_with_one_other_colour", "Compared with only one other colour."),
    ], [f"Total = {' + '.join(str(c) for c in counts)} = {tot}", f"{cols[i].capitalize()} : total = {counts[i]} : {tot} = {a} : {t}"],
        {"counts": counts, "i": i}, lambda c: ratio_text(a, t), auto_slips=False, figure=fig)


@checker(counters_part_to_total)
def _(p):
    part, tot = p["counts"][p["i"]], sum(p["counts"])
    g = next(g for g in range(part, 0, -1) if part % g == 0 and tot % g == 0)
    return F(rcode(part // g, tot // g))


@template(T, "competent", NOTATION)
def units_three_people_total(r):
    """Bar model with a : b : c units; two people's total is given, find the third person's amount."""
    while True:
        a, b, c = [r.randint(1, 6) for _ in range(3)]
        if len({a, b, c}) >= 2 and b not in (a + c,):
            break
    m = r.randint(3, 12)
    T_ = (a + c) * m
    n1, n2, n3 = r.sample(NAMES, 3)
    item = r.choice(["stickers", "marbles", "cards", "stamps"])
    stem = (f"The model shows the number of {item} that {n1}, {n2} and {n3} have. {n1} and {n3} have {T_} {item} "
            f"altogether. How many {item} does {n2} have?")
    fig = unit_rows([(n1.split()[0], a), (n2.split()[0], b), (n3.split()[0], c)], title=f"Bar model with {a}, {b} and {c} equal units")
    ans = b * m
    return build(units_three_people_total, stem, ans, [
        (m, "found_one_unit_only", f"Found 1 unit ({T_} ÷ {a + c} = {m}) but did not multiply by {b}."),
        (F(b * T_, a + b + c), "used_all_the_units", f"Divided {T_} by all {plural(a + b + c, 'unit')} instead of {a + c}."),
        (F(T_ * b, a) if (T_ * b) % a == 0 else None, "compared_with_one_person_only", f"Treated {T_} as {n1}'s amount only."),
        (T_ - ans if T_ - ans != ans else None, "subtracted_from_the_total", f"Subtracted {n2}'s share from {T_}."),
    ], [f"{n1} and {n3}: {a} + {c} = {plural(a + c, 'unit')}", f"1 unit = {T_} ÷ {a + c} = {m}", f"{n2}: {b} × {m} = {ans}"],
        {"a": a, "b": b, "c": c, "T": T_}, unit_size=m, whole=True, figure=fig)


@checker(units_three_people_total)
def _(p):
    # brute force: find the unit size m with (a + c) * m == T, then Ben has b * m
    m = brute(lambda m: (p["a"] + p["c"]) * m == p["T"])
    return F(p["b"] * m)


@template(T, "competent", NOTATION)
def units_difference_total(r):
    """Bar model with a : b : c units; the difference between two people is given, find the total."""
    while True:
        a, b, c = [r.randint(1, 6) for _ in range(3)]
        if b > a:
            break
    m = r.randint(2, 12)
    D = (b - a) * m
    n1, n2, n3 = r.sample(NAMES, 3)
    item = r.choice(["stickers", "marbles", "cards", "stamps"])
    stem = (f"The model shows the number of {item} that {n1}, {n2} and {n3} have. {n2} has {D} more {item} than {n1}. "
            f"How many {item} do the three children have altogether?")
    fig = unit_rows([(n1.split()[0], a), (n2.split()[0], b), (n3.split()[0], c)], title=f"Bar model with {a}, {b} and {c} equal units")
    ans = (a + b + c) * m
    return build(units_difference_total, stem, ans, [
        (D, "gave_the_difference", f"Gave the {D} difference, not the total."),
        (D * (a + b + c), "multiplied_by_total_units", f"Multiplied the difference {D} by all {plural(a + b + c, 'unit')}."),
        ((b + c) * m, "left_out_a_person", f"Left out {n1}'s {item}."),
        (m * (b - a + c), "used_the_wrong_units", "Added the difference in units to the third person's units only."),
    ], [f"{n2} has {b} − {a} = {plural(b - a, 'more unit')}, so {plural(b - a, 'unit')} = {D}", f"1 unit = {D} ÷ {b - a} = {m}",
        f"Total = {a + b + c} × {m} = {ans}"], {"a": a, "b": b, "c": c, "D": D}, unit_size=m, whole=True, figure=fig)


@checker(units_difference_total)
def _(p):
    m = brute(lambda m: (p["b"] - p["a"]) * m == p["D"])
    return F(m * p["a"] + m * p["b"] + m * p["c"])
