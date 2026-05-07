"""学习模块 API 路由

提供学习进度管理的 API 接口。
"""

from typing import Any

from fastapi import APIRouter, Query

from app.core.dependencies import DBSession, CurrentUserId
from app.schemas.common import ApiResponse
from app.schemas.learning import (
    ContinueLearningResponse,
    PlayUrlResponse,
    PreviewResponse,
    ProgressResponse,
    SaveProgressRequest,
)
from app.services.learning_service import learning_service

router = APIRouter(prefix="/learning", tags=["学习模块"])


@router.post(
    "/courses/{course_id}/start",
    response_model=ApiResponse[dict],
    summary="开始学习",
    description="开始学习指定课程",
)
async def start_learning(
    course_id: int,
    db: DBSession,
    user_id: CurrentUserId,
) -> ApiResponse[dict]:
    """开始学习接口"""
    result = await learning_service.start_learning(db, user_id, course_id)
    return ApiResponse.success(data=result)


@router.post(
    "/progress",
    response_model=ApiResponse[ProgressResponse],
    summary="保存进度",
    description="保存学习进度",
)
async def save_progress(
    data: SaveProgressRequest,
    db: DBSession,
    user_id: CurrentUserId,
) -> ApiResponse[ProgressResponse]:
    """保存进度接口"""
    progress = await learning_service.save_progress(db, user_id, data)
    total_time = data.total_time if data.total_time is not None else 0
    return ApiResponse.success(
        data=ProgressResponse(**learning_service._to_progress_payload(progress, total_time)),
        message="保存成功",
    )


@router.get(
    "/progress",
    response_model=ApiResponse[Any],
    summary="获取进度",
    description="获取课程学习进度",
)
async def get_progress(
    course_id: int | None = Query(default=None, description="课程ID"),
    section_id: int | None = Query(default=None, description="小节ID"),
    resource_id: int | None = Query(default=None, description="资源ID"),
    db: DBSession = None,
    user_id: CurrentUserId = None,
) -> ApiResponse[Any]:
    """获取进度接口"""
    progress_list = await learning_service.get_progress(
        db,
        user_id,
        course_id=course_id,
        section_id=section_id,
        resource_id=resource_id,
    )
    serialized = [ProgressResponse(**p) for p in progress_list]

    if resource_id is not None and course_id is None:
        return ApiResponse.success(data=serialized[0], message="获取成功")

    return ApiResponse.success(data=serialized, message="获取成功")


@router.get(
    "/courses/{course_id}/continue",
    response_model=ApiResponse[ContinueLearningResponse],
    summary="继续学习",
    description="获取继续学习信息",
)
async def continue_learning(
    course_id: int,
    db: DBSession,
    user_id: CurrentUserId,
) -> ApiResponse[ContinueLearningResponse]:
    """继续学习接口"""
    result = await learning_service.get_continue_info(db, user_id, course_id)
    return ApiResponse.success(data=ContinueLearningResponse(**result))


@router.get(
    "/resources/{resource_id}/play",
    response_model=ApiResponse[PlayUrlResponse],
    summary="获取播放地址",
    description="获取视频播放地址",
)
async def get_play_url(
    resource_id: int,
    db: DBSession,
    user_id: CurrentUserId,
) -> ApiResponse[PlayUrlResponse]:
    """获取播放地址接口"""
    result = await learning_service.get_play_url(db, user_id, resource_id)
    return ApiResponse.success(data=PlayUrlResponse(**result))


@router.get(
    "/resources/{resource_id}/preview",
    response_model=ApiResponse[PreviewResponse],
    summary="文档预览",
    description="获取文档预览地址",
)
async def get_preview_url(
    resource_id: int,
    db: DBSession,
    user_id: CurrentUserId,
) -> ApiResponse[PreviewResponse]:
    """获取预览地址接口"""
    result = await learning_service.get_preview_url(db, user_id, resource_id)
    return ApiResponse.success(data=PreviewResponse(**result))
