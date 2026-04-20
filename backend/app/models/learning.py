"""学习模块数据模型

定义学习进度、资源进度相关的数据库模型。
"""

from datetime import datetime

from sqlalchemy import String, DateTime, Integer, Float, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class ResourceProgress(BaseModel):
    """资源学习进度模型

    记录用户对单个资源的学习进度。

    Attributes:
        user_id: 用户ID
        course_id: 课程ID
        chapter_id: 章节ID
        section_id: 小节ID，可为空以支持章节级资源
        resource_id: 资源ID
        progress: 学习进度（百分比）
        position: 播放位置（秒）
        is_completed: 是否完成
        completed_at: 完成时间
        last_play_at: 最后播放时间
    """

    __tablename__ = "resource_progress"

    user_id: Mapped[int] = mapped_column(
        nullable=False,
        index=True,
        comment="用户ID",
    )
    course_id: Mapped[int] = mapped_column(
        nullable=False,
        index=True,
        comment="课程ID",
    )
    chapter_id: Mapped[int] = mapped_column(
        nullable=False,
        index=True,
        comment="章节ID",
    )
    section_id: Mapped[int | None] = mapped_column(
        nullable=True,
        index=True,
        comment="小节ID",
    )
    resource_id: Mapped[int] = mapped_column(
        nullable=False,
        index=True,
        comment="资源ID",
    )
    progress: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
        comment="学习进度（百分比）",
    )
    position: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="播放位置（秒）",
    )
    is_completed: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
        comment="是否完成",
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="完成时间",
    )
    last_play_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="最后播放时间",
    )

    def __repr__(self) -> str:
        return f"<ResourceProgress(user_id={self.user_id}, resource_id={self.resource_id})>"
