"""
日志记录工具模块
提供统一的日志记录功能
"""

import logging
import sys
from pathlib import Path
from typing import Optional

from config.settings import settings

class Logger:
    """日志记录器类"""
    
    def __init__(self, name: str, log_file: Optional[str] = None):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, settings.LOG_LEVEL))
        
        # 避免重复添加处理器
        if not self.logger.handlers:
            self._setup_handlers(log_file)
    
    def _setup_handlers(self, log_file: Optional[str] = None):
        """设置日志处理器"""
        formatter = logging.Formatter(settings.LOG_FORMAT)
        
        # 控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        # 文件处理器
        if log_file:
            settings.create_directories()
            file_path = settings.LOG_DIR / log_file
            file_handler = logging.FileHandler(file_path, encoding='utf-8')
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
    
    def debug(self, message: str, *args, **kwargs):
        """调试级别日志"""
        self.logger.debug(message, *args, **kwargs)
    
    def info(self, message: str, *args, **kwargs):
        """信息级别日志"""
        self.logger.info(message, *args, **kwargs)
    
    def warning(self, message: str, *args, **kwargs):
        """警告级别日志"""
        self.logger.warning(message, *args, **kwargs)
    
    def error(self, message: str, *args, **kwargs):
        """错误级别日志"""
        self.logger.error(message, *args, **kwargs)
    
    def critical(self, message: str, *args, **kwargs):
        """严重错误级别日志"""
        self.logger.critical(message, *args, **kwargs)

# 预定义的日志记录器
app_logger = Logger("app", "app.log")
api_logger = Logger("api", "api.log")
data_logger = Logger("data", "data.log")

def get_logger(name: str, log_file: Optional[str] = None) -> Logger:
    """获取日志记录器实例"""
    return Logger(name, log_file)