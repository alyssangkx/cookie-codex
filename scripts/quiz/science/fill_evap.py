"""PSLE-style items for sci-cycles-water-evaporation (file sci-water-evap.json), all tiers (round sci-fill4-water-evap-2026-11-20)."""
from fillkit import add, table, graph, lint
from figs_evap import dishes, towels

SUB, FILE = "sci-cycles-water-evaporation", "sci-water-evap.json"
EV, FT, RD = "sci-pat-evaporation-rate", "sci-pat-fair-test-design", "sci-pat-read-data"
B, I, C = "basic", "intermediate", "competent"
P = []
def q(*a): P.append(a)
def W(t, tag, why): return (t, tag, why)
D = "°C"
HDR = ["Set-up", "Temp|(" + D + ")", "Fan", "Dish width|(cm)", "Water|(ml)"]
WID = [58, 64, 52, 84, 64]
def ST(rows, cap="Set-ups of water in dishes"): return lambda: table(HDR, rows, WID, cap)
def GR(xs, ser, ymax, xl, yl, cap, step, **k): return lambda: graph(xs, ser, ymax, xl, yl, cap, ystep=step, W=360, H=250, **k)
# equal volume of water (1800 square units) in containers of different width
WIDE = dict(w=110, h=16); MID = dict(w=76, h=24); NAR = dict(w=50, h=36); TALL = dict(w=40, h=45, ch=80)

# ---------------- basic ----------------
q("ev-001", B, 1, EV, "Which process changes liquid water at the surface of a puddle into water vapour?", "Evaporation",
  [W("Condensation", "reversed", "Condensation changes water vapour into liquid water, the opposite change."), W("Freezing", "wrong-change", "Freezing changes liquid water into ice."), W("Melting", "wrong-change", "Melting changes a solid, such as ice, into liquid water.")],
  ["Evaporation is the change of liquid water into water vapour at its surface."], None)
q("ev-002", B, 1, EV, "Which day is the best for drying wet clothes quickly?", "A hot and windy day",
  [W("A cool day with no wind", "wrong-factor", "Cool, still air gives the slowest drying."), W("A cool and windy day", "partial", "Wind helps, but the cool air slows evaporation."), W("A hot day with no moving air at all", "partial", "Heat helps, but there is no wind to carry the vapour away.")],
  ["Heat and wind both speed up evaporation."], None)
q("ev-003", B, 1, EV, "Two identical wet towels are hung in the same sunny spot as shown. Which towel will dry first?", "P, because more of its water is exposed to the air",
  [W("Q, because it is thicker and holds more heat", "wrong-idea", "A thick folded towel hides most of its water from the air, so it dries slower."), W("Q, because its water is packed close together", "wrong-idea", "Packed water has less surface in contact with the air."), W("Both dry at the same time because they are in the same place", "ignore-area", "The shape matters. The spread towel has a larger exposed surface.")],
  ["The spread-out towel P shows a larger surface to the air, so it dries faster."], lambda: towels([("P", "spread"), ("Q", "folded")], "Two wet towels on a line"))
q("ev-004", B, 1, EV, "Which statement about evaporation is correct?", "It can happen at room temperature",
  [W("It happens only when water boils", "boil-confusion", "Water evaporates at any temperature. Boiling is faster, but evaporation does not wait for it."), W("It happens only when water is in sunlight", "wrong-idea", "Water also evaporates in the shade."), W("It changes water vapour into liquid water", "reversed", "That is condensation.")],
  ["Water evaporates from its surface at any temperature."], None)
q("ev-005", B, 1, EV, "After a sunny afternoon, a puddle on a road has gone. Where did the water go?", "It became vapour and went into the air",
  [W("It sank down into the hard road", "wrong-idea", "A road is hard and does not soak up a puddle."), W("It changed into tiny pieces of ice", "wrong-change", "The day was hot, so the water did not freeze."), W("It was destroyed by the heat of the Sun", "wrong-idea", "Matter is not destroyed. The water changed state.")],
  ["The water evaporated into water vapour."], None)
q("ev-006", B, 1, EV, "Which of the following would increase the rate of evaporation of water in a bowl?", "Blowing air across the water with a fan",
  [W("Putting a lid on the bowl", "wrong-factor", "A lid traps the water vapour above the water."), W("Moving the bowl to a colder place", "wrong-factor", "A colder place slows evaporation."), W("Pouring the water into a narrow tall cup", "wrong-factor", "A narrower surface is smaller, so evaporation is slower.")],
  ["Moving air carries away water vapour, so evaporation is faster."], None)
q("ev-007", B, 1, EV, "Two containers hold the same amount of water and are left in the same place, as shown. Which has less water left after 5 hours?", "A, because more of its water touches the air",
  [W("B, because its water is deeper and stores more heat", "wrong-idea", "Depth does not speed up evaporation. Surface area does."), W("B, because its sides are taller", "wrong-idea", "Tall sides do not help the water evaporate."), W("They are the same, as they hold equal water", "ignore-area", "Equal amounts of water do not mean equal exposed surface.")],
  ["A is wider, so it has the larger exposed surface and loses water faster."],
  lambda: dishes([dict(lab="A", **WIDE), dict(lab="B", **NAR)], "Two containers of water"))
q("ev-008", B, 1, EV, "Two identical dishes hold the same amount of water. A fan blows over dish A, as shown. Which dries up first?", "A, because moving air carries the vapour away",
  [W("B, because still air keeps the water warm", "wrong-idea", "Still air lets vapour build up above the water, so B is slower."), W("A, because the fan makes the water hotter", "wrong-idea", "A fan does not heat the water."), W("They dry up together, as the dishes are the same", "ignore-wind", "Wind is the one difference, and it speeds up evaporation.")],
  ["Moving air removes the water vapour at the surface, so A dries first."],
  lambda: dishes([dict(lab="A", fan=True, **MID), dict(lab="B", **MID)], "Two dishes of water"))
q("ev-009", B, 1, EV, "Two identical dishes hold the same amount of water. One is in a sunny spot and one in a shady spot, as shown. Which loses more water in 4 hours?", "A, because the heat of the Sun warms its water",
  [W("B, because the shade is a cooler and calmer place", "reversed", "Cooler places slow evaporation down."), W("B, because the Sun makes its water heavier", "wrong-idea", "The Sun does not add mass to water."), W("Both lose the same amount of water", "ignore-temp", "The Sun makes one dish warmer, so it loses water faster.")],
  ["A is warmer, so its water evaporates faster."],
  lambda: dishes([dict(lab="A", sun=True, notes=["sunny spot"], **MID), dict(lab="B", notes=["shady spot"], **MID)], "Two dishes of water"))
q("ev-010", B, 1, EV, "Why do we hang washing in an open, airy place instead of in a closed cupboard?", "Moving air carries away the vapour, so it dries faster",
  [W("Moving air makes the water in the clothes boil", "boil-confusion", "Air does not make the water boil."), W("Clothes dry faster because the cupboard has no light", "wrong-idea", "Light is not what dries the clothes. Moving air and warmth are."), W("The cupboard adds more water to the clothes", "wrong-idea", "A cupboard does not add water. It just stops the vapour leaving.")],
  ["Wind carries away the water vapour from the clothes."], None)
q("ev-011", B, 1, EV, "Where should Mei hang her wet shoes so that they dry quickly?", "Near a sunny window where air can move",
  [W("Inside a closed shoe cupboard", "wrong-factor", "A closed space has no moving air."), W("Inside a plastic bag in the shade", "wrong-factor", "The bag traps the vapour and the shade is cooler."), W("In a dark, cold storeroom", "wrong-factor", "Cold, still air slows evaporation.")],
  ["A warm, breezy place makes the water evaporate fastest."], None)
q("ev-012", B, 1, EV, "Salt is made from seawater in wide, shallow pans left under the Sun. Why are the pans wide and shallow?", "A large surface lets the water evaporate quickly",
  [W("The salt sinks to the bottom faster in a deep pan", "wrong-idea", "Depth does not help the water to leave."), W("A shallow pan makes the water freeze", "wrong-change", "Pans are left in the Sun so that water evaporates, not freezes."), W("A wide pan makes the seawater less salty", "wrong-idea", "The amount of salt does not change. Only the water leaves.")],
  ["More of the water is exposed to the air and the Sun, so it evaporates faster."], None)
q("ev-013", B, 1, EV, "Two same pots hold 200 ml of water each. After one day, the pot with a lid has more water left. Why?", "The lid stops the vapour escaping",
  [W("The lid stops the Sun from heating the water", "wrong-idea", "The pots may be in the same place and heat is not the main cause."), W("The lid adds water to the pot", "wrong-idea", "A lid does not add water."), W("The lid makes the water too cold to evaporate", "wrong-idea", "Water at any temperature can evaporate.")],
  ["With a lid, the water vapour stays trapped, so less water is lost."], None)
q("ev-014", B, 1, FT, "Mei wants to find out if wind affects how fast water evaporates. Which two set-ups should she compare?", "A and B",
  [W("A and C", "wrong-pair", "A and C differ in temperature, not in wind."), W("B and C", "two-changes", "B and C differ in both fan and temperature."), W("C and D", "two-changes", "C and D differ in both temperature and amount of water.")],
  ["A and B are the same except for the fan."],
  ST([["A", "25", "off", "10", "80"], ["B", "25", "on", "10", "80"], ["C", "35", "off", "10", "80"], ["D", "25", "off", "10", "120"]]))
q("ev-015", B, 1, EV, "Which apparatus is best for finding how much water is left in a dish after 3 hours?", "A measuring cylinder",
  [W("A thermometer put into the dish", "wrong-tool", "A thermometer measures temperature."), W("A ruler held next to the dish", "wrong-tool", "A ruler measures length."), W("A stopwatch started with the test", "wrong-tool", "A stopwatch measures time.")],
  ["A measuring cylinder measures the volume of water."], None)
q("ev-016", B, 1, RD, "Each dish had 100 ml of water at first. The bar chart shows the water left after 4 hours. Which dish lost the most water?", "Q",
  [W("R", "read-wrong-way", "R has the tallest bar, which means the most water is left, so it lost the least."), W("P", "wrong-reading", "P kept 70 ml, so it lost 30 ml, less than Q."), W("S", "wrong-reading", "S kept 55 ml, so it lost 45 ml, less than Q.")],
  ["Q has the shortest bar. It kept 40 ml, so it lost 60 ml."],
  lambda: graph(["P", "Q", "R", "S"], [("left", [70, 40, 85, 55])], 100, "Dish", "Water left (ml)", "Water in each dish after 4 hours", ystep=20, W=340, H=240, bars=True))
q("ev-017", B, 1, EV, "Cup X is left in a hot kitchen and cup Y in a cold room. Both are the same and hold the same amount of water. After one day, which has less water?", "Cup X, because it is warmer",
  [W("Cup Y, because it is colder", "reversed", "Evaporation is slower in a colder place."), W("Both have the same amount of water", "ignore-temp", "The two places differ in temperature, so the loss differs."), W("Neither, because water cannot leave a cup", "wrong-idea", "Water vapour can leave from the open top.")],
  ["Higher temperature means faster evaporation."], None)
q("ev-018", B, 1, EV, "On a hot, dry day the water level in a pond drops. What mainly causes this?", "Evaporation of the water",
  [W("Condensation of the water", "reversed", "Condensation would add water, not remove it."), W("Boiling of the pond water", "boil-confusion", "A pond is far below boiling temperature."), W("Freezing of the pond water", "wrong-change", "A hot day does not freeze water.")],
  ["Water evaporates from the pond surface and joins the air as water vapour."], None)
q("ev-019", B, 1, EV, "Mrs Tan's kitchen floor is wet. Which action helps the floor dry fastest?", "Switching on a fan to blow air over the floor",
  [W("Covering the floor with a plastic sheet", "wrong-factor", "A cover traps the vapour."), W("Closing all the windows and doors", "wrong-factor", "Closing up stops the air from moving."), W("Switching on a freezer next to the floor", "wrong-factor", "A colder place slows evaporation.")],
  ["Moving air carries away the vapour, so the floor dries faster."], None)
q("ev-020", B, 1, EV, "From which part of a dish of water does evaporation take place?", "The surface of the water",
  [W("The bottom of the dish", "wrong-idea", "Vapour leaves at the top where water meets the air."), W("Only the sides of the dish", "wrong-idea", "The sides do not matter. The surface does."), W("Only the middle of the water", "wrong-idea", "All of the surface can lose water.")],
  ["Water changes into vapour where it meets the air, at the surface."], None)
q("ev-021", B, 1, EV, "Which of the following is an example of evaporation?", "Wet footprints on warm ground slowly vanish",
  [W("Droplets form on the outside of a cold glass", "reversed", "That is condensation."), W("Water turns into ice in a freezer", "wrong-change", "That is freezing."), W("Steam turns into drops on a pot lid", "reversed", "That is condensation.")],
  ["The water of the footprints changes into water vapour."], None)
q("ev-022", B, 1, EV, "Two identical dishes hold the same amount of water. Dish Q is covered with a lid, as shown. Which loses less water in one day?", "Q, because the vapour cannot escape",
  [W("P, because its water is cooler", "wrong-idea", "The uncovered dish is not cooler in any way shown."), W("P, because the lid draws water out of Q", "wrong-idea", "A lid does not draw water out."), W("Both lose the same amount of water", "ignore-lid", "The lid is the one difference and it slows the loss.")],
  ["The lid traps the vapour, so Q loses less water."],
  lambda: dishes([dict(lab="P", **MID), dict(lab="Q", lid=True, **MID)], "Two dishes of water"))
q("ev-023", B, 1, EV, "Ali wants his wet hair to dry quickly. Which is the best way?", "A hair dryer blowing warm air",
  [W("Covering it with a plastic cap", "wrong-factor", "The cap traps the vapour."), W("Sitting in a cold, closed room alone", "wrong-factor", "Cold, still air is slow."), W("Tying it into a tight bun", "wrong-factor", "A bun hides most of the hair from the air.")],
  ["Warm, moving air makes the water evaporate faster."], None)
q("ev-024", B, 1, EV, "Which wet cloth will take the longest time to dry?", "A cloth folded up in a closed box in a cool room",
  [W("A cloth spread out on a hot, windy open balcony", "wrong-factor", "This is the fastest way to dry."), W("A cloth spread out under a fan in a warm room", "wrong-factor", "Moving air makes it dry fast."), W("A cloth hung open in a warm, sunny room", "wrong-factor", "Heat and a wide surface make it dry fast.")],
  ["Folded, closed in and cool: every factor slows the evaporation."], None)
q("ev-025", B, 1, EV, "Why should wet clothes on a line be hung with space between them?", "More of each cloth is exposed to moving air",
  [W("The clothes weigh less when they are apart", "wrong-idea", "The clothes weigh the same however they hang."), W("The Sun can freeze the clothes if they touch", "wrong-change", "Heat does not freeze clothes."), W("Touching clothes stop the water from existing", "wrong-idea", "Water does not stop existing. It just leaves slower.")],
  ["Space lets air reach more of the wet surface."], None)

# ---------------- intermediate ----------------
T3 = lambda: table(HDR, [["A", "20", "off", "6", "50"], ["B", "20", "off", "12", "50"], ["C", "35", "off", "12", "50"], ["D", "35", "on", "12", "50"]], WID, "Four dishes of water")
q("ev-101", I, 1, FT, "Ali tests how the width of the dish affects the speed of evaporation. Which two set-ups should he compare?", "A and B",
  [W("B and C", "wrong-pair", "B and C differ in temperature, not in width."), W("C and D", "wrong-pair", "C and D differ in the fan, not in width."), W("A and D", "two-changes", "A and D differ in width, temperature and fan.")],
  ["A and B are the same except for the dish width (6 cm and 12 cm)."], T3)
q("ev-102", I, 1, FT, "Which two set-ups should be compared to find out how temperature affects evaporation?", "B and C",
  [W("A and B", "wrong-pair", "A and B differ in dish width."), W("C and D", "wrong-pair", "C and D differ in the fan."), W("A and C", "two-changes", "A and C differ in both temperature and dish width.")],
  ["B and C differ only in temperature (20 " + D + " and 35 " + D + ")."], T3)
q("ev-103", I, 1, FT, "Which two set-ups should be compared to find out how wind affects evaporation?", "C and D",
  [W("A and B", "wrong-pair", "A and B differ in dish width."), W("B and C", "wrong-pair", "B and C differ in temperature."), W("B and D", "two-changes", "B and D differ in both temperature and fan.")],
  ["C and D are the same except for the fan."], T3)
T6 = lambda: table(HDR, [["A", "35", "on", "12", "100"], ["B", "25", "off", "6", "100"], ["C", "35", "off", "6", "100"], ["D", "25", "on", "12", "100"]], WID, "Four dishes of water")
q("ev-104", I, 1, EV, "The same dishes are left for 6 hours. In which set-up will the water be used up first?", "A",
  [W("B", "reversed", "B has a low temperature, no wind and a small surface, so it is the slowest."), W("C", "partial", "C is hot, but it has no wind and a small surface."), W("D", "partial", "D has wind and a wide dish, but it is cooler than A.")],
  ["A has a high temperature, a fan and a wide dish: all three speed up evaporation."], T6)
q("ev-105", I, 1, EV, "The dishes hold the same amount of water and are left in the same place. Which dish will be the last to run dry?", "C",
  [W("A", "reversed", "A has the widest surface, so it dries first."), W("B", "partial", "B has a smaller surface than A, but C is smaller still."), W("They run dry together", "ignore-area", "Their exposed surfaces differ, so the times differ.")],
  ["C is the narrowest, so it has the smallest exposed surface."],
  lambda: dishes([dict(lab="A", **WIDE), dict(lab="B", **MID), dict(lab="C", **NAR)], "Three dishes of water", minslot=110))
G2 = GR(["0", "1", "2", "3", "4"], [("X", [100, 82, 64, 46, 28]), ("Y", [100, 94, 88, 82, 76])], 100, "Time (h)", "Water left (ml)", "Water left in two dishes", 20, legend="bl")
q("ev-106", I, 1, RD, "Two dishes had the same amount of water at first, as the graph shows. In which dish did the water evaporate faster?", "X, because its line falls more steeply",
  [W("Y, because it has more water left", "read-wrong-way", "More water left means less water evaporated."), W("Y, because its line is flatter", "reversed", "A flatter line means slower loss."), W("Both, because the lines start together", "ignore-data", "The lines separate, so the rates differ.")],
  ["X lost 72 ml in 4 hours and Y lost 24 ml, so X evaporated faster."], G2)
q("ev-107", I, 1, RD, "From the graph of the two dishes, how much water evaporated from dish X in the first 3 hours?", "54 ml",
  [W("46 ml", "read-wrong-way", "46 ml is the water left, not the water lost."), W("18 ml", "wrong-dish", "18 ml is the loss of dish Y."), W("28 ml", "wrong-reading", "28 ml is the water left at 4 hours.")],
  ["100 - 46 = 54 ml."], G2)
q("ev-108", I, 1, EV, "In salt farms, seawater is led into very wide, shallow ponds in sunny places. Which pair of reasons explains this best?", "A big surface and the Sun's heat both speed up evaporation",
  [W("A deep pond heats up too fast and the water boils", "boil-confusion", "Evaporation, not boiling, removes the water."), W("A shallow pond stops the wind and stores the salt", "wrong-factor", "Wind helps evaporation and the pond does not stop it."), W("Wide ponds help the Sun freeze the salt out", "wrong-change", "Salt is left behind when the water evaporates.")],
  ["Wide ponds expose more water, and the Sun warms it."], None)
q("ev-109", I, 1, EV, "Wet clothes are hung in a small bathroom with the door and window shut. They dry slowly. Which is the main reason?", "There is no moving air to carry the vapour away",
  [W("There is no light to dry the clothes", "wrong-idea", "Light itself does not dry clothes."), W("The clothes weigh more in a small room", "wrong-idea", "Weight does not change with the room."), W("Evaporation cannot happen indoors", "wrong-idea", "Evaporation happens indoors too, only slower here.")],
  ["Without moving air, the vapour stays near the clothes."], None)
q("ev-110", I, 1, EV, "The same amount of water is poured into a wide dish and a tall, narrow cup and left side by side. After a day, the cup has more water left. Why?", "The dish has a larger exposed surface",
  [W("The cup is taller and the water is deeper", "wrong-idea", "Deeper water does not slow evaporation by being deep. The small surface does."), W("The dish makes the water hotter", "wrong-idea", "Both are in the same place, so the temperature is the same."), W("The cup has less water at first", "wrong-idea", "The question says the amounts are the same.")],
  ["Evaporation takes place at the surface, so the wider dish loses water faster."],
  lambda: dishes([dict(lab="Dish", **WIDE), dict(lab="Cup", **TALL)], "Water in a dish and in a cup", minslot=110))
q("ev-111", I, 1, EV, "Two identical beakers hold the same amount of water. One is placed near a heater and one in a cool room. Which statement is correct?", "The water near the heater evaporates faster",
  [W("The water in the cool room evaporates faster", "reversed", "Heat speeds up evaporation."), W("Only the water near the heater evaporates", "wrong-idea", "Water evaporates in a cool room too, only slowly."), W("The two evaporate at the same rate", "ignore-temp", "The places differ in temperature, so the rates differ.")],
  ["Higher temperature gives faster evaporation, but evaporation still happens in the cool room."], None)
q("ev-112", I, 1, EV, "Zara says, \"Water in an open cup inside a cold refrigerator cannot evaporate.\" What is the best reply?", "It does evaporate, but more slowly than in a warm room",
  [W("She is right, because evaporation only needs boiling", "boil-confusion", "Evaporation takes place at any temperature."), W("She is right, because evaporation needs sunlight", "wrong-idea", "Sunlight is not needed."), W("It evaporates faster because it is cold", "reversed", "Cold slows evaporation.")],
  ["Evaporation is slower in the cold but is never zero."], None)
q("ev-113", I, 1, EV, "Which statement tells evaporation and boiling apart correctly?", "Evaporation is at the surface at any temperature, and boiling is throughout the liquid",
  [W("Evaporation happens only below 50 " + D + ", and boiling happens only above it", "wrong-idea", "Evaporation also takes place at higher temperatures."), W("Evaporation makes liquid water, and boiling makes water vapour", "reversed", "Both give water vapour from liquid water."), W("Evaporation needs a fan to start it, and boiling does not", "wrong-idea", "A fan only makes evaporation faster.")],
  ["Evaporation is a surface change at any temperature. Boiling is rapid vapour formation in the whole liquid."], None)
q("ev-114", I, 1, EV, "Two identical dishes hold the same amount of water and sit in the same place. Dish Q has a lid. After 6 hours, which is correct?", "Dish P has less water left than dish Q",
  [W("Dish Q has less water left than dish P", "reversed", "The lid keeps the vapour in, so Q loses less."), W("Both have the same amount left", "ignore-lid", "The lid is the one difference and slows the loss."), W("Dish Q has no water left", "wrong-idea", "A covered dish loses water slowly.")],
  ["The lid traps the vapour, so Q loses less."],
  lambda: dishes([dict(lab="P", **MID), dict(lab="Q", lid=True, **MID)], "Two dishes of water in the same place"))
q("ev-115", I, 1, EV, "Which set-up in the table would take the longest to lose all its water?", "B",
  [W("A", "reversed", "A is hot, windy and wide: the fastest."), W("C", "partial", "C is hot, so it is faster than B."), W("D", "partial", "D has a fan and is wide, so it is faster than B.")],
  ["B is cool, has no fan and the narrowest dish."], T6)
q("ev-116", I, 1, RD, "The four dishes held 100 ml of water at first and have the same width. The bar chart shows the water left after 3 hours. Which dish was probably in the hottest place?", "S",
  [W("P", "read-wrong-way", "P has the most water left, so it was probably the coolest."), W("Q", "partial", "Q lost some water, but S lost more."), W("R", "partial", "R lost some water, but S lost more.")],
  ["S lost the most water (85 ml), so it evaporated fastest."],
  lambda: graph(["P", "Q", "R", "S"], [("left", [92, 70, 45, 15])], 100, "Dish", "Water left (ml)", "Water in each dish after 3 hours", ystep=20, W=340, H=240, bars=True))
q("ev-117", I, 1, EV, "Ben pours 100 ml of water each into a tray and a tall cup and leaves them in the Sun for 5 hours. The cup has more water left. What does this show?", "A smaller exposed surface gives slower evaporation",
  [W("Tall containers make water heavier", "wrong-idea", "The mass of water does not depend on the container."), W("Water evaporates only from wide containers", "wrong-idea", "It evaporates from every open container."), W("Trays make water boil in the Sun", "boil-confusion", "The water is not boiling.")],
  ["The cup's surface is smaller, so less water leaves."], None)
q("ev-118", I, 1, EV, "A wet shirt is rolled into a tight ball and another is hung with the sleeves spread. Why does the rolled one dry more slowly?", "Most of its water is hidden from the air",
  [W("The rolled shirt is hotter inside", "wrong-idea", "It is not hotter. Its water is just covered."), W("Water cannot evaporate from cloth that is rolled", "wrong-idea", "It evaporates, but only from the outside."), W("The spread shirt is heavier so it loses more", "wrong-idea", "Weight is not the reason.")],
  ["The tight roll exposes a small surface, so it dries slowly."], None)
q("ev-119", I, 1, FT, "Mei compares a towel spread in the Sun with a towel folded in the shade to see if the area exposed matters. Why is this not a fair test?", "Both the area and the temperature are different",
  [W("Both towels are made of the same kind of cloth", "wrong-idea", "Equal cloth is correct for a fair test."), W("She is using only two towels in the test", "wrong-idea", "Two towels are enough for a comparison."), W("The towels are both wet at the very start", "wrong-idea", "They should both be wet at the start.")],
  ["Two things differ, so we cannot tell which one caused the difference."], None)
q("ev-120", I, 1, EV, "A fan blows over a wet cloth. Why does the cloth dry faster?", "The air carries away the vapour as it forms",
  [W("The fan heats the water in the cloth", "wrong-idea", "A fan blows air. It does not heat the water."), W("The fan pushes the water out of the cloth", "wrong-idea", "The water leaves as vapour, not pushed as liquid."), W("The fan turns the water into ice first", "wrong-change", "Freezing is not part of drying.")],
  ["Moving air takes away vapour, so more water can evaporate."], None)
q("ev-121", I, 1, EV, "Which action would slow down the evaporation of a dish of water the most?", "Covering it and placing it in a cool room",
  [W("Placing it in a cool room and leaving the lid off", "partial", "This slows evaporation, but less than doing both."), W("Covering it with a lid and leaving it in the Sun", "partial", "This slows evaporation, but less than doing both."), W("Pouring it into a wider dish in a cool room", "reversed", "A wider surface speeds up evaporation.")],
  ["A lid and a cool place each slow evaporation. Together they slow it the most."], None)
q("ev-122", I, 1, FT, "Dish A is wide and has no fan. Dish B is narrow and has a fan. Both hold the same amount of water. Why can Ali not conclude from this test that wind makes water evaporate faster?", "Both the dish width and the fan are different",
  [W("The two dishes hold the same amount of water", "wrong-idea", "This is correct for a fair test."), W("A fan is not needed for a test", "wrong-idea", "A fan is a good way to make wind."), W("Dish A will dry faster, so the fan has no effect", "wrong-idea", "The dishes also differ in width, so no conclusion is possible.")],
  ["Two variables are changed, so any difference could be due to either."],
  lambda: dishes([dict(lab="A", **WIDE), dict(lab="B", fan=True, **NAR)], "Two dishes of water"))
q("ev-123", I, 1, EV, "After rain, two puddles are the same size. One is in a sunny car park and one is in a shady car park. Which statement is correct?", "The sunny puddle dries first because it is warmer",
  [W("The shady puddle dries first because it is cooler", "reversed", "Cooler places slow evaporation."), W("They dry together because they are the same size", "ignore-temp", "The temperature differs, so the speed differs."), W("The sunny puddle dries by boiling away", "boil-confusion", "The puddle does not reach boiling temperature.")],
  ["More heat gives faster evaporation."], None)
G3 = GR(["0", "2", "4", "6", "8"], [("X", [100, 98, 97, 95, 94]), ("Y", [100, 76, 52, 28, 4])], 100, "Time (h)", "Water left (ml)", "Water left in two dishes", 20, legend="bl")
q("ev-124", I, 1, RD, "The graph shows two dishes with the same water at first. One has a lid and the other does not. Which is the dish with the lid?", "X, because it loses very little water",
  [W("Y, because it loses the most water", "reversed", "A lid stops water from leaving, so the lid dish loses little."), W("Y, because its line falls steadily", "reversed", "A falling line means water is leaving freely."), W("X, because its line starts at the top", "wrong-reading", "Both lines start at the same point.")],
  ["X is almost flat, so the vapour was held in by the lid."], G3)
q("ev-125", I, 1, RD, "The same dish of water was left at three temperatures. It took 12 hours at 20 " + D + ", 8 hours at 30 " + D + " and 5 hours at 40 " + D + " to dry up. Which conclusion is supported?", "A higher temperature made the water dry up sooner",
  [W("A higher temperature made the water last longer", "reversed", "The time got shorter as the temperature rose."), W("The temperature had no effect on the time", "ignore-temp", "The times are all different."), W("Water dried up only at 40 " + D, "wrong-idea", "It dried up at every temperature.")],
  ["The drying time falls from 12 h to 5 h as the temperature rises."], None)

# ---------------- competent ----------------
T4 = lambda: table(HDR, [["A", "30", "on", "10", "100"], ["B", "30", "on", "10", "200"], ["C", "30", "on", "5", "100"], ["D", "40", "on", "10", "100"]], WID, "Four dishes of water")
q("ev-201", C, 1, FT, "Mei wants to find out if the exposed surface area affects the rate of evaporation. Which two set-ups should she compare?", "A and C",
  [W("A and B", "wrong-pair", "A and B differ in the amount of water."), W("A and D", "wrong-pair", "A and D differ in temperature."), W("B and D", "two-changes", "B and D differ in both the amount of water and temperature.")],
  ["A and C differ only in the dish width, which sets the exposed surface."], T4)
q("ev-202", C, 1, FT, "Ravi wants to find out if the starting amount of water changes the time taken for the dish to dry up. Which two set-ups should he compare?", "A and B",
  [W("A and C", "wrong-pair", "A and C differ in dish width."), W("C and D", "two-changes", "C and D differ in dish width and temperature."), W("A and D", "wrong-pair", "A and D differ in temperature.")],
  ["A and B differ only in the amount of water."], T4)
q("ev-203", C, 1, FT, "Dishes A and D are compared. The water in D is used up sooner. What can be concluded?", "The higher temperature made evaporation faster",
  [W("The fan made evaporation faster", "wrong-factor", "Both have a fan, so the fan is not the difference."), W("The wider dish made evaporation faster", "wrong-factor", "Both dishes have the same width."), W("The bigger amount of water evaporated faster", "wrong-factor", "Both have 100 ml.")],
  ["A and D differ only in temperature (30 and 40 " + D + ")."], T4)
T5 = lambda: table(HDR, [["A", "30", "on", "8", "100"], ["B", "30", "off", "12", "100"], ["C", "20", "on", "12", "100"], ["D", "20", "off", "8", "100"]], WID, "Four dishes of water")
q("ev-204", C, 1, FT, "Anna compares sets B and C and finds that C dries up later. She says the lower temperature caused this. Why is her conclusion not reliable?", "The fan setting was different too",
  [W("The dishes were the same width", "wrong-idea", "Both are 12 cm wide, which is fair."), W("Both dishes held 100 ml of water", "wrong-idea", "Equal water is correct."), W("Water cannot dry up at 20 " + D, "wrong-idea", "Water evaporates at any temperature.")],
  ["B and C differ in temperature and in the fan, so two things changed."], T5)
G5 = GR(["0", "2", "4", "6", "8"], [("X", [100, 60, 20, 0, 0]), ("Y", [100, 76, 52, 28, 4]), ("Z", [100, 88, 76, 64, 52])], 100, "Time (h)", "Water left (ml)", "Water left in three dishes", 20, legend="bl")
q("ev-205", C, 1, RD, "Three dishes of the same size hold 100 ml of water each. They are in the same place with fans of different speed: none, slow and fast. Which line shows the dish with the slow fan?", "Y",
  [W("X", "partial", "X falls fastest, so it is the fast fan."), W("Z", "partial", "Z falls slowest, so it has no fan."), W("The graph cannot show it", "wrong-idea", "The steepness of the lines ranks them.")],
  ["Steepest X is the fast fan, middle Y is the slow fan, flattest Z is no fan."], G5)
G6 = GR(["0", "1", "2", "3", "4"], [("P", [100, 80, 60, 40, 20]), ("Q", [100, 90, 80, 70, 60])], 100, "Time (h)", "Water left (ml)", "Water left in dishes P and Q", 20, legend="bl")
q("ev-206", C, 1, RD, "The graph shows two dishes of water. Compared with Q, how fast did the water in P evaporate?", "Two times as fast",
  [W("Four times as fast", "wrong-ratio", "P lost 80 ml and Q lost 40 ml in 4 h, a ratio of 2."), W("The same speed", "ignore-data", "The lines have different steepness."), W("Half as fast", "reversed", "P loses more water, so it is faster.")],
  ["P lost 20 ml each hour and Q lost 10 ml each hour."], G6)
q("ev-207", C, 1, RD, "The graph shows two dishes of water. If the water in P keeps evaporating at the same rate, when will P have no water left?", "5 hours",
  [W("4 hours", "wrong-reading", "At 4 h there is still 20 ml in P."), W("6 hours", "wrong-calc", "20 ml at 20 ml per hour takes one more hour, not two."), W("10 hours", "wrong-dish", "10 hours would suit the rate of Q, 10 ml per hour.")],
  ["20 ml are left at 4 h and 20 ml are lost each hour, so it ends at 5 h."], G6)
G8 = GR(["0", "2", "4", "6", "8"], [("K", [100, 56, 12, 0, 0]), ("L", [100, 84, 68, 52, 36]), ("M", [100, 99, 98, 97, 96])], 100, "Time (h)", "Water left (ml)", "Water left in three dishes", 20, legend="bl")
q("ev-208", C, 1, RD, "Three identical dishes hold 100 ml of water. One is uncovered in the Sun, one is uncovered in the shade and one is covered in the shade. Which line shows the dish that is uncovered in the shade?", "L",
  [W("K", "partial", "K falls fastest, so it is the one in the Sun."), W("M", "partial", "M is almost flat, so it is covered."), W("None of them", "wrong-idea", "The middle line fits the dish in the shade.")],
  ["Sun is fastest (K), shade uncovered is middle (L) and covered is slowest (M)."], G8)
q("ev-209", C, 1, EV, "A fan blows over a tightly closed bottle of water for a whole day. The water level hardly changes. Why?", "The vapour formed cannot leave the bottle",
  [W("A fan can only dry solid things", "wrong-idea", "A fan helps liquids evaporate when the vapour can leave."), W("The water has been frozen by the moving air", "wrong-change", "Moving air does not freeze water."), W("Evaporation does not happen at room temperature", "wrong-idea", "It does at any temperature.")],
  ["A closed bottle keeps the vapour in, so the level stays almost the same."], None)
q("ev-210", C, 1, EV, "A pot of water is at 25 " + D + ". Another pot is boiling at 100 " + D + ". Which statement is correct?", "Both pots evaporate, and bubbles form inside only the boiling one",
  [W("Water evaporates only in the boiling pot, and not at 25 " + D, "boil-confusion", "Water at 25 " + D + " also evaporates from its surface."), W("Water in the 25 " + D + " pot cannot become vapour at all", "wrong-idea", "It slowly does."), W("Bubbles of vapour form inside both of the pots", "wrong-idea", "Only the boiling water has vapour bubbles throughout.")],
  ["Evaporation is at the surface at any temperature. Boiling also forms bubbles inside."], None)
q("ev-211", C, 1, EV, "Which of the following would slow down the evaporation of seawater in a salt pan?", "Building high walls around the pan to block the wind",
  [W("Spreading the seawater in a thin layer", "reversed", "A thin layer has a large surface, which speeds it up."), W("Moving the pan from the shade into full sun", "reversed", "More heat speeds it up."), W("Letting the wind blow across the pan", "reversed", "Wind speeds it up.")],
  ["Blocking the wind leaves vapour above the water, so evaporation is slower."], None)
q("ev-212", C, 1, FT, "The three dishes hold the same amount of water and are left in the same place. Which two dishes should be compared to find the effect of exposed surface area?", "A and C",
  [W("A and B", "two-changes", "A and B differ in both width and fan."), W("B and C", "wrong-pair", "B and C differ in the fan only."), W("A, B and C all together", "wrong-idea", "Compare two dishes that differ in one thing.")],
  ["A and C are blown by a fan and differ only in width."],
  lambda: dishes([dict(lab="A", fan=True, **WIDE), dict(lab="B", **NAR), dict(lab="C", fan=True, **NAR)], "Three dishes of water", minslot=110))
q("ev-213", C, 1, EV, "A dish loses 40 ml of water in 3 hours at 30 " + D + ". The same dish, with the same amount of water, is put in the same place with the temperature raised to 40 " + D + ". How much water does it most likely lose in 3 hours?", "More than 40 ml",
  [W("Less than 40 ml", "reversed", "A higher temperature speeds up evaporation."), W("Exactly 40 ml", "ignore-temp", "The temperature is different, so the loss differs."), W("None", "wrong-idea", "Water still evaporates at 40 " + D + ".")],
  ["Higher temperature means more water lost in the same time."], None)
q("ev-214", C, 1, EV, "Which set-up in the table has the slowest rate of evaporation?", "B",
  [W("A", "reversed", "A has every fast factor."), W("C", "partial", "C is hot, so it is faster than B."), W("D", "partial", "D has wind and a wide dish, so it is faster than B.")],
  ["B is cooler, has no fan and has the smallest surface."], T6)
q("ev-215", C, 1, RD, "Dishes P and Q differ only in width (P is 6 cm, Q is 10 cm). Dishes Q and R differ only in temperature (R is hotter). Each had 100 ml of water. The bar chart shows the water left after 3 hours. Which conclusion is supported?", "A wider dish and a higher temperature each made evaporation faster",
  [W("A narrower dish and a higher temperature each made evaporation faster", "reversed", "P is narrower and kept more water."), W("Only the width of the dish changed the rate", "ignore-temp", "R also lost more water than Q."), W("Only the temperature changed the rate", "ignore-area", "Q also lost more water than P.")],
  ["P to Q: more water lost with the wider dish. Q to R: more lost at a higher temperature."],
  lambda: graph(["P", "Q", "R"], [("left", [80, 50, 20])], 100, "Dish", "Water left (ml)", "Water in each dish after 3 hours", ystep=20, W=320, H=240, bars=True))
q("ev-216", C, 1, FT, "Ali tests how wind affects evaporation using two dishes of water. Which of these must be kept the same in both dishes?", "The width of the dish",
  [W("The speed of the air moving over the dish", "changed-variable", "This is the variable Ali changes."), W("Whether a fan is blowing at the dish", "changed-variable", "This is the variable Ali changes."), W("The amount of water left after 3 hours", "measured-variable", "This is what Ali measures. It is expected to differ.")],
  ["Everything except the wind must stay the same, including the dish width."], None)
q("ev-217", C, 1, FT, "Mei changes the width of the dish to see how it affects evaporation. What should she measure?", "The water left in each dish after the same time",
  [W("The width of each dish, which she changes", "changed-variable", "She changes the width. She does not measure it as the result."), W("The temperature of the room around the dishes", "kept-same", "The temperature is kept the same."), W("The number of dishes that she is using", "wrong-idea", "This does not show how fast the water evaporated.")],
  ["The result is shown by how much water has been lost in the same time."], None)
q("ev-218", C, 1, EV, "A heap of wet clothes stays damp in a basket for days, but the same clothes hung out dry in a few hours. What is the main reason?", "Little water is exposed, and air does not move over it",
  [W("The clothes in the basket weigh less than the hung ones", "wrong-idea", "Weight is not the cause."), W("The basket makes the water in the clothes more salty", "wrong-idea", "The water does not become salty."), W("Clothes cannot lose water when it is dark inside", "wrong-idea", "Evaporation does not need light.")],
  ["A heap hides its water and has no wind, so it dries slowly."], None)
q("ev-219", C, 1, EV, "The same volume of rainwater is spread thinly over a large car park and also collected in a narrow bucket in the same Sun. Which dries first and why?", "The car park, because its thin layer has a large surface",
  [W("The bucket, because its water is deeper than the layer", "wrong-idea", "Deeper water does not dry faster."), W("The bucket, because its sides keep the water warm", "wrong-idea", "The sides do not speed things up."), W("They dry at the same time", "ignore-area", "The surfaces differ greatly.")],
  ["A large surface exposes more water to the air."], None)
q("ev-220", C, 1, RD, "Wei pours 100 ml of water each into a narrow beaker and a wide tray in the Sun. After 2 hours, the beaker has 92 ml and the tray has 70 ml. How much more water evaporated from the tray than from the beaker?", "22 ml",
  [W("30 ml", "wrong-calc", "30 ml is the water lost from the tray only."), W("8 ml", "wrong-calc", "8 ml is the water lost from the beaker only."), W("162 ml", "wrong-calc", "162 ml adds the water that is left, which is not a loss.")],
  ["Tray lost 100 - 70 = 30 ml. Beaker lost 100 - 92 = 8 ml. 30 - 8 = 22 ml."], None)
q("ev-221", C, 1, EV, "A dish of water dries up in 10 hours at 30 " + D + " and in 6 hours at 40 " + D + ". Everything else is the same. Which is the best prediction for 50 " + D + "?", "Less than 6 hours",
  [W("More than 6 hours", "reversed", "Heat speeds up evaporation."), W("Exactly 6 hours", "ignore-temp", "Temperature has an effect."), W("Exactly 2 hours", "assume-linear", "We cannot be sure of an exact time. The safe claim is that it is shorter.")],
  ["A higher temperature makes it faster, so the time is shorter."], None)
q("ev-222", C, 1, EV, "A beaker of water is placed on a hot plate that is switched on, before the water reaches boiling point. Compared with an identical beaker on a bench, what is true?", "The beaker on the hot plate loses water faster",
  [W("No water evaporates until the water starts to boil", "boil-confusion", "Evaporation happens before boiling."), W("The beaker on the bench evaporates faster than the other", "reversed", "Heat speeds up evaporation."), W("The two beakers evaporate at the same rate as each other", "ignore-temp", "The hot plate warms the water, so it evaporates faster.")],
  ["Warm water evaporates faster, even before it boils."], None)
q("ev-223", C, 1, FT, "Zara puts 100 ml in dish A and 150 ml in dish B, and puts a fan by B only. She wants to test the effect of the fan. How can she improve the test?", "Pour equal amounts into both dishes",
  [W("Use dishes of different widths", "adds-variable", "A different width adds a second changed variable."), W("Put the two dishes in different places", "adds-variable", "A different place adds a second changed variable."), W("Measure the dishes after different times", "adds-variable", "Different times make the results unfair.")],
  ["Only the fan should differ, so the water amount must be equal."], None)
G9 = GR(["0", "1", "2", "3", "4"], [("A", [100, 85, 70, 55, 40]), ("B", [60, 45, 30, 15, 0])], 100, "Time (h)", "Water left (ml)", "Water left in dishes A and B", 20, legend="tr")
q("ev-224", C, 1, RD, "Dishes A and B are the same size and are in the same place. Which statement about the graph is correct?", "Both evaporated at the same rate, but B started with less water",
  [W("B evaporated faster because it ran out first", "wrong-reading", "Both lose 15 ml each hour."), W("A evaporated faster because it has more water left", "read-wrong-way", "More water left does not mean faster loss."), W("A did not evaporate at all", "wrong-reading", "A's line goes down, so it did evaporate.")],
  ["Both lines have the same steepness: 15 ml per hour."], G9)
q("ev-225", C, 1, RD, "The same amount of water was put in dishes of different width. The bar chart shows the time taken to dry up. Which is the best prediction for a 12 cm dish?", "Fewer than 8 hours",
  [W("More than 8 hours", "reversed", "The time falls as the dish gets wider."), W("Exactly 8 hours", "ignore-data", "The pattern is that wider dishes dry sooner."), W("20 hours", "wrong-dish", "20 hours is for the narrowest dish.")],
  ["Wider dishes dry up sooner, so 12 cm takes less than 8 hours."],
  lambda: graph(["4", "6", "8", "10"], [("hours", [20, 14, 10, 8])], 24, "Dish width (cm)", "Time to dry (h)", "Time for the water to dry up", ystep=4, W=340, H=240, bars=True))

if __name__ == '__main__':
    print(add(SUB, FILE, P)); lint(SUB, FILE)
