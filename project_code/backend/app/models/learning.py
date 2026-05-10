"""学习模块数据模型

定义学习进度、资源进度相关的数据库模型。
"""

from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Float, Index, Integer, String, UniqueConstraint
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


class LearningSession(BaseModel):
    """学习会话事实表。"""

    __tablename__ = "learning_sessions"
    __table_args__ = (
        UniqueConstraint("session_id", name="uq_learning_sessions_session_id"),
        Index("idx_learning_sessions_user_started", "user_id", "started_at"),
        Index("idx_learning_sessions_course_started", "course_id", "started_at"),
    )

    session_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        unique=True,
        index=True,
        comment="前端生成的幂等会话ID",
    )
    user_id: Mapped[int] = mapped_column(nullable=False, index=True, comment="用户ID")
    course_id: Mapped[int] = mapped_column(nullable=False, index=True, comment="课程ID")
    chapter_id: Mapped[int] = mapped_column(nullable=False, index=True, comment="章节ID")
    section_id: Mapped[int | None] = mapped_column(nullable=True, index=True, comment="小节ID")
    resource_id: Mapped[int] = mapped_column(nullable=False, index=True, comment="资源ID")
    resource_type: Mapped[str] = mapped_column(String(20), nullable=False, index=True, comment="资源类型")
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True, comment="开始时间")
    ended_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, comment="结束时间")
    effective_duration_seconds: Mapped[int] = mapped_column(Integer, default=0, nullable=False, comment="有效学习时长")
    start_position_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True, comment="媒体开始位置")
    end_position_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True, comment="媒体结束位置")
    progress_percent_at_end: Mapped[float | None] = mapped_column(Float, nullable=True, comment="结束时进度")
    is_completed_at_end: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, comment="结束时是否完成")
    end_reason: Mapped[str] = mapped_column(String(30), nullable=False, comment="结束原因")


class LearningRecordEntry(BaseModel):
    """学生可见学习记录条目。"""

    __tablename__ = "learning_record_entries"
    __table_args__ = (
        Index("idx_learning_record_entries_visible_user_course", "user_id", "course_id", "visible"),
    )

    user_id: Mapped[int] = mapped_column(nullable=False, index=True, comment="用户ID")
    course_id: Mapped[int] = mapped_column(nullable=False, index=True, comment="课程ID")
    last_section_id: Mapped[int | None] = mapped_column(nullable=True, comment="最后学习小节ID")
    last_resource_id: Mapped[int] = mapped_column(nullable=False, index=True, comment="最后学习资源ID")
    last_learn_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True, comment="最后学习时间")
    course_progress_snapshot: Mapped[float] = mapped_column(Float, default=0.0, nullable=False, comment="课程进度快照")
    course_completed_snapshot: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, comment="课程完成快照")
    visible: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True, comment="是否可见")
    hidden_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, comment="隐藏时间")


class StudentDailyLearningStats(BaseModel):
    """学生每日学习统计。"""

    __tablename__ = "student_daily_learning_stats"
    __table_args__ = (
        UniqueConstraint("user_id", "stat_date", name="uq_student_daily_learning_stats_user_date"),
    )

    user_id: Mapped[int] = mapped_column(nullable=False, index=True, comment="用户ID")
    stat_date: Mapped[date] = mapped_column(Date, nullable=False, index=True, comment="统计日期")
    effective_duration_seconds: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    video_duration_seconds: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    audio_duration_seconds: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    document_duration_seconds: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    image_duration_seconds: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    session_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    learned_course_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    completed_resource_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class StudentCourseDailyStats(BaseModel):
    """学生课程每日统计。"""

    __tablename__ = "student_course_daily_stats"
    __table_args__ = (
        UniqueConstraint("user_id", "course_id", "stat_date", name="uq_student_course_daily_stats_user_course_date"),
    )

    user_id: Mapped[int] = mapped_column(nullable=False, index=True, comment="用户ID")
    course_id: Mapped[int] = mapped_column(nullable=False, index=True, comment="课程ID")
    stat_date: Mapped[date] = mapped_column(Date, nullable=False, index=True, comment="统计日期")
    effective_duration_seconds: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    session_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    completed_resource_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    course_progress_at_day_end: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    is_course_completed_at_day_end: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class CourseDailyLearningStats(BaseModel):
    """课程每日学习统计。"""

    __tablename__ = "course_daily_learning_stats"
    __table_args__ = (
        UniqueConstraint("course_id", "stat_date", name="uq_course_daily_learning_stats_course_date"),
    )

    course_id: Mapped[int] = mapped_column(nullable=False, index=True, comment="课程ID")
    stat_date: Mapped[date] = mapped_column(Date, nullable=False, index=True, comment="统计日期")
    active_student_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    new_started_student_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    new_completed_student_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    cumulative_started_student_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    cumulative_completed_student_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_effective_duration_seconds: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    avg_progress: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    completion_rate: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)


class PlatformDailyLearningStats(BaseModel):
    """平台每日学习统计。"""

    __tablename__ = "platform_daily_learning_stats"
    __table_args__ = (
        UniqueConstraint("stat_date", name="uq_platform_daily_learning_stats_date"),
    )

    stat_date: Mapped[date] = mapped_column(Date, nullable=False, index=True, comment="统计日期")
    active_student_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    new_started_course_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    new_completed_course_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_effective_duration_seconds: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    active_course_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
