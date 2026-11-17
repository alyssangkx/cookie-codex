"""Whole numbers (math-whole-numbers): basic, intermediate and competent generators."""
from itertools import permutations
from decimal import Decimal, ROUND_HALF_UP
from common import *
from figures_A import growing_rows_fig, overlap_cards_fig, number_grid_fig

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


@template(T, "intermediate", OPS + "12", OPS + "16")
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


@template(T, "intermediate", OPS + "16", OPS + "15")
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


@template(T, "competent", OPS + "15", OPS + "19")
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
        stem = f"A shop sells {A} and {B}. There are {Nn} altogether, with {L} {what}. How many {A} are there?"
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


@template(T, "competent", OPS + "15", OPS + "19")
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
        [f"Factors of {a}: {', '.join(map(str, factors(a)))}", f"Factors of {b}: {', '.join(map(str, factors(b)))}",
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
        [f"Multiples of {a}: {', '.join(str(a * i) for i in range(1, 8))}", f"Multiples of {b}: {', '.join(str(b * i) for i in range(1, 8))}", f"Smallest common: {L}"],
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
        [f"Factors of {A}: {', '.join(map(str, factors(A)))}", f"Factors of {B}: {', '.join(map(str, factors(B)))}", f"Greatest common: {g}"],
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
    stem = (f"Bus A leaves a stop every {a} minutes and Bus B leaves every {b} minutes. They both leave together at {h}:{m:02d} a.m. "
            f"After how many minutes will they next leave together?")
    return build(lcm_word, stem, L, [
        (a * b, "multiplied_the_numbers", "Multiplied the two times."),
        (gcd(a, b), "used_hcf", "Used the highest common factor."),
        (a + b, "added_times", "Added the two times."),
        (L + min(a, b), "slip", "Slip."), (L - min(a, b), "slip", "Slip.")],
        [f"LCM of {a} and {b} is {L}."], {"a": a, "b": b}, whole=True, show=lambda x: f"{int(x)} minutes")


@checker(lcm_word)
def _(p):
    return F(brute(lambda n: n % p["a"] == 0 and n % p["b"] == 0, 1, 2000))


@template(T, "intermediate", FM + "05", FM + "04")
def multiples_below_limit(r):
    """math-pat-multiples-factors-direct"""
    mode = r.choice(["largest_below", "smallest_above", "common_below"])
    if mode == "common_below":
        a, b = r.sample([4, 6, 8, 9, 10, 12], 2)
        L = lcm(a, b)
        lim = r.randint(L * 3 + 1, L * 12)
        ans = (lim - 1) // L * L if True else None
        stem = f"What is the greatest common multiple of {a} and {b} that is smaller than {lim}?"
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
            f"How many times will they flash together in the next {mins} minutes, not counting the one at 8:00 p.m.?")
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
        wrong = [(int(str(q).replace("0", "", 1)) if "0" in str(q) else None, "dropped_zero_in_quotient", "Left out a zero in the quotient."),
                 (q + 10, "careless_slip", "Slip in the tens."), (q - 10, "careless_slip", "Slip in the tens."),
                 (q * 10 if q * 10 < a else None, "misplaced_digit", "Put the quotient digits one place too high."),
                 (q + 1, "careless_slip", "Slip in the ones.")]
        prm = {"a": a, "b": b, "mul": False}
    return build(big_four_ops, stem, ans, wrong, [stem[14:-1] + f" = {num(ans)}"], prm, num, whole=True)


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
        (other if other != ans else None, "ignored_the_condition", f"Formed the {'greatest' if big else 'smallest'} number but it is not a {cond} number."),
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
        [f"The age gap stays {d} years.", f"In {n} years: son = 1 unit, {a} = {k} units, so {k - 1} units = {d}", f"1 unit = {F(d, k - 1)}, so the son will be {s + n}; now he is {s + n} − {n} = {s}"],
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
