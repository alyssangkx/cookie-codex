-- Run by sqltest.sh after 014: a past-paper question's explanation is stored (well-formed only), served with the question by
-- pp_serve, and shown to the child's parent by pp_seen; anon still reads nothing. Raises on failure.
\set QUIET on
create function pg_temp.ok(c boolean, what text) returns void language plpgsql as $$
begin if c is not true then raise exception 'FAIL: %', what; end if; raise notice 'ok  %', what; end $$;
create function pg_temp.fails(q text, what text) returns void language plpgsql as $$
begin
  begin execute q; exception when others then raise notice 'ok  % (%)', what, sqlerrm; return; end;
  raise exception 'FAIL: % (no error)', what;
end $$;
grant execute on all functions in schema pg_temp to anon, authenticated;

insert into public.pp_items (id, src_id, subject, subtopic, level, stem, options, answer, year, blind_src, explain) values
  ('pp-8800000001', 'exp-1', 'english', 'eng-grammar-mcq', 'basic', 'Andrew prefers to have his dinner earlier, ____ he?',
   '["doesn''t","hasn''t","isn''t","didn''t"]', 0, 2025, 'b',
   '{"right": "prefers is present simple, so the tag uses does: doesn''t he?", "wrong": [null, "hasn''t needs has as a helper", "isn''t needs is", "didn''t is past"]}'),
  ('pp-8800000002', 'exp-2', 'english', 'eng-grammar-mcq', 'basic', 'no explanation yet ____.', '["a","b","c","d"]', 1, 2025, 'b', null);
select pg_temp.fails($$insert into public.pp_items (id, src_id, subject, subtopic, level, stem, options, answer, year, blind_src, explain)
  values ('pp-8800000003','x','english','eng-grammar-mcq','basic','s','["a","b","c","d"]',0,2025,'b','"just text"')$$, 'an explanation must be an object');
select pg_temp.fails($$insert into public.pp_items (id, src_id, subject, subtopic, level, stem, options, answer, year, blind_src, explain)
  values ('pp-8800000004','x','english','eng-grammar-mcq','basic','s','["a","b","c","d"]',0,2025,'b','{"wrong": []}')$$, 'an explanation must say why the key is right');

insert into auth.users (id, email) values ('88888888-0000-0000-0000-0000000000a1', 'exp-parent@x.test'), ('88888888-0000-0000-0000-0000000000c1', 'child-exp@children.invalid');
insert into public.families (parent_id, consent_version) values ('88888888-0000-0000-0000-0000000000a1', 'test');
insert into public.profiles (id, parent_id, name, role) values ('88888888-0000-0000-0000-0000000000c1', '88888888-0000-0000-0000-0000000000a1', 'Expchild', 'child');
update public.profiles set created_at = now() - interval '30 days' where id = '88888888-0000-0000-0000-0000000000c1';

select set_config('request.jwt.claims', jsonb_build_object('sub', '88888888-0000-0000-0000-0000000000c1', 'aal', 'aal1', 'app_metadata', '{}'::jsonb)::text, false);
set role authenticated;
select pg_temp.ok((select (public.pp_serve(array['pp-8800000001','pp-8800000002'])->'items') @>
                   '[{"id":"pp-8800000001","explain":{"wrong":[null,"hasn''t needs has as a helper","isn''t needs is","didn''t is past"]}},{"id":"pp-8800000002","explain":null}]'),
                  'pp_serve sends the explanation with the question (null when there is none)');
reset role;
select set_config('request.jwt.claims', jsonb_build_object('sub', '88888888-0000-0000-0000-0000000000a1', 'aal', 'aal1')::text, false);
set role authenticated;
select pg_temp.ok((select explain ->> 'right' like 'prefers is present simple%' from public.pp_seen('88888888-0000-0000-0000-0000000000c1') where id = 'pp-8800000001'),
                  'the parent sees it with the questions their child was served');
reset role;
set role anon;
select set_config('request.jwt.claims', '', false);
select pg_temp.fails($$select * from public.pp_seen('88888888-0000-0000-0000-0000000000c1')$$, 'anon still cannot read it');
reset role;
\echo EXPLAIN CHECKS PASSED
