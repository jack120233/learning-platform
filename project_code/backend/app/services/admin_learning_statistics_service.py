"""管理员平台学习统计服务。"""

from __future__ import annotations

from datetime import date, datetime, time, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenException, ValidationException
from app.models.category import Category
from app.models.course import Course
from app.models.learning import LearningSession
from app.models.learning_progress import LearningProgress
from app.models.user import User


class AdminLearningStatisticsService:
    """管理员平台学习统计读模型。"""

    def _ensure_admin(self, current_user: User) -> None:
        if current_user.role != "admin":
            raise ForbiddenException("仅管理员可访问学习统计")

    def _range_dates(self, trend_range: str, allow_all: bool = False) -> tuple[date | None, date]:
        allowed = {"7d", "30d"} | ({"all"} if allow_all else set())
        if trend_range not in allowed:
            raise ValidationException("range 参数无效")
        today = date.today()
        if trend_range == "all":
            return None, today
        days = 30 if trend_range == "30d" else 7
        return today - timedelta(days=days - 1), today

    def _date_bounds(self, start_date: date | None, end_date: date) -> tuple[datetime | None, datetime]:
        start_at = datetime.combine(start_date, time.min) if start_date else None
        end_at = datetime.combine(end_date + timedelta(days=1), time.min)
        return start_at, end_at

    def _apply_course_filters(
        self,
        query,
        category_id: int | None,
        teacher_id: int | None,
        course_status: str,
    ):
        if course_status not in {"all", "draft", "published", "archived"}:
            raise ValidationException("course_status 参数无效")
        if category_id is not None:
            query = query.where(Course.category_id == category_id)
        if teacher_id is not None:
            query = query.where(Course.teacher_id == teacher_id)
        if course_status != "all":
            query = query.where(Course.status == course_status)
        return query

    def _build_course_base_query(
        self,
        category_id: int | None,
        teacher_id: int | None,
        course_status: str,
    ):
        query = select(Course, User.username.label("teacher_username"), Category.name.label("category_name")).join(
            User, User.id == Course.teacher_id
        ).outerjoin(Category, Category.id == Course.category_id)
        return self._apply_course_filters(query, category_id, teacher_id, course_status)

    def _build_session_query(
        self,
        category_id: int | None,
        teacher_id: int | None,
        course_status: str,
    ):
        query = select(LearningSession).join(User, User.id == LearningSession.user_id).join(Course, Course.id == LearningSession.course_id).where(
            User.role == "student"
        )
        return self._apply_course_filters(query, category_id, teacher_id, course_status)

    def _apply_time_range(self, query, start_at: datetime | None, end_at: datetime):
        if start_at is not None:
            query = query.where(LearningSession.started_at >= start_at)
        return query.where(LearningSession.started_at < end_at)

    async def get_overview(
        self,
        db: AsyncSession,
        current_user: User,
        trend_range: str = "7d",
        category_id: int | None = None,
        teacher_id: int | None = None,
        course_status: str = "all",
    ) -> dict:
        """获取平台学习统计概览。"""
        self._ensure_admin(current_user)
        start_date, end_date = self._range_dates(trend_range, allow_all=True)
        start_at, end_at = self._date_bounds(start_date, end_date)

        session_base = self._build_session_query(category_id, teacher_id, course_status).subquery()

        total_student_query = select(func.count(func.distinct(session_base.c.user_id))).select_from(session_base)
        active_student_query = select(func.count(func.distinct(session_base.c.user_id))).select_from(session_base)
        total_duration_query = select(func.sum(session_base.c.effective_duration_seconds)).select_from(session_base)
        active_course_query = select(func.count(func.distinct(session_base.c.course_id))).select_from(session_base)
        if start_at is not None:
            active_student_query = active_student_query.where(session_base.c.started_at >= start_at)
            total_duration_query = total_duration_query.where(session_base.c.started_at >= start_at)
            active_course_query = active_course_query.where(session_base.c.started_at >= start_at)
        active_student_query = active_student_query.where(session_base.c.started_at < end_at)
        total_duration_query = total_duration_query.where(session_base.c.started_at < end_at)
        active_course_query = active_course_query.where(session_base.c.started_at < end_at)

        total_student_result = await db.execute(total_student_query)
        active_student_result = await db.execute(active_student_query)
        total_duration_result = await db.execute(total_duration_query)
        active_course_result = await db.execute(active_course_query)

        return {
            "range": trend_range,
            "total_student_count": int(total_student_result.scalar() or 0),
            "active_student_count": int(active_student_result.scalar() or 0),
            "total_duration_seconds": int(total_duration_result.scalar() or 0),
            "active_course_count": int(active_course_result.scalar() or 0),
            "new_started_course_count": await self._count_new_started_pairs(db, start_at, end_at, category_id, teacher_id, course_status),
            "new_completed_course_count": await self._count_new_completed_pairs(db, start_at, end_at, category_id, teacher_id, course_status),
        }

    async def get_trend(
        self,
        db: AsyncSession,
        current_user: User,
        trend_range: str = "7d",
        metric: str = "duration",
        category_id: int | None = None,
        teacher_id: int | None = None,
        course_status: str = "all",
    ) -> dict:
        """获取平台学习趋势，补齐缺失日期。"""
        self._ensure_admin(current_user)
        if metric not in {"duration", "active_students", "completed_courses"}:
            raise ValidationException("metric 参数无效")
        start_date, end_date = self._range_dates(trend_range, allow_all=False)
        assert start_date is not None
        start_at, end_at = self._date_bounds(start_date, end_date)

        values: dict[date, int] = {}
        if metric == "completed_courses":
            completed_query = (
                select(func.date(LearningProgress.completed_at), func.count())
                .join(User, User.id == LearningProgress.user_id)
                .join(Course, Course.id == LearningProgress.course_id)
                .where(
                    User.role == "student",
                    LearningProgress.completed_at >= start_at,
                    LearningProgress.completed_at < end_at,
                )
                .group_by(func.date(LearningProgress.completed_at))
            )
            completed_query = self._apply_course_filters(completed_query, category_id, teacher_id, course_status)
            result = await db.execute(completed_query)
        elif metric == "active_students":
            active_query = (
                select(func.date(LearningSession.started_at), func.count(func.distinct(LearningSession.user_id)))
                .join(User, User.id == LearningSession.user_id)
                .join(Course, Course.id == LearningSession.course_id)
                .where(User.role == "student")
            )
            active_query = self._apply_course_filters(active_query, category_id, teacher_id, course_status)
            active_query = self._apply_time_range(active_query, start_at, end_at).group_by(func.date(LearningSession.started_at))
            result = await db.execute(active_query)
        else:
            duration_query = (
                select(func.date(LearningSession.started_at), func.sum(LearningSession.effective_duration_seconds))
                .join(User, User.id == LearningSession.user_id)
                .join(Course, Course.id == LearningSession.course_id)
                .where(User.role == "student")
            )
            duration_query = self._apply_course_filters(duration_query, category_id, teacher_id, course_status)
            duration_query = self._apply_time_range(duration_query, start_at, end_at).group_by(func.date(LearningSession.started_at))
            result = await db.execute(duration_query)

        for raw_date, value in result.all():
            values[self._coerce_date(raw_date)] = int(value or 0)

        items = []
        current = start_date
        while current <= end_date:
            items.append({"date": current.isoformat(), "value": values.get(current, 0)})
            current += timedelta(days=1)
        return {"range": trend_range, "metric": metric, "items": items}

    async def get_popular_courses(
        self,
        db: AsyncSession,
        current_user: User,
        trend_range: str = "7d",
        category_id: int | None = None,
        teacher_id: int | None = None,
        course_status: str = "all",
        limit: int = 10,
    ) -> list[dict]:
        """获取热门课程列表。"""
        self._ensure_admin(current_user)
        start_date, end_date = self._range_dates(trend_range, allow_all=True)
        start_at, end_at = self._date_bounds(start_date, end_date)
        courses = await self._course_metric_rows(db, start_at, end_at, category_id, teacher_id, course_status)
        courses.sort(key=lambda item: (-item["active_student_count"], -item["total_duration_seconds"], item["course_id"]))
        return courses[:limit]

    async def get_low_completion_courses(
        self,
        db: AsyncSession,
        current_user: User,
        trend_range: str = "7d",
        category_id: int | None = None,
        teacher_id: int | None = None,
        course_status: str = "all",
        limit: int = 10,
    ) -> list[dict]:
        """获取低完成率课程列表。"""
        self._ensure_admin(current_user)
        start_date, end_date = self._range_dates(trend_range, allow_all=True)
        start_at, end_at = self._date_bounds(start_date, end_date)
        courses = await self._course_metric_rows(db, start_at, end_at, category_id, teacher_id, course_status)
        items = [
            {
                "course_id": item["course_id"],
                "course_title": item["course_title"],
                "teacher_id": item["teacher_id"],
                "teacher_username": item["teacher_username"],
                "started_student_count": item["started_student_count"],
                "completed_student_count": item["completed_student_count"],
                "completion_rate": item["completion_rate"],
                "avg_progress": item["avg_progress"],
                "recent_learn_at": item["recent_learn_at"],
            }
            for item in courses
            if item["started_student_count"] >= 5 and item["completion_rate"] < 30
        ]
        items.sort(key=lambda item: (item["completion_rate"], -item["started_student_count"], item["course_id"]))
        return items[:limit]

    async def _course_metric_rows(
        self,
        db: AsyncSession,
        start_at: datetime | None,
        end_at: datetime,
        category_id: int | None,
        teacher_id: int | None,
        course_status: str,
    ) -> list[dict]:
        course_query = self._build_course_base_query(category_id, teacher_id, course_status)
        course_result = await db.execute(course_query)
        rows = []
        for course, teacher_username, category_name in course_result.all():
            started_count = await self._count_started_students(db, course.id)
            completed_count = await self._count_completed_students(db, course.id)
            completion_rate = (completed_count / started_count * 100) if started_count else 0.0
            rows.append({
                "course_id": course.id,
                "course_title": course.title,
                "category_id": course.category_id,
                "category_name": category_name,
                "teacher_id": course.teacher_id,
                "teacher_username": teacher_username,
                "active_student_count": await self._count_active_students(db, course.id, start_at, end_at),
                "total_duration_seconds": await self._sum_duration(db, course.id, start_at, end_at),
                "completion_rate": round(completion_rate, 2),
                "recent_learn_at": await self._recent_learn_at(db, course.id),
                "started_student_count": started_count,
                "completed_student_count": completed_count,
                "avg_progress": round(await self._avg_progress(db, course.id), 2),
            })
        return rows

    async def _count_started_students(self, db: AsyncSession, course_id: int) -> int:
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
        return len(set(progress_result.scalars().all()) | set(session_result.scalars().all()))

    async def _count_active_students(self, db: AsyncSession, course_id: int, start_at: datetime | None, end_at: datetime) -> int:
        query = select(func.count(func.distinct(LearningSession.user_id))).join(User, User.id == LearningSession.user_id).where(
            User.role == "student",
            LearningSession.course_id == course_id,
            LearningSession.started_at < end_at,
        )
        if start_at is not None:
            query = query.where(LearningSession.started_at >= start_at)
        result = await db.execute(query)
        return int(result.scalar() or 0)

    async def _sum_duration(self, db: AsyncSession, course_id: int, start_at: datetime | None, end_at: datetime) -> int:
        query = select(func.sum(LearningSession.effective_duration_seconds)).join(User, User.id == LearningSession.user_id).where(
            User.role == "student",
            LearningSession.course_id == course_id,
            LearningSession.started_at < end_at,
        )
        if start_at is not None:
            query = query.where(LearningSession.started_at >= start_at)
        result = await db.execute(query)
        return int(result.scalar() or 0)

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

    async def _avg_progress(self, db: AsyncSession, course_id: int) -> float:
        result = await db.execute(
            select(func.avg(LearningProgress.progress))
            .join(User, User.id == LearningProgress.user_id)
            .where(User.role == "student", LearningProgress.course_id == course_id)
        )
        return float(result.scalar() or 0.0)

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

    async def _count_new_started_pairs(
        self,
        db: AsyncSession,
        start_at: datetime | None,
        end_at: datetime,
        category_id: int | None,
        teacher_id: int | None,
        course_status: str,
    ) -> int:
        first_started = (
            select(
                LearningSession.user_id.label("user_id"),
                LearningSession.course_id.label("course_id"),
                func.min(LearningSession.started_at).label("first_started_at"),
            )
            .join(User, User.id == LearningSession.user_id)
            .join(Course, Course.id == LearningSession.course_id)
            .where(User.role == "student")
        )
        first_started = self._apply_course_filters(first_started, category_id, teacher_id, course_status)
        subquery = first_started.group_by(LearningSession.user_id, LearningSession.course_id).subquery()
        query = select(func.count()).select_from(subquery).where(subquery.c.first_started_at < end_at)
        if start_at is not None:
            query = query.where(subquery.c.first_started_at >= start_at)
        result = await db.execute(query)
        return int(result.scalar() or 0)

    async def _count_new_completed_pairs(
        self,
        db: AsyncSession,
        start_at: datetime | None,
        end_at: datetime,
        category_id: int | None,
        teacher_id: int | None,
        course_status: str,
    ) -> int:
        query = (
            select(func.count())
            .select_from(LearningProgress)
            .join(User, User.id == LearningProgress.user_id)
            .join(Course, Course.id == LearningProgress.course_id)
            .where(
                User.role == "student",
                LearningProgress.completed_at.is_not(None),
                LearningProgress.completed_at < end_at,
            )
        )
        query = self._apply_course_filters(query, category_id, teacher_id, course_status)
        if start_at is not None:
            query = query.where(LearningProgress.completed_at >= start_at)
        result = await db.execute(query)
        return int(result.scalar() or 0)

    def _coerce_date(self, value: object) -> date:
        if isinstance(value, date) and not isinstance(value, datetime):
            return value
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, str):
            return date.fromisoformat(value[:10])
        raise ValueError("无法解析日期")


admin_learning_statistics_service = AdminLearningStatisticsService()
