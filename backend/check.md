# Integration Status Check: Frontend ↔ Backend

## 1. ✅ Integration Status

The ClairEat system is **fully integration-ready**. 
The backend architecture precisely mirrors the specific models, parameters, and endpoints required by the frontend documentation. Authentication schemas, API designs, data shapes, and SSE streaming mechanisms map flawlessly. There are no missing core APIs required by the frontend integration guide.

---

## 2. 🔗 Endpoint Mapping Table

| Frontend Requirement / Context | Expected API Call | Backend Endpoint | Status |
|--------------------------------|-------------------|------------------|--------|
| **Auth** | `supabase.auth.*` | Validates JWT emitted by Supabase | ✅ Matched |
| **Onboarding** | `POST /profile/onboarding` | `POST /v1/profile/onboarding` | ✅ Matched |
| **Dashboard - Meals** | `GET /meals/today` | `GET /v1/meals/today` | ✅ Matched |
| **Dashboard - Summary** | `GET /meals/daily-summary` | `GET /v1/meals/daily-summary` | ✅ Matched |
| **Dashboard - Water** | `GET /water/today` | `GET /v1/water/today` | ✅ Matched |
| **Dashboard - Streaks** | `GET /streaks/summary` | `GET /v1/streaks/summary` | ✅ Matched |
| **Dashboard - Insights** | `GET /insights?unread_only=true` | `GET /v1/insights?unread_only=true`| ✅ Matched |
| **Log Meal - Search** | `GET /food/search?q=...` | `GET /v1/food/search?q=...` | ✅ Matched |
| **Log Meal - Barcode** | `GET /food/barcode/...` | `GET /v1/food/barcode/{barcode}` | ✅ Matched |
| **Log Meal - NLP** | `GET /food/nlp?q=...` | `GET /v1/food/nlp?q=...` | ✅ Matched |
| **Log Meal - Submit** | `POST /meals/log` | `POST /v1/meals/log` | ✅ Matched |
| **Log Meal - Photo** | `POST /meals/{id}/photo` | `POST /v1/meals/{meal_id}/photo` | ✅ Matched |
| **Meal Plan - Generate**| `POST /meal-plans/generate` | `POST /v1/meal-plans/generate`| ✅ Matched |
| **Meal Plan - Active** | `GET /meal-plans/active` | `GET /v1/meal-plans/active` | ✅ Matched |
| **Meal Plan - Shopping** | `GET /meal-plans/{id}/shopping`| `GET /v1/meal-plans/{plan_id}/shopping`|✅ Matched |
| **AI Coach - Chat** | `POST /ai/chat` (SSE stream) | `POST /v1/ai/chat` (EventSource) | ✅ Matched |
| **AI Coach - Score** | `POST /ai/meal-score` | `POST /v1/ai/meal-score` | ✅ Matched |
| **AI Coach - Swap** | `POST /ai/food-swap` | `POST /v1/ai/food-swap` | ✅ Matched |
| **AI Coach - Tip** | `GET /ai/daily-tip` | `GET /v1/ai/daily-tip` | ✅ Matched |
| **AI Coach - Analyze** | `POST /ai/analyze-day` | `POST /v1/ai/analyze-day` | ✅ Matched |
| **Analytics - Weekly** | `GET /analytics/weekly` | `GET /v1/analytics/weekly` | ✅ Matched |
| **Analytics - Trends** | `GET /analytics/trends` | `GET /v1/analytics/trends` | ✅ Matched |
| **Analytics - Patterns**| `GET /analytics/patterns` | `GET /v1/analytics/patterns` | ✅ Matched |
| **Analytics - Progress**| `GET /analytics/goal-progress`| `GET /v1/analytics/goal-progress`| ✅ Matched |
| **Analytics - Gaps** | `GET /analytics/nutrient-gaps`| `GET /v1/analytics/nutrient-gaps`| ✅ Matched |
| **Habits - Create** | `POST /habits` | `POST /v1/habits` | ✅ Matched |
| **Habits - Log** | `POST /habits/{id}/log` | `POST /v1/habits/{habit_id}/log` | ✅ Matched |
| **Habits - Suggestions**| `GET /habits/suggested` | `GET /v1/habits/suggested` | ✅ Matched |
| **Water - Log** | `POST /water/log` | `POST /v1/water/log` | ✅ Matched |

---

## 3. ❌ Gaps & Issues

While the integration maps out perfectly, here are minor friction points that could occur in production:

1. **API Prefix Versioning**: 
    - The frontend integration guide implies relative paths (e.g., `api.post('/meals/log')`). In `lib/api.ts` from `FRONTEND_INTEGRATION.md`, the base URL (`NEXT_PUBLIC_API_BASE_URL`) needs to explicitly include `/v1` (e.g. `http://localhost:8000/v1`) as configured. Currently, the documentation correctly points this out, but it's a common integration risk.
2. **AI Streaming Fallbacks**:
    - `EventSource` and fetch `getReader()` handle network interruptions differently. The frontend expects a specific SSE payload structure `data: {"chunk": ...}` which matches the backend entirely, but the frontend needs proper retry logic if the stream drops mid-generation.
3. **Photo Upload Header Mapping**:
    - Fetching `FormData` objects using the typed API wrapper can sometimes overwrite boundary headers if not handled carefully. `FRONTEND_INTEGRATION.md` demonstrates this perfectly bypassing the abstraction wrapper (`apiFetch`), fetching natively for photo uploads.

---

## 4. ⚠️ Required Additions / Fixes

### What needs to be added/adjusted in the backend
- **Nothing immediately required.** The specs describe a fully sealed, functional application layer.
- *Future consideration*: Consider a `/v1/profile/delete` or full data-wipe endpoint to comply with account deletion requests cleanly.
- *Future consideration*: Presigned Supabase Storage URLs. The photo endpoint currently proxy-uploads via the backend. Emitting presigned URLs and uploading directly from frontend to Supabase would offload bytes from the FastAPI worker.

### What needs to be adjusted in the frontend (Suggestions)
- **Error Retries**: Ensure `RATE_LIMIT_EXCEEDED` statuses invoke an automatic backoff so users aren't fully blocked unnecessarily.
- **Handling Empty States**: Some lists from endpoints like `/history`, `/insights`, or `/streaks/summary` will return empty arrays `[]` on fresh accounts. The UI must aggressively map empty states. 
- **Offline / Optimistic Updates**: The integration is highly dependent on sequential API hits for habits and water. Implementing React Query (`@tanstack/react-query`) with cache invalidation would drastically boost responsiveness versus hard `await Promise.all` data fetches on page mount.

---

## 5. 💡 Recommendations

- **API Type Synchronization**: Since both stacks rely on rigid schemas (Pydantic models in Python, Typescript interfaces in Next.js), you should consider a script to auto-generate TypeScript definitions from the `openapi.json` generated by FastAPI at `http://localhost:8000/openapi.json`. Tools like `openapi-typescript-codegen` remove the manual maintenance burden.
- **Use React Query / SWR**: As shown in the dashboard example, doing large `Promise.all` batches in standard hooks might become a waterfall bottleneck. State management layers specifically built for concurrent caching will perform much better with these isolated endpoints.
- **WebSockets over SSE**: If functionality expands to background generation notices (e.g. the scorer finishing and updating a row), native WebSockets or a Supabase realtime trigger are more effective than SSE. However, SSE completely suffices for chat.
