"""
澳洲租房聚合系统 - FastAPI 后端

主应用程序入口点，配置FastAPI应用、路由、中间件等。
"""

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from contextlib import asynccontextmanager
import time
import logging

from app.core.config import settings
from app.api.api_v1.api import api_router
from app.core.logging import setup_logging

# 设置日志
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动
    logger.info("🚀 启动澳洲租房聚合系统后端服务")
    logger.info(f"📊 环境: {settings.ENVIRONMENT}")
    logger.info(f"🌐 API版本: {settings.API_V1_STR}")
    
    # 初始化数据库 (可选)
    try:
        from app.database.base import init_database
        await init_database()
        logger.info("🗄️  数据库连接成功")
    except Exception as e:
        logger.warning(f"⚠️  数据库连接失败: {e}")
        logger.info("ℹ️  系统将在无数据库模式下运行 (仅内存存储)")
    
    # 检查Firecrawl API连接 (测试实际端点)
    try:
        import httpx
        async with httpx.AsyncClient(timeout=10) as client:
            # 测试实际的抓取端点而不是健康检查
            test_payload = {
                "url": "https://httpbin.org/status/200",
                "formats": ["markdown"]
            }
            response = await client.post(
                f"{settings.FIRECRAWL_BASE_URL}/v1/scrape",
                headers={"Authorization": f"Bearer {settings.FIRECRAWL_API_KEY}"},
                json=test_payload
            )
            if response.status_code in [200, 201]:
                logger.info("🔥 Firecrawl API 连接正常")
            else:
                logger.warning(f"⚠️  Firecrawl API 测试失败: {response.status_code}")
                logger.info("ℹ️  API功能可能受限，但基本服务正常")
    except Exception as e:
        logger.warning(f"⚠️  Firecrawl API 连接检查失败: {e}")
        logger.info("ℹ️  将使用模拟数据模式运行")
    
    # 显示系统启动完成状态
    logger.info("✅ 系统启动完成")
    logger.info("📋 服务状态:")
    logger.info("   🌐 FastAPI: ✅ 运行中")
    logger.info("   🗄️  数据库: ⚠️  可选模式 (如需持久化，请启动PostgreSQL)")
    logger.info("   🔥 Firecrawl: ⚠️  请检查API密钥和网络连接")
    logger.info("   📊 API文档: http://localhost:8000/docs")
    logger.info("   🔍 健康检查: http://localhost:8000/health")
    
    yield
    
    # 关闭
    logger.info("🛑 正在关闭系统...")
    try:
        from app.database.base import close_database
        await close_database()
        logger.info("🗄️  数据库连接已关闭")
    except Exception as e:
        logger.error(f"❌ 数据库关闭失败: {e}")
    
    logger.info("🛑 澳洲租房聚合系统后端服务已关闭")


# 创建FastAPI应用
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="澳洲租房聚合系统后端API - 支持实时抓取Domain.com.au等房产网站数据",
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
    lifespan=lifespan
)

# CORS中间件
cors_origins = [origin.strip() for origin in settings.BACKEND_CORS_ORIGINS.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Gzip压缩中间件
app.add_middleware(GZipMiddleware, minimum_size=1000)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """添加处理时间头"""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(f"{process_time:.4f}")
    return response


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """记录API请求"""
    start_time = time.time()
    
    # 记录请求
    logger.info(
        f"🔍 {request.method} {request.url.path}",
        extra={
            "method": request.method,
            "url": str(request.url),
            "client_ip": request.client.host if request.client else "unknown"
        }
    )
    
    response = await call_next(request)
    
    # 记录响应
    process_time = time.time() - start_time
    logger.info(
        f"✅ {request.method} {request.url.path} - {response.status_code} ({process_time:.3f}s)",
        extra={
            "method": request.method,
            "url": str(request.url),
            "status_code": response.status_code,
            "process_time": process_time
        }
    )
    
    return response


# 注册API路由
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/")
async def root():
    """根端点 - 基本信息"""
    return {
        "message": "澳洲租房聚合系统后端API",
        "version": settings.VERSION,
        "status": "running",
        "docs_url": f"{settings.API_V1_STR}/docs",
        "api_url": settings.API_V1_STR
    }


@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "service": "rental-aggregator-backend",
        "version": settings.VERSION,
        "timestamp": time.time()
    }


if __name__ == "__main__":
    import uvicorn
    
    # 开发模式运行
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=True,
        log_level="info"
    )