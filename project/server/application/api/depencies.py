from application.crud import BaseDAO
from application.database import AsyncSessionApp
from application.models import Users, Tweets


# Назначение текущей сессии
async def get_current_session():
    current_session = AsyncSessionApp()
    try:
        yield current_session
    finally:
        await current_session.close()


class UserDAO(BaseDAO):
    model = Users


class TweetDAO(BaseDAO):
    model = Tweets
