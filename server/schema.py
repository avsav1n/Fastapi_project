import re
from base64 import b64decode
from datetime import datetime
from re import Match
from typing import Annotated, ClassVar
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator


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
    role: str
    registered_at: datetime


class PaginatedUserResponse(BasePaginatedResponse):
    results: list[UserResponse]


class BaseUserRequest(BaseModel):
    username: str
    password: str

    password_pattern: ClassVar = re.compile(r"^(?=.*\d)(?=.*[a-z])(?=.*[A-Z])(?!.*\s).*$")

    @field_validator("password", mode="before")
    @classmethod
    def validate_password(cls, value: str) -> str:
        pattern: str = r"^(?=.*\d)(?=.*[a-z])(?=.*[A-Z])(?!.*\s).*$"
        result: Match = re.fullmatch(pattern=pattern, string=value)
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
    def convert_order_by(cls, value: tuple[str]) -> tuple[str]:
        return tuple("".join(value).replace(" ", "").split(","))


class AuthParams(BaseModel):
    authorization: str | None = None
    username: str | None = None
    password: str | None = None
    token: UUID | None = None

    @model_validator(mode="before")
    @classmethod
    def convert_auth_data(cls, data: dict[str, str]) -> dict:
        if data.get("authorization"):
            type, auth_data = data["authorization"].split(maxsplit=1)
            match type:
                case "Basic":
                    decoded_data: str = b64decode(auth_data, validate=True).decode()
                    data["username"], data["password"] = decoded_data.replace(":", " ").split()
                case "Token":
                    data["token"] = auth_data
        return data


class TokenResponse(BaseModel):
    token: UUID
    created_at: datetime
