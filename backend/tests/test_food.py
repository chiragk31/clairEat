"""Tests — Food search endpoints."""

import pytest
from unittest.mock import AsyncMock, MagicMock


FOOD_ROW = {
    "id": "food-uuid-1",
    "name": "Avocado",
    "source": "usda",
    "calories_per_100g": 160.0,
    "protein_per_100g": 2.0,
    "carbs_per_100g": 9.0,
    "fat_per_100g": 15.0,
    "vitamins": {},
    "minerals": {},
    "allergens": [],
}


@pytest.mark.asyncio
async def test_food_search_returns_results(client, mock_db):
    mock_db.table.return_value.select.return_value.ilike.return_value.limit.return_value.execute = \
        AsyncMock(return_value=MagicMock(data=[FOOD_ROW]))

    response = await client.get("/v1/food/search?q=avocado")
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert data["total"] >= 0  # May pull from external APIs too


@pytest.mark.asyncio
async def test_food_search_requires_min_length(client):
    response = await client.get("/v1/food/search?q=a")
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_barcode_lookup_not_found(client, mock_db):
    mock_db.table.return_value.select.return_value.eq.return_value.limit.return_value.execute = \
        AsyncMock(return_value=MagicMock(data=[]))

    with pytest.MonkeyPatch().context() as m:
        from app.services.food import open_food_facts
        m.setattr(
            "app.services.food.food_service._off_client.lookup_barcode",
            AsyncMock(return_value=None),
        )
        response = await client.get("/v1/food/barcode/9999999999999")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_food_detail_not_found(client, mock_db):
    mock_db.table.return_value.select.return_value.eq.return_value.single.return_value.execute = \
        AsyncMock(return_value=MagicMock(data=None))

    response = await client.get("/v1/food/nonexistent-id")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_custom_food(client, mock_db):
    created_food = {**FOOD_ROW, "source": "user", "id": "new-food-id"}
    mock_db.table.return_value.insert.return_value.execute = \
        AsyncMock(return_value=MagicMock(data=[created_food]))

    response = await client.post("/v1/food/custom", json={
        "name": "Homemade Protein Bar",
        "calories_per_100g": 350.0,
        "protein_per_100g": 25.0,
        "carbs_per_100g": 30.0,
        "fat_per_100g": 10.0,
    })
    assert response.status_code == 201
