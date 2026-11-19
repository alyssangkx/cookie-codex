-- Run by sqltest.sh after stub + 001 + seed + 002. Every check raises on failure (psql ON_ERROR_STOP).
\set QUIET on
create function pg_temp.as_user(p_id uuid, p_role text default null, p_aal text default 'aal1') returns void language sql as $$
  select set_config('request.jwt.claims', jsonb_build_object('sub', p_id, 'aal', p_aal,
    'app_metadata', case when p_role is null then '{}'::jsonb else jsonb_build_object('role', p_role) end)::text, false) $$;
create function pg_temp.ok(c boolean, what text) returns void language plpgsql as $$
begin if c is not true then raise exception 'FAIL: %', what; end if; raise notice 'ok  %', what; end $$;
create function pg_temp.fails(q text, what text) returns void language plpgsql as $$
begin
  begin execute q; exception when others then raise notice 'ok  % (%)', what, sqlerrm; return; end;
  raise exception 'FAIL: % (no error)', what;
end $$;
-- a child profile with its own auth user (profiles.id references auth.users), as parent-api creates it
create function pg_temp.kid(p_parent uuid, p_name text, p_role text default 'child') returns uuid language plpgsql as $$
declare v uuid := gen_random_uuid();
begin
  insert into auth.users (id, email) values (v, 'child-' || v || '@children.invalid');
  insert into profiles (id, parent_id, name, role) values (v, p_parent, p_name, p_role);
  return v;
end $$;
grant execute on all functions in schema pg_temp to authenticated;

-- ---------------------------------------------------------------- backfill
select pg_temp.ok((select count(*) = 1 from families f join auth.users u on u.id = f.parent_id where u.email = 'admin@x.test'
                   and f.consent_version = 'owner'), 'admin family backfilled');
select pg_temp.ok(not exists (select 1 from information_schema.columns where table_name = 'families' and column_name = 'code'), 'family code column gone (003)');
select pg_temp.ok((select count(*) = 0 from private.pin_attempts where key ~ '^(name|trust):[0-9a-f-]{36}:'), 'family-scoped lock rows removed (003)');
select pg_temp.ok((select unlimited from profiles where name = 'Admin'), 'Admin player unlimited');
select pg_temp.ok((select unlimited from profiles where role = 'test'), 'Test Player unlimited');
select pg_temp.ok((select not unlimited from profiles where name = 'Alyssa'), 'Alyssa not unlimited');

-- ---------------------------------------------------------------- two families (as the service role would)
insert into auth.users (id, email, email_confirmed_at, raw_app_meta_data) values
  ('11111111-1111-1111-1111-111111111111', 'p1@x.test', now(), '{"role":"parent"}'),
  ('22222222-2222-2222-2222-222222222222', 'p2@x.test', now(), '{"role":"parent"}'),
  ('a1111111-1111-1111-1111-111111111111', 'child-a1@children.invalid', now(), '{}'),
  ('b2222222-2222-2222-2222-222222222222', 'child-b2@children.invalid', now(), '{}');
insert into families (parent_id, consent_version) values
  ('11111111-1111-1111-1111-111111111111', '1'), ('22222222-2222-2222-2222-222222222222', '1');
insert into profiles (id, parent_id, name) values
  ('a1111111-1111-1111-1111-111111111111', '11111111-1111-1111-1111-111111111111', 'Emma'),
  ('b2222222-2222-2222-2222-222222222222', '22222222-2222-2222-2222-222222222222', 'Emma2');
select pg_temp.ok(true, 'username with a digit allowed');
select pg_temp.fails($$select pg_temp.kid('22222222-2222-2222-2222-222222222222', 'EMMA')$$, 'a username taken in another family is refused (site-wide)');
select pg_temp.fails($$select pg_temp.kid('22222222-2222-2222-2222-222222222222', '2Emma')$$, 'a username must start with a letter');
select pg_temp.fails($$select pg_temp.kid('11111111-1111-1111-1111-111111111111', 'emma')$$, 'same name twice in one family refused');
select pg_temp.fails($$select pg_temp.kid('11111111-1111-1111-1111-111111111111', 'Admin')$$, 'name Admin reserved for a parent');
select pg_temp.fails($$select pg_temp.kid('11111111-1111-1111-1111-111111111111', 'Tess', 'test')$$, 'test profile refused for a parent');
select pg_temp.fails($$update profiles set unlimited = true where id = 'a1111111-1111-1111-1111-111111111111'$$, 'unlimited refused for a parent''s child');
do $$ begin
  for i in 1..5 loop
    perform pg_temp.kid('11111111-1111-1111-1111-111111111111', 'Kid ' || chr(64 + i));
  end loop; end $$;
select pg_temp.fails($$select pg_temp.kid('11111111-1111-1111-1111-111111111111', 'Seventh')$$, 'seventh child refused');
delete from auth.users where id in (select id from profiles where name like 'Kid %');
select pg_temp.ok((select count(*) = 1 from profiles where parent_id = '11111111-1111-1111-1111-111111111111'), 'six-child test cleaned up');
-- a deleted child does not count toward the six
update profiles set deleted_at = now() where id = 'a1111111-1111-1111-1111-111111111111';
do $$ begin for i in 1..6 loop perform pg_temp.kid('11111111-1111-1111-1111-111111111111', 'Kid ' || chr(64 + i)); end loop; end $$;
select pg_temp.ok(true, 'six active children allowed beside a deleted one');
delete from auth.users where id in (select id from profiles where name like 'Kid %');
update profiles set deleted_at = null where id = 'a1111111-1111-1111-1111-111111111111';

-- ---------------------------------------------------------------- RLS as parent 1
set role authenticated;
select pg_temp.as_user('11111111-1111-1111-1111-111111111111', 'parent');
select pg_temp.ok((select count(*) = 1 and bool_and(parent_id = '11111111-1111-1111-1111-111111111111') from families), 'parent sees only their family row');
select pg_temp.ok((select count(*) = 1 from profiles), 'parent sees only their own child');
select pg_temp.ok((select array_agg(s.status) = '{ok}' from push_save('a1111111-1111-1111-1111-111111111111', '{"schemaVersion":4}', 4) s), 'parent push to own child ok');
select pg_temp.ok((select array_agg(s.status) = '{denied}' from push_save('b2222222-2222-2222-2222-222222222222', '{"schemaVersion":4}', 4) s), 'parent push to other family denied');
select pg_temp.ok((select count(*) = 1 from saves), 'parent reads only own child''s save');
update saves set data = '{"x":1}' where child_id = 'b2222222-2222-2222-2222-222222222222';
delete from profiles where id = 'b2222222-2222-2222-2222-222222222222';
select pg_temp.fails($$select pin_hash from profiles$$, 'pin_hash not readable');
select pg_temp.fails($$update families set consent_version = 'x'$$, 'family row not client-writable');
select pg_temp.fails($$select pin_clear_name_lock('b2222222-2222-2222-2222-222222222222')$$, 'cannot clear another family''s lock');
select pin_clear_name_lock('a1111111-1111-1111-1111-111111111111');
select pg_temp.ok(true, 'can clear own child''s lock');
select pg_temp.fails($$select rate_hit('x', 1, '1 hour')$$, 'rate_hit not callable by clients');
reset role;
select pg_temp.ok((select count(*) = 1 from profiles where id = 'b2222222-2222-2222-2222-222222222222'), 'other family''s child untouched');
insert into private.pin_attempts (key) values ('name:emma'), ('trust:emma'), ('name:emma2');
set role authenticated;
select pg_temp.as_user('11111111-1111-1111-1111-111111111111', 'parent');
select pin_clear_name_lock('a1111111-1111-1111-1111-111111111111');
reset role;
select pg_temp.ok((select count(*) = 0 from private.pin_attempts where key in ('name:emma', 'trust:emma')), 'parent clears the username-keyed locks of their child');
select pg_temp.ok((select count(*) = 1 from private.pin_attempts where key = 'name:emma2'), 'another child''s lock is untouched');
delete from private.pin_attempts where key = 'name:emma2';
select pg_temp.ok((select count(*) = 0 from saves where child_id = 'b2222222-2222-2222-2222-222222222222'), 'other family''s save untouched');

-- ---------------------------------------------------------------- child session, shape gate, deletes
set role authenticated;
select pg_temp.as_user('a1111111-1111-1111-1111-111111111111');
select pg_temp.ok((select array_agg(s.status) = '{ok}' from push_save('a1111111-1111-1111-1111-111111111111', '{"schemaVersion":4,"a":1}', 4, (select rev from saves where child_id = 'a1111111-1111-1111-1111-111111111111')) s), 'child pushes own save');
select pg_temp.ok((select array_agg(s.status) = '{invalid}' from push_save('a1111111-1111-1111-1111-111111111111', '[1]', 4, null, true) s), 'array save invalid');
select pg_temp.ok((select array_agg(s.status) = '{invalid}' from push_save('a1111111-1111-1111-1111-111111111111', '{"a":1}', 4, null, true) s), 'save without schemaVersion invalid');
reset role;
update profiles set deleted_at = now() where id = 'a1111111-1111-1111-1111-111111111111';
set role authenticated;
select pg_temp.ok((select array_agg(s.status) = '{denied}' from push_save('a1111111-1111-1111-1111-111111111111', '{"schemaVersion":4}', 4, null, true) s), 'deleted child cannot push');
reset role;
update profiles set deleted_at = null where id = 'a1111111-1111-1111-1111-111111111111';
update families set deleted_at = now() where parent_id = '11111111-1111-1111-1111-111111111111';
set role authenticated;
select pg_temp.ok((select array_agg(s.status) = '{denied}' from push_save('a1111111-1111-1111-1111-111111111111', '{"schemaVersion":4}', 4, null, true) s), 'child of a deleted family cannot push');
reset role;
update families set deleted_at = null where parent_id = '11111111-1111-1111-1111-111111111111';

-- ---------------------------------------------------------------- admin rules unchanged
set role authenticated;
select pg_temp.as_user('00000000-0000-0000-0000-0000000000ad', 'admin', 'aal2');
select pg_temp.ok((select array_agg(s.status) = '{denied}' from push_save('00000000-0000-0000-0000-000000000001', '{"schemaVersion":4}', 4) s), 'admin cannot write Alyssa''s save');
select pg_temp.ok((select array_agg(s.status) = '{ok}' from push_save('00000000-0000-0000-0000-000000000003', '{"schemaVersion":4}', 4) s), 'admin writes the Test Player''s save');
reset role;

-- ---------------------------------------------------------------- purge jobs
insert into private.pin_attempts (key) values ('name:emma2');
update families set deleted_at = now() - interval '8 days' where parent_id = '22222222-2222-2222-2222-222222222222';
update profiles set deleted_at = now() - interval '6 days' where id = 'a1111111-1111-1111-1111-111111111111';
select private.purge_deleted();
select pg_temp.ok((select count(*) = 0 from auth.users where id in ('22222222-2222-2222-2222-222222222222', 'b2222222-2222-2222-2222-222222222222')), 'family deleted 8 days ago: parent and child purged');
select pg_temp.ok((select count(*) = 1 from profiles where id = 'a1111111-1111-1111-1111-111111111111'), 'child deleted 6 days ago kept (still restorable)');
update profiles set deleted_at = now() - interval '8 days' where id = 'a1111111-1111-1111-1111-111111111111';
select private.purge_deleted();
select pg_temp.ok((select count(*) = 0 from auth.users where id = 'a1111111-1111-1111-1111-111111111111'), 'child deleted 8 days ago purged');
select pg_temp.ok((select count(*) = 1 from auth.users where id = '11111111-1111-1111-1111-111111111111'), 'their parent kept');
select pg_temp.ok((select count(*) = 3 from profiles p join auth.users u on u.id = p.parent_id where u.email = 'admin@x.test'), 'admin''s profiles untouched by the purge');
insert into auth.users (email, created_at) values ('late@x.test', now() - interval '4 days');
select private.purge_unconfirmed();
select pg_temp.ok((select count(*) = 0 from auth.users where email = 'late@x.test'), 'unverified sign-up purged after 3 days');
select pg_temp.ok(public.rate_hit('k', 2, '1 hour') and public.rate_hit('k', 2, '1 hour') and not public.rate_hit('k', 2, '1 hour'), 'rate_hit allows 2 then refuses');
\echo ALL CHECKS PASSED
