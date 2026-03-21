"""业务逻辑服务模块

导出所有服务类。
"""

from app.services.auth_service import AuthService, auth_service
from app.services.system_service import (
    AnnouncementService, CategoryService, TagService,
    announcement_service, category_service, tag_service,
)
from app.services.user_service import (
    AdminApplicationService, TeacherAuditService, UserService,
    admin_application_service, teacher_audit_service, user_service,
)
from app.services.course_service import (
    CourseService, MaterialService, course_service, material_service,
)
from app.services.content_service import (
    ChapterService, SectionService, ResourceService,
    chapter_service, section_service, resource_service,
)
from app.services.learning_service import LearningService, learning_service
from app.services.feedback_service import FeedbackService, feedback_service
from app.services.message_service import MessageService, message_service

__all__ = [
    "AuthService", "auth_service",
    "CategoryService", "TagService", "AnnouncementService",
    "category_service", "tag_service", "announcement_service",
    "UserService", "TeacherAuditService", "AdminApplicationService",
    "user_service", "teacher_audit_service", "admin_application_service",
    "CourseService", "MaterialService", "course_service", "material_service",
    "ChapterService", "SectionService", "ResourceService",
    "chapter_service", "section_service", "resource_service",
    "LearningService", "learning_service",
    "FeedbackService", "feedback_service",
    "MessageService", "message_service",
]