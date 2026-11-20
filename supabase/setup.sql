-- U STOLU · Supabase setup (run once in SQL Editor as project owner)
-- Public library; per-user private favorites; only manually appointed admin can change recipes/photos.
-- NEVER include a service_role key in your website, repository, or browser code.

create table if not exists public.admin_users (
  user_id uuid primary key references auth.users(id) on delete cascade,
  granted_at timestamptz not null default now()
);

create table if not exists public.favorites (
  user_id uuid not null references auth.users(id) on delete cascade,
  recipe_id text not null check (recipe_id ~ '^[a-z0-9][a-z0-9-]{2,79}$'),
  added_at timestamptz not null default now(),
  primary key (user_id, recipe_id)
);

create index if not exists favorites_recipe_idx on public.favorites (recipe_id);

create table if not exists public.recipes (
  id text primary key check (id ~ '^[a-z0-9][a-z0-9-]{2,79}$'),
  body jsonb not null,
  image_url text,
  updated_at timestamptz not null default now(),
  constraint recipe_body_valid check (
    coalesce(jsonb_typeof(body) = 'object'
    and body ? 'id'
    and body ? 'title'
    and body ? 'category'
    and body ? 'protein'
    and body ? 'ingredients'
    and body ? 'steps'
    and body ->> 'id' = id
    and body ->> 'category' in ('breakfast', 'lunch', 'dinner')
    and body ->> 'protein' in ('meat', 'vegetarian')
    and jsonb_typeof(body -> 'ingredients') = 'array'
    and jsonb_typeof(body -> 'steps') = 'array'
    and length(body ->> 'title') between 1 and 160
    and length(body::text) < 200000, false)
  )
);

create or replace function public.set_recipe_modified_time()
returns trigger language plpgsql set search_path = '' as $$
begin
  new.updated_at := now();
  return new;
end $$;

drop trigger if exists set_recipe_modified_time on public.recipes;
create trigger set_recipe_modified_time before update on public.recipes
for each row execute function public.set_recipe_modified_time();

alter table public.admin_users enable row level security;
alter table public.favorites enable row level security;
alter table public.recipes enable row level security;

-- Explicit grants: roles are resolved in DB, never from user-editable profile metadata.
revoke all on public.admin_users from anon, authenticated;
revoke all on public.favorites from anon, authenticated;
revoke all on public.recipes from anon, authenticated;
grant select on public.admin_users to authenticated;
grant select, insert, delete on public.favorites to authenticated;
grant select on public.recipes to anon, authenticated;
grant insert, update on public.recipes to authenticated;

-- Admin membership is NOT editable via public Data API.
drop policy if exists "User reads only their admin membership" on public.admin_users;
create policy "User reads only their admin membership" on public.admin_users
for select to authenticated using ((select auth.uid()) = user_id);

-- A normal user can see/insert/delete only their own favorites.
drop policy if exists "User sees own favorites" on public.favorites;
create policy "User sees own favorites" on public.favorites
for select to authenticated using ((select auth.uid()) = user_id);
drop policy if exists "User adds own favorites" on public.favorites;
create policy "User adds own favorites" on public.favorites
for insert to authenticated with check ((select auth.uid()) = user_id);
drop policy if exists "User removes own favorites" on public.favorites;
create policy "User removes own favorites" on public.favorites
for delete to authenticated using ((select auth.uid()) = user_id);

-- All visitors can see public recipes, but only an explicitly appointed admin can edit.
drop policy if exists "Anyone reads public recipes" on public.recipes;
create policy "Anyone reads public recipes" on public.recipes
for select to anon, authenticated using (true);
drop policy if exists "Admin creates recipes" on public.recipes;
create policy "Admin creates recipes" on public.recipes
for insert to authenticated
with check (exists (select 1 from public.admin_users where user_id = (select auth.uid())));
drop policy if exists "Admin updates recipes" on public.recipes;
create policy "Admin updates recipes" on public.recipes
for update to authenticated
using (exists (select 1 from public.admin_users where user_id = (select auth.uid())))
with check (exists (select 1 from public.admin_users where user_id = (select auth.uid())));

-- A public bucket: photographs are visible to everybody, uploads are ADMIN-ONLY.
insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values ('recipe-images', 'recipe-images', true, 6291456,
        array['image/png','image/jpeg','image/webp'])
on conflict (id) do update set
  public = excluded.public,
  file_size_limit = excluded.file_size_limit,
  allowed_mime_types = excluded.allowed_mime_types;

drop policy if exists "Admin uploads recipe photos" on storage.objects;
create policy "Admin uploads recipe photos" on storage.objects
for insert to authenticated
with check (bucket_id = 'recipe-images' and
  exists (select 1 from public.admin_users where user_id = (select auth.uid())));

drop policy if exists "Admin updates recipe photos" on storage.objects;
create policy "Admin updates recipe photos" on storage.objects
for update to authenticated
using (bucket_id = 'recipe-images' and
  exists (select 1 from public.admin_users where user_id = (select auth.uid())))
with check (bucket_id = 'recipe-images' and
  exists (select 1 from public.admin_users where user_id = (select auth.uid())));

drop policy if exists "Admin removes recipe photos" on storage.objects;
create policy "Admin removes recipe photos" on storage.objects
for delete to authenticated
using (bucket_id = 'recipe-images' and
  exists (select 1 from public.admin_users where user_id = (select auth.uid())));

-- IMPORTANT: No INSERT/UPDATE/DELETE grant to clients on admin_users.
-- After you create & verify YOUR OWN account, appoint it manually in SQL Editor:
-- insert into public.admin_users (user_id)
-- select id from auth.users where email = 'TVUJ-EMAIL@DOMENA.CZ' and email_confirmed_at is not null
-- on conflict (user_id) do nothing;
