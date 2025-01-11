import logging
import random
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from application.models import BaseProj, Users
from application.api.dependencies import get_current_session
from application.main import app_proj
from tests.factories import UserFactory, TweetFactory, LikeFactory, MediaFactory, FollowerFactory

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Фикстуры с использованием фабрик
@pytest_asyncio.fixture()
async def test_db_session() -> AsyncGenerator[AsyncSession, None]:
    logger.info("Старт фикстуры")
    # Строка подключения к тестовой базе данных
    test_database_url = "postgresql+asyncpg://test:test@localhost:5433/test_twitter"
    test_engine_local = create_async_engine(test_database_url)
    logger.info("Создание движка")
    test_async_session = async_sessionmaker(test_engine_local, expire_on_commit=False)
    logger.info("Создание фабрики сессий")
    async with test_engine_local.begin() as conn:
        await conn.run_sync(BaseProj.metadata.drop_all)
        await conn.run_sync(BaseProj.metadata.create_all)
        logger.info("Удаление старых и создание новых таблиц")
    async with test_async_session() as session:
        logger.info(f"Создание тестовой сессии session: {session}")
        users = []
        UserFactory._meta.sqlalchemy_session = session
        for i in range(3):
            if i == 0:
                user = UserFactory(api_key='test')
            else:
                user = UserFactory()
            users.append(user)
        logger.info(f"Create test users {users}")
        session.add_all(users)
        await session.commit()
        logger.info(f"Test users added {users}")

        tweets = []
        likes = []
        media = []
        followers = []

        # Создание подписок
        FollowerFactory._meta.sqlalchemy_session = session
        for follower in users:
            followed = random.choice([user for user in users if user != follower])
            follower_record = FollowerFactory(
                follower_id=follower.id,
                followed_id=followed.id
            )
            followers.append(follower_record)
        logger.info("Followers added")
        session.add_all(followers)

        # Создание твитов
        TweetFactory._meta.sqlalchemy_session = session
        for user in users:
            for _ in range(2):
                tweet = TweetFactory(author_id=user.id)
                tweets.append(tweet)
        logger.info(f"Tweets created: {[tweet.text for tweet in tweets]}")
        session.add_all(tweets)
        await session.commit()
        logger.info(f"Tweets added: {[tweet.id for tweet in tweets]}")

        # Создание лайков
        LikeFactory._meta.sqlalchemy_session = session
        for tweet in tweets:
            if random.choice([True, False]):
                like = LikeFactory(
                    tweet_id=tweet.id,
                    user_id=random.choice(users).id
                )
                likes.append(like)
        logger.info(f"Likes created: {[like for like in likes]}")
        session.add_all(likes)

        # Создание медиа
        MediaFactory._meta.sqlalchemy_session = session
        for tweet in tweets:
            if random.choice([True, False]):
                media_item = MediaFactory(tweet_id=tweet.id)
                media.append(media_item)
        logger.info(f"Media created: {[med.file_name for med in media]}")
        session.add_all(media)

        await session.commit()
        logger.info("Likes & media added")

        yield session
        logger.info(f"Preparation for closing the session {session}")
        await session.close()
        logger.info("Session closed")
    async with test_engine_local.begin() as conn:
        await conn.run_sync(BaseProj.metadata.drop_all)
        logger.info("Tables dropped")


@pytest.fixture()
def test_app(test_db_session: AsyncSession) -> FastAPI:
    app_proj.dependency_overrides[get_current_session] = lambda: test_db_session
    logger.info("Override dependency")
    return app_proj


@pytest_asyncio.fixture()
async def client(test_app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(
            transport=ASGITransport(app=test_app),
            base_url="http://localhost:5000"
    ) as client:
        logger.info("Create test client")
        yield client