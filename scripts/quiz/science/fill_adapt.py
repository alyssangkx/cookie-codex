"""PSLE-style Intermediate and Competent items for sci-interactions-env-adapt (round sci-fill-adapt-2026-11-20)."""
from fillkit import add, table, graph, lint

SUB, FILE = "sci-interactions-env-adapt", "sci-adaptations.json"
AD, HI, RD, FT = "sci-pat-adaptations", "sci-pat-human-impact", "sci-pat-read-data", "sci-pat-fair-test-design"
I, C = "intermediate", "competent"
P = []
def q(*a): P.append(a)
def W(t, tag, why): return (t, tag, why)
def tb(h, r, w, c): return lambda: table(h, r, w, c)

# ---------------- intermediate ----------------
q("ae-101", I, 1, AD, "The table shows four animals and a body feature of each. Which animal is best suited to live in a very cold place?", "Q",
  [W("P", "wrong-habitat", "P has a thin, bare skin that loses body heat quickly, so it suits a warm place."), W("R", "wrong-habitat", "R has large, thin ears used to lose heat, which suits a hot place."), W("S", "wrong-habitat", "S has a thin coat of short hairs, which would not keep it warm in the cold.")],
  ["A thick layer of fat and thick fur keep heat in.", "So Q can live in a very cold place."],
  tb(["Animal", "Body feature"], [["P", "thin bare skin"], ["Q", "thick fur and a layer of fat"], ["R", "very large thin ears"], ["S", "short thin coat of hairs"]], [70, 220], "Four animals"))
q("ae-102", I, 1, AD, "The table shows the leaves of four plants. Which plant is most likely to survive in a hot, dry place?", "T",
  [W("S", "wrong-habitat", "S has big, thin leaves that lose a lot of water to the air."), W("U", "wrong-habitat", "U has thin leaves with many openings, which lose water quickly in the heat."), W("V", "wrong-habitat", "V grows its leaves under water, so it does not live in a dry place.")],
  ["Small leaves with a thick waxy coat lose very little water.", "Plant T is the one that can survive in a dry place."],
  tb(["Plant", "Leaves"], [["S", "big and thin"], ["T", "small with a thick waxy coat"], ["U", "thin with many openings"], ["V", "grow under water"]], [70, 220], "Leaves of four plants"))
q("ae-103", I, 1, AD, "The table shows the feet of four animals. Which animal spends most of its time swimming in water?", "S",
  [W("P", "wrong-feature", "P has long toes that grip branches, so it lives in trees."), W("Q", "wrong-feature", "Q has hard hooves for running on hard ground."), W("R", "wrong-feature", "R has sharp claws for digging or catching prey on land.")],
  ["Webbed feet push against a lot of water, so S swims well."],
  tb(["Animal", "Its feet"], [["P", "long toes that grip"], ["Q", "hard hooves"], ["R", "sharp claws"], ["S", "toes joined by skin"]], [70, 200], "Four animals"))
q("ae-104", I, 1, AD, "A stick insect looks like a twig of the plant it lives on. How does this help the stick insect?", "Predators find it hard to see it",
  [W("It can catch other insects more easily", "wrong-use", "Looking like a twig hides the insect from predators. It is not for hunting."), W("It can fly higher than other insects", "wrong-use", "Its shape does not help it fly. It helps it hide."), W("It stays warm in the cold season", "wrong-use", "A twig-like shape does not keep it warm.")],
  ["Looking like a twig is camouflage. Predators do not notice the insect, so fewer of them eat it."], None)
q("ae-105", I, 1, AD, "Which row correctly shows a structural adaptation and a behavioural adaptation?", "Webbed feet of a duck; a bird flying to a warmer place in winter",
  [W("Thick fur of a bear; webbed feet of a duck", "both-structural", "Both are body parts, so both are structural. None of them is something the animal does."), W("A bird flying to a warmer place in winter; a bear sleeping through winter", "both-behavioural", "Both are things animals do, so both are behavioural. None of them is a body part."), W("A bear sleeping through winter; thick fur of a bear", "reversed", "The order is the wrong way round. Sleeping is behavioural and thick fur is structural.")],
  ["A structural adaptation is a body part or body covering, such as webbed feet.", "A behavioural adaptation is what the animal does, such as flying to a warmer place."], None)
q("ae-106", I, 1, AD, "Many birds fly to another country when winter comes. What is the main reason this helps them to survive?", "They can find more food in the warmer place",
  [W("They can lay more eggs in the cold place", "wrong-reason", "Food is hard to find in winter. Laying eggs in the cold is not the reason."), W("They need to grow thicker feathers", "wrong-reason", "Flying away is not how they grow feathers."), W("They want to be away from the sunlight", "wrong-reason", "Birds do not need to escape sunlight in winter.")],
  ["In winter the cold place has little food.", "Birds that fly to a warmer place can find food and survive."], None)
q("ae-107", I, 1, AD, "Many desert animals hide in burrows during the day and come out only at night. How does this help them survive?", "They avoid the heat of the day and lose less water",
  [W("They can see better in the strong sunlight", "wrong-reason", "At night there is no strong sunlight."), W("They can eat the plants that only grow at night", "wrong-reason", "Plants do not grow only at night. The reason is the heat."), W("They can stay warm during the cold days", "wrong-reason", "Desert days are hot, not cold.")],
  ["Days in the desert are very hot. Staying in a burrow keeps the animal cool.", "It also loses less water from its body."], None)
q("ae-108", I, 1, AD, "A bear eats a lot in autumn and then sleeps in a cave through winter, living off the fat it stored. How does this help the bear?", "It saves energy when there is little food",
  [W("It makes the bear grow bigger in winter", "wrong-reason", "The bear uses up fat in winter and does not grow."), W("It lets the bear hunt in the dark", "wrong-reason", "The bear is asleep and does not hunt."), W("It keeps the bear safe from the heat", "wrong-reason", "Winter is the cold season, so heat is not the problem.")],
  ["Food is scarce in winter. Sleeping uses very little energy, so the stored fat lasts until spring."], None)
q("ae-109", I, 1, AD, "A rabbit has an eye on each side of its head. How does this help the rabbit?", "It can see a wide area and spot danger",
  [W("It can see small insects very clearly", "wrong-use", "Eyes on the sides give a wide view, not a close, sharp one."), W("It can judge the distance to its food exactly", "wrong-use", "Judging distance well needs both eyes at the front, like a hunter."), W("It can see in the dark", "wrong-use", "The position of the eyes does not help seeing in the dark.")],
  ["Eyes on the sides of the head let a rabbit see almost all around it.", "It can spot a predator coming from any direction."], None)
q("ae-110", I, 1, AD, "The leaves of a cactus are covered by a thick waxy layer. How does this help the plant?", "It stops water from escaping from the leaves",
  [W("It lets more sunlight reach the leaves", "wrong-use", "A thick layer cuts down water loss. It does not let in more light."), W("It helps the roots take in water", "wrong-use", "The waxy layer is on the leaves, not the roots."), W("It makes the leaves taste bad to insects", "wrong-use", "The waxy layer does not stop insects. It keeps water in.")],
  ["A thick waxy layer is waterproof. Water cannot escape from the cactus into the dry air."], None)
q("ae-111", I, 2, HI, "The graph shows the area of forest in a country over 40 years. Which statement is correct?", "The area of forest became smaller every 10 years",
  [W("The area of forest became bigger every 10 years", "reversed", "The line goes down. The area gets smaller."), W("The area of forest stayed the same", "misread", "The values are lower at each point on the graph."), W("The area of forest was smallest in 1980", "misread", "1980 had the largest area. The smallest was in 2020.")],
  ["Each point on the line is lower than the one before.", "So the forest became smaller every 10 years."],
  lambda: graph(["1980", "1990", "2000", "2010", "2020"], [("f", [90, 76, 60, 48, 40])], 100, "Year", "Forest area (thousand km²)", "Forest area in a country", ystep=20))
q("ae-112", I, 2, HI, "Trees are planted on a bare hillside. How does this help the environment?", "Their roots hold the soil so it is not washed away by rain",
  [W("Their leaves make the rain fall faster onto the hill", "wrong-effect", "Trees do not make rain fall faster."), W("Their roots make the soil too hard to be washed away", "wrong-effect", "Roots do not harden the soil. They hold it in place."), W("Their flowers make the soil warmer for the plants", "wrong-effect", "Flowers do not warm the soil.")],
  ["Roots of trees hold the soil together.", "This stops heavy rain from washing the soil down the hill."], None)
q("ae-113", I, 2, HI, "Fishermen catch too many fish, including young ones, from a sea each year. After some years, there are very few fish. What is the best reason?", "Too few fish were left to breed and make young",
  [W("The fish moved to a warmer sea", "wrong-reason", "Fish do not all leave because of fishing. The fish were caught."), W("The young fish grew bigger and ate each other", "wrong-reason", "The young fish were being caught before they could grow."), W("The sea water became too salty", "wrong-reason", "Catching fish does not change how salty the sea is.")],
  ["Catching too many fish, young ones too, leaves too few to breed.", "So the number of fish keeps falling."], None)
q("ae-114", I, 2, HI, "Why does recycling aluminium cans help the environment?", "Less metal has to be mined from the ground",
  [W("More cans can be thrown into the sea", "wrong-effect", "Throwing cans into the sea pollutes it. Recycling means the cans are used again."), W("The cans make the soil more fertile", "wrong-effect", "Cans do not add anything good to soil."), W("The cans give off less heat when they rot", "wrong-effect", "Metal cans do not rot. Recycling saves resources.")],
  ["Recycling uses old cans to make new ones.", "So less metal needs to be dug up, which saves natural resources."], None)
q("ae-115", I, 1, AD, "Penguins in a very cold place huddle close together in groups. How does this help them?", "They lose less body heat",
  [W("They can swim faster", "wrong-use", "Huddling happens on the ice, not in the water."), W("They can see danger from further away", "wrong-use", "Standing together does not help them see further."), W("They can catch more fish", "wrong-use", "Penguins huddle to keep warm, not to catch fish.")],
  ["Huddling together keeps the warm air between their bodies, so each penguin loses less heat."], None)
q("ae-116", I, 1, AD, "Which of the following is a behavioural adaptation that helps an animal escape from predators?", "A hedgehog curls into a ball when it is frightened",
  [W("A stick insect has a body shaped like a twig", "structural", "This is a body shape, so it is a structural adaptation."), W("A porcupine has sharp quills on its back", "structural", "Quills are body parts, so this is a structural adaptation."), W("A frog has green skin like the leaves around it", "structural", "Skin colour is part of the body, so it is structural.")],
  ["A behavioural adaptation is something an animal does.", "Curling into a ball is what the hedgehog does when in danger."], None)

# ---------------- competent ----------------
q("ae-201", C, 1, AD, "Which row correctly matches each animal to how its feature helps it survive?", "Camel: wide flat feet, so it does not sink into sand",
  [W("Camel: large hump, so it stores water", "myth", "The hump stores fat, not water."), W("Polar bear: thin fur, so it can swim faster", "wrong-reason", "A polar bear has thick fur to keep warm."), W("Duck: sharp claws, so it can push through water", "wrong-reason", "A duck has webbed feet for swimming, not sharp claws.")],
  ["Wide, flat feet spread the camel's weight over a larger area, so it does not sink into soft sand."], None)
q("ae-202", C, 1, AD, "Which of the following are structural adaptations?\nA: A frog's green skin.\nB: A bear's winter sleep.\nC: A fish's gills.\nD: A swallow flying to a warm place in winter.", "A and C only",
  [W("A and B only", "mix-up", "B is something the bear does, so it is behavioural."), W("B and D only", "mix-up", "Both are things animals do, so both are behavioural."), W("C and D only", "mix-up", "D is behavioural because it is something the bird does.")],
  ["Skin colour and gills are parts of the body, so A and C are structural.", "Sleeping through winter and flying away are behaviours."], None)
q("ae-203", C, 1, AD, "Which of the following are behavioural adaptations?\nA: A cactus storing water in its stem.\nB: A whale's thick layer of blubber.\nC: A squirrel burying nuts in autumn.\nD: A fish swimming in a group (school).", "C and D only",
  [W("A and B only", "mix-up", "Both are parts of the body, so both are structural."), W("A and C only", "mix-up", "A is the stem of a plant, which is structural."), W("B and D only", "mix-up", "B is a body part, so it is structural.")],
  ["Burying nuts and swimming in a group are things the animals do, so they are behavioural.", "A and B are body parts."], None)
q("ae-204", C, 1, AD, "The table shows the leaves and roots of two plants, A and B. Where does each plant most likely live?", "A lives in a desert and B lives on a dark rainforest floor",
  [W("A lives on a dark rainforest floor and B lives in a desert", "reversed", "Plant A, with small waxy leaves and deep roots, is the desert one."), W("Both A and B live in a desert", "misread", "Plant B has large thin leaves that would lose too much water in the heat."), W("Both A and B live on a dark rainforest floor", "misread", "Plant A has small waxy leaves. It lives where water is short.")],
  ["Small waxy leaves and deep roots save and find water in dry places.", "Large thin leaves catch weak light in a dark forest."],
  tb(["Plant", "Leaves", "Roots"], [["A", "small, thick, waxy", "long and deep"], ["B", "large and thin", "short and shallow"]], [60, 160, 130], "Two plants"))
q("ae-205", C, 1, AD, "The table shows four animals. Which animal is best able to swim fast through water?", "P",
  [W("Q", "wrong-feature", "Q has a wide, flat body and short limbs, which do not cut through water."), W("R", "wrong-feature", "R has a rough, bumpy body that would slow it down in water."), W("S", "wrong-feature", "S has long legs and a thin body made for running on land.")],
  ["A smooth body that is narrow at the ends and has fins can move easily through water."],
  tb(["Animal", "Body"], [["P", "smooth, narrow at both ends, with fins"], ["Q", "wide, flat, short limbs"], ["R", "bumpy, rough skin"], ["S", "long legs, thin body"]], [70, 260], "Four animals"))
q("ae-206", C, 2, HI, "The table shows the area of sea ice and the number of polar bear cubs born in one place over 20 years. Which statement does the table best support?", "As the sea ice became smaller, fewer cubs were born",
  [W("As the sea ice became smaller, more cubs were born", "reversed", "The number of cubs fell when the ice area fell."), W("The number of cubs did not change as the ice melted", "misread", "The number of cubs fell from 60 to 20."), W("The area of sea ice became larger every 5 years", "misread", "The ice area was smaller at each year shown.")],
  ["Both columns go down together.", "There were fewer cubs when there was less sea ice."],
  tb(["Year", "Sea ice (million km²)", "Cubs born"], [["2000", "10", "60"], ["2005", "8.5", "55"], ["2010", "7", "40"], ["2015", "6", "30"], ["2020", "5", "20"]], [70, 170, 100], "Sea ice and polar bear cubs"))
q("ae-207", C, 1, FT, "Wei Ling puts a thick coat of wax on one of two identical leaves and leaves the other bare. She leaves both in the sun and weighs them each day. The table shows her results. What can she conclude?", "A waxy coat helps a leaf lose less water",
  [W("A waxy coat makes a leaf take in more water", "wrong-conclusion", "The waxy leaf lost less mass, so it kept more water. It did not take any in."), W("Leaves lose no water when they are in the sun", "wrong-conclusion", "Both leaves lost mass, so both lost water."), W("A leaf without wax loses water more slowly", "reversed", "The leaf without wax lost more mass, so it lost water faster.")],
  ["The bare leaf's mass fell by 4 g. The waxy leaf's mass fell by only 1 g.", "So the wax stops some water from escaping."],
  tb(["Leaf", "Mass at start (g)", "Mass after 3 days (g)"], [["With wax", "10", "9"], ["Without wax", "10", "6"]], [90, 140, 170], "Mass of two leaves"))
q("ae-208", C, 1, FT, "Paper moths of two colours were placed on a dark tree trunk. Birds were allowed to look for them for 10 minutes. The table shows how many were found. What can be concluded?", "Moths that match their background are seen less",
  [W("Dark moths are always safer than pale moths everywhere", "overgeneralise", "They were safer only on the dark trunk. On a pale background it may be the other way round."), W("Birds only eat the pale moths that they find", "wrong-conclusion", "Birds found some dark moths too, only fewer."), W("Pale moths hide better on a dark trunk", "reversed", "The pale moths were found more often on the dark trunk.")],
  ["More pale moths were found on the dark trunk than dark moths.", "So moths that match their background are seen less."],
  tb(["Colour of moths", "Number put out", "Number found by birds"], [["Dark", "20", "4"], ["Pale", "20", "15"]], [110, 120, 150], "Moths on a dark tree trunk"))
q("ae-209", C, 2, HI, "Oil spills from a ship into the sea and covers the feathers of seabirds. Why are these birds likely to die?", "Their feathers no longer keep them warm and dry",
  [W("The oil gives them too much extra food to eat", "wrong-effect", "Oil is not food. It harms the birds."), W("The oil makes their wings grow too large", "wrong-effect", "Oil does not make wings grow."), W("The oil makes the sea water too salty to swim in", "wrong-effect", "The harm comes from the oil on the feathers, not from salty water.")],
  ["Oil clogs the feathers, so water gets through to the skin.", "The birds get cold and cannot swim or fly well."], None)
q("ae-210", C, 2, HI, "Which of the following actions can help to reduce global warming?\nA: Planting more trees.\nB: Burning more fuel in cars.\nC: Using public transport.\nD: Cutting down forests.", "A and C only",
  [W("A and B only", "mix-up", "B puts more carbon dioxide into the air, which makes global warming worse."), W("B and D only", "mix-up", "Both make global warming worse."), W("C and D only", "mix-up", "D removes trees that take in carbon dioxide.")],
  ["Trees take in carbon dioxide, and public transport burns less fuel for each person.", "Burning more fuel and cutting forests make it worse."], None)
q("ae-211", C, 2, HI, "After all the trees on a hillside are cut down, heavy rain washes soil into a river and the river water turns muddy. Why do the water plants in the river die?", "The mud blocks light so they cannot make food",
  [W("The mud gives them too many minerals to take in", "wrong-reason", "Mud in the water does not feed them. It blocks the light."), W("The rain makes the river water too cold", "wrong-reason", "The rain is not the direct cause. It is the mud in the water."), W("The mud stops them from making flowers", "wrong-reason", "The plants die because they cannot make food, not because of flowers.")],
  ["Muddy water lets in less light.", "Plants need light to make food, so the water plants die."], None)
q("ae-212", C, 2, HI, "A factory pours waste into a stream at point Q. The bar graph shows the number of fish at four points along the stream. P is before Q. Which statement is the best explanation of the graph?", "The waste harms fish near where it enters and is spread out further downstream",
  [W("The waste makes the fish grow bigger at point R", "wrong-reason", "The graph shows the number of fish, not their size. There are few at R."), W("There were fewer fish at point P because the stream began there", "wrong-reason", "P had the most fish. It is before the waste."), W("Fish prefer to live near the factory", "reversed", "Very few fish live near the factory outlet.")],
  ["Point P is before the waste and has many fish.", "Point Q is at the outlet and has the fewest. The number grows again as the waste is diluted."],
  lambda: graph(["P", "Q", "R", "S"], [("fish", [22, 3, 8, 16])], 25, "Point along the stream", "Number of fish", "Fish at four points in a stream", ystep=5, bars=True))
q("ae-213", C, 1, AD, "A desert fox has very large ears that have many blood vessels close to the skin. How do the large ears help the fox?", "They let the fox lose body heat to the air",
  [W("They keep the fox's body warm in the cold desert night", "wrong-reason", "Large thin ears lose heat. They would make the fox colder."), W("They help the fox store water in its body", "wrong-reason", "Ears do not store water."), W("They keep the sand out of its eyes", "wrong-reason", "Large ears are for losing heat, not for blocking sand.")],
  ["Heat moves out of the blood into the air through the large, thin ears.", "This helps the fox stay cool in the hot desert."], None)
q("ae-214", C, 2, HI, "The graph shows the average temperature of the Earth over 40 years. Which statement is correct?", "The average temperature rose over the years",
  [W("The average temperature fell over the years", "reversed", "The line goes up, so the temperature rose."), W("The average temperature stayed the same", "misread", "The values are higher each time."), W("The average temperature was highest in 1980", "misread", "1980 had the lowest value on the graph.")],
  ["Each point on the line is higher than the one before it, so the average temperature rose."],
  lambda: graph(["1980", "1990", "2000", "2010", "2020"], [("t", [14.0, 14.2, 14.4, 14.6, 14.9])], 15.0, "Year", "Average temperature (°C)", "Average temperature of the Earth", ystep=0.5, ymin=13.5))
q("ae-215", C, 2, HI, "A farmer puts too much fertiliser on his field. Some of it washes into a nearby pond, and green algae spread over the surface. Why may the fish in the pond die?", "Algae block light, so plants die and oxygen is used up",
  [W("The algae use up all the food of the fish in one day", "wrong-reason", "Fish are not killed that fast by the algae eating their food. The main problem is the light and oxygen."), W("The fertiliser makes the pond water too cold for the fish", "wrong-reason", "Fertiliser does not change the water temperature much."), W("The algae give off a gas that helps fish to breathe", "wrong-reason", "Dying plants and algae use up oxygen, they do not add it for the fish.")],
  ["Algae cover the surface and cut off light, so the plants below die.", "Dead plants rot and use oxygen, and the fish do not have enough to breathe."], None)
q("ae-216", C, 2, HI, "Which shows the correct chain of events that leads to global warming?", "More fuel burnt, more carbon dioxide in the air, more heat trapped, Earth becomes warmer",
  [W("More trees planted, more carbon dioxide in the air, more heat trapped, Earth becomes warmer", "wrong-cause", "More trees take in carbon dioxide, so there would be less of it."), W("More fuel burnt, less carbon dioxide in the air, more heat trapped, Earth becomes warmer", "wrong-link", "Burning fuel gives more carbon dioxide, not less."), W("More fuel burnt, more carbon dioxide in the air, less heat trapped, Earth becomes cooler", "wrong-link", "More carbon dioxide traps more heat and the Earth warms.")],
  ["Burning fuel adds carbon dioxide. Carbon dioxide traps heat, so the Earth becomes warmer."], None)
q("ae-217", C, 1, AD, "A camel has a hump of fat on its back. Which statement is correct about how the hump helps the camel?", "The fat can be used for energy when the camel cannot find food",
  [W("The hump holds a large store of water for the camel", "myth", "The hump holds fat. It does not hold water."), W("The hump keeps the camel's body cool in the sun", "wrong-reason", "Fat on the back does not cool the camel."), W("The hump makes the camel run faster over the sand", "wrong-reason", "The hump has no effect on how fast it runs.")],
  ["The hump stores fat, which the camel's body breaks down to get energy when food is scarce."], None)
q("ae-218", C, 2, HI, "Which statements about reducing waste are correct?\nA: Washing and reusing glass jars saves resources.\nB: Throwing away things that can be mended reduces waste.\nC: Sorting paper and bottles for recycling means less new material is needed.\nD: Using a lot of plastic bags gives less rubbish.", "A and C only",
  [W("A and B only", "mix-up", "B is wrong. Throwing away things that can be mended makes more waste."), W("B and D only", "mix-up", "Both B and D increase waste."), W("C and D only", "mix-up", "D is wrong. Using many plastic bags makes more rubbish.")],
  ["Reusing jars and recycling save resources, so A and C are correct.", "B and D make more rubbish."], None)
q("ae-219", C, 1, AD, "The table shows four animals that live in a hot desert. Which animal is best adapted to survive there?", "R",
  [W("P", "wrong-feature", "P has thick fur and is active in the day, so it would overheat."), W("Q", "wrong-feature", "Q has a thin, bare body that loses water quickly and is active in the day."), W("S", "wrong-feature", "S is active at night, but its thin fur and small ears do not help it lose heat or save water.")],
  ["R has large ears to lose heat, a waxy skin that holds in water, and it is active at night when it is cool."],
  tb(["Animal", "Body", "Active in the"], [["P", "thick fur, small ears", "day"], ["Q", "thin bare skin", "day"], ["R", "large ears, skin holds in water", "night"], ["S", "thin fur, small ears", "night"]], [60, 220, 100], "Four desert animals"))
q("ae-220", C, 1, AD, "An Arctic fox has brown fur in summer and white fur in winter. How does this help the fox?", "Other animals find it hard to see it on the ground",
  [W("It keeps the fox warm during the summer months", "wrong-reason", "Brown fur does not warm the fox. The colour helps it hide."), W("It makes the fox's fur grow faster in each season", "wrong-reason", "Fur colour does not change how fast fur grows."), W("It lets the fox store more fat for winter", "wrong-reason", "Fur colour has nothing to do with storing fat.")],
  ["The fur colour matches the ground in each season.", "That makes the fox hard to see, so it can hide from predators and sneak up on prey."], None)
q("ae-221", C, 2, HI, "Why is it a good idea for a country to have rules to stop people from hunting rare animals?", "The animals can breed and their numbers can grow again",
  [W("The rare animals will become fiercer", "wrong-effect", "Rules do not change how fierce animals are."), W("There will be fewer plants for them to eat", "wrong-effect", "Plants are not affected this way. The rules protect the animals."), W("The animals will move to another country", "wrong-effect", "The rules do not make animals move. They protect those in the country.")],
  ["If the animals are not hunted, more of them live to breed.", "Their numbers can grow again and the kind is not lost."], None)

if __name__ == "__main__":
    print("added", add(SUB, FILE, P))
    lint(SUB, FILE, "ae-")
