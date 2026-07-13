"""Windows 安装版后端入口。"""

from __future__ import annotations

from datetime import datetime
import os
from pathlib import Path
import sys
import traceback

import uvicorn
from fastapi import APIRouter


BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.config import settings  # noqa: E402


def _resolve_bootstrap_log_path() -> Path:
    log_dir = os.getenv("LOG_DIR")
    if log_dir and log_dir.strip():
        resolved_log_dir = Path(log_dir).expanduser().resolve()
    else:
        resolved_log_dir = BACKEND_ROOT / "logs"
    resolved_log_dir.mkdir(parents=True, exist_ok=True)
    return resolved_log_dir / "bootstrap.log"


def _write_bootstrap_log(message: str) -> None:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_path = _resolve_bootstrap_log_path()
    with log_path.open("a", encoding="utf-8") as fp:
        fp.write(f"[{timestamp}] {message}\n")



def main() -> None:
    """启动安装版后端服务。"""
    _write_bootstrap_log(
        "starting"
        f" runtime_root={settings.resolved_runtime_root_dir}"
        f" host={settings.host}"
        f" port={settings.port}"
        f" frontend_index={settings.parsed_frontend_index_path}"
        f" database={settings.resolved_sqlite_database_path}"
    )
    try:
        from app.main import app

        uvicorn.run(
            app,
            host=settings.host,
            port=settings.port,
            reload=False,
            log_level=settings.log_level.lower(),
            log_config=None,
            timeout_graceful_shutdown=5,
            access_log=False,
        )
    except Exception:
        _write_bootstrap_log("startup_failed\n" + traceback.format_exc())
        raise


if __name__ == "__main__":
    main()
