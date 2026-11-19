"""Whole numbers (math-whole-numbers): basic, intermediate and competent generators."""
from itertools import permutations
from decimal import Decimal, ROUND_HALF_UP
from common import *
from figures_A import (growing_rows_fig, overlap_cards_fig, number_grid_fig, count_shapes_fig, dot_boxes_fig,
                       number_line_fig)

T = "math-whole-numbers"
NUM = "math-whole-numbers-numbers-up-to-100-1000-10-000-100-000-and-10-million-"
OPS = "math-whole-numbers-addition-subtraction-multiplication-and-division-"
FM = "math-whole-numbers-factors-and-multiples-"
NB = " "


def num(x):
    return f"{int(x):,}".replace(",", NB)


PLACES = ["ones", "tens", "hundreds", "thousands", "ten thousands", "hundred thousands", "millions", "ten millions"]
ONES = ("zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen "
        "sixteen seventeen eighteen nineteen").split()
TENS = ["", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"]


def _tw(n):
    return ONES[n] if n < 20 else TENS[n // 10] + ("-" + ONES[n % 10] if n % 10 else "")


def _w3(g):
    h, t = divmod(g, 100)
    s = []
    if h:
        s.append(ONES[h] + " hundred")
    if t:
        s.append(("and " if h else "") + _tw(t))
    return " ".join(s)


def words(n):
    m, rest = divmod(n, 10 ** 6)
    k, o = divmod(rest, 1000)
    parts = []
    if m:
        parts.append(_w3(m) + " million")
    if k:
        parts.append(_w3(k) + " thousand")
    if o:
        parts.append(_w3(o))
    if len(parts) > 1:
        sep = " and " if 0 < o < 100 else ", "
        return ", ".join(parts[:-1]) + sep + parts[-1]
    return parts[0]


def ordn(k):
    return f"{k}{'th' if 10 <= k % 100 <= 20 else {1: 'st', 2: 'nd', 3: 'rd'}.get(k % 10, 'th')}"


def brute(pred, lo=1, hi=100000):
    return next((n for n in range(lo, hi + 1) if pred(n)), None)


def ceil_div(a, b):
    return -(-a // b)


def r_half_up(n, place):
    return int((Decimal(n) / Decimal(place)).quantize(Decimal(1), rounding=ROUND_HALF_UP)) * place


def slip_set(ans, *steps):
    out = []
    for s in steps:
        out += [(ans + s, "careless_slip", "Made a careless slip in the last step."),
                (ans - s, "careless_slip", "Made a careless slip in the last step.")]
    return out


# ================================================================ NUMBERS: basic

@template(T, "basic", NUM + "18", NUM + "14", NUM + "02")
def digit_value(r):
    digits = r.sample(range(10), 7)
    if digits[0] == 0:
        return None
    p = r.randint(1, 6)
    d = digits[6 - p]
    if d == 0:
        return None
    n = int("".join(map(str, digits)))
    ans = d * 10 ** p
    stem = f"What is the value of the digit {d} in {num(n)}?"
    return build(digit_value, stem, ans, [
        (d * 10 ** (p + 1), "read_one_place_too_high", f"Read the {d} as being in the {PLACES[p + 1]} place."),
        (d * 10 ** (p - 1), "read_one_place_too_low", f"Read the {d} as being in the {PLACES[p - 1]} place."),
        (d, "gave_the_digit_not_its_value", "Gave the digit itself instead of its value."),
        (d * 10 ** (p + 2) if p + 2 <= 6 else d * 10 ** (p - 2) if p >= 2 else None, "wrong_place", "Counted the places wrongly."),
    ], [f"{d} is in the {PLACES[p]} place.", f"Value = {d} × {num(10 ** p)} = {num(ans)}"],
        {"n": n, "d": d}, num, whole=True)


@checker(digit_value)
def _(p):
    s = str(p["n"])
    return F(p["d"] * 10 ** (len(s) - 1 - s.index(str(p["d"]))))


def _numeral_parts(r):
    m = r.randint(1, 9)
    t = r.choice([r.randint(1, 99), r.randint(100, 999)])
    o = r.choice([0, r.randint(1, 99), r.randint(100, 999)])
    return m, t, o


def _numeral_wrongs(m, t, o):
    return [
        (int(str(m) + str(t) + (str(o) if o else "")), "dropped_placeholder_zero",
         "Left out the zero place holders when joining the groups."),
        (m * 10 ** 6 + t * 100 + o, "read_thousand_as_hundred", "Treated the thousands as hundreds."),
        (m * 10 ** 6 + o * 1000 + t if o else None, "misplaced_thousands_group", "Swapped the thousands and ones groups."),
        (m * 10 ** 6 + t * 10 ** 4 + o, "misplaced_thousands_group", "Put the thousands group one place too high."),
        (m * 10 ** 5 + t * 1000 + o, "dropped_placeholder_zero", "Wrote the millions in the hundred-thousands place."),
    ]


@template(T, "basic", NUM + "24", NUM + "19", NUM + "15")
def numeral_from_words(r):
    """math-pat-place-value-read-write"""
    m, t, o = _numeral_parts(r)
    n = m * 10 ** 6 + t * 1000 + o
    stem = f"Which numeral is '{words(n)}'?"
    return build(numeral_from_words, stem, n, _numeral_wrongs(m, t, o),
                 [f"Millions: {m} 000 000", f"Thousands: {t} 000", f"Ones: {o}", f"Total = {num(n)}"],
                 {"m": m, "t": t, "o": o}, num, whole=True)


@checker(numeral_from_words)
def _(p):
    return F(int(f"{p['m']}{p['t']:03d}{p['o']:03d}"))


@template(T, "basic", NUM + "24", NUM + "19")
def words_from_numeral(r):
    """math-pat-place-value-read-write"""
    m, t, o = _numeral_parts(r)
    n = m * 10 ** 6 + t * 1000 + o
    stem = f"Which of these is {num(n)} written in words?"
    return build(words_from_numeral, stem, n, _numeral_wrongs(m, t, o),
                 [f"{num(n)} = {m} million + {t} thousand + {o}", words(n)],
                 {"m": m, "t": t, "o": o}, lambda x: words(int(x)), whole=True)


@checker(words_from_numeral)
def _(p):
    return F(p["m"] * 10 ** 6 + p["t"] * 1000 + p["o"])


@template(T, "basic", NUM + "20", NUM + "16", NUM + "10")
def form_number(r):
    """math-pat-form-numbers-from-digits"""
    ds = r.sample(range(10), 5)
    big = r.random() < 0.5
    desc = sorted(ds, reverse=True)
    asc = sorted(ds)
    if asc[0] == 0:
        asc[0], asc[1] = asc[1], asc[0]
    greatest, smallest = int("".join(map(str, desc))), int("".join(map(str, asc)))
    lead0 = int("".join(map(str, sorted(ds))))
    part_g = int("".join(map(str, [desc[0]] + sorted(desc[1:]))))
    part_s = int("".join(map(str, [asc[0]] + sorted(asc[1:], reverse=True))))
    ans = greatest if big else smallest
    stem = (f"Using each of the digits {', '.join(map(str, sorted(ds)))} once, what is the "
            f"{'greatest' if big else 'smallest'} 5-digit number that can be formed?")
    wrong = [(smallest if big else greatest, "gave_opposite", "Gave the smallest instead of the greatest."
              if big else "Gave the greatest instead of the smallest."),
             (part_g if big else part_s, "sorted_only_first_digit", "Put the right first digit but did not order the rest."),
             (lead0 if not big else None, "leading_zero_allowed", "Started with 0, which does not make a 5-digit number."),
             (ans + 9 if big else ans - 9, "swapped_last_digits", "Swapped the last two digits.")]
    return build(form_number, stem, ans, wrong, [
        "Greatest: digits from largest to smallest." if big else "Smallest: smallest non-zero digit first, then the rest from smallest to largest.",
        f"Answer: {num(ans)}"], {"ds": ds, "big": big}, num, whole=True)


@checker(form_number)
def _(p):
    nums = [int("".join(map(str, q))) for q in permutations(p["ds"]) if q[0] != 0]
    return F(max(nums) if p["big"] else min(nums))


@template(T, "basic", NUM + "22", NUM + "23")
def round_whole(r):
    """math-pat-rounding-estimation"""
    place = r.choice([10, 100, 1000])
    n = r.randint(1200, 98999)
    ans = r_half_up(n, place)
    if n % place == 0:
        return None
    floor_ = n // place * place
    stem = r.choice([f"Round {num(n)} to the nearest {num(place)}.",
                     f"{num(n)} ≈ ? (correct to the nearest {num(place)})"])
    other = r_half_up(n, place * 10)
    return build(round_whole, stem, ans, [
        (floor_ if floor_ != ans else floor_ + place, "always_rounded_down" if floor_ != ans else "always_rounded_up",
         "Rounded down without looking at the next digit." if floor_ != ans else "Rounded up without looking at the next digit."),
        (other, "rounded_to_wrong_place", f"Rounded to the nearest {num(place * 10)}."),
        (r_half_up(n, place // 10) if place > 10 else None, "rounded_to_wrong_place", f"Rounded to the nearest {num(place // 10)}."),
        (ans + place, "rounding_slip", "Made a slip with the rounding digit."),
        (ans - place, "rounding_slip", "Made a slip with the rounding digit."),
    ], [f"Look at the digit to the right of the {num(place)} place.", f"Answer: {num(ans)}"],
        {"n": n, "place": place}, num, whole=True)


@checker(round_whole)
def _(p):
    n, pl = p["n"], p["place"]
    return F(((n * 2 + pl) // (2 * pl)) * pl)


@template(T, "basic", NUM + "21", NUM + "17", NUM + "11")
def next_term(r):
    d = r.choice([25, 50, 100, 250, 500, 1000, 2500, 5000])
    up = r.random() < 0.6
    a = r.randint(1, 9) * d + (0 if r.random() < .5 else d * 5)
    if not up:
        a += 6 * d
        sd = -d
    else:
        sd = d
    seq = [a + i * sd for i in range(4)]
    ans = a + 4 * sd
    stem = f"What is the next number in the pattern {', '.join(num(x) for x in seq)}, ... ?"
    return build(next_term, stem, ans, [
        (seq[-1] + 2 * sd, "skipped_a_term", "Skipped a term."),
        (seq[-1], "repeated_last_term", "Gave the last term again."),
        (ans + sd // 10 if abs(sd) >= 100 else None, "slip_in_a_digit", "Made a slip adding the step."),
        (seq[-1] + sd * 10, "wrong_step_size", "Added ten steps."),
        (ans + sd // 5 if abs(sd) >= 100 else ans + 1, "slip_in_a_digit", "Made a slip adding the step."),
    ], [f"The pattern {'adds' if up else 'subtracts'} {num(d)} each time.", f"{num(seq[-1])} {'+' if up else '−'} {num(d)} = {num(ans)}"],
        {"a": a, "sd": sd}, num, whole=True)


@checker(next_term)
def _(p):
    x = p["a"]
    for _ in range(4):
        x += p["sd"]
    return F(x)


# ================================================================ NUMBERS: intermediate

@template(T, "intermediate", NUM + "18", NUM + "14")
def same_digit_ratio(r):
    p, q = sorted(r.sample(range(7), 2), reverse=True)
    d = r.randint(1, 9)
    others = r.sample([x for x in range(10) if x != d], 5)
    ds = []
    it = iter(others)
    for pos in range(6, -1, -1):
        ds.append(d if pos in (p, q) else next(it))
    if ds[0] == 0:
        return None
    n = int("".join(map(str, ds)))
    k = p - q
    stem = (f"In {num(n)}, the value of the digit {d} in the {PLACES[p]} place is how many times "
            f"the value of the digit {d} in the {PLACES[q]} place?")
    return build(same_digit_ratio, stem, 10 ** k, [
        (k, "counted_places_not_powers_of_10", "Gave the number of places between the digits."),
        (1, "same_digit_same_value", "Thought the same digit always has the same value."),
        (10 ** (k + 1), "counted_one_place_too_many", "Counted one place too many."),
        (10 ** (k - 1), "counted_one_place_too_few", "Counted one place too few."),
        (d * 10 ** k, "multiplied_by_digit", "Multiplied by the digit as well."),
    ], [f"The digits are {k} place{'s' if k > 1 else ''} apart.", f"Each place is 10 times the one before: 10^{k} = {num(10 ** k)}"],
        {"n": n, "d": d}, num, whole=True)


@checker(same_digit_ratio)
def _(p):
    s = str(p["n"])
    idx = [i for i, c in enumerate(s) if c == str(p["d"])]
    return F(10 ** (idx[1] - idx[0]))


@template(T, "intermediate", NUM + "18", NUM + "20")
def n_more_less(r):
    e = r.randint(4, 6)
    f_ = r.randint(2, e - 1)
    k = r.randint(1, 9)
    n = r.randint(1, 9) * 10 ** e + r.choice([0, 0, r.randint(1, 9) * 10 ** r.randint(0, 2)])
    more = r.random() < 0.4
    step = k * 10 ** f_
    ans = n + step if more else n - step
    if not more and ans <= 0:
        return None
    stem = f"What is {num(step)} {'more' if more else 'less'} than {num(n)}?"
    wrong = [(n + step if not more else n - step, "wrong_operation", "Used the wrong operation."),
             (n + k * 10 ** (f_ + 1) if more else n - k * 10 ** (f_ + 1), "wrong_place", f"Used {num(k * 10 ** (f_ + 1))} instead."),
             (n + k * 10 ** (f_ - 1) if more else n - k * 10 ** (f_ - 1), "wrong_place", f"Used {num(k * 10 ** (f_ - 1))} instead."),
             (ans + 10 ** f_ if not more else ans - 10 ** f_, "borrowing_slip", "Made a slip with borrowing or carrying.")]
    return build(n_more_less, stem, ans, wrong, [f"{num(n)} {'+' if more else '−'} {num(step)} = {num(ans)}"],
                 {"n": n, "step": step, "more": more}, num, whole=True)


@checker(n_more_less)
def _(p):
    return F(p["n"] + p["step"] if p["more"] else p["n"] - p["step"])


@template(T, "intermediate", NUM + "22", NUM + "20")
def rounding_limits(r):
    place = r.choice([10, 100, 1000])
    X = r.randint(2, 90) * place
    big = r.random() < 0.5
    h = place // 2
    ans = X + h - 1 if big else X - h
    stem = (f"A number is {num(X)} when rounded to the nearest {num(place)}. "
            f"What is the {'greatest' if big else 'smallest'} whole number it could be?")
    wrong = [(X + h if big else X - h - 1, "boundary_rounds_the_other_way",
              "Used a boundary value that rounds the other way." if big else "Went one below the lowest number that rounds to it."),
             (X + place - 1 if big else X - place + 1, "used_whole_place_not_half", "Used a whole place value instead of half."),
             (X, "gave_the_rounded_number", "Gave the rounded number itself."),
             (ans + (1 if big else -1) * 10, "slip", "Made a slip with the last digits.")]
    return build(rounding_limits, stem, ans, wrong, [
        f"Numbers from {num(X - h)} to {num(X + h - 1)} round to {num(X)}.", f"Answer: {num(ans)}"],
        {"X": X, "place": place, "big": big}, num, whole=True)


@checker(rounding_limits)
def _(p):
    X, pl = p["X"], p["place"]
    ok = [n for n in range(X - pl, X + pl + 1) if r_half_up(n, pl) == X]
    return F(max(ok) if p["big"] else min(ok))


@template(T, "intermediate", NUM + "23", NUM + "22")
def estimate_sum(r):
    """math-pat-rounding-estimation"""
    place = r.choice([100, 1000])
    a = r.randint(1500, 9400)
    b = r.randint(1500, 9400)
    ans = r_half_up(a, place) + r_half_up(b, place)
    if a % place == 0 or b % place == 0:
        return None
    stem = f"Estimate {num(a)} + {num(b)} by rounding each number to the nearest {num(place)}."
    return build(estimate_sum, stem, ans, [
        (r_half_up(a, place) + b, "rounded_only_one_number", "Rounded only one of the numbers."),
        (r_half_up(a, place * 10) + r_half_up(b, place * 10), "rounded_to_wrong_place", f"Rounded to the nearest {num(place * 10)}."),
        (a + b, "found_exact_answer", "Worked out the exact answer instead of an estimate."),
        (ans + place, "rounding_slip", "Rounded one number the wrong way."),
    ], [f"{num(a)} ≈ {num(r_half_up(a, place))}", f"{num(b)} ≈ {num(r_half_up(b, place))}", f"Estimate = {num(ans)}"],
        {"a": a, "b": b, "place": place}, num, whole=True)


@checker(estimate_sum)
def _(p):
    pl = p["place"]
    return F(((p["a"] * 2 + pl) // (2 * pl)) * pl + ((p["b"] * 2 + pl) // (2 * pl)) * pl)


def sf1(n):
    mag = 10 ** (len(str(n)) - 1)
    return r_half_up(n, mag)


@template(T, "intermediate", NUM + "23", NUM + "22")
def estimate_product(r):
    """math-pat-rounding-estimation"""
    a = r.randint(120, 890)
    b = r.randint(12, 89)
    if a % 100 == 0 or b % 10 == 0:
        return None
    ra, rb = sf1(a), sf1(b)
    ans = ra * rb
    stem = f"Estimate {num(a)} × {b} by rounding each number to 1 significant figure."
    return build(estimate_product, stem, ans, [
        (ra * b, "rounded_only_one_number", f"Rounded only {num(a)}."),
        (a * rb, "rounded_only_one_number", f"Rounded only {b}."),
        (ans * 10, "extra_zero", "Wrote one zero too many."),
        (ans // 10, "missing_zero", "Left out a zero."),
        (a * b, "found_exact_answer", "Worked out the exact answer instead of an estimate."),
    ], [f"{num(a)} ≈ {num(ra)}, {b} ≈ {rb}", f"{num(ra)} × {rb} = {num(ans)}"],
        {"a": a, "b": b}, num, whole=True)


@checker(estimate_product)
def _(p):
    def one_sf(n):
        s = str(n)
        lead = int(s[0]) + (1 if int(s[1]) >= 5 else 0)
        return lead * 10 ** (len(s) - 1)
    return F(one_sf(p["a"]) * one_sf(p["b"]))


@template(T, "intermediate", NUM + "21", NUM + "17", NUM + "11")
def nth_term(r):
    d = r.choice([3, 4, 5, 6, 7, 8, 9, 12])
    a = r.randint(2, 20)
    k = r.randint(15, 60)
    seq = [a + i * d for i in range(3)]
    ans = a + (k - 1) * d
    stem = f"The first three numbers in a pattern are {', '.join(map(str, seq))}. The pattern continues in the same way. What is the {ordn(k)} number?"
    return build(nth_term, stem, ans, [
        (a + k * d, "counted_k_steps_not_k_minus_1", "Added the step k times instead of k − 1 times."),
        (k * d, "forgot_first_term", "Gave k × step and ignored the first term."),
        (a + (k - 2) * d, "counted_too_few_steps", "Added the step one time too few."),
        (ans + 10, "slip", "Made a slip in the last step."),
    ], [f"The step is {d}.", f"{ordn(k)} number = {a} + {k - 1} × {d} = {ans}"], {"a": a, "d": d, "k": k}, whole=True, show=str)


@checker(nth_term)
def _(p):
    x = p["a"]
    for _ in range(p["k"] - 1):
        x += p["d"]
    return F(x)


# ================================================================ NUMBERS: competent

@template(T, "competent", NUM + "20", NUM + "16", NUM + "12")
def digit_cards_even_odd(r):
    """math-pat-form-numbers-from-digits"""
    while True:
        ds = r.sample(range(10), 5)
        ev = [d for d in ds if d % 2 == 0]
        od = [d for d in ds if d % 2]
        if ev and od and len([d for d in ds if d]) >= 4:
            break
    rest = lambda ds_, last: sorted([d for d in ds_ if d != last], reverse=True) + [last]
    ge = int("".join(map(str, rest(ds, min(ev)))))
    # smallest odd: last digit = largest odd digit, rest ascending with a non-zero first digit
    best = None
    for last in od:
        others = sorted(d for d in ds if d != last)
        if others[0] == 0:
            others[0], others[1] = others[1], others[0]
        v = int("".join(map(str, others + [last])))
        best = v if best is None or v < best else best
    so = best
    ans = ge - so
    gr = int("".join(map(str, sorted(ds, reverse=True))))
    stem = (f"Using each of the digits {', '.join(map(str, sorted(ds)))} once, Ali makes the greatest even 5-digit "
            f"number and the smallest odd 5-digit number. What is the difference between the two numbers?")
    return build(digit_cards_even_odd, stem, ans, [
        (gr - so, "used_greatest_number_not_greatest_even", "Used the greatest number, which may be odd."),
        (ge + so, "added_instead_of_subtracted", "Added the two numbers."),
        (ge - int("".join(map(str, sorted(ds)))), "used_smallest_number_not_smallest_odd", "Used the smallest number, which may be even or start with 0."),
        (ans + 10, "slip", "Made a slip in the subtraction."),
    ], [f"Greatest even: {num(ge)}", f"Smallest odd: {num(so)}", f"{num(ge)} − {num(so)} = {num(ans)}"],
        {"ds": ds}, num, whole=True)


@checker(digit_cards_even_odd)
def _(p):
    nums = [int("".join(map(str, q))) for q in permutations(p["ds"]) if q[0] != 0]
    return F(max(n for n in nums if n % 2 == 0) - min(n for n in nums if n % 2))


@template(T, "competent", NUM + "15", NUM + "09")
def page_digits(r):
    N = r.randint(120, 480)
    ans = 9 + 180 + 3 * (N - 99)
    stem = f"How many digits are used altogether to number the pages of a book from page 1 to page {N}?"
    return build(page_digits, stem, ans, [
        (3 * N, "treated_all_pages_as_3_digit", "Counted 3 digits for every page."),
        (2 * 90 + 3 * (N - 99) + 9, "counted_two_digit_pages_as_90_digits", "Counted the 90 two-digit pages as 90 digits."),
        (9 + 90 + 3 * (N - 99), "counted_two_digit_pages_as_90_digits", "Counted the 90 two-digit pages as 90 digits."),
        (9 + 180 + 3 * (N - 100), "left_out_page_100", "Left out one page."),
        (N + 9 + 90, "counted_pages_not_digits", "Counted extra digits only for some pages."),
    ], ["Pages 1–9: 9 × 1 = 9 digits", "Pages 10–99: 90 × 2 = 180 digits", f"Pages 100–{N}: {N - 99} × 3 = {3 * (N - 99)} digits",
        f"Total = {num(ans)}"], {"N": N}, num, whole=True)


@checker(page_digits)
def _(p):
    return F(sum(len(str(i)) for i in range(1, p["N"] + 1)))


@template(T, "competent", NUM + "12", NUM + "13")
def count_evens(r):
    a = r.randint(2, 400) * 2
    b = a + 2 * r.randint(30, 300)
    ans = (b - a) // 2 + 1
    stem = f"How many even numbers are there from {num(a)} to {num(b)}, including both {num(a)} and {num(b)}?"
    return build(count_evens, stem, ans, [
        ((b - a) // 2, "forgot_to_include_both_ends", "Did not count both ends."),
        (b - a + 1, "counted_all_numbers", "Counted odd numbers as well."),
        (b - a, "counted_all_numbers", "Subtracted and forgot to halve."),
        ((b - a) // 2 + 2, "counted_end_twice", "Counted one end twice."),
    ], [f"({num(b)} − {num(a)}) ÷ 2 = {(b - a) // 2}", f"Add 1 for the first number: {ans}"], {"a": a, "b": b}, num, whole=True)


@checker(count_evens)
def _(p):
    return F(len([n for n in range(p["a"], p["b"] + 1) if n % 2 == 0]))


# ================================================================ OPERATIONS: basic

@template(T, "basic", OPS + "09", OPS + "05")
def add_sub_algorithm(r):
    """math-pat-whole-number-four-ops-direct"""
    a = r.randint(2100, 9899)
    b = r.randint(1100, a - 200)
    if r.random() < 0.5:
        ans = a + b
        digits = lambda x: [int(c) for c in f"{x:05d}"]
        nocarry = int("".join(str((x + y) % 10) for x, y in zip(digits(a), digits(b))))
        stem = f"Find {num(a)} + {num(b)}."
        wrong = [(nocarry, "forgot_to_carry", "Forgot to carry over."),
                 (ans + 100 if (a % 1000 + b % 1000) < 1000 else ans - 1000, "carried_to_wrong_column", "Carried to the wrong place."),
                 (ans + 10, "careless_slip", "Slip in the tens."), (ans - 100, "careless_slip", "Slip in the hundreds.")]
        steps = [f"{num(a)} + {num(b)} = {num(ans)}"]
    else:
        ans = a - b
        da, db = f"{a:05d}", f"{b:05d}"
        smaller = int("".join(str(abs(int(x) - int(y))) for x, y in zip(da, db)))
        stem = f"Find {num(a)} − {num(b)}."
        wrong = [(smaller, "subtracted_smaller_digit_from_larger", "Took the smaller digit from the larger in each column."),
                 (ans + 100, "borrow_not_reduced", "Forgot to reduce the digit that was borrowed from."),
                 (ans - 10, "careless_slip", "Slip in the tens."), (ans + 1000, "careless_slip", "Slip in the thousands.")]
        steps = [f"{num(a)} − {num(b)} = {num(ans)}"]
    return build(add_sub_algorithm, stem, ans, wrong, steps, {"a": a, "b": b, "add": "+" in stem}, num, whole=True)


@checker(add_sub_algorithm)
def _(p):
    return F(p["a"] + p["b"] if p["add"] else p["a"] - p["b"])


@template(T, "basic", OPS + "15", OPS + "13")
def mult_algorithm(r):
    """math-pat-whole-number-four-ops-direct"""
    a = r.randint(120, 899)
    b = r.randint(12, 89)
    if b % 10 == 0:
        return None
    u, t = b % 10, b // 10
    ans = a * b
    stem = f"Find {num(a)} × {b}."
    return build(mult_algorithm, stem, ans, [
        (a * u + a * t, "forgot_place_holder_zero", "Forgot the zero when multiplying by the tens digit."),
        (a * u + a * t * 100, "shifted_two_places", "Shifted the second row two places."),
        (ans + 100, "careless_slip", "Slip with a carry."), (ans - a, "miscounted_one_row", "Missed one copy of the number."),
        (ans + 10, "careless_slip", "Slip with a carry."),
    ], [f"{a} × {u} = {a * u}", f"{a} × {t * 10} = {a * t * 10}", f"{a * u} + {a * t * 10} = {num(ans)}"],
        {"a": a, "b": b}, num, whole=True)


@checker(mult_algorithm)
def _(p):
    return F(sum(p["a"] for _ in range(p["b"])))


@template(T, "basic", OPS + "16", OPS + "13")
def div_algorithm(r):
    """math-pat-whole-number-four-ops-direct"""
    d = r.randint(3, 9)
    q = r.choice([r.randint(100, 999), r.randint(1, 9) * 100 + r.randint(1, 9)])
    n = q * d
    zero = "0" in str(q)
    stem = f"Find {num(n)} ÷ {d}."
    return build(div_algorithm, stem, q, [
        (int(str(q).replace("0", "", 1)) if zero else None, "dropped_zero_in_quotient", "Left out a zero in the quotient."),
        (q + 10, "careless_slip", "Slip in the tens."), (q - 10, "careless_slip", "Slip in the tens."),
        (q + 100, "careless_slip", "Slip in the hundreds."), (q - 1, "careless_slip", "Slip in the ones."),
    ], [f"{num(n)} ÷ {d} = {num(q)}"], {"n": n, "d": d}, num, whole=True)


@checker(div_algorithm)
def _(p):
    return F(brute(lambda q: q * p["d"] == p["n"], 1, 2000))


@template(T, "basic", OPS + "12", OPS + "16")
def remainder_of(r):
    d = r.randint(4, 9)
    q = r.randint(120, 990)
    rem = r.randint(1, d - 1)
    n = q * d + rem
    stem = f"What is the remainder when {num(n)} is divided by {d}?"
    return build(remainder_of, stem, rem, [
        (d - rem, "gave_amount_to_next_multiple", f"Found how much more is needed to reach the next multiple of {d}."),
        (rem + 1, "careless_slip", "Off by one."), (rem - 1, "careless_slip", "Off by one."),
        (rem + 2, "careless_slip", "Slip in the subtraction."), (d - rem + 1, "careless_slip", "Slip in the subtraction."),
    ], [f"{num(q * d)} is a multiple of {d}.", f"{num(n)} − {num(q * d)} = {rem}"], {"n": n, "d": d}, whole=True, show=str)


@checker(remainder_of)
def _(p):
    x = p["n"]
    while x >= p["d"]:
        x -= p["d"] * (x // p["d"])
    return F(x)


@template(T, "basic", OPS + "17")
def times_powers_of_ten(r):
    k = r.randint(1, 3)
    if r.random() < 0.5:
        a, m = r.randint(2, 99), r.randint(2, 9)
        f_ = m * 10 ** k
        ans = a * f_
        stem = f"Find {a} × {num(f_)}."
        wrong = [(ans * 10, "added_extra_zero", "Wrote one zero too many."), (ans // 10, "left_out_a_zero", "Left out a zero."),
                 (a * m, "forgot_the_zeros", "Forgot the zeros of the multiplier."),
                 (a * m * 10 ** (k + 2), "added_extra_zero", "Wrote two zeros too many.")]
    else:
        q, m = r.randint(2, 99), r.randint(2, 9)
        dv = m * 10 ** k
        n = q * dv
        ans = q
        stem = f"Find {num(n)} ÷ {num(dv)}."
        wrong = [(q * 10, "removed_too_few_zeros", "Removed one zero too few."), (n // dv * 100 if False else q // 10 if q % 10 == 0 else None, "removed_too_many_zeros", "Removed one zero too many."),
                 (q * 100, "removed_too_few_zeros", "Removed two zeros too few."), (q + 10, "careless_slip", "Slip in the tens."),
                 (q + 1, "careless_slip", "Slip in the ones."), (q - 1, "careless_slip", "Slip in the ones.")]
        a, m, f_ = n, 0, dv
    return build(times_powers_of_ten, stem, ans, wrong, [stem[5:-1] + f" = {num(ans)}"],
                 {"a": a, "f": f_, "mul": "×" in stem}, num, whole=True)


@checker(times_powers_of_ten)
def _(p):
    return F(p["a"] * p["f"] if p["mul"] else p["a"] // p["f"])


def calc(tokens, groups):
    toks = list(tokens)
    for g in groups:
        i = 1
        while i < len(toks):
            if toks[i] in g:
                a, op, b = toks[i - 1], toks[i], toks[i + 1]
                v = {"+": a + b, "−": a - b, "×": a * b, "÷": F(a) / b if b else None}[op]
                if v is None:
                    return None
                toks[i - 1:i + 2] = [v]
            else:
                i += 2
    return toks[0]


def expr_str(tokens):
    return " ".join(str(t) for t in tokens)


@template(T, "basic", OPS + "18")
def order_of_operations(r):
    """math-pat-order-of-operations"""
    form = r.randint(1, 5)
    a, b, c, d = (r.randint(2, 12) for _ in range(4))
    if form == 1:
        tk = [a, "+", b, "×", c]
    elif form == 2:
        tk = [a + b * c + r.randint(1, 9), "−", b, "×", c]
    elif form == 3:
        tk = [a, "+", b * c, "÷", c]
    elif form == 4:
        tk = [a, "×", b, "−", c, "×", d]
        if a * b <= c * d:
            return None
    else:
        tk = [a * 5, "−", b * c, "÷", c, "+", d]
    hi, lo = {"×", "÷"}, {"+", "−"}
    ans = calc(tk, [hi, lo])
    rev = calc(tk, [lo, hi])
    ltr = calc(tk, [hi | lo])
    ok = lambda v: v is not None and F(v).denominator == 1 and v > 0
    if ans is None or not ok(ans):
        return None
    stem = f"Find the value of {expr_str(tk)}."
    return build(order_of_operations, stem, ans, [
        (ltr if ok(ltr) else None, "worked_left_to_right", "Worked from left to right and ignored the order of operations."),
        (rev if ok(rev) else None, "added_or_subtracted_first", "Added or subtracted before multiplying or dividing."),
        (ans + 10, "slip", "Slip in the last step."), (ans - 1, "slip", "Slip in the last step."), (ans + 2, "slip", "Slip.")],
        ["Multiply and divide first, then add and subtract.", f"Answer: {ans}"], {"expr": expr_str(tk)}, whole=True, show=lambda x: str(int(x)))


@checker(order_of_operations)
def _(p):
    return F(eval(p["expr"].replace("×", "*").replace("÷", "//").replace("−", "-")))


@template(T, "basic", OPS + "10", OPS + "06", OPS + "09")
def subtract_from_power(r):
    k = r.choice([3, 4])
    P = 10 ** k
    n = r.randint(P // 10 + 123, P - 17)
    if n % 10 == 0:
        return None
    ans = P - n
    stem = f"Find {num(P)} − {num(n)}."
    return build(subtract_from_power, stem, ans, [
        (P - 1 - n, "used_nine_complement_for_last_digit", "Took every digit from 9, including the ones digit."),
        (P - n - 10, "borrowed_twice", "Borrowed from the tens twice."),
        (P - n + 10, "careless_slip", "Slip in the tens."), (P - n + 100, "careless_slip", "Slip in the hundreds."),
    ], [f"{num(P)} − {num(n)} = {num(ans)}"], {"P": P, "n": n}, num, whole=True)


@checker(subtract_from_power)
def _(p):
    x = p["n"]
    s = 0
    while x + s < p["P"]:
        s += 1
    return F(s)


# ================================================================ OPERATIONS: intermediate

@template(T, "intermediate", OPS + "19", OPS + "18")
def brackets(r):
    """math-pat-order-of-operations"""
    a, b, c, d = (r.randint(2, 12) for _ in range(4))
    form = r.randint(1, 5)
    if form == 1:
        s, ans, w1, w2 = f"({a} + {b}) × {c} − {d}", (a + b) * c - d, a + b * c - d, (a + b) * (c - d)
    elif form == 2:
        s, ans, w1, w2 = f"{a} × ({b + c} − {c}) + {d}", a * b + d, a * (b + c) - c + d, a * (b + c - c + d)
    elif form == 3:
        s, ans, w1, w2 = f"({a * c} − {b * c}) ÷ {c} + {d}" if a > b else f"({b * c} − {a * c}) ÷ {c} + {d}", abs(a - b) + d, (a * c - b * c // c + d) if a > b else None, None
        if a == b:
            return None
        if a < b:
            w1 = b * c - a * c // c + d
    elif form == 5:
        e, f2 = r.randint(2, 9), r.randint(2, 6)
        A = b * (c + d) + r.randint(5, 30)
        s, ans = f"{A} − {b} × ({c} + {d}) + {e * f2} ÷ {f2}", A - b * (c + d) + e
        w1, w2 = A - b * c + d + e, ((A - b * (c + d)) + e * f2) // f2 if ((A - b * (c + d)) + e * f2) % f2 == 0 else None
    else:
        s, ans, w1, w2 = f"{a * b + c} − ({c} + {a}) × {b}", a * b + c - (c + a) * b, None, None
        if ans <= 0:
            return None
        w1 = a * b + c - c + a * b
        w2 = (a * b + c - (c + a)) * b
    return build(brackets, f"Find the value of {s}.", ans, [
        (w1, "ignored_the_brackets", "Ignored the brackets."),
        (w2, "wrong_order_after_brackets", "Did the brackets then used the wrong order for the rest."),
        (ans + 10, "slip", "Slip in the last step."), (ans - 1, "slip", "Slip in the last step."), (ans + 2, "slip", "Slip.")],
        ["Work out the brackets first.", f"Answer: {ans}"], {"expr": s}, whole=True, show=lambda x: str(int(x)))


@checker(brackets)
def _(p):
    return F(eval(p["expr"].replace("×", "*").replace("÷", "//").replace("−", "-")))


@template(T, "intermediate", OPS + "15", OPS + "19")
def two_step_packs(r):
    x, y = two_names(r)
    packs, per = r.randint(12, 48), r.randint(12, 36)
    used_groups, each = r.randint(3, 9), r.randint(10, 50)
    total = packs * per
    used = used_groups * each
    if used >= total:
        return None
    ans = total - used
    item = r.choice(["pencils", "stickers", "beads", "cards"])
    stem = (f"{x} bought {packs} packs of {item}, with {per} {item} in each pack. {x} gave {each} {item} to each of "
            f"{used_groups} friends. How many {item} did {x} have left?")
    return build(two_step_packs, stem, ans, [
        (total - each, "forgot_to_multiply_friends", f"Gave away {each} only."),
        (packs * per + used, "added_instead_of_subtracted", "Added instead of subtracting."),
        (packs + per - used if packs + per > used else None, "added_packs_and_per", "Added instead of multiplying."),
        (ans + 10, "slip", "Slip in the subtraction."), (ans - 10, "slip", "Slip in the subtraction.")],
        [f"Total = {packs} × {per} = {total}", f"Given away = {used_groups} × {each} = {used}", f"Left = {total} − {used} = {ans}"],
        {"packs": packs, "per": per, "g": used_groups, "each": each}, num, whole=True)


@checker(two_step_packs)
def _(p):
    left = 0
    for _ in range(p["packs"]):
        left += p["per"]
    for _ in range(p["g"]):
        left -= p["each"]
    return F(left)


@template(T, "intermediate", OPS + "12", OPS + "16", calc=True)
def buses_needed(r):
    seats = r.randint(25, 55)
    people = r.randint(100, 900)
    if people % seats == 0:
        return None
    ans = ceil_div(people, seats)
    what = r.choice(["buses", "vans", "boats"])
    stem = f"{people} people go on a trip. Each of the {what} can carry {seats} people. What is the least number of {what} needed?"
    return build(buses_needed, stem, ans, [
        (people // seats, "ignored_the_remainder", "Ignored the remainder, so some people had no seat."),
        (people // seats + 2, "added_too_many", "Added two extra for the remainder."),
        (people % seats, "gave_the_remainder", "Gave the remainder."),
        (ans + 1, "slip", "One too many."), (ans - 1, "slip", "One too few.")],
        [f"{people} ÷ {seats} = {people // seats} remainder {people % seats}", "The remainder needs one more vehicle."],
        {"people": people, "seats": seats}, whole=True, show=str)


@checker(buses_needed)
def _(p):
    k = 1
    while k * p["seats"] < p["people"]:
        k += 1
    return F(k)


@template(T, "intermediate", OPS + "16", OPS + "15", calc=True)
def cutting_pieces(r):
    """math-pat-cutting-pieces-no-joining"""
    L = r.randint(7, 19)
    per = r.randint(3, 9)
    R = L * per + r.randint(1, L - 1)
    rolls = r.randint(5, 14)
    P = per * (rolls - 1) + r.randint(1, per - 1)
    ans = ceil_div(P, per)
    thing = r.choice(["ribbon", "rope", "wire"])
    stem = (f"Strips {L} cm long are cut from {thing}s that are each {R} cm long. No joining is allowed. "
            f"What is the least number of {thing}s needed to make {P} strips?")
    return build(cutting_pieces, stem, ans, [
        (ceil_div(P * L, R), "used_total_length", "Divided the total length of the strips by the length of one piece."),
        (P // per, "rounded_down_pieces", "Rounded down, so some strips are missing."),
        (per, "gave_pieces_per_piece", f"Gave the number of strips from one {thing}."),
        (ans + 1, "slip", "One too many."), (ans - 1, "slip", "One too few.")],
        [f"Strips from one {thing}: {R} ÷ {L} = {per} remainder {R % L}, so {per} strips.", f"{P} ÷ {per} = {P // per} remainder {P % per}", f"Least number = {ans}"],
        {"L": L, "R": R, "P": P}, whole=True, show=str)


@checker(cutting_pieces)
def _(p):
    k, made = 0, 0
    while made < p["P"]:
        k += 1
        made += p["R"] // p["L"]
    return F(k)


@template(T, "intermediate", OPS + "13", OPS + "15")
def cycle_sum(r):
    """math-pat-repeating-pattern-cycle-sum"""
    k = r.randint(3, 5)
    cyc = [r.randint(1, 9) for _ in range(k)]
    n = r.randint(40, 200)
    if n % k == 0 or len(set(cyc)) < 3:
        return None
    s = sum(cyc)
    ans = (n // k) * s + sum(cyc[: n % k])
    stem = f"The numbers {', '.join(map(str, cyc))} repeat in this order. What is the sum of the first {n} numbers?"
    return build(cycle_sum, stem, ans, [
        (F(n * s, k), "averaged_the_cycle", "Used the average of the block for every number."),
        ((n // k) * s, "ignored_remainder", "Left out the numbers left over after the full blocks."),
        (ceil_div(n, k) * s, "rounded_up_cycles", "Counted the last unfinished block as a full block."),
        (ans + 1, "slip", "Slip in adding."), (ans - 2, "slip", "Slip in adding.")],
        [f"One block has {k} numbers with sum {s}.", f"{n} ÷ {k} = {n // k} blocks remainder {n % k}",
         f"Sum = {n // k} × {s} + {sum(cyc[: n % k])} = {ans}"], {"cyc": cyc, "n": n}, whole=True, show=lambda x: num(x))


@checker(cycle_sum)
def _(p):
    return F(sum(p["cyc"][i % len(p["cyc"])] for i in range(p["n"])))


@template(T, "intermediate", OPS + "15", OPS + "18")
def growing_figure(r):
    """math-pat-growing-figure-pattern"""
    c = r.choice([1, 2, 3])
    N = r.randint(8, 15)
    ans = c * N * (N + 1) // 2
    stem = (f"The figures show a pattern of squares. Row 1 of each figure has {c} square{'s' if c > 1 else ''}, "
            f"and each row below has {c} more square{'s' if c > 1 else ''} than the row above. "
            f"Figure k has k rows. How many squares are there in Figure {N}?")
    return build(growing_figure, stem, ans, [
        (c * N, "gave_last_row_only", "Gave the number of squares in the last row only."),
        (N * N * c if N * N * c != ans else None, "used_n_squared", "Multiplied the figure number by itself."),
        (N * (N + 1) // 2 if c > 1 else None, "forgot_squares_per_step", "Found 1 + 2 + … + N and forgot the multiplier."),
        (ans + c, "slip", "Added one row too many by mistake."), (ans - c, "slip", "Missed a row.")],
        [f"Rows have {c}, {2 * c}, {3 * c}, … squares.", f"Figure {N}: {c} × (1 + 2 + … + {N}) = {c} × {N * (N + 1) // 2} = {ans}"],
        {"c": c, "N": N}, whole=True, show=num, figure=growing_rows_fig(c))


@checker(growing_figure)
def _(p):
    return F(sum(p["c"] * i for i in range(1, p["N"] + 1)))


@template(T, "intermediate", OPS + "13", OPS + "16")
def overlap_cards(r):
    """math-pat-gap-overlap-counting"""
    L = r.randint(8, 20)
    ov = r.randint(2, L // 2)
    n = r.randint(6, 30)
    total = n * L - (n - 1) * ov
    stem = (f"Identical cards, each {L} cm long, are placed in a straight row. Each card overlaps the next card by {ov} cm. "
            f"The row is {total} cm long. How many cards are in the row? The figure is not drawn to scale.")
    return build(overlap_cards, stem, n, [
        (ceil_div(total, L), "ignored_overlap", "Divided the length by the length of one card."),
        (total // (L - ov) if total % (L - ov) == 0 else None, "forgot_first_card", "Divided by the visible length of one card and forgot the first full card."),
        (n - 1, "forgot_first_card", "Left out the first card."), (n + 1, "slip", "One extra card."),
        (n + 2, "slip", "Two extra cards.")],
        [f"First card: {L} cm. Each extra card adds {L} − {ov} = {L - ov} cm.", f"({total} − {L}) ÷ {L - ov} = {n - 1} extra cards", f"Cards = {n}"],
        {"L": L, "ov": ov, "total": total}, whole=True, show=str, figure=overlap_cards_fig(L, ov, total))


@checker(overlap_cards)
def _(p):
    n = 1
    while n * p["L"] - (n - 1) * p["ov"] < p["total"]:
        n += 1
    return F(n)


@template(T, "intermediate", OPS + "16", OPS + "15")
def posts_gaps(r):
    """math-pat-gap-overlap-counting"""
    d = r.randint(2, 9)
    k = r.randint(8, 40)
    closed = r.random() < 0.4
    Lg = d * k
    if closed:
        stem = f"Trees are planted {d} m apart around a circular pond with a path {Lg} m long. How many trees are planted?"
        ans = k
        wrong = [(k + 1, "added_one_for_the_end", "Added 1 as if the path were a straight line."), (k - 1, "subtracted_one", "Took one off."),
                 (k + 2, "slip", "Two too many."), (k * 2, "multiplied_by_two", "Counted both sides.")]
    else:
        stem = f"Posts are placed {d} m apart along a straight fence {Lg} m long, with a post at each end. How many posts are needed?"
        ans = k + 1
        wrong = [(k, "forgot_the_extra_post", "Gave the number of gaps."), (k + 2, "slip", "Added 2."), (k - 1, "slip", "Took one off."),
                 (Lg, "gave_the_length", "Gave the length.")]
    return build(posts_gaps, stem, ans, wrong, [f"{Lg} ÷ {d} = {k} gaps", "A straight line needs 1 more post than gaps; a closed path needs the same."],
                 {"d": d, "Lg": Lg, "closed": closed}, whole=True, show=str)


@checker(posts_gaps)
def _(p):
    pos = list(range(0, p["Lg"] + 1, p["d"]))
    return F(len(pos) - 1 if p["closed"] else len(pos))


# ================================================================ OPERATIONS: competent

@template(T, "competent", OPS + "19", OPS + "15")
def working_backwards_transfers(r):
    """math-pat-working-backwards-transfers"""
    x, y, z = r.sample(NAMES, 3)
    E = r.randint(8, 30)
    a, b, s = r.randint(2, 9), r.randint(2, 9), r.randint(1, 8)
    start = [E + a, E - a + b, E + s - b]
    if min(start) <= 0:
        return None
    ans = start[0] - start[2]
    stem = (f"{x}, {y} and {z} each had ${E} in the end. In between, {x} gave ${a} to {y}, then {y} gave ${b} to {z}, "
            f"then {z} spent ${s}. How much more money than {z} did {x} have at first?")
    return build(working_backwards_transfers, stem, ans, [
        (a + b, "forgot_to_undo_spending", f"Did not add back the ${s} {z} spent."),
        (a + b + s, "reversed_spending", f"Added the ${s} instead of subtracting."),
        (a, "gave_one_persons_change", f"Gave {x}'s change only."),
        (ans + 1, "slip", "Off by 1."), (ans + 2, "slip", "Off by 2.")],
        [f"{z} before spending: ${E} + ${s} = ${E + s}", f"{z} at first: ${E + s} − ${b} = ${E + s - b}", f"{x} at first: ${E} + ${a} = ${E + a}",
         f"Difference = ${ans}"], {"E": E, "a": a, "b": b, "s": s}, whole=True, show=lambda v: f"${int(v)}")


@checker(working_backwards_transfers)
def _(p):
    A = B = C = p["E"]
    C += p["s"]
    C -= p["b"]
    B += p["b"]
    B -= p["a"]
    A += p["a"]
    return F(A - C)


@template(T, "competent", OPS + "19", OPS + "15")
def transfer_difference(r):
    """math-pat-transfer-difference-change"""
    x, y = two_names(r)
    g = r.randint(5, 40)
    d2 = r.choice([0, r.randint(1, 20)])
    d1 = d2 + 2 * g
    item = r.choice(["cards", "stickers", "marbles"])
    if d2 == 0:
        stem = f"{x} had {d1} more {item} than {y}. After {x} gave some {item} to {y}, they had the same number of {item}. How many {item} did {x} give?"
    else:
        stem = f"{x} had {d1} more {item} than {y}. After {x} gave some {item} to {y}, {x} had {d2} more {item} than {y}. How many {item} did {x} give?"
    return build(transfer_difference, stem, g, [
        (d1 - d2, "forgot_to_halve", "Gave the change in the difference without halving."),
        ((d1 + d2) // 2 if (d1 + d2) % 2 == 0 else None, "added_instead_of_subtracted", "Added the two differences."),
        (d2 if d2 else d1, "gave_a_difference", "Gave one of the differences."),
        (g + 1, "slip", "Off by 1."), (g - 1, "slip", "Off by 1.")],
        [f"Change in difference = {d1} − {d2} = {d1 - d2}", f"Each {item[:-1]} given reduces the difference by 2.", f"{d1 - d2} ÷ 2 = {g}"],
        {"d1": d1, "d2": d2}, whole=True, show=str)


@checker(transfer_difference)
def _(p):
    gv = 0
    while p["d1"] - 2 * gv != p["d2"]:
        gv += 1
    return F(gv)


@template(T, "competent", OPS + "15", OPS + "19")
def total_given_then_difference(r):
    """math-pat-transfer-difference-change"""
    x, y = two_names(r)
    e = r.randint(2, 30)
    gv = r.randint(5, 40)
    Af = r.randint(20, 80)
    Bf = Af + e
    T_ = Af + Bf
    ans = Af + gv
    stem = (f"{x} and {y} had {T_} stickers altogether. {x} gave {gv} stickers to {y}. Then {y} had {e} more stickers than {x}. "
            f"How many stickers did {x} have at first?")
    return build(total_given_then_difference, stem, ans, [
        (Af, "forgot_to_add_back_given", "Gave how many stickers the person had at the end."),
        (Bf, "gave_other_person", "Gave the other person's final amount."),
        ((T_ + e) // 2 + gv if (T_ + e) % 2 == 0 else None, "added_the_difference", "Added the difference instead of subtracting."),
        (ans + 5, "slip", "Slip."), (ans - gv - gv, "subtracted_instead_of_added", "Subtracted what was given away.")],
        [f"At the end: 2 × {x}'s = {T_} − {e} = {T_ - e}, so {x} has {Af}", f"At first: {Af} + {gv} = {ans}"],
        {"T": T_, "e": e, "g": gv}, whole=True, show=str)


@checker(total_given_then_difference)
def _(p):
    a = 1
    while a + (a + p["e"]) != p["T"]:
        a += 1
    return F(a + p["g"])


@template(T, "competent", OPS + "15", OPS + "19", calc=True)
def two_prices_difference(r):
    """math-pat-two-quantities-two-prices-difference"""
    x = r.choice(NAMES)
    n = r.randint(8, 40)
    p2 = r.randint(60, 250)
    p1 = p2 + r.randint(40, 250)
    dpr = lambda c: f"${c // 100}.{c % 100:02d}"
    D = n * (p1 - p2)
    a, b = r.choice([("pens", "pencils"), ("notebooks", "folders"), ("apples", "oranges")])
    stem = (f"{x} bought the same number of {a} at {dpr(p1)} each and {b} at {dpr(p2)} each. "
            f"{x} spent {dpr(D)} more on the {a} than on the {b}. How many {a} did {x} buy?")
    return build(two_prices_difference, stem, n, [
        (F(D, p1), "divided_by_one_price", f"Divided the extra amount by the price of one {a[:-1]}."),
        (F(D, p2), "divided_by_cheaper_price", f"Divided the extra amount by the price of one {b[:-1]}."),
        (F(D, p1 + p2), "divided_by_sum_of_prices", "Divided by the sum of the prices."),
        (n + 1, "slip", "Off by 1."), (n - 1, "slip", "Off by 1.")],
        [f"Each pair of one of each costs {dpr(p1)} − {dpr(p2)} = {dpr(p1 - p2)} more for the {a}.", f"{dpr(D)} ÷ {dpr(p1 - p2)} = {n}"],
        {"p1": p1, "p2": p2, "D": D}, whole=True, show=str)


@checker(two_prices_difference)
def _(p):
    return F(brute(lambda n: n * p["p1"] - n * p["p2"] == p["D"], 1, 2000))


@template(T, "competent", OPS + "15", OPS + "19")
def equal_total_two_ways(r):
    """math-pat-equal-total-two-ways"""
    kids = r.randint(6, 30)
    b = r.randint(2, 6)
    a = b + r.randint(1, 4)
    s = r.randint(2, 20)
    lo = a * kids - s  # total
    left = lo - b * kids
    if left <= 0:
        return None
    total = lo
    ask = r.choice(["total", "kids"])
    item = r.choice(["sweets", "stickers", "beads"])
    stem = (f"Some {item} are shared among a group of children. If each child gets {a} {item}, there are {s} {item} too few. "
            f"If each child gets {b} {item}, there are {left} {item} left over. How many {item} are there altogether?"
            if ask == "total" else
            f"Some {item} are shared among a group of children. If each child gets {a} {item}, there are {s} {item} too few. "
            f"If each child gets {b} {item}, there are {left} {item} left over. How many children are there?")
    if ask == "total":
        ans, wrong = total, [(kids, "gave_number_of_children", "Found the number of children only."),
                             (a * kids, "one_way_without_adjust", "Forgot to take away the shortage."),
                             (b * kids, "other_way_without_adjust", "Forgot to add the leftover."),
                             (total + b, "slip", "Slip."), (total - b, "slip", "Slip.")]
    else:
        ans, wrong = kids, [(total, "gave_total_not_children", "Found the total number of items."),
                            (s + left, "forgot_to_divide", "Did not divide by the difference."),
                            (F(s + left, a + b) if (s + left) % (a + b) == 0 else None, "divided_by_sum", "Divided by the sum of the amounts."),
                            (kids + 1, "slip", "Off by 1."), (kids - 1, "slip", "Off by 1.")]
    return build(equal_total_two_ways, stem, ans, wrong, [f"Difference in {item} per child: {a} − {b} = {a - b}", f"Difference in total: {s} + {left} = {s + left}",
                                                         f"Children = {s + left} ÷ {a - b} = {kids}", f"Total = {b} × {kids} + {left} = {total}"],
                 {"a": a, "b": b, "s": s, "left": left, "ask": ask}, whole=True, show=str)


@checker(equal_total_two_ways)
def _(p):
    for k in range(1, 3000):
        if p["a"] * k - p["s"] == p["b"] * k + p["left"]:
            return F(k if p["ask"] == "kids" else p["a"] * k - p["s"])


@template(T, "competent", OPS + "15", OPS + "19")
def legs_assumption(r):
    """math-pat-assumption-guess-and-check"""
    hi = r.randint(0, 2)
    (A, a), (B, b), what = [(("tables", 4), ("stools", 3), "legs"), (("tricycles", 3), ("bicycles", 2), "wheels"),
                            (("$5 notes", 5), ("$2 notes", 2), "dollars")][hi]
    x = r.randint(5, 20)
    y = r.randint(5, 20)
    Nn = x + y
    L = a * x + b * y
    nm = r.choice(NAMES)
    if what == "dollars":
        stem = f"{nm} has {Nn} notes. Some are $5 notes and the rest are $2 notes. The notes are worth ${L} altogether. How many $5 notes does {nm} have?"
    else:
        stem = (f"A shop sells {A} and {B}. Each {A[:-1]} has {a} {what} and each {B[:-1]} has {b} {what}. "
                f"There are {Nn} altogether, with {L} {what} in all. How many {A} are there?")
    return build(legs_assumption, stem, x, [
        (y, "gave_other_type", f"Gave the number of {B}."),
        (F(L, a + b), "divided_by_sum", "Divided the total by the sum of the numbers per item."),
        (Nn, "assumed_all_one_type", "Assumed all were the first type."),
        (x + 1, "slip", "Off by 1."), (x - 1, "slip", "Off by 1.")],
        [f"If all were {B}: {Nn} × {b} = {Nn * b}", f"Extra = {L} − {Nn * b} = {L - Nn * b}", f"Each swap adds {a - b}: {L - Nn * b} ÷ {a - b} = {x}"],
        {"a": a, "b": b, "N": Nn, "L": L}, whole=True, show=str)


@checker(legs_assumption)
def _(p):
    return F(next(k for k in range(p["N"] + 1) if p["a"] * k + p["b"] * (p["N"] - k) == p["L"]))


@template(T, "competent", OPS + "15", OPS + "19", calc=True)
def set_cost(r):
    """math-pat-grouping-as-a-set"""
    nm = r.choice(NAMES)
    pc = r.randint(300, 1500)  # cents
    pk = r.choice([150, 200, 250, 50, 80, 120])
    k = r.randint(3, 8)
    sets = r.randint(3, 14)
    S = sets * (pc + k * pk)
    dpr = lambda c: f"${c // 100}.{c % 100:02d}"
    stem = (f"A cake costs {dpr(pc)} and a cookie costs {dpr(pk)}. {nm} bought {k} cookies for every cake and spent {dpr(S)} altogether. "
            f"How many cakes did {nm} buy?")
    return build(set_cost, stem, sets, [
        (F(S, pc), "used_one_item_only", "Divided the total by the price of a cake."),
        (F(S, pk), "used_cookie_price_only", "Divided the total by the price of a cookie."),
        (F(S, pc + pk), "added_unit_prices", "Added the two prices once, ignoring that there are several cookies."),
        (sets + 1, "slip", "Off by 1."), (sets - 1, "slip", "Off by 1.")],
        [f"One set: 1 cake + {k} cookies = {dpr(pc)} + {dpr(k * pk)} = {dpr(pc + k * pk)}", f"{dpr(S)} ÷ {dpr(pc + k * pk)} = {sets}"],
        {"pc": pc, "pk": pk, "k": k, "S": S}, whole=True, show=str)


@checker(set_cost)
def _(p):
    return F(brute(lambda n: n * (p["pc"] + p["k"] * p["pk"]) == p["S"], 1, 5000))


@template(T, "competent", OPS + "12", OPS + "16")
def day_after(r):
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    s = r.randint(0, 6)
    n = r.randint(60, 400)
    if n % 7 == 0:
        return None
    ans = (s + n) % 7
    show = lambda x: days[int(x) % 7]
    stem = f"Today is {days[s]}. What day of the week will it be {n} days from today?"
    return build(day_after, stem, F(ans + 1), [
        ((ans + 1) % 7 + 1, "off_by_one_day", "Counted today as day 1."),
        (((s + n // 7) % 7) + 1, "used_quotient_not_remainder", "Used the number of weeks instead of the remainder."),
        (((ans - 1) % 7) + 1, "off_by_one_day", "Counted one day too few."),
        (((s + 3) % 7) + 1, "slip", "Slip.")],
        [f"{n} ÷ 7 = {n // 7} remainder {n % 7}", f"Move {n % 7} days on from {days[s]}."],
        {"s": s, "n": n}, lambda x: days[int(x) - 1])


@checker(day_after)
def _(p):
    d = p["s"]
    for _ in range(p["n"]):
        d = (d + 1) % 7
    return F(d + 1)


# ================================================================ FACTORS AND MULTIPLES

def factors(n):
    return [d for d in range(1, n + 1) if n % d == 0]


@template(T, "basic", FM + "02", FM + "01")
def pick_factor(r):
    N = r.choice([36, 48, 60, 72, 84, 90, 96, 54, 64, 75, 80, 45, 56, 42, 66, 99, 78, 88])
    f = r.choice([x for x in range(3, 13) if N % x == 0])
    non = r.sample([x for x in range(3, 15) if N % x], 3)
    stem = f"Which of these numbers is a factor of {N}?"
    return build(pick_factor, stem, f, [(n_, "did_not_check_by_dividing", f"{N} is not divisible by {n_}.") for n_ in non],
                 [f"{N} ÷ {f} = {N // f}, with no remainder."], {"N": N, "f": f}, whole=True, show=str)


@checker(pick_factor)
def _(p):
    return F(p["f"]) if p["N"] % p["f"] == 0 else F(-1)


@template(T, "basic", FM + "04", FM + "01")
def pick_multiple(r):
    k = r.randint(3, 9)
    m = r.randint(6, 25)
    N = k * m
    s = str(N)
    swap = int(s[::-1])
    non = [N + 1, N - 1, N + 2, N + k - 1, N - k + 1, swap]
    non = [x for x in dict.fromkeys(non) if x % k and x > 0]
    stem = f"Which of these numbers is a multiple of {k}?"
    return build(pick_multiple, stem, N, [
        (non[0], "transposed_digits_or_off_by_one", f"{non[0]} is not in the {k} times table."),
        (non[1] if len(non) > 1 else None, "off_by_one_multiple", f"{non[1] if len(non) > 1 else ''} is not in the {k} times table."),
        (non[2] if len(non) > 2 else None, "off_by_one_multiple", f"{non[2] if len(non) > 2 else ''} is not in the {k} times table."),
        (non[3] if len(non) > 3 else None, "off_by_one_multiple", "Not a multiple.")],
        [f"{k} × {m} = {N}"], {"k": k, "N": N}, whole=True, show=str)


@checker(pick_multiple)
def _(p):
    return F(p["N"]) if p["N"] % p["k"] == 0 else F(-1)


def mlist(n, upto):
    """'n, 2n, ... , **upto**': every multiple of n up to and including `upto` (the answer is bold)."""
    return ", ".join(f"**{n * i}**" if n * i == upto else str(n * i) for i in range(1, upto // n + 1))


def flist(n, bold=None):
    """Complete factor list of n; `bold` (the answer) is marked."""
    return ", ".join(f"**{d}**" if d == bold else str(d) for d in factors(n))


@template(T, "basic", FM + "03", FM + "01")
def count_common_factors(r):
    a, b = r.sample([12, 16, 18, 20, 24, 30, 36, 40, 42, 48, 54, 60], 2)
    ans = len(set(factors(a)) & set(factors(b)))
    stem = f"How many common factors do {a} and {b} have?"
    return build(count_common_factors, stem, ans, [
        (gcd(a, b), "gave_the_hcf", "Gave the highest common factor instead of counting."),
        (len(factors(a)), "counted_factors_of_one_number", f"Counted the factors of {a} only."),
        (ans - 1, "left_out_1", "Left out the factor 1."), (ans + 1, "slip", "Counted one extra."),
        (len(factors(b)), "counted_factors_of_one_number", f"Counted the factors of {b} only.")],
        [f"Factors of {a}: {flist(a)}", f"Factors of {b}: {flist(b)}",
         f"Common: {', '.join(map(str, sorted(set(factors(a)) & set(factors(b)))))}"], {"a": a, "b": b}, whole=True, show=str)


@checker(count_common_factors)
def _(p):
    return F(sum(1 for d in range(1, min(p["a"], p["b"]) + 1) if p["a"] % d == 0 and p["b"] % d == 0))


@template(T, "basic", FM + "05", FM + "01")
def small_lcm(r):
    a, b = r.sample(range(2, 10), 2)
    L = lcm(a, b)
    stem = f"What is the smallest number that is a multiple of both {a} and {b}?"
    return build(small_lcm, stem, L, [
        (a * b, "multiplied_the_numbers", "Multiplied the two numbers."),
        (max(a, b), "gave_larger_number", "Gave the larger number."),
        (L + max(a, b), "next_common_multiple_slip", "Gave a later common multiple."),
        (gcd(a, b) if gcd(a, b) > 1 else None, "gave_the_hcf", "Gave the highest common factor."),
        (L - min(a, b), "slip", "Slip.")],
        [f"Multiples of {a}: {mlist(a, L)}", f"Multiples of {b}: {mlist(b, L)}",
         f"The first number in both lists is **{L}**.", f"Smallest common multiple: **{L}**"],
        {"a": a, "b": b}, whole=True, show=str)


@checker(small_lcm)
def _(p):
    return F(brute(lambda n: n % p["a"] == 0 and n % p["b"] == 0, 1, 500))


@template(T, "basic", FM + "03", FM + "02")
def small_hcf(r):
    g = r.randint(2, 9)
    a, b = r.sample([x for x in range(2, 13)], 2)
    if gcd(a, b) != 1:
        return None
    A, B = a * g, b * g
    stem = f"What is the greatest number that is a factor of both {A} and {B}?"
    return build(small_hcf, stem, g, [
        (A * B // g, "found_the_lcm", "Found the lowest common multiple."),
        (abs(A - B), "found_difference", "Gave the difference of the numbers."),
        (min(A, B) if min(A, B) % max(g, 1) == 0 and min(A, B) != g else None, "gave_smaller_number", "Gave the smaller number."),
        (g + 1, "slip", "Slip."), (max(1, g - 1), "slip", "Slip.")],
        [f"Factors of {A}: {flist(A, g)}", f"Factors of {B}: {flist(B, g)}", f"Greatest common factor: **{g}**"],
        {"A": A, "B": B}, whole=True, show=str)


@checker(small_hcf)
def _(p):
    return F(max(d for d in range(1, p["A"] + 1) if p["A"] % d == 0 and p["B"] % d == 0))


@template(T, "intermediate", FM + "03", FM + "01")
def hcf_word(r):
    g = r.randint(4, 15)
    a, b = r.sample(range(3, 13), 2)
    if gcd(a, b) != 1:
        return None
    A, B = a * g, b * g
    thing = r.choice(["ribbon", "rope", "wire"])
    stem = (f"Two pieces of {thing}, {A} cm and {B} cm long, are cut into pieces of equal length with no {thing} left over. "
            f"What is the greatest possible length of each piece, in cm?")
    return build(hcf_word, stem, g, [
        (A * B // g, "used_lcm", "Used the lowest common multiple."),
        (abs(A - B), "used_difference", "Gave the difference in length."),
        (g * 2 if A % (2 * g) == 0 and B % (2 * g) == 0 else None, "wrong_factor", "Gave a smaller common factor."),
        (g + 1, "slip", "Slip."), (g - 1, "slip", "Slip.")],
        [f"HCF of {A} and {B} is {g}."], {"A": A, "B": B}, whole=True, show=str)


@checker(hcf_word)
def _(p):
    return F(max(d for d in range(1, p["A"] + 1) if p["A"] % d == 0 and p["B"] % d == 0))


@template(T, "intermediate", FM + "05", FM + "04")
def lcm_word(r):
    a, b = r.sample([6, 8, 9, 10, 12, 15, 18, 20, 24, 25, 30], 2)
    if lcm(a, b) > 150:
        return None
    h, m = r.randint(6, 9), r.choice([0, 15, 30, 45])
    nm = r.choice(["bus A", "light A", "bell A"])
    L = lcm(a, b)
    stem = (f"Bus A leaves a stop every {plural(a, 'minute')} and Bus B leaves every {plural(b, 'minute')}. They both leave together at {h}:{m:02d} a.m. "
            f"After how many minutes will they next leave together?")
    return build(lcm_word, stem, L, [
        (a * b, "multiplied_the_numbers", "Multiplied the two times."),
        (gcd(a, b), "used_hcf", "Used the highest common factor."),
        (a + b, "added_times", "Added the two times."),
        (L + min(a, b), "slip", "Slip."), (L - min(a, b), "slip", "Slip.")],
        [f"LCM of {a} and {b} is {L}."], {"a": a, "b": b}, whole=True, show=lambda x: f"{plural(int(x), 'minute')}")


@checker(lcm_word)
def _(p):
    return F(brute(lambda n: n % p["a"] == 0 and n % p["b"] == 0, 1, 2000))


@template(T, "intermediate", FM + "05", FM + "04", calc=True)
def multiples_below_limit(r):
    """math-pat-multiples-factors-direct"""
    mode = r.choice(["largest_below", "smallest_above", "common_below"])
    if mode == "common_below":
        a, b = r.sample([4, 6, 8, 9, 10, 12], 2)
        L = lcm(a, b)
        lim = r.randint(L * 3 + 1, L * 12)
        ans = (lim - 1) // L * L if True else None
        stem = f"What is the greatest number smaller than {lim} that is a multiple of both {a} and {b}?"
        return build(multiples_below_limit, stem, ans, [
            ((lim - 1) // max(a, b) * max(a, b), "used_only_the_larger_number", f"Used multiples of {max(a, b)} only."),
            (ans + L, "went_over_the_limit", "Gave a common multiple that is over the limit."),
            (ans - L, "went_one_multiple_too_low", "Went one common multiple too low."),
            (lim - 1, "took_just_below_limit", "Took the number just below the limit."),
            (a * b * ((lim - 1) // (a * b)) if a * b * ((lim - 1) // (a * b)) else None, "used_product", "Used the product of the two numbers.")],
            [f"LCM = {L}", f"Largest multiple of {L} below {lim} = {ans}"], {"mode": mode, "a": a, "b": b, "lim": lim}, whole=True, show=str)
    k = r.randint(4, 19)
    lim = r.randint(150, 900)
    if mode == "largest_below":
        if lim % k == 0:
            lim += 1
        ans = lim // k * k
        stem = f"Find the largest multiple of {k} that is smaller than {lim}."
        wrong = [(lim - 1, "took_limit_itself", "Used a number next to the limit."), (ans - k, "went_one_multiple_too_low", "Went one multiple too low."),
                 (ans + k, "went_over_the_limit", "Went over the limit."), (lim - lim % k + k - 1 if False else ans + 1, "slip", "Slip.")]
    else:
        if lim % k == 0:
            lim += 1
        ans = (lim // k + 1) * k
        stem = f"Find the smallest multiple of {k} that is greater than {lim}."
        wrong = [(lim + 1, "took_limit_itself", "Used the number next to the limit."), (ans - k, "went_under_the_limit", "Gave a multiple below the limit."),
                 (ans + k, "went_one_multiple_too_high", "Went one multiple too high."), (ans + 1, "slip", "Slip.")]
    return build(multiples_below_limit, stem, ans, wrong, [f"{lim} ÷ {k} = {lim // k} remainder {lim % k}", f"Answer: {ans}"],
                 {"mode": mode, "k": k, "lim": lim, "a": 0, "b": 0}, whole=True, show=str)


@checker(multiples_below_limit)
def _(p):
    if p["mode"] == "common_below":
        return F(max(n for n in range(1, p["lim"]) if n % p["a"] == 0 and n % p["b"] == 0))
    if p["mode"] == "largest_below":
        return F(max(n for n in range(1, p["lim"]) if n % p["k"] == 0))
    return F(next(n for n in range(p["lim"] + 1, p["lim"] + 100) if n % p["k"] == 0))


@template(T, "competent", FM + "05", FM + "04")
def square_from_tiles(r):
    a, b = r.sample(range(3, 16), 2)
    if gcd(a, b) != 1 or abs(a - b) < 2:
        return None
    side = lcm(a, b)
    ans = (side // a) * (side // b)
    stem = (f"Rectangular tiles, each {a} cm by {b} cm, are all placed the same way round to make the smallest possible square. "
            f"How many tiles are needed?")
    return build(square_from_tiles, stem, ans, [
        (side, "gave_the_side_length", "Gave the side of the square in cm."),
        (a * b, "multiplied_the_sides", "Used the product of the sides as the number of tiles."),
        (side // a + side // b, "added_tiles_per_side", "Added the number of tiles along each side."),
        (ans + a, "slip", "Slip."), (ans - 1, "slip", "Slip.")],
        [f"Side of square = LCM of {a} and {b} = {side} cm", f"Tiles along one side: {side} ÷ {a} = {side // a}; along the other: {side // b}",
         f"Total = {side // a} × {side // b} = {ans}"], {"a": a, "b": b}, whole=True, show=str)


@checker(square_from_tiles)
def _(p):
    s = brute(lambda n: n % p["a"] == 0 and n % p["b"] == 0, 1, 5000)
    return F(s * s // (p["a"] * p["b"]))


@template(T, "competent", FM + "05", FM + "04")
def flash_together(r):
    a, b, c = r.sample([2, 3, 4, 5, 6, 8, 10, 12], 3)
    L = lcm(a, b, c)
    mins = r.randint(6, 30)
    secs = mins * 60
    if L > secs // 3 or L < 12:
        return None
    ans = secs // L
    stem = (f"Three lights flash every {a} seconds, {b} seconds and {c} seconds. They flash together at 8:00 p.m. "
            f"How many times will they flash together in the next {plural(mins, 'minute')}, not counting the one at 8:00 p.m.?")
    return build(flash_together, stem, ans, [
        (ans + 1, "counted_the_start", "Counted the flash at the start as well."),
        (secs // lcm(a, b), "used_two_lights_only", "Used only two of the lights."),
        (ans - 1, "counted_one_too_few", "Counted one too few."),
        (secs // (a * b * c) if secs // (a * b * c) else None, "used_product", "Used the product of the three numbers instead of the LCM.")],
        [f"LCM of {a}, {b}, {c} is {L} seconds.", f"{mins} min = {secs} s; {secs} ÷ {L} = {ans} remainder {secs % L}"],
        {"a": a, "b": b, "c": c, "secs": secs}, whole=True, show=str)


@checker(flash_together)
def _(p):
    return F(sum(1 for t in range(1, p["secs"] + 1) if t % p["a"] == 0 and t % p["b"] == 0 and t % p["c"] == 0))


@template(T, "competent", FM + "05", FM + "04")
def remainder_smallest(r):
    a, b = r.sample([4, 5, 6, 8, 9, 10, 12], 2)
    L = lcm(a, b)
    rem = r.randint(1, min(a, b) - 1)
    ans = L + rem
    stem = f"What is the smallest number greater than {rem} that leaves a remainder of {rem} when divided by {a} and also when divided by {b}?"
    return build(remainder_smallest, stem, ans, [
        (L, "forgot_the_remainder", "Gave the lowest common multiple without adding the remainder."),
        (a * b + rem if a * b != L else None, "used_product", "Used the product of the two numbers."),
        (L - rem, "subtracted_the_remainder", "Subtracted the remainder."),
        (ans + L, "next_number_slip", "Gave the next such number."), (ans + 1, "slip", "Slip.")],
        [f"LCM of {a} and {b} is {L}.", f"Number = {L} + {rem} = {ans}"], {"a": a, "b": b, "rem": rem}, whole=True, show=str)


@checker(remainder_smallest)
def _(p):
    return F(brute(lambda n: n > p["rem"] and n % p["a"] == p["rem"] and n % p["b"] == p["rem"], 1, 5000))


@template(T, "competent", FM + "03", FM + "01")
def squares_from_rectangle(r):
    g = r.randint(3, 12)
    a, b = r.sample(range(2, 10), 2)
    if gcd(a, b) != 1:
        return None
    A, B = a * g, b * g
    ans = a * b
    stem = f"A rectangle measuring {A} cm by {B} cm is cut into identical squares with no waste. The squares are as large as possible. How many squares are there?"
    return build(squares_from_rectangle, stem, ans, [
        (g, "gave_the_side", "Gave the side of one square in cm."),
        (A * B // 1 // (g if g else 1), "used_hcf_as_area", "Divided the area by the side instead of the area of one square."),
        (a + b, "added_squares_along_sides", "Added the numbers of squares along the sides."),
        (ans + a, "slip", "Slip."), (ans - 1, "slip", "Slip.")],
        [f"HCF of {A} and {B} is {g}, so each square has side {g} cm.", f"{A} ÷ {g} = {a}, {B} ÷ {g} = {b}", f"{a} × {b} = {ans}"],
        {"A": A, "B": B}, whole=True, show=str)


@checker(squares_from_rectangle)
def _(p):
    s = max(d for d in range(1, p["A"] + 1) if p["A"] % d == 0 and p["B"] % d == 0)
    return F((p["A"] * p["B"]) // (s * s))


# ================================================================ extra patterns (added after catalogue grew)

@template(T, "basic", OPS + "15", OPS + "16")
def big_four_ops(r):
    """math-pat-whole-number-four-ops-direct"""
    if r.random() < 0.5:
        a = r.choice([r.randint(1100, 9999), r.randint(1, 9) * 1000 + r.randint(1, 9)])
        b = r.choice([12, 15, 18, 25, 24, 35, 45, 16, 22, 36, 64])
        ans = a * b
        stem = f"Find the value of {num(a)} × {b}."
        expr = f"{num(a)} × {b}"
        u, t = b % 10, b // 10
        wrong = [(a * u + a * t, "forgot_place_holder_zero", "Forgot the zero when multiplying by the tens digit."),
                 (a * u + a * t * 100, "shifted_two_places", "Shifted the second row two places."),
                 (ans - a * 10 if ans > a * 10 else None, "missed_one_row", "Missed ten copies of the number."),
                 (ans + 1000, "careless_slip", "Slip with a carry."), (ans - 100, "careless_slip", "Slip with a carry.")]
        prm = {"a": a, "b": b, "mul": True}
    else:
        b = r.choice([12, 15, 16, 24, 25, 32, 35, 45])
        q = r.choice([r.randint(120, 990), r.randint(1, 9) * 100 + r.randint(1, 9)])
        a = q * b
        ans = q
        stem = f"Find the value of {num(a)} ÷ {b}."
        expr = f"{num(a)} ÷ {b}"
        wrong = [(int(str(q).replace("0", "", 1)) if "0" in str(q) else None, "dropped_zero_in_quotient", "Left out a zero in the quotient."),
                 (q + 10, "careless_slip", "Slip in the tens."), (q - 10, "careless_slip", "Slip in the tens."),
                 (q * 10 if q * 10 < a else None, "misplaced_digit", "Put the quotient digits one place too high."),
                 (q + 1, "careless_slip", "Slip in the ones.")]
        prm = {"a": a, "b": b, "mul": False}
    return build(big_four_ops, stem, ans, wrong, [f"{expr} = {num(ans)}"], prm, num, whole=True)


@checker(big_four_ops)
def _(p):
    if p["mul"]:
        return F(sum(p["a"] for _ in range(p["b"])))
    return F(brute(lambda q: q * p["b"] == p["a"], 1, 5000))


@template(T, "intermediate", NUM + "20", NUM + "16", NUM + "12")
def form_with_condition(r):
    """math-pat-form-numbers-from-digits"""
    while True:
        ds = r.sample(range(10), 4)
        if len([d for d in ds if d]) >= 3:
            break
    cond = r.choice(["even", "odd", "multiple of 5"])
    ok = {"even": lambda n: n % 2 == 0, "odd": lambda n: n % 2 == 1, "multiple of 5": lambda n: n % 5 == 0}[cond]
    big = r.random() < 0.5
    nums = sorted(int("".join(map(str, q))) for q in permutations(ds) if q[0] != 0)
    good = [n for n in nums if ok(n)]
    if not good:
        return None
    # greedy: choose the last digit first, then arrange the rest
    last_opts = [d for d in ds if ok(d)]
    best = None
    for last in last_opts:
        rest = [d for d in ds if d != last]
        if big:
            body = sorted(rest, reverse=True)
        else:
            body = sorted(rest)
            if body[0] == 0:
                if len(body) < 2 or body[1] == 0:
                    continue
                body[0], body[1] = body[1], body[0]
        v = int("".join(map(str, body + [last])))
        best = v if best is None or (v > best if big else v < best) else best
    ans = best
    other = max(nums) if big else min(nums)
    opposite = (min(good) if big else max(good))
    stem = (f"Use all the digits {', '.join(map(str, sorted(ds)))} once each to form the {'greatest' if big else 'smallest'} "
            f"4-digit {cond if cond != 'multiple of 5' else 'multiple of 5'} number. What is the number?")
    return build(form_with_condition, stem, ans, [
        (other if other != ans else None, "ignored_the_condition", f"Formed the {'greatest' if big else 'smallest'} number but it is not {a_an(cond)} {cond} number."),
        (opposite if opposite != ans else None, "gave_the_opposite", f"Gave the {'smallest' if big else 'greatest'} number that works."),
        (int(str(ans)[:2] + str(ans)[3] + str(ans)[2]), "swapped_last_two_digits", "Swapped the last two digits."),
        (int(str(ans)[1] + str(ans)[0] + str(ans)[2:]), "swapped_first_two_digits", "Swapped the first two digits.")],
        [f"The last digit must make the number {cond}.", f"Answer: {num(ans)}"], {"ds": ds, "cond": cond, "big": big}, num, whole=True)


@checker(form_with_condition)
def _(p):
    ok = {"even": lambda n: n % 2 == 0, "odd": lambda n: n % 2 == 1, "multiple of 5": lambda n: n % 5 == 0}[p["cond"]]
    nums = [int("".join(map(str, q))) for q in permutations(p["ds"]) if q[0] != 0 and ok(int("".join(map(str, q))))]
    return F(max(nums) if p["big"] else min(nums))


@template(T, "intermediate", OPS + "15", OPS + "19")
def more_than_total_model(r):
    """math-pat-whole-number-more-than-total-model"""
    a, b, c = r.sample(NAMES, 3)
    k = r.randint(2, 4)
    m = r.randint(5, 60)
    base = r.randint(20, 150)
    total = base * (2 + k) + m
    ask = r.choice(["b", "c"])
    stem = (f"{a}, {b} and {c} saved ${total} altogether. {b} saved ${m} more than {a}. {c} saved {'twice' if k == 2 else str(k) + ' times'} as much as {a}. "
            f"How much did {b if ask == 'b' else c} save?")
    ans = base + m if ask == "b" else k * base
    return build(more_than_total_model, stem, ans, [
        (F(total, 2 + k), "forgot_the_extra_amount", "Divided the total by the number of units without removing the extra."),
        (base if ask == "b" else base + m, "gave_the_wrong_person", f"Found {a}'s savings or mixed up the people."),
        (F(total - m, 2 + k + 1), "counted_one_unit_too_many", "Used one unit too many."),
        (ans + m if ask == "c" else ans + 10, "slip", "Slip."), (ans - 5, "slip", "Slip.")],
        [f"Take away the ${m} extra: ${total} − ${m} = ${total - m}", f"{2 + k} equal units: ${total - m} ÷ {2 + k} = ${base} for {a}", f"Answer: ${ans}"],
        {"total": total, "m": m, "k": k, "ask": ask}, whole=True, show=lambda v: f"${int(v)}")


@checker(more_than_total_model)
def _(p):
    for x in range(1, p["total"]):
        if x + (x + p["m"]) + p["k"] * x == p["total"]:
            return F(x + p["m"] if p["ask"] == "b" else p["k"] * x)


@template(T, "intermediate", OPS + "15", OPS + "19")
def age_problem(r):
    """math-pat-age-problems"""
    a, b = r.sample(["Mrs Tan", "Mr Lim", "Mdm Rani", "Mr Singh", "Aunt Mei", "Uncle Ben"], 2)
    s = r.randint(5, 14)
    n = r.randint(3, 10)
    k = r.randint(3, 5)
    M_future = k * (s + n)
    M_now = M_future - n
    d = M_now - s
    if d < 15 or d > 45:
        return None
    stem = f"{a} is {d} years older than {a.split()[0] + ' ' + a.split()[1] if False else 'the son'}. In {n} years' time, {a}'s age will be {k} times the son's age. How old is the son now?"
    stem = f"{a} is {d} years older than {a}'s son. In {n} years' time, {a}'s age will be {k} times the son's age. How old is the son now?"
    return build(age_problem, stem, s, [
        (s + n, "gave_the_age_in_the_future", "Gave the son's age in the future."),
        (F(d, k - 1), "forgot_the_years_passed", "Divided the age gap by one less than the multiple without allowing for the years."),
        (F(d, k), "divided_by_the_multiple", "Divided the age gap by the multiple."),
        (s + 1, "slip", "Off by 1."), (s - 1 if s > 1 else s + 2, "slip", "Off by 1.")],
        [f"The age gap stays {d} years.", f"In {n} years: son = 1 unit, {a} = {plural(k, 'unit')}, so {plural(k - 1, 'unit')} = {d}", f"1 unit = {F(d, k - 1)}, so the son will be {s + n}; now he is {s + n} − {n} = {s}"],
        {"d": d, "n": n, "k": k}, whole=True, show=str)


@checker(age_problem)
def _(p):
    for s_ in range(1, 100):
        if (s_ + p["d"] + p["n"]) == p["k"] * (s_ + p["n"]):
            return F(s_)


@template(T, "intermediate", OPS + "15", OPS + "13")
def number_grid_column(r):
    """math-pat-number-pattern-grid"""
    c = r.choice([4, 5, 6])
    N = r.randint(c * 8 + 1, c * 40)
    row = (N - 1) // c + 1
    pos = (N - 1) % c
    col = pos if row % 2 == 1 else c - 1 - pos
    L = "ABCDEFGH"
    ans = col + 1
    stem = (f"The counting numbers 1, 2, 3, ... are written in {c} columns, {L[0]} to {L[c - 1]}, as shown. Row 1 is written from {L[0]} to {L[c - 1]}, "
            f"Row 2 from {L[c - 1]} back to {L[0]}, and the rows keep going left to right, then right to left. In which column is {N} written?")
    return build(number_grid_column, stem, ans, [
        (pos + 1, "ignored_the_reversal", "Treated every row as running from left to right."),
        (c - pos, "reversed_every_row", "Treated every row as running from right to left."),
        (ans % c + 1, "slip", "Slip, off by one column."), (ans - 1 if ans > 1 else c, "slip", "Slip, off by one column."),
        (c, "slip", "Guessed the last column.")],
        [f"{N} ÷ {c} = {N // c} remainder {N % c}, so it is in Row {row}.", f"Row {row} runs {'left to right' if row % 2 else 'right to left'}.", f"Column {L[col]}"],
        {"c": c, "N": N}, whole=True, show=lambda v: f"Column {L[int(v) - 1]}", figure=number_grid_fig(c))


@checker(number_grid_column)
def _(p):
    c, N = p["c"], p["N"]
    n, r_ = 0, 0
    while n < N:
        r_ += 1
        cells = list(range(n + 1, n + c + 1))
        order = cells if r_ % 2 else cells[::-1]
        if N in cells:
            return F(order.index(N) + 1)
        n += c


# ================================================================ GROUP A GAPS: foundations (P1-P3)
# Early skills, revised at P6 standard: quick and direct at basic, multi-step at intermediate and competent.
import re as _re

def _unwords(s):
    n = 0
    for p in _re.split(r"[- ]", s):
        if p in TENS and p:
            n += 10 * TENS.index(p)
        elif p in ONES:
            n += ONES.index(p)
    return n


def _ev(s):
    return eval(s.replace("×", "*").replace("÷", "/").replace("−", "-"))


def _eq_true(s):
    a, b = s.split("=")
    return _ev(a) == _ev(b)


def _eqs(fn, stem, opts, ci, wrongs, steps, params):
    """Options are number sentences; the value is the option's position (1-4)."""
    return build(fn, stem, ci + 1, [(i + 1, t, w) for i, t, w in wrongs], steps, params,
                 show=lambda v: opts[int(v) - 1], whole=True, auto_slips=False)


def _eqs_check(p):
    good = [i for i, s in enumerate(p["opts"]) if _eq_true(s)]
    return F(good[0] + 1) if len(good) == 1 else None


# ---------------------------------------------------------------- NUM-01: counting and comparing sets

@template(T, "basic", NUM + "01")
def ga_count_one_shape(r):
    cs = r.sample(range(3, 11), 3)
    kind = r.randrange(3)
    nm = ["circles", "squares", "triangles"]
    total = sum(cs)
    who = r.choice(NAMES)
    n = cs[kind]
    stem = (f"{who} drew {plural(total, 'shape')} in a box: circles, squares and triangles, as shown. "
            f"How many {nm[kind]} did {who} draw?")
    return build(ga_count_one_shape, stem, n, [
        (total, "counted_every_shape", "Counted all the shapes instead of only one kind."),
        (cs[(kind + 1) % 3], "counted_the_wrong_shape", "Counted a different kind of shape."),
        *slip_set(n, 1)],
        [f"Count only the {nm[kind]}: {n}."], {"cs": cs, "kind": kind}, whole=True,
        figure=count_shapes_fig(tuple(cs), r.randrange(10 ** 6)))


@checker(ga_count_one_shape)
def _(p):
    shapes = ["c"] * p["cs"][0] + ["s"] * p["cs"][1] + ["t"] * p["cs"][2]
    return F(shapes.count("cst"[p["kind"]]))


@template(T, "intermediate", NUM + "01")
def ga_compare_boxes(r):
    cs = r.sample(range(5, 26), 3)
    L = "ABC"
    order = sorted(range(3), key=lambda i: cs[i])
    y, x = (order[0], order[2]) if r.random() < 0.5 else (order[0], order[1])
    who = r.choice(NAMES)
    d = cs[x] - cs[y]
    stem = (f"{who} put {sum(cs)} counters into three boxes, A, B and C, as shown. "
            f"How many more counters are in Box {L[x]} than in Box {L[y]}?")
    return build(ga_compare_boxes, stem, d, [
        (cs[x] + cs[y], "added_the_two_boxes", "Added the two boxes instead of finding the difference."),
        (cs[x], "gave_one_box_only", f"Gave the number in Box {L[x]} instead of the difference."),
        *slip_set(d, 1)],
        [f"Box {L[x]}: {cs[x]}, Box {L[y]}: {cs[y]}", f"{cs[x]} − {cs[y]} = {d}"],
        {"cs": cs, "x": x, "y": y}, whole=True, figure=dot_boxes_fig(cs, list(L)))


@checker(ga_compare_boxes)
def _(p):
    a, b = p["cs"][p["x"]], p["cs"][p["y"]]
    return F(len([k for k in range(b + 1, a + 1)]))


@template(T, "competent", NUM + "01", OPS + "19")
def ga_equalise_boxes(r):
    while True:
        cs = r.sample(range(5, 26), 3)
        if sum(cs) % 3 == 0:
            break
    m = sum(cs) // 3
    who = r.choice(NAMES)
    ans = sum(c - m for c in cs if c > m)
    stem = (f"{who} has {sum(cs)} counters in three boxes, A, B and C, as shown. {who} moves counters from the fuller boxes "
            f"to the emptier boxes until all three boxes have the same number. How many counters are moved altogether?")
    return build(ga_equalise_boxes, stem, ans, [
        (m, "gave_the_final_number_in_each_box", "Gave the number in each box at the end."),
        (max(cs) - min(cs), "used_the_biggest_difference", "Used the difference between the fullest and the emptiest box."),
        (sum(c - min(cs) for c in cs), "compared_with_the_smallest", "Compared every box with the emptiest box."),
        *slip_set(ans, 1)],
        [f"{sum(cs)} ÷ 3 = {m} in each box.", "Counters to move = how many the fuller boxes have above " + str(m) + f": {ans}"],
        {"cs": cs}, whole=True, figure=dot_boxes_fig(cs, list("ABC")))


@checker(ga_equalise_boxes)
def _(p):
    c, moves = list(p["cs"]), 0
    while len(set(c)) > 1:
        c[c.index(max(c))] -= 1
        c[c.index(min(c))] += 1
        moves += 1
    return F(moves)


# ---------------------------------------------------------------- NUM-03: read and write numbers to 100

@template(T, "basic", NUM + "03")
def ga_numeral_words_100(r):
    t, o = r.randint(2, 9), r.randint(1, 9)
    if t == o:
        return None
    n = 10 * t + o
    sw = 10 * o + t
    mode = r.randrange(2)
    wrongs = [(sw, "swapped_the_digits", "Wrote the tens digit and the ones digit the wrong way round."),
              (n + 10 if t < 9 else n - 10, "tens_word_slip", "Used the wrong tens word."),
              *slip_set(n, 1)]
    if mode == 0:
        stem = f"Which numeral stands for '{words(n)}'?"
        sh = str
    else:
        stem = f"Which of these is {n} written in words?"
        sh = lambda v: words(int(v)) if v > 0 else "0"
    return build(ga_numeral_words_100, stem, n, wrongs, [f"{t} tens and {o} ones: {n} = {words(n)}"],
                 {"w": words(n), "mode": mode}, show=sh, whole=True, auto_slips=False)


@checker(ga_numeral_words_100)
def _(p):
    return F(_unwords(p["w"]))


@template(T, "competent", NUM + "03", NUM + "04")
def ga_swap_digits_words(r):
    t, o = r.randint(3, 9), r.randint(1, 9)
    if t == o:
        return None
    n = 10 * t + o
    s = 10 * o + t
    k = r.randint(2, 6) * 10 + r.randint(1, 8)
    ans = s - k
    who = r.choice(NAMES)
    if ans < 10:
        return None
    stem = (f"{who} writes the number '{words(n)}' in numerals. {who} swaps its two digits to make a new number, "
            f"then subtracts '{words(k)}' from the new number. Which of these is the answer in words?")
    return build(ga_swap_digits_words, stem, ans, [
        (n - k, "forgot_to_swap", "Subtracted from the original number without swapping the digits."),
        (s + k, "added_instead", "Added instead of subtracting."),
        (abs(n - s) + k if abs(n - s) + k != ans else ans + 10, "other_slip", "Used the difference of the two numbers by mistake."),
        *slip_set(ans, 10)],
        [f"{words(n)} = {n}; swapped: {s}", f"{s} − {k} = {ans}", words(ans)],
        {"nw": words(n), "kw": words(k)}, show=lambda v: words(int(v)) if v > 0 else "0", whole=True, auto_slips=False)


@checker(ga_swap_digits_words)
def _(p):
    n, k = _unwords(p["nw"]), _unwords(p["kw"])
    return F(int(str(n)[::-1]) - k)


# ---------------------------------------------------------------- NUM-04: compare and order to 100

@template(T, "basic", NUM + "04")
def ga_greatest_least(r):
    ts = r.sample(range(1, 10), 3)
    nums = [10 * ts[0] + r.randint(0, 9), 10 * ts[0] + r.randint(0, 9), 10 * ts[1] + r.randint(0, 9), 10 * ts[2] + r.randint(0, 9)]
    if len(set(nums)) < 4:
        return None
    big = r.random() < 0.5
    ans = max(nums) if big else min(nums)
    opp = min(nums) if big else max(nums)
    others = [x for x in nums if x not in (ans, opp)]
    byones = sorted(others, key=lambda x: -(x % 10) if big else (x % 10))
    r.shuffle(nums)
    stem = f"Which is the {'greatest' if big else 'smallest'} of these numbers? {', '.join(map(str, nums))}"
    return build(ga_greatest_least, stem, ans, [
        (opp, "picked_the_opposite_extreme", f"Picked the {'smallest' if big else 'greatest'} number."),
        (byones[0], "compared_ones_digits_first", "Compared the ones digits before the tens digits."),
        (byones[1], "misread_the_order", "Did not compare the tens digits carefully.")],
        [f"Compare the tens first, then the ones: {ans}"], {"nums": nums, "big": big}, whole=True, auto_slips=False)


@checker(ga_greatest_least)
def _(p):
    s = sorted(p["nums"])
    return F(s[-1] if p["big"] else s[0])


@template(T, "intermediate", NUM + "04")
def ga_rank_or_between(r):
    if r.random() < 0.5:
        a = r.randint(12, 80)
        b = a + r.randint(5, 15)
        kind = r.randrange(3)
        lo_in, hi_in = [(False, False), (True, True), (False, True)][kind]
        txt = ["greater than {a} and smaller than {b}", "at least {a} and at most {b}",
               "greater than {a} and at most {b}"][kind].format(a=a, b=b)
        ans = len([x for x in range(100) if (x >= a if lo_in else x > a) and (x <= b if hi_in else x < b)])
        cand = [b - a, b - a + 1, b - a - 1]
        wr = [(c, "counted_the_end_numbers_wrongly", "Included or left out an end number by mistake.") for c in cand if c != ans]
        stem = f"How many whole numbers are {txt}?"
        return build(ga_rank_or_between, stem, ans, wr + slip_set(ans, 2), [f"List the numbers from {a} to {b} and check the end numbers: {ans}"],
                     {"mode": "between", "a": a, "b": b, "kind": kind}, whole=True, auto_slips=False)
    nums = r.sample(range(11, 99), 5)
    k = r.choice([2, 3, 4])
    s = sorted(nums)
    ans = s[k - 1]
    byones = sorted(nums, key=lambda x: (x % 10, x))[k - 1]
    r.shuffle(nums)
    stem = f"Arrange these numbers from the smallest to the greatest: {', '.join(map(str, nums))}. Which number is in position {k}?"
    wr = [(s[5 - k], "counted_from_the_greatest", "Counted the position from the greatest number."),
          (byones, "ordered_by_ones_digit", "Ordered the numbers by their ones digits."),
          (s[k], "off_by_one_position", "Picked the number one position too far."),
          (s[k - 2], "off_by_one_position", "Picked the number one position too early.")]
    return build(ga_rank_or_between, stem, ans, wr, [f"Smallest to greatest: {', '.join(map(str, s))}", f"Position {k}: {ans}"],
                 {"mode": "rank", "nums": nums, "k": k}, whole=True, auto_slips=False)


@checker(ga_rank_or_between)
def _(p):
    if p["mode"] == "rank":
        return F(sorted(p["nums"], key=lambda x: x)[p["k"] - 1])
    a, b, k = p["a"], p["b"], p["kind"]
    lo = a if k == 1 else a + 1
    hi = b if k in (1, 2) else b - 1
    return F(max(0, hi - lo + 1))


@template(T, "competent", NUM + "04", NUM + "08")
def ga_digit_cards_sum(r):
    ds = sorted(r.sample(range(1, 10), 4), reverse=True)
    a, b, c, d = ds
    most = r.random() < 0.5
    ans = 10 * (a + b) + (c + d) if most else 10 * (c + d) + (a + b)
    alt1 = (10 * a + b) + (10 * c + d) if most else (10 * d + c) + (10 * b + a)
    # a realistic wrong pairing: the second-best card in the tens with the best, or the second-smallest with the smallest
    alt2 = 10 * (a + c) + (b + d) if most else 10 * (b + d) + (a + c)
    r.shuffle(ds)
    stem = (f"{r.choice(NAMES)} has four digit cards: {', '.join(map(str, ds))}. Two 2-digit numbers are made using all four cards. "
            f"What is the {'greatest' if most else 'smallest'} possible sum of the two numbers?")
    return build(ga_digit_cards_sum, stem, ans, [
        (alt1, "made_the_numbers_one_after_the_other", "Made one number from the two best cards and the other from the rest, instead of using the best cards as tens digits."),
        (alt2, "put_the_wrong_cards_in_the_tens", "Put the wrong pair of cards in the tens place."),
        (a + b + c + d, "added_the_digits", "Added the four digits only."),
        *slip_set(ans, 9)],
        [f"Cards in order: {a}, {b}, {c}, {d}", f"Tens digits: {a} and {b}" if most else f"Tens digits: {d} and {c}", f"Sum = {ans}"],
        {"ds": ds, "most": most}, whole=True, auto_slips=False)


@checker(ga_digit_cards_sum)
def _(p):
    best = None
    for pm in permutations(p["ds"]):
        v = 10 * pm[0] + pm[1] + 10 * pm[2] + pm[3]
        best = v if best is None else (max(best, v) if p["most"] else min(best, v))
    return F(best)


# ---------------------------------------------------------------- NUM-05: number sequences up to 100

@template(T, "basic", NUM + "05")
def ga_missing_term(r):
    d = r.choice([2, 3, 4, 5, 10])
    a = r.randint(1, 100 - 6 * d)
    seq = [a + i * d for i in range(6)]
    i = r.randint(1, 4)
    ans = seq[i]
    shown = ", ".join("__" if j == i else str(v) for j, v in enumerate(seq))
    stem = f"What is the missing number in this pattern? {shown}"
    return build(ga_missing_term, stem, ans, [
        (seq[i + 1], "gave_the_next_term", "Gave the number after the gap."),
        (seq[i - 1], "gave_the_previous_term", "Gave the number before the gap."),
        *slip_set(ans, 1)],
        [f"The numbers go up by {d} each time.", f"{seq[i - 1]} + {d} = {ans}"],
        {"seq": [None if j == i else v for j, v in enumerate(seq)]}, whole=True, auto_slips=False)


@checker(ga_missing_term)
def _(p):
    s = p["seq"]
    k = s.index(None)
    known = [(j, v) for j, v in enumerate(s) if v is not None]
    d = F(known[-1][1] - known[0][1], known[-1][0] - known[0][0])
    return known[0][1] + (k - known[0][0]) * d


@template(T, "intermediate", NUM + "05")
def ga_alternating_rule(r):
    a, b = r.sample([2, 3, 4, 5, 6, 7], 2)
    s = r.randint(1, 12)
    n = r.randint(7, 10)

    def term(k):
        return s + (k // 2) * (a + b) + (k % 2) * a
    if term(n - 1) > 100:
        return None
    who = r.choice(NAMES)
    first = ", ".join(str(term(k)) for k in range(5))
    ans = term(n - 1)
    stem = (f"{who} makes a pattern: {first}, ... The rule is to add {a}, then add {b}, then add {a}, then add {b}, and so on. "
            f"What is the {ordn(n)} number in the pattern?")
    return build(ga_alternating_rule, stem, ans, [
        (s + (n - 1) * a, "used_only_the_first_step", f"Added {a} every time."),
        (term(n - 2), "off_by_one_term", "Gave the number one place too early."),
        (term(n), "off_by_one_term", "Gave the number one place too late."),
        *slip_set(ans, 1)],
        [f"Two steps add {a} + {b} = {a + b}.", f"The {ordn(n)} number is {ans}."], {"s": s, "a": a, "b": b, "n": n}, whole=True, auto_slips=False)


@checker(ga_alternating_rule)
def _(p):
    v, seq = p["s"], []
    for k in range(p["n"]):
        seq.append(v)
        v += p["a"] if k % 2 == 0 else p["b"]
    return F(seq[-1])


@template(T, "competent", NUM + "05", OPS + "19")
def ga_pattern_two_terms(r):
    d = r.randint(2, 9)
    i = r.randint(2, 4)
    j = i + r.randint(4, 6)
    k = j + r.randint(2, 4)
    a1 = r.randint(1, 12)
    vi, vj, vk = a1 + (i - 1) * d, a1 + (j - 1) * d, a1 + (k - 1) * d
    if vk > 100:
        return None
    stem = (f"The numbers in a pattern go up by the same amount each time. The {ordn(i)} number is {vi} and the {ordn(j)} number is {vj}. "
            f"What is the {ordn(k)} number?")
    return build(ga_pattern_two_terms, stem, vk, [
        (vj + (k - j + 1) * d, "counted_one_step_too_many", "Counted one step too many from the later number."),
        (vj + (k - j), "added_the_number_of_steps", "Added the number of places instead of the number of steps times the step."),
        (vi + (k - j) * d, "mixed_up_the_starting_number", "Started from the earlier number but counted only the later steps."),
        *slip_set(vk, d)],
        [f"{j - i} steps take the number from {vi} to {vj}, so each step is ({vj} − {vi}) ÷ {j - i} = {d}.",
         f"From {ordn(j)} to {ordn(k)} is {k - j} steps: {vj} + {k - j} × {d} = {vk}"],
        {"i": i, "vi": vi, "j": j, "vj": vj, "k": k}, whole=True, auto_slips=False)


@checker(ga_pattern_two_terms)
def _(p):
    for d in range(1, 60):
        a1 = p["vi"] - (p["i"] - 1) * d
        if a1 > 0 and a1 + (p["j"] - 1) * d == p["vj"]:
            return F(a1 + (p["k"] - 1) * d)


# ---------------------------------------------------------------- NUM-06: ordinal numbers

ORD = ["first", "second", "third", "fourth", "fifth", "sixth", "seventh", "eighth", "ninth", "tenth"]


@template(T, "basic", NUM + "06")
def ga_ordinal_basic(r):
    k = r.randint(3, 10)
    who = r.choice(NAMES)
    mode = r.randrange(3)
    if mode == 0:
        stem = f"Which of these shows '{ORD[k - 1]}' in symbols?"
        return build(ga_ordinal_basic, stem, k, [
            (11 - k, "counted_from_the_other_end", "Counted from the other end of the list."),
            (k + 1, "off_by_one_place", "Gave the next ordinal number."), (k - 1, "off_by_one_place", "Gave the ordinal number before.")],
            [f"{ORD[k - 1]} = {ordn(k)}"], {"w": ORD[k - 1], "mode": 0}, show=ordn, whole=True, auto_slips=False)
    side = "front" if mode == 1 else "back"
    stem = f"{who} is {ordn(k)} from the {side} of a queue. How many people are in front of {who}?" if mode == 1 else \
        f"{who} is {ordn(k)} from the front of a queue. How many people are behind {who} if there are {k + r.randint(2, 6)} people in the queue?"
    if mode == 1:
        return build(ga_ordinal_basic, stem, k - 1, [
            (k, "counted_the_person_too", f"Counted {who} as well."), (k + 1, "off_by_one_place", "Added one extra person."),
            (k - 2, "off_by_one_place", "Left out one person."), *slip_set(k - 1, 2)],
            [f"{k - 1} people stand in front of the {ordn(k)} person."], {"mode": 1, "k": k}, whole=True, auto_slips=False)
    n = int(stem.split("if there are ")[1].split()[0])
    return build(ga_ordinal_basic, stem, n - k, [
        (n - k + 1, "counted_the_person_too", f"Counted {who} as well."), (k, "gave_the_position", "Gave the position instead of how many are behind."),
        (n - k - 1, "off_by_one_place", "Left out one person."), *slip_set(n - k, 2)],
        [f"{n} − {k} = {n - k}"], {"mode": 2, "k": k, "n": n}, whole=True, auto_slips=False)


@checker(ga_ordinal_basic)
def _(p):
    if p["mode"] == 0:
        return F(ORD.index(p["w"]) + 1)
    if p["mode"] == 1:
        return F(len(list(range(1, p["k"]))))
    return F(len(list(range(p["k"] + 1, p["n"] + 1))))


@template(T, "intermediate", NUM + "06", OPS + "19")
def ga_queue_positions(r):
    who, w2 = two_names(r)
    if r.random() < 0.5:
        f, b = r.randint(3, 12), r.randint(3, 12)
        ans = f + b - 1
        stem = f"{who} is {ordn(f)} from the front of a queue and {ordn(b)} from the back. How many people are in the queue?"
        return build(ga_queue_positions, stem, ans, [
            (f + b, "counted_the_person_twice", f"Counted {who} twice."),
            (f + b - 2, "left_the_person_out", f"Left {who} out."),
            *slip_set(ans, 2)],
            [f"{f - 1} people in front + {who} + {b - 1} people behind = {ans}"], {"mode": "total", "f": f, "b": b}, whole=True, auto_slips=False)
    a = r.randint(2, 8)
    c = a + r.randint(4, 10)
    ans = c - a - 1
    stem = f"{who} is {ordn(a)} in a line and {w2} is {ordn(c)} in the same line. How many people are between {who} and {w2}?"
    return build(ga_queue_positions, stem, ans, [
        (c - a, "included_one_end_person", "Counted one of the two named people as well."),
        (c - a + 1, "included_both_end_people", "Counted both named people as well."),
        (c + a - 1, "added_the_positions", "Added the two positions."), *slip_set(ans, 2)],
        [f"{c} − {a} − 1 = {ans}"], {"mode": "between", "a": a, "c": c}, whole=True, auto_slips=False)


@checker(ga_queue_positions)
def _(p):
    if p["mode"] == "between":
        return F(len([x for x in range(p["a"] + 1, p["c"])]))
    for n in range(1, 100):
        if n - p["b"] + 1 == p["f"]:
            return F(n)


@template(T, "competent", NUM + "06", OPS + "19")
def ga_race_places(r):
    who, w2, w3 = r.sample(NAMES, 3)
    mode = r.randrange(3)
    if mode == 2:
        a, b, g = r.randint(3, 8), r.randint(3, 8), r.randint(2, 6)
        n = a + g + b
        stem = (f"Some children stand in a row. {who} is {ordn(a)} from the left and {w2} is {ordn(b)} from the right. "
                f"There are {g} children between {who} and {w2}. How many children are in the row?")
        return build(ga_race_places, stem, n, [
            (n + 1, "counted_one_extra", "Counted one extra child."), (a + b, "forgot_the_children_between", "Left out the children between them."),
            (n - 1, "left_one_out", "Left one child out."), *slip_set(n, 2)],
            [f"{a} + {g} + {b} = {n}"], {"mode": 2, "a": a, "b": b, "g": g}, whole=True, auto_slips=False)
    s, behind, ahead = r.randint(4, 7), r.randint(2, 5), r.randint(2, 3)
    ali = s + behind
    pri = s - ahead
    T_ = ali + r.randint(2, 8)
    if mode == 0:
        ans = T_ - ali
        q = f"How many runners finished behind {w3}?"
        stem = (f"{who} finished {ordn(s)} in a race. {w3} finished {behind} places behind {who}. "
                f"There were {T_} runners in the race and nobody tied. {q}")
        return build(ga_race_places, stem, ans, [
            (ans + 1, "counted_the_person_too", f"Counted {w3} as well."), (T_ - s, "forgot_the_places_behind", f"Counted from {who}'s place only."),
            (ans - 1, "off_by_one_place", "Left one runner out."), *slip_set(ans, 2)],
            [f"{w3} finished {ordn(ali)}.", f"{T_} − {ali} = {ans}"], {"mode": 0, "s": s, "behind": behind, "T": T_}, whole=True, auto_slips=False)
    ans = ali - pri - 1
    stem = (f"{who} finished {ordn(s)} in a race. {w2} finished {ahead} places ahead of {who} and {w3} finished {behind} places behind {who}. "
            f"How many runners finished between {w2} and {w3}?")
    return build(ga_race_places, stem, ans, [
        (behind + ahead, "forgot_the_person_in_the_middle", f"Forgot to count {who}."),
        (ali - pri, "included_one_end_person", "Counted one of the named runners."),
        (ans + 2, "included_both_end_people", "Counted both named runners."), *slip_set(ans, 2)],
        [f"{w2} was {ordn(pri)} and {w3} was {ordn(ali)}.", f"Runners between: {ali} − {pri} − 1 = {ans}"],
        {"mode": 1, "s": s, "behind": behind, "ahead": ahead}, whole=True, auto_slips=False)


@checker(ga_race_places)
def _(p):
    if p["mode"] == 2:
        for n in range(1, 100):
            L, R = p["a"], n - p["b"] + 1
            if R - L - 1 == p["g"]:
                return F(n)
    order = list(range(1, 60))
    if p["mode"] == 0:
        return F(len([x for x in order if p["s"] + p["behind"] < x <= p["T"]]))
    return F(len([x for x in order if p["s"] - p["ahead"] < x < p["s"] + p["behind"]]))


# ---------------------------------------------------------------- NUM-07: counting in tens and hundreds

@template(T, "basic", NUM + "07")
def ga_number_line_arrow(r):
    if r.random() < 0.75:
        step, lo = 10, r.randrange(100, 900, 10)
    else:
        step, lo = 100, 0
    k = r.randint(2, 9)
    hi = lo + 10 * step
    ans = lo + k * step
    stem = f"The number line goes from {lo} to {hi} in equal steps. What number does the arrow point to?"
    return build(ga_number_line_arrow, stem, ans, [
        (k * step, "forgot_the_starting_number", "Counted the steps from 0 instead of from the first number."),
        (lo + k, "counted_each_step_as_one", f"Counted each step as 1 instead of {step}."),
        (lo + (k + 1) * step, "counted_one_step_too_many", "Counted one step too many."),
        (lo + (k - 1) * step, "counted_one_step_too_few", "Counted one step too few."),
        (k * 10, "wrong_step_size", "Used the wrong step size.")],
        [f"The line has 10 equal steps from {lo} to {hi}, so each step is {step}.", f"{lo} + {k} × {step} = {ans}"],
        {"lo": lo, "step": step, "k": k}, whole=True, auto_slips=False, figure=number_line_fig(lo, step, 10, k))


@checker(ga_number_line_arrow)
def _(p):
    v = p["lo"]
    for _i in range(p["k"]):
        v += p["step"]
    return F(v)


@template(T, "basic", NUM + "07", NUM + "08")
def ga_tens_hundreds_more(r):
    unit = r.choice([10, 100])
    k = r.randint(2, 9)
    up = r.random() < 0.7
    n = r.randint(110, 880) if unit == 10 else r.randint(110, 880 - 100)
    if not up:
        n = r.randint(k * unit + 20, 990)
    if up and n + k * unit > 990:
        return None
    ans = n + k * unit if up else n - k * unit
    other = 100 if unit == 10 else 10
    u = "tens" if unit == 10 else "hundreds"
    stem = f"What number is {k} {u} {'more' if up else 'less'} than {n}?"
    sg = 1 if up else -1
    return build(ga_tens_hundreds_more, stem, ans, [
        (n + sg * k, "changed_the_ones", f"Changed the ones instead of the {u}."),
        (n + sg * k * other, "used_the_wrong_place", f"Changed the {'hundreds' if unit == 10 else 'tens'} instead of the {u}."),
        (n + sg * k * unit + sg * 1 * unit, "counted_one_too_many", f"Counted one {u[:-1]} too many."),
        (n + sg * (k - 1) * unit, "counted_one_too_few", f"Counted one {u[:-1]} too few.")],
        [f"{k} {u} = {k * unit}", f"{n} {'+' if up else '−'} {k * unit} = {ans}"],
        {"n": n, "k": k, "unit": unit, "up": up}, whole=True, auto_slips=False)


@checker(ga_tens_hundreds_more)
def _(p):
    v = p["n"]
    for _i in range(p["k"]):
        v = v + p["unit"] if p["up"] else v - p["unit"]
    return F(v)


@template(T, "intermediate", NUM + "07", OPS + "19")
def ga_count_on_and_back(r):
    n = r.randint(120, 600)
    a, b = r.randint(2, 6), r.randint(3, 9)
    ans = n + 100 * a - 10 * b
    who = r.choice(NAMES)
    stem = (f"{who} starts at {n} and counts on in hundreds {a} times. Then {who} counts back in tens {b} times. "
            f"What number does {who} reach?")
    return build(ga_count_on_and_back, stem, ans, [
        (n + 100 * a + 10 * b, "counted_on_both_times", "Counted on in both parts."),
        (n + 10 * a - 100 * b, "swapped_hundreds_and_tens", "Swapped the hundreds and the tens."),
        (n + 100 * a - 100 * b, "counted_back_in_hundreds", "Counted back in hundreds instead of tens."),
        (n + 100 * a - 10 * (b - 1), "slip_in_counting_back", "Counted back one ten too few."),
        (n + 100 * a - 10 * (b + 1), "slip_in_counting_back", "Counted back one ten too many.")],
        [f"{a} hundreds on: {n} + {100 * a} = {n + 100 * a}", f"{b} tens back: {n + 100 * a} − {10 * b} = {ans}"],
        {"n": n, "a": a, "b": b}, whole=True, auto_slips=False)


@checker(ga_count_on_and_back)
def _(p):
    v = p["n"]
    for _i in range(p["a"]):
        v += 100
    for _i in range(p["b"]):
        v -= 10
    return F(v)


@template(T, "competent", NUM + "07", NUM + "08")
def ga_packs_of_ten(r):
    unit, thing, pack = r.choice([(10, "stickers", "packs of 10 stickers"), (100, "beads", "boxes of 100 beads"),
                                  (10, "pencils", "packs of 10 pencils")])
    a = r.randint(3, 14) if unit == 10 else r.randint(2, 5)
    c = r.randint(2, 9) if unit == 10 else r.randint(1, 3)
    loose = r.randint(2, 9) if unit == 10 else r.randint(11, 89)
    d = r.randint(11, 39) if unit == 10 else r.randint(12, 90)
    who = r.choice(NAMES)
    total = unit * a + loose + unit * c - d
    if total < 5 or total > 990:
        return None
    stem = (f"{who} has {a} {pack} and {loose} loose {thing}. {who} buys {c} more {pack.split(' of')[0]} and then gives away {d} {thing}. "
            f"How many {thing} does {who} have now?")
    return build(ga_packs_of_ten, stem, total, [
        (a + loose + c - d, "counted_packs_as_ones", "Counted each pack as 1 instead of its full number."),
        (unit * a + unit * c - d, "left_out_the_loose_ones", "Left out the loose ones."),
        (unit * a + loose + unit * c + d, "added_instead_of_giving_away", "Added the ones given away."),
        *slip_set(total, unit)],
        [f"Packs: {a} + {c} = {a + c}, so {unit * (a + c)}", f"{unit * (a + c)} + {loose} − {d} = {total}"],
        {"unit": unit, "a": a, "c": c, "loose": loose, "d": d}, whole=True, auto_slips=False)


@checker(ga_packs_of_ten)
def _(p):
    items = [p["unit"]] * (p["a"] + p["c"]) + [1] * p["loose"]
    return F(len(items) and sum(items) - p["d"])


# ---------------------------------------------------------------- NUM-08: place value up to 1000

@template(T, "basic", NUM + "08")
def ga_place_value_digit(r):
    ds = r.sample(range(1, 10), 3)
    n = 100 * ds[0] + 10 * ds[1] + ds[2]
    pos = r.randrange(3)
    pn = ["ones", "tens", "hundreds"][pos]
    d = int(str(n)[::-1][pos])
    ans = d * 10 ** pos
    if r.random() < 0.5:
        stem = f"What is the value of the digit {d} in {n}?"
        wr = [(d, "gave_the_digit_not_its_value", "Gave the digit instead of its value."),
              (d * 10 ** ((pos + 1) % 3), "wrong_place", "Used the wrong place."),
              (d * 10 ** ((pos + 2) % 3), "wrong_place", "Used the wrong place."), *slip_set(ans, 1)]
        return build(ga_place_value_digit, stem, ans, wr, [f"{d} is in the {pn} place, so its value is {ans}."],
                     {"mode": "value", "n": n, "pos": pos}, whole=True, auto_slips=False)
    stem = f"In the number {n}, which digit is in the {pn} place?"
    others = [int(c) for c in str(n) if int(c) != d]
    return build(ga_place_value_digit, stem, d, [
        (others[0], "wrong_place", "Read the digit from the wrong place."),
        (others[1], "wrong_place", "Read the digit from the wrong place."), (ans if ans != d else n, "gave_the_value_not_the_digit", "Gave the value instead of the digit.")],
        [f"The {pn} digit of {n} is {d}."], {"mode": "digit", "n": n, "pos": pos}, whole=True, auto_slips=False)


@checker(ga_place_value_digit)
def _(p):
    digits = [int(c) for c in f"{p['n']:03d}"]
    h, t, o = digits
    d = [o, t, h][p["pos"]]
    return F(d if p["mode"] == "digit" else d * [1, 10, 100][p["pos"]])


@template(T, "intermediate", NUM + "08")
def ga_hundreds_tens_ones(r):
    if r.random() < 0.6:
        h, t, o = r.randint(2, 7), r.randint(11, 25), r.randint(1, 9)
        n = 100 * h + 10 * t + o
        if n > 990:
            return None
        stem = f"What number is made up of {h} hundreds, {t} tens and {o} ones?"
        return build(ga_hundreds_tens_ones, stem, n, [
            (100 * h + t + o, "treated_tens_as_ones", "Treated the tens as ones."),
            (100 * h + 10 * (t % 10) + o, "ignored_the_extra_hundreds", "Wrote only the tens digit and forgot that 10 tens make a hundred."),
            (int(f"{h}{t}{o}"), "wrote_the_digits_side_by_side", "Wrote the numbers side by side."),
            *slip_set(n, 10)],
            [f"{t} tens = {10 * t}", f"{100 * h} + {10 * t} + {o} = {n}"], {"mode": "make", "h": h, "t": t, "o": o}, whole=True, auto_slips=False)
    n = r.randint(111, 989)
    if n % 10 == 0:
        return None
    ans = n // 10
    stem = f"How many tens are there in {n}? Count only complete tens."
    return build(ga_hundreds_tens_ones, stem, ans, [
        (n % 100 // 10, "gave_the_tens_digit", "Gave the digit in the tens place."),
        (n // 100, "gave_the_hundreds_digit", "Gave the digit in the hundreds place."),
        (n // 10 + 1, "rounded_up", "Counted the ones as another ten."), *slip_set(ans, 1)],
        [f"{n} = {ans} tens and {n % 10} ones."], {"mode": "tens", "n": n}, whole=True, auto_slips=False)


@checker(ga_hundreds_tens_ones)
def _(p):
    if p["mode"] == "make":
        return F(sum([100] * p["h"] + [10] * p["t"] + [1] * p["o"]))
    k = 0
    while (k + 1) * 10 <= p["n"]:
        k += 1
    return F(k)


@template(T, "competent", NUM + "08", NUM + "04")
def ga_digit_clues(r):
    while True:
        h, t, d = r.randint(1, 9), r.randint(0, 6), r.randint(1, 3)
        o = t + d
        if o <= 9 and len({h, t, o}) == 3:
            break
    S = h + t + o
    n = 100 * h + 10 * t + o
    stem = (f"A 3-digit number has {h} in the hundreds place. The digit in the ones place is {d} more than the digit in the tens place. "
            f"The sum of its three digits is {S}. What is the number?")
    return build(ga_digit_clues, stem, n, [
        (100 * h + 10 * o + t, "swapped_tens_and_ones", "Swapped the tens digit and the ones digit."),
        (100 * h + 10 * (t + d) + (t + d) if t + d <= 9 else n + 11, "used_the_clue_for_both_digits", "Used the same digit for both places."),
        (100 * h + 10 * (o + 1 if o < 9 else o - 1) + t, "wrong_digit_sum", "Did not check that the digits add up to the sum."),
        *slip_set(n, 10)],
        [f"Tens + ones = {S} − {h} = {S - h}", f"Ones = tens + {d}, so 2 × tens + {d} = {S - h}", f"Tens = {t}, ones = {o}"],
        {"h": h, "d": d, "S": S}, whole=True, auto_slips=False)


@checker(ga_digit_clues)
def _(p):
    hits = [n for n in range(100, 1000)
            if n // 100 == p["h"] and n % 10 - n // 10 % 10 == p["d"] and sum(map(int, str(n))) == p["S"]]
    return F(hits[0]) if len(hits) == 1 else None


@template(T, "competent", NUM + "08", NUM + "04")
def ga_greatest_even_number(r):
    ds = r.sample(range(0, 10), 4)
    evens = sorted(int("".join(map(str, p))) for p in permutations(ds, 3)
                   if p[0] != 0 and p[2] % 2 == 0)
    if len(evens) < 4:
        return None
    ans = evens[-1]
    allv = sorted(int("".join(map(str, p))) for p in permutations(ds, 3) if p[0] != 0)
    who = r.choice(NAMES)
    stem = (f"{who} has four digit cards: {', '.join(map(str, ds))}. {who} chooses three of the cards to make a 3-digit even number. "
            f"What is the greatest even number {who} can make?")
    return build(ga_greatest_even_number, stem, ans, [
        (allv[-1], "ignored_the_even_condition", "Made the greatest number but forgot it must be even."),
        (evens[-2], "stopped_at_a_near_miss", "Chose a good number but not the greatest even one."),
        (evens[-3], "stopped_at_a_near_miss", "Chose a good number but not the greatest even one."),
        (evens[0], "made_the_smallest", "Made the smallest even number.")],
        ["The ones digit must be even, so try each even card in the ones place and arrange the others from greatest to smallest.", f"Greatest: {ans}"],
        {"ds": ds}, whole=True, auto_slips=False)


@checker(ga_greatest_even_number)
def _(p):
    best = 0
    for a in p["ds"]:
        for b in p["ds"]:
            for c in p["ds"]:
                if len({a, b, c}) == 3 and a != 0 and c % 2 == 0:
                    best = max(best, 100 * a + 10 * b + c)
    return F(best)


# ---------------------------------------------------------------- OPS-01: addition and subtraction concepts

@template(T, "basic", OPS + "01")
def ga_number_bond(r):
    whole = r.randint(30, 99)
    part = r.randint(11, whole - 8)
    other = whole - part
    form = r.randrange(3)
    if form == 0:
        stem = f"In a number bond, the whole is {whole} and one part is {part}. What is the other part?"
        ans, eq = other, f"x + {part} = {whole}"
        wr = [(whole + part, "added_the_whole_and_the_part", "Added the whole and the part."), (abs(whole - part - 10), "slip_in_renaming", "Made a slip when renaming."),
              (part, "gave_the_part_given", "Gave the part that was already given.")]
    elif form == 1:
        stem = f"Find the missing number: {part} + __ = {whole}"
        ans, eq = other, f"{part} + x = {whole}"
        wr = [(whole + part, "added_instead_of_subtracting", "Added instead of subtracting."), (part + 10 if part + 10 != other else part - 10, "slip_in_renaming", "Made a slip when renaming."),
              (whole - part + 10, "slip_in_renaming", "Forgot to rename a ten.")]
    else:
        stem = f"Find the missing number: {whole} − __ = {part}"
        ans, eq = other, f"{whole} − x = {part}"
        wr = [(whole + part, "added_instead_of_subtracting", "Added the two numbers."), (part, "gave_the_number_given", "Copied the number after the equals sign."),
              (whole - part + 10, "slip_in_renaming", "Forgot to rename a ten.")]
    return build(ga_number_bond, stem, ans, wr + slip_set(ans, 1), [f"{whole} − {part} = {other}"], {"eq": eq}, whole=True, auto_slips=False)


@checker(ga_number_bond)
def _(p):
    lhs, rhs = p["eq"].split("=")
    return next((F(x) for x in range(1, 200) if _ev(lhs.replace("x", f"({x})")) == int(rhs)), None)


@template(T, "intermediate", OPS + "01")
def ga_check_sentence(r):
    a, b = r.randint(21, 70), r.randint(11, 29)
    c = a + b
    if r.random() < 0.5:
        stem = f"Which number sentence can be used to check that {c} − {b} = {a}?"
        opts = [f"{a} + {b} = {c}", f"{c} + {b} = {a}", f"{a} − {b} = {c}", f"{b} − {a} = {c}"]
        why = ["Added the answer and the number taken away to get back to the whole."]
    else:
        stem = f"Which subtraction sentence can be used to check that {a} + {b} = {c}?"
        opts = [f"{c} − {b} = {a}", f"{a} − {b} = {c}", f"{b} − {c} = {a}", f"{a} − {c} = {b}"]
        why = ["Took one part away from the whole to get back the other part."]
    if sum(_eq_true(s) for s in opts) != 1 or len(set(opts)) < 4:
        return None
    wrongs = [(1, "mixed_up_the_whole_and_the_parts", "Put the whole in the wrong place."),
              (2, "mixed_up_the_whole_and_the_parts", "Put the whole in the wrong place."),
              (3, "wrote_the_numbers_in_the_wrong_order", "Wrote the numbers in the wrong order.")]
    r_ = r.sample(range(4), 4)
    opts = [opts[i] for i in r_]
    ci = r_.index(0)
    return _eqs(ga_check_sentence, stem, opts, ci, [(r_.index(i), t, w) for i, t, w in wrongs], why + [f"Whole = {c}; parts = {a} and {b}."], {"opts": opts})


@checker(ga_check_sentence)
def _(p):
    return _eqs_check(p)


@template(T, "competent", OPS + "01", OPS + "19")
def ga_equal_after_giving(r):
    who, w2 = two_names(r)
    g = r.randint(6, 24)
    tot = 2 * r.randint(25, 48)
    a0 = tot // 2 + g
    stem = (f"{who} and {w2} have {tot} stickers altogether. After {who} gives {g} stickers to {w2}, they have the same number of stickers. "
            f"How many stickers did {who} have at first?")
    return build(ga_equal_after_giving, stem, a0, [
        (tot // 2, "ignored_the_stickers_given", "Gave the number each has at the end."),
        (tot // 2 - g, "gave_w2_s_amount", f"Gave how many {w2} had at first."),
        (tot // 2 + 2 * g, "counted_the_move_twice", "Counted the stickers given twice."),
        *slip_set(a0, 1)],
        [f"{tot} ÷ 2 = {tot // 2} each at the end.", f"{who} had {tot // 2} + {g} = {a0} at first."], {"tot": tot, "g": g}, whole=True, auto_slips=False)


@checker(ga_equal_after_giving)
def _(p):
    return next(F(a) for a in range(1, p["tot"]) if a - p["g"] == p["tot"] - a + p["g"])


# ---------------------------------------------------------------- OPS-02: adding and subtracting within 100

@template(T, "basic", OPS + "02")
def ga_add_ones_chain(r):
    k = r.choice([3, 4, 5])
    xs = [r.randint(2, 9) for _ in range(k)]
    s = sum(xs)
    stem = f"Find the value of {' + '.join(map(str, xs))}."
    return build(ga_add_ones_chain, stem, s, [
        (s - xs[0], "left_one_number_out", "Left out one of the numbers."),
        (s + xs[-1], "counted_one_number_twice", "Added one of the numbers twice."),
        (s + 10, "slip_when_bridging_ten", "Made a slip when making a ten."), (s - 10, "slip_when_bridging_ten", "Made a slip when making a ten."),
        *slip_set(s, 1)],
        [f"Add in pairs that make 10 where you can: total {s}."], {"xs": xs}, whole=True, auto_slips=False)


@checker(ga_add_ones_chain)
def _(p):
    t = 0
    for x in p["xs"]:
        t += x
    return F(t)


@template(T, "basic", OPS + "02")
def ga_add_sub_renaming(r):
    if r.random() < 0.5:
        a, b = r.randint(15, 78), r.randint(12, 60)
        if (a % 10) + (b % 10) < 10 or a + b > 100:
            return None
        ans = a + b
        stem = f"Find {a} + {b}."
        wr = [(ans - 10, "forgot_to_carry", "Forgot to add the extra ten."), (ans + 10, "carried_twice", "Added the extra ten twice."),
              (ans - 9, "slip_when_carrying", "Made a slip when carrying.")]
        mode = "add"
    else:
        a, b = r.randint(41, 99), r.randint(12, 38)
        if a % 10 >= b % 10 or a <= b:
            return None
        ans = a - b
        stem = f"Find {a} − {b}."
        wr = [(10 * (a // 10 - b // 10) + (b % 10 - a % 10), "took_the_smaller_digit_from_the_larger", "Subtracted the smaller ones digit from the larger one."),
              (ans + 10, "forgot_to_rename", "Forgot to take 1 ten away after renaming."),
              (ans - 10, "took_the_ten_twice", "Took away the renamed ten twice.")]
        mode = "sub"
    return build(ga_add_sub_renaming, stem, ans, wr + slip_set(ans, 1), [f"{a} {'+' if mode == 'add' else '−'} {b} = {ans}"],
                 {"a": a, "b": b, "mode": mode}, whole=True, auto_slips=False)


@checker(ga_add_sub_renaming)
def _(p):
    a, b = p["a"], p["b"]
    if p["mode"] == "add":
        ones, carry = (a % 10 + b % 10) % 10, (a % 10 + b % 10) // 10
        return F(10 * (a // 10 + b // 10 + carry) + ones)
    borrow = 1 if a % 10 < b % 10 else 0
    return F(10 * (a // 10 - b // 10 - borrow) + (a % 10 + 10 * borrow - b % 10))


CTX = [("A bookshop had", "books", "sold", "received"), ("A bakery made", "buns", "sold", "baked"),
       ("A school hall had", "chairs", "removed", "added"), ("A fruit stall had", "oranges", "sold", "restocked")]


@template(T, "intermediate", OPS + "02", OPS + "19")
def ga_three_step_100(r):
    lead, item, down, up = r.choice(CTX)
    a, b, c = r.randint(40, 95), r.randint(12, 38), r.randint(11, 35)
    if r.random() < 0.5:
        ans = a - b + c
        if a - b < 1 or ans > 100:
            return None
        stem = f"{lead} {a} {item}. {down.capitalize()} {b} {item}, then {up} {c} more. How many {item} are there now?"
        wr = [(a - b - c, "subtracted_both", "Subtracted both numbers."), (a + b + c, "added_both", "Added both numbers."), (a - b, "left_out_the_last_step", "Forgot the last step.")]
        sg = (1, -1, 1)
    else:
        ans = a + b - c
        if a + b > 100 or ans < 1:
            return None
        stem = f"{lead} {a} {item}. It {up} {b} more {item}, then {down} {c}. How many {item} are there now?"
        wr = [(a - b - c, "used_the_wrong_signs", "Used the wrong signs."), (a + b + c, "added_both", "Added both numbers."), (a + b, "left_out_the_last_step", "Forgot the last step.")]
        sg = (1, 1, -1)
    return build(ga_three_step_100, stem, ans, wr + slip_set(ans, 10), [f"{a} {'+' if sg[1] > 0 else '−'} {b} {'+' if sg[2] > 0 else '−'} {c} = {ans}"],
                 {"a": a, "b": b, "c": c, "s1": sg[1], "s2": sg[2]}, whole=True, auto_slips=False)


@checker(ga_three_step_100)
def _(p):
    v = p["a"]
    v += p["s1"] * p["b"]
    v += p["s2"] * p["c"]
    return F(v)


@template(T, "competent", OPS + "02", OPS + "19")
def ga_game_scores(r):
    who = r.choice(NAMES)
    xs = [r.randint(5, 9) for _ in range(4)]
    L, G = r.randint(8, 19), r.randint(15, 30)
    S = sum(xs)
    ans = S - L + G
    if S - L < 5:
        return None
    stem = (f"In a game, {who} scored {xs[0]}, {xs[1]}, {xs[2]} and {plural(xs[3], 'point')} in the first four rounds. "
            f"{who} lost {plural(L, 'point')} in the fifth round and won {plural(G, 'point')} in the sixth round. What is {who}'s score after six rounds?")
    return build(ga_game_scores, stem, ans, [
        (S + L + G, "added_the_lost_points", "Added the points lost."), (S - L - G, "subtracted_the_won_points", "Subtracted the points won."),
        (S + L - G if S + L - G > 0 else S + 2 * L, "mixed_up_gain_and_loss", "Swapped the gain and the loss."), *slip_set(ans, 10)],
        [f"First four rounds: {S}", f"{S} − {L} + {G} = {ans}"], {"xs": xs, "L": L, "G": G}, whole=True, auto_slips=False)


@checker(ga_game_scores)
def _(p):
    score = 0
    for x in p["xs"]:
        score += x
    score -= p["L"]
    score += p["G"]
    return F(score)


# ---------------------------------------------------------------- OPS-03: mental calculation

@template(T, "basic", OPS + "03")
def ga_mental_basic(r):
    mode = r.randrange(3)
    if mode == 0:
        if r.random() < 0.5:
            a, b = r.randint(6, 12), r.randint(5, 9)
            if a + b > 20 or a + b < 11:
                return None
            e, ans, op = f"{a} + {b}", a + b, "+"
        else:
            a, b = r.randint(12, 19), r.randint(4, 9)
            if a % 10 >= b:
                return None
            e, ans, op = f"{a} − {b}", a - b, "−"
        wr = [(a + b if op == "−" else abs(a - b), "used_the_wrong_operation", "Used the wrong operation."),
              (ans + 10, "slip_over_ten", "Slipped when crossing 10."), (ans - 10, "slip_over_ten", "Slipped when crossing 10.")]
    elif mode == 1:
        a, b = r.randint(21, 89), r.randint(1, 8)
        up = r.random() < 0.5
        if (a % 10 + b > 9) if up else (a % 10 < b):
            return None
        e, ans, op = f"{a} {'+' if up else '−'} {b}", (a + b if up else a - b), "+" if up else "−"
        wr = [(a + 10 * b if up else a - 10 * b, "changed_the_tens", "Changed the tens digit instead of the ones digit."),
              (a + 10 * b + b if up else a - b + 10, "tens_and_ones_confused", "Mixed up tens and ones."),
              (ans + 10, "slip_over_ten", "Slipped with the tens."), (ans - 10, "slip_over_ten", "Slipped with the tens.")]
    else:
        a, b = r.randint(11, 89), r.randint(1, 5) * 10
        up = r.random() < 0.5
        if (a + b > 99) if up else (a <= b):
            return None
        e, ans, op = f"{a} {'+' if up else '−'} {b}", (a + b if up else a - b), "+" if up else "−"
        wr = [(a + b // 10 if up else a - b // 10, "changed_the_ones", "Changed the ones digit instead of the tens digit."),
              (a + b + 1 if up else a - b + 1, "slip_in_ones", "Changed the ones digit by mistake."),
              (ans + 10, "slip_with_the_tens", "Slipped with the tens."), (ans - 10, "slip_with_the_tens", "Slipped with the tens.")]
    stem = f"Without using paper, work out {e}."
    return build(ga_mental_basic, stem, ans, wr, [f"{e} = {ans}"], {"e": e}, whole=True, auto_slips=False)


@checker(ga_mental_basic)
def _(p):
    toks = p["e"].split()
    a, op, b = int(toks[0]), toks[1], int(toks[2])
    v = a
    for _i in range(b):
        v += 1 if op == "+" else -1
    return F(v)


@template(T, "intermediate", OPS + "03", OPS + "19")
def ga_mental_chain(r):
    v = r.randint(21, 70)
    who = r.choice(NAMES)
    steps = []
    cur = v
    for _i in range(4):
        kind = r.choice(["+t", "-t", "+o", "-o"])
        if kind == "+t" and cur <= 80:
            amt = r.randint(1, 3) * 10
            cur += amt
        elif kind == "-t" and cur >= 40:
            amt = r.randint(1, 3) * 10
            cur -= amt
        elif kind == "+o" and cur % 10 <= 5:
            amt = r.randint(1, 9 - cur % 10)
            cur += amt
        elif kind == "-o" and cur % 10 >= 2:
            amt = r.randint(1, cur % 10)
            cur -= amt
        else:
            return None
        steps.append((kind[0], amt))
    ans = cur
    if ans < 5 or ans > 99:
        return None
    txt = ", then ".join(f"{'adds' if s == '+' else 'subtracts'} {a}" for s, a in steps)
    stem = f"{who} thinks of the number {v}. {who} {txt}. What number does {who} get at the end?"
    flip = v + sum(a if s == "+" else -a for s, a in steps[:-1]) + (steps[-1][1] if steps[-1][0] == "-" else -steps[-1][1])
    ones_as_tens = v + sum((a * 10 if a < 10 else a) * (1 if s == "+" else -1) for s, a in steps)
    return build(ga_mental_chain, stem, ans, [
        (ans - steps[-1][1] * (1 if steps[-1][0] == "+" else -1), "left_out_the_last_step", "Left out the last step."),
        (flip, "reversed_the_last_operation", "Did the opposite of the last step."),
        (ones_as_tens, "tens_and_ones_confused", "Treated a number of ones as tens."),
        *slip_set(ans, 10)],
        [f"Start at {v}"] + [f"{s} {a}" for s, a in steps] + [f"Answer: {ans}"], {"v": v, "steps": steps}, whole=True, auto_slips=False)


@checker(ga_mental_chain)
def _(p):
    v = p["v"]
    for s, a in p["steps"]:
        for _i in range(a):
            v += 1 if s == "+" else -1
    return F(v)


@template(T, "competent", OPS + "03", OPS + "19")
def ga_mental_three_friends(r):
    a_, b_, c_ = r.sample(NAMES, 3)
    a = r.randint(24, 59)
    d1 = r.randint(1, 4) * 10
    d2 = r.randint(1, a % 10) if a % 10 else None
    if not d2:
        return None
    rv = a + d1
    sv = rv - d2
    tot = a + rv + sv
    stem = (f"{a_} has {a} stickers. {b_} has {d1} more stickers than {a_}. {c_} has {d2} fewer stickers than {b_}. "
            f"How many stickers do the three children have altogether?")
    return build(ga_mental_three_friends, stem, tot, [
        (a + rv, "left_out_the_third_child", f"Left out {c_}."), (a + rv + a - d2, "compared_with_the_wrong_child", f"Compared {c_} with {a_} instead of {b_}."),
        (a + rv + rv + d2, "swapped_fewer_and_more", "Used 'more' instead of 'fewer'."), *slip_set(tot, 10)],
        [f"{b_}: {a} + {d1} = {rv}", f"{c_}: {rv} − {d2} = {sv}", f"Total: {a} + {rv} + {sv} = {tot}"],
        {"a": a, "d1": d1, "d2": d2}, whole=True, auto_slips=False)


@checker(ga_mental_three_friends)
def _(p):
    kids = [p["a"]]
    kids.append(kids[0] + p["d1"])
    kids.append(kids[1] - p["d2"])
    return F(sum(kids))


# ---------------------------------------------------------------- OPS-04: multiplication and division concepts

@template(T, "basic", OPS + "04")
def ga_repeated_addition(r):
    k, m = r.randint(3, 8), r.randint(2, 9)
    if k * m > 40 or k == m:
        return None
    opts = [f"{k} × {m}", f"{k} × {k}", f"{m} × {m}", f"{k} + {m}"]
    tot = k * m
    ads = " + ".join([str(m)] * k)
    stem = f"Which expression has the same value as {ads}?"
    r_ = r.sample(range(4), 4)
    shown = [opts[i] for i in r_]
    wr = [(r_.index(1), "squared_the_number_of_groups", "Multiplied the number of groups by itself."),
          (r_.index(2), "squared_the_number_added", "Multiplied the number being added by itself."),
          (r_.index(3), "added_the_two_numbers", "Added the number of groups and the number in each group.")]
    if len({_ev(s) for s in opts}) < 4:
        return None
    return build(ga_repeated_addition, stem, r_.index(0) + 1, [(i + 1, t, w) for i, t, w in wr],
                 [f"{ads} has {k} lots of {m}, so it is {k} × {m} = {tot}."], {"opts": shown, "k": k, "m": m},
                 show=lambda v: shown[int(v) - 1], whole=True, auto_slips=False)


@checker(ga_repeated_addition)
def _(p):
    tot = 0
    for _i in range(p["k"]):
        tot += p["m"]
    hit = [i for i, s in enumerate(p["opts"]) if _ev(s) == tot]
    return F(hit[0] + 1) if len(hit) == 1 else None


@template(T, "basic", OPS + "04", OPS + "07")
def ga_mult_div_small(r):
    if r.random() < 0.5:
        k, m = r.randint(2, 9), r.randint(2, 9)
        if k * m > 40:
            return None
        who = r.choice(NAMES)
        stem = f"{who} puts {m} stickers on each of {k} cards. How many stickers does {who} use?"
        ans = k * m
        wr = [(k + m, "added_instead_of_multiplied", "Added the two numbers."), (k * (m + 1), "one_group_too_many", "Counted one group too many."),
              (k * (m - 1), "one_group_too_few", "Counted one group too few.")]
        p = {"mode": "mult", "k": k, "m": m}
    else:
        k, q = r.randint(2, 5), r.randint(2, 6)
        n = k * q
        if n > 20:
            return None
        who = r.choice(NAMES)
        stem = f"{who} shares {n} sweets equally among {k} friends. How many sweets does each friend get?"
        ans = q
        wr = [(n - k, "subtracted_instead_of_divided", "Subtracted the two numbers."), (k, "gave_the_number_of_friends", "Gave the number of friends."),
              (n + k, "added_instead_of_divided", "Added the two numbers."), (q + 1, "slip", "Slip."), (q - 1, "slip", "Slip.")]
        p = {"mode": "div", "k": k, "n": n}
    return build(ga_mult_div_small, stem, ans, wr, [f"{ans}"], p, whole=True, auto_slips=False)


@checker(ga_mult_div_small)
def _(p):
    if p["mode"] == "mult":
        return F(sum([p["m"]] * p["k"]))
    return next(F(q) for q in range(1, 30) if q * p["k"] == p["n"])


@template(T, "intermediate", OPS + "04", OPS + "19")
def ga_groups_then_change(r):
    who = r.choice(NAMES)
    if r.random() < 0.5:
        k, m = r.randint(3, 8), r.randint(3, 8)
        if k * m > 40:
            return None
        e = r.randint(3, min(12, k * m - 5))
        ans = k * m - e
        stem = f"{who} packs {k} bags with {m} muffins in each bag. {who} then gives away {e} muffins. How many muffins are left?"
        return build(ga_groups_then_change, stem, ans, [
            (k + m - e if k + m - e > 0 else k * m + e, "added_instead_of_multiplied", "Added the number of bags and the muffins in a bag."),
            (k * m + e, "added_the_muffins_given_away", "Added the muffins given away."), (k * (m - 1) if m > 1 else k, "used_the_wrong_amount", "Subtracted one from each bag."),
            *slip_set(ans, 1)], [f"{k} × {m} = {k * m}", f"{k * m} − {e} = {ans}"], {"mode": "mult", "k": k, "m": m, "e": e}, whole=True, auto_slips=False)
    k, q = r.randint(3, 5), r.randint(4, 9)
    n = k * q
    g = r.randint(1, q - 2)
    ans = q - g
    stem = f"{who} shares {n} stickers equally among {k} children. Each child then gives away {g} stickers. How many stickers does each child have now?"
    return build(ga_groups_then_change, stem, ans, [
        (q, "forgot_the_stickers_given_away", "Forgot the stickers given away."), (n - g, "subtracted_before_dividing", "Took the stickers away before sharing."),
        (n // k - g * k if n // k - g * k > 0 else q + g, "used_the_wrong_amount", "Took away the stickers of all the children."), *slip_set(ans, 1)],
        [f"{n} ÷ {k} = {q}", f"{q} − {g} = {ans}"], {"mode": "div", "n": n, "k": k, "g": g}, whole=True, auto_slips=False)


@checker(ga_groups_then_change)
def _(p):
    if p["mode"] == "mult":
        return F(sum([p["m"]] * p["k"]) - p["e"])
    each = next(q for q in range(1, 100) if q * p["k"] == p["n"])
    return F(each - p["g"])


@template(T, "competent", OPS + "04", OPS + "19")
def ga_groups_markers(r):
    g = r.randint(3, 5)
    q = r.randint(4, 8)
    n = g * q
    p_ = r.randint(2, 4)
    x = r.randint(3, 9)
    total = q * p_
    ans = total - x
    if ans < 3:
        return None
    who = r.choice(["Mrs Tan", "Mr Lim", "Miss Chua", "Mr Raj", "Madam Aisha"])
    stem = (f"A class of {n} children is put into groups of {g}. Each group is given {p_} markers. "
            f"The teacher, {who}, finds that {x} of the markers are dried up. How many working markers are there?")
    return build(ga_groups_markers, stem, ans, [
        (n * p_ - x, "gave_markers_to_each_child", "Gave markers to every child instead of every group."),
        (q + p_ - x if q + p_ - x > 0 else total + x, "added_instead_of_multiplied", "Added the number of groups and the markers."),
        (total + x, "added_the_dried_up_markers", "Added the markers that dried up."), *slip_set(ans, 1)],
        [f"{n} ÷ {g} = {q} groups", f"{q} × {p_} = {total} markers", f"{total} − {x} = {ans}"], {"n": n, "g": g, "p": p_, "x": x}, whole=True, auto_slips=False)


@checker(ga_groups_markers)
def _(p):
    groups = len([i for i in range(0, p["n"], p["g"])])
    return F(sum([p["p"]] * groups) - p["x"])


# ---------------------------------------------------------------- OPS-07 / OPS-08: tables of 2, 3, 4, 5 and 10

TBL = [2, 3, 4, 5, 10]


@template(T, "basic", OPS + "07")
def ga_table_direct(r):
    k, m = r.choice(TBL), r.randint(3, 12)
    if k == m:
        return None
    n = k * m
    mode = r.randrange(3)
    if mode == 0:
        stem = f"Work out {m} × {k}."
        ans, wr = n, [(m + k, "added_instead_of_multiplied", "Added the two numbers."), (n + k, "one_group_too_many", "Counted one group too many."),
                      (n - k, "one_group_too_few", "Counted one group too few.")]
    elif mode == 1:
        stem = f"Work out {n} ÷ {k}."
        ans, wr = m, [(n - k, "subtracted_instead_of_divided", "Subtracted the two numbers."), (k, "gave_the_divisor", "Gave the number you divide by."),
                      (m + 1, "slip", "Slip."), (m - 1, "slip", "Slip.")]
    else:
        stem = f"How many {k}s are there in {n}?"
        ans, wr = m, [(n - k, "subtracted_instead_of_divided", "Subtracted the two numbers."), (n + k, "added_instead_of_divided", "Added the numbers."),
                      (m + 1, "slip", "Slip."), (m - 1, "slip", "Slip.")]
    return build(ga_table_direct, stem, ans, wr, [f"{m} × {k} = {n}"], {"k": k, "m": m, "mode": mode}, whole=True, auto_slips=False)


@checker(ga_table_direct)
def _(p):
    k, m = p["k"], p["m"]
    if p["mode"] == 0:
        return F(sum([k] * m))
    return F(len(range(k, k * m + 1, k)))


@template(T, "intermediate", OPS + "07")
def ga_given_product(r):
    a, b = r.choice(TBL), r.randint(3, 9)
    if a == b:
        return None
    c = a * b
    stem = f"Given that {a} × {b} = {c}, find the value of {c} ÷ {a} + {c} ÷ {b}."
    ans = a + b
    return build(ga_given_product, stem, ans, [
        (b, "stopped_after_one_division", f"Worked out only {c} ÷ {a}."), (c, "gave_the_product", "Gave the product."),
        (a * b - a - b if a * b - a - b > 0 else c + 1, "multiplied_instead", "Used multiplication in the second step."),
        (abs(a - b), "subtracted_the_answers", "Subtracted the two quotients."), *slip_set(ans, 1)],
        [f"{c} ÷ {a} = {b}", f"{c} ÷ {b} = {a}", f"{b} + {a} = {ans}"], {"a": a, "b": b}, whole=True, auto_slips=False)


@checker(ga_given_product)
def _(p):
    c = p["a"] * p["b"]
    return F(len(range(p["a"], c + 1, p["a"])) + len(range(p["b"], c + 1, p["b"])))


@template(T, "competent", OPS + "07", OPS + "19")
def ga_table_story(r):
    r1, t1 = r.randint(4, 9), r.choice([3, 4, 5, 10])
    r2, t2 = r.randint(3, 8), r.choice([2, 5, 10])
    t3 = r.choice([2, 3, 4, 5])
    tot = r1 * t1 + r2 * t2
    s = tot % t3 + t3 * r.randint(0, 2)
    rem = tot - s
    if s < 3 or rem < 20 or rem // t3 > 30:
        return None
    ans = rem // t3
    stem = (f"A hall has {r1} rows of {t1} chairs and {r2} rows of {t2} chairs. {s} chairs are taken out. "
            f"The chairs left are arranged in rows of {t3}. How many rows are there?")
    return build(ga_table_story, stem, ans, [
        (tot // t3, "forgot_the_chairs_taken_out", "Forgot to take the chairs out first."),
        (r1 + r2, "counted_the_original_rows", "Gave the number of rows at the start."), *slip_set(ans, 1)],
        [f"{r1} × {t1} + {r2} × {t2} = {tot}", f"{tot} − {s} = {rem}", f"{rem} ÷ {t3} = {ans}"],
        {"r1": r1, "t1": t1, "r2": r2, "t2": t2, "s": s, "t3": t3}, whole=True, auto_slips=False)


@checker(ga_table_story)
def _(p):
    chairs = sum([p["t1"]] * p["r1"]) + sum([p["t2"]] * p["r2"]) - p["s"]
    return next((F(rows) for rows in range(1, 200) if rows * p["t3"] == chairs), None)


@template(T, "basic", OPS + "08")
def ga_missing_factor(r):
    k, m = r.choice(TBL), r.randint(2, 10)
    n = k * m
    form = r.randrange(4)
    eq = [f"x × {k} = {n}", f"{k} × x = {n}", f"x ÷ {k} = {m}", f"{n} ÷ x = {m}"][form]
    ans = [m, m, n, k][form]
    if form == 3 and k == m:
        return None
    shown = eq.replace("x", "__")
    wr = [(n + k if form < 2 else m + k, "used_the_wrong_operation", "Used the wrong operation."),
          (abs(n - k) if form < 2 else abs(m - k), "used_the_wrong_operation", "Subtracted instead."),
          (n * k if form == 3 else (m * k if form < 2 else m + k + 1), "used_the_wrong_operation", "Used the wrong operation.")]
    return build(ga_missing_factor, f"Find the missing number: {shown}", ans, wr + slip_set(ans, 1),
                 [f"Use the multiplication fact {m} × {k} = {n}."], {"eq": eq}, whole=True, auto_slips=False)


@checker(ga_missing_factor)
def _(p):
    lhs, rhs = p["eq"].split("=")
    for x in range(1, 200):
        v = _ev(lhs.replace("x", f"({x})"))
        if v == int(rhs):
            return F(x)


@template(T, "intermediate", OPS + "08")
def ga_groups_leftover(r):
    g = r.choice(TBL)
    q = r.randint(3, 9)
    rem = r.randint(1, g - 1) if g > 2 else 1
    n = g * q + rem
    who = r.choice(NAMES)
    mode = r.randrange(3)
    base = f"{who} packs {n} oranges into bags. Each bag holds {g} oranges"
    if mode == 0:
        stem, ans = base + ". How many bags are filled completely?", q
        wr = [(q + 1, "counted_the_partly_filled_bag", "Counted the bag that is not full."), (rem, "gave_the_leftover", "Gave the oranges left over."),
              (n - g, "subtracted_instead_of_divided", "Subtracted instead of dividing.")]
    elif mode == 1:
        stem, ans = base + ", as full as possible. How many oranges are left over?", rem
        wr = [(q, "gave_the_number_of_bags", "Gave the number of full bags."), (g - rem if g - rem != rem else rem + 1, "counted_the_empty_spaces", "Gave how many more are needed to fill another bag."),
              (n - g, "subtracted_instead_of_divided", "Subtracted instead of dividing.")]
    else:
        stem, ans = base + ". How many bags are needed to hold all the oranges?", q + 1
        wr = [(q, "ignored_the_leftover", "Ignored the oranges left over."), (q + 2, "counted_one_bag_too_many", "Counted an extra bag."),
              (rem, "gave_the_leftover", "Gave the oranges left over.")]
    return build(ga_groups_leftover, stem, ans, wr + slip_set(ans, 1), [f"{n} ÷ {g} = {q} remainder {rem}"],
                 {"n": n, "g": g, "mode": mode}, whole=True, auto_slips=False)


@checker(ga_groups_leftover)
def _(p):
    n, g, left = p["n"], p["g"], p["n"]
    bags = 0
    while left >= g:
        left -= g
        bags += 1
    return F([bags, left, bags + (1 if left else 0)][p["mode"]])


@template(T, "competent", OPS + "08", OPS + "19")
def ga_tickets_change(r):
    price, n = r.choice(TBL), r.randint(5, 12)
    paid = 50 if price * n <= 50 else 100
    change = paid - price * n
    if change < 1 or (price == 10 and n > 9):
        return None
    who = r.choice(NAMES)
    stem = f"{who} buys some tickets at ${price} each. {who} pays ${paid} and gets ${change} change. How many tickets did {who} buy?"
    return build(ga_tickets_change, stem, n, [
        (paid - change, "gave_the_money_spent", "Gave the money spent instead of the number of tickets."),
        (paid // price, "ignored_the_change", "Divided the money paid by the price."),
        (n + 1, "slip", "Slip."), (n - 1, "slip", "Slip."),
        (change // price if change // price else n + 2, "divided_the_change", "Divided the change by the price.")],
        [f"Money spent: {paid} − {change} = {paid - change}", f"{paid - change} ÷ {price} = {n}"], {"price": price, "paid": paid, "change": change}, whole=True, auto_slips=False)


@checker(ga_tickets_change)
def _(p):
    return next((F(n) for n in range(1, 100) if n * p["price"] + p["change"] == p["paid"]), None)


# ---------------------------------------------------------------- OPS-11 / OPS-14: tables of 6, 7, 8 and 9

@template(T, "basic", OPS + "11")
def ga_table_high(r):
    k, m = r.randint(6, 9), r.randint(3, 12)
    n = k * m
    mode = r.randrange(3)
    if mode == 0:
        stem, ans = f"Work out {k} × {m}.", n
        wr = [(k + m, "added_instead_of_multiplied", "Added the two numbers."), (n + k, "one_group_too_many", "Counted one group too many."),
              (n - k, "one_group_too_few", "Counted one group too few.")]
    elif mode == 1:
        stem, ans = f"Work out {n} ÷ {k}.", m
        wr = [(m + 1, "slip_in_the_table", "Slipped in the times table."), (m - 1, "slip_in_the_table", "Slipped in the times table."),
              (n - k, "subtracted_instead_of_divided", "Subtracted the two numbers."), (k, "gave_the_divisor", "Gave the number you divide by.")]
    else:
        stem, ans = f"Find the missing number: __ × {k} = {n}", m
        wr = [(n - k, "subtracted_instead_of_divided", "Subtracted instead."), (n + k, "added_instead", "Added instead."),
              (m + 1, "slip_in_the_table", "Slipped in the times table."), (m - 1, "slip_in_the_table", "Slipped in the times table.")]
    return build(ga_table_high, stem, ans, wr, [f"{m} × {k} = {n}"], {"k": k, "m": m, "mode": mode}, whole=True, auto_slips=False)


@checker(ga_table_high)
def _(p):
    k, m = p["k"], p["m"]
    return F(sum([k] * m)) if p["mode"] == 0 else F(len(range(k, k * m + 1, k)))


@template(T, "intermediate", OPS + "11", OPS + "07")
def ga_two_pack_sizes(r):
    a, s1 = r.randint(4, 9), r.choice([6, 7, 8, 9])
    b, s2 = r.randint(3, 8), r.choice([6, 7, 8, 9])
    if s1 == s2 or a == b:
        return None
    tot = a * s1 + b * s2
    who = r.choice(NAMES)
    stem = f"{who} buys {a} packs of {plural(s1, 'pen')} and {b} packs of {plural(s2, 'pen')}. How many pens does {who} buy altogether?"
    return build(ga_two_pack_sizes, stem, tot, [
        (a * s2 + b * s1, "swapped_the_pack_sizes", "Matched the numbers of packs with the wrong pack sizes."),
        (a * s1, "left_out_the_second_kind", "Left out the second kind of pack."),
        (a * b + s1 * s2, "multiplied_the_wrong_pairs", "Multiplied the packs together and the pack sizes together."),
        *slip_set(tot, s1)],
        [f"{a} × {s1} = {a * s1}", f"{b} × {s2} = {b * s2}", f"{a * s1} + {b * s2} = {tot}"],
        {"a": a, "s1": s1, "b": b, "s2": s2}, whole=True, auto_slips=False)


@checker(ga_two_pack_sizes)
def _(p):
    return F(sum([p["s1"]] * p["a"]) + sum([p["s2"]] * p["b"]))


@template(T, "competent", OPS + "11", OPS + "19")
def ga_pens_at_first(r):
    a, s1 = r.randint(5, 9), r.randint(6, 9)
    b, s2 = r.randint(4, 8), r.randint(6, 9)
    left = r.randint(15, 45)
    sold = a * s1 + b * s2
    start = sold + left
    who = r.choice(NAMES)
    item = r.choice(["pens", "erasers", "rulers"])
    stem = (f"A shop sold {a} boxes of {s1} {item} in the morning and {b} boxes of {s2} {item} in the afternoon. "
            f"At closing, {left} {item} were left. How many {item} did {who}'s shop have at first?")
    return build(ga_pens_at_first, stem, start, [
        (sold - left, "subtracted_the_leftover", "Subtracted the ones left instead of adding."),
        (sold, "forgot_the_leftover", "Forgot the ones left."),
        (a + b + left, "added_the_number_of_boxes", "Added the number of boxes instead of the items in them."),
        *slip_set(start, 10)],
        [f"Sold: {a} × {s1} + {b} × {s2} = {sold}", f"At first: {sold} + {left} = {start}"],
        {"a": a, "s1": s1, "b": b, "s2": s2, "left": left}, whole=True, auto_slips=False)


@checker(ga_pens_at_first)
def _(p):
    items = [p["s1"]] * p["a"] + [p["s2"]] * p["b"]
    return F(sum(items) + p["left"])


@template(T, "basic", OPS + "14")
def ga_mental_tables(r):
    k, m = r.randint(2, 9), r.randint(2, 9)
    c = r.randint(3, 15)
    n = k * m
    kind = r.randrange(3)
    if kind == 0:
        e, ans = f"{k} × {m} + {c}", n + c
        wr = [(k * (m + c), "ignored_the_order_of_operations", "Added before multiplying."), (n - c if n > c else n + 2 * c, "used_the_wrong_sign", "Subtracted instead of adding.")]
    elif kind == 1:
        if n <= c + 3:
            return None
        e, ans = f"{k} × {m} − {c}", n - c
        wr = [(k * (m - c) if m > c else n + c, "ignored_the_order_of_operations", "Subtracted before multiplying."), (n + c, "used_the_wrong_sign", "Added instead of subtracting.")]
    else:
        e, ans = f"{c} + {k} × {m}", n + c
        wr = [((c + k) * m, "worked_left_to_right", "Added first and then multiplied."), (c * k + m, "ignored_the_order_of_operations", "Multiplied the wrong numbers.")]
    stem = f"Find the value of {e}."
    return build(ga_mental_tables, stem, ans, wr + slip_set(ans, k), [f"Multiply first: {k} × {m} = {n}", f"Then {ans}"], {"e": e}, whole=True, auto_slips=False)


@checker(ga_mental_tables)
def _(p):
    return F(int(_ev(p["e"])))


@template(T, "intermediate", OPS + "14", OPS + "11")
def ga_equal_products(r):
    a, b, c = r.randint(3, 9), r.randint(4, 12), r.choice([2, 3, 4, 6])
    n = a * b
    if n % c or a == c or n // c == b or n // c == a:
        return None
    ans = n // c
    if r.random() < 0.6:
        stem = f"Fill in the missing number: {a} × {b} = {c} × __"
        wr = [(a + b - c, "used_addition_to_balance", "Balanced the two sides by adding and subtracting."), (b, "copied_the_other_factor", "Copied the other factor."),
              (a * b - c, "subtracted_instead", "Subtracted instead of dividing.")]
        p = {"mode": "eq", "a": a, "b": b, "c": c}
    else:
        stem = f"Given that {a} × {b} = {n}, find the value of {a} × {b + 1} without multiplying the numbers out again."
        ans = n + a
        wr = [(n + b, "added_the_wrong_factor", "Added the other factor."), (n + b + 1, "added_the_wrong_factor", "Added the larger number."),
              (n + 1, "added_one", "Added one.")]
        p = {"mode": "next", "a": a, "b": b}
    return build(ga_equal_products, stem, ans, wr + slip_set(ans, 1), [f"{a} × {b} = {n}", f"Answer {ans}"], p, whole=True, auto_slips=False)


@checker(ga_equal_products)
def _(p):
    if p["mode"] == "next":
        return F(sum([p["a"]] * (p["b"] + 1)))
    n = p["a"] * p["b"]
    return next((F(x) for x in range(1, 200) if p["c"] * x == n), None)


@template(T, "competent", OPS + "14", OPS + "11")
def ga_share_then_lose(r):
    d, q = r.randint(6, 9), r.randint(6, 12)
    g = r.randint(2, q - 2)
    k = r.randint(3, 5)
    T_ = d * q
    ans = k * (q - g)
    who = r.choice(NAMES)
    stem = (f"{who} shares {T_} marbles equally among {d} friends. Each friend then loses {g} marbles. "
            f"How many marbles do {k} of the friends have altogether now?")
    return build(ga_share_then_lose, stem, ans, [
        (k * q, "forgot_the_marbles_lost", "Forgot the marbles lost."), (q - g, "found_one_friend_only", "Found the marbles of one friend only."),
        (k * q - g, "subtracted_the_loss_once", "Subtracted the loss only once."), *slip_set(ans, k)],
        [f"{T_} ÷ {d} = {q}", f"{q} − {g} = {q - g}", f"{k} × {q - g} = {ans}"], {"T": T_, "d": d, "g": g, "k": k}, whole=True, auto_slips=False)


@checker(ga_share_then_lose)
def _(p):
    each = next(q for q in range(1, 200) if q * p["d"] == p["T"])
    return F(sum([each - p["g"]] * p["k"]))


@template(T, "intermediate", NUM + "03", OPS + "03")
def ga_words_add_tens(r):
    n = r.randint(11, 78)
    if n % 10 == 0:
        return None
    k = r.randint(1, 20) * 1
    k = k - k % 10 if k >= 10 else 10
    sub = r.random() < 0.4
    ans = n - k if sub else n + k
    if ans < 10 or ans > 99 or ans % 10 == 0:
        return None
    who = r.choice(NAMES)
    stem = (f"{who} reads the number '{words(n)}', then {'takes away' if sub else 'adds'} '{words(k)}'. "
            f"Which of these is the answer written in words?")
    swapped = int(str(ans)[::-1])
    return build(ga_words_add_tens, stem, ans, [
        (swapped if swapped != ans else ans + 1, "swapped_the_digits", "Wrote the tens and ones the wrong way round."),
        (n + k if sub else n - k if n - k > 0 else ans + 10, "used_the_wrong_operation", "Used the wrong operation."),
        (ans + 1, "slip_in_ones", "Changed the ones digit by mistake."), (ans - 1, "slip_in_ones", "Changed the ones digit by mistake.")],
        [f"{n} {'−' if sub else '+'} {k} = {ans}", words(ans)], {"nw": words(n), "kw": words(k), "sub": sub},
        show=lambda v: words(int(v)) if v > 0 else "0", whole=True, auto_slips=False)


@checker(ga_words_add_tens)
def _(p):
    a, b = _unwords(p["nw"]), _unwords(p["kw"])
    return F(a - b if p["sub"] else a + b)
