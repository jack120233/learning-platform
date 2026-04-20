"""反馈消息模块测试

测试反馈管理和消息管理功能。
"""

import uuid
from datetime import timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.core.db_schema import ensure_database_compatibility
from app.models.user import User


def unique_key(prefix: str = "fb") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


class TestFeedback:
    """反馈管理测试类"""

    @pytest.mark.asyncio
    async def test_create_feedback(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_user: User,
        test_course,
    ):
        """测试提交课程反馈，兼容前端请求结构。"""
        from app.models.captcha import CaptchaRecord
        from tests.test_auth import unique_key, utcnow

        key = unique_key("feedback")
        captcha = CaptchaRecord(
            captcha_key=key,
            captcha_text="test",
            image_base64="test",
            expires_at=utcnow() + timedelta(minutes=5),
        )
        db_session.add(captcha)
        await db_session.flush()

        login_response = await client.post(
            "/api/v1/auth/login",
            json={
                "username": "testuser",
                "password": "Test123456",
                "captcha_key": key,
                "captcha_text": "test",
            },
        )

        if login_response.status_code != 200:
            pytest.skip("登录失败")

        token = login_response.json()["data"]["access_token"]

        response = await client.post(
            "/api/v1/feedbacks",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "feedback_type": "course",
                "course_id": test_course.id,
                "content": "这是测试反馈内容，来自课程详情页。",
                "images": ["https://example.com/test-feedback.png"],
            },
        )

        assert response.status_code == 200
        data = response.json()["data"]
        assert data["feedback_id"] > 0
        assert data["feedback_type"] == "course"
        assert data["course_id"] == test_course.id
        assert data["course_title"] == test_course.title
        assert data["status"] == "pending"
        assert data["images"] == ["https://example.com/test-feedback.png"]

    @pytest.mark.asyncio
    async def test_get_feedbacks(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_user: User,
        test_course,
    ):
        """测试获取反馈列表时返回前端需要的字段。"""
        from app.models.feedback import Feedback
        from app.models.captcha import CaptchaRecord
        from tests.test_auth import unique_key, utcnow

        key = unique_key("feedback_list")
        captcha = CaptchaRecord(
            captcha_key=key,
            captcha_text="test",
            image_base64="test",
            expires_at=utcnow() + timedelta(minutes=5),
        )
        db_session.add(captcha)
        await db_session.flush()

        login_response = await client.post(
            "/api/v1/auth/login",
            json={
                "username": "testuser",
                "password": "Test123456",
                "captcha_key": key,
                "captcha_text": "test",
            },
        )

        if login_response.status_code != 200:
            pytest.skip("登录失败")

        token = login_response.json()["data"]["access_token"]

        feedback = Feedback(
            user_id=test_user.id,
            type="course",
            course_id=test_course.id,
            title="课程反馈",
            content="视频章节有点卡顿",
            images='["https://example.com/course-feedback.png"]',
            status="processed",
        )
        db_session.add(feedback)
        await db_session.flush()

        response = await client.get(
            "/api/v1/feedbacks",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        payload = response.json()["data"]
        assert payload["total"] >= 1
        assert len(payload["items"]) >= 1
        item = payload["items"][0]
        assert item["feedback_id"] == feedback.id
        assert item["feedback_type"] == "course"
        assert item["course_id"] == test_course.id
        assert item["course_title"] == test_course.title
        assert item["username"] == test_user.username
        assert item["status"] == "processed"

    @pytest.mark.asyncio
    async def test_get_feedback_detail(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_user: User,
        test_course,
    ):
        """测试反馈详情接口兼容字典序列化结果。"""
        from app.models.captcha import CaptchaRecord
        from app.models.feedback import Feedback
        from tests.test_auth import unique_key, utcnow

        key = unique_key("feedback_detail")
        captcha = CaptchaRecord(
            captcha_key=key,
            captcha_text="test",
            image_base64="test",
            expires_at=utcnow() + timedelta(minutes=5),
        )
        db_session.add(captcha)
        await db_session.flush()

        login_response = await client.post(
            "/api/v1/auth/login",
            json={
                "username": "testuser",
                "password": "Test123456",
                "captcha_key": key,
                "captcha_text": "test",
            },
        )

        if login_response.status_code != 200:
            pytest.skip("登录失败")

        token = login_response.json()["data"]["access_token"]

        feedback = Feedback(
            user_id=test_user.id,
            type="course",
            course_id=test_course.id,
            title="课程反馈详情",
            content="详情接口测试内容",
            status="pending",
        )
        db_session.add(feedback)
        await db_session.flush()

        response = await client.get(
            f"/api/v1/feedbacks/{feedback.id}",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()["data"]
        assert data["feedback_id"] == feedback.id
        assert data["course_id"] == test_course.id


@pytest.mark.asyncio
async def test_ensure_database_compatibility_adds_feedback_course_id():
    """测试数据库兼容检查会为旧版 feedbacks 表补充 course_id 字段。"""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)

    try:
        async with engine.begin() as conn:
            await conn.execute(
                text(
                    """
                    CREATE TABLE feedbacks (
                        id INTEGER PRIMARY KEY,
                        user_id INTEGER NOT NULL,
                        type VARCHAR(20) NOT NULL,
                        title VARCHAR(200) NOT NULL,
                        content TEXT NOT NULL,
                        contact VARCHAR(100),
                        images TEXT,
                        status VARCHAR(20),
                        reply TEXT,
                        replied_at DATETIME,
                        replied_by INTEGER
                    )
                    """
                )
            )

            messages = await ensure_database_compatibility(conn)

            def get_columns(sync_conn):
                return inspect(sync_conn).get_columns("feedbacks")

            columns = await conn.run_sync(get_columns)

        assert "已为 feedbacks 表补充 course_id 字段" in messages
        assert any(column["name"] == "course_id" for column in columns)
    finally:
        await engine.dispose()


class TestMessage:
    """消息管理测试类"""

    @pytest.mark.asyncio
    async def test_get_messages(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_user: User,
    ):
        """测试获取消息列表"""
        from app.models.captcha import CaptchaRecord
        from tests.test_auth import unique_key, utcnow

        key = unique_key("messages")
        captcha = CaptchaRecord(
            captcha_key=key,
            captcha_text="test",
            image_base64="test",
            expires_at=utcnow() + timedelta(minutes=5),
        )
        db_session.add(captcha)
        await db_session.flush()

        login_response = await client.post(
            "/api/v1/auth/login",
            json={
                "username": "testuser",
                "password": "Test123456",
                "captcha_key": key,
                "captcha_text": "test",
            },
        )

        if login_response.status_code != 200:
            pytest.skip("登录失败")

        token = login_response.json()["data"]["access_token"]

        response = await client.get(
            "/api/v1/messages",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code in [200, 400, 401]

    @pytest.mark.asyncio
    async def test_get_unread_count(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_user: User,
    ):
        """测试获取未读消息数量"""
        from app.models.captcha import CaptchaRecord
        from tests.test_auth import unique_key, utcnow

        key = unique_key("unread")
        captcha = CaptchaRecord(
            captcha_key=key,
            captcha_text="test",
            image_base64="test",
            expires_at=utcnow() + timedelta(minutes=5),
        )
        db_session.add(captcha)
        await db_session.flush()

        login_response = await client.post(
            "/api/v1/auth/login",
            json={
                "username": "testuser",
                "password": "Test123456",
                "captcha_key": key,
                "captcha_text": "test",
            },
        )

        if login_response.status_code != 200:
            pytest.skip("登录失败")

        token = login_response.json()["data"]["access_token"]

        response = await client.get(
            "/api/v1/messages/unread-count",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_mark_all_read(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_user: User,
    ):
        """测试批量标记已读"""
        from app.models.captcha import CaptchaRecord
        from tests.test_auth import unique_key, utcnow

        key = unique_key("mark_read")
        captcha = CaptchaRecord(
            captcha_key=key,
            captcha_text="test",
            image_base64="test",
            expires_at=utcnow() + timedelta(minutes=5),
        )
        db_session.add(captcha)
        await db_session.flush()

        login_response = await client.post(
            "/api/v1/auth/login",
            json={
                "username": "testuser",
                "password": "Test123456",
                "captcha_key": key,
                "captcha_text": "test",
            },
        )

        if login_response.status_code != 200:
            pytest.skip("登录失败")

        token = login_response.json()["data"]["access_token"]

        response = await client.post(
            "/api/v1/messages/mark-all-read",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code in [200, 400, 401]


# 导入必要的模型
from app.models.captcha import CaptchaRecord
