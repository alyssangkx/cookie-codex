# To-do list

This file holds everything the owner and Claude have agreed or recommended but not finished. Add to it whenever
something is discussed. Tick an item (`[x]`) only once it is done and verified, and write the date next to it.

Priority (owner, 20 Nov 2026): the learning, training and assessment loop comes first. Game mechanics come second and
may be reworked, but cards already awarded stay.

Private details (server addresses, keys, past-paper text) are kept out of this file. They live in the private notes
outside the repo.

## Now (20 Nov 2026)

- [ ] **Server queue, then pickup on dev**
  - Tag Maths, Science and Chinese 2018–2024.
  - Apply the Chinese rule: the sub-topic comes from the paper section, except 语文应用.
  - Tag English 2018–2026 by paper section.
  - Re-run the MCQ audit with passages and figures.
  - Re-read the answer-key grids, twice per box, and keep only boxes where both reads agree.
  - Then `audit/pickup.sh` applies the agreed key fixes to the merged files and re-scores the audit.
- [ ] **Audit follow-up:** re-adjudicate the "unjudged" disagreements using the new passage and figure picks. Report
  the error rate per subject before and after the key fixes.

## Past-paper data quality

- [ ] Fix the answer-key grid reading in `scripts/pastpapers/vlm_read.py`.
  - What goes wrong: the 32B swaps, duplicates or invents cells.
  - The fix:
    - read cell by cell, or twice;
    - add a gate that flags runs of the same value or 1-2-3-4;
    - re-read any key the blind solver disagrees with.
- [ ] Quarantine the 14 items listed in the audit (`mcq-answers.md`). The 72B's `ans_check` flag does not predict
  wrong keys, so do not rely on it.
- [ ] **No past-paper question reaches a child before a blind-answer check.** About 6% of Maths keys and at least 5%
  of English keys were wrong.
- [ ] Re-read the 9 answer pages that would not parse (queued).
- [ ] Tagger bias in Science:
  - it files friction, spring and weight questions under "Forces and their effects": add a rule, then re-tag the
    forces questions;
  - it puts water changes of state under general "states of matter".
- [ ] Tag accuracy for English, Maths and Chinese is not measured yet. Build a checked key for each, as was done for
  Science (110 questions, about 100k Sonnet tokens per subject).
- [ ] English patterns: about 29% of English questions get no pattern. Extend `scripts/quiz/english/patterns.json`.
- [ ] Speed is excluded as off-syllabus, but 2026 prelims had 6 speed items. Re-check once 2018–2024 are tagged.
- [ ] 2025 MCQ import, phase 1 (`prompt-pp-mcq-import.md`), after the blind-answer check. Stop before any SQL or data
  load.
- [ ] Part 2 design run (`prompt-design-part2-run.md`).

## Question banks (content)

- [ ] **Populate the site's Science questions (owner, 20 Nov 2026).** This is the main Science task.
  - **Do it only after the repo is robust** and three things are clearly understood from the tagged papers:
    - how often each question type appears;
    - how each type is asked (stem framing, options, mark split);
    - what picture, graph or table goes with it.
  - **Then the questions come from one of two sources:**
    - straight from the repo's past papers, served privately after the blind-answer check;
    - generated in the same style.
  - First step: a Science frequency and format study over all tagged years, covering type × framing × figure kind
    (photo, diagram, graph, table, set-up drawing).

- [ ] **Science:**
  - Adaptations and Plant reproduction need Intermediate and Competent items (only Basic is playable).
  - Plant parts and functions: bring each tier to 25.
  - About 15 plant-transport items share one plant drawing: vary them.
  - The site's Science covers only about 6% of what Science papers test. This is the largest content gap, and every
    Science diagnostic depends on it.
- [ ] **English and Chinese:** a strict second review of the 15 visual-text sets and the 57 rewritten idiom items. They
  had only one review pass.
- [ ] **Maths:** add Angles templates until Angles reaches its share of paper marks (it is at 230 questions, under its
  share).
- [ ] Keep weighting banks by paper frequency as new tags arrive (2018–2024).

## Learning loop (`docs/learning-loop-design.md`, owner decisions 1–10 accepted)

1. [ ] **Encouragement lines on results (S):** score bands, 20 English and 20 Chinese lines (Chinese with English
   underneath in term 1). The owner edits the table in the design doc.
2. [ ] **Submit-then-review for WA/SA papers (M):**
   - answer everything against the clock, submit, see the score, then step through only the wrong answers;
   - wall clock, one pause of up to 10 minutes, submits itself at zero;
   - add English and Science papers.
3. [ ] **Initial assessment, study plan and re-assessment cycle (L):**
   - one subject a day in the December holidays;
   - cards stay on tier mastery, with a "Competent" badge added;
   - real past-paper items wait for the private import.
4. [ ] **Open-answer marker (L), per `docs/marking-framework.md`:**
   - [ ] rubric schema and private storage, plus a reviewer page in admin;
   - [ ] rubric drafting batch on the server for Science Paper 2, reviewed in samples;
   - [ ] typed-answer marker for Science, with calibration: the owner blind-marks 100 answers per subject, target at
     least 90% agreement per point;
   - [ ] Maths Paper 2 v1: typed final answer plus typed steps, M and A marks, model drawings as units;
   - [ ] Maths Paper 2 v2:
     - printable paper with answer boxes and a QR code per page;
     - photo upload;
     - transcribe, then confirm, then mark;
     - parent reviews unsure marks;
     - photos kept 90 days;
   - [ ] English and Chinese open-ended answers.
5. [ ] **Tutor chat: low priority (owner).** It comes after most of the site is redesigned, including the marker. It
   is available only on questions answered wrong, and must pass a red-team test first.

## Home server for live LLM features

- [ ] Run Qwen2.5-VL-32B on its own GPU (GPU 3), and test that it fits and passes before any child-facing use. The
  uncensored model is never child-facing.
- [ ] Owner: point llm mode at GPUs 0–2 so the dedicated GPU stays free.
- [ ] Cloudflare Tunnel (TLS) on a domain the owner controls, then close the plain-HTTP router forward.
- [ ] Supabase Edge Function proxy: it holds the API key and checks the child's login.
- [ ] Data retention: typed answers 90 days, transcripts 30 days, both visible to the parent with a notice. A safety
  flag also emails the parent, with no transcript text.

## Game design (pilot -> redesign, `docs/game-economy.md`)

- [ ] **The first question banks were a pilot (owner, 20 Nov 2026).** They are being redesigned from the repository.
  Game mechanics stay; an awarded card is never taken away.
- [ ] **Replacement cards:** when a redesigned tier's card is already owned, give the next unowned card of the same
  rarity (fixed, previewed).
- [ ] **Coins ("Crumbs"):**
  - earned per quiz, following the AL bands (more for AL1 and a perfect score; WA/SA papers ×3), plus retest steps,
    goals and streak weeks;
  - spent in a fixed-price shop where the child picks the card;
  - rarer cards are achievement-only: Super Epic for topic competency, Legendary for a WA/SA paper at AL1–AL2, and
    Beast, Dragon, Witch and Ancient for milestones.
- [ ] Owner questions in `docs/game-economy.md`: the currency name, the earning table and prices, whether tier
  clears still give a card, and the bar for the rare cards.

## Site and tech

- [ ] Stale "N mastered" on a redesigned tier of the same size is not detected. Store a per-tier id hash in `syncTiers` and compare it with a build-time hash (display only).
- [ ] The Daily Review button on /train can show for retests of deleted questions (the review then says "Nothing to review today"). Give it a bank-aware count.

- [ ] Astro 7 upgrade on its own branch (npm advisories; none can be exploited here).
- [ ] A shared username-rule helper across `pin-login`, `admin` and `parent-api`.
- [ ] A single RPC `get_save_if_newer`.
- [ ] Owner: delete the test parent account from sign-up testing, if not done.

## Done

- [x] 20 Nov 2026: content redesign live (`975eeec`).
  - Maths: its own random stream per template, weighting by paper marks, exam-style rewrites (4,281 to 3,826
    questions; most Maths ids changed once).
  - Science: figures, re-filing, new items.
  - English and Chinese: pilot items rewritten under new keys, in the sub-topic each now tests.
  - Rewards rebuilt: Science 90, English 26, Chinese 11 slots moved; awarded cards stay.
  - Parent page leaves out deleted questions; one category per question (`check_dupes.py`).
- [x] 20 Nov 2026: parent sign-up live; family code removed.
- [x] 20 Nov 2026: site review leftovers. Login message, P–S line labels, home labels, Library jump chips, and a
  script-src CSP are all live.
- [x] 20 Nov 2026: tagger gate rebuilt on a checked key (84%). 2025, 2026 and Science 2024 tagged.
- [x] 20 Nov 2026: answer-page re-read. Questions with an answer went from 25,459 to 40,553.
- [x] 20 Nov 2026: design docs written: `learning-loop-design.md` and `marking-framework.md`.
