"""系统管理服务模块

提供分类、标签、公告管理的业务逻辑。
"""

from datetime import datetime, timezone
from typing import Literal

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictException, NotFoundException, ValidationException
from app.models.category import Category
from app.models.tag import Tag
from app.models.announcement import Announcement
from app.schemas.system import (
    AnnouncementCreate,
    AnnouncementUpdate,
    CategoryCreate,
    CategoryUpdate,
    TagCreate,
)


class CategoryService:
    """分类服务类"""

    async def get_list(
        self,
        db: AsyncSession,
        parent_id: int | None = None,
        is_active: bool | None = None,
    ) -> list[Category]:
        """获取分类列表

        Args:
            db: 数据库会话
            parent_id: 父分类ID
            is_active: 是否启用

        Returns:
            分类列表
        """
        query = select(Category)

        if parent_id is not None:
            query = query.where(Category.parent_id == parent_id)
        if is_active is not None:
            query = query.where(Category.is_active == is_active)

        query = query.order_by(Category.sort_order, Category.id)
        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_by_id(self, db: AsyncSession, category_id: int) -> Category | None:
        """通过ID获取分类"""
        return await db.get(Category, category_id)

    async def create(
        self,
        db: AsyncSession,
        data: CategoryCreate,
    ) -> Category:
        """创建分类

        Args:
            db: 数据库会话
            data: 创建数据

        Returns:
            创建的分类

        Raises:
            ConflictException: slug已存在
            NotFoundException: 父分类不存在
        """
        # 检查slug是否已存在
        existing = await self._get_by_slug(db, data.slug)
        if existing:
            raise ConflictException("分类标识已存在")

        # 检查父分类是否存在
        if data.parent_id:
            parent = await self.get_by_id(db, data.parent_id)
            if not parent:
                raise NotFoundException("父分类不存在")

        category = Category(**data.model_dump())
        db.add(category)
        await db.flush()
        return category

    async def update(
        self,
        db: AsyncSession,
        category_id: int,
        data: CategoryUpdate,
    ) -> Category:
        """更新分类

        Args:
            db: 数据库会话
            category_id: 分类ID
            data: 更新数据

        Returns:
            更新后的分类

        Raises:
            NotFoundException: 分类不存在
            ConflictException: slug已存在
        """
        category = await self.get_by_id(db, category_id)
        if not category:
            raise NotFoundException("分类不存在")

        # 检查slug是否与其他分类冲突
        if data.slug and data.slug != category.slug:
            existing = await self._get_by_slug(db, data.slug)
            if existing:
                raise ConflictException("分类标识已存在")

        # 更新属性
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(category, key, value)

        await db.flush()
        return category

    async def delete(self, db: AsyncSession, category_id: int) -> None:
        """删除分类

        Args:
            db: 数据库会话
            category_id: 分类ID

        Raises:
            NotFoundException: 分类不存在
            ValidationException: 存在子分类
        """
        category = await self.get_by_id(db, category_id)
        if not category:
            raise NotFoundException("分类不存在")

        # 检查是否有子分类
        children = await self.get_list(db, parent_id=category_id)
        if children:
            raise ValidationException("存在子分类，无法删除")

        await db.delete(category)

    async def _get_by_slug(self, db: AsyncSession, slug: str) -> Category | None:
        """通过slug获取分类"""
        result = await db.execute(
            select(Category).where(Category.slug == slug)
        )
        return result.scalar_one_or_none()


class TagService:
    """标签服务类"""

    async def get_list(
        self,
        db: AsyncSession,
        keyword: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Tag], int]:
        """获取标签列表

        Args:
            db: 数据库会话
            keyword: 搜索关键词
            page: 页码
            page_size: 每页数量

        Returns:
            标签列表和总数
        """
        query = select(Tag)

        if keyword:
            query = query.where(Tag.name.ilike(f"%{keyword}%"))

        # 获取总数
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        # 分页查询
        query = query.order_by(Tag.use_count.desc(), Tag.id)
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await db.execute(query)
        tags = list(result.scalars().all())

        return tags, total

    async def create(
        self,
        db: AsyncSession,
        data: TagCreate,
    ) -> Tag:
        """创建标签

        Args:
            db: 数据库会话
            data: 创建数据

        Returns:
            创建的标签

        Raises:
            ConflictException: 标签名称或slug已存在
        """
        # 检查名称是否已存在
        existing_name = await self._get_by_name(db, data.name)
        if existing_name:
            raise ConflictException("标签名称已存在")

        # 检查slug是否已存在
        existing_slug = await self._get_by_slug(db, data.slug)
        if existing_slug:
            raise ConflictException("标签标识已存在")

        tag = Tag(**data.model_dump())
        db.add(tag)
        await db.flush()
        return tag

    async def _get_by_name(self, db: AsyncSession, name: str) -> Tag | None:
        """通过名称获取标签"""
        result = await db.execute(
            select(Tag).where(Tag.name == name)
        )
        return result.scalar_one_or_none()

    async def _get_by_slug(self, db: AsyncSession, slug: str) -> Tag | None:
        """通过slug获取标签"""
        result = await db.execute(
            select(Tag).where(Tag.slug == slug)
        )
        return result.scalar_one_or_none()


class AnnouncementService:
    """公告服务类"""

    async def get_list(
        self,
        db: AsyncSession,
        is_published: bool | None = None,
        type: str | None = None,
        page: int = 1,
        page_size: int = 10,
    ) -> tuple[list[Announcement], int]:
        """获取公告列表

        Args:
            db: 数据库会话
            is_published: 是否已发布
            type: 公告类型
            page: 页码
            page_size: 每页数量

        Returns:
            公告列表和总数
        """
        query = select(Announcement)

        if is_published is not None:
            query = query.where(Announcement.is_published == is_published)
        if type:
            query = query.where(Announcement.type == type)

        # 获取总数
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        # 排序：置顶在前，然后按发布时间倒序
        query = query.order_by(
            Announcement.is_top.desc(),
            Announcement.publish_at.desc(),
        )
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await db.execute(query)
        announcements = list(result.scalars().all())

        return announcements, total

    async def get_active_list(
        self,
        db: AsyncSession,
        limit: int = 5,
    ) -> list[Announcement]:
        """获取有效公告列表（用于前台展示）

        Args:
            db: 数据库会话
            limit: 返回数量

        Returns:
            有效公告列表
        """
        now = datetime.now(timezone.utc)
        query = select(Announcement).where(
            and_(
                Announcement.is_published == True,
                Announcement.publish_at <= now,
                (Announcement.expire_at == None) | (Announcement.expire_at > now),
            )
        )
        query = query.order_by(
            Announcement.is_top.desc(),
            Announcement.publish_at.desc(),
        ).limit(limit)

        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_by_id(
        self,
        db: AsyncSession,
        announcement_id: int,
    ) -> Announcement | None:
        """通过ID获取公告"""
        return await db.get(Announcement, announcement_id)


# 创建全局服务实例
category_service = CategoryService()
tag_service = TagService()
announcement_service = AnnouncementService()