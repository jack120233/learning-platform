"""运行版本配置与 SQLite bootstrap 测试。"""

from __future__ import annotations

import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import BASE_DIR, DEFAULT_ENV_FILE, REPOSITORY_ROOT, Settings, settings
from app.core.cache import DiskCacheAdapter, InMemoryCache
from app.core.dependencies import get_db
from app.core.runtime import (
    SQLITE_BOOTSTRAP_VERSION,
    configure_sqlite_runtime,
    describe_sqlite_bootstrap_status,
    ensure_sqlite_file_startup,
    get_sqlite_bootstrap_manifest_path,
    get_sqlite_temporary_database_path,
    get_temporary_manifest_path,
    initialize_database_schema,
    install_sqlite_runtime_hooks,
    reset_local_state,
)
from app.main import app, should_serve_frontend_spa
from app.models import Announcement, Category, Chapter, Course, Permission, Resource, RolePermission, Section, Tag, User
from app.services.permission_service import DEFAULT_ROLE_PERMISSION_IDS
from scripts.seed_data import (
    get_demo_document_runtime_paths,
    get_expected_demo_document_file_names,
    resolve_demo_document_runtime_path,
)


def test_settings_model_config_points_to_backend_env_file():
    env_file = Path(Settings.model_config["env_file"])

    assert env_file.is_absolute() is True
    assert env_file == DEFAULT_ENV_FILE
    assert env_file == BASE_DIR / ".env"


def test_defaults_to_sqlite_file_and_diskcache(tmp_path):
    instance = Settings(
        _env_file=None,
        local_data_dir=str(tmp_path / "data"),
        local_cache_dir=str(tmp_path / "data" / "cache"),
        upload_dir=str(tmp_path / "uploads"),
        log_dir=str(tmp_path / "logs"),
    )

    assert instance.async_database_url.startswith("sqlite+aiosqlite:///")
    assert instance.async_database_url.endswith("windows-local.db")
    assert instance.effective_cache_backend == "diskcache"
    assert instance.resolved_cache_dir == tmp_path / "data" / "cache"
    assert instance.resolved_upload_dir == tmp_path / "uploads"
    assert instance.resolved_log_dir == tmp_path / "logs"
    assert instance.sqlalchemy_connect_args == {"timeout": instance.sqlite_timeout_seconds}
    assert instance.resolved_sqlite_database_path == tmp_path / "data" / "windows-local.db"


def test_relative_sqlite_paths_resolve_to_backend_root():
    instance = Settings(
        _env_file=None,
        database_url="sqlite+aiosqlite:///./data/learning_platform.db",
        local_data_dir="./data",
        local_cache_dir="./data/cache",
        upload_dir="uploads",
        log_dir="logs",
    )

    expected_database_path = (BASE_DIR / "data" / "learning_platform.db").resolve()
    expected_cache_dir = (BASE_DIR / "data" / "cache").resolve()
    expected_upload_dir = (BASE_DIR / "uploads").resolve()
    expected_log_dir = (BASE_DIR / "logs").resolve()

    assert instance.resolved_sqlite_database_path == expected_database_path
    assert instance.async_database_url == f"sqlite+aiosqlite:///{expected_database_path.as_posix()}"
    assert instance.resolved_cache_dir == expected_cache_dir
    assert instance.resolved_upload_dir == expected_upload_dir
    assert instance.resolved_log_dir == expected_log_dir


def test_explicit_database_url_keeps_in_memory_sqlite_for_tests():
    instance = Settings(
        _env_file=None,
        database_url="sqlite+aiosqlite:///:memory:",
    )

    assert instance.async_database_url == "sqlite+aiosqlite:///:memory:"
    assert instance.is_sqlite_memory_database is True
    assert instance.is_sqlite_file_database is False
    assert instance.resolved_sqlite_database_path is None
    assert instance.sqlalchemy_connect_args == {}


def test_auto_cache_defaults_to_diskcache():
    instance = Settings(_env_file=None)

    assert instance.effective_cache_backend == "diskcache"
    assert instance.async_database_url.endswith("windows-local.db")
    assert instance.resolved_sqlite_database_path == (BASE_DIR / "data" / "windows-local.db").resolve()


def test_frontend_paths_point_to_ui_dist():
    instance = Settings(_env_file=None)

    assert instance.parsed_frontend_dist_dir.name == "dist"
    assert instance.parsed_frontend_index_path.name == "index.html"
    assert instance.frontend_ready in {True, False}


def test_runtime_root_dir_rebases_relative_release_paths(tmp_path):
    runtime_root = tmp_path / "LearningPlatform"
    instance = Settings(
        _env_file=None,
        runtime_root_dir=str(runtime_root),
        local_data_dir="data",
        local_cache_dir="data/cache",
        upload_dir="uploads",
        log_dir="logs",
        frontend_dist_dir="frontend/dist",
        frontend_index_path="frontend/dist/index.html",
    )

    assert instance.resolved_runtime_root_dir == runtime_root.resolve()
    assert instance.resolved_local_data_dir == (runtime_root / "data").resolve()
    assert instance.resolved_cache_dir == (runtime_root / "data" / "cache").resolve()
    assert instance.resolved_upload_dir == (runtime_root / "uploads").resolve()
    assert instance.resolved_log_dir == (runtime_root / "logs").resolve()
    assert instance.parsed_frontend_dist_dir == (runtime_root / "frontend" / "dist").resolve()
    assert instance.parsed_frontend_index_path == (
        runtime_root / "frontend" / "dist" / "index.html"
    ).resolve()


def test_init_db_script_bootstraps_standard_database_from_repo_root(tmp_path):
    data_dir = tmp_path / "data"
    uploads_dir = tmp_path / "uploads"
    logs_dir = tmp_path / "logs"
    cache_dir = tmp_path / "cache"
    database_path = data_dir / "script-init.db"
    manifest_path = get_sqlite_bootstrap_manifest_path(database_path)

    env = os.environ.copy()
    env.update(
        {
            "PYTHONPATH": str(BASE_DIR),
            "DATABASE_URL": f"sqlite+aiosqlite:///{database_path.as_posix()}",
            "UPLOAD_DIR": str(uploads_dir),
            "LOG_DIR": str(logs_dir),
            "LOCAL_DATA_DIR": str(data_dir),
            "LOCAL_CACHE_DIR": str(cache_dir),
        }
    )

    result = subprocess.run(
        [sys.executable, str(REPOSITORY_ROOT / "project_code" / "backend" / "scripts" / "init_db.py")],
        cwd=REPOSITORY_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )

    assert "已完成标准 SQLite 初始化" in result.stdout
    assert database_path.exists() is True
    assert manifest_path.exists() is True
    demo_document_paths = sorted((uploads_dir / "demo-documents").glob("*.md"))
    assert [path.name for path in demo_document_paths] == sorted(get_expected_demo_document_file_names())


@pytest.mark.parametrize(
    "path",
    [
        "dashboard",
        "/courses/1",
        "teacher/courses/create",
    ],
)
def test_spa_fallback_allows_frontend_routes(path):
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
def test_spa_fallback_excludes_api_and_upload_routes(path):
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


@pytest.fixture
def sqlite_runtime_settings(tmp_path, monkeypatch):
    data_dir = tmp_path / "data"
    uploads_dir = tmp_path / "uploads"
    logs_dir = tmp_path / "logs"
    cache_dir = tmp_path / "cache"
    database_path = data_dir / "learning_platform.db"
    manifest_path = get_sqlite_bootstrap_manifest_path(database_path)
    database_url = f"sqlite+aiosqlite:///{database_path.as_posix()}"

    monkeypatch.setattr(settings, "database_url", database_url)
    monkeypatch.setattr(settings, "upload_dir", str(uploads_dir))
    monkeypatch.setattr(settings, "log_dir", str(logs_dir))
    monkeypatch.setattr(settings, "local_data_dir", str(data_dir))
    monkeypatch.setattr(settings, "local_cache_dir", str(cache_dir))
    monkeypatch.setattr(settings, "local_database_filename", "learning_platform.db")

    return {
        "tmp_path": tmp_path,
        "data_dir": data_dir,
        "uploads_dir": uploads_dir,
        "logs_dir": logs_dir,
        "cache_dir": cache_dir,
        "database_path": database_path,
        "database_url": database_url,
        "manifest_path": manifest_path,
        "temporary_database_path": get_sqlite_temporary_database_path(database_path),
        "temporary_manifest_path": get_temporary_manifest_path(manifest_path),
    }


async def _open_session_factory(database_path: Path) -> tuple[Any, async_sessionmaker[AsyncSession]]:
    engine = create_async_engine(
        f"sqlite+aiosqlite:///{database_path.as_posix()}",
        connect_args={"timeout": settings.sqlite_timeout_seconds},
    )
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    return engine, session_factory


@pytest.mark.asyncio
async def test_ensure_sqlite_file_startup_bootstraps_standard_database(sqlite_runtime_settings):
    database_path = sqlite_runtime_settings["database_path"]
    manifest_path = sqlite_runtime_settings["manifest_path"]

    result = await ensure_sqlite_file_startup()

    assert result.status == "bootstrapped"
    assert database_path.exists() is True
    assert manifest_path.exists() is True
    assert sqlite_runtime_settings["uploads_dir"] in result.directories
    assert sqlite_runtime_settings["logs_dir"] in result.directories
    assert sqlite_runtime_settings["cache_dir"] in result.directories
    assert any("已写入默认权限与角色权限" in message for message in result.messages)

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["bootstrap_version"] == SQLITE_BOOTSTRAP_VERSION
    assert manifest["seed_profile"] == "base,demo"
    assert manifest["initialized_at"]

    engine, session_factory = await _open_session_factory(database_path)
    try:
        async with session_factory() as session:
            users = await session.execute(select(User.username).order_by(User.id.asc()))
            categories = await session.execute(select(Category.name).order_by(Category.id.asc()))
            tags = await session.execute(select(Tag.name).order_by(Tag.id.asc()))
            courses = await session.execute(
                select(Course.title, Course.total_sections, Course.total_duration).order_by(Course.id.asc())
            )
            chapters = await session.execute(
                select(Chapter.section_count, Chapter.total_duration).order_by(Chapter.id.asc())
            )
            sections = await session.execute(
                select(Section.resource_count, Section.duration).order_by(Section.id.asc())
            )
            resources = await session.execute(
                select(Resource.type, Resource.duration, Resource.file_url).order_by(Resource.id.asc())
            )
            announcements = await session.execute(select(Announcement.title).order_by(Announcement.id.asc()))
            permissions = await session.execute(select(Permission.id))
            role_permissions = await session.execute(select(RolePermission.id))
            admin_role_permissions = await session.execute(
                select(RolePermission.permission_id)
                .where(RolePermission.role == "admin")
                .order_by(RolePermission.permission_id.asc())
            )

        assert list(users.scalars().all()) == ["admin1", "teacher1", "student1"]
        category_names = list(categories.scalars().all())
        tag_names = list(tags.scalars().all())
        assert len(category_names) == 6
        assert "智能网联" in category_names
        assert len(tag_names) == 11
        assert "智能网联" in tag_names
        assert courses.all() == [
            ("Python入门", 4, 0),
            ("FastAPI实战", 4, 0),
        ]
        assert chapters.all() == [(2, 0), (2, 0), (2, 0), (2, 0)]
        assert sections.all() == [(1, 0)] * 8
        resource_rows = resources.all()
        assert len(resource_rows) == 8
        assert all(resource_type == "document" for resource_type, _duration, _file_url in resource_rows)
        assert all(duration == 0 for _resource_type, duration, _file_url in resource_rows)
        actual_document_names = {
            resolve_demo_document_runtime_path(file_url).name
            for _resource_type, _duration, file_url in resource_rows
        }
        assert actual_document_names == set(get_expected_demo_document_file_names())
        assert all(path.is_file() for path in get_demo_document_runtime_paths())
        assert len(announcements.scalars().all()) == 2
        assert len(permissions.scalars().all()) == 19
        assert len(role_permissions.scalars().all()) == 33
        assert list(admin_role_permissions.scalars().all()) == sorted(DEFAULT_ROLE_PERMISSION_IDS["admin"])

        inspection = describe_sqlite_bootstrap_status(database_path)
        assert inspection.status == "standard"
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_ensure_sqlite_file_startup_skips_standard_database_without_writing(sqlite_runtime_settings):
    database_path = sqlite_runtime_settings["database_path"]
    manifest_path = sqlite_runtime_settings["manifest_path"]

    first_result = await ensure_sqlite_file_startup()
    assert first_result.status == "bootstrapped"

    database_mtime = database_path.stat().st_mtime_ns
    manifest_mtime = manifest_path.stat().st_mtime_ns
    demo_document_path = get_demo_document_runtime_paths()[0]
    demo_document_mtime = demo_document_path.stat().st_mtime_ns

    second_result = await ensure_sqlite_file_startup()

    assert second_result.status == "skipped"
    assert any("检测到标准 SQLite 初始化状态" in message for message in second_result.messages)
    assert database_path.stat().st_mtime_ns == database_mtime
    assert manifest_path.stat().st_mtime_ns == manifest_mtime
    assert demo_document_path.stat().st_mtime_ns == demo_document_mtime


@pytest.mark.asyncio
async def test_install_sqlite_runtime_hooks_configure_new_file_connections(
    sqlite_runtime_settings,
):
    sqlite_runtime_settings["database_path"].parent.mkdir(parents=True, exist_ok=True)
    runtime_engine = create_async_engine(
        sqlite_runtime_settings["database_url"],
        connect_args={"timeout": 0},
    )
    install_sqlite_runtime_hooks(runtime_engine)

    try:
        async with runtime_engine.connect() as conn:
            busy_timeout = (await conn.execute(text("PRAGMA busy_timeout"))).scalar()

        assert busy_timeout == settings.sqlite_busy_timeout_ms
    finally:
        await runtime_engine.dispose()


@pytest.mark.asyncio
async def test_ensure_sqlite_file_startup_blocks_database_without_manifest(sqlite_runtime_settings):
    database_path = sqlite_runtime_settings["database_path"]
    database_path.parent.mkdir(parents=True, exist_ok=True)
    database_path.touch()

    result = await ensure_sqlite_file_startup()

    assert result.status == "blocked"
    assert any("缺少 bootstrap 清单" in message for message in result.messages)
    assert any("reset_local_state.py" in message for message in result.messages)


@pytest.mark.asyncio
async def test_ensure_sqlite_file_startup_blocks_manifest_without_database(sqlite_runtime_settings):
    manifest_path = sqlite_runtime_settings["manifest_path"]
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        json.dumps(
            {
                "bootstrap_version": SQLITE_BOOTSTRAP_VERSION,
                "seed_profile": "base,demo",
                "initialized_at": "2026-07-08T00:00:00+00:00",
            }
        ),
        encoding="utf-8",
    )

    result = await ensure_sqlite_file_startup()

    assert result.status == "blocked"
    assert any("缺少 SQLite 数据库" in message for message in result.messages)
    assert any("reset_local_state.py" in message for message in result.messages)


@pytest.mark.asyncio
async def test_ensure_sqlite_file_startup_blocks_manifest_version_mismatch(sqlite_runtime_settings):
    database_path = sqlite_runtime_settings["database_path"]
    manifest_path = sqlite_runtime_settings["manifest_path"]
    database_path.parent.mkdir(parents=True, exist_ok=True)
    database_path.touch()
    manifest_path.write_text(
        json.dumps(
            {
                "bootstrap_version": "2025-01-01.0",
                "seed_profile": "base,demo",
                "initialized_at": "2026-07-08T00:00:00+00:00",
            }
        ),
        encoding="utf-8",
    )

    result = await ensure_sqlite_file_startup()

    assert result.status == "blocked"
    assert any("版本不匹配" in message for message in result.messages)
    assert any("reset_local_state.py" in message for message in result.messages)


@pytest.mark.asyncio
async def test_reset_local_state_clears_database_manifest_uploads_cache_and_logs(sqlite_runtime_settings):
    database_path = sqlite_runtime_settings["database_path"]
    manifest_path = sqlite_runtime_settings["manifest_path"]
    temporary_database_path = sqlite_runtime_settings["temporary_database_path"]
    temporary_manifest_path = sqlite_runtime_settings["temporary_manifest_path"]
    uploads_dir = sqlite_runtime_settings["uploads_dir"]
    logs_dir = sqlite_runtime_settings["logs_dir"]
    cache_dir = sqlite_runtime_settings["cache_dir"]

    result = await ensure_sqlite_file_startup()
    assert result.status == "bootstrapped"
    assert all(path.is_file() for path in get_demo_document_runtime_paths())

    uploads_dir.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)
    cache_dir.mkdir(parents=True, exist_ok=True)
    (uploads_dir / "demo.txt").write_text("upload", encoding="utf-8")
    (logs_dir / "app.log").write_text("log", encoding="utf-8")
    (cache_dir / "cache.bin").write_text("cache", encoding="utf-8")
    temporary_database_path.write_text("temp-db", encoding="utf-8")
    Path(f"{temporary_database_path}-wal").write_text("temp-wal", encoding="utf-8")
    temporary_manifest_path.write_text("{}", encoding="utf-8")

    messages = reset_local_state()

    assert database_path.exists() is False
    assert manifest_path.exists() is False
    assert temporary_database_path.exists() is False
    assert temporary_manifest_path.exists() is False
    assert list(uploads_dir.iterdir()) == []
    assert all(path.exists() is False for path in get_demo_document_runtime_paths())
    assert list(logs_dir.iterdir()) == []
    assert list(cache_dir.iterdir()) == []
    assert any("下次启动将执行首次初始化" in message for message in messages)


@pytest.mark.asyncio
async def test_reset_and_rebootstrap_recreates_demo_documents(sqlite_runtime_settings):
    reset_local_state()

    result = await ensure_sqlite_file_startup()

    assert result.status == "bootstrapped"
    assert all(path.is_file() for path in get_demo_document_runtime_paths())


@pytest.mark.asyncio
async def test_login_api_succeeds_after_reset_and_bootstrap(sqlite_runtime_settings):
    database_path = sqlite_runtime_settings["database_path"]

    reset_local_state()
    startup_result = await ensure_sqlite_file_startup()
    assert startup_result.status == "bootstrapped"

    engine, session_factory = await _open_session_factory(database_path)

    async def override_get_db():
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
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://testserver",
        ) as client:
            response = await client.post(
                "/api/v1/auth/login",
                json={
                    "login_id": "admin1@example.com",
                    "password": "Admin123456",
                    "remember_me": False,
                },
            )

        payload = response.json()
        assert response.status_code == 200
        assert payload["code"] == 200
        assert payload["data"]["user"]["username"] == "admin1"
        assert payload["data"]["user"]["email"] == "admin1@example.com"
        assert payload["data"]["access_token"]
        assert payload["data"]["refresh_token"]
    finally:
        app.dependency_overrides.clear()
        await engine.dispose()


@pytest.mark.asyncio
async def test_initialize_database_schema_backfills_legacy_user_columns(tmp_path):
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'legacy-users.db'}")

    try:
        async with engine.begin() as conn:
            await conn.execute(
                text(
                    "CREATE TABLE users ("
                    "username VARCHAR(50) NOT NULL, "
                    "email VARCHAR(100) NOT NULL, "
                    "phone VARCHAR(20), "
                    "password_hash VARCHAR(255) NOT NULL, "
                    "nickname VARCHAR(50), "
                    "avatar VARCHAR(500), "
                    "bio TEXT, "
                    "role VARCHAR(20) NOT NULL, "
                    "status VARCHAR(20) NOT NULL, "
                    "last_login_at DATETIME, "
                    "login_fail_count INTEGER NOT NULL DEFAULT 0, "
                    "locked_until DATETIME, "
                    "id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, "
                    "created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP, "
                    "updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP"
                    ")"
                )
            )
            await conn.execute(text("CREATE UNIQUE INDEX ix_users_username ON users (username)"))
            await conn.execute(text("CREATE UNIQUE INDEX ix_users_email ON users (email)"))
            await conn.execute(text("CREATE INDEX ix_users_status ON users (status)"))
            await conn.execute(text("CREATE INDEX ix_users_role ON users (role)"))
            await conn.execute(
                text(
                    "INSERT INTO users (username, email, password_hash, role, status, login_fail_count) "
                    "VALUES ('admin1', 'admin1@example.com', 'x', 'admin', 'active', 0)"
                )
            )

            messages = await initialize_database_schema(conn)

            pragma_rows = await conn.execute(text("PRAGMA table_info(users)"))
            columns = {row[1]: row for row in pragma_rows.fetchall()}
            data_row = await conn.execute(
                text(
                    "SELECT username, email, original_username, username_change_remaining "
                    "FROM users WHERE email = 'admin1@example.com'"
                )
            )
            data = data_row.one()

        assert "已为 users 表补充 original_username 字段" in messages
        assert "已为 users 表补充 username_change_remaining 字段" in messages
        assert "original_username" in columns
        assert "username_change_remaining" in columns
        assert columns["username_change_remaining"][3] == 1
        assert data == ("admin1", "admin1@example.com", None, 1)
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
