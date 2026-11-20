"""Data analysis (math-data-analysis): average of a set of data, at basic, intermediate and competent levels."""
from itertools import combinations

from common import *

T = "math-data-analysis"
O = "math-data-analysis-average-of-a-set-of-data-"
AVG, REL = O + "01", O + "02"

CONTEXTS = [("the time taken by a pupil to run 100 m on each of the days", "seconds", (14, 24)),
            ("the marks scored in a test by a group of pupils", "marks", (30, 95)),
            ("the masses of a group of parcels", "kg", (8, 60)),
            ("the heights of a group of plants", "cm", (20, 150)),
            ("the amounts of pocket money saved by a group of children", "dollars", (15, 90)),
            ("the numbers of books read by a group of pupils in a month", "books", (3, 25))]


def brute(pred, hi=20000):
    return next((F(n) for n in range(1, hi + 1) if pred(n)), None)


def slipn(v, d=1):
    return [(v + d, "careless_slip", "Made a slip in the calculation."),
            (v - d, "careless_slip", "Made a slip in the calculation.")]


def listing(xs):
    return ", ".join(map(str, xs[:-1])) + f" and {xs[-1]}"


def sample_list(r, n, lo, hi):
    """n values in [lo, hi] whose sum divides by n."""
    while True:
        xs = [r.randint(lo, hi) for _ in range(n)]
        if sum(xs) % n == 0 and len(set(xs)) > 1:
            return xs


# ---------------------------------------------------------------- basic

@template(T, "basic", AVG)
def average_direct(r):
    """math-pat-average-direct"""
    n = r.choice([4, 5, 6])
    what, u, (lo, hi) = r.choice(CONTEXTS)
    xs = sample_list(r, n, lo, hi)
    avg = sum(xs) // n
    if r.random() < 0.5:
        stem = f"The following numbers show {what} (in {u}): {listing(xs)}. What is the average of these numbers?"
    else:
        stem = f"What is the average of {listing(xs)}?"
    med = sorted(xs)[n // 2] if n % 2 else F(sorted(xs)[n // 2 - 1] + sorted(xs)[n // 2], 2)
    return build(average_direct, stem, avg, [
        (sum(xs), "gave_the_total", "Added the numbers but did not divide."),
        (F(sum(xs), n - 1), "divided_by_wrong_count", f"Divided by {n - 1} instead of {n}."),
        (med if med != avg else None, "gave_the_median", "Gave the middle number."),
        (F(sum(xs), n + 1), "divided_by_wrong_count", f"Divided by {n + 1} instead of {n}."),
        (F(max(xs) + min(xs), 2), "averaged_the_biggest_and_smallest", "Found the average of the biggest and smallest numbers only."),
        *slipn(avg, 1), *slipn(avg, 2),
    ], [f"Total = {' + '.join(map(str, xs))} = {sum(xs)}", f"Average = {sum(xs)} ÷ {n} = {avg}"], {"xs": xs}, whole=True, auto_slips=False)


@checker(average_direct)
def _(q):
    xs = q["xs"]
    # the value x with x * n = total
    return brute(lambda x: x * len(xs) == sum(xs), 2000)


@template(T, "basic", AVG)
def average_from_total(r):
    n = r.randint(3, 12)
    avg = r.randint(8, 90)
    tot = n * avg
    nm = r.choice(NAMES)
    ctx = r.choice([
        (f"The total mass of {n} bags of rice is {tot} kg. What is the average mass of a bag, in kg?", "kg"),
        (f"{nm} scored a total of {plural(tot, 'point')} in {n} games. What was the average number of points per game?", "points"),
        (f"{n} children saved ${tot} altogether. What is the average amount saved by a child, in dollars?", "dollars"),
        (f"A bakery sold {tot} cakes in {n} days. What was the average number of cakes sold per day?", "cakes"),
    ])
    return build(average_from_total, ctx[0], avg, [
        (tot * n, "multiplied_instead_of_divided", "Multiplied the total by the number of items."),
        (F(tot, n + 1), "divided_by_wrong_count", f"Divided by {n + 1}."),
        (F(tot, n - 1), "divided_by_wrong_count", f"Divided by {n - 1}."),
        (tot - n, "subtracted", "Subtracted the number of items from the total."),
        *slipn(avg, 1), *slipn(avg, 2),
    ], [f"Average = total ÷ number = {tot} ÷ {n} = {avg}"], {"tot": tot, "n": n}, whole=True, auto_slips=False)


@checker(average_from_total)
def _(q):
    return brute(lambda x: x * q["n"] == q["tot"], 2000)


@template(T, "basic", REL)
def total_from_average(r):
    n = r.randint(3, 15)
    avg = r.randint(6, 80)
    nm = r.choice(NAMES)
    ctx = r.choice([
        f"The average mass of {n} boxes is {avg} kg. What is the total mass of the {n} boxes, in kg?",
        f"{nm} read an average of {plural(avg, 'page')} a day for {n} days. How many pages did {nm} read altogether?",
        f"The average mark of {n} pupils in a quiz is {avg}. What is the total of their marks?",
        f"The average cost of {n} meals is ${avg}. How much do the {n} meals cost altogether, in dollars?",
    ])
    tot = n * avg
    return build(total_from_average, ctx, tot, [
        (F(avg, n) if avg % n == 0 else avg + n, "divided_instead_of_multiplied", "Divided the average by the number of items."),
        (avg + n, "added", "Added the average and the number of items."),
        (tot + avg, "extra_item", "Counted one item too many."),
        (tot - avg, "item_missing", "Counted one item too few."),
        *slipn(tot, 10),
    ], [f"Total = average × number = {avg} × {n} = {tot}"], {"avg": avg, "n": n}, whole=True, auto_slips=False)


@checker(total_from_average)
def _(q):
    return F(sum(q["avg"] for _ in range(q["n"])))


@template(T, "basic", REL)
def count_from_total_average(r):
    n = r.randint(3, 15)
    avg = r.randint(5, 60)
    tot = n * avg
    nm = r.choice(NAMES)
    ctx = r.choice([
        f"The total mass of some boxes is {tot} kg. The average mass of a box is {avg} kg. How many boxes are there?",
        f"{nm} read {plural(tot, 'page')} in some days. {nm} read an average of {plural(avg, 'page')} a day. For how many days did {nm} read?",
        f"A group of children saved ${tot} altogether. Each child saved ${avg} on average. How many children are in the group?",
    ])
    return build(count_from_total_average, ctx, n, [
        (tot * avg, "multiplied_instead_of_divided", "Multiplied the total by the average."),
        (tot - avg, "subtracted", "Subtracted the average from the total."),
        (tot + avg, "added", "Added the total and the average."),
        *slipn(n, 1), *slipn(n, 2),
    ], [f"Number = total ÷ average = {tot} ÷ {avg} = {n}"], {"tot": tot, "avg": avg}, whole=True, auto_slips=False)


@checker(count_from_total_average)
def _(q):
    return brute(lambda n: n * q["avg"] == q["tot"], 2000)


@template(T, "basic", AVG)
def average_table(r):
    n = r.choice([4, 5])
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"][:n]
    xs = sample_list(r, n, 10, 60)
    avg = sum(xs) // n
    nm = r.choice(NAMES)
    rows = ", ".join(f"{d} {x}" for d, x in zip(days, xs))
    stem = f"{nm} counted the visitors to a shop each day: {rows}. What was the average number of visitors per day?"
    return build(average_table, stem, avg, [
        (sum(xs), "gave_the_total", "Gave the total."),
        (F(sum(xs), n + 1), "divided_by_wrong_count", f"Divided by {n + 1}."),
        (max(xs), "gave_the_largest", "Gave the largest number."),
        (F(sum(xs), n - 1), "divided_by_wrong_count", f"Divided by {n - 1}."),
        *slipn(avg, 1), *slipn(avg, 2),
    ], [f"Total = {sum(xs)}", f"Average = {sum(xs)} ÷ {n} = {avg}"], {"xs": xs}, whole=True, auto_slips=False)


@checker(average_table)
def _(q):
    return brute(lambda x: x * len(q["xs"]) == sum(q["xs"]), 2000)


# ---------------------------------------------------------------- intermediate

@template(T, "intermediate", REL, weight=2)
def find_missing_value(r):
    """math-pat-average-find-missing"""
    n = r.choice([4, 5, 6])
    avg = r.randint(40, 90)
    known = [r.randint(avg - 25, avg + 20) for _ in range(n - 1)]
    last = avg * n - sum(known)
    if last < 10 or last > 100 or last == avg:
        return None
    nm = r.choice(NAMES)
    unit_ = r.choice(["marks", "points"])
    stem = (f"{nm} took {n} tests. The scores for the first {n - 1} tests were {listing(known)} {unit_}. "
            f"The average score for all {n} tests was {avg} {unit_}. What was the score for the last test?")
    return build(find_missing_value, stem, last, [
        (avg, "gave_the_average", "Gave the average."),
        (F(sum(known), n - 1), "averaged_the_known_values", f"Found the average of the first {n - 1} scores."),
        (F(avg * n - sum(known) + avg, 1) if False else avg * (n - 1) - sum(known), "used_wrong_total", f"Used {avg} × {n - 1} as the total."),
        (F(avg * n, n) + (avg * n - sum(known)) if False else abs(sum(known) - avg * n + 2 * avg) or None, "added_instead_of_subtracted", "Made a sign error."),
        *slipn(last, 1), *slipn(last, 2),
    ], [f"Total of all {n} scores = {avg} × {n} = {avg * n}", f"Total of the first {n - 1} = {sum(known)}", f"Last score = {avg * n} − {sum(known)} = {last}"],
        {"known": known, "avg": avg, "n": n}, unit(unit_), whole=True, auto_slips=False)


@checker(find_missing_value)
def _(q):
    return brute(lambda x: F(sum(q["known"]) + x, q["n"]) == q["avg"], 3000)


@template(T, "intermediate", REL)
def item_joins_or_leaves(r):
    n = r.randint(4, 9)
    join = r.random() < 0.5
    nm = r.choice(NAMES)
    th = r.choice([("pupils", "mass", "kg", (34, 46), (28, 60)),
                   ("players", "height", "cm", (150, 168), (140, 185)),
                   ("workers", "age", "years", (30, 45), (22, 62))])
    A = r.randint(*th[3])
    lo_v, hi_v = th[4]
    if join:
        newv = r.randint(max(lo_v, A + 3), hi_v)
        A2 = F(A * n + newv, n + 1)
        if A2.denominator != 1:
            return None
        A2 = int(A2)
        stem = (f"The average {th[1]} of {n} {th[0]} is {A} {th[2]}. When another person joins them, "
                f"the average {th[1]} of all {n + 1} becomes {A2} {th[2]}. What is the {th[1]} of the new person?")
        ans = newv
        wrong = [(A2, "gave_the_new_average", "Gave the new average."),
                 (A2 - A, "gave_the_change_in_average", "Gave the change in the average."),
                 (A2 * n - A * n, "used_wrong_count", f"Used {n} instead of {n + 1} for the new total."),
                 *slipn(ans, 1), *slipn(ans, 2)]
        steps = [f"Old total = {A} × {n} = {A * n}", f"New total = {A2} × {n + 1} = {A2 * (n + 1)}", f"New person = {A2 * (n + 1)} − {A * n} = {ans}"]
    else:
        gone = r.randint(lo_v, hi_v)
        A2 = F(A * n - gone, n - 1)
        if A2.denominator != 1 or gone == A:
            return None
        A2 = int(A2)
        stem = (f"The average {th[1]} of {n} {th[0]} is {A} {th[2]}. After one person leaves, the average {th[1]} of the remaining {n - 1} "
                f"is {A2} {th[2]}. What is the {th[1]} of the person who left?")
        ans = gone
        wrong = [(A2, "gave_the_new_average", "Gave the new average."),
                 (abs(A - A2), "gave_the_change_in_average", "Gave the change in the average."),
                 (A * n - A2 * n, "used_wrong_count", f"Used {n} instead of {n - 1} for the new total."),
                 *slipn(ans, 1), *slipn(ans, 2)]
        steps = [f"Old total = {A} × {n} = {A * n}", f"New total = {A2} × {n - 1} = {A2 * (n - 1)}", f"Person who left = {A * n} − {A2 * (n - 1)} = {ans}"]
    return build(item_joins_or_leaves, stem, ans, wrong, steps, {"n": n, "A": A, "A2": A2, "join": join},
                 lambda x: f"{frac(x)} {noun(x, th[2][:-1], th[2]) if th[2] == 'years' else th[2]}",
                 whole=True, auto_slips=False)


@checker(item_joins_or_leaves)
def _(q):
    n, A, A2 = q["n"], q["A"], q["A2"]
    if q["join"]:
        return brute(lambda v: F(A * n + v, n + 1) == A2, 5000)
    return brute(lambda v: F(A * n - v, n - 1) == A2, 5000)


@template(T, "intermediate", REL)
def subgroup_average(r):
    n1, n2 = r.randint(2, 6), r.randint(2, 6)
    a1, a2 = r.randint(20, 80), r.randint(20, 80)
    if a1 == a2 or F(n1 * a1 + n2 * a2, n1 + n2).denominator != 1:
        return None
    avg = (n1 * a1 + n2 * a2) // (n1 + n2)
    x, y = two_names(r)
    stem = (f"{x} had {n1} bags with an average mass of {a1} kg each. {y} had {n2} bags with an average mass of {a2} kg each. "
            f"What is the average mass of all the {n1 + n2} bags together, in kg?")
    return build(subgroup_average, stem, avg, [
        (F(a1 + a2, 2) if (a1 + a2) % 2 == 0 else None, "averaged_the_averages", "Found the average of the two averages."),
        (n1 * a1 + n2 * a2, "gave_the_total", "Gave the total mass."),
        (F(n1 * a1 + n2 * a2, 2) if (n1 * a1 + n2 * a2) % 2 == 0 else None, "divided_by_two", "Divided the total by 2."),
        *slipn(avg, 1), *slipn(avg, 2),
    ], [f"Total mass = {n1} × {a1} + {n2} × {a2} = {n1 * a1 + n2 * a2}", f"Average = {n1 * a1 + n2 * a2} ÷ {n1 + n2} = {avg}"],
        {"n1": n1, "a1": a1, "n2": n2, "a2": a2}, unit("kg"), whole=True, auto_slips=False)


@checker(subgroup_average)
def _(q):
    total = sum(q["a1"] for _ in range(q["n1"])) + sum(q["a2"] for _ in range(q["n2"]))
    return brute(lambda x: x * (q["n1"] + q["n2"]) == total, 2000)


@template(T, "intermediate", AVG, REL)
def two_classes_average(r):
    nb, ng = r.randint(10, 30), r.randint(10, 30)
    ab, ag = r.randint(40, 90), r.randint(40, 90)
    if ab == ag or nb == ng or F(nb * ab + ng * ag, nb + ng).denominator != 1:
        return None
    avg = (nb * ab + ng * ag) // (nb + ng)
    stem = (f"In a class, {nb} boys scored an average of {plural(ab, 'mark')} in a test and {ng} girls scored an average of {plural(ag, 'mark')}. "
            f"What was the average mark of the whole class?")
    return build(two_classes_average, stem, avg, [
        (F(ab + ag, 2) if (ab + ag) % 2 == 0 else None, "averaged_the_averages", "Found the average of the two averages."),
        (nb * ab + ng * ag, "gave_the_total", "Gave the total marks."),
        (F(nb * ab + ng * ag, 2) if (nb * ab + ng * ag) % 2 == 0 else None, "divided_by_two", "Divided the total by 2."),
        (F(nb * ab + ng * ag, max(nb, ng)) if (nb * ab + ng * ag) % max(nb, ng) == 0 else None, "divided_by_larger_group", "Divided by the larger group only."),
        *slipn(avg, 1), *slipn(avg, 2),
    ], [f"Total marks = {nb} × {ab} + {ng} × {ag} = {nb * ab + ng * ag}", f"Pupils = {nb + ng}", f"Average = {avg}"],
        {"nb": nb, "ab": ab, "ng": ng, "ag": ag}, whole=True, auto_slips=False)


@checker(two_classes_average)
def _(q):
    marks = [q["ab"]] * q["nb"] + [q["ag"]] * q["ng"]
    return brute(lambda x: x * len(marks) == sum(marks), 2000)


@template(T, "intermediate", REL)
def corrected_value(r):
    n = r.randint(4, 10)
    right = r.randint(20, 90)
    wrong_v = right + r.choice([-1, 1]) * r.choice([9, 18, 27, 36, 45])
    if wrong_v <= 0 or (wrong_v - right) % n:
        return None
    Awrong = r.randint(40, 80)
    Acorrect = F(Awrong * n - wrong_v + right, n)
    if Acorrect.denominator != 1:
        return None
    nm = r.choice(NAMES)
    stem = (f"{nm} worked out the average of {n} test scores and got {Awrong}. Later {nm} found that one score had been written as "
            f"{wrong_v} when it should have been {right}. What is the correct average?")
    return build(corrected_value, stem, Acorrect, [
        (Awrong, "kept_the_old_average", "Kept the original average."),
        (Awrong + abs(wrong_v - right), "added_the_whole_difference", "Added the full difference to the average instead of dividing by the number of scores."),
        (Awrong - (right - wrong_v), "wrong_direction", "Adjusted the average in the wrong direction."),
        *slipn(Acorrect, 1), *slipn(Acorrect, 2),
    ], [f"Wrong total = {Awrong} × {n} = {Awrong * n}", f"Correct total = {Awrong * n} − {wrong_v} + {right} = {Awrong * n - wrong_v + right}",
        f"Correct average = {Acorrect}"], {"n": n, "Aw": Awrong, "wrong": wrong_v, "right": right}, whole=True, auto_slips=False)


@checker(corrected_value)
def _(q):
    scores_total = q["Aw"] * q["n"]
    return brute(lambda a: a * q["n"] == scores_total - q["wrong"] + q["right"], 2000)


# ---------------------------------------------------------------- competent

@template(T, "competent", REL)
def extreme_value(r):
    """math-pat-average-extreme-value"""
    n = r.choice([4, 5, 6])
    big = r.random() < 0.6
    # 2-digit numbers, all different
    if big:
        avg = r.randint(20, 40)
        tot = avg * n
        lo = sum(range(10, 10 + n - 1))
        ans = tot - lo
        if ans > 99 or ans <= 10 + n - 2:
            return None
        stem = f"The average of {n} different 2-digit whole numbers is {avg}. What is the largest possible value of one of the numbers?"
        wrong = [(tot - 10 * (n - 1), "others_all_the_smallest_equal", f"Made the other numbers all 10, but they must be different."),
                 (tot - sum(range(1, n)), "others_started_at_one", "Started the other numbers at 1, which is not a 2-digit number."),
                 (tot - sum(range(10, 10 + n)) + 10 if False else tot - sum(range(10, 10 + n)), "used_one_extra_number", f"Took away {n} different numbers instead of {n - 1}."),
                 *slipn(ans, 1), *slipn(ans, 2)]
        steps = [f"Total = {avg} × {n} = {tot}", f"Smallest {n - 1} different 2-digit numbers: {', '.join(map(str, range(10, 10 + n - 1)))} (sum {lo})",
                 f"Largest number = {tot} − {lo} = {ans}"]
    else:
        avg = r.randint(60, 90)
        tot = avg * n
        hi = sum(range(99, 99 - (n - 1), -1))
        ans = tot - hi
        if ans < 10 or ans >= 99 - n + 2:
            return None
        stem = f"The average of {n} different 2-digit whole numbers is {avg}. What is the smallest possible value of one of the numbers?"
        wrong = [(tot - 99 * (n - 1), "others_all_the_largest_equal", "Made the other numbers all 99, but they must be different."),
                 (tot - sum(range(100, 100 + n - 1)) if tot - sum(range(100, 100 + n - 1)) > 0 else None, "others_started_at_100", "Used 100 and above, which are not 2-digit numbers."),
                 (tot - sum(range(99, 99 - n, -1)), "used_one_extra_number", f"Took away {n} different numbers instead of {n - 1}."),
                 *slipn(ans, 1), *slipn(ans, 2)]
        steps = [f"Total = {avg} × {n} = {tot}", f"Largest {n - 1} different 2-digit numbers: {', '.join(str(x) for x in range(99, 99 - (n - 1), -1))} (sum {hi})",
                 f"Smallest number = {tot} − {hi} = {ans}"]
    return build(extreme_value, stem, ans, wrong, steps, {"n": n, "avg": avg, "big": big}, whole=True, auto_slips=False)


@checker(extreme_value)
def _(q):
    n, tot = q["n"], q["n"] * q["avg"]
    pool = list(range(10, 100))
    best = None
    for cand in (range(99, 9, -1) if q["big"] else range(10, 100)):
        others = [x for x in pool if x != cand]
        rem = tot - cand
        lo = sum(sorted(others)[: n - 1])
        hi = sum(sorted(others)[-(n - 1):])
        if lo <= rem <= hi:
            best = cand
            break
    return F(best) if best is not None else None


@template(T, "competent", REL)
def middle_number_from_groups(r):
    while True:
        xs = [r.randint(10, 60) for _ in range(5)]
        if sum(xs) % 5 == 0 and sum(xs[:3]) % 3 == 0 and sum(xs[2:]) % 3 == 0 and len(set(xs)) == 5:
            break
    A, B, C = sum(xs) // 5, sum(xs[:3]) // 3, sum(xs[2:]) // 3
    mid = xs[2]
    nm = r.choice(NAMES)
    stem = (f"The average of five numbers is {A}. The average of the first three numbers is {B} and the average of the last three numbers is {C}. "
            f"What is the third number?")
    tot = 3 * B + 3 * C - 5 * A
    return build(middle_number_from_groups, stem, mid, [
        (F(B + C, 2) if (B + C) % 2 == 0 else None, "averaged_the_two_averages", "Found the average of the two averages."),
        (3 * B + 3 * C, "forgot_to_subtract_the_total", "Added the two group totals but did not subtract the total of all five."),
        (5 * A - 3 * B if 5 * A - 3 * B > 0 else None, "subtracted_one_group_only", "Subtracted the first group's total from the total of all five numbers."),
        (A, "gave_the_average", "Gave the average of all five numbers."),
        *slipn(mid, 1), *slipn(mid, 2),
    ], [f"Total of 5 = {A} × 5 = {5 * A}", f"First 3: {B} × 3 = {3 * B}; last 3: {C} × 3 = {3 * C}",
        f"The third number is counted twice in {3 * B} + {3 * C} = {3 * B + 3 * C}", f"Third number = {3 * B + 3 * C} − {5 * A} = {mid}"],
        {"A": A, "B": B, "C": C}, whole=True, auto_slips=False)


@checker(middle_number_from_groups)
def _(q):
    return brute(lambda m: 3 * q["B"] + 3 * q["C"] - m == 5 * q["A"], 1000)


@template(T, "competent", REL)
def two_removed_average(r):
    n = r.choice([6, 8, 10])
    A = r.randint(20, 60)
    A2 = r.randint(A - 8, A + 8)
    if A2 == A:
        return None
    gone = A * n - A2 * (n - 2)
    if gone <= 0 or gone % 2:
        return None
    ans = gone // 2
    nm = r.choice(NAMES)
    stem = (f"The average mass of {n} parcels is {A} kg. When two parcels are removed, the average mass of the remaining {n - 2} parcels is {A2} kg. "
            f"What is the average mass of the two parcels that were removed, in kg?")
    return build(two_removed_average, stem, ans, [
        (gone, "gave_the_total_of_the_two", "Gave the total mass of the two parcels."),
        (abs(A - A2), "gave_the_change_in_average", "Gave the difference between the averages."),
        (F(A + A2, 2) if (A + A2) % 2 == 0 else None, "averaged_the_averages", "Found the average of the two averages."),
        (A * n - A2 * n if False else abs(F(A * n - A2 * n, 2)), "used_wrong_count", f"Used {n} instead of {n - 2} for the new total."),
        *slipn(ans, 1), *slipn(ans, 2),
    ], [f"Total of {n} = {A * n}", f"Total of {n - 2} = {A2 * (n - 2)}", f"Two removed = {gone}", f"Average = {gone} ÷ 2 = {ans}"],
        {"n": n, "A": A, "A2": A2}, unit("kg"), whole=True, auto_slips=False)


@checker(two_removed_average)
def _(q):
    return brute(lambda a: 2 * a + q["A2"] * (q["n"] - 2) == q["A"] * q["n"], 5000)


@template(T, "competent", REL)
def remaining_group_average(r):
    n = r.choice([20, 24, 30, 40])
    k = r.randint(8, n - 6)
    A = r.randint(55, 80)
    Ak = r.randint(A + 3, A + 18)
    rest = (A * n - Ak * k)
    if rest <= 0 or rest % (n - k):
        return None
    ans = rest // (n - k)
    if ans == A:
        return None
    stem = (f"A group of {n} pupils had an average mark of {A} in a test. {k} of the pupils passed the test and their average mark was {Ak}. "
            f"What was the average mark of the pupils who did not pass?")
    return build(remaining_group_average, stem, ans, [
        (F(A + Ak, 2) if (A + Ak) % 2 == 0 else None, "averaged_the_averages", "Found the average of the two averages."),
        (A - (Ak - A), "mirrored_the_difference", "Went below the group average by the same amount as the passing average is above it."),
        (rest, "gave_the_total_of_the_rest", "Gave the total marks of those who did not pass."),
        (F(rest, n) if rest % n == 0 else None, "divided_by_the_whole_group", f"Divided by {n} instead of {n - k}."),
        *slipn(ans, 1), *slipn(ans, 2),
    ], [f"Total marks = {A} × {n} = {A * n}", f"Passed: {Ak} × {k} = {Ak * k}", f"Not passed: {A * n} − {Ak * k} = {rest} for {n - k} pupils",
        f"Average = {rest} ÷ {n - k} = {ans}"], {"n": n, "k": k, "A": A, "Ak": Ak}, whole=True, auto_slips=False)


@checker(remaining_group_average)
def _(q):
    return brute(lambda a: a * (q["n"] - q["k"]) + q["Ak"] * q["k"] == q["A"] * q["n"], 1000)


@template(T, "competent", REL, AVG)
def two_equal_missing(r):
    """math-pat-average-find-missing"""
    n = r.choice([5, 6, 7])
    known_n = n - 2
    avg = r.randint(50, 90)
    x = r.randint(30, 99)
    if x == avg:
        return None
    known = [r.randint(40, 95) for _ in range(known_n)]
    if avg * n - sum(known) != 2 * x:
        # adjust last known value to fit
        known[-1] = avg * n - 2 * x - sum(known[:-1])
        if not 20 <= known[-1] <= 100:
            return None
    nm = r.choice(NAMES)
    stem = (f"{nm}'s scores in {n} tests had an average of {avg}. The scores in the first {known_n} tests were {listing(known)}. "
            f"The scores in the last two tests were the same. What was the score in each of the last two tests?")
    rest = avg * n - sum(known)
    return build(two_equal_missing, stem, x, [
        (rest, "gave_the_total_of_the_two", "Gave the total of the last two scores."),
        (F(avg * known_n - sum(known), 2) if (avg * known_n - sum(known)) % 2 == 0 and avg * known_n - sum(known) > 0 else None, "used_wrong_total", f"Used {avg} × {known_n} as the total."),
        (avg, "gave_the_average", "Gave the average."),
        (F(rest, 3) if rest % 3 == 0 else None, "divided_by_wrong_count", "Divided by 3 instead of 2."),
        *slipn(x, 1), *slipn(x, 2),
    ], [f"Total of all {n} tests = {avg} × {n} = {avg * n}", f"Total of the first {known_n} = {sum(known)}", f"Last two = {avg * n} − {sum(known)} = {rest}",
        f"Each = {rest} ÷ 2 = {x}"], {"known": known, "avg": avg, "n": n}, whole=True, auto_slips=False)


@checker(two_equal_missing)
def _(q):
    return brute(lambda x: F(sum(q["known"]) + 2 * x, q["n"]) == q["avg"], 5000)


@template(T, "competent", REL)
def group_size_from_average_change(r):
    n = r.randint(4, 12)
    A = r.randint(130, 150)
    d = r.randint(1, 3)
    A2 = A + d
    newv = A2 + n * d
    nm = r.choice(NAMES)
    stem = (f"The average height of a group of children is {A} cm. When {nm}, who is {newv} cm tall, joins the group, the average height rises to {A2} cm. "
            f"How many children were in the group at first?")
    return build(group_size_from_average_change, stem, n, [
        (n + 1, "counted_the_new_member", "Counted the new person as well."),
        (newv - A2, "gave_the_extra_height", "Gave how much taller the new person is than the new average."),
        (F(newv - A, d) if (newv - A) % d == 0 else None, "used_the_old_average", "Used the old average instead of the new average."),
        (newv - A, "gave_the_height_difference", "Gave how much taller the new person is than the old average."),
        *slipn(n, 1), *slipn(n, 2),
    ], [f"The new person is {newv} − {A2} = {newv - A2} cm above the new average", f"This extra height is shared to raise every one of the group by {d} cm",
        f"Number in the group = {newv - A2} ÷ {d} = {n}"], {"A": A, "A2": A2, "newv": newv}, whole=True, auto_slips=False)


@checker(group_size_from_average_change)
def _(q):
    return brute(lambda n: F(q["A"] * n + q["newv"], n + 1) == q["A2"], 500)
