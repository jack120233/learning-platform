"""Pydantic 数据模型模块

导出所有 Pydantic 模型。
"""

from app.schemas.common import (
    ApiResponse,
    BusinessCode,
    ErrorResponse,
    PageData,
)
from app.schemas.feedback import (
    FeedbackCreate,
    FeedbackResponse,
    FeedbackProcess,
)
from app.schemas.message import (
    MessageResponse,
    MessageSend,
    UnreadCountResponse,
)

__all__ = [
    # 通用模型
    "ApiResponse",
    "BusinessCode",
    "ErrorResponse",
    "PageData",
    # 反馈模型
    "FeedbackCreate",
    "FeedbackResponse",
    "FeedbackProcess",
    # 消息模型
    "MessageResponse",
    "MessageSend",
    "UnreadCountResponse",
]