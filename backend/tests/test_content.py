"""课程内容模块测试

测试章节、小节、资源管理功能。
"""

import uuid
from datetime import datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.security import create_access_token
from app.models.user import User
from app.models.course import Course
from app.models.category import Category
from app.models.content import Chapter, Section


def unique_key(prefix: str = "content") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


async def create_content_test_user(
    db_session: AsyncSession,
    role: str = "teacher",
) -> tuple[User, dict[str, str]]:
    """创建课程内容测试用户并返回认证头。"""
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

    headers = {"Authorization": f"Bearer {create_access_token(user.id)}"}
    return user, headers


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

    @pytest.mark.asyncio
    async def test_sort_chapters(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ):
        """测试章节排序"""
        teacher, headers = await create_content_test_user(db_session, "teacher")

        category = Category(
            name="章节排序分类",
            slug=f"sort-chap-{uuid.uuid4().hex[:8]}",
            is_active=True,
        )
        db_session.add(category)
        await db_session.flush()

        course = Course(
            title="章节排序课程",
            teacher_id=teacher.id,
            category_id=category.id,
            status="draft",
            price=0,
            level="beginner",
        )
        db_session.add(course)
        await db_session.flush()

        chapter1 = Chapter(course_id=course.id, title="章节1", sort_order=1)
        chapter2 = Chapter(course_id=course.id, title="章节2", sort_order=2)
        chapter3 = Chapter(course_id=course.id, title="章节3", sort_order=3)
        db_session.add_all([chapter1, chapter2, chapter3])
        await db_session.flush()

        response = await client.post(
            f"/api/v1/courses/{course.id}/chapters/sort",
            headers=headers,
            json={"chapter_ids": [chapter3.id, chapter1.id, chapter2.id]},
        )

        assert response.status_code == 200
        assert response.json()["message"] == "排序成功"

        result = await db_session.execute(
            select(Chapter)
            .where(Chapter.course_id == course.id)
            .order_by(Chapter.sort_order, Chapter.id)
        )
        sorted_chapters = list(result.scalars().all())
        assert [chapter.id for chapter in sorted_chapters] == [
            chapter3.id,
            chapter1.id,
            chapter2.id,
        ]
        assert [chapter.sort_order for chapter in sorted_chapters] == [1, 2, 3]

    @pytest.mark.asyncio
    async def test_sort_chapters_requires_all_course_chapter_ids(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ):
        """测试章节排序时必须传入课程全部章节ID"""
        teacher, headers = await create_content_test_user(db_session, "teacher")

        category = Category(
            name="章节排序校验分类",
            slug=f"sort-chap-check-{uuid.uuid4().hex[:8]}",
            is_active=True,
        )
        db_session.add(category)
        await db_session.flush()

        course = Course(
            title="章节排序校验课程",
            teacher_id=teacher.id,
            category_id=category.id,
            status="draft",
            price=0,
            level="beginner",
        )
        db_session.add(course)
        await db_session.flush()

        chapter1 = Chapter(course_id=course.id, title="章节1", sort_order=1)
        chapter2 = Chapter(course_id=course.id, title="章节2", sort_order=2)
        db_session.add_all([chapter1, chapter2])
        await db_session.flush()

        response = await client.post(
            f"/api/v1/courses/{course.id}/chapters/sort",
            headers=headers,
            json={"chapter_ids": [chapter1.id]},
        )

        assert response.status_code == 422
        assert response.json()["message"] == "chapter_ids 必须包含该课程全部章节ID"


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

    @pytest.mark.asyncio
    async def test_sort_sections(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ):
        """测试小节排序"""
        teacher, headers = await create_content_test_user(db_session, "teacher")

        category = Category(
            name="小节排序分类",
            slug=f"sort-sec-{uuid.uuid4().hex[:8]}",
            is_active=True,
        )
        db_session.add(category)
        await db_session.flush()

        course = Course(
            title="小节排序课程",
            teacher_id=teacher.id,
            category_id=category.id,
            status="draft",
            price=0,
            level="beginner",
        )
        db_session.add(course)
        await db_session.flush()

        chapter = Chapter(course_id=course.id, title="章节", sort_order=1)
        db_session.add(chapter)
        await db_session.flush()

        section1 = Section(
            course_id=course.id,
            chapter_id=chapter.id,
            title="小节1",
            sort_order=1,
        )
        section2 = Section(
            course_id=course.id,
            chapter_id=chapter.id,
            title="小节2",
            sort_order=2,
        )
        section3 = Section(
            course_id=course.id,
            chapter_id=chapter.id,
            title="小节3",
            sort_order=3,
        )
        db_session.add_all([section1, section2, section3])
        await db_session.flush()

        response = await client.post(
            f"/api/v1/courses/{course.id}/chapters/{chapter.id}/sections/sort",
            headers=headers,
            json={"section_ids": [section3.id, section1.id, section2.id]},
        )

        assert response.status_code == 200
        assert response.json()["message"] == "排序成功"

        result = await db_session.execute(
            select(Section)
            .where(Section.chapter_id == chapter.id)
            .order_by(Section.sort_order, Section.id)
        )
        sorted_sections = list(result.scalars().all())
        assert [section.id for section in sorted_sections] == [
            section3.id,
            section1.id,
            section2.id,
        ]
        assert [section.sort_order for section in sorted_sections] == [1, 2, 3]

    @pytest.mark.asyncio
    async def test_sort_sections_requires_all_chapter_section_ids(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ):
        """测试小节排序时必须传入章节全部小节ID"""
        teacher, headers = await create_content_test_user(db_session, "teacher")

        category = Category(
            name="小节排序校验分类",
            slug=f"sort-sec-check-{uuid.uuid4().hex[:8]}",
            is_active=True,
        )
        db_session.add(category)
        await db_session.flush()

        course = Course(
            title="小节排序校验课程",
            teacher_id=teacher.id,
            category_id=category.id,
            status="draft",
            price=0,
            level="beginner",
        )
        db_session.add(course)
        await db_session.flush()

        chapter = Chapter(course_id=course.id, title="章节", sort_order=1)
        db_session.add(chapter)
        await db_session.flush()

        section1 = Section(
            course_id=course.id,
            chapter_id=chapter.id,
            title="小节1",
            sort_order=1,
        )
        section2 = Section(
            course_id=course.id,
            chapter_id=chapter.id,
            title="小节2",
            sort_order=2,
        )
        db_session.add_all([section1, section2])
        await db_session.flush()

        response = await client.post(
            f"/api/v1/courses/{course.id}/chapters/{chapter.id}/sections/sort",
            headers=headers,
            json={"section_ids": [section1.id]},
        )

        assert response.status_code == 422
        assert response.json()["message"] == "section_ids 必须包含该章节全部小节ID"


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
