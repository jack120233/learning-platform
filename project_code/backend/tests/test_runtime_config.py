"""运行版本配置与缓存抽象测试。"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import Settings
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


def test_windows_local_frontend_paths_point_to_ui_dist():
    settings = Settings(app_edition="windows_local")

    assert settings.parsed_frontend_dist_dir.name == "dist"
    assert settings.parsed_frontend_index_path.name == "index.html"
    assert settings.windows_local_frontend_ready in {True, False}


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
