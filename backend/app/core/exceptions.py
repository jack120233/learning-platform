"""自定义异常模块

定义项目中使用的自定义异常类。
"""

from fastapi import HTTPException, status

from app.schemas.common import BusinessCode


class AppException(Exception):
    """应用基础异常类

    所有自定义异常应继承此类。
    """

    def __init__(
        self,
        code: int = BusinessCode.BAD_REQUEST,
        message: str = "操作失败",
        details: dict | None = None,
    ):
        self.code = code
        self.message = message
        self.details = details
        super().__init__(self.message)


class UnauthorizedException(AppException):
    """未授权异常

    用户未登录或令牌无效时抛出。
    """

    def __init__(self, message: str = "未授权访问"):
        super().__init__(
            code=BusinessCode.UNAUTHORIZED,
            message=message,
        )


class ForbiddenException(AppException):
    """禁止访问异常

    用户无权限访问资源时抛出。
    """

    def __init__(self, message: str = "无权访问"):
        super().__init__(
            code=BusinessCode.FORBIDDEN,
            message=message,
        )


class NotFoundException(AppException):
    """资源未找到异常

    请求的资源不存在时抛出。
    """

    def __init__(self, message: str = "资源不存在"):
        super().__init__(
            code=BusinessCode.NOT_FOUND,
            message=message,
        )


class ValidationException(AppException):
    """数据验证异常

    请求数据验证失败时抛出。
    """

    def __init__(self, message: str = "数据验证失败", details: dict | None = None):
        super().__init__(
            code=BusinessCode.VALIDATION_ERROR,
            message=message,
            details=details,
        )


class ConflictException(AppException):
    """冲突异常

    资源冲突时抛出（如用户已存在）。
    """

    def __init__(self, message: str = "资源冲突"):
        super().__init__(
            code=BusinessCode.CONFLICT,
            message=message,
        )


class AuthenticationException(AppException):
    """认证失败异常

    登录认证失败时抛出。
    """

    def __init__(self, message: str = "认证失败"):
        super().__init__(
            code=BusinessCode.INVALID_CREDENTIALS,
            message=message,
        )


class AccountLockedException(AppException):
    """账户锁定异常

    账户被锁定时抛出。
    """

    def __init__(self, message: str = "账户已被锁定"):
        super().__init__(
            code=BusinessCode.ACCOUNT_LOCKED,
            message=message,
        )


def app_exception_to_http_exception(exc: AppException) -> HTTPException:
    """将应用异常转换为 HTTP 异常

    Args:
        exc: 应用异常实例

    Returns:
        FastAPI HTTPException 实例
    """
    # 根据业务码映射 HTTP 状态码
    http_status_map = {
        BusinessCode.SUCCESS: status.HTTP_200_OK,
        BusinessCode.BAD_REQUEST: status.HTTP_400_BAD_REQUEST,
        BusinessCode.UNAUTHORIZED: status.HTTP_401_UNAUTHORIZED,
        BusinessCode.FORBIDDEN: status.HTTP_403_FORBIDDEN,
        BusinessCode.NOT_FOUND: status.HTTP_404_NOT_FOUND,
        BusinessCode.METHOD_NOT_ALLOWED: status.HTTP_405_METHOD_NOT_ALLOWED,
        BusinessCode.CONFLICT: status.HTTP_409_CONFLICT,
        BusinessCode.VALIDATION_ERROR: status.HTTP_422_UNPROCESSABLE_ENTITY,
        BusinessCode.INTERNAL_ERROR: status.HTTP_500_INTERNAL_SERVER_ERROR,
    }

    http_status = http_status_map.get(exc.code, status.HTTP_400_BAD_REQUEST)

    return HTTPException(
        status_code=http_status,
        detail={
            "code": exc.code,
            "message": exc.message,
            "details": exc.details,
        },
    )