-- Run by sqltest.sh after 013: pp_counts gives a signed-in user the active count per sub-topic and level, nothing else;
-- withdrawn items are not counted; anon cannot call it. Raises on failure.
\set QUIET on
create function pg_temp.ok(c boolean, what text) returns void language plpgsql as $$
begin if c is not true then raise exception 'FAIL: %', what; end if; raise notice 'ok  %', what; end $$;
create function pg_temp.fails(q text, what text) returns void language plpgsql as $$
begin
  begin execute q; exception when others then raise notice 'ok  % (%)', what, sqlerrm; return; end;
  raise exception 'FAIL: % (no error)', what;
end $$;
grant execute on all functions in schema pg_temp to anon, authenticated;

insert into public.pp_items (id, src_id, subject, subtopic, level, stem, options, answer, figures, year, blind_src, active) values
  ('pp-7700000101', 'cnt-1', 'science', 'sci-cnt', 'basic', 's', '["a","b","c","d"]', 1, '[]', 2025, 'b', true),
  ('pp-7700000102', 'cnt-2', 'science', 'sci-cnt', 'basic', 's', '["a","b","c","d"]', 1, '[]', 2025, 'b', true),
  ('pp-7700000103', 'cnt-3', 'science', 'sci-cnt', 'competent', 's', '["a","b","c","d"]', 1, '[]', 2025, 'b', true),
  ('pp-7700000104', 'cnt-4', 'science', 'sci-cnt', 'basic', 's', '["a","b","c","d"]', 1, '[]', 2025, 'b', false);

set role authenticated;
select set_config('request.jwt.claims', '{"sub":"77777777-0000-0000-0000-0000000000a1","aal":"aal1"}', false);
select pg_temp.ok((select n = 2 from public.pp_counts() where subtopic = 'sci-cnt' and level = 'basic'), 'active basic items counted, the withdrawn one not');
select pg_temp.ok((select n = 1 from public.pp_counts() where subtopic = 'sci-cnt' and level = 'competent'), 'per level');
select pg_temp.ok((select array_agg(k order by k) = array['level','n','subtopic']
                     from jsonb_object_keys((select to_jsonb(c) from public.pp_counts() c limit 1)) k), 'numbers only: no id, text or key column');
reset role;
set role anon;
select set_config('request.jwt.claims', '', false);
select pg_temp.fails($$select * from public.pp_counts()$$, 'anon cannot call it');
reset role;
\echo COUNTS CHECKS PASSED
