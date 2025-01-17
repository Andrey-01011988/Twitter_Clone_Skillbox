import os
import factory
from faker import Faker
from application.models import Users, Tweets, Like, Media, Followers


fake = Faker("ru_RU")


class UserFactory(factory.alchemy.SQLAlchemyModelFactory):
    """Генератор случайных пользователей."""

    class Meta:
        model = Users
        sqlalchemy_session = None

    name = factory.LazyAttribute(lambda _: fake.name())  # Генерация имени пользователя
    api_key = factory.LazyAttribute(
        lambda _: fake.bothify(text="??###?##")
    )  # Генерация API-ключа


class TweetFactory(factory.alchemy.SQLAlchemyModelFactory):
    """Генератор случайных твитов."""

    class Meta:
        model = Tweets
        sqlalchemy_session = None

    text = factory.LazyAttribute(
        lambda _: fake.sentence(nb_words=5, variable_nb_words=True)
    )  # Генерация текста твита
    author_id = factory.SubFactory(
        UserFactory
    )  # Привязка твита к случайному пользователю


class LikeFactory(factory.alchemy.SQLAlchemyModelFactory):
    """Генератор случайных лайков."""

    class Meta:
        model = Like
        sqlalchemy_session = None

    tweet_id = factory.SubFactory(TweetFactory)  # Создание твита, который лайкаем
    user_id = factory.SubFactory(
        UserFactory
    )  # Создание пользователя, который ставит лайк


class MediaFactory(factory.alchemy.SQLAlchemyModelFactory):
    """Генератор случайных медиафайлов."""

    class Meta:
        model = Media
        sqlalchemy_session = None

    @factory.lazy_attribute
    def file_body(self):
        """Загрузка изображения из файла."""
        image_directory = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "./images")
        )
        image_files = os.listdir(image_directory)

        # Выбор случайного изображения из директории
        selected_image = fake.random_element(image_files)

        # Полный путь к изображению
        image_path = os.path.join(image_directory, selected_image)

        # Чтение изображения в бинарном формате
        with open(image_path, "rb") as f:
            return f.read()  # Возвращаем бинарные данные изображения

    @factory.lazy_attribute
    def file_name(self):
        """Имя файла медиа."""
        image_directory = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "./images")
        )
        selected_image = fake.random_element(os.listdir(image_directory))
        return selected_image  # Возвращаем имя файла

    tweet_id = factory.SubFactory(TweetFactory)  # Привязываем медиа к твиту


class FollowerFactory(factory.alchemy.SQLAlchemyModelFactory):
    """Генератор случайных подписок пользователей."""

    class Meta:
        model = Followers
        sqlalchemy_session = None

    account_id = factory.SubFactory(
        UserFactory
    )  # Создание пользователя, который подписывается
    follower_id = factory.SubFactory(
        UserFactory
    )  # Создание пользователя, на которого подписываются
