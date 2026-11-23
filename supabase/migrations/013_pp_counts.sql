-- Cookie Codex, migration 013: live past-paper counts for the parent page (owner, 23 Nov 2026: "each reload updates the
-- pie chart with the current number of questions"). NOT YET APPLIED: needs the owner's OK.
-- Apply with:  supabase db query --remote --yes -f supabase/migrations/013_pp_counts.sql   (never `db push`).
-- Test: scripts/accounts/sqltest.sh applies it after 012 and runs test_pp_counts.sql.
--
-- Numbers only: how many active past-paper questions each sub-topic and level has. The same numbers already ship in the
-- static build (site/src/data/pp_counts.json, written at each upload); this reads them live, so the page no longer waits for
-- a deploy. No id, text, key or picture leaves the table (the lockdown of migration 007 is unchanged).

begin;

create function public.pp_counts()
returns table (subject text, subtopic text, level text, n int)
language sql stable security definer set search_path = '' as $$
  select i.subject, i.subtopic, i.level, count(*)::int from public.pp_items i where i.active group by i.subject, i.subtopic, i.level
$$;
revoke execute on function public.pp_counts() from public, anon;
grant execute on function public.pp_counts() to authenticated;

commit;
