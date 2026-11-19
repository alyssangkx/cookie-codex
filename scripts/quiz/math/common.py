"""Shared helpers for the PSLE math question generators.

A template is a function gen(rng) -> dict | None, registered with @template.
It returns the stem, the correct value, a priority-ordered list of wrong answers
(each produced by a named mistake), solution steps and the params needed to re-check it.
Each template also has a .check(params) that recomputes the answer by a different
route (brute force or plug-back), used by check_math.py.
"""
import re
from fractions import Fraction as F
from math import gcd, lcm

REGISTRY = {}  # topic -> list of template functions

NAMES = ["Ali", "Mei Ling", "Ravi", "Siti", "Jun Wei", "Priya", "Hui Min", "Farid",
         "Kumar", "Xin Yi", "Aisha", "Daniel", "Wei Jie", "Nurul", "Arjun", "Shu Fen"]


def template(topic, level, *outcomes, same_value_ok=False, calc=False):
    """Register a generator. The first outcome decides which sub-topic the question is filed under.
    Put the top-school pattern ids it covers (math-pat-...) in the docstring for the coverage report.
    calc=True: a calculator is allowed (PSLE Paper 2 style). The default False means Paper 1 style, and
    check_math.py then requires every step to be workable by hand (hand_problems below)."""
    def deco(fn):
        fn.topic, fn.level, fn.outcomes, fn.same_value_ok, fn.calc = topic, level, list(outcomes), same_value_ok, calc
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


def noun(n, word, many=None):
    """Just the noun form for a count: noun(1, 'note') -> 'note', noun(2, 'note') -> 'notes'."""
    try:
        one = F(n) == 1
    except (ValueError, TypeError, ZeroDivisionError):
        one = str(n) == "1"  # e.g. a mixed-number string such as '1 1/2'
    return word if one else (many or word + 's')


def plural(n, word, many=None):
    """'1 unit', '2 units'. Pass many= for irregular plurals. n may be int or Fraction (1 only is singular)."""
    return f"{n} {noun(n, word, many)}"


def ordinal(n):
    """1st, 2nd, 3rd, 4th, 11th, 12th, 22nd."""
    n = int(n)
    suf = "th" if 10 <= n % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suf}"


_VOWEL_LETTERS = set("aefhilmnorsx")  # letters whose NAME starts with a vowel sound: ay, ef, aitch, el, em, en, oh, ar, es, ex
_A_WORDS = ("one", "once", "ewe", "euro", "eu", "use", "usu", "uti", "ubiq", "uran")
_AN_WORDS = ("hour", "honest", "honour", "heir")
_UNI_A = re.compile(r"uni[tfoqvcslp]")  # unit, uniform, union, unique, universe... ; but unimportant, unidentified, unintended are 'an'


def a_an(n_or_word):
    """'a' or 'an' by how the first word is SPOKEN. Numbers: an 8, 11, 18, 80-89, 800-899, 8000, 11000, 18000
    (commas or not; 1800 is 'one thousand ...' so 'a'). Letters by name: an L-shaped, an x-axis, an MRT, a UFO.
    Words by sound: an hour, a unit, a useful, an unusual, a one. A leading $, quote or bracket is ignored.
    Returns None for a token it cannot judge (no letter or digit to start with)."""
    parts = str(n_or_word).strip().split()
    s = parts[0].lstrip("$£€¥(\"'\u201c\u2018[~").replace(",", "") if parts else ""
    if not s or not s[0].isalnum():
        return None
    if s[0].isdigit():
        digits = re.match(r"\d+", s).group()
        g = len(digits) % 3 or 3  # size of the leading spoken group
        lead = int(digits[:g])
        if g == 3:
            return "an" if digits[0] == "8" else "a"
        return "an" if lead in (8, 11, 18) or 80 <= lead <= 89 else "a"
    word = re.match(r"[A-Za-z]+", s).group()
    rest = s[len(word):]
    if len(word) == 1 and (rest[:1] == "-" or len(parts) > 1 or not rest):  # a letter said by its name: L-shaped, x-axis
        return "an" if word.lower() in _VOWEL_LETTERS else "a"
    if len(word) >= 2 and word.isupper():  # acronym spelled out: MRT, UFO, SMS
        return "an" if word[0].lower() in _VOWEL_LETTERS else "a"
    w = word.lower()
    if w.startswith(_AN_WORDS):
        return "an"
    if w.startswith(_A_WORDS) or _UNI_A.match(w):
        return "a"
    return "an" if w[0] in "aeiou" else "a"


_COUNT_WORDS = {"units", "pens", "parts", "slices", "shapes", "divisions", "marks", "cents", "weeks", "wholes", "litres",
                "minutes", "hours", "pages", "sums", "points", "words", "bookmarks", "cards", "leaflets"}


def unit(u):
    """Formatter for option text: '1 slice', '3 slices'. A plural counting word at the start of u
    takes its singular for exactly 1 (so 'litres per minute' gives '1 litre per minute')."""
    head, _, tail = u.partition(" ")
    if head in _COUNT_WORDS:
        return lambda x: f"{frac(x)} {noun(x, head[:-1], head)}" + (f" {tail}" if tail else "")
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
        "calc": fn.calc,  # not part of the id (stable_id hashes topic, template and params only)
        **({"figure": q["figure"]} if q.get("figure") else {}),
    }


# ---------------------------------------------------------------- by hand (no calculator)
# The MOE primary syllabus's written-computation limits, as a check on Paper 1 style (calc=False) questions:
#   multiply: by a power of 10, by a 1-significant-digit number (any other factor), or one factor up to 2
#   significant digits and the other up to 4 (4-digit by 2-digit);
#   divide (after cancelling common trailing zeros): by a power of 10, by a 1-significant-digit number (3, 40, 0.5),
#   by a whole number up to 12, or by a 2-significant-digit number when the quotient is under 1000 with at most
#   2 decimal places (35 ÷ 25 = 1.4, 1350 ÷ 45 = 30).
# ponytail: reads the × and ÷ chains in the worked solution only. A chain a × b ÷ c is worked left to right and each
# step is judged on its running value (108 × 2 ÷ 24 checks 108 × 2, then 216 ÷ 24). An operand that is part of a
# fraction or mixed number (3/4, 2 3/4) ends the chain, since its true size is not the digits next to the sign.
# A step written another way is not checked.
_N = r"\$?\d[\d,]*(?:\.\d+)?(?![\d/])"
_CHAIN = re.compile(r"(?<![\d/.,])" + _N + r"(?:\s*[×÷]\s*" + _N + r")+")
_PART = re.compile(r"([×÷])?\s*\$?(\d[\d,]*(?:\.\d+)?)")


def _sig(x):
    """Significant digits of a positive number: 3200 -> 2, 0.05 -> 1, 3.14 -> 3."""
    t = format(x.normalize(), "f").replace(".", "").strip("0")
    return len(t) or 1


def _pow10(x):
    return x > 0 and format(x.normalize(), "f").replace(".", "").strip("0") == "1"


def _step_ok(x, op, y):
    if op == "×":
        return _pow10(x) or _pow10(y) or min(_sig(x), _sig(y)) == 1 \
            or min(_sig(x), _sig(y)) <= 2 and max(_sig(x), _sig(y)) <= 4
    while x == x.to_integral() and y == y.to_integral() and x % 10 == 0 and y % 10 == 0:
        x, y = x / 10, y / 10  # 6000 ÷ 1200 is worked as 60 ÷ 12
    q = x / y
    return _pow10(y) or _sig(y) == 1 or (y == y.to_integral() and y <= 12) \
        or (_sig(y) == 2 and q * 100 == (q * 100).to_integral() and q < 1000)


def hand_problems(lines):
    """-> the steps in these lines that are not workable by hand under the rule above."""
    from decimal import Decimal as D, getcontext
    getcontext().prec = 28
    bad = []
    for line in lines:
        for m in _CHAIN.finditer(line.replace("**", "")):
            parts = _PART.findall(m.group(0))
            run = D(parts[0][1].replace(",", ""))
            for op, b in parts[1:]:
                y = D(b.replace(",", ""))
                if run == 0 or y == 0:
                    break
                if not _step_ok(run, op, y):
                    bad.append(f"{format(run.normalize(), 'f')} {op} {b}")
                    break
                run = run * y if op == "×" else run / y
    return bad


def coprime_pair(rng, lo, hi, proper=True):
    while True:
        b = rng.randint(lo, hi)
        a = rng.randint(1, b - 1) if proper else rng.randint(1, 3 * b)
        if gcd(a, b) == 1 and a != b:
            return a, b


__all__ = ["F", "gcd", "lcm", "template", "hand_problems", "checker", "build", "finalize", "frac", "money",
           "unit", "plural", "noun", "ordinal", "a_an", "two_names", "coprime_pair", "REGISTRY", "NAMES"]


if __name__ == "__main__":
    for x in (8, 11, 18, 80, 85, 89, 800, 899, 8000, 8500, "11,000", 11000, "18,000", 800000, "8.5"):
        assert a_an(x) == "an", x
    for x in (1, 7, 9, 10, 180000, 12, 17, 19, 79, 90, 100, 118, 180, 799, 900, 1800, 1100, 7000, 12000, 188000, 118000, "0.8", "9.5"):
        assert a_an(x) == "a", x
    assert a_an("hour") == "an" and a_an("unit") == "a" and a_an("umbrella") == "an" and a_an("pair of shoes") == "a"
    assert a_an("apple") == "an" and a_an("watch") == "a" and a_an("one") == "a"
    for x in ("L-shaped", "x-axis", "MRT", "unusual", "unimportant", "unidentified", "hour", "honest", "$8", "$85.50", "(8",
              "8%", "umbrella", "SMS", "F-test", "R-shaped"):
        assert a_an(x) == "an", x
    for x in ("UFO", "unit", "uniform", "useful", "ewe", "one", "euro", "unique", "universe", "$1.50", "U-shaped", "D-shaped",
              "B-flat", "watch", "hotel"):
        assert a_an(x) == "a", x
    assert a_an("$") is None and a_an("") is None and a_an("-") is None
    assert plural(1, "note") == "1 note" and plural(2, "watch", "watches") == "2 watches" and noun(3, "coin") == "coins"
    print("common.py self-check ok")
