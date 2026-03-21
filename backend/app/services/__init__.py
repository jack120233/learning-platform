"""业务逻辑服务模块

导出所有服务类。
"""

from app.services.auth_service import AuthService, auth_service

__all__ = [
    "AuthService",
    "auth_service",
]