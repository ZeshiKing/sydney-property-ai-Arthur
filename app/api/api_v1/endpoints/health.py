"""
健康检查端点

提供系统健康状态检查功能
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
import asyncio
import asyncpg
import redis.asyncio as redis
from datetime import datetime

from app.core.config import settings
from app.core.logging import api_logger

router = APIRouter()


class HealthResponse(BaseModel):
    """健康检查响应模型"""
    status: str
    timestamp: str
    version: str
    environment: str
    services: Dict[str, Any]


class ServiceStatus(BaseModel):
    """服务状态模型"""
    status: str
    response_time_ms: float
    details: Dict[str, Any] = {}


async def check_database() -> ServiceStatus:
    """检查数据库连接状态"""
    start_time = asyncio.get_event_loop().time()
    
    try:
        conn = await asyncpg.connect(str(settings.DATABASE_URL))
        await conn.execute("SELECT 1")
        await conn.close()
        
        response_time = (asyncio.get_event_loop().time() - start_time) * 1000
        
        return ServiceStatus(
            status="healthy",
            response_time_ms=round(response_time, 2),
            details={"connection": "success"}
        )
    except Exception as e:
        response_time = (asyncio.get_event_loop().time() - start_time) * 1000
        
        return ServiceStatus(
            status="unhealthy",
            response_time_ms=round(response_time, 2),
            details={"error": str(e)}
        )


async def check_redis() -> ServiceStatus:
    """检查Redis连接状态"""
    start_time = asyncio.get_event_loop().time()
    
    try:
        redis_client = redis.from_url(settings.REDIS_URL)
        await redis_client.ping()
        await redis_client.close()
        
        response_time = (asyncio.get_event_loop().time() - start_time) * 1000
        
        return ServiceStatus(
            status="healthy",
            response_time_ms=round(response_time, 2),
            details={"connection": "success"}
        )
    except Exception as e:
        response_time = (asyncio.get_event_loop().time() - start_time) * 1000
        
        return ServiceStatus(
            status="unhealthy",
            response_time_ms=round(response_time, 2),
            details={"error": str(e)}
        )


async def check_firecrawl() -> ServiceStatus:
    """检查Firecrawl API状态"""
    import httpx
    
    start_time = asyncio.get_event_loop().time()
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.FIRECRAWL_BASE_URL}/health",
                headers={"Authorization": f"Bearer {settings.FIRECRAWL_API_KEY}"},
                timeout=10
            )
            
        response_time = (asyncio.get_event_loop().time() - start_time) * 1000
        
        if response.status_code == 200:
            return ServiceStatus(
                status="healthy",
                response_time_ms=round(response_time, 2),
                details={"api_status": "available"}
            )
        else:
            return ServiceStatus(
                status="degraded",
                response_time_ms=round(response_time, 2),
                details={"status_code": response.status_code}
            )
            
    except Exception as e:
        response_time = (asyncio.get_event_loop().time() - start_time) * 1000
        
        return ServiceStatus(
            status="unhealthy",
            response_time_ms=round(response_time, 2),
            details={"error": str(e)}
        )


@router.get("/", response_model=HealthResponse)
async def health_check():
    """
    健康检查端点
    
    返回系统整体健康状态和各个服务的状态
    """
    api_logger.info("Health check requested")
    
    # 并行检查各个服务
    database_status, redis_status, firecrawl_status = await asyncio.gather(
        check_database(),
        check_redis(),
        check_firecrawl(),
        return_exceptions=True
    )
    
    # 处理异常情况
    if isinstance(database_status, Exception):
        database_status = ServiceStatus(
            status="error",
            response_time_ms=0,
            details={"error": str(database_status)}
        )
    
    if isinstance(redis_status, Exception):
        redis_status = ServiceStatus(
            status="error",
            response_time_ms=0,
            details={"error": str(redis_status)}
        )
    
    if isinstance(firecrawl_status, Exception):
        firecrawl_status = ServiceStatus(
            status="error",
            response_time_ms=0,
            details={"error": str(firecrawl_status)}
        )
    
    # 确定整体系统状态
    all_statuses = [database_status.status, redis_status.status, firecrawl_status.status]
    
    if all(status == "healthy" for status in all_statuses):
        overall_status = "healthy"
    elif any(status == "unhealthy" or status == "error" for status in all_statuses):
        overall_status = "unhealthy"
    else:
        overall_status = "degraded"
    
    response = HealthResponse(
        status=overall_status,
        timestamp=datetime.utcnow().isoformat() + "Z",
        version=settings.VERSION,
        environment=settings.ENVIRONMENT,
        services={
            "database": database_status.dict(),
            "redis": redis_status.dict(),
            "firecrawl": firecrawl_status.dict()
        }
    )
    
    api_logger.info(f"Health check completed: {overall_status}")
    return response


@router.get("/ready")
async def readiness_check():
    """
    就绪检查端点
    
    检查应用是否准备好接收请求
    """
    try:
        # 检查关键服务
        database_status = await check_database()
        
        if database_status.status != "healthy":
            raise HTTPException(
                status_code=503,
                detail="Database not available"
            )
        
        return {"status": "ready", "timestamp": datetime.utcnow().isoformat() + "Z"}
    
    except Exception as e:
        api_logger.error(f"Readiness check failed: {e}")
        raise HTTPException(
            status_code=503,
            detail="Service not ready"
        )


@router.get("/live")
async def liveness_check():
    """
    存活检查端点
    
    简单的存活检查，不检查外部依赖
    """
    return {
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "version": settings.VERSION
    }