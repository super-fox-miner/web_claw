import os
import yaml

def get_mcp_tools():
    """
    获取所有MCP工具的说明文档
    """
    mcp_tools_dir = os.path.join(os.path.dirname(__file__), "mcp_tool")
    tools_info = []
    
    # 遍历mcp_tool目录下的所有yml文件
    for file_name in os.listdir(mcp_tools_dir):
        if file_name.endswith(".yml"):
            file_path = os.path.join(mcp_tools_dir, file_name)
            with open(file_path, "r", encoding="utf-8") as f:
                try:
                    tool_data = yaml.safe_load(f)
                    tools_info.append(tool_data)
                except yaml.YAMLError as e:
                    print(f"读取文件 {file_name} 时出错: {str(e)}")
    
    return tools_info

def get_mcp_tool_by_name(tool_name):
    """
    根据工具名称获取工具的说明文档
    """
    mcp_tools = get_mcp_tools()
    
    for server in mcp_tools:
        for tool in server.get("tools", []):
            if tool.get("name") == tool_name:
                return tool
    
    return None

def send_mcp_tool_documentation(tool_name=None):
    """
    发送MCP工具的说明文档
    如果指定了tool_name，则发送特定工具的说明文档
    如果指定的是服务器名称，则发送该服务器的所有工具说明文档
    否则发送所有工具的说明文档
    """
    if tool_name:
        # 首先尝试查找工具
        tool = get_mcp_tool_by_name(tool_name)
        if tool:
            return tool
        
        # 如果没找到工具，尝试查找服务器
        mcp_tools = get_mcp_tools()
        for server in mcp_tools:
            if server.get("server_name") == tool_name:
                return server
        
        # 既不是工具名称也不是服务器名称
        return f"未找到工具或服务器: {tool_name}"
    else:
        return get_mcp_tools()
