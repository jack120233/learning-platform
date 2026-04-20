"""反馈消息相关 Pydantic 模型。

定义反馈消息模块的请求和响应模型。
"""

from datetime import datetime
from typing import Literal

from pydantic import AliasChoices, BaseModel, Field, model_validator


# ==================== 反馈模型 ====================

class FeedbackCreate(BaseModel):
    """提交反馈请求。

    同时兼容当前前端使用的 `feedback_type/course_id/content/images`
    和后端旧版 `type/title/content/contact/images` 结构。
    """

    feedback_type: Literal["system", "course"] = Field(
        default="system",
        validation_alias=AliasChoices("feedback_type", "type"),
        description="反馈类型：system/course",
    )
    course_id: int | None = Field(
        default=None,
        ge=1,
        description="关联课程 ID（课程反馈时可传）",
    )
    title: str | None = Field(
        default=None,
        min_length=1,
        max_length=200,
        description="反馈标题（兼容旧版请求）",
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

    @model_validator(mode="before")
    @classmethod
    def _normalize_legacy_type(cls, data):
        """兼容旧版 `type` 枚举。"""
        if not isinstance(data, dict):
            return data

        if "feedback_type" not in data and "type" in data:
            legacy_type = data.get("type")
            data["feedback_type"] = "course" if legacy_type == "course" else "system"

        return data

    @model_validator(mode="after")
    def _finalize(self):
        """补齐默认标题并校验课程反馈参数。"""
        if self.feedback_type == "course" and self.course_id is None:
            raise ValueError("课程反馈必须提供 course_id")

        if not self.title:
            self.title = "课程反馈" if self.feedback_type == "course" else "系统反馈"

        return self


class FeedbackProcess(BaseModel):
    """处理反馈请求"""

    reply: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="回复内容",
    )


class FeedbackResponse(BaseModel):
    """反馈响应。

    返回前端当前在“我的反馈”和“反馈管理”页面实际使用的字段，
    同时保留旧字段名，降低联调改动面。
    """

    feedback_id: int = Field(description="反馈ID")
    id: int = Field(description="反馈ID（兼容旧字段）")
    user_id: int = Field(description="用户ID")
    username: str | None = Field(default=None, description="用户名")
    user_email: str | None = Field(default=None, description="用户邮箱")
    user_phone: str | None = Field(default=None, description="用户手机号")
    feedback_type: Literal["system", "course"] = Field(description="反馈类型")
    type: Literal["system", "course"] = Field(description="反馈类型（兼容旧字段）")
    course_id: int | None = Field(default=None, description="关联课程ID")
    course_title: str | None = Field(default=None, description="关联课程标题")
    title: str = Field(description="反馈标题")
    content: str = Field(description="反馈内容")
    contact: str | None = Field(default=None, description="联系方式")
    images: list[str] = Field(default_factory=list, description="图片URLs")
    status: Literal["pending", "processed"] = Field(description="处理状态")
    reply: str | None = Field(default=None, description="回复内容")
    replied_at: datetime | None = Field(default=None, description="回复时间（兼容旧字段）")
    processed_at: datetime | None = Field(default=None, description="处理时间")
    created_at: datetime = Field(description="创建时间")

    model_config = {"from_attributes": True}


class FeedbackBatchProcess(BaseModel):
    """批量处理反馈请求。"""

    feedback_ids: list[int] = Field(
        ...,
        min_length=1,
        description="反馈 ID 列表",
    )


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
