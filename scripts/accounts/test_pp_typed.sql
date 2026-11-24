-- Run by sqltest.sh after 015: a typed past-paper question (no options, answer 0, accepted answers, optional scaffold) is
-- stored only well-formed, an MCQ row still needs its options and carries no accept list, pp_serve and pp_seen return the
-- new fields, and anon still reads nothing. Raises on failure.
\set QUIET on
create function pg_temp.ok(c boolean, what text) returns void language plpgsql as $$
begin if c is not true then raise exception 'FAIL: %', what; end if; raise notice 'ok  %', what; end $$;
create function pg_temp.fails(q text, what text) returns void language plpgsql as $$
begin
  begin execute q; exception when others then raise notice 'ok  % (%)', what, sqlerrm; return; end;
  raise exception 'FAIL: % (no error)', what;
end $$;
grant execute on all functions in schema pg_temp to anon, authenticated;

insert into public.pp_items (id, src_id, subject, subtopic, level, stem, options, answer, year, blind_src, kind, accept, scaffold) values
  ('pp-7700000001', 'typed-1', 'english', 'eng-synthesis', 'basic', 'Julia tried hard to persuade me. I still did not go to the party.',
   '[]', 0, 2021, 'b', 'typed', '["However hard Julia tried to persuade me, I still did not go to the party."]', 'However ____, I still did not go to the party.'),
  ('pp-7700000002', 'typed-2', 'english', 'eng-grammar-cloze', 'basic', 'The garden is dedicated [[29]] children.', '[]', 0, 2021, 'b', 'typed', '["to"]', null);
select pg_temp.ok((select count(*) = 2 from public.pp_items where kind = 'typed'), 'typed rows with and without a scaffold are stored');
set role service_role;  -- the uploads' role: the accept check's function must run for it
insert into public.pp_items (id, src_id, subject, subtopic, level, stem, options, answer, year, blind_src, kind, accept)
  values ('pp-770000000d', 'typed-sr', 'english', 'eng-synthesis', 'basic', 'x y', '[]', 0, 2021, 'b', 'typed', '["x y z"]');
reset role;
select pg_temp.ok((select count(*) = 1 from public.pp_items where id = 'pp-770000000d'), 'service_role (the uploads) can insert a typed row');
set role authenticated;
select pg_temp.fails($$select public.pp_accept_ok('["a"]')$$, 'a signed-in user cannot call the check function');
reset role;
select pg_temp.ok((select bool_and(kind = 'mcq') from public.pp_items where id not like 'pp-77%'), 'every earlier row is an MCQ by default');
select pg_temp.fails($$insert into public.pp_items (id, src_id, subject, subtopic, level, stem, options, answer, year, blind_src, kind)
  values ('pp-7700000003','t3','english','eng-synthesis','basic','s','[]',0,2021,'b','typed')$$, 'a typed row needs its accepted answers');
select pg_temp.fails($$insert into public.pp_items (id, src_id, subject, subtopic, level, stem, options, answer, year, blind_src, kind, accept)
  values ('pp-7700000004','t4','english','eng-synthesis','basic','s','["a","b","c","d"]',0,2021,'b','typed','["x"]')$$, 'a typed row has no options');
select pg_temp.fails($$insert into public.pp_items (id, src_id, subject, subtopic, level, stem, options, answer, year, blind_src, kind, accept)
  values ('pp-7700000005','t5','english','eng-synthesis','basic','s','[]',2,2021,'b','typed','["x"]')$$, 'a typed row has answer 0');
select pg_temp.fails($$insert into public.pp_items (id, src_id, subject, subtopic, level, stem, options, answer, year, blind_src, kind, accept)
  values ('pp-7700000006','t6','english','eng-synthesis','basic','s','[]',0,2021,'b','typed','[]')$$, 'an empty accept list is refused');
select pg_temp.fails($$insert into public.pp_items (id, src_id, subject, subtopic, level, stem, options, answer, year, blind_src, kind, accept)
  values ('pp-770000000a','ta','english','eng-synthesis','basic','s','[]',0,2021,'b','typed','["ok", "  "]')$$, 'a blank accepted answer is refused');
select pg_temp.fails($$insert into public.pp_items (id, src_id, subject, subtopic, level, stem, options, answer, year, blind_src, kind, accept)
  values ('pp-770000000b','tb','english','eng-synthesis','basic','s','[]',0,2021,'b','typed','[1]')$$, 'a non-string accepted answer is refused');
select pg_temp.fails(format($f$insert into public.pp_items (id, src_id, subject, subtopic, level, stem, options, answer, year, blind_src, kind, accept)
  values ('pp-770000000c','tc','english','eng-synthesis','basic','s','[]',0,2021,'b','typed', %L)$f$, jsonb_build_array(repeat('x', 1001))::text),
  'an accepted answer over 1000 characters is refused');
select pg_temp.fails($$insert into public.pp_items (id, src_id, subject, subtopic, level, stem, options, answer, year, blind_src)
  values ('pp-7700000007','t7','english','eng-grammar-mcq','basic','s','[]',0,2021,'b')$$, 'an MCQ row still needs 4 options');
select pg_temp.fails($$insert into public.pp_items (id, src_id, subject, subtopic, level, stem, options, answer, year, blind_src, accept)
  values ('pp-7700000008','t8','english','eng-grammar-mcq','basic','s','["a","b","c","d"]',0,2021,'b','["a"]')$$, 'an MCQ row carries no accept list');
select pg_temp.fails($$insert into public.pp_items (id, src_id, subject, subtopic, level, stem, options, answer, year, blind_src, kind, accept)
  values ('pp-7700000009','t9','english','eng-synthesis','basic','s','[]',0,2021,'b','essay','["x"]')$$, 'kind is mcq or typed');

insert into auth.users (id, email) values ('77777777-0000-0000-0000-0000000000a1', 'typed-parent@x.test'), ('77777777-0000-0000-0000-0000000000c1', 'child-typed@children.invalid');
insert into public.families (parent_id, consent_version) values ('77777777-0000-0000-0000-0000000000a1', 'test');
insert into public.profiles (id, parent_id, name, role) values ('77777777-0000-0000-0000-0000000000c1', '77777777-0000-0000-0000-0000000000a1', 'Typedchild', 'child');
update public.profiles set created_at = now() - interval '30 days' where id = '77777777-0000-0000-0000-0000000000c1';

select set_config('request.jwt.claims', jsonb_build_object('sub', '77777777-0000-0000-0000-0000000000c1', 'aal', 'aal1', 'app_metadata', '{}'::jsonb)::text, false);
set role authenticated;
select pg_temp.ok((select (public.pp_serve(array['pp-7700000001','pp-7700000002'])->'items') @>
                   '[{"id":"pp-7700000001","kind":"typed","options":[],"scaffold":"However ____, I still did not go to the party.",
                      "accept":["However hard Julia tried to persuade me, I still did not go to the party."]},
                     {"id":"pp-7700000002","kind":"typed","scaffold":null,"accept":["to"]}]'),
                  'pp_serve sends kind, accepted answers and scaffold');
reset role;
select set_config('request.jwt.claims', jsonb_build_object('sub', '77777777-0000-0000-0000-0000000000a1', 'aal', 'aal1')::text, false);
set role authenticated;
select pg_temp.ok((select kind = 'typed' and accept ->> 0 like 'However hard%' and scaffold like 'However ____%'
                     from public.pp_seen('77777777-0000-0000-0000-0000000000c1') where id = 'pp-7700000001'),
                  'the parent sees the typed question with its answer line and accepted answer');
reset role;
set role anon;
select set_config('request.jwt.claims', '', false);
select pg_temp.fails($$select * from public.pp_seen('77777777-0000-0000-0000-0000000000c1')$$, 'anon still cannot read it');
reset role;
\echo TYPED CHECKS PASSED
