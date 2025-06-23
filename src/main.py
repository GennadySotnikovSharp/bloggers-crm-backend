from src.services.env import load_env
load_env()

from fastapi import FastAPI
from src.websocket import router

app = FastAPI()

app.include_router(router)
