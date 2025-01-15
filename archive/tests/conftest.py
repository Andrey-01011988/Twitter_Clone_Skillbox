import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from application.main import app_proj
from application.models import BaseProj, Users
from application.api.dependencies import get_current_session
from tests.test_database import test_engine, AsyncSessionTest, create_pool, close_pool


@pytest.fixture(scope="function")
async def setup_database():
    # Создаем пул соединений
    pool = await create_pool()
    async with test_engine.begin() as conn:
        await conn.run_sync(BaseProj.metadata.create_all)

    yield pool  # Передаем пул в тесты

    async with test_engine.begin() as conn:
        await conn.run_sync(BaseProj.metadata.drop_all)

    await close_pool(pool)  # Закрываем пул после тестов


# Переопределение зависимости get_current_session
def get_session_override(pool):
    async def session_override():
        connection = await pool.acquire()  # Получаем соединение из пула
        session = AsyncSessionTest(bind=connection)  # Создаем сессию
        try:
            yield session  # Возвращаем сессию для использования
        finally:
            await session.close()  # Закрываем сессию после использования
            await pool.release(connection)  # Возвращаем соединение в пул
    return session_override


@pytest.fixture()
async def client_app(setup_database):
    pool = setup_database  # Получаем пул из фикстуры

    # Переопределяем зависимость
    app_proj.dependency_overrides[get_current_session] = get_session_override(pool)

    async with AsyncClient(transport=ASGITransport(app=app_proj), base_url="http://server:5000") as client:
        yield client

    # Убираем переопределение после завершения тестов
    app_proj.dependency_overrides.pop(get_current_session)


@pytest.fixture()
async def add_test_data():
    async with AsyncSessionTest() as session:
        user1 = Users(name="Test", api_key="test")
        user2 = Users(name="Bob", api_key="boobs")
        session.add(user1)
        session.add(user2)
        await session.commit()

        yield

        # Очистка данных после тестов
        await session.execute(text("DELETE FROM users"))
        await session.commit()