"""Money (math-money): basic, intermediate and competent generators."""
from decimal import Decimal
from common import *

T = "math-money"
M = "math-money-money-"


def H(c):
    """Cents (int) to an exact dollar value."""
    return F(c, 100)


def dp(c):
    return f"${c // 100}.{c % 100:02d}"


def digitwise(a, b, op):
    L = max(len(str(a)), len(str(b)))
    sa, sb = str(a).zfill(L), str(b).zfill(L)
    if op == "+":
        return int("".join(str((int(x) + int(y)) % 10) for x, y in zip(sa, sb)))
    return int("".join(str(abs(int(x) - int(y))) for x, y in zip(sa, sb)))


# ================================================================ basic

@template(T, "basic", M + "02", M + "01")
def count_money(r):
    x = r.choice(NAMES)
    n5, n2, n50, n20, n10 = r.randint(1, 4), r.randint(1, 5), r.randint(1, 6), r.randint(2, 7), r.randint(1, 6)
    total = n5 * 500 + n2 * 200 + n50 * 50 + n20 * 20 + n10 * 10
    stem = (f"{x} has {n5} $5 note{'s' if n5 > 1 else ''}, {n2} $2 note{'s' if n2 > 1 else ''}, {n50} 50-cent coin{'s' if n50 > 1 else ''}, "
            f"{n20} 20-cent coins and {n10} 10-cent coin{'s' if n10 > 1 else ''}. How much money does {x} have altogether?")
    return build(count_money, stem, H(total), [
        (H(total - n20 * 20), "forgot_one_kind_of_coin", "Left out the 20-cent coins."),
        (H(total - n10 * 10 + n10 * 100), "counted_10_cent_coins_as_dollars", "Counted each 10-cent coin as $1."),
        (H(total - n50 * 50 + n50 * 5), "mixed_up_coin_values", "Counted each 50-cent coin as 5 cents."),
        (H(total + 10), "slip", "Slip in adding the cents."), (H(total - 100), "slip", "Slip in adding the dollars.")],
        [f"Notes: {n5} × $5 + {n2} × $2 = ${n5 * 5 + n2 * 2}", f"Coins: {n50 * 50 + n20 * 20 + n10 * 10} cents", f"Total = {dp(total)}"],
        {"n": [n5, n2, n50, n20, n10]}, money, auto_slips=False)


@checker(count_money)
def _(p):
    vals = [500, 200, 50, 20, 10]
    cents = 0
    for v, k in zip(vals, p["n"]):
        for _ in range(k):
            cents += v
    return F(cents, 100)


@template(T, "basic", M + "05")
def dollars_cents_convert(r):
    to_cents = r.random() < 0.5
    c = r.randint(105, 9999)
    if c % 100 == 0 or c % 10 == 0 and r.random() < .5:
        return None
    if to_cents:
        stem = f"Express {dp(c)} in cents."
        return build(dollars_cents_convert, stem, c, [
            (c // 10, "used_10_cents_in_a_dollar", "Used 1 dollar = 10 cents."), (c * 10, "used_1000_cents_in_a_dollar", "Used 1 dollar = 1 000 cents."),
            (c // 100 * 10 + c % 100 // 10 if False else (c // 100) * 100 + (c % 100) * 10, "wrong_place_for_cents", "Put the cents in the wrong place."),
            (c + 100, "slip", "Slip."), (c - 100, "slip", "Slip.")],
            ["1 dollar = 100 cents", f"{dp(c)} = {c} cents"], {"c": c, "to_cents": True}, lambda v: f"{int(v)} cents", whole=True, auto_slips=False)
    stem = f"Express {c} cents in dollars."
    return build(dollars_cents_convert, stem, H(c), [
        (H(c) * 10, "used_10_cents_in_a_dollar", "Divided by 10 instead of 100."), (H(c) / 10, "used_1000_cents_in_a_dollar", "Divided by 1 000."),
        (H(c) + F(9, 100) if False else H((c // 100) * 100 + (c % 100) // 10 + (c % 10) * 10), "swapped_cents_digits", "Swapped the digits in the cents."),
        (H(c) + 1, "slip", "Slip."), (H(c) - 1 if H(c) > 1 else None, "slip", "Slip.")],
        ["100 cents = 1 dollar", f"{c} ÷ 100 = {dp(c)}"], {"c": c, "to_cents": False}, money, auto_slips=False)


@checker(dollars_cents_convert)
def _(p):
    return F(p["c"]) if p["to_cents"] else F(str(Decimal(p["c"]) / 100))


@template(T, "basic", M + "03")
def write_money_decimal(r):
    d = r.randint(1, 99)
    c = r.choice([r.randint(1, 9), r.randint(10, 99)])
    ans = d * 100 + c
    stem = f"Write {d} dollars and {c} cent{'s' if c > 1 else ''} in decimal notation."
    swapped = (c % 10) * 10 + c // 10 if c >= 10 else c * 10
    return build(write_money_decimal, stem, H(ans), [
        (H(d * 100 + swapped) if c < 10 else H(d * 100 + swapped), "misplaced_the_cents" if c < 10 else "swapped_cents_digits",
         "Wrote the cents as tenths of a dollar." if c < 10 else "Swapped the digits of the cents."),
        (d * 100 + c, "joined_dollars_and_cents", "Joined the dollars and cents as one whole number."),
        (H(c * 100 + d) if c < 100 else None, "swapped_dollars_and_cents", "Swapped the dollars and the cents."),
        (F(d, 10) + F(c, 100), "dollars_in_wrong_place", "Put the dollars in the tenths place."),
        (H(ans + 100), "slip", "Slip.")],
        [f"{d} dollars = ${d}", f"{c} cents = ${c / 100:.2f}", f"Total = {dp(ans)}"], {"d": d, "c": c}, money, auto_slips=False)


@checker(write_money_decimal)
def _(p):
    return F(str(Decimal(p["d"]) + Decimal(p["c"]) / 100))


@template(T, "basic", M + "04")
def greatest_amount(r):
    ds = r.sample(range(1, 10), 3)
    a, b, c = ds
    cands = {a * 100 + b * 10 + c, a * 100 + c * 10 + b, b * 100 + a * 10 + c, c * 100 + b * 10 + a, (a * 10 + b) * 10 + c, (b * 10 + c) * 10 + a}
    cands = sorted(cands)
    big = r.random() < 0.5
    opts = r.sample(cands, 4)
    ans = max(opts) if big else min(opts)
    stem = (f"The digits {a}, {b} and {c} are each used once to make amounts of money, such as $x.yz. "
            f"The amounts are {', '.join(dp(v) for v in sorted(opts))}. Which is the {'greatest' if big else 'smallest'} amount?")
    return build(greatest_amount, stem, H(ans), [(H(v), "compared_the_cents_not_the_dollars", "Looked at the cents digits before the dollars.")
                                                for v in sorted(opts, key=lambda v: (v % 100) * (-1 if big else 1)) if v != ans],
                 ["Compare the dollars first, then the cents.", f"Answer: {dp(ans)}"], {"opts": opts, "big": big}, money, auto_slips=False)


@checker(greatest_amount)
def _(p):
    return H(max(p["opts"]) if p["big"] else min(p["opts"]))


@template(T, "basic", M + "06")
def add_two_amounts(r):
    x = r.choice(NAMES)
    a, b = r.randint(150, 1999), r.randint(150, 1999)
    if (a % 100) + (b % 100) < 100:
        return None
    ans = a + b
    i1, i2 = r.sample(["a book", "a pen", "a ruler", "a bag of fruit", "a drink", "a notebook"], 2)
    stem = f"{x} spent {dp(a)} on {i1} and {dp(b)} on {i2}. How much did {x} spend altogether?"
    nocarry = (a // 100 + b // 100) * 100 + (a % 100 + b % 100) % 100
    return build(add_two_amounts, stem, H(ans), [
        (H(nocarry), "forgot_to_carry_the_cents", "Forgot to carry 1 dollar from the cents."),
        (H(digitwise(a, b, "+")), "added_columns_without_carrying", "Added each column without carrying."),
        (H(ans + 10), "slip", "Slip in the cents."), (H(ans - 100), "slip", "Slip in the dollars."), (H(ans + 100), "slip", "Slip in the dollars.")],
        [f"{dp(a)} + {dp(b)} = {dp(ans)}"], {"a": a, "b": b}, money, auto_slips=False)


@checker(add_two_amounts)
def _(p):
    return F(str(Decimal(p["a"]) / 100 + Decimal(p["b"]) / 100))


@template(T, "basic", M + "06")
def change_from_note(r):
    x = r.choice(NAMES)
    note = r.choice([5, 10, 20, 50])
    a = r.randint(105, note * 100 - 120)
    if a % 100 == 0 or a % 100 > 90:
        return None
    ans = note * 100 - a
    item = r.choice(["a toy", "a pencil case", "a T-shirt", "a puzzle", "some fruit"])
    stem = f"{x} paid for {item} that cost {dp(a)} with a ${note} note. How much change should {x} get?"
    return build(change_from_note, stem, H(ans), [
        (H(digitwise(note * 100, a, "−")), "subtracted_smaller_digit_from_larger", "Took the smaller digit from the larger in each column."),
        (H(ans + 100), "borrow_not_reduced", "Forgot to reduce the dollars after borrowing."),
        (H(a + note * 100 if False else (note - a // 100) * 100 - (a % 100)) if (note - a // 100) * 100 - (a % 100) > 0 and (note - a // 100) * 100 - (a % 100) != ans else None,
         "forgot_cents_borrow", "Subtracted the dollars and the cents separately and ignored the borrow."),
        (H(ans - 10), "slip", "Slip in the cents."), (H(ans + 10), "slip", "Slip in the cents.")],
        [f"${note}.00 − {dp(a)} = {dp(ans)}"], {"note": note, "a": a}, money, auto_slips=False)


@checker(change_from_note)
def _(p):
    paid = F(p["note"])
    return paid - F(p["a"], 100)


# ================================================================ intermediate

CONTEXTS = [
    ("car park", "parked for", 60, 30, "The car park charges {f} for the first hour and {p} for every additional half hour or part of it. "),
    ("taxi", "travelled", 1000, 400, "A taxi ride costs {f} for the first 1 km and {p} for every additional 400 m or part of it. "),
    ("parcel", "weighs", 100, 50, "Posting a parcel costs {f} for the first 100 g and {p} for every additional 50 g or part of it. "),
]


@template(T, "intermediate", M + "06", M + "03")
def tariff_charge(r):
    """math-pat-tariff-charge"""
    kind = r.randint(0, 2)
    name, _, first, block, text = CONTEXTS[kind]
    f_ = r.randint(180, 450)
    p_ = r.randint(30, 95)
    n_blocks = r.randint(2, 7)
    extra = n_blocks * block - r.randint(1, block - 1)
    if kind == 0:
        extra = n_blocks * 30 - r.choice([5, 10, 20])
    total = first + extra
    ans = f_ + n_blocks * p_
    who = r.choice(NAMES)
    if kind == 0:
        tm = f"{total // 60} h {total % 60} min"
        tail = f"{who} parked for {tm}. How much did {who} pay?"
    elif kind == 1:
        tail = f"{who}'s ride was {total / 1000:.1f} km." if total % 100 == 0 else f"{who}'s ride was {total} m."
        tail += f" How much did {who} pay for the ride?"
    else:
        tail = f"{who}'s parcel has a mass of {total} g. How much does {who} pay to post it?"
    stem = text.format(f=dp(f_), p=dp(p_)) + tail
    fl = extra // block
    return build(tariff_charge, stem, H(ans), [
        (H(f_ + fl * p_), "ignored_the_part_block", "Did not charge for the last part of a block."),
        (H(f_ + (n_blocks + 1) * p_), "charged_one_block_too_many", "Counted the first block as an extra block as well."),
        (H(ceil_div(total, block) * p_), "charged_every_block_from_the_start", "Charged the extra rate from the start."),
        (H(ans + 10), "slip", "Slip."), (H(ans - p_ + 10 if ans - p_ + 10 != ans else ans + 20), "slip", "Slip.")],
        [f"After the first {first}: {extra} remains.", f"{extra} ÷ {block} = {fl} remainder {extra % block}, so {n_blocks} extra blocks.",
         f"Total = {dp(f_)} + {n_blocks} × {dp(p_)} = {dp(ans)}"],
        {"f": f_, "p": p_, "first": first, "block": block, "total": total}, money, auto_slips=False)


def ceil_div(a, b):
    return -(-a // b)


@checker(tariff_charge)
def _(p):
    charge, covered = p["f"], p["first"]
    while covered < p["total"]:
        charge += p["p"]
        covered += p["block"]
    return F(charge, 100)


@template(T, "intermediate", M + "06", M + "02")
def buy_n_get_free(r):
    """math-pat-promo-buy-n-get-free"""
    n = r.randint(3, 6)
    price = r.randint(60, 250)
    N = r.randint(15, 60)
    free = N // (n + 1)
    pay = N - free
    ans = pay * price
    item = r.choice(["buns", "muffins", "apples", "pencils", "stickers"])
    nm = r.choice(NAMES)
    stem = (f"{item.capitalize()} cost {dp(price)} each. For every {n} {item} bought, 1 more is free. "
            f"What is the least amount {nm} must pay to get {N} {item}?")
    return build(buy_n_get_free, stem, H(ans), [
        (H(N * price), "no_promotion_used", "Paid for every one and ignored the free ones."),
        (H(round(N * price * n / (n + 1))), "averaged_the_discount", f"Treated every {item[:-1]} as costing {n}/{n + 1} of the price."),
        (H(ceil_div(N, n + 1) * n * price), "bought_extra_to_complete_the_set", "Bought full sets, which gives more than needed and costs more."),
        (H(ans + price), "slip", "Paid for one extra."), (H(ans - price), "slip", "Paid for one too few.")],
        [f"Each set of {n + 1} costs {n} {item}.", f"{N} ÷ {n + 1} = {free} remainder {N % (n + 1)}, so {free} are free.",
         f"Pay for {N} − {free} = {pay}: {pay} × {dp(price)} = {dp(ans)}"], {"n": n, "price": price, "N": N}, money, auto_slips=False)


@checker(buy_n_get_free)
def _(p):
    b = 0
    while b + b // p["n"] < p["N"]:
        b += 1
    return F(b * p["price"], 100)


@template(T, "intermediate", M + "06", M + "02")
def change_after_items(r):
    x = r.choice(NAMES)
    k = r.randint(2, 6)
    a = r.randint(125, 480)
    b = r.randint(110, 650)
    note = r.choice([20, 50, 100])
    spent = k * a + b
    if spent > note * 100 - 50:
        return None
    ans = note * 100 - spent
    i1, i2 = r.choice([("notebooks", "a pen"), ("rulers", "a bag"), ("packets of sweets", "a drink"), ("erasers", "a ruler")])
    stem = f"{x} bought {k} {i1} at {dp(a)} each and {i2} for {dp(b)}. {x} paid with a ${note} note. How much change did {x} receive?"
    return build(change_after_items, stem, H(ans), [
        (H(note * 100 - a - b), "forgot_to_multiply_by_number_of_items", f"Used the price of only one of the {i1}."),
        (H(spent), "gave_the_total_spent", "Gave the amount spent, not the change."),
        (H(note * 100 - k * a), "forgot_the_second_item", f"Forgot {i2}."),
        (H(ans + 10), "slip", "Slip."), (H(ans - 100), "slip", "Slip.")],
        [f"{k} × {dp(a)} = {dp(k * a)}", f"Total = {dp(k * a)} + {dp(b)} = {dp(spent)}", f"Change = ${note} − {dp(spent)} = {dp(ans)}"],
        {"k": k, "a": a, "b": b, "note": note}, money, auto_slips=False)


@checker(change_after_items)
def _(p):
    paid = F(p["note"])
    for _ in range(p["k"]):
        paid -= F(p["a"], 100)
    return paid - F(p["b"], 100)


@template(T, "intermediate", M + "04", M + "05")
def most_minus_least(r):
    x, y, z = r.sample(NAMES, 3)
    cs = r.sample(range(305, 780), 3)
    a, b, c = cs
    ans = max(cs) - min(cs)
    mid = sorted(cs)[1]
    stem = f"{x} has {dp(a)}, {y} has {b} cents and {z} has {dp(c)}. How much more money does the person with the most have than the person with the least?"
    return build(most_minus_least, stem, H(ans), [
        (H(max(cs) - mid), "used_wrong_pair", "Compared the most with the middle amount."),
        (H(mid - min(cs)), "used_wrong_pair", "Compared the middle with the least amount."),
        (H(ans + 10), "slip", "Slip."), (H(ans + 100), "slip", "Slip."), (H(abs(ans - 100)) if ans != 100 else None, "slip", "Slip.")],
        [f"Write all in dollars: {dp(a)}, {dp(b)}, {dp(c)}", f"Most − least = {dp(max(cs))} − {dp(min(cs))} = {dp(ans)}"],
        {"cs": cs}, money, auto_slips=False)


@checker(most_minus_least)
def _(p):
    v = [F(c, 100) for c in p["cs"]]
    return max(v) - min(v)


@template(T, "intermediate", M + "06", M + "02")
def weekly_saving_cycle(r):
    """math-pat-weekly-saving-cycle"""
    x = r.choice(NAMES)
    g = r.randint(4, 8)
    s = r.randint(250, g * 100 - 60)
    net = [g * 100 - s] * 5 + [g * 100] * 2
    wk = sum(net)
    X = r.randint(40, 300) * 100 + r.choice([0, 50])
    W = (X - 1) // wk
    rem = X - W * wk
    cum, d = 0, 0
    for v in net:
        d += 1
        cum += v
        if cum >= rem:
            break
    ans = 7 * W + d
    stem = (f"{x} gets ${g} pocket money every day. From Monday to Friday {x} spends {dp(s)} each day. On Saturday and Sunday {x} spends nothing. "
            f"{x} starts saving on a Monday. After how many days will {x} first have at least {dp(X)}?")
    return build(weekly_saving_cycle, stem, ans, [
        (ceil_div(X * 7, wk), "averaged_per_day", "Used the average savings per day."),
        ((W + 1) * 7, "whole_weeks_only", "Counted whole weeks only."),
        (ans - 1, "slip", "Did not count the last day."), (ans + 1, "slip", "Counted one extra day."),
        (7 * W + 5 if d != 5 else 7 * W + 7, "stopped_after_weekdays", "Stopped at the end of a school week.")],
        [f"Saved in one week: 5 × {dp(g * 100 - s)} + 2 × ${g} = {dp(wk)}", f"After {W} weeks: {dp(W * wk)}; still need {dp(rem)}", f"Days = {7 * W} + {d} = {ans}"],
        {"g": g, "s": s, "X": X}, whole=True, show=str, auto_slips=False)


@checker(weekly_saving_cycle)
def _(p):
    saved, day = 0, 0
    while saved < p["X"]:
        spend = p["s"] if day % 7 < 5 else 0
        saved += p["g"] * 100 - spend
        day += 1
    return F(day)


# ================================================================ competent

@template(T, "competent", M + "06", M + "02")
def weeks_to_save(r):
    x = r.choice(NAMES)
    P = r.randint(60, 480)
    sv = r.randint(10, P // 3)
    d = r.randint(6, 25)
    if (P - sv) % d == 0:
        return None
    ans = ceil_div(P - sv, d)
    item = r.choice(["a bicycle", "a tablet", "a pair of shoes", "a camera"])
    stem = f"{item.capitalize()} costs ${P}. {x} has saved ${sv} and saves another ${d} every week. After how many weeks will {x} first have enough money to buy it?"
    return build(weeks_to_save, stem, ans, [
        ((P - sv) // d, "ignored_the_remainder", "Rounded down, so the money is not quite enough."),
        (ceil_div(P, d), "forgot_the_savings_so_far", "Ignored the money already saved."),
        (ans + 1, "slip", "One week too many."), (ans - 1, "slip", "One week too few."),
        (P - sv, "gave_the_amount_needed", "Gave the amount still needed.")],
        [f"Still needed: ${P} − ${sv} = ${P - sv}", f"${P - sv} ÷ ${d} = {(P - sv) // d} remainder {(P - sv) % d}", f"The remainder needs one more week: {ans}"],
        {"P": P, "sv": sv, "d": d}, whole=True, show=str, auto_slips=False)


@checker(weeks_to_save)
def _(p):
    w, have = 0, p["sv"]
    while have < p["P"]:
        have += p["d"]
        w += 1
    return F(w)


@template(T, "competent", M + "06", M + "02")
def offer_saving(r):
    k = r.randint(3, 6)
    unit_a = r.randint(80, 220)
    pa = k * unit_a
    pb = unit_a + r.randint(10, 60)
    sets = r.randint(2, 6)
    N = k * sets
    ans = N * pb - sets * pa
    item = r.choice(["pens", "cookies", "badges", "erasers"])
    stem = (f"Shop A sells {item} at {k} for {dp(pa)}. Shop B sells the same {item} at {dp(pb)} each. "
            f"How much is saved by buying {N} {item} from Shop A instead of Shop B?")
    return build(offer_saving, stem, H(ans), [
        (H(pb - unit_a), "saving_for_one_only", f"Found the saving on one {item[:-1]} only."),
        (H(k * pb - pa), "saving_for_one_set_only", f"Found the saving for one set of {k}."),
        (H(abs(N * pb - N * pa)) if N * pb != N * pa and abs(N * pb - N * pa) != ans else None, "used_set_price_as_one_price", "Treated the set price as the price of one."),
        (H(ans + 10), "slip", "Slip."), (H(ans - 10), "slip", "Slip.")],
        [f"Shop A: {N} ÷ {k} = {sets} sets × {dp(pa)} = {dp(sets * pa)}", f"Shop B: {N} × {dp(pb)} = {dp(N * pb)}", f"Saved = {dp(ans)}"],
        {"k": k, "pa": pa, "pb": pb, "sets": sets}, money, auto_slips=False)


@checker(offer_saving)
def _(p):
    a = b = F(0)
    for _ in range(p["sets"]):
        a += F(p["pa"], 100)
        for _ in range(p["k"]):
            b += F(p["pb"], 100)
    return b - a


@template(T, "competent", M + "06", M + "02")
def money_backwards(r):
    x = r.choice(NAMES)
    a = r.randint(250, 900)
    n = r.randint(2, 5)
    b = r.randint(80, 350)
    left = r.randint(150, 1500)
    ans = a + n * b + left
    stem = (f"{x} spent {dp(a)} on lunch. Then {x} bought {n} pens at {dp(b)} each. {x} had {dp(left)} left. "
            f"How much money did {x} have at first?")
    return build(money_backwards, stem, H(ans), [
        (H(a + b + left), "forgot_to_multiply_pens", "Added the price of only one pen."),
        (H(a + n * b), "forgot_the_money_left", "Forgot the money left."),
        (H(abs(left - a - n * b)) if abs(left - a - n * b) else None, "subtracted_when_working_backwards", "Subtracted instead of adding back."),
        (H(ans + 10), "slip", "Slip."), (H(ans - 100), "slip", "Slip.")],
        [f"Pens: {n} × {dp(b)} = {dp(n * b)}", f"At first: {dp(a)} + {dp(n * b)} + {dp(left)} = {dp(ans)}"],
        {"a": a, "n": n, "b": b, "left": left}, money, auto_slips=False)


@checker(money_backwards)
def _(p):
    have = F(p["left"], 100)
    for _ in range(p["n"]):
        have += F(p["b"], 100)
    return have + F(p["a"], 100)


@template(T, "competent", M + "02", M + "01")
def coins_same_number(r):
    """math-pat-grouping-as-a-set"""
    x = r.choice(NAMES)
    kinds = r.choice([(20, 50), (10, 50), (20, 10 * 5), (5, 20)])
    a, b = kinds
    n = r.randint(8, 60)
    total = n * (a + b)
    stem = f"{x} has the same number of {a}-cent coins and {b}-cent coins. The coins are worth {dp(total)} altogether. How many {a}-cent coins does {x} have?"
    return build(coins_same_number, stem, n, [
        (F(total, a), "used_one_coin_only", f"Divided by {a} cents only."),
        (F(total, b), "used_one_coin_only", f"Divided by {b} cents only."),
        (F(total, a + b) * 2 if total % (a + b) == 0 else None, "counted_all_the_coins", "Found the total number of coins."),
        (n + 1, "slip", "Off by 1."), (n - 1, "slip", "Off by 1.")],
        [f"One of each: {a} + {b} = {a + b} cents", f"{total} ÷ {a + b} = {n}"], {"a": a, "b": b, "total": total}, whole=True, show=str, auto_slips=False)


@checker(coins_same_number)
def _(p):
    k = 0
    cents = 0
    while cents < p["total"]:
        cents += p["a"] + p["b"]
        k += 1
    return F(k) if cents == p["total"] else None


@template(T, "competent", M + "06", M + "02")
def price_two_equations(r):
    """math-pat-price-two-equations"""
    x = r.choice(NAMES)
    k = r.randint(2, 4)
    m1, m2 = sorted(r.sample(range(1, 7), 2))
    pn = r.randint(150, 650)
    pp = r.randint(40, 300)
    A = k * pn + m1 * pp
    B = k * pn + m2 * pp
    ask = r.choice(["pen", "notebook"])
    stem = (f"{k} notebooks and {m1} pens cost {dp(A)}. {k} notebooks and {m2} pens cost {dp(B)}. "
            f"What is the cost of one {ask}?")
    if ask == "pen":
        ans = pp
        wrong = [(H((B - A)), "forgot_to_divide_by_extra_pens", f"Gave the cost of the {m2 - m1} extra pens."),
                 (H(B // (k + m2)) if B % (k + m2) == 0 else H(round(B / (k + m2))), "divided_by_number_of_items", "Divided the total by the number of items."),
                 (H(round((B - A) / (m2 + m1))), "divided_by_wrong_number", "Divided by the total number of pens."),
                 (H(ans + 10), "slip", "Slip."), (H(ans - 10), "slip", "Slip.")]
        steps = [f"Extra {m2 - m1} pens cost {dp(B)} − {dp(A)} = {dp(B - A)}", f"1 pen = {dp(B - A)} ÷ {m2 - m1} = {dp(pp)}"]
    else:
        ans = pn
        wrong = [(H(round(A / k)), "ignored_the_pens", "Divided the first total by the number of notebooks."),
                 (H(round(A / (k + m1))), "divided_by_number_of_items", "Divided the total by the number of items."),
                 (H(pn + pp), "added_a_pen", "Forgot to take away the cost of all the pens."),
                 (H(ans + 10), "slip", "Slip."), (H(ans - 10), "slip", "Slip.")]
        steps = [f"1 pen = {dp((B - A) // (m2 - m1))}", f"{m1} pens = {dp(m1 * pp)}", f"{k} notebooks = {dp(A)} − {dp(m1 * pp)} = {dp(k * pn)}", f"1 notebook = {dp(pn)}"]
    return build(price_two_equations, stem, H(ans), wrong, steps, {"k": k, "m1": m1, "m2": m2, "A": A, "B": B, "ask": ask}, money, auto_slips=False)


@checker(price_two_equations)
def _(p):
    for pp in range(1, 5000):
        if (p["B"] - p["A"]) == (p["m2"] - p["m1"]) * pp:
            pen = pp
            break
    if p["ask"] == "pen":
        return F(pen, 100)
    return F(p["A"] - p["m1"] * pen, p["k"] * 100)


@template(T, "intermediate", M + "02", M + "01")
def coins_relationship(r):
    """math-pat-coins-notes-total-value"""
    x = r.choice(NAMES)
    a, b = r.choice([(50, 20), (20, 10), (50, 10), (10, 5), (20, 5)])
    kind = r.choice(["times", "more"])
    n = r.randint(6, 40)
    k = r.randint(2, 4)
    mo = r.randint(3, 12)
    cnt_a = k * n if kind == "times" else n + mo
    total = cnt_a * a + n * b
    rel = (f"{'twice' if k == 2 else str(k) + ' times'} as many {a}-cent coins as {b}-cent coins" if kind == "times"
           else f"{mo} more {a}-cent coins than {b}-cent coins")
    stem = f"{x} has {rel}. The total value of the coins is {dp(total)}. How many {b}-cent coins does {x} have?"
    if kind == "times":
        unit_v = k * a + b
        wrong = [(F(total, a), "divided_by_one_coin_value", f"Divided by {a} cents only."), (F(total, b), "divided_by_one_coin_value", f"Divided by {b} cents only."),
                 (F(total, a + b), "added_the_coin_values", "Added the two coin values without using the ratio."), (k * n, "gave_the_other_coin", f"Gave the number of {a}-cent coins."),
                 (n + 1, "slip", "Off by 1.")]
        steps = [f"Each group: {k} × {a} + {b} = {unit_v} cents", f"{total} ÷ {unit_v} = {n}"]
    else:
        wrong = [(F(total, a + b), "ignored_the_extra_coins", "Divided by the sum of the coin values without removing the extra coins."),
                 (F(total, b), "divided_by_one_coin_value", f"Divided by {b} cents only."), (n + mo, "gave_the_other_coin", f"Gave the number of {a}-cent coins."),
                 (n + 1, "slip", "Off by 1."), (n - 1, "slip", "Off by 1.")]
        steps = [f"Extra coins: {mo} × {a} = {mo * a} cents", f"Equal groups: {total} − {mo * a} = {total - mo * a} cents", f"{total - mo * a} ÷ {a + b} = {n}"]
    return build(coins_relationship, stem, n, wrong, steps, {"a": a, "b": b, "kind": kind, "k": k, "mo": mo, "total": total}, whole=True, show=str, auto_slips=False)


@checker(coins_relationship)
def _(p):
    for n in range(1, 5000):
        cnt = p["k"] * n if p["kind"] == "times" else n + p["mo"]
        if cnt * p["a"] + n * p["b"] == p["total"]:
            return F(n)
