import uuid
from typing import Dict, Set
from fastapi import WebSocket, WebSocketDisconnect
from src.utils.logger import logger


class ConnectionManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.pending_requests: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info("WebSocket连接已建立")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        for req_id, ws in list(self.pending_requests.items()):
            if ws == websocket:
                del self.pending_requests[req_id]
        logger.info("WebSocket连接已断开")

    def register_request(self, websocket: WebSocket, request_id: str = None): # type: ignore
        if request_id is None:
            request_id = str(uuid.uuid4())
        self.pending_requests[request_id] = websocket
        logger.info(f"注册请求：{request_id}")
        return request_id

    def unregister_request(self, request_id: str):
        if request_id in self.pending_requests:
            del self.pending_requests[request_id]
            logger.info(f"注销请求：{request_id}")


manager = ConnectionManager()
