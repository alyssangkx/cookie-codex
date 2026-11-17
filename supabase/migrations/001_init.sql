-- Cookie Codex accounts, migration 001.  NOT APPLIED: review first (docs/accounts-plan.md).
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
  name        text not null check (char_length(btrim(name)) between 1 and 30),
  role        text not null default 'child' check (role in ('child', 'test')),
  -- 'pbkdf2-sha256$<iterations>$<salt b64>$<hash b64>'; null = no PIN set, login refused
  pin_hash    text,
  pin_set_at  timestamptz,
  created_at  timestamptz not null default now()
);
-- A child logs in by typing their name, so child names are unique for now. When a second family
-- joins, add a family code and make this unique per parent instead (see the plan).
create unique index profiles_child_name_uq on public.profiles (lower(btrim(name))) where role = 'child';
create index profiles_parent_idx on public.profiles (parent_id);

create table public.saves (
  child_id        uuid primary key references public.profiles (id) on delete cascade,
  data            jsonb not null check (octet_length(data::text) < 2000000),
  schema_version  int not null,
  updated_at      timestamptz not null default now()
);

-- Lockout counters. Only the pin-login function (service role) touches this; RLS on, no policies.
create table private.pin_attempts (
  key           text primary key,          -- 'device:<id>' | 'name:<lowercase name>' | 'ip:<sha256>'
  fails         int not null default 0,
  locked_until  timestamptz,
  updated_at    timestamptz not null default now()
);
alter table private.pin_attempts enable row level security;

-- The server clock decides updated_at, never the browser.
create function private.touch_updated_at() returns trigger
language plpgsql set search_path = '' as $$
begin
  new.updated_at := now();
  return new;
end $$;
create trigger saves_touch before insert or update on public.saves
  for each row execute function private.touch_updated_at();

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

grant usage on schema private to authenticated, service_role;
grant execute on function private.is_admin(), private.owns_child(uuid), private.is_test_profile(uuid)
  to authenticated;

-- ---------------------------------------------------------------- RLS: profiles

alter table public.profiles enable row level security;

create policy profiles_select on public.profiles for select to authenticated
  using (parent_id = (select auth.uid()) or id = (select auth.uid()) or (select private.is_admin()));
create policy profiles_insert on public.profiles for insert to authenticated
  with check (parent_id = (select auth.uid()));
create policy profiles_update on public.profiles for update to authenticated
  using (parent_id = (select auth.uid())) with check (parent_id = (select auth.uid()));
create policy profiles_delete on public.profiles for delete to authenticated
  using (parent_id = (select auth.uid()));

-- Column grants keep pin_hash out of every client response, even to the owning parent.
-- Do not add a table-wide GRANT SELECT later: it would expose pin_hash again.
revoke all on public.profiles from anon, authenticated;
grant select (id, parent_id, name, role, pin_set_at, created_at) on public.profiles to authenticated;
grant insert (id, parent_id, name) on public.profiles to authenticated;
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

-- The browser sends the updated_at it last saw (p_base). If the server row has moved on, nothing is
-- written and the server copy comes back with status 'conflict', so the client can warn instead of
-- silently overwriting. p_force overwrites after the user chose "keep this device". Security
-- invoker: every read and write goes through the RLS policies above.
create function public.push_save(
  p_child uuid, p_data jsonb, p_version int, p_base timestamptz default null, p_force boolean default false
) returns table (status text, updated_at timestamptz, data jsonb, schema_version int)
language plpgsql security invoker set search_path = '' as $$
declare cur public.saves;
begin
  select * into cur from public.saves where child_id = p_child for update;
  if not found then
    insert into public.saves (child_id, data, schema_version) values (p_child, p_data, p_version)
      returning 'ok', saves.updated_at, null::jsonb, saves.schema_version into status, updated_at, data, schema_version;
    return next; return;
  end if;
  if p_force or (p_base is not null and cur.updated_at = p_base) then
    update public.saves s set data = p_data, schema_version = p_version where s.child_id = p_child
      returning 'ok', s.updated_at, null::jsonb, s.schema_version into status, updated_at, data, schema_version;
    return next; return;
  end if;
  status := 'conflict'; updated_at := cur.updated_at; data := cur.data; schema_version := cur.schema_version;
  return next;
end $$;
revoke execute on function public.push_save(uuid, jsonb, int, timestamptz, boolean) from public, anon;
grant execute on function public.push_save(uuid, jsonb, int, timestamptz, boolean) to authenticated;

-- ---------------------------------------------------------------- PIN lockout (service role only)

-- Returns the lock expiry if the key is currently locked, else null.
create function public.pin_locked_until(p_key text) returns timestamptz
language sql stable security definer set search_path = '' as $$
  select locked_until from private.pin_attempts where key = p_key and locked_until > now()
$$;

-- Count one wrong try. Fails older than the lock window start a new count; reaching p_max locks the
-- key for p_lock. Atomic per key. Returns (fails, locked_until).
create function public.pin_record_failure(p_key text, p_max int default 5, p_lock interval default '15 minutes')
returns table (fails int, locked_until timestamptz)
language plpgsql security definer set search_path = '' as $$
declare cur private.pin_attempts; n int;
begin
  insert into private.pin_attempts (key) values (p_key) on conflict (key) do nothing;
  select * into cur from private.pin_attempts where key = p_key for update;
  if cur.updated_at < now() - p_lock or (cur.locked_until is not null and cur.locked_until <= now()) then
    n := 1;
  else
    n := cur.fails + 1;
  end if;
  update private.pin_attempts a
     set fails = n, updated_at = now(),
         locked_until = case when n >= p_max then now() + p_lock else null end
   where a.key = p_key
  returning a.fails, a.locked_until into fails, locked_until;
  return next;
end $$;

create function public.pin_clear(p_keys text[]) returns void
language sql security definer set search_path = '' as $$
  delete from private.pin_attempts where key = any (p_keys)
$$;

revoke execute on function public.pin_locked_until(text), public.pin_record_failure(text, int, interval),
  public.pin_clear(text[]) from public, anon, authenticated;
grant execute on function public.pin_locked_until(text), public.pin_record_failure(text, int, interval),
  public.pin_clear(text[]) to service_role;
