#!/usr/bin/env python3
"""
删除 memory/rules 目录下的规则文件
使用 MemorySystem 类提供的方法
"""

import sys
import os

# 添加 src 目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from memory.system import MemorySystem


def main():
    """主函数"""
    # 初始化 MemorySystem
    memory = MemorySystem(memory_dir="memory")
    
    print("=" * 50)
    print("规则文件删除工具")
    print("=" * 50)
    print()
    
    # 获取所有域
    domains = memory.list_domains()
    
    # 收集所有规则
    all_rules = []
    for domain in domains:
        rules = memory.retrieve_rules(domain=domain, top_k=100)
        for rule in rules:
            all_rules.append({
                "file": rule["file"],
                "domain": rule["domain"],
                "topic": rule["topic"]
            })
    
    if not all_rules:
        print("当前没有规则文件")
        return
    
    # 去重并排序
    seen = set()
    unique_rules = []
    for rule in all_rules:
        if rule["file"] not in seen:
            seen.add(rule["file"])
            unique_rules.append(rule)
    
    unique_rules.sort(key=lambda x: x["file"])
    
    print("当前规则文件列表:")
    for i, rule in enumerate(unique_rules, 1):
        print(f"  {i}. {rule['file']} (domain: {rule['domain']}, topic: {rule['topic']})")
    print()
    
    # 交互式选择
    print("操作选项:")
    print("  1. 删除指定规则 (输入序号或文件名)")
    print("  2. 删除所有规则")
    print("  3. 退出")
    print()
    
    choice = input("请选择操作 (1/2/3): ").strip()
    
    if choice == '1':
        user_input = input("请输入要删除的规则序号或文件名: ").strip()
        
        # 判断是序号还是文件名
        if user_input.isdigit():
            idx = int(user_input) - 1
            if 0 <= idx < len(unique_rules):
                filename = unique_rules[idx]["file"]
            else:
                print("无效的序号")
                return
        else:
            filename = user_input
            if not filename.endswith('.md'):
                filename += '.md'
        
        # 确认删除
        confirm = input(f"确认删除 '{filename}'? (yes/no): ")
        if confirm.lower() == 'yes':
            result = memory.delete_rule(filename)
            if result["success"]:
                print(f"成功: {result['output']}")
            else:
                print(f"失败: {result.get('error', '未知错误')}")
        else:
            print("已取消删除")
    
    elif choice == '2':
        print(f"即将删除 {len(unique_rules)} 个规则文件:")
        for rule in unique_rules:
            print(f"  - {rule['file']}")
        
        confirm = input("\n确认删除全部? (yes/no): ")
        if confirm.lower() == 'yes':
            success_count = 0
            for rule in unique_rules:
                result = memory.delete_rule(rule["file"])
                if result["success"]:
                    print(f"已删除: {rule['file']}")
                    success_count += 1
                else:
                    print(f"删除失败: {rule['file']} - {result.get('error', '未知错误')}")
            print(f"\n成功删除 {success_count}/{len(unique_rules)} 个规则文件")
        else:
            print("已取消删除操作")
    
    elif choice == '3':
        print("已退出")
    
    else:
        print("无效的选择")


if __name__ == "__main__":
    main()
