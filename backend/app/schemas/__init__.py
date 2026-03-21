"""Pydantic 数据模型模块

导出所有 Pydantic 模型。
"""

from app.schemas.common import (
    ApiResponse,
    BusinessCode,
    ErrorResponse,
    PageData,
)
from app.schemas.content import (
    ChapterCreate,
    ChapterResponse,
    ChapterUpdate,
    CourseContentResponse,
    ResourceCreate,
    ResourceResponse,
    SectionCreate,
    SectionResponse,
    SectionUpdate,
)

__all__ = [
    # 通用模型
    "ApiResponse",
    "BusinessCode",
    "ErrorResponse",
    "PageData",
    # 章节模型
    "ChapterCreate",
    "ChapterUpdate",
    "ChapterResponse",
    # 小节模型
    "SectionCreate",
    "SectionUpdate",
    "SectionResponse",
    # 资源模型
    "ResourceCreate",
    "ResourceResponse",
    # 内容结构
    "CourseContentResponse",
]