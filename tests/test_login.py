import pytest
from httpx import BasicAuth

from server.auth import hash_password
from tests.utils import AsyncAPIClient, validate_uuid

pytestmark = pytest.mark.anyio
BASE_URL = "/login/"


class TestPost:
    async def test_login_success(self, url_factory, user_factory, client: AsyncAPIClient):
        user_data: dict = await user_factory(raw=True)
        await user_factory(**hash_password(user_data.copy()))
        url: str = url_factory()
        auth: BasicAuth = BasicAuth(username=user_data["username"], password=user_data["password"])

        response = await client.post(url=url, auth=auth)
        response_json: dict = response.json()

        assert response.status_code == 201
        assert validate_uuid(response_json["token"])

    async def test_login_fail_unauthorized(self, url_factory, client: AsyncAPIClient):
        url: str = url_factory()

        response = await client.post(url=url)

        assert response.status_code == 401

    async def test_login_fail_invalid_password(
        self, url_factory, user_factory, client: AsyncAPIClient
    ):
        user_data: dict = await user_factory(raw=True)
        await user_factory(**hash_password(user_data.copy()))
        url: str = url_factory()
        auth: BasicAuth = BasicAuth(username=user_data["username"], password="INVALID_PASSWORD")

        response = await client.post(url=url, auth=auth)

        assert response.status_code == 401
