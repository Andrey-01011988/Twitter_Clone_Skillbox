import logging

import pytest
from httpx import AsyncClient, Response
from fastapi import status


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestTweetAPI:

    @classmethod
    def setup_class(cls):
        cls.headers = {"Api-Key": "test"}
        cls.invalid_headers = {"Api-Key": "invalid_key"}
        cls.test_tweet_id = 1
        cls.delete_like_tweet_id = 3
        cls.invalid_tweet_id = 999


    @pytest.mark.asyncio
    async def test_get_all_tweets(self, client: AsyncClient):
        """
        Проверяет успешное получение всех твитов. Ожидается статус код 200 и наличие ключа "tweets" в ответе
        """
        response: Response = await client.get("/api/tweets")

        logger.info(response.json())
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.json(), dict)
        assert "tweets" in response.json()


    @pytest.mark.asyncio
    async def test_add_tweet(self, client: AsyncClient):
        """
        Проверяет добавление нового твита с корректными данными. Ожидается статус код 201 и наличие ключа "tweet_id" в ответе.
        """
        tweet_data = {
            "tweet_data": "This is a test tweet",
            "tweet_media_ids": []  # Можно добавить ID медиафайлов, если нужно
        }

        response: Response = await client.post("/api/tweets", json=tweet_data, headers=self.headers)

        logger.info(response.json())

        assert response.status_code == status.HTTP_201_CREATED
        assert response.json().get("result") is True
        assert "tweet_id" in response.json()


    @pytest.mark.asyncio
    async def test_add_tweet_with_invalid_api_key(self, client: AsyncClient):
        """
        Проверяет добавление твита с неверным API-ключом. Ожидается статус код 404 (пользователь не найден).
        """
        tweet_data = {
            "tweet_data": "This is a test tweet",
            "tweet_media_ids": []
        }

        response: Response = await client.post("/api/tweets", json=tweet_data, headers=self.invalid_headers)

        logger.info(response.json())

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.json().get("error_message") == "Доступ запрещен: неверный API ключ"


    @pytest.mark.asyncio
    async def test_add_like(self, client: AsyncClient):
        """
        Проверяет успешное добавление лайка к существующему твиту. Ожидается статус код 200.
        """
        response: Response = await client.post(f"/api/tweets/{self.test_tweet_id}/likes", headers=self.headers)

        logger.info(response.json())

        assert response.status_code == status.HTTP_200_OK
        assert response.json().get("result") is True


    @pytest.mark.asyncio
    async def test_add_like_to_invalid_tweet(self, client: AsyncClient):
        """
        Проверяет добавление лайка к несуществующему твиту. Ожидается статус код 404.
        """
        response: Response = await client.post(f"/api/tweets/{self.invalid_tweet_id}/likes", headers=self.headers)

        logger.info(response.json())

        assert response.status_code == status.HTTP_404_NOT_FOUND


    @pytest.mark.asyncio
    async def test_delete_tweet(self, client: AsyncClient):
        """
        Проверяет успешное удаление существующего твита. Ожидается статус код 200.
        """
        response: Response = await client.delete(f"/api/tweets/{self.test_tweet_id}", headers=self.headers)

        logger.info(response.json())

        assert response.status_code == status.HTTP_200_OK
        assert response.json().get("result") is True


    @pytest.mark.asyncio
    async def test_delete_invalid_tweet(self, client: AsyncClient):
        """
        Проверяет удаление несуществующего твита. Ожидается статус код 404.
        """
        response: Response = await client.delete(f"/api/tweets/{self.invalid_tweet_id}", headers=self.headers)

        logger.info(response.json())

        assert response.status_code == status.HTTP_404_NOT_FOUND


    @pytest.mark.asyncio
    async def test_delete_like(self, client: AsyncClient):
        """
        Проверяет успешное удаление лайка от существующего твита. Ожидается статус код 200.
        """
        # Предполагается, что пользователь уже поставил лайк на этот твит
        response: Response = await client.delete(f"/api/tweets/{self.delete_like_tweet_id}/likes", headers=self.headers)

        logger.info(response.json())

        assert response.status_code == status.HTTP_200_OK
        assert response.json().get("result") is True


    @pytest.mark.asyncio
    async def test_delete_like_for_invalid_tweet(self, client: AsyncClient):
        """
        Проверяет удаление лайка от несуществующего твита. Ожидается статус код 404.
        """
        response: Response = await client.delete(f"/api/tweets/{self.invalid_tweet_id}/likes", headers=self.headers)

        logger.info(response.json())

        assert response.status_code == status.HTTP_404_NOT_FOUND


# Запуск из консоли
# (ubuntuenv) uservm@uservm-VirtualBox:~/PycharmProjects/python_advanced_diploma/project/server$
# python -m pytest tests_local/test_tweets_routes.py -v --log-cli-level=INFO

# Если запускать из контейнера, то необходимо указать порт 5432 и имя контейнера вместо localhost
# (ubuntuenv) uservm@uservm-VirtualBox:~/PycharmProjects/python_advanced_diploma$ docker exec -it project_server_1 /bin/sh
# pytest -v tests_local/test_tweets_routes.py
