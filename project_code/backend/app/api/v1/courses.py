"""课程管理 API 路由

提供课程管理相关的 API 接口。
"""

from pathlib import Path

from fastapi import APIRouter, Query, Request
from sqlalchemy import select

from app.core.dependencies import CurrentUser, CurrentUserId, DBSession
from app.core.exceptions import NotFoundException, ValidationException
from app.models.course import CourseTag
from app.models.user import User
from app.schemas.common import ApiResponse, PageData
from app.schemas.course import (
    BatchCourseActionRequest,
    BatchCourseActionResponse,
    CourseCreate,
    CourseListResponse,
    CourseManageScope,
    CourseResponse,
    CourseSearchParams,
    CourseStatisticsAuthorizationCandidateResponse,
    CourseStatisticsAuthorizationGrantRequest,
    CourseStatisticsAuthorizationResponse,
    CourseUpdate,
    MaterialCreate,
    MaterialResponse,
)
from app.services.course_service import course_service, material_service
from app.services.course_statistics_authorization_service import course_statistics_authorization_service
from app.services.upload_service import upload_service

router = APIRouter(prefix="/courses", tags=["课程管理"])


def build_course_list_item(course) -> CourseListResponse:
    return CourseListResponse(
        id=course.id,
        title=course.title,
        subtitle=course.subtitle,
        cover_url=course.cover_url,
        teacher_id=course.teacher_id,
        teacher_name=None,
        price=course.price,
        original_price=course.original_price,
        level=course.level,
        status=course.status,
        is_free=course.is_free,
        total_duration=course.total_duration,
        total_sections=course.total_sections,
        student_count=course.student_count,
        rating=course.rating,
        rating_count=course.rating_count,
        author=course.author,
        view_count=0,
        created_at=course.created_at,
        published_at=course.published_at,
    )


@router.get(
    "",
    response_model=ApiResponse[PageData[CourseListResponse]],
    summary="课程列表",
    description="获取已发布的课程列表",
)
async def get_courses(
    db: DBSession,
    category_id: int | None = Query(default=None, description="分类ID"),
    is_free: bool | None = Query(default=None, description="是否免费"),
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=10, ge=1, le=50, description="每页数量"),
) -> ApiResponse[PageData[CourseListResponse]]:
    """获取课程列表接口"""
    courses, total = await course_service.get_list(
        db,
        status="published",
        category_id=category_id,
        is_free=is_free,
        page=page,
        page_size=page_size,
    )
    items = [build_course_list_item(course) for course in courses]
    return ApiResponse.success(
        data=PageData.create(items=items, total=total, page=page, page_size=page_size),
    )


@router.get(
    "/search",
    response_model=ApiResponse[PageData[CourseListResponse]],
    summary="课程搜索",
    description="根据条件搜索课程",
)
async def search_courses(
    db: DBSession,
    keyword: str | None = Query(default=None, description="搜索关键词"),
    category_id: int | None = Query(default=None, description="分类ID"),
    level: str | None = Query(default=None, description="难度等级"),
    is_free: bool | None = Query(default=None, description="是否免费"),
    min_price: float | None = Query(default=None, description="最低价格"),
    max_price: float | None = Query(default=None, description="最高价格"),
    sort_by: str = Query(default="published_at", description="排序字段"),
    sort_order: str = Query(default="desc", description="排序方向"),
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=10, ge=1, le=50, description="每页数量"),
) -> ApiResponse[PageData[CourseListResponse]]:
    """课程搜索接口"""
    courses, total = await course_service.search(
        db,
        keyword=keyword,
        category_id=category_id,
        level=level,
        is_free=is_free,
        min_price=min_price,
        max_price=max_price,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        page_size=page_size,
    )
    items = [build_course_list_item(course) for course in courses]
    return ApiResponse.success(
        data=PageData.create(items=items, total=total, page=page, page_size=page_size),
    )


@router.get(
    "/homepage",
    response_model=ApiResponse[list[CourseListResponse]],
    summary="首页课程",
    description="获取首页推荐的课程",
)
async def get_homepage_courses(
    db: DBSession,
    limit: int = Query(default=8, ge=1, le=20, description="返回数量"),
) -> ApiResponse[list[CourseListResponse]]:
    """获取首页课程接口"""
    courses = await course_service.get_homepage_courses(db, limit)
    items = [build_course_list_item(course) for course in courses]
    return ApiResponse.success(data=items)


@router.get(
    "/my-courses",
    response_model=ApiResponse[PageData[CourseListResponse]],
    summary="我的课程",
    description="获取当前用户创建的课程列表",
)
async def get_my_courses(
    db: DBSession,
    user_id: CurrentUserId,
    status: str | None = Query(default=None, description="状态筛选"),
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=10, ge=1, le=50, description="每页数量"),
) -> ApiResponse[PageData[CourseListResponse]]:
    """获取我的课程接口"""
    courses, total = await course_service.get_my_courses(
        db,
        teacher_id=user_id,
        status=status,
        page=page,
        page_size=page_size,
    )
    items = [build_course_list_item(course) for course in courses]
    return ApiResponse.success(
        data=PageData.create(items=items, total=total, page=page, page_size=page_size),
    )


@router.get(
    "/manage",
    response_model=ApiResponse[PageData[CourseListResponse]],
    summary="课程管理列表",
    description="按角色获取课程管理列表",
)
async def get_manage_courses(
    db: DBSession,
    current_user: CurrentUser,
    scope: str = Query(default=CourseManageScope.MINE, description="范围"),
    status: str | None = Query(default=None, description="状态筛选"),
    keyword: str | None = Query(default=None, description="关键词"),
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=10, ge=1, le=50, description="每页数量"),
) -> ApiResponse[PageData[CourseListResponse]]:
    """获取课程管理列表。"""
    courses, total = await course_service.get_manage_courses(
        db,
        current_user=current_user,
        scope=scope,
        status=status,
        keyword=keyword,
        page=page,
        page_size=page_size,
    )
    items = [build_course_list_item(course) for course in courses]
    return ApiResponse.success(
        data=PageData.create(items=items, total=total, page=page, page_size=page_size),
    )


@router.get(
    "/{course_id}",
    response_model=ApiResponse[CourseResponse],
    summary="课程详情",
    description="获取指定课程的详细信息",
)
async def get_course(course_id: int, db: DBSession) -> ApiResponse[CourseResponse]:
    """获取课程详情接口"""
    course = await course_service.get_by_id(db, course_id)
    if not course:
        raise NotFoundException("课程不存在")

    result = await db.execute(select(CourseTag).where(CourseTag.course_id == course_id))
    tags = result.scalars().all()
    chapters = await course_service.get_chapters_with_sections(db, course_id)
    materials = await material_service.get_by_course(db, course_id)
    total_sections = sum(chapter.section_count for chapter in chapters)
    total_duration = sum(chapter.total_duration for chapter in chapters)

    teacher_name_result = await db.execute(select(User.nickname).where(User.id == course.teacher_id))
    teacher_nickname = teacher_name_result.scalar()

    course_dict = {
        "id": course.id,
        "title": course.title,
        "subtitle": course.subtitle,
        "summary": course.summary,
        "description": course.description,
        "cover_url": course.cover_url,
        "teacher_id": course.teacher_id,
        "teacher_name": teacher_nickname,
        "category_id": course.category_id,
        "category_name": None,
        "price": course.price,
        "original_price": course.original_price,
        "level": course.level,
        "status": course.status,
        "is_free": course.is_free,
        "total_duration": total_duration,
        "total_sections": total_sections,
        "student_count": course.student_count,
        "rating": course.rating,
        "rating_count": course.rating_count,
        "author": course.author,
        "tags": [{"id": t.tag_id} for t in tags],
        "chapters": chapters,
        "materials": [MaterialResponse.model_validate(material) for material in materials],
        "created_at": course.created_at,
        "published_at": course.published_at,
    }
    return ApiResponse.success(data=CourseResponse(**course_dict))


@router.post(
    "",
    response_model=ApiResponse[CourseResponse],
    summary="创建课程",
    description="创建新课程",
)
async def create_course(data: CourseCreate, db: DBSession, user_id: CurrentUserId) -> ApiResponse[CourseResponse]:
    """创建课程接口"""
    course = await course_service.create(db, user_id, data)
    return ApiResponse.success(data=CourseResponse.model_validate(course), message="创建成功")


@router.post(
    "/batch-action",
    response_model=ApiResponse[BatchCourseActionResponse],
    summary="批量课程操作",
    description="批量上架、下架、删除课程",
)
async def batch_course_action(
    data: BatchCourseActionRequest,
    db: DBSession,
    current_user: CurrentUser,
) -> ApiResponse[BatchCourseActionResponse]:
    """批量课程操作接口。"""
    result = await course_service.batch_action(
        db,
        current_user=current_user,
        action=data.action,
        course_ids=data.course_ids,
    )
    return ApiResponse.success(data=result, message=result.message or "批量操作完成")


@router.post(
    "/{course_id}",
    response_model=ApiResponse[CourseResponse],
    summary="更新课程",
    description="更新指定课程的信息",
)
async def update_course(
    course_id: int,
    data: CourseUpdate,
    db: DBSession,
    current_user: CurrentUser,
) -> ApiResponse[CourseResponse]:
    """更新课程接口"""
    course = await course_service.update(db, course_id, current_user, data)
    return ApiResponse.success(data=CourseResponse.model_validate(course), message="更新成功")


@router.post(
    "/{course_id}/publish",
    response_model=ApiResponse[CourseResponse],
    summary="发布课程",
    description="发布指定课程",
)
async def publish_course(
    course_id: int,
    db: DBSession,
    current_user: CurrentUser,
) -> ApiResponse[CourseResponse]:
    """发布课程接口"""
    course = await course_service.publish(db, course_id, current_user)
    return ApiResponse.success(data=CourseResponse.model_validate(course), message="发布成功")


@router.post(
    "/{course_id}/archive",
    response_model=ApiResponse[CourseResponse],
    summary="下架课程",
    description="下架指定课程",
)
async def archive_course(
    course_id: int,
    db: DBSession,
    current_user: CurrentUser,
) -> ApiResponse[CourseResponse]:
    """下架课程接口"""
    course = await course_service.archive(db, course_id, current_user)
    return ApiResponse.success(data=CourseResponse.model_validate(course), message="下架成功")


@router.delete(
    "/{course_id}",
    response_model=ApiResponse[None],
    summary="删除课程",
    description="删除指定课程（仅草稿状态可删除）",
)
async def delete_course(
    course_id: int,
    db: DBSession,
    current_user: CurrentUser,
) -> ApiResponse[None]:
    """删除课程接口"""
    await course_service.delete(db, course_id, current_user)
    return ApiResponse.success(message="删除成功")


@router.post(
    "/{course_id}/materials",
    response_model=ApiResponse[MaterialResponse],
    summary="上传配套资料",
    description="为课程上传配套资料",
)
async def create_material(
    course_id: int,
    request: Request,
    db: DBSession,
    user_id: CurrentUserId,
) -> ApiResponse[MaterialResponse]:
    """上传配套资料接口"""
    content_type = request.headers.get("content-type", "").lower()

    if content_type.startswith("multipart/form-data"):
        form = await request.form()
        upload_file = form.get("file")
        if upload_file is None or not hasattr(upload_file, "filename"):
            raise ValidationException("请上传资料文件")

        upload_result = await upload_service.save_file(file=upload_file, base_url=str(request.base_url))
        file_name = str(upload_result["file_name"])
        data = MaterialCreate(
            name=file_name,
            file_url=str(upload_result["file_url"]),
            file_size=int(upload_result["file_size"]),
            file_type=Path(file_name).suffix.lower().lstrip(".") or None,
        )
    else:
        payload = await request.json()
        data = MaterialCreate.model_validate(payload)

    material = await material_service.create(db, course_id, user_id, data)
    return ApiResponse.success(data=MaterialResponse.model_validate(material), message="上传成功")


@router.delete(
    "/{course_id}/materials/{material_id}",
    response_model=ApiResponse[None],
    summary="删除配套资料",
    description="删除指定配套资料",
)
async def delete_material(
    course_id: int,
    material_id: int,
    db: DBSession,
    user_id: CurrentUserId,
) -> ApiResponse[None]:
    """删除配套资料接口"""
    await material_service.delete(db, material_id, user_id)
    return ApiResponse.success(message="删除成功")


@router.post(
    "/{course_id}/materials/{material_id}/delete",
    response_model=ApiResponse[None],
    summary="删除配套资料（兼容旧前端）",
    description="兼容旧版前端仍使用的 POST 删除路径，建议优先使用 DELETE 接口",
    include_in_schema=False,
)
async def delete_material_legacy(
    course_id: int,
    material_id: int,
    db: DBSession,
    user_id: CurrentUserId,
) -> ApiResponse[None]:
    """兼容旧前端的资料删除接口。"""
    await material_service.delete(db, material_id, user_id)
    return ApiResponse.success(message="删除成功")


@router.get(
    "/{course_id}/statistics-authorizations",
    response_model=ApiResponse[list[CourseStatisticsAuthorizationResponse]],
    summary="课程统计授权列表",
    description="获取课程统计授权列表",
)
async def get_course_statistics_authorizations(
    course_id: int,
    db: DBSession,
    current_user: CurrentUser,
) -> ApiResponse[list[CourseStatisticsAuthorizationResponse]]:
    """获取课程统计授权列表。"""
    rows = await course_statistics_authorization_service.list_authorizations(db, course_id, current_user)
    return ApiResponse.success(
        data=[CourseStatisticsAuthorizationResponse(**row) for row in rows],
        message="获取成功",
    )


@router.get(
    "/{course_id}/statistics-authorizations/candidates",
    response_model=ApiResponse[list[CourseStatisticsAuthorizationCandidateResponse]],
    summary="课程统计授权候选老师",
    description="获取可授权老师列表",
)
async def get_course_statistics_authorization_candidates(
    course_id: int,
    db: DBSession,
    current_user: CurrentUser,
    keyword: str | None = Query(default=None, description="搜索关键词"),
) -> ApiResponse[list[CourseStatisticsAuthorizationCandidateResponse]]:
    """获取课程统计授权候选老师。"""
    rows = await course_statistics_authorization_service.list_candidates(db, course_id, current_user, keyword=keyword)
    return ApiResponse.success(
        data=[CourseStatisticsAuthorizationCandidateResponse(**row) for row in rows],
        message="获取成功",
    )


@router.post(
    "/{course_id}/statistics-authorizations",
    response_model=ApiResponse[list[CourseStatisticsAuthorizationResponse]],
    summary="授予课程统计授权",
    description="为课程批量授予统计查看权限",
)
async def grant_course_statistics_authorizations(
    course_id: int,
    data: CourseStatisticsAuthorizationGrantRequest,
    db: DBSession,
    current_user: CurrentUser,
) -> ApiResponse[list[CourseStatisticsAuthorizationResponse]]:
    """授予课程统计授权。"""
    rows = await course_statistics_authorization_service.grant_authorizations(db, course_id, data.teacher_ids, current_user)
    return ApiResponse.success(
        data=[CourseStatisticsAuthorizationResponse(**row) for row in rows],
        message="授权成功",
    )


@router.delete(
    "/{course_id}/statistics-authorizations/{teacher_id}",
    response_model=ApiResponse[None],
    summary="撤销课程统计授权",
    description="撤销指定老师的课程统计查看权限",
)
async def revoke_course_statistics_authorization(
    course_id: int,
    teacher_id: int,
    db: DBSession,
    current_user: CurrentUser,
) -> ApiResponse[None]:
    """撤销课程统计授权。"""
    await course_statistics_authorization_service.revoke_authorization(db, course_id, teacher_id, current_user)
    return ApiResponse.success(message="撤销成功")
