# Past-paper questions: served per quiz, with daily limits, a log and alerts (anti-scraping)

Status: **accepted** · Date: 2026-11-21 · Source: owner, chat 21 Nov 2026 · Builds on ADR 0004 (past papers stay private)

**Context.** Past-paper questions are served only to signed-in children and the admin (migration 004). But sign-up is
open (a stranger can register as a parent, create a child and log in as it), one `pp_items_for` call returns up to 4,000
questions for up to 40 sub-topics at 120 calls an hour, and readers may list and download every object in the
`pp-figures` bucket. One account could copy the whole collection in minutes. The owner wants the questions behind a login
AND protected from scraping and mass download, in place before the bulk upload.

**Decision.**
- Two read steps: a pool call returns question ids and their easier-first order only (no text); a content call returns
  the text and short-lived (10 min) figure links for at most 15 ids, enough for one quiz. The bulk read is removed.
- Figures only through the server: readers can no longer list or read the bucket directly; the content call signs URLs
  for exactly the questions it serves.
- Limits per account: 250 different past-paper questions a day and 40 content calls an hour; half for the account's first
  7 days; higher for the admin and the Test Player. The day's quota also counts per parent (family), so extra child
  accounts do not multiply it.
- Every served question is logged per account and day. Hitting a limit blocks past-paper content for the rest of the day
  and flags the account. The admin page shows a "Heavy use" report (top accounts, flagged ones, per family), and the
  admin is emailed when an account is flagged.

**Consequences.** The quiz page needs the content call before showing a past-paper question (one extra round trip per
quiz). A child never reaches the limits in normal use (the 2-hour daily cap allows about 150 questions). The email alert
needs a function secret for the site's Gmail sender, which the owner sets in their own terminal. Built together with the
one-pool redesign (ADR 0011) and switched on with the Science upload.
