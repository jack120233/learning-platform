"""学习模块服务

提供学习进度管理的业务逻辑。
"""

from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import func, select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenException, NotFoundException, ValidationException
from app.core.resource_types import normalize_resource_type
from app.models.content import Resource, Section
from app.models.learning import LearningRecordEntry, LearningSession, ResourceProgress
from app.models.learning_progress import LearningProgress
from app.schemas.learning import LearningSessionRequest, SaveProgressRequest


class LearningService:
    """学习服务类"""

    ANALYTICS_RESOURCE_TYPES = {"video", "audio", "document", "image"}
    RESOURCE_TYPE_CAPS = {
        "document": 20 * 60,
        "image": 5 * 60,
    }

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
        await self._sync_course_progress_and_record(db, user_id, progress, now)
        await db.flush()
        return progress

    async def _sync_course_progress_and_record(
        self,
        db: AsyncSession,
        user_id: int,
        resource_progress: ResourceProgress,
        learned_at: datetime,
    ) -> LearningProgress:
        """同步课程级进度和学生可见学习记录。"""
        required_resource_result = await db.execute(
            select(Resource.id)
            .where(
                Resource.course_id == resource_progress.course_id,
                Resource.is_required.is_(True),
            )
        )
        required_resource_ids = [row[0] for row in required_resource_result.all()]
        required_count = len(required_resource_ids)
        completed_count = 0
        if required_resource_ids:
            completed_result = await db.execute(
                select(func.count(func.distinct(ResourceProgress.resource_id)))
                .select_from(ResourceProgress)
                .where(
                    ResourceProgress.user_id == user_id,
                    ResourceProgress.resource_id.in_(required_resource_ids),
                    ResourceProgress.is_completed.is_(True),
                )
            )
            completed_count = completed_result.scalar() or 0

        course_progress = round((completed_count / required_count) * 100, 2) if required_count else 0.0
        is_course_completed = required_count > 0 and completed_count >= required_count

        result = await db.execute(
            select(LearningProgress).where(
                LearningProgress.user_id == user_id,
                LearningProgress.course_id == resource_progress.course_id,
            )
        )
        learning_progress = result.scalar_one_or_none()
        if not learning_progress:
            learning_progress = LearningProgress(
                user_id=user_id,
                course_id=resource_progress.course_id,
            )
            db.add(learning_progress)

        learning_progress.progress = course_progress
        learning_progress.last_section_id = resource_progress.section_id
        learning_progress.last_resource_id = resource_progress.resource_id
        learning_progress.last_position = resource_progress.position
        learning_progress.last_learn_at = learned_at
        if is_course_completed and learning_progress.completed_at is None:
            learning_progress.completed_at = learned_at

        record_result = await db.execute(
            select(LearningRecordEntry).where(
                LearningRecordEntry.user_id == user_id,
                LearningRecordEntry.course_id == resource_progress.course_id,
                LearningRecordEntry.visible.is_(True),
            )
        )
        record = record_result.scalar_one_or_none()
        if not record:
            record = LearningRecordEntry(
                user_id=user_id,
                course_id=resource_progress.course_id,
                last_resource_id=resource_progress.resource_id,
                last_learn_at=learned_at,
            )
            db.add(record)

        record.last_section_id = resource_progress.section_id
        record.last_resource_id = resource_progress.resource_id
        record.last_learn_at = learned_at
        record.course_progress_snapshot = course_progress
        record.course_completed_snapshot = is_course_completed
        record.visible = True
        return learning_progress

    async def _ensure_resource_learning_access(self, db: AsyncSession, user_id: int, course_id: int) -> None:
        """复用当前课程学习边界：仅允许访问已发布课程或自己创建的课程。"""
        from app.models.course import Course
        from app.models.user import User

        course = await db.get(Course, course_id)
        if not course:
            raise NotFoundException("课程不存在")

        if course.status == "published" or course.teacher_id == user_id:
            return
        user = await db.get(User, user_id)
        if user and user.role == "admin":
            return
        raise ForbiddenException("无权学习该资源")

    def _normalize_session_duration(self, data: LearningSessionRequest, resource: Resource, resource_type: str) -> int:
        started_at = data.started_at.replace(tzinfo=None) if data.started_at.tzinfo else data.started_at
        ended_at = data.ended_at.replace(tzinfo=None) if data.ended_at.tzinfo else data.ended_at
        if ended_at < started_at:
            raise ValidationException("结束时间不能早于开始时间")
        if data.effective_duration_seconds < 0:
            raise ValidationException("有效学习时长不能为负数")
        if resource_type not in self.ANALYTICS_RESOURCE_TYPES:
            raise ValidationException("暂不支持该资源类型的学习会话统计")

        wall_clock_seconds = int((ended_at - started_at).total_seconds())
        caps = [data.effective_duration_seconds, wall_clock_seconds]
        type_cap = self.RESOURCE_TYPE_CAPS.get(resource_type)
        if type_cap is not None:
            caps.append(type_cap)
        if resource_type in {"video", "audio"} and resource.duration > 0:
            caps.append(resource.duration)
        return max(0, min(caps))

    async def save_session(
        self,
        db: AsyncSession,
        user_id: int,
        data: LearningSessionRequest,
    ) -> dict:
        """保存学习会话事实，按 session_id 幂等。"""
        resource = await db.get(Resource, data.resource_id)
        if not resource:
            raise NotFoundException("资源不存在")
        await self._ensure_resource_learning_access(db, user_id, resource.course_id)

        resource_type = normalize_resource_type(
            resource.type,
            file_url=resource.file_url,
            file_name=resource.title,
        )
        accepted_duration = self._normalize_session_duration(data, resource, resource_type)

        result = await db.execute(
            select(LearningSession).where(LearningSession.session_id == data.session_id)
        )
        session = result.scalar_one_or_none()
        duplicate = session is not None

        if session:
            if session.user_id != user_id:
                raise ValidationException("session_id 已被使用")
            if session.resource_id != data.resource_id:
                raise ValidationException("session_id 对应的资源不一致")

            previous_reason = session.end_reason
            previous_completed = session.is_completed_at_end
            previous_duration = session.effective_duration_seconds
            previous_ended_at = session.ended_at
            data_ended_at = data.ended_at.replace(tzinfo=None) if data.ended_at.tzinfo else data.ended_at
            session_ended_at = session.ended_at.replace(tzinfo=None) if session.ended_at.tzinfo else session.ended_at
            previous_ended_at_compare = previous_ended_at.replace(tzinfo=None) if previous_ended_at.tzinfo else previous_ended_at
            session.ended_at = data.ended_at if data_ended_at > session_ended_at else session.ended_at
            session.effective_duration_seconds = max(session.effective_duration_seconds, accepted_duration)
            if data.end_position_seconds is not None:
                session.end_position_seconds = max(session.end_position_seconds or 0, data.end_position_seconds)
            if data.progress_percent_at_end is not None:
                session.progress_percent_at_end = max(session.progress_percent_at_end or 0.0, data.progress_percent_at_end)
            session.is_completed_at_end = session.is_completed_at_end or data.is_completed_at_end
            if data.is_completed_at_end or accepted_duration > previous_duration or data_ended_at > previous_ended_at_compare:
                session.end_reason = data.end_reason
            if previous_completed and not data.is_completed_at_end:
                session.end_reason = previous_reason
        else:
            session = LearningSession(
                session_id=data.session_id,
                user_id=user_id,
                course_id=resource.course_id,
                chapter_id=resource.chapter_id,
                section_id=resource.section_id,
                resource_id=resource.id,
                resource_type=resource_type,
                started_at=data.started_at,
                ended_at=data.ended_at,
                effective_duration_seconds=accepted_duration,
                start_position_seconds=data.start_position_seconds,
                end_position_seconds=data.end_position_seconds,
                progress_percent_at_end=data.progress_percent_at_end,
                is_completed_at_end=data.is_completed_at_end,
                end_reason=data.end_reason,
            )
            db.add(session)

        await db.flush()
        return {
            "session_id": session.session_id,
            "accepted": True,
            "effective_duration_seconds": session.effective_duration_seconds,
            "duplicate": duplicate,
        }

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
        if course_id is None and resource_id is None:
            raise ValidationException("course_id 或 resource_id 必须至少提供一组")

        query = select(ResourceProgress).where(ResourceProgress.user_id == user_id)
        if course_id is not None:
            query = query.where(ResourceProgress.course_id == course_id)
        if section_id is not None:
            query = query.where(ResourceProgress.section_id == section_id)
        if resource_id is not None:
            query = query.where(ResourceProgress.resource_id == resource_id)

        result = await db.execute(query.order_by(ResourceProgress.updated_at.desc(), ResourceProgress.id.desc()))
        progress_items = list(result.scalars().all())

        if resource_id is not None and course_id is None:
            resource = await db.get(Resource, resource_id)
            if not resource:
                raise NotFoundException("资源不存在")
            progress = progress_items[0] if progress_items else None
            if progress:
                return [self._to_progress_payload(progress, resource.duration or 0)]
            return [{
                "course_id": resource.course_id,
                "chapter_id": resource.chapter_id,
                "section_id": resource.section_id,
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
            section = await db.get(Section, progress.section_id) if progress.section_id is not None else None
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
            "file_name": Path(resource.file_url).name or resource.title,
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
