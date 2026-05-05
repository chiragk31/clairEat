"""Tests — Meal logging endpoints."""

import pytest
from datetime import date
from unittest.mock import AsyncMock, MagicMock


MEAL_LOG_ROW = {
    "id": "meal-log-uuid-1",
    "user_id": "00000000-0000-0000-0000-000000000001",
    "meal_date": str(date.today()),
    "meal_type": "breakfast",
    "total_calories": 430.0,
    "total_protein_g": 18.0,
    "total_carbs_g": 55.0,
    "total_fat_g": 14.0,
    "total_fiber_g": 5.0,
    "mood_before": "happy",
    "mood_after": None,
    "hunger_level_before": 7,
    "fullness_level_after": None,
    "notes": "Ate slowly",
    "ai_meal_score": None,
    "ai_feedback": None,
    "image_url": None,
    "logged_at": "2026-04-15T12:00:00",
    "meal_log_items": [],
}

FOOD_ROW = {
    "calories_per_100g": 160.0,
    "protein_per_100g": 2.0,
    "carbs_per_100g": 9.0,
    "fat_per_100g": 15.0,
    "fiber_per_100g": 3.0,
}

PROFILE_ROW = {
    "id": "00000000-0000-0000-0000-000000000001",
    "daily_calorie_target": 2200,
    "daily_protein_target_g": 120.0,
    "daily_carb_target_g": 260.0,
    "daily_fat_target_g": 65.0,
    "weight_kg": 75.0,
}


def make_execute(data):
    """Helper — build an AsyncMock execute that returns given data."""
    return AsyncMock(return_value=MagicMock(data=data))


@pytest.mark.asyncio
async def test_log_meal_returns_201(client, mock_db):
    # food lookup returns FOOD_ROW
    mock_db.table.return_value.select.return_value.eq.return_value.single.return_value.execute = \
        make_execute(FOOD_ROW)
    # meal_logs insert
    mock_db.table.return_value.insert.return_value.execute = \
        make_execute([MEAL_LOG_ROW])

    response = await client.post("/v1/meals/log", json={
        "meal_date": str(date.today()),
        "meal_type": "breakfast",
        "items": [
            {"food_item_id": "food-uuid-1", "quantity_g": 200},
        ],
        "mood_before": "happy",
        "hunger_level_before": 7,
        "notes": "Ate slowly",
    })

    assert response.status_code == 201
    data = response.json()
    assert "meal_log_id" in data
    assert "total_calories" in data


@pytest.mark.asyncio
async def test_log_meal_invalid_type(client, mock_db):
    response = await client.post("/v1/meals/log", json={
        "meal_date": str(date.today()),
        "meal_type": "midnight_snack",   # invalid
        "items": [{"food_item_id": "uuid", "quantity_g": 100}],
    })
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_today_meals(client, mock_db):
    mock_db.table.return_value.select.return_value.eq.return_value \
        .eq.return_value.order.return_value.execute = make_execute([MEAL_LOG_ROW])

    response = await client.get("/v1/meals/today")
    assert response.status_code == 200
    data = response.json()
    assert "date" in data
    assert "meals" in data


@pytest.mark.asyncio
async def test_daily_summary_structure(client, mock_db):
    # meal_logs
    mock_db.table.return_value.select.return_value.eq.return_value \
        .eq.return_value.execute = make_execute([{
            "total_calories": 1240.0, "total_protein_g": 62.0,
            "total_carbs_g": 145.0, "total_fat_g": 38.0, "total_fiber_g": 12.0
        }])

    response = await client.get("/v1/meals/daily-summary")
    assert response.status_code == 200
    data = response.json()
    assert "totals" in data
    assert "targets" in data
    assert "pct_complete" in data
    assert "water_ml" in data


@pytest.mark.asyncio
async def test_delete_meal_not_found(client, mock_db):
    mock_db.table.return_value.delete.return_value.eq.return_value \
        .eq.return_value.execute = make_execute([])  # empty = not found

    response = await client.delete("/v1/meals/nonexistent-id")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_meal_history_default_7_days(client, mock_db):
    mock_db.table.return_value.select.return_value.eq.return_value \
        .gte.return_value.order.return_value.execute = make_execute([
            {"meal_date": str(date.today()), "total_calories": 1800,
             "total_protein_g": 90, "total_carbs_g": 210, "total_fat_g": 55}
        ])

    response = await client.get("/v1/meals/history?days=7")
    assert response.status_code == 200
    data = response.json()
    assert "days" in data
    assert "total_days" in data
