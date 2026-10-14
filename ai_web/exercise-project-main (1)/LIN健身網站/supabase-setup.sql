-- ============================================================
-- Lin AI 好友排行榜：資料庫設定
-- 用法：Supabase 專案左邊選單 → SQL Editor → New query
--       把這整份貼上，按 Run（只要做一次）。看到 Success 就完成。
-- ============================================================

-- 1. 兩張表：個人資料、好友關係
create table if not exists public.lin_profiles (
  id          uuid primary key,
  code        text not null unique,
  name        text not null,
  reps        integer not null default 0,
  xp          integer not null default 0,
  streak      integer not null default 0,
  week_reps   integer not null default 0,
  week_key    text not null default '',
  updated_at  timestamptz not null default now()
);

create table if not exists public.lin_friends (
  owner       uuid not null references public.lin_profiles(id) on delete cascade,
  friend      uuid not null references public.lin_profiles(id) on delete cascade,
  created_at  timestamptz not null default now(),
  primary key (owner, friend),
  constraint lin_friends_not_self check (owner <> friend)
);

-- 2. 鎖住資料表：不建立任何 policy，網站不能直接讀寫資料表，
--    只能透過下面幾個函式（函式裡有檢查），所以不會有人能列出所有使用者。
alter table public.lin_profiles enable row level security;
alter table public.lin_friends  enable row level security;

-- 3. 建立或更新自己的資料，回傳好友代碼
create or replace function public.lin_upsert_profile(
  p_id uuid, p_name text, p_reps integer, p_xp integer,
  p_streak integer, p_week integer, p_week_key text
) returns text
language plpgsql
security definer
set search_path = public
as $$
declare
  v_name  text := left(btrim(coalesce(p_name, '')), 12);
  v_reps  integer := least(greatest(coalesce(p_reps, 0), 0), 10000000);
  v_xp    integer := least(greatest(coalesce(p_xp, 0), 0), 100000000);
  v_str   integer := least(greatest(coalesce(p_streak, 0), 0), 100000);
  v_week  integer := least(greatest(coalesce(p_week, 0), 0), 1000000);
  v_wk    text := left(coalesce(p_week_key, ''), 10);
  v_old   public.lin_profiles%rowtype;
  v_code  text;
  v_try   integer := 0;
  i       integer;
begin
  if p_id is null then
    raise exception 'id required';
  end if;
  if char_length(v_name) < 1 then
    raise exception 'name required';
  end if;

  select * into v_old from public.lin_profiles where id = p_id;

  if found then
    -- 簡單防作弊：一次更新，累計次數最多只能增加 2 萬
    v_reps := least(v_reps, v_old.reps + 20000);
    update public.lin_profiles
       set name = v_name, reps = v_reps, xp = v_xp, streak = v_str,
           week_reps = v_week, week_key = v_wk, updated_at = now()
     where id = p_id;
    return v_old.code;
  end if;

  loop
    v_code := '';
    for i in 1..6 loop
      v_code := v_code || substr('ABCDEFGHJKLMNPQRSTUVWXYZ23456789', 1 + floor(random() * 32)::integer, 1);
    end loop;
    exit when not exists (select 1 from public.lin_profiles where code = v_code);
    v_try := v_try + 1;
    if v_try > 20 then
      raise exception 'code generation failed';
    end if;
  end loop;

  insert into public.lin_profiles (id, code, name, reps, xp, streak, week_reps, week_key)
  values (p_id, v_code, v_name, least(v_reps, 20000), v_xp, v_str, v_week, v_wk);
  return v_code;
end;
$$;

-- 4. 用好友代碼互加好友（雙方都會出現在對方的名單）
create or replace function public.lin_add_friend(p_id uuid, p_code text)
returns text
language plpgsql
security definer
set search_path = public
as $$
declare
  v_friend public.lin_profiles%rowtype;
  v_code   text := upper(regexp_replace(coalesce(p_code, ''), '[^A-Za-z0-9]', '', 'g'));
begin
  if not exists (select 1 from public.lin_profiles where id = p_id) then
    raise exception 'profile required';
  end if;

  select * into v_friend from public.lin_profiles where code = v_code;
  if not found then
    raise exception 'not found';
  end if;
  if v_friend.id = p_id then
    raise exception 'self';
  end if;
  if (select count(*) from public.lin_friends where owner = p_id) >= 100 then
    raise exception 'too many friends';
  end if;

  insert into public.lin_friends (owner, friend)
  values (p_id, v_friend.id), (v_friend.id, p_id)
  on conflict do nothing;

  return v_friend.name;
end;
$$;

-- 5. 取得「我 + 我的好友」的排行資料（看不到任何人的 id）
create or replace function public.lin_get_board(p_id uuid)
returns table (
  code text, name text, reps integer, xp integer, streak integer,
  week_reps integer, week_key text, updated_at timestamptz, is_me boolean
)
language sql
stable
security definer
set search_path = public
as $$
  select p.code, p.name, p.reps, p.xp, p.streak, p.week_reps, p.week_key, p.updated_at,
         (p.id = p_id) as is_me
    from public.lin_profiles p
   where p.id = p_id
      or p.id in (select f.friend from public.lin_friends f where f.owner = p_id);
$$;

-- 6. 刪除好友（雙方的名單都會移除）
create or replace function public.lin_remove_friend(p_id uuid, p_code text)
returns void
language plpgsql
security definer
set search_path = public
as $$
declare
  v_fid uuid;
begin
  select id into v_fid from public.lin_profiles
   where code = upper(regexp_replace(coalesce(p_code, ''), '[^A-Za-z0-9]', '', 'g'));
  if v_fid is null then
    return;
  end if;
  delete from public.lin_friends
   where (owner = p_id and friend = v_fid) or (owner = v_fid and friend = p_id);
end;
$$;

-- 7. 刪除我自己的所有資料
create or replace function public.lin_delete_me(p_id uuid)
returns void
language plpgsql
security definer
set search_path = public
as $$
begin
  delete from public.lin_profiles where id = p_id;
end;
$$;

-- 8. 開放網站呼叫這幾個函式（只有函式，沒有資料表）
revoke all on function public.lin_upsert_profile(uuid, text, integer, integer, integer, integer, text) from public;
revoke all on function public.lin_add_friend(uuid, text) from public;
revoke all on function public.lin_get_board(uuid) from public;
revoke all on function public.lin_remove_friend(uuid, text) from public;
revoke all on function public.lin_delete_me(uuid) from public;

grant execute on function public.lin_upsert_profile(uuid, text, integer, integer, integer, integer, text) to anon, authenticated;
grant execute on function public.lin_add_friend(uuid, text) to anon, authenticated;
grant execute on function public.lin_get_board(uuid) to anon, authenticated;
grant execute on function public.lin_remove_friend(uuid, text) to anon, authenticated;
grant execute on function public.lin_delete_me(uuid) to anon, authenticated;

-- 9. 讓 Supabase 立刻認得新函式
notify pgrst, 'reload schema';
