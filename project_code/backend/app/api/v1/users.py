"""用户管理 API 路由

提供用户管理相关的 API 接口。
"""

import json

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import CurrentUser, DBSession, CurrentUserId
from app.schemas.common import ApiResponse, PageData
from app.schemas.feedback import FeedbackResponse
from app.schemas.user import (
    AdminApplicationCreate,
    AdminApplicationResponse,
    AdminApplicationReview,
    ChangePasswordRequest,
    LearningRecordDeleteRequest,
    LearningRecordDeleteResponse,
    LearningRecordResponse,
    TeacherAuditApply,
    TeacherAuditResponse,
    TeacherAuditReview,
    TeacherOptionResponse,
    UserProfileUpdate,
    UserResponse,
    UserListResponse,
    UserStatusUpdate,
)
from app.services.user_service import (
    user_service,
    teacher_audit_service,
    admin_application_service,
)
from app.services.feedback_service import feedback_service
from app.services.permission_service import permission_service

router = APIRouter(prefix="/users", tags=["用户管理"])


# ==================== 个人信息相关 ====================

@router.get(
    "/me",
    response_model=ApiResponse[UserResponse],
    summary="获取当前用户信息",
    description="获取当前登录用户的个人信息",
)
async def get_current_user(
    db: DBSession,
    user_id: CurrentUserId,
) -> ApiResponse[UserResponse]:
    """获取当前用户信息接口"""
    user = await user_service.get_current_user(db, user_id)
    return ApiResponse.success(data=UserResponse.model_validate(user))


@router.post(
    "/me",
    response_model=ApiResponse[UserResponse],
    summary="更新个人信息",
    description="更新当前用户的个人信息",
)
async def update_profile(
    data: UserProfileUpdate,
    db: DBSession,
    user_id: CurrentUserId,
) -> ApiResponse[UserResponse]:
    """更新个人信息接口"""
    user = await user_service.update_profile(db, user_id, data)
    return ApiResponse.success(
        data=UserResponse.model_validate(user),
        message="更新成功",
    )


@router.post(
    "/me/change-password",
    response_model=ApiResponse[None],
    summary="修改密码",
    description="修改当前用户的密码",
)
async def change_password(
    data: ChangePasswordRequest,
    db: DBSession,
    user_id: CurrentUserId,
) -> ApiResponse[None]:
    """修改密码接口"""
    await user_service.change_password(
        db,
        user_id,
        data.old_password,
        data.new_password,
    )
    return ApiResponse.success(message="密码修改成功")


@router.get(
    "/me/learning-records",
    response_model=ApiResponse[PageData[LearningRecordResponse]],
    summary="获取学习记录",
    description="获取当前用户的课程学习记录",
)
async def get_learning_records(
    db: DBSession,
    user_id: CurrentUserId,
    time_range: str = Query(default="all", description="时间范围：recent_7/recent_30/all"),
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=10, ge=1, le=50, description="每页数量"),
) -> ApiResponse[PageData[LearningRecordResponse]]:
    """获取学习记录接口"""
    records, total = await user_service.get_learning_records(
        db,
        user_id,
        time_range=time_range,
        page=page,
        page_size=page_size,
    )
    return ApiResponse.success(
        data=PageData.create(
            items=[LearningRecordResponse.model_validate(r) for r in records],
            total=total,
            page=page,
            page_size=page_size,
        ),
    )


@router.post(
    "/me/learning-records/delete",
    response_model=ApiResponse[LearningRecordDeleteResponse],
    summary="删除学习记录",
    description="隐藏当前用户的可见学习记录，不影响进度和统计",
)
async def delete_learning_records(
    data: LearningRecordDeleteRequest,
    db: DBSession,
    user_id: CurrentUserId,
) -> ApiResponse[LearningRecordDeleteResponse]:
    """隐藏学习记录接口。"""
    deleted_count = await user_service.hide_learning_records(db, user_id, data.record_ids)
    return ApiResponse.success(
        data=LearningRecordDeleteResponse(deleted_count=deleted_count),
        message="删除成功",
    )


@router.get(
    "/teachers/options",
    response_model=ApiResponse[list[TeacherOptionResponse]],
    summary="老师选择项",
    description="获取可作为课程反馈对象的老师列表",
)
async def get_teacher_options(
    db: DBSession,
    current_user: CurrentUser,
    keyword: str | None = Query(default=None, description="搜索关键词"),
    page_size: int = Query(default=100, ge=1, le=100, description="返回数量"),
) -> ApiResponse[list[TeacherOptionResponse]]:
    """获取老师选择项接口。"""
    teachers, _ = await user_service.get_user_list(
        db,
        keyword=keyword,
        role="teacher",
        status="active",
        page=1,
        page_size=page_size,
    )
    return ApiResponse.success(
        data=[
            TeacherOptionResponse(
                teacher_id=teacher.id,
                username=teacher.username,
                nickname=teacher.nickname,
                avatar=teacher.avatar,
            )
            for teacher in teachers
        ]
    )


@router.get(
    "/me/feedbacks",
    response_model=ApiResponse[PageData[FeedbackResponse]],
    summary="获取我的反馈",
    description="获取当前用户提交的反馈列表",
)
async def get_my_feedbacks(
    db: DBSession,
    user_id: CurrentUserId,
    status: str | None = Query(default=None, description="状态筛选"),
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=10, ge=1, le=50, description="每页数量"),
) -> ApiResponse[PageData[FeedbackResponse]]:
    """获取当前用户反馈列表接口。"""
    feedbacks, total = await feedback_service.get_list(
        db,
        user_id=user_id,
        status=status,
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


# ==================== 用户管理（管理员） ====================

@router.get(
    "",
    response_model=ApiResponse[PageData[UserListResponse]],
    summary="用户列表",
    description="获取用户列表（管理员权限）",
)
async def get_user_list(
    db: DBSession,
    current_user: CurrentUser,
    keyword: str | None = Query(default=None, description="搜索关键词"),
    role: str | None = Query(default=None, description="角色筛选"),
    status: str | None = Query(default=None, description="状态筛选"),
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=10, ge=1, le=100, description="每页数量"),
) -> ApiResponse[PageData[UserListResponse]]:
    """获取用户列表接口（管理员）"""
    if current_user.role != "teacher":
        await permission_service.ensure_permission(
            db,
            current_user.role,
            "admin.user",
            "无权查看用户列表",
        )
        permission_service.ensure_admin(current_user.role, "仅管理员可查看用户列表")
    users, total = await user_service.get_user_list(
        db,
        keyword=keyword,
        role=role,
        status=status,
        page=page,
        page_size=page_size,
    )
    return ApiResponse.success(
        data=PageData.create(
            items=[UserListResponse.model_validate(u) for u in users],
            total=total,
            page=page,
            page_size=page_size,
        ),
    )


@router.post(
    "/{target_user_id}/username-change-opportunity",
    response_model=ApiResponse[UserResponse],
    summary="开放用户名修改机会",
    description="老师或管理员为用户增加一次用户名修改机会",
)
async def grant_username_change_opportunity(
    target_user_id: int,
    db: DBSession,
    user_id: CurrentUserId,
) -> ApiResponse[UserResponse]:
    """开放用户名修改机会接口。"""
    user = await user_service.grant_username_change_opportunity(db, target_user_id, user_id)
    return ApiResponse.success(data=UserResponse.model_validate(user), message="开放成功")


@router.post(
    "/{target_user_id}/status",
    response_model=ApiResponse[UserResponse],
    summary="禁用/启用用户",
    description="更新用户状态（管理员权限）",
)
async def update_user_status(
    target_user_id: int,
    data: UserStatusUpdate,
    db: DBSession,
    current_user: CurrentUser,
) -> ApiResponse[UserResponse]:
    """更新用户状态接口（管理员）"""
    await permission_service.ensure_permission(
        db,
        current_user.role,
        "admin.user",
        "无权更新用户状态",
    )
    permission_service.ensure_admin(current_user.role, "仅管理员可更新用户状态")
    user = await user_service.update_user_status(db, target_user_id, data, current_user.id)
    return ApiResponse.success(
        data=UserResponse.model_validate(user),
        message="状态更新成功",
    )


@router.post(
    "/{target_user_id}",
    response_model=ApiResponse[None],
    summary="删除用户",
    description="删除指定用户（管理员权限）",
)
async def delete_user(
    target_user_id: int,
    db: DBSession,
    current_user: CurrentUser,
) -> ApiResponse[None]:
    """删除用户接口（管理员）"""
    await permission_service.ensure_permission(
        db,
        current_user.role,
        "admin.user",
        "无权删除用户",
    )
    permission_service.ensure_admin(current_user.role, "仅管理员可删除用户")
    await user_service.delete_user(db, target_user_id, current_user.id)
    return ApiResponse.success(message="删除成功")


# ==================== 讲师审核 ====================

@router.get(
    "/teacher-audits",
    response_model=ApiResponse[PageData[TeacherAuditResponse]],
    summary="讲师审核列表",
    description="获取讲师申请审核列表（管理员权限）",
)
async def get_teacher_audits(
    db: DBSession,
    current_user: CurrentUser,
    status: str | None = Query(default=None, description="状态筛选"),
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=10, ge=1, le=50, description="每页数量"),
) -> ApiResponse[PageData[TeacherAuditResponse]]:
    """获取讲师审核列表接口"""
    await permission_service.ensure_permission(
        db,
        current_user.role,
        "admin.teacher_audit",
        "无权查看讲师审核列表",
    )
    permission_service.ensure_admin(current_user.role, "仅管理员可查看讲师审核列表")
    audits, total = await teacher_audit_service.get_list(
        db,
        status=status,
        page=page,
        page_size=page_size,
    )

    # 转换并添加用户名
    items = []
    for audit in audits:
        audit_dict = {
            "id": audit.id,
            "user_id": audit.user_id,
            "real_name": audit.real_name,
            "phone": audit.phone,
            "email": audit.email,
            "organization": audit.organization,
            "title": audit.title,
            "introduction": audit.introduction,
            "certificate_urls": json.loads(audit.certificate_urls) if audit.certificate_urls else None,
            "status": audit.status,
            "review_comment": audit.review_comment,
            "created_at": audit.created_at,
            "reviewed_at": audit.reviewed_at,
        }
        # 获取用户名
        user = await db.get(User, audit.user_id) if hasattr(db, 'get') else None
        if user:
            from app.models.user import User
            result = await db.execute(
                __import__('sqlalchemy', fromlist=['select']).select(User.username).where(User.id == audit.user_id)
            )
            username = result.scalar_one_or_none()
            audit_dict["username"] = username
        items.append(TeacherAuditResponse(**audit_dict))

    return ApiResponse.success(
        data=PageData.create(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
        ),
    )


@router.post(
    "/teacher-audits/{audit_id}/review",
    response_model=ApiResponse[TeacherAuditResponse],
    summary="审核讲师",
    description="审核讲师申请（管理员权限）",
)
async def review_teacher_audit(
    audit_id: int,
    data: TeacherAuditReview,
    db: DBSession,
    current_user: CurrentUser,
) -> ApiResponse[TeacherAuditResponse]:
    """审核讲师申请接口"""
    await permission_service.ensure_permission(
        db,
        current_user.role,
        "admin.teacher_audit",
        "无权审核讲师申请",
    )
    permission_service.ensure_admin(current_user.role, "仅管理员可审核讲师申请")
    audit = await teacher_audit_service.review(db, audit_id, data, current_user.id)
    return ApiResponse.success(
        data=TeacherAuditResponse.model_validate(audit),
        message="审核完成",
    )


# ==================== 管理员申请 ====================

@router.get(
    "/admin-applications",
    response_model=ApiResponse[PageData[AdminApplicationResponse]],
    summary="管理员申请列表",
    description="获取管理员申请列表（管理员权限）",
)
async def get_admin_applications(
    db: DBSession,
    current_user: CurrentUser,
    status: str | None = Query(default=None, description="状态筛选"),
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=10, ge=1, le=50, description="每页数量"),
) -> ApiResponse[PageData[AdminApplicationResponse]]:
    """获取管理员申请列表接口"""
    await permission_service.ensure_permission(
        db,
        current_user.role,
        "admin.admin_application",
        "无权查看管理员申请列表",
    )
    permission_service.ensure_admin(current_user.role, "仅管理员可查看管理员申请列表")
    applications, total = await admin_application_service.get_list(
        db,
        status=status,
        page=page,
        page_size=page_size,
    )

    # 转换并添加用户名
    items = []
    for app in applications:
        app_dict = {
            "id": app.id,
            "user_id": app.user_id,
            "reason": app.reason,
            "department": app.department,
            "status": app.status,
            "review_comment": app.review_comment,
            "created_at": app.created_at,
            "reviewed_at": app.reviewed_at,
        }
        items.append(AdminApplicationResponse(**app_dict))

    return ApiResponse.success(
        data=PageData.create(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
        ),
    )


@router.post(
    "/admin-applications/{application_id}/review",
    response_model=ApiResponse[AdminApplicationResponse],
    summary="审核管理员申请",
    description="审核管理员申请（管理员权限）",
)
async def review_admin_application(
    application_id: int,
    data: AdminApplicationReview,
    db: DBSession,
    current_user: CurrentUser,
) -> ApiResponse[AdminApplicationResponse]:
    """审核管理员申请接口"""
    await permission_service.ensure_permission(
        db,
        current_user.role,
        "admin.admin_application",
        "无权审核管理员申请",
    )
    permission_service.ensure_admin(current_user.role, "仅管理员可审核管理员申请")
    application = await admin_application_service.review(db, application_id, data, current_user.id)
    return ApiResponse.success(
        data=AdminApplicationResponse.model_validate(application),
        message="审核完成",
    )


# 导入 User 模型用于查询
from app.models.user import User
