"""角色权限管理接口测试。"""

from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.user import User


async def login_as_role(
    client: AsyncClient,
    db_session: AsyncSession,
    role: str,
) -> dict[str, str]:
    """创建唯一测试用户并返回认证头。"""
    unique_suffix = uuid4().hex[:8]
    username = f"{role}_{unique_suffix}"
    password = "Admin123456" if role == "admin" else "Test123456"

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
    return {"Authorization": f"Bearer {token}"}


class TestPermissionTree:
    """权限树接口测试。"""

    @pytest.mark.asyncio
    async def test_get_permission_tree_success(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ):
        admin_headers = await login_as_role(client, db_session, "admin")
        response = await client.get("/api/v1/permissions/tree", headers=admin_headers)

        assert response.status_code == 200
        payload = response.json()
        assert payload["code"] == 200
        assert isinstance(payload["data"], list)
        assert any(item["code"] == "learn" for item in payload["data"])
        admin_node = next(item for item in payload["data"] if item["code"] == "admin")
        assert any(child["code"] == "admin.role_permission" for child in admin_node["children"])

    @pytest.mark.asyncio
    async def test_get_permission_tree_forbidden_for_student(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ):
        auth_headers = await login_as_role(client, db_session, "student")
        response = await client.get("/api/v1/permissions/tree", headers=auth_headers)

        assert response.status_code == 403
        payload = response.json()
        assert payload["message"] == "无权查看角色权限配置"

class TestRolePermissions:
    """角色权限配置接口测试。"""

    @pytest.mark.asyncio
    async def test_get_role_permissions_success(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ):
        admin_headers = await login_as_role(client, db_session, "admin")
        response = await client.get(
            "/api/v1/roles/student/permissions",
            headers=admin_headers,
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["code"] == 200
        assert payload["data"] == [1, 11, 12, 13, 14]

    @pytest.mark.asyncio
    async def test_get_role_permissions_allows_same_role_user(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ):
        teacher_headers = await login_as_role(client, db_session, "teacher")
        response = await client.get(
            "/api/v1/roles/teacher/permissions",
            headers=teacher_headers,
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["code"] == 200
        assert payload["data"] == [1, 2, 11, 12, 13, 14, 21, 22, 23]

    @pytest.mark.asyncio
    async def test_get_my_permissions_success(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ):
        teacher_headers = await login_as_role(client, db_session, "teacher")
        response = await client.get(
            "/api/v1/users/me/permissions",
            headers=teacher_headers,
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["code"] == 200
        assert payload["data"] == [
            "learn",
            "learn.course",
            "learn.progress",
            "learn.profile",
            "feedback.submit",
            "teacher",
            "teacher.course",
            "teacher.content",
            "teacher.upload",
        ]

    @pytest.mark.asyncio
    async def test_update_role_permissions_success(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ):
        admin_headers = await login_as_role(client, db_session, "admin")
        response = await client.post(
            "/api/v1/roles/teacher/permissions",
            headers=admin_headers,
            json={"permissions": [11, 12, 21, 22, 23]},
        )

        assert response.status_code == 200
        assert response.json()["message"] == "权限配置已更新"

        follow_up = await client.get(
            "/api/v1/roles/teacher/permissions",
            headers=admin_headers,
        )
        assert follow_up.status_code == 200
        # 自动补齐父级节点 learn(1) 和 teacher(2)
        assert follow_up.json()["data"] == [1, 2, 11, 12, 21, 22, 23]

    @pytest.mark.asyncio
    async def test_update_role_permissions_rejects_invalid_permission_id(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ):
        admin_headers = await login_as_role(client, db_session, "admin")
        response = await client.post(
            "/api/v1/roles/student/permissions",
            headers=admin_headers,
            json={"permissions": [9999]},
        )

        assert response.status_code == 422
        payload = response.json()
        assert payload["message"] == "存在无效的权限ID"
        assert payload["details"]["invalid_permissions"] == [9999]

    @pytest.mark.asyncio
    async def test_update_role_permissions_forbidden_for_teacher(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ):
        teacher_headers = await login_as_role(client, db_session, "teacher")
        response = await client.post(
            "/api/v1/roles/student/permissions",
            headers=teacher_headers,
            json={"permissions": [1, 11]},
        )

        assert response.status_code == 403
        payload = response.json()
        assert payload["message"] == "无权修改角色权限配置"

    @pytest.mark.asyncio
    async def test_get_permission_tree_allows_role_permission_operator(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ):
        admin_headers = await login_as_role(client, db_session, "admin")
        grant_response = await client.post(
            "/api/v1/roles/student/permissions",
            headers=admin_headers,
            json={"permissions": [34]},
        )
        assert grant_response.status_code == 200

        student_headers = await login_as_role(client, db_session, "student")
        response = await client.get("/api/v1/permissions/tree", headers=student_headers)

        assert response.status_code == 200
        payload = response.json()
        assert payload["code"] == 200
        assert any(item["code"] == "admin" for item in payload["data"])
