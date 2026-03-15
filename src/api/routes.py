from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import asyncio
from src.config.loader import load_config
from src.functions.executor import process_function_call_async, execute_function_async

from src.api.connection_manager import manager
from src.utils.logger import logger

router = APIRouter()


@router.get("/health")
def get_health():
    return {"status": "success", "message": "连接成功"}


@router.get("/api/config")
def get_config():
    return load_config()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    
    try:
        while True:
            data = await websocket.receive_json()
            message_type = data.get("type")
            
            if message_type == "execute":
                request_id = manager.register_request(websocket, data.get("id"))
                function_call = {
                    "function": data.get("function"),
                    "parameters": data.get("parameters", {})
                }
                
                result = await execute_function_async(function_call)
                
                response = {
                    "type": "result",
                    "id": request_id,
                    "success": result.get("success", False),
                    "output": result.get("output"),
                    "error": result.get("error")
                }
                
                await websocket.send_json(response)
                manager.unregister_request(request_id)
                    
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket错误：{str(e)}")
        manager.disconnect(websocket)
