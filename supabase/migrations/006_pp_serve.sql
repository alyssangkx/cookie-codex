-- Cookie Codex, migration 006: past-paper questions served per quiz, with daily limits, a log and flags (ADR 0012,
-- owner 21 Nov 2026: anti-scraping).  NOT YET APPLIED.
-- Apply with:  supabase db query --remote --yes -f supabase/migrations/006_pp_serve.sql   (never `db push`).
-- Test: scripts/accounts/sqltest.sh runs 001-006 locally.
-- Additive only: the old bulk read (pp_items_for) and the readers' select policy on pp-figures stay until the new site
-- is live, then migration 007 removes them (so the live plant-transport sub-topic never breaks).
--
-- What it adds:
--   * pp_items.ord: easier-first rank inside a sub-topic (written by load_pp.py upload).
--   * public.pp_pool(subject, subtopic): question ids and their rank only, no text. Readers as in 004.
--   * public.pp_serve(ids[]): text and figure paths for at most 15 ids (one quiz), as jsonb {status: 'ok', items} or
--     {status: 'limit'}. Every id served is logged per account and Singapore day; a new id beyond the account's daily
--     limit (250 distinct questions; 125 in the account's first 7 days; 2000 for the admin and the Test Player) or the
--     family's (400 distinct a day across a parent's children) is refused, the account is flagged, and nothing is served.
--     40 calls an hour (400 for the admin and the Test Player).
--   * private.pp_served (the log) and private.pp_flags; public.pp_flag_take(uid) for the pp-serve function (service role
--     only) to email the admin once per flag; public.pp_usage_report() for the admin page (admin at aal2 only).
-- Nothing in this file contains past-paper content.

begin;

alter table public.pp_items add column ord int;  -- easier-first rank inside the sub-topic; null sorts last

create table private.pp_served (
  user_id   uuid not null references auth.users (id) on delete cascade,
  family    uuid,                                    -- the child's parent_id (null for the admin)
  item_id   text not null,
  day       date not null,                           -- Singapore date
  served_at timestamptz not null default now(),
  primary key (user_id, item_id, day)
);
create index pp_served_family_day on private.pp_served (family, day);
create index pp_served_day on private.pp_served (day);
alter table private.pp_served enable row level security;

create table private.pp_flags (
  user_id     uuid not null references auth.users (id) on delete cascade,
  day         date not null,
  reason      text not null,
  created_at  timestamptz not null default now(),
  notified_at timestamptz,
  primary key (user_id, day)
);
alter table private.pp_flags enable row level security;

create function private.sg_today() returns date language sql stable as $$ select (now() at time zone 'Asia/Singapore')::date $$;

-- The admin, or one of the admin's own unlimited profiles (the Test Player): the higher limits.
create function private.pp_trusted() returns boolean
language sql stable security definer set search_path = '' as $$
  select coalesce(auth.jwt() -> 'app_metadata' ->> 'role', '') = 'admin'
      or exists (select 1 from public.profiles p where p.id = auth.uid() and p.unlimited)
$$;

create function public.pp_pool(p_subject text, p_subtopic text)
returns table (id text, ord int)
language plpgsql security definer set search_path = '' as $$
begin
  if not private.can_read_pp() then
    raise exception 'not allowed' using errcode = '42501';
  end if;
  if not public.rate_hit('ppp:' || auth.uid()::text, case when private.pp_trusted() then 1200 else 120 end, interval '1 hour') then
    raise exception 'too many requests' using errcode = '53400';
  end if;
  return query
    select i.id, i.ord from public.pp_items i
     where i.active and i.subject = p_subject and i.subtopic = p_subtopic
     order by i.ord nulls last, i.id;
end $$;
revoke execute on function public.pp_pool(text, text) from public, anon;
grant execute on function public.pp_pool(text, text) to authenticated;

create function public.pp_serve(p_ids text[])
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
   where not exists (select 1 from private.pp_served s where s.user_id = v_uid and s.item_id = x and s.day = v_day);
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
                                        'year', i.year) order by i.id)
      from public.pp_items i where i.active and i.id = any (p_ids)), '[]'::jsonb));
end $$;
revoke execute on function public.pp_serve(text[]) from public, anon;
grant execute on function public.pp_serve(text[]) to authenticated;

-- For the pp-serve function (service role): the flag of this account today, once (it then emails the admin).
create function public.pp_flag_take(p_uid uuid)
returns table (name text, reason text, day date)
language plpgsql security definer set search_path = '' as $$
begin
  return query
    update private.pp_flags f set notified_at = now()
     where f.user_id = p_uid and f.day = private.sg_today() and f.notified_at is null
    returning (select coalesce(p.name, 'admin account') from public.profiles p where p.id = f.user_id), f.reason, f.day;
end $$;
revoke execute on function public.pp_flag_take(uuid) from public, anon, authenticated;
grant execute on function public.pp_flag_take(uuid) to service_role;

-- Admin page "Heavy use": today's top accounts, flags of the last 7 days, the busiest families today.
create function public.pp_usage_report()
returns jsonb
language plpgsql security definer set search_path = '' as $$
declare v_day date := private.sg_today();
begin
  if coalesce(auth.jwt() -> 'app_metadata' ->> 'role', '') <> 'admin' or coalesce(auth.jwt() ->> 'aal', '') <> 'aal2' then
    raise exception 'not allowed' using errcode = '42501';
  end if;
  return jsonb_build_object(
    'day', v_day,
    'top', coalesce((select jsonb_agg(t order by t.n desc) from (
       select coalesce(p.name, 'admin account') as name, s.user_id, count(*) as n,
              exists (select 1 from private.pp_flags f where f.user_id = s.user_id and f.day = v_day) as flagged
         from private.pp_served s left join public.profiles p on p.id = s.user_id
        where s.day = v_day group by s.user_id, p.name order by count(*) desc limit 20) t), '[]'::jsonb),
    'families', coalesce((select jsonb_agg(t order by t.n desc) from (
       select s.family, count(distinct s.item_id) as n, count(distinct s.user_id) as children
         from private.pp_served s where s.day = v_day and s.family is not null
        group by s.family having count(distinct s.item_id) >= 150 order by 2 desc limit 20) t), '[]'::jsonb),
    'flags', coalesce((select jsonb_agg(t order by t.day desc) from (
       select coalesce(p.name, 'admin account') as name, f.user_id, f.day, f.reason, f.notified_at
         from private.pp_flags f left join public.profiles p on p.id = f.user_id
        where f.day > v_day - 7 order by f.day desc limit 50) t), '[]'::jsonb));
end $$;
revoke execute on function public.pp_usage_report() from public, anon;
grant execute on function public.pp_usage_report() to authenticated;

commit;
