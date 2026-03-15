from loguru import logger
import os
from datetime import datetime

# 创建日志目录
log_dir = "logs"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

# 配置info级别日志（每天00:00创建新文件，3天清理）
logger.add(
    f"{log_dir}/info_{{time:YYYY-MM-DD}}.log",
    level="INFO",
    rotation="00:00",
    retention="3 days",
    enqueue=True,
    backtrace=True,
    diagnose=True
)

# 配置error级别日志（500MB创建新文件，4周清理）
logger.add(
    f"{log_dir}/error_{{time:YYYY-MM-DD}}.log",
    level="ERROR",
    rotation="500 MB",
    retention="4 weeks",
    enqueue=True,
    backtrace=True,
    diagnose=True
)

# 导出logger
__all__ = ["logger"]
