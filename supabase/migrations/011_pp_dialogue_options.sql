-- 011 (22 Nov 2026, owner OK "A and B ok"): past-paper Chinese 完成对话 sets have 8 phrases per blank. Options stay
-- exactly 4 (answer 0-3) everywhere else; only sub-topic chi-dialogue-mcq may carry 8 (answer 0-7).
begin;
alter table public.pp_items drop constraint pp_items_options_check;
alter table public.pp_items drop constraint pp_items_answer_check;
alter table public.pp_items add constraint pp_items_options_check check (
  jsonb_typeof(options) = 'array'
  and (jsonb_array_length(options) = 4 or (subtopic = 'chi-dialogue-mcq' and jsonb_array_length(options) = 8)));
alter table public.pp_items add constraint pp_items_answer_check check (
  answer >= 0 and answer < (case when jsonb_typeof(options) = 'array' then jsonb_array_length(options) else 4 end));
commit;
