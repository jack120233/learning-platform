"""业务逻辑服务模块

导出所有服务类。
"""

from app.services.learning_service import LearningService, learning_service

__all__ = [
    "LearningService",
    "learning_service",
]