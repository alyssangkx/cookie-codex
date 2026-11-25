# Mock paper mode: design (draft, 25 Nov 2026)

Status: **draft for the owner**. Nothing here is built. Source: Phase 1 report, section 4, with the owner's accepted
defaults. Decision record: [ADR 0013](adr/0013-mock-papers.md). Blueprints:
`site/src/data/mockpaper/english.json` and `chinese.json` (data only; nothing imports them yet).

## What it is

A "Mock paper" button beside the WA/SA paper builder, for English and Chinese. It sets a paper shaped like Paper 2 of
the PSLE: sections in paper order, each with a printed title and instruction, marks per question, one clock for the
whole paper. It reuses the paper runner (submit-then-review, one 10-minute pause, wall-clock deadline, draft in kv).

Accepted defaults (owner):
1. Start without Editing and the open-ended sections; the score is out of the marks covered (English 60 of 90, Chinese
   58 of 90). A section is added by flipping `available` when it can be marked.
2. Past-paper questions only.
3. A mock paper does not count toward the daily past-paper allowance.
4. An AL band is shown, labelled an estimate while sections are missing.
5. A mock paper counts toward the Legendary card as a paper does today.

## Section tables (from the blueprints)

| English Paper 2 (110 min) | Questions | Marks | Available |
|---|---|---|---|
| Grammar | 10 | 10 | yes |
| Vocabulary | 5 | 5 | yes |
| Vocabulary Cloze (1 set) | 5 | 5 | yes, thin supply (11 sets) |
| Visual Text (1 set) | 5 | 5 | yes |
| Grammar Cloze (1 set) | 10 | 10 | yes |
| Editing | 10 | 10 | no, nothing in the bank |
| Comprehension Cloze (1 set) | 15 | 15 | yes |
| Synthesis and Transformation | 5 | 10 | yes (typed) |
| Comprehension OE | 10 | 20 | no, needs a marker |

| Chinese Paper 2 (100 min) | Questions | Marks | Available |
|---|---|---|---|
| 语文应用 | 15 | 30 | yes |
| 短文填空 (1 set) | 5 | 10 | yes |
| 阅读理解一 (1 passage) | 5 | 10 | yes |
| 完成对话 (1 set, 8 options) | 4 | 8 | yes |
| 阅读理解二 | 11 | 32 | no, needs a marker |

## Build steps

### Step 1: blueprint and marks
- Files: `site/src/data/mockpaper/{english,chinese}.json` (written), new `site/src/lib/mock.ts` (types, `loadBlueprint`,
  `coveredMarks`), `mock.test.ts`.
- Rules: the blueprint is the only place the numbers live. `coveredMarks` = sum of `questions x marksPerQuestion` over
  `available` sections (60 and 58). A test fails if the sums of all sections differ from `totalMarks` (90) or if an
  `available` section lists a sub-topic missing from the syllabus JSON.
- Clock: `minutes` from the blueprint, but the deadline is scaled by covered marks (English 110 x 60/90, about 73
  minutes) so a shorter paper is not easier on time. Open question for the owner: scale, or keep the full time.

### Step 2: section headers and passage sets (`pick.ts`, `quiz/index.astro`)
- New `pickMock(blueprint, pools, seen, now, rand)` in `pick.ts`, returning `{ sectionId, ids[] }[]`.
- Drawing: per section, choose sub-topic by round-robin over `subTopics` (Chinese 语文应用), then:
  - single-question sections: unseen first, then due retests, then anything else (as `pickPaper`);
  - set sections (`wholeSets`): draw whole sets using `wholePassages`/`pickPassage` logic: one set whose blank count
    best matches `blanksPerSet`, unseen set first. Never cut a set. If no set has the exact count, take the closest
    and the section's marks follow the blanks actually drawn (stored in the draft).
- Mixing: schools and years are mixed freely; no single past paper is complete in the data. Prefer different source
  papers across sections (the item's source id is known to `pp_serve`); this is a preference, not a rule.
- Unseen first, then due retests (so a mock paper also clears retests), then seen.
- The quiz page draws a section header (title, instruction line, marks) before the first question of each section.
- Draft v2 (see Data shapes). Hold-back: the paper runner's `paperOk` filter (4 options, not in a set) does not apply to
  a mock paper; a separate `mockOk` allows sets and typed items.

### Step 3: typed and cloze screens inside a paper
- `quiz/index.astro`: today `isWhole` is `!PAPER && ...`, so the whole-passage cloze screen is off in paper mode. Lift
  the `!PAPER` guard for mock mode: a cloze section renders as one screen (all blanks, one submit button per the
  section), Synthesis as typed lines.
- Submit-then-review stays: no feedback during the paper. A cloze or typed section is checked by the same function as
  in a tier quiz, only after the final submit.
- Navigation: a section list lets the child jump between sections; a cloze counts answered when any blank is filled.

### Step 4: Chinese
- Enable the subject in `/paper/`; the Chinese section titles and instructions come from the blueprint (Chinese text).
- 完成对话 uses the 8-option screen; the "grey out a used phrase" hint is dropped in a paper (it is feedback).
- 短文填空 is a whole-passage cloze (MCQ blanks). The Chinese result line uses the existing bilingual rule.

### Step 5: batched fetching (client, plus one migration)
- A paper has up to 75 questions (English) or 29 (Chinese). `pp_serve` takes at most 15 ids per call, 40 calls an hour.
  The client fetches the pool for the sections, picks, then fetches content in batches of 15 in section order, with
  section 1 first so the child can start; later batches load while the first section is done. A failed batch retries
  once and then shows a "Try again" in that section without losing answers.
- Allowance exemption (needs a migration, described not written). In `pp_serve`, add a parameter
  `p_mock boolean default false`. When true, ids are still logged in `private.pp_served` (for the heavy-use report),
  but the account and family daily counts (125/250/2000 and 400) used for the limit check ignore rows served in mock
  mode: add a column `mock boolean not null default false` to `private.pp_served` and count only `mock = false` rows. The
  hourly call cap (40; 400 for trusted) stays, since 75 questions need only 5 calls. A separate ceiling guards abuse:
  at most 3 mock papers a day per account (counted by distinct paper id passed as `p_paper`), so the exemption cannot
  be used to scrape. Anything else in 010/016 is unchanged; `sqltest.sh` gets a test for each rule.
- Reason for a ceiling: ADR 0012 limits exist to stop copying the pool; an exempt paper still serves only what the child
  is shown, but unlimited exempt papers would defeat the limit.

### Step 6: per-section results
- Result screen: score by section (marks gained of marks available), total out of covered marks, estimated AL band,
  and the usual step-through of wrong and blank answers, grouped by section.
- AL band: `alBand` of the percentage over covered marks, shown as "AL n (estimate: Editing and open-ended sections
  not included)" while any section is unavailable. No label once all sections are available.
- Crumbs: `quizCrumbs(..., 'paper')` scales by questions/10 capped at x3; a mock paper uses the same rule (a mock paper
  is always x3). Legendary: counts as a paper if 20+ questions and 85%+ on covered marks; the 3-topics rule is met by
  sections (each section is a topic for English and Chinese). One a week as today.
- Retests: every wrong, blank or ran-out answer becomes a 1/3/7 day retest through `answer(..., retireNew = false,
  picked)`, with `LEFT_BLANK` and `''` as in a paper. Papers never retire questions or clear tiers (pass `{}`).

## Data shapes

Draft v2 (kv `paper-draft`, version field `v: 2`; v1 drafts still load):
```
{ v: 2, kind: 'mock', owner, ts, rev, subject: 'english' | 'chinese', blueprintVersion: string,
  clock, mins,
  sections: [{ id, title, ids: string[], marksEach: number, marks: number, groups?: string[] }],
  ids: string[],            // all ids in paper order (kept so v1 code paths work)
  picks: Pick[], at, topics: string[], mix: 'mock' }
```
`draftOk` accepts v 1 or 2; an older tab seeing v 2 ignores it (no schema bump of the save). `blueprintVersion` stops a
draft from using a blueprint that changed (marks are copied into the draft, so a later edit never changes a live paper).

Section result (in the finished attempt and the result screen):
```
{ id, title, marks, gained, answered, blank, wrong: string[] }
```
Attempt record gains optional `mock: { subject, covered, gained, estimated: boolean, sections: SectionResult[] }`.
Optional field, so no schema bump; `cleanSave` keeps it.

## Rules summary
- Whole sets only; never cut a passage. Mix schools and years; unseen first, then due retests, then seen.
- Score = marks gained / marks covered; the unavailable sections add nothing and the page says so.
- Not a daily past-paper allowance cost (migration), but still counts as a started paper for the daily tries and the
  120-minute day: it ends the day at the cap like any paper. Open question: a 110-minute paper under a 120-minute
  daily cap leaves little else; the owner may want mock papers outside the cap.
- Retests booked as 1/3/7 days, exactly as for papers.

## Risks
- Thin Vocabulary Cloze (11 sets): repeats; a child may see a set twice in a few mocks.
- Set sizes may not match the blueprint (blank counts unverified); the marks then follow the drawn set.
- Paper length: 75 items in one draft in kv (size, a few hundred KB of ids and picks only; text is not stored).
- 15-id content batches: a slow network stalls a section; need good retry and loading states.
- Typed marking of Synthesis is all or nothing and may be harsh; partial marks need a decision.
- The estimated AL may mislead if read as a prediction; the label must stay next to the number.
- Enabling the `!PAPER` cloze screen could change WA/SA behaviour if the guard is shared: keep a `MOCK` flag separate.
- Migration touches `pp_serve`, the anti-scraping gate: needs review by the database reviewer and the owner's approval.

## Tests
- `mock.test.ts`: blueprint sums (60 and 58 covered, 90 total); all sub-topic ids exist in the syllabus JSON.
- `pickMock`: never cuts a set; unseen before seen; due retests before seen; no duplicate id; section order; a short
  pool yields a shorter section and correct marks; Chinese 语文应用 spread over the seven sub-topics.
- Draft: v1 loads, v2 loads, bad shape rejected; stale second tab cannot write; blueprint change does not alter a live draft.
- Scoring: gained/covered, estimate flag when sections are missing, AL band cut-offs at 90/85 boundaries.
- Retests: wrong, blank and ran-out answers book 1/3/7 days; no tier clears; no question retires.
- Crumbs and Legendary: mock x3, 85% on covered marks, once a week.
- `scripts/accounts/sqltest.sh`: mock serving ignores the daily counts, still logs, respects the hourly cap and the
  3-papers-a-day ceiling; a non-mock call is unchanged.
- Screenshots: each section type in a paper (MCQ, set, cloze, typed, dialogue), result screen, resume after reload.
