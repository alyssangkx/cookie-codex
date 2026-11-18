# How top-school English papers test grammar terms (metalanguage)

Source: the 188 OCR'd P5/P6 papers (WA, SA, EOY and Prelim) in the project's English paper set. Method: a word-boundary search for grammar terms (noun, verb, adjective, adverb, pronoun, preposition, conjunction, participle, tense, clause, singular, plural, active/passive voice, comparative, superlative, word class, part of speech), then reading every hit in context. Hits for "subject", "article", "phrase" and "object" were almost all non-grammar uses (a school subject, a newspaper article, "the words or phrases below", a physical object) and were dropped. OCR is noisy, so counts are lower bounds.

## Counts

| Class | What it is | Papers | Questions |
|---|---|---|---|
| (a) Definition | "What is an adverb?" | 0 | 0 |
| (b) Identify a term in a sentence | "The underlined word is a ..." | 1 | 1 |
| (c) Term only in the instruction | "Circle the adjective that ..." | 4 | 4 |
| (d) No term at all | the rest | 183 | n/a |

- (b): one Prelim option reads "The words are used as a proper noun" (a visual-text question about a title in capitals). One other Prelim answer key carries a "Part of speech" column, which labels answers but is not a question.
- (c): four Nan Hua comprehension questions ask the pupil to circle or give an adjective that describes a feeling or tone.
- (d): grammar is tested only through form. About 131 papers have a one-blank grammar MCQ (about 1,100 parsed items; see `english-question-patterns.md`), and the options are inflections, prepositions, conjunctions or agreement choices. The instruction never names the term.
- "Underlined" appears in 148 papers, but only for "closest in meaning to the underlined word" and "spelling or grammatical error". Neither asks for a word class.
- One paper mentions "participles", but as a school-story plot detail, not a question.

## Five examples (paraphrased)

1. (c) "Circle the adjective that best describes Max's feeling." (P6 Prelim, comprehension)
2. (c) "Give an adjective to describe how Bill felt about his situation." (P6 WA1)
3. (b) One option says a capitalised title uses "a proper noun". (P6 WA1, visual text)
4. (d) A one-blank item gives four forms of one verb and asks for the form that fits the time marker.
5. (d) A one-blank item gives four conjunctions and only one fits the meaning of the two clauses.

## Decision

Grammar terms are barely tested: no definition questions, and about 5 questions in 188 papers carry a term, and those only in the instruction. The syllabus outcome `eng-gram-terms-meta-1` remains, so the bank is rewritten to use the terms, never to define them:

- identify the word class or role of a word inside a sentence (noun, verb, adjective, adverb, pronoun, preposition, conjunction, subject, object);
- let the sentence decide for words that can be two classes (home, fast, well, hard, light, early, past, down, before, since);
- choose the form a term names (past participle, comparative, superlative, plural, passive);
- identify tense or voice from a sentence, and the main or subordinate clause;
- choose a conjunction or relative pronoun that fits.

These items also exercise the skills the one-blank grammar MCQ tests (agreement, tense, conjunctions, prepositions). Terms are kept to the P6 level: no future perfect, no present perfect continuous, and "participle" only as "past participle".

Bank: 84 items (`txf-101` to `txf-184`), 28 per level, with the correct answer in each position 7 times per level.
