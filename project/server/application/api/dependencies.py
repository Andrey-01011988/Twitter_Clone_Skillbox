import logging

from fastapi import Header, HTTPException, Request, Depends
from sqlalchemy import delete, and_

from application.crud import BaseDAO
from application.database import AsyncSessionApp
from application.models import Users, Tweets, Media, Like, Followers
from sqlalchemy.ext.asyncio import AsyncSession

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Назначение текущей сессии
async def get_current_session() -> AsyncSession:
    logger.info("Создание новой сессии Dependencies")
    async with AsyncSessionApp() as current_session:
        try:
            yield current_session
        finally:
            await current_session.close()
            logger.info("Закрытие сессии Dependencies")


async def get_client_token(session: AsyncSession = Depends(get_current_session), api_key: str = Header(...)):
    """
    Извлекает API ключ из заголовка и проверяет его на валидность.

    :param session:
    :param api_key: API ключ пользователя
    :return: API ключ, если он валиден
    """
    user = await UserDAO.find_one_or_none(api_key=api_key,  session=session)
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


class MediaDAO(BaseDAO):
    model = Media


class LikeDAO(BaseDAO):
    model = Like


class FollowersDAO(BaseDAO):
    model = Followers
