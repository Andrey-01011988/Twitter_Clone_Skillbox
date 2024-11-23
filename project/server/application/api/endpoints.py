from typing import List, Sequence, Optional

from fastapi import APIRouter, Depends, Header, HTTPException

from api.depencies import get_current_session, UserDAO, TweetDAO
from models import Users
from schemas import UserOut, TweetIn

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

@main_router.post("/tweets", response_model=TweetIn, status_code=201)
async def  add_tweet(tweet_media_ids: Optional[List[int]], tweet_data: str, api_key: str = Header(...), ) -> dict:
    """
    Добавляет новый твит от пользователя
    :param tweet_media_ids:
    :param tweet_data: Данные твита (текст и идентификаторы медиа)
    :param api_key:  ключ пользователя
    :return: Результат операции и идентификатор нового твита
    """
    user = await UserDAO.find_one_or_none(api_key=api_key)
    if user is None:
        raise HTTPException(status_code=403, detail="Доступ запрещен: неверный API ключ")

    new_tweet = await TweetDAO.add(author_id=user.id, text=tweet_data)

    return {"result": True, "tweet_id": new_tweet.id}
