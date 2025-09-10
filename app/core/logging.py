"""
日志配置模块

配置应用程序的日志系统，支持不同的日志级别和格式化
"""

import logging
import sys
from pathlib import Path
from typing import Dict, Any

from app.core.config import settings


class ColoredFormatter(logging.Formatter):
    """彩色日志格式化器"""
    
    # ANSI颜色代码
    COLORS = {
        'DEBUG': '\033[36m',     # 青色
        'INFO': '\033[32m',      # 绿色
        'WARNING': '\033[33m',   # 黄色
        'ERROR': '\033[31m',     # 红色
        'CRITICAL': '\033[35m',  # 紫色
        'RESET': '\033[0m'       # 重置
    }
    
    def format(self, record):
        # 添加颜色
        if record.levelname in self.COLORS:
            record.levelname = f"{self.COLORS[record.levelname]}{record.levelname}{self.COLORS['RESET']}"
        
        return super().format(record)


def setup_logging():
    """设置日志配置"""
    
    # 创建日志目录
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # 根日志配置
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))
    
    # 清除现有处理器
    root_logger.handlers.clear()
    
    # 控制台处理器 (彩色输出)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = ColoredFormatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # 文件处理器 (应用日志)
    file_handler = logging.FileHandler(
        log_dir / "app.log",
        mode="a",
        encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)
    
    # 错误日志处理器
    error_handler = logging.FileHandler(
        log_dir / "error.log",
        mode="a",
        encoding="utf-8"
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(file_formatter)
    root_logger.addHandler(error_handler)
    
    # 设置特定模块的日志级别
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    
    # 创建专用日志器
    setup_specialized_loggers()


def setup_specialized_loggers():
    """设置专用日志器"""
    
    log_dir = Path("logs")
    
    # API请求日志器
    api_logger = logging.getLogger("api")
    api_handler = logging.FileHandler(
        log_dir / "api.log",
        mode="a",
        encoding="utf-8"
    )
    api_formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    api_handler.setFormatter(api_formatter)
    api_logger.addHandler(api_handler)
    api_logger.setLevel(logging.INFO)
    
    # 爬虫日志器
    scraping_logger = logging.getLogger("scraping")
    scraping_handler = logging.FileHandler(
        log_dir / "scraping.log",
        mode="a",
        encoding="utf-8"
    )
    scraping_handler.setFormatter(api_formatter)
    scraping_logger.addHandler(scraping_handler)
    scraping_logger.setLevel(logging.INFO)
    
    # 数据库日志器
    db_logger = logging.getLogger("database")
    db_handler = logging.FileHandler(
        log_dir / "database.log",
        mode="a",
        encoding="utf-8"
    )
    db_handler.setFormatter(api_formatter)
    db_logger.addHandler(db_handler)
    db_logger.setLevel(logging.INFO)


def get_logger(name: str) -> logging.Logger:
    """获取日志器"""
    return logging.getLogger(name)


# 预定义的日志器
api_logger = logging.getLogger("api")
scraping_logger = logging.getLogger("scraping")
db_logger = logging.getLogger("database")
csv_logger = logging.getLogger("csv_export")