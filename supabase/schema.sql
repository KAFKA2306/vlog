-- Add image_url to novels if not exists
alter table novels add column if not exists image_url text;

-- Create bucket if not exists
insert into storage.buckets (id, name, public)
values ('vlog-photos', 'vlog-photos', true)
on conflict (id) do nothing;

-- Enable Row Level Security (idempotent)
alter table daily_entries enable row level security;
alter table novels enable row level security;

-- Policies
do $$
begin
  -- Daily Entries Policies
  if not exists (select 1 from pg_policies where tablename = 'daily_entries' and policyname = 'Public entries are viewable by everyone') then
    create policy "Public entries are viewable by everyone" on daily_entries for select using (is_public = true);
  end if;

  if not exists (select 1 from pg_policies where tablename = 'daily_entries' and policyname = 'Service role can do everything on daily_entries') then
    create policy "Service role can do everything on daily_entries" on daily_entries for all using (true) with check (true);
  end if;

  -- Novels Policies
  if not exists (select 1 from pg_policies where tablename = 'novels' and policyname = 'Public novels are viewable by everyone') then
    create policy "Public novels are viewable by everyone" on novels for select using (is_public = true);
  end if;

  if not exists (select 1 from pg_policies where tablename = 'novels' and policyname = 'Service role can do everything on novels') then
    create policy "Service role can do everything on novels" on novels for all using (true) with check (true);
  end if;

  -- Storage Policies
  if not exists (select 1 from pg_policies where tablename = 'objects' and policyname = 'Photos are viewable by everyone') then
    create policy "Photos are viewable by everyone" on storage.objects for select using (bucket_id = 'vlog-photos');
  end if;
  
  if not exists (select 1 from pg_policies where tablename = 'objects' and policyname = 'Service role can upload photos') then
    create policy "Service role can upload photos" on storage.objects for insert with check (bucket_id = 'vlog-photos');
  end if;
  
  if not exists (select 1 from pg_policies where tablename = 'objects' and policyname = 'Service role can update photos') then
    create policy "Service role can update photos" on storage.objects for update using (bucket_id = 'vlog-photos');
  end if;
end
$$;
