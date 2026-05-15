"""老师课程学习统计 API 路由。"""

from fastapi import APIRouter, Query
from fastapi.responses import Response

from app.core.dependencies import CurrentUser, DBSession
from app.schemas.common import ApiResponse, PageData
from app.schemas.learning import (
    TeacherCourseStatisticsItem,
    TeacherCourseStatisticsOverviewResponse,
    TeacherCourseStudentStatisticsItem,
)
from app.services.teacher_statistics_service import teacher_statistics_service

router = APIRouter(prefix="/teacher/statistics", tags=["老师课程统计"])


@router.get(
    "/courses",
    response_model=ApiResponse[PageData[TeacherCourseStatisticsItem]],
    summary="老师可查看统计课程列表",
    description="获取当前老师负责或被授权查看统计的课程列表",
)
async def get_teacher_statistics_courses(
    db: DBSession,
    current_user: CurrentUser,
    keyword: str | None = Query(default=None, description="关键词"),
    permission_type: str = Query(default="all", description="all/owner/authorized"),
    status: str = Query(default="all", description="all/draft/published/archived"),
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=10, ge=1, le=50, description="每页数量"),
) -> ApiResponse[PageData[TeacherCourseStatisticsItem]]:
    """老师可查看统计课程列表。"""
    items, total = await teacher_statistics_service.list_courses(
        db,
        current_user,
        keyword=keyword,
        permission_type=permission_type,
        status=status,
        page=page,
        page_size=page_size,
    )
    return ApiResponse.success(
        data=PageData.create(
            items=[TeacherCourseStatisticsItem(**item) for item in items],
            total=total,
            page=page,
            page_size=page_size,
        )
    )


@router.get(
    "/courses/{course_id}/overview",
    response_model=ApiResponse[TeacherCourseStatisticsOverviewResponse],
    summary="老师课程统计概览",
    description="获取单门课程学习统计概览",
)
async def get_teacher_course_statistics_overview(
    course_id: int,
    db: DBSession,
    current_user: CurrentUser,
    range: str = Query(default="7d", description="7d/30d"),
) -> ApiResponse[TeacherCourseStatisticsOverviewResponse]:
    """老师课程统计概览。"""
    data = await teacher_statistics_service.get_overview(db, course_id, current_user, trend_range=range)
    return ApiResponse.success(data=TeacherCourseStatisticsOverviewResponse(**data))


@router.get(
    "/courses/{course_id}/students",
    response_model=ApiResponse[PageData[TeacherCourseStudentStatisticsItem]],
    summary="老师课程学生学习明细",
    description="分页获取课程学生学习明细",
)
async def get_teacher_course_statistics_students(
    course_id: int,
    db: DBSession,
    current_user: CurrentUser,
    status: str = Query(default="all", description="all/inactive/low_progress/completed"),
    keyword: str | None = Query(default=None, description="学生用户名关键词"),
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=10, ge=1, le=100, description="每页数量"),
) -> ApiResponse[PageData[TeacherCourseStudentStatisticsItem]]:
    """老师课程学生学习明细。"""
    items, total = await teacher_statistics_service.list_students(
        db,
        course_id,
        current_user,
        status=status,
        keyword=keyword,
        page=page,
        page_size=page_size,
    )
    return ApiResponse.success(
        data=PageData.create(
            items=[TeacherCourseStudentStatisticsItem(**item) for item in items],
            total=total,
            page=page,
            page_size=page_size,
        )
    )


@router.get(
    "/courses/{course_id}/students/export",
    summary="导出老师课程学生学习明细",
    description="按当前筛选条件导出 CSV",
)
async def export_teacher_course_statistics_students(
    course_id: int,
    db: DBSession,
    current_user: CurrentUser,
    status: str = Query(default="all", description="all/inactive/low_progress/completed"),
    keyword: str | None = Query(default=None, description="学生用户名关键词"),
) -> Response:
    """导出老师课程学生学习明细。"""
    csv_text = await teacher_statistics_service.export_students_csv(
        db,
        course_id,
        current_user,
        status=status,
        keyword=keyword,
    )
    return Response(
        content=csv_text.encode("utf-8"),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="course-{course_id}-students.csv"'},
    )
