"""FastAPI 应用入口模块

初始化 FastAPI 应用，配置中间件、路由和异常处理。
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.v1.router import router as api_v1_router
from app.config import settings
from app.core.dependencies import AsyncSessionLocal, engine
from app.core.exceptions import AppException, app_exception_to_http_exception
from app.core.logging import get_logger, setup_logging
from app.core.runtime import (
    configure_sqlite_runtime,
    ensure_runtime_directories,
    ensure_windows_local_startup,
    initialize_database_schema,
)
from app.middleware import RequestLoggingMiddleware
from app.schemas.common import ApiResponse

# 初始化日志
setup_logging(
    level=settings.log_level,
    log_dir=str(settings.resolved_log_dir),
    log_to_console=settings.log_to_console,
    log_to_file=settings.log_to_file,
    log_file_prefix=settings.log_file_prefix,
    backup_count=settings.log_backup_count,
)

logger = get_logger(__name__)
ensure_runtime_directories()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """应用生命周期管理

    处理应用启动和关闭时的资源初始化与清理。
    """
    # 启动时执行
    logger.info(f"🚀 {settings.app_name} v{settings.app_version} 启动中...")
    logger.info(f"📝 环境: {settings.environment}")
    logger.info(f"🌐 API 文档: http://{settings.host}:{settings.port}/docs")
    logger.info(f"📁 日志目录: {settings.resolved_log_dir}")
    logger.info(f"🖼️ 上传目录: {settings.resolved_upload_dir}")
    if settings.is_windows_edition:
        logger.info(f"🗂️ 本地数据目录: {settings.resolved_local_database_path.parent}")
        logger.info(f"🧰 缓存后端: {settings.effective_cache_backend}")
    if settings.is_sqlite_file_database:
        logger.info(f"🛢️ SQLite 数据库: {settings.async_database_url}")
    if settings.is_windows_edition:
        _, startup_messages, seeded = await ensure_windows_local_startup(engine, AsyncSessionLocal)
        for message in startup_messages:
            if "请手动检查" in message:
                logger.warning(message)
            else:
                logger.info(message)
        edition_label = "Windows 单机版" if settings.app_edition == "windows_local" else "Windows 机房版"
        logger.info(f"已导入{edition_label}种子数据" if seeded else f"{edition_label}种子数据已存在，跳过导入")
    else:
        async with engine.begin() as conn:
            startup_messages = await configure_sqlite_runtime(conn)
            startup_messages.extend(await initialize_database_schema(conn))
        for message in startup_messages:
            if "请手动检查" in message:
                logger.warning(message)
            else:
                logger.info(message)

    yield

    # 关闭时执行
    logger.info(f"👋 {settings.app_name} 正在关闭...")


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
    StaticFiles(directory=settings.resolved_upload_dir),
    name="uploads",
)

frontend_dist_dir = settings.parsed_frontend_dist_dir
frontend_index_path = settings.parsed_frontend_index_path
if settings.is_windows_edition and frontend_index_path.is_file():
    app.mount(
        "/assets",
        StaticFiles(directory=frontend_dist_dir / "assets"),
        name="frontend-assets",
    )


def _path_matches_prefix(path: str, prefix: str) -> bool:
    normalized_path = f"/{path.lstrip('/')}"
    normalized_prefix = f"/{prefix.strip('/')}"
    return normalized_path == normalized_prefix or normalized_path.startswith(f"{normalized_prefix}/")


def should_serve_frontend_spa(frontend_path: str, api_prefix: str, upload_prefix: str) -> bool:
    """Return whether an unmatched path may be handled by the SPA fallback."""
    api_root = api_prefix.strip("/").split("/", 1)[0]
    reserved_prefixes = [api_prefix, upload_prefix]
    if api_root:
        reserved_prefixes.append(f"/{api_root}")

    return not any(
        _path_matches_prefix(frontend_path, prefix)
        for prefix in reserved_prefixes
        if prefix.strip("/")
    )


# 根路径
@app.get("/", summary="根路径", response_model=None)
async def root():
    """根路径接口

    返回服务基本信息。

    Returns:
        服务信息
    """
    if settings.is_windows_edition and settings.parsed_frontend_index_path.is_file():
        return FileResponse(settings.parsed_frontend_index_path)

    return ApiResponse.success(
        data={
            "name": settings.app_name,
            "version": settings.app_version,
            "environment": settings.environment,
        },
        message="欢迎访问在线学习平台 API",
    )


@app.get("/{frontend_path:path}", response_model=None, include_in_schema=False)
async def frontend_spa_fallback(frontend_path: str):
    if (
        not settings.is_windows_edition
        or not settings.parsed_frontend_index_path.is_file()
        or not should_serve_frontend_spa(
            frontend_path,
            settings.api_v1_prefix,
            settings.upload_url_prefix,
        )
    ):
        raise HTTPException(status_code=404, detail="Not Found")
    return FileResponse(settings.parsed_frontend_index_path)


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
