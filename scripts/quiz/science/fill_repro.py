"""PSLE-style Intermediate and Competent items for sci-cycles-repro-plants (round sci-fill-repro-2026-11-20).
    python3 scripts/quiz/science/fill_repro.py
"""
from fillkit import add, table, graph, ship, lint
from figs_flower import flower

SUB, FILE, PAT = "sci-cycles-repro-plants", "sci-plant-repro.json", "sci-pat-plant-reproduction"
FT = "sci-pat-fair-test-design"
RD = "sci-pat-read-data"
FL = lambda m, o=1: (lambda: flower(m, o))
M1 = {"A": "petal", "B": "anther", "C": "stigma", "D": "ovary"}
M2 = {"P": "stigma", "Q": "ovary", "R": "petal", "S": "anther"}
M3 = {"W": "anther", "X": "ovary", "Y": "stigma", "Z": "petal"}
M4 = {"A": "ovary", "B": "stigma", "C": "anther", "D": "filament"}
M5 = {"A": "stigma", "B": "ovule", "C": "petal", "D": "anther"}
M6 = {"P": "petal", "Q": "ovary", "R": "anther", "S": "stigma"}


def germ_table():
    return table(["Set-up", "Cotton wool", "Place"], [["P", "dry", "warm room"], ["Q", "wet", "warm room"], ["R", "wet", "inside a fridge"], ["S", "dry", "inside a fridge"]], [70, 100, 130], "Bean seeds in four dishes")


def fruit_table():
    return table(["Fruit", "What it looks like"], [["P", "thin, papery wing; dry and light"], ["Q", "soft, sweet, bright red flesh"], ["R", "covered in small hooks"], ["S", "hollow, light, waterproof husk"]], [60, 230], "Four kinds of fruit")


def fair_table():
    return table(["Set-up", "Cotton wool", "Place", "Light"], [["P", "wet", "warm room", "dark"], ["Q", "wet", "fridge", "dark"], ["R", "wet", "warm room", "light"], ["S", "dry", "fridge", "light"]], [60, 90, 100, 70], "Seeds in four set-ups")


def air_table():
    return table(["Set-up", "Seeds placed in", "Place"], [["P", "wet cotton wool", "warm room"], ["Q", "dry cotton wool", "warm room"], ["R", "boiled, cooled water|with oil on top", "warm room"], ["S", "tap water with no oil", "warm room"]], [60, 200, 90], "Four set-ups for bean seeds")


def results_table():
    return table(["Set-up", "Seeds in dish", "Seeds that germinated after one week"], [["P", "10", "9"], ["Q", "10", "0"], ["R", "10", "0"], ["S", "10", "6"]], [60, 90, 200], "Results of the four set-ups")


def temp_graph():
    return graph(["5", "15", "25", "35", "45"], [("seeds", [0, 4, 9, 6, 0])], 10, "Temperature (°C)", "Seeds germinated", "Germination of 10 seeds at each temperature", ystep=2)


def days_graph():
    return graph(["1", "2", "3", "4", "5", "6"], [("Warm room", [0, 20, 60, 85, 90, 90]), ("Cold room", [0, 0, 5, 10, 20, 25])], 100, "Day", "Seeds germinated (%)", "Seeds germinated in two rooms", ystep=20)


def water_bars():
    return graph(["0", "5", "10", "20"], [("s", [0, 8, 9, 3])], 10, "Water given each day (mL)", "Seeds germinated", "Germination of 10 seeds", ystep=2, bars=True)


def own(n):
    return n

def W(t, tag, why):
    return (t, tag, why)

P = []
def q(*a):
    P.append(a)

I = "intermediate"
C = "competent"
# ---------------- intermediate ----------------
q("rq-101", I, 2, PAT, "The picture shows a flower cut in half. Which part makes pollen?", "Part B",
  [W("Part A", "wrong-part", "Part A is a petal. Petals are brightly coloured to attract insects. They do not make pollen."), W("Part C", "wrong-part", "Part C is the stigma, which receives pollen. It does not make it."), W("Part D", "wrong-part", "Part D is the ovary, which holds the ovules. It does not make pollen.")],
  ["Pollen is made in the anther (part B)."], FL(M1))
q("rq-102", I, 2, PAT, "In the picture of the flower, pollen from another flower must land on which part for the flower to make seeds?", "Part P",
  [W("Part Q", "wrong-part", "Part Q is the ovary. Pollen lands on the stigma at the top, not on the ovary."), W("Part R", "wrong-part", "Part R is a petal. Insects may land on it, but the pollen must reach the stigma."), W("Part S", "wrong-part", "Part S is an anther. It makes pollen and has pollen on it already.")],
  ["Pollen has to land on the stigma (part P). That is called pollination."], FL(M2))
q("rq-103", I, 2, PAT, "The picture shows a flower cut in half. After fertilisation, which part will grow into a seed?", "Part B",
  [W("Part A", "wrong-part", "Part A is the stigma. It only receives pollen and does not become the seed."), W("Part C", "wrong-part", "Part C is a petal. Petals wither after pollination."), W("Part D", "wrong-part", "Part D is an anther. It makes pollen and does not become the seed.")],
  ["Part B is the ovule inside the ovary. After fertilisation, the ovule grows into the seed."], FL(M5))
q("rq-104", I, 2, PAT, "The picture shows a flower cut in half. After pollination and fertilisation, which part grows into the fruit?", "Part X",
  [W("Part W", "wrong-part", "Part W is an anther. It makes pollen, and it dries up after the pollen is gone."), W("Part Y", "wrong-part", "Part Y is the stigma. It receives pollen and does not grow into the fruit."), W("Part Z", "wrong-part", "Part Z is a petal. Petals wither after pollination.")],
  ["The ovary (part X) holds the ovules. It grows into the fruit and the ovules become seeds."], FL(M3))
q("rq-105", I, 2, PAT, "Look at the picture of the flower. Part D is a thin stalk that holds up part C. What is the job of part D?", "To hold the anther up where pollen can be carried off",
  [W("To make the pollen that the flower needs for seeds", "wrong-part", "Pollen is made in the anther (part C), not in the stalk that holds it."), W("To grow into the fruit once pollination has taken place", "wrong-part", "The ovary (part A) grows into the fruit, not the stalk."), W("To catch pollen that is brought from other flowers", "wrong-part", "Pollen is caught by the stigma (part B).")],
  ["Part D is the filament. It holds the anther up where wind or insects can reach the pollen."], FL(M4))
q("rq-106", I, 2, PAT, "A flower has small green petals and no smell. Its anthers hang outside the flower and its stigma is feathery. How is this flower most likely pollinated?", "By the wind",
  [W("By bees", "wrong-feature", "Bees are attracted by large, bright, scented flowers with nectar. This flower has none of these."), W("By butterflies", "wrong-feature", "Butterflies visit bright, sweet-smelling flowers, which this flower is not."), W("By birds", "wrong-feature", "Birds that pollinate flowers visit large, brightly coloured flowers.")],
  ["Small dull flowers with hanging anthers and a feathery stigma are made for wind pollination."], None)
q("rq-107", I, 2, PAT, "Which of these features helps a flower to be pollinated by insects?", "It makes a sweet liquid in the flower",
  [W("Its pollen is very light and dry", "wind-feature", "Very light, dry pollen is blown by the wind. Insect flowers have sticky pollen."), W("Its stigma hangs far outside the flower", "wind-feature", "A stigma that hangs out is found on wind-pollinated flowers, to catch pollen from the air."), W("Its petals are small and green", "wind-feature", "Small green petals do not attract insects. They belong to wind-pollinated flowers.")],
  ["The sweet liquid (nectar) makes insects come to the flower, and pollen sticks to them as they feed."], None)
q("rq-108", I, 2, PAT, "Grass flowers are pollinated by the wind. Why does a grass flower make a very large amount of pollen?", "Most pollen is blown away and little lands on a stigma",
  [W("The pollen must feed the insects that visit the flower", "wrong-idea", "Grass flowers are not visited by insects for food. The wind carries the pollen."), W("The pollen is needed to make the petals bright", "wrong-idea", "Pollen has nothing to do with the colour of the petals."), W("The pollen turns into the fruit", "wrong-idea", "The fruit grows from the ovary, not from the pollen.")],
  ["The wind blows pollen in all directions, so a lot is wasted.", "Making a lot gives a better chance that some lands on a stigma."], None)
q("rq-109", I, 2, PAT, "A bee visits a flower P and then a flower Q of the same kind. Where must some pollen from flower P land for a seed to form in flower Q?", "On the stigma of flower Q",
  [W("On a petal of flower Q, which attracts the bee", "wrong-part", "A petal only attracts insects. Pollen on a petal cannot lead to seeds."), W("On the anther of flower Q, which makes pollen", "wrong-part", "The anther makes pollen. Pollen must land on a stigma."), W("On the stem that holds up flower Q", "wrong-part", "Pollen on the stem cannot reach the ovules.")],
  ["Pollination is when pollen lands on a stigma of a flower of the same kind."], None)
q("rq-110", I, 2, PAT, "A farmer covers some flowers of a gourd plant with net bags that keep insects out. These flowers do not make fruits. What is the best reason?", "Pollen was not carried to the stigmas",
  [W("The petals did not get enough sunlight", "wrong-idea", "The net bags let light in, and petals do not make the fruit."), W("The roots could not take in water", "wrong-idea", "The bags cover the flowers, not the roots."), W("The anthers made too much pollen", "wrong-idea", "Too much pollen would not stop a fruit forming. The stigma needs to receive pollen.")],
  ["Insects carry pollen from flower to flower.", "Without insects, no pollen reaches the stigmas, so no seeds or fruits form."], None)
q("rq-111", I, 2, PAT, "Which of the following describes fertilisation in a flowering plant?", "A male cell from pollen joins a female cell in an ovule",
  [W("Pollen from an anther lands on a stigma", "mix-up", "That is pollination. Fertilisation happens afterwards, when the cells join."), W("An insect carries pollen from one flower to another", "mix-up", "That is how pollen is carried. It is not fertilisation."), W("A seed is carried far away from the parent plant", "mix-up", "That is seed dispersal, which happens after the seed has formed.")],
  ["In fertilisation, a male cell from the pollen joins a female cell inside an ovule."], None)
q("rq-112", I, 2, PAT, "Kai put bean seeds on cotton wool in dishes P, Q, R and S as shown in the table. In which dish will the seeds most likely germinate?", "Q",
  [W("P", "missing-water", "The cotton wool in P is dry. Seeds need water to germinate."), W("R", "too-cold", "R is inside a fridge. Seeds need warmth to germinate."), W("S", "missing-both", "S is dry and cold, so it lacks both water and warmth.")],
  ["Seeds need water, air and warmth to germinate.", "Only Q has wet cotton wool in a warm room."], germ_table)
q("rq-113", I, 2, PAT, "The graph shows how many of 10 bean seeds germinated at five temperatures. At which temperature did the most seeds germinate?", "25 °C",
  [W("5 °C", "misread", "At 5 °C no seeds germinated. This is too cold."), W("15 °C", "misread", "At 15 °C only 4 seeds germinated, fewer than at 25 °C."), W("45 °C", "misread", "At 45 °C no seeds germinated. This is too hot.")],
  ["The highest point on the graph is at 25 °C, with 9 seeds germinated."], temp_graph)
q("rq-114", I, 3, PAT, "The table shows four kinds of fruit. Which fruit is most likely to be spread when an animal eats it and drops the seeds far away?", "Q",
  [W("P", "wrong-agent", "P has a thin wing, so the wind carries it away."), W("R", "wrong-agent", "R has hooks, which catch on an animal's fur. The animal does not need to eat it."), W("S", "wrong-agent", "S is light and hollow, so it floats on water.")],
  ["A soft, sweet, bright fruit is eaten by animals. The seeds pass out in the droppings far from the parent plant."], fruit_table)
q("rq-115", I, 3, PAT, "In the table of four fruits, which fruit is most likely to be carried away on the fur of a passing animal?", "R",
  [W("P", "wrong-agent", "P has a wing, so it is carried by the wind."), W("Q", "wrong-agent", "Q is soft and sweet and is spread by animals that eat it."), W("S", "wrong-agent", "S is light and waterproof and floats on water.")],
  ["The small hooks of R catch on fur and clothes, so the fruit is carried to new places."], fruit_table)
q("rq-116", I, 3, PAT, "The table shows four kinds of fruit. Which fruit is most likely to be spread by water?", "S",
  [W("P", "wrong-agent", "P is dry and light with a wing. It is made for the wind."), W("Q", "wrong-agent", "Q is a juicy fruit that animals eat."), W("R", "wrong-agent", "R has hooks and sticks to animals.")],
  ["A light, hollow, waterproof husk floats, so the fruit is carried far by water."], fruit_table)
q("rq-117", I, 1, PAT, "Tiny brown dots form on the underside of a fern leaf. Each dot holds many spores. Which statement about the spores is correct?", "The spores are blown away and may grow into new ferns in damp places",
  [W("The spores are the fruits that grow on the fern leaf", "wrong-idea", "Ferns do not make flowers or fruits. Spores are not fruits."), W("The spores stay on the leaf and grow into new ferns there", "wrong-idea", "Spores are blown away from the parent fern. They do not grow on the leaf."), W("The spores must be carried by bees from fern to fern", "wrong-idea", "Spores are carried by the wind. Ferns have no flowers to attract bees.")],
  ["Ferns reproduce by spores. The very light spores are blown by the wind.", "A spore that lands in a damp place can grow into a new fern."], None)
q("rq-118", I, 1, PAT, "Small plantlets grow along the edge of a leaf of a Bryophyllum plant. When they fall onto soil, they grow into new plants. From which part of the parent plant do the new plants grow?", "The leaf",
  [W("The root", "wrong-part", "The plantlets are on the leaf edge, not on the roots."), W("The flower", "wrong-part", "No flower is needed. The plantlets grow on the leaf."), W("The seed", "wrong-part", "These new plants do not come from seeds.")],
  ["The new plants grow from the leaf of the parent plant, without seeds."], None)
q("rq-119", I, 1, PAT, "A strawberry plant sends out long stems along the ground. A new plant grows at the end of each stem. Which statement about this is correct?", "The new plants grow without seeds",
  [W("The new plants grow only after bees pollinate the stems", "wrong-idea", "Pollination is about flowers making seeds. These stems are not flowers."), W("The new plants grow from spores on the stems", "wrong-idea", "Strawberry plants are flowering plants. They do not make spores."), W("The new plants grow only when the parent dies", "wrong-idea", "The parent plant keeps living while the new plants grow.")],
  ["The long stems grow new plants. No seeds are needed for this way of reproducing."], None)
q("rq-120", I, 1, PAT, "A gardener wants new plants without waiting for any flower to be pollinated first. Which of these should he plant?", "A piece of rose stem",
  [W("A bean seed", "wrong-idea", "A seed forms only after a flower has been pollinated and fertilised."), W("A mango seed", "wrong-idea", "A mango seed also comes from a pollinated flower."), W("A sunflower seed", "wrong-idea", "A sunflower seed also forms after pollination.")],
  ["Seeds only form after pollination and fertilisation.", "A piece of rose stem can grow roots and leaves into a new plant with no flowers involved."], None)
q("rq-121", I, 2, PAT, "The picture shows a flower cut in half. The ovary of this flower holds 3 ovules. All 3 ovules are fertilised. How many seeds can the fruit have?", "3",
  [W("1", "miscount", "Each fertilised ovule becomes one seed, so 3 ovules give more than 1 seed."), W("2", "miscount", "All 3 ovules are fertilised, so 3 seeds form, not 2."), W("6", "miscount", "One ovule makes one seed. The number of seeds cannot be more than the number of ovules.")],
  ["Each fertilised ovule grows into one seed.", "3 fertilised ovules give 3 seeds."], FL({"A": "ovary", "B": "stigma", "C": "petal"}, 3))
q("rq-122", I, 2, PAT, "A tomato fruit has 40 seeds. How many ovules in the flower were fertilised to form this fruit?", "40",
  [W("1", "miscount", "A flower's ovary has many ovules. Each seed comes from its own ovule."), W("4", "miscount", "Each seed comes from one fertilised ovule, so there must be as many ovules as seeds."), W("80", "miscount", "Each ovule makes one seed, not two.")],
  ["One fertilised ovule makes one seed, so 40 seeds come from 40 fertilised ovules."], None)
q("rq-123", I, 2, PAT, "Which of the following lists the events in the correct order, from first to last?", "Pollination, fertilisation, seeds form, seeds are dispersed",
  [W("Fertilisation, pollination, fruit and seeds form, seeds are dispersed", "wrong-order", "Pollen must land on the stigma before the cells can join, so pollination comes first."), W("Pollination, seeds are dispersed, fertilisation, fruit and seeds form", "wrong-order", "Seeds are dispersed only after they have formed."), W("Pollination, fruit and seeds form, fertilisation, seeds are dispersed", "wrong-order", "The fruit and seeds form only after fertilisation.")],
  ["Pollen lands on the stigma, then the cells join, then the ovary and ovules grow, and the seeds are carried away."], None)

# ---------------- competent ----------------
q("rq-201", C, 2, PAT, "Which of the following statements about pollination are correct?\nA: Pollen lands on the stigma.\nB: Pollen can only be carried by insects.\nC: Pollination happens before fertilisation.\nD: Pollination is when a male cell joins a female cell.", "A and C only",
  [W("A and B only", "mix-up", "B is wrong. Wind and some animals also carry pollen."), W("B and D only", "mix-up", "Both B and D are wrong. Joining of cells is fertilisation."), W("C and D only", "mix-up", "D is wrong. The joining of the male and female cells is fertilisation, not pollination.")],
  ["A is correct: pollination is pollen landing on a stigma.", "C is correct: the cells can join only after pollen has landed.", "B is wrong (wind, water and animals carry pollen). D describes fertilisation."], None)
q("rq-202", C, 2, PAT, "Which of the following statements about a flowering plant are correct?\nA: The ovary grows into the fruit.\nB: Pollen is made in the stigma.\nC: Each fertilised ovule becomes a seed.\nD: Petals grow into the seeds.", "A and C only",
  [W("A and B only", "mix-up", "B is wrong. Pollen is made in the anther."), W("B and D only", "mix-up", "Both are wrong. The stigma receives pollen and petals wither."), W("C and D only", "mix-up", "D is wrong. Petals wither after pollination.")],
  ["A and C are correct. B is wrong because pollen is made in the anther. D is wrong because petals do not become seeds."], None)
q("rq-203", C, 2, PAT, "Four flowers on a plant were treated as shown in the table. Insects visited all the flowers. Which flower is least able to make seeds?", "R",
  [W("P", "wrong-reasoning", "P has no petals, so fewer insects may visit, but its stigma can still receive pollen."), W("Q", "wrong-reasoning", "Q has no anthers, but it can still receive pollen carried from other flowers."), W("S", "wrong-reasoning", "S has no sepals. The sepals do not take part in making seeds.")],
  ["Seeds form only if pollen lands on a stigma.", "R has no stigma, so pollen cannot reach its ovules."],
  lambda: table(["Flower", "Part removed"], [["P", "all the petals"], ["Q", "all the anthers"], ["R", "the stigma"], ["S", "the sepals"]], [70, 180], "Four flowers on one plant"))
q("rq-204", C, 2, FT, "Four set-ups use bean seeds, as in the table. Which two set-ups should Mei compare to find out if seeds need warmth to germinate?", "P and Q",
  [W("P and R", "wrong-pair", "P and R differ in light, not in warmth."), W("Q and S", "wrong-pair", "Q and S differ in water, light and so on. More than one thing is different."), W("R and S", "wrong-pair", "R and S differ in water, not in warmth.")],
  ["For a fair test, only one thing should differ.", "P and Q differ only in the place (warm or cold). The wetness and the darkness are the same."], fair_table)
q("rq-205", C, 2, RD, "In the four set-ups of the table, only the seeds in P and R germinated. Which conclusion is correct?", "Seeds germinate with or without light",
  [W("Seeds need light to germinate", "wrong-conclusion", "P was dark and the seeds still germinated."), W("Seeds need water to germinate", "invalid-comparison", "S differs from the others in both water and place, so this test does not show it."), W("Seeds germinate better in a cold place", "wrong-conclusion", "The seeds in the cold place (Q and S) did not germinate at all.")],
  ["P (dark) and R (light) are the same except for light. Both germinated, so light is not needed.", "S cannot show the need for water as it also differs in place."], fair_table)
q("rq-206", C, 2, RD, "The graph shows seeds germinating in a warm room and a cold room over 6 days. Which statement is supported by the graph?", "From Day 2, more seeds had germinated in the warm room",
  [W("All the seeds in the warm room had germinated by Day 6", "misread", "At Day 6, only 90 % had germinated, not all."), W("No seeds germinated at all in the cold room", "misread", "By Day 6, 25 % of the seeds in the cold room had germinated."), W("Seeds in the cold room germinated faster than in the warm room", "reversed", "The warm room line is always higher from Day 2.")],
  ["On every day from Day 2 the warm room line is above the cold room line.", "At Day 6 the warm room has 90 % and the cold room 25 %."], days_graph)
q("rq-207", C, 3, PAT, "The table shows four kinds of fruit. On a windy island there are no animals and no streams. Which fruit is most likely to be spread far from its parent plant there?", "P",
  [W("Q", "wrong-agent", "Q needs an animal to eat it, but there are no large animals."), W("R", "wrong-agent", "R needs an animal's fur to catch on to."), W("S", "wrong-agent", "S floats, but there are no streams to carry it.")],
  ["With only wind, the fruit that can fly is carried: the one with a thin papery wing."], fruit_table)
q("rq-208", C, 2, PAT, "A farmer sprays a strong insecticide that kills all the bees in his orchard. Fewer fruits grow on his trees that season. What is the best reason?", "Less pollen reached the stigmas, so fewer flowers were fertilised",
  [W("The trees could not make any pollen without the bees", "wrong-idea", "The anthers of the trees make pollen on their own. Bees only carry it."), W("The petals fell off too soon for the fruits to grow", "wrong-idea", "Petals falling off is normal after pollination. It does not reduce fruit by itself."), W("The roots took in less water from the soil that season", "wrong-idea", "The insecticide killed bees. It was not about water in the roots.")],
  ["Bees carry pollen to stigmas.", "With no bees, fewer stigmas get pollen, fewer ovules are fertilised and fewer fruits form."], None)
q("rq-209", C, 3, PAT, "Seedlings that grow right under their parent plant often grow poorly. What is the best reason?", "They compete with the parent for light and water",
  [W("They cannot be pollinated by insects or wind", "wrong-idea", "Pollination happens in flowers, long before seedlings grow."), W("They cannot make flowers or fruits", "wrong-idea", "Seedlings are young. Flowers come later and are not the problem here."), W("They have lost their seed coat too early", "wrong-idea", "A seed coat protects the seed. It has no effect on how the seedling grows later.")],
  ["Seedlings under the parent share the same light, water and soil.", "That is why dispersing seeds far away helps new plants grow well."], None)
q("rq-210", C, 1, PAT, "Which statements about spores and seeds are correct?\nA: Both can grow into new plants.\nB: A seed has stored food but a spore does not.\nC: Spores are made in flowers.\nD: Ferns make seeds inside fruits.", "A and B only",
  [W("A and C only", "mix-up", "C is wrong. Ferns and mosses have no flowers."), W("B and D only", "mix-up", "D is wrong. Ferns have no fruits or seeds."), W("C and D only", "mix-up", "Both are wrong. Plants with spores have no flowers, fruits or seeds.")],
  ["A and B are correct. C and D are wrong because spore plants have no flowers, fruits or seeds."], None)
q("rq-211", C, 1, PAT, "A gardener takes cuttings from a rose bush that has red flowers and plants them. What colour are the flowers of the new plants most likely to be?", "Red, because they grow from a part of the parent plant",
  [W("White, because cuttings are weaker than seeds", "wrong-idea", "A cutting grows into a plant like its parent. Weakness does not change the colour."), W("Pink, because the colour mixes with the soil", "wrong-idea", "Soil does not change the colour of the flowers."), W("Any colour, because insects must pollinate the cuttings", "wrong-idea", "Cuttings grow from stems. No pollination is involved.")],
  ["A cutting is a part of the parent plant, so the new plant is like the parent. Its flowers are red."], None)
q("rq-212", C, 2, FT, "Aisha wants to find out if seeds need air to germinate. Which two set-ups in the table should she compare?", "R and S",
  [W("P and Q", "wrong-pair", "P and Q differ in water. They test water, not air."), W("P and S", "wrong-pair", "P has cotton wool and S has tap water, so more than the air differs."), W("Q and R", "wrong-pair", "Q is dry and R is wet, so water is different too.")],
  ["R and S are both in water in a warm room. Only the air differs: R's water has no air (boiled and covered with oil)."], air_table)
q("rq-213", C, 2, RD, "Aisha's results are in the table. Which conclusion is correct?", "Seeds need both water and air to germinate",
  [W("Seeds need light to germinate", "not-tested", "Light was not tested in any of the set-ups."), W("Seeds germinate best when covered with water", "wrong-conclusion", "P (damp cotton wool) had more germinating seeds than S (in water)."), W("Seeds can germinate without water if there is air", "wrong-conclusion", "Q had air but no water and no seeds germinated.")],
  ["Q (no water) shows that water is needed; R (no air) shows that air is needed.", "P has both and nine seeds germinated."], results_table)
q("rq-214", C, 2, PAT, "The picture shows a flower. Which row correctly gives the job of two of its labelled parts?", "P: attracts insects; Q: grows into the fruit",
  [W("P: makes pollen; Q: grows into the fruit", "wrong-part", "P is a petal, which attracts insects. It does not make pollen."), W("P: attracts insects; Q: receives pollen", "wrong-part", "Q is the ovary. The stigma (S) receives pollen."), W("P: receives pollen; Q: makes pollen", "wrong-part", "Both are wrong: the petal does not receive pollen and the ovary does not make it.")],
  ["P is a petal and Q is the ovary. Petals attract insects, and the ovary grows into the fruit."], FL(M6))
q("rq-215", C, 2, PAT, "Soon after pollination, the petals of a flower wither and fall off, but the ovary grows bigger. Why can the flower afford to lose its petals?", "The petals have done their job of attracting insects",
  [W("The petals are needed to carry pollen down to the ovary", "wrong-idea", "Petals do not carry pollen. Insects and wind do."), W("The petals have changed into the seeds of the fruit", "wrong-idea", "The seeds come from the ovules, not the petals."), W("The petals would stop the ovary from growing bigger", "wrong-idea", "Petals do not affect the growth of the ovary.")],
  ["Petals attract insects. Pollination has happened, so they are no longer needed."], None)
q("rq-216", C, 2, FT, "Ravi gives 5 mL, 10 mL and 20 mL of water each day to three dishes with 10 bean seeds each, in the same warm room. What should he measure to find out how the amount of water affects germination?", "The seeds that germinate in each dish",
  [W("The temperature of the room each day", "wrong-variable", "The temperature must stay the same, so it is not what he measures."), W("The colour of the dishes he uses", "wrong-variable", "The colour of the dish is not related to the question."), W("The number of seeds put in each dish", "wrong-variable", "This is the same (10) in all dishes. It is a variable kept the same.")],
  ["The amount of water is the one thing changed.", "The results to measure are how many seeds germinate in each dish."], None)
q("rq-217", C, 2, RD, "The bar graph shows how many of 10 seeds germinated when given different amounts of water each day. Which conclusion is best supported?", "Seeds germinate best with some water, and too much lowers germination",
  [W("The more water the seeds are given, the more seeds germinate", "misread", "At 20 mL only 3 seeds germinated, fewer than at 10 mL."), W("Seeds do not need any water to germinate at all", "misread", "With no water, none of the seeds germinated."), W("Seeds that were given 5 mL of water germinated best", "misread", "Seeds given 10 mL did best (9 seeds), better than 5 mL (8 seeds).")],
  ["No water gave 0 seeds, 10 mL gave the most (9) and 20 mL gave only 3.", "So some water is needed but too much is harmful."], water_bars)
q("rq-218", C, 2, PAT, "A gardener grows a herb under a net that keeps out insects. He gently shakes the flowers every day and the plant makes fruits. How does shaking help?", "Pollen is shaken from the anthers onto the stigmas",
  [W("The shaking makes the roots take in more water", "wrong-idea", "Shaking flowers does not change how roots take in water."), W("The shaking joins the male and female cells directly", "wrong-idea", "The cells join inside the ovule after pollen reaches the stigma. Shaking only helps pollination."), W("The shaking makes the petals grow into fruits", "wrong-idea", "Fruits grow from the ovary, not the petals.")],
  ["Without insects, shaking moves pollen from the anthers to the stigmas, so pollination can happen."], None)
q("rq-219", C, 3, PAT, "Birds eat the berries of a plant. The seeds inside have a hard, smooth coat. Why is the hard coat useful to the plant?", "It protects the inside from the bird's stomach juices",
  [W("It makes the seeds light enough to be blown away by wind", "wrong-idea", "A hard coat does not make a seed lighter. These seeds travel inside birds."), W("It helps the seeds to stick to the bird's feathers and legs", "wrong-idea", "A smooth coat does not stick. Hooks would do that."), W("It lets the seeds float on water", "wrong-idea", "These seeds are carried by birds, not by water.")],
  ["The seeds pass through the bird's body and come out in the droppings.", "The hard coat protects the inside of the seed from the juices that digest food."], None)
q("rq-220", C, 2, PAT, "Pollen from a rose flower lands on the stigma of a hibiscus flower. What is most likely to happen?", "Pollination happens but fertilisation does not",
  [W("Fertilisation happens and the hibiscus makes seeds", "wrong-idea", "Pollen can only fertilise ovules of the same kind of plant."), W("Neither pollination nor fertilisation happens", "wrong-idea", "Pollination is simply pollen landing on a stigma, so it has happened."), W("Fertilisation happens but the flower makes no pollen", "wrong-idea", "Fertilisation does not happen, and the anthers still make pollen.")],
  ["Pollination is pollen landing on a stigma, so it does happen.", "The male cell of a rose cannot join the female cell of a hibiscus, so there is no fertilisation."], None)
q("rq-221", C, 1, PAT, "Which of the following is evidence that a plant can reproduce without seeds?", "A leaf placed on wet soil grows roots and a plant",
  [W("A seed grows into a seedling in wet cotton wool", "wrong-idea", "That is a seed growing, so it needs a seed."), W("Bees visit the flowers of a plant", "wrong-idea", "Bees carrying pollen lead to seeds."), W("A fruit has many seeds inside it", "wrong-idea", "That shows seeds, not reproduction without them.")],
  ["A new plant that grows from a leaf grows from part of the parent plant. No seed is involved."], None)
q("rq-222", C, 3, PAT, "A coconut has a fibrous husk that holds air. Which of the following is the best reason why this helps the coconut palm reproduce?", "The coconut floats and is carried by the sea to a new beach",
  [W("The coconut flower is pollinated by sea water", "wrong-idea", "The husk is on the fruit, which forms after pollination."), W("The husk stops the seed from ever germinating on land", "wrong-idea", "The seed can germinate when it reaches a beach."), W("The husk lets the wind lift it up like a wing", "wrong-idea", "A coconut is heavy. It is carried by water, not the wind.")],
  ["Air in the husk makes the coconut float.", "Sea water carries it to a new beach where it can germinate."], None)
q("rq-223", C, 2, PAT, "A student says: 'A flower with no ovary can never make a seed.' Which reason supports the student's statement?", "Seeds grow from ovules, which are inside the ovary",
  [W("Seeds grow from pollen, which is made in the ovary of a flower", "wrong-idea", "Pollen is made in the anther, and seeds do not grow from pollen."), W("The ovary attracts the insects that carry the pollen", "wrong-idea", "Petals attract insects, not the ovary."), W("The ovary is the part that receives the pollen", "wrong-idea", "The stigma receives pollen.")],
  ["An ovule becomes a seed after fertilisation. Ovules are inside the ovary.", "Without an ovary there are no ovules."], None)

if __name__ == "__main__":
    n = add(SUB, FILE, P)
    print("added", n)
    lint(SUB, FILE, "rq-")
