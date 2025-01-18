from typing import Annotated, ClassVar

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, status
from fastapi_utils.cbv import cbv
from sqlalchemy.ext.asyncio import AsyncSession

from server.auth import check_password, hash_password
from server.crud import Database, get_user_by_username
from server.dependenсies import SessionDependency, get_session, get_token
from server.filters import FilterSet
from server.models import ORM_MODEL, Advertisement, Token, User
from server.pagination import Paginator
from server.schema import (
    AdvertisementResponse,
    AuthParams,
    CreateAdvertisementRequest,
    CreateUserRequest,
    PaginatedAdvertisementsResponse,
    PaginatedUserResponse,
    QueryParams,
    TokenResponse,
    UpdateAdvertisementRequest,
    UpdateUserRequest,
    UserResponse,
)

usr_router = APIRouter(prefix="/user")
adv_router = APIRouter(prefix="/advertisement")
auth_router = APIRouter(prefix="/login")


class BaseView:
    session: AsyncSession = Depends(get_session)
    token: Token = Depends(get_token)

    model: ClassVar[ORM_MODEL] = None
    search_fields: ClassVar[tuple[str]] = None
    filterset_class: ClassVar = FilterSet
    pagination_class: ClassVar = Paginator

    def __init__(self):
        self.dbase = Database(session=self.session, model=self.model)

    async def get_list(self, request: Request, query_params: QueryParams):
        query_params: dict = query_params.model_dump()
        filterset: FilterSet = self.filterset_class(
            model=self.model, search_fields=self.search_fields, filter_params=query_params
        )
        paginator: Paginator = self.pagination_class(
            url=str(request.url), pagination_params=query_params
        )
        objs: list[ORM_MODEL] = await self.dbase.get_list(filterset=filterset, paginator=paginator)
        objs: list[dict] = [obj.as_dict for obj in objs]
        page = paginator.get_paginated_page(values=objs)
        return page

    async def get_detail(self, id: int):
        obj: ORM_MODEL = await self.dbase.get_detail(id=id)
        return obj.as_dict

    async def delete(self, id: int):
        obj: ORM_MODEL = await self.dbase.get_detail(id=id)
        await self.dbase.delete(obj=obj)


@cbv(router=usr_router)
class UserView(BaseView):
    model = User
    search_fields = ("username",)

    @usr_router.get("/", response_model=PaginatedUserResponse, status_code=status.HTTP_200_OK)
    async def get_list(self, request: Request, query_params: Annotated[QueryParams, Query()]):
        return await super().get_list(request, query_params)

    @usr_router.get("/{id}/", response_model=UserResponse, status_code=status.HTTP_200_OK)
    async def get_detail(self, id: int):
        return await super().get_detail(id)

    @usr_router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
    async def create(self, user_info: CreateUserRequest):
        validated_data: dict = user_info.model_dump()
        validated_data: dict = hash_password(validated_data)
        created_user: User = await self.dbase.create(validated_data=validated_data)
        return created_user.as_dict

    @usr_router.patch("/{id}/", response_model=UserResponse, status_code=status.HTTP_200_OK)
    async def update(self, user_info: UpdateUserRequest, id: int):
        validated_data: dict = user_info.model_dump(exclude_unset=True)
        if validated_data.get("password"):
            validated_data: dict = hash_password(validated_data)
        user: User = await self.dbase.get_detail(id=id)
        updated_user: User = await self.dbase.update(obj=user, validated_data=validated_data)
        return updated_user.as_dict

    @usr_router.delete("/{id}/", status_code=status.HTTP_204_NO_CONTENT)
    async def delete(self, id: int):
        return await super().delete(id)


@cbv(router=adv_router)
class AdvertisementView(BaseView):
    model = Advertisement
    search_fields = (
        "title",
        "description",
        "price",
    )

    @adv_router.get(
        "/", response_model=PaginatedAdvertisementsResponse, status_code=status.HTTP_200_OK
    )
    async def get_list(self, request: Request, query_params: Annotated[QueryParams, Query()]):
        return await super().get_list(request, query_params)

    @adv_router.get("/{id}/", response_model=AdvertisementResponse, status_code=status.HTTP_200_OK)
    async def get_detail(self, id: int):
        return await super().get_detail(id)

    @adv_router.post("/", response_model=AdvertisementResponse, status_code=status.HTTP_201_CREATED)
    async def create(self, adv_info: CreateAdvertisementRequest):
        validated_data: dict = adv_info.model_dump()
        validated_data["id_user"] = self.token.id_user
        created_adv: Advertisement = await self.dbase.create(validated_data=validated_data)
        return created_adv.as_dict

    @adv_router.patch(
        "/{id}/", response_model=AdvertisementResponse, status_code=status.HTTP_200_OK
    )
    async def update(self, adv_info: UpdateAdvertisementRequest, id: int):
        validated_data: dict = adv_info.model_dump(exclude_unset=True)
        adv: Advertisement = await self.dbase.get_detail(id=id)
        updated_adv: Advertisement = await self.dbase.update(obj=adv, validated_data=validated_data)
        return updated_adv.as_dict

    @adv_router.delete("/{id}/", status_code=status.HTTP_204_NO_CONTENT)
    async def delete(self, id: int):
        return await super().delete(id)


@auth_router.post("", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def login(session: SessionDependency, auth: Annotated[AuthParams, Header()]):
    if not all([auth.username, auth.password]):
        raise HTTPException(401, "Basic authorization credentials were not provided")
    user: User = await get_user_by_username(session=session, username=auth.username)
    if not check_password(auth.password, user.password):
        raise HTTPException(401, "The provided password is invalid")
    dbase: Database = Database(session=session, model=Token)
    token: Token = await dbase.create(validated_data={"user": user})
    return token.as_dict
