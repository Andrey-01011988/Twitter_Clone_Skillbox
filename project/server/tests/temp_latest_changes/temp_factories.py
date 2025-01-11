import os
import factory
from faker import Faker
from application.models import Users, Tweets, Like, Media, Followers

from tests.test_database import AsyncSessionTest

fake = Faker("ru_RU")


class UserFactory(factory.alchemy.SQLAlchemyModelFactory):
    """Генератор случайных пользователей."""

    class Meta:
        model = Users
        sqlalchemy_session = None

    name = factory.LazyAttribute(lambda _: fake.name())  # Генерация имени пользователя
    api_key = factory.LazyAttribute(lambda _: fake.bothify(text='??###?##'))  # Генерация API-ключа

    # @classmethod
    # def create_user(cls, session=None, **kwargs):
    #     """Создает пользователя и добавляет его в указанную сессию."""
    #     user = cls(**kwargs)  # Создаем объект пользователя
    #     if session:
    #         session.add(user)  # Добавляем пользователя в переданную сессию
    #     return user


class TweetFactory(factory.alchemy.SQLAlchemyModelFactory):
    """Генератор случайных твитов."""

    class Meta:
        model = Tweets

    text = factory.LazyAttribute(lambda _: fake.sentence(nb_words=5, variable_nb_words=True))  # Генерация текста твита
    author_id = factory.SubFactory(UserFactory)  # Привязка твита к случайному пользователю

    # @classmethod
    # def create_tweet(cls, session=None, **kwargs):
    #     """Создает твит и добавляет его в указанную сессию."""
    #     tweet = cls(**kwargs)
    #     if session:
    #         session.add(tweet)
    #     return tweet


class LikeFactory(factory.alchemy.SQLAlchemyModelFactory):
    """Генератор случайных лайков."""

    class Meta:
        model = Like

    tweet_id = factory.SubFactory(TweetFactory)  # Создание твита, который лайкаем
    user_id = factory.SubFactory(UserFactory)  # Создание пользователя, который ставит лайк

    # @classmethod
    # def create_like(cls, session=None, **kwargs):
    #     """Создает лайк и добавляет его в указанную сессию."""
    #     like = cls(**kwargs)
    #     if session:
    #         session.add(like)
    #     return like


class MediaFactory(factory.alchemy.SQLAlchemyModelFactory):
    """Генератор случайных медиафайлов."""

    class Meta:
        model = Media

    @factory.lazy_attribute
    def file_body(self):
        """Загрузка изображения из файла."""
        image_directory = '/server/tests/images'  # Замените на путь к вашей директории с изображениями
        image_files = os.listdir(image_directory)

        # Выбор случайного изображения из директории
        selected_image = fake.random_element(image_files)

        # Полный путь к изображению
        image_path = os.path.join(image_directory, selected_image)

        # Чтение изображения в бинарном формате
        with open(image_path, 'rb') as f:
            return f.read()  # Возвращаем бинарные данные изображения

    file_name = factory.LazyAttribute(lambda obj: os.path.basename(obj.file_body))  # Имя файла медиа
    tweet_id = factory.SubFactory(TweetFactory)  # Привязываем медиа к твиту

    # @classmethod
    # def create_media(cls, session=None, **kwargs):
    #     """Создает медиафайл и добавляет его в указанную сессию."""
    #     media = cls(**kwargs)
    #     if session:
    #         session.add(media)
    #     return media


class FollowerFactory(factory.alchemy.SQLAlchemyModelFactory):
    """Генератор случайных подписок пользователей."""

    class Meta:
        model = Followers

    follower_id = factory.SubFactory(UserFactory)  # Создание пользователя, который подписывается
    followed_id = factory.SubFactory(UserFactory)  # Создание пользователя, на которого подписываются

    # @classmethod
    # def create_follower(cls, session=None, **kwargs):
    #     """Создает подписку и добавляет ее в указанную сессию."""
    #     follower = cls(**kwargs)
    #     if session:
    #         session.add(follower)
    #     return follower
