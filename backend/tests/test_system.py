"""系统管理模块测试

测试分类、标签、公告管理功能。
"""

import uuid
from datetime import datetime

import pytest
from httpx import AsyncClient
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.message import Message
from app.models.user import User


async def login_as_admin(
    client: AsyncClient,
    db_session: AsyncSession,
) -> dict[str, str]:
    """创建唯一管理员并返回认证头。"""
    unique_suffix = uuid.uuid4().hex[:8]
    username = f"admin_{unique_suffix}"
    password = "Admin123456"

    user = User(
        username=username,
        email=f"{username}@example.com",
        password_hash=hash_password(password),
        nickname="系统管理员",
        role="admin",
        status="active",
    )
    db_session.add(user)
    await db_session.flush()

    response = await client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": password},
    )
    assert response.status_code == 200
    token = response.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


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

    @pytest.mark.asyncio
    async def test_admin_can_create_announcement(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_user,
    ):
        """测试管理员创建公告"""
        admin_headers = await login_as_admin(client, db_session)
        title = f"测试公告{uuid.uuid4().hex[:8]}"
        response = await client.post(
            "/api/v1/announcements",
            headers=admin_headers,
            json={
                "title": title,
                "content": "这是一条测试公告",
                "is_published": True,
            },
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["message"] == "创建成功"
        assert payload["data"]["title"] == title
        assert payload["data"]["is_published"] is True
        assert payload["data"]["author_name"] == "系统管理员"
        assert datetime.fromisoformat(payload["data"]["publish_at"])

        result = await db_session.execute(
            select(Message).where(
                Message.user_id == test_user.id,
                Message.type == "announcement",
                Message.link == f"/announcements/{payload['data']['id']}",
            )
        )
        message = result.scalar_one_or_none()
        assert message is not None
        assert message.title == title
        assert message.content == "这是一条测试公告"

    @pytest.mark.asyncio
    async def test_admin_can_update_announcement(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ):
        """测试管理员更新公告"""
        admin_headers = await login_as_admin(client, db_session)
        create_response = await client.post(
            "/api/v1/announcements",
            headers=admin_headers,
            json={
                "title": f"待更新公告{uuid.uuid4().hex[:8]}",
                "content": "初始内容",
            },
        )
        announcement_id = create_response.json()["data"]["id"]

        update_response = await client.post(
            f"/api/v1/announcements/{announcement_id}",
            headers=admin_headers,
            json={
                "title": "已更新公告",
                "content": "更新后的内容",
                "is_published": True,
            },
        )

        assert update_response.status_code == 200
        payload = update_response.json()
        assert payload["message"] == "更新成功"
        assert payload["data"]["title"] == "已更新公告"
        assert payload["data"]["is_published"] is True
        assert payload["data"]["author_name"] == "系统管理员"
        assert datetime.fromisoformat(payload["data"]["publish_at"])

    @pytest.mark.asyncio
    async def test_published_announcement_is_visible_in_student_messages(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        auth_headers: dict[str, str],
        test_user,
    ):
        """测试已发布公告会同步到学生消息中心。"""
        admin_headers = await login_as_admin(client, db_session)
        create_response = await client.post(
            "/api/v1/announcements",
            headers=admin_headers,
            json={
                "title": f"消息中心公告{uuid.uuid4().hex[:8]}",
                "content": "学生端应该可以看到这条公告",
                "is_published": True,
            },
        )
        assert create_response.status_code == 200

        messages_response = await client.get(
            "/api/v1/messages",
            headers=auth_headers,
            params={"type": "announcement"},
        )
        assert messages_response.status_code == 200
        payload = messages_response.json()["data"]
        assert payload["total"] >= 1
        matched = next(
            item
            for item in payload["items"]
            if item["title"] == create_response.json()["data"]["title"]
        )
        assert matched["type"] == "announcement"
        assert matched["content"] == "学生端应该可以看到这条公告"

    @pytest.mark.asyncio
    async def test_unpublishing_announcement_removes_synced_messages(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_user,
    ):
        """测试公告转回草稿后会移除同步消息。"""
        admin_headers = await login_as_admin(client, db_session)
        create_response = await client.post(
            "/api/v1/announcements",
            headers=admin_headers,
            json={
                "title": f"待撤回公告{uuid.uuid4().hex[:8]}",
                "content": "先发布后撤回",
                "is_published": True,
            },
        )
        announcement_id = create_response.json()["data"]["id"]

        update_response = await client.post(
            f"/api/v1/announcements/{announcement_id}",
            headers=admin_headers,
            json={"is_published": False},
        )
        assert update_response.status_code == 200

        result = await db_session.execute(
            select(func.count()).select_from(Message).where(
                Message.user_id == test_user.id,
                Message.type == "announcement",
                Message.link == f"/announcements/{announcement_id}",
            )
        )
        assert result.scalar_one() == 0

    @pytest.mark.asyncio
    async def test_admin_can_delete_announcement(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ):
        """测试管理员删除公告"""
        admin_headers = await login_as_admin(client, db_session)
        create_response = await client.post(
            "/api/v1/announcements",
            headers=admin_headers,
            json={
                "title": f"待删除公告{uuid.uuid4().hex[:8]}",
                "content": "删除测试",
            },
        )
        announcement_id = create_response.json()["data"]["id"]

        delete_response = await client.post(
            f"/api/v1/announcements/{announcement_id}/delete",
            headers=admin_headers,
        )
        assert delete_response.status_code == 200
        assert delete_response.json()["message"] == "删除成功"

        get_response = await client.get(f"/api/v1/announcements/{announcement_id}")
        assert get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_announcements_supports_keyword_filter(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ):
        """测试公告列表支持关键词搜索"""
        admin_headers = await login_as_admin(client, db_session)
        title = f"关键字公告{uuid.uuid4().hex[:8]}"
        create_response = await client.post(
            "/api/v1/announcements",
            headers=admin_headers,
            json={
                "title": title,
                "content": "关键词过滤测试",
            },
        )
        assert create_response.status_code == 200

        response = await client.get("/api/v1/announcements", params={"keyword": title})
        assert response.status_code == 200
        items = response.json()["data"]["items"]
        matched_item = next(item for item in items if item["title"] == title)
        assert matched_item["author_name"] == "系统管理员"
