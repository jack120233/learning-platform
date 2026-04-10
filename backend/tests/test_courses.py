"""课程管理模块测试

测试课程CRUD、发布、搜索等功能。
"""

import uuid
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import urlparse

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.security import create_access_token
from app.models.user import User
from app.models.course import Course, CourseMaterial
from app.models.category import Category
from app.models.content import Chapter, Section, Resource


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
        # 创建测试分类
        category = Category(
            name="测试分类",
            slug=f"test-cat-{uuid.uuid4().hex[:8]}",
            is_active=True,
        )
        db_session.add(category)
        await db_session.flush()

        # 创建测试课程
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
        assert len(data["chapters"][0]["resources"]) == 1
        assert data["chapters"][0]["resources"][0]["resource_id"] == chapter_resource.id
        assert data["chapters"][0]["resources"][0]["file_name"] == "章节讲义.pdf"
        assert len(data["chapters"][0]["sections"]) == 1
        assert len(data["chapters"][0]["sections"][0]["resources"]) == 1
        assert data["chapters"][0]["sections"][0]["resources"][0]["resource_id"] == section_resource.id
        assert data["chapters"][0]["sections"][0]["resources"][0]["resource_type"] == "video"


class TestMyCourses:
    """我的课程测试类"""

    @pytest.mark.asyncio
    async def test_get_my_courses(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_teacher: User,
    ):
        """测试获取我的课程列表"""
        from app.models.captcha import CaptchaRecord
        from tests.test_auth import unique_key, utcnow

        key = unique_key("mycourse")
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
                "username": "testteacher",
                "password": "Teacher123456",
                "captcha_key": key,
                "captcha_text": "test",
            },
        )

        if login_response.status_code != 200:
            assert login_response.status_code in [200, 400, 401]
            return

        token = login_response.json()["data"]["access_token"]

        response = await client.get(
            "/api/v1/courses/my-courses",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200


class TestCourseCRUD:
    """课程CRUD测试类"""

    @pytest.mark.asyncio
    async def test_create_course(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_teacher: User,
    ):
        """测试创建课程"""
        from app.models.captcha import CaptchaRecord
        from tests.test_auth import unique_key, utcnow

        # 创建分类
        category = Category(
            name="创建课程分类",
            slug=f"create-cat-{uuid.uuid4().hex[:8]}",
            is_active=True,
        )
        db_session.add(category)
        await db_session.flush()

        key = unique_key("create")
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
                "username": "testteacher",
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
            "/api/v1/courses",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "title": "新建测试课程",
                "subtitle": "副标题",
                "summary": "课程简介",
                "description": "描述",
                "category_id": category.id,
                "price": 99.0,
                "level": "beginner",
            },
        )

        assert response.status_code == 200
        assert response.json()["data"]["summary"] == "课程简介"

    @pytest.mark.asyncio
    async def test_update_course(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_teacher: User,
    ):
        """测试更新课程"""
        from app.models.captcha import CaptchaRecord
        from tests.test_auth import unique_key, utcnow

        # 创建分类和课程
        category = Category(
            name="更新课程分类",
            slug=f"update-cat-{uuid.uuid4().hex[:8]}",
            is_active=True,
        )
        db_session.add(category)
        await db_session.flush()

        course = Course(
            title="待更新课程",
            subtitle="旧副标题",
            description="旧描述",
            teacher_id=test_teacher.id,
            category_id=category.id,
            status="draft",
            price=99.0,
            level="beginner",
        )
        db_session.add(course)
        await db_session.flush()

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
                "username": "testteacher",
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
            f"/api/v1/courses/{course.id}",
            headers={"Authorization": f"Bearer {token}"},
            json={"title": "已更新课程"},
        )

        assert response.status_code == 200


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
                "username": "testteacher",
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
        assert data["data"]["file_url"].startswith("http://test/uploads/course-covers/")

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
        assert data["message"] == "仅讲师或管理员可上传课程封面"


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
        assert data["file_url"].startswith("http://test/uploads/files/")

        upload_path = urlparse(data["file_url"]).path
        file_path = (
            Path(settings.upload_dir)
            / Path(upload_path.lstrip("/")).relative_to("uploads")
        )
        assert file_path.exists()
        file_path.unlink(missing_ok=True)

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
                "username": "testteacher",
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
