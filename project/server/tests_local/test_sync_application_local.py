import asyncio
import logging

import pytest
from httpx import AsyncClient, ASGITransport
# from sqlalchemy.ext.asyncio import AsyncSession
# from fastapi.testclient import TestClient

from application.api.dependencies import get_current_session
from application.main import app_proj
from application.models import BaseProj, Users
from sqlalchemy.ext.asyncio import AsyncConnection
from tests_local.test_database_local import test_engine, AsyncSessionTest, test_session
# from tests.factories import UserFactory, TweetFactory, LikeFactory, MediaFactory, FollowerFactory  # Импортируйте фабрики


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

# Переопределение сессии приложения для тестирования
async def override_get_session():
    logger.info("Создание тестовой сессии Dependencies")
    try:
        yield test_session
    finally:
        await test_session.close()
        logger.info("Закрытие тестовой сессии Dependencies")

app_proj.dependency_overrides[get_current_session] = override_get_session


@pytest.fixture(scope="function")
async def setup_database(event_loop):
    print("Запуск фикстуры")
    async with test_engine.begin() as conn:
        print("Начало")
        await conn.run_sync(BaseProj.metadata.drop_all)
        await conn.run_sync(BaseProj.metadata.create_all)
        print("Тестовая б/д создана")

    yield

    async with test_engine.begin() as conn:
        await conn.run_sync(BaseProj.metadata.drop_all)


@pytest.fixture(scope="function")
async def add_data(event_loop):
    async with test_session:
        print("Создание новой тестовой сессии")
        users = []
        print(f"Текущая сессия: {test_session}")
        # Логирование информации о подключении
        connection_info = test_session.bind.url
        print(f"Подключение к базе данных: {connection_info}")
        # UserFactory._meta.sqlalchemy_session = test_session
        names = ['Марина', 'Витя']
        api_keys = ['hvc', 'hfbfbv9']
        for i in range(3):
            if i == 0:
                # user = UserFactory(api_key='test')
                user = Users(name='Test', api_key='test')
            else:
                user = Users(name=names[i - 1], api_key=api_keys[i - 1])
            users.append(user)
        test_session.add_all(users)
        await test_session.commit()
        logger.info(f"Добавлено пользователей: {len(users)}")

    yield


@pytest.mark.asyncio
async def test_all_users(setup_database, add_data):
    # loop = asyncio.get_running_loop()  # Получение текущего цикла событий
    async with AsyncClient(
            transport=ASGITransport(app=app_proj),
            base_url="http://localhost:5000") as ac:
        response = await ac.get("/api/all_users")
    logger.info(response.json())
    assert response.status_code == 200
    assert len(response.json()) > 0

# @pytest.mark.asyncio
# async def test_one_recipe(setup_database):
#     client = TestClient(app_proj)
#     response = client.get("/api/all_users")
#     print(response.json())
#     assert response.status_code == 200


# Запуск из: (ubuntuenv) uservm@uservm-VirtualBox:~/PycharmProjects/python_advanced_diploma/project/server$
# python -m pytest tests_local/test_sync_application_local.py
# (ubuntuenv) uservm@uservm-VirtualBox:~/PycharmProjects/python_advanced_diploma/project/server$
# python -m pytest tests_local/test_sync_application_local.py -v --log-cli-level=INFO