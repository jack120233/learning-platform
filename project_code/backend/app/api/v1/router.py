"""API v1 路由聚合模块

聚合所有 v1 版本的 API 路由。
"""

from fastapi import APIRouter

from app.api.v1 import (
    auth, health, categories, tags, announcements, permissions,
    users, courses, content, learning, feedbacks, messages, uploads
)

# v1 版本路由器
router = APIRouter()

# 注册子路由
router.include_router(health.router, tags=["健康检查"])
router.include_router(auth.router, tags=["用户认证"])
router.include_router(categories.router, tags=["分类管理"])
router.include_router(tags.router, tags=["标签管理"])
router.include_router(announcements.router, tags=["公告管理"])
router.include_router(permissions.router, tags=["角色权限管理"])
router.include_router(users.router, tags=["用户管理"])
router.include_router(courses.router, tags=["课程管理"])
router.include_router(uploads.router, tags=["文件上传"])
router.include_router(content.router, tags=["课程内容"])
router.include_router(learning.router, tags=["学习模块"])
router.include_router(feedbacks.router, tags=["反馈管理"])
router.include_router(messages.router, tags=["消息管理"])
