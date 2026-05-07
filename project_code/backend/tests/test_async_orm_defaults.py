"""异步 ORM 默认值回归测试。"""

import pytest
from sqlalchemy import inspect as sa_inspect
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.schemas.course import CourseCreate, CourseResponse
from app.services.course_service import course_service


@pytest.mark.asyncio
async def test_create_course_loads_server_defaults(
    db_session: AsyncSession,
    test_teacher: User,
):
    """创建课程后，server_default 字段应在序列化前就已加载。"""
    course = await course_service.create(
        db_session,
        test_teacher.id,
        CourseCreate(title="默认值课程", description="描述"),
    )

    state = sa_inspect(course)

    assert "created_at" not in state.unloaded
    assert course.created_at is not None

    response = CourseResponse.model_validate(course)
    assert response.created_at == course.created_at
