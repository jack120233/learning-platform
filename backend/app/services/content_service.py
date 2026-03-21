"""课程内容服务模块

提供章节、小节、资源管理的业务逻辑。
"""

from typing import Literal

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    ForbiddenException,
    NotFoundException,
    ValidationException,
)
from app.models.content import Chapter, Section, Resource
from app.schemas.content import (
    ChapterCreate,
    ChapterUpdate,
    ResourceCreate,
    SectionCreate,
    SectionUpdate,
)


class ChapterService:
    """章节服务类"""

    async def get_list(
        self,
        db: AsyncSession,
        course_id: int,
    ) -> list[Chapter]:
        """获取课程章节列表

        Args:
            db: 数据库会话
            course_id: 课程ID

        Returns:
            章节列表
        """
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
        data: ChapterCreate,
    ) -> Chapter:
        """创建章节

        Args:
            db: 数据库会话
            course_id: 课程ID
            data: 创建数据

        Returns:
            创建的章节
        """
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
        chapter_id: int,
        data: ChapterUpdate,
    ) -> Chapter:
        """更新章节

        Args:
            db: 数据库会话
            chapter_id: 章节ID
            data: 更新数据

        Returns:
            更新后的章节

        Raises:
            NotFoundException: 章节不存在
        """
        chapter = await self.get_by_id(db, chapter_id)
        if not chapter:
            raise NotFoundException("章节不存在")

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(chapter, key, value)

        await db.flush()
        return chapter

    async def delete(
        self,
        db: AsyncSession,
        chapter_id: int,
    ) -> None:
        """删除章节

        Args:
            db: 数据库会话
            chapter_id: 章节ID

        Raises:
            NotFoundException: 章节不存在
            ValidationException: 存在小节
        """
        chapter = await self.get_by_id(db, chapter_id)
        if not chapter:
            raise NotFoundException("章节不存在")

        # 检查是否有小节
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
        """获取章节小节列表

        Args:
            db: 数据库会话
            chapter_id: 章节ID

        Returns:
            小节列表
        """
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
        data: SectionCreate,
    ) -> Section:
        """创建小节

        Args:
            db: 数据库会话
            course_id: 课程ID
            chapter_id: 章节ID
            data: 创建数据

        Returns:
            创建的小节

        Raises:
            NotFoundException: 章节不存在
        """
        # 验证章节存在
        chapter = await db.get(Chapter, chapter_id)
        if not chapter:
            raise NotFoundException("章节不存在")

        section = Section(
            course_id=course_id,
            chapter_id=chapter_id,
            title=data.title,
            description=data.description,
            sort_order=data.sort_order,
            is_free=data.is_free,
        )
        db.add(section)

        # 更新章节小节数量
        chapter.section_count += 1

        await db.flush()
        return section

    async def update(
        self,
        db: AsyncSession,
        section_id: int,
        data: SectionUpdate,
    ) -> Section:
        """更新小节

        Args:
            db: 数据库会话
            section_id: 小节ID
            data: 更新数据

        Returns:
            更新后的小节

        Raises:
            NotFoundException: 小节不存在
        """
        section = await self.get_by_id(db, section_id)
        if not section:
            raise NotFoundException("小节不存在")

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(section, key, value)

        await db.flush()
        return section

    async def delete(
        self,
        db: AsyncSession,
        section_id: int,
    ) -> None:
        """删除小节

        Args:
            db: 数据库会话
            section_id: 小节ID

        Raises:
            NotFoundException: 小节不存在
            ValidationException: 存在资源
        """
        section = await self.get_by_id(db, section_id)
        if not section:
            raise NotFoundException("小节不存在")

        # 检查是否有资源
        resources = await db.execute(
            select(func.count()).where(Resource.section_id == section_id)
        )
        if resources.scalar() > 0:
            raise ValidationException("存在资源，无法删除")

        # 更新章节小节数量
        chapter = await db.get(Chapter, section.chapter_id)
        if chapter:
            chapter.section_count -= 1

        await db.delete(section)


class ResourceService:
    """资源服务类"""

    async def get_list(
        self,
        db: AsyncSession,
        section_id: int,
    ) -> list[Resource]:
        """获取小节资源列表

        Args:
            db: 数据库会话
            section_id: 小节ID

        Returns:
            资源列表
        """
        result = await db.execute(
            select(Resource)
            .where(Resource.section_id == section_id)
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
        data: ResourceCreate,
    ) -> Resource:
        """创建资源

        Args:
            db: 数据库会话
            course_id: 课程ID
            chapter_id: 章节ID
            section_id: 小节ID
            data: 创建数据

        Returns:
            创建的资源

        Raises:
            NotFoundException: 小节不存在
        """
        # 验证小节存在
        section = await db.get(Section, section_id)
        if not section:
            raise NotFoundException("小节不存在")

        resource = Resource(
            course_id=course_id,
            chapter_id=chapter_id,
            section_id=section_id,
            title=data.title,
            type=data.type,
            file_url=data.file_url,
            file_size=data.file_size,
            duration=data.duration,
            sort_order=data.sort_order,
            is_free=data.is_free,
        )
        db.add(resource)

        # 更新小节资源数量和时长
        section.resource_count += 1
        if data.type == "video":
            section.duration += data.duration

        # 更新章节时长
        chapter = await db.get(Chapter, chapter_id)
        if chapter and data.type == "video":
            chapter.total_duration += data.duration

        await db.flush()
        return resource

    async def delete(
        self,
        db: AsyncSession,
        resource_id: int,
    ) -> None:
        """删除资源

        Args:
            db: 数据库会话
            resource_id: 资源ID

        Raises:
            NotFoundException: 资源不存在
        """
        resource = await self.get_by_id(db, resource_id)
        if not resource:
            raise NotFoundException("资源不存在")

        # 更新小节资源数量和时长
        section = await db.get(Section, resource.section_id)
        if section:
            section.resource_count -= 1
            if resource.type == "video":
                section.duration -= resource.duration

        # 更新章节时长
        chapter = await db.get(Chapter, resource.chapter_id)
        if chapter and resource.type == "video":
            chapter.total_duration -= resource.duration

        await db.delete(resource)


# 创建全局服务实例
chapter_service = ChapterService()
section_service = SectionService()
resource_service = ResourceService()