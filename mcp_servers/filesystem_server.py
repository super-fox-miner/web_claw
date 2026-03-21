#!/usr/bin/env python3
"""
Filesystem MCP Server using FastMCP
"""
import sys
import os
import time
import threading
from fastmcp import FastMCP

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# 文件锁字典，用于实现并发控制
file_locks = {}
lock_lock = threading.Lock()  # 用于保护file_locks字典的锁

class ReadWriteLock:
    """读写锁类，实现读写分离
    - 允许多个读操作同时进行
    - 写操作会阻塞所有其他操作（包括读操作）
    - 写操作之间互斥
    - 读操作会等待写操作完成后再执行
    """
    def __init__(self, file_path):
        self.file_path = file_path
        self._read_ready = threading.Condition(threading.RLock())
        self._readers = 0
        self._writers = 0
        self._write_waiters = 0
    
    def acquire_read(self, timeout=30):
        """获取读锁，支持超时
        读操作会等待写操作完成后再执行
        """
        start_time = time.time()
        while time.time() - start_time < timeout:
            with self._read_ready:
                if self._writers == 0 and self._write_waiters == 0:
                    # 只有当没有写操作且没有写操作等待时，才能获取读锁
                    # 这样可以避免写操作饿死
                    self._readers += 1
                    return True
                self._read_ready.wait(0.1)  # 等待0.1秒后重试
        return False
    
    def release_read(self):
        """释放读锁"""
        with self._read_ready:
            self._readers -= 1
            if self._readers == 0:
                self._read_ready.notify_all()
    
    def acquire_write(self, timeout=30):
        """获取写锁，支持超时
        写操作会等待所有读操作完成后再执行
        """
        start_time = time.time()
        while time.time() - start_time < timeout:
            with self._read_ready:
                if self._readers == 0 and self._writers == 0:
                    self._writers += 1
                    return True
                self._write_waiters += 1
                try:
                    self._read_ready.wait(0.1)  # 等待0.1秒后重试
                finally:
                    self._write_waiters -= 1
        return False
    
    def release_write(self):
        """释放写锁"""
        with self._read_ready:
            self._writers -= 1
            self._read_ready.notify_all()

def get_file_lock(file_path):
    """获取或创建文件锁"""
    with lock_lock:
        if file_path not in file_locks:
            file_locks[file_path] = ReadWriteLock(file_path)
        return file_locks[file_path]


class FilesystemMCPServer:
    def __init__(self, server_name):
        self.server_name = server_name
        self.mcp = FastMCP("Filesystem Server")
        # 加载环境变量
        self.base_dir = self._load_base_dir()
        
    def _load_base_dir(self):
        """从.env文件加载BASE_DIR"""
        env_file = os.path.join(os.path.dirname(__file__), '..', '.env')
        if os.path.exists(env_file):
            with open(env_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        key, value = line.split('=', 1)
                        if key == 'BASE_DIR':
                            return value.strip()
        # 默认使用当前工作目录
        return os.getcwd()
        
    def resolve_path(self, path, operation):
        """解析路径，确保在允许的目录内并具有相应权限"""
        # 简化路径解析，使用.env中的BASE_DIR
        if path.startswith('/'):
            # 移除开头的斜杠
            path = path[1:]
        # 使用.env中配置的BASE_DIR
        base_dir = self.base_dir
        # 构建完整路径
        full_path = os.path.join(base_dir, path)
        # 规范化路径
        full_path = os.path.normpath(full_path)
        
        # 恢复安全检查 - 确保路径在允许范围内
        normalized_path = os.path.normpath(full_path)
        normalized_base = os.path.normpath(base_dir)
        if not normalized_path.startswith(normalized_base):
            raise PermissionError(f"权限不足：文件路径 {path} 超出允许范围")
        
        return full_path
        
    def register_tools(self):
        """注册所有工具"""
        
        @self.mcp.tool()
        def write_file(path: str, content: str) -> str:
            """创建新文件或覆盖现有文件"""
            try:
                full_path = self.resolve_path(path, "write")
                # 获取写锁
                file_lock = get_file_lock(full_path)
                if not file_lock.acquire_write():
                    return f"文件锁定失败，请稍后重试"
                
                try:
                    os.makedirs(os.path.dirname(full_path), exist_ok=True)
                    with open(full_path, "w", encoding="utf-8") as f:
                        f.write(content)
                    return f"文件写入成功: {path}"
                finally:
                    file_lock.release_write()
            except Exception as e:
                return f"文件写入失败: {str(e)}"
        
        @self.mcp.tool()
        def append_file(path: str, content: str) -> str:
            """追加内容到文件末尾"""
            try:
                full_path = self.resolve_path(path, "write")
                # 获取写锁
                file_lock = get_file_lock(full_path)
                if not file_lock.acquire_write():
                    return f"文件锁定失败，请稍后重试"
                
                try:
                    # 确保目录存在（处理相对路径的情况）
                    dir_name = os.path.dirname(full_path)
                    if dir_name:
                        os.makedirs(dir_name, exist_ok=True)
                    with open(full_path, "a", encoding="utf-8") as f:
                        f.write(content)
                    return f"文件追加成功: {path}"
                finally:
                    file_lock.release_write()
            except Exception as e:
                return f"文件追加失败: {str(e)}"
        
        @self.mcp.tool()
        def delete_content(path: str, start_pos: int, end_pos: int) -> str:
            """删除文件中指定位置的内容（从start_pos到end_pos，不包含end_pos）"""
            try:
                full_path = self.resolve_path(path, "write")
                # 获取写锁
                file_lock = get_file_lock(full_path)
                if not file_lock.acquire_write():
                    return f"文件锁定失败，请稍后重试"
                
                try:
                    with open(full_path, "r", encoding="utf-8") as f:
                        content = f.read()
                    
                    if start_pos < 0 or end_pos > len(content) or start_pos >= end_pos:
                        return f"删除位置无效: start_pos={start_pos}, end_pos={end_pos}, 文件长度={len(content)}"
                    
                    new_content = content[:start_pos] + content[end_pos:]
                    with open(full_path, "w", encoding="utf-8") as f:
                        f.write(new_content)
                    return f"内容删除成功: 删除了{end_pos - start_pos} 个字符"
                finally:
                    file_lock.release_write()
            except Exception as e:
                return f"内容删除失败: {str(e)}"
        
        @self.mcp.tool()
        def delete_lines(path: str, start_line: int, end_line: int) -> str:
            """删除文件中指定行范围的内容（行号从1开始，包含start_line和end_line）"""
            try:
                full_path = self.resolve_path(path, "write")
                # 获取写锁
                file_lock = get_file_lock(full_path)
                if not file_lock.acquire_write():
                    return f"文件锁定失败，请稍后重试"
                
                try:
                    with open(full_path, "r", encoding="utf-8") as f:
                        lines = f.readlines()
                    
                    if start_line < 1 or end_line > len(lines) or start_line > end_line:
                        return f"行号无效: start_line={start_line}, end_line={end_line}, 文件总行数={len(lines)}"
                    
                    deleted_lines = lines[start_line-1:end_line]
                    new_lines = lines[:start_line-1] + lines[end_line:]
                    with open(full_path, "w", encoding="utf-8") as f:
                        f.writelines(new_lines)
                    return f"行删除成功: 删除了{end_line - start_line + 1} 行"
                finally:
                    file_lock.release_write()
            except Exception as e:
                return f"行删除失败: {str(e)}"
        
        @self.mcp.tool()
        def read_file(path: str) -> str:
            """读取文件的全部内容"""
            try:
                full_path = self.resolve_path(path, "read")
                # 获取读锁（允许多个读操作同时进行）
                file_lock = get_file_lock(full_path)
                if not file_lock.acquire_read():
                    return f"文件锁定失败，请稍后重试"
                
                try:
                    with open(full_path, "r", encoding="utf-8") as f:
                        return f.read()
                finally:
                    file_lock.release_read()
            except Exception as e:
                return f"文件读取失败: {str(e)}"
        
        @self.mcp.tool()
        def create_directory(path: str) -> str:
            """创建新目录或确保其存在"""
            try:
                full_path = self.resolve_path(path, "write")
                os.makedirs(full_path, exist_ok=True)
                return f"目录创建成功: {path}"
            except Exception as e:
                return f"目录创建失败: {str(e)}"
        
        @self.mcp.tool()
        def list_directory(path: str) -> str:
            """列出目录内容"""
            try:
                full_path = self.resolve_path(path, "read")
                items = []
                for item in os.listdir(full_path):
                    item_path = os.path.join(full_path, item)
                    if os.path.isdir(item_path):
                        items.append(f"[DIR] {item}")
                    else:
                        items.append(f"[FILE] {item}")
                return "\n".join(items)
            except Exception as e:
                return f"目录列出失败: {str(e)}"
    
    def run(self):
        """运行服务器"""
        self.register_tools()
        print(f"Starting Filesystem MCP Server with stdio transport...")
        self.mcp.run(transport='stdio')


def main():
    if len(sys.argv) < 2:
        print("Usage: python filesystem_server.py <server_name>")
        sys.exit(1)
    
    server_name = sys.argv[1]
    server = FilesystemMCPServer(server_name)
    
    try:
        server.run()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
