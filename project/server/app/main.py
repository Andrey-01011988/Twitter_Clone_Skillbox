from contextlib import asynccontextmanager
from typing import List, Sequence, Tuple

from fastapi import FastAPI, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


from database import AsyncSessionApp, proj_engine
from models import BaseProj, Users
from schemas import UserOut, UserIn


@asynccontextmanager
async def lifespan(app: FastAPI):
    current_session = AsyncSessionApp()
    async with proj_engine.begin() as conn:
        await conn.run_sync(BaseProj.metadata.create_all)
        yield
    await current_session.close()
    await proj_engine.dispose()

app_proj = FastAPI(lifespan=lifespan)


# Назначение текущей сессии
async def get_current_session():
    current_session = AsyncSessionApp()
    try:
        yield current_session
    finally:
        await current_session.close()


@app_proj.get('/')
async def hello():
    """
    curl -i GET "http://localhost:8000/"
    Для запуска в docker-compose:
    curl -i GET "http://localhost:5000/"
    :return: str
    """
    return f'Welcome'


@app_proj.get("/users", response_model=List[UserOut])
async def get_all_users(current_session: AsyncSession = Depends(get_current_session)) -> Sequence[Users]:
    """
    Выводит всех пользователей
    curl -i GET "http://localhost:8000/users"
    Для запуска в docker-compose:
    curl -i GET "http://localhost:5000/users"
    """

    users = Users

    result = await current_session.execute(select(users))

    return result.scalars().all()


@app_proj.post("/user", response_model=UserOut, status_code=201)
async def add_one_user(user: UserIn, current_session: AsyncSession = Depends(get_current_session)) -> str:
    """
    Добавляет пользователя, возвращает его
    curl -X POST "http://localhost:8000/user" -H "Content-Type: application/json" -d '{"name": "Anon", "api_key": "1wc65vc4v1fv"}'
    Для запуска в docker-compose:
    curl -X POST "http://localhost:5000/user" -H "Content-Type: application/json" -d '{"name": "Bob", "api_key": "541df411vfv45"}'
    """

    new_user = Users(**dict(user))

    async with current_session.begin():
        current_session.add(new_user)
    return f"User added: {new_user}\n"
