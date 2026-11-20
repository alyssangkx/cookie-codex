-- Minimal stand-in for Supabase Storage's tables (for 004 in sqltest.sh): the bucket row and object rows with RLS on,
-- as on the real project. Not an emulator: no signing, no HTTP.
create schema storage;
create table storage.buckets (
  id text primary key, name text not null, public boolean default false, file_size_limit bigint, allowed_mime_types text[]
);
create table storage.objects (
  id uuid primary key default gen_random_uuid(), bucket_id text references storage.buckets (id), name text, owner uuid
);
alter table storage.objects enable row level security;
grant usage on schema storage to anon, authenticated, service_role;
grant select on storage.objects to anon, authenticated;
grant all on storage.objects, storage.buckets to service_role;
