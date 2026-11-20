"""Removing one template must not regenerate any other sub-topic, nor the sibling templates' questions.

1. Builds math-geometry in memory twice: as is, and without one template. Every question outside that template's
   sub-topic and level must be identical, and every sibling template must keep all the questions it had (it may get
   more, to make up the removed template's share).
2. Two made-up templates whose stems overlap: removing the first frees stems the second also produces. The second
   must keep every question it had, with the same ids and options.

    python3 scripts/quiz/math/test_isolation.py
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import build  # noqa: E402

TOPIC, VICTIM = "math-geometry", "grid_point_triangle"


def real_topic():
    before = build.bank(TOPIC)
    saved = build.REGISTRY[TOPIC][:]
    victim = next(t for t in saved if t.key == VICTIM)
    build.REGISTRY[TOPIC] = [t for t in saved if t is not victim]
    try:
        after = build.bank(TOPIC)
    finally:
        build.REGISTRY[TOPIC] = saved
    sub = build.sub_of(victim)
    inside = lambda q: q["level"] == victim.level and re.sub(r"-\d+$", "", q["outcomes"][0]) == sub
    out_b = [q for q in before if not inside(q)]
    assert out_b == [q for q in after if not inside(q)], "a question outside the changed sub-topic changed"
    in_b = [q for q in before if inside(q) and q["template"] != VICTIM]
    in_a = {q["id"]: q for q in after if inside(q)}
    lost = [q["id"] for q in in_b if in_a.get(q["id"]) != q]
    assert not lost, f"sibling templates lost or changed questions: {lost[:5]}"
    assert not any(q["template"] == VICTIM for q in after)
    print(f"ok: {len(out_b)} questions outside {sub}/{victim.level} unchanged; {len(in_b)} sibling questions kept, "
          f"{len(in_a) - len(in_b)} added to refill the tier")


def fake(key, lo, hi):
    """A template whose stems are 'Find N.' for N in lo..hi, so two fakes with overlapping ranges share stems."""
    def gen(rng):
        x = rng.randint(lo, hi)
        if rng.random() < 0.2:
            return None  # like real templates, some draws fail
        return {"stem": f"Find {x}.", "correct": (str(x), x),
                "wrong": [(str(x + k), x + k, "slip", "A slip.") for k in (1, 2, 3)],
                "steps": [str(x)], "params": {"x": x}, "figure": None}
    gen.topic, gen.level, gen.outcomes, gen.key, gen.weight, gen.calc = "math-fake", "basic", ["math-fake-sub-01"], key, 1, False
    return gen


def stem_collision():
    a, b, c = fake("first", 0, 30), fake("second", 10, 40), fake("third", 200, 400)
    before = build.sub_bank("math-fake", "basic", [a, b, c], 45, "2027")
    after = build.sub_bank("math-fake", "basic", [b, c], 45, "2027")
    b_before = [q for q in before if q["template"] == "second"]
    b_after = {q["id"]: q for q in after if q["template"] == "second"}
    a_stems = {q["stem"] for q in before if q["template"] == "first"}
    freed = [s for s in (q["stem"] for q in b_after.values()) if s in a_stems]
    assert freed, "test setup: removing the first template should free a stem the second one produces"
    changed = [q["id"] for q in b_before if b_after.get(q["id"]) != q]
    assert not changed, f"the second template's questions changed after a freed stem: {changed[:5]}"
    print(f"ok: removing a template freed {len(freed)} stems its sibling also makes; the sibling's "
          f"{len(b_before)} questions kept their ids and options")


def three_overlapping():
    """Three siblings whose stems overlap pairwise: removing the first grows the second, which must not take
    questions from the untouched third (nor lose any of its own)."""
    for n in (30, 45, 60):
        a, b, c = fake("first", 0, 30), fake("second", 10, 40), fake("third", 20, 50)
        before = build.sub_bank("math-fake", "basic", [a, b, c], n, "2027")
        after = {q["id"]: q for q in build.sub_bank("math-fake", "basic", [b, c], n, "2027")}
        for key in ("second", "third"):
            mine = [q for q in before if q["template"] == key]
            changed = [q["id"] for q in mine if after.get(q["id"]) != q]
            assert not changed, f"n={n}: removing the first template changed {key}'s questions: {changed[:5]}"
        assert len(after) == min(n, 41), f"n={n}: the tier was not refilled ({len(after)})"  # stems 10-50 exist
    print("ok: three overlapping siblings at n = 30, 45, 60: removing one leaves both others' questions intact")


if __name__ == "__main__":
    real_topic()
    stem_collision()
    three_overlapping()
