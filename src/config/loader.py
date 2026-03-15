import os
import json
import yaml
from typing import Dict, Any, List, Optional
from src.utils.settings import settings
from src.utils.logger import logger

CONFIG_FILE = "config.json"
PROMPTS_FILE = "prompts.yml"
PROMPTS_DIR = "prompts"
TOOL_MAPPING_FILE = settings.TOOL_MAPPING_FILE
MCP_TOOLS_DIR = "mcp_tool"

# 配置缓存
_config_cache = {}

# 读取配置文件
def load_config():
    if "config" not in _config_cache:
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    config = json.load(f)
                    logger.info("配置文件加载成功")
                    
                    # 处理模式的提示词引用
                    if "modes" in config:
                        for mode in config["modes"]:
                            # 如果模式有 prompt_file 字段，从文件加载
                            if "prompt_file" in mode:
                                prompt_file = mode["prompt_file"]
                                prompt_text = load_prompt_from_file(prompt_file)
                                if prompt_text:
                                    mode["text"] = prompt_text
                            # 兼容旧版：如果是 互动 模式且没有 prompt_file，使用默认 prompts.yml
                            elif mode.get("label") == "🤖 互动":
                                prompts = load_prompts()
                                mode["text"] = prompts.get("interaction", "")
                    
                    _config_cache["config"] = config
            except Exception as e:
                logger.error(f"加载配置文件失败: {e}")
                _config_cache["config"] = get_default_config()
        else:
            # 如果没有配置文件，使用默认配置
            _config_cache["config"] = get_default_config()
    return _config_cache["config"]

# 读取默认提示词文件
def load_prompts():
    if "prompts" not in _config_cache:
        if os.path.exists(PROMPTS_FILE):
            try:
                with open(PROMPTS_FILE, "r", encoding="utf-8") as f:
                    prompts = yaml.safe_load(f)
                    logger.info("提示词文件加载成功")
                    _config_cache["prompts"] = prompts
            except Exception as e:
                logger.error(f"加载提示词文件失败: {e}")
                _config_cache["prompts"] = {"interaction": ""}
        else:
            logger.info("使用默认提示词")
            _config_cache["prompts"] = {"interaction": ""}
    return _config_cache["prompts"]

# 从文件加载提示词
def load_prompt_from_file(prompt_file):
    """从 prompts 目录加载提示词文件"""
    prompt_path = os.path.join(PROMPTS_DIR, prompt_file)
    if os.path.exists(prompt_path):
        try:
            with open(prompt_path, "r", encoding="utf-8") as f:
                prompt_data = yaml.safe_load(f)
                logger.info(f"从 {prompt_file} 加载提示词成功")
                return prompt_data.get("interaction", "")
        except Exception as e:
            logger.error(f"加载提示词文件 {prompt_file} 失败: {e}")
            return ""
    else:
        logger.warning(f"提示词文件 {prompt_file} 不存在")
        return ""

# 读取工具映射配置
def load_tool_mapping() -> Dict[str, Any]:
    if "tool_mapping" not in _config_cache:
        if os.path.exists(TOOL_MAPPING_FILE):
            try:
                with open(TOOL_MAPPING_FILE, "r", encoding="utf-8") as f:
                    mapping = yaml.safe_load(f)
                    logger.info("工具映射文件加载成功")
                    _config_cache["tool_mapping"] = mapping
            except Exception as e:
                logger.error(f"加载工具映射文件失败: {e}")
                _config_cache["tool_mapping"] = {"inline_tools": [], "mcp_tools": []}
        else:
            logger.info("工具映射文件不存在，使用默认配置")
            # 硬编码inline工具定义
            _config_cache["tool_mapping"] = {
                "inline_tools": [
                    {
                        "name": "send_mcp_tool_documentation",
                        "description": "获取MCP工具的说明文档",
                        "parameters": {
                            "tool_name": "string"
                        }
                    }
                ],
                "mcp_tools": []
            }
    return _config_cache["tool_mapping"]

# 读取MCP服务器配置
def load_mcp_servers() -> List[Dict[str, Any]]:
    if "mcp_servers" not in _config_cache:
        servers = []
        
        # 从 mcp_tool 文件夹加载
        if os.path.exists(MCP_TOOLS_DIR) and os.path.isdir(MCP_TOOLS_DIR):
            for filename in os.listdir(MCP_TOOLS_DIR):
                if filename.endswith('.yml') or filename.endswith('.yaml'):
                    filepath = os.path.join(MCP_TOOLS_DIR, filename)
                    try:
                        with open(filepath, "r", encoding="utf-8") as f:
                            config = yaml.safe_load(f)
                            
                            if config and "server_name" in config:
                                server_config = {
                                    "name": config["server_name"],
                                    "command": config.get("command", "python"),
                                    "args": config.get("args", []),
                                    "env": config.get("env", {})
                                }
                                

                                
                                servers.append(server_config)
                                logger.info(f"从 mcp_tool/{filename} 加载MCP服务器配置: {server_config['name']}")
                    except Exception as e:
                        logger.error(f"加载MCP工具配置文件 {filename} 失败: {e}")
        
        if servers:
            logger.info(f"MCP服务器配置加载成功，共 {len(servers)} 个服务器")
        else:
            logger.warning("未找到任何MCP服务器配置")
        
        _config_cache["mcp_servers"] = servers
    return _config_cache["mcp_servers"]

# 获取工具映射字典
def get_tool_routing_map() -> Dict[str, Dict[str, Any]]:
    if "tool_routing_map" not in _config_cache:
        routing_map = {}
        
        # 首先加载 inline_tools（从原有的 tool_mapping.yml 兼容）
        mapping = load_tool_mapping()
        for tool in mapping.get("inline_tools", []):
            routing_map[tool["name"]] = {
                "type": "inline",
                "description": tool.get("description", ""),
                "parameters": tool.get("parameters", {})
            }
        
        # 从 mcp_tool 目录加载 MCP 工具
        if os.path.exists(MCP_TOOLS_DIR) and os.path.isdir(MCP_TOOLS_DIR):
            for filename in os.listdir(MCP_TOOLS_DIR):
                if filename.endswith('.yml') or filename.endswith('.yaml'):
                    filepath = os.path.join(MCP_TOOLS_DIR, filename)
                    try:
                        with open(filepath, "r", encoding="utf-8") as f:
                            config = yaml.safe_load(f)
                            
                            if config and "server_name" in config:
                                server_name = config["server_name"]
                                for tool in config.get("tools", []):
                                    routing_map[tool["name"]] = {
                                        "type": "mcp",
                                        "server": server_name,
                                        "description": tool.get("description", ""),
                                        "parameters": tool.get("parameters", {})
                                    }
                    except Exception as e:
                        logger.error(f"加载MCP工具配置文件 {filename} 失败: {e}")
        
        _config_cache["tool_routing_map"] = routing_map
    return _config_cache["tool_routing_map"]

# 获取默认配置
def get_default_config():
    prompts = load_prompts()
    return {
        "modes": [
            {
                "label": "🔍 写代码",
                "text": "直接输出代码，不要任何多余的解释：\n\n",
                "save": True
            },
            {
                "label": "🤖 互动",
                "text": prompts.get("interaction", ""),
                "save": True
            },
            {
                "label": "🚫 无",
                "text": "",
                "save": False
            }
        ]
    }

# 清除缓存
def clear_config_cache():
    """清除配置缓存，强制重新加载"""
    global _config_cache
    _config_cache = {}
    logger.info("配置缓存已清除")
