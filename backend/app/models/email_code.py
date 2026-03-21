"""邮箱验证码数据模型

定义邮箱验证码相关的数据库模型。
"""

from datetime import datetime

from sqlalchemy import DateTime, Enum, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class EmailCode(BaseModel):
    """邮箱验证码模型

    存储邮箱验证码记录，用于注册验证和密码重置。

    Attributes:
        email: 邮箱地址
        code: 验证码
        purpose: 用途（register/reset_password）
        is_used: 是否已使用
        expires_at: 过期时间
    """

    __tablename__ = "email_codes"

    email: Mapped[str] = mapped_column(
        String(100),
        index=True,
        nullable=False,
        comment="邮箱地址",
    )
    code: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        comment="验证码",
    )
    purpose: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="register",
        comment="用途",
    )
    is_used: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
        comment="是否已使用",
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        comment="过期时间",
    )

    def __repr__(self) -> str:
        return f"<EmailCode(id={self.id}, email={self.email}, purpose={self.purpose})>"

    @property
    def is_expired(self) -> bool:
        """检查验证码是否过期"""
        return datetime.utcnow() > self.expires_at

    @property
    def is_valid(self) -> bool:
        """检查验证码是否有效"""
        return not self.is_used and not self.is_expired