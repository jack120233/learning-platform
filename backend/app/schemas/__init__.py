"""Pydantic 数据模型模块

导出所有 Pydantic 模型。
"""

from app.schemas.auth import (
    CaptchaResponse, LoginRequest, LoginResponse, RefreshTokenRequest,
    RegisterRequest, ResetPasswordRequest, SendEmailCodeRequest,
    TokenResponse, UserResponse as AuthUserResponse,
)
from app.schemas.common import ApiResponse, BusinessCode, ErrorResponse, PageData
from app.schemas.system import (
    AnnouncementCreate, AnnouncementResponse, AnnouncementUpdate,
    CategoryCreate, CategoryResponse, CategoryUpdate, TagCreate, TagResponse,
)
from app.schemas.user import (
    AdminApplicationCreate, AdminApplicationResponse, AdminApplicationReview,
    ChangePasswordRequest, LearningRecordResponse, TeacherAuditApply,
    TeacherAuditResponse, TeacherAuditReview, UserProfileUpdate,
    UserResponse, UserListResponse, UserStatusUpdate,
)
from app.schemas.course import (
    CourseCreate, CourseUpdate, CourseResponse, CourseListResponse,
    CourseSearchParams, MaterialCreate, MaterialResponse,
)
from app.schemas.content import (
    ChapterCreate, ChapterResponse, ChapterUpdate,
    SectionCreate, SectionResponse, SectionUpdate,
    ResourceCreate, ResourceResponse, CourseContentResponse,
)
from app.schemas.learning import (
    ContinueLearningResponse, PlayUrlResponse, PreviewResponse,
    ProgressResponse, SaveProgressRequest, StartLearningRequest,
)

__all__ = [
    "ApiResponse", "BusinessCode", "ErrorResponse", "PageData",
    "RegisterRequest", "LoginRequest", "LoginResponse", "RefreshTokenRequest",
    "SendEmailCodeRequest", "ResetPasswordRequest", "AuthUserResponse",
    "CaptchaResponse", "TokenResponse",
    "CategoryCreate", "CategoryUpdate", "CategoryResponse",
    "TagCreate", "TagResponse",
    "AnnouncementCreate", "AnnouncementUpdate", "AnnouncementResponse",
    "UserProfileUpdate", "ChangePasswordRequest", "UserResponse",
    "UserListResponse", "UserStatusUpdate", "LearningRecordResponse",
    "TeacherAuditApply", "TeacherAuditResponse", "TeacherAuditReview",
    "AdminApplicationCreate", "AdminApplicationResponse", "AdminApplicationReview",
    "CourseCreate", "CourseUpdate", "CourseResponse", "CourseListResponse",
    "CourseSearchParams", "MaterialCreate", "MaterialResponse",
    "ChapterCreate", "ChapterUpdate", "ChapterResponse",
    "SectionCreate", "SectionUpdate", "SectionResponse",
    "ResourceCreate", "ResourceResponse", "CourseContentResponse",
    "StartLearningRequest", "SaveProgressRequest", "ProgressResponse",
    "ContinueLearningResponse", "PlayUrlResponse", "PreviewResponse",
]