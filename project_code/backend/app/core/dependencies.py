"""依赖注入模块

提供 FastAPI 依赖注入函数，包括数据库会话、用户认证等。
"""

from typing import Annotated, AsyncGenerator

from sqlalchemy import select

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings
from app.core.security import decode_token
from app.core.sql_logging import install_sql_logging
from app.core.runtime import install_sqlite_runtime_hooks
from app.models.user import User
from app.schemas.common import BusinessCode

# HTTP Bearer 认证方案
security = HTTPBearer(auto_error=False)


# 数据库引擎
engine = create_async_engine(
    settings.async_database_url,
    echo=settings.database_echo,
    pool_pre_ping=True,
    connect_args=settings.sqlalchemy_connect_args,
)
install_sqlite_runtime_hooks(engine)
install_sql_logging(engine)

# 异步会话工厂
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """获取数据库会话

    使用依赖注入方式管理数据库会话生命周期。
    自动处理会话的开启和关闭。

    Yields:
        AsyncSession: 异步数据库会话
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# 数据库会话依赖类型
DBSession = Annotated[AsyncSession, Depends(get_db)]


async def get_current_user_id(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(security),
    ],
) -> int:
    """获取当前用户 ID

    从 Authorization 头中解析 JWT 令牌，返回用户 ID。

    Args:
        credentials: HTTP Bearer 凭证

    Returns:
        用户 ID

    Raises:
        HTTPException: 令牌无效或已过期
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": BusinessCode.UNAUTHORIZED,
                "message": "未提供认证令牌",
            },
        )

    token = credentials.credentials
    payload = decode_token(token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": BusinessCode.TOKEN_INVALID,
                "message": "令牌无效",
            },
        )

    # 检查令牌类型
    token_type = payload.get("type")
    if token_type != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": BusinessCode.TOKEN_INVALID,
                "message": "令牌类型错误",
            },
        )

    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": BusinessCode.TOKEN_INVALID,
                "message": "令牌格式错误",
            },
        )

    return int(user_id)


# 当前用户 ID 依赖类型
CurrentUserId = Annotated[int, Depends(get_current_user_id)]


async def get_current_user(
    db: DBSession,
    user_id: CurrentUserId,
) -> User:
    """获取当前用户对象。"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": BusinessCode.UNAUTHORIZED,
                "message": "用户不存在或已失效",
            },
        )
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


async def get_optional_user_id(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(security),
    ],
) -> int | None:
    """获取可选用户 ID

    如果提供了有效令牌则返回用户 ID，否则返回 None。
    用于可选认证的接口。

    Args:
        credentials: HTTP Bearer 凭证

    Returns:
        用户 ID 或 None
    """
    if credentials is None:
        return None

    token = credentials.credentials
    payload = decode_token(token)

    if payload is None:
        return None

    user_id = payload.get("sub")
    if user_id is None:
        return None

    return int(user_id)


# 可选用户 ID 依赖类型
OptionalUserId = Annotated[int | None, Depends(get_optional_user_id)]
