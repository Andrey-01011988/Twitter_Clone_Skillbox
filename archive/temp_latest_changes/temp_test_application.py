import logging

import pytest
import random
from fastapi.testclient import TestClient

from application.api.dependencies import get_current_session
from application.main import app_proj
from application.models import BaseProj
from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from tests.test_database import test_engine, AsyncSessionTest
from tests.factories import UserFactory, TweetFactory, LikeFactory, MediaFactory, FollowerFactory  # Импортируйте фабрики

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
    print("Запуск фикстуры")
    async with test_engine.begin() as conn:
        print("Начало")
        try:
            await conn.run_sync(BaseProj.metadata.create_all)
        except Exception as e:
            logger.error(f"Ошибка при создании таблиц: {e}")
            raise
        print("Тестовая б/д создана")

    # Создаем сессию вне контекстного менеджера
    test_session = AsyncSessionTest()
    async with test_session:
        try:
            logger.info("Создание новой тестовой сессии")
            users = []
            UserFactory._meta.sqlalchemy_session = test_session
            print(f"Текущая сессия: {test_session}")

            # Логирование информации о подключении
            connection_info = test_session.bind.url
            logger.info(f"Подключение к базе данных: {connection_info}")

            # Создание пользователей
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
            #         tweet = TweetFactory(author_id=user.id)
            #         tweets.append(tweet)
            #
            # # Создание лайков
            # for tweet in tweets:
            #     if random.choice([True, False]):
            #         like = LikeFactory(
            #             tweet_id=tweet.id,
            #             user_id=random.choice(users).id
            #         )
            #         likes.append(like)
            #
            # # Создание медиа
            # for tweet in tweets:
            #     if random.choice([True, False]):
            #         media_item = MediaFactory(tweet_id=tweet.id)
            #         media.append(media_item)
            #
            # # Создание подписок
            # for follower in users:
            #     followed = random.choice([user for user in users if user != follower])
            #     follower_record = FollowerFactory(
            #         follower_id=follower.id,
            #         followed_id=followed.id
            #     )
            #     followers.append(follower_record)
            #
            # test_session.add_all(tweets)
            # test_session.add_all(likes)
            # test_session.add_all(media)
            # test_session.add_all(followers)
            #
            # # Единый commit для всех изменений
            # await test_session.commit()
            logger.info("Все данные успешно добавлены в базу данных")

            yield test_session  # Передаем сессию в тесты

        except Exception as e:
            logger.error(f"Ошибка при работе с базой данных: {e}")
            await test_session.rollback()
            raise

        finally:
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
    async with AsyncClient(app=app_proj) as ac:
        response = await ac.get("/api/all_users")
    print(response.json())
    assert response.status_code == 200
    assert len(response.json()) > 0 # тут тест должен доказать что setup_database сработала и что то добавила


# pytest -v tests/test_application.py
# pytest -s tests/test_application.py
