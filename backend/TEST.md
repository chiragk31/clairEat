# ClairEat API — Manual Test Guide

> Test every endpoint step-by-step using `curl`.  
> **Base URL:** `http://localhost:8000/v1`  
> **Tip:** Run endpoints in the order listed — each section builds on the previous one.

---

## Setup

```bash
# Set these once in your terminal session
BASE="http://localhost:8000/v1"
TOKEN=""           # fill in after login (step 2)
```

---

## 0. Health Check

```bash
# Root
curl http://localhost:8000/

# Health (shows cache stats)
curl http://localhost:8000/health
```

**Expected:**
```json
{ "status": "healthy", "version": "1.0.0", "cache": { ... } }
```

---

## 1. Auth

### 1a. Register

```bash
curl -s -X POST "$BASE/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "testuser@claireat.com",
    "password": "SecurePass123!",
    "full_name": "Test User"
  }' | python3 -m json.tool
```

**Expected 201:**
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

---

### 1b. Login

```bash
curl -s -X POST "$BASE/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "testuser@claireat.com",
    "password": "SecurePass123!"
  }' | python3 -m json.tool
```

**Copy the `access_token` and set:**
```bash
TOKEN="paste_your_access_token_here"
```

---

### 1c. Refresh Token

```bash
curl -s -X POST "$BASE/auth/refresh" \
  -H "Content-Type: application/json" \
  -d '{ "refresh_token": "paste_refresh_token_here" }' | python3 -m json.tool
```

---

### 1d. Invalid Login (expect 401)

```bash
curl -s -X POST "$BASE/auth/login" \
  -H "Content-Type: application/json" \
  -d '{ "email": "testuser@claireat.com", "password": "wrongpassword" }'
```

---

### 1e. Invalid Email Format (expect 422)

```bash
curl -s -X POST "$BASE/auth/register" \
  -H "Content-Type: application/json" \
  -d '{ "email": "not-an-email", "password": "pass123" }'
```

---

### 1f. Logout

```bash
curl -s -X POST "$BASE/auth/logout" \
  -H "Authorization: Bearer $TOKEN"
# Expected: 204 No Content (empty body)
```

---

## 2. Profile & Onboarding

### 2a. Complete Onboarding

```bash
curl -s -X POST "$BASE/profile/onboarding" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "Test User",
    "age": 26,
    "gender": "male",
    "height_cm": 175,
    "weight_kg": 72,
    "target_weight_kg": 78,
    "activity_level": "moderate",
    "health_goals": ["muscle_gain"],
    "dietary_restrictions": ["gluten_free"],
    "allergies": ["peanuts"],
    "timezone": "Asia/Kolkata"
  }' | python3 -m json.tool
```

**Expected 201:** `{ "profile": {...}, "tdee": { "bmr": ..., "goal_calories": ..., "protein_g": ... } }`

---

### 2b. Get Profile

```bash
curl -s "$BASE/profile" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

---

### 2c. Update Profile (partial — only weight)

```bash
curl -s -X PUT "$BASE/profile" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{ "weight_kg": 73.5 }' | python3 -m json.tool
```

---

### 2d. Get Latest TDEE

```bash
curl -s "$BASE/profile/tdee" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

---

### 2e. Missing Auth (expect 401)

```bash
curl -s "$BASE/profile"
```

---

## 3. Food Search

### 3a. Search by Name

```bash
curl -s "$BASE/food/search?q=avocado&limit=5" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

---

### 3b. Search — Short Query (expect 422)

```bash
curl -s "$BASE/food/search?q=a" \
  -H "Authorization: Bearer $TOKEN"
```

---

### 3c. Barcode Lookup

```bash
# Barcode for Heinz Ketchup
curl -s "$BASE/food/barcode/0057000000006" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

---

### 3d. Natural Language Parse

```bash
curl -s "$BASE/food/nlp?q=2%20boiled%20eggs%20and%20a%20banana" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

**Expected:**
```json
{ "parsed_items": [ { "name": "Boiled Egg", "quantity_g": 100, "calories": 155 }, ... ] }
```

---

### 3e. Create Custom Food

```bash
curl -s -X POST "$BASE/food/custom" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Homemade Protein Bar",
    "calories_per_100g": 350,
    "protein_per_100g": 25,
    "carbs_per_100g": 30,
    "fat_per_100g": 10,
    "allergens": ["nuts"]
  }' | python3 -m json.tool
```

**Save the `id` for later:**
```bash
FOOD_ID="paste_food_id_here"
```

---

### 3f. Get Food Detail by ID

```bash
curl -s "$BASE/food/$FOOD_ID" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

---

### 3g. Food History & Favorites

```bash
curl -s "$BASE/food/history"   -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
curl -s "$BASE/food/favorites" -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

---

## 4. Meal Logging

### 4a. Log a Meal (with food_item_id)

```bash
curl -s -X POST "$BASE/meals/log" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"meal_date\": \"$(date +%Y-%m-%d)\",
    \"meal_type\": \"breakfast\",
    \"items\": [
      { \"food_item_id\": \"$FOOD_ID\", \"quantity_g\": 60 },
      { \"custom_food_name\": \"Greek Yogurt\", \"quantity_g\": 150, \"calories\": 90, \"protein_g\": 10, \"carbs_g\": 5, \"fat_g\": 1 }
    ],
    \"mood_before\": \"happy\",
    \"hunger_level_before\": 7,
    \"notes\": \"Good breakfast\"
  }" | python3 -m json.tool
```

**Save the `meal_log_id`:**
```bash
MEAL_ID="paste_meal_log_id_here"
```

---

### 4b. Log a Meal — Invalid Type (expect 422)

```bash
curl -s -X POST "$BASE/meals/log" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"meal_date\": \"$(date +%Y-%m-%d)\",
    \"meal_type\": \"midnight_snack\",
    \"items\": [{ \"custom_food_name\": \"Chips\", \"quantity_g\": 50, \"calories\": 250 }]
  }"
```

---

### 4c. Today's Meals

```bash
curl -s "$BASE/meals/today" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

---

### 4d. Daily Summary

```bash
curl -s "$BASE/meals/daily-summary" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

---

### 4e. Meals on a Specific Date

```bash
curl -s "$BASE/meals/date/$(date +%Y-%m-%d)" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

---

### 4f. Meal History (7 days)

```bash
curl -s "$BASE/meals/history?days=7" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

---

### 4g. Get Single Meal Detail

```bash
curl -s "$BASE/meals/$MEAL_ID" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

---

### 4h. Delete a Meal (expect 204)

```bash
curl -s -X DELETE "$BASE/meals/$MEAL_ID" \
  -H "Authorization: Bearer $TOKEN"
# Empty body, status 204
```

---

### 4i. Delete Non-existent Meal (expect 404)

```bash
curl -s -X DELETE "$BASE/meals/00000000-0000-0000-0000-000000000000" \
  -H "Authorization: Bearer $TOKEN"
```

---

## 5. Water Tracking

### 5a. Log Water Intake

```bash
curl -s -X POST "$BASE/water/log" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{ "amount_ml": 500 }' | python3 -m json.tool
```

```bash
# Log again
curl -s -X POST "$BASE/water/log" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{ "amount_ml": 250 }' | python3 -m json.tool
```

---

### 5b. Today's Hydration Summary

```bash
curl -s "$BASE/water/today" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

**Expected:**
```json
{ "today_total_ml": 750, "target_ml": 2520, "glasses_logged": 3.0, "pct_complete": 29.8 }
```

---

### 5c. Water History (7 days)

```bash
curl -s "$BASE/water/history?days=7" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

---

## 6. Habits & Streaks

### 6a. Create a Habit

```bash
curl -s -X POST "$BASE/habits" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "habit_name": "Drink 8 glasses of water",
    "habit_type": "water_intake",
    "target_value": 8,
    "target_unit": "glasses",
    "frequency": "daily",
    "reminder_times": ["08:00", "14:00", "20:00"]
  }' | python3 -m json.tool
```

```bash
HABIT_ID="paste_habit_id_here"
```

---

### 6b. List All Habits

```bash
curl -s "$BASE/habits" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

---

### 6c. Update Habit

```bash
curl -s -X PUT "$BASE/habits/$HABIT_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{ "target_value": 10, "reminder_times": ["09:00", "15:00"] }' | python3 -m json.tool
```

---

### 6d. Log Habit Completion

```bash
curl -s -X POST "$BASE/habits/$HABIT_ID/log" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{ "value_achieved": 8 }' | python3 -m json.tool
```

**Expected:**
```json
{ "is_completed": true, "streak": { "current_streak": 1, "longest_streak": 1 }, "milestone_reached": null }
```

---

### 6e. Log Partial (not completed)

```bash
curl -s -X POST "$BASE/habits/$HABIT_ID/log" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{ "value_achieved": 5 }' | python3 -m json.tool
```

---

### 6f. Get Habit Streak

```bash
curl -s "$BASE/habits/$HABIT_ID/streak" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

---

### 6g. All Streaks Summary

```bash
curl -s "$BASE/streaks/summary" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

---

### 6h. AI-Suggested Habits

```bash
curl -s "$BASE/habits/suggested" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

---

### 6i. Delete (Archive) Habit

```bash
curl -s -X DELETE "$BASE/habits/$HABIT_ID" \
  -H "Authorization: Bearer $TOKEN"
# Expected: 204 No Content
```

---

## 7. AI Coach

### 7a. Chat (Non-streaming preview)

```bash
curl -s -X POST "$BASE/ai/chat" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What should I eat for dinner tonight to hit my protein goal?"
  }'
```

> The response is SSE (`text/event-stream`). Each line looks like:  
> `data: {"chunk": "Based on your..."}`  
> `data: {"done": true, "session_id": "uuid"}`

---

### 7b. Chat with Session ID (continue conversation)

```bash
SESSION_ID="paste_session_id_from_previous_response"

curl -s -X POST "$BASE/ai/chat" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"session_id\": \"$SESSION_ID\",
    \"message\": \"Can you give me a recipe for that?\"
  }"
```

---

### 7c. Chat History (all session previews)

```bash
curl -s "$BASE/ai/chat/history" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

---

### 7d. Chat History for a Session

```bash
curl -s "$BASE/ai/chat/history?session_id=$SESSION_ID" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

---

### 7e. Score a Meal

```bash
curl -s -X POST "$BASE/ai/meal-score" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "items": [
      { "name": "Avocado Toast", "quantity_g": 150, "calories": 320 },
      { "name": "Boiled Egg", "quantity_g": 60, "calories": 93 }
    ]
  }' | python3 -m json.tool
```

**Expected:**
```json
{ "score": 84, "grade": "B+", "feedback": "...", "suggestions": ["..."] }
```

---

### 7f. Food Swap

```bash
curl -s -X POST "$BASE/ai/food-swap" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{ "food_name": "White rice", "reason": "lower_carbs" }' | python3 -m json.tool
```

---

### 7g. Daily Tip

```bash
curl -s "$BASE/ai/daily-tip" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

---

### 7h. Analyze Today

```bash
curl -s -X POST "$BASE/ai/analyze-day" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{}' | python3 -m json.tool
```

---

## 8. Meal Plans

### 8a. Generate a 7-Day Plan

> ⏱️ This takes 5–20 seconds (AI generation). Be patient.

```bash
NEXT_MON=$(date -d 'next monday' +%Y-%m-%d 2>/dev/null || date -v+Mon +%Y-%m-%d)

curl -s -X POST "$BASE/meal-plans/generate" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"start_date\": \"$NEXT_MON\",
    \"preferences\": {
      \"exclude_ingredients\": [\"mushrooms\"],
      \"cuisine_preference\": [\"Mediterranean\"],
      \"max_prep_minutes\": 30
    }
  }" | python3 -m json.tool
```

```bash
PLAN_ID="paste_meal_plan_id_here"
```

---

### 8b. Get Active Plan

```bash
curl -s "$BASE/meal-plans/active" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

---

### 8c. Get Plan by ID

```bash
curl -s "$BASE/meal-plans/$PLAN_ID" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

---

### 8d. Shopping List

```bash
curl -s "$BASE/meal-plans/$PLAN_ID/shopping" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

---

### 8e. Activate a Plan

```bash
curl -s -X POST "$BASE/meal-plans/$PLAN_ID/activate" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

---

### 8f. Delete a Plan (expect 204)

```bash
curl -s -X DELETE "$BASE/meal-plans/$PLAN_ID" \
  -H "Authorization: Bearer $TOKEN"
```

---

## 9. Insights

### 9a. Get All Insights

```bash
curl -s "$BASE/insights" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

---

### 9b. Get Unread Only

```bash
curl -s "$BASE/insights?unread_only=true" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

---

### 9c. Mark Insight as Read

```bash
INSIGHT_ID="paste_insight_id_here"

curl -s -X POST "$BASE/insights/$INSIGHT_ID/read" \
  -H "Authorization: Bearer $TOKEN"
# Expected: 204 No Content
```

---

## 10. Analytics

### 10a. Weekly Report

```bash
curl -s "$BASE/analytics/weekly" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

# With explicit week start
curl -s "$BASE/analytics/weekly?week_start=$(date +%Y-%m-%d)" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

---

### 10b. 30-Day Macro Trends

```bash
curl -s "$BASE/analytics/trends?days=30" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

---

### 10c. Eating Patterns

```bash
curl -s "$BASE/analytics/patterns" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

---

### 10d. Goal Progress

```bash
curl -s "$BASE/analytics/goal-progress" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

---

### 10e. Nutrient Gaps

```bash
curl -s "$BASE/analytics/nutrient-gaps" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

---

## 11. Edge Cases & Validation

### Missing required field (expect 422)

```bash
curl -s -X POST "$BASE/meals/log" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{ "meal_type": "breakfast" }'
# Missing meal_date and items
```

---

### Hunger level out of range (expect 422)

```bash
curl -s -X POST "$BASE/meals/log" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"meal_date\": \"$(date +%Y-%m-%d)\",
    \"meal_type\": \"lunch\",
    \"items\": [{ \"custom_food_name\": \"Salad\", \"quantity_g\": 200, \"calories\": 80 }],
    \"hunger_level_before\": 15
  }"
```

---

### Route not found (expect 404)

```bash
curl -s "$BASE/nonexistent-route" -H "Authorization: Bearer $TOKEN"
```

---

## 12. Swagger UI

The fastest way to test all endpoints interactively:

```
http://localhost:8000/docs
```

1. Click **Authorize** → paste your `Bearer <token>`
2. All endpoints are explorable with live request/response

ReDoc (read-only documentation):
```
http://localhost:8000/redoc
```
