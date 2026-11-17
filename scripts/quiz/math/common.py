"""Shared helpers for the PSLE math question generators.

A template is a function gen(rng) -> dict | None, registered with @template.
It returns the stem, the correct value, a priority-ordered list of wrong answers
(each produced by a named mistake), solution steps and the params needed to re-check it.
Each template also has a .check(params) that recomputes the answer by a different
route (brute force or plug-back), used by check_math.py.
"""
from fractions import Fraction as F
from math import gcd, lcm

REGISTRY = {}  # topic -> list of template functions

NAMES = ["Ali", "Mei Ling", "Ravi", "Siti", "Jun Wei", "Priya", "Hui Min", "Farid",
         "Kumar", "Xin Yi", "Aisha", "Daniel", "Wei Jie", "Nurul", "Arjun", "Shu Fen"]


def template(topic, level, *outcomes, same_value_ok=False):
    """Register a generator. The first outcome decides which sub-topic the question is filed under.
    Put the top-school pattern ids it covers (math-pat-...) in the docstring for the coverage report."""
    def deco(fn):
        fn.topic, fn.level, fn.outcomes, fn.same_value_ok = topic, level, list(outcomes), same_value_ok
        fn.key = fn.__name__
        REGISTRY.setdefault(topic, []).append(fn)
        return fn
    return deco


def checker(gen_fn):
    """Attach the independent re-check to a template: @checker(simplest_form)."""
    def deco(fn):
        gen_fn.check = fn
        return fn
    return deco


def frac(x, mixed=True):
    """3/4, 2 1/4 or 5. Mixed numbers by default, as PSLE answers are written."""
    x = F(x)
    if x.denominator == 1:
        return str(x.numerator)
    if mixed and x > 1:
        w = x.numerator // x.denominator
        r = x - w
        return f"{w} {r.numerator}/{r.denominator}"
    return f"{x.numerator}/{x.denominator}"


def money(x):
    x = F(x)
    return f"${x.numerator}" if x.denominator == 1 else f"${float(x):.2f}"


def unit(u):
    return lambda x: f"{frac(x)} {u}"


def two_names(rng):
    return rng.sample(NAMES, 2)


def slips(correct, unit_size=None):
    """Careless-calculation distractors close to the answer."""
    c = F(correct)
    out = []
    if unit_size:
        out += [(c + unit_size, "miscounted_units", "Counted one unit too many."),
                (c - unit_size, "miscounted_units", "Counted one unit too few.")]
    if c.denominator != 1:
        n, d = c.numerator, c.denominator
        if c > 1:
            out.append((c + 1, "slip_converting_to_mixed_number",
                        "Made a slip changing the improper fraction to a mixed number."))
        out += [(F(n + 1, d), "careless_slip_in_numerator", "Careless slip working out the numerator."),
                (F(n - 1, d), "careless_slip_in_numerator", "Careless slip working out the numerator.")]
    return out


def build(fn, stem, correct, wrong, steps, params, show=frac, unit_size=None, whole=False, auto_slips=True,
          figure=None):
    """Pick 3 distractors in priority order, shuffle, and return the question dict.

    wrong: list of (value, tag, why). value may be (display_text, value) to show an unreduced
    form such as 6/9 when the question is about simplest form. Values that are non-positive, equal to the correct
    display, equal in value to the correct answer (unless the template allows it, e.g.
    'simplest form'), or duplicates are dropped. Returns None when fewer than 3 survive,
    so the caller retries with new numbers.

    Priority: the first two method mistakes, then one careless slip, then the rest. whole=True
    drops non-integer distractors (counts and money), which would give the answer away.
    """
    correct = F(correct)
    sl = slips(correct, unit_size) if auto_slips and not fn.same_value_ok else []
    wrong = [w for w in wrong if w[0] is not None]
    wrong = wrong[:2] + sl[:1] + wrong[2:] + sl[1:]
    picked, seen_disp, seen_val = [], {show(correct)}, {correct}
    for value, tag, why in wrong:
        if value is None:
            continue
        d, value = value if isinstance(value, tuple) else (None, value)
        value = F(value)
        d = d or show(value)
        if value <= 0 or (whole and value.denominator != 1) or d in seen_disp or (value in seen_val and not fn.same_value_ok):
            continue
        seen_disp.add(d)
        seen_val.add(value)
        picked.append((d, value, tag, why))
        if len(picked) == 3:
            break
    if len(picked) < 3:
        return None
    return {"stem": stem, "correct": (show(correct), correct), "wrong": picked, "steps": steps,
            "params": params, "figure": figure}


def finalize(q, fn, rng, qid):
    opts = [(*q["correct"], None)] + [(d, v, {"tag": t, "why": w}) for d, v, t, w in q["wrong"]]
    rng.shuffle(opts)
    if sorted(d for d, _, _ in opts) == ["A", "B", "C", "D"]:
        opts.sort(key=lambda o: o[0])  # "which figure?" questions: keep the letters in order
    return {
        "id": qid,
        "topic": fn.topic,
        "level": fn.level,
        "template": fn.key,
        "outcomes": fn.outcomes,
        "stem": q["stem"],
        "options": [d for d, _, _ in opts],
        "optionValues": [str(v) for _, v, _ in opts],
        "answer": next(i for i, (_, _, e) in enumerate(opts) if e is None),
        "explain": [e for _, _, e in opts],
        "solution": q["steps"],
        "params": q["params"],
        **({"figure": q["figure"]} if q.get("figure") else {}),
    }


def coprime_pair(rng, lo, hi, proper=True):
    while True:
        b = rng.randint(lo, hi)
        a = rng.randint(1, b - 1) if proper else rng.randint(1, 3 * b)
        if gcd(a, b) == 1 and a != b:
            return a, b


__all__ = ["F", "gcd", "lcm", "template", "checker", "build", "finalize", "frac", "money",
           "unit", "two_names", "coprime_pair", "REGISTRY", "NAMES"]
