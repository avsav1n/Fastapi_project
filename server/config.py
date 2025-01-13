import os

# Параметры поключения к базе данных PostgreSQL
POSTGRES_DB = os.getenv("POSTGRES_DB", "fastapiproject")
POSTGRES_USER = os.getenv("POSTGRES_NAME", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "1111")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")

# Параметры пагинации
VALUES_ON_PAGE = 5
