"""反馈消息数据模型。

定义反馈、消息相关的数据库模型。
"""

from datetime import datetime

from sqlalchemy import String, Text, DateTime, Integer, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class Feedback(BaseModel):
    """用户反馈模型

    存储用户提交的反馈信息。

    Attributes:
        user_id: 用户ID
        type: 反馈类型（system/course）
        course_id: 关联课程ID
        target_user_id: 反馈目标用户ID
        title: 反馈标题
        content: 反馈内容
        contact: 联系方式
        images: 图片URLs（JSON数组）
        status: 处理状态（pending/processed）
        reply: 回复内容
        replied_at: 回复时间
        replied_by: 回复人ID
    """

    __tablename__ = "feedbacks"

    user_id: Mapped[int] = mapped_column(
        nullable=False,
        index=True,
        comment="用户ID",
    )
    type: Mapped[str] = mapped_column(
        String(20),
        default="system",
        nullable=False,
        comment="反馈类型",
    )
    course_id: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        index=True,
        comment="关联课程ID",
    )
    target_user_id: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        index=True,
        comment="反馈目标用户ID",
    )
    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="反馈标题",
    )
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="反馈内容",
    )
    contact: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="联系方式",
    )
    images: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="图片URLs（JSON数组）",
    )
    status: Mapped[str] = mapped_column(
        String(20),
        default="pending",
        nullable=False,
        index=True,
        comment="处理状态",
    )
    reply: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="回复内容",
    )
    replied_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="回复时间",
    )
    replied_by: Mapped[int | None] = mapped_column(
        nullable=True,
        comment="回复人ID",
    )

    def __repr__(self) -> str:
        return f"<Feedback(id={self.id}, user_id={self.user_id}, type={self.type})>"
