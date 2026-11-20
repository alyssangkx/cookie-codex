-- Run by sqltest.sh after test_accounts.sql: the 004 rules (past-paper items readable only through pp_items_for by a
-- signed-in child, parent or admin; never by anon; figures bucket private). Every check raises on failure.
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
create function pg_temp.n(p_sub text) returns int language sql as $$
  select count(*)::int from public.pp_items_for('science', array[p_sub]) $$;
grant execute on all functions in schema pg_temp to anon, authenticated;

-- fixtures (as the service role / loader would write them): placeholder text only
insert into auth.users (id, email) values
  ('22222222-0000-0000-0000-0000000000a1', 'pp-parent@x.test'),
  ('22222222-0000-0000-0000-0000000000a2', 'pp-stranger@x.test'),
  ('22222222-0000-0000-0000-0000000000c1', 'child-pp1@children.invalid'),
  ('22222222-0000-0000-0000-0000000000c2', 'child-pp2@children.invalid');
insert into public.families (parent_id, consent_version) values ('22222222-0000-0000-0000-0000000000a1', 'test');
insert into public.profiles (id, parent_id, name, role) values
  ('22222222-0000-0000-0000-0000000000c1', '22222222-0000-0000-0000-0000000000a1', 'Ppkid', 'child'),
  ('22222222-0000-0000-0000-0000000000c2', '22222222-0000-0000-0000-0000000000a1', 'Ppgone', 'child');
update public.profiles set deleted_at = now() where id = '22222222-0000-0000-0000-0000000000c2';
insert into public.pp_items (id, src_id, subject, subtopic, level, stem, options, answer, figures, year, blind_src, active) values
  ('pp-0000000001', 's1', 'science', 'sci-systems-plant-transport-parts', 'basic', 'placeholder stem', '["a","b","c","d"]', 0,
   '[{"path":"science/pp-0000000001-1.webp","w":900,"h":400}]', 2025, 'vl-pages', true),
  ('pp-0000000002', 's2', 'science', 'sci-systems-plant-transport-parts', 'basic', 'placeholder stem', '["a","b","c","d"]', 1, '[]', 2025, 'text', false),
  ('pp-0000000003', 's3', 'science', 'sci-systems-circuit', 'basic', 'placeholder stem', '["a","b","c","d"]', 2, '[]', 2025, 'text', true);
select pg_temp.fails($$insert into public.pp_items (id, src_id, subject, subtopic, level, stem, options, answer, blind_src)
  values ('pp-0000000009', 's9', 'science', 'sci-x', 'basic', 'x', '["a","b","c"]', 0, 't')$$, 'a row needs exactly 4 options');
select pg_temp.fails($$insert into public.pp_items (id, src_id, subject, subtopic, level, stem, options, answer, blind_src)
  values ('pp-0000000009', 's9', 'science', 'sci-x', 'basic', 'x', '["a","b","c","d"]', 4, 't')$$, 'answer is 0-3');
insert into storage.objects (bucket_id, name) values ('pp-figures', 'science/pp-0000000001-1.webp');
select pg_temp.ok((select not public from storage.buckets where id = 'pp-figures'), 'figures bucket is private');

-- anon: nothing
set role anon;
select pg_temp.as_user(null);
select pg_temp.fails($$select pg_temp.n('sci-systems-plant-transport-parts')$$, 'anon cannot call pp_items_for');
select pg_temp.fails($$select count(*) from public.pp_items$$, 'anon cannot select pp_items');
select pg_temp.ok((select count(*) = 0 from storage.objects where bucket_id = 'pp-figures'), 'anon sees no figure objects');
reset role;

set role authenticated;
-- a signed-in user without a profile or family (e.g. an unconfirmed sign-up): refused
select pg_temp.as_user('22222222-0000-0000-0000-0000000000a2');
select pg_temp.fails($$select pg_temp.n('sci-systems-plant-transport-parts')$$, 'a stranger account is refused');
select pg_temp.ok((select count(*) = 0 from storage.objects where bucket_id = 'pp-figures'), 'a stranger sees no figure objects');
-- the child
select pg_temp.as_user('22222222-0000-0000-0000-0000000000c1');
select pg_temp.fails($$select count(*) from public.pp_items$$, 'a child cannot select the table directly');
select pg_temp.ok(pg_temp.n('sci-systems-plant-transport-parts') = 1, 'a child gets the active items of the asked sub-topic only');
select pg_temp.ok((select count(*) = 2 from public.pp_items_for('science', array['sci-systems-plant-transport-parts', 'sci-systems-circuit'])), 'several sub-topics in one call');
select pg_temp.ok((select count(*) = 0 from public.pp_items_for('maths', array['sci-systems-circuit'])), 'subject must match');
select pg_temp.ok((select count(*) = 1 from storage.objects where bucket_id = 'pp-figures'), 'a child may sign figure URLs');
select pg_temp.fails($$select count(*) from public.pp_items_for('science', array[]::text[])$$, 'empty sub-topic list refused');
select pg_temp.fails($$select count(*) from public.pp_items_for('science', array(select 'sci-' || g from generate_series(1, 41) g))$$, 'over 40 sub-topics refused');
select pg_temp.fails($$insert into storage.objects (bucket_id, name) values ('pp-figures', 'science/x.webp')$$, 'a child cannot upload figures');
-- a deleted child
select pg_temp.as_user('22222222-0000-0000-0000-0000000000c2');
select pg_temp.fails($$select pg_temp.n('sci-systems-plant-transport-parts')$$, 'a deleted child is refused');
-- the parent and the admin
select pg_temp.as_user('22222222-0000-0000-0000-0000000000a1');
select pg_temp.ok(pg_temp.n('sci-systems-plant-transport-parts') = 1, 'a parent with a live family may read');
select pg_temp.as_user('00000000-0000-0000-0000-0000000000ad', 'admin');
select pg_temp.ok(pg_temp.n('sci-systems-circuit') = 1, 'the admin may read');
-- the Test Player (role test, the admin's)
select pg_temp.as_user('00000000-0000-0000-0000-000000000003');
select pg_temp.ok(pg_temp.n('sci-systems-circuit') = 1, 'the Test Player may read');
reset role;

-- rate limit: the 121st call in an hour is refused
update private.rate_hits set n = 120, window_start = now() where key = 'pp:00000000-0000-0000-0000-000000000003';
set role authenticated;
select pg_temp.as_user('00000000-0000-0000-0000-000000000003');
select pg_temp.fails($$select pg_temp.n('sci-systems-circuit')$$, 'over 120 calls an hour refused');
reset role;
-- a parent's deleted family closes access
update public.families set deleted_at = now() where parent_id = '22222222-0000-0000-0000-0000000000a1';
set role authenticated;
select pg_temp.as_user('22222222-0000-0000-0000-0000000000c1');
select pg_temp.fails($$select pg_temp.n('sci-systems-plant-transport-parts')$$, 'a child of a deleted family is refused');
reset role;
\echo PP CHECKS PASSED
