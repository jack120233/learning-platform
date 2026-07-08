"""运行版本配置与缓存抽象测试。"""

import pytest
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import Settings
from app.core.cache import DiskCacheAdapter, InMemoryCache
from app.core.runtime import (
    configure_sqlite_runtime,
    initialize_database_schema,
    initialize_permission_defaults,
    seed_database_if_empty,
)
from app.main import should_serve_frontend_spa
from app.models.permission import RolePermission
from app.services.permission_service import permission_service


def test_windows_local_defaults_to_sqlite_file_and_diskcache(tmp_path):
    settings = Settings(
        _env_file=None,
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
        _env_file=None,
        app_edition="windows_classroom",
        database_url="sqlite+aiosqlite:///:memory:",
    )

    assert settings.async_database_url == "sqlite+aiosqlite:///:memory:"
    assert settings.is_sqlite_memory_database is True
    assert settings.is_sqlite_file_database is False
    assert settings.sqlalchemy_connect_args == {}


def test_server_defaults_to_memory_cache():
    settings = Settings(_env_file=None, app_edition="server")

    assert settings.effective_cache_backend == "memory"
    assert settings.async_database_url == "sqlite+aiosqlite:///:memory:"


def test_windows_local_frontend_paths_point_to_ui_dist():
    settings = Settings(_env_file=None, app_edition="windows_local")

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
async def test_diskcache_adapter_delegates_operations():
    class FakeCache:
        def __init__(self) -> None:
            self.store: dict[str, object] = {}

        def get(self, key: str, default: object = None) -> object:
            return self.store.get(key, default)

        def set(self, key: str, value: object, expire: int | None = None) -> bool:
            self.store[key] = value
            return True

        def delete(self, key: str) -> bool:
            return self.store.pop(key, None) is not None

        def clear(self) -> None:
            self.store.clear()

    cache = DiskCacheAdapter(cache=FakeCache())

    assert await cache.set("health", "ok", ttl=60) is True
    assert await cache.get("health") == "ok"
    assert await cache.delete("health") is True
    assert await cache.get("health") is None
    await cache.set("health", "ok", ttl=60)
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


@pytest.mark.asyncio
async def test_initialize_database_schema_does_not_preseed_teacher_only_permissions(tmp_path):
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'bootstrap.db'}")
    async_session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    try:
        async with engine.begin() as conn:
            await initialize_database_schema(conn)

        async with async_session_factory() as session:
            result = await session.execute(select(RolePermission.role, RolePermission.permission_id))
            assert result.all() == []

            await permission_service.ensure_schema_and_seed(session)

            role_permissions = await session.execute(
                select(RolePermission.role, RolePermission.permission_id)
                .order_by(RolePermission.role.asc(), RolePermission.permission_id.asc())
            )
            grouped: dict[str, list[int]] = {}
            for role, permission_id in role_permissions.all():
                grouped.setdefault(role, []).append(permission_id)

            assert grouped["student"] == [1, 11, 12, 13, 14]
            assert grouped["teacher"] == [1, 2, 11, 12, 13, 14, 21, 22, 23]
            assert grouped["admin"] == [1, 2, 3, 11, 12, 13, 14, 21, 22, 23, 31, 32, 33, 35, 36, 37, 38, 39]
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_initialize_permission_defaults_fills_new_database_completely(tmp_path):
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'windows-local.db'}")
    async_session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    try:
        async with engine.begin() as conn:
            await initialize_database_schema(conn)

        messages = await initialize_permission_defaults(async_session_factory)
        assert messages == []

        async with async_session_factory() as session:
            role_permissions = await session.execute(
                select(RolePermission.role, RolePermission.permission_id)
                .order_by(RolePermission.role.asc(), RolePermission.permission_id.asc())
            )
            grouped: dict[str, list[int]] = {}
            for role, permission_id in role_permissions.all():
                grouped.setdefault(role, []).append(permission_id)

            assert grouped["student"] == [1, 11, 12, 13, 14]
            assert grouped["teacher"] == [1, 2, 11, 12, 13, 14, 21, 22, 23]
            assert grouped["admin"] == [1, 2, 3, 11, 12, 13, 14, 21, 22, 23, 31, 32, 33, 35, 36, 37, 38, 39]
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_initialize_database_schema_repairs_sqlite_resource_progress_section_nullability(tmp_path):
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'legacy-resource-progress.db'}")

    try:
        async with engine.begin() as conn:
            await conn.execute(
                text(
                    "CREATE TABLE resource_progress ("
                    "id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, "
                    "user_id INTEGER NOT NULL, "
                    "course_id INTEGER NOT NULL, "
                    "chapter_id INTEGER NOT NULL, "
                    "section_id INTEGER NOT NULL, "
                    "resource_id INTEGER NOT NULL, "
                    "progress FLOAT NOT NULL DEFAULT 0.0, "
                    "position INTEGER NOT NULL DEFAULT 0, "
                    "is_completed BOOLEAN NOT NULL DEFAULT 0, "
                    "completed_at DATETIME NULL, "
                    "last_play_at DATETIME NULL, "
                    "created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP, "
                    "updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP"
                    ")"
                )
            )
            await conn.execute(text("CREATE INDEX idx_resource_progress_user_id ON resource_progress (user_id)"))
            await conn.execute(text("CREATE INDEX idx_resource_progress_course_id ON resource_progress (course_id)"))
            await conn.execute(text("CREATE INDEX idx_resource_progress_chapter_id ON resource_progress (chapter_id)"))
            await conn.execute(text("CREATE INDEX idx_resource_progress_section_id ON resource_progress (section_id)"))
            await conn.execute(text("CREATE INDEX idx_resource_progress_resource_id ON resource_progress (resource_id)"))
            await conn.execute(
                text(
                    "INSERT INTO resource_progress ("
                    "user_id, course_id, chapter_id, section_id, resource_id, "
                    "progress, position, is_completed, created_at, updated_at"
                    ") VALUES (1, 2, 3, 4, 5, 0.5, 12, 0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"
                )
            )

            messages = await initialize_database_schema(conn)

            pragma_rows = await conn.execute(text("PRAGMA table_info(resource_progress)"))
            columns = {row[1]: row for row in pragma_rows.fetchall()}
            data_rows = await conn.execute(
                text(
                    "SELECT user_id, course_id, chapter_id, section_id, resource_id, progress, position "
                    "FROM resource_progress"
                )
            )
            data = data_rows.one()

        assert "已将 resource_progress.section_id 调整为可空，支持章节级资源进度" in messages
        assert columns["section_id"][3] == 0
        assert data == (1, 2, 3, 4, 5, 0.5, 12)
    finally:
        await engine.dispose()
