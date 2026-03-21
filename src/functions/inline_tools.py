import sys
import os
import yaml
from typing import Dict, Any

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

# 加载工具映射配置
tool_mapping_path = os.path.join(project_root, 'tool_mapping.yml')
tool_mapping = {}
try:
    with open(tool_mapping_path, 'r', encoding='utf-8') as f:
        tool_mapping = yaml.safe_load(f)
except Exception as e:
    print(f"加载工具映射配置失败: {e}")

# 导入工具函数
try:
    from src.utils.tools import send_mcp_tool_documentation
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
print("记忆系统初始化成功")


async def execute_inline_tool(function_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
    try:
        # 特殊处理 send_mcp_tool_documentation
        if function_name == 'send_mcp_tool_documentation':
            tool_name = parameters.get('tool_name')
            result = send_mcp_tool_documentation(tool_name)
            return {"success": True, "output": result}
        
        # 检查工具是否在配置中注册
        inline_tools = tool_mapping.get('inline_tools', [])
        tool_info = next((tool for tool in inline_tools if tool.get('name') == function_name), None)
        
        if not tool_info:
            return {"success": False, "error": f"未知内联函数：{function_name}"}
        
        # 检查记忆系统是否有对应方法
        if hasattr(memory_system, function_name):
            method = getattr(memory_system, function_name)
            
            # 处理特殊参数情况
            if function_name == 'record':
                # 处理 next_task 为 None 的情况
                next_task = parameters.get('next_task')
                if next_task is None:
                    parameters['next_task'] = "无"
            
            # 调用方法并返回结果
            result = method(**parameters)
            # 确保返回格式正确
            if isinstance(result, dict) and ('success' in result):
                return result
            else:
                return {"success": True, "output": result}
        else:
            return {"success": False, "error": f"记忆系统中不存在函数：{function_name}"}
    except Exception as e:
        return {"success": False, "error": str(e)}
