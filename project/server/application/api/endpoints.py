from datetime import datetime
from io import BytesIO
from typing import List, Sequence, Optional, Dict, Union, Any

from PIL import Image
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Request
from fastapi.responses import  StreamingResponse, JSONResponse
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from application.api.dependencies import get_current_session, UserDAO, TweetDAO, MediaDAO, LikeDAO, FollowersDAO, get_client_token, get_current_user
from application.models import Users, Tweets, Like
from application.schemas import UserOut, TweetIn, TweetOut, ErrorResponse, SimpleUserOut, UserIn


main_router = APIRouter(prefix="/api", tags=["API"])


# @main_router.get("/all_users", response_model=List[SimpleUserOut])
# async def get_all_users(session: AsyncSession = Depends(get_current_session)) -> List[Users]:
#     """
#     Выводит всех пользователей.
#
#     Этот эндпоинт возвращает список всех пользователей из базы данных.
#
#     Пример запроса:
#         curl -i GET "http://localhost:8000/api/all_users"
#
#     Для запуска в docker-compose:
#         curl -i GET "http://localhost:5000/api/all_users"
#
#     Аргументы:
#         session (AsyncSession): Асинхронная сессия SQLAlchemy.
#
#     Возвращает:
#         Список пользователей.
#     """
#     result = await UserDAO.find_all(session=session)
#     return result


@main_router.get("/all_users", response_model=List[SimpleUserOut])
async def get_all_users(session: AsyncSession = Depends(get_current_session)) -> Sequence[Users]:
    result = await session.execute(select(Users))
    return result.scalars().all()


@main_router.get("/tweets", response_model=Dict[str, Union[bool, List[TweetOut]]],
                 responses={403: {"model": ErrorResponse}, 500: {"model": ErrorResponse}})
async def get_users_tweets(request: Request) -> JSONResponse | dict[
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
    session = request.state.session  # Получаем сохраненную сессию
    try:
        # Получаем все твиты пользователя с подгрузкой связанных данных (автор, медиа и лайки)
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

    Пример запроса:
        curl -i -X GET -H "Api-Key: 1wc65vc4v1fv" "http://localhost:5000/api/users/me"
    """

    return {
        "result": True,
        "user": current_user.to_json()
    }


@main_router.get("/media/{media_id}")
async def get_media(media_id: int, session: AsyncSession = Depends(get_current_session)):
    """
    Получение медиа привязанного к твиту в виде изображения.

    Аргументы:
        media_id (int): Идентификатор медиа.
        session (AsyncSession): Асинхронная сессия SQLAlchemy.

    Возвращает:
        Изображение в формате, определяемом по содержимому.

    Пример запроса:
        curl -i -X GET "http://localhost:5000/api/media/1"
    """

    media = await MediaDAO.find_one_or_none_by_id(media_id, session=session)

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
async def get_user_info_by_id(user_id: int,
                              request: Request) -> JSONResponse | dict[
    str, bool | list[Any]] | Any:
    """
    Пользователь может получить информацию о произвольном профиле по его id.

    Аргументы:
        user_id (int): Идентификатор пользователя, информацию о котором необходимо получить.
        session (AsyncSession): Асинхронная сессия SQLAlchemy.

    Возвращает:
        Статус операции и информация о пользователе в формате JSON.

    Пример запроса с использованием curl:
    ```
    curl -i -X GET -H "Api-Key: 1wc65vc4v1fv" "http://localhost:5000/api/users/<user_id>"
    ```

    :raises HTTPException:
        - 403, если пользователь не аутентифицирован.
        - 404, если пользователь с указанным id не найден.
        - 500, если произошла внутренняя ошибка сервера.
    """
    session = request.state.session  # Получаем сохраненную сессию
    user_info_by_id = await UserDAO.find_one_or_none_by_id(
        user_id,
        session=session,
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


@main_router.post("/add_user", status_code=201)
async def add_one_user(user: UserIn, session: AsyncSession = Depends(get_current_session)) -> str:
    """
    Добавляет пользователя, возвращает его.

    Аргументы:
        user (UserIn): Данные нового пользователя.
        session (AsyncSession): Асинхронная сессия SQLAlchemy.

    Пример запроса:
    ```
    curl -X POST "http://localhost:8000/api/add_user" -H "Content-Type: application/json" -d '{"name": "Anon", "api_key": "1wc65vc4v1fv"}'
    ```

    Для запуска в docker-compose:
    ```
    curl -X POST "http://localhost:5000/api/add_user" -H "Content-Type: application/json" -d '{"name": "Dan", "api_key": "test"}'
    """

    new_user = await UserDAO.add(session=session, **user.dict())

    return f"User added: {new_user}\n"


@main_router.post("/tweets", status_code=201)
async def add_tweet(tweet: TweetIn, request: Request, current_user: Users = Depends(get_current_user)) -> dict:
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
    session = request.state.session  # Получаем сохраненную сессию
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


@main_router.post("/medias")
async def add_media(api_key: str = Depends(get_client_token),
                    file: UploadFile = File(...),
                    session: AsyncSession = Depends(get_current_session)) -> dict:
    """
    Эндпоинт для загрузки медиафайлов.

    Этот эндпоинт позволяет пользователям загружать медиафайлы (например, изображения) и
    связывать их с определенным твитом по его идентификатору.

    Аргументы:
        api_key (str): API ключ пользователя, необходимый для аутентификации.
        file (UploadFile): Загружаемый файл (изображение или другой медиафайл).
        session (AsyncSession): Асинхронная сессия SQLAlchemy.

    Возвращает:
        JSON-ответ с результатом операции и ID загруженного медиафайла.

    Пример запроса с использованием curl:
    ```
    curl -i -X POST -H "api-key: 1wc65vc4v1fv" -F "file=@/path/to/your/image.jpg" "http://localhost:5000/api/medias"
    ```

    :raises HTTPException:
        - 400, если произошла ошибка при загрузке файла или создании записи в базе данных.
    """

    try:
        file_body = await file.read()

        # Создание записи в базе данных
        new_media = await MediaDAO.add(session=session, file_body=file_body, file_name=file.filename)

        return {"result": True, "media_id": new_media.id}

    except Exception as e:
        raise HTTPException(status_code=500, detail="Ошибка при загрузке файла")


@main_router.post("/tweets/{tweet_id}/likes")
async def add_like(tweet_id: int,
                    request: Request,
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
    session = request.state.session  # Получаем сохраненную сессию
    tweet = await TweetDAO.find_one_or_none_by_id(tweet_id, session=session)

    if not tweet:
        raise HTTPException(status_code=404, detail="Твит не найден")

    await LikeDAO.add(session=session, tweet_id=tweet_id, user_id=current_user.id)

    return {"result": True}


@main_router.post("/users/{user_id}/follow")
async def follow_user(user_id: int,
                        request: Request,
                        current_user: Users = Depends(get_current_user)) -> dict:
    """
    Пользователь может зафоловить другого пользователя.

    Аргументы:
        user_id (int): Пользователь, которого фолловят.
        current_user (Users): Пользователь, который фолловит.
        session (AsyncSession): Асинхронная сессия SQLAlchemy.

    Возвращает:
        Статус операции в формате JSON.

    Пример запроса с использованием curl:
    ```
    curl -X POST -H "Api-Key: 1wc65vc4v1fv" http://localhost:5000/api/users/<user_id>/follow
    ```

    :raises HTTPException:
        - 404, если указанный пользователь не найден.
        - 409, если пользователь уже подписан на данного пользователя.
    """
    session = request.state.session  # Получаем сохраненную сессию
    # Проверяем, существует ли пользователь, на которого подписываются
    followed_user = await UserDAO.find_one_or_none_by_id(user_id, session=session)

    if not followed_user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    # Проверяем, не подписан ли текущий пользователь уже на данного пользователя
    existing_follow = await FollowersDAO.find_one_or_none(
        follower_id=user_id,
        followed_id=current_user.id,
        session=session
    )

    if existing_follow:
        raise HTTPException(status_code=409, detail="Вы уже подписаны на этого пользователя")

    # Добавляем запись о подписке в таблицу followers
    await FollowersDAO.add_followers(session=session, follower_id=user_id, followed_id=current_user.id)

    return {"result": True}


@main_router.delete("/tweets/{tweet_id}")
async def delete_tweet(tweet_id: int,
                        request: Request,
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
    session = request.state.session  # Получаем сохраненную сессию
    # Находим твит по идентификатору
    current_tweet = await TweetDAO.find_one_or_none_by_id(tweet_id, session=session)

    # Проверяем, существует ли твит и принадлежит ли он текущему пользователю
    if not current_tweet or current_tweet.author_id != current_user.id:
        raise HTTPException(status_code=404, detail="Твит не найден или вы не имеете прав на его удаление")

    # Удаляем твит
    await TweetDAO.delete(session=session, instance=current_tweet)

    return {"result": True}


@main_router.delete("/users/{user_id}/follow")
async def delete_following(user_id: int,
                            request: Request,
                            current_user: Users = Depends(get_current_user)) -> dict:
    """
    Пользователь может убрать подписку на другого пользователя.

    Аргументы:
        user_id (int): Идентификатор пользователя, от которого пользователь хочет отписаться.
        current_user (Users): Текущий пользователь, который отписывается.
        session (AsyncSession): Асинхронная сессия SQLAlchemy.

    Возвращает:
        Статус операции в формате JSON.

    Пример запроса с использованием curl:
    ```
    curl -i -X DELETE -H "Api-Key: 1wc65vc4v1fv" "http://localhost:5000/api/users/<user_id>/follow"
    ```

    :raises HTTPException:
        - 403, если пользователь не аутентифицирован.
        - 404, если пользователь, от которого отписываются, не найден.
        - 409, если текущий пользователь не подписан на данного пользователя.
    """
    session = request.state.session  # Получаем сохраненную сессию
    # Проверяем, существует ли пользователь, от которого отписываются
    followed_user = await UserDAO.find_one_or_none_by_id(user_id, session=session)

    if not followed_user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    # Проверяем, есть ли запись о подписке
    existing_follow = await FollowersDAO.find_one_or_none(
        follower_id=user_id,
        followed_id=current_user.id,
        session=session
    )

    if not existing_follow:
        raise HTTPException(status_code=409, detail="Вы не подписаны на этого пользователя")

    # Удаляем запись о подписке из таблицы followers
    await FollowersDAO.delete_followers(session=session, follower_id=user_id, followed_id=current_user.id)

    return {"result": True}


@main_router.delete("/tweets/{tweet_id}/likes")
async def delete_like(tweet_id: int,
                        request: Request,
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
    session = request.state.session  # Получаем сохраненную сессию
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

