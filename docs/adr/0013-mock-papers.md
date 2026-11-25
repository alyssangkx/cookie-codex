# Mock papers: PSLE Paper 2 blueprints on the paper runner, scored out of the marks covered

Status: **proposed (draft)** · Date: 2026-11-25 · Source: owner's accepted defaults, Phase 1 report section 4 (24 Nov 2026) · Design: [mock-paper-design.md](../mock-paper-design.md)

**Context.** The paper runner takes only single 4-option questions, has no sections or marks, caps at 40 questions and a
full paper uses about 30% of the daily past-paper allowance (ADR 0012). Chinese is not offered, and an English paper
is Grammar and Vocabulary only. A child preparing for Paper 2 cannot practise its real shape. Editing, Comprehension OE
and 阅读理解二 have no questions the site can mark, and no single past paper is complete in the data.

**Decision.**
- Add a "Mock paper" mode to the existing paper runner, one blueprint file per subject (`site/src/data/mockpaper/`),
  with sections in paper order, marks, minutes and an `available` flag.
- Start without Editing and the open-ended sections; score out of the marks covered (English 60 of 90, Chinese 58 of 90).
  A section is added by flipping its flag.
- Past-paper questions only, drawn as whole sets, mixing schools and years, unseen first, then due retests.
- A mock paper does not count toward the daily past-paper allowance. This needs a migration to `pp_serve`, with a
  ceiling (3 mock papers a day per account) so the exemption cannot be used to copy the pool.
- Show an AL band, labelled an estimate while sections are missing.
- A mock paper counts toward the Legendary card by today's rule.
- Wrong and blank answers become 1/3/7-day retests as in a paper; papers never retire questions or clear tiers.
- Draft v2 in kv, no save schema bump.

**Consequences.** Six build steps (blueprint, sets, typed and cloze screens, Chinese, batched fetching with the
migration, per-section results). The migration touches the anti-scraping gate and needs review and the owner's
approval. Open questions: scale the clock to the marks covered; whether the 120-minute daily cap applies to a mock paper;
partial marks for Synthesis; the blank counts of the real sets are unverified; 2027 formats are unconfirmed.
