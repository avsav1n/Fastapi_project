from math import ceil

import pytest

from server.config import VALUES_ON_PAGE
from server.models import User
from tests.utils import AsyncAPIClient

pytestmark = pytest.mark.anyio
BASE_URL = "/user/"


class TestGetList:
    async def test_get_success(self, url_factory, user_factory, client: AsyncAPIClient):
        await user_factory(VALUES_ON_PAGE)
        url: str = url_factory()

        response = await client.get(url=url)
        response_json: dict[str, str | int | list] = response.json()

        assert response.status_code == 200
        assert isinstance(response_json, dict)
        assert isinstance(response_json["results"], list)
        assert len(response_json["results"]) == VALUES_ON_PAGE
        assert response_json["quantity"] >= VALUES_ON_PAGE

    async def test_get_fail_invalid_first_page(self, url_factory, client: AsyncAPIClient):
        invalid_page = -5
        url: str = url_factory(page=invalid_page)

        response = await client.get(url=url)

        assert response.status_code == 422

    async def test_get_success_invalid_last_page(
        self, url_factory, user_factory, client: AsyncAPIClient
    ):
        await user_factory(VALUES_ON_PAGE + 1)
        arrange_response = await client.get(url=url_factory())
        quantity_in_database: int = arrange_response.json()["quantity"]
        last_page: int = ceil(quantity_in_database / VALUES_ON_PAGE)
        invalid_page: int = last_page + 10
        url: str = url_factory(page=invalid_page)

        response = await client.get(url=url)
        response_json: dict[str, str | int | list] = response.json()

        assert response.status_code == 200
        assert response_json["quantity"] >= VALUES_ON_PAGE
        assert response_json["current_page"] == last_page
        assert response_json["previous"].startswith("http://")
        assert response_json["next"] is None

    async def test_get_success_search_no_results(
        self, url_factory, user_factory, client: AsyncAPIClient
    ):
        await user_factory(VALUES_ON_PAGE)
        search_value: str = "random_value_123"
        url: str = url_factory(search=search_value.upper())

        response = await client.get(url=url)
        response_json: dict[str, str | int | list] = response.json()

        assert response.status_code == 200
        assert len(response_json["results"]) == 0
        assert response_json["quantity"] == 0

    async def test_get_success_search(self, url_factory, user_factory, client: AsyncAPIClient):
        user: User = await user_factory()
        search_value: str = user.username[1:-1]
        url: str = url_factory(search=search_value.upper())

        response = await client.get(url=url)
        response_json: dict[str, str | int | list] = response.json()

        assert response.status_code == 200
        assert len(response_json["results"]) == 1
        assert user.as_dict == response_json["results"][0]
        assert response_json["quantity"] == 1

    async def test_get_success_order_by_asc(
        self, url_factory, user_factory, client: AsyncAPIClient
    ):
        await user_factory(VALUES_ON_PAGE)
        url: str = url_factory(order_by="id")

        response = await client.get(url=url)
        response_json: dict[str, str | int | list] = response.json()
        sorted_results: list[dict] = sorted(response_json["results"], key=lambda x: x["id"])

        assert response.status_code == 200
        assert sorted_results == response_json["results"]

    async def test_get_success_order_by_desc(
        self, url_factory, user_factory, client: AsyncAPIClient
    ):
        await user_factory(VALUES_ON_PAGE)
        url: str = url_factory(order_by="-id")

        response = await client.get(url=url)
        response_json: dict[str, str | int | list] = response.json()
        sorted_results: list[dict] = sorted(
            response_json["results"], key=lambda x: x["id"], reverse=True
        )

        assert response.status_code == 200
        assert sorted_results == response_json["results"]


class TestGetDetail:
    async def test_get_success(self, url_factory, user_factory, client: AsyncAPIClient):
        user: User = await user_factory()
        url: str = url_factory(id=user.id)

        response = await client.get(url=url)
        response_json: dict[str, str | int] = response.json()

        assert response.status_code == 200
        assert user.as_dict == response_json

    async def test_get_success_client(self, url_factory, client: AsyncAPIClient):
        url: str = url_factory(id=client.admin.id)

        response = await client.get(url=url)
        response_json: dict[str, str | int] = response.json()

        assert response.status_code == 200
        assert client.admin.as_dict == response_json

    async def test_get_fail_no_results(self, url_factory, client: AsyncAPIClient):
        url: str = url_factory(id="-1")

        response = await client.get(url=url)

        assert response.status_code == 400


class TestPost:
    async def test_post_success(self, url_factory, user_factory, client: AsyncAPIClient):
        user_data: dict = await user_factory(raw=True)
        url: str = url_factory()

        response = await client.post(url=url, json=user_data)
        response_json: dict[str, str | int] = response.json()

        assert response.status_code == 201
        assert user_data["username"] == response_json["username"]

    async def test_post_fail_simple_password(
        self, url_factory, user_factory, client: AsyncAPIClient
    ):
        user_data: dict = await user_factory(raw=True, password="simple_password")
        url: str = url_factory()

        response = await client.post(url=url, json=user_data)

        assert response.status_code == 422

    async def test_post_fail_no_username(self, url_factory, user_factory, client: AsyncAPIClient):
        user_data: dict = await user_factory(raw=True)
        user_data.pop("username")
        url: str = url_factory()

        response = await client.post(url=url, json=user_data)

        assert response.status_code == 422

    async def test_post_fail_existed_username(
        self, url_factory, user_factory, client: AsyncAPIClient
    ):
        user_data: dict = await user_factory(raw=True, username=client.user.username)
        url: str = url_factory()

        response = await client.post(url=url, json=user_data)

        assert response.status_code == 409

    async def test_post_fail_no_http_body(self, url_factory, client: AsyncAPIClient):
        url: str = url_factory()

        response = await client.post(url=url, json={})

        assert response.status_code == 422


class TestPatch:
    async def test_patch_fail_unauthorized(self, url_factory, client: AsyncAPIClient):
        url: str = url_factory(id=client.user.id)
        data_for_update: dict = {"password": "QWErty123"}

        response = await client.patch(url=url, json=data_for_update)

        assert response.status_code == 401

    async def test_patch_success_owner(self, url_factory, client: AsyncAPIClient):
        data_for_update: dict = {"password": "QWErty123"}
        url: str = url_factory(id=client.user.id)

        response = await client.patch(
            url=url, json=data_for_update, headers=client.user.auth_header
        )
        response_json: dict[str, str | int] = response.json()

        assert response.status_code == 200
        assert client.user.as_dict == response_json

    async def test_patch_fail_not_owner(self, url_factory, user_factory, client: AsyncAPIClient):
        user: User = await user_factory()
        data_for_update: dict = {"password": "QWErty123"}
        url: str = url_factory(id=user.id)

        response = await client.patch(
            url=url, json=data_for_update, headers=client.user.auth_header
        )

        assert response.status_code == 403

    async def test_patch_success_admin(self, url_factory, user_factory, client: AsyncAPIClient):
        user: User = await user_factory()
        data_for_update: dict = {"password": "QWErty123"}
        url: str = url_factory(id=user.id)

        response = await client.patch(
            url=url, json=data_for_update, headers=client.admin.auth_header
        )
        response_json: dict[str, str | int] = response.json()

        assert response.status_code == 200
        assert user.as_dict == response_json


class TestDelete:
    async def test_delete_fail_unauthorized(
        self, url_factory, user_factory, client: AsyncAPIClient
    ):
        user: User = await user_factory()
        url: str = url_factory(id=user.id)

        response = await client.delete(url=url)

        assert response.status_code == 401

    async def test_delete_fail_not_owner(self, url_factory, user_factory, client: AsyncAPIClient):
        user: User = await user_factory()
        url: str = url_factory(id=user.id)

        response = await client.delete(url=url, headers=client.user.auth_header)

        assert response.status_code == 403

    async def test_delete_success_admin(self, url_factory, user_factory, client: AsyncAPIClient):
        user: User = await user_factory()
        url: str = url_factory(id=user.id)

        response = await client.delete(url=url, headers=client.admin.auth_header)

        assert response.status_code == 204
