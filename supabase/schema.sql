-- VLog Supabase security contract.
-- Anonymous and authenticated clients may only read rows explicitly marked public.
-- All writes are performed with the service role, which bypasses RLS in Supabase.

alter table public.daily_entries add column if not exists image_url text;
alter table public.novels add column if not exists image_url text;

insert into storage.buckets (id, name, public)
values ('vlog-photos', 'vlog-photos', true)
on conflict (id) do update set public = excluded.public;

alter table public.daily_entries enable row level security;
alter table public.novels enable row level security;

revoke all on table public.daily_entries from anon, authenticated;
revoke all on table public.novels from anon, authenticated;
grant select on table public.daily_entries to anon, authenticated;
grant select on table public.novels to anon, authenticated;

drop policy if exists "Public entries are viewable by everyone" on public.daily_entries;
drop policy if exists "Service role can do everything on daily_entries" on public.daily_entries;
create policy "Public entries are viewable by everyone"
on public.daily_entries
for select
to anon, authenticated
using (is_public = true);

drop policy if exists "Public novels are viewable by everyone" on public.novels;
drop policy if exists "Service role can do everything on novels" on public.novels;
create policy "Public novels are viewable by everyone"
on public.novels
for select
to anon, authenticated
using (is_public = true);

drop policy if exists "Photos are viewable by everyone" on storage.objects;
drop policy if exists "Service role can upload photos" on storage.objects;
drop policy if exists "Service role can update photos" on storage.objects;
create policy "Photos are viewable by everyone"
on storage.objects
for select
to anon, authenticated
using (bucket_id = 'vlog-photos');

create table if not exists public.evaluations (
  id uuid primary key default gen_random_uuid(),
  date date not null,
  target_type text not null,
  score float8 not null,
  reasoning text,
  created_at timestamptz default now(),
  unique(date, target_type)
);

alter table public.evaluations enable row level security;
revoke all on table public.evaluations from anon, authenticated;
drop policy if exists "Service role can do everything on evaluations" on public.evaluations;
