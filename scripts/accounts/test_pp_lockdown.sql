-- Run by sqltest.sh after 007: the bulk read and the readers' bucket access are gone; the per-quiz path still works.
\set QUIET on
create function pg_temp.as_user(p_id uuid) returns void language sql as $$
  select set_config('request.jwt.claims', jsonb_build_object('sub', p_id, 'aal', 'aal1', 'app_metadata', '{}'::jsonb)::text, false) $$;
create function pg_temp.ok(c boolean, what text) returns void language plpgsql as $$
begin if c is not true then raise exception 'FAIL: %', what; end if; raise notice 'ok  %', what; end $$;
grant execute on all functions in schema pg_temp to authenticated;
select pg_temp.ok(to_regprocedure('public.pp_items_for(text, text[])') is null, 'the bulk read pp_items_for is gone');
select pg_temp.ok(not exists (select 1 from pg_policies where tablename = 'objects' and policyname = 'pp_figures_read'), 'the readers'' bucket policy is gone');
set role authenticated;
select pg_temp.as_user('44444444-0000-0000-0000-0000000000c2');
select pg_temp.ok((select count(*) = 0 from storage.objects where bucket_id = 'pp-figures'), 'a child can no longer list the pictures');
select pg_temp.ok((select count(*) > 0 from public.pp_pool('science', array['sci-test-pool'])), 'the per-quiz pool still works');
reset role;
\echo LOCKDOWN CHECKS PASSED
