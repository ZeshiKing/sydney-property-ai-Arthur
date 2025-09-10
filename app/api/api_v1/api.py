"""
API v1 路由配置

统一管理所有API v1版本的路由
"""

from fastapi import APIRouter

from app.api.api_v1.endpoints import properties, health

# 创建API路由器
api_router = APIRouter()

# 注册各模块路由
api_router.include_router(
    health.router,
    prefix="/health",
    tags=["健康检查"]
)

api_router.include_router(
    properties.router,
    prefix="/properties",
    tags=["房产搜索"]
)