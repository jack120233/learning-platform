"""老师课程学习统计服务。"""

from __future__ import annotations

import csv
import io
from datetime import date, datetime, time, timedelta, timezone
from typing import Literal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenException, ValidationException
from app.models.course import Course, CourseTeacherAssignment
from app.models.learning import LearningSession
from app.models.learning_progress import LearningProgress
from app.models.user import User
from app.services.course_statistics_authorization_service import STATISTICS_VIEWER, course_statistics_authorization_service

TeacherPermissionType = Literal["owner", "authorized"]
StudentStatusFilter = Literal["all", "inactive", "low_progress", "completed"]


class TeacherStatisticsService:
    """老师课程学习统计读模型。"""

    def _ensure_teacher(self, current_user: User) -> None:
        if current_user.effective_role != "teacher":
            raise ForbiddenException("仅老师可访问课程统计")

    def _range_dates(self, trend_range: str) -> tuple[date, date]:
        if trend_range not in {"7d", "30d"}:
            raise ValidationException("range 仅支持 7d 或 30d")
        days = 30 if trend_range == "30d" else 7
        today = date.today()
        return today - timedelta(days=days - 1), today

    def _date_to_bounds(self, start_date: date | None, end_date: date | None) -> tuple[datetime | None, datetime | None]:
        start_at = datetime.combine(start_date, time.min) if start_date else None
        end_at = datetime.combine(end_date + timedelta(days=1), time.min) if end_date else None
        return start_at, end_at

    async def list_courses(
        self,
        db: AsyncSession,
        current_user: User,
        keyword: str | None = None,
        permission_type: str = "all",
        status: str = "all",
        page: int = 1,
        page_size: int = 10,
    ) -> tuple[list[dict], int]:
        """列出当前老师可查看统计的课程。"""
        self._ensure_teacher(current_user)
        if permission_type not in {"all", "owner", "authorized"}:
            raise ValidationException("permission_type 参数无效")
        if status not in {"all", "draft", "published", "archived"}:
            raise ValidationException("status 参数无效")

        viewable: dict[int, tuple[Course, TeacherPermissionType]] = {}
        if permission_type in {"all", "owner"}:
            owned_query = select(Course).where(Course.teacher_id == current_user.id)
            owned_result = await db.execute(owned_query)
            for course in owned_result.scalars().all():
                viewable[course.id] = (course, "owner")

        if permission_type in {"all", "authorized"}:
            authorized_query = (
                select(Course)
                .join(CourseTeacherAssignment, CourseTeacherAssignment.course_id == Course.id)
                .where(
                    CourseTeacherAssignment.teacher_id == current_user.id,
                    CourseTeacherAssignment.permission_type == STATISTICS_VIEWER,
                    CourseTeacherAssignment.is_active.is_(True),
                )
            )
            authorized_result = await db.execute(authorized_query)
            for course in authorized_result.scalars().all():
                viewable.setdefault(course.id, (course, "authorized"))

        filtered: list[tuple[Course, TeacherPermissionType]] = []
        normalized_keyword = keyword.strip().lower() if keyword else ""
        for course, course_permission_type in viewable.values():
            if status != "all" and course.status != status:
                continue
            if normalized_keyword and normalized_keyword not in course.title.lower():
                continue
            filtered.append((course, course_permission_type))

        filtered.sort(key=lambda item: item[0].created_at, reverse=True)
        total = len(filtered)
        offset = (page - 1) * page_size
        page_items = filtered[offset:offset + page_size]
        start_date, end_date = self._range_dates("7d")

        items = []
        for course, course_permission_type in page_items:
            metrics = await self.get_course_metrics(db, course.id, start_date, end_date)
            items.append({
                "course_id": course.id,
                "course_title": course.title,
                "course_cover": course.cover_url,
                "course_status": course.status,
                "permission_type": course_permission_type,
                "started_student_count": metrics["started_student_count"],
                "active_student_count_7d": metrics["active_student_count"],
                "avg_progress": metrics["avg_progress"],
                "completion_rate": metrics["completion_rate"],
                "total_duration_seconds": metrics["total_duration_seconds"],
                "recent_learn_at": metrics["recent_learn_at"],
            })
        return items, total

    async def get_overview(
        self,
        db: AsyncSession,
        course_id: int,
        current_user: User,
        trend_range: str = "7d",
    ) -> dict:
        """获取单门课程统计概览。"""
        self._ensure_teacher(current_user)
        course = await course_statistics_authorization_service.ensure_statistics_access(db, course_id, current_user)
        start_date, end_date = self._range_dates(trend_range)
        metrics = await self.get_course_metrics(db, course.id, start_date, end_date)
        return {
            "course_id": course.id,
            "course_title": course.title,
            "range": trend_range,
            **metrics,
        }

    async def list_students(
        self,
        db: AsyncSession,
        course_id: int,
        current_user: User,
        status: str = "all",
        keyword: str | None = None,
        page: int = 1,
        page_size: int = 10,
    ) -> tuple[list[dict], int]:
        """分页获取课程学生学习明细。"""
        self._ensure_teacher(current_user)
        await course_statistics_authorization_service.ensure_statistics_access(db, course_id, current_user)
        rows = await self._get_student_detail_rows(db, course_id, status=status, keyword=keyword)
        total = len(rows)
        offset = (page - 1) * page_size
        return rows[offset:offset + page_size], total

    async def export_students_csv(
        self,
        db: AsyncSession,
        course_id: int,
        current_user: User,
        status: str = "all",
        keyword: str | None = None,
    ) -> str:
        """导出课程学生学习明细 CSV，含 UTF-8 BOM。"""
        self._ensure_teacher(current_user)
        await course_statistics_authorization_service.ensure_statistics_access(db, course_id, current_user)
        rows = await self._get_student_detail_rows(db, course_id, status=status, keyword=keyword)
        output = io.StringIO()
        output.write("﻿")
        writer = csv.writer(output)
        writer.writerow(["学生ID", "用户名", "学习进度", "有效学习时长（秒）", "最近学习时间", "是否完成", "完成时间"])
        for row in rows:
            writer.writerow([
                row["student_id"],
                row["username"],
                row["progress"],
                row["total_duration_seconds"],
                row["last_learn_at"].isoformat() if row["last_learn_at"] else "",
                "是" if row["is_completed"] else "否",
                row["completed_at"].isoformat() if row["completed_at"] else "",
            ])
        return output.getvalue()

    async def get_course_metrics(
        self,
        db: AsyncSession,
        course_id: int,
        start_date: date | None,
        end_date: date | None,
    ) -> dict:
        """计算课程统计指标；时长仅来自学习会话事实。"""
        start_at, end_at = self._date_to_bounds(start_date, end_date)
        started_student_ids = await self._get_started_student_ids(db, course_id)
        active_student_count = await self._count_active_students(db, course_id, start_at, end_at)
        total_duration = await self._sum_session_duration(db, course_id, None, None)
        range_duration = await self._sum_session_duration(db, course_id, start_at, end_at)
        avg_progress = await self._avg_progress(db, course_id)
        completed_count = await self._count_completed_students(db, course_id)
        started_count = len(started_student_ids)
        completion_rate = (completed_count / started_count * 100) if started_count else 0.0
        return {
            "started_student_count": started_count,
            "active_student_count": active_student_count,
            "avg_progress": round(avg_progress, 2),
            "completion_rate": round(completion_rate, 2),
            "avg_duration_seconds": int(total_duration / started_count) if started_count else 0,
            "total_duration_seconds": total_duration,
            "range_duration_seconds": range_duration,
            "recent_learn_at": await self._recent_learn_at(db, course_id),
        }

    async def _get_student_detail_rows(
        self,
        db: AsyncSession,
        course_id: int,
        status: str,
        keyword: str | None,
    ) -> list[dict]:
        if status not in {"all", "inactive", "low_progress", "completed"}:
            raise ValidationException("status 参数无效")

        student_ids = await self._get_started_student_ids(db, course_id)
        if not student_ids:
            return []

        user_query = select(User.id, User.username).where(
            User.role == "student",
            User.id.in_(student_ids),
        )
        if keyword:
            user_query = user_query.where(User.username.ilike(f"%{keyword.strip()}%"))
        user_result = await db.execute(user_query)
        users = {user_id: username for user_id, username in user_result.all()}

        progress_result = await db.execute(
            select(
                LearningProgress.user_id,
                LearningProgress.progress,
                LearningProgress.last_learn_at,
                LearningProgress.completed_at,
            )
            .join(User, User.id == LearningProgress.user_id)
            .where(
                User.role == "student",
                LearningProgress.course_id == course_id,
                LearningProgress.user_id.in_(list(users.keys()) or [-1]),
            )
        )
        progress_by_user = {
            user_id: {
                "progress": float(progress or 0.0),
                "last_learn_at": last_learn_at,
                "completed_at": completed_at,
            }
            for user_id, progress, last_learn_at, completed_at in progress_result.all()
        }

        durations = await self._student_durations(db, course_id, list(users.keys()))
        session_last_times = await self._student_recent_session_times(db, course_id, list(users.keys()))
        inactive_threshold = self._to_naive_utc(datetime.now(timezone.utc) - timedelta(days=7))
        rows = []
        for student_id, username in users.items():
            progress = progress_by_user.get(student_id, {})
            progress_value = float(progress.get("progress", 0.0))
            progress_last = self._to_naive_utc(progress.get("last_learn_at"))
            session_last = self._to_naive_utc(session_last_times.get(student_id))
            last_learn_at = max([item for item in (progress_last, session_last) if item is not None], default=None)
            completed_at = self._to_naive_utc(progress.get("completed_at"))
            is_completed = completed_at is not None
            row = {
                "student_id": student_id,
                "username": username,
                "progress": round(progress_value, 2),
                "total_duration_seconds": durations.get(student_id, 0),
                "last_learn_at": last_learn_at,
                "completed_at": completed_at,
                "is_completed": is_completed,
            }
            if status == "inactive" and not (last_learn_at is None or last_learn_at < inactive_threshold):
                continue
            if status == "low_progress" and not (progress_value < 30 and not is_completed):
                continue
            if status == "completed" and not is_completed:
                continue
            rows.append(row)

        rows.sort(key=lambda item: (item["progress"], item["student_id"]))
        return rows

    async def _get_started_student_ids(self, db: AsyncSession, course_id: int) -> set[int]:
        progress_result = await db.execute(
            select(LearningProgress.user_id)
            .join(User, User.id == LearningProgress.user_id)
            .where(User.role == "student", LearningProgress.course_id == course_id)
        )
        session_result = await db.execute(
            select(LearningSession.user_id)
            .join(User, User.id == LearningSession.user_id)
            .where(User.role == "student", LearningSession.course_id == course_id)
        )
        return set(progress_result.scalars().all()) | set(session_result.scalars().all())

    async def _count_active_students(
        self,
        db: AsyncSession,
        course_id: int,
        start_at: datetime | None,
        end_at: datetime | None,
    ) -> int:
        query = select(func.count(func.distinct(LearningSession.user_id))).join(User, User.id == LearningSession.user_id).where(
            User.role == "student",
            LearningSession.course_id == course_id,
        )
        if start_at is not None:
            query = query.where(LearningSession.started_at >= start_at)
        if end_at is not None:
            query = query.where(LearningSession.started_at < end_at)
        result = await db.execute(query)
        return int(result.scalar() or 0)

    async def _sum_session_duration(
        self,
        db: AsyncSession,
        course_id: int,
        start_at: datetime | None,
        end_at: datetime | None,
    ) -> int:
        query = select(func.sum(LearningSession.effective_duration_seconds)).join(User, User.id == LearningSession.user_id).where(
            User.role == "student",
            LearningSession.course_id == course_id,
        )
        if start_at is not None:
            query = query.where(LearningSession.started_at >= start_at)
        if end_at is not None:
            query = query.where(LearningSession.started_at < end_at)
        result = await db.execute(query)
        return int(result.scalar() or 0)

    async def _avg_progress(self, db: AsyncSession, course_id: int) -> float:
        result = await db.execute(
            select(func.avg(LearningProgress.progress))
            .join(User, User.id == LearningProgress.user_id)
            .where(User.role == "student", LearningProgress.course_id == course_id)
        )
        return float(result.scalar() or 0.0)

    async def _count_completed_students(self, db: AsyncSession, course_id: int) -> int:
        result = await db.execute(
            select(func.count(func.distinct(LearningProgress.user_id)))
            .join(User, User.id == LearningProgress.user_id)
            .where(
                User.role == "student",
                LearningProgress.course_id == course_id,
                LearningProgress.completed_at.is_not(None),
            )
        )
        return int(result.scalar() or 0)

    async def _recent_learn_at(self, db: AsyncSession, course_id: int) -> datetime | None:
        progress_result = await db.execute(
            select(func.max(LearningProgress.last_learn_at))
            .join(User, User.id == LearningProgress.user_id)
            .where(User.role == "student", LearningProgress.course_id == course_id)
        )
        session_result = await db.execute(
            select(func.max(LearningSession.started_at))
            .join(User, User.id == LearningSession.user_id)
            .where(User.role == "student", LearningSession.course_id == course_id)
        )
        candidates = [value for value in (progress_result.scalar(), session_result.scalar()) if value is not None]
        return max(candidates) if candidates else None

    async def _student_durations(self, db: AsyncSession, course_id: int, user_ids: list[int]) -> dict[int, int]:
        if not user_ids:
            return {}
        result = await db.execute(
            select(LearningSession.user_id, func.sum(LearningSession.effective_duration_seconds))
            .join(User, User.id == LearningSession.user_id)
            .where(
                User.role == "student",
                LearningSession.course_id == course_id,
                LearningSession.user_id.in_(user_ids),
            )
            .group_by(LearningSession.user_id)
        )
        return {user_id: int(duration or 0) for user_id, duration in result.all()}

    async def _student_recent_session_times(self, db: AsyncSession, course_id: int, user_ids: list[int]) -> dict[int, datetime]:
        if not user_ids:
            return {}
        result = await db.execute(
            select(LearningSession.user_id, func.max(LearningSession.started_at))
            .join(User, User.id == LearningSession.user_id)
            .where(
                User.role == "student",
                LearningSession.course_id == course_id,
                LearningSession.user_id.in_(user_ids),
            )
            .group_by(LearningSession.user_id)
        )
        return {user_id: started_at for user_id, started_at in result.all() if started_at is not None}

    def _to_naive_utc(self, value: datetime | None) -> datetime | None:
        """Normalize datetimes for cross-database comparison."""
        if value is None:
            return None
        if value.tzinfo is None:
            return value
        return value.astimezone(timezone.utc).replace(tzinfo=None)


teacher_statistics_service = TeacherStatisticsService()
