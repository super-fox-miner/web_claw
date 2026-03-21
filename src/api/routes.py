from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import asyncio
from src.config.loader import load_config
from src.functions.executor import process_function_call_async, execute_function_async
from src.memory.system import MemorySystem

from src.api.connection_manager import manager
from src.utils.logger import logger

router = APIRouter()

# 初始化记忆系统
memory_system = MemorySystem()


@router.get("/health")
def get_health():
    return {"status": "success", "message": "连接成功"}


@router.get("/api/config")
def get_config():
    return load_config()


@router.get("/api/rules")
def get_rules():
    """获取所有规则列表"""
    try:
        rules = memory_system.list_rule()
        return rules
    except Exception as e:
        logger.error(f"获取规则列表失败: {str(e)}")
        return {"error": str(e)}


@router.delete("/api/rules/{rule_id}")
def delete_rule(rule_id: str):
    """删除指定规则"""
    try:
        result = memory_system.delete_rule(rule_id)
        return result
    except Exception as e:
        logger.error(f"删除规则失败: {str(e)}")
        return {"error": str(e)}


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
