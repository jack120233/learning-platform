"""业务逻辑服务模块

导出所有服务类。
"""

from app.services.feedback_service import FeedbackService, feedback_service
from app.services.message_service import MessageService, message_service

__all__ = [
    "FeedbackService",
    "feedback_service",
    "MessageService",
    "message_service",
]