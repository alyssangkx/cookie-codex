# PSLE English MCQ question patterns from school papers

Generated 2026-11-17 from `scripts/quiz/english/patterns.json`. Source of truth for the data is that JSON; this page summarises it. Phase E1 of the English school.

## Summary

- 188 free P5/P6 English papers from sgtestpaper.com were downloaded and analysed (106 P6, 82 P5; 23 schools; years 2022 to 2025). P6 prelims: 58. Other exams are WA1/WA2/WA3, SA1/SA2, EOY and similar. 255 P5/P6 English pages were listed. 31 were composition-only (Compo) pages and were skipped as they hold no MCQ. Of 224 PDF requests, 36 returned 404 (30 of them 2022 P5, which the source does not host at the guessed address; 6 others), leaving the papers analysed here.
- 187 of 188 PDFs were scans (under 300 characters per page) and were read by OCR (tesseract `eng`); 1 had a usable text layer. So OCR success was 100% in the sense that every paper produced text, but quality is moderate (see limits below).
- 175 of 188 papers contained at least one recognisable MCQ section. The rest are WA papers that hold only open-ended items, or whose OCR lost the section headers.
- The Booklet A running order is very stable across schools and years: **Q1-10 grammar MCQ, Q11-15 vocabulary MCQ, Q16-20 vocabulary-in-context MCQ (closest in meaning to a marked word in a passage), then Q21-25 (P5, and recent P6) or Q21-28 (older P6) visual-text comprehension MCQ.** Booklet B (cloze, editing, synthesis, open-ended comprehension) is not multiple choice.
- Synthesis is not MCQ and is excluded. Listening MCQ (Paper 3) is not in the papers' PDFs and is out of scope.
- Frequencies are numbers of distinct papers with at least one item of that type. They come from automated parsing of OCR text, with the grammar-point classifier checked by reading about 60 sampled items. The error rate is not measured (unverified).

## Question types

| Id | Type | Section | Level | Papers (P6 / P5) | Schools | Items per paper (median, range) | Skill |
|---|---|---|---|---|---|---|---|
| `eng-pat-vocab-word` | Vocabulary MCQ: single-word choice | Paper 2 Booklet A, Q11-15 | intermediate | 152 (90 / 62) | 23 | 4 (2-32) | Choose the word with the right meaning, strength and collocation. |
| `eng-pat-grammar-mcq` | Grammar MCQ (one blank in a sentence, four options) | Paper 2 Booklet A, Q1-10 | intermediate | 131 (83 / 48) | 21 | 10 (5-18) | Choose the grammatically correct form in context. |
| `eng-pat-visual-mcq` | Visual-text comprehension MCQ (poster, brochure or notice, often paired with a second text) | Paper 2 Booklet A, Q21-25 (P6: often Q21-28) | competent | 126 (82 / 44) | 23 | 8 (5-18) | Read and interpret multimodal texts at literal, inferential and evaluative levels. |
| `eng-pat-vocab-passage-mcq` | Vocabulary-in-context MCQ (closest in meaning to a marked word in a passage) | Paper 2 Booklet A, Q16-20 | competent | 117 (78 / 39) | 23 | 5 (5-13) | Infer word meaning from context; recognise synonyms. |
| `eng-pat-vocab-phrasal` | Vocabulary MCQ: phrasal verb choice | Paper 2 Booklet A, Q11-15 | intermediate | 90 (60 / 30) | 20 | 1 (1-4) | Choose the phrasal verb whose particle gives the intended meaning. |
| `eng-pat-vocab-idiom` | Vocabulary MCQ: idiom or fixed-expression choice | Paper 2 Booklet A, Q11-15 | competent | 48 (24 / 24) | 15 | 1 (1-10) | Choose the idiom that matches the situation. |
| `eng-pat-reading-mcq` | Passage comprehension MCQ (non-visual text in Booklet A) | Paper 2 Booklet A, late items | competent | 11 (9 / 2) | 8 | 8 (8-20) | Show literal and inferential understanding of a written text. |
| `eng-pat-cloze-mcq` | Cloze MCQ (numbered blanks in a passage, four options each) | Paper 2 Booklet A or WA papers | intermediate | 5 (2 / 3) | 5 | 5 (4-5) | Use cohesion and sentence-level grammar across a passage. |

Item counts per paper come from the printed question ranges ("For each question from 11 to 15 ..."), so they hold even where OCR lost an item. Items per paper above the usual range (for example 10 idioms) are parser artefacts where a section mixed sub-types.

## Syllabus mapping and distractor traps

### Vocabulary MCQ: single-word choice

- Id `eng-pat-vocab-word`; syllabus outcomes: `eng-vocab-use-appropriate-1`, `eng-vocab-rich-words-1`
- Structure: A sentence with one blank; four single words of similar meaning or the same word class (verbs, adjectives, adverbs, nouns). Only one fits the collocation and nuance.
- Traps: `near-synonym` (all four words mean roughly the same but differ in strength or tone); `wrong-collocation` (the word cannot go with the noun or verb in the sentence); `wrong-register` (the word is too formal or too casual for the context); `sound-alike` (options share a root or look alike but mean different things)

### Grammar MCQ (one blank in a sentence, four options)

- Id `eng-pat-grammar-mcq`; syllabus outcomes: `eng-gram-wps-items-1`, `eng-gram-wps-items-2`, `eng-gram-wps-items-3`, `eng-gram-wps-items-4`, `eng-gram-wps-items-5`, `eng-gram-wps-items-6`, `eng-gram-wps-apply-1`, `eng-gram-wps-apply-2`
- Structure: A single sentence with one blank; four short options, usually single words or two-word verb groups that differ by one grammar feature. Tested only through the choice of form.
- Traps: `same-word-wrong-form` (options are inflections of one word (tense, -ing, -ed, agreement)); `same-class-neighbour` (options are words from one class (all prepositions, all wh-words, all conjunctions) and only one fits the clause); `nearest-noun-agreement` (a plural or singular word right before the blank pulls the verb the wrong way); `meaning-fits-grammar-does-not` (an option makes sense but breaks the structure, for example the wrong tense after a time marker)

### Visual-text comprehension MCQ (poster, brochure or notice, often paired with a second text)

- Id `eng-pat-visual-mcq`; syllabus outcomes: `eng-read-close-visual-1`, `eng-vocab-use-appropriate-4`, `eng-read-close-lit-2`, `eng-read-crit-eval-2`
- Structure: A poster, advertisement, brochure or schedule (sometimes with a short article or email as Text 2), then 5 to 8 questions on literal facts, the purpose of a feature (picture, quote, layout) and comparing the two texts.
- Traps: `detail-from-wrong-part` (the option is true of another part of the text, not the one asked about); `over-generalisation` (the option says all or only where the text says some); `purpose-vs-content` (the option states what the feature shows rather than why it is there); `text-mix-up` (the option is true of Text 1 when Text 2 was asked about)

### Vocabulary-in-context MCQ (closest in meaning to a marked word in a passage)

- Id `eng-pat-vocab-passage-mcq`; syllabus outcomes: `eng-vocab-rich-words-2`, `eng-vocab-rich-words-1`, `eng-gram-text-cohesion-1`
- Structure: A short passage with five marked words or phrases, numbered. For each, choose the option closest in meaning to the marked item as used in the passage.
- Traps: `other-sense` (the option is a real meaning of the word, but not the one used in this passage); `unrelated-sound-alike` (the option looks like the word but means something else); `wrong-word-class` (the option does not fit the grammar of the sentence)

### Vocabulary MCQ: phrasal verb choice

- Id `eng-pat-vocab-phrasal`; syllabus outcomes: `eng-vocab-use-appropriate-2`, `eng-vocab-rich-words-1`
- Structure: A sentence with one blank; four phrasal verbs sharing a verb (or a particle) and differing in the other part.
- Traps: `same-verb-wrong-particle` (options share the verb; only one particle gives the intended sense); `literal-vs-figurative` (an option is right for the literal meaning but not the figurative one)

### Vocabulary MCQ: idiom or fixed-expression choice

- Id `eng-pat-vocab-idiom`; syllabus outcomes: `eng-vocab-use-appropriate-2`
- Structure: A sentence or short dialogue with one blank; four idioms or multi-word expressions. The context implies the intended meaning.
- Traps: `similar-image` (all four idioms use a similar image (body parts, animals, money) but mean different things); `opposite-meaning` (one option means the opposite of what the situation needs); `literal-reading` (an option sounds plausible if read literally)

### Passage comprehension MCQ (non-visual text in Booklet A)

- Id `eng-pat-reading-mcq`; syllabus outcomes: `eng-read-close-lit-1`, `eng-read-close-lit-2`, `eng-read-crit-eval-1`
- Structure: A continuous text (article, story or email) followed by multiple-choice questions on facts, inference and the writer's purpose. Seen mainly in older papers or some schools.
- Traps: `true-but-not-asked` (the option is true in the text but does not answer the question); `extreme-wording` (the option goes further than the text)

### Cloze MCQ (numbered blanks in a passage, four options each)

- Id `eng-pat-cloze-mcq`; syllabus outcomes: `eng-gram-text-cohesion-1`, `eng-gram-wps-items-1`, `eng-gram-wps-items-4`
- Structure: A passage with numbered blanks; each blank has four options. Rare compared with the one-sentence formats.
- Traps: `whole-passage-clue` (the answer depends on a clue in another sentence); `same-class-neighbour` (options are of one word class)

## Grammar points tested in the grammar MCQ

Tally over 1111 grammar items that the parser read from the OCR text; 939 were assigned a point and 172 were left unclassified (OCR damage, or a point the classifier does not model, for example articles or adjective forms). Shares are of the classified items. Because OCR drops some options, the counts are a sample, not the full item count. Papers = distinct papers with at least one item of that point.

| Rank | Grammar point | Items | Share | Papers (P6 / P5) | Schools | Syllabus outcome |
|---|---|---|---|---|---|---|
| 1 | tenses and auxiliaries | 157 | 16.7% | 100 (66 / 34) | 19 | `eng-gram-wps-items-1` |
| 2 | prepositions | 118 | 12.6% | 97 (61 / 36) | 21 | `eng-gram-wps-items-3` |
| 3 | verb forms (gerund / participle / infinitive) | 108 | 11.5% | 77 (53 / 24) | 21 | `eng-gram-wps-items-1` |
| 4 | subject-verb agreement | 94 | 10.0% | 83 (47 / 36) | 18 | `eng-gram-wps-items-2` |
| 5 | quantifiers and determiners | 93 | 9.9% | 89 (59 / 30) | 18 | `eng-gram-wps-apply-2` |
| 6 | question tags | 88 | 9.4% | 85 (58 / 27) | 19 | `eng-gram-wps-items-6` |
| 7 | conjunctions and connectors | 86 | 9.2% | 84 (52 / 32) | 18 | `eng-gram-wps-items-4` |
| 8 | relative pronouns / wh-words | 64 | 6.8% | 64 (38 / 26) | 17 | `eng-gram-wps-items-5` |
| 9 | pronouns (incl. reflexive) | 46 | 4.9% | 43 (27 / 16) | 15 | `eng-gram-wps-items-5` |
| 10 | modals | 35 | 3.7% | 35 (19 / 16) | 13 | `eng-gram-wps-items-1` |
| 11 | conditionals | 33 | 3.5% | 31 (23 / 8) | 12 | `eng-gram-wps-apply-3` |
| 12 | reported speech | 7 | 0.7% | 7 (3 / 4) | 4 | `eng-gram-wps-items-1` |
| 13 | passive voice | 7 | 0.7% | 7 (7 / 0) | 6 | `eng-gram-wps-items-1` |
| 14 | inversion | 3 | 0.3% | 3 (2 / 1) | 2 | `eng-gram-wps-apply-3` |

Reading the table: tense and verb-form items (tenses and auxiliaries, verb forms, subject-verb agreement) together are the largest block. Prepositions, quantifiers/determiners, question tags and conjunctions each appear in more than half of the papers. Reported speech, passive voice and inversion are rare as one-blank MCQ in these papers; they are mostly tested in Booklet B synthesis, which is not MCQ. Grouped as the syllabus names them: `eng-gram-wps-items-1` (tenses and verb forms) is the biggest, then `-3` prepositions, `-2` agreement, `-4` conjunctions, `-5` pronouns, `-6` question tags.

## Other sections seen (not MCQ)

Papers in which the section appears (by keyword in the OCR text; indicative only):

| Section | Papers |
|---|---|
| grammar cloze (free fill-in) | 156 |
| synthesis and transformation (rewrite) | 141 |
| grammar cloze (word box) | 120 |
| writing (Paper 1) | 75 |
| comprehension cloze | 55 |
| editing for spelling and grammar | 43 |

## OCR and method limits

- Text came from `tesseract eng` at 200 dpi, page-segmentation mode 4. Option numbers like "(1)" are sometimes read as "41." or "{o)", and underlined words are not marked, so the vocabulary-in-context items lose their target word.
- Parsed items per section are typically 70-100% of the printed range. Type frequencies use the printed ranges; grammar-point tallies use only parsed items.
- The grammar-point classifier is rule based (option shape plus stem cues). Items with garbled options fall into "unclassified". Verb-form and tense items overlap, and some modal, conditional and reported-speech items may be filed under tenses.
- Visual-text and passage comprehension are told apart by header keywords (poster, brochure, Text 1 and so on), so a few passage MCQ sets may be filed as visual-text.
- Answer keys are not in the papers, so no answer-position or correct-option statistics were taken.
- Paper text stays in the temp folder outside the repo. This page and the JSON hold type names, counts and paraphrased descriptions only.

## Papers analysed

| School | P5 papers | P6 papers |
|---|---|---|
| ACS (Junior) | 7 | 8 |
| ACS (Primary) | 2 | 2 |
| Ai Tong | 3 | 2 |
| Catholic High | 3 | 6 |
| Henry Park | 8 | 5 |
| MGS | 0 | 6 |
| Maha Bodhi | 8 | 1 |
| Maris Stella | 3 | 3 |
| Nan Chiau | 0 | 1 |
| Nan Hua | 6 | 11 |
| Nanyang | 8 | 12 |
| PLMGS | 2 | 2 |
| Pei Chun | 0 | 2 |
| Pei Hwa | 0 | 1 |
| Raffles | 6 | 8 |
| Red Swastika | 9 | 7 |
| Rosyth | 5 | 10 |
| Rulang | 2 | 0 |
| SCGS | 0 | 4 |
| St Hilda | 3 | 0 |
| St Nicholas Girls' | 2 | 7 |
| Tao Nan | 5 | 7 |
| Temasek | 0 | 1 |
