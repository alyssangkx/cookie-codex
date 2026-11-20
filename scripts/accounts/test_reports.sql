-- Run by sqltest.sh after test_pp_items.sql: the 005 rules (question reports written only through report_question by a
-- signed-in child, the Test Player or the admin; never by a parent or anon; nobody reads the table but the service role).
\set QUIET on
create function pg_temp.as_user(p_id uuid, p_role text default null) returns void language sql as $$
  select set_config('request.jwt.claims', case when p_id is null then '' else jsonb_build_object('sub', p_id, 'aal', 'aal1',
    'app_metadata', case when p_role is null then '{}'::jsonb else jsonb_build_object('role', p_role) end)::text end, false) $$;
create function pg_temp.ok(c boolean, what text) returns void language plpgsql as $$
begin if c is not true then raise exception 'FAIL: %', what; end if; raise notice 'ok  %', what; end $$;
create function pg_temp.fails(q text, what text) returns void language plpgsql as $$
begin
  begin execute q; exception when others then raise notice 'ok  % (%)', what, sqlerrm; return; end;
  raise exception 'FAIL: % (no error)', what;
end $$;
grant execute on all functions in schema pg_temp to anon, authenticated;

insert into auth.users (id, email) values
  ('33333333-0000-0000-0000-0000000000a1', 'rq-parent@x.test'),
  ('33333333-0000-0000-0000-0000000000c1', 'child-rq1@children.invalid');
insert into public.families (parent_id, consent_version) values ('33333333-0000-0000-0000-0000000000a1', 'test');
insert into public.profiles (id, parent_id, name, role) values
  ('33333333-0000-0000-0000-0000000000c1', '33333333-0000-0000-0000-0000000000a1', 'Rqkid', 'child');

set role authenticated;
select pg_temp.as_user('33333333-0000-0000-0000-0000000000c1');
select public.report_question('pp-3f46ebd0cf', 'picture', '  only three answers  ');
select public.report_question('pp-3f46ebd0cf', 'answer', '');
select public.report_question('scisys-0123456789', 'question');
select pg_temp.fails($$select count(*) from public.question_reports$$, 'a child cannot read the reports table');
select pg_temp.fails($$insert into public.question_reports (qid, reporter, kind) values ('x-1', auth.uid(), 'other')$$, 'a child cannot insert directly');
select pg_temp.fails($$select public.report_question('pp-1', 'rude', null)$$, 'an unknown kind is refused');
select pg_temp.fails($$select public.report_question('PP;drop', 'other', null)$$, 'a malformed question id is refused');
select pg_temp.fails($$select public.report_question('pp-1', 'other', repeat('x', 301))$$, 'a note over 300 characters is refused');
select pg_temp.as_user('33333333-0000-0000-0000-0000000000a1');
select pg_temp.fails($$select public.report_question('pp-1', 'other', null)$$, 'a parent is refused');
select pg_temp.as_user('00000000-0000-0000-0000-000000000003');
select public.report_question('pp-3f46ebd0cf', 'other', null);
select pg_temp.as_user('00000000-0000-0000-0000-0000000000ad', 'admin');
select public.report_question('pp-3f46ebd0cf', 'other', 'admin check');
reset role;
set role anon;
select pg_temp.as_user(null);
select pg_temp.fails($$select public.report_question('pp-1', 'other', null)$$, 'anon is refused');
reset role;

select pg_temp.ok((select count(*) = 2 from public.question_reports where reporter = '33333333-0000-0000-0000-0000000000c1'),
                  'a second report of the same question replaces the first');
select pg_temp.ok((select kind = 'answer' and note is null from public.question_reports
                    where reporter = '33333333-0000-0000-0000-0000000000c1' and qid = 'pp-3f46ebd0cf'), 'the latest report wins; a blank note is stored as null');
select pg_temp.ok((select count(*) = 4 from public.question_reports), 'the Test Player and the admin may report');

update private.rate_hits set n = 30, window_start = now() where key = 'rq:33333333-0000-0000-0000-0000000000c1';
set role authenticated;
select pg_temp.as_user('33333333-0000-0000-0000-0000000000c1');
select pg_temp.fails($$select public.report_question('pp-2', 'other', null)$$, 'over 30 reports a day refused');
reset role;

delete from auth.users where id = '33333333-0000-0000-0000-0000000000c1';
select pg_temp.ok((select count(*) = 2 from public.question_reports), 'a deleted account takes its reports with it');
\echo REPORT CHECKS PASSED
