import logging
from datetime import datetime
from typing import Dict, Union, List, Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from starlette.responses import JSONResponse

from application.api.dependencies import get_current_session, TweetDAO, get_current_user, MediaDAO, LikeDAO
from application.models import Tweets, Like, Users
from application.schemas import TweetOut, ErrorResponse, TweetIn

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


tweets_router = APIRouter(prefix="/api", tags=["Tweets"])


@tweets_router.get("/tweets", response_model=Dict[str, Union[bool, List[TweetOut]]],
                 responses={403: {"model": ErrorResponse}, 500: {"model": ErrorResponse}})
async def get_users_tweets(
        session: AsyncSession = Depends(get_current_session)
    ) -> JSONResponse | dict[
    str, bool | list[Any]] | Any:
    """
    Получение ленты твитов для пользователя.

    Этот эндпоинт позволяет пользователю получить список твитов на основе переданного API ключа.
    Если API ключ неверный, возвращается ошибка 403. В случае других ошибок возвращается ошибка 500.

    Пример запроса:
        curl -i -H "api-key: 1wc65vc4v1fv" "http://localhost:5000/api/tweets"

    Аргументы:
        session (AsyncSession): Асинхронная сессия SQLAlchemy.

    Возвращает:
        JSON-ответ с результатом запроса. Если запрос успешен, возвращает список твитов.
        В случае ошибки возвращает соответствующее сообщение об ошибке.

        - Код 403: `detail`: "User not authenticated".
        - Код 500: `detail`: Сообщение об ошибке с описанием проблемы.

    Пример успешного ответа:
    {
        "result": true,
        "tweets": [
            {
                "id": 1,
                "content": "Привет, мир!",
                "author": {
                    "id": 123,
                    "name": "Пользователь1"
                },
                "attachments": [],
                "likes": []
            },
            ...
        ]
    }

    Примечание: Убедитесь, что переданный API ключ действителен и соответствует зарегистрированному пользователю.
    """
    logger.info(f"Сессия получена из зависимости session: {session}")
    try:
        # Получаем все твиты пользователя с подгрузкой связанных данных (автор, медиа и лайки)
        logger.info(f"Сессия передается в метод запроса session: {session}")
        all_tweets = await TweetDAO.find_all(session=session, options=[
            selectinload(Tweets.author),  # Подгружаем автора твита
            selectinload(Tweets.attachments),  # Подгружаем медиафайлы твита
            selectinload(Tweets.likes).selectinload(Like.user)  # Подгружаем лайки и пользователей, которые их поставили
        ])

        # Преобразуем каждый твит в формат JSON
        tweets_json = [tweet.to_json() for tweet in all_tweets]
    except Exception as e:
        # Обработка любых других ошибок (например, ошибки базы данных)
        raise HTTPException(status_code=500, detail=str(e))

    # Возвращаем успешный ответ с результатами
    return {
        "result": True,
        "tweets": tweets_json  # Список твитов в формате JSON
    }


@tweets_router.post("/tweets", status_code=201)
async def add_tweet(
        tweet: TweetIn,
        session: AsyncSession = Depends(get_current_session),
        current_user: Users = Depends(get_current_user)
    ) -> dict[str, bool | Any]:
    """
    Добавляет новый твит от пользователя.

    Аргументы:
        tweet (TweetIn): Объект типа TweetIn, содержащий данные о твите.
        current_user (Users): Текущий пользователь, который добавляет твит.
                              Получается из зависимости get_current_user.
        session (AsyncSession): Асинхронная сессия SQLAlchemy.

    Возвращает:
        Словарь с результатом операции и идентификатором нового твита.

        Пример ответа:
        {
            "result": True,
            "tweet_id": 123
        }

    :raises HTTPException: Если произошла ошибка при добавлении твита, возвращает статус 400 и сообщение об ошибке.

    Пример запроса:
    ```
    curl -iX POST "http://localhost:5000/api/tweets"
        -H "Api-Key: 1wc65vc4v1fv"
        -H "Content-Type: application/json"
        -d '{"tweet_media_ids": [], "tweet_data": "Привет"}'
    ```
    """

    new_tweet_data = {
        "author_id": current_user.id,
        "text": tweet.tweet_data,
        "timestamp": datetime.now().replace(tzinfo=None)
    }

    try:
        new_tweet = await TweetDAO.add(session=session, **new_tweet_data)

        # Привязка медиафайлов к новому твиту
        for media_id in tweet.tweet_media_ids:
            media = await MediaDAO.find_one_or_none_by_id(media_id, session=session)  # Получаем медиа по ID
            if media:
                media.tweet_id = new_tweet.id  # Привязываем медиа к новому твиту
                await MediaDAO.update(session=session, instance=media,
                                      tweet_id=new_tweet.id)  # Обновляем запись в базе данных

        return {"result": True, "tweet_id": new_tweet.id}

    except SQLAlchemyError as e:
        raise HTTPException(status_code=400, detail=str(e))


@tweets_router.post("/tweets/{tweet_id}/likes")
async def add_like(tweet_id: int,
                    session: AsyncSession = Depends(get_current_session),
                    current_user: Users = Depends(get_current_user)) -> dict:
    """
    Пользователь может поставить отметку «Нравится» на твит по его идентификатору.
    Лайк можно поставить только на существующий твит.

    Аргументы:
        tweet_id (int): Идентификатор твита, к которому пользователь хочет добавить лайк.
        current_user (Users): Текущий пользователь, полученный из зависимостей.
        session (AsyncSession): Асинхронная сессия SQLAlchemy.

    Возвращает:
        Статус операции в формате JSON.

    Пример запроса с использованием curl:
    ```
    curl -i -X POST -H "Api-Key: 1wc65vc4v1fv" "http://localhost:5000/api/tweets/<tweet_id>/likes"
    ```

    :raises HTTPException:
        - 403, если пользователь не аутентифицирован.
        - 404, если твит не найден.
    """

    tweet = await TweetDAO.find_one_or_none_by_id(tweet_id, session=session)

    if not tweet:
        raise HTTPException(status_code=404, detail="Твит не найден")

    await LikeDAO.add(session=session, tweet_id=tweet_id, user_id=current_user.id)

    return {"result": True}


@tweets_router.delete("/tweets/{tweet_id}")
async def delete_tweet(tweet_id: int,
                        session: AsyncSession = Depends(get_current_session),
                        current_user: Users = Depends(get_current_user)) -> dict:
    """
    Этот эндпоинт позволяет пользователю удалить твит по его идентификатору.
    Удаление возможно только для твитов, принадлежащих текущему пользователю.

    Аргументы:
        tweet_id (int): Идентификатор твита для удаления.
        current_user (Users): Текущий пользователь, полученный из зависимостей.
        session (AsyncSession): Асинхронная сессия SQLAlchemy.

    Возвращает:
        Статус операции в формате JSON.

    Пример запроса с использованием curl:
    ```
    curl -i -X DELETE -H "Api-Key: 1wc65vc4v1fv" "http://localhost:5000/api/tweets/<tweet_id>"
    ```

    :raises HTTPException:
        - 403, если пользователь не аутентифицирован.
        - 404, если твит не найден или пользователь не имеет прав на его удаление.
    """
    # Находим твит по идентификатору
    current_tweet = await TweetDAO.find_one_or_none_by_id(tweet_id, session=session)

    # Проверяем, существует ли твит и принадлежит ли он текущему пользователю
    if not current_tweet or current_tweet.author_id != current_user.id:
        raise HTTPException(status_code=404, detail="Твит не найден или вы не имеете прав на его удаление")

    # Удаляем твит
    await TweetDAO.delete(session=session, instance=current_tweet)

    return {"result": True}


@tweets_router.delete("/tweets/{tweet_id}/likes")
async def delete_like(tweet_id: int,
                        session: AsyncSession = Depends(get_current_session),
                        current_user: Users = Depends(get_current_user)) -> dict:
    """
    Пользователь может убрать отметку «Нравится» с твита.

    Аргументы:
        tweet_id (int): Идентификатор твита, с которого пользователь хочет убрать лайк.
        current_user (Users): Текущий пользователь, полученный из зависимостей.
        session (AsyncSession): Асинхронная сессия SQLAlchemy.

    Возвращает:
        Статус операции в формате JSON.

    Пример запроса с использованием curl:
    ```
    curl -i -X DELETE -H "Api-Key: 1wc65vc4v1fv" "http://localhost:5000/api/tweets/<tweet_id>/likes"
    ```

    :raises HTTPException:
        - 403, если пользователь не аутентифицирован.
        - 404, если лайк не найден или пользователь не имеет прав на его удаление.
    """
    # Ищем лайк по идентификатору твита и пользователю
    like = await LikeDAO.find_one_or_none(
        tweet_id=tweet_id,
        user_id=current_user.id,
        session=session
    )

    if not like:
        raise HTTPException(status_code=404, detail="Лайк не найден или вы не имеете прав на его удаление")

    # Удаляем лайк
    await LikeDAO.delete(session=session, instance=like)

    return {"result": True}