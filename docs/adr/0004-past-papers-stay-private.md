# Past papers stay private; verbatim items only via Supabase with RLS after a blind-answer check

Status: accepted. Date: 20 Nov 2026. Source: `docs/past-papers-design.md` (Scope), `docs/learning-loop-design.md`, `docs/todo.md` (Past-paper data quality).

**Context.** The 2018-2026 papers are commercial and copyrighted; the owner holds the copies. The repo is public. Audits found about 6% of Math keys and at least 5% of English keys wrong or mismatched, and the vision model's `ans_check` flag did not predict errors.

**Decision.** Past-paper text, images, answers and rubrics never enter the repo or `site/`. Site drills are original items modelled on the papers. Verbatim past-paper MCQs may reach a child only from a private Supabase table behind row-level security, and only after a blind-answer check; items from the audit are quarantined. Docs carry counts, not text.

**Consequences.** Anything that touches papers writes outside the repo. Verified past items never count toward tiers or cards. The import waits for the blind-answer check and the owner's go-ahead.
