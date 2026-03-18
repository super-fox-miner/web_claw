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
        elif function_name == 'query_memory':
            query = parameters.get('query')
            top_k = parameters.get('top_k', 5)
            filters = parameters.get('filters')
            rules = memory_system.query_memory(query, top_k, filters)
            return {"success": True, "output": rules}
        
        elif function_name == 'add_rule':
            rule_name = parameters.get('rule_name')
            content = parameters.get('content')
            domain = parameters.get('domain')
            tags = parameters.get('tags')
            result = memory_system.add_rule(rule_name, content, domain, tags)
            return result
        
        elif function_name == 'delete_rule':
            rule_id = parameters.get('rule_id')
            result = memory_system.delete_rule(rule_id)
            return result
        
        elif function_name == 'record':
            task_chain = parameters.get('task_chain')
            current_task = parameters.get('current_task')
            next_task = parameters.get('next_task')
            # 处理 next_task 为 None 的情况
            if next_task is None:
                next_task = "无"
            result = memory_system.record(task_chain, current_task, next_task)
            return result
        
        elif function_name == 'get_memory_tool_documentation':
            documentation = memory_system.get_memory_tool_documentation()
            return {"success": True, "output": documentation}
        
        elif function_name == 'help':
            result = memory_system.help()
            return {"success": True, "output": result}
        
        else:
            return {"success": False, "error": f"未知内联函数：{function_name}"}
    except Exception as e:
        return {"success": False, "error": str(e)}
