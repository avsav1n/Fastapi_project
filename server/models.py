from datetime import datetime
from typing import TypeAlias

import sqlalchemy as sq
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

import server.config as cfg

DSN = (
    f"postgresql+asyncpg://{cfg.POSTGRES_USER}:"
    f"{cfg.POSTGRES_PASSWORD}@{cfg.POSTGRES_HOST}:"
    f"{cfg.POSTGRES_PORT}/{cfg.POSTGRES_DB}"
)
engine = create_async_engine(url=DSN)
Session = async_sessionmaker(bind=engine, expire_on_commit=False)


class Base(AsyncAttrs, DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "User"

    id: Mapped[int] = mapped_column(sq.Integer, primary_key=True)
    username: Mapped[str] = mapped_column(sq.String(100), unique=True)
    password: Mapped[str] = mapped_column(sq.String(100))
    registered_at: Mapped[datetime] = mapped_column(sq.DateTime, server_default=sq.func.now())

    advertisements: Mapped[list["Advertisement"]] = relationship(
        "Advertisement", back_populates="author", cascade="all, delete-orphan"
    )

    @property
    def as_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "registered_at": self.registered_at.isoformat(),
        }


class Advertisement(Base):
    __tablename__ = "Advertisement"

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


ORM_MODEL: TypeAlias = User | Advertisement
