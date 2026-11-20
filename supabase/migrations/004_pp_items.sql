-- Cookie Codex, migration 004: private past-paper MCQs (ADR 0004, amended 20 Nov 2026).  APPLIED to the live project 20 Nov 2026.
-- It was applied with:  supabase db query --remote --yes -f supabase/migrations/004_pp_items.sql
-- (there is no migrations table; never `db push`). Do not re-run it. Test: scripts/accounts/sqltest.sh runs 001-004 locally.
--
-- What it adds:
--   * public.pp_items: verbatim past-paper MCQs that passed the blind-answer check. No client may select the table
--     directly (RLS on, no policies, no grants); rows are written only by the service role (scripts/pastpapers/load_pp.py).
--   * public.pp_items_for(subject, subtopics[]): the only read path. Signed-in child (incl. the Test Player) or
--     the admin only (owner, 20 Nov 2026): no parent role, no anon; at most 40 sub-topics per call and 120 calls per
--     user per hour.
--   * Storage bucket pp-figures (private) for the WebP crops. The same readers may select objects there, which is
--     what supabase-js createSignedUrls() needs; nobody but the service role may write.
-- Nothing in this file contains past-paper content.

begin;

create table public.pp_items (
  id          text primary key check (id ~ '^pp-[0-9a-f]{10}$'),      -- pp-<sha1(source question id)[:10]>
  src_id      text not null unique,                                  -- the private repository's question id
  subject     text not null check (subject in ('maths', 'science', 'english', 'chinese')),
  subtopic    text not null check (subtopic ~ '^[a-z0-9-]{3,80}$'),  -- an id from site/src/data/syllabus/<subject>.json
  level       text not null check (level in ('basic', 'intermediate', 'competent')),
  pattern     text,
  stem        text not null check (length(stem) between 1 and 4000),
  options     jsonb not null check (jsonb_typeof(options) = 'array' and jsonb_array_length(options) = 4),
  answer      smallint not null check (answer between 0 and 3),      -- index into options (the paper's (1)-(4) order)
  figures     jsonb not null default '[]' check (jsonb_typeof(figures) = 'array'),  -- [{path, w, h}] in pp-figures
  year        smallint check (year between 2000 and 2100),
  school      text,
  paper       text,
  qno         smallint,
  marks       numeric,
  blind_src   text not null,                                         -- which blind-check pass agreed with the key
  active      boolean not null default true,                         -- false = withdrawn (kept so saves still resolve)
  loaded_at   timestamptz not null default now()
);
create index pp_items_sub_idx on public.pp_items (subject, subtopic) where active;

alter table public.pp_items enable row level security;
revoke all on public.pp_items from public, anon, authenticated;
grant all on public.pp_items to service_role;

-- ---------------------------------------------------------------- who may read

-- A signed-in child or Test Player whose profile and family are not deleted, or the admin. NOT a parent (owner,
-- 20 Nov 2026: sign-up is open, so a parent account must not open the papers). Children have their own auth users
-- (001), so auth.uid() is the profile id; a parent's uid is never a profile id.
create function private.can_read_pp() returns boolean
language sql stable security definer set search_path = '' as $$
  select auth.uid() is not null and (
       exists (select 1 from public.profiles p left join public.families f on f.parent_id = p.parent_id
                where p.id = auth.uid() and p.deleted_at is null and f.deleted_at is null)
    or coalesce(auth.jwt() -> 'app_metadata' ->> 'role', '') = 'admin')
$$;
revoke execute on function private.can_read_pp() from public, anon;
grant execute on function private.can_read_pp() to authenticated;

-- The one read path. Volatile because rate_hit writes. Returns no school/paper/qno: the site shows only
-- "Past paper <year>" (owner, 20 Nov 2026).
create function public.pp_items_for(p_subject text, p_subtopics text[])
returns table (id text, subtopic text, level text, pattern text, stem text, options jsonb, answer smallint,
               figures jsonb, year smallint)
language plpgsql security definer set search_path = '' as $$
begin
  if not private.can_read_pp() then
    raise exception 'not allowed' using errcode = '42501';
  end if;
  if coalesce(cardinality(p_subtopics), 0) not between 1 and 40 then
    raise exception 'bad request' using errcode = '22023';
  end if;
  if not public.rate_hit('pp:' || auth.uid()::text, 120, interval '1 hour') then
    raise exception 'too many requests' using errcode = '53400';
  end if;
  return query
    select i.id, i.subtopic, i.level, i.pattern, i.stem, i.options, i.answer, i.figures, i.year
      from public.pp_items i
     where i.active and i.subject = p_subject and i.subtopic = any (p_subtopics)
     order by i.id
     limit 4000;
end $$;
revoke execute on function public.pp_items_for(text, text[]) from public, anon;
grant execute on function public.pp_items_for(text, text[]) to authenticated;

-- ---------------------------------------------------------------- figures: private Storage bucket

insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values ('pp-figures', 'pp-figures', false, 204800, array['image/webp'])
on conflict (id) do update
  set public = false, file_size_limit = excluded.file_size_limit, allowed_mime_types = excluded.allowed_mime_types;

-- Readers may create signed URLs (and download) objects in this bucket; no insert/update/delete policy, so only the
-- service role (the loader) writes. A signed URL is a bearer link until it expires: the site asks for 2 hours.
create policy pp_figures_read on storage.objects for select to authenticated
  using (bucket_id = 'pp-figures' and (select private.can_read_pp()));

commit;
