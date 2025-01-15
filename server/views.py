from fastapi import APIRouter, Request, status

from server.config import VALUES_ON_PAGE
from server.crud import Database
from server.dependenсies import SessionDependency
from server.models import Advertisement, User
from server.pagination import Paginator
from server.schema import (
    AdvertisementResponse,
    CreateAdvertisementRequest,
    CreateUserRequest,
    PaginatedAdvertisementsResponse,
    PaginatedUserResponse,
    UpdateAdvertisementRequest,
    UpdateUserRequest,
    UserResponse,
)
from server.security import hash_password

usr_router = APIRouter(prefix="/user")
adv_router = APIRouter(prefix="/advertisement")


@usr_router.get("", response_model=PaginatedUserResponse, status_code=status.HTTP_200_OK)
async def get_user_list(
    session: SessionDependency,
    request: Request,
    page: int = 1,
    search: str = None,
    order_by: str = None,
):
    dbase = Database(session=session, model=User)
    users: list[dict] = [
        user.as_dict for user in await dbase.get_list(search_by=search, order_by=order_by)
    ]
    paginator = Paginator(sequence=users, values_on_page=VALUES_ON_PAGE, url=str(request.url))
    return paginator.get_page(page=page)


@usr_router.get("/{id}", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def get_user_detail(session: SessionDependency, id: int):
    dbase = Database(session=session, model=User)
    user: User = await dbase.get_detail(id=id)
    return user.as_dict


@usr_router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(session: SessionDependency, user_info: CreateUserRequest):
    validated_data: dict = user_info.model_dump()
    validated_data: dict = hash_password(validated_data)
    dbase = Database(session=session, model=User)
    created_user: User = await dbase.create(validated_data=validated_data)
    return created_user.as_dict


@usr_router.patch("/{id}", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def update_user(session: SessionDependency, user_info: UpdateUserRequest, id: int):
    validated_data: dict = user_info.model_dump(exclude_unset=True)
    if validated_data.get("password"):
        validated_data: dict = hash_password(validated_data)
    dbase = Database(session=session, model=User)
    user: User = await dbase.get_detail(id=id)
    updated_user: User = await dbase.update(obj=user, validated_data=validated_data)
    return updated_user.as_dict


@usr_router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(session: SessionDependency, id: int):
    dbase = Database(session=session, model=User)
    user: User = await dbase.get_detail(id=id)
    await dbase.delete(obj=user)


@adv_router.get("", response_model=PaginatedAdvertisementsResponse, status_code=status.HTTP_200_OK)
async def get_adv_list(
    session: SessionDependency,
    request: Request,
    page: int = 1,
    search: str = None,
    order_by: str = None,
):
    dbase = Database(session=session, model=Advertisement)
    advs: list[dict] = [
        adv.as_dict for adv in await dbase.get_list(search_by=search, order_by=order_by)
    ]
    paginator = Paginator(sequence=advs, values_on_page=VALUES_ON_PAGE, url=str(request.url))
    return paginator.get_page(page=page)


@adv_router.get("/{id}", response_model=AdvertisementResponse, status_code=status.HTTP_200_OK)
async def get_adv_detail(session: SessionDependency, id: int):
    dbase = Database(session=session, model=Advertisement)
    adv: Advertisement = await dbase.get_detail(id=id)
    return adv.as_dict


@adv_router.post("", response_model=AdvertisementResponse, status_code=status.HTTP_201_CREATED)
async def create_adv(session: SessionDependency, adv_info: CreateAdvertisementRequest):
    validated_data: dict = adv_info.model_dump()
    dbase = Database(session=session, model=Advertisement)
    created_adv: Advertisement = await dbase.create(validated_data=validated_data)
    return created_adv.as_dict


@adv_router.patch("/{id}", response_model=AdvertisementResponse, status_code=status.HTTP_200_OK)
async def update_adv(session: SessionDependency, adv_info: UpdateAdvertisementRequest, id: int):
    validated_data: dict = adv_info.model_dump(exclude_unset=True)
    dbase = Database(session=session, model=Advertisement)
    adv: Advertisement = await dbase.get_detail(id=id)
    updated_adv: Advertisement = await dbase.update(obj=adv, validated_data=validated_data)
    return updated_adv.as_dict


@adv_router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_adv(session: SessionDependency, id: int):
    dbase = Database(session=session, model=Advertisement)
    user: Advertisement = await dbase.get_detail(id=id)
    await dbase.delete(obj=user)
