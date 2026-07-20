from fastapi import WebSocket
from typing import Dict, List, Tuple


class ConnectionManager:
    def __init__(self):
        # doc_id -> list of (websocket, username) tuples
        self.connections: Dict[int, List[Tuple[WebSocket, str]]] = {}

    async def connect(self, websocket: WebSocket, doc_id: int, username: str):
        await websocket.accept()
        if doc_id not in self.connections:
            self.connections[doc_id] = []
        self.connections[doc_id].append((websocket, username))

    def disconnect(self, websocket: WebSocket, doc_id: int):
        if doc_id in self.connections:
            self.connections[doc_id] = [
                (ws, u) for ws, u in self.connections[doc_id]
                if ws != websocket
            ]
            if not self.connections[doc_id]:
                del self.connections[doc_id]

    def get_usernames(self, doc_id: int) -> List[str]:
        return [u for _, u in self.connections.get(doc_id, [])]

    async def broadcast_to_others(self, message: dict, doc_id: int, sender: WebSocket):
        """Send a message to every connected client except the sender."""
        for ws, _ in self.connections.get(doc_id, []):
            if ws != sender:
                try:
                    await ws.send_json(message)
                except Exception:
                    pass  # Client may have already disconnected

    async def broadcast_to_all(self, message: dict, doc_id: int):
        """Send a message to every connected client including the sender."""
        for ws, _ in self.connections.get(doc_id, []):
            try:
                await ws.send_json(message)
            except Exception:
                pass


# Single shared instance used across the entire app
manager = ConnectionManager()
