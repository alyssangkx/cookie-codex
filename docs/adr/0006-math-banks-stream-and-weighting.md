# Math banks: own random stream per template; weighting by nine years of paper marks

Status: accepted. Date: 20 Nov 2026. Source: `docs/todo.md` (Done), commit `975eeec`.

**Context.** Math questions come from parametric templates. One shared random stream makes a template's questions depend on which other templates exist, so ids and question sets shift whenever any template changes. Sub-topic sizes also did not follow what papers actually test.

**Decision.** Each template draws from its own random stream, so editing one template does not reshuffle the others. Question counts per sub-topic are weighted by their share of marks in the 2018-2026 papers (13,986 tagged items), and stems are rewritten in exam style.

**Consequences.** Most Math ids changed once (4,281 to 3,826 questions). Weights are recomputed when tags change (moved 3 sub-topics by 1 point or more; 3,818 questions). Speed is excluded because it is fading in the papers. Angles is below its weight and needs more templates.
