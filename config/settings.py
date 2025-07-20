"""
配置管理模块
统一管理应用程序的所有配置项
"""

import os
from pathlib import Path
from typing import Optional

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent

class Settings:
    """应用程序配置类"""
    
    # API配置
    ANTHROPIC_API_KEY: Optional[str] = os.getenv('ANTHROPIC_API_KEY')
    CLAUDE_MODEL: str = "claude-3-5-sonnet-20241022"
    MAX_TOKENS: int = 1000
    
    # 数据文件配置
    DATA_DIR = PROJECT_ROOT / "data"
    PROPERTY_DATA_FILE = PROJECT_ROOT / "sydney_properties_working_final.csv"
    
    # 日志配置
    LOG_DIR = PROJECT_ROOT / "logs"
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Streamlit配置
    STREAMLIT_CONFIG = {
        "page_title": "demoRA - 智能找房助手",
        "page_icon": "🏠",
        "layout": "wide",
        "initial_sidebar_state": "expanded"
    }
    
    # 房源筛选配置
    DEFAULT_RESULT_LIMIT = 10
    BUDGET_RELAXATION_FACTOR = 1.5  # 预算放宽系数
    MIN_RESULTS_THRESHOLD = 3  # 最少结果数量阈值
    
    # 地理分析配置
    SYDNEY_REGIONS = {
        "city": ["Sydney", "Circular Quay", "The Rocks"],
        "inner": ["Surry Hills", "Darlinghurst", "Paddington"],
        "middle": ["Bondi", "Manly", "Chatswood"],
        "outer": ["Parramatta", "Liverpool", "Blacktown"],
        "coastal": ["Bondi Beach", "Manly Beach", "Cronulla"]
    }
    
    @classmethod
    def validate(cls) -> bool:
        """验证配置是否有效"""
        if not cls.ANTHROPIC_API_KEY:
            return False
        if not cls.PROPERTY_DATA_FILE.exists():
            return False
        return True
    
    @classmethod
    def create_directories(cls) -> None:
        """创建必要的目录"""
        cls.LOG_DIR.mkdir(exist_ok=True)
        cls.DATA_DIR.mkdir(exist_ok=True)

# 全局设置实例
settings = Settings()