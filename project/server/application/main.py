from contextlib import asynccontextmanager
# from typing import List, Sequence

from fastapi import FastAPI, HTTPException, Request
# from sqlalchemy import select
# from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse

from database import AsyncSessionApp, proj_engine
from models import BaseProj
# from api.depencies import get_current_session
from api.endpoints import main_router
# from schemas import UserOut, UserIn


@asynccontextmanager
async def lifespan(app: FastAPI):
    current_session = AsyncSessionApp()
    async with proj_engine.begin() as conn:
        await conn.run_sync(BaseProj.metadata.create_all)
        yield
    await current_session.close()
    await proj_engine.dispose()

app_proj = FastAPI(lifespan=lifespan)

app_proj.include_router(main_router)


@app_proj.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "result": False,
            "error_type": exc.detail if isinstance(exc.detail, str) else "Unknown Error",
            "error_message": exc.detail if isinstance(exc.detail, str) else str(exc.detail),
        },
    )


@app_proj.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "result": False,
            "error_type": "Internal Server Error",
            "error_message": str(exc),
        },
    )


# Назначение текущей сессии
# async def get_current_session():
#     current_session = AsyncSessionApp()
#     try:
#         yield current_session
#     finally:
#         await current_session.close()
app_proj.mount("/static", StaticFiles(directory="/app/static"), name="static")
app_proj.mount("/js", StaticFiles(directory="/app/static/js"), name="js")
app_proj.mount("/css", StaticFiles(directory="/app/static/css"), name="css")

@app_proj.get("/index")
def read_main():
    return FileResponse("/app/templates/index_fastAPI.html")


@app_proj.get("/welcome")
async def hello():
    """
    curl -i GET "http://localhost:8000/"
    Для запуска в docker-compose:
    curl -i GET "http://localhost:5000/"
    :return: str
    """
    return f'Welcome'


# @app_proj.get("/users", response_model=List[UserOut])
# async def get_all_users(current_session: AsyncSession = Depends(get_current_session)) -> Sequence[Users]:
#     """
#     Выводит всех пользователей
#     curl -i GET "http://localhost:8000/users"
#     Для запуска в docker-compose:
#     curl -i GET "http://localhost:5000/users"
#     """
#
#     users = Users
#
#     result = await current_session.execute(select(users))
#
#     return result.scalars().all()
#
#
# @app_proj.post("/user", response_model=UserOut, status_code=201)
# async def add_one_user(user: UserIn, current_session: AsyncSession = Depends(get_current_session)) -> str:
#     """
#     Добавляет пользователя, возвращает его
#     curl -X POST "http://localhost:8000/user" -H "Content-Type: application/json" -d '{"name": "Anon", "api_key": "1wc65vc4v1fv"}'
#     Для запуска в docker-compose:
#     curl -X POST "http://localhost:5000/user" -H "Content-Type: application/json" -d '{"name": "Bob", "api_key": "541df411vfv45"}'
#     """
#
#     new_user = Users(**dict(user))
#
#     async with current_session.begin():
#         current_session.add(new_user)
#     return f"User added: {new_user}\n"
