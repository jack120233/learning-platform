"""课程内容 API 回归测试。"""

from __future__ import annotations

from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.api.v1.router import router as api_v1_router
from app.config import settings
from app.core.db_schema import ensure_database_compatibility
from app.core.dependencies import get_db
from app.core.exceptions import AppException, app_exception_to_http_exception
from app.core.security import create_access_token
from app.models.content import Chapter, Resource, Section
from app.models.course import Course
from app.models.user import User


pytestmark = pytest.mark.asyncio


@pytest_asyncio.fixture
async def session_factory(
    tmp_path,
) -> AsyncGenerator[async_sessionmaker[AsyncSession], None]:
    """为每个测试创建隔离的 SQLite 会话工厂。"""
    db_path = tmp_path / "content-api.sqlite3"
    engine = create_async_engine(
        f"sqlite+aiosqlite:///{db_path}",
        future=True,
    )

    async with engine.begin() as conn:
        await ensure_database_compatibility(conn)

    factory = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
        autocommit=False,
    )
    try:
        yield factory
    finally:
        await engine.dispose()


@pytest_asyncio.fixture
async def test_app(
    session_factory: async_sessionmaker[AsyncSession],
) -> AsyncGenerator[FastAPI, None]:
    """创建使用测试数据库的最小 FastAPI 应用。"""
    app = FastAPI(openapi_url="/openapi.json")

    @app.exception_handler(AppException)
    async def _handle_app_exception(
        request: Request,
        exc: AppException,
    ) -> JSONResponse:
        http_exc = app_exception_to_http_exception(exc)
        return JSONResponse(
            status_code=http_exc.status_code,
            content=http_exc.detail,
        )

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        async with session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    app.dependency_overrides[get_db] = override_get_db
    app.include_router(api_v1_router, prefix=settings.api_v1_prefix)

    try:
        yield app
    finally:
        app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def client(test_app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    """创建异步测试客户端。"""
    transport = ASGITransport(app=test_app)
    async with AsyncClient(
        transport=transport,
        base_url="http://testserver",
    ) as async_client:
        yield async_client


async def _seed_section_with_resources(
    session_factory: async_sessionmaker[AsyncSession],
) -> dict[str, int]:
    """写入一个带资源的小节用于删除测试。"""
    async with session_factory() as session:
        teacher = User(
            username="teacher_delete_section",
            email="teacher_delete_section@example.com",
            password_hash="hashed-password",
            role="teacher",
            status="active",
        )
        session.add(teacher)
        await session.flush()

        course = Course(
            title="删除小节测试课程",
            teacher_id=teacher.id,
            status="draft",
            total_duration=120,
            total_sections=1,
        )
        session.add(course)
        await session.flush()

        chapter = Chapter(
            course_id=course.id,
            title="测试章节",
            total_duration=120,
            section_count=1,
        )
        session.add(chapter)
        await session.flush()

        section = Section(
            course_id=course.id,
            chapter_id=chapter.id,
            title="测试小节",
            duration=120,
            resource_count=2,
        )
        session.add(section)
        await session.flush()

        session.add_all(
            [
                Resource(
                    course_id=course.id,
                    chapter_id=chapter.id,
                    section_id=section.id,
                    title="测试视频",
                    type="video",
                    file_url="https://example.com/video.mp4",
                    file_size=1024,
                    duration=120,
                ),
                Resource(
                    course_id=course.id,
                    chapter_id=chapter.id,
                    section_id=section.id,
                    title="测试文档",
                    type="document",
                    file_url="https://example.com/doc.pdf",
                    file_size=512,
                    duration=0,
                ),
            ]
        )
        await session.commit()

        return {
            "teacher_id": teacher.id,
            "course_id": course.id,
            "chapter_id": chapter.id,
            "section_id": section.id,
        }


async def test_delete_section_route_is_exposed_in_openapi(
    client: AsyncClient,
) -> None:
    """删除小节接口应通过 OpenAPI 暴露为 DELETE 路由。"""
    response = await client.get("/openapi.json")

    assert response.status_code == 200
    delete_operation = response.json()["paths"][
        "/api/v1/courses/{course_id}/chapters/{chapter_id}/sections/{section_id}"
    ]["delete"]
    assert delete_operation["summary"] == "删除小节"
    assert "下属资源" in delete_operation["description"]


async def test_delete_section_cascades_resources_and_updates_aggregates(
    session_factory: async_sessionmaker[AsyncSession],
    client: AsyncClient,
) -> None:
    """删除小节时应一并删除资源并更新聚合统计。"""
    ids = await _seed_section_with_resources(session_factory)
    headers = {
        "Authorization": f"Bearer {create_access_token(ids['teacher_id'])}",
    }

    response = await client.delete(
        (
            f"/api/v1/courses/{ids['course_id']}/chapters/"
            f"{ids['chapter_id']}/sections/{ids['section_id']}"
        ),
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["code"] == 200
    assert response.json()["message"] == "删除成功"

    async with session_factory() as session:
        deleted_section = await session.get(Section, ids["section_id"])
        remaining_resources = await session.execute(
            select(Resource).where(Resource.section_id == ids["section_id"])
        )
        chapter = await session.get(Chapter, ids["chapter_id"])
        course = await session.get(Course, ids["course_id"])

    assert deleted_section is None
    assert remaining_resources.scalars().all() == []
    assert chapter is not None
    assert chapter.section_count == 0
    assert chapter.total_duration == 0
    assert course is not None
    assert course.total_sections == 0
    assert course.total_duration == 0
