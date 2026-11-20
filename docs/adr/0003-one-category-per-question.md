# One category per question

Status: accepted. Date: 20 Nov 2026. Source: `scripts/quiz/check_dupes.py`, `docs/todo.md` (Done).

**Context.** Perfect classification of questions is not required, but a question filed under two sub-topics would be drilled and counted twice and would distort mastery and rewards.

**Decision.** Every question belongs to exactly one sub-topic: that of its first outcome id (trailing `-NN` removed). `check_dupes.py` fails if the same stem appears under two sub-topics within a subject.

**Consequences.** A question that fits two topics must be filed under one. Misfiling is tolerated; duplication is not.
