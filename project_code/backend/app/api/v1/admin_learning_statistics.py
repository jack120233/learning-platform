"""管理员平台学习统计 API 路由。"""

from fastapi import APIRouter, Query

from app.core.dependencies import CurrentUser, DBSession
from app.schemas.common import ApiResponse
from app.schemas.learning import (
    AdminLearningStatisticsOverviewResponse,
    AdminLearningStatisticsTrendResponse,
    AdminLowCompletionCourseStatisticsItem,
    AdminPopularCourseStatisticsItem,
)
from app.services.admin_learning_statistics_service import admin_learning_statistics_service

router = APIRouter(prefix="/admin/learning-statistics", tags=["管理员学习统计"])


@router.get(
    "/overview",
    response_model=ApiResponse[AdminLearningStatisticsOverviewResponse],
    summary="平台学习统计概览",
    description="获取平台学习统计概览",
)
async def get_admin_learning_statistics_overview(
    db: DBSession,
    current_user: CurrentUser,
    range: str = Query(default="7d", description="7d/30d/all"),
    category_id: int | None = Query(default=None, description="分类ID"),
    teacher_id: int | None = Query(default=None, description="讲师ID"),
    course_status: str = Query(default="all", description="课程状态"),
) -> ApiResponse[AdminLearningStatisticsOverviewResponse]:
    data = await admin_learning_statistics_service.get_overview(
        db,
        current_user,
        trend_range=range,
        category_id=category_id,
        teacher_id=teacher_id,
        course_status=course_status,
    )
    return ApiResponse.success(data=AdminLearningStatisticsOverviewResponse(**data))


@router.get(
    "/trend",
    response_model=ApiResponse[AdminLearningStatisticsTrendResponse],
    summary="平台学习趋势",
    description="获取平台学习趋势",
)
async def get_admin_learning_statistics_trend(
    db: DBSession,
    current_user: CurrentUser,
    range: str = Query(default="7d", description="7d/30d"),
    metric: str = Query(default="duration", description="duration/active_students/completed_courses"),
    category_id: int | None = Query(default=None, description="分类ID"),
    teacher_id: int | None = Query(default=None, description="讲师ID"),
    course_status: str = Query(default="all", description="课程状态"),
) -> ApiResponse[AdminLearningStatisticsTrendResponse]:
    data = await admin_learning_statistics_service.get_trend(
        db,
        current_user,
        trend_range=range,
        metric=metric,
        category_id=category_id,
        teacher_id=teacher_id,
        course_status=course_status,
    )
    return ApiResponse.success(data=AdminLearningStatisticsTrendResponse(**data))


@router.get(
    "/popular-courses",
    response_model=ApiResponse[list[AdminPopularCourseStatisticsItem]],
    summary="热门课程统计",
    description="获取热门课程统计列表",
)
async def get_admin_learning_statistics_popular_courses(
    db: DBSession,
    current_user: CurrentUser,
    range: str = Query(default="7d", description="7d/30d/all"),
    category_id: int | None = Query(default=None, description="分类ID"),
    teacher_id: int | None = Query(default=None, description="讲师ID"),
    course_status: str = Query(default="all", description="课程状态"),
    limit: int = Query(default=10, ge=1, le=50, description="返回数量"),
) -> ApiResponse[list[AdminPopularCourseStatisticsItem]]:
    rows = await admin_learning_statistics_service.get_popular_courses(
        db,
        current_user,
        trend_range=range,
        category_id=category_id,
        teacher_id=teacher_id,
        course_status=course_status,
        limit=limit,
    )
    return ApiResponse.success(data=[AdminPopularCourseStatisticsItem(**row) for row in rows])


@router.get(
    "/low-completion-courses",
    response_model=ApiResponse[list[AdminLowCompletionCourseStatisticsItem]],
    summary="低完成率课程统计",
    description="获取低完成率课程统计列表",
)
async def get_admin_learning_statistics_low_completion_courses(
    db: DBSession,
    current_user: CurrentUser,
    range: str = Query(default="7d", description="7d/30d/all"),
    category_id: int | None = Query(default=None, description="分类ID"),
    teacher_id: int | None = Query(default=None, description="讲师ID"),
    course_status: str = Query(default="all", description="课程状态"),
    limit: int = Query(default=10, ge=1, le=50, description="返回数量"),
) -> ApiResponse[list[AdminLowCompletionCourseStatisticsItem]]:
    rows = await admin_learning_statistics_service.get_low_completion_courses(
        db,
        current_user,
        trend_range=range,
        category_id=category_id,
        teacher_id=teacher_id,
        course_status=course_status,
        limit=limit,
    )
    return ApiResponse.success(data=[AdminLowCompletionCourseStatisticsItem(**row) for row in rows])
