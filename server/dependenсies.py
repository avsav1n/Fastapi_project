from typing import Annotated, AsyncGenerator, TypeAlias

from fastapi import Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from server.crud import validate_token
from server.models import Session, Token, User
from server.schema import AuthParams


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Зависимость асинхронной сессии"""
    session: AsyncSession = Session()
    try:
        yield session
    finally:
        await session.close()


SessionDependency: TypeAlias = Annotated[AsyncSession, Depends(get_session, use_cache=True)]


async def get_user(
    auth: Annotated[AuthParams, Header()], session: SessionDependency
) -> User | None:
    """Зависимость авторизации

    :param Annotated[AuthParams, Header auth: namedtuple параметров заголовка авторизации
    :param SessionDependency session: объект асинхронной сессии
    :return User | None: объект User при наличии валидного токена в заголовке, иначе None
    """
    if auth.token is not None:
        token: Token = await validate_token(session=session, token=auth.token)
        return token.user
