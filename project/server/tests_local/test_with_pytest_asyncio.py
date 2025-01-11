import logging

import pytest
from httpx import AsyncClient, Response


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestUserAPI:

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
        headers = {"Api-Key": "test"}
        response: Response = await client.get("/api/users/me", headers=headers)
        logger.info(type(response))
        logger.info(response.json())
        assert response.status_code == 200
        assert isinstance(response.json(), dict)
        assert "user" in response.json()

# Запуск из консоли
# (ubuntuenv) uservm@uservm-VirtualBox:~/PycharmProjects/python_advanced_diploma/project/server$
# python -m pytest tests_local/test_with_pytest_asyncio.py -v --log-cli-level=INFO

# Если запускать из контейнера, то необходимо указать порт 5432 и имя контейнера вместо localhost
# (ubuntuenv) uservm@uservm-VirtualBox:~/PycharmProjects/python_advanced_diploma$ docker exec -it project_server_1 /bin/sh
# pytest -v tests_local/test_with_pytest_asyncio.py
