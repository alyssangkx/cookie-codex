-- Run by sqltest.sh after 012 (and 007): a parent reads only the past-paper items the server served their own child, and
-- only those items' pictures; another parent, the child, anon and the admin without aal2 get nothing. Raises on failure.
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
grant execute on all functions in schema pg_temp to anon, authenticated;

insert into auth.users (id, email) values
  ('66666666-0000-0000-0000-0000000000a1', 'seen-parent-a@x.test'), ('66666666-0000-0000-0000-0000000000a2', 'seen-parent-b@x.test'),
  ('66666666-0000-0000-0000-0000000000c1', 'child-seen1@children.invalid'), ('66666666-0000-0000-0000-0000000000ad', 'seen-admin@x.test');
insert into public.families (parent_id, consent_version) values ('66666666-0000-0000-0000-0000000000a1', 'test'), ('66666666-0000-0000-0000-0000000000a2', 'test');
insert into public.profiles (id, parent_id, name, role) values ('66666666-0000-0000-0000-0000000000c1', '66666666-0000-0000-0000-0000000000a1', 'Seenkid', 'child');
insert into public.pp_items (id, src_id, subject, subtopic, level, stem, options, answer, figures, year, blind_src) values
  ('pp-6600000101', 'seen-1', 'science', 'sci-seen', 'basic', 'served stem', '["a","b","c","d"]', 1, '[{"path":"science/pp-6600000101-1.webp","w":10,"h":10}]', 2025, 'b'),
  ('pp-6600000102', 'seen-2', 'science', 'sci-seen', 'basic', 'never served', '["a","b","c","d"]', 2, '[{"path":"science/pp-6600000102-1.webp","w":10,"h":10}]', 2025, 'b');
insert into private.pp_served (user_id, family, item_id, day) values
  ('66666666-0000-0000-0000-0000000000c1', '66666666-0000-0000-0000-0000000000a1', 'pp-6600000101', private.sg_today());
insert into storage.objects (bucket_id, name) values ('pp-figures', 'science/pp-6600000101-1.webp'), ('pp-figures', 'science/pp-6600000102-1.webp');
-- the parent writes the unserved id into the child's save: it must not unlock anything
insert into public.saves (child_id, data, schema_version) values ('66666666-0000-0000-0000-0000000000c1', '{"questions":{"pp-6600000102":{"s":1,"w":1,"due":0}}}', 4)
  on conflict (child_id) do update set data = excluded.data;

set role authenticated;
select pg_temp.as_user('66666666-0000-0000-0000-0000000000a1');
select pg_temp.ok((select array_agg(id) = array['pp-6600000101'] from public.pp_seen('66666666-0000-0000-0000-0000000000c1')),
  'the parent sees the served item only (an id written into the save unlocks nothing)');
select pg_temp.ok((select answer = 1 and stem = 'served stem' from public.pp_seen('66666666-0000-0000-0000-0000000000c1')), 'with its stem and key');
select pg_temp.ok((select array_agg(name) = array['science/pp-6600000101-1.webp'] from storage.objects where bucket_id = 'pp-figures'),
  'the parent may sign that item''s picture and no other');
select pg_temp.as_user('66666666-0000-0000-0000-0000000000a2');
select pg_temp.fails($$select * from public.pp_seen('66666666-0000-0000-0000-0000000000c1')$$, 'another parent cannot read them');
select pg_temp.ok((select count(*) = 0 from storage.objects where bucket_id = 'pp-figures'), 'another parent sees no pictures');
select pg_temp.as_user('66666666-0000-0000-0000-0000000000c1');
select pg_temp.fails($$select * from public.pp_seen('66666666-0000-0000-0000-0000000000c1')$$, 'the child cannot read them here');
select pg_temp.as_user('66666666-0000-0000-0000-0000000000ad', 'admin', 'aal1');
select pg_temp.fails($$select * from public.pp_seen('66666666-0000-0000-0000-0000000000c1')$$, 'the admin without the authenticator code cannot');
select pg_temp.as_user('66666666-0000-0000-0000-0000000000ad', 'admin', 'aal2');
select pg_temp.ok((select count(*) = 1 from public.pp_seen('66666666-0000-0000-0000-0000000000c1')), 'the admin at aal2 can');
reset role;
set role anon;
select pg_temp.as_user(null);
select pg_temp.fails($$select * from public.pp_seen('66666666-0000-0000-0000-0000000000c1')$$, 'anon cannot call it');
reset role;
\echo SEEN CHECKS PASSED
