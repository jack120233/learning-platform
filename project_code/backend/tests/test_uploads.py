"""上传服务相关测试。"""

import asyncio
import logging
import tempfile
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import pytest

from app.config import Settings, settings
from app.core.exceptions import ValidationException
from app.schemas.upload import ChunkUploadCompleteRequest, ChunkUploadInitRequest


UPLOAD_SERVICE_PATH = Path(__file__).resolve().parents[1] / "app" / "services" / "upload_service.py"
UPLOAD_SERVICE_SPEC = spec_from_file_location("tests_upload_service", UPLOAD_SERVICE_PATH)
assert UPLOAD_SERVICE_SPEC is not None and UPLOAD_SERVICE_SPEC.loader is not None
upload_service_module = module_from_spec(UPLOAD_SERVICE_SPEC)
UPLOAD_SERVICE_SPEC.loader.exec_module(upload_service_module)
UploadService = upload_service_module.UploadService


class SizedPayload:
    """仅用于触发大小校验的轻量占位内容。"""

    def __init__(self, size: int) -> None:
        self.size = size

    def __len__(self) -> int:
        return self.size

    def __bool__(self) -> bool:
        return self.size > 0


class StubUploadFile:
    """最小上传文件桩对象。"""

    def __init__(self, filename: str, content_type: str, payload: object) -> None:
        self.filename = filename
        self.content_type = content_type
        self._payload = payload
        self.closed = False

    async def read(self) -> object:
        return self._payload

    async def close(self) -> None:
        self.closed = True


@pytest.fixture
def upload_settings(monkeypatch):
    with tempfile.TemporaryDirectory(dir=Path.cwd()) as temp_dir:
        temp_path = Path(temp_dir)
        monkeypatch.setattr(settings, "upload_dir", str(temp_path / "uploads"))
        monkeypatch.setattr(settings, "upload_url_prefix", "/uploads")
        monkeypatch.setattr(settings, "course_cover_max_size", 10 * 1024 * 1024)
        monkeypatch.setattr(settings, "general_file_max_size", 500 * 1024 * 1024)
        monkeypatch.setattr(settings, "chunk_file_max_size", 5 * 1024 * 1024 * 1024)
        yield temp_path


def run_async(awaitable):
    """在未安装 pytest-asyncio 的环境里执行协程。"""
    return asyncio.run(awaitable)


def test_settings_upload_size_defaults_match_plan():
    instance = Settings(_env_file=None)

    assert instance.general_file_max_size == 500 * 1024 * 1024
    assert instance.chunk_file_max_size == 5 * 1024 * 1024 * 1024


def test_save_file_accepts_content_at_general_limit(upload_settings, monkeypatch):
    monkeypatch.setattr(settings, "general_file_max_size", 4)
    service = UploadService()
    upload = StubUploadFile("lesson.pdf", "application/pdf", b"data")

    result = run_async(service.save_file(upload))

    assert result["file_name"] == "lesson.pdf"
    assert result["file_size"] == 4
    assert result["file_url"].startswith("/uploads/files/")
    assert upload.closed is True


def test_save_file_rejects_content_over_general_limit_with_dynamic_message(upload_settings):
    service = UploadService()
    upload = StubUploadFile(
        "lesson.pdf",
        "application/pdf",
        SizedPayload(settings.general_file_max_size + 1),
    )

    with pytest.raises(ValidationException, match="文件大小不能超过500MB"):
        run_async(service.save_file(upload))


def test_save_feedback_image_preserves_ten_mb_limit(upload_settings):
    service = UploadService()
    upload = StubUploadFile(
        "feedback.png",
        "image/png",
        SizedPayload(settings.course_cover_max_size + 1),
    )

    with pytest.raises(ValidationException, match="文件大小不能超过10MB"):
        run_async(service.save_feedback_image(upload))


def test_init_chunk_upload_accepts_file_size_at_five_gb_limit(upload_settings):
    service = UploadService()
    data = ChunkUploadInitRequest(
        file_name="course.mp4",
        file_size=settings.chunk_file_max_size,
        chunk_size=10 * 1024 * 1024,
        content_type="video/mp4",
    )

    result = run_async(service.init_chunk_upload(data))

    assert result["chunk_size"] == 10 * 1024 * 1024
    assert result["total_chunks"] == 512


def test_init_chunk_upload_accepts_image_at_ten_mb_limit(upload_settings):
    service = UploadService()
    data = ChunkUploadInitRequest(
        file_name="cover.png",
        file_size=settings.course_cover_max_size,
        chunk_size=1024 * 1024,
        content_type="image/png",
    )

    result = run_async(service.init_chunk_upload(data))

    assert result["total_chunks"] == 10


def test_init_chunk_upload_rejects_file_size_over_five_gb_limit(upload_settings):
    service = UploadService()
    data = ChunkUploadInitRequest(
        file_name="course.mp4",
        file_size=settings.chunk_file_max_size + 1,
        chunk_size=10 * 1024 * 1024,
        content_type="video/mp4",
    )

    with pytest.raises(ValidationException, match="文件大小不能超过5GB"):
        run_async(service.init_chunk_upload(data))


def test_init_chunk_upload_rejects_image_over_ten_mb_limit(upload_settings):
    service = UploadService()
    data = ChunkUploadInitRequest(
        file_name="cover.png",
        file_size=settings.course_cover_max_size + 1,
        chunk_size=1024 * 1024,
        content_type="image/png",
    )

    with pytest.raises(ValidationException, match="文件大小不能超过10MB"):
        run_async(service.init_chunk_upload(data))


def test_complete_chunk_upload_merges_parts_with_existing_flow(upload_settings):
    service = UploadService()
    init_data = ChunkUploadInitRequest(
        file_name="course.mp4",
        file_size=6,
        chunk_size=2,
        content_type="video/mp4",
    )
    init_result = run_async(service.init_chunk_upload(init_data))
    upload_id = str(init_result["upload_id"])

    for index, payload in enumerate((b"ab", b"cd", b"ef")):
        chunk = StubUploadFile(f"chunk-{index}.part", "application/octet-stream", payload)
        result = run_async(service.save_chunk(upload_id, index, chunk))
        assert result == {"chunk_index": index}
        assert chunk.closed is True

    complete_result = run_async(service.complete_chunk_upload(
        ChunkUploadCompleteRequest(
            upload_id=upload_id,
            file_name="course.mp4",
            total_chunks=3,
        )
    ))

    assert complete_result["file_name"] == "course.mp4"
    assert complete_result["file_size"] == 6
    assert complete_result["file_url"].startswith("/uploads/files/")


def test_consume_queued_file_deletions_removes_local_uploaded_file(upload_settings):
    service = UploadService()
    stored_file = Path(settings.upload_dir) / settings.general_upload_subdir / "lesson.pdf"
    stored_file.parent.mkdir(parents=True, exist_ok=True)
    stored_file.write_bytes(b"lesson")

    class FakeSession:
        def __init__(self) -> None:
            self.info = {}

    session = FakeSession()
    service.queue_file_deletions(session, ["/uploads/files/lesson.pdf"])

    service.consume_queued_file_deletions(session)

    assert stored_file.exists() is False
    assert session.info == {}


def test_filter_deletable_file_urls_skips_external_and_shared_urls(upload_settings):
    service = UploadService()

    class FakeScalarResult:
        def __init__(self, value: int) -> None:
            self._value = value

        def scalar(self) -> int:
            return self._value

    class FakeSession:
        def __init__(self) -> None:
            self._results = [
                FakeScalarResult(1),
                FakeScalarResult(0),
                FakeScalarResult(1),
                FakeScalarResult(0),
                FakeScalarResult(0),
                FakeScalarResult(0),
            ]

        async def execute(self, _statement):
            return self._results.pop(0)

    deletable = run_async(service.filter_deletable_file_urls(
        FakeSession(),
        [
            "/uploads/course-covers/shared.png",
            "https://cdn.example.com/shared.pdf",
            "/uploads/files/reused.pdf",
            "/uploads/files/unique.pdf",
            "/uploads/files/unique.pdf",
        ],
        excluded_course_id=1,
    ))

    assert deletable == ["/uploads/files/unique.pdf"]


def test_consume_queued_file_deletions_logs_and_continues_on_failure(caplog):
    service = UploadService()
    deleted_urls: list[str] = []

    def fake_delete(file_url: str | None) -> bool:
        if file_url == "/uploads/files/broken.pdf":
            raise OSError("file locked")
        deleted_urls.append(str(file_url))
        return True

    service.delete_file_by_url = fake_delete  # type: ignore[method-assign]

    class FakeSession:
        def __init__(self) -> None:
            self.info = {
                service.pending_delete_session_key: {
                    "/uploads/files/broken.pdf",
                    "/uploads/files/ok.pdf",
                }
            }

    with caplog.at_level(logging.WARNING):
        service.consume_queued_file_deletions(FakeSession())

    assert deleted_urls == ["/uploads/files/ok.pdf"]
    assert "提交后清理上传文件失败" in caplog.text
