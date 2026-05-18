"""数据库迁移脚本：剥离 file_url 等列的绝对 URL 前缀。

历史上 upload_service 把 request.base_url 拼到上传文件 URL 前面写入数据库，
导致存到 DB 的形如 ``http://localhost:8000/uploads/files/xxx.pdf``，
浏览器从 Vite dev server (3000) 访问时会绕过 ``/uploads`` 代理，触发跨域。

现在 upload_service 改为只返回 ``/uploads/...`` 相对路径，本脚本负责把存量数据
里 ``http(s)://host[:port]/uploads/...`` 形态的值剥成 ``/uploads/...``，
对外部 URL（例如种子数据里的 ``https://example.com/...``）保持原样。

用法:
    cd backend
    python scripts/migrate_strip_upload_prefix.py
"""

import asyncio
import json
import sys
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text

from app.config import settings
from app.core.dependencies import engine


UPLOAD_PREFIX = settings.upload_url_prefix.rstrip("/") or "/uploads"


def strip_origin(value: str) -> str:
    """把 ``http(s)://host[:port]/uploads/...`` 剥成 ``/uploads/...``。

    只有当 URL 解析得到的 path 以配置的 upload_url_prefix 开头时才剥离；
    其它绝对 URL（外部资源、CDN）保持不变；纯相对路径也保持不变。
    """
    if not value:
        return value

    if value.startswith(UPLOAD_PREFIX + "/") or value == UPLOAD_PREFIX:
        return value

    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"}:
        return value
    if not parsed.path:
        return value
    if not (parsed.path == UPLOAD_PREFIX or parsed.path.startswith(UPLOAD_PREFIX + "/")):
        return value

    return parsed.path


def transform_json_list(value: str | None) -> str | None:
    """对 JSON 编码的字符串列表字段做剥离。"""
    if value is None:
        return None
    try:
        decoded = json.loads(value)
    except (TypeError, ValueError):
        return value
    if not isinstance(decoded, list):
        return value

    new_list = [strip_origin(item) if isinstance(item, str) else item for item in decoded]
    if new_list == decoded:
        return value
    return json.dumps(new_list, ensure_ascii=False)


# (表名, 主键列, URL 列, 是否 JSON 列)
SCALAR_TARGETS: list[tuple[str, str, str]] = [
    ("courses", "id", "cover_url"),
    ("resources", "id", "file_url"),
    ("course_materials", "id", "file_url"),
    ("users", "id", "avatar"),
]

JSON_LIST_TARGETS: list[tuple[str, str, str]] = [
    ("feedbacks", "id", "images"),
    ("teacher_audits", "id", "certificate_urls"),
]


async def migrate_scalar(conn, table: str, pk: str, column: str) -> int:
    """剥离单值 URL 列。返回更新行数。"""
    rows = (
        await conn.execute(
            text(f"SELECT {pk}, {column} FROM {table} WHERE {column} IS NOT NULL")
        )
    ).all()
    updated = 0
    for pk_value, raw in rows:
        if raw is None:
            continue
        stripped = strip_origin(raw)
        if stripped == raw:
            continue
        await conn.execute(
            text(f"UPDATE {table} SET {column} = :v WHERE {pk} = :id"),
            {"v": stripped, "id": pk_value},
        )
        updated += 1
    return updated


async def migrate_json_list(conn, table: str, pk: str, column: str) -> int:
    rows = (
        await conn.execute(
            text(f"SELECT {pk}, {column} FROM {table} WHERE {column} IS NOT NULL")
        )
    ).all()
    updated = 0
    for pk_value, raw in rows:
        if raw is None:
            continue
        stripped = transform_json_list(raw)
        if stripped == raw:
            continue
        await conn.execute(
            text(f"UPDATE {table} SET {column} = :v WHERE {pk} = :id"),
            {"v": stripped, "id": pk_value},
        )
        updated += 1
    return updated


async def main() -> None:
    print("=" * 50)
    print("数据库迁移：剥离 upload URL 绝对前缀")
    print(f"upload_url_prefix = {UPLOAD_PREFIX}")
    print("=" * 50)

    try:
        async with engine.begin() as conn:
            for table, pk, column in SCALAR_TARGETS:
                count = await migrate_scalar(conn, table, pk, column)
                print(f"  {table}.{column}: 更新 {count} 行")

            for table, pk, column in JSON_LIST_TARGETS:
                count = await migrate_json_list(conn, table, pk, column)
                print(f"  {table}.{column} (JSON list): 更新 {count} 行")

    except Exception as exc:  # noqa: BLE001
        print(f"❌ 迁移失败: {exc}")
        sys.exit(1)

    print("\n" + "=" * 50)
    print("数据库迁移完成")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
