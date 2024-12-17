import pytest
import random
from application.api.dependencies import get_current_session
from application.main import app_proj
from application.models import BaseProj
from tests.test_database import AsyncSessionTest, test_engine
from tests.factories import UserFactory, TweetFactory, LikeFactory, MediaFactory, FollowerFactory  # Импортируйте фабрики

async def override_get_session():
    test_session = AsyncSessionTest()
    try:
        yield test_session
    finally:
        await test_session.close()

app_proj.dependency_overrides[get_current_session] = override_get_session

@pytest.fixture(scope="function")
async def db_session():
    async with AsyncSessionTest() as session:
        yield session

@pytest.fixture(scope="module")
async def setup_database():
    print("Запуск фикстуры")
    async with test_engine.begin() as conn:
        print("Начало")
        await conn.run_sync(BaseProj.metadata.create_all)
        print("Тестовая б/д создана")

        async with AsyncSessionTest() as test_session:
            # Создание трех пользователей, один из которых будет с api_key = 'test'
            users = []
            for i in range(3):
                if i == 0:  # Первый пользователь будет с api_key 'test'
                    user = UserFactory(api_key='test')
                else:
                    user = UserFactory()
                users.append(user)
                test_session.add_all(users)
            await test_session.commit()  # Сохраняем пользователей в базе данных

            # Создание двух твитов для каждого пользователя
            for user in users:
                tweets = [TweetFactory(author_id=user.id) for _ in range(2)]
                test_session.add_all(tweets)
                await test_session.commit()  # Сохраняем твиты в базе данных

                # Случайное количество лайков для каждого твита
                for tweet in tweets:
                    if random.choice([True, False]):  # Случайно решаем ставить лайк или нет
                        LikeFactory(tweet_id=tweet.id, user_id=random.choice(users).id)  # Лайк от случайного пользователя

                # Прикрепление медиа к случайным твитам
                if random.choice([True, False]):
                    tweet_with_media = random.choice(tweets)  # Выбор случайного твита для прикрепления медиа
                    MediaFactory(tweet_id=tweet_with_media.id)

            # Случайные подписки между пользователями
            for follower in users:
                followed = random.choice([user for user in users if user != follower])  # Исключаем самого себя
                FollowerFactory(follower_id=follower.id, followed_id=followed.id)

            await test_session.commit()  # Сохраняем все изменения в базе данных

    yield  # Здесь будут выполняться тесты
