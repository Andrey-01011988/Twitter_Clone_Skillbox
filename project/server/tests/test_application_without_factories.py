import logging

import pytest
import asyncio
# from httpx import AsyncClient, ASGITransport
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from application.api.dependencies import get_current_session
from application.main import app_proj
from application.models import BaseProj, Users
from tests.test_database import test_engine, AsyncSessionTest, test_session

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# # Назначение текущей сессии
# async def override_get_session() -> AsyncSession:
#     logger.info("Создание тестовой сессии Dependencies")
#     async with AsyncSessionTest() as current_session:
#         try:
#             yield current_session
#         finally:
#             await current_session.close()
#             logger.info("Закрытие тестовой сессии Dependencies")

async def override_get_session():
    try:
        yield test_session
        logger.info("Создание новой тестовой сессии")
        logger.info(f"Текущая сессия: {test_session}")
    finally:
        await test_session.close()
        logger.info(f"Закрытие тестовой сессии {test_session}")

app_proj.dependency_overrides[get_current_session] = override_get_session

@pytest.fixture(scope="module")
async def setup_database():
    print("Запуск фикстуры")
    async with test_engine.begin() as conn:
        print("Начало")
        await conn.run_sync(BaseProj.metadata.create_all)
        print("Тестовая б/д создана")

        async with test_session:
            new_user = Users(
                        name="Brian",
                        api_key="tttt"
            )
            print(f"Создан пользователь: {new_user.name}, {new_user.api_key}")
            test_session.add(new_user)
            await test_session.commit()

    yield

        # session = None
        # try:
        #     async  with AsyncSessionTest() as temp_session:
        #         print("Использование тестовой сессии")
        #         print(f"Текущая сессия: {temp_session}")
        #         new_user = Users(
        #             name="Brian",
        #             api_key="tttt"
        #         )
        #         print(f"Создан пользователь: {new_user.name}, {new_user.api_key}")
        #         session = temp_session
        #         await session.add(new_user)
        #         await session.commit()
        #         print("Пользователь успешно добавлен в базу данных")
        # except Exception as e:
        #     print(f"Ошибка при работе с сессией: {e}")
        # finally:
        #     if session:
        #         await session.close()
        #     yield session


# @pytest.mark.asyncio
# async def test_all_users(setup_database):
#     """ Проверка всех GET маршрутов """
#     async with AsyncClient(
#         transport=ASGITransport(app=app_proj), base_url="http://test"
#     ) as client:
#         response = await client.get("/api/all_users")
#         print(response.json())
#         assert response.status_code == 200  # Проверяем, что статус код ответа равен 200

@pytest.mark.asyncio
async def test_all_users(setup_database):
    """ Проверка всех GET маршрутов """
    client = TestClient(app_proj)
    response = client.get("/api/all_users")
    print(response.json())
    assert response.status_code == 200  # Проверяем, что статус код ответа равен 200

# @pytest.mark.asyncio
# async def test_all_users(setup_database):
#     async with AsyncClient(transport=ASGITransport(app=app_proj)) as client:
#         response = await client.get("/api/all_users")
#         assert response.status_code == 200

# pytest -v tests/test_application_without_factories.py
