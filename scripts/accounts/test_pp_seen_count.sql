-- Run by sqltest.sh after 016: every question counts as seen once unless the upload says more, the count is bounded, and
-- pp_serve and pp_seen return it. Raises on failure.
\set QUIET on
create function pg_temp.ok(c boolean, what text) returns void language plpgsql as $$
begin if c is not true then raise exception 'FAIL: %', what; end if; raise notice 'ok  %', what; end $$;
create function pg_temp.fails(q text, what text) returns void language plpgsql as $$
begin
  begin execute q; exception when others then raise notice 'ok  % (%)', what, sqlerrm; return; end;
  raise exception 'FAIL: % (no error)', what;
end $$;
grant execute on all functions in schema pg_temp to anon, authenticated;

select pg_temp.ok((select bool_and(seen = 1) from public.pp_items), 'every earlier row counts as seen once');
update public.pp_items set seen = 4 where id = 'pp-7700000001';
select pg_temp.fails($$update public.pp_items set seen = 0 where id = 'pp-7700000001'$$, 'seen is at least 1');
select set_config('request.jwt.claims', jsonb_build_object('sub', '77777777-0000-0000-0000-0000000000c1', 'aal', 'aal1', 'app_metadata', '{}'::jsonb)::text, false);
set role authenticated;
select pg_temp.ok((select (public.pp_serve(array['pp-7700000001'])->'items') @> '[{"id":"pp-7700000001","seen":4}]'), 'pp_serve sends the count');
reset role;
select set_config('request.jwt.claims', jsonb_build_object('sub', '77777777-0000-0000-0000-0000000000a1', 'aal', 'aal1')::text, false);
set role authenticated;
select pg_temp.ok((select seen = 4 from public.pp_seen('77777777-0000-0000-0000-0000000000c1') where id = 'pp-7700000001'), 'pp_seen sends it too');
reset role;
\echo SEENCOUNT CHECKS PASSED
