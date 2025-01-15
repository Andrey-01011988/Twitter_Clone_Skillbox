import logging

import pytest
from httpx import AsyncClient, Response
from fastapi import status


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestUserAPI:

    @classmethod
    def setup_class(cls):
        cls.headers = {"Api-Key": "test"}
        cls.invalid_headers = {"Api-Key": "invalid_key"}
        cls.test_user_id = 2
        cls.invalid_user_id = 999


    @pytest.mark.asyncio()
    async def test_get_users_information(self, client: AsyncClient):
        response: Response = await client.get("/api/all_users")
        logger.info(type(response))
        logger.info(response.json())
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        assert len(response.json()) > 0


    @pytest.mark.asyncio()
    async def test_get_user_me(self, client: AsyncClient):
        response: Response = await client.get("/api/users/me", headers=self.headers)
        logger.info(type(response))
        logger.info(response.json())
        assert response.status_code == 200
        assert isinstance(response.json(), dict)
        assert "user" in response.json()


    @pytest.mark.asyncio()
    async def test_get_user_info_by_id(self, client: AsyncClient):
        response: Response = await client.get(f"/api/users/{self.test_user_id}")
        logger.info(type(response))
        logger.info(response.json())
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.json(), dict)
        assert "user" in response.json()


    @pytest.mark.asyncio()
    async def test_add_one_user(self, client: AsyncClient):
        new_user_data = {
            "name": "new_user",
            "api_key": "test_api_key",
        }
        response: Response = await client.post("/api/add_user", json=new_user_data)
        logger.info(type(response))
        logger.info(response.text)
        assert response.status_code == status.HTTP_201_CREATED
        assert "User added:" in response.text


    @pytest.mark.asyncio()
    async def test_follow_user(self, client: AsyncClient):
        follow_user_id = 3  # Замените на ID пользователя, на которого хотите подписаться

        response: Response = await client.post(f"/api/users/{follow_user_id}/follow", headers=self.headers)

        logger.info(type(response))
        logger.info(response.json())

        assert response.status_code == status.HTTP_200_OK
        assert response.json().get("result") is True


    @pytest.mark.asyncio()
    async def test_delete_following(self, client: AsyncClient):
        unfollow_user_id = 2  # Замените на ID пользователя, от которого хотите отписаться

        response: Response = await client.delete(f"/api/users/{unfollow_user_id}/follow", headers=self.headers)

        logger.info(type(response))
        logger.info(response.json())

        assert response.status_code == status.HTTP_200_OK
        assert response.json().get("result") is True


    @pytest.mark.asyncio()
    async def test_add_one_user_with_missing_fields(self, client: AsyncClient):
        new_user_data = {
            "name": "new_user"
            # api_key отсутствует
        }

        response: Response = await client.post("/api/add_user", json=new_user_data)

        logger.info(type(response))
        logger.info(response.json())

        assert response.status_code == 422  # Unprocessable Entity
        assert not response.json().get("result")


    @pytest.mark.asyncio()
    async def test_follow_user_with_invalid_id(self, client: AsyncClient):
        follow_user_id = self.invalid_user_id  # Используем несуществующий ID

        response: Response = await client.post(f"/api/users/{follow_user_id}/follow", headers=self.headers)

        logger.info(type(response))
        logger.info(response.json())

        assert response.status_code == 404
        assert not response.json().get("result")
        assert response.json().get("error_message") == "Пользователь не найден"

    @pytest.mark.asyncio()
    async def test_follow_user_with_invalid_api_key(self, client: AsyncClient):
        follow_user_id = self.test_user_id  # Используем существующий ID

        response: Response = await client.post(f"/api/users/{follow_user_id}/follow", headers=self.invalid_headers)

        logger.info(type(response))
        logger.info(response.json())

        assert response.status_code == 403  # Forbidden (если обработчик проверяет ключи)

    @pytest.mark.asyncio()
    async def test_delete_following_with_invalid_api_key(self, client: AsyncClient):
        unfollow_user_id = self.test_user_id  # Используем существующий ID

        response: Response = await client.delete(f"/api/users/{unfollow_user_id}/follow", headers=self.invalid_headers)

        logger.info(type(response))
        logger.info(response.json())

        assert response.status_code == 403  # Forbidden (если обработчик проверяет ключи)

# Запуск из консоли
# (ubuntuenv) uservm@uservm-VirtualBox:~/PycharmProjects/python_advanced_diploma/project/server$
# python -m pytest tests_local/test_users_routes.py -v --log-cli-level=INFO

# Если запускать из контейнера, то необходимо указать порт 5432 и имя контейнера вместо localhost
# (ubuntuenv) uservm@uservm-VirtualBox:~/PycharmProjects/python_advanced_diploma$ docker exec -it project_server_1 /bin/sh
# pytest -v tests_local/test_users_routes.py
