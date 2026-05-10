"""学习模块 API 路由

提供学习进度管理的 API 接口。
"""

from typing import Any

from fastapi import APIRouter, Query

from app.core.dependencies import CurrentUser, CurrentUserId, DBSession
from app.core.exceptions import ForbiddenException, ValidationException
from app.schemas.common import ApiResponse
from app.schemas.learning import (
    ContinueLearningResponse,
    LearningSessionRequest,
    LearningSessionResponse,
    PlayUrlResponse,
    PreviewResponse,
    ProgressResponse,
    SaveProgressRequest,
    StudentCourseDistributionResponse,
    StudentStatisticsOverviewResponse,
    StudentStatisticsTrendResponse,
)
from app.services.learning_service import learning_service
from app.services.learning_statistics_service import learning_statistics_service

router = APIRouter(prefix="/learning", tags=["学习模块"])


def ensure_student_user(user: CurrentUser) -> None:
    """确保当前用户是学生。"""
    if user.role != "student":
        raise ForbiddenException("仅学生可访问学习统计")


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


@router.post(
    "/sessions",
    response_model=ApiResponse[LearningSessionResponse],
    summary="上报学习会话",
    description="保存学习统计事实，不更新当前进度快照",
)
async def save_learning_session(
    data: LearningSessionRequest,
    db: DBSession,
    user_id: CurrentUserId,
) -> ApiResponse[LearningSessionResponse]:
    """学习会话上报接口。"""
    result = await learning_service.save_session(db, user_id, data)
    return ApiResponse.success(data=LearningSessionResponse(**result), message="保存成功")


@router.get(
    "/statistics/me/overview",
    response_model=ApiResponse[StudentStatisticsOverviewResponse],
    summary="我的学习统计概览",
    description="获取当前学生的个人学习统计概览",
)
async def get_my_statistics_overview(
    db: DBSession,
    current_user: CurrentUser,
) -> ApiResponse[StudentStatisticsOverviewResponse]:
    """学生个人学习统计概览接口。"""
    ensure_student_user(current_user)
    result = await learning_statistics_service.get_student_overview(db, current_user.id)
    return ApiResponse.success(data=StudentStatisticsOverviewResponse(**result), message="获取成功")


@router.get(
    "/statistics/me/trend",
    response_model=ApiResponse[StudentStatisticsTrendResponse],
    summary="我的学习趋势",
    description="获取当前学生 7 天或 30 天学习趋势",
)
async def get_my_statistics_trend(
    db: DBSession,
    current_user: CurrentUser,
    range: str = Query(default="7d", pattern="^(7d|30d)$", description="统计范围：7d 或 30d"),
) -> ApiResponse[StudentStatisticsTrendResponse]:
    """学生个人学习趋势接口。"""
    ensure_student_user(current_user)
    try:
        result = await learning_statistics_service.get_student_trend(db, current_user.id, range)
    except ValueError as exc:
        raise ValidationException(str(exc)) from exc
    return ApiResponse.success(data=StudentStatisticsTrendResponse(**result), message="获取成功")


@router.get(
    "/statistics/me/course-distribution",
    response_model=ApiResponse[StudentCourseDistributionResponse],
    summary="我的课程状态分布",
    description="获取当前学生在学/已完成课程数量",
)
async def get_my_course_distribution(
    db: DBSession,
    current_user: CurrentUser,
) -> ApiResponse[StudentCourseDistributionResponse]:
    """学生个人课程状态分布接口。"""
    ensure_student_user(current_user)
    result = await learning_statistics_service.get_student_course_distribution(db, current_user.id)
    return ApiResponse.success(data=StudentCourseDistributionResponse(**result), message="获取成功")


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
