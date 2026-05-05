# ClairEat — Frontend ↔ Backend Integration Guide

> Covers every API the Next.js frontend needs to call, the exact request shapes, authentication flow, and SSE streaming setup.

---

## 1. Setup

### Install the Supabase client in the frontend

```bash
npm install @supabase/supabase-js
```

### Environment variables (Next.js `.env.local`)

```env
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-supabase-anon-key
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/v1
```

---

## 2. Auth Flow

Authentication is handled **entirely by Supabase Auth**. The backend validates the same JWT that Supabase issues to the client.

### 2a. Create the Supabase client (`lib/supabase.ts`)

```ts
import { createClient } from '@supabase/supabase-js'

export const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
)
```

### 2b. Register / Login

```ts
// Register
const { data, error } = await supabase.auth.signUp({
  email: 'user@example.com',
  password: 'SecurePass123!',
})

// Login
const { data, error } = await supabase.auth.signInWithPassword({
  email: 'user@example.com',
  password: 'SecurePass123!',
})
```

### 2c. Get the JWT for backend calls

```ts
const { data: { session } } = await supabase.auth.getSession()
const token = session?.access_token   // pass this as Bearer token
```

### 2d. Create a typed API client (`lib/api.ts`)

```ts
const API = process.env.NEXT_PUBLIC_API_BASE_URL

async function apiFetch(path: string, options: RequestInit = {}) {
  const { data: { session } } = await supabase.auth.getSession()
  const token = session?.access_token

  const res = await fetch(`${API}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(options.headers ?? {}),
    },
  })

  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err?.error?.message ?? `API error ${res.status}`)
  }

  if (res.status === 204) return null
  return res.json()
}

export const api = {
  get:    (path: string)              => apiFetch(path),
  post:   (path: string, body: any)  => apiFetch(path, { method: 'POST',   body: JSON.stringify(body) }),
  put:    (path: string, body: any)  => apiFetch(path, { method: 'PUT',    body: JSON.stringify(body) }),
  delete: (path: string)             => apiFetch(path, { method: 'DELETE' }),
}
```

---

## 3. Page → Endpoint Mapping

### `/onboarding`

```ts
// Submit onboarding form
const result = await api.post('/profile/onboarding', {
  full_name: 'Chirag',
  age: 26,
  gender: 'male',
  height_cm: 175,
  weight_kg: 72,
  target_weight_kg: 78,
  activity_level: 'moderate',
  health_goals: ['muscle_gain'],
  dietary_restrictions: ['gluten_free'],
  allergies: ['peanuts'],
})
// result.profile  — full profile object
// result.tdee     — { bmr, tdee, goal_calories, protein_g, carbs_g, fat_g }
```

---

### `/` (Dashboard)

```ts
const [todayMeals, dailySummary, waterToday, streaks, insights] = await Promise.all([
  api.get('/meals/today'),
  api.get('/meals/daily-summary'),
  api.get('/water/today'),
  api.get('/streaks/summary'),
  api.get('/insights?unread_only=true'),
])
```

**`/meals/daily-summary` response shape:**
```json
{
  "totals":      { "calories": 1240, "protein_g": 62, "carbs_g": 145, "fat_g": 38 },
  "targets":     { "calories": 2300, "protein_g": 115, "carbs_g": 259, "fat_g": 64 },
  "pct_complete": { "calories": 54, "protein": 54 },
  "water_ml": 1500,
  "water_target_ml": 2500
}
```

---

### `/log-meal`

**Step 1 — Search food:**

```ts
const results = await api.get(`/food/search?q=${encodeURIComponent(query)}&limit=10`)
// results.results[]  ← array of food items with nutrition per 100g
```

**Step 2 — Barcode scan:**

```ts
const food = await api.get(`/food/barcode/${barcodeValue}`)
```

**Step 3 — NLP input:**

```ts
const parsed = await api.get(`/food/nlp?q=${encodeURIComponent('2 boiled eggs and a banana')}`)
// parsed.parsed_items[]  ← [{ name, quantity_g, calories, protein_g, ... }]
```

**Step 4 — Log the meal:**

```ts
const logged = await api.post('/meals/log', {
  meal_date: '2026-04-15',
  meal_type: 'breakfast',          // breakfast | lunch | dinner | snack | pre_workout | post_workout
  items: [
    { food_item_id: 'uuid', quantity_g: 200 },
    { custom_food_name: 'Homemade Granola', quantity_g: 50, calories: 230, protein_g: 5, carbs_g: 34, fat_g: 9 }
  ],
  mood_before: 'happy',
  hunger_level_before: 7,
  notes: 'Ate slowly',
})
// logged.meal_log_id, logged.total_calories, logged.ai_meal_score (async, may be null initially)
```

**Upload meal photo:**

```ts
const formData = new FormData()
formData.append('file', photoFile)   // File object from <input type="file">

const { data: { session } } = await supabase.auth.getSession()
await fetch(`${API}/meals/${mealLogId}/photo`, {
  method: 'POST',
  headers: { Authorization: `Bearer ${session?.access_token}` },
  body: formData,
})
```

---

### `/meal-plan`

```ts
// Generate a new plan
const plan = await api.post('/meal-plans/generate', {
  start_date: '2026-04-21',
  preferences: {
    exclude_ingredients: ['mushrooms'],
    cuisine_preference: ['Mediterranean'],
    max_prep_minutes: 30,
  },
})
// plan.days[]  ← 7 days, each with meals[]

// Get current active plan
const active = await api.get('/meal-plans/active')

// Get shopping list
const shopping = await api.get(`/meal-plans/${plan.meal_plan_id}/shopping`)
// shopping.shopping_list[]  ← [{ category, items: [{ name, total_quantity }] }]
```

---

### `/ai-coach` — Streaming SSE Chat

Use the native `EventSource` API (or a custom hook). The backend returns `text/event-stream`.

```ts
// React hook example
function useAIChat(sessionId?: string) {
  const [messages, setMessages] = useState<Message[]>([])
  const [streaming, setStreaming] = useState('')

  const send = async (userMessage: string) => {
    const { data: { session } } = await supabase.auth.getSession()
    const token = session?.access_token

    // Add user message immediately
    setMessages(prev => [...prev, { role: 'user', content: userMessage }])

    const response = await fetch(`${API}/ai/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ session_id: sessionId, message: userMessage }),
    })

    const reader = response.body!.getReader()
    const decoder = new TextDecoder()
    let aiText = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      const lines = decoder.decode(value).split('\n')
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const payload = JSON.parse(line.slice(6))
          if (payload.chunk) {
            aiText += payload.chunk
            setStreaming(aiText)              // live update as tokens arrive
          }
          if (payload.done) {
            setMessages(prev => [...prev, { role: 'assistant', content: aiText }])
            setStreaming('')
          }
        }
      }
    }
  }

  return { messages, streaming, send }
}
```

**Other AI endpoints:**

```ts
// Score a meal manually
const score = await api.post('/ai/meal-score', {
  items: [{ name: 'Avocado Toast', quantity_g: 150 }]
})
// { score: 82, grade: "B+", feedback: "...", suggestions: ["..."] }

// Healthier food swap
const swap = await api.post('/ai/food-swap', {
  food_name: 'White rice',
  reason: 'lower_carbs',
})

// Daily personalised tip (cached per user, 24h)
const tip = await api.get('/ai/daily-tip')
// { tip: "...", category: "habit", generated_at: "..." }

// Full day AI analysis
const analysis = await api.post('/ai/analyze-day', {})
// { summary, score, highlights[], improvements[], tomorrow_suggestion }
```

---

### `/analytics`

```ts
const [weekly, trends, patterns, goalProgress, gaps] = await Promise.all([
  api.get('/analytics/weekly'),
  api.get('/analytics/trends?days=30'),
  api.get('/analytics/patterns'),
  api.get('/analytics/goal-progress'),
  api.get('/analytics/nutrient-gaps'),
])
```

Feed `trends.days[]` directly into a Recharts `<LineChart>` for the macro trend graph.

---

### `/wellness`

```ts
const [insights, gaps, suggested, tip] = await Promise.all([
  api.get('/insights'),
  api.get('/analytics/nutrient-gaps'),
  api.get('/habits/suggested'),
  api.get('/ai/daily-tip'),
])
```

---

### `/habits`

```ts
// Create habit
const habit = await api.post('/habits', {
  habit_name: 'Drink 8 glasses of water',
  habit_type: 'water_intake',
  target_value: 8,
  target_unit: 'glasses',
  frequency: 'daily',
})

// Log today's value
const result = await api.post(`/habits/${habit.id}/log`, { value_achieved: 6 })
// { is_completed: false, streak: { current_streak: 12, longest_streak: 30 }, milestone_reached: null }

// Water logging
await api.post('/water/log', { amount_ml: 250 })
const waterStatus = await api.get('/water/today')
// { today_total_ml: 1750, target_ml: 2625, glasses_logged: 7, pct_complete: 66.7 }
```

---

## 4. Error Handling

All errors follow this shape:

```json
{
  "error": {
    "code": "NOT_FOUND",
    "message": "Meal log abc not found.",
    "detail": null
  }
}
```

| HTTP Status | Code | Meaning |
|---|---|---|
| 400 | `VALIDATION_ERROR` | Bad request body |
| 401 | `UNAUTHORIZED` | Missing or expired token |
| 403 | `FORBIDDEN` | Insufficient permissions |
| 404 | `NOT_FOUND` | Resource doesn't exist |
| 409 | `DUPLICATE` | Duplicate resource |
| 422 | — | Pydantic schema validation failed |
| 429 | `RATE_LIMIT_EXCEEDED` | Too many requests (check `Retry-After` header) |
| 502 | `EXTERNAL_API_ERROR` | External food/AI API unreachable |
| 503 | `AI_SERVICE_ERROR` | Both Gemini and Groq unavailable |

Recommended frontend error handler:

```ts
try {
  const data = await api.post('/meals/log', payload)
} catch (err: any) {
  if (err.message.includes('RATE_LIMIT')) {
    toast.error('Too many requests. Please slow down.')
  } else if (err.message.includes('AI_SERVICE')) {
    toast.warning('AI temporarily unavailable. Try again in a minute.')
  } else {
    toast.error(err.message)
  }
}
```

---

## 5. Token Refresh

Supabase handles refresh automatically. For long sessions, listen to auth state:

```ts
// In your root layout or auth context
useEffect(() => {
  const { data: { subscription } } = supabase.auth.onAuthStateChange(
    (event, session) => {
      if (event === 'SIGNED_OUT') router.push('/login')
      if (event === 'TOKEN_REFRESHED') {
        // session.access_token is already the new token
        // apiFetch() calls supabase.auth.getSession() on each call, so it auto-picks up the new token
      }
    }
  )
  return () => subscription.unsubscribe()
}, [])
```

---

## 6. CORS

The backend allows requests from origins listed in `ALLOWED_ORIGINS`. For local development ensure `.env` contains:

```env
ALLOWED_ORIGINS=http://localhost:3000
```

For production append your Vercel URL:

```env
ALLOWED_ORIGINS=http://localhost:3000,https://claireat.vercel.app,https://claireat.com
```
