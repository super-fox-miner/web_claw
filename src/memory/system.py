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
                        if file_content:
                            memory = json.loads(file_content)
                except (json.JSONDecodeError, Exception):
                    memory = {"records": [], "last_updated": datetime.now().isoformat() + "Z"}
            
            # 添加新记录
            record = {
                "id": str(int(time.time() * 1000)),
                "content": task_record,
                "timestamp": datetime.now().isoformat() + "Z"
            }
            memory["records"].append(record)
            
            # 限制最多20条记录
            if len(memory["records"]) > 20:
                memory["records"].pop(0)
            
            memory["last_updated"] = datetime.now().isoformat() + "Z"
            
            # 保存短期记忆
            with open(self.short_memory_file, 'w', encoding='utf-8') as f:
                json.dump(memory, f, indent=2, ensure_ascii=False)
            
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
        snippet_content = """
        -query_memory{query: str, filters: dict}函数，根据用户需求和可选的元数据过滤获取相关规则
        - send_mcp_tool_documentation{tool_name: str}函数，获取MCP工具的说明文档
        注意：向量检索基于语义相似度，不需要预先定义固定的域或类别
        """
        
        return snippet_content
