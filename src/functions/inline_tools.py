import sys
import os
from typing import Dict, Any

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

# 导入工具函数
try:
    from tools import send_mcp_tool_documentation
except ImportError as e:
    print(f"导入工具函数失败: {e}")
    # 如果导入失败，提供一个简单的实现
    def send_mcp_tool_documentation(tool_name=None):
        if tool_name:
            return f"工具 {tool_name} 的说明文档"
        else:
            return "所有MCP工具的说明文档"

# 导入记忆系统
from src.memory import MemorySystem

# 初始化记忆系统
memory_system = MemorySystem()


async def execute_inline_tool(function_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
    try:
        if function_name == 'send_mcp_tool_documentation':
            tool_name = parameters.get('tool_name')
            result = send_mcp_tool_documentation(tool_name)
            return {"success": True, "output": result}
        
        # 记忆系统工具
        elif function_name == 'retrieve_rules':
            domain = parameters.get('domain')
            topic = parameters.get('topic')
            top_k = parameters.get('top_k', 3)
            rules = memory_system.retrieve_rules(domain, topic, top_k)
            return {"success": True, "output": rules}
        
        elif function_name == 'add_rule':
            file_name = parameters.get('file_name')
            domain = parameters.get('domain')
            topic = parameters.get('topic')
            content = parameters.get('content')
            result = memory_system.add_rule(file_name, domain, topic, content)
            return result
        
        elif function_name == 'use_rule':
            file_name = parameters.get('file_name')
            result = memory_system.use_rule(file_name)
            return result
        
        elif function_name == 'delete_rule':
            file_name = parameters.get('file_name')
            result = memory_system.delete_rule(file_name)
            return result
        
        elif function_name == 'list_domains':
            domains = memory_system.list_domains()
            return {"success": True, "output": domains}
        
        elif function_name == 'list_topics':
            domain = parameters.get('domain')
            topics = memory_system.list_topics(domain)
            return {"success": True, "output": topics}
        
        elif function_name == 'record':
            content = parameters.get('content')
            result = memory_system.record(content)
            return result
        
        elif function_name == 'read_record':
            result = memory_system.read_record()
            return result
        
        elif function_name == 'get_memory_tool_documentation':
            documentation = memory_system.get_memory_tool_documentation()
            return {"success": True, "output": documentation}
        
        else:
            return {"success": False, "error": f"未知内联函数：{function_name}"}
    except Exception as e:
        return {"success": False, "error": str(e)}
