import os
import json
import yaml
import time
from datetime import datetime
from typing import Dict, List, Optional, Any

class MemorySystem:
    # 固定的domain选项
    VALID_DOMAINS = [
        "global",         # 全局规则（所有任务都会执行）
        "code",           # 代码相关
        "file",           # 编辑器文本处理
        "filesystem",     # 文件系统操作
        "word",           # Word文档处理
        "excel",          # Excel表格处理
    ]
    
    # 固定的topic选项（按domain分组）
    VALID_TOPICS = {
        "global": ["greeting", "response-style", "behavior", "personality"],
        "code": ["style", "structure", "optimization", "debugging", "testing"],
        "file": ["formatting", "layout", "template", "conversion", "editing"],
        "filesystem": ["file-operation", "directory-management", "path-handling", "permissions"],
        "word": ["document-creation", "formatting", "table-handling", "image-insertion", "header-footer"],
        "excel": ["worksheet-management", "data-entry", "formula-application", "chart-creation", "formatting"]
    }

    def __init__(self, memory_dir: str = "memory"):
        """初始化记忆系统"""
        self.memory_dir = memory_dir
        self.rules_dir = os.path.join(memory_dir, "rules")
        self.index_file = os.path.join(memory_dir, "index.json")
        self.short_memory_file = os.path.join(memory_dir, "short_memory.json")
        
        # 确保目录结构存在
        os.makedirs(self.rules_dir, exist_ok=True)
        
        # 初始化索引文件
        self._init_index()
        
        # 初始化短期记忆文件
        self._init_short_memory()
        
        # 初始化内存中的规则缓存
        self._rules_cache = {}
        self._load_rules_to_cache()
    
    def _init_index(self):
        """初始化索引文件"""
        if not os.path.exists(self.index_file):
            initial_index = {
                "rules": {},
                "domains": [],
                "topics": {},
                "last_updated": datetime.now().isoformat() + "Z"
            }
            with open(self.index_file, 'w', encoding='utf-8') as f:
                json.dump(initial_index, f, indent=2, ensure_ascii=False)
    
    def _init_short_memory(self):
        """初始化短期记忆文件"""
        if not os.path.exists(self.short_memory_file):
            initial_memory = {
                "records": [],
                "last_updated": datetime.now().isoformat() + "Z"
            }
            with open(self.short_memory_file, 'w', encoding='utf-8') as f:
                json.dump(initial_memory, f, indent=2, ensure_ascii=False)
    
    def _load_index(self) -> Dict[str, Any]:
        """加载索引文件"""
        with open(self.index_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _save_index(self, index: Dict[str, Any]):
        """保存索引文件"""
        index["last_updated"] = datetime.now().isoformat() + "Z"
        with open(self.index_file, 'w', encoding='utf-8') as f:
            json.dump(index, f, indent=2, ensure_ascii=False)
    
    def _load_rules_to_cache(self):
        """加载规则到内存缓存"""
        index = self._load_index()
        self._rules_cache = {}
        for rule_file, rule_data in index["rules"].items():
            self._rules_cache[rule_file] = rule_data
    
    def _parse_front_matter(self, content: str) -> tuple[Dict[str, Any], str]:
        """解析YAML Front Matter和Markdown内容"""
        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                front_matter = yaml.safe_load(parts[1])
                markdown_content = parts[2].strip()
                return front_matter, markdown_content
        return {}, content
    
    def add_rule(self, file_name: str, domain: str, topic: str, content: str) -> Dict[str, Any]:
        """添加新规则"""
        # 验证domain
        if domain not in self.VALID_DOMAINS:
            valid_domains_str = ", ".join(self.VALID_DOMAINS)
            return {
                "success": False, 
                "error": f"无效的domain: '{domain}'。有效的domain选项: {valid_domains_str}"
            }
        
        # 验证topic
        if domain not in self.VALID_TOPICS:
            return {
                "success": False, 
                "error": f"domain '{domain}' 没有对应的topic定义"
            }
        
        if topic not in self.VALID_TOPICS[domain]:
            valid_topics_str = ", ".join(self.VALID_TOPICS[domain])
            return {
                "success": False, 
                "error": f"无效的topic: '{topic}'。domain '{domain}' 的有效topic选项: {valid_topics_str}"
            }
        
        # 确保文件名以.md结尾
        if not file_name.endswith('.md'):
            file_name += '.md'
        
        # 构建文件路径
        rule_path = os.path.join(self.rules_dir, file_name)
        
        # 准备元数据
        now = datetime.now().isoformat() + "Z"
        metadata = {
            "domain": domain,
            "topic": topic,
            "author": "system",
            "created_at": now,
            "updated_at": now,
            "references": 0,
            "activation": 0.5,
            "priority": "medium",
            "related_tools": [],
            "tags": []
        }
        
        # 解析内容，提取元数据（如果有）
        if content.startswith('---'):
            front_matter, markdown_content = self._parse_front_matter(content)
            metadata.update(front_matter)
        else:
            # 构建完整的规则文件内容
            front_matter_str = yaml.dump(metadata, default_flow_style=False, allow_unicode=True)
            markdown_content = content
            content = f"---\n{front_matter_str}---\n\n{markdown_content}"
        
        # 写入规则文件
        with open(rule_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # 更新索引
        index = self._load_index()
        index["rules"][file_name] = metadata
        
        # 更新域和主题
        if domain not in index["domains"]:
            index["domains"].append(domain)
        
        if domain not in index["topics"]:
            index["topics"][domain] = []
        if topic not in index["topics"][domain]:
            index["topics"][domain].append(topic)
        
        self._save_index(index)
        
        # 更新缓存
        self._load_rules_to_cache()
        
        return {"success": True, "output": f"Rule {file_name} added successfully"}
    
    def retrieve_rules(self, domain: Optional[str] = None, topic: Optional[str] = None, top_k: int = 3) -> List[Dict[str, Any]]:
        """检索相关规则"""
        # 加载索引
        index = self._load_index()
        
        # 先收集所有 global 规则（全局规则总是被返回）
        global_rules = []
        filtered_rules = []
        
        for rule_file, rule_data in index["rules"].items():
            # 加载规则内容
            rule_path = os.path.join(self.rules_dir, rule_file)
            if not os.path.exists(rule_path):
                continue
                
            with open(rule_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            front_matter, markdown_content = self._parse_front_matter(content)
            
            rule_info = {
                "file": rule_file,
                "domain": front_matter.get("domain", "unknown"),
                "topic": front_matter.get("topic", "unknown"),
                "content": markdown_content,
                "activation": rule_data.get("activation", 0.5),
                "references": rule_data.get("references", 0)
            }
            
            # 如果是 global 规则，加入 global_rules
            if rule_data.get("domain") == "global":
                global_rules.append(rule_info)
            # 否则检查是否匹配 domain 和 topic
            elif domain and rule_data.get("domain") != domain:
                continue
            elif topic and rule_data.get("topic") != topic:
                continue
            else:
                filtered_rules.append(rule_info)
        
        # 按激活值排序
        global_rules.sort(key=lambda x: x["activation"], reverse=True)
        filtered_rules.sort(key=lambda x: x["activation"], reverse=True)
        
        # 将 global 规则放在最前面，然后是其他规则
        result = global_rules + filtered_rules
        
        # 返回前top_k个
        return result[:top_k]
    
    def use_rule(self, file_name: str) -> Dict[str, Any]:
        """记录规则使用"""
        # 确保文件名以.md结尾
        if not file_name.endswith('.md'):
            file_name += '.md'
        
        # 更新索引
        index = self._load_index()
        
        if file_name not in index["rules"]:
            return {"success": False, "error": f"Rule {file_name} not found"}
        
        # 更新使用统计
        rule_data = index["rules"][file_name]
        rule_data["references"] += 1
        rule_data["updated_at"] = datetime.now().isoformat() + "Z"
        
        # 增加激活值（0-1之间）
        rule_data["activation"] = min(1.0, rule_data["activation"] + 0.1)
        
        self._save_index(index)
        
        # 更新缓存
        self._load_rules_to_cache()
        
        return {"success": True, "output": f"Rule {file_name} usage recorded"}
    
    def delete_rule(self, file_name: str) -> Dict[str, Any]:
        """删除规则"""
        # 确保文件名以.md结尾
        if not file_name.endswith('.md'):
            file_name += '.md'
        
        # 构建文件路径
        rule_path = os.path.join(self.rules_dir, file_name)
        
        # 删除文件
        if os.path.exists(rule_path):
            os.remove(rule_path)
        
        # 更新索引
        index = self._load_index()
        
        if file_name in index["rules"]:
            del index["rules"][file_name]
            self._save_index(index)
        
        # 更新缓存
        self._load_rules_to_cache()
        
        return {"success": True, "output": f"Rule {file_name} deleted successfully"}
    
    def list_domains(self) -> List[str]:
        """列出所有域"""
        index = self._load_index()
        return index["domains"]
    
    def list_topics(self, domain: str) -> Dict[str, Any]:
        """列出指定域的所有主题和文件名"""
        index = self._load_index()
        topics = index["topics"].get(domain, [])
        
        # 收集该域下的所有文件名
        filenames = []
        for file_name, rule_data in index["rules"].items():
            if rule_data.get("domain") == domain:
                filenames.append(file_name)
        
        return {
            "topics": topics,
            "filenames": filenames
        }
    
    def record(self, content: str) -> Dict[str, Any]:
        """记录短期记忆"""
        try:
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
                "content": content,
                "timestamp": datetime.now().isoformat() + "Z"
            }
            memory["records"].append(record)
            
            # 限制最多10条记录，超过时删除最旧的一条
            if len(memory["records"]) > 10:
                memory["records"].pop(0)
            
            memory["last_updated"] = datetime.now().isoformat() + "Z"
            
            # 保存短期记忆
            with open(self.short_memory_file, 'w', encoding='utf-8') as f:
                json.dump(memory, f, indent=2, ensure_ascii=False)
            
            return {"success": True, "output": "记录成功"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def read_record(self) -> Dict[str, Any]:
        """读取短期记忆"""
        try:
            # 加载短期记忆
            if os.path.exists(self.short_memory_file):
                try:
                    with open(self.short_memory_file, 'r', encoding='utf-8') as f:
                        file_content = f.read().strip()
                        if file_content:  # 确保文件内容不为空
                            memory = json.loads(file_content)
                            return {"success": True, "output": memory}
                except (json.JSONDecodeError, Exception):
                    # 如果文件损坏或为空，返回默认空结构
                    pass
            return {"success": True, "output": {"records": [], "last_updated": datetime.now().isoformat() + "Z"}}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def new_record(self, content: str) -> Dict[str, Any]:
        """新建短期记忆（覆盖原有内容）"""
        try:
            # 创建新的记录结构
            memory = {
                "records": [
                    {
                        "id": str(int(time.time() * 1000)),
                        "content": content,
                        "timestamp": datetime.now().isoformat() + "Z"
                    }
                ],
                "last_updated": datetime.now().isoformat() + "Z"
            }
            
            # 保存短期记忆（覆盖原有内容）
            with open(self.short_memory_file, 'w', encoding='utf-8') as f:
                json.dump(memory, f, indent=2, ensure_ascii=False)
            
            return {"success": True, "output": "新建记录成功"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_memory_tool_documentation(self, action: Optional[str] = None) -> Dict[str, Any]:
        """获取记忆工具说明文档"""
        full_docs = {
            "retrieve_rules": {
                "description": "检索相关规则",
                "parameters": {
                    "domain": f"规则领域（字符串，可选，固定选项）",
                    "topic": "规则主题（字符串，可选，需与domain对应）", 
                    "top_k": "返回规则数量（整数，默认3）"
                },
                "example": {"function": "retrieve_rules", "parameters": {"domain": "code", "topic": "style", "top_k": 3}}
            },
            "add_rule": {
                "description": "添加新规则",
                "parameters": {
                    "file_name": "规则文件名（字符串，必需）",
                    "domain": f"规则领域（字符串，必需，固定选项）",
                    "topic": "规则主题（字符串，必需，需与domain对应）",
                    "content": "规则内容（字符串，必需）"
                },
                "example": {"function": "add_rule", "parameters": {"file_name": "code-style.md", "domain": "code", "topic": "style", "content": "..."}}
            },
            "use_rule": {
                "description": "记录规则使用",
                "parameters": {
                    "file_name": "规则文件名（字符串，必需）"
                },
                "example": {"function": "use_rule", "parameters": {"file_name": "code-style.md"}}
            },
            "delete_rule": {
                "description": "删除规则",
                "parameters": {
                    "file_name": "规则文件名（字符串，必需）"
                },
                "example": {"function": "delete_rule", "parameters": {"file_name": "code-style.md"}}
            },
            "list_domains": {
                "description": "列出所有域。域类型说明：\n- global: 全局规则（所有任务都会执行）\n- code: 代码相关\n- file: 编辑器文本处理\n- filesystem: 文件系统操作\n- word: Word文档处理\n- excel: Excel表格处理\n",
                "parameters": {},
                "example": {"function": "list_domains", "parameters": {}}
            },
            "list_topics": {
                "description": "列出指定域的所有主题和对应的文件名",
                "parameters": {
                    "domain": f"规则领域（字符串，必需，固定选项：{', '.join(self.VALID_DOMAINS)}"
                },
                "example": {"function": "list_topics", "parameters": {"domain": "code"}}
            },
            "record": {
                "description": "记录短期记忆",
                "parameters": {
                    "content": "记录内容（字符串，必需）"
                },
                "example": {"function": "record", "parameters": {"content": "任务需求：xxx，任务规划：xxx，任务流程：xxx"}}
            },
            "read_record": {
                "description": "读取短期记忆",
                "parameters": {},
                "example": {"function": "read_record", "parameters": {}}
            }
        }
        
        if action == "add":
            return {
                "add_rule": full_docs["add_rule"],
                "delete_rule": full_docs["delete_rule"]
            }
        elif action == "use":
            return {
                "retrieve_rules": full_docs["retrieve_rules"],
                "use_rule": full_docs["use_rule"],
                "list_domains": full_docs["list_domains"],
                "list_topics": full_docs["list_topics"]
            }
        else:
            return full_docs
