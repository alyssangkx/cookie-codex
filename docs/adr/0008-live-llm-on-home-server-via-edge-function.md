# Live LLM features run on the home server behind a Supabase Edge Function proxy; tutor chat is low priority

Status: accepted (design; nothing built). Date: 20 Nov 2026. Source: `docs/learning-loop-design.md` (Shared, Owner decisions), `docs/past-papers-design.md` section 9.

**Context.** Marking open answers and a tutor chat need a model. A hosted API would receive copyrighted keys and rubrics and children's free text. The model is on the owner's machine, which is not safe to expose directly.

**Decision.** Live LLM features run on the home server, never on a hosted API. The browser calls one Supabase Edge Function that checks the session, rate-limits, loads the question and rubric server-side and calls the model over an outbound tunnel; the browser never sees the model's address. The child-facing model must be a safety-aligned one. The open-answer marker comes before the tutor chat, and the tutor chat waits until most of the site is redesigned.

**Consequences.** Past-paper text and rubrics never ship in `site/`. The model must be available whenever children play, which competes with the server's image workers for GPUs. The build order is affirmations, submit-then-review, the assessment cycle, the marker, then the chat.
