import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from sqlalchemy.orm import selectinload
from fastapi.responses import JSONResponse

from application.database import AsyncSessionApp, proj_engine
from application.models import BaseProj, Users
from application.api.dependencies import UserDAO, get_current_session
from application.api.endpoints import main_router


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


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
    """
    Middleware для проверки аутентификации пользователя по API ключу.

    Этот middleware проверяет наличие API ключа в заголовках запроса и пытается найти
    соответствующего пользователя в базе данных. Если пользователь найден, он сохраняется
    в атрибуте состояния запроса для дальнейшего использования в обработчиках.

    Аргументы:
        request (Request): Объект запроса FastAPI, содержащий информацию о текущем запросе.
        call_next (Callable): Функция, которая принимает запрос и возвращает ответ.
                              Используется для передачи управления следующему обработчику.

    Возвращает:
        Response: Ответ FastAPI, полученный от следующего обработчика.

    Исключения:
        Возвращает JSONResponse с кодом 404 и сообщением {"error": "User not found"},
        если пользователь с указанным API ключом не найден в базе данных.

    Пример использования:
        Этот middleware автоматически применяется ко всем запросам, начинающимся с "/api",
        за исключением тех, которые указаны в списке исключений. Например:

        - Запросы к "/api/medias/" не требуют проверки пользователя.
        - Запросы к "/api/all_users" также не требуют проверки.

    Примечание:
        Убедитесь, что функция `get_current_session` правильно настроена для получения
        асинхронной сессии SQLAlchemy, чтобы middleware мог корректно взаимодействовать
        с базой данных.
    """
    logger.info(f"Обрабатываем путь: {request.url.path}")
    # Определяем список префиксов для исключения
    excluded_prefixes = ["/api/medias/", "/api/all_users", "/api/add_user", "/api/media"]
    logger.info("Сравниваем с исключенными префиксами: %s", excluded_prefixes)

    # Проверяем, начинается ли путь с "/api" и не начинается ли он с любого из исключенных префиксов
    if request.url.path.startswith("/api") and not any(
            request.url.path.startswith(prefix) for prefix in excluded_prefixes):
        async for session in get_current_session():
            logger.info("Путь не исключен из проверки.")
            request.state.session = session  # Сохраняем сессию в атрибуте запроса
            api_key = request.headers.get("Api-Key", "test")

            user = await UserDAO.find_one_or_none(
                session=session,
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
    else:
        logger.info("Путь исключен из проверки.")

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
