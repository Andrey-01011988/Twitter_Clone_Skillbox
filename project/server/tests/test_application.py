import logging

import pytest
import random
from fastapi.testclient import TestClient

from application.api.dependencies import get_current_session
from application.main import app_proj
from application.models import BaseProj
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
        await conn.run_sync(BaseProj.metadata.create_all)
        print("Тестовая б/д создана")

        async with AsyncSessionTest() as test_session:
            logger.info("Создание новой тестовой сессии")
            # Создание трех пользователей, один из которых будет с api_key = 'test'
            users = []
            logger.info(f"Текущая сессия: {test_session}")
            for i in range(3):
                if i == 0:  # Первый пользователь будет с api_key 'test'
                    user = UserFactory.create_user(session=test_session, api_key='test')
                else:
                    user = UserFactory.create_user(session=test_session)
                users.append(user)
            logger.info(f"Созданные пользователи: {[(user.name, user.api_key) for user in users]}")

            try:
                await test_session.commit()
                logger.info("Пользователи успешно добавлены в базу данных")
            except Exception as e:
                logger.error(f"Ошибка при коммите: {e}")
                await test_session.rollback()

            tweets = []
            likes = []
            media = []
            followers = []

            # Создание двух твитов для каждого пользователя
            for user in users:
                for _ in range(2):
                    tweet = TweetFactory.create_tweet(session=test_session, author_id=user.id)
                    tweets.append(tweet)

            # Случайное количество лайков для каждого твита
            for tweet in tweets:
                if random.choice([True, False]):  # Случайно решаем ставить лайк или нет
                    like = LikeFactory.create_like(session=test_session, tweet_id=tweet.id, user_id=random.choice(users).id)
                    likes.append(like)

            # Прикрепление медиа к случайным твитам
            for tweet in tweets:
                if random.choice([True, False]):
                    media_item = MediaFactory.create_media(session=test_session, tweet_id=tweet.id)
                    media.append(media_item)

            try:
                await test_session.commit()  # Сохраняем все изменения в базе данных
                logger.info("Твиты, лайки и медиа успешно добавлены в базу данных")
            except Exception as e:
                logger.error(f"Ошибка при коммите: {e}")
                await test_session.rollback()

            # Случайные подписки между пользователями
            for follower in users:
                followed = random.choice([user for user in users if user != follower])  # Исключаем самого себя
                follower_record = FollowerFactory.create_follower(session=test_session, follower_id=follower.id, followed_id=followed.id)
                followers.append(follower_record)

            try:
                await test_session.commit()  # Сохраняем все изменения в базе данных
                logger.info("Подписки успешно добавлены в базу данных")
            except Exception as e:
                logger.error(f"Ошибка при коммите: {e}")
                await test_session.rollback()

    yield  # Здесь будут выполняться тесты


@pytest.mark.asyncio
async def test_all_users(setup_database):
    """ Проверка всех GET маршрутов """
    client = TestClient(app_proj)
    response = client.get("/api/all_users")
    print(response.json())
    assert response.status_code == 200  # Проверяем, что статус код ответа равен 200


@pytest.mark.asyncio
async def test_all_users_session(setup_database):
    async with AsyncSessionTest() as session:
        # Здесь вы можете выполнять запросы к базе данных
        result = await session.execute(text("SELECT * FROM users"))
        users = result.scalars().all()
        print(users)
        assert len(users) > 0  # Пример проверки на наличие пользователей
