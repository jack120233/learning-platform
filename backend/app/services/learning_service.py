"""学习模块服务

提供学习进度管理的业务逻辑。
"""

import json
from datetime import datetime, timezone

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException, ForbiddenException
from app.models.learning import ResourceProgress
from app.schemas.learning import (
    SaveProgressRequest,
    StartLearningRequest,
)


class LearningService:
    """学习服务类"""

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
                "has_progress": True,
                "last_resource_id": progress.resource_id,
                "last_position": progress.position,
            }

        return {
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
            progress.position = data.position
            progress.progress = data.progress
            progress.last_play_at = now

            # 检查是否完成
            if data.progress >= 95 and not progress.is_completed:
                progress.is_completed = True
                progress.completed_at = now
        else:
            # 创建新进度记录
            progress = ResourceProgress(
                user_id=user_id,
                course_id=data.course_id,
                chapter_id=data.chapter_id,
                section_id=data.section_id,
                resource_id=data.resource_id,
                position=data.position,
                progress=data.progress,
                last_play_at=now,
            )
            if data.progress >= 95:
                progress.is_completed = True
                progress.completed_at = now
            db.add(progress)

        await db.flush()
        return progress

    async def get_progress(
        self,
        db: AsyncSession,
        user_id: int,
        course_id: int,
    ) -> list[ResourceProgress]:
        """获取课程学习进度

        Args:
            db: 数据库会话
            user_id: 用户ID
            course_id: 课程ID

        Returns:
            进度列表
        """
        result = await db.execute(
            select(ResourceProgress).where(
                and_(
                    ResourceProgress.user_id == user_id,
                    ResourceProgress.course_id == course_id,
                )
            )
        )
        return list(result.scalars().all())

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
            return {
                "course_id": course_id,
                "chapter_id": progress.chapter_id,
                "section_id": progress.section_id,
                "resource_id": progress.resource_id,
                "position": progress.position,
            }

        return {
            "course_id": course_id,
            "chapter_id": None,
            "section_id": None,
            "resource_id": None,
            "position": 0,
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
        # 实际项目中需要：
        # 1. 查询资源信息
        # 2. 检查用户权限
        # 3. 生成带签名的播放URL
        return {
            "resource_id": resource_id,
            "title": "示例视频",
            "play_url": f"https://example.com/video/{resource_id}.mp4",
            "duration": 300,
            "is_free": True,
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
        # 实际项目中需要：
        # 1. 查询资源信息
        # 2. 检查用户权限
        # 3. 生成预览URL
        return {
            "resource_id": resource_id,
            "title": "示例文档",
            "preview_url": f"https://example.com/doc/{resource_id}.pdf",
            "file_type": "pdf",
        }


# 创建全局服务实例
learning_service = LearningService()