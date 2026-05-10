"""课程数据模型

定义课程相关的数据库模型。
"""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class Course(BaseModel):
    """课程模型

    存储课程基本信息。

    Attributes:
        title: 课程标题
        subtitle: 课程副标题
        summary: 课程简介
        description: 课程描述
        cover_url: 封面图片URL
        teacher_id: 讲师ID
        category_id: 分类ID
        price: 课程价格
        original_price: 原价
        level: 难度等级（beginner/intermediate/advanced）
        status: 课程状态（draft/published/archived）
        is_free: 是否免费
        total_duration: 总时长（秒）
        total_sections: 小节数量
        student_count: 学员数量
        rating: 评分
        rating_count: 评分人数
        published_at: 发布时间
    """

    __tablename__ = "courses"

    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        index=True,
        comment="课程标题",
    )
    subtitle: Mapped[str | None] = mapped_column(
        String(300),
        nullable=True,
        comment="课程副标题",
    )
    summary: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="课程简介",
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="课程描述",
    )
    cover_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="封面图片URL",
    )
    teacher_id: Mapped[int] = mapped_column(
        nullable=False,
        index=True,
        comment="讲师ID",
    )
    author: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="作者",
    )
    category_id: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        index=True,
        comment="分类ID",
    )
    price: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
        comment="课程价格",
    )
    original_price: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
        comment="原价",
    )
    level: Mapped[str] = mapped_column(
        String(20),
        default="beginner",
        nullable=False,
        comment="难度等级",
    )
    status: Mapped[str] = mapped_column(
        String(20),
        default="draft",
        nullable=False,
        index=True,
        comment="课程状态",
    )
    is_free: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
        comment="是否免费",
    )
    total_duration: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="总时长（秒）",
    )
    total_sections: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="小节数量",
    )
    student_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="学员数量",
    )
    rating: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
        comment="评分",
    )
    rating_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="评分人数",
    )
    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="发布时间",
    )

    def __repr__(self) -> str:
        return f"<Course(id={self.id}, title={self.title}, status={self.status})>"

    @property
    def is_published(self) -> bool:
        """检查课程是否已发布"""
        return self.status == "published"


class CourseTeacherAssignment(BaseModel):
    """课程统计授权模型。

    管理员可授权非课程负责人老师查看、明细和导出单门课程学习统计。
    该授权不参与课程编辑、发布、下架、删除或资源资料管理权限判断。
    """

    __tablename__ = "course_teacher_assignments"
    __table_args__ = (
        UniqueConstraint(
            "course_id",
            "teacher_id",
            "permission_type",
            name="uq_course_teacher_assignment_permission",
        ),
        Index("idx_course_teacher_assignment_teacher_active", "teacher_id", "is_active"),
        Index("idx_course_teacher_assignment_course_active", "course_id", "is_active"),
    )

    course_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True,
        comment="课程ID",
    )
    teacher_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True,
        comment="被授权老师ID",
    )
    permission_type: Mapped[str] = mapped_column(
        String(50),
        default="statistics_viewer",
        nullable=False,
        comment="授权类型",
    )
    assigned_by: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="授权管理员ID",
    )
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        comment="授权时间",
    )
    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="撤销时间",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="是否生效",
    )

    def __repr__(self) -> str:
        return (
            f"<CourseTeacherAssignment(course_id={self.course_id}, "
            f"teacher_id={self.teacher_id}, active={self.is_active})>"
        )


class CourseMaterial(BaseModel):
    """课程配套资料模型

    存储课程配套资料信息。

    Attributes:
        course_id: 课程ID
        name: 资料名称
        file_url: 文件URL
        file_size: 文件大小（字节）
        file_type: 文件类型
        download_count: 下载次数
    """

    __tablename__ = "course_materials"

    course_id: Mapped[int] = mapped_column(
        nullable=False,
        index=True,
        comment="课程ID",
    )
    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="资料名称",
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
    file_type: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="文件类型",
    )
    download_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="下载次数",
    )

    def __repr__(self) -> str:
        return f"<CourseMaterial(id={self.id}, course_id={self.course_id}, name={self.name})>"


class CourseTag(BaseModel):
    """课程标签关联模型

    存储课程与标签的多对多关系。
    """

    __tablename__ = "course_tags"

    course_id: Mapped[int] = mapped_column(
        nullable=False,
        index=True,
        comment="课程ID",
    )
    tag_id: Mapped[int] = mapped_column(
        nullable=False,
        index=True,
        comment="标签ID",
    )

    def __repr__(self) -> str:
        return f"<CourseTag(course_id={self.course_id}, tag_id={self.tag_id})>"
