import logging
from io import BytesIO

from PIL import Image
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import StreamingResponse

from application.api.dependencies import get_current_session, MediaDAO, get_client_token

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


medias_router = APIRouter(prefix="/api", tags=["Media"])


@medias_router.get("/media/{media_id}")
async def get_media(
    media_id: int, session: AsyncSession = Depends(get_current_session)
):
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
        content_type = (
            f"image/{image.format.lower()}"  # Получаем тип контента в нижнем регистре
        )

        # Сбрасываем указатель потока на начало
        image_stream.seek(0)

        return StreamingResponse(image_stream, media_type=content_type)

    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid image data")


@medias_router.post("/medias")
async def add_media(
    api_key: str = Depends(get_client_token),
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_current_session),
) -> dict:
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
        new_media = await MediaDAO.add(
            session=session, file_body=file_body, file_name=file.filename
        )

        return {"result": True, "media_id": new_media.id}

    except Exception as e:
        raise HTTPException(status_code=500, detail="Ошибка при загрузке файла")
