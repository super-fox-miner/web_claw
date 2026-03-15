---
domain: code
topic: style
author: system
created_at: "2026-03-13T14:00:00Z"
updated_at: "2026-03-13T14:00:00Z"
references: 0
activation: 0.5
priority: high
related_tools:
  - write_file
  - read_file
tags:
  - python
  - coding
  - style-guide
---

# Python 代码风格指南

## 规则描述

本规则定义了 Python 代码编写的最佳风格实践，包括命名规范、缩进、注释等要求。

## 工具调用示例

### 示例：创建符合规范的 Python 文件
```json
{
  "function": "write_file",
  "parameters": {
    "path": "/example.py",
    "content": "def calculate_total(items):\n    \"\"\"计算商品总价\"\"\"\n    total = sum(item['price'] * item['quantity'] for item in items)\n    return total"
  }
}
```

## 最佳实践

- 函数名使用小写加下划线：`calculate_total`
- 类名使用驼峰命名法：`ClassName`
- 使用4个空格缩进
- 每行不超过80个字符
- 导入语句按标准库、第三方库、本地库分组

## 注意事项

- 避免使用单字符变量名（除了循环中的i,j,k）
- 函数应该有明确的文档字符串
- 避免过长的函数，建议不超过30行