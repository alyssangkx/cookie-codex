# Open-ended sections: typed answers, marked on the home server

Status: design, not built (written overnight 25 Nov 2026, for the owner's review). Records the owner's accepted defaults
from the P5 scope report and sits under ADR 0008 (a child's answers never go to a hosted model) and the new ADR 0014.
Builds on [marking-framework.md](marking-framework.md) (point rubrics), [learning-loop-design.md](learning-loop-design.md)
and migration 015 (typed answers that the site marks itself). No site code and no migration file come with this document.

## What this covers

The English sections Comprehension OE, and the Chinese 阅读理解二 (and any later reading section) ask for a written answer
of a phrase to a few sentences. The site cannot mark these by string match the way it marks Synthesis (migration 015).
This design adds: an answer box, a key and checklist shown at once, a private store for the typed text, a marker that
runs on the owner's home GPU server overnight, and a way for the mark to reach the child's device and the 1/3/7-day
retest.

Out of scope: Science and Math Paper 2 open answers (same machinery later, see "Reuse"), photographed handwriting,
the tutor chat.

## Decisions taken (owner's accepted defaults)

1. ADR 0008 stands. No typed answer, passage, key or rubric is sent to a hosted model.
2. The child sees the school key and a point checklist the moment they submit. The model's mark comes later.
3. The home GPU server marks a queue overnight. The mark appears on the child's next visit.
4. A mark below full marks counts as wrong: the question comes back after 1, then 3, then 7 days.
5. The owner marks the calibration answers blind before any model is trusted (README in the calibration folder).

## 1. Answer entry

Where: a new quiz mode, `/quiz/?mode=open&sub=<section>` (not the 10-question tier quiz). A session is **3 questions**
(about 10 minutes): written answers are slow, and the day cap in minutes still applies.

On a phone (the main device):

- The question and its passage sit on one screen as two panes: a **Passage** tab and a **Question** tab at the top
  (sticky). The answer box stays above the keyboard. A "Show passage" bottom sheet covers about 70% of the height so
  the child can look back without losing the typed text. Lines of the passage are numbered when the paper numbers them,
  because stems say "lines 12 to 14".
- On a tablet or laptop the passage is a left column and question plus box a right column.
- The box is a plain `<textarea>`: grows up to 8 lines, then scrolls; limit 600 characters (English) and 300
  characters (Chinese); a live counter appears only in the last 50 characters. No spellcheck underline for English
  (`spellcheck="false"`): the marker must see what the child wrote, and the exam does not spellcheck either. Autocorrect
  and autocapitalise follow the phone's setting.
- Chinese: the box accepts the phone's own pinyin or handwriting keyboard (`lang="zh-Hans"`, `inputmode="text"`). The
  site never swaps in its own keyboard. IME composition is respected: the character counter and the Submit button ignore
  `compositionstart` to `compositionend`, so a half-typed syllable is not counted or sent. Typing pinyin letters instead
  of characters is the child's mistake; the marker is told to mark characters, not pinyin.
- Multi-part questions: the stem shows (a) and (b); there is one box per part, joined with a blank line when sent
  (the marker sees "(a) ...", "(b) ...").
- A draft lives in kv `oe-draft` on the device (not the save, no schema bump), keyed to the player, so a locked phone
  or a reload keeps the text. It is deleted at submit.
- Submit asks nothing twice: one "Hand in" button, disabled while the box is empty or only spaces. A blank answer is
  never sent; "Skip" records nothing and the question stays new.

## 2. What the child sees at submit

Right after "Hand in" (no waiting for the model):

1. The child's own answer, shown back.
2. **The school key** (the model answer), labelled "The school's answer".
3. **A point checklist**: one line per mark point, written for a 12-year-old from the rubric ("It says the bike tyre came
   off"), each with a tick box. The child ticks the points their own answer already has. The line count equals the marks.
4. A line: "Your teacher-robot will check this tonight. Tomorrow you will see your mark. What you tick now helps you learn;
   it does not change your mark."

The self-check ticks are saved with the answer row (`self_ticks`) and shown to the marker's reviewer later, so the owner
can see how far children over- or under-tick (a useful measure of learning, not used for marks).

Nothing the child sees at submit is a mark. The question does not retire at submit and does not count towards a tier's
"N mastered" yet.

What the key and checklist expose: they are the same text the paper's marking scheme already gives the child on the
answer page of a printed paper, held privately (ADR 0004). The checklist wording is generated from the rubric points and
reviewed in the same sample pass as the rubrics (marking-framework, "Where rubrics come from"). The key and checklist
are returned by the submit call and never by the question-serving call, so a child cannot read them before answering.

## 3. The private table for typed answers

Described in words, then a sketch. This is a sketch for the owner to approve; the real migration (016 or later) comes at
build step 1.

**What is stored, per answer:** who (the child's profile id), which question (the `pp-<hex>` id), the typed text, the
language, the marks available, the child's self-check ticks, when it was handed in, and the marking state (queued,
claimed by the worker, marked, failed, or skipped), the result, and when to delete it.

**Who can read:**

- the child: only their own rows, only for the last 90 days;
- the parent: the rows of their own children (the parent page's "Open answers" list), through a function that checks
  `profiles.parent_id = auth.uid()` and skips deleted profiles and families;
- the admin: all rows (for calibration and disagreements);
- nobody else; no client may insert, update or delete: all writes go through functions or the worker's Edge Function.

**Retention:** 90 days from submit (decision 4 in the Science marking plan). A nightly `private.purge_oe()` deletes
expired rows; deleting a child (7-day undo) or a parent account removes their rows (`on delete cascade`); the parent can
also delete a single answer at any time. The mark and the retest state live on in the save without the text.

**Limits:**

| Limit | Value | Why |
|---|---|---|
| Submits per child per day | 12 answers | 3 per session, 4 sessions; the day cap is 2 hours anyway |
| Submits per child per question per 7 days | 3 (original plus 2 resubmits) | a resubmit is allowed after the mark; it is a new row linked by `resubmit_of`; stops brute-forcing the key |
| Text length | 1,200 characters in the database (600 English, 300 Chinese in the box) | the box limit is for the child; the database limit is the hard stop |
| Queue size | 400 open rows overall; new submits get "try again tomorrow" if exceeded | protects the worker; the owner sees a counter |
| Per parent (family) per day | 40 answers | extra children do not multiply it (same idea as ADR 0012) |

Resubmits: after the mark appears, the child may try again from the key. A resubmit is marked like any other answer
and replaces the earlier mark for retest purposes only if it scores higher on the same question and day; otherwise the
first mark stands. (The point of a retest is recall after a gap, not copying the key within the hour. Resubmits within
the hour are allowed for learning but never count towards retiring the question.)

### SQL sketch (not a migration)

```sql
-- queue + store
create table public.oe_answers (
  id           bigint generated always as identity primary key,
  child        uuid not null references public.profiles (id) on delete cascade,
  qid          text not null check (qid ~ '^pp-[0-9a-f]{10}$'),
  lang         text not null check (lang in ('en', 'zh')),
  answer       text not null check (length(btrim(answer)) between 1 and 1200),
  marks_avail  smallint not null check (marks_avail between 1 and 12),
  self_ticks   jsonb,                       -- ["p1","p3"]
  resubmit_of  bigint references public.oe_answers (id) on delete set null,
  submitted_at timestamptz not null default now(),
  status       text not null default 'queued'
               check (status in ('queued', 'claimed', 'marked', 'failed', 'skipped')),
  claimed_at   timestamptz,
  claim_id     uuid,                        -- the worker's lease token
  tries        smallint not null default 0, -- claim count; 3 failures -> 'failed'
  marked_at    timestamptz,
  marks_awarded smallint check (marks_awarded >= 0),
  result       jsonb,                       -- validated worker output (section 5)
  model        text,                        -- model name + version, for audit
  rubric_ver   smallint,
  confidence   text check (confidence in ('high', 'medium', 'low')),
  applied_at   timestamptz,                 -- the device applied the mark to its save
  expires_at   timestamptz not null default now() + interval '90 days'
);
create index oe_answers_queue_idx on public.oe_answers (submitted_at) where status in ('queued', 'claimed');
create index oe_answers_child_idx on public.oe_answers (child, submitted_at desc);
alter table public.oe_answers enable row level security;
revoke all on public.oe_answers from public, anon, authenticated;
grant all on public.oe_answers to service_role;

-- private rubric and key (service_role only; never returned by pp_serve)
create table public.oe_rubrics (
  qid         text primary key references public.pp_items (id),
  key_text    text not null,
  points      jsonb not null,               -- marking-framework point list with accept/reject
  child_lines jsonb not null,               -- the checklist wording for the child, one per point
  version     smallint not null default 1,
  approved    boolean not null default false  -- only approved rubrics can be served for open answers
);
alter table public.oe_rubrics enable row level security;
revoke all on public.oe_rubrics from public, anon, authenticated;
grant all on public.oe_rubrics to service_role;

-- the child's write path: checks login, rate limits, rubric approved, stores, returns key + checklist
create function public.oe_submit(p_qid text, p_answer text, p_ticks jsonb default null) returns jsonb ...;
-- the child's and parent's read paths
create function public.oe_results(p_since timestamptz default null) returns table (...) ...;   -- child: own, unapplied first
create function public.oe_for_parent(p_child uuid) returns table (...) ...;                     -- checks parent_id
create function public.oe_applied(p_ids bigint[]) returns void ...;                             -- sets applied_at
create function private.purge_oe() returns void ...;                                            -- expires_at < now()
```

All functions are `security definer set search_path = ''`, check `private.can_read_pp()` for the child path (the same
gate as `pp_serve`), and use `public.rate_hit` as `report_question` does (migration 005).

## 4. The marking worker on the home server

**Direction:** the worker only ever calls out. It polls a Supabase Edge Function `oe-queue` over HTTPS. Nothing on the
home network listens for the internet, so no tunnel or open port is needed for marking. (ADR 0008's tunnel stays
reserved for a future live tutor chat.) Authentication: a long random worker key held in the Edge Function secrets and
in the server's private config, sent as a bearer header; the function uses the service role internally. The key is
never in the repository or the site.

**Loop** (a systemd timer on the server, nightly window, say 22:00 to 06:00 Singapore time, plus a quick drain when the
GPU is idle; the existing image workers keep priority, so the first line of the loop is the GPU-free check from the
server handover notes):

1. `claim`: ask for up to 10 queued rows. The function picks `status = 'queued'` rows with `for update skip locked`,
   sets `claimed`, `claimed_at`, a `claim_id`, increments `tries`, and returns the jobs. Rows claimed more than 30 minutes
   ago with no result go back to `queued` (the lease expires) and `tries` counts; at 3 tries a row becomes `failed`.
2. Mark each job with the local model (below), twice if the first answer is low confidence.
3. `complete`: post the result with the `claim_id`. The function validates (rules below), stores, sets `marked`.
4. `release` on any error, with a short reason (stored for the owner, no answer text).

**Model:** chosen by the calibration experiment, not by guess. A safety-aligned open model, text only, on GPUs 0 to 2
(not the dedicated GPU 3; the uncensored model is never used). The experiment is in
`/data/alvin/tmp/cookie-codex/oe-calibration/README.md`.

**Input JSON** (one job; no names, no ids that identify the child):

```json
{
  "job_id": 123,
  "claim_id": "uuid",
  "lang": "en",
  "marks_avail": 2,
  "passage": "full passage text",
  "question": "the stem, with (a)/(b) parts",
  "key": "the school's model answer",
  "points": [
    {"id": "p1", "idea": "...", "marks": 1, "accept": ["..."], "reject": ["..."], "context": true},
    {"id": "p2", "idea": "...", "marks": 1, "accept": ["..."], "reject": ["..."], "context": true}
  ],
  "answer": "the child's typed text"
}
```

**Output JSON** (one per job, nothing else; the worker rejects non-JSON and retries once):

```json
{
  "job_id": 123,
  "claim_id": "uuid",
  "marks": 1,
  "points": [
    {"id": "p1", "awarded": true,  "span": "the exact words from the answer that earn it", "why": "short, for the owner"},
    {"id": "p2", "awarded": false, "span": null,  "missing": "what the child left out, in simple words"}
  ],
  "feedback": "One sentence a 12-year-old can read: what was good and what is missing.",
  "confidence": "high"
}
```

**Validation by the Edge Function (the model is never trusted on arithmetic or spans):**

- every `points[].id` is one of the rubric's ids, each exactly once;
- an awarded point's `span` must be a substring of the child's answer after whitespace and punctuation are normalised
  (the same `norm()` idea as `typed.ts`); no span, or a span that is not in the answer, turns the point into not awarded;
- the total `marks` is recomputed as the sum of the awarded points' marks and replaces the model's number;
- `marks` cannot exceed `marks_avail`;
- `feedback` is at most 200 characters and is checked against a small blocklist; for Chinese it must be in Chinese.

**Confidence:** `high`, `medium`, `low`. The worker sets `low` itself if any of these hold: the two runs disagree on the
total, the answer is shorter than 3 characters or longer than the limit, the answer looks like pinyin or random
characters, or the model says it is unsure. A `low` row is stored with its marks, but the child sees **"Ask a grown-up to
check this one"** instead of a mark, and the parent page shows it at the top with the key and the checklist. Low
confidence never produces a retest by itself (see section 6).

**Safety flags:** the model also returns `safety: false|true`. A `true` row is not shown to the child as a mark, and the
parent gets a note with no answer text ("a note to look at"), as the Science marking plan already says.

## 5. How the mark reaches the device (no save schema bump)

The save already holds everything a retest needs (`questions[id]` with `s`, `due`, `w`, `a`). No new save field is added.

1. On load of `/train`, a school page, and the open-answer page, the site calls `oe_results()`: the child's marked rows
   with `applied_at is null`, newest first.
2. For each row the site calls `answer(s, qid, ok, submittedAt, true, picked)` once, where:
   - `ok` = `marks_awarded === marks_avail` (full marks only; below full marks is wrong, owner default 3);
   - `now` is the **submit time**, not the marking time, so the spacing is counted from when the child answered;
   - `picked` is a short text such as `"1 of 2 marks"` (under `PICK_MAX`), so the parent page's "Questions answered wrong"
     list already shows it through the existing `a` field;
   - a `low`-confidence or `safety` row is skipped (not applied) and stays `applied_at is null`.
3. The site then calls `oe_applied(ids)` so the server stops returning the row, and keeps the applied ids in kv
   `oe-applied` so a failed call or an offline tab never applies the same row twice (the call is idempotent by row id).
4. `save()` runs once at the end. Tier clearing follows the existing rule: the question is retired when `s === 0`, and
   `syncTiers` runs on the next quiz page, as it already does after Daily Review.
5. A retest of an open question is the same flow again: the child writes a fresh answer, the mark comes the next day, and
   `answer()` is called with the original submit time; `answer()` already treats an answer to a not-yet-due state as no
   change and to a due state as a step.

The child's "my mark" card on the school page reads straight from `oe_results()` (mark, the one-sentence feedback, and
the checklist with the marker's ticks beside the child's own).

## 6. Parent view and the "disagree" route

**Parent page, "Open answers"** (per child, last 30 days, newest first):

- the question's label (section and "Past paper <year>", no school), the child's answer, the mark or "waiting" or
  "ask a grown-up", the one-sentence feedback, and the days left before the text is deleted;
- the low-confidence rows first, with the key and the checklist so the parent can mark by hand;
- "Delete this answer" (removes the text now; the mark already in the save stays);
- a small summary: how many marked this week and how many came back as retests.

**Disagree:** every marked answer has "I think this mark is wrong" for the child and the parent. It calls
`report_question` (migration 005) with a new `kind = 'mark'`, and the note field carries the answer id. A migration
adds the kind to the check constraint and an optional `answer_id bigint` column. Reports of kind `mark` show in the
admin's open-reports query with the answer, the key, the rubric and the model's result side by side. The owner can:

- correct the mark (the owner's mark replaces the model's: `marks_awarded`, `model = 'owner'`, `applied_at` reset so
  the device re-applies the corrected mark with `answer()`);
- edit the rubric's `accept` or `reject` lines (marking-framework: disagreements become new lines) and bump `version`;
- mark the report resolved.

If an owner correction lifts a mark to full marks after a retest was booked, the device applies the correction as a
normal correct answer; the existing rules never un-clear a tier, so the worst case is a retest the child does not need.

## 7. Privacy notice wording to add

Add to `site/src/pages/privacy/index.astro`, and bump `CONSENT_VERSION` so parents agree again (the "Changes" section
already promises that).

Under "What we keep", a new bullet:

> **Written answers.** When your child types an answer to a reading question, we keep the text, the question it
> answered, and the mark, for 90 days, so a grown-up can read it and so the answer can be marked. Written answers are
> marked by a program that runs on a private computer in our own home; they are not sent to any outside AI service.

Under "Why":

> Written answers are kept only to mark them and to show you what your child wrote. They are not used to train any model
> and are not shared.

Under "Your choices", a bullet:

> **Written answers:** you can read and delete them on the parent page. They are also erased automatically after 90 days.
> If you think a mark is wrong, tell us from the answer and we will correct it.

Under "Who can see it", add: "The operator can read written answers to check the marking and fix mistakes."

Do not mention a model name or the home address in the notice.

## 8. Failure modes

| What goes wrong | What happens |
|---|---|
| Home server off or GPU busy for days | Rows stay queued. The child sees "waiting" with the key and checklist. After 7 unmarked days the parent page offers "Mark it yourself" (key and checklist); the self-mark is stored as `model = 'parent'`. The child is never blocked; the 1/3/7-day retest does not start until a mark exists. |
| Worker crashes mid-claim | The lease (30 min) expires, the row returns to `queued`, `tries` counts; 3 tries make it `failed` and the parent sees it. |
| Model returns garbage JSON or an out-of-rubric id | The worker retries once; then `release`. The Edge Function never stores an invalid result. |
| Model gives full marks without evidence | A point without a span in the answer is not awarded. Total is recomputed server-side. |
| Model is too strict or too lenient overall | Caught by the calibration pass and by the disagreement queue; the owner can switch the section off in a single flag (`oe_rubrics.approved = false`) and the answer page falls back to key plus self-check only (no queue). |
| Answer is empty, pinyin, copy of the passage, or text meant to trick the model | The marker marks only against the rubric and the answer text; "ignore previous instructions" has no points; the prompt tells the model the answer is data. Copying a long run of passage text that does not address the question earns nothing (marking-framework). Very low or odd answers go `low` confidence. |
| A child pastes the key back | The key is shown after submit; a resubmit within the hour never counts towards retiring (section 3). Copying gets full marks once; the retest 1 day later asks again. The owner can see it in the 90-day log. |
| Queue grows faster than the server marks | A cap of 400 open rows; new submits get "try again tomorrow". The owner's counter shows the backlog. |
| Network or sign-in fails at submit | The draft stays in `oe-draft`; Hand in retries; nothing is lost. A 5xx never marks the question answered. |
| Tab or device applies the same result twice | `oe_applied` and the kv `oe-applied` guard make it idempotent. |
| Parent deletes an answer before it is marked | The row is removed, the queue skips it, and no retest is booked. |
| Offensive or distressing text in an answer | `safety` flag: no mark shown to the child; a note (no text) goes to the parent. The text stays only for the 90 days. |
| A section's Chinese passage has OCR errors | The rubric and key are authoritative; the marker is told the passage may contain misread characters. A rubric is `approved` only after a human has read the passage text for that question (build step 2). |
| Retention job fails | Every read function filters on `expires_at > now()`, so a late purge never exposes old text. |

## 9. Build order, with tests

Each step ships on its own and can stop there.

1. **Schema.** A migration with `oe_answers`, `oe_rubrics`, `oe_submit`, `oe_results`, `oe_for_parent`, `oe_applied`,
   `purge_oe`, and the `mark` kind for question reports. Tests (`scripts/accounts/sqltest.sh`, new `test_oe.sql`): a
   child reads only their rows; a parent reads only their own children's rows; one family cannot read another; anon and a
   parent cannot call `oe_submit`; per-day and per-question limits; length limits; an expired row is invisible;
   deleting a child removes rows.
2. **Rubrics and the checklist wording.** A script `scripts/pastpapers/oe_rubrics.py` drafts points and child lines from
   the key (same pipeline as `section_explain.py`), a reviewer reads each passage and approves a sample; no rubric
   without `approved`. Tests: every rubric's marks sum to the question's marks; every point has an idea and wording;
   no child line contains the key's exact sentence; a question with a garbled passage is never `approved`.
3. **Answer page, key and checklist, no marking yet.** The answer box, draft, submit, key and checklist, and "waiting"
   state; the parent "Open answers" list with a "Mark it yourself" button. Tests (`node --test`): draft keeps text over a
   reload, a blank is never sent, IME composition is not counted, character limits, an answer is shown back unchanged,
   and `answer()` is not called at submit. Screenshots on a 360 px phone, with and without the passage sheet open, in
   English and Chinese.
4. **Worker and Edge Function.** `oe-queue` (claim, complete, release) and the worker program. Tests: lease expiry,
   `skip locked` (two workers never get the same row), the three validation rules (span must be in the answer, total
   recomputed, ids exact), a malformed result is rejected, `tries` reaches `failed`. A dry run on the calibration answers
   with the chosen model before anything touches live rows.
5. **Results to the device.** `oe_results` use in `store.ts` callers (a small pure function in a new `oe.ts`, with tests
   like `sync.test.ts`): full marks retire, below full marks retest from the submit time, `low` and `safety` skipped,
   applied twice does nothing, orders of arrival do not matter.
6. **Disagree and owner correction.** `kind = 'mark'` reports, the admin side-by-side view, owner correction that
   re-applies.
7. **Privacy notice and consent version bump**, shipped in the same release as step 3 (the notice must be live before
   any child types an answer).
8. **Turn on one section** (English Comprehension OE) for the Test Player only, then for children when the calibration
   pass is met; Chinese after its own pass.

## Reuse

Science open answers and Math Paper 2 typed steps use the same table, the same worker and the same device flow; only the
rubric shape and the model change (marking-framework: Science points with accept and reject, Math method marks). The
`lang` column becomes a `section` kind when they arrive.

## Open questions for the owner

- Is 3 questions per open session right, or should it be 2?
- Is 12 answers a day per child enough, and is 40 a day per family enough for a family of four?
- Should a parent be able to mark an answer by hand after 7 days of waiting (proposed), or should it stay waiting until
  the server marks it?
- Is the 90-day retention the same for Chinese and English (proposed yes)?
- The calibration result decides the model and whether a second run is needed per answer; this design assumes two runs
  only when the first is low confidence.
