"""数据库迁移脚本：增加 author 字段
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import inspect, text
from app.core.dependencies import engine

async def migrate_author() -> None:
    print("=" * 50)
    print("数据库迁移脚本：增加 author 字段")
    print("=" * 50)

    try:
        async with engine.begin() as conn:
            # 检查字段是否存在
            def has_author_column(sync_conn) -> bool:
                columns = inspect(sync_conn).get_columns("courses")
                return any(column["name"] == "author" for column in columns)

            if not await conn.run_sync(has_author_column):
                print("正在为 courses 表添加 author 字段...")
                await conn.execute(
                    text("ALTER TABLE courses ADD COLUMN author VARCHAR(100) NULL COMMENT '作者名字'")
                )
                print("✅ 字段添加成功")
            else:
                print("ℹ️ courses 表中已存在 author 字段，无需重复添加")

    except Exception as e:
        print(f"❌ 迁移失败: {e}")
        sys.exit(1)

    print("\n" + "=" * 50)
    print("数据库迁移完成")
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(migrate_author())
