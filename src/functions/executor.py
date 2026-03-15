import re
import json
from typing import Dict, Any, Optional
from src.config.loader import get_tool_routing_map
from src.functions.inline_tools import execute_inline_tool
from src.functions.mcp_tools import execute_mcp_tool
from src.utils.logger import logger


async def execute_function_async(function_call: Dict[str, Any]) -> Dict[str, Any]:
    function_name = function_call.get('function')
    parameters = function_call.get('parameters', {})
    
    logger.info(f"执行函数：{function_name}")
    logger.info(f"参数：{parameters}")
    
    routing_map = get_tool_routing_map()
    tool_info = routing_map.get(function_name) # type: ignore
    
    if not tool_info:
        logger.error(f"未知函数：{function_name}")
        return {"success": False, "error": f"未知函数：{function_name}"}
    
    try:
        if tool_info["type"] == "inline":
            result = await execute_inline_tool(function_name, parameters) # type: ignore
            logger.info(f"内联工具执行结果：{result}")
            return result
        elif tool_info["type"] == "mcp":
            result = await execute_mcp_tool(tool_info["server"], function_name, parameters) # type: ignore
            logger.info(f"MCP工具执行结果：{result}")
            return result
        else:
            logger.error(f"未知工具类型：{tool_info['type']}")
            return {"success": False, "error": f"未知工具类型：{tool_info['type']}"}
    except Exception as e:
        logger.error(f"执行函数时出错：{str(e)}")
        return {"success": False, "error": str(e)}


async def process_function_call_async(content: str) -> Optional[Dict[str, Any]]:
    try:
        json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
        if json_match:
            function_call = json.loads(json_match.group(1))
            logger.info("解析到function call:")
            logger.info(json.dumps(function_call, indent=2))
            return await execute_function_async(function_call)
        
        json_match = re.search(r'\{\s*"function"\s*:\s*".*?"\s*,\s*"parameters"\s*:\s*\{.*?\}\s*\}', content, re.DOTALL)
        if json_match:
            function_call = json.loads(json_match.group(0))
            logger.info("解析到function call:")
            logger.info(json.dumps(function_call, indent=2))
            return await execute_function_async(function_call)
    except Exception as e:
        logger.error(f"处理function call时出错：{str(e)}")
    return None
