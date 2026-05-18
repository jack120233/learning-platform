"""角色权限管理 API 路由。"""

from typing import Literal

from fastapi import APIRouter

from app.core.dependencies import CurrentUser, DBSession
from app.schemas.common import ApiResponse
from app.schemas.permission import PermissionTreeItem, RolePermissionUpdateRequest
from app.services.permission_service import permission_service

router = APIRouter(tags=["角色权限管理"])


@router.get(
    "/permissions/tree",
    response_model=ApiResponse[list[PermissionTreeItem]],
    summary="获取权限树",
    description="获取角色权限管理页面使用的权限树数据",
)
async def get_permission_tree(
    db: DBSession,
    current_user: CurrentUser,
) -> ApiResponse[list[PermissionTreeItem]]:
    """获取权限树接口。"""
    permission_service.ensure_admin(current_user.role, "无权查看角色权限配置")
    permission_tree = await permission_service.get_permission_tree(db)
    return ApiResponse.success(
        data=[PermissionTreeItem.model_validate(item) for item in permission_tree]
    )


@router.get(
    "/users/me/permissions",
    response_model=ApiResponse[list[str]],
    summary="获取当前用户权限编码",
    description="获取当前登录用户所属角色的权限编码列表，用于前端权限控制",
)
async def get_current_user_permissions(
    db: DBSession,
    current_user: CurrentUser,
) -> ApiResponse[list[str]]:
    """获取当前用户权限编码接口。"""
    permission_codes = await permission_service.get_role_permission_codes(db, current_user.effective_role)
    return ApiResponse.success(data=permission_codes)


@router.get(
    "/roles/{role}/permissions",
    response_model=ApiResponse[list[int]],
    summary="获取角色权限",
    description="获取指定角色当前配置的权限ID列表",
)
async def get_role_permissions(
    role: Literal["student", "teacher", "admin"],
    db: DBSession,
    current_user: CurrentUser,
) -> ApiResponse[list[int]]:
    """获取角色权限接口。"""
    if current_user.role != role:
        permission_service.ensure_admin(current_user.role, "无权查看角色权限配置")
    permission_ids = await permission_service.get_role_permissions(db, role)
    return ApiResponse.success(data=permission_ids)


@router.post(
    "/roles/{role}/permissions",
    response_model=ApiResponse[None],
    summary="更新角色权限",
    description="更新指定角色的权限配置",
)
async def update_role_permissions(
    role: Literal["student", "teacher", "admin"],
    data: RolePermissionUpdateRequest,
    db: DBSession,
    current_user: CurrentUser,
) -> ApiResponse[None]:
    """更新角色权限接口。"""
    permission_service.ensure_admin(current_user.role, "无权修改角色权限配置")
    await permission_service.update_role_permissions(db, role, data.permissions)
    return ApiResponse.success(message="权限配置已更新")
