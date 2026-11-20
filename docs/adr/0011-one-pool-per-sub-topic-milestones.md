# One past-paper pool per sub-topic with milestones to competency, replacing difficulty tiers

Status: **accepted** · Date: 2026-11-21 · Source: owner, chat 21 Nov 2026 · Design: [past-paper-pools-design.md](../past-paper-pools-design.md)

**Context.** The aim is competence on the past-paper questions of every sub-topic. Past-paper questions are already at
exam level, and splitting each sub-topic into Basic, Intermediate and Competent pools of 20 leaves most sub-topics
unplayable (v1 site-ready list: 8 of 35 Science sub-topics with three tiers of 20, 24 of 35 with one pool of 20).

**Decision.** Each sub-topic has one pool of past-paper questions (playable at 20). A correct answer removes the question
from the pool and adds to the sub-topic's competency count; a wrong answer returns it to the pool. Competency is a
majority of the sub-topic's past-paper questions answered correctly. The three cards per sub-topic are earned at three
milestones of that count. New questions are served easier-first (tagger difficulty, then paper position) without
levels. Generated questions are support only (past-paper precedent required; fill-in under 20, later "try a similar
one").

**Consequences.** No save schema bump (ADR 0002): the three tier slots per sub-topic become milestones 1-3, cleared slots
stay, cards stay (ADR 0001). The tier gate, the perfect-first-try clear and per-tier tries go; tries per day apply per
sub-topic. A growing pool can lower the shown share, but a milestone once reached is never taken away. ADR 0010's
"Competent" tier name is retired; the badge stays "Exam-ready". Owner decisions: a wrongly answered question counts
only when right on a later day (one 1-day retest); milestones at 1/6, 1/3 and a majority; generated fill-ins never count.
