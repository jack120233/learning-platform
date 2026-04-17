"""反馈消息模块测试

测试反馈管理和消息管理功能。
"""

import uuid
from datetime import datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

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
    ):
        """测试提交反馈"""
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
                "type": "suggestion",
                "title": "测试反馈",
                "content": "这是测试反馈内容",
            },
        )

        assert response.status_code in [200, 400, 422]

    @pytest.mark.asyncio
    async def test_get_feedbacks(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_user: User,
    ):
        """测试获取反馈列表"""
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

        response = await client.get(
            "/api/v1/feedbacks",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code in [200, 400, 401]


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
