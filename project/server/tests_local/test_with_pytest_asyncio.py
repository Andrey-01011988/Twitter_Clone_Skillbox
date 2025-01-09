import logging
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport, Response
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from application.models import BaseProj, Users
from application.api.dependencies import get_current_session
from application.main import app_proj


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@pytest_asyncio.fixture()
async def test_db_session() -> AsyncGenerator[AsyncSession, None]:
    # Строка подключения к тестовой базе данных
    test_database_url = "postgresql+asyncpg://test:test@localhost:5433/test_twitter"
    test_engine_local = create_async_engine(test_database_url, echo=True)
    test_async_session = async_sessionmaker(test_engine_local, expire_on_commit=False)
    async with test_engine_local.begin() as conn:
        await conn.run_sync(BaseProj.metadata.drop_all)
        await conn.run_sync(BaseProj.metadata.create_all)
    async with test_async_session() as session:
        users = []
        names = ['Марина', 'Витя']
        api_keys = ['hvc', 'hfbfbv9']
        for i in range(3):
            if i == 0:
                # user = UserFactory(api_key='test')
                user = Users(name='Test', api_key='test')
            else:
                user = Users(name=names[i - 1], api_key=api_keys[i - 1])
            users.append(user)
        session.add_all(users)
        yield session
        await session.close()


@pytest.fixture()
def test_app(test_db_session: AsyncSession) -> FastAPI:
    app_proj.dependency_overrides[get_current_session] = lambda: test_db_session
    return app_proj


@pytest_asyncio.fixture()
async def client(test_app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(
            transport=ASGITransport(app=test_app),
            base_url="http://localhost:5000"
    ) as client:
        yield client

# Работает
@pytest.mark.asyncio()
async def test_get_users_information(client: AsyncClient):
    response: Response = await client.get("/api/all_users")
    logger.info(type(response))
    logger.info(response.json())
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) > 0

# Не работает
@pytest.mark.asyncio()
async def test_get_user_me(client: AsyncClient):
    headers = {"Api-Key": "test"}
    response: Response = await client.get("/api/users/me", headers=headers)
    logger.info(type(response))
    logger.info(response.json())
    assert response.status_code == 200
    assert isinstance(response.json(), dict)
    assert "user" in response.json()


# (ubuntuenv) uservm@uservm-VirtualBox:~/PycharmProjects/python_advanced_diploma/project/server$
# python -m pytest tests_local/test_with_pytest_asyncio.py -v --log-cli-level=INFO