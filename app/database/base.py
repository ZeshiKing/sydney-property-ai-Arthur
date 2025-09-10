"""
数据库基础配置

SQLAlchemy 2.0 数据库连接和会话管理
"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, DateTime, func
from typing import AsyncGenerator
import logging

from app.core.config import settings

# 配置日志
logger = logging.getLogger(__name__)

# 创建异步数据库引擎
engine = create_async_engine(
    str(settings.DATABASE_URL),
    echo=settings.DEBUG,  # 在调试模式下显示SQL语句
    pool_pre_ping=True,   # 连接池健康检查
    pool_recycle=3600,    # 1小时后回收连接
    pool_size=10,         # 连接池大小
    max_overflow=20       # 最大溢出连接数
)

# 创建异步会话工厂
async_session_maker = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False
)


class Base(DeclarativeBase):
    """数据库模型基类"""
    
    # 通用字段
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """获取异步数据库会话"""
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def create_tables():
    """创建所有数据库表"""
    async with engine.begin() as conn:
        # 导入所有模型以确保它们被注册
        from app.models.property import Property
        from app.models.search_history import SearchHistory
        
        # 创建所有表
        await conn.run_sync(Base.metadata.create_all)
        logger.info("数据库表创建完成")


async def drop_tables():
    """删除所有数据库表 (仅用于测试)"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        logger.info("数据库表删除完成")


async def init_database():
    """初始化数据库"""
    try:
        await create_tables()
        logger.info("数据库初始化成功")
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        raise


async def close_database():
    """关闭数据库连接"""
    await engine.dispose()
    logger.info("数据库连接已关闭")