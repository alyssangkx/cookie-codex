"""Build site/src/data/rewards.json: the fixed, previewed card reward for every (sub-topic, tier).

Implements docs/game-design.md section 4. No randomness at play time: a seeded shuffle here
decides every reward once, and the site shows it before the quiz.

    python scripts/quiz/build_rewards.py
"""
import json
import random
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "site" / "src" / "data"
SCHOOLS = ["math", "science", "english", "chinese"]
# new (non-duplicate) cards per school and tier, from the design's school table
NEW = {"math": (20, 22, 17), "science": (22, 24, 19), "english": (8, 9, 7), "chinese": (8, 9, 7)}
HIGH_SHARE = {"math": 8, "science": 9, "english": 3, "chinese": 4}  # legendary + super-epic capstones (24)
FIRST_DUP = 7  # no duplicate in the first 7 slots (so the 7 commons open Math)
SEED = "ccx-rewards-2027"
# English moved to the PSLE Paper 2 sections (9 sub-topics instead of 12, owner decision 20 Nov 2026). Its star-slot
# draws now use their own RNG, and the main RNG still makes the 12 draws (these list lengths) the old English layout
# made, so every school drawn after English (Chinese) keeps exactly the rewards it had.
LEGACY_ENGLISH_DRAWS = [7, 7, 7, 7, 7, 7, 8, 7, 7, 7, 7, 7]


def playable_subs():
    """Sub-topics with at least 20 questions in some tier, from the built banks."""
    from collections import Counter
    c = Counter()
    for f in (DATA / "quiz").glob("*/*.json"):
        for q in json.loads(f.read_text())["questions"]:
            c[(re.sub(r"-\d+$", "", q["outcomes"][0]), q["level"])] += 1
    return {sub for (sub, _), n in c.items() if n >= 20}


PLAYABLE = playable_subs()


def level_num(level):
    m = re.match(r"P(\d)", level or "")
    return int(m.group(1)) if m else 9


def ordered_subtopics(school):
    """Sub-topics sorted by home level (highest P-level among outcomes), then syllabus order."""
    syl = json.loads((DATA / "syllabus" / f"{school}.json").read_text())
    subs, i = [], 0
    for strand in syl["strands"]:
        for topic in strand["topics"]:
            for st in topic["subtopics"]:
                home = max((level_num(o.get("level")) for o in st["outcomes"]), default=9)
                subs.append({"id": st["id"], "name": st["name"], "topic": topic["id"],
                             "topicName": topic["name"], "home": home, "i": i})
                i += 1
    # sub-topics that have questions come first, so early rewards (the 7 commons) are earnable now; English keeps the
    # paper's section order, so its "Coming soon" sections sit where they come in the paper
    if school != "english":
        subs.sort(key=lambda s: (s["id"] not in PLAYABLE, s["home"], s["i"]))
    last_of_topic = {s["topic"]: s["id"] for s in subs}  # later sub-topics overwrite earlier ones
    for s in subs:
        s["capstone"] = last_of_topic[s["topic"]] == s["id"]
    return subs


def spread(n_slots, n_dups, avoid):
    """Indices for duplicate slots: evenly spread over [FIRST_DUP, n_slots), avoiding capstones if possible."""
    cand = [i for i in range(FIRST_DUP, n_slots) if i not in avoid] or list(range(FIRST_DUP, n_slots))
    if n_dups > len(cand):
        cand = list(range(FIRST_DUP, n_slots))
    step = len(cand) / n_dups if n_dups else 0
    return {cand[int(k * step)] for k in range(n_dups)}


def main():
    rng = random.Random(SEED)
    cookies = json.loads((DATA / "cookies.json").read_text())["cookies"]
    by = {}
    for c in cookies:
        by.setdefault(c["rarity"], []).append(c["slug"])
    for v in by.values():
        rng.shuffle(v)
    epics = by["epic"][:]
    basic_epic, inter_epic, comp_epic = epics[:40], epics[40:90], epics[90:116]

    basic = by["common"] + rng.sample(by["special"] + basic_epic, 51)  # 7 commons open Math
    inter = rng.sample(by["rare"] + inter_epic, 64)
    high = rng.sample(by["legendary"] + by["super-epic"], 24)
    comp_low = comp_epic[:]

    order, slots = {}, {}
    pos = {"b": 0, "i": 0, "high": 0, "low": 0}
    main_rng = rng
    for school in SCHOOLS:
        rng = random.Random(f"{SEED}-english") if school == "english" else main_rng
        if school == "chinese":
            for n in LEGACY_ENGLISH_DRAWS:
                main_rng.choice(range(n))
        subs = ordered_subtopics(school)
        order[school] = subs
        n = len(subs)
        caps = {k for k, s in enumerate(subs) if s["capstone"]}
        for tier, pool, n_new in (("b", basic, NEW[school][0]), ("i", inter, NEW[school][1])):
            dups = spread(n, n - n_new, set())
            earned = []
            for k, s in enumerate(subs):
                if k in dups:
                    slots[f"{s['id']}|{tier}"] = {"slug": rng.choice(earned), "dup": True}
                else:
                    slug = pool[pos[tier]]
                    pos[tier] += 1
                    earned.append(slug)
                    slots[f"{s['id']}|{tier}"] = {"slug": slug, "dup": False}
        # competent: legendaries and super-epics at capstones, epics elsewhere
        n_new = NEW[school][2]
        n_high = HIGH_SHARE[school]
        dups = spread(n, n - n_new, caps)
        high_left, earned = n_high, []
        new_slots = [k for k in range(n) if k not in dups]
        cap_new = [k for k in new_slots if k in caps]
        # capstones first; if there are fewer capstones than high cards, the latest other new slots
        high_at = cap_new[-n_high:] + [k for k in reversed(new_slots) if k not in caps][:max(0, n_high - len(cap_new))]
        high_at = set(high_at)
        for k, s in enumerate(subs):
            key = f"{s['id']}|c"
            if k in dups:
                slots[key] = {"slug": rng.choice(earned), "dup": True}
            elif k in high_at and high_left:
                slug = high[pos["high"]]
                pos["high"] += 1
                high_left -= 1
                earned.append(slug)
                slots[key] = {"slug": slug, "dup": False}
            else:
                slug = comp_low[pos["low"]]
                pos["low"] += 1
                earned.append(slug)
                slots[key] = {"slug": slug, "dup": False}

    milestones = {"ancient": by["ancient"], "dragon": by["dragon"], "beast": by["beast"], "witch": by["witch"]}
    out = {"seed": SEED, "order": order, "slots": slots, "milestones": milestones}
    (DATA / "rewards.json").write_text(json.dumps(out, ensure_ascii=False, indent=1))

    # self-check: every cookie used exactly once as a new card or milestone
    new = [v["slug"] for v in slots.values() if not v["dup"]]
    ms = [s for v in milestones.values() for s in v]
    assert len(new) == len(set(new)) == 172, len(set(new))
    assert sorted(new + ms) == sorted(c["slug"] for c in cookies)
    first_math_basic = [slots[f"{s['id']}|b"]["slug"] for s in order["math"][:7]]
    assert set(first_math_basic) == set(by["common"]), "first 7 Math Basic rewards should be the commons"
    print(f"rewards.json: {len(slots)} slots, {len(new)} new cards, {len(slots) - len(new)} star slots, "
          f"{len(ms)} milestone cards")


if __name__ == "__main__":
    main()
