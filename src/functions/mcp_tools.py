from typing import Dict, Any
from src.config.loader import load_mcp_servers
from src.mcp.client import get_mcp_client, init_mcp_servers


# 模块级变量，用于跟踪是否已初始化
_mcp_initialized = False


def ensure_mcp_initialized():
    """确保MCP客户端已初始化"""
    global _mcp_initialized
    if not _mcp_initialized:
        servers = load_mcp_servers()
        init_mcp_servers(servers)
        _mcp_initialized = True


async def execute_mcp_tool(server_name: str, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
    try:
        ensure_mcp_initialized()
        mcp_client = get_mcp_client()
        return await mcp_client.call_tool(server_name, tool_name, parameters)
    except Exception as e:
        return {"success": False, "error": f"MCP工具执行失败：{str(e)}"}
