-- Cookie Codex, migration 005: "Report a problem with this question" (owner, 21 Nov 2026).  NOT YET APPLIED.
-- Apply with:  supabase db query --remote --yes -f supabase/migrations/005_question_reports.sql   (never `db push`).
-- Test: scripts/accounts/sqltest.sh runs 001-005 locally.
--
-- What it adds:
--   * public.question_reports: one row per (question, reporter): the question id the quiz showed (a generated id or a
--     pp-<10 hex> past-paper id; pp_items.src_id leads back to the paper and page), what looks wrong, an optional note.
--     No client may read or write the table directly (RLS on, no policies, no grants). A deleted account's reports go
--     with it (on delete cascade). Nothing here contains question content.
--   * public.report_question(qid, kind, note): the only write path. Signed-in child (incl. the Test Player) or the admin,
--     the same readers as pp_items_for (private.can_read_pp, 004); a second report of the same question by the same
--     child replaces the first; at most 30 reports per user per day.
-- Read the open reports (admin, from a terminal):
--   select r.created_at, r.qid, i.src_id, r.kind, r.note from public.question_reports r
--     left join public.pp_items i on i.id = r.qid where r.resolved_at is null order by r.created_at;
-- then `python3 scripts/pastpapers/load_pp.py where <qid>` prints the paper, page and crop.

begin;

create table public.question_reports (
  id          bigint generated always as identity primary key,
  qid         text not null check (qid ~ '^[a-z0-9-]{3,60}$'),
  reporter    uuid not null references auth.users (id) on delete cascade,
  kind        text not null check (kind in ('picture', 'answer', 'question', 'other')),
  note        text check (length(note) <= 300),
  created_at  timestamptz not null default now(),
  resolved_at timestamptz,
  unique (qid, reporter)
);

alter table public.question_reports enable row level security;
revoke all on public.question_reports from public, anon, authenticated;
grant all on public.question_reports to service_role;

create function public.report_question(p_qid text, p_kind text, p_note text default null)
returns void
language plpgsql security definer set search_path = '' as $$
begin
  if not private.can_read_pp() then
    raise exception 'not allowed' using errcode = '42501';
  end if;
  if not public.rate_hit('rq:' || auth.uid()::text, 30, interval '1 day') then
    raise exception 'too many requests' using errcode = '53400';
  end if;
  insert into public.question_reports (qid, reporter, kind, note)
  values (p_qid, auth.uid(), p_kind, nullif(btrim(p_note), ''))
  on conflict (qid, reporter) do update
    set kind = excluded.kind, note = excluded.note, created_at = now(), resolved_at = null;
end $$;
revoke execute on function public.report_question(text, text, text) from public, anon;
grant execute on function public.report_question(text, text, text) to authenticated;

commit;
