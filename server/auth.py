import bcrypt
from fastapi import HTTPException

from server.models import ORM_MODEL, Right, Role, User


def hash_password(data: dict[str, str]) -> dict[str, str]:
    """Функция хеширования пароля

    :param dict[str, str] data: словарь с оригинальным паролем под ключом 'password'
    :return dict[str, str]: словарь с хешированным паролем под ключом 'password'
    """
    hashed_password: bytes = bcrypt.hashpw(data["password"].encode(), bcrypt.gensalt())
    data["password"] = hashed_password.decode()
    return data


def check_password(password: str, hashed_password: str) -> bool:
    """Функция сравнения оригинальным и хешированного пароля

    :param str password: оригинальным пароль
    :param str hashed_password: хешированный пароль
    :return bool: True - если пароли совпадают, иначе False
    """
    return bcrypt.checkpw(password.encode(), hashed_password.encode())


async def check_permissions(
    user: User | None,
    model: ORM_MODEL,
    obj: ORM_MODEL = None,
    **kwargs,
):
    """Функция проверки прав доступа к запрашиваемому ресурсу

    :param User | None user: объект User, предоставивший валидный токен или
        None (неавторизованный пользователь)
    :param ORM_MODEL model: ORM-модель, к которой осуществляется запрос
    :param ORM_MODEL obj: объект ORM-модели, к которому применяются действия, defaults to None
        Для корректной проверки собственности запрашиваемого ресурса, в используемых ORM-моделях
        необходимо определить классовый атрибут _owner_field - указатель на поле, по которому
        проверка будет проводиться.

    Функция настраивается непосредственно во view-методах через позиционные аргументы.
    Достаточно установить True на требуемые проверки:
        check_permissions(obj=user, owner_only=True, update=True)
    Принимаемые аргументы соответствуют полям прав таблицы Right.
    :owner_only: если True необходимо проверить пользователя на владельца ресурса
        В таком случае функции также необходимо передать ORM-объект для проверки.
    :read: если True необходимо проверить разрешение пользователя на чтение
    :create: если True необходимо проверить разрешение пользователя на создание
    :update: если True необходимо проверить разрешение пользователя на обновление
    :delete: если True необходимо проверить разрешение пользователя на удаление

    При запросе неавторизованного пользователя, ему автоматически назначаются минимальные права,
        описанные в схеме прав server.config.ROLE_RIGHTS_SCHEMA
    """
    if user is None:
        rights: list[Right] = Right.get_rights_for_anon()
    else:
        role: Role = await user.awaitable_attrs.role
        rights: list[Right] = role.rights
    right: list = [right for right in rights if right.model == model.__tablename__]
    if not right:
        raise HTTPException(403, "You don't have permissions to access this resource")
    right: Right = right[0]
    permissions: list = [True]

    if kwargs.pop("owner_only", None) and right.owner_only:
        if obj is None:
            raise ValueError(f"Owner_only check required object {model.__tablename__}")
        if not user.id == getattr(obj, model._owner_field):
            raise HTTPException(403, "Action is available only for the owner")

    for action in kwargs:
        if hasattr(right, action):
            flag: bool = getattr(right, action)
            permissions.append(flag == kwargs[action] or flag)
    if not all(permissions):
        if user is None:
            raise HTTPException(401, "Token authorization credentials were not provided")
        raise HTTPException(403, "You don't have permissions to access this resource")
