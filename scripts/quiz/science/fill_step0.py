"""Round sci-fill-step0-2026-11-20: reword fi- options so the correct one is not so often the longest (new keys), and top up
sci-cycles-life-cycles-compare Competent and sci-systems-plant-parts-fn to 25 per tier."""
import json
from fillkit import add, table, ITEMS, REVIEW, remove, ship

# old key -> {old option text: new option text}
FI = {
    "fi-003": {"To increase friction so the runner does not slip": "To give more grip on the ground"},
    "fi-011": {"Magnetic force": "The magnetic force of a magnet", "Gravitational force": "The gravitational force of the Earth"},
    "fi-012": {"A pen that clicks to push the tip out": "A pen that clicks open"},
    "fi-016": {"The magnetic force of the Earth": "The magnetic force between the Earth and it"},
    "fi-020": {"Downwards, towards the centre of the Earth": "Downwards, towards the Earth"},
    "fi-120": {"The type of surface": "The type of surface the car moves on", "The height of the ramp": "The height of the ramp used each time"},
    "fi-123": {"The Earth pulls the bag down with a force of 6 N": "The Earth pulls the bag down with 6 N"},
    "fi-213": {"The higher the ramp, the further the car moves": "A higher ramp makes the car go further"},
    "fi-215": {"The load and the first length of the springs": "The load and first length"},
    "fi-218": {"Its weight downwards and the elastic spring force upwards": "Its weight down and the spring force up"},
    "fi-224": {"Putting a thick rubber sheet under the cupboard": "Putting a rubber mat under it"},
    "fi-227": {"The material of the blocks and the table": "The material of the blocks and table"},
    "fi-229": {"Friction between the pads and the wheel produces heat": "Friction between pads and wheel makes heat"},
}


def reword_fi():
    f = ITEMS / "sci-forces-investigate.json"
    d = json.loads(f.read_text())
    old = []
    for it in d["items"]:
        m = FI.get(it["key"])
        if not m:
            continue
        hit = 0
        for i, o in enumerate(it["options"]):
            if o in m:
                it["options"][i] = m[o]
                hit += 1
        assert hit == len(m), it["key"]
        old.append(it["key"])
        it["key"] = "fi-%d" % (int(it["key"][3:]) + 300)
    f.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n")
    rv = json.loads(REVIEW.read_text())
    for k in old:
        rv.pop("sci-interactions-forces-investigate|" + k, None)
    REVIEW.write_text(json.dumps(rv, ensure_ascii=False, indent=1) + "\n")
    return old


PP, LC = "sci-systems-plant-parts-fn", "sci-cycles-life-cycles-compare"
PF, FT, RD, PH, LS = "sci-pat-plant-parts-function", "sci-pat-fair-test-design", "sci-pat-read-data", "sci-pat-photosynthesis", "sci-pat-life-cycle-stages"
B, I, C = "basic", "intermediate", "competent"
def W(t, tag, why): return (t, tag, why)
P = []
def q(*a): P.append(a)
q("pp-201", B, 1, PF, "A florist keeps cut roses in a vase of water. Which part of each rose lets the water travel up to the flower?", "The stem", [W("The thorns", "wrong-part", "Thorns do not carry water."), W("The petals", "wrong-part", "Petals are at the top. They do not carry water up."), W("The roots", "wrong-part", "Cut roses have no roots.")], ["The stem carries water up to the other parts."], None)
q("pp-202", B, 1, PF, "We eat lettuce in a salad. Which part of the lettuce plant are we mostly eating?", "The leaves", [W("The roots", "wrong-part", "Roots are under the soil. We do not eat them in lettuce."), W("The flowers", "wrong-part", "Lettuce is eaten before it flowers."), W("The seeds", "wrong-part", "We do not eat the seeds of lettuce.")], ["The green, leafy part of lettuce is its leaves."], None)
q("pp-203", I, 1, PF, "A farmer picks off all the flowers of a tomato plant before they can form fruits. Which job of the plant part is stopped?", "Making seeds for new plants", [W("Taking in water from the soil", "wrong-job", "This is the job of the roots."), W("Holding the plant up", "wrong-job", "This is the job of the stem."), W("Making food for the plant", "wrong-job", "This is mainly the job of the leaves.")], ["Flowers make the fruits and seeds."], None)
q("pp-204", I, 1, PF, "The roots of a tree spread out wide under the soil. How does this help the tree?", "It holds the tree firmly and takes in more water", [W("It helps the tree make food from sunlight", "wrong-job", "There is no sunlight under the soil. Leaves make food."), W("It carries food up to the leaves", "wrong-job", "Roots do not carry food up to the leaves."), W("It helps the tree catch more sunlight", "wrong-job", "Leaves catch the sunlight.")], ["Wide roots anchor the tree and reach more water."], None)
q("pp-205", I, 1, PH, "A gardener cuts all the leaves off a plant but leaves its stem and roots. After some weeks the plant is weaker. Why?", "It cannot make food without its leaves", [W("Its roots cannot take in any water at all", "wrong-idea", "The roots still take in water."), W("Its stem can no longer stand up", "wrong-idea", "The stem still holds up the plant."), W("It has too much food stored in its leaves", "wrong-idea", "The leaves were cut off, so they store nothing.")], ["Leaves make food, so without them the plant becomes weak."], None)
TB = lambda: table(["Plant", "Roots", "Leaves", "After 4 weeks"], [["P", "yes", "yes", "healthy"], ["Q", "yes", "cut off|each day", "weak"], ["R", "cut off", "yes", "wilted"]], [60, 80, 90, 110], "Three plants (same light, water, soil)")
q("pp-206", C, 2, FT, "The table shows three plants kept in the same place. Which two plants should be compared to find out if leaves are needed to keep a plant healthy?", "P and Q", [W("P and R", "wrong-pair", "P and R differ in their roots, not their leaves."), W("Q and R", "wrong-pair", "Q and R differ in both roots and leaves."), W("P only", "wrong-pair", "One plant cannot be compared with itself.")], ["P and Q differ only in the leaves."], TB)
q("pp-207", C, 2, RD, "Using the same table, what does plant R show?", "A plant needs roots to take in water", [W("A plant needs roots to make food", "wrong-job", "Roots do not make food."), W("A plant needs roots to catch light", "wrong-job", "Roots do not catch light."), W("A plant needs roots to carry food to its leaves", "wrong-job", "This is not shown. R wilted because it lacked water.")], ["With its roots cut off R wilted, so roots are needed for taking in water."], TB)
Q = []
Q.append(("lc-085", C, 3, LS, "How many stages are in the life cycle of a cockroach, and how many are in the life cycle of a mosquito?", "3 stages and 4 stages", [W("4 stages and 3 stages", "swapped", "A cockroach has no pupa, so it has fewer stages."), W("3 stages and 3 stages", "wrong-count", "A mosquito has egg, larva, pupa and adult."), W("4 stages and 4 stages", "wrong-count", "A cockroach has egg, nymph and adult only.")], ["Cockroach: egg, nymph, adult (3). Mosquito: egg, larva, pupa, adult (4)."], None))

if __name__ == "__main__":
    old = reword_fi()
    print("reworded", len(old))
    print(add(PP, "sci-plant-parts.json", P), add(LC, "sci-life-cycles.json", Q))
    R = "sci-fill-step0-2026-11-20"
    n = ship("sci-interactions-forces-investigate", "sci-forces-investigate.json", R, "option lengths reworded; new key")
    n += ship(PP, "sci-plant-parts.json", R, "top-up item checked: one defensible answer, no give-away")
    n += ship(LC, "sci-life-cycles.json", R, "top-up item checked")
    print("shipped", n)
