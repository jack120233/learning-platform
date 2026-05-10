"""课程统计授权服务。"""

from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenException, NotFoundException, ValidationException
from app.models.course import Course, CourseTeacherAssignment
from app.models.user import User

STATISTICS_VIEWER = "statistics_viewer"


class CourseStatisticsAuthorizationService:
    """课程统计授权业务服务。"""

    def ensure_admin(self, current_user: User) -> None:
        if current_user.role != "admin":
            raise ForbiddenException("仅管理员可管理课程统计授权")

    async def _get_course(self, db: AsyncSession, course_id: int) -> Course:
        course = await db.get(Course, course_id)
        if not course:
            raise NotFoundException("课程不存在")
        return course

    async def list_authorizations(
        self,
        db: AsyncSession,
        course_id: int,
        current_user: User,
    ) -> list[dict]:
        """列出课程统计授权。"""
        self.ensure_admin(current_user)
        course = await self._get_course(db, course_id)
        rows = await self._fetch_authorization_rows(db, course.id, include_inactive=True)
        return [self._row_to_authorization(row) for row in rows if row[1].id != course.teacher_id]

    async def list_candidates(
        self,
        db: AsyncSession,
        course_id: int,
        current_user: User,
        keyword: str | None = None,
        page_size: int = 100,
    ) -> list[dict]:
        """列出可授权老师候选项。"""
        self.ensure_admin(current_user)
        course = await self._get_course(db, course_id)
        active_assignment_query = select(CourseTeacherAssignment.teacher_id).where(
            CourseTeacherAssignment.course_id == course.id,
            CourseTeacherAssignment.permission_type == STATISTICS_VIEWER,
            CourseTeacherAssignment.is_active.is_(True),
        )
        active_result = await db.execute(active_assignment_query)
        active_teacher_ids = set(active_result.scalars().all())

        query = select(User).where(
            User.role == "teacher",
            User.status == "active",
            User.id != course.teacher_id,
        )
        if keyword:
            query = query.where(User.username.ilike(f"%{keyword}%"))
        query = query.order_by(User.id.desc()).limit(page_size)
        result = await db.execute(query)
        return [
            {
                "teacher_id": teacher.id,
                "username": teacher.username,
                "authorized": teacher.id in active_teacher_ids,
            }
            for teacher in result.scalars().all()
        ]

    async def grant_authorizations(
        self,
        db: AsyncSession,
        course_id: int,
        teacher_ids: list[int],
        current_user: User,
    ) -> list[dict]:
        """授予课程统计查看权限，采用全量校验后幂等创建/激活。"""
        self.ensure_admin(current_user)
        course = await self._get_course(db, course_id)
        unique_teacher_ids = list(dict.fromkeys(teacher_ids))
        if not unique_teacher_ids:
            raise ValidationException("teacher_ids 不能为空")
        if course.teacher_id in unique_teacher_ids:
            raise ValidationException("课程负责人无需授权")

        teacher_result = await db.execute(select(User).where(User.id.in_(unique_teacher_ids)))
        teachers = {teacher.id: teacher for teacher in teacher_result.scalars().all()}
        invalid_ids = [teacher_id for teacher_id in unique_teacher_ids if teacher_id not in teachers]
        ineligible_ids = [
            teacher_id
            for teacher_id, teacher in teachers.items()
            if teacher.role != "teacher" or teacher.status != "active"
        ]
        if invalid_ids or ineligible_ids:
            raise ValidationException("存在不可授权的老师", details={
                "invalid_teacher_ids": invalid_ids,
                "ineligible_teacher_ids": sorted(ineligible_ids),
            })

        existing_result = await db.execute(
            select(CourseTeacherAssignment).where(
                CourseTeacherAssignment.course_id == course.id,
                CourseTeacherAssignment.teacher_id.in_(unique_teacher_ids),
                CourseTeacherAssignment.permission_type == STATISTICS_VIEWER,
            )
        )
        existing_by_teacher_id = {item.teacher_id: item for item in existing_result.scalars().all()}
        now = datetime.now(timezone.utc)
        for teacher_id in unique_teacher_ids:
            assignment = existing_by_teacher_id.get(teacher_id)
            if assignment:
                assignment.assigned_by = current_user.id
                assignment.assigned_at = now
                assignment.revoked_at = None
                assignment.is_active = True
            else:
                db.add(CourseTeacherAssignment(
                    course_id=course.id,
                    teacher_id=teacher_id,
                    permission_type=STATISTICS_VIEWER,
                    assigned_by=current_user.id,
                    assigned_at=now,
                    revoked_at=None,
                    is_active=True,
                ))
        await db.flush()
        rows = await self._fetch_authorization_rows(db, course.id, include_inactive=False)
        return [self._row_to_authorization(row) for row in rows]

    async def revoke_authorization(
        self,
        db: AsyncSession,
        course_id: int,
        teacher_id: int,
        current_user: User,
    ) -> None:
        """撤销课程统计查看权限。"""
        self.ensure_admin(current_user)
        course = await self._get_course(db, course_id)
        teacher = await db.get(User, teacher_id)
        if not teacher or teacher.role != "teacher":
            raise NotFoundException("老师不存在")
        if teacher.id == course.teacher_id:
            raise ValidationException("课程负责人无需撤销统计授权")

        result = await db.execute(
            select(CourseTeacherAssignment).where(
                CourseTeacherAssignment.course_id == course.id,
                CourseTeacherAssignment.teacher_id == teacher_id,
                CourseTeacherAssignment.permission_type == STATISTICS_VIEWER,
                CourseTeacherAssignment.is_active.is_(True),
            )
        )
        assignment = result.scalar_one_or_none()
        if assignment:
            assignment.is_active = False
            assignment.revoked_at = datetime.now(timezone.utc)
            await db.flush()

    async def has_statistics_access(self, db: AsyncSession, course_id: int, teacher: User) -> bool:
        """判断老师是否可查看课程统计。"""
        if teacher.role != "teacher":
            return False
        course = await self._get_course(db, course_id)
        if course.teacher_id == teacher.id:
            return True
        result = await db.execute(
            select(func.count()).select_from(CourseTeacherAssignment).where(
                CourseTeacherAssignment.course_id == course.id,
                CourseTeacherAssignment.teacher_id == teacher.id,
                CourseTeacherAssignment.permission_type == STATISTICS_VIEWER,
                CourseTeacherAssignment.is_active.is_(True),
            )
        )
        return (result.scalar() or 0) > 0

    async def ensure_statistics_access(self, db: AsyncSession, course_id: int, teacher: User) -> Course:
        """确保老师可查看课程统计并返回课程。"""
        if teacher.role != "teacher":
            raise ForbiddenException("仅讲师可访问课程统计")
        course = await self._get_course(db, course_id)
        if course.teacher_id == teacher.id:
            return course
        result = await db.execute(
            select(func.count()).select_from(CourseTeacherAssignment).where(
                CourseTeacherAssignment.course_id == course.id,
                CourseTeacherAssignment.teacher_id == teacher.id,
                CourseTeacherAssignment.permission_type == STATISTICS_VIEWER,
                CourseTeacherAssignment.is_active.is_(True),
            )
        )
        if not (result.scalar() or 0):
            raise ForbiddenException("无权查看此课程统计")
        return course

    async def _fetch_authorization_rows(
        self,
        db: AsyncSession,
        course_id: int,
        include_inactive: bool,
    ) -> list[tuple[CourseTeacherAssignment, User]]:
        query = (
            select(CourseTeacherAssignment, User)
            .join(User, User.id == CourseTeacherAssignment.teacher_id)
            .where(
                CourseTeacherAssignment.course_id == course_id,
                CourseTeacherAssignment.permission_type == STATISTICS_VIEWER,
            )
        )
        if not include_inactive:
            query = query.where(CourseTeacherAssignment.is_active.is_(True))
        query = query.order_by(CourseTeacherAssignment.is_active.desc(), CourseTeacherAssignment.assigned_at.desc())
        result = await db.execute(query)
        return list(result.all())

    def _row_to_authorization(self, row: tuple[CourseTeacherAssignment, User]) -> dict:
        assignment, teacher = row
        return {
            "teacher_id": teacher.id,
            "username": teacher.username,
            "assigned_by": assignment.assigned_by,
            "assigned_at": assignment.assigned_at,
            "is_active": assignment.is_active,
            "revoked_at": assignment.revoked_at,
        }


course_statistics_authorization_service = CourseStatisticsAuthorizationService()
