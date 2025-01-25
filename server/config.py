import os

# Параметры поключения к базе данных PostgreSQL
POSTGRES_DB = os.getenv("POSTGRES_DB", "fastapiproject")
POSTGRES_USER = os.getenv("POSTGRES_NAME", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "1111")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")

# Параметры пагинации
VALUES_ON_PAGE = int(os.getenv("VALUES_ON_PAGE", 5))

# Параметры аутентификации
TOKEN_TTL_HOURS = int(os.getenv("TOKEN_TTL_HOURS", 48))

# Параметры прав
# На основании данной схемы при миграции бд заполняются таблицы Role и Right,
# а также возвращаются объекты Right для неавторизованного пользователя (anon)
ROLE_RIGHTS_SCHEMA = [
    {
        "name": "user",
        "rights": [
            {"model": "User"},
            {"model": "Advertisement"},
        ],
    },
    {
        "name": "admin",
        "rights": [
            {"model": "User", "owner_only": False},
            {"model": "Advertisement", "owner_only": False},
        ],
    },
    {
        "name": "anon",
        "rights": [
            {
                "model": "User",
                "owner_only": False,
                "read": True,
                "create": True,
                "update": False,
                "delete": False,
            },
            {
                "model": "Advertisement",
                "owner_only": False,
                "read": True,
                "create": False,
                "update": False,
                "delete": False,
            },
        ],
    },
]
