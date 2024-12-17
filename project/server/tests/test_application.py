import pytest
from fastapi.testclient import TestClient

from application.main import app_proj

client = TestClient(app_proj)

@pytest.mark.asyncio
async def test_all_users(setup_database):
    """ Проверка всех GET маршрутов """
    response = client.get("/api/all_users")
    print(response)
    assert response.status_code == 200  # Проверяем, что статус код ответа равен 200
