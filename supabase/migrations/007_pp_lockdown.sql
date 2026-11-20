-- Cookie Codex, migration 007: remove the bulk past-paper read paths (ADR 0012).  NOT YET APPLIED.
-- Apply ONLY after the site that uses pp_pool + the pp-serve function is live (the old site reads through pp_items_for).
-- Apply with:  supabase db query --remote --yes -f supabase/migrations/007_pp_lockdown.sql   (never `db push`).
-- Test: scripts/accounts/sqltest.sh applies it after the 004-006 checks and runs test_pp_lockdown.sql.
--   * public.pp_items_for: up to 4,000 questions for 40 sub-topics in one call. Gone; pp_pool lists ids only and
--     pp_serve gives at most 15 questions a call under daily limits.
--   * storage policy pp_figures_read: let every reader list and download every picture. Gone; only the pp-serve function
--     (service role) signs 10-minute URLs, for the questions it serves.

begin;
drop function public.pp_items_for(text, text[]);
drop policy pp_figures_read on storage.objects;
commit;
