"""运行版本配置与缓存抽象测试。"""

import pytest
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import Settings
from app.core import runtime
from app.core.cache import InMemoryCache, RedisCachePlaceholder
from app.core.runtime import configure_sqlite_runtime, seed_database_if_empty
from app.main import should_serve_frontend_spa


def test_windows_local_defaults_to_sqlite_file_and_diskcache(tmp_path):
    settings = Settings(
        app_edition="windows_local",
        windows_local_data_dir=str(tmp_path / "data"),
        windows_local_cache_dir=str(tmp_path / "data" / "cache"),
        windows_local_upload_dir=str(tmp_path / "uploads"),
        windows_local_log_dir=str(tmp_path / "logs"),
    )

    assert settings.async_database_url.startswith("sqlite+aiosqlite:///")
    assert settings.async_database_url.endswith("windows-local.db")
    assert settings.effective_cache_backend == "diskcache"
    assert settings.resolved_cache_dir == tmp_path / "data" / "cache"
    assert settings.resolved_upload_dir == tmp_path / "uploads"
    assert settings.resolved_log_dir == tmp_path / "logs"
    assert settings.sqlalchemy_connect_args == {"timeout": settings.sqlite_timeout_seconds}


def test_windows_classroom_defaults_to_isolated_sqlite_file_and_diskcache(tmp_path):
    settings = Settings(
        app_edition="windows_classroom",
        windows_classroom_data_dir=str(tmp_path / "data"),
        windows_classroom_cache_dir=str(tmp_path / "data" / "cache"),
        windows_classroom_upload_dir=str(tmp_path / "uploads"),
        windows_classroom_log_dir=str(tmp_path / "logs"),
    )

    assert settings.async_database_url.startswith("sqlite+aiosqlite:///")
    assert settings.async_database_url.endswith("windows-classroom.db")
    assert settings.effective_cache_backend == "diskcache"
    assert settings.resolved_cache_dir == tmp_path / "data" / "cache"
    assert settings.resolved_upload_dir == tmp_path / "uploads"
    assert settings.resolved_log_dir == tmp_path / "logs"
    assert settings.sqlalchemy_connect_args == {"timeout": settings.sqlite_timeout_seconds}
    assert settings.resolved_local_database_path.parent in settings.runtime_directories
    assert settings.resolved_cache_dir in settings.runtime_directories


def test_explicit_database_url_keeps_in_memory_sqlite_for_tests():
    settings = Settings(
        app_edition="windows_classroom",
        database_url="sqlite+aiosqlite:///:memory:",
    )

    assert settings.async_database_url == "sqlite+aiosqlite:///:memory:"
    assert settings.is_sqlite_memory_database is True
    assert settings.is_sqlite_file_database is False
    assert settings.sqlalchemy_connect_args == {}


def test_server_defaults_to_redis_cache_without_requiring_connection():
    settings = Settings(app_edition="server")

    assert settings.effective_cache_backend == "redis"
    assert settings.async_database_url == "sqlite+aiosqlite:///:memory:"


@pytest.mark.parametrize("app_edition", ["windows_local", "windows_classroom"])
def test_windows_frontend_paths_point_to_ui_dist(app_edition):
    settings = Settings(app_edition=app_edition)

    assert settings.parsed_frontend_dist_dir.name == "dist"
    assert settings.parsed_frontend_index_path.name == "index.html"
    assert settings.windows_frontend_ready in {True, False}


@pytest.mark.parametrize(
    "path",
    [
        "dashboard",
        "/courses/1",
        "teacher/courses/create",
    ],
)
def test_windows_local_spa_fallback_allows_frontend_routes(path):
    assert should_serve_frontend_spa(path, "/api/v1", "/uploads") is True


@pytest.mark.parametrize(
    "path",
    [
        "api",
        "api/unknown",
        "/api/v1/unknown",
        "uploads",
        "uploads/missing.png",
    ],
)
def test_windows_local_spa_fallback_excludes_api_and_upload_routes(path):
    assert should_serve_frontend_spa(path, "/api/v1", "/uploads") is False


def test_upload_static_files_support_range_requests(tmp_path):
    video_path = tmp_path / "sample.mp4"
    video_path.write_bytes(b"0123456789" * 200)
    app = FastAPI()
    app.mount("/uploads", StaticFiles(directory=tmp_path), name="uploads")

    response = TestClient(app).get(
        "/uploads/sample.mp4",
        headers={"Range": "bytes=0-9"},
    )

    assert response.status_code == 206
    assert response.headers["content-range"] == "bytes 0-9/2000"
    assert response.headers["accept-ranges"] == "bytes"
    assert response.content == b"0123456789"


@pytest.mark.asyncio
async def test_memory_cache_basic_operations():
    cache = InMemoryCache()

    assert await cache.get("missing", default="fallback") == "fallback"
    assert await cache.set("course:list", {"items": [1]}, ttl=60) is True
    assert await cache.get("course:list") == {"items": [1]}
    assert await cache.delete("course:list") is True
    assert await cache.get("course:list") is None


@pytest.mark.asyncio
async def test_redis_placeholder_does_not_require_live_redis():
    cache = RedisCachePlaceholder()

    assert await cache.set("health", "ok", ttl=60) is True
    assert await cache.get("health") == "ok"
    await cache.clear()
    assert await cache.get("health") is None


@pytest.mark.asyncio
async def test_sqlite_runtime_skips_pragmas_for_memory_database():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    try:
        async with engine.begin() as conn:
            messages = await configure_sqlite_runtime(conn)
        assert messages == []
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_windows_classroom_sqlite_runtime_enables_wal_and_busy_timeout(tmp_path, monkeypatch):
    database_path = tmp_path / "classroom.db"
    classroom_settings = Settings(
        app_edition="windows_classroom",
        database_url=f"sqlite+aiosqlite:///{database_path}",
        sqlite_busy_timeout_ms=12345,
    )
    monkeypatch.setattr(runtime, "settings", classroom_settings)
    engine = create_async_engine(classroom_settings.async_database_url)

    try:
        async with engine.begin() as conn:
            messages = await runtime.configure_sqlite_runtime(conn)
            busy_timeout = (await conn.execute(text("PRAGMA busy_timeout"))).scalar()
            journal_mode = (await conn.execute(text("PRAGMA journal_mode"))).scalar()

        assert "已设置 SQLite busy_timeout=12345ms" in messages
        assert "已设置 SQLite journal_mode=WAL" in messages
        assert busy_timeout == 12345
        assert str(journal_mode).lower() == "wal"
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_seed_database_if_empty_runs_only_when_empty(tmp_path):
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'seed.db'}")
    async_session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    calls: list[str] = []

    async def seed_runner() -> None:
        calls.append("called")

    try:
        async with engine.begin() as conn:
            from app.models import Base

            await conn.run_sync(Base.metadata.create_all)

        seeded = await seed_database_if_empty(async_session_factory, seed_runner)
        assert seeded is True
        assert calls == ["called"]

        async with async_session_factory() as session:
            from app.models.user import User

            session.add(User(username="existing", email="existing@example.com", password_hash="x", role="student", status="active"))
            await session.flush()
            await session.commit()

        calls.clear()
        seeded_again = await seed_database_if_empty(async_session_factory, seed_runner)
        assert seeded_again is False
        assert calls == []
    finally:
        await engine.dispose()
