# Coverage of top-school question types

Each row is a question type found in the top-school P5/P6 papers (`scripts/quiz/math/patterns.json`). A type is covered when a generator names its id.

| Topic | Types | Covered | Missing |
|---|---|---|---|
| algebra | 5 | 5 | — |
| area | 10 | 10 | — |
| data | 7 | 7 | — |
| decimals | 5 | 5 | — |
| fractions | 16 | 16 | — |
| geometry | 10 | 10 | — |
| measurement | 6 | 6 | — |
| money | 5 | 5 | — |
| percentage | 6 | 6 | — |
| rate | 3 | 3 | — |
| ratio | 11 | 11 | — |
| whole | 19 | 19 | — |

**103 of 103 question types covered.**

Not counted (outside the 2021 syllabus, which has no Speed): math-pat-speed-distance-time-basic, math-pat-speed-two-runners-finish, math-pat-speed-catch-up-meet

## algebra

| Type | Level | Papers | Diagram | Generators |
|---|---|---|---|---|
| math-pat-true-false-not-possible-to-tell | intermediate | 59 |  | always_true_statement (intermediate) |
| math-pat-algebra-expression-from-context | intermediate | 50 |  | expression_two_events (intermediate) |
| math-pat-algebra-simplify-substitute | basic | 43 |  | simplify_basic (basic), substitute_basic (basic) |
| math-pat-algebra-equation-from-figure | intermediate | 15 | yes | equation_from_figure_triangle (intermediate), rectangle_perimeter_area (competent) |
| math-pat-algebra-workers-total | competent | 3 |  | workers_total (competent) |

## area

| Type | Level | Papers | Diagram | Generators |
|---|---|---|---|---|
| math-pat-area-triangle-rectangle-composite | intermediate | 142 | yes | composite_house (intermediate), rect_minus_triangle (intermediate), corner_two_points (competent), three_sides_points (competent), point_inside (competent) |
| math-pat-volume-cuboid-water-level | intermediate | 106 | yes | tank_water_volume (intermediate), depth_after_pour (intermediate), pour_into_tank (competent), solid_in_water (competent), pour_between_tanks (competent) |
| math-pat-circle-area-composite-shaded | competent | 81 | yes | shaded_square_family (competent), shaded_lens (competent), semis_area (competent), pond_path (competent) |
| math-pat-volume-count-unit-cubes | basic | 73 | yes | count_cubes (basic), cubes_to_fill (basic) |
| math-pat-circle-perimeter-composite | intermediate | 72 | yes | track_pa (intermediate), semis_perimeter (intermediate), rect_semi_pa (intermediate), square_arc_perimeter (intermediate) |
| math-pat-perimeter-area-identical-rectangles | competent | 50 | yes | identical_rects (competent) |
| math-pat-volume-cube-cuboid-direct | basic | 44 |  | cuboid_volume (basic), cube_volume (basic), find_dimension (intermediate) |
| math-pat-area-triangle-height-base | basic | 31 | yes | base_height_identify (basic) |
| math-pat-perimeter-composite-identical-pieces | intermediate | 29 | yes | identical_squares (intermediate) |
| math-pat-circumference-in-context | competent | 12 |  | wheel_revolutions (competent), loops_around (competent) |

## data

| Type | Level | Papers | Diagram | Generators |
|---|---|---|---|---|
| math-pat-table-bar-graph-reading | basic | 123 | yes | picture_read (basic), bar_read (basic), bar_extreme (basic), table_read (basic), line_read (basic), pie_basic (basic), bar_diff (intermediate), bar_total_two (intermediate), picture_total (intermediate), table_total (intermediate), line_change (intermediate), pie_amount (intermediate), pie_compare (competent), bar_percent (competent), picture_money (competent) |
| math-pat-average-find-missing | intermediate | 85 |  | find_missing_value (intermediate), two_equal_missing (competent) |
| math-pat-pie-chart-reading | intermediate | 59 | yes | pie_amount (intermediate), pie_compare (competent), pie_work_back (competent) |
| math-pat-graph-find-missing-from-average | intermediate | 58 | yes | avg_missing_bar (intermediate), bar_new_average (competent) |
| math-pat-line-graph-rate-and-time | intermediate | 39 | yes | line_rate (intermediate), line_reach (intermediate), line_extend (competent) |
| math-pat-average-direct | basic | 27 |  | average_direct (basic) |
| math-pat-average-extreme-value | competent | 10 |  | extreme_value (competent) |

## decimals

| Type | Level | Papers | Diagram | Generators |
|---|---|---|---|---|
| math-pat-fraction-to-decimal-rounded | basic | 91 |  | fraction_to_decimal (basic) |
| math-pat-decimal-operations-direct | basic | 59 |  | mult_by_digit (basic), div_by_digit (basic), mul_div_ten_powers (basic) |
| math-pat-place-value-decimals | basic | 40 |  | dec_place_value (basic), decimal_as_units (basic) |
| math-pat-decimal-add-subtract | basic | 38 |  | decimal_add_subtract (basic) |
| math-pat-decimal-compare-order | basic | 31 |  | dec_compare (basic), between_decimals (intermediate) |

## fractions

| Type | Level | Papers | Diagram | Generators |
|---|---|---|---|---|
| math-pat-fraction-successive-parts | intermediate | 104 |  | remainder_left (intermediate), remainder_backwards (competent), book_more_than_pen (competent), fixed_then_fraction (intermediate) |
| math-pat-fraction-operations-simplest | basic | 87 |  | frac_times_whole (basic), frac_div_whole (basic), whole_div_frac (basic), share_into_bags (intermediate), mixed_times_whole_context (competent) |
| math-pat-fraction-share-remainder | basic | 67 |  | share_remainder (basic) |
| math-pat-fraction-compare-order | basic | 57 |  | compare_order (basic) |
| math-pat-fraction-shaded-figure | basic | 54 | yes | shaded_figure (basic) |
| math-pat-fraction-division-share | basic | 49 |  | share_into_bags (intermediate), division_as_fraction (intermediate), division_share_compare (competent) |
| math-pat-fraction-of-quantity-left | basic | 39 |  | quantity_left (basic), add_subtract_story (competent) |
| math-pat-fraction-two-groups-sold-remainder | competent | 38 |  | two_groups_sold (competent) |
| math-pat-fraction-equivalent-improper-mixed | basic | 29 |  | improper_mixed (basic), missing_equivalent (intermediate), equivalent_in_context (competent), mixed_add_context (intermediate) |
| math-pat-fraction-same-share-two-quantities | competent | 27 |  | equal_fractions (competent) |
| math-pat-fraction-express-as-fraction-of | basic | 19 |  | express_as_fraction_of (basic) |
| math-pat-fraction-divide-by-fraction-pieces | intermediate | 12 |  | how_many_cups (intermediate) |
| math-pat-fraction-equal-use-per-day | intermediate | 11 |  | equal_use_per_day (intermediate) |
| math-pat-constant-part-new-fraction | competent | 7 |  | constant_part_new_fraction (competent), constant_part_add (competent), constant_part_remove (competent) |
| math-pat-fraction-part-difference-find-total | intermediate | 7 |  | more_boys_than_girls (intermediate) |
| math-pat-unequal-wholes-same-remainder | competent | 3 |  | unequal_wholes_same_remainder (competent) |

## geometry

| Type | Level | Papers | Diagram | Generators |
|---|---|---|---|---|
| math-pat-angles-chained-shapes | competent | 135 | yes | square_isosceles (competent), circle_chain (competent), butterfly_triangles (competent), ang_isosceles_exterior (competent), ang_rhombus_equilateral (competent), ang_square_isosceles (competent), rhombus_equilateral (competent), parallelogram_isosceles (competent), trapezium_isosceles (competent), collinear_isosceles (competent), rect_isosceles_chain (competent) |
| math-pat-angles-one-step | basic | 98 | yes | angles_on_line (basic), angles_at_point (basic), vertically_opposite (basic), angle_notation (basic), crossing_lines_algebra (intermediate), angle_ratio (intermediate), line_expressions (intermediate), reflex_angle (intermediate), ang_exterior_angle (intermediate), triangle_third_angle (basic), isosceles_basic (basic), exterior_angle (intermediate), isosceles_exterior (intermediate) |
| math-pat-painted-cubes-and-views | competent | 87 | yes | painted_cube (competent), stack_cubes (competent) |
| math-pat-symmetry-and-construction | basic | 75 | yes | lines_of_symmetry_count (basic), symmetric_letters (basic), which_dotted_line (basic), symmetric_figure_count (intermediate), regular_polygon_lines (intermediate), shade_to_symmetry (intermediate), symmetry_axes_pattern (competent), shade_two_lines (competent) |
| math-pat-direction-turn-compass | basic | 73 |  | compass_turn (basic), compass_two_turns (competent) |
| math-pat-angles-parallel-quadrilaterals | intermediate | 64 | yes | ang_quad_diagonal (intermediate), ang_trapezium_angles (intermediate), parallelogram_basic (basic), rhombus_diagonal (intermediate), trapezium_angles (intermediate), true_statements (intermediate), rhombus_equilateral (competent), parallelogram_isosceles (competent), trapezium_isosceles (competent) |
| math-pat-shapes-classify-2d | basic | 45 |  | shape_by_property (basic), grid_which_quadrilateral (competent), grid_triangle_type (competent) |
| math-pat-nets-and-solids | basic | 44 |  | solid_from_faces (basic) |
| math-pat-angles-folded-paper | competent | 41 | yes | folded_paper (competent), ang_folded_flap (competent) |
| math-pat-cubes-packing-scale | competent | 28 | yes | cube_packing (competent) |

## measurement

| Type | Level | Papers | Diagram | Generators |
|---|---|---|---|---|
| math-pat-order-mixed-units | basic | 60 |  | ruler_length (basic), order_measures (basic) |
| math-pat-time-elapsed-clock | basic | 47 |  | clock_plus_duration (basic) |
| math-pat-mass-whole-and-part | intermediate | 45 |  | whole_part_mass (intermediate), box_and_books (competent) |
| math-pat-measure-add-subtract-story | basic | 37 |  | measure_story (basic), add_compound (intermediate), subtract_compound (intermediate) |
| math-pat-unit-conversion-compound | basic | 19 |  | convert_decimal (basic) |
| math-pat-volume-reading-containers | basic | 8 | yes | read_beaker (basic) |

## money

| Type | Level | Papers | Diagram | Generators |
|---|---|---|---|---|
| math-pat-tariff-charge | intermediate | 94 |  | tariff_charge (intermediate) |
| math-pat-coins-notes-total-value | intermediate | 40 |  | coins_relationship (intermediate) |
| math-pat-promo-buy-n-get-free | intermediate | 22 |  | buy_n_get_free (intermediate) |
| math-pat-price-two-equations | competent | 22 |  | price_two_equations (competent) |
| math-pat-weekly-saving-cycle | intermediate | 3 |  | weekly_saving_cycle (intermediate) |

## percentage

| Type | Level | Papers | Diagram | Generators |
|---|---|---|---|---|
| math-pat-percent-gst-discount-direct | basic | 150 |  | discount_then_gst (intermediate), reverse_gst (competent) |
| math-pat-percent-reverse-find-original | intermediate | 78 |  | find_original_after_discount (intermediate), reverse_items_affordable (competent) |
| math-pat-percent-shaded-figure | basic | 48 | yes | percent_shaded_figure (basic) |
| math-pat-interest-deposit | intermediate | 19 |  | interest_deposit (intermediate) |
| math-pat-percent-two-groups-both-change | competent | 18 |  | two_groups_both_change (competent) |
| math-pat-simple-interest-loan | intermediate | 5 |  | simple_interest_loan (intermediate) |

## rate

| Type | Level | Papers | Diagram | Generators |
|---|---|---|---|---|
| math-pat-unitary-rate-basic | basic | 72 |  | total_from_rate (basic) |
| math-pat-tank-fill-drain-net-rate | competent | 21 | yes | tank_fill_drain (competent) |
| math-pat-two-machines-rate-work | competent | 12 |  | two_machines (competent) |

## ratio

| Type | Level | Papers | Diagram | Generators |
|---|---|---|---|---|
| math-pat-ratio-express-and-equivalent | basic | 94 |  | simplest_ratio (basic), missing_term (basic), ratio_with_units (basic) |
| math-pat-ratio-total-find-part | intermediate | 88 |  | three_way_share (intermediate), multiple_and_ratio (intermediate) |
| math-pat-ratio-fraction-conversion | basic | 74 |  | ratio_to_fraction (basic), fraction_to_ratio (basic) |
| math-pat-ratio-triangle-area-shared-height | intermediate | 43 | yes | triangle_area_shared_height (intermediate) |
| math-pat-ratio-one-changes-other-constant | competent | 28 |  | one_quantity_unchanged (competent) |
| math-pat-ratio-transfer-constant-total | competent | 15 |  | transfer_total_unchanged (competent), give_fraction_new_ratio (competent) |
| math-pat-ratio-difference-find-total | intermediate | 10 |  | ratio_difference_to_total (intermediate) |
| math-pat-ratio-one-quantity-constant | competent | 9 |  | one_quantity_unchanged (competent) |
| math-pat-ratio-same-amount-both-change | competent | 7 |  | ages_constant_difference (competent) |
| math-pat-ratio-three-way-share-remainder | competent | 6 |  | three_way_share_remainder (competent) |
| math-pat-square-sides-ratio-area-units | competent | 4 | yes | square_sides_area (competent) |

## whole

| Type | Level | Papers | Diagram | Generators |
|---|---|---|---|---|
| math-pat-growing-figure-pattern | intermediate | 96 | yes | growing_figure (intermediate) |
| math-pat-rounding-estimation | basic | 73 |  | round_whole (basic), estimate_sum (intermediate), estimate_product (intermediate) |
| math-pat-place-value-read-write | basic | 69 |  | numeral_from_words (basic), words_from_numeral (basic) |
| math-pat-multiples-factors-direct | basic | 62 |  | multiples_below_limit (intermediate) |
| math-pat-whole-number-four-ops-direct | basic | 59 |  | add_sub_algorithm (basic), mult_algorithm (basic), div_algorithm (basic), big_four_ops (basic) |
| math-pat-transfer-difference-change | competent | 53 |  | transfer_difference (competent), total_given_then_difference (competent) |
| math-pat-order-of-operations | basic | 53 |  | order_of_operations (basic), brackets (intermediate) |
| math-pat-whole-number-more-than-total-model | intermediate | 42 |  | more_than_total_model (intermediate) |
| math-pat-gap-overlap-counting | intermediate | 37 | yes | overlap_cards (intermediate), posts_gaps (intermediate) |
| math-pat-grouping-as-a-set | intermediate | 31 |  | coins_same_number (competent), set_cost (competent) |
| math-pat-age-problems | intermediate | 30 |  | age_problem (intermediate) |
| math-pat-form-numbers-from-digits | basic | 24 |  | form_number (basic), digit_cards_even_odd (competent), form_with_condition (intermediate) |
| math-pat-repeating-pattern-cycle-sum | intermediate | 21 |  | cycle_sum (intermediate) |
| math-pat-cutting-pieces-no-joining | intermediate | 17 |  | cutting_pieces (intermediate) |
| math-pat-working-backwards-transfers | competent | 16 |  | working_backwards_transfers (competent) |
| math-pat-two-quantities-two-prices-difference | competent | 12 |  | two_prices_difference (competent) |
| math-pat-equal-total-two-ways | competent | 10 |  | equal_total_two_ways (competent) |
| math-pat-number-pattern-grid | intermediate | 10 | yes | number_grid_column (intermediate) |
| math-pat-assumption-guess-and-check | competent | 9 |  | legs_assumption (competent) |

## Syllabus outcomes

**181 of 181 outcomes** are practised by at least one generator (or documented as skipped).

'secondary only' means the outcome is practised inside templates filed under another outcome of the same or a related sub-topic.

| Outcome | Level | Generators |
|---|---|---|
| whole-numbers-numbers-up-to-100-1000-10-000-100-000-and-10-million-01 | P1 | 2 templates |
| whole-numbers-numbers-up-to-100-1000-10-000-100-000-and-10-million-02 | P1 | secondary only (1 templates) |
| whole-numbers-numbers-up-to-100-1000-10-000-100-000-and-10-million-03 | P1 | 3 templates |
| whole-numbers-numbers-up-to-100-1000-10-000-100-000-and-10-million-04 | P1 | 3 templates |
| whole-numbers-numbers-up-to-100-1000-10-000-100-000-and-10-million-05 | P1 | 3 templates |
| whole-numbers-numbers-up-to-100-1000-10-000-100-000-and-10-million-06 | P1 | 3 templates |
| whole-numbers-numbers-up-to-100-1000-10-000-100-000-and-10-million-07 | P2 | 4 templates |
| whole-numbers-numbers-up-to-100-1000-10-000-100-000-and-10-million-08 | P2 | 4 templates |
| whole-numbers-numbers-up-to-100-1000-10-000-100-000-and-10-million-09 | P2 | secondary only (1 templates) |
| whole-numbers-numbers-up-to-100-1000-10-000-100-000-and-10-million-10 | P2 | secondary only (1 templates) |
| whole-numbers-numbers-up-to-100-1000-10-000-100-000-and-10-million-11 | P2 | secondary only (2 templates) |
| whole-numbers-numbers-up-to-100-1000-10-000-100-000-and-10-million-12 | P2 | 1 templates |
| whole-numbers-numbers-up-to-100-1000-10-000-100-000-and-10-million-13 | P3 | secondary only (1 templates) |
| whole-numbers-numbers-up-to-100-1000-10-000-100-000-and-10-million-14 | P3 | secondary only (2 templates) |
| whole-numbers-numbers-up-to-100-1000-10-000-100-000-and-10-million-15 | P3 | 1 templates |
| whole-numbers-numbers-up-to-100-1000-10-000-100-000-and-10-million-16 | P3 | secondary only (3 templates) |
| whole-numbers-numbers-up-to-100-1000-10-000-100-000-and-10-million-17 | P3 | secondary only (2 templates) |
| whole-numbers-numbers-up-to-100-1000-10-000-100-000-and-10-million-18 | P4 | 3 templates |
| whole-numbers-numbers-up-to-100-1000-10-000-100-000-and-10-million-19 | P4 | secondary only (2 templates) |
| whole-numbers-numbers-up-to-100-1000-10-000-100-000-and-10-million-20 | P4 | 3 templates |
| whole-numbers-numbers-up-to-100-1000-10-000-100-000-and-10-million-21 | P4 | 2 templates |
| whole-numbers-numbers-up-to-100-1000-10-000-100-000-and-10-million-22 | P4 | 2 templates |
| whole-numbers-numbers-up-to-100-1000-10-000-100-000-and-10-million-23 | P4 | 2 templates |
| whole-numbers-numbers-up-to-100-1000-10-000-100-000-and-10-million-24 | P5 | 2 templates |
| whole-numbers-addition-subtraction-multiplication-and-division-01 | P1 | 2 templates |
| whole-numbers-addition-subtraction-multiplication-and-division-02 | P1 | 2 templates |
| whole-numbers-addition-subtraction-multiplication-and-division-03 | P1 | 2 templates |
| whole-numbers-addition-subtraction-multiplication-and-division-04 | P1 | 3 templates |
| whole-numbers-addition-subtraction-multiplication-and-division-05 | P2 | secondary only (1 templates) |
| whole-numbers-addition-subtraction-multiplication-and-division-06 | P2 | secondary only (1 templates) |
| whole-numbers-addition-subtraction-multiplication-and-division-07 | P2 | 2 templates |
| whole-numbers-addition-subtraction-multiplication-and-division-08 | P2 | 2 templates |
| whole-numbers-addition-subtraction-multiplication-and-division-09 | P3 | 1 templates |
| whole-numbers-addition-subtraction-multiplication-and-division-10 | P3 | 1 templates |
| whole-numbers-addition-subtraction-multiplication-and-division-11 | P3 | 2 templates |
| whole-numbers-addition-subtraction-multiplication-and-division-12 | P3 | 3 templates |
| whole-numbers-addition-subtraction-multiplication-and-division-13 | P3 | 2 templates |
| whole-numbers-addition-subtraction-multiplication-and-division-14 | P3 | 2 templates |
| whole-numbers-addition-subtraction-multiplication-and-division-15 | P4 | 12 templates |
| whole-numbers-addition-subtraction-multiplication-and-division-16 | P4 | 3 templates |
| whole-numbers-addition-subtraction-multiplication-and-division-17 | P5 | 1 templates |
| whole-numbers-addition-subtraction-multiplication-and-division-18 | P5 | 1 templates |
| whole-numbers-addition-subtraction-multiplication-and-division-19 | P5 | 3 templates |
| whole-numbers-factors-and-multiples-01 | P4 | secondary only (6 templates) |
| whole-numbers-factors-and-multiples-02 | P4 | 1 templates |
| whole-numbers-factors-and-multiples-03 | P4 | 4 templates |
| whole-numbers-factors-and-multiples-04 | P4 | 1 templates |
| whole-numbers-factors-and-multiples-05 | P4 | 6 templates |
| fractions-fraction-of-a-whole-and-of-a-set-01 | P2 | 1 templates |
| fractions-fraction-of-a-whole-and-of-a-set-02 | P2 | 3 templates |
| fractions-fraction-of-a-whole-and-of-a-set-03 | P4 | 10 templates |
| fractions-equivalent-fractions-and-simplest-form-01 | P3 | 3 templates |
| fractions-equivalent-fractions-and-simplest-form-02 | P3 | 2 templates |
| fractions-equivalent-fractions-and-simplest-form-03 | P3 | 1 templates |
| fractions-equivalent-fractions-and-simplest-form-04 | P3 | 1 templates |
| fractions-mixed-numbers-and-improper-fractions-01 | P4 | 3 templates |
| fractions-addition-and-subtraction-of-fractions-01 | P2 | 3 templates |
| fractions-addition-and-subtraction-of-fractions-02 | P3 | 3 templates |
| fractions-addition-and-subtraction-of-fractions-03 | P4 | 2 templates |
| fractions-addition-and-subtraction-of-fractions-04 | P5 | 1 templates |
| fractions-multiplication-and-division-of-fractions-01 | P5 | 1 templates |
| fractions-multiplication-and-division-of-fractions-02 | P5 | 5 templates |
| fractions-multiplication-and-division-of-fractions-03 | P5 | 3 templates |
| fractions-multiplication-and-division-of-fractions-04 | P5 | 3 templates |
| fractions-multiplication-and-division-of-fractions-05 | P6 | 3 templates |
| fractions-multiplication-and-division-of-fractions-06 | P6 | 2 templates |
| fractions-fraction-and-division-01 | P5 | 2 templates |
| fractions-fraction-and-division-02 | P5 | 1 templates |
| decimals-decimal-notation-and-comparison-01 | P4 | 2 templates |
| decimals-decimal-notation-and-comparison-02 | P4 | 5 templates |
| decimals-decimal-notation-and-comparison-03 | P4 | 2 templates |
| decimals-decimal-notation-and-comparison-04 | P4 | 2 templates |
| decimals-decimal-notation-and-comparison-05 | P4 | 2 templates |
| decimals-four-operations-with-decimals-01 | P4 | 5 templates |
| decimals-four-operations-with-decimals-02 | P4 | 6 templates |
| decimals-four-operations-with-decimals-03 | P4 | 1 templates |
| decimals-four-operations-with-decimals-04 | P4 | 1 templates |
| decimals-four-operations-with-decimals-05 | P5 | 1 templates |
| decimals-four-operations-with-decimals-06 | P5 | 2 templates |
| money-money-01 | P1 | secondary only (3 templates) |
| money-money-02 | P2 | 3 templates |
| money-money-03 | P2 | 1 templates |
| money-money-04 | P2 | 2 templates |
| money-money-05 | P2 | 1 templates |
| money-money-06 | P3 | 10 templates |
| percentage-percentage-01 | P5 | 3 templates |
| percentage-percentage-02 | P5 | 6 templates |
| percentage-percentage-03 | P5 | 7 templates |
| percentage-percentage-04 | P6 | 6 templates |
| percentage-percentage-05 | P6 | 2 templates |
| rate-rate-01 | P5 | 4 templates |
| rate-rate-02 | P5 | 13 templates |
| ratio-ratio-01 | P6 | 5 templates |
| ratio-ratio-02 | P6 | 6 templates |
| ratio-ratio-03 | P6 | 6 templates |
| ratio-ratio-04 | P6 | 1 templates |
| ratio-ratio-05 | P6 | 2 templates |
| ratio-ratio-06 | P6 | 1 templates |
| ratio-ratio-07 | P6 | 2 templates |
| algebra-algebra-01 | P6 | 2 templates |
| algebra-algebra-02 | P6 | 1 templates |
| algebra-algebra-03 | P6 | 3 templates |
| algebra-algebra-04 | P6 | 3 templates |
| algebra-algebra-05 | P6 | 11 templates |
| measurement-length-mass-and-volume-01 | P1 | 1 templates |
| measurement-length-mass-and-volume-02 | P1 | 4 templates |
| measurement-length-mass-and-volume-03 | P1 | 4 templates |
| measurement-length-mass-and-volume-04 | P2 | 1 templates |
| measurement-length-mass-and-volume-05 | P2 | 1 templates |
| measurement-length-mass-and-volume-06 | P3 | 3 templates |
| measurement-length-mass-and-volume-07 | P3 | 11 templates |
| measurement-length-mass-and-volume-08 | P3 | 3 templates |
| measurement-time-01 | P1 | 1 templates |
| measurement-time-02 | P2 | 1 templates |
| measurement-time-03 | P2 | 2 templates |
| measurement-time-04 | P3 | 2 templates |
| measurement-time-05 | P3 | 10 templates |
| measurement-time-06 | P3 | 2 templates |
| area-and-volume-area-and-perimeter-01 | P3 | secondary only (1 templates) |
| area-and-volume-area-and-perimeter-02 | P3 | 1 templates |
| area-and-volume-area-and-perimeter-03 | P3 | 3 templates |
| area-and-volume-area-and-perimeter-04 | P3 | 3 templates |
| area-and-volume-area-and-perimeter-05 | P4 | 3 templates |
| area-and-volume-area-and-perimeter-06 | P4 | 1 templates |
| area-and-volume-area-and-perimeter-07 | P4 | 6 templates |
| area-and-volume-area-of-triangle-01 | P5 | 1 templates |
| area-and-volume-area-of-triangle-02 | P5 | 7 templates |
| area-and-volume-area-of-triangle-03 | P5 | 5 templates |
| area-and-volume-volume-of-cube-and-cuboid-01 | P5 | 2 templates |
| area-and-volume-volume-of-cube-and-cuboid-02 | P5 | secondary only (4 templates) |
| area-and-volume-volume-of-cube-and-cuboid-03 | P5 | 4 templates |
| area-and-volume-volume-of-cube-and-cuboid-04 | P5 | 4 templates |
| area-and-volume-volume-of-cube-and-cuboid-05 | P5 | 7 templates |
| area-and-volume-volume-of-cube-and-cuboid-06 | P5 | 2 templates |
| area-and-volume-volume-of-cube-and-cuboid-07 | P6 | 1 templates |
| area-and-volume-volume-of-cube-and-cuboid-08 | P6 | 1 templates |
| area-and-volume-volume-of-cube-and-cuboid-09 | P6 | 1 templates |
| area-and-volume-volume-of-cube-and-cuboid-10 | P6 | 1 templates |
| area-and-volume-volume-of-cube-and-cuboid-11 | P6 | skipped: Placeholder: the syllabus line lost its symbols in PDF extraction (marked unverified). |
| area-and-volume-area-and-circumference-of-circle-01 | P6 | 6 templates |
| area-and-volume-area-and-circumference-of-circle-02 | P6 | 2 templates |
| area-and-volume-area-and-circumference-of-circle-03 | P6 | 8 templates |
| geometry-2d-shapes-01 | P1 | 5 templates |
| geometry-2d-shapes-02 | P1 | 1 templates |
| geometry-2d-shapes-03 | P1 | 2 templates |
| geometry-2d-shapes-04 | P1 | 3 templates |
| geometry-2d-shapes-05 | P2 | 2 templates |
| geometry-3d-shapes-and-nets-01 | P2 | 5 templates |
| geometry-3d-shapes-and-nets-02 | P4 | 2 templates |
| geometry-3d-shapes-and-nets-03 | P4 | 3 templates |
| geometry-3d-shapes-and-nets-04 | P4 | 2 templates |
| geometry-3d-shapes-and-nets-05 | P4 | 1 templates |
| geometry-angles-01 | P3 | 3 templates |
| geometry-angles-02 | P4 | 1 templates |
| geometry-angles-03 | P4 | 1 templates |
| geometry-angles-04 | P4 | 3 templates |
| geometry-angles-05 | P5 | 2 templates |
| geometry-angles-06 | P5 | 2 templates |
| geometry-angles-07 | P5 | 3 templates |
| geometry-angles-08 | P5 | 11 templates |
| geometry-perpendicular-and-parallel-lines-01 | P3 | 4 templates |
| geometry-perpendicular-and-parallel-lines-02 | P3 | 2 templates |
| geometry-rectangle-and-square-01 | P4 | 8 templates |
| geometry-rectangle-and-square-02 | P4 | 3 templates |
| geometry-line-symmetry-01 | P4 | 5 templates |
| geometry-line-symmetry-02 | P4 | 3 templates |
| geometry-line-symmetry-03 | P4 | secondary only (2 templates) |
| geometry-triangles-parallelogram-rhombus-and-trapezium-01 | P5 | 2 templates |
| geometry-triangles-parallelogram-rhombus-and-trapezium-02 | P5 | 1 templates |
| geometry-triangles-parallelogram-rhombus-and-trapezium-03 | P5 | 2 templates |
| geometry-triangles-parallelogram-rhombus-and-trapezium-04 | P5 | 3 templates |
| geometry-triangles-parallelogram-rhombus-and-trapezium-05 | P5 | 2 templates |
| geometry-triangles-parallelogram-rhombus-and-trapezium-06 | P6 | 4 templates |
| data-representation-and-interpretation-picture-graphs-bar-graphs-tables-line-graphs-and-pie-charts-01 | P1 | 1 templates |
| data-representation-and-interpretation-picture-graphs-bar-graphs-tables-line-graphs-and-pie-charts-02 | P2 | 2 templates |
| data-representation-and-interpretation-picture-graphs-bar-graphs-tables-line-graphs-and-pie-charts-03 | P3 | 9 templates |
| data-representation-and-interpretation-picture-graphs-bar-graphs-tables-line-graphs-and-pie-charts-04 | P3 | secondary only (4 templates) |
| data-representation-and-interpretation-picture-graphs-bar-graphs-tables-line-graphs-and-pie-charts-05 | P4 | 3 templates |
| data-representation-and-interpretation-picture-graphs-bar-graphs-tables-line-graphs-and-pie-charts-06 | P4 | 11 templates |
| data-analysis-average-of-a-set-of-data-01 | P6 | 4 templates |
| data-analysis-average-of-a-set-of-data-02 | P6 | 12 templates |
