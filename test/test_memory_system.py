import asyncio
import websockets
import json
import time

async def send_websocket_request(function_name, parameters):
    """发送WebSocket请求并获取响应"""
    try:
        async with websockets.connect("ws://localhost:52431/ws") as websocket:
            test_data = {
                "type": "execute",
                "id": f"test_{int(time.time())}",
                "function": function_name,
                "parameters": parameters
            }

            print(f"\n发送请求: {json.dumps(test_data, indent=2, ensure_ascii=False)}")
            await websocket.send(json.dumps(test_data))
            response = await websocket.recv()
            response_data = json.loads(response)
            
            print(f"响应: {json.dumps(response_data, indent=2, ensure_ascii=False)}")
            return response_data
                
    except Exception as e:
        print(f"请求失败: {str(e)}")
        return None

async def test_memory_system():
    """测试新的记忆系统"""
    print("=" * 60)
    print("开始测试新的记忆系统（基于向量库）")
    print("=" * 60)
    
    # 测试1：添加规则1 - 写日志规则
    print("\n" + "-" * 40)
    print("测试1：添加规则 - 写日志规则")
    print("-" * 40)
    
    rule1_content = """# 写日志规则

## 规则描述
当用户说"写日志"时，AI需要：
1. 总结当前对话的上下文内容
2. 将总结内容写入日志文件
3. 日志文件格式：[时间] - [主题] - [内容摘要]
"""

    result1 = await send_websocket_request("add_rule", {
        "rule_name": "写日志规则",
        "content": rule1_content,
        "domain": "logging",
        "tags": ["日志", "总结", "文件写入"]
    })
    
    # 测试2：添加规则2 - Word文档字体规则
    print("\n" + "-" * 40)
    print("测试2：添加规则 - Word文档字体规则")
    print("-" * 40)
    
    rule2_content = """# Word文档字体规则

## 规则描述
创建Word文档时，字体设置规则：
1. 所有字体使用黑体
2. 标题使用16号字体
3. 正文使用12号字体
4. 确保文档格式统一美观
"""

    result2 = await send_websocket_request("add_rule", {
        "rule_name": "Word文档字体规则",
        "content": rule2_content,
        "domain": "word",
        "tags": ["Word", "字体", "黑体", "格式"]
    })
    
    # 测试3：查询规则 - 查询日志相关规则
    print("\n" + "-" * 40)
    print("测试3：查询规则 - 查询日志相关规则")
    print("-" * 40)
    
    result3 = await send_websocket_request("query_memory", {
        "query": "写日志总结上下文",
        "top_k": 3,
        "filters": {"domain": "logging"}
    })
    
    # 测试4：查询规则 - 查询Word相关规则
    print("\n" + "-" * 40)
    print("测试4：查询规则 - 查询Word相关规则")
    print("-" * 40)
    
    result4 = await send_websocket_request("query_memory", {
        "query": "创建Word文档字体设置",
        "top_k": 3,
        "filters": {"domain": "word"}
    })
    
    # 测试5：模拟用户场景 - "写一篇文章给我，word格式"
    print("\n" + "-" * 40)
    print("测试5：模拟用户场景 - '写一篇文章给我，word格式'")
    print("-" * 40)
    
    # 查询相关规则
    result5 = await send_websocket_request("query_memory", {
        "query": "写一篇文章给我，word格式",
        "top_k": 5
    })
    
    if result5 and result5.get("success"):
        rules = result5.get("output", [])
        
        print(f"\n找到 {len(rules)} 条相关规则：")
        for i, rule in enumerate(rules, 1):
            print(f"\n规则 {i}: {rule.get('rule_name')}")
            print(f"相似度: {rule.get('similarity', 0):.4f}")
            content = rule.get('content', '')
            if content:
                print(f"内容摘要: {content[:100]}...")
        
        # 模拟日志总结
        print("\n" + "-" * 40)
        print("日志总结：")
        print("-" * 40)
        summary = """[2026-03-18] - 用户请求：写一篇文章给我，word格式

处理过程：
1. 查询到相关规则：Word文档字体规则
2. 根据规则，创建Word文档时应使用黑体字体
3. 标题使用16号字体，正文使用12号字体
4. 确保文档格式统一美观

执行结果：
- 成功创建Word文档
- 应用黑体字体格式
- 文档格式符合规则要求
"""
        print(summary)
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_memory_system())
