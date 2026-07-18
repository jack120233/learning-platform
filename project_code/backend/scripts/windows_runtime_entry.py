"""Windows 安装版后端入口。"""

from __future__ import annotations

import asyncio
from datetime import datetime
import json
import os
from pathlib import Path
import socket
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


def _create_runtime_listener(host: str, requested_port: int) -> socket.socket:
    """Bind before Uvicorn starts so port 0 has no launcher-side race."""

    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
            listener.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        listener.bind((host, requested_port))
        listener.listen(socket.SOMAXCONN)
        listener.setblocking(False)
        return listener
    except Exception:
        listener.close()
        raise


def _write_runtime_port_report(port: int) -> None:
    """Atomically report the selected port to this launcher's private file."""

    raw_path = os.getenv("LEARNING_PLATFORM_PORT_REPORT_FILE", "").strip()
    raw_token = os.getenv("LEARNING_PLATFORM_SESSION_TOKEN", "").strip()
    if not raw_path or not raw_token:
        return

    report_path = Path(raw_path).expanduser().resolve()
    report_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = report_path.with_suffix(f".{os.getpid()}.tmp")
    payload = {
        "pid": os.getpid(),
        "port": port,
        "token": raw_token,
    }
    temporary_path.write_text(
        json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary_path, report_path)



def main() -> None:
    """启动安装版后端服务。"""
    listener: socket.socket | None = None
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

        listener = _create_runtime_listener(settings.host, settings.port)
        selected_port = int(listener.getsockname()[1])
        _write_runtime_port_report(selected_port)
        _write_bootstrap_log(f"listener_bound port={selected_port}")

        server = uvicorn.Server(
            uvicorn.Config(
                app,
                host=settings.host,
                port=selected_port,
                reload=False,
                log_level=settings.log_level.lower(),
                log_config=None,
                timeout_graceful_shutdown=5,
                access_log=False,
            )
        )
        asyncio.run(
            server.serve(
                sockets=[listener],
            )
        )
    except Exception:
        _write_bootstrap_log("startup_failed\n" + traceback.format_exc())
        raise
    finally:
        if listener is not None:
            listener.close()


if __name__ == "__main__":
    main()
