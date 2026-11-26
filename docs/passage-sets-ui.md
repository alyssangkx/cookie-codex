# Passage sets: text on screen, every answer before one Submit (owner, 26 Nov 2026)

Owner's words: the Chinese MCQ cloze reads from a scanned passage; OCR it into text on the site, with the 4 options inside
the passage, clicking one selects it and greys out the other 3, all questions answered before submission. The same for
every Chinese section that uses an image (dialogue completion: drag and drop the answers into the blanks). For all
multi-question passage questions in all subjects, the answers are all filled before submission.

## Data (one contract, the one English cloze already uses)

- **Only text-only passages become text** (owner, 26 Nov 2026). A page with a picture, photo, chart, map or table the passage
  or its questions need keeps its scanned image (English Visual Text always does). The OCR reads say PICTURE for such a page.

- **Cloze (chi-cloze-mcq) and dialogue (chi-dialogue-mcq):** every row of a set carries the WHOLE passage (dialogue: one
  turn per line, `名字：话`) as its `stem`. Each blank is `（n）＿＿＿＿`; the row's own blank is marked like an asked English
  cloze blank. `options` stay per row (cloze 4, dialogue the shared 8). The scanned page leaves `figures` once the text is in.
  Text comes from two server reads that agree (queue 41, `scripts/pastpapers/zh_passage_ocr.py`); a set without an agreed
  read keeps its picture and works as today.
- **Reading (chi-yuedu-mcq-text) and other passage MCQ sets:** each row keeps its question as `stem`; the passage travels as
  a text figure `{"text": "<passage, paragraphs separated by blank lines>"}` in `figures` (same for every row of the set).

## Screens (quiz page, sub-topics that are whole-passage sets)

1. **One screen per set, one Submit.** All questions of the set are answered first; Submit marks them all (an unanswered
   question gets one warning, like the typed cloze; all of them count when time runs out). Each question stays its own
   question for scores and retests. This applies to every passage set in every subject (Chinese reading, dialogue, cloze;
   English visual text, comprehension, vocabulary cloze passages): `group` set on the rows.
2. **Cloze MCQ:** the passage is text; at each blank the 4 options sit inline as chips. Tapping one selects it and greys out
   the other 3 of that blank (tap another to change). No separate option list.
3. **Dialogue:** the 8 phrases sit in a bank above the dialogue. Drag a phrase onto a blank (desktop), or tap a phrase then
   tap a blank (touch and keyboard: the same flow, so it works without drag). A placed phrase greys out in the bank; tapping a
   filled blank sends its phrase back.
4. **Reading:** the passage text above, the questions below, each with its options; one Submit.
5. **After Submit:** the passage shows every answer in place (right in green, wrong with the correct one), and under it one
   line per question: "(n) **answer** reason" (the existing past-paper explanation format).

Accessibility: every chip and blank is a real button with a label; focus order follows the passage; it works at phone
width (16px gutter) with no horizontal scroll.
