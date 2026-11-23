-- Cookie Codex, migration 014: explanations for past-paper questions (owner, 23 Nov 2026: "why is the answer correct ...
-- do it for all applicable English questions"; Maths and Science later). APPLIED to the live project 23 Nov 2026 (owner OK; verified: column present, 12,811 active items intact, pp_serve sends explain, anon cannot call pp_seen).
-- Apply with:  supabase db query --remote --yes -f supabase/migrations/014_pp_explain.sql   (never `db push`).
-- Test: scripts/accounts/sqltest.sh applies it after 013 and runs test_pp_explain.sql.
--
-- pp_items.explain: {"right": "why the key is right", "wrong": ["why option 1 does not fit", null for the key, ...]},
-- written by scripts/pastpapers/explain.py (server model) and checked by a second model before upload; null when there
-- is none. It travels with the question exactly as the stem and key do: pp_serve (the quiz) and pp_seen (the parent's
-- list of a child's questions) return it; no other read is added (the lockdown of 007 stands).

begin;

alter table public.pp_items add column explain jsonb
  check (explain is null or (jsonb_typeof(explain) = 'object' and coalesce(jsonb_typeof(explain -> 'right'), '') = 'string'));

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
                                        'year', i.year, 'grp', i.grp, 'seq', i.seq, 'explain', i.explain) order by i.id)
      from public.pp_items i where i.active and i.id = any (p_ids)), '[]'::jsonb));
end $$;
revoke execute on function public.pp_serve(text[]) from public, anon;
grant execute on function public.pp_serve(text[]) to authenticated;

drop function public.pp_seen(uuid);  -- its returned columns change
create function public.pp_seen(p_child uuid)
returns table (id text, subtopic text, level text, stem text, options jsonb, answer smallint, figures jsonb, grp text, seq int, explain jsonb)
language plpgsql stable security definer set search_path = '' as $$
begin
  if p_child is null or not private.may_see_child(p_child) then
    raise exception 'not allowed' using errcode = '42501';
  end if;
  return query
    select i.id, i.subtopic, i.level, i.stem, i.options, i.answer, i.figures, i.grp, i.seq, i.explain
      from public.pp_items i
     where i.active  -- a withdrawn item (migration 008) is never shown again
       and exists (select 1 from private.pp_served s where s.user_id = p_child and s.item_id = i.id)
     order by i.subtopic, i.grp nulls first, i.seq, i.id;
end $$;
revoke execute on function public.pp_seen(uuid) from public, anon;
grant execute on function public.pp_seen(uuid) to authenticated;

commit;
