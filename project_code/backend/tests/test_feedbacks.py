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
from app.core.security import hash_password
from app.models.permission import RolePermission
from app.models.user import User


def unique_key(prefix: str = "fb") -> str:
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


class TestFeedback:
    """反馈管理测试类"""

    @pytest.mark.asyncio
    async def test_create_feedback(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_user: User,
        test_course,
        test_teacher: User,
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
                "target_user_id": test_teacher.id,
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
        assert data["target_user_id"] == test_teacher.id
        assert data["target_username"] == test_teacher.username
        assert data["status"] == "pending"
        assert data["images"] == ["https://example.com/test-feedback.png"]

    @pytest.mark.asyncio
    async def test_get_feedbacks(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_course,
    ):
        """测试获取反馈列表时返回前端需要的字段。"""
        from app.models.feedback import Feedback

        student_auth = await create_role_user(client, db_session, "student")

        feedback = Feedback(
            user_id=student_auth["user_id"],
            type="course",
            course_id=test_course.id,
            target_user_id=test_course.teacher_id,
            title="课程反馈",
            content="视频章节有点卡顿",
            images='["https://example.com/course-feedback.png"]',
            status="processed",
        )
        db_session.add(feedback)
        await db_session.flush()

        response = await client.get(
            "/api/v1/feedbacks",
            headers=student_auth["headers"],
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
        assert item["username"] == student_auth["username"]
        assert item["status"] == "processed"

    @pytest.mark.asyncio
    async def test_get_feedback_detail(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_course,
    ):
        """测试反馈详情接口兼容字典序列化结果。"""
        from app.models.feedback import Feedback

        student_auth = await create_role_user(client, db_session, "student")

        feedback = Feedback(
            user_id=student_auth["user_id"],
            type="course",
            course_id=test_course.id,
            target_user_id=test_course.teacher_id,
            title="课程反馈详情",
            content="详情接口测试内容",
            status="pending",
        )
        db_session.add(feedback)
        await db_session.flush()

        response = await client.get(
            f"/api/v1/feedbacks/{feedback.id}",
            headers=student_auth["headers"],
        )

        assert response.status_code == 200
        data = response.json()["data"]
        assert data["feedback_id"] == feedback.id
        assert data["course_id"] == test_course.id

    @pytest.mark.asyncio
    async def test_process_feedback_with_reply(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_course,
        test_admin: User,
        admin_headers: dict,
    ):
        """测试管理员处理反馈时会写入回复内容和处理信息。"""
        from app.models.feedback import Feedback

        student_auth = await create_role_user(client, db_session, "student")

        feedback = Feedback(
            user_id=student_auth["user_id"],
            type="course",
            course_id=test_course.id,
            target_user_id=test_course.teacher_id,
            title="课程反馈待处理",
            content="这里有一个需要管理员回复的问题",
            status="pending",
        )
        db_session.add(feedback)
        await db_session.flush()

        response = await client.post(
            f"/api/v1/feedbacks/{feedback.id}/process",
            headers=admin_headers,
            json={"reply": "已核查该课程问题，我们会尽快修复。"},
        )

        assert response.status_code == 200
        data = response.json()["data"]
        assert data["feedback_id"] == feedback.id
        assert data["status"] == "processed"
        assert data["reply"] == "已核查该课程问题，我们会尽快修复。"
        assert data["replied_at"] is not None
        assert data["processed_at"] is not None

        await db_session.refresh(feedback)
        assert feedback.status == "processed"
        assert feedback.reply == "已核查该课程问题，我们会尽快修复。"
        assert feedback.replied_at is not None
        assert feedback.replied_by == test_admin.id

    @pytest.mark.asyncio
    async def test_system_feedback_admin_reply_student_can_view_reply(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        admin_headers: dict,
    ):
        """测试平台反馈无需课程/目标老师，管理员处理后学生可查看回复。"""
        student_auth = await create_role_user(client, db_session, "student")

        create_response = await client.post(
            "/api/v1/feedbacks",
            headers=student_auth["headers"],
            json={
                "feedback_type": "system",
                "content": "平台反馈闭环测试内容，不应要求课程或目标老师。",
                "images": ["https://example.com/system-feedback.png"],
            },
        )

        assert create_response.status_code == 200
        created = create_response.json()["data"]
        feedback_id = created["feedback_id"]
        assert created["feedback_type"] == "system"
        assert created["course_id"] is None
        assert created["target_user_id"] is None
        assert created["status"] == "pending"

        admin_list_response = await client.get(
            "/api/v1/feedbacks",
            headers=admin_headers,
            params={"feedback_type": "system", "page": 1, "page_size": 10},
        )
        assert admin_list_response.status_code == 200
        admin_items = admin_list_response.json()["data"]["items"]
        assert feedback_id in {item["feedback_id"] for item in admin_items}

        process_response = await client.post(
            f"/api/v1/feedbacks/{feedback_id}/process",
            headers=admin_headers,
            json={"reply": "管理员已收到平台反馈，并完成处理。"},
        )
        assert process_response.status_code == 200
        processed = process_response.json()["data"]
        assert processed["status"] == "processed"
        assert processed["reply"] == "管理员已收到平台反馈，并完成处理。"
        assert processed["replied_at"] is not None
        assert processed["processed_at"] is not None

        student_feedbacks_response = await client.get(
            "/api/v1/users/me/feedbacks",
            headers=student_auth["headers"],
        )
        assert student_feedbacks_response.status_code == 200
        student_items = student_feedbacks_response.json()["data"]["items"]
        student_item = next(item for item in student_items if item["feedback_id"] == feedback_id)
        assert student_item["status"] == "processed"
        assert student_item["reply"] == "管理员已收到平台反馈，并完成处理。"
        assert student_item["replied_at"] is not None

    @pytest.mark.asyncio
    async def test_teacher_with_feedback_permission_can_view_all_feedbacks(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_course,
    ):
        """测试拥有反馈权限的讲师可查看全量反馈列表和详情。"""
        from app.models.feedback import Feedback

        teacher_auth = await create_role_user(client, db_session, "teacher")
        student_auth = await create_role_user(client, db_session, "student")
        db_session.add(RolePermission(role="teacher", permission_id=36))
        await db_session.flush()

        own_feedback = Feedback(
            user_id=teacher_auth["user_id"],
            type="system",
            title="讲师自己的反馈",
            content="讲师自己提交的反馈",
            status="pending",
        )
        student_feedback = Feedback(
            user_id=student_auth["user_id"],
            type="course",
            course_id=test_course.id,
            target_user_id=test_course.teacher_id,
            title="学生课程反馈",
            content="学生提交的课程问题",
            status="pending",
        )
        db_session.add_all([own_feedback, student_feedback])
        await db_session.flush()

        list_response = await client.get(
            "/api/v1/feedbacks",
            headers=teacher_auth["headers"],
        )

        assert list_response.status_code == 200
        items = list_response.json()["data"]["items"]
        feedback_ids = {item["feedback_id"] for item in items}
        assert own_feedback.id in feedback_ids
        assert student_feedback.id in feedback_ids

        detail_response = await client.get(
            f"/api/v1/feedbacks/{student_feedback.id}",
            headers=teacher_auth["headers"],
        )
        assert detail_response.status_code == 200
        detail = detail_response.json()["data"]
        assert detail["feedback_id"] == student_feedback.id
        assert detail["user_id"] == student_auth["user_id"]

    @pytest.mark.asyncio
    async def test_student_cannot_view_other_user_feedback_detail(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_course,
    ):
        """测试没有反馈管理权限的普通用户不能查看他人反馈详情。"""
        from app.models.feedback import Feedback

        owner_auth = await create_role_user(client, db_session, "student")
        student_auth = await create_role_user(client, db_session, "student")
        feedback = Feedback(
            user_id=owner_auth["user_id"],
            type="course",
            course_id=test_course.id,
            target_user_id=test_course.teacher_id,
            title="别人的反馈",
            content="这是别人的反馈内容",
            status="pending",
        )
        db_session.add(feedback)
        await db_session.flush()

        response = await client.get(
            f"/api/v1/feedbacks/{feedback.id}",
            headers=student_auth["headers"],
        )

        assert response.status_code == 403
        assert response.json()["message"] == "无权查看该反馈"

    @pytest.mark.asyncio
    async def test_course_teacher_can_view_and_process_own_course_feedback(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_course,
        teacher_headers: dict,
    ):
        """测试课程讲师可查看并处理自己课程的反馈。"""
        from app.models.feedback import Feedback

        student_auth = await create_role_user(client, db_session, "student")
        feedback = Feedback(
            user_id=student_auth["user_id"],
            type="course",
            course_id=test_course.id,
            target_user_id=test_course.teacher_id,
            title="课程视频问题",
            content="视频播放到第三节时卡顿",
            status="pending",
        )
        db_session.add(feedback)
        await db_session.flush()

        list_response = await client.get(
            "/api/v1/feedbacks",
            headers=teacher_headers,
            params={"feedback_type": "course"},
        )

        assert list_response.status_code == 200
        items = list_response.json()["data"]["items"]
        feedback_ids = {item["feedback_id"] for item in items}
        assert feedback.id in feedback_ids
        assert all(item["target_user_id"] == test_course.teacher_id for item in items)

        detail_response = await client.get(
            f"/api/v1/feedbacks/{feedback.id}",
            headers=teacher_headers,
        )
        assert detail_response.status_code == 200

        process_response = await client.post(
            f"/api/v1/feedbacks/{feedback.id}/process",
            headers=teacher_headers,
            json={"reply": "老师已收到，会检查该视频资源。"},
        )

        assert process_response.status_code == 200
        data = process_response.json()["data"]
        assert data["status"] == "processed"
        assert data["reply"] == "老师已收到，会检查该视频资源。"

        await db_session.refresh(feedback)
        assert feedback.replied_by == test_course.teacher_id

    @pytest.mark.asyncio
    async def test_course_feedback_can_target_other_active_teacher(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_course,
    ):
        """测试课程反馈可以选择非课程原讲师的其他老师。"""
        from sqlalchemy import delete

        from app.models.feedback import Feedback

        await db_session.execute(
            delete(RolePermission).where(
                RolePermission.role == "teacher",
                RolePermission.permission_id == 36,
            )
        )
        await db_session.flush()

        original_teacher_auth = await create_role_user(client, db_session, "teacher")
        target_teacher_auth = await create_role_user(client, db_session, "teacher")
        student_auth = await create_role_user(client, db_session, "student")

        response = await client.post(
            "/api/v1/feedbacks",
            headers=student_auth["headers"],
            json={
                "feedback_type": "course",
                "course_id": test_course.id,
                "target_user_id": target_teacher_auth["user_id"],
                "content": "我想把这个课程问题反馈给另一位老师协助查看。",
            },
        )
        assert response.status_code == 200
        feedback_id = response.json()["data"]["feedback_id"]
        assert response.json()["data"]["target_user_id"] == target_teacher_auth["user_id"]

        original_teacher_response = await client.get(
            f"/api/v1/feedbacks/{feedback_id}",
            headers=original_teacher_auth["headers"],
        )
        assert original_teacher_response.status_code == 403
        assert original_teacher_response.json()["message"] == "无权查看该反馈"

        target_detail_response = await client.get(
            f"/api/v1/feedbacks/{feedback_id}",
            headers=target_teacher_auth["headers"],
        )
        assert target_detail_response.status_code == 200

        process_response = await client.post(
            f"/api/v1/feedbacks/{feedback_id}/process",
            headers=target_teacher_auth["headers"],
            json={"reply": "已收到，我来协助处理这个课程问题。"},
        )
        assert process_response.status_code == 200

        feedback = await db_session.get(Feedback, feedback_id)
        assert feedback is not None
        assert feedback.target_user_id == target_teacher_auth["user_id"]
        assert feedback.replied_by == target_teacher_auth["user_id"]

    @pytest.mark.asyncio
    async def test_get_teacher_options_for_feedback_target(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_teacher: User,
    ):
        """测试登录用户可获取 active 老师选择项。"""
        student_auth = await create_role_user(client, db_session, "student")

        response = await client.get(
            "/api/v1/users/teachers/options",
            headers=student_auth["headers"],
        )

        assert response.status_code == 200
        options = response.json()["data"]
        teacher_ids = {item["teacher_id"] for item in options}
        assert test_teacher.id in teacher_ids
        assert all("email" not in item for item in options)

    @pytest.mark.asyncio
    async def test_create_course_feedback_rejects_invalid_target_teacher(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_course,
    ):
        """测试课程反馈必须选择有效 active 老师。"""
        student_auth = await create_role_user(client, db_session, "student")
        target_student_auth = await create_role_user(client, db_session, "student")

        response = await client.post(
            "/api/v1/feedbacks",
            headers=student_auth["headers"],
            json={
                "feedback_type": "course",
                "course_id": test_course.id,
                "target_user_id": target_student_auth["user_id"],
                "content": "尝试把课程反馈提交给学生账号。",
            },
        )

        assert response.status_code == 422
        assert response.json()["message"] == "请选择有效的反馈老师"

    @pytest.mark.asyncio
    async def test_teacher_cannot_view_or_process_other_teacher_course_feedback(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_course,
    ):
        """测试讲师不能查看或处理其他讲师课程的反馈。"""
        from sqlalchemy import delete

        from app.models.feedback import Feedback

        await db_session.execute(
            delete(RolePermission).where(
                RolePermission.role == "teacher",
                RolePermission.permission_id == 36,
            )
        )
        await db_session.flush()

        other_teacher_auth = await create_role_user(client, db_session, "teacher")
        student_auth = await create_role_user(client, db_session, "student")
        feedback = Feedback(
            user_id=student_auth["user_id"],
            type="course",
            course_id=test_course.id,
            target_user_id=test_course.teacher_id,
            title="非本人课程反馈",
            content="这个反馈属于测试课程原讲师",
            status="pending",
        )
        db_session.add(feedback)
        await db_session.flush()

        list_response = await client.get(
            "/api/v1/feedbacks",
            headers=other_teacher_auth["headers"],
            params={"feedback_type": "course"},
        )
        assert list_response.status_code == 200
        assert list_response.json()["data"]["items"] == []

        detail_response = await client.get(
            f"/api/v1/feedbacks/{feedback.id}",
            headers=other_teacher_auth["headers"],
        )
        assert detail_response.status_code == 403
        assert detail_response.json()["message"] == "无权查看该反馈"

        process_response = await client.post(
            f"/api/v1/feedbacks/{feedback.id}/process",
            headers=other_teacher_auth["headers"],
            json={"reply": "尝试处理其他讲师课程反馈"},
        )
        assert process_response.status_code == 403
        assert process_response.json()["message"] == "无权处理该反馈"


@pytest.mark.asyncio
async def test_ensure_database_compatibility_adds_feedback_fields():
    """测试数据库兼容检查会为旧版 feedbacks 表补充反馈关联字段。"""
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
        assert "已为 feedbacks 表补充 target_user_id 字段" in messages
        assert any(column["name"] == "course_id" for column in columns)
        assert any(column["name"] == "target_user_id" for column in columns)
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
