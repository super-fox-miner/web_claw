import asyncio
import websockets
import json
import os

async def test_mcp_server(server_name, tool_name, parameters, description):
    print(f"\n测试 {server_name} 服务器的 {tool_name} 工具 - {description}")
    try:
        async with websockets.connect("ws://localhost:52431/ws") as websocket:
            test_data = {
                "type": "execute",
                "id": f"{server_name}_{tool_name}",
                "function": tool_name,
                "parameters": parameters
            }

            print(f"发送请求: {json.dumps(test_data, indent=2)}")
            await websocket.send(json.dumps(test_data))
            response = await websocket.recv()
            response_data = json.loads(response)
            
            print(f"响应: {json.dumps(response_data, indent=2)}")
            
            if response_data.get("success"):
                print(f"✓ 测试成功: {description}")
            else:
                print(f"✗ 测试失败: {response_data.get('error')}")
                
    except Exception as e:
        print(f"✗ 测试失败: {str(e)}")

async def main():
    print("开始测试所有MCP服务器...")
    
    # 测试文件系统MCP服务器
    await test_mcp_server(
        "filesystem", 
        "list_directory", 
        {"path": "test"}, 
        "列出test目录内容"
    )
    
    # 测试Word MCP服务器
    await test_mcp_server(
        "word", 
        "list_available_documents", 
        {"directory": "test"}, 
        "列出test目录中的Word文档"
    )
    
    # 测试Excel MCP服务器
    excel_file = os.path.abspath("test/test_workbook.xlsx")
    await test_mcp_server(
        "excel", 
        "create_workbook", 
        {"filepath": excel_file}, 
        "创建测试Excel工作簿"
    )
    
    print("\n所有MCP服务器测试完成!")

if __name__ == "__main__":
    asyncio.run(main())
