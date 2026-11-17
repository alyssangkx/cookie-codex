"""Rate (math-rate): generators for basic, intermediate and competent levels.

Speed is not in the 2021 syllabus, so every question here is about a rate of work, flow, price or pay.
"""
from common import *

T = "math-rate"
O = "math-rate-rate-"
PER, FIND = O + "01", O + "02"


def brute(pred, hi=20000):
    return next((F(n) for n in range(1, hi + 1) if pred(n)), None)


def slip(v, d):
    return [(v + d, "careless_slip", "Made a slip in the calculation."),
            (v - d, "careless_slip", "Made a slip in the calculation.")]


# ---------------------------------------------------------------- basic

FLOWS = [(lambda tot, t: f"A tap fills {plural(tot, 'litre')} of water in {plural(t, 'minute')}", "litres per minute", "litres"),
         (lambda tot, t: f"A machine packs {plural(tot, 'box', 'boxes')} in {plural(t, 'minute')}", "boxes per minute", "boxes"),
         (lambda tot, t: f"A printer prints {plural(tot, 'page')} in {plural(t, 'minute')}", "pages per minute", "pages"),
         (lambda tot, t: f"A baker makes {plural(tot, 'bun')} in {plural(t, 'hour')}", "buns per hour", "buns"),
         (lambda tot, t: f"A factory makes {plural(tot, 'toy')} in {plural(t, 'hour')}", "toys per hour", "toys"),
         (lambda tot, t: f"A pump removes {plural(tot, 'litre')} of water in {plural(t, 'minute')}", "litres per minute", "litres")]


@template(T, "basic", PER)
def rate_per_unit(r):
    rate = r.randint(2, 40)
    t = r.randint(3, 15)
    tot = rate * t
    stem0, unit_, _ = r.choice(FLOWS)
    stem = f"{stem0(tot, t)}. How many {unit_} is that?"
    return build(rate_per_unit, stem, rate, [
        (tot * t, "multiplied_instead_of_divided", f"Multiplied {tot} by {t}."),
        (F(t, tot) if False else tot - t, "subtracted", f"Subtracted {t} from {tot}."),
        (tot + t, "added", f"Added {tot} and {t}."),
        *slip(rate, 1), *slip(rate, 2),
    ], [f"Rate = total ÷ time = {tot} ÷ {t} = {rate}"], {"tot": tot, "t": t}, lambda x: f"{x} {unit_}",
        auto_slips=False, whole=True)


@checker(rate_per_unit)
def _(q):
    return brute(lambda x: x * q["t"] == q["tot"])


@template(T, "basic", FIND)
def total_from_rate(r):
    """math-pat-unitary-rate-basic"""
    rate = r.randint(2, 30)
    t0 = r.randint(2, 9)
    t = r.choice([x for x in range(5, 60, 5) if x != t0])
    thing, per = r.choice([("cups", "minutes"), ("biscuits", "minutes"), ("leaflets", "minutes"), ("bolts", "minutes"),
                           ("parcels", "hours"), ("shirts", "hours")])
    tot0, ans = rate * t0, rate * t
    stem = f"A machine makes {tot0} {thing} in {t0} {per}. At this rate, how many {thing} will it make in {t} {per}?"
    return build(total_from_rate, stem, ans, [
        (tot0 * t, "multiplied_the_givens", f"Multiplied {tot0} by {t}."),
        (F(tot0 * t0, t) if (tot0 * t0) % t == 0 else None, "divided_by_the_new_time", "Divided by the new time instead of multiplying."),
        (F(t, t0) * (tot0 if False else 1) if False else tot0 + (t - t0), "added_the_difference_in_time", f"Added {t - t0} to {tot0}."),
        *slip(ans, rate), *slip(ans, 10),
    ], [f"Rate = {tot0} ÷ {t0} = {rate} per {per[:-1]}", f"{t} {per} → {rate} × {t} = {ans}"],
        {"tot0": tot0, "t0": t0, "t": t}, unit(thing), auto_slips=False, whole=True)


@checker(total_from_rate)
def _(q):
    # scale by the time ratio with exact fractions
    return F(q["tot0"]) * F(q["t"], q["t0"])


@template(T, "basic", FIND)
def time_from_rate(r):
    rate = r.randint(3, 25)
    t = r.randint(4, 24)
    tot = rate * t
    ctx = r.choice([
        (f"A tap flows at {plural(rate, 'litre')} per minute. How many minutes does it take to fill a pail that holds {plural(tot, 'litre')}?", "min"),
        (f"A printer prints {plural(rate, 'page')} per minute. How many minutes does it take to print {plural(tot, 'page')}?", "min"),
        (f"A worker packs {rate} boxes per hour. How many hours does it take to pack {tot} boxes?", "h"),
    ])
    return build(time_from_rate, ctx[0], t, [
        (tot * rate, "multiplied_instead_of_divided", f"Multiplied {tot} by {rate}."),
        (tot - rate, "subtracted", f"Subtracted {rate} from {tot}."),
        (F(rate * 100, tot) if False else rate + t + 1 if False else tot + rate, "added", f"Added {tot} and {rate}."),
        *slip(t, 1), *slip(t, 2),
    ], [f"Time = total ÷ rate = {tot} ÷ {rate} = {t}"], {"tot": tot, "rate": rate}, unit(ctx[1]),
        auto_slips=False, whole=True)


@checker(time_from_rate)
def _(q):
    done, t = 0, 0
    while done < q["tot"]:
        done += q["rate"]
        t += 1
    return F(t)


@template(T, "basic", PER)
def price_per_unit(r):
    rate = F(r.randint(2, 40), 2)  # $1 to $20 in 50-cent steps
    k = r.randint(3, 9)
    cost = rate * k
    thing = r.choice([("kg of rice", "kg"), ("kg of apples", "kg"), ("metres of ribbon", "m"), ("litres of milk", "L"),
                      ("kg of chicken", "kg")])
    stem = f"{k} {thing[0]} cost {money(cost)}. What is the cost of 1 {thing[1]}?"
    return build(price_per_unit, stem, rate, [
        (cost * k, "multiplied_instead_of_divided", f"Multiplied {money(cost)} by {k}."),
        (cost - k, "subtracted", f"Subtracted {k} from the cost."),
        (cost + k, "added", f"Added {k} to the cost."),
        (rate + F(1, 2), "careless_slip", "Made a slip in the calculation."),
        (rate - F(1, 2), "careless_slip", "Made a slip in the calculation."),
    ], [f"Cost of 1 {thing[1]} = {money(cost)} ÷ {k} = {money(rate)}"], {"cost2": int(cost * 2), "k": k}, money,
        auto_slips=False)


@checker(price_per_unit)
def _(q):
    return next(F(c, 100) for c in range(1, 100000) if c * q["k"] == q["cost2"] * 50)


@template(T, "basic", FIND)
def pay_from_rate(r):
    rate = r.randint(8, 25)
    h = r.randint(3, 12)
    n = r.choice(NAMES)
    ans = rate * h
    stem = f"{n} earns ${rate} per hour at a part-time job. How much does {n} earn in {plural(h, 'hour')}?"
    return build(pay_from_rate, stem, ans, [
        (F(rate, h) if False else rate + h, "added", f"Added {rate} and {h}."),
        (F(ans, 2) if ans % 2 == 0 else rate * (h - 1), "halved_or_missed_an_hour", "Made a slip with the number of hours."),
        (rate * (h + 1), "extra_hour", "Counted one hour too many."),
        (ans + 10, "careless_slip", "Made a slip in the calculation."),
        (ans - 10, "careless_slip", "Made a slip in the calculation."),
    ], [f"Amount earned = ${rate} × {h} = ${ans}"], {"rate": rate, "h": h}, money, auto_slips=False, whole=True)


@checker(pay_from_rate)
def _(q):
    return F(sum(q["rate"] for _ in range(q["h"])))


# ---------------------------------------------------------------- intermediate

@template(T, "intermediate", FIND)
def tank_litres_time(r):
    a, b, c = r.choice([20, 25, 40, 50, 60, 80, 100]), r.choice([20, 25, 40, 50, 60]), r.choice([20, 25, 40, 50])
    vol = a * b * c
    if vol % 1000:
        return None
    L = vol // 1000
    rate = r.choice([x for x in range(2, 26) if L % x == 0 and 4 <= L // x <= 60] or [0])
    if rate == 0:
        return None
    t = L // rate
    thing = r.choice(["rectangular fish tank", "water tank", "rectangular container"])
    stem = (f"An empty {thing} is {a} cm long, {b} cm wide and {c} cm high. A tap fills it at {plural(rate, 'litre')} per minute. "
            f"How many minutes does it take to fill the {thing} completely? (1 litre = 1000 cm³)")
    return build(tank_litres_time, stem, t, [
        (F(vol, rate), "forgot_to_convert_to_litres", "Used the volume in cm³ without changing it to litres."),
        (L * rate, "multiplied_instead_of_divided", "Multiplied the capacity by the rate."),
        (F(vol, 100 * rate) if vol % (100 * rate) == 0 else None, "wrong_conversion", "Used 1 litre = 100 cm³."),
        (t + 1, "careless_slip", "Made a slip in the calculation."),
        (t - 1, "careless_slip", "Made a slip in the calculation."),
        (t * 2, "doubled", "Made a slip with the capacity."),
    ], [f"Volume = {a} × {b} × {c} = {vol} cm³ = {plural(L, 'litre')}", f"Time = {L} ÷ {rate} = {plural(t, 'minute')}"],
        {"a": a, "b": b, "c": c, "rate": rate}, unit("minutes"), whole=True, auto_slips=False)


@checker(tank_litres_time)
def _(q):
    litres = F(q["a"] * q["b"] * q["c"], 1000)
    water, t = 0, 0
    while water < litres:
        water += q["rate"]
        t += 1
    return F(t)


@template(T, "intermediate", PER)
def rate_compare_difference(r):
    ra, rb = r.sample(range(4, 30), 2)
    ta, tb = r.randint(3, 12), r.randint(3, 12)
    if ta == tb:
        return None
    A, B = ra * ta, rb * tb
    x, y = two_names(r)
    thing = r.choice([("words", "typed"), ("sums", "solved"), ("bookmarks", "made")])
    stem = (f"{x} {thing[1]} {A} {thing[0]} in {plural(ta, 'minute')}. {y} {thing[1]} {B} {thing[0]} in {plural(tb, 'minute')}. "
            f"How many more {thing[0]} per minute did the faster person manage than the other person?")
    ans = abs(ra - rb)
    return build(rate_compare_difference, stem, ans, [
        (abs(A - B), "compared_totals", "Compared the totals and ignored the different times."),
        (F(abs(A - B), abs(ta - tb)), "divided_differences", "Divided the difference in totals by the difference in times."),
        (ra + rb, "added_the_rates", "Added the two rates."),
        (ans + 1, "careless_slip", "Made a slip in the calculation."),
        (ans + 2, "careless_slip", "Made a slip in the calculation."),
        (max(ra, rb), "gave_the_faster_rate", "Gave the faster rate itself."),
    ], [f"{x}: {A} ÷ {ta} = {ra} per minute", f"{y}: {B} ÷ {tb} = {rb} per minute", f"Difference = {ans}"],
        {"A": A, "ta": ta, "B": B, "tb": tb}, unit(f"{thing[0]}"), whole=True, auto_slips=False)


@checker(rate_compare_difference)
def _(q):
    a = brute(lambda x: x * q["ta"] == q["A"])
    b = brute(lambda x: x * q["tb"] == q["B"])
    return abs(a - b)


@template(T, "intermediate", FIND)
def combined_taps_time(r):
    ra, rb = r.sample(range(3, 30), 2)
    t = r.randint(4, 20)
    V = (ra + rb) * t
    stem = (f"Tap A fills a tub at {plural(ra, 'litre')} per minute and Tap B fills it at {plural(rb, 'litre')} per minute. "
            f"How many minutes do the two taps take to fill an empty tub of {plural(V, 'litre')} when both are turned on together?")
    return build(combined_taps_time, stem, t, [
        (F(V, ra) if V % ra == 0 else None, "used_one_tap_only", "Used Tap A only."),
        (F(V, abs(ra - rb)) if V % abs(ra - rb) == 0 else None, "subtracted_the_rates", "Subtracted the rates."),
        (F(V, rb) if V % rb == 0 else None, "used_the_other_tap_only", "Used Tap B only."),
        (t + 1, "careless_slip", "Made a slip in the calculation."),
        (t - 1, "careless_slip", "Made a slip in the calculation."),
        (t + 2, "careless_slip", "Made a slip in the calculation."),
    ], [f"Together: {ra} + {rb} = {plural(ra + rb, 'litre')} per minute", f"Time = {V} ÷ {ra + rb} = {plural(t, 'minute')}"],
        {"ra": ra, "rb": rb, "V": V}, unit("minutes"), whole=True, auto_slips=False)


@checker(combined_taps_time)
def _(q):
    water, t = 0, 0
    while water < q["V"]:
        water += q["ra"] + q["rb"]
        t += 1
    return F(t)


@template(T, "intermediate", FIND)
def printing_cost(r):
    rate = r.choice([20, 25, 30, 40, 50])
    pages = r.choice([300, 400, 500])
    reams = r.randint(2, 6)
    P = pages * reams
    cost = r.randint(4, 12)
    mins = P // rate if P % rate == 0 else None
    if mins is None:
        return None
    n = r.choice(NAMES)
    stem = (f"{n}'s printer prints {plural(rate, 'page')} per minute. A pack of {pages} sheets of paper costs ${cost}. "
            f"How much does the paper cost to print for {plural(mins, 'minute')} (assume one page per sheet)?")
    ans = reams * cost
    return build(printing_cost, stem, ans, [
        (P * cost, "multiplied_pages_by_price", "Multiplied the number of pages by the price of a pack."),
        (mins * cost, "multiplied_minutes_by_price", "Multiplied the minutes by the price of a pack."),
        (cost * (reams + 1), "extra_pack", "Counted one pack too many."),
        (ans + 2, "careless_slip", "Made a slip in the calculation."),
        (ans - 2, "careless_slip", "Made a slip in the calculation."),
    ], [f"Pages printed = {rate} × {mins} = {P}", f"Packs needed = {P} ÷ {pages} = {reams}", f"Cost = {reams} × ${cost} = ${ans}"],
        {"rate": rate, "pages": pages, "mins": mins, "cost": cost}, money, whole=True, auto_slips=False)


@checker(printing_cost)
def _(q):
    printed, packs = 0, 0
    for _ in range(q["mins"]):
        printed += q["rate"]
    while packs * q["pages"] < printed:
        packs += 1
    return F(packs * q["cost"])


@template(T, "intermediate", PER)
def rate_unit_change(r):
    per_min = r.choice([F(1, 2), F(1, 4), F(3, 2), 2, 3, F(5, 2)])
    h = r.randint(2, 6)
    ans = F(per_min) * 60 * h
    thing = r.choice([("A leaking tap loses", "litres of water"), ("A machine uses", "litres of oil"),
                      ("A fountain sprays", "litres of water")])
    ps = f"{float(per_min):g}"
    stem = f"{thing[0]} {plural(ps, 'litre')} per minute. How many {thing[1]} is that in {plural(h, 'hour')}?"
    return build(rate_unit_change, stem, ans, [
        (per_min * h, "forgot_to_change_hours_to_minutes", "Used the number of hours as minutes."),
        (F(per_min) * 100 * h, "used_100_minutes_in_an_hour", "Used 100 minutes in an hour."),
        (F(per_min) * 24 * h if False else F(per_min) * 30 * h, "used_30_minutes_in_an_hour", "Used 30 minutes in an hour."),
        (ans + 10, "careless_slip", "Made a slip in the calculation."),
        (ans - 10, "careless_slip", "Made a slip in the calculation."),
        (F(per_min) * 60 * (h + 1), "extra_hour", "Counted one hour too many."),
    ], [f"{plural(h, 'hour')} = {plural(h * 60, 'minute')}", f"{ps} × {h * 60} = {float(ans):g} litres"],
        {"p2": int(per_min * 4), "h": h}, lambda x: f"{float(x):g} {noun(float(f'{float(x):g}'), 'litre')}", auto_slips=False)


@checker(rate_unit_change)
def _(q):
    return sum(F(q["p2"], 4) for _ in range(q["h"] * 60))


@template(T, "intermediate", FIND)
def time_to_fill_rest(r):
    rate = r.randint(3, 20)
    t = r.randint(4, 20)
    C = r.randint(100, 400)
    s = C - rate * t
    if s < 10:
        return None
    thing = r.choice(["pool", "water tank", "drum"])
    stem = (f"{a_an(thing).capitalize()} {thing} holds {plural(C, 'litre')} when full. It now has {plural(s, 'litre')} of water. "
            f"A tap fills it at {plural(rate, 'litre')} per minute. How many more minutes will it take to fill the {thing}?")
    return build(time_to_fill_rest, stem, t, [
        (F(C, rate) if C % rate == 0 else None, "forgot_water_already_in", "Ignored the water already in the container."),
        (F(s, rate) if s % rate == 0 else None, "used_the_water_already_in", "Divided the water already there by the rate."),
        (t + 1, "careless_slip", "Made a slip in the calculation."),
        (t - 1, "careless_slip", "Made a slip in the calculation."),
        (F(C + s, rate) if (C + s) % rate == 0 else None, "added_instead_of_subtracted", "Added the water already in."),
        (t + 2, "careless_slip", "Made a slip in the calculation."),
    ], [f"Water needed = {C} − {s} = {plural(C - s, 'litre')}", f"Time = {C - s} ÷ {rate} = {plural(t, 'minute')}"],
        {"C": C, "s": s, "rate": rate}, unit("minutes"), whole=True, auto_slips=False)


@checker(time_to_fill_rest)
def _(q):
    w, t = q["s"], 0
    while w < q["C"]:
        w += q["rate"]
        t += 1
    return F(t)


# ---------------------------------------------------------------- competent

@template(T, "competent", FIND)
def tank_fill_drain(r):
    """math-pat-tank-fill-drain-net-rate"""
    a, b, c = r.choice([40, 50, 60, 80, 100]), r.choice([40, 50, 60, 80]), r.choice([25, 40, 50])
    if (a * b * c) % 1000:
        return None
    L = a * b * c // 1000
    fr = r.choice([(1, 4), (1, 2), (3, 4), (1, 5), (2, 5)])
    start = F(L * fr[0], fr[1])
    if start.denominator != 1:
        return None
    fill = r.randint(6, 20)
    drain = r.randint(1, fill - 2)
    t = r.randint(4, 15)
    V = start + (fill - drain) * t
    if V > L:
        return None
    stem = (f"A tank {a} cm by {b} cm by {c} cm was {fr[0]}/{fr[1]} full of water. A tap running at {plural(fill, 'litre')} per minute "
            f"filled it while a drain emptied it at the same time. After {plural(t, 'minute')} there were {plural(int(V), 'litre')} of water in the tank. "
            f"What was the rate of the drain in litres per minute? (1 litre = 1000 cm³)")
    net = (V - start) / t
    return build(tank_fill_drain, stem, drain, [
        (net, "gave_the_net_rate", "Gave the net rate at which the tank filled."),
        (fill + net, "added_instead_of_subtracted", "Added the net rate to the tap's rate."),
        (F(L - start, t) if (L - start) % t == 0 else None, "used_the_capacity_not_the_final_volume", "Used the capacity as the volume after the time."),
        (drain + 1, "careless_slip", "Made a slip in the calculation."),
        (drain + 2, "careless_slip", "Made a slip in the calculation."),
        (F(V, t) if V % t == 0 else None, "forgot_the_starting_volume", "Forgot the water already in the tank."),
    ], [f"Capacity = {a} × {b} × {c} ÷ 1000 = {plural(L, 'litre')}", f"Water at first = {fr[0]}/{fr[1]} × {L} = {plural(int(start), 'litre')}",
        f"Net gain = {int(V)} − {int(start)} = {plural(int(V - start), 'litre')} in {t} min = {plural(net, 'litre')} per minute",
        f"Drain = {fill} − {net} = {plural(drain, 'litre')} per minute"],
        {"a": a, "b": b, "c": c, "fr": list(fr), "fill": fill, "t": t, "V": int(V)}, unit("litres per minute"),
        whole=True, auto_slips=False)


@checker(tank_fill_drain)
def _(q):
    L = F(q["a"] * q["b"] * q["c"], 1000)
    start = L * F(*q["fr"])
    for d in range(1, q["fill"]):
        v = start
        for _ in range(q["t"]):
            v += q["fill"] - d
        if v == q["V"]:
            return F(d)


@template(T, "competent", FIND)
def two_machines(r):
    """math-pat-two-machines-rate-work"""
    tA = r.choice([20, 24, 30, 36, 40, 45, 60])
    tB = r.choice([x for x in (30, 40, 45, 48, 60, 72, 90, 120) if x > tA])
    D = r.randint(2, 12)
    g = gcd(tA, tB)
    u, v = tB // g, tA // g  # rate A : rate B = tB : tA
    if u - v < 1:
        return None
    rb = D * v // (u - v) if (D * v) % (u - v) == 0 else None
    if rb is None:
        return None
    ra = rb + D
    if ra * tA != rb * tB:
        return None
    job = ra * tA
    together = F(job, ra + rb)
    if together.denominator != 1:
        return None
    ask = r.choice(["time", "size"])
    name1, name2 = r.choice([("Pump A", "Pump B"), ("Machine A", "Machine B")])
    what = "tank" if "Pump" in name1 else "job"
    tail = ("how many litres of water does the tank hold?" if ask == "size" else "how many minutes do they take to fill the tank?") \
        if what == "tank" else ("how many items are in the job?" if ask == "size" else "how many minutes do they take together?")
    verb = "fills a tank" if what == "tank" else "completes a job"
    stem = (f"{name1} {verb} in {plural(tA, 'minute')} and {name2} {'fills the same tank' if what == 'tank' else 'completes the same job'} in {plural(tB, 'minute')}. "
            f"{name1} works {D} {'litres' if what == 'tank' else 'items'} per minute faster than {name2}. "
            f"If both work together, {tail}" if ask == "time" else
            f"{name1} {verb} in {plural(tA, 'minute')} and {name2} {'fills the same tank' if what == 'tank' else 'completes the same job'} in {plural(tB, 'minute')}. "
            f"{name1} works {D} {'litres' if what == 'tank' else 'items'} per minute faster than {name2}. {tail[0].upper() + tail[1:]}")
    if ask == "time":
        ans = int(together)
        wrong = [((tA + tB) // 2, "averaged_the_times", f"Averaged {tA} and {tB}."),
                 (tA + tB, "added_the_times", f"Added {tA} and {tB}."),
                 (F(job, ra) , "used_the_faster_machine_only", "Used the faster one only."),
                 (ans + 2, "careless_slip", "Made a slip in the calculation."),
                 (ans - 2, "careless_slip", "Made a slip in the calculation."),
                 (F(job, rb), "used_the_slower_machine_only", "Used the slower one only.")]
        steps = [f"Rates are in the ratio {tB} : {tA} = {u} : {v}", f"{u - v} unit(s) = {D}, so rate B = {rb} and rate A = {ra} per minute",
                 f"Job = {ra} × {tA} = {job}", f"Time together = {job} ÷ {ra + rb} = {plural(ans, 'minute')}"]
        sh = unit("minutes")
    else:
        ans = job
        wrong = [(rb * tA, "used_wrong_rate", "Multiplied the slower rate by the faster time."),
                 (D * tA, "used_the_difference", "Multiplied the difference in rates by the time."),
                 (ra * tB, "used_wrong_time", "Multiplied the faster rate by the slower time."),
                 (ans + 10, "careless_slip", "Made a slip in the calculation."),
                 (ans - 10, "careless_slip", "Made a slip in the calculation."),
                 ((ra + rb) * tA, "added_rates_before_multiplying", "Used the combined rate with one time.")]
        steps = [f"Rates are in the ratio {tB} : {tA} = {u} : {v}", f"{u - v} unit(s) = {D}, so rate B = {rb} and rate A = {ra} per minute",
                 f"Job = {ra} × {tA} = {job}"]
        sh = unit("litres" if what == "tank" else "items")
    return build(two_machines, stem, ans, wrong, steps, {"tA": tA, "tB": tB, "D": D, "ask": ask}, sh,
                 whole=True, auto_slips=False)


@checker(two_machines)
def _(q):
    rb = next(x for x in range(1, 5000) if (x + q["D"]) * q["tA"] == x * q["tB"])
    ra = rb + q["D"]
    job = ra * q["tA"]
    return F(job) if q["ask"] == "size" else F(job, ra + rb)


@template(T, "competent", FIND)
def relay_taps(r):
    ra = r.randint(3, 20)
    rb = r.randint(2, 20)
    t1 = r.randint(2, 12)
    t2 = r.randint(2, 12)
    V = ra * t1 * 2
    if V % 2 or (V // 2) % (ra + rb):
        return None
    t2 = V // 2 // (ra + rb)
    ans = t1 + t2
    stem = (f"Tap A fills a tank at {plural(ra, 'litre')} per minute. It runs alone until the tank is half full. "
            f"Tap B, which fills at {plural(rb, 'litre')} per minute, is then turned on as well. "
            f"The tank holds {plural(V, 'litre')}. How many minutes does it take to fill the tank from empty?")
    return build(relay_taps, stem, ans, [
        (F(V, ra + rb), "used_both_taps_all_the_time", "Used both taps from the start."),
        (F(V, ra) if V % ra == 0 else None, "used_tap_a_all_the_time", "Used Tap A for the whole job."),
        (t1 + 1, "careless_slip", "Made a slip in the calculation."),
        (ans + 2, "careless_slip", "Made a slip in the calculation."),
        (ans - 1, "careless_slip", "Made a slip in the calculation."),
        (t2 * 2 if t2 * 2 != ans else None, "doubled_the_second_stage", "Found the second stage and doubled it."),
    ], [f"Half the tank = {plural(V // 2, 'litre')}", f"Tap A alone: {V // 2} ÷ {ra} = {plural(t1, 'minute')}",
        f"Both taps: {V // 2} ÷ {ra + rb} = {plural(t2, 'minute')}", f"Total = {t1} + {t2} = {plural(ans, 'minute')}"],
        {"ra": ra, "rb": rb, "V": V}, unit("minutes"), whole=True, auto_slips=False)


@checker(relay_taps)
def _(q):
    w, t = 0, 0
    while w < q["V"] // 2:
        w += q["ra"]
        t += 1
    while w < q["V"]:
        w += q["ra"] + q["rb"]
        t += 1
    return F(t)


@template(T, "competent", FIND)
def leaking_tank(r):
    F_ = r.randint(8, 25)
    leak = r.randint(1, F_ - 3)
    t = r.randint(5, 25)
    s = r.randint(5, 60)
    C = s + (F_ - leak) * t
    stem = (f"A tank holds {plural(C, 'litre')} when full and now has {plural(s, 'litre')}. A tap fills it at {plural(F_, 'litre')} per minute, "
            f"but a crack in the tank lets out {plural(leak, 'litre')} per minute. How many minutes will it take for the tank to be full?")
    return build(leaking_tank, stem, t, [
        (F(C - s, F_) if (C - s) % F_ == 0 else None, "ignored_the_leak", "Ignored the leak."),
        (F(C - s, F_ + leak) if (C - s) % (F_ + leak) == 0 else None, "added_the_leak", "Added the leak to the tap's rate."),
        (F(C, F_ - leak) if C % (F_ - leak) == 0 else None, "ignored_water_already_in", "Ignored the water already in the tank."),
        (t + 1, "careless_slip", "Made a slip in the calculation."),
        (t - 1, "careless_slip", "Made a slip in the calculation."),
        (t + 3, "careless_slip", "Made a slip in the calculation."),
    ], [f"Net rate = {F_} − {leak} = {plural(F_ - leak, 'litre')} per minute", f"Water needed = {C} − {s} = {plural(C - s, 'litre')}",
        f"Time = {C - s} ÷ {F_ - leak} = {plural(t, 'minute')}"], {"C": C, "s": s, "F": F_, "leak": leak}, unit("minutes"),
        whole=True, auto_slips=False)


@checker(leaking_tank)
def _(q):
    w, t = q["s"], 0
    while w < q["C"]:
        w += q["F"] - q["leak"]
        t += 1
    return F(t)


@template(T, "competent", FIND, PER)
def rate_ratio_share(r):
    u, v = r.sample(range(1, 7), 2)
    if gcd(u, v) != 1 or u < v:
        return None
    t = r.randint(3, 12)
    per = r.randint(2, 8)
    T_ = (u + v) * per * t
    t2 = r.randint(2, 15)
    ans = u * per * t2
    thing = r.choice(["pages", "leaflets", "cards"])
    x, y = two_names(r)
    stem = (f"Machine A prints {plural(u, 'page')} for every {plural(v, 'page')} that Machine B prints. Together they print {T_} {thing} in {plural(t, 'minute')}. "
            f"How many {thing} does Machine A print in {plural(t2, 'minute')}?")
    return build(rate_ratio_share, stem, ans, [
        (v * per * t2, "used_machine_b", "Found Machine B's pages."),
        (F(T_ * u, u + v) if (T_ * u) % (u + v) == 0 else None, "forgot_to_scale_the_time", f"Found A's share of the {t}-minute total, not {plural(t2, 'minute')}."),
        (F(T_ * t2, t) if (T_ * t2) % t == 0 else None, "gave_the_total_for_both", "Gave the pages printed by both machines."),
        (ans + per, "careless_slip", "Made a slip in the calculation."),
        (ans - per, "careless_slip", "Made a slip in the calculation."),
    ], [f"Together: {T_} ÷ {t} = {T_ // t} per minute", f"{plural(u + v, 'unit')} = {T_ // t}, so 1 unit = {per} per minute",
        f"Machine A: {u} × {per} = {u * per} per minute", f"In {plural(t2, 'minute')}: {u * per} × {t2} = {ans}"],
        {"u": u, "v": v, "T": T_, "t": t, "t2": t2}, unit(thing), whole=True, auto_slips=False)


@checker(rate_ratio_share)
def _(q):
    both = F(q["T"], q["t"])
    a = both * F(q["u"], q["u"] + q["v"])
    return a * q["t2"]


@template(T, "competent", FIND)
def two_stage_rate(r):
    a = r.randint(4, 15)
    b = r.randint(a + 2, a + 12)
    t1 = r.randint(3, 12)
    t2 = r.randint(3, 15)
    C = a * t1 + b * t2
    stem = (f"A pump fills an empty tank at {plural(a, 'litre')} per minute for the first {plural(t1, 'minute')}. It is then set to a faster rate "
            f"of {plural(b, 'litre')} per minute until the tank, which holds {plural(C, 'litre')}, is full. "
            f"How many minutes does it take to fill the tank altogether?")
    ans = t1 + t2
    return build(two_stage_rate, stem, ans, [
        (t2, "gave_second_stage_only", "Gave the time at the faster rate only."),
        (F(C, b) if C % b == 0 else None, "used_the_faster_rate_throughout", "Used the faster rate for the whole time."),
        (F(C, a) if C % a == 0 else None, "used_the_slower_rate_throughout", "Used the slower rate for the whole time."),
        (ans + 1, "careless_slip", "Made a slip in the calculation."),
        (ans - 1, "careless_slip", "Made a slip in the calculation."),
        (ans + 2, "careless_slip", "Made a slip in the calculation."),
    ], [f"First stage: {a} × {t1} = {plural(a * t1, 'litre')}", f"Left to fill = {C} − {a * t1} = {plural(C - a * t1, 'litre')}",
        f"Second stage: {C - a * t1} ÷ {b} = {plural(t2, 'minute')}", f"Total = {t1} + {t2} = {plural(ans, 'minute')}"],
        {"a": a, "b": b, "t1": t1, "C": C}, unit("minutes"), whole=True, auto_slips=False)


@checker(two_stage_rate)
def _(q):
    w, t = 0, 0
    for _ in range(q["t1"]):
        w += q["a"]
        t += 1
    while w < q["C"]:
        w += q["b"]
        t += 1
    return F(t)
