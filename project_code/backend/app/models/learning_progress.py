"""学习记录数据模型

定义学习记录相关的数据库模型。
"""

from datetime import datetime

from sqlalchemy import String, DateTime, Integer, Float
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class LearningProgress(BaseModel):
    """课程学习记录模型

    记录用户的课程学习进度。

    Attributes:
        user_id: 用户ID
        course_id: 课程ID
        progress: 学习进度（百分比）
        last_section_id: 最后学习的小节ID
        last_position: 最后播放位置（秒）
        total_duration: 累计学习时长（秒）
        completed_at: 完成时间
    """

    __tablename__ = "learning_progress"

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
    progress: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
        comment="学习进度（百分比）",
    )
    last_section_id: Mapped[int | None] = mapped_column(
        nullable=True,
        comment="最后学习的小节ID",
    )
    last_position: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="最后播放位置（秒）",
    )
    total_duration: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="累计学习时长（秒）",
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="完成时间",
    )

    def __repr__(self) -> str:
        return f"<LearningProgress(id={self.id}, user_id={self.user_id}, course_id={self.course_id})>"