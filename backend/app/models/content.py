"""课程内容数据模型

定义章节、小节、资源相关的数据库模型。
"""

from datetime import datetime

from sqlalchemy import String, Text, DateTime, Integer, Float, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class Chapter(BaseModel):
    """章节模型

    存储课程章节信息。

    Attributes:
        course_id: 课程ID
        title: 章节标题
        description: 章节描述
        sort_order: 排序序号
        is_free: 是否免费试看
        total_duration: 章节总时长（秒）
        section_count: 小节数量
    """

    __tablename__ = "chapters"

    course_id: Mapped[int] = mapped_column(
        nullable=False,
        index=True,
        comment="课程ID",
    )
    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="章节标题",
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="章节描述",
    )
    sort_order: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="排序序号",
    )
    is_free: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
        comment="是否免费试看",
    )
    total_duration: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="章节总时长（秒）",
    )
    section_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="小节数量",
    )

    def __repr__(self) -> str:
        return f"<Chapter(id={self.id}, course_id={self.course_id}, title={self.title})>"


class Section(BaseModel):
    """小节模型

    存储课程小节信息。

    Attributes:
        course_id: 课程ID
        chapter_id: 章节ID
        title: 小节标题
        description: 小节描述
        sort_order: 排序序号
        is_free: 是否免费试看
        duration: 小节时长（秒）
        resource_count: 资源数量
    """

    __tablename__ = "sections"

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
    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="小节标题",
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="小节描述",
    )
    sort_order: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="排序序号",
    )
    is_free: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
        comment="是否免费试看",
    )
    duration: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="小节时长（秒）",
    )
    resource_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="资源数量",
    )

    def __repr__(self) -> str:
        return f"<Section(id={self.id}, chapter_id={self.chapter_id}, title={self.title})>"


class Resource(BaseModel):
    """学习资源模型

    存储小节学习资源（视频、文档等）。

    Attributes:
        course_id: 课程ID
        chapter_id: 章节ID
        section_id: 小节ID
        title: 资源标题
        type: 资源类型（video/document/quiz）
        file_url: 文件URL
        file_size: 文件大小（字节）
        duration: 视频时长（秒）
        sort_order: 排序序号
        is_free: 是否免费试看
        view_count: 观看次数
    """

    __tablename__ = "resources"

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
    section_id: Mapped[int] = mapped_column(
        nullable=False,
        index=True,
        comment="小节ID",
    )
    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="资源标题",
    )
    type: Mapped[str] = mapped_column(
        String(20),
        default="video",
        nullable=False,
        comment="资源类型",
    )
    file_url: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        comment="文件URL",
    )
    file_size: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="文件大小（字节）",
    )
    duration: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="视频时长（秒）",
    )
    sort_order: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="排序序号",
    )
    is_free: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
        comment="是否免费试看",
    )
    view_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="观看次数",
    )

    def __repr__(self) -> str:
        return f"<Resource(id={self.id}, section_id={self.section_id}, title={self.title})>"