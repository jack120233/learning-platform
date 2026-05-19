"""角色权限管理接口测试。"""

from uuid import uuid4

import pytest
from sqlalchemy import select
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db_schema import ensure_database_compatibility
from app.core.security import hash_password
from app.models.permission import RolePermission
from app.services.permission_service import permission_service
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
        json={"username": f"{username}@example.com", "password": password},
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
    async def test_admin_and_teacher_default_permissions_are_different(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ):
        admin_headers = await login_as_role(client, db_session, "admin")
        reset_response = await client.post(
            "/api/v1/roles/teacher/permissions",
            headers=admin_headers,
            json={"permissions": [1, 11, 12, 13, 14, 2, 21, 22, 23]},
        )
        assert reset_response.status_code == 200

        teacher_headers = await login_as_role(client, db_session, "teacher")
        teacher_response = await client.get(
            "/api/v1/users/me/permissions",
            headers=teacher_headers,
        )
        admin_response = await client.get(
            "/api/v1/users/me/permissions",
            headers=admin_headers,
        )

        assert teacher_response.status_code == 200
        assert admin_response.status_code == 200
        assert teacher_response.json()["data"] == [
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
        assert "admin.user" in admin_response.json()["data"]
        assert "admin.teacher_audit" in admin_response.json()["data"]
        assert admin_response.json()["data"] != teacher_response.json()["data"]

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
    async def test_ensure_database_compatibility_removes_teacher_admin_permissions(
        self,
        db_session: AsyncSession,
    ):
        db_session.add_all([
            RolePermission(role="teacher", permission_id=31),
            RolePermission(role="teacher", permission_id=32),
            RolePermission(role="teacher", permission_id=35),
        ])
        await db_session.flush()

        async with db_session.bind.begin() as conn:
            messages = await ensure_database_compatibility(conn)

        permission_ids = await db_session.execute(
            select(RolePermission.permission_id)
            .where(RolePermission.role == "teacher")
            .order_by(RolePermission.permission_id.asc())
        )

        assert "已清理老师角色的历史后台权限" in messages
        assert list(permission_ids.scalars().all()) == [1, 2, 11, 12, 13, 14, 21, 22, 23]

    @pytest.mark.asyncio
    async def test_permission_seed_backfills_missing_roles_without_overwriting_teacher(
        self,
        db_session: AsyncSession,
    ):
        await permission_service.ensure_schema_and_seed(db_session)
        await db_session.execute(
            RolePermission.__table__.delete().where(RolePermission.role.in_(["student", "admin"]))
        )
        await db_session.flush()

        await permission_service.ensure_schema_and_seed(db_session)

        result = await db_session.execute(
            select(RolePermission.role, RolePermission.permission_id)
            .order_by(RolePermission.role.asc(), RolePermission.permission_id.asc())
        )
        rows = result.all()
        grouped: dict[str, list[int]] = {}
        for role, permission_id in rows:
            grouped.setdefault(role, []).append(permission_id)

        assert grouped["student"] == [1, 11, 12, 13, 14]
        assert grouped["teacher"] == [1, 2, 11, 12, 13, 14, 21, 22, 23]
        assert grouped["admin"] == [1, 2, 3, 11, 12, 13, 14, 21, 22, 23, 31, 32, 33, 35, 36, 37, 38, 39]

    @pytest.mark.asyncio
    async def test_permission_check_backfills_partial_role_permissions(
        self,
        db_session: AsyncSession,
    ):
        await permission_service.ensure_schema_and_seed(db_session)
        await db_session.execute(
            RolePermission.__table__.delete().where(
                (RolePermission.role == "student") & (RolePermission.permission_id == 14)
            )
        )
        await db_session.execute(
            RolePermission.__table__.delete().where(
                (RolePermission.role == "admin") & (RolePermission.permission_id.in_([38, 39]))
            )
        )
        await db_session.flush()

        messages = await permission_service.check_and_backfill_default_permissions(db_session)

        result = await db_session.execute(
            select(RolePermission.role, RolePermission.permission_id)
            .order_by(RolePermission.role.asc(), RolePermission.permission_id.asc())
        )
        rows = result.all()
        grouped: dict[str, list[int]] = {}
        for role, permission_id in rows:
            grouped.setdefault(role, []).append(permission_id)

        assert "已为学生角色补录 1 条默认权限" in messages
        assert "已为管理员角色补录 2 条默认权限" in messages
        assert grouped["student"] == [1, 11, 12, 13, 14]
        assert grouped["teacher"] == [1, 2, 11, 12, 13, 14, 21, 22, 23]
        assert grouped["admin"] == [1, 2, 3, 11, 12, 13, 14, 21, 22, 23, 31, 32, 33, 35, 36, 37, 38, 39]

    @pytest.mark.asyncio
    async def test_get_permission_tree_allows_role_permission_operator(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ):
        admin_headers = await login_as_role(client, db_session, "admin")
        student_headers = await login_as_role(client, db_session, "student")
        response = await client.get("/api/v1/permissions/tree", headers=student_headers)

        assert response.status_code == 403
        payload = response.json()
        assert payload["message"] == "无权查看角色权限配置"
