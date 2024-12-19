import pytest
import random
from fastapi.testclient import TestClient

from application.api.dependencies import get_current_session
from application.main import app_proj
from application.models import BaseProj
from sqlalchemy import text
from tests.test_database import test_session, test_engine, AsyncSessionTest
from tests.factories import UserFactory, TweetFactory, LikeFactory, MediaFactory, FollowerFactory  # Импортируйте фабрики

# async def override_get_session():
#     try:
#         yield test_session
#     finally:
#         await test_session.close()
async def override_get_session():
    async with AsyncSessionTest() as session:  # Создаем новую сессию
        yield session  # Возвращаем новую сессию

app_proj.dependency_overrides[get_current_session] = override_get_session


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

            test_session.add_all(users)  # Добавляем всех пользователей сразу
            await test_session.commit()  # Сохраняем пользователей в базе данных

            tweets = []
            likes = []
            media = []
            followers = []  # Список для хранения подписок

            # Создание двух твитов для каждого пользователя
            for user in users:
                for _ in range(2):
                    tweet = TweetFactory(author_id=user.id)
                    tweets.append(tweet)

                # Случайное количество лайков для каждого твита
                for tweet in tweets:
                    if random.choice([True, False]):  # Случайно решаем ставить лайк или нет
                        like = LikeFactory(tweet_id=tweet.id, user_id=random.choice(users).id)  # Лайк от случайного пользователя
                        likes.append(like)

                # Прикрепление медиа к случайным твитам
                if random.choice([True, False]):
                    tweet_with_media = random.choice(tweets)  # Выбор случайного твита для прикрепления медиа
                    media_item = MediaFactory(tweet_id=tweet_with_media.id)
                    media.append(media_item)

            # Добавляем твиты, лайки и медиа в сессию
            test_session.add_all(tweets)
            test_session.add_all(likes)
            test_session.add_all(media)

            await test_session.commit()  # Сохраняем все изменения в базе данных

            # Случайные подписки между пользователями
            for follower in users:
                followed = random.choice([user for user in users if user != follower])  # Исключаем самого себя
                follower_record = FollowerFactory(follower_id=follower.id, followed_id=followed.id)
                followers.append(follower_record)

            # Добавляем записи о подписках в сессию
            test_session.add_all(followers)

            await test_session.commit()  # Сохраняем все изменения в базе данных

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
