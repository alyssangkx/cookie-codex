# PSLE Science MCQ question patterns from school papers

Generated 2026-11-18 from `scripts/quiz/science/patterns.json`. Source of truth for the data is that JSON; this page summarises it. Phase S1 of the Science school (papers, catalogue and roadmap). The build plan is in [`../roadmap-science.md`](../roadmap-science.md).

## Summary

- 214 free P5/P6 Science papers from sgtestpaper.com were downloaded and analysed (117 P6, 97 P5; 22 schools; 2022 to 2025). P6 prelims: 58. Other exams: Prelim 58, WA2 48, WA1 46, EOY 33, SA1 14, WA3 9, and a few others. The download used the same URL pattern as the English run and a 2 second delay between requests. Of 249 PDF requests, 35 returned 404 (33 of them 2022 P5, which the source does not host at the guessed address, and 2 2025 P5). Nothing was blocked and no workaround was needed. 2026 papers were left out by design.
- All 214 PDFs were scans (no text layer) and were read by OCR (tesseract `eng`, 200 dpi, page-segmentation mode 4). Every paper produced text, but quality is moderate: option numbers are sometimes misread, diagram labels are lost, and tables come out as loose text.
- The parser found 3,339 four-option MCQ items in 200 papers (the rest are WA papers whose OCR lost the option markers). 140 papers gave 10 or more items and are counted as holding a Booklet A section. Booklet A prints "questions 1 to 28" (28 MCQs, 2 marks each, 56 marks) on 86 of the 119 papers where a range could be read; in those, the parser recovered about 22 of the 28 items on average (79%), so the per-paper counts below are scaled to a 28-item paper where noted. WA papers print shorter ranges (10 to 20).
- The syllabus survey (`docs/syllabus/science.md`) states 30 MCQs; the school papers print 28 (56 marks), so plan on 28 per Booklet A. Booklet A is 56 of the 100 marks; the rest is Booklet B.
- 3,245 of 3,339 items (97%) were assigned to one of 33 question types by a weighted keyword classifier (stem first, options second). A spot check of about 45 sampled items found roughly two thirds filed where a teacher would file them; the rest are neighbours (for example a volume measurement filed under materials). Treat frequencies as indicative, not exact (unverified).
- Booklet B (structured, 40 marks) is not multiple choice and is out of scope. Practical and performance tasks are school-based and are not in the PSLE paper.

## Question types

Frequencies are the number of distinct papers with at least one item of that type. "Items per 28" scales the parsed items to a 28-question paper. "Figure" is the figure kind the type needs under the owner policy (see below): `svg` is code-drawn black and white with exact labels; `lineart` is AI-generated black and white with no text in the image and HTML labels; `mixed` has both; `none` needs no figure.

| Id | Type | Topic (sub-topic) | Level | Papers (P6 / P5) | Items | Items per 28 | Figure | Cue share |
|---|---|---|---|---|---|---|---|---|
| `sci-pat-circuit-basics` | Electric circuits: complete and open circuits, symbols, switches | Electrical System (`systems-circuit`) | intermediate | 123 (79 / 44) | 256 | 2.4 | svg | 90% |
| `sci-pat-states-of-matter` | Properties of solids, liquids and gases (mass, volume, shape) | Cycles in Matter and Water (`cycles-matter-states`) | intermediate | 129 (80 / 49) | 227 | 2.1 | svg | 81% |
| `sci-pat-change-of-state` | Changes of state: melting, freezing, boiling, condensation, evaporation | Cycles in Matter and Water (`cycles-water-states`) | competent | 127 (73 / 54) | 201 | 1.9 | svg | 79% |
| `sci-pat-plant-parts-function` | Plant parts and their functions (root, stem, leaf, stomata) | Plant System (`systems-plant-parts-fn`) | intermediate | 117 (69 / 48) | 194 | 1.8 | lineart | 80% |
| `sci-pat-heat-temperature` | Heat gain and loss, temperature and thermometers | Energy Forms and Uses (`energy-heat-temp`) | competent | 113 (60 / 53) | 181 | 1.7 | svg | 78% |
| `sci-pat-plant-reproduction` | Plant reproduction: flower parts, pollination, fertilisation, dispersal, germination | Cycles in Plants and Animals (`cycles-repro-plants`) | competent | 106 (62 / 44) | 164 | 1.5 | lineart | 79% |
| `sci-pat-classify-groups` | Classify organisms into broad groups (plants, animals, fungi, bacteria) | Diversity of Living and Non-Living Things (`diversity-living-classification`) | intermediate | 99 (66 / 33) | 162 | 1.5 | mixed | 64% |
| `sci-pat-forces-effects` | Forces and their effects (push, pull, contact and non-contact forces) | Interaction of Forces (`interactions-forces-effects`) | intermediate | 87 (78 / 9) | 142 | 1.3 | svg | 70% |
| `sci-pat-resp-circulatory` | Respiratory and circulatory systems (lungs, heart, blood) | Human System (`systems-resp-circ-parts`) | competent | 98 (59 / 39) | 141 | 1.3 | lineart | 76% |
| `sci-pat-energy-conversion` | Energy forms and conversion | Energy Conversion (`energy-conv-forms`) | intermediate | 75 (75 / 0) | 134 | 1.3 | svg | 72% |
| `sci-pat-material-properties` | Properties and uses of materials | Diversity of Materials (`diversity-materials-properties`) | intermediate | 97 (65 / 32) | 128 | 1.2 | svg | 88% |
| `sci-pat-magnet-properties` | Magnets: poles, magnetic materials, attraction and repulsion | Interaction of Forces (`interactions-magnet-props`) | intermediate | 93 (67 / 26) | 124 | 1.2 | svg | 90% |
| `sci-pat-cell-continuity` | Cell parts, functions and continuity of kind | Cycles in Plants and Animals (`cycles-repro-cell`) | intermediate | 91 (53 / 38) | 123 | 1.2 | lineart | 74% |
| `sci-pat-digestive-system` | Human digestive system: organs and digestion | Human System (`systems-digestive-parts`) | intermediate | 88 (53 / 35) | 116 | 1.1 | lineart | 72% |
| `sci-pat-read-data` | Interpret a graph or results table and draw a conclusion | Scientific inquiry skills assessed in PSLE (`inquiry-analyse`) | competent | 80 (54 / 26) | 104 | 1.0 | svg | 100% |
| `sci-pat-food-chain-web` | Food chains and food webs: energy flow and population effects | Interactions within the Environment (`interactions-env-survival`) | competent | 69 (68 / 1) | 100 | 0.9 | svg | 90% |
| `sci-pat-life-cycle-stages` | Life cycle stages and comparison (insect, amphibian, plant) | Cycles in Plants and Animals (`cycles-life-cycles-compare`) | competent | 76 (49 / 27) | 93 | 0.9 | lineart | 85% |
| `sci-pat-light-shadows` | Light: sources, seeing, reflection and shadows | Energy Forms and Uses (`energy-light-seeing`) | intermediate | 78 (54 / 24) | 93 | 0.9 | svg | 76% |
| `sci-pat-human-reproduction` | Human reproduction: gametes, fertilisation and development | Cycles in Plants and Animals (`cycles-repro-humans`) | intermediate | 76 (38 / 38) | 88 | 0.8 | lineart | 76% |
| `sci-pat-population-community` | Organism, population, community and habitat | Interactions within the Environment (`interactions-env-community`) | intermediate | 58 (56 / 2) | 83 | 0.8 | none | 78% |
| `sci-pat-photosynthesis` | Photosynthesis: requirements, products and experiment set-ups | Energy Forms and Uses (`energy-photo-requirements`) | competent | 49 (36 / 13) | 62 | 0.6 | svg | 73% |
| `sci-pat-fair-test-design` | Fair test and experiment design: variables and set-up choice | Scientific inquiry skills assessed in PSLE (`inquiry-evaluate`) | competent | 51 (32 / 19) | 60 | 0.6 | svg | 83% |
| `sci-pat-human-impact` | Human impact on the environment and conservation | Interactions within the Environment (`interactions-env-adapt`) | intermediate | 35 (30 / 5) | 41 | 0.4 | none | 49% |
| `sci-pat-friction-spring-weight` | Friction, elastic spring force and weight: investigations | Interaction of Forces (`interactions-forces-investigate`) | competent | 36 (36 / 0) | 40 | 0.4 | svg | 95% |
| `sci-pat-plant-transport` | Plant transport system: water and food transport | Plant System (`systems-plant-transport-parts`) | competent | 34 (17 / 17) | 36 | 0.3 | mixed | 89% |
| `sci-pat-adaptations` | Adaptations of plants and animals (structural and behavioural) | Interactions within the Environment (`interactions-env-adapt`) | intermediate | 30 (30 / 0) | 36 | 0.3 | lineart | 58% |
| `sci-pat-living-characteristics` | Characteristics of living and non-living things | Diversity of Living and Non-Living Things (`diversity-living-characteristics`) | basic | 29 (18 / 11) | 33 | 0.3 | none | 70% |
| `sci-pat-water-cycle` | Water cycle and water conservation | Cycles in Matter and Water (`cycles-water-cycle`) | intermediate | 22 (8 / 14) | 22 | 0.2 | svg | 68% |
| `sci-pat-heat-effects-conductors` | Effects of heat: expansion and contraction, and heat conductors | Energy Forms and Uses (`energy-heat-effects`) | competent | 21 (12 / 9) | 22 | 0.2 | svg | 73% |
| `sci-pat-circuit-variables` | Current strength, conductors and insulators | Electrical System (`systems-circuit-vars`) | competent | 11 (6 / 5) | 13 | 0.1 | svg | 100% |
| `sci-pat-gases-in-air` | Gases in air and tests for gases | Human System (`systems-air-gases`) | intermediate | 12 (8 / 4) | 12 | 0.1 | svg | 50% |
| `sci-pat-respiration-sun` | Respiration and the Sun as the source of energy | Energy Forms and Uses (`energy-photo-respiration`) | basic | 9 (9 / 0) | 9 | 0.1 | none | 67% |
| `sci-pat-evaporation-rate` | Rate of evaporation: factors and fair set-ups | Cycles in Matter and Water (`cycles-water-evaporation`) | competent | 5 (2 / 3) | 5 | 0.0 | svg | 80% |

The items-per-28 column is the average number of items of that type in one paper. Types at the bottom (evaporation rate, gases in air, circuit variables, respiration and the Sun) are rare in school papers: they are mostly tested inside other types (a set-up question on heat, or a graph item) rather than alone.

## Figures: which questions need one

A figure cue is a stem containing a phrase such as "the diagram below", "the graph shows", "study the set-up", "food web", "circuit", "as shown", "the table", "part X" or a labelled-arrow reference. OCR loses the drawings themselves, so the share is a floor for diagram items but also counts tables printed as text, which this project renders as HTML or svg tables. It is an estimate.

| Topic | Items classified | With a figure cue | Share |
|---|---|---|---|
| Diversity of Living and Non-Living Things (General characteristics and classification) | 195 | 127 | 65% |
| Diversity of Materials | 128 | 112 | 88% |
| Cycles in Plants and Animals (Life Cycles) | 93 | 79 | 85% |
| Cycles in Plants and Animals (Reproduction) | 375 | 287 | 77% |
| Cycles in Matter and Water (Matter) | 227 | 185 | 81% |
| Cycles in Matter and Water (Water) | 228 | 177 | 78% |
| Plant System (Plant parts and functions) | 194 | 156 | 80% |
| Human System (Digestive system) | 116 | 83 | 72% |
| Human System (Respiratory and circulatory systems) | 153 | 113 | 74% |
| Plant System (Respiratory and circulatory systems) | 36 | 32 | 89% |
| Electrical System | 269 | 244 | 91% |
| Interaction of Forces (Magnets) | 124 | 112 | 90% |
| Interaction of Forces (Frictional force, gravitational force, elastic spring force) | 182 | 137 | 75% |
| Interactions within the Environment | 260 | 196 | 75% |
| Energy Forms and Uses (Light) | 93 | 71 | 76% |
| Energy Forms and Uses (Heat) | 203 | 158 | 78% |
| Energy Forms and Uses (Photosynthesis) | 71 | 51 | 72% |
| Energy Conversion | 134 | 97 | 72% |
| Scientific inquiry skills assessed in PSLE (AO II b) | 164 | 154 | 94% |
| **All topics** | **3245** | **2571** | **79%** |

Reading the table: roughly three in four Science MCQs carry a figure or a table. The types that are mostly words are living and non-living characteristics, respiration and the Sun, human impact, and population and community. The most figure-bound are electric circuits, magnets, graph and table reading, and fair-test set-ups.

### Figure kinds by type

| Type | Kind | svg figures needed | lineart figures needed | Share of figure items that are lineart |
|---|---|---|---|---|
| `living-characteristics` | none | - | - | 0% |
| `classify-groups` | mixed | classification chart or key (flowchart); feature table | organism pictures | 30% |
| `material-properties` | svg | results table; object with labelled parts | - | 0% |
| `life-cycle-stages` | lineart | cycle arrow diagram with letters | stage drawings for each animal | 85% |
| `cell-continuity` | lineart | feature table | plant and animal cell drawings | 70% |
| `plant-reproduction` | lineart | germination set-up; feature table | flower, fruit and seed drawings with lettered parts | 70% |
| `human-reproduction` | lineart | - | male and female reproductive system drawings | 100% |
| `states-of-matter` | svg | experimental set-up (syringe, tank, balloon, measuring cylinder); property table | - | 0% |
| `change-of-state` | svg | state-change arrow diagram; melting and boiling point table; heating or cooling curve; condensation set-up (cold cup, lid) | - | 0% |
| `evaporation-rate` | svg | set-up comparison (dishes, cloths, temperature, fan) | - | 0% |
| `water-cycle` | svg | water cycle diagram | - | 0% |
| `plant-parts-function` | lineart | stomata and covered-leaf set-up | whole plant and leaf drawings | 70% |
| `digestive-system` | lineart | organ-to-function table | digestive system drawing with lettered organs | 85% |
| `resp-circulatory` | lineart | inhaled and exhaled air table; systems overview flow diagram | lungs and heart with blood paths | 70% |
| `gases-in-air` | svg | jar and candle set-up | - | 0% |
| `plant-transport` | mixed | stained stem and ringed stem set-up | plant with arrow paths | 50% |
| `circuit-basics` | svg | circuit diagram (cells, bulbs, switches, wires); circuit table of bulbs lit or not | - | 0% |
| `circuit-variables` | svg | test circuit with gap; circuit pair comparison | - | 0% |
| `magnet-properties` | svg | bar magnets with poles; discs and rods attraction table; magnetic strength set-up (clips, floating magnet) | - | 0% |
| `forces-effects` | svg | force arrow diagram; ramp and moving object set-up | - | 0% |
| `friction-spring-weight` | svg | spring and load set-up; friction surface comparison; extension graph; force arrow diagram | - | 0% |
| `food-chain-web` | svg | food web with arrows; food chain; population graph | - | 0% |
| `population-community` | none | habitat table | - | 0% |
| `adaptations` | lineart | adaptation matching table | animal feet, beaks and plant parts | 70% |
| `human-impact` | none | - | - | 0% |
| `light-shadows` | svg | source, object and screen ray diagram; periscope ray path; shadow shapes | - | 0% |
| `heat-temperature` | svg | thermometer and objects scene; cooling and warming graph; heat flow arrow diagram | - | 0% |
| `heat-effects-conductors` | svg | lid and jar set-up; heated rod and balloon set-up; conductor comparison table | - | 0% |
| `respiration-sun` | none | - | - | 0% |
| `photosynthesis` | svg | covered-leaf and iodine test set-up; aquatic plant bubble set-up | - | 0% |
| `energy-conversion` | svg | device or track diagram | - | 0% |
| `fair-test-design` | svg | set-up table; apparatus drawing | - | 0% |
| `read-data` | svg | line graph; bar chart; results table | - | 0% |

## Syllabus mapping, skills and distractor traps

### Characteristics of living and non-living things

- Id `sci-pat-living-characteristics`; sub-topic `sci-diversity-living-characteristics`; syllabus outcomes: `sci-diversity-living-characteristics-1`, `sci-diversity-living-characteristics-2`
- Structure: A statement or short list about what living things need or do, or a set of items to sort into living and non-living.
- Skill: Recall what living things need and do; tell living from non-living.
- Figure: none
- Traps: `need-vs-characteristic` (an option swaps what a living thing needs (water, food, air) with what it does (grow, respond, reproduce)); `moves-means-alive` (an option treats movement or growth-like change as proof of life (a car, a flame))

### Classify organisms into broad groups (plants, animals, fungi, bacteria)

- Id `sci-pat-classify-groups`; sub-topic `sci-diversity-living-classification`; syllabus outcomes: `sci-diversity-living-classification-1`, `sci-diversity-living-classification-2`
- Structure: A classification chart, key or table of features (spores, seeds, fur, scales, six legs) with a question on where an organism belongs or which placement is wrong.
- Skill: Place organisms in groups from observable features; read a classification chart or key.
- Figure: mixed
- Traps: `shared-feature-overgeneralised` (an option gives a feature that only some members of the group have); `group-mix-up` (insects, reptiles or amphibians are swapped because they share one feature); `yeast-as-plant` (fungi are filed with plants)

### Properties and uses of materials

- Id `sci-pat-material-properties`; sub-topic `sci-diversity-materials-properties`; syllabus outcomes: `sci-diversity-materials-properties-1`, `sci-diversity-materials-properties-2`
- Structure: An object or a results table (strength, absorbency, flexibility) and a question on which material suits a purpose or which property explains a use.
- Skill: Match a material property to a use; read a results table.
- Figure: svg
- Traps: `property-for-wrong-use` (a real property of the material that is irrelevant to the use named); `table-misread` (the row with the highest or lowest value is read for the wrong property)

### Life cycle stages and comparison (insect, amphibian, plant)

- Id `sci-pat-life-cycle-stages`; sub-topic `sci-cycles-life-cycles-compare`; syllabus outcomes: `sci-cycles-life-cycles-compare-1`, `sci-cycles-life-cycles-compare-2`, `sci-cycles-life-cycles-compare-3`
- Structure: A cycle diagram with stages labelled by letter, or two animals compared, with questions on which stage feeds, moults, flies or looks like the adult.
- Skill: Order and compare life cycle stages; tell complete from incomplete metamorphosis.
- Figure: lineart
- Traps: `complete-vs-incomplete` (pupa and nymph are swapped, so the wrong metamorphosis is assigned); `stage-misplaced` (a behaviour is given to a stage it does not belong to (a pupa eating)); `young-looks-like-adult` (the wrong animal is said to have young that look like the adult)

### Cell parts, functions and continuity of kind

- Id `sci-pat-cell-continuity`; sub-topic `sci-cycles-repro-cell`; syllabus outcomes: `sci-cycles-repro-cell-1`, `sci-cycles-repro-cell-2`
- Structure: A plant or animal cell diagram, a table of which cell parts are present, or an inherited-trait table, with a question on function or presence.
- Skill: Name cell parts and functions; recognise that traits pass from both parents.
- Figure: lineart
- Traps: `plant-animal-part-swap` (cell wall or chloroplast is said to be in animal cells); `part-function-swap` (the functions of nucleus and cytoplasm or cell membrane are swapped); `trait-from-wrong-parent` (an inherited trait count ignores that both parents contribute)

### Plant reproduction: flower parts, pollination, fertilisation, dispersal, germination

- Id `sci-pat-plant-reproduction`; sub-topic `sci-cycles-repro-plants`; syllabus outcomes: `sci-cycles-repro-plants-1`, `sci-cycles-repro-plants-2`, `sci-cycles-repro-plants-3`
- Structure: A flower, fruit or seed diagram with letters, or a table of features of wind- and insect-pollinated flowers, with questions on function, order of events or which flower can form a fruit.
- Skill: Link flower parts to function; sequence pollination, fertilisation, dispersal and germination.
- Figure: lineart
- Traps: `pollination-vs-fertilisation` (pollen landing on the stigma is called fertilisation, or the reverse); `part-function-swap` (the roles of stigma, anther and ovary are exchanged); `wrong-dispersal-agent` (a fruit feature (wing, hook, juicy flesh) is matched to the wrong agent); `germination-needs` (sunlight or soil is listed as a germination need)

### Human reproduction: gametes, fertilisation and development

- Id `sci-pat-human-reproduction`; sub-topic `sci-cycles-repro-humans`; syllabus outcomes: `sci-cycles-repro-humans-1`, `sci-cycles-repro-humans-2`
- Structure: A diagram of the male and female reproductive systems with lettered parts, or a statement about fertilisation and the developing baby.
- Skill: Identify the reproductive organs, gametes and where fertilisation and development happen.
- Figure: lineart
- Traps: `part-function-swap` (the roles of ovary, uterus and testis are swapped); `where-fertilisation` (fertilisation is placed in the uterus rather than the oviduct); `egg-vs-fertilised-egg` (the egg cell and the fertilised egg are confused)

### Properties of solids, liquids and gases (mass, volume, shape)

- Id `sci-pat-states-of-matter`; sub-topic `sci-cycles-matter-states`; syllabus outcomes: `sci-cycles-matter-states-1`, `sci-cycles-matter-states-2`, `sci-cycles-matter-states-3`
- Structure: A set-up with air pumped in or a stone dropped into water, or a table of two properties for several substances, asking what happens to mass and volume.
- Skill: Compare mass, volume and shape of solids, liquids and gases; show that gas takes space and has mass.
- Figure: svg
- Traps: `gas-no-mass` (air is said to have no mass or no definite volume); `volume-vs-mass-change` (mass and volume are swapped when air is added to a closed container); `shape-vs-volume` (a liquid is said to keep its shape)

### Changes of state: melting, freezing, boiling, condensation, evaporation

- Id `sci-pat-change-of-state`; sub-topic `sci-cycles-water-states`; syllabus outcomes: `sci-cycles-water-states-1`, `sci-cycles-water-states-2`, `sci-cycles-water-states-3`, `sci-cycles-water-states-4`
- Structure: A diagram of arrows between ice, water and steam, a melting and boiling point table with a state at one temperature, or a heating or cooling graph.
- Skill: Name the change of state and its heat direction; read melting-point tables and heating curves.
- Figure: svg
- Traps: `process-name-swap` (condensation and evaporation, or melting and freezing, are exchanged); `heat-direction-wrong` (heat loss is attached to a change that needs heat gain); `state-at-temperature` (the state is read against the melting point only, ignoring the boiling point)

### Rate of evaporation: factors and fair set-ups

- Id `sci-pat-evaporation-rate`; sub-topic `sci-cycles-water-evaporation`; syllabus outcomes: `sci-cycles-water-evaporation-1`
- Structure: Several set-ups that differ in surface area, temperature or wind; pick the fair pair or explain which dries faster.
- Skill: Choose a fair set-up for a factor that changes the rate of evaporation.
- Figure: svg
- Traps: `two-variables-changed` (the pair differs in more than one factor); `rate-vs-amount` (a bigger water amount is taken to evaporate faster)

### Water cycle and water conservation

- Id `sci-pat-water-cycle`; sub-topic `sci-cycles-water-cycle`; syllabus outcomes: `sci-cycles-water-cycle-1`, `sci-cycles-water-cycle-2`, `sci-cycles-water-cycle-3`
- Structure: A cycle diagram with lettered stages, or everyday actions to sort into saving and wasting water.
- Skill: Order the stages of the water cycle and link each to a change of state; choose water-saving actions.
- Figure: svg
- Traps: `stage-vs-change` (a stage of the cycle is matched to the wrong change of state); `saving-looks-like-saving` (an action that sounds thrifty uses more water in total)

### Plant parts and their functions (root, stem, leaf, stomata)

- Id `sci-pat-plant-parts-function`; sub-topic `sci-systems-plant-parts-fn`; syllabus outcomes: `sci-systems-plant-parts-fn-1`, `sci-systems-plant-parts-fn-2`
- Structure: A plant with lettered parts, or a set-up in which a part is covered or removed, with questions on function and what would happen.
- Skill: Match a plant part to its function; predict what happens when a part is covered or removed.
- Figure: lineart
- Traps: `part-function-swap` (roots and stem, or leaf and stem, are given each other's functions); `which-part-takes-in` (water is said to enter through the leaf); `stomata-direction` (stomata are said to take in water or to close in the light)

### Human digestive system: organs and digestion

- Id `sci-pat-digestive-system`; sub-topic `sci-systems-digestive-parts`; syllabus outcomes: `sci-systems-digestive-parts-1`
- Structure: A digestive system diagram with lettered organs, or a table matching organ to function, or the order food passes through.
- Skill: Order the digestive organs and state what each does.
- Figure: lineart
- Traps: `organ-function-swap` (the roles of stomach and small intestine, or liver and pancreas, are swapped); `absorption-site` (absorption of digested food is placed in the large intestine); `order-reversed` (two organs are listed in the wrong order)

### Respiratory and circulatory systems (lungs, heart, blood)

- Id `sci-pat-resp-circulatory`; sub-topic `sci-systems-resp-circ-parts`; syllabus outcomes: `sci-systems-resp-circ-parts-1`, `sci-systems-resp-circ-parts-2`, `sci-systems-resp-circ-parts-3`, `sci-systems-resp-circ-parts-4`
- Structure: A diagram of lungs, heart and body with arrows showing oxygen-rich and oxygen-poor blood, or a table comparing inhaled and exhaled air.
- Skill: Trace air and blood through lungs, heart and body; compare inhaled and exhaled air.
- Figure: lineart
- Traps: `oxygen-poor-vs-rich` (the vessel carrying oxygen-rich blood is named as carrying oxygen-poor blood); `organ-function-swap` (the functions of heart and lungs are exchanged); `inhaled-exhaled-swap` (inhaled and exhaled air composition is swapped)

### Gases in air and tests for gases

- Id `sci-pat-gases-in-air`; sub-topic `sci-systems-air-gases`; syllabus outcomes: `sci-systems-air-gases-1`
- Structure: A candle burning in a closed jar, a limewater test or a statement on what air contains.
- Skill: Recall the composition of air and interpret burning and limewater tests.
- Figure: svg
- Traps: `air-is-oxygen` (air is said to be mostly oxygen); `burning-gas-produced` (burning is said to use up carbon dioxide)

### Plant transport system: water and food transport

- Id `sci-pat-plant-transport`; sub-topic `sci-systems-plant-transport-parts`; syllabus outcomes: `sci-systems-plant-transport-parts-1`, `sci-systems-plant-transport-parts-2`
- Structure: A stem stained with coloured water, a ring of bark removed from a stem, or a diagram of arrows for water and food in a plant.
- Skill: Explain how water and food move through a plant from a stained stem or ringed stem.
- Figure: mixed
- Traps: `direction-swap` (water is said to move down and food only up); `tube-mix-up` (water-carrying and food-carrying tubes are exchanged); `ringing-effect` (the part above the ring is said to die first when it is the part below)

### Electric circuits: complete and open circuits, symbols, switches

- Id `sci-pat-circuit-basics`; sub-topic `sci-systems-circuit`; syllabus outcomes: `sci-systems-circuit-1`, `sci-systems-circuit-2`, `sci-systems-circuit-3`
- Structure: Circuit diagrams with cells, bulbs and switches; decide which bulbs light, which circuit is complete, or what a switch controls.
- Skill: Decide which bulbs light or whether a circuit is complete from a diagram.
- Figure: svg
- Traps: `series-vs-parallel` (a bulb in a parallel branch is said to go out when its neighbour fails); `closed-switch-misread` (a bulb is said to light with a switch open); `short-circuit-missed` (a wire that bypasses a bulb is ignored)

### Current strength, conductors and insulators

- Id `sci-pat-circuit-variables`; sub-topic `sci-systems-circuit-vars`; syllabus outcomes: `sci-systems-circuit-vars-1`, `sci-systems-circuit-vars-2`
- Structure: A test circuit with a gap for an object, or two circuits with different numbers of cells or bulbs, asking which bulb is brighter or which material conducts.
- Skill: Predict bulb brightness from cells and bulbs; classify conductors and insulators from a test.
- Figure: svg
- Traps: `more-cells-brighter-mix-up` (adding bulbs is said to brighten them); `metal-equals-conductor` (a metal-looking object is called a conductor without the test result)

### Magnets: poles, magnetic materials, attraction and repulsion

- Id `sci-pat-magnet-properties`; sub-topic `sci-interactions-magnet-props`; syllabus outcomes: `sci-interactions-magnet-props-1`, `sci-interactions-magnet-props-2`, `sci-interactions-magnet-props-3`, `sci-interactions-magnet-props-4`, `sci-interactions-magnet-props-5`
- Structure: Bar magnets with poles marked, or discs and rods tested against a magnet, asking which attract, which repel or which must be a magnet.
- Skill: Predict attraction or repulsion from poles; identify magnets and magnetic materials from tests.
- Figure: svg
- Traps: `like-poles-attract` (like poles are said to attract); `attract-means-magnet` (an object attracted by a magnet is said to be a magnet itself); `only-repel-proves-magnet` (the test for a magnet (repulsion) is confused with attraction)

### Forces and their effects (push, pull, contact and non-contact forces)

- Id `sci-pat-forces-effects`; sub-topic `sci-interactions-forces-effects`; syllabus outcomes: `sci-interactions-forces-effects-1`, `sci-interactions-forces-effects-2`, `sci-interactions-forces-effects-3`
- Structure: A moving object, ramp or hurdle scene, or a list of effects of a force, asking which force acts or what the force does.
- Skill: Identify the force acting and its effect on motion or shape.
- Figure: svg
- Traps: `force-changes-mass` (a force is said to change the mass of an object); `contact-vs-noncontact` (gravity or magnetic force is listed as a contact force); `motion-needs-force` (a constant speed is taken to need a continuing force)

### Friction, elastic spring force and weight: investigations

- Id `sci-pat-friction-spring-weight`; sub-topic `sci-interactions-forces-investigate`; syllabus outcomes: `sci-interactions-forces-investigate-1`, `sci-interactions-forces-investigate-2`, `sci-interactions-forces-investigate-3`
- Structure: A spring with loads, a surface comparison for friction, or a graph of extension against load.
- Skill: Interpret friction, spring-extension and weight investigations.
- Figure: svg
- Traps: `friction-direction` (friction is drawn in the direction of motion); `weight-vs-mass` (weight in newtons is confused with mass in grams); `spring-force-direction` (the elastic spring force is drawn pointing away from the stretched spring)

### Food chains and food webs: energy flow and population effects

- Id `sci-pat-food-chain-web`; sub-topic `sci-interactions-env-survival`; syllabus outcomes: `sci-interactions-env-survival-1`, `sci-interactions-env-survival-2`, `sci-interactions-env-survival-3`, `sci-interactions-env-survival-4`
- Structure: A food web with lettered organisms, with questions on which statement is false, who is a producer or predator, or what happens to populations when one changes.
- Skill: Trace energy flow and predict population changes in a food web.
- Figure: svg
- Traps: `arrow-direction` (the arrow is read as "eats" instead of "energy goes to"); `direct-vs-indirect-effect` (only the first effect on a population is considered); `predator-increase-reflex` (a prey increase is said to follow a predator increase)

### Organism, population, community and habitat

- Id `sci-pat-population-community`; sub-topic `sci-interactions-env-community`; syllabus outcomes: `sci-interactions-env-community-1`, `sci-interactions-env-community-2`
- Structure: A habitat description, a list of organisms or a table of conditions, asking which term applies or what a habitat provides.
- Skill: Distinguish organism, population, community and habitat.
- Figure: none
- Traps: `population-vs-community` (population (one kind) and community (all kinds) are swapped); `habitat-vs-organism` (habitat is taken to mean the animals living in it)

### Adaptations of plants and animals (structural and behavioural)

- Id `sci-pat-adaptations`; sub-topic `sci-interactions-env-adapt`; syllabus outcomes: `sci-interactions-env-adapt-1`, `sci-interactions-env-adapt-2`
- Structure: An animal or plant with a feature described, asking what the adaptation is for or whether it is structural or behavioural.
- Skill: Match an adaptation to its purpose; classify structural and behavioural adaptations.
- Figure: lineart
- Traps: `structural-vs-behavioural` (a body feature is labelled behavioural or the reverse); `adaptation-purpose-swap` (the purpose of the feature is matched to another adaptation)

### Human impact on the environment and conservation

- Id `sci-pat-human-impact`; sub-topic `sci-interactions-env-adapt`; syllabus outcomes: `sci-interactions-env-adapt-1`, `sci-interactions-env-adapt-2`
- Structure: A list of actions, asking which conserve resources or which cause pollution or loss of habitat.
- Skill: Judge the effect of human activity on the environment; choose conservation actions.
- Figure: none
- Traps: `sounds-green-but-not` (an action that sounds green causes more harm overall); `wrong-effect-link` (pollution is linked to the wrong effect on the community)

### Light: sources, seeing, reflection and shadows

- Id `sci-pat-light-shadows`; sub-topic `sci-energy-light-seeing`; syllabus outcomes: `sci-energy-light-seeing-1`, `sci-energy-light-seeing-2`, `sci-energy-light-seeing-3`
- Structure: A light source, object and screen drawn in a row, or a ray path in a periscope, asking what is seen, the shadow shape or the mirror position.
- Skill: Decide what can be seen and how a shadow changes; follow a ray path.
- Figure: svg
- Traps: `shadow-size-direction` (moving the object towards the light is said to shrink the shadow); `reflector-seen-as-source` (a reflecting object is called a light source); `transparent-casts-shadow` (a transparent object is said to cast a full shadow)

### Heat gain and loss, temperature and thermometers

- Id `sci-pat-heat-temperature`; sub-topic `sci-energy-heat-temp`; syllabus outcomes: `sci-energy-heat-temp-1`, `sci-energy-heat-temp-2`, `sci-energy-heat-temp-3`, `sci-energy-heat-temp-4`
- Structure: Two objects at different temperatures, a cooling or warming graph, or a scene such as a jacket or an ice pack, asking the direction of heat flow.
- Skill: Tell heat gain from heat loss; separate temperature from heat; read thermometers and graphs.
- Figure: svg
- Traps: `heat-flows-wrong-way` (cold is said to travel into the warm object); `temperature-vs-heat` (a hotter object is said to contain more heat); `insulator-warms` (a jacket is said to make heat)

### Effects of heat: expansion and contraction, and heat conductors

- Id `sci-pat-heat-effects-conductors`; sub-topic `sci-energy-heat-effects`; syllabus outcomes: `sci-energy-heat-effects-1`, `sci-energy-heat-effects-2`
- Structure: A metal lid, a rod or a ball-and-ring set-up, asking what expands or contracts and why a lid loosens, or which material conducts heat best.
- Skill: Use expansion and contraction to explain observations; compare heat conductors.
- Figure: svg
- Traps: `expands-on-cooling` (a metal is said to expand when cooled); `conductor-vs-insulator` (the best heat conductor is picked from the wrong end of the results)

### Respiration and the Sun as the source of energy

- Id `sci-pat-respiration-sun`; sub-topic `sci-energy-photo-respiration`; syllabus outcomes: `sci-energy-photo-respiration-1`, `sci-energy-photo-respiration-2`, `sci-energy-photo-respiration-3`
- Structure: A statement or short chain on what respiration needs and gives, or how energy in fuel and food came from the Sun.
- Skill: State what respiration needs and gives; trace energy back to the Sun.
- Figure: none
- Traps: `photosynthesis-vs-respiration` (the two processes are swapped); `sun-direct-to-animal` (an animal is said to get energy straight from the Sun)

### Photosynthesis: requirements, products and experiment set-ups

- Id `sci-pat-photosynthesis`; sub-topic `sci-energy-photo-requirements`; syllabus outcomes: `sci-energy-photo-requirements-1`
- Structure: A leaf covered with foil, a plant in the dark or an iodine-tested leaf, asking what the plant needs or makes.
- Skill: Identify what a plant needs and makes; interpret leaf-test set-ups.
- Figure: svg
- Traps: `products-vs-needs` (oxygen is listed as a need and carbon dioxide as a product); `starch-test-misread` (a leaf that stays brown with iodine is read as having starch); `soil-as-food` (plants are said to take in their food from soil)

### Energy forms and conversion

- Id `sci-pat-energy-conversion`; sub-topic `sci-energy-conv-forms`; syllabus outcomes: `sci-energy-conv-forms-1`, `sci-energy-conv-forms-2`, `sci-energy-conv-forms-3`
- Structure: A device (bell, toy car, ball on a track) or a list of energy sources and forms, asking for the order of conversions or which statement is wrong.
- Skill: Name energy forms and trace the conversions in a device.
- Figure: svg
- Traps: `energy-destroyed` (energy is said to be lost or destroyed when an object stops); `form-mislabel` (food energy or fuel is labelled kinetic); `conversion-order-reversed` (the order of conversions is reversed)

### Fair test and experiment design: variables and set-up choice

- Id `sci-pat-fair-test-design`; sub-topic `sci-inquiry-evaluate`; syllabus outcomes: `sci-inquiry-evaluate-1`, `sci-inquiry-predict-hyp-1`, `sci-inquiry-predict-hyp-2`
- Structure: A table of set-ups differing in a few factors, asking which set-ups to compare, which variable to change, keep the same or measure, or the aim of the experiment.
- Skill: Choose which set-ups to compare; name the variable changed, kept the same and measured.
- Figure: svg
- Traps: `two-things-changed` (the pair differs in more than one factor); `measured-vs-changed` (the measured variable and the changed variable are swapped); `aim-too-broad` (the aim claims more than the set-up can show)

### Interpret a graph or results table and draw a conclusion

- Id `sci-pat-read-data`; sub-topic `sci-inquiry-analyse`; syllabus outcomes: `sci-inquiry-analyse-1`, `sci-inquiry-analyse-2`
- Structure: A line graph, bar chart or table of results, asking for a reading, a trend, a prediction or the valid conclusion.
- Skill: Read values and trends from a graph or table; pick the valid conclusion.
- Figure: svg
- Traps: `trend-over-reach` (the conclusion goes beyond the range of the data); `wrong-axis-read` (the value is read from the wrong axis or the wrong row); `correlation-as-cause` (two changes that go together are said to cause each other)

## Format notes (apply to many types)

- **Statement-combination items.** Several statements labelled A to D, with options such as "A and B only". Seen across life science, forces and environment; about one item in five. Build these as a format on top of any type, not as a separate type.
- **Table-completion items.** The options are rows of a table ("Which row is correct?"), common in systems, energy conversion and states of matter. Render as an HTML table.
- **Fair-test items** are a format as well as a type: they appear inside evaporation, plant growth, heat and friction questions, so fair-test practice is also a skill to build into other sub-topics.

## OCR and method limits

- Text came from `tesseract eng` at 200 dpi, page-segmentation mode 4. Diagrams are lost, labels on diagrams are lost, and option numbers like "(3)" are sometimes read as "(8)" or "{A)". The parser recovered about 79% of the printed Booklet A items.
- The classifier is keyword based. Items that mix two topics (a graph about a plant, a set-up about heat in water) are filed under the keyword with the highest weight. Spot-checked precision is about two thirds.
- Counts of types per paper are for items the parser found; the scaled "items per 28" column assumes the lost items look like the found ones.
- Papers stay in the temp folder (`/data/alvin/tmp/cookie-codex/science/papers/`) and are copyright of the schools. This repository holds only type names, counts and paraphrases. No question text is stored.
