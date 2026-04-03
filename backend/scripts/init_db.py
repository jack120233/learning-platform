"""数据库初始化脚本

用于首次部署时初始化数据库表结构。

用法:
    cd backend
    python scripts/init_db.py
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import inspect, text

from app.core.dependencies import engine
from app.models import Base


async def init_database() -> None:
    """初始化数据库表结构"""
    print("=" * 50)
    print("数据库初始化脚本")
    print("=" * 50)

    try:
        async with engine.begin() as conn:
            # 测试数据库连接
            await conn.execute(text("SELECT 1"))
            print("✅ 数据库连接成功")

            # 创建所有表
            await conn.run_sync(Base.metadata.create_all)
            print("✅ 数据库表初始化完成")

            def has_course_summary_column(sync_conn) -> bool:
                columns = inspect(sync_conn).get_columns("courses")
                return any(column["name"] == "summary" for column in columns)

            if not await conn.run_sync(has_course_summary_column):
                await conn.execute(
                    text("ALTER TABLE courses ADD COLUMN summary VARCHAR(500)")
                )
                print("✅ 已为 courses 表补充 summary 字段")

        # 显示创建的表
        async with engine.connect() as conn:
            def get_table_names(sync_conn) -> list[str]:
                return inspect(sync_conn).get_table_names()

            tables = await conn.run_sync(get_table_names)
            print(f"\n已创建 {len(tables)} 张表:")
            for t in tables:
                print(f"  - {t}")

    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        sys.exit(1)

    print("\n" + "=" * 50)
    print("数据库初始化完成")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(init_database())
