"""数据库模型模块

导出所有数据库模型。
"""

from app.models.base import Base, BaseModel, IDMixin, SoftDeleteMixin, TimestampMixin
from app.models.user import User
from app.models.teacher_audit import TeacherAudit
from app.models.admin_application import AdminApplication
from app.models.learning_progress import LearningProgress

__all__ = [
    "Base",
    "BaseModel",
    "IDMixin",
    "TimestampMixin",
    "SoftDeleteMixin",
    "User",
    "TeacherAudit",
    "AdminApplication",
    "LearningProgress",
]