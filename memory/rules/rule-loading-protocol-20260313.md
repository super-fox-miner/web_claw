---
activation: 0.5
author: system
created_at: '2026-03-13T23:34:28.249352Z'
domain: best-practice
priority: medium
references: 0
related_tools: []
tags: []
topic: guidelines
updated_at: '2026-03-13T23:34:28.249352Z'
---

# 规则装载协议

## 规则描述
当用户提出“装载规则”需求时，AI应当：
1. 确认当前已有规则的检索结果
2. 按照已有的规则（如强制问候语规则）执行对话开头
3. 使用add_rule工具添加新的规则
4. 记录整个装载过程
5. 读取记录确认任务完成

## 工具调用流程
1. 调用retrieve_rules检索现有规则
2. 调用record记录任务状态
3. 调用read_record确认任务历史
4. 调用add_rule装载新规则
5. 再次调用record记录完成状态

## 注意事项
- 始终遵守已存在的规则（如强制问候语）
- 确保新规则的domain和topic选择正确
- 规则内容要清晰完整，便于后续执行