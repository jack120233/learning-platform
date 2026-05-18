"""认证 API 路由

提供用户认证相关的 API 接口。
"""

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import DBSession, CurrentUserId
from app.schemas.auth import (
    CaptchaResponse,
    LoginRequest,
    LoginResponse,
    RefreshTokenRequest,
    RegisterRequest,
    ResetPasswordRequest,
    SendEmailCodeRequest,
    TokenResponse,
)
from app.schemas.common import ApiResponse
from app.services.auth_service import auth_service

router = APIRouter(prefix="/auth", tags=["用户认证"])


@router.post(
    "/register",
    response_model=ApiResponse[LoginResponse],
    summary="用户注册",
    description="使用真实姓名、邮箱和密码注册新用户账户",
)
async def register(
    request: RegisterRequest,
    db: DBSession,
) -> ApiResponse[LoginResponse]:
    """用户注册接口

    Args:
        request: 注册请求数据
        db: 数据库会话

    Returns:
        注册成功后的登录令牌和用户信息
    """
    response = await auth_service.register(db, request)
    return ApiResponse.success(
        data=response,
        message="注册成功",
    )


@router.post(
    "/login",
    response_model=ApiResponse[LoginResponse],
    summary="用户登录",
    description="使用用户名/邮箱和密码登录系统",
)
async def login(
    request: LoginRequest,
    db: DBSession,
    http_request: Request,
) -> ApiResponse[LoginResponse]:
    """用户登录接口

    Args:
        request: 登录请求数据
        db: 数据库会话
        http_request: HTTP 请求对象

    Returns:
        登录响应，包含访问令牌和用户信息
    """
    # 获取设备信息和 IP 地址
    device_info = http_request.headers.get("user-agent")
    ip_address = http_request.client.host if http_request.client else None

    response = await auth_service.login(
        db,
        request,
        device_info=device_info,
        ip_address=ip_address,
    )

    return ApiResponse.success(
        data=response,
        message="登录成功",
    )


@router.post(
    "/logout",
    response_model=ApiResponse[None],
    summary="退出登录",
    description="退出当前登录状态，撤销刷新令牌",
)
async def logout(
    db: DBSession,
    user_id: CurrentUserId,
    refresh_token: str | None = None,
) -> ApiResponse[None]:
    """退出登录接口

    Args:
        db: 数据库会话
        user_id: 当前用户 ID
        refresh_token: 要撤销的刷新令牌（可选）

    Returns:
        成功响应
    """
    await auth_service.logout(db, user_id, refresh_token)
    return ApiResponse.success(message="退出成功")


@router.post(
    "/refresh",
    response_model=ApiResponse[TokenResponse],
    summary="刷新令牌",
    description="使用刷新令牌获取新的访问令牌",
)
async def refresh_token(
    request: RefreshTokenRequest,
    db: DBSession,
) -> ApiResponse[TokenResponse]:
    """刷新令牌接口

    Args:
        request: 刷新令牌请求数据
        db: 数据库会话

    Returns:
        新的访问令牌
    """
    response = await auth_service.refresh_token(db, request.refresh_token)
    return ApiResponse.success(
        data=response,
        message="令牌刷新成功",
    )


@router.get(
    "/captcha",
    response_model=ApiResponse[CaptchaResponse],
    summary="获取图形验证码",
    description="获取图形验证码用于注册、登录等需要验证的场景",
)
async def get_captcha(
    db: DBSession,
) -> ApiResponse[CaptchaResponse]:
    """获取图形验证码接口

    Args:
        db: 数据库会话

    Returns:
        验证码响应，包含唯一标识和 Base64 图片
    """
    response = await auth_service.get_captcha(db)
    return ApiResponse.success(
        data=response,
        message="获取成功",
    )


@router.post(
    "/send-email-code",
    response_model=ApiResponse[None],
    summary="发送邮箱验证码",
    description="发送邮箱验证码用于注册验证或密码重置",
)
async def send_email_code(
    request: SendEmailCodeRequest,
    db: DBSession,
) -> ApiResponse[None]:
    """发送邮箱验证码接口

    Args:
        request: 发送验证码请求数据
        db: 数据库会话

    Returns:
        成功响应
    """
    await auth_service.send_email_code(db, request)
    return ApiResponse.success(message="验证码已发送，请查收邮件")


@router.post(
    "/reset-password",
    response_model=ApiResponse[None],
    summary="密码找回",
    description="通过邮箱验证码重置密码",
)
async def reset_password(
    request: ResetPasswordRequest,
    db: DBSession,
) -> ApiResponse[None]:
    """密码找回接口

    Args:
        request: 密码重置请求数据
        db: 数据库会话

    Returns:
        成功响应
    """
    await auth_service.reset_password(db, request)
    return ApiResponse.success(message="密码重置成功")