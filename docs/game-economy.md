# Game economy proposal (pilot to redesign)

**Status: built 20 Nov 2026** after the owner's answers (all as recommended), then tightened after review. Where it
differs from the text below, this list wins:
- The ledger is an optional save field with no schema bump (ADR 0002), not a migration.
- **WA/SA paper Crumbs scale with length:** the band's Crumbs x (questions / 10), at most x3 (10 questions x1, 20 x2,
  30 or more x3), rounded, at least 1. A short paper never pays more per question than a tier quiz.
- **Legendary, paper route:** a paper of 20+ questions from 3+ topics at AL1-AL2 (85%+), at most one per calendar week;
  later qualifying papers that week earn their Crumbs only.
- **Legendary, subject route (built):** once per subject, when every competency topic of the subject (below) has all its
  playable Competent tiers cleared; a subject counts once it has 2 or more competency topics.
- **Super Epic:** once per competency topic: a Math or Science topic, or an English or Chinese booklet (their topics are
  single paper sections), counting only sub-topics with a playable Competent tier, and only groups with 2 or more.
Code: `site/src/lib/crumbs.ts` (`quizCrumbs`, `competencyGroups`), `store.ts` (`finishQuiz`, `purchase`), `/shop/`.

Status: proposal for the owner (20 Nov 2026). It amends [game-design.md](game-design.md), whose rules still apply: no
loot boxes, no money, no leaderboards or comparing children, rewards shown before they are earned.

**Context.** The first question banks were a pilot. The banks are now being redesigned from the past-paper repository,
and they will keep changing. Game mechanics come second to learning, but **a card that was awarded is never taken
away.**

## 1. Replacement cards for redesigned tiers

- When a redesigned tier is cleared and its slot's cookie is **already owned**, award a **replacement**: the next
  unowned cookie of the same rarity, in a fixed order kept in `rewards.json`.
  - This covers both cases: a card earned in the pilot, and a card moved by a slot reshuffle.
  - There is no randomness. The tier page previews the actual card the child will get.
- If every cookie of that rarity is already owned, give one star on the slot's cookie plus a coin bonus (section 2).
- Done at award time in `store.ts`, because only the save knows which cards are owned. `rewards.json` adds a
  per-rarity order list.
- Today a duplicate becomes a star. Replacement makes clearing a redesigned tier always feel new.

## 2. Coins from quizzes

A small currency earned by doing the work. Suggested name: **Crumbs**.

**Earn.** The score bands follow PSLE AL grading, so the numbers teach the real scale.

| Quiz score | AL band | Crumbs |
|---|---|---|
| 90–100% | AL1 | 8, plus 4 for a perfect score |
| 85–89% | AL2 | 7 |
| 80–84% | AL3 | 6 |
| 75–79% | AL4 | 5 |
| 65–74% | AL5 | 4 |
| 45–64% | AL6 | 3 |
| 20–44% | AL7 | 2 |
| under 20% | AL8 | 1 (finishing always earns something) |

- **WA/SA paper:** the same bands multiplied by the paper's length: x(questions / 10), at most x3 (built rule; see Status).
- **Learning extras:**
  - each retest step passed: 1 (rewards remembering);
  - daily goal met: 3;
  - a streak week: 10;
  - beating the last diagnostic band in a topic: 15.
- **Never earned for:**
  - abandoned quizzes;
  - quizzes past the daily tries or time cap (already capped);
  - the unlimited test account. It can earn, but its coins are flagged and kept out of parent stats.
- Coins are never lost and never expire. There are no penalties.

**Spend: a shop with fixed prices.** The child picks the exact card. There are no packs and no random draws.

| Rarity (cards in the game) | How to get it |
|---|---|
| Common (7) | 30 Crumbs, or tier rewards |
| Rare (14) | 60 Crumbs, or tier rewards |
| Special (11), Epic (116) | 120 Crumbs, or tier rewards |
| Super Epic (13) | **Not for sale.** Competency in a topic: every sub-topic's Competent tier in that topic cleared |
| Legendary (11) | **Not for sale.** A WA/SA paper at AL1–AL2, or a subject's topics all at Competent |
| Beast (6), Dragon (2), Witch (1), Ancient (5) | **Not for sale.** The existing school milestones, plus big re-assessment improvements |

**Pace.** At 2 to 4 quizzes a day, a child earns about 15 to 25 Crumbs a day. That is a Common about every 2 days, a
Rare every 3 to 4, and an Epic about weekly. So coins top up a collection rather than replace tier rewards.

**When there is nothing left to buy:**
- spend coins on stars for owned cards (a coin sink with no learning cost);
- or on decorations in My House (later).

## 3. Guardrails

- **No real money, ever.** Coins can't be bought, traded or sent between children.
- **No pressure tactics:** nothing random, no time-limited shop, no flash sales, no fear-of-missing-out timers.
- **Parents see everything:** the parent page shows the coin ledger (last 50 entries) and what was bought.
- **Rare cards prove learning.** The rarest cards come only from competency and paper results, never from coins or
  playing time.
- **Accepted risk:** coins live in the save, which the child's own device can edit, like every other limit (site
  review F11). That's fine for one family. Server-side checks are needed only if coins ever matter beyond the family.

## 4. Build steps (after the learning-loop items)

1. Replacement cards: `rewards.json` rarity order, the award logic in `store.ts`, the tier preview, and tests. (S–M)
2. Crumbs ledger in the save (a schema bump with a migration that starts everyone at 0), earning hooks in
   `finishQuiz` and retests, and display on the result screen next to the encouragement line. (M)
3. Shop page: fixed prices, buy chosen cards, and stars for owned cards. (M)
4. Achievement-only cards: topic competency, WA/SA AL bands, re-assessment improvement. (M, after the assessment
   cycle)

## Owner questions

1. Name the currency "Crumbs"? (Or "Dough" or "Sprinkles".)
2. Approve the AL-mirrored earning table and the prices above? (Recommended: yes, then tune after two weeks of real
   use.)
3. Should tier clears keep giving a card as well as coins? (Recommended: yes, so cards still mark mastery.)
4. Super Epic for topic competency, Legendary for WA/SA AL1–AL2: is that the right bar?
