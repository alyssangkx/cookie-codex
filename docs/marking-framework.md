# Marking framework for open-ended answers

Status: recommendation (20 Nov 2026). Follows [learning-loop-design.md](learning-loop-design.md) item 1. This covers how
an LLM on the home server marks typed or photographed answers. Science comes first, then Math Paper 2, then English
and Chinese open-ended answers.

## What the public sources say

| Source | Point |
|---|---|
| [PSLE chief marker interview (republished copy)](https://bureautabletpcphilly.pages.dev/292285.html) | The scheme rewards the concept more than exact keywords. It is drafted by the chief setter, checked against real scripts, and updated. |
| MOE school briefings ([Meridian 2023](https://www.meridianpri.moe.edu.sg/files/Communications/CFD%202023/Science/2023/2023%20CFD%20P5P6%20SC%20Sharing.pdf), [Shuqun 2025](https://shuqunpri.moe.edu.sg/files/PSLE_Briefing_2025_Science.pdf)) | Answers follow **Claim, Evidence, Reasoning**, but not every question needs all three. General statements score nothing: link the answer to the set-up in the question. Typical demands are describe an observation, infer or conclude, state a choice, cite data, and give a reason. |
| Tuition guides (for example [Geniebook](https://geniebook.com/exam-preparation/psle/article/psle-science-mastering-question-types-and-answering-techniques)) | They claim exact keywords such as "expands" are required. This is **unverified** against SEAB material, so the marker treats scientific terms as concepts (see below). |
| [SEAB PSLE Mathematics syllabus (0038, 2025)](https://www.seab.gov.sg/files/PSLE%20Syllabus%20documents/2025%20PSLE/0038_y25_sy.pdf) | On a 2-mark question, a correct answer gets full marks. A wrong answer still gets 1 mark for a correct method shown. |
| School briefings ([Henry Park P6 Math](https://www.henryparkpri.moe.edu.sg/files/2a__Standard_Mathematics_P6_25.pdf)) | Structured questions (3 to 5 marks) give marks for the essential steps. Any mathematically logical alternative method still earns them. Never erase working. |
| Research on LLM grading of handwritten work ([Levine et al. 2026](https://arxiv.org/abs/2605.19043), [AI grading of college calculus 2026](https://arxiv.org/pdf/2603.00895), [GPT-4 on handwritten exams](https://arxiv.org/html/2411.05231v2), [VEHME, EMNLP 2025](https://aclanthology.org/anthology-files/pdf/emnlp/2025.emnlp-main.1619.pdf), [CHECK-MAT 2025](https://preview.aclanthology.org/ingest-emnlp/2025.mathnlp-main.6.pdf)) | Marking item by item against a rubric works well. **Most errors come from reading the handwriting, not from applying the rubric.** Models sometimes misread a vague rubric. Real deployments keep a person in the loop. |

## Science: a rubric per question

Every open-ended question has a private rubric, stored with the question in Supabase (never in the repo). Each mark is
one **mark point**:

```json
{ "marks": 2, "kind": "cause-effect",
  "points": [
    { "id": "p1", "role": "fact|process|claim|evidence|reasoning",
      "idea": "the air in the flask gains heat from the hot water",
      "accept": ["air is heated by the water", "heat flows from the water to the air"],
      "reject": ["the air gets hot by itself", "cold leaves the air"],
      "context": true },
    { "id": "p2", "role": "process", "after": "p1",
      "idea": "the air expands and pushes the cork out", "accept": ["..."], "reject": ["..."], "context": true } ] }
```

- **One idea per point.** `accept` lists equivalent phrasings, so concepts count over exact keywords. `reject` lists the
  usual misconceptions ("cold flows", "gets bigger" when the scheme wants a particle or heat idea).
- **`context: true`** means the point must name this set-up (the flask, plant X, magnet A). A general textbook sentence
  scores nothing, as the school briefings warn.
- **Processes are chains.** Each link is a point, and `after` sets the order: heat gain, then evaporation, then water
  vapour, then contact with a cooler surface, then heat loss, then condensation. A link that is missing or in the
  wrong order loses that mark only.
- **Question kinds get templates:**
  - cause-effect;
  - process chain;
  - fair test (variable changed, variables kept the same, what is measured);
  - reliability (repeat the experiment and average);
  - conclusion from data (compare using the data, with units);
  - predict and explain;
  - classify and justify.

  The template proposes the points; a person approves them.
- **Where rubrics come from:**
  1. The answer keys give a model answer, often a short one.
  2. The LLM drafts the points, `accept` and `reject` from the question and that model answer.
  3. A reviewer approves a sample per question kind, and every rubric used in a diagnostic.

**Marker output, one JSON per answer:**
- for each point: awarded yes or no, plus **the exact span of the child's answer that earns it** (no span means no
  mark, which keeps the marker grounded);
- the total;
- the missing point, said in child-friendly words;
- a corrected answer in the child's own wording where possible;
- a confidence. When unsure, it says "ask a grown-up to check" rather than guessing.

**Calibration:** the owner blind-marks 100 answers per subject (decision 8). The target is at least 90% agreement per
point, and the exact total on at least 85% of answers. Disagreements become new `accept` or `reject` lines.

## Math Paper 2: method marks

Rubric per question, in the SEAB style:

- **2-mark questions:** `A2` for the correct answer, otherwise `M1` for a correct method.
- **3 to 5 marks:**
  - one `M` per essential step, with its key intermediate value (for example "1 unit = 24", "total before = 360");
  - one `A1` for the final answer with its unit;
  - other logical methods allowed (any route that reaches the intermediate values).

  Follow-through is off unless a question allows it.
- **Model drawings:** describe them as units ("boy 3u, girl 5u, difference 2u = 48"). An answer that states the unit
  relation earns the method mark the drawing would.

**How the child's working gets to the marker**, in two stages:

1. **v1, typed:** a final-answer box, marked automatically, plus optional typed steps, one line each, which the marker
   checks against the `M` points. Drawn work is self-checked against the worked solution and does not count towards
   competency (decision 9).
2. **v2, printed and photographed:**
   - The site prints the paper as a PDF, with an answer space per question and a small QR code per page that names
     the attempt and the page.
   - The child writes by hand. A parent photographs each page and uploads the photos.
   - The marker runs in **two steps**, because handwriting is where errors come from:
     1. The vision model transcribes each question's working, cropped by the answer-space boxes. The child or parent
        sees the transcript and fixes misreadings.
     2. A second call marks the confirmed transcript against the rubric.
   - Low-confidence marks go to the parent page for a quick review.
   - Photos go in a private Supabase Storage bucket per child, kept 90 days (decision 4).

**Model:** Qwen2.5-VL-32B on the dedicated GPU (decision 3) for transcription and marking. Measure it on 50 real
photographed scripts before turning photo marking on. If it misreads too often, try a newer open vision model, or a
handwriting-maths reader as a separate transcription step (the CHECK-MAT finding).

## English and Chinese open-ended answers

These follow the Science shape: points with `accept` and `reject`. They add a language rule. Comprehension answers that
copy irrelevant lines lose the point. Synthesis and transformation answers are marked on the required structure (for
example "Despite ..., ..."), with the meaning kept. A good share of those can be checked by rule before any LLM is
used.

## Build steps

1. **Rubric schema and storage:** the JSON above, a private Supabase table, and a reviewer page in admin. (M)
2. **Rubric drafting:** a batch job on the server for Science Paper 2 items from the past papers, reviewed in samples.
   (M)
3. **Typed-answer marker:** Science, behind the Edge Function proxy. Calibrate it on 100 owner-marked answers. (L)
4. **Math Paper 2 v1:** typed final answer plus typed steps. (M)
5. **Math Paper 2 v2:** printable paper, photo upload, the two-step transcribe-then-mark flow, and parent review. (L)
6. **English and Chinese open-ended answers.** (M)
