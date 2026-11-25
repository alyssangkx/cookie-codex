# Open-ended answers are typed, kept 90 days, and marked overnight on the home server

Status: **proposed** (design only; owner to accept) · Date: 2026-11-25 · Source: owner's accepted defaults, P5 scope report, section 5 · Builds on ADR 0008 (stands unchanged), ADR 0004 and ADR 0012

**Context.** English Comprehension OE and Chinese 阅读理解二 need written answers marked against a school key and a point
rubric. String matching (migration 015) cannot do it. The only strong marker is a language model, and ADR 0008 forbids
sending a child's answers to a hosted one. Past-paper keys and rubrics are private (ADR 0004).

**Decision.**
- **ADR 0008 stands.** A child's typed answer, the passage, the key and the rubric are never sent to a hosted model. Only
  the owner's home GPU server marks them.
- **Pull, not push.** The home server's worker polls a Supabase Edge Function outbound over HTTPS and posts results back.
  No tunnel and no open port are needed for marking. ADR 0008's tunnel remains the plan only for a future live tutor chat.
- **Key and checklist at once, mark next visit.** At submit the child sees the school key and a point checklist (self-check
  ticks that never change the mark). The model's mark arrives the next day. Below full marks counts as wrong and is
  retested after 1, 3 and 7 days from the submit time.
- **One private table for the text.** `oe_answers` holds the typed text, 90 days, readable by the child, the child's parent
  and the admin through functions only; limits per child, per family and per question. Rubrics live in a separate
  service-only table and an item is open for answers only when its rubric is approved.
- **The server checks the model.** An awarded point needs a span that appears in the answer; the total is recomputed from
  the awarded points; low confidence shows "ask a grown-up" and never books a retest by itself.
- **No save schema bump.** The mark reaches the device through the existing `answer()` and the `a` field.
- **Model by test.** The owner blind-marks 40 questions x 5 answers per language; a model is used for a language only if
  it matches the owner's exact total on at least 85% and wrongly gives full marks on at most 5%.
- **Privacy notice and consent version change** before any child types an answer.

**Consequences.** Marking is overnight: the child's next visit shows the mark, and a server outage delays it (a parent can
mark by hand after 7 days). A new table, an Edge Function, a worker program and a parent list are needed. The home server's
GPUs are shared with the image workers, so the worker runs in a night window and defers to them. Retesting from the submit
time means a mark that arrives late can already be due. The design and build order are in `docs/open-ended-design.md`.
