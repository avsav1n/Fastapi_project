import bcrypt


def hash_password(data: dict) -> dict:
    hashed_password: bytes = bcrypt.hashpw(data["password"].encode(), bcrypt.gensalt())
    data["password"] = hashed_password.decode()
    return data


def check_password(password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed_password.encode())
