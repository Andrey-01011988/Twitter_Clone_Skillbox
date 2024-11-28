from datetime import datetime
from typing import List, Sequence, Optional, Dict, Union, Any

from fastapi import APIRouter, Depends, Header, HTTPException, UploadFile, File

from api.depencies import get_current_session, UserDAO, TweetDAO, MediaDAO, get_client_token
from models import Users, Tweets, Like
from schemas import UserOut, TweetIn, TweetOut, ErrorResponse, SimpleUserOut
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import selectinload
from starlette.responses import JSONResponse

main_router = APIRouter(prefix="/api", tags=["API"], dependencies=[Depends(get_current_session)])


@main_router.get("/users", response_model=List[SimpleUserOut])
async def get_all_users() -> Sequence[Users]:
    """
        Выводит всех пользователей
        curl -i GET "http://localhost:8000/api/users"
        Для запуска в docker-compose:
        curl -i GET "http://localhost:5000/api/users"
    """

    result = await UserDAO.find_all()

    return result


@main_router.get("/tweets", response_model=Dict[str, Union[bool, List[TweetOut]]],
         responses={403: {"model": ErrorResponse}, 500: {"model": ErrorResponse}})
async def get_users_tweets(api_key: str = Depends(get_client_token)) -> JSONResponse | dict[str, bool | list[Any]] | Any:
    """
    Получение ленты твитов для пользователя.

    Этот endpoint позволяет пользователю получить список твитов на основе переданного API ключа.
    Если API ключ неверный, возвращается ошибка 403. В случае других ошибок возвращается ошибка 500.

    Пример запроса:
    curl -i -H "api-key: 1wc65vc4v1fv" GET "http://localhost:5000/api/tweets"

    :param api_key: API ключ пользователя, который используется для аутентификации.
    :return: JSON-ответ с результатом запроса. Если запрос успешен, возвращает список твитов.
             В случае ошибки возвращает соответствующее сообщение об ошибке.
    """
    # Проверяем наличие пользователя по переданному API ключу
    user = await UserDAO.find_one_or_none(api_key=api_key)

    try:
        # Получаем все твиты пользователя с подгрузкой связанных данных (автор, медиа и лайки)
        all_tweets = await TweetDAO.find_all(options=[
                selectinload(Tweets.author), # Подгружаем автора твита
                selectinload(Tweets.media),  # Подгружаем медиафайлы твита
                selectinload(Tweets.likes).selectinload(Like.user)  # Подгружаем лайки и пользователей, которые их поставили
            ],
            author_id=user.id)

        # Преобразуем каждый твит в формат JSON
        tweets_json = [tweet.to_json() for tweet in all_tweets]
    except Exception as e:
        # # Обработка любых других ошибок (например, ошибки базы данных)
        raise HTTPException(status_code=500, detail=str(e))

    # Возвращаем успешный ответ с результатами
    return {
        "result": True,
        "tweets": tweets_json  # Список твитов в формате JSON
    }


@main_router.get("/users/me", response_model=Dict[str, Union[bool, UserOut]],
                 responses={403: {"model": ErrorResponse}, 500: {"model": ErrorResponse}})
async def get_user_info(api_key: str = Depends(get_client_token)) -> JSONResponse | dict[str, bool | list[Any]] | Any:
    """
    Пользователь получает информацию о своем профиле.
    :param api_key:
    :return:
    """
    cur_user = await UserDAO.find_one_or_none(
        options=[
            selectinload(Users.followers),
            selectinload(Users.following)
        ],
        api_key=api_key
    )


    return {
        "result": True,
        "user": cur_user.to_json()
    }


# @main_router.post("/tweets", response_model=TweetIn, status_code=201)
@main_router.post("/tweets", status_code=201)
async def  add_tweet(tweet: TweetIn, api_key: str = Depends(get_client_token)) -> dict:
    """
    Добавляет новый твит от пользователя
    curl -iX POST "http://localhost:5000/api/tweets" -H "api-key: 1wc65vc4v1fv" -H "Content-Type: application/json" -d '{"tweet_media_ids": [], "text": "Привет"}'
    :param tweet:
    :param api_key:  ключ пользователя
    :return: Результат операции и идентификатор нового твита
    """
    user = await UserDAO.find_one_or_none(api_key=api_key)

    new_tweet_data ={
        "author_id": user.id,
        "text": tweet.text,
        "timestamp": datetime.now().replace(tzinfo=None)
    }
    try:
        new_tweet = await TweetDAO.add(**new_tweet_data)
        return {"result": True, "tweet_id": new_tweet.id}
    except SQLAlchemyError as e:
        raise HTTPException(status_code=400, detail=str(e))


@main_router.post("/medias")
async def add_media(api_key: str = Header(...) ):
    """
    Endpoint для загрузки файлов из твита.
    :return:
    """


@main_router.post("/medias")
async def add_media(api_key: str = Depends(get_client_token), file: UploadFile = File(...), tweet_id: int = None):
    """
    Endpoint для загрузки медиафайлов.
    :param api_key: API ключ пользователя
    :param file: Загружаемый файл
    :param tweet_id: ID твита, к которому будет привязано медиа
    :return: ID загруженного медиафайла

    curl -i -X POST -H "api-key: 1wc65vc4v1fv" -F "file=/home/uservm/PycharmProjects/python_advanced_diploma/cats_1179x2556.jpg" "http://localhost:5000/api/medias?tweet_id=3"
    """
    # Проверяем наличие твита, если tweet_id передан
    if tweet_id is not None:
        tweet = await TweetDAO.find_one_or_none_by_id(tweet_id)
        if tweet is None:
            raise HTTPException(status_code=404, detail="Твит не найден")

    # Сохранение файла на сервере
    try:
        file_location = f"static/media/{file.filename}"  # Путь для сохранения файла
        with open(file_location, "wb") as buffer:
            buffer.write(await file.read())

        # Создание записи в базе данных
        new_media = await MediaDAO.add(url=file_location,
                                       tweet_id=tweet_id)  # Здесь можно указать tweet_id если он известен

        return {"result": True, "media_id": new_media.id}

    except SQLAlchemyError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Ошибка при загрузке файла")
