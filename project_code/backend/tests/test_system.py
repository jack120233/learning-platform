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
from app.models.permission import RolePermission
from app.models.tag import Tag
from app.models.user import User
from app.models.course import CourseTag
from app.services.permission_service import DEFAULT_ROLE_PERMISSION_IDS, permission_service


async def login_as_admin(
    client: AsyncClient,
    db_session: AsyncSession,
) -> dict[str, str]:
    """创建唯一管理员并返回认证头。"""
    unique_suffix = uuid.uuid4().hex[:8]
    username = f"admin_{unique_suffix}"
    password = "Admin123456"

    await permission_service.ensure_schema_and_seed(db_session)

    result = await db_session.execute(
        select(RolePermission.permission_id).where(RolePermission.role == "admin")
    )
    existing_permission_ids = set(result.scalars().all())
    missing_permission_ids = [
        permission_id
        for permission_id in DEFAULT_ROLE_PERMISSION_IDS["admin"]
        if permission_id not in existing_permission_ids
    ]
    if missing_permission_ids:
        db_session.add_all(
            [
                RolePermission(role="admin", permission_id=permission_id)
                for permission_id in missing_permission_ids
            ]
        )

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


async def create_role_user(
    client: AsyncClient,
    db_session: AsyncSession,
    role: str,
    password: str = "Test123456",
) -> dict[str, str | int]:
    """创建指定角色用户并返回认证头。"""
    unique_suffix = uuid.uuid4().hex[:8]
    username = f"{role}_{unique_suffix}"
    user = User(
        username=username,
        email=f"{username}@example.com",
        password_hash=hash_password(password),
        nickname=f"{role}-tester",
        role=role,
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
    return {
        "user_id": user.id,
        "username": username,
        "headers": {"Authorization": f"Bearer {token}"},
    }


async def ensure_role_permission(
    db_session: AsyncSession,
    role: str,
    permission_id: int,
) -> None:
    """确保角色权限存在。"""
    existing = await db_session.execute(
        select(RolePermission).where(
            RolePermission.role == role,
            RolePermission.permission_id == permission_id,
        )
    )
    if existing.scalar_one_or_none() is not None:
        return

    db_session.add(RolePermission(role=role, permission_id=permission_id))
    await db_session.flush()


async def create_test_tag(
    db_session: AsyncSession,
    name_prefix: str = "测试标签",
    slug_prefix: str = "test-tag",
) -> Tag:
    """创建测试标签。"""
    unique_suffix = uuid.uuid4().hex[:8]
    tag = Tag(
        name=f"{name_prefix}{unique_suffix}",
        slug=f"{slug_prefix}-{unique_suffix}",
        color="#409EFF",
    )
    db_session.add(tag)
    await db_session.flush()
    await db_session.refresh(tag)
    return tag


class TestCategory:
    """分类管理测试类"""

    @pytest.mark.asyncio
    async def test_get_categories(self, client: AsyncClient):
        """测试获取分类列表"""
        response = await client.get("/api/v1/categories")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_student_without_permission_cannot_create_category(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ):
        """测试普通用户不能创建分类。"""
        student_auth = await create_role_user(client, db_session, "student")
        name = f"测试分类{uuid.uuid4().hex[:8]}"
        slug = f"test-cat-{uuid.uuid4().hex[:8]}"

        response = await client.post(
            "/api/v1/categories",
            headers=student_auth["headers"],
            json={
                "name": name,
                "slug": slug,
            },
        )

        assert response.status_code == 403
        assert response.json()["message"] == "无权创建分类"

    @pytest.mark.asyncio
    async def test_teacher_with_category_permission_can_create_category(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ):
        """测试拥有分类管理权限的讲师可创建分类。"""
        teacher_auth = await create_role_user(client, db_session, "teacher")
        await ensure_role_permission(db_session, "teacher", 38)
        name = f"测试分类{uuid.uuid4().hex[:8]}"
        slug = f"test-cat-{uuid.uuid4().hex[:8]}"

        response = await client.post(
            "/api/v1/categories",
            headers=teacher_auth["headers"],
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
    async def test_student_without_permission_cannot_create_tag(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ):
        """测试普通用户不能创建标签。"""
        student_auth = await create_role_user(client, db_session, "student")
        name = f"测试标签{uuid.uuid4().hex[:8]}"
        slug = f"test-tag-{uuid.uuid4().hex[:8]}"

        response = await client.post(
            "/api/v1/tags",
            headers=student_auth["headers"],
            json={"name": name, "slug": slug},
        )

        assert response.status_code == 403
        assert response.json()["message"] == "无权创建标签"

    @pytest.mark.asyncio
    async def test_teacher_with_tag_permission_can_create_tag(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ):
        """测试拥有标签管理权限的讲师可创建标签。"""
        teacher_auth = await create_role_user(client, db_session, "teacher")
        await ensure_role_permission(db_session, "teacher", 39)
        name = f"测试标签{uuid.uuid4().hex[:8]}"
        slug = f"test-tag-{uuid.uuid4().hex[:8]}"

        response = await client.post(
            "/api/v1/tags",
            headers=teacher_auth["headers"],
            json={"name": name, "slug": slug},
        )

        assert response.status_code == 200
        data = response.json()["data"]
        assert data["name"] == name
        assert data["slug"] == slug
        assert datetime.fromisoformat(data["created_at"])


class TestTagDelete:
    """标签删除测试类"""

    @pytest.mark.asyncio
    async def test_student_without_permission_cannot_delete_tag(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ):
        """测试普通用户不能删除标签。"""
        student_auth = await create_role_user(client, db_session, "student")
        tag = await create_test_tag(db_session)

        response = await client.delete(
            f"/api/v1/tags/{tag.id}",
            headers=student_auth["headers"],
        )

        assert response.status_code == 403
        assert response.json()["message"] == "无权删除标签"

    @pytest.mark.asyncio
    async def test_teacher_with_tag_permission_can_delete_unused_tag(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ):
        """测试拥有标签权限的讲师可删除未被引用标签。"""
        teacher_auth = await create_role_user(client, db_session, "teacher")
        await ensure_role_permission(db_session, "teacher", 39)
        tag = await create_test_tag(db_session)
        tag_id = tag.id

        response = await client.delete(
            f"/api/v1/tags/{tag_id}",
            headers=teacher_auth["headers"],
        )

        assert response.status_code == 200
        assert response.json()["message"] == "删除成功"
        result = await db_session.execute(select(func.count()).select_from(Tag).where(Tag.id == tag_id))
        assert (result.scalar() or 0) == 0

    @pytest.mark.asyncio
    async def test_delete_tag_returns_not_found_for_missing_tag(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ):
        """测试删除不存在标签返回未找到。"""
        teacher_auth = await create_role_user(client, db_session, "teacher")
        await ensure_role_permission(db_session, "teacher", 39)

        response = await client.delete(
            "/api/v1/tags/999999",
            headers=teacher_auth["headers"],
        )

        assert response.status_code == 404
        assert response.json()["message"] == "标签不存在"

    @pytest.mark.asyncio
    async def test_delete_tag_fails_when_tag_is_used_by_course(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ):
        """测试已被课程引用的标签不能删除。"""
        from tests.test_courses import create_course_with_status, create_upload_test_user_with_user

        teacher_auth = await create_role_user(client, db_session, "teacher")
        await ensure_role_permission(db_session, "teacher", 39)
        tag = await create_test_tag(db_session, name_prefix="引用标签", slug_prefix="used-tag")
        teacher, _ = await create_upload_test_user_with_user(db_session, "teacher")
        course = await create_course_with_status(db_session, teacher.id, "draft", "标签引用课程")
        db_session.add(CourseTag(course_id=course.id, tag_id=tag.id))
        await db_session.flush()

        response = await client.delete(
            f"/api/v1/tags/{tag.id}",
            headers=teacher_auth["headers"],
        )

        assert response.status_code == 422
        assert response.json()["message"] == "标签已被课程引用，无法删除"

    @pytest.mark.asyncio
    async def test_teacher_with_tag_permission_can_batch_delete_tags(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ):
        """测试拥有标签权限的讲师可批量删除未被引用标签。"""
        teacher_auth = await create_role_user(client, db_session, "teacher")
        await ensure_role_permission(db_session, "teacher", 39)
        tag_a = await create_test_tag(db_session, name_prefix="批量标签A", slug_prefix="batch-tag-a")
        tag_b = await create_test_tag(db_session, name_prefix="批量标签B", slug_prefix="batch-tag-b")

        response = await client.post(
            "/api/v1/tags/batch-delete",
            headers=teacher_auth["headers"],
            json={"tag_ids": [tag_a.id, tag_b.id]},
        )

        assert response.status_code == 200
        data = response.json()["data"]
        assert data["success_count"] == 2
        assert data["failed_count"] == 0
        assert set(data["success_ids"]) == {tag_a.id, tag_b.id}
        assert await db_session.get(Tag, tag_a.id) is None
        assert await db_session.get(Tag, tag_b.id) is None

    @pytest.mark.asyncio
    async def test_batch_delete_tags_returns_failure_details(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ):
        """测试批量删除标签返回失败明细。"""
        from tests.test_courses import create_course_with_status, create_upload_test_user_with_user

        teacher_auth = await create_role_user(client, db_session, "teacher")
        await ensure_role_permission(db_session, "teacher", 39)
        removable_tag = await create_test_tag(db_session, name_prefix="可删标签", slug_prefix="removable-tag")
        used_tag = await create_test_tag(db_session, name_prefix="被引用标签", slug_prefix="used-batch-tag")
        removable_tag_id = removable_tag.id
        used_tag_id = used_tag.id
        teacher, _ = await create_upload_test_user_with_user(db_session, "teacher")
        course = await create_course_with_status(db_session, teacher.id, "draft", "批量标签引用课程")
        db_session.add(CourseTag(course_id=course.id, tag_id=used_tag_id))
        await db_session.flush()

        response = await client.post(
            "/api/v1/tags/batch-delete",
            headers=teacher_auth["headers"],
            json={"tag_ids": [removable_tag_id, used_tag_id, 999999]},
        )

        assert response.status_code == 200
        data = response.json()["data"]
        assert data["success_count"] == 1
        assert data["failed_count"] == 2
        assert data["success_ids"] == [removable_tag_id]
        failed_items = {item["tag_id"]: item["reason"] for item in data["failed_items"]}
        assert failed_items[used_tag_id] == "标签已被课程引用，无法删除"
        assert failed_items[999999] == "标签不存在"
        removable_result = await db_session.execute(
            select(func.count()).select_from(Tag).where(Tag.id == removable_tag_id)
        )
        used_result = await db_session.execute(
            select(func.count()).select_from(Tag).where(Tag.id == used_tag_id)
        )
        assert (removable_result.scalar() or 0) == 0
        assert (used_result.scalar() or 0) == 1


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
    async def test_published_announcement_excludes_admin_recipients(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_admin,
    ):
        """测试发布公告不会给管理员生成站内消息。"""
        admin_headers = await login_as_admin(client, db_session)
        student_auth = await create_role_user(client, db_session, "student")
        teacher_auth = await create_role_user(client, db_session, "teacher")
        title = f"排除管理员公告{uuid.uuid4().hex[:8]}"

        response = await client.post(
            "/api/v1/announcements",
            headers=admin_headers,
            json={
                "title": title,
                "content": "管理员不应接收公告消息",
                "is_published": True,
            },
        )
        assert response.status_code == 200
        announcement_id = response.json()["data"]["id"]

        result = await db_session.execute(
            select(Message.user_id).where(
                Message.type == "announcement",
                Message.link == f"/announcements/{announcement_id}",
            )
        )
        recipient_ids = set(result.scalars().all())
        assert student_auth["user_id"] in recipient_ids
        assert teacher_auth["user_id"] in recipient_ids
        assert test_admin.id not in recipient_ids

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
    async def test_republishing_announcement_creates_new_non_admin_messages(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ):
        """测试同一公告再次发布会给非管理员生成新的可见消息。"""
        admin_headers = await login_as_admin(client, db_session)
        student_auth = await create_role_user(client, db_session, "student")
        title = f"再次发布公告{uuid.uuid4().hex[:8]}"
        create_response = await client.post(
            "/api/v1/announcements",
            headers=admin_headers,
            json={
                "title": title,
                "content": "第一次发布内容",
                "is_published": True,
            },
        )
        assert create_response.status_code == 200
        announcement_id = create_response.json()["data"]["id"]

        republish_response = await client.post(
            f"/api/v1/announcements/{announcement_id}",
            headers=admin_headers,
            json={"is_published": True},
        )
        assert republish_response.status_code == 200

        messages_response = await client.get(
            "/api/v1/messages",
            headers=student_auth["headers"],
            params={"type": "announcement"},
        )
        assert messages_response.status_code == 200
        matched_messages = [
            item
            for item in messages_response.json()["data"]["items"]
            if item["link"] == f"/announcements/{announcement_id}"
        ]
        assert len(matched_messages) == 2
        assert {item["title"] for item in matched_messages} == {title}

        unread_response = await client.get(
            "/api/v1/messages/unread-count",
            headers=student_auth["headers"],
        )
        assert unread_response.status_code == 200
        unread_data = unread_response.json()["data"]
        assert unread_data["announcement"] == 2
        assert unread_data["total"] >= 2

    @pytest.mark.asyncio
    async def test_editing_published_announcement_without_status_does_not_resend(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ):
        """测试编辑已发布公告内容但不提交发布状态时不会重新发送消息。"""
        admin_headers = await login_as_admin(client, db_session)
        student_auth = await create_role_user(client, db_session, "student")
        title = f"编辑不重发公告{uuid.uuid4().hex[:8]}"
        create_response = await client.post(
            "/api/v1/announcements",
            headers=admin_headers,
            json={
                "title": title,
                "content": "首次发布内容",
                "is_published": True,
            },
        )
        assert create_response.status_code == 200
        announcement_id = create_response.json()["data"]["id"]

        update_response = await client.post(
            f"/api/v1/announcements/{announcement_id}",
            headers=admin_headers,
            json={
                "title": f"{title}-已编辑",
                "content": "只编辑内容，不重发消息",
            },
        )
        assert update_response.status_code == 200
        assert update_response.json()["data"]["content"] == "只编辑内容，不重发消息"

        messages_response = await client.get(
            "/api/v1/messages",
            headers=student_auth["headers"],
            params={"type": "announcement"},
        )
        assert messages_response.status_code == 200
        matched_messages = [
            item
            for item in messages_response.json()["data"]["items"]
            if item["link"] == f"/announcements/{announcement_id}"
        ]
        assert len(matched_messages) == 1
        assert matched_messages[0]["title"] == title
        assert matched_messages[0]["content"] == "首次发布内容"

    @pytest.mark.asyncio
    async def test_unpublishing_announcement_removes_synced_messages(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_user,
    ):
        """测试公告转回草稿后会移除所有同步消息。"""
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
        republish_response = await client.post(
            f"/api/v1/announcements/{announcement_id}",
            headers=admin_headers,
            json={"is_published": True},
        )
        assert republish_response.status_code == 200

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


class TestMessagePermission:
    """系统消息发送权限测试类"""

    @pytest.mark.asyncio
    async def test_student_without_permission_cannot_send_system_message(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ):
        """测试普通用户不能发送系统消息。"""
        student_auth = await create_role_user(client, db_session, "student")
        target_user = await create_role_user(client, db_session, "student")

        response = await client.post(
            "/api/v1/messages/send",
            headers=student_auth["headers"],
            json={
                "user_id": target_user["user_id"],
                "type": "system",
                "title": "系统通知",
                "content": "普通用户不应发送成功",
            },
        )

        assert response.status_code == 403
        assert response.json()["message"] == "无权发送系统消息"

    @pytest.mark.asyncio
    async def test_teacher_with_message_permission_can_send_system_message(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ):
        """测试拥有系统消息权限的讲师可发送系统消息。"""
        teacher_auth = await create_role_user(client, db_session, "teacher")
        target_user = await create_role_user(client, db_session, "student")
        await ensure_role_permission(db_session, "teacher", 37)

        send_response = await client.post(
            "/api/v1/messages/send",
            headers=teacher_auth["headers"],
            json={
                "user_id": target_user["user_id"],
                "type": "system",
                "title": "系统通知",
                "content": "这是一条定向系统消息",
            },
        )

        assert send_response.status_code == 200
        payload = send_response.json()["data"]
        assert payload["title"] == "系统通知"
        assert payload["type"] == "system"

        list_response = await client.get(
            "/api/v1/messages",
            headers=target_user["headers"],
            params={"type": "system"},
        )
        assert list_response.status_code == 200
        items = list_response.json()["data"]["items"]
        matched = next(item for item in items if item["title"] == "系统通知")
        assert matched["content"] == "这是一条定向系统消息"

        unread_response = await client.get(
            "/api/v1/messages/unread-count",
            headers=target_user["headers"],
        )
        assert unread_response.status_code == 200
        assert unread_response.json()["data"]["system"] >= 1
