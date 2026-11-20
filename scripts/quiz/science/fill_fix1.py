"""Round sci-fill-fix1-2026-11-20 (coordinator review): (1) circuit() main switch now in series, figures redrawn, verdicts renewed;
(2) cv-119 reworded; (3) 'the same ...' stems made standalone; (4) ht-221 states the same metal. Content changes get new keys."""
import json, re, glob
from fillkit import ITEMS, REVIEW, ship
from figs_circuit import circuit

# figure-only redraws (same question, same answer): keys keep, verdict renewed
REDRAWN = "ci-013 ci-102 ci-103 ci-104 ci-105 ci-106 ci-107 ci-813 ci-114 ci-121 ci-124 ci-201 ci-211 ci-212 ci-213 ci-215 ci-218".split() + \
          "cv-013 cv-105 cv-121 cv-206 cv-915".split()
MANUAL = {  # key -> dict(stem=(old,new)) / full stem / fig
 "ci-205": dict(stem="A circuit has a cell, a closed switch S and three bulbs P, Q and R, all one after another in a single path. Which statement is correct?",
                fig=lambda: circuit([[("L", "P"), ("L", "Q"), ("L", "R")], [("S", "S", True), ("B", 1)]], caption="Three bulbs in one path", W=340)),
 "cv-119": dict(stem="Circuit A has two cells in series and one bulb. Circuit B has the same bulb with only one cell. How does the brightness of the bulb in B compare with A?"),
 "ht-221": dict(stem=("Two metal blocks of the same size,", "Two blocks of the same size, made of the same metal,")),
 "ht-217": dict(stem="Three cups hold the same amount of hot water at the same starting temperature and are left in a room. The table shows the temperature of each after 30 min. Which cup gave the most heat to the room?"),
 "fi-420": dict(stem="A student rolls a toy car down a ramp onto different surfaces and measures how far it travels each time. Which is the variable that is measured?"),
 "he-017": dict(stem="Rods A, B and C are heated at one end, as shown. Which rod is the poorest conductor of heat?"),
}
SAME = [(r"^In the same (experiment|circuit|graph|table|results)", r"In the \1 shown"), (r"^Using the same (experiment|circuit|graph|table|results)", r"Using the \1 shown"),
        (r"^For the same leaf", "For the leaf shown")]
SAME_PRE = [(r"^In the same", "In the"), ]


def newstem(it):
    k = it["key"]
    m = MANUAL.get(k)
    if m and isinstance(m.get("stem"), str):
        return m["stem"]
    if m and "stem" in m:
        assert m["stem"][0] in it["stem"], k
        return it["stem"].replace(*m["stem"])
    s = it["stem"]
    for a, b in SAME:
        s2 = re.sub(a, b, s)
        if s2 != s:
            return s2
    return None


if __name__ == "__main__":
    rv = json.loads(REVIEW.read_text())
    R = "sci-fill-fix1-2026-11-20"
    subs = {}
    for fn in sorted(glob.glob(str(ITEMS / "*.json"))):
        d = json.load(open(fn))
        sub = d["subtopic"]; subs[sub] = fn.split("/")[-1]
        keys = {it["key"] for it in d["items"]}
        for it in d["items"]:
            ns = newstem(it)
            if ns is None:
                if it["key"] in REDRAWN:
                    rv.pop(f"{sub}|{it['key']}", None)
                continue
            m = MANUAL.get(it["key"], {})
            it["stem"] = ns
            if "fig" in m:
                it["figure"] = m["fig"]()
            elif it["key"] in REDRAWN:
                pass
            rv.pop(f"{sub}|{it['key']}", None)
            pre, num = it["key"].split("-")
            for off in (700, 800, 900):
                nk = f"{pre}-{int(num) + off}"
                if nk not in keys:
                    break
            keys.add(nk); it["key"] = nk
        open(fn, "w").write(json.dumps(d, ensure_ascii=False, indent=2) + "\n")
    REVIEW.write_text(json.dumps(rv, ensure_ascii=False, indent=1) + "\n")
    n = 0
    for sub, fn in subs.items():
        n += ship(sub, fn, R, "coordinator fixes: standalone stem / redrawn figure rechecked by render; one defensible answer")
    print("shipped", n)
