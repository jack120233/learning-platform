"""公告管理 API 路由

提供公告管理相关的 API 接口。
"""

from fastapi import APIRouter, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import DBSession
from app.schemas.common import ApiResponse, PageData
from app.schemas.system import AnnouncementResponse
from app.services.system_service import announcement_service

router = APIRouter(prefix="/announcements", tags=["公告管理"])


@router.get(
    "",
    response_model=ApiResponse[PageData[AnnouncementResponse]],
    summary="公告列表",
    description="获取公告列表，支持按类型和发布状态筛选",
)
async def get_announcements(
    db: DBSession,
    is_published: bool | None = Query(default=None, description="是否已发布"),
    type: str | None = Query(default=None, description="公告类型"),
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=10, ge=1, le=100, description="每页数量"),
) -> ApiResponse[PageData[AnnouncementResponse]]:
    """获取公告列表接口"""
    announcements, total = await announcement_service.get_list(
        db,
        is_published=is_published,
        type=type,
        page=page,
        page_size=page_size,
    )
    return ApiResponse.success(
        data=PageData.create(
            items=[AnnouncementResponse.model_validate(a) for a in announcements],
            total=total,
            page=page,
            page_size=page_size,
        ),
    )


@router.get(
    "/active",
    response_model=ApiResponse[list[AnnouncementResponse]],
    summary="有效公告列表",
    description="获取当前有效的公告列表（用于前台展示）",
)
async def get_active_announcements(
    db: DBSession,
    limit: int = Query(default=5, ge=1, le=20, description="返回数量"),
) -> ApiResponse[list[AnnouncementResponse]]:
    """获取有效公告列表接口"""
    announcements = await announcement_service.get_active_list(db, limit)
    return ApiResponse.success(
        data=[AnnouncementResponse.model_validate(a) for a in announcements],
    )


@router.get(
    "/{announcement_id}",
    response_model=ApiResponse[AnnouncementResponse],
    summary="公告详情",
    description="获取指定公告的详细信息",
)
async def get_announcement(
    announcement_id: int,
    db: DBSession,
) -> ApiResponse[AnnouncementResponse]:
    """获取公告详情接口"""
    announcement = await announcement_service.get_by_id(db, announcement_id)
    if not announcement:
        from app.core.exceptions import NotFoundException
        raise NotFoundException("公告不存在")
    return ApiResponse.success(
        data=AnnouncementResponse.model_validate(announcement),
    )