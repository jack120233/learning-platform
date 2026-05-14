"""标签管理 API 路由

提供标签管理相关的 API 接口。
"""

from fastapi import APIRouter, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import CurrentUser, DBSession
from app.schemas.common import ApiResponse, PageData
from app.schemas.system import BatchTagDeleteRequest, BatchTagDeleteResponse, TagCreate, TagResponse
from app.services.permission_service import permission_service
from app.services.system_service import tag_service

router = APIRouter(prefix="/tags", tags=["标签管理"])


@router.get(
    "",
    response_model=ApiResponse[PageData[TagResponse]],
    summary="标签列表",
    description="获取标签列表，支持关键词搜索和分页",
)
async def get_tags(
    db: DBSession,
    keyword: str | None = Query(default=None, description="搜索关键词"),
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=20, ge=1, le=100, description="每页数量"),
) -> ApiResponse[PageData[TagResponse]]:
    """获取标签列表接口"""
    tags, total = await tag_service.get_list(
        db,
        keyword=keyword,
        page=page,
        page_size=page_size,
    )
    return ApiResponse.success(
        data=PageData.create(
            items=[TagResponse.model_validate(t) for t in tags],
            total=total,
            page=page,
            page_size=page_size,
        ),
    )


@router.post(
    "",
    response_model=ApiResponse[TagResponse],
    summary="创建标签",
    description="创建新的标签",
)
async def create_tag(
    data: TagCreate,
    db: DBSession,
    current_user: CurrentUser,
) -> ApiResponse[TagResponse]:
    """创建标签接口"""
    required_permission = "teacher.course" if current_user.role == "teacher" else "admin.tag"
    await permission_service.ensure_permission(
        db,
        current_user.role,
        required_permission,
        "无权创建标签",
    )
    tag = await tag_service.create(db, data)
    return ApiResponse.success(
        data=TagResponse.model_validate(tag),
        message="创建成功",
    )


@router.delete(
    "/{tag_id}",
    response_model=ApiResponse[None],
    summary="删除标签",
    description="删除指定标签（被课程引用时无法删除）",
)
async def delete_tag(
    tag_id: int,
    db: DBSession,
    current_user: CurrentUser,
) -> ApiResponse[None]:
    """删除标签接口"""
    await permission_service.ensure_permission(
        db,
        current_user.role,
        "admin.tag",
        "无权删除标签",
    )
    await tag_service.delete(db, tag_id)
    return ApiResponse.success(message="删除成功")


@router.post(
    "/batch-delete",
    response_model=ApiResponse[BatchTagDeleteResponse],
    summary="批量删除标签",
    description="批量删除标签，返回成功和失败明细",
)
async def batch_delete_tags(
    data: BatchTagDeleteRequest,
    db: DBSession,
    current_user: CurrentUser,
) -> ApiResponse[BatchTagDeleteResponse]:
    """批量删除标签接口"""
    await permission_service.ensure_permission(
        db,
        current_user.role,
        "admin.tag",
        "无权批量删除标签",
    )
    result = await tag_service.batch_delete(db, data.tag_ids)
    return ApiResponse.success(data=result, message="批量删除完成")
