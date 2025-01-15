import logging

import pytest
import random
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession

from application.api.dependencies import get_current_session
from application.main import app_proj
from application.models import BaseProj

from tests.factories import UserFactory, TweetFactory, LikeFactory, MediaFactory, FollowerFactory  # Импортируйте фабрики

from tests_local.test_database_local import test_engine, AsyncSessionTest

# async def override_get_session():
#     try:
#         yield test_session
#     finally:
#         await test_session.close()
# async def override_get_session():
#     async with AsyncSessionTest() as session:  # Создаем новую сессию
#         yield session  # Возвращаем новую сессию

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Назначение текущей сессии
async def override_get_session() -> AsyncSession:
    logger.info("Создание тестовой сессии Dependencies")
    async with AsyncSessionTest() as current_session:
        try:
            yield current_session
        finally:
            await current_session.close()
            logger.info("Закрытие тестовой сессии Dependencies")

app_proj.dependency_overrides[get_current_session] = override_get_session


@pytest.fixture(scope="module")
async def setup_database():
    logger.info("Запуск фикстуры")
    async with test_engine.begin() as conn:
        logger.info("Начало")
        await conn.run_sync(BaseProj.metadata.drop_all)
        await conn.run_sync(BaseProj.metadata.create_all)
        logger.info("Тестовая б/д создана")

    # Создаем сессию вне контекстного менеджера
    async with AsyncSessionTest() as test_session:
        try:
            logger.info("Создание новой тестовой сессии")
            users = []
            logger.info(f"Текущая сессия: {test_session}")

            # Логирование информации о подключении
            connection_info = test_session.bind.url
            logger.info(f"Подключение к базе данных: {connection_info}")
            # Создание пользователей
            UserFactory._meta.sqlalchemy_session = test_session
            for i in range(3):
                if i == 0:
                    user = UserFactory(api_key='test')
                else:
                    user = UserFactory()
                users.append(user)
            test_session.add_all(users)
            await test_session.commit()

            # tweets = []
            # likes = []
            # media = []
            # followers = []
            #
            # # Создание твитов
            # for user in users:
            #     for _ in range(2):
            #         tweet = TweetFactory.create_tweet(session=test_session, author_id=user.id)
            #         tweets.append(tweet)
            #
            # # Создание лайков
            # for tweet in tweets:
            #     if random.choice([True, False]):
            #         like = LikeFactory.create_like(
            #             session=test_session,
            #             tweet_id=tweet.id,
            #             user_id=random.choice(users).id
            #         )
            #         likes.append(like)
            #
            # # Создание медиа
            # for tweet in tweets:
            #     if random.choice([True, False]):
            #         media_item = MediaFactory.create_media(session=test_session, tweet_id=tweet.id)
            #         media.append(media_item)
            #
            # # Создание подписок
            # for follower in users:
            #     followed = random.choice([user for user in users if user != follower])
            #     follower_record = FollowerFactory.create_follower(
            #         session=test_session,
            #         follower_id=follower.id,
            #         followed_id=followed.id
            #     )
            #     followers.append(follower_record)
            #
            # # Единый commit для всех изменений
            # await test_session.commit()
            logger.info("Все данные успешно добавлены в базу данных")
        except Exception as e:
            logger.error(f"Ошибка при работе с базой данных: {e}")
            await test_session.rollback()
            raise
    yield
    # Очистка после тестов
    async with test_engine.begin() as conn:
        await conn.run_sync(BaseProj.metadata.drop_all)
    await test_session.close()


# @pytest.mark.asyncio
# async def test_all_users(setup_database):
#     """ Проверка всех GET маршрутов """
#     client = TestClient(app_proj)
#     response = client.get("/api/all_users")
#     print(response.json())
#     assert response.status_code == 200  # Проверяем, что статус код ответа равен 200


# @pytest.mark.asyncio
# async def test_all_users_session(setup_database):
#     async with AsyncSessionTest() as session:
#         # Здесь вы можете выполнять запросы к базе данных
#         result = await session.execute(text("SELECT * FROM users"))
#         users = result.scalars().all()
#         print(users)
#         assert len(users) > 0  # Пример проверки на наличие пользователей


@pytest.mark.asyncio
async def test_all_users(setup_database):
    async with AsyncClient(
            transport=ASGITransport(app=app_proj),
            base_url="http://localhost:5000") as ac:
        response = await ac.get("/api/all_users")
    logger.info(response.json())
    assert response.status_code == 200
    assert len(response.json()) > 0 # тут тест должен доказать что setup_database сработала и что то добавила

# Запуск из: (ubuntuenv) uservm@uservm-VirtualBox:~/PycharmProjects/python_advanced_diploma/project/server$
# python -m pytest tests_local/test_application_local.py
