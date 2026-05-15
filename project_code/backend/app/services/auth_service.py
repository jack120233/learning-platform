"""认证服务模块

提供用户认证相关的业务逻辑。
"""

import hashlib
import random
import string
from datetime import datetime, timedelta, timezone
from typing import Literal

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.exceptions import (
    AccountLockedException,
    AuthenticationException,
    ConflictException,
    NotFoundException,
    ValidationException,
)
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.captcha import CaptchaRecord
from app.models.email_code import EmailCode
from app.models.refresh_token import RefreshToken
from app.models.teacher_audit import TeacherAudit
from app.models.user import User
from app.schemas.auth import (
    CaptchaResponse,
    LoginRequest,
    LoginResponse,
    RegisterRequest,
    ResetPasswordRequest,
    SendEmailCodeRequest,
    TokenResponse,
    UserResponse,
)


class AuthService:
    """认证服务类

    提供用户注册、登录、令牌管理等功能。
    """

    async def register(
        self,
        db: AsyncSession,
        request: RegisterRequest,
    ) -> LoginResponse:
        """用户注册。"""
        existing_user = await self._get_user_by_username(db, request.username)
        if existing_user:
            raise ConflictException("用户名已被使用")

        existing_email = await self._get_user_by_email(db, request.email)
        if existing_email:
            raise ConflictException("邮箱已被注册")

        if request.phone:
            existing_phone = await self._get_user_by_phone(db, request.phone)
            if existing_phone:
                raise ConflictException("手机号已被使用")

        status = "pending" if request.role == "teacher" else "active"
        user = User(
            username=request.username,
            email=str(request.email).lower(),
            phone=request.phone,
            password_hash=hash_password(request.password),
            role=request.role,
            status=status,
        )

        db.add(user)
        await db.flush()
        await db.refresh(user)

        if request.role == "teacher":
            audit = TeacherAudit(
                user_id=user.id,
                real_name=(request.real_name or request.username).strip(),
                phone=request.phone or "未填写",
                email=str(request.email).lower(),
                status="pending",
            )
            db.add(audit)
            await db.flush()

        return await self._create_login_response(db, user)

    async def login(
        self,
        db: AsyncSession,
        request: LoginRequest,
        device_info: str | None = None,
        ip_address: str | None = None,
    ) -> LoginResponse:
        """用户登录

        Args:
            db: 数据库会话
            request: 登录请求
            device_info: 设备信息
            ip_address: IP地址

        Returns:
            登录响应

        Raises:
            ValidationException: 验证码无效
            AccountLockedException: 账户被锁定
            AuthenticationException: 认证失败
        """
        # 验证图形验证码
        # TODO: 暂时注释掉图形验证码校验，后续单独测试
        # await self._verify_captcha(db, request.captcha_key, request.captcha_text)

        # 查找用户
        user = await self._get_user_by_username_or_email(db, request.username)
        if not user:
            raise AuthenticationException("用户名或密码错误")

        # 检查账户是否被锁定
        if user.is_locked:
            remaining = (user.locked_until - datetime.utcnow()).seconds // 60
            raise AccountLockedException(f"账户已被锁定，请{remaining}分钟后再试")

        # 验证密码
        if not verify_password(request.password, user.password_hash):
            await self._handle_login_failure(db, user)
            raise AuthenticationException("用户名或密码错误")

        # 检查账户状态：待审核老师允许登录，但权限端按学生处理
        if user.status != "active" and not (user.role == "teacher" and user.status == "pending"):
            raise AuthenticationException("账户已被禁用")

        return await self._create_login_response(
            db,
            user,
            remember_me=request.remember_me,
            device_info=device_info,
            ip_address=ip_address,
        )

    async def logout(
        self,
        db: AsyncSession,
        user_id: int,
        refresh_token: str | None = None,
    ) -> None:
        """用户登出

        Args:
            db: 数据库会话
            user_id: 用户ID
            refresh_token: 刷新令牌（可选）
        """
        if refresh_token:
            # 撤销指定的刷新令牌
            result = await db.execute(
                select(RefreshToken).where(
                    and_(
                        RefreshToken.token == refresh_token,
                        RefreshToken.user_id == user_id,
                    )
                )
            )
            token_record = result.scalar_one_or_none()
            if token_record:
                token_record.is_revoked = True
        else:
            # 撤销该用户所有刷新令牌
            result = await db.execute(
                select(RefreshToken).where(RefreshToken.user_id == user_id)
            )
            tokens = result.scalars().all()
            for token in tokens:
                token.is_revoked = True

    async def refresh_token(
        self,
        db: AsyncSession,
        refresh_token: str,
    ) -> TokenResponse:
        """刷新访问令牌

        Args:
            db: 数据库会话
            refresh_token: 刷新令牌

        Returns:
            新的令牌响应

        Raises:
            AuthenticationException: 令牌无效或已过期
        """
        # 验证刷新令牌
        payload = decode_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            raise AuthenticationException("无效的刷新令牌")

        user_id = payload.get("sub")
        if not user_id:
            raise AuthenticationException("令牌格式错误")

        # 检查数据库中的令牌状态
        result = await db.execute(
            select(RefreshToken).where(RefreshToken.token == refresh_token)
        )
        token_record = result.scalar_one_or_none()

        if not token_record or token_record.is_revoked:
            raise AuthenticationException("刷新令牌已被撤销")

        if token_record.is_expired:
            raise AuthenticationException("刷新令牌已过期")

        # 检查用户状态：待审核老师允许刷新令牌，但权限端按学生处理
        user = await db.get(User, int(user_id))
        if not user or (user.status != "active" and not (user.role == "teacher" and user.status == "pending")):
            raise AuthenticationException("用户不存在或已被禁用")

        # 生成新的访问令牌
        access_token = create_access_token(subject=user.id)

        return TokenResponse(
            access_token=access_token,
            expires_in=settings.access_token_expire_minutes * 60,
        )

    async def get_captcha(self, db: AsyncSession) -> CaptchaResponse:
        """获取图形验证码

        Args:
            db: 数据库会话

        Returns:
            验证码响应
        """
        # 生成随机验证码文本
        captcha_text = "".join(
            random.choices(string.ascii_uppercase + string.digits, k=4)
        )

        # 生成唯一标识
        captcha_key = hashlib.md5(
            f"{captcha_text}{datetime.utcnow().timestamp()}".encode()
        ).hexdigest()

        # 生成简单的 Base64 图片（实际项目应使用图形库生成）
        # 这里使用简单的文本占位，实际项目需要使用 PIL 等库生成图片
        image_base64 = self._generate_captcha_image(captcha_text)

        # 计算过期时间
        expires_at = datetime.now(timezone.utc) + timedelta(
            minutes=settings.captcha_expire_minutes
        )

        # 保存验证码记录
        captcha_record = CaptchaRecord(
            captcha_key=captcha_key,
            captcha_text=captcha_text.lower(),
            image_base64=image_base64,
            expires_at=expires_at,
        )
        db.add(captcha_record)

        return CaptchaResponse(
            captcha_key=captcha_key,
            captcha_image=image_base64,
        )

    async def send_email_code(
        self,
        db: AsyncSession,
        request: SendEmailCodeRequest,
    ) -> None:
        """发送邮箱验证码

        Args:
            db: 数据库会话
            request: 发送请求

        Raises:
            ValidationException: 验证码无效或发送频率过高
            ConflictException: 邮箱已注册（注册场景）
        """
        # 验证图形验证码
        # TODO: 暂时注释掉图形验证码校验，后续单独测试
        # await self._verify_captcha(db, request.captcha_key, request.captcha_text)

        # 注册场景检查邮箱是否已存在
        if request.purpose == "register":
            existing = await self._get_user_by_email(db, request.email)
            if existing:
                raise ConflictException("邮箱已被注册")

        # 密码重置场景检查邮箱是否存在
        if request.purpose == "reset_password":
            existing = await self._get_user_by_email(db, request.email)
            if not existing:
                raise NotFoundException("邮箱未注册")

        # 检查发送频率（1分钟内不能重复发送）
        recent_code = await self._get_recent_email_code(db, request.email)
        if recent_code:
            raise ValidationException("验证码发送过于频繁，请稍后再试")

        # 生成验证码
        code = "".join(random.choices(string.digits, k=6))

        # 计算过期时间
        expires_at = datetime.now(timezone.utc) + timedelta(
            minutes=settings.email_code_expire_minutes
        )

        # 保存验证码
        email_code = EmailCode(
            email=request.email,
            code=code,
            purpose=request.purpose,
            expires_at=expires_at,
        )
        db.add(email_code)

        # 实际项目应在这里发送邮件
        # await send_email(request.email, code, request.purpose)
        print(f"[邮件发送] 收件人: {request.email}, 验证码: {code}, 用途: {request.purpose}")

    async def reset_password(
        self,
        db: AsyncSession,
        request: ResetPasswordRequest,
    ) -> None:
        """重置密码

        Args:
            db: 数据库会话
            request: 重置请求

        Raises:
            ValidationException: 验证码无效
            NotFoundException: 用户不存在
        """
        # 验证邮箱验证码
        email_code = await self._get_valid_email_code(
            db, request.email, "reset_password"
        )
        if not email_code:
            raise ValidationException("邮箱验证码无效或已过期")

        # 查找用户
        user = await self._get_user_by_email(db, request.email)
        if not user:
            raise NotFoundException("用户不存在")

        # 更新密码
        user.password_hash = hash_password(request.new_password)
        user.login_fail_count = 0
        user.locked_until = None

        # 标记验证码为已使用
        email_code.is_used = True

        # 撤销所有刷新令牌
        result = await db.execute(
            select(RefreshToken).where(RefreshToken.user_id == user.id)
        )
        tokens = result.scalars().all()
        for token in tokens:
            token.is_revoked = True

    # ==================== 私有方法 ====================

    async def _create_login_response(
        self,
        db: AsyncSession,
        user: User,
        remember_me: bool = False,
        device_info: str | None = None,
        ip_address: str | None = None,
    ) -> LoginResponse:
        """生成登录令牌响应并记录刷新令牌。"""
        user.login_fail_count = 0
        user.last_login_at = datetime.now(timezone.utc)

        access_token = create_access_token(subject=user.id)
        refresh_token = create_refresh_token(
            subject=user.id,
            remember_me=remember_me,
        )

        days = (
            settings.remember_me_expire_days
            if remember_me
            else settings.refresh_token_expire_days
        )
        token_record = RefreshToken(
            token=refresh_token,
            user_id=user.id,
            expires_at=datetime.now(timezone.utc) + timedelta(days=days),
            device_info=device_info,
            ip_address=ip_address,
        )
        db.add(token_record)
        await db.flush()

        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.access_token_expire_minutes * 60,
            user=UserResponse.model_validate(user),
        )

    async def _verify_captcha(
        self,
        db: AsyncSession,
        captcha_key: str,
        captcha_text: str,
    ) -> None:
        """验证图形验证码"""
        result = await db.execute(
            select(CaptchaRecord).where(CaptchaRecord.captcha_key == captcha_key)
        )
        captcha = result.scalar_one_or_none()

        if not captcha:
            raise ValidationException("验证码不存在")

        if captcha.is_expired:
            raise ValidationException("验证码已过期")

        if captcha.captcha_text != captcha_text.lower():
            raise ValidationException("验证码错误")

    async def _get_user_by_username(
        self,
        db: AsyncSession,
        username: str,
    ) -> User | None:
        """通过用户名获取用户"""
        result = await db.execute(
            select(User).where(User.username == username.lower())
        )
        return result.scalar_one_or_none()

    async def _get_user_by_email(
        self,
        db: AsyncSession,
        email: str,
    ) -> User | None:
        """通过邮箱获取用户"""
        result = await db.execute(
            select(User).where(User.email == email.lower())
        )
        return result.scalar_one_or_none()

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

    async def _get_user_by_username_or_email(
        self,
        db: AsyncSession,
        username: str,
    ) -> User | None:
        """通过用户名或邮箱获取用户"""
        result = await db.execute(
            select(User).where(
                (User.username == username.lower()) | (User.email == username.lower())
            )
        )
        return result.scalar_one_or_none()

    async def _get_valid_email_code(
        self,
        db: AsyncSession,
        email: str,
        purpose: str,
    ) -> EmailCode | None:
        """获取有效的邮箱验证码"""
        result = await db.execute(
            select(EmailCode).where(
                and_(
                    EmailCode.email == email.lower(),
                    EmailCode.purpose == purpose,
                    EmailCode.is_used == False,
                    EmailCode.expires_at > datetime.now(timezone.utc),
                )
            )
        )
        return result.scalar_one_or_none()

    async def _get_recent_email_code(
        self,
        db: AsyncSession,
        email: str,
    ) -> EmailCode | None:
        """获取最近发送的邮箱验证码（1分钟内）"""
        one_minute_ago = datetime.now(timezone.utc) - timedelta(minutes=1)
        result = await db.execute(
            select(EmailCode).where(
                and_(
                    EmailCode.email == email.lower(),
                    EmailCode.created_at > one_minute_ago,
                )
            )
        )
        return result.scalar_one_or_none()

    async def _handle_login_failure(
        self,
        db: AsyncSession,
        user: User,
    ) -> None:
        """处理登录失败"""
        user.login_fail_count += 1

        if user.login_fail_count >= settings.login_max_attempts:
            user.locked_until = datetime.now(timezone.utc) + timedelta(
                minutes=settings.login_lockout_minutes
            )

    def _generate_captcha_image(self, text: str) -> str:
        """生成验证码图片的 Base64 编码

        实际项目应使用 PIL 等库生成真实图片。
        这里返回一个简单的 SVG 格式图片作为示例。
        """
        import base64

        # 生成简单的 SVG 图片
        svg_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg width="120" height="40" xmlns="http://www.w3.org/2000/svg">
    <rect width="100%" height="100%" fill="#f0f0f0"/>
    <text x="50%" y="50%" dominant-baseline="middle" text-anchor="middle"
          font-family="Arial" font-size="24" font-weight="bold" fill="#333">
        {text}
    </text>
</svg>'''

        # Base64 编码
        return f"data:image/svg+xml;base64,{base64.b64encode(svg_content.encode()).decode()}"


# 创建全局服务实例
auth_service = AuthService()
