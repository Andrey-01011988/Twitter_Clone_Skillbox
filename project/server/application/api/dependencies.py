from crud import BaseDAO
from database import AsyncSessionApp
from fastapi import Header, HTTPException, Request
from models import Users, Tweets, Media, Like, Followers
from sqlalchemy import delete, and_


# Назначение текущей сессии
async def get_current_session():
    current_session = AsyncSessionApp()
    try:
        yield current_session
    finally:
        await current_session.close()


async def get_client_token(api_key: str = Header(...)):
    """
    Извлекает API ключ из заголовка и проверяет его на валидность.

    :param api_key: API ключ пользователя
    :return: API ключ, если он валиден
    """
    user = await UserDAO.find_one_or_none(api_key=api_key)
    if user is None:
        raise HTTPException(status_code=403, detail="Доступ запрещен: неверный API ключ")
    return api_key


# Зависимость для получения текущего пользователя
async def get_current_user(request: Request):
    if not hasattr(request.state, 'current_user'):
        raise HTTPException(status_code=403, detail="User not authenticated")
    return request.state.current_user


class UserDAO(BaseDAO):
    model = Users


class TweetDAO(BaseDAO):
    model = Tweets

    @classmethod
    async def delete_tweet(cls, tweet_id: int, user_id: int):
        """
        Удаляет твит, если он принадлежит указанному пользователю.

        :param tweet_id: Идентификатор твита
        :param user_id: Идентификатор пользователя
        :return: True, если твит был удален, иначе False
        """
        async with AsyncSessionApp() as session:
            async with session.begin():
                tweet = await cls.find_one_or_none_by_id(
                    data_id=tweet_id
                )
                if tweet and tweet.author_id == user_id:
                    await session.delete(tweet)
                    return True
                return False


class MediaDAO(BaseDAO):
    model = Media


class LikeDAO(BaseDAO):
    model = Like

    @classmethod
    async def delete_like(cls, tweet_id: int, user_id: int):
        """
        Удаляет лайк, если он принадлежит указанному пользователю.

        :param tweet_id: Идентификатор твита
        :param user_id: Идентификатор пользователя
        :return: True, если твит был удален, иначе False
        """
        async with AsyncSessionApp() as session:
            async with session.begin():
                like = await cls.find_one_or_none(
                    tweet_id=tweet_id,
                    user_id=user_id
                )
                if like:
                    await session.delete(like)
                    return True
                return False


class FollowersDAO(BaseDAO):
    model = Followers

    @classmethod
    async def add(cls, follower_id: int, followed_id: int):
        """
        Асинхронно добавляет новую запись о подписке между пользователями.

        :param follower_id: Идентификатор пользователя, который фолловит.
        :param followed_id: Идентификатор пользователя, на которого фолловят.
        """

        # Проверяем существование записи
        existing_follow = await cls.find_one_or_none(
            follower_id=follower_id,
            followed_id=followed_id
        )

        if existing_follow:
            raise Exception("Подписка уже существует")

        async with AsyncSessionApp() as session:
            async with session.begin():
                new_follow = cls.model(follower_id=follower_id, followed_id=followed_id)
                session.add(new_follow)
                await session.commit()

    @classmethod
    async def delete(cls, follower_id: int, followed_id: int):
        """
        Асинхронно удаляет запись о подписке между пользователями.

        :param follower_id: Идентификатор пользователя, который отписывается.
        :param followed_id: Идентификатор пользователя, от которого отписываются.
        """
        async with AsyncSessionApp() as session:
            async with session.begin():
                await session.execute(
                    delete(cls.model).where(
                        and_(
                            cls.model.follower_id == follower_id,
                            cls.model.followed_id == followed_id
                        )
                    )
                )
                await session.commit()
