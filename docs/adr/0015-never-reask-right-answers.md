# A question answered right is never asked again; passage-set wrong answers are held

Status: **accepted** (owner, 27 Nov 2026) · Changes ADR 0011 (a one-pool quiz no longer refills with counted questions)

**Context.** The owner, testing Vocabulary MCQ: "questions that were answered correctly ... should be excluded from future
tests, only wrong answers are recycled. If wrong answers are within multi question passages, they can be excluded for the
time being ie not retested." Until now a tier or pool quiz short of new questions was topped up with retired (answered
right) questions so it was always 10, a cloze section re-asked a whole passage when one blank was due, and a practice
paper fell back to answered questions.

**Decision.**
- `pick.ts` never picks a retired question (`s 0`): tier and pool quizzes, cloze sections and practice papers. A quiz
  near the end of its pool is shorter; an empty one tells the child every question is done.
- A passage set is never asked again once any of its questions is answered; a set cut short carries on from its first
  unanswered question. A cloze section asks only passages with no blank answered.
- A wrong answer to a passage-set question is **held**: `QState.h = 1` on a retest state (`s > 0`). It stays a wrong
  answer, so it never counts as right, mastered, toward a milestone or toward clearing a tier, but nothing asks it or
  counts it as due (`isDue`, `inReview`, `pickTier`, `pickReview`, the parent's revision test and Retest buttons).
  Pending passage retests from before this change are held when a quiz page loads their bank (`holdPassageRetests`).

**Consequences.** For clearing, a held question counts as finished (`isFinished` in store.ts), so a tier and the next one
never lock while passage retests are off; it is never counted as mastered, right or toward a milestone. A question
already right is never turned into a held one. Retests come back on by deleting `h` (no other data is lost). An old tab
(an earlier build) ignores `h` and may ask a held question and drop the flag; the next load of its bank holds it again. Until a Daily Review has loaded
every bank, an old pending passage retest still shows in the Daily Review count; that review then holds it and may say
"Nothing to review today" once. Practice papers (owner, 27 Nov 2026): a question right the first time in a paper
retires, as in a tier quiz; a paper reuses questions corrected after a mistake (`s 0, w > 0`) but never one right the
first time. Papers still never clear tiers (they pass no tier ids).
