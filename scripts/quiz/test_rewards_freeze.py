"""Frozen English reward slots: a newly playable section must not move any pinned slot, any non-English slot, or
the one-use-per-cookie rule. Writes only to a scratch folder. Run: python3 scripts/quiz/test_rewards_freeze.py"""
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import build_rewards as b

scratch = Path("/data/alvin/tmp/cookie-codex/freeze")
scratch.mkdir(parents=True, exist_ok=True)
pins = json.loads(b.FROZEN.read_text())
base = b.main(out_path=scratch / "base.json")
assert json.loads((scratch / "base.json").read_text()) == json.loads((b.DATA / "rewards.json").read_text())
for extra in ({"eng-editing"}, {"eng-vocab-cloze", "eng-comp-cloze"}, {"eng-editing", "eng-synthesis", "eng-vocab-cloze"}):
    sim = b.main(playable=b.PLAYABLE | extra, out_path=scratch / "sim.json")
    b.PLAYABLE = {s for s in b.PLAYABLE if s not in extra}
    for k, v in pins.items():
        assert sim[k] == v, ("pinned slot moved", extra, k)
    for k, v in base.items():
        if not k.startswith("eng-"):
            assert sim[k] == v, ("non-English slot moved", extra, k)
    moved = [k for k in base if k.startswith("eng-") and sim[k] != base[k]]
    print(sorted(extra), "-> English slots changed (all unpinned):", len(moved))
    assert not set(moved) & set(pins)
print("freeze test OK")
