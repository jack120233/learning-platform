"""学习统计聚合服务。"""

from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, time, timedelta

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.learning import (
    CourseDailyLearningStats,
    LearningSession,
    PlatformDailyLearningStats,
    ResourceProgress,
    StudentCourseDailyStats,
    StudentDailyLearningStats,
)
from app.models.learning_progress import LearningProgress
from app.models.user import User


class LearningStatisticsService:
    """学习统计聚合服务。"""

    def _date_bounds(self, stat_date: date) -> tuple[datetime, datetime]:
        start = datetime.combine(stat_date, time.min)
        end = start + timedelta(days=1)
        return start, end

    def _as_comparable(self, value: datetime | None) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None:
            return value
        return value.replace(tzinfo=None)

    async def aggregate_date(self, db: AsyncSession, stat_date: date) -> dict:
        """重建单日学习统计。"""
        start_at, end_at = self._date_bounds(stat_date)
        await self._clear_date(db, stat_date)

        session_query = (
            select(LearningSession)
            .join(User, User.id == LearningSession.user_id)
            .where(
                User.role == "student",
                LearningSession.started_at >= start_at,
                LearningSession.started_at < end_at,
            )
        )
        session_result = await db.execute(session_query)
        sessions = list(session_result.scalars().all())

        student_rows: dict[int, dict] = defaultdict(lambda: {
            "effective_duration_seconds": 0,
            "video_duration_seconds": 0,
            "audio_duration_seconds": 0,
            "document_duration_seconds": 0,
            "image_duration_seconds": 0,
            "session_count": 0,
            "course_ids": set(),
            "completed_resource_ids": set(),
        })
        student_course_rows: dict[tuple[int, int], dict] = defaultdict(lambda: {
            "effective_duration_seconds": 0,
            "session_count": 0,
            "completed_resource_ids": set(),
        })
        course_rows: dict[int, dict] = defaultdict(lambda: {
            "active_user_ids": set(),
            "duration": 0,
        })
        active_courses: set[int] = set()

        for session in sessions:
            student = student_rows[session.user_id]
            student["effective_duration_seconds"] += session.effective_duration_seconds
            student["session_count"] += 1
            student["course_ids"].add(session.course_id)
            if session.is_completed_at_end:
                student["completed_resource_ids"].add(session.resource_id)
            type_key = f"{session.resource_type}_duration_seconds"
            if type_key in student:
                student[type_key] += session.effective_duration_seconds

            student_course = student_course_rows[(session.user_id, session.course_id)]
            student_course["effective_duration_seconds"] += session.effective_duration_seconds
            student_course["session_count"] += 1
            if session.is_completed_at_end:
                student_course["completed_resource_ids"].add(session.resource_id)

            course = course_rows[session.course_id]
            course["active_user_ids"].add(session.user_id)
            course["duration"] += session.effective_duration_seconds
            active_courses.add(session.course_id)

        for user_id, values in student_rows.items():
            db.add(StudentDailyLearningStats(
                user_id=user_id,
                stat_date=stat_date,
                effective_duration_seconds=values["effective_duration_seconds"],
                video_duration_seconds=values["video_duration_seconds"],
                audio_duration_seconds=values["audio_duration_seconds"],
                document_duration_seconds=values["document_duration_seconds"],
                image_duration_seconds=values["image_duration_seconds"],
                session_count=values["session_count"],
                learned_course_count=len(values["course_ids"]),
                completed_resource_count=len(values["completed_resource_ids"]),
            ))

        for (user_id, course_id), values in student_course_rows.items():
            progress = await self._get_learning_progress(db, user_id, course_id)
            db.add(StudentCourseDailyStats(
                user_id=user_id,
                course_id=course_id,
                stat_date=stat_date,
                effective_duration_seconds=values["effective_duration_seconds"],
                session_count=values["session_count"],
                completed_resource_count=len(values["completed_resource_ids"]),
                course_progress_at_day_end=progress.progress if progress else 0.0,
                is_course_completed_at_day_end=bool(progress and progress.completed_at),
            ))

        for course_id, values in course_rows.items():
            started_count = await self._count_course_started_students(db, course_id, start_at, end_at)
            completed_count = await self._count_course_completed_students(db, course_id, start_at, end_at)
            cumulative_started_count = await self._count_course_started_students(db, course_id, None, end_at)
            cumulative_completed_count = await self._count_course_completed_students(db, course_id, None, end_at)
            avg_progress = await self._avg_course_progress(db, course_id)
            completion_rate = (cumulative_completed_count / cumulative_started_count * 100) if cumulative_started_count else 0.0
            db.add(CourseDailyLearningStats(
                course_id=course_id,
                stat_date=stat_date,
                active_student_count=len(values["active_user_ids"]),
                new_started_student_count=started_count,
                new_completed_student_count=completed_count,
                cumulative_started_student_count=cumulative_started_count,
                cumulative_completed_student_count=cumulative_completed_count,
                total_effective_duration_seconds=values["duration"],
                avg_progress=round(avg_progress, 2),
                completion_rate=round(completion_rate, 2),
            ))

        new_started_course_count = 0
        new_completed_course_count = 0
        for course_id in active_courses:
            if await self._course_first_started_in_range(db, course_id, start_at, end_at):
                new_started_course_count += 1
            if await self._course_first_completed_in_range(db, course_id, start_at, end_at):
                new_completed_course_count += 1

        db.add(PlatformDailyLearningStats(
            stat_date=stat_date,
            active_student_count=len(student_rows),
            new_started_course_count=new_started_course_count,
            new_completed_course_count=new_completed_course_count,
            total_effective_duration_seconds=sum(row["effective_duration_seconds"] for row in student_rows.values()),
            active_course_count=len(active_courses),
        ))

        await db.flush()
        return {
            "stat_date": stat_date.isoformat(),
            "session_count": len(sessions),
            "student_count": len(student_rows),
            "course_count": len(active_courses),
        }

    async def aggregate_range(self, db: AsyncSession, start_date: date, end_date: date) -> list[dict]:
        """重建日期区间内的学习统计，包含起止日期。"""
        if end_date < start_date:
            raise ValueError("end_date cannot be earlier than start_date")

        results = []
        current = start_date
        while current <= end_date:
            results.append(await self.aggregate_date(db, current))
            current += timedelta(days=1)
        return results

    async def get_student_overview(self, db: AsyncSession, user_id: int) -> dict:
        """获取学生个人学习统计概览。"""
        today = date.today()
        last_7_start = today - timedelta(days=6)
        distribution = await self.get_student_course_distribution(db, user_id)
        daily_durations = await self._get_student_daily_durations(db, user_id, None, today)

        total_duration = await self._sum_student_session_duration(db, user_id, None, None)
        last_7_duration = sum(
            duration
            for stat_date, duration in daily_durations.items()
            if last_7_start <= stat_date <= today
        )
        active_dates = [stat_date for stat_date, duration in daily_durations.items() if duration > 0]

        return {
            "total_duration_seconds": total_duration,
            "last_7_days_duration_seconds": last_7_duration,
            "learning_course_count": distribution["learning_count"],
            "completed_course_count": distribution["completed_count"],
            "continuous_learning_days": self._continuous_days(active_dates, today),
            "active_learning_days": len(active_dates),
        }

    async def get_student_trend(self, db: AsyncSession, user_id: int, trend_range: str = "7d") -> dict:
        """获取学生个人学习趋势。"""
        if trend_range not in {"7d", "30d"}:
            raise ValueError("trend_range must be 7d or 30d")

        days = 30 if trend_range == "30d" else 7
        today = date.today()
        start_date = today - timedelta(days=days - 1)
        daily_durations = await self._get_student_daily_durations(db, user_id, start_date, today)

        items = []
        current = start_date
        while current <= today:
            items.append({
                "date": current.isoformat(),
                "duration_seconds": daily_durations.get(current, 0),
            })
            current += timedelta(days=1)

        return {"range": trend_range, "items": items}

    async def get_student_course_distribution(self, db: AsyncSession, user_id: int) -> dict:
        """获取学生课程学习/完成分布。"""
        learning_result = await db.execute(
            select(func.count()).select_from(LearningProgress).where(
                LearningProgress.user_id == user_id,
                LearningProgress.completed_at.is_(None),
            )
        )
        completed_result = await db.execute(
            select(func.count()).select_from(LearningProgress).where(
                LearningProgress.user_id == user_id,
                LearningProgress.completed_at.is_not(None),
            )
        )
        return {
            "learning_count": learning_result.scalar() or 0,
            "completed_count": completed_result.scalar() or 0,
        }

    async def _clear_date(self, db: AsyncSession, stat_date: date) -> None:
        for model in (
            StudentDailyLearningStats,
            StudentCourseDailyStats,
            CourseDailyLearningStats,
            PlatformDailyLearningStats,
        ):
            await db.execute(delete(model).where(model.stat_date == stat_date))

    async def _get_student_daily_durations(
        self,
        db: AsyncSession,
        user_id: int,
        start_date: date | None,
        end_date: date,
    ) -> dict[date, int]:
        """按自然日读取学生有效学习时长，当前日始终用实时会话覆盖。"""
        daily_durations: dict[date, int] = {}
        stats_query = select(
            StudentDailyLearningStats.stat_date,
            StudentDailyLearningStats.effective_duration_seconds,
        ).where(
            StudentDailyLearningStats.user_id == user_id,
            StudentDailyLearningStats.stat_date <= end_date,
        )
        if start_date is not None:
            stats_query = stats_query.where(StudentDailyLearningStats.stat_date >= start_date)
        stats_result = await db.execute(stats_query)
        for stat_date, duration in stats_result.all():
            daily_durations[stat_date] = int(duration or 0)

        session_query = select(
            func.date(LearningSession.started_at),
            func.sum(LearningSession.effective_duration_seconds),
        ).where(
            LearningSession.user_id == user_id,
            LearningSession.started_at < datetime.combine(end_date + timedelta(days=1), time.min),
        )
        if start_date is not None:
            session_query = session_query.where(
                LearningSession.started_at >= datetime.combine(start_date, time.min)
            )
        session_query = session_query.group_by(func.date(LearningSession.started_at))
        session_result = await db.execute(session_query)
        for raw_date, duration in session_result.all():
            stat_date = self._coerce_date(raw_date)
            if stat_date is None or stat_date > end_date:
                continue
            if stat_date == end_date or stat_date not in daily_durations:
                daily_durations[stat_date] = int(duration or 0)

        return daily_durations

    async def _sum_student_session_duration(
        self,
        db: AsyncSession,
        user_id: int,
        start_at: datetime | None,
        end_at: datetime | None,
    ) -> int:
        query = select(func.sum(LearningSession.effective_duration_seconds)).where(
            LearningSession.user_id == user_id,
        )
        if start_at is not None:
            query = query.where(LearningSession.started_at >= start_at)
        if end_at is not None:
            query = query.where(LearningSession.started_at < end_at)
        result = await db.execute(query)
        return int(result.scalar() or 0)

    def _coerce_date(self, value: object) -> date | None:
        if isinstance(value, date) and not isinstance(value, datetime):
            return value
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, str):
            return date.fromisoformat(value[:10])
        return None

    def _continuous_days(self, active_dates: list[date], today: date) -> int:
        active_set = set(active_dates)
        if not active_set:
            return 0
        current = today if today in active_set else max(active_set)
        days = 0
        while current in active_set:
            days += 1
            current -= timedelta(days=1)
        return days

    async def _get_learning_progress(self, db: AsyncSession, user_id: int, course_id: int) -> LearningProgress | None:
        result = await db.execute(
            select(LearningProgress).where(
                LearningProgress.user_id == user_id,
                LearningProgress.course_id == course_id,
            )
        )
        return result.scalar_one_or_none()

    async def _count_course_started_students(
        self,
        db: AsyncSession,
        course_id: int,
        start_at: datetime | None,
        end_at: datetime,
    ) -> int:
        first_started_subquery = (
            select(
                ResourceProgress.user_id.label("user_id"),
                func.min(ResourceProgress.created_at).label("first_started_at"),
            )
            .join(User, User.id == ResourceProgress.user_id)
            .where(User.role == "student", ResourceProgress.course_id == course_id)
            .group_by(ResourceProgress.user_id)
            .subquery()
        )
        query = select(func.count()).select_from(first_started_subquery).where(
            first_started_subquery.c.first_started_at < end_at
        )
        if start_at is not None:
            query = query.where(first_started_subquery.c.first_started_at >= start_at)
        result = await db.execute(query)
        return result.scalar() or 0

    async def _count_course_completed_students(
        self,
        db: AsyncSession,
        course_id: int,
        start_at: datetime | None,
        end_at: datetime,
    ) -> int:
        first_completed_subquery = (
            select(
                LearningProgress.user_id.label("user_id"),
                func.min(LearningProgress.completed_at).label("first_completed_at"),
            )
            .join(User, User.id == LearningProgress.user_id)
            .where(
                User.role == "student",
                LearningProgress.course_id == course_id,
                LearningProgress.completed_at.is_not(None),
            )
            .group_by(LearningProgress.user_id)
            .subquery()
        )
        query = select(func.count()).select_from(first_completed_subquery).where(
            first_completed_subquery.c.first_completed_at < end_at
        )
        if start_at is not None:
            query = query.where(first_completed_subquery.c.first_completed_at >= start_at)
        result = await db.execute(query)
        return result.scalar() or 0

    async def _avg_course_progress(self, db: AsyncSession, course_id: int) -> float:
        result = await db.execute(
            select(func.avg(LearningProgress.progress))
            .join(User, User.id == LearningProgress.user_id)
            .where(User.role == "student", LearningProgress.course_id == course_id)
        )
        return float(result.scalar() or 0.0)

    async def _course_first_started_in_range(
        self,
        db: AsyncSession,
        course_id: int,
        start_at: datetime,
        end_at: datetime,
    ) -> bool:
        result = await db.execute(
            select(func.min(ResourceProgress.created_at))
            .join(User, User.id == ResourceProgress.user_id)
            .where(User.role == "student", ResourceProgress.course_id == course_id)
        )
        first_started = self._as_comparable(result.scalar())
        return bool(first_started and start_at <= first_started < end_at)

    async def _course_first_completed_in_range(
        self,
        db: AsyncSession,
        course_id: int,
        start_at: datetime,
        end_at: datetime,
    ) -> bool:
        result = await db.execute(
            select(func.min(LearningProgress.completed_at))
            .join(User, User.id == LearningProgress.user_id)
            .where(
                User.role == "student",
                LearningProgress.course_id == course_id,
                LearningProgress.completed_at.is_not(None),
            )
        )
        first_completed = self._as_comparable(result.scalar())
        return bool(first_completed and start_at <= first_completed < end_at)


learning_statistics_service = LearningStatisticsService()
