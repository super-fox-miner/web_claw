import asyncio
import websockets
import json
import os

async def test_write_data_to_excel():
    print("开始测试write_data_to_excel函数...")
    
    excel_file = "test/test_write_data.xlsx"
    
    # 首先创建工作簿
    print("\n1. 创建Excel工作簿")
    try:
        async with websockets.connect("ws://localhost:52431/ws") as websocket:
            create_data = {
                "type": "execute",
                "id": "create_workbook",
                "function": "create_workbook",
                "parameters": {
                    "filepath": excel_file
                }
            }
            
            await websocket.send(json.dumps(create_data))
            response = await websocket.recv()
            response_data = json.loads(response)
            
            print(f"创建工作簿响应: {json.dumps(response_data, indent=2)}")
            
            if not response_data.get("success"):
                print(f"✗ 创建工作簿失败: {response_data.get('error')}")
                return
    except Exception as e:
        print(f"✗ 创建工作簿失败: {str(e)}")
        return
    
    # 创建工作表
    print("\n2. 创建工作表")
    try:
        async with websockets.connect("ws://localhost:52431/ws") as websocket:
            create_sheet_data = {
                "type": "execute",
                "id": "create_worksheet",
                "function": "create_worksheet",
                "parameters": {
                    "filepath": excel_file,
                    "sheet_name": "Sheet1"
                }
            }
            
            await websocket.send(json.dumps(create_sheet_data))
            response = await websocket.recv()
            response_data = json.loads(response)
            
            print(f"创建工作表响应: {json.dumps(response_data, indent=2)}")
            
            if not response_data.get("success"):
                print(f"✗ 创建工作表失败: {response_data.get('error')}")
                return
    except Exception as e:
        print(f"✗ 创建工作表失败: {str(e)}")
        return
    
    # 测试write_data_to_excel函数
    print("\n3. 测试write_data_to_excel函数")
    try:
        async with websockets.connect("ws://localhost:52431/ws") as websocket:
            write_data = {
                "type": "execute",
                "id": "write_data_to_excel",
                "function": "write_data_to_excel",
                "parameters": {
                    "filepath": excel_file,
                    "sheet_name": "Sheet1",
                    "data": [
                        ["姓名", "年龄", "城市"],
                        ["张三", 25, "北京"],
                        ["李四", 30, "上海"],
                        ["王五", 28, "广州"]
                    ],
                    "start_cell": "A1"
                }
            }
            
            print(f"发送请求: {json.dumps(write_data, indent=2)}")
            await websocket.send(json.dumps(write_data))
            response = await websocket.recv()
            response_data = json.loads(response)
            
            print(f"写入数据响应: {json.dumps(response_data, indent=2)}")
            
            if response_data.get("success"):
                print(f"✓ write_data_to_excel测试成功!")
                print(f"输出: {response_data.get('output')}")
            else:
                print(f"✗ write_data_to_excel测试失败: {response_data.get('error')}")
                
    except Exception as e:
        print(f"✗ write_data_to_excel测试失败: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_write_data_to_excel())
