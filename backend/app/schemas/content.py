from __future__ import annotations

"""课程内容相关 Pydantic 模型

定义课程内容模块的请求和响应模型。
"""

from datetime import datetime
from typing import Literal

from pydantic import AliasChoices, BaseModel, Field, model_validator


# ==================== 章节模型 ====================

class ChapterCreate(BaseModel):
    """创建章节请求"""

    title: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="章节标题",
    )
    description: str | None = Field(
        default=None,
        max_length=1000,
        description="章节描述",
    )
    sort_order: int = Field(
        default=0,
        description="排序序号",
    )
    is_free: bool = Field(
        default=False,
        description="是否免费试看",
    )


class ChapterUpdate(BaseModel):
    """更新章节请求"""

    title: str | None = Field(
        default=None,
        min_length=1,
        max_length=200,
        description="章节标题",
    )
    description: str | None = Field(
        default=None,
        max_length=1000,
        description="章节描述",
    )
    sort_order: int | None = Field(
        default=None,
        description="排序序号",
    )
    is_free: bool | None = Field(
        default=None,
        description="是否免费试看",
    )


class ChapterSortRequest(BaseModel):
    """章节排序请求"""

    chapter_ids: list[int] = Field(
        ...,
        min_length=1,
        description="按目标顺序排列的章节ID数组",
    )


class ChapterResponse(BaseModel):
    """章节响应"""

    chapter_id: int = Field(
        validation_alias=AliasChoices("id", "chapter_id"),
        description="章节ID",
    )
    course_id: int = Field(description="课程ID")
    title: str = Field(description="章节标题")
    description: str | None = Field(default=None, description="章节描述")
    sort_order: int = Field(description="排序序号")
    is_free: bool = Field(description="是否免费试看")
    total_duration: int = Field(description="章节总时长（秒）")
    section_count: int = Field(description="小节数量")
    created_at: datetime = Field(description="创建时间")

    model_config = {"from_attributes": True}


# ==================== 小节模型 ====================

class SectionCreate(BaseModel):
    """创建小节请求"""

    title: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="小节标题",
    )
    description: str | None = Field(
        default=None,
        max_length=1000,
        description="小节描述",
    )
    sort_order: int = Field(
        default=0,
        description="排序序号",
    )
    is_free: bool = Field(
        default=False,
        description="是否免费试看",
    )


class SectionUpdate(BaseModel):
    """更新小节请求"""

    title: str | None = Field(
        default=None,
        min_length=1,
        max_length=200,
        description="小节标题",
    )
    description: str | None = Field(
        default=None,
        max_length=1000,
        description="小节描述",
    )
    sort_order: int | None = Field(
        default=None,
        description="排序序号",
    )
    is_free: bool | None = Field(
        default=None,
        description="是否免费试看",
    )


class SectionSortRequest(BaseModel):
    """小节排序请求"""

    section_ids: list[int] = Field(
        ...,
        min_length=1,
        description="按目标顺序排列的小节ID数组",
    )


class SectionResponse(BaseModel):
    """小节响应"""

    section_id: int = Field(
        validation_alias=AliasChoices("id", "section_id"),
        description="小节ID",
    )
    course_id: int = Field(description="课程ID")
    chapter_id: int = Field(description="章节ID")
    title: str = Field(description="小节标题")
    description: str | None = Field(default=None, description="小节描述")
    sort_order: int = Field(description="排序序号")
    is_free: bool = Field(description="是否免费试看")
    duration: int = Field(description="小节时长（秒）")
    resource_count: int = Field(description="资源数量")
    created_at: datetime = Field(description="创建时间")
    resources: list[ResourceResponse] = Field(default_factory=list, description="资源列表")

    model_config = {"from_attributes": True}


# ==================== 资源模型 ====================

class ResourceCreate(BaseModel):
    """创建资源请求"""

    title: str | None = Field(
        default=None,
        min_length=1,
        max_length=200,
        description="资源标题",
    )
    type: Literal["video", "audio", "document", "image", "quiz"] = Field(
        default="document",
        description="资源类型",
    )
    resource_type: Literal["video", "audio", "document", "image", "quiz"] | None = Field(
        default=None,
        description="兼容前端的资源类型字段",
    )
    file_name: str | None = Field(
        default=None,
        max_length=200,
        description="兼容前端的文件名字段",
    )
    file_url: str = Field(
        ...,
        max_length=500,
        description="文件URL",
    )
    file_size: int = Field(
        default=0,
        ge=0,
        description="文件大小（字节）",
    )
    duration: int = Field(
        default=0,
        ge=0,
        description="视频时长（秒）",
    )
    sort_order: int = Field(
        default=0,
        description="排序序号",
    )
    is_free: bool = Field(
        default=False,
        description="是否免费试看",
    )

    @model_validator(mode="before")
    @classmethod
    def normalize_frontend_payload(cls, data: object) -> object:
        """兼容前端当前使用的字段命名。"""
        if not isinstance(data, dict):
            return data

        normalized = dict(data)
        if normalized.get("resource_type") and not normalized.get("type"):
            normalized["type"] = normalized["resource_type"]
        if normalized.get("file_name") and not normalized.get("title"):
            normalized["title"] = normalized["file_name"]
        return normalized


class ResourceResponse(BaseModel):
    """资源响应"""

    id: int = Field(description="资源ID")
    resource_id: int = Field(validation_alias=AliasChoices("id", "resource_id"), description="资源ID")
    course_id: int = Field(description="课程ID")
    chapter_id: int = Field(description="章节ID")
    section_id: int | None = Field(default=None, description="小节ID")
    title: str = Field(description="资源标题")
    file_name: str = Field(validation_alias=AliasChoices("title", "file_name"), description="文件名")
    type: str = Field(description="资源类型")
    resource_type: str = Field(validation_alias=AliasChoices("type", "resource_type"), description="资源类型")
    file_url: str = Field(description="文件URL")
    file_size: int = Field(description="文件大小（字节）")
    duration: int = Field(description="视频时长（秒）")
    sort_order: int = Field(description="排序序号")
    is_free: bool = Field(description="是否免费试看")
    view_count: int = Field(description="观看次数")
    created_at: datetime = Field(description="创建时间")

    model_config = {"from_attributes": True}


# ==================== 课程内容完整结构 ====================

class CourseContentResponse(BaseModel):
    """课程内容完整结构响应"""

    chapters: list["ChapterWithSections"] = Field(description="章节列表")


class ChapterWithSections(BaseModel):
    """带小节的章节响应"""

    chapter_id: int = Field(description="章节ID")
    course_id: int = Field(description="课程ID")
    title: str = Field(description="章节标题")
    description: str | None = Field(default=None, description="章节描述")
    sort_order: int = Field(description="排序序号")
    is_free: bool = Field(description="是否免费试看")
    total_duration: int = Field(description="章节总时长（秒）")
    section_count: int = Field(description="小节数量")
    created_at: datetime = Field(description="创建时间")
    sections: list[SectionResponse] = Field(description="小节列表")
    resources: list[ResourceResponse] = Field(default_factory=list, description="章节资源")

    model_config = {"from_attributes": True}


SectionResponse.model_rebuild()
ChapterWithSections.model_rebuild()
