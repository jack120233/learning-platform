"""SQLite 统一初始化脚本。

默认执行标准首启 bootstrap，而不是仅建表。

用法:
    cd backend
    python scripts/init_db.py
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import inspect

from app.config import settings
from app.core.dependencies import engine
from app.core.runtime import ensure_runtime_directories, ensure_sqlite_file_startup, initialize_database_schema


async def init_database() -> None:
    """执行统一初始化。"""
    print("=" * 50)
    print("SQLite 统一初始化脚本")
    print("=" * 50)

    try:
        ensure_runtime_directories()

        if settings.is_sqlite_file_database:
            startup_result = await ensure_sqlite_file_startup()
            for message in startup_result.messages:
                print(message)
            if startup_result.status == "blocked":
                raise RuntimeError("\n".join(startup_result.messages))
            print("已完成标准 SQLite 初始化" if startup_result.status == "bootstrapped" else "已初始化，跳过")
        else:
            async with engine.begin() as conn:
                for message in await initialize_database_schema(conn):
                    print(message)

        # 显示创建的表
        async with engine.connect() as conn:
            def get_table_names(sync_conn) -> list[str]:
                return inspect(sync_conn).get_table_names()

            tables = await conn.run_sync(get_table_names)
            print(f"\n已创建 {len(tables)} 张表:")
            for t in tables:
                print(f"  - {t}")

    except Exception as e:
        print(f"初始化失败: {e}")
        sys.exit(1)

    print("\n" + "=" * 50)
    print("数据库初始化完成")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(init_database())
