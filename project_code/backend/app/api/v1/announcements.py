"""公告管理 API 路由

提供公告管理相关的 API 接口。
"""

from fastapi import APIRouter, Query
from sqlalchemy import select

from app.core.dependencies import CurrentUser, DBSession
from app.models.user import User
from app.schemas.common import ApiResponse, PageData
from app.schemas.system import AnnouncementCreate, AnnouncementResponse, AnnouncementUpdate
from app.services.permission_service import permission_service
from app.services.system_service import announcement_service

router = APIRouter(prefix="/announcements", tags=["公告管理"])


async def _get_author_name_map(db: DBSession, author_ids: set[int]) -> dict[int, str]:
    """批量获取作者名称映射。"""
    if not author_ids:
        return {}

    result = await db.execute(
        select(User.id, User.username).where(User.id.in_(author_ids))
    )
    return {
        user_id: username
        for user_id, username in result.all()
    }


def _build_announcement_response(announcement, author_name: str | None = None) -> AnnouncementResponse:
    """构造公告响应对象。"""
    payload = AnnouncementResponse.model_validate(announcement).model_dump()
    payload["author_name"] = author_name
    return AnnouncementResponse(**payload)


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
    keyword: str | None = Query(default=None, description="搜索关键词"),
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=10, ge=1, le=100, description="每页数量"),
) -> ApiResponse[PageData[AnnouncementResponse]]:
    """获取公告列表接口"""
    announcements, total = await announcement_service.get_list(
        db,
        is_published=is_published,
        type=type,
        keyword=keyword,
        page=page,
        page_size=page_size,
    )
    author_name_map = await _get_author_name_map(
        db,
        {announcement.author_id for announcement in announcements if announcement.author_id is not None},
    )
    return ApiResponse.success(
        data=PageData.create(
            items=[
                _build_announcement_response(a, author_name_map.get(a.author_id))
                for a in announcements
            ],
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
    author_name_map = await _get_author_name_map(
        db,
        {announcement.author_id for announcement in announcements if announcement.author_id is not None},
    )
    return ApiResponse.success(
        data=[
            _build_announcement_response(a, author_name_map.get(a.author_id))
            for a in announcements
        ],
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
    author_name_map = await _get_author_name_map(
        db,
        {announcement.author_id} if announcement.author_id is not None else set(),
    )
    return ApiResponse.success(
        data=_build_announcement_response(announcement, author_name_map.get(announcement.author_id)),
    )


@router.post(
    "",
    response_model=ApiResponse[AnnouncementResponse],
    summary="创建公告",
    description="创建新的系统公告",
)
async def create_announcement(
    data: AnnouncementCreate,
    db: DBSession,
    current_user: CurrentUser,
) -> ApiResponse[AnnouncementResponse]:
    """创建公告接口。"""
    await permission_service.ensure_permission(
        db,
        current_user.role,
        "admin.announcement",
        "无权创建公告",
    )
    announcement = await announcement_service.create(db, data, current_user.id)
    return ApiResponse.success(
        data=_build_announcement_response(
            announcement,
            current_user.username,
        ),
        message="创建成功",
    )


@router.post(
    "/{announcement_id}",
    response_model=ApiResponse[AnnouncementResponse],
    summary="更新公告",
    description="更新指定公告的信息",
)
async def update_announcement(
    announcement_id: int,
    data: AnnouncementUpdate,
    db: DBSession,
    current_user: CurrentUser,
) -> ApiResponse[AnnouncementResponse]:
    """更新公告接口。"""
    await permission_service.ensure_permission(
        db,
        current_user.role,
        "admin.announcement",
        "无权修改公告",
    )
    announcement = await announcement_service.update(db, announcement_id, data)
    author_name_map = await _get_author_name_map(
        db,
        {announcement.author_id} if announcement.author_id is not None else set(),
    )
    return ApiResponse.success(
        data=_build_announcement_response(announcement, author_name_map.get(announcement.author_id)),
        message="更新成功",
    )


@router.post(
    "/{announcement_id}/delete",
    response_model=ApiResponse[None],
    summary="删除公告",
    description="删除指定公告",
)
async def delete_announcement(
    announcement_id: int,
    db: DBSession,
    current_user: CurrentUser,
) -> ApiResponse[None]:
    """删除公告接口。"""
    await permission_service.ensure_permission(
        db,
        current_user.role,
        "admin.announcement",
        "无权删除公告",
    )
    await announcement_service.delete(db, announcement_id)
    return ApiResponse.success(message="删除成功")
