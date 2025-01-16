import logging

import pytest
from httpx import AsyncClient, Response
from fastapi import status


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestMediaAPI:

    @classmethod
    def setup_class(cls):
        cls.headers = {"Api-Key": "test"}
        cls.invalid_headers = {"Api-Key": "invalid_key"}
        cls.test_media_id = 1  # Замените на ID существующего медиа для тестирования
        cls.invalid_media_id = 999  # Предполагается, что такого медиа нет


    @pytest.mark.asyncio
    async def test_get_media(self, client: AsyncClient):
        """Проверяет успешное получение медиа файла по его ID. Ожидается статус код 200 и правильный тип контента."""
        # import pdb; pdb.set_trace()
        response: Response = await client.get(f"/api/media/{self.test_media_id}")
        logger.info(response.headers)

        assert response.status_code == status.HTTP_200_OK
        assert "image/jpeg" in response.headers['content-type']


    @pytest.mark.asyncio
    async def test_get_invalid_media(self, client: AsyncClient):
        """
        Проверяет обработку ошибки при запросе несуществующего медиа файла (ID 999).
        Ожидается статус код 404 и сообщение об ошибке.
        """
        response: Response = await client.get(f"/api/media/{self.invalid_media_id}")
        logger.info(response.json())

        assert response.status_code == status.HTTP_404_NOT_FOUND  # Ожидаем ошибку 404 для несуществующего медиа
        assert response.json().get("error_message") == "Media not found"


    @pytest.mark.asyncio
    async def test_add_media(self, client: AsyncClient):
        """
        Проверяет успешное добавление нового медиа файла с корректными данными.
        Ожидается статус код 200 и наличие ключа "media_id" в ответе.
        """
        media_file = {
            "file": ("test_image.png", b"fake_image_data", "image/png")
        }

        response: Response = await client.post("/api/medias", files=media_file, headers=self.headers)

        logger.info(response.json())

        assert response.status_code == status.HTTP_200_OK
        assert response.json().get("result") is True
        assert "media_id" in response.json()


    @pytest.mark.asyncio
    async def test_add_media_with_invalid_api_key(self, client: AsyncClient):
        """
        Проверяет обработку ошибки при попытке добавить медиа файл с неверным API-ключом.
        Ожидается статус код 403, проверяется соответствие сообщения об ошибке.
        """
        media_file = {
            "file": ("test_image.png", b"fake_image_data", "image/png")
        }

        response: Response = await client.post("/api/medias", files=media_file, headers=self.invalid_headers)

        logger.info(response.json())

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.json().get("error_message") == "Доступ запрещен: неверный API ключ"

    @pytest.mark.asyncio
    async def test_add_media_without_file(self, client: AsyncClient):
        """
        Проверяет обработку ошибки при попытке добавить медиа файл без указания файла.
        Ожидается статус код 422 (Unprocessable Entity).
        """
        response: Response = await client.post("/api/medias", headers=self.headers)  # Без файла

        logger.info(response.json())

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY  # Ожидаем ошибку 422 для отсутствующего файла


# Запуск из консоли
# (ubuntuenv) uservm@uservm-VirtualBox:~/PycharmProjects/python_advanced_diploma/project/server$
# python -m pytest tests_local/test_medias_routes.py -v --log-cli-level=INFO