"""消息相关 Pydantic 模型

定义消息模块的请求和响应模型。
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


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
    type: Literal["announcement", "notification", "system", "course", "interaction"] = Field(
        default="notification",
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
    announcement: int = Field(default=0, description="公告未读数")
    notification: int = Field(default=0, description="通知未读数")
    system: int = Field(default=0, description="系统消息未读数")
    course: int = Field(default=0, description="课程消息未读数")
    interaction: int = Field(default=0, description="互动消息未读数")
