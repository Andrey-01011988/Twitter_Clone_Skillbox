import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import selectinload

from application.database import AsyncSessionApp, proj_engine
from application.models import BaseProj, Users
from application.api.tweets_routes import tweets_router
from application.api.medias_routes import medias_router
from application.api.users_routes import users_router
from application.api.dependencies import UserDAO

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):

    logger.info("Соединение с базой данных lifespan")
    async with proj_engine.begin() as conn:
        await conn.run_sync(BaseProj.metadata.create_all)
        logger.info("Создание таблиц, если необходимо, lifespan")
        async with AsyncSessionApp() as session:
            logger.info("Создание новой сессии для добавления тестового пользователя %s", session)
            try:
                test_user = await  UserDAO.find_one_or_none(
                    session=session,
                    options=[selectinload(Users.followers)],
                    api_key="test"
                )

                if test_user is None:
                    user = await UserDAO.add(session=session, name="Dan", api_key="test")
                    logger.info("Тестовый пользователь успешно добавлен %s", user)
                else:
                    logger.info("Тестовый пользователь уже существует")
            except Exception as e:
                logger.error("Ошибка при добавлении тестового пользователя: %s", e)
            finally:
                logger.info("Закрытие сессии %s", session)
                await session.close()
                logger.info("Сессия закрыта")

    yield

    logger.info("Закрытие всех соединений и освобождение ресурсов б/д lifespan")
    await proj_engine.dispose()


app_proj = FastAPI(lifespan=lifespan)

app_proj.include_router(users_router)
app_proj.include_router(tweets_router)
app_proj.include_router(medias_router)


@app_proj.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "result": False,
            "error_type": (
                f"HTTP {exc.status_code}"
                if isinstance(exc.status_code, int)
                else "Unknown Error"
            ),
            "error_message": (
                exc.detail if isinstance(exc.detail, str) else str(exc.detail)
            ),
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


@app_proj.get("/welcome")
async def hello():
    """
    curl -i GET "http://localhost:8000/"
    Для запуска в docker-compose:
    curl -i GET "http://localhost:5000/"
    :return: str
    """
    return f"Welcome"
