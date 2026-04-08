"""系统管理模块测试

测试分类、标签、公告管理功能。
"""

import uuid
from datetime import datetime

import pytest
from httpx import AsyncClient


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
    ):
        """测试创建分类"""
        name = f"测试分类{uuid.uuid4().hex[:8]}"
        slug = f"test-cat-{uuid.uuid4().hex[:8]}"

        response = await client.post(
            "/api/v1/categories",
            json={
                "name": name,
                "slug": slug,
            },
        )

        assert response.status_code == 200
        data = response.json()["data"]
        assert data["name"] == name
        assert data["slug"] == slug
        assert datetime.fromisoformat(data["created_at"])


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
    ):
        """测试创建标签"""
        name = f"测试标签{uuid.uuid4().hex[:8]}"
        slug = f"test-tag-{uuid.uuid4().hex[:8]}"

        response = await client.post(
            "/api/v1/tags",
            json={"name": name, "slug": slug},
        )

        assert response.status_code == 200
        data = response.json()["data"]
        assert data["name"] == name
        assert data["slug"] == slug
        assert datetime.fromisoformat(data["created_at"])


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
