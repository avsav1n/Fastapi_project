from datetime import datetime, timedelta
from uuid import UUID

import sqlalchemy as sq
from fastapi import HTTPException
from sqlalchemy import Select
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from server.config import TOKEN_TTL_HOURS
from server.filters import FilterSet
from server.models import ORM_MODEL, Token, User
from server.pagination import Paginator


class Database:
    def __init__(self, session: AsyncSession, model: ORM_MODEL):
        self._session = session
        self._model = model

    async def _save_changes(self, obj: ORM_MODEL = None) -> None:
        if obj:
            self._session.add(instance=obj)
        try:
            await self._session.commit()
        except IntegrityError:
            raise HTTPException(409, f"{self._model.__tablename__} already exists")

    async def _calculate_quantity(self, query: Select) -> int:
        query: Select = sq.select(sq.func.count()).select_from(query.subquery())
        return await self._session.scalar(query)

    async def get_list(self, paginator: Paginator, filterset: FilterSet = None) -> list[ORM_MODEL]:
        """Метод получения записей

        :param Paginator paginator: объект класса для пагинации данных
        :param FilterSet filterset: объект класса для фильтрации данных, defaults to None
        :return list[ORM_MODEL]: список полученных объектов ORM-модели
        """
        query: Select = sq.select(self._model)
        if filterset is not None:
            query: Select = filterset.filter_query(query=query)

        quantity_objects: int = await self._calculate_quantity(query=query)
        paginator.quantity_objects = quantity_objects
        query: Select = paginator.paginate_query(query=query)
        return await self._session.scalars(query)

    async def get_detail(self, id: int) -> ORM_MODEL:
        """Метод получения записи

        :param int id: идентификатор записи
        :raises HTTPException: ошибка, вызываемая при отсутствии записи в базе данных
        :return ORM_MODEL: полученный объект ORM-модели
        """
        obj: ORM_MODEL | None = await self._session.get(entity=self._model, ident=id)
        if obj:
            return obj
        raise HTTPException(400, f"{self._model.__tablename__} with {id=} not found")

    async def create(self, validated_data: dict) -> ORM_MODEL:
        """Метод создания новой записи

        :param dict validated_data: данные для создания ORM-модели
        :return ORM_MODEL: созданный объект ORM-модели
        """
        obj: ORM_MODEL = self._model(**validated_data)
        await self._save_changes(obj=obj)
        return obj

    async def update(self, obj: ORM_MODEL, validated_data: dict) -> ORM_MODEL:
        """Метод частичного обновления записи

        :param ORM_MODEL obj: объект ORM-модели для частичного обновления
        :param dict validated_data: данные для обновления ORM-модели
        :return ORM_MODEL: обновленный объект ORM-модели
        """
        for attr, value in validated_data.items():
            setattr(obj, attr, value)
        await self._save_changes(obj=obj)
        await self._session.refresh(instance=obj)
        return obj

    async def delete(self, obj: ORM_MODEL) -> ORM_MODEL:
        """Метод удаления записи

        :param ORM_MODEL obj: объект ORM-модели для удаления
        :return ORM_MODEL: удаленный объект ORM-модели
        """
        await self._session.delete(instance=obj)
        await self._save_changes()
        return obj


async def get_user_by_username(session: AsyncSession, username: str) -> User:
    """Метод получения объекта User по уникальному имени пользователя

    :param AsyncSession session: объект асинхронной сессии
    :param str username: уникальное имя пользователя
    :raises HTTPException: ошибка, вызываемая при отсутствии записи в базе данных
    :return User: полученный объект User
    """
    query = sq.select(User).where(User.username == username)
    user: User = await session.scalar(query)
    if user:
        return user
    raise HTTPException(400, f"User with {username=} not found")


async def validate_token(session: AsyncSession, token: UUID) -> Token:
    query: Select = sq.select(Token).where(
        Token.token == token, Token.created_at >= datetime.now() - timedelta(hours=TOKEN_TTL_HOURS)
    )
    token: Token | None = await session.scalar(query)
    if token:
        return token
    raise HTTPException(401, "The provided authorization token is invalid")
