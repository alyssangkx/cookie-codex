"""Fractions (math-fractions): generators for basic, intermediate and competent levels."""
from common import *

T = "math-fractions"
O = "math-fractions-"
SIMPLEST = O + "equivalent-fractions-and-simplest-form-02"
ADD = O + "addition-and-subtraction-of-fractions-03"
ADD_MIXED = O + "addition-and-subtraction-of-fractions-04"
MUL_WHOLE = O + "multiplication-and-division-of-fractions-01"
MUL_FRAC = O + "multiplication-and-division-of-fractions-02"
DIV_BY_WHOLE = O + "multiplication-and-division-of-fractions-05"
DIV_BY_FRAC = O + "multiplication-and-division-of-fractions-06"
OF_SET = O + "fraction-of-a-whole-and-of-a-set-03"


def brute(pred, hi=20000):
    """First positive integer n <= hi with pred(n); the independent route for word problems."""
    return next((n for n in range(1, hi + 1) if pred(F(n))), None)


# ---------------------------------------------------------------- basic

@template(T, "basic", SIMPLEST, same_value_ok=True)
def simplest_form(r):
    a, b = coprime_pair(r, 3, 12)
    k = r.choice([4, 6, 8, 9, 10, 12])  # composite, so there is a 'not highest factor' trap
    n, d = a * k, b * k
    f = next(f for f in range(2, k) if k % f == 0)
    show = lambda x: frac(x, mixed=False)
    stem = f"Express {n}/{d} in its simplest form."
    return build(simplest_form, stem, F(a, b), [
        ((f"{n // f}/{d // f}", F(a, b)), "stopped_before_simplest",
         f"Divided by {f}, a common factor, but not by the HCF {k}."),
        (F(a, d), "divided_numerator_only", f"Divided only the numerator by {k}."),
        (F(b, a), "inverted_fraction", "Turned the fraction upside down."),
        (F(n // k, d // f), "divided_by_different_numbers",
         f"Divided the numerator by {k} but the denominator by {f}."),
    ], [f"HCF of {n} and {d} is {k}.", f"{n} ÷ {k} = {a}, {d} ÷ {k} = {b}.", f"{n}/{d} = {a}/{b}"],
        {"n": n, "d": d}, show)


@checker(simplest_form)
def _(p):
    return F(p["n"], p["d"])


@template(T, "basic", ADD)
def add_unlike(r):
    b, d = r.sample(range(2, 13), 2)
    L = lcm(b, d)
    if L > 60:
        return None
    a, c = r.randint(1, b - 1), r.randint(1, d - 1)
    if gcd(a, b) != 1 or gcd(c, d) != 1:
        return None
    ans = F(a, b) + F(c, d)
    stem = f"Find the value of {a}/{b} + {c}/{d}. Give your answer in its simplest form."
    return build(add_unlike, stem, ans, [
        (F(a + c, b + d), "added_numerators_and_denominators", "Added the tops and added the bottoms."),
        (F(a * (L // b) + c, L), "renamed_only_first_fraction",
         f"Changed {a}/{b} to {a * (L // b)}/{L} but did not change the numerator {c} of {c}/{d}."),
        (F(a + c, L), "forgot_to_rename_numerators", f"Used denominator {L} but kept the numerators {a} and {c}."),
        (abs(F(a, b) - F(c, d)), "subtracted_instead_of_added", "Subtracted instead of adding."),
    ], [f"LCM of {b} and {d} is {L}.",
        f"{a}/{b} = {a * L // b}/{L}, {c}/{d} = {c * L // d}/{L}.",
        f"{a * L // b}/{L} + {c * L // d}/{L} = {a * L // b + c * L // d}/{L}"
        + ("" if frac(ans) == f"{a * L // b + c * L // d}/{L}" else f" = {frac(ans)}")],
        {"a": a, "b": b, "c": c, "d": d})


@checker(add_unlike)
def _(p):
    return F(p["a"] * p["d"] + p["c"] * p["b"], p["b"] * p["d"])


@template(T, "basic", MUL_WHOLE)
def frac_times_whole(r):
    """math-pat-fraction-operations-simplest"""
    a, b = coprime_pair(r, 3, 12)
    n = r.randint(2, 15)
    if n % b == 0:
        return None
    ans = F(a * n, b)
    stem = f"Find the value of {a}/{b} × {n}."
    return build(frac_times_whole, stem, ans, [
        (F(a, b * n), "multiplied_denominator", f"Multiplied the denominator by {n} instead of the numerator."),
        (F(a + n, b), "added_whole_to_numerator", f"Added {n} to the numerator."),
        (F(n * b, a), "inverted_fraction", f"Multiplied by {b}/{a} instead of {a}/{b}."),
        (F(a * n, b * n), "multiplied_top_and_bottom", "Multiplied both numerator and denominator by the whole number."),
    ], [f"{a}/{b} × {n} = {a} × {n} / {b} = {a * n}/{b}", f"= {frac(ans)}"], {"a": a, "b": b, "n": n})


@checker(frac_times_whole)
def _(p):
    return F(p["a"], p["b"]) * p["n"]


@template(T, "basic", DIV_BY_WHOLE)
def frac_div_whole(r):
    """math-pat-fraction-operations-simplest"""
    a, b = coprime_pair(r, 2, 9)
    n = r.randint(2, 9)
    ans = F(a, b * n)
    stem = f"Find the value of {a}/{b} ÷ {n}."
    return build(frac_div_whole, stem, ans, [
        (F(a * n, b), "multiplied_instead_of_dividing", f"Multiplied by {n} instead of dividing."),
        (F(b * n, a), "inverted_answer", "Turned the answer upside down."),
        (F(a, b + n), "added_to_denominator", f"Added {n} to the denominator."),
        (F(b, a * n), "inverted_the_fraction_not_the_divisor", f"Flipped {a}/{b} instead of {n}."),
    ], [f"Dividing by {n} is the same as multiplying by 1/{n}.",
        f"{a}/{b} × 1/{n} = {a}/{b * n}", f"= {frac(ans)}"], {"a": a, "b": b, "n": n})


@checker(frac_div_whole)
def _(p):
    return F(p["a"], p["b"]) / p["n"]


@template(T, "basic", DIV_BY_FRAC)
def whole_div_frac(r):
    """math-pat-fraction-operations-simplest"""
    a, b = coprime_pair(r, 2, 9)
    n = r.randint(2, 12)
    ans = F(n * b, a)
    stem = f"Find the value of {n} ÷ {a}/{b}."
    return build(whole_div_frac, stem, ans, [
        (F(n * a, b), "did_not_invert_divisor", f"Multiplied by {a}/{b} instead of {b}/{a}."),
        (F(a, n * b), "inverted_answer", "Turned the answer upside down."),
        (F(n * b), "ignored_numerator", f"Multiplied by {b} but forgot to divide by {a}."),
        (F(n, a), "ignored_denominator", f"Divided by {a} but forgot to multiply by {b}."),
    ], [f"Dividing by {a}/{b} is the same as multiplying by {b}/{a}.",
        f"{n} × {b}/{a} = {n * b}/{a}", f"= {frac(ans)}"], {"a": a, "b": b, "n": n})


@checker(whole_div_frac)
def _(p):
    return p["n"] / F(p["a"], p["b"])


@template(T, "basic", OF_SET)
def fraction_of_quantity(r):
    a, b = coprime_pair(r, 3, 12)
    m = r.randint(2, 12)
    Q = b * m
    thing, show = r.choice([("stamps", unit("stamps")), ("pupils", unit("pupils")), ("dollars", money),
                            ("marbles", unit("marbles"))])
    whole = f"${Q}" if thing == "dollars" else f"{Q} {thing}"
    ans = F(a * m)
    stem = f"What is {a}/{b} of {whole}?"
    return build(fraction_of_quantity, stem, ans, [
        (F(m), "found_one_part_only", f"Divided by {b} but did not multiply by {a}."),
        (F(Q - a * m), "found_the_other_part", f"Found the remaining {b - a}/{b} instead."),
        (F(Q * b, a), "divided_by_the_fraction", f"Divided by {a}/{b} instead of multiplying."),
        (F(Q * a), "multiplied_by_numerator_only", f"Multiplied by {a} but did not divide by {b}."),
    ], [f"1/{b} of {Q} = {Q} ÷ {b} = {m}", f"{a}/{b} of {Q} = {a} × {m} = {a * m}"], {"a": a, "b": b, "Q": Q}, show, unit_size=m, whole=True)


@checker(fraction_of_quantity)
def _(p):
    return F(p["a"], p["b"]) * p["Q"]


# ---------------------------------------------------------------- intermediate

@template(T, "intermediate", ADD_MIXED)
def mixed_subtract_borrow(r):
    a, b = coprime_pair(r, 2, 12)
    c, d = coprime_pair(r, 2, 12)
    if b == d or lcm(b, d) > 36 or F(a, b) >= F(c, d):
        return None
    p, q = r.randint(3, 9), r.randint(1, 2)
    first, second = p + F(a, b), q + F(c, d)
    ans = first - second
    L = lcm(b, d)
    name = r.choice(NAMES)
    stem = (f"A ribbon is {frac(first)} m long. {name} cuts off {frac(second)} m. "
            f"How long is the ribbon that is left?")
    return build(mixed_subtract_borrow, stem, ans, [
        ((p - q) + (F(c, d) - F(a, b)), "subtracted_smaller_fraction_from_larger",
         f"Did {c}/{d} − {a}/{b} because {a}/{b} is smaller, instead of renaming 1 whole."),
        (ans + 1, "forgot_to_take_away_the_borrowed_whole",
         "Renamed 1 whole as a fraction but did not reduce the whole number by 1."),
        ((p - q) + F(abs(a - c), abs(b - d)), "subtracted_numerators_and_denominators",
         "Subtracted tops and bottoms separately."),
        (first + second, "added_instead_of_subtracted", "Added the two lengths."),
    ], [f"{frac(first)} = {p - 1} {(a * L // b) + L}/{L} (rename 1 whole)",
        f"{frac(second)} = {q} {c * L // d}/{L}",
        f"{p - 1} {(a * L // b) + L}/{L} − {q} {c * L // d}/{L} = {frac(ans)} m"],
        {"p": p, "a": a, "b": b, "q": q, "c": c, "d": d}, unit("m"))


@checker(mixed_subtract_borrow)
def _(p):
    return F(p["p"] * p["b"] + p["a"], p["b"]) - F(p["q"] * p["d"] + p["c"], p["d"])


@template(T, "intermediate", MUL_FRAC, OF_SET)
def remainder_left(r):
    """math-pat-fraction-successive-parts"""
    a, b = coprime_pair(r, 3, 8)
    c, d = coprime_pair(r, 2, 6)
    total = b * d * r.randint(2, 8)
    after1 = total - total * F(a, b)
    left = after1 * (1 - F(c, d))
    name = r.choice(NAMES)
    stem = (f"{name} had ${total}. {name} spent {a}/{b} of it on a bag and {c}/{d} of the remainder "
            f"on a book. How much money did {name} have left?")
    return build(remainder_left, stem, left, [
        (total * (1 - F(a, b) - F(c, d)), "took_second_fraction_of_total",
         f"Took {c}/{d} of the whole ${total} instead of the remainder."),
        (after1 * F(c, d), "gave_cost_of_book", "Gave the cost of the book instead of the money left."),
        (after1, "stopped_after_first_step", "Stopped after paying for the bag."),
        (total * F(a, b), "gave_cost_of_bag", "Gave the cost of the bag."),
    ], [f"Bag: {a}/{b} × ${total} = ${total * F(a, b)}", f"Remainder: ${total} − ${total * F(a, b)} = ${after1}",
        f"Book: {c}/{d} × ${after1} = ${after1 * F(c, d)}", f"Left: ${after1} − ${after1 * F(c, d)} = ${left}"],
        {"total": total, "a": a, "b": b, "c": c, "d": d}, money, whole=True)


@checker(remainder_left)
def _(p):
    rem = p["total"] * F(p["b"] - p["a"], p["b"])
    return rem * F(p["d"] - p["c"], p["d"])


@template(T, "intermediate", OF_SET)
def more_boys_than_girls(r):
    """math-pat-fraction-part-difference-find-total"""
    b = r.randint(5, 12)
    a = r.randint(b // 2 + 1, b - 1)
    if gcd(a, b) != 1:
        return None
    m = r.randint(3, 15)
    total, boys, girls = b * m, a * m, (b - a) * m
    D = boys - girls
    stem = (f"{a}/{b} of the pupils in a hall are boys. There are {D} more boys than girls. "
            f"How many pupils are there in the hall?")
    return build(more_boys_than_girls, stem, total, [
        (boys, "gave_number_of_boys", "Found the number of boys only."),
        (F(D * b, a), "treated_difference_as_boys", f"Took {D} as {a}/{b} of the pupils."),
        (D * b, "treated_difference_as_one_part", f"Took {D} as 1/{b} of the pupils."),
        (girls, "gave_number_of_girls", "Found the number of girls only."),
    ], [f"Girls = 1 − {a}/{b} = {b - a}/{b}", f"Difference = {a}/{b} − {b - a}/{b} = {2 * a - b}/{b} → {D} pupils",
        f"1/{b} → {D} ÷ {2 * a - b} = {m}", f"Total = {b} × {m} = {total}"],
        {"a": a, "b": b, "D": D}, unit("pupils"), unit_size=m, whole=True)


@checker(more_boys_than_girls)
def _(p):
    return brute(lambda n: (n * p["a"] / p["b"]).denominator == 1 and
                 n * F(p["a"], p["b"]) - n * F(p["b"] - p["a"], p["b"]) == p["D"])


@template(T, "intermediate", DIV_BY_WHOLE)
def share_into_bags(r):
    """math-pat-fraction-operations-simplest math-pat-fraction-division-share"""
    a, b = coprime_pair(r, 2, 9)
    n = r.randint(2, 9)
    ans = F(a, b * n)
    stem = f"{a}/{b} kg of flour is packed equally into {n} bags. What is the mass of flour in each bag?"
    return build(share_into_bags, stem, ans, [
        (F(a * n, b), "multiplied_instead_of_dividing", f"Multiplied by {n} instead of dividing."),
        (F(n * b, a), "divided_bags_by_flour", f"Worked out {n} ÷ {a}/{b} instead of {a}/{b} ÷ {n}."),
        (F(a, b + n), "added_to_denominator", f"Added {n} to the denominator."),
        (F(b * n, a), "inverted_answer", "Turned the answer upside down."),
    ], [f"{a}/{b} ÷ {n} = {a}/{b} × 1/{n}", f"= {frac(ans)} kg"], {"a": a, "b": b, "n": n}, unit("kg"))


@checker(share_into_bags)
def _(p):
    return F(p["a"], p["b"]) / p["n"]


@template(T, "intermediate", DIV_BY_FRAC)
def how_many_cups(r):
    """math-pat-fraction-divide-by-fraction-pieces"""
    a, b = coprime_pair(r, 3, 10)
    if a == 1:
        return None
    n = a * r.randint(2, 6)
    ans = F(n * b, a)
    stem = f"A jug holds {plural(n, 'litre')} of juice. How many cups of {a}/{b} litre can be filled completely?"
    return build(how_many_cups, stem, ans, [
        (F(n * a, b), "multiplied_instead_of_dividing", f"Worked out {n} × {a}/{b}."),
        (F(n * b), "ignored_numerator", f"Multiplied by {b} but did not divide by {a}."),
        (F(n, a), "ignored_denominator", f"Divided by {a} but did not multiply by {b}."),
        (F(n * b + a), "added_instead_of_divided", "Mixed up the steps."),
    ], [f"{n} ÷ {a}/{b} = {n} × {b}/{a}", f"= {n * b}/{a} = {frac(ans)}"], {"a": a, "b": b, "n": n},
        unit("cups"), whole=True)


@checker(how_many_cups)
def _(p):
    return brute(lambda k: k * F(p["a"], p["b"]) <= p["n"] < (k + 1) * F(p["a"], p["b"]))


@template(T, "intermediate", MUL_FRAC)
def fraction_of_remainder(r):
    a, b = coprime_pair(r, 3, 9)
    c, d = coprime_pair(r, 2, 6)
    ans = F(a, b) * F(c, d)
    name = r.choice(NAMES)
    stem = (f"{a}/{b} of a cake was left after a party. {name} ate {c}/{d} of the cake that was left. "
            f"What fraction of the whole cake did {name} eat?")
    return build(fraction_of_remainder, stem, ans, [
        (F(c, d), "fraction_of_remainder_as_fraction_of_whole", f"Gave {c}/{d}, which is a fraction of the leftover only."),
        (F(a, b) - F(c, d), "subtracted_fractions", f"Worked out {a}/{b} − {c}/{d}."),
        (F(a, b) - ans, "found_what_is_still_left", "Found the fraction of the cake still left."),
        (F(a + c, b + d), "added_numerators_and_denominators", "Added tops and bottoms."),
    ], [f"{c}/{d} of {a}/{b} = {c}/{d} × {a}/{b}", f"= {frac(ans)}"], {"a": a, "b": b, "c": c, "d": d})


@checker(fraction_of_remainder)
def _(p):
    return F(p["a"] * p["c"], p["b"] * p["d"])


# ---------------------------------------------------------------- competent

@template(T, "competent", MUL_FRAC, OF_SET)
def remainder_backwards(r):
    """math-pat-fraction-successive-parts"""
    a, b = coprime_pair(r, 3, 8)
    c, d = coprime_pair(r, 2, 6)
    total = b * d * r.randint(2, 10)
    after1 = total * F(b - a, b)
    left = after1 * F(d - c, d)
    name = r.choice(NAMES)
    stem = (f"{name} spent {a}/{b} of the money in a wallet on a pair of shoes and {c}/{d} of the remaining money "
            f"on a shirt. {name} had ${left} left. How much money was in the wallet at first?")
    naive = 1 - F(a, b) - F(c, d)
    return build(remainder_backwards, stem, total, [
        (left / naive if naive > 0 else None, "took_second_fraction_of_total",
         f"Took {c}/{d} of all the money instead of the remainder."),
        (after1, "worked_back_only_one_step", "Found the money left after the shoes only."),
        (total * F(a, b), "gave_cost_of_shoes", "Gave the cost of the shoes."),
        (left + after1 * F(c, d), "added_shirt_to_money_left", "Added the shirt and the money left, but missed the shoes."),
    ], [f"Money left = {d - c}/{d} of the remainder → ${left}",
        f"Remainder = ${left} ÷ {d - c} × {d} = ${after1}",
        f"Remainder = {b - a}/{b} of the money → ${after1}",
        f"At first = ${after1} ÷ {b - a} × {b} = ${total}"],
        {"a": a, "b": b, "c": c, "d": d, "left": int(left)}, money,
        unit_size=total // b, whole=True)


@checker(remainder_backwards)
def _(p):
    def ok(n):
        rem = n - n * F(p["a"], p["b"])
        return rem - rem * F(p["c"], p["d"]) == p["left"]
    return brute(ok)


@template(T, "competent", MUL_FRAC, OF_SET)
def book_more_than_pen(r):
    """math-pat-fraction-successive-parts"""
    a, b = coprime_pair(r, 3, 8)
    c, d = coprime_pair(r, 2, 6)
    diff_frac = F(a, b) - F(c, d) * F(b - a, b)
    if diff_frac <= 0:
        return None
    M = b * d * r.randint(1, 8)
    D = diff_frac * M
    if D.denominator != 1 or M > 600:
        return None
    book, pen = M * F(a, b), M * F(b - a, b) * F(c, d)
    name = r.choice(NAMES)
    stem = (f"{name} spent {a}/{b} of a sum of money on a book and {c}/{d} of the remainder on a pen. "
            f"The book cost ${D} more than the pen. How much money did {name} have at first?")
    naive = F(a, b) - F(c, d)
    return build(book_more_than_pen, stem, M, [
        (D / naive if naive > 0 else None, "took_second_fraction_of_total",
         f"Took the pen as {c}/{d} of all the money."),
        (book, "gave_cost_of_book", "Gave the cost of the book."),
        (M - book, "gave_remainder_after_book", "Gave the money left after buying the book."),
        (M - book - pen, "gave_money_left", "Gave the money left at the end."),
    ], [f"Pen = {c}/{d} × {b - a}/{b} = {frac(F(c, d) * F(b - a, b))} of the money",
        f"Book − pen = {a}/{b} − {frac(F(c, d) * F(b - a, b))} = {frac(diff_frac)} of the money",
        f"{frac(diff_frac)} → ${D}", f"Money at first = ${D} ÷ {frac(diff_frac)} = ${M}"],
        {"a": a, "b": b, "c": c, "d": d, "D": int(D)}, money,
        unit_size=M // (b * d), whole=True)


@checker(book_more_than_pen)
def _(p):
    def ok(n):
        book = n * F(p["a"], p["b"])
        pen = (n - book) * F(p["c"], p["d"])
        return book - pen == p["D"]
    return brute(ok)


@template(T, "competent", MUL_FRAC)
def equal_fractions(r):
    """math-pat-fraction-same-share-two-quantities"""
    p_, q_ = coprime_pair(r, 2, 6)
    s_r = coprime_pair(r, 2, 6)
    r_, s_ = s_r
    if F(p_, q_) == F(r_, s_):
        return None
    # p/q of A = r/s of B  =>  A : B = (r/s) : (p/q) = r*q : s*p
    u, v = r_ * q_, s_ * p_
    g = gcd(u, v)
    u, v = u // g, v // g
    if u <= v or u - v > 4:
        return None
    m = r.randint(2, 12)
    A, B, D = u * m, v * m, (u - v) * m
    x, y = two_names(r)
    stem = (f"{p_}/{q_} of {x}'s stickers is equal to {r_}/{s_} of {y}'s stickers. "
            f"{x} has {D} more stickers than {y}. How many stickers do they have altogether?")
    naive = None if r_ == p_ else F((r_ + p_) * D, abs(r_ - p_))
    return build(equal_fractions, stem, A + B, [
        (naive, "used_numerators_as_ratio", f"Took the ratio as {r_} : {p_} from the numerators only."),
        (A, "gave_first_person_only", f"Gave {x}'s stickers only."),
        (B, "gave_second_person_only", f"Gave {y}'s stickers only."),
    ], [f"Make the numerators the same: {p_}/{q_} of {x} = {r_}/{s_} of {y}",
        f"{x} : {y} = {r_ * q_} : {s_ * p_} = {u} : {v}",
        f"{plural(u - v, 'unit')} → {D}, so 1 unit → {m}", f"Altogether = {u + v} × {m} = {A + B}"],
        {"p": p_, "q": q_, "r": r_, "s": s_, "D": D}, unit("stickers"),
        unit_size=m, whole=True)


@checker(equal_fractions)
def _(p):
    # brute force over A, with B = A - D
    for A in range(p["D"] + 1, 5000):
        B = A - p["D"]
        if A * F(p["p"], p["q"]) == B * F(p["r"], p["s"]):
            return F(A + B)


@template(T, "competent", OF_SET, MUL_FRAC)
def glasses_in_groups(r):
    a, b = coprime_pair(r, 3, 9)
    x, y = r.choice([(1, 2), (1, 3), (2, 3), (1, 4), (3, 4)]), r.choice([(1, 2), (1, 3), (2, 5), (1, 4)])
    total = b * x[1] * y[1] * r.randint(1, 4)
    boys = total * F(a, b)
    girls = total - boys
    G = boys * F(*x) + girls * F(*y)
    if G.denominator != 1 or total > 400 or x == y:
        return None
    stem = (f"{a}/{b} of the pupils in a school hall are boys. {x[0]}/{x[1]} of the boys and "
            f"{y[0]}/{y[1]} of the girls wear glasses. {G} pupils wear glasses. How many pupils are in the hall?")
    naive = F(*x) + F(*y)
    return build(glasses_in_groups, stem, total, [
        (G / naive if naive < 1 else None, "added_the_two_fractions", "Added the two fractions as if they were of the same group."),
        (boys, "gave_number_of_boys", "Gave the number of boys."),
        (total - G, "gave_pupils_without_glasses", "Gave the number of pupils without glasses."),
        (girls, "gave_number_of_girls", "Gave the number of girls."),
    ], [f"Boys with glasses = {x[0]}/{x[1]} × {a}/{b} = {frac(F(*x) * F(a, b))} of the pupils",
        f"Girls with glasses = {y[0]}/{y[1]} × {b - a}/{b} = {frac(F(*y) * F(b - a, b))} of the pupils",
        f"Glasses = {frac(G / total)} of the pupils → {G}", f"Pupils = {G} ÷ {frac(G / total)} = {total}"],
        {"a": a, "b": b, "x": list(x), "y": list(y), "G": int(G)}, unit("pupils"),
        unit_size=total // b, whole=True)


@checker(glasses_in_groups)
def _(p):
    def ok(n):
        boys = n * F(p["a"], p["b"])
        return (boys.denominator == 1 and boys * F(*p["x"]) + (n - boys) * F(*p["y"]) == p["G"])
    return brute(ok)


# ---------------------------------------------------------------- from the top-school paper survey
# (docs/syllabus/math-question-patterns.md; pattern ids in each docstring)

DEC = O + "fraction-and-division-02"


def round2(a, b):
    """a/b rounded half-up to 2 decimal places, as a Fraction over 100 (integer arithmetic)."""
    return F((200 * a + b) // (2 * b), 100)


@template(T, "basic", DEC)
def fraction_to_decimal(r):
    """math-pat-fraction-to-decimal-rounded"""
    b = r.choice([3, 6, 7, 9, 11, 12, 13])
    a = r.randint(1, b - 1)
    if gcd(a, b) != 1:
        return None
    ans = round2(a, b)
    one_dp = F((20 * a + b) // (2 * b), 10)
    show = lambda x: f"{float(x):.2f}"
    stem = f"Express {a}/{b} as a decimal, correct to 2 decimal places."
    return build(fraction_to_decimal, stem, ans, [
        (F(100 * a // b, 100) if F(100 * a // b, 100) != ans else None, "cut_off_instead_of_rounding",
         "Cut the decimal off after 2 places instead of rounding."),
        (round2(b, a), "divided_the_wrong_way", f"Worked out {b} ÷ {a} instead of {a} ÷ {b}."),
        ((f"{float(one_dp):.1f}", one_dp) if one_dp * 100 != ans * 100 else None, "rounded_to_1_decimal_place",
         "Rounded to 1 decimal place instead of 2."),
        (ans + F(1, 100), "rounding_slip", "Rounded up when the next digit was less than 5."),
        (ans - F(1, 100), "rounding_slip", "Made a slip in the last digit."),
    ], [f"{a}/{b} = {a} ÷ {b} = {float(F(a, b)):.4f}…", f"The third decimal place is {int(1000 * a // b) % 10}, "
        + ("so round up." if (1000 * a // b) % 10 >= 5 else "so round down."), f"Answer: {show(ans)}"],
        {"a": a, "b": b}, show, auto_slips=False)


@checker(fraction_to_decimal)
def _(p):
    from decimal import Decimal, ROUND_HALF_UP
    d = (Decimal(p["a"]) / Decimal(p["b"])).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return F(str(d))


@template(T, "basic", DIV_BY_WHOLE, MUL_WHOLE)
def share_remainder(r):
    """math-pat-fraction-share-remainder"""
    a, b = coprime_pair(r, 3, 8)
    L = r.randint(2, 9)
    n = r.randint(2, 6)
    rest = L * F(b - a, b)
    ans = rest / n
    name = r.choice(NAMES)
    stem = (f"{name} used {a}/{b} of {a_an(L)} {L} m long rope. The rest of the rope was cut into {n} equal pieces. "
            f"How long is each piece?")
    return build(share_remainder, stem, ans, [
        (L * F(a, b) / n, "shared_the_used_part", f"Shared the {a}/{b} that was used instead of the rest."),
        (F(L, n), "ignored_the_used_part", "Shared the whole rope."),
        (rest, "did_not_divide", f"Found the rest but did not divide by {n}."),
        (F(b - a, b * n), "forgot_the_length", "Found the fraction of the rope, not the length."),
    ], [f"Rest = (1 − {a}/{b}) × {L} m = {frac(rest)} m", f"Each piece = {frac(rest)} ÷ {n} = {frac(ans)} m"],
        {"a": a, "b": b, "L": L, "n": n}, unit("m"))


@checker(share_remainder)
def _(p):
    return (p["L"] - p["L"] * F(p["a"], p["b"])) / p["n"]


@template(T, "intermediate", OF_SET, MUL_FRAC)
def fixed_then_fraction(r):
    """math-pat-fraction-successive-parts (fixed amount first, then a fraction of the rest)"""
    c, d = coprime_pair(r, 2, 7)
    x = r.randint(2, 20) * 5
    R = d * r.randint(3, 15)
    left = R * F(d - c, d)
    M = x + R
    name = r.choice(NAMES)
    stem = (f"{name} had some money. {name} spent ${x} on a book and {c}/{d} of the remaining money on a bag. "
            f"{name} had ${left} left. How much money did {name} have at first?")
    return build(fixed_then_fraction, stem, M, [
        (R, "forgot_to_add_back_fixed_amount", f"Worked back to ${R} but did not add the ${x} for the book."),
        ((left + x) / F(d - c, d), "added_fixed_amount_before_working_back",
         f"Added ${x} before undoing the {c}/{d}."),
        (left + x, "ignored_the_fraction", f"Added ${x} to ${left} and ignored the {c}/{d} spent on the bag."),
        (R - x, "subtracted_fixed_amount", f"Subtracted ${x} instead of adding it."),
    ], [f"Money left = {d - c}/{d} of the remainder → ${left}", f"Remainder = ${left} ÷ {d - c} × {d} = ${R}",
        f"At first = ${R} + ${x} = ${M}"], {"c": c, "d": d, "x": x, "left": int(left)}, money,
        unit_size=R // d, whole=True)


@checker(fixed_then_fraction)
def _(p):
    return brute(lambda n: n > p["x"] and (n - p["x"]) * F(p["d"] - p["c"], p["d"]) == p["left"])


@template(T, "competent", OF_SET)
def constant_part_new_fraction(r):
    """math-pat-constant-part-new-fraction"""
    a, b = coprime_pair(r, 3, 8)
    c, d = coprime_pair(r, 3, 9)
    if F(c, d) >= F(a, b):
        return None
    red = lcm(a, c) * r.randint(1, 6)
    T0, T1 = red * b // a, red * d // c
    x = T1 - T0
    if T1 > 400 or T0 < 20:
        return None
    stem = (f"In a jar, {a}/{b} of the beads are red and the rest are blue. After {x} blue beads are added, "
            f"the red beads make up {c}/{d} of all the beads. How many beads were in the jar at first?")
    naive = F(x) / (F(a, b) - F(c, d))
    return build(constant_part_new_fraction, stem, T0, [
        (T1, "gave_total_after", "Gave the number of beads after the blue beads were added."),
        (naive, "treated_change_in_fraction_as_added_beads",
         f"Took {x} as ({a}/{b} − {c}/{d}) of the beads, but the whole changed."),
        (red, "gave_red_beads", "Gave the number of red beads."),
        (T0 - red, "gave_blue_beads_at_first", "Gave the number of blue beads at first."),
    ], [f"The red beads do not change. Make red the same number of units: LCM of {a} and {c} is {lcm(a, c)}",
        f"Before: red {plural(lcm(a, c), 'unit')} of {lcm(a, c) * b // a}; after: red {plural(lcm(a, c), 'unit')} of {lcm(a, c) * d // c}",
        f"{plural(lcm(a, c) * d // c - lcm(a, c) * b // a, 'unit')} → {x}, so 1 unit = {red // lcm(a, c)}",
        f"At first = {lcm(a, c) * b // a} × {red // lcm(a, c)} = {T0}"],
        {"a": a, "b": b, "c": c, "d": d, "x": x}, unit("beads"), unit_size=red // lcm(a, c), whole=True)


@checker(constant_part_new_fraction)
def _(p):
    def ok(n):
        red = n * F(p["a"], p["b"])
        return red.denominator == 1 and red * p["d"] == p["c"] * (n + p["x"])
    return brute(ok)


@template(T, "competent", OF_SET, MUL_FRAC)
def unequal_wholes_same_remainder(r):
    """math-pat-unequal-wholes-same-remainder"""
    a, b = coprime_pair(r, 2, 6)
    c, d = coprime_pair(r, 2, 6)
    if F(a, b) <= F(c, d):
        return None
    B = b * d * r.randint(1, 10)
    A = B * F(d - c, d) / F(b - a, b)
    if A.denominator != 1 or A > 1000:
        return None
    A, D = int(A), int(A) - B
    left = A * F(b - a, b)
    x, y = two_names(r)
    stem = (f"{x} had ${D} more than {y}. {x} spent {a}/{b} of {x}'s money and {y} spent {c}/{d} of {y}'s money. "
            f"They then had the same amount of money left. How much money did they have altogether at first?")
    return build(unequal_wholes_same_remainder, stem, A + B, [
        (A, "gave_first_person_only", f"Gave {x}'s money at first only."),
        (2 * left, "gave_total_left", "Gave the total money left at the end."),
        (B, "gave_second_person_only", f"Gave {y}'s money at first only."),
        (F(2 * D, 1) / (F(a, b) - F(c, d)) if True else None, "treated_difference_as_fraction_gap",
         f"Took ${D} as {a}/{b} − {c}/{d} of the money."),
    ], [f"Left: {b - a}/{b} of {x}'s = {d - c}/{d} of {y}'s money",
        f"{x} : {y} = {frac(F(d - c, d))} : {frac(F(b - a, b))} = {A // gcd(A, B)} : {B // gcd(A, B)}",
        f"Difference {plural(A // gcd(A, B) - B // gcd(A, B), 'unit')} → ${D}, so 1 unit = ${gcd(A, B)}",
        f"Altogether = ({A // gcd(A, B)} + {B // gcd(A, B)}) × ${gcd(A, B)} = ${A + B}"],
        {"a": a, "b": b, "c": c, "d": d, "D": D}, money, unit_size=gcd(A, B), whole=True)


@checker(unequal_wholes_same_remainder)
def _(p):
    def ok(Bn):
        An = Bn + p["D"]
        return An * F(p["b"] - p["a"], p["b"]) == Bn * F(p["d"] - p["c"], p["d"])
    Bn = brute(ok)
    return F(2 * Bn + p["D"])


# ---------------------------------------------------------------- catalogue v2 (OCR of 209 papers)

from figures import Fig  # noqa: E402

EQUIV_ORDER = O + "equivalent-fractions-and-simplest-form-03"
MIXED = O + "mixed-numbers-and-improper-fractions-01"
WHOLE_PART = O + "fraction-of-a-whole-and-of-a-set-01"


@template(T, "basic", EQUIV_ORDER)
def compare_order(r):
    """math-pat-fraction-compare-order"""
    fr = []
    while len(fr) < 4:
        b = r.randint(3, 12)
        a = r.randint(1, b - 1)
        if gcd(a, b) == 1 and F(a, b) not in [F(*x) for x in fr]:
            fr.append((a, b))
    want = r.choice(["greatest", "smallest"])
    vals = [F(a, b) for a, b in fr]
    ans = max(vals) if want == "greatest" else min(vals)
    pick = max if want == "greatest" else min
    big_num = F(*pick(fr, key=lambda x: x[0]))
    small_den = F(*min(fr, key=lambda x: x[1])) if want == "greatest" else F(*max(fr, key=lambda x: x[1]))
    big_den = F(*max(fr, key=lambda x: x[1])) if want == "greatest" else F(*min(fr, key=lambda x: x[1]))
    others = [v for v in vals if v != ans]
    show = lambda x: frac(x, mixed=False)
    stem = f"Which of these fractions is the {want}? " + ", ".join(f"{a}/{b}" for a, b in fr)
    q = build(compare_order, stem, ans, [
        (big_num, "compared_numerators_only", f"Picked the {'largest' if want == 'greatest' else 'smallest'} numerator without looking at the denominator."),
        (big_den, "thought_bigger_denominator_means_bigger", "Thought a bigger denominator makes a bigger fraction."),
        (small_den, "compared_denominators_only", "Looked only at the denominators."),
    ] + [(v, "compared_without_common_denominator", "Compared without changing to a common denominator.") for v in others],
        [f"Common denominator {lcm(*[b for _, b in fr])}: " + ", ".join(
            f"{a}/{b} = {a * lcm(*[b for _, b in fr]) // b}/{lcm(*[b for _, b in fr])}" for a, b in fr),
         f"The {want} is {show(ans)}"], {"fr": [list(x) for x in fr], "want": want}, show, auto_slips=False)
    # every option must be one of the four listed fractions
    if q and all(v in vals for _, v, _, _ in q["wrong"]):
        return q
    return None


@checker(compare_order)
def _(p):
    vals = [F(a, b) for a, b in p["fr"]]
    return max(vals) if p["want"] == "greatest" else min(vals)


@template(T, "basic", WHOLE_PART)
def shaded_figure(r):
    """math-pat-fraction-shaded-figure"""
    rows, cols = r.choice([(2, 4), (2, 6), (3, 4), (3, 6), (4, 4), (2, 5), (3, 5), (4, 6)])
    n = rows * cols
    k = r.randint(2, n - 2)
    if gcd(k, n) == 1 and r.random() < 0.6:
        return None  # prefer questions that need simplifying
    cells = set(r.sample(range(n), k))
    f = Fig(40 + cols * 40, 20 + rows * 40)
    for i in range(n):
        x, y = 20 + (i % cols) * 40, 10 + (i // cols) * 40
        f.rect(x, y, 40, 40, shade=0.45 if i in cells else 0)
    show = lambda x: frac(x, mixed=False)
    want = r.choice(["shaded", "unshaded"])
    ans = F(k, n) if want == "shaded" else F(n - k, n)
    other = F(n - k, n) if want == "shaded" else F(k, n)
    stem = f"The figure is made of {n} equal squares. What fraction of the figure is {want}? Give your answer in its simplest form."
    return build(shaded_figure, stem, ans, [
        (other, f"gave_{'unshaded' if want == 'shaded' else 'shaded'}_fraction", f"Found the {'unshaded' if want == 'shaded' else 'shaded'} part instead."),
        (F(k, n - k) if want == "shaded" else F(n - k, k), "compared_part_with_other_part",
         "Compared the shaded part with the unshaded part instead of with the whole."),
        (F(k + 1, n) if want == "shaded" else F(n - k + 1, n), "miscounted_squares", "Counted one square too many."),
        (F(k - 1, n) if want == "shaded" else F(n - k - 1, n), "miscounted_squares", "Counted one square too few."),
    ], [f"{k} of the {n} squares are shaded.", f"{want.capitalize()}: {(k if want == 'shaded' else n - k)}/{n} = {show(ans)}"],
        {"k": k, "n": n, "want": want}, show, auto_slips=False, figure=f.svg("Grid of equal squares, some shaded"))


@checker(shaded_figure)
def _(p):
    return F(p["k"] if p["want"] == "shaded" else p["n"] - p["k"], p["n"])


@template(T, "basic", MIXED)
def improper_mixed(r):
    """math-pat-fraction-equivalent-improper-mixed"""
    d = r.randint(3, 12)
    w, rem = r.randint(1, 9), r.randint(1, d - 1)
    if gcd(rem, d) != 1:
        return None
    val = w + F(rem, d)
    if r.random() < 0.5:
        stem = f"Express {w * d + rem}/{d} as a mixed number."
        return build(improper_mixed, stem, val, [
            (w + F(d - rem, d), "used_the_wrong_remainder", f"Wrote the remainder as {d - rem} instead of {rem}."),
            (w - 1 + F(rem, d), "whole_number_one_too_small", "Made a slip in the whole number."),
            (w + 1 + F(rem, d), "whole_number_one_too_big", "Made a slip in the whole number."),
        ], [f"{w * d + rem} ÷ {d} = {w} remainder {rem}", f"= {frac(val)}"], {"w": w, "rem": rem, "d": d, "dir": "to_mixed"},
            auto_slips=False)
    show = lambda x: frac(x, mixed=False)
    stem = f"Express {w} {rem}/{d} as an improper fraction."
    return build(improper_mixed, stem, val, [
        (F(w + rem, d), "added_whole_to_numerator", f"Added {w} to the numerator instead of {w} × {d}."),
        (F(w * d - rem, d), "subtracted_numerator", f"Worked out {w} × {d} − {rem}."),
        (F(w * rem + d, d) if F(w * rem + d, d) != val else None, "multiplied_wrong_numbers", f"Worked out {w} × {rem} + {d}."),
        (val + F(1, d), "careless_slip_in_numerator", "Careless slip working out the numerator."),
    ], [f"{plural(w, 'whole')} = {w * d}/{d}", f"{w * d}/{d} + {rem}/{d} = {w * d + rem}/{d}"],
        {"w": w, "rem": rem, "d": d, "dir": "to_improper"}, show, auto_slips=False)


@checker(improper_mixed)
def _(p):
    return F(p["w"] * p["d"] + p["rem"], p["d"])


@template(T, "basic", OF_SET)
def express_as_fraction_of(r):
    """math-pat-fraction-express-as-fraction-of"""
    kind = r.choice(["time", "mass", "length"])
    if kind == "time":
        small, big, k, su, bu = r.choice([15, 20, 25, 35, 40, 45, 50]), r.randint(1, 3), 60, "minutes", "hours"
    elif kind == "mass":
        small, big, k, su, bu = r.choice([150, 250, 350, 400, 450, 600, 750]), r.randint(1, 3), 1000, "g", "kg"
    else:
        small, big, k, su, bu = r.choice([15, 25, 35, 40, 45, 60, 75]), r.randint(1, 3), 100, "cm", "m"
    ans = F(small, big * k)
    show = lambda x: frac(x, mixed=False)
    one = {"minutes": "1 hour", "g": "1 kg", "cm": "1 m"}[su]
    stem = f"Express {small} {su} as a fraction of {big} {bu if big > 1 else bu.rstrip('s')}. Give your answer in its simplest form."
    wrong_k = {60: 100, 1000: 100, 100: 10}[k]
    return build(express_as_fraction_of, stem, ans, [
        (F(small, big), "forgot_to_convert_units", f"Did not change {bu} to {su} first."),
        (F(big * k, small), "inverted_fraction", "Wrote the fraction upside down."),
        (F(small, big * wrong_k), "used_wrong_conversion", f"Used the wrong number of {su} in {one}."),
        (F(small, k), "converted_only_one_unit", f"Used {one} instead of {big} {bu}."),
    ], [f"{big} {bu} = {big * k} {su}", f"{small}/{big * k} = {show(ans)}"], {"small": small, "big": big, "k": k}, show,
        auto_slips=False)


@checker(express_as_fraction_of)
def _(p):
    return F(p["small"]) / (p["big"] * p["k"])


@template(T, "basic", OF_SET)
def quantity_left(r):
    """math-pat-fraction-of-quantity-left"""
    a, b = coprime_pair(r, 3, 9)
    Q = r.randint(2, 9)
    if (Q * a) % b == 0:
        return None
    thing, u = r.choice([("flour", "kg"), ("juice", "litres"), ("ribbon", "m"), ("rice", "kg"), ("paint", "litres")])
    name = r.choice(NAMES)
    left = Q * F(b - a, b)
    stem = f"{name} bought {Q} {u} of {thing} and used {a}/{b} of it. How much {thing} was left?"
    return build(quantity_left, stem, left, [
        (Q * F(a, b), "gave_amount_used", "Found the amount used instead of the amount left."),
        (Q - F(a, b), "subtracted_fraction_from_quantity", f"Took away {a}/{b} {u} instead of {a}/{b} of {Q} {u}."),
        (F(b - a, b), "forgot_the_quantity", "Gave the fraction left, not the amount."),
    ], [f"Fraction left = 1 − {a}/{b} = {b - a}/{b}", f"{b - a}/{b} × {Q} = {frac(left)} {u}"],
        {"a": a, "b": b, "Q": Q}, unit(u))


@checker(quantity_left)
def _(p):
    return p["Q"] - p["Q"] * F(p["a"], p["b"])


@template(T, "intermediate", OF_SET, MUL_FRAC)
def equal_use_per_day(r):
    """math-pat-fraction-equal-use-per-day"""
    n = r.randint(8, 16)  # the tank lasts n days
    d1 = r.randint(1, n // 2)
    d2 = r.randint(d1 + 2, n - 1)
    p, q = 1 - F(d1, n), 1 - F(d2, n)
    stem = (f"A tank of water was full. The same amount of water was used every day. After {d1} day{'s' if d1 > 1 else ''}, "
            f"{frac(p, mixed=False)} of the tank was left. After {d2} days, {frac(q, mixed=False)} of the tank was left. "
            f"What fraction of the tank was used each day?")
    show = lambda x: frac(x, mixed=False)
    return build(equal_use_per_day, stem, F(1, n), [
        (p - q, "forgot_to_divide_by_days", f"Found the water used from day {d1} to day {d2} but did not divide by {d2 - d1}."),
        ((p - q) / d2, "divided_by_wrong_number_of_days", f"Divided by {d2} instead of {d2 - d1}."),
        (q / d2, "used_fraction_left", "Used the fraction left instead of the fraction used."),
        (F(1, n + 1), "careless_slip", "Made a slip in the subtraction."),
    ], [f"Used from day {d1} to day {d2}: {show(p)} − {show(q)} = {show(p - q)}", f"Days: {d2} − {d1} = {d2 - d1}",
        f"Each day: {show(p - q)} ÷ {d2 - d1} = {show(F(1, n))}"],
        {"p": str(p), "q": str(q), "d1": d1, "d2": d2}, show, auto_slips=False)


@checker(equal_use_per_day)
def _(p):
    return (F(p["p"]) - F(p["q"])) / (p["d2"] - p["d1"])


@template(T, "competent", OF_SET)
def two_groups_sold(r):
    """math-pat-fraction-two-groups-sold-remainder"""
    a, b = coprime_pair(r, 3, 8)
    c, d = coprime_pair(r, 2, 5)
    T0 = b * d * r.randint(2, 12)
    apples, pears = T0 * a // b, T0 - T0 * a // b
    x = r.randint(1, max(1, pears // 2))
    left = apples - apples * c // d + pears - x
    if (apples * c) % d or left <= 0 or T0 > 600:
        return None
    coef = F(a, b) * F(d - c, d) + F(b - a, b)
    stem = (f"A fruit stall had some apples and pears. {a}/{b} of the fruits were apples. After {c}/{d} of the apples "
            f"and {x} pears were sold, {left} fruits were left. How many fruits were there at first?")
    naive = (left + x) / (1 - F(c, d))
    return build(two_groups_sold, stem, T0, [
        (F(left) / coef, "forgot_to_add_back_pears_sold", f"Did not add back the {x} pears that were sold."),
        (naive, "took_fraction_of_all_fruits", f"Took {c}/{d} of all the fruits instead of the apples."),
        (apples, "gave_apples_only", "Gave the number of apples at first."),
        (left + x + apples * c // d + 1, "careless_slip", "Made a slip adding back what was sold."),
    ], [f"Apples left = {d - c}/{d} of {a}/{b} = {frac(F(a, b) * F(d - c, d))} of the fruits",
        f"Pears = {b - a}/{b} of the fruits", f"{frac(coef)} of the fruits = {left} + {x} = {left + x}",
        f"Fruits at first = {left + x} ÷ {frac(coef)} = {T0}"],
        {"a": a, "b": b, "c": c, "d": d, "x": x, "left": left}, unit("fruits"), unit_size=T0 // b, whole=True)


@checker(two_groups_sold)
def _(p):
    def ok(n):
        ap = n * F(p["a"], p["b"])
        if ap.denominator != 1 or (ap * F(p["c"], p["d"])).denominator != 1:
            return False
        return ap - ap * F(p["c"], p["d"]) + (n - ap) - p["x"] == p["left"]
    return brute(ok)


# ---------------------------------------------------------------- fill the remaining sub-topic tiers

FRAC_DIV = O + "fraction-and-division-01"
SIMPLEST_FRAC = O + "equivalent-fractions-and-simplest-form-02"
EQUIV_FIND = O + "equivalent-fractions-and-simplest-form-04"


@template(T, "intermediate", EQUIV_FIND, SIMPLEST_FRAC)
def missing_equivalent(r):
    """math-pat-fraction-equivalent-improper-mixed"""
    a, b = coprime_pair(r, 3, 12)
    k = r.randint(2, 9)
    m = r.randint(2, 9)
    if k == m:
        return None
    # a/b = (a*k)/(b*k) = (a*m)/? ; find ?
    stem = f"Find the missing number: {a * k}/{b * k} = {a * m}/?"
    ans = b * m
    return build(missing_equivalent, stem, ans, [
        (b * k + (a * m - a * k) if b * k + (a * m - a * k) > 0 else None, "added_the_difference",
         f"Added {a * m - a * k} to the denominator instead of keeping the fraction equal."),
        (F(b * k * a * m, a * k * a) if (b * k * a * m) % (a * k * a) == 0 and F(b * k * a * m, a * k * a) != ans else None,
         "multiplied_wrong_terms", "Multiplied the wrong terms."),
        (b * k * m, "multiplied_denominator_by_new_factor", f"Multiplied {b * k} by {m} without simplifying first."),
        (ans + b, "careless_slip", "Made a slip in the multiplication."),
        (ans - b, "careless_slip", "Made a slip in the multiplication."),
    ], [f"{a * k}/{b * k} = {a}/{b} in simplest form", f"{a}/{b} = {a * m}/{b * m}", f"Missing number = {ans}"],
        {"a": a, "b": b, "k": k, "m": m}, whole=True)


@checker(missing_equivalent)
def _(p):
    return F(brute(lambda x: F(p["a"] * p["k"], p["b"] * p["k"]) == F(p["a"] * p["m"], x)))


@template(T, "competent", SIMPLEST_FRAC, OF_SET)
def equivalent_in_context(r):
    """math-pat-fraction-equivalent-improper-mixed"""
    a, b = coprime_pair(r, 3, 9)
    k = r.randint(3, 12)
    extra_b = r.randint(2, 6)
    # a/b of the beads are red; after adding extra red, red is c/d of the beads ... keep blue the same
    blue = (b - a) * k
    red = a * k
    total2 = red + extra_b + blue
    c = F(red + extra_b, total2)
    if c.denominator > 20:
        return None
    stem = (f"In a box, {a}/{b} of the beads are red and the rest are blue. There are {blue} blue beads. "
            f"After {extra_b} more red beads are put in, what fraction of the beads in the box are red? "
            f"Give your answer in its simplest form.")
    show = lambda x: frac(x, mixed=False)
    return build(equivalent_in_context, stem, c, [
        (F(red + extra_b, red + blue), "kept_the_old_total", "Added the red beads but kept the old total."),
        (F(a, b), "ignored_the_new_beads", "Gave the fraction before the new beads were added."),
        (F(red, total2), "forgot_to_add_to_red", "Added the beads to the total but not to the red beads."),
        (F(blue, total2), "gave_blue_fraction", "Gave the fraction of blue beads."),
    ], [f"Blue = {b - a}/{b} of the beads → {blue}, so 1/{b} → {k}", f"Red = {a} × {k} = {red}",
        f"After: red = {red + extra_b}, total = {total2}", f"Fraction red = {red + extra_b}/{total2} = {show(c)}"],
        {"a": a, "b": b, "blue": blue, "x": extra_b}, show, auto_slips=False)


@checker(equivalent_in_context)
def _(p):
    k = p["blue"] // (p["b"] - p["a"])
    red = p["a"] * k + p["x"]
    return F(red, red + p["blue"])


@template(T, "intermediate", MIXED, ADD_MIXED)
def mixed_add_context(r):
    """math-pat-fraction-equivalent-improper-mixed"""
    a, b = coprime_pair(r, 2, 8)
    c = r.randint(1, b - 1)
    if gcd(c, b) != 1 or a + c <= b:
        return None  # make the fractions add past one whole, so the improper sum must be renamed
    p, q = r.randint(1, 5), r.randint(1, 5)
    ans = p + q + F(a + c, b)
    name = r.choice(NAMES)
    stem = f"{name} poured {p} {a}/{plural(b, 'litre')} of water into a pail, then another {q} {c}/{plural(b, 'litre')}. How much water was in the pail?"
    return build(mixed_add_context, stem, ans, [
        ((f"{p + q} {a + c}/{plural(b, 'litre')}", ans), "did_not_rename_improper_fraction",
         f"Left {a + c}/{b} as it is instead of changing it to 1 {a + c - b}/{b}."),
        (p + q + F(a + c - b, b), "lost_the_carried_whole", "Changed the fraction part but forgot to add the 1 whole."),
        (p + q + F(a + c, 2 * b), "added_denominators", "Added the denominators too."),
        (ans + 1, "careless_slip", "Made a slip adding the whole numbers."),
    ], [f"Wholes: {p} + {q} = {p + q}", f"Fractions: {a}/{b} + {c}/{b} = {a + c}/{b} = 1 {a + c - b}/{b}",
        f"Total = {plural(frac(ans), 'litre')}"], {"p": p, "q": q, "a": a, "c": c, "b": b}, unit("litres"), auto_slips=False)


@checker(mixed_add_context)
def _(p):
    return F(p["p"] * p["b"] + p["a"], p["b"]) + F(p["q"] * p["b"] + p["c"], p["b"])


@template(T, "competent", MIXED, MUL_WHOLE)
def mixed_times_whole_context(r):
    """math-pat-fraction-operations-simplest"""
    a, b = coprime_pair(r, 2, 8)
    w = r.randint(1, 4)
    n = r.randint(3, 9)
    left = r.randint(1, 5)
    each = w + F(a, b)
    used = each * n
    total = used + left
    name = r.choice(NAMES)
    stem = (f"{name} cut {n} pieces of ribbon, each {frac(each)} m long, from a roll. {left} m of ribbon was left. "
            f"How long was the roll at first?")
    return build(mixed_times_whole_context, stem, total, [
        (used, "forgot_the_leftover", f"Did not add the {left} m that was left."),
        (w * n + F(a, b) + left, "multiplied_only_the_whole_number", f"Multiplied {w} by {n} but not the {a}/{b}."),
        (each + left, "did_not_multiply", f"Used one piece instead of {n} pieces."),
        (total + F(1, b), "careless_slip_in_numerator", "Careless slip working out the numerator."),
    ], [f"{frac(each)} × {n} = {frac(used)} m", f"Roll = {frac(used)} + {left} = {frac(total)} m"],
        {"w": w, "a": a, "b": b, "n": n, "left": left}, unit("m"), auto_slips=False)


@checker(mixed_times_whole_context)
def _(p):
    return F(p["w"] * p["b"] + p["a"], p["b"]) * p["n"] + p["left"]


@template(T, "competent", ADD, ADD_MIXED)
def add_subtract_story(r):
    """math-pat-fraction-of-quantity-left"""
    b, d = r.sample(range(3, 11), 2)
    if lcm(b, d) > 40:
        return None
    a, c = r.randint(1, b - 1), r.randint(1, d - 1)
    if gcd(a, b) != 1 or gcd(c, d) != 1 or F(a, b) + F(c, d) >= 1:
        return None
    x, y = two_names(r)
    rest = 1 - F(a, b) - F(c, d)
    slices = lcm(b, d) * r.randint(1, 3)
    left = slices * rest
    if left.denominator != 1:
        return None
    stem = (f"A cake was cut into {slices} equal slices. {x} ate {a}/{b} of the cake and {y} ate {c}/{d} of it. "
            f"How many slices were left?")
    return build(add_subtract_story, stem, left, [
        (slices * (F(a, b) + F(c, d)), "gave_slices_eaten", "Found the slices eaten instead of the slices left."),
        (slices - slices * F(a + c, b + d) if (slices * F(a + c, b + d)).denominator == 1 else None,
         "added_numerators_and_denominators", "Added the tops and the bottoms of the fractions."),
        (slices * (1 - F(a, b)), "subtracted_only_one_fraction", f"Took away only {x}'s share."),
        (left + 1, "miscounted_units", "Counted one slice too many."),
    ], [f"Eaten = {a}/{b} + {c}/{d} = {frac(F(a, b) + F(c, d))}", f"Left = 1 − {frac(F(a, b) + F(c, d))} = {frac(rest)}",
        f"{frac(rest)} × {slices} = {plural(left, 'slice')}"], {"a": a, "b": b, "c": c, "d": d, "slices": slices}, unit("slices"),
        whole=True)


@checker(add_subtract_story)
def _(p):
    return p["slices"] - p["slices"] * F(p["a"], p["b"]) - p["slices"] * F(p["c"], p["d"])


def share_amount(x, sing, many):
    """'3/5 of a pizza', '1 pizza', '1 1/2 pizzas': a share at or below 1 takes the singular."""
    x = F(x)
    return f"{frac(x)} of {a_an(sing)} {sing}" if x < 1 else f"{frac(x)} {noun(x, sing, many)}"


@template(T, "intermediate", FRAC_DIV)
def division_as_fraction(r):
    """math-pat-fraction-division-share"""
    n = r.randint(3, 9)
    k = r.randint(2, 12)
    if k % n == 0:
        return None
    thing, sing = r.choice([("pizzas", "pizza"), ("cakes", "cake"), ("loaves of bread", "loaf of bread"), ("watermelons", "watermelon")])
    stem = f"{k} {thing} are shared equally among {n} children. How many {thing} does each child get?"
    ans = F(k, n)
    return build(division_as_fraction, stem, ans, [
        (F(n, k), "divided_the_wrong_way", f"Worked out {n} ÷ {k} instead of {k} ÷ {n}."),
        (F(k // n) if k // n else None, "dropped_the_remainder", "Gave only the whole number part."),
        (F(k, n * 2), "halved_wrongly", "Divided by twice the number of children."),
        (ans + 1, "slip_converting_to_mixed_number", "Made a slip changing the improper fraction to a mixed number."),
    ], [f"{k} ÷ {n} = {k}/{n}", f"= {frac(ans)}"], {"k": k, "n": n}, lambda x: share_amount(x, sing, thing),
        auto_slips=False)


@checker(division_as_fraction)
def _(p):
    return F(p["k"]) / p["n"]


@template(T, "competent", FRAC_DIV, DIV_BY_WHOLE)
def division_share_compare(r):
    """math-pat-fraction-division-share"""
    k1, n1 = r.randint(2, 9), r.randint(3, 10)
    k2, n2 = r.randint(2, 9), r.randint(3, 10)
    if F(k1, n1) == F(k2, n2) or n1 == n2 or k1 % n1 == 0 or k2 % n2 == 0:
        return None
    x, y = two_names(r)
    stem = (f"In {x}'s group, {k1} pizzas are shared equally among {n1} pupils. In {y}'s group, {k2} pizzas are "
            f"shared equally among {n2} pupils. How much more pizza does each pupil in the group with the bigger share get?")
    diff = abs(F(k1, n1) - F(k2, n2))
    show = lambda v: share_amount(v, "pizza", "pizzas")
    return build(division_share_compare, stem, diff, [
        (abs(F(n1, k1) - F(n2, k2)), "divided_the_wrong_way", "Worked out pupils ÷ pizzas."),
        (F(abs(k1 - k2), abs(n1 - n2)), "subtracted_tops_and_bottoms", "Subtracted pizzas and pupils separately."),
        (max(F(k1, n1), F(k2, n2)), "gave_the_bigger_share", "Gave the bigger share instead of the difference."),
        (diff + F(1, lcm(n1, n2)), "careless_slip", "Made a slip with the common denominator."),
    ], [f"{x}'s group: {k1} ÷ {n1} = {frac(F(k1, n1))}", f"{y}'s group: {k2} ÷ {n2} = {frac(F(k2, n2))}",
        f"Difference = {frac(diff)}"], {"k1": k1, "n1": n1, "k2": k2, "n2": n2}, show, auto_slips=False)


@checker(division_share_compare)
def _(p):
    return abs(F(p["k1"]) / p["n1"] - F(p["k2"]) / p["n2"])


# ---------------------------------------------------------------- gap group B (missing outcomes)

from figures_gapB import fraction_bars  # noqa: E402

CMP = O + "fraction-of-a-whole-and-of-a-set-02"
EQ1 = O + "equivalent-fractions-and-simplest-form-01"
AS1 = O + "addition-and-subtraction-of-fractions-01"
AS2 = O + "addition-and-subtraction-of-fractions-02"
MI3 = O + "multiplication-and-division-of-fractions-03"
MI4 = O + "multiplication-and-division-of-fractions-04"
SF = lambda x: frac(x, mixed=False)  # noqa: E731


def _seq_code(nums):
    v = 0
    for x in nums:
        v = v * 100 + x
    return v


def _seq_nums(code):
    code, out = int(code), []
    while code:
        out.append(code % 100)
        code //= 100
    return out[::-1]


# ---- comparing and ordering unit fractions and like fractions

@template(T, "basic", CMP)
def compare_unit_fractions(r):
    """Which unit fraction is greatest or smallest (denominators up to 12)."""
    ds = r.sample(range(2, 13), 4)
    want = r.choice(["greatest", "smallest"])
    show_ds = ds[:]
    r.shuffle(show_ds)
    ans_d = min(ds) if want == "greatest" else max(ds)
    others = sorted((d for d in ds if d != ans_d), reverse=(want == "greatest"))
    stem = f"Which of these unit fractions is the {want}? " + ", ".join(f"1/{d}" for d in show_ds)
    why = ("Thought a bigger denominator means a bigger fraction." if want == "greatest"
           else "Thought a smaller denominator means a smaller fraction.")
    q = build(compare_unit_fractions, stem, F(1, ans_d), [
        (F(1, others[0]), "bigger_denominator_means_bigger", why),
        (F(1, others[1]), "compared_denominators_the_wrong_way", "Ordered the denominators the wrong way round."),
        (F(1, others[2]), "guessed_from_the_look_of_the_numbers", "Did not think about the size of the equal parts."),
    ], [f"Unit fractions: the more equal parts the whole is cut into, the smaller each part.",
        f"The {want} is 1/{ans_d}."], {"ds": show_ds, "want": want}, SF, auto_slips=False)
    return q


@checker(compare_unit_fractions)
def _(p):
    vals = {d: F(1, d) for d in p["ds"]}
    pick = max(vals.values()) if p["want"] == "greatest" else min(vals.values())
    return pick


@template(T, "intermediate", CMP)
def order_like_fractions(r):
    """Arrange like fractions from smallest to greatest (or the reverse)."""
    n = r.randint(5, 12)
    nums = r.sample(range(1, n), 4)
    way = r.choice(["smallest to greatest", "greatest to smallest"])
    s = sorted(nums, reverse=(way == "greatest to smallest"))
    rev = s[::-1]
    sw1 = [s[1], s[0], s[2], s[3]]
    sw2 = [s[0], s[1], s[3], s[2]]
    rot = s[1:] + s[:1]
    show = lambda c: ", ".join(f"{x}/{n}" for x in _seq_nums(c))  # noqa: E731
    stem = f"Arrange these fractions in order, from {way}: " + ", ".join(f"{x}/{n}" for x in nums)
    return build(order_like_fractions, stem, _seq_code(s), [
        (_seq_code(rev), "ordered_the_wrong_way_round", "Wrote the order backwards."),
        (_seq_code(sw1), "swapped_two_neighbours", "Swapped two fractions that are next to each other."),
        (_seq_code(sw2), "swapped_two_neighbours", "Swapped two fractions that are next to each other."),
        (_seq_code(rot), "moved_one_fraction_wrongly", "Put one fraction in the wrong place."),
    ], [f"The denominators are the same ({n}), so compare the numerators.",
        f"Numerators {way}: " + ", ".join(str(x) for x in s)], {"nums": nums, "n": n, "way": way}, show,
        auto_slips=False)


@checker(order_like_fractions)
def _(p):
    # bubble sort by cross-multiplication, independent of sorted()
    xs = [F(x, p["n"]) for x in p["nums"]]
    for i in range(len(xs)):
        for j in range(len(xs) - 1 - i):
            if xs[j] > xs[j + 1]:
                xs[j], xs[j + 1] = xs[j + 1], xs[j]
    if p["way"] == "greatest to smallest":
        xs = xs[::-1]
    return F(_seq_code([int(x * p["n"]) for x in xs]))


@template(T, "competent", CMP)
def compare_like_story(r):
    """Three children eat slices of identical cakes: how much more did the most eat than the least?"""
    n = r.randint(6, 12)
    x, y, z = r.sample(range(1, n), 3)
    na, nb, nc = r.sample(NAMES, 3)
    big, mid, small = sorted([x, y, z], reverse=True)
    ans = F(big - small, n)
    stem = (f"Three identical cakes were each cut into {n} equal slices. {na} ate {x}/{n} of a cake, "
            f"{nb} ate {y}/{n} of a cake and {nc} ate {z}/{n} of a cake. How much more cake did the child who ate "
            f"the most eat than the child who ate the least? Give your answer in its simplest form.")
    return build(compare_like_story, stem, ans, [
        (F(big - mid, n), "compared_the_wrong_pair", "Compared the child who ate the most with the middle child."),
        (F(mid - small, n), "compared_the_wrong_pair", "Compared the middle child with the child who ate the least."),
        (big - small, "gave_slices_not_fraction", "Gave the number of slices without the denominator."),
        (F(big + small, n), "added_instead_of_subtracted", "Added the most and the least."),
    ], [f"Most: {big}/{n}. Least: {small}/{n}.", f"{big}/{n} − {small}/{n} = {big - small}/{n}"
        + ("" if frac(ans) == f"{big - small}/{n}" else f" = {frac(ans)}")],
        {"vals": [x, y, z], "n": n}, SF)


@checker(compare_like_story)
def _(p):
    xs = [F(v, p["n"]) for v in p["vals"]]
    return max(xs) - min(xs)


# ---- equivalent fractions (with bars)

@template(T, "basic", EQ1)
def equivalent_bar_parts(r):
    """Two bars of equal length: how many parts of the finer bar equal the shaded fraction of the coarser bar."""
    n = r.randint(2, 6)
    k = r.randint(2, 12 // n) if 12 // n >= 2 else 2
    N = n * k
    a = r.randint(1, n - 1)
    name = r.choice(NAMES)
    stem = (f"{name} drew two bars of the same length. The top bar has {a}/{n} shaded. The bottom bar is cut into "
            f"{N} equal parts. How many parts of the bottom bar must be shaded to show a fraction equal to {a}/{n}?")
    fig = fraction_bars([("Top", n, a), ("Bottom", N, None)], title=f"Top bar with {a} of {plural(n, 'part')} shaded, bottom bar with {plural(N, 'part')}")
    return build(equivalent_bar_parts, stem, a * k, [
        (a, "kept_the_same_numerator", f"Shaded {plural(a, 'part')}, the same number as the top bar, but the parts are smaller."),
        (a + N - n, "added_the_same_to_both", f"Added {N - n} to both the numerator and the denominator."),
        (N - a * k, "gave_unshaded_parts", "Found the number of parts NOT shaded."),
        (a * k + 1, "careless_slip", "Counted one part too many."),
        (a * k - 1, "careless_slip", "Counted one part too few."),
    ], [f"{N} ÷ {n} = {k}, so each part of the top bar is {plural(k, 'part')} of the bottom bar.",
        f"{a} × {k} = {plural(a * k, 'part')}"], {"a": a, "n": n, "N": N}, whole=True, auto_slips=False, figure=fig)


@checker(equivalent_bar_parts)
def _(p):
    return F(next(s for s in range(1, p["N"] + 1) if F(s, p["N"]) == F(p["a"], p["n"])))


@template(T, "intermediate", EQ1)
def equivalent_read_bar(r):
    """Read the shaded part of a bar and give an equal fraction in simplest form."""
    while True:
        N = r.randint(4, 12)
        s = r.randint(2, N - 2)
        g = gcd(s, N)
        if g > 1:
            break
    p_, q_ = s // g, N // g
    name = r.choice(NAMES)
    stem = (f"{name} shaded part of a strip of paper that was cut into {N} equal parts. "
            f"Which fraction is equal to the part of the strip that is shaded?")
    fig = fraction_bars([("Strip", N, s)], title=f"Strip of {N} equal parts, some shaded")
    return build(equivalent_read_bar, stem, F(p_, q_), [
        (F(q_ - p_, q_), "gave_the_unshaded_fraction", "Found the fraction that is NOT shaded."),
        (F(q_, p_), "inverted_fraction", "Turned the fraction upside down."),
        (F(p_, N), "divided_numerator_only", f"Divided only the numerator by {g}."),
        (F(s, N - s), "compared_part_with_other_part", "Compared the shaded part with the unshaded part."),
    ], [f"{s} of the {plural(N, 'part')} are shaded: {s}/{N}.", f"Divide top and bottom by {g}: {p_}/{q_}."],
        {"s": s, "N": N}, SF, auto_slips=False, figure=fig)


@checker(equivalent_read_bar)
def _(p):
    s, N = p["s"], p["N"]
    d = next(d for d in range(N, 0, -1) if s % d == 0 and N % d == 0)  # highest common factor by search
    return F(s // d, N // d)


@template(T, "competent", EQ1)
def equivalent_two_strips(r):
    """Two strips of the same length cut into different numbers of parts: how many more parts to shade."""
    n = r.randint(2, 6)
    k = r.randint(2, 4)
    N = n * k
    a = r.randint(1, n - 1)
    b = r.randint(1, a * k - 1)
    name = r.choice(NAMES)
    stem = (f"{name} has two strips of paper of the same length. Strip A is cut into {n} equal parts and {plural(a, 'part')} are "
            f"shaded. Strip B is cut into {N} equal parts and {plural(b, 'part')} {'is' if b == 1 else 'are'} shaded. How many more parts of Strip B "
            f"must be shaded so that both strips have the same fraction shaded?")
    fig = fraction_bars([("A", n, a), ("B", N, b)], title=f"Strip A: {a} of {plural(n, 'part')} shaded; strip B: {b} of {plural(N, 'part')} shaded")
    ans = a * k - b
    return build(equivalent_two_strips, stem, ans, [
        (a * k, "forgot_parts_already_shaded", f"Found the {plural(a * k, 'part')} needed but did not subtract the {b} already shaded."),
        (a + N - n - b, "added_the_same_to_both", f"Added {N - n} to both the numerator and the denominator of {a}/{n}."),
        (N - b, "gave_unshaded_parts", "Found the number of parts of Strip B not shaded."),
        (a - b if a > b else None, "compared_part_counts", "Compared the number of shaded parts without noticing the parts are different sizes."),
        (ans + 1, "careless_slip", "Counted one part too many."),
    ], [f"{a}/{n} = {a * k}/{N}", f"Strip B needs {plural(a * k, 'part')} shaded.", f"{a * k} − {b} = {ans} more parts"],
        {"a": a, "n": n, "N": N, "b": b}, whole=True, auto_slips=False, figure=fig)


@checker(equivalent_two_strips)
def _(p):
    need = next(s for s in range(1, p["N"] + 1) if F(s, p["N"]) == F(p["a"], p["n"]))
    return F(need - p["b"])


# ---- adding and subtracting like fractions within one whole

@template(T, "basic", AS1)
def like_add_sub(r):
    """Add or subtract two like fractions (denominator up to 12); the answer is within one whole."""
    n = r.randint(4, 12)
    op = r.choice(["+", "−"])
    if op == "+":
        a = r.randint(1, n - 2)
        b = r.randint(1, n - 1 - a)
        ans = F(a + b, n)
        wrongs = [
            (F(a + b, 2 * n), "added_the_denominators_too", "Added the denominators as well as the numerators."),
            (a + b, "dropped_the_denominator", "Added the numerators and forgot the denominator."),
            (F(a * b, n), "multiplied_the_numerators", "Multiplied the numerators."),
        ]
        steps = [f"The denominators are the same, so add the numerators: {a} + {b} = {a + b}.", f"{a}/{n} + {b}/{n} = {a + b}/{n}"]
    else:
        a = r.randint(2, n - 1)
        b = r.randint(1, a - 1)
        ans = F(a - b, n)
        wrongs = [
            (F(a + b, n), "added_instead_of_subtracted", "Added instead of subtracting."),
            (a - b, "dropped_the_denominator", "Subtracted the numerators and forgot the denominator."),
            (F(a - b, n - b), "subtracted_from_the_denominator", f"Subtracted {b} from the denominator too."),
        ]
        steps = [f"The denominators are the same, so subtract the numerators: {a} − {b} = {a - b}.", f"{a}/{n} − {b}/{n} = {a - b}/{n}"]
    if ans != F(ans.numerator, n):
        steps[-1] += f" = {SF(ans)}"
    verb = "Add" if op == "+" else "Subtract"
    stem = (f"{verb} {b}/{n} {'to' if op == '+' else 'from'} {a}/{n}. Give your answer in its simplest form."
            if op == "+" else f"Subtract {b}/{n} from {a}/{n}. Give your answer in its simplest form.")
    return build(like_add_sub, stem, ans, wrongs, steps, {"a": a, "b": b, "n": n, "op": op}, SF)


@checker(like_add_sub)
def _(p):
    # count slices: start with a slices of size 1/n, add or remove b of them
    slices = p["a"] + p["b"] if p["op"] == "+" else p["a"] - p["b"]
    return F(1, p["n"]) * slices


@template(T, "intermediate", AS1)
def like_story_left(r):
    """A fraction of a book is read over two days: what fraction is not yet read."""
    n = r.randint(5, 12)
    a = r.randint(1, n - 3)
    b = r.randint(1, n - 1 - a)
    name = r.choice(NAMES)
    ans = F(n - a - b, n)
    stem = (f"{name} read {a}/{n} of a book on Saturday and {b}/{n} of the book on Sunday. "
            f"What fraction of the book has {name} not read? Give your answer in its simplest form.")
    return build(like_story_left, stem, ans, [
        (F(a + b, n), "gave_the_part_read", "Found the fraction already read, not the fraction left."),
        (F(n - a, n), "used_one_day_only", "Took away the fraction for Saturday only."),
        (F(abs(a - b), n) if a != b else None, "subtracted_the_two_days", "Subtracted one day from the other."),
    ], [f"Read: {a}/{n} + {b}/{n} = {a + b}/{n}", f"Not read: {n}/{n} − {a + b}/{n} = {n - a - b}/{n}"
        + ("" if frac(ans) == f"{n - a - b}/{n}" else f" = {SF(ans)}")], {"a": a, "b": b, "n": n}, SF)


@checker(like_story_left)
def _(p):
    left = p["n"]
    for part in (p["a"], p["b"]):
        left -= part
    return F(left, p["n"])


@template(T, "competent", AS1)
def like_tank_three_steps(r):
    """Tank filled, topped up, then some used: a three-step story with like fractions."""
    n = r.randint(6, 12)
    a = r.randint(2, n - 3)
    b = r.randint(1, n - a)
    c = r.randint(1, a + b - 1)
    name = r.choice(NAMES)
    ans = F(a + b - c, n)
    stem = (f"A tank was {a}/{n} full of water. {name} poured in water that filled another {b}/{n} of the tank. "
            f"Then {c}/{n} of the tank was used to water plants. What fraction of the tank was full at the end? "
            f"Give your answer in its simplest form.")
    return build(like_tank_three_steps, stem, ans, [
        (F(a + b + c, n), "added_the_amount_used", "Added the water used instead of taking it away."),
        (F(a - b - c, n) if a > b + c else None, "subtracted_the_water_poured_in", "Took away the water poured in."),
        (F(a + b, n), "forgot_the_water_used", "Forgot to take away the water that was used."),
        (F(a - c + b - 1, n), "careless_slip", "Made a slip in the numerator."),
    ], [f"After pouring: {a}/{n} + {b}/{n} = {a + b}/{n}", f"After using: {a + b}/{n} − {c}/{n} = {a + b - c}/{n}"
        + ("" if frac(ans) == f"{a + b - c}/{n}" else f" = {SF(ans)}")], {"a": a, "b": b, "c": c, "n": n}, SF)


@checker(like_tank_three_steps)
def _(p):
    level = 0
    for step in (p["a"], p["b"], -p["c"]):
        level += step
    return F(level, p["n"])


# ---- adding and subtracting two related fractions within one whole

def _related(r, lo_b=2, hi_b=6):
    b = r.randint(lo_b, hi_b)
    k = r.randint(2, 12 // b) if 12 // b >= 2 else None
    if k is None:
        return None
    return b, b * k, k


@template(T, "basic", AS2)
def related_add_sub(r):
    """Add or subtract two related fractions (one denominator is a multiple of the other), within one whole."""
    rel = _related(r)
    if rel is None:
        return None
    b, d, k = rel
    a = r.randint(1, b - 1)
    op = r.choice(["+", "−"])
    if op == "+":
        c = r.randint(1, d - 1)
        if F(a, b) + F(c, d) >= 1:
            return None
        ans = F(a, b) + F(c, d)
        wrongs = [
            (F(a + c, b + d), "added_numerators_and_denominators", "Added the tops and added the bottoms."),
            (F(a + c, d), "forgot_to_rename", f"Used denominator {d} but did not change the numerator {a}."),
            (abs(F(a, b) - F(c, d)), "subtracted_instead_of_added", "Subtracted instead of adding."),
        ]
        steps = [f"{a}/{b} = {a * k}/{d}", f"{a * k}/{d} + {c}/{d} = {a * k + c}/{d}"]
        stem = f"Work out {a}/{b} + {c}/{d}. Write your answer as a fraction in its simplest form."
    else:
        c = r.randint(1, a * k - 1)
        ans = F(a, b) - F(c, d)
        wrongs = [
            (F(a - c, d) if a > c else None, "forgot_to_rename", f"Used denominator {d} but did not change the numerator {a}."),
            (F(a, b) + F(c, d) if F(a, b) + F(c, d) != 1 else None, "added_instead_of_subtracted", "Added instead of subtracting."),
            (F(abs(a * k - c), b), "kept_the_wrong_denominator", f"Subtracted {a * k} − {c} but kept denominator {b}."),
        ]
        steps = [f"{a}/{b} = {a * k}/{d}", f"{a * k}/{d} − {c}/{d} = {a * k - c}/{d}"]
        stem = f"Work out {a}/{b} − {c}/{d}. Write your answer as a fraction in its simplest form."
    if frac(ans) != steps[-1].split("= ")[-1]:
        steps[-1] += f" = {SF(ans)}"
    return build(related_add_sub, stem, ans, wrongs, steps, {"a": a, "b": b, "c": c, "d": d, "op": op}, SF)


@checker(related_add_sub)
def _(p):
    L = p["d"]  # the larger denominator is a multiple of b
    top_a = p["a"] * (L // p["b"])
    top = top_a + p["c"] if p["op"] == "+" else top_a - p["c"]
    return F(top, L)


@template(T, "intermediate", AS2)
def related_pizza_left(r):
    """Two people eat related fractions of one pizza: what fraction is left."""
    rel = _related(r)
    if rel is None:
        return None
    b, d, k = rel
    a = r.randint(1, b - 1)
    c = r.randint(1, d - 1)
    eaten = F(a, b) + F(c, d)
    if eaten >= 1:
        return None
    n1, n2 = r.sample(NAMES, 2)
    ans = 1 - eaten
    stem = (f"{n1} ate {a}/{b} of a pizza and {n2} ate {c}/{d} of the same pizza. "
            f"What fraction of the pizza was left? Give your answer in its simplest form.")
    return build(related_pizza_left, stem, ans, [
        (eaten, "gave_the_part_eaten", "Found the fraction eaten instead of the fraction left."),
        (1 - F(a + c, d), "forgot_to_rename", f"Added {a}/{d} + {c}/{d} without renaming {a}/{b}."),
        (1 - F(a + c, b + d), "added_numerators_and_denominators", "Added the tops and added the bottoms."),
        (1 - F(a, b), "used_one_person_only", f"Took away only {n1}'s share."),
    ], [f"Eaten: {a * k}/{d} + {c}/{d} = {a * k + c}/{d}", f"Left: {d}/{d} − {a * k + c}/{d} = {d - a * k - c}/{d}"
        + ("" if frac(ans) == f"{d - a * k - c}/{d}" else f" = {SF(ans)}")], {"a": a, "b": b, "c": c, "d": d}, SF)


@checker(related_pizza_left)
def _(p):
    L = p["d"]
    return F(L - p["a"] * (L // p["b"]) - p["c"], L)


@template(T, "competent", AS2)
def related_money_three_parts(r):
    """Money spent on three things with related fractions: what fraction is left."""
    rel = _related(r)
    if rel is None:
        return None
    b, d, k = rel
    a = r.randint(1, b - 1)
    c = r.randint(1, d - 2)
    e = r.randint(1, d - 1)
    spent = F(a, b) + F(c, d) + F(e, d)
    if spent >= 1:
        return None
    name = r.choice(NAMES)
    ans = 1 - spent
    stem = (f"{name} had some money. {name} spent {a}/{b} of it on a book and {c}/{d} of it on a pen, and gave {e}/{d} "
            f"of it to a cousin. What fraction of the money was left? Give your answer in its simplest form.")
    return build(related_money_three_parts, stem, ans, [
        (1 - F(a, b) - F(c, d), "forgot_the_gift", "Left out the money given to the cousin."),
        (spent, "gave_the_part_spent", "Found the fraction spent and gave it as the fraction left."),
        (1 - F(a + c + e, b + d + d), "added_numerators_and_denominators", "Added all the tops and all the bottoms."),
        (1 - F(c + e, d), "forgot_the_book", "Left out the money spent on the book."),
    ], [f"Spent altogether: {a * k}/{d} + {c}/{d} + {e}/{d} = {a * k + c + e}/{d}", f"Left: {d - a * k - c - e}/{d}"
        + ("" if frac(ans) == f"{d - a * k - c - e}/{d}" else f" = {SF(ans)}")], {"a": a, "b": b, "c": c, "d": d, "e": e}, SF)


@checker(related_money_three_parts)
def _(p):
    L = p["d"]
    gone = p["a"] * (L // p["b"]) + p["c"] + p["e"]
    return F(L - gone, L)


# ---- multiplying two improper fractions

def _improper(r, lo=2, hi=8):
    while True:
        b = r.randint(lo, hi)
        a = r.randint(b + 1, 2 * b + 3)
        if gcd(a, b) == 1:
            return a, b


@template(T, "basic", MI3)
def improper_times_improper(r):
    """Multiply two improper fractions; answer as a mixed number or whole number in simplest form."""
    a, b = _improper(r)
    c, d = _improper(r)
    ans = F(a * c, b * d)
    stem = f"Work out {a}/{b} × {c}/{d}. Give your answer as a mixed number in its simplest form."
    return build(improper_times_improper, stem, ans, [
        (F(a * c, b + d), "added_the_denominators", "Multiplied the tops but added the bottoms."),
        (F(a * d, b * c), "inverted_second_fraction", "Turned the second fraction upside down, as for division."),
        (F(a * c, b), "kept_one_denominator", f"Multiplied the numerators but kept only the denominator {b}."),
    ], [f"Numerators: {a} × {c} = {a * c}", f"Denominators: {b} × {d} = {b * d}",
        f"{a * c}/{b * d} = {frac(ans)}"], {"a": a, "b": b, "c": c, "d": d})


@checker(improper_times_improper)
def _(p):
    # route through mixed numbers: (w1 + r1) * (w2 + r2) expanded
    w1, r1 = divmod(p["a"], p["b"])
    w2, r2 = divmod(p["c"], p["d"])
    x, y = F(r1, p["b"]), F(r2, p["d"])
    return w1 * w2 + w1 * y + w2 * x + x * y


@template(T, "intermediate", MI3)
def improper_times_improper_cancel(r):
    """Multiply two improper fractions where a numerator cancels with a denominator."""
    while True:
        b = r.randint(2, 6)
        d = r.randint(2, 6)
        m = r.randint(1, 3)
        a = d * m
        c = r.randint(d + 1, 2 * d + 3)
        if a > b and gcd(a, b) == 1 and gcd(c, d) == 1 and F(a, b) > 1:
            break
    if r.random() < 0.5:
        a, b, c, d = c, d, a, b
    ans = F(a * c, b * d)
    stem = f"Find the value of {a}/{b} × {c}/{d}. Give your answer in its simplest form."
    return build(improper_times_improper_cancel, stem, ans, [
        (F(a * c, b + d), "added_the_denominators", "Multiplied the tops but added the bottoms."),
        (F(a * d, b * c), "inverted_second_fraction", "Turned the second fraction upside down, as for division."),
        (F(a * c, b), "kept_one_denominator", f"Multiplied the numerators but kept only the denominator {b}."),
        (F(a, b) + F(c, d), "added_instead_of_multiplied", "Added the fractions instead of multiplying."),
    ], [f"Cancel the common factor between {a if a % d == 0 else c} and {d if a % d == 0 else b}.",
        f"{a}/{b} × {c}/{d} = {a * c}/{b * d} = {frac(ans)}"], {"a": a, "b": b, "c": c, "d": d})


@checker(improper_times_improper_cancel)
def _(p):
    num, den = p["a"] * p["c"], p["b"] * p["d"]
    g = next(g for g in range(min(num, den), 0, -1) if num % g == 0 and den % g == 0)
    return F(num // g, den // g)


@template(T, "competent", MI3)
def improper_times_improper_story(r):
    """A jug holds an improper fraction times as much as a bottle that holds an improper amount: find the total."""
    a, b = _improper(r, 2, 6)
    c, d = _improper(r, 2, 6)
    name = r.choice(NAMES)
    bottle = F(a, b)
    jug = bottle * F(c, d)
    ans = bottle + jug
    stem = (f"A bottle holds {a}/{b} L of juice. A jug holds {c}/{d} times as much juice as the bottle. "
            f"{name} poured all the juice from the bottle and the jug into a tank. How much juice was in the tank?")
    return build(improper_times_improper_story, stem, ans, [
        (jug, "forgot_the_bottle", "Found only the juice in the jug."),
        (bottle + F(c, d), "added_instead_of_multiplied", f"Added {c}/{d} L to the bottle instead of multiplying."),
        (bottle * F(c, d) * 2, "counted_the_jug_twice", "Added the juice in the jug twice."),
        (bottle / F(c, d) + bottle, "divided_instead_of_multiplied", "Divided by the fraction instead of multiplying."),
    ], [f"Juice in the jug: {a}/{b} × {c}/{d} = {frac(jug)} L", f"Juice in the tank: {frac(bottle)} + {frac(jug)} = {frac(ans)} L"],
        {"a": a, "b": b, "c": c, "d": d}, unit("L"))


@checker(improper_times_improper_story)
def _(p):
    bottle = F(p["a"], p["b"])
    factor = F(p["c"], p["d"])
    return bottle * (1 + factor)  # 1 bottle + factor bottles


# ---- multiplying a mixed number by a whole number

def _mixed(r, hi_b=8):
    a, b = coprime_pair(r, 2, hi_b)
    return r.randint(1, 5), a, b


@template(T, "basic", MI4)
def mixed_times_whole(r):
    """Multiply a mixed number by a whole number; answer in simplest form."""
    w, a, b = _mixed(r)
    n = r.randint(2, 9)
    mixed = w + F(a, b)
    ans = mixed * n
    stem = f"Work out {w} {a}/{b} × {n}. Give your answer as a mixed number in its simplest form."
    return build(mixed_times_whole, stem, ans, [
        (w * n + F(a, b), "multiplied_only_the_whole_number", f"Multiplied {w} by {n} but did not multiply {a}/{b}."),
        (w + F(a * n, b), "multiplied_only_the_fraction", f"Multiplied {a}/{b} by {n} but did not multiply {w}."),
        (mixed, "multiplied_top_and_bottom", f"Multiplied the top and the bottom of {a}/{b} by {n}, which does not change it."),
    ], [f"{w} {a}/{b} = {w * b + a}/{b}", f"{w * b + a}/{b} × {n} = {(w * b + a) * n}/{b} = {frac(ans)}"],
        {"w": w, "a": a, "b": b, "n": n})


@checker(mixed_times_whole)
def _(p):
    total = F(0)
    for _i in range(p["n"]):  # repeated addition
        total += p["w"] + F(p["a"], p["b"])
    return total


@template(T, "intermediate", MI4)
def mixed_times_whole_cancel(r):
    """Multiply a mixed number by a whole number that cancels with the denominator."""
    w, a, b = _mixed(r)
    n = b * r.randint(1, 3) if r.random() < 0.7 else r.choice([x for x in range(2, 13) if gcd(x, b) > 1] or [b])
    mixed = w + F(a, b)
    ans = mixed * n
    stem = f"Find the value of {n} × {w} {a}/{b}. Give your answer in its simplest form."
    return build(mixed_times_whole_cancel, stem, ans, [
        (w * n + F(a, b), "multiplied_only_the_whole_number", f"Multiplied {w} by {n} but did not multiply {a}/{b}."),
        (w + F(a * n, b), "multiplied_only_the_fraction", f"Multiplied {a}/{b} by {n} but did not multiply {w}."),
        (F(w * b + a, b * n) if (w * b + a) * 1 > 0 else None, "divided_instead_of_multiplied", f"Divided by {n} instead of multiplying."),
    ], [f"{w} {a}/{b} = {w * b + a}/{b}", f"{n} × {w * b + a}/{b} = {n * (w * b + a)}/{b} = {frac(ans)}"],
        {"w": w, "a": a, "b": b, "n": n})


@checker(mixed_times_whole_cancel)
def _(p):
    return F(p["n"] * p["w"] * p["b"] + p["n"] * p["a"], p["b"])


@template(T, "competent", MI4)
def mixed_times_whole_shelves(r):
    """Shelves of mixed-number length cut from a plank: how much plank is left."""
    w, a, b = _mixed(r, 6)
    n = r.randint(3, 8)
    each = w + F(a, b)
    used = each * n
    left = r.randint(1, 4)
    plank = int(used) + 1 + left
    name = r.choice(NAMES)
    ans = plank - used
    stem = (f"{name} needs {n} shelves. Each shelf is {w} {a}/{b} m long. {name} has a plank that is {plank} m long. "
            f"How much of the plank will be left after the {n} shelves are cut?")
    return build(mixed_times_whole_shelves, stem, ans, [
        (plank - (w * n + F(a, b)), "multiplied_only_the_whole_number", f"Multiplied {w} by {n} but not the {a}/{b}."),
        (used, "gave_the_length_used", "Found the length used instead of the length left."),
        (plank - each, "used_one_shelf_only", "Took away the length of one shelf only."),
        (plank + used, "added_instead_of_subtracted", "Added the length used to the plank."),
    ], [f"Length needed: {w} {a}/{b} × {n} = {frac(used)} m", f"Left: {plank} − {frac(used)} = {frac(ans)} m"],
        {"w": w, "a": a, "b": b, "n": n, "plank": plank}, unit("m"), auto_slips=False)


@checker(mixed_times_whole_shelves)
def _(p):
    need = F(0)
    for _i in range(p["n"]):
        need += F(p["w"] * p["b"] + p["a"], p["b"])
    return p["plank"] - need
