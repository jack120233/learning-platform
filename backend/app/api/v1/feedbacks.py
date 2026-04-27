"""反馈管理 API 路由。

提供反馈管理相关的 API 接口。
"""

from fastapi import APIRouter, Query

from app.core.dependencies import CurrentUser, DBSession
from app.core.exceptions import ForbiddenException, NotFoundException
from app.schemas.common import ApiResponse, PageData
from app.schemas.feedback import (
    FeedbackBatchProcess,
    FeedbackCreate,
    FeedbackProcess,
    FeedbackResponse,
)
from app.services.feedback_service import feedback_service
from app.services.permission_service import permission_service


async def has_feedback_admin_permission(db: DBSession, role: str) -> bool:
    """判断当前角色是否拥有反馈管理权限。"""
    permission_codes = await permission_service.get_role_permission_codes(db, role)
    return "admin.feedback" in permission_codes

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
    current_user: CurrentUser,
) -> ApiResponse[FeedbackResponse]:
    """提交反馈接口"""
    feedback = await feedback_service.create(db, current_user.id, data)
    detail = await feedback_service.get_by_id(db, feedback.id)
    return ApiResponse.success(
        data=FeedbackResponse.model_validate(detail),
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
    current_user: CurrentUser,
    feedback_type: str | None = Query(default=None, description="类型筛选：system/course"),
    status: str | None = Query(default=None, description="状态筛选"),
    keyword: str | None = Query(default=None, description="关键字搜索"),
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=10, ge=1, le=50, description="每页数量"),
) -> ApiResponse[PageData[FeedbackResponse]]:
    """获取反馈列表接口"""
    can_view_all = await has_feedback_admin_permission(db, current_user.role)
    can_view_course_feedback = current_user.role == "teacher"

    feedbacks, total = await feedback_service.get_list(
        db,
        user_id=None if can_view_all or can_view_course_feedback else current_user.id,
        teacher_id=current_user.id if can_view_course_feedback and not can_view_all else None,
        feedback_type=feedback_type,
        status=status,
        keyword=keyword if can_view_all or can_view_course_feedback else None,
        page=page,
        page_size=page_size,
    )

    return ApiResponse.success(
        data=PageData.create(
            items=[FeedbackResponse.model_validate(feedback) for feedback in feedbacks],
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
    current_user: CurrentUser,
) -> ApiResponse[FeedbackResponse]:
    """获取反馈详情接口"""
    feedback = await feedback_service.get_by_id(db, feedback_id)
    if not feedback:
        raise NotFoundException("反馈不存在")

    can_view_all = await has_feedback_admin_permission(db, current_user.role)
    can_view_course_feedback = (
        current_user.role == "teacher"
        and feedback["target_user_id"] == current_user.id
    )
    if not can_view_all and not can_view_course_feedback and feedback["user_id"] != current_user.id:
        raise ForbiddenException("无权查看该反馈")

    return ApiResponse.success(data=FeedbackResponse.model_validate(feedback))


@router.post(
    "/{feedback_id}/process",
    response_model=ApiResponse[FeedbackResponse],
    summary="标记已处理",
    description="处理反馈（管理员）",
)
async def process_feedback(
    feedback_id: int,
    db: DBSession,
    current_user: CurrentUser,
    data: FeedbackProcess | None = None,
) -> ApiResponse[FeedbackResponse]:
    """处理反馈接口（管理员）"""
    can_process_all = await has_feedback_admin_permission(db, current_user.role)
    if not can_process_all and current_user.role != "teacher":
        raise ForbiddenException("无权处理反馈")

    feedback = await feedback_service.process(
        db,
        feedback_id,
        data,
        current_user.id,
        allow_global=can_process_all,
    )
    detail = await feedback_service.get_by_id(db, feedback.id)
    return ApiResponse.success(
        data=FeedbackResponse.model_validate(detail),
        message="处理成功",
    )


@router.post(
    "/batch-process",
    response_model=ApiResponse[dict],
    summary="批量标记已处理",
    description="批量处理反馈（管理员）",
)
async def batch_process_feedbacks(
    data: FeedbackBatchProcess,
    db: DBSession,
    current_user: CurrentUser,
) -> ApiResponse[dict]:
    """批量处理反馈接口（管理员）。"""
    await permission_service.ensure_permission(
        db,
        current_user.role,
        "admin.feedback",
        "无权处理反馈",
    )

    count = 0
    for feedback_id in data.feedback_ids:
        await feedback_service.process(db, feedback_id, None, current_user.id, allow_global=True)
        count += 1

    return ApiResponse.success(
        data={"count": count},
        message="批量处理成功",
    )
