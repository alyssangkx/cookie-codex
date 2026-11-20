# One past-paper pool per sub-topic, with milestones to competency

Status: **proposed** (owner to approve) · 21 Nov 2026 · Decision record: [ADR 0011](adr/0011-one-pool-per-sub-topic-milestones.md)

## Why

The aim is a student who is competent on the past-paper questions of every sub-topic: real PSLE and prelim questions,
which are already at exam level. The three difficulty tiers (Basic, Intermediate, Competent) were made for generated
questions written at three levels. For past papers they are artificial, and they split each sub-topic three ways, so few
sub-topics reach 20 questions per tier. With v1 of the site-ready list (21 Nov), one pool of 20 makes 24 of 35 Science
sub-topics playable instead of 8.

## The design (owner's words, 21 Nov 2026)

> The tiers should be measured by the number of questions attempted and correct. Wrong answers get recycled into the pool
> again, correct questions removed add to the competency count. More like milestones to achieve competency. Competency is
> majority of the past paper questions for a category attempted and correct.

1. **One pool per sub-topic.** All of a sub-topic's past-paper questions, no difficulty levels. Playable at 20 questions.
2. **Correct leaves the pool and counts; wrong goes back in.** A question answered correctly is removed from the pool and
   adds to the sub-topic's competency count. A question answered wrongly returns to the pool to be asked again.
3. **Competency = a majority of the sub-topic's past-paper questions answered correctly.** Shown as the sub-topic's
   competency badge (the "Exam-ready" badge of ADR 0010) and as a per-subject share on the training and parent pages.
4. **Three milestones on the way, each with its card.** The 3 cards per sub-topic stay; they are earned at milestones of
   the competency count instead of by clearing tiers. Cards already won stay.
5. **Easier first, without levels.** New questions are served in order of the tagger's difficulty, then their position in
   the paper, so a child warms up before the hardest ones. Every question counts the same.
6. **Generated questions are support only.** Only those that pass the past-paper precedent check (CLAUDE.md), used to fill
   a sub-topic that has fewer than 20 past-paper questions, and later as "try a similar one" after a wrong answer.
7. **Papers are the main check.** Timed prelim-style papers of past-paper questions only (the existing paper mode),
   submit-then-review as in ADR 0005.

## What changes in the code

| Today | After |
|---|---|
| `Tier` = basic/intermediate/competent; pools per (sub-topic, tier); `MIN_POOL` 20 per tier | One pool per sub-topic; `MIN_POOL` 20 per sub-topic |
| A tier clears when all its questions are retired; its card is awarded | Milestone *k* is reached when the competency count passes its threshold; its card is awarded |
| `tierOpen`: the next tier opens after the previous one | No gate: the whole sub-topic is open once playable |
| Perfect first try clears Basic or Intermediate at once | Dropped (no tiers to clear) |
| Tries per tier per day (5 for P1-P5, 3 for P6) | Tries per sub-topic per day, same numbers |
| `pick.ts`: due retests, then new, then not-due, then retired, within the tier | Due retests, then new questions easier-first, then not-due; retired questions only when nothing else is left |
| `train.ts`/rewards: 3 slots per sub-topic tied to tiers | The same 3 slots tied to milestones 1-3 (no reward moves) |

**Saves (ADR 0002: no schema bump).** The save keeps its three tier slots per sub-topic; they now mean milestones 1, 2
and 3 (`basic` = milestone 1, `intermediate` = 2, `competent` = 3). A slot already cleared stays cleared, so every card
won stays and counts as that milestone reached. Question states are keyed by question id and do not change. Questions
of generated banks that leave the site remain orphan states (kept, never deleted).

**The pool grows.** As more past papers are recovered, a sub-topic's pool gets bigger, so the competency share can fall.
A milestone or badge once reached is never taken away (as cleared tiers are never un-cleared today); the page shows the
current share.

## Open questions for the owner

1. **When does a wrong answer count once it is right?** (a) The next correct answer counts (simple, as stated above).
   (b) Keep the spaced retests: a question first answered wrongly counts only when it is right on a later day (one retest
   at 1 day; today's rule is 1, 3 and 7 days). Recommended: (b) with one retest, so a question cannot be counted from
   short-term memory a minute after seeing its answer.
2. **Milestone thresholds.** Recommended: milestone 1 at one sixth, milestone 2 at one third, milestone 3 at a majority
   (over half) = competency. Alternative: a quarter, a majority, all.
3. **Do generated fill-in questions count toward milestones?** Recommended: no; milestones and competency count
   past-paper questions only, generated ones are practice.
4. **Name on screen.** ADR 0010 calls the competency badge "Exam-ready" (since "Competent" was a tier name). With tiers
   gone, "Competent" is free. Keep "Exam-ready", or call it "Competent"?

## Rollout

1. Owner approves this note and ADR 0011 (and answers the open questions).
2. Build behind the existing past-paper switch: `store.ts` (pool, milestones, tries), `pick.ts` (order), `train.ts` and
   the tier page (milestones instead of tiers), the rewards preview, the parent page; tests for each rule.
3. Goes live together with the past-paper upload, so children see the change once.
