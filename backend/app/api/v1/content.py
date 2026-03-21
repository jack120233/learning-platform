"""课程内容 API 路由

提供章节、小节、资源管理的 API 接口。
"""

from fastapi import APIRouter
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import DBSession, CurrentUserId
from app.schemas.common import ApiResponse
from app.schemas.content import (
    ChapterCreate,
    ChapterResponse,
    ChapterUpdate,
    CourseContentResponse,
    ResourceCreate,
    ResourceResponse,
    SectionCreate,
    SectionResponse,
    SectionUpdate,
)
from app.services.content_service import (
    chapter_service,
    section_service,
    resource_service,
)

router = APIRouter(tags=["课程内容"])


# ==================== 章节管理 ====================

@router.get(
    "/courses/{course_id}/chapters",
    response_model=ApiResponse[list[ChapterResponse]],
    summary="章节列表",
    description="获取指定课程的章节列表",
)
async def get_chapters(
    course_id: int,
    db: DBSession,
) -> ApiResponse[list[ChapterResponse]]:
    """获取章节列表接口"""
    chapters = await chapter_service.get_list(db, course_id)
    return ApiResponse.success(
        data=[ChapterResponse.model_validate(c) for c in chapters],
    )


@router.post(
    "/courses/{course_id}/chapters",
    response_model=ApiResponse[ChapterResponse],
    summary="创建章节",
    description="为指定课程创建新章节",
)
async def create_chapter(
    course_id: int,
    data: ChapterCreate,
    db: DBSession,
    user_id: CurrentUserId,
) -> ApiResponse[ChapterResponse]:
    """创建章节接口"""
    # 实际项目中需要验证用户是否有权限操作该课程
    chapter = await chapter_service.create(db, course_id, data)
    return ApiResponse.success(
        data=ChapterResponse.model_validate(chapter),
        message="创建成功",
    )


@router.post(
    "/courses/{course_id}/chapters/{chapter_id}",
    response_model=ApiResponse[ChapterResponse],
    summary="更新章节",
    description="更新指定章节的信息",
)
async def update_chapter(
    course_id: int,
    chapter_id: int,
    data: ChapterUpdate,
    db: DBSession,
    user_id: CurrentUserId,
) -> ApiResponse[ChapterResponse]:
    """更新章节接口"""
    chapter = await chapter_service.update(db, chapter_id, data)
    return ApiResponse.success(
        data=ChapterResponse.model_validate(chapter),
        message="更新成功",
    )


@router.delete(
    "/courses/{course_id}/chapters/{chapter_id}",
    response_model=ApiResponse[None],
    summary="删除章节",
    description="删除指定章节（存在小节时无法删除）",
)
async def delete_chapter(
    course_id: int,
    chapter_id: int,
    db: DBSession,
    user_id: CurrentUserId,
) -> ApiResponse[None]:
    """删除章节接口"""
    await chapter_service.delete(db, chapter_id)
    return ApiResponse.success(message="删除成功")


# ==================== 小节管理 ====================

@router.get(
    "/courses/{course_id}/chapters/{chapter_id}/sections",
    response_model=ApiResponse[list[SectionResponse]],
    summary="小节列表",
    description="获取指定章节的小节列表",
)
async def get_sections(
    course_id: int,
    chapter_id: int,
    db: DBSession,
) -> ApiResponse[list[SectionResponse]]:
    """获取小节列表接口"""
    sections = await section_service.get_list(db, chapter_id)
    return ApiResponse.success(
        data=[SectionResponse.model_validate(s) for s in sections],
    )


@router.post(
    "/courses/{course_id}/chapters/{chapter_id}/sections",
    response_model=ApiResponse[SectionResponse],
    summary="创建小节",
    description="为指定章节创建新小节",
)
async def create_section(
    course_id: int,
    chapter_id: int,
    data: SectionCreate,
    db: DBSession,
    user_id: CurrentUserId,
) -> ApiResponse[SectionResponse]:
    """创建小节接口"""
    section = await section_service.create(db, course_id, chapter_id, data)
    return ApiResponse.success(
        data=SectionResponse.model_validate(section),
        message="创建成功",
    )


@router.post(
    "/courses/{course_id}/chapters/{chapter_id}/sections/{section_id}",
    response_model=ApiResponse[SectionResponse],
    summary="更新小节",
    description="更新指定小节的信息",
)
async def update_section(
    course_id: int,
    chapter_id: int,
    section_id: int,
    data: SectionUpdate,
    db: DBSession,
    user_id: CurrentUserId,
) -> ApiResponse[SectionResponse]:
    """更新小节接口"""
    section = await section_service.update(db, section_id, data)
    return ApiResponse.success(
        data=SectionResponse.model_validate(section),
        message="更新成功",
    )


@router.delete(
    "/courses/{course_id}/chapters/{chapter_id}/sections/{section_id}",
    response_model=ApiResponse[None],
    summary="删除小节",
    description="删除指定小节（存在资源时无法删除）",
)
async def delete_section(
    course_id: int,
    chapter_id: int,
    section_id: int,
    db: DBSession,
    user_id: CurrentUserId,
) -> ApiResponse[None]:
    """删除小节接口"""
    await section_service.delete(db, section_id)
    return ApiResponse.success(message="删除成功")


# ==================== 资源管理 ====================

@router.post(
    "/courses/{course_id}/sections/{section_id}/resources",
    response_model=ApiResponse[ResourceResponse],
    summary="上传资源",
    description="为指定小节上传学习资源",
)
async def create_resource(
    course_id: int,
    section_id: int,
    data: ResourceCreate,
    db: DBSession,
    user_id: CurrentUserId,
) -> ApiResponse[ResourceResponse]:
    """上传资源接口"""
    # 需要获取小节的章节ID
    section = await section_service.get_by_id(db, section_id)
    if not section:
        from app.core.exceptions import NotFoundException
        raise NotFoundException("小节不存在")

    resource = await resource_service.create(
        db, course_id, section.chapter_id, section_id, data
    )
    return ApiResponse.success(
        data=ResourceResponse.model_validate(resource),
        message="上传成功",
    )


@router.delete(
    "/courses/{course_id}/sections/{section_id}/resources/{resource_id}",
    response_model=ApiResponse[None],
    summary="删除资源",
    description="删除指定学习资源",
)
async def delete_resource(
    course_id: int,
    section_id: int,
    resource_id: int,
    db: DBSession,
    user_id: CurrentUserId,
) -> ApiResponse[None]:
    """删除资源接口"""
    await resource_service.delete(db, resource_id)
    return ApiResponse.success(message="删除成功")