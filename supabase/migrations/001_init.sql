-- Cookie Codex accounts, migration 001.  NOT APPLIED: review first (docs/accounts-plan.md).
-- This file has never been applied anywhere, so it is edited in place rather than followed by a
-- 002 migration. Once it is applied to a real project, every change must be a new migration.
--
-- Model: every child has their own Supabase auth user (random password nobody types). profiles.id
-- IS that user's id, so a child session can be matched to a row with auth.uid(). profiles.parent_id
-- is the owning grown-up (today: the admin account; later: a parent). Roles for grown-ups live in
-- auth.users.raw_app_meta_data->>'role' ('admin' | 'parent'), which the client can never write.
-- The PIN is NEVER stored in plain text and no PIN appears in this repo: the admin types it into
-- the admin tool, and the pin-login/admin-pin functions store only a salted, peppered hash.

create schema if not exists private;

-- ---------------------------------------------------------------- tables

create table public.profiles (
  id          uuid primary key references auth.users (id) on delete cascade,
  parent_id   uuid not null references auth.users (id) on delete cascade,
  -- ASCII only for now: the same regex pin-login applies before any lookup. Non-ASCII names later
  -- need NFC normalisation on both sides.
  name        text not null check (btrim(name) ~ '^[A-Za-z][A-Za-z -]{0,19}$'),
  -- the exact-match key pin-login queries; pin-login normalises its input the same way
  name_key    text generated always as (lower(btrim(name))) stored,
  role        text not null default 'child' check (role in ('child', 'test')),
  -- 'pbkdf2-sha256$<iterations>$<salt b64>$<hash b64>'; null = no PIN set, login refused
  pin_hash    text,
  -- set by trigger whenever pin_hash is set or changed; pin-login puts it in the trusted-device
  -- token's HMAC, so a PIN reset revokes every token issued before it
  pin_set_at  timestamptz,
  created_at  timestamptz not null default now()
);
-- A child logs in by typing their name, so child names are unique among children for now (the Test
-- Player is excluded). When a second family joins, add a family code and make this unique per
-- parent instead (see the plan).
create unique index profiles_name_key_uq on public.profiles (name_key) where role = 'child';
create index profiles_parent_idx on public.profiles (parent_id);

create table public.saves (
  child_id        uuid primary key references public.profiles (id) on delete cascade,
  data            jsonb not null check (octet_length(data::text) < 2000000),
  schema_version  int not null,
  rev             bigint not null default 0,   -- bumped by every write; the sync compare-and-set key
  updated_at      timestamptz not null default now()
);

-- Lockout counters. Only the pin-login function (service role) touches this; RLS on, no policies.
create table private.pin_attempts (
  key           text primary key,          -- 'device:<id>' | 'name:<name_key>' (untrusted) | 'trust:<name_key>' (trusted)
  fails         int not null default 0,
  strikes       int not null default 0,    -- times this key has locked since its last success (escalation)
  locked_until  timestamptz,
  updated_at    timestamptz not null default now()
);
alter table private.pin_attempts enable row level security;

-- The server clock decides updated_at, never the browser.
create function private.touch_updated_at() returns trigger
language plpgsql set search_path = '' as $$
begin
  new.updated_at := now();
  -- every write advances rev, even one that bypassed push_save
  if tg_op = 'UPDATE' and new.rev <= old.rev then new.rev := old.rev + 1; end if;
  return new;
end $$;
create trigger saves_touch before insert or update on public.saves
  for each row execute function private.touch_updated_at();

-- pin_set_at follows pin_hash: set on every insert with a hash and every change of the hash (set or reset).
create function private.touch_pin_set_at() returns trigger
language plpgsql set search_path = '' as $$
begin
  if new.pin_hash is not null and (tg_op = 'INSERT' or new.pin_hash is distinct from old.pin_hash) then
    new.pin_set_at := now();
  end if;
  return new;
end $$;
create trigger profiles_pin_set_at before insert or update of pin_hash on public.profiles
  for each row execute function private.touch_pin_set_at();

-- ---------------------------------------------------------------- role helpers (used by RLS)

create function private.is_admin() returns boolean
language sql stable set search_path = '' as $$
  select coalesce(auth.jwt() -> 'app_metadata' ->> 'role', '') = 'admin'
$$;

-- security definer so the policy lookup does not re-enter profiles' own RLS
create function private.owns_child(p_child uuid) returns boolean
language sql stable security definer set search_path = '' as $$
  select exists (select 1 from public.profiles p where p.id = p_child and p.parent_id = auth.uid())
$$;

create function private.is_test_profile(p_child uuid) returns boolean
language sql stable security definer set search_path = '' as $$
  select exists (select 1 from public.profiles p where p.id = p_child and p.role = 'test')
$$;

-- the caller is this child's own session (the profile row must exist)
create function private.is_self(p_child uuid) returns boolean
language sql stable security definer set search_path = '' as $$
  select exists (select 1 from public.profiles p where p.id = p_child and p.id = auth.uid())
$$;

grant usage on schema private to authenticated, service_role;
grant execute on function private.is_admin(), private.owns_child(uuid), private.is_test_profile(uuid), private.is_self(uuid)
  to authenticated;

-- ---------------------------------------------------------------- RLS: profiles

alter table public.profiles enable row level security;

create policy profiles_select on public.profiles for select to authenticated
  using (parent_id = (select auth.uid()) or id = (select auth.uid()) or (select private.is_admin()));
-- Only an admin session writes profiles. A child or a parent never inserts, renames or deletes one
-- from the browser; creating a child needs an auth user anyway, so it goes through admin-pin
-- (service role). Reads: a child sees only its own row, a parent only its children, and the column
-- grants below keep pin_hash out of every response.
create policy profiles_insert on public.profiles for insert to authenticated
  with check ((select private.is_admin()));
create policy profiles_update on public.profiles for update to authenticated
  using ((select private.is_admin())) with check ((select private.is_admin()));
create policy profiles_delete on public.profiles for delete to authenticated
  using ((select private.is_admin()));

-- Column grants keep pin_hash out of every client response, even to the owning parent.
-- Do not add a table-wide GRANT SELECT later: it would expose pin_hash again.
revoke all on public.profiles from anon, authenticated;
grant select (id, parent_id, name, role, pin_set_at, created_at) on public.profiles to authenticated;
grant insert (id, parent_id, name, role) on public.profiles to authenticated;
grant update (name) on public.profiles to authenticated;
grant delete on public.profiles to authenticated;

-- ---------------------------------------------------------------- RLS: saves

alter table public.saves enable row level security;

-- the owning parent and the child's own session can read and write; the admin can read all
create policy saves_select on public.saves for select to authenticated
  using ((select private.owns_child(child_id)) or child_id = (select auth.uid()) or (select private.is_admin()));
create policy saves_insert on public.saves for insert to authenticated
  with check ((select private.owns_child(child_id)) or child_id = (select auth.uid()));
create policy saves_update on public.saves for update to authenticated
  using ((select private.owns_child(child_id)) or child_id = (select auth.uid()))
  with check ((select private.owns_child(child_id)) or child_id = (select auth.uid()));
create policy saves_delete on public.saves for delete to authenticated
  using ((select private.owns_child(child_id)));

-- The admin is also the parent of the real child, so the rules above would let the admin write
-- Alyssa's save. These RESTRICTIVE policies narrow that: an admin session may only write the Test
-- Player's save. (A child's own session and a normal parent are unaffected.)
create policy saves_admin_test_only_ins on public.saves as restrictive for insert to authenticated
  with check (not (select private.is_admin()) or (select private.is_test_profile(child_id)));
create policy saves_admin_test_only_upd on public.saves as restrictive for update to authenticated
  using (not (select private.is_admin()) or (select private.is_test_profile(child_id)))
  with check (not (select private.is_admin()) or (select private.is_test_profile(child_id)));
create policy saves_admin_test_only_del on public.saves as restrictive for delete to authenticated
  using (not (select private.is_admin()) or (select private.is_test_profile(child_id)));

revoke all on public.saves from anon;

-- ---------------------------------------------------------------- sync: compare-and-set push

-- The browser sends the rev it last saw (p_base_rev; null = never synced). The update succeeds only
-- where rev = p_base_rev and sets rev = rev + 1, returning the new rev. Otherwise nothing is written
-- and the server copy comes back with status 'conflict', so the client can warn instead of silently
-- overwriting. p_force overwrites after the user chose "keep this device". A first save inserts with
-- on conflict do nothing, so two devices racing to create the row cannot both win: the loser falls
-- through to the compare-and-set and conflicts.
-- Write permission is decided FIRST, before any row is touched, by the same helpers the RLS policies
-- use (no logic is repeated here): an admin session may write only a test profile
-- (private.is_test_profile); anyone else may write if it is the child itself (private.is_self) or the
-- owning parent (private.owns_child). Otherwise status 'denied' comes back on both the update and the
-- insert path, never 'conflict' or an RLS exception.
-- Security invoker: RLS still applies as a second layer. UNTESTED: needs a Supabase project.
create function public.push_save(
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

-- ---------------------------------------------------------------- PIN lockout (service role only)

-- One atomic step: check the locks, then count this attempt BEFORE the PIN is verified. Concurrent
-- requests serialise on the row locks, so no more than p_max attempts per key can ever pass.
--
-- Three kinds of key, each with its own limit; a lock doubles each time the key trips
-- (base, 2x, 4x, ... capped at 24 h); strikes reset only in pin_clear (a successful login):
--   device:<id>     5 tries, base 15 min   every request
--   name:<name_key> 20 tries, base 15 min  requests WITHOUT a valid trusted-device token
--   trust:<name_key> 30 tries, base 15 min requests WITH a valid trusted-device token (bounds a copied token)
-- p_device_key and p_name_key are each optional (null / '' skips that key). pin-login calls it twice:
-- first (device_key, null, false) so a locked device costs one cheap call before any profile lookup,
-- then (null, name_key, trusted) once the token has been verified against the profile.
-- Rows are locked in key order (device < name < trust), so two calls cannot deadlock.
-- Returns allowed = false (and scope 'device' or 'name') with the lock expiry if a key is locked: nothing
-- is counted. Otherwise every given key is incremented; reaching its limit applies the lock NOW (the
-- attempt that reaches the limit is still allowed, the next one is refused), and the expiry is returned
-- in device_until / name_until so the caller can answer 'locked' straight after a wrong PIN.
-- On a wrong PIN the incremented counters simply stand; on success the caller runs pin_clear.
-- A fail count older than 24 h restarts, as does the first try after a lock has expired (strikes stay).
-- Worst-case rates are documented in docs/accounts-plan.md section 5. UNTESTED: needs a Supabase project.
create function private.pin_bump(p_key text, p_max int, p_base interval)
returns table (fails int, locked_until timestamptz)
language sql security definer set search_path = '' as $$
  insert into private.pin_attempts as a (key, fails, strikes, locked_until, updated_at)
  values (p_key, 1, 0, null, now())
  on conflict (key) do update set
    fails = case when a.updated_at < now() - interval '24 hours' or a.locked_until is not null then 1 else a.fails + 1 end,
    strikes = a.strikes + case
      when (case when a.updated_at < now() - interval '24 hours' or a.locked_until is not null then 1 else a.fails + 1 end) >= p_max
      then 1 else 0 end,
    locked_until = case
      when (case when a.updated_at < now() - interval '24 hours' or a.locked_until is not null then 1 else a.fails + 1 end) >= p_max
      then now() + least(p_base * power(2::double precision, least(a.strikes, 20)), interval '24 hours')
      else null end,
    updated_at = now()
  returning a.fails, a.locked_until
$$;

revoke execute on function private.pin_bump(text, int, interval) from public, anon, authenticated;

create function public.pin_reserve_attempt(p_device_key text, p_name_key text, p_trusted boolean)
returns table (allowed boolean, scope text, device_until timestamptz, name_until timestamptz, attempts_left int)
language plpgsql security definer set search_path = '' as $$
declare
  v_dev text := nullif(p_device_key, '');
  v_nm  text := case when coalesce(p_name_key, '') = '' then null
                     else (case when p_trusted then 'trust:' else 'name:' end) || p_name_key end;
  d private.pin_attempts; n private.pin_attempts; r record;
begin
  if v_dev is not null then insert into private.pin_attempts (key) values (v_dev) on conflict (key) do nothing; end if;
  if v_nm  is not null then insert into private.pin_attempts (key) values (v_nm)  on conflict (key) do nothing; end if;
  if v_dev is not null then select * into d from private.pin_attempts a where a.key = v_dev for update; end if;
  if v_nm  is not null then select * into n from private.pin_attempts a where a.key = v_nm  for update; end if;

  if d.locked_until > now() then
    allowed := false; scope := 'device'; device_until := d.locked_until; name_until := null; attempts_left := 0;
    return next; return;
  end if;
  if n.locked_until > now() then
    allowed := false; scope := 'name'; device_until := null; name_until := n.locked_until; attempts_left := null;
    return next; return;
  end if;

  allowed := true; scope := null; device_until := null; name_until := null; attempts_left := null;
  if v_dev is not null then
    select * into r from private.pin_bump(v_dev, 5, interval '15 minutes');
    device_until := r.locked_until; attempts_left := greatest(0, 5 - r.fails);
  end if;
  if v_nm is not null then
    select * into r from private.pin_bump(v_nm, case when p_trusted then 30 else 20 end, interval '15 minutes');
    name_until := r.locked_until;
  end if;
  return next;
end $$;

create function public.pin_clear(p_keys text[]) returns void
language sql security definer set search_path = '' as $$
  delete from private.pin_attempts where key = any (p_keys)
$$;

revoke execute on function public.pin_reserve_attempt(text, text, boolean), public.pin_clear(text[]) from public, anon, authenticated;
grant execute on function public.pin_reserve_attempt(text, text, boolean), public.pin_clear(text[]) to service_role;

-- Admin only: clear a child's per-name and trusted-name locks (and their escalation) so a stranger's guessing cannot keep
-- her out. Called from /admin/ with the admin's own session; the caller's app_metadata role is checked
-- inside. Device keys are not touched. UNTESTED: needs a Supabase project.
create function public.pin_clear_name_lock(p_child uuid) returns void
language plpgsql security definer set search_path = '' as $$
begin
  if not private.is_admin() then
    raise exception 'admin only' using errcode = '42501';
  end if;
  delete from private.pin_attempts
   where key in ('name:' || (select p.name_key from public.profiles p where p.id = p_child),
                 'trust:' || (select p.name_key from public.profiles p where p.id = p_child));
end $$;
revoke execute on function public.pin_clear_name_lock(uuid) from public, anon;
grant execute on function public.pin_clear_name_lock(uuid) to authenticated, service_role;
