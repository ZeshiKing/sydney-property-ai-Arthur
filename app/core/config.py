"""
应用配置设置

包含所有应用程序配置，支持环境变量和默认值
"""

from pydantic_settings import BaseSettings
from pydantic import PostgresDsn, field_validator, Field, ValidationInfo
from typing import List, Optional, Any
import os
from pathlib import Path


class Settings(BaseSettings):
    """应用配置类"""
    
    # 基本设置
    PROJECT_NAME: str = "澳洲租房聚合系统后端"
    VERSION: str = "2.0.0-python"
    DESCRIPTION: str = "基于FastAPI的澳洲房产数据聚合API服务"
    API_V1_STR: str = "/api/v1"
    PORT: int = 3000
    
    # 环境设置
    ENVIRONMENT: str = Field(default="development", env="ENVIRONMENT")
    DEBUG: bool = Field(default=True, env="DEBUG")
    
    # CORS设置
    BACKEND_CORS_ORIGINS: str = Field(
        default="http://localhost:3000,http://127.0.0.1:3000,http://localhost:8000",
        env="BACKEND_CORS_ORIGINS"
    )

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: str) -> str:
        # 简化处理，直接返回字符串，在FastAPI应用中再分割
        return v
    
    # 数据库设置
    DB_HOST: str = Field(default="localhost", env="DB_HOST")
    DB_PORT: int = Field(default=5432, env="DB_PORT")
    DB_NAME: str = Field(default="rental_aggregator", env="DB_NAME") 
    DB_USER: str = Field(default="postgres", env="DB_USER")
    DB_PASSWORD: str = Field(default="password123", env="DB_PASSWORD")
    DATABASE_URL: Optional[str] = None
    
    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_db_connection(cls, v: Optional[str], info: ValidationInfo) -> Any:
        if isinstance(v, str):
            return v
        values = info.data if info.data else {}
        user = values.get("DB_USER", "postgres")
        password = values.get("DB_PASSWORD", "password123")
        host = values.get("DB_HOST", "localhost")
        port = values.get("DB_PORT", 5432)
        db_name = values.get("DB_NAME", "rental_aggregator")

        return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{db_name}"
    
    # Redis设置
    REDIS_HOST: str = Field(default="localhost", env="REDIS_HOST")
    REDIS_PORT: int = Field(default=6379, env="REDIS_PORT")
    REDIS_PASSWORD: Optional[str] = Field(default="redis123", env="REDIS_PASSWORD")
    REDIS_URL: Optional[str] = None
    
    @field_validator("REDIS_URL", mode="before")
    @classmethod
    def assemble_redis_connection(cls, v: Optional[str], info: ValidationInfo) -> str:
        if isinstance(v, str):
            return v

        values = info.data if info.data else {}
        password = values.get("REDIS_PASSWORD")
        if password:
            return f"redis://:{password}@{values.get('REDIS_HOST')}:{values.get('REDIS_PORT')}"
        else:
            return f"redis://{values.get('REDIS_HOST')}:{values.get('REDIS_PORT')}"
    
    # Firecrawl API设置
    FIRECRAWL_API_KEY: str = Field(env="FIRECRAWL_API_KEY")
    FIRECRAWL_BASE_URL: str = Field(default="https://api.firecrawl.dev", env="FIRECRAWL_BASE_URL")
    
    # OpenAI API设置
    OPENAI_API_KEY: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    OPENAI_MODEL: str = Field(default="gpt-4o-mini", env="OPENAI_MODEL")
    OPENAI_MAX_TOKENS: int = Field(default=500, env="OPENAI_MAX_TOKENS")
    OPENAI_TEMPERATURE: float = Field(default=0.1, env="OPENAI_TEMPERATURE")
    
    # 缓存设置
    CACHE_TTL_SECONDS: int = Field(default=3600, env="CACHE_TTL_SECONDS")  # 1小时
    SEARCH_CACHE_TTL: int = Field(default=300, env="SEARCH_CACHE_TTL")     # 5分钟
    
    # 限流设置
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = Field(default=100, env="RATE_LIMIT_REQUESTS_PER_MINUTE")
    RATE_LIMIT_BURST: int = Field(default=10, env="RATE_LIMIT_BURST")
    
    # CSV导出设置
    CSV_EXPORT_DIR: str = Field(default="csv_exports", env="CSV_EXPORT_DIR")
    CSV_MAX_FILES: int = Field(default=50, env="CSV_MAX_FILES")
    
    # 日志设置
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    LOG_FORMAT: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        env="LOG_FORMAT"
    )
    
    # Celery设置 (后台任务)
    CELERY_BROKER_URL: Optional[str] = None
    CELERY_RESULT_BACKEND: Optional[str] = None
    
    @field_validator("CELERY_BROKER_URL", mode="before")
    @classmethod
    def assemble_celery_broker(cls, v: Optional[str], info: ValidationInfo) -> str:
        if isinstance(v, str):
            return v
        values = info.data if info.data else {}
        return values.get("REDIS_URL", "redis://localhost:6379")
    
    @field_validator("CELERY_RESULT_BACKEND", mode="before")
    @classmethod
    def assemble_celery_backend(cls, v: Optional[str], info: ValidationInfo) -> str:
        if isinstance(v, str):
            return v
        values = info.data if info.data else {}
        return values.get("REDIS_URL", "redis://localhost:6379")
    
    # 安全设置
    SECRET_KEY: str = Field(default="your-secret-key-change-in-production", env="SECRET_KEY")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    
    # 爬虫设置
    SCRAPING_MAX_RETRIES: int = Field(default=3, env="SCRAPING_MAX_RETRIES")
    SCRAPING_RETRY_DELAY: float = Field(default=2.0, env="SCRAPING_RETRY_DELAY")
    SCRAPING_TIMEOUT: int = Field(default=30, env="SCRAPING_TIMEOUT")
    
    # 性能设置
    MAX_CONCURRENT_REQUESTS: int = Field(default=10, env="MAX_CONCURRENT_REQUESTS")
    REQUEST_TIMEOUT: int = Field(default=30, env="REQUEST_TIMEOUT")
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": True
    }


# 创建全局设置实例
settings = Settings()


def get_project_root() -> Path:
    """获取项目根目录"""
    return Path(__file__).parent.parent.parent


def get_csv_export_path() -> Path:
    """获取CSV导出目录路径"""
    project_root = get_project_root()
    csv_path = project_root / settings.CSV_EXPORT_DIR
    csv_path.mkdir(exist_ok=True)
    return csv_path


def is_development() -> bool:
    """是否为开发环境"""
    return settings.ENVIRONMENT.lower() in ["development", "dev"]


def is_production() -> bool:
    """是否为生产环境"""
    return settings.ENVIRONMENT.lower() in ["production", "prod"]