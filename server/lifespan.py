from fastapi import FastAPI
from server.models import close_orm
from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await close_orm()
