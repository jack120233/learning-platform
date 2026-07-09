"""本地运行时初始化工具。"""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import shutil
from typing import Any, Literal

from sqlalchemy import event, select, text
from sqlalchemy.engine import URL
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine, async_sessionmaker, create_async_engine

from app.config import settings
from app.models.user import User


SQLITE_BOOTSTRAP_VERSION = "2026-07-09.1"
SQLITE_BOOTSTRAP_ENVIRONMENT = "sqlite_file"
BASE_SEED_LAYER = "base"
DEMO_SEED_LAYER = "demo"
DEFAULT_SQLITE_SEED_LAYERS: tuple[str, ...] = (BASE_SEED_LAYER, DEMO_SEED_LAYER)
SQLITE_BOOTSTRAP_MANIFEST_FILENAME = ".sqlite-bootstrap.json"
SQLITE_DATABASE_ARTIFACT_SUFFIXES = ("", "-wal", "-shm", "-journal")
STANDARD_SQLITE_EXPECTED_ROW_COUNTS: dict[str, int] = {
    "users": 3,
    "categories": 5,
    "tags": 10,
    "courses": 2,
    "chapters": 4,
    "sections": 8,
    "resources": 8,
    "announcements": 2,
    "permissions": 19,
    "role_permissions": 33,
    "course_tags": 4,
}
SQLITE_BOOTSTRAP_REQUIRED_TABLES = frozenset(
    {
        "announcements",
        "categories",
        "chapters",
        "courses",
        "permissions",
        "refresh_tokens",
        "resources",
        "role_permissions",
        "sections",
        "tags",
        "users",
    }
)
RESET_LOCAL_STATE_HINT = "检测到非标准本地库，请先运行 reset_local_state.py 清空本地状态"


@dataclass(frozen=True)
class SqliteBootstrapInspection:
    """SQLite 首启状态检查结果。"""

    status: Literal["empty", "standard", "blocked"]
    database_path: Path
    manifest_path: Path
    messages: list[str]


@dataclass(frozen=True)
class SqliteStartupResult:
    """SQLite 启动判定结果。"""

    status: Literal["bootstrapped", "skipped", "blocked"]
    database_path: Path
    manifest_path: Path
    directories: list[Path]
    messages: list[str]


def ensure_runtime_directories() -> list[Path]:
    """确保当前运行版本需要的本地目录存在。"""
    created_or_existing: list[Path] = []
    for directory in settings.runtime_directories:
        directory.mkdir(parents=True, exist_ok=True)
        created_or_existing.append(directory)
    return created_or_existing


def _is_sqlite_file_url(url: URL) -> bool:
    """判断给定 URL 是否为文件型 SQLite。"""
    if not url.drivername.startswith("sqlite"):
        return False

    database = url.database or ""
    if database in {"", ":memory:"}:
        return False

    return url.query.get("mode") != "memory"


def serialize_seed_layers(seed_layers: Iterable[str]) -> str:
    """将种子层集合序列化为稳定字符串。"""
    return ",".join(sorted(dict.fromkeys(seed_layers)))


def get_sqlite_bootstrap_manifest_path(database_path: Path) -> Path:
    """返回 SQLite bootstrap 清单路径。"""
    return database_path.parent / SQLITE_BOOTSTRAP_MANIFEST_FILENAME


def get_sqlite_temporary_database_path(database_path: Path) -> Path:
    """返回 SQLite 临时库路径。"""
    return Path(f"{database_path}.tmp")


def get_temporary_manifest_path(manifest_path: Path) -> Path:
    """返回 bootstrap 清单临时文件路径。"""
    return Path(f"{manifest_path}.tmp")


def _load_bootstrap_manifest(manifest_path: Path) -> dict[str, Any]:
    with manifest_path.open("r", encoding="utf-8") as fp:
        payload = json.load(fp)
    if not isinstance(payload, dict):
        raise ValueError("bootstrap 清单格式错误")
    return payload


def inspect_sqlite_bootstrap_state(
    database_path: Path,
    expected_seed_layers: tuple[str, ...] = DEFAULT_SQLITE_SEED_LAYERS,
) -> SqliteBootstrapInspection:
    """按三态规则检查文件型 SQLite 是否处于标准首启状态。"""
    manifest_path = get_sqlite_bootstrap_manifest_path(database_path)
    database_exists = database_path.exists()
    manifest_exists = manifest_path.exists()
    expected_seed_profile = serialize_seed_layers(expected_seed_layers)

    if not database_exists and not manifest_exists:
        return SqliteBootstrapInspection(
            status="empty",
            database_path=database_path,
            manifest_path=manifest_path,
            messages=["未发现 SQLite 数据库和 bootstrap 清单，将执行首次初始化"],
        )

    if database_exists and manifest_exists:
        try:
            manifest = _load_bootstrap_manifest(manifest_path)
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            return SqliteBootstrapInspection(
                status="blocked",
                database_path=database_path,
                manifest_path=manifest_path,
                messages=[
                    f"bootstrap 清单不可用: {exc}",
                    RESET_LOCAL_STATE_HINT,
                ],
            )

        bootstrap_version = manifest.get("bootstrap_version")
        seed_profile = manifest.get("seed_profile")
        initialized_at = manifest.get("initialized_at")
        if bootstrap_version != SQLITE_BOOTSTRAP_VERSION:
            return SqliteBootstrapInspection(
                status="blocked",
                database_path=database_path,
                manifest_path=manifest_path,
                messages=[
                    "bootstrap 清单版本不匹配",
                    RESET_LOCAL_STATE_HINT,
                ],
            )
        if seed_profile != expected_seed_profile:
            return SqliteBootstrapInspection(
                status="blocked",
                database_path=database_path,
                manifest_path=manifest_path,
                messages=[
                    "bootstrap 清单种子配置不匹配",
                    RESET_LOCAL_STATE_HINT,
                ],
            )
        if not initialized_at:
            return SqliteBootstrapInspection(
                status="blocked",
                database_path=database_path,
                manifest_path=manifest_path,
                messages=[
                    "bootstrap 清单缺少 initialized_at",
                    RESET_LOCAL_STATE_HINT,
                ],
            )

        return SqliteBootstrapInspection(
            status="standard",
            database_path=database_path,
            manifest_path=manifest_path,
            messages=["检测到标准 SQLite 初始化状态，跳过首次初始化"],
        )

    if database_exists:
        reason = "已发现 SQLite 数据库，但缺少 bootstrap 清单"
    else:
        reason = "已发现 bootstrap 清单，但缺少 SQLite 数据库"

    return SqliteBootstrapInspection(
        status="blocked",
        database_path=database_path,
        manifest_path=manifest_path,
        messages=[reason, RESET_LOCAL_STATE_HINT],
    )


def clear_directory_contents(directory: Path) -> None:
    """清空目录内容但保留目录本身。"""
    if not directory.exists():
        directory.mkdir(parents=True, exist_ok=True)
        return

    for child in directory.iterdir():
        if child.is_dir():
            shutil.rmtree(child)
        else:
            child.unlink()


def delete_sqlite_database_files(database_path: Path) -> list[str]:
    """删除 SQLite 数据库及其关联 WAL/SHM 文件。"""
    messages: list[str] = []
    for suffix in SQLITE_DATABASE_ARTIFACT_SUFFIXES:
        artifact_path = database_path if not suffix else Path(f"{database_path}{suffix}")
        if artifact_path.exists():
            artifact_path.unlink()
            messages.append(f"已删除 {artifact_path.name}")
    return messages


def delete_bootstrap_manifest_files(manifest_path: Path) -> list[str]:
    """删除 bootstrap 清单及其临时文件。"""
    messages: list[str] = []
    for artifact_path in (manifest_path, get_temporary_manifest_path(manifest_path)):
        if artifact_path.exists():
            artifact_path.unlink()
            messages.append(f"已删除 {artifact_path.name}")
    return messages


async def configure_sqlite_runtime(conn: AsyncConnection) -> list[str]:
    """为 SQLite 文件数据库应用本地运行优化。"""
    if not _is_sqlite_file_url(conn.engine.url):
        return []

    messages: list[str] = []
    await conn.execute(text(f"PRAGMA busy_timeout={settings.sqlite_busy_timeout_ms}"))
    messages.append(f"已设置 SQLite busy_timeout={settings.sqlite_busy_timeout_ms}ms")

    if settings.app_edition == "windows_classroom":
        result = await conn.execute(text("PRAGMA journal_mode=WAL"))
        journal_mode = (result.scalar() or "").upper()
        messages.append(f"已设置 SQLite journal_mode={journal_mode or 'WAL'}")

    return messages


def install_sqlite_runtime_hooks(engine: AsyncEngine) -> None:
    """为 SQLite 文件数据库安装连接级运行参数。"""
    if not _is_sqlite_file_url(engine.url):
        return

    if getattr(engine.sync_engine, "_learning_platform_sqlite_runtime_hooks", False):
        return

    @event.listens_for(engine.sync_engine, "connect")
    def _configure_sqlite_on_connect(dbapi_connection, _connection_record) -> None:
        cursor = dbapi_connection.cursor()
        try:
            cursor.execute(f"PRAGMA busy_timeout={settings.sqlite_busy_timeout_ms}")
            if settings.app_edition == "windows_classroom":
                cursor.execute("PRAGMA journal_mode=WAL")
                cursor.fetchone()
        finally:
            cursor.close()

    setattr(engine.sync_engine, "_learning_platform_sqlite_runtime_hooks", True)


async def create_database_schema(conn: AsyncConnection) -> list[str]:
    """创建当前代码对应的完整表结构。"""
    from app.models import Base

    await conn.run_sync(Base.metadata.create_all)
    return ["已创建数据库表结构"]


async def initialize_database_schema(conn: AsyncConnection) -> list[str]:
    """创建数据库表并执行历史兼容修复。"""
    from app.core.db_schema import ensure_database_compatibility

    messages = await create_database_schema(conn)
    messages.extend(await ensure_database_compatibility(conn))
    return messages


async def seed_database_if_empty(
    session_factory: async_sessionmaker[Any],
    seed_runner: Callable[[], object] | None = None,
) -> bool:
    """兼容旧脚本调用：仅当无用户时导入演示种子。"""
    async with session_factory() as session:
        result = await session.execute(select(User.id).limit(1))
        if result.scalar_one_or_none() is not None:
            return False

    if seed_runner is None:
        from scripts.seed_data import seed_database as seed_runner

    await seed_runner()
    return True


async def initialize_permission_defaults(
    session_factory: async_sessionmaker[Any],
) -> list[str]:
    """手工初始化权限默认数据，并在发现缺失时补录。"""
    from app.services.permission_service import permission_service

    async with session_factory() as session:
        await permission_service.ensure_schema_and_seed(session)
        messages = await permission_service.check_and_backfill_default_permissions(session)
        await session.commit()
    return messages


async def initialize_standard_sqlite_data(
    session_factory: async_sessionmaker[Any],
    seed_layers: tuple[str, ...] = DEFAULT_SQLITE_SEED_LAYERS,
) -> list[str]:
    """初始化标准 SQLite 首启数据。"""
    from app.services.permission_service import permission_service
    from scripts.seed_data import seed_base_data, seed_demo_data

    async with session_factory() as session:
        await permission_service.ensure_schema_and_seed(session)
        await seed_base_data(session)
        if DEMO_SEED_LAYER in seed_layers:
            await seed_demo_data(session)
        await session.commit()

    messages = [
        "已写入默认权限与角色权限",
        "已写入基础数据",
    ]
    if DEMO_SEED_LAYER in seed_layers:
        messages.append("已写入演示数据")
    return messages


def validate_standard_sqlite_database(database_path: Path) -> list[str]:
    """校验标准首启数据库产物。"""
    from app.services.permission_service import DEFAULT_PERMISSIONS, DEFAULT_ROLE_PERMISSION_IDS
    from scripts.seed_data import (
        get_demo_document_runtime_paths,
        get_expected_demo_document_file_names,
        resolve_demo_document_runtime_path,
    )

    messages: list[str] = []

    with sqlite3.connect(database_path) as conn:
        table_rows = conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'").fetchall()
        tables = {row[0] for row in table_rows}
        missing_tables = sorted(SQLITE_BOOTSTRAP_REQUIRED_TABLES - tables)
        if missing_tables:
            raise RuntimeError(f"标准首启校验失败，缺少表: {', '.join(missing_tables)}")
        messages.append(f"已校验核心表 {len(SQLITE_BOOTSTRAP_REQUIRED_TABLES)} 张")

        default_users = {"admin1", "teacher1", "student1"}
        user_rows = conn.execute(
            "SELECT username FROM users WHERE username IN (?, ?, ?)",
            tuple(sorted(default_users)),
        ).fetchall()
        actual_users = {row[0] for row in user_rows}
        if actual_users != default_users:
            raise RuntimeError("标准首启校验失败，默认账号不完整")
        messages.append("已校验 3 个默认账号")

        for table_name, expected_count in STANDARD_SQLITE_EXPECTED_ROW_COUNTS.items():
            actual_count = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
            if actual_count != expected_count:
                raise RuntimeError(
                    f"标准首启校验失败，{table_name} 数量不正确: {actual_count} != {expected_count}"
                )
        messages.append("已校验标准种子数量")

        invalid_section_count = conn.execute(
            "SELECT COUNT(*) FROM sections WHERE resource_count != 1 OR duration != 0"
        ).fetchone()[0]
        if invalid_section_count:
            raise RuntimeError("标准首启校验失败，小节资源数量或时长不正确")

        invalid_chapter_count = conn.execute(
            "SELECT COUNT(*) FROM chapters WHERE section_count != 2 OR total_duration != 0"
        ).fetchone()[0]
        if invalid_chapter_count:
            raise RuntimeError("标准首启校验失败，章节结构或时长不正确")

        invalid_course_count = conn.execute(
            "SELECT COUNT(*) FROM courses WHERE total_sections != 4 OR total_duration != 0"
        ).fetchone()[0]
        if invalid_course_count:
            raise RuntimeError("标准首启校验失败，课程总节数或总时长不正确")
        messages.append("已校验课程结构与时长口径")

        course_titles = [
            row[0]
            for row in conn.execute("SELECT title FROM courses ORDER BY id").fetchall()
        ]
        if course_titles != ["Python入门", "FastAPI实战"]:
            raise RuntimeError("标准首启校验失败，课程标题不正确")

        permission_ids = {row[0] for row in conn.execute("SELECT id FROM permissions").fetchall()}
        expected_permission_ids = {seed.id for seed in DEFAULT_PERMISSIONS}
        if permission_ids != expected_permission_ids:
            raise RuntimeError("标准首启校验失败，默认权限定义不完整")

        for role, expected_permission_ids_for_role in DEFAULT_ROLE_PERMISSION_IDS.items():
            actual_permission_ids_for_role = [
                row[0]
                for row in conn.execute(
                    "SELECT permission_id FROM role_permissions WHERE role = ? ORDER BY permission_id",
                    (role,),
                ).fetchall()
            ]
            if actual_permission_ids_for_role != sorted(expected_permission_ids_for_role):
                raise RuntimeError(f"标准首启校验失败，{role} 角色默认权限不正确")
        messages.append("已校验权限与角色权限")

        expected_demo_document_file_names = set(get_expected_demo_document_file_names())
        actual_demo_document_file_names: set[str] = set()
        resource_rows = conn.execute(
            "SELECT type, file_url FROM resources ORDER BY id"
        ).fetchall()
        for resource_type, file_url in resource_rows:
            if resource_type != "document":
                raise RuntimeError("标准首启校验失败，演示资源类型不是文档")
            try:
                runtime_path = resolve_demo_document_runtime_path(file_url)
            except ValueError as exc:
                raise RuntimeError(f"标准首启校验失败，演示资源地址不正确: {exc}") from exc
            if not runtime_path.is_file():
                raise RuntimeError(f"标准首启校验失败，缺少演示文档文件: {runtime_path.name}")
            actual_demo_document_file_names.add(runtime_path.name)

        if actual_demo_document_file_names != expected_demo_document_file_names:
            raise RuntimeError("标准首启校验失败，演示文档文件集合不完整")

        missing_runtime_documents = [
            path.name for path in get_demo_document_runtime_paths() if not path.is_file()
        ]
        if missing_runtime_documents:
            raise RuntimeError(
                f"标准首启校验失败，演示文档文件缺失: {', '.join(missing_runtime_documents)}"
            )
        messages.append("已校验演示文档资源")

    return messages


def write_sqlite_bootstrap_manifest(
    manifest_path: Path,
    seed_layers: tuple[str, ...] = DEFAULT_SQLITE_SEED_LAYERS,
) -> list[str]:
    """写入 bootstrap 清单。"""
    temporary_manifest_path = get_temporary_manifest_path(manifest_path)
    payload = {
        "bootstrap_version": SQLITE_BOOTSTRAP_VERSION,
        "seed_profile": serialize_seed_layers(seed_layers),
        "initialized_at": datetime.now(timezone.utc).isoformat(),
    }

    with temporary_manifest_path.open("w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=2)
        fp.write("\n")
    temporary_manifest_path.replace(manifest_path)

    if not manifest_path.exists():
        raise RuntimeError("bootstrap 清单写入失败")

    return [f"已写入 bootstrap 清单: {manifest_path.name}"]


def _sqlite_url_for_path(database_path: Path) -> str:
    return f"sqlite+aiosqlite:///{database_path.as_posix()}"


async def bootstrap_sqlite_database(
    database_path: Path,
    seed_layers: tuple[str, ...] = DEFAULT_SQLITE_SEED_LAYERS,
) -> list[str]:
    """使用临时库完成标准 SQLite 首启初始化。"""
    manifest_path = get_sqlite_bootstrap_manifest_path(database_path)
    temporary_database_path = get_sqlite_temporary_database_path(database_path)

    messages = [
        f"SQLite 数据库路径: {database_path}",
        f"bootstrap 清单路径: {manifest_path}",
        f"临时数据库路径: {temporary_database_path}",
    ]

    messages.extend(delete_sqlite_database_files(temporary_database_path))
    messages.extend(delete_bootstrap_manifest_files(manifest_path))

    temporary_database_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_engine = create_async_engine(
        _sqlite_url_for_path(temporary_database_path),
        connect_args=settings.sqlalchemy_connect_args,
    )
    install_sqlite_runtime_hooks(temporary_engine)
    temporary_session_factory = async_sessionmaker(
        temporary_engine,
        expire_on_commit=False,
    )

    try:
        async with temporary_engine.begin() as conn:
            messages.extend(await configure_sqlite_runtime(conn))
            messages.extend(await create_database_schema(conn))

        messages.extend(await initialize_standard_sqlite_data(temporary_session_factory, seed_layers))

        await temporary_engine.dispose()
        messages.extend(validate_standard_sqlite_database(temporary_database_path))
        temporary_database_path.replace(database_path)
        messages.append(f"已原子替换正式数据库: {database_path.name}")
        messages.extend(write_sqlite_bootstrap_manifest(manifest_path, seed_layers))
        return messages
    except Exception:
        raise
    finally:
        await temporary_engine.dispose()
        messages.extend(delete_sqlite_database_files(temporary_database_path))
        temporary_manifest_path = get_temporary_manifest_path(manifest_path)
        if temporary_manifest_path.exists():
            temporary_manifest_path.unlink()


async def ensure_sqlite_file_startup(
    seed_layers: tuple[str, ...] = DEFAULT_SQLITE_SEED_LAYERS,
) -> SqliteStartupResult:
    """为文件型 SQLite 执行统一三态首启判定。"""
    directories = ensure_runtime_directories()
    database_path = settings.resolved_sqlite_database_path
    if database_path is None:
        raise RuntimeError("当前数据库不是文件型 SQLite，不能执行统一 SQLite bootstrap")

    inspection = inspect_sqlite_bootstrap_state(database_path, seed_layers)
    if inspection.status == "empty":
        messages = list(inspection.messages)
        messages.extend(await bootstrap_sqlite_database(database_path, seed_layers))
        manifest_path = get_sqlite_bootstrap_manifest_path(database_path)
        if not manifest_path.exists():
            raise RuntimeError("首次初始化完成后未发现 bootstrap 清单")
        return SqliteStartupResult(
            status="bootstrapped",
            database_path=database_path,
            manifest_path=manifest_path,
            directories=directories,
            messages=messages,
        )

    result_status: Literal["skipped", "blocked"] = (
        "skipped" if inspection.status == "standard" else "blocked"
    )
    return SqliteStartupResult(
        status=result_status,
        database_path=inspection.database_path,
        manifest_path=inspection.manifest_path,
        directories=directories,
        messages=list(inspection.messages),
    )


def reset_local_state() -> list[str]:
    """清空本地 SQLite、bootstrap 清单、上传、缓存和日志。"""
    messages: list[str] = []

    database_path = settings.resolved_sqlite_database_path
    if database_path is not None:
        manifest_path = get_sqlite_bootstrap_manifest_path(database_path)
        temporary_database_path = get_sqlite_temporary_database_path(database_path)
        messages.extend(delete_sqlite_database_files(database_path))
        messages.extend(delete_sqlite_database_files(temporary_database_path))
        messages.extend(delete_bootstrap_manifest_files(manifest_path))

    clear_directory_contents(settings.resolved_upload_dir)
    messages.append(f"已清空上传目录: {settings.resolved_upload_dir}")

    clear_directory_contents(settings.resolved_log_dir)
    messages.append(f"已清空日志目录: {settings.resolved_log_dir}")

    clear_directory_contents(settings.resolved_cache_dir)
    messages.append(f"已清空缓存目录: {settings.resolved_cache_dir}")

    messages.append("下次启动将执行首次初始化")
    return messages


def describe_sqlite_bootstrap_status(
    database_path: Path,
    seed_layers: tuple[str, ...] = DEFAULT_SQLITE_SEED_LAYERS,
) -> SqliteBootstrapInspection:
    """对外暴露当前 SQLite 首启状态检查。"""
    return inspect_sqlite_bootstrap_state(database_path, seed_layers)
