-- Cookie Codex accounts, migration 003: remove the family code (owner's decision, 20 Nov 2026).
-- A child logs in with a username and a 4-digit PIN on any device. Usernames are unique across the whole site
-- (a parent picking a taken one is told so), and may now contain digits (Emma2). Applied together with the
-- pin-login / parent-api / admin versions that no longer read families.code (docs/accounts-plan.md 12.14).
-- What stays from 002: families (consent record, 7-day delete), unlimited flag, guard trigger, push_save gate,
-- rate_hit, purge jobs.

-- ---------------------------------------------------------------- usernames: site-wide, letters and digits
-- A soft-deleted child keeps its name for the 7-day undo window, then the purge frees it.
drop index public.profiles_family_name_uq;
create unique index profiles_name_key_uq on public.profiles (name_key) where role = 'child';

-- the name check from 001, widened to digits after the first letter (same rule in pin-login, parent-api, admin)
alter table public.profiles drop constraint profiles_name_check;
alter table public.profiles add constraint profiles_name_check check (btrim(name) ~ '^[A-Za-z][A-Za-z0-9 -]{0,19}$');

-- ---------------------------------------------------------------- family code gone
alter table public.families drop column code;
drop function private.gen_family_code();
revoke all on public.families from anon, authenticated;
grant select (parent_id, consent_version, consented_at, deleted_at) on public.families to authenticated;

-- ---------------------------------------------------------------- lock keys back to the username
-- pin-login counts 'name:<name_key>' / 'trust:<name_key>' again (as in 001). Keys of the 002 form
-- ('name:<parent_id>:<name_key>') are dead from now on; this removes them.
create or replace function public.pin_clear_name_lock(p_child uuid) returns void
language plpgsql security definer set search_path = '' as $$
declare k text;
begin
  if not (private.is_admin() or private.owns_child(p_child)) then
    raise exception 'owner only' using errcode = '42501';
  end if;
  select p.name_key into k from public.profiles p where p.id = p_child;
  if k is null then return; end if;
  delete from private.pin_attempts where key in ('name:' || k, 'trust:' || k);
end $$;
revoke execute on function public.pin_clear_name_lock(uuid) from public, anon;
grant execute on function public.pin_clear_name_lock(uuid) to authenticated, service_role;

delete from private.pin_attempts where key ~ '^(name|trust):[0-9a-f-]{36}:';

-- purge_deleted no longer has family-scoped lock rows to clean
create or replace function private.purge_deleted() returns void
language sql security definer set search_path = '' as $$
  delete from auth.users u using public.profiles p
   where u.id = p.id and p.role = 'child'
     and (p.deleted_at < now() - interval '7 days'
          or exists (select 1 from public.families f
                      where f.parent_id = p.parent_id and f.deleted_at < now() - interval '7 days'));
  delete from auth.users u using public.families f
   where u.id = f.parent_id and f.deleted_at < now() - interval '7 days';
$$;
revoke execute on function private.purge_deleted() from public, anon, authenticated;
