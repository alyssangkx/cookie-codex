-- Cookie Codex, migration 010: past-paper passage sets (owner OK 21 Nov 2026, "apply migration 010").  APPLIED to the live project 21 Nov 2026 (verified: grp/seq columns, pp_pool and pp_serve return them, grants unchanged).
-- Apply with:  supabase db query --remote --yes -f supabase/migrations/010_pp_sets.sql   (never `db push`).
-- A visual text, cloze or reading passage is one set of questions shown with the same exam pages: pp_items gets the set id
-- (grp) and the question's place in it (seq), both optional (single questions keep null). pp_pool returns them with the ids,
-- so whole sets can be picked before any text is fetched; pp_serve returns them with the content. Limits, logging, the
-- active-only rule (008) and grants are unchanged.

begin;
alter table public.pp_items
  add column grp text check (grp is null or grp ~ '^[a-z0-9-]{3,80}$'),
  add column seq int check (seq is null or seq between 1 and 99);
create index pp_items_grp_idx on public.pp_items (grp) where grp is not null;

-- pp_pool's row type changes, so it is dropped and created again (same body, two more columns)
drop function public.pp_pool(text, text[]);
create function public.pp_pool(p_subject text, p_subtopics text[])
returns table (id text, subtopic text, level text, ord int, grp text, seq int)
language plpgsql security definer set search_path = '' as $$
begin
  if not private.can_read_pp() then
    raise exception 'not allowed' using errcode = '42501';
  end if;
  if coalesce(cardinality(p_subtopics), 0) not between 1 and 40 then
    raise exception 'bad request' using errcode = '22023';
  end if;
  if not public.rate_hit('ppp:' || auth.uid()::text, case when private.pp_trusted() then 1200 else 120 end, interval '1 hour') then
    raise exception 'too many requests' using errcode = '53400';
  end if;
  return query
    select i.id, i.subtopic, i.level, i.ord, i.grp, i.seq from public.pp_items i
     where i.active and i.subject = p_subject and i.subtopic = any (p_subtopics)
     order by i.subtopic, i.ord nulls last, i.id;
end $$;
revoke execute on function public.pp_pool(text, text[]) from public, anon;
grant execute on function public.pp_pool(text, text[]) to authenticated;

create or replace function public.pp_serve(p_ids text[])
returns jsonb
language plpgsql security definer set search_path = '' as $$
declare
  v_uid uuid := auth.uid();
  v_day date := private.sg_today();
  v_trusted boolean := private.pp_trusted();
  v_family uuid;
  v_created timestamptz;
  v_limit int;
  v_new text[];
  v_mine int;
  v_fam int;
begin
  if not private.can_read_pp() then
    raise exception 'not allowed' using errcode = '42501';
  end if;
  if coalesce(cardinality(p_ids), 0) not between 1 and 15
     or exists (select 1 from unnest(p_ids) x where x is null or x !~ '^pp-[0-9a-f]{10}$') then
    raise exception 'bad request' using errcode = '22023';
  end if;
  if not public.rate_hit('pps:' || v_uid::text, case when v_trusted then 400 else 40 end, interval '1 hour') then
    raise exception 'too many requests' using errcode = '53400';
  end if;
  select p.parent_id, p.created_at into v_family, v_created from public.profiles p where p.id = v_uid;
  v_limit := case when v_trusted then 2000 when v_created > now() - interval '7 days' then 125 else 250 end;
  -- ids this account has not been served today (the same question again the same day costs nothing)
  select coalesce(array_agg(distinct x), '{}') into v_new from unnest(p_ids) x
   where exists (select 1 from public.pp_items i where i.id = x and i.active)  -- 008: an inactive or unknown id costs nothing
     and not exists (select 1 from private.pp_served s where s.user_id = v_uid and s.item_id = x and s.day = v_day);
  if cardinality(v_new) > 0 then
    select count(*) into v_mine from private.pp_served s where s.user_id = v_uid and s.day = v_day;
    select count(distinct s.item_id) into v_fam from private.pp_served s where s.family = v_family and s.day = v_day;
    if v_mine + cardinality(v_new) > v_limit
       or (not v_trusted and v_family is not null
           and v_fam + (select count(*) from unnest(v_new) x
                         where not exists (select 1 from private.pp_served s where s.family = v_family and s.day = v_day and s.item_id = x)) > 400) then
      insert into private.pp_flags (user_id, day, reason)
      values (v_uid, v_day, case when v_mine + cardinality(v_new) > v_limit then 'account daily limit ' || v_limit else 'family daily limit 400' end)
      on conflict (user_id, day) do nothing;
      return jsonb_build_object('status', 'limit');
    end if;
    insert into private.pp_served (user_id, family, item_id, day)
    select v_uid, v_family, x, v_day from unnest(v_new) x on conflict do nothing;
  end if;
  return jsonb_build_object('status', 'ok', 'items', coalesce((
    select jsonb_agg(jsonb_build_object('id', i.id, 'subtopic', i.subtopic, 'level', i.level, 'pattern', i.pattern,
                                        'stem', i.stem, 'options', i.options, 'answer', i.answer, 'figures', i.figures,
                                        'year', i.year, 'grp', i.grp, 'seq', i.seq) order by i.id)
      from public.pp_items i where i.active and i.id = any (p_ids)), '[]'::jsonb));
end $$;
revoke execute on function public.pp_serve(text[]) from public, anon;
grant execute on function public.pp_serve(text[]) to authenticated;

commit;
