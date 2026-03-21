"""刷新令牌数据模型

定义刷新令牌相关的数据库模型。
"""

from datetime import datetime

from sqlalchemy import DateTime, String, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class RefreshToken(BaseModel):
    """刷新令牌模型

    存储刷新令牌记录，用于令牌刷新和失效管理。

    Attributes:
        token: 刷新令牌值
        user_id: 关联用户ID
        expires_at: 过期时间
        is_revoked: 是否已撤销
        device_info: 设备信息
        ip_address: IP地址
    """

    __tablename__ = "refresh_tokens"

    token: Mapped[str] = mapped_column(
        String(500),
        unique=True,
        index=True,
        nullable=False,
        comment="刷新令牌值",
    )
    user_id: Mapped[int] = mapped_column(
        nullable=False,
        index=True,
        comment="关联用户ID",
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        comment="过期时间",
    )
    is_revoked: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
        comment="是否已撤销",
    )
    device_info: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="设备信息",
    )
    ip_address: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="IP地址",
    )

    def __repr__(self) -> str:
        return f"<RefreshToken(id={self.id}, user_id={self.user_id})>"

    @property
    def is_expired(self) -> bool:
        """检查令牌是否过期"""
        return datetime.utcnow() > self.expires_at

    @property
    def is_valid(self) -> bool:
        """检查令牌是否有效"""
        return not self.is_revoked and not self.is_expired