"""认证相关 Pydantic 模型

定义认证模块的请求和响应模型。
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field, field_validator


# ==================== 请求模型 ====================

class RegisterRequest(BaseModel):
    """用户注册请求"""

    username: str = Field(
        ...,
        min_length=2,
        max_length=50,
        description="用户名",
        examples=["zhangsan"],
    )
    email: EmailStr = Field(
        ...,
        description="邮箱地址",
        examples=["zhangsan@example.com"],
    )
    password: str = Field(
        ...,
        min_length=6,
        max_length=50,
        description="密码",
        examples=["password123"],
    )
    captcha_key: str = Field(
        ...,
        description="验证码标识",
    )
    captcha_text: str = Field(
        ...,
        min_length=4,
        max_length=6,
        description="验证码内容",
    )
    role: Literal["student", "teacher"] = Field(
        default="student",
        description="用户角色",
    )

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        """验证用户名格式"""
        if not v.isalnum():
            raise ValueError("用户名只能包含字母和数字")
        return v.lower()

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """验证密码强度"""
        if not any(c.isupper() for c in v) and not any(c.isdigit() for c in v):
            raise ValueError("密码必须包含大写字母或数字")
        return v


class LoginRequest(BaseModel):
    """用户登录请求"""

    username: str = Field(
        ...,
        description="用户名或邮箱",
        examples=["zhangsan"],
    )
    password: str = Field(
        ...,
        description="密码",
        examples=["password123"],
    )
    captcha_key: str = Field(
        ...,
        description="验证码标识",
    )
    captcha_text: str = Field(
        ...,
        min_length=4,
        max_length=6,
        description="验证码内容",
    )
    remember_me: bool = Field(
        default=False,
        description="是否记住我",
    )


class RefreshTokenRequest(BaseModel):
    """刷新令牌请求"""

    refresh_token: str = Field(
        ...,
        description="刷新令牌",
    )


class SendEmailCodeRequest(BaseModel):
    """发送邮箱验证码请求"""

    email: EmailStr = Field(
        ...,
        description="邮箱地址",
        examples=["zhangsan@example.com"],
    )
    purpose: Literal["register", "reset_password"] = Field(
        ...,
        description="用途",
    )
    captcha_key: str = Field(
        ...,
        description="验证码标识",
    )
    captcha_text: str = Field(
        ...,
        min_length=4,
        max_length=6,
        description="验证码内容",
    )


class ResetPasswordRequest(BaseModel):
    """密码重置请求"""

    email: EmailStr = Field(
        ...,
        description="邮箱地址",
    )
    code: str = Field(
        ...,
        min_length=6,
        max_length=6,
        description="邮箱验证码",
    )
    new_password: str = Field(
        ...,
        min_length=6,
        max_length=50,
        description="新密码",
    )

    @field_validator("new_password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """验证密码强度"""
        if not any(c.isupper() for c in v) and not any(c.isdigit() for c in v):
            raise ValueError("密码必须包含大写字母或数字")
        return v


# ==================== 响应模型 ====================

class UserResponse(BaseModel):
    """用户信息响应"""

    id: int = Field(description="用户ID")
    username: str = Field(description="用户名")
    email: str = Field(description="邮箱")
    nickname: str | None = Field(default=None, description="昵称")
    avatar: str | None = Field(default=None, description="头像URL")
    role: str = Field(description="角色")
    status: str = Field(description="状态")
    created_at: datetime = Field(description="注册时间")

    model_config = {"from_attributes": True}


class LoginResponse(BaseModel):
    """登录响应"""

    access_token: str = Field(description="访问令牌")
    refresh_token: str = Field(description="刷新令牌")
    token_type: str = Field(default="bearer", description="令牌类型")
    expires_in: int = Field(description="访问令牌有效期（秒）")
    user: UserResponse = Field(description="用户信息")


class CaptchaResponse(BaseModel):
    """验证码响应"""

    captcha_key: str = Field(description="验证码唯一标识")
    captcha_image: str = Field(description="Base64 编码的验证码图片")


class TokenResponse(BaseModel):
    """令牌响应"""

    access_token: str = Field(description="访问令牌")
    token_type: str = Field(default="bearer", description="令牌类型")
    expires_in: int = Field(description="访问令牌有效期（秒）")