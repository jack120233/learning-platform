"""通用响应模型模块

定义 API 统一响应格式，符合项目规范：
{ "code": int, "message": str, "data": object }
"""

from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

# 泛型类型变量，用于响应数据类型
T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    """统一 API 响应模型

    所有 API 接口应使用此模型包装响应数据。

    Attributes:
        code: 业务状态码，200 表示成功
        message: 响应消息
        data: 响应数据，类型由泛型参数决定
    """

    code: int = Field(default=200, description="业务状态码")
    message: str = Field(default="success", description="响应消息")
    data: T | None = Field(default=None, description="响应数据")

    @classmethod
    def success(cls, data: T = None, message: str = "操作成功") -> "ApiResponse[T]":
        """创建成功响应

        Args:
            data: 响应数据
            message: 成功消息

        Returns:
            ApiResponse 实例
        """
        return cls(code=200, message=message, data=data)

    @classmethod
    def error(cls, code: int = 400, message: str = "操作失败", data: T = None) -> "ApiResponse[T]":
        """创建错误响应

        Args:
            code: 错误码
            message: 错误消息
            data: 附加数据

        Returns:
            ApiResponse 实例
        """
        return cls(code=code, message=message, data=data)


class PageData(BaseModel, Generic[T]):
    """分页数据模型

    用于包装分页查询结果。

    Attributes:
        items: 数据列表
        total: 总记录数
        page: 当前页码
        page_size: 每页记录数
        total_pages: 总页数
    """

    items: list[T] = Field(default_factory=list, description="数据列表")
    total: int = Field(default=0, description="总记录数")
    page: int = Field(default=1, ge=1, description="当前页码")
    page_size: int = Field(default=10, ge=1, le=100, description="每页记录数")
    total_pages: int = Field(default=0, description="总页数")

    @classmethod
    def create(
        cls,
        items: list[T],
        total: int,
        page: int = 1,
        page_size: int = 10,
    ) -> "PageData[T]":
        """创建分页数据

        Args:
            items: 数据列表
            total: 总记录数
            page: 当前页码
            page_size: 每页记录数

        Returns:
            PageData 实例
        """
        total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )


class ErrorResponse(BaseModel):
    """错误响应详情

    用于详细描述错误信息。
    """

    code: int = Field(description="错误码")
    message: str = Field(description="错误消息")
    details: Any | None = Field(default=None, description="错误详情")


# 常用业务状态码定义
class BusinessCode:
    """业务状态码常量"""

    # 成功
    SUCCESS = 200

    # 客户端错误 4xx
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    METHOD_NOT_ALLOWED = 405
    CONFLICT = 409
    VALIDATION_ERROR = 422

    # 业务错误 1xxx
    USER_NOT_FOUND = 1001
    USER_ALREADY_EXISTS = 1002
    INVALID_CREDENTIALS = 1003
    ACCOUNT_LOCKED = 1004
    INVALID_VERIFICATION_CODE = 1005
    TOKEN_EXPIRED = 1006
    TOKEN_INVALID = 1007

    # 课程相关错误 2xxx
    COURSE_NOT_FOUND = 2001
    CHAPTER_NOT_FOUND = 2002
    SECTION_NOT_FOUND = 2003
    RESOURCE_NOT_FOUND = 2004
    COURSE_NOT_PUBLISHED = 2005

    # 服务器错误 5xx
    INTERNAL_ERROR = 500
    DATABASE_ERROR = 501
    REDIS_ERROR = 502