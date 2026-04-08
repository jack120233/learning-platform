"""请求上下文工具。

用于在同一个请求范围内共享 request_id 和数据库统计信息。
"""

from contextvars import ContextVar, Token
from dataclasses import dataclass


@dataclass
class RequestDBStats:
    """单次请求的数据库统计。"""

    query_count: int = 0
    total_duration_ms: float = 0.0


_request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)
_request_db_stats_var: ContextVar[RequestDBStats | None] = ContextVar(
    "request_db_stats",
    default=None,
)


def set_request_id(request_id: str) -> Token[str | None]:
    """设置当前请求 ID。"""
    return _request_id_var.set(request_id)


def get_request_id() -> str | None:
    """获取当前请求 ID。"""
    return _request_id_var.get()


def reset_request_id(token: Token[str | None]) -> None:
    """恢复请求 ID 上下文。"""
    _request_id_var.reset(token)


def start_request_db_stats() -> Token[RequestDBStats | None]:
    """初始化当前请求的数据库统计。"""
    return _request_db_stats_var.set(RequestDBStats())


def get_request_db_stats() -> RequestDBStats:
    """获取当前请求的数据库统计。"""
    stats = _request_db_stats_var.get()
    if stats is None:
        return RequestDBStats()
    return stats


def record_db_query(duration_ms: float) -> None:
    """累计一条 SQL 的执行统计。"""
    stats = _request_db_stats_var.get()
    if stats is None:
        return

    stats.query_count += 1
    stats.total_duration_ms += duration_ms


def reset_request_db_stats(token: Token[RequestDBStats | None]) -> None:
    """恢复数据库统计上下文。"""
    _request_db_stats_var.reset(token)
