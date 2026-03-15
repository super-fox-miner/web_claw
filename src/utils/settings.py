from dotenv import load_dotenv
import os

# 加载环境变量
load_dotenv()


class Settings:
    """应用配置类"""
    # 服务器配置
    SERVER_HOST = os.getenv("SERVER_HOST", "127.0.0.1")
    SERVER_PORT = int(os.getenv("SERVER_PORT", "52431"))
    
    # 日志配置
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    
    # CORS配置
    CORS_ORIGINS = ["https://chat.deepseek.com", "https://www.doubao.com"]
    
    # 工具映射配置文件
    TOOL_MAPPING_FILE = "tool_mapping.yml"
    
    # 基础目录配置
    BASE_DIR = os.getenv("BASE_DIR", "d:/LocalMind")


# 导出settings实例
settings = Settings()

__all__ = ["settings"]
