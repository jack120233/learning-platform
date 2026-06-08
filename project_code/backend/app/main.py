"""FastAPI 应用入口模块

初始化 FastAPI 应用，配置中间件、路由和异常处理。
"""

import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.v1.router import router as api_v1_router
from app.config import settings
from app.core.db_schema import ensure_database_compatibility
from app.core.dependencies import engine
from app.core.exceptions import AppException, app_exception_to_http_exception
from app.core.logging import get_logger, setup_logging
from app.middleware import RequestLoggingMiddleware
from app.schemas.common import ApiResponse

# 初始化日志
setup_logging(
    level=settings.log_level,
    log_dir=settings.log_dir,
    log_to_console=settings.log_to_console,
    log_to_file=settings.log_to_file,
    log_file_prefix=settings.log_file_prefix,
    backup_count=settings.log_backup_count,
)

logger = get_logger(__name__)
Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """应用生命周期管理

    处理应用启动和关闭时的资源初始化与清理。
    """
    # 启动时执行
    logger.info(f"{settings.app_name} v{settings.app_version} 启动中...")
    logger.info(f"环境: {settings.environment}")
    logger.info(f"API 文档: http://{settings.host}:{settings.port}/docs")
    logger.info(f"日志目录: {settings.log_dir}")
    logger.info(f"上传目录: {settings.upload_dir}")
    async with engine.begin() as conn:
        schema_messages = await ensure_database_compatibility(conn)
    for message in schema_messages:
        if "请手动检查" in message:
            logger.warning(message)
        else:
            logger.info(message)

    yield

    # 关闭时执行
    logger.info(f"{settings.app_name} 正在关闭...")


# 创建 FastAPI 应用实例
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="在线学习平台后端 API 服务",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# 配置 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.parsed_cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=["*"] if isinstance(settings.cors_allow_methods, str) else settings.cors_allow_methods,
    allow_headers=["*"] if isinstance(settings.cors_allow_headers, str) else settings.cors_allow_headers,
)

# 添加请求日志中间件
app.add_middleware(RequestLoggingMiddleware)


# 注册异常处理器
@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """处理应用自定义异常"""
    http_exc = app_exception_to_http_exception(exc)
    return JSONResponse(
        status_code=http_exc.status_code,
        content=http_exc.detail,
    )


# 注册 API 路由
app.include_router(api_v1_router, prefix=settings.api_v1_prefix)
app.mount(
    settings.upload_url_prefix,
    StaticFiles(directory=settings.upload_dir),
    name="uploads",
)


# 根路径
@app.get("/", summary="根路径")
async def root() -> ApiResponse:
    """根路径接口

    返回服务基本信息。

    Returns:
        服务信息
    """
    return ApiResponse.success(
        data={
            "name": settings.app_name,
            "version": settings.app_version,
            "environment": settings.environment,
        },
        message="欢迎访问在线学习平台 API",
    )


# 全局异常处理（兜底）
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """全局异常处理器

    捕获未处理的异常，返回统一错误响应。
    """
    # 记录错误日志
    logger.error(
        f"未处理的异常: {exc.__class__.__name__}: {exc}",
        exc_info=True,
    )

    return JSONResponse(
        status_code=500,
        content={
            "code": 500,
            "message": "服务器内部错误" if not settings.debug else str(exc),
            "data": None,
        },
    )
