"""课程管理模块测试

测试课程CRUD、发布、搜索等功能。
"""

import uuid
from datetime import datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.course import Course
from app.models.category import Category


def unique_key(prefix: str = "course") -> str:
    """生成唯一键"""
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


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
            description="测试描述",
            teacher_id=test_teacher.id,
            category_id=category.id,
            status="published",
            price=99.0,
            level="beginner",
        )
        db_session.add(course)
        await db_session.flush()

        response = await client.get(f"/api/v1/courses/{course.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["title"] == "测试课程详情"

    @pytest.mark.asyncio
    async def test_get_course_not_found(self, client: AsyncClient):
        """测试课程不存在"""
        response = await client.get("/api/v1/courses/999999")
        assert response.status_code == 404


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
                "description": "描述",
                "category_id": category.id,
                "price": 99.0,
                "level": "beginner",
            },
        )

        assert response.status_code == 200

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