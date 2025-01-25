import asyncio
from functools import partial

import pytest
from httpx import ASGITransport

from server.app import app
from tests.utils import (
    AdvertisementFactory,
    AsyncAPIClient,
    ClientInfo,
    UserFactory,
    create_client,
    gen_url,
)


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture(scope="session")
async def clients_info() -> list[ClientInfo, ClientInfo]:
    clients = [await create_client(role=role) for role in ("user", "admin")]
    return clients


@pytest.fixture(scope="session")
async def client(clients_info: list[ClientInfo, ClientInfo]) -> AsyncAPIClient:
    client: AsyncAPIClient = AsyncAPIClient(
        transport=ASGITransport(app=app), base_url="http://localhost:8000"
    )
    client.user, client.admin = clients_info
    return client


@pytest.fixture(scope="session")
def user_factory():
    async def factory(size: int = None, /, **kwargs):
        if kwargs.pop("raw", None):
            return UserFactory.stub(**kwargs).__dict__
        if size and size > 1:
            return await asyncio.gather(*UserFactory.create_batch(size, **kwargs))
        return await UserFactory.create(**kwargs)

    return factory


@pytest.fixture(scope="session")
def adv_factory():
    async def factory(size: int = None, /, **kwargs):
        if kwargs.pop("raw", None):
            return AdvertisementFactory.stub(**kwargs).__dict__
        if size and size > 1:
            return await asyncio.gather(*AdvertisementFactory.create_batch(size, **kwargs))
        return await AdvertisementFactory.create(**kwargs)

    return factory


@pytest.fixture(scope="module")
def url_factory(request):
    if not hasattr(request.module, "BASE_URL"):
        raise ValueError("Test module must contain a base URL path constant BASE_URL")
    factory = partial(gen_url, base_url=getattr(request.module, "BASE_URL"))
    return factory
