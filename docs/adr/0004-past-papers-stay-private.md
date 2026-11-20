# Past papers stay private; verbatim items only via Supabase with RLS after a blind-answer check

Status: accepted. Date: 20 Nov 2026. Source: `docs/past-papers-design.md` (Scope), `docs/learning-loop-design.md`, `docs/todo.md` (Past-paper data quality).

**Context.** The 2018-2026 papers are commercial and copyrighted; the owner holds the copies. The repo is public. Audits found about 6% of Math keys and at least 5% of English keys wrong or mismatched, and the vision model's `ans_check` flag did not predict errors.

**Decision.** Past-paper text, images, answers and rubrics never enter the repo or `site/`. Site drills are original items modelled on the papers. Verbatim past-paper MCQs may reach a child only from a private Supabase table behind row-level security, and only after a blind-answer check; items from the audit are quarantined. Docs carry counts, not text.

**Consequences.** Anything that touches papers writes outside the repo. Verified past items never count toward tiers or cards. The import waits for the blind-answer check and the owner's go-ahead.

## Amendment, 20 Nov 2026 (owner)

**Decision.** Science uses the checked past-paper MCQs with their original pictures (compressed WebP crops), and they count like generated questions:
- **Progress:** they count fully toward mastery, tier clearing, cards and Crumbs. This replaces "Verified past items never count toward tiers or cards" above.
- **Per sub-topic, per tier:** past-paper items are mixed in while a tier has fewer than 20 of them, and replace the generated items once it has 20 or more. Each sub-topic switches on as its import lands, Plant transport first; the generated items stay live until then. Daily Review always mixes, so older retests stay reachable.
- **Checked** means the blind-answer check agrees with the key, or a second local solver does. The second solver has two routes, the vision model at full resolution and the 72B text model on the transcribed figure text, and both must reach the key. Items also pass the quarantine, the answer-grid check and a visual review of their pictures.
- **Readers:** signed-in children (including the Test Player) and the admin only. No parent role, no anon (migration 004). The parent page's wrong-answer list leaves past-paper items out.
- **On screen:** "Past paper <year>". The school is never shown or sent.
- **Tiers:** difficulty 1 is Basic. Difficulty 2 is Intermediate, or Competent when the item sits in the last 40% of its booklet's MCQs. Difficulty 3 is Competent.

**Unchanged:** no past-paper text, picture or answer enters the repo, `site/`, `site/dist` or the public `/data/quiz` endpoint. Docs carry counts only.
