#!/usr/bin/env python3
import os
import yaml
from typing import Dict, Any, Optional


class FileAccessManager:
    """文件访问管理器，用于验证MCP服务器的文件访问权限"""
    
    def __init__(self, config_path: str = "mcp_file_access.yml"):
        """初始化文件访问管理器
        
        Args:
            config_path: 配置文件路径
        """
        self.config_path = config_path
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件
        
        Returns:
            配置字典
        """
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"加载配置文件失败: {e}")
            return {"global": {"enabled": False}, "servers": {}}
    
    def get_global_config(self) -> Dict[str, Any]:
        """获取全局配置
        
        Returns:
            全局配置字典
        """
        return self.config.get("global", {})
    
    def get_server_config(self, server_name: str) -> Optional[Dict[str, Any]]:
        """获取服务器配置
        
        Args:
            server_name: 服务器名称
            
        Returns:
            服务器配置字典，如果不存在返回None
        """
        servers = self.config.get("servers", {})
        return servers.get(server_name)
    
    def is_file_access_enabled(self, server_name: str) -> bool:
        """检查服务器是否启用了文件访问
        
        Args:
            server_name: 服务器名称
            
        Returns:
            是否启用文件访问
        """
        # 首先检查服务器特定配置
        server_config = self.get_server_config(server_name)
        if server_config is not None:
            return server_config.get("enabled", False)
        
        # 如果服务器没有特定配置，使用全局配置
        global_config = self.get_global_config()
        return global_config.get("enabled", False)
    
    def get_base_dir(self, server_name: str) -> str:
        """获取基础目录
        
        Args:
            server_name: 服务器名称
            
        Returns:
            基础目录路径
            
        Raises:
            ValueError: 基础目录未配置
        """
        # 首先检查服务器特定配置
        server_config = self.get_server_config(server_name)
        if server_config and "base_dir" in server_config:
            return server_config.get("base_dir", "")
        
        # 如果服务器没有特定配置，使用全局配置
        global_config = self.get_global_config()
        base_dir = global_config.get("base_dir", "")
        
        if not base_dir:
            raise ValueError("基础目录未配置")
        
        return base_dir
    
    def validate_path(self, server_name: str, path: str) -> str:
        """验证并解析路径
        
        Args:
            server_name: 服务器名称
            path: 相对或绝对路径
            
        Returns:
            解析后的绝对路径
            
        Raises:
            ValueError: 路径验证失败
        """
        # 检查文件访问是否启用
        if not self.is_file_access_enabled(server_name):
            raise ValueError(f"服务器 {server_name} 未启用文件访问")
        
        # 获取基础目录
        base_dir = self.get_base_dir(server_name)
        
        # 移除开头的/，使用相对路径
        while path.startswith("/"):
            path = path[1:]
        
        # 拼接完整路径
        # 确保使用正确的路径分隔符
        full_path = os.path.join(base_dir, path)
        
        # 规范化路径
        full_path = os.path.normpath(full_path)
        normalized_base_dir = os.path.normpath(base_dir)
        
        # 确保路径在base_dir内
        if not full_path.startswith(normalized_base_dir):
            raise ValueError(f"路径不在允许的目录内: {full_path}")
        
        return full_path
    
    def validate_access(self, server_name: str, path: str, operation: str) -> str:
        """验证访问权限并返回解析后的路径
        
        Args:
            server_name: 服务器名称
            path: 相对或绝对路径
            operation: 操作类型 (read, write, execute)
            
        Returns:
            解析后的绝对路径
            
        Raises:
            ValueError: 权限验证失败
        """
        # 简化版本：只验证路径，不检查具体权限
        # 只要文件访问启用且路径在允许范围内，就允许所有操作
        return self.validate_path(server_name, path)
