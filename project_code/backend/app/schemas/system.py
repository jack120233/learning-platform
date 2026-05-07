"""系统管理相关 Pydantic 模型

定义系统管理模块的请求和响应模型。
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator


# ==================== 分类模型 ====================

class CategoryCreate(BaseModel):
    """创建分类请求"""

    name: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="分类名称",
    )
    slug: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="URL友好标识",
    )
    description: str | None = Field(
        default=None,
        max_length=500,
        description="分类描述",
    )
    icon: str | None = Field(
        default=None,
        max_length=200,
        description="分类图标URL",
    )
    parent_id: int | None = Field(
        default=None,
        description="父分类ID",
    )
    sort_order: int = Field(
        default=0,
        description="排序序号",
    )

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v: str) -> str:
        """验证slug格式"""
        if not v.isalnum() and "-" not in v and "_" not in v:
            raise ValueError("slug只能包含字母、数字、连字符和下划线")
        return v.lower()


class CategoryUpdate(BaseModel):
    """更新分类请求"""

    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=50,
        description="分类名称",
    )
    slug: str | None = Field(
        default=None,
        min_length=1,
        max_length=50,
        description="URL友好标识",
    )
    description: str | None = Field(
        default=None,
        max_length=500,
        description="分类描述",
    )
    icon: str | None = Field(
        default=None,
        max_length=200,
        description="分类图标URL",
    )
    parent_id: int | None = Field(
        default=None,
        description="父分类ID",
    )
    sort_order: int | None = Field(
        default=None,
        description="排序序号",
    )
    is_active: bool | None = Field(
        default=None,
        description="是否启用",
    )


class CategoryResponse(BaseModel):
    """分类响应"""

    id: int = Field(description="分类ID")
    name: str = Field(description="分类名称")
    slug: str = Field(description="URL友好标识")
    description: str | None = Field(default=None, description="分类描述")
    icon: str | None = Field(default=None, description="分类图标URL")
    sort_order: int = Field(description="排序序号")
    parent_id: int | None = Field(default=None, description="父分类ID")
    is_active: bool = Field(description="是否启用")
    created_at: datetime = Field(description="创建时间")

    model_config = {"from_attributes": True}


# ==================== 标签模型 ====================

class TagCreate(BaseModel):
    """创建标签请求"""

    name: str = Field(
        ...,
        min_length=1,
        max_length=30,
        description="标签名称",
    )
    slug: str = Field(
        ...,
        min_length=1,
        max_length=30,
        description="URL友好标识",
    )
    color: str | None = Field(
        default=None,
        max_length=20,
        description="标签颜色",
    )

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v: str) -> str:
        """验证slug格式"""
        if not v.isalnum() and "-" not in v and "_" not in v:
            raise ValueError("slug只能包含字母、数字、连字符和下划线")
        return v.lower()


class TagResponse(BaseModel):
    """标签响应"""

    id: int = Field(description="标签ID")
    name: str = Field(description="标签名称")
    slug: str = Field(description="URL友好标识")
    color: str | None = Field(default=None, description="标签颜色")
    use_count: int = Field(description="使用次数")
    created_at: datetime = Field(description="创建时间")

    model_config = {"from_attributes": True}


class BatchTagDeleteRequest(BaseModel):
    """批量删除标签请求"""

    tag_ids: list[int] = Field(min_length=1, max_length=100, description="标签ID列表")


class BatchTagDeleteFailure(BaseModel):
    """批量删除标签失败项"""

    tag_id: int = Field(description="标签ID")
    reason: str = Field(description="失败原因")


class BatchTagDeleteResponse(BaseModel):
    """批量删除标签响应"""

    success_ids: list[int] = Field(default_factory=list, description="成功删除的标签ID")
    failed_items: list[BatchTagDeleteFailure] = Field(default_factory=list, description="失败项")
    success_count: int = Field(default=0, description="成功数量")
    failed_count: int = Field(default=0, description="失败数量")
    message: str | None = Field(default=None, description="结果说明")


# ==================== 公告模型 ====================

class AnnouncementCreate(BaseModel):
    """创建公告请求"""

    title: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="公告标题",
    )
    content: str = Field(
        ...,
        min_length=1,
        description="公告内容",
    )
    type: Literal["notice", "update", "maintenance"] = Field(
        default="notice",
        description="公告类型",
    )
    is_top: bool = Field(
        default=False,
        description="是否置顶",
    )
    is_published: bool = Field(
        default=False,
        description="是否发布",
    )
    publish_at: datetime | None = Field(
        default=None,
        description="发布时间",
    )
    expire_at: datetime | None = Field(
        default=None,
        description="过期时间",
    )


class AnnouncementUpdate(BaseModel):
    """更新公告请求"""

    title: str | None = Field(
        default=None,
        min_length=1,
        max_length=200,
        description="公告标题",
    )
    content: str | None = Field(
        default=None,
        min_length=1,
        description="公告内容",
    )
    type: Literal["notice", "update", "maintenance"] | None = Field(
        default=None,
        description="公告类型",
    )
    is_top: bool | None = Field(
        default=None,
        description="是否置顶",
    )
    is_published: bool | None = Field(
        default=None,
        description="是否发布",
    )
    publish_at: datetime | None = Field(
        default=None,
        description="发布时间",
    )
    expire_at: datetime | None = Field(
        default=None,
        description="过期时间",
    )


class AnnouncementResponse(BaseModel):
    """公告响应"""

    id: int = Field(description="公告ID")
    title: str = Field(description="公告标题")
    content: str = Field(description="公告内容")
    type: str = Field(description="公告类型")
    is_top: bool = Field(description="是否置顶")
    is_published: bool = Field(description="是否发布")
    publish_at: datetime | None = Field(default=None, description="发布时间")
    expire_at: datetime | None = Field(default=None, description="过期时间")
    view_count: int = Field(description="浏览次数")
    author_id: int | None = Field(default=None, description="作者ID")
    author_name: str | None = Field(default=None, description="作者名称")
    created_at: datetime = Field(description="创建时间")

    model_config = {"from_attributes": True}
