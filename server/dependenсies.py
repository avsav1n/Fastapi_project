from typing import Annotated, AsyncGenerator, TypeAlias

from fastapi import Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from server.config import TOKEN_TTL_HOURS
from server.crud import validate_token
from server.models import Session, Token
from server.schema import AuthParams


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with Session() as session:
        yield session


SessionDependency: TypeAlias = Annotated[AsyncSession, Depends(get_session, use_cache=True)]


async def get_token(auth: Annotated[AuthParams, Header()], session: SessionDependency) -> Token:
    token: Token = await validate_token(session=session, token=auth.token)
    return token


TokenDependency: TypeAlias = Annotated[Token, Depends(get_token)]
