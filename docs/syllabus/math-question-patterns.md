# Math question patterns (P5/P6, top Singapore primary schools)

Generated 2026-11-17 from `scripts/quiz/math/patterns.json` (the machine-readable catalogue that drives the quiz generators). This page lists question *types*: what is asked, the solving method and the usual traps. No question text from any paper is stored here. Every example is original wording with new names and numbers.

## Summary

- Papers analysed: **209** (114 P6, 95 P5) from **14** schools, all read from Tesseract OCR text.
- Patterns: **106** (40 basic, 36 intermediate, 30 competent). 29 need a diagram. 1366 question blocks were left unclassified.
- Coverage caveat: OCR is good for question text and noisy for symbols, fractions and diagrams, and some pages failed OCR entirely. Questions were split and assigned by keyword rules with sampled spot-checks, so frequencies (distinct papers per pattern) are lower bounds and some assignments may be wrong.
- Most frequent: `percent-gst-discount-direct` (150), `area-triangle-rectangle-composite` (142), `angles-chained-shapes` (135), `table-bar-graph-reading` (123), `volume-cuboid-water-level` (106).
- Competent-level questions are dominated by angle chasing, circle composites, before/after ratio and fraction changes, and price-difference problems.

## Coverage

Papers per school and level (P5 / P6):

| School | P5 | P6 | Total |
|---|---|---|---|
| ACSJ | 7 | 9 | 16 |
| Ai Tong | 8 | 4 | 12 |
| Catholic High | 4 | 8 | 12 |
| Henry Park | 10 | 6 | 16 |
| MGS | 2 | 9 | 11 |
| Maha Bodhi | 5 | 0 | 5 |
| Maris Stella | 3 | 3 | 6 |
| Nan Hua | 11 | 12 | 23 |
| Nanyang | 11 | 13 | 24 |
| Raffles Girls' | 7 | 12 | 19 |
| Red Swastika | 10 | 9 | 19 |
| Rosyth | 7 | 13 | 20 |
| SCGS | 2 | 7 | 9 |
| Tao Nan | 8 | 9 | 17 |
| **All** | 95 | 114 | 209 |

Question blocks: **6428** readable blocks after dropping cover, instruction and answer-key pages; **5062** classified into a pattern, **1366** unclassified (no rule matched, sub-parts without context, or too garbled). A block can contain more than one question, so these are block counts, not exact question counts.

## Patterns (sorted by topic, then frequency)

| Topic | Pattern | Level | Section | Freq | Diagram |
|---|---|---|---|---|---|
| Algebra | `algebra-expression-from-context` | intermediate | P1-short | 50 | no |
| Algebra | `algebra-simplify-substitute` | basic | P1-MCQ | 43 | no |
| Algebra | `algebra-equation-from-figure` | intermediate | P2-short | 15 | yes |
| Algebra | `algebra-workers-total` | competent | P2-short | 3 | no |
| Angles | `angles-chained-shapes` | competent | P2-short | 135 | yes |
| Angles | `angles-one-step` | basic | P1-MCQ | 98 | yes |
| Angles | `angles-parallel-quadrilaterals` | intermediate | P1-MCQ | 64 | yes |
| Angles | `angles-folded-paper` | competent | P2-short | 41 | yes |
| Area & perimeter of composite figures | `area-triangle-rectangle-composite` | intermediate | P2-short | 142 | yes |
| Area & perimeter of composite figures | `perimeter-area-identical-rectangles` | competent | P2-long | 50 | yes |
| Area & perimeter of composite figures | `area-triangle-height-base` | basic | P1-MCQ | 31 | yes |
| Area & perimeter of composite figures | `perimeter-composite-identical-pieces` | intermediate | P1-MCQ | 29 | yes |
| Average | `average-find-missing` | intermediate | P2-short | 85 | no |
| Average | `average-direct` | basic | P2-short | 27 | no |
| Average | `average-extreme-value` | competent | P2-short | 10 | no |
| Circles | `circle-area-composite-shaded` | competent | P2-short | 81 | yes |
| Circles | `circle-perimeter-composite` | intermediate | P1-MCQ | 72 | yes |
| Circles | `circumference-in-context` | competent | P2-short | 12 | no |
| Data representation | `table-bar-graph-reading` | basic | P1-MCQ | 123 | yes |
| Data representation | `pie-chart-reading` | intermediate | P1-MCQ | 59 | yes |
| Data representation | `graph-find-missing-from-average` | intermediate | P2-short | 58 | yes |
| Data representation | `line-graph-rate-and-time` | intermediate | P1-MCQ | 39 | yes |
| Decimals | `fraction-to-decimal-rounded` | basic | P1-short | 91 | no |
| Decimals | `decimal-operations-direct` | basic | P1-short | 59 | no |
| Decimals | `place-value-decimals` | basic | P1-MCQ | 40 | no |
| Decimals | `decimal-add-subtract` | basic | P1-short | 38 | no |
| Decimals | `decimal-compare-order` | basic | P1-MCQ | 31 | no |
| Fractions | `fraction-successive-parts` | intermediate | P2-short | 104 | no |
| Fractions | `fraction-operations-simplest` | basic | P1-MCQ | 87 | no |
| Fractions | `fraction-share-remainder` | basic | P2-short | 67 | no |
| Fractions | `fraction-compare-order` | basic | P1-MCQ | 57 | no |
| Fractions | `fraction-shaded-figure` | basic | P1-MCQ | 54 | yes |
| Fractions | `fraction-division-share` | basic | P1-short | 49 | no |
| Fractions | `fraction-of-quantity-left` | basic | P1-MCQ | 39 | no |
| Fractions | `fraction-two-groups-sold-remainder` | competent | P2-long | 38 | no |
| Fractions | `fraction-equivalent-improper-mixed` | basic | P1-MCQ | 29 | no |
| Fractions | `fraction-same-share-two-quantities` | competent | P2-long | 27 | no |
| Fractions | `fraction-express-as-fraction-of` | basic | P1-short | 19 | no |
| Fractions | `fraction-divide-by-fraction-pieces` | intermediate | P1-short | 12 | no |
| Fractions | `fraction-equal-use-per-day` | intermediate | P2-short | 11 | no |
| Fractions | `constant-part-new-fraction` | competent | P2-long | 7 | no |
| Fractions | `fraction-part-difference-find-total` | intermediate | P2-short | 7 | no |
| Fractions | `unequal-wholes-same-remainder` | competent | P2-long | 3 | no |
| Geometry | `symmetry-and-construction` | basic | P2-short | 75 | yes |
| Geometry | `direction-turn-compass` | basic | P1-MCQ | 73 | no |
| Geometry | `shapes-classify-2d` | basic | P1-MCQ | 45 | no |
| Geometry | `nets-and-solids` | basic | P1-MCQ | 44 | no |
| Measurement | `order-mixed-units` | basic | P1-MCQ | 60 | no |
| Measurement | `mass-whole-and-part` | intermediate | P2-short | 45 | no |
| Measurement | `measure-add-subtract-story` | basic | P1-short | 37 | no |
| Measurement | `unit-conversion-compound` | basic | P1-short | 19 | no |
| Measurement | `volume-reading-containers` | basic | P1-MCQ | 8 | yes |
| Money | `tariff-charge` | intermediate | P1-MCQ | 94 | no |
| Money | `coins-notes-total-value` | intermediate | P2-short | 40 | no |
| Money | `promo-buy-n-get-free` | intermediate | P1-MCQ | 22 | no |
| Money | `price-two-equations` | competent | P2-long | 22 | no |
| Money | `weekly-saving-cycle` | intermediate | P2-short | 3 | no |
| Patterns | `growing-figure-pattern` | intermediate | P2-short | 96 | yes |
| Patterns | `gap-overlap-counting` | intermediate | P1-MCQ | 37 | yes |
| Patterns | `repeating-pattern-cycle-sum` | intermediate | P1-MCQ | 21 | no |
| Percentage | `percent-gst-discount-direct` | basic | P1-MCQ | 150 | no |
| Percentage | `percent-reverse-find-original` | intermediate | P2-short | 78 | no |
| Percentage | `percent-shaded-figure` | basic | P1-MCQ | 48 | yes |
| Percentage | `interest-deposit` | intermediate | P2-short | 19 | no |
| Percentage | `percent-two-groups-both-change` | competent | P2-long | 18 | no |
| Percentage | `simple-interest-loan` | intermediate | P2-short | 5 | no |
| Rate | `unitary-rate-basic` | basic | P1-MCQ | 72 | no |
| Rate | `speed-catch-up-meet` | competent | P2-long | 22 | no |
| Rate | `tank-fill-drain-net-rate` | competent | P2-long | 21 | yes |
| Rate | `two-machines-rate-work` | competent | P2-long | 12 | no |
| Ratio | `ratio-express-and-equivalent` | basic | P1-MCQ | 94 | no |
| Ratio | `ratio-total-find-part` | intermediate | P2-short | 88 | no |
| Ratio | `ratio-fraction-conversion` | basic | P1-MCQ | 74 | no |
| Ratio | `ratio-triangle-area-shared-height` | intermediate | P2-short | 43 | yes |
| Ratio | `ratio-one-changes-other-constant` | competent | P2-long | 28 | no |
| Ratio | `ratio-transfer-constant-total` | competent | P2-long | 15 | no |
| Ratio | `ratio-difference-find-total` | intermediate | P2-short | 10 | no |
| Ratio | `ratio-one-quantity-constant` | competent | P2-long | 9 | no |
| Ratio | `ratio-same-amount-both-change` | competent | P2-long | 7 | no |
| Ratio | `ratio-three-way-share-remainder` | competent | P2-long | 6 | no |
| Ratio | `square-sides-ratio-area-units` | competent | P2-long | 4 | yes |
| Reasoning (true / false / not possible to tell) | `true-false-not-possible-to-tell` | intermediate | P2-short | 59 | no |
| Speed | `speed-distance-time-basic` | intermediate | P2-short | 22 | no |
| Speed | `speed-two-runners-finish` | competent | P2-long | 5 | no |
| Time | `time-elapsed-clock` | basic | P1-MCQ | 47 | no |
| Volume | `volume-cuboid-water-level` | intermediate | P1-short | 106 | yes |
| Volume | `painted-cubes-and-views` | competent | P2-long | 87 | yes |
| Volume | `volume-count-unit-cubes` | basic | P1-short | 73 | yes |
| Volume | `volume-cube-cuboid-direct` | basic | P1-short | 44 | no |
| Volume | `cubes-packing-scale` | competent | P2-short | 28 | yes |
| Whole numbers | `rounding-estimation` | basic | P1-MCQ | 73 | no |
| Whole numbers | `place-value-read-write` | basic | P1-MCQ | 69 | no |
| Whole numbers | `multiples-factors-direct` | basic | P1-MCQ | 62 | no |
| Whole numbers | `whole-number-four-ops-direct` | basic | P1-short | 59 | no |
| Whole numbers | `transfer-difference-change` | competent | P2-short | 53 | no |
| Whole numbers | `order-of-operations` | basic | P1-MCQ | 53 | no |
| Whole numbers | `whole-number-more-than-total-model` | intermediate | P2-short | 42 | no |
| Whole numbers | `grouping-as-a-set` | intermediate | P2-short | 31 | no |
| Whole numbers | `age-problems` | intermediate | P2-short | 30 | no |
| Whole numbers | `form-numbers-from-digits` | basic | P1-short | 24 | no |
| Whole numbers | `cutting-pieces-no-joining` | intermediate | P2-short | 17 | no |
| Whole numbers | `working-backwards-transfers` | competent | P1-MCQ | 16 | no |
| Whole numbers | `two-quantities-two-prices-difference` | competent | P2-short | 12 | no |
| Whole numbers | `equal-total-two-ways` | competent | P2-short | 10 | no |
| Whole numbers | `number-pattern-grid` | intermediate | P1-MCQ | 10 | yes |
| Whole numbers | `assumption-guess-and-check` | competent | P2-long | 9 | no |

## Ten most frequent competent-level patterns

### 1. angles-chained-shapes (seen in 135 papers, Angles)

**Structure.** Two or three shapes share a side (rhombus + equilateral/isosceles triangle, rectangle + square, circle with centre O); find an angle that needs 3-5 chained steps.

**Method.**
- Label every angle you can find directly on the diagram
- Use equal sides to get equal angles (isosceles, equilateral = 60)
- Move from the shared side to the next shape
- Check angles at a point (360) or on a line (180)
- Verify the answer is reasonable on the picture

**Common mistakes.** `subtracted_instead_of_added`; `supplement_used`; `gave_triangle_angle`

**Example.** ABCD is a rhombus with angle ABC = 70 degrees. CDE is an equilateral triangle on the other side of CD from A. Find angle ADE.

Answer: 130 degrees. Angle ADC = angle ABC = 70 (opposite angles of a rhombus). Angle CDE = 60. A and E are on opposite sides of DC, so angle ADE = 70 + 60 = 130.

### 2. painted-cubes-and-views (seen in 87 papers, Volume)

**Structure.** A solid built from unit cubes is painted; count cubes with 0, 1, 2 or 3 painted faces, or give surface area, top/side/front views, or nets.

**Method.**
- Picture or sketch the solid and its layers
- Corner cubes have 3 faces painted; edge cubes (excluding corners) 2; face centres 1; hidden cubes 0
- Count edge cubes using (edge length - 2) for each edge
- Check the counts add up to the total number of cubes

**Common mistakes.** `counted_corners_only`; `counted_one_face_cubes`; `edges_times_length`

**Example.** A 4 cm by 3 cm by 2 cm cuboid made of 1-cm cubes has all its outside faces painted. It is then taken apart. How many of the 1-cm cubes have exactly 2 faces painted?

Answer: 12. Edges of length 4: 4 edges x (4-2) = 8. Edges of length 3: 4 x 1 = 4. Edges of length 2: 4 x 0 = 0. Total 12 (checked by counting all 24 cubes: 8 + 12 + 4 + 0).

### 3. circle-area-composite-shaded (seen in 81 papers, Circles)

**Structure.** A shaded region lies between squares/triangles and quadrants/semicircles; find its area using a given pi (3.14, 22/7 or calculator).

**Method.**
- Mark which regions are added and which are subtracted
- Find radius from the diameter or side of the figure
- Area of quadrant = 1/4 x pi x r x r; semicircle = 1/2 x pi x r x r
- Combine and round as the question states

**Common mistakes.** `gave_quadrant_only`; `radius_halved`; `used_arc_length`

**Example.** A quadrant of radius 12 cm is drawn inside a square of side 12 cm, with its centre at one corner of the square. Use pi = 3.14. Find the area of the part of the square outside the quadrant.

Answer: 30.96 cm2. Square = 144. Quadrant = 1/4 x 3.14 x 12 x 12 = 113.04. 144 - 113.04 = 30.96.

### 4. transfer-difference-change (seen in 53 papers, Whole numbers)

**Structure.** A has d more than B; after A gives B some, A has d' more (or A has k times B); find how many were given or the totals.

**Method.**
- Note total is constant but the difference changes
- Change in difference = 2 x amount given
- Divide by 2 for the amount given
- If a multiple is given afterwards, use units on the new total

**Common mistakes.** `forgot_to_halve`; `added_instead_of_subtracted`; `gave_final_difference`

**Example.** Pia had 74 more cards than Quin. After Pia gave Quin some cards, she had 18 more cards than Quin. How many cards did Pia give?

Answer: 28. The gap shrank by 74 - 18 = 56. Each card moves the gap by 2, so 56 / 2 = 28.

### 5. perimeter-area-identical-rectangles (seen in 50 papers, Area & perimeter of composite figures)

**Structure.** Identical small rectangles (length = k x width) form a larger figure; the outer perimeter is given; find a side, then the area of the figure or of a part.

**Method.**
- Let the width be 1u and the length k u
- Count how many u make up the outer perimeter (heuristic: units)
- Perimeter / total units = 1 unit
- Find the dimensions, then the area asked

**Common mistakes.** `area_of_one_rectangle`; `treated_as_square`; `halved_area`

**Example.** Six identical rectangles are arranged in 2 rows of 3 to form a bigger rectangle (3 lengths wide, 2 widths tall). Each rectangle's length is 2 times its width. The perimeter of the bigger rectangle is 96 cm. What is its area?

Answer: 432 cm2. Width w: bigger rectangle is 6w by 2w, perimeter 16w = 96, w = 6. Area = 36 x 12 = 432.

### 6. angles-folded-paper (seen in 41 papers, Angles)

**Structure.** A paper strip or rectangle is folded along a line; some angles are given; find angles at the fold or in the folded part.

**Method.**
- A fold is a reflection: the angle before = the angle after on each side of the fold line
- Angles on a straight line add to 180
- Write an equation using the equal angle twice
- Solve and check the other angles

**Common mistakes.** `forgot_to_halve`; `supplement_of_answer`; `gave_given_angle`

**Example.** A strip of paper along line ZAY is folded at A along fold line AB so that AZ lands on AZ' with angle Z'AY = 38 degrees. Find angle ZAB.

Answer: 71 degrees. Angle ZAB = angle Z'AB by the fold. 2 x angle ZAB + 38 = 180, so angle ZAB = 71.

### 7. fraction-two-groups-sold-remainder (seen in 38 papers, Fractions)

**Structure.** A whole is split by a fraction into two kinds; a fraction of one kind and a number of the other are sold; the amount left is given and the original total is asked.

**Method.**
- Write each kind as a fraction of the total
- Work out the fraction of the total left in each kind
- Add the fractions left, take away the fixed number sold, and equate to the amount left
- Solve for the total (unit fraction method)

**Common mistakes.** `gave_total_left_fraction`; `ignored_fixed_number`; `gave_amount_left`

**Example.** A baker made some buns. 2/5 of them were cheese buns and the rest were raisin buns. He sold 3/4 of the cheese buns and 40 raisin buns and had 100 buns left. How many buns did he make?

Answer: 200. Cheese left = 1/4 of 2/5 = 1/10 of the total. Raisin = 3/5 of the total, so raisin left = 3/5 - 40. 1/10 + 3/5 = 7/10, so 7/10 of the total - 40 = 100, 7/10 of the total = 140 and the total = 200.

### 8. cubes-packing-scale (seen in 28 papers, Volume)

**Structure.** Small and large cubes are packed into a box or built into a bigger cube; find numbers of cubes, side lengths or true/false statements about volumes.

**Method.**
- Compare side lengths: a cube twice as long has 8 times the volume
- Find how many small cubes fit along each edge
- The bigger cube's side is the smallest cube that fits the shape
- Count cubes needed minus cubes already there

**Common mistakes.** `gave_total_not_extra`; `used_cube_of_4`; `gave_given_count`

**Example.** Twelve identical small cubes are put together to form a cuboid that is 3 cubes long, 2 wide and 2 high. What is the least number of extra small cubes needed to make a bigger solid cube?

Answer: 15. The smallest cube that contains it is 3 x 3 x 3 = 27 cubes. 27 - 12 = 15.

### 9. ratio-one-changes-other-constant (seen in 28 papers, Ratio)

**Structure.** Two quantities are in ratio a : b; some of one quantity is sold, spent or added while the other stays the same; the new ratio is given and an amount or a total is asked.

**Method.**
- Mark the quantity that does not change and give it the same number of units before and after
- Rescale the two ratios so the unchanged quantity has equal units
- Compare the changing quantity before and after; the unit difference equals the amount removed or added
- Find one unit, then the quantity asked

**Common mistakes.** `answered_first_quantity`; `gave_amount_removed`; `units_not_matched`

**Example.** A box held cookies and brownies in the ratio 7 : 4. After 40 cookies were sold, the ratio of cookies to brownies became 1 : 2. How many brownies were in the box?

Answer: 32. Brownies stay at 4 units. After the sale, cookies : brownies = 1 : 2 = 2 : 4, so cookies = 2 units. Sold = 7 - 2 = 5 units = 40, 1 unit = 8. Brownies = 4 x 8 = 32.

### 10. fraction-same-share-two-quantities (seen in 27 papers, Fractions)

**Structure.** A fraction of one quantity equals a different fraction of another; their ratio is found, then a total or difference is used to find one amount.

**Method.**
- Give the equal parts the same number of units (make both equal to a common multiple of the numerators)
- Read each quantity in units and form the ratio
- Use the total or difference to find one unit
- Multiply to find the amount asked

**Common mistakes.** `answered_other_person`; `used_numerators_as_ratio`; `used_wrong_share`

**Example.** 3/4 of Ravi's savings is equal to 2/3 of Sam's savings. Together they have $255. How much does Sam have?

Answer: $135. Let 3/4 of Ravi = 2/3 of Sam = 12 units. Ravi = 12 / (3/4) = 16 units and Sam = 12 / (2/3) = 18 units, so Ravi : Sam = 8 : 9. 17 units = 255, 1 unit = 15, Sam = 9 x 15 = $135.

## Papers analysed

School, level, exam, year. All hosted on a public free test paper site; every paper was OCR'd.

- ACSJ, P5, SA2, 2022
- ACSJ, P5, EOY, 2024
- ACSJ, P5, WA1, 2024
- ACSJ, P5, WA2, 2024
- ACSJ, P5, EOY, 2025
- ACSJ, P5, WA1, 2025
- ACSJ, P5, WA2, 2025
- ACSJ, P6, Prelim, 2022
- ACSJ, P6, SA1, 2022
- ACSJ, P6, Prelim, 2023
- ACSJ, P6, WA2, 2023
- ACSJ, P6, Prelim, 2024
- ACSJ, P6, WA2, 2024
- ACSJ, P6, Prelim, 2025
- ACSJ, P6, WA1, 2025
- ACSJ, P6, WA2, 2025
- Ai Tong, P5, SA2, 2021
- Ai Tong, P5, EOY, 2022
- Ai Tong, P5, EOY, 2023
- Ai Tong, P5, WA1, 2023
- Ai Tong, P5, WA2, 2023
- Ai Tong, P5, EOY, 2025
- Ai Tong, P5, WA1, 2025
- Ai Tong, P5, WA2, 2025
- Ai Tong, P6, Prelim, 2021
- Ai Tong, P6, SA1, 2021
- Ai Tong, P6, Prelim, 2023
- Ai Tong, P6, Prelim, 2025
- Catholic High, P5, SA2, 2021
- Catholic High, P5, EOY, 2022
- Catholic High, P5, EOY, 2024
- Catholic High, P5, WA2, 2024
- Catholic High, P6, Prelim, 2021
- Catholic High, P6, SA1, 2021
- Catholic High, P6, Prelim, 2022
- Catholic High, P6, SA1, 2022
- Catholic High, P6, Prelim, 2023
- Catholic High, P6, Prelim, 2024
- Catholic High, P6, Prelim, 2025
- Catholic High, P6, WA2, 2025
- Henry Park, P5, SA2, 2021
- Henry Park, P5, EOY, 2023
- Henry Park, P5, WA1, 2023
- Henry Park, P5, WA2, 2023
- Henry Park, P5, EOY, 2024
- Henry Park, P5, WA1, 2024
- Henry Park, P5, WA2, 2024
- Henry Park, P5, EOY, 2025
- Henry Park, P5, WA1, 2025
- Henry Park, P5, WA2, 2025
- Henry Park, P6, Prelim, 2021
- Henry Park, P6, SA1, 2021
- Henry Park, P6, Prelim, 2022
- Henry Park, P6, Prelim, 2024
- Henry Park, P6, WA2, 2024
- Henry Park, P6, Prelim, 2025
- MGS, P5, SA2, 2021
- MGS, P5, EOY, 2022
- MGS, P6, Prelim, 2021
- MGS, P6, SA1, 2021
- MGS, P6, Prelim, 2022
- MGS, P6, SA1, 2022
- MGS, P6, Prelim, 2023
- MGS, P6, Prelim, 2024
- MGS, P6, WA1, 2024
- MGS, P6, WA2, 2024
- MGS, P6, Prelim, 2025
- Maha Bodhi, P5, SA2, 2021
- Maha Bodhi, P5, SA2, 2022
- Maha Bodhi, P5, EOY, 2023
- Maha Bodhi, P5, EOY, 2024
- Maha Bodhi, P5, EOY, 2025
- Maris Stella, P5, EOY, 2023
- Maris Stella, P5, WA1, 2023
- Maris Stella, P5, WA2, 2023
- Maris Stella, P6, CA1, 2022
- Maris Stella, P6, Prelim, 2023
- Maris Stella, P6, Prelim, 2024
- Nan Hua, P5, SA2, 2021
- Nan Hua, P5, EOY, 2022
- Nan Hua, P5, EOY, 2023
- Nan Hua, P5, WA1, 2023
- Nan Hua, P5, WA2, 2023
- Nan Hua, P5, EOY, 2024
- Nan Hua, P5, WA1, 2024
- Nan Hua, P5, WA2, 2024
- Nan Hua, P5, EOY, 2025
- Nan Hua, P5, WA1, 2025
- Nan Hua, P5, WA2, 2025
- Nan Hua, P6, Prelim, 2021
- Nan Hua, P6, SA1, 2021
- Nan Hua, P6, Prelim, 2022
- Nan Hua, P6, SA1, 2022
- Nan Hua, P6, Prelim, 2023
- Nan Hua, P6, WA1, 2023
- Nan Hua, P6, WA2, 2023
- Nan Hua, P6, Prelim, 2024
- Nan Hua, P6, WA1, 2024
- Nan Hua, P6, WA2, 2024
- Nan Hua, P6, Prelim, 2025
- Nan Hua, P6, WA2, 2025
- Nanyang, P5, SA2, 2021
- Nanyang, P5, EOY, 2022
- Nanyang, P5, EOY, 2023
- Nanyang, P5, WA1, 2023
- Nanyang, P5, WA2, 2023
- Nanyang, P5, EOY, 2024
- Nanyang, P5, WA1, 2024
- Nanyang, P5, WA2, 2024
- Nanyang, P5, EOY, 2025
- Nanyang, P5, WA1, 2025
- Nanyang, P5, WA2, 2025
- Nanyang, P6, Prelim, 2021
- Nanyang, P6, SA1, 2021
- Nanyang, P6, Prelim, 2022
- Nanyang, P6, SA1, 2022
- Nanyang, P6, WA1, 2022
- Nanyang, P6, Prelim, 2023
- Nanyang, P6, WA1, 2023
- Nanyang, P6, WA2, 2023
- Nanyang, P6, Prelim, 2024
- Nanyang, P6, SA1, 2024
- Nanyang, P6, WA1, 2024
- Nanyang, P6, Prelim, 2025
- Nanyang, P6, SA1, 2025
- Raffles Girls', P5, SA2, 2021
- Raffles Girls', P5, EOY, 2022
- Raffles Girls', P5, EOY, 2023
- Raffles Girls', P5, WA2, 2023
- Raffles Girls', P5, EOY, 2025
- Raffles Girls', P5, WA1, 2025
- Raffles Girls', P5, WA2, 2025
- Raffles Girls', P6, Prelim, 2021
- Raffles Girls', P6, SA1, 2021
- Raffles Girls', P6, Prelim, 2022
- Raffles Girls', P6, SA1, 2022
- Raffles Girls', P6, Prelim, 2023
- Raffles Girls', P6, WA1, 2023
- Raffles Girls', P6, WA2, 2023
- Raffles Girls', P6, Prelim, 2024
- Raffles Girls', P6, WA1, 2024
- Raffles Girls', P6, Prelim, 2025
- Raffles Girls', P6, WA1, 2025
- Raffles Girls', P6, WA2, 2025
- Red Swastika, P5, SA2, 2021
- Red Swastika, P5, EOY, 2022
- Red Swastika, P5, EOY, 2023
- Red Swastika, P5, WA1, 2023
- Red Swastika, P5, WA2, 2023
- Red Swastika, P5, EOY, 2024
- Red Swastika, P5, WA1, 2024
- Red Swastika, P5, WA2, 2024
- Red Swastika, P5, EOY, 2025
- Red Swastika, P5, WA2, 2025
- Red Swastika, P6, Prelim, 2021
- Red Swastika, P6, SA1, 2021
- Red Swastika, P6, Prelim, 2022
- Red Swastika, P6, SA1, 2022
- Red Swastika, P6, Prelim, 2023
- Red Swastika, P6, Prelim, 2024
- Red Swastika, P6, WA1, 2024
- Red Swastika, P6, WA2, 2024
- Red Swastika, P6, Prelim, 2025
- Rosyth, P5, SA2, 2021
- Rosyth, P5, EOY, 2022
- Rosyth, P5, EOY, 2023
- Rosyth, P5, WA1, 2023
- Rosyth, P5, WA2, 2023
- Rosyth, P5, EOY, 2024
- Rosyth, P5, WA2, 2024
- Rosyth, P6, Prelim, 2021
- Rosyth, P6, SA1, 2021
- Rosyth, P6, Prelim, 2022
- Rosyth, P6, SA1, 2022
- Rosyth, P6, Prelim, 2023
- Rosyth, P6, WA1, 2023
- Rosyth, P6, WA2, 2023
- Rosyth, P6, Prelim, 2024
- Rosyth, P6, WA1, 2024
- Rosyth, P6, WA2, 2024
- Rosyth, P6, Prelim, 2025
- Rosyth, P6, WA1, 2025
- Rosyth, P6, WA2, 2025
- SCGS, P5, SA2, 2021
- SCGS, P5, SA2, 2022
- SCGS, P6, Prelim, 2021
- SCGS, P6, SA1, 2021
- SCGS, P6, Prelim, 2022
- SCGS, P6, Prelim, 2023
- SCGS, P6, WA1, 2023
- SCGS, P6, Prelim, 2024
- SCGS, P6, Prelim, 2025
- Tao Nan, P5, SA2, 2021
- Tao Nan, P5, EOY, 2022
- Tao Nan, P5, EOY, 2023
- Tao Nan, P5, WA2, 2023
- Tao Nan, P5, EOY, 2024
- Tao Nan, P5, EOY, 2025
- Tao Nan, P5, WA1, 2025
- Tao Nan, P5, WA2, 2025
- Tao Nan, P6, Prelim, 2021
- Tao Nan, P6, SA1, 2021
- Tao Nan, P6, Prelim, 2022
- Tao Nan, P6, SA1, 2022
- Tao Nan, P6, Prelim, 2023
- Tao Nan, P6, WA2, 2023
- Tao Nan, P6, Prelim, 2024
- Tao Nan, P6, SA1, 2024
- Tao Nan, P6, Prelim, 2025
