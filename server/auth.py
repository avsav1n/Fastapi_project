import bcrypt


def hash_password(data: dict[str, str]) -> dict[str, str]:
    """Функция хеширования пароля

    :param dict[str, str] data: словарь с нехешированным паролем под ключом 'password'
    :return dict[str, str]: словарь с хешированным паролем под ключом 'password'
    """
    hashed_password: bytes = bcrypt.hashpw(data["password"].encode(), bcrypt.gensalt())
    data["password"] = hashed_password.decode()
    return data


def check_password(password: str, hashed_password: str) -> bool:
    """Функция сравнения нехешированного и хешированного пароля

    :param str password: нехешированный пароль
    :param str hashed_password: хешированный пароль
    :return bool: True - если пароли совпадают, иначе False
    """
    return bcrypt.checkpw(password.encode(), hashed_password.encode())
