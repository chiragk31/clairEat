# 🥗 SmartEat — Intelligent Food Choice & Habit Builder
## Detailed Backend Architecture Plan

> **Stack:** FastAPI + Supabase | **AI:** Google Gemini (primary) + Groq (fallback) | **APIs:** Free, no credit card required

---

## 1. PROBLEM ANALYSIS

### Core User Problems
- Users make poor food decisions due to lack of real-time, personalized guidance
- No context-awareness: existing apps don't adapt to mood, time, location, or past behavior
- Habit loops are not reinforced; users abandon nutrition goals within weeks
- Food data is hard to interpret (macros, glycemic index, micronutrients) without AI assistance

### Solution Pillars
1. **Contextual Intelligence** — AI adapts suggestions based on time of day, meal history, health goals, activity level
2. **Behavioral Loop Engine** — Streak tracking, nudges, and pattern analysis to build lasting habits
3. **Real-time Food Intelligence** — Nutrition lookup, barcode scan support, meal scoring
4. **Conversational AI Coach** — Chat-based nutritional advisor using Gemini + Groq fallback
5. **Personalized Meal Planning** — Weekly AI-generated meal plans based on preferences and constraints

---

## 2. SYSTEM ARCHITECTURE OVERVIEW

```
┌─────────────────────────────────────────────────────────────┐
│                        CLIENT (Mobile/Web)                   │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTPS / WebSocket
┌────────────────────────▼────────────────────────────────────┐
│                    FastAPI Backend                           │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────────────┐ │
│  │  Auth Router  │ │  Food Router │ │  AI Coach Router     │ │
│  ├──────────────┤ ├──────────────┤ ├──────────────────────┤ │
│  │  Habit Router │ │  Meal Router │ │  Analytics Router    │ │
│  └──────────────┘ └──────────────┘ └──────────────────────┘ │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │              Service Layer (Business Logic)             │ │
│  │  AI Orchestrator | Habit Engine | Nutrition Calculator  │ │
│  └─────────────────────────────────────────────────────────┘ │
└───────┬──────────────┬────────────────┬───────────────────┬─┘
        │              │                │                   │
┌───────▼──────┐ ┌─────▼──────┐ ┌──────▼──────┐ ┌────────▼────┐
│   Supabase   │ │  Gemini AI │ │  Groq AI    │ │ External    │
│  (Postgres + │ │  (Primary) │ │  (Fallback) │ │ Free APIs   │
│   Storage +  │ └────────────┘ └─────────────┘ └─────────────┘
│   Realtime)  │
└──────────────┘
```

---

## 3. FREE EXTERNAL APIs (No Credit Card Required)

| API | Purpose | Free Tier | Endpoint |
|-----|---------|-----------|----------|
| **Open Food Facts** | Food/barcode database, nutrition data | Unlimited, open source | `world.openfoodfacts.org/api/v2` |
| **Nutritionix** | Natural language food search, restaurant data | 500 req/day free | `api.nutritionix.com/v1_1` |
| **USDA FoodData Central** | Official US nutrition database | Unlimited with free API key | `api.nal.usda.gov/fdc/v1` |
| **Edamam Food DB** | Recipe nutrition analysis | 1000 req/month free | `api.edamam.com/api/food-database/v2` |
| **TheMealDB** | Recipe database with meal categories | Unlimited free | `www.themealdb.com/api/json/v1/1` |
| **Spoonacular** | Meal planning, ingredient parsing | 150 req/day free | `api.spoonacular.com` |
| **Wger Workout** | Exercise & calorie burn data | Unlimited open source | `wger.de/api/v2` |
| **Open Meteo** | Weather for contextual advice | Unlimited free | `api.open-meteo.com/v1` |
| **IPinfo** | User location from IP for local food context | 50K req/month free | `ipinfo.io/json` |
| **Google Gemini** | Primary AI (Flash model) | Free tier available | `generativelanguage.googleapis.com` |
| **Groq** | Fallback AI (LLaMA 3.1) | Free tier with limits | `api.groq.com/openai/v1` |

---

## 4. SUPABASE DATABASE SCHEMA

### 4.1 Users & Profiles

```sql
-- Users (extends Supabase Auth)
create table public.profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  username text unique,
  full_name text,
  age integer,
  gender text check (gender in ('male', 'female', 'other', 'prefer_not_to_say')),
  height_cm float,
  weight_kg float,
  target_weight_kg float,
  activity_level text check (activity_level in ('sedentary', 'light', 'moderate', 'active', 'very_active')),
  health_goals text[] default '{}', -- ['weight_loss', 'muscle_gain', 'maintenance', 'diabetes_control']
  dietary_restrictions text[] default '{}', -- ['vegetarian', 'vegan', 'gluten_free', 'lactose_free']
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

-- Daily calorie targets by formula (stored for reference)
create table public.tdee_calculations (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references profiles(id) on delete cascade,
  bmr float,           -- Basal Metabolic Rate
  tdee float,          -- Total Daily Energy Expenditure
  goal_calories float, -- Adjusted for goal
  formula_used text,   -- 'mifflin_st_jeor' or 'harris_benedict'
  calculated_at timestamptz default now()
);
```

### 4.2 Food & Nutrition

```sql
-- Cached food items from external APIs
create table public.food_items (
  id uuid primary key default gen_random_uuid(),
  external_id text,           -- barcode or API id
  source text,                -- 'open_food_facts', 'usda', 'nutritionix', 'edamam'
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
  vitamins jsonb default '{}', -- { "vitamin_c": 10.5, "vitamin_d": 2.1, ... }
  minerals jsonb default '{}', -- { "iron": 1.2, "calcium": 120, ... }
  nutriscore text,             -- A to E (European nutrition score)
  nova_group integer,          -- 1-4 (food processing level)
  ingredients text,
  allergens text[],
  image_url text,
  is_verified boolean default false,
  created_at timestamptz default now()
);

create index idx_food_items_barcode on food_items(barcode);
create index idx_food_items_name on food_items using gin(to_tsvector('english', name));

-- User's custom food items
create table public.user_foods (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references profiles(id) on delete cascade,
  food_item_id uuid references food_items(id),
  custom_name text,
  custom_serving_size_g float,
  is_favorite boolean default false,
  times_logged integer default 0,
  created_at timestamptz default now()
);
```

### 4.3 Meal Logging

```sql
create type meal_type as enum ('breakfast', 'lunch', 'dinner', 'snack', 'pre_workout', 'post_workout');

create table public.meal_logs (
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
  mood_before text,    -- 'happy', 'stressed', 'tired', 'neutral'
  mood_after text,
  hunger_level_before integer check (hunger_level_before between 1 and 10),
  fullness_level_after integer check (fullness_level_after between 1 and 10),
  location text,
  notes text,
  ai_meal_score float, -- AI-generated quality score 0-100
  ai_feedback text,    -- AI-generated feedback on this meal
  image_url text       -- photo of meal (stored in Supabase Storage)
);

create table public.meal_log_items (
  id uuid primary key default gen_random_uuid(),
  meal_log_id uuid references meal_logs(id) on delete cascade,
  food_item_id uuid references food_items(id),
  custom_food_name text, -- if not in database
  quantity_g float not null,
  calories float not null,
  protein_g float,
  carbs_g float,
  fat_g float,
  fiber_g float,
  created_at timestamptz default now()
);

create index idx_meal_logs_user_date on meal_logs(user_id, meal_date);
```

### 4.4 Meal Plans

```sql
create table public.meal_plans (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references profiles(id) on delete cascade,
  plan_name text,
  start_date date,
  end_date date,
  is_active boolean default true,
  target_calories integer,
  generated_by text default 'gemini',
  generation_context jsonb, -- what context was given to AI
  created_at timestamptz default now()
);

create table public.meal_plan_entries (
  id uuid primary key default gen_random_uuid(),
  meal_plan_id uuid references meal_plans(id) on delete cascade,
  day_of_week integer check (day_of_week between 1 and 7), -- 1=Mon, 7=Sun
  meal_type meal_type,
  recipe_name text,
  recipe_description text,
  estimated_calories integer,
  estimated_protein_g float,
  estimated_carbs_g float,
  estimated_fat_g float,
  ingredients jsonb, -- [{ "name": "chicken breast", "quantity": "150g" }]
  preparation_steps text[],
  prep_time_minutes integer,
  external_recipe_id text,  -- from TheMealDB or Spoonacular
  created_at timestamptz default now()
);
```

### 4.5 Habits & Streaks

```sql
create table public.habits (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references profiles(id) on delete cascade,
  habit_name text not null,
  habit_type text check (habit_type in ('water_intake', 'meal_timing', 'vegetable_serving', 'sugar_limit', 'custom')),
  target_value float,
  target_unit text,     -- 'glasses', 'grams', 'servings', 'times'
  frequency text,       -- 'daily', 'weekly'
  reminder_times time[],
  is_active boolean default true,
  created_at timestamptz default now()
);

create table public.habit_logs (
  id uuid primary key default gen_random_uuid(),
  habit_id uuid references habits(id) on delete cascade,
  user_id uuid references profiles(id) on delete cascade,
  log_date date not null,
  value_achieved float,
  is_completed boolean default false,
  logged_at timestamptz default now()
);

create table public.streaks (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references profiles(id) on delete cascade,
  habit_id uuid references habits(id),
  streak_type text,     -- 'logging', 'goal_hit', 'habit_specific'
  current_streak integer default 0,
  longest_streak integer default 0,
  last_activity_date date,
  updated_at timestamptz default now()
);
```

### 4.6 AI Conversations & Insights

```sql
create table public.ai_conversations (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references profiles(id) on delete cascade,
  session_id uuid default gen_random_uuid(),
  role text check (role in ('user', 'assistant')),
  content text not null,
  ai_provider text,     -- 'gemini' or 'groq'
  context_snapshot jsonb, -- user context at time of message
  tokens_used integer,
  created_at timestamptz default now()
);

create table public.ai_insights (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references profiles(id) on delete cascade,
  insight_type text,    -- 'weekly_summary', 'pattern_detected', 'goal_progress', 'suggestion'
  title text,
  content text,
  data jsonb,           -- structured data backing the insight
  is_read boolean default false,
  valid_until timestamptz,
  created_at timestamptz default now()
);

create table public.food_recommendations (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references profiles(id) on delete cascade,
  recommendation_type text, -- 'meal_swap', 'add_nutrient', 'avoid', 'best_time_to_eat'
  title text,
  description text,
  food_item_id uuid references food_items(id),
  reason text,
  priority integer default 5, -- 1 (high) to 10 (low)
  is_dismissed boolean default false,
  generated_at timestamptz default now()
);
```

### 4.7 Water & Supplements Tracking

```sql
create table public.water_logs (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references profiles(id) on delete cascade,
  log_date date not null,
  amount_ml integer not null,
  logged_at timestamptz default now()
);

create table public.supplement_logs (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references profiles(id) on delete cascade,
  supplement_name text,
  dose_amount float,
  dose_unit text,
  log_date date not null,
  taken_at timestamptz default now()
);
```

### 4.8 Supabase RLS Policies

```sql
-- Enable RLS on all tables
alter table profiles enable row level security;
alter table meal_logs enable row level security;
alter table meal_log_items enable row level security;
alter table habits enable row level security;
alter table habit_logs enable row level security;
alter table streaks enable row level security;
alter table ai_conversations enable row level security;

-- Example RLS policies (repeat for all tables)
create policy "Users can view own profile" on profiles
  for select using (auth.uid() = id);

create policy "Users can update own profile" on profiles
  for update using (auth.uid() = id);

create policy "Users can access own meal logs" on meal_logs
  for all using (auth.uid() = user_id);
```

---

## 5. FASTAPI PROJECT STRUCTURE

```
smarteat-backend/
├── app/
│   ├── main.py                    # FastAPI app entry, CORS, lifespan
│   ├── config.py                  # Settings, env vars (pydantic-settings)
│   ├── dependencies.py            # Auth middleware, DB client injection
│   │
│   ├── routers/
│   │   ├── auth.py                # Login, register, refresh token
│   │   ├── profile.py             # Profile CRUD, onboarding, TDEE calc
│   │   ├── food.py                # Search food, barcode lookup, cache
│   │   ├── meals.py               # Log meals, get history, daily summary
│   │   ├── meal_plans.py          # Generate/get/save meal plans
│   │   ├── habits.py              # Create/track habits, streaks
│   │   ├── water.py               # Water tracking
│   │   ├── ai_coach.py            # Chat endpoint (streaming), suggestions
│   │   ├── insights.py            # AI-generated insights, patterns
│   │   └── analytics.py           # Weekly/monthly nutrition reports
│   │
│   ├── services/
│   │   ├── ai/
│   │   │   ├── orchestrator.py    # Primary/fallback AI routing logic
│   │   │   ├── gemini_service.py  # Gemini Flash calls, streaming
│   │   │   ├── groq_service.py    # Groq LLaMA fallback
│   │   │   ├── prompt_builder.py  # Build context-aware prompts
│   │   │   └── response_parser.py # Parse/validate AI responses
│   │   │
│   │   ├── food/
│   │   │   ├── food_service.py    # Unified food search across APIs
│   │   │   ├── open_food_facts.py # Open Food Facts integration
│   │   │   ├── usda_service.py    # USDA FoodData API integration
│   │   │   ├── nutritionix.py     # Nutritionix natural language
│   │   │   └── nutrition_calc.py  # Macro/micro calculations
│   │   │
│   │   ├── meals/
│   │   │   ├── meal_service.py    # Meal CRUD + scoring
│   │   │   ├── meal_scorer.py     # AI meal quality scoring
│   │   │   └── meal_planner.py    # AI meal plan generation
│   │   │
│   │   ├── habits/
│   │   │   ├── habit_service.py   # Habit CRUD + completion logic
│   │   │   └── streak_engine.py   # Streak calculation + rewards
│   │   │
│   │   ├── analytics/
│   │   │   ├── report_service.py  # Aggregation queries
│   │   │   ├── pattern_detector.py # Detect eating patterns
│   │   │   └── insight_generator.py # Generate insights from data
│   │   │
│   │   └── external/
│   │       ├── weather_service.py # Open Meteo integration
│   │       ├── recipe_service.py  # TheMealDB + Spoonacular
│   │       └── exercise_service.py # Wger calorie burn data
│   │
│   ├── models/
│   │   ├── user.py
│   │   ├── food.py
│   │   ├── meal.py
│   │   ├── habit.py
│   │   └── ai.py
│   │
│   ├── schemas/                   # Pydantic request/response models
│   │   ├── auth.py
│   │   ├── profile.py
│   │   ├── food.py
│   │   ├── meal.py
│   │   ├── habit.py
│   │   └── ai.py
│   │
│   ├── core/
│   │   ├── supabase_client.py     # Supabase client singleton
│   │   ├── cache.py               # In-memory + Redis-lite caching
│   │   ├── exceptions.py          # Custom exception handlers
│   │   └── logging.py             # Structured logging setup
│   │
│   └── utils/
│       ├── tdee_calculator.py     # Mifflin-St Jeor TDEE formula
│       ├── nutrition_utils.py     # Helpers for nutrient math
│       └── date_utils.py          # Timezone-aware date helpers
│
├── tests/
│   ├── test_food.py
│   ├── test_meals.py
│   ├── test_ai.py
│   └── test_habits.py
│
├── requirements.txt
├── .env.example
├── Dockerfile
└── README.md
```

---

## 6. KEY API ENDPOINTS

### Authentication
```
POST   /auth/register              → Register with email/password
POST   /auth/login                 → Login, returns JWT
POST   /auth/logout                → Invalidate session
POST   /auth/refresh               → Refresh JWT token
POST   /auth/google                → OAuth via Supabase Google provider
```

### Profile & Onboarding
```
GET    /profile                    → Get user profile
PUT    /profile                    → Update profile
POST   /profile/onboarding         → Complete onboarding + calculate TDEE
GET    /profile/tdee               → Get calorie targets
PUT    /profile/goals              → Update dietary goals
```

### Food Search & Database
```
GET    /food/search?q={query}      → Unified search across all APIs
GET    /food/barcode/{barcode}     → Lookup by barcode (Open Food Facts)
GET    /food/nlp?q={natural_text}  → Natural language parsing via Nutritionix
GET    /food/{id}                  → Get cached food item details
POST   /food/custom                → Save custom food item
GET    /food/favorites             → User's favorite foods
GET    /food/history               → Recently logged foods
```

### Meal Logging
```
POST   /meals/log                  → Log a complete meal
GET    /meals/today                → Today's full meal log + totals
GET    /meals/date/{date}          → Meals on specific date
GET    /meals/history?days=7       → N-day meal history
GET    /meals/{id}                 → Single meal log detail
DELETE /meals/{id}                 → Delete meal log
POST   /meals/{id}/photo           → Upload meal photo to Supabase Storage
GET    /meals/daily-summary        → Calories + macros vs targets for today
```

### Meal Plans
```
POST   /meal-plans/generate        → AI generates weekly meal plan
GET    /meal-plans/active          → Get current active meal plan
GET    /meal-plans/{id}            → Get specific meal plan
POST   /meal-plans/{id}/activate   → Set plan as active
DELETE /meal-plans/{id}            → Delete meal plan
GET    /meal-plans/{id}/shopping   → Generate shopping list from plan
```

### Habits & Streaks
```
POST   /habits                     → Create a habit
GET    /habits                     → List all active habits
PUT    /habits/{id}                → Update habit settings
DELETE /habits/{id}                → Archive habit
POST   /habits/{id}/log            → Log habit completion for today
GET    /habits/{id}/streak         → Get streak data for habit
GET    /streaks/summary            → All streaks summary
GET    /habits/suggested           → AI-suggested habits based on logs
```

### Water Tracking
```
POST   /water/log                  → Log water intake (ml)
GET    /water/today                → Today's total intake vs target
GET    /water/history?days=7       → N-day water history
```

### AI Coach
```
POST   /ai/chat                    → Send message to AI coach (streaming)
GET    /ai/chat/history            → Previous conversations
POST   /ai/meal-score              → Score a meal or food item with AI
POST   /ai/food-swap               → Get healthier alternative to a food
GET    /ai/daily-tip               → Personalized daily tip
POST   /ai/analyze-day             → AI analysis of today's eating
```

### Insights & Analytics
```
GET    /insights                   → All unread AI insights
POST   /insights/{id}/read         → Mark insight as read
GET    /analytics/weekly           → Weekly nutrition report
GET    /analytics/trends           → 30-day macro trends
GET    /analytics/patterns         → Detected eating patterns
GET    /analytics/goal-progress    → Progress toward health goals
GET    /analytics/nutrient-gaps    → Chronically missing nutrients
```

---

## 7. AI ORCHESTRATION — GEMINI + GROQ FALLBACK

```python
# app/services/ai/orchestrator.py

import asyncio
from enum import Enum
from typing import AsyncGenerator

class AIProvider(str, Enum):
    GEMINI = "gemini"
    GROQ = "groq"

class AIOrchestrator:
    """Routes AI requests to Gemini first, falls back to Groq on failure."""

    def __init__(self, gemini: GeminiService, groq: GroqService):
        self.primary = gemini
        self.fallback = groq
        self.failure_threshold = 3       # Failures before circuit breaker trips
        self.failure_window_seconds = 60
        self._primary_failures = 0
        self._circuit_open_until = None

    async def chat(
        self, 
        messages: list[dict], 
        system_prompt: str,
        stream: bool = False
    ) -> str | AsyncGenerator:
        
        # Circuit breaker: skip primary if it keeps failing
        if self._is_circuit_open():
            return await self._call_fallback(messages, system_prompt, stream)

        try:
            result = await self._call_primary(messages, system_prompt, stream)
            self._reset_failures()
            return result

        except (GeminiRateLimitError, GeminiServiceError) as e:
            self._record_failure()
            # Seamlessly fall through to Groq
            return await self._call_fallback(messages, system_prompt, stream)

    async def generate_meal_plan(self, user_context: dict) -> dict:
        """Specialized method for structured meal plan generation."""
        prompt = PromptBuilder.meal_plan_prompt(user_context)
        try:
            return await self.primary.generate_json(prompt)
        except Exception:
            return await self.fallback.generate_json(prompt)

    def _is_circuit_open(self) -> bool:
        if self._circuit_open_until and datetime.now() < self._circuit_open_until:
            return True
        return False

    def _record_failure(self):
        self._primary_failures += 1
        if self._primary_failures >= self.failure_threshold:
            # Open circuit for 2 minutes
            self._circuit_open_until = datetime.now() + timedelta(minutes=2)

    def _reset_failures(self):
        self._primary_failures = 0
        self._circuit_open_until = None
```

---

## 8. CONTEXT-AWARE PROMPT BUILDING

```python
# app/services/ai/prompt_builder.py

class PromptBuilder:
    
    SYSTEM_PROMPT = """You are SmartEat, an expert nutritionist and behavioral coach.
You help users make better food choices by combining nutritional science with 
behavioral psychology. Always be encouraging, evidence-based, and practical.
Keep responses concise unless asked for detail."""

    @staticmethod
    def build_user_context(profile: dict, recent_meals: list, 
                           today_summary: dict, weather: dict = None) -> str:
        """Build rich context string to inject into AI prompts."""
        return f"""
USER PROFILE:
- Age: {profile['age']}, Gender: {profile['gender']}
- Weight: {profile['weight_kg']}kg, Height: {profile['height_cm']}cm
- Activity Level: {profile['activity_level']}
- Health Goals: {', '.join(profile['health_goals'])}
- Dietary Restrictions: {', '.join(profile['dietary_restrictions'])}
- Daily Calorie Target: {profile['daily_calorie_target']} kcal

TODAY SO FAR ({datetime.now().strftime('%A %I:%M %p')}):
- Calories consumed: {today_summary['calories']} / {profile['daily_calorie_target']}
- Protein: {today_summary['protein_g']}g / {profile['daily_protein_target_g']}g
- Carbs: {today_summary['carbs_g']}g, Fat: {today_summary['fat_g']}g
- Water: {today_summary['water_ml']}ml

RECENT EATING PATTERNS (last 7 days):
{PromptBuilder._format_patterns(recent_meals)}

{f"WEATHER: {weather['condition']}, {weather['temp_c']}°C — factor this in for food suggestions." if weather else ""}
"""

    @staticmethod
    def meal_score_prompt(food_items: list, user_profile: dict) -> str:
        return f"""
Score this meal out of 100 for this user and explain in 2-3 sentences.
Focus on: goal alignment, macros balance, micronutrient density, and processing level.
Return JSON: {{"score": int, "grade": "A/B/C/D/F", "feedback": str, "suggestions": [str]}}

User Goals: {user_profile['health_goals']}
Daily Calorie Target: {user_profile['daily_calorie_target']}
Meal: {json.dumps(food_items)}
"""

    @staticmethod 
    def meal_plan_prompt(user_context: dict) -> str:
        return f"""
Generate a 7-day meal plan as structured JSON.
Each day should have breakfast, lunch, dinner, and 1-2 snacks.
Must respect dietary restrictions, hit calorie targets (±10%), and vary daily.

Return ONLY valid JSON matching this schema:
{{
  "days": [{{
    "day": "Monday",
    "meals": [{{
      "meal_type": "breakfast",
      "name": str,
      "description": str,
      "calories": int,
      "protein_g": float,
      "carbs_g": float,
      "fat_g": float,
      "ingredients": [{{"name": str, "quantity": str}}],
      "prep_minutes": int
    }}]
  }}]
}}

{user_context}
"""
```

---

## 9. FOOD SEARCH SERVICE (Multi-API Cascade)

```python
# app/services/food/food_service.py

class FoodSearchService:
    """
    Search cascade:
    1. Check Supabase cache (food_items table)
    2. Try Open Food Facts (best for packaged goods)
    3. Try USDA FoodData (best for whole foods)
    4. Try Nutritionix (best for restaurant/natural language)
    """

    async def search(self, query: str, limit: int = 10) -> list[FoodItem]:
        # 1. Check local cache first
        cached = await self._search_cache(query, limit)
        if len(cached) >= limit:
            return cached

        # 2. Fan out to external APIs concurrently
        results = await asyncio.gather(
            self._search_open_food_facts(query),
            self._search_usda(query),
            self._search_nutritionix(query),
            return_exceptions=True
        )

        # 3. Deduplicate, rank, and cache results
        merged = self._merge_and_dedupe(results)
        await self._cache_results(merged)
        return merged[:limit]

    async def lookup_barcode(self, barcode: str) -> FoodItem | None:
        # Check cache
        cached = await self._get_cached_barcode(barcode)
        if cached:
            return cached
        
        # Open Food Facts is best for barcodes
        item = await self._fetch_open_food_facts_barcode(barcode)
        if item:
            await self._cache_food_item(item)
        return item

    async def natural_language_parse(self, text: str) -> list[FoodItem]:
        """Parse '2 boiled eggs and a banana' into structured food items."""
        # Nutritionix excels at this
        return await self._nutritionix_nlp(text)
```

---

## 10. HABIT ENGINE & STREAK LOGIC

```python
# app/services/habits/streak_engine.py

class StreakEngine:
    
    async def update_streak(self, user_id: str, habit_id: str) -> StreakResult:
        streak = await self.db.get_streak(user_id, habit_id)
        today = date.today()
        yesterday = today - timedelta(days=1)
        
        if streak.last_activity_date == today:
            return streak  # Already logged today
        
        if streak.last_activity_date == yesterday:
            # Continue streak
            streak.current_streak += 1
        else:
            # Streak broken — reset
            streak.current_streak = 1
        
        streak.longest_streak = max(streak.current_streak, streak.longest_streak)
        streak.last_activity_date = today
        
        await self.db.save_streak(streak)
        
        # Check for milestone achievements
        await self._check_milestones(streak)
        return streak

    async def _check_milestones(self, streak: Streak):
        milestones = [7, 14, 21, 30, 60, 90, 180, 365]
        if streak.current_streak in milestones:
            await self.notification_service.send(
                user_id=streak.user_id,
                title=f"🔥 {streak.current_streak}-Day Streak!",
                body=f"You've maintained this habit for {streak.current_streak} days!"
            )
```

---

## 11. NUTRITION PATTERN DETECTOR

```python
# app/services/analytics/pattern_detector.py

class PatternDetector:
    """
    Analyzes meal logs to surface actionable behavioral patterns.
    Patterns detected:
    - Consistent meal skipping (e.g., always skip breakfast)
    - Late-night eating (meals after 9pm)
    - Protein deficit days
    - Emotional eating correlation (mood vs meal quality)
    - Weekend vs weekday eating differences
    - Nutrient gaps (chronically low vitamins/minerals)
    """

    async def detect_all(self, user_id: str, days: int = 30) -> list[Pattern]:
        logs = await self.db.get_meal_logs(user_id, days=days)
        
        patterns = await asyncio.gather(
            self._detect_meal_skipping(logs),
            self._detect_late_night_eating(logs),
            self._detect_protein_deficits(logs),
            self._detect_mood_correlations(logs),
            self._detect_weekend_differences(logs),
            self._detect_nutrient_gaps(logs),
        )
        
        # Filter to significant patterns only
        significant = [p for p in patterns if p and p.confidence >= 0.7]
        
        # Convert to AI insights
        for pattern in significant:
            await self.insight_generator.create_insight(user_id, pattern)
        
        return significant

    async def _detect_protein_deficits(self, logs: list) -> Pattern | None:
        target = logs[0].user_profile.daily_protein_target_g
        deficit_days = [l for l in logs if l.total_protein_g < target * 0.8]
        
        if len(deficit_days) / len(logs) > 0.6:  # >60% of days under target
            return Pattern(
                type="protein_deficit",
                confidence=len(deficit_days) / len(logs),
                message=f"You're under your protein target on {len(deficit_days)} of the last {len(logs)} days.",
                suggestion="Try adding a protein-rich snack like Greek yogurt or boiled eggs."
            )
```

---

## 12. CACHING STRATEGY

```python
# app/core/cache.py
# Using in-memory cache (no Redis required, no credit card)

from cachetools import TTLCache
import asyncio

class CacheManager:
    def __init__(self):
        # Food search cache — 24h TTL, max 5000 items
        self.food_cache = TTLCache(maxsize=5000, ttl=86400)
        
        # AI response cache — 1h TTL (for identical prompts)
        self.ai_cache = TTLCache(maxsize=1000, ttl=3600)
        
        # External API cache — 6h TTL (weather, exercise data)
        self.external_cache = TTLCache(maxsize=500, ttl=21600)

    def get_food(self, key: str) -> dict | None:
        return self.food_cache.get(key)
    
    def set_food(self, key: str, value: dict):
        self.food_cache[key] = value

# Supabase food_items table acts as persistent L2 cache
# In-memory TTLCache is L1 (faster, no DB round-trip)
```

---

## 13. CORE BUSINESS LOGIC — TDEE CALCULATOR

```python
# app/utils/tdee_calculator.py

class TDEECalculator:
    
    ACTIVITY_MULTIPLIERS = {
        "sedentary": 1.2,
        "light": 1.375,
        "moderate": 1.55,
        "active": 1.725,
        "very_active": 1.9
    }
    
    GOAL_ADJUSTMENTS = {
        "weight_loss": -500,       # 500 kcal deficit = ~0.5kg/week loss
        "aggressive_loss": -750,
        "maintenance": 0,
        "muscle_gain": +300,       # Lean bulk surplus
        "weight_gain": +500
    }

    @classmethod
    def calculate(cls, profile: UserProfile) -> TDEEResult:
        # Mifflin-St Jeor BMR
        if profile.gender == "male":
            bmr = (10 * profile.weight_kg) + (6.25 * profile.height_cm) - (5 * profile.age) + 5
        else:
            bmr = (10 * profile.weight_kg) + (6.25 * profile.height_cm) - (5 * profile.age) - 161
        
        tdee = bmr * cls.ACTIVITY_MULTIPLIERS[profile.activity_level]
        
        primary_goal = profile.health_goals[0] if profile.health_goals else "maintenance"
        adjustment = cls.GOAL_ADJUSTMENTS.get(primary_goal, 0)
        goal_calories = max(1200, tdee + adjustment)  # Never below 1200
        
        # Macro split (defaults, adjustable)
        protein_g = profile.weight_kg * 1.6   # 1.6g/kg for active individuals
        fat_g = goal_calories * 0.25 / 9      # 25% calories from fat
        carb_g = (goal_calories - (protein_g * 4) - (fat_g * 9)) / 4
        
        return TDEEResult(
            bmr=round(bmr),
            tdee=round(tdee),
            goal_calories=round(goal_calories),
            protein_g=round(protein_g),
            carbs_g=round(carb_g),
            fat_g=round(fat_g)
        )
```

---

## 14. ENVIRONMENT CONFIGURATION

```env
# .env.example

# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# AI Providers (free tiers)
GEMINI_API_KEY=your-gemini-api-key          # Google AI Studio — free
GROQ_API_KEY=your-groq-api-key              # Groq console — free

# AI Models
GEMINI_MODEL=gemini-1.5-flash               # Fast, free-tier friendly
GROQ_MODEL=llama-3.1-8b-instant            # Fast fallback

# Food APIs (all free, no credit card)
USDA_API_KEY=your-usda-key                  # api.nal.usda.gov — instant free key
NUTRITIONIX_APP_ID=your-app-id             # Free dev account
NUTRITIONIX_APP_KEY=your-app-key
EDAMAM_APP_ID=your-app-id                  # Free tier, 1000 req/month
EDAMAM_APP_KEY=your-app-key
SPOONACULAR_API_KEY=your-key               # 150 req/day free

# Open APIs (no key needed)
OPEN_FOOD_FACTS_BASE=https://world.openfoodfacts.org
THEMEALDB_BASE=https://www.themealdb.com/api/json/v1/1
OPEN_METEO_BASE=https://api.open-meteo.com/v1
WGER_BASE=https://wger.de/api/v2

# App Config
APP_NAME=SmartEat
DEBUG=false
SECRET_KEY=your-secret-key-here
ALLOWED_ORIGINS=https://your-frontend.com
```

---

## 15. DEPENDENCIES (requirements.txt)

```txt
# Core
fastapi==0.115.0
uvicorn[standard]==0.32.0
python-dotenv==1.0.1
pydantic-settings==2.6.0
pydantic[email]==2.9.0

# Supabase
supabase==2.9.1
postgrest==0.17.0

# AI SDKs
google-generativeai==0.8.3
groq==0.11.0

# HTTP Client
httpx==0.27.2
aiohttp==3.10.10
tenacity==9.0.0      # Retry logic for API calls

# Caching
cachetools==5.5.0

# Auth / Security
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.12

# Data Processing
pandas==2.2.3        # Analytics / pattern detection
numpy==2.1.3

# Utilities
python-dateutil==2.9.0
pytz==2024.2
Pillow==11.0.0       # Image processing for meal photos

# Testing
pytest==8.3.3
pytest-asyncio==0.24.0
httpx==0.27.2        # For test client
```

---

## 16. STREAMING AI CHAT ENDPOINT

```python
# app/routers/ai_coach.py

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
import json

router = APIRouter(prefix="/ai", tags=["AI Coach"])

@router.post("/chat")
async def chat_with_coach(
    request: ChatRequest,
    user = Depends(get_current_user),
    ai: AIOrchestrator = Depends(get_ai_orchestrator),
    db: SupabaseClient = Depends(get_db)
):
    # Build personalized context
    profile = await db.get_profile(user.id)
    today_summary = await db.get_today_summary(user.id)
    recent_meals = await db.get_recent_meals(user.id, days=7)
    
    system_prompt = PromptBuilder.SYSTEM_PROMPT
    context = PromptBuilder.build_user_context(profile, recent_meals, today_summary)
    
    # Get conversation history for this session
    history = await db.get_conversation_history(user.id, request.session_id)
    
    messages = [
        *history,
        {"role": "user", "content": f"{context}\n\nUser message: {request.message}"}
    ]

    async def generate():
        full_response = ""
        async for chunk in ai.chat(messages, system_prompt, stream=True):
            full_response += chunk
            yield f"data: {json.dumps({'chunk': chunk})}\n\n"
        
        # Save conversation to DB
        await db.save_message(user.id, request.session_id, "user", request.message)
        await db.save_message(user.id, request.session_id, "assistant", full_response)
        yield f"data: {json.dumps({'done': True})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")
```

---

## 17. DEVELOPMENT PHASES

### Phase 1 — Foundation (Weeks 1-2)
- [ ] Supabase project setup, schema migration, RLS policies
- [ ] FastAPI project scaffolding, folder structure
- [ ] Supabase Auth integration (JWT middleware)
- [ ] Profile CRUD + onboarding flow + TDEE calculator
- [ ] Basic food search (Open Food Facts + USDA)
- [ ] Meal logging CRUD endpoints

### Phase 2 — Core Intelligence (Weeks 3-4)
- [ ] Gemini + Groq AI orchestrator with circuit breaker
- [ ] Streaming AI chat endpoint
- [ ] Context-aware prompt builder
- [ ] Meal scoring endpoint
- [ ] Barcode lookup via Open Food Facts
- [ ] Nutritionix natural language parsing

### Phase 3 — Habits & Engagement (Week 5)
- [ ] Habit creation and logging
- [ ] Streak engine with milestone detection
- [ ] Water tracking
- [ ] Daily summary and progress endpoints

### Phase 4 — Plans & Analytics (Week 6)
- [ ] AI-generated meal plan endpoint
- [ ] TheMealDB + Spoonacular recipe integration
- [ ] Weekly analytics aggregations
- [ ] Pattern detection engine
- [ ] AI insight generator

### Phase 5 — Polish & Optimization (Week 7)
- [ ] Multi-layer caching (L1 in-memory + L2 Supabase)
- [ ] Rate limiting (per-user API quotas)
- [ ] Structured logging and error tracking
- [ ] Comprehensive test suite
- [ ] API documentation (auto-generated by FastAPI)
- [ ] Dockerfile + deployment config

---

## 18. SECURITY CHECKLIST

- [x] All tables protected by Supabase Row Level Security (RLS)
- [x] JWT validation on every protected endpoint
- [x] API keys stored in environment variables only
- [x] Input validation via Pydantic schemas on all endpoints
- [x] Rate limiting per user (prevent AI API abuse)
- [x] Meal photo uploads validated (type + size limits)
- [x] SQL injection prevention (Supabase PostgREST parameterized queries)
- [x] CORS configured for specific frontend origins only

---

## 19. MONITORING & OBSERVABILITY

```python
# Key metrics to track:

# AI Usage
- Gemini API calls per day (stay within free limits)
- Groq fallback activation rate
- Average AI response latency

# API Health  
- External API failure rates (Open Food Facts, USDA, Nutritionix)
- Cache hit rate (target >70% for food searches)
- Endpoint P95 latency

# Business Metrics
- Daily Active Users logging meals
- Meal plan generation count
- Habit streak retention rates
- Average meals logged per user per day
```

---

*Generated for ClairEat Backend v1.0 — FastAPI + Supabase + Gemini/Groq Architecture*
