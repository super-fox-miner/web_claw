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
        # 确保向量存储目录存在
        vector_store_dir = os.path.join(self.memory_dir, "vector_store")
        os.makedirs(vector_store_dir, exist_ok=True)
        
        # 初始化ChromaDB客户端
        self.chroma_client = chromadb.PersistentClient(
            path=vector_store_dir,
            settings=Settings(
                anonymized_telemetry=False
            )
        )
        
        # 初始化嵌入模型
        embedding_model_path = os.getenv('EMBEDDING_MODEL_PATH', './models/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')
        self.embedding_model = SentenceTransformer(embedding_model_path)
        
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
            metadata["tags"] = ",".join(tags)
        
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
        
        # 构建where条件
        where = None
        if filters:
            where = {}
            for key, value in filters.items():
                where[key] = value
        
        # 搜索向量数据库
        results = self.vector_collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where,
            include=["documents", "metadatas", "distances"]
        )
        
        # 格式化结果
        formatted_results = []
        ids = results.get("ids", [[]])[0]
        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]
        
        for id, document, metadata, distance in zip(ids, documents, metadatas, distances):
            # 处理tags字段
            if "tags" in metadata and isinstance(metadata["tags"], str):
                metadata["tags"] = metadata["tags"].split(",")
            
            formatted_results.append({
                "id": id,
                "rule_name": metadata.get("rule_name"),
                "content": document,
                "similarity": 1 - distance,
                "metadata": metadata
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
    
    # 全局计数器
    record_count = 0
    
    def record(self, task_chain: str = "", current_task: str = "无", next_task: str = "无", context: str = "无", rule: list = [], use_tool: bool = None, new_record: bool = False) -> Dict[str, Any]:
        """记录任务进度"""
        try:
            # 检查use_tool是否为空
            if use_tool is None:
                return {"success": False, "error": "use_tool不能为空"}
            
            # 增加全局计数器
            MemorySystem.record_count += 1
            # 计数器到14就清零
            if MemorySystem.record_count >= 14:
                MemorySystem.record_count = 0
            
            # 创建任务记录
            task_record = {
                "task_chain": task_chain,
                "current_task": current_task,
                "next_task": next_task,
                "context": context,
                "rule": rule,
                "use_tool": use_tool
            }
            
            # 处理new_record为True的情况
            if new_record:
                # 新记录时检查传入的task_chain是否为空
                if not task_chain:
                    return {"success": False, "error": "任务链不能为空"}
                memory = {
                    "record": task_record,
                    "last_updated": datetime.now().isoformat() + "Z"
                }
            else:
                # 加载短期记忆
                memory = {"record": {}, "last_updated": datetime.now().isoformat() + "Z"}
                if os.path.exists(self.short_memory_file):
                    try:
                        with open(self.short_memory_file, 'r', encoding='utf-8') as f:
                            file_content = f.read().strip()
                            if file_content:
                                memory = json.loads(file_content)
                    except (json.JSONDecodeError, Exception):
                        memory = {"record": {}, "last_updated": datetime.now().isoformat() + "Z"}
                
                # 检查现有记录中的task_chain是否有内容
                if 'record' in memory and 'task_chain' in memory['record']:
                    if not memory['record']['task_chain']:
                        return {"success": False, "error": "任务链不能为空"}
                
                # 覆盖记录
                memory["record"] = task_record
            
            memory["last_updated"] = datetime.now().isoformat() + "Z"
            
            # 保存短期记忆
            with open(self.short_memory_file, 'w', encoding='utf-8') as f:
                json.dump(memory, f, indent=2, ensure_ascii=False)
            
            # 构建输出
            if use_tool:
                output = f"[系统]当前完成任务{current_task}, 下一个任务{next_task}，可使用send_mcp_tool_documentation{{tool_name: str}}函数获取工具说明文档，不填写参数返回可用工具列表，完成后使用record记录进度"
            else:
                output = f"[系统]当前完成任务{current_task}, 下一个任务{next_task}，完成后使用record记录进度"
            
            # 如果下一个任务是无，加上任务完成提示
            if next_task == "无":
                output += "，如果任务完成'message'内输入任务完成"
            
            # 检查是否需要上下文提炼提醒
            if MemorySystem.record_count % 3 == 0:
                output = f"[系统]请提炼上下文信息，并删除任务链上以完成的任务，当前任务链为{task_chain}, 下一个任务{next_task}"
            
            # 检查是否需要规则回顾
            if MemorySystem.record_count % 5 == 0:
                rule_str = ",".join(rule) if rule else "无"
                output = f"[系统]回顾当前规则{rule_str}，当前任务{current_task}，下一个任务{next_task}"
            
            return {"success": True, "output": output}
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
                    "filters": "元数据过滤条件（字典，可选，例如：{'domain': 'code'}）"
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
                    "task_chain": "任务链（字符串，非必填，但为空时会报错）",
                    "current_task": "当前完成的任务（字符串，非必填，默认值为'无'）",
                    "next_task": "接下来要完成的任务（字符串，非必填，默认值为'无'）",
                    "context": "上下文信息（字符串，非必填，默认值为'无'）",
                    "rule": "规则列表（列表，非必填，默认值为[]）",
                    "use_tool": "是否调用工具（布尔值，必填，不填写则报错）",
                    "new_record": "是否是新记录（布尔值，非必填，默认值为False）"
                },
                "example": {"function": "record", "parameters": {"task_chain": "开发新功能", "current_task": "用户注册", "next_task": "邮箱验证", "context": "用户注册流程", "rule": ["注册规则1", "注册规则2"], "use_tool": true, "new_record": false}}
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
        snippet_content = """
        -query_memory{query: str, filters: dict}函数，根据用户需求和可选的元数据过滤获取相关规则
        - send_mcp_tool_documentation{tool_name: str}函数，获取MCP工具的说明文档
        注意：向量检索基于语义相似度，不需要预先定义固定的域或类别
        """
        
        return snippet_content
    
    def list_rule(self) -> List[Dict[str, Any]]:
        """列出所有规则及其ID"""
        # 从向量数据库中获取所有规则
        all_data = self.vector_collection.get()
        
        # 整理规则信息
        rules = []
        for rule_id, document, metadata in zip(all_data['ids'], all_data['documents'], all_data['metadatas']):
            # 处理tags字段
            if "tags" in metadata and isinstance(metadata["tags"], str):
                metadata["tags"] = metadata["tags"].split(",")
            
            rules.append({
                "id": rule_id,
                "rule_name": metadata.get("rule_name", "未知"),
                "content": document,
                "metadata": metadata
            })
        
        return rules
