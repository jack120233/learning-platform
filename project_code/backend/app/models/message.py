"""消息数据模型

定义消息相关的数据库模型。
"""

from datetime import datetime

from sqlalchemy import String, Text, DateTime, Integer, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class Message(BaseModel):
    """站内消息模型

    存储系统消息和通知。

    Attributes:
        user_id: 接收用户ID
        type: 消息类型（system/course/interaction）
        title: 消息标题
        content: 消息内容
        link: 跳转链接
        is_read: 是否已读
        read_at: 阅读时间
        sender_id: 发送者ID（系统消息为空）
    """

    __tablename__ = "messages"

    user_id: Mapped[int] = mapped_column(
        nullable=False,
        index=True,
        comment="接收用户ID",
    )
    type: Mapped[str] = mapped_column(
        String(20),
        default="system",
        nullable=False,
        index=True,
        comment="消息类型",
    )
    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="消息标题",
    )
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="消息内容",
    )
    link: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="跳转链接",
    )
    is_read: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
        index=True,
        comment="是否已读",
    )
    read_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="阅读时间",
    )
    sender_id: Mapped[int | None] = mapped_column(
        nullable=True,
        comment="发送者ID",
    )

    def __repr__(self) -> str:
        return f"<Message(id={self.id}, user_id={self.user_id}, type={self.type})>"