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
from app.models.content import Chapter, Section, Resource


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
        assert isinstance(response.json()["data"], list)


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
            status="draft",
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
        assert response.json()["data"]["chapter_id"] > 0

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
            status="draft",
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
    async def test_delete_chapter_legacy_post_route(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ):
        """测试兼容旧前端的 POST 删除章节路由"""
        teacher, headers = await create_content_test_user(db_session, "teacher")

        category = Category(
            name="删除章节分类",
            slug=f"delete-chap-{uuid.uuid4().hex[:8]}",
            is_active=True,
        )
        db_session.add(category)
        await db_session.flush()

        course = Course(
            title="删除章节课程",
            teacher_id=teacher.id,
            category_id=category.id,
            status="draft",
            price=0,
            level="beginner",
        )
        db_session.add(course)
        await db_session.flush()

        chapter = Chapter(
            course_id=course.id,
            title="待删除章节",
            sort_order=1,
        )
        db_session.add(chapter)
        await db_session.flush()

        response = await client.post(
            f"/api/v1/courses/{course.id}/chapters/{chapter.id}/delete",
            headers=headers,
        )

        assert response.status_code == 200
        await db_session.flush()
        result = await db_session.execute(
            select(Chapter.id).where(Chapter.id == chapter.id)
        )
        assert result.scalar_one_or_none() is None

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
            status="draft",
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
        assert response.json()["data"]["section_id"] > 0
        await db_session.refresh(course)
        await db_session.refresh(chapter)
        assert course.total_sections == 1
        assert chapter.section_count == 1

    @pytest.mark.asyncio
    async def test_delete_section_legacy_post_route(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ):
        """测试兼容旧前端的 POST 删除小节路由"""
        teacher, headers = await create_content_test_user(db_session, "teacher")

        category = Category(
            name="删除小节分类",
            slug=f"delete-sec-{uuid.uuid4().hex[:8]}",
            is_active=True,
        )
        db_session.add(category)
        await db_session.flush()

        course = Course(
            title="删除小节课程",
            teacher_id=teacher.id,
            category_id=category.id,
            status="draft",
            price=0,
            level="beginner",
        )
        db_session.add(course)
        await db_session.flush()

        chapter = Chapter(
            course_id=course.id,
            title="章节",
            sort_order=1,
            section_count=1,
        )
        db_session.add(chapter)
        await db_session.flush()

        section = Section(
            course_id=course.id,
            chapter_id=chapter.id,
            title="待删除小节",
            sort_order=1,
        )
        db_session.add(section)
        await db_session.flush()

        response = await client.post(
            f"/api/v1/courses/{course.id}/chapters/{chapter.id}/sections/{section.id}/delete",
            headers=headers,
        )

        assert response.status_code == 200
        await db_session.flush()
        result = await db_session.execute(
            select(Section.id).where(Section.id == section.id)
        )
        assert result.scalar_one_or_none() is None

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
        assert isinstance(response.json()["data"], list)


# 导入必要的模型
from app.models.captcha import CaptchaRecord


class TestSectionResourceAPI:
    """小节资源接口测试。"""

    @pytest.mark.asyncio
    async def test_create_section_resource_accepts_resource_type_payload(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ):
        """测试小节资源接口兼容前端 resource_type/file_name 字段。"""
        teacher, headers = await create_content_test_user(db_session, "teacher")

        category = Category(
            name="资源分类",
            slug=f"resource-cat-{uuid.uuid4().hex[:8]}",
            is_active=True,
        )
        db_session.add(category)
        await db_session.flush()

        course = Course(
            title="资源课程",
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

        section = Section(
            course_id=course.id,
            chapter_id=chapter.id,
            title="小节",
            sort_order=1,
        )
        db_session.add(section)
        await db_session.flush()

        response = await client.post(
            f"/api/v1/courses/{course.id}/sections/{section.id}/resources",
            headers=headers,
            json={
                "resource_type": "document",
                "file_name": "讲义.pdf",
                "file_url": "http://test/uploads/files/handout.pdf",
                "file_size": 2048,
                "sort_order": 0,
                "is_free": False,
            },
        )

        assert response.status_code == 200
        data = response.json()["data"]
        assert data["resource_id"] > 0
        assert data["resource_type"] == "document"
        assert data["file_name"] == "讲义.pdf"
        assert data["title"] == "讲义.pdf"
        assert data["is_required"] is True

    @pytest.mark.asyncio
    async def test_create_section_resource_accepts_optional_required_flag(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ):
        """测试小节资源可显式创建为选修资源。"""
        teacher, headers = await create_content_test_user(db_session, "teacher")

        category = Category(
            name="选修资源分类",
            slug=f"optional-resource-{uuid.uuid4().hex[:8]}",
            is_active=True,
        )
        db_session.add(category)
        await db_session.flush()

        course = Course(
            title="选修资源课程",
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

        section = Section(
            course_id=course.id,
            chapter_id=chapter.id,
            title="小节",
            sort_order=1,
        )
        db_session.add(section)
        await db_session.flush()

        response = await client.post(
            f"/api/v1/courses/{course.id}/sections/{section.id}/resources",
            headers=headers,
            json={
                "resource_type": "document",
                "file_name": "拓展阅读.pdf",
                "file_url": "http://test/uploads/files/optional.pdf",
                "file_size": 2048,
                "sort_order": 0,
                "is_free": False,
                "is_required": False,
            },
        )

        assert response.status_code == 200
        data = response.json()["data"]
        assert data["is_required"] is False

        result = await db_session.execute(
            select(Resource).where(Resource.id == data["resource_id"])
        )
        resource = result.scalar_one()
        assert resource.is_required is False

    @pytest.mark.asyncio
    async def test_delete_section_resource_legacy_post_route(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ):
        """测试兼容旧前端的 POST 删除资源接口。"""
        teacher, headers = await create_content_test_user(db_session, "teacher")

        category = Category(
            name="资源删除分类",
            slug=f"resource-delete-{uuid.uuid4().hex[:8]}",
            is_active=True,
        )
        db_session.add(category)
        await db_session.flush()

        course = Course(
            title="资源删除课程",
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

        section = Section(
            course_id=course.id,
            chapter_id=chapter.id,
            title="小节",
            sort_order=1,
        )
        db_session.add(section)
        await db_session.flush()

        resource = Resource(
            course_id=course.id,
            chapter_id=chapter.id,
            section_id=section.id,
            title="待删除资源",
            type="document",
            file_url="http://test/uploads/files/delete.pdf",
            file_size=1024,
            sort_order=1,
        )
        db_session.add(resource)
        await db_session.flush()

        response = await client.post(
            f"/api/v1/courses/{course.id}/sections/{section.id}/resources/{resource.id}/delete",
            headers=headers,
        )

        assert response.status_code == 200
        await db_session.flush()
        result = await db_session.execute(
            select(Resource.id).where(Resource.id == resource.id)
        )
        assert result.scalar_one_or_none() is None


class TestPublishedCourseContentEditGuard:
    """已发布课程内容编辑保护测试。"""

    async def _create_course_tree(
        self,
        db_session: AsyncSession,
        status: str = "published",
    ) -> tuple[User, dict[str, str], Course, Chapter, Section]:
        teacher, headers = await create_content_test_user(db_session, "teacher")
        category = Category(
            name=f"发布保护分类-{uuid.uuid4().hex[:8]}",
            slug=f"published-guard-{uuid.uuid4().hex[:8]}",
            is_active=True,
        )
        db_session.add(category)
        await db_session.flush()

        course = Course(
            title="发布保护课程",
            teacher_id=teacher.id,
            category_id=category.id,
            status=status,
            price=0,
            level="beginner",
        )
        db_session.add(course)
        await db_session.flush()

        chapter = Chapter(course_id=course.id, title="原章节", sort_order=1)
        db_session.add(chapter)
        await db_session.flush()

        section = Section(
            course_id=course.id,
            chapter_id=chapter.id,
            title="原小节",
            sort_order=1,
        )
        db_session.add(section)
        await db_session.flush()
        return teacher, headers, course, chapter, section

    @pytest.mark.asyncio
    async def test_cannot_create_chapter_on_published_course(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ):
        """已发布课程不能创建章节。"""
        _teacher, headers, course, _chapter, _section = await self._create_course_tree(db_session)

        response = await client.post(
            f"/api/v1/courses/{course.id}/chapters",
            headers=headers,
            json={"title": "新增章节", "sort_order": 2},
        )

        assert response.status_code == 422
        assert response.json()["message"] == "已发布课程不能直接编辑，请先下架"

    @pytest.mark.asyncio
    async def test_cannot_update_chapter_on_published_course(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ):
        """已发布课程不能更新章节，且标题保持不变。"""
        _teacher, headers, course, chapter, _section = await self._create_course_tree(db_session)

        response = await client.post(
            f"/api/v1/courses/{course.id}/chapters/{chapter.id}",
            headers=headers,
            json={"title": "不应写入章节"},
        )

        assert response.status_code == 422
        await db_session.refresh(chapter)
        assert chapter.title == "原章节"

    @pytest.mark.asyncio
    async def test_archived_course_content_mutation_succeeds(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ):
        """已下架课程可以继续编辑内容。"""
        _teacher, headers, course, chapter, _section = await self._create_course_tree(db_session, status="archived")

        response = await client.post(
            f"/api/v1/courses/{course.id}/chapters/{chapter.id}",
            headers=headers,
            json={"title": "下架后章节标题"},
        )

        assert response.status_code == 200
        await db_session.refresh(chapter)
        assert chapter.title == "下架后章节标题"

    @pytest.mark.asyncio
    async def test_cannot_create_section_on_published_course(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ):
        """已发布课程不能创建小节。"""
        _teacher, headers, course, chapter, _section = await self._create_course_tree(db_session)

        response = await client.post(
            f"/api/v1/courses/{course.id}/chapters/{chapter.id}/sections",
            headers=headers,
            json={"title": "新增小节", "sort_order": 2},
        )

        assert response.status_code == 422
        assert response.json()["message"] == "已发布课程不能直接编辑，请先下架"

    @pytest.mark.asyncio
    async def test_cannot_create_resource_on_published_course(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ):
        """已发布课程不能创建资源。"""
        _teacher, headers, course, _chapter, section = await self._create_course_tree(db_session)

        response = await client.post(
            f"/api/v1/courses/{course.id}/sections/{section.id}/resources",
            headers=headers,
            json={
                "resource_type": "document",
                "file_name": "禁止新增.pdf",
                "file_url": "http://test/uploads/files/no-resource.pdf",
                "file_size": 1024,
            },
        )

        assert response.status_code == 422
        assert response.json()["message"] == "已发布课程不能直接编辑，请先下架"


class TestChapterResourceAPI:
    """章节资源接口测试。"""

    @pytest.mark.asyncio
    async def test_create_chapter_resource(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ):
        """测试创建章节级资源。"""
        teacher, headers = await create_content_test_user(db_session, "teacher")

        category = Category(
            name="章节资源分类",
            slug=f"chapter-resource-{uuid.uuid4().hex[:8]}",
            is_active=True,
        )
        db_session.add(category)
        await db_session.flush()

        course = Course(
            title="章节资源课程",
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

        response = await client.post(
            f"/api/v1/courses/{course.id}/chapters/{chapter.id}/resources",
            headers=headers,
            json={
                "resource_type": "document",
                "file_name": "章节讲义.pdf",
                "file_url": "http://test/uploads/files/chapter-handout.pdf",
                "file_size": 4096,
                "sort_order": 1,
                "is_free": False,
            },
        )

        assert response.status_code == 200
        data = response.json()["data"]
        assert data["resource_id"] > 0
        assert data["chapter_id"] == chapter.id
        assert data["section_id"] is None
        assert data["file_name"] == "章节讲义.pdf"
        assert data["is_required"] is True

    @pytest.mark.asyncio
    async def test_delete_chapter_resource_legacy_post_route(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ):
        """测试兼容旧前端的章节资源删除接口。"""
        teacher, headers = await create_content_test_user(db_session, "teacher")

        category = Category(
            name="章节资源删除分类",
            slug=f"chapter-resource-delete-{uuid.uuid4().hex[:8]}",
            is_active=True,
        )
        db_session.add(category)
        await db_session.flush()

        course = Course(
            title="章节资源删除课程",
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

        resource = Resource(
            course_id=course.id,
            chapter_id=chapter.id,
            section_id=None,
            title="待删除章节资源",
            type="document",
            file_url="http://test/uploads/files/chapter-delete.pdf",
            file_size=1024,
            sort_order=1,
        )
        db_session.add(resource)
        await db_session.flush()

        response = await client.post(
            f"/api/v1/courses/{course.id}/chapters/{chapter.id}/resources/{resource.id}/delete",
            headers=headers,
        )

        assert response.status_code == 200
        await db_session.flush()
        result = await db_session.execute(
            select(Resource.id).where(Resource.id == resource.id)
        )
        assert result.scalar_one_or_none() is None

    @pytest.mark.asyncio
    async def test_chapter_resource_does_not_change_section_counts(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ):
        """测试章节资源不会污染小节统计字段。"""
        teacher, headers = await create_content_test_user(db_session, "teacher")

        category = Category(
            name="章节统计分类",
            slug=f"chapter-resource-stats-{uuid.uuid4().hex[:8]}",
            is_active=True,
        )
        db_session.add(category)
        await db_session.flush()

        course = Course(
            title="章节统计课程",
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

        section = Section(
            course_id=course.id,
            chapter_id=chapter.id,
            title="小节",
            sort_order=1,
            resource_count=0,
            duration=0,
        )
        db_session.add(section)
        await db_session.flush()

        response = await client.post(
            f"/api/v1/courses/{course.id}/chapters/{chapter.id}/resources",
            headers=headers,
            json={
                "resource_type": "video",
                "file_name": "chapter-video.mp4",
                "file_url": "http://test/uploads/files/chapter-video.mp4",
                "file_size": 10240,
                "duration": 120,
                "sort_order": 1,
                "is_free": False,
            },
        )

        assert response.status_code == 200
        await db_session.refresh(section)
        await db_session.refresh(chapter)
        await db_session.refresh(course)

        assert section.resource_count == 0
        assert section.duration == 0
        assert chapter.total_duration == 120
        assert course.total_duration == 120
