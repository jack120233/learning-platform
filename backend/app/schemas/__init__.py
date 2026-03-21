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
    UserResponse,
)
from app.schemas.common import (
    ApiResponse,
    BusinessCode,
    ErrorResponse,
    PageData,
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
    "UserResponse",
    "CaptchaResponse",
    "TokenResponse",
]