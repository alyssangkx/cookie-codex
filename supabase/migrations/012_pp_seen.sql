-- Cookie Codex, migration 012: a parent sees the past-paper questions their own child was given (owner, 23 Nov 2026:
-- the parent page shows every question the child attempted and every mistake, with its pictures).
-- Apply with:  supabase db query --remote --yes -f supabase/migrations/012_pp_seen.sql   (never `db push`).
-- Test: scripts/accounts/sqltest.sh applies it after 011 and runs test_pp_seen.sql.
--
-- The lockdown (ADR 0012, migration 007) stays: there is still no bulk read. A grown-up reads only items the server
-- itself served that child (private.pp_served, written by pp_serve under its daily limits), never ids taken from the
-- save, which a parent can write. So a parent sees exactly the questions their child has already been shown.
--   * public.pp_seen(p_child): those items' text, key and figure paths, for the child's parent or the admin at aal2.
--   * storage policy pp_figures_seen: signed URLs for exactly those items' pictures (pp-figures stays unlistable).

begin;

create function private.may_see_child(p_child uuid) returns boolean
language sql stable security definer set search_path = '' as $$
  select private.owns_child(p_child)
      or (private.is_admin() and coalesce(auth.jwt() ->> 'aal', '') = 'aal2')
$$;
revoke execute on function private.may_see_child(uuid) from public, anon;
grant execute on function private.may_see_child(uuid) to authenticated;

create function public.pp_seen(p_child uuid)
returns table (id text, subtopic text, level text, stem text, options jsonb, answer smallint, figures jsonb, grp text, seq int)
language plpgsql stable security definer set search_path = '' as $$
begin
  if p_child is null or not private.may_see_child(p_child) then
    raise exception 'not allowed' using errcode = '42501';
  end if;
  return query
    select i.id, i.subtopic, i.level, i.stem, i.options, i.answer, i.figures, i.grp, i.seq
      from public.pp_items i
     where exists (select 1 from private.pp_served s where s.user_id = p_child and s.item_id = i.id)
     order by i.subtopic, i.grp nulls first, i.seq, i.id;
end $$;
revoke execute on function public.pp_seen(uuid) from public, anon;
grant execute on function public.pp_seen(uuid) to authenticated;

-- a picture is visible when it belongs to an item served to a child this grown-up may see
create function private.pp_fig_seen(p_name text) returns boolean
language sql stable security definer set search_path = '' as $$
  select exists (
    select 1 from private.pp_served s join public.pp_items i on i.id = s.item_id
     where private.may_see_child(s.user_id)
       and i.figures @> jsonb_build_array(jsonb_build_object('path', p_name)))
$$;
revoke execute on function private.pp_fig_seen(text) from public, anon;
grant execute on function private.pp_fig_seen(text) to authenticated;

create policy pp_figures_seen on storage.objects for select to authenticated
  using (bucket_id = 'pp-figures' and private.pp_fig_seen(name));

commit;
