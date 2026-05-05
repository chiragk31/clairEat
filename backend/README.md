# ClairEat Backend

> **FastAPI + Supabase + Gemini/Groq** — Production-ready intelligent nutrition platform API.

---

## Stack

| Layer | Technology |
|---|---|
| Framework | FastAPI (Python 3.12) |
| Database | Supabase Postgres (managed) |
| Auth | Supabase Auth (JWT + Google OAuth) |
| AI Primary | Google Gemini 1.5 Flash |
| AI Fallback | Groq LLaMA 3.1 8B (circuit-breaker) |
| Food APIs | Open Food Facts · USDA · Nutritionix |
| Caching | TTLCache L1 (in-memory) + Supabase L2 |
| Container | Docker (multi-stage, non-root) |

---

## Quick Start

### 1. Clone and activate your venv

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env — fill in Supabase, Gemini, Groq keys at minimum
```

### 3. Run the Supabase migration

Open the [Supabase SQL Editor](https://supabase.com/dashboard) and paste the entire contents of:

```
supabase/migrations/001_full_schema.sql
```

This creates all tables, indexes, enum types, and Row Level Security policies.

### 4. Start the dev server

```bash
uvicorn app.main:app --reload --port 8000
```

API available at: `http://localhost:8000`  
Swagger docs: `http://localhost:8000/docs`  
ReDoc: `http://localhost:8000/redoc`

---

## Project Structure

```
backend/
├── app/
│   ├── main.py                 # App factory, CORS, lifespan, routers
│   ├── config.py               # Pydantic-settings (all env vars)
│   ├── dependencies.py         # JWT auth middleware, DB injection
│   │
│   ├── routers/                # One file per feature domain
│   │   ├── auth.py             # /v1/auth/*
│   │   ├── profile.py          # /v1/profile/*
│   │   ├── food.py             # /v1/food/*
│   │   ├── meals.py            # /v1/meals/*
│   │   ├── meal_plans.py       # /v1/meal-plans/*
│   │   ├── habits.py           # /v1/habits/* + /v1/streaks/*
│   │   ├── water.py            # /v1/water/*
│   │   ├── ai_coach.py         # /v1/ai/*  (SSE streaming)
│   │   ├── insights.py         # /v1/insights/*
│   │   └── analytics.py        # /v1/analytics/*
│   │
│   ├── services/               # All business logic lives here
│   │   ├── ai/                 # Gemini · Groq · Orchestrator · Prompts
│   │   ├── food/               # Open Food Facts · USDA · Nutritionix
│   │   ├── meals/              # Meal CRUD · Scorer · Planner
│   │   ├── habits/             # Habit CRUD · Streak Engine
│   │   ├── analytics/          # Reports · Pattern Detector · Insights
│   │   └── external/           # Weather (Open Meteo) · Location (IPInfo)
│   │
│   ├── schemas/                # Pydantic request/response models
│   ├── core/                   # Cache · Rate limiter · Exceptions · Logging
│   └── utils/                  # TDEE calc · Nutrition math · Date helpers
│
├── supabase/
│   └── migrations/
│       └── 001_full_schema.sql
│
├── tests/
├── .env.example
├── Dockerfile
├── pytest.ini
└── requirements.txt
```

---

## API Base URL

```
http://localhost:8000/v1        # development
https://api.claireat.com/v1    # production
```

All protected endpoints require:

```http
Authorization: Bearer <supabase_access_token>
```

---

## Key Features

### 🔐 Auth
- Email/password register + login via Supabase Auth
- Google OAuth redirect
- JWT refresh token flow

### 📊 Profile & TDEE
- Full onboarding in one `POST /profile/onboarding` call
- Mifflin-St Jeor BMR → TDEE → goal-adjusted calories + macro targets
- Auto-recalculates macros on profile update

### 🍎 Food Search (Multi-Source Cascade)
1. L1 in-memory TTLCache (sub-millisecond)
2. L2 Supabase `food_items` table (persistent)
3. Open Food Facts + USDA queried **in parallel** via `asyncio.gather`
4. Nutritionix NLP for natural language (`"2 boiled eggs and a banana"`)

### 🍽️ Meal Logging
- Log meals with multiple food items
- Auto-computes macro totals per meal
- AI scoring runs **asynchronously** after log (non-blocking)
- Photo upload to Supabase Storage (≤5 MB, JPEG/PNG/WebP)

### 🤖 AI Coach (Gemini + Groq)
- **Circuit breaker**: after 3 Gemini failures in 60s → routes to Groq for 2 min
- **Streaming SSE** chat with full user context injection
- Meal scoring, food swap suggestions, daily tip (cached 24h/user), day analysis

### 📅 Meal Plans
- 7-day AI-generated plan with structured JSON output
- Auto-deactivates previous plan on new generation
- Shopping list auto-categorised (Proteins / Produce / Grains / Dairy / Other)

### 🏆 Habits & Streaks
- Habit CRUD with daily log upsert
- Streak milestones at 7 / 14 / 21 / 30 / 60 / 90 / 180 / 365 days
- AI-suggested habits from detected patterns

### 📈 Analytics & Insights
- Weekly report, 30-day macro trends, goal progress, nutrient gap analysis
- Pattern detector: protein deficits, breakfast skipping, late-night eating, weekend differences
- Patterns with confidence ≥ 0.70 auto-converted to `ai_insights` rows

---

## Docker

```bash
docker build -t claireat-backend .
docker run -p 8000:8000 --env-file .env claireat-backend
```

---

## Running Tests

```bash
pytest tests/ -v
```

---

## Rate Limits

| Endpoint | Limit |
|---|---|
| `POST /v1/ai/chat` | 20 req / user / hour |
| `POST /v1/meal-plans/generate` | 5 req / user / day |
| `GET /v1/food/search` | 60 req / user / minute |
