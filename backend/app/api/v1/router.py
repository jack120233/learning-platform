"""API v1 路由聚合模块

聚合所有 v1 版本的 API 路由。
"""

from fastapi import APIRouter

from app.api.v1 import feedbacks, health, messages

# v1 版本路由器
router = APIRouter()

# 注册子路由
router.include_router(
    health.router,
    tags=["健康检查"],
)
router.include_router(
    feedbacks.router,
    tags=["反馈管理"],
)
router.include_router(
    messages.router,
    tags=["消息管理"],
)