# Game Design Review: Cookie Codex PSLE Quiz

Reviewed 2026-11-17 (snapshot 11:12 local). Subject: `docs/game-design.md` plus what is actually built.
Method lenses (read by hand from the game-studios template, no scripts run):
**[ECO]** economy-designer (faucets/sinks, curves with worked values, reward psychology, health metrics),
**[SYS]** systems-designer, **[BAL]** balance-check Phase 4 (progression and loot checks) and Phase 5 report format,
**[DR]** design-review single-doc checklist, **[ACC]** accessibility-specialist.
Filter applied to everything: does it get more correct, spaced, appropriately hard PSLE practice done?

Content snapshot at review time (banks are still being generated, so numbers will drift): 4 Math banks
(`math-fractions` 352 Qs, `math-percentage` 300, `math-rate` 300, `math-ratio` 300 = 1,252). **20 of 93 Math tiers are
playable** (>= 20 questions): equivalent fractions B; fraction of a whole B/I/C; mixed numbers B; add/sub fractions B/I;
fraction and division B; mult/div fractions B/I/C; rate B/I/C; percentage B/I/C; ratio B/I/C. Answer positions are balanced
(about 25% each), no duplicate stems, all 4-option MCQs; the bank itself looks sound.

## Health summary: CONCERNS

The learning loop (spaced retest, 8/10 on two days, no money, no loot boxes, previewed rewards, "Not yet" copy) is well
conceived and the numbers behind pass rules are mostly sane. But several built behaviours undermine the stated purpose:
a tier can be credited without any pass, papers and abandoned quizzes silently drain tier pools, the clock runs while the
child reads worked solutions, the retest queue grows without bound, the streak breaks on every 5-day-a-week routine, and
card power is nearly constant. None is a dark pattern in the monetisation sense; two (streak, reward-for-failing) lean that
way. Nothing is CRITICAL because nothing harms the child, but items 1-3 below should be fixed before the monster work.

## Findings, ranked

### HIGH

**H1. Tiers can be credited with zero passes, and papers/abandoned quizzes drain pools.** [SYS exploit scan, ECO faucet]
Evidence: `quiz/index.astro` `init()`: if `pickTier` returns nothing the tier is `autoCredit`ed and the card awarded.
`answer()` is called per question inside `choose()`, so every paper question (`mode=paper`), review question and
every question of a quiz the child closes before the end retires or queues the question. `pickTier` only draws unseen
questions, so a 20-question WA paper over Ratio retires about 15 of a 25-question tier pool. Tier pools are 25/34/50 in
Fractions. `attemptsToday` counts only finished attempts, so abandoning gives unlimited tries. Also `pickTier` shrinks the
quiz when few questions remain, and the pass test is `score/total >= 0.8`: a 1-question quiz passes on a 25% guess, a
3-question quiz on 1.6% twice.
Fix: (a) auto-credit only if `passes.length >= 1` and the last 10 answers on the tier were >= 80%, otherwise reopen the pool
by recycling retired questions oldest-first; (b) a pass quiz must have exactly 10 questions: if fewer than 10 unseen remain,
top up with retired questions (not counted as retiring); (c) papers and reviews must not call `answer()` for unseen
questions (log to `attempts` only, advance a retest only if due); (d) write the attempt row at quiz start and finalise it at
the end, so abandoning counts as a try.

**H2. The timer runs while the child reads the worked solution.** [DR learning-purpose, ACC timing]
Evidence: `deadline` is fixed at `begin()`; after each answer `choose()` shows a multi-step solution and the clock keeps
running. Limits are 12/15/20 min for 10 Qs (1.2/1.5/2.0 min each), the PSLE-pace figure, but the child is also expected to
read a "why this was tempting" note and 2-4 solution steps. The incentive is to skip feedback, which is the highest-value
learning in the game. Time-up also calls `finish(true)` with no warning or announcement.
Fix: pause the clock while the feedback panel is open (timer measures only reading and answering the question); keep the
per-question budget. Add a visible "untimed practice" mode that cannot clear a tier but retires nothing, for anxious days.

**H3. Retest backlog grows without bound; capacity cannot clear it.** [ECO flow balance, SYS feedback loops]
Evidence: `pickTier` takes at most `min(3, floor(0.3 x 10))` due retests, and only from the same tier; `pickReview` returns at
most 5 across everything. A wrong answer needs 3 further correct appearances (steps 1, 3, 7 days); at 70% recall that is
about 4.3 appearances per wrong item (3 / 0.7). At 80% fresh accuracy a fresh quiz creates 2 wrong items, so about 8.6 retest
appearances per fresh quiz. At 1.5 fresh quizzes a day that is about 13 appearances a day against a ceiling of about 9.5
(3 x 1.5 same-tier + 5 review), and in practice far less because tier-quiz retests only come from the tier being played.
The queue grows by several items a day for the whole run, so old retests would never come back before PSLE.
Fix: make the Daily Review 10 questions (or 8 + 2 fresh) when the due count exceeds 10, count a Review as half a quiz
toward the goal, and let a tier quiz take due retests from the same *sub-topic* (any tier) up to the 30% cap. Show the parent
"due now / overdue 7+ days".

**H4. Streak breaks on every normal week; the design says it will not.** [ECO reward psychology, DR well-being]
Evidence: `bumpStreak` keeps the streak only if the last study day was yesterday, or two days ago with the weekly freeze
unused. A 5-days-a-week routine (the design's own planning basis, 226 active days) misses Sat and Sun, a 3-day gap,
so the streak resets to 1 every Monday. Design section 6 promises "rest days never break it". `liveStreak` shows
"No streak yet" or "N-day streak" on the home card.
Fix: track the streak in *weeks*: a week is kept if it has >= 4 goal days (parent-editable); display "N weeks in a row".
Never show "No streak yet"; show "best N weeks" and total study days. Streak must not gate any card (it does not today; keep it).

### MEDIUM

**M1. Reward preview is wrong for most playable tiers.** [ECO reward psychology, DR "previewed" rule]
Evidence: of the first 20 playable tiers, 11 are star slots ("Reward: +1 star for X", `[sub].astro` line 31), but their target
card is one earned in a sub-topic the child has not reached (for example Fraction of a whole B is a dup of a common that
belongs to a no-question slot). `award()` creates the card when absent and returns "New card!". So the preview says
"+1 star" and the result says "New card!". It is honest in effect but breaks the "previewed" promise, and it means the star
mechanic is almost invisible while only part of Math is playable.
Fix: build the dup target from cards the student can actually own earlier in the *playable* order, or show the preview as
"A card from the Basic set" until owned. Rebuild rewards with content-aware order (see Rarity section).

**M2. Retire-on-first-correct lets lucky guesses through, and the entry rate is high.** [SYS, DR learning]
Evidence: `answer()`: a new question answered correctly goes straight to `s: 0`. With 4 options a guess is right 25%.
Share of retired items that were guesses: mastery 50% gives 20%; 70% gives 9.7%; 85% gives 4.2%. The retest ladder
itself is sturdy (guessing three steps in a row is 1.6%), but only items that were *wrong* ever enter it. Because a
guessed-correct item is never seen again, the weakest topics have the leakiest retirement.
Fix: new correct answers enter the ladder at step 2 (due in 3 days) when the quiz time on that question was under 5 s, or
the tier is Competent, or the child changed their answer; otherwise keep retire. Simpler: retire only after a second correct
on a *later day* for Competent tier (stage "confirm", one extra appearance). Keep it capped by the 30% rule.

**M3. 8/10 on 10 questions is a decent but noisy gate; two days make it good.** [BAL progression, SYS]
Worked values (binomial, guess 25% on unknown items; mastery a gives p = a + 0.25(1-a)):

| True mastery | P(>=8/10) one quiz | Two passes on two days |
|---|---|---|
| 50% | 0.21 | 0.045 |
| 60% | 0.38 | 0.147 |
| 70% | 0.60 | 0.362 |
| 80% | 0.82 | 0.673 |
| 90% | 0.97 | 0.933 |
| pure guess | 0.0004 | about 0 |

So guessing alone never clears a tier, and a 60% child clears with probability 15% on a given pair (and gets feedback
each time). A 70% child needs about 2.8 passes-days, an 80% child 1.5. This is reasonable; the real leaks are H1 and M2.
A 90%-mastery child fails the first quiz 3% of the time and can still be blocked by 3 tries/day, which is fine.
Recommendation: keep 8/10, but require the two passes to use *disjoint* questions (true today only because passed items
retire) and keep the 10-question minimum from H1(b).

**M4. Card power is nearly constant, so it is a decoration.** [ECO, BAL progression curves]
Evidence: `store.ts` `power = round(acc x (1 + 0.05(stars-1)))` capped at 100; `acc` is the mean of the best two *passing*
quizzes, so `acc` is always 80-100 (auto-credited tiers default to `acc = 100`). Design thresholds: below 60 gives +15 s,
60-84 gives +30 s, 85+ gives hint x2. The below-60 band is unreachable and 60-84 is reached only by 80-84% cards with 1-2
stars. A 1-star 90% card = 90, a 5-star 85% card = 102 -> 100. `acc` is set once at `award()` and never updated, although the
design says retraining updates it. Maximum stars in Math: 3, on 24 cards.
Fix: define power on *retention*, not first-pass: `power = round(100 x (0.5 x acc_two_best + 0.5 x retention))` where
retention = share of the card's source-sub-topic questions currently retired or at step 3 (0-1), plus `+4 x (stars-1)`.
Update on every Daily Review. Range then spans about 40-100 and responds to practice.

**M5. Daily goal and streak count a quiz, not effort.** [ECO exploit, DR]
Evidence: `finishQuiz` increments `quizzes` for tier, paper and review modes alike; a 5-question Daily Review (or a
rapid-click 0/10 quiz) meets "2 quizzes" and bumps the streak; `d.min += round(ms/60000)` records 0 minutes for a 20 s quiz.
Fix: goal unit = 10 answered questions (review of 5 counts as 5), with a floor of 3 minutes of play, so goal and cap speak
the same language (answered questions and minutes).

**M6. Spaced intervals drift and can be skipped.** [SYS, DR]
Evidence: `due = now + n x 86,400,000` (24-hour blocks, not calendar days) so a retest set at 7 pm Monday is not due for a
child studying at 5 pm Tuesday. Not-due retests also fill short pools (`pickTier` spare list) and `answer()` advances them,
so a step-1 item answered correctly the same day jumps to step 2, defeating spacing. Papers do the same.
Fix: `due = start of local day + n`; an out-of-schedule correct answer leaves the step unchanged (no advance, no retire).

**M7. Band gate and prerequisite rules are designed but not built.** [DR completeness]
Evidence: `tierOpen` only checks Basic then Intermediate then Competent. The P-band gate (60% of previous band) and the
"sub-topic n+1 needs n Intermediate" rule do not exist, so all 31 Math sub-topics are open from day one. That is actually
kinder for a P6 child with sparse content, but the design text should say so or the rules should be built.

### LOW

**L1. Parent settings can create an impossible day.** `clamp(cap, 15, 90)` and `clamp(goal, 1, 5)` are independent. A cap of
15 min with a goal of 2 quizzes (12 + 15 min limits) can never be met, so the streak cannot grow. Validate goal x average quiz
minutes <= cap.

**L2. Cap is checked at the start only; the in-progress quiz finishes.** Acceptable (design says so), but a Competent quiz
at x1.5 extra time can overshoot by 30 min. Cap overshoot bound should be stated to the parent.

**L3. Timer low-time signal is colour only.** [ACC] See Accessibility.

## 1. Pacing (question 1)

Real rules used: 8/10 twice on different days, max 3 tries per tier per day, one counted pass per day per tier,
limits 12/15/20 min, 20% of minutes reserved for Daily Review, 226 active days (5 days/week from 17 Nov 2026 to 30 Sep
2027: 317 calendar days), a quiz costs 80% of its limit, tiers unlock in order B, I, C, the student plays the first
uncleared tier in sub-topic order. Monte Carlo, 200 runs ([ECO] Phase "progression curve"; script `sim.py` in the temp folder).
Mastery 0.75 means P(pass a quiz) = 0.72 (pq 0.81); 0.85 means 0.91.

**If all 93 Math tiers had questions (the design's own scope, Math only):**

| Min/day | Mastery | Tiers by 30 Sep | Distinct cards | Stars | Longest gap between new cards | Last clear on active day |
|---|---|---|---|---|---|---|
| 20 | 0.75 | 81 | 51 | 30 | 15 days | 224 (budget exhausted) |
| 25 | 0.75 | 91 | 58 | 34 | 13 days | 222 |
| 30 | 0.75 | 93 | 59 | 34 | 11 days | 184 |
| 20 | 0.85 | 93 | 59 | 34 | 11 days | 204 |
| 25 | 0.85 | 93 | 59 | 34 | 10 days | 184 |
| 30 | 0.85 | 93 | 59 | 34 | 9 days | 150 |

**What is playable today (20 tiers):** all 20 tiers clear on active day 43-54 at 20 min (0.75-0.85), day 35-44 at 25 min,
day 29-36 at 30 min, giving about 18 distinct cards and 2 stars. After that the game has nothing to clear.

Findings from the table:
- The design's table (100/125/150 tiers, 64/80/96 cards, 36/45/54 stars) is for four schools. For Math alone the pool is 93
  tiers, 59 cards and 34 stars, and it is **reached** at 30 min/day (or at 20 min if the child is strong). The design
  statement "the pool does not run out" is true for the full game, false for Math-only.
- Real binding constraint is content, not time: at 20 minutes a child clears the whole playable set in about 7-11 weeks
  (to roughly late January 2027), then has only Daily Review, papers and retests until the remaining banks arrive.
  The MVP estimate "about 2 weeks" was for 2 sub-topics; with 20 tiers it is 5-8 weeks, still far short of the 44 weeks to PSLE.
- Dead zones (full build): gaps of up to 15 days without a *new* card occur because 34 of 93 slots are star slots and they cluster
  (run of 4 dups in depth-first order, 2 in breadth-first order). With only 20 playable tiers the longest gap is 3-5 active days.
- Power spikes: Competent legendaries (Ratio C, Rate C, Add/Sub C) land at the end of each topic, which is the right place, but
  because only 2 of Math's legendaries are new cards (the rest are duplicates), the "big moment" is a +1 star on an unowned card.
- Time cost per tier at mastery 0.75: about 2.8 attempts x (12/15/20 x 0.8) min = 27/34/45 min, mean 35 min (design says 36;
  reasonable). Competent costs 1.7x Basic for the same single card, which matches the intent.

## 2. Economy (question 2)

Faucets: tier clears (card or star), milestones (not built). Sinks: none (stars are free, power feeds unbuilt boosts). [ECO]
- **Inflation:** none in the money sense. The only inflation is *power compression* (M4): all cards sit at 80-100.
- **Pointless cards:** (a) the 14 duplicates a student gets on their own earlier cards, since stars add 0-20% to a number that
  is capped at 100; (b) any card equipped for boosts, since boosts do not exist yet. Cards are still collectables with portraits
  and backstories, which is a fine intrinsic reward; they are not pointless as a Codex, only as power items.
- **Autocredit** gives `acc = 100`, so the most "powerful" cards are those a child never passed (H1).
- **Ancient unlocks (2n legendaries at 2 stars or more):** Math contains only **2 new legendaries**; their duplicate counts are
  3 and 1, so both can reach 2 stars only after clearing at least 4 specific Competent slots deep in the P5/P6 order.
  Ancient 1 (2 legendaries at 2 stars) is therefore reachable only at the very end of Math and only if every dup slot lands on
  one of the two; Ancients 2-5 (4, 6, 8, 10 legendaries) need Science/English/Chinese content. The eleven legendaries across
  all schools make Ancient 5 require owning **10 of 11 at 2 stars**, which needs all four schools plus lucky dup placement.
  Verdict: Ancient 1 is plausible before PSLE only with full Math at 25+ min; Ancients 2-5 are not reachable before PSLE.
  Recommendation: define the unlock on *owned legendaries or super-epics at 2 stars*, `n` ancients needing `n + 1` such cards
  (2, 3, 4, 5, 6), and let any dup of the same tier class bump a star (not a random card).
- Health metrics to add [ECO]: median days between new cards, share of clears that are stars, share of cards >= 2 stars, retired
  vs due question ratio per sub-topic, autocredit count.

## 3. Rarity mapping (question 3)

Evidence from `build_rewards.py` and `rewards.json`: Math order is sorted by home level, and the first seven Math sub-topics are
P2/P3 items with **no questions** (geometry 2D, money, length/mass/volume, time, perpendicular lines, etc.). The seven commons
are Basic rewards for those slots (slots 0-6). Playable content starts at slot 1 (equivalent fractions B = common) then slot
7+. Today's playable Basic rewards are: 1 common (equivalent fractions), 6 epics, and 3 *duplicates of commons* (fraction of
a whole, rate, percentage Basic). Competent rewards: Ratio C and Rate C are legendary **duplicates**; mult/div C is a new
super-epic. So the child's first content gives epics and a handful of commons, while 6 of 7 commons sit on content that has no
questions, as suspected. The Competent legendaries sit on the capstones only, which is right, but two of three playable
legendary slots are star slots.

Recommended fix (order-independent, in `build_rewards.py`):
1. Sort sub-topics by **playable-first** (has content, then home level), not by home level alone; regenerate when a new bank lands.
2. Reserve commons for the first 7 *playable* Basic tiers; map the remaining commons-class cards (special, epics) after.
3. Place legendaries on the first Competent tier of each *playable topic capstone*; make the dups point only to cards already
   owned *at that point in the playable order*, so "+1 star" always means a card the child holds.
4. Keep a stable card per (sub-topic, tier) once any child has seen it (write `rewards.json` once per released bank and only
   append), so previews never change under the child.

## 4. Learning (question 4)

- **Spaced retest (1, 3, 7 days):** matches the expanding-interval literature in spirit and the code matches the design.
  It is good for a 10-month horizon, but the 7-day final step is short for a 44-week window; add a 21-day step for Competent
  items. See H3 and M6 for the volume and drift problems.
- **30% retest cap:** reasonable, but it is also the cause of the backlog (H3) and applies only to the same tier.
- **Daily Review:** useful; make it larger when the queue is large and let it count as half a goal.
- **Papers never count toward a pass:** true for `finishQuiz`, but they still call `answer()` (H1c, M6), so they change retirement.
- **Retire-on-first-correct is too generous** (M2): 4-20% of retired items were guesses depending on mastery.
- **8/10 reliably separates mastery from luck?** Against *pure guessing*: yes (0.0004). Against partial knowledge (60-70%):
  not reliably in one quiz; two passes on separate days are the real gate (M3).

## 5. Child safety and well-being (question 5)

Positive: no money, no leaderboard, no push, "Not yet" copy, nothing is taken away when a streak breaks, cap and PIN exist.
- **Streak pressure:** H4 (breaks every Monday for a 5-day routine); "No streak yet" shown after any break is mildly shaming.
  Replace with weeks and "best".
- **Daily cap:** good in principle; default 45 min exceeds the pacing plan (20-30). Default to 30 min, goal 20 questions.
  The cap is checked by `localStorage`, so a child can clear it; the parent should know it is a convenience, not security.
- **"Done for today" wording** (quiz index, `quiz/index.astro`): "Done for today! You have reached today's training time.
  Come back tomorrow." tells the child what they cannot do. Suggest: "Great work. You did N questions today. Your brain
  needs rest to remember them. See you tomorrow, and your review questions will be waiting." Avoid "you have reached" (reads as a limit).
- **Reward for failing** (H1): a child who fails repeatedly gets a card on pool exhaustion, which teaches that persistence
  without improving is rewarded and gives the parent a false mastery grid.
- **No dark patterns found:** no variable rewards, no scarcity timers, no purchase hooks. Watch for: streak loss aversion (H4),
  and a boss "win threshold" that changes ("one band above") which can feel like a moving goalpost.

## 6. Accessibility of the quiz flow (question 6) [ACC]

| Item | Evidence (`quiz/index.astro`) | Verdict | Fix |
|---|---|---|---|
| Time limits | Fixed timer; parent-only x1.5 switch; no "off" | WCAG 2.2.1 Timing Adjustable not met (child cannot adjust) | Add untimed practice mode (H2) and x2 option |
| Timer announcement | `role="timer"` (implicitly `aria-live=off`), no warning at 1 min or time-up | Screen reader users get no warning | Announce at 2 min, 1 min, 10 s via a polite live region; do not announce every second |
| Colour-only | `.timer.low` changes colour only; `.opt.right/.wrong` add check/cross via CSS `::after` | Timer fails 1.4.1; options OK (glyphs) but CSS `content` is not reliably read | Add text "Time is running low" and real visually hidden text "Correct"/"Wrong" |
| Keyboard | A-D and 1-4 select; Enter on focused Next; first option focused each render | Works; single-key shortcuts cannot be turned off (2.1.4) | Offer a setting to disable shortcuts, or require focus inside the options group |
| Focus after answer | Focus moves to Next, feedback is a polite live region | Screen reader reads Next, may miss the verdict | Move focus to the feedback heading or include verdict in the button's `aria-describedby` |
| Fractions | `<span class="fr">` with hidden "/" | Good, "/" is in the DOM for readers | Keep |
| Contrast | berry #a8304a on white 6.6:1 ok; cocoa-soft #6b5443 on cream about 6:1 ok | Passes AA | Keep |
| Focus ring | 3 px berry outline, 3 px offset | Good | Keep |
| Time-up while answering | `finish(true)` ends mid-question without warning | Distressing for a child | Grace: finish after current question if less than 15 s over, and say so |
| Figures | SVG figures injected as raw HTML, no `alt`/`aria-label` seen | Likely a blocker for blind users | Add `role="img"` + text description per figure in the bank |

## 7. The monster system (question 7) [SYS]

Evaluation of design section 5:
- **Band mapping is circular.** The "level" of a monster is the student's *estimated band*, estimated from "recent boss accuracy"
  on monsters that are themselves chosen from the band. Accuracy on an AL3 boss is not comparable to accuracy on an AL7 boss.
  Fix with a fixed composition per monster and a **guess-corrected** weighted score (see spec). MCQ accuracy also has a 25% floor, so
  "AL8 < 20%" is unreachable; correct with `m = (acc - 0.25) / 0.75`.
- **Win thresholds are mis-tuned** (6/7/8/9 of 10). Probability a child wins at various true mastery (binomial, guess 25%):

| Threshold | mastery 0 | 30% | 50% | 70% | 85% |
|---|---|---|---|---|---|
| 6/10 | 0.02 | 0.32 | **0.69** | 0.95 | 1.00 |
| 7/10 | 0.00 | 0.13 | 0.45 | 0.83 | 0.98 |
| 8/10 | 0.00 | 0.04 | 0.21 | 0.60 | 0.91 |
| 9/10 | 0.00 | 0.01 | 0.06 | 0.31 | **0.69** |

  A 50% child beats an AL6 monster 69% of the time (too easy); an 85% child beats AL1 only 69% (too hard for the top band, and
  the 10-question noise is large). Use one threshold (7/10) and let the *mix* carry difficulty.
- **Card boosts distort the measurement.** Hint hides an option (guess rises from 25% to 33% or 50%); shield forgives a
  wrong answer (+10 points). Both inflate the score that feeds the band. Rule: a boosted question counts 0.5 toward the estimate.
  `+time` is harmless and should be the only boost that counts fully.
- **Pool:** "drawn from unretired questions" would empty the boss pool as the child masters content. Boss draws from **all** questions
  of cleared sub-topics (retired included, which is spaced practice), and **boss answers do not retire anything**.
- **Weekly monster:** needs 4 sub-topics with >= 10 answers each in 14 days; with 20 playable tiers and 2 quizzes a day that is
  usually met, but add a fallback (use the 4 lowest-retention sub-topics from any time) and exclude sub-topics with fewer than 10 answers.
- **Win cards:** Beast cards for "first win vs each school monster" need all four schools; today only Math can award one.
- Pacing: the first boss should appear only when >= 3 sub-topics have a cleared Basic tier (about 3-4 weeks in).

## Values that need attention

| Value | Current | Suggested | Reason |
|---|---|---|---|
| Auto-credit on empty pool | credit with 0 passes, `acc` 100 | require >= 1 pass and last-10 >= 80%; else recycle retired Qs | H1, reward for failing |
| Pass quiz size | 1-10 questions (80% of what is left) | exactly 10 | H1, 1-question quiz passes at 25% guess |
| Timer during feedback | runs | paused while feedback open | H2 |
| Retest per tier quiz | <= 3, same tier | <= 3, same sub-topic, any tier | H3 |
| Daily Review size | 5 | 10 when due > 10; counts half | H3 |
| Streak unit | days, 1 freeze/week | weeks with >= 4 goal days | H4 |
| Goal unit | 2 quizzes | 20 answered questions + 3 min floor | M5 |
| `due` | now + n x 24 h | local day start + n | M6 |
| Retest steps | 1, 3, 7 | 1, 3, 7, 21 (Competent) | 44-week horizon |
| New-correct retire | retire at once | confirm in 3 days for Competent | M2 |
| Card power | 80-100 (acc x stars) | retention-based, 40-100 | M4 |
| Power thresholds | <60, 60-84, 85+ | <60, 60-79, 80+ with retention power | Bands unreachable today |
| Daily cap default | 45 min | 30 min | Pacing plan is 20-30 min |
| Ancient unlock | 2n legendaries at 2 stars | n + 1 legendary or super-epic at 2 stars | 2 legendaries in Math; unreachable |
| Win threshold | 6/7/8/9 of 10 | 7 of 10 for all, mix carries difficulty | table above |
| Band estimate | raw boss accuracy | guess-corrected, mix-weighted (spec) | Circularity |
| 7 commons slots | first 7 home-level slots | first 7 *playable* Basic tiers | Section 3 |
| MIN_POOL | 20 | 30 for I and C | Pass needs 20 fresh Qs; retire shrinks pool |
| Time per question | 1.2/1.5/2.0 min incl. feedback | same, feedback paused | H2 |

## Appendix A. Spec: Math Monster v1 (buildable)

**Purpose:** a 10-question mixed boss quiz that measures current Math MCQ skill, feeds the parent's band estimate and weekly weak spots,
and rewards a reliable win. Mode `boss` in `/quiz/?mode=boss&level=AL5`; extends `Attempt.mode` to `'boss'`.

**Inputs**
- `cleared`: sub-topics with Basic cleared (and tiers cleared for each).
- Banks `math-*.json` limited to cleared sub-topics.
- `questions` save map (steps, due, w), `attempts` (boss history), `cards` equipped (max 3), `settings.extraTime`.
- Level `k` in 1..8 (monster ALk). Challenge level = `best_beaten_AL - 1` (start at AL6 for a new player).

**Composition (counts of basic, intermediate, competent out of 10)**

| Monster | B | I | C | Time at 1.2/1.5/2.0 min |
|---|---|---|---|---|
| AL8 | 7 | 3 | 0 | 12.9 |
| AL7 | 6 | 4 | 0 | 13.2 |
| AL6 | 5 | 4 | 1 | 14.0 |
| AL5 | 4 | 4 | 2 | 14.8 |
| AL4 | 3 | 4 | 3 | 15.6 |
| AL3 | 2 | 4 | 4 | 16.4 |
| AL2 | 1 | 4 | 5 | 17.2 |
| AL1 | 0 | 3 | 7 | 18.5 |

`time_limit = ceil(sum(per_q_min) x (extraTime ? 1.5 : 1))`; the clock pauses while feedback is open.

**Selection** (pure function `pickBoss(qs, seen, mix, now, rand)`, unit-testable like `pickTier`)
1. Pool = questions of cleared sub-topics with the needed level.
2. Fill each level quota in this priority: due retests (oldest first, max 3 total), then retired questions with the oldest
   `lastSeen` (interleaved retrieval), then unseen (only if still short).
3. At most 3 questions from the same sub-topic (interleaving).
4. If fewer than 10 can be found, shrink to the largest k >= 6 that fits; below 6, return "Play more topics first".
5. Return ordered B, I, C.

**State effects (no retiring)**
- Wrong: if the question is unseen, set step 1 (due tomorrow); if retired, return to step 3 (due in 7 days); if on the ladder, keep step.
- Correct: leave state unchanged (boss never retires or advances). Log in `attempts` with `mode: 'boss'`, `level`, `sub-topics`, `tags`.

**Scoring**
- `raw = correct` (0-10), shown to the child.
- `boosted` = number of questions answered while hint or shield was used; `eff = correct - 0.5 x boosted_correct`.
- Win if `raw >= 7` (and the time limit was not exceeded). Win threshold is the same for all levels.
- Estimate input: `w_b=1, w_i=1.5, w_c=2`, `W = sum(w x correct_effective) / sum(w x asked)`.
- Guess-corrected mastery `m = clamp((W - 0.25) / 0.75, 0, 1)`.

**Band estimate (per school, shown to parent as a range)**
- `est_pct = 100 x m` over the last 5 boss attempts, each weighted `1 + (9 - ALk)/8` (harder monsters count more).
- Map by PSLE bands: AL1 >= 90, AL2 85-89, AL3 80-84, AL4 75-79, AL5 65-74, AL6 45-64, AL7 20-44, AL8 < 20.
- Display `AL{band} to AL{band+1}` (a range), the label "estimated from multiple-choice only, not a prediction", and "not enough data"
  until 3 boss attempts exist. Never show a single AL to the child; show only the monster they fight and the result.

**Boosts (v1)**
- `+time`: +30 s (Basic-class card), counts fully.
- `hint`: hide one wrong option, once per fight (Intermediate class), question counts 0.5.
- `shield`: first wrong answer is re-asked once without a hint; if the second try is right it counts 0.5 (Competent class).
- Strength by power tier: below 60 -> +15 s; 60-79 -> as above; >= 80 -> hint hides two options but counts 0.25.
- A student with no cards can win; boosts never alter `raw` in the win rule when `eff` is below threshold by more than 1.

**Rewards:** first win at each school gives the Beast card (Math only in v1); a win at the child's challenge level gives +1 star
to the equipped card with the lowest stars (cap 5). A loss gives nothing and a message "Not yet. We found 3 topics to review"
with links; there is no penalty and no cooldown.

**Weekly monster (v1.1, optional)**
- Every Monday build from the last 14 days: the 4 sub-topics with lowest guess-corrected accuracy (>= 10 answers each, else take
  those with the lowest retention) and the top 3 mistake tags.
- 6 questions from those sub-topics (preferring wrongly-answered tags), 2 due retests, 2 retired questions from other sub-topics.
- Win is `raw >= 7`; reward +1 star and a progress mark; a miss gives the same message as above. Counts toward Beast 10/25 wins.

**Edge cases**
- No cleared sub-topics: button disabled with "Clear a Basic tier first".
- Fewer than 10 questions available: see step 4; never run a 1-question boss.
- Extra-time on: limits x1.5 and the 3-minute floor for the goal still apply.
- Cap reached: refuse to start (same message as other modes), unless a boss is already in progress.
- Abandoned boss: no attempt row, but answers already given are logged as in the tier rules (see H1d: write the attempt row at start).
- Level above AL1 or below AL8: clamp to 1..8.
- Save migration: add `monsters: Record<'math', { recent: [..], bestBeaten: number }>`; if absent, default `bestBeaten = 7`.
- Time-up: unanswered questions are wrong with tag `ran_out_of_time`, same as tiers.
- Weekly monster when fewer than 4 qualifying sub-topics: use the available ones and fill with retests.

## Appendix B. What I did not check
- Science, English and Chinese content does not exist yet, so the multi-school economy (Ancient unlocks, 186-card balance) is evaluated from
  `rewards.json` and the design only.
- Question *correctness* in the banks was not audited (answer position and duplicates were).
- Real student mastery and recall rates are assumed (0.75-0.85 and 0.7), so pacing numbers are model outputs, not measurements.
- The school calendar (WA/SA/prelim dates, holidays) is not modelled; prelim exams come before 30 Sep, so effective revision time is shorter than 317 days.
