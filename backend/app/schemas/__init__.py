"""Pydantic 数据模型模块

导出所有 Pydantic 模型。
"""

from app.schemas.common import (
    ApiResponse,
    BusinessCode,
    ErrorResponse,
    PageData,
)
from app.schemas.course import (
    CourseCreate,
    CourseUpdate,
    CourseResponse,
    CourseListResponse,
    CourseSearchParams,
    MaterialCreate,
    MaterialResponse,
)

__all__ = [
    # 通用模型
    "ApiResponse",
    "BusinessCode",
    "ErrorResponse",
    "PageData",
    # 课程模型
    "CourseCreate",
    "CourseUpdate",
    "CourseResponse",
    "CourseListResponse",
    "CourseSearchParams",
    # 配套资料模型
    "MaterialCreate",
    "MaterialResponse",
]