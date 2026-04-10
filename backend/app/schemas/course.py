from __future__ import annotations

"""课程管理相关 Pydantic 模型

定义课程管理模块的请求和响应模型。
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.content import ChapterWithSections


# ==================== 课程模型 ====================

class CourseCreate(BaseModel):
    """创建课程请求"""

    title: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="课程标题",
    )
    subtitle: str | None = Field(
        default=None,
        max_length=300,
        description="课程副标题",
    )
    summary: str | None = Field(
        default=None,
        max_length=500,
        description="简介",
    )
    description: str | None = Field(
        default=None,
        max_length=5000,
        description="课程描述",
    )
    cover_url: str | None = Field(
        default=None,
        max_length=500,
        description="封面图片URL",
    )
    category_id: int | None = Field(
        default=None,
        description="分类ID",
    )
    price: float = Field(
        default=0.0,
        ge=0,
        description="课程价格",
    )
    original_price: float | None = Field(
        default=None,
        ge=0,
        description="原价",
    )
    level: Literal["beginner", "intermediate", "advanced"] = Field(
        default="beginner",
        description="难度等级",
    )
    is_free: bool = Field(
        default=False,
        description="是否免费",
    )
    tag_ids: list[int] | None = Field(
        default=None,
        description="标签ID列表",
    )


class CourseUpdate(BaseModel):
    """更新课程请求"""

    title: str | None = Field(
        default=None,
        min_length=1,
        max_length=200,
        description="课程标题",
    )
    subtitle: str | None = Field(
        default=None,
        max_length=300,
        description="课程副标题",
    )
    summary: str | None = Field(
        default=None,
        max_length=500,
        description="简介",
    )
    description: str | None = Field(
        default=None,
        max_length=5000,
        description="课程描述",
    )
    cover_url: str | None = Field(
        default=None,
        max_length=500,
        description="封面图片URL",
    )
    category_id: int | None = Field(
        default=None,
        description="分类ID",
    )
    price: float | None = Field(
        default=None,
        ge=0,
        description="课程价格",
    )
    original_price: float | None = Field(
        default=None,
        ge=0,
        description="原价",
    )
    level: Literal["beginner", "intermediate", "advanced"] | None = Field(
        default=None,
        description="难度等级",
    )
    is_free: bool | None = Field(
        default=None,
        description="是否免费",
    )
    tag_ids: list[int] | None = Field(
        default=None,
        description="标签ID列表",
    )


class CourseResponse(BaseModel):
    """课程响应"""

    id: int = Field(description="课程ID")
    title: str = Field(description="课程标题")
    subtitle: str | None = Field(default=None, description="课程副标题")
    summary: str | None = Field(default=None, description="简介")
    description: str | None = Field(default=None, description="课程描述")
    cover_url: str | None = Field(default=None, description="封面图片URL")
    teacher_id: int = Field(description="讲师ID")
    teacher_name: str | None = Field(default=None, description="讲师名称")
    category_id: int | None = Field(default=None, description="分类ID")
    category_name: str | None = Field(default=None, description="分类名称")
    price: float = Field(description="课程价格")
    original_price: float | None = Field(default=None, description="原价")
    level: str = Field(description="难度等级")
    status: str = Field(description="课程状态")
    is_free: bool = Field(description="是否免费")
    total_duration: int = Field(description="总时长（秒）")
    total_sections: int = Field(description="小节数量")
    student_count: int = Field(description="学员数量")
    rating: float = Field(description="评分")
    rating_count: int = Field(description="评分人数")
    tags: list[dict] | None = Field(default=None, description="标签列表")
    chapters: list[ChapterWithSections] = Field(
        default_factory=list,
        description="章节及小节列表",
    )
    materials: list[MaterialResponse] = Field(
        default_factory=list,
        description="课程资料列表",
    )
    created_at: datetime = Field(description="创建时间")
    published_at: datetime | None = Field(default=None, description="发布时间")

    model_config = {"from_attributes": True}


class CourseListResponse(BaseModel):
    """课程列表响应（简化版）"""

    id: int = Field(description="课程ID")
    title: str = Field(description="课程标题")
    subtitle: str | None = Field(default=None, description="课程副标题")
    cover_url: str | None = Field(default=None, description="封面图片URL")
    teacher_name: str | None = Field(default=None, description="讲师名称")
    price: float = Field(description="课程价格")
    original_price: float | None = Field(default=None, description="原价")
    level: str = Field(description="难度等级")
    is_free: bool = Field(description="是否免费")
    total_duration: int = Field(description="总时长（秒）")
    student_count: int = Field(description="学员数量")
    rating: float = Field(description="评分")

    model_config = {"from_attributes": True}


# ==================== 配套资料模型 ====================

class MaterialCreate(BaseModel):
    """创建配套资料请求"""

    name: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="资料名称",
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
    file_type: str | None = Field(
        default=None,
        max_length=50,
        description="文件类型",
    )


class MaterialResponse(BaseModel):
    """配套资料响应"""

    id: int = Field(description="资料ID")
    material_id: int = Field(validation_alias="id", description="资料ID")
    course_id: int = Field(description="课程ID")
    name: str = Field(description="资料名称")
    file_name: str = Field(validation_alias="name", description="资料名称")
    file_url: str = Field(description="文件URL")
    file_size: int = Field(description="文件大小（字节）")
    file_type: str | None = Field(default=None, description="文件类型")
    download_count: int = Field(description="下载次数")
    created_at: datetime = Field(description="创建时间")

    model_config = {"from_attributes": True}


# ==================== 文件上传模型 ====================

class UploadFileResponse(BaseModel):
    """文件上传响应"""

    file_name: str = Field(description="原始文件名")
    file_url: str = Field(description="文件访问地址")
    url: str = Field(description="兼容前端的文件访问地址")
    file_size: int = Field(description="文件大小（字节）")
    content_type: str | None = Field(default=None, description="文件 MIME 类型")


# ==================== 课程搜索模型 ====================

class CourseSearchParams(BaseModel):
    """课程搜索参数"""

    keyword: str | None = Field(default=None, description="搜索关键词")
    category_id: int | None = Field(default=None, description="分类ID")
    level: str | None = Field(default=None, description="难度等级")
    is_free: bool | None = Field(default=None, description="是否免费")
    min_price: float | None = Field(default=None, description="最低价格")
    max_price: float | None = Field(default=None, description="最高价格")
    sort_by: str | None = Field(default=None, description="排序字段")
    sort_order: str | None = Field(default="desc", description="排序方向")
    page: int = Field(default=1, ge=1, description="页码")
    page_size: int = Field(default=10, ge=1, le=50, description="每页数量")


CourseResponse.model_rebuild()
