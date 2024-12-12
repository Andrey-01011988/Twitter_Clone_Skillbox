from contextlib import asynccontextmanager
# from typing import List, Sequence

from fastapi import FastAPI, HTTPException, Request
from sqlalchemy.orm import selectinload

# from sqlalchemy.ext.asyncio import AsyncSession
# from starlette.responses import FileResponse
# from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse

from database import AsyncSessionApp, proj_engine
from models import BaseProj, Users
from api.dependencies import UserDAO
from api.endpoints import main_router


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


@app_proj.middleware("http")
async def check_user_middleware(request: Request, call_next):
    # Определяем список префиксов для исключения
    excluded_prefixes = ["/api/medias/", "/api/all_users", "/api/add_user", "/api/media"]
    # Проверяем, начинается ли путь с "/api" и не начинается ли он с любого из исключенных префиксов
    if request.url.path.startswith("/api") and not any(request.url.path.startswith(prefix) for prefix in excluded_prefixes):
        api_key = request.headers.get("Api-Key", "test")
        user = await UserDAO.find_one_or_none(
            options=[
                selectinload(Users.followers),
                selectinload(Users.following)
            ],
            api_key=api_key
        )
        if not user:
            return JSONResponse(status_code=404, content={"error": "User not found"})

        # Сохраняем пользователя в атрибуте запроса
        request.state.current_user = user

    response = await call_next(request)  # Передаем управление следующему обработчику
    return response


@app_proj.get("/welcome")
async def hello():
    """
    curl -i GET "http://localhost:8000/"
    Для запуска в docker-compose:
    curl -i GET "http://localhost:5000/"
    :return: str
    """
    return f'Welcome'
