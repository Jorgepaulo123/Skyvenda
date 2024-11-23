from fastapi import WebSocket
from typing import Dict, Set
import json

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, WebSocket] = {}
        self.typing_users: Dict[int, Set[int]] = {}  # user_id -> set of users typing to them
        
    async def connect(self, websocket: WebSocket, user_id: int):
        await websocket.accept()
        self.active_connections[user_id] = websocket
        
    def disconnect(self, user_id: int):
        if user_id in self.active_connections:
            del self.active_connections[user_id]
            
    async def send_personal_message(self, message: dict, user_id: int):
        if user_id in self.active_connections:
            await self.active_connections[user_id].send_json(message)
            
    async def notify_typing(self, typing_user_id: int, receiver_id: int, is_typing: bool):
        if receiver_id not in self.typing_users:
            self.typing_users[receiver_id] = set()
            
        if is_typing:
            self.typing_users[receiver_id].add(typing_user_id)
        else:
            self.typing_users[receiver_id].discard(typing_user_id)
            
        if receiver_id in self.active_connections:
            await self.active_connections[receiver_id].send_json({
                "type": "typing_status",
                "user_id": typing_user_id,
                "is_typing": is_typing
            })

manager = ConnectionManager()
