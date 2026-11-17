# PSLE Chinese (华文) MCQ question patterns from school papers

Generated 2026-11-17 from `scripts/quiz/chinese/patterns.json`. Source of truth for the data is that JSON; this page summarises it.

## Summary

- 171 free P5/P6 Chinese papers from sgtestpaper.com were downloaded and analysed (95 P6, 76 P5; 21 schools; years 2022 to 2025). P6 prelims: 53. Other exams are WA1/WA2/WA3, SA1, EOY and similar.
- All 171 PDFs are scans (no text layer, under 300 characters per page), so everything was read by OCR (tesseract `chi_sim`). OCR quality is moderate: about 73% of the parsed 语文应用 items had all four options readable as clean Chinese. Tone marks in pinyin options and some characters are unreliable. Only 151 papers yielded a parsable 语文应用 section and 82 a parsable cloze.
- Ten question types were found in the three MCQ sections 语文应用, 短文填空 and 完成对话. In the 语文应用 pages sampled by reading (about 12 papers), the running order was consistent: 2 pinyin items, 2 character items, then word-choice, word-meaning, conjunction, sentence-completion and "which sentence is correct" items.
- This confirms that the item types the official SEAB documents do not name (同音字/形近字, 近义词, 关联词, 词语搭配) are all really tested, as MCQ stems. 句子排列, 量词 and 修辞 were **not** seen as MCQ types in the readable text; only one sentence-order item was found (not enough to call a type).
- Frequencies are numbers of distinct papers with at least one item of that type. They come from automated classification of OCR text, checked by reading about 60 sampled items. The error rate is not measured (unverified), and counts are lower bounds where OCR lost items.

## Question types

| Section | Type | Level | Papers (P6 / P5) | Main traps |
|---|---|---|---|---|
| 语文应用 | 汉语拼音 (pinyin of an underlined word) | basic | 124 (76 / 48) | initial-confusion, final-confusion, tone, polyphone |
| 语文应用 | 形近字／同音字辨认 (choose the right character) | intermediate | 124 (77 / 47) | look-alike, homophone, wrong-word |
| 语文应用 | 选词填空：近义词辨析 (near-synonym word choice) | intermediate | 118 (75 / 43) | near-synonym, wrong-collocation, shared-character, wrong-register |
| 语文应用 | 词语／成语的意思 (meaning of an underlined word or idiom) | intermediate | 104 (71 / 33) | half-right, opposite, context-only, similar-word |
| 语文应用 | 关联词 (conjunction pair) | basic | 84 (57 / 27) | wrong-logic, half-pair, similar-relation |
| 语文应用 | 句子选用 (choose the clause that completes the sentence) | intermediate | 112 (71 / 41) | wrong-logic, off-topic, wrong-connector |
| 语文应用 | 词语运用：哪个句子正确 (which sentence uses the word correctly) | competent | 112 (74 / 38) | wrong-collocation, wrong-sense, wrong-word-class, wrong-register |
| 语文应用 / 短文填空 | 成语运用 (idiom used correctly) | competent | 39 (19 / 20) | wrong-situation, wrong-register, wrong-character |
| 短文填空 | 短文填空：词语选用 (cloze word choice) | intermediate | 82 (51 / 31) | near-synonym, adverb-logic, wrong-collocation, whole-passage-clue |
| 完成对话 | 完成对话 (complete the dialogue) | intermediate | 117 (76 / 41) | keyword-overlap, wrong-logic, wrong-person-or-tense |

Parsed items not matched to a type: 98 (mostly OCR-damaged items and comprehension questions that leaked into the parsed section).

## Top types with original examples

All examples are original, written for this project. None is copied from a paper. Answer is the option number.

### 汉语拼音 (pinyin of an underlined word) (124 papers, basic)

- Id: `chi-pat-pinyin`; syllabus topic: `chi-pinyin-sound-1`
- Structure: A sentence with one underlined 2-character word; choose the option giving its correct Hanyu Pinyin (4 romanised options).
- Traps: `initial-confusion` (options differ in the initial: z/zh, c/ch, s/sh, n/l, q/x, g/k); `final-confusion` (options differ in the final: an/ang, in/ing, en/eng, ao/ou); `tone` (same letters with a different tone mark (tone marks are often unreadable in OCR, so the share of pure-tone items is unverified)); `polyphone` (a 多音字 is in the word, so the reading depends on context (seen less often; unverified))
- Example: 他每天坚持跑步，身体越来越强壮。（画线词语：坚持）
  - (1) jiān chí / (2) jiàn chí / (3) jiān shí / (4) jiàn shí
  - Answer (1) jiān chí. “坚”读 jiān（第一声），“持”读 chí（声母是 ch），所以选 jiān chí。

### 形近字／同音字辨认 (choose the right character) (124 papers, intermediate)

- Id: `chi-pat-zixing`; syllabus topic: `chi-zixing-form-3`
- Structure: A sentence with a word missing one character; four single characters are offered and one forms the correct word in context.
- Traps: `look-alike` (options share a component, e.g. 绝/觉/决 or 续/许/须); `homophone` (options sound the same or nearly the same but mean different things); `wrong-word` (a wrong character still looks plausible because it makes a real word elsewhere)
- Caveat: Look-alike and homophone items are not separated: the OCR has no reliable tone marks and no answer keys, so which sub-type each item is was not counted.
- Example: 爸爸工作很勤____，常常加班到深夜。
  - (1) 劳 / (2) 荣 / (3) 营 / (4) 萤
  - Answer (1) 劳. “勤劳”表示努力工作；荣、营、萤的字形和“劳”相近，但不能组成“勤＿”这个词。

### 选词填空：近义词辨析 (near-synonym word choice) (118 papers, intermediate)

- Id: `chi-pat-xuanci`; syllabus topic: `chi-ciyu-choose-4`
- Structure: A sentence with one blank; four 2-character words of similar meaning or sharing a character; choose the one that fits the sentence.
- Traps: `near-synonym` (same general meaning but the wrong nuance or intensity); `wrong-collocation` (the word cannot go with the noun or verb in the sentence); `shared-character` (two or more options share a character, e.g. 促进/训练/提高); `wrong-register` (a positive or negative word (褒贬) that clashes with the situation)
- Example: 这个小镇的空气很____，住在这里对身体很好。
  - (1) 清新 / (2) 清洁 / (3) 清楚 / (4) 清醒
  - Answer (1) 清新. “清新”形容空气新鲜干净；清洁多指没有脏东西，清楚指不模糊，清醒指头脑不糊涂。

### 完成对话 (complete the dialogue) (117 papers, intermediate)

- Id: `chi-pat-wancheng-duihua`; syllabus topic: `chi-dialogue-mcq-1`
- Structure: A dialogue of 7 to 9 lines with 4 numbered blanks and a list of 8 phrases or short sentences; match 4 of them to the blanks by context. Four phrases are not used.
- Traps: `keyword-overlap` (an unused phrase repeats a word from the dialogue but fits no blank); `wrong-logic` (a phrase that continues the topic but answers a different question); `wrong-person-or-tense` (a phrase with the wrong subject, or a time that does not match the line before)
- Caveat: Observed format is a list of 8 phrases with 4 blanks (answers written in the booklet), not a 4-option MCQ; the 117-paper count is papers whose OCR contains the 完成对话 heading. Per-item types were sampled by reading about 6 dialogues, not parsed.
- Example: 小美：你怎么了，看起来很不高兴？ 小文：我的作业本不见了，Q1。
  - (1) 我已经找遍了书包 / (2) 我想把作业本送给你 / (3) 我喜欢吃面包 / (4) 今天天气真好
  - Answer (1) 我已经找遍了书包. 小文在说明难过的原因，接着说明自己做过的事，只有第一项符合语境。

### 句子选用 (choose the clause that completes the sentence) (112 papers, intermediate)

- Id: `chi-pat-juzi-xuanyong`; syllabus topic: `chi-juzi-choose-1`
- Structure: A sentence missing its first or last clause; choose the clause that fits the meaning and the connecting word.
- Traps: `wrong-logic` (the clause contradicts the cause, result or turn in the given half); `off-topic` (the clause is grammatical but about another event or person); `wrong-connector` (the option starts with a conjunction that does not match the other half)
- Example: 他没有带伞，____。
  - (1) 结果被雨淋湿了 / (2) 因此心情很愉快 / (3) 可是他带了一把伞 / (4) 所以天气很凉爽
  - Answer (1) 结果被雨淋湿了. 没带伞遇到下雨，自然的结果是被淋湿；其他选项或自相矛盾，或和前半句没有因果关系。

### 词语运用：哪个句子正确 (which sentence uses the word correctly) (112 papers, competent)

- Id: `chi-pat-ciyu-yunyong`; syllabus topic: `chi-juzi-choose-2`
- Structure: The stem asks which sentence is correct; the same target word appears in all four sentences and only one uses it with the right meaning and collocation.
- Traps: `wrong-collocation` (the word is attached to an object or verb it cannot take); `wrong-sense` (a word with several meanings is used in the wrong sense); `wrong-word-class` (a verb used as an adjective or the reverse); `wrong-register` (a positive word used for a negative situation or the reverse)
- Example: 以下哪一个句子是正确的？
  - (1) 请大家保持安静，不要吵闹。 / (2) 他每天保持上学。 / (3) 我们要保持这个好消息告诉妈妈。 / (4) 弟弟的房间保持了新衣服。
  - Answer (1) 请大家保持安静，不要吵闹。. “保持”表示使一种状态继续不变，常搭配“安静、清洁、联系”；其他句子的搭配都不通。

### 词语／成语的意思 (meaning of an underlined word or idiom) (104 papers, intermediate)

- Id: `chi-pat-ciyuyi`; syllabus topic: `chi-ciyu-idiom-1`
- Structure: A sentence with an underlined word or idiom; choose the explanation that matches its meaning in the sentence (4 short explanations).
- Traps: `half-right` (the explanation covers only one part of the word); `opposite` (the explanation says the opposite of the word); `context-only` (the option fits the sentence topic but does not explain the word); `similar-word` (the option explains a different word that looks or sounds similar)
- Caveat: Counts include some items where OCR lost the blank and the item is really a sentence-completion; the underlined word is not visible in OCR, so word vs idiom was not split.
- Example: 弟弟做事总是三心二意，难怪成绩不好。（画线成语：三心二意）
  - (1) 做事不专心，不能一心一意 / (2) 想了很多办法来解决问题 / (3) 做事很有计划，一步一步来 / (4) 不愿意和别人合作
  - Answer (1) 做事不专心，不能一心一意. “三心二意”形容做事不专心，所以选第一项。

The other three types (idiom use, cloze and dialogue) have examples in the JSON.

## Papers analysed (metadata only)

Source URLs are in the JSON. School counts: ACS (Junior) 13, ACS (Primary) 4, Ai Tong 8, Catholic High 10, Henry Park 9, Maha Bodhi 7, Maris Stella 6, Methodist Girls (MGS) 6, Nan Hua 14, Nanyang 16, Paya Lebar Methodist Girls (PLMGS) 5, Pei Chun 1, Pei Hwa 1, Raffles Girls' 14, Red Swastika 13, Rosyth 15, Rulang 2, SCGS 4, St Hilda's 4, St Nicholas Girls 9, Tao Nan 10.

| School | Level | Exam | Year |
|---|---|---|---|
| ACS (Junior) | P5 | EOY | 2025 |
| ACS (Junior) | P5 | WA3 | 2025 |
| ACS (Junior) | P5 | EOY | 2024 |
| ACS (Junior) | P5 | WA1 | 2024 |
| ACS (Junior) | P5 | WA3 | 2024 |
| ACS (Junior) | P6 | Prelim | 2025 |
| ACS (Junior) | P6 | WA1 | 2025 |
| ACS (Junior) | P6 | Prelim | 2024 |
| ACS (Junior) | P6 | WA2 | 2024 |
| ACS (Junior) | P6 | WA2 | 2023 |
| ACS (Junior) | P6 | BA1 | 2022 |
| ACS (Junior) | P6 | Prelim | 2022 |
| ACS (Junior) | P6 | SA1 | 2022 |
| ACS (Primary) | P5 | EOY | 2023 |
| ACS (Primary) | P5 | WA2 | 2023 |
| ACS (Primary) | P6 | Prelim | 2024 |
| ACS (Primary) | P6 | Prelim | 2023 |
| Ai Tong | P5 | EOY | 2025 |
| Ai Tong | P5 | WA1 | 2025 |
| Ai Tong | P5 | WA2 | 2025 |
| Ai Tong | P5 | WA3 | 2025 |
| Ai Tong | P5 | EOY | 2023 |
| Ai Tong | P5 | WA1 | 2023 |
| Ai Tong | P6 | Prelim | 2025 |
| Ai Tong | P6 | Prelim | 2023 |
| Catholic High | P5 | EOY | 2024 |
| Catholic High | P5 | WA2 | 2024 |
| Catholic High | P5 | WA3 | 2024 |
| Catholic High | P6 | Prelim | 2025 |
| Catholic High | P6 | WA1 | 2025 |
| Catholic High | P6 | WA2 | 2025 |
| Catholic High | P6 | Prelim | 2024 |
| Catholic High | P6 | Prelim | 2023 |
| Catholic High | P6 | Prelim | 2022 |
| Catholic High | P6 | SA1 | 2022 |
| Henry Park | P5 | EOY | 2025 |
| Henry Park | P5 | EOY | 2024 |
| Henry Park | P5 | WA1 | 2024 |
| Henry Park | P5 | WA2 | 2024 |
| Henry Park | P5 | WA3 | 2024 |
| Henry Park | P5 | EOY | 2023 |
| Henry Park | P6 | Prelim | 2025 |
| Henry Park | P6 | Prelim | 2024 |
| Henry Park | P6 | Prelim | 2022 |
| Maha Bodhi | P5 | EOY | 2025 |
| Maha Bodhi | P5 | WA2 | 2025 |
| Maha Bodhi | P5 | EOY | 2024 |
| Maha Bodhi | P5 | WA2 | 2024 |
| Maha Bodhi | P5 | EOY | 2023 |
| Maha Bodhi | P5 | WA1 | 2023 |
| Maha Bodhi | P6 | SA1 | 2022 |
| Maris Stella | P5 | EOY | 2023 |
| Maris Stella | P5 | WA1 | 2023 |
| Maris Stella | P6 | Prelim | 2023 |
| Maris Stella | P6 | WA1 | 2023 |
| Maris Stella | P6 | WA2 | 2023 |
| Maris Stella | P6 | CA1 | 2022 |
| Methodist Girls (MGS) | P6 | Prelim | 2025 |
| Methodist Girls (MGS) | P6 | Prelim | 2024 |
| Methodist Girls (MGS) | P6 | WA1 | 2024 |
| Methodist Girls (MGS) | P6 | Prelim | 2023 |
| Methodist Girls (MGS) | P6 | Prelim | 2022 |
| Methodist Girls (MGS) | P6 | SA1 | 2022 |
| Nan Hua | P5 | EOY | 2025 |
| Nan Hua | P5 | WA2 | 2025 |
| Nan Hua | P5 | WA3 | 2025 |
| Nan Hua | P5 | EOY | 2024 |
| Nan Hua | P5 | WA2 | 2024 |
| Nan Hua | P5 | EOY | 2023 |
| Nan Hua | P5 | WA2 | 2023 |
| Nan Hua | P6 | Prelim | 2025 |
| Nan Hua | P6 | Prelim | 2024 |
| Nan Hua | P6 | WA2 | 2024 |
| Nan Hua | P6 | Prelim | 2023 |
| Nan Hua | P6 | WA2 | 2023 |
| Nan Hua | P6 | Prelim | 2022 |
| Nan Hua | P6 | SA1 | 2022 |
| Nanyang | P5 | EOY | 2025 |
| Nanyang | P5 | WA1 | 2025 |
| Nanyang | P5 | WA2 | 2025 |
| Nanyang | P5 | EOY | 2024 |
| Nanyang | P5 | WA1 | 2024 |
| Nanyang | P5 | EOY | 2023 |
| Nanyang | P5 | WA2 | 2023 |
| Nanyang | P6 | Prelim | 2025 |
| Nanyang | P6 | SA1 | 2025 |
| Nanyang | P6 | Prelim | 2024 |
| Nanyang | P6 | SA1 | 2024 |
| Nanyang | P6 | Prelim | 2023 |
| Nanyang | P6 | WA1 | 2023 |
| Nanyang | P6 | WA2 | 2023 |
| Nanyang | P6 | Prelim | 2022 |
| Nanyang | P6 | SA1 | 2022 |
| Paya Lebar Methodist Girls (PLMGS) | P5 | EOY | 2024 |
| Paya Lebar Methodist Girls (PLMGS) | P5 | WA1 | 2024 |
| Paya Lebar Methodist Girls (PLMGS) | P5 | WA2 | 2024 |
| Paya Lebar Methodist Girls (PLMGS) | P6 | Prelim | 2025 |
| Paya Lebar Methodist Girls (PLMGS) | P6 | Prelim | 2022 |
| Pei Chun | P6 | Prelim | 2024 |
| Pei Hwa | P6 | Prelim | 2023 |
| Raffles Girls' | P5 | EOY | 2025 |
| Raffles Girls' | P5 | WA1 | 2025 |
| Raffles Girls' | P5 | WA2 | 2025 |
| Raffles Girls' | P5 | EOY | 2023 |
| Raffles Girls' | P5 | WA1 | 2023 |
| Raffles Girls' | P6 | Prelim | 2025 |
| Raffles Girls' | P6 | WA1 | 2025 |
| Raffles Girls' | P6 | WA2 | 2025 |
| Raffles Girls' | P6 | Prelim | 2024 |
| Raffles Girls' | P6 | WA1 | 2024 |
| Raffles Girls' | P6 | Prelim | 2023 |
| Raffles Girls' | P6 | WA1 | 2023 |
| Raffles Girls' | P6 | Prelim | 2022 |
| Raffles Girls' | P6 | SA1 | 2022 |
| Red Swastika | P5 | EOY | 2025 |
| Red Swastika | P5 | WA1 | 2025 |
| Red Swastika | P5 | EOY | 2024 |
| Red Swastika | P5 | WA1 | 2024 |
| Red Swastika | P5 | WA2 | 2024 |
| Red Swastika | P5 | EOY | 2023 |
| Red Swastika | P5 | WA2 | 2023 |
| Red Swastika | P6 | Prelim | 2025 |
| Red Swastika | P6 | Prelim | 2024 |
| Red Swastika | P6 | WA1 | 2024 |
| Red Swastika | P6 | Prelim | 2023 |
| Red Swastika | P6 | Prelim | 2022 |
| Red Swastika | P6 | SA1 | 2022 |
| Rosyth | P5 | EOY | 2024 |
| Rosyth | P5 | WA2 | 2024 |
| Rosyth | P5 | EOY | 2023 |
| Rosyth | P5 | WA1 | 2023 |
| Rosyth | P5 | WA2 | 2023 |
| Rosyth | P6 | Prelim | 2025 |
| Rosyth | P6 | WA1 | 2025 |
| Rosyth | P6 | WA2 | 2025 |
| Rosyth | P6 | Prelim | 2024 |
| Rosyth | P6 | WA1 | 2024 |
| Rosyth | P6 | WA2 | 2024 |
| Rosyth | P6 | Prelim | 2023 |
| Rosyth | P6 | WA1 | 2023 |
| Rosyth | P6 | WA2 | 2023 |
| Rosyth | P6 | Prelim | 2022 |
| Rulang | P5 | EOY | 2025 |
| Rulang | P5 | WA2 | 2025 |
| SCGS | P6 | Prelim | 2024 |
| SCGS | P6 | Prelim | 2023 |
| SCGS | P6 | WA1 | 2023 |
| SCGS | P6 | Prelim | 2022 |
| St Hilda's | P5 | EOY | 2025 |
| St Hilda's | P5 | WA1 | 2025 |
| St Hilda's | P5 | WA2 | 2025 |
| St Hilda's | P5 | WA3 | 2025 |
| St Nicholas Girls | P5 | EOY | 2024 |
| St Nicholas Girls | P5 | WA2 | 2024 |
| St Nicholas Girls | P6 | Prelim | 2025 |
| St Nicholas Girls | P6 | WA2 | 2025 |
| St Nicholas Girls | P6 | Prelim | 2023 |
| St Nicholas Girls | P6 | WA1 | 2023 |
| St Nicholas Girls | P6 | WA2 | 2023 |
| St Nicholas Girls | P6 | Prelim | 2022 |
| St Nicholas Girls | P6 | SA1 | 2022 |
| Tao Nan | P5 | EOY | 2025 |
| Tao Nan | P5 | EOY | 2024 |
| Tao Nan | P5 | EOY | 2023 |
| Tao Nan | P5 | WA1 | 2023 |
| Tao Nan | P6 | Prelim | 2025 |
| Tao Nan | P6 | Prelim | 2024 |
| Tao Nan | P6 | SA1 | 2024 |
| Tao Nan | P6 | Prelim | 2023 |
| Tao Nan | P6 | Prelim | 2022 |
| Tao Nan | P6 | SA1 | 2022 |

## Science and English availability

Counted from the listing pages on sgtestpaper.com (not downloaded). A count is the number of paper download pages listed, across all schools, per level and year. Listing pages for 2021 returned 404 and the 2026 pages had no entries, so the counts cover 2022 to 2025.

| Subject | Level | 2022 | 2023 | 2024 | 2025 | Total |
|---|---|---|---|---|---|---|
| Science | P5 | 33 | 31 | 33 | 35 | 132 |
| Science | P6 | 27 | 32 | 29 | 29 | 117 |
| English | P5 | 30 | 29 | 33 | 42 | 134 |
| English | P6 | 28 | 28 | 34 | 31 | 121 |
| Chinese | P5 | 30 | 22 | 27 | 30 | 109 |
| Chinese | P6 | 25 | 26 | 22 | 22 | 95 |

Source URL pattern: `https://www.sgtestpaper.com/primary/subject20YY/yYYp{5|6}{science|english|chinese}.html`, for example the 2025 P6 Science list is `https://www.sgtestpaper.com/primary/subject2025/y25p6science.html`. Each entry links to a `download_20YY/` page and a PDF under `test_papers_20YY/primary_{5|6}_{subject}/`. Whether every listed Science and English PDF downloads, and whether it has a text layer, was not tested. The same site also lists Science and English for other levels.
