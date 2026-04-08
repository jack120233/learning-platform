"""课程管理服务模块

提供课程管理相关的业务逻辑。
"""

from collections import defaultdict
from datetime import datetime, timezone
from typing import Literal

from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    ForbiddenException,
    NotFoundException,
    ValidationException,
)
from app.models.course import Course, CourseMaterial, CourseTag
from app.models.content import Chapter, Section
from app.schemas.course import (
    CourseCreate,
    CourseUpdate,
    MaterialCreate,
)
from app.schemas.content import ChapterWithSections, SectionResponse


class CourseService:
    """课程管理服务类"""

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
        """获取课程列表

        Args:
            db: 数据库会话
            status: 状态筛选
            category_id: 分类筛选
            teacher_id: 讲师筛选
            is_free: 是否免费筛选
            page: 页码
            page_size: 每页数量

        Returns:
            课程列表和总数
        """
        query = select(Course)

        if status:
            query = query.where(Course.status == status)
        if category_id:
            query = query.where(Course.category_id == category_id)
        if teacher_id:
            query = query.where(Course.teacher_id == teacher_id)
        if is_free is not None:
            query = query.where(Course.is_free == is_free)

        # 获取总数
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        # 排序和分页
        query = query.order_by(Course.published_at.desc(), Course.id.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await db.execute(query)
        courses = list(result.scalars().all())

        return courses, total

    async def get_by_id(
        self,
        db: AsyncSession,
        course_id: int,
    ) -> Course | None:
        """通过ID获取课程"""
        return await db.get(Course, course_id)

    async def get_chapters_with_sections(
        self,
        db: AsyncSession,
        course_id: int,
    ) -> list[ChapterWithSections]:
        """获取课程详情页需要的章节树。"""
        chapter_result = await db.execute(
            select(Chapter)
            .where(Chapter.course_id == course_id)
            .order_by(Chapter.sort_order, Chapter.id)
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

        sections_by_chapter: dict[int, list[SectionResponse]] = defaultdict(list)
        for section in sections:
            sections_by_chapter[section.chapter_id].append(
                SectionResponse.model_validate(section)
            )

        chapter_items: list[ChapterWithSections] = []
        for chapter in chapters:
            chapter_sections = sections_by_chapter.get(chapter.id, [])
            chapter_items.append(
                ChapterWithSections(
                    chapter_id=chapter.id,
                    course_id=chapter.course_id,
                    title=chapter.title,
                    description=chapter.description,
                    sort_order=chapter.sort_order,
                    is_free=chapter.is_free,
                    total_duration=sum(
                        section.duration for section in chapter_sections
                    ),
                    section_count=len(chapter_sections),
                    created_at=chapter.created_at,
                    sections=chapter_sections,
                )
            )

        return chapter_items

    async def create(
        self,
        db: AsyncSession,
        teacher_id: int,
        data: CourseCreate,
    ) -> Course:
        """创建课程

        Args:
            db: 数据库会话
            teacher_id: 讲师ID
            data: 创建数据

        Returns:
            创建的课程
        """
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
        )
        db.add(course)
        await db.flush()

        # 添加标签关联
        if data.tag_ids:
            for tag_id in data.tag_ids:
                course_tag = CourseTag(
                    course_id=course.id,
                    tag_id=tag_id,
                )
                db.add(course_tag)

        return course

    async def update(
        self,
        db: AsyncSession,
        course_id: int,
        user_id: int,
        data: CourseUpdate,
    ) -> Course:
        """更新课程

        Args:
            db: 数据库会话
            course_id: 课程ID
            user_id: 当前用户ID
            data: 更新数据

        Returns:
            更新后的课程

        Raises:
            NotFoundException: 课程不存在
            ForbiddenException: 无权限
        """
        course = await self.get_by_id(db, course_id)
        if not course:
            raise NotFoundException("课程不存在")

        # 检查权限
        if course.teacher_id != user_id:
            raise ForbiddenException("无权修改此课程")

        # 更新属性
        update_data = data.model_dump(exclude_unset=True, exclude={"tag_ids"})
        for key, value in update_data.items():
            setattr(course, key, value)

        # 更新标签
        if data.tag_ids is not None:
            # 删除原有标签
            await db.execute(
                CourseTag.__table__.delete().where(CourseTag.course_id == course_id)
            )
            # 添加新标签
            for tag_id in data.tag_ids:
                course_tag = CourseTag(
                    course_id=course.id,
                    tag_id=tag_id,
                )
                db.add(course_tag)

        await db.flush()
        return course

    async def publish(
        self,
        db: AsyncSession,
        course_id: int,
        user_id: int,
    ) -> Course:
        """发布课程

        Args:
            db: 数据库会话
            course_id: 课程ID
            user_id: 当前用户ID

        Returns:
            发布后的课程

        Raises:
            NotFoundException: 课程不存在
            ForbiddenException: 无权限
            ValidationException: 课程信息不完整
        """
        course = await self.get_by_id(db, course_id)
        if not course:
            raise NotFoundException("课程不存在")

        # 检查权限
        if course.teacher_id != user_id:
            raise ForbiddenException("无权发布此课程")

        # 检查课程状态
        if course.status == "published":
            raise ValidationException("课程已发布")

        # 检查课程信息是否完整
        if not course.title or not course.description:
            raise ValidationException("请完善课程信息后再发布")

        course.status = "published"
        course.published_at = datetime.now(timezone.utc)

        await db.flush()
        return course

    async def archive(
        self,
        db: AsyncSession,
        course_id: int,
        user_id: int,
    ) -> Course:
        """下架课程

        Args:
            db: 数据库会话
            course_id: 课程ID
            user_id: 当前用户ID

        Returns:
            下架后的课程

        Raises:
            NotFoundException: 课程不存在
            ForbiddenException: 无权限
        """
        course = await self.get_by_id(db, course_id)
        if not course:
            raise NotFoundException("课程不存在")

        # 检查权限
        if course.teacher_id != user_id:
            raise ForbiddenException("无权下架此课程")

        course.status = "archived"
        await db.flush()
        return course

    async def delete(
        self,
        db: AsyncSession,
        course_id: int,
        user_id: int,
    ) -> None:
        """删除课程

        Args:
            db: 数据库会话
            course_id: 课程ID
            user_id: 当前用户ID

        Raises:
            NotFoundException: 课程不存在
            ForbiddenException: 无权限
            ValidationException: 已发布的课程不能删除
        """
        course = await self.get_by_id(db, course_id)
        if not course:
            raise NotFoundException("课程不存在")

        # 检查权限
        if course.teacher_id != user_id:
            raise ForbiddenException("无权删除此课程")

        # 检查课程状态
        if course.status == "published":
            raise ValidationException("已发布的课程不能删除，请先下架")

        await db.delete(course)

    async def get_my_courses(
        self,
        db: AsyncSession,
        teacher_id: int,
        status: str | None = None,
        page: int = 1,
        page_size: int = 10,
    ) -> tuple[list[Course], int]:
        """获取我的课程列表

        Args:
            db: 数据库会话
            teacher_id: 讲师ID
            status: 状态筛选
            page: 页码
            page_size: 每页数量

        Returns:
            课程列表和总数
        """
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
        """搜索课程

        Args:
            db: 数据库会话
            keyword: 关键词
            category_id: 分类ID
            level: 难度等级
            is_free: 是否免费
            min_price: 最低价格
            max_price: 最高价格
            sort_by: 排序字段
            sort_order: 排序方向
            page: 页码
            page_size: 每页数量

        Returns:
            课程列表和总数
        """
        query = select(Course).where(Course.status == "published")

        # 关键词搜索
        if keyword:
            query = query.where(
                or_(
                    Course.title.ilike(f"%{keyword}%"),
                    Course.description.ilike(f"%{keyword}%"),
                )
            )

        # 条件筛选
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

        # 获取总数
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        # 排序
        sort_column = getattr(Course, sort_by, Course.published_at)
        if sort_order == "asc":
            query = query.order_by(sort_column.asc())
        else:
            query = query.order_by(sort_column.desc())

        # 分页
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await db.execute(query)
        courses = list(result.scalars().all())

        return courses, total

    async def get_homepage_courses(
        self,
        db: AsyncSession,
        limit: int = 8,
    ) -> list[Course]:
        """获取首页推荐课程

        Args:
            db: 数据库会话
            limit: 返回数量

        Returns:
            推荐课程列表
        """
        query = select(Course).where(
            Course.status == "published"
        ).order_by(
            Course.rating.desc(),
            Course.student_count.desc(),
        ).limit(limit)

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
        """创建配套资料

        Args:
            db: 数据库会话
            course_id: 课程ID
            user_id: 当前用户ID
            data: 创建数据

        Returns:
            创建的资料

        Raises:
            NotFoundException: 课程不存在
            ForbiddenException: 无权限
        """
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

    async def delete(
        self,
        db: AsyncSession,
        material_id: int,
        user_id: int,
    ) -> None:
        """删除配套资料

        Args:
            db: 数据库会话
            material_id: 资料ID
            user_id: 当前用户ID

        Raises:
            NotFoundException: 资料不存在
            ForbiddenException: 无权限
        """
        material = await db.get(CourseMaterial, material_id)
        if not material:
            raise NotFoundException("资料不存在")

        course = await db.get(Course, material.course_id)
        if not course or course.teacher_id != user_id:
            raise ForbiddenException("无权删除此资料")

        await db.delete(material)

    async def get_by_course(
        self,
        db: AsyncSession,
        course_id: int,
    ) -> list[CourseMaterial]:
        """获取课程的所有资料"""
        result = await db.execute(
            select(CourseMaterial).where(
                CourseMaterial.course_id == course_id
            ).order_by(CourseMaterial.created_at.desc())
        )
        return list(result.scalars().all())


# 创建全局服务实例
course_service = CourseService()
material_service = MaterialService()
