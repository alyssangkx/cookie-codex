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
| math-pat-angles-chained-shapes | competent | 135 | yes | square_isosceles (competent), circle_chain (competent), butterfly_triangles (competent), rhombus_equilateral (competent), parallelogram_isosceles (competent), trapezium_isosceles (competent), collinear_isosceles (competent), rect_isosceles_chain (competent) |
| math-pat-angles-one-step | basic | 98 | yes | angles_on_line (basic), angles_at_point (basic), vertically_opposite (basic), angle_notation (basic), crossing_lines_algebra (intermediate), angle_ratio (intermediate), line_expressions (intermediate), reflex_angle (intermediate), triangle_third_angle (basic), isosceles_basic (basic), exterior_angle (intermediate), isosceles_exterior (intermediate) |
| math-pat-painted-cubes-and-views | competent | 87 | yes | painted_cube (competent), stack_cubes (competent) |
| math-pat-symmetry-and-construction | basic | 75 | yes | lines_of_symmetry_count (basic), symmetric_letters (basic), which_dotted_line (basic), symmetric_figure_count (intermediate), regular_polygon_lines (intermediate), shade_to_symmetry (intermediate), symmetry_axes_pattern (competent), shade_two_lines (competent) |
| math-pat-direction-turn-compass | basic | 73 |  | compass_turn (basic), compass_two_turns (competent) |
| math-pat-angles-parallel-quadrilaterals | intermediate | 64 | yes | parallelogram_basic (basic), rhombus_diagonal (intermediate), trapezium_angles (intermediate), true_statements (intermediate), rhombus_equilateral (competent), parallelogram_isosceles (competent), trapezium_isosceles (competent) |
| math-pat-shapes-classify-2d | basic | 45 |  | shape_by_property (basic) |
| math-pat-nets-and-solids | basic | 44 |  | solid_from_faces (basic) |
| math-pat-angles-folded-paper | competent | 41 | yes | folded_paper (competent) |
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
