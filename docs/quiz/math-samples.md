# Math question samples

One question per template, taken from the generated banks (`python3 scripts/quiz/math/build.py`). ✔ marks the correct option. Each wrong option shows the mistake it represents. Fractions and Ratio were the pilot topics; the last section shows the templates rewritten after the November 2026 bank review (their figures are not shown here).

## Fractions

### Basic

**fracti-b-4f9f21b777** (simplest_form). Express 12/84 in its simplest form.

- A. 6/42: *stopped_before_simplest* (Divided by 2, a common factor, but not by the HCF 12.)
- B. 1/84: *divided_numerator_only* (Divided only the numerator by 12.)
- C. 1/7 ✔
- D. 7: *inverted_fraction* (Turned the fraction upside down.)

Solution: HCF of 12 and 84 is 12. → 12 ÷ 12 = 1, 84 ÷ 12 = 7. → 12/84 = 1/7

**fracti-b-4f29a5c52b** (compare_order). Which of these fractions is the smallest? 3/11, 1/8, 1/4, 3/7

- A. 1/4: *thought_bigger_denominator_means_bigger* (Thought a bigger denominator makes a bigger fraction.)
- B. 3/11: *compared_denominators_only* (Looked only at the denominators.)
- C. 3/7: *compared_without_common_denominator* (Compared without changing to a common denominator.)
- D. 1/8 ✔

Solution: Common denominator 616: 3/11 = 168/616, 1/8 = 77/616, 1/4 = 154/616, 3/7 = 264/616 → The smallest is 1/8

**fracti-b-d9d7310b5f** (equivalent_bar_parts). Siti drew two bars of the same length. The top bar has 2/6 shaded. The bottom bar is cut into 12 equal parts. How many parts of the bottom bar must be shaded to show a fraction equal to 2/6?

- A. 4 ✔
- B. 5: *careless_slip* (Counted one part too many.)
- C. 8: *added_the_same_to_both* (Added 6 to both the numerator and the denominator.)
- D. 2: *kept_the_same_numerator* (Shaded 2 parts, the same number as the top bar, but the parts are smaller.)

Solution: 12 ÷ 6 = 2, so each part of the top bar is 2 parts of the bottom bar. → 2 × 2 = 4 parts

**fracti-b-e84a641dc9** (add_unlike). Find the value of 4/5 + 7/10. Give your answer in its simplest form.

- A. 1 1/10: *forgot_to_rename_numerators* (Used denominator 10 but kept the numerators 4 and 7.)
- B. 11/15: *added_numerators_and_denominators* (Added the tops and added the bottoms.)
- C. 2 1/2: *slip_converting_to_mixed_number* (Made a slip changing the improper fraction to a mixed number.)
- D. 1 1/2 ✔

Solution: LCM of 5 and 10 is 10. → 4/5 = 8/10, 7/10 = 7/10. → 8/10 + 7/10 = 15/10 = 1 1/2

**fracti-b-0075140f36** (like_add_sub). Subtract 2/8 from 6/8. Give your answer in its simplest form.

- A. 1/2 ✔
- B. 1: *added_instead_of_subtracted* (Added instead of subtracting.)
- C. 2/3: *subtracted_from_the_denominator* (Subtracted 2 from the denominator too.)
- D. 4: *dropped_the_denominator* (Subtracted the numerators and forgot the denominator.)

Solution: The denominators are the same, so subtract the numerators: 6 − 2 = 4. → 6/8 − 2/8 = 4/8 = 1/2

**fracti-b-7f6e8c20ce** (related_add_sub). Work out 3/4 + 1/12. Write your answer as a fraction in its simplest form.

- A. 1/4: *added_numerators_and_denominators* (Added the tops and added the bottoms.)
- B. 1: *careless_slip_in_numerator* (Careless slip working out the numerator.)
- C. 5/6 ✔
- D. 1/3: *forgot_to_rename* (Used denominator 12 but did not change the numerator 3.)

Solution: 3/4 = 9/12 → 9/12 + 1/12 = 10/12 = 5/6

**fracti-b-3a4e30af81** (frac_times_whole). Find the value of 3/8 × 12.

- A. 1/32: *multiplied_denominator* (Multiplied the denominator by 12 instead of the numerator.)
- B. 5 1/2: *slip_converting_to_mixed_number* (Made a slip changing the improper fraction to a mixed number.)
- C. 1 7/8: *added_whole_to_numerator* (Added 12 to the numerator.)
- D. 4 1/2 ✔

Solution: 3/8 × 12 = 3 × 12 / 8 = 36/8 → = 4 1/2

**fracti-b-adaba71847** (frac_div_whole). Find the value of 2/3 ÷ 4.

- A. 6: *inverted_answer* (Turned the answer upside down.)
- B. 1/3: *careless_slip_in_numerator* (Careless slip working out the numerator.)
- C. 1/6 ✔
- D. 2 2/3: *multiplied_instead_of_dividing* (Multiplied by 4 instead of dividing.)

Solution: Dividing by 4 is the same as multiplying by 1/4. → 2/3 × 1/4 = 2/12 → = 1/6

**fracti-b-633d72f988** (whole_div_frac). Find the value of 11 ÷ 1/3.

- A. 33 ✔
- B. 11: *ignored_denominator* (Divided by 1 but forgot to multiply by 3.)
- C. 3 2/3: *did_not_invert_divisor* (Multiplied by 1/3 instead of 3/1.)
- D. 1/33: *inverted_answer* (Turned the answer upside down.)

Solution: Dividing by 1/3 is the same as multiplying by 3/1. → 11 × 3/1 = 33/1 → = 33

**fracti-b-5d81f92fb1** (share_remainder). Jun Wei used 1/4 of a 7 m long rope. The rest of the rope was cut into 5 equal pieces. How long is each piece?

- A. 1 1/20 m ✔
- B. 1 2/5 m: *ignored_the_used_part* (Shared the whole rope.)
- C. 7/20 m: *shared_the_used_part* (Shared the 1/4 that was used instead of the rest.)
- D. 2 1/20 m: *slip_converting_to_mixed_number* (Made a slip changing the improper fraction to a mixed number.)

Solution: Rest = (1 − 1/4) × 7 m = 5 1/4 m → Each piece = 5 1/4 ÷ 5 = 1 1/20 m

**fracti-b-b70457e480** (improper_times_improper). Work out 12/7 × 3/2. Give your answer as a mixed number in its simplest form.

- A. 3 4/7: *slip_converting_to_mixed_number* (Made a slip changing the improper fraction to a mixed number.)
- B. 2 4/7 ✔
- C. 4: *added_the_denominators* (Multiplied the tops but added the bottoms.)
- D. 1 1/7: *inverted_second_fraction* (Turned the second fraction upside down, as for division.)

Solution: Numerators: 12 × 3 = 36 → Denominators: 7 × 2 = 14 → 36/14 = 2 4/7

**fracti-b-e6e199ff07** (mixed_times_whole). Work out 4 3/4 × 9. Give your answer as a mixed number in its simplest form.

- A. 36 3/4: *multiplied_only_the_whole_number* (Multiplied 4 by 9 but did not multiply 3/4.)
- B. 43 3/4: *slip_converting_to_mixed_number* (Made a slip changing the improper fraction to a mixed number.)
- C. 42 3/4 ✔
- D. 10 3/4: *multiplied_only_the_fraction* (Multiplied 3/4 by 9 but did not multiply 4.)

Solution: 4 3/4 = 19/4 → 19/4 × 9 = 171/4 = 42 3/4

**fracti-b-595970d4ce** (fraction_of_quantity). What is 8/11 of 22 marbles?

- A. 2 marbles: *found_one_part_only* (Divided by 11 but did not multiply by 8.)
- B. 18 marbles: *miscounted_units* (Counted one unit too many.)
- C. 6 marbles: *found_the_other_part* (Found the remaining 3/11 instead.)
- D. 16 marbles ✔

Solution: 1/11 of 22 = 22 ÷ 11 = 2 → 8/11 of 22 = 8 × 2 = 16

**fracti-b-afafbbc227** (shaded_figure). The figure is made of 15 equal squares. What fraction of the figure is shaded? Give your answer in its simplest form.

- A. 1/5 ✔
- B. 1/4: *compared_part_with_other_part* (Compared the shaded part with the unshaded part instead of with the whole.)
- C. 4/15: *miscounted_squares* (Counted one square too many.)
- D. 4/5: *gave_unshaded_fraction* (Found the unshaded part instead.)

Solution: 3 of the 15 squares are shaded. → Shaded: 3/15 = 1/5

**fracti-b-804fd4b10e** (express_as_fraction_of). Express 250 g as a fraction of 2 kg. Give your answer in its simplest form.

- A. 1/8 ✔
- B. 8: *inverted_fraction* (Wrote the fraction upside down.)
- C. 5/4: *used_wrong_conversion* (Used the wrong number of g in 1 kg.)
- D. 125: *forgot_to_convert_units* (Did not change kg to g first.)

Solution: 2 kg = 2000 g → 250/2000 = 1/8

**fracti-b-0267366295** (quantity_left). Aisha bought 3 litres of paint and used 1/5 of it. How much paint was left?

- A. 2 4/5 litres: *subtracted_fraction_from_quantity* (Took away 1/5 litres instead of 1/5 of 3 litres.)
- B. 2 2/5 litres ✔
- C. 3 2/5 litres: *slip_converting_to_mixed_number* (Made a slip changing the improper fraction to a mixed number.)
- D. 3/5 litres: *gave_amount_used* (Found the amount used instead of the amount left.)

Solution: Fraction left = 1 − 1/5 = 4/5 → 4/5 × 3 = 2 2/5 litres

**fracti-b-49f9d10f5d** (compare_unit_fractions). Which of these unit fractions is the greatest? 1/6, 1/7, 1/10, 1/3

- A. 1/10: *bigger_denominator_means_bigger* (Thought a bigger denominator means a bigger fraction.)
- B. 1/7: *compared_denominators_the_wrong_way* (Ordered the denominators the wrong way round.)
- C. 1/6: *guessed_from_the_look_of_the_numbers* (Did not think about the size of the equal parts.)
- D. 1/3 ✔

Solution: Unit fractions: the more equal parts the whole is cut into, the smaller each part. → The greatest is 1/3.

**fracti-b-a21e88d9a3** (fraction_to_decimal). Express 9/11 as a decimal, correct to 2 decimal places.

- A. 0.8: *rounded_to_1_decimal_place* (Rounded to 1 decimal place instead of 2.)
- B. 1.22: *divided_the_wrong_way* (Worked out 11 ÷ 9 instead of 9 ÷ 11.)
- C. 0.81: *cut_off_instead_of_rounding* (Cut the decimal off after 2 places instead of rounding.)
- D. 0.82 ✔

Solution: 9/11 = 9 ÷ 11 = 0.8182… → The third decimal place is 8, so round up. → Answer: 0.82

**fracti-b-1450c6b0b1** (improper_mixed). Express 29/7 as a mixed number.

- A. 4 6/7: *used_the_wrong_remainder* (Wrote the remainder as 6 instead of 1.)
- B. 4 1/7 ✔
- C. 5 1/7: *whole_number_one_too_big* (Made a slip in the whole number.)
- D. 3 1/7: *whole_number_one_too_small* (Made a slip in the whole number.)

Solution: 29 ÷ 7 = 4 remainder 1 → = 4 1/7

### Intermediate

**fracti-i-cdac789921** (mixed_subtract_borrow). A ribbon is 4 2/3 m long. Hui Min cuts off 2 10/11 m. How long is the ribbon that is left?

- A. 2 25/33 m: *forgot_to_take_away_the_borrowed_whole* (Renamed 1 whole as a fraction but did not reduce the whole number by 1.)
- B. 3 m: *subtracted_numerators_and_denominators* (Subtracted tops and bottoms separately.)
- C. 2 8/33 m: *subtracted_smaller_fraction_from_larger* (Did 10/11 − 2/3 because 2/3 is smaller, instead of renaming 1 whole.)
- D. 1 25/33 m ✔

Solution: 4 2/3 = 3 55/33 (rename 1 whole) → 2 10/11 = 2 30/33 → 3 55/33 − 2 30/33 = 1 25/33 m

**fracti-i-2904723094** (like_story_left). Priya read 4/7 of a book on Saturday and 1/7 of the book on Sunday. What fraction of the book has Priya not read? Give your answer in its simplest form.

- A. 1/7: *careless_slip_in_numerator* (Careless slip working out the numerator.)
- B. 2/7 ✔
- C. 3/7: *used_one_day_only* (Took away the fraction for Saturday only.)
- D. 5/7: *gave_the_part_read* (Found the fraction already read, not the fraction left.)

Solution: Read: 4/7 + 1/7 = 5/7 → Not read: 7/7 − 5/7 = 2/7

**fracti-i-f9f78be0ee** (related_pizza_left). Siti ate 1/3 of a pizza and Ravi ate 1/6 of the same pizza. What fraction of the pizza was left? Give your answer in its simplest form.

- A. 7/9: *added_numerators_and_denominators* (Added the tops and added the bottoms.)
- B. 2/3: *forgot_to_rename* (Added 1/6 + 1/6 without renaming 1/3.)
- C. 1: *careless_slip_in_numerator* (Careless slip working out the numerator.)
- D. 1/2 ✔

Solution: Eaten: 2/6 + 1/6 = 3/6 → Left: 6/6 − 3/6 = 3/6 = 1/2

**fracti-i-7fd1329483** (remainder_left). Ali had $40. Ali spent 3/4 of it on a bag and 3/5 of the remainder on a book. How much money did Ali have left?

- A. $6: *gave_cost_of_book* (Gave the cost of the book instead of the money left.)
- B. $4 ✔
- C. $10: *stopped_after_first_step* (Stopped after paying for the bag.)
- D. $30: *gave_cost_of_bag* (Gave the cost of the bag.)

Solution: Bag: 3/4 × $40 = $30 → Remainder: $40 − $30 = $10 → Book: 3/5 × $10 = $6 → Left: $10 − $6 = $4

**fracti-i-83b513a034** (share_into_bags). 7/9 kg of flour is packed equally into 6 bags. What is the mass of flour in each bag?

- A. 7 5/7 kg: *divided_bags_by_flour* (Worked out 6 ÷ 7/9 instead of 7/9 ÷ 6.)
- B. 4 2/3 kg: *multiplied_instead_of_dividing* (Multiplied by 6 instead of dividing.)
- C. 4/27 kg: *careless_slip_in_numerator* (Careless slip working out the numerator.)
- D. 7/54 kg ✔

Solution: 7/9 ÷ 6 = 7/9 × 1/6 → = 7/54 kg

**fracti-i-fde69fd843** (how_many_cups). A jug holds 6 litres of juice. How many cups of 3/7 litre can be filled completely?

- A. 2 cups: *ignored_denominator* (Divided by 3 but did not multiply by 7.)
- B. 42 cups: *ignored_numerator* (Multiplied by 7 but did not divide by 3.)
- C. 14 cups ✔
- D. 45 cups: *added_instead_of_divided* (Mixed up the steps.)

Solution: 6 ÷ 3/7 = 6 × 7/3 → = 42/3 = 14

**fracti-i-63d3b73c09** (fraction_of_remainder). 2/7 of a cake was left after a party. Priya ate 1/5 of the cake that was left. What fraction of the whole cake did Priya eat?

- A. 2/35 ✔
- B. 3/35: *subtracted_fractions* (Worked out 2/7 − 1/5.)
- C. 1/5: *fraction_of_remainder_as_fraction_of_whole* (Gave 1/5, which is a fraction of the leftover only.)
- D. 8/35: *found_what_is_still_left* (Found the fraction of the cake still left.)

Solution: 1/5 of 2/7 = 1/5 × 2/7 → = 2/35

**fracti-i-bea5e9d523** (improper_times_improper_cancel). Find the value of 5/3 × 13/5. Give your answer in its simplest form.

- A. 25/39: *inverted_second_fraction* (Turned the second fraction upside down, as for division.)
- B. 5 1/3: *slip_converting_to_mixed_number* (Made a slip changing the improper fraction to a mixed number.)
- C. 8 1/8: *added_the_denominators* (Multiplied the tops but added the bottoms.)
- D. 4 1/3 ✔

Solution: Cancel the common factor between 5 and 5. → 5/3 × 13/5 = 65/15 = 4 1/3

**fracti-i-d2e01913d3** (mixed_times_whole_cancel). Find the value of 6 × 4 1/2. Give your answer in its simplest form.

- A. 7: *multiplied_only_the_fraction* (Multiplied 1/2 by 6 but did not multiply 4.)
- B. 24 1/2: *multiplied_only_the_whole_number* (Multiplied 4 by 6 but did not multiply 1/2.)
- C. 3/4: *divided_instead_of_multiplied* (Divided by 6 instead of multiplying.)
- D. 27 ✔

Solution: 4 1/2 = 9/2 → 6 × 9/2 = 54/2 = 27

**fracti-i-6fde2386c8** (more_boys_than_girls). 9/10 of the pupils in a hall are boys. There are 88 more boys than girls. How many pupils are there in the hall?

- A. 99 pupils: *gave_number_of_boys* (Found the number of boys only.)
- B. 110 pupils ✔
- C. 121 pupils: *miscounted_units* (Counted one unit too many.)
- D. 880 pupils: *treated_difference_as_one_part* (Took 88 as 1/10 of the pupils.)

Solution: Girls = 1 − 9/10 = 1/10 → Difference = 9/10 − 1/10 = 8/10 → 88 pupils → 1/10 → 88 ÷ 8 = 11 → Total = 10 × 11 = 110

**fracti-i-988a1b7b4e** (fixed_then_fraction). Kumar had some money. Kumar spent $90 on a book and 1/3 of the remaining money on a bag. Kumar had $6 left. How much money did Kumar have at first?

- A. $102: *miscounted_units* (Counted one unit too many.)
- B. $99 ✔
- C. $144: *added_fixed_amount_before_working_back* (Added $90 before undoing the 1/3.)
- D. $9: *forgot_to_add_back_fixed_amount* (Worked back to $9 but did not add the $90 for the book.)

Solution: Money left = 2/3 of the remainder → $6 → Remainder = $6 ÷ 2 × 3 = $9 → At first = $9 + $90 = $99

**fracti-i-c7296cca32** (equal_use_per_day). A tank of water was full. The same amount of water was used every day. After 3 days, 5/8 of the tank was left. After 7 days, 1/8 of the tank was left. What fraction of the tank was used each day?

- A. 1/56: *used_fraction_left* (Used the fraction left instead of the fraction used.)
- B. 1/2: *forgot_to_divide_by_days* (Found the water used from day 3 to day 7 but did not divide by 4.)
- C. 1/14: *divided_by_wrong_number_of_days* (Divided by 7 instead of 4.)
- D. 1/8 ✔

Solution: Used from day 3 to day 7: 5/8 − 1/8 = 1/2 → Days: 7 − 3 = 4 → Each day: 1/2 ÷ 4 = 1/8

**fracti-i-572a778546** (order_like_fractions). Arrange these fractions in order, from greatest to smallest: 10/11, 1/11, 6/11, 3/11

- A. 10/11, 6/11, 3/11, 1/11 ✔
- B. 6/11, 10/11, 3/11, 1/11: *swapped_two_neighbours* (Swapped two fractions that are next to each other.)
- C. 1/11, 3/11, 6/11, 10/11: *ordered_the_wrong_way_round* (Wrote the order backwards.)
- D. 10/11, 6/11, 1/11, 3/11: *swapped_two_neighbours* (Swapped two fractions that are next to each other.)

Solution: The denominators are the same (11), so compare the numerators. → Numerators greatest to smallest: 10, 6, 3, 1

**fracti-i-404134badf** (missing_equivalent). Find the missing number: 6/10 = 21/?

- A. 25: *added_the_difference* (Added 15 to the denominator instead of keeping the fraction equal.)
- B. 70: *multiplied_denominator_by_new_factor* (Multiplied 10 by 7 without simplifying first.)
- C. 40: *careless_slip* (Made a slip in the multiplication.)
- D. 35 ✔

Solution: 6/10 = 3/5 in simplest form → 3/5 = 21/35 → Missing number = 35

**fracti-i-2ea0f7ee64** (equivalent_read_bar). Priya shaded part of a strip of paper that was cut into 12 equal parts. Which fraction is equal to the part of the strip that is shaded?

- A. 6: *inverted_fraction* (Turned the fraction upside down.)
- B. 5/6: *gave_the_unshaded_fraction* (Found the fraction that is NOT shaded.)
- C. 1/6 ✔
- D. 1/12: *divided_numerator_only* (Divided only the numerator by 2.)

Solution: 2 of the 12 parts are shaded: 2/12. → Divide top and bottom by 2: 1/6.

**fracti-i-07268f6f11** (mixed_add_context). Priya poured 4 2/7 litres of water into a pail, then another 3 6/7 litres. How much water was in the pail?

- A. 7 4/7 litres: *added_denominators* (Added the denominators too.)
- B. 8 1/7 litres ✔
- C. 9 1/7 litres: *careless_slip* (Made a slip adding the whole numbers.)
- D. 7 1/7 litres: *lost_the_carried_whole* (Changed the fraction part but forgot to add the 1 whole.)

Solution: Wholes: 4 + 3 = 7 → Fractions: 2/7 + 6/7 = 8/7 = 1 1/7 → Total = 8 1/7 litres

**fracti-i-ad280fee62** (division_as_fraction). 10 watermelons are shared equally among 8 children. How many watermelons does each child get?

- A. 1 1/4 watermelons ✔
- B. 1 watermelon: *dropped_the_remainder* (Gave only the whole number part.)
- C. 5/8 of a watermelon: *halved_wrongly* (Divided by twice the number of children.)
- D. 4/5 of a watermelon: *divided_the_wrong_way* (Worked out 8 ÷ 10 instead of 10 ÷ 8.)

Solution: 10 ÷ 8 = 10/8 → = 1 1/4

### Competent

**fracti-c-763956ba07** (remainder_backwards). Ali spent 1/5 of the money in a wallet on a pair of shoes and 1/3 of the remaining money on a shirt. Ali had $80 left. How much money was in the wallet at first?

- A. $180: *miscounted_units* (Counted one unit too many.)
- B. $30: *gave_cost_of_shoes* (Gave the cost of the shoes.)
- C. $150 ✔
- D. $120: *worked_back_only_one_step* (Found the money left after the shoes only.)

Solution: Money left = 2/3 of the remainder → $80 → Remainder = $80 ÷ 2 × 3 = $120 → Remainder = 4/5 of the money → $120 → At first = $120 ÷ 4 × 5 = $150

**fracti-c-38424fbc8f** (book_more_than_pen). Aisha spent 3/4 of a sum of money on a book and 1/4 of the remainder on a pen. The book cost $77 more than the pen. How much money did Aisha have at first?

- A. $112 ✔
- B. $119: *miscounted_units* (Counted one unit too many.)
- C. $154: *took_second_fraction_of_total* (Took the pen as 1/4 of all the money.)
- D. $84: *gave_cost_of_book* (Gave the cost of the book.)

Solution: Pen = 1/4 × 1/4 = 1/16 of the money → Book − pen = 3/4 − 1/16 = 11/16 of the money → 11/16 → $77 → Money at first = $77 ÷ 11/16 = $112

**fracti-c-84d1f4514b** (equal_fractions). 1/3 of Ravi's stickers is equal to 5/6 of Mei Ling's stickers. Ravi has 36 more stickers than Mei Ling. How many stickers do they have altogether?

- A. 60 stickers: *gave_first_person_only* (Gave Ravi's stickers only.)
- B. 96 stickers: *miscounted_units* (Counted one unit too many.)
- C. 54 stickers: *used_numerators_as_ratio* (Took the ratio as 5 : 1 from the numerators only.)
- D. 84 stickers ✔

Solution: Make the numerators the same: 1/3 of Ravi = 5/6 of Mei Ling → Ravi : Mei Ling = 15 : 6 = 5 : 2 → 3 units → 36, so 1 unit → 12 → Altogether = 7 × 12 = 84

**fracti-c-ccecae66fa** (improper_times_improper_story). A bottle holds 9/4 L of juice. A jug holds 5/2 times as much juice as the bottle. Ravi poured all the juice from the bottle and the jug into a tank. How much juice was in the tank?

- A. 4 3/4 L: *added_instead_of_multiplied* (Added 5/2 L to the bottle instead of multiplying.)
- B. 5 5/8 L: *forgot_the_bottle* (Found only the juice in the jug.)
- C. 8 7/8 L: *slip_converting_to_mixed_number* (Made a slip changing the improper fraction to a mixed number.)
- D. 7 7/8 L ✔

Solution: Juice in the jug: 9/4 × 5/2 = 5 5/8 L → Juice in the tank: 2 1/4 + 5 5/8 = 7 7/8 L

**fracti-c-1fe87a0c28** (mixed_times_whole_shelves). Xin Yi needs 3 shelves. Each shelf is 1 1/4 m long. Xin Yi has a plank that is 8 m long. How much of the plank will be left after the 3 shelves are cut?

- A. 4 3/4 m: *multiplied_only_the_whole_number* (Multiplied 1 by 3 but not the 1/4.)
- B. 3 3/4 m: *gave_the_length_used* (Found the length used instead of the length left.)
- C. 6 3/4 m: *used_one_shelf_only* (Took away the length of one shelf only.)
- D. 4 1/4 m ✔

Solution: Length needed: 1 1/4 × 3 = 3 3/4 m → Left: 8 − 3 3/4 = 4 1/4 m

**fracti-c-196b792d01** (glasses_in_groups). 4/7 of the pupils in a school hall are boys. 1/2 of the boys and 2/5 of the girls wear glasses. 64 pupils wear glasses. How many pupils are in the hall?

- A. 140 pupils ✔
- B. 160 pupils: *miscounted_units* (Counted one unit too many.)
- C. 76 pupils: *gave_pupils_without_glasses* (Gave the number of pupils without glasses.)
- D. 80 pupils: *gave_number_of_boys* (Gave the number of boys.)

Solution: Boys with glasses = 1/2 × 4/7 = 2/7 of the pupils → Girls with glasses = 2/5 × 3/7 = 6/35 of the pupils → Glasses = 16/35 of the pupils → 64 → Pupils = 64 ÷ 16/35 = 140

**fracti-c-09af4fd1ad** (constant_part_new_fraction). In a jar, 3/5 of the beads are red and the rest are blue. After 24 blue beads are added, the red beads make up 1/3 of all the beads. How many beads were in the jar at first?

- A. 54 beads: *gave_total_after* (Gave the number of beads after the blue beads were added.)
- B. 30 beads ✔
- C. 90 beads: *treated_change_in_fraction_as_added_beads* (Took 24 as (3/5 − 1/3) of the beads, but the whole changed.)
- D. 36 beads: *miscounted_units* (Counted one unit too many.)

Solution: The red beads do not change. Make red the same number of units: LCM of 3 and 1 is 3 → Before: red 3 units of 5; after: red 3 units of 9 → 4 units → 24, so 1 unit = 6 → At first = 5 × 6 = 30

**fracti-c-43060e9ce6** (unequal_wholes_same_remainder). Daniel had $18 more than Shu Fen. Daniel spent 2/3 of Daniel's money and Shu Fen spent 1/2 of Shu Fen's money. They then had the same amount of money left. How much money did they have altogether at first?

- A. $108: *miscounted_units* (Counted one unit too many.)
- B. $36: *gave_total_left* (Gave the total money left at the end.)
- C. $54: *gave_first_person_only* (Gave Daniel's money at first only.)
- D. $90 ✔

Solution: Left: 1/3 of Daniel's = 1/2 of Shu Fen's money → Daniel : Shu Fen = 1/2 : 1/3 = 3 : 2 → Difference 1 unit → $18, so 1 unit = $18 → Altogether = (3 + 2) × $18 = $90

**fracti-c-def3b059e8** (two_groups_sold). A fruit stall had some apples and pears. 1/8 of the fruits were apples. After 3/5 of the apples and 43 pears were sold, 105 fruits were left. How many fruits were there at first?

- A. 160 fruits ✔
- B. 370 fruits: *took_fraction_of_all_fruits* (Took 3/5 of all the fruits instead of the apples.)
- C. 20 fruits: *gave_apples_only* (Gave the number of apples at first.)
- D. 180 fruits: *miscounted_units* (Counted one unit too many.)

Solution: Apples left = 2/5 of 1/8 = 1/20 of the fruits → Pears = 7/8 of the fruits → 37/40 of the fruits = 105 + 43 = 148 → Fruits at first = 148 ÷ 37/40 = 160

**fracti-c-0371cfb954** (compare_like_story). Three identical cakes were each cut into 10 equal slices. Wei Jie ate 8/10 of a cake, Ravi ate 1/10 of a cake and Ali ate 3/10 of a cake. How much more cake did the child who ate the most eat than the child who ate the least? Give your answer in its simplest form.

- A. 7/10 ✔
- B. 1/2: *compared_the_wrong_pair* (Compared the child who ate the most with the middle child.)
- C. 4/5: *careless_slip_in_numerator* (Careless slip working out the numerator.)
- D. 1/5: *compared_the_wrong_pair* (Compared the middle child with the child who ate the least.)

Solution: Most: 8/10. Least: 1/10. → 8/10 − 1/10 = 7/10

**fracti-c-1716d2e6f1** (equivalent_in_context). In a box, 3/4 of the beads are red and the rest are blue. There are 3 blue beads. After 5 more red beads are put in, what fraction of the beads in the box are red? Give your answer in its simplest form.

- A. 7/6: *kept_the_old_total* (Added the red beads but kept the old total.)
- B. 3/4: *ignored_the_new_beads* (Gave the fraction before the new beads were added.)
- C. 9/17: *forgot_to_add_to_red* (Added the beads to the total but not to the red beads.)
- D. 14/17 ✔

Solution: Blue = 1/4 of the beads → 3, so 1/4 → 3 → Red = 3 × 3 = 9 → After: red = 14, total = 17 → Fraction red = 14/17 = 14/17

**fracti-c-5ff28b1b64** (equivalent_two_strips). Nurul has two strips of paper of the same length. Strip A is cut into 5 equal parts and 2 parts are shaded. Strip B is cut into 10 equal parts and 3 parts are shaded. How many more parts of Strip B must be shaded so that both strips have the same fraction shaded?

- A. 7: *gave_unshaded_parts* (Found the number of parts of Strip B not shaded.)
- B. 1 ✔
- C. 2: *careless_slip* (Counted one part too many.)
- D. 4: *forgot_parts_already_shaded* (Found the 4 parts needed but did not subtract the 3 already shaded.)

Solution: 2/5 = 4/10 → Strip B needs 4 parts shaded. → 4 − 3 = 1 more parts

**fracti-c-bb633e15e9** (mixed_times_whole_context). Xin Yi cut 5 pieces of ribbon, each 4 2/5 m long, from a roll. 3 m of ribbon was left. How long was the roll at first?

- A. 23 2/5 m: *multiplied_only_the_whole_number* (Multiplied 4 by 5 but not the 2/5.)
- B. 7 2/5 m: *did_not_multiply* (Used one piece instead of 5 pieces.)
- C. 25 m ✔
- D. 22 m: *forgot_the_leftover* (Did not add the 3 m that was left.)

Solution: 4 2/5 × 5 = 22 m → Roll = 22 + 3 = 25 m

**fracti-c-79452ff21d** (add_subtract_story). A cake was cut into 120 equal slices. Xin Yi ate 1/10 of the cake and Nurul ate 7/8 of it. How many slices were left?

- A. 108 slices: *subtracted_only_one_fraction* (Took away only Xin Yi's share.)
- B. 117 slices: *gave_slices_eaten* (Found the slices eaten instead of the slices left.)
- C. 4 slices: *miscounted_units* (Counted one slice too many.)
- D. 3 slices ✔

Solution: Eaten = 1/10 + 7/8 = 39/40 → Left = 1 − 39/40 = 1/40 → 1/40 × 120 = 3 slices

**fracti-c-86afcfc9fc** (like_tank_three_steps). A tank was 3/6 full of water. Farid poured in water that filled another 2/6 of the tank. Then 2/6 of the tank was used to water plants. What fraction of the tank was full at the end? Give your answer in its simplest form.

- A. 5/6: *forgot_the_water_used* (Forgot to take away the water that was used.)
- B. 7/6: *added_the_amount_used* (Added the water used instead of taking it away.)
- C. 1: *careless_slip_in_numerator* (Careless slip working out the numerator.)
- D. 1/2 ✔

Solution: After pouring: 3/6 + 2/6 = 5/6 → After using: 5/6 − 2/6 = 3/6 = 1/2

**fracti-c-9d0af38c8f** (related_money_three_parts). Arjun had some money. Arjun spent 1/3 of it on a book and 3/9 of it on a pen, and gave 2/9 of it to a cousin. What fraction of the money was left? Give your answer in its simplest form.

- A. 8/9: *gave_the_part_spent* (Found the fraction spent and gave it as the fraction left.)
- B. 1/3: *forgot_the_gift* (Left out the money given to the cousin.)
- C. 2/9: *careless_slip_in_numerator* (Careless slip working out the numerator.)
- D. 1/9 ✔

Solution: Spent altogether: 3/9 + 3/9 + 2/9 = 8/9 → Left: 1/9

**fracti-c-3c8ec97a30** (division_share_compare). In Jun Wei's group, 2 pizzas are shared equally among 10 pupils. In Mei Ling's group, 8 pizzas are shared equally among 3 pupils. How much more pizza does each pupil in the group with the bigger share get?

- A. 4 5/8 pizzas: *divided_the_wrong_way* (Worked out pupils ÷ pizzas.)
- B. 2 7/15 pizzas ✔
- C. 6/7 of a pizza: *subtracted_tops_and_bottoms* (Subtracted pizzas and pupils separately.)
- D. 2 2/3 pizzas: *gave_the_bigger_share* (Gave the bigger share instead of the difference.)

Solution: Jun Wei's group: 2 ÷ 10 = 1/5 → Mei Ling's group: 8 ÷ 3 = 2 2/3 → Difference = 2 7/15

## Ratio

### Basic

**ratio-b-e871044cfc** (simplest_ratio). Express 64 : 48 : 72 in its simplest form.

- A. 8 : 6 : 9 ✔
- B. 32 : 24 : 36: *stopped_before_simplest* (Divided by 2 but not by the HCF 8.)
- C. 9 : 6 : 8: *reversed_order* (Wrote the terms in the wrong order.)
- D. 8 : 6 : 36: *divided_terms_by_different_numbers* (Divided the last term by 2 instead of 8.)

Solution: HCF of 64, 48, 72 is 8. → Divide each term by 8: 8 : 6 : 9

**ratio-b-0f98b9fce9** (divide_in_ratio). Farid and Priya share $70 in the ratio 1 : 4. How much does the person with the larger share get?

- A. $42: *miscounted_units* (Counted one unit too few.)
- B. $14: *found_one_unit_only* (Found 1 unit ($70 ÷ 5) but did not multiply.)
- C. $56 ✔
- D. $70: *miscounted_units* (Counted one unit too many.)

Solution: Total units = 1 + 4 = 5 → 1 unit = $70 ÷ 5 = $14 → Larger share = 4 × $14 = $56

**ratio-b-a34bd73b4c** (missing_term). Find the missing number: 3 : 2 = 15 : ?

- A. 8: *miscounted_units* (Counted one unit too few.)
- B. 10 ✔
- C. 12: *miscounted_units* (Counted one unit too many.)
- D. 14: *added_the_difference* (Added 12 to 2 instead of multiplying by 5.)

Solution: 15 = 3 × 5 → Missing number = 2 × 5 = 10

**ratio-b-ce9a288344** (ratio_with_units). Find the ratio of 35 minutes to 1 hour. Give your answer in its simplest form.

- A. 7 : 12 ✔
- B. 12 : 7: *reversed_order* (Wrote the terms in the wrong order.)
- C. 7 : 20: *used_100_minutes_in_an_hour* (Used 100 minutes in an hour.)
- D. 35 : 1: *forgot_to_convert_units* (Compared 35 with 1 without changing hours to minutes.)

Solution: 1 h = 60 min → 35 : 60 = 7 : 12

**ratio-b-3e46392865** (ratio_to_fraction). The ratio of red beads to yellow beads in a box is 8 : 1. What fraction of the beads are red beads?

- A. 1/9: *found_fraction_of_other_colour* (Found the fraction of yellow beads.)
- B. 8: *used_other_part_as_whole* (Wrote 8/1, comparing with yellow beads instead of all the beads.)
- C. 1: *careless_slip_in_numerator* (Careless slip working out the numerator.)
- D. 8/9 ✔

Solution: Total units = 8 + 1 = 9 → Fraction of red beads = 8/9

**ratio-b-8ceb626a13** (fraction_to_ratio). The number of boys in a club is 7/9 of the number of girls. What is the ratio of the number of boys to the total number of children?

- A. 9 : 16: *gave_girls_to_total* (Gave girls : total.)
- B. 7 : 9: *gave_boys_to_girls* (Gave boys : girls, not boys : total.)
- C. 7 : 16 ✔
- D. 7 : 2: *subtracted_instead_of_added* (Used 9 − 7 for the total.)

Solution: Boys : girls = 7 : 9 → Total = 7 + 9 = 16 units → Boys : total = 7 : 16

**ratio-b-4983c4b33f** (counters_two_colours). Jun Wei put 6 counters in two rows, as shown. What is the ratio of the number of yellow counters to the number of white counters? Give your answer in its simplest form.

- A. 1 : 2: *reversed_order* (Wrote the ratio the wrong way round.)
- B. 4 : 2: *stopped_before_simplest* (Wrote 4 : 2 and did not simplify.)
- C. 2 : 1 ✔
- D. 2 : 3: *gave_part_to_total* (Compared yellow counters with all the counters.)

Solution: Yellow: 4, white: 2 → 4 : 2 = 2 : 1

### Intermediate

**ratio-i-78423a7e29** (ratio_difference_to_total). The ratio of Daniel's marbles to Mei Ling's marbles is 5 : 2. Daniel has 39 more marbles than Mei Ling. How many marbles do they have altogether?

- A. 273 marbles: *treated_difference_as_one_unit* (Took 39 as 1 unit.)
- B. 91 marbles ✔
- C. 65 marbles: *gave_first_person_only* (Gave Daniel's marbles only.)
- D. 104 marbles: *miscounted_units* (Counted one unit too many.)

Solution: Difference = 5 − 2 = 3 units → 39 → 1 unit = 39 ÷ 3 = 13 → Altogether = 7 × 13 = 91

**ratio-i-a70d55eb83** (combine_ratios). The ratio of A to B is 2 : 5. The ratio of B to C is 7 : 6. Find the ratio of A to B to C.

- A. 14 : 35 : 6: *scaled_only_first_ratio* (Changed the first ratio but not the second.)
- B. 2 : 5 : 6: *joined_without_matching_B* (Joined the ratios as 2 : 5 : 6 without making B the same.)
- C. 14 : 35 : 30 ✔
- D. 30 : 35 : 14: *reversed_order* (Wrote the ratio backwards.)

Solution: Make B the same: LCM of 5 and 7 is 35 → A : B = 14 : 35, B : C = 35 : 30 → A : B : C = 14 : 35 : 30

**ratio-i-931fe1456c** (part_to_total). The ratio of boys to girls in a choir is 5 : 9. There are 81 girls. How many children are in the choir?

- A. 45 children: *gave_number_of_boys* (Gave the number of boys.)
- B. 1134 children: *did_not_find_one_unit* (Multiplied 81 by 14 without finding 1 unit.)
- C. 126 children ✔
- D. 135 children: *miscounted_units* (Counted one unit too many.)

Solution: 9 units → 81 → 1 unit = 81 ÷ 9 = 9 → Total = 14 × 9 = 126

**ratio-i-886c52d5ec** (three_way_share). $38 is shared among three friends in the ratio 2 : 8 : 9. How much more does the person with the largest share get than the person with the smallest share?

- A. $2: *found_one_unit_only* (Found 1 unit only.)
- B. $18: *gave_largest_share* (Gave the largest share instead of the difference.)
- C. $14 ✔
- D. $16: *miscounted_units* (Counted one unit too many.)

Solution: Total units = 19 → 1 unit = $38 ÷ 19 = $2 → Difference = (9 − 2) × $2 = $14

**ratio-i-8b06bdfe2a** (multiple_and_ratio). Daniel, Hui Min and Farid share $36. Daniel gets 2 times as much as Hui Min. The ratio of Hui Min's share to Farid's share is 2 : 3. How much does Farid get?

- A. $4: *found_one_unit_only* (Found 1 unit only.)
- B. $8: *gave_second_person* (Gave Hui Min's share.)
- C. $12 ✔
- D. $16: *gave_first_person* (Gave Daniel's share.)

Solution: Hui Min : Farid = 2 : 3, so Daniel = 2 × 2 = 4 units → Daniel : Hui Min : Farid = 4 : 2 : 3 → 1 unit = $36 ÷ 9 = $4 → Farid = 3 × $4 = $12

**ratio-i-8412a4987e** (triangle_area_shared_height). In the figure, B, C and D lie on a straight line and BC : CD = 2 : 1. The area of triangle ABC is 28 cm². What is the area of triangle ACD?

- A. 28 cm²: *miscounted_units* (Counted one unit too many.)
- B. 56 cm²: *inverted_ratio* (Used CD : BC = 2 : 1 the wrong way round.)
- C. 42 cm²: *gave_whole_triangle* (Gave the area of the whole triangle ABD.)
- D. 14 cm² ✔

Solution: The triangles share the same height from A, so their areas are in the ratio of their bases. → 2 units → 28 cm², so 1 unit = 14 cm² → Area ACD = 1 × 14 = 14 cm²

**ratio-i-82328a3ad1** (counters_three_colours). Ravi arranged 4 counters in three rows, as shown. What is the ratio of the number of blue counters to the number of red counters to the number of white counters? Give your answer in its simplest form.

- A. 1 : 1 : 2: *reversed_order* (Wrote the ratio backwards.)
- B. 2 : 1 : 1 ✔
- C. 1 : 2 : 1: *used_the_order_of_the_rows* (Wrote the ratio in the order of the rows, not the order asked.)
- D. 2 : 1: *left_out_a_term* (Wrote only the first two terms.)

Solution: blue: 2, red: 1, white: 1 → 2 : 1 : 1 = 2 : 1 : 1

**ratio-i-e82d8efa89** (counters_part_to_total). Farid used 14 counters to make the three rows shown. What is the ratio of the number of yellow counters to the total number of counters? Give your answer in its simplest form.

- A. 6 : 14: *stopped_before_simplest* (Did not simplify.)
- B. 3 : 4: *compared_with_the_others_only* (Compared the yellow counters with the other counters, not the total.)
- C. 3 : 7 ✔
- D. 7 : 3: *reversed_order* (Wrote the ratio backwards.)

Solution: Total = 6 + 4 + 4 = 14 → Yellow : total = 6 : 14 = 3 : 7

### Competent

**ratio-c-a44288bf81** (transfer_total_unchanged). The ratio of Arjun's cards to Priya's cards was 9 : 4. After Arjun gave 9 cards to Priya, the ratio became 8 : 5. How many cards did Arjun have at first?

- A. 81 cards ✔
- B. 90 cards: *miscounted_units* (Counted one unit too many.)
- C. 72 cards: *gave_amount_after_transfer* (Gave Arjun's cards after giving some away.)
- D. 36 cards: *gave_other_person* (Gave Priya's cards at first.)

Solution: The total does not change. Make the totals equal: 13 and 13 → 13 units → Before 9 : 4, after 8 : 5 → Arjun lost 1 unit → 9 cards, so 1 unit = 9 → Arjun at first = 9 × 9 = 81

**ratio-c-295659910c** (one_quantity_unchanged). The ratio of red balloons to blue balloons at a party was 1 : 1. After 6 more red balloons were added, the ratio became 3 : 2. How many balloons were there at first?

- A. 6 balloons: *compared_terms_without_matching_blue* (Compared the ratios without keeping the blue balloons the same.)
- B. 24 balloons ✔
- C. 12 balloons: *gave_red_only* (Gave the red balloons at first only.)
- D. 30 balloons: *gave_total_after* (Gave the total after the red balloons were added.)

Solution: Blue does not change. Make blue the same: 1 and 2 → 2 units → Before 2 : 2, after 3 : 2 → Red increased by 1 unit → 6, so 1 unit = 6 → At first = (2 + 2) × 6 = 24

**ratio-c-64db7b7145** (ages_constant_difference). The ratio of Ravi's age to Priya's age is 3 : 1. In 12 years' time, the ratio will be 3 : 2. How old is Ravi now?

- A. 12 years old ✔
- B. 16 years old: *miscounted_units* (Counted one unit too many.)
- C. 24 years old: *gave_age_in_future* (Gave Ravi's age in 12 years' time.)
- D. 4 years old: *gave_other_person* (Gave Priya's age.)

Solution: The age difference does not change. Make it the same: 2 and 1 → 2 units → Now 3 : 1, later 6 : 4 → 3 units → 12 years, so 1 unit = 4 → Ravi now = 3 × 4 = 12

**ratio-c-307effcdcf** (give_fraction_new_ratio). The ratio of Jun Wei's stickers to Xin Yi's stickers is 2 : 1. Jun Wei gives 1/2 of Jun Wei's stickers to Xin Yi. What is the new ratio of Jun Wei's stickers to Xin Yi's stickers?

- A. 1 : 2 ✔
- B. 2 : 1: *reversed_order* (Wrote the ratio backwards.)
- C. 1 : 1: *forgot_to_add_to_other_person* (Took the stickers from Jun Wei but did not add them to Xin Yi.)
- D. 1 : 5: *took_fraction_of_total* (Took 1/2 of all the stickers.)

Solution: Let Jun Wei = 4 units and Xin Yi = 2 units (multiply by 2) → Jun Wei gives 1/2 × 4 = 2 units → New: 2 : 4 = 1 : 2

**ratio-c-46cd4b9756** (square_sides_area). The lengths of the sides of two squares are in the ratio 2 : 5. The difference between their areas is 189 cm². What is the area of the bigger square?

- A. 315 cm²: *used_side_ratio_for_areas* (Used 2 : 5 for the areas instead of 4 : 25.)
- B. 36 cm²: *gave_smaller_square* (Gave the area of the smaller square.)
- C. 225 cm² ✔
- D. 234 cm²: *miscounted_units* (Counted one unit too many.)

Solution: Areas are in the ratio 2² : 5² = 4 : 25 → Difference = 21 units → 189 cm² → 1 unit = 9 cm² → Bigger square = 25 × 9 = 225 cm²

**ratio-c-a0fac384e2** (three_way_share_remainder). Mr Lim spent 1/5 of a sum of money. He shared the rest among Hui Min, Priya and Mei Ling in the ratio 1 : 3 : 4. Mei Ling received $100. How much money did Mr Lim have at first?

- A. $1000: *used_wrong_share* (Took $100 as Hui Min's share.)
- B. $250 ✔
- C. $240: *added_fraction_of_the_rest* (Added 1/5 of the shared money instead of working back.)
- D. $200: *forgot_the_fraction_spent_first* (Found the money shared but did not undo the 1/5 spent.)

Solution: 4 units → $100, so 1 unit = $25 → Money shared = 8 × $25 = $200 → Money shared = 4/5 of the money → At first = $200 ÷ 4 × 5 = $250

**ratio-c-1bdef237d6** (units_three_people_total). The model shows the number of stamps that Aisha, Hui Min and Wei Jie have. Aisha and Wei Jie have 24 stamps altogether. How many stamps does Hui Min have?

- A. 40: *miscounted_units* (Counted one unit too many.)
- B. 32 ✔
- C. 8: *found_one_unit_only* (Found 1 unit (24 ÷ 3 = 8) but did not multiply by 4.)
- D. 96: *compared_with_one_person_only* (Treated 24 as Aisha's amount only.)

Solution: Aisha and Wei Jie: 1 + 2 = 3 units → 1 unit = 24 ÷ 3 = 8 → Hui Min: 4 × 8 = 32

**ratio-c-a7681f7a7f** (units_difference_total). The model shows the number of stickers that Nurul, Jun Wei and Mei Ling have. Jun Wei has 9 more stickers than Nurul. How many stickers do the three children have altogether?

- A. 9: *gave_the_difference* (Gave the 9 difference, not the total.)
- B. 117: *miscounted_units* (Counted one unit too many.)
- C. 81: *left_out_a_person* (Left out Nurul's stickers.)
- D. 108 ✔

Solution: Jun Wei has 4 − 3 = 1 more unit, so 1 unit = 9 → 1 unit = 9 ÷ 1 = 9 → Total = 12 × 9 = 108

## Rewritten after the bank review (November 2026)

### Basic

**geomet-b-577daa57f1** (pp_pick_pair). Wei Jie draws four lines, P, Q, R and S, on a square grid. Which two lines are parallel to each other?

- A. Q and R: *chose_lines_that_would_meet* (Lines Q and R would meet at 45° if they were drawn longer, so they are not parallel.)
- B. R and S: *chose_lines_that_would_meet* (Lines R and S would meet at 45° if they were drawn longer, so they are not parallel.)
- C. P and S ✔
- D. P and R: *chose_lines_that_would_meet* (Lines P and R would meet at 45° if they were drawn longer, so they are not parallel.)

Solution: Parallel lines slope the same way, so they never meet however long they are drawn. → Line P goes straight across. Line S goes straight across. → So lines P and S are parallel.

### Intermediate

**geomet-i-22d044248e** (pp_letters_both). The letters V, P, U, K and N are drawn on a square grid. How many of the letters have both perpendicular and parallel lines?

- A. 2 ✔
- B. 1: *missed_one_letter* (Missed one of the letters.)
- C. 3: *counted_letters_with_perpendicular_lines* (Counted the letters with perpendicular lines without checking for parallel lines too.)
- D. 4: *miscounted_the_letters* (Miscounted the letters.)

Solution: V: no perpendicular lines, no parallel lines → P: has perpendicular lines, 2 pairs of parallel lines → U: has perpendicular lines, 1 pair of parallel lines → K: has perpendicular lines, no parallel lines → N: no perpendicular lines, 1 pair of parallel lines → So the answer is 2.

### Competent

**geomet-c-0805fe551a** (grid_which_quadrilateral). Nurul draws four shapes on a square grid. Which shape is a parallelogram?

- A. A: *chose_a_trapezium* (That shape has only one pair of parallel sides.)
- B. B ✔
- C. C: *chose_a_kite* (That shape has no parallel sides.)
- D. D: *chose_a_trapezium* (That shape has only one pair of parallel sides.)

Solution: A parallelogram has two pairs of parallel sides. → Count the squares along each side to check which sides are parallel and equal. → Only one of the shapes is a parallelogram.

**geomet-c-9c94ca0bf3** (grid_triangle_type). Shu Fen draws Triangle S on a square grid. What type of triangle is Triangle S?

- A. isosceles triangle ✔
- B. right-angled triangle: *chose_right_angled* (None of its angles is a right angle.)
- C. right-angled isosceles triangle: *chose_right_angled_isosceles* (It has two equal sides but no right angle.)
- D. equilateral triangle: *chose_equilateral* (Its three sides are not all the same length.)

Solution: Two sides each go 4 squares one way and 2 the other way, so they are the same length. → None of the angles is a right angle. → Triangle S is an isosceles triangle.

**geomet-c-a5aa66aa52** (grid_point_triangle). Farid marks the points G, H, W, X, Y and Z on a square grid. Which point, when joined to G and H, forms a right-angled triangle?

- A. Z: *no_right_angle* (Triangle GHZ has no right angle (its largest angle is about 121°).)
- B. Y: *no_right_angle* (Triangle GHY has no right angle (its largest angle is about 70°).)
- C. X: *no_right_angle* (Triangle GHX has no right angle (its largest angle is about 166°).)
- D. W ✔

Solution: A right-angled triangle has one corner that is a right angle. → At H, one side goes 1 across and 4 down and the other goes 4 across and 1 down: they meet at a right angle. → So W forms a right-angled triangle with G and H.

**geomet-c-6b89bb643a** (pp_pick_pair_slanted). Kumar draws five lines, P, Q, R, S and T, on a square grid. Which two lines are parallel to each other?

- A. P and Q: *chose_lines_that_would_meet* (Lines P and Q would meet at about 18° if they were drawn longer, so they are not parallel.)
- B. Q and S ✔
- C. P and S: *chose_lines_that_would_meet* (Lines P and S would meet at about 18° if they were drawn longer, so they are not parallel.)
- D. R and T: *chose_lines_that_would_meet* (Lines R and T would meet at about 27° if they were drawn longer, so they are not parallel.)

Solution: Parallel lines slope the same way, so they never meet however long they are drawn. → Line Q goes 1 across for every 2 down. Line S goes 1 across for every 2 down. → So lines Q and S are parallel.

**geomet-c-fc028fbfd8** (pp_letters_parallel_pairs). The letters T, K, E, L, O and N are drawn on a square grid. How many of the letters have perpendicular lines but no parallel lines?

- A. 5: *forgot_no_parallel_lines* (Counted every letter with perpendicular lines, including those that also have parallel lines.)
- B. 3 ✔
- C. 4: *counted_one_letter_too_many* (Counted one letter too many.)
- D. 2: *missed_right_angles_between_slanting_lines* (Missed the right angles between slanting lines (count the squares: they meet at a right angle too).)

Solution: T: has perpendicular lines, no parallel lines → K: has perpendicular lines, no parallel lines → E: has perpendicular lines, 3 pairs of parallel lines → L: has perpendicular lines, no parallel lines → O: has perpendicular lines, 2 pairs of parallel lines → N: no perpendicular lines, 1 pair of parallel lines → So the answer is 3.

**percen-c-9b2a6c3a8d** (compare_more_less). Jun Wei has 25% more stickers than Shu Fen. Shu Fen has what percentage fewer stickers than Jun Wei?

- A. 125%: *gave_one_of_the_totals* (Gave one of the totals in units.)
- B. 75%: *gave_the_complement* (Gave 100% minus the percentage.)
- C. 25%: *gave_the_same_percentage* (Used the same percentage in both directions.)
- D. 20% ✔

Solution: Let Shu Fen have 100 units, so Jun Wei has 125 → Shu Fen has 25 fewer than Jun Wei → 25/125 × 100% = 20%
