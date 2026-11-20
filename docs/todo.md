# To-do list

This file holds everything the owner and Claude have agreed or recommended but not finished. Add to it whenever
something is discussed. Tick an item (`[x]`) only once it is done and verified, and write the date next to it.

Priority (owner, 20 Nov 2026): the learning, training and assessment loop comes first. Game mechanics come second and
may be reworked, but cards already awarded stay. Game progress (tier states, question states, attempts) may be wiped
and reset when that simplifies a redesign; the cards stay.

Private details (server addresses, keys, past-paper text) are kept out of this file. They live in the private notes
outside the repo.

## Schedule (as of 20 Nov 2026, estimates)

1. **Submit-then-review for WA/SA papers:** going live 20 Nov, after the last review fixes. Tier quizzes keep instant
   feedback.
2. **Review and fix of site questions against the papers:**
   - The main rewrites and deletes have been live since 20 Nov.
   - Follow-ups on 20–21 Nov: a strict second review of the English visual-text sets and the Chinese idiom items,
     more Angles templates, and checked answer keys for the English, Maths and Chinese tags.
   - **Approved 20 Nov:** reorganise the site's English categories to match the paper sections, in progress. The order is Grammar MCQ, Vocabulary MCQ, Vocabulary Cloze, Visual Text, Grammar Cloze, Editing, Comprehension Cloze, Synthesis & Transformation, Comprehension OE. Sections the site can't ask yet show "Coming soon".
3. **Science population:**
   - Batch 1 on 20 Nov: plant reproduction and adaptations (upper tiers), forces, energy, survival, photosynthesis.
   - Batch 2 on 21–22 Nov: heat, circuits, respiration and circulation, water, light, matter, magnets,
     classification, materials.
   - Batch 3 on 23 Nov: the remaining small sub-topics.
   - Real past-paper items next week, after the blind-check adjudication and the owner's OK for the import.
   - Open-ended items after the marker is built.

## Now (20 Nov 2026)

- [ ] **Server queue, then pickup on dev**
  - [x] Tag Maths, Science and Chinese 2018–2024 (done 08:45, 70 min).
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
- [x] 20 Nov: the 14 audit items are in the private `pastpapers/quarantine.jsonl`.
- [ ] (kept for context) Quarantine the 14 items listed in the audit (`mcq-answers.md`). The 72B's `ans_check` flag does not predict
  wrong keys, so do not rely on it.
- [ ] **No past-paper question reaches a child before a blind-answer check.** About 6% of Maths keys and at least 5%
  of English keys were wrong.
- [ ] Re-read the 9 answer pages that would not parse (queued).
- [ ] Tagger bias in Science (the rule was added to `tag_llm.py`; the re-tag is queued on the server):
  - it files friction, spring and weight questions under "Forces and their effects": add a rule, then re-tag the
    forces questions;
  - it puts water changes of state under general "states of matter".
- [x] 20 Nov: tag accuracy measured against checked keys.
  - Maths 89% acceptable (77% exact).
  - English 84%: 94% where the paper names the section, 74% where the 72B filled it.
  - Chinese 85% after the section rule, 73% before it.
  - Report: `goldkeys/report.md`, private.
- [x] Add the suggested tagger rules for Maths, English and Chinese to `tag_llm.py` (percentage vs fractions, never
  a null st; lettered word list means grammar cloze, posters mean visual text; route maps mean 听后选答, single-word
  gaps mean 词语选用).
- [ ] EN/MA/ZH tagger rules + gold-gated re-tag (queue 10, `vlm/run_tag10.sh` waiting on queue 9; new files `tags72r10.jsonl`, gate lines in `vlm/tag10-done.txt`):
- [ ] Automatic crop review (owner, 20 Nov 2026: the server model should check pictures, not a person): (a) script fixes in `load_pp.py figures`: grow a crop cut off at an edge to the next blank band, straighten skewed scans; (b) server pass with Qwen2.5-VL-32B per selected item, crop next to its full page: is the figure complete, does it belong to this question, does it carry part of another question; a fail goes to `hold-auto.txt` (read like `hold.txt`). The owner then only spot-checks a sample per sub-topic. Run (b) after queue 10.
- [x] 20 Nov 2026: first past-paper sub-topic live. Owner reviewed and uploaded Plant transport (3 questions: 2 Basic, 1 Intermediate, merged into the generated tiers); `PP_ENABLED = true`. Next imports in order: forces, survival, plant reproduction, energy, photosynthesis, adaptations, resp-circ, heat, circuits (after queue 9 and the crop check).
- [ ] Past-paper follow-ups from the go-live review (20 Nov 2026), none affecting Plant transport today:
  - 'replace' tiers (20+ pp items): Daily Review always merges, so it stores gen+pp while the page counts pp only; make tierIds() in review send the tier quiz's pool, before any sub-topic reaches 20 pp items in a tier;
  - a failed pp fetch makes a quiz store the generated-only total ("N mastered" reads 0 until the next good quiz) and could clear a tier without its pp items; same when a figure fails to sign. Display only; revisit if seen;
  - crop growth can pull in option lines or a neighbouring question when the gap is under 25 px; the server crop check (above) must catch these; a crop as wide as the page is never located (so never grown).
- [ ] Before switching any past-paper sub-topic on (code review 20 Nov 2026):
  - [x] tier counts: train.ts counts and hashes a tier from the generated bank at build time, but the quiz adds or swaps in pp items at run time, so "N of M mastered" reads 0 on merged/replaced tiers. Done 20 Nov: `load_pp.py upload --apply` (or `counts`) writes `site/src/data/pp_counts.json` (numbers only); train.ts counts what the quiz will use and leaves the hash undefined on those tiers (liveMastered size check);
  - [x] `load_pp.py upload` must set active=false on rows of the uploaded sub-topics that are no longer selected (held, dropped or re-tagged away); done 20 Nov (also revives nothing held); dry run counts them when the Supabase env is set.
- [ ] Decide before importing English past papers: the tagger files "closest in meaning to the underlined word" under Vocabulary Cloze (as the papers label it), but the site keeps those single-sentence items in Vocabulary MCQ and Vocabulary Cloze takes passage sets only. Pick one home (recommended: Vocabulary MCQ, matching the site).
- [ ] Then a server re-tag run:
  - Maths: 175 null-st items plus the confused sub-topics;
  - English: the 72B-filled sections;
  - Chinese: the 语文应用 split.
  - Gate each subject on its new gold key.
- [ ] English patterns: about 29% of English questions get no pattern. Extend `scripts/quiz/english/patterns.json`.
- [x] 20 Nov: Speed re-checked over 2018–2026. It is fading (about 2.3% of Maths items in 2018, 1.7% in 2025, 6 tagged items in 2026), so it stays excluded.
- [ ] 2025 MCQ import, phase 1 (`prompt-pp-mcq-import.md`), after the blind-answer check. Stop before any SQL or data
  load.
- [ ] Part 2 design run (`prompt-design-part2-run.md`).

## Question banks (content)

- [ ] **Owner, 20 Nov 2026, later: Science uses the real past-paper questions with their original pictures. Do not create code-drawn graphics** (the generated plant graphic was poor). The code-drawn Science fill is stopped after its fix step.
  - Next: the private import of Science past-paper MCQs with compressed crops (`prompt-pp-mcq-import.md`: a Supabase table plus a private Storage bucket with signed URLs; nothing in the public repo).
  - Only blind-checked items go in: 2025–2026 now; 2018–2024 need a blind check on the server first.
  - Stop before any SQL or deploy for the owner's OK.
  - Decide what happens to the generated Science items with code-drawn figures in the meantime.
- [ ] **Populate the site's Science questions (owner, 20 Nov 2026).** This is the main Science task.
  - **Do it only after the repo is robust** and three things are clearly understood from the tagged papers:
    - how often each question type appears;
    - how each type is asked (stem framing, options, mark split);
    - what picture, graph or table goes with it.
  - **Then the questions come from one of two sources:**
    - straight from the repo's past papers, served privately after the blind-answer check;
    - generated in the same style.
  - [x] 20 Nov: frequency and format study done.
    - Public summary: `docs/quiz/science-paper-profile.md`. Private report:
      `audit/science-study/report.md`, with blueprints.
    - The site's 5 sub-topics carry only 15.6% of marks.
    - MCQ is 54% of marks; open-ended is 46%, about 70% of it "explain why/how".
    - 88% of questions have a figure: set-ups 30%, labelled diagrams 22%, tables 11%, line graphs 10%, circuits 7%.
    - Figure kinds are being re-measured on the server.
  - [ ] **Build order:**
    1. Top up the Intermediate and Competent tiers of plant reproduction and adaptations.
    2. Then forces-effects (10.2% of marks), energy-conv (8.9%), env-survival (8.1%), photosynthesis (5.9%),
       heat-effects (5.4%), circuit (4.8%), resp-circ (4.5%) and water-states (3.6%).
    3. Then light, matter, magnets, living classification and materials.
    4. Build each small sub-topic alongside its parent (circuit-vars with circuit, and so on).
    - Almost all MCQ blueprints are code-generatable (SVG tables, line graphs, circuits, food webs, set-ups,
      ray/shadow, ramps).
    - Flower/fruit, heart/lung, cell and beak/foot items need drawn line art.
    - Open-ended items need verbatim repo items or the marker.

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
- [x] 20 Nov: Maths weights recomputed from all 2018–2026 tags (13,986 items). 3 sub-topics moved by 1 point or more; 3,826 to 3,818 questions; rewards unchanged.

## Learning loop (`docs/learning-loop-design.md`, owner decisions 1–10 accepted)

1. [x] **Encouragement lines on results (S):** score bands, 20 English and 20 Chinese lines (Chinese with English
   underneath until 31 Mar 2027). Built 20 Nov 2026; the owner edits `site/src/data/encouragement.json`.
2. [x] **Submit-then-review for WA/SA papers (M):** built 20 Nov 2026 (`site/src/lib/paper.ts`):
   - answer everything against the clock, submit, see the score, then step through only the wrong and blank answers;
   - wall clock, one pause of up to 10 minutes, submits itself at zero; a reload resumes the paper;
   - English and Science papers: added, with items outside passage sets only (Grammar, Vocabulary; all Science).
   - [ ] Later: English cloze and comprehension sets as whole sets in papers; keep `ids`/`picks` on the last 20 papers
     so a review can reopen later; flag-a-question on the answer sheet.
3. [ ] **Initial assessment, study plan and re-assessment cycle (L):**
   - one subject a day in the December holidays;
   - cards stay on tier mastery, with an "Exam-ready" badge added (not "Competent", which is a tier name);
   - **Design conflict to settle first:** `past-papers-design.md` stores competency in the save at schema 5, but ADR 0002 rules out schema bumps (an old tab could overwrite the server save). Store it server-side, or in a field old code ignores, and decide this before the build.
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
- [x] 20 Nov: owner confirmed the Chinese booklet groups for Super Epic: Paper 2 Booklet A (语文应用, 短文填空, 阅读理解一), Booklet B (完成对话, 阅读理解二), Paper 3 (听力). Already built (`CHI_BOOKLET` in `train.ts`).
- [x] 20 Nov: owner answered the economy questionnaire, all as recommended:
  - coins are called Crumbs, earned on the AL table;
  - prices are 30, 60 and 120;
  - tier clears still give a card;
  - Super Epic for topic competency, Legendary for a WA/SA paper at AL1–AL2;
  - spare coins buy stars;
  - parents see the coin ledger.
- [ ] **Build the economy:** replacement cards, the Crumbs ledger (an optional save field, no schema bump per ADR
  0002), the shop page, achievement-only rare cards and the parent ledger. Start after the display-fix agent is done
  with store.ts.
- [ ] **Shop on the home map, replacing the Ranking Tower:** a drawn shop building as one transparent sprite over the
  tower spot on every map variant, plus its hotspot to /shop/. Check with screenshots at 375px and 1280px.

## Development practice (20 Nov 2026)

- [ ] `GLOSSARY.md` and `docs/adr/`, written with the domain-modeling skill (in progress).
- [ ] **Turn the review findings into checks** in `check_science.py` and `check_english.py`, after the current
  Science batch and the English reorganisation:
  - captions, labels and alt text must not hold the answer's words;
  - the stem must not echo the answer;
  - no near-duplicate options;
  - per sub-topic, the correct option is the longest in no more than about 35% of items;
  - flag figures whose drawn objects don't match the stem's nouns.
- [ ] **A short "working rules" section in CLAUDE.md**, Karpathy-style (the plugin is skipped):
  - state the syllabus scope and definitions before a question batch;
  - exactly one defensible answer per item;
  - figures depict the stem;
  - say what's unclear instead of guessing;
  - every review fault class becomes a check.

  Then a writing-for-agents pass to tighten CLAUDE.md.
- [ ] **Matt Pocock skills (already installed):**
  - to-questionnaire for the economy decisions;
  - grilling and prototype before the assessment cycle and the marker builds;
  - tdd and handoff written into agent briefs.

## Site and tech

- [x] Freeze English reward slots of cleared tiers (owner approved 20 Nov 2026): `scripts/quiz/english_frozen.json` pins
  the 15 slots of the 5 playable sections; `build_rewards.py` keeps them and `test_rewards_freeze.py` proves it. When a
  section ships, add its 3 slots to the pin file (copy them from rewards.json) in the same commit.

- [ ] Stale "N mastered" on a redesigned tier of the same size is not detected. Store a per-tier id hash in `syncTiers` and compare it with a build-time hash (display only).
- [ ] The Daily Review button on /train can show for retests of deleted questions (the review then says "Nothing to review today"). Give it a bank-aware count.

- [ ] Astro 7 upgrade on its own branch (npm advisories; none can be exploited here).
- [ ] A shared username-rule helper across `pin-login`, `admin` and `parent-api`.
- [ ] A single RPC `get_save_if_newer`.
- [ ] Owner: delete the test parent account from sign-up testing, if not done.

## Done

- [x] 20 Nov 2026: second big push live (`3500954`).
  - Submit-then-review WA/SA papers, now for English and Science too.
  - Encouragement lines.
  - English categories by paper section.
  - Science: 18 sub-topics, about 1,450 questions, with code-drawn figures to be replaced by real past-paper items.
  - Angles templates and nine-year Maths weights.
  - Display fixes: tier id hash and reversible parking of orphan retests.
  - Review WARN checks.
  - Game economy: Crumbs, the shop on the home map, replacement cards, achievement-only rare cards, the parent ledger.
  - GLOSSARY and ADRs.
- [x] 20 Nov 2026: hotfix live (`daa2547`). Plant transport worked solutions no longer show one letter per line.
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
- [x] 20 Nov 2026: Science SVG table headers overflowed their cells (owner screenshot, `ph-211`). New FAIL rule `figure-text-overflow` in `check_science.py`; `fillkit.table` wraps/widens; 76 figures rebuilt (74 shipped re-fingerprinted, keys unchanged).
