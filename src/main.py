from services.env import load_env
load_env()

from fastapi import FastAPI
from services.websocket import router

app = FastAPI()

app.include_router(router)