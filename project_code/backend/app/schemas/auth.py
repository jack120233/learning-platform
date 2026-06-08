"""认证相关 Pydantic 模型

定义认证模块的请求和响应模型。
"""

from datetime import datetime
from typing import Literal

from pydantic import (
    AliasChoices,
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

from app.schemas.validators import EmailAddress


# ==================== 请求模型 ====================

class RegisterRequest(BaseModel):
    """用户注册请求"""

    username: str = Field(
        ...,
        min_length=2,
        max_length=50,
        description="真实姓名/登录名",
        examples=["张三"],
    )
    email: EmailAddress = Field(
        ...,
        description="邮箱地址",
        examples=["zhangsan@example.com"],
    )
    phone: str | None = Field(
        default=None,
        min_length=11,
        max_length=20,
        description="手机号码",
    )
    password: str = Field(
        ...,
        min_length=6,
        max_length=50,
        description="密码",
        examples=["password123"],
    )
    confirm_password: str | None = Field(
        default=None,
        min_length=6,
        max_length=50,
        description="确认密码（兼容前端）",
    )
    role: Literal["student", "teacher"] = Field(
        default="student",
        description="用户角色",
    )
    real_name: str | None = Field(
        default=None,
        min_length=2,
        max_length=50,
        description="真实姓名",
    )

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        """验证真实姓名/登录名。"""
        normalized = v.strip()
        if not normalized:
            raise ValueError("请输入真实姓名")
        return normalized

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """验证密码强度"""
        if not any(c.isupper() for c in v) and not any(c.isdigit() for c in v):
            raise ValueError("密码必须包含大写字母或数字")
        return v

    @model_validator(mode="after")
    def validate_confirm_password(self) -> "RegisterRequest":
        """兼容前端确认密码字段。"""
        if self.confirm_password is not None and self.confirm_password != self.password:
            raise ValueError("两次输入的密码不一致")
        return self


class LoginRequest(BaseModel):
    """用户登录请求"""

    model_config = ConfigDict(populate_by_name=True)

    username: str = Field(
        ...,
        validation_alias=AliasChoices("login_id", "username"),
        description="邮箱或手机号（优先使用 login_id，兼容历史 username 字段）",
        examples=["zhangsan@example.com", "13800000000"],
    )
    password: str = Field(
        ...,
        description="密码",
        examples=["password123"],
    )
    remember_me: bool = Field(
        default=False,
        description="是否记住我",
    )

    # TODO: 验证码功能待后续测试后启用
    captcha_key: str | None = Field(
        default=None,
        description="验证码标识（暂未启用）",
    )
    captcha_text: str | None = Field(
        default=None,
        min_length=4,
        max_length=6,
        description="验证码内容（暂未启用）",
    )


class RefreshTokenRequest(BaseModel):
    """刷新令牌请求"""

    refresh_token: str = Field(
        ...,
        description="刷新令牌",
    )


class SendEmailCodeRequest(BaseModel):
    """发送邮箱验证码请求"""

    email: EmailAddress = Field(
        ...,
        description="邮箱地址",
        examples=["zhangsan@example.com"],
    )
    purpose: Literal["register", "reset_password"] = Field(
        ...,
        description="用途",
    )

    # TODO: 验证码功能待后续测试后启用
    captcha_key: str | None = Field(
        default=None,
        description="验证码标识（暂未启用）",
    )
    captcha_text: str | None = Field(
        default=None,
        min_length=4,
        max_length=6,
        description="验证码内容（暂未启用）",
    )


class ResetPasswordRequest(BaseModel):
    """密码重置请求"""

    email: EmailAddress = Field(
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
