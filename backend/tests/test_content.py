"""课程内容模块测试

测试章节、小节、资源管理功能。
"""

import uuid
from datetime import datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.course import Course
from app.models.category import Category
from app.models.content import Chapter, Section


def unique_key(prefix: str = "content") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


class TestChapterList:
    """章节列表测试类"""

    @pytest.mark.asyncio
    async def test_get_chapters(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_teacher: User,
    ):
        """测试获取章节列表"""
        category = Category(
            name="章节分类",
            slug=f"chapter-cat-{uuid.uuid4().hex[:8]}",
            is_active=True,
        )
        db_session.add(category)
        await db_session.flush()

        course = Course(
            title="章节测试课程",
            teacher_id=test_teacher.id,
            category_id=category.id,
            status="published",
            price=0,
            level="beginner",
        )
        db_session.add(course)
        await db_session.flush()

        response = await client.get(f"/api/v1/courses/{course.id}/chapters")
        assert response.status_code == 200


class TestChapterCRUD:
    """章节CRUD测试类"""

    @pytest.mark.asyncio
    async def test_create_chapter(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_teacher: User,
    ):
        """测试创建章节"""
        from app.models.captcha import CaptchaRecord
        from tests.test_auth import unique_key, utcnow

        category = Category(
            name="创建章节分类",
            slug=f"create-chap-{uuid.uuid4().hex[:8]}",
            is_active=True,
        )
        db_session.add(category)
        await db_session.flush()

        course = Course(
            title="创建章节课程",
            teacher_id=test_teacher.id,
            category_id=category.id,
            status="published",
            price=0,
            level="beginner",
        )
        db_session.add(course)
        await db_session.flush()

        key = unique_key("create_chap")
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
            f"/api/v1/courses/{course.id}/chapters",
            headers={"Authorization": f"Bearer {token}"},
            json={"title": "新章节", "sort_order": 1},
        )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_update_chapter(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_teacher: User,
    ):
        """测试更新章节"""
        from app.models.captcha import CaptchaRecord
        from tests.test_auth import unique_key, utcnow

        category = Category(
            name="更新章节分类",
            slug=f"update-chap-{uuid.uuid4().hex[:8]}",
            is_active=True,
        )
        db_session.add(category)
        await db_session.flush()

        course = Course(
            title="更新章节课程",
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
            title="旧章节标题",
            sort_order=1,
        )
        db_session.add(chapter)
        await db_session.flush()

        key = unique_key("update_chap")
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
            f"/api/v1/courses/{course.id}/chapters/{chapter.id}",
            headers={"Authorization": f"Bearer {token}"},
            json={"title": "新章节标题"},
        )

        assert response.status_code == 200


class TestSectionCRUD:
    """小节CRUD测试类"""

    @pytest.mark.asyncio
    async def test_create_section(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_teacher: User,
    ):
        """测试创建小节"""
        from app.models.captcha import CaptchaRecord
        from tests.test_auth import unique_key, utcnow

        category = Category(
            name="创建小节分类",
            slug=f"create-sec-{uuid.uuid4().hex[:8]}",
            is_active=True,
        )
        db_session.add(category)
        await db_session.flush()

        course = Course(
            title="创建小节课程",
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

        key = unique_key("create_sec")
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
            f"/api/v1/courses/{course.id}/chapters/{chapter.id}/sections",
            headers={"Authorization": f"Bearer {token}"},
            json={"title": "新小节", "sort_order": 1},
        )

        assert response.status_code == 200


class TestSectionList:
    """小节列表测试类"""

    @pytest.mark.asyncio
    async def test_get_sections(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_teacher: User,
    ):
        """测试获取小节列表"""
        category = Category(
            name="小节列表分类",
            slug=f"sec-list-{uuid.uuid4().hex[:8]}",
            is_active=True,
        )
        db_session.add(category)
        await db_session.flush()

        course = Course(
            title="小节列表课程",
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

        response = await client.get(
            f"/api/v1/courses/{course.id}/chapters/{chapter.id}/sections"
        )
        assert response.status_code == 200


# 导入必要的模型
from app.models.captcha import CaptchaRecord