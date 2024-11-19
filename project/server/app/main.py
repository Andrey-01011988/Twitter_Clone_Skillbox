from contextlib import asynccontextmanager
from typing import List, Sequence

from fastapi import FastAPI, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from project.server.app import schemas, models
from project.server.app.database import AsyncSessionApp, proj_engine
from project.server.app.models import BaseProj


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


@app_proj.get("/users", response_model=List[schemas.UserOut])
async def get_all_users(current_session: AsyncSession = Depends(get_current_session)) -> Sequence[models.Users]:
    """
    Выводит всех пользователей
    curl -iX GET "http://localhost:8000/users"
    """

    users = models.Users

    result = await current_session.execute(select(users))

    return result.scalars().all()


@app_proj.post("/user", response_model=schemas.UserOut, status_code=201)
async def add_one_user(user: schemas.UserIn, current_session: AsyncSession = Depends(get_current_session)) -> models.Users:
    """
    Добавляет пользователя, возвращает его
    curl -X POST "http://localhost:8000/user" -H "Content-Type: application/json" -d '{"name": "Anon", "api_key": "1wc65vc4v1fv"}'
    """

    new_user = models.Users(**dict(user))

    async with current_session.begin():
        current_session.add(new_user)
    return new_user
