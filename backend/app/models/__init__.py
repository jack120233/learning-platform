"""数据库模型模块

导出所有数据库模型。
"""

from app.models.base import Base, BaseModel, IDMixin, SoftDeleteMixin, TimestampMixin
from app.models.course import Course, CourseMaterial, CourseTag

__all__ = [
    "Base",
    "BaseModel",
    "IDMixin",
    "TimestampMixin",
    "SoftDeleteMixin",
    "Course",
    "CourseMaterial",
    "CourseTag",
]