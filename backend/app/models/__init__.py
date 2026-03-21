"""数据库模型模块

导出所有数据库模型。
"""

from app.models.base import Base, BaseModel, IDMixin, SoftDeleteMixin, TimestampMixin
from app.models.captcha import CaptchaRecord
from app.models.email_code import EmailCode
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.models.category import Category
from app.models.tag import Tag
from app.models.announcement import Announcement
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
    "CaptchaRecord",
    "EmailCode",
    "RefreshToken",
    "Category",
    "Tag",
    "Announcement",
    "TeacherAudit",
    "AdminApplication",
    "LearningProgress",
]