from datetime import datetime
from functools import lru_cache
from typing import Literal, Self, TypeAlias
from uuid import UUID

import sqlalchemy as sq
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from server.config import (
    POSTGRES_DB,
    POSTGRES_HOST,
    POSTGRES_PASSWORD,
    POSTGRES_PORT,
    POSTGRES_USER,
    ROLE_RIGHTS_SCHEMA,
)

DSN = (
    f"postgresql+asyncpg://{POSTGRES_USER}:"
    f"{POSTGRES_PASSWORD}@{POSTGRES_HOST}:"
    f"{POSTGRES_PORT}/{POSTGRES_DB}"
)
engine = create_async_engine(url=DSN)
Session = async_sessionmaker(bind=engine, expire_on_commit=False)

ROLE = Literal["admin", "user"]
MODEL = Literal["Role", "Right", "User", "Advertisement", "Token"]


class Base(AsyncAttrs, DeclarativeBase):
    pass


roles_rights = sq.Table(
    "roles_rights_relation",
    Base.metadata,
    sq.Column("role_id", sq.ForeignKey("Role.id")),
    sq.Column("right_id", sq.ForeignKey("Right.id")),
)


class Right(Base):
    """Модель таблицы Right

    Содержит права на совершение действий с указанной таблицей.
    Все права по-умолчанию выставлены для роли user.

    :owner_only: требование проверки собственности.
        Если True необходимо проверять пользователя на владельца ресурса,
        к которому осуществляется обращение, если False, то не требуется - в таком случае
        можно осуществлять изменение/удаление любых ресурсов при наличии
        соответствующих разрешений update/delete.
    :read: разрешение на чтение (HTTP-метод GET).
    :create: разрешение на создание (HTTP-метод POST).
    :update: разрешение на обновление (HTTP-метод PATCH).
    :delete: разрешение на удаление (HTTP-метод DELETE)
    """

    __tablename__ = "Right"
    __table_args__ = (
        sq.UniqueConstraint("model", "owner_only", "read", "create", "update", "delete"),
    )

    id: Mapped[int] = mapped_column(sq.Integer, primary_key=True)
    model: Mapped[MODEL] = mapped_column(sq.String(50), nullable=False)
    owner_only: Mapped[bool] = mapped_column(sq.Boolean, default=True)
    read: Mapped[bool] = mapped_column(sq.Boolean, default=True)
    create: Mapped[bool] = mapped_column(sq.Boolean, default=True)
    update: Mapped[bool] = mapped_column(sq.Boolean, default=True)
    delete: Mapped[bool] = mapped_column(sq.Boolean, default=True)

    @classmethod
    @lru_cache(maxsize=128)
    def get_rights_for_anon(cls) -> list[Self]:
        """Классовый метод формирования прав для неавторизованного пользователя

        В текущей реализации информация подтягивается из схемы прав server.config.ROLE_RIGHTS_SCHEMA

        :return list[Self]: список объектов Right
        """
        for role in ROLE_RIGHTS_SCHEMA:
            if role["name"] == "anon":
                return [cls(**right) for right in role["rights"]]


class Role(Base):
    """Модель таблицы Role"""

    __tablename__ = "Role"

    id: Mapped[int] = mapped_column(sq.Integer, primary_key=True)
    name: Mapped[ROLE] = mapped_column(sq.String(50), nullable=False, unique=True)

    rights: Mapped[list["Right"]] = relationship("Right", secondary=roles_rights, lazy="joined")
    users: Mapped[list["User"]] = relationship("User", back_populates="role")


class User(Base):
    """Модель таблицы User"""

    __tablename__ = "User"
    _owner_field = "id"

    id: Mapped[int] = mapped_column(sq.Integer, primary_key=True)
    role_name: Mapped[ROLE] = mapped_column(sq.String(50), sq.ForeignKey(Role.name), default="user")
    username: Mapped[str] = mapped_column(sq.String(100), unique=True)
    password: Mapped[str] = mapped_column(sq.String(100))
    registered_at: Mapped[datetime] = mapped_column(sq.DateTime, server_default=sq.func.now())

    advertisements: Mapped[list["Advertisement"]] = relationship(
        "Advertisement", back_populates="author", cascade="all, delete-orphan"
    )
    tokens: Mapped[list["Token"]] = relationship(
        "Token", back_populates="user", cascade="all, delete-orphan"
    )
    role: Mapped["Role"] = relationship("Role", back_populates="users")

    @property
    def as_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "role": self.role_name,
            "registered_at": self.registered_at.isoformat(),
        }


class Token(Base):
    """Модель таблицы Token"""

    __tablename__ = "Token"
    _owner_field = "id_user"

    id: Mapped[int] = mapped_column(sq.Integer, primary_key=True)
    id_user: Mapped[int] = mapped_column(sq.Integer, sq.ForeignKey(User.id, ondelete="CASCADE"))
    token: Mapped[UUID] = mapped_column(
        sq.UUID, server_default=sq.func.gen_random_uuid(), unique=True
    )
    created_at: Mapped[datetime] = mapped_column(sq.DateTime, server_default=sq.func.now())

    user: Mapped["User"] = relationship("User", back_populates="tokens", lazy="joined")

    @property
    def as_dict(self):
        return {
            "token": self.token,
            "created_at": self.created_at.isoformat(),
        }


class Advertisement(Base):
    """Модель таблицы Advertisement"""

    __tablename__ = "Advertisement"
    _owner_field = "id_user"

    id: Mapped[int] = mapped_column(sq.Integer, primary_key=True)
    id_user: Mapped[int] = mapped_column(sq.Integer, sq.ForeignKey(User.id, ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(sq.String(100), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(sq.Text, nullable=False)
    price: Mapped[int] = mapped_column(sq.BigInteger, nullable=False)
    created_at: Mapped[datetime] = mapped_column(sq.DateTime, server_default=sq.func.now())
    updated_at: Mapped[datetime] = mapped_column(
        sq.DateTime, server_default=sq.func.now(), onupdate=sq.func.now()
    )

    author: Mapped["User"] = relationship("User", back_populates="advertisements")

    @property
    def as_dict(self):
        return {
            "id": self.id,
            "id_user": self.id_user,
            "title": self.title,
            "description": self.description,
            "price": self.price,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


async def close_orm():
    await engine.dispose()


ORM_MODEL: TypeAlias = User | Advertisement | Token
