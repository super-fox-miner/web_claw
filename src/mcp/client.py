import asyncio
import json
import os
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from fastmcp.client import Client
from fastmcp.client.transports import PythonStdioTransport
from src.utils.logger import logger
from src.utils.settings import settings


@dataclass
class MCPServerConfig:
    name: str
    command: str
    args: List[str]
    env: Optional[Dict[str, str]] = None


class MCPClient:
    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MCPClient, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not MCPClient._initialized:
            self.servers: Dict[str, MCPServerConfig] = {}
            self.clients: Dict[str, Client] = {}
            MCPClient._initialized = True

    def register_server(self, config: MCPServerConfig):
        self.servers[config.name] = config

    async def start_server(self, server_name: str) -> bool:
        if server_name not in self.servers:
            logger.error(f"MCP服务器未注册: {server_name}")
            return False
        return True

    async def stop_server(self, server_name: str):
        pass

    def _process_file_paths(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        base_dir = settings.BASE_DIR
        
        if base_dir:
            file_params = ['filename', 'file_name', 'path', 'file_path', 'filepath']
            for param in file_params:
                if param in arguments:
                    file_path = arguments[param]
                    if file_path == "/":
                        arguments[param] = base_dir
                        logger.debug(f"修改参数 {param}: {file_path} -> {arguments[param]}")
                    elif file_path.startswith("/"):
                        relative_path = file_path[1:]
                        arguments[param] = os.path.join(base_dir, relative_path)
                        logger.debug(f"修改参数 {param}: {file_path} -> {arguments[param]}")
                    elif os.path.isabs(file_path):
                        normalized_base = os.path.normpath(base_dir)
                        normalized_path = os.path.normpath(file_path)
                        if not normalized_path.startswith(normalized_base):
                            return {"success": False, "error": "权限不足：文件路径超出允许范围"}
                    else:
                        arguments[param] = os.path.join(base_dir, file_path)
                        logger.debug(f"修改参数 {param}: {file_path} -> {arguments[param]}")
        return arguments

    async def call_tool(self, server_name: str, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        if server_name not in self.servers:
            logger.error(f"MCP服务器未注册: {server_name}")
            return {"success": False, "error": f"MCP服务器未注册: {server_name}"}

        config = self.servers[server_name]
        try:
            processed_args = self._process_file_paths(arguments)
            if "success" in processed_args and not processed_args["success"]:
                return processed_args
            
            transport = PythonStdioTransport(
                script_path=config.args[0],
                args=config.args[1:],
                env=config.env
            )
            
            async with Client(transport=transport) as client:
                logger.info(f"成功连接到MCP服务器: {server_name}")
                logger.debug(f"调用工具: {tool_name}, 参数: {processed_args}")
                result = await client.call_tool(tool_name, processed_args)
                
                if hasattr(result, "content") and len(result.content) > 0:
                    text_content = ""
                    for item in result.content:
                        if hasattr(item, "text"):
                            text_content += item.text + "\n"
                    return {
                        "success": True,
                        "output": text_content.strip()
                    }
                return {
                    "success": True,
                    "output": str(result)
                }
        except Exception as e:
            logger.error(f"调用MCP工具失败: {e}")
            return {"success": False, "error": str(e)}

    async def list_tools(self, server_name: str) -> List[Dict[str, Any]]:
        if server_name not in self.servers:
            logger.error(f"MCP服务器未注册: {server_name}")
            return []

        config = self.servers[server_name]
        try:
            transport = PythonStdioTransport(
                script_path=config.args[0],
                args=config.args[1:],
                env=config.env
            )
            
            async with Client(transport=transport) as client:
                tools = await client.list_tools()
                return [{
                    "name": tool.name,
                    "description": tool.description
                } for tool in tools]
        except Exception as e:
            logger.error(f"列出MCP工具失败: {e}")
            return []

    async def close_all(self):
        pass


def get_mcp_client() -> MCPClient:
    """获取MCP客户端单例"""
    return MCPClient()


def init_mcp_servers(servers_config: List[Dict[str, Any]]):
    """初始化MCP服务器配置"""
    client = get_mcp_client()
    for server_config in servers_config:
        config = MCPServerConfig(
            name=server_config["name"],
            command=server_config["command"],
            args=server_config.get("args", []),
            env=server_config.get("env")
        )
        client.register_server(config)
    logger.info(f"MCP服务器初始化完成，共注册 {len(servers_config)} 个服务器")
