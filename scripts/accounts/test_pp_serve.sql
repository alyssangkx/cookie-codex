-- Run by sqltest.sh after test_reports.sql: the 006 rules (past-paper questions served per quiz: ids-only pool, at most 15
-- per content call, daily limits per account and family, a log, flags, the admin report). Every check raises on failure.
\set QUIET on
create function pg_temp.as_user(p_id uuid, p_role text default null, p_aal text default 'aal1') returns void language sql as $$
  select set_config('request.jwt.claims', case when p_id is null then '' else jsonb_build_object('sub', p_id, 'aal', p_aal,
    'app_metadata', case when p_role is null then '{}'::jsonb else jsonb_build_object('role', p_role) end)::text end, false) $$;
create function pg_temp.ok(c boolean, what text) returns void language plpgsql as $$
begin if c is not true then raise exception 'FAIL: %', what; end if; raise notice 'ok  %', what; end $$;
create function pg_temp.fails(q text, what text) returns void language plpgsql as $$
begin
  begin execute q; exception when others then raise notice 'ok  % (%)', what, sqlerrm; return; end;
  raise exception 'FAIL: % (no error)', what;
end $$;
create function pg_temp.ids(a int, b int) returns text[] language sql as $$
  select array_agg('pp-44' || lpad(g::text, 8, '0') order by g) from generate_series(a, b) g $$;
-- served-log padding: n made-up ids for a user today (a log row needs no matching item)
create function pg_temp.pad(p_uid uuid, p_family uuid, p_tag text, n int) returns void language sql as $$
  insert into private.pp_served (user_id, family, item_id, day)
  select p_uid, p_family, 'pp-' || p_tag || lpad(g::text, 6, '0'), private.sg_today() from generate_series(1, n) g $$;
grant execute on all functions in schema pg_temp to anon, authenticated;

insert into auth.users (id, email) values
  ('44444444-0000-0000-0000-0000000000a1', 'pps-parent-a@x.test'), ('44444444-0000-0000-0000-0000000000a2', 'pps-parent-b@x.test'),
  ('44444444-0000-0000-0000-0000000000c1', 'child-pps1@children.invalid'), ('44444444-0000-0000-0000-0000000000c2', 'child-pps2@children.invalid'),
  ('44444444-0000-0000-0000-0000000000c3', 'child-pps3@children.invalid'), ('44444444-0000-0000-0000-0000000000c4', 'child-pps4@children.invalid');
insert into public.families (parent_id, consent_version) values ('44444444-0000-0000-0000-0000000000a1', 'test'), ('44444444-0000-0000-0000-0000000000a2', 'test');
insert into public.profiles (id, parent_id, name, role) values
  ('44444444-0000-0000-0000-0000000000c1', '44444444-0000-0000-0000-0000000000a1', 'Ppsnew', 'child'),
  ('44444444-0000-0000-0000-0000000000c2', '44444444-0000-0000-0000-0000000000a1', 'Ppsold', 'child'),
  ('44444444-0000-0000-0000-0000000000c3', '44444444-0000-0000-0000-0000000000a2', 'Ppsfama', 'child'),
  ('44444444-0000-0000-0000-0000000000c4', '44444444-0000-0000-0000-0000000000a2', 'Ppsfamb', 'child');
update public.profiles set created_at = now() - interval '30 days'
 where id in ('44444444-0000-0000-0000-0000000000c2', '44444444-0000-0000-0000-0000000000c3', '44444444-0000-0000-0000-0000000000c4');
insert into public.pp_items (id, src_id, subject, subtopic, level, stem, options, answer, year, blind_src, ord)
select 'pp-44' || lpad(g::text, 8, '0'), 'pps-src-' || g, 'science', 'sci-test-pool', 'basic', 'placeholder stem ' || g,
       '["a","b","c","d"]', 0, 2025, 'vl-pages', 31 - g from generate_series(1, 30) g;
update public.pp_items set active = false where id = 'pp-4400000030';

set role authenticated;
-- the pool: ids and rank only, active items, easier (lower ord) first
select pg_temp.as_user('44444444-0000-0000-0000-0000000000c1');
select pg_temp.ok((select count(*) = 29 from public.pp_pool('science', array['sci-test-pool'])), 'pool lists the active items of the sub-topic');
select pg_temp.ok((select id = 'pp-4400000029' from public.pp_pool('science', array['sci-test-pool']) limit 1), 'pool is easier-first (lowest ord first)');
select pg_temp.ok((select level = 'basic' and subtopic = 'sci-test-pool' from public.pp_pool('science', array['sci-test-pool']) limit 1), 'pool gives sub-topic and level, for tier-mode merges');
select pg_temp.fails($$select count(*) from public.pp_pool('science', array[]::text[])$$, 'an empty sub-topic list refused');
select pg_temp.fails($$select public.pp_serve(pg_temp.ids(1, 16))$$, 'more than 15 ids in one call refused');
select pg_temp.fails($$select public.pp_serve(array['pp-xyz'])$$, 'a malformed id refused');
select pg_temp.fails($$select public.pp_serve(array[]::text[])$$, 'an empty call refused');
select pg_temp.ok((select public.pp_serve(pg_temp.ids(1, 10)) ->> 'status' = 'ok'), 'a child is served 10 questions');
select pg_temp.ok((select jsonb_array_length(public.pp_serve(pg_temp.ids(1, 10)) -> 'items') = 10), 'the same 10 again the same day');
select pg_temp.ok((select jsonb_array_length(public.pp_serve(array['pp-4400000030']) -> 'items') = 0), 'an inactive item is not served');
reset role;
select pg_temp.ok((select count(*) = 11 from private.pp_served where user_id = '44444444-0000-0000-0000-0000000000c1'),
                  'each question is logged once a day (repeats cost nothing)');

-- a new account (first 7 days): 125 a day
select pg_temp.pad('44444444-0000-0000-0000-0000000000c1', '44444444-0000-0000-0000-0000000000a1', 'aa', 110);
set role authenticated;
select pg_temp.as_user('44444444-0000-0000-0000-0000000000c1');
select pg_temp.ok((select public.pp_serve(pg_temp.ids(11, 15)) ->> 'status' = 'limit'), 'a new account is stopped past 125 a day');
reset role;
select pg_temp.ok((select count(*) = 121 from private.pp_served where user_id = '44444444-0000-0000-0000-0000000000c1'), 'a refused call serves and logs nothing');
select pg_temp.ok((select reason = 'account daily limit 125' from private.pp_flags where user_id = '44444444-0000-0000-0000-0000000000c1'), 'the account is flagged');

-- an older account: 250 a day
select pg_temp.pad('44444444-0000-0000-0000-0000000000c2', '44444444-0000-0000-0000-0000000000a1', 'bb', 245);
set role authenticated;
select pg_temp.as_user('44444444-0000-0000-0000-0000000000c2');
select pg_temp.ok((select public.pp_serve(pg_temp.ids(11, 15)) ->> 'status' = 'ok'), 'an older account may reach 250');
select pg_temp.ok((select public.pp_serve(pg_temp.ids(16, 16)) ->> 'status' = 'limit'), 'and is stopped at 251');
reset role;

-- a family: 400 distinct a day across the parent's children
select pg_temp.pad('44444444-0000-0000-0000-0000000000c3', '44444444-0000-0000-0000-0000000000a2', 'cc', 200);
select pg_temp.pad('44444444-0000-0000-0000-0000000000c4', '44444444-0000-0000-0000-0000000000a2', 'dd', 195);
set role authenticated;
select pg_temp.as_user('44444444-0000-0000-0000-0000000000c4');
select pg_temp.ok((select public.pp_serve(pg_temp.ids(1, 10)) ->> 'status' = 'limit'), 'a second child cannot multiply the quota (family 400)');
reset role;
select pg_temp.ok((select reason = 'family daily limit 400' from private.pp_flags where user_id = '44444444-0000-0000-0000-0000000000c4'), 'flagged as a family limit');
set role authenticated;
select pg_temp.as_user('44444444-0000-0000-0000-0000000000c4');
select pg_temp.ok((select public.pp_serve(pg_temp.ids(1, 5)) ->> 'status' = 'ok'), 'up to the family limit is still served');
reset role;

-- the hourly cap
update private.rate_hits set n = 40, window_start = now() where key = 'pps:44444444-0000-0000-0000-0000000000c3';
insert into private.rate_hits (key, n, window_start) values ('pps:44444444-0000-0000-0000-0000000000c3', 40, now()) on conflict (key) do update set n = 40, window_start = now();
set role authenticated;
select pg_temp.as_user('44444444-0000-0000-0000-0000000000c3');
select pg_temp.fails($$select public.pp_serve(pg_temp.ids(1, 1))$$, 'over 40 calls an hour refused');

-- who may not read: a parent, anon
select pg_temp.as_user('44444444-0000-0000-0000-0000000000a1');
select pg_temp.fails($$select count(*) from public.pp_pool('science', array['sci-test-pool'])$$, 'a parent may not list the pool');
select pg_temp.fails($$select public.pp_serve(pg_temp.ids(1, 1))$$, 'a parent may not be served');
reset role;
set role anon;
select pg_temp.as_user(null);
select pg_temp.fails($$select public.pp_serve(array['pp-4400000001'])$$, 'anon may not be served');
reset role;

-- the admin: higher limits, and the report only at aal2
select pg_temp.pad('00000000-0000-0000-0000-0000000000ad', null, 'ee', 300);
set role authenticated;
select pg_temp.as_user('00000000-0000-0000-0000-0000000000ad', 'admin');
select pg_temp.ok((select public.pp_serve(pg_temp.ids(1, 15)) ->> 'status' = 'ok'), 'the admin is not held to 250');
select pg_temp.fails($$select public.pp_usage_report()$$, 'the report needs aal2');
select pg_temp.as_user('00000000-0000-0000-0000-0000000000ad', 'admin', 'aal2');
select pg_temp.ok((select jsonb_array_length(public.pp_usage_report() -> 'flags') = 3), 'the admin report lists today''s flags');
select pg_temp.ok((select (public.pp_usage_report() -> 'top' -> 0 ->> 'n')::int >= 300), 'the admin report lists the top accounts');
select pg_temp.as_user('44444444-0000-0000-0000-0000000000c2');
select pg_temp.fails($$select public.pp_usage_report()$$, 'a child may not read the report');
select pg_temp.fails($$select * from public.pp_flag_take('44444444-0000-0000-0000-0000000000c1')$$, 'only the service role takes flags');
select pg_temp.fails($$select count(*) from private.pp_served$$, 'nobody reads the log directly');
reset role;
select pg_temp.ok((select count(*) = 1 from public.pp_flag_take('44444444-0000-0000-0000-0000000000c1')), 'a flag is taken once for the email');
select pg_temp.ok((select count(*) = 0 from public.pp_flag_take('44444444-0000-0000-0000-0000000000c1')), 'and not again');
\echo PP SERVE CHECKS PASSED
