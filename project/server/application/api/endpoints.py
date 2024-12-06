from datetime import datetime
from io import BytesIO
from typing import List, Sequence, Optional, Dict, Union, Any

from PIL import Image
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import  StreamingResponse

from api.dependencies import get_current_session, UserDAO, TweetDAO, MediaDAO, LikeDAO, FollowersDAO, get_client_token, get_current_user
from models import Users, Tweets, Like
from schemas import UserOut, TweetIn, TweetOut, ErrorResponse, SimpleUserOut, UserIn
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import selectinload
from starlette.responses import JSONResponse

main_router = APIRouter(prefix="/api", tags=["API"], dependencies=[Depends(get_current_session)])


@main_router.get("/all_users", response_model=List[SimpleUserOut])
async def get_all_users() -> Sequence[Users]:
    """
        Выводит всех пользователей
        curl -i GET "http://localhost:8000/api/all_users"
        Для запуска в docker-compose:
        curl -i GET "http://localhost:5000/api/all_users"
    """

    result = await UserDAO.find_all()

    return result


@main_router.get("/tweets", response_model=Dict[str, Union[bool, List[TweetOut]]],
         responses={403: {"model": ErrorResponse}, 500: {"model": ErrorResponse}})
async def get_users_tweets(current_user: Users = Depends(get_current_user)) -> JSONResponse | dict[str, bool | list[Any]] | Any:
    """
    Получение ленты твитов для пользователя.

    Этот endpoint позволяет пользователю получить список твитов на основе переданного API ключа.
    Если API ключ неверный, возвращается ошибка 403. В случае других ошибок возвращается ошибка 500.

    Пример запроса:
    curl -i -H "api-key: 1wc65vc4v1fv" "http://localhost:5000/api/tweets"

    :param current_user: Пользователь, полученный из зависимости `get_current_user`,
                         который извлекает текущего пользователя из состояния запроса.
                         Если пользователь не аутентифицирован, возвращается ошибка 403.
    :return: JSON-ответ с результатом запроса. Если запрос успешен, возвращает список твитов.
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

    try:
        # Получаем все твиты пользователя с подгрузкой связанных данных (автор, медиа и лайки)
        all_tweets = await TweetDAO.find_all(options=[
                selectinload(Tweets.author), # Подгружаем автора твита
                selectinload(Tweets.attachments),  # Подгружаем медиафайлы твита
                selectinload(Tweets.likes).selectinload(Like.user)  # Подгружаем лайки и пользователей, которые их поставили
            ],
            author_id=current_user.id)

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
async def get_user_info(current_user: Users = Depends(get_current_user)) -> JSONResponse | dict[str, bool | list[Any]] | Any:
    """
   Получение информации о профиле текущего пользователя.

    Этот эндпоинт позволяет пользователю получить информацию о своем профиле,
    включая данные о подписках и подписчиках.

    :param current_user: Пользователь, полученный из зависимости `get_current_user`,
                         который извлекает текущего пользователя из состояния запроса.
                         Если пользователь не аутентифицирован, возвращается ошибка 403.
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

    return {
        "result": True,
        "user": current_user.to_json()
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


@main_router.get("/users/{user_id}", response_model=Dict[str, Union[bool, UserOut]],
                 responses={403: {"model": ErrorResponse}, 500: {"model": ErrorResponse}})
async def get_user_info_by_id(user_id: int, current_user: Users = Depends(get_current_user)) -> JSONResponse | dict[str, bool | list[Any]] | Any:
    """
    Пользователь может получить информацию о произвольном профиле по его id.

    :param user_id: Идентификатор пользователя, информацию о котором необходимо получить.
    :param current_user: Текущий аутентифицированный пользователь.
    :return: Статус операции и информация о пользователе в формате JSON.

    Пример запроса с использованием curl:
    ```
    curl -i -X GET -H "Api-Key: 1wc65vc4v1fv" "http://localhost:5000/api/users/<user_id>"
    ```

    :raises HTTPException:
        - 403, если пользователь не аутентифицирован.
        - 404, если пользователь с указанным id не найден.
        - 500, если произошла внутренняя ошибка сервера.
    """

    user_info_by_id = await UserDAO.find_one_or_none_by_id(
        user_id,
        options=[
            selectinload(Users.followers),
            selectinload(Users.following)
        ]
    )
    if user_info_by_id is None:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    return {
        "result": True,
        "user": user_info_by_id.to_json()
    }


# Просто добавил из main.py
@main_router.post("/add_user", status_code=201)
async def add_one_user(user: UserIn) -> str:
    """
    Добавляет пользователя, возвращает его
    curl -X POST "http://localhost:8000/api/add_user" -H "Content-Type: application/json" -d '{"name": "Anon", "api_key": "1wc65vc4v1fv"}'
    Для запуска в docker-compose:
    curl -X POST "http://localhost:5000/api/add_user" -H "Content-Type: application/json" -d '{"name": "Dan", "api_key": "test"}'
    """

    new_user = await UserDAO.add(**user.dict())

    return f"User added: {new_user}\n"


@main_router.post("/tweets", status_code=201)
async def  add_tweet(tweet: TweetIn, current_user: Users = Depends(get_current_user)) -> dict:
    """
    Добавляет новый твит от пользователя
    curl -iX POST "http://localhost:5000/api/tweets"
        -H "Api-Key: 1wc65vc4v1fv"
        -H "Content-Type: application/json"
        -d '{"tweet_media_ids": [], "content": "Привет"}'
    :param current_user: Текущий пользователь, который добавляет твит.
                         Получается из зависимости get_current_user.
    :param tweet: Объект типа TweetIn, содержащий данные о твите.
                  Поля:
                  - tweet_media_ids (List[int]): Список идентификаторов медиа, связанных с твитом.
                  - content (str): Содержимое твита.
    :return: Словарь с результатом операции и идентификатором нового твита.
             Пример ответа:
             {
                 "result": True,
                 "tweet_id": 123
             }
    :raises HTTPException: Если произошла ошибка при добавлении твита, возвращает статус 400 и сообщение об ошибке.
    """

    new_tweet_data ={
        "author_id": current_user.id,
        "text": tweet.content,
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
    curl -i -X POST -H "api-key: 1wc65vc4v1fv" -F "file=@/path/to/your/image.jpg" "http://localhost:5000/api/medias?tweet_id=3"

    :raises HTTPException:
        - 404, если указанный tweet_id не соответствует существующему твиту.
        - 400, если произошла ошибка при загрузке файла или создании записи в базе данных.

    curl -i -X POST -H "Api-Key: 1wc65vc4v1fv" -F "file=@/home/uservm/PycharmProjects/python_advanced_diploma/cats_1179x2556.jpg"
    "http://localhost:5000/api/medias?tweet_id=3"
    /home/uservm/PycharmProjects/python_advanced_diploma/bottom-view-plane-sky.jpg
    """
    # Проверяем наличие твита, если tweet_id передан
    if tweet_id is not None:
        tweet = await TweetDAO.find_one_or_none_by_id(tweet_id)
        if tweet is None:
            raise HTTPException(status_code=404, detail="Твит не найден")

    # Сохранение файла на сервере
    try:

        file_body = await file.read()
        # Создание записи в базе данных
        new_media = await MediaDAO.add(file_body=file_body,
                                       file_name=file.filename,
                                       tweet_id=tweet_id)  # Здесь можно указать tweet_id если он известен

        return {"result": True, "media_id": new_media.id}

    except Exception as e:
        raise HTTPException(status_code=500, detail="Ошибка при загрузке файла")


@main_router.post("/tweets/{tweet_id}/likes")
async def add_like(tweet_id: int, current_user: Users = Depends(get_current_user)) -> dict:
    """
    Пользователь может поставить отметку «Нравится» на твит по его идентификатору.
    Лайк можно поставить только на существующий твит.

    :param tweet_id: Идентификатор твита, к которому пользователь хочет добавить лайк.
    :param current_user: Текущий пользователь, полученный из зависимостей.
    :return: Статус операции в формате JSON.

    Пример запроса с использованием curl:
    curl -i -X POST -H "Api-Key: 1wc65vc4v1fv" "http://localhost:5000/api/tweets/<tweet_id>/likes"

    :raises HTTPException:
        - 403, если пользователь не аутентифицирован.
        - 404, если твит не найден.
    """

    tweet = await TweetDAO.find_one_or_none_by_id(tweet_id)

    if not tweet:
        raise HTTPException(status_code=404, detail="Твит не найден")

    await LikeDAO.add(
        tweet_id=tweet_id,
        user_id=current_user.id
    )

    return {"result": True}


@main_router.post("/users/{user_id}/follow")
async def follow_user(user_id: int, current_user: Users = Depends(get_current_user)) -> dict:
    """
    Пользователь может зафоловить другого пользователя.
    :param user_id: Пользователь, которого фолловят.
    :param current_user: Пользователь, который фолловит.
    :return: Статус операции в формате JSON.

    Пример запроса с использованием curl:
    curl -X POST -H "Api-Key: 1wc65vc4v1fv" http://localhost:5000/api/users/<user_id>/follow
    """

    # Проверяем, существует ли пользователь, на которого подписываются
    followed_user = await UserDAO.find_one_or_none_by_id(user_id)

    if not followed_user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    # Проверяем, не подписан ли текущий пользователь уже на данного пользователя
    existing_follow = await FollowersDAO.find_one_or_none(
        follower_id=current_user.id,
        followed_id=user_id
    )

    if existing_follow:
        raise HTTPException(status_code=409, detail="Вы уже подписаны на этого пользователя")

    # Добавляем запись о подписке в таблицу followers
    await FollowersDAO.add(follower_id=current_user.id, followed_id=user_id)

    return {"result": True}


@main_router.delete("/tweets/{tweet_id}")
async def delete_tweet(tweet_id: int, current_user: Users = Depends(get_current_user)) -> dict:
    """
    Этот эндпоинт позволяет пользователю удалить твит по его идентификатору.
    Удаление возможно только для твитов, принадлежащих текущему пользователю.

    :param tweet_id: Идентификатор твита для удаления.
    :param current_user: Текущий пользователь, полученный из зависимостей.
    :return: Статус операции в формате JSON.

    Пример запроса с использованием curl:
    curl -i -X DELETE -H "Api-Key: 1wc65vc4v1fv" "http://localhost:5000/api/tweets/<tweet_id>"

    :raises HTTPException:
        - 403, если пользователь не аутентифицирован.
        - 404, если твит не найден или пользователь не имеет прав на его удаление.
    """

    result = await TweetDAO.delete_tweet(tweet_id=tweet_id, user_id=current_user.id)

    if not result:
        raise HTTPException(status_code=404, detail="Твит не найден или вы не имеете прав на его удаление")

    return {"result": True}


@main_router.delete("/users/{user_id}/follow")
async def delete_following(user_id: int, current_user: Users = Depends(get_current_user)) -> dict:
    """
    Пользователь может убрать подписку на другого пользователя.

    :param user_id: Идентификатор пользователя, от которого пользователь хочет отписаться.
    :param current_user: Текущий пользователь, который отписывается.
    :return: Статус операции в формате JSON.

    Пример запроса с использованием curl:
    curl -i -X DELETE -H "Api-Key: 1wc65vc4v1fv" "http://localhost:5000/api/users/<user_id>/follow"

    :raises HTTPException:
        - 403, если пользователь не аутентифицирован.
        - 404, если пользователь, от которого отписываются, не найден.
        - 409, если текущий пользователь не подписан на данного пользователя.
    """

    # Проверяем, существует ли пользователь, от которого отписываются
    followed_user = await UserDAO.find_one_or_none_by_id(user_id)

    if not followed_user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    # Проверяем, есть ли запись о подписке
    existing_follow = await FollowersDAO.find_one_or_none(
        follower_id=current_user.id,
        followed_id=user_id
    )

    if not existing_follow:
        raise HTTPException(status_code=409, detail="Вы не подписаны на этого пользователя")

    # Удаляем запись о подписке из таблицы followers
    await FollowersDAO.delete(follower_id=current_user.id, followed_id=user_id)

    return {"result": True}


@main_router.delete("/tweets/{tweet_id}/likes")
async def delete_like(tweet_id: int, current_user: Users = Depends(get_current_user)) -> dict:
    """
    Пользователь может убрать отметку «Нравится» с твита.
    :param tweet_id: Идентификатор твита.
    :param current_user: Текущий пользователь, полученный из зависимостей.
    :return: Статус операции в формате JSON.

    Пример запроса с использованием curl:
    curl -i -X DELETE -H "Api-Key: 1wc65vc4v1fv" "http://localhost:5000/api/tweets/<tweet_id>/likes"
    """

    result = await LikeDAO.delete_like(tweet_id=tweet_id, user_id=current_user.id)

    if not result:
        raise HTTPException(status_code=404, detail="Лайк не найден или вы не имеете прав на его удаление")

    return {"result": True}
