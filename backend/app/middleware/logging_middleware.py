"""请求日志中间件

自动记录所有 HTTP 请求的详细信息。
"""

import time
import uuid
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.core.logging import get_logger
from app.core.request_context import (
    get_request_db_stats,
    reset_request_db_stats,
    reset_request_id,
    set_request_id,
    start_request_db_stats,
)
from app.core.sql_logging import get_database_log_label

logger = get_logger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """请求日志中间件

    记录每个请求的方法、路径、状态码、耗时等信息。
    为每个请求生成唯一的请求ID，便于追踪。
    """

    def __init__(self, app: ASGIApp) -> None:
        """初始化中间件

        Args:
            app: ASGI 应用实例
        """
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """处理请求

        Args:
            request: 请求对象
            call_next: 下一个处理函数

        Returns:
            响应对象
        """
        # 生成请求ID
        request_id = str(uuid.uuid4())[:8]
        request.state.request_id = request_id
        request_id_token = set_request_id(request_id)
        request_db_stats_token = start_request_db_stats()

        # 记录请求开始时间
        start_time = time.perf_counter()

        # 获取客户端信息
        client_host = request.client.host if request.client else "unknown"
        client_port = request.client.port if request.client else 0

        # 获取用户信息（如果已认证）
        user_id = "anonymous"
        authorization = request.headers.get("authorization", "")
        if authorization.startswith("Bearer "):
            # 不解析 token，只记录是否存在
            user_id = "authenticated"

        full_path = request.url.path
        if request.url.query:
            full_path = f"{full_path}?{request.url.query}"

        # 记录请求开始
        logger.info(
            f"[{request_id}] 请求开始 | {request.method} {full_path} | "
            f"客户端: {client_host}:{client_port} | 用户: {user_id} | "
            f"数据库: {get_database_log_label()}"
        )

        # 记录请求体（仅用于调试，且限制大小）
        if request.method in ["POST", "PUT", "PATCH"]:
            content_type = request.headers.get("content-type", "")
            if "application/json" in content_type:
                logger.debug(f"[{request_id}] Content-Type: {content_type}")

        try:
            # 调用下一个处理器
            response = await call_next(request)

            # 计算请求耗时
            duration_ms = (time.perf_counter() - start_time) * 1000
            db_stats = get_request_db_stats()

            # 记录请求完成
            log_level = logging.INFO if response.status_code < 400 else logging.WARNING
            if response.status_code >= 500:
                log_level = logging.ERROR

            logger.log(
                log_level,
                f"[{request_id}] 请求完成 | {request.method} {full_path} | "
                f"状态码: {response.status_code} | 耗时: {duration_ms:.2f}ms | "
                f"数据库: {db_stats.query_count}条SQL/{db_stats.total_duration_ms:.2f}ms"
            )

            # 添加请求ID到响应头
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Response-Time"] = f"{duration_ms:.2f}ms"

            return response

        except Exception as exc:
            # 计算请求耗时
            duration_ms = (time.perf_counter() - start_time) * 1000
            db_stats = get_request_db_stats()

            # 记录异常
            logger.error(
                f"[{request_id}] 请求异常 | {request.method} {full_path} | "
                f"耗时: {duration_ms:.2f}ms | 数据库: {db_stats.query_count}条SQL/"
                f"{db_stats.total_duration_ms:.2f}ms | 错误: {exc}",
                exc_info=True,
            )
            raise
        finally:
            reset_request_db_stats(request_db_stats_token)
            reset_request_id(request_id_token)


# 需要导入 logging 模块
import logging
