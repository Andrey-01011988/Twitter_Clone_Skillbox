import logging
from typing import Union

from fastapi import Header, HTTPException, Depends

from application.crud import BaseDAO
from application.database import AsyncSessionApp
from application.models import Users, Tweets, Media, Like, Followers
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from starlette.responses import JSONResponse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Назначение текущей сессии
async def get_current_session() -> AsyncSession:
    logger.info("Создание новой сессии Dependencies")
    async with AsyncSessionApp() as current_session:
        try:
            logger.info(f"Передача сессии session: {current_session}")
            yield current_session
        finally:
            logger.info(f"Закрывается сессия session: {current_session}")
            await current_session.close()
            logger.info("Закрытие сессии Dependencies")


async def get_client_token(
    session: AsyncSession = Depends(get_current_session), api_key: str = Header(...)
):
    """
    Извлекает API ключ из заголовка и проверяет его на валидность.

    :param session:
    :param api_key: API ключ пользователя
    :return: API ключ, если он валиден
    """
    user = await UserDAO.find_one_or_none(api_key=api_key, session=session)
    logger.info(f"Пользователь найден {user}")
    if user is None:
        raise HTTPException(
            status_code=403, detail="Доступ запрещен: неверный API ключ"
        )
    logger.info(f"Возвращен ключ api_key: {api_key}")
    return api_key


# Зависимость для получения текущего пользователя
async def get_current_user(
    session: AsyncSession = Depends(get_current_session),
    api_key: str = Depends(get_client_token),
) -> Union[Users, JSONResponse]:
    current_user = await UserDAO.find_one_or_none(
        session=session,
        options=[selectinload(Users.authors), selectinload(Users.followers)],
        api_key=api_key,
    )
    if not current_user:
        logger.warning(f"Пользователь с API ключом {api_key} не найден.")
        return JSONResponse(status_code=404, content={"error": "User not found"})
    return current_user


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
