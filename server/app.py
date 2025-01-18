from fastapi import FastAPI

from server.lifespan import lifespan
from server.views import adv_router, usr_router


def get_app() -> FastAPI:
    app = FastAPI(
        description="API service of advertisements for sale/purchase",
        version="1.0",
        lifespan=lifespan,
    )
    app.include_router(usr_router)
    app.include_router(adv_router)
    return app


app = get_app()
