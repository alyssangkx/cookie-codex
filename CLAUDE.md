# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

The running to-do list is `docs/todo.md`: add every agreed or recommended item there, and tick it only when done.

Terms are defined in `GLOSSARY.md` and past decisions are in `docs/adr/`: read them before renaming, merging or redefining a concept.

## Working rules (for every agent)

- **Before a batch of questions:** state the syllabus scope and the definitions you will use. Keep definitions
  consistent across items; for example, pollination means pollen landing on the stigma of the same kind of flower.
  Stay inside the P6 syllabus: no mass and acceleration, no action-reaction.
- **Every question:** exactly one defensible answer ("mainly" when two causes act). The figure draws what the stem
  describes. Captions, labels and alt text never name or imply the answer. The stem never gives the answer away. No
  item depends on another item's figure. The correct option is the strictly longest in no more than about 30% of a
  sub-topic.
- **When unsure** whether something is in scope or what the owner wants, say so in your report. Don't guess.
- **Every fault class a review finds becomes an automatic check** (the WARN rules in the `check_*.py` scripts), not
  only a one-off fix.
- **Touch only what the task needs.** Commit only your own files, by explicit path (never `git add -A`); other agents
  share the working tree. Never push unless the owner asked; a `/code-review` comes first.
- **Prove it works:** run the checks and tests and report their exit codes. Look at rendered figures and pages as
  screenshots, not just the code.

Alyssa's Cookie Codex is a static Astro site with two parts:
- **A PSLE revision game.** A Primary 6 student answers timed multiple-choice quizzes (PSLE 2027 syllabus; only Math has questions so far) and earns Cookie Run: Kingdom cookie cards.
- **The Codex.** A reference library of all 186 cookies.

Python scripts in `scripts/` generate all the data. The Astro site in `site/` renders it. Accounts and sync use Supabase (project `kxxnipzejmyctnziojzd`, Singapore): progress is cached in the browser and synced to the server for a signed-in child (see Accounts below).

## Commands

Site (run from `site/`; `node_modules` is not committed):

```bash
npm install
npm run dev       # dev server
npm run build     # static build to site/dist/
```

Tests and checks (from the repo root):

```bash
node --test site/src/lib/*.test.ts        # game logic: store, pick, suggest (Node 24 strips TS types)
python3 scripts/quiz/math/build.py        # regenerate all Math question banks (--topic math-ratio for one)
python3 scripts/quiz/test_stable_ids.py   # a reworded stem keeps its id
python3 scripts/quiz/math/test_isolation.py # removing a template leaves other sub-topics' questions unchanged
python3 scripts/quiz/check_dupes.py         # must print "0 failures": no question stem appears under two sub-topics (each question has one category)
python3 scripts/quiz/check_math.py        # must print "0 failures": re-solves every question independently (SHOW=n prints n failures, default 40)
python3 scripts/quiz/coverage.py          # top-school question types covered -> docs/quiz/coverage.md
python3 scripts/quiz/build_rewards.py     # card reward per (sub-topic, tier) -> site/src/data/rewards.json
python3 scripts/quiz/build_progression.py # P1-P5 sub-topics (tries per day) -> site/src/data/progression.json
```

After changing generators, run build → check_math → coverage → build_rewards → build_progression. The rewards depend on which sub-topics have questions.

Cookie data refresh (needs `requests`; both scripts hit live sites with a delay per cookie):

```bash
python scripts/crk_images.py         # portraits -> downloads/crk_cookies/ + manifest.csv
python scripts/build_cookie_data.py  # -> site/src/data/cookies.json, copies images to site/public/cookies/
```

## Architecture

### Question banks (`scripts/quiz/math/`)

- **Generators.** Each `topic_*.py` registers parametric generators with `@template(topic, level, *outcomes)`, defined in `common.py`.
  - A generator picks random numbers and returns a stem, the correct value, and wrong options. Each wrong option comes from a named mistake (a `tag` plus a `why`).
  - `build()` takes two method mistakes first, then one careless slip.
  - `whole=True` drops non-integer distractors.
  - `auto_slips=False` turns off the automatic fraction slips (use it for decimals and money).
  - `calc=True` marks a calculator question (PSLE Paper 2 style). The default `calc=False` is Paper 1 style (no calculator): the quiz shows a "No calculator" badge, and `check_math.py` fails any step in the worked solution that is not workable by hand (`hand_problems()` in `common.py`: 4-digit by 2-digit multiplication, division by 1-significant-digit numbers, by up to 12, or by 2-digit numbers with a short exact quotient). `calc` is not part of the id.
- **Independent check.** Every template needs `@checker(fn)`: a second solver (brute force, plug-back, or exact `Fraction`) that `check_math.py` compares with the stored answer.
  - Template names can repeat across topics. Lookups are by `(topic, key)`.
- **Diagrams.** Use `figures.py` (SVG with `currentColor`) plus `figures_<group>.py` helpers. A figure must agree with the stem's numbers and never show the answer.
- **Banks.**
  - `build.py` writes `site/src/data/quiz/math/<topic>.json`. Each template draws from its own random stream (topic, level, template key, seed): changing a template never touches other sub-topics. Inside a sub-topic, templates' candidates (each from its own stream minus its own repeats) are merged by weight and the first n new stems are kept, so removing a template never changes a sibling's questions unless the level's quota shrinks (the variety cap of 10 per unit of weight binds in some sub-topics); adding one or raising a weight can push siblings' last questions out. `weight` must be a whole number >= 1. Stems are never compared across sub-topics (`check_dupes.py` enforces that). `PAPER_MARKS_PCT` keys are asserted to be real sub-topics. Questions per (sub-topic, level) follow the sub-topic's share of PSLE paper marks: 14 per 1% of marks, capped at 100 and at 10 per unit of template `weight`, but never under 25 (the floor wins, so a one-template level still gets 25) (`@template(..., weight=n)`, default 1, not part of the id). Since 20 Nov 2026; the switch changed most Math ids once (owner-approved: learning first, awarded cards stay).
  - A question is filed under the sub-topic of its **first** outcome id.
  - Question ids are `<topic prefix>-<level letter>-sha1(topic | template key | canonical JSON of params)[:10]` (`stable_id()` in `build.py`). Rewording a stem, explanation or figure keeps the id; changing a template's numbers or param structure makes a new question. Never key progress on stem text. `check_math.py` fails on a duplicate id, and `test_stable_ids.py` proves a reword keeps ids.
  - There is no id alias map. The v1→v2 migration simply clears `questions` (no v1 saves were ever deployed). Ids that leave a bank later (the 20 Nov 2026 redesign: the first banks were a pilot; the Math re-seed replaced most Math ids) stay in a save as orphans: they are never asked again and the parent page leaves them out (their states stay in the save: deleting them from a tab running an older build could wipe live progress, so nothing deletes them), and pages show a tier's stored "N mastered" only when its stored `total` equals the current bank count (`liveMastered`), so a count from a replaced bank (or an unknown bank size) reads as 0 until the next quiz recounts it; a redesigned tier of the same size is not detected (display only). Cleared tiers and cards stay (owner: game progress may be wiped and reset if a redesign needs it, but cards always stay). Deliberately no schema bump: an old tab meeting a newer save version would start fresh and could push that over the server save. A rewritten item must get a new key (English, Chinese, Science ids are sha1(topic|key)), or the new question inherits the old one's progress.
- **Coverage.**
  - `patterns.json` is the catalogue of question types seen in top-school P5/P6 papers (from OCR'd PDFs).
  - A template covers a type by naming its `math-pat-...` id in its docstring.
  - Speed types are excluded because Speed is not in the 2021 syllabus.
- **English passage sets and visual text.** English keys `vis-NN-K` (visual text), `read-NN-K` (comprehension) and `ecloze-NN-K` (cloze) form sets: `english/build.py` emits `group`/`seq` and ships a set only if every item shipped (`hold_sets`). Cloze blanks are `(1) ____`; the asked one is `(N) ________` (8 underscores) and the quiz page highlights it. An item may carry `"visual": {kind: poster|notice|brochure|timetable|email, title, subtitle?, blocks: [{heading?, lines[]}], footer?}` (plain strings; all items of a `vis-` set share it, `check_english.py` enforces). The quiz page draws it as a CSS card above the stem (timetable lines with ` | ` become a table; email `From:/To:/Subject:` lines become the header) and the review screen shows it collapsed.
- **Syllabus.** `site/src/data/syllabus/<subject>.json` is strands → topics → sub-topics → outcomes, surveyed from SEAB/MOE (sources in `docs/syllabus/`).

### Chinese banks (`scripts/quiz/chinese/`)

- **完成对话 (8-option dialogue sets).** Sub-topic `chi-dialogue-mcq` has 8 options (A-H), not 4: a set is one dialogue with 4 blanks, one item per blank (keys `duihua-NN-K`), all sharing the same stem text and the same 8 phrases (4 used once each, 4 distractors). `build.py` shuffles the 8 with one seed per set, emits `group`/`seq`, and ships a set only if all 4 blanks pass review. `check_chinese.py` checks the shared stem/options, 4 different answers, explain length 8. The quiz page shows `chi-dialogue-mcq` questions in a 2-column grid, and greys out a phrase already answered correctly for an earlier blank in the same quiz (a hint only). WA/SA papers skip 8-option items.

### English banks (`scripts/quiz/english/`)

Same contract as the Chinese banks, with 4 options per item (passage sets: see Question banks above).

- **Sections are the sub-topics** (owner decision, 20 Nov 2026). The English school's sub-topics are the PSLE Paper 2 sections in paper order: Grammar MCQ, Vocabulary MCQ, Vocabulary Cloze, Visual Text (strand `eng-p2a`, Booklet A), Grammar Cloze, Editing, Comprehension Cloze, Synthesis & Transformation, Comprehension OE (`eng-p2b`, Booklet B). In `site/src/data/syllabus/english.json`, `strands` holds them (each section is a topic `eng-sec-<x>` with one sub-topic `eng-<x>` and one outcome `eng-<x>-1`; ids match the past-paper audit's section ids); the MOE syllabus moved to `syllabusStrands`. Editing, Comprehension Cloze and Synthesis & Transformation are open-answer (`mcqTestable: false`) and stay "Coming soon" with no items (`check_english.py` fails an item filed there) until the site can mark open answers. Vocabulary Cloze is "Coming soon" until real passage items exist (the single-sentence "closest in meaning" items are in Vocabulary MCQ). The sub-topic flags the format: `passage: true` sections take only passage-set items and the others only single items; `cloze: true` (Grammar Cloze, Comprehension Cloze, and Chinese `chi-cloze-mcq`) takes only blank-filling `ecloze-` sets, and the quiz page fills blanks for exactly these sub-topics (`clozeSubs` in `train.ts`). Grammar Cloze is asked blank by blank with 4 options (the paper uses a word box); Comprehension OE holds the reading passages, practised as MCQ. `rewards.json` lists English in paper order (the training pages show that order) but `build_rewards.py` assigns its slots playable-first, and only playable sections are capstones, so the legendary and super-epic Competent cards sit on earnable tiers. English has 24 new cards and fewer playable tiers, so some new cards wait on "Coming soon" sections. The school page groups the sections by booklet (`listGroup`) and calls them sections (`unitName` in `suggest.ts`).

```bash
python3 scripts/quiz/english/build.py     # items/*.json (the sub-topic is each file's "subtopic" field; several files may share one) + review.json -> site/src/data/quiz/english/<topic>.json
python3 scripts/quiz/check_english.py     # must print "0 failures"; its WARN section (stem echo, near-duplicate options, correct option longest in >35% of a sub-topic) does not fail unless --strict
python3 scripts/quiz/english/coverage.py  # -> docs/quiz/english-coverage.md
python3 scripts/quiz/build_rewards.py     # after the banks change
```

- **Frozen reward slots (owner, 20 Nov 2026).** `scripts/quiz/english_frozen.json` pins the English slots of every section that is playable, so a cleared tier's card never changes when another section opens (`freeze_english` in `build_rewards.py`; unpinned slots only change if their cookie collides with a pinned one; Math, Science and Chinese are untouched). When a section ships, add its 3 slots (copied from `rewards.json`) to the pin file in the same commit. `python3 scripts/quiz/test_rewards_freeze.py` simulates newly playable sections and fails if a pinned slot moves.

- **Items** are `{key, level, outcome, syllabus, pattern, stem, options[4], answer, explain[4], solution[], gloss?}`. `pattern` is an id from `patterns.json`; `outcome` is the section outcome (`<file's sub-topic>-1`); `syllabus` is the MOE syllabus outcome (in `syllabusStrands`), metadata the bank keeps as the question's second outcome.
- **Review gate.** An item ships only if `review.json` has `"<subtopic>|<key>": {"ship": true, "fingerprint": ...}` for its current stem, options, answer, explain, solution, level, outcome and pattern (`fingerprint()` in `scripts/quiz/bankcommon.py`, shared with the Chinese build). Anything else is dropped, unreviewed or stale. Options are shuffled with a seed from the key; ids are `engsec-<sha1(topic|key)>` and ignore the level (moving to the sections on 20 Nov 2026 changed every English id; progress on the old ids is orphaned, cards stay). Empty and stale banks are not written or are deleted.
- **Checks.** Stem has a `____` blank or a `?`; options are 4 distinct strings with the same first-letter case and end punctuation; explain is null only for the answer.
- **Site.** `train.ts` marks English `ready` once a sub-topic has a playable tier (20 questions). `build_rewards.py` lists the English sections in paper order; English star slots draw from their own RNG and the main RNG replays the old layout's 12 English draws (`LEGACY_ENGLISH_DRAWS`), so Math, Science and Chinese rewards do not move when English changes. English is open on the home map (`home-hotspots.json`), with the `chinese-english-open` art; `index.astro` shows a school open only when its hotspot says "open" AND `SCHOOLS.ready` is true, and throws if the art for the open set is missing.

### Science banks (`scripts/quiz/science/`)

Same contract as English (4 options, items + `review.json` with fingerprints, fail-closed, key-seeded shuffle, ids `sci<strand>-<sha1>`), reusing `scripts/quiz/bankcommon.py`. No passage sets.

```bash
python3 scripts/quiz/science/build.py     # items/*.json (each file has "subtopic") + review.json -> site/src/data/quiz/science/<topic>.json
python3 scripts/quiz/check_science.py     # must print "0 failures"; WARN section as English plus figure text naming the answer and figure/stem mismatch (--strict makes warnings fail). FAIL rule `figure-text-overflow` (`svg_text_overflows` in `bankcommon.py`): an inline-SVG label wider than its centred cell/box, or past the viewBox, fails; `fillkit.table` wraps a cell at a space and widens the column, never shrinking the font
python3 scripts/quiz/science/coverage.py  # -> docs/quiz/science-coverage.md
python3 scripts/quiz/build_rewards.py     # after the banks change
```

- **Figures.** An item may carry `"figure"`, copied into the bank question and part of the review fingerprint: (a) an inline SVG string made by code (black and white, `currentColor`, with a `viewBox`; no scripts, handlers, external refs or other colours), drawn like Math figures; or (b) line art `{"img": "/science/<file>.webp", "alt": "...", "labels": [{"x": 0-100, "y": 0-100, "text": "..."}]}` with the file under `site/public/science/`. The quiz page shows (b) as the image with the labels placed on it as escaped HTML (`figureHtml` in `quiz/index.astro`). `check_science.py` validates both, and fails a label that equals the correct option.
- **Site.** `train.ts` marks Science `ready` once a sub-topic has a playable tier. The home map shows a school open only when its hotspot says "open" AND `SCHOOLS.ready`; flip the Science hotspot in `home-hotspots.json` only after the content passes review (the `all-open` art exists). When the first Science sub-topic becomes playable, `build_rewards.py` moves it to the front of Science, so Science slots shift; Math, Chinese and English do not.

### Game (`site/src/lib/`)

- **`store.ts`** is the only code that touches localStorage (key `ccx:save`, interface `SaveV1`, now `schemaVersion: 4`). Never read or write storage directly. Rules it implements:
  - **Clearing is mastery.** A tier is cleared when every question in it is retired (`questions[id].s === 0`), for all tiers (P1-P6, Math and Chinese). A question answered right the first time retires at once; a wrong one retires after its 1, 3, 7 day retests are answered right. The score and the ≥ 80% pass flag on a full 10-question quiz are kept for display only. `store.ts` has no question ids, so `finishQuiz(..., tierIds)` takes a `"sub|tier" -> ids` map from the quiz page (which has the banks loaded) and `syncTiers()` stores `mastered`/`total` on the tier state and clears a tier when they match, awarding its card (a duplicate adds a star). Other pages show `mastered` of the build-time question count. A cleared tier is never un-cleared. **Exception: a perfect first try on Basic or Intermediate, all subjects.** If a child's first-ever tier quiz on a sub-topic's Basic or Intermediate tier scores 10/10 (a full `QUIZ_SIZE` quiz), `finishQuiz` clears that tier at once (before `syncTiers`), awards its card and the next tier opens (`QuizResult.autoPromoted`; the result screen says "Perfect first try! <Tier> cleared, and the next tier is open."). "First" is per tier: no earlier tier attempt for that `sub|tier` in `s.attempts`; any earlier attempt on it, finished or abandoned (`open`), means it is not a first try, so quitting after a mistake and retrying cannot earn it. Competent is not included and clears by mastery; everything else follows mastery. A Daily Review can clear a tier too (`newlyCleared`).
  - **Tries per tier per day** depend on the sub-topic's P-level (highest outcome `level` in the syllabus JSON): 5 for P1-P5, 3 for P6 and all Chinese (`triesPerDay(sub)`). `site/src/data/progression.json` (from `scripts/quiz/build_progression.py`, run after `build_rewards.py`) lists only the P1-P5 sub-topics, so `store.ts` imports no big JSON; an unlisted sub-topic counts as P6. The daily cap is a parent setting, 45 to 120 minutes in steps of 15.
  - Spaced retest: a wrong answer is due again in 1, then 3, then 7 days; a new question answered correctly retires at once. `questions[id].a` (optional) keeps the option text picked on the latest wrong answer for the parent page's "Questions answered wrong" list, which also lets the admin pick a child and read that child's save (select only; RLS already allows an admin).
  - Practice papers never retire questions.
  - **Orphan retests are parked, never deleted (ADR 0002).** Daily Review loads every bank and calls `syncParked(s, ids, true)`: a retest state whose id is in no bank gets `parked: true`, and any parked id that is present is unparked before picking. Tier quizzes and papers only unpark the ids they loaded. `isDue` (so `/train`'s Daily Review button and `dueCount` without a map) skips parked states; `answer()` always unparks. Reversible on purpose: an older tab missing newer bank files may park live states.
  - **Past-paper tier counts.** `site/src/data/pp_counts.json` (`{"<sub>|<b|i|c>": n}`, numbers only, written by `load_pp.py upload --apply` or `counts`) lets `train.ts` count a tier as the quiz will (`ppTierCount`: merge = generated + pp, replace = pp once >= `PP_MIN_TIER`) for sub-topics in `PP_SWITCH` while `PP_ENABLED`; those tiers have `Sub.hash` undefined, so `liveMastered` uses the size check (pp ids are private).
  - **Stale "N of M mastered".** `syncTiers` stores `hash` (`tierHash` of the tier's sorted ids) next to `mastered`/`total`; `train.ts` computes the same per tier (`Sub.hash`). `liveMastered(st, count, hash)` needs the size and, when both sides have one, the hash to match; older states fall back to the size check. Both fields are optional: no schema bump.
  - A started quiz counts toward the daily tries (5 for P1-P5, 3 for P6).
  - The daily limits: the day ends at `dailyCapMin` minutes (default 120, parent range 45-180). The 10-quiz limit (`DAILY_QUIZ_CAP`) is **switched off for now** (`QUIZ_CAP_ON = false`, owner's request, 19 Nov 2026); set it to `true` to restore the rule below, where the day also ends at 10 quizzes, whichever comes first. The tests pass `true` to keep the cap logic covered. Tier quizzes and WA/SA papers count from the moment they start (`beginQuiz()` records an open attempt, replaced when the quiz finishes, so an abandoned one still counts), except a paper the child discards, or one put away after its time ran out: its record is removed at once, so it no longer counts (this only matters if the quiz cap is switched back on); Daily Review and retests inside a tier quiz do not. After the quiz limit only Daily Review stays open; after the time limit nothing does. `dayBlock(s, mode)` gives the reason and `blockMessage()` the text; the quiz page re-checks it in `begin()`. There is also a daily goal.
  - **Unlimited test account:** `isUnlimited()` is true when kv `profile-unlimited` is `1`, which the login page stores from pin-login's `profile.unlimited` (the server flag `profiles.unlimited`, migration 002; only the admin's own profiles may carry it, so naming a child "Admin" gives nothing; cached once per page load). It has no time cap, no quiz cap, no tries-per-day limit, and `tierOpen()` is always true so every tier is unlocked. Tiers under `MIN_POOL` are still unplayable; clearing, cards and mastery work normally.
  - The streak counts weeks with 4 or more goal days, so weekends never break it.
  - Card power reflects retention.
  - `migrations` runs on `load()` and `importCode()`. Add a new step there for every schema bump.
    - 1→2 keeps progress, cards, attempts, days, streak and settings, and clears `questions` (old stem-hash ids cannot be matched).
    - 2→3 changes no fields. A tier whose questions are all retired but not yet marked cleared only clears after its next quiz (`syncTiers` needs the question ids, which only the quiz page has). There is deliberately no load-time sync.
    - 3→4 sets `dailyCapMin` to 120 only if it is exactly 45 (the old default); other values were a parent's choice and stay. (Deliberate: the owner asked for a 2-hour cap for the existing child.)
    - `load()` copies the pre-migration save string to `ccx:backup`.
    - If a save is unreadable or a migration fails (no step, or a throw), `load()` keeps the raw string in `ccx:failed:1..3` before returning `fresh()`, and leaves `ccx:save` alone until a real save. A string already stored is not added again; when all 3 slots are full they rotate (2 to 1, 3 to 2, new into 3) so the newest broken save is kept; a legacy `ccx:failed` key is folded into the slots once and removed. Recover a save by copying a slot's value back into `ccx:save`.
    - `importCode()` writes no backup. The parent page calls `backupLocal()` only after the user confirms the import.
  - It also handles the save code (export/import). The PIN lives on the server only.
  - One allowed exception: the inline pre-paint gate script in `Base.astro` reads the single `ccx:auth` key (`AUTH_KEY` in `supabase.ts`) to redirect before first paint, because an inline script cannot import modules.
- **PIN login** (`supabase/functions/pin-login`, SQL in `supabase/migrations/001_init.sql`; applied and deployed, live-tested in Phase B). One atomic RPC checks then counts a device key (5 tries) and a `name:` (20, no token) or `trust:` (30, valid token) key; any locked key counts nothing. Locks double from 15 min to 24 h. The device fail count resets after 15 quiet minutes (forgives typos); name and trust counts only after 24 h, so pacing does not avoid escalation; escalation decays after 7 quiet days. Success clears the device and only the name-side key it used (a trusted login never resets a stranger's `name:` escalation; the admin can clear it). There is no IP limit. Worst case: about 240 days (stranger) or about 92 days (copied tokens) to 5,000 guesses; details in `docs/accounts-plan.md` section 5.
- **`pick.ts`** chooses questions:
  - tier quizzes are always 10 (≤ 3 due retests from the sub-topic, then new questions, then not-due retests, then retired ones);
  - Daily Review takes 5–15 due retests; due blanks of one passage are asked together in passage order (`reviewPassages`; only due ones, nothing added). In a cloze, blanks not in the quiz show their answer in grey (so nothing reads as skipped), and an open blank of the quiz is a button that jumps to that question (the current one moves after it);
  - WA/SA papers are mixed across chosen topics of one subject (Math, English or Science); only `paperOk` items (4 options, not in a passage set), so cloze, comprehension and visual-text sets and all Chinese stay out.
- **`paper.ts`** holds the paper rules (submit-then-review, 20 Nov 2026): the child answers every question with no feedback, can move back and forth and change answers, then submits; the score, then a step-through of wrong and blank answers only (`reviewList`). Wall clock (`tickPaper`): one pause of up to 10 minutes (`PAUSE_MAX`), submits itself at zero, also after a reload or a locked phone. A draft (ids, picks, clock) lives in kv `paper-draft` (not the save, so no schema bump), keyed to the player (`draftOwner`); `/quiz/?mode=paper` resumes it whatever the link asks, and `/paper/` shows a Resume banner. A `rev` counter stops a stale second tab from writing or submitting. A paper whose time ran out more than `GRACE` (10 min) ago is `stale` (`draftState`): put away unscored (`discardDraft`: no result, no retests, nothing booked) with a plain note; within the grace it is handed in. A new paper never replaces a live or due one (the quiz page and `/paper/` offer Resume / Hand it in / Discard; `saveDraft` refuses at rev 0), and a paper's open record is matched by its own ts (`finishQuiz(..., openTs)`, `closeOpenPaper`; `discardDraft` closes it at once), so a paper on another device never loses its record; `closeStalePapers` only removes open paper records over 2 days old. Choosing "Hand it in" on a due paper hands it in even if the grace runs out meanwhile. On submit each answer goes through `answer(..., retireNew = false, picked)`, so wrong and blank answers become 1/3/7-day retests as before; a blank left on purpose is stored as `LEFT_BLANK` (parent page: "left blank", tag `blank`), one at zero as `''` ("time ran out", tag `ran_out_of_time`). Papers pass `{}` as tier ids: they never clear tiers.
- **`encourage.ts`** picks the growth-mindset line on every result screen from `data/encouragement.json` (owner-editable): bands perfect / 80%+ / 50-79% / under 50%, a hash of the attempt time, never the same line as the attempt before (`lineForLast` walks the finished history). Chinese-subject results show the Chinese line with the English under it until `bilingualUntil`, then Chinese only.
- **`suggest.ts`** works out power (tier weights 1/2/3) and the "train today" suggestions.
- **`train.ts`** (build time only) holds sub-topics in reward order, question counts and the playable flag per tier (20 or more questions), rewards and card info.
- **Rewards are fixed and previewed:** there is no randomness at play time. All 186 cookies are used once each; the 7 commons sit on the first playable sub-topics.
- **Economy (`crumbs.ts`, owner's answers 20 Nov 2026, `docs/game-economy.md`).** Crumbs per finished quiz by AL band, retests, daily goal, streak week; the Shop (`/shop/`) sells the exact card at fixed prices (Super Epic, Legendary and milestones are not for sale); a cleared tier whose card is owned gives the next unowned card of its rarity (`rarityOrder` in `rewards.json`, derived from `slots` only, so it moves no slot); Super Epic per competency group (`competencyGroups`: Math/Science topics, English/Chinese paper booklets via `booklet`/`CHI_BOOKLET` in `train.ts`; members = sub-topics with a playable Competent tier, 2+), Legendary per subject once every sub-topic of it is playable at Competent and cleared, and a Legendary for a 20+ question paper whose questions span 3+ topics at 85%+ (one a week; the quiz page passes the questions' topics as `paperTopics`); paper Crumbs scale with length (x questions/10, max x3). Pure rules in `crumbs.ts`; `finishQuiz(..., opts)` takes `{ eco, retests }` (pages build `eco` with `toEconomy`); purchases go through `store.ts` `purchase()`, which re-reads the stored save so two tabs cannot double-spend. The save field `crumbs` is optional (no schema bump) and `cleanSave` keeps it.
- **Parked retests** store the bank-set hash that parked them (`banksHash` in `train.ts`; older tabs write `true`). `reviewDueCount` counts every due state not parked by the current banks, so the `/train/` button and school page never hide a retest an old tab parked; the school page unparks ids in the banks it loads, Daily Review re-checks the rest. The parent retest queue uses the same rule (`inReview`). After awaiting bank files, pages call `syncParkedStored()` (re-reads the stored save), never `save()` on a copy loaded before the await.
- Design rules are in `docs/game-design.md`, as amended by `docs/game-design-review.md`: no leaderboards or comparing children, no monetisation or loot boxes, a parent-set daily cap.

### Pages (`site/src/pages/`)

| Route | Page |
|---|---|
| `/` | Home base: the map art (`public/home/map-{wide,tall}.webp`, no text in the image) with HTML hotspots from `data/home-hotspots.json`. Re-check the hotspot positions with screenshots whenever the art changes. |
| `/train/math/` | "What do you want to train today?" |
| `/train/<school>/<sub>/` | Tier page with the reward preview |
| `/quiz/?sub=&tier=` | The quiz runner; also `?mode=review` and `?mode=paper&topics=` |
| `/paper/` | WA/SA paper builder |
| `/collection/` | My House |
| `/parent/` | Parent page: an admin at aal2, or a parent (aal2 once they enrol an authenticator). A parent also gets "Your family" (children and their usernames, PINs, rename, delete with a 7-day undo, delete account) through `parent-api`; shows the save on this device |
| `/login/` | "Who's playing?": username + 4-digit PIN pad, on any device; Turnstile CAPTCHA on a device without a device token, calls `pin-login` |
| `/admin/` | Admin email + password, TOTP (aal2), children, PINs, name locks, Test Player and its test tools |
| `/grownups/`, `/signup/`, `/signup/verify/`, `/reset/` | Parent sign-in (TOTP step if enrolled), open sign-up (consent boxes, CAPTCHA, email confirmation), verify link -> `parent-api register`, password reset |
| `/privacy/` | Privacy notice (version `CONSENT_VERSION` in `supabase.ts`) |
| `/codex/` | The Library (cookie shelf) |
| `/cookie/<slug>/`, `/personality/<tag>/` | Codex detail pages |

- `/data/quiz/<topic>.json` is a static endpoint serving the slim banks, which the quiz page fetches.
- Markup built with innerHTML needs `<style is:global>` with page-prefixed selectors, because scoped styles don't reach it.

### Accounts (`supabase/functions/admin`, `site/src/lib/{supabase,sync,testtools}.ts`)

- **Open parent sign-up** (docs/accounts-plan.md section 12; **live since 19 Nov 2026**: migrations `002_parents.sql` and `003_no_family_code.sql` (20 Nov) applied, `pin-login` v8, `admin` v8, `parent-api` v2 deployed; Auth CAPTCHA (Turnstile) and sign-ups on; Gmail SMTP from psleadmin@gmail.com). No family code (removed by migration 003, owner's decision 20 Nov 2026): a child logs in with a **username unique across the site** (letters first, then letters, digits, spaces, hyphens; up to 20) and a PIN; a parent picking a taken username gets `name_taken`; lock keys are `name:<name_key>` / `trust:<name_key>`; deletes are soft for 7 days (`deleted_at`, purged by `private.purge_deleted()`). Tests: `scripts/accounts/sqltest.sh` (001 + 002 + 003 in a Postgres container, 44 checks, needs docker) and `scripts/accounts/isolation.mjs` (two throwaway families against the live project; the owner runs it with the service key). Supabase Auth CAPTCHA also guards password sign-in, so server-side sign-ins (`pin-login`, `admin test_login`, the isolation script) use the service-role key, which Auth exempts (`verifyCaptcha` in supabase/auth). If Supabase changes that, child PIN login and Test Player login fail: re-run `isolation.mjs`, whose sign-in step names it.

- **`admin` Edge Function** (JWT verification ON; needs `app_metadata.role = 'admin'` and `aal2`): `create_child`, `set_pin` (shares `_shared/pin.ts` hashing), `clear_name_lock`, `list_children`, `create_test_player`, `test_login` (a session for the Test Player only), `delete_child` (non-test needs `confirm` = the name). Redeploy: `supabase functions deploy admin --use-api --yes`.
- **`supabase.ts`** is the one browser client (session persists in localStorage; 90-day idle sign-out; `callFunction` uses plain fetch because the CORS allow-list has no `x-client-info`).
- **`sync.ts`** sits under `store.ts` (`save()` calls a hook; `store.ts` stays the only code touching localStorage, incl. `kv` for device id/token/revs). Pure decisions (`decideHydrate`, `decidePush`, ...) are tested in `sync.test.ts`. Push is debounced 2 s with the base rev; a conflict shows a banner (use the newer one, or force-push with `p_force`); `denied` stops syncing quietly.
- **Login gate** is in `Base.astro`: game pages (`/`, `/train`, `/quiz`, `/paper`, `/collection`) redirect to `/login` without a session; `/parent` needs an admin at aal2 or a parent (else `/grownups/`); the Library stays public. Header "Log out" ends this browser's session only.
- Test tools (`testtools.ts`) edit only the Test Player's save through `push_save`; the database refuses an admin write to anyone else.

### Cookie data

- `site/src/data/cookies.json` (committed) comes from `build_cookie_data.py`. Edit the generator, not the JSON.
- Each rarity needs a `--r-<rarity>` colour in `global.css`.
- `site/public/cookies/` is the committed image copy; `downloads/` is the gitignored raw scrape.
