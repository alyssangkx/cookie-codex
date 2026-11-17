"""Rewording a stem must not change a question id.

Rebuilds one topic twice into a temp dir: once as is, once with one template's stem reworded.
Every id must be identical, and the reworded stems must actually differ.

    python3 scripts/quiz/test_stable_ids.py
"""
import functools
import json
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE / "math"))
import build  # noqa: E402

TOPIC = "math-ratio"
TMP_ROOT = Path("/data/alvin/tmp/cookie-codex/accounts")


def rebuild(tmp, name):
    build.OUT = tmp / name
    sys.argv = ["build.py", "--topic", TOPIC]
    build.main()
    return json.loads((build.OUT / f"{TOPIC}.json").read_text())["questions"]


def main():
    TMP_ROOT.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=TMP_ROOT) as d:
        tmp = Path(d)
        before = rebuild(tmp, "before")

        victim = build.REGISTRY[TOPIC][0]

        @functools.wraps(victim)  # keeps topic, level, outcomes, key
        def reworded(rng):
            q = victim(rng)
            if q:
                q = {**q, "stem": q["stem"] + " Show your working."}
            return q

        reworded.check = getattr(victim, "check", None)
        build.REGISTRY[TOPIC][0] = reworded
        try:
            after = rebuild(tmp, "after")
        finally:
            build.REGISTRY[TOPIC][0] = victim

    ids_before = [q["id"] for q in before]
    ids_after = [q["id"] for q in after]
    changed = sum(a["stem"] != b["stem"] for a, b in zip(before, after))
    assert changed > 0, "the monkeypatch did not reword any stem"
    assert ids_before == ids_after, "an id changed after a pure wording change"
    assert len(set(ids_before)) == len(ids_before), "duplicate ids in the bank"
    print(f"ok: {changed} stems reworded in {TOPIC}, all {len(ids_before)} ids unchanged")


if __name__ == "__main__":
    main()
