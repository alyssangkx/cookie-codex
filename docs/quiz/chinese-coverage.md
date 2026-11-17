# Chinese bank: PSLE syllabus and top-school coverage

816 shipped questions (basic 263, intermediate 301, competent 252). Regenerate with `python3 scripts/quiz/chinese/coverage.py`.

## 1. PSLE syllabus (SEAB 0005 / 小学华文课程标准)

| Sub-topic | Outcome | MCQ-testable | Shipped |
|---|---|---|---|
| 字音辨认 (character sound) | 根据句子的意思，选出字词的正确汉语拼音 (choose the correct pinyin for a character or wor… | yes | 77 |
| 字音辨认 (character sound) | 辨别多音字在语境中的读音 (identify the reading of a polyphonic character in conte… | yes | 34 |
| 字形辨认 (character form) | 根据句意选出正确的字 (choose the correct character for the sentence meaning) | yes | 5 |
| 字形辨认 (character form) | 辨别同音字 (distinguish homophones) | yes | 36 |
| 字形辨认 (character form) | 辨别形近字 (distinguish look-alike characters) | yes | 71 |
| 词语选用 (word choice) | 根据句子的意思选出最适当的词语 (choose the most suitable word for the sentence meani… | yes | 80 |
| 词语选用 (word choice) | 选出最适当的短语 (choose the most suitable phrase) | yes | 18 |
| 词语选用 (word choice) | 辨别词语搭配 (identify correct word collocations) | yes | 18 |
| 词语选用 (word choice) | 辨别近义词的细微差别 (tell near-synonyms apart) | yes | 35 |
| 成语和习用语 (idioms and common expressions) | 在语境中正确运用成语 (use idioms correctly in context) | yes | 55 |
| 成语和习用语 (idioms and common expressions) | 在语境中正确运用习用语 (use common expressions correctly in context) | yes | 57 |
| 句子选用 (sentence choice) | 根据句子的意思选出最适当的句子 (choose the most suitable sentence for the meaning) | yes | 47 |
| 句子选用 (sentence choice) | 辨别句子结构是否完整、通顺 (judge whether sentence structure is complete and well-… | yes | 49 |
| 关联词 (conjunctions) | 选用适当的关联词连接句子 (choose a suitable conjunction pair) | yes | 99 |
| 句子排列 (sentence ordering) | 把句子排列成通顺的语段 (arrange sentences into a coherent paragraph) | yes | 0 **not yet** |
| 多项选择短文填空 (MCQ cloze) | 根据短文内容和上下文，选出最适当的答案 (choose the best answer from passage content and … | yes | 16 |
| 多项选择短文填空 (MCQ cloze) | 理解语境以判断词语的用法 (use context to judge word usage) | yes | 42 |
| 对话填答 (dialogue completion) | 根据对话内容，选出最适当的答案 (choose the best response from the dialogue content) | yes | 0 **not yet** |
| 对话填答 (dialogue completion) | 判断对话中的情境和语气 (judge situation and tone in a dialogue) | yes | 0 **not yet** |
| 篇章理解 (passage understanding) | 根据篇章内容选出最适当的答案 (choose the best answer from passage content) | yes | 61 |
| 篇章理解 (passage understanding) | 理解词句在篇章中的意思 (understand words and sentences in the passage) | yes | 16 |
| 实用文与篇章 (practical text and passage) | 根据实用文和篇章的内容回答问题 (answer questions on a practical text and passage) | no | 0 |
| 实用文与篇章 (practical text and passage) | 书面互动 (written interaction) | no | 0 |
| 听后选答 (listen then choose) | 听对话、通告、广告、说明、介绍、故事后选出最适当的答案 (listen to dialogues, announcements, ads,… | yes | 0 **not yet** |

**18 of 22 MCQ-testable outcomes have questions.** Not yet covered: 句子排列 (sentence ordering); 对话填答 (dialogue completion); 听后选答 (listen then choose). See `docs/content-schedule.md` for when they are planned.

## 2. Top-school question types (171 P5/P6 papers, 21 schools, 2022–2025)

| Type | Papers it appears in | Shipped questions |
|---|---|---|
| 阅读理解一 (passage MCQ) (`chi-pat-yuedu-mcq`) | 139 | 77 |
| 汉语拼音 (pinyin of an underlined word) (`chi-pat-pinyin`) | 124 | 111 |
| 形近字／同音字辨认 (choose the right character) (`chi-pat-zixing`) | 124 | 112 |
| 选词填空：近义词辨析 (near-synonym word choice) (`chi-pat-xuanci`) | 118 | 151 |
| 完成对话 (complete the dialogue) (`chi-pat-wancheng-duihua`) | 117 | 0 **not yet** |
| 句子选用 (choose the clause that completes the sentence) (`chi-pat-juzi-xuanyong`) | 112 | 47 |
| 词语运用：哪个句子正确 (which sentence uses the word correctly) (`chi-pat-ciyu-yunyong`) | 112 | 49 |
| 词语／成语的意思 (meaning of an underlined word or idiom) (`chi-pat-ciyuyi`) | 104 | 55 |
| 关联词 (conjunction pair) (`chi-pat-guanlian`) | 84 | 99 |
| 短文填空：词语选用 (cloze word choice) (`chi-pat-duanwen-tiankong`) | 82 | 58 |
| 成语运用 (idiom used correctly) (`chi-pat-chengyu`) | 39 | 57 |

## 3. Words tested in the papers

Of 454 two-to-four-character words seen at least twice in the papers' MCQ slots (OCR, noisy), **421 (92%)** appear somewhere in the shipped questions. Approximate: a plain substring match can also hit a word inside a longer word. No paper sentences are copied; only which words get tested.
