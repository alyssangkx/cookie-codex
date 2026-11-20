"""Percentage (math-percentage): generators for basic, intermediate and competent levels.

GST is 9% (Singapore, from 2024). Money answers keep exact 2-decimal values; wrong options
are rounded to cents so no option gives itself away with extra decimal places.
"""
from common import *
from figures import Fig

T = "math-percentage"
O = "math-percentage-percentage-"
EXPR, PART, DISC, WHOLE, CHANGE = (O + f"0{i}" for i in range(1, 6))

ITEMS = ["school bag", "jacket", "watch", "pair of shoes", "bicycle", "calculator", "tennis racket",
         "set of headphones", "water bottle", "reading lamp", "keyboard", "board game", "football",
         "umbrella", "backpack"]
ITEM_PRICE = {"school bag": (25, 120), "jacket": (30, 150), "watch": (20, 300), "pair of shoes": (30, 150),
              "bicycle": (100, 800), "calculator": (10, 60), "tennis racket": (30, 250),
              "set of headphones": (20, 300), "water bottle": (5, 40), "reading lamp": (15, 100),
              "keyboard": (20, 200), "board game": (15, 80), "football": (10, 80), "umbrella": (8, 40),
              "backpack": (30, 150)}


ITEM_PLURAL = {"school bag": "school bags", "jacket": "jackets", "watch": "watches", "pair of shoes": "pairs of shoes",
               "bicycle": "bicycles", "calculator": "calculators", "tennis racket": "tennis rackets",
               "set of headphones": "sets of headphones", "water bottle": "water bottles",
               "reading lamp": "reading lamps", "keyboard": "keyboards", "board game": "board games",
               "football": "footballs", "umbrella": "umbrellas", "backpack": "backpacks"}
assert set(ITEM_PLURAL) == set(ITEMS) == set(ITEM_PRICE)


def item_for(r, price):
    """An item that really sells for about this price in Singapore (no $500 water bottles)."""
    ok = [i for i in ITEMS if ITEM_PRICE[i][0] <= price <= ITEM_PRICE[i][1]]
    if not ok:
        raise ValueError(f"no item in ITEM_PRICE sells for ${price}")
    return r.choice(ok)


GROUPS = ["pupils", "stamps", "cookies", "stickers", "marbles", "books", "cards", "beads"]


def pc(x):
    return f"{round(float(x), 1):g}%"


def r2(x):
    """Round a Fraction to cents."""
    x = F(x)
    return F(round(x * 100), 100)


def brute(pred, hi=20000):
    return next((F(n) for n in range(1, hi + 1) if pred(n)), None)


def cents(x):
    return (F(x) * 100).denominator == 1


def pcs(s, w):
    """Careless slips for a percentage answer."""
    return [(s + 10, "careless_slip", "Made a slip in the calculation."),
            (s - 10, "careless_slip", "Made a slip in the calculation."),
            (s + 5, "careless_slip", "Made a slip in the calculation."),
            (s * 10, "decimal_point_slip", "Put the decimal point in the wrong place.")]


# ---------------------------------------------------------------- basic

@template(T, "basic", PART)
def pct_of_quantity(r):
    p = r.choice([5, 10, 15, 20, 25, 30, 35, 40, 45, 60, 75, 80, 90])
    W = 20 * r.randint(2, 45)
    ans = W * p // 100
    g = r.choice(GROUPS)
    name = r.choice(NAMES)
    ctx = r.choice([
        f"{name} has {W} {g}. {p}% of them are rare ones. How many {g} are rare?",
        f"A box holds {W} {g}. {p}% of the {g} are new. How many are new?",
        f"There are {W} {g} in a collection. {name} gives away {p}% of them. How many {g} does {name} give away?",
        f"What is {p}% of {W}?",
    ])
    return build(pct_of_quantity, ctx, ans, [
        (W - ans, "found_the_remainder", f"Found {100 - p}% instead of {p}%."),
        (ans * 10, "decimal_point_slip", "Put the decimal point in the wrong place."),
        (F(W, p) if W % p == 0 else None, "divided_by_the_percent", f"Divided {W} by {p}."),
        (F(ans, 10) if ans % 10 == 0 else None, "decimal_point_slip", "Put the decimal point in the wrong place."),
        (ans + W // 20, "careless_slip", "Made a slip in the calculation."),
        (ans - W // 20, "careless_slip", "Made a slip in the calculation."),
        (p, "gave_the_percent", "Gave the percentage as the answer."),
    ], [f"1% of {W} = {F(W, 100)}", f"{p}% of {W} = {p} × {F(W, 100)} = {ans}"],
        {"p": p, "W": W}, unit_size=None, whole=True)


@checker(pct_of_quantity)
def _(q):
    return brute(lambda x: x * 100 == q["p"] * q["W"])


@template(T, "basic", EXPR)
def part_as_percent(r):
    t = r.choice([8, 20, 25, 40, 50, 80, 200, 250])
    s = r.randint(1, t - 1)
    if cents(F(s, t)) is False or (F(s * 100, t) * 2).denominator != 1:
        return None
    ans = F(s * 100, t)
    n = r.choice(NAMES)
    ctx = r.choice([
        f"{n} answered {s} out of {t} questions correctly. What percentage of the questions did {n} answer correctly?",
        f"{s} of the {t} pupils in a class wear spectacles. What percentage of the class wears spectacles?",
        f"A tank holds {plural(t, 'litre')}. It has {plural(s, 'litre')} of water. What percentage of the tank is full?",
        f"{n} saved ${s} of ${t}. What percentage of ${t} did {n} save?",
    ])
    return build(part_as_percent, ctx, ans, [
        (100 - ans, "found_the_other_part", "Found the percentage that was left over."),
        (F(t * 100, s), "reversed_the_fraction", f"Divided {t} by {s}."),
        (s, "gave_the_count", "Gave the part itself instead of a percentage."),
        (F(s, t), "forgot_to_multiply_by_100", "Wrote the fraction as a decimal and did not multiply by 100."),
        (ans + 10, "careless_slip", "Made a slip in the calculation."),
        (ans / 10, "decimal_point_slip", "Put the decimal point in the wrong place."),
    ], [f"Fraction = {s}/{t}", f"Percentage = {s}/{t} × 100% = {pc(ans)}"], {"s": s, "t": t}, pc, auto_slips=False)


@checker(part_as_percent)
def _(q):
    # find the percentage x (in half-percents) such that x% of t equals s
    return next(F(h, 2) for h in range(1, 201) if F(h, 2) * q["t"] == 100 * q["s"])


@template(T, "basic", DISC)
def discount_amount(r):
    price = 20 * r.randint(2, 30)
    d = r.choice([5, 10, 15, 20, 25, 30, 40, 50])
    item = item_for(r, price)
    ans = F(price * d, 100)
    stem = f"{a_an(item).capitalize()} {item} usually costs ${price}. It is on sale at a discount of {d}%. How much is the discount, in dollars?"
    return build(discount_amount, stem, ans, [
        (price - ans, "gave_the_sale_price", "Gave the selling price instead of the discount."),
        (d, "gave_the_percent", f"Gave {d} as the number of dollars."),
        (F(price, d), "divided_by_the_percent", f"Divided {price} by {d}."),
        (ans * 10, "decimal_point_slip", "Put the decimal point in the wrong place."),
        (ans + 2, "careless_slip", "Made a slip in the calculation."),
        (ans - 2, "careless_slip", "Made a slip in the calculation."),
    ], [f"Discount = {d}% of ${price}", f"= {d} ÷ 100 × {price} = ${ans}"], {"price": price, "d": d}, money,
        auto_slips=False, whole=True)


@checker(discount_amount)
def _(q):
    return brute(lambda x: x * 100 == q["price"] * q["d"])


@template(T, "basic", DISC)
def gst_amount(r):
    price = 10 * r.randint(2, 40)
    item = item_for(r, price)
    ans = F(price * 9, 100)
    stem = f"{a_an(item).capitalize()} {item} costs ${price} before GST. GST is 9%. How much is the GST on the {item}?"
    return build(gst_amount, stem, ans, [
        (price + ans, "added_gst_to_the_price", "Gave the price including GST instead of the GST."),
        (price - ans, "subtracted_instead_of_added", "Took the GST off the price."),
        (F(price * 9, 1000), "decimal_point_slip", "Put the decimal point in the wrong place."),
        (F(price, 9), "divided_by_the_percent", "Divided the price by 9."),
        (r2(ans + F(9, 10)), "careless_slip", "Made a slip in the calculation."),
        (r2(ans - F(9, 10)), "careless_slip", "Made a slip in the calculation."),
    ], [f"GST = 9% of ${price}", f"= 9 ÷ 100 × {price} = {money(ans)}"], {"price": price}, money, auto_slips=False)


@checker(gst_amount)
def _(q):
    return F(sum(F(9, 100) for _ in range(q["price"])))  # 9 cents per dollar of price


@template(T, "basic", WHOLE)
def find_whole_simple(r):
    p = r.choice([5, 10, 20, 25, 50])
    v = r.randint(3, 40) * (2 if p == 5 else 1)
    ans = F(v * 100, p)
    g = r.choice(GROUPS)
    n = r.choice(NAMES)
    ctx = r.choice([
        f"{p}% of the {g} in a box are broken. There are {v} broken {g}. How many {g} are in the box?",
        f"{n} spent {p}% of the money in a wallet and spent ${v}. How much money was in the wallet at first?",
        f"{v} is {p}% of a number. What is the number?",
    ])
    cash = "wallet" in ctx
    return build(find_whole_simple, ctx, ans, [
        (F(v * p, 100), "found_percent_of_the_given", f"Found {p}% of {v}."),
        (v * p, "multiplied_by_the_percent", f"Multiplied {v} by {p}."),
        (ans - v, "gave_the_rest", "Found the amount left over."),
        (ans + 10, "careless_slip", "Made a slip in the calculation."),
        (ans - 10, "careless_slip", "Made a slip in the calculation."),
        (ans / 10, "decimal_point_slip", "Put the decimal point in the wrong place."),
    ], [f"{p}% → {v}", f"1% → {F(v, p)}", f"100% → {ans}"], {"p": p, "v": v}, money if cash else frac,
        auto_slips=False, whole=True)


@checker(find_whole_simple)
def _(q):
    return brute(lambda x: x * q["p"] == q["v"] * 100)


@template(T, "basic", CHANGE)
def pct_increase_simple(r):
    old = r.choice([20, 25, 40, 50, 80, 200, 250, 400])
    ch = r.randint(1, old)
    if (F(ch * 100, old) * 2).denominator != 1:
        return None
    new = old + ch
    n = r.choice(NAMES)
    ctx = r.choice([
        f"The number of visitors to a library rose from {old} to {new}. What was the percentage increase?",
        f"{n}'s height increased from {old} cm to {new} cm. What was the percentage increase in height?",
        f"A plant grew from {old} cm to {new} cm. By what percentage did the plant grow?",
    ])
    ans = F(ch * 100, old)
    return build(pct_increase_simple, ctx, ans, [
        (F(ch * 100, new), "divided_by_the_new_value", "Divided the change by the new value instead of the old."),
        (F(new * 100, old), "gave_new_as_percent_of_old", "Found the new value as a percentage of the old value."),
        (ch, "gave_the_change", "Gave the increase itself, not a percentage."),
        (ans + 10, "careless_slip", "Made a slip in the calculation."),
        (ans - 5, "careless_slip", "Made a slip in the calculation."),
        (ans / 10, "decimal_point_slip", "Put the decimal point in the wrong place."),
    ], [f"Increase = {new} − {old} = {ch}", f"Percentage increase = {ch}/{old} × 100% = {pc(ans)}"],
        {"old": old, "new": new}, pc, auto_slips=False)


@checker(pct_increase_simple)
def _(q):
    return next(F(h, 2) for h in range(1, 401) if q["old"] * (100 + F(h, 2)) == 100 * q["new"])


# ---------------------------------------------------------------- intermediate

@template(T, "intermediate", DISC)
def sale_price(r):
    price = 20 * r.randint(3, 40)
    d = r.choice([10, 15, 20, 25, 30, 35, 40, 50])
    item = item_for(r, price)
    ans = F(price * (100 - d), 100)
    n = r.choice(NAMES)
    stem = f"{n} bought {a_an(item)} {item} with {a_an(d)} {d}% discount. The usual price was ${price}. How much did {n} pay?"
    return build(sale_price, stem, ans, [
        (F(price * d, 100), "gave_the_discount", "Gave the discount instead of the price paid."),
        (price + F(price * d, 100), "added_instead_of_subtracted", "Added the discount to the usual price."),
        (price - d, "subtracted_percent_as_dollars", f"Subtracted ${d} instead of {d}% of the price."),
        (ans + 5, "careless_slip", "Made a slip in the calculation."),
        (ans - 5, "careless_slip", "Made a slip in the calculation."),
    ], [f"Discount = {d}% of ${price} = ${F(price * d, 100)}", f"Price paid = ${price} − ${F(price * d, 100)} = {money(ans)}",
        f"(or {100 - d}% of ${price} = {money(ans)})"], {"price": price, "d": d}, money, auto_slips=False, whole=True)


@checker(sale_price)
def _(q):
    # 1% of the price, taken (100 - d) times
    one = F(q["price"], 100)
    return sum(one for _ in range(100 - q["d"]))


@template(T, "intermediate", DISC)
def price_with_gst(r):
    price = 10 * r.randint(3, 60)
    item = item_for(r, price)
    ans = F(price * 109, 100)
    n = r.choice(NAMES)
    stem = f"The price of {a_an(item)} {item} is ${price} before GST. {n} pays 9% GST on it. How much does {n} pay altogether?"
    return build(price_with_gst, stem, ans, [
        (F(price * 9, 100), "gave_gst_only", "Gave only the GST."),
        (price - F(price * 9, 100), "subtracted_instead_of_added", "Took 9% off instead of adding 9%."),
        (price + 9, "added_percent_as_dollars", "Added $9 instead of 9% of the price."),
        (F(price * 109, 1000), "decimal_point_slip", "Put the decimal point in the wrong place."),
        (r2(ans + F(9, 10)), "careless_slip", "Made a slip in the calculation."),
        (r2(ans - F(9, 10)), "careless_slip", "Made a slip in the calculation."),
    ], [f"GST = 9% of ${price} = {money(F(price * 9, 100))}", f"Total = ${price} + {money(F(price * 9, 100))} = {money(ans)}",
        "(or 109% of the price)"], {"price": price}, money, auto_slips=False)


@checker(price_with_gst)
def _(q):
    return F(q["price"]) * F(109, 100)


@template(T, "intermediate", DISC, CHANGE, weight=2)
def discount_then_gst(r):
    """math-pat-percent-gst-discount-direct"""
    price = 5 * r.randint(8, 80)
    d = r.choice([10, 20, 25, 30, 40, 50])
    sale = F(price * (100 - d), 100)
    ans = sale * F(109, 100)
    if not cents(ans) or not cents(sale):
        return None
    item = item_for(r, price)
    stem = (f"{a_an(item).capitalize()} {item} is marked ${price}. The shop gives {a_an(d)} {d}% discount and then adds 9% GST on the discounted price. "
            f"How much must the customer pay?")
    gst_first = F(price * 109, 100) * F(100 - d, 100)
    return build(discount_then_gst, stem, ans, [
        (sale, "forgot_gst", "Stopped after the discount and forgot the GST."),
        (price * F(100 + 9 - d, 100), "combined_the_percentages", f"Worked out {100 + 9 - d}% of the price: the GST is on the discounted price only."),
        (F(price * 109, 100), "forgot_discount", "Added the GST but forgot the discount."),
        (r2(gst_first) if gst_first != ans else None, "wrong_order", "Applied GST to the marked price first."),
        (r2(ans + F(9, 10)), "careless_slip", "Made a slip in the calculation."),
        (r2(ans - F(9, 10)), "careless_slip", "Made a slip in the calculation."),
    ], [f"Price after discount = {100 - d}% of ${price} = {money(sale)}",
        f"GST = 9% of {money(sale)} = {money(sale * F(9, 100))}", f"Total = {money(ans)}"],
        {"price": price, "d": d}, money, auto_slips=False)


@checker(discount_then_gst)
def _(q):
    c = q["price"] * 100  # in cents
    c = c - c * q["d"] // 100
    c = c + c * 9 // 100
    return F(c, 100)


@template(T, "intermediate", CHANGE)
def pct_change_two_values(r):
    old = r.choice([20, 25, 40, 50, 60, 80, 120, 150, 200, 250, 300, 400])
    up = r.random() < 0.5
    pct = r.choice([5, 10, 12.5, 15, 20, 25, 30, 35, 40, 50, 60, 75])
    ch = F(old) * F(pct).limit_denominator(2) / 100
    if ch.denominator != 1:
        return None
    new = old + ch if up else old - ch
    if new <= 0:
        return None
    new = int(new)
    ch = int(ch)
    word, sub = ("rose", "increase") if up else ("fell", "decrease")
    n = r.choice(NAMES)
    what = r.choice([("The number of pupils in a school", ""), ("The mass of a parcel", " g"),
                     (f"{n}'s savings", ""), ("The number of visitors to a museum", "")])
    if "savings" in what[0]:
        old_s, new_s = f"${old}", f"${new}"
    else:
        old_s, new_s = f"{old}{what[1]}", f"{new}{what[1]}"
    stem = f"{what[0]} {word} from {old_s} to {new_s}. What was the percentage {sub}?"
    ans = F(pct).limit_denominator(2)
    return build(pct_change_two_values, stem, ans, [
        (F(ch * 100, new), "divided_by_the_new_value", "Divided the change by the new value instead of the old value."),
        (F(new * 100, old) if not up else F(new * 100, old) - 0 if False else F(new * 100, old), "new_as_percent_of_old",
         "Found the new value as a percentage of the old value."),
        (F(ch), "gave_the_change", "Gave the change itself, not a percentage."),
        (ans + 5, "careless_slip", "Made a slip in the calculation."),
        (ans - 5, "careless_slip", "Made a slip in the calculation."),
        (ans / 10, "decimal_point_slip", "Put the decimal point in the wrong place."),
    ], [f"Change = {abs(new - old)}", f"Percentage {sub} = {abs(new - old)}/{old} × 100% = {pc(ans)}"],
        {"old": old, "new": new}, pc, auto_slips=False)


@checker(pct_change_two_values)
def _(q):
    return next(F(h, 2) for h in range(1, 401) if abs(q["new"] - q["old"]) * 200 == h * q["old"])


@template(T, "intermediate", WHOLE, DISC, weight=2)
def find_original_after_discount(r):
    """math-pat-percent-reverse-find-original"""
    d = r.choice([10, 20, 25, 30, 40, 50, 60])
    orig = 20 * r.randint(3, 40)
    paid = F(orig * (100 - d), 100)
    if paid.denominator != 1:
        return None
    item = item_for(r, orig)
    n = r.choice(NAMES)
    stem = f"After {a_an(d)} {d}% discount, {n} paid ${paid} for {a_an(item)} {item}. What was the price of the {item} before the discount?"
    return build(find_original_after_discount, stem, orig, [
        (paid + F(paid * d, 100), "took_percent_of_the_given", f"Added {d}% of ${paid} to ${paid}: the {d}% is of the original price."),
        (paid + d, "added_percent_as_dollars", f"Added ${d} instead of finding the original."),
        (F(paid * (100 + d), 100) if False else F(paid * 100, 100 - d + 0) * F(100 - d, 100) if False else orig - paid,
         "gave_the_discount", "Found the discount instead of the original price."),
        (orig + 20, "careless_slip", "Made a slip in the calculation."),
        (orig - 20, "careless_slip", "Made a slip in the calculation."),
    ], [f"{100 - d}% of the original = ${paid}", f"1% = ${F(paid, 100 - d)}", f"100% = ${orig}"],
        {"d": d, "paid": int(paid)}, money, auto_slips=False, whole=True)


@checker(find_original_after_discount)
def _(q):
    return brute(lambda x: x * (100 - q["d"]) == q["paid"] * 100)


@template(T, "intermediate", PART, EXPR)
def percent_of_remainder_forward(r):
    M = 100 * r.randint(2, 15)
    a = r.choice([10, 20, 25, 30, 40])
    b = r.choice([10, 20, 25, 40, 50])
    left = F(M * (100 - a) * (100 - b), 10000)
    if left.denominator != 1:
        return None
    n = r.choice(NAMES)
    thing1, thing2 = r.choice([("a book", "lunch"), ("a game", "snacks"), ("a T-shirt", "a movie ticket")])
    stem = (f"{n} had ${M}. {n} spent {a}% of it on {thing1} and {b}% of the remainder on {thing2}. "
            f"How much money did {n} have left?")
    return build(percent_of_remainder_forward, stem, left, [
        (F(M * (100 - a - b), 100), "added_the_percents", f"Took away {a + b}% of ${M} as if both percentages were of the same amount."),
        (F(M * (100 - a), 100), "stopped_after_one_step", f"Stopped after buying {thing1}."),
        (F(M * a, 100) + F(M * (100 - a) * b, 10000), "gave_total_spent", "Gave the total amount spent."),
        (left + 10, "careless_slip", "Made a slip in the calculation."),
        (left - 10, "careless_slip", "Made a slip in the calculation."),
    ], [f"After {thing1}: {100 - a}% of ${M} = ${F(M * (100 - a), 100)}",
        f"After the second purchase: {100 - b}% of ${F(M * (100 - a), 100)} = ${left}"],
        {"M": M, "a": a, "b": b}, money, auto_slips=False, whole=True)


@checker(percent_of_remainder_forward)
def _(q):
    c = q["M"]
    c -= F(c * q["a"], 100)
    c -= F(c * q["b"], 100)
    return c


@template(T, "intermediate", DISC, calc=True)
def simple_interest_loan(r):
    """math-pat-simple-interest-loan"""
    P = 1000 * r.randint(6, 60)
    rate = r.choice([2, 3, 4, 5])
    yrs = r.choice([2, 3, 4, 5])
    total = P + P * rate * yrs // 100
    mths = 12 * yrs
    if (total * 1) % mths:
        return None
    each = F(total, mths)
    n = r.choice(NAMES)
    stem = (f"{n} borrowed ${P} from a bank at a simple interest rate of {rate}% per year. "
            f"{n} will repay the loan with its interest in {mths} equal monthly instalments over {yrs} years. "
            f"How much is each instalment?")
    one_year = P + P * rate // 100
    comp = F(P) * (1 + F(rate, 100)) ** yrs
    return build(simple_interest_loan, stem, each, [
        (F(P, mths), "ignored_the_interest", "Divided the loan only and forgot the interest."),
        (F(one_year, mths), "interest_for_one_year_only", f"Charged interest for 1 year instead of {yrs} years."),
        (F(P * rate * yrs, 100 * mths), "gave_interest_per_month", "Divided the interest only."),
        (F(comp.numerator, comp.denominator) / mths if (comp / mths).denominator == 1 else None, "used_compound_interest", "Used compound interest."),
        (each + 10, "careless_slip", "Made a slip in the calculation."),
        (each - 10, "careless_slip", "Made a slip in the calculation."),
    ], [f"Interest = ${P} × {rate}% × {yrs} = ${P * rate * yrs // 100}", f"Total to repay = ${total}",
        f"Each instalment = ${total} ÷ {mths} = ${each}"], {"P": P, "rate": rate, "yrs": yrs}, money,
        auto_slips=False, whole=True)


@checker(simple_interest_loan)
def _(q):
    total, i = F(q["P"]), 0
    for _ in range(q["yrs"]):  # interest year by year on the same principal
        total += F(q["P"] * q["rate"], 100)
    return total / (12 * q["yrs"])


# ---------------------------------------------------------------- competent

CLUBS = [("Cooking", "Chess", "Robotics"), ("Drama", "Art", "Choir"), ("Football", "Netball", "Swimming"),
         ("Guitar", "Piano", "Drumming")]


@template(T, "competent", PART, CHANGE)
def two_groups_both_change(r):
    """math-pat-percent-two-groups-both-change"""
    k = r.randint(2, 6)
    c = 5 * r.randint(2, 30)
    p = r.choice([10, 20, 25, 30, 40, 50])
    g = r.choice([10, 20, 25, 30, 40, 50, 60])
    moved = F(p * (k + 1) * c, 100)
    if moved.denominator != 1:
        return None
    R = F(100 * moved, g)
    if R.denominator != 1:
        return None
    final = int(R + moved)
    A, B, C = r.choice(CLUBS)
    stem = (f"The {A} Club had {k} times as many members as the {B} Club. {p}% of the members of each of these two clubs "
            f"left to join the {C} Club. As a result, the number of members in the {C} Club increased by {g}% to {final}. "
            f"How many members did the {A} Club have at first?")
    return build(two_groups_both_change, stem, k * c, [
        (c, "gave_the_smaller_club", f"Gave the members of the {B} Club."),
        (R, "gave_the_third_club_at_first", f"Gave the number of members the {C} Club had at first."),
        (moved, "gave_the_number_who_left", "Gave the number of members who moved clubs."),
        (k * c + 5 * k, "careless_slip", "Made a slip in the calculation."),
        (k * c - 5 * k, "careless_slip", "Made a slip in the calculation."),
        ((k + 1) * c, "gave_both_clubs", "Gave the total of the two clubs."),
    ], [f"{C} Club at first: {100 + g}% = {final}, so 100% = {int(R)}", f"Members who joined = {final} − {int(R)} = {int(moved)}",
        f"{p}% of ({k} + 1) units = {int(moved)}", f"1 unit = {c}", f"{A} Club = {k} × {c} = {k * c}"],
        {"k": k, "p": p, "g": g, "final": final}, whole=True, auto_slips=False)


@checker(two_groups_both_change)
def _(q):
    moved = F(q["final"]) - F(q["final"] * 100, 100 + q["g"])
    c = brute(lambda c: F(q["p"] * (q["k"] + 1) * c, 100) == moved, 5000)
    return q["k"] * c


@template(T, "competent", PART, CHANGE)
def constant_part_add(r):
    """math-pat-constant-part-new-fraction"""
    p = r.choice([40, 50, 60, 75, 80])
    q = r.choice([x for x in (20, 25, 30, 40, 50, 60) if x < p])
    N = 20 * r.randint(1, 15)
    if F(N * p, q).denominator != 1 or F(N * p, 100).denominator != 1:
        return None
    N2 = F(N * p, q)
    x = N2 - N
    if x <= 0:
        return None
    part, other, noun = r.choice([("boys", "girls", "members of a club"), ("girls", "boys", "members of a choir"),
                                  ("boys", "girls", "pupils in a class")])
    stem = (f"{p}% of the {noun} are {part}. After {int(x)} more {other} join, "
            f"the {part} make up {q}% of all the {noun.split(' ')[0]}. How many {noun.split(' ')[0]} were there at first?")
    return build(constant_part_add, stem, N, [
        (N2, "gave_the_new_total", "Gave the total after the new items joined."),
        (F(N * p, 100), "gave_the_unchanged_part", f"Gave the number of {part}."),
        (x, "gave_the_number_added", "Gave the number added."),
        (F(x * 100, p - q), "used_percent_difference_as_whole", "Took the difference in percentages as the whole."),
        (N + 20, "careless_slip", "Made a slip in the calculation."),
        (N - 20, "careless_slip", "Made a slip in the calculation."),
    ], [f"The {part} stay the same: {p}% of the old total = {q}% of the new total",
        f"Old total : new total = {q} : {p} = {q // gcd(p, q)} : {p // gcd(p, q)}",
        f"Difference = {plural((p - q) // gcd(p, q), 'unit')} = {int(x)}", f"Old total = {q // gcd(p, q)} × {int(x) // ((p - q) // gcd(p, q))} = {N}"],
        {"p": p, "q": q, "x": int(x)}, whole=True, auto_slips=False)


@checker(constant_part_add)
def _(q):
    return brute(lambda N: N * q["p"] == q["q"] * (N + q["x"]), 5000)


@template(T, "competent", PART, CHANGE)
def constant_part_remove(r):
    """math-pat-constant-part-new-fraction"""
    p = r.choice([20, 25, 30, 40])
    q = r.choice([x for x in (40, 50, 60, 75) if x > p])
    N = 20 * r.randint(2, 20)
    N2 = F(N * p, q)
    if N2.denominator != 1 or F(N * p, 100).denominator != 1:
        return None
    x = N - N2
    if x <= 0:
        return None
    part, other = r.choice([("chocolates", "mints"), ("red sweets", "green sweets"), ("strawberry sweets", "orange sweets")])
    nm = r.choice(NAMES)
    stem = (f"{nm} had {N} sweets in a bag. {p}% of them were {part}, and the rest were {other}. {nm} then ate some of the {other}, "
            f"so the {part} became {q}% of the sweets left. How many sweets did {nm} eat?")
    return build(constant_part_remove, stem, x, [
        (N2, "gave_the_number_left", "Gave the number of sweets left in the bag."),
        (F(N * (q - p), 100), "took_percent_difference_of_total", f"Found {q - p}% of {N}."),
        (F(N * p, 100), "gave_the_unchanged_part", f"Gave the number of {part}."),
        (x + 5, "careless_slip", "Made a slip in the calculation."),
        (x - 5, "careless_slip", "Made a slip in the calculation."),
        (N - F(N * p, 100), "gave_the_other_sweets", f"Gave the number of {other} at first."),
    ], [f"Number of {part} = {p}% of {N} = {int(F(N * p, 100))}", f"This is {q}% of the sweets left",
        f"Sweets left = {int(F(N * p, 100))} ÷ {q} × 100 = {int(N2)}", f"Sweets eaten = {N} − {int(N2)} = {int(x)}"],
        {"p": p, "q": q, "N": N}, whole=True, auto_slips=False)


@checker(constant_part_remove)
def _(q):
    return brute(lambda x: q["N"] * q["p"] == q["q"] * (q["N"] - x), q["N"])


@template(T, "competent", WHOLE, DISC, calc=True)
def reverse_items_affordable(r):
    """math-pat-percent-reverse-find-original"""
    d = r.choice([10, 20, 25, 30, 40, 50])
    orig = 20 * r.randint(3, 30)
    paid = F(orig * (100 - d), 100)
    if paid.denominator != 1:
        return None
    k = r.randint(2, 7)
    B = orig * k + r.randint(0, orig - 1)
    if B // paid == k:
        return None
    item = item_for(r, orig)
    n = r.choice(NAMES)
    stem = (f"During a sale, {a_an(item)} {item} was sold at {a_an(d)} {d}% discount for ${paid}. "
            f"{n} has ${B}. How many of these {ITEM_PLURAL[item]} can {n} buy at the usual price?")
    return build(reverse_items_affordable, stem, k, [
        (int(B // paid), "used_the_sale_price", "Divided by the sale price, not the usual price."),
        (F(B, orig + 0) if B % orig == 0 and False else int(B // (paid + F(paid * d, 100))), "added_percent_of_given", f"Added {d}% of ${paid} to find the usual price."),
        (k + 1, "rounded_up", "Rounded the answer up instead of down."),
        (k - 1, "miscounted", "Made a slip in the count."),
        (int(B // (paid + d)), "added_percent_as_dollars", f"Added ${d} to find the usual price."),
    ], [f"{100 - d}% of the usual price = ${paid}", f"Usual price = ${paid} ÷ {100 - d} × 100 = ${orig}",
        f"${B} ÷ ${orig} = {B / orig:.2f}, so {n} can buy {k}"], {"d": d, "paid": int(paid), "B": B}, whole=True,
        auto_slips=False)


@checker(reverse_items_affordable)
def _(q):
    orig = brute(lambda x: x * (100 - q["d"]) == q["paid"] * 100)
    count = 0
    while (count + 1) * orig <= q["B"]:
        count += 1
    return F(count)


@template(T, "competent", WHOLE, CHANGE, calc=True)
def successive_changes_original(r):
    a = r.choice([10, 20, 25, 30, 50])
    b = r.choice([10, 20, 25, 40, 50])
    orig = 20 * r.randint(2, 40)
    fin = F(orig * (100 + a) * (100 - b), 10000)
    if fin.denominator != 1 or a == b:
        return None
    item = r.choice(["a concert ticket", "a pair of trainers", "a bicycle", "a bag"])
    stem = (f"The price of {item} was increased by {a}% in June. In July the new price was reduced by {b}% "
            f"and it then cost ${fin}. What was the price before June?")
    net = F(fin * 100, 100 + a - b)
    return build(successive_changes_original, stem, orig, [
        (net, "used_net_percentage", f"Treated the two changes as a single change of {a - b}%."),
        (F(fin * (100 + b), 100), "undid_only_the_second_change", f"Undid only the {b}% reduction."),
        (F(fin * (100 + b) * (100 - a), 10000), "undid_with_wrong_percents", "Undid each change using the wrong percentage."),
        (orig + 20, "careless_slip", "Made a slip in the calculation."),
        (orig - 20, "careless_slip", "Made a slip in the calculation."),
        (fin, "gave_final_price", "Gave the final price."),
    ], [f"After the increase: {100 + a}% of the original", f"After the reduction: {100 - b}% of that = ${fin}",
        f"{100 - b}% of {100 + a}% of the original = {F((100 - b) * (100 + a), 100)}% = ${fin}",
        f"Original = ${fin} ÷ {F((100 - b) * (100 + a), 100)} × 100 = ${orig}"],
        {"a": a, "b": b, "fin": int(fin)}, money, whole=True, auto_slips=False)


@checker(successive_changes_original)
def _(q):
    return brute(lambda o: F(o * (100 + q["a"]), 100) * (100 - q["b"]) == q["fin"] * 100)


@template(T, "competent", PART, CHANGE)
def successive_change_overall(r):
    a = r.choice([10, 20, 25, 30, 40, 50])
    b = r.choice([10, 20, 25, 30, 40, 50])
    net = F((100 + a) * (100 - b), 100) - 100
    if net == 0 or net.denominator != 1:
        return None
    item = r.choice(["a toy robot", "a school bag", "a football", "a watch"])
    stem = (f"The price of {item} was first increased by {a}% and later the new price was decreased by {b}%. "
            f"What was the overall change compared with the original price?")

    def code(x):
        x = F(x)
        return int(abs(x) * 10) * 2 + (1 if x < 0 else 0) + 1

    def show(c):
        c -= 1
        pct = F(c // 2, 10)
        return f"{float(pct):g}% {'decrease' if c % 2 else 'increase'}"

    ans = code(net)
    opts = [
        (show(code(a - b) if a != b else code(-1)), code(a - b) if a != b else code(-1)),
        (show(code(-net)), code(-net)),
        (show(code(a + b)), code(a + b)),
        (show(code(max(a, b)) if False else code(-a)), code(-a)),
        (show(code(net + 5)), code(net + 5)),
    ]
    tags = [("added_the_percents_with_signs", f"Subtracted {b} from {a} to get {a - b}%."),
            ("wrong_direction", "Gave the right size but the wrong direction."),
            ("added_the_percents", f"Added {a}% and {b}%."),
            ("used_first_change_only", f"Used the first change of {a}% increase."),
            ("careless_slip", "Made a slip in the calculation.")]
    wrong = [(v, t, w) for (v, (t, w)) in zip(opts, tags)]
    return build(successive_change_overall, stem, ans, [(v[1], t, w) for v, t, w in wrong],
                 [f"Take the original as 100", f"After the increase: {100 + a}", f"After the decrease: {100 + a} × {100 - b}% = {F((100 + a) * (100 - b), 100)}",
                  f"Overall change = {F((100 + a) * (100 - b), 100) - 100} → {show(ans)}"],
                 {"a": a, "b": b}, show, auto_slips=False)


@checker(successive_change_overall)
def _(q):
    v = 100 * 100
    v = v * (100 + q["a"]) // 100
    v = v * (100 - q["b"]) // 100
    net = F(v - 10000, 100)
    return F(int(abs(net) * 10) * 2 + (1 if net < 0 else 0) + 1)


@template(T, "competent", WHOLE, EXPR)
def remainder_backwards(r):
    a = r.choice([10, 20, 25, 30, 40, 50])
    b = r.choice([10, 20, 25, 40, 50])
    M = 100 * r.randint(2, 20)
    left = F(M * (100 - a) * (100 - b), 10000)
    if left.denominator != 1 or a == b:
        return None
    n = r.choice(NAMES)
    stem = (f"{n} spent {a}% of the money on a bag and {b}% of the remainder on a pen. "
            f"{n} had ${left} left. How much money did {n} have at first?")
    return build(remainder_backwards, stem, M, [
        (F(left * 100, 100 - a - b), "added_the_percents", f"Treated ${left} as {100 - a - b}% of the money."),
        (F(left * 100, 100 - b), "worked_back_one_step", f"Undid only the {b}% spent on the pen."),
        (left + F(left * (a + b), 100), "added_percents_of_the_given", f"Added {a + b}% of ${left} to ${left}."),
        (M + 20, "careless_slip", "Made a slip in the calculation."),
        (M - 20, "careless_slip", "Made a slip in the calculation."),
        (F(left * 100, 100 - b) - left, "gave_the_pen_and_bag", "Gave the amount spent on the bag and pen only."),
    ], [f"After the bag: {100 - a}% of the money", f"After the pen: {100 - b}% of that = ${left}",
        f"{100 - b}% → ${left}", f"1% → ${F(left, 100 - b)}", f"100% (after the bag) = ${F(left * 100, 100 - b)}",
        f"{100 - a}% of the money = ${F(left * 100, 100 - b)}", f"Money at first = ${M}"],
        {"a": a, "b": b, "left": int(left)}, money, whole=True, auto_slips=False)


@checker(remainder_backwards)
def _(q):
    return brute(lambda M: F(F(M * (100 - q["a"]), 100) * (100 - q["b"]), 100) == q["left"], 5000)


@template(T, "competent", WHOLE, DISC)
def reverse_gst(r):
    """math-pat-percent-gst-discount-direct"""
    P = r.randint(20, 400)
    T_ = F(P * 109, 100)
    n = r.choice(NAMES)
    item = item_for(r, P)
    stem = f"{n} paid {money(T_)} for {a_an(item)} {item}. This amount included 9% GST. What was the price of the {item} before GST?"
    return build(reverse_gst, stem, P, [
        (r2(T_ - T_ * F(9, 100)), "took_gst_off_the_total", "Took 9% off the total: the GST is 9% of the price before GST."),
        (T_ - 9, "subtracted_percent_as_dollars", "Subtracted $9 from the total."),
        (r2(T_ * F(9, 100)), "gave_9_percent_of_total", "Found 9% of the total."),
        (P + 5, "careless_slip", "Made a slip in the calculation."),
        (P - 5, "careless_slip", "Made a slip in the calculation."),
        (r2(T_ / 2), "divided_by_two", "Divided the total by 2."),
    ], [f"Price before GST = 100%, with GST = 109%", f"109% → {money(T_)}", f"1% → {money(T_ / 109)}",
        f"100% → ${P}"], {"P": P}, money, auto_slips=False)


@checker(reverse_gst)
def _(q):
    cents_total = q["P"] * 109  # cents with GST
    return brute(lambda x: x * 109 == cents_total, 100000)


@template(T, "competent", EXPR, CHANGE)
def compare_more_less(r):
    # realistic sizes only (bank review: "900% more" is not a P6 question): 10%-100% more, 10%-90% fewer, answers
    # a whole number or one decimal place
    pairs_more = [(25, 20), (60, F(75, 2)), (100, 50)]
    pairs_less = [(20, 25), (50, 100), (60, 150)]
    n1, n2 = two_names(r)
    if r.random() < 0.5:
        p, ans = r.choice(pairs_more)
        stem = f"{n1} has {p}% more stickers than {n2}. {n2} has what percentage fewer stickers than {n1}?"
        steps = [f"Let {n2} have 100 units, so {n1} has {100 + p}", f"{n2} has {p} fewer than {n1}",
                 f"{p}/{100 + p} × 100% = {pc(ans)}"]
        kind = "more"
    else:
        p, ans = r.choice(pairs_less)
        stem = f"{n1} has {p}% fewer stickers than {n2}. {n2} has what percentage more stickers than {n1}?"
        steps = [f"Let {n2} have 100 units, so {n1} has {100 - p}", f"{n2} has {p} more than {n1}",
                 f"{p}/{100 - p} × 100% = {ans}%"]
        kind = "less"
    return build(compare_more_less, stem, ans, [
        (p, "gave_the_same_percentage", "Used the same percentage in both directions."),
        (100 - p if p < 100 else 100 + p, "gave_the_complement", "Gave 100% minus the percentage."),
        (100 + p if kind == "more" else 100 - p if p < 100 else p + 10, "gave_one_of_the_totals", "Gave one of the totals in units."),
        (ans + 10, "careless_slip", "Made a slip in the calculation."),
        (ans - 5, "careless_slip", "Made a slip in the calculation."),
    ], steps, {"p": p, "kind": kind}, pc, auto_slips=False)


@checker(compare_more_less)
def _(q):
    base = 100
    other = base + q["p"] if q["kind"] == "more" else base - q["p"]
    diff = abs(other - base)
    return F(diff * 100, other)


@template(T, "basic", EXPR)
def percent_shaded_figure(r):
    """math-pat-percent-shaded-figure"""
    rows, cols = r.choice([(4, 5), (5, 5), (5, 8), (5, 10), (2, 10)])
    total = rows * cols
    k = r.randint(3, total - 3)
    if (F(k * 100, total) * 2).denominator != 1:
        return None
    ask_un = r.random() < 0.5
    cells = list(range(total))
    r.shuffle(cells)
    shaded = set(cells[:k])
    cs = min(26, 300 // cols)
    f = Fig(cols * cs + 16, rows * cs + 16)
    for i in range(total):
        f.rect(8 + (i % cols) * cs, 8 + (i // cols) * cs, cs, cs, shade=0.35 if i in shaded else 0.0, width=1.2)
    fig = f.svg(f"Grid of {total} equal squares with some shaded")
    what = "not shaded" if ask_un else "shaded"
    ask = total - k if ask_un else k
    other = k if ask_un else total - k
    ans = F(ask * 100, total)
    stem = f"The figure is made up of {total} equal squares. What percentage of the figure is {what}?"
    return build(percent_shaded_figure, stem, ans, [
        (F(other * 100, total), "gave_the_other_part", f"Gave the percentage that is {'shaded' if ask_un else 'not shaded'}."),
        (ask, "gave_the_count", "Gave the number of squares as a percentage."),
        (other, "gave_the_other_count", "Gave the number of the other squares as a percentage."),
        (ans + 10, "careless_slip", "Made a slip in the calculation."),
        (ans - 5, "careless_slip", "Made a slip in the calculation."),
        (F(total * 100, ask), "reversed_the_fraction", "Divided the total by the part."),
    ], [f"Squares {what} = {ask} out of {total}", f"{ask}/{total} × 100% = {pc(ans)}"],
        {"ask": ask, "total": total}, pc, auto_slips=False, figure=fig)


@checker(percent_shaded_figure)
def _(q):
    return next(F(h, 2) for h in range(1, 201) if F(h, 2) * q["total"] == 100 * q["ask"])


@template(T, "intermediate", DISC)
def interest_deposit(r):
    """math-pat-interest-deposit"""
    P = 1000 * r.randint(2, 20)
    rate = F(r.choice([3, 4, 5, 6, 7, 8]), 2)
    yrs = r.randint(2, 6)
    interest = P * rate * yrs / 100
    if interest.denominator != 1:
        return None
    ans = P + interest
    n = r.choice(NAMES)
    stem = (f"{n} put ${P} in a bank that pays simple interest of {float(rate):g}% per year. "
            f"How much money will {n} have in the bank after {yrs} years?")
    comp = r2(F(P) * (1 + rate / 100) ** yrs)
    return build(interest_deposit, stem, ans, [
        (interest, "forgot_the_deposit", "Gave the interest only."),
        (P + P * rate / 100, "interest_for_one_year_only", "Added one year of interest only."),
        (comp, "used_compound_interest", "Added interest on the interest each year."),
        (ans + 100, "careless_slip", "Made a slip in the calculation."),
        (ans - 100, "careless_slip", "Made a slip in the calculation."),
    ], [f"Interest for 1 year = {float(rate):g}% of ${P} = {money(P * rate / 100)}", f"Interest for {yrs} years = {money(interest)}",
        f"Total = ${P} + {money(interest)} = {money(ans)}"], {"P": P, "r2": int(rate * 2), "yrs": yrs}, money, auto_slips=False)


@checker(interest_deposit)
def _(q):
    bal = F(q["P"])
    for _ in range(q["yrs"]):
        bal += F(q["P"] * q["r2"], 200)
    return bal
