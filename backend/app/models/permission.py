"""权限管理相关数据库模型。"""

from sqlalchemy import ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class Permission(BaseModel):
    """权限定义表。"""

    __tablename__ = "permissions"

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="权限名称",
    )
    code: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        index=True,
        comment="权限编码",
    )
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="",
        comment="权限描述",
    )
    parent_id: Mapped[int | None] = mapped_column(
        ForeignKey("permissions.id"),
        nullable=True,
        index=True,
        comment="父级权限ID",
    )
    sort_order: Mapped[int] = mapped_column(
        default=0,
        nullable=False,
        comment="排序序号",
    )


class RolePermission(BaseModel):
    """角色与权限关联表。"""

    __tablename__ = "role_permissions"
    __table_args__ = (
        UniqueConstraint("role", "permission_id", name="uq_role_permissions_role_permission"),
        Index("idx_role_permissions_role", "role"),
    )

    role: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="角色编码",
    )
    permission_id: Mapped[int] = mapped_column(
        ForeignKey("permissions.id"),
        nullable=False,
        comment="权限ID",
    )
