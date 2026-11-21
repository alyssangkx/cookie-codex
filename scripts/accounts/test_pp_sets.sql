-- Run by sqltest.sh after 010: passage sets (grp, seq) are stored, listed by pp_pool and served by pp_serve.
\set QUIET on
create function pg_temp.ok(c boolean, what text) returns void language plpgsql as $$
begin if c is not true then raise exception 'FAIL: %', what; end if; raise notice 'ok  %', what; end $$;
create function pg_temp.fails(q text, what text) returns void language plpgsql as $$
begin
  begin execute q; exception when others then raise notice 'ok  % (%)', what, sqlerrm; return; end;
  raise exception 'FAIL: % (no error)', what;
end $$;
grant execute on all functions in schema pg_temp to anon, authenticated;
insert into public.pp_items (id, src_id, subject, subtopic, level, stem, options, answer, year, blind_src, ord, grp, seq)
values ('pp-5500000001', 'set-src-1', 'english', 'eng-visual-text', 'basic', 'q1', '["a","b","c","d"]', 0, 2025, 'vl-pages', 1, 'eng-2025-001-vt', 1),
       ('pp-5500000002', 'set-src-2', 'english', 'eng-visual-text', 'basic', 'q2', '["a","b","c","d"]', 1, 2025, 'vl-pages', 2, 'eng-2025-001-vt', 2),
       ('pp-5500000003', 'set-src-3', 'english', 'eng-grammar-mcq', 'basic', 'single', '["a","b","c","d"]', 2, 2025, 'vl-pages', 1, null, null);
select pg_temp.fails($$insert into public.pp_items (id, src_id, subject, subtopic, level, stem, options, answer, year, blind_src, grp, seq)
  values ('pp-5500000004','x','english','eng-visual-text','basic','s','["a","b","c","d"]',0,2025,'b','Bad Group!',1)$$, 'a set id must be a plain lower-case id');
select pg_temp.fails($$insert into public.pp_items (id, src_id, subject, subtopic, level, stem, options, answer, year, blind_src, grp, seq)
  values ('pp-5500000005','x','english','eng-visual-text','basic','s','["a","b","c","d"]',0,2025,'b','eng-set',0)$$, 'a position starts at 1');
-- a fresh signed-in child of its own (the 006 test used up its children's daily quota on purpose)
insert into auth.users (id, email) values ('55555555-0000-0000-0000-0000000000a1', 'sets-parent@x.test'), ('55555555-0000-0000-0000-0000000000c1', 'child-sets@children.invalid');
insert into public.families (parent_id, consent_version) values ('55555555-0000-0000-0000-0000000000a1', 'test');
insert into public.profiles (id, parent_id, name, role) values ('55555555-0000-0000-0000-0000000000c1', '55555555-0000-0000-0000-0000000000a1', 'Setschild', 'child');
update public.profiles set created_at = now() - interval '30 days' where id = '55555555-0000-0000-0000-0000000000c1';
select set_config('request.jwt.claims', jsonb_build_object('sub', '55555555-0000-0000-0000-0000000000c1', 'aal', 'aal1', 'app_metadata', '{}'::jsonb)::text, false);
set role authenticated;
select pg_temp.ok((select count(*) = 2 and bool_and(grp = 'eng-2025-001-vt') and array_agg(seq order by seq) = '{1,2}'
                   from public.pp_pool('english', array['eng-visual-text'])), 'pp_pool lists a set with its id and positions');
select pg_temp.ok((select grp is null and seq is null from public.pp_pool('english', array['eng-grammar-mcq'])), 'a single question has no set');
select pg_temp.ok((select (public.pp_serve(array['pp-5500000001','pp-5500000003'])->'items') @> '[{"id":"pp-5500000001","grp":"eng-2025-001-vt","seq":1},{"id":"pp-5500000003","grp":null,"seq":null}]'),
                  'pp_serve returns the set id and position with the content');
reset role;
select pg_temp.ok(not has_function_privilege('anon', 'public.pp_pool(text, text[])', 'execute'), 'pp_pool stays closed to signed-out users');
select pg_temp.ok(has_function_privilege('authenticated', 'public.pp_pool(text, text[])', 'execute'), 'pp_pool open to signed-in users');
