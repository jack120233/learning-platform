"""角色权限管理相关 Pydantic 模型。"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator


RoleName = Literal["student", "teacher", "admin"]


class PermissionTreeItem(BaseModel):
    """权限树节点。"""

    permission_id: int = Field(description="权限ID")
    name: str = Field(description="权限名称")
    code: str = Field(description="权限编码")
    description: str = Field(default="", description="权限描述")
    parent_id: int | None = Field(default=None, description="父级权限ID")
    children: list["PermissionTreeItem"] = Field(default_factory=list, description="子权限")


class RolePermissionUpdateRequest(BaseModel):
    """更新角色权限请求。"""

    permissions: list[int] = Field(default_factory=list, description="权限ID数组")

    @field_validator("permissions")
    @classmethod
    def normalize_permissions(cls, value: list[int]) -> list[int]:
        """去重并保持升序，避免重复权限ID导致约束冲突。"""
        return sorted(set(value))
