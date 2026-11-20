"""Round sci-fill-step0c-2026-11-20: review fixes (content change = new key; old key retired in fillkit.RETIRED).
 1 candle-in-a-jar set made consistent: the flame goes out when the oxygen left is too little (not "all oxygen used")
 2 rc-201 figure neutral   3 water-state graph stops at boiling (no vapour heated in an open beaker)   4 wc-223 one answer
 5 ag-114 bright light for both jars   6 ev-116 wind/air moisture controlled   7 cv-013 distractors   8 rc-212 table."""
import json
from fillkit import add, remove, ship, table, graph, lint, ITEMS, RETIRED
from figs_air import trough, bells
from figs_resp import circ_block
from figs_wstates import curve
from figs_wcycle import cycle
from fill_circuit_vars import two, cs, cp

SAG, SRC, SWS, SWC, SEV, SCV = "sci-systems-air-gases", "sci-systems-resp-circ-parts", "sci-cycles-water-states", "sci-cycles-water-cycle", "sci-cycles-water-evaporation", "sci-systems-circuit-vars"
D = "°C"
B, I, C = "basic", "intermediate", "competent"
def W(t, tag, why): return (t, tag, why)

CV2 = lambda: curve([(0, -10), (2, 0), (6, 0), (12, 100), (20, 100)], [("A", 1, -10, 8, -10), ("B", 4, 0, 0, -9), ("C", 9, 50, -13, 0), ("D", 16, 100, 0, -9)], caption="Heating ice in a beaker", xmax=20)
RD = "sci-pat-read-data"

AIR = [
 ("ag-318", B, 1, "sci-pat-gases-in-air", "A candle burns under a jar standing on a table. After a while the flame goes out. Why?", "There was too little oxygen left in the jar to keep it burning",
  [W("All the air in the jar has been used up", "air-vs-oxygen", "Only some of the oxygen is used. The other gases stay in the jar."), W("The nitrogen in the jar has been used up", "wrong-gas", "Nitrogen is not used by a burning candle."), W("The jar has too much oxygen", "reversed", "Extra oxygen makes the flame brighter.")],
  ["A burning candle uses oxygen. When the oxygen left is too little, the flame goes out."], lambda: bells([(150, 90, 120, "Jar")], "A candle burning under a jar")),
 ("ag-401", I, 1, "sci-pat-gases-in-air", "A jar is placed over a burning candle standing in water. The flame goes out and the water level in the jar rises. Why does the water level rise?", "The burning candle used some of the oxygen, so there is less gas in the jar",
  [W("The heat of the flame pushes the water up into the jar", "wrong-idea", "A flame does not push the water."), W("The candle wax turns into water that fills the jar from below", "wrong-idea", "Candle wax does not turn into the water in the trough."), W("The nitrogen in the jar is used up by the candle", "wrong-gas", "A candle does not use nitrogen.")],
  ["Some of the oxygen is used, so less gas is left and the air outside pushes water in."], lambda: trough(0, True)),
 ("ag-402", I, 1, "sci-pat-gases-in-air", "A candle burns under a jar over water until it goes out. The water rises a little way into the jar. Which statement about the gas left in the jar is correct?", "It still has some oxygen, but too little to keep the flame going",
  [W("It has no oxygen left, only nitrogen and carbon dioxide", "all-used", "A flame goes out while some oxygen is still left."), W("It is all carbon dioxide, made by the burning candle", "wrong-idea", "Most of the gas left is nitrogen."), W("It is all nitrogen, as nothing else can stay in the jar", "wrong-idea", "Some oxygen and a little carbon dioxide are still there.")],
  ["The flame goes out when the oxygen is too low. Some oxygen is still left."], lambda: trough(0.2, False, caption="Water level after the flame went out")),
 ("ag-403", I, 1, "sci-pat-gases-in-air", "A candle burns under a jar over water as shown. The flame goes out and the water level rises. Which gas in the jar did the candle use?", "Oxygen",
  [W("Nitrogen", "wrong-gas", "A burning candle does not use nitrogen."), W("Carbon dioxide", "reversed", "A burning candle makes a little carbon dioxide."), W("Water vapour", "wrong-gas", "Water vapour is a tiny, changing part of air.")],
  ["Burning uses oxygen from the air in the jar."], lambda: trough(0, True, caption="A candle burning under a jar")),
 ("ag-414", I, 1, "sci-pat-gases-in-air", "A candle is lit in each of two identical closed jars. Jar A has air only. Jar B has air and a green plant. Both jars are kept in bright light. In which jar does the candle burn for longer?", "Jar B, because the plant adds oxygen in light",
  [W("Jar A, because the plant takes in the oxygen", "reversed", "In bright light the plant gives out oxygen."), W("Both the same, because the plant takes no part", "wrong-idea", "The plant changes the gases in the jar."), W("Jar B, because the plant adds carbon dioxide in light", "wrong-gas", "In light the plant takes in carbon dioxide.")],
  ["More oxygen lets the candle burn longer."], None),
 ("ag-501", C, 1, "sci-pat-gases-in-air", "A candle burns in a closed jar over water until it goes out. The water rises only a short way up the jar. Why does it not rise further?", "The candle used only some of the oxygen, and the other gases stayed in the jar",
  [W("The water is too heavy for the air outside to push it any higher", "wrong-idea", "The amount of gas lost sets the rise."), W("The candle used up all the gases in the jar before it went out", "wrong-idea", "Most of the gas in the jar remained."), W("The candle made new oxygen as it burned, which filled the space", "reversed", "A burning candle uses oxygen. It does not make it.")],
  ["Only some of the oxygen is used, and the rest of the gas stays in the jar."], lambda: trough(0.2, False, caption="Water level after burning")),
]
RESP = [
 ("rc-501", C, 1, "sci-pat-resp-circulatory", "The diagram shows how blood moves between the lungs, the heart and the body. Which two arrows carry blood that contains the most oxygen?", "B and C",
  [W("A and B", "mixed", "A carries blood from the heart to the lungs, which has little oxygen."), W("A and D", "poor-only", "Both carry blood that has little oxygen."), W("C and D", "mixed", "D carries blood from the body to the heart, which has little oxygen.")],
  ["Blood takes in oxygen in the lungs and goes along B to the heart. The heart pumps it along C to the body."], lambda: circ_block()),
 ("rc-512", C, 3, "sci-pat-resp-circulatory", "The table shows whether three substances are carried by human blood and by the tubes of plants. Which substance is most likely P?", "Water",
  [W("Oxygen", "human-only", "Oxygen is carried by blood but not by the tubes of plants, like Q."), W("Carbon dioxide", "human-only", "Carbon dioxide is carried by blood but not by the tubes of plants, like Q."), W("Light energy", "wrong-idea", "No living thing carries light in its tubes, like R.")],
  ["Blood carries water and so do the tubes of plants."], lambda: table(["Substance", "In human blood?", "In plant tubes?"], [["P", "Yes", "Yes"], ["Q", "Yes", "No"], ["R", "No", "No"]], [90, 150, 150], "Substances carried")),
]
WST = [
 ("ws-411", I, 4, RD, "Ice in a beaker is heated steadily. The graph shows the temperature. Which part of the graph shows the ice melting?", "B",
  [W("A", "wrong-reading", "In A the ice is getting warmer but has not started to melt."), W("C", "wrong-reading", "In C the melting is over and the water is getting hotter."), W("D", "wrong-reading", "D is the flat part where the water boils.")],
  ["The first flat part, at 0 " + D + ", is the ice melting."], CV2),
 ("ws-412", I, 4, RD, "Ice in a beaker is heated steadily and its temperature is recorded as shown. Which part of the graph shows the water boiling?", "D",
  [W("B", "wrong-reading", "B is at 0 " + D + ", where ice melts."), W("C", "wrong-reading", "In C the temperature is still rising, so the water has not started to boil."), W("A", "wrong-reading", "In A the ice is still warming up, below its melting point.")],
  ["The second flat part, at 100 " + D + ", is boiling."], CV2),
 ("ws-413", I, 4, RD, "Ice in a beaker is heated steadily and its temperature is recorded as shown. In which state is the water during part C?", "Liquid water only",
  [W("Ice and liquid water", "wrong-reading", "That is part B, while the ice is melting."), W("Liquid water and water vapour", "wrong-reading", "That is part D, while the water boils."), W("Ice only", "wrong-reading", "The ice has all melted by the end of part B.")],
  ["All the ice has melted and the water has not started to boil."], CV2),
 ("ws-414", I, 4, RD, "Ice in a beaker is heated steadily and its temperature is recorded as shown. Why does the temperature stay at 0 " + D + " in part B although the heater is still on?", "The heat gained is used to change ice into water",
  [W("The heater stops giving out heat for a while", "wrong-idea", "The heater is still on."), W("The ice loses heat as fast as it gains heat", "wrong-idea", "The ice is gaining heat all the time."), W("The thermometer cannot read above 0 " + D, "wrong-idea", "The same thermometer reads higher later.")],
  ["Heat is used up in changing the state, so the temperature does not rise until all the ice has melted."], CV2),
 ("ws-415", I, 3, RD, "Ice in a beaker is heated steadily and its temperature is recorded as shown. What is the boiling point of the water?", "100 " + D,
  [W("0 " + D, "wrong-reading", "0 " + D + " is where the first flat part is, which is melting."), W("50 " + D, "wrong-reading", "50 " + D + " is only a reading on the way up in part C."), W("20 " + D, "wrong-reading", "20 is a time in minutes, not a temperature.")],
  ["The temperature stays at 100 " + D + " in the second flat part."], CV2),
 ("ws-501", C, 4, RD, "Ice is heated in a beaker and its temperature is recorded as shown. In which parts does the water gain heat but its temperature stay the same?", "B and D",
  [W("A and C", "wrong-reading", "The temperature rises in these parts."), W("B and C", "wrong-reading", "The temperature rises in part C."), W("A and D", "wrong-reading", "The temperature rises in part A.")],
  ["The flat parts, B and D, are where the heat changes the state."], CV2),
 ("ws-502", C, 4, RD, "Ice is heated in a beaker and its temperature is recorded as shown. In which state is the water at 3 minutes?", "Ice and liquid water",
  [W("Ice only", "wrong-reading", "The ice has started to melt after 2 minutes."), W("Liquid water only", "wrong-reading", "The ice does not finish melting until 6 minutes."), W("Liquid water and water vapour", "wrong-reading", "The water does not boil until about 12 minutes.")],
  ["At 3 minutes the graph is in the flat part B at 0 " + D + ", so ice and liquid water are both there."], CV2),
 ("ws-503", C, 4, RD, "Ice is heated in a beaker and its temperature is recorded as shown. What can be seen in the beaker at 15 minutes?", "Bubbles rising through water that is still there",
  [W("Only ice cubes still floating in cold water", "wrong-reading", "The ice melted by 6 minutes."), W("Only clear gas, with no liquid water left", "wrong-reading", "The water has not all boiled away yet."), W("Water with no bubbles, which is still getting hotter", "wrong-reading", "Water at 100 " + D + " is boiling, so it has bubbles.")],
  ["At 15 minutes the water is boiling at 100 " + D + ", so there are bubbles and liquid is left."], CV2),
]
WCY = [
 ("wc-523", C, 1, "sci-pat-water-cycle", "Look at the picture of the water cycle. At which letter do drops of liquid water reach the ground?", "S",
  [W("P", "wrong-stage", "P is water rising as a gas."), W("Q", "wrong-stage", "Q is the cloud, whose droplets are too light to fall."), W("R", "wrong-stage", "R is the river, where water is already on the land.")],
  ["Rain falls as liquid drops, at S."], lambda: cycle({"ev": "P", "co": "Q", "pr": "S", "ru": "R"}, "The water cycle")),
]
EVAP = [
 ("ev-416", I, 1, RD, "Four dishes held 100 ml of water at first and have the same width. They stood in four places with the same wind and the same moisture in the air, and the places differed only in how hot they were. The bar chart shows the water left after 3 hours. Which dish was probably in the hottest place?", "S",
  [W("P", "read-wrong-way", "P has the most water left, so it was probably the coolest."), W("Q", "partial", "Q lost some water, but S lost more."), W("R", "partial", "R lost some water, but S lost more.")],
  ["S lost the most water (85 ml), so it evaporated fastest."], lambda: graph(["P", "Q", "R", "S"], [("left", [92, 70, 45, 15])], 100, "Dish", "Water left (ml)", "Water in each dish after 3 hours", ystep=20, W=340, H=240, bars=True)),
]
CVR = [
 ("cv-313", B, 1, "sci-pat-circuit-variables", "The bulbs in circuits A and B are the same. How does the brightness of the bulb in A compare with a bulb in B?", "They are equally bright",
  [W("The bulb in A is brighter", "wrong-idea", "In a parallel circuit each bulb has its own path to the battery."), W("The bulb in B is brighter", "wrong-idea", "Each path has the same current as in A."), W("The bulbs in B do not light", "wrong-idea", "Each path in B is a complete loop with the battery, so both bulbs light.")],
  ["In B each bulb has its own path, so it is as bright as the bulb in A."], two(lambda c: cs(2, 1, c), lambda c: cp(2, c))),
]
STEPS = [(SAG, "sci-air-gases.json", AIR), (SRC, "sci-resp-circ.json", RESP), (SWS, "sci-water-states.json", WST), (SWC, "sci-water-cycle.json", WCY), (SEV, "sci-water-evap.json", EVAP), (SCV, "sci-circuit-vars.json", CVR)]

if __name__ == "__main__":
    for sub, fn, rows in STEPS:
        old = [k for k in RETIRED if k.split("-")[0] == rows[0][0].split("-")[0]]
        remove(sub, fn, set(old))
        print(fn, "added", add(sub, fn, rows), "shipped", ship(sub, fn, "sci-fill-step0c-2026-11-20", "review fix: one defensible answer, figure neutral or drawn to match the stem; checked by render"))
        lint(sub, fn, rows[0][0].split("-")[0] + "-")
