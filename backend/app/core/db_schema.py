"""数据库结构兼容性检查工具。

用于在应用启动或初始化脚本中补齐历史数据库缺失的字段，
避免代码已升级而线上表结构尚未同步时直接报错。
"""

from collections.abc import Callable

from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import AsyncConnection


async def ensure_database_compatibility(conn: AsyncConnection) -> list[str]:
    """补齐当前版本代码依赖的历史兼容字段。

    Returns:
        执行结果说明，供调用方记录日志或打印输出。
    """

    messages: list[str] = []

    def has_table(sync_conn, table_name: str) -> bool:
        return inspect(sync_conn).has_table(table_name)

    def get_columns(sync_conn, table_name: str) -> list[dict]:
        return inspect(sync_conn).get_columns(table_name)

    async def ensure_column(
        table_name: str,
        column_name: str,
        alter_sql_factory: Callable[[str], str],
        success_message: str,
    ) -> bool:
        if not await conn.run_sync(has_table, table_name):
            return False

        columns = await conn.run_sync(get_columns, table_name)
        if any(column["name"] == column_name for column in columns):
            return False

        await conn.execute(text(alter_sql_factory(conn.dialect.name)))
        messages.append(success_message)
        return True

    await ensure_column(
        "courses",
        "summary",
        lambda _: "ALTER TABLE courses ADD COLUMN summary VARCHAR(500)",
        "已为 courses 表补充 summary 字段",
    )

    if await conn.run_sync(has_table, "resources"):
        resource_columns = await conn.run_sync(get_columns, "resources")
        section_column = next(
            (column for column in resource_columns if column["name"] == "section_id"),
            None,
        )
        if section_column and not bool(section_column.get("nullable")):
            if conn.dialect.name == "mysql":
                await conn.execute(
                    text(
                        "ALTER TABLE resources "
                        "MODIFY COLUMN section_id INTEGER NULL COMMENT '小节ID'"
                    )
                )
                messages.append("已将 resources.section_id 调整为可空，支持章节级资源")
            else:
                messages.append(
                    "当前数据库方言不支持自动调整 resources.section_id 可空性，请手动检查"
                )

    await ensure_column(
        "feedbacks",
        "course_id",
        lambda _: "ALTER TABLE feedbacks ADD COLUMN course_id INTEGER",
        "已为 feedbacks 表补充 course_id 字段",
    )

    return messages
