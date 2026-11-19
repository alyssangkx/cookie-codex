# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Alyssa's Cookie Codex is a static Astro site with two parts:
- **A PSLE revision game.** A Primary 6 student answers timed multiple-choice quizzes (PSLE 2027 syllabus; only Math has questions so far) and earns Cookie Run: Kingdom cookie cards.
- **The Codex.** A reference library of all 186 cookies.

Python scripts in `scripts/` generate all the data. The Astro site in `site/` renders it. Accounts and sync use Supabase (project `kxxnipzejmyctnziojzd`, Singapore): progress is cached in the browser and synced to the server for a signed-in child (see Accounts below).

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
python3 scripts/quiz/test_stable_ids.py   # a reworded stem keeps its id
python3 scripts/quiz/check_math.py        # must print "0 failures": re-solves every question independently (SHOW=n prints n failures, default 40)
python3 scripts/quiz/coverage.py          # top-school question types covered -> docs/quiz/coverage.md
python3 scripts/quiz/build_rewards.py     # card reward per (sub-topic, tier) -> site/src/data/rewards.json
python3 scripts/quiz/build_progression.py # P1-P5 sub-topics (tries per day) -> site/src/data/progression.json
```

After changing generators, run build → check_math → coverage → build_rewards → build_progression. The rewards depend on which sub-topics have questions.

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
  - `calc=True` marks a calculator question (PSLE Paper 2 style). The default `calc=False` is Paper 1 style (no calculator): the quiz shows a "No calculator" badge, and `check_math.py` fails any step in the worked solution that is not workable by hand (`hand_problems()` in `common.py`: 4-digit by 2-digit multiplication, division by 1-significant-digit numbers, by up to 12, or by 2-digit numbers with a short exact quotient). `calc` is not part of the id.
- **Independent check.** Every template needs `@checker(fn)`: a second solver (brute force, plug-back, or exact `Fraction`) that `check_math.py` compares with the stored answer.
  - Template names can repeat across topics. Lookups are by `(topic, key)`.
- **Diagrams.** Use `figures.py` (SVG with `currentColor`) plus `figures_<group>.py` helpers. A figure must agree with the stem's numbers and never show the answer.
- **Banks.**
  - `build.py` writes `site/src/data/quiz/math/<topic>.json`, with at least 25 unique questions per (sub-topic, level).
  - A question is filed under the sub-topic of its **first** outcome id.
  - Question ids are `<topic prefix>-<level letter>-sha1(topic | template key | canonical JSON of params)[:10]` (`stable_id()` in `build.py`). Rewording a stem, explanation or figure keeps the id; changing a template's numbers or param structure makes a new question. Never key progress on stem text. `check_math.py` fails on a duplicate id, and `test_stable_ids.py` proves a reword keeps ids.
  - There is no id alias map: the site was never deployed with v1 saves, so the v1→v2 migration simply clears `questions`.
- **Coverage.**
  - `patterns.json` is the catalogue of question types seen in top-school P5/P6 papers (from OCR'd PDFs).
  - A template covers a type by naming its `math-pat-...` id in its docstring.
  - Speed types are excluded because Speed is not in the 2021 syllabus.
- **English passage sets and visual text.** English keys `vis-NN-K` (visual text), `read-NN-K` (comprehension) and `ecloze-NN-K` (cloze) form sets: `english/build.py` emits `group`/`seq` and ships a set only if every item shipped (`hold_sets`). Cloze blanks are `(1) ____`; the asked one is `(N) ________` (8 underscores) and the quiz page highlights it. An item may carry `"visual": {kind: poster|notice|brochure|timetable|email, title, subtitle?, blocks: [{heading?, lines[]}], footer?}` (plain strings; all items of a `vis-` set share it, `check_english.py` enforces). The quiz page draws it as a CSS card above the stem (timetable lines with ` | ` become a table; email `From:/To:/Subject:` lines become the header) and the review screen shows it collapsed.
- **Syllabus.** `site/src/data/syllabus/<subject>.json` is strands → topics → sub-topics → outcomes, surveyed from SEAB/MOE (sources in `docs/syllabus/`).

### Chinese banks (`scripts/quiz/chinese/`)

- **完成对话 (8-option dialogue sets).** Sub-topic `chi-dialogue-mcq` has 8 options (A-H), not 4: a set is one dialogue with 4 blanks, one item per blank (keys `duihua-NN-K`), all sharing the same stem text and the same 8 phrases (4 used once each, 4 distractors). `build.py` shuffles the 8 with one seed per set, emits `group`/`seq`, and ships a set only if all 4 blanks pass review. `check_chinese.py` checks the shared stem/options, 4 different answers, explain length 8. The quiz page shows `chi-dialogue-mcq` questions in a 2-column grid, and greys out a phrase already answered correctly for an earlier blank in the same quiz (a hint only). WA/SA papers skip 8-option items.

### English banks (`scripts/quiz/english/`)

Same contract as the Chinese banks, with 4 options per item and no passage sets yet.

```bash
python3 scripts/quiz/english/build.py     # items/*.json (the sub-topic is each file's "subtopic" field; several files may share one) + review.json -> site/src/data/quiz/english/<topic>.json
python3 scripts/quiz/check_english.py     # must print "0 failures"
python3 scripts/quiz/english/coverage.py  # -> docs/quiz/english-coverage.md
python3 scripts/quiz/build_rewards.py     # after the banks change
```

- **Items** are `{key, level, outcome, pattern, stem, options[4], answer, explain[4], solution[], gloss?}`. `pattern` is an id from `patterns.json`; `outcome` is a syllabus outcome id under the file's sub-topic.
- **Review gate.** An item ships only if `review.json` has `"<subtopic>|<key>": {"ship": true, "fingerprint": ...}` for its current stem, options, answer, explain and solution (`fingerprint()` in `scripts/quiz/bankcommon.py`, shared with the Chinese build). Anything else is dropped, unreviewed or stale. Options are shuffled with a seed from the key; ids are `eng<strand>-<sha1(topic|key)>` and ignore the level. Empty and stale banks are not written or are deleted.
- **Checks.** Stem has a `____` blank or a `?`; options are 4 distinct strings with the same first-letter case and end punctuation; explain is null only for the answer.
- **Site.** `train.ts` marks English `ready` once a sub-topic has a playable tier (20 questions). `build_rewards.py` already lists English sub-topics (playable ones first within English), so Math and Chinese rewards do not move. English is open on the home map (`home-hotspots.json`), with the `chinese-english-open` art; `index.astro` shows a school open only when its hotspot says "open" AND `SCHOOLS.ready` is true, and throws if the art for the open set is missing.

### Science banks (`scripts/quiz/science/`)

Same contract as English (4 options, items + `review.json` with fingerprints, fail-closed, key-seeded shuffle, ids `sci<strand>-<sha1>`), reusing `scripts/quiz/bankcommon.py`. No passage sets.

```bash
python3 scripts/quiz/science/build.py     # items/*.json (each file has "subtopic") + review.json -> site/src/data/quiz/science/<topic>.json
python3 scripts/quiz/check_science.py     # must print "0 failures"
python3 scripts/quiz/science/coverage.py  # -> docs/quiz/science-coverage.md
python3 scripts/quiz/build_rewards.py     # after the banks change
```

- **Figures.** An item may carry `"figure"`, copied into the bank question and part of the review fingerprint: (a) an inline SVG string made by code (black and white, `currentColor`, with a `viewBox`; no scripts, handlers, external refs or other colours), drawn like Math figures; or (b) line art `{"img": "/science/<file>.webp", "alt": "...", "labels": [{"x": 0-100, "y": 0-100, "text": "..."}]}` with the file under `site/public/science/`. The quiz page shows (b) as the image with the labels placed on it as escaped HTML (`figureHtml` in `quiz/index.astro`). `check_science.py` validates both, and fails a label that equals the correct option.
- **Site.** `train.ts` marks Science `ready` once a sub-topic has a playable tier. The home map shows a school open only when its hotspot says "open" AND `SCHOOLS.ready`; flip the Science hotspot in `home-hotspots.json` only after the content passes review (the `all-open` art exists). When the first Science sub-topic becomes playable, `build_rewards.py` moves it to the front of Science, so Science slots shift; Math, Chinese and English do not.

### Game (`site/src/lib/`)

- **`store.ts`** is the only code that touches localStorage (key `ccx:save`, interface `SaveV1`, now `schemaVersion: 3`). Never read or write storage directly. Rules it implements:
  - **Clearing is mastery.** A tier is cleared when every question in it is retired (`questions[id].s === 0`), for all tiers (P1-P6, Math and Chinese). A question answered right the first time retires at once; a wrong one retires after its 1, 3, 7 day retests are answered right. The score and the ≥ 80% pass flag on a full 10-question quiz are kept for display only. `store.ts` has no question ids, so `finishQuiz(..., tierIds)` takes a `"sub|tier" -> ids` map from the quiz page (which has the banks loaded) and `syncTiers()` stores `mastered`/`total` on the tier state and clears a tier when they match, awarding its card (a duplicate adds a star). Other pages show `mastered` of the build-time question count. A cleared tier is never un-cleared. **Exception: a perfect first try on Basic or Intermediate, all subjects.** If a child's first-ever tier quiz on a sub-topic's Basic or Intermediate tier scores 10/10 (a full `QUIZ_SIZE` quiz), `finishQuiz` clears that tier at once (before `syncTiers`), awards its card and the next tier opens (`QuizResult.autoPromoted`; the result screen says "Perfect first try! <Tier> cleared, and the next tier is open."). "First" is per tier: no earlier tier attempt for that `sub|tier` in `s.attempts`; any earlier attempt on it, finished or abandoned (`open`), means it is not a first try, so quitting after a mistake and retrying cannot earn it. Competent is not included and clears by mastery; everything else follows mastery. A Daily Review can clear a tier too (`newlyCleared`).
  - **Tries per tier per day** depend on the sub-topic's P-level (highest outcome `level` in the syllabus JSON): 5 for P1-P5, 3 for P6 and all Chinese (`triesPerDay(sub)`). `site/src/data/progression.json` (from `scripts/quiz/build_progression.py`, run after `build_rewards.py`) lists only the P1-P5 sub-topics, so `store.ts` imports no big JSON; an unlisted sub-topic counts as P6. The daily cap is a parent setting, 45 to 120 minutes in steps of 15.
  - Spaced retest: a wrong answer is due again in 1, then 3, then 7 days; a new question answered correctly retires at once. `questions[id].a` (optional) keeps the option text picked on the latest wrong answer for the parent page's "Questions answered wrong" list, which also lets the admin pick a child and read that child's save (select only; RLS already allows an admin).
  - Practice papers never retire questions.
  - A started quiz counts toward the daily tries (5 for P1-P5, 3 for P6).
  - The daily limits: the day ends at `dailyCapMin` minutes (default 120, parent range 45-180). The 10-quiz limit (`DAILY_QUIZ_CAP`) is **switched off for now** (`QUIZ_CAP_ON = false`, owner's request, 19 Nov 2026); set it to `true` to restore the rule below, where the day also ends at 10 quizzes, whichever comes first. The tests pass `true` to keep the cap logic covered. Tier quizzes and WA/SA papers count from the moment they start (`beginQuiz()` records an open attempt, replaced when the quiz finishes, so an abandoned one still counts); Daily Review and retests inside a tier quiz do not. After the quiz limit only Daily Review stays open; after the time limit nothing does. `dayBlock(s, mode)` gives the reason and `blockMessage()` the text; the quiz page re-checks it in `begin()`. There is also a daily goal.
  - **Admin test account:** `isUnlimited()` is true when kv `player-name` is `Admin` (a deliberate name-based check; signing in as it needs its PIN; cached once per page load, since login and logout navigate). It has no time cap, no quiz cap, no tries-per-day limit, and `tierOpen()` is always true so every tier is unlocked. Tiers under `MIN_POOL` are still unplayable; clearing, cards and mastery work normally.
  - The streak counts weeks with 4 or more goal days, so weekends never break it.
  - Card power reflects retention.
  - `migrations` runs on `load()` and `importCode()`. Add a new step there for every schema bump.
    - 1→2 keeps progress, cards, attempts, days, streak and settings, and clears `questions` (old stem-hash ids cannot be matched).
    - 2→3 changes no fields. A tier whose questions are all retired but not yet marked cleared only clears after its next quiz (`syncTiers` needs the question ids, which only the quiz page has). There is deliberately no load-time sync.
    - 3→4 sets `dailyCapMin` to 120 only if it is exactly 45 (the old default); other values were a parent's choice and stay. (Deliberate: the owner asked for a 2-hour cap for the existing child.)
    - `load()` copies the pre-migration save string to `ccx:backup`.
    - If a save is unreadable or a migration fails (no step, or a throw), `load()` keeps the raw string in `ccx:failed:1..3` before returning `fresh()`, and leaves `ccx:save` alone until a real save. A string already stored is not added again; when all 3 slots are full they rotate (2 to 1, 3 to 2, new into 3) so the newest broken save is kept; a legacy `ccx:failed` key is folded into the slots once and removed. Recover a save by copying a slot's value back into `ccx:save`.
    - `importCode()` writes no backup. The parent page calls `backupLocal()` only after the user confirms the import.
  - It also handles the save code (export/import). The PIN lives on the server only.
  - One allowed exception: the inline pre-paint gate script in `Base.astro` reads the single `ccx:auth` key (`AUTH_KEY` in `supabase.ts`) to redirect before first paint, because an inline script cannot import modules.
- **PIN login** (`supabase/functions/pin-login`, SQL in `supabase/migrations/001_init.sql`; applied and deployed, live-tested in Phase B). One atomic RPC checks then counts a device key (5 tries) and a `name:` (20, no token) or `trust:` (30, valid token) key; any locked key counts nothing. Locks double from 15 min to 24 h. The device fail count resets after 15 quiet minutes (forgives typos); name and trust counts only after 24 h, so pacing does not avoid escalation; escalation decays after 7 quiet days. Success clears the device and only the name-side key it used (a trusted login never resets a stranger's `name:` escalation; the admin can clear it). There is no IP limit. Worst case: about 240 days (stranger) or about 92 days (copied tokens) to 5,000 guesses; details in `docs/accounts-plan.md` section 5.
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
| `/parent/` | Parent page, gated by an admin session at aal2 (the old PIN screen is gone); shows the save on this device |
| `/login/` | "Who's playing?": name + 4-digit PIN pad, calls `pin-login` |
| `/admin/` | Admin email + password, TOTP (aal2), children, PINs, name locks, Test Player and its test tools |
| `/codex/` | The Library (cookie shelf) |
| `/cookie/<slug>/`, `/personality/<tag>/` | Codex detail pages |

- `/data/quiz/<topic>.json` is a static endpoint serving the slim banks, which the quiz page fetches.
- Markup built with innerHTML needs `<style is:global>` with page-prefixed selectors, because scoped styles don't reach it.

### Accounts (`supabase/functions/admin`, `site/src/lib/{supabase,sync,testtools}.ts`)

- **`admin` Edge Function** (JWT verification ON; needs `app_metadata.role = 'admin'` and `aal2`): `create_child`, `set_pin` (shares `_shared/pin.ts` hashing), `clear_name_lock`, `list_children`, `create_test_player`, `test_login` (a session for the Test Player only), `delete_child` (non-test needs `confirm` = the name). Redeploy: `supabase functions deploy admin --use-api --yes`.
- **`supabase.ts`** is the one browser client (session persists in localStorage; 90-day idle sign-out; `callFunction` uses plain fetch because the CORS allow-list has no `x-client-info`).
- **`sync.ts`** sits under `store.ts` (`save()` calls a hook; `store.ts` stays the only code touching localStorage, incl. `kv` for device id/token/revs). Pure decisions (`decideHydrate`, `decidePush`, ...) are tested in `sync.test.ts`. Push is debounced 2 s with the base rev; a conflict shows a banner (use the newer one, or force-push with `p_force`); `denied` stops syncing quietly.
- **Login gate** is in `Base.astro`: game pages (`/`, `/train`, `/quiz`, `/paper`, `/collection`) redirect to `/login` without a session; `/parent` needs an admin at aal2; the Library stays public. Header "Log out" ends this browser's session only.
- Test tools (`testtools.ts`) edit only the Test Player's save through `push_save`; the database refuses an admin write to anyone else.

### Cookie data

- `site/src/data/cookies.json` (committed) comes from `build_cookie_data.py`. Edit the generator, not the JSON.
- Each rarity needs a `--r-<rarity>` colour in `global.css`.
- `site/public/cookies/` is the committed image copy; `downloads/` is the gitignored raw scrape.
