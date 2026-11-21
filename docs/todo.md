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

### One pool per sub-topic, milestones to competency (owner, 21 Nov 2026)
Proposed in `docs/past-paper-pools-design.md` and ADR 0011: difficulty tiers go; one past-paper pool per sub-topic
(playable at 20); correct answers leave the pool and add to the competency count, wrong ones go back; competency = a
majority of the sub-topic's past-paper questions correct; 3 cards at milestones; easier-first order; generated questions
support only. Supersedes the 'balanced thirds' tier split (owner OK'd it, then chose this redesign).
- [x] Owner approved (21 Nov 2026): wrong answer counts only when right on a later day (one 1-day retest); milestones 1/6, 1/3, majority (= competency); generated fill-ins never count; badge "Exam-ready".
- [ ] Build; live together with the past-paper upload. Done 21 Nov: store.ts (short retest, milestoneAt/syncMilestones, pool quizzes without a tier, tries per sub-topic; tests), pick.ts (pickPool easier-first; test), migration 006 pp_pool returns sub-topic + level + rank. Client plan (in progress):
  - A. pastpaper.ts: PpMode 'pool' (set per sub-topic in PP_SWITCH at upload: 'pool' at 20+ past-paper questions, else 'merge'); stub type (id, sub, level, ord; 4 placeholder options so paperOk keeps it) until hydrated.
  - B. ppfetch.ts: fetchPool(subs) -> stubs via pp_pool; fetchItems(ids) -> PpQ via pp-serve in chunks of 15; 'daily_limit' reported apart from failures.
  - C. train.ts: Sub.pool {count} for 'pool' sub-topics (pp_counts total), playable at 20; no tier hashes.
  - D. quiz page: pool quiz (no tier param; pickPool on the easier-first ids; title without tier; 20 minutes; finishQuiz opts.pools; answer(short) for pp ids of pool sub-topics); every mode hydrates the picked pp ids before showing them; daily_limit -> a plain message; Daily Review syncs milestones of pool sub-topics.
  - E. tier page [sub].astro: milestone view (counted/total bar, 3 markers with their cards, Exam-ready badge, Train button).
  - F. school page, G. result screen ("Milestone 1 reached"), H. parent page and suggest labels via MILESTONE_NAME; I. tests, build, screenshots.
  - Status 21 Nov: A-G done and committed (165 tests, build 0, sub-topic page checked at 420 and 1200 px). Parent page needs nothing yet (its mastery grid lists Maths only; make it pool-aware when Maths switches). Release order: owner OK -> apply 006, deploy pp-serve (+ ALERT_* secrets by the owner) -> upload Science with `ord`, PP_SWITCH 'pool' for sub-topics with 20+ (else 'merge') -> code review, push -> check live -> apply 007.

### Anti-scraping for past-paper questions (owner, 21 Nov 2026, ADR 0012) — before the bulk upload
- [x] (built 21 Nov, not applied) Migration 006: pool call (ids + order only), content call (<= 15 ids, text + figure paths), served log per account/day, limits (250 distinct/day, 40 calls/hour; half in the first 7 days; family-wide; admin/Test Player higher), flag table; drop the bulk `pp_items_for` and the readers' select policy on `pp-figures`. SQL tests in `sqltest.sh`.
- [x] (built 21 Nov, not deployed) Edge function `pp-serve`: checks the session and the limits through the content call, signs 10-minute figure URLs with the service role; emails the admin when an account is flagged (owner sets the Gmail sender secret in their own terminal).
- [x] (built 21 Nov) Site: `ppfetch.ts` and the quiz page use pool + content calls; admin page "Heavy use" report. Migration 007 (drop the bulk read and the readers' bucket policy) written, to apply after the new site is live.
- [x] 006 applied and pp-serve deployed (owner OK, 21 Nov 2026); checked: pool/serve callable by signed-in users only, flag_take service-role only, log under RLS, `ord` column present, the function refuses a call without a token (401) and allows the site's origin. The old bulk read stays until 007.
- [x] Science upload (owner OK), then push and the live check, then 007 (applied 21 Nov 2026).

### Past-paper precedent for generated questions (owner, 21 Nov 2026)
Rule: a generated question stays only if a past paper has a question testing the same concept (any format). Owner choices:
any format counts; no match = hold (reversible, reason recorded); show the judge's calibration and ~30 'no match' examples
before removing anything; thin tiers (< 20) are acceptable until past papers fill them. Scope: 7,376 generated questions
(Maths 3,888 from 524 templates, judged per template; Science 1,427, English 1,034, Chinese 1,027 per item).
- [ ] `scripts/pastpapers/concept_match.py`: pack (dev) -> server run (candidates by word overlap from all 58k scanned questions, same sub-topic first; Qwen2.5-72B judge, JSON with the matching question and a reason) -> report (calibration: real past-paper MCQs must find a twin, owner-ruled-out items and off-syllabus probes must not).
- [ ] English past-paper MCQs (21 Nov 2026): keys settled by owner-approved consensus. Local third model (72B) unreliable (owner sample: key right 11/17 against it); Sonnet judge 96.5% (fails 98%); Opus 20/21 on hard items (not run in full). Outside models (owner ran them): Gemini 98.5%, all three of Gemini/Grok/Perplexity agree -> 99.2% on 260 keyed. Verdicts in audit/blindcheck/consensus/english-<y>.jsonl: 173 keys confirmed, 233 replaced (four models against the key; owner spot check 20/20 for the models). load_pp: eng_incomplete + Q1-15 only (16-20 vocabulary cloze, 21+ visual text are the passage phase). English select: 2,897 (grammar 1,926, vocabulary 969; 230 consensus keys). Next: sample sheet for the owner, PP_SWITCH for eng-grammar-mcq / eng-vocab-mcq, figures/upload dry run, owner upload. Group A papers (6, misread keys confirmed by a double re-read) partly covered by the replacements; the rest of the re-read to apply.
  - [x] English visual text LIVE 21 Nov 2026 (pushed b06500d; on-screen check as Admin by the owner pending) (396 questions, 97 sets, migration 010 applied; site asks whole sets, pages once, tap to zoom). Owner, 21 Nov: the scanned questions showed next to the quiz's own text, so the pictures are now the poster only (poster_pieces: from the "Study this ..." line to the "For each question ..." heading; 76 questions held where either line is not found, set-no-cut; 7 in an exact duplicate set). Owner sample v2 check, then upload and push. Later: near-duplicate sets (same paper under two schools, OCR differs) are not caught; 76 set-no-cut could be recovered by hand. Follow-ups from review: a set cut short by an earlier quiz brings back its counted members (wholePassages takes the whole set; only matters for sets near 10 questions); `figures` reports set pages against --target-kb though they are sized at 220 KB; keep passage runs in their own --out (they overwrite selected.jsonl). Then Chinese cloze and reading.
  - [ ] Chinese cloze (400 in 101 sets) and reading (493 in 149 sets) built 21 Nov 2026: load_pp --passage chinese-cloze/chinese-reading; cloze stems are the blank's sentence with （16）＿＿＿＿ (neighbours （19）＿＿, filled by the quiz), passage page shown once; reading passage cut above its first question; keys = paper key confirmed by the blind solver (no outside-model verdicts yet: 194 cloze and 257 reading disagreements wait for an image pack). Also fixed: 13 live Chinese single items showed doubled numbers ("(1) 1 获得"), strip_num now strips "1 " before a Chinese word (chi1826fix re-upload). Owner sample, then upload and push. Later: Chinese dialogue (8 options).
- [ ] Maths past papers (21 Nov 2026): 1,274 uploaded-ready (19 pool, 12 merge). Follow-ups: past-paper MCQs are Paper 1 (no calculator) but carry no calc flag, so the "No calculator" badge does not show on them (add calc:false for Paper 1 items in load_pp/pp_items); Rate is now one pool, so the generated speed templates (owner request) are no longer served there; past-paper speed questions are (check the owner is fine, or keep Rate on 'merge').
- [ ] POOL_CAP follow-ups (review 21 Nov 2026): a re-upload re-ranks ord, so the counted 300 can shift and lower a child's counted number (reached milestones stay); freeze ranks of already-uploaded ids, or rank new items after them. strip_num drops a leading "(1)" from an option whose own text starts with a statement number when OCR already lost the printed label.
- [ ] Passage phase, English visual text (keys settled 21 Nov 2026): imgpack.py PDF packs (page scans + questions) run by the owner through Claude, Gemini, Perplexity; three-model agreement right on all 192 checked keyed questions after the owner confirmed the models on the 7 apparent misses (the keys there were wrong). Verdicts in consensus/english-<y>.jsonl: 78 confirmed, 23 replaced, 7 corrected (69 sets incl. the pilot; 57 disputed still held). To go live: upload each set with its visual-text page(s) as the figure, grouped as a set (group/seq), Q16+ rule lifted for these; English vocabulary cloze and comprehension, Chinese cloze/reading and the 1,008 Chinese "underline lost" items next, by the same packs.
- [ ] Chinese single items (21 Nov 2026): chi_incomplete (blank or pinyin options), consensus 185 confirmed / 67 replaced (Gemini + Perplexity 99.7%; owner spot check: models right on all judgeable). 1,805 ready; owner sample sheet before upload.
- [ ] Past-paper stems carry scanner markers children can see: "(cont)", "(sub)", "(a)"/"(b)" at line starts (about 40 Science items, e.g. pp-699ed1d689, pp-29e22e295c). Strip or rewrite them in load_pp select (with a selftest), check the shared-stem cases ("(cont)" means the stem continues a figure), re-upload.
- [ ] Server picture check of every Science figure (vision model: does the picture show what the stem refers to, and nothing from another question?): the tester found crops with only the options table and crops holding the previous question, which the page rule cannot catch. Owner OK pending. Queue 21 (21 Nov): GATE FAILED on all 4 prompts: Qwen2.5-VL-32B calls every crop "complete, belongs to the question" (it misses the options-table-only crop, the previous-question crop and the earlier known-bad crops), so the vision check is shelved. Proposed instead: an OCR-word check per crop on dev (another question number at the margin or a second (1)-(4) option set inside the crop; a crop whose words are only the option texts). Note: cropcheck's tester gate cases read sci1826b; a re-select that drops held items needs them pointed at stable copies.
- [ ] load_pp table_rows (21 Nov 2026), latent, no effect on current data: all-lowercase two-item lists ("heart, lungs") would be sent for a picture (require capitalised cells); rows OCR'd as "Light,Heat" are missed (split on \s*,\s*).
- [ ] Science pictures (tester reports 21 Nov 2026): 372 of 1,250 uploaded items carried a crop from another part of the paper (Booklet B question with the same number, 40-50 pages away), and figure links expired after 10 min (review showed no images). Fixed: `own_page_crops` in load_pp select (crops only on the question's pages; 89 items whose only crop was elsewhere are rejected `crop-other-page`), 2 reported items held, pp-serve links 2 h. New set /data/alvin/tmp/cookie-codex/ppimport/sci1826b: 1,162 items, 1,018 figures. Owner: deploy pp-serve and re-upload (with --subtopics so sci-systems-air-gases' last row is switched off).
  - [ ] Results so far (21 Nov 2026): pass 1 too strict, pass 2 (lenient) wrongly matched 5/19 ruled-out probes, pass 3 pair check (queue 20) confirmed only 2/7 real twins and wrongly matched 1/5. Nothing held. Next: a judge that passes both calibration sets (stronger model, or 2-of-3 across passes), then show the owner calibration + ~30 samples.
- [x] Review fixes before the full run (21 Nov): option digits kept (only a bracketed label is stripped), Maths units keyed (sub-topic, template), figure labels in the probe text, long passages keep their question, unparsed replies and unjudged probes are never a no-match (coverage in the report), verdicts tied to the question text, tolerant resume. Queue 18 stopped at 1,600 and re-run from scratch at 06:56.
- [ ] Show the owner the calibration and samples; on OK, hold the no-match items (review.json ship false / Maths templates) and rebuild.

### MCQ push (owner, 21 Nov 2026)
Scope: MCQs only, all 4 subjects, 2018-2026. Target: 90% of MCQs per subject recovered; the rest go to a holding list
with a reason, processed later (not every question is recoverable: unclear scans, no answer sheet). Owner decisions:
(1) a question with no answer key may ship if two independent models agree AND that agreement is measured at 98%+ on
keyed questions first (shown to the owner; model-answered rows marked in the data); (2) passage-based MCQs (cloze,
comprehension, visual text: 33% of English, 43% of Chinese MCQs) are phase 2; (3) when the blind check disagrees with
the key, a third, different model decides 2 of 3, else holding list; (4) Science first, then Maths, then English and
Chinese. Baseline 21 Nov (scanned cleanly / with key / blind agrees): Science 7,250 MCQs 56/28/18%, Maths 4,410
71/40/6%, English 7,879 76/59/8%, Chinese 6,565 35/29/7%; tag accuracy vs gold 87/97/83/85%.
- [x] 1. Text rules made for English rejected short Chinese stems (2,801 text-short, 899 low-alpha): fixed 21 Nov (CJK characters count triple toward the 20-character minimum; blanks and punctuation are left out of the letter ratio). Chinese scanned cleanly 35% -> 90%, with key 29% -> 74%. The 539 short English stems are correct rejections (the scan kept only the underlined word, not its sentence): repair pass. Watch: pinyin items lose the underline that marks the tested word (the options make it clear, but the repair pass should restore it).
- [x] 2. Blind check Maths, English, Chinese 2018-24: queue 17 done 21 Nov (about 10,800 keyed MCQs, 67-81% agree per year; results in `audit/blindcheck/<subject>-<year>.jsonl`).
- [ ] 3. One server repair pass per failed MCQ (re-read from its page: options, statements A-D, options in the picture, figure box, unclear key).
- [ ] 4. Model-consensus answers where there is no key: measure precision on keyed items first (98% bar), show the owner.
- [ ] 5. Third-model adjudication of blind-check disagreements.
- [ ] 6. English and Chinese sections set by position in the paper (booklet, question number), not by the tagger.
- [ ] Site-ready list v1 (21 Nov 2026, `/data/alvin/tmp/cookie-codex/siteready/site-ready-mcq.csv`, sent to the owner): 2,758 MCQs (Science 1,297, Maths 251, English 543, Chinese 667; standalone sections only). Tiers with 20+: Science 27/105, Maths 1/93, English 3/6, Chinese 6/21. Competent is thin everywhere because the tier comes from the question's position in the paper (`--tier-rule position`). Tiers are being replaced (ADR 0011). v2 (21 Nov 2026, after queue 17: Maths/English/Chinese 2018-24 blind check, agreement 67-81%): 8,045 site-ready MCQs (Science 1,297, Maths 1,315, English 2,863, Chinese 2,570); sub-topics with one pool of 20+: Science 24/35 (the 3 inquiry-skill sub-topics have none), Maths 19/31, English 2/2, Chinese 5/7. v3 after the repair/answer passes.
- [ ] 7. Holding list file per subject with a reason per question; recount against the 90% target after each pass.

- [ ] Fix the answer-key grid reading in `scripts/pastpapers/vlm_read.py`. Partly done 20 Nov 2026: `scripts/pastpapers/anskey_ocr.py` reads grids from the OCR word boxes (>= 2 agreeing reads per cell) and `load_pp.py select --ocr-keys` uses it as a fallback; the rest (rotated and badly scanned key pages, papers with no key page) still needs a better read.
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
  - 20 Nov 2026 result: Chinese gate PASSED (82%), Maths PASSED (97%). English scored 0% because the server's `english.json` still had the old MOE sub-topics while the gold file uses the Paper 2 sections; synced and re-run as queue 14 (`vlm/run_tag14.sh`, the stale output kept as `tags72r10-stale.jsonl`). English re-run (queue 14, 21:38): sub-topic 83% (86/104, gate 80%), but the gate script reported FAILED on its pattern check (11,340 of 23,507 with no pattern, limit 10%). The blanks are all in sections with no English pattern defined (Editing, Synthesis, Comprehension Cloze 100% blank; Comprehension OE 91%); the Booklet A sections are 0% blank. So English passes on what the gate means to test. 21 Nov 2026, against the same gold, old vs new tags: Maths 89% -> 97%, English 0% (old MOE sub-topics that no longer exist, and only 2 of 9 years) -> 83%, Chinese 85% -> 82% (new tags fill twice as many patterns). Owner OK: Maths and English switched on the server and dev (`tags72.jsonl` = the new tags; old kept as `tags72-pre-r10.jsonl`). Chinese kept on the old tags because its topics were slightly better. Open: improve the Chinese rules and re-tag (`vlm/tag10/chinese-compare.txt` lists the misses); fix the gate to count blank patterns only in sections that have patterns.
- [ ] "Report a problem with this question" (owner OK, 21 Nov 2026): built, not live. Migration `005_question_reports.sql` (table + `report_question` RPC, children/Test Player/admin only, one report per child per question, 30 a day; `sqltest.sh` checks pass), the link under every answered question and in the paper review (`quiz/index.astro`), and `load_pp.py where <id>` (paper, PDF page, crops, key, holds). Applied to the live project and pushed 21 Nov 2026 (owner OK). Open: read reports (query in the 005 header), fix each confirmed one, and turn a new fault class into a check.
- [ ] Drawn pictures in generated Science (owner report, 21 Nov 2026: "the picture of the flower is poorly drawn; drawings from past papers only; tables, flowcharts and graphs are OK"). 457 of 1,433 generated Science questions carry a drawn picture (374 code-drawn SVG, 83 line art). Owner: remove a sub-topic's drawn questions once its past-paper questions reach 20 per tier (not before); symbol diagrams stay (circuits, light rays, set-up schematics); pictures of real things (flowers, animals, apparatus) go. Open: classify the 457 (drawing vs symbol diagram vs table/graph), then remove per sub-topic as past papers arrive. No new drawings.
- [x] First owner reports (21 Nov 2026, 5, Plant reproduction): rq-202 ovule solution now links ovary -> fruit with ovule -> seed; rq-205 option reworded to "Seeds do not need light to germinate"; rq-204 removed (repeats rq-205's table); rq-221 removed (reproduction from plant parts is not taught at P6, owner); rq-214 (flower drawing) left for the drawings rule above. Review follow-up: the same ruling also removed rq-818 (Bryophyllum plantlets), rq-119 (strawberry runners), rq-211 (rose cuttings) and rp-013 (rose cutting, found by the new rule); tiers now Basic 24, Intermediate 24, Competent 22. Kept: sci-plant-parts pp-009/pp-074 (a money-plant cutting is only the setting; they test what roots do, and the stem states the roots grew). New WARN rules in check_science.py: `plant-parts-reproduction` (0 now) and `shared-figure` (shipped items of one sub-topic sharing one figure).
- [ ] Shared figures (from the owner's report on a repeated germination table): `check_science.py` WARN `shared-figure` lists 105 figures used by 2+ shipped items (e.g. one food web carries 11 questions; rq-207 shares the four-fruit dispersal table with rq-114/115/116). Owner to decide: allow a figure set (several questions on one picture), cap it (e.g. 2 per figure), or remove repeats. Many are drawn pictures that the drawn-picture rule will retire anyway.
- [ ] Statement re-read: server queue 16 (`vlm/run_tag16.sh`, `scripts/pastpapers/stmt_reread.py`, VL-72B, 141 Science items) started 21 Nov 04:35. Then: `select` uses a usable read (statements into the stem, combinations as options), blind-check those, spot-check a few.
- [ ] Queue 15 result (21 Nov): 206 Science items with reread/OCR keys blind-checked, 102 agree (53%, about the 58% of all Science keys; paper sci-2026-024 0/7, its key page is probably misread). Merged into `audit/blindcheck/science-<year>.jsonl` (old files `.pre-q15`); `select --ocr-keys --reread-keys` 2018-2026 now 1,297 items (+73). The 2025-26 upload set does not use these flags yet.
- [ ] Statement questions (owner spot-check, 21 Nov 2026: pp-3f46ebd0cf). A question that lists statements A-D and gives combinations as the options ("(1) B and D only") was read with the statements as its 4 options; the real options were lost (sometimes cropped as a "figure", sometimes another question's picture was cropped instead), so the options and key shown would be wrong. New `select` reject `options-are-statements` (all 4 options lettered A-D in order; selftest): 135 Science items 2018-2026, 25 in 2025-26 (18 were in the 2025-26 selection, now 221 items). Open: re-read these on the server as statement questions (statements A-D into the stem, the 4 combinations as options), then blind-check them; the same check for Maths/English/Chinese.
- [ ] Review points left open (20 Nov 2026 `/code-review` before push; all fail closed, none reaches the site): (1) reread keys need a blind run that uses them: queued 21 Nov 2026 as server queue 15 (`vlm/run_tag15.sh`, 206 Science items: 172 reread + 34 OCR-only keys, folder `blindcheck/q15`; `select` rejects now carry the key for this); (2) the reread and the first vision read are both VL-32B, so their errors correlate (the blind check still has to agree); (3) `find-answer-pages` can call a late question page an answer page from a repeated header alone (loses items, measured precision 0.97); (4) `questions_on_answer_pages.json` is not refreshed when the detector changes: re-run `find-answer-pages` for all years after any detector change. (5) 21 Nov review: `needs-blind-check-ocr` is decided before the garbled/figure checks, so a blind run may include a few items that fail later anyway (GPU time only); a crop held in `hold-crop.txt` is not re-checked until its line is deleted.
- [ ] Automatic crop review (owner, 20 Nov 2026: the server model should check pictures, not a person): (a) script fixes in `load_pp.py figures`: grow a crop cut off at an edge to the next blank band, straighten skewed scans; (b) server pass with Qwen2.5-VL-32B per selected item, crop next to its full page: is the figure complete, does it belong to this question, does it carry part of another question; a fail goes to `hold-auto.txt` (read like `hold.txt`). The owner then only spot-checks a sample per sub-topic. Run (b) after queue 10.
  - Built 20 Nov 2026 (not yet run): `scripts/pastpapers/cropcheck.py` (pack/pickup dev side; gate/run/merge on the server), `load_pp.py cropcheck-apply` writes `hold-auto.txt` (read by `select`/`upload`), server queue 11 (`vlm/run_tag11.sh`: waits for queue 9, gate, full run); queue 10 now waits for queue 11. Open: gate result (must pass first), then `cropcheck.py pickup` and `cropcheck-apply`; refresh the item list after queue 9 recovers more items with `cropcheck.py pack --push`.
  - 20 Nov 2026 result: the gate FAILED, so queue 11 did no full run. Qwen2.5-VL-32B called nearly every crop complete and caught at most 1 of the 3 known-bad crops on any of 4 prompts (`cropcheck/gate.log` on the server). The deterministic fixes in `figures` did run (2025-26: 100 straightened, 88 grown, 9 still touching an edge, 1 not located). Options for the owner: (a) hold the 10 unresolved crops automatically and use the person spot-check (about 5 per sub-topic) as the picture check; (b) try Qwen2.5-VL-72B-AWQ on the same gate (not on the server yet: about 40 GB to download), and run the full check only if it passes.
  - Owner chose both (20 Nov 2026). (a) done: `load_pp.py figures` writes `hold-crop.txt` (10 items in 2025-26; read by select/upload/review) and `review --subtopics all --sample 5` builds the spot-check page (2025-26: 123 items, 28 sub-topics, held items left out). First item already showed a crop from another question (pp-6963c68b11, now in hold.txt), so the spot-check matters. (b) queued: server queue 13 (`vlm/run_tag13.sh`, `PP_VLM` env in cropcheck.py) waits for queue 10 and the VL-72B download, runs the same gate, then the full run on all 4 GPUs only if it passes.
  - 20 Nov 2026 result: the VL-72B gate FAILED too (best prompt 4 of 5 right, none 5 of 5; `cropcheck/gate72.log`). It now catches the bad crops but rejects good ones: it said the clean pp-59bab0deb1 diagram "includes part of question 5" on 3 of 4 prompts. So no automatic picture check; the owner's spot-check (a) is the picture check. Not worth another model unless a gate set of 20+ crops is built first.
- [x] 20 Nov 2026: first past-paper sub-topic live. Owner reviewed and uploaded Plant transport (3 questions: 2 Basic, 1 Intermediate, merged into the generated tiers); `PP_ENABLED = true`. Next imports in order: forces, survival, plant reproduction, energy, photosynthesis, adaptations, resp-circ, heat, circuits (after queue 9 and the crop check).
- [ ] Past-paper follow-ups from the go-live review (20 Nov 2026), none affecting Plant transport today:
  - [x] 20 Nov 2026 (`tierPoolIds` in pastpaper.ts; also a failed pp fetch now reports nothing for a switched sub-topic): 'replace' tiers (20+ pp items): Daily Review always merges, so it stores gen+pp while the page counts pp only; make tierIds() in review send the tier quiz's pool, before any sub-topic reaches 20 pp items in a tier;
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
- [x] 20 Nov 2026: exam-standard audit of 15 generated Science sub-topics (1,133 shipped items, 5 agents): 45 items fixed (joke distractors, stems leaning on other items, 4 figure/stem contradictions, 2 tied answers, 1 rewritten as ph-929); no wrong keys found. 18 doubtful items listed for the owner in /data/alvin/tmp/cookie-codex/sciaudit/*.json. Forces effects and Energy forms not audited (86 and 96 past-paper items will replace most). Tied answers and figure/stem contradictions have no cheap automatic check (they need reading); they stay a per-batch review item. Owner scope rulings (20 Nov 2026, P6 teaches these even where the syllabus JSON summary omits them): blood carries water as well as oxygen and digested food; pupils investigate overloading a spring past its elastic limit; plants respire too.
- [ ] figure-text-overflow follow-ups (code review 20 Nov 2026): run the same check on Math figures in `check_math.py`; add vertical fit (wrapped cells, captions below the viewBox); width is a fixed per-character estimate (0.55/0.6 em), so a label a few px over its box can pass (ci-111 "object" was widened by hand after the visual pass).
- [ ] Minor review notes (20 Nov 2026, not blocking): cropcheck-apply uses the one global pack whatever --subject (only Science has packs); a pack stamp leaves page images out and old figs/ are not cleared; the ci-005/ci-010 switch exemption is a key list in bankcommon (a per-item field would travel with the item); warning_self_tests leaves scripts/quiz/science on sys.path. Design choice kept: one bad past-paper row fails the whole fetch (fail closed).
- [x] 20 Nov 2026: circuit items (owner photos `ci-114`, `ci-102`): 22 figures drew a switch S the stem never mentioned. New FAIL rule `figure-unstated-switch` and WARN `stays-lit-unqualified`; stems now state the switch (`ci-004/005/010` only name it, since the drawn state is the question); `ci-102`/`ci-124` keys say "stays lit at the same brightness"; `ci-104/105/106` figures redrawn to match their stems; 26 items re-fingerprinted. Doubtful, left: none.
