"""PSLE-style items for sci-systems-resp-circ-parts (file sci-resp-circ.json), all tiers.

Scope: nose, windpipe, lungs; heart, blood, blood vessels; fish gills; plants take in oxygen all day (respiration);
blood carries digested food and oxygen to the cells and carbon dioxide away; the heart pumps blood to all parts of the body.
No alveoli, no named heart chambers or vessels, no blood cell detail.
"""
from fillkit import add, table, graph, lint
import figs_resp as R

SUB, FILE = "sci-systems-resp-circ-parts", "sci-resp-circ.json"
RC, RD = "sci-pat-resp-circulatory", "sci-pat-read-data"
B, I, C = "basic", "intermediate", "competent"
P = []
def q(*a): P.append(a)
def W(t, tag, why): return (t, tag, why)
def tb(h, r, w, c): return lambda: table(h, r, w, c)
def rs(n, p, l, h): return lambda: R.resp_system(n, p, l, h)
def fs(g, f, t, e): return lambda: R.fish(g, f, t, e)
def lt(ans, names, others=None):
    """Four lettered options P-S: wrong ones teach what that letter shows."""
    ls = [x for x in "PQRS" if x != ans]
    return [W(x, "wrong-part", f"{x} shows the {names[x]}, not the part asked about.") for x in ls]

# ---------------- basic ----------------
q("rc-001", B, 1, RC, "Which organ pumps blood to all parts of the human body?", "The heart",
  [W("The lungs", "wrong-organ", "The lungs take oxygen from the air into the blood."), W("The windpipe", "wrong-organ", "The windpipe carries air to the lungs."), W("The nose", "wrong-organ", "Air enters the body through the nose.")],
  ["The heart pumps blood to all parts of the body."], None)
q("rc-002", B, 1, RC, "Which part of the respiratory system carries air from the nose to the lungs?", "The windpipe",
  [W("The heart", "wrong-system", "The heart is part of the circulatory system and pumps blood."), W("A blood vessel", "wrong-system", "Blood vessels carry blood, not air."), W("The food pipe", "wrong-system", "The food pipe belongs to the digestive system.")],
  ["Air passes along the windpipe on its way to the lungs."], None)
q("rc-003", B, 1, RC, "What is the main job of the lungs?", "To take oxygen from the air into the blood",
  [W("To pump blood to the whole body", "heart-job", "Pumping blood is the job of the heart."), W("To break food down into tiny pieces for the body", "digestive-job", "Breaking down food is done by the digestive system."), W("To carry digested food to the cells", "blood-job", "Blood carries digested food to the cells.")],
  ["Oxygen from the air passes into the blood in the lungs."], None)
q("rc-004", B, 1, RC, "Which part of the body carries blood to all other parts of the body?", "Blood vessels",
  [W("The stomach and gut", "wrong-organ", "The stomach is part of the digestive system."), W("The windpipe", "wrong-organ", "The windpipe carries air, not blood."), W("The nose", "wrong-organ", "The nose lets air into the body.")],
  ["Blood moves round the body inside blood vessels."], None)
q("rc-005", B, 1, RC, "The diagram shows some parts inside a person. Which letter shows the lungs?", "R",
  lt("R", {"P": "nose", "Q": "windpipe", "S": "heart"}), ["The two large organs filling the chest, on each side of the windpipe, are the lungs."], rs("P", "Q", "R", "S"))
q("rc-006", B, 1, RC, "The diagram shows some parts inside a person. Which letter shows the windpipe?", "R",
  lt("R", {"P": "lungs", "Q": "heart", "S": "nose"}), ["The windpipe is the tube that leads down from the nose to the lungs."], rs("S", "R", "P", "Q"))
q("rc-007", B, 1, RC, "The diagram shows some parts inside a person. Which letter shows the part that pumps blood?", "P",
  lt("P", {"Q": "nose", "R": "lungs", "S": "windpipe"}), ["The heart pumps blood. It sits between the lungs."], rs("Q", "S", "R", "P"))
q("rc-008", B, 1, RC, "What is the job of the blood vessels?", "To carry blood to and from different parts of the body",
  [W("To pump blood round the whole body", "heart-job", "The heart pumps the blood. Vessels only carry it."), W("To let air pass in and out of the lungs when we breathe", "windpipe-job", "Air travels through the windpipe, not blood vessels."), W("To break down food into digested food", "digestive-job", "This happens in the digestive system.")],
  ["Blood vessels are tubes that carry blood."], None)
q("rc-009", B, 1, RC, "Which of the following does blood carry to the cells?", "Oxygen and digested food",
  [W("Oxygen and waste left after digestion", "undigested", "Undigested food stays in the gut and leaves as waste."), W("Carbon dioxide and digested food", "wrong-gas", "Carbon dioxide is carried away from the cells."), W("Carbon dioxide and waste from the gut", "both-wrong", "Neither is carried to the cells.")],
  ["Blood brings oxygen and digested food to the cells."], None)
q("rc-010", B, 2, RC, "Which part of the body do humans use to take in oxygen from the air?", "The lungs",
  [W("The heart", "wrong-organ", "The heart pumps blood."), W("The stomach", "wrong-organ", "The stomach helps to digest food."), W("The skin", "wrong-organ", "Humans do not take in oxygen through the skin.")],
  ["Humans take in oxygen from the air with their lungs."], None)
q("rc-011", B, 2, RC, "Which part of its body does a fish use to take in oxygen from the water?", "Its gills",
  [W("Its lungs", "fish-lungs", "Fish do not have lungs for breathing in water."), W("Its fins", "wrong-part", "Fins help the fish to move."), W("Its scales", "wrong-part", "Scales cover and protect the body.")],
  ["Fish take in oxygen that is dissolved in water through their gills."], None)
q("rc-012", B, 2, RC, "The diagram shows a fish. Which letter shows the part that takes in oxygen from the water?", "R",
  lt("R", {"P": "fin", "Q": "tail", "S": "eye"}), ["The gills are just behind the head. Oxygen dissolved in the water passes into the blood there."], fs("R", "P", "Q", "S"))
q("rc-013", B, 2, RC, "Which gas is more in the air a person breathes out than in the air the person breathes in?", "Carbon dioxide",
  [W("Oxygen", "reversed", "There is less oxygen in the air breathed out."), W("Nitrogen", "wrong-gas", "Nitrogen is not used by the body, so it hardly changes."), W("Carbon monoxide", "wrong-gas", "Air we breathe out has almost no carbon monoxide.")],
  ["Cells make carbon dioxide, which is breathed out."], None)
q("rc-014", B, 2, RC, "Which statement about plants and humans is correct?", "Both take in oxygen and give out carbon dioxide",
  [W("Only humans need to take in oxygen", "plants-no-oxygen", "Plants also use oxygen for respiration."), W("Plants take in carbon dioxide only and never take in oxygen", "plants-no-oxygen", "Plants take in oxygen all day and night."), W("Only plants give out carbon dioxide", "one-sided", "Humans give out carbon dioxide too.")],
  ["Plants and humans both take in oxygen and give out carbon dioxide."], None)
q("rc-015", B, 2, RC, "The table compares the air a boy breathes in with the air he breathes out. Which gas is X?", "Carbon dioxide",
  [W("Oxygen", "swapped", "Oxygen is the gas that is less in the air breathed out."), W("Nitrogen", "wrong-gas", "Nitrogen hardly changes."), W("Carbon monoxide", "wrong-gas", "Air has almost no carbon monoxide.")],
  ["Gas X is more in the air breathed out, so it is carbon dioxide."], tb(["Gas", "Breathed in", "Breathed out"], [["X", "Very little", "More"], ["Y", "A lot", "Less"]], [70, 120, 120], "Gases in the air"))
q("rc-016", B, 3, RC, "How is water carried from the roots to the leaves of a plant?", "Through tubes in the stem",
  [W("Through blood vessels in the stem", "plant-blood", "Plants do not have blood."), W("By a heart in the roots", "plant-heart", "Plants do not have a heart."), W("Through the air spaces around the roots", "wrong-route", "Water travels in tubes, not through air spaces.")],
  ["Plants have tubes that carry water."], None)
q("rc-017", B, 3, RC, "What carries digested food to all parts of the human body?", "Blood",
  [W("Air", "wrong-carrier", "Air carries oxygen into the lungs only."), W("Saliva", "wrong-carrier", "Saliva stays in the mouth."), W("Urine", "wrong-carrier", "Urine is waste, not a carrier of food.")],
  ["The blood carries digested food round the body."], None)
q("rc-018", B, 3, RC, "Which statement about carrying substances in plants and humans is correct?", "Plants use tubes and humans use blood vessels",
  [W("Plants use blood vessels and humans use tubes", "swapped", "Plants have tubes. Humans have blood vessels."), W("Both plants and humans use blood vessels", "plant-blood", "Plants do not have blood vessels."), W("Only humans carry substances around the body", "wrong-idea", "Plants also carry water and food in tubes.")],
  ["Plants carry water and food in tubes, humans carry substances in blood vessels."], None)
q("rc-019", B, 3, RC, "Which gas does blood carry away from the cells?", "Carbon dioxide",
  [W("Oxygen", "reversed", "Oxygen is carried to the cells."), W("Nitrogen", "wrong-gas", "Cells do not make nitrogen."), W("Carbon monoxide", "wrong-gas", "Cells do not make carbon monoxide.")],
  ["Blood carries carbon dioxide from the cells to the lungs."], None)
q("rc-020", B, 3, RC, "The diagram shows blood moving round the body. Which letter shows blood going from the heart to the body?", "C",
  [W("A", "wrong-arrow", "A shows blood going from the heart to the lungs."), W("B", "wrong-arrow", "B shows blood going from the lungs to the heart."), W("D", "wrong-arrow", "D shows blood coming back from the body to the heart.")],
  ["Arrow C leaves the heart and goes to the body."], lambda: R.circ_block())
q("rc-021", B, 4, RC, "Which two systems work together to bring oxygen to the cells of the body?", "The respiratory system and the circulatory system",
  [W("The digestive system and the respiratory system", "wrong-system", "The digestive system deals with food, not oxygen."), W("The digestive system and the circulatory system together", "wrong-system", "These two move food, not oxygen."), W("The digestive system only", "wrong-system", "The digestive system takes in no oxygen.")],
  ["The lungs take in oxygen and the blood carries it to the cells."], None)
q("rc-022", B, 4, RC, "Which system breaks food down into digested food that the blood can carry?", "The digestive system",
  [W("The respiratory system", "wrong-system", "This system takes in oxygen."), W("The circulatory system", "wrong-system", "This system carries digested food but does not make it."), W("The skeleton", "wrong-system", "The skeleton supports the body.")],
  ["Food is broken down by the digestive system."], None)
q("rc-023", B, 4, RC, "Why do the cells of the body need digested food and oxygen?", "To release energy for the body to work",
  [W("To get rid of the carbon dioxide they make quickly", "reversed", "Carbon dioxide is a waste gas made by cells."), W("To make the blood vessels longer", "wrong-idea", "Cells do not use them for that."), W("To stop the heart from beating", "wrong-idea", "The heart must keep beating.")],
  ["Cells use digested food and oxygen to release energy."], None)
q("rc-024", B, 4, RC, "Which substance is made in the cells when they use digested food and oxygen to release energy?", "Carbon dioxide",
  [W("Oxygen", "wrong-gas", "Oxygen is used up, not made."), W("Digested food", "wrong-substance", "Digested food is used up."), W("Undigested food", "wrong-substance", "Undigested food never reaches the cells.")],
  ["Cells give out carbon dioxide when they release energy."], None)
q("rc-025", B, 4, RC, "After a meal, digested food reaches the rest of the body. Where does it go first after leaving the digestive system?", "Into the blood",
  [W("Into the lungs", "wrong-place", "The lungs deal with air."), W("Into the windpipe", "wrong-place", "The windpipe carries air."), W("Out through the nose", "wrong-place", "Only air leaves by the nose.")],
  ["Digested food enters the blood, which carries it to the cells."], None)

# ---------------- intermediate ----------------
q("rc-101", I, 1, RC, "Which letter shows the part where oxygen from the air passes into the blood?", "S",
  lt("S", {"P": "windpipe", "Q": "heart", "R": "nose"}), ["Oxygen passes into the blood in the lungs."], rs("R", "P", "S", "Q"))
q("rc-102", I, 1, RC, "Which of the following shows the path taken by air when a person breathes in through the nose?", "Nose, windpipe, lungs",
  [W("Nose, lungs, windpipe", "wrong-order", "Air passes along the windpipe before it reaches the lungs."), W("Windpipe, nose, lungs", "wrong-order", "Air enters through the nose first."), W("Lungs, windpipe, nose", "reversed", "This is the path of air being breathed out.")],
  ["Air goes from the nose, down the windpipe, to the lungs."], None)
q("rc-103", I, 1, RC, "Which pair of part and job is correct?", "Heart: pumps blood to all parts of the body",
  [W("Lungs: pump blood to all parts of the body", "swapped", "Lungs take in oxygen. They do not pump blood."), W("Windpipe: passes oxygen into the blood", "wrong-job", "The windpipe only carries air to the lungs."), W("Blood vessels: pump blood back to the heart", "wrong-job", "Blood vessels carry blood but do not pump it.")],
  ["The heart is the pump of the circulatory system."], None)
q("rc-104", I, 1, RC, "Which of the following is not carried by the blood?", "Air from the nose",
  [W("Oxygen", "carried", "Blood carries oxygen to the cells."), W("Digested food from the gut", "carried", "Blood carries digested food to the cells."), W("Carbon dioxide", "carried", "Blood carries carbon dioxide away from the cells.")],
  ["Air travels in the windpipe. The blood carries only oxygen, digested food and carbon dioxide from the list."], None)
q("rc-105", I, 1, RC, "Which letter shows the part that carries air directly to the lungs?", "Q",
  lt("Q", {"P": "lungs", "R": "heart", "S": "nose"}), ["The windpipe leads straight into the lungs."], rs("S", "Q", "P", "R"))
q("rc-106", I, 1, RC, "Mei puts her hand on her chest and breathes in deeply. What does she feel?", "Her chest rises as her lungs fill with air",
  [W("Her chest falls as her lungs fill with air", "reversed", "The chest goes down when air is breathed out."), W("Her chest stays the same as air goes to her heart", "wrong-idea", "Air goes to the lungs, not the heart."), W("Her chest falls as her lungs fill with blood", "wrong-idea", "Lungs fill with air, not blood.")],
  ["The chest rises when we breathe in and falls when we breathe out."], None)
q("rc-107", I, 1, RC, "Which statement about the heart is correct?", "It pumps blood through blood vessels to all parts of the body",
  [W("It takes in oxygen from the air and gives out carbon dioxide", "lung-job", "That is the job of the lungs."), W("It breaks down food into digested food for the blood", "digestive-job", "That is done in the digestive system."), W("It carries air along the windpipe to the nose", "windpipe-job", "The heart has nothing to do with the air passage.")],
  ["The heart pumps blood round the body."], None)
q("rc-108", I, 2, RC, "The diagram shows a fish. Which letter shows where oxygen dissolved in the water passes into the fish's blood?", "S",
  lt("S", {"P": "tail", "Q": "fin", "R": "eye"}), ["Oxygen enters a fish's blood at its gills."], fs("S", "Q", "P", "R"))
q("rc-109", I, 2, RC, "Which of the following describes how a fish gets oxygen?", "Water passes over its gills, where oxygen enters the blood",
  [W("Air goes in its nose and down to its lungs", "fish-lungs", "Fish have gills, not lungs."), W("Oxygen enters its blood through its scales", "wrong-part", "Scales do not take in oxygen."), W("It swallows air bubbles that fill up its stomach and gut", "wrong-part", "Air in the stomach does not reach the blood.")],
  ["A fish takes in dissolved oxygen through its gills."], None)
q("rc-110", I, 2, RC, "The table shows how three living things take in oxygen. Which of the following correctly names X and Y?", "X: gills, Y: lungs",
  [W("X: lungs, Y: gills", "swapped", "Fish use gills and humans use lungs."), W("X: fins, Y: windpipe", "wrong-part", "Neither part takes oxygen into the blood."), W("X: gills, Y: heart", "wrong-part", "The heart pumps blood.")],
  ["Fish use gills and humans use lungs."], tb(["Living thing", "Part for taking in oxygen"], [["Fish", "X"], ["Human", "Y"], ["Plant", "Leaves and roots"]], [110, 200], "How living things take in oxygen"))
q("rc-111", I, 2, RC, "Which of the following is the same for plants, fish and humans?", "They all take in oxygen and give out carbon dioxide",
  [W("They all use lungs to take in oxygen", "lung-all", "Fish have gills and plants have neither."), W("They all take in oxygen only from the air around them", "air-only", "Fish take in oxygen dissolved in water."), W("They all give out carbon dioxide only at night", "night-only", "Living things give out carbon dioxide all the time.")],
  ["All living things take in oxygen and give out carbon dioxide for respiration."], None)
q("rc-112", I, 2, RD, "The table shows three gases in the air a girl breathes in and out. Which gas is most likely to be Y?", "Carbon dioxide",
  [W("Oxygen", "swapped", "Oxygen goes down, not up, after breathing."), W("Nitrogen", "wrong-gas", "Nitrogen stays about the same."), W("Carbon monoxide", "wrong-gas", "Air has almost no carbon monoxide.")],
  ["Y rises from 0.04% to 4%, so it is carbon dioxide."], tb(["Gas", "Breathed in (%)", "Breathed out (%)"], [["X", "21", "16"], ["Y", "0.04", "4"], ["Z", "78", "78"]], [60, 120, 120], "Gases in air"))
q("rc-113", I, 2, RC, "A potted plant is kept in a dark room for a whole day. Does it take in oxygen?", "Yes, because plants respire all the time",
  [W("No, it takes in oxygen only when there is light", "light-only", "Plants respire all the time."), W("No, in the dark it takes in carbon dioxide instead", "wrong-gas", "Taking in carbon dioxide does not replace oxygen use."), W("Yes, but only through its roots", "roots-only", "Leaves take in oxygen too.")],
  ["Plants respire all day, so they always take in oxygen."], None)
q("rc-114", I, 2, RC, "A fish is taken out of the water and put on a dry table. It soon dies. Which is the best reason?", "Its gills cannot take in enough oxygen from the air",
  [W("Its lungs fill up with air and cannot work", "fish-lungs", "Fish do not have lungs."), W("Its blood vessels stop carrying food", "wrong-reason", "Lack of oxygen is the cause."), W("It cannot give out carbon dioxide through its nose", "wrong-reason", "Fish do not breathe through a nose.")],
  ["Gills are made to take oxygen from water, not from air."], None)
q("rc-115", I, 3, RC, "Which of the following is the same for the transport systems of plants and humans?", "Both have tubes that carry substances around the body",
  [W("Both have a heart that pumps the liquid", "plant-heart", "Plants do not have a heart."), W("Both carry blood to every part", "plant-blood", "Plants do not have blood."), W("Both carry oxygen and carbon dioxide in their tubes all the time", "wrong-idea", "Plant tubes carry water and food.")],
  ["Plants have tubes and humans have blood vessels."], None)
q("rc-116", I, 3, RC, "Which two substances are carried in the tubes of a plant?", "Water and food",
  [W("Oxygen and carbon dioxide", "wrong-substance", "These are not carried in the plant's tubes."), W("Water and oxygen", "wrong-substance", "Oxygen is not carried in them."), W("Blood and water", "plant-blood", "Plants have no blood.")],
  ["The tubes of a plant carry water and food."], None)
q("rc-117", I, 3, RC, "The table shows what blood carries. Which of the following correctly names P, Q and R?", "P: oxygen, Q: carbon dioxide, R: digested food",
  [W("P: carbon dioxide, Q: oxygen, R: digested food", "swapped", "Oxygen goes from the lungs to the cells."), W("P: digested food, Q: carbon dioxide, R: oxygen", "wrong-source", "Digested food comes from the small intestine."), W("P: oxygen, Q: digested food, R: carbon dioxide", "wrong-source", "Carbon dioxide goes from the cells to the lungs.")],
  ["Blood carries oxygen from the lungs, carbon dioxide to the lungs and digested food from the small intestine."],
  tb(["Substance", "From", "To"], [["P", "Lungs", "Cells"], ["Q", "Cells", "Lungs"], ["R", "Small intestine", "Cells"]], [90, 120, 70], "Substances carried by blood"))
q("rc-118", I, 3, RC, "Which statement about moving substances in plants and humans is correct?", "In humans, the heart pumps blood; plants do not have a heart",
  [W("In plants, a heart in the stem pushes water up", "plant-heart", "Plants do not have a heart."), W("In humans, substances move without blood vessels", "wrong-idea", "Humans need blood vessels."), W("In both, the tubes carry only oxygen and carbon dioxide around the body", "wrong-idea", "Plant tubes carry water and food.")],
  ["Humans have a heart. Plants do not."], None)
q("rc-119", I, 3, RC, "Which statement about blood is correct?", "It carries digested food to the cells and carbon dioxide away from them",
  [W("It carries oxygen away from the cells and carbon dioxide to them", "reversed", "Oxygen goes to the cells. Carbon dioxide goes away."), W("It carries undigested food to the cells and oxygen away from them", "undigested", "Cells get digested food, not undigested food."), W("It carries air from the lungs to the cells and takes food away from the cells again", "wrong-idea", "Blood carries oxygen, not air.")],
  ["Blood brings digested food and oxygen to the cells and takes carbon dioxide away."], None)
q("rc-120", I, 4, RC, "After a meal, digested food passes into the blood vessels. Which system moves it to the muscles?", "The circulatory system",
  [W("The respiratory system", "wrong-system", "This system carries air."), W("The digestive system", "wrong-system", "It makes digested food but does not move it around the body."), W("The muscular system", "wrong-system", "Muscles do not carry food round the body.")],
  ["The circulatory system carries digested food round the body."], None)
q("rc-121", I, 4, RC, "A person cannot breathe for several minutes and becomes very ill. Which is the best reason?", "Oxygen cannot reach the cells, so they cannot release energy",
  [W("Digested food cannot enter the blood vessels in the small intestine", "wrong-reason", "Food enters blood in the small intestine."), W("The heart cannot pump blood without any carbon dioxide", "wrong-reason", "Carbon dioxide is not needed for pumping."), W("The cells cannot make oxygen for themselves when needed", "wrong-reason", "Cells never make oxygen.")],
  ["Without breathing, no oxygen reaches the cells."], None)
q("rc-122", I, 4, RC, "In the diagram, which letter shows blood that has just taken in oxygen?", "B",
  [W("A", "wrong-arrow", "A shows blood going from the heart to the lungs, so it has not yet taken in oxygen."), W("C", "wrong-arrow", "C shows blood going from the heart to the body, so it already carries oxygen but did not just take it in."), W("D", "wrong-arrow", "D shows blood coming back from the body.")],
  ["Blood takes in oxygen in the lungs, so arrow B from the lungs to the heart shows it."], lambda: R.circ_block())
q("rc-123", I, 4, RD, "The graph shows Dev's pulse rate. He ran fast from 2 to 6 minutes. Which statement best explains his pulse rate at 6 minutes?", "His heart beat faster to bring more to his muscles",
  [W("His lungs pumped his blood faster", "lung-job", "The heart pumps the blood."), W("His heart beat faster to bring in more air from outside", "wrong-job", "Air comes in through the nose."), W("His blood vessels became shorter", "wrong-idea", "Vessels do not change length.")],
  ["The heart beat faster so the blood could bring more oxygen and digested food to the muscles."],
  lambda: graph(["0", "2", "4", "6", "8", "10"], [("Pulse", [70, 70, 125, 150, 100, 72])], 160, "Time (minutes)", "Pulse (beats per min)", "Dev's pulse rate", ystep=40))
q("rc-124", I, 4, RC, "Where do oxygen and digested food enter the blood?", "Oxygen at the lungs and digested food at the small intestine",
  [W("Oxygen at the small intestine and digested food at the lungs", "swapped", "These are the wrong way round."), W("Both at the lungs", "wrong-place", "Food enters blood in the small intestine."), W("Both at the heart", "wrong-place", "The heart only pumps blood.")],
  ["Oxygen enters at the lungs. Digested food enters at the small intestine."], None)
q("rc-125", I, 4, RC, "What happens to the carbon dioxide made by the cells of a leg muscle?", "Blood carries it to the lungs, where it is breathed out",
  [W("Blood carries it to the heart, where it is stored", "wrong-place", "The heart does not store gases."), W("Blood carries it to the stomach, where it is broken down and digested", "wrong-place", "Gases are not digested."), W("It stays in the muscle cells until they are used up", "wrong-idea", "The body must get rid of it.")],
  ["Carbon dioxide goes in the blood to the lungs and out through the nose."], None)

# ---------------- competent ----------------
q("rc-201", C, 1, RC, "In the diagram, solid lines show oxygen-rich blood. Which two arrows carry blood that contains the most oxygen?", "B and C",
  [W("A and B", "mixed", "A carries oxygen-poor blood."), W("A and D", "poor-only", "Both carry oxygen-poor blood."), W("C and D", "mixed", "D carries oxygen-poor blood.")],
  ["Solid lines B and C carry oxygen-rich blood; A and D are dashed (oxygen-poor)."], lambda: R.circ_block(legend=True))
q("rc-202", C, 1, RC, "Which statement about parts P, Q, R and S is correct?", "Q carries air from P to R, where oxygen enters the blood",
  [W("R carries air from Q to P, where oxygen leaves the blood", "reversed", "Air goes from the nose down to the lungs."), W("S pumps air along Q to R, where carbon dioxide is made", "heart-job", "The heart pumps blood, not air."), W("P carries air to S, where digested food enters the blood", "wrong-job", "The heart takes in no food.")],
  ["P is the nose, Q the windpipe, R the lungs and S the heart."], rs("P", "Q", "R", "S"))
q("rc-203", C, 1, RC, "A piece of food blocks Sam's windpipe. Which is the most direct result?", "Air cannot reach the lungs, so oxygen cannot enter the blood",
  [W("Blood cannot reach the lungs, so the heart stops", "wrong-idea", "The blood vessels are not blocked."), W("Digested food cannot reach the cells, so energy is lost", "wrong-idea", "Food is not carried in the windpipe."), W("Carbon dioxide cannot leave the cells, so oxygen is made", "wrong-idea", "Cells never make oxygen.")],
  ["The windpipe is the air passage to the lungs."], None)
q("rc-204", C, 1, RC, "Which of the following correctly compares the heart and the lungs?", "The heart pumps blood round the body; the lungs take oxygen into the blood",
  [W("The heart takes in air; the lungs pump blood to the cells", "swapped", "The jobs are the wrong way round."), W("The heart carries oxygen; the lungs carry digested food", "wrong-job", "Both statements are wrong."), W("The heart gives out carbon dioxide; the lungs make blood", "wrong-job", "The heart gives out no gas.")],
  ["The heart pumps. The lungs pass oxygen into the blood."], None)
q("rc-205", C, 1, RC, "What would most likely happen if a person's heart stopped pumping?", "Blood would stop moving, so cells would get no oxygen or digested food",
  [W("Air would stop entering the nose, so the lungs would fill with blood", "wrong-idea", "Air would still enter, but it would not be carried."), W("Digested food would stop forming, so the cells would make oxygen", "wrong-idea", "Cells never make oxygen."), W("Blood vessels would carry air instead, so the cells would keep working", "wrong-idea", "Blood vessels never carry air.")],
  ["The heart pumps blood. If it stops, oxygen and digested food cannot reach the cells."], None)
q("rc-206", C, 2, RC, "The diagram shows a fish. Which letter shows the part used to take in oxygen, and what else passes through it?", "Q; carbon dioxide also leaves the blood through it",
  [W("P; carbon dioxide also leaves the blood through it", "wrong-part", "P is the eye."), W("Q; only oxygen can pass through it", "one-gas", "Carbon dioxide leaves through the gills as well."), W("R; carbon dioxide also leaves the blood through it", "wrong-part", "R is the tail.")],
  ["Q is the gills: oxygen enters and carbon dioxide leaves."], fs("Q", "S", "R", "P"))
q("rc-207", C, 2, RC, "The table compares a fish and a human. What are P and Q?", "P: water, Q: air",
  [W("P: air, Q: air", "fish-air", "A fish takes in oxygen dissolved in water."), W("P: water, Q: water", "human-water", "Humans take in oxygen from the air."), W("P: air, Q: water", "swapped", "These are the wrong way round.")],
  ["A fish gets oxygen dissolved in water. A human gets oxygen from the air."], tb(["Living thing", "Takes in oxygen from", "Gives out"], [["Fish", "P", "Carbon dioxide"], ["Human", "Q", "Carbon dioxide"]], [100, 170, 130], "Taking in oxygen"))
q("rc-208", C, 2, RC, "A farmer puts an air pump in a crowded fish tank. The fish are less likely to die. Why?", "More air dissolves in the water, so the gills can take in more oxygen",
  [W("Bubbles carry food into the gills of the fish", "wrong-idea", "Bubbles do not carry food."), W("Bubbles let the fish breathe air through their noses", "fish-nose", "Fish breathe through gills."), W("Bubbles push carbon dioxide into the fish's lungs", "fish-lungs", "Fish have no lungs.")],
  ["More oxygen dissolves in the water, and the gills take it in."], None)
q("rc-209", C, 2, RD, "The graph shows the oxygen left in the water of a tank after one hour with different numbers of fish. Which conclusion is correct?", "The more fish there are, the more oxygen they use up",
  [W("More fish make more oxygen for the water", "reversed", "Fish use up oxygen."), W("Fish stop taking in oxygen when there are more than six", "wrong-idea", "Every fish keeps taking in oxygen."), W("The oxygen in the water does not depend on the fish", "no-trend", "The line falls as fish increase.")],
  ["The line falls, so more fish use up more of the oxygen."],
  lambda: graph(["2", "4", "6", "8", "10"], [("Oxygen", [7.0, 6.2, 5.4, 4.6, 3.8])], 8, "Number of fish in tank", "Oxygen left (mg per litre)", "Oxygen left in the water", ystep=2))
q("rc-210", C, 2, RC, "Which of the following describes how a plant gets the oxygen it uses?", "It takes in oxygen from the air around its leaves and roots",
  [W("It takes in oxygen only through its roots and uses its leaves for carbon dioxide", "roots-only", "Leaves take in oxygen too."), W("It takes in oxygen only at night through its leaves", "night-only", "Plants respire all day and night."), W("It gets oxygen from the water in the tubes of its stem", "wrong-idea", "The stem tubes carry water and food.")],
  ["Plants take in oxygen from the air, through leaves and roots."], None)
q("rc-211", C, 2, RC, "The table shows whether three living things have lungs or gills. All three take in oxygen. Which of the following names P, Q and R?", "P: human, Q: fish, R: plant",
  [W("P: fish, Q: human, R: plant", "swapped", "Humans have lungs. Fish have gills."), W("P: human, Q: plant, R: fish", "wrong-name", "A plant has neither, so it is R."), W("P: plant, Q: fish, R: human", "wrong-name", "A human has lungs, so it is P.")],
  ["Humans have lungs, fish have gills and plants have neither."], tb(["Living thing", "Lungs", "Gills"], [["P", "Yes", "No"], ["Q", "No", "Yes"], ["R", "No", "No"]], [100, 90, 90], "Lungs and gills"))
q("rc-212", C, 3, RC, "The table compares how substances are carried in plants and humans. Which substance is most likely Q?", "Digested food",
  [W("Oxygen", "human-only", "Oxygen is carried only by blood."), W("Carbon dioxide", "human-only", "Carbon dioxide is carried only by blood."), W("Light energy", "wrong-idea", "Light is not carried by either.")],
  ["Digested food is carried by blood in humans and food in the tubes of plants."], tb(["Substance", "Carried in humans?", "Carried in plants?"], [["P", "No", "Yes"], ["Q", "Yes", "Yes"], ["R", "Yes", "No"]], [90, 160, 160], "Substances carried"))
q("rc-213", C, 3, RC, "Blood vessels carry substances in the human body. Which part of a plant does a similar job?", "The tubes in the roots, stem and leaves",
  [W("The roots, which pump water up to the leaves", "plant-heart", "Roots do not pump."), W("The flowers, which carry food to the roots", "wrong-part", "Flowers do not carry food."), W("The air spaces in the leaves, which carry blood", "plant-blood", "Plants do not have blood.")],
  ["The tubes of a plant carry water and food, like blood vessels."], None)
q("rc-214", C, 3, RC, "Why must blood vessels reach every part of the human body?", "So that every cell gets oxygen and digested food and loses carbon dioxide",
  [W("So that the heart can take in air from every part", "wrong-idea", "The heart takes in no air."), W("So that digested food is broken down in every vessel", "wrong-idea", "Food is digested in the digestive system."), W("So that blood can leave the body with the carbon dioxide", "wrong-idea", "Blood stays inside; carbon dioxide leaves in the breath.")],
  ["Every cell needs a supply of oxygen and digested food and a way to lose carbon dioxide."], None)
q("rc-215", C, 3, RD, "The bar graph shows the oxygen in blood at three places. Which statement explains the difference between the first two bars?", "Oxygen passes into the blood as it flows through the lungs",
  [W("Oxygen passes out of the blood as it flows through the lungs", "reversed", "Blood gains oxygen in the lungs."), W("Digested food in the lungs adds oxygen to the blood", "wrong-idea", "Oxygen comes from the air."), W("The heart makes oxygen and adds it to the blood", "heart-job", "The heart only pumps blood.")],
  ["The blood leaving the lungs has more oxygen because it took it in from the air."],
  lambda: graph(["Going to lungs", "Leaving lungs", "Leaving muscles"], [("Oxygen", [4, 8, 3])], 10, "Place in the body", "Oxygen in blood (units)", "Oxygen in the blood", ystep=2, bars=True, W=380))
q("rc-216", C, 3, RC, "Which of the following is carried by blood vessels in humans but not by the tubes in plants?", "Oxygen and carbon dioxide",
  [W("Water and food made by the plant", "plant-only", "These are carried in plants."), W("Water only", "wrong-idea", "Water is carried in plants."), W("Nothing, as both carry the same things", "wrong-idea", "Blood carries oxygen and carbon dioxide.")],
  ["Blood carries gases; plant tubes carry water and food."], None)
q("rc-217", C, 3, RC, "The table compares two transport systems. Which of the following gives X and Y?", "X: water and food; Y: oxygen, digested food and carbon dioxide",
  [W("X: oxygen and carbon dioxide; Y: water and food", "swapped", "These are the wrong way round."), W("X: water and oxygen; Y: digested food only", "wrong-idea", "Both lists are wrong."), W("X: food only; Y: oxygen and digested food", "wrong-idea", "Plants carry water too; blood also carries carbon dioxide.")],
  ["Plant tubes carry water and food; blood carries oxygen, digested food and carbon dioxide."],
  tb(["Transport system", "Substances carried"], [["Tubes in a plant", "X"], ["Blood vessels in a human", "Y"]], [200, 140], "Two transport systems"))
q("rc-218", C, 4, RC, "In the diagram, solid lines show oxygen-rich blood. Which letter shows blood that carries carbon dioxide from the body cells to the heart?", "D",
  [W("A", "wrong-arrow", "A shows blood going from the heart to the lungs."), W("B", "wrong-arrow", "B shows blood going from the lungs to the heart."), W("C", "wrong-arrow", "C shows blood going from the heart to the body.")],
  ["Blood returning from the body cells carries carbon dioxide, so it is arrow D."], lambda: R.circ_block(("A", "B", "C", "D"), legend=True))
q("rc-219", C, 4, RC, "The diagram shows how substances move in the body. Which of the following names the substance moved by P, Q and R?", "P: digested food, Q: oxygen, R: carbon dioxide",
  [W("P: oxygen, Q: digested food, R: carbon dioxide", "swapped", "Digested food comes from the small intestine."), W("P: digested food, Q: carbon dioxide, R: oxygen", "reversed", "Oxygen enters the blood at the lungs."), W("P: carbon dioxide, Q: oxygen, R: digested food", "wrong-order", "The lungs do not add digested food.")],
  ["Digested food enters the blood at the small intestine, oxygen enters at the lungs and carbon dioxide leaves at the lungs."], lambda: R.integ_block())
q("rc-220", C, 4, RD, "The table shows a girl's pulse rate and breathing rate. What is the best reason for the change after she runs?", "Her muscle cells need more oxygen, so more is taken in and carried faster",
  [W("Her muscle cells need less oxygen, so less carbon dioxide is made", "reversed", "Running makes cells use more oxygen."), W("Her lungs make more blood, so her heart beats faster", "lung-job", "Lungs do not make blood."), W("Her blood vessels need more air, so she breathes harder", "wrong-idea", "Blood vessels carry blood, not air.")],
  ["Faster breathing takes in more oxygen and a faster pulse carries it to the muscles."], tb(["Measurement", "At rest", "After running"], [["Pulse (beats per min)", "75", "130"], ["Breaths per min", "16", "32"]], [150, 90, 110], "Before and after running"))
q("rc-221", C, 4, RD, "The graph shows a boy's breathing rate. He ran from 2 to 6 minutes. At which time were his muscle cells most likely releasing energy fastest?", "At 6 minutes",
  [W("At 0 minutes", "rest", "He was resting."), W("At 2 minutes", "start", "He had just started to run."), W("At 10 minutes", "rest", "He had stopped and recovered.")],
  ["His breathing rate is highest at 6 minutes, so his cells use the most oxygen then."],
  lambda: graph(["0", "2", "4", "6", "8", "10"], [("Breathing", [16, 18, 30, 40, 28, 18])], 50, "Time (minutes)", "Breaths per minute", "A boy's breathing rate", ystep=10))
q("rc-222", C, 4, RC, "Why do people need to eat and to breathe in order to run?", "The blood brings digested food and oxygen to muscle cells, which use them to release energy",
  [W("The blood brings food and air to the muscle cells, which store them as energy", "wrong-idea", "Cells use oxygen and digested food, not air, to release energy."), W("The lungs bring digested food and oxygen to muscle cells, which make energy", "lung-job", "Blood carries them; the lungs do not."), W("The blood takes carbon dioxide to the muscles, which release it as energy", "wrong-idea", "Carbon dioxide is waste.")],
  ["Digested food and oxygen reach the cells in the blood and are used to release energy."], None)
q("rc-223", C, 4, RC, "A patient's small intestine cannot pass digested food into the blood. What is the most direct effect?", "Less of the food the body can use reaches the cells",
  [W("The cells receive less oxygen from the lungs", "wrong-effect", "The lungs are not affected."), W("The blood cannot carry carbon dioxide to the lungs", "wrong-effect", "Carbon dioxide is still carried."), W("The lungs cannot take in air through the windpipe", "wrong-effect", "The air passage is not affected.")],
  ["Digested food reaches the cells only after it enters the blood."], None)
q("rc-224", C, 4, RC, "The blood vessels in a man's leg are partly blocked, so less blood reaches the leg. What is most likely to happen to the cells of his leg?", "They get less oxygen and digested food, and carbon dioxide builds up",
  [W("They get more oxygen, but less carbon dioxide builds up", "wrong-effect", "Less blood brings less oxygen."), W("They get the same oxygen, but less digested food", "wrong-effect", "Both are carried by the blood."), W("They get less carbon dioxide, so they release more energy", "wrong-effect", "With less supply they release less energy.")],
  ["Less blood means less oxygen and food in and less carbon dioxide taken away."], None)
q("rc-225", C, 4, RC, "Which statement links the digestive, respiratory and circulatory systems?", "Digested food and oxygen are taken in by two systems and carried to the cells by the third",
  [W("Digested food and oxygen are both taken in by the lungs and carried by the heart alone", "wrong-idea", "Food does not enter at the lungs."), W("Oxygen is made by the digestive system and carried by the lungs to the cells", "wrong-idea", "No system makes oxygen."), W("Carbon dioxide is taken in by the lungs and carried to the cells as food", "wrong-idea", "Carbon dioxide is a waste gas.")],
  ["The digestive and respiratory systems take in food and oxygen; the circulatory system carries them to the cells."], None)

if __name__ == '__main__':
    print(add(SUB, FILE, P)); lint(SUB, FILE)
