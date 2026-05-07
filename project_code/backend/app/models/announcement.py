"""公告数据模型

定义公告相关的数据库模型。
"""

from datetime import datetime

from sqlalchemy import String, Text, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class Announcement(BaseModel):
    """公告模型

    用于系统公告管理。

    Attributes:
        title: 公告标题
        content: 公告内容
        type: 公告类型（notice/update/maintenance）
        is_top: 是否置顶
        is_published: 是否发布
        publish_at: 发布时间
        expire_at: 过期时间
        view_count: 浏览次数
        author_id: 作者ID
    """

    __tablename__ = "announcements"

    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        index=True,
        comment="公告标题",
    )
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="公告内容",
    )
    type: Mapped[str] = mapped_column(
        String(20),
        default="notice",
        nullable=False,
        comment="公告类型",
    )
    is_top: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
        comment="是否置顶",
    )
    is_published: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
        comment="是否发布",
    )
    publish_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="发布时间",
    )
    expire_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="过期时间",
    )
    view_count: Mapped[int] = mapped_column(
        default=0,
        nullable=False,
        comment="浏览次数",
    )
    author_id: Mapped[int | None] = mapped_column(
        nullable=True,
        comment="作者ID",
    )

    def __repr__(self) -> str:
        return f"<Announcement(id={self.id}, title={self.title})>"

    @property
    def is_active(self) -> bool:
        """检查公告是否有效（已发布且未过期）"""
        if not self.is_published:
            return False
        now = datetime.utcnow()
        if self.publish_at and self.publish_at > now:
            return False
        if self.expire_at and self.expire_at < now:
            return False
        return True