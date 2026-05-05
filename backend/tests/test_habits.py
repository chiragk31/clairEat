"""Tests — Habit creation, logging, and streak engine."""

import pytest
from datetime import date, timedelta
from unittest.mock import AsyncMock, MagicMock


HABIT_ROW = {
    "id": "habit-uuid-1",
    "user_id": "00000000-0000-0000-0000-000000000001",
    "habit_name": "Drink 8 glasses of water",
    "habit_type": "water_intake",
    "target_value": 8.0,
    "target_unit": "glasses",
    "frequency": "daily",
    "reminder_times": ["08:00", "13:00"],
    "is_active": True,
    "created_at": "2026-04-01T00:00:00",
}

STREAK_ROW = {
    "id": "streak-uuid-1",
    "user_id": "00000000-0000-0000-0000-000000000001",
    "habit_id": "habit-uuid-1",
    "streak_type": "habit_specific",
    "current_streak": 12,
    "longest_streak": 30,
    "last_activity_date": str(date.today() - timedelta(days=1)),
    "updated_at": "2026-04-14T00:00:00",
}


def make_execute(data):
    return AsyncMock(return_value=MagicMock(data=data))


@pytest.mark.asyncio
async def test_create_habit_success(client, mock_db):
    mock_db.table.return_value.insert.return_value.execute = make_execute([HABIT_ROW])

    response = await client.post("/v1/habits", json={
        "habit_name": "Drink 8 glasses of water",
        "habit_type": "water_intake",
        "target_value": 8,
        "target_unit": "glasses",
        "frequency": "daily",
        "reminder_times": ["08:00", "13:00"],
    })

    assert response.status_code == 201
    data = response.json()
    assert data["habit_name"] == "Drink 8 glasses of water"
    assert data["target_value"] == 8.0


@pytest.mark.asyncio
async def test_list_habits(client, mock_db):
    mock_db.table.return_value.select.return_value.eq.return_value \
        .eq.return_value.order.return_value.execute = make_execute([HABIT_ROW])

    response = await client.get("/v1/habits")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_log_habit_completes_streak(client, mock_db):
    # get_habit
    mock_db.table.return_value.select.return_value.eq.return_value \
        .eq.return_value.single.return_value.execute = make_execute(HABIT_ROW)
    # upsert habit log
    mock_db.table.return_value.upsert.return_value.execute = make_execute([{"id": "log-1"}])
    # get streak (yesterday)
    mock_db.table.return_value.select.return_value.eq.return_value \
        .eq.return_value.single.return_value.execute = make_execute(STREAK_ROW)
    # update streak
    mock_db.table.return_value.update.return_value.eq.return_value \
        .eq.return_value.execute = make_execute([{**STREAK_ROW, "current_streak": 13}])

    response = await client.post("/v1/habits/habit-uuid-1/log", json={"value_achieved": 8})
    assert response.status_code == 200
    data = response.json()
    assert data["is_completed"] is True
    assert "streak" in data


@pytest.mark.asyncio
async def test_log_habit_not_completed(client, mock_db):
    """Value below target should mark is_completed=False."""
    mock_db.table.return_value.select.return_value.eq.return_value \
        .eq.return_value.single.return_value.execute = make_execute(HABIT_ROW)
    mock_db.table.return_value.upsert.return_value.execute = make_execute([{"id": "log-1"}])
    mock_db.table.return_value.select.return_value.eq.return_value \
        .eq.return_value.single.return_value.execute = make_execute(STREAK_ROW)

    response = await client.post("/v1/habits/habit-uuid-1/log", json={"value_achieved": 4})
    assert response.status_code == 200
    assert response.json()["is_completed"] is False


@pytest.mark.asyncio
async def test_delete_habit_soft_deletes(client, mock_db):
    mock_db.table.return_value.update.return_value.eq.return_value \
        .eq.return_value.execute = make_execute([{**HABIT_ROW, "is_active": False}])

    response = await client.delete("/v1/habits/habit-uuid-1")
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_streaks_summary(client, mock_db):
    global_streak = {"current_streak": 12, "longest_streak": 30, "last_activity_date": str(date.today())}
    mock_db.table.return_value.select.return_value.eq.return_value \
        .eq.return_value.is_.return_value.limit.return_value.execute = make_execute([global_streak])
    mock_db.table.return_value.select.return_value.eq.return_value \
        .eq.return_value.order.return_value.execute = make_execute([])

    response = await client.get("/v1/streaks/summary")
    assert response.status_code == 200
    data = response.json()
    assert "global_logging_streak" in data
    assert "habits" in data
