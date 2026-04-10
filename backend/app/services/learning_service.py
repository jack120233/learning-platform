"""学习模块服务

提供学习进度管理的业务逻辑。
"""

from datetime import datetime, timezone

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException, ValidationException
from app.core.resource_types import normalize_resource_type
from app.models.content import Resource, Section
from app.models.learning import ResourceProgress
from app.schemas.learning import (
    SaveProgressRequest,
)


class LearningService:
    """学习服务类"""

    @staticmethod
    def _to_progress_payload(progress: ResourceProgress, total_time: int = 0) -> dict:
        return {
            "course_id": progress.course_id,
            "chapter_id": progress.chapter_id,
            "section_id": progress.section_id,
            "resource_id": progress.resource_id,
            "progress": progress.progress,
            "position": progress.position,
            "current_time": progress.position,
            "total_time": total_time,
            "is_completed": progress.is_completed,
            "last_play_at": progress.last_play_at,
            "last_learn_at": progress.last_play_at,
        }

    async def start_learning(
        self,
        db: AsyncSession,
        user_id: int,
        course_id: int,
    ) -> dict:
        """开始学习课程

        Args:
            db: 数据库会话
            user_id: 用户ID
            course_id: 课程ID

        Returns:
            学习状态信息
        """
        # 检查是否有学习记录
        result = await db.execute(
            select(ResourceProgress)
            .where(
                and_(
                    ResourceProgress.user_id == user_id,
                    ResourceProgress.course_id == course_id,
                )
            )
            .order_by(ResourceProgress.updated_at.desc())
            .limit(1)
        )
        progress = result.scalar_one_or_none()

        if progress:
            return {
                "course_id": course_id,
                "started_at": (progress.last_play_at or datetime.now(timezone.utc)).isoformat(),
                "has_progress": True,
                "last_resource_id": progress.resource_id,
                "last_position": progress.position,
            }

        return {
            "course_id": course_id,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "has_progress": False,
            "last_resource_id": None,
            "last_position": 0,
        }

    async def save_progress(
        self,
        db: AsyncSession,
        user_id: int,
        data: SaveProgressRequest,
    ) -> ResourceProgress:
        """保存学习进度

        Args:
            db: 数据库会话
            user_id: 用户ID
            data: 进度数据

        Returns:
            进度记录
        """
        resource = await db.get(Resource, data.resource_id)
        if not resource:
            raise NotFoundException("资源不存在")
        if resource.section_id is None:
            raise ValidationException("当前资源未绑定到小节，无法记录学习进度")

        course_id = data.course_id or resource.course_id
        chapter_id = data.chapter_id or resource.chapter_id
        section_id = data.section_id or resource.section_id
        position = data.position if data.position is not None else (data.current_time or 0)
        progress_percent = data.progress if data.progress is not None else 0.0

        # 查找现有进度记录
        result = await db.execute(
            select(ResourceProgress).where(
                and_(
                    ResourceProgress.user_id == user_id,
                    ResourceProgress.resource_id == data.resource_id,
                )
            )
        )
        progress = result.scalar_one_or_none()

        now = datetime.now(timezone.utc)

        if progress:
            # 更新进度
            progress.course_id = course_id
            progress.chapter_id = chapter_id
            progress.section_id = section_id
            progress.position = position
            progress.progress = progress_percent
            progress.last_play_at = now
            progress.is_completed = data.is_completed or progress_percent >= 95

            # 检查是否完成
            if progress.is_completed and not progress.completed_at:
                progress.completed_at = now
        else:
            # 创建新进度记录
            progress = ResourceProgress(
                user_id=user_id,
                course_id=course_id,
                chapter_id=chapter_id,
                section_id=section_id,
                resource_id=data.resource_id,
                position=position,
                progress=progress_percent,
                last_play_at=now,
            )
            if data.is_completed or progress_percent >= 95:
                progress.is_completed = True
                progress.completed_at = now
            db.add(progress)

        await db.flush()
        return progress

    async def get_progress(
        self,
        db: AsyncSession,
        user_id: int,
        course_id: int | None = None,
        section_id: int | None = None,
        resource_id: int | None = None,
    ) -> list[dict]:
        """获取课程或单资源学习进度

        Args:
            db: 数据库会话
            user_id: 用户ID
            course_id: 课程ID
            section_id: 小节ID
            resource_id: 资源ID

        Returns:
            进度列表
        """
        if course_id is None and (section_id is None or resource_id is None):
            raise ValidationException("course_id 或 section_id + resource_id 必须至少提供一组")

        query = select(ResourceProgress).where(ResourceProgress.user_id == user_id)
        if course_id is not None:
            query = query.where(ResourceProgress.course_id == course_id)
        if section_id is not None:
            query = query.where(ResourceProgress.section_id == section_id)
        if resource_id is not None:
            query = query.where(ResourceProgress.resource_id == resource_id)

        result = await db.execute(query.order_by(ResourceProgress.updated_at.desc(), ResourceProgress.id.desc()))
        progress_items = list(result.scalars().all())

        if section_id is not None and resource_id is not None:
            resource = await db.get(Resource, resource_id)
            if not resource:
                raise NotFoundException("资源不存在")
            progress = progress_items[0] if progress_items else None
            if progress:
                return [self._to_progress_payload(progress, resource.duration or 0)]
            return [{
                "course_id": resource.course_id,
                "chapter_id": resource.chapter_id,
                "section_id": section_id,
                "resource_id": resource_id,
                "progress": 0.0,
                "position": 0,
                "current_time": 0,
                "total_time": resource.duration or 0,
                "is_completed": False,
                "last_play_at": None,
                "last_learn_at": None,
            }]

        if not progress_items:
            return []

        resource_ids = [item.resource_id for item in progress_items]
        resource_result = await db.execute(
            select(Resource).where(Resource.id.in_(resource_ids))
        )
        resources_by_id = {resource.id: resource for resource in resource_result.scalars().all()}
        return [
            self._to_progress_payload(item, resources_by_id.get(item.resource_id).duration if resources_by_id.get(item.resource_id) else 0)
            for item in progress_items
        ]

    async def get_continue_info(
        self,
        db: AsyncSession,
        user_id: int,
        course_id: int,
    ) -> dict:
        """获取继续学习信息

        Args:
            db: 数据库会话
            user_id: 用户ID
            course_id: 课程ID

        Returns:
            继续学习信息
        """
        result = await db.execute(
            select(ResourceProgress)
            .where(
                and_(
                    ResourceProgress.user_id == user_id,
                    ResourceProgress.course_id == course_id,
                )
            )
            .order_by(ResourceProgress.updated_at.desc())
            .limit(1)
        )
        progress = result.scalar_one_or_none()

        if progress:
            section = await db.get(Section, progress.section_id)
            resource = await db.get(Resource, progress.resource_id)
            return {
                "course_id": course_id,
                "chapter_id": progress.chapter_id,
                "section_id": progress.section_id,
                "resource_id": progress.resource_id,
                "position": progress.position,
                "last_section_id": progress.section_id,
                "last_section_title": section.title if section else "",
                "last_resource_id": progress.resource_id,
                "last_resource_type": normalize_resource_type(
                    resource.type if resource else "",
                    file_url=resource.file_url if resource else None,
                    file_name=resource.title if resource else None,
                ),
                "current_time": progress.position,
                "last_learn_at": progress.last_play_at,
            }

        return {
            "course_id": course_id,
            "chapter_id": None,
            "section_id": None,
            "resource_id": None,
            "position": 0,
            "last_section_id": None,
            "last_section_title": "",
            "last_resource_id": None,
            "last_resource_type": "",
            "current_time": 0,
            "last_learn_at": None,
        }

    async def get_play_url(
        self,
        db: AsyncSession,
        user_id: int,
        resource_id: int,
    ) -> dict:
        """获取播放地址

        Args:
            db: 数据库会话
            user_id: 用户ID
            resource_id: 资源ID

        Returns:
            播放信息
        """
        resource = await db.get(Resource, resource_id)
        if not resource:
            raise NotFoundException("资源不存在")

        resource_type = normalize_resource_type(
            resource.type,
            file_url=resource.file_url,
            file_name=resource.title,
        )

        return {
            "resource_id": resource_id,
            "title": resource.title,
            "play_url": resource.file_url,
            "file_url": resource.file_url,
            "resource_type": resource_type,
            "file_name": resource.title,
            "duration": resource.duration,
            "is_free": resource.is_free,
            "resolution": None,
            "thumbnail_url": None,
        }

    async def get_preview_url(
        self,
        db: AsyncSession,
        user_id: int,
        resource_id: int,
    ) -> dict:
        """获取文档预览地址

        Args:
            db: 数据库会话
            user_id: 用户ID
            resource_id: 资源ID

        Returns:
            预览信息
        """
        resource = await db.get(Resource, resource_id)
        if not resource:
            raise NotFoundException("资源不存在")

        return {
            "resource_id": resource_id,
            "title": resource.title,
            "preview_url": resource.file_url,
            "file_type": resource.file_url.rsplit(".", 1)[-1] if "." in resource.file_url else resource.type,
        }


# 创建全局服务实例
learning_service = LearningService()
