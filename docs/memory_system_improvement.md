# 记忆系统改进方案

## 1. 方案概述

本方案旨在完全改造项目的记忆系统，使用向量库实现更高效、更智能的规则存储和检索功能，替代传统的基于文件系统的存储方式。

### 1.1 目标

- 移除对 pyactup 库的依赖（如果存在）
- 使用向量库实现永久记忆存储
- 设计符合向量库特点的新接口
- 提高规则检索的准确性和效率
- 保持与项目其他部分的兼容性

### 1.2 技术选型

- **向量嵌入**：sentence-transformers
- **向量存储**：ChromaDB
- **编程语言**：Python

## 2. 现有系统分析

### 2.1 现有结构

当前的记忆系统由以下部分组成：

- `MemorySystem` 类（`src/memory/system.py`）
- 规则文件存储在 `memory/rules/` 目录中
- 索引文件 `memory/index.json` 存储规则元数据
- 短期记忆文件 `memory/short_memory.json` 记录任务进度

### 2.2 现有功能

- 添加规则（`add_rule`）
- 检索规则（`retrieve_rules`）
- 记录规则使用（`use_rule`）
- 删除规则（`delete_rule`）
- 列出所有域（`list_domains`）
- 记录任务进度（`record`）
- 获取工具文档（`get_memory_tool_documentation`）
- 帮助函数（`help`）

### 2.3 存在的问题

- 规则检索基于简单的域匹配，缺乏语义理解
- 规则存储依赖文件系统，检索效率较低
- 无法根据规则内容的相似度进行检索
- `retrieve_rules` 方法设计不符合向量库的使用特点
- `use_rule` 方法在向量库场景下显得多余，因为向量检索本身就是基于相关性的

## 3. 改进方案

### 3.1 向量库的正确使用方式

在理解新的设计之前，需要先澄清向量库的正确使用方式：

#### 3.1.1 传统向量库使用流程

```
用户需求 → 生成查询向量 → 向量相似度搜索 → 返回最相关的规则
```

#### 3.1.2 为什么不需要 use_rule

在向量库场景下，`use_rule` 方法显得多余的原因：

1. **语义相关性已体现**：向量检索本身就是基于语义相似度的，返回的结果已经按相关性排序
2. **自动选择机制**：AI系统会自动选择最相关的规则，不需要显式记录"使用了某个规则"
3. **统计功能后台化**：如果需要统计规则使用情况，应该在后台自动记录，而不是作为用户接口
4. **简化交互流程**：用户只需要查询规则，不需要关心"记录使用"这个额外步骤

#### 3.1.3 为什么不需要固定的域列表

在向量库场景下，固定的域列表（如 `VALID_DOMAINS`）显得多余的原因：

1. **语义检索的优势**：向量检索本身就是基于语义相似度的，不需要预先分类
2. **自然分类**：系统会自动找到相关的内容，不需要人工预先定义类别
3. **灵活性限制**：固定的域列表限制了系统的扩展性和灵活性
4. **常规做法**：主流向量库（如 ChromaDB、Pinecone、Weaviate）都不要求预先定义固定的域

#### 3.1.4 元数据的正确使用方式

元数据在向量库中是有用的，但应该是灵活的：

1. **可选而非必需**：元数据应该是可选的，不是必需的
2. **灵活的结构**：支持任意键值对，不限制固定的字段
3. **过滤辅助**：元数据主要用于辅助过滤，不是主要的检索方式
4. **常规做法**：主流向量库都支持灵活的元数据过滤

#### 3.1.5 新的记忆系统流程

```
用户需求 → query_memory(query="用户需求") → 返回最相关的规则 → AI使用规则回答
```

### 3.2 架构设计

### 3.2 核心组件

#### 3.2.1 向量存储管理

- 使用 ChromaDB 创建和管理向量存储
- 为每个规则生成嵌入向量
- 提供基于相似度的规则检索
- 完全基于向量库存储规则，不再依赖文件系统

#### 3.2.2 记忆管理

- 设计符合向量库特点的新接口
- 实现规则的增删查功能
- 支持灵活的元数据管理
- 支持基于用户需求的语义检索
- 不使用固定的域列表，保持系统的灵活性

#### 3.2.3 任务记录
- 保持短期记忆功能不变
- 确保任务进度记录正常

### 3.3 实现细节

#### 3.3.1 依赖项

需要添加以下依赖：

```bash
pip install sentence-transformers chromadb
```

#### 3.3.2 架构变更

1. **移除文件系统依赖**
   - 不再使用 `memory/rules/` 目录存储规则文件
   - 不再使用 `index.json` 存储规则元数据
   - 完全基于向量库存储所有规则数据

2. **重新设计接口**
   - 移除 `retrieve_rules` 方法
   - 添加 `query_memory` 方法，支持基于用户需求的语义检索
   - 移除 `use_rule` 方法，因为向量检索本身就是基于相关性的
   - 移除 `list_domains` 方法，不再使用固定的域列表
   - 保持其他核心功能的兼容性

3. **向量存储设计**
   - 为每个规则生成唯一ID
   - 存储规则内容、灵活的元数据和向量嵌入
   - 支持灵活的元数据过滤，不限制固定的域

### 3.4 兼容性考虑

- 保持与项目其他部分的接口兼容
- 确保任务记录功能正常
- 提供平滑的迁移路径

## 4. 实现步骤

### 4.1 步骤 1：添加依赖

在项目的 `requirements.txt` 文件中添加所需依赖。

### 4.2 步骤 2：完全重写 MemorySystem 类

- 移除文件系统相关代码
- 实现向量存储相关功能
- 设计新的接口方法
- 保持必要的兼容性

### 4.3 步骤 3：数据迁移（可选）

- 从现有文件系统规则迁移到向量存储
- 确保所有现有规则都能正确导入

### 4.4 步骤 4：测试

- 测试新接口的功能
- 测试向量相似度检索的准确性
- 测试系统性能
- 确保与项目其他部分的兼容性

## 5. 预期效果

### 5.1 性能提升

- 规则检索速度提高
- 内存使用更加高效
- 支持更大规模的规则存储

### 5.2 功能增强

- 支持基于语义的规则检索
- 提高规则匹配的准确性
- 支持更复杂的查询场景
- 简化系统架构

### 5.3 兼容性保证

- 与项目其他部分的接口兼容
- 保持任务记录功能
- 提供清晰的使用文档

## 6. 代码实现

### 6.1 新的 MemorySystem 类

```python
import os
import json
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings

class MemorySystem:
    def __init__(self, memory_dir: str = "memory"):
        """初始化记忆系统"""
        self.memory_dir = memory_dir
        self.short_memory_file = os.path.join(memory_dir, "short_memory.json")
        
        # 确保目录结构存在
        os.makedirs(self.memory_dir, exist_ok=True)
        
        # 初始化短期记忆文件
        self._init_short_memory()
        
        # 初始化向量存储
        self._init_vector_store()
    
    def _init_vector_store(self):
        """初始化向量存储"""
        # 初始化ChromaDB客户端
        self.chroma_client = chromadb.Client(Settings(
            persist_directory=os.path.join(self.memory_dir, "vector_store"),
            anonymized_telemetry=False
        ))
        
        # 初始化嵌入模型
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # 创建或获取向量集合
        self.vector_collection = self.chroma_client.get_or_create_collection(
            name="rules",
            metadata={"description": "存储规则的向量集合"}
        )
    
    def _init_short_memory(self):
        """初始化短期记忆文件"""
        if not os.path.exists(self.short_memory_file):
            initial_memory = {
                "records": [],
                "last_updated": datetime.now().isoformat() + "Z"
            }
            with open(self.short_memory_file, 'w', encoding='utf-8') as f:
                json.dump(initial_memory, f, indent=2, ensure_ascii=False)
    
    def add_rule(self, rule_name: str, content: str, domain: Optional[str] = None, tags: Optional[List[str]] = None) -> Dict[str, Any]:
        """添加新规则"""
        # 生成唯一ID
        rule_id = f"{rule_name}_{int(time.time())}"
        
        # 准备元数据
        now = datetime.now().isoformat() + "Z"
        metadata = {
            "rule_name": rule_name,
            "created_at": now,
            "updated_at": now,
        }
        
        # 添加可选的域和标签
        if domain:
            metadata["domain"] = domain
        if tags:
            metadata["tags"] = tags
        
        # 生成嵌入向量
        embedding = self.embedding_model.encode(content).tolist()
        
        # 存储到向量数据库
        self.vector_collection.add(
            documents=[content],
            embeddings=[embedding],
            metadatas=[metadata],
            ids=[rule_id]
        )
        
        return {"success": True, "output": f"Rule '{rule_name}' added successfully with ID: {rule_id}"}
    
    def query_memory(self, query: str, top_k: int = 5, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """基于用户需求查询相关规则"""
        # 生成查询向量
        query_embedding = self.embedding_model.encode(query).tolist()
        
        # 搜索向量数据库（支持可选的元数据过滤）
        results = self.vector_collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=filters,  # 支持灵活的元数据过滤
            include=["documents", "metadatas", "distances"]
        )
        
        # 格式化结果
        formatted_results = []
        for i, (id, document, metadata, distance) in enumerate(zip(
            results.get("ids", [[]])[0],
            results.get("documents", [[]])[0],
            results.get("metadatas", [[]])[0],
            results.get("distances", [[]])[0]
        )):
            formatted_results.append({
                "id": id,
                "rule_name": metadata.get("rule_name"),
                "content": document,
                "similarity": 1 - distance,  # 将距离转换为相似度
                "metadata": metadata  # 返回完整的元数据
            })
        
        # 按相似度排序
        formatted_results.sort(key=lambda x: x["similarity"], reverse=True)
        
        return formatted_results
    
    def delete_rule(self, rule_id: str) -> Dict[str, Any]:
        """删除规则"""
        try:
            # 从向量数据库中删除
            self.vector_collection.delete(ids=[rule_id])
            return {"success": True, "output": f"Rule {rule_id} deleted successfully"}
        except Exception as e:
            return {"success": False, "error": f"Failed to delete rule: {str(e)}"}
    
    def record(self, task_chain: str, current_task: str, next_task: str) -> Dict[str, Any]:
        """记录任务进度"""
        try:
            # 创建任务记录
            task_record = {
                "task_chain": task_chain,
                "current_task": current_task,
                "next_task": next_task
            }
            
            # 加载短期记忆
            memory = {"records": [], "last_updated": datetime.now().isoformat() + "Z"}
            if os.path.exists(self.short_memory_file):
                try:
                    with open(self.short_memory_file, 'r', encoding='utf-8') as f:
                        file_content = f.read().strip()
                        if file_content:  # 确保文件内容不为空
                            memory = json.loads(file_content)
                except (json.JSONDecodeError, Exception):
                    # 如果文件损坏或为空，使用默认空结构
                    memory = {"records": [], "last_updated": datetime.now().isoformat() + "Z"}
            
            # 添加新记录
            record = {
                "id": str(int(time.time() * 1000)),
                "content": task_record,
                "timestamp": datetime.now().isoformat() + "Z"
            }
            memory["records"].append(record)
            
            # 限制最多20条记录，超过时删除最旧的一条
            if len(memory["records"]) > 20:
                memory["records"].pop(0)
            
            memory["last_updated"] = datetime.now().isoformat() + "Z"
            
            # 保存短期记忆
            with open(self.short_memory_file, 'w', encoding='utf-8') as f:
                json.dump(memory, f, indent=2, ensure_ascii=False)
            
            # 返回格式化消息
            return {"success": True, "output": f"已完成{current_task}任务，下一步完成{next_task}任务，可以使用help获取规则和工具信息"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_memory_tool_documentation(self, action: Optional[str] = None) -> Dict[str, Any]:
        """获取记忆工具说明文档"""
        full_docs = {
            "query_memory": {
                "description": "基于用户需求查询相关规则",
                "parameters": {
                    "query": "用户需求描述（字符串，必需）",
                    "top_k": "返回规则数量（整数，默认5）",
                    "filters": "元数据过滤条件（字典，可选，例如：{'domain': 'code', 'tags': ['optimization']}）"
                },
                "example": {"function": "query_memory", "parameters": {"query": "如何优化Python代码", "top_k": 3, "filters": {"domain": "code"}}}
            },
            "add_rule": {
                "description": "添加新规则",
                "parameters": {
                    "rule_name": "规则名称（字符串，必需）",
                    "content": "规则内容（字符串，必需）",
                    "domain": "规则领域（字符串，可选，不限制固定值）",
                    "tags": "规则标签（字符串列表，可选）"
                },
                "example": {"function": "add_rule", "parameters": {"rule_name": "Python代码优化", "content": "...", "domain": "code", "tags": ["optimization", "performance"]}}
            },
            "delete_rule": {
                "description": "删除规则",
                "parameters": {
                    "rule_id": "规则ID（字符串，必需）"
                },
                "example": {"function": "delete_rule", "parameters": {"rule_id": "python_optimization_1234567890"}}
            },

            "record": {
                "description": "记录任务进度",
                "parameters": {
                    "task_chain": "任务链（字符串，必需）",
                    "current_task": "当前完成的任务（字符串，必需）",
                    "next_task": "接下来要完成的任务（字符串，必需）"
                },
                "example": {"function": "record", "parameters": {"task_chain": "开发新功能", "current_task": "用户注册", "next_task": "邮箱验证"}}
            }
        }
        
        if action == "add":
            return {
                "add_rule": full_docs["add_rule"],
                "delete_rule": full_docs["delete_rule"]
            }
        elif action == "use":
            return {
                "query_memory": full_docs["query_memory"]
            }
        else:
            return full_docs

    def help(self) -> str:
        """帮助函数，输出指定代码片段"""
        # 硬编码输出指定代码片段
        snippet_content = """
        -query_memory{query: str, filters: dict}函数，根据用户需求和可选的元数据过滤获取相关规则
        - send_mcp_tool_documentation{tool_name: str}函数，获取MCP工具的说明文档
        注意：向量检索基于语义相似度，不需要预先定义固定的域或类别
        """
        
        return snippet_content
```

### 6.2 依赖项配置

在 `requirements.txt` 文件中添加：

```
sentence-transformers
chromadb
```

## 7. 测试计划

### 7.1 功能测试

- **规则管理**：测试添加、查询、使用和删除规则的功能
- **向量搜索**：测试基于语义的规则检索
- **兼容性**：确保与项目其他部分的接口兼容
- **任务记录**：测试任务进度记录功能

### 7.2 性能测试

- **检索速度**：测试不同规模规则库的检索速度
- **内存使用**：测试系统内存使用情况
- **存储效率**：测试向量存储的空间效率

### 7.3 边界测试

- **空规则库**：测试空规则库的处理
- **大型规则**：测试大型规则的处理
- **高频操作**：测试高频添加/删除/查询操作

## 8. 风险评估

### 8.1 潜在风险

- **依赖项问题**：sentence-transformers 和 chromadb 的安装和兼容性
- **性能问题**：向量嵌入和搜索可能在大规模规则库中性能下降
- **兼容性问题**：与项目其他部分的接口可能需要调整

### 8.2 缓解措施

- **依赖项管理**：在测试环境中充分测试依赖项
- **性能优化**：考虑使用更轻量级的嵌入模型
- **接口设计**：保持核心接口的兼容性

## 9. 结论

本方案通过完全改造记忆系统，使用向量库技术实现了更智能、更高效的规则存储和检索功能。

### 主要改进

1. **全新的接口设计**：移除了不符合向量库特点的 `retrieve_rules` 和 `use_rule` 方法，添加了 `query_memory` 方法，支持基于用户需求的语义检索

2. **完全基于向量存储**：不再依赖文件系统存储规则，所有规则都存储在 ChromaDB 中，提高了检索效率和可靠性

3. **智能语义检索**：使用 sentence-transformers 生成向量嵌入，实现了基于语义的规则检索，提高了规则匹配的准确性

4. **简化的架构**：移除了文件系统相关的代码和多余的 `use_rule` 方法，简化了系统架构，降低了维护成本

5. **保持兼容性**：保持了与项目其他部分的接口兼容，确保系统能够平滑过渡

该方案不仅解决了当前系统的局限性，还为未来的扩展提供了更灵活的基础。通过向量存储，系统可以更好地理解用户需求和规则内容，提供更准确的检索结果，从而提高整个项目的智能化水平。

## 10. 接口文件修改

为了适配新的记忆系统，需要更新以下接口文件：

### 10.1 tool_mapping.yml

```yaml
# 工具映射配置
inline_tools:
  - name: send_mcp_tool_documentation
    description: 获取MCP工具的说明文档
    parameters:
      tool_name: string
    
  # 记忆系统工具
  - name: get_memory_tool_documentation
    description: 获取记忆工具的说明文档
    parameters: {}
    
  - name: query_memory
    description: 基于用户需求查询相关规则
    parameters:
      query: string
      top_k: number
      filters: object
    
  - name: add_rule
    description: 添加新规则
    parameters:
      rule_name: string
      content: string
      domain: string
      tags: array
    
  - name: delete_rule
    description: 删除规则
    parameters:
      rule_id: string
    
  - name: record
    description: 记录任务进度
    parameters:
      task_chain: string
      current_task: string
      next_task: string

  - name: help
    description: 帮助函数，输出指定代码片段
    parameters: {}

mcp_tools: []
```

### 10.2 src/functions/inline_tools.py

```python
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
```

### 10.3 接口变更说明

1. **移除的方法**：
   - `retrieve_rules`：被 `query_memory` 替代
   - `use_rule`：不再需要
   - `list_domains`：不再需要

2. **新增的方法**：
   - `query_memory`：基于用户需求的语义检索

3. **修改的方法**：
   - `add_rule`：参数调整，支持可选的 domain 和 tags
   - `delete_rule`：参数从 file_name 改为 rule_id

4. **保持不变的方法**：
   - `record`：任务进度记录
   - `help`：帮助函数
   - `get_memory_tool_documentation`：获取工具文档