from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from server.filters import Filter
from server.models import ORM_CLASS, ORM_OBJECT


class Database:
    def __init__(self, session: AsyncSession, model: ORM_CLASS):
        self._session = session
        self._model = model

    async def _save_changes(self, obj: ORM_OBJECT = None) -> None:
        if obj:
            self._session.add(instance=obj)
        try:
            await self._session.commit()
        except IntegrityError:
            raise HTTPException(409, f"{self._model.__tablename__} already exists")

    async def get_list(self, search_by: str = None, order_by: str = None) -> list[ORM_OBJECT]:
        filter = Filter(model=self._model, search_by=search_by, order_by=order_by)
        return await self._session.scalars(filter.select_expression)

    async def get_detail(self, id: int) -> ORM_OBJECT:
        obj: ORM_OBJECT | None = await self._session.get(entity=self._model, ident=id)
        if obj:
            return obj
        raise HTTPException(400, f"{self._model.__tablename__} with {id=} not found")

    async def create(self, validated_data: dict) -> ORM_OBJECT:
        obj: ORM_OBJECT = self._model(**validated_data)
        await self._save_changes(obj=obj)
        return obj

    async def update(self, obj: ORM_OBJECT, validated_data: dict) -> ORM_OBJECT:
        for attr, value in validated_data.items():
            setattr(obj, attr, value)
        await self._save_changes(obj=obj)
        await self._session.refresh(instance=obj)
        return obj

    async def delete(self, obj: ORM_OBJECT) -> ORM_OBJECT:
        await self._session.delete(instance=obj)
        await self._save_changes()
        return obj
