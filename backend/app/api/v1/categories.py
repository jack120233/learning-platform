"""分类管理 API 路由

提供分类管理相关的 API 接口。
"""

from fastapi import APIRouter, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import DBSession
from app.schemas.common import ApiResponse, PageData
from app.schemas.system import (
    CategoryCreate,
    CategoryResponse,
    CategoryUpdate,
)
from app.services.system_service import category_service

router = APIRouter(prefix="/categories", tags=["分类管理"])


@router.get(
    "",
    response_model=ApiResponse[list[CategoryResponse]],
    summary="分类列表",
    description="获取分类列表，支持按父分类和状态筛选",
)
async def get_categories(
    db: DBSession,
    parent_id: int | None = Query(default=None, description="父分类ID"),
    is_active: bool | None = Query(default=None, description="是否启用"),
) -> ApiResponse[list[CategoryResponse]]:
    """获取分类列表接口"""
    categories = await category_service.get_list(
        db,
        parent_id=parent_id,
        is_active=is_active,
    )
    return ApiResponse.success(
        data=[CategoryResponse.model_validate(c) for c in categories],
    )


@router.post(
    "",
    response_model=ApiResponse[CategoryResponse],
    summary="创建分类",
    description="创建新的分类",
)
async def create_category(
    data: CategoryCreate,
    db: DBSession,
) -> ApiResponse[CategoryResponse]:
    """创建分类接口"""
    category = await category_service.create(db, data)
    return ApiResponse.success(
        data=CategoryResponse.model_validate(category),
        message="创建成功",
    )


@router.put(
    "/{category_id}",
    response_model=ApiResponse[CategoryResponse],
    summary="更新分类",
    description="更新指定分类的信息",
)
async def update_category(
    category_id: int,
    data: CategoryUpdate,
    db: DBSession,
) -> ApiResponse[CategoryResponse]:
    """更新分类接口"""
    category = await category_service.update(db, category_id, data)
    return ApiResponse.success(
        data=CategoryResponse.model_validate(category),
        message="更新成功",
    )


@router.delete(
    "/{category_id}",
    response_model=ApiResponse[None],
    summary="删除分类",
    description="删除指定分类（存在子分类时无法删除）",
)
async def delete_category(
    category_id: int,
    db: DBSession,
) -> ApiResponse[None]:
    """删除分类接口"""
    await category_service.delete(db, category_id)
    return ApiResponse.success(message="删除成功")