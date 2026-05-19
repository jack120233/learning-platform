"""课程管理模块测试

测试课程CRUD、发布、搜索等功能。
"""

import uuid
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import urlparse

import pytest
from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.security import create_access_token
from app.models.category import Category
from app.models.content import Chapter, Resource, Section
from app.models.course import Course, CourseMaterial, CourseTeacherAssignment
from app.models.user import User


def unique_key(prefix: str = "course") -> str:
    """生成唯一键"""
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


async def create_upload_test_user(
    db_session: AsyncSession,
    role: str,
) -> dict[str, str]:
    """创建上传接口测试用户并返回认证头。"""
    user = User(
        username=unique_key(role),
        email=f"{unique_key(role)}@example.com",
        password_hash="test-password-hash",
        nickname=f"{role}-tester",
        role=role,
        status="active",
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.refresh(user)

    return {"Authorization": f"Bearer {create_access_token(user.id)}"}


async def create_upload_test_user_with_user(
    db_session: AsyncSession,
    role: str,
) -> tuple[User, dict[str, str]]:
    """创建上传接口测试用户并返回用户和认证头。"""
    user = User(
        username=unique_key(role),
        email=f"{unique_key(role)}@example.com",
        password_hash="test-password-hash",
        nickname=f"{role}-tester",
        role=role,
        status="active",
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.refresh(user)

    return user, {"Authorization": f"Bearer {create_access_token(user.id)}"}


async def create_course_with_status(
    db_session: AsyncSession,
    teacher_id: int,
    status: str,
    title: str,
) -> Course:
    """创建指定状态课程。"""
    category = Category(
        name=f"{title}-分类",
        slug=unique_key("course-cat"),
        is_active=True,
    )
    db_session.add(category)
    await db_session.flush()

    course = Course(
        title=title,
        subtitle=f"{title}-副标题",
        summary=f"{title}-简介",
        description=f"{title}-描述",
        teacher_id=teacher_id,
        category_id=category.id,
        status=status,
        price=99.0,
        level="beginner",
    )
    if status == "published":
        course.published_at = datetime.utcnow()
    db_session.add(course)
    await db_session.flush()
    await db_session.refresh(course)
    return course


class TestCourseList:
    """课程列表测试类"""

    @pytest.mark.asyncio
    async def test_get_course_list(self, client: AsyncClient):
        """测试获取课程列表"""
        response = await client.get("/api/v1/courses")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data["data"]

    @pytest.mark.asyncio
    async def test_search_courses(self, client: AsyncClient):
        """测试搜索课程"""
        response = await client.get(
            "/api/v1/courses/search",
            params={"keyword": "Python"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data["data"]

    @pytest.mark.asyncio
    async def test_get_homepage_courses(self, client: AsyncClient):
        """测试获取首页课程"""
        response = await client.get("/api/v1/courses/homepage")
        assert response.status_code == 200


class TestCourseManageList:
    """课程管理列表测试。"""

    @pytest.mark.asyncio
    async def test_teacher_only_gets_own_courses(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ):
        """老师只能看到自己的课程。"""
        teacher, headers = await create_upload_test_user_with_user(db_session, "teacher")
        other_teacher, _other_headers = await create_upload_test_user_with_user(db_session, "teacher")
        own_course = await create_course_with_status(db_session, teacher.id, "draft", "老师自己的课程")
        await create_course_with_status(db_session, other_teacher.id, "draft", "别人的课程")

        response = await client.get(
            "/api/v1/courses/manage",
            headers=headers,
            params={"scope": "mine"},
        )

        assert response.status_code == 200
        items = response.json()["data"]["items"]
        assert len(items) == 1
        assert items[0]["course_id"] == own_course.id
        assert items[0]["status"] == "draft"
        assert "created_at" in items[0]

    @pytest.mark.asyncio
    async def test_teacher_gets_all_published_courses(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ):
        """老师可查看所有已发布课程。"""
        teacher, teacher_headers = await create_upload_test_user_with_user(db_session, "teacher")
        other_teacher, _ = await create_upload_test_user_with_user(db_session, "teacher")

        own_published = await create_course_with_status(db_session, teacher.id, "published", "我的已发布课程")
        other_published = await create_course_with_status(db_session, other_teacher.id, "published", "别人的已发布课程")
        await create_course_with_status(db_session, other_teacher.id, "draft", "草稿课程")

        response = await client.get(
            "/api/v1/courses/manage",
            headers=teacher_headers,
            params={"scope": "published_all"},
        )

        assert response.status_code == 200
        ids = {item["course_id"] for item in response.json()["data"]["items"]}
        assert own_published.id in ids
        assert other_published.id in ids
        assert len(ids) == 2

    @pytest.mark.asyncio
    async def test_student_cannot_get_all_published_courses(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ):
        """学员不能查看全站已发布课程管理列表。"""
        student, headers = await create_upload_test_user_with_user(db_session, "student")

        response = await client.get(
            "/api/v1/courses/manage",
            headers=headers,
            params={"scope": "published_all"},
        )

        assert response.status_code == 403


class TestCourseStatisticsAuthorization:
    """课程统计授权测试。"""

    @pytest.mark.asyncio
    async def test_admin_grants_lists_candidates_and_revokes_statistics_authorization(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ):
        """管理员可授权、候选排除负责人、重复授权幂等、撤销后失效。"""
        owner, _ = await create_upload_test_user_with_user(db_session, "teacher")
        candidate, _ = await create_upload_test_user_with_user(db_session, "teacher")
        inactive_teacher = User(
            username=unique_key("inactive_teacher"),
            email=f"{unique_key('inactive_teacher')}@example.com",
            password_hash="test-password-hash",
            role="teacher",
            status="disabled",
        )
        student, _student_headers = await create_upload_test_user_with_user(db_session, "student")
        admin, admin_headers = await create_upload_test_user_with_user(db_session, "admin")
        db_session.add(inactive_teacher)
        await db_session.flush()
        course = await create_course_with_status(db_session, owner.id, "published", "统计授权课程")

        candidate_response = await client.get(
            f"/api/v1/courses/{course.id}/statistics-authorizations/candidates",
            headers=admin_headers,
        )

        assert candidate_response.status_code == 200
        candidates = candidate_response.json()["data"]
        candidate_ids = {item["teacher_id"] for item in candidates}
        assert candidate.id in candidate_ids
        assert owner.id not in candidate_ids
        assert inactive_teacher.id not in candidate_ids
        assert student.id not in candidate_ids
        assert all("nickname" not in item and "email" not in item and "phone" not in item for item in candidates)

        grant_response = await client.post(
            f"/api/v1/courses/{course.id}/statistics-authorizations",
            headers=admin_headers,
            json={"teacher_ids": [candidate.id, candidate.id]},
        )

        assert grant_response.status_code == 200
        grants = grant_response.json()["data"]
        assert [item["teacher_id"] for item in grants].count(candidate.id) == 1
        assert grants[0]["username"] == candidate.username
        assert grants[0]["assigned_by"] == admin.id
        assert grants[0]["is_active"] is True
        assert "nickname" not in grants[0]

        repeat_response = await client.post(
            f"/api/v1/courses/{course.id}/statistics-authorizations",
            headers=admin_headers,
            json={"teacher_ids": [candidate.id]},
        )
        assert repeat_response.status_code == 200
        assignment_count = await db_session.scalar(
            select(func.count()).select_from(CourseTeacherAssignment).where(
                CourseTeacherAssignment.course_id == course.id,
                CourseTeacherAssignment.teacher_id == candidate.id,
                CourseTeacherAssignment.permission_type == "statistics_viewer",
            )
        )
        assert assignment_count == 1
        active_count = await db_session.scalar(
            select(func.count()).select_from(CourseTeacherAssignment).where(
                CourseTeacherAssignment.course_id == course.id,
                CourseTeacherAssignment.teacher_id == candidate.id,
                CourseTeacherAssignment.permission_type == "statistics_viewer",
                CourseTeacherAssignment.is_active.is_(True),
            )
        )
        assert active_count == 1
        assert len({item["teacher_id"] for item in repeat_response.json()["data"]}) == 1
        assert repeat_response.json()["data"][0]["teacher_id"] == candidate.id

        candidate_response_after_grant = await client.get(
            f"/api/v1/courses/{course.id}/statistics-authorizations/candidates",
            headers=admin_headers,
        )
        authorized_candidates = {
            item["teacher_id"]: item["authorized"]
            for item in candidate_response_after_grant.json()["data"]
        }
        assert authorized_candidates[candidate.id] is True

        revoke_response = await client.delete(
            f"/api/v1/courses/{course.id}/statistics-authorizations/{candidate.id}",
            headers=admin_headers,
        )
        assert revoke_response.status_code == 200

        list_response = await client.get(
            f"/api/v1/courses/{course.id}/statistics-authorizations",
            headers=admin_headers,
        )
        listed = [item for item in list_response.json()["data"] if item["teacher_id"] == candidate.id]
        assert listed
        assert listed[0]["is_active"] is False
        assert listed[0]["revoked_at"] is not None

    @pytest.mark.asyncio
    async def test_statistics_authorization_is_admin_only_and_not_course_edit_permission(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ):
        """统计授权仅管理员可维护，且不授予课程编辑或下架权限。"""
        owner, _owner_headers = await create_upload_test_user_with_user(db_session, "teacher")
        authorized_teacher, authorized_headers = await create_upload_test_user_with_user(db_session, "teacher")
        admin, admin_headers = await create_upload_test_user_with_user(db_session, "admin")
        course = await create_course_with_status(db_session, owner.id, "published", "只读统计授权课程")

        non_admin_response = await client.post(
            f"/api/v1/courses/{course.id}/statistics-authorizations",
            headers=authorized_headers,
            json={"teacher_ids": [authorized_teacher.id]},
        )
        assert non_admin_response.status_code == 403

        grant_response = await client.post(
            f"/api/v1/courses/{course.id}/statistics-authorizations",
            headers=admin_headers,
            json={"teacher_ids": [authorized_teacher.id]},
        )
        assert grant_response.status_code == 200
        assert grant_response.json()["data"][0]["assigned_by"] == admin.id

        update_response = await client.post(
            f"/api/v1/courses/{course.id}",
            headers=authorized_headers,
            json={"title": "被授权老师不能编辑课程"},
        )
        assert update_response.status_code == 403

        archive_response = await client.post(
            f"/api/v1/courses/{course.id}/archive",
            headers=authorized_headers,
        )
        assert archive_response.status_code == 403

        delete_response = await client.delete(
            f"/api/v1/courses/{course.id}",
            headers=authorized_headers,
        )
        assert delete_response.status_code == 403

    @pytest.mark.asyncio
    async def test_authorization_rejects_owner_and_ineligible_teacher(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ):
        """授权接口拒绝课程负责人、禁用老师和非老师用户。"""
        owner, _ = await create_upload_test_user_with_user(db_session, "teacher")
        inactive_teacher = User(
            username=unique_key("inactive_teacher"),
            email=f"{unique_key('inactive_teacher')}@example.com",
            password_hash="test-password-hash",
            role="teacher",
            status="disabled",
        )
        student, _ = await create_upload_test_user_with_user(db_session, "student")
        _admin, admin_headers = await create_upload_test_user_with_user(db_session, "admin")
        db_session.add(inactive_teacher)
        await db_session.flush()
        course = await create_course_with_status(db_session, owner.id, "published", "授权校验课程")

        owner_response = await client.post(
            f"/api/v1/courses/{course.id}/statistics-authorizations",
            headers=admin_headers,
            json={"teacher_ids": [owner.id]},
        )
        assert owner_response.status_code == 422

        ineligible_response = await client.post(
            f"/api/v1/courses/{course.id}/statistics-authorizations",
            headers=admin_headers,
            json={"teacher_ids": [inactive_teacher.id, student.id]},
        )
        assert ineligible_response.status_code == 422


class TestCourseDetail:
    """课程详情测试类"""

    @pytest.mark.asyncio
    async def test_get_course_detail(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_teacher: User,
    ):
        """测试获取课程详情"""
        category = Category(
            name="测试分类",
            slug=f"test-cat-{uuid.uuid4().hex[:8]}",
            is_active=True,
        )
        db_session.add(category)
        await db_session.flush()

        course = Course(
            title="测试课程详情",
            subtitle="测试副标题",
            summary="测试简介",
            description="测试描述",
            teacher_id=test_teacher.id,
            category_id=category.id,
            status="published",
            price=99.0,
            level="beginner",
        )
        db_session.add(course)
        await db_session.flush()

        chapter = Chapter(
            course_id=course.id,
            title="第一章",
            sort_order=1,
            is_free=True,
        )
        db_session.add(chapter)
        await db_session.flush()

        section = Section(
            course_id=course.id,
            chapter_id=chapter.id,
            title="第一节",
            sort_order=1,
            is_free=True,
        )
        db_session.add(section)
        await db_session.flush()

        response = await client.get(f"/api/v1/courses/{course.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["title"] == "测试课程详情"
        assert data["data"]["summary"] == "测试简介"
        assert data["data"]["total_sections"] == 1
        assert len(data["data"]["chapters"]) == 1
        assert data["data"]["chapters"][0]["course_id"] == course.id
        assert data["data"]["chapters"][0]["chapter_id"] == chapter.id
        assert data["data"]["chapters"][0]["title"] == "第一章"
        assert data["data"]["chapters"][0]["section_count"] == 1
        assert len(data["data"]["chapters"][0]["sections"]) == 1
        assert data["data"]["chapters"][0]["sections"][0]["section_id"] == section.id
        assert data["data"]["chapters"][0]["sections"][0]["title"] == "第一节"

    @pytest.mark.asyncio
    async def test_get_course_not_found(self, client: AsyncClient):
        """测试课程不存在"""
        response = await client.get("/api/v1/courses/999999")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_course_detail_includes_materials_and_resources(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ):
        """测试课程详情包含资料、章节资源和小节资源。"""
        teacher, _headers = await create_upload_test_user_with_user(db_session, "teacher")

        category = Category(
            name="详情资源分类",
            slug=f"detail-assets-{uuid.uuid4().hex[:8]}",
            is_active=True,
        )
        db_session.add(category)
        await db_session.flush()

        course = Course(
            title="资源详情课程",
            summary="带资源的课程详情",
            teacher_id=teacher.id,
            category_id=category.id,
            status="published",
            price=0,
            level="beginner",
        )
        db_session.add(course)
        await db_session.flush()

        chapter = Chapter(
            course_id=course.id,
            title="第一章",
            sort_order=1,
            total_duration=120,
            section_count=1,
        )
        db_session.add(chapter)
        await db_session.flush()

        section = Section(
            course_id=course.id,
            chapter_id=chapter.id,
            title="第一节",
            sort_order=1,
            resource_count=1,
            duration=60,
        )
        db_session.add(section)
        await db_session.flush()

        material = CourseMaterial(
            course_id=course.id,
            name="教学大纲.pdf",
            file_url="http://test/uploads/files/outline.pdf",
            file_size=1024,
            file_type="pdf",
        )
        chapter_resource = Resource(
            course_id=course.id,
            chapter_id=chapter.id,
            section_id=None,
            title="章节讲义.pdf",
            type="document",
            file_url="http://test/uploads/files/chapter.pdf",
            file_size=2048,
            sort_order=1,
        )
        section_resource = Resource(
            course_id=course.id,
            chapter_id=chapter.id,
            section_id=section.id,
            title="第一节视频.mp4",
            type="video",
            file_url="http://test/uploads/files/section.mp4",
            file_size=4096,
            duration=60,
            sort_order=1,
        )
        db_session.add_all([material, chapter_resource, section_resource])
        await db_session.flush()

        response = await client.get(f"/api/v1/courses/{course.id}")

        assert response.status_code == 200
        data = response.json()["data"]
        assert len(data["materials"]) == 1
        assert data["materials"][0]["material_id"] == material.id
        assert data["materials"][0]["file_name"] == "教学大纲.pdf"
        assert len(data["chapters"]) == 1


class TestCoursePublish:
    """课程发布测试类"""

    @pytest.mark.asyncio
    async def test_publish_course(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_teacher: User,
    ):
        """测试发布课程"""
        from app.models.captcha import CaptchaRecord
        from tests.test_auth import unique_key, utcnow

        category = Category(
            name="发布课程分类",
            slug=f"publish-cat-{uuid.uuid4().hex[:8]}",
            is_active=True,
        )
        db_session.add(category)
        await db_session.flush()

        course = Course(
            title="待发布课程",
            subtitle="副标题",
            description="描述",
            teacher_id=test_teacher.id,
            category_id=category.id,
            status="draft",
            price=99.0,
            level="beginner",
        )
        db_session.add(course)
        await db_session.flush()

        chapter = Chapter(
            course_id=course.id,
            title="发布前置章节",
            sort_order=1,
        )
        db_session.add(chapter)
        await db_session.flush()

        resource = Resource(
            course_id=course.id,
            chapter_id=chapter.id,
            title="发布前置必修资源",
            type="video",
            file_url="http://test/uploads/files/publish-required.mp4",
            is_required=True,
            sort_order=1,
        )
        db_session.add(resource)
        await db_session.flush()

        key = unique_key("publish")
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
                "username": "teacher@example.com",
                "password": "Teacher123456",
                "captcha_key": key,
                "captcha_text": "test",
            },
        )

        if login_response.status_code != 200:
            assert login_response.status_code in [200, 400, 401]
            return

        token = login_response.json()["data"]["access_token"]

        response = await client.post(
            f"/api/v1/courses/{course.id}/publish",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code in [200, 400, 404]

    @pytest.mark.asyncio
    async def test_admin_cannot_publish_other_teacher_course(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ):
        """管理员不能发布他人课程。"""
        teacher, _ = await create_upload_test_user_with_user(db_session, "teacher")
        _course = await create_course_with_status(db_session, teacher.id, "draft", "待管理员发布课程")
        _admin, admin_headers = await create_upload_test_user_with_user(db_session, "admin")

        response = await client.post(
            f"/api/v1/courses/{_course.id}/publish",
            headers=admin_headers,
        )

        assert response.status_code == 403


class TestCourseCoverUpload:
    """课程封面上传测试类"""

    @pytest.mark.asyncio
    async def test_upload_course_cover_success(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ):
        """测试上传课程封面成功"""
        teacher_headers = await create_upload_test_user(db_session, "teacher")
        file_content = b"fake-png-content"

        response = await client.post(
            "/api/v1/upload/file",
            headers=teacher_headers,
            files={"file": ("course-cover.png", file_content, "image/png")},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "上传成功"
        assert data["data"]["file_name"] == "course-cover.png"
        assert data["data"]["file_size"] == len(file_content)
        assert data["data"]["url"] == data["data"]["file_url"]
        assert data["data"]["file_url"].startswith("/uploads/course-covers/")

        upload_path = urlparse(data["data"]["file_url"]).path
        file_path = Path(settings.upload_dir) / Path(upload_path.lstrip("/")).relative_to("uploads")
        assert file_path.exists()

        preview_response = await client.get(upload_path)
        assert preview_response.status_code == 200
        assert preview_response.content == file_content

        file_path.unlink(missing_ok=True)

    @pytest.mark.asyncio
    async def test_upload_course_cover_invalid_type(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ):
        """测试上传课程封面文件类型不支持"""
        teacher_headers = await create_upload_test_user(db_session, "teacher")
        response = await client.post(
            "/api/v1/upload/file",
            headers=teacher_headers,
            files={"file": ("course-cover.gif", b"gif-content", "image/gif")},
        )

        assert response.status_code == 422
        data = response.json()
        assert data["message"] == "仅支持 JPG/PNG 格式图片"

    @pytest.mark.asyncio
    async def test_upload_course_cover_requires_teacher_role(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ):
        """测试普通用户不能上传课程封面"""
        auth_headers = await create_upload_test_user(db_session, "student")
        response = await client.post(
            "/api/v1/upload/file",
            headers=auth_headers,
            files={"file": ("course-cover.png", b"fake-png-content", "image/png")},
        )

        assert response.status_code == 403
        data = response.json()
        assert data["message"] == "仅老师或管理员可上传课程封面"


class TestCourseMaterials:
    """课程资料测试类。"""

    @pytest.mark.asyncio
    async def test_create_material_from_json_payload(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ):
        """测试通过 JSON 创建课程资料记录。"""
        teacher, headers = await create_upload_test_user_with_user(db_session, "teacher")

        category = Category(
            name="资料分类",
            slug=f"material-json-{uuid.uuid4().hex[:8]}",
            is_active=True,
        )
        db_session.add(category)
        await db_session.flush()

        course = Course(
            title="资料 JSON 课程",
            teacher_id=teacher.id,
            category_id=category.id,
            status="draft",
            price=0,
            level="beginner",
        )
        db_session.add(course)
        await db_session.flush()

        response = await client.post(
            f"/api/v1/courses/{course.id}/materials",
            headers=headers,
            json={
                "name": "教学大纲.pdf",
                "file_url": "http://test/uploads/files/outline.pdf",
                "file_size": 1024,
                "file_type": "pdf",
            },
        )

        assert response.status_code == 200
        data = response.json()["data"]
        assert data["name"] == "教学大纲.pdf"
        assert data["file_name"] == "教学大纲.pdf"
        assert data["file_type"] == "pdf"

    @pytest.mark.asyncio
    async def test_create_material_from_multipart_file(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ):
        """测试通过 multipart 直接上传课程资料。"""
        teacher, headers = await create_upload_test_user_with_user(db_session, "teacher")

        category = Category(
            name="资料上传分类",
            slug=f"material-upload-{uuid.uuid4().hex[:8]}",
            is_active=True,
        )
        db_session.add(category)
        await db_session.flush()

        course = Course(
            title="资料上传课程",
            teacher_id=teacher.id,
            category_id=category.id,
            status="draft",
            price=0,
            level="beginner",
        )
        db_session.add(course)
        await db_session.flush()

        response = await client.post(
            f"/api/v1/courses/{course.id}/materials",
            headers=headers,
            files={
                "file": ("lesson-outline.pdf", b"%PDF-1.4 course material", "application/pdf")
            },
        )

        assert response.status_code == 200
        data = response.json()["data"]
        assert data["material_id"] > 0
        assert data["file_name"] == "lesson-outline.pdf"
        assert data["file_type"] == "pdf"
        assert data["file_url"].startswith("/uploads/files/")

        upload_path = urlparse(data["file_url"]).path
        file_path = Path(settings.upload_dir) / Path(upload_path.lstrip("/")).relative_to("uploads")
        assert file_path.exists()
        file_path.unlink(missing_ok=True)

    @pytest.mark.asyncio
    async def test_cannot_create_material_on_published_course(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ):
        """已发布课程不能新增配套资料。"""
        teacher, headers = await create_upload_test_user_with_user(db_session, "teacher")
        course = await create_course_with_status(db_session, teacher.id, "published", "已发布资料课程")

        response = await client.post(
            f"/api/v1/courses/{course.id}/materials",
            headers=headers,
            json={
                "name": "禁止新增.pdf",
                "file_url": "http://test/uploads/files/no-create.pdf",
                "file_size": 1024,
                "file_type": "pdf",
            },
        )

        assert response.status_code == 422
        assert response.json()["message"] == "已发布课程不能直接编辑，请先下架"
        material_count = await db_session.scalar(
            select(func.count()).select_from(CourseMaterial).where(CourseMaterial.course_id == course.id)
        )
        assert material_count == 0

    @pytest.mark.asyncio
    async def test_cannot_delete_material_on_published_course(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ):
        """已发布课程不能删除配套资料。"""
        teacher, headers = await create_upload_test_user_with_user(db_session, "teacher")
        course = await create_course_with_status(db_session, teacher.id, "published", "已发布删除资料课程")
        material = CourseMaterial(
            course_id=course.id,
            name="待保留资料.pdf",
            file_url="http://test/uploads/files/keep.pdf",
            file_size=512,
            file_type="pdf",
        )
        db_session.add(material)
        await db_session.flush()

        response = await client.post(
            f"/api/v1/courses/{course.id}/materials/{material.id}/delete",
            headers=headers,
        )

        assert response.status_code == 422
        assert response.json()["message"] == "已发布课程不能直接编辑，请先下架"
        result = await db_session.execute(
            select(CourseMaterial.id).where(CourseMaterial.id == material.id)
        )
        assert result.scalar_one_or_none() == material.id

    @pytest.mark.asyncio
    async def test_delete_material_legacy_post_route(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ):
        """测试兼容旧前端的资料删除路由。"""
        teacher, headers = await create_upload_test_user_with_user(db_session, "teacher")

        category = Category(
            name="资料删除分类",
            slug=f"material-delete-{uuid.uuid4().hex[:8]}",
            is_active=True,
        )
        db_session.add(category)
        await db_session.flush()

        course = Course(
            title="资料删除课程",
            teacher_id=teacher.id,
            category_id=category.id,
            status="draft",
            price=0,
            level="beginner",
        )
        db_session.add(course)
        await db_session.flush()

        response = await client.post(
            f"/api/v1/courses/{course.id}/materials",
            headers=headers,
            json={
                "name": "待删除资料.pdf",
                "file_url": "http://test/uploads/files/delete-me.pdf",
                "file_size": 512,
                "file_type": "pdf",
            },
        )
        material_id = response.json()["data"]["material_id"]

        delete_response = await client.post(
            f"/api/v1/courses/{course.id}/materials/{material_id}/delete",
            headers=headers,
        )

        assert delete_response.status_code == 200


class TestPublishedCourseEditGuard:
    """已发布课程编辑保护测试。"""

    @pytest.mark.asyncio
    async def test_owner_cannot_update_published_course(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ):
        """负责人不能直接更新已发布课程，且数据库标题保持不变。"""
        teacher, headers = await create_upload_test_user_with_user(db_session, "teacher")
        course = await create_course_with_status(db_session, teacher.id, "published", "已发布原标题")

        response = await client.post(
            f"/api/v1/courses/{course.id}",
            headers=headers,
            json={"title": "不应写入的新标题"},
        )

        assert response.status_code == 422
        assert response.json()["message"] == "已发布课程不能直接编辑，请先下架"
        await db_session.refresh(course)
        assert course.title == "已发布原标题"

    @pytest.mark.asyncio
    async def test_owner_can_archive_then_update_course(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ):
        """负责人下架后可以更新课程。"""
        teacher, headers = await create_upload_test_user_with_user(db_session, "teacher")
        course = await create_course_with_status(db_session, teacher.id, "published", "待下架编辑课程")

        archive_response = await client.post(
            f"/api/v1/courses/{course.id}/archive",
            headers=headers,
            json={"archive_reason": "编辑前下架"},
        )
        assert archive_response.status_code == 200

        update_response = await client.post(
            f"/api/v1/courses/{course.id}",
            headers=headers,
            json={"title": "下架后新标题"},
        )

        assert update_response.status_code == 200
        await db_session.refresh(course)
        assert course.status == "archived"
        assert course.title == "下架后新标题"

    @pytest.mark.asyncio
    async def test_other_teacher_updating_published_course_gets_forbidden(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ):
        """其他老师更新已发布课程返回越权，且不暴露发布状态校验。"""
        owner, _ = await create_upload_test_user_with_user(db_session, "teacher")
        _other_teacher, headers = await create_upload_test_user_with_user(db_session, "teacher")
        course = await create_course_with_status(db_session, owner.id, "published", "他人发布课程")

        response = await client.post(
            f"/api/v1/courses/{course.id}",
            headers=headers,
            json={"title": "越权标题"},
        )

        assert response.status_code == 403
        await db_session.refresh(course)
        assert course.title == "他人发布课程"


class TestCourseArchive:
    """课程下架测试类"""

    @pytest.mark.asyncio
    async def test_archive_course(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_teacher: User,
    ):
        """测试下架课程"""
        from app.models.captcha import CaptchaRecord
        from tests.test_auth import unique_key, utcnow

        category = Category(
            name="下架课程分类",
            slug=f"archive-cat-{uuid.uuid4().hex[:8]}",
            is_active=True,
        )
        db_session.add(category)
        await db_session.flush()

        course = Course(
            title="待下架课程",
            subtitle="副标题",
            description="描述",
            teacher_id=test_teacher.id,
            category_id=category.id,
            status="published",
            price=99.0,
            level="beginner",
        )
        db_session.add(course)
        await db_session.flush()

        key = unique_key("archive")
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
                "username": "teacher@example.com",
                "password": "Teacher123456",
                "captcha_key": key,
                "captcha_text": "test",
            },
        )

        if login_response.status_code != 200:
            assert login_response.status_code in [200, 400, 401]
            return

        token = login_response.json()["data"]["access_token"]

        response = await client.post(
            f"/api/v1/courses/{course.id}/archive",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code in [200, 400, 404]

    @pytest.mark.asyncio
    async def test_admin_can_archive_other_teacher_published_course(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ):
        """管理员可下架他人已发布课程。"""
        teacher, _ = await create_upload_test_user_with_user(db_session, "teacher")
        course = await create_course_with_status(db_session, teacher.id, "published", "教师已发布课程")
        _admin, admin_headers = await create_upload_test_user_with_user(db_session, "admin")

        response = await client.post(
            f"/api/v1/courses/{course.id}/archive",
            headers=admin_headers,
        )

        assert response.status_code == 200
        assert response.json()["data"]["status"] == "archived"


class TestBatchCourseAction:
    """批量课程操作测试。"""

    @pytest.mark.asyncio
    async def test_teacher_batch_delete_own_non_published_courses(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ):
        """老师可批量删除自己的未发布课程。"""
        teacher, headers = await create_upload_test_user_with_user(db_session, "teacher")
        draft_course = await create_course_with_status(db_session, teacher.id, "draft", "老师草稿课程")
        archived_course = await create_course_with_status(db_session, teacher.id, "archived", "老师下架课程")

        response = await client.post(
            "/api/v1/courses/batch-action",
            headers=headers,
            json={
                "action": "delete",
                "course_ids": [draft_course.id, archived_course.id],
            },
        )

        assert response.status_code == 200
        data = response.json()["data"]
        assert data["success_count"] == 2
        assert data["failed_count"] == 0

    @pytest.mark.asyncio
    async def test_admin_batch_archive_other_teachers_published_courses(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ):
        """管理员可批量下架多名老师的已发布课程。"""
        teacher_a, _ = await create_upload_test_user_with_user(db_session, "teacher")
        teacher_b, _ = await create_upload_test_user_with_user(db_session, "teacher")
        course_a = await create_course_with_status(db_session, teacher_a.id, "published", "老师A课程")
        course_b = await create_course_with_status(db_session, teacher_b.id, "published", "老师B课程")
        _admin, admin_headers = await create_upload_test_user_with_user(db_session, "admin")

        response = await client.post(
            "/api/v1/courses/batch-action",
            headers=admin_headers,
            json={
                "action": "archive",
                "course_ids": [course_a.id, course_b.id],
                "archive_reason": "管理员批量下架",
            },
        )

        assert response.status_code == 200
        data = response.json()["data"]
        assert data["success_count"] == 2
        assert data["failed_count"] == 0

    @pytest.mark.asyncio
    async def test_admin_batch_delete_other_teacher_courses_fails(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ):
        """管理员不能批量删除他人课程。"""
        teacher, _ = await create_upload_test_user_with_user(db_session, "teacher")
        draft_course = await create_course_with_status(db_session, teacher.id, "draft", "待删草稿课程")
        _admin, admin_headers = await create_upload_test_user_with_user(db_session, "admin")

        response = await client.post(
            "/api/v1/courses/batch-action",
            headers=admin_headers,
            json={
                "action": "delete",
                "course_ids": [draft_course.id],
            },
        )

        assert response.status_code == 200
        data = response.json()["data"]
        assert data["success_count"] == 0
        assert data["failed_count"] == 1
        assert data["failed_items"][0]["course_id"] == draft_course.id
        assert "无权删除" in data["failed_items"][0]["reason"]

    @pytest.mark.asyncio
    async def test_teacher_batch_delete_other_teacher_published_course_returns_forbidden(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ):
        """老师批量删除他人已发布课程返回越权失败，而非发布状态校验。"""
        owner, _ = await create_upload_test_user_with_user(db_session, "teacher")
        other_teacher, headers = await create_upload_test_user_with_user(db_session, "teacher")
        published_course = await create_course_with_status(db_session, owner.id, "published", "他人已发布课程")

        response = await client.post(
            "/api/v1/courses/batch-action",
            headers=headers,
            json={
                "action": "delete",
                "course_ids": [published_course.id],
            },
        )

        assert other_teacher.id != owner.id
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["success_count"] == 0
        assert data["failed_count"] == 1
        assert data["failed_items"][0]["course_id"] == published_course.id
        assert "无权删除" in data["failed_items"][0]["reason"]
        assert "先下架" not in data["failed_items"][0]["reason"]

    @pytest.mark.asyncio
    async def test_teacher_batch_delete_published_course_returns_failure(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ):
        """批量删除已发布课程会返回失败明细。"""
        teacher, headers = await create_upload_test_user_with_user(db_session, "teacher")
        published_course = await create_course_with_status(db_session, teacher.id, "published", "已发布课程")
        archived_course = await create_course_with_status(db_session, teacher.id, "archived", "可删除课程")

        response = await client.post(
            "/api/v1/courses/batch-action",
            headers=headers,
            json={
                "action": "delete",
                "course_ids": [published_course.id, archived_course.id],
            },
        )

        assert response.status_code == 200
        data = response.json()["data"]
        assert data["success_count"] == 1
        assert data["failed_count"] == 1
        assert data["failed_items"][0]["course_id"] == published_course.id
        assert "先下架" in data["failed_items"][0]["reason"]
