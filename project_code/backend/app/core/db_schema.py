"""数据库结构兼容性检查工具。

用于在应用启动或初始化脚本中补齐历史数据库缺失的字段，
避免代码已升级而线上表结构尚未同步时直接报错。
"""

from collections.abc import Callable

from sqlalchemy import inspect, text

from app.models import Base
from sqlalchemy.ext.asyncio import AsyncConnection

from app.services.permission_service import DEFAULT_ROLE_PERMISSION_IDS


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

    await conn.run_sync(lambda sync_conn: Base.metadata.create_all(bind=sync_conn))

    await ensure_column(
        "courses",
        "summary",
        lambda _: "ALTER TABLE courses ADD COLUMN summary VARCHAR(500)",
        "已为 courses 表补充 summary 字段",
    )

    await ensure_column(
        "resources",
        "is_required",
        lambda dialect: (
            "ALTER TABLE resources ADD COLUMN is_required BOOLEAN NOT NULL DEFAULT 1"
            if dialect == "sqlite"
            else "ALTER TABLE resources ADD COLUMN is_required BOOLEAN NOT NULL DEFAULT TRUE COMMENT '是否必修资源'"
        ),
        "已为 resources 表补充 is_required 字段",
    )

    await ensure_column(
        "learning_progress",
        "last_resource_id",
        lambda _: "ALTER TABLE learning_progress ADD COLUMN last_resource_id INTEGER",
        "已为 learning_progress 表补充 last_resource_id 字段",
    )
    await ensure_column(
        "learning_progress",
        "last_learn_at",
        lambda _: "ALTER TABLE learning_progress ADD COLUMN last_learn_at DATETIME",
        "已为 learning_progress 表补充 last_learn_at 字段",
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

    if await conn.run_sync(has_table, "resource_progress"):
        progress_columns = await conn.run_sync(get_columns, "resource_progress")
        progress_section_column = next(
            (column for column in progress_columns if column["name"] == "section_id"),
            None,
        )
        if progress_section_column and not bool(progress_section_column.get("nullable")):
            if conn.dialect.name == "mysql":
                await conn.execute(
                    text(
                        "ALTER TABLE resource_progress "
                        "MODIFY COLUMN section_id INTEGER NULL COMMENT '小节ID'"
                    )
                )
                messages.append("已将 resource_progress.section_id 调整为可空，支持章节级资源进度")
            elif conn.dialect.name == "sqlite":
                await conn.execute(text("ALTER TABLE resource_progress RENAME TO resource_progress_old"))
                await conn.execute(
                    text(
                        "CREATE TABLE resource_progress ("
                        "id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, "
                        "user_id INTEGER NOT NULL, "
                        "course_id INTEGER NOT NULL, "
                        "chapter_id INTEGER NOT NULL, "
                        "section_id INTEGER NULL, "
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
                await conn.execute(
                    text(
                        "INSERT INTO resource_progress ("
                        "id, user_id, course_id, chapter_id, section_id, resource_id, "
                        "progress, position, is_completed, completed_at, last_play_at, created_at, updated_at"
                        ") "
                        "SELECT "
                        "id, user_id, course_id, chapter_id, section_id, resource_id, "
                        "progress, position, is_completed, completed_at, last_play_at, created_at, updated_at "
                        "FROM resource_progress_old"
                    )
                )
                await conn.execute(text("DROP TABLE resource_progress_old"))
                await conn.execute(text("CREATE INDEX idx_resource_progress_user_id ON resource_progress (user_id)"))
                await conn.execute(text("CREATE INDEX idx_resource_progress_course_id ON resource_progress (course_id)"))
                await conn.execute(text("CREATE INDEX idx_resource_progress_chapter_id ON resource_progress (chapter_id)"))
                await conn.execute(text("CREATE INDEX idx_resource_progress_section_id ON resource_progress (section_id)"))
                await conn.execute(text("CREATE INDEX idx_resource_progress_resource_id ON resource_progress (resource_id)"))
                messages.append("已将 resource_progress.section_id 调整为可空，支持章节级资源进度")
            else:
                messages.append(
                    "当前数据库方言不支持自动调整 resource_progress.section_id 可空性，请手动检查"
                )

    await ensure_column(
        "feedbacks",
        "course_id",
        lambda _: "ALTER TABLE feedbacks ADD COLUMN course_id INTEGER",
        "已为 feedbacks 表补充 course_id 字段",
    )
    await ensure_column(
        "feedbacks",
        "target_user_id",
        lambda _: "ALTER TABLE feedbacks ADD COLUMN target_user_id INTEGER",
        "已为 feedbacks 表补充 target_user_id 字段",
    )
    await ensure_column(
        "messages",
        "is_deleted",
        lambda _: "ALTER TABLE messages ADD COLUMN is_deleted BOOLEAN NOT NULL DEFAULT 0",
        "已为 messages 表补充 is_deleted 字段",
    )
    await ensure_column(
        "messages",
        "deleted_at",
        lambda _: "ALTER TABLE messages ADD COLUMN deleted_at DATETIME",
        "已为 messages 表补充 deleted_at 字段",
    )

    if await conn.run_sync(has_table, "permissions") and await conn.run_sync(has_table, "role_permissions"):
        allowed_teacher_permission_ids = ", ".join(
            str(permission_id) for permission_id in DEFAULT_ROLE_PERMISSION_IDS["teacher"]
        )
        teacher_rows = await conn.execute(
            text("SELECT permission_id FROM role_permissions WHERE role = 'teacher'")
        )
        current_teacher_permission_ids = {row[0] for row in teacher_rows.fetchall()}
        if current_teacher_permission_ids:
            target_teacher_permission_ids = set(DEFAULT_ROLE_PERMISSION_IDS["teacher"])

            stale_teacher_permission_ids = current_teacher_permission_ids - target_teacher_permission_ids
            missing_teacher_permission_ids = target_teacher_permission_ids - current_teacher_permission_ids

            if stale_teacher_permission_ids:
                await conn.execute(
                    text(
                        "DELETE FROM role_permissions "
                        "WHERE role = 'teacher' "
                        f"AND permission_id NOT IN ({allowed_teacher_permission_ids})"
                    )
                )
                messages.append("已清理老师角色的历史后台权限")

            for permission_id in sorted(missing_teacher_permission_ids):
                await conn.execute(
                    text(
                        "INSERT INTO role_permissions (role, permission_id) "
                        "SELECT :role, :permission_id "
                        "WHERE NOT EXISTS ("
                        "SELECT 1 FROM role_permissions WHERE role = :role AND permission_id = :permission_id"
                        ")"
                    ),
                    {"role": "teacher", "permission_id": permission_id},
                )
            if missing_teacher_permission_ids:
                messages.append("已补齐老师角色当前默认权限")

    return messages
