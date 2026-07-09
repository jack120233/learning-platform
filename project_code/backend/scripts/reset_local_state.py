"""本地状态清理脚本。

清空 SQLite、bootstrap 清单、uploads、cache、logs，恢复到第一次打开前状态。

用法:
    cd backend
    python scripts/reset_local_state.py
"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import settings
from app.core.runtime import ensure_runtime_directories, reset_local_state


def main() -> None:
    print("=" * 50)
    print("本地状态清理脚本")
    print("=" * 50)

    try:
        ensure_runtime_directories()
        for message in reset_local_state():
            print(message)

        print("=" * 50)
        if settings.is_sqlite_file_database:
            print(f"SQLite 已清空: {settings.resolved_sqlite_database_path}")
        print("=" * 50)
    except Exception as exc:
        print(f"重置失败: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
