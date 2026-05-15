"""用户数据模型

定义用户相关的数据库模型。
"""

from datetime import datetime
from typing import Literal

from sqlalchemy import DateTime, Enum, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class User(BaseModel):
    """用户模型

    存储用户基本信息和账户状态。

    Attributes:
        username: 用户名，唯一
        email: 邮箱地址，唯一
        phone: 手机号码，可选，唯一
        password_hash: 密码哈希值
        nickname: 昵称
        avatar: 头像URL
        bio: 个人简介
        role: 用户角色（student/teacher/admin）
        status: 账户状态（active/disabled/pending）
        last_login_at: 最后登录时间
        login_fail_count: 连续登录失败次数
        locked_until: 账户锁定截止时间
    """

    __tablename__ = "users"

    username: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=False,
        comment="用户名",
    )
    original_username: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="历史用户名记录",
    )
    username_change_remaining: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
        comment="剩余用户名修改次数",
    )
    email: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        index=True,
        nullable=False,
        comment="邮箱地址",
    )
    phone: Mapped[str | None] = mapped_column(
        String(20),
        unique=True,
        nullable=True,
        comment="手机号码",
    )
    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="密码哈希值",
    )
    nickname: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="昵称",
    )
    avatar: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="头像URL",
    )
    bio: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="个人简介",
    )
    role: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="student",
        index=True,
        comment="用户角色",
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="active",
        index=True,
        comment="账户状态",
    )
    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="最后登录时间",
    )
    login_fail_count: Mapped[int] = mapped_column(
        default=0,
        nullable=False,
        comment="连续登录失败次数",
    )
    locked_until: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="账户锁定截止时间",
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username={self.username}, role={self.role})>"

    @property
    def user_id(self) -> int:
        return self.id

    @property
    def effective_role(self) -> str:
        if self.role == "teacher" and self.status == "pending":
            return "student"
        return self.role

    @property
    def is_pending_teacher(self) -> bool:
        return self.role == "teacher" and self.status == "pending"

    @property
    def can_change_username(self) -> bool:
        return self.role != "student" or self.username_change_remaining > 0

    @property
    def is_locked(self) -> bool:
        """检查账户是否被锁定"""
        if self.locked_until is None:
            return False
        return datetime.utcnow() < self.locked_until

    @property
    def is_active(self) -> bool:
        """检查账户是否活跃"""
        return self.status == "active" and not self.is_locked