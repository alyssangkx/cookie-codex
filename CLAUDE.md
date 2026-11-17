# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Alyssa's Cookie Codex is a static Astro site with two parts:
- **A PSLE revision game.** A Primary 6 student answers timed multiple-choice quizzes (PSLE 2027 syllabus; only Math has questions so far) and earns Cookie Run: Kingdom cookie cards.
- **The Codex.** A reference library of all 186 cookies.

Python scripts in `scripts/` generate all the data. The Astro site in `site/` renders it. There is no backend: game progress lives in the browser.

## Commands

Site (run from `site/`; `node_modules` is not committed):

```bash
npm install
npm run dev       # dev server
npm run build     # static build to site/dist/
```

Tests and checks (from the repo root):

```bash
node --test site/src/lib/*.test.ts        # game logic: store, pick, suggest (Node 24 strips TS types)
python3 scripts/quiz/math/build.py        # regenerate all Math question banks (--topic math-ratio for one)
python3 scripts/quiz/check_math.py        # must print "0 failures": re-solves every question independently
python3 scripts/quiz/coverage.py          # top-school question types covered -> docs/quiz/coverage.md
python3 scripts/quiz/build_rewards.py     # card reward per (sub-topic, tier) -> site/src/data/rewards.json
```

After changing generators, run build → check_math → coverage → build_rewards. The rewards depend on which sub-topics have questions.

Cookie data refresh (needs `requests`; both scripts hit live sites with a delay per cookie):

```bash
python scripts/crk_images.py         # portraits -> downloads/crk_cookies/ + manifest.csv
python scripts/build_cookie_data.py  # -> site/src/data/cookies.json, copies images to site/public/cookies/
```

## Architecture

### Question banks (`scripts/quiz/math/`)

- **Generators.** Each `topic_*.py` registers parametric generators with `@template(topic, level, *outcomes)`, defined in `common.py`.
  - A generator picks random numbers and returns a stem, the correct value, and wrong options. Each wrong option comes from a named mistake (a `tag` plus a `why`).
  - `build()` takes two method mistakes first, then one careless slip.
  - `whole=True` drops non-integer distractors.
  - `auto_slips=False` turns off the automatic fraction slips (use it for decimals and money).
- **Independent check.** Every template needs `@checker(fn)`: a second solver (brute force, plug-back, or exact `Fraction`) that `check_math.py` compares with the stored answer.
  - Template names can repeat across topics. Lookups are by `(topic, key)`.
- **Diagrams.** Use `figures.py` (SVG with `currentColor`) plus `figures_<group>.py` helpers. A figure must agree with the stem's numbers and never show the answer.
- **Banks.**
  - `build.py` writes `site/src/data/quiz/math/<topic>.json`, with at least 25 unique questions per (sub-topic, level).
  - A question is filed under the sub-topic of its **first** outcome id.
  - Question ids hash the stem, so adding templates never re-points a saved progress entry.
- **Coverage.**
  - `patterns.json` is the catalogue of question types seen in top-school P5/P6 papers (from OCR'd PDFs).
  - A template covers a type by naming its `math-pat-...` id in its docstring.
  - Speed types are excluded because Speed is not in the 2021 syllabus.
- **Syllabus.** `site/src/data/syllabus/<subject>.json` is strands → topics → sub-topics → outcomes, surveyed from SEAB/MOE (sources in `docs/syllabus/`).

### Game (`site/src/lib/`)

- **`store.ts`** is the only code that touches localStorage (key `ccx:save`, schema `SaveV1`). Never read or write storage directly. Rules it implements:
  - A pass is ≥ 80% on a full 10-question tier quiz. Two passes on different days clear the tier and award its card; a duplicate card adds a star.
  - Spaced retest: a wrong answer is due again in 1, then 3, then 7 days; a new question answered correctly retires at once.
  - Practice papers never retire questions.
  - A started quiz counts toward the 3 tries per day.
  - The daily cap and goal.
  - The streak counts weeks with 4 or more goal days, so weekends never break it.
  - Card power reflects retention.
  - It also handles the save code (export/import) and the PIN hash.
- **`pick.ts`** chooses questions:
  - tier quizzes are always 10 (≤ 3 due retests from the sub-topic, then new questions, then not-due retests, then retired ones);
  - Daily Review takes 5–15 due retests;
  - WA/SA papers are mixed across chosen topics.
- **`suggest.ts`** works out power (tier weights 1/2/3) and the "train today" suggestions.
- **`train.ts`** (build time only) holds sub-topics in reward order, question counts and the playable flag per tier (20 or more questions), rewards and card info.
- **Rewards are fixed and previewed:** there is no randomness at play time. All 186 cookies are used once each; the 7 commons sit on the first playable sub-topics.
- Design rules are in `docs/game-design.md`, as amended by `docs/game-design-review.md`: no leaderboards or comparing children, no monetisation or loot boxes, a parent-set daily cap.

### Pages (`site/src/pages/`)

| Route | Page |
|---|---|
| `/` | Home base: the map art (`public/home/map-{wide,tall}.webp`, no text in the image) with HTML hotspots from `data/home-hotspots.json`. Re-check the hotspot positions with screenshots whenever the art changes. |
| `/train/math/` | "What do you want to train today?" |
| `/train/<school>/<sub>/` | Tier page with the reward preview |
| `/quiz/?sub=&tier=` | The quiz runner; also `?mode=review` and `?mode=paper&topics=` |
| `/paper/` | WA/SA paper builder |
| `/collection/` | My House |
| `/parent/` | PIN-gated parent page |
| `/codex/` | The Library (cookie shelf) |
| `/cookie/<slug>/`, `/personality/<tag>/` | Codex detail pages |

- `/data/quiz/<topic>.json` is a static endpoint serving the slim banks, which the quiz page fetches.
- Markup built with innerHTML needs `<style is:global>` with page-prefixed selectors, because scoped styles don't reach it.

### Cookie data

- `site/src/data/cookies.json` (committed) comes from `build_cookie_data.py`. Edit the generator, not the JSON.
- Each rarity needs a `--r-<rarity>` colour in `global.css`.
- `site/public/cookies/` is the committed image copy; `downloads/` is the gitignored raw scrape.
