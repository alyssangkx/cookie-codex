# Cookie Codex

A PSLE revision game for one Primary 6 pupil (and other families who sign up), plus a reference library of Cookie Run: Kingdom cookies. Learning comes first; the game rewards it with cards. Decisions behind these terms are in [docs/adr/](docs/adr/).

Each entry gives the term, what it is, the file or function that owns it, and the neighbours it is confused with. Terms marked **Retired** no longer exist.

## Syllabus and content structure

**Subject** (also **school** in game copy):
One of Math, Science, English, Chinese. The map shows each subject as a "school" with a monster; `School` in `site/src/lib/store.ts` is the type.
_Avoid_: course, paper (a paper is an exam)

**Strand / topic / sub-topic**:
The three levels of `site/src/data/syllabus/<subject>.json`: strands contain topics, topics contain sub-topics, sub-topics contain outcomes. A sub-topic is the unit a child trains.
_Avoid_: unit, chapter

**Category**:
Umbrella word only (owner, 20 Nov 2026): code and docs say **sub-topic**; on screen each subject uses the paper's own word, **"section"** for English and Chinese (prelim paper sections) and **"topic"** for Math and Science (SEAB syllabus sub-topics) (ADR 0007). "Coming soon" marks sections the site cannot ask yet.
_Avoid_: using category and topic interchangeably (a topic is the level above the sub-topic)

**Paper section**:
A numbered part of an English or Chinese prelim paper, such as Grammar MCQ, Vocabulary Cloze, Visual Text, Comprehension OE. English order: Grammar MCQ, Vocabulary MCQ, Vocabulary Cloze, Visual Text, Grammar Cloze, Editing, Comprehension Cloze, Synthesis & Transformation, Comprehension OE.
_Avoid_: section of the syllabus

**Outcome**:
A single learning outcome from the syllabus JSON (id with a trailing `-NN`). A question is filed under the sub-topic of its first outcome id.
Owner: syllabus JSON; `scripts/quiz/check_dupes.py` states the filing rule.

**P-level**:
The school year (P1 to P6) a sub-topic's highest outcome belongs to. It sets tries per day (5 for P1-P5, 3 for P6 and all Chinese) through `triesPerDay` in `store.ts`.
_Avoid_: tier, level (see below)

**Tier**:
Basic, Intermediate or Competent: the three difficulty steps inside one sub-topic, each with its own question pool, time limit and card.
Owner: `Tier` in `store.ts`.

**Question level**:
The `level` letter on a question (b, i, c). It decides which tier's pool the question joins. It is not part of the question id.
_Avoid_: tier, P-level

**Pattern**:
A catalogue id for a question type seen in past papers (`math-pat-...`, English `patterns.json`). A Math template covers a pattern by naming it in its docstring.
Owner: `patterns.json` per subject; `scripts/quiz/coverage.py`.
_Avoid_: topic, method

**Template** (Math) vs **item** (English, Chinese, Science):
A template is a parametric generator that makes many Math questions, each wrong option from a named mistake. An item is one hand-written, reviewed question stored in `items/*.json`. Both end up as questions in a bank.
Owner: `scripts/quiz/math/common.py` (`@template`); `scripts/quiz/<subject>/items/`.

**Bank**:
The shipped JSON of questions for one sub-topic, `site/src/data/quiz/<subject>/<topic>.json`, built by each subject's `build.py`.
_Avoid_: pool (a pool is the set of questions in one tier)

**Playable tier**:
A tier with at least `MIN_POOL` (20) questions. Only playable tiers can be trained; `train.ts` marks a sub-topic ready when one tier is playable.
Owner: `MIN_POOL` in `store.ts`; `playable` in `train.ts`.

**Passage set**:
Questions that share one text and ship whole or not at all: English `vis-NN-K`, `read-NN-K`, `ecloze-NN-K`; Chinese dialogue sets. Carried by `group`/`seq`.

## Question identity and review

**Key**:
The author-chosen name of a template or item within a topic (for example `vis-03-2`). It is input to the id and never shown.

**Question id**:
The stable id of a question: Math `<prefix>-<level letter>-sha1(topic | template key | canonical JSON of params)[:10]`; other subjects `eng<strand>-<sha1(topic|key)>` and the like. Rewording stem, explanation or figure keeps it; changing a template's numbers makes a new question. Progress is keyed on ids, never on stem text.
Owner: `stable_id()` in `scripts/quiz/math/build.py`; `scripts/quiz/bankcommon.py`.

**Fingerprint**:
A 16-character hash of everything a reviewer judged (stem, options, answer, explanation, solution, gloss, level, outcome, pattern, visual, figure). An item edited after review no longer matches its verdict.
Owner: `fingerprint()` in `bankcommon.py`.

**Review gate**:
The rule that an English, Chinese or Science item ships only if `review.json` holds a verdict for its current fingerprint. Unreviewed and stale items are dropped. It fails closed.
Owner: `review.json` per subject; each `build.py`.

**Ship**:
To be written into a bank. A question ships when it passes the review gate (and, for a set, when every member does). `"ship": true` is the review verdict field.
_Avoid_: publish, release

**One category per question**:
Each question is filed under exactly one sub-topic. `check_dupes.py` fails if the same stem sits under two (ADR 0003).

## Learning loop

**Retest** (spaced steps):
A wrong answer comes due again in 1 day, then 3, then 7. A wrong answer at any step returns to step 1.
Owner: `answer()` in `store.ts`.
_Avoid_: review (Daily Review is the quiz that asks due retests)

**Parked**:
A retest state whose question id was in no bank when Daily Review last loaded every bank (`syncParked`). It is not counted as due and is never deleted; any page that loads the id unparks it, and answering always unparks it.
Owner: `questions[id].parked` in the save, `syncParked` in `store.ts`.

**Retired**:
A question state `s === 0`: answered right first time, or right at the 7-day retest. A retired question is no longer drilled in its tier.
Owner: `questions[id].s` in the save.

**Mastered**:
The count of retired questions in a tier, shown as "N of M mastered". `liveMastered` returns 0 when the stored count was made against a bank of a different size, or (when the tier state has one) a different id hash (`tierHash`, stored by `syncTiers`, computed per tier by `train.ts`).
Owner: `syncTiers`, `liveMastered` in `store.ts`.

**Cleared**:
A tier whose questions are all retired. Clearing awards its card, and a cleared tier is never un-cleared. The exception is a perfect first try on Basic or Intermediate (10 of 10 on the first-ever quiz of that tier), which clears at once.
Owner: `finishQuiz` in `store.ts`.
_Avoid_: passed (the 80% score is display only)

**Tier quiz**:
A 10-question quiz on one tier: up to 3 due retests, then new, then not-due, then retired questions. It gives instant feedback after each answer.
Owner: `pick.ts`.

**Daily Review**:
A 5-15 question quiz of due retests across sub-topics. It counts toward the goal, never toward clearing a tier, and does not count against the 10-quiz limit.
Owner: `pick.ts` (`reviewPassages` keeps passage blanks together).

**WA/SA practice paper**:
A timed paper mixed across chosen topics, in the style of a Weighted Assessment or Semestral Assessment. Practice papers never retire questions or clear tiers.
Owner: `/paper/` page; `site/src/lib/paper.ts`.
_Avoid_: tier quiz

**Submit-then-review**:
The WA/SA paper flow: answer everything, change answers freely, submit, then review only wrong and blank answers. Tier quizzes and Daily Review do not use it (ADR 0005).

**Draft** (paper draft):
The in-progress state of a WA/SA paper (ids, picks, flags, deadline, pause used), kept through `store.ts` so a reload resumes. A draft belongs to one player and one attempt.
Owner: `PaperDraft`, `loadDraft` in `paper.ts`.

**Tries per day**:
How many quizzes a child may start per tier per day: 5 for P1-P5 sub-topics, 3 for P6 and Chinese. A started quiz counts.
Owner: `triesPerDay` in `store.ts`; `progression.json`.

**Daily cap**:
The parent-set training time limit per day (default 120 minutes, range 45-180 in steps of 15). A separate 10-quiz limit exists but is switched off (`QUIZ_CAP_ON`). `dayBlock` gives the reason.
_Avoid_: daily goal (the goal is a target; the cap ends play)

**Daily goal**:
The parent-set target (about 2 quizzes or 20 minutes) that makes a day count toward the streak. Weeks with 4 or more goal days keep the streak.

**Encouragement line / score band**:
The line shown on a result, picked by percentage band (perfect, 80%+, 50-79%, under 50%) and by a hash of the attempt time. Lines praise effort and strategy, say "not yet" not "fail", and never compare children. Chinese results show a Chinese line with the English below.
Source: `docs/learning-loop-design.md` section 4.
_Avoid_: AL band

**AL band**:
A PSLE Achievement Level (AL1 best to AL8) derived from a score percentage. Used only in the parent view and the proposed economy; the child never sees one.
_Avoid_: score band

**Competency** (proposed):
A per-pattern state of Not yet, Developing, Exam-ready or Not measured (owner, 20 Nov 2026: the top state and its badge are called **Exam-ready**, never "Competent", which is a tier name), built from evidence in the save (`comp`, schema 5). Designed in `docs/past-papers-design.md` section 4; not built.
_Avoid_: mastered, Competent (the tier); call the top state Exam-ready

**Diagnose / Drill / Re-assess** (proposed):
The assessment cycle: probe a sub-topic with fresh items, drill it in the site banks, re-assess with a different set. Re-assess never repeats Diagnose items.
Source: `docs/past-papers-design.md` section 5.

## Game and rewards

**Card**:
A cookie from the 186 in the Library, awarded once per slot. An awarded card is never taken away (ADR 0001).
Owner: `site/src/data/cookies.json`; `rewards.json`.

**Card slot**:
One fixed (sub-topic, tier) pair that maps to one card in `rewards.json`. Slots are generated, previewed before the quiz, and never random (ADR 0009). A slot's card can change when banks are rebuilt; owned cards stay owned.
Owner: `scripts/quiz/build_rewards.py`.

**Star / duplicate**:
A slot whose card is already owned gives a **replacement card**: the next unowned card of the same rarity in `rewards.json` `rarityOrder` (previewed on the tier page). Only when that rarity has no card left does it give one star on the slot card plus Crumbs (half the shop price, 60 for Super Epic and Legendary).
_Avoid_: level-up

**Rarity**:
The class of a card: common (7), rare (14), special (11), epic (116), super epic (13), legendary (11), and the milestone classes beast, dragon, witch, ancient. Each needs a `--r-<rarity>` colour in `global.css`.

**Milestone**:
A card earned by behaviour, not by clearing a tier: Ancient, Dragon, Beast, Witch (14 cards). Specified in `docs/game-design.md` section 4; deferred. Never for sale.

**Achievement card**:
A Super Epic for each competency group (a Math or Science topic, or an English or Chinese paper booklet; members are the sub-topics with a playable Competent tier, 2 or more) once all are cleared at Competent. A Legendary once per subject when every sub-topic of the subject is playable at Competent and cleared, or for a WA/SA paper of 20+ questions drawn from 3+ topics at AL1-AL2 (85%+), at most one paper Legendary a week. Gives the next unowned card of that rarity, else a star and 60 Crumbs. Not for sale.
Owner: `store.ts` (`achievements`), `crumbs.ts` (`achievementPreview`).
_Avoid_: tier reward

**Card power**:
A number that reflects retention of the questions behind a card, worked out in `suggest.ts`.

**Crumbs**:
The coin, earned per finished quiz by AL band (8 for AL1, +4 perfect, down to 1 for AL8; WA/SA papers x(questions/10), at most x3), +1 per retest step passed, +3 for the daily goal, +10 per streak week. Spent in the Shop at fixed prices on the exact card picked (Common 30, Rare 60, Special and Epic 120); once a rarity is all owned, on stars. Never random, never expire, no real money. Kept in the optional save field `crumbs` (balance, last 50 ledger entries, every purchase; no schema bump). The unlimited account's Crumbs are flagged `test` and left out of parent totals.
Owner: `site/src/lib/crumbs.ts`; `store.ts` (`finishQuiz`, `purchase`); `/shop/`.

## Save, sync and accounts

**Save**:
One child's progress: tiers, question states, attempts, days, streak, cards, settings. Interface `SaveV1` (name kept for imports), `schemaVersion` 4 in the code. Only `store.ts` touches localStorage.
Owner: `store.ts`.

**Schema bump**:
Raising `schemaVersion` plus a step in `migrations`. Content redesigns do not bump it (ADR 0002).

**Orphan question state**:
A `questions[id]` entry whose id is no longer in any bank. It is kept, never deleted; the parent page leaves it out of lists.

**Sync / push_save / rev**:
Browser-to-server save sync. A debounced push carries the base `rev`; `push_save` rejects a stale rev (conflict banner) unless forced. `sync.ts` holds the pure decisions.
Owner: `site/src/lib/sync.ts`; Supabase function `push_save`.

**Child / parent / admin**:
Child: a profile that logs in with username and PIN. Parent: an email account (aal2 once an authenticator is enrolled) that owns children. Admin: the owner, with `app_metadata.role = 'admin'`; owns the Test Player.

**Unlimited account**:
A child profile with the server flag `unlimited`, which has no time or tries cap and every tier open. Only the admin's own profiles can carry it.

**Username**:
A child's login name, unique across the whole site (letters first; letters, digits, spaces, hyphens; up to 20).
_Avoid_: name, family code

**PIN login**:
Username plus 4-digit PIN, checked by the `pin-login` Edge Function with escalating lockouts and a CAPTCHA on untrusted devices.

**Device token**:
A secret kept on a trusted device so it skips the CAPTCHA and uses the more lenient `trust:` lock key.
Owner: `kv` in `store.ts`; `pin-login`.

**Family**:
A parent's row that holds the consent record and the 7-day delete. **Retired as a login concept:** the family code was removed on 20 Nov 2026 (migration 003); do not reintroduce "family code".

## Past papers (private)

**Past paper**:
A scanned school prelim paper, 2018-2026. Commercial and copyrighted: it lives outside the repo (ADR 0004). Only counts and public summaries appear in docs.

**Merged question**:
One question record after the text read and the vision-model read are reconciled (`merged.jsonl`).
Owner: `docs/past-papers-design.md` section 1.

**Tag (st / pat)**:
The labels the tagger gives a merged question: `st` a sub-topic id, `pat` a pattern id (plus method, difficulty, confidence).
Owner: `scripts/pastpapers/tag_llm.py`.

**Gold key**:
A hand-adjudicated set of tags (110 Science 2024 questions) used as the gate: a full tagging run starts only at 80% agreement.
_Avoid_: answer key (the school's marking key)

**Blind-answer check**:
Solving a past-paper question without seeing its key, then comparing. No past-paper question reaches a child before it passes.

**Quarantine**:
The private list of past-paper items withheld after the audit found wrong or mismatched keys.

**Pilot bank**:
The first banks (before 20 Nov 2026), now redesigned from the papers. Pilot cards stay owned.

## Infrastructure terms

**The server** (GPU server):
The owner's home machine that runs the vision and text models for tagging and, later, live marking. Its address is private.

**llm mode**:
A server state that loads one large model across all GPUs and stops the image workers.
_Avoid_: tutor mode

**Edge Function proxy**:
The planned path from the browser to the server's model, through a Supabase Edge Function that checks the session and rate limit. The browser never sees the model's address.
