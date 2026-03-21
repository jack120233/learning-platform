"""用户管理服务模块

提供用户信息管理、讲师审核、管理员申请等业务逻辑。
"""

import json
from datetime import datetime, timezone
from typing import Literal

from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    AuthenticationException,
    ConflictException,
    ForbiddenException,
    NotFoundException,
    ValidationException,
)
from app.core.security import hash_password, verify_password
from app.models.user import User
from app.models.teacher_audit import TeacherAudit
from app.models.admin_application import AdminApplication
from app.models.learning_progress import LearningProgress
from app.schemas.user import (
    AdminApplicationCreate,
    AdminApplicationReview,
    TeacherAuditApply,
    TeacherAuditReview,
    UserProfileUpdate,
    UserStatusUpdate,
)


class UserService:
    """用户管理服务类"""

    async def get_current_user(
        self,
        db: AsyncSession,
        user_id: int,
    ) -> User:
        """获取当前用户信息

        Args:
            db: 数据库会话
            user_id: 用户ID

        Returns:
            用户对象

        Raises:
            NotFoundException: 用户不存在
        """
        user = await db.get(User, user_id)
        if not user:
            raise NotFoundException("用户不存在")
        return user

    async def update_profile(
        self,
        db: AsyncSession,
        user_id: int,
        data: UserProfileUpdate,
    ) -> User:
        """更新个人信息

        Args:
            db: 数据库会话
            user_id: 用户ID
            data: 更新数据

        Returns:
            更新后的用户

        Raises:
            NotFoundException: 用户不存在
            ConflictException: 手机号已被使用
        """
        user = await db.get(User, user_id)
        if not user:
            raise NotFoundException("用户不存在")

        # 检查手机号是否已被其他用户使用
        if data.phone and data.phone != user.phone:
            existing = await self._get_user_by_phone(db, data.phone)
            if existing:
                raise ConflictException("手机号已被使用")

        # 更新属性
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(user, key, value)

        await db.flush()
        return user

    async def change_password(
        self,
        db: AsyncSession,
        user_id: int,
        old_password: str,
        new_password: str,
    ) -> None:
        """修改密码

        Args:
            db: 数据库会话
            user_id: 用户ID
            old_password: 原密码
            new_password: 新密码

        Raises:
            NotFoundException: 用户不存在
            AuthenticationException: 原密码错误
        """
        user = await db.get(User, user_id)
        if not user:
            raise NotFoundException("用户不存在")

        # 验证原密码
        if not verify_password(old_password, user.password_hash):
            raise AuthenticationException("原密码错误")

        # 更新密码
        user.password_hash = hash_password(new_password)

    async def get_learning_records(
        self,
        db: AsyncSession,
        user_id: int,
        page: int = 1,
        page_size: int = 10,
    ) -> tuple[list[LearningProgress], int]:
        """获取学习记录

        Args:
            db: 数据库会话
            user_id: 用户ID
            page: 页码
            page_size: 每页数量

        Returns:
            学习记录列表和总数
        """
        query = select(LearningProgress).where(
            LearningProgress.user_id == user_id
        )

        # 获取总数
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        # 分页查询
        query = query.order_by(LearningProgress.updated_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await db.execute(query)
        records = list(result.scalars().all())

        return records, total

    async def get_user_list(
        self,
        db: AsyncSession,
        keyword: str | None = None,
        role: str | None = None,
        status: str | None = None,
        page: int = 1,
        page_size: int = 10,
    ) -> tuple[list[User], int]:
        """获取用户列表（管理员）

        Args:
            db: 数据库会话
            keyword: 搜索关键词
            role: 角色筛选
            status: 状态筛选
            page: 页码
            page_size: 每页数量

        Returns:
            用户列表和总数
        """
        query = select(User)

        if keyword:
            query = query.where(
                or_(
                    User.username.ilike(f"%{keyword}%"),
                    User.email.ilike(f"%{keyword}%"),
                    User.nickname.ilike(f"%{keyword}%"),
                )
            )
        if role:
            query = query.where(User.role == role)
        if status:
            query = query.where(User.status == status)

        # 获取总数
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        # 分页查询
        query = query.order_by(User.id.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await db.execute(query)
        users = list(result.scalars().all())

        return users, total

    async def update_user_status(
        self,
        db: AsyncSession,
        user_id: int,
        data: UserStatusUpdate,
        operator_id: int,
    ) -> User:
        """更新用户状态（管理员）

        Args:
            db: 数据库会话
            user_id: 用户ID
            data: 状态数据
            operator_id: 操作人ID

        Returns:
            更新后的用户

        Raises:
            NotFoundException: 用户不存在
            ForbiddenException: 不能禁用自己或管理员
        """
        user = await db.get(User, user_id)
        if not user:
            raise NotFoundException("用户不存在")

        # 不能禁用自己
        if user_id == operator_id:
            raise ForbiddenException("不能修改自己的状态")

        # 不能禁用其他管理员
        operator = await db.get(User, operator_id)
        if operator and user.role == "admin" and operator.role != "admin":
            raise ForbiddenException("无权操作管理员账户")

        user.status = data.status
        await db.flush()
        return user

    async def delete_user(
        self,
        db: AsyncSession,
        user_id: int,
        operator_id: int,
    ) -> None:
        """删除用户（管理员）

        Args:
            db: 数据库会话
            user_id: 用户ID
            operator_id: 操作人ID

        Raises:
            NotFoundException: 用户不存在
            ForbiddenException: 不能删除自己或管理员
        """
        user = await db.get(User, user_id)
        if not user:
            raise NotFoundException("用户不存在")

        # 不能删除自己
        if user_id == operator_id:
            raise ForbiddenException("不能删除自己的账户")

        # 不能删除其他管理员
        operator = await db.get(User, operator_id)
        if operator and user.role == "admin":
            raise ForbiddenException("不能删除管理员账户")

        await db.delete(user)

    async def _get_user_by_phone(
        self,
        db: AsyncSession,
        phone: str,
    ) -> User | None:
        """通过手机号获取用户"""
        result = await db.execute(
            select(User).where(User.phone == phone)
        )
        return result.scalar_one_or_none()


class TeacherAuditService:
    """讲师审核服务类"""

    async def apply(
        self,
        db: AsyncSession,
        user_id: int,
        data: TeacherAuditApply,
    ) -> TeacherAudit:
        """申请成为讲师

        Args:
            db: 数据库会话
            user_id: 用户ID
            data: 申请数据

        Returns:
            申请记录

        Raises:
            ConflictException: 已有待审核的申请或已是讲师
        """
        user = await db.get(User, user_id)
        if not user:
            raise NotFoundException("用户不存在")

        # 检查是否已是讲师
        if user.role == "teacher":
            raise ConflictException("您已是讲师")

        # 检查是否有待审核的申请
        pending = await self._get_pending_application(db, user_id)
        if pending:
            raise ConflictException("您有待审核的申请，请等待审核结果")

        # 创建申请记录
        audit = TeacherAudit(
            user_id=user_id,
            real_name=data.real_name,
            phone=data.phone,
            email=data.email,
            organization=data.organization,
            title=data.title,
            introduction=data.introduction,
            certificate_urls=json.dumps(data.certificate_urls) if data.certificate_urls else None,
        )
        db.add(audit)
        await db.flush()
        return audit

    async def get_list(
        self,
        db: AsyncSession,
        status: str | None = None,
        page: int = 1,
        page_size: int = 10,
    ) -> tuple[list[TeacherAudit], int]:
        """获取审核列表（管理员）

        Args:
            db: 数据库会话
            status: 状态筛选
            page: 页码
            page_size: 每页数量

        Returns:
            审核列表和总数
        """
        query = select(TeacherAudit)

        if status:
            query = query.where(TeacherAudit.status == status)

        # 获取总数
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        # 分页查询
        query = query.order_by(TeacherAudit.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await db.execute(query)
        audits = list(result.scalars().all())

        return audits, total

    async def review(
        self,
        db: AsyncSession,
        audit_id: int,
        data: TeacherAuditReview,
        reviewer_id: int,
    ) -> TeacherAudit:
        """审核讲师申请（管理员）

        Args:
            db: 数据库会话
            audit_id: 审核ID
            data: 审核数据
            reviewer_id: 审核人ID

        Returns:
            审核记录

        Raises:
            NotFoundException: 申请不存在
            ValidationException: 申请已审核
        """
        audit = await db.get(TeacherAudit, audit_id)
        if not audit:
            raise NotFoundException("申请不存在")

        if audit.status != "pending":
            raise ValidationException("该申请已审核")

        # 更新审核状态
        audit.status = "approved" if data.approve else "rejected"
        audit.reviewer_id = reviewer_id
        audit.review_comment = data.comment
        audit.reviewed_at = datetime.now(timezone.utc)

        # 如果通过，更新用户角色
        if data.approve:
            user = await db.get(User, audit.user_id)
            if user:
                user.role = "teacher"

        await db.flush()
        return audit

    async def _get_pending_application(
        self,
        db: AsyncSession,
        user_id: int,
    ) -> TeacherAudit | None:
        """获取用户待审核的申请"""
        result = await db.execute(
            select(TeacherAudit).where(
                and_(
                    TeacherAudit.user_id == user_id,
                    TeacherAudit.status == "pending",
                )
            )
        )
        return result.scalar_one_or_none()


class AdminApplicationService:
    """管理员申请服务类"""

    async def apply(
        self,
        db: AsyncSession,
        user_id: int,
        data: AdminApplicationCreate,
    ) -> AdminApplication:
        """申请成为管理员

        Args:
            db: 数据库会话
            user_id: 用户ID
            data: 申请数据

        Returns:
            申请记录

        Raises:
            ConflictException: 已有待审核的申请或已是管理员
        """
        user = await db.get(User, user_id)
        if not user:
            raise NotFoundException("用户不存在")

        # 检查是否已是管理员
        if user.role == "admin":
            raise ConflictException("您已是管理员")

        # 检查是否有待审核的申请
        pending = await self._get_pending_application(db, user_id)
        if pending:
            raise ConflictException("您有待审核的申请，请等待审核结果")

        # 创建申请记录
        application = AdminApplication(
            user_id=user_id,
            reason=data.reason,
            department=data.department,
        )
        db.add(application)
        await db.flush()
        return application

    async def get_list(
        self,
        db: AsyncSession,
        status: str | None = None,
        page: int = 1,
        page_size: int = 10,
    ) -> tuple[list[AdminApplication], int]:
        """获取申请列表（管理员）

        Args:
            db: 数据库会话
            status: 状态筛选
            page: 页码
            page_size: 每页数量

        Returns:
            申请列表和总数
        """
        query = select(AdminApplication)

        if status:
            query = query.where(AdminApplication.status == status)

        # 获取总数
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        # 分页查询
        query = query.order_by(AdminApplication.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await db.execute(query)
        applications = list(result.scalars().all())

        return applications, total

    async def review(
        self,
        db: AsyncSession,
        application_id: int,
        data: AdminApplicationReview,
        reviewer_id: int,
    ) -> AdminApplication:
        """审核管理员申请（管理员）

        Args:
            db: 数据库会话
            application_id: 申请ID
            data: 审核数据
            reviewer_id: 审核人ID

        Returns:
            申请记录

        Raises:
            NotFoundException: 申请不存在
            ValidationException: 申请已审核
        """
        application = await db.get(AdminApplication, application_id)
        if not application:
            raise NotFoundException("申请不存在")

        if application.status != "pending":
            raise ValidationException("该申请已审核")

        # 更新审核状态
        application.status = "approved" if data.approve else "rejected"
        application.reviewer_id = reviewer_id
        application.review_comment = data.comment
        application.reviewed_at = datetime.now(timezone.utc)

        # 如果通过，更新用户角色
        if data.approve:
            user = await db.get(User, application.user_id)
            if user:
                user.role = "admin"

        await db.flush()
        return application

    async def _get_pending_application(
        self,
        db: AsyncSession,
        user_id: int,
    ) -> AdminApplication | None:
        """获取用户待审核的申请"""
        result = await db.execute(
            select(AdminApplication).where(
                and_(
                    AdminApplication.user_id == user_id,
                    AdminApplication.status == "pending",
                )
            )
        )
        return result.scalar_one_or_none()


# 创建全局服务实例
user_service = UserService()
teacher_audit_service = TeacherAuditService()
admin_application_service = AdminApplicationService()