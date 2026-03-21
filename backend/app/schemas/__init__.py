"""Pydantic 数据模型模块

导出所有 Pydantic 模型。
"""

from app.schemas.auth import (
    CaptchaResponse,
    LoginRequest,
    LoginResponse,
    RefreshTokenRequest,
    RegisterRequest,
    ResetPasswordRequest,
    SendEmailCodeRequest,
    TokenResponse,
    UserResponse as AuthUserResponse,
)
from app.schemas.common import (
    ApiResponse,
    BusinessCode,
    ErrorResponse,
    PageData,
)
from app.schemas.system import (
    AnnouncementCreate,
    AnnouncementResponse,
    AnnouncementUpdate,
    CategoryCreate,
    CategoryResponse,
    CategoryUpdate,
    TagCreate,
    TagResponse,
)
from app.schemas.user import (
    AdminApplicationCreate,
    AdminApplicationResponse,
    AdminApplicationReview,
    ChangePasswordRequest,
    LearningRecordResponse,
    TeacherAuditApply,
    TeacherAuditResponse,
    TeacherAuditReview,
    UserProfileUpdate,
    UserResponse,
    UserListResponse,
    UserStatusUpdate,
)

__all__ = [
    # 通用模型
    "ApiResponse",
    "BusinessCode",
    "ErrorResponse",
    "PageData",
    # 认证模型
    "RegisterRequest",
    "LoginRequest",
    "LoginResponse",
    "RefreshTokenRequest",
    "SendEmailCodeRequest",
    "ResetPasswordRequest",
    "AuthUserResponse",
    "CaptchaResponse",
    "TokenResponse",
    # 分类模型
    "CategoryCreate",
    "CategoryUpdate",
    "CategoryResponse",
    # 标签模型
    "TagCreate",
    "TagResponse",
    # 公告模型
    "AnnouncementCreate",
    "AnnouncementUpdate",
    "AnnouncementResponse",
    # 用户模型
    "UserProfileUpdate",
    "ChangePasswordRequest",
    "UserResponse",
    "UserListResponse",
    "UserStatusUpdate",
    "LearningRecordResponse",
    # 讲师审核模型
    "TeacherAuditApply",
    "TeacherAuditResponse",
    "TeacherAuditReview",
    # 管理员申请模型
    "AdminApplicationCreate",
    "AdminApplicationResponse",
    "AdminApplicationReview",
]