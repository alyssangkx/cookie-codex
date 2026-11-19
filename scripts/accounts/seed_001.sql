-- The live data shape before 002: the admin, Alyssa, the Admin player, the Test Player (fake ids and emails).
insert into auth.users (id, email, email_confirmed_at, raw_app_meta_data) values
  ('00000000-0000-0000-0000-0000000000ad', 'admin@x.test', now(), '{"role":"admin"}'),
  ('00000000-0000-0000-0000-000000000001', 'child-1@children.invalid', now(), '{}'),
  ('00000000-0000-0000-0000-000000000002', 'child-2@children.invalid', now(), '{}'),
  ('00000000-0000-0000-0000-000000000003', 'child-3@children.invalid', now(), '{}');
insert into public.profiles (id, parent_id, name, role) values
  ('00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-0000000000ad', 'Alyssa', 'child'),
  ('00000000-0000-0000-0000-000000000002', '00000000-0000-0000-0000-0000000000ad', 'Admin', 'child'),
  ('00000000-0000-0000-0000-000000000003', '00000000-0000-0000-0000-0000000000ad', 'Test Player', 'test');
insert into private.pin_attempts (key) values ('name:alyssa');
