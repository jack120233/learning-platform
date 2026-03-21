"""反馈消息相关 Pydantic 模型

定义反馈消息模块的请求和响应模型。
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field


# ==================== 反馈模型 ====================

class FeedbackCreate(BaseModel):
    """提交反馈请求"""

    type: Literal["bug", "suggestion", "question", "other"] = Field(
        default="other",
        description="反馈类型",
    )
    title: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="反馈标题",
    )
    content: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="反馈内容",
    )
    contact: str | None = Field(
        default=None,
        max_length=100,
        description="联系方式",
    )
    images: list[str] | None = Field(
        default=None,
        description="图片URLs",
    )


class FeedbackProcess(BaseModel):
    """处理反馈请求"""

    reply: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="回复内容",
    )


class FeedbackResponse(BaseModel):
    """反馈响应"""

    id: int = Field(description="反馈ID")
    user_id: int = Field(description="用户ID")
    type: str = Field(description="反馈类型")
    title: str = Field(description="反馈标题")
    content: str = Field(description="反馈内容")
    contact: str | None = Field(default=None, description="联系方式")
    images: list[str] | None = Field(default=None, description="图片URLs")
    status: str = Field(description="处理状态")
    reply: str | None = Field(default=None, description="回复内容")
    replied_at: datetime | None = Field(default=None, description="回复时间")
    created_at: datetime = Field(description="创建时间")

    model_config = {"from_attributes": True}


# ==================== 消息模型 ====================

class MessageResponse(BaseModel):
    """消息响应"""

    id: int = Field(description="消息ID")
    type: str = Field(description="消息类型")
    title: str = Field(description="消息标题")
    content: str = Field(description="消息内容")
    link: str | None = Field(default=None, description="跳转链接")
    is_read: bool = Field(description="是否已读")
    read_at: datetime | None = Field(default=None, description="阅读时间")
    created_at: datetime = Field(description="创建时间")

    model_config = {"from_attributes": True}


class MessageSend(BaseModel):
    """发送消息请求"""

    user_id: int = Field(..., description="接收用户ID")
    type: Literal["system", "course", "interaction"] = Field(
        default="system",
        description="消息类型",
    )
    title: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="消息标题",
    )
    content: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="消息内容",
    )
    link: str | None = Field(
        default=None,
        max_length=500,
        description="跳转链接",
    )


class UnreadCountResponse(BaseModel):
    """未读数量响应"""

    total: int = Field(description="总未读数")
    system: int = Field(default=0, description="系统消息未读数")
    course: int = Field(default=0, description="课程消息未读数")
    interaction: int = Field(default=0, description="互动消息未读数")