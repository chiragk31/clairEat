-- ============================================================
-- ClairEat — Full Supabase Schema Migration
-- Run these in order in your Supabase SQL editor.
-- ============================================================

-- 001 — Profiles (extends Supabase Auth users)
create table if not exists public.profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  username text unique,
  full_name text,
  age integer,
  gender text check (gender in ('male', 'female', 'other', 'prefer_not_to_say')),
  height_cm float,
  weight_kg float,
  target_weight_kg float,
  activity_level text check (activity_level in ('sedentary', 'light', 'moderate', 'active', 'very_active')),
  health_goals text[] default '{}',
  dietary_restrictions text[] default '{}',
  allergies text[] default '{}',
  daily_calorie_target integer,
  daily_protein_target_g float,
  daily_carb_target_g float,
  daily_fat_target_g float,
  timezone text default 'UTC',
  location_city text,
  onboarding_complete boolean default false,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

-- 002 — TDEE Calculations
create table if not exists public.tdee_calculations (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references profiles(id) on delete cascade,
  bmr float,
  tdee float,
  goal_calories float,
  formula_used text default 'mifflin_st_jeor',
  calculated_at timestamptz default now()
);

-- 003 — Food Items (external API cache)
create table if not exists public.food_items (
  id uuid primary key default gen_random_uuid(),
  external_id text,
  source text,
  name text not null,
  brand text,
  barcode text unique,
  serving_size_g float,
  serving_unit text,
  calories_per_100g float,
  protein_per_100g float,
  carbs_per_100g float,
  fat_per_100g float,
  fiber_per_100g float,
  sugar_per_100g float,
  sodium_per_100g float,
  vitamins jsonb default '{}',
  minerals jsonb default '{}',
  nutriscore text,
  nova_group integer,
  ingredients text,
  allergens text[] default '{}',
  image_url text,
  is_verified boolean default false,
  created_at timestamptz default now(),
  unique (external_id, source)
);

create index if not exists idx_food_items_barcode on food_items(barcode);
create index if not exists idx_food_items_name on food_items using gin(to_tsvector('english', name));

-- 004 — User Foods (favourites / custom)
create table if not exists public.user_foods (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references profiles(id) on delete cascade,
  food_item_id uuid references food_items(id),
  custom_name text,
  custom_serving_size_g float,
  is_favorite boolean default false,
  times_logged integer default 0,
  created_at timestamptz default now()
);

-- 005 — Meal Type Enum
do $$ begin
  create type meal_type as enum (
    'breakfast', 'lunch', 'dinner', 'snack', 'pre_workout', 'post_workout'
  );
exception when duplicate_object then null;
end $$;

-- 006 — Meal Logs
create table if not exists public.meal_logs (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references profiles(id) on delete cascade,
  logged_at timestamptz default now(),
  meal_date date not null,
  meal_type meal_type not null,
  total_calories float default 0,
  total_protein_g float default 0,
  total_carbs_g float default 0,
  total_fat_g float default 0,
  total_fiber_g float default 0,
  mood_before text,
  mood_after text,
  hunger_level_before integer check (hunger_level_before between 1 and 10),
  fullness_level_after integer check (fullness_level_after between 1 and 10),
  location text,
  notes text,
  ai_meal_score float,
  ai_feedback text,
  image_url text
);

create index if not exists idx_meal_logs_user_date on meal_logs(user_id, meal_date);

-- 007 — Meal Log Items
create table if not exists public.meal_log_items (
  id uuid primary key default gen_random_uuid(),
  meal_log_id uuid references meal_logs(id) on delete cascade,
  food_item_id uuid references food_items(id),
  custom_food_name text,
  quantity_g float not null,
  calories float not null default 0,
  protein_g float,
  carbs_g float,
  fat_g float,
  fiber_g float,
  created_at timestamptz default now()
);

-- 008 — Meal Plans
create table if not exists public.meal_plans (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references profiles(id) on delete cascade,
  plan_name text,
  start_date date,
  end_date date,
  is_active boolean default true,
  target_calories integer,
  generated_by text default 'gemini',
  generation_context jsonb,
  created_at timestamptz default now()
);

-- 009 — Meal Plan Entries
create table if not exists public.meal_plan_entries (
  id uuid primary key default gen_random_uuid(),
  meal_plan_id uuid references meal_plans(id) on delete cascade,
  day_of_week integer check (day_of_week between 1 and 7),
  meal_type meal_type,
  recipe_name text,
  recipe_description text,
  estimated_calories integer,
  estimated_protein_g float,
  estimated_carbs_g float,
  estimated_fat_g float,
  ingredients jsonb default '[]',
  preparation_steps text[] default '{}',
  prep_time_minutes integer,
  external_recipe_id text,
  created_at timestamptz default now()
);

-- 010 — Habits
create table if not exists public.habits (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references profiles(id) on delete cascade,
  habit_name text not null,
  habit_type text check (habit_type in ('water_intake', 'meal_timing', 'vegetable_serving', 'sugar_limit', 'custom')),
  target_value float,
  target_unit text,
  frequency text default 'daily',
  reminder_times time[] default '{}',
  is_active boolean default true,
  created_at timestamptz default now()
);

-- 011 — Habit Logs
create table if not exists public.habit_logs (
  id uuid primary key default gen_random_uuid(),
  habit_id uuid references habits(id) on delete cascade,
  user_id uuid references profiles(id) on delete cascade,
  log_date date not null,
  value_achieved float,
  is_completed boolean default false,
  logged_at timestamptz default now(),
  unique (habit_id, log_date)
);

-- 012 — Streaks
create table if not exists public.streaks (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references profiles(id) on delete cascade,
  habit_id uuid references habits(id) on delete cascade,
  streak_type text,
  current_streak integer default 0,
  longest_streak integer default 0,
  last_activity_date date,
  updated_at timestamptz default now()
);

-- 013 — AI Conversations
create table if not exists public.ai_conversations (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references profiles(id) on delete cascade,
  session_id uuid default gen_random_uuid(),
  role text check (role in ('user', 'assistant')),
  content text not null,
  ai_provider text,
  context_snapshot jsonb,
  tokens_used integer,
  created_at timestamptz default now()
);

create index if not exists idx_ai_conversations_session on ai_conversations(user_id, session_id);

-- 014 — AI Insights
create table if not exists public.ai_insights (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references profiles(id) on delete cascade,
  insight_type text,
  title text,
  content text,
  data jsonb,
  is_read boolean default false,
  valid_until timestamptz,
  created_at timestamptz default now()
);

-- 015 — Water Logs
create table if not exists public.water_logs (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references profiles(id) on delete cascade,
  log_date date not null,
  amount_ml integer not null,
  logged_at timestamptz default now()
);

create index if not exists idx_water_logs_user_date on water_logs(user_id, log_date);

-- ============================================================
-- Row Level Security Policies
-- ============================================================

alter table profiles enable row level security;
alter table tdee_calculations enable row level security;
alter table food_items enable row level security;
alter table user_foods enable row level security;
alter table meal_logs enable row level security;
alter table meal_log_items enable row level security;
alter table meal_plans enable row level security;
alter table meal_plan_entries enable row level security;
alter table habits enable row level security;
alter table habit_logs enable row level security;
alter table streaks enable row level security;
alter table ai_conversations enable row level security;
alter table ai_insights enable row level security;
alter table water_logs enable row level security;

-- Profiles
create policy "Users can view own profile" on profiles for select using (auth.uid() = id);
create policy "Users can update own profile" on profiles for update using (auth.uid() = id);
create policy "Users can insert own profile" on profiles for insert with check (auth.uid() = id);

-- All user-scoped tables: access own rows only
create policy "Own meal_logs" on meal_logs for all using (auth.uid() = user_id);
create policy "Own meal_log_items" on meal_log_items for all using (
  exists (select 1 from meal_logs where meal_logs.id = meal_log_id and meal_logs.user_id = auth.uid())
);
create policy "Own meal_plans" on meal_plans for all using (auth.uid() = user_id);
create policy "Own meal_plan_entries" on meal_plan_entries for all using (
  exists (select 1 from meal_plans where meal_plans.id = meal_plan_id and meal_plans.user_id = auth.uid())
);
create policy "Own habits" on habits for all using (auth.uid() = user_id);
create policy "Own habit_logs" on habit_logs for all using (auth.uid() = user_id);
create policy "Own streaks" on streaks for all using (auth.uid() = user_id);
create policy "Own ai_conversations" on ai_conversations for all using (auth.uid() = user_id);
create policy "Own ai_insights" on ai_insights for all using (auth.uid() = user_id);
create policy "Own water_logs" on water_logs for all using (auth.uid() = user_id);
create policy "Own tdee_calculations" on tdee_calculations for all using (auth.uid() = user_id);
create policy "Own user_foods" on user_foods for all using (auth.uid() = user_id);

-- Food items are public read, service-role write
create policy "Anyone can read food_items" on food_items for select using (true);
