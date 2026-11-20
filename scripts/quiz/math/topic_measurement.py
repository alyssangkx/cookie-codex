"""Measurement (math-measurement): length/mass/volume and time, at basic, intermediate and competent levels."""
import re
from decimal import Decimal

from common import *
from figures_C import beaker_svg, clock_svg, num, ruler_svg, two_clocks_svg

T = "math-measurement"
LM = "math-measurement-length-mass-and-volume-"
LM_RULER, LM_UNITS, LM_ORDER, LM_ML, LM_COMPOUND, LM_CONVERT = (LM + f"0{i}" for i in (1, 4, 5, 6, 7, 8))
TM = "math-measurement-time-"
TM_5, TM_MIN, TM_HM, TM_SEC, TM_FIND, TM_24 = (TM + f"0{i}" for i in range(1, 7))

SYS = [("km", "m", 1000), ("m", "cm", 100), ("kg", "g", 1000), ("l", "ml", 1000)]
PLACES = ["classroom", "school hall", "library", "canteen", "science lab", "sports hall", "music room",
          "art room", "reading corner", "staff room", "bus interchange", "community centre"]


def cc(q, r):
    """Compound measure code: q big units and r small units (r may be un-normalised)."""
    return q * 100000 + r


def cshow(u1, u2):
    def f(c):
        q, r = divmod(int(c), 100000)
        if q and r:
            return f"{q} {u1} {r} {u2}"
        return f"{q} {u1}" if q else f"{r} {u2}"
    return f


def usd(u):
    return lambda v: f"{num(v)} {u}"


def fmt12(v):
    v = int(v)
    h24, m = divmod(v, 60)
    return f"{h24 % 12 or 12}:{m:02d} {'am' if h24 < 12 else 'pm'}"


def fmt24(v):
    h, m = divmod(int(v), 60)
    return f"{h:02d}{m:02d} h"


def fmtclk(v):
    h, m = divmod(int(v), 60)
    return f"{h}:{m:02d}"


def day(v):
    v = int(v) % 1440
    return v or None


def nm(r):
    return r.choice(NAMES)


# ================================================================ length, mass and volume: basic

@template(T, "basic", LM_RULER)
def ruler_length(r):
    """math-pat-order-mixed-units reading a ruler"""
    name = nm(r)
    obj = r.choice(["pencil", "strip of paper", "ribbon", "eraser", "matchstick", "feather", "leaf", "straw"])
    start = r.choice([0, 0, 1, 2, 3, 4])
    ln = r.randint(3, 11)
    end = start + ln
    if end > 15:
        return None
    stem = f"{name} places {a_an(obj)} {obj} along a ruler as shown. What is the length of the {obj}?"
    return build(ruler_length, stem, ln, [
        (end, "read_only_the_right_end", "Read the right end of the object without subtracting the starting mark."),
        (ln + 1, "counted_marks_not_gaps", "Counted the marks instead of the centimetre gaps."),
        (ln - 1, "counted_gaps_off_by_one", "Counted one gap too few."),
        (start + ln + 1, "misread_scale", "Misread the end mark."),
    ], [f"Left end is at {start} cm and right end at {end} cm.", f"{end} - {start} = {ln} cm"],
        {"start": start, "end": end}, usd("cm"), whole=True, auto_slips=False, figure=ruler_svg(start, end))


@checker(ruler_length)
def _(p):
    return F(sum(1 for _ in range(p["start"], p["end"])))


@template(T, "basic", LM_CONVERT)
def convert_to_small(r):
    u1, u2, k = r.choice(SYS)
    a = r.randint(2, 19)
    b = r.randint(5, k - 5)
    if b % 5 or (k == 100 and b % 5 == 0 and b < 10):
        pass
    ans = a * k + b
    wk = k // 10
    concat = int(f"{a}{b}")
    stem = f"Express {a} {u1} {b} {u2} in {u2}."
    return build(convert_to_small, stem, ans, [
        (a * k, "forgot_the_small_part", f"Changed {a} {u1} to {u2} but left out the {b} {u2}."),
        (a * wk + b, "wrong_conversion_factor", f"Used 1 {u1} = {wk} {u2}."),
        (concat, "joined_the_numbers", f"Wrote {a} and {b} side by side."),
        (ans + wk, "slip_in_addition", "Made a slip in the addition."),
        (ans - wk, "slip_in_addition", "Made a slip in the addition."),
    ], [f"1 {u1} = {k} {u2}", f"{a} {u1} = {a * k} {u2}", f"{a * k} + {b} = {ans}"],
        {"a": a, "b": b, "k": k}, usd(u2), whole=True, auto_slips=False)


@checker(convert_to_small)
def _(p):
    a, b, k = p["a"], p["b"], p["k"]
    return F(next(n for n in range(1, 400000) if divmod(n, k) == (a, b)))


@template(T, "basic", LM_CONVERT, weight=2)
def convert_to_compound(r):
    u1, u2, k = r.choice(SYS)
    q = r.randint(2, 15)
    rem = r.randint(12, k - 3)
    N = q * k + rem
    wk = k // 10
    stem = f"Express {N} {u2} in {u1} and {u2}."
    sh = cshow(u1, u2)
    return build(convert_to_compound, stem, cc(q, rem), [
        (cc(N // wk, N % wk), "wrong_conversion_factor", f"Divided by {wk} instead of {k}."),
        (cc(q, rem // 10) if rem >= 10 else None, "dropped_a_digit", "Lost a digit in the small part."),
        (cc(q + 1, rem), "slip_in_big_unit", f"Made a slip in the number of {u1}."),
        (cc(rem // (k // 10) if False else q, rem + 10), "slip_in_small_unit", f"Made a slip in the {u2} part."),
    ], [f"1 {u1} = {k} {u2}", f"{N} ÷ {k} = {q} remainder {rem}", f"{N} {u2} = {q} {u1} {rem} {u2}"],
        {"N": N, "k": k}, sh, auto_slips=False)


@checker(convert_to_compound)
def _(p):
    N, k = p["N"], p["k"]
    q = next(q for q in range(0, 2000) if 0 <= N - q * k < k)
    return F(cc(q, N - q * k))


@template(T, "basic", LM_CONVERT, LM_COMPOUND, weight=2)
def convert_decimal(r):
    """math-pat-unit-conversion-compound"""
    u1, u2, k = r.choice(SYS)
    if r.random() < 0.5:
        a = r.randint(1, 12)
        b = r.choice([x for x in range(1, k) if x % (5 if k == 100 else 25) == 0 and x % 10])
        ans = F(a * k + b, k)
        stem = f"Express {a} {u1} {b} {u2} in {u1}."
        wrong = [(a + F(b, 10), "decimal_place_error", f"Treated {b} {u2} as {num(F(b, 10))} {u1}."),
                 (a + F(b, 10 * k), "decimal_place_error", "Put the decimal point one place too far."),
                 (F(a * k + b), "did_not_convert", f"Gave the answer in {u2}."),
                 (a + F(b, 1), "added_without_converting", f"Added {a} and {b} without converting.")]
        steps = [f"{b} {u2} = {num(F(b, k))} {u1}", f"{a} + {num(F(b, k))} = {num(ans)}"]
        params = {"mode": "a", "a": a, "b": b, "k": k}
        return build(convert_decimal, stem, ans, wrong, steps, params, usd(u1), whole=False, auto_slips=False)
    x = Decimal(r.randint(11, 199)) / Decimal(r.choice([10, 100]))
    if x == x.to_integral():
        return None
    xs = format(x.normalize(), "f")
    ans = F(x) * k
    if ans.denominator != 1:
        return None
    stem = f"Express {xs} {u1} in {u2}."
    return build(convert_decimal, stem, ans, [
        (F(x) * (k // 10), "wrong_conversion_factor", f"Multiplied by {k // 10}."),
        (F(x) * k * 10, "wrong_conversion_factor", f"Multiplied by {k * 10}."),
        (F(x) * (k // 100) if k // 100 else None, "wrong_conversion_factor", "Multiplied by too small a number."),
        (ans + k // 10, "slip_in_working", "Made a slip in the working."),
        (ans + 10, "slip_in_working", "Made a slip in the working."),
    ], [f"1 {u1} = {k} {u2}", f"{xs} × {k} = {ans}"], {"mode": "b", "x": xs, "k": k}, usd(u2), whole=True,
        auto_slips=False)


@checker(convert_decimal)
def _(p):
    if p["mode"] == "a":
        total = p["a"] * p["k"] + p["b"]
        return F(total, p["k"])
    return F(Decimal(p["x"]) * p["k"])


UNIT_BASE = {"km": 1000, "m": 1, "cm": F(1, 100), "kg": 1000, "g": 1, "l": 1000, "ml": 1}
MEAS = re.compile(r"([\d.]+)\s*(km|cm|m|kg|g|ml|l)\b")


def parse_meas(s):
    return sum(F(Decimal(n)) * UNIT_BASE[u] for n, u in MEAS.findall(s))


@template(T, "basic", LM_ORDER)
def order_measures(r):
    """math-pat-order-mixed-units"""
    u1, u2, k = r.choice(SYS)
    base = r.randint(2, 9) * k + r.randint(1, 9) * (k // 10)
    vals = sorted(r.sample([base + d * (k // 20) * s for d in range(1, 8) for s in (-1, 1)], 4))
    disp = []
    for v in vals:
        a, b = divmod(v, k)
        style = r.choice(["small", "dec", "comp"])
        if style == "small":
            disp.append(f"{v} {u2}")
        elif style == "dec":
            disp.append(f"{num(F(v, k))} {u1}")
        else:
            disp.append(f"{a} {u1} {b} {u2}" if b else f"{a} {u1}")
    if len(set(disp)) < 4:
        return None
    r.shuffle(vals)
    # recompute the displays after shuffle so display i matches vals[i]
    disp = []
    for v in vals:
        a, b = divmod(v, k)
        style = r.choice(["small", "dec", "comp"])
        disp.append({"small": f"{v} {u2}", "dec": f"{num(F(v, k))} {u1}",
                     "comp": f"{a} {u1} {b} {u2}" if b else f"{a} {u1}"}[style])
    ask = r.choice(["longest", "shortest"]) if u1 in ("km", "m") else r.choice(["largest", "smallest"])
    noun = {"km": "length", "m": "length", "kg": "mass", "l": "volume"}[u1]
    ask = {"longest": "longest", "shortest": "shortest"}.get(ask, ask)
    if u1 == "kg":
        ask = "heaviest" if ask == "largest" else "lightest" if ask == "smallest" else ask
    big = ask in ("longest", "largest", "heaviest")
    raw = [float(re.match(r"[\d.]+", d).group()) for d in disp]
    true_i = vals.index(max(vals) if big else min(vals))
    raw_i = raw.index(max(raw) if big else min(raw))
    if raw_i == true_i:
        return None
    order = [raw_i] + [i for i in range(4) if i not in (raw_i, true_i)]
    tags = ["compared_numbers_without_converting"] + ["did_not_compare_after_converting"] * 2
    why = ["Compared the numbers and ignored the units."] + ["Did not change to the same unit before comparing."] * 2
    stem = f"Which of these is the {ask}? Choose the correct {noun}."
    names = r.sample(range(4), 0)
    stem = f"Which of the following measures is the {ask}?"
    wrong = [((disp[i], vals[i]), tags[n], why[n]) for n, i in enumerate(order)]
    shown = dict(zip(vals, disp))
    return build(order_measures, stem, vals[true_i], wrong,
                 [f"Change every measure to {u2}.", "; ".join(f"{d} = {v} {u2}" for d, v in zip(disp, vals)),
                  f"The {ask} is {disp[true_i]}."], {"opts": disp, "ask": ask, "scale": 100 if u1 == "m" else 1},
                 lambda v: shown[int(v)], whole=True, auto_slips=False)


@checker(order_measures)
def _(p):
    vs = [parse_meas(d) for d in p["opts"]]
    big = p["ask"] in ("longest", "largest", "heaviest")
    v = max(vs) if big else min(vs)
    u = re.findall(r"[a-z]+", p["opts"][0])[-1]
    # the bank stores the value in the small unit of that system
    small = {"km": 1, "m": 1, "cm": 1, "kg": 1, "g": 1, "l": 1, "ml": 1}
    return F(v) * p["scale"]


@template(T, "basic", LM_COMPOUND, LM_CONVERT)
def measure_story(r):
    """math-pat-measure-add-subtract-story"""
    u1, u2, k = r.choice([("kg", "g", 1000), ("l", "ml", 1000), ("km", "m", 1000)])
    a, b = r.randint(1, 6), r.randrange(100, 1000, 50)
    S = a * k + b
    used = r.randrange(150, S - 100, 50)
    got = r.randrange(150, 1500, 50)
    if used >= S or used % 100 == 0 and got % 100 == 0:
        return None
    res = S - used + got
    name = nm(r)
    thing = {"g": "rice", "ml": "orange juice", "m": "rope"}[u2]
    verb = {"g": ("used", "bought"), "ml": ("drank", "poured in"), "m": ("cut off", "added")}[u2]
    in_big = r.random() < 0.5
    stem = (f"{name} had {a} {u1} {b} {u2} of {thing}. {name} {verb[0]} {used} {u2} and then {verb[1]} another {got} {u2}. "
            f"How much {thing} does {name} have now, in {u1 if in_big else u2}?")
    if in_big:
        sh = usd(u1)
        val = lambda x: F(x, k)
    else:
        sh = usd(u2)
        val = lambda x: F(x)
    wrongs = [(S - used, "forgot_to_add", f"Stopped after taking away the {used} {u2}."),
              (S - used - got, "subtracted_the_second_amount", f"Took away the {got} {u2} as well."),
              (S + used + got, "added_both", "Added both amounts."),
              (S + used - got, "wrong_operations", "Added the first amount and took away the second."),
              (res + 100, "slip_in_working", "Made a slip in the working."),
              (res - 50, "slip_in_working", "Made a slip in the working.")]
    return build(measure_story, stem, val(res), [(val(v), t, w) for v, t, w in wrongs if v > 0],
                 [f"{a} {u1} {b} {u2} = {S} {u2}", f"{S} - {used} + {got} = {res} {u2}"] + ([f"{res} {u2} = {num(F(res, k))} {u1}"] if in_big else []),
                 {"S": S, "used": used, "got": got, "k": k, "big": in_big}, sh, auto_slips=False)


@checker(measure_story)
def _(p):
    v = F(p["S"])
    v -= p["used"]
    v += p["got"]
    return v / p["k"] if p["big"] else v


@template(T, "basic", LM_ML, LM_UNITS)
def read_beaker(r):
    """math-pat-volume-reading-containers"""
    vmax, minor, major = r.choice([(500, 50, 100), (1000, 100, 200), (250, 10, 50), (200, 10, 50), (600, 20, 100),
                                   (400, 20, 100)])
    level = r.randrange(minor, vmax - minor, minor)
    if level % major == 0:
        return None
    name = nm(r)
    thing = r.choice(["water", "orange juice", "milk", "syrup"])
    stem = f"{name} pours {thing} into the measuring beaker as shown. How much {thing}, in ml, is in the beaker?"
    below = level - level % major
    return build(read_beaker, stem, level, [
        (below, "read_the_nearest_numbered_mark", "Read the numbered mark just below the level."),
        (level + minor, "misread_scale_by_one_division", "Counted one small division too many."),
        (level - minor, "misread_scale_by_one_division", "Counted one small division too few."),
        (below + major, "read_the_nearest_numbered_mark", "Read the numbered mark just above the level."),
    ], [f"Each small division is {minor} ml.", f"The level is {plural((level - below) // minor, 'division')} above {below} ml.",
        f"{below} + {level - below} = {level} ml"], {"level": level, "minor": minor},
        usd("ml"), whole=True, auto_slips=False, figure=beaker_svg(level, vmax, minor, major))


@checker(read_beaker)
def _(p):
    return F(sum(p["minor"] for _ in range(p["level"] // p["minor"])))


SENSE = [("the length of a ballpoint pen", "length", 15, "cm"), ("the height of a classroom door", "length", 2, "m"),
         ("the length of a school bus", "length", 12, "m"), ("the distance from home to the nearest MRT station", "length", 2, "km"),
         ("the width of a mobile phone", "length", 7, "cm"), ("the height of a primary school pupil", "length", 140, "cm"),
         ("the mass of a ripe mango", "mass", 300, "g"), ("the mass of a school bag with books", "mass", 4, "kg"),
         ("the mass of an adult cat", "mass", 4, "kg"), ("the mass of a coin", "mass", 5, "g"),
         ("the volume of a spoonful of medicine", "volume", 5, "ml"), ("the volume of a can of drink", "volume", 330, "ml"),
         ("the volume of water in a full bucket", "volume", 10, "l"), ("the volume of a bottle of cooking oil", "volume", 2, "l")]
SENSE_UNITS = {"length": [("cm", 1), ("m", 100), ("km", 100000)], "mass": [("g", 1), ("kg", 1000)],
               "volume": [("ml", 1), ("l", 1000)]}


@template(T, "basic", LM_UNITS)
def sensible_unit(r):
    name = nm(r)
    thing, kind, v, u = r.choice(SENSE)
    noun = {"length": "length", "mass": "mass", "volume": "volume of liquid"}[kind]
    scale = dict(SENSE_UNITS[kind])
    others = [(x, s) for x, s in SENSE_UNITS[kind] if x != u]
    base = v * scale[u]
    opts = {(f"{v} {u}"): base}
    wrong = []
    for x, s in others:
        wrong.append(((f"{v} {x}", v * s), "wrong_unit", f"Chose the unit {x}, which is far too " +
                      ("big." if s > scale[u] else "small.")))
    wrong.append(((f"{v * 10} {u}", v * 10 * scale[u]), "wrong_size", "The number is ten times too large."))
    wrong.append(((f"{max(v // 10, 1) if v >= 10 else v * 100} {u}", (max(v // 10, 1) if v >= 10 else v * 100) * scale[u]),
                  "wrong_size", "The number is far too small or too large."))
    stem = f"{name} estimates {thing}. Which estimate is the most reasonable?"
    disp = {base: f"{v} {u}"}
    for (d, val), _, _ in wrong:
        disp[val] = d
    return build(sensible_unit, stem, base, wrong, [f"{thing} is about {v} {u}."], {"thing": thing},
                 lambda x: disp[int(x)], whole=True, auto_slips=False)


@checker(sensible_unit)
def _(p):
    row = next(x for x in SENSE if x[0] == p["thing"])
    return F(row[2] * dict(SENSE_UNITS[row[1]])[row[3]])


# ================================================================ length, mass and volume: intermediate

def carry_pair(r, k, carry):
    while True:
        b1, b2 = r.randint(10, k - 10), r.randint(10, k - 10)
        if (b1 + b2 >= k) == carry:
            return b1, b2


CTX_ADD = [("m", "cm", 100, "{a}'s ribbon is {x} long and {b}'s ribbon is {y} long.", "total length"),
           ("kg", "g", 1000, "{a}'s bag of rice has a mass of {x} and {b}'s bag has a mass of {y}.", "total mass"),
           ("l", "ml", 1000, "{a}'s jug holds {x} of water and {b}'s jug holds {y}.", "total volume of water"),
           ("km", "m", 1000, "{a} ran {x} on Saturday and {b} ran {y}.", "total distance")]


@template(T, "intermediate", LM_COMPOUND)
def add_compound(r):
    """math-pat-measure-add-subtract-story"""
    u1, u2, k, thing, what = r.choice(CTX_ADD)
    a1, a2 = r.randint(1, 9), r.randint(1, 9)
    b1, b2 = carry_pair(r, k, r.random() < 0.85)
    N = (a1 + a2) * k + b1 + b2
    q, rem = divmod(N, k)
    a, b = r.sample(NAMES, 2)
    stem = (thing.format(a=a, b=b, x=f"{a1} {u1} {b1} {u2}", y=f"{a2} {u1} {b2} {u2}") +
            f" What is the {what} of the two, in {u1} and {u2}?")
    sh = cshow(u1, u2)
    return build(add_compound, stem, cc(q, rem), [
        (cc(a1 + a2, (b1 + b2) % k) if b1 + b2 >= k else cc(a1 + a2 + 1, b1 + b2), "forgot_to_carry",
         f"Did not change {k} {u2} to 1 {u1}."),
        (cc(a1 + a2, b1 + b2) if b1 + b2 >= k else None, "left_small_part_over_limit",
         f"Left {b1 + b2} {u2} without changing to {u1}."),
        (cc(q, (rem + 10) % k or 10), "slip_in_addition", f"Made a slip adding the {u2}."),
        (cc(q + 1, rem), "slip_in_addition", f"Made a slip adding the {u1}."),
        (cc(q, (rem - 10) % k or 20), "slip_in_addition", f"Made a slip adding the {u2}."),
    ], [f"{u1}: {a1} + {a2} = {a1 + a2}", f"{u2}: {b1} + {b2} = {b1 + b2}", f"Total = {sh(cc(q, rem))}"],
        {"a1": a1, "b1": b1, "a2": a2, "b2": b2, "k": k}, sh, auto_slips=False)


@checker(add_compound)
def _(p):
    N = p["a1"] * p["k"] + p["b1"] + p["a2"] * p["k"] + p["b2"]
    q = next(q for q in range(2000) if 0 <= N - q * p["k"] < p["k"])
    return F(cc(q, N - q * p["k"]))


@template(T, "intermediate", LM_COMPOUND)
def subtract_compound(r):
    """math-pat-measure-add-subtract-story"""
    u1, u2, k, thing, what = r.choice(CTX_ADD)
    a2 = r.randint(1, 6)
    a1 = a2 + r.randint(2, 6)
    b1 = r.randint(10, k // 2 - 10)
    b2 = r.randint(b1 + 10, k - 10)
    N = (a1 - a2) * k + b1 - b2
    q, rem = divmod(N, k)
    a, b = r.sample(NAMES, 2)
    stem = (thing.format(a=a, b=b, x=f"{a1} {u1} {b1} {u2}", y=f"{a2} {u1} {b2} {u2}") +
            f" Find the difference between the two amounts. Give your answer in {u1} and {u2}.")
    sh = cshow(u1, u2)
    return build(subtract_compound, stem, cc(q, rem), [
        (cc(a1 - a2, b2 - b1), "subtracted_smaller_from_larger", f"Took {b1} {u2} from {b2} {u2} the wrong way round."),
        (cc(q + 1, rem), "forgot_to_regroup", f"Did not take 1 {u1} away after regrouping."),
        (cc(q, (rem + 10) % k or 10), "slip_in_subtraction", f"Made a slip in the {u2}."),
        (cc(q - 1, rem) if q > 1 else None, "slip_in_subtraction", f"Made a slip in the {u1}."),
        (cc(q, (rem - 10) % k or 20), "slip_in_subtraction", f"Made a slip in the {u2}."),
    ], [f"{a1} {u1} {b1} {u2} = {(a1 - 1)} {u1} {b1 + k} {u2}", f"{(a1 - 1) - a2} {u1}, {b1 + k} - {b2} = {rem} {u2}",
        f"Answer: {sh(cc(q, rem))}"], {"a1": a1, "b1": b1, "a2": a2, "b2": b2, "k": k}, sh, auto_slips=False)


@checker(subtract_compound)
def _(p):
    N = (p["a1"] * p["k"] + p["b1"]) - (p["a2"] * p["k"] + p["b2"])
    q = next(q for q in range(2000) if 0 <= N - q * p["k"] < p["k"])
    return F(cc(q, N - q * p["k"]))


@template(T, "intermediate", LM_COMPOUND)
def repeat_measure(r):
    u1, u2, k = r.choice([("l", "ml", 1000), ("kg", "g", 1000), ("m", "cm", 100)])
    thing = {"ml": "bottles of drink holding", "g": "packets of flour of mass", "cm": "pieces of rope of length"}[u2]
    n = r.randint(6, 18)
    v = r.choice([x for x in range(15, 400, 5) if x % 10 or u2 == "cm"])
    N = n * v
    if N < k or N % k == 0:
        return None
    q, rem = divmod(N, k)
    name = nm(r)
    stem = f"{name} has {n} {thing} {v} {u2} each. What is the total in {u1} and {u2}?"
    sh = cshow(u1, u2)
    wk = k // 10
    return build(repeat_measure, stem, cc(q, rem), [
        (cc(N // wk, N % wk), "wrong_conversion_factor", f"Used 1 {u1} = {wk} {u2}."),
        (cc(0, N), "did_not_change_units", f"Left the answer as {N} {u2}."),
        (cc(q, rem // 10 if rem >= 10 else rem + 1), "dropped_a_digit", "Lost a digit in the small part."),
        (cc(q + 1, rem), "slip_in_multiplication", "Made a slip in the multiplication."),
    ], [f"{n} × {v} = {N} {u2}", f"{N} {u2} = {sh(cc(q, rem))}"], {"n": n, "v": v, "k": k}, sh, auto_slips=False)


@checker(repeat_measure)
def _(p):
    N = sum(p["v"] for _ in range(p["n"]))
    q = next(q for q in range(2000) if 0 <= N - q * p["k"] < p["k"])
    return F(cc(q, N - q * p["k"]))


@template(T, "intermediate", LM_COMPOUND)
def share_equally(r):
    u1, u2, k = r.choice([("l", "ml", 1000), ("kg", "g", 1000), ("m", "cm", 100)])
    n = r.randint(3, 9)
    each = r.choice([x for x in range(20, 600, 5)])
    T_ = n * each
    a, b = divmod(T_, k)
    if a < 1 or b == 0:
        return None
    thing = {"ml": "juice poured equally into", "g": "sugar packed equally into", "cm": "ribbon cut into"}[u2]
    pcs = {"ml": "cups", "g": "bags", "cm": "equal pieces"}[u2]
    name = nm(r)
    stem = f"{name} has {a} {u1} {b} {u2} of {thing.split(' ')[0]}, " if False else \
        f"{name} shares {a} {u1} {b} {u2} equally among {n} {pcs[:-1] if pcs.endswith('s') else pcs}s. " if False else \
        f"A total of {a} {u1} {b} {u2} is divided equally into {plural(n, 'part')}. How many {u2} are in each part?"
    return build(share_equally, stem, each, [
        (F(a * k, n) + b if (a * k) % n == 0 else None, "divided_only_the_big_unit", f"Divided only the {a} {u1} and added the {b} {u2}."),
        (T_ // (n + 1), "wrong_number_of_parts", f"Divided by {n + 1}."),
        (T_ // (n - 1), "wrong_number_of_parts", f"Divided by {n - 1}."),
        (each * 10, "decimal_place_error", "Put a zero in the wrong place."),
        (each + 5, "slip_in_division", "Made a slip in the division."),
        (each - 5, "slip_in_division", "Made a slip in the division."),
    ], [f"{a} {u1} {b} {u2} = {T_} {u2}", f"{T_} ÷ {n} = {each}"], {"a": a, "b": b, "k": k, "n": n},
        usd(u2), whole=True, auto_slips=False)


@checker(share_equally)
def _(p):
    T_ = p["a"] * p["k"] + p["b"]
    return F(next(e for e in range(1, T_ + 1) if e * p["n"] == T_))


@template(T, "intermediate", LM_COMPOUND, LM_CONVERT)
def whole_part_mass(r):
    """math-pat-mass-whole-and-part"""
    fr = r.choice([F(1, 2), F(1, 3), F(1, 4), F(2, 5), F(3, 4), F(2, 3)])
    d = fr.denominator
    contents = d * r.randint(1, 8) * 100
    E = r.randint(2, 12) * 50
    M = E + contents
    M2 = int(M - fr * contents)
    thing = r.choice(["bottle of cooking oil", "jar of honey", "tin of biscuits", "tub of paint", "pot of soup"])
    name = nm(r)
    fs = f"{fr.numerator}/{fr.denominator}"
    stem = (f"{name}'s full {thing} has a total mass of {num(F(M, 1000))} kg. After {fs} of the contents "
            f"are used, the total mass is {num(F(M2, 1000))} kg. What is the mass of the empty container, in grams?")
    rem = M - M2
    return build(whole_part_mass, stem, E, [
        (M2, "took_remaining_as_empty", "Used the mass after using some contents as the empty mass."),
        (M - rem * fr if (M - rem * fr).denominator == 1 else None, "multiplied_instead_of_divided",
         f"Multiplied the used mass by {fs} instead of dividing."),
        (M - rem * (d - fr.numerator) / fr.numerator if (M - rem * (d - fr.numerator) / fr.numerator) > 0 else None,
         "used_wrong_number_of_parts", "Used the number of parts left instead of the whole."),
        (E + 100, "slip_in_subtraction", "Made a slip in the subtraction."),
        (E - 50 if E > 50 else E + 150, "slip_in_subtraction", "Made a slip in the subtraction."),
    ], [f"Mass used = {M} - {M2} = {rem} g", f"{fs} of contents = {rem} g, so contents = {rem / fr} g",
        f"Empty = {M} - {rem / fr} = {E} g"], {"M": M, "M2": M2, "n": fr.numerator, "d": d},
        usd("g"), whole=True, auto_slips=False)


@checker(whole_part_mass)
def _(p):
    f = F(p["n"], p["d"])
    return F(next(E for E in range(0, p["M"]) if (p["M"] - E) * (1 - f) + E == p["M2"]))


@template(T, "intermediate", LM_ML, LM_COMPOUND, calc=True)
def cups_from_jug(r):
    z = r.choice([150, 200, 250, 300, 350, 120])
    a = r.randint(2, 6)
    b = r.choice([x for x in range(50, 1000, 50)])
    tot = a * 1000 + b
    if tot % z == 0:
        return None
    cnt = tot // z
    stem = f"A jug contains {a} l {b} ml of water. {nm(r)} fills as many glasses of {z} ml as possible. How many glasses are filled completely?"
    return build(cups_from_jug, stem, cnt, [
        (cnt + 1, "counted_the_part_glass", "Counted the glass that is only partly filled."),
        ((a * 100 + b) // z, "wrong_conversion_factor", "Used 1 l = 100 ml."),
        (cnt - 1, "slip_in_division", "Made a slip in the division."),
        (cnt + 2, "slip_in_division", "Made a slip in the division."),
    ], [f"{a} l {b} ml = {tot} ml", f"{tot} ÷ {z} = {cnt} remainder {tot % z}"], {"tot": tot, "z": z},
        lambda v: f"{num(v)}", whole=True, auto_slips=False)


@checker(cups_from_jug)
def _(p):
    n, left = 0, p["tot"]
    while left >= p["z"]:
        left -= p["z"]
        n += 1
    return F(n)


# ================================================================ length, mass and volume: competent

@template(T, "competent", LM_COMPOUND, LM_ML)
def fill_and_pour(r):
    C = r.randint(3, 9)
    c, cm = r.choice([150, 200, 250]), r.randint(4, 12)
    b, bn = r.choice([300, 400, 500, 600]), r.randint(1, 4)
    used = c * cm + b * bn
    if used >= C * 1000 - 100:
        return None
    left = C * 1000 - used
    name = nm(r)
    stem = (f"{name} wants to fill {a_an(C)} {C} l container with water. {name} pours in {cm} cups of {c} ml each and "
            f"{bn} bottle{'s' if bn > 1 else ''} of {b} ml each. How much more water, in ml, is needed to fill the container?")
    return build(fill_and_pour, stem, left, [
        (used, "gave_the_amount_poured", "Gave the amount already poured in."),
        (C * 1000 - c * cm, "forgot_the_bottles", "Left out the water from the bottles."),
        (C * 100 - used if C * 100 > used else None, "wrong_conversion_factor", "Used 1 l = 100 ml."),
        (left + 100, "slip_in_working", "Made a slip in the working."),
        (left - 50, "slip_in_working", "Made a slip in the working."),
    ], [f"Poured: {cm} × {c} + {bn} × {b} = {used} ml", f"{C} l = {C * 1000} ml", f"{C * 1000} - {used} = {left} ml"],
        {"C": C, "c": c, "cm": cm, "b": b, "bn": bn}, usd("ml"), whole=True, auto_slips=False)


@checker(fill_and_pour)
def _(p):
    left = p["C"] * 1000
    for _ in range(p["cm"]):
        left -= p["c"]
    for _ in range(p["bn"]):
        left -= p["b"]
    return F(left)


@template(T, "competent", LM_COMPOUND, calc=True)
def rope_cut_pieces(r):
    L = r.randint(6, 12)
    n, p_ = r.randint(2, 4), r.choice([60, 75, 85, 95, 110])
    q = r.choice([35, 45, 55, 65])
    R = L * 100 - n * p_
    if R <= q * 2 or R % q == 0:
        return None
    pieces, left = divmod(R, q)
    a, b = r.sample(NAMES, 2)
    stem = (f"{a} has a rope {L} m long. {a} cuts off {n} pieces of {p_} cm each. {b} then cuts the rest of the rope "
            f"into as many pieces of {q} cm as possible. How long, in cm, is the piece of rope left over?")
    return build(rope_cut_pieces, stem, left, [
        (pieces, "gave_number_of_pieces", "Gave the number of pieces instead of the length left over."),
        (q - left, "used_the_gap_to_next_piece", "Found how much more was needed for another piece."),
        (R, "gave_rope_after_first_cut", "Gave the length of rope after the first cut."),
        ((L * 100 - p_) % q or None, "forgot_pieces_count", f"Cut off only 1 piece of {p_} cm in the first step."),
        (left + 5, "slip_in_division", "Made a slip in the division."),
    ], [f"Cut off: {n} × {p_} = {n * p_} cm", f"Left: {L * 100} - {n * p_} = {R} cm", f"{R} ÷ {q} = {pieces} remainder {left}"],
        {"L": L, "n": n, "p": p_, "q": q}, usd("cm"), whole=True, auto_slips=False)


@checker(rope_cut_pieces)
def _(p):
    R = p["L"] * 100
    for _ in range(p["n"]):
        R -= p["p"]
    while R >= p["q"]:
        R -= p["q"]
    return F(R)


@template(T, "competent", LM_ML, LM_COMPOUND)
def tap_and_leak(r):
    a = r.randint(6, 15)
    b = r.randint(2, a - 2)
    t = r.randint(5, 20)
    cap = (a - b) * a * t
    name = nm(r)
    stem = (f"An empty tank holds {cap} l of water. A tap fills it at {a} l per minute, but a leak loses {b} l "
            f"every minute. How many minutes does {name} need to fill the tank?")
    ans = cap // (a - b)
    return build(tap_and_leak, stem, ans, [
        (cap // a, "ignored_the_leak", "Ignored the water lost through the leak."),
        (cap // b if cap % b == 0 else None, "used_only_the_leak_rate", "Used the leak rate only."),
        (cap // (a + b) if cap % (a + b) == 0 else None, "added_the_rates", "Added the fill rate and the leak rate."),
        (ans + 5, "slip_in_division", "Made a slip in the division."),
        (ans - 5, "slip_in_division", "Made a slip in the division."),
        (ans + 10, "slip_in_division", "Made a slip in the division."),
    ], [f"Net rate = {a} - {b} = {a - b} l per minute", f"{cap} ÷ {a - b} = {plural(ans, 'minute')}"],
        {"cap": cap, "a": a, "b": b}, usd("minutes"), whole=True, auto_slips=False)


@checker(tap_and_leak)
def _(p):
    water, m = 0, 0
    while water < p["cap"]:
        water += p["a"] - p["b"]
        m += 1
    return F(m)


@template(T, "competent", LM_COMPOUND)
def box_and_books(r):
    """math-pat-mass-whole-and-part"""
    box = r.randint(2, 9) * 100
    bk = r.randint(2, 9) * 50 + 100
    n1, n2 = r.sample(range(3, 15), 2)
    n1, n2 = min(n1, n2), max(n1, n2)
    if n2 - n1 < 2:
        return None
    M1, M2 = box + n1 * bk, box + n2 * bk
    name = nm(r)
    stem = (f"{name} packs {n1} identical books into an empty box, and the total mass is {M1} g. With {n2} of the same "
            f"books in the box, the total mass is {M2} g. What is the mass of the empty box, in grams?")
    return build(box_and_books, stem, box, [
        (bk, "found_book_not_box", "Found the mass of one book instead of the box."),
        (M1 - n1 * (M2 - M1) // (n2 - n1) - bk if M1 - n1 * (M2 - M1) // (n2 - n1) - bk > 0 else None,
         "slip_in_subtraction", "Took away one book too many."),
        (M1 - (M2 - M1), "subtracted_whole_difference", "Subtracted the whole difference in mass once."),
        (M1 // n1, "divided_total_by_books", "Divided the total mass by the number of books."),
        (box + 100, "slip_in_working", "Made a slip in the working."),
    ], [f"{n2 - n1} books = {M2} - {M1} = {M2 - M1} g", f"1 book = {bk} g", f"Box = {M1} - {n1} × {bk} = {box} g"],
        {"M1": M1, "M2": M2, "n1": n1, "n2": n2}, usd("g"), whole=True, auto_slips=False)


@checker(box_and_books)
def _(p):
    return F(next(x for x in range(1, p["M1"]) if (p["M1"] - x) % p["n1"] == 0 and
                  x + (p["M1"] - x) // p["n1"] * p["n2"] == p["M2"]))


@template(T, "competent", LM_COMPOUND, LM_CONVERT)
def fraction_then_used(r):
    M = r.choice([2, 3, 4, 5, 6])
    fr = r.choice([F(1, 4), F(2, 5), F(3, 5), F(1, 5), F(3, 4)])
    if (M * 1000 * fr).denominator != 1:
        return None
    e = r.choice([150, 250, 350, 450])
    used = M * 1000 * fr
    left = M * 1000 - used - e
    if left <= 0:
        return None
    name = nm(r)
    thing = r.choice(["flour", "sugar", "rice"])
    stem = (f"{name} has {M} kg of {thing}. {fr.numerator}/{fr.denominator} of it is used for baking and another {e} g "
            f"is used for cooking. How much {thing} is left, in grams?")
    return build(fraction_then_used, stem, left, [
        (M * 1000 * (1 - fr), "forgot_the_extra", f"Did not take away the {e} g."),
        (used - e if used > e else None, "took_fraction_as_left", "Used the fraction used as the amount left."),
        (M * 1000 * (1 - fr) + e, "added_instead_of_subtracted", f"Added the {e} g instead of taking it away."),
        (left + 100, "slip_in_subtraction", "Made a slip in the subtraction."),
        (left - 50, "slip_in_subtraction", "Made a slip in the subtraction."),
    ], [f"{M} kg = {M * 1000} g", f"Used for baking = {used} g", f"Left = {M * 1000} - {used} - {e} = {left} g"],
        {"M": M, "n": fr.numerator, "d": fr.denominator, "e": e}, usd("g"), whole=True, auto_slips=False)


@checker(fraction_then_used)
def _(p):
    parts = F(p["M"] * 1000, p["d"])
    return F(p["M"] * 1000) - parts * p["n"] - p["e"]


@template(T, "competent", LM_COMPOUND)
def three_ribbons(r):
    A = r.randint(8, 25) * 10
    d = r.choice([20, 30, 35, 45, 55])
    k = r.choice([2, 3])
    B = A + d
    Cc = k * B
    tot = A + B + Cc
    a, b, c = r.sample(NAMES, 3)
    stem = (f"{a}'s ribbon is {num(F(A, 100))} m long. {b}'s ribbon is {d} cm longer than {a}'s, and {c}'s ribbon is "
            f"{k} times as long as {b}'s. What is the total length of the three ribbons, in metres?")
    return build(three_ribbons, stem, F(tot, 100), [
        (F(A + B + k * d + A, 100), "found_c_by_adding_difference", f"Worked out {c}'s ribbon as {k} × {d} cm."),
        (F(A + B, 100) * 1, "left_out_a_ribbon", "Left out one ribbon."),
        (F(tot, 10), "wrong_conversion_factor", "Changed centimetres to metres by dividing by 10."),
        (F(A + Cc - d + B, 100), "slip_in_working", "Made a slip in the working."),
        (F(tot + 10, 100), "slip_in_addition", "Made a slip in the addition."),
    ], [f"{b}'s = {A} + {d} = {B} cm", f"{c}'s = {k} × {B} = {Cc} cm", f"Total = {A} + {B} + {Cc} = {tot} cm = {num(F(tot, 100))} m"],
        {"A": A, "d": d, "k": k}, usd("m"), auto_slips=False)


@checker(three_ribbons)
def _(p):
    B = p["A"] + p["d"]
    return F(sum([p["A"], B, B * p["k"]]), 100)


# ================================================================ time: basic

def hands_to_time(h, m):
    ha, ma = (h % 12 + m / 60) * 30, m * 6
    mm = round(ma / 6) % 60
    hh = int(ha // 30) or 12
    return hh * 60 + mm


@template(T, "basic", TM_5)
def read_clock_5(r):
    h, m = r.randint(1, 12), r.randrange(0, 60, 5)
    name, place = nm(r), r.choice(PLACES)
    stem = f"{name} looked at the clock in the {place}. What time does the clock show?"
    sw_h = (m // 5) or 12
    sw_m = (h % 12) * 5
    ans = h * 60 + m
    hr = lambda x: x if x <= 12 else x - 12
    return build(read_clock_5, stem, ans, [
        (sw_h * 60 + sw_m, "swapped_the_hands", "Read the hour hand as the minute hand and the minute hand as the hour hand."),
        ((hr(h + 1)) * 60 + m, "read_wrong_hour", "Read the hour for the next hour mark."),
        (h * 60 + (m + 5) % 60 or None, "misread_minute_mark", "Counted one mark too far on the minute hand."),
        (h * 60 + (m - 5) % 60, "misread_minute_mark", "Counted one mark too few on the minute hand."),
        ((hr(h - 1) or 12) * 60 + m, "read_wrong_hour", "Read the hour for the previous hour mark."),
    ], [f"The short hand points near {h}, so the hour is {h}.", f"The long hand points to {m // 5}, so {plural(m, 'minute')} past.",
        f"The time is {fmtclk(ans)}."], {"h": h, "m": m}, fmtclk, whole=True, auto_slips=False,
        figure=clock_svg(h, m))


@checker(read_clock_5)
def _(p):
    return F(hands_to_time(p["h"], p["m"]))


@template(T, "basic", TM_MIN)
def read_clock_minute(r):
    h, m = r.randint(1, 12), r.choice([x for x in range(1, 60) if x % 5])
    name, place = nm(r), r.choice(PLACES)
    stem = f"The clock in the {place} is shown. What time does it show, to the nearest minute? ({name} is practising telling time.)"
    ans = h * 60 + m
    hr = lambda x: (x - 1) % 12 + 1
    return build(read_clock_minute, stem, ans, [
        (h * 60 + 60 - m, "read_minutes_backwards", "Counted the minutes from the 12 going the wrong way."),
        (hr(h + 1) * 60 + m, "read_wrong_hour", "Used the next hour although the hour hand has not reached it."),
        (h * 60 + m + 1, "misread_minute_mark", "Counted one minute mark too many."),
        (h * 60 + m - 1 if m > 1 else None, "misread_minute_mark", "Counted one minute mark too few."),
        (h * 60 + (m // 5 * 5), "read_nearest_five", "Read only the nearest numbered minute mark."),
    ], [f"Hour: {h}.", f"Minutes: the long hand is {plural(m, 'mark')} after the 12.", f"Time: {fmtclk(ans)}."],
        {"h": h, "m": m}, fmtclk, whole=True, auto_slips=False, figure=clock_svg(h, m))


@checker(read_clock_minute)
def _(p):
    return F(hands_to_time(p["h"], p["m"]))


@template(T, "basic", TM_HM, TM_SEC)
def hm_convert(r):
    big, small = r.choice([("h", "min"), ("min", "s")])
    if r.random() < 0.5:
        a, b = r.randint(1, 9), r.randint(5, 55)
        ans = a * 60 + b
        stem = f"Express {a} {big} {b} {small} in {small}."
        return build(hm_convert, stem, ans, [
            (a * 100 + b, "used_100_for_60", f"Used 1 {big} = 100 {small}."),
            (a * 60, "forgot_the_small_part", f"Left out the {b} {small}."),
            (a + b, "added_without_converting", "Added the numbers without converting."),
            (ans + 10, "slip_in_addition", "Made a slip in the addition."),
            (ans - 10, "slip_in_addition", "Made a slip in the addition."),
        ], [f"1 {big} = 60 {small}", f"{a} × 60 = {a * 60}", f"{a * 60} + {b} = {ans}"], {"mode": "a", "a": a, "b": b},
            usd(small), whole=True, auto_slips=False)
    a, b = r.randint(1, 9), r.randint(5, 55)
    N = a * 60 + b
    sh = cshow(big, small)
    stem = f"Express {N} {small} in {big} and {small}."
    return build(hm_convert, stem, cc(a, b), [
        (cc(N // 100, N % 100), "used_100_for_60", f"Divided by 100 instead of 60."),
        (cc(a + 1, b), "slip_in_big_unit", f"Made a slip in the number of {big}."),
        (cc(a, 60 - b), "remainder_taken_from_60", "Used 60 minus the remainder."),
        (cc(N // 60, (N % 60) // 10) if (N % 60) >= 10 else None, "dropped_a_digit", "Lost a digit."),
        (cc(a, b + 10), "slip_in_small_unit", f"Made a slip in the {small}."),
    ], [f"{N} ÷ 60 = {a} remainder {b}", f"{N} {small} = {a} {big} {b} {small}"], {"mode": "b", "N": N}, sh, auto_slips=False)


@checker(hm_convert)
def _(p):
    if p["mode"] == "a":
        return F(sum([60] * p["a"]) + p["b"])
    N = p["N"]
    h = next(h for h in range(100) if 0 <= N - h * 60 < 60)
    return F(cc(h, N - h * 60))


@template(T, "basic", TM_24)
def to_24h(r):
    h, m = r.randint(1, 11), r.randrange(0, 60, 5)
    if r.random() < 0.5:
        pm = r.random() < 0.5
        v = (h + 12 if pm else h) * 60 + m
        stem = f"{nm(r)}'s class starts at {h}:{m:02d} {'pm' if pm else 'am'}. Write this time using the 24-hour clock."
        wrong = [((h if pm else h + 12) * 60 + m, "forgot_to_add_12" if pm else "added_12_to_am",
                  "Did not add 12 hours." if pm else "Added 12 hours to an am time."),
                 ((h + 10) * 60 + m, "added_10_not_12", "Added 10 instead of 12."),
                 (v + 10, "slip_in_minutes", "Made a slip in the minutes."),
                 ((h + 12 if pm else h) * 60 + (m + 30) % 60 + 5, "slip_in_minutes", "Made a slip in the minutes.")]
        return build(to_24h, stem, v, wrong, [f"{h}:{m:02d} {'pm' if pm else 'am'} = {fmt24(v)}"],
                     {"mode": "a", "h": h, "m": m, "pm": pm}, fmt24, whole=True, auto_slips=False)
    pm = r.random() < 0.6
    v = (h + 12 if pm else h) * 60 + m
    stem = f"A train leaves at {fmt24(v)}. Write this time using the 12-hour clock, with am or pm."
    ans = v
    ap = fmt12
    return build(to_24h, stem, ans, [
        ((v + 720) % 1440 or None, "wrong_am_pm", "Chose am for pm (or the other way round)."),
        ((v - 600) % 1440, "subtracted_10_not_12", "Subtracted 10 instead of 12."),
        ((((h + 12 - 12) * 60) + (m + 10) % 60) % 1440 + 0 if False else (v + 20) % 1440, "slip_in_minutes", "Made a slip in the minutes."),
        (v - 10, "slip_in_minutes", "Made a slip in the minutes."),
    ], [f"{fmt24(v)} = {ap(v)}"], {"mode": "b", "h": h, "m": m, "pm": pm}, ap, whole=True, auto_slips=False)


@checker(to_24h)
def _(p):
    return F((p["h"] + (12 if p["pm"] else 0)) * 60 + p["m"])


def clock_add(h, m, d):
    t = h * 60 + m + d
    h2 = ((t // 60) - 1) % 12 + 1
    return h2 * 60 + t % 60


@template(T, "basic", TM_FIND, TM_5, weight=3)
def clock_plus_duration(r):
    """math-pat-time-elapsed-clock"""
    h, m = r.randint(1, 12), r.randrange(0, 60, 5)
    d = r.choice([x for x in range(15, 100, 5)])
    if m + d < 60:
        return None
    name = nm(r)
    act = r.choice(["started reading", "began homework", "started a swimming lesson", "started cooking dinner"])
    stem = f"The clock shows the time when {name} {act}. The activity lasted {plural(d, 'minute')}. What time did it end?"
    ans = clock_add(h, m, d)
    hr = lambda x: (x - 1) % 12 + 1
    return build(clock_plus_duration, stem, ans, [
        (h * 60 + (m + d) % 60, "forgot_to_carry_the_hour", "Did not add 1 hour after going past 60 minutes."),
        (clock_add(h, m, -d), "subtracted_instead_of_added", "Went back in time instead of forward."),
        (hr(h + 1) * 60 + (m + d) % 60 + 10 if False else hr(h + 2) * 60 + (m + d) % 60, "carried_too_many_hours", "Added one hour too many."),
        (ans + 5, "slip_in_addition", "Made a slip in the addition."),
        (ans - 10, "slip_in_addition", "Made a slip in the addition."),
    ], [f"Start: {fmtclk(h * 60 + m)}", f"{m} + {d} = {plural(m + d, 'minute')} = 1 h {m + d - 60} min", f"Finish: {fmtclk(ans)}"],
        {"h": h, "m": m, "d": d}, fmtclk, whole=True, auto_slips=False, figure=clock_svg(h, m))


@checker(clock_plus_duration)
def _(p):
    t = p["h"] * 60 + p["m"]
    for _ in range(p["d"]):
        t += 1
    h = (t // 60 - 1) % 12 + 1
    return F(h * 60 + t % 60)


@template(T, "basic", TM_FIND)
def time_after_simple(r):
    h24, m = r.randint(5, 16), r.randrange(5, 60, 5)
    d = r.randint(25, 110)
    start = h24 * 60 + m
    end = start + d
    if m + d < 60 and r.random() < 0.8:
        return None
    thing = r.choice(["bus journey", "lesson", "film", "football match", "concert"])
    stem = f"{a_an(thing).capitalize()} {thing} starts at {fmt12(start)} and lasts {plural(d, 'minute')}. At what time does it end?"
    return build(time_after_simple, stem, end, [
        (start + d % 60 + (d // 60) * 60 if False else (start - d), "subtracted_instead_of_added", "Subtracted the minutes."),
        (day(start + (d // 60) * 60 + (m + d % 60) % 60 - m + 0) if False else (end - (60 if m + d >= 60 else -60)), "carry_error", "Made an error with the hour carried over."),
        (end + 5, "slip_in_addition", "Made a slip in the addition."),
        (end - 10, "slip_in_addition", "Made a slip in the addition."),
        ((end + 720) % 1440, "wrong_am_pm", "Changed am to pm."),
    ], [f"{fmt12(start)} + {d} min = {fmt12(end)}"], {"start": start, "d": d}, fmt12, whole=True, auto_slips=False)


@checker(time_after_simple)
def _(p):
    t = p["start"]
    for _ in range(p["d"]):
        t += 1
    return F(t)


# ================================================================ time: intermediate

def two_clock_times(r):
    h1, m1 = r.randint(1, 12), r.randrange(0, 60, 5)
    d = r.randrange(65, 360, 5)
    if d % 60 == 0:
        return None
    t1 = h1 * 60 + m1
    t2 = t1 + d
    h2 = (t2 // 60 - 1) % 12 + 1
    return h1, m1, h2, t2 % 60, d


@template(T, "intermediate", TM_FIND)
def duration_two_clocks(r):
    res = two_clock_times(r)
    if not res:
        return None
    h1, m1, h2, m2, d = res
    name = nm(r)
    stem = f"{name} started a task at the time shown on the first clock and finished at the time shown on the second clock. How long did the task take?"
    dh, dm = divmod(d, 60)
    sh = cshow("h", "min")
    return build(duration_two_clocks, stem, cc(dh, dm), [
        (cc(abs(((h2 - h1) % 12)), abs(m2 - m1)) if abs(m2 - m1) else None, "subtracted_smaller_minutes_from_larger", "Subtracted the minutes the wrong way round."),
        (cc(dh + 1, dm), "forgot_to_regroup", "Did not take 1 hour away after regrouping."),
        (cc(dh - 1, dm) if dh > 1 else None, "regrouped_twice", "Took an hour away too many."),
        (cc(dh, (dm + 10) % 60 or 5), "slip_in_subtraction", "Made a slip in the minutes."),
        (cc(dh, (dm + 50) % 60 or 5), "slip_in_subtraction", "Made a slip in the minutes."),
    ], [f"From {fmtclk(h1 * 60 + m1)} to {fmtclk(h2 * 60 + m2)}", f"Duration = {sh(cc(dh, dm))}"],
        {"h1": h1, "m1": m1, "h2": h2, "m2": m2}, sh, auto_slips=False,
        figure=two_clocks_svg((h1, m1), (h2, m2)))


@checker(duration_two_clocks)
def _(p):
    t1, t2 = p["h1"] % 12 * 60 + p["m1"], p["h2"] % 12 * 60 + p["m2"]
    d = next(x for x in range(1, 721) if (t1 + x) % 720 == t2)
    return F(cc(d // 60, d % 60))


@template(T, "intermediate", TM_FIND)
def duration_am_pm(r):
    s = r.randint(8, 11) * 60 + r.randrange(5, 60, 5)
    e = r.randint(13, 17) * 60 + r.randrange(0, 60, 5)
    d = e - s
    if d % 60 == 0:
        return None
    dh, dm = divmod(d, 60)
    sh = cshow("h", "min")
    name = nm(r)
    ev = r.choice(["a workshop", "a sports camp", "a school fair", "a drawing class"])
    stem = f"{name} attended {ev} from {fmt12(s)} to {fmt12(e)}. How long did it last?"
    wrong_h = e // 60 - s // 60
    return build(duration_am_pm, stem, cc(dh, dm), [
        (cc(wrong_h, abs(e % 60 - s % 60)), "subtracted_smaller_minutes_from_larger", "Took the smaller minutes from the larger."),
        (cc(dh + 1, dm), "forgot_to_regroup", "Did not regroup 1 hour into 60 minutes."),
        (cc(dh - 1, dm) if dh > 1 else None, "regrouped_twice", "Took one hour away too many."),
        (cc(dh, (dm + 10) % 60 or 10), "slip_in_subtraction", "Made a slip in the minutes."),
        (cc(dh, (dm + 50) % 60 or 10), "slip_in_subtraction", "Made a slip in the minutes."),
    ], [f"{fmt12(s)} to 12:00 noon, then to {fmt12(e)}", f"Total = {sh(cc(dh, dm))}"], {"s": s, "e": e}, sh, auto_slips=False)


@checker(duration_am_pm)
def _(p):
    n, t = 0, p["s"]
    while t < p["e"]:
        t += 1
        n += 1
    return F(cc(n // 60, n % 60))


@template(T, "intermediate", TM_FIND)
def finish_time_cross(r):
    s = r.randint(8, 11) * 60 + r.randrange(5, 60, 5)
    dh, dm = r.randint(2, 6), r.randrange(10, 60, 5)
    d = dh * 60 + dm
    e = s + d
    if e < 12 * 60 + 5 or e >= 1440 or s + d < 12 * 60:
        return None
    name = nm(r)
    ev = r.choice(["a hike", "a bus tour", "a camp activity", "a long film marathon"])
    stem = f"{ev.capitalize()} starts at {fmt12(s)} and lasts {dh} h {dm} min. {name} wants to know when it ends. At what time does it end?"
    return build(finish_time_cross, stem, e, [
        (day(e - 720), "wrong_am_pm", "Gave the right clock time but the wrong am or pm."),
        (day(s + dh * 60 + (s % 60 + dm) % 60 - s % 60), "forgot_to_carry_the_hour", "Did not add 1 hour for the minutes over 60."),
        (day(e + 10), "slip_in_addition", "Made a slip in the minutes."),
        (day(e - 5), "slip_in_addition", "Made a slip in the minutes."),
        (day(s - d), "subtracted_instead_of_added", "Took the time away instead of adding it."),
    ], [f"{fmt12(s)} + {dh} h = {fmt12(s + dh * 60)}", f"+ {dm} min = {fmt12(e)}"], {"s": s, "d": d}, fmt12, whole=True, auto_slips=False)


@checker(finish_time_cross)
def _(p):
    t = p["s"]
    for _ in range(p["d"]):
        t += 1
    return F(t)


@template(T, "intermediate", TM_FIND)
def start_time_backwards(r):
    e = r.randint(13, 20) * 60 + r.randrange(5, 60, 5)
    dh, dm = r.randint(1, 5), r.randrange(10, 60, 5)
    d = dh * 60 + dm
    s = e - d
    if s % 60 + dm == 0 or s < 12 * 60 + 5 or s // 60 >= e // 60:
        pass
    if s <= 60 or (s // 60 >= 12) != (e // 60 >= 12) and r.random() < 0.0:
        return None
    name = nm(r)
    stem = f"A show ended at {fmt12(e)} after running for {dh} h {dm} min. At what time did the show start?"
    return build(start_time_backwards, stem, s, [
        (day(e + d), "added_instead_of_subtracted", "Added the time instead of taking it away."),
        (day(e - dh * 60 - abs(e % 60 - dm)), "subtracted_smaller_minutes_from_larger", "Took the smaller minutes from the larger."),
        (day(s + 720), "wrong_am_pm", "Gave the right clock time but the wrong am or pm."),
        (day(s + 10), "slip_in_subtraction", "Made a slip in the minutes."),
        (day(s - 5), "slip_in_subtraction", "Made a slip in the minutes."),
    ], [f"{fmt12(e)} - {dh} h = {fmt12(e - dh * 60)}", f"- {dm} min = {fmt12(s)}"], {"e": e, "d": d}, fmt12, whole=True, auto_slips=False)


@checker(start_time_backwards)
def _(p):
    t = p["e"]
    for _ in range(p["d"]):
        t -= 1
    return F(t)


@template(T, "intermediate", TM_24, TM_FIND)
def duration_24h(r):
    s = r.randint(7, 12) * 60 + r.randrange(5, 60, 5)
    e = r.randint(14, 20) * 60 + r.randrange(0, 60, 5)
    d = e - s
    if d % 60 == 0:
        return None
    dh, dm = divmod(d, 60)
    sh = cshow("h", "min")
    name = nm(r)
    stem = f"A coach trip left at {fmt24(s)} and reached its destination at {fmt24(e)}. How long was the trip?"
    return build(duration_24h, stem, cc(dh, dm), [
        (cc(e // 60 - s // 60, abs(e % 60 - s % 60)), "subtracted_smaller_minutes_from_larger", "Took the smaller minutes from the larger."),
        (cc(dh, (e - s) % 100 % 60) if (e - s) % 100 % 60 and (e - s) % 100 % 60 != dm else None, "treated_time_as_decimal", "Subtracted the 24-hour times like ordinary numbers."),
        (cc(dh + 1, dm), "forgot_to_regroup", "Did not regroup 1 hour."),
        (cc(dh, (dm + 10) % 60 or 5), "slip_in_subtraction", "Made a slip in the minutes."),
        (cc(dh - 1, dm) if dh > 1 else None, "regrouped_twice", "Took one hour away too many."),
    ], [f"{fmt24(s)} to {fmt24(e)}", f"Duration = {sh(cc(dh, dm))}"], {"s": s, "e": e}, sh, auto_slips=False)


@checker(duration_24h)
def _(p):
    h1, m1, h2, m2 = p["s"] // 60, p["s"] % 60, p["e"] // 60, p["e"] % 60
    mins = (h2 - h1) * 60 + (m2 - m1)
    return F(cc(mins // 60, mins % 60))


@template(T, "intermediate", TM_SEC, TM_HM)
def repeat_task_time(r):
    m, s = r.randint(2, 4), r.randrange(5, 60, 5)
    n = r.randint(5, 14)
    T_ = n * (m * 60 + s)
    if T_ % 60 == 0:
        return None
    q, rem = divmod(T_, 60)
    sh = cshow("min", "s")
    name = nm(r)
    thing = r.choice(["song on a playlist", "lap round the track", "video clip", "round of a game"])
    stem = f"Each {thing} takes {m} min {s} s. {name} does it {n} times without a break. How long does it take altogether, in minutes and seconds?"
    return build(repeat_task_time, stem, cc(q, rem), [
        (cc(n * m + (n * s) // 100, (n * s) % 100), "used_100_s_in_a_minute", "Used 100 seconds in a minute."),
        (cc(n * m, n * s), "did_not_regroup_seconds", f"Left {n * s} seconds without changing to minutes."),
        (cc(q, (rem + 10) % 60 or 10), "slip_in_multiplication", "Made a slip in the seconds."),
        (cc(q + 1, rem), "slip_in_multiplication", "Made a slip in the minutes."),
        (cc(q - 1, rem) if q > 1 else None, "slip_in_multiplication", "Made a slip in the minutes."),
    ], [f"{m} min {s} s = {m * 60 + s} s", f"{n} × {m * 60 + s} = {T_} s", f"{T_} s = {sh(cc(q, rem))}"],
        {"m": m, "s": s, "n": n}, sh, auto_slips=False)


@checker(repeat_task_time)
def _(p):
    T_ = sum(p["m"] * 60 + p["s"] for _ in range(p["n"]))
    return F(cc(T_ // 60, T_ % 60))


# ================================================================ time: competent

@template(T, "competent", TM_FIND)
def journey_legs(r):
    s = r.randint(5, 8) * 60 + r.randrange(5, 60, 5)
    w1, w2 = r.randrange(10, 40, 5), r.randrange(5, 25, 5)
    bh, bm = r.randint(1, 3), r.randrange(10, 55, 5)
    tot = w1 + w2 + bh * 60 + bm
    e = s + tot
    if e >= 1440 or e < 12 * 60 + 5:
        return None
    name = nm(r)
    stem = (f"{name} leaves home at {fmt12(s)}, walks for {w1} min to the bus stop, waits {w2} min for the bus and then "
            f"travels {bh} h {bm} min on the bus to a theme park. At what time does {name} arrive?")
    return build(journey_legs, stem, e, [
        (day(e - w2), "left_out_the_waiting_time", "Left out the waiting time."),
        (day(e - w1), "left_out_the_walk", "Left out the walk."),
        (day(e - 720), "wrong_am_pm", "Gave the right clock time but the wrong am or pm."),
        (day(e + 10), "slip_in_addition", "Made a slip in the addition."),
        (day(e - 5), "slip_in_addition", "Made a slip in the addition."),
    ], [f"Total time = {w1} + {w2} + {bh * 60 + bm} = {tot} min = {tot // 60} h {tot % 60} min", f"{fmt12(s)} + {tot // 60} h {tot % 60} min = {fmt12(e)}"],
        {"s": s, "legs": [w1, w2, bh * 60 + bm]}, fmt12, whole=True, auto_slips=False)


@checker(journey_legs)
def _(p):
    t = p["s"]
    for leg in p["legs"]:
        for _ in range(leg):
            t += 1
    return F(t)


@template(T, "competent", TM_FIND)
def latest_departure(r):
    arrive = r.randint(8, 10) * 60 + r.randrange(0, 60, 15)
    a, b, c = r.randrange(10, 35, 5), r.randrange(20, 50, 5), r.randrange(5, 20, 5)
    tot = a + b + c
    s = arrive - tot
    name = nm(r)
    stem = (f"{name} must reach school by {fmt12(arrive)}. The walk to the MRT station takes {a} min, the train ride takes "
            f"{b} min and the walk to school takes {c} min. {name} plans no waiting time. What is the latest time {name} can leave home?")
    return build(latest_departure, stem, s, [
        (day(arrive + tot), "added_instead_of_subtracted", "Added the travelling time instead of taking it away."),
        (day(arrive - (tot - c)), "left_out_one_leg", "Left out the last walk."),
        (day(arrive - (tot - a)), "left_out_one_leg", "Left out the first walk."),
        (day(s + 5), "slip_in_subtraction", "Made a slip in the subtraction."),
        (day(s - 10), "slip_in_subtraction", "Made a slip in the subtraction."),
    ], [f"Total travel = {a} + {b} + {c} = {tot} min", f"{fmt12(arrive)} - {tot} min = {fmt12(s)}"],
        {"arrive": arrive, "legs": [a, b, c]}, fmt12, whole=True, auto_slips=False)


@checker(latest_departure)
def _(p):
    t = p["arrive"]
    for leg in p["legs"]:
        for _ in range(leg):
            t -= 1
    return F(t)


@template(T, "competent", TM_FIND, TM_HM)
def clock_gains(r):
    start = r.randint(7, 9) * 60
    hours = r.randint(4, 10)
    g = r.choice([2, 3, 4, 5])
    if start + hours * 60 + hours * g >= 1440:
        return None
    name = nm(r)
    if r.random() < 0.5:
        real = start + hours * 60
        shown = real + hours * g
        stem = (f"{name}'s clock gains {g} min every hour. It is set to the correct time at {fmt12(start)}. "
                f"What time will the clock show when the correct time is {fmt12(real)}?")
        return build(clock_gains, stem, shown, [
            (real, "ignored_the_gain", "Ignored the minutes gained."),
            (real - hours * g, "subtracted_the_gain", "Took the gain away instead of adding it."),
            (real + g, "counted_gain_once", f"Added only {g} min."),
            (real + hours * g + 5, "slip_in_addition", "Made a slip in the addition."),
            (real + (hours + 1) * g, "counted_one_hour_too_many", "Counted one hour too many."),
        ], [f"Hours passed = {hours}", f"Gain = {hours} × {g} = {hours * g} min", f"Clock shows {fmt12(shown)}"],
            {"mode": "a", "start": start, "hours": hours, "g": g}, fmt12, whole=True, auto_slips=False)
    real = start + hours * 60
    shown = real + hours * g
    stem = (f"{name}'s clock gains {g} min every hour. It is set to the correct time at {fmt12(start)}. "
            f"Later the clock shows {fmt12(shown)}. What is the correct time then?")
    return build(clock_gains, stem, real, [
        (shown, "gave_the_clock_time", "Gave the time shown on the clock."),
        (shown + hours * g, "added_the_gain", "Added the gain instead of taking it away."),
        (shown - g, "counted_gain_once", f"Took away only {g} min."),
        (real + 5, "slip_in_subtraction", "Made a slip in the subtraction."),
        (real - 10, "slip_in_subtraction", "Made a slip in the subtraction."),
    ], [f"Each real hour the clock shows {60 + g} min", f"Clock time passed = {shown - start} min = {hours} × {60 + g}", f"Real time passed = {hours} h",
        f"Correct time = {fmt12(real)}"], {"mode": "b", "start": start, "hours": hours, "g": g}, fmt12, whole=True, auto_slips=False)


@checker(clock_gains)
def _(p):
    t_real, t_clk = p["start"], p["start"]
    for _ in range(p["hours"]):
        t_real += 60
        t_clk += 60 + p["g"]
    return F(t_clk if p["mode"] == "a" else t_real)


@template(T, "competent", TM_SEC, TM_HM)
def machine_rate(r):
    s = r.choice([6, 8, 10, 12, 15, 18, 20])
    n = r.choice([x for x in range(200, 1500, 50) if (x * s) % 60 == 0 and (x * s) // 60 >= 70])
    T_ = n * s
    mins = T_ // 60
    q, rem = divmod(mins, 60)
    if rem == 0:
        return None
    sh = cshow("h", "min")
    name = nm(r)
    item = r.choice(["biscuits", "cards", "stickers", "pencils"])
    stem = f"A machine packs one box of {item} every {s} seconds. How long does it take to pack {n} boxes, in hours and minutes?"
    return build(machine_rate, stem, cc(q, rem), [
        (cc((T_ // 100) // 60, (T_ // 100) % 60) if (T_ // 100) % 60 else None, "divided_by_100", "Divided by 100 instead of 60."),
        (cc(T_ // 60, 0), "mixed_up_minutes_and_hours", "Gave the number of minutes as the number of hours."),
        (cc(q, (rem + 10) % 60 or 10), "slip_in_division", "Made a slip in the minutes."),
        (cc(q + 1, rem), "slip_in_division", "Made a slip in the hours."),
        (cc(q - 1, rem) if q > 1 else None, "slip_in_division", "Made a slip in the hours."),
    ], [f"{n} × {s} = {T_} s", f"{T_} ÷ 60 = {mins} min", f"{mins} min = {sh(cc(q, rem))}"], {"n": n, "s": s}, sh, auto_slips=False)


@checker(machine_rate)
def _(p):
    secs = sum(p["s"] for _ in range(p["n"]))
    mins = secs // 60
    return F(cc(mins // 60, mins % 60))


@template(T, "competent", TM_FIND)
def film_schedule(r):
    s = r.randint(11, 14) * 60 + r.randrange(0, 60, 5)
    d1, d2 = r.randrange(80, 140, 5), r.randrange(95, 160, 5)
    gap = r.randrange(15, 45, 5)
    e = s + d1 + gap + d2
    if e >= 1440:
        return None
    name = nm(r)
    stem = (f"{name} watches two films at the cinema. The first film starts at {fmt12(s)} and lasts {d1 // 60} h {d1 % 60} min. "
            f"After {a_an(gap)} {gap}-minute break, the second film starts and lasts {d2 // 60} h {d2 % 60} min. At what time does the second film end?")
    return build(film_schedule, stem, e, [
        (day(e - gap), "left_out_the_break", "Left out the break between the films."),
        (day(e - d1), "left_out_a_film", "Left out the first film."),
        (day(e + 10), "slip_in_addition", "Made a slip in the addition."),
        (day(e - 5), "slip_in_addition", "Made a slip in the addition."),
        (day(e - 720), "wrong_am_pm", "Gave the right clock time but the wrong am or pm."),
    ], [f"Total = {d1} + {gap} + {d2} = {d1 + gap + d2} min", f"{fmt12(s)} + {(d1 + gap + d2) // 60} h {(d1 + gap + d2) % 60} min = {fmt12(e)}"],
        {"s": s, "parts": [d1, gap, d2]}, fmt12, whole=True, auto_slips=False)


@checker(film_schedule)
def _(p):
    t = p["s"]
    for x in p["parts"]:
        for _ in range(x):
            t += 1
    return F(t)


@template(T, "competent", TM_HM)
def training_total(r):
    x = r.choice([35, 40, 45, 50, 55])
    y = r.randint(3, 6)
    w = r.randint(3, 8)
    T_ = x * y * w
    q, rem = divmod(T_, 60)
    if rem == 0:
        return None
    sh = cshow("h", "min")
    name = nm(r)
    stem = f"{name} trains for {x} min a day on {y} days every week. How long does {name} train in {plural(w, 'week')}, in hours and minutes?"
    return build(training_total, stem, cc(q, rem), [
        (cc(T_ // 100, T_ % 100), "used_100_for_60", "Divided by 100 instead of 60."),
        (cc((x * y) // 60, (x * y) % 60), "forgot_the_weeks", "Worked out one week only."),
        (cc(q, (rem + 10) % 60 or 10), "slip_in_multiplication", "Made a slip in the minutes."),
        (cc(q + 1, rem), "slip_in_multiplication", "Made a slip in the hours."),
        (cc(q - 1, rem) if q > 1 else None, "slip_in_multiplication", "Made a slip in the hours."),
    ], [f"{x} × {y} × {w} = {T_} min", f"{T_} min = {sh(cc(q, rem))}"], {"x": x, "y": y, "w": w}, sh, auto_slips=False)


@checker(training_total)
def _(p):
    total = 0
    for _ in range(p["w"]):
        for _ in range(p["y"]):
            total += p["x"]
    return F(cc(total // 60, total % 60))


# ================================================================ Group C gap fills: lengths in cm (ordering, ruler drawing)
from figures_gapC import ruler_line_svg, ruler_lines_svg  # noqa: E402

LEN_OBJ = ["pencil", "ribbon", "rope", "stick", "strip of paper", "string", "straw", "eraser", "crayon", "leaf",
           "twig", "spring", "scarf", "wire", "bookmark", "ruler"]
LONG_WORDS = {"longest": max, "shortest": min}


def _first_digit_pick(vals, ask):
    """The item a child picks by looking only at the first digit of each number."""
    key = [int(str(v)[0]) for v in vals]
    pick = max(key) if ask == "longest" else min(key)
    idx = [i for i, k in enumerate(key) if k == pick]
    return idx[0] if len(idx) == 1 else None


@template(T, "basic", LM + "02")
def cm_longest_shortest(r):
    """Compare four lengths in cm: which is the longest / shortest."""
    name = nm(r)
    objs = r.sample(LEN_OBJ, 4)
    vals = r.sample(range(4, 49), 4)
    ask = r.choice(["longest", "shortest"])
    t = vals.index(max(vals) if ask == "longest" else min(vals))
    fd = _first_digit_pick(vals, ask)
    if fd is None or fd == t:
        return None
    opp = vals.index(min(vals) if ask == "longest" else max(vals))
    rest = [i for i in range(4) if i not in (t, fd, opp)]
    order = [fd, opp] + rest
    why = ["Compared only the first digit of each number.", f"Picked the {'shortest' if ask == 'longest' else 'longest'} instead.",
           "Did not compare all the lengths."]
    tags = ["compared_first_digits_only", "picked_the_opposite", "did_not_compare_all"]
    stem = (f"{name} measures four things: the {objs[0]} is {vals[0]} cm long, the {objs[1]} is {vals[1]} cm, "
            f"the {objs[2]} is {vals[2]} cm and the {objs[3]} is {vals[3]} cm. Which one is the {ask}?")
    wrong = [(i + 1, tags[n] if n < 2 else tags[2], why[n] if n < 2 else why[2]) for n, i in enumerate(order)]
    return build(cm_longest_shortest, stem, t + 1, wrong,
                 [f"Compare the whole numbers: {', '.join(str(v) for v in vals)}.",
                  f"The {ask} length is {max(vals) if ask == 'longest' else min(vals)} cm, the {objs[t]}."],
                 {"vals": vals, "ask": ask}, lambda v: objs[int(v) - 1], whole=True, auto_slips=False)


@checker(cm_longest_shortest)
def _(p):
    order = sorted(range(4), key=lambda i: p["vals"][i])
    return F((order[-1] if p["ask"] == "longest" else order[0]) + 1)


@template(T, "intermediate", LM + "02")
def cm_second_longest(r):
    """Second longest / second shortest of four lengths in cm."""
    name = nm(r)
    objs = r.sample(LEN_OBJ, 4)
    vals = r.sample(range(5, 60), 4)
    ask = r.choice(["second longest", "second shortest"])
    srt = sorted(range(4), key=lambda i: vals[i])
    t = srt[-2] if ask == "second longest" else srt[1]
    other = srt[1] if ask == "second longest" else srt[-2]
    ext = srt[-1] if ask == "second longest" else srt[0]
    far = srt[0] if ask == "second longest" else srt[-1]
    stem = (f"The lengths of four things in {name}'s pencil case are: {objs[0]} {vals[0]} cm, {objs[1]} {vals[1]} cm, "
            f"{objs[2]} {vals[2]} cm and {objs[3]} {vals[3]} cm. Which is the {ask}?")
    wrong = [(other + 1, "counted_from_the_wrong_end", "Counted from the wrong end of the ordered list."),
             (ext + 1, "gave_the_extreme_one", f"Gave the {'longest' if ask == 'second longest' else 'shortest'} instead of the second."),
             (far + 1, "gave_the_other_extreme", "Gave the item at the other end of the list.")]
    return build(cm_second_longest, stem, t + 1, wrong,
                 [f"Order from shortest to longest: {', '.join(f'{vals[i]} cm' for i in srt)}.",
                  f"The {ask} is the {objs[t]}, {vals[t]} cm."], {"vals": vals, "ask": ask},
                 lambda v: objs[int(v) - 1], whole=True, auto_slips=False)


@checker(cm_second_longest)
def _(p):
    v = p["vals"]
    ranked = sorted(range(4), key=lambda i: -v[i])  # longest first
    return F((ranked[1] if p["ask"] == "second longest" else ranked[2]) + 1)


@template(T, "intermediate", LM + "02")
def cm_how_much_longer(r):
    """How much longer is the longest than the shortest of three lengths in cm."""
    name = nm(r)
    objs = r.sample(LEN_OBJ, 3)
    vals = r.sample(range(6, 60), 3)
    s = sorted(vals)
    ans = s[2] - s[0]
    i_long, i_short = vals.index(s[2]), vals.index(s[0])
    stem = (f"{name} has {a_an(objs[0])} {objs[0]} that is {vals[0]} cm long, {a_an(objs[1])} {objs[1]} that is {vals[1]} cm long and "
            f"{a_an(objs[2])} {objs[2]} that is {vals[2]} cm long. How much longer is the {objs[i_long]} than the {objs[i_short]}, in cm?")
    return build(cm_how_much_longer, stem, ans, [
        (s[2] + s[0], "added_instead_of_subtracting", "Added the two lengths."),
        (s[1] - s[0], "used_the_middle_length", "Compared the shortest with the middle one."),
        (s[2] - s[1], "used_the_middle_length", "Compared the longest with the middle one."),
        (ans + 10, "slip_ten_out", "Made a slip of 10 when subtracting."),
        (ans - 10, "slip_ten_out", "Made a slip of 10 when subtracting."),
    ], [f"{s[2]} - {s[0]} = {ans} cm"], {"vals": vals}, usd("cm"), whole=True, auto_slips=False)


@checker(cm_how_much_longer)
def _(p):
    best = 0
    for a in p["vals"]:
        for b in p["vals"]:
            best = max(best, a - b)
    return F(best)


@template(T, "competent", LM + "02")
def cm_chain_lengths(r):
    """Three pieces defined by 'longer than' and 'shorter than' steps; find the gap between longest and shortest."""
    name = nm(r)
    obj = r.choice(["ribbon", "rope", "string", "wire", "strip of cloth"])
    a = r.randint(12, 40)
    d1, d2 = r.randint(4, 15), r.randint(4, 24)
    b, c = a + d1, a + d1 - d2
    if c <= 0 or d1 == d2:
        return None
    lo, hi = min(a, b, c), max(a, b, c)
    ans = hi - lo
    stem = (f"{name} cuts three pieces of {obj}. Piece 1 is {a} cm long. Piece 2 is {d1} cm longer than Piece 1. "
            f"Piece 3 is {d2} cm shorter than Piece 2. How much longer is the longest piece than the shortest piece, in cm?")
    return build(cm_chain_lengths, stem, ans, [
        (d1 + d2, "added_both_changes", "Added the two differences without finding each length."),
        (abs(d1 - d2) if abs(d1 - d2) != ans else None, "compared_only_piece_1_and_3", "Compared Piece 1 with Piece 3 only."),
        (min(b - a, b - c), "compared_with_the_wrong_piece", "Compared the longest piece with the wrong piece instead of the shortest."),
        (ans + 5, "arithmetic_slip", "Made a small arithmetic slip."),
        (ans - 1, "arithmetic_slip", "Made a small arithmetic slip."),
    ], [f"Piece 2 = {a} + {d1} = {b} cm", f"Piece 3 = {b} - {d2} = {c} cm", f"Longest - shortest = {hi} - {lo} = {ans} cm"],
        {"a": a, "d1": d1, "d2": d2}, usd("cm"), whole=True, auto_slips=False)


@checker(cm_chain_lengths)
def _(p):
    ps = [p["a"]]
    ps.append(ps[0] + p["d1"])
    ps.append(ps[1] - p["d2"])
    return F(max(ps) - min(ps))


def _ruler_q(r, fn, start_choices, stem_fmt):
    name = nm(r)
    obj = r.choice(["pencil", "strip of paper", "ribbon", "eraser", "matchstick", "feather", "leaf", "straw", "twig"])
    start = r.choice(start_choices)
    whole_cm = r.randint(3, 11)
    off = r.choice([1, 2, 3, 7, 8, 9])
    end10 = (start + whole_cm) * 10 + off
    if end10 > 150 - 4:
        return None
    ln = whole_cm + (1 if off > 5 else 0)
    end_round = start + ln
    nb = ln - 1 if off > 5 else ln + 1  # the neighbouring whole number a careless rounding gives
    stem = stem_fmt.format(name=name, obj=obj)
    wrong = [(nb, "rounded_the_wrong_way", "Rounded to the wrong whole number of centimetres."),
             (end_round if start else ln + 1, "read_only_the_right_end" if start else "counted_marks_not_gaps",
              "Read the right end of the line without subtracting the start mark." if start else "Counted the marks instead of the gaps."),
             (ln - 1 if ln - 1 != nb else ln + 1, "counted_gaps_off_by_one", "Counted one gap too few or too many."),
             (ln + 2, "misread_scale", "Misread the end mark.")]
    return build(fn, stem, ln, wrong,
                 [f"The line starts at {start} cm. Its right end is at about {end10 / 10:g} cm.",
                  f"Length = {end10 / 10:g} - {start} = {(end10 - start * 10) / 10:g} cm, which is {ln} cm to the nearest cm."],
                 {"start": start, "end10": end10}, usd("cm"), whole=True, auto_slips=False,
                 figure=ruler_line_svg(start, end10))


def _ruler_check(p):
    length10 = p["end10"] - 10 * p["start"]
    return F(min(range(0, 16), key=lambda k: abs(10 * k - length10)))


@template(T, "basic", LM + "03")
def ruler_nearest_cm(r):
    """Measure a line segment from 0 on a ruler, to the nearest cm."""
    return _ruler_q(r, ruler_nearest_cm, [0],
                    "{name} measures a {obj} with a ruler, starting from the 0 mark, as shown. What is the length of the {obj} to the nearest cm?")


checker(ruler_nearest_cm)(_ruler_check)


@template(T, "intermediate", LM + "03")
def ruler_nearest_cm_offset(r):
    """Measure a line segment that starts away from 0, to the nearest cm."""
    return _ruler_q(r, ruler_nearest_cm_offset, [1, 2, 3, 4, 5],
                    "{name} measures a {obj} with a ruler but starts from a mark that is not 0, as shown. "
                    "What is the length of the {obj} to the nearest cm?")


checker(ruler_nearest_cm_offset)(_ruler_check)


@template(T, "intermediate", LM + "03")
def which_line_is_n_cm(r):
    """Four lines drawn against a ruler: which one is exactly N cm long."""
    name = nm(r)
    n = r.randint(4, 10)
    lines = []

    def mk_line(length, start=None):
        s = r.randint(0, 15 - length) if start is None else start
        return (s, s + length)
    right = mk_line(n)
    dec = [(r.randint(1, n - 1), n),  # ends at N but starts away from 0
           mk_line(n + 1), mk_line(n - 1)]
    if dec[0][0] < 1 or n - dec[0][0] == n:
        return None
    pos = r.randrange(4)
    allv = dec[:]
    allv.insert(pos, right)
    if len({b - a for a, b in allv}) < 4:
        return None
    lines = [("ABCD"[i], a, b) for i, (a, b) in enumerate(allv)]
    tags = [("read_only_the_right_end", f"Read the end mark (it is {n}) without subtracting where the line starts."),
            ("counted_one_too_many", f"Picked the line that is {n + 1} cm long."),
            ("counted_one_too_few", f"Picked the line that is {n - 1} cm long.")]
    wrong = []
    kinds = [0, 1, 2]  # dec[0] ends at N, dec[1] is N+1 long, dec[2] is N-1 long
    kinds.insert(pos, None)
    for i in range(4):
        if i == pos:
            continue
        k = kinds[i]
        wrong.append((i + 1, tags[k][0], tags[k][1]))
    wrong.sort(key=lambda w: [t[0] for t in tags].index(w[1]))
    stem = f"{name} measures four lines, A to D, with a ruler. Which line is exactly {n} cm long?"
    return build(which_line_is_n_cm, stem, pos + 1, wrong,
                 [f"Length = right end - left end for each line.", f"Only line {'ABCD'[pos]} has right end - left end = {n} cm."],
                 {"lines": [list(x) for x in allv], "n": n}, lambda v: "ABCD"[int(v) - 1], whole=True, auto_slips=False,
                 figure=ruler_lines_svg(lines))


@checker(which_line_is_n_cm)
def _(p):
    ok = [i + 1 for i, (a, b) in enumerate(p["lines"]) if len(range(a, b)) == p["n"]]
    return F(ok[0]) if len(ok) == 1 else None


@template(T, "competent", LM + "03")
def ruler_then_total(r):
    """Read a line off the ruler to the nearest cm, then use it in a two-step length problem."""
    name = nm(r)
    start = r.choice([0, 1, 2, 3])
    whole_cm = r.randint(3, 9)
    off = r.choice([1, 2, 3, 7, 8, 9])
    end10 = (start + whole_cm) * 10 + off
    ln = whole_cm + (1 if off > 5 else 0)
    k = r.randint(2, 4)
    d = r.randint(3, 12)
    ans = ln + k * ln + d
    stem = (f"{name} measures the line on the ruler to the nearest cm. {name} then draws a second line that is {k} times as long "
            f"and a third line that is {d} cm long. {name} joins all three lines end to end. What is the total length, in cm?")
    return build(ruler_then_total, stem, ans, [
        (end10 // 10 + k * (end10 // 10) + d, "read_only_the_right_end", "Used the right-end mark as the length of the line."),
        (k * ln + d, "left_out_the_first_line", "Left out the first line."),
        (ln + k + d, "added_k_instead_of_multiplying", "Added the number of times instead of multiplying."),
        (ans + 10, "slip_ten_out", "Made a slip of 10."),
        (ans - 1, "arithmetic_slip", "Made a small arithmetic slip."),
    ], [f"The first line is {ln} cm.", f"Second line = {k} x {ln} = {k * ln} cm.", f"Total = {ln} + {k * ln} + {d} = {ans} cm"],
        {"start": start, "end10": end10, "k": k, "d": d}, usd("cm"), whole=True, auto_slips=False,
        figure=ruler_line_svg(start, end10))


@checker(ruler_then_total)
def _(p):
    first = _ruler_check(p)
    total = first
    for _ in range(p["k"]):
        total += first
    return total + p["d"]
