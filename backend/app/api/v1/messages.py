"""消息管理 API 路由

提供消息管理相关的 API 接口。
"""

from fastapi import APIRouter, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import DBSession, CurrentUserId
from app.schemas.common import ApiResponse, PageData
from app.schemas.message import (
    MessageResponse,
    MessageSend,
    UnreadCountResponse,
)
from app.services.message_service import message_service

router = APIRouter(prefix="/messages", tags=["消息管理"])


@router.get(
    "",
    response_model=ApiResponse[PageData[MessageResponse]],
    summary="消息列表",
    description="获取当前用户的消息列表",
)
async def get_messages(
    db: DBSession,
    user_id: CurrentUserId,
    type: str | None = Query(default=None, description="类型筛选"),
    is_read: bool | None = Query(default=None, description="已读状态"),
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=10, ge=1, le=50, description="每页数量"),
) -> ApiResponse[PageData[MessageResponse]]:
    """获取消息列表接口"""
    messages, total = await message_service.get_list(
        db,
        user_id=user_id,
        type=type,
        is_read=is_read,
        page=page,
        page_size=page_size,
    )
    return ApiResponse.success(
        data=PageData.create(
            items=[MessageResponse.model_validate(m) for m in messages],
            total=total,
            page=page,
            page_size=page_size,
        ),
    )


@router.get(
    "/{message_id:int}",
    response_model=ApiResponse[MessageResponse],
    summary="消息详情",
    description="获取指定消息的详细信息",
)
async def get_message(
    message_id: int,
    db: DBSession,
    user_id: CurrentUserId,
) -> ApiResponse[MessageResponse]:
    """获取消息详情接口"""
    message = await message_service.get_by_id(db, message_id, user_id)
    if not message:
        from app.core.exceptions import NotFoundException
        raise NotFoundException("消息不存在")
    return ApiResponse.success(data=MessageResponse.model_validate(message))


@router.post(
    "/{message_id:int}/read",
    response_model=ApiResponse[MessageResponse],
    summary="标记已读",
    description="标记指定消息为已读",
)
async def mark_message_read(
    message_id: int,
    db: DBSession,
    user_id: CurrentUserId,
) -> ApiResponse[MessageResponse]:
    """标记已读接口"""
    message = await message_service.mark_read(db, message_id, user_id)
    return ApiResponse.success(
        data=MessageResponse.model_validate(message),
        message="已标记为已读",
    )


@router.post(
    "/mark-all-read",
    response_model=ApiResponse[dict],
    summary="批量已读",
    description="标记所有消息为已读",
)
async def mark_all_read(
    db: DBSession,
    user_id: CurrentUserId,
) -> ApiResponse[dict]:
    """批量已读接口"""
    count = await message_service.mark_all_read(db, user_id)
    return ApiResponse.success(
        data={"count": count},
        message=f"已标记{count}条消息为已读",
    )


@router.delete(
    "/{message_id:int}",
    response_model=ApiResponse[None],
    summary="删除消息",
    description="删除指定消息",
)
async def delete_message(
    message_id: int,
    db: DBSession,
    user_id: CurrentUserId,
) -> ApiResponse[None]:
    """删除消息接口"""
    await message_service.delete(db, message_id, user_id)
    return ApiResponse.success(message="删除成功")


@router.get(
    "/unread-count",
    response_model=ApiResponse[UnreadCountResponse],
    summary="未读数量",
    description="获取各类型未读消息数量",
)
async def get_unread_count(
    db: DBSession,
    user_id: CurrentUserId,
) -> ApiResponse[UnreadCountResponse]:
    """获取未读数量接口"""
    result = await message_service.get_unread_count(db, user_id)
    return ApiResponse.success(data=UnreadCountResponse(**result))


@router.post(
    "/send",
    response_model=ApiResponse[MessageResponse],
    summary="发送系统消息",
    description="发送系统消息（管理员）",
)
async def send_message(
    data: MessageSend,
    db: DBSession,
    user_id: CurrentUserId,
) -> ApiResponse[MessageResponse]:
    """发送消息接口（管理员）"""
    message = await message_service.send(db, data)
    return ApiResponse.success(
        data=MessageResponse.model_validate(message),
        message="发送成功",
    )
