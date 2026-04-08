"""SQL 日志增强工具。"""

from __future__ import annotations

import time
from typing import Any

from sqlalchemy import event
from sqlalchemy.engine import URL, make_url
from sqlalchemy.engine.interfaces import ExceptionContext
from sqlalchemy.ext.asyncio import AsyncEngine

from app.config import settings
from app.core.logging import get_logger
from app.core.request_context import get_request_id, record_db_query

logger = get_logger("app.sql")


def _get_url(database_url: str | URL | None = None) -> URL | None:
    """解析数据库连接串。"""
    try:
        if isinstance(database_url, URL):
            return database_url
        return make_url(database_url or settings.async_database_url)
    except Exception:
        return None


def get_database_log_label(database_url: str | URL | None = None) -> str:
    """返回适合写入日志的数据库标识。"""
    url = _get_url(database_url)
    if url is None:
        return str(database_url or settings.async_database_url)

    dialect = url.drivername
    host = url.host or "local"
    port = f":{url.port}" if url.port else ""
    database = url.database or "(default)"
    return f"{dialect}://{host}{port}/{database}"


def _normalize_sql(statement: str) -> str:
    """压缩 SQL 空白，便于单行日志查看。"""
    return " ".join(statement.split())


def _truncate(value: str, limit: int = 1000) -> str:
    """限制日志字段长度，避免单行过长。"""
    if len(value) <= limit:
        return value
    return f"{value[:limit]}...(truncated)"


def _format_parameters(parameters: Any) -> str:
    """格式化 SQL 绑定参数。"""
    if not settings.database_log_parameters:
        return "<hidden>"

    try:
        return _truncate(repr(parameters))
    except Exception:
        return "<unrepr-able>"


def install_sql_logging(engine: AsyncEngine) -> None:
    """为 SQLAlchemy 异步引擎注册 SQL 日志监听。"""
    sync_engine = engine.sync_engine
    if getattr(sync_engine, "_request_sql_logging_installed", False):
        return

    db_label = get_database_log_label(sync_engine.url)

    @event.listens_for(sync_engine, "before_cursor_execute")
    def before_cursor_execute(
        conn,
        cursor,
        statement,
        parameters,
        context,
        executemany,
    ) -> None:
        context._query_start_time = time.perf_counter()

    @event.listens_for(sync_engine, "after_cursor_execute")
    def after_cursor_execute(
        conn,
        cursor,
        statement,
        parameters,
        context,
        executemany,
    ) -> None:
        start_time = getattr(context, "_query_start_time", None)
        duration_ms = (time.perf_counter() - start_time) * 1000 if start_time else 0.0
        record_db_query(duration_ms)

        request_id = get_request_id() or "-"
        rowcount = getattr(cursor, "rowcount", None)

        logger.debug(
            "[%s] SQL执行 | 数据库: %s | 耗时: %.2fms | rowcount: %s | SQL: %s | 参数: %s",
            request_id,
            db_label,
            duration_ms,
            rowcount,
            _truncate(_normalize_sql(statement)),
            _format_parameters(parameters),
        )

    @event.listens_for(sync_engine, "handle_error")
    def handle_error(exception_context: ExceptionContext) -> None:
        request_id = get_request_id() or "-"

        logger.error(
            "[%s] SQL异常 | 数据库: %s | 错误: %s | SQL: %s | 参数: %s",
            request_id,
            db_label,
            exception_context.original_exception,
            _truncate(_normalize_sql(exception_context.statement or "")),
            _format_parameters(exception_context.parameters),
        )

    sync_engine._request_sql_logging_installed = True
