from typing import Annotated, AsyncGenerator, TypeAlias

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from server.models import Session


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with Session() as session:
        yield session


SessionDependency: TypeAlias = Annotated[AsyncSession, Depends(get_session)]
