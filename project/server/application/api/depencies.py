from crud import BaseDAO
from database import AsyncSessionApp
from fastapi import Header, HTTPException
from models import Users, Tweets, Media


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


class UserDAO(BaseDAO):
    model = Users


class TweetDAO(BaseDAO):
    model = Tweets

class MediaDAO(BaseDAO):
    model = Media
