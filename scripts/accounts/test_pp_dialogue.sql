-- Run by sqltest.sh after 011: 8 options only for chi-dialogue-mcq, the answer always inside the options.
\set QUIET on
create function pg_temp.fails(q text, what text) returns void language plpgsql as $$
begin
  begin execute q; exception when others then raise notice 'ok  % (%)', what, sqlerrm; return; end;
  raise exception 'FAIL: % (no error)', what;
end $$;
insert into public.pp_items (id, src_id, subject, subtopic, level, stem, options, answer, year, blind_src, ord, grp, seq)
values ('pp-6600000001', 'dlg-1', 'chinese', 'chi-dialogue-mcq', 'basic', '（26）＿＿＿＿', '["1","2","3","4","5","6","7","8"]', 7, 2025, 'models', 1, 'chi-2025-001-dl', 26);
do $$ begin raise notice 'ok  an 8-phrase dialogue blank is stored, answer 7'; end $$;
select pg_temp.fails($$insert into public.pp_items (id, src_id, subject, subtopic, level, stem, options, answer, year, blind_src)
  values ('pp-6600000002','x','chinese','chi-cloze-mcq','basic','s','["1","2","3","4","5","6","7","8"]',0,2025,'b')$$, '8 options outside the dialogue sub-topic');
select pg_temp.fails($$insert into public.pp_items (id, src_id, subject, subtopic, level, stem, options, answer, year, blind_src)
  values ('pp-6600000003','x','english','eng-grammar-mcq','basic','s','["a","b","c","d"]',4,2025,'b')$$, 'an answer past the 4th option');
select pg_temp.fails($$insert into public.pp_items (id, src_id, subject, subtopic, level, stem, options, answer, year, blind_src)
  values ('pp-6600000004','x','chinese','chi-dialogue-mcq','basic','s','["1","2","3","4","5","6"]',0,2025,'b')$$, 'a dialogue blank with 6 options');
select pg_temp.fails($$insert into public.pp_items (id, src_id, subject, subtopic, level, stem, options, answer, year, blind_src)
  values ('pp-6600000005','x','chinese','chi-dialogue-mcq','basic','s','["1","2","3","4","5","6","7","8"]',8,2025,'b')$$, 'an answer past the 8th phrase');
do $$ begin raise notice 'dialogue checks passed: 5'; end $$;
