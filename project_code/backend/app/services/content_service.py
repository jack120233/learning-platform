"""课程内容服务模块

提供章节、小节、资源管理的业务逻辑。
"""

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.resource_types import normalize_resource_type
from app.core.exceptions import (
    ForbiddenException,
    NotFoundException,
    ValidationException,
)
from app.models.course import Course
from app.models.content import Chapter, Section, Resource
from app.schemas.content import (
    ChapterCreate,
    ChapterUpdate,
    ResourceCreate,
    SectionCreate,
    SectionUpdate,
)


PUBLISHED_COURSE_EDIT_MESSAGE = "已发布课程不能直接编辑，请先下架"


async def _ensure_course_editable(
    db: AsyncSession,
    course_id: int,
    user_id: int,
) -> Course:
    """加载课程并确认当前用户可编辑且课程未发布。"""
    course = await db.get(Course, course_id)
    if not course:
        raise NotFoundException("课程不存在")
    if course.teacher_id != user_id:
        raise ForbiddenException("无权修改此课程")
    if course.status == "published":
        raise ValidationException(PUBLISHED_COURSE_EDIT_MESSAGE)
    return course


def _ensure_chapter_belongs_to_course(chapter: Chapter | None, course_id: int) -> Chapter:
    """确认章节存在且属于指定课程。"""
    if not chapter or chapter.course_id != course_id:
        raise NotFoundException("章节不存在")
    return chapter


def _ensure_section_belongs_to_course(
    section: Section | None,
    course_id: int,
    chapter_id: int | None = None,
) -> Section:
    """确认小节存在且属于指定课程/章节。"""
    if not section or section.course_id != course_id:
        raise NotFoundException("小节不存在")
    if chapter_id is not None and section.chapter_id != chapter_id:
        raise NotFoundException("小节不存在")
    return section


def _ensure_resource_belongs_to_path(
    resource: Resource | None,
    course_id: int,
    chapter_id: int | None = None,
    section_id: int | None = None,
) -> Resource:
    """确认资源存在且属于指定课程/章节/小节路径。"""
    if not resource or resource.course_id != course_id:
        raise NotFoundException("资源不存在")
    if section_id is not None and resource.section_id != section_id:
        raise NotFoundException("资源不存在")
    if chapter_id is not None:
        if resource.chapter_id != chapter_id:
            raise NotFoundException("资源不存在")
        if section_id is None and resource.section_id is not None:
            raise NotFoundException("资源不存在")
    return resource


async def _delete_resource_record(
    db: AsyncSession,
    resource: Resource,
    *,
    update_section: bool = True,
) -> None:
    """删除资源记录并同步聚合字段。"""
    if update_section and resource.section_id:
        section = await db.get(Section, resource.section_id)
        if section:
            section.resource_count = max(0, section.resource_count - 1)
            if resource.type == "video":
                section.duration = max(0, section.duration - resource.duration)

    chapter = await db.get(Chapter, resource.chapter_id)
    if chapter and resource.type == "video":
        chapter.total_duration = max(0, chapter.total_duration - resource.duration)

    course = await db.get(Course, resource.course_id)
    if course and resource.type == "video":
        course.total_duration = max(0, course.total_duration - resource.duration)

    await db.delete(resource)


class ChapterService:
    """章节服务类"""

    async def get_list(
        self,
        db: AsyncSession,
        course_id: int,
    ) -> list[Chapter]:
        """获取课程章节列表"""
        result = await db.execute(
            select(Chapter)
            .where(Chapter.course_id == course_id)
            .order_by(Chapter.sort_order, Chapter.id)
        )
        return list(result.scalars().all())

    async def get_by_id(
        self,
        db: AsyncSession,
        chapter_id: int,
    ) -> Chapter | None:
        """通过ID获取章节"""
        return await db.get(Chapter, chapter_id)

    async def create(
        self,
        db: AsyncSession,
        course_id: int,
        user_id: int,
        data: ChapterCreate,
    ) -> Chapter:
        """创建章节"""
        await _ensure_course_editable(db, course_id, user_id)
        chapter = Chapter(
            course_id=course_id,
            title=data.title,
            description=data.description,
            sort_order=data.sort_order,
            is_free=data.is_free,
        )
        db.add(chapter)
        await db.flush()
        return chapter

    async def update(
        self,
        db: AsyncSession,
        course_id: int,
        chapter_id: int,
        user_id: int,
        data: ChapterUpdate,
    ) -> Chapter:
        """更新章节"""
        await _ensure_course_editable(db, course_id, user_id)
        chapter = _ensure_chapter_belongs_to_course(
            await self.get_by_id(db, chapter_id),
            course_id,
        )

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(chapter, key, value)

        await db.flush()
        return chapter

    async def sort(
        self,
        db: AsyncSession,
        course_id: int,
        user_id: int,
        chapter_ids: list[int],
    ) -> None:
        """批量排序章节。"""
        await _ensure_course_editable(db, course_id, user_id)
        if not chapter_ids:
            raise ValidationException("chapter_ids 不能为空")

        if len(set(chapter_ids)) != len(chapter_ids):
            raise ValidationException("chapter_ids 不能包含重复ID")

        chapters = await self.get_list(db, course_id)
        if not chapters:
            raise ValidationException("该课程下没有可排序的章节")

        chapter_map = {chapter.id: chapter for chapter in chapters}
        current_ids = set(chapter_map.keys())
        provided_ids = set(chapter_ids)

        if provided_ids != current_ids:
            raise ValidationException("chapter_ids 必须包含该课程全部章节ID")

        for index, chapter_id in enumerate(chapter_ids, start=1):
            chapter_map[chapter_id].sort_order = index

        await db.flush()

    async def delete(
        self,
        db: AsyncSession,
        course_id: int,
        chapter_id: int,
        user_id: int,
    ) -> None:
        """删除章节"""
        await _ensure_course_editable(db, course_id, user_id)
        chapter = _ensure_chapter_belongs_to_course(
            await self.get_by_id(db, chapter_id),
            course_id,
        )

        sections = await db.execute(
            select(func.count()).where(Section.chapter_id == chapter_id)
        )
        if sections.scalar() > 0:
            raise ValidationException("存在小节，无法删除")

        await db.delete(chapter)


class SectionService:
    """小节服务类"""

    async def get_list(
        self,
        db: AsyncSession,
        chapter_id: int,
    ) -> list[Section]:
        """获取章节小节列表"""
        result = await db.execute(
            select(Section)
            .where(Section.chapter_id == chapter_id)
            .order_by(Section.sort_order, Section.id)
        )
        return list(result.scalars().all())

    async def get_by_id(
        self,
        db: AsyncSession,
        section_id: int,
    ) -> Section | None:
        """通过ID获取小节"""
        return await db.get(Section, section_id)

    async def create(
        self,
        db: AsyncSession,
        course_id: int,
        chapter_id: int,
        user_id: int,
        data: SectionCreate,
    ) -> Section:
        """创建小节"""
        course = await _ensure_course_editable(db, course_id, user_id)
        chapter = _ensure_chapter_belongs_to_course(
            await db.get(Chapter, chapter_id),
            course_id,
        )

        section = Section(
            course_id=course_id,
            chapter_id=chapter_id,
            title=data.title,
            description=data.description,
            sort_order=data.sort_order,
            is_free=data.is_free,
        )
        db.add(section)

        chapter.section_count += 1
        course.total_sections += 1

        await db.flush()
        return section

    async def update(
        self,
        db: AsyncSession,
        course_id: int,
        chapter_id: int,
        section_id: int,
        user_id: int,
        data: SectionUpdate,
    ) -> Section:
        """更新小节"""
        await _ensure_course_editable(db, course_id, user_id)
        section = _ensure_section_belongs_to_course(
            await self.get_by_id(db, section_id),
            course_id,
            chapter_id,
        )

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(section, key, value)

        await db.flush()
        return section

    async def sort(
        self,
        db: AsyncSession,
        course_id: int,
        chapter_id: int,
        user_id: int,
        section_ids: list[int],
    ) -> None:
        """批量排序小节。"""
        await _ensure_course_editable(db, course_id, user_id)
        _ensure_chapter_belongs_to_course(await db.get(Chapter, chapter_id), course_id)

        if not section_ids:
            raise ValidationException("section_ids 不能为空")

        if len(set(section_ids)) != len(section_ids):
            raise ValidationException("section_ids 不能包含重复ID")

        sections = await self.get_list(db, chapter_id)
        if not sections:
            raise ValidationException("该章节下没有可排序的小节")

        section_map = {section.id: section for section in sections}
        current_ids = set(section_map.keys())
        provided_ids = set(section_ids)

        if provided_ids != current_ids:
            raise ValidationException("section_ids 必须包含该章节全部小节ID")

        for index, section_id in enumerate(section_ids, start=1):
            section_map[section_id].sort_order = index

        await db.flush()

    async def delete(
        self,
        db: AsyncSession,
        course_id: int,
        chapter_id: int,
        section_id: int,
        user_id: int,
    ) -> None:
        """删除小节"""
        await _ensure_course_editable(db, course_id, user_id)
        section = _ensure_section_belongs_to_course(
            await self.get_by_id(db, section_id),
            course_id,
            chapter_id,
        )

        resources_result = await db.execute(
            select(Resource).where(Resource.section_id == section_id)
        )
        for resource in resources_result.scalars().all():
            await _delete_resource_record(db, resource, update_section=False)

        chapter = await db.get(Chapter, section.chapter_id)
        if chapter:
            chapter.section_count = max(0, chapter.section_count - 1)

        course = await db.get(Course, section.course_id)
        if course:
            course.total_sections = max(0, course.total_sections - 1)

        await db.delete(section)


class ResourceService:
    """资源服务类"""

    async def get_list(
        self,
        db: AsyncSession,
        section_id: int,
    ) -> list[Resource]:
        """获取小节资源列表"""
        result = await db.execute(
            select(Resource)
            .where(Resource.section_id == section_id)
            .order_by(Resource.sort_order, Resource.id)
        )
        return list(result.scalars().all())

    async def get_list_by_chapter(
        self,
        db: AsyncSession,
        chapter_id: int,
    ) -> list[Resource]:
        """获取章节级资源列表。"""
        result = await db.execute(
            select(Resource)
            .where(
                Resource.chapter_id == chapter_id,
                Resource.section_id.is_(None),
            )
            .order_by(Resource.sort_order, Resource.id)
        )
        return list(result.scalars().all())

    async def get_by_id(
        self,
        db: AsyncSession,
        resource_id: int,
    ) -> Resource | None:
        """通过ID获取资源"""
        return await db.get(Resource, resource_id)

    async def create(
        self,
        db: AsyncSession,
        course_id: int,
        chapter_id: int,
        section_id: int,
        user_id: int,
        data: ResourceCreate,
    ) -> Resource:
        """兼容旧调用，创建小节资源。"""
        return await self.create_for_section(db, course_id, chapter_id, section_id, user_id, data)

    async def create_for_section(
        self,
        db: AsyncSession,
        course_id: int,
        chapter_id: int,
        section_id: int,
        user_id: int,
        data: ResourceCreate,
    ) -> Resource:
        """创建小节资源。"""
        await _ensure_course_editable(db, course_id, user_id)
        _ensure_chapter_belongs_to_course(await db.get(Chapter, chapter_id), course_id)
        section = _ensure_section_belongs_to_course(
            await db.get(Section, section_id),
            course_id,
            chapter_id,
        )

        resource_type = normalize_resource_type(
            data.type,
            file_url=data.file_url,
            file_name=data.title or data.file_name,
        )

        resource = Resource(
            course_id=course_id,
            chapter_id=chapter_id,
            section_id=section_id,
            title=data.title,
            type=resource_type,
            file_url=data.file_url,
            file_size=data.file_size,
            duration=data.duration,
            sort_order=data.sort_order,
            is_free=data.is_free,
            is_required=data.is_required,
        )
        db.add(resource)

        section.resource_count += 1
        if resource_type == "video":
            section.duration += data.duration

        chapter = await db.get(Chapter, chapter_id)
        if chapter and resource_type == "video":
            chapter.total_duration += data.duration

        course = await db.get(Course, course_id)
        if course and resource_type == "video":
            course.total_duration += data.duration

        await db.flush()
        return resource

    async def create_for_chapter(
        self,
        db: AsyncSession,
        course_id: int,
        chapter_id: int,
        user_id: int,
        data: ResourceCreate,
    ) -> Resource:
        """创建章节级资源。"""
        await _ensure_course_editable(db, course_id, user_id)
        chapter = _ensure_chapter_belongs_to_course(
            await db.get(Chapter, chapter_id),
            course_id,
        )

        resource_type = normalize_resource_type(
            data.type,
            file_url=data.file_url,
            file_name=data.title or data.file_name,
        )

        resource = Resource(
            course_id=course_id,
            chapter_id=chapter_id,
            section_id=None,
            title=data.title,
            type=resource_type,
            file_url=data.file_url,
            file_size=data.file_size,
            duration=data.duration,
            sort_order=data.sort_order,
            is_free=data.is_free,
            is_required=data.is_required,
        )
        db.add(resource)

        if resource_type == "video":
            chapter.total_duration += data.duration
            course = await db.get(Course, course_id)
            if course:
                course.total_duration += data.duration

        await db.flush()
        return resource

    async def delete(
        self,
        db: AsyncSession,
        course_id: int,
        resource_id: int,
        user_id: int,
        chapter_id: int | None = None,
        section_id: int | None = None,
    ) -> None:
        """删除资源"""
        await _ensure_course_editable(db, course_id, user_id)
        resource = _ensure_resource_belongs_to_path(
            await self.get_by_id(db, resource_id),
            course_id,
            chapter_id=chapter_id,
            section_id=section_id,
        )
        await _delete_resource_record(db, resource)


# 创建全局服务实例
chapter_service = ChapterService()
section_service = SectionService()
resource_service = ResourceService()
