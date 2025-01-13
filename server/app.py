from fastapi import FastAPI

from server.lifespan import lifespan

app = FastAPI(
    description="API service of advertisements for sale/purchase",
    version="1.0",
    lifespan=lifespan,
)

ADV_BASE_URL = "/advertisement"
ADV_URL_W_ID = "/advertisement/{id}"
USR_BASE_URL = "/user"
USR_URL_W_ID = "/user/{id}"
