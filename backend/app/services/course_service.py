"""课程管理服务模块

提供课程管理相关的业务逻辑。
"""

from collections import defaultdict
from datetime import datetime, timezone
from typing import Literal

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenException, NotFoundException, ValidationException
from app.core.resource_types import normalize_resource_type
from app.models.content import Chapter, Resource, Section
from app.models.course import Course, CourseMaterial, CourseTag
from app.models.user import User
from app.schemas.content import ChapterWithSections, ResourceResponse, SectionResponse
from app.schemas.course import (
    BatchCourseActionFailure,
    BatchCourseActionResponse,
    CourseCreate,
    CourseManageScope,
    CourseUpdate,
    MaterialCreate,
)


class CourseService:
    """课程管理服务类"""

    def _can_manage_course(self, current_user: User, course: Course) -> bool:
        return current_user.role == "admin" or course.teacher_id == current_user.id

    def _can_publish_course(self, current_user: User, course: Course) -> bool:
        return course.teacher_id == current_user.id

    def _can_archive_course(self, current_user: User, course: Course) -> bool:
        return course.status == "published" and (
            current_user.role == "admin" or course.teacher_id == current_user.id
        )

    def _can_delete_course(self, current_user: User, course: Course) -> bool:
        return course.teacher_id == current_user.id and course.status != "published"

    def _ensure_course_exists(self, course: Course | None) -> Course:
        if not course:
            raise NotFoundException("课程不存在")
        return course

    def _ensure_publishable(self, course: Course) -> None:
        if course.status == "published":
            raise ValidationException("课程已发布")
        if not course.title or not course.description:
            raise ValidationException("请完善课程信息后再发布")

    async def get_list(
        self,
        db: AsyncSession,
        status: str | None = None,
        category_id: int | None = None,
        teacher_id: int | None = None,
        is_free: bool | None = None,
        page: int = 1,
        page_size: int = 10,
    ) -> tuple[list[Course], int]:
        """获取课程列表"""
        query = select(Course)

        if status:
            query = query.where(Course.status == status)
        if category_id:
            query = query.where(Course.category_id == category_id)
        if teacher_id:
            query = query.where(Course.teacher_id == teacher_id)
        if is_free is not None:
            query = query.where(Course.is_free == is_free)

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        query = query.order_by(Course.published_at.desc(), Course.id.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await db.execute(query)
        courses = list(result.scalars().all())
        return courses, total

    async def get_manage_courses(
        self,
        db: AsyncSession,
        current_user: User,
        scope: str = CourseManageScope.MINE,
        status: str | None = None,
        keyword: str | None = None,
        page: int = 1,
        page_size: int = 10,
    ) -> tuple[list[Course], int]:
        """获取课程管理列表。"""
        query = select(Course)

        if scope == CourseManageScope.PUBLISHED_ALL:
            if current_user.role != "admin":
                raise ForbiddenException("仅管理员可查看全部已发布课程")
            query = query.where(Course.status == "published")
        else:
            query = query.where(Course.teacher_id == current_user.id)
            if status:
                query = query.where(Course.status == status)

        if keyword:
            query = query.where(
                or_(
                    Course.title.ilike(f"%{keyword}%"),
                    Course.subtitle.ilike(f"%{keyword}%"),
                    Course.summary.ilike(f"%{keyword}%"),
                )
            )

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        query = query.order_by(Course.published_at.desc(), Course.created_at.desc(), Course.id.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await db.execute(query)
        return list(result.scalars().all()), total

    async def get_by_id(self, db: AsyncSession, course_id: int) -> Course | None:
        """通过ID获取课程"""
        return await db.get(Course, course_id)

    async def get_chapters_with_sections(
        self,
        db: AsyncSession,
        course_id: int,
    ) -> list[ChapterWithSections]:
        """获取课程详情页需要的章节树。"""
        chapter_result = await db.execute(
            select(Chapter).where(Chapter.course_id == course_id).order_by(Chapter.sort_order, Chapter.id)
        )
        chapters = list(chapter_result.scalars().all())
        if not chapters:
            return []

        chapter_ids = [chapter.id for chapter in chapters]
        section_result = await db.execute(
            select(Section)
            .where(Section.chapter_id.in_(chapter_ids))
            .order_by(Section.chapter_id, Section.sort_order, Section.id)
        )
        sections = list(section_result.scalars().all())
        section_ids = [section.id for section in sections]

        resource_result = await db.execute(
            select(Resource)
            .where(Resource.chapter_id.in_(chapter_ids))
            .order_by(Resource.chapter_id, Resource.section_id, Resource.sort_order, Resource.id)
        )
        resources = list(resource_result.scalars().all())

        chapter_resources_by_chapter: dict[int, list[ResourceResponse]] = defaultdict(list)
        section_resources_by_section: dict[int, list[ResourceResponse]] = defaultdict(list)
        for resource in resources:
            resource_item = ResourceResponse.model_validate(resource)
            normalized_type = normalize_resource_type(
                resource.type,
                file_url=resource.file_url,
                file_name=resource.title,
            )
            resource_item.type = normalized_type
            resource_item.resource_type = normalized_type
            if resource.section_id is None:
                chapter_resources_by_chapter[resource.chapter_id].append(resource_item)
            elif resource.section_id in section_ids:
                section_resources_by_section[resource.section_id].append(resource_item)

        sections_by_chapter: dict[int, list[SectionResponse]] = defaultdict(list)
        for section in sections:
            sections_by_chapter[section.chapter_id].append(
                SectionResponse(
                    section_id=section.id,
                    course_id=section.course_id,
                    chapter_id=section.chapter_id,
                    title=section.title,
                    description=section.description,
                    sort_order=section.sort_order,
                    is_free=section.is_free,
                    duration=section.duration,
                    resource_count=section.resource_count,
                    created_at=section.created_at,
                    resources=section_resources_by_section.get(section.id, []),
                )
            )

        chapter_items: list[ChapterWithSections] = []
        for chapter in chapters:
            chapter_sections = sections_by_chapter.get(chapter.id, [])
            chapter_resources = chapter_resources_by_chapter.get(chapter.id, [])
            computed_section_count = len(chapter_sections)
            computed_duration = sum(section.duration for section in chapter_sections) + sum(
                resource.duration for resource in chapter_resources if resource.resource_type == "video"
            )
            chapter_items.append(
                ChapterWithSections(
                    chapter_id=chapter.id,
                    course_id=chapter.course_id,
                    title=chapter.title,
                    description=chapter.description,
                    sort_order=chapter.sort_order,
                    is_free=chapter.is_free,
                    total_duration=max(chapter.total_duration, computed_duration),
                    section_count=max(chapter.section_count, computed_section_count),
                    created_at=chapter.created_at,
                    sections=chapter_sections,
                    resources=chapter_resources,
                )
            )

        return chapter_items

    async def create(self, db: AsyncSession, teacher_id: int, data: CourseCreate) -> Course:
        """创建课程"""
        course = Course(
            title=data.title,
            subtitle=data.subtitle,
            summary=data.summary,
            description=data.description,
            cover_url=data.cover_url,
            teacher_id=teacher_id,
            category_id=data.category_id,
            price=data.price,
            original_price=data.original_price,
            level=data.level,
            is_free=data.is_free,
            author=data.author,
        )
        db.add(course)
        await db.flush()

        if data.tag_ids:
            for tag_id in data.tag_ids:
                db.add(CourseTag(course_id=course.id, tag_id=tag_id))

        return course

    async def update(
        self,
        db: AsyncSession,
        course_id: int,
        current_user: User,
        data: CourseUpdate,
    ) -> Course:
        """更新课程"""
        course = self._ensure_course_exists(await self.get_by_id(db, course_id))
        if not self._can_manage_course(current_user, course):
            raise ForbiddenException("无权修改此课程")

        update_data = data.model_dump(exclude_unset=True, exclude={"tag_ids"})
        for key, value in update_data.items():
            setattr(course, key, value)

        if data.tag_ids is not None:
            await db.execute(CourseTag.__table__.delete().where(CourseTag.course_id == course_id))
            for tag_id in data.tag_ids:
                db.add(CourseTag(course_id=course.id, tag_id=tag_id))

        await db.flush()
        return course

    async def publish(self, db: AsyncSession, course_id: int, current_user: User) -> Course:
        """发布课程"""
        course = self._ensure_course_exists(await self.get_by_id(db, course_id))
        if not self._can_publish_course(current_user, course):
            raise ForbiddenException("无权发布此课程")
        self._ensure_publishable(course)
        course.status = "published"
        course.published_at = datetime.now(timezone.utc)
        await db.flush()
        return course

    async def archive(self, db: AsyncSession, course_id: int, current_user: User) -> Course:
        """下架课程"""
        course = self._ensure_course_exists(await self.get_by_id(db, course_id))
        if not self._can_archive_course(current_user, course):
            raise ForbiddenException("无权下架此课程")
        course.status = "archived"
        await db.flush()
        return course

    async def delete(self, db: AsyncSession, course_id: int, current_user: User) -> None:
        """删除课程"""
        course = self._ensure_course_exists(await self.get_by_id(db, course_id))
        if not self._can_delete_course(current_user, course):
            if course.status == "published":
                raise ValidationException("已发布的课程不能删除，请先下架")
            raise ForbiddenException("无权删除此课程")
        await db.delete(course)

    async def batch_action(
        self,
        db: AsyncSession,
        current_user: User,
        action: Literal["publish", "archive", "delete"],
        course_ids: list[int],
    ) -> BatchCourseActionResponse:
        """批量课程操作。"""
        unique_ids = list(dict.fromkeys(course_ids))
        response = BatchCourseActionResponse(action=action)

        for course_id in unique_ids:
            course = await self.get_by_id(db, course_id)
            if not course:
                response.failed_items.append(BatchCourseActionFailure(course_id=course_id, reason="课程不存在"))
                continue

            try:
                if action == "publish":
                    if not self._can_publish_course(current_user, course):
                        raise ForbiddenException("无权发布此课程")
                    self._ensure_publishable(course)
                    course.status = "published"
                    course.published_at = datetime.now(timezone.utc)
                elif action == "archive":
                    if not self._can_archive_course(current_user, course):
                        raise ForbiddenException("无权下架此课程")
                    course.status = "archived"
                else:
                    if not self._can_delete_course(current_user, course):
                        if course.status == "published":
                            raise ValidationException("已发布课程需先下架后才能删除")
                        raise ForbiddenException("无权删除此课程")
                    await db.delete(course)

                response.success_ids.append(course_id)
            except (ForbiddenException, ValidationException) as exc:
                response.failed_items.append(BatchCourseActionFailure(course_id=course_id, reason=str(exc)))

        response.success_count = len(response.success_ids)
        response.failed_count = len(response.failed_items)
        response.message = f"已成功处理 {response.success_count} 门课程"
        await db.flush()
        return response

    async def get_my_courses(
        self,
        db: AsyncSession,
        teacher_id: int,
        status: str | None = None,
        page: int = 1,
        page_size: int = 10,
    ) -> tuple[list[Course], int]:
        """获取我的课程列表"""
        return await self.get_list(
            db,
            status=status,
            teacher_id=teacher_id,
            page=page,
            page_size=page_size,
        )

    async def search(
        self,
        db: AsyncSession,
        keyword: str | None = None,
        category_id: int | None = None,
        level: str | None = None,
        is_free: bool | None = None,
        min_price: float | None = None,
        max_price: float | None = None,
        sort_by: str = "published_at",
        sort_order: str = "desc",
        page: int = 1,
        page_size: int = 10,
    ) -> tuple[list[Course], int]:
        """搜索课程"""
        query = select(Course).where(Course.status == "published")

        if keyword:
            query = query.where(
                or_(
                    Course.title.ilike(f"%{keyword}%"),
                    Course.description.ilike(f"%{keyword}%"),
                )
            )
        if category_id:
            query = query.where(Course.category_id == category_id)
        if level:
            query = query.where(Course.level == level)
        if is_free is not None:
            query = query.where(Course.is_free == is_free)
        if min_price is not None:
            query = query.where(Course.price >= min_price)
        if max_price is not None:
            query = query.where(Course.price <= max_price)

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        sort_column = getattr(Course, sort_by, Course.published_at)
        query = query.order_by(sort_column.asc() if sort_order == "asc" else sort_column.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await db.execute(query)
        return list(result.scalars().all()), total

    async def get_homepage_courses(self, db: AsyncSession, limit: int = 8) -> list[Course]:
        """获取首页推荐课程"""
        query = (
            select(Course)
            .where(Course.status == "published")
            .order_by(Course.rating.desc(), Course.student_count.desc())
            .limit(limit)
        )
        result = await db.execute(query)
        return list(result.scalars().all())


class MaterialService:
    """配套资料服务类"""

    async def create(
        self,
        db: AsyncSession,
        course_id: int,
        user_id: int,
        data: MaterialCreate,
    ) -> CourseMaterial:
        """创建配套资料"""
        course = await db.get(Course, course_id)
        if not course:
            raise NotFoundException("课程不存在")
        if course.teacher_id != user_id:
            raise ForbiddenException("无权为此课程添加资料")

        material = CourseMaterial(
            course_id=course_id,
            name=data.name,
            file_url=data.file_url,
            file_size=data.file_size,
            file_type=data.file_type,
        )
        db.add(material)
        await db.flush()
        return material

    async def delete(self, db: AsyncSession, material_id: int, user_id: int) -> None:
        """删除配套资料"""
        material = await db.get(CourseMaterial, material_id)
        if not material:
            raise NotFoundException("资料不存在")

        course = await db.get(Course, material.course_id)
        if not course or course.teacher_id != user_id:
            raise ForbiddenException("无权删除此资料")

        await db.delete(material)

    async def get_by_course(self, db: AsyncSession, course_id: int) -> list[CourseMaterial]:
        """获取课程的所有资料"""
        result = await db.execute(
            select(CourseMaterial)
            .where(CourseMaterial.course_id == course_id)
            .order_by(CourseMaterial.created_at.desc())
        )
        return list(result.scalars().all())


course_service = CourseService()
material_service = MaterialService()
