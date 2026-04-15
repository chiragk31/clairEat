# 🥗 clairEat — Backend Architecture & API Specification

> **Stack:** FastAPI + Supabase (Postgres + Auth + Storage + Realtime)
> **AI:** Google Gemini Flash (primary) + Groq LLaMA 3.1 (circuit-breaker fallback)
> **Version:** 1.0 — Production Ready Blueprint

---

## 1. 🧠 System Overview

### What the Backend Does
clairEat's backend is a modular SaaS API that powers a contextually intelligent nutrition platform. It handles:

- **Identity & Onboarding** — Supabase Auth with JWT; profile creation and TDEE calculation
- **Food Intelligence** — Multi-source food search, barcode lookup, NLP-based intake parsing
- **Meal Logging** — CRUD for daily meal entries, macro aggregation, real-time progress
- **Meal Plan Generation** — AI-generated 7-day meal plans customised to user profile
- **AI Conversational Coach** — Streaming chat endpoint with rich user-context injection
- **Habit & Streak Engine** — Habit definition, daily logging, streak calculation and milestone rewards
- **Analytics & Insights** — Aggregated weekly/monthly trends, pattern detection, AI-generated insights
- **Wellness Summaries** — Contextual health tips derived from logged data and external signals

### Core Responsibilities

| Responsibility | Owner |
|---|---|
| Authentication & sessions | Supabase Auth + JWT middleware |
| Business logic & orchestration | FastAPI service layer |
| Persistent data store | Supabase Postgres (with RLS) |
| File storage (meal photos) | Supabase Storage |
| AI reasoning & chat | Gemini Flash / Groq LLaMA |
| Food nutrition data | Open Food Facts, USDA, Nutritionix, Edamam |
| Recipe data | TheMealDB, Spoonacular |
| Contextual signals | Open Meteo (weather), IPinfo (locale) |

### High-Level Architecture

```
+-------------------------------------------------------------------+
|                     Client (Next.js / Mobile)                     |
+------------------------------+------------------------------------+
                               | HTTPS / SSE (streaming)
+------------------------------v------------------------------------+
|                         FastAPI Backend                           |
|                                                                   |
|  +-------------+  +-------------+  +--------------------------+  |
|  | Auth Router |  | Food Router |  |   AI Coach Router        |  |
|  +-------------+  +-------------+  +--------------------------+  |
|  | Meal Router |  | Habit Router|  |   Analytics Router       |  |
|  +-------------+  +-------------+  +--------------------------+  |
|  | Profile Rtr |  | Water Router|  |   Insights Router        |  |
|  +-------------+  +-------------+  +--------------------------+  |
|                                                                   |
|  +-----------------------------------------------------------+   |
|  |              Service Layer  (Business Logic)              |   |
|  |  AI Orchestrator | Habit Engine | Nutrition Calculator    |   |
|  |  Food Aggregator | Pattern Detector | Insight Generator   |   |
|  +-----------------------------------------------------------+   |
+--------+--------------+-------------+--------------+------------+
         |              |             |              |
+--------v------+ +-----v------+ +---v------+ +----v-----------+
|   Supabase    | | Gemini AI  | | Groq AI  | | External APIs  |
| (Postgres +   | |  (Primary) | |(Fallback)| | Food / Recipe  |
|  Storage +    | +------------+ +----------+ | Weather / Exer |
|  Realtime +   |                             +----------------+
|  Auth)        |
+---------------+
```

---

## 2. 🧩 Core Feature Mapping (Frontend Routes → Backend)

| Frontend Route | Backend Responsibilities |
|---|---|
| `/onboarding` | `POST /profile/onboarding` — save profile, compute TDEE & macro targets, set goals/diet prefs |
| `/` (Dashboard) | `GET /meals/today`, `GET /meals/daily-summary`, `GET /water/today`, `GET /streaks/summary`, `GET /insights` |
| `/log-meal` | `GET /food/search`, `GET /food/barcode/:id`, `POST /meals/log`, `POST /meals/:id/photo`, `GET /meals/today` |
| `/meal-plan` | `POST /meal-plans/generate`, `GET /meal-plans/active`, `GET /meal-plans/:id`, `GET /meal-plans/:id/shopping` |
| `/ai-coach` | `POST /ai/chat` (streaming SSE), `GET /ai/chat/history`, `GET /ai/daily-tip` |
| `/analytics` | `GET /analytics/weekly`, `GET /analytics/trends`, `GET /analytics/patterns`, `GET /analytics/goal-progress` |
| `/wellness` | `GET /insights`, `GET /analytics/nutrient-gaps`, `GET /habits/suggested`, `GET /ai/daily-tip` |

---

## 3. 🗄️ Database Design

All tables live in Supabase Postgres. Row Level Security (RLS) is enabled on every table.

---

### `profiles` — extends Supabase Auth users

| Field | Type | Notes |
|---|---|---|
| `id` | `uuid PK` | References `auth.users(id)` |
| `username` | `text UNIQUE` | Optional display handle |
| `full_name` | `text` | |
| `age` | `integer` | |
| `gender` | `text` | `male / female / other / prefer_not_to_say` |
| `height_cm` | `float` | |
| `weight_kg` | `float` | |
| `target_weight_kg` | `float` | |
| `activity_level` | `text` | `sedentary / light / moderate / active / very_active` |
| `health_goals` | `text[]` | `['weight_loss','muscle_gain','maintenance','diabetes_control']` |
| `dietary_restrictions` | `text[]` | `['vegetarian','vegan','gluten_free','lactose_free']` |
| `allergies` | `text[]` | Free-text list |
| `daily_calorie_target` | `integer` | Computed on onboarding |
| `daily_protein_target_g` | `float` | |
| `daily_carb_target_g` | `float` | |
| `daily_fat_target_g` | `float` | |
| `timezone` | `text` | Default `UTC` |
| `location_city` | `text` | For contextual tips |
| `onboarding_complete` | `boolean` | Default `false` |
| `created_at` | `timestamptz` | |
| `updated_at` | `timestamptz` | |

---

### `food_items` — cached nutrition data from external APIs

| Field | Type | Notes |
|---|---|---|
| `id` | `uuid PK` | |
| `external_id` | `text` | Source API's id |
| `source` | `text` | `open_food_facts / usda / nutritionix / edamam` |
| `name` | `text NOT NULL` | Full-text indexed |
| `brand` | `text` | |
| `barcode` | `text UNIQUE` | EAN/UPC |
| `serving_size_g` | `float` | |
| `calories_per_100g` | `float` | |
| `protein_per_100g` | `float` | |
| `carbs_per_100g` | `float` | |
| `fat_per_100g` | `float` | |
| `fiber_per_100g` | `float` | |
| `sugar_per_100g` | `float` | |
| `sodium_per_100g` | `float` | |
| `vitamins` | `jsonb` | `{"vitamin_c": 10.5, "vitamin_d": 2.1}` |
| `minerals` | `jsonb` | `{"iron": 1.2, "calcium": 120}` |
| `nutriscore` | `text` | A–E European score |
| `nova_group` | `integer` | 1–4 processing level |
| `allergens` | `text[]` | |
| `image_url` | `text` | |
| `created_at` | `timestamptz` | |

**Indexes:** `barcode` (btree), `name` (GIN full-text)

---

### `meal_logs` — one row per eating event

| Field | Type | Notes |
|---|---|---|
| `id` | `uuid PK` | |
| `user_id` | `uuid FK → profiles` | |
| `meal_date` | `date NOT NULL` | For daily grouping |
| `meal_type` | `enum` | `breakfast / lunch / dinner / snack / pre_workout / post_workout` |
| `total_calories` | `float` | Computed from items |
| `total_protein_g` | `float` | |
| `total_carbs_g` | `float` | |
| `total_fat_g` | `float` | |
| `total_fiber_g` | `float` | |
| `mood_before` | `text` | `happy / stressed / tired / neutral` |
| `hunger_level_before` | `integer` | 1–10 |
| `fullness_level_after` | `integer` | 1–10 |
| `notes` | `text` | Mindful eating notes |
| `ai_meal_score` | `float` | AI quality score 0–100 |
| `ai_feedback` | `text` | AI-generated feedback |
| `image_url` | `text` | Supabase Storage path |
| `logged_at` | `timestamptz` | |

**Index:** `(user_id, meal_date)` composite

---

### `meal_log_items` — individual foods within a meal log

| Field | Type | Notes |
|---|---|---|
| `id` | `uuid PK` | |
| `meal_log_id` | `uuid FK → meal_logs` | Cascade delete |
| `food_item_id` | `uuid FK → food_items` | Nullable if custom |
| `custom_food_name` | `text` | If food not in DB |
| `quantity_g` | `float NOT NULL` | |
| `calories` | `float NOT NULL` | |
| `protein_g` | `float` | |
| `carbs_g` | `float` | |
| `fat_g` | `float` | |
| `fiber_g` | `float` | |

---

### `meal_plans` — AI-generated weekly plans

| Field | Type | Notes |
|---|---|---|
| `id` | `uuid PK` | |
| `user_id` | `uuid FK → profiles` | |
| `plan_name` | `text` | e.g. "Week of April 14" |
| `start_date` | `date` | |
| `end_date` | `date` | |
| `is_active` | `boolean` | Only one active at a time |
| `target_calories` | `integer` | |
| `generated_by` | `text` | `gemini / groq` |
| `generation_context` | `jsonb` | User context snapshot at generation time |
| `created_at` | `timestamptz` | |

---

### `meal_plan_entries` — one meal per row per day

| Field | Type | Notes |
|---|---|---|
| `id` | `uuid PK` | |
| `meal_plan_id` | `uuid FK → meal_plans` | Cascade delete |
| `day_of_week` | `integer` | 1=Mon … 7=Sun |
| `meal_type` | `enum` | Same as `meal_logs` |
| `recipe_name` | `text` | |
| `recipe_description` | `text` | |
| `estimated_calories` | `integer` | |
| `estimated_protein_g` | `float` | |
| `estimated_carbs_g` | `float` | |
| `estimated_fat_g` | `float` | |
| `ingredients` | `jsonb` | `[{"name":"chicken","quantity":"150g"}]` |
| `preparation_steps` | `text[]` | |
| `prep_time_minutes` | `integer` | |
| `external_recipe_id` | `text` | TheMealDB / Spoonacular ref |

---

### `habits` — user-defined repeatable targets

| Field | Type | Notes |
|---|---|---|
| `id` | `uuid PK` | |
| `user_id` | `uuid FK → profiles` | |
| `habit_name` | `text NOT NULL` | |
| `habit_type` | `text` | `water_intake / meal_timing / vegetable_serving / sugar_limit / custom` |
| `target_value` | `float` | |
| `target_unit` | `text` | `glasses / grams / servings / times` |
| `frequency` | `text` | `daily / weekly` |
| `reminder_times` | `time[]` | |
| `is_active` | `boolean` | |

---

### `habit_logs` — daily completion records

| Field | Type | Notes |
|---|---|---|
| `id` | `uuid PK` | |
| `habit_id` | `uuid FK → habits` | |
| `user_id` | `uuid FK → profiles` | |
| `log_date` | `date NOT NULL` | |
| `value_achieved` | `float` | Actual value logged |
| `is_completed` | `boolean` | Whether target was hit |

---

### `streaks` — rolling streak counters

| Field | Type | Notes |
|---|---|---|
| `id` | `uuid PK` | |
| `user_id` | `uuid FK → profiles` | |
| `habit_id` | `uuid FK → habits` | Nullable = global logging streak |
| `streak_type` | `text` | `logging / goal_hit / habit_specific` |
| `current_streak` | `integer` | |
| `longest_streak` | `integer` | |
| `last_activity_date` | `date` | |

---

### `ai_conversations` — full chat history

| Field | Type | Notes |
|---|---|---|
| `id` | `uuid PK` | |
| `user_id` | `uuid FK → profiles` | |
| `session_id` | `uuid` | Groups messages into a thread |
| `role` | `text` | `user / assistant` |
| `content` | `text NOT NULL` | |
| `ai_provider` | `text` | `gemini / groq` |
| `context_snapshot` | `jsonb` | User data at message time |
| `tokens_used` | `integer` | |
| `created_at` | `timestamptz` | |

---

### `ai_insights` — AI-generated tips and notifications

| Field | Type | Notes |
|---|---|---|
| `id` | `uuid PK` | |
| `user_id` | `uuid FK → profiles` | |
| `insight_type` | `text` | `weekly_summary / pattern_detected / goal_progress / suggestion` |
| `title` | `text` | |
| `content` | `text` | |
| `data` | `jsonb` | Backing data (numbers, charts) |
| `is_read` | `boolean` | |
| `valid_until` | `timestamptz` | Auto-expire stale insights |
| `created_at` | `timestamptz` | |

---

### `water_logs`

| Field | Type | Notes |
|---|---|---|
| `id` | `uuid PK` | |
| `user_id` | `uuid FK → profiles` | |
| `log_date` | `date NOT NULL` | |
| `amount_ml` | `integer NOT NULL` | |
| `logged_at` | `timestamptz` | |

---

### `tdee_calculations`

| Field | Type | Notes |
|---|---|---|
| `id` | `uuid PK` | |
| `user_id` | `uuid FK → profiles` | |
| `bmr` | `float` | Basal Metabolic Rate |
| `tdee` | `float` | Total Daily Energy Expenditure |
| `goal_calories` | `float` | Adjusted for goal |
| `formula_used` | `text` | `mifflin_st_jeor` |
| `calculated_at` | `timestamptz` | |

---

### Entity Relationships

```
profiles
  +-- meal_logs ----------> meal_log_items -----> food_items
  +-- meal_plans ---------> meal_plan_entries
  +-- habits -------------> habit_logs
  +-- streaks
  +-- water_logs
  +-- ai_conversations
  +-- ai_insights
  +-- tdee_calculations
```

---

## 4. 🔌 API Design

**Base URL:** `https://api.claireat.com/v1`
**Auth:** All protected endpoints require `Authorization: Bearer <jwt>`

---

### Auth APIs

#### `POST /auth/register`
**Purpose:** Register new user with email + password.

**Request:**
```json
{ "email": "chirag@example.com", "password": "SecurePass123!", "full_name": "Chirag" }
```
**Response `201`:**
```json
{ "user_id": "uuid", "access_token": "eyJ...", "refresh_token": "eyJ..." }
```

---

#### `POST /auth/login`
**Purpose:** Authenticate and receive JWT tokens.

**Request:** `{ "email": "...", "password": "..." }`
**Response `200`:** `{ "access_token": "eyJ...", "refresh_token": "eyJ...", "expires_in": 3600 }`

---

#### `POST /auth/refresh`
**Purpose:** Refresh expired access token.

**Request:** `{ "refresh_token": "eyJ..." }`
**Response `200`:** `{ "access_token": "eyJ...", "expires_in": 3600 }`

---

#### `POST /auth/logout`
**Purpose:** Invalidate current session.
**Response `204`:** No content.

---

#### `POST /auth/google`
**Purpose:** OAuth via Supabase Google provider.
**Response `200`:** `{ "redirect_url": "https://..." }` or `{ "access_token": "..." }`

---

### Profile & Onboarding APIs

#### `POST /profile/onboarding`
**Purpose:** Complete onboarding — save profile and auto-compute TDEE + macro targets.

**Request:**
```json
{
  "full_name": "Chirag",
  "age": 26,
  "gender": "male",
  "height_cm": 175,
  "weight_kg": 72,
  "target_weight_kg": 78,
  "activity_level": "moderate",
  "health_goals": ["muscle_gain"],
  "dietary_restrictions": ["gluten_free"],
  "allergies": ["peanuts"]
}
```
**Response `201`:**
```json
{
  "profile": { "...": "..." },
  "tdee": {
    "bmr": 1780,
    "tdee": 2759,
    "goal_calories": 3059,
    "protein_g": 115,
    "carbs_g": 344,
    "fat_g": 85
  }
}
```

---

#### `GET /profile`
**Purpose:** Fetch current user's full profile.
**Response `200`:** Full profile object with computed macro targets.

---

#### `PUT /profile`
**Purpose:** Update any profile fields (partial update supported).
**Request:** Any subset of profile fields.
**Response `200`:** Updated profile object.

---

#### `GET /profile/tdee`
**Purpose:** Get latest TDEE calculation.
**Response `200`:** `{ "bmr": 1780, "tdee": 2759, "goal_calories": 3059, ... }`

---

### Food Search APIs

#### `GET /food/search?q={query}&limit=10`
**Purpose:** Unified food search — hits cache first, then external APIs in parallel.

**Response `200`:**
```json
{
  "results": [
    {
      "id": "uuid",
      "name": "Avocado",
      "calories_per_100g": 160,
      "protein_per_100g": 2,
      "carbs_per_100g": 9,
      "fat_per_100g": 15,
      "nutriscore": "A",
      "source": "usda"
    }
  ],
  "total": 8
}
```

---

#### `GET /food/barcode/{barcode}`
**Purpose:** Look up packaged food by EAN/UPC barcode (Open Food Facts priority).
**Response `200`:** Single food item or `404`.

---

#### `GET /food/nlp?q={natural_text}`
**Purpose:** Parse natural language like "2 boiled eggs and a banana" into food items.

**Response `200`:**
```json
{
  "parsed_items": [
    { "name": "Boiled Egg", "quantity_g": 100, "calories": 155 },
    { "name": "Banana", "quantity_g": 120, "calories": 107 }
  ]
}
```

---

#### `GET /food/{id}` — Full food detail including vitamins + minerals.
#### `POST /food/custom` — Save a custom food item.
#### `GET /food/favorites` — User's bookmarked foods by frequency.
#### `GET /food/history` — Recently logged foods (last 30 days, de-duped).

---

### Meal Logging APIs

#### `POST /meals/log`
**Purpose:** Log a complete meal with one or more food items.

**Request:**
```json
{
  "meal_date": "2026-04-15",
  "meal_type": "breakfast",
  "items": [
    { "food_item_id": "uuid", "quantity_g": 200 },
    { "custom_food_name": "Homemade Granola", "quantity_g": 50, "calories": 230, "protein_g": 5, "carbs_g": 34, "fat_g": 9 }
  ],
  "mood_before": "happy",
  "hunger_level_before": 7,
  "notes": "Ate slowly"
}
```
**Response `201`:**
```json
{
  "meal_log_id": "uuid",
  "total_calories": 430,
  "total_protein_g": 18,
  "ai_meal_score": 84,
  "ai_feedback": "Great protein ratio. Consider adding berries for fiber."
}
```

---

#### `GET /meals/today`
**Purpose:** All meals logged for today.
**Response `200`:** `{ "date": "...", "meals": [{ "meal_type": "breakfast", "total_calories": 430, "items": [...] }] }`

---

#### `GET /meals/daily-summary`
**Purpose:** Aggregated macro totals vs daily targets.

**Response `200`:**
```json
{
  "totals": { "calories": 1240, "protein_g": 62, "carbs_g": 145, "fat_g": 38 },
  "targets": { "calories": 2300, "protein_g": 115, "carbs_g": 259, "fat_g": 64 },
  "pct_complete": { "calories": 54, "protein": 54 },
  "water_ml": 1500,
  "water_target_ml": 2500
}
```

---

#### `GET /meals/date/{date}` — Meals on a specific date (YYYY-MM-DD).
#### `GET /meals/history?days=7` — N-day meal history grouped by date.
#### `GET /meals/{id}` — Single meal detail with all items and AI feedback.
#### `DELETE /meals/{id}` — Remove a logged meal (`204`).
#### `POST /meals/{id}/photo` — Upload meal photo (`multipart/form-data`, max 5MB).

---

### Meal Plan APIs

#### `POST /meal-plans/generate`
**Purpose:** Trigger AI (Gemini) to generate a 7-day personalised meal plan.

**Request:**
```json
{
  "start_date": "2026-04-21",
  "preferences": {
    "exclude_ingredients": ["mushrooms"],
    "cuisine_preference": ["Mediterranean"],
    "max_prep_minutes": 30
  }
}
```
**Response `201`:**
```json
{
  "meal_plan_id": "uuid",
  "days": [
    {
      "day": "Monday",
      "meals": [
        {
          "meal_type": "breakfast",
          "recipe_name": "Overnight Protein Oats",
          "estimated_calories": 320,
          "estimated_protein_g": 22,
          "prep_time_minutes": 5,
          "ingredients": [{ "name": "Rolled oats", "quantity": "80g" }]
        }
      ]
    }
  ]
}
```

---

#### `GET /meal-plans/active` — Current active plan with all entries.
#### `GET /meal-plans/{id}` — Specific plan.
#### `POST /meal-plans/{id}/activate` — Set plan as active.
#### `DELETE /meal-plans/{id}` — Delete a plan (`204`).

#### `GET /meal-plans/{id}/shopping`
**Purpose:** Generate a consolidated shopping list from the plan.

**Response `200`:**
```json
{
  "shopping_list": [
    { "category": "Proteins", "items": [{ "name": "Chicken breast", "total_quantity": "900g" }] },
    { "category": "Produce",  "items": [{ "name": "Avocado", "total_quantity": "7 pieces" }] }
  ]
}
```

---

### Habit & Streak APIs

#### `POST /habits`
**Purpose:** Create a new trackable habit.

**Request:**
```json
{
  "habit_name": "Drink 8 glasses of water",
  "habit_type": "water_intake",
  "target_value": 8,
  "target_unit": "glasses",
  "frequency": "daily",
  "reminder_times": ["08:00", "13:00", "19:00"]
}
```
**Response `201`:** Created habit object.

---

#### `GET /habits` — All active habits.
#### `PUT /habits/{id}` — Update habit settings.
#### `DELETE /habits/{id}` — Soft-delete (sets `is_active = false`).

#### `POST /habits/{id}/log`
**Purpose:** Log today's completion value.

**Request:** `{ "value_achieved": 7 }`
**Response `200`:**
```json
{
  "is_completed": true,
  "streak": { "current_streak": 13, "longest_streak": 30 },
  "milestone_reached": "14_days"
}
```

---

#### `GET /streaks/summary`
**Purpose:** All streak data across habits + global meal logging streak.

**Response `200`:**
```json
{
  "global_logging_streak": { "current": 12, "longest": 30 },
  "habits": [{ "habit_name": "Water intake", "current_streak": 13, "longest_streak": 30 }]
}
```

---

#### `GET /habits/suggested` — AI-recommended habits from pattern analysis.

---

### Water Tracking APIs

#### `POST /water/log`
**Purpose:** Add a water intake entry.
**Request:** `{ "amount_ml": 250 }`
**Response `200`:** `{ "today_total_ml": 1750, "target_ml": 2500, "glasses_logged": 7 }`

#### `GET /water/today` — Today's hydration summary.
#### `GET /water/history?days=7` — N-day history.

---

### AI Coach APIs

#### `POST /ai/chat`
**Purpose:** Send message to the AI coach. Returns **Server-Sent Events (SSE) stream**.

**Request:** `{ "session_id": "uuid", "message": "What should I eat tonight?" }`

**Response:** `Content-Type: text/event-stream`
```
data: {"chunk": "Based on your remaining macros"}
data: {"chunk": " and muscle gain goal..."}
data: {"chunk": " I recommend a salmon and quinoa bowl."}
data: {"done": true, "session_id": "uuid"}
```

---

#### `GET /ai/chat/history?session_id={uuid}`
**Purpose:** Retrieve conversation history. Without `session_id` returns all session previews.

**Response `200`:**
```json
{
  "sessions": [
    { "session_id": "uuid", "started_at": "2026-04-15T18:42:00Z", "preview": "What should I eat tonight?", "message_count": 6 }
  ]
}
```

---

#### `POST /ai/meal-score`
**Purpose:** AI scores a meal out of 100 with grade and suggestions.

**Request:** `{ "items": [{ "name": "Avocado Toast", "quantity_g": 150 }] }`
**Response `200`:**
```json
{ "score": 82, "grade": "B+", "feedback": "Great healthy fats. Add protein.", "suggestions": ["Add Greek yogurt"] }
```

---

#### `POST /ai/food-swap`
**Purpose:** Get a healthier alternative.
**Request:** `{ "food_name": "White rice", "reason": "lower_carbs" }`
**Response `200`:** `{ "alternatives": [{ "name": "Cauliflower rice", "benefit": "70% fewer carbs" }] }`

---

#### `GET /ai/daily-tip`
**Purpose:** Personalized daily tip (cached per user for 24h).
**Response `200`:** `{ "tip": "You skipped breakfast 3 times this week...", "category": "habit" }`

---

#### `POST /ai/analyze-day`
**Purpose:** Full AI analysis of today's eating.
**Response `200`:**
```json
{
  "summary": "Strong start! Breakfast was balanced. Lunch was high in sodium.",
  "score": 78,
  "highlights": ["Hit protein target for the first time this week"],
  "improvements": ["Add fiber to dinner"],
  "tomorrow_suggestion": "Pre-plan using Tuesday's meal plan entry."
}
```

---

### Analytics & Insights APIs

#### `GET /insights?unread_only=true`
**Response `200`:**
```json
{
  "insights": [
    {
      "id": "uuid", "type": "pattern_detected",
      "title": "Late-Night Snacking Pattern",
      "content": "You consume ~35% of daily calories after 9 PM on weekdays.",
      "is_read": false
    }
  ]
}
```

#### `POST /insights/{id}/read` — Mark insight as read.

---

#### `GET /analytics/weekly?week_start=2026-04-14`
**Response `200`:**
```json
{
  "week": "Apr 14–20 2026",
  "avg_daily_calories": 2080,
  "calorie_target": 2300,
  "days": [{ "date": "2026-04-14", "calories": 1980, "protein_g": 88, "carbs_g": 230 }],
  "top_logged_foods": ["Avocado Toast", "Grilled Chicken"],
  "goal_hit_days": 5
}
```

---

#### `GET /analytics/trends?days=30`
**Response `200`:** Daily macro time-series for charting + week-on-week change percentages.

---

#### `GET /analytics/patterns`
**Response `200`:**
```json
{
  "patterns": [
    { "type": "protein_deficit", "confidence": 0.72, "message": "Under protein target on 65% of days", "suggestion": "Add Greek yogurt to breakfast" }
  ]
}
```

---

#### `GET /analytics/goal-progress`
**Response `200`:**
```json
{
  "goals": [
    { "goal": "muscle_gain", "protein_avg_g": 88, "protein_target_g": 115, "pct_achieved": 76, "on_track": false }
  ]
}
```

---

#### `GET /analytics/nutrient-gaps`
**Response `200`:**
```json
{
  "gaps": [
    { "nutrient": "Vitamin D", "avg_intake": 3.1, "target": 15, "unit": "mcg", "gap_pct": 79 },
    { "nutrient": "Iron",      "avg_intake": 8.2, "target": 18, "unit": "mg",  "gap_pct": 54 }
  ]
}
```

---

## 5. 🔄 Data Flow

### Meal Logging Flow
```
User searches food → GET /food/search
     |
     +--> Backend: check food_items cache → Open Food Facts → USDA → Nutritionix (parallel)
     |
User selects food + quantity → POST /meals/log
     |
     +--> Compute macro totals from quantities
     +--> Write meal_log + meal_log_items to Supabase
     +--> Async: AI meal scoring → update ai_meal_score
     +--> StreakEngine: update global logging streak
     |
Response: meal_log_id + totals + ai_score → Frontend updates calorie ring
```

### AI Chat Flow
```
User types message → POST /ai/chat { session_id, message }
     |
Parallel DB fetch:
  profile + today_summary + 7-day meal history + weather (optional)
     |
PromptBuilder injects full context into system message
     |
AIOrchestrator:
  Try Gemini Flash (streaming)
     +--> Success: stream chunks via SSE → browser EventSource
     +--> Error: record failure → fallback to Groq LLaMA (streaming)
     |
On stream complete:
  Save user + assistant messages to ai_conversations
```

### Analytics Generation Flow
```
User visits /analytics → GET /analytics/weekly + GET /analytics/patterns
     |
weekly:   Supabase aggregation on meal_logs (GROUP BY date)
patterns: PatternDetector runs async coroutines on 30-day logs
     |
Significant patterns (confidence >= 0.7) → InsightGenerator → ai_insights table
     |
Response → Frontend renders calorie chart + macro bars + heatmap
```

### Meal Plan Generation Flow
```
User clicks "Generate Plan" → POST /meal-plans/generate
     |
Backend builds full user context: profile + goals + restrictions + recent history
     |
PromptBuilder.meal_plan_prompt(context) → structured JSON schema prompt
     |
AIOrchestrator.generate_meal_plan() → Gemini (primary) → Groq (fallback)
     |
Parse + validate 7-day JSON response
Write meal_plans + meal_plan_entries rows
Deactivate previous active plan
     |
Response: full plan → Frontend renders 7-column meal grid
```

---

## 6. 🤖 AI Integration

### Provider Strategy

| Scenario | Provider |
|---|---|
| All requests (primary) | Gemini 1.5 Flash |
| Gemini rate-limited or down | Groq LLaMA 3.1 8B Instant |
| Circuit breaker tripped (>=3 failures in 60s) | Groq only for 2 minutes, then retry Gemini |
| Structured JSON output (meal plans) | Gemini Flash with JSON mode |

### Context Injected into Every AI Request

```
USER PROFILE:
  age, gender, weight, height, activity_level, health_goals, dietary_restrictions

TODAY SO FAR:
  calories consumed vs target, protein/carbs/fat totals, water logged

RECENT PATTERNS (7 days):
  avg daily intake, most logged foods, meal timing

TEMPORAL CONTEXT:
  current time + day of week (for meal timing advice)

OPTIONAL SIGNALS:
  weather condition + temperature
```

### AI Use Cases

| Feature | Output Format | Provider |
|---|---|---|
| Chat coach | Streaming text | Gemini / Groq |
| Meal scoring | `{score, grade, feedback, suggestions}` JSON | Gemini |
| Meal plan | 7-day structured JSON | Gemini |
| Food swap | Alternatives with reasons | Gemini / Groq |
| Daily tip | One-sentence text | Gemini (cached 24h) |
| Day analysis | Summary + highlights + improvements | Gemini |
| Habit suggestions | Named habits with reasons | Gemini |

### Token Management
- Chat history capped at **last 20 messages per session** to stay within context window
- Meal plan prompt ~800 tokens; response ~2,000 tokens
- Daily tip cached per user for 24h (reduces API calls by ~80%)

---

## 7. ⚙️ Backend Tech Stack

| Layer | Technology | Rationale |
|---|---|---|
| **Framework** | FastAPI (Python 3.12) | Async, auto OpenAPI docs, Pydantic validation, SSE support |
| **Database** | Supabase Postgres | Managed DB + Auth + Storage + Realtime; generous free tier |
| **Auth** | Supabase Auth | Email + Google OAuth; JWT auto-managed |
| **AI Primary** | Google Gemini 1.5 Flash | Fast, free tier, JSON mode, streaming |
| **AI Fallback** | Groq LLaMA 3.1 8B | Very fast inference, generous free tier |
| **Food APIs** | Open Food Facts + USDA + Nutritionix | Free; covers packaged goods, whole foods, NLP |
| **Recipe APIs** | TheMealDB + Spoonacular | Free tiers sufficient for plan enrichment |
| **Caching** | `cachetools.TTLCache` (L1) + Supabase `food_items` (L2) | No Redis needed; zero cost |
| **HTTP Client** | `httpx` async | Non-blocking external API calls |
| **Backend Hosting** | Railway / Render | Free/low-cost; easy FastAPI deploy |
| **Frontend Hosting** | Vercel | Next.js optimised, generous free tier |
| **File Storage** | Supabase Storage | Meal photos; S3-compatible, 1GB free |

---

## 8. 🔐 Authentication & Security

### JWT Flow
1. User logs in → Supabase issues `access_token` (1h) + `refresh_token` (7d)
2. Frontend stores tokens in `httpOnly` cookies (not localStorage)
3. Every API request sends `Authorization: Bearer <access_token>`
4. FastAPI middleware validates signature + expiry with Supabase public key
5. `user_id` extracted and scoped to all DB queries

### Row Level Security (RLS)
Every table enforces data isolation at the database level:
```sql
create policy "own data only" on meal_logs
  for all using (auth.uid() = user_id);
-- Repeated for ALL tables
```
Even if application logic has a bug, the DB enforces user isolation.

### Rate Limiting (in-memory sliding window per `user_id`)

| Endpoint | Limit |
|---|---|
| `POST /ai/chat` | 20 req / user / hour |
| `POST /meal-plans/generate` | 5 req / user / day |
| `GET /food/search` | 60 req / user / minute |

### Input Validation
All request bodies validated by Pydantic v2 schemas before reaching service layer.

### File Upload Security
- MIME whitelist: `image/jpeg`, `image/png`, `image/webp`
- Max size: 5MB per meal photo
- Stored in Supabase Storage bucket with private access policy

### API Key Security
- All third-party keys in environment variables only
- Supabase Service Role key strictly server-side only
- Keys rotated immediately if exposed

---

## 9. 📊 Scalability Considerations

### Caching Layers

| Layer | Data | TTL | Storage |
|---|---|---|---|
| L1 in-memory | Food search results | 24h | `TTLCache` (max 5,000 entries) |
| L1 in-memory | Daily AI tip | 24h | `TTLCache` (max 1,000) |
| L1 in-memory | Weather data | 6h | `TTLCache` (max 500) |
| L2 persistent | Food nutrition data | Permanent | `food_items` Supabase table |
| L2 persistent | AI insights | 7 days | `ai_insights` with `valid_until` |

Target cache hit rate: **>70%** for food searches.

### Background Jobs (APScheduler or Supabase pg_cron)

| Job | Schedule | Action |
|---|---|---|
| AI Meal Scoring | After `POST /meals/log` (async) | Score meal, write `ai_meal_score` |
| Daily Tip Pre-generation | 06:00 user timezone | Generate and cache tip |
| Pattern Detection | Nightly 02:00 UTC | Run pattern detector for active users |
| Streak Recalculation | Midnight UTC | Detect broken streaks, notify users |
| Nutrient Gap Analysis | Sunday 03:00 UTC | Aggregate weekly micronutrient data |

### API Optimizations
- External food API calls use `asyncio.gather()` — parallel, not sequential (3x faster)
- `food_items` table is a write-once cache; repeat searches skip all external calls
- Analytics use pre-computed daily aggregates, not raw log table scans
- Composite DB indexes on `(user_id, meal_date)` for all time-range queries

---

## 10. 🧱 Folder Structure

```
claireat-backend/
├── app/
│   ├── main.py                     # FastAPI app init, CORS, lifespan
│   ├── config.py                   # Settings (pydantic-settings)
│   ├── dependencies.py             # Auth middleware, injected clients
│   │
│   ├── routers/
│   │   ├── auth.py                 # /auth/*
│   │   ├── profile.py              # /profile/*
│   │   ├── food.py                 # /food/*
│   │   ├── meals.py                # /meals/*
│   │   ├── meal_plans.py           # /meal-plans/*
│   │   ├── habits.py               # /habits/*, /streaks/*
│   │   ├── water.py                # /water/*
│   │   ├── ai_coach.py             # /ai/*
│   │   ├── insights.py             # /insights/*
│   │   └── analytics.py            # /analytics/*
│   │
│   ├── services/
│   │   ├── ai/
│   │   │   ├── orchestrator.py     # Primary/fallback routing + circuit breaker
│   │   │   ├── gemini_service.py   # Gemini Flash: chat + JSON mode
│   │   │   ├── groq_service.py     # Groq LLaMA fallback
│   │   │   ├── prompt_builder.py   # Context-aware prompt construction
│   │   │   └── response_parser.py  # Validate + parse AI JSON responses
│   │   │
│   │   ├── food/
│   │   │   ├── food_service.py     # Cascade search orchestrator
│   │   │   ├── open_food_facts.py  # Barcode + packaged food
│   │   │   ├── usda_service.py     # Whole food database
│   │   │   ├── nutritionix.py      # NLP parsing + restaurant data
│   │   │   └── nutrition_calc.py   # Macro/micro math
│   │   │
│   │   ├── meals/
│   │   │   ├── meal_service.py     # CRUD + macro aggregation
│   │   │   ├── meal_scorer.py      # Async AI scoring after log
│   │   │   └── meal_planner.py     # AI plan generation + DB write
│   │   │
│   │   ├── habits/
│   │   │   ├── habit_service.py    # Habit CRUD + daily log
│   │   │   └── streak_engine.py    # Streak math + milestone detection
│   │   │
│   │   ├── analytics/
│   │   │   ├── report_service.py   # Weekly/monthly aggregation
│   │   │   ├── pattern_detector.py # Behavioral pattern analysis
│   │   │   └── insight_generator.py # Patterns -> ai_insights rows
│   │   │
│   │   └── external/
│   │       ├── weather_service.py  # Open Meteo
│   │       ├── recipe_service.py   # TheMealDB + Spoonacular
│   │       └── location_service.py # IPinfo locale
│   │
│   ├── schemas/                    # Pydantic request/response models
│   │   ├── auth.py
│   │   ├── profile.py
│   │   ├── food.py
│   │   ├── meal.py
│   │   ├── habit.py
│   │   └── ai.py
│   │
│   ├── core/
│   │   ├── supabase_client.py      # Singleton client
│   │   ├── cache.py                # TTLCache manager
│   │   ├── rate_limiter.py         # Per-user sliding window
│   │   ├── exceptions.py           # HTTP exception handlers
│   │   └── logging.py              # Structured JSON logging
│   │
│   └── utils/
│       ├── tdee_calculator.py      # Mifflin-St Jeor BMR + TDEE
│       ├── nutrition_utils.py      # Nutrient math helpers
│       └── date_utils.py           # Timezone-aware date utilities
│
├── tests/
│   ├── test_auth.py
│   ├── test_food.py
│   ├── test_meals.py
│   ├── test_habits.py
│   ├── test_ai.py
│   └── test_analytics.py
│
├── supabase/
│   └── migrations/
│       ├── 001_profiles.sql
│       ├── 002_food_items.sql
│       ├── 003_meal_logs.sql
│       ├── 004_meal_plans.sql
│       ├── 005_habits_streaks.sql
│       ├── 006_ai_tables.sql
│       ├── 007_water_logs.sql
│       └── 008_rls_policies.sql
│
├── requirements.txt
├── .env.example
├── Dockerfile
└── README.md
```

---

## 11. 🌐 External APIs (All Free)

| API | Purpose | Free Tier | Base URL |
|---|---|---|---|
| Open Food Facts | Barcode + packaged food DB | Unlimited (open source) | `world.openfoodfacts.org/api/v2` |
| USDA FoodData Central | Whole food nutrition | Unlimited (free API key) | `api.nal.usda.gov/fdc/v1` |
| Nutritionix | NLP food parsing, restaurants | 500 req/day | `api.nutritionix.com/v1_1` |
| Edamam Food DB | Recipe nutrition analysis | 1,000 req/month | `api.edamam.com/api/food-database/v2` |
| TheMealDB | Recipe details for meal plans | Unlimited | `www.themealdb.com/api/json/v1/1` |
| Spoonacular | Ingredient parsing + plan enrichment | 150 req/day | `api.spoonacular.com` |
| Wger Workout | Exercise calorie burn data | Unlimited (open source) | `wger.de/api/v2` |
| Open Meteo | Weather for contextual suggestions | Unlimited (no key needed) | `api.open-meteo.com/v1` |
| IPinfo | User locale from IP | 50K req/month | `ipinfo.io/json` |
| Google Gemini Flash | Primary AI | Free tier (AI Studio) | `generativelanguage.googleapis.com` |
| Groq LLaMA 3.1 | AI fallback | Free tier | `api.groq.com/openai/v1` |

---

## 12. 🚀 Development Phases

| Phase | Duration | Key Deliverables |
|---|---|---|
| **1 — Foundation** | Weeks 1–2 | Supabase schema + RLS migrations, FastAPI scaffolding, Auth JWT middleware, Profile CRUD + TDEE calc, Food search (Open Food Facts + USDA), Meal log CRUD |
| **2 — Core Intelligence** | Weeks 3–4 | Gemini + Groq orchestrator with circuit breaker, Streaming SSE chat, Context-aware prompts, Meal scoring, Barcode lookup, NLP parsing |
| **3 — Habits & Engagement** | Week 5 | Habit CRUD, Streak engine + milestones, Water tracking, Daily summaries |
| **4 — Plans & Analytics** | Week 6 | AI meal plan generation, Recipe integration, Analytics aggregations, Pattern detection, Insight generator |
| **5 — Polish & Production** | Week 7 | Multi-layer caching, Rate limiting, Structured logging, Test suite, Dockerfile, API documentation |

---

*clairEat Backend Specification v1.0 — FastAPI + Supabase + Gemini/Groq*
