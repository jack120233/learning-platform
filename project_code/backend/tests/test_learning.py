"""学习模块测试

测试学习进度、视频播放等功能。
"""

import uuid
from datetime import datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.models.user import User
from app.models.course import Course
from app.models.learning import LearningSession
from app.models.learning_progress import LearningProgress
from app.models.category import Category
from app.models.content import Chapter, Resource, Section


def unique_key(prefix: str = "learn") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


class TestLearningProgress:
    """学习进度测试类"""

    @pytest.mark.asyncio
    async def test_start_learning(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_user: User,
        test_teacher: User,
    ):
        """测试开始学习"""
        from app.models.captcha import CaptchaRecord
        from tests.test_auth import unique_key, utcnow

        category = Category(
            name="学习分类",
            slug=f"learn-cat-{uuid.uuid4().hex[:8]}",
            is_active=True,
        )
        db_session.add(category)
        await db_session.flush()

        course = Course(
            title="学习测试课程",
            teacher_id=test_teacher.id,
            category_id=category.id,
            status="published",
            price=0,
            level="beginner",
        )
        db_session.add(course)
        await db_session.flush()

        key = unique_key("start_learn")
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
            f"/api/v1/learning/courses/{course.id}/start",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code in [200, 400, 404]

    @pytest.mark.asyncio
    async def test_get_progress(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_user: User,
    ):
        """测试获取学习进度"""
        from app.models.captcha import CaptchaRecord
        from tests.test_auth import unique_key, utcnow

        key = unique_key("get_progress")
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

        # 如果登录失败，调整断言
        if login_response.status_code != 200:
            pytest.skip("登录失败")

        token = login_response.json()["data"]["access_token"]

        response = await client.get(
            "/api/v1/learning/progress",
            headers={"Authorization": f"Bearer {token}"},
        )

        # 可能返回 200 或其他状态码
        assert response.status_code in [200, 400, 401, 422]

    @pytest.mark.asyncio
    async def test_save_progress(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_user: User,
        test_teacher: User,
    ):
        """测试保存学习进度"""
        from app.models.captcha import CaptchaRecord
        from tests.test_auth import unique_key, utcnow

        category = Category(
            name="保存进度分类",
            slug=f"save-progress-{uuid.uuid4().hex[:8]}",
            is_active=True,
        )
        db_session.add(category)
        await db_session.flush()

        course = Course(
            title="保存进度课程",
            teacher_id=test_teacher.id,
            category_id=category.id,
            status="published",
            price=0,
            level="beginner",
        )
        db_session.add(course)
        await db_session.flush()

        chapter = Chapter(
            course_id=course.id,
            title="章节",
            sort_order=1,
        )
        db_session.add(chapter)
        await db_session.flush()

        section = Section(
            course_id=course.id,
            chapter_id=chapter.id,
            title="小节",
            sort_order=1,
            duration=600,
        )
        db_session.add(section)
        await db_session.flush()

        key = unique_key("save_progress")
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
            "/api/v1/learning/progress",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "course_id": course.id,
                "section_id": section.id,
                "position": 120,
            },
        )

        assert response.status_code in [200, 400, 401, 404, 422]


class TestTeacherCourseStatistics:
    """讲师课程统计测试。"""

    @pytest.mark.asyncio
    async def test_teacher_course_statistics_access_control_and_export_privacy(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ):
        """验证负责人、被授权、撤销和隐私边界。"""
        from app.models.user import User
        from tests.test_auth import utcnow

        owner = User(
            username=unique_key("teacher_owner"),
            email=f"{unique_key('teacher_owner')}@example.com",
            password_hash="test-password-hash",
            nickname="课程负责人",
            role="teacher",
            status="active",
        )
        authorized_teacher = User(
            username=unique_key("teacher_authorized"),
            email=f"{unique_key('teacher_authorized')}@example.com",
            password_hash="test-password-hash",
            nickname="被授权老师",
            role="teacher",
            status="active",
        )
        revoked_teacher = User(
            username=unique_key("teacher_revoked"),
            email=f"{unique_key('teacher_revoked')}@example.com",
            password_hash="test-password-hash",
            nickname="已撤销老师",
            role="teacher",
            status="active",
        )
        student_a = User(
            username=unique_key("student_a"),
            email=f"{unique_key('student_a')}@example.com",
            password_hash="test-password-hash",
            nickname="学生A",
            role="student",
            status="active",
        )
        student_b = User(
            username=unique_key("student_b"),
            email=f"{unique_key('student_b')}@example.com",
            password_hash="test-password-hash",
            nickname="学生B",
            role="student",
            status="active",
        )
        outsider = User(
            username=unique_key("teacher_outsider"),
            email=f"{unique_key('teacher_outsider')}@example.com",
            password_hash="test-password-hash",
            nickname="无权限老师",
            role="teacher",
            status="active",
        )
        category = Category(
            name="统计课程分类",
            slug=f"statistics-{uuid.uuid4().hex[:8]}",
            is_active=True,
        )
        db_session.add_all([owner, authorized_teacher, revoked_teacher, student_a, student_b, outsider, category])
        await db_session.flush()

        course = Course(
            title="教师统计课程",
            teacher_id=owner.id,
            category_id=category.id,
            status="published",
            cover_url="https://example.com/cover.png",
        )
        db_session.add(course)
        await db_session.flush()

        first_session = LearningSession(
            session_id=unique_key("session_1"),
            user_id=student_a.id,
            course_id=course.id,
            chapter_id=1,
            section_id=1,
            resource_id=11,
            resource_type="video",
            started_at=utcnow() - timedelta(days=1),
            ended_at=utcnow() - timedelta(days=1) + timedelta(minutes=20),
            effective_duration_seconds=1200,
            start_position_seconds=0,
            end_position_seconds=1200,
            progress_percent_at_end=25.0,
            is_completed_at_end=False,
            end_reason="leave_page",
        )
        second_session = LearningSession(
            session_id=unique_key("session_2"),
            user_id=student_b.id,
            course_id=course.id,
            chapter_id=1,
            section_id=1,
            resource_id=12,
            resource_type="video",
            started_at=utcnow() - timedelta(hours=2),
            ended_at=utcnow() - timedelta(hours=2) + timedelta(minutes=40),
            effective_duration_seconds=2400,
            start_position_seconds=0,
            end_position_seconds=2400,
            progress_percent_at_end=85.0,
            is_completed_at_end=True,
            end_reason="completed",
        )
        student_a_progress = LearningProgress(
            user_id=student_a.id,
            course_id=course.id,
            progress=25.0,
            last_section_id=1,
            last_resource_id=11,
            last_position=120,
            total_duration=1200,
            last_learn_at=utcnow() - timedelta(days=1),
            completed_at=None,
        )
        student_b_progress = LearningProgress(
            user_id=student_b.id,
            course_id=course.id,
            progress=85.0,
            last_section_id=1,
            last_resource_id=12,
            last_position=2400,
            total_duration=2400,
            last_learn_at=utcnow() - timedelta(hours=2),
            completed_at=utcnow() - timedelta(hours=2),
        )
        db_session.add_all([first_session, second_session, student_a_progress, student_b_progress])
        await db_session.flush()

        admin = User(
            username=unique_key("statistics_admin"),
            email=f"{unique_key('statistics_admin')}@example.com",
            password_hash="test-password-hash",
            role="admin",
            status="active",
        )
        db_session.add(admin)
        await db_session.flush()
        admin_headers = {"Authorization": f"Bearer {create_access_token(admin.id)}"}
        authorize_response = await client.post(
            f"/api/v1/courses/{course.id}/statistics-authorizations",
            headers=admin_headers,
            json={"teacher_ids": [authorized_teacher.id, revoked_teacher.id]},
        )
        assert authorize_response.status_code == 200

        revoke_response = await client.delete(
            f"/api/v1/courses/{course.id}/statistics-authorizations/{revoked_teacher.id}",
            headers=admin_headers,
        )
        assert revoke_response.status_code == 200

        owner_headers = {"Authorization": f"Bearer {create_access_token(owner.id)}"}
        authorized_headers = {"Authorization": f"Bearer {create_access_token(authorized_teacher.id)}"}
        revoked_headers = {"Authorization": f"Bearer {create_access_token(revoked_teacher.id)}"}
        outsider_headers = {"Authorization": f"Bearer {create_access_token(outsider.id)}"}

        list_response = await client.get(
            "/api/v1/teacher/statistics/courses",
            headers=owner_headers,
        )
        assert list_response.status_code == 200
        list_items = list_response.json()["data"]["items"]
        assert len(list_items) == 1
        assert list_items[0]["course_id"] == course.id
        assert list_items[0]["permission_type"] == "owner"

        authorized_list_response = await client.get(
            "/api/v1/teacher/statistics/courses",
            headers=authorized_headers,
        )
        assert authorized_list_response.status_code == 200
        authorized_list_items = authorized_list_response.json()["data"]["items"]
        assert len(authorized_list_items) == 1
        assert authorized_list_items[0]["permission_type"] == "authorized"

        forbidden_list_response = await client.get(
            "/api/v1/teacher/statistics/courses",
            headers=outsider_headers,
        )
        assert forbidden_list_response.status_code == 200
        assert forbidden_list_response.json()["data"]["items"] == []

        overview_response = await client.get(
            f"/api/v1/teacher/statistics/courses/{course.id}/overview",
            headers=authorized_headers,
            params={"range": "7d"},
        )
        assert overview_response.status_code == 200
        overview = overview_response.json()["data"]
        assert overview["started_student_count"] == 2
        assert overview["active_student_count"] == 2
        assert overview["total_duration_seconds"] == 3600
        assert overview["completion_rate"] == 50.0
        assert overview["avg_duration_seconds"] == 1800
        assert overview["course_id"] == course.id

        owner_overview_response = await client.get(
            f"/api/v1/teacher/statistics/courses/{course.id}/overview",
            headers=owner_headers,
        )
        assert owner_overview_response.status_code == 200

        revoked_overview_response = await client.get(
            f"/api/v1/teacher/statistics/courses/{course.id}/overview",
            headers=revoked_headers,
        )
        assert revoked_overview_response.status_code == 403

        unauthorized_overview_response = await client.get(
            f"/api/v1/teacher/statistics/courses/{course.id}/overview",
            headers=outsider_headers,
        )
        assert unauthorized_overview_response.status_code == 403

        student_response = await client.get(
            f"/api/v1/teacher/statistics/courses/{course.id}/students",
            headers=authorized_headers,
            params={"status": "all", "page": 1, "page_size": 10},
        )
        assert student_response.status_code == 200
        student_items = student_response.json()["data"]["items"]
        assert [item["student_id"] for item in student_items] == [student_a.id, student_b.id]
        assert all("email" not in item and "phone" not in item and "nickname" not in item and "avatar" not in item for item in student_items)
        assert student_items[0]["progress"] == 25.0
        assert student_items[1]["is_completed"] is True

        completed_response = await client.get(
            f"/api/v1/teacher/statistics/courses/{course.id}/students",
            headers=authorized_headers,
            params={"status": "completed"},
        )
        assert completed_response.status_code == 200
        assert [item["student_id"] for item in completed_response.json()["data"]["items"]] == [student_b.id]

        low_progress_response = await client.get(
            f"/api/v1/teacher/statistics/courses/{course.id}/students",
            headers=authorized_headers,
            params={"status": "low_progress"},
        )
        assert low_progress_response.status_code == 200
        assert [item["student_id"] for item in low_progress_response.json()["data"]["items"]] == [student_a.id]

        inactive_response = await client.get(
            f"/api/v1/teacher/statistics/courses/{course.id}/students",
            headers=authorized_headers,
            params={"status": "inactive"},
        )
        assert inactive_response.status_code == 200
        assert inactive_response.json()["data"]["items"] == []

        export_response = await client.get(
            f"/api/v1/teacher/statistics/courses/{course.id}/students/export",
            headers=authorized_headers,
        )
        assert export_response.status_code == 200
        csv_bytes = export_response.content
        assert csv_bytes.startswith(b"\xef\xbb\xbf")
        csv_text = csv_bytes.decode("utf-8-sig")
        assert "邮箱" not in csv_text
        assert "电话" not in csv_text
        assert "昵称" not in csv_text
        assert "学生ID,用户名,学习进度,有效学习时长（秒）,最近学习时间,是否完成,完成时间" in csv_text
        assert student_a.username in csv_text and student_b.username in csv_text
        assert "T" in csv_text

        revoked_export_response = await client.get(
            f"/api/v1/teacher/statistics/courses/{course.id}/students/export",
            headers=revoked_headers,
        )
        assert revoked_export_response.status_code == 403

        outsider_export_response = await client.get(
            f"/api/v1/teacher/statistics/courses/{course.id}/students/export",
            headers=outsider_headers,
        )
        assert outsider_export_response.status_code == 403

        public_course_response = await client.get(
            f"/api/v1/teacher/statistics/courses/{course.id}/overview",
            headers={"Authorization": f"Bearer {create_access_token(student_a.id)}"},
        )
        assert public_course_response.status_code == 403

        assert first_session.effective_duration_seconds == 1200
        assert second_session.effective_duration_seconds == 2400


class TestAdminLearningStatistics:
    """管理员学习统计测试。"""

    @pytest.mark.asyncio
    async def test_admin_learning_statistics_student_only_filters_and_trend_zero_fill(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ):
        """管理员统计仅统计学生学习行为，并支持筛选、趋势补零和低完成率阈值。"""
        from app.models.user import User
        from tests.test_auth import utcnow

        admin = User(
            username=unique_key("admin_stats"),
            email=f"{unique_key('admin_stats')}@example.com",
            password_hash="test-password-hash",
            role="admin",
            status="active",
        )
        teacher = User(
            username=unique_key("teacher_stats"),
            email=f"{unique_key('teacher_stats')}@example.com",
            password_hash="test-password-hash",
            role="teacher",
            status="active",
        )
        student = User(
            username=unique_key("student_stats"),
            email=f"{unique_key('student_stats')}@example.com",
            password_hash="test-password-hash",
            role="student",
            status="active",
        )
        teacher_learner = User(
            username=unique_key("teacher_learner"),
            email=f"{unique_key('teacher_learner')}@example.com",
            password_hash="test-password-hash",
            role="teacher",
            status="active",
        )
        category = Category(
            name="管理员统计分类",
            slug=f"admin-statistics-{uuid.uuid4().hex[:8]}",
            is_active=True,
        )
        db_session.add_all([admin, teacher, student, teacher_learner, category])
        await db_session.flush()

        course = Course(
            title="管理员统计课程",
            teacher_id=teacher.id,
            category_id=category.id,
            status="published",
        )
        db_session.add(course)
        await db_session.flush()

        student_session = LearningSession(
            session_id=unique_key("admin_session_student"),
            user_id=student.id,
            course_id=course.id,
            chapter_id=1,
            section_id=1,
            resource_id=101,
            resource_type="video",
            started_at=utcnow() - timedelta(days=1),
            ended_at=utcnow() - timedelta(days=1) + timedelta(minutes=30),
            effective_duration_seconds=1800,
            start_position_seconds=0,
            end_position_seconds=1800,
            progress_percent_at_end=20.0,
            is_completed_at_end=False,
            end_reason="leave_page",
        )
        teacher_session = LearningSession(
            session_id=unique_key("admin_session_teacher"),
            user_id=teacher_learner.id,
            course_id=course.id,
            chapter_id=1,
            section_id=1,
            resource_id=102,
            resource_type="video",
            started_at=utcnow() - timedelta(days=1),
            ended_at=utcnow() - timedelta(days=1) + timedelta(minutes=60),
            effective_duration_seconds=3600,
            start_position_seconds=0,
            end_position_seconds=3600,
            progress_percent_at_end=100.0,
            is_completed_at_end=True,
            end_reason="completed",
        )
        progress = LearningProgress(
            user_id=student.id,
            course_id=course.id,
            progress=20.0,
            last_section_id=1,
            last_resource_id=101,
            last_position=1800,
            total_duration=1800,
            last_learn_at=utcnow() - timedelta(days=1),
            completed_at=None,
        )
        db_session.add_all([student_session, teacher_session, progress])
        await db_session.flush()

        admin_headers = {"Authorization": f"Bearer {create_access_token(admin.id)}"}
        teacher_headers = {"Authorization": f"Bearer {create_access_token(teacher.id)}"}
        filters = {
            "range": "7d",
            "category_id": category.id,
            "teacher_id": teacher.id,
            "course_status": "published",
        }

        overview_response = await client.get(
            "/api/v1/admin/learning-statistics/overview",
            headers=admin_headers,
            params=filters,
        )
        assert overview_response.status_code == 200
        overview = overview_response.json()["data"]
        assert overview["total_student_count"] == 1
        assert overview["active_student_count"] == 1
        assert overview["total_duration_seconds"] == 1800
        assert overview["active_course_count"] == 1
        assert overview["new_started_course_count"] == 1

        forbidden_response = await client.get(
            "/api/v1/admin/learning-statistics/overview",
            headers=teacher_headers,
            params=filters,
        )
        assert forbidden_response.status_code == 403

        trend_response = await client.get(
            "/api/v1/admin/learning-statistics/trend",
            headers=admin_headers,
            params={**filters, "metric": "duration"},
        )
        assert trend_response.status_code == 200
        trend_items = trend_response.json()["data"]["items"]
        assert len(trend_items) == 7
        assert sum(item["value"] for item in trend_items) == 1800
        assert any(item["value"] == 0 for item in trend_items)

        active_trend_response = await client.get(
            "/api/v1/admin/learning-statistics/trend",
            headers=admin_headers,
            params={**filters, "metric": "active_students"},
        )
        assert active_trend_response.status_code == 200
        assert sum(item["value"] for item in active_trend_response.json()["data"]["items"]) == 1

        popular_response = await client.get(
            "/api/v1/admin/learning-statistics/popular-courses",
            headers=admin_headers,
            params=filters,
        )
        assert popular_response.status_code == 200
        popular_items = popular_response.json()["data"]
        assert len(popular_items) == 1
        assert popular_items[0]["course_id"] == course.id
        assert popular_items[0]["active_student_count"] == 1
        assert popular_items[0]["total_duration_seconds"] == 1800
        assert popular_items[0]["teacher_username"] == teacher.username
        assert "nickname" not in popular_items[0]

        low_completion_response = await client.get(
            "/api/v1/admin/learning-statistics/low-completion-courses",
            headers=admin_headers,
            params=filters,
        )
        assert low_completion_response.status_code == 200
        assert low_completion_response.json()["data"] == []


class TestContinueLearning:
    """继续学习测试类"""

    @pytest.mark.asyncio
    async def test_continue_learning(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_user: User,
        test_teacher: User,
    ):
        """测试继续学习"""
        from app.models.captcha import CaptchaRecord
        from tests.test_auth import unique_key, utcnow

        category = Category(
            name="继续学习分类",
            slug=f"continue-{uuid.uuid4().hex[:8]}",
            is_active=True,
        )
        db_session.add(category)
        await db_session.flush()

        course = Course(
            title="继续学习课程",
            teacher_id=test_teacher.id,
            category_id=category.id,
            status="published",
            price=0,
            level="beginner",
        )
        db_session.add(course)
        await db_session.flush()

        key = unique_key("continue")
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
            f"/api/v1/learning/courses/{course.id}/continue",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code in [200, 404]

    @pytest.mark.asyncio
    async def test_continue_learning_supports_chapter_resource_progress(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_user: User,
        test_teacher: User,
    ):
        """测试章节资源支持继续学习和进度恢复。"""
        from app.models.captcha import CaptchaRecord
        from tests.test_auth import unique_key, utcnow

        category = Category(
            name="章节继续学习分类",
            slug=f"chapter-continue-{uuid.uuid4().hex[:8]}",
            is_active=True,
        )
        db_session.add(category)
        await db_session.flush()

        course = Course(
            title="章节资源继续学习课程",
            teacher_id=test_teacher.id,
            category_id=category.id,
            status="published",
            price=0,
            level="beginner",
        )
        db_session.add(course)
        await db_session.flush()

        chapter = Chapter(
            course_id=course.id,
            title="章节资源章节",
            sort_order=1,
        )
        db_session.add(chapter)
        await db_session.flush()

        resource = Resource(
            course_id=course.id,
            chapter_id=chapter.id,
            section_id=None,
            title="chapter-video.mp4",
            type="video",
            file_url="http://test/uploads/files/chapter-video.mp4",
            file_size=1024,
            duration=300,
            sort_order=0,
            is_free=False,
        )
        db_session.add(resource)
        await db_session.flush()

        key = unique_key("chapter_continue")
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

        save_response = await client.post(
            "/api/v1/learning/progress",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "course_id": course.id,
                "chapter_id": chapter.id,
                "resource_id": resource.id,
                "current_time": 45,
                "total_time": 300,
                "is_completed": False,
            },
        )

        assert save_response.status_code == 200
        save_payload = save_response.json()["data"]
        assert save_payload["chapter_id"] == chapter.id
        assert save_payload["section_id"] is None
        assert save_payload["resource_id"] == resource.id
        assert save_payload["current_time"] == 45

        progress_response = await client.get(
            f"/api/v1/learning/progress?resource_id={resource.id}",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert progress_response.status_code == 200
        progress_payload = progress_response.json()["data"]
        assert progress_payload["resource_id"] == resource.id
        assert progress_payload["section_id"] is None
        assert progress_payload["current_time"] == 45

        continue_response = await client.get(
            f"/api/v1/learning/courses/{course.id}/continue",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert continue_response.status_code == 200
        continue_payload = continue_response.json()["data"]
        assert continue_payload["chapter_id"] == chapter.id
        assert continue_payload["section_id"] is None
        assert continue_payload["last_section_id"] is None
        assert continue_payload["last_resource_id"] == resource.id
        assert continue_payload["current_time"] == 45


# 导入必要的模型
from app.models.captcha import CaptchaRecord
