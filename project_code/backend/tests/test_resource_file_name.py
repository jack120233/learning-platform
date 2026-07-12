"""资源原始文件名持久化测试。"""

import asyncio
from importlib.util import module_from_spec, spec_from_file_location
from datetime import datetime, timezone
from pathlib import Path

from app.models.content import Chapter, Resource, Section
from app.models.course import Course
from app.schemas.content import ResourceCreate, ResourceResponse
from app.services.upload_service import upload_service


SERVICES_DIR = Path(__file__).resolve().parents[1] / "app" / "services"


def load_service_module(module_name: str):
    module_path = SERVICES_DIR / f"{module_name}.py"
    module_spec = spec_from_file_location(f"tests_{module_name}", module_path)
    assert module_spec is not None and module_spec.loader is not None
    module = module_from_spec(module_spec)
    module_spec.loader.exec_module(module)
    return module


ResourceService = load_service_module("content_service").ResourceService
CourseService = load_service_module("course_service").CourseService
LearningService = load_service_module("learning_service").LearningService


def run_async(awaitable):
    """在未安装 pytest-asyncio 的环境里执行协程。"""
    return asyncio.run(awaitable)


class FakeScalarResult:
    """最小查询结果桩对象。"""

    def __init__(self, items):
        self._items = items

    def scalars(self):
        return self

    def all(self):
        return self._items

    def scalar(self):
        return self._items[0] if self._items else None


class FakeAsyncSession:
    """覆盖当前测试所需最小 AsyncSession 能力。"""

    def __init__(self, *, get_map=None, execute_results=None):
        self._get_map = get_map or {}
        self._execute_results = list(execute_results or [])
        self.added = []
        self.deleted = []
        self.info = {}

    async def get(self, model, key):
        return self._get_map.get((model, key))

    def add(self, instance):
        self.added.append(instance)

    async def delete(self, instance):
        self.deleted.append(instance)

    async def flush(self):
        return None

    async def execute(self, _statement):
        return self._execute_results.pop(0)


def test_resource_create_keeps_file_name_and_title_in_sync():
    payload = ResourceCreate.model_validate(
        {
            "resource_type": "document",
            "file_name": "lesson-outline.pdf",
            "file_url": "/uploads/files/hashed.pdf",
            "file_size": 128,
        }
    )

    assert payload.title == "lesson-outline.pdf"
    assert payload.file_name == "lesson-outline.pdf"


def test_resource_create_does_not_persist_title_as_original_file_name():
    payload = ResourceCreate.model_validate(
        {
            "resource_type": "document",
            "title": "第一课课件",
            "file_url": "/uploads/files/hashed.pdf",
            "file_size": 128,
        }
    )

    assert payload.title == "第一课课件"
    assert payload.file_name is None


def test_resource_response_prefers_persisted_file_name():
    payload = ResourceResponse.model_validate(
        {
            "id": 1,
            "resource_id": 1,
            "course_id": 10,
            "chapter_id": 20,
            "section_id": 30,
            "title": "第一课课件",
            "file_name": "lesson-outline.pdf",
            "type": "document",
            "resource_type": "document",
            "file_url": "/uploads/files/hashed.pdf",
            "file_size": 128,
            "duration": 0,
            "sort_order": 1,
            "is_free": False,
            "is_required": True,
            "view_count": 0,
            "created_at": "2026-07-13T00:00:00Z",
        }
    )

    assert payload.file_name == "lesson-outline.pdf"


def test_resource_response_falls_back_to_title_when_file_name_is_none():
    payload = ResourceResponse.model_validate(
        Resource(
            id=1,
            course_id=10,
            chapter_id=20,
            section_id=30,
            title="第一课课件",
            file_name=None,
            type="document",
            file_url="/uploads/files/hashed.pdf",
            file_size=128,
            duration=0,
            sort_order=1,
            is_free=False,
            is_required=True,
            view_count=0,
            created_at=datetime.now(timezone.utc),
        )
    )

    assert payload.file_name == "第一课课件"


def test_resource_service_persists_original_file_name_for_new_resources():
    async def scenario():
        course = Course(id=1, title="测试课程", teacher_id=99, status="draft")
        chapter = Chapter(id=2, course_id=1, title="第一章", total_duration=0)
        section = Section(id=3, course_id=1, chapter_id=2, title="第一节", resource_count=0, duration=0)
        session = FakeAsyncSession(
            get_map={
                (Course, 1): course,
                (Chapter, 2): chapter,
                (Section, 3): section,
            }
        )

        service = ResourceService()
        resource = await service.create_for_section(
            session,
            1,
            2,
            3,
            99,
            ResourceCreate(
                title="第一课课件",
                file_name="lesson-outline.pdf",
                file_url="/uploads/files/hashed.pdf",
                file_size=128,
                resource_type="document",
            ),
        )

        assert resource.title == "第一课课件"
        assert resource.file_name == "lesson-outline.pdf"
        assert session.added[-1] is resource

    run_async(scenario())


def test_course_service_prefers_original_file_name_in_course_tree():
    created_at = datetime.now(timezone.utc)
    course_service = CourseService()
    chapter = Chapter(
        id=2,
        course_id=1,
        title="第一章",
        sort_order=1,
        is_free=False,
        total_duration=0,
        section_count=1,
        created_at=created_at,
    )
    section = Section(
        id=3,
        course_id=1,
        chapter_id=2,
        title="第一节",
        sort_order=1,
        is_free=False,
        duration=0,
        resource_count=1,
        created_at=created_at,
    )
    resource = Resource(
        id=4,
        course_id=1,
        chapter_id=2,
        section_id=3,
        title="第一课课件",
        file_name="lesson-outline.pdf",
        type="document",
        file_url="/uploads/files/hashed.pdf",
        file_size=128,
        duration=0,
        sort_order=1,
        is_free=False,
        is_required=True,
        view_count=0,
        created_at=created_at,
    )
    session = FakeAsyncSession(
        execute_results=[
            FakeScalarResult([chapter]),
            FakeScalarResult([section]),
            FakeScalarResult([resource]),
        ]
    )

    chapters = run_async(course_service.get_chapters_with_sections(session, 1))

    assert chapters[0].sections[0].resources[0].file_name == "lesson-outline.pdf"


def test_course_service_delete_queues_course_asset_files():
    course = Course(
        id=1,
        title="测试课程",
        teacher_id=99,
        status="draft",
        cover_url="/uploads/course-covers/course.png",
    )
    session = FakeAsyncSession(
        get_map={(Course, 1): course},
        execute_results=[
            FakeScalarResult(["/uploads/files/outline.pdf"]),
            FakeScalarResult(["/uploads/files/lesson.mp4", "/uploads/files/lesson.mp4"]),
            FakeScalarResult([1]),
            FakeScalarResult([0]),
            FakeScalarResult([1]),
            FakeScalarResult([0]),
            FakeScalarResult([0]),
            FakeScalarResult([0]),
        ],
    )

    run_async(CourseService().delete(session, 1, type("Teacher", (), {"id": 99})()))

    assert session.deleted == [course]
    assert session.info[upload_service.pending_delete_session_key] == {
        "/uploads/files/lesson.mp4",
    }


def test_learning_service_play_url_returns_original_file_name():
    resource = Resource(
        id=4,
        course_id=1,
        chapter_id=2,
        section_id=3,
        title="第一课视频",
        file_name="lesson-video.mp4",
        type="video",
        file_url="/uploads/files/hashed.mp4",
        file_size=1024,
        duration=90,
        sort_order=1,
        is_free=False,
        is_required=True,
        view_count=0,
    )
    session = FakeAsyncSession(get_map={(Resource, 4): resource})

    payload = run_async(LearningService().get_play_url(session, user_id=99, resource_id=4))

    assert payload["file_name"] == "lesson-video.mp4"
