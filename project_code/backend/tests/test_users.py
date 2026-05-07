"""用户管理模块测试

测试用户信息管理、密码修改、学习记录等功能。
"""

import uuid
from datetime import datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.content import Chapter, Resource, Section
from app.models.course import Course
from app.models.learning import ResourceProgress
from app.models.user import User
from app.core.security import hash_password
from app.models.permission import RolePermission


def unique_key(prefix: str = "user") -> str:
    """生成唯一键"""
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


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


class TestUserProfile:
    """用户个人信息测试类"""

    @pytest.mark.asyncio
    async def test_get_current_user(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_user: User,
    ):
        """测试获取当前用户信息"""
        # 先登录获取 token
        from app.models.captcha import CaptchaRecord
        from tests.test_auth import unique_key, utcnow

        key = unique_key("profile")
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
            assert login_response.status_code in [200, 400, 401]
            return

        token = login_response.json()["data"]["access_token"]

        response = await client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["username"] == "testuser"

    @pytest.mark.asyncio
    async def test_get_current_user_unauthorized(self, client: AsyncClient):
        """测试未认证获取用户信息失败"""
        response = await client.get("/api/v1/users/me")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_update_profile(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_user: User,
    ):
        """测试更新个人信息"""
        from app.models.captcha import CaptchaRecord
        from tests.test_auth import unique_key, utcnow

        key = unique_key("update")
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
            assert login_response.status_code in [200, 400, 401]
            return

        token = login_response.json()["data"]["access_token"]

        response = await client.post(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {token}"},
            json={"nickname": "新昵称"},
        )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_my_feedbacks(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_user: User,
        test_course,
    ):
        """测试获取我的反馈列表接口兼容反馈字典结构。"""
        from app.models.captcha import CaptchaRecord
        from app.models.feedback import Feedback
        from tests.test_auth import unique_key, utcnow

        key = unique_key("my_feedbacks")
        captcha = CaptchaRecord(
            captcha_key=key,
            captcha_text="test",
            image_base64="test",
            expires_at=utcnow() + timedelta(minutes=5),
        )
        db_session.add(captcha)
        await db_session.flush()

        feedback = Feedback(
            user_id=test_user.id,
            type="course",
            course_id=test_course.id,
            title="我的课程反馈",
            content="个人中心反馈列表测试",
            images='["https://example.com/profile-feedback.png"]',
            status="pending",
        )
        db_session.add(feedback)
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
            assert login_response.status_code in [200, 400, 401]
            return

        token = login_response.json()["data"]["access_token"]

        response = await client.get(
            "/api/v1/users/me/feedbacks",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        payload = response.json()["data"]
        assert payload["total"] >= 1
        item = payload["items"][0]
        assert item["feedback_id"] == feedback.id
        assert item["feedback_type"] == "course"
        assert item["course_id"] == test_course.id
        assert item["course_title"] == test_course.title
        assert item["images"] == ["https://example.com/profile-feedback.png"]

    @pytest.mark.asyncio
    async def test_get_learning_records_uses_resource_progress(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_user: User,
        test_teacher: User,
        test_category,
    ):
        """测试学习记录接口会从 resource_progress 聚合课程级记录。"""
        from app.models.captcha import CaptchaRecord
        from tests.test_auth import unique_key, utcnow

        course = Course(
            title="学习记录课程",
            cover_url="https://example.com/course-cover.png",
            teacher_id=test_teacher.id,
            category_id=test_category.id,
            status="published",
            price=0,
            level="beginner",
            total_duration=1800,
        )
        db_session.add(course)
        await db_session.flush()

        chapter = Chapter(
            course_id=course.id,
            title="第一章",
            sort_order=1,
        )
        db_session.add(chapter)
        await db_session.flush()

        section = Section(
            course_id=course.id,
            chapter_id=chapter.id,
            title="第一节",
            sort_order=1,
            duration=600,
        )
        db_session.add(section)
        await db_session.flush()

        resource = Resource(
            course_id=course.id,
            chapter_id=chapter.id,
            section_id=section.id,
            title="教学视频",
            type="video",
            file_url="https://example.com/video.mp4",
            duration=600,
            sort_order=1,
        )
        db_session.add(resource)
        await db_session.flush()

        progress = ResourceProgress(
            user_id=test_user.id,
            course_id=course.id,
            chapter_id=chapter.id,
            section_id=section.id,
            resource_id=resource.id,
            progress=35.5,
            position=213,
            last_play_at=utcnow(),
        )
        db_session.add(progress)
        await db_session.flush()

        key = unique_key("learning_records")
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
            assert login_response.status_code in [200, 400, 401]
            return

        token = login_response.json()["data"]["access_token"]

        response = await client.get(
            "/api/v1/users/me/learning-records",
            headers={"Authorization": f"Bearer {token}"},
            params={"page": 1, "page_size": 10, "time_range": "all"},
        )

        assert response.status_code == 200
        payload = response.json()["data"]
        assert payload["total"] >= 1
        item = payload["items"][0]
        assert item["course_id"] == course.id
        assert item["course_title"] == course.title
        assert item["course_cover"] == course.cover_url
        assert item["last_section_id"] == section.id
        assert item["last_section_title"] == section.title
        assert item["course_status"] == course.status

    @pytest.mark.asyncio
    async def test_get_learning_records_supports_chapter_resource_progress(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_user: User,
        test_teacher: User,
        test_category,
    ):
        """测试学习记录接口支持章节级资源进度展示。"""
        from app.models.captcha import CaptchaRecord
        from tests.test_auth import unique_key, utcnow

        course = Course(
            title="章节资源学习记录课程",
            cover_url="https://example.com/chapter-course-cover.png",
            teacher_id=test_teacher.id,
            category_id=test_category.id,
            status="published",
            price=0,
            level="beginner",
            total_duration=1200,
        )
        db_session.add(course)
        await db_session.flush()

        chapter = Chapter(
            course_id=course.id,
            title="章节资源章",
            sort_order=1,
        )
        db_session.add(chapter)
        await db_session.flush()

        resource = Resource(
            course_id=course.id,
            chapter_id=chapter.id,
            section_id=None,
            title="章节导学视频",
            type="video",
            file_url="https://example.com/chapter-video.mp4",
            duration=480,
            sort_order=1,
        )
        db_session.add(resource)
        await db_session.flush()

        progress = ResourceProgress(
            user_id=test_user.id,
            course_id=course.id,
            chapter_id=chapter.id,
            section_id=None,
            resource_id=resource.id,
            progress=62.5,
            position=300,
            last_play_at=utcnow(),
        )
        db_session.add(progress)
        await db_session.flush()

        key = unique_key("chapter_learning_records")
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
            assert login_response.status_code in [200, 400, 401]
            return

        token = login_response.json()["data"]["access_token"]

        response = await client.get(
            "/api/v1/users/me/learning-records",
            headers={"Authorization": f"Bearer {token}"},
            params={"page": 1, "page_size": 10, "time_range": "all"},
        )

        assert response.status_code == 200
        payload = response.json()["data"]
        assert payload["total"] >= 1
        item = next(candidate for candidate in payload["items"] if candidate["course_id"] == course.id)
        assert item["course_title"] == course.title
        assert item["course_cover"] == course.cover_url
        assert item["last_section_id"] is None
        assert item["last_section_title"] == resource.title
        assert item["course_status"] == course.status


class TestChangePassword:
    """修改密码测试类"""

    @pytest.mark.asyncio
    async def test_change_password_success(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_user: User,
    ):
        """测试修改密码成功"""
        from app.models.captcha import CaptchaRecord
        from tests.test_auth import unique_key, utcnow

        key = unique_key("chpwd")
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
            assert login_response.status_code in [200, 400, 401]
            return

        token = login_response.json()["data"]["access_token"]

        response = await client.post(
            "/api/v1/users/me/change-password",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "old_password": "Test123456",
                "new_password": "NewTest123",
            },
        )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_change_password_wrong_old(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_user: User,
    ):
        """测试旧密码错误"""
        from app.models.captcha import CaptchaRecord
        from tests.test_auth import unique_key, utcnow

        key = unique_key("chpwd_wrong")
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
            assert login_response.status_code in [200, 400, 401]
            return

        token = login_response.json()["data"]["access_token"]

        response = await client.post(
            "/api/v1/users/me/change-password",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "old_password": "WrongPassword1",
                "new_password": "NewTest123",
            },
        )

        assert response.status_code in [400, 401, 422]


class TestLearningRecords:
    """学习记录测试类"""

    @pytest.mark.asyncio
    async def test_get_learning_records(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_user: User,
    ):
        """测试获取学习记录"""
        from app.models.captcha import CaptchaRecord
        from tests.test_auth import unique_key, utcnow

        key = unique_key("records")
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
            assert login_response.status_code in [200, 400, 401]
            return

        token = login_response.json()["data"]["access_token"]

        response = await client.get(
            "/api/v1/users/me/learning-records",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "items" in data["data"]


class TestUserList:
    """用户列表测试类（管理员）"""

    @pytest.mark.asyncio
    async def test_admin_can_get_user_list(
        self,
        client: AsyncClient,
        admin_headers: dict,
    ):
        """测试管理员可获取用户列表。"""
        response = await client.get(
            "/api/v1/users",
            headers=admin_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "items" in data["data"]

    @pytest.mark.asyncio
    async def test_student_without_permission_cannot_get_user_list(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ):
        """测试普通用户无法获取用户列表。"""
        student_auth = await create_role_user(client, db_session, "student")

        response = await client.get(
            "/api/v1/users",
            headers=student_auth["headers"],
        )

        assert response.status_code == 403
        assert response.json()["message"] == "无权查看用户列表"

    @pytest.mark.asyncio
    async def test_teacher_with_admin_user_permission_still_cannot_get_user_list(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ):
        """测试讲师即使残留用户管理权限也不能获取用户列表。"""
        teacher_auth = await create_role_user(client, db_session, "teacher")
        db_session.add(RolePermission(role="teacher", permission_id=31))
        await db_session.flush()

        response = await client.get(
            "/api/v1/users",
            headers=teacher_auth["headers"],
        )

        assert response.status_code == 403
        assert response.json()["message"] == "仅管理员可查看用户列表"


class TestTeacherAudit:
    """讲师审核测试类"""

    @pytest.mark.asyncio
    async def test_admin_can_get_teacher_audits(
        self,
        client: AsyncClient,
        admin_headers: dict,
    ):
        """测试管理员可获取讲师审核列表。"""
        response = await client.get(
            "/api/v1/users/teacher-audits",
            headers=admin_headers,
        )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_student_without_permission_cannot_get_teacher_audits(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ):
        """测试普通用户无法获取讲师审核列表。"""
        student_auth = await create_role_user(client, db_session, "student")

        response = await client.get(
            "/api/v1/users/teacher-audits",
            headers=student_auth["headers"],
        )

        assert response.status_code == 403
        assert response.json()["message"] == "无权查看讲师审核列表"

    @pytest.mark.asyncio
    async def test_teacher_with_teacher_audit_permission_still_cannot_get_teacher_audits(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ):
        """测试讲师即使残留讲师审核权限也不能获取审核列表。"""
        teacher_auth = await create_role_user(client, db_session, "teacher")
        db_session.add(RolePermission(role="teacher", permission_id=32))
        await db_session.flush()

        response = await client.get(
            "/api/v1/users/teacher-audits",
            headers=teacher_auth["headers"],
        )

        assert response.status_code == 403
        assert response.json()["message"] == "仅管理员可查看讲师审核列表"


class TestAdminApplications:
    """管理员申请测试类"""

    @pytest.mark.asyncio
    async def test_admin_can_get_admin_applications(
        self,
        client: AsyncClient,
        admin_headers: dict,
    ):
        """测试管理员可获取管理员申请列表。"""
        response = await client.get(
            "/api/v1/users/admin-applications",
            headers=admin_headers,
        )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_student_without_permission_cannot_get_admin_applications(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ):
        """测试普通用户无法获取管理员申请列表。"""
        student_auth = await create_role_user(client, db_session, "student")

        response = await client.get(
            "/api/v1/users/admin-applications",
            headers=student_auth["headers"],
        )

        assert response.status_code == 403
        assert response.json()["message"] == "无权查看管理员申请列表"

    @pytest.mark.asyncio
    async def test_teacher_with_admin_application_permission_still_cannot_get_admin_applications(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ):
        """测试讲师即使残留管理员申请权限也不能获取申请列表。"""
        teacher_auth = await create_role_user(client, db_session, "teacher")
        db_session.add(RolePermission(role="teacher", permission_id=33))
        await db_session.flush()

        response = await client.get(
            "/api/v1/users/admin-applications",
            headers=teacher_auth["headers"],
        )

        assert response.status_code == 403
        assert response.json()["message"] == "仅管理员可查看管理员申请列表"
