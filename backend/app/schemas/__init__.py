"""Pydantic 数据模型模块

导出所有 Pydantic 模型。
"""

from app.schemas.common import (
    ApiResponse,
    BusinessCode,
    ErrorResponse,
    PageData,
)
from app.schemas.learning import (
    ContinueLearningResponse,
    PlayUrlResponse,
    PreviewResponse,
    ProgressResponse,
    SaveProgressRequest,
    StartLearningRequest,
)

__all__ = [
    # 通用模型
    "ApiResponse",
    "BusinessCode",
    "ErrorResponse",
    "PageData",
    # 学习模块模型
    "StartLearningRequest",
    "SaveProgressRequest",
    "ProgressResponse",
    "ContinueLearningResponse",
    "PlayUrlResponse",
    "PreviewResponse",
]