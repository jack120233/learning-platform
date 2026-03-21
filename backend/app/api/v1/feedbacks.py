"""反馈管理 API 路由

提供反馈管理相关的 API 接口。
"""

import json

from fastapi import APIRouter, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import DBSession, CurrentUserId
from app.schemas.common import ApiResponse, PageData
from app.schemas.feedback import (
    FeedbackCreate,
    FeedbackResponse,
    FeedbackProcess,
)
from app.services.feedback_service import feedback_service

router = APIRouter(prefix="/feedbacks", tags=["反馈管理"])


@router.post(
    "",
    response_model=ApiResponse[FeedbackResponse],
    summary="提交反馈",
    description="提交用户反馈",
)
async def create_feedback(
    data: FeedbackCreate,
    db: DBSession,
    user_id: CurrentUserId,
) -> ApiResponse[FeedbackResponse]:
    """提交反馈接口"""
    feedback = await feedback_service.create(db, user_id, data)
    return ApiResponse.success(
        data=FeedbackResponse.model_validate(feedback),
        message="提交成功",
    )


@router.get(
    "",
    response_model=ApiResponse[PageData[FeedbackResponse]],
    summary="反馈列表",
    description="获取反馈列表（用户查看自己的反馈，管理员查看所有）",
)
async def get_feedbacks(
    db: DBSession,
    user_id: CurrentUserId,
    status: str | None = Query(default=None, description="状态筛选"),
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=10, ge=1, le=50, description="每页数量"),
) -> ApiResponse[PageData[FeedbackResponse]]:
    """获取反馈列表接口"""
    # 实际项目中需要根据用户角色决定是否传入 user_id
    feedbacks, total = await feedback_service.get_list(
        db,
        user_id=user_id,  # 普通用户只能看自己的反馈
        status=status,
        page=page,
        page_size=page_size,
    )

    items = []
    for f in feedbacks:
        f_dict = {
            "id": f.id,
            "user_id": f.user_id,
            "type": f.type,
            "title": f.title,
            "content": f.content,
            "contact": f.contact,
            "images": json.loads(f.images) if f.images else None,
            "status": f.status,
            "reply": f.reply,
            "replied_at": f.replied_at,
            "created_at": f.created_at,
        }
        items.append(FeedbackResponse(**f_dict))

    return ApiResponse.success(
        data=PageData.create(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
        ),
    )


@router.get(
    "/{feedback_id}",
    response_model=ApiResponse[FeedbackResponse],
    summary="反馈详情",
    description="获取指定反馈的详细信息",
)
async def get_feedback(
    feedback_id: int,
    db: DBSession,
    user_id: CurrentUserId,
) -> ApiResponse[FeedbackResponse]:
    """获取反馈详情接口"""
    feedback = await feedback_service.get_by_id(db, feedback_id)
    if not feedback:
        from app.core.exceptions import NotFoundException
        raise NotFoundException("反馈不存在")

    f_dict = {
        "id": feedback.id,
        "user_id": feedback.user_id,
        "type": feedback.type,
        "title": feedback.title,
        "content": feedback.content,
        "contact": feedback.contact,
        "images": json.loads(feedback.images) if feedback.images else None,
        "status": feedback.status,
        "reply": feedback.reply,
        "replied_at": feedback.replied_at,
        "created_at": feedback.created_at,
    }
    return ApiResponse.success(data=FeedbackResponse(**f_dict))


@router.post(
    "/{feedback_id}/process",
    response_model=ApiResponse[FeedbackResponse],
    summary="标记已处理",
    description="处理反馈（管理员）",
)
async def process_feedback(
    feedback_id: int,
    data: FeedbackProcess,
    db: DBSession,
    user_id: CurrentUserId,
) -> ApiResponse[FeedbackResponse]:
    """处理反馈接口（管理员）"""
    feedback = await feedback_service.process(db, feedback_id, data, user_id)
    return ApiResponse.success(
        data=FeedbackResponse.model_validate(feedback),
        message="处理成功",
    )