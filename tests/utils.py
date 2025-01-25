from typing import Literal, NamedTuple
from urllib.parse import urlencode, urlparse
from uuid import UUID

import sqlalchemy as sq
from factory import Faker
from factory.alchemy import SQLAlchemyModelFactory
from httpx import AsyncClient

from server.models import Advertisement, Session, Token, User


class BaseFactory(SQLAlchemyModelFactory):
    class Meta:
        abstract = True

    @classmethod
    async def _create(cls, model_class, *args, **kwargs):
        obj = model_class(*args, **kwargs)
        async with Session() as session:
            session.add(obj)
            try:
                await session.commit()
            except sq.exc.IntegrityError:
                await session.rollback()
                unique_column = cls._meta.sqlalchemy_get_or_create
                query = sq.select(cls._meta.model).where(sq.text(f"{unique_column}=:value"))
                obj = await session.scalar(query, {"value": getattr(obj, unique_column)})
        return obj


class UserFactory(BaseFactory):
    username: str = Faker("hostname")
    password: str = Faker("password", special_chars=False)

    class Meta:
        model = User
        sqlalchemy_get_or_create: str = "username"


class TokenFactory(BaseFactory):
    class Meta:
        model = Token


class AdvertisementFactory(BaseFactory):
    title: str = Faker("sentence", variable_nb_words=False, nb_words=4)
    description: str = Faker("paragraph", nb_sentences=10)
    price: int = Faker("pyint")

    class Meta:
        model = Advertisement
        sqlalchemy_get_or_create: str = "title"

    @classmethod
    async def _create(cls, model_class, *args, **kwargs):
        if not (kwargs.get("author") or kwargs.get("id_user")):
            user: User = await UserFactory.create()
            kwargs.update({"author": user})
        return await super()._create(model_class, *args, **kwargs)


class ClientInfo(NamedTuple):
    id: int
    username: str
    role: str
    registered_at: str
    auth_header: str

    @property
    def as_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "role": self.role,
            "registered_at": self.registered_at,
        }


class AsyncAPIClient(AsyncClient):
    def __init__(self, *args, **kwargs):
        self.user = None
        self.admin = None
        super().__init__(*args, **kwargs)


class UrlParams(NamedTuple):
    id: int | None = None
    page: str | None = None
    search: str | None = None
    order_by: str | None = None

    @property
    def query(self):
        qs: dict = self._asdict()
        qs.pop("id", None)
        return {key: val for key, val in qs.items() if val is not None}


async def create_client(role: Literal["user", "admin"]) -> ClientInfo:
    """Функция создания тестового пользователя

    :param Literal["user", "admin"] role: роль пользователя
    :return ClientInfo: namedtuple с информацией о пользователе
    """
    user: User = await UserFactory(role_name=role)
    user_token: Token = await TokenFactory(user=user)
    return ClientInfo(**user.as_dict, auth_header={"Authorization": f"Token {user_token.token}"})


def gen_url(base_url: str, **kwargs) -> str:
    """Функция формирования URL c path-параметрами и query-string

    :param str base_url: базовый URL
    :return str: сформированный URL
    """
    url_params: UrlParams = UrlParams(**kwargs)
    parsed_url = urlparse(base_url)
    path = parsed_url.path
    if url_params.id is not None:
        path = f"{path}{url_params.id}/"
    new_qs = urlencode(query=url_params.query, doseq=True)
    return parsed_url._replace(path=path, query=new_qs).geturl()


def validate_uuid(uuid: str) -> bool:
    """Функция валидации UUID

    :param str uuid: уникальный идентификатор
    :return bool: результат валидации
    """
    try:
        UUID(uuid)
        return True
    except ValueError:
        return False
