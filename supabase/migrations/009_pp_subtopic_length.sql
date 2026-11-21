-- 009: past-paper sub-topic ids up to 120 characters (NOT applied yet).
-- Apply with:  supabase db query --remote --yes -f supabase/migrations/009_pp_subtopic_length.sql   (never `db push`).
-- The Maths syllabus has a 103-character sub-topic id (math-data-representation-and-interpretation-picture-graphs-bar-
-- graphs-tables-line-graphs-and-pie-charts); 004 allowed 80, so the Maths upload's row batch was refused and nothing was
-- written (21 Nov 2026). Only the length changes; the character set and every other column stay as they are.
begin;
alter table public.pp_items drop constraint pp_items_subtopic_check;
alter table public.pp_items add constraint pp_items_subtopic_check check (subtopic ~ '^[a-z0-9-]{3,120}$');
commit;
