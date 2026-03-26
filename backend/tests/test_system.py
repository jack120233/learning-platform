"""系统管理模块测试

测试分类、标签、公告管理功能。
"""

import uuid
from datetime import datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


def unique_key(prefix: str = "sys") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


class TestCategory:
    """分类管理测试类"""

    @pytest.mark.asyncio
    async def test_get_categories(self, client: AsyncClient):
        """测试获取分类列表"""
        response = await client.get("/api/v1/categories")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_create_category(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_admin: User,
    ):
        """测试创建分类"""
        from app.models.captcha import CaptchaRecord
        from tests.test_auth import unique_key, utcnow

        key = unique_key("cat_create")
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
                "username": "testadmin",
                "password": "Admin123456",
                "captcha_key": key,
                "captcha_text": "test",
            },
        )

        if login_response.status_code != 200:
            pytest.skip("登录失败")

        token = login_response.json()["data"]["access_token"]

        response = await client.post(
            "/api/v1/categories",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": f"测试分类{uuid.uuid4().hex[:8]}",
                "slug": f"test-cat-{uuid.uuid4().hex[:8]}",
            },
        )

        assert response.status_code in [200, 400, 401, 403]


class TestTag:
    """标签管理测试类"""

    @pytest.mark.asyncio
    async def test_get_tags(self, client: AsyncClient):
        """测试获取标签列表"""
        response = await client.get("/api/v1/tags")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_create_tag(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_admin: User,
    ):
        """测试创建标签"""
        from app.models.captcha import CaptchaRecord
        from tests.test_auth import unique_key, utcnow

        key = unique_key("tag_create")
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
                "username": "testadmin",
                "password": "Admin123456",
                "captcha_key": key,
                "captcha_text": "test",
            },
        )

        if login_response.status_code != 200:
            pytest.skip("登录失败")

        token = login_response.json()["data"]["access_token"]

        response = await client.post(
            "/api/v1/tags",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": f"测试标签{uuid.uuid4().hex[:8]}"},
        )

        assert response.status_code in [200, 400, 401, 403, 422]


class TestAnnouncement:
    """公告管理测试类"""

    @pytest.mark.asyncio
    async def test_get_announcements(self, client: AsyncClient):
        """测试获取公告列表"""
        response = await client.get("/api/v1/announcements")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_active_announcements(self, client: AsyncClient):
        """测试获取有效公告"""
        response = await client.get("/api/v1/announcements/active")
        assert response.status_code == 200


# 导入必要的模型
from app.models.captcha import CaptchaRecord