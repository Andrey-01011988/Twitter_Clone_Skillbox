import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_all_users_returns_empty_list_when_no_users_exist(client_app: AsyncClient):
    # Убедимся, что база данных пустая перед выполнением этого теста
    response = await client_app.get("/api/all_users")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_get_all_users_returns_users_list_when_users_exist(client_app: AsyncClient, add_test_data):
    response = await client_app.get("/api/all_users")
    assert response.status_code == 200
    users = response.json()
    user_names= [user["name"] for user in users]
    assert "Test" in user_names

# pytest -v tests/test_app_asyncpg.py