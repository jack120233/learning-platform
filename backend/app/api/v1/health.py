"""健康检查路由模块

提供服务健康状态检查接口。
"""

from fastapi import APIRouter

from app.schemas.common import ApiResponse

router = APIRouter()


@router.get("/health", summary="健康检查")
async def health_check() -> ApiResponse:
    """健康检查接口

    用于检查服务是否正常运行。

    Returns:
        成功响应
    """
    return ApiResponse.success(message="服务运行正常")


@router.get("/ping", summary="Ping 检查")
async def ping() -> ApiResponse:
    """Ping 检查接口

    简单的连通性测试接口。

    Returns:
        Pong 响应
    """
    return ApiResponse.success(message="pong")