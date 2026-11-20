# No save schema bump for content redesigns; never delete orphan question states

Status: accepted. Date: 20 Nov 2026. Source: `site/src/lib/store.ts` (`liveMastered`), `site/src/pages/parent/index.astro`, `docs/learning-loop-design.md` section 2.

**Context.** The 20 Nov 2026 redesign changed most Math question ids and removed pilot questions. A schema bump would stop an old browser tab from reading a save written by a newer version, and that tab could then overwrite the server save.

**Decision.** Content redesigns do not bump `schemaVersion`; new save fields are optional. Question states whose ids are no longer in any bank (orphan question states) are kept, not deleted. Display code handles them: `liveMastered` reads a stored mastered count as 0 when it was made against a bank of a different size, and the parent page leaves orphans out.

**Consequences.** Stale counts show as 0 until the next quiz on the tier recounts them. A redesign of the same size can slip past the size check (noted in code). A bump is reserved for a real change of save shape, with a migration step.
