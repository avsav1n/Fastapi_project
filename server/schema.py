import re
from datetime import datetime
from typing import Annotated, ClassVar

from pydantic import BaseModel, Field, field_validator


class PaginationParams(BaseModel):
    page: int


class BasePaginatedResponse(BaseModel):
    quantity: int
    current_page: int
    previous: str | None
    next: str | None


class UserResponse(BaseModel):
    id: int
    username: str
    registered_at: datetime


class PaginatedUserResponse(BasePaginatedResponse):
    results: list[UserResponse]


class BaseUserRequest(BaseModel):
    username: str
    password: str

    password_pattern: ClassVar = re.compile(r"^(?=.*\d)(?=.*[a-z])(?=.*[A-Z])(?!.*\s).*$")

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        result = cls.password_pattern.fullmatch(value)
        if result:
            return value
        raise ValueError(
            "The password too simple. It must contain numbers, uppercase and lowercase letters."
        )


class CreateUserRequest(BaseUserRequest):
    pass


class UpdateUserRequest(BaseUserRequest):
    username: str | None = None
    password: str | None = None


class AdvertisementResponse(BaseModel):
    id: int
    id_user: int
    title: str
    description: str
    price: int
    created_at: datetime
    updated_at: datetime


class PaginatedAdvertisementsResponse(BasePaginatedResponse):
    results: list[AdvertisementResponse]


class BaseAdvertisementRequest(BaseModel):
    id_user: int
    title: str
    description: str
    price: int


class CreateAdvertisementRequest(BaseAdvertisementRequest):
    pass


class UpdateAdvertisementRequest(BaseAdvertisementRequest):
    id_user: int | None = None
    title: str | None = None
    description: str | None = None
    price: int | None = None


class QueryParams(BaseModel):
    model_config = {"extra": "forbid"}

    page: Annotated[int, Field(1, ge=1)]
    search: Annotated[str | None, Field(None)]
    order_by: Annotated[tuple[str], Field(["id"])]

    @field_validator("order_by", mode="before")
    @classmethod
    def validate_order_by(cls, value: tuple[str]) -> tuple[str]:
        return tuple("".join(value).replace(" ", "").split(","))
