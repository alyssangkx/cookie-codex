-- DRAFT - not applied. Cookie Codex accounts, migration 002: open parent sign-up.
-- Design: docs/accounts-plan.md section 12. Do NOT apply until the owner says "apply" and has answered
-- the decisions listed there. 001_init.sql is applied and frozen: every change is in this file.
--
-- What it does
--   1. families: one row per parent with the FAMILY CODE a child types at login (+ consent record).
--   2. Child names become unique per parent (was: globally unique).
--   3. profiles.unlimited: server-set flag that replaces the name-based isUnlimited() "Admin" check.
--   4. Guard trigger: reserved names, per-parent child cap, test/unlimited only under the admin.
--   5. pin_clear_name_lock: the owning parent may clear a lock, lock keys carry the family (parent id).
--   6. push_save: shape and size check on the jsonb (audit F6). Lower size cap on saves.
--   7. rate_hit(): small fixed-window counter for parent-side actions (service role only).
--   8. purge jobs for pin_attempts and unconfirmed sign-ups (pg_cron lines are commented out).
--   9. Backfill: a families row for the existing grown-up (the admin: Alyssa, Admin player, Test Player).
-- Apply order with the functions (docs section 12.11): this migration and the new pin-login go live
-- together, because the lockout key format changes from '<name_key>' to '<parent_id>:<name_key>'.
-- Nothing here changes RLS on profiles or saves for children, or widens what a parent can do from the
-- browser: parents still write profiles only through the parent-api Edge Function (service role).

-- ---------------------------------------------------------------- family code

-- 8 symbols from 31 (digits 2-9, letters without I, L, O): 31^8 = 8.5e11. The code is a locator, not a
-- secret (children share it); the PIN and the lockouts are the secret. Modulo bias is under 1 part in 28.
create function private.gen_family_code() returns text
language plpgsql volatile set search_path = '' as $$
declare
  alpha constant text := '23456789ABCDEFGHJKMNPQRSTUVWXYZ';
  b bytea := extensions.gen_random_bytes(8);
  out text := '';
  i int;
begin
  for i in 0..7 loop
    out := out || substr(alpha, (get_byte(b, i) % 31) + 1, 1);
  end loop;
  return out;
end $$;
revoke execute on function private.gen_family_code() from public, anon, authenticated;

create table public.families (
  parent_id         uuid primary key references auth.users (id) on delete cascade,
  code              text not null unique check (code ~ '^[2-9A-HJKMNP-Z]{8}$'),
  consent_version   text not null,                       -- which privacy notice the parent accepted
  consented_at      timestamptz not null default now(),  -- server clock
  created_at        timestamptz not null default now()
);
alter table public.families enable row level security;
create policy families_select on public.families for select to authenticated
  using (parent_id = (select auth.uid()));
-- No client write policy: rows are created, rotated and deleted by parent-api / admin (service role).
revoke all on public.families from anon, authenticated;
grant select (parent_id, code, consent_version, consented_at) on public.families to authenticated;

-- Backstop for the sign-up cap (free-tier database size). Raise it with a new migration.
create function private.families_cap() returns trigger
language plpgsql security definer set search_path = '' as $$
begin
  if (select count(*) from public.families) >= 500 then
    raise exception 'family limit reached' using errcode = 'P0001';
  end if;
  return new;
end $$;
create trigger families_cap before insert on public.families
  for each row execute function private.families_cap();

-- ---------------------------------------------------------------- profiles

-- Names unique PER PARENT. Login now finds the family by code first, then the name inside it.
drop index public.profiles_name_key_uq;
create unique index profiles_family_name_uq on public.profiles (parent_id, name_key) where role = 'child';

-- Server-set. No client column grant, so no browser session can set it. Only the admin's own profiles
-- (Test Player, the Admin player) may carry it, enforced in the trigger below.
alter table public.profiles add column unlimited boolean not null default false;
grant select (unlimited) on public.profiles to authenticated;

create function private.profiles_guard() returns trigger
language plpgsql security definer set search_path = '' as $$
declare v_admin boolean; v_n int;
begin
  v_admin := exists (select 1 from auth.users u
                      where u.id = new.parent_id and u.raw_app_meta_data ->> 'role' = 'admin');
  if new.role = 'test' and v_admin then new.unlimited := true; end if;
  if new.unlimited and not v_admin then
    raise exception 'unlimited is for the admin account only' using errcode = 'P0001';
  end if;
  if not v_admin then
    if new.role = 'test' then
      raise exception 'test profiles are admin only' using errcode = 'P0001';
    end if;
    if lower(btrim(new.name)) in ('admin', 'test player') then
      raise exception 'reserved name' using errcode = 'P0001';
    end if;
    if tg_op = 'INSERT' and new.role = 'child' then
      select count(*) into v_n from public.profiles p where p.parent_id = new.parent_id and p.role = 'child';
      if v_n >= 6 then raise exception 'child limit reached' using errcode = 'P0001'; end if;
    end if;
  end if;
  return new;
end $$;
create trigger profiles_guard before insert or update of name, role, unlimited on public.profiles
  for each row execute function private.profiles_guard();

-- ---------------------------------------------------------------- lockout: parent may clear their own children

-- Same signature as 001, so the deployed admin function keeps working. Lock keys are now
-- '<parent_id>:<name_key>' (the new pin-login builds the same string). The owning parent or an admin may
-- clear; the check reads the caller's own JWT, so call it AS THE CALLER (like the admin function does).
create or replace function public.pin_clear_name_lock(p_child uuid) returns void
language plpgsql security definer set search_path = '' as $$
declare k text;
begin
  if not (private.is_admin() or private.owns_child(p_child)) then
    raise exception 'owner only' using errcode = '42501';
  end if;
  select p.parent_id::text || ':' || p.name_key into k from public.profiles p where p.id = p_child;
  if k is null then return; end if;
  delete from private.pin_attempts where key in ('name:' || k, 'trust:' || k);
end $$;
revoke execute on function public.pin_clear_name_lock(uuid) from public, anon;
grant execute on function public.pin_clear_name_lock(uuid) to authenticated, service_role;

-- ---------------------------------------------------------------- saves: size and shape

-- NOT VALID: enforced on every new write, existing rows are not scanned. Measure the Test Player's save
-- before choosing the number (docs 12.11); 512 KB is the draft value (the table check stays at 2 MB).
alter table public.saves add constraint saves_size_cap check (octet_length(data::text) < 524288) not valid;

-- push_save, same signature and rules as 001, plus a shape gate: an object, at most 40 top-level keys,
-- carrying a numeric schemaVersion. A bad shape returns status 'invalid' (the client must treat it like
-- 'denied': no retry loop; decidePush gets the case in Phase 2). The key whitelist is a Phase 2 task.
create or replace function public.push_save(
  p_child uuid, p_data jsonb, p_version int, p_base_rev bigint default null, p_force boolean default false
) returns table (status text, rev bigint, updated_at timestamptz, data jsonb, schema_version int)
language plpgsql security invoker set search_path = '' as $$
declare allowed boolean;
begin
  allowed := case when private.is_admin() then private.is_test_profile(p_child)
                  else private.is_self(p_child) or private.owns_child(p_child) end;
  if not coalesce(allowed, false) then
    status := 'denied'; rev := null; updated_at := null; data := null; schema_version := null;
    return next; return;
  end if;
  if jsonb_typeof(p_data) is distinct from 'object'
     or (select count(*) from jsonb_object_keys(p_data)) > 40
     or jsonb_typeof(p_data -> 'schemaVersion') is distinct from 'number'
     or octet_length(p_data::text) >= 524288 then
    status := 'invalid'; rev := null; updated_at := null; data := null; schema_version := null;
    return next; return;
  end if;

  insert into public.saves as s (child_id, data, schema_version) values (p_child, p_data, p_version)
    on conflict (child_id) do nothing
    returning 'ok', s.rev, s.updated_at, null::jsonb, s.schema_version
    into status, rev, updated_at, data, schema_version;
  if found then return next; return; end if;

  update public.saves s set data = p_data, schema_version = p_version, rev = s.rev + 1
   where s.child_id = p_child and (p_force or s.rev = p_base_rev)
  returning 'ok', s.rev, s.updated_at, null::jsonb, s.schema_version
    into status, rev, updated_at, data, schema_version;
  if found then return next; return; end if;

  select 'conflict', s.rev, s.updated_at, s.data, s.schema_version
    into status, rev, updated_at, data, schema_version
    from public.saves s where s.child_id = p_child;
  if not found then
    status := 'denied'; rev := null; updated_at := null; data := null; schema_version := null;
  end if;
  return next;
end $$;
revoke execute on function public.push_save(uuid, jsonb, int, bigint, boolean) from public, anon;
grant execute on function public.push_save(uuid, jsonb, int, bigint, boolean) to authenticated;

-- ---------------------------------------------------------------- rate counter for parent-side actions

create table private.rate_hits (
  key           text primary key,
  window_start  timestamptz not null default now(),
  n             int not null default 0
);
alter table private.rate_hits enable row level security;

-- Fixed window: true while the key is under p_max hits in the current window, false once over.
-- Used by parent-api ('parent:<id>' 60 per hour for PIN hashing and child changes; 'register:<id>').
create function public.rate_hit(p_key text, p_max int, p_window interval) returns boolean
language plpgsql security definer set search_path = '' as $$
declare r private.rate_hits;
begin
  insert into private.rate_hits (key) values (p_key) on conflict (key) do nothing;
  select * into r from private.rate_hits t where t.key = p_key for update;
  if r.window_start < now() - p_window then
    update private.rate_hits t set window_start = now(), n = 1 where t.key = p_key;
    return true;
  end if;
  update private.rate_hits t set n = t.n + 1 where t.key = p_key;
  return r.n + 1 <= p_max;
end $$;
revoke execute on function public.rate_hit(text, int, interval) from public, anon, authenticated;
grant execute on function public.rate_hit(text, int, interval) to service_role;

-- ---------------------------------------------------------------- purge jobs (audit F4)

-- Lock rows the attacker created with throwaway device ids / names. Strikes decay after 7 quiet days, so a
-- row untouched for 8 days carries no state worth keeping.
create function private.purge_pin_attempts() returns void
language sql security definer set search_path = '' as $$
  delete from private.pin_attempts
   where updated_at < now() - interval '8 days'
     and (locked_until is null or locked_until < now() - interval '8 days');
  delete from private.rate_hits where window_start < now() - interval '2 days';
$$;

-- Sign-ups never verified within 3 days (no profiles, never a child account). Frees the address and the table.
create function private.purge_unconfirmed() returns void
language sql security definer set search_path = '' as $$
  delete from auth.users u
   where u.email_confirmed_at is null
     and u.created_at < now() - interval '3 days'
     and u.email not like '%@children.invalid'
     and not exists (select 1 from public.profiles p where p.parent_id = u.id);
$$;
revoke execute on function private.purge_pin_attempts(), private.purge_unconfirmed() from public, anon, authenticated;

-- pg_cron must first be enabled by the owner (Dashboard > Database > Extensions). Then:
-- select cron.schedule('purge-pin-attempts', '17 3 * * *', $$select private.purge_pin_attempts()$$);
-- select cron.schedule('purge-unconfirmed',  '37 3 * * *', $$select private.purge_unconfirmed()$$);

-- ---------------------------------------------------------------- backfill (existing data)

-- The existing grown-up (the admin) gets a family code so Alyssa, the Admin player and the Test Player can
-- log in under it. consent_version 'owner' = the owner's own household, not a sign-up.
insert into public.families (parent_id, code, consent_version)
  select s.parent_id, private.gen_family_code(), 'owner'
    from (select distinct parent_id from public.profiles) s
  on conflict (parent_id) do nothing;

-- The existing Test Player carries the flag (the guard trigger would also set it on any later write).
update public.profiles set unlimited = true where role = 'test';

-- The live "Admin" player (a role 'child' profile used for browser checks, owned by the admin) keeps its
-- unlimited play, now as a server flag instead of a name check. Matches only a profile whose owner is an
-- admin account. VERIFY FIRST with a read-only query that exactly one such profile exists.
update public.profiles p set unlimited = true
 where p.name_key = 'admin' and p.role = 'child'
   and exists (select 1 from auth.users u where u.id = p.parent_id and u.raw_app_meta_data ->> 'role' = 'admin');
