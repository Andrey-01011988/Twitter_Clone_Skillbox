from datetime import datetime
from typing import List, Sequence, Optional

from black import timezone
from fastapi import APIRouter, Depends, Header, HTTPException

from api.depencies import get_current_session, UserDAO, TweetDAO
from models import Users, Tweets
from schemas import UserOut, TweetIn, TweetOut
from sqlalchemy.exc import SQLAlchemyError


main_router = APIRouter(prefix="/api", tags=["API"], dependencies=[Depends(get_current_session)])


@main_router.get("/users", response_model=List[UserOut])
async def get_all_users() -> Sequence[Users]:
    """
        Выводит всех пользователей
        curl -i GET "http://localhost:8000/api/users"
        Для запуска в docker-compose:
        curl -i GET "http://localhost:5000/api/users"
    """

    result = await UserDAO.find_all()

    return result


@main_router.get("/tweets", response_model=List[TweetOut])
async def get_users_tweets(api_key: str = Header(...)) -> dict:
    """
    Пользователь может получить ленту с твитами.
    curl -i -H "api-key: 1wc65vc4v1fv" GET "http://localhost:5000/api/tweets"
    :param api_key:
    :return:
    """
    user = await UserDAO.find_one_or_none(api_key=api_key)
    if user is None:
        raise HTTPException(status_code=403, detail="Доступ запрещен: неверный API ключ")

    all_tweets = await TweetDAO.find_all(author_id=user.id)

    # Преобразование timestamp в строку
    for tweet in all_tweets:
        tweet.timestamp = tweet.timestamp.isoformat()  # Преобразование datetime в строку

    return all_tweets


# @main_router.post("/tweets", response_model=TweetIn, status_code=201)
@main_router.post("/tweets", status_code=201)
async def  add_tweet(tweet: TweetIn, api_key: str = Header(...) ) -> dict:
    """
    Добавляет новый твит от пользователя
    curl -iX POST "http://localhost:5000/api/tweets" -H "api-key: 1wc65vc4v1fv" -H "Content-Type: application/json" -d '{"tweet_media_ids": [], "text": "Привет"}'
    :param tweet:
    :param api_key:  ключ пользователя
    :return: Результат операции и идентификатор нового твита
    """
    user = await UserDAO.find_one_or_none(api_key=api_key)
    if user is None:
        raise HTTPException(status_code=403, detail="Доступ запрещен: неверный API ключ")

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
