"""安全工具模块

提供密码加密、JWT 令牌生成与验证等功能。
"""

from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings

# 密码加密上下文
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=settings.bcrypt_rounds,
)


def hash_password(password: str) -> str:
    """生成密码哈希值

    Args:
        password: 明文密码

    Returns:
        密码哈希值
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码

    Args:
        plain_password: 明文密码
        hashed_password: 密码哈希值

    Returns:
        验证结果
    """
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(
    subject: str | int,
    expires_delta: timedelta | None = None,
    extra_data: dict[str, Any] | None = None,
) -> str:
    """创建访问令牌

    Args:
        subject: 令牌主体（通常是用户 ID）
        expires_delta: 过期时间增量
        extra_data: 额外数据

    Returns:
        JWT 访问令牌
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.access_token_expire_minutes
        )

    to_encode = {
        "sub": str(subject),
        "exp": expire,
        "type": "access",
    }
    if extra_data:
        to_encode.update(extra_data)

    return jwt.encode(
        to_encode,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def create_refresh_token(
    subject: str | int,
    remember_me: bool = False,
) -> str:
    """创建刷新令牌

    Args:
        subject: 令牌主体（通常是用户 ID）
        remember_me: 是否记住我（延长过期时间）

    Returns:
        JWT 刷新令牌
    """
    days = settings.remember_me_expire_days if remember_me else settings.refresh_token_expire_days
    expire = datetime.now(timezone.utc) + timedelta(days=days)

    to_encode = {
        "sub": str(subject),
        "exp": expire,
        "type": "refresh",
    }

    return jwt.encode(
        to_encode,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def decode_token(token: str) -> dict[str, Any] | None:
    """解码并验证令牌

    Args:
        token: JWT 令牌

    Returns:
        解码后的载荷，验证失败返回 None
    """
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        return payload
    except JWTError:
        return None


def get_token_subject(token: str) -> str | None:
    """获取令牌主体

    Args:
        token: JWT 令牌

    Returns:
        令牌主体（通常是用户 ID）
    """
    payload = decode_token(token)
    if payload:
        return payload.get("sub")
    return None


def get_token_type(token: str) -> str | None:
    """获取令牌类型

    Args:
        token: JWT 令牌

    Returns:
        令牌类型（access 或 refresh）
    """
    payload = decode_token(token)
    if payload:
        return payload.get("type")
    return None


def is_token_expired(token: str) -> bool:
    """检查令牌是否过期

    Args:
        token: JWT 令牌

    Returns:
        是否过期
    """
    payload = decode_token(token)
    if not payload:
        return True

    exp = payload.get("exp")
    if not exp:
        return True

    return datetime.now(timezone.utc).timestamp() > exp