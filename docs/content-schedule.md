# Content schedule: PSLE 2027

Written 2026-11-17. PSLE written papers are expected around 30 Sep 2027 (confirm against the SEAB circular); school prelims run in August.

## Where each subject stands

| Subject | MCQ share of PSLE marks | Content method | Past papers | Status |
|---|---|---|---|---|
| **Math** | 18 MCQ in Paper 1 (≈26 of 100 marks); the game also drills Paper 2 methods as MCQ | Parametric generators with independent checkers | 209 top-school P5/P6 papers OCR'd; 103 question types | **Done**: 13 topics, 93 tiers, 4,281 questions, 181/181 outcomes |
| **Chinese** | 58 of 200 (语文应用 15 × 2, 短文填空 5 × 2, 阅读理解一 5 × 2, 完成对话 4 × 2) | Curated item bank, blind-answered by a second agent, parent spot-check | 171 papers from 21 schools OCR'd; 10 types (`docs/syllabus/chinese-question-patterns.md`) | **Next** |
| **Science** | 60 of 100 (Booklet A: 30 MCQ × 2) | Mixed: parametric where quantitative (energy, forces, data), curated for concept items; diagrams via the Math figure toolkit | About 250 free P5/P6 papers listed on sgtestpaper.com (not yet downloaded) | Planned |
| **English** | 45 of 200 (Paper 2 Booklet A: 25 MCQ; Listening: 20 MCQ, needs audio) | Curated item bank (grammar, vocabulary, visual text) with blind-answer review | About 255 free P5/P6 papers listed (not yet downloaded) | Planned |

Not in scope for an MCQ game: compositions, oral, open-ended comprehension, Science Booklet B, and English or Chinese listening (it needs recorded audio; reconsider with a text-to-speech pass later).

## Chinese: what the papers test (and what to build first)

| Type (frequency in 171 papers) | Level | Build |
|---|---|---|
| 汉语拼音 (124) | Basic | Phase 1 |
| 形近字 / 同音字 (124) | Intermediate | Phase 1 |
| 近义词选词填空 (118) | Intermediate | Phase 1 |
| 词语 / 成语的意思 (104) | Intermediate | Phase 1 |
| 关联词 (84) | Basic | Phase 1 |
| 词语运用: "which sentence uses the word correctly" (112) | Competent | Phase 1 |
| 句子选用 (112) | Intermediate | Phase 2 |
| 成语运用 (39 or more) | Competent | Phase 2 |
| 短文填空, a cloze passage (82 or more) | Intermediate | Phase 2: original passages |
| 完成对话 (117): 8 phrases for 4 blanks, not a 4-option MCQ | Intermediate | Phase 3: needs a matching-style quiz format |

Counts are approximate: OCR of Chinese scans is imperfect (about 73% of items fully readable), and the papers carry no answer keys.

## Proposed order

| When | Work | Why this order |
|---|---|---|
| **Nov–Dec 2026** | **Chinese Phase 1:** the six 语文应用 vocabulary types above, as a reviewed bank (at least 25 items per sub-topic per level). In parallel: logins (accounts plan Phase B) and deploy to Vercel. | Highest-frequency Chinese items; vocabulary needs daily spaced practice over months, so it should start earliest. Logins must exist before real progress accumulates. |
| **Jan–Feb 2027** | **Science:** download and OCR the papers, catalogue types, build the 19 topics. Diagram questions use the existing figure toolkit. | The largest MCQ share of any paper (60%); P6 Science topics are taught in Term 1, so the bank lines up with school. |
| **Mar–Apr 2027** | **English Booklet A:** grammar MCQ, vocabulary MCQ and visual-text MCQ from catalogued types. | Grammar items are not named in the syllabus, so the paper catalogue defines them. Fits after Science without overlapping the March holidays crunch. |
| **May 2027** | **Chinese Phase 2:** 句子选用, 成语运用, and 短文填空 with original passages. | Builds on the Phase 1 vocabulary. |
| **Jun 2027 (mid-year holidays)** | Monsters and boss quizzes (design section 5); mixed-subject practice papers; second-pass Science fill-ins. | Holidays give time for longer sessions and the game layer. |
| **Jul–Aug 2027** | **Chinese Phase 3** (完成对话 matching format); prelim-style full MCQ papers per subject; weak-spot drills driven by mistake tags. **Content freeze on 15 Aug.** | Prelims are in August; after them, only revision. |
| **Sep 2027** | Revision only: Daily Review, practice papers, no new content. | Stability before PSLE. |

## Risks

- **Language accuracy:** Chinese and English items are written by a model. Every item is blind-answered by a second agent, and a parent spot-checks 30 random items per batch before release.
- **Copyright:** papers are used only to learn types and difficulty; no paper text enters the repo.
- **OCR limits:** Chinese tone marks OCR poorly, so 汉语拼音 items are written from dictionary pinyin, never from OCR text.
