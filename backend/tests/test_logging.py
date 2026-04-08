"""日志能力测试。"""

import logging

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.models.course import Course


class TestRequestAndSqlLogging:
    """验证请求日志和 SQL 日志可以串联排查。"""

    @pytest.mark.asyncio
    async def test_my_courses_logs_sql_content(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_teacher,
        caplog,
    ):
        course = Course(
            title="日志测试课程",
            subtitle="日志测试副标题",
            description="日志测试描述",
            teacher_id=test_teacher.id,
            status="draft",
            price=9.9,
            level="beginner",
        )
        db_session.add(course)
        await db_session.flush()

        token = create_access_token(test_teacher.id)
        caplog.set_level(logging.DEBUG)

        response = await client.get(
            "/api/v1/courses/my-courses?page=1&page_size=10",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        request_id = response.headers["X-Request-ID"]
        messages = [record.getMessage() for record in caplog.records]
        combined = "\n".join(messages)

        assert f"[{request_id}] 请求开始" in combined
        assert f"[{request_id}] 请求完成" in combined
        assert f"[{request_id}] SQL执行" in combined
        assert "FROM courses" in combined
        assert "teacher_id" in combined
        assert "数据库: 2条SQL/" in combined
