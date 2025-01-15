#!/bin/sh

echo "Make database migrations"
alembic upgrade head

echo "Starting server"
uvicorn server.app:app --workers 3 --proxy-headers --uds /app/socket/asgi.socket
