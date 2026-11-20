"""Original Science items written to refill plant-parts-fn and open env-adapt and repro-plants (round r3).

    python3 scripts/quiz/science/new_items.py     # idempotent: adds items whose key is not in the target file yet

Wording is original (PSLE paper framing: a short scenario, a picture where one helps, 4 options, 3 named mistakes).
Figures are code-made SVG (black and white, currentColor) or an existing line-art image copied from a sibling item.
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import figs_basic as F  # noqa: E402

ITEMS = HERE / "items"


def fig_of(key):
    for f in ITEMS.glob("*.json"):
        for it in json.loads(f.read_text())["items"]:
            if it["key"] == key and it.get("figure"):
                return it["figure"]
    raise KeyError(key)


def table_svg(rows):
    """Yes/No table of plant parts: rows = [(plant, roots, stem, leaves)]."""
    b = ""
    heads = ["Plant", "Roots", "Stem", "Leaves"]
    for j, h in enumerate(heads):
        b += F.box(10 + j * 80, 10, 78, 30, h, bold=True)
    for i, r in enumerate(rows):
        for j, c in enumerate(r):
            b += F.box(10 + j * 80, 44 + i * 34, 78, 30, c)
    return F.svg(340, 60 + len(rows) * 34, b)


def fish():
    b = '<path d="M60 90 Q110 40 180 90 Q110 140 60 90 Z"/><path d="M60 90 L25 60 L25 120 Z"/><path d="M110 55 Q125 35 140 60"/>'
    b += '<circle cx="155" cy="82" r="4" fill="currentColor"/><path d="M185 70 Q175 90 185 110" stroke-dasharray="3 3"/>' + F.txt(110, 165, "a fish")
    return F.svg(220, 175, b)


def winged_seed():
    b = '<ellipse cx="100" cy="150" rx="12" ry="18"/><path d="M100 132 Q150 90 160 60 Q120 62 100 132"/>' + F.txt(110, 205, "a seed with a thin wing")
    return F.svg(220, 215, b)


def hooked_seed():
    b = '<circle cx="110" cy="100" r="22"/>'
    import math
    for a in range(0, 360, 30):
        x1, y1 = 110 + 22 * math.cos(math.radians(a)), 100 + 22 * math.sin(math.radians(a))
        x2, y2 = 110 + 38 * math.cos(math.radians(a)), 100 + 38 * math.sin(math.radians(a))
        b += f'<path d="M{x1:.0f} {y1:.0f} L{x2:.0f} {y2:.0f} q4 -6 8 -2"/>'
    b += F.txt(110, 170, "a seed with tiny hooks")
    return F.svg(220, 185, b)


def coconut():
    b = '<path d="M20 150 Q50 135 80 150 T140 150 T200 150"/><ellipse cx="110" cy="120" rx="34" ry="28"/><path d="M80 125 Q110 150 140 125" />'
    b += F.txt(110, 190, "a coconut")
    return F.svg(220, 205, b)


WP = lambda: F.img("pp-whole-plant", "A potted plant in line art.")
WPL = lambda: fig_of("pp-014")  # whole plant, letters A flower, B leaf, C stem, D roots
CACTUS = lambda: F.img("pp-cactus", "A cactus growing in the desert.")
MANGROVE = lambda: F.img("pp-mangrove", "A mangrove tree in muddy water, with curved roots arching from the trunk and some roots growing up out of the mud.")
LILY = lambda: F.img("pp-water-lily", "A water lily in a pond, with a wide leaf floating on the surface.")
SEED = lambda: F.img("pp-bean-seed", "A bean seed cut open, showing its outer covering and the parts inside.")
FLOWER = lambda: F.img("pp-flower-cut", "A flower cut in half, showing its petals and the parts inside.")
PLANT = lambda: F.plant()

PARTS, ADAPT, REPRO = "sci-pat-plant-parts-function", "sci-pat-adaptations", "sci-pat-plant-reproduction"
SP_PARTS, SP_ADAPT, SP_REPRO = "sci-systems-plant-parts-fn", "sci-interactions-env-adapt", "sci-cycles-repro-plants"

# (key, level, outcome no., pattern, stem, correct, [(wrong option, tag, why) x3], solution lines, figure maker or None)
P = [
    ("pp-101", "basic", 1, PARTS, "A gardener ties a tall plant to a stick so that it does not fall over. Which part of the plant is held up by the stick?",
     "The stem", [("The roots", "wrong-part", "The roots are under the soil. The stick holds up the part above the soil."), ("The flower only", "too-narrow", "The stick holds up the whole plant, not just the flower."), ("The seeds", "wrong-part", "Seeds form inside the fruit. They are not what holds a plant up.")],
     ["The stem holds up the leaves and flowers, so the stick helps the stem."], WP),
    ("pp-102", "basic", 1, PARTS, "Hui plants a bean seed in wet soil. Which part of the young plant first grows down into the soil?",
     "The root", [("The first leaves", "wrong-part", "The first leaves grow upwards into the light, not down into the soil."), ("The flower", "wrong-part", "The flower grows much later, on an adult plant."), ("The fruit", "wrong-part", "The fruit forms after the flower. It is not the first part to grow.")],
     ["A young plant grows its root down first to take in water and hold itself in the soil."], SEED),
    ("pp-103", "basic", 1, PARTS, "Which part of a plant is usually found under the soil?",
     "The roots", [("The leaves", "wrong-part", "Leaves grow above the soil where they can get light."), ("The flowers", "wrong-part", "Flowers grow above the soil, where insects can reach them."), ("The fruits", "wrong-part", "Fruits grow above the soil on the plant.")],
     ["Roots grow down in the soil. The leaves, flowers and fruits are above it."], None),
    ("pp-104", "basic", 1, PARTS, "Which part of a plant joins the roots to the leaves?",
     "The stem", [("The flower", "wrong-part", "The flower is at the top of the plant and does not join the roots to the leaves."), ("The fruit", "wrong-part", "A fruit holds seeds. It is not a link between roots and leaves."), ("The seed", "wrong-part", "A seed grows into a new plant. It does not join parts of the plant.")],
     ["The stem is the part between the roots and the leaves."], WP),
    ("pp-105", "basic", 1, PARTS, "Which part of a healthy plant is usually green?",
     "The leaves", [("The roots", "wrong-part", "Roots are under the soil, away from light, and are usually pale or brown."), ("The petals", "wrong-part", "Petals are usually brightly coloured to attract insects, not green."), ("The seeds", "wrong-part", "Seeds are usually brown or another colour inside a fruit, not green like leaves.")],
     ["Leaves are green because they hold the green substance that helps them make food."], WP),

    ("pp-111", "intermediate", 2, PARTS, "Look at the picture of the potted plant. Mei Ling picks off part A every day. What will the plant be unable to make?",
     "Seeds", [("Food", "wrong-part", "Food is made in the leaves (part B), which are still there."), ("Roots", "wrong-part", "Roots grow from the plant under the soil. They do not come from the flower."), ("Water", "wrong-part", "A plant does not make water. It takes water in through its roots.")],
     ["Part A is the flower. Flowers make the seeds.", "With no flowers there will be no seeds."], WPL),
    ("pp-112", "intermediate", 2, PARTS, "Look at the picture of the potted plant. Water must travel from the soil to the leaves. Which shows the parts it passes through, in order?",
     "D, C, B", [("B, C, D", "reversed-order", "This is the wrong way round. Water moves up, from the roots to the leaves."), ("D, B, C", "stem-skipped", "The water cannot jump from the roots to the leaves. It goes up the stem first."), ("C, D, B", "wrong-start", "Water enters at the roots (D), not at the stem.")],
     ["Part D is the roots, part C is the stem and part B is a leaf.", "Water goes in at the roots, up the stem and into the leaves."], WPL),
    ("pp-113", "intermediate", 2, PARTS, "Look at the picture of the potted plant. Part D is torn off when the plant is pulled out of the soil. After some days the leaves droop. Why?",
     "The plant cannot take in enough water", [("The plant cannot make seeds", "wrong-reason", "Seeds do not affect the leaves drooping. The leaves droop because of too little water."), ("The stem cannot hold up the plant", "wrong-reason", "The stem is still there. Drooping comes from a lack of water."), ("The leaves cannot get any sunlight", "wrong-reason", "The leaves are still in the light. The problem is below the soil.")],
     ["Part D is the roots, which take in water.", "Without roots the plant cannot take in enough water, so the leaves droop."], WPL),
    ("pp-114", "intermediate", 1, PARTS, "Which of these is NOT a job of the roots of a plant?",
     "Making food for the plant", [("Holding the plant in the soil", "is-a-job", "This is a job of the roots, so it is not the answer."), ("Taking in water from the soil", "is-a-job", "This is a job of the roots, so it is not the answer."), ("Taking in mineral salts from the soil", "is-a-job", "This is a job of the roots, so it is not the answer.")],
     ["Roots hold the plant and take in water and mineral salts.", "Food is made in the leaves, not in the roots."], WP),
    ("pp-115", "intermediate", 1, PARTS, "Aisha cuts the stem of a potted plant just above the soil and leaves the top part in the pot. After a few days the leaves dry up. Why?",
     "Water from the roots cannot reach the leaves", [("The leaves cannot make seeds any more", "wrong-reason", "Leaves do not make seeds. They dry up because they get no water."), ("The roots cannot hold the plant firmly", "wrong-reason", "The roots are still in the soil. The cut stem breaks the path for water."), ("The leaves take in too much sunlight", "wrong-reason", "Light was the same as before. The change is the cut stem.")],
     ["The stem carries water from the roots up to the leaves.", "When the stem is cut, no water can reach the leaves, so they dry up."], WP),
    ("pp-122", "intermediate", 2, PARTS, "A bean seed has just started to grow. The first part to come out grows down into the soil before any leaves open. How does this part help the young plant?",
     "It holds the plant and takes in water", [("It makes food for the plant", "wrong-job", "Food is made in the leaves, and there are no leaves yet."), ("It takes in light for the leaves", "wrong-job", "This part is in the soil. It does not take in light."), ("It carries food to the flower", "wrong-job", "A young bean plant has no flower yet, and this part does not do this job.")],
     ["The first part to grow down is the root.", "It takes in water and holds the young plant firmly in the soil."], lambda: F.img("pp-bean-seedling", "A young bean seedling in line art.")),
    ("pp-117", "intermediate", 1, PARTS, "Sugar cane juice comes from the tall, thick stalks of the sugar cane plant. Which part of the plant is the stalk?",
     "The stem", [("The root", "wrong-part", "Roots grow under the soil. The tall stalk is above it."), ("The leaf", "wrong-part", "Leaves are the thin green blades. The thick stalk is not a leaf."), ("The fruit", "wrong-part", "A fruit holds seeds. The stalk is the part that holds the plant up.")],
     ["The tall, thick part that holds up the leaves is the stem."], None),
    ("pp-118", "intermediate", 1, PARTS, "We eat the green heads of broccoli. These heads are bunches of flower buds. Which part of the broccoli plant do we eat?",
     "The flowers", [("The roots", "wrong-part", "The heads are above the ground. Roots are under the soil."), ("The leaves", "wrong-part", "The heads are buds that would open into flowers. They are not leaves."), ("The seeds", "wrong-part", "The buds have not made seeds yet.")],
     ["The heads are flower buds, so we eat the flowers of the plant."], None),
    ("pp-119", "intermediate", 1, PARTS, "A sheet of plastic covers the soil of a potted plant. Water is poured only onto the plastic. After a few days the leaves droop. What is the reason?",
     "Water cannot reach the roots in the soil", [("The leaves cannot make food without plastic", "wrong-reason", "Plastic has nothing to do with making food. The soil is blocked so the roots cannot get water."), ("The stem has too much water", "wrong-reason", "The stem is getting less water, not more."), ("The flowers are using all the water", "wrong-reason", "Flowers do not use up the water. The roots simply cannot reach any.")],
     ["Plants take in water through the roots in the soil.", "The plastic stops the water reaching the soil, so the leaves droop."], PLANT),
    ("pp-120", "intermediate", 1, PARTS, "Which two parts of a plant take in things from outside the plant?",
     "The roots and the leaves", [("The stem and the flowers", "wrong-parts", "The stem carries things and the flowers make seeds. Neither takes in water or air."), ("The flowers and the fruits", "wrong-parts", "These help the plant to make seeds, not to take in things for food."), ("The stem and the roots", "one-wrong", "The roots take in water but the stem does not take in anything from outside.")],
     ["The roots take in water and mineral salts from the soil.", "The leaves take in air (carbon dioxide) to make food."], WP),

    ("pp-131", "competent", 2, PARTS, "Look at the picture of the potted plant. Which row matches each part with its job?",
     "A: makes seeds; B: makes food; C: carries water; D: takes in water", [
         ("A: makes food; B: makes seeds; C: carries water; D: takes in water", "swapped-jobs", "Part A is the flower, which makes seeds. Part B is the leaf, which makes food."),
         ("A: makes seeds; B: takes in water; C: makes food; D: carries water", "jobs-mixed", "Leaves do not take in water from the soil. Roots do that and stems carry it."),
         ("A: takes in water; B: carries water; C: makes seeds; D: makes food", "jobs-mixed", "Each job here is given to the wrong part.")],
     ["A is the flower, B a leaf, C the stem and D the roots.", "Flower: seeds. Leaf: food. Stem: carries water. Roots: take in water."], WPL),
    ("pp-132", "competent", 1, PARTS, "A gardener sprays water on the leaves of a potted plant every day but never waters the soil. After two weeks the plant is weak. Which is the best reason?",
     "The roots take in most of a plant's water", [
         ("Leaves make food only when they are dry", "false-claim", "Leaves make food using light and air. They do not need to be dry to do it."),
         ("The stem cannot carry water from the leaves", "wrong-direction", "The stem carries water up from the roots. It does not need to carry water down from the leaves."),
         ("Water on the leaves stops light from reaching them", "false-claim", "A little water on the leaves does not stop them from making food.")],
     ["Plants take in most water through their roots.", "With dry soil the roots cannot take in enough water, so the plant becomes weak."], WP),
    ("pp-133", "competent", 2, PARTS, "The table shows the parts that four plants have. Which plant has what it needs to take in water, hold up its leaves and make food?",
     "P", [("Q", "missing-part", "Plant Q has no leaves, so it cannot make food."), ("R", "missing-part", "Plant R has no roots, so it cannot take in water from the soil."), ("S", "missing-part", "Plant S has no stem, so it cannot hold up its leaves or carry water up to them.")],
     ["Taking in water needs roots, holding up leaves needs a stem and making food needs leaves.", "Only plant P has all three."],
     lambda: table_svg([("P", "Yes", "Yes", "Yes"), ("Q", "Yes", "Yes", "No"), ("R", "No", "Yes", "Yes"), ("S", "Yes", "No", "Yes")])),
    ("pp-135", "competent", 2, PARTS, "The table shows the parts that four plants have. Which plant has roots and leaves but no part to carry water between them?",
     "S", [("P", "has-all", "Plant P has a stem, so water can travel from its roots to its leaves."), ("Q", "no-leaves", "Plant Q has roots and a stem but no leaves, so it has no leaves for the water to reach."), ("R", "no-roots", "Plant R has a stem and leaves but no roots, so it has no roots to take water in.")],
     ["Water travels up the stem from the roots to the leaves.", "Only plant S has both roots and leaves but no stem."],
     lambda: table_svg([("P", "Yes", "Yes", "Yes"), ("Q", "Yes", "Yes", "No"), ("R", "No", "Yes", "Yes"), ("S", "Yes", "No", "Yes")])),
]

A = [
    ("ad-001", "basic", 1, ADAPT, "A cactus grows in a hot, dry desert. Which part of the cactus stores water?",
     "The thick stem", [("The sharp spines", "wrong-part", "Spines are thin and cannot hold water."), ("The tiny roots only", "wrong-part", "Roots take water in. The water is stored in the thick stem."), ("The flowers", "wrong-part", "Flowers help the plant to make seeds, not store water.")],
     ["The thick stem of a cactus stores water for the dry times."], CACTUS),
    ("ad-002", "basic", 1, ADAPT, "The leaves of a cactus are thin, sharp spines. How does this help the cactus live in a desert?",
     "Less water is lost from the plant", [("More light is caught for making food", "wrong-effect", "Wide leaves, not spines, catch more light."), ("It takes in more water from the air", "wrong-effect", "Spines do not take in water."), ("It makes the stem grow taller", "wrong-effect", "Spines have nothing to do with height.")],
     ["Small spines have very little surface, so very little water vapour escapes."], CACTUS),
    ("ad-003", "basic", 1, ADAPT, "Some roots of a mangrove tree grow upwards out of the muddy water. Why does the tree have these roots?",
     "To take in air", [("To take in more mud", "wrong-reason", "The tree does not need to take in mud."), ("To catch sunlight", "wrong-reason", "Roots do not catch light. Leaves do."), ("To make seeds", "wrong-reason", "Seeds are not made in roots.")],
     ["Mud has very little air. Roots growing up into the air can take it in."], MANGROVE),
    ("ad-004", "basic", 1, ADAPT, "A water lily has wide leaves that float on the water. How does this help the plant?",
     "The leaves can catch lots of sunlight", [("The leaves can take in water from the soil", "wrong-job", "Leaves are not the part that takes in water from the soil."), ("The leaves can store air for the roots", "wrong-job", "Storing air is not the job of wide leaves."), ("The leaves can hold the plant in the mud", "wrong-job", "Roots hold a plant in the mud, not floating leaves.")],
     ["Floating leaves lie in the light, so they can make food."], LILY),
    ("ad-005", "basic", 1, ADAPT, "A fish has a smooth body that is narrow at the front and the back. How does this help the fish?",
     "It can move through water easily", [("It can breathe air easily", "wrong-effect", "A fish breathes with its gills. Its shape does not help it breathe air."), ("It can stay on land for a long time", "wrong-effect", "A fish cannot live on land."), ("It can hide among rocks on land", "wrong-effect", "A fish lives in water, so this does not help.")],
     ["A smooth, narrow body makes less push from the water, so the fish swims fast."], fish),
    ("ad-006", "basic", 1, ADAPT, "A camel has a hump that stores fat. How does this help the camel in the desert?",
     "It is a store of food for hard times", [("It stops the camel from sweating", "wrong-effect", "The fat does not stop sweating."), ("It helps the camel to float", "wrong-effect", "A camel does not live in water."), ("It keeps the camel cool in the shade", "wrong-effect", "The hump is a food store, not a cooler.")],
     ["Fat in the hump can be used as food when there is little to eat."], None),
    ("ad-007", "basic", 1, ADAPT, "A polar bear has thick fur and a thick layer of fat under its skin. How does this help it?",
     "It keeps the bear warm in the cold", [("It helps the bear to run fast", "wrong-effect", "Fur and fat do not make it faster."), ("It helps the bear to hide in the desert", "wrong-effect", "Polar bears live in cold places, not deserts."), ("It lets the bear store water", "wrong-effect", "Fat and fur keep in heat. They are not for storing water.")],
     ["Thick fur and fat keep heat in, so the bear stays warm."], None),
    ("ad-008", "basic", 1, ADAPT, "A tortoise pulls its head and legs into its hard shell when it is in danger. How does the shell help it?",
     "It protects the tortoise from enemies", [("It helps the tortoise to find food", "wrong-effect", "A shell does not help find food."), ("It helps the tortoise to swim fast", "wrong-effect", "A heavy shell does not make it swim fast."), ("It keeps the tortoise cool in the sun", "wrong-effect", "The shell is for protection.")],
     ["A hard shell is hard for enemies to bite or crush, so the tortoise is safer."], None),
    ("ad-009", "basic", 1, ADAPT, "A duck has webbed feet. How do they help the duck?",
     "They push the water to help it swim", [("They help the duck to climb trees", "wrong-effect", "Webbed feet are not good for climbing."), ("They keep the duck warm in the nest", "wrong-effect", "Webbing on the feet is for swimming."), ("They help the duck to dig for worms", "wrong-effect", "Webbed feet are for swimming, not digging.")],
     ["The skin between the toes makes the foot wide, so it pushes more water."], None),
    ("ad-010", "basic", 1, ADAPT, "Many birds fly to a warmer place when the cold season begins. What kind of adaptation is this?",
     "A behavioural adaptation", [("A structural adaptation", "wrong-type", "A structural adaptation is a body part. Flying away is an action the bird does."), ("A seed dispersal adaptation", "wrong-type", "Seed dispersal is about plants. Birds are moving themselves."), ("A food-making adaptation", "wrong-type", "The birds do not make food. They move to find food and warmth.")],
     ["Moving to another place is something the animal does, so it is behavioural."], None),
    ("ad-011", "basic", 1, ADAPT, "Which of these is a structural adaptation?",
     "A porcupine's sharp quills", [("A bird flying to a warmer place", "behavioural", "This is something the bird does, so it is behavioural."), ("A bear sleeping through the cold season", "behavioural", "This is behaviour, not a body part."), ("A squirrel storing nuts", "behavioural", "This is behaviour, not a body part.")],
     ["A structural adaptation is a part of the body, such as quills.", "The other three are things animals do."], None),
    ("ad-012", "basic", 1, ADAPT, "A seed has a thin, light wing. How does the wing help the plant?",
     "The wind can carry the seed far away", [("It helps the seed to take in water", "wrong-effect", "The wing is not for taking in water."), ("It helps the seed to float on a pond", "wrong-effect", "The thin wing is for the wind, not water."), ("It sticks the seed to an animal's fur", "wrong-effect", "Sticking to fur needs hooks or sticky parts, not a wing.")],
     ["A light wing catches the wind, so seeds travel away from the parent plant."], winged_seed),
    ("ad-013", "basic", 1, ADAPT, "A coconut has a thick husk that holds air. How does this help the coconut plant?",
     "It can float to faraway places", [("It keeps the coconut warm", "wrong-effect", "The husk is for floating."), ("It lets the wind carry the coconut", "wrong-effect", "A coconut is too heavy to be carried by wind."), ("It makes animals eat the coconut", "wrong-effect", "The husk is not a food for animals.")],
     ["The husk holds air and floats, so water carries the coconut away from the tree."], coconut),
    ("ad-014", "basic", 1, ADAPT, "A seed has many tiny hooks on its outside. How does this help the plant?",
     "It can cling to an animal", [("It can float on water", "wrong-effect", "Hooks do not help a seed float."), ("It can be blown by the wind", "wrong-effect", "Hooks do not help a seed travel by wind."), ("It can make food for the plant", "wrong-effect", "Hooks do not make food.")],
     ["Hooks catch on fur or clothes, so the seed is carried to a new place."], hooked_seed),
    ("ad-027", "basic", 1, ADAPT, "An owl has very large eyes that can see well in dim light. How does this help it?",
     "It can hunt at night", [("It can hide in the sand", "wrong-effect", "Large eyes do not help an owl hide in sand."), ("It can swim very fast", "wrong-effect", "Eyes do not help an owl swim."), ("It can store water for a long time", "wrong-effect", "Eyes do not store water.")],
     ["Large eyes let an owl see in the dark, so it can look for food at night."], None),
    ("ad-028", "basic", 1, ADAPT, "A frog has green and brown skin that looks like the plants around it. How does this help the frog?",
     "Enemies find it hard to see the frog", [("It keeps the frog warm at night", "wrong-effect", "Skin colour does not keep a frog warm."), ("It helps the frog swim faster", "wrong-effect", "Skin colour does not make a frog swim faster."), ("It stores food for the frog", "wrong-effect", "Skin colour is not a food store.")],
     ["Skin that matches the plants helps the frog hide from its enemies."], None),
    ("ad-029", "basic", 1, ADAPT, "A mole has strong front legs with large claws. How do they help the mole?",
     "It can dig tunnels in the soil", [("It can swim across ponds", "wrong-effect", "Strong claws are not for swimming."), ("It can climb tall trees", "wrong-effect", "A mole lives under the ground, not in trees."), ("It can fly short distances", "wrong-effect", "A mole cannot fly.")],
     ["Strong legs and large claws are good for digging, so a mole can make tunnels."], None),
    ("ad-030", "basic", 1, ADAPT, "A giraffe has a very long neck. How does this help it?",
     "It can reach leaves high up on trees", [("It can swim in deep water", "wrong-effect", "A long neck does not help a giraffe swim."), ("It can dig for roots in the ground", "wrong-effect", "A long neck is not for digging."), ("It can hide in the long grass", "wrong-effect", "A tall animal cannot hide easily in grass.")],
     ["A long neck lets a giraffe reach food that other animals cannot reach."], None),
    ("ad-021", "basic", 2, ADAPT, "A forest is cut down to build a road. What happens to many of the animals that lived there?",
     "They lose their homes", [("They grow thicker fur", "wrong-effect", "Animals cannot change their bodies that quickly."), ("They find more food and shelter", "wrong-effect", "Fewer trees means less food and shelter."), ("They are not affected", "wrong-effect", "Their habitat is gone, so they are affected.")],
     ["Trees give food and shelter. When they are cut down, animals lose their homes."], None),
    ("ad-022", "basic", 2, ADAPT, "Which of these actions is good for the environment?",
     "Planting new trees in a cleared area", [("Burning rubbish in an open field", "harms-air", "Burning rubbish puts smoke and harmful gases in the air."), ("Pouring used cooking oil down the drain", "harms-water", "Oil pollutes the water and harms animals and plants."), ("Throwing plastic bags into the sea", "harms-sea", "Plastic harms sea animals and does not break down quickly.")],
     ["New trees give food and shelter and help to replace what was lost."], None),
    ("ad-023", "basic", 2, ADAPT, "Why is it harmful to pour oil into the sea?",
     "It harms sea animals and plants", [("It makes the sea cooler", "wrong-effect", "Oil does not make the sea cooler."), ("It gives sea animals more food", "wrong-effect", "Oil is not food. It covers and poisons animals."), ("It makes the water cleaner", "wrong-effect", "Oil makes water dirty, not clean.")],
     ["Oil covers the water. It poisons the animals and plants that live in it."], None),
    ("ad-024", "basic", 2, ADAPT, "Recycling paper helps the environment because fewer ____ need to be cut down.",
     "trees", [("rocks", "wrong-word", "Paper is made from trees, not rocks."), ("fish", "wrong-word", "Paper is not made from fish."), ("clouds", "wrong-word", "Paper is not made from clouds.")],
     ["Paper is made from wood.", "Recycling used paper means fewer trees are cut down."], None),
    ("ad-025", "basic", 2, ADAPT, "Burning large amounts of fuel puts gases in the air that make the Earth warmer. This is called ____.",
     "global warming", [("deforestation", "wrong-term", "Deforestation is the cutting down of forests."), ("recycling", "wrong-term", "Recycling means using materials again."), ("reforestation", "wrong-term", "Reforestation means planting trees again.")],
     ["The Earth getting warmer because of gases from burning fuel is called global warming."], None),
    ("ad-026", "basic", 2, ADAPT, "A student brings her own bag when she goes shopping instead of taking new plastic bags. How does this help the environment?",
     "Less plastic rubbish is made", [("More trees are cut down", "wrong-effect", "A cloth bag does not need more trees to be cut."), ("More oil is poured into the sea", "wrong-effect", "This has nothing to do with using her own bag."), ("More forest is cleared for roads", "wrong-effect", "Her own bag does not clear forests.")],
     ["Using a bag again means fewer new plastic bags are made and thrown away."], None),
]

R = [
    ("rp-001", "basic", 2, REPRO, "What is the movement of pollen from one flower to another called?",
     "Pollination", [("Germination", "wrong-term", "Germination is when a seed starts to grow into a young plant."), ("Seed dispersal", "wrong-term", "Seed dispersal is the spreading of seeds away from the parent plant."), ("Fertilisation", "wrong-term", "Fertilisation is when a male and a female cell join. It happens after pollination.")],
     ["Moving pollen from one flower to another is called pollination."], FLOWER),
    ("rp-002", "basic", 2, REPRO, "Which of these animals often carry pollen from flower to flower?",
     "Bees and butterflies", [("Worms and snails", "wrong-animals", "Worms and snails stay low on the ground and do not visit flowers to feed."), ("Fish and frogs", "wrong-animals", "Fish and frogs live in or near water, not among flowers."), ("Ants and earthworms", "wrong-animals", "These stay mostly on the ground or in the soil.")],
     ["Bees and butterflies visit flowers for the sweet nectar, so pollen sticks to them and is carried on."], FLOWER),
    ("rp-003", "basic", 2, REPRO, "Which of these things must a bean seed have to start growing?",
     "Water, air and warmth", [("Sunlight, soil and wind", "wrong-needs", "A seed does not need light, soil or wind to start growing."), ("Soil, light and carbon dioxide", "wrong-needs", "These are not needed for a seed to germinate."), ("Light, mineral salts and wind", "wrong-needs", "A seed needs none of these to begin to grow.")],
     ["A seed needs water, air and warmth to germinate."], SEED),
    ("rp-004", "basic", 2, REPRO, "What do we call it when a seed starts to grow into a young plant?",
     "Germination", [("Pollination", "wrong-term", "Pollination is the movement of pollen between flowers."), ("Fertilisation", "wrong-term", "Fertilisation is the joining of a male and a female cell inside the flower."), ("Seed dispersal", "wrong-term", "Seed dispersal is the spreading of seeds.")],
     ["A seed starting to grow is germination."], SEED),
    ("rp-005", "basic", 2, REPRO, "In the picture of the bean seed cut open, part C is the tiny young plant inside. What will part C grow into?",
     "A new plant", [("The covering of the seed", "wrong-part", "The covering is part A and does not grow into the new plant."), ("The fruit that holds the seeds", "wrong-part", "A fruit forms from the flower, not from the young plant inside the seed."), ("The food store of the seed", "wrong-part", "The food store is a different part (part B).")],
     ["Part C is the young plant, or baby plant, inside the seed.", "It grows into a new plant."], lambda: fig_of("pp-028")),
    ("rp-006", "basic", 2, REPRO, "What do we call the carrying of seeds away from the parent plant?",
     "Seed dispersal", [("Germination", "wrong-term", "Germination is when a seed starts to grow."), ("Pollination", "wrong-term", "Pollination is the movement of pollen."), ("Fertilisation", "wrong-term", "Fertilisation is the joining of a male and a female cell.")],
     ["Carrying seeds away from the parent plant is called seed dispersal."], None),
    ("rp-007", "basic", 3, REPRO, "Why is it good for a plant to have its seeds carried far away from it?",
     "The young plants have more room and light", [("The seeds can make food for the parent plant", "wrong-reason", "Seeds do not make food for the parent plant."), ("The parent plant can make more flowers", "wrong-reason", "Where seeds land does not change how many flowers the parent makes."), ("The seeds can grow into fruits right away", "wrong-reason", "Seeds do not become fruits. They grow into new plants.")],
     ["Seeds that fall next to the parent must share its light, water and space.", "Seeds carried far away have more room to grow."], None),
    ("rp-008", "basic", 3, REPRO, "Which of these seeds is carried away by the wind?",
     "A dandelion seed", [("A coconut", "water-seed", "A coconut is spread by water, not wind."), ("A burr seed", "animal-seed", "A burr has hooks, so it is carried on animals' fur."), ("A mango seed", "animal-seed", "A mango is a juicy fruit. Animals eat it and spread the seed.")],
     ["A dandelion seed has light hairs that catch the wind and carry it away."], None),
    ("rp-009", "basic", 3, REPRO, "Which of these seeds is carried away by water?",
     "A coconut", [("A seed with a light wing", "wind-seed", "A winged seed is carried by wind."), ("A seed with tiny hooks", "animal-seed", "A hooked seed is carried on animals' fur."), ("A seed in a bright red berry", "animal-seed", "A bright berry is eaten by animals, which spread the seed.")],
     ["A coconut has a thick husk that floats, so water can carry it away."], None),
    ("rp-010", "basic", 3, REPRO, "Birds eat red berries and later drop the seeds in their droppings far away. How are the seeds spread?",
     "By animals", [("By wind", "wrong-way", "The seeds are carried inside the bird, not blown by wind."), ("By water", "wrong-way", "Water does not carry the seeds in this case."), ("By the fruit splitting open", "wrong-way", "The fruit is eaten. It does not split open to throw the seeds out.")],
     ["Animals eat the fruit and drop the seeds somewhere else, so the seeds are spread by animals."], None),
    ("rp-011", "basic", 3, REPRO, "The ripe fruits of a rubber tree dry in the sun and burst with a snap. The seeds land far from the tree. How are the seeds spread?",
     "By the fruit itself", [("By wind", "wrong-way", "Wind does not throw the seeds. The fruit bursts by itself."), ("By animals", "wrong-way", "No animal is needed. The fruit bursts open by itself."), ("By water", "wrong-way", "The fruits dry in the sun. Water is not involved.")],
     ["Some fruits dry and burst open, which throws the seeds away from the plant."], None),
    ("rp-012", "basic", 1, REPRO, "Which of these plants makes spores instead of seeds?",
     "A fern", [("A hibiscus plant", "makes-seeds", "A hibiscus makes flowers and seeds."), ("A mango tree", "makes-seeds", "A mango tree makes flowers, fruits and seeds."), ("A bean plant", "makes-seeds", "A bean plant makes flowers, pods and seeds.")],
     ["Ferns do not make flowers or seeds.", "They make tiny spores."], None),
    ("rp-013", "basic", 1, REPRO, "A gardener pushes a cut branch of a rose bush into wet soil. Weeks later it has roots and leaves and is a new rose plant. What did the new plant grow from?",
     "A part of the old plant", [("A seed hidden inside the branch", "wrong-source", "No seed was planted. The branch itself grew roots and leaves."), ("A fruit of the old plant", "wrong-source", "A fruit was not planted, only the cut branch."), ("Pollen from another rose", "wrong-source", "Pollen does not grow into a plant by itself.")],
     ["A new plant can grow from a cut piece of stem.", "No seed was planted."], None),
    ("rp-015", "basic", 2, REPRO, "After a flower has been pollinated and fertilised, which part of it grows into the fruit?",
     "The ovary", [("The petals", "wrong-part", "The petals usually wither and fall off."), ("The stamen", "wrong-part", "The stamen makes pollen. It does not become the fruit."), ("The flower stalk", "wrong-part", "The stalk holds up the flower and does not become the fruit.")],
     ["The ovary holds the tiny egg cells.", "After fertilisation, it grows into the fruit and the egg cells become seeds."], None),
    ("rp-016", "basic", 2, REPRO, "A bean seed is planted in soil. Where does the young plant get its food before its leaves can make food?",
     "From the food stored in the seed", [("From the soil only", "wrong-source", "Soil gives water and mineral salts, but not food."), ("From the air only", "wrong-source", "Air alone cannot feed a young plant that has no leaves yet."), ("From the sunlight only", "wrong-source", "Sunlight is only used by leaves to make food, and there are no leaves yet.")],
     ["A bean seed has a food store inside it.", "The young plant uses this until its leaves can make food."], SEED),
    ("rp-017", "basic", 2, REPRO, "Which of these must happen first before a flower can make seeds?",
     "Pollen reaches its female part", [("The seeds are spread by wind", "later-step", "Seeds are spread only after they have been made."), ("A seed starts to grow", "later-step", "Growing from a seed happens after the seed has been made."), ("An animal eats the fruit", "later-step", "The fruit forms only after pollination, so this comes later.")],
     ["Seeds can form only after pollen reaches the female part of a flower.", "Spreading and growing of seeds come later."], FLOWER),
    ("rp-018", "basic", 2, REPRO, "A bean seed is put on dry cotton wool in a warm room. After a week it has not started to grow. What is missing?",
     "Water", [("Soil", "not-needed", "A seed can start to grow without soil, for example on wet cotton wool."), ("Sunlight", "not-needed", "A seed does not need light to start to grow."), ("Wind", "not-needed", "Wind is not needed for a seed to start to grow.")],
     ["A seed needs water, air and warmth to germinate.", "The room is warm and has air. The cotton wool is dry, so water is missing."], SEED),
    ("rp-014", "basic", 2, REPRO, "Pollen is made in the male part of a flower called the ____.",
     "stamen", [("petal", "wrong-part", "Petals attract insects. They do not make pollen."), ("ovary", "wrong-part", "The ovary is the female part. It holds the tiny egg cells that become seeds."), ("stalk", "wrong-part", "The stalk holds up the flower. It does not make pollen.")],
     ["The stamen is the male part of the flower and makes pollen."], FLOWER),
]


def remove(fname, key):
    """Delete the item with this key from an item file (use when an item is reworded under a new key)."""
    f = ITEMS / fname
    d = json.loads(f.read_text())
    d["items"] = [it for it in d["items"] if it["key"] != key]
    f.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n")


def add(subtopic, fname, rows):
    """Append each row whose key is NOT already in the target file; keys that exist are skipped and printed.
    A reworded item must get a NEW key (and the old one removed with remove()), never overwrite the old key.
    Creates the target file if missing."""
    f = ITEMS / fname
    d = json.loads(f.read_text()) if f.exists() else {"subtopic": subtopic, "items": []}
    have = {it["key"] for it in d["items"]}
    n = 0
    for key, lvl, on, pat, stem, ok, wrongs, sol, fm in rows:
        if key in have:
            print("skipped (key exists):", key)
            continue
        pos = (int(key.split("-")[1]) * 3 + 1) % 4
        opts = [w[0] for w in wrongs]
        expl = [{"tag": w[1], "why": w[2]} for w in wrongs]
        opts.insert(pos, ok)
        expl.insert(pos, None)
        it = {"key": key, "level": lvl, "outcome": f"{subtopic}-{on}", "pattern": pat, "stem": stem, "options": opts, "answer": pos,
              "explain": expl, "solution": sol}
        if fm:
            it["figure"] = fm()
        d["items"].append(it)
        n += 1
    f.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n")
    return n


if __name__ == "__main__":
    remove("sci-plant-parts.json", "pp-121")  # reworded as pp-122
    n = [add(SP_PARTS, "sci-plant-parts.json", P), add(SP_ADAPT, "sci-adaptations.json", A), add(SP_REPRO, "sci-plant-repro.json", R)]
    print("added", n)
