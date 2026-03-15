# MCP 文档修改指南

## 1. 需要修改的文档

### 1.1 核心配置文件

| 文件名        | 路径                             | 说明                 |
| ------------- | -------------------------------- | -------------------- |
| filesystem.yml | d:\LocalMind\mcp_tool\filesystem.yml | 文件系统MCP服务器配置 |
| word.yml      | d:\LocalMind\mcp_tool\word.yml      | Word MCP服务器配置   |
| excel.yml     | d:\LocalMind\mcp_tool\excel.yml     | Excel MCP服务器配置  |
| pdf.yml       | d:\LocalMind\mcp_tool\pdf.yml       | PDF MCP服务器配置    |
| .env          | d:\LocalMind\.env                  | 环境变量配置文件     |

### 1.2 代码文件

| 文件名       | 路径                                    | 说明           |
| ------------ | --------------------------------------- | -------------- |
| mcp_tools.py | d:\LocalMind\src\functions\mcp_tools.py | MCP 工具实现   |
| client.py    | d:\LocalMind\src\mcp\client.py          | MCP 客户端实现 |
| routes.py    | d:\LocalMind\src\api\routes.py          | API 路由配置   |
| loader.py    | d:\LocalMind\src\config\loader.py       | 配置加载模块   |

### 1.3 文档文件

| 文件名      | 路径                          | 说明     |
| ----------- | ----------------------------- | -------- |
| 产品文档.md | d:\LocalMind\docs\产品文档.md | 产品文档 |
| 接口文档.md | d:\LocalMind\docs\接口文档.md | 接口文档 |

## 2. 具体修改方法

### 2.0 虚拟环境设置

**修改内容：**

- 所有 MCP 服务器的安装和运行都应在虚拟环境中进行

**步骤：**

1. 创建虚拟环境：

   ```bash
   python -m venv venv
   ```

2. 激活虚拟环境：

   - Windows: `venv\Scripts\activate`
   - Linux/Mac: `source venv/bin/activate`

3. 安装基础依赖：
   ```bash
   pip install mcp fastmcp typer
   ```

### 2.1 MCP 服务器配置文件

**修改内容：**

- 在 `mcp_tool` 目录中为每个 MCP 服务器创建单独的配置文件
- 配置服务器命令、参数和环境变量
- 配置服务器的工具定义

**示例 - filesystem.yml：**

```yaml
# 文件系统MCP服务器配置

server_name: filesystem
description: 文件系统操作MCP服务器

# 服务器启动配置
command: python
args:
  - "mcp_servers/filesystem_server.py"
  - "filesystem"
env: {}

tools:
  - name: write_file
    description: 创建新文件或覆盖现有文件
    parameters:
      path: string
      content: string
    example: {"function": "write_file", "parameters": {"path": "/test.txt", "content": "hello world"}}

  - name: append_file
    description: 追加内容到文件末尾
    parameters:
      path: string
      content: string
    example: {"function": "append_file", "parameters": {"path": "/test.txt", "content": "\nappended content"}}

  - name: delete_content
    description: 删除文件中指定位置的内容（从start_pos到end_pos，不包含end_pos）
    parameters:
      path: string
      start_pos: number
      end_pos: number
    example: {"function": "delete_content", "parameters": {"path": "/test.txt", "start_pos": 5, "end_pos": 10}}

  - name: delete_lines
    description: 删除文件中指定行范围的内容（行号从1开始，包含start_line和end_line）
    parameters:
      path: string
      start_line: number
      end_line: number
    example: {"function": "delete_lines", "parameters": {"path": "/test.txt", "start_line": 2, "end_line": 5}}

  - name: read_file
    description: 读取文件的全部内容
    parameters:
      path: string
    example: {"function": "read_file", "parameters": {"path": "/test.txt"}}

  - name: create_directory
    description: 创建新目录或确保其存在
    parameters:
      path: string
    example: {"function": "create_directory", "parameters": {"path": "/test"}}

  - name: list_directory
    description: 列出目录内容
    parameters:
      path: string
    example: {"function": "list_directory", "parameters": {"path": "/"}}
```

**示例 - word.yml：**

```yaml
# Word MCP服务器配置

server_name: word
description: Word文档操作MCP服务器

# 服务器启动配置
command: python
args:
  - "mcp_servers/Office-Word-MCP-Server/word_mcp_server.py"
env:
  PYTHONPATH: "mcp_servers/Office-Word-MCP-Server"
  MCP_TRANSPORT: "stdio"

tools:
  - name: create_document
    description: 创建新的Word文档
    parameters:
      filename: string
      title: string
      author: string
    example: {"function": "create_document", "parameters": {"filename": "/document.docx", "title": "测试文档", "author": "用户"}}

  - name: get_document_text
    description: 获取文档文本
    parameters:
      filename: string
    example: {"function": "get_document_text", "parameters": {"filename": "/document.docx"}}
```

**示例 - excel.yml：**

```yaml
# Excel MCP服务器配置

server_name: excel
description: Excel文档操作MCP服务器

# 服务器启动配置
command: python
args:
  - "mcp_servers/excel-mcp-server/src/excel_mcp/__main__.py"
env:
  PYTHONPATH: "mcp_servers/excel-mcp-server"
  MCP_TRANSPORT: "stdio"

tools:
  - name: create_workbook
    description: 创建新的Excel工作簿
    parameters:
      filepath: string
    example: {"function": "create_workbook", "parameters": {"filepath": "/workbook.xlsx"}}

  - name: create_worksheet
    description: 创建新的工作表
    parameters:
      filepath: string
      sheet_name: string
    example: {"function": "create_worksheet", "parameters": {"filepath": "/workbook.xlsx", "sheet_name": "Sheet1"}}
```

**示例 - pdf.yml：**

```yaml
# PDF Reader MCP服务器配置

server_name: pdf
description: PDF文件读取MCP服务器

# 服务器启动配置
command: python
args:
  - "mcp_servers/pdf-reader-mcp/src/server.py"
env: {}

tools:
  - name: read_local_pdf
    description: 读取本地PDF文件的文本内容
    parameters:
      path: string
    example: {"function": "read_local_pdf", "parameters": {"path": "/sample.pdf"}}

  - name: read_pdf_url
    description: 从URL读取PDF文件的文本内容
    parameters:
      url: string
    example: {"function": "read_pdf_url", "parameters": {"url": "https://example.com/document.pdf"}}
```

### 2.2 .env 文件配置

**修改内容：**

- 配置环境变量，包括基础目录、服务器端口等

**示例：**

```env
# 服务器配置
SERVER_HOST=127.0.0.1
SERVER_PORT=52431

# 目录配置
BASE_DIR=d:/LocalMind

# 日志配置
LOG_LEVEL=INFO
```

### 2.3 安装 MCP 服务器依赖

**文件系统服务器：**
- 无特殊依赖，使用标准库

**Word 服务器：**
```bash
pip install python-docx
```

**Excel 服务器：**
```bash
pip install openpyxl
```

**PDF 服务器：**
```bash
pip install PyPDF2>=3.0.0 requests>=2.31.0
```

### 2.4 mcp_tools.py

**修改内容：**

- 实现新的 MCP 工具函数
- 处理工具调用和响应

**示例：**

```python
from typing import Dict, Any
from src.config.loader import load_mcp_servers
from src.mcp.client import get_mcp_client, MCPServerConfig


def init_mcp_client():
    mcp_client = get_mcp_client()
    servers = load_mcp_servers()

    for server_config in servers:
        config = MCPServerConfig(
            name=server_config["name"],
            command=server_config["command"],
            args=server_config.get("args", []),
            env=server_config.get("env")
        )
        mcp_client.register_server(config)

    return mcp_client


async def execute_mcp_tool(server_name: str, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
    try:
        mcp_client = init_mcp_client()
        return await mcp_client.call_tool(server_name, tool_name, parameters)
    except Exception as e:
        return {"success": False, "error": f"MCP工具执行失败：{str(e)}"}
```

### 2.5 client.py

**修改内容：**

- 实现 MCP 客户端连接和通信
- 处理服务器认证和错误处理
- 从环境变量获取基础目录

**示例：**

```python
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
```

### 2.6 loader.py

**修改内容：**

- 从 mcp_tool 目录加载服务器配置
- 从 mcp_tool 目录加载工具映射

**示例：**

```python
import os
import json
import yaml
from typing import Dict, Any, List, Optional
from src.utils.settings import settings
from src.utils.logger import logger

CONFIG_FILE = "config.json"
PROMPTS_FILE = "prompts.yml"
TOOL_MAPPING_FILE = settings.TOOL_MAPPING_FILE
MCP_TOOLS_DIR = "mcp_tool"

# 配置缓存
_config_cache = {}

# 读取配置文件
def load_config() -> Dict[str, Any]:
    if "config" not in _config_cache:
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    config = json.load(f)
                    _config_cache["config"] = config
            except Exception as e:
                logger.error(f"加载配置文件失败: {e}")
                _config_cache["config"] = {}
        else:
            logger.info("配置文件不存在，使用默认配置")
            _config_cache["config"] = {}
    return _config_cache["config"]

# 读取提示词配置
def load_prompts() -> Dict[str, str]:
    if "prompts" not in _config_cache:
        if os.path.exists(PROMPTS_FILE):
            try:
                with open(PROMPTS_FILE, "r", encoding="utf-8") as f:
                    prompts = yaml.safe_load(f)
                    _config_cache["prompts"] = prompts
            except Exception as e:
                logger.error(f"加载提示词配置失败: {e}")
                _config_cache["prompts"] = {"interaction": ""}
        else:
            logger.info("使用默认提示词")
            _config_cache["prompts"] = {"interaction": ""}
    return _config_cache["prompts"]

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
    tool_mapping = load_tool_mapping()
    
    return {
        "prompts": prompts,
        "tool_mapping": tool_mapping
    }
```

### 2.7 routes.py

**修改内容：**

- 添加 MCP 相关的 API 路由
- 处理工具调用请求

**示例：**

```python
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
```

### 2.8 产品文档

**修改内容：**

- 添加 MCP 相关的产品功能描述
- 更新技术架构图和流程说明
- 说明新的配置文件结构和加载方式

### 2.9 接口文档

**修改内容：**

- 添加 MCP 相关的接口说明
- 更新配置文件和参数说明
- 说明新的文件路径处理方式

## 3. 验证方法

### 3.1 配置验证

- 检查 `mcp_tool` 目录中的配置文件格式是否正确
- 验证 `.env` 文件中的环境变量配置是否正确
- 验证服务器连接是否正常

### 3.2 功能验证

- 测试 MCP 工具调用是否成功
- 验证工具响应是否正确
- 测试文件路径处理是否正确

### 3.3 文档验证

- 检查文档是否完整
- 验证文档是否准确反映系统功能

### 3.4 MCP 服务器安装和测试

**文件系统服务器测试：**

1. 确保 `mcp_servers/filesystem_server.py` 存在
2. 测试命令：
   ```bash
   python -m src.main
   ```
3. 使用 WebSocket 客户端测试文件操作功能

**Word 服务器测试：**

1. 安装依赖：
   ```bash
   pip install python-docx
   ```
2. 确保 `mcp_servers/Office-Word-MCP-Server/word_mcp_server.py` 存在
3. 测试创建文档功能

**Excel 服务器测试：**

1. 安装依赖：
   ```bash
   pip install openpyxl
   ```
2. 确保 `mcp_servers/excel-mcp-server/src/excel_mcp/__main__.py` 存在
3. 测试创建工作簿功能

**PDF 服务器测试：**

1. 安装依赖：
   ```bash
   pip install PyPDF2>=3.0.0 requests>=2.31.0
   ```
2. 确保 `mcp_servers/pdf-reader-mcp/src/server.py` 存在
3. 测试读取本地 PDF 文件功能

**通用测试脚本：**

```python
import asyncio
import websockets
import json

async def test_mcp_tool(server_name, tool_name, parameters):
    async with websockets.connect("ws://localhost:52431/ws") as websocket:
        test_data = {
            "type": "execute",
            "id": "1",
            "function": "execute_mcp_tool",
            "parameters": {
                "server_name": server_name,
                "tool_name": tool_name,
                "parameters": parameters
            }
        }

        await websocket.send(json.dumps(test_data))
        response = await websocket.recv()
        print(f"Response for {tool_name}:", response)

# 测试文件系统服务器
asyncio.run(test_mcp_tool("filesystem", "list_directory", {"path": "/"}))

# 测试PDF服务器
asyncio.run(test_mcp_tool("pdf", "read_local_pdf", {"path": "/sample.pdf"}))
```

## 4. 常见问题

### 4.1 配置错误

- **YAML 文件格式错误**：检查 `mcp_tool` 目录中的配置文件格式
- **环境变量配置错误**：检查 `.env` 文件中的 `BASE_DIR` 配置
- **服务器路径错误**：确保 `args` 中的路径指向正确的服务器脚本

### 4.2 连接失败

- **依赖未安装**：确保安装了所有必要的依赖包
- **服务器脚本不存在**：检查服务器脚本路径是否正确
- **Python 路径问题**：确保 `PYTHONPATH` 环境变量设置正确

### 4.3 工具调用失败

- **参数错误**：检查工具参数是否正确
- **文件路径错误**：确保文件路径格式正确，以 `/` 开头
- **权限不足**：确保文件操作在 `BASE_DIR` 目录内

### 4.4 服务器特定问题

- **Word 服务器**：
  - **ModuleNotFoundError: No module named 'docx'**：安装 python-docx 依赖
  - **FileNotFoundError**：确保文档路径正确

- **Excel 服务器**：
  - **ModuleNotFoundError: No module named 'openpyxl'**：安装 openpyxl 依赖
  - **PermissionError**：确保有写入权限

- **PDF 服务器**：
  - **ModuleNotFoundError: No module named 'PyPDF2'**：安装 PyPDF2 依赖
  - **URLError**：确保网络连接正常

## 5. 最佳实践

- **配置管理**：
  - 使用版本控制管理配置文件
  - 定期备份配置文件
  - 遵循命名规范和文档标准

- **环境设置**：
  - 所有 MCP 服务器的安装和运行都应在虚拟环境中进行
  - 为每个 MCP 服务器安装必要的依赖
  - 确保 `BASE_DIR` 目录存在且有正确的权限

- **开发测试**：
  - 测试新配置后再部署到生产环境
  - 测试工具调用时使用 WebSocket 通信，确保端到端功能正常
  - 遵循文件路径规范，使用一致的参数命名（如 filepath）

- **安全注意事项**：
  - 确保所有文件操作都限制在 `BASE_DIR` 目录内
  - 定期检查服务器配置，确保没有安全漏洞
  - 使用强密码保护敏感操作
