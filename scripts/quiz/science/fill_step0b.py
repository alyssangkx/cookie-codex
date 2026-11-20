"""Round sci-fill-step0b-2026-11-20: clear WARN findings (figure-leak, stem-echo, near-dup-options) in existing items; content changes get a new key."""
import json
from fillkit import ITEMS, REVIEW, ship

# file: {old key: dict(stem=(old,new), opts={old:new}, fig={old:new}, sol=[...])}
P = {
 "sci-circuit-vars.json": {"cv-215": dict(sub="sci-systems-circuit-vars",
    opts={"Yes, each bulb has its own path to the cell": "Yes, each bulb is joined straight across the cell"},
    fig={"Two bulbs, separate paths": "Bulbs P and Q on one cell"})},
 "sci-circuit.json": {
  "ci-113": dict(sub="sci-systems-circuit", fig={"Two bulbs, two paths": "Circuit with a switch S"}),
  "ci-220": dict(sub="sci-systems-circuit", stem=("covered in thick plastic tape", "covered in thick sticky tape"))},
 "sci-photo-req.json": {
  "ph-013": dict(sub="sci-energy-photo-requirements", fig={"A leaf in bright light": "A leaf with part of it covered"}),
  "ph-117": dict(sub="sci-energy-photo-requirements", stem=("after a day in the light", "after a day on a sunny windowsill")),
  "ph-217": dict(sub="sci-energy-photo-requirements", stem=("a healthy plant in bright light", "a healthy green plant on a sunny day"))},
 "sci-plant-parts.json": {"pp-118": dict(sub="sci-systems-plant-parts-fn", stem=("These heads are bunches of flower buds.", "These heads are bunches of buds that have not opened.")), "pp-059": dict(sub="sci-systems-plant-parts-fn",
    opts={"Most of the water lost by the plant leaves through its leaves": "Taking off the leaves greatly cuts the water a plant loses"})},
 "sci-env-survival.json": {"es-025": dict(sub="sci-interactions-env-survival", stem=("kept in a dry box with no water for many days", "kept in a very dry box for many days"))},
 "sci-forces-investigate.json": {
  "fi-021": dict(sub="sci-interactions-forces-investigate", stem=("cut into two equal halves. What is the weight of one half, compared with the whole apple?", "cut into two equal pieces. How does the weight of one piece compare with the weight of the whole apple?"),
    opts={"It is half the weight of the whole apple": "It is half as heavy as the whole apple", "It is the same as the whole apple": "It is as heavy as the whole apple", "It is twice the weight of the whole apple": "It is twice as heavy as the whole apple"}),
  "fi-204": dict(sub="sci-interactions-forces-investigate", stem=("A spring was stretched by a very heavy load.", "A spring carried a very heavy load.")),
  "fi-209": dict(sub="sci-interactions-forces-investigate", stem=("on a rough floor and on a smooth floor.", "once on a floor covered with sandpaper and once on a polished floor."))},
 "sci-heat-effects.json": {"he-210": dict(sub="sci-energy-heat-effects", stem=("three cups wrapped in cloth, foil or nothing", "three cups covered with cloth, foil or nothing"))},
 "sci-plant-repro.json": {"rq-118": dict(sub="sci-cycles-repro-plants", stem=("along the edge of a leaf of a Bryophyllum plant", "along the notched edge of the parts of a Bryophyllum plant that make its food"))},
 "sci-adaptations.json": {"ae-216": dict(sub="sci-interactions-env-adapt",
    opts={"More fuel burnt, less carbon dioxide in the air, more heat trapped, Earth becomes warmer": "More fuel burnt, more oxygen in the air, more heat trapped, Earth becomes warmer"})},
}
if __name__ == "__main__":
    rv = json.loads(REVIEW.read_text())
    R = "sci-fill-step0b-2026-11-20"
    for fn, m in P.items():
        f = ITEMS / fn
        d = json.loads(f.read_text())
        keys = {it["key"] for it in d["items"]}
        for it in d["items"]:
            c = m.get(it["key"])
            if not c:
                continue
            if "stem" in c:
                assert c["stem"][0] in it["stem"], it["key"]
                it["stem"] = it["stem"].replace(*c["stem"])
            for o, n in c.get("opts", {}).items():
                assert o in it["options"], (it["key"], o)
                it["options"][it["options"].index(o)] = n
            for o, n in c.get("fig", {}).items():
                assert o in it["figure"], (it["key"], o)
                it["figure"] = it["figure"].replace(o, n)
            pre, num = it["key"].split("-")
            nk = f"{pre}-{int(num) + 700}"
            assert nk not in keys
            rv.pop(f"{c['sub']}|{it['key']}", None)
            it["key"] = nk
        f.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n")
    REVIEW.write_text(json.dumps(rv, ensure_ascii=False, indent=1) + "\n")
    n = 0
    for fn, m in P.items():
        sub = list(m.values())[0]["sub"]
        n += ship(sub, fn, R, "WARN fix: reworded, new key; one defensible answer unchanged")
    print("shipped", n)
