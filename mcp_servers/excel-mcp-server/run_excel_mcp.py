#!/usr/bin/env python3
"""
Excel MCP Server启动脚本
用于启动Excel MCP服务器的stdio模式
"""
import sys
import os

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# 导入并运行excel_mcp模块的stdio模式
from excel_mcp.server import run_stdio

if __name__ == "__main__":
    try:
        # 运行stdio模式
        run_stdio()
    except KeyboardInterrupt:
        print("\nShutting down server...")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("Service stopped.")