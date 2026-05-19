"""本地运行时初始化工具。"""

from collections.abc import Callable
from pathlib import Path
from typing import Any

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncConnection, async_sessionmaker

from app.config import settings
from app.models.user import User


def ensure_runtime_directories() -> list[Path]:
    """确保当前运行版本需要的本地目录存在。"""
    created_or_existing: list[Path] = []
    for directory in settings.runtime_directories:
        directory.mkdir(parents=True, exist_ok=True)
        created_or_existing.append(directory)
    return created_or_existing


async def configure_sqlite_runtime(conn: AsyncConnection) -> list[str]:
    """为 SQLite 文件数据库应用本地运行优化。"""
    if not settings.is_sqlite_file_database:
        return []

    messages: list[str] = []
    await conn.execute(text(f"PRAGMA busy_timeout={settings.sqlite_busy_timeout_ms}"))
    messages.append(f"已设置 SQLite busy_timeout={settings.sqlite_busy_timeout_ms}ms")

    if settings.app_edition == "windows_classroom":
        result = await conn.execute(text("PRAGMA journal_mode=WAL"))
        journal_mode = (result.scalar() or "").upper()
        messages.append(f"已设置 SQLite journal_mode={journal_mode or 'WAL'}")

    return messages


async def initialize_database_schema(conn: AsyncConnection) -> list[str]:
    """创建数据库表并执行兼容性修复。"""
    from app.core.db_schema import ensure_database_compatibility
    from app.models import Base

    await conn.run_sync(Base.metadata.create_all)
    return await ensure_database_compatibility(conn)


async def seed_database_if_empty(
    session_factory: async_sessionmaker[Any],
    seed_runner: Callable[[], object] | None = None,
) -> bool:
    """在数据库没有用户数据时复用种子脚本导入测试数据。"""
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
    """初始化权限默认数据，并在发现缺失时补录。"""
    from app.services.permission_service import permission_service

    async with session_factory() as session:
        await permission_service.ensure_schema_and_seed(session)
        messages = await permission_service.check_and_backfill_default_permissions(session)
        await session.commit()
    return messages


async def ensure_windows_local_startup(
    engine: Any,
    session_factory: async_sessionmaker[Any],
) -> tuple[list[Path], list[str], bool]:
    """执行 Windows 单机版启动所需的目录、建表、兼容检查和种子初始化。"""
    directories = ensure_runtime_directories()

    async with engine.begin() as conn:
        runtime_messages = await configure_sqlite_runtime(conn)
        schema_messages = await initialize_database_schema(conn)

    permission_messages = await initialize_permission_defaults(session_factory)
    seeded = await seed_database_if_empty(session_factory)
    return directories, runtime_messages + schema_messages + permission_messages, seeded
