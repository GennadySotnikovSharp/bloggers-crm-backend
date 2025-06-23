from fastapi import WebSocket
from typing import Dict, List, Any


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[Dict[str, Any]] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append({"ws": websocket, "user_id": None, "role": None, "chat_id": None})

    def disconnect(self, websocket: WebSocket):
        self.active_connections = [conn for conn in self.active_connections if conn["ws"] != websocket]

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def send_to_all_marketers(self, message: str):
        for conn in self.active_connections:
            if conn["role"] == "marketer":
                await conn["ws"].send_text(message)

    def get_user_id(self, websocket: WebSocket):
        for conn in self.active_connections:
            if conn["ws"] == websocket:
                return conn["user_id"]
        return None