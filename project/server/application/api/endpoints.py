from datetime import datetime
from io import BytesIO
from typing import List, Sequence, Optional, Dict, Union, Any

from PIL import Image
from fastapi import APIRouter, Depends, Header, HTTPException, UploadFile, File
from fastapi.responses import  StreamingResponse

from api.dependencies import get_current_session, UserDAO, TweetDAO, MediaDAO, get_client_token
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
    curl -i -H "api-key: 1wc65vc4v1fv" "http://localhost:5000/api/tweets"

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
                selectinload(Tweets.attachments),  # Подгружаем медиафайлы твита
                selectinload(Tweets.likes).selectinload(Like.user)  # Подгружаем лайки и пользователей, которые их поставили
            ],
            author_id=user.id)

        # Применяем unique() к результату
        # all_tweets = all_tweets.unique()

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
   Получение информации о профиле текущего пользователя.

    Этот эндпоинт позволяет пользователю получить информацию о своем профиле,
    включая данные о подписках и подписчиках.

    :param api_key: API ключ пользователя, необходимый для аутентификации.
    :return:
        - result (bool): Указывает на успешность операции.
        - user (UserOut): Объект с информацией о пользователе.

    Примеры возможных ответов:
        - Успешный ответ:
            {
                "result": true,
                "user": {
                    "id": 1,
                    "username": "example_user",
                    "followers": [...],
                    "following": [...]
                }
            }
        - Ошибка 403:
            {
                "result": false,
                "error_type": "AccessDenied",
                "error_message": "Доступ запрещен: неверный API ключ"
            }
        - Ошибка 500:
            {
                "result": false,
                "error_type": "InternalServerError",
                "error_message": "Произошла ошибка на сервере"
            }

    curl -i -X GET -H "Api-Key: 1wc65vc4v1fv" "http://localhost:5000/api/users/me"
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


@main_router.get("/medias/{media_id}")
async def get_media(media_id: int):
    """
    Получение медиа привязанного к твиту в виде изображения.

    :param media_id: Идентификатор медиа.
    :return: Возвращает изображение в формате, определяемом по содержимому.
    curl -i -X GET "http://localhost:5000/api/medias/1"
    """
    media = await MediaDAO.find_one_or_none_by_id(media_id)

    if media is None:
        raise HTTPException(status_code=404, detail="Media not found")

    # Создаем поток для передачи данных
    image_stream = BytesIO(media.file_body)

    try:
        # Открываем изображение с помощью Pillow для определения формата
        image = Image.open(image_stream)
        content_type = f'image/{image.format.lower()}'  # Получаем тип контента в нижнем регистре

        # Сбрасываем указатель потока на начало
        image_stream.seek(0)

        return StreamingResponse(image_stream, media_type=content_type)

    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid image data")


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
async def add_media(api_key: str = Depends(get_client_token), file: UploadFile = File(...), tweet_id: int = None):
    """
     Эндпоинт для загрузки медиафайлов.

    Этот эндпоинт позволяет пользователям загружать медиафайлы (например, изображения) и
    связывать их с определенным твитом по его идентификатору.

    :param api_key: API ключ пользователя, необходимый для аутентификации.
    :param file: Загружаемый файл (изображение или другой медиафайл).
    :param tweet_id: (необязательный) ID твита, к которому будет привязано медиа.
                     Если передан, проверяется существование твита.

    :return: JSON-ответ с результатом операции и ID загруженного медиафайла.

    Пример запроса с использованием curl:
    ```
    curl -i -X POST -H "api-key: 1wc65vc4v1fv" -F "file=@/path/to/your/image.jpg" "http://localhost:5000/api/medias?tweet_id=3"
    ```

    :raises HTTPException:
        - 404, если указанный tweet_id не соответствует существующему твиту.
        - 400, если произошла ошибка при загрузке файла или создании записи в базе данных.

    curl -i -X POST -H "api-key: 1wc65vc4v1fv" -F "file=@/home/uservm/PycharmProjects/python_advanced_diploma/cats_1179x2556.jpg" "http://localhost:5000/api/medias?tweet_id=3"
    """
    # Проверяем наличие твита, если tweet_id передан
    if tweet_id is not None:
        tweet = await TweetDAO.find_one_or_none_by_id(tweet_id)
        if tweet is None:
            raise HTTPException(status_code=404, detail="Твит не найден")

    # Сохранение файла на сервере
    try:
        # file_location = f"static/media/{file.filename}"  # Путь для сохранения файла
        # with open(file_location, "wb") as buffer:
        #     buffer.write(await file.read())

        file_body = await file.read()
        # Создание записи в базе данных
        new_media = await MediaDAO.add(file_body=file_body,
                                       file_name=file.filename,
                                       tweet_id=tweet_id)  # Здесь можно указать tweet_id если он известен

        return {"result": True, "media_id": new_media.id}

    except Exception as e:
        raise HTTPException(status_code=500, detail="Ошибка при загрузке файла")


@main_router.delete("/tweets/{tweet_id}")
async def delete_tweet(tweet_id: int, api_key: str = Depends(get_client_token)) -> dict:
    """
    Пользователь удаляет именно свой собственный твит.

    :param tweet_id: Идентификатор твита для удаления.
    :param api_key: API ключ пользователя.
    :return: Статус операции.
    curl -i -X DELETE -H "api-key: 1wc65vc4v1fv" "http://localhost:5000/api/tweets/4"
    """
    cur_user = await UserDAO.find_one_or_none(api_key=api_key)

    # Пытаемся удалить твит через TweetDAO
    result = await TweetDAO.delete_tweet(tweet_id=tweet_id, user_id=cur_user.id)

    if not result:
        raise HTTPException(status_code=404, detail="Твит не найден или вы не имеете прав на его удаление")

    return {"result": True}
